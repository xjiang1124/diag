#!/usr/bin/env python

import sys
import os
import time
import re
import argparse
import threading
import traceback
import csv

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
import testlog
import mtp_diag_regression as diag_reg
from emmc_test_parameters import test2args as emmctest2args
from diag_screening_ddr import get_test_arguments
from diag_screening_ddr import args2optionstring
from libdefs import MTP_Const
from libdefs import NIC_Type
from libdefs import MTP_ASIC_SUPPORT
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import Swm_Test_Mode
from libdefs import MFG_DIAG_CMDS
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Path
from libdefs import Voltage_Margin
from libdefs import MFG_DIAG_SIG
from libdiag_db import diag_db
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libmfg_cfg import *
from collections import OrderedDict

def save_test_data2csv_file(mtp_mgmt_ctrl=None, nic_test_data=None, csvfilename="emmc_validation.csv.log"):
    """
    covert the nic test data which is a dict to two two dimensional table as raw data, 
    calcluate the min, max and avg value as test results, then store them in the specified csv file 
    """

    if not nic_test_data:
        return None
    if not mtp_mgmt_ctrl:
        return None

    # calculate cols of the raw_data_table
    HEADER_COLS = 4 # number of cols header
    cols = HEADER_COLS
    max_iter = 0
    ite = 0
    for k, v in nic_test_data.items():
        if not v:
            continue
        ite += 1
        if len(v) > max_iter:
            max_iter = len(v)
    for _ in range(1, ite+1):
        cols += max_iter

    # calculate the rows of the raw_data_table
    rows_head = 0 
    rows_high = 0
    rows_low = 0
    for k, v in nic_test_data.items():
        if not v: 
            continue
        for item in v:
            m_rows_head = 0
            m_rows_high = 0
            m_rows_low = 0
            for kk, vv in item.items():
                if kk == "head":
                    m_rows_head += len(vv)
                if kk == "data":
                    # print(vv["high"])
                    # print(vv["low"])
                    m_rows_high += len(vv["high"])
                    m_rows_low += len(vv["low"])
            if m_rows_head > rows_head:
                rows_head = m_rows_head
            if m_rows_high > rows_high:
                rows_high = m_rows_high
            if m_rows_low > rows_low:
                rows_low = m_rows_low
    rows_head += 1  # add 1 row to head for Units, iterations, etc
    rows_high *= 2
    rows_low *= 2
    rows = rows_head + rows_high + rows_low

    # creating an empty raw_data_table
    raw_data_table = []
    for _ in range(rows):
        row = []
        for _ in  range(cols):
            row.append("")
        raw_data_table.append(row)

    # Fill raw_data_table header
    running_slot =0 
    for k, v in nic_test_data.items():
        if not v:
            continue
        col_index = max_iter * int(running_slot) + 4
        for row_index, vv in enumerate(v[0]["head"].keys()):
            raw_data_table[row_index][0] = vv
        for row_index, vv in enumerate(v[0]["head"].values()):
            raw_data_table[row_index][col_index] = vv
        running_slot +=1
    raw_data_table[rows_head-1][0]  = "Vmargin"
    raw_data_table[rows_head-1][1]  = "Test Config"
    raw_data_table[rows_head-1][2]  = "IOPS/BW"
    raw_data_table[rows_head-1][3]  = "Units"

    # Fill raw_data_table with data:
    running_slot =0 
    for k, v in nic_test_data.items():
        if not v:
            continue
        for ite, item in enumerate(v):
            col_index = ite +  max_iter * int(running_slot) + 4
            raw_data_table[rows_head-1][col_index] = "Iteration" + str(ite+1)
            for kk, vv in item["data"].items():
                if kk == "high":
                    for r in range((rows_high)):
                        row_index = r+rows_head
                        raw_data_table[row_index][0] = kk
                        raw_data_table[row_index][1] = item["data"][kk].keys()[r//2]
                        if r % 2 == 0:
                            raw_data_table[row_index][2] = "IOPS"
                            #raw_data_table[row_index][3] = "K"
                            raw_data_table[row_index][3] = ""
                            if item["data"][kk].keys()[r//2] == "STRESSAPPTEST":
                                raw_data_table[row_index][2] = ""
                                raw_data_table[row_index][3] = "P/F"
                            # print("-"*10)
                            # print(row_index,col_index)
                            raw_data_table[row_index][col_index] = item["data"][kk].values()[r//2][0]
                        if r % 2 == 1:
                            raw_data_table[row_index][2] = "BW"
                            raw_data_table[row_index][3] = "MB/s"
                            if item["data"][kk].keys()[r//2] == "STRESSAPPTEST":
                                raw_data_table[row_index][2] = ""
                                raw_data_table[row_index][3] = "MB/s"
                            # print("+"*10)
                            # print(row_index,col_index)
                            raw_data_table[row_index][col_index] = item["data"][kk].values()[r//2][1]

                if kk == "low":
                    for r in range(rows_low):
                        row_index = r+rows_head+rows_high
                        raw_data_table[row_index][0] = kk
                        raw_data_table[row_index][1] = item["data"][kk].keys()[r//2]
                        if r % 2 == 0:
                            raw_data_table[row_index][2] = "IOPS"
                            #raw_data_table[row_index][3] = "K"
                            raw_data_table[row_index][3] = ""
                            if item["data"][kk].keys()[r//2] == "STRESSAPPTEST":
                                raw_data_table[row_index][2] = ""
                                raw_data_table[row_index][3] = "P/F"
                            # print("-"*10)
                            # print(row_index,col_index)
                            raw_data_table[row_index][col_index] = item["data"][kk].values()[r//2][0]
                        if r % 2 == 1:
                            raw_data_table[row_index][2] = "BW"
                            raw_data_table[row_index][3] = "MB/s"
                            if item["data"][kk].keys()[r//2] == "STRESSAPPTEST":
                                raw_data_table[row_index][2] = ""
                                raw_data_table[row_index][3] = "MB/s"
                            # print("+"*10)
                            # print(row_index,col_index)
                            raw_data_table[row_index][col_index] = item["data"][kk].values()[r//2][1]
        running_slot += 1

    # Calcalue min, max and average from all test iterations
    results_table = []
    for row_i, row in enumerate(raw_data_table):
        results_row = []
        for col_i, col in enumerate(row):
            if row_i < rows_head-1:
                if col_i < HEADER_COLS:
                    results_row.append(col)
                elif (col_i - HEADER_COLS) % max_iter ==0:
                    results_row.append(col)
                    results_row.append("")
                    results_row.append("")
                else:
                    continue
            elif row_i == rows_head-1:
                if col_i < HEADER_COLS:
                    results_row.append(col)
                elif (col_i - HEADER_COLS) % max_iter ==0:
                    results_row.append("AVG")
                    results_row.append("MIN")
                    results_row.append("MAX")
                else:
                    continue
            else:
                if col_i < HEADER_COLS:
                    results_row.append(col)
                elif (col_i - HEADER_COLS) % max_iter ==0:
                    # cal min, max and average
                    valid_data_list = []
                    for data in row[col_i:(col_i+max_iter)]:
                        if data:
                            valid_data_list.append(data)
                    if "PASS" in valid_data_list or "FAIL" in valid_data_list:
                        pass_count = valid_data_list.count("PASS")
                        fail_count = valid_data_list.count("FAIL")
                        if fail_count:                            
                            results_row.append("{:s}PASS{:s}FAIL".format(str(pass_count), str(fail_count)))
                            results_row.append("{:s}PASS{:s}FAIL".format(str(pass_count), str(fail_count)))
                            results_row.append("{:s}PASS{:s}FAIL".format(str(pass_count), str(fail_count)))
                        else:
                            results_row.append("{:s}PASS".format(str(pass_count)))
                            results_row.append("{:s}PASS".format(str(pass_count)))
                            results_row.append("{:s}PASS".format(str(pass_count)))
                    else:
                        valid_data_list = [float(i) for i in valid_data_list]
                        results_row.append(str(sum(valid_data_list) / len(valid_data_list)))
                        results_row.append(str(min(valid_data_list)))
                        results_row.append(str(max(valid_data_list)))
                else:
                    continue
        results_table.append(results_row)  

    finally_table = results_table + [[]] + [["RAW DATA BELOW"]] + raw_data_table

    # print the finnal table in the log file 
    for i in finally_table:
        row = ""
        for j in i:
            row += j + ","
        mtp_mgmt_ctrl.cli_log_inf(row.strip(","))
    with open(csvfilename, 'wb') as csvfile:
        mywriter = csv.writer(csvfile)
        mywriter.writerows(finally_table)
    return csvfilename

def diag_para_emmc_validation_test(mtp_mgmt_ctrl, nic_type, nic_list, emmc_suite, stop_on_err, aapl, swmtestmode):
    """
    This funtion run EMMC Validation test in parallel on individual NIC card by calling single_nic_emmc_validation_test in threads
    """

    if aapl == False:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} EMMC Validation Test Start".format(nic_type), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} EMMC Validation Test Start with aapl initiaize".format(nic_type), level=0)
    
    # swmtestmode parameter is a placehold for now, just print out it's pass in value for now
    mtp_mgmt_ctrl.cli_log_inf("MTP {:} pass in swmtestmode value is {:s}".format(nic_type, swmtestmode), level=0)

    iterations = emmc_suite["ITER"]
    fail_list = list()
    new_nic_list = nic_list[:]
    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
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
        mtp_mgmt_ctrl.cli_log_inf("--*" * 30)
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} EMMC Validation Test Iteration {:d}".format(nic_type, idx), level=0)
        # power cycle every iteration
        if idx > 1: 
            mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Calling MTP_NIC_DIAG_INIT To Power Cycle NIC Card and Re-init it ".format(nic_type), level=0)
            if not mtp_mgmt_ctrl.mtp_nic_diag_init(new_nic_list, nic_util=True, stop_on_err=stop_on_err):
                mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                for slot in new_nic_list:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        nic_test_rslt_list[slot] = False
                        if slot not in fail_list:
                            fail_list.append(slot)
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_err("STOP_ON_ERR asserted when diag initial")
                    raise Exception
        # Run Test
        for slot in new_nic_list[:]:
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                nic_test_rslt_list[slot] = False
                if slot not in fail_list:
                    fail_list.append(slot)
                continue
            nic_thread = threading.Thread(target = single_nic_emmc_validation_test, args = (mtp_mgmt_ctrl, slot, test_steps, nic_test_rslt_list, nic_test_data, stop_on_err))
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)

        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    ret = nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(5)

        for slot in new_nic_list[:]:
            if not nic_test_rslt_list[slot]:
                if slot not in fail_list:
                    fail_list.append(slot)
                if stop_on_err:
                    if stop_on_err:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                        raise Exception
                new_nic_list.remove(slot)

    savedfile = save_test_data2csv_file(mtp_mgmt_ctrl, nic_test_data)
    if savedfile:
        mtp_mgmt_ctrl.cli_log_inf("Test data saved to CSV file {:s}".format(savedfile))

    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))

    if aapl == False:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel DSP Test Complete\n".format(nic_type), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel PRBS Test Complete\n".format(nic_type), level=0)

    return fail_list

def single_nic_emmc_validation_test(mtp_mgmt_ctrl, slot, test_steps, nic_test_rslt_list, nic_test_data, stop_on_err):
    """
    this function run emmc performance test commands passed in from test_steps parameter
    mark failed NIC cards with passed in nic_test_rslt_list parameter
    and put parsed emmc performace data into passed in dict type parameter nic_test_data
    """

    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot) # get the PN format like this 68-0015-02 01
    pn = pn.split()[0]
    emmc_test_data = {}

    # Routine Check
    head_data = single_nic_emmc_validation_test_precheck(mtp_mgmt_ctrl, slot, sn)
    if not head_data:
        nic_test_rslt_list[slot] = False
        if stop_on_err:
            return

    # run test steps under both vmargin high and vmargin low for all Normal temperature, Low temperature and High temperature
    for vmargin in [Voltage_Margin.high, Voltage_Margin.low]:
        # set vmargin to low or high 
        # (EMMC_PRE_SET, NIC_VMARG) START
        test = "NIC_VMARG"
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, "EMMC_PRE_SET", test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        if not mtp_mgmt_ctrl.mtp_set_nic_vmarg(slot, vmargin):
            nic_test_rslt_list[slot] = False
        if not mtp_mgmt_ctrl.mtp_nic_display_voltage(slot):
            nic_test_rslt_list[slot] = False
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, "EMMC_PRE_SET", test, duration)) 
        # (EMMC_PRE_SET, NIC_VMARG) END

        # Sleep 30 seconds before emmc performace test
        time.sleep(30)

        # Start emmc performace test commands
        fio_stressapp_data = {}
        fio_stressapp_order_data = OrderedDict()
        for test in test_steps:
            cmds = ["cd /data/nic_util/", "rm -rf Random*", "rm -rf Sequen*"]
            tout = MTP_Const.NIC_CON_CMD_DELAY
            argsdict = get_test_arguments(test, pn, emmctest2args)
            if not argsdict:
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Test Step {:s} Failed".format(sn, test))
                nic_test_rslt_list[slot] = False
            cmd_options =  args2optionstring(argsdict)
            if "FIO_" in test:
                cmd = "./fio "
            elif "STRESSAPPTEST" in test:
                cmd = "./stressapptest_arm "
                tout = int(argsdict["-s"]) + 300
            else:
                return 
            cmd += cmd_options
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, cmd)
            cmds.append(cmd)
            cmd_result = mtp_mgmt_ctrl.mtp_exec_nic_cmds_get_lastcmd_info(slot, cmds, tout)
            if not cmd_result:
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Command {:s} Failed".format(sn, cmd))
                nic_test_rslt_list[slot] = False
                continue
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
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} IOPS={:s}, BW={:s}MiB/s".format(test, iops, bw))
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
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} Status:{:s}, File Copy At {:s}MB/s".format(test, res, file_cp_bw))

        # sort data
        for key in sorted(fio_stressapp_data.keys()):
            fio_stressapp_order_data[key] = fio_stressapp_data[key]
        emmc_test_data[vmargin] = fio_stressapp_order_data

        #post test command
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} Execute Post Test Commands".format(sn))
        cmd = "dmesg | grep mmc"
        result = mtp_mgmt_ctrl.mtp_exec_nic_cmd_get_info(slot, cmd)
        if not result:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Command {:s} Failed".format(sn, cmd))
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, result)

    nic_test_data[slot].append({"head": head_data, "data": emmc_test_data})
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} Run EMMC bench mark ".format(sn))

