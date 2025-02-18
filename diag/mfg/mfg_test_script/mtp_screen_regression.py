#!/usr/bin/env python

import sys
import os
import time
import pexpect
import re
import argparse
import random
import datetime
import threading
import traceback
import json
import concurrent.futures
from collections import OrderedDict

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
import test_utils
import libmtp_utils
import testlog
import parallelize
from libdefs import MTP_Const
from libdefs import NIC_Type
from libdefs import MTP_TYPE
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import Swm_Test_Mode
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Path
from libdefs import Voltage_Margin
from libdefs import Factory
from libdefs import MTP_DIAG_Logfile
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libmfg_cfg import *
from diag_screening_emmc import save_test_data2csv_file
from diag_screening_ddr import get_test_arguments
from diag_screening_ddr import args2optionstring
from emmc_test_parameters import test2args as emmctest2args


# test cleanup.
def mtp_test_cleanup(error_code, fp_list=None):
    # if fp_list:
    #     for fp in fp_list:
    #         fp.close()
    os.system("sync")

def program_mtp_fru(mtp_mgmt_ctrl):
    mtp_sn = mtp_mgmt_ctrl._mtp_sn
    mtp_mac = mtp_mgmt_ctrl._mtp_mac
    cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False
    if not mtp_mgmt_ctrl.mtp_set_sn_rev_mac_command(sn=mtp_sn, maj="04", mac=mtp_mac):
        mtp_mgmt_ctrl.cli_log_err("MTP program FRU command failed", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("MTP program FRU command passed", level=0)
    return True

def check_fully_populated(mtp_mgmt_ctrl, nic_list):
    missing_nic_list = list()
    if len(nic_list) != 10:
        mtp_mgmt_ctrl.cli_log_err("Not able to detect 10 NICs", level=0)
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot not in nic_list:
                mtp_mgmt_ctrl.cli_log_err("Missing slot {:s}".format(str(slot+1)), level=0)
                missing_nic_list.append(slot)

    if not missing_nic_list:
        mtp_mgmt_ctrl.cli_log_inf("MTP detect 10 NIC passed", level=0)
    return missing_nic_list

def check_nic_type(mtp_mgmt_ctrl, nic_list):
    if len(nic_list) == 0: return False
    first_slot = nic_list[0]
    nic_fail_list = list()
    for slot in nic_list:
        if mtp_mgmt_ctrl.mtp_get_nic_type(first_slot) != mtp_mgmt_ctrl.mtp_get_nic_type(slot):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Incorrect NIC Type mismatch with first slot {:s}".foramt(mtp_mgmt_ctrl.mtp_get_nic_type(first_slot)))
            nic_fail_list.append(slot)
    return nic_fail_list

def run_j2c_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, stage, force_sequential):
    @parallelize.parallel_nic_using_j2c
    def run_j2c_test_normally(mtp_mgmt_ctrl, slot, test, vmarg):
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot)
        mode = libmfg_utils.get_mode_param(mtp_mgmt_ctrl, slot, test)
        n_vmarg = vmarg
        if vmarg in (Voltage_Margin.high, Voltage_Margin.low):
            n_vmarg += libmfg_utils.pick_voltage_margin_percentage(pn)
            mtp_mgmt_ctrl.cli_log_inf("Vmargin is: {:s} After Apply Percentage using Part Number: {:s} For before run_l1.sh".format(n_vmarg, pn), level=0)

        return mtp_mgmt_ctrl.mtp_run_asic_l1_bash(slot, sn, mode, n_vmarg, stage)

    @parallelize.sequential_nic_test
    def run_j2c_test_sequentially(mtp_mgmt_ctrl, slot, test, vmarg):
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot)
        mode = libmfg_utils.get_mode_param(mtp_mgmt_ctrl, slot, test)
        n_vmarg = vmarg
        if vmarg in (Voltage_Margin.high, Voltage_Margin.low):
            n_vmarg += libmfg_utils.pick_voltage_margin_percentage(pn)
            mtp_mgmt_ctrl.cli_log_inf("Vmargin is: {:s} After Apply Percentage using Part Number: {:s} For before run_l1.sh".format(n_vmarg, pn), level=0)

        return mtp_mgmt_ctrl.mtp_run_asic_l1_bash(slot, sn, mode, n_vmarg, stage)

    if force_sequential:
        fail_j2c_list = run_j2c_test_sequentially(mtp_mgmt_ctrl, nic_list, test, vmarg)
    else:
        fail_j2c_list = run_j2c_test_normally(mtp_mgmt_ctrl, nic_list, test, vmarg)

    # double check the L1 test even if it passed
    if dsp == "ASIC" and test == "L1":
        for slot in nic_list:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            pass_count, log_err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_nic_l1_err(sn)
            number_of_l1_tests = 7
            err_msg_list = list()
            if pass_count != number_of_l1_tests:
                err_msg_list = ["L1 Sub Test only passed: {:d}".format(pass_count)]
                fail_j2c_list += [slot]
            if log_err_msg_list:
                err_msg_list += log_err_msg_list

            for err_msg in err_msg_list:
                mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_set_err_msg(err_msg)

    return fail_j2c_list

