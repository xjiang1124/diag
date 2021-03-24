#!/usr/bin/env python

import sys
import os
import time
import pexpect
import threading
import argparse
import re
import copy

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

def load_mtp_usb_serial_port(mtp_mgmt_ctrl):
    usb_serial = []
    for port in range(5):
        port_pre = os.system("ls /dev/ttyUSB{} > /dev/null 2>&1".format(port))
        if port_pre == 0:
            usb_serial.append("ttyUSB{}".format(port))
            mtp_mgmt_ctrl.cli_log_info("Found /dev/ttyUSB{}".format(port))
    return usb_serial

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

    serial_port = []
    if card_type == "ORTANO":
        serial_port = load_mtp_usb_serial_port(mtp_mgmt_trl)

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

    for _slot, _sn, _nic_type in fail_match:
        slot = int(_slot) - 1
        sn = _sn.strip()
        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))

    for _slot, _sn, _nic_type in pass_match:
        slot = int(_slot) - 1
        sn = _sn.strip()
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

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


    for _slot, _sn, _nic_type in fail_match:
        key = libmfg_utils.nic_key(int(_slot), base=0)
        nic_type = _nic_type.strip()
        sn = _sn.strip()
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    for _slot, _sn, _nic_type in pass_match:
        key = libmfg_utils.nic_key(int(_slot), base=0)
        nic_type = _nic_type.strip()
        sn = _sn.strip()
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

    if  card_type == "ORTANO":
        for port in serial_port:
            print (port)
            cmd = "mtp_fst_script/rotctrl -b 115200 -d elba -c ortano -p {:s}".format(port)
            if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_FST_TEST_TIMEOUT):
                mtp_mgmt_ctrl.cli_log_err("Executing ROT test over usb port {:s} Failed".format(port), level=0)
            result = mtp_mgmt_ctrl.mtp_get_cmd_buf()
            pass_reg_exp = re.compile("ROT test PASSED")
            fail_reg_exp = re.compile("ROT test FAILED")
            pass_match = pass_reg_exp.search(result)
            fail_match = file_reg_exp.search(result)
            if pass_match:
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s}".format(port, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
            elif fail_match:
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s}".format(port, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
            else:
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s}".format(port, MTP_DIAG_Report.NIC_DIAG_REGRESSION_UNFINISH), level=0)
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)
            mtp_mgmt_ctrl.cli_log_inf("MTP ROT Tests Complete", level=0)
    logfile_close(log_filep_list)
    return

if __name__ == "__main__":
    main()

