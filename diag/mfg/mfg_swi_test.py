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


def load_mtp_cfg(cfg_yaml=None):
    mtp_chassis_cfg_file_list = list()
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath(cfg_yaml))
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/swi_mtp_chassis_cfg.yaml"))
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


def single_mtp_swi_test(mtp_swi_script_dir, nic_sw_img_file_list, profile_cfg_file_list, mtp_mgmt_ctrl, mtp_id, fail_nic_list, mtp_test_summary, sw_pn_list, skip_testlist = [], mtpcfg_file=None, mirror_logdir=None):
    stage = FF_Stage.FF_SWI

    img_opts = ""
    for nic_sw_img_file in nic_sw_img_file_list:
        img_opts += nic_sw_img_file + " "

    sw_pn_opts = ""
    for sw_pn in sw_pn_list:
        sw_pn_opts += sw_pn + " "

    # go to mtp_swi_script and start the test
    cmd = "cd {:s}".format(mtp_swi_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MFG SW Install Test Start", level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)

    if profile_cfg_file_list:
        profile_cfg_file = profile_cfg_file_list[0] # multiple profiles not supported
        cmd = "./mtp_swi_test.py --image {:s} --profile {:s} --mtpid {:s} --swpn {:s}".format(img_opts, profile_cfg_file, mtp_id, sw_pn_opts)
    else:
        cmd = "./mtp_swi_test.py --image {:s} --mtpid {:s} --swpn {:s}".format(img_opts, mtp_id, sw_pn_opts)
    if skip_testlist:
        skipped_testlist = " --skip-test {:s}".format('"'+'" "'.join(skip_testlist).strip()+'"')
    else:
        skipped_testlist = ""
    if fail_nic_list:
        fail_slots_cmd = " --fail-slots "
        fail_slots_cmd += ' '.join(map(str, fail_nic_list))
    else:
        fail_slots_cmd = ""
    cmd += skipped_testlist
    cmd += fail_slots_cmd
    if mtpcfg_file:
        cmd += " --mtpcfg " + mtpcfg_file
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_SW_TEST_TIMEOUT)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("MFG SW Install Test Complete", level=0)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    # save the ecc dump files
    asic_sub_dir = "/asic_logs/"
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_swi_script_dir + asic_sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    # cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, mtp_swi_script_dir + asic_sub_dir)
    # mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_DUMP_FILES, mtp_swi_script_dir + asic_sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_swi_script_dir, mtp_id, mtp_test_summary, stage, mirror_logdir=mirror_logdir)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("MTP Collect SW Install Test result failed", level=0)
        return
    libmfg_utils.assign_nic_retest_flag(test_log_file, mtp_test_summary, stage)
    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, stage, mtp_test_summary)
    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)
    return