def mtp_nvme_ssd_validation_test(mtp_mgmt_ctrl):
    """MTP NVME SSD validation test

    Args:
        mtp_mgmt_ctrl (_type_): _description_
        slot (_type_): _description_
        test_steps (_type_): _description_
        nic_test_rslt_list (_type_): _description_
        nic_test_data (_type_): _description_
        stop_on_err (_type_): _description_
    """

    mtp_script_dir = testlog.get_mtp_test_log_folder(mtp_mgmt_ctrl)
    mtp_mgmt_ctrl.cli_log_inf("MTP NVME SSD Validation Test Start")

    mtp_mgmt_ctrl.cli_log_inf("GET NVME SSD drive info")
    drive_info = read_mtp_nvme_ssd_para(mtp_mgmt_ctrl)
    if not drive_info:
        mtp_mgmt_ctrl.mtp_diag_fail_report("Failed To Get NVME SSD drive info")
        return False
    mtp_mgmt_ctrl.cli_log_inf(str(drive_info))

    # load test configuration
    parameter_cfg_yaml = "config/emmc_test_suite.yaml"
    emmc_suite = libmfg_utils.load_cfg_from_yaml_file_list([parameter_cfg_yaml])

    iterations = emmc_suite["ITER"]
    iterations = 1

    # test data is the parsed results from emmc bench mark test tool,  the key is the nic slot number, the value is the list of all test iteratrions
    nic_test_data = {
        1:[],
        2:[],
        3:[],
        4:[],
        5:[],
        6:[],
        7:[],
        8:[],
        9:[],
        10:[]
    }
    test_steps = [step["NAME"] for step in  emmc_suite["TEST_CASE"]]

    for idx in range(1, int(iterations)+1):
        mtp_mgmt_ctrl.cli_log_inf("--*" * 30, level=0)
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} NVME SSD Validation Test Iteration {:d}".format(drive_info["FormFactor"], idx), level=0)
        mtp_mgmt_ctrl.cli_log_inf("--*" * 30, level=0)
        # Run Test

        sn = drive_info["SerialNumber"]
        emmc_test_data = {}

        # run test steps under both vmargin high and vmargin low for all Normal temperature, Low temperature and High temperature
        for vmargin in [Voltage_Margin.high, Voltage_Margin.low]:
            # set vmargin to low or high
            # (EMMC_PRE_SET, NIC_VMARG) START
            # test = "NIC_VMARG"
            # mtp_mgmt_ctrl.cli_log_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, "EMMC_PRE_SET", test))
            # start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            # if not mtp_mgmt_ctrl.mtp_set_nic_vmarg(slot, vmargin):
            #     nic_test_rslt_list[slot] = False
            # if not mtp_mgmt_ctrl.mtp_nic_display_voltage(slot):
            #     nic_test_rslt_list[slot] = False
            # duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            # mtp_mgmt_ctrl.cli_log_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, "EMMC_PRE_SET", test, duration))
            # (EMMC_PRE_SET, NIC_VMARG) END

            # Sleep 30 seconds before emmc performace test
            time.sleep(30)

            # Start emmc performace test commands
            fio_stressapp_data = {}
            fio_stressapp_order_data = OrderedDict()
            dir_in_ssd_partition = '/home/diag'
            for test in test_steps:
                cmds = ["cd "+dir_in_ssd_partition, "rm -rf Random*", "rm -rf Sequen*"]
                tout = MTP_Const.NIC_CON_CMD_DELAY
                argsdict = get_test_arguments(test_case_name=test, part_number="MATERA_PN_NVME", test2args=emmctest2args)
                if not argsdict:
                    mtp_mgmt_ctrl.cli_log_inf("{:s} -> Test Step {:s} Failed".format(sn, test), level=0)
                    return False
                cmd_options =  args2optionstring(argsdict)
                if "FIO_" in test:
                    cmd = "/usr/bin/fio "
                elif "STRESSAPPTEST" in test:
                    cmd = "/home/diag/diag/tools/stressapptest "
                    tout = max([int(arg_s_val) for arg_s_val in argsdict["-s"]]) + 300
                else:
                    return
                cmd += cmd_options
                mtp_mgmt_ctrl.cli_log_inf(cmd)
                cmds.append(cmd)
                for cmd in cmds:
                    cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=tout)
                    if not cmd_result:
                        mtp_mgmt_ctrl.cli_log_inf("{:s} -> Command {:s} Failed".format(sn, cmd))
                        return False
                cmd_result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
                if not cmd_result:
                    mtp_mgmt_ctrl.cli_log_err("Failed to get command {:s} Output".format(cmd))
                    return False

                #parse cmd_results
                if "FIO_" in test:
                    pattern = r':\s+IOPS=(.*),\s+BW=(.*?)\s+'
                    match_obj = re.search(pattern, cmd_result)
                    if match_obj:
                        iops = match_obj.group(1).lower()
                        if 'k' in iops:
                            iops = iops.strip('k')
                            iops = str(int(float(iops) * 1000))
                        bw = match_obj.group(2)
                        bw = bw.strip("MiB/s")
                        fio_stressapp_data[test] = (iops, bw)
                        mtp_mgmt_ctrl.cli_log_inf("{:s} IOPS={:s}, BW={:s}MiB/s".format(test, iops, bw))
                elif "STRESSAPPTEST" in test:
                    pattern1 = r'Status:\s+(\w+)\s+-+\s+please verify no corrected errors'
                    match_obj1 = re.search(pattern1, cmd_result)
                    pattern2 = r'Stats: File Copy: .* at (\d+\.+\d*MB\/s)'
                    match_obj2 = re.search(pattern2, cmd_result)
                    if match_obj1 and match_obj2:
                        res = match_obj1.group(1)
                        file_cp_bw = match_obj2.group(1)
                        file_cp_bw = file_cp_bw.strip("MB/s")
                        fio_stressapp_data[test] = (res, file_cp_bw)
                        mtp_mgmt_ctrl.cli_log_inf("{:s} Status:{:s}, File Copy At {:s}MB/s".format(test, res, file_cp_bw))

            # sort data
            for key in sorted(fio_stressapp_data.keys()):
                fio_stressapp_order_data[key] = fio_stressapp_data[key]
            emmc_test_data[vmargin] = fio_stressapp_order_data

        head_data = OrderedDict()
        #head_data["SlotID"] = "Slot1"
        head_data["Serial_Number"] = sn
        head_data["Model Number"] = drive_info["ModelNumber"]
        head_data["Capacity"] = str(round(float(drive_info["PhysicalSize"]) / 1024 / 1024 / 1024, 2)) + 'GB'
        head_data["Firmware Revision"] = drive_info["Firmware"]
        nic_test_data[1].append({"head": head_data, "data": emmc_test_data})

    savedfile = save_test_data2csv_file(mtp_mgmt_ctrl, nic_test_data, csvfilename="ssd_validation.csv.log")
    if savedfile:
        cmd = "mv /home/diag/mfg_test_script/{:s} {:s}".format(savedfile, mtp_script_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=tout):
            mtp_mgmt_ctrl.cli_log_inf("Command {:s} Failed".format(cmd))
            return False
        mtp_mgmt_ctrl.cli_log_inf("Test data saved to CSV file {:s}".format(savedfile))

    return True

def get_mtp_nvme_ssd_formfactor(mtp_mgmt_ctrl, dev_name='/dev/nvme0n1'):
    """so we don't have a command to get nvme ssd drive formfactor, so we just hardcode to M.2, if we found some utility in the future, we can rewrite the function

    Args:
        mtp_mgmt_ctrl (_type_): _description_
        dev_name (str, optional): _description_. Defaults to '/dev/nvme0n1'.
    """

    return "M.2"

def read_mtp_nvme_ssd_para(mtp_mgmt_ctrl, dev_name='/dev/nvme0n1'):
    """read NVME SSD drive info using nvme cli tool

    Args:
        mtp_mgmt_ctrl (_type_): _description_
    """

    json_file = "/tmp/nveme_info.json"
    cmd = "nvme list -o json {:s} > {:s}".format(dev_name, json_file)

    if not  mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Read NVMD SSD parameter command failed. {:s}".format(cmd), level=0)
        mtp_mgmt_ctrl.mtp_dump_err_msg(mtp_mgmt_ctrl.mtp_get_cmd_buf())
        return False

    try:
        with open(json_file) as json_file_obj:
            device_info_in_json = json.load(json_file_obj)
    except Exception as Err:
        mtp_mgmt_ctrl.mtp_dump_err_msg(mtp_mgmt_ctrl.mtp_get_cmd_buf())
        mtp_mgmt_ctrl.cli_log_err(str(Err))
        return False

    try:
        device_info = device_info_in_json["Devices"][0]
    except Exception as Err:
        mtp_mgmt_ctrl.cli_log_err(str(Err))
        return False

    dev_form_factor = get_mtp_nvme_ssd_formfactor(mtp_mgmt_ctrl, dev_name)
    if not dev_form_factor:
        return False
    device_info["FormFactor"] = dev_form_factor

    return device_info

