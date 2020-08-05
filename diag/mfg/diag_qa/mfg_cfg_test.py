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
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db


def load_mtp_cfg():
    # DL/P2C MTP Chassis
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


def single_mtp_cfg_test(mtp_cfg_script_dir, mtp_mgmt_ctrl, mtp_id, mtp_test_summary):
    # go to mtp_cfg_script and start the test
    cmd = "cd {:s}".format(mtp_cfg_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    #mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MFG CFG Test Start", level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
    cmd = "./mtp_cfg_test.py --mtpid {:s}".format(mtp_id)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_CFG_TEST_TIMEOUT)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("MFG CFG Test Complete", level=0)
    #mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_cfg_script_dir, mtp_id, mtp_test_summary, FF_Stage.FF_CFG)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("MTP Collect CFG Test result failed", level=0)
        return
    # if GLB_CFG_MFG_TEST_MODE:
    #     libmfg_utils.mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, FF_Stage.FF_CFG)
    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)


def main():
    parser = argparse.ArgumentParser(description="MFG MTP CFG Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')

    fru_cfg_file = "fru_cfg.yaml"
    verbosity = False
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True

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

    if not libmfg_utils.file_exist(fru_cfg_file):
        libmfg_utils.cli_err("Unable to locate fru config file: {:s}".format(fru_cfg_file))
        return

    mfg_cfg_start_ts = libmfg_utils.timestamp_snapshot()

    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="CFG-SSH"):
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

        # Check if image updated is needed
        mtp_cfg_image_list = list()
        mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
        if (mtp_capability & 0x1):
            mtp_cfg_image_list.append(MFG_IMAGE_FILES.NAPLES100_CPLD_IMAGE)
            mtp_cfg_image_list.append(MFG_IMAGE_FILES.VOMERO_CPLD_IMAGE)
        if (mtp_capability & 0x2):
            mtp_cfg_image_list.append(MFG_IMAGE_FILES.NAPLES25_CPLD_IMAGE)
            mtp_dl_image_list.append(MFG_IMAGE_FILES.NAPLES25SWM_CPLD_IMAGE)    
            mtp_dl_image_list.append(MFG_IMAGE_FILES.NAPLES25_HPE_OCP_CPLD_IMAGE) 

        onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
        if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, mtp_cfg_image_list, onboard_image_files):
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
    mtp_cfg_script_dir = "mtp_cfg_script/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_cfg_script_pkg = "mtp_cfg_script.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP CFG Test script", level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_cfg_script_dir, mtp_cfg_script_pkg, fru_cfg_file):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP CFG Test script failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Deploy MTP CFG Test script complete", level=0)

    mtp_thread_list = list()
    mfg_cfg_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_cfg_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_cfg_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_cfg_script_dir,
                                                                            mtp_mgmt_ctrl,
                                                                            mtp_id,
                                                                            mfg_cfg_summary[mtp_id]))
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

    mfg_cfg_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP CFG Test Duration:{:s}".format(mfg_cfg_stop_ts - mfg_cfg_start_ts))

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

    # dump the summary
    libmfg_utils.mfg_summary_disp(FF_Stage.FF_CFG, mfg_cfg_summary, mtpid_fail_list)


if __name__ == "__main__":
    main()
