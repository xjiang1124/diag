#!/usr/bin/env python

import sys
import os
import time
import pexpect
import threading
import argparse
import re
import copy
import json

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libdefs import FF_Stage
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl

def get_nic_ssh_cmd(ip, cmd):
    ssh_cmd_fmt = "/home/diag/mtp_fst_script/sshpass -p pen123 ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30' -o 'LogLevel=ERROR' root@{} {}"
    ssh_cmd_fmt = "/home/diag/mtp_fst_script/sshpass -p pen123 ssh -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30' -o 'LogLevel=ERROR' root@{} {}"
    ssh_cmd = ssh_cmd_fmt.format(ip, cmd)
    return ssh_cmd

def get_slot_bus_list(mtp_mgmt_ctrl, card_type):
    if card_type == "ORTANO":
        # elba
        cmd = "lspci -d 1dd8:0002"
    else:
        # capri
        cmd = "lspci -d 1dd8:1000"
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
    bus_list_match = re.findall(r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]+) ", result)
    mtp_mgmt_ctrl.cli_log_inf("Found {:d} devices".format(len(bus_list_match)))

    if len(bus_list_match):
        bus_list = list()
        for bus in bus_list_match:
            bus_list.append(bus)
        slot_bus_list = decode_pci_slot(bus_list)
    else:
        mtp_mgmt_ctrl.cli_log_err("No devices found")
        slot_bus_list = []

    return slot_bus_list

def decode_pci_slot(bus_list):
    """
        41:00.0         slot 5  (top)   enp69s0
        21:00.0         slot 4          enp35s0  // 21+offset if slot 1 is taken
        61:00.0         slot 3          enp99s0
        08:00.0         slot 2          enp10s0
        21:00.0         slot 1  (lowest)enp35s0
    """
    old_fst = ['18:00.0', '3b:00.0', 'd8:00.0', 'af:00.0']
    new_fst = ['21:00.0', '08:00.0', '61:00.0', '41:00.0']
    slot_bus_list = []

    for bus in bus_list:
        if bus in new_fst:
            slot_bus_list.append((new_fst.index(bus), bus))
        elif bus in old_fst:
            slot_bus_list.append((old_fst.index(bus), bus))
        else:
            if "21:00.0" in bus_list: #slot 1 of new fst occupied already
                slot_bus_list.append((3, bus))
            else:
                print("Unknown pci bus! "+bus)

    return slot_bus_list

def check_pcie_link(mtp_mgmt_ctrl, slot, bus, card_type):
    if card_type == "ORTANO":
        expected_speed = "16"
        expected_width = "16"
    else:
        expected_speed = "8"
        expected_width = "8"

    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("lspci -vv -s {:s} | grep LnkSta:".format(bus)):
        mtp_mgmt_ctrl.cli_log_err("Unable to retrieve link speed and width")
        return False
    else:
        result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
        if "Speed {:s}GT/s".format(expected_speed) in result:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "PCIE link speed pass")
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "PCIE link speed fails")
            return False

        if "Width x{:s}".format(expected_width) in result:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "PCIE link width pass")
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "PCIE link width fails")
            return False
    return True

def get_eth_mnic(mtp_mgmt_ctrl, slot, bus):
    bus_str = bus.split(":", 1)[0]
    bus_int = int(bus_str, 16)+4
    eth = "enp"+str(bus_int)+"s0"
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Enable NIC mnic {:s}".format(eth))

    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("ifconfig {:s} down".format(eth))
    time.sleep(1)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("ifconfig {:s} 169.254.{:d}.2/24".format(eth, bus_int))
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("ifconfig {:s} up".format(eth))
    time.sleep(1)
    if eth+": ERROR" in mtp_mgmt_ctrl.mtp_get_cmd_buf():
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Failed to enable NIC mnic")
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("ifconfig {:s} down".format(eth))
        time.sleep(1)
        return ""
    return "169.254.{:d}.1".format(bus_int)

def get_product_name_from_pn(pn):
    if "DSC2-2Q200-32R32F64P-R" in pn:
        product_name = "ORTANO2"
    elif "68-0015-02" in pn:
        product_name = "ORTANO2"
    else:
        product_name = "UNKNOWN"
        print("Unknown PN:", pn)

    return product_name