def mtp_cpu_validation_test(mtp_mgmt_ctrl):
    """MTP CPU validation Test, AMD CPU only Since using AMD Validation Toolkits(AVT)

    Args:
        mtp_mgmt_ctrl (_type_): _description_
        stop_on_err (_type_): _description_
    """

    avt_installation_dir = "/home/diag/AMD_tool_AVT/"
    avt_test_log_template = "avt_mfg_test.utp"
    avt_test_log_csv = "avt_stress_log.csv"
    avt_pmm_log_csv = "/tmp/avt_pmm_log.csv.log"
    cpu_validation_result = True
    mtp_script_dir = testlog.get_mtp_test_log_folder(mtp_mgmt_ctrl)

    def mtp_2nd_mgmt_exec_cmd(mtp_mgmt_ctrl, handle, cmd, sig_list=[], timeout=MTP_Const.OS_CMD_DELAY):

        rc = True
        handle.sendline(cmd)
        cmd_before = ""
        buf_before_sig = ""
        for sig in sig_list:
            idx = libmfg_utils.mfg_expect(handle, [sig], timeout)
            buf_before_sig += handle.before
            if idx < 0:
                rc = False
                cmd_before = handle.before
                break
        idx = libmfg_utils.mfg_expect(handle, ["$"], timeout)
        # signature match fails
        if not rc:
            mtp_mgmt_ctrl.mtp_dump_err_msg(cmd_before)
            return (False, cmd_before)
        elif idx < 0:
            mtp_mgmt_ctrl.mtp_dump_err_msg(handle.before)
            return (False, buf_before_sig + handle.before)
        else:
            cmd_output = buf_before_sig + handle.before
            # print(cmd_buf + "$")

        # get command return code
        handle.sendline("echo $?")
        idx = libmfg_utils.mfg_expect(handle, ["$"], 3)
        idx = libmfg_utils.mfg_expect(handle, ["$"], 5)
        if idx < 0:
            mtp_mgmt_ctrl.cli_log_slot_wrn("Failed to Get Command Return Value" + handle.before)
            return (True, cmd_output)

        cmd_return_code = handle.before.splitlines()[2].strip("\r").strip()
        if cmd_return_code != '0':
            return (False, cmd_output + " echo $?" + handle.before)

        return (True, cmd_output)

    def mtp_2nd_mgmt_exec_sudo_cmd_resp(mtp_mgmt_ctrl, handle, cmd, timeout=MTP_Const.OS_CMD_DELAY):

        userid = mtp_mgmt_ctrl._mgmt_cfg[1]
        passwd = mtp_mgmt_ctrl._mgmt_cfg[2]

        handle.sendline("sudo -k " + cmd)
        idx = libmfg_utils.mfg_expect(handle, [userid + ":", "$"], timeout=10)
        if idx < 0:
            rs = handle.before
            return (False, "[FAIL]: " + rs)
        elif idx == 0:
            handle.sendline(passwd)
            idx = libmfg_utils.mfg_expect(handle, ["$"], timeout=timeout)
            if idx < 0:
                mtp_mgmt_ctrl.cli_log_err("sudo password not correct", level=0)
                return (False, "[FAIL]: sudo password not correct" + handle.before)
            else:
                rs = handle.before
        elif idx == 1:
            rs = handle.before

        # get command return code
        handle.sendline("echo $?")
        idx = libmfg_utils.mfg_expect(handle, ["$"], 3)
        idx = libmfg_utils.mfg_expect(handle, ["$"], 5)
        if idx < 0:
            mtp_mgmt_ctrl.cli_log_slot_wrn("Failed to Get Command Return Value" + handle.before)
            return (True, rs)

        cmd_return_code = handle.before.splitlines()[2].strip("\r").strip()
        if cmd_return_code != '0':
            return (False, rs + " echo $?" + handle.before)

        return (True, rs)

    def run_avt_stress_system(mtp_mgmt_ctrl):

        mtp_mgmt_ctrl.cli_log_inf_lock("start running avt stress system", level=0)
        result = False

        tout = MTP_Const.NIC_CON_CMD_DELAY
        cmd = "cd " + avt_installation_dir
        cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=tout)
        if not cmd_result:
            mtp_mgmt_ctrl.cli_log_err_lock("Command {:s} Failed".format(cmd), level=0)
            return result

        cmd = './AVT -module tct "settargetpower(65,maxcpustress) settesttime(1m) log(T=' + avt_test_log_template + ',O=./' + avt_test_log_csv + ',I=1000) -multi"'
        mtp_mgmt_ctrl.cli_log_inf_lock(cmd, level=0)
        rs = mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd_resp(cmd, timeout=tout)
        mtp_mgmt_ctrl.cli_log_inf_lock(str(rs), level=0)
        mtp_mgmt_ctrl.cli_log_inf_lock("finished avt stress system", level=0)
        if not rs or rs.startswith("[FAIL]:"):
            mtp_mgmt_ctrl.cli_log_err_lock("AVS stress command failed.{:s}".format(cmd), level=0)
            mtp_mgmt_ctrl.cli_log_err_lock(rs, level=0)
            return result
        result = True
        return result

    def run_avt_loop_pstates(mtp_mgmt_ctrl, avt_stress_handle):

        mtp_mgmt_ctrl.cli_log_inf_lock("start runing avt loop pstates", level=0)
        result = False

        tout = MTP_Const.NIC_CON_CMD_DELAY
        cmd = "cd " + avt_installation_dir
        cmd_result = mtp_2nd_mgmt_exec_cmd(mtp_mgmt_ctrl, avt_stress_handle, cmd, timeout=30)
        if not cmd_result[0]:
            mtp_mgmt_ctrl.cli_log_err_lock("command {:s} on 2nd mtp mgmt session failed".format(cmd), level=0)
            mtp_mgmt_ctrl.cli_log_err_lock(cmd_result[1], level=0)
            return result

        cmd = './AVT -module pstates "mode(up) loop(40) -multi"' # 40 loops takes about 1 min, match stress time setting
        mtp_mgmt_ctrl.cli_log_inf_lock(cmd, level=0)
        cmd_result = mtp_2nd_mgmt_exec_sudo_cmd_resp(mtp_mgmt_ctrl, avt_stress_handle, cmd, timeout=tout)
        mtp_mgmt_ctrl.cli_log_inf_lock(cmd_result[1], level=0)
        mtp_mgmt_ctrl.cli_log_inf_lock("finished avt loop pstates", level=0)
        if not cmd_result[0] or cmd_result[1].startswith("[FAIL]:"):
            mtp_mgmt_ctrl.cli_log_err_lock("AVT loop pstates command failed.{:s}".format(cmd), level=0)
            mtp_mgmt_ctrl.cli_log_err_lock(cmd_result[1], level=0)
            return result
        result = True
        return result

    def run_avt_pmm_getdata(mtp_mgmt_ctrl, avt_pmm_getdata_handle):
        mtp_mgmt_ctrl.cli_log_inf_lock("start runing avt pmm get data for PPT_VALUE", level=0)
        result = False

        tout = MTP_Const.NIC_CON_CMD_DELAY
        cmd = "cd " + avt_installation_dir
        cmd_result = mtp_2nd_mgmt_exec_cmd(mtp_mgmt_ctrl, avt_pmm_getdata_handle, cmd, timeout=30)
        if not cmd_result[0]:
            mtp_mgmt_ctrl.cli_log_err_lock("command {:s} on 3rd mtp mgmt session failed".format(cmd), level=0)
            mtp_mgmt_ctrl.cli_log_err_lock(cmd_result[1], level=0)
            return result

        frs = []
        # 15 loops is approximate 1 miniute
        for i in range(15):
            cmd = "date +%H:%M:%S:%3N"
            cmd_result = mtp_2nd_mgmt_exec_cmd(mtp_mgmt_ctrl, avt_pmm_getdata_handle, cmd, timeout=30)
            if not cmd_result[0]:
                mtp_mgmt_ctrl.cli_log_err_lock("command {:s} on 3rd mtp mgmt session failed".format(cmd), level=0)
                mtp_mgmt_ctrl.cli_log_err_lock(cmd_result[1], level=0)
                return result

            timestamp = ""
            for timestamp in re.finditer(r'\d{2}:\d{2}:\d{2}:\d{3}', cmd_result[1]):
                timestamp = timestamp.group(0)
                break

            cmd = './AVT -module pmm "get_pmdata(2)"'
            if i == 0:
                mtp_mgmt_ctrl.cli_log_inf_lock(cmd, level=0)
            cmd_result = mtp_2nd_mgmt_exec_sudo_cmd_resp(mtp_mgmt_ctrl, avt_pmm_getdata_handle, cmd, timeout=tout)
            if not cmd_result[0] or cmd_result[1].startswith("[FAIL]:"):
                mtp_mgmt_ctrl.cli_log_err_lock("AVT pmm get data command failed.{:s}".format(cmd), level=0)
                mtp_mgmt_ctrl.cli_log_err_lock(cmd_result[1], level=0)
                return result
            rs_line_head = "TIMESTAMP,"
            rs_line_value = timestamp + ","
            for line in cmd_result[1].split("\n"):
                line = line.strip("\r")
                if "[INFRASTRUCTURE]" in line:
                    rs_line_head += ",".join([item.split(":")[0].strip() for item in line.split(",")[2:]])
                    rs_line_value += ",".join([item.split(":")[1].strip() for item in line.split(",")[2:]])
                if "[FREQUENCIES]" in line:
                    rs_line_head += "," + ",".join([item.split(":")[0].strip() for item in line.split(",")[2:]])
                    rs_line_value += "," + ",".join([item.split(":")[1].strip() for item in line.split(",")[2:]])
            if not frs:
                frs.append(rs_line_head)
            frs.append(rs_line_value)
            if i == 0:
                for line in frs:
                    mtp_mgmt_ctrl.cli_log_inf_lock(line, level=0)
            # no sleep needed since PM bus is slow bus, it takes 3 seconds to get one batch of data.
            # time.sleep(1)

        with open(avt_pmm_log_csv, 'w') as logfile:
            for line in frs:
                logfile.write(line + "\n")

        mtp_mgmt_ctrl.cli_log_inf_lock("finished pmm get data", level=0)
        result = True
        return result

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Validation Test Start".format("AMD CPU"), level=0)
    # copy avt customized logging template file to avt tool desired destination directory
    cmd = "cp /home/diag/mfg_test_script/config/{:s} {:s}/Log/Template/STD/".format(avt_test_log_template, avt_installation_dir)
    mtp_mgmt_ctrl.cli_log_inf(cmd)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False

    avt_loop_pstates_handle = mtp_mgmt_ctrl.mtp_session_create()
    avt_pmm_getdata_handle = mtp_mgmt_ctrl.mtp_session_create()
    if not avt_loop_pstates_handle:
        mtp_mgmt_ctrl.cli_log_err("Failed to create new ssh connection for AVT pstates monitor", level=0)
        return False
    if not avt_pmm_getdata_handle:
        mtp_mgmt_ctrl.cli_log_err("Failed to create new ssh connection for AVT PPT_VALUE monitor", level=0)
        return False

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit the task to the executor
        avt_pmm_result = executor.submit(run_avt_pmm_getdata, mtp_mgmt_ctrl, avt_pmm_getdata_handle)
        #let pmm monitor start first, so that we can see CPU power change when stress
        time.sleep(10)
        avt_pstates_result = executor.submit(run_avt_loop_pstates, mtp_mgmt_ctrl, avt_loop_pstates_handle)
        avt_stress_result = executor.submit(run_avt_stress_system , mtp_mgmt_ctrl)

    avt_loop_pstates_handle.close()
    avt_pmm_getdata_handle.close()

    if not avt_stress_result.result():
        cpu_validation_result = False
        mtp_mgmt_ctrl.cli_log_err("AVT system stress test thread failed")
    if not avt_pstates_result.result():
        cpu_validation_result = False
        mtp_mgmt_ctrl.cli_log_err("AVT loop pstates thread failed")
    if not avt_pmm_result.result():
        cpu_validation_result = False
        mtp_mgmt_ctrl.cli_log_err("AVT pmm PPT_VALUE monitor thread failed")

    cmd = "cp {:s}/{:s} {:s}/{:s}".format(avt_installation_dir, avt_test_log_csv, mtp_script_dir, avt_test_log_csv+".log")
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False
    cmd = "mv {:s} {:s}".format(avt_pmm_log_csv, mtp_script_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False

    mtp_mgmt_ctrl.cli_log_inf("Test data saved to CSV file {:s}/{:s} and {:s}".format(mtp_script_dir, avt_test_log_csv+".log", os.path.basename(avt_pmm_log_csv)))
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Validation Test Finished".format("AMD CPU"), level=0)
    return cpu_validation_result

def mtp_mem_validation_test(mtp_mgmt_ctrl):
    """using the Stressful Application Test (stressapptest) for DDR stress test.
    same tool as SDD and EMMC validation, we will not specify '-f" option, it means no write data to disk thread. we focus on memory test here.
    and we only specify test time, not specify megabytes of ram to test option '-M', let to tool auto decide the maxiumum available memory for stress test.

    Args:
        mtp_mgmt_ctrl (_type_): mtp management controller instance
    """

    stress_test_time = 60  # Set stress test running time in seconds
    cmd = "/home/diag/diag/tools/stressapptest"
    tout = stress_test_time * 2.5
    cmd += " -s " + str(stress_test_time)
    mtp_mgmt_ctrl.cli_log_inf("MTP DDR Memory Validation Test Start")
    mtp_mgmt_ctrl.cli_log_inf(cmd)
    cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=tout)
    if not cmd_result:
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False
    cmd_result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
    if "Found 0 hardware incidents".lower() not in cmd_result.lower() or "Status: PASS - please verify no corrected errors".lower() not in cmd_result.lower():
        mtp_mgmt_ctrl.cli_log_err("Hardware Error Found By stressapptest Tool:")
        mtp_mgmt_ctrl.cli_log_err(cmd_result)
        return False
    bandwidth = ""
    for m in re.finditer(r'Stats:\s+Memory\s+Copy:\s+.*M\s+at\s+(.*)', cmd_result):
        bandwidth = m.group(1)
        break
    if bandwidth:
        mtp_mgmt_ctrl.cli_log_inf("MTP DDR Memory Validation Passed with data bandwidth {:s}".format(bandwidth))
    mtp_mgmt_ctrl.cli_log_inf("MTP DDR Memory Validation Test Finished")
    return True

