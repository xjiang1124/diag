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
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl


def load_mtp_cfg():
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/swi_mtp_chassis_cfg.yaml"))
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


def single_mtp_swi_test(mtp_swi_script_dir, nic_sw_img_file, profile_cfg_file, mtp_mgmt_ctrl, mtp_id, mtp_test_summary, sw_pn, skip_testlist = []):
    # go to mtp_swi_script and start the test
    cmd = "cd {:s}".format(mtp_swi_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MFG SW Install Test Start", level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
    if profile_cfg_file:
        cmd = "./mtp_swi_test.py --image {:s} --profile {:s} --mtpid {:s} --swpn {:s}".format(nic_sw_img_file, profile_cfg_file, mtp_id, sw_pn)
    else:
        cmd = "./mtp_swi_test.py --image {:s} --mtpid {:s} --swpn {:s}".format(nic_sw_img_file, mtp_id, sw_pn)
    if skip_testlist:
        skipped_testlist = " --skip-test {:s}".format('"'+'" "'.join(skip_testlist).strip()+'"')
    else:
        skipped_testlist = ""
    cmd += skipped_testlist
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_SW_TEST_TIMEOUT)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("MFG SW Install Test Complete", level=0)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_swi_script_dir, mtp_id, mtp_test_summary, FF_Stage.FF_SWI)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("MTP Collect SW Install Test result failed", level=0)
        return
    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, FF_Stage.FF_SWI)
    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)
    return


def main():
    parser = argparse.ArgumentParser(description="MFG Software Install Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db)
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
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)

    # get sw image name based on the sw pn
    sw_pn = libmfg_utils.sw_pn_scan()
    nic_sw_link_file = "release/{:s}".format(sw_pn)
    if not libmfg_utils.file_exist(nic_sw_link_file):
        mtp_mgmt_ctrl.cli_log_err("Software image link {:s} doesn't exist... Abort".format(nic_sw_link_file), level=0)
        return
    nic_sw_img_file = os.readlink(nic_sw_link_file)

    profile_link_cfg_file = "release/profile_{:s}.py".format(sw_pn)
    if not libmfg_utils.file_exist(profile_link_cfg_file):
        mtp_mgmt_ctrl.cli_log_inf("No Profile will apply to PN: {:s}".format(sw_pn), level=0)
        profile_cfg_file = None
    else:
        profile_cfg_file = "release/" + os.readlink(profile_link_cfg_file)
        mtp_mgmt_ctrl.cli_log_inf("Profile {:s} will apply to PN: {:s}".format(profile_cfg_file, sw_pn), level=0)

    mfg_swi_start_ts = libmfg_utils.timestamp_snapshot()

    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="SW-SSH"):
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

        # Check if image updated is needed
        mtp_swi_image_list = list()
        mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
        mtp_swi_image_list.append(nic_sw_img_file)
        if (mtp_capability & 0x1):
            for card_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.cpld_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                    continue
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing secure cpld image for {:s}".format(card_type))
                    continue
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.goldfw_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing goldfw image for {:s}".format(card_type))
                    continue
        if (mtp_capability & 0x2):
            for card_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.cpld_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                    continue
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing secure cpld image for {:s}".format(card_type))
                    continue
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.goldfw_img[card_type])
                    mtp_swi_image_list.append(NIC_IMAGES.goldfw_img["68-0015"])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing goldfw image for {:s}".format(card_type))
                    continue
                if card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2:
                    try:
                        mtp_swi_image_list.append(NIC_IMAGES.fail_cpld_img[card_type])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        continue

        onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
        if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, mtp_swi_image_list, onboard_image_files):
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
    mtp_swi_script_dir = "mtp_swi_script/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_swi_script_pkg = "mtp_swi_script.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP SW Install Test script", level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_swi_script_dir, mtp_swi_script_pkg, profile_cfg_file):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP SW Install Test script failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Deploy MTP SW Install Test script complete", level=0)

    mtp_thread_list = list()
    mfg_swi_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_swi_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_swi_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_swi_script_dir,
                                                                            nic_sw_img_file,
                                                                            profile_cfg_file,
                                                                            mtp_mgmt_ctrl,
                                                                            mtp_id,
                                                                            mfg_swi_summary[mtp_id],
                                                                            sw_pn,
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

    mfg_swi_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP Software Install Test Duration:{:s}".format(mfg_swi_stop_ts - mfg_swi_start_ts))

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

    # dump the summary
    libmfg_utils.mfg_summary_disp(FF_Stage.FF_SWI, mfg_swi_summary, mtpid_fail_list)

    return

if __name__ == "__main__":
    main()
