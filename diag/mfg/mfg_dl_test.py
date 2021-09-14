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
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import FF_Stage
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
from libdefs import Swm_Test_Mode


def load_mtp_cfg():
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
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


def single_mtp_dl_test(mtp_dl_script_dir, mtp_mgmt_ctrl, mtp_id, mtp_test_summary, swm_test_mode, skip_testlist = [], rework=False):

    # go to mtp_dl_test and start the test
    cmd = "cd {:s}".format(mtp_dl_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MFG DL Test Start", level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)

    cmd = None
    if skip_testlist:
        skipped_testlist = "--skip-test {:s}".format('"'+'" "'.join(skip_testlist).strip()+'"')
    else:
        skipped_testlist = ""
    cmd = "./mtp_dl_test.py --mtpid {:s} --swm {:s} {:s}".format(mtp_id, swm_test_mode, skipped_testlist)

    if rework:
        cmd = cmd.replace("mtp_dl_test.py", "mtp_rework_nic.py")

    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_DL_TEST_TIMEOUT)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("MFG DL Test Complete", level=0)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    # save the avs log files
    asic_sub_dir = "/asic_logs/"
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_dl_script_dir + asic_sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, mtp_dl_script_dir + asic_sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_dl_script_dir, mtp_id, mtp_test_summary, FF_Stage.FF_DL)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("MTP Collect DL Test result failed", level=0)
        return
    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, FF_Stage.FF_DL)
    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)


def main():
    parser = argparse.ArgumentParser(description="MFG MTP DL Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("-r", "--rework", help="Call rework script", action='store_true')
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])

    verbosity = False
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True

    swmtestmode = Swm_Test_Mode.SW_DETECT  
    if args.swm:
        swmtestmode = args.swm

    if not args.rework:
        rework = False

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db)
    mtp_mgmt_ctrl_list = list()
    mtpid_fail_list = list()

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

    mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="DL-SSH"):
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

        # Check if image updated is needed
        mtp_dl_image_list = list()
        mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
        if (mtp_capability & 0x1):
            for card_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.cpld_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                    continue
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.diagfw_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(card_type))
                    continue
        if (mtp_capability & 0x2):
            for card_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.cpld_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                    continue
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.diagfw_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(card_type))
                    continue

                if card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2 or card_type == NIC_Type.POMONTEDELL:
                    try:
                        mtp_dl_image_list.append(NIC_IMAGES.fail_cpld_img[card_type])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing failsafe cpld image for {:s}".format(card_type))
                        continue
                if nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
                    try:
                        mtp_dl_image_list.append(NIC_IMAGES.fea_cpld_img[card_type])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing feature row image for {:s}".format(card_type))
                        continue
        if not GLB_CFG_MFG_TEST_MODE:
            mtp_dl_image_list.append(NIC_IMAGES.fea_cpld_img["ORTANO2"])
        onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
        if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, mtp_dl_image_list, onboard_image_files):
            mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis firmware", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP NIC firmware is updated", level=0)

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

    # Copy script, config file on to each MTP Chassis
    mtp_dl_script_dir = "mtp_dl_script/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_dl_script_pkg = "mtp_dl_script.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP DL Test script", level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_dl_script_dir, mtp_dl_script_pkg):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP DL Test script failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Deploy MTP DL Test script complete", level=0)

    mtp_thread_list = list()
    mfg_dl_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_dl_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_dl_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_dl_script_dir,
                                                                           mtp_mgmt_ctrl,
                                                                           mtp_id,
                                                                           mfg_dl_summary[mtp_id],
                                                                           swmtestmode,
                                                                           args.skip_test, 
                                                                           args.rework))
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

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

    # dump the summary
    libmfg_utils.mfg_summary_disp(FF_Stage.FF_DL, mfg_dl_summary, mtpid_fail_list)


if __name__ == "__main__":
    main()