def health_status(mtp_health):
    mtp_health.monitr_mtp_health(timeout=MTP_Const.MTP_HEALTH_MONITOR_CYCLE)

def mtp_usb_validation_test(mtp_mgmt_ctrl):
    """
    Matera MTP USB validation test
    assuming USB device will be /dev/sda, and partion is /dev/sda1

    Args:
        mtp_mgmt_ctrl (_type_): _description_
    """

    mtp_mgmt_ctrl.cli_log_inf("MTP USB Validation Test Start")
    usb_probe_result = libmtp_utils.mtp_usb_sanity_check(mtp_mgmt_ctrl)
    if not usb_probe_result:
        return False
    tout = MTP_Const.NIC_CON_CMD_DELAY
    cmd = "cd " + usb_probe_result["MOUNTPOINTS"]
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=tout):
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False

    cmd = "fsck -y /dev/sda1"
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd(cmd, timeout=tout):
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False

    stress_test_time = 60  # Set stress test running time in seconds
    cmd = "/home/diag/diag/tools/stressapptest -M 400 -f file.1 -f file.2"
    tout = stress_test_time * 2.5
    cmd += " -s " + str(stress_test_time)
    mtp_mgmt_ctrl.cli_log_inf(cmd)
    cmd_result = mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=tout)
    if not cmd_result:
        mtp_mgmt_ctrl.cli_log_err("Command {:s} Failed".format(cmd))
        return False
    cmd_result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
    if "Found 0 hardware incidents".lower() not in cmd_result.lower() or "Status: PASS - please verify no corrected errors".lower() not in cmd_result.lower():
        mtp_mgmt_ctrl.cli_log_err("Hardware Error Found By stressapptest Tool:")
        mtp_mgmt_ctrl.cli_log_err(cmd_result)
        return False

    pattern = r'Stats: File Copy: .* at (\d+\.+\d*MB\/s)'
    match_obj = re.search(pattern, cmd_result)
    file_cp_bw = ""
    if match_obj:
        file_cp_bw = match_obj.group(1)

    if not file_cp_bw:
        mtp_mgmt_ctrl.cli_log_inf("Did not get USB bandwidth data, Ignore")
    mtp_mgmt_ctrl.cli_log_inf("{:s} USB Drive {:s} Validation Pass with bandwidth {:s}".format(usb_probe_result["SIZE"], usb_probe_result["MODEL"], file_cp_bw))
    mtp_mgmt_ctrl.cli_log_inf("USB DriveValidation Test Finished")

    # clean up
    cmd = "rm -rf *"
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=tout):
        mtp_mgmt_ctrl.cli_log_inf("Clean up USB drive Command {:s} Failed, Ignore".format(cmd))
    cmd = "cd -; umount -f " + usb_probe_result["MOUNTPOINTS"]
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=tout):
        mtp_mgmt_ctrl.cli_log_inf("Clean up USB drive Command {:s} Failed, Ignore".format(cmd))

    return True

