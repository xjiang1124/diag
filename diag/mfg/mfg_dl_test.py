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
import test_utils
from libdefs import MTP_Const
from libdefs import FF_Stage
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE


def load_mtp_cfg(cfg_yaml=None):
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath(cfg_yaml))
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db

def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, skip_slots=[]):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    if len(skip_slots) > 0 and not mtp_cfg_db.set_mtp_slots_to_skip(mtp_id, skip_slots):
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to set skip slots")
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg, slots_to_skip=mtp_slots_to_skip)
    return mtp_mgmt_ctrl


def main():
    parser = argparse.ArgumentParser(description="MFG MTP DL Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--dpn", help="Supply Diagnostic Part Number, for QA/lab only...MFG should enter DPN through scanning", default=None)
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser.add_argument("--skip-slots", "--skip-slot", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--jobd_logdir", "--logdir", help="Store final log to different path", default=None)

    verbosity = False
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True

    swmtestmode = Swm_Test_Mode.SW_DETECT  
    if args.swm:
        swmtestmode = args.swm

    stage = FF_Stage.FF_DL

    mtpcfg_file = None
    if args.mtpcfg:
        mtpcfg_file = os.path.relpath(args.mtpcfg)
        mtp_cfg_db = load_mtp_cfg(mtpcfg_file)
    else:
        mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
    mtp_mgmt_ctrl_list = list()
    mtpid_fail_list = list()
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
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)
        fail_nic_list[mtp_id] = list()
        nic_sn_list[mtp_id] = list()
        invalid_nic_list[mtp_id] = list()

    mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

    mtp_thread_list = list()
    mfg_dl_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_dl_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = test_utils.single_mtp_test,
                                      args = (
                                                stage,
                                                mtp_mgmt_ctrl,
                                                mfg_dl_summary[mtp_id],
                                                args.skip_test,
                                                args.skip_slots),
                                    kwargs = ({
                                                "mtpcfg_file": mtpcfg_file,
                                                "jobd_logdir": args.jobd_logdir,
                                                "testsuite_name": stage,
                                                "swm_test_mode": swmtestmode,
                                                "dpn": args.dpn}))
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

    mfg_dl_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP DL Test Duration:{:s}".format(mfg_dl_stop_ts - mfg_dl_start_ts))

    # dump the summary
    test_result = libmfg_utils.mfg_summary_disp(stage, mfg_dl_summary, mtpid_fail_list)

    # print return code for JobD to pick up
    if test_result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
