#!/usr/bin/env python

import sys
import os
import time
import pexpect
import threading
import argparse
import re

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

    # local log files
    log_filep_list = list()
    test_log_file = "test_fst.log"
    test_log_filep = open(test_log_file, "w+", buffering=0)
    log_filep_list.append(test_log_filep)

    diag_log_file = "diag_fst.log"
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

    if card_type == "GENERAL":
        cmd = MFG_DIAG_CMDS.FST_DIAG_CMD_FMT
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
        pass_reg_exp = r"slot(\d).*sn:(.*)type:(.*)pass"
        fail_reg_exp = r"slot(\d).*sn:(.*)type:(.*)failed"
        pass_match = re.findall(pass_reg_exp, result)
        fail_match = re.findall(fail_reg_exp, result)
        dsp = FF_Stage.FF_FST
        test = "PCIE_LINK"
    elif card_type == "CLOUD":
        cmd = MFG_DIAG_CMDS.FST_DIAG_CMD_FMT_CLD.format(card_type, stage)
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
        pass_reg_exp = r"Slot (\d).* SN: (.*) Product name: (.*) pass"
        #pass_reg_exp = r"Slot (\d).*found"
        fail_reg_exp = r"Slot (\d).* SN: (.*) Product name: (.*) failed"
        pass_match = re.findall(pass_reg_exp, result)
        fail_match = re.findall(fail_reg_exp, result)
        dsp = FF_Stage.FF_FST
        test = "PCIE_LINK"
        print(pass_match)
        print(fail_match)

        if stage == "FETCH_SN":
            return

    for _slot, _sn, _nic_type in fail_match:
        slot = int(_slot) - 1
        sn = _sn.strip()
        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))

    for _slot, _sn, _nic_type in pass_match:
        slot = int(_slot) - 1
        sn = _sn.strip()
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

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

    logfile_close(log_filep_list)
    return

if __name__ == "__main__":
    main()