@parallelize.parallel_nic_using_ssh
def naples_get_nic_logfile(mtp_mgmt_ctrl, slot, mtp_para_test_list):
    ret = True
    mtp_para_test_list = mtp_para_test_list[slot]
    logfile_list = list()
    path = MTP_DIAG_Logfile.NIC_ONBOARD_ASIC_LOG_DIR
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if "SNAKE_HBM" in mtp_para_test_list:
        logfile_list.append(path+"snake_hbm.log")
        logfile_list.append("/data/nic_util/asicutil*log")
    if "SNAKE_PCIE" in mtp_para_test_list:
        logfile_list.append(path+"snake_pcie.log")
        logfile_list.append("/data/nic_util/asicutil*log")
    if "PRBS_ETH" in mtp_para_test_list:
        logfile_list.append(path+"prbs_eth.log")
        logfile_list.append("/data/nic_util/asicutil*log")
    if "SNAKE_ELBA" in mtp_para_test_list:
        if nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"snake_giglio.log")
        elif nic_type in ELBA_NIC_TYPE_LIST:
            logfile_list.append(path+"snake_elba.log")
        if mtp_mgmt_ctrl.mtp_get_mtp_type() != MTP_TYPE.MATERA:
            logfile_list.append("/data/nic_util/asicutil*log")
    if "ETH_PRBS" in mtp_para_test_list:
        if nic_type in CAPRI_NIC_TYPE_LIST:
            # uses DSP log
            pass
        elif nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"giglio_PRBS_MX.log")
        elif nic_type in ELBA_NIC_TYPE_LIST:
            logfile_list.append(path+"elba_PRBS_MX.log")
    if "ARM_L1" in mtp_para_test_list:
        if nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"giglio_arm_l1_test.log")
        elif nic_type in ELBA_NIC_TYPE_LIST:
            logfile_list.append(path+"elba_arm_l1_test.log")
    if "PCIE_PRBS" in mtp_para_test_list:
        if nic_type in CAPRI_NIC_TYPE_LIST:
            # uses DSP log
            pass
        elif nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"giglio_PRBS_PCIE.log")
        elif nic_type in ELBA_NIC_TYPE_LIST:
            logfile_list.append(path+"elba_PRBS_PCIE.log")
        if mtp_mgmt_ctrl.mtp_get_mtp_type() != MTP_TYPE.MATERA:
            logfile_list.append("/data/nic_util/asicutil*log")
    if "DDR_BIST" in mtp_para_test_list:
        logfile_list.append(path+"arm_ddr_bist_0.log")
        logfile_list.append(path+"arm_ddr_bist_1.log")

    if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_logfile(slot, logfile_list):
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Collecting MTP parallel test logfile failed")
        return False

    # for test in mtp_para_test_list:
    #     err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_mtp_para_err(slot, test)
    #     for err_msg in err_msg_list:
    #         mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_set_err_msg(err_msg)
    #         ret = False

    return ret