def get_fw_info(mtp_mgmt_ctrl, slot, nic_mgmt_ip):
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Retrieve FW info")
    cmd = "/nic/tools/fwupdate -l"
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(get_nic_ssh_cmd(nic_mgmt_ip, cmd)):
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "failed to execute fwupdate -l")
        mtp_mgmt_ctrl.cli_log_slot_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
        return False
    fw_json = re.findall(r"{.+}", mtp_mgmt_ctrl.mtp_get_cmd_buf(),re.DOTALL)
    if not fw_json:
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "failed to execute fwupdate -l")
        mtp_mgmt_ctrl.cli_log_slot_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
        return False
    fwlist = json.loads(fw_json[0])
    try:
        print_fwlist = ""
        if "boot0" in fwlist:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "boot0:     {:15s}   {:s} ".format(fwlist["boot0"]["image"]["software_version"], fwlist["boot0"]["image"]["build_date"]) )
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "FWLIST missing boot0 info")
        if "mainfwa" in fwlist:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "mainfwa:   {:15s}   {:s} ".format(fwlist["mainfwa"]["kernel_fit"]["software_version"], fwlist["mainfwa"]["kernel_fit"]["build_date"]) )
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "FWLIST missing mainfwa info")
        if "mainfwb" in fwlist:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "mainfwb:   {:15s}   {:s} ".format(fwlist["mainfwb"]["kernel_fit"]["software_version"], fwlist["mainfwb"]["kernel_fit"]["build_date"]) )
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "FWLIST missing mainfwb info")
        if "goldfw" in fwlist:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "goldfw:    {:15s}   {:s} ".format(fwlist["goldfw"]["kernel_fit"]["software_version"], fwlist["goldfw"]["kernel_fit"]["build_date"]) )
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "FWLIST missing goldfw info")
        if "diagfw" in fwlist:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "diagfw:    {:15s}   {:s} ".format(fwlist["diagfw"]["kernel_fit"]["software_version"], fwlist["diagfw"]["kernel_fit"]["build_date"]) )
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "FWLIST missing diagfw info")

        mtp_mgmt_ctrl.cli_log_slot_inf(slot, print_fwlist)
    except KeyError as e:
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "FWLIST missing info")
        mtp_mgmt_ctrl.cli_log_slot_err(slot, e)
        return False
    return True

def load_mtp_usb_serial_port(mtp_mgmt_ctrl):
    usb_serial = []
    for port in range(5):
        port_pre = os.system("ls /dev/ttyUSB{} > /dev/null 2>&1".format(port))
        if port_pre == 0:
            usb_serial.append("ttyUSB{}".format(port))
            mtp_mgmt_ctrl.cli_log_inf("Found /dev/ttyUSB{}".format(port))
    return usb_serial

