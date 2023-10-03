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
import libmtp_utils
import test_utils
from libdefs import Swm_Test_Mode
from libdefs import FF_Stage
from libdefs import MTP_Const
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db

def load_mtp_cfg():
    # MTP Screen Chassis
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/mtp_screen_chassis_cfg.yaml"))
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
    parser = argparse.ArgumentParser(description="MFG MTP SCREEN Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip-test", help="skip a particular test section", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--jobd_logdir", "--logdir", help="Store final log to different path", default=None)
    parser.add_argument("--l1-seq", help="asic L1 run under sequence mode", action='store_true')

    stage = FF_Stage.FF_SRN
    verbosity = False
    swmtestmode = Swm_Test_Mode.SW_DETECT
    l1_sequence = False
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    if args.swm:
        swmtestmode = args.swm
    if args.l1_seq:
        l1_sequence = True

    mtpcfg_file = None
    if args.mtpcfg:
        mtpcfg_file = os.path.relpath(args.mtpcfg)
        mtp_cfg_db = load_mtp_cfg(mtpcfg_file)
    else:
        mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
    mtpid_fail_list = list()
    mtp_mgmt_ctrl_list = list()
    fail_nic_list = dict()
    scan_rslt = dict()

    # only allow one per time
    if len(mtpid_list) > 1:
        mtp_mgmt_ctrl.cli_log_err("One MTP per time", level=0)
        return

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

    mfg_srn_start_ts = libmfg_utils.timestamp_snapshot()

    mtp_thread_list = list()
    mfg_srn_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_srn_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = test_utils.single_mtp_test,
                                      args = (
                                                stage,
                                                mtp_mgmt_ctrl,
                                                mfg_srn_summary[mtp_id],
                                                args.skip_test),
                                    kwargs = ({
                                                "mtpcfg_file": mtpcfg_file,
                                                "swm_test_mode": swmtestmode,
                                                "mtpcfg_file": mtpcfg_file,
                                                "jobd_logdir": args.jobd_logdir,
                                                "l1_sequence": l1_sequence,
                                                "swm_test_mode": swmtestmode}))
        mtp_thread.daemon = True
        mtp_thread.start()
        mtp_thread_list.append(mtp_thread)
        time.sleep(2)

    # monitor all the thread
    while True:
        if len(mtp_thread_list) == 0:
            break
        for mtp_thread in mtp_thread_list[:]:
            if not mtp_thread.is_alive():
                mtp_thread.join()
                mtp_thread_list.remove(mtp_thread)
        time.sleep(5)
    mfg_srn_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP SCREEN Test Duration:{:s}".format(mfg_srn_stop_ts - mfg_srn_start_ts))

    # dump the summary
    mtp_sn = mtp_mgmt_ctrl.get_mtp_sn()
    test_result = libmfg_utils.mfg_summary_srn_disp(FF_Stage.FF_SRN, mfg_srn_summary, mtpid_fail_list, mtp_sn)

    # print return code for JobD to pick up
    if test_result:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