@parallelize.parallel_nic_using_ssh
def single_nic_dsp_test(mtp_mgmt_ctrl, slot, test, dsp, vmarg, swmtestmode):
    def get_diag_para_test_run_cmd(dsp, test, slot, opts, sn, mode):
        card_name = "NIC{:d}".format(slot+1)
        param = '"'
        if "SN" in opts and opts["SN"]:
            param += 'sn={:s} '.format(sn)
        if "SLOT" in opts and opts["SLOT"]:
            param += 'slot={:d}'.format(slot+1)
        if "MODE" in opts and opts["MODE"]:
            param += 'mode={:s}'.format(mode)
        param += '"'
        return libmfg_utils.diag_para_run_cmd(card_name, dsp, test, param)

    def get_diag_para_test_errcode_cmd(dsp, slot, opts):
        card_name = "NIC{:d}".format(slot+1)
        return libmfg_utils.diag_para_errcode_cmd(card_name, dsp)

    diag_test_timeout = MTP_Const.DIAG_MEM_DDR_STRESS_TEST_TIMEOUT if dsp == "MEM" and test == "DDR_STRESS" else MTP_Const.DIAG_PARA_TEST_TIMEOUT
    opts = {"NIC_NAME": True, "SN": False, "SLOT": False}
    mode = libmfg_utils.get_mode_param(mtp_mgmt_ctrl, slot, test)
    diag_cmd = get_diag_para_test_run_cmd(dsp, test, slot, opts, None, mode)
    rslt_cmd = get_diag_para_test_errcode_cmd(dsp, slot, opts)

    card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if dsp == "NIC_ASIC" and test == "ETH_PRBS" and card_type in (NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT):
        # external loopback for P2C
        if vmarg == Voltage_Margin.normal:
            diag_cmd += " -p 'int_lpbk=0'"
        # internal loopback for 2C/4C
        else:
            diag_cmd += " -p 'int_lpbk=1'"

    ret, err_msg_list = mtp_mgmt_ctrl.mtp_run_diag_test_para(slot, diag_cmd, rslt_cmd, test, timeout=diag_test_timeout)

    if test == "I2C":
        mtp_mgmt_ctrl.mtp_nic_i2c_bus_scan(slot)

    # Collect NIC onboard logfiles
    asic_dir_logfile_list = []
    path = MTP_DIAG_Logfile.NIC_ONBOARD_ASIC_LOG_DIR
    if dsp == "NIC_ASIC" and test == "PCIE_PRBS" and card_type in ELBA_NIC_TYPE_LIST:
        asic_dir_logfile_list.append(path+"elba_PRBS_PCIE.log")
    if dsp == "NIC_ASIC" and test == "ETH_PRBS" and card_type in ELBA_NIC_TYPE_LIST:
        asic_dir_logfile_list.append(path+"elba_PRBS_MX.log")
    if dsp == "NIC_ASIC" and test == "L1" and card_type in ELBA_NIC_TYPE_LIST:
        asic_dir_logfile_list.append(path+"elba_arm_l1_test.log")

    if dsp == "NIC_ASIC" and test == "PCIE_PRBS" and card_type in GIGLIO_NIC_TYPE_LIST:
        asic_dir_logfile_list.append(path+"giglio_PRBS_PCIE.log")
    if dsp == "NIC_ASIC" and test == "ETH_PRBS" and card_type in GIGLIO_NIC_TYPE_LIST:
        asic_dir_logfile_list.append(path+"giglio_PRBS_MX.log")
    if dsp == "NIC_ASIC" and test == "L1" and card_type in GIGLIO_NIC_TYPE_LIST:
        asic_dir_logfile_list.append(path+"giglio_arm_l1_test.log")
    if dsp == "MEM" and test == "DDR_STRESS":
        asic_dir_logfile_list.append("/data/nic_util/" + "stressapptest.log")

    if asic_dir_logfile_list:
        if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_logfile(slot, asic_dir_logfile_list):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Collecting NIC onboard asic logfile for ({:s}, {:s}) test failed".format(dsp, test))
            ret = False

    if dsp == "NIC_ASIC" and test == "L1":
        pass_count, log_err_msg_list = mtp_mgmt_ctrl.mtp_nic_retrieve_arm_l1_err(sn)
        number_of_arm_l1_tests = 2
        if pass_count != number_of_arm_l1_tests:
            err_msg_list.append("ARM L1 Sub Test only passed: {:d}".format(pass_count))
            ret = False
        if log_err_msg_list:
            err_msg_list += log_err_msg_list

    # only display first 3 and last 3 error messages
    if len(err_msg_list) < 6:
        err_msg_disp_list = err_msg_list
    else:
        err_msg_disp_list = err_msg_list[:3] + err_msg_list[-3:]
    for err_msg in err_msg_disp_list:
        mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_set_err_msg(err_msg)

    return ret