def fetch_sn_cloud_stage(mtp_mgmt_ctrl, card_type):
    pass_list, fail_list = [], []

    slot_bus_list = get_slot_bus_list(mtp_mgmt_ctrl, card_type)
    if len(slot_bus_list) == 0:
        logfile_close(log_filep_list)
        return

    for slot, bus in slot_bus_list:
        pass_list.append(slot)

        ### DECODE ETH
        nic_mgmt_ip = get_eth_mnic(mtp_mgmt_ctrl, slot, bus)
        if not nic_mgmt_ip:
            fail_list.append(slot)
            pass_list.remove(slot)
            continue

        ### GET FRU
        cmd = "cat /tmp/fru.json"
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(get_nic_ssh_cmd(nic_mgmt_ip, cmd)):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "failed to fetch SN")
            mtp_mgmt_ctrl.cli_log_slot_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
            fail_list.append(slot)
            pass_list.remove(slot)
            continue
        fru_json = re.findall(r"{.+}", mtp_mgmt_ctrl.mtp_get_cmd_buf(),re.DOTALL)
        if not fru_json:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Get FRU failed")
            mtp_mgmt_ctrl.cli_log_slot_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
            fail_list.append(slot)
            pass_list.remove(slot)
            continue
        fru = json.loads(fru_json[0])

        if fru["serial-number"]:
            sn = fru["serial-number"]
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to parse serial-number from FRU")
            SN = "SN_UNKNOWN"

        try:
            pn = fru["board-assembly-area"]
        except KeyError:
            try:
                pn = fru["part-number"]
            except KeyError:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to parse part-number from FRU")
                pn = ""

        product_name = get_product_name_from_pn(pn)

        if product_name == "UNKNOWN":
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "SN = {:s}, PN = {:s}, TYPE = {:s}".format(sn, pn, product_name))
            continue

        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}, PN = {:s}, TYPE = {:s}".format(sn, pn, product_name))

        # for flexflow/logging purposes:
        mtp_mgmt_ctrl.mtp_set_nic_sn(slot, sn)
        mtp_mgmt_ctrl.mtp_set_nic_type(slot, product_name)


        ### GET FW INFO
        if not get_fw_info(mtp_mgmt_ctrl, slot, nic_mgmt_ip):
            fail_list.append(slot)
            pass_list.remove(slot)
            continue

        ### SET PEFORMANCE MODE
        if product_name == "ORTANO2":
            # Ensure performance mode even though this step is not needed with newer mainfw anymore.
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Set performance mode")
            cmd = "touch /sysconfig/config0/.perf_mode"
            if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(get_nic_ssh_cmd(nic_mgmt_ip, cmd)):
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "failed to set performance mode")
                mtp_mgmt_ctrl.cli_log_slot_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
                # fail_list.append(slot)
                # pass_list.remove(slot)
                # continue

        ### SWITCH TO MAINFW
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Switch to mainfw")
        cmd = "/nic/tools/fwupdate -s mainfwa"
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(get_nic_ssh_cmd(nic_mgmt_ip, cmd)):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "failed to switch to mainfw")
            mtp_mgmt_ctrl.cli_log_slot_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
            fail_list.append(slot)
            pass_list.remove(slot)
            continue

    return pass_list, fail_list

def check_pcie_stage(mtp_mgmt_ctrl, card_type):
    pass_list, fail_list = [], []
    slot_bus_list = get_slot_bus_list(mtp_mgmt_ctrl, card_type)
    if len(slot_bus_list) == 0:
        logfile_close(log_filep_list)
        return

    for slot, bus in slot_bus_list:
        pass_list.append(slot)
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Retrieve PCIE link {:s} properties".format(bus))
        if not check_pcie_link(mtp_mgmt_ctrl, slot, bus, card_type):
            fail_list.append(slot)
            pass_list.remove(slot)

    return pass_list, fail_list

