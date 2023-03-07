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

parser = argparse.ArgumentParser(description="MFG Final Test", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
parser.add_argument("-card_type", "--card_type", help="card type", type=str, default="general")
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


def single_mtp_fst_test(mtp_fst_script_dir, mtp_mgmt_ctrl, mtp_id, mtp_test_summary, card_type, stage, cfgyml=None, mirror_logdir=None):
    # go to mtp_fst_script and start the test
    cmd = "cd {:s}".format(mtp_fst_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MFG FST Test Start", level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
    cmd = "./mtp_fst_test.py --mtpid {:s} --card_type {:s} --stage {:s}".format(mtp_id, card_type, stage)
    if cfgyml:
        cmd += " --mtpcfg {:s}".format(cfgyml)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("MFG FST Test Complete", level=0)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    # For cloud card, collect logs at CHECK_PCIE stage
    if "CLOUD" in card_type or card_type == "ORTANO2ADIIBM":
        if stage == "FETCH_SN":
            return
    
    test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_fst_script_dir, mtp_id, mtp_test_summary, FF_Stage.FF_FST, mirror_logdir=mirror_logdir)
    mtp_mgmt_ctrl.cli_log_inf("Collect MTP Logfile {:s}".format(test_log_file), level=0)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("MTP Collect FST Test result failed", level=0)
        return
    cmd = "cp {:s} {:s}".format(test_log_file, mirror_logdir)
    os.system(cmd)
    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, FF_Stage.FF_FST, mtp_test_summary)
    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)
    return


def main():
    card_type = args.card_type.upper()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

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
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)

    mfg_fst_start_ts = libmfg_utils.timestamp_snapshot()

    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="FST-SSH", max_retry=10):
        #if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue

        # Sync timestamp to server
        timestamp_str = str(libmfg_utils.timestamp_snapshot())
        if not mtp_mgmt_ctrl.mtp_mgmt_set_date(timestamp_str, fst=True):
            mtp_mgmt_ctrl.cli_log_err("MTP Chassis timestamp sync failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Chassis timestamp sync'd", level=0)

        mtp_dl_image_list = list()
        onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
        if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, mtp_dl_image_list, onboard_image_files):
            mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis firmware", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP NIC firmware is updated", level=0)

        mtp_diag_image = MFG_IMAGE_FILES.penctl_img
        nic_diag_image = MFG_IMAGE_FILES.penctl_token_img

        if not libmfg_utils.mtp_update_fst_image(mtp_mgmt_ctrl, mtp_diag_image, nic_diag_image, onboard_image_files):
            mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis diag image", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag Image is updated", level=0)


    # Copy script, config file on to each MTP Chassis
    mtp_fst_script_dir = "mtp_fst_script/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_fst_script_pkg = "mtp_fst_script.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP FST Test script", level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_fst_script_dir, mtp_fst_script_pkg, extra_config=mtpcfg_file):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP FST Test script failed", level=1)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Deploy MTP FST Test script complete", level=0)
    # now that file has been packaged into config/, discard full path
    if mtpcfg_file:
        mtpcfg_file = os.path.basename(mtpcfg_file)

    mtp_thread_list = list()
    mfg_fst_summary = dict()
    stage = "FETCH_SN"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_fst_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_fst_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_fst_script_dir,
                                                                            mtp_mgmt_ctrl,
                                                                            mtp_id,
                                                                            mfg_fst_summary[mtp_id], 
                                                                            card_type,
                                                                            stage, mtpcfg_file, args.logdir))
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

    # for Cloud, we need to reboot and do stage II test
    if "CLOUD" in card_type or card_type == "ORTANO2ADIIBM":
        print("Power Cycle FST Server")
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            if not mtp_mgmt_ctrl.mtp_power_cycle():
                mtp_mgmt_ctrl.cli_log_err("Unable to reboot MTP Chassis", level=0)
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
            else:
                mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is power cycled", level=0)
                mtp_mgmt_ctrl.cli_log_inf("Disconnect MTP chassis...", level=0)
                mtp_mgmt_ctrl.mtp_mgmt_disconnect()

        # Connect to MTP
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="FST-SSH", max_retry=10):
                mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
            else:
                mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

        # Stage II test

        mtp_thread_list = list()
        mfg_fst_summary = dict()
        stage = "CHECK_PCIE"
        print("Performing pcie check")
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
            mfg_fst_summary[mtp_id] = list()
            mtp_thread = threading.Thread(target = single_mtp_fst_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_fst_script_dir,
                                                                                mtp_mgmt_ctrl,
                                                                                mtp_id,
                                                                                mfg_fst_summary[mtp_id], 
                                                                                card_type,
                                                                                stage, mtpcfg_file))
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
