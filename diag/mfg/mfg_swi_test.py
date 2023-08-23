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
from libdefs import FLEX_TWO_WAY_COMM
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import FLEX_SHOP_FLOOR_CONTROL
from libmfg_cfg import FLEX_ERR_CODE_MAP
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import GIGLIO_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
import test_utils


def load_mtp_cfg(cfg_yaml=None):
    mtp_chassis_cfg_file_list = list()
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath(cfg_yaml))
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/swi_mtp_chassis_cfg.yaml"))
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
    parser = argparse.ArgumentParser(description="MFG Software Install Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser.add_argument("--sw-pn", "-swpn", "--swpn", "-sw-pn", help="pre-select SW PN or list of SW PNs", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--skip-slots", "--skip-slot", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--jobd_logdir", "--logdir", help="Store final log to different path", default=None)


    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False
    stage=FF_Stage.FF_SWI

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

    # logfiles
    open_file_track_mtp_list = dict()
    logfile_dir_list = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id] = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)

    # get sw image name based on the sw pn
    if not args.sw_pn:
        sw_pn_list = [libmfg_utils.sw_pn_scan()]
    else:
        sw_pn_list = args.sw_pn
    for sw_pn in sw_pn_list:
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            mtp_mgmt_ctrl.cli_log_inf("==> Scanned SW PN: {:s} <==".format(sw_pn))
    nic_sw_img_file_list = list()
    for sw_pn in sw_pn_list:
        nic_sw_link_file = "release/{:s}".format(sw_pn)
        if not libmfg_utils.file_exist(nic_sw_link_file):
            for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
                mtp_mgmt_ctrl.cli_log_err("Software image link {:s} doesn't exist... Abort".format(nic_sw_link_file), level=0)
            return
        nic_sw_img_file = os.readlink(nic_sw_link_file)
        nic_sw_img_file_list.append(nic_sw_img_file)

    # get path to profile, but doesnt work if multiple sw_pn supplied
    profile_cfg_file_list = list()
    for sw_pn in sw_pn_list:
        profile_link_cfg_file = "release/profile_{:s}.py".format(sw_pn)
        if not libmfg_utils.file_exist(profile_link_cfg_file):
            for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
                mtp_mgmt_ctrl.cli_log_inf("No Profile will apply to PN: {:s}".format(sw_pn), level=0)
            profile_cfg_file = None
        else:
            profile_cfg_file = "release/" + os.readlink(profile_link_cfg_file)
            for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
                mtp_mgmt_ctrl.cli_log_inf("Profile {:s} will apply to PN: {:s}".format(profile_cfg_file, sw_pn), level=0)
            profile_cfg_file_list.append(profile_link_cfg_file)

    if not GLB_CFG_MFG_TEST_MODE:
        args.skip_test.append("SCAN_VERIFY")

    if "SCAN_VERIFY" not in args.skip_test:
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            libmfg_utils.single_mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id])

    mfg_swi_start_ts = libmfg_utils.timestamp_snapshot()

    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    mtp_thread_list = list()
    mfg_swi_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_swi_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = test_utils.single_mtp_test,
                                      args = (
                                                stage,
                                                mtp_mgmt_ctrl,
                                                mfg_swi_summary[mtp_id],
                                                logfile_dir_list[mtp_id],
                                                open_file_track_mtp_list[mtp_id],
                                                args.skip_test,
                                                args.jobd_logdir,
                                                args.skip_slots),
                                    kwargs = ({
                                                "mtpcfg_file": mtpcfg_file,
                                                "testsuite_name": stage,
                                                "nic_sw_img_file_list": nic_sw_img_file_list,
                                                "profile_cfg_file_list": profile_cfg_file_list,
                                                "sw_pn_list": sw_pn_list}))
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

    mfg_swi_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP Software Install Test Duration:{:s}".format(mfg_swi_stop_ts - mfg_swi_start_ts))

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

    # dump the summary
    test_result = libmfg_utils.mfg_summary_disp(stage, mfg_swi_summary, mtpid_fail_list)

    # print return code for JobD to pick up
    if test_result:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