def check_rot(mtp_mgmt_ctrl, card_type, pass_nic_list, fail_nic_list):
    pass_list, fail_list = [], []
    serial_ports = []
    if card_type == "ORTANO":
        serial_ports = load_mtp_usb_serial_port(mtp_mgmt_ctrl)
    else:
        return

    result = ""
    for port in serial_ports:
        cmd = "mtp_fst_script/rotctrl -b 115200 -d elba -c ortano -p {:s}".format(port)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_FST_TEST_TIMEOUT):
            mtp_mgmt_ctrl.cli_log_err("Executing ROT test over usb port {:s} Failed".format(port), level=0)
        result += mtp_mgmt_ctrl.mtp_get_cmd_buf()
    pass_reg_exp_rot = re.compile("ROT test PASSED ([A-Za-z0-9]*)")
    fail_reg_exp_rot = re.compile("ROT test FAILED ([A-Za-z0-9]*)")
    pass_match_rot = pass_reg_exp_rot.findall(result)
    fail_match_rot = fail_reg_exp_rot.findall(result)

    # Matching game
    # match slot to SN, finding missing ones.
    for slot in pass_nic_list + fail_nic_list:
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if sn in pass_match_rot:
            pass_list.append(slot)
        elif sn in fail_match_rot:
            fail_list.append(slot)
        else:
            fail_list.append(slot)

    # Save the logs
    for sn in pass_match_rot + fail_match_rot:
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("cp /home/diag/{:s}.log /home/diag/mtp_fst_script/rot_{:s}.log".format(sn, sn), timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("rm /home/diag/{:s}.log".format(sn), timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)
    for port in serial_ports:
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("cp /home/diag/{:s}.log /home/diag/mtp_fst_script/rot_{:s}.log".format(port, port), timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("rm /home/diag/{:s}.log".format(port), timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)

    return pass_list, fail_list

def logfile_close(filep_list):
    for fp in filep_list:
        fp.close()
    os.system("sync")


def load_mtp_cfg():
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/fst_mtps_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db

def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg)
    return mtp_mgmt_ctrl

def main():
    parser = argparse.ArgumentParser(description="MTP Final Stage Test Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTPS-001, etc", required=True)
    parser.add_argument("-card_type", "--card_type", help="card type", type=str, default="general")
    parser.add_argument("-stage", "--stage", help="stage", type=str, default="FETCH_SN")

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid
    card_type = args.card_type.upper()
    stage = args.stage.upper()

    mtp_cfg_db = load_mtp_cfg()

    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
    fst = 0
    if mtp_capability == 0x4:
        fst=1

    # local log files
    log_filep_list = list()
    test_log_file = "test_fst.log"
    if "CLOUD" in card_type and stage != "FETCH_SN":
        test_log_filep = open(test_log_file, "a+", buffering=0)
    else:
        test_log_filep = open(test_log_file, "w+", buffering=0)
    log_filep_list.append(test_log_filep)

    diag_log_file = "diag_fst.log"
    if "CLOUD" in card_type and stage != "FETCH_SN":
        diag_log_filep = open(diag_log_file, "a+", buffering=0)
    else:
        diag_log_filep = open(diag_log_file, "w+", buffering=0)
    log_filep_list.append(diag_log_filep)

    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = "diag_{:s}_fst.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, "w+")
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list)

    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTPS chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg = True):
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTPS chassis", level=0)
        logfile_close(log_filep_list)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTPS chassis connected", level=0)

    mtp_mgmt_ctrl.cli_log_inf("MTP Final Stage Test Start", level=0)
    start_ts = libmfg_utils.timestamp_snapshot()



    pass_nic_list = list()
    fail_nic_list = list()

    # rebuild pass/fail with previous stage.
    test_records = []
    if stage != "FETCH_SN" and card_type == "ORTANO":
        with open(".tmp.json", "r") as fh:
            test_records = json.loads(fh.read())

        for record in test_records:
            slot = record[0]
            sn = record[1]
            nic_type = record[2]
            result = record[3]

            mtp_mgmt_ctrl.mtp_set_nic_sn(slot, sn)
            mtp_mgmt_ctrl.mtp_set_nic_type(slot, nic_type)
            if result == "PASS":
                pass_nic_list.append(slot)
            if result == "FAIL":
                fail_nic_list.append(slot)



    if card_type == "GENERAL" or card_type == "GENERAL_OLD" or card_type == "ORACLE":
        cmd = MFG_DIAG_CMDS.FST_DIAG_CMD_FMT_CLD.format(card_type, stage, fst)
        #cmd = MFG_DIAG_CMDS.FST_DIAG_CMD_FMT
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_FST_TEST_TIMEOUT):
            mtp_mgmt_ctrl.cli_log_err("MTP Final Stage Test Failed", level=0)
            logfile_close(log_filep_list)
            return
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        mtp_mgmt_ctrl.cli_log_inf("MTP Final Stage Test Complete", level=0)

        result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
        # find the regexp for pass slot only:
        # eg: slot2 18:00.0 sn: FLM1914005F type: NAPLES100 pass
        pass_reg_exp = r"slot: (\d).* sn: (.*) type: (.*) pass"
        fail_reg_exp = r"slot: (\d).* sn: (.*) type: (.*) failed"
        pass_match = re.findall(pass_reg_exp, result)
        fail_match = re.findall(fail_reg_exp, result)
        dsp = FF_Stage.FF_FST
        test = "PCIE_LINK"
    elif "CLOUD" in card_type:
        cmd = MFG_DIAG_CMDS.FST_DIAG_CMD_FMT_CLD.format(card_type, stage, fst)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_FST_TEST_TIMEOUT):
            mtp_mgmt_ctrl.cli_log_err("MTP Final Stage Test Failed", level=0)
            logfile_close(log_filep_list)
            return
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        mtp_mgmt_ctrl.cli_log_inf("MTP Final Stage Test Complete", level=0)

        result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
        print(result)
        # find the regexp for pass slot only:
        # eg: slot1 18:00.0 sn: FLM1914005F type: NAPLES100 pass
        pass_reg_exp = r"slot: (\d).* sn: (.*) type: (.*) pass"
        fail_reg_exp = r"slot: (\d).* sn: (.*) type: (.*) failed"
        pass_match = re.findall(pass_reg_exp, result)
        fail_match = re.findall(fail_reg_exp, result)
        dsp = FF_Stage.FF_FST

        if stage == "FETCH_SN":
            test = "FETCH_SN"
        else:
            test = "PCIE_LINK"
    elif card_type == "ORTANO":
        dsp = FF_Stage.FF_FST

        if stage == "FETCH_SN":
            testlist = ["FETCH_SN"]
        elif stage == "CHECK_PCIE":
            testlist = ["PCIE_LINK", "ROT"]
        else:
            testlist = []

        for test in testlist:
            mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format("", dsp, test), level=0)
            start_ts = libmfg_utils.timestamp_snapshot()

            if test == "FETCH_SN":
                test_pass_list, test_fail_list = fetch_sn_cloud_stage(mtp_mgmt_ctrl, card_type)
            elif test == "PCIE_LINK":
                test_pass_list, test_fail_list = check_pcie_stage(mtp_mgmt_ctrl, card_type)
            elif test == "ROT":
                test_pass_list, test_fail_list = check_rot(mtp_mgmt_ctrl, card_type, pass_nic_list, fail_nic_list)
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown FST Test: {:s}, Ignore".format(test))
                continue

            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)

            for slot in test_pass_list:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

                # update global result list also.
                if slot not in pass_nic_list and slot not in fail_nic_list:
                    pass_nic_list.append(slot)

            for slot in test_fail_list:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))

                # update global result list also.
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                    fail_nic_list.append(slot)

                if slot not in pass_nic_list and slot not in fail_nic_list:
                    fail_nic_list.append(slot)

    else:
        mtp_mgmt_ctrl.cli_log_err("Unknown card type", level=0)
        mtp_mgmt_ctrl.cli_log_err("MTP Final Stage Test Failed", level=0)
        logfile_close(log_filep_list)
        return

    if stage == "FETCH_SN" and card_type == "ORTANO":
        ## save variables needed through the powercycle.
        save_record = list()
        for slot in pass_nic_list:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            save_record.append((slot, sn, nic_type, "PASS"))
        for slot in fail_nic_list:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            save_record.append((slot, sn, nic_type, "FAIL"))
        with open(".tmp.json", "w") as fh:
            json.dump(save_record, fh, allow_nan=True)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("sync")

        cmd = "cp /home/diag/mtp_fst_script/diag_fst.log /home/diag/mtp_fst_script/diag_fst.log.0"
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)
        cmd = "cp /home/diag/mtp_fst_script/test_fst.log /home/diag/mtp_fst_script/test_fst.log.0"
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)

        # end the test here
        logfile_close(log_filep_list)
        return

    if "CLOUD" in card_type:
        if stage == "FETCH_SN":
            cmd = "cp /home/diag/mtp_fst_script/diag_fst.log /home/diag/mtp_fst_script/diag_fst.log.0"
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)
            cmd = "cp /home/diag/mtp_fst_script/test_fst.log /home/diag/mtp_fst_script/test_fst.log.0"
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)

            logfile_close(log_filep_list)
            return
        else:
            #get the first pass results for the final diag result
            f = open("diag_fst.log.0", "r")
            file_buf = f.read() # Read whole file in the file_content string
            f.close()
            fail_match1 = re.findall(fail_reg_exp, file_buf)
            pass_match1 = re.findall(pass_reg_exp, file_buf)
            if fail_match1:
                #remove anything that failed first pass from pass_match in case it's there
                for n in fail_match1:
                    print(n)
                    pass_match = [x for x in pass_match if x!= n]
                #add anything from first pass failed match (failed_match1) to the failed_match if not there
                for n in fail_match1:
                    if n not in fail_match:
                        fail_match.append(n)
                #sort it based on slot number
                fail_match.sort(key = lambda x: x[0])

    if "ORTANO" not in card_type:
        for _slot, _sn, _nic_type in fail_match:
            if _slot in pass_nic_list:
                pass_nic_list.remove(_slot)
            if _slot not in fail_nic_list:
                fail_nic_list.append(_slot)

        for _slot, _sn, _nic_type in pass_match:
            if _slot in fail_nic_list:
                continue
            if _slot not in pass_nic_list:
                pass_nic_list.append(_slot)

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

    logfile_close(log_filep_list)
    return

if __name__ == "__main__":
    main()