def main():
    parser = argparse.ArgumentParser(description="MFG Software Install Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser.add_argument("--sw-pn", "-swpn", "--swpn", "-sw-pn", help="pre-select SW PN or list of SW PNs", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
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

    # get sw image name based on the sw pn
    if not args.sw_pn:
        sw_pn_list = [libmfg_utils.sw_pn_scan()]
    else:
        sw_pn_list = args.sw_pn
    for sw_pn in sw_pn_list:
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
            mtp_mgmt_ctrl.cli_log_inf("No Profile will apply to PN: {:s}".format(sw_pn), level=0)
            profile_cfg_file = None
        else:
            profile_cfg_file = "release/" + os.readlink(profile_link_cfg_file)
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

    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, stage=stage, level=0):
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue

    # load SNs
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_diag_pre_init_start():
            mtp_mgmt_ctrl.cli_log_err("MTP diag init failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue

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
        mtp_swi_image_list = list()
        mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
        for nic_sw_img_file in nic_sw_img_file_list:
            mtp_swi_image_list.append(nic_sw_img_file)
        if (mtp_capability & 0x1):
            for card_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.cpld_img[card_type])
                    if card_type == NIC_Type.NAPLES100HPE:
                        mtp_swi_image_list.append(NIC_IMAGES.cpld_img["P41854"])
                    if card_type == NIC_Type.ORTANO2ADI:
                        mtp_swi_image_list.append(NIC_IMAGES.cpld_img["68-0026"])
                        mtp_swi_image_list.append(NIC_IMAGES.fail_cpld_img["68-0026"])
                    if card_type == NIC_Type.ORTANO2ADIIBM:
                        mtp_swi_image_list.append(NIC_IMAGES.cpld_img["68-0028"])
                        mtp_swi_image_list.append(NIC_IMAGES.fail_cpld_img["68-0028"])
                    if card_type == NIC_Type.ORTANO2ADIMSFT:
                        mtp_swi_image_list.append(NIC_IMAGES.cpld_img["68-0034"])
                        mtp_swi_image_list.append(NIC_IMAGES.fail_cpld_img["68-0034"])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img[card_type])
                    if card_type == NIC_Type.NAPLES100HPE:
                        mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img["P41854"])
                    if card_type == NIC_Type.ORTANO2ADI:
                        mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img["68-0026"])
                    if card_type == NIC_Type.ORTANO2ADIIBM:
                        mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img["68-0028"])
                    if card_type == NIC_Type.ORTANO2ADIMSFT:
                        mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img["68-0034"])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing secure cpld image for {:s}".format(card_type))
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.goldfw_img[card_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing goldfw image for {:s}".format(card_type))
                if card_type == NIC_Type.ORTANO2ADIIBM:
                    try:
                        mtp_swi_image_list.append(NIC_IMAGES.cert_img["68-0028"])
                        mtp_swi_image_list.append(NIC_IMAGES.goldfw_img["68-0028"])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing goldfw & cert image for {:s}".format(card_type))
        if (mtp_capability & 0x2):
            for card_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST + ["P41851", "P46653", "68-0016", "68-0017"]:
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.cpld_img[card_type])
                    if card_type == NIC_Type.NAPLES100HPE:
                        mtp_swi_image_list.append(NIC_IMAGES.cpld_img["P41854"])
                    if card_type == NIC_Type.ORTANO2ADI:
                        mtp_swi_image_list.append(NIC_IMAGES.cpld_img["68-0026"])
                        mtp_swi_image_list.append(NIC_IMAGES.fail_cpld_img["68-0026"])
                    if card_type == NIC_Type.ORTANO2ADIIBM:
                        mtp_swi_image_list.append(NIC_IMAGES.cpld_img["68-0028"])
                        mtp_swi_image_list.append(NIC_IMAGES.fail_cpld_img["68-0028"])
                    if card_type == NIC_Type.ORTANO2ADIMSFT:
                        mtp_swi_image_list.append(NIC_IMAGES.cpld_img["68-0034"])
                        mtp_swi_image_list.append(NIC_IMAGES.fail_cpld_img["68-0034"])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img[card_type])
                    if card_type == NIC_Type.NAPLES100HPE:
                        mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img["P41854"])
                    if card_type == NIC_Type.ORTANO2ADI:
                        mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img["68-0026"])
                    if card_type == NIC_Type.ORTANO2ADIIBM:
                        mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img["68-0028"])
                    if card_type == NIC_Type.ORTANO2ADIMSFT:
                        mtp_swi_image_list.append(NIC_IMAGES.sec_cpld_img["68-0034"])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing secure cpld image for {:s}".format(card_type))
                try:
                    mtp_swi_image_list.append(NIC_IMAGES.goldfw_img[card_type])
                    mtp_swi_image_list.append(NIC_IMAGES.goldfw_img["68-0015"])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing goldfw image for {:s}".format(card_type))
                if card_type in ELBA_NIC_TYPE_LIST or card_type in GIGLIO_NIC_TYPE_LIST:
                    try:
                        mtp_swi_image_list.append(NIC_IMAGES.fail_cpld_img[card_type])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                if card_type in FPGA_TYPE_LIST:
                    try:
                        mtp_swi_image_list.append(NIC_IMAGES.timer1_img[card_type])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing timer1 image for {:s}".format(card_type))
                    try:
                        mtp_swi_image_list.append(NIC_IMAGES.timer2_img[card_type])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing timer2 image for {:s}".format(card_type))
                    try:
                        mtp_swi_image_list.append(NIC_IMAGES.uboot_img[card_type])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing uboot image for {:s}".format(card_type))
                if card_type == NIC_Type.ORTANO2ADIIBM:
                    try:
                        mtp_swi_image_list.append(NIC_IMAGES.cert_img["68-0028"])
                        mtp_swi_image_list.append(NIC_IMAGES.goldfw_img["68-0028"])
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing goldfw & cert image for {:s}".format(card_type))

        onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
        if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, mtp_swi_image_list, onboard_image_files):
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
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            if GLB_CFG_MFG_TEST_MODE and FLEX_SHOP_FLOOR_CONTROL:
                if sn is not None and str(sn).upper() != "UNKNOWN" and str(sn).upper() != "NONE" and len(str(sn)) > 6:
                    pre_post_fail_list = libmfg_utils.flx_web_srv_two_way_comm_precheck_uut(mtp_mgmt_ctrl, fail_nic_list[mtp_id], sn, stage, slot, retry=FLEX_TWO_WAY_COMM.PRE_POST_RETRY)

    # Close file handles
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])
    for mtp_id in mtpid_fail_list:
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])

    # Copy script, config file on to each MTP Chassis
    mtp_swi_script_dir = "mtp_swi_script/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_swi_script_pkg = "mtp_swi_script.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP SW Install Test script", level=0)
        profile_cfg_file = " ".join(x for x in profile_cfg_file_list)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_swi_script_dir, mtp_swi_script_pkg, logfile_dir_list[mtp_id], profile_cfg_file, extra_config=mtpcfg_file):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP SW Install Test script failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Deploy MTP SW Install Test script complete", level=0)
    # now that file has been packaged into config/, discard full path
    if mtpcfg_file:
        mtpcfg_file = os.path.basename(mtpcfg_file)

    mtp_thread_list = list()
    mfg_swi_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_swi_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_swi_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_swi_script_dir,
                                                                            nic_sw_img_file_list,
                                                                            profile_cfg_file_list,
                                                                            mtp_mgmt_ctrl,
                                                                            mtp_id,
                                                                            fail_nic_list[mtp_id],
                                                                            mfg_swi_summary[mtp_id],
                                                                            sw_pn_list,
                                                                            args.skip_test,
                                                                            mtpcfg_file,
                                                                            args.jobd_logdir))
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
