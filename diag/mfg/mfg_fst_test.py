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
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libmfg_cfg import MFG_IMAGE_FILES
import test_utils

parser = argparse.ArgumentParser(description="MFG Final Test", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
parser.add_argument("-card_type", "--card_type", help="card type", type=str, default="general")
parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
parser.add_argument("--logdir", help="Log dir", default=None)

args = parser.parse_args()

def load_mtp_cfg(cfg_yaml):
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath(cfg_yaml))
    else:
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
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg, slots_to_skip=mtp_slots_to_skip)
    return mtp_mgmt_ctrl


def main():
    card_type = args.card_type.upper()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False
    stage = FF_Stage.FF_FST
    mtpcfg_file = None
    if args.mtpcfg:
        mtpcfg_file = os.path.relpath(args.mtpcfg)
    mtp_cfg_db = load_mtp_cfg(mtpcfg_file)
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
    mtpid_fail_list = list()
    mtp_mgmt_ctrl_list = list()

    # init mtp_ctrl list
    for mtp_id in mtpid_list:
        if verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list)
        if mtp_cfg_db.get_mtp_max_slots(mtp_id):
            mtp_mgmt_ctrl._slots = mtp_cfg_db.get_mtp_max_slots(mtp_id)

        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)

    # logfiles
    stage = FF_Stage.FF_FST
    open_file_track_mtp_list = dict()
    logfile_dir_list = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id] = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)

    if not GLB_CFG_MFG_TEST_MODE:
        args.skip_test.append("SCAN_VERIFY")

    if "SCAN_VERIFY" not in args.skip_test and False:
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            libmfg_utils.single_mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id], is_fst_test=True)

    mfg_fst_start_ts = libmfg_utils.timestamp_snapshot()

    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    mtp_thread_list = list()
    mfg_fst_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_fst_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = test_utils.single_mtp_test,
                                      args = (stage,
                                            mtp_mgmt_ctrl,
                                            mfg_fst_summary[mtp_id],
                                            logfile_dir_list[mtp_id],
                                            open_file_track_mtp_list[mtp_id],
                                            args.skip_test,
                                            args.logdir),
                                    kwargs = ({"mtpcfg_file": mtpcfg_file,
                                            "testsuite_name": stage,
                                            "card_type": card_type}))
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

    mfg_fst_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP Final Test Duration:{:s}".format(mfg_fst_stop_ts - mfg_fst_start_ts))

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

    # dump the summary
    final_result = libmfg_utils.mfg_summary_disp(FF_Stage.FF_FST, mfg_fst_summary, mtpid_fail_list)

    return final_result

if __name__ == "__main__":
    if not main():
        sys.exit(1)
    sys.exit(0)
