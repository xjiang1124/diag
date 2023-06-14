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
from libdefs import NIC_Type
from libdefs import Swm_Test_Mode
from libdefs import FF_Stage
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libdefs import FLEX_TWO_WAY_COMM
from libmfg_cfg import *
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db


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
    parser.add_argument("--skip-test", help="skip a particular test or test section", nargs="*", default=[])
    parser.add_argument("--only-test", help="run particular tests only", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
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

        # logfiles
        open_file_track_mtp_list = dict()
        logfile_dir_list = dict()
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id] = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)

        mfg_start_ts = libmfg_utils.timestamp_snapshot()
        mtp_mgmt_ctrl.cli_log_inf("LOOP CYCLE: {0} START".format((loop_cnt + 1)), level=0)
        # power off all the test mtp
        libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list, safely=False)
        # power on the mtp chassis
        libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

        # Connect to MTP
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
            if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, stage=stage, level=0):
                current_test_rs = False

        if current_test_rs and loop_cnt == 0:
            # Sync timestamp to server
            for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
                timestamp_str = str(libmfg_utils.timestamp_snapshot())
                if not mtp_mgmt_ctrl.mtp_mgmt_set_date(timestamp_str):
                    mtp_mgmt_ctrl.cli_log_err("MTP Chassis timestamp sync failed", level=0)
                    current_test_rs = False
                else:
                    mtp_mgmt_ctrl.cli_log_inf("MTP Chassis timestamp sync'd", level=0)

            # Check if diag image updated is needed
            for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
                onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
                mtp_diag_image = MFG_IMAGE_FILES.MTP_AMD64_IMAGE
                nic_diag_image = MFG_IMAGE_FILES.MTP_ARM64_IMAGE
                if not libmfg_utils.mtp_update_diag_image(mtp_mgmt_ctrl, mtp_diag_image, nic_diag_image, onboard_image_files):
                    mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis diag image", level=0)
                    current_test_rs = False
                mtp_mgmt_ctrl.cli_log_inf("MTP Diag Image is updated", level=0)

        # load SNs
        if current_test_rs:
            for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
                if not mtp_mgmt_ctrl.mtp_diag_pre_init_start():
                    mtp_mgmt_ctrl.cli_log_err("MTP diag init failed", level=0)
                    current_test_rs = False

        # type check
        if current_test_rs:
            for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
                nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
                for slot in range(MTP_Const.MTP_SLOT_NUM):
                    if not nic_prsnt_list[slot]:
                        continue
                    if slot in fail_nic_list[mtp_id]:
                        continue
                    dsp = stage
                    test = "NIC_TYPE"
                    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                    ret = mtp_mgmt_ctrl.mtp_nic_type_test(slot)
                    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                    if not ret:
                        current_test_rs = False
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                        if slot not in fail_nic_list[mtp_id]:
                            fail_nic_list[mtp_id].append(slot)

        # Sanity check
        if current_test_rs:
            try:
                sanity_fail_list = libmfg_utils.sanity_check(mtp_cfg_db, mtpid_list, mtp_mgmt_ctrl_list, mtpid_fail_list, fail_nic_list, args.skip_test)
                if len(fail_nic_list[mtp_id]) > 0:
                    current_test_rs = False
            except Exception as e:
                err_msg = traceback.format_exc()
                current_test_rs = False
                for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
                    mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)

        mfg_end_ts = libmfg_utils.timestamp_snapshot()
        mtp_mgmt_ctrl.cli_log_inf("MFG Test Duration: {0}".format(mfg_end_ts - mfg_start_ts), level=0)
        mtp_mgmt_ctrl.cli_log_inf("MFG Test Log: {0}".format(logfile_dir_list[mtp_id]), level=0)
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
