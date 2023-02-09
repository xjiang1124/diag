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
from libmfg_cfg import FPGA_TYPE_LIST
from libmfg_cfg import NEED_UBOOT_IMG_CARD_TYPE_LIST
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


def single_mtp_dl_test(mtp_dl_script_dir, mtp_mgmt_ctrl, mtp_id, fail_nic_list, mtp_test_summary, swm_test_mode, skip_testlist=[], rework=False):
    stage = FF_Stage.FF_DL

    # go to mtp_dl_test and start the test
    cmd = "cd {:s}".format(mtp_dl_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MFG DL Test Start", level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)

    cmd = None
    if skip_testlist:
        skipped_testlist = " --skip-test {:s}".format('"'+'" "'.join(skip_testlist).strip()+'"')
    else:
        skipped_testlist = ""
    if fail_nic_list:
        fail_slots = " --fail-slots "
        fail_slots += ' '.join(map(str,fail_nic_list))
    else:
        fail_slots = ""
    cmd = "./mtp_dl_test.py --mtpid {:s} --swm {:s}".format(mtp_id, swm_test_mode)
    if skipped_testlist:
        cmd += skipped_testlist
    if fail_slots:
        cmd += fail_slots

    if rework:
        cmd = cmd.replace("mtp_dl_test.py", "mtp_rework_nic.py")

    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_DL_TEST_TIMEOUT)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("MFG DL Test Complete", level=0)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    # save the avs and ecc dump log files
    asic_sub_dir = "/asic_logs/"
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_dl_script_dir + asic_sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, mtp_dl_script_dir + asic_sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_DUMP_FILES, mtp_dl_script_dir + asic_sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_dl_script_dir, mtp_id, mtp_test_summary, stage)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("MTP Collect DL Test result failed", level=0)
        return
    libmfg_utils.assign_nic_retest_flag(test_log_file, mtp_test_summary, stage)
    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, stage, mtp_test_summary)
    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)


def main():
    parser = argparse.ArgumentParser(description="MFG MTP DL Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("-r", "--rework", help="Call rework script", action='store_true')
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])

    verbosity = False
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True

    swmtestmode = Swm_Test_Mode.SW_DETECT  
    if args.swm:
        swmtestmode = args.swm

    if not args.rework:
        rework = False

    stage = FF_Stage.FF_DL

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
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list)
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)
        fail_nic_list[mtp_id] = list()
        nic_sn_list[mtp_id] = list()
        invalid_nic_list[mtp_id] = list()

    # logfiles
    open_file_track_mtp_list = dict()
    logfile_dir_list = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id] = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)

    if not GLB_CFG_MFG_TEST_MODE:
        args.skip_test.append("SCAN_VERIFY")

    if "SCAN_VERIFY" not in args.skip_test:
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            libmfg_utils.single_mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id], swmtestmode)

    mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list, safely=False)
    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="DL-SSH", retry_with_powercycle=True):
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis. Abort test", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

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

    # Check if diag image updated is needed
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
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

    # load SNs
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_diag_pre_init_start():
            mtp_mgmt_ctrl.cli_log_err("MTP diag init failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

    # type check
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
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                if slot not in fail_nic_list[mtp_id]:
                    fail_nic_list[mtp_id].append(slot)

    # Check that firmware images are present
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
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
                    if card_type == NIC_Type.ORTANO2ADI:
                        mtp_dl_image_list.append(NIC_IMAGES.goldfw_img["ORTANO2ADI"])
                    if card_type == NIC_Type.ORTANO2ADIIBM:
                        mtp_dl_image_list.append(NIC_IMAGES.goldfw_img["ORTANO2ADIIBM"])
                    if card_type == NIC_Type.ORTANO2ADIMSFT:
                        mtp_dl_image_list.append(NIC_IMAGES.goldfw_img["ORTANO2ADIMSFT"])
                    if card_type == NIC_Type.ORTANO2ADICR:
                        mtp_dl_image_list.append(NIC_IMAGES.goldfw_img["ORTANO2ADICR"])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing goldfw image for {:s}".format(card_type))
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.diagfw_img[card_type])
                    mtp_dl_image_list.append(NIC_IMAGES.diagfw_img["68-0010"])
                    mtp_dl_image_list.append(NIC_IMAGES.diagfw_img["68-0015"])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(card_type))
                if card_type in ELBA_NIC_TYPE_LIST:
                    try:
                        mtp_dl_image_list.append(NIC_IMAGES.fail_cpld_img[card_type])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing failsafe cpld image for {:s}".format(card_type))
                if card_type in ELBA_NIC_TYPE_LIST and card_type not in FPGA_TYPE_LIST:
                    try:
                        mtp_dl_image_list.append(NIC_IMAGES.fea_cpld_img[card_type])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing feature row image for {:s}".format(card_type))
            for card_type in FPGA_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.timer1_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing timer1 image for {:s}".format(card_type))
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.timer2_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing timer2 image for {:s}".format(card_type))
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.uboot_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing uboot image for {:s}".format(card_type))

            for card_type in NEED_UBOOT_IMG_CARD_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.uboot_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing uboot image for {:s}".format(card_type))

        if not GLB_CFG_MFG_TEST_MODE:
            mtp_dl_image_list.append(NIC_IMAGES.fea_cpld_img["ORTANO2"])
        mtp_dl_image_list.append(NIC_IMAGES.uboot_img["INSTALLER"])

        mtp_dl_image_list = list(set(mtp_dl_image_list))
        if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, mtp_dl_image_list, onboard_image_files):
            mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis firmware", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP NIC firmware is updated", level=0)

    # Flex flow 2 Way communication Pre-Post 
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list[mtp_id]:
                continue
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            if GLB_CFG_MFG_TEST_MODE and FLEX_SHOP_FLOOR_CONTROL:
                pre_post_fail_list = libmfg_utils.flx_web_srv_two_way_comm_precheck_uut(mtp_mgmt_ctrl, fail_nic_list[mtp_id], sn, stage, slot, retry=FLEX_TWO_WAY_COMM.PRE_POST_RETRY)

    # Close file handles
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])
    for mtp_id in mtpid_fail_list:
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])

    # Copy script, config file on to each MTP Chassis
    mtp_dl_script_dir = "mtp_dl_script/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_dl_script_pkg = "mtp_dl_script.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP DL Test script", level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_dl_script_dir, mtp_dl_script_pkg, logfile_dir_list[mtp_id]):
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
                                                                           fail_nic_list[mtp_id],
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
    libmfg_utils.mfg_summary_disp(stage, mfg_dl_summary, mtpid_fail_list)


if __name__ == "__main__":
    main()
