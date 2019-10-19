#!/usr/bin/env python

import sys
import os
import time
import datetime
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
from libdefs import MFG_DIAG_CMDS
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
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/sw_mtp_chassis_cfg.yaml"))
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
    parser = argparse.ArgumentParser(description="MTP Software Profile Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid

    mtp_cfg_db = load_mtp_cfg()

    # local log files
    log_filep_list = list()
    test_log_file = "test_sw.log"
    test_log_filep = open(test_log_file, "w+")
    log_filep_list.append(test_log_filep)

    diag_log_file = "diag_sw.log"
    diag_log_filep = open(diag_log_file, "w+")
    log_filep_list.append(diag_log_filep)

    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = "diag_{:s}_sw.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, "w+")
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list)

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
        logfile_close(log_filep_list)
        return

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()
    time.sleep(60)

    dsp = "SW"
    pass_nic_list = list()
    fail_nic_list = list()

    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot\n")
            continue

        if mtp_mgmt_ctrl.mtp_nic_mgmt_reinit(slot):
            pass_nic_list.append(slot)
        else:
            fail_nic_list.append(slot)
 
    if not mtp_mgmt_ctrl.mtp_nic_mgmt_mac_refresh():
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP mac address refresh failed, test abort...")
        logfile_close(log_filep_list)
        return

    if not mtp_mgmt_ctrl.mtp_mgmt_nic_mac_validate():
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP detect duplicate mac address, test abort...")
        logfile_close(log_filep_list)
        return

    for slot in pass_nic_list[:]:
        sn = "FLM183100{:02d}".format(slot+1)
        for test in ["PROFILE"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            # nic power status check
            if test == "PROFILE":
                ret = mtp_mgmt_ctrl.mtp_nic_sw_profile(slot, "profile_90-0001-0001.py")
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SW Test: {:s}, Ignore".format(test))
                continue
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.cli_log_inf("MTP Software Profile Test Complete", level=0)

    for slot in pass_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        sn = "FLM183100{:02d}".format(slot+1)
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

    for slot in fail_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        sn = "FLM183100{:02d}".format(slot+1)
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    logfile_close(log_filep_list)
    return

if __name__ == "__main__":
    main()