def single_nic_emmc_validation_test_precheck(mtp_mgmt_ctrl, slot, sn):
    """
    this function run some routine commands which will collect the emmmc basic inforation
    return these info in a dict
    """
    
    basic_info = OrderedDict()
    basic_info["SlotID"] = "Slot" + str(int(slot)+1)

    basic_info["NIC_Serial_Number"] = sn
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Getting EMMC PN and Capacity".format(sn))

    cmd = "dmesg | grep mmc"
    # if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_info(cmd):
    # #if not mtp_mgmt_ctrl.mtp_nic_fst_exec_cmd(slot, cmd):
    result = mtp_mgmt_ctrl.mtp_exec_nic_cmd_get_info(slot, cmd)
    if not result:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Command {:s} Failed".format(sn, cmd))
        return False
    #mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, result)
    matches = re.findall(r'mmcblk0:\s+mmc0:\d+\s+(\w+)\s+(\d+\.\d+)\s+GiB', result)
    if not matches:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Failed to Get EMMC PN and Capacity, Match Failed".format(sn))
        return False
    basic_info["EMMC Part Number"] = matches[0][0]
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "Got EMMC Part Number: {:s}".format(matches[0][0]))
    basic_info["Capacity"] = matches[0][1]
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "Got EMMC Capacity: {:s}".format(matches[0][1]))

    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Getting EMMC fw version".format(sn))
    cmd = "mmc extcsd read /dev/mmcblk0 | grep Firmware"
    result = mtp_mgmt_ctrl.mtp_exec_nic_cmd_get_info(slot, cmd)
    if not result:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Command {:s} Failed".format(sn, cmd))
        return False
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, result)
    emmc_fw_version = result.split(":")[-1].strip()
    if not emmc_fw_version:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Failed to Get EMMC Firmware Version, using placehold NA ".format(sn))
        emmc_fw_version = "NA"
    basic_info["eMMC Firmware Version"] = emmc_fw_version
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "Got EMMC Firmware Version: {:s}".format(emmc_fw_version))
    
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Getting NIC linux rev".format(sn))
    cmd = "fwupdate -l | grep -A20 diagfw | grep software_version"
    result = mtp_mgmt_ctrl.mtp_exec_nic_cmd_get_info(slot, cmd)
    if not result:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Command {:s} Failed".format(sn, cmd))
        return False
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, result)
    matches = re.findall(r'"software_version": "(.*)",', result)
    if not matches:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} -> Failed to Get NIC linux rev, Match Failed".format(sn))
        return False
    basic_info["NIC Linux Rev"] = matches[0][0]
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "Got NIC linux rev: {:s}".format(matches[0][0]))

    return basic_info