def main():
    parser = argparse.ArgumentParser(description="Single MTP Screen Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--stop_on_error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--stage", "--corner", type=FF_Stage, help="diagnostic environment condition", choices=list(FF_Stage), default=FF_Stage.FF_SRN)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip_test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("--skip_slots", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--mtpsn", help="MTP SN, like FLM0021330001, etc", default="")
    parser.add_argument("--mtpmac", help="MTP MAC, like BBBBBBBBBBAF, etc", default="")
    parser.add_argument("--mtp_type", help="pass mtp type for test", nargs="?", default="", type=str, required=True)
    parser.add_argument("--l1_seq", help="asic L1 run under sequence mode", action='store_true')
    args = parser.parse_args()

    mtp_id = "MTP-000"
    mtp_sn = ""
    mtp_mac = ""
    stop_on_err = False
    verbosity = False
    swm_lp_boot_mode = False
    l1_sequence = False
    if args.mtpid:
        mtp_id = args.mtpid
        mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    if args.stop_on_error:
        stop_on_err = True
    if args.verbosity:
        verbosity = True
    if args.stage:
        stage = args.stage
    if args.swm:
        swmtestmode = args.swm
        print(" SWMTESTMODE=" + str(swmtestmode))
    if args.mtpsn:
        mtp_sn = args.mtpsn
    if args.mtpmac:
        mtp_mac = str(args.mtpmac).upper().replace(':','')
    if args.l1_seq:
        l1_sequence = True
    if args.mtp_type:
        mtp_type = args.mtp_type

    fail_step = ""
    fail_desc = ""

    low_temp_threshold, high_temp_threshold = libmfg_utils.pick_temperature_thresholds(stage)
    fanspd = libmfg_utils.pick_fan_speed(stage)
    vmarg = Voltage_Margin.normal

    # load the mtp config
    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/mtp_screen_chassis_cfg.yaml"))
    if args.mtpcfg:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/"+args.mtpcfg))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)

    # find the mtp management config based on the mtpid
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")

    # find the apc config based on the mtpid
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    # set skip slots when pass in skip_slots
    if len(args.skip_slots) > 0 and not mtp_cfg_db.set_mtp_slots_to_skip(mtp_id, args.skip_slots):
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to set skip slots")

    # find any slots to skip
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id,
                             sys.stdout,
                             None,
                             [],
                             None,
                             mgmt_cfg = mtp_mgmt_cfg,
                             apc_cfg = mtp_apc_cfg,
                             slots_to_skip = mtp_slots_to_skip,
                             dbg_mode = verbosity)
    mtp_mgmt_ctrl._mtp_sn = mtp_sn
    mtp_mgmt_ctrl._mtp_mac = mtp_mac

    # logfiles
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=stage)

    try:
        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, stage=stage, skip_test_list=args.skip_test):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
            return

        if MTP_HEALTH_MONITOR:
            thread_health = threading.Thread(target=health_status, args=(mtp_mgmt_ctrl.get_mtp_health_monitor(),))
            thread_health.start()

        # Set Naples25SWM test mode
        mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        pass_nic_list = list()
        fail_nic_list = list()
        skip_nic_list = list()
        rs = True
        mac = ""
        fail_desc = ""

        # Add failed slots from toplevel
        if args.fail_slots:
            for slot in args.fail_slots:
                fail_nic_list.append(int(slot))

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            if not nic_prsnt_list[slot]:
                continue
            if slot not in pass_nic_list:
                pass_nic_list.append(slot)

        nic_test_history = {slot: [] for slot in pass_nic_list}

        @parallelize.parallel_nic_using_ssh
        def update_nic_test_history(mtp_mgmt_ctrl, slot, test):
            nic_test_history[slot].append(test)

        def get_slots_of_type(nic_type, except_type=[]):
            return mtp_mgmt_ctrl.get_slots_of_type(nic_type, pass_nic_list, except_type)

        def run_mtp_test(nic_list_orig, test, dsp=str(stage), *test_args, **test_kwargs):
            nic_list = nic_list_orig[:]

            if not nic_list:
                return []

            if test in args.skip_test:
                mtp_mgmt_ctrl.cli_log_wrn(MTP_DIAG_Report.NIC_DIAG_TEST_SKIPPED.format(mtp_sn, stage, test), level=0)
                return nic_list

            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(mtp_sn, stage, test), level=0)

            if DRY_RUN:
                ret = []
            elif test == "MTP_CONNECT":
                ret = mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True)
                fail_desc = "MTP connection fails"
            elif test == "MTP_FRU_PROG":
                ret = program_mtp_fru(mtp_mgmt_ctrl)
                fail_desc = "MTP program FRU fails"
            elif test == "SSD_BENCHMARK":
                ret = mtp_nvme_ssd_validation_test(mtp_mgmt_ctrl)
                fail_desc = "MTP M.2 NVME SSD validation test failed"
            elif test == "CPU_BENCHMARK":
                ret = mtp_cpu_validation_test(mtp_mgmt_ctrl)
                fail_desc = "MTP CPU validation test failed"
            elif test == "MEM_BENCHMARK":
                ret = mtp_mem_validation_test(mtp_mgmt_ctrl)
                fail_desc = "MTP DDR Memory validation test failed"
            elif test == "USB_BENCHMARK":
                ret = mtp_usb_validation_test(mtp_mgmt_ctrl)
                fail_desc = "MTP USB validation test failed"
            elif test == "VDDIO_MEM_MARGIN_LOW":
                ret = mtp_mgmt_ctrl.mtp_set_mem_vddio(nic_list, margin=-5)
                fail_desc = "MTP set vddio mem margin low test failed"
            elif test == "VDDIO_MEM_MARGIN_HIGH":
                ret = mtp_mgmt_ctrl.mtp_set_mem_vddio(nic_list, margin=5)
                fail_desc = "MTP set vddio mem margin high test failed"
            elif test == "VDDIO_MEM_MARGIN_NORMAL":
                ret = mtp_mgmt_ctrl.mtp_set_mem_vddio(nic_list, margin=0)
                fail_desc = "MTP set vddio mem margin normal test failed"
            elif test == "I2C_DEVICE":
                ret = mtp_mgmt_ctrl.mtp_i2c_show(nic_list)
                fail_desc = "MTP show i2c device test failed"
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown test '{:s}'".format(test))
                ret = False

            if not ret:
                rlist = nic_list
            else:
                rlist = []

            for slot in rlist:
                if slot in nic_list_orig:
                    nic_list_orig.remove(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)

            duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
            if rlist:
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(mtp_sn, stage, test, "FAILED", duration), level=0)
            else:
                mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(mtp_sn, stage, test, duration), level=0)

            if rlist and args.stop_on_error:
                mtp_mgmt_ctrl.cli_log_err("stop_on_err raised")
                raise Exception

            return rlist

        def run_nic_test(nic_list_orig, test, dsp=str(stage), *test_args, **test_kwargs):
            nic_list = nic_list_orig[:]

            if test in args.skip_test:
                test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, dsp, test)
                return nic_list

            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            test_utils.test_start_nic_log_message(mtp_mgmt_ctrl, nic_list, dsp, test)

            if DRY_RUN:
                rlist = []
            elif test == "SLOTS_FULL_CHECK":
                rlist = check_fully_populated(mtp_mgmt_ctrl, nic_list)
                fail_desc = "MTP not able to detect 10 NICs. (missing slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "SLOTS_TYPE_CHECK":
                rlist = check_nic_type(mtp_mgmt_ctrl, nic_list)
                fail_desc = "MTP not able to detect 10 ORTANO2 NICs. (slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "NIC_PWRCYC":
                rlist = mtp_mgmt_ctrl.mtp_power_cycle_nic(nic_list)
            elif test == "NIC_DIAG_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, skip_test_list=args.skip_test, vmargin=vmarg, **test_kwargs)
                fail_desc = "Initialize NIC diag environment failed"
            elif test == "UART":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_nic_console_access(nic_list)
            elif test == "NIC_JTAG":
                rlist = mtp_mgmt_ctrl.mtp_check_nic_jtag(nic_list)
                fail_desc = "Fail to Pre check(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "NIC_POWER":
                rlist = mtp_mgmt_ctrl.mtp_check_nic_list_pwr_status(nic_list, test)
                fail_desc = "Fail to Pre check(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "NIC_STATUS":
                rlist = mtp_mgmt_ctrl.mtp_check_nic_list_status(nic_list)
                fail_desc = "Fail to Pre check(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "NIC_DIAG_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_diag_boot(nic_list)
                fail_desc = "Fail to Pre check(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "NIC_CPLD":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_cpld_console(nic_list, timestamp_check=False) # cant read timestamp from smb
                fail_desc = "Fail to Pre check(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "NIC_TYPE":
                rlist = mtp_mgmt_ctrl.mtp_nic_type_test(nic_list)
                fail_desc = "Fail to Pre check(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "SNAKE_ELBA":
                update_nic_test_history(mtp_mgmt_ctrl, nic_list, test)
                rlist = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(nic_list, test, vmarg)
            elif test == "PCIE_PRBS":
                update_nic_test_history(mtp_mgmt_ctrl, nic_list, test)
                rlist = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(nic_list, test, vmarg)
                fail_desc = "Fail to PCIE_PRBS check(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "L1_SETUP":
                rlist = mtp_mgmt_ctrl.mtp_l1_setup(nic_list)
                fail_desc = "MTP L1 setup test failed"
            elif test == "L1":
                rlist = run_j2c_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, stage, test_kwargs["l1_sequence"])
                fail_desc = "Fail to L1 check(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "I2C":
                rlist = single_nic_dsp_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                fail_desc = "Fail to run I2C(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "SEC_KEY_PROG":
                rlist = mtp_mgmt_ctrl.mtp_program_nic_sec_key(nic_list)
                fail_desc = "Fail to SEC_KEY_PROG(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            elif test == "ASIC_LOG_SAVE":
                rlist = naples_get_nic_logfile(mtp_mgmt_ctrl, nic_list, nic_test_history)
                fail_desc = "Fail to Collect ASIC Log(slots: {:s})".format(",".join([str(slot+1) for slot in rlist]))
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown test '{:s}'".format(test))
                rlist = nic_list
            # catch bad return value
            if not isinstance(rlist, list):
                mtp_mgmt_ctrl.cli_log_err("Test {} failed with '{}', expected slot list".format(test, repr(rlist)))
                rlist = nic_list[:]

            for slot in rlist:
                # mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                if slot in nic_list_orig:
                    nic_list_orig.remove(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)

            duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
            test_utils.test_fail_nic_log_message(mtp_mgmt_ctrl, rlist, dsp, test, start_ts, swmtestmode)
            test_utils.test_pass_nic_log_message(mtp_mgmt_ctrl, nic_list_orig, dsp, test, start_ts, swmtestmode)

            if rlist and args.stop_on_error:
                mtp_mgmt_ctrl.cli_log_err("stop_on_err raised")
                raise Exception

            return rlist

        if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.MATERA:
            run_mtp_test(pass_nic_list, "USB_BENCHMARK")
            run_mtp_test(pass_nic_list, "SSD_BENCHMARK")
            run_mtp_test(pass_nic_list, "CPU_BENCHMARK")
            run_mtp_test(pass_nic_list, "MEM_BENCHMARK")
            run_mtp_test(pass_nic_list, "VDDIO_MEM_MARGIN_LOW")
            run_mtp_test(pass_nic_list, "VDDIO_MEM_MARGIN_HIGH")
            run_mtp_test(pass_nic_list, "VDDIO_MEM_MARGIN_NORMAL")
            run_mtp_test(pass_nic_list, "I2C_DEVICE")
            run_nic_test(pass_nic_list, "SLOTS_FULL_CHECK")
            run_nic_test(pass_nic_list, "NIC_PWRCYC")
            run_nic_test(pass_nic_list, "UART")
            run_nic_test(pass_nic_list, "NIC_DIAG_INIT", nic_util=True)
            run_nic_test(pass_nic_list, "NIC_TYPE")
            run_nic_test(pass_nic_list, "NIC_POWER")
            run_nic_test(pass_nic_list, "NIC_JTAG")
            run_nic_test(pass_nic_list, "NIC_DIAG_BOOT")
            run_nic_test(pass_nic_list, "NIC_CPLD")
            run_nic_test(pass_nic_list, "I2C", "I2C")
            run_nic_test(pass_nic_list, "PCIE_PRBS", "ASIC")
            run_nic_test(pass_nic_list, "SNAKE_ELBA", "ASIC")
            run_nic_test(pass_nic_list, "NIC_DIAG_INIT")
            run_nic_test(pass_nic_list, "ASIC_LOG_SAVE")
            run_nic_test(pass_nic_list, "L1_SETUP")
            run_nic_test(pass_nic_list, "L1", "ASIC", l1_sequence=l1_sequence)

        else:
            run_mtp_test(pass_nic_list, "MTP_FRU_PROG")
            run_nic_test(pass_nic_list, "SLOTS_FULL_CHECK")
            run_nic_test(pass_nic_list, "SLOTS_TYPE_CHECK")
            run_nic_test(pass_nic_list, "NIC_DIAG_INIT", swm_lp=swm_lp_boot_mode, nic_util=True)
            run_nic_test(pass_nic_list, "NIC_TYPE")
            run_nic_test(pass_nic_list, "NIC_POWER")
            run_nic_test(pass_nic_list, "NIC_JTAG")
            run_nic_test(pass_nic_list, "NIC_STATUS")
            run_nic_test(pass_nic_list, "NIC_DIAG_BOOT")
            run_nic_test(pass_nic_list, "NIC_CPLD")
            run_nic_test(pass_nic_list, "PCIE_PRBS", "ASIC")
            run_nic_test(pass_nic_list, "L1", "ASIC", l1_sequence=l1_sequence)
            run_nic_test(pass_nic_list, "NIC_PWRCYC")
            run_nic_test(pass_nic_list[:1], "SEC_KEY_PROG") # only program one slot
        mtp_mgmt_ctrl.mtp_mgmt_diag_history_disp() # log the diag test history

        # clear the diag test history
        if not stop_on_err:
            mtp_mgmt_ctrl.mtp_mgmt_diag_history_clear()

        testlog.gather_dsp_logs(mtp_mgmt_ctrl, vmarg)

        # clean up logfiles for the next run
        cmd = "cleanup.sh"
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

        if MTP_HEALTH_MONITOR:
            mtp_mgmt_ctrl.get_mtp_health_monitor().set_event_status()
            thread_health.join()

        mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Test Complete\n", level=0)

        for slot in pass_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

        for slot in fail_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_err("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

        #write final result
        mtp_mgmt_ctrl.cli_log_inf("##########  MFG {:s} Test Summary  ##########".format("MTP_SCREEN"))
        mtp_mgmt_ctrl.cli_log_inf("---------- {:s} Report: ----------".format(mtp_id))

        #if len(fail_nic_list) != 0 or len(pass_nic_list) != 10 or len(fail_desc) > 0:
        if fail_nic_list: # ignore full 10 slots check for CI/CD
            mtp_mgmt_ctrl.cli_log_err("[{:s}] {:s} FINAL_SRN_MTP_RESULT_FAIL --> {:s}".format(mtp_id, mtp_sn, fail_desc))
        else:
            mtp_mgmt_ctrl.cli_log_inf("[{:s}] {:s} FINAL_SRN_MTP_RESULT_PASS".format(mtp_id, mtp_sn))

        mtp_mgmt_ctrl.cli_log_inf("--------- {:s} Report End --------\n".format(mtp_id))

        return True

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        # err_msg = str(e)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)
        if MTP_HEALTH_MONITOR and 'thread_health' in locals():
            mtp_mgmt_ctrl.get_mtp_health_monitor().set_event_status()
            thread_health.join()

    mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_PASS, open_file_track_list)


if __name__ == "__main__":
    main()
