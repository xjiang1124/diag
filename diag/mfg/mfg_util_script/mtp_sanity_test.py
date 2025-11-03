#!/usr/bin/env python

import sys
import os
import time
import pexpect
import re
import argparse
import threading
import traceback

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
import testlog
import test_utils
from libdefs import NIC_Type
from libdefs import Swm_Test_Mode
from libdefs import FF_Stage
from libdefs import MTP_Const
from libmfg_cfg import *
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl


def load_mtp_cfg(cfg_yaml = None):
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath(cfg_yaml))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db

def mtp_test_cleanup(error_code, fp_list=None):
    if fp_list:
        for fp in fp_list:
            fp.close()
    os.system("sync")


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg, slots_to_skip=mtp_slots_to_skip)
    return mtp_mgmt_ctrl


def main():
    parser = argparse.ArgumentParser(description="MFG P2C Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip-test", help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser.add_argument("--only-test", help="run particular tests only", nargs="*", default=[])
    parser.add_argument("--mtpid", "-mtpid", help="pre-select MTPs", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--stop-on-error", help="Stop test when fail occur", action='store_true')
    parser.add_argument("--iteration", help="Iteration to run with MTP power cycle", type=int, required=False, default=1)
    parser.add_argument("--jobd_logdir", "--logdir", help="Store final log to different path", default=None)

    verbosity = False
    swmtestmode = Swm_Test_Mode.SW_DETECT
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    if args.swm:
        swmtestmode = args.swm
    stage = FF_Stage.FF_P2C
    iteration = 1
    mtpcfg_file = None
    stop_on_error = False
    if args.stop_on_error:
        stop_on_error = True
    if args.iteration:
        iteration = args.iteration
    else:
        iteration = 1
    if args.mtpcfg:
        mtpcfg_file = os.path.relpath(args.mtpcfg)
        mtp_cfg_db = load_mtp_cfg(mtpcfg_file)
    else:
        mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
    mtpid_fail_list = list()
    mtp_mgmt_ctrl_list = list()
    fail_nic_list = dict()
    nic_sn_list = dict()
    invalid_nic_list = dict()

    # init mtp_ctrl list
    for mtp_id in mtpid_list:
        if verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list)
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)
        fail_nic_list[mtp_id] = list()
        nic_sn_list[mtp_id] = list()
        invalid_nic_list[mtp_id] = list()

    final_test_rs = True
    current_test_rs = False
    total_test_rs = list()

    for loop_cnt in range(iteration):
        current_test_rs = True

        mfg_start_ts = libmfg_utils.timestamp_snapshot()
        mtp_mgmt_ctrl.cli_log_inf("LOOP CYCLE: {0} START".format((loop_cnt + 1)), level=0)

        if not test_utils.single_mtp_test(stage,
                                          mtp_mgmt_ctrl,
                                          mfg_p2c_summary[mtp_id],
                                          args.skip_test,
                                          jobd_logdir=args.jobd_logdir,
                                          mtpcfg_file=mtpcfg_file,
                                          testsuite_name=stage,
                                          swm_test_mode=swmtestmode):
            current_test_rs = False

        mfg_end_ts = libmfg_utils.timestamp_snapshot()
        mtp_mgmt_ctrl.cli_log_inf("MFG Test Duration: {0}".format(mfg_end_ts - mfg_start_ts), level=0)
        mtp_mgmt_ctrl.cli_log_inf("MFG Test Log: {0}".format(testlog.get_mtp_test_log_folder(mtp_mgmt_ctrl)), level=0)
        # result
        if current_test_rs:
            mtp_mgmt_ctrl.cli_log_inf("MFG Test Result: {0}".format("PASS"), level=0)
            total_test_rs.append("PASS")
        else:
            mtp_mgmt_ctrl.cli_log_inf("MFG Test Result: {0}".format("FAIL"), level=0)
            total_test_rs.append("FAIL")

        final_test_rs &= current_test_rs
        mtp_mgmt_ctrl.cli_log_inf("LOOP CYCLE: {0} END\n".format((loop_cnt + 1)), level=0)

        # close file handles
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            mtp_test_cleanup(open_file_track_mtp_list[mtp_id])

        if stop_on_error and not current_test_rs:
            break

    if final_test_rs:
        mtp_mgmt_ctrl.cli_log_inf("*******************************************", level=0)
        mtp_mgmt_ctrl.cli_log_inf("FINAL_POWER_CYCLE_WITH_SANTITY_TEST_PASS", level=0)
        mtp_mgmt_ctrl.cli_log_inf("*******************************************\n\n", level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("*******************************************", level=0)
        mtp_mgmt_ctrl.cli_log_inf("FINAL_POWER_CYCLE_WITH_SANTITY_TEST_FAIL", level=0)
        mtp_mgmt_ctrl.cli_log_inf("*******************************************\n\n", level=0)

    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list, safely=False)
    mtp_mgmt_ctrl.cli_log_inf("*******************************************", level=0)
    mtp_mgmt_ctrl.cli_log_inf("SUMMARY_POWER_CYCLE_WITH_SANTITY_TEST_RESULT", level=0)
    mtp_mgmt_ctrl.cli_log_inf("*******************************************", level=0)

    for rs_idx, rs in enumerate(total_test_rs):
        mtp_mgmt_ctrl.cli_log_inf("{0}TH RESULT: {1}".format((rs_idx + 1), rs), level=0)

if __name__ == "__main__":
    main()