def main():
    parser = argparse.ArgumentParser(description="Single MTP EMMC Validation Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--stop_on_error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("-stage", "--stage", type=FF_Stage, help="diagnostic environment condition", choices=list(FF_Stage), default=FF_Stage.FF_P2C)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--fail-slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("-cfg", "--cfgyaml", help="Test case config file for EMMC test suite, default to %(default)s", default="config/emmc_test_suite.yaml")
    args = parser.parse_args()

    mtp_id = args.mtpid
    mtp_cli_id_str = libmfg_utils.id_str(mtp=mtp_id)
    parameter_cfg_yaml = args.cfgyaml
    
    swm_lp_boot_mode = False 
    stop_on_err = args.stop_on_error
    verbosity = args.verbosity
    stage = args.stage
    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    # two voltage margin for all Normal temperature, Low temperature and High temperature
    # Normal temperature
    high_temp_threshold, low_temp_threshold = libmfg_utils.pick_temperature_thresholds(stage)
    fanspd = libmfg_utils.pick_fan_speed(stage)

    # load the mtp config
    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
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

    # find any slots to skip
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)

    # load EMMC test suite test cases and test steps
    emmc_test_suites = libmfg_utils.load_cfg_from_yaml_file_list([parameter_cfg_yaml])

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id,
                            sys.stdout,
                            None,
                            [],
                            None,
                            mgmt_cfg = mtp_mgmt_cfg,
                            apc_cfg = mtp_apc_cfg,
                            slots_to_skip = mtp_slots_to_skip,
                            dbg_mode = verbosity)

    # logfiles
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=stage)

    try:
        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, stage=stage):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
            return

        # Set Naples25SWM test mode
        mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)

        # Wait the Chamber temperature, if HT or LT is set
        mtp_mgmt_ctrl.cli_log_inf("EMMC Validation Test Ambient Temperature Check", level=0)
        # rdy = mtp_mgmt_ctrl.mtp_wait_temp_ready(low_temp_threshold, high_temp_threshold)
        # hack for temp
        rdy = True
        if not rdy:
            mtp_mgmt_ctrl.mtp_diag_fail_report("EMMC Validation Test Ambient Temperature Check Failed")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_ENV_SETUP, open_file_track_list)
            return
        # only MFG HT/LT need soaking process
        if stage == FF_Stage.FF_2C_H or stage == FF_Stage.FF_2C_L:
            mtp_mgmt_ctrl.mtp_wait_soaking()
        mtp_mgmt_ctrl.cli_log_inf("EMMC Validation Test Ambient Temperature Check Complete\n", level=0)

        # Construct data structures for cards to test
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        pass_nic_list = list()
        fail_nic_list = list()
        skip_nic_list = list()

        # Add failed slots from toplevel
        if args.fail_slots:
            for slot in args.fail_slots:
                fail_nic_list.append(int(slot))

        nic_type_full_list = MFG_VALID_NIC_TYPE_LIST
        nic_test_full_list = list() # list of lists, NOT dict. order of insertion matters

        for nic_type in nic_type_full_list:
            nic_type_list = list()
            # make a list for all NICs of this type in MTP
            for slot in range(MTP_Const.MTP_SLOT_NUM):
                if slot in fail_nic_list:
                    continue
                if not nic_prsnt_list[slot]:
                    continue
                if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == nic_type:
                    nic_type_list.append(slot)
                    pass_nic_list.append(slot)
            nic_test_full_list.append(nic_type_list)

        nic_skipped_list = mtp_mgmt_ctrl.mtp_get_nic_skip_list()
        for slot in range(len(nic_skipped_list)):
            if nic_skipped_list[slot]:
                skip_nic_list.append(slot)

        # check if MTP support present NIC
        mtp_mgmt_ctrl.cli_log_inf("MTP and NIC Type compatibility check started", level=0)
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_type == NIC_Type.VOMERO2:
                mtp_exp_capability = 0x3
            elif nic_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
                mtp_exp_capability = 0x2
            elif nic_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
                mtp_exp_capability = 0x1
            else:
                mtp_mgmt_ctrl.cli_log_err("NIC Type {:s}'s MTP compatibility unknown".format(nic_type), level=0)
                continue

            if nic_type == NIC_Type.NAPLES25SWM:
                if nic_list:
                    for slot in range(len(nic_list)):
                        if (mtp_mgmt_ctrl.mtp_get_swmtestmode(nic_list[slot]) in (Swm_Test_Mode.SWMALOM, Swm_Test_Mode.ALOM)):
                            swm_lp_boot_mode=True
                else:
                    swm_lp_boot_mode=False

                if stage not in (FF_Stage.FF_P2C, FF_Stage.QA):    #Skip SWM Low Power Test for 4C
                    swm_lp_boot_mode=False

            if nic_list:
                if not mtp_capability & mtp_exp_capability:
                    mtp_mgmt_ctrl.mtp_diag_fail_report("MTP capability 0x{:x} doesn't support {:s}".format(mtp_capability, nic_type))
                    libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                    diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
                    return
        mtp_mgmt_ctrl.cli_log_inf("MTP and NIC Type compatibility check complete\n", level=0)
        mtp_mgmt_ctrl.cli_log_inf("Single MTP EMMC Validation Test Start To Run", level=0)

        fanspd = mtp_mgmt_ctrl.mtp_get_fanspd()
        inlet = mtp_mgmt_ctrl.mtp_get_inlet_temp(low_temp_threshold, high_temp_threshold)
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Fan Speed = {:3d}%".format(fanspd))
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(inlet))
        mtp_mgmt_ctrl.cli_log_inf("EMMC Validation Test Environment End\n", level=0)

        # Programmables Check
        programmables_checked = False
        if not programmables_checked:
            mtp_mgmt_ctrl.mtp_power_off_nic()
            mtp_mgmt_ctrl.mtp_power_on_nic(slot_list=pass_nic_list, dl=False)

            dsp = stage

            # Update programmables if necessary
            dl_check_fail_list = diag_reg.naples_update_prog(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, fail_nic_list, [], dsp, stop_on_err)
            programmables_checked = True
            for slot in dl_check_fail_list:
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Disable PCIe polling
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.mtp_power_on_nic(slot_list=pass_nic_list, dl=False)
        if mtp_mgmt_ctrl.mtp_get_asic_support() == MTP_ASIC_SUPPORT.CAPRI:
            mtp_mgmt_ctrl.cli_log_inf("Wait {:02d} seconds for NIC power up before disable PCIE poll".format(MTP_Const.MTP_PCIE_EN_DIS_DELAY), level=0)
            libmfg_utils.count_down(MTP_Const.MTP_PCIE_EN_DIS_DELAY)
            diag_pre_fail_list = diag_reg.mtp_nic_diag_init_pre(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, [], None)
            for slot in diag_pre_fail_list:
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_test_full_list, swm_lp=swm_lp_boot_mode, nic_util=True, stop_on_err=stop_on_err):
            for nic_list in nic_test_full_list:
                for slot in nic_list:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        if slot not in fail_nic_list:
                            fail_nic_list.append(slot)
                        if slot in pass_nic_list:
                            pass_nic_list.remove(slot)
                        if stop_on_err:
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                            return

        # emmc test can run mixed nic card type in parallel
        mix_nictype = list()
        all_nic_list = list()
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_list:
                if nic_type not in mix_nictype:
                    mix_nictype.append(nic_type)
                all_nic_list += nic_list
        mix_nictype = "_".join(mix_nictype)

        diag_para_fail_list = diag_para_emmc_validation_test(mtp_mgmt_ctrl,
                                                            mix_nictype,
                                                            all_nic_list,
                                                            emmc_test_suites,
                                                            stop_on_err,
                                                            False,
                                                            swmtestmode)
        for slot in diag_para_fail_list:
            if slot in all_nic_list and stop_on_err:
                all_nic_list.remove(slot)
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)

        # log the diag test history
        mtp_mgmt_ctrl.mtp_mgmt_diag_history_disp()

        # clear the diag test history
        if not stop_on_err:
            mtp_mgmt_ctrl.mtp_mgmt_diag_history_clear()

        diag_sub_dir = "/diag_logs/"
        nic_sub_dir = "/nic_logs/"
        asic_sub_dir = "/asic_logs/"
        # create log dir
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + diag_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + nic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        # save the asic/diag log files
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_DIAG_LOG_FILES, mtp_script_dir + diag_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, mtp_script_dir + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_NIC_LOG_FILES, mtp_script_dir + nic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        # clean up logfiles for the next run
        cmd = "cleanup.sh"
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

        # Enable PCIe poll
        if not stop_on_err:
            if mtp_mgmt_ctrl.mtp_get_asic_support() == MTP_ASIC_SUPPORT.CAPRI:
                mtp_mgmt_ctrl.mtp_power_cycle_nic(slot_list=pass_nic_list, dl=False)
                mtp_mgmt_ctrl.cli_log_inf("Wait {:02d} seconds for NIC power up before enable PCIE poll".format(MTP_Const.MTP_PCIE_EN_DIS_DELAY), level=0)
                libmfg_utils.count_down(MTP_Const.MTP_PCIE_EN_DIS_DELAY)
                diag_post_fail_list = diag_reg.mtp_nic_diag_init_post(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, [], stage)
                # failed enable pcie poll, fail the card
                for slot in diag_post_fail_list:
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)

        mtp_mgmt_ctrl.cli_log_inf("MTP EMMC Verification Test Complete\n", level=0)

        for slot in pass_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            if not swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES25SWM and (swmtestmode == Swm_Test_Mode.ALOM):
                alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

        for slot in fail_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            if not swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_err("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES25SWM and (swmtestmode == Swm_Test_Mode.ALOM):
                alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

        for slot in skip_nic_list:
            key = libmfg_utils.nic_key(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s}".format(key, MTP_DIAG_Report.NIC_DIAG_REGRESSION_SKIP), level=0)

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)

    diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_PASS, open_file_track_list)

if __name__ == "__main__":
    main()
