#!/usr/bin/env python

import sys
import os
import time
import pexpect
import re
import argparse
import threading

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import Env_Cond
from libdefs import Swm_Test_Mode
from libdefs import NIC_Type
from libdefs import FF_Stage
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db


def load_mtp_cfg():
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
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
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg)
    return mtp_mgmt_ctrl


def single_mtp_4c_test(mtp_script_dir, mtp_mgmt_ctrl, mtp_id, stage, fail_nic_list, mtp_test_summary, swm_test_mode, l1_sequence, skip_test=[]):
    if skip_test:
        skipped_testlist = " --skip-test {:s}".format('"'+'" "'.join(skip_test).strip()+'"')
    else:
        skipped_testlist = ""
    if fail_nic_list:
        fail_slots = " --fail-slots "
        fail_slots += ' '.join(map(str,fail_nic_list))
    else:
        fail_slots = ""
    # go to mtp_regression and Start the regression
    cmd = "cd {:s}".format(mtp_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MFG {:s} Test Start".format(stage), level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
    if stage == FF_Stage.FF_4C_H:
        cmd = "./mtp_diag_regression.py --mtpid {:s} --corner {:s} --swm {:s}".format(mtp_id, Env_Cond.MFG_HT, swm_test_mode)
    else:
        cmd = "./mtp_diag_regression.py --mtpid {:s} --corner {:s} --swm {:s}".format(mtp_id, Env_Cond.MFG_LT, swm_test_mode)
    if skip_test:
        cmd += skipped_testlist
    if fail_slots:
        cmd += fail_slots
    if l1_sequence:
        cmd += " --l1-seq "
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_4C_TEST_TIMEOUT)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("MFG {:s} Test Complete".format(stage), level=0)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_script_dir, mtp_id, mtp_test_summary, stage)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("MTP Collect {:s} Test result failed".format(stage), level=0)
        return
    libmfg_utils.assign_nic_retest_flag(test_log_file, mtp_test_summary, stage)
    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, stage)
    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)
    return


def main():
    parser = argparse.ArgumentParser(description="MFG 4C Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--high-temp", help="high temperature environment", action='store_true')
    parser.add_argument("--low-temp", help="low temperature environment", action='store_true')
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip-test", help="skip a particular test section", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser.add_argument("--l1-seq", help="asic L1 run under sequence mode", action='store_true')

    verbosity = False
    l1_sequence = False
    swmtestmode = Swm_Test_Mode.SW_DETECT
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    if args.swm:
        swmtestmode = args.swm

    if verbosity:
        diag_log_filep = sys.stdout
        diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
    else:
        diag_log_filep = None
        diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM

    if args.l1_seq:
        l1_sequence = True

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
    mtp_mgmt_ctrl_list = list()
    mtpid_fail_list = list()
    fail_nic_list = dict()

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

    # wait operator set chamber temperature
    if args.high_temp:
        libmfg_utils.cli_inf("CLOSE THE CHAMBER AND SET TEMPERATURE TO {:d} DEGREE CENTIGRADE\n".format(MTP_Const.MFG_EDVT_HIGH_TEMP))
        libmfg_utils.action_confirm("SCAN *STOP* TO START TEST", "STOP")
        stage = FF_Stage.FF_4C_H
    elif args.low_temp:
        libmfg_utils.cli_inf("CLOSE THE CHAMBER AND SET TEMPERATURE TO {:d} DEGREE CENTIGRADE\n".format(MTP_Const.MFG_EDVT_LOW_TEMP))
        libmfg_utils.action_confirm("SCAN *STOP* TO START TEST", "STOP")
        stage = FF_Stage.FF_4C_L
    else:
        libmfg_utils.sys_exit("Unknown 4C Corner... Abort")

    # logfiles
    open_file_track_mtp_list = dict()
    logfile_dir_list = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id] = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)

    mfg_4c_start_ts = libmfg_utils.timestamp_snapshot()

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list, safely=False)
    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="4C-SSH", retry_with_powercycle=True):
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis. Abort test", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        # Check if image updated is needed
        mtp_dl_image_list = list()
        mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
        if (mtp_capability & 0x1):
            for card_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.cpld_img[card_type])
                    if card_type == NIC_Type.NAPLES100HPE:
                        mtp_dl_image_list.append(NIC_IMAGES.cpld_img["P41854"])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.diagfw_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(card_type))
        if (mtp_capability & 0x2):
            for card_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST + ["P41851", "P46653", "68-0016", "68-0017"]:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.cpld_img[card_type])
                    if card_type == NIC_Type.NAPLES100HPE:
                        mtp_dl_image_list.append(NIC_IMAGES.cpld_img["P41854"])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.diagfw_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(card_type))
                try:
                    if card_type == NIC_Type.LACONA32 or card_type == NIC_Type.LACONA32DELL:
                        mtp_dl_image_list.append(NIC_IMAGES.uboot_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing uboot image for {:s}".format(card_type))

        onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
        if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, mtp_dl_image_list, onboard_image_files):
            mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis firmware", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP NIC firmware is updated", level=0)

        onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
        mtp_diag_image = MFG_IMAGE_FILES.MTP_AMD64_IMAGE
        nic_diag_image = MFG_IMAGE_FILES.MTP_ARM64_IMAGE
        if not libmfg_utils.mtp_update_diag_image(mtp_mgmt_ctrl, mtp_diag_image, nic_diag_image, onboard_image_files):
            mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis diag image", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag Image is updated", level=0)

    # Sync timestamp to server
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        timestamp_str = str(libmfg_utils.timestamp_snapshot())
        if not mtp_mgmt_ctrl.mtp_mgmt_set_date(timestamp_str):
            mtp_mgmt_ctrl.cli_log_err("MTP Chassis timestamp sync failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Chassis timestamp sync'd", level=0)

    # close file handles
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])
    for mtp_id in mtpid_fail_list:
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])

    # Copy script, config file on to each MTP Chassis
    mtp_4c_script_dir = "mtp_regression/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_4c_script_pkg = "mtp_regression.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP {:s} Test script".format(stage), level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_4c_script_dir, mtp_4c_script_pkg, logfile_dir_list[mtp_id]):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP {:s} Test script failed".format(stage), level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Deploy MTP {:s} Test script complete".format(stage), level=0)

    mtp_thread_list = list()
    mfg_4c_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_4c_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_4c_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_4c_script_dir,
                                                                           mtp_mgmt_ctrl,
                                                                           mtp_id,
                                                                           stage,
                                                                           fail_nic_list[mtp_id],
                                                                           mfg_4c_summary[mtp_id],
                                                                           swmtestmode,
                                                                           l1_sequence,
                                                                           args.skip_test))
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

    mfg_4c_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG {:s} Test Duration:{:s}".format(stage, mfg_4c_stop_ts - mfg_4c_start_ts))

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

    # dump the summary
    libmfg_utils.mfg_summary_disp(stage, mfg_4c_summary, mtpid_fail_list)

if __name__ == "__main__":
    main()
