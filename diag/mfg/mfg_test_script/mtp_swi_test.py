#!/usr/bin/env python3

import sys
import os
import argparse
import re
import ntpath
import time
import traceback

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import PSLC_MODE_TYPE_LIST
from libmfg_cfg import CAPRI_NIC_TYPE_LIST
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import GIGLIO_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmfg_cfg import FAILSAFE_CPLD_TYPE_LIST
from libmfg_cfg import MAINFW_TYPE_LIST
from libmfg_cfg import CTO_MODEL_TYPE_LIST
from libmfg_cfg import SWI_UPDATE_FRU_TYPE_LIST
from libmfg_cfg import MFG_VALID_NIC_TYPE_LIST
from libmfg_cfg import MTP_HEALTH_MONITOR
from libmfg_cfg import DRY_RUN
from libmfg_cfg import SALINA_NIC_TYPE_LIST
from libmfg_cfg import SALINA_DPU_NIC_TYPE_LIST
from libmfg_cfg import SALINA_AI_NIC_TYPE_LIST
from libdefs import MTP_TYPE
from libdefs import FF_Stage
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode
import image_control
import testlog
import test_utils
import parallelize
import scanning

def logfile_close(filep_list):
    for fp in filep_list:
        fp.close()
    os.system("sync")


def load_mtp_cfg(cfg_yaml=None):
    mtp_chassis_cfg_file_list = list()
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/"+cfg_yaml))
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

def swi_display_program_matrix(mtp_mgmt_ctrl, slot):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    sku = mtp_mgmt_ctrl.get_scanned_sku(slot)

    swi_image_dict = image_control.get_all_images_for_stage(mtp_mgmt_ctrl, slot, FF_Stage.FF_SWI)
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Software Program Matrix:")
    if sku:
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SKU: {:s}".format(sku))
    for image_name, image_file_path in list(swi_image_dict.items()):
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, image_name + " image: " + os.path.basename(image_file_path))
        img_chksum = mtp_mgmt_ctrl.mtp_get_file_md5sum(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_file_path)
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, image_name + " MD5 checksum: " + img_chksum)

    if nic_type == NIC_Type.NAPLES100:
        nic_profile = "netapp_nic_profile.py"
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Profile: " + os.path.basename(nic_profile))

    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Software Program Matrix end\n")

@parallelize.parallel_nic_using_ssh
def swi_fru_program(mtp_mgmt_ctrl, slot):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    mac = mtp_mgmt_ctrl.mtp_get_nic_fru(slot)[1].replace('-', '')
    pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot)
    dpn = mtp_mgmt_ctrl.mtp_get_nic_dpn(slot)
    sku = mtp_mgmt_ctrl.get_scanned_sku(slot) if mtp_mgmt_ctrl.get_scanned_sku(slot) not in ("POLLARA-1Q400P-D", "POLLARA-1Q400P-H") else "POLLARA-1Q400P"
    prog_date = mtp_mgmt_ctrl.get_scanned_ts(slot)
    return mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn, dpn, sku, stage=FF_Stage.FF_SWI)

@parallelize.parallel_nic_using_ssh
def swi_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.PANAREA:
        return mtp_mgmt_ctrl.mtp_nic_uc_zephyr_cpld_update(slot, cpld_img_file, dl_step=False)
    else:
        return mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file, dl_step=False)

@parallelize.parallel_nic_using_ssh
def swi_fail_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.PANAREA:
        return mtp_mgmt_ctrl.mtp_nic_uc_zephyr_cpld_update(slot, failsafe_cpld_img_file, partition='1', dl_step=False)
    else:
        return mtp_mgmt_ctrl.mtp_program_nic_failsafe_cpld(slot, failsafe_cpld_img_file)

@parallelize.parallel_nic_using_ssh
def swi_secure_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_sec_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_sec_cpld(slot, sec_cpld_img_file)

@parallelize.parallel_nic_using_ssh
def swi_ufm1_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    ufm1_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_ufm1(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_ufm1(slot, ufm1_img_file)

@parallelize.parallel_nic_using_ssh
def dl_ufm1_cfg0_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    ufm1_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_ufm1(mtp_mgmt_ctrl, slot, dsp)["filename"]
    cfg0_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_ufm1_cfg0(slot, ufm1_img_file, cfg0_img_file)

@parallelize.parallel_nic_using_ssh
def swi_cpld_compare(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_sec_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_compare_nic_cpld_img(slot, sec_cpld_img_file, "cfg0")

@parallelize.parallel_nic_using_ssh
def swi_fail_cpld_compare(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_compare_nic_cpld_img(slot, failsafe_cpld_img_file, "cfg1")

@parallelize.parallel_nic_using_ssh
def swi_goldfw_copy(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_goldfw(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_copy_nic_gold(slot, gold_img_file)

@parallelize.parallel_nic_using_ssh
def swi_cert_copy(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    cert_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cert(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_copy_nic_cert(slot, cert_img_file, directory="/data/")

@parallelize.parallel_nic_using_ssh
def swi_goldfw_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_goldfw(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_gold(slot, gold_img_file)

@parallelize.parallel_nic_using_ssh
def swi_mainfw_install(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    emmc_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_mainfw(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_emmc(slot, emmc_img_file)

@parallelize.parallel_nic_using_ssh
def swi_fw_img_store_to_emmc(mtp_mgmt_ctrl, slot):
    # since the SWI QSPI image OOB may not enable, so we save the mainfw and goldfw binary file to emmc with an OOB QSPI image before SWI official test
    dsp = FF_Stage.FF_SWI
    emmc_mainfw_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_mainfw(mtp_mgmt_ctrl, slot, dsp)["filename"]
    goldfw_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_goldfw(mtp_mgmt_ctrl, slot, dsp)["filename"]
    rc1 = mtp_mgmt_ctrl.mtp_copy_nic_file(slot, goldfw_img_file)
    rc2 = mtp_mgmt_ctrl.mtp_copy_nic_file(slot, emmc_mainfw_img_file)
    return rc1 and rc2

@parallelize.parallel_nic_using_ssh
def swi_salina_qspi_program(mtp_mgmt_ctrl, slot, secure_img=False):
    dsp = FF_Stage.FF_SWI
    img_type="nonsecure"
    if secure_img:
        image_path = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_qspi_prog_secure_sh_img(mtp_mgmt_ctrl, slot, dsp)["filename"]
        img_type="secure"
    else:
        image_path = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_qspi_prog_sh_img(mtp_mgmt_ctrl, slot, dsp)["filename"]
        img_type="nonsecure"
    return mtp_mgmt_ctrl.matera_mtp_program_nic_qspi(slot, image_path, img_type)

@parallelize.parallel_nic_using_ssh
def swi_salina_dump_boot(mtp_mgmt_ctrl, slot):
    return mtp_mgmt_ctrl.matera_mtp_dump_nic_boot(slot)

@parallelize.parallel_nic_using_ssh
def salina_erase_qspi(mtp_mgmt_ctrl, slot):
    return mtp_mgmt_ctrl.matera_mtp_erase_nic_qspi(slot)

@parallelize.parallel_nic_using_ssh
def salina_parse_ocp_sn(mtp_mgmt_ctrl, slot):
    ret = mtp_mgmt_ctrl.mtp_parse_nic_ocp_fru(slot)
    return ret

@parallelize.parallel_nic_using_ssh
def ocp_rmii_linkup(mtp_mgmt_ctrl, slot):
    ret = mtp_mgmt_ctrl.mtp_ocp_rmii_linkup(slot)
    return ret

def ocp_connect(mtp_mgmt_ctrl, slot):
    failed_slots = list()
    for s in slot:
        if not mtp_mgmt_ctrl.mtp_ocp_connect(s):
            failed_slots.append(s)
    return failed_slots

@parallelize.parallel_nic_using_ssh
def swi_verify_board_id(mtp_mgmt_ctrl, slot):
    pn = mtp_mgmt_ctrl.get_scanned_pn(slot)
    return mtp_mgmt_ctrl.mtp_nic_assign_board_id(slot, pn, verifyOnly=True)

@parallelize.parallel_nic_using_ssh
def swi_uc_img_program(mtp_mgmt_ctrl, slot, prog_suc_only=False):
    dsp = FF_Stage.FF_SWI
    uc_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_suc_sw_img(mtp_mgmt_ctrl, slot, dsp)["filename"]
    cmd_format = MFG_DIAG_CMDS().PANAREA_SUC_SW_IMAGE_PROG
    if prog_suc_only:
        cmd_format = MFG_DIAG_CMDS().PANAREA_SUC_SW_IMAGE_SUC_PROG
    return mtp_mgmt_ctrl.mtp_nic_uc_image_program(slot, cmd_format, uc_img_file)

@parallelize.parallel_nic_using_ssh
def swi_uc_boot_check(mtp_mgmt_ctrl, slot):
    return mtp_mgmt_ctrl.mtp_nic_uc_zephyr_boot_check(slot, stage=FF_Stage.FF_SWI)

@parallelize.parallel_nic_using_ssh
def swi_vulcano_boot_check(mtp_mgmt_ctrl, slot):
    return mtp_mgmt_ctrl.mtp_nic_vulcano_boot_check(slot)

def health_status(mtp_health):
    mtp_health.monitr_mtp_health(timeout=MTP_Const.MTP_HEALTH_MONITOR_CYCLE)

def main():
    parser = argparse.ArgumentParser(description="MTP Software Install Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--skip_test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("--skip_slots", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--swm", help="SWM test mode")
    parser.add_argument("--sku", help="Supply CTO SKU, for QA/lab only...MFG should enter SKU through scanning", default=None)

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid
    if not args.skip_test:
        args.skip_test = []

    mtp_cfg_db = load_mtp_cfg(args.mtpcfg)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, sys.stdout, None, [], skip_slots=args.skip_slots)
    # local logfiles
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=FF_Stage.FF_SWI)

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)


    try:
        # read scanned barcode file except when we're skipping in dev environment
        scanned_nic_fru_cfg = dict()
        if "SCAN_VERIFY" not in args.skip_test:
            scanning.read_scanned_barcodes(mtp_mgmt_ctrl)
            scanned_nic_fru_cfg = mtp_mgmt_ctrl.barcode_scans

        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, stage=FF_Stage.FF_SWI):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            logfile_close(open_file_track_list)
            return

        if MTP_HEALTH_MONITOR:
            thread_health = threading.Thread(target=health_status, args=(mtp_mgmt_ctrl.get_mtp_health_monitor(),))
            thread_health.start()

        fail_nic_list = list()
        pass_nic_list = list()
        hmac_no_prog_slots = list()
        hmac_prog_slots = list()
        val_cert_pass_slots = list()
        val_cert_fail_slots = list()

        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        # Add failed slots from toplevel
        if args.fail_slots:
            for slot in args.fail_slots:
                fail_nic_list.append(int(slot))

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            if not nic_prsnt_list[slot]:
                continue
            if slot not in pass_nic_list:
                pass_nic_list.append(slot)

        def get_slots_of_type(nic_type, except_type=[]):
            return mtp_mgmt_ctrl.get_slots_of_type(nic_type, pass_nic_list, except_type)

        def get_slots_of_sku(sku):
            return mtp_mgmt_ctrl.get_slots_of_sku(sku, pass_nic_list)

        def run_swi_test(nic_list_orig, test, *test_args, **test_kwargs):
            stage = FF_Stage.FF_SWI
            nic_list = nic_list_orig[:]

            if test in args.skip_test:
                test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, stage, test)
                return nic_list

            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            test_utils.test_start_nic_log_message(mtp_mgmt_ctrl, nic_list, stage, test)

            if DRY_RUN:
                rlist = []

            elif test == "NIC_PWRCYC":
                rlist = mtp_mgmt_ctrl.mtp_power_cycle_nic(nic_list)

            elif test == "SCAN_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_scan_verify(nic_list)
            elif test == "FAKE_SCAN_VERIFY":
                rlist = mtp_mgmt_ctrl.fake_scan_verify(nic_list, scanned_sku=args.sku)

            elif test == "NIC_POWER":
                rlist = mtp_mgmt_ctrl.mtp_check_nic_list_pwr_status(nic_list, test)
            elif test == "NIC_TYPE":
                rlist = mtp_mgmt_ctrl.mtp_nic_type_test(nic_list)
            elif test == "NIC_PRSNT":
                rlist = mtp_mgmt_ctrl.mtp_nic_check_prsnt(nic_list)
            elif test == "NIC_INIT":
                rlist = mtp_mgmt_ctrl.mtp_check_nic_list_status(nic_list)
            elif test == "CONSOLE_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(nic_list)
            elif test == "SET_MAINFWA":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_nic_mainfwa_boot(nic_list)
            elif test == "SET_MAINFWB":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_nic_mainfwb_boot(nic_list)
            elif test == "SET_DIAGFW":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(nic_list)
            elif test == "SET_EXTDIAGFW":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_nic_extdiag_boot(nic_list)
            elif test == "SET_GOLDFW":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_nic_goldfw_boot(nic_list)
            elif test == "SET_EXTOSA":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_nic_extosa_boot(nic_list)
            elif test == "SET_EXTOSB":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_nic_extosb_boot(nic_list)
            elif test == "NIC_DIAG_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(nic_list)
            elif test == "GOLDFW_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_gold_boot(nic_list)
            elif test == "DIAG_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_diag_boot(nic_list)
            elif test == "SW_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_sw_boot(nic_list)
            elif test == "SW_A_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_sw_boot(nic_list, targetfw="mainfwa")
            elif test == "SW_B_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_sw_boot(nic_list, targetfw="mainfwb")
            elif test == "LOADED_FW_VERSION_CHECK":
                rlist = mtp_mgmt_ctrl.mtp_salina_nic_verify_loaded_fw_version(nic_list)
            elif test == "EXTDIAG_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_extdiag_boot(nic_list)
            elif test == "EXTDIAG_BOOT_SMODE":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_extdiag_smode_boot(nic_list)
            elif test == "SEC_BOOT_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_nic_secboot_verify(nic_list)
            elif test == "CFG_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_nic_cfg_verify(nic_list)

            elif test == "NIC_DIAG_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, skip_test_list=args.skip_test, **test_kwargs)
            elif test == "SW_MGMT_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_sw_mgmt_init(nic_list)

            elif test == "FRU_PROG":
                rlist = swi_fru_program(mtp_mgmt_ctrl, nic_list)
            elif test == "NIC_FRU_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_diag_init_fru_init(nic_list, False, False)
            elif test == "SKU_VALIDATE":
                rlist = mtp_mgmt_ctrl.mtp_nic_validate_sku_dpn_match(nic_list)
            elif test == "VERIFY_BOARD_ID":
                rlist = swi_verify_board_id(mtp_mgmt_ctrl, nic_list)
            elif test == "uC_SUC_IMG_PROG":
                rlist = swi_uc_img_program(mtp_mgmt_ctrl, nic_list, prog_suc_only=True)
            elif test == "uC_SW_IMG_PROG":
                rlist = swi_uc_img_program(mtp_mgmt_ctrl, nic_list)
            elif test == "uC_BOOTING_CHK":
                rlist = swi_uc_boot_check(mtp_mgmt_ctrl, nic_list)
            elif test == "VULCANO_BOOTING_CHK":
                rlist = swi_vulcano_boot_check(mtp_mgmt_ctrl, nic_list)
            elif test == "uC_VERSION_CHK":
                rlist = mtp_mgmt_ctrl.mtp_nic_suc_version_read_check(nic_list, stage=FF_Stage.FF_SWI)
            elif test == "SUC_USB_RESCAN":
                rlist =  mtp_mgmt_ctrl.mtp_uc_usb_resacn(nic_list)
            elif test == "uC_FRU_DUMP_CHK":
                rlist = mtp_mgmt_ctrl.mtp_nic_suc_fru_dump_check(nic_list)
            elif test == "VULCANO_VERSION_CHK":
                rlist = mtp_mgmt_ctrl.mtp_nic_vulcano_version_read_check(nic_list, stage=FF_Stage.FF_SWI)
            elif test == "VULCANO_FRU_DUMP_CHK":
                rlist = mtp_mgmt_ctrl.mtp_nic_vulcano_fru_dump_check(nic_list)
            elif test == "VULCANO_FPGA_UART_STATS_DUMP":
                rlist = mtp_mgmt_ctrl.mtp_vulcano_fpga_uart_stats_dump(nic_list)
            elif test == "CPLD_PROG":
                rlist = swi_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "FSAFE_CPLD_PROG":
                rlist = swi_fail_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "CPLD_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_cpld(nic_list, dl_step=False)
            elif test == "SEC_CPLD_PROG":
                rlist = swi_secure_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "UMF1_PROG":
                rlist = swi_ufm1_program(mtp_mgmt_ctrl, nic_list)
            elif test == "UMF1_CFG0_CPLD_PROG":
                rlist = dl_ufm1_cfg0_program(mtp_mgmt_ctrl, nic_list)
            elif test == "CPLD_REF":
                rlist = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(nic_list)
            elif test == "SEC_CPLD_REF":
                rlist = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(nic_list)
            elif test == "SEC_CPLD_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_cpld(nic_list, sec_cpld=True, dl_step=False)
            elif test == "COMPARE_CPLD":
                rlist = swi_cpld_compare(mtp_mgmt_ctrl, nic_list)
            elif test == "COMPARE_FAILSAFE_CPLD":
                rlist = swi_fail_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "FPGA_PROG":
                rlist = mtp_mgmt_ctrl.mtp_program_nic_fpga(nic_list)
            elif test == "FPGA_PROG_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_fpga(nic_list)
            elif test == "ERASE_MAINFW":
                rlist = mtp_mgmt_ctrl.mtp_erase_main_fw_partition(nic_list)

            elif test == "DISABLE_ESEC_WP":
                rlist = mtp_mgmt_ctrl.mtp_nic_esec_write_protect(nic_list, enable=False)
            elif test == "ENABLE_ESEC_WP":
                rlist = mtp_mgmt_ctrl.mtp_nic_esec_write_protect(nic_list, enable=True)
            elif test == "EFUSE_PROG":
                rlist = mtp_mgmt_ctrl.mtp_program_nic_efuse(nic_list)
            elif test == "SEC_KEY_PROG":
                rlist = mtp_mgmt_ctrl.mtp_program_nic_sec_key(nic_list, skip_hmac_list=hmac_prog_slots)
            elif test == "SEC_KEY_VAL_UDS":
                rlist = mtp_mgmt_ctrl.mtp_nic_val_uds_cert(nic_list)
            elif test == "SEC_PROG_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_sec_cpld(nic_list)
            elif test == "SALINA_ERASE_PCIEAWD_ENV":
                rlist = mtp_mgmt_ctrl.mtp_erase_piceawd_env_salina(nic_list)
            elif test == "OCP_FRU_SN":
                rlist = salina_parse_ocp_sn(mtp_mgmt_ctrl, nic_list)
            elif test == "OCP_RMII":
                rlist = ocp_rmii_linkup(mtp_mgmt_ctrl, nic_list)
            elif test == "OCP_CONN":
                rlist = ocp_connect(mtp_mgmt_ctrl, nic_list)

            elif test == "COPY_GOLD":
                rlist = swi_goldfw_copy(mtp_mgmt_ctrl, nic_list)
            elif test == "COPY_CERT":
                rlist = swi_cert_copy(mtp_mgmt_ctrl, nic_list)
            elif test == "SW_INSTALL":
                rlist = swi_mainfw_install(mtp_mgmt_ctrl, nic_list)
            elif test == "SALINA_GOLDFW_INSTALL":
                rlist = mtp_mgmt_ctrl.mtp_program_nic_goldfw_salina(nic_list, stage=test_kwargs["stage"])
            elif test == "SALINA_MAINFWA_INSTALL" or test == "SALINA_MAINFWB_INSTALL":
                rlist = mtp_mgmt_ctrl.mtp_program_nic_mainfw_salina(nic_list, stage=test_kwargs["stage"])
            elif test == "GOLDFW_PROG":
                rlist = swi_goldfw_program(mtp_mgmt_ctrl, nic_list)
            elif test == "SALINA_QSPI_PROG":
                rlist = swi_salina_qspi_program(mtp_mgmt_ctrl, nic_list, secure_img=test_kwargs["secure_img"])
            elif test == "SALINA_QSPI_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_power_cycle_boot_stage(nic_list, bootstage=test_kwargs["bootstage"], new_layout=False)
            elif test == "SALINA_NEW_QSPI_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_power_cycle_boot_stage(nic_list, bootstage=test_kwargs["bootstage"], new_layout=True)
            elif test == "SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_power_cycle_boot_stage(nic_list, bootstage=test_kwargs["bootstage"], new_mem_layout=True)
            elif test == "NIC_PARA_MGMT_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_test_setup_multi(nic_list)
            elif test == "NIC_BOOT_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_boot_info_init(nic_list)
            elif test == "NIC_DIAG_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, skip_test_list=args.skip_test, **test_kwargs)
            elif test == "FW_IMG_STORE2EMMC":
                rlist = swi_fw_img_store_to_emmc(mtp_mgmt_ctrl, nic_list)
            elif test == "BOARD_CONFIG_CERT":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_board_config_cert(nic_list, test_kwargs["cert_img_file"], directory="/data/")
            elif test == "SW_PROFILE":
                rlist = mtp_mgmt_ctrl.mtp_nic_sw_profile(nic_list, test_kwargs["nic_profile"])
            elif test == "SW_MODE_SWITCH":
                rlist = mtp_mgmt_ctrl.mtp_nic_sw_mode_switch(nic_list)
            elif test == "SW_MODE_SWITCH_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_nic_sw_mode_switch_verify(nic_list)
            elif test == "PDSCTL_SYSTEM":
                rlist = mtp_mgmt_ctrl.mtp_pdsctl_system_show(nic_list)
            elif test == "KEYS_CHECK":
                rlist = mtp_mgmt_ctrl.mtp_nic_read_secure_boot_keys(nic_list)
            elif test == "CONF_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_nic_device_conf_verify(nic_list)
            elif test == "SW_CLEANUP":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_nic_sw_cleanup_shutdown(nic_list)
            elif test == "SW_SHUTDOWN":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_nic_sw_shutdown(nic_list)
            elif test == "CLEAR_PRE_UBOOT_SECTION":
                rlist = mtp_mgmt_ctrl.mtp_nic_clear_pre_uboot_section(nic_list)
            elif test == "DUMP_BOOT_BIN":
                rlist = swi_salina_dump_boot(mtp_mgmt_ctrl, nic_list)
            elif test == "NIC_CTRL_INSTANCE_CPLD_PROPERTY_UPDATE":
                rlist = mtp_mgmt_ctrl.mtp_nic_diag_init_cpld_diag(nic_list, emmc_format=False)
            elif test == "ASSIGN_BOARDID_PCISUBSYSTEMID_FROM_ZEPHYR":
                rlist = mtp_mgmt_ctrl.mtp_nic_zephyr_boardid_pcisubsystemid_write(nic_list, stage=FF_Stage.FF_SWI)
            elif test == "SET_ZEPHYR_MAINFWA":
                rlist = mtp_mgmt_ctrl.mtp_nic_zephyr_debug_update_firmware(nic_list, bootfw='mainfwa')
            elif test == "SET_ZEPHYR_MAINFWB":
                rlist = mtp_mgmt_ctrl.mtp_nic_zephyr_debug_update_firmware(nic_list, bootfw='mainfwb')
            elif test == "SET_ZEPHYR_GOLDFW":
                rlist = mtp_mgmt_ctrl.mtp_nic_zephyr_debug_update_firmware(nic_list, bootfw='goldfw')
            elif test == "I2C_DUMP":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_nic_i2c_dump(nic_list)
            elif test == "ESEC_UNLOCK":
                rlist = mtp_mgmt_ctrl.mtp_nic_esecure_hw_unlock(nic_list)

            elif test == "SEC_KEY_VAL_UDS_CATE":
                rlist, rlist_val_cert_pass_slots, rlist_val_cert_fail_slots = libmfg_utils.get_val_uds_cert_category_slots(mtp_mgmt_ctrl, nic_list, stage=test_kwargs["stage"])
                for slot in rlist_val_cert_pass_slots:
                    val_cert_pass_slots.append(slot)
                for slot in rlist_val_cert_fail_slots:
                    val_cert_fail_slots.append(slot)
            elif test == "HMAC_PROG_CATE":
                rlist, rlist_hmac_no_prog_slots, rlist_hmac_prog_slots = libmfg_utils.get_hmac_category_slots(mtp_mgmt_ctrl, nic_list, stage=test_kwargs["stage"])
                for slot in rlist_hmac_no_prog_slots:
                    hmac_no_prog_slots.append(slot)
                for slot in rlist_hmac_prog_slots:
                    hmac_prog_slots.append(slot)

            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown test '{:s}'".format(test))
                rlist = nic_list

            # catch bad return value
            if not isinstance(rlist, list):
                mtp_mgmt_ctrl.cli_log_err("Test {} failed with '{}', expected slot list".format(test, repr(rlist)))
                rlist = nic_list[:]

            rlist = list(set(rlist))

            for slot in rlist:
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot, testname=test)
                # update input list, could be pass_nic_list or a subset
                if slot in nic_list_orig:
                    nic_list_orig.remove(slot)
                # update global pass/fail list
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)

            duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
            test_utils.test_fail_nic_log_message(mtp_mgmt_ctrl, rlist, stage, test, start_ts)
            test_utils.test_pass_nic_log_message(mtp_mgmt_ctrl, nic_list_orig, stage, test, start_ts)
            return rlist

        dsp = FF_Stage.FF_SWI
        if "SCAN_VERIFY" in args.skip_test:
            # only for QA, fake the scans
            run_swi_test(pass_nic_list, "FAKE_SCAN_VERIFY")
        else:
            fru_reprogram_list = run_swi_test(pass_nic_list, "SCAN_VERIFY")
        if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.MATERA:
            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "NIC_CTRL_INSTANCE_CPLD_PROPERTY_UPDATE")
            # power cycle all nic
            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "NIC_CTRL_INSTANCE_CPLD_PROPERTY_UPDATE")
            mtp_mgmt_ctrl.mtp_set_swmtestmode(Swm_Test_Mode.SW_DETECT)
            run_swi_test(pass_nic_list, "NIC_PWRCYC")
            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "ESEC_UNLOCK")
            run_swi_test(pass_nic_list, "NIC_PWRCYC")
            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "HMAC_PROG_CATE", stage=dsp)
            # run_swi_test(hmac_prog_slots, "SEC_KEY_VAL_UDS_CATE", stage=dsp)
            run_swi_test(list(set(pass_nic_list) - set(val_cert_pass_slots)), "CLEAR_PRE_UBOOT_SECTION")

            # record ocp adapter fru
            run_swi_test(get_slots_of_type(NIC_Type.LINGUA), "OCP_FRU_SN")
            run_swi_test(get_slots_of_type(NIC_Type.LINGUA), "OCP_RMII")
            run_swi_test(get_slots_of_type(NIC_Type.LINGUA), "OCP_CONN")

            # Reprogram FRU with final SKU
            sku_fru_prog_list = get_slots_of_type(CTO_MODEL_TYPE_LIST)
            # Before programming, check that scanned SKU is valid for this card
            run_swi_test(sku_fru_prog_list, "SKU_VALIDATE")
            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "FRU_PROG")

            for slot in pass_nic_list:
                swi_display_program_matrix(mtp_mgmt_ctrl, slot)

            run_swi_test(pass_nic_list, "NIC_PRSNT")
            run_swi_test(pass_nic_list, "NIC_INIT")

            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "SALINA_QSPI_PROG", secure_img=False)
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY", bootstage="linux")
            run_swi_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_NEW_QSPI_VERIFY", bootstage="zephyr")

            run_swi_test(list(set(get_slots_of_type(SALINA_NIC_TYPE_LIST)) - set(val_cert_pass_slots)), "NIC_INIT")
            run_swi_test(list(set(get_slots_of_type(SALINA_NIC_TYPE_LIST)) - set(val_cert_pass_slots)), "EFUSE_PROG")
            run_swi_test(list(set(get_slots_of_type(SALINA_NIC_TYPE_LIST)) - set(val_cert_pass_slots)), "SEC_KEY_PROG")
            run_swi_test(list(set(get_slots_of_type(SALINA_NIC_TYPE_LIST)) - set(val_cert_pass_slots)), "DUMP_BOOT_BIN")

            run_swi_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_QSPI_PROG", secure_img=False)
            run_swi_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_NEW_QSPI_VERIFY", bootstage="zephyr")

            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "NIC_CTRL_INSTANCE_CPLD_PROPERTY_UPDATE")
            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY", bootstage="zephyr")
            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "ASSIGN_BOARDID_PCISUBSYSTEMID_FROM_ZEPHYR")

            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY", bootstage="linux")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "NIC_PARA_MGMT_INIT")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "NIC_BOOT_INIT")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "FW_IMG_STORE2EMMC")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_MAINFWA_INSTALL", stage=FF_Stage.FF_SWI)
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SET_EXTOSA")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SET_MAINFWA")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "NIC_PWRCYC")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SW_A_BOOT")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_MAINFWB_INSTALL", stage=FF_Stage.FF_SWI)
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SET_EXTOSB")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SET_MAINFWB")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "NIC_PWRCYC")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SW_B_BOOT")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_GOLDFW_INSTALL", stage=FF_Stage.FF_SWI)
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SET_GOLDFW")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "NIC_PWRCYC")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "GOLDFW_BOOT")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "LOADED_FW_VERSION_CHECK")
            ### for oracle leni, ship with mainfw
            run_swi_test(get_slots_of_sku("DSC3-2Q400-64R64E64P-O"), "SET_EXTOSA")
            run_swi_test(get_slots_of_sku("DSC3-2Q400-64R64E64P-O"), "SET_MAINFWA")
            run_swi_test(get_slots_of_sku("DSC3-2Q400-64R64E64P-O"), "NIC_PWRCYC")
            run_swi_test(get_slots_of_sku("DSC3-2Q400-64R64E64P-O"), "SW_A_BOOT")
            ### for generic leni, ship with goldfw
            run_swi_test(get_slots_of_sku("DSC3-2Q400-64S64E64P"), "SET_GOLDFW")
            run_swi_test(get_slots_of_sku("DSC3-2Q400-64S64E64P"), "NIC_PWRCYC")
            run_swi_test(get_slots_of_sku("DSC3-2Q400-64S64E64P"), "GOLDFW_BOOT")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SW_CLEANUP")
            cpld_list = get_slots_of_type(SALINA_NIC_TYPE_LIST)
            run_swi_test(cpld_list, "UMF1_CFG0_CPLD_PROG")
            fsafe_cpld_type_list = get_slots_of_type(FAILSAFE_CPLD_TYPE_LIST)
            run_swi_test(fsafe_cpld_type_list, "FSAFE_CPLD_PROG")
            run_swi_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "NIC_PWRCYC")
            ### for oracle leni, ship with mainfw
            run_swi_test(get_slots_of_sku("DSC3-2Q400-64R64E64P-O"), "SW_BOOT")
            ### for generic leni, ship with goldfw
            run_swi_test(get_slots_of_sku("DSC3-2Q400-64S64E64P"), "GOLDFW_BOOT")
            run_swi_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_NEW_QSPI_VERIFY", bootstage="zephyr")
            run_swi_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SET_ZEPHYR_MAINFWB")
            run_swi_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_NEW_QSPI_VERIFY", bootstage="zephyr")
            run_swi_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SET_ZEPHYR_GOLDFW")
            run_swi_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_NEW_QSPI_VERIFY", bootstage="zephyr")
            run_swi_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SET_ZEPHYR_MAINFWA")
            run_swi_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_NEW_QSPI_VERIFY", bootstage="zephyr")

            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "SALINA_ERASE_PCIEAWD_ENV")
            run_swi_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "I2C_DUMP")
        elif mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.PANAREA:
            run_swi_test(pass_nic_list, "NIC_CTRL_INSTANCE_CPLD_PROPERTY_UPDATE")
            run_swi_test(pass_nic_list, "NIC_TYPE")
            run_swi_test(pass_nic_list, "NIC_INIT")
            run_swi_test(pass_nic_list, "FRU_PROG")
            run_swi_test(pass_nic_list, "NIC_PWRCYC")

            # Program SuC image only.
            saved_pass_nic_list = pass_nic_list[:]
            run_swi_test([slot for slot in pass_nic_list if int(slot) % 2 == 0], "uC_SUC_IMG_PROG")
            run_swi_test([slot for slot in pass_nic_list if int(slot) % 2 == 1], "uC_SUC_IMG_PROG")
            # Retry as program may fail as of USB related issue
            img_prog_fail_list = [slot for slot in saved_pass_nic_list if slot not in pass_nic_list]
            if img_prog_fail_list:
                run_swi_test(img_prog_fail_list, "NIC_PWRCYC")
                run_swi_test(img_prog_fail_list, "uC_SUC_IMG_PROG")
                for slot in img_prog_fail_list:
                    if slot not in pass_nic_list:
                        pass_nic_list.append(slot)
                    if slot in fail_nic_list:
                        fail_nic_list.remove(slot)

            run_swi_test(pass_nic_list, "NIC_PWRCYC")

            # Program Bundle image once.
            saved_pass_nic_list = pass_nic_list[:]
            run_swi_test([slot for slot in pass_nic_list if int(slot) % 2 == 0], "uC_SW_IMG_PROG")
            run_swi_test([slot for slot in pass_nic_list if int(slot) % 2 == 1], "uC_SW_IMG_PROG")
            # Retry as program may fail as of USB related issue
            img_prog_fail_list = [slot for slot in saved_pass_nic_list if slot not in pass_nic_list]
            if img_prog_fail_list:
                run_swi_test(img_prog_fail_list, "NIC_PWRCYC")
                run_swi_test(img_prog_fail_list, "uC_SW_IMG_PROG")
                for slot in img_prog_fail_list:
                    if slot not in pass_nic_list:
                        pass_nic_list.append(slot)
                    if slot in fail_nic_list:
                        fail_nic_list.remove(slot)

            # Program Bundle image twice.
            saved_pass_nic_list = pass_nic_list[:]
            run_swi_test([slot for slot in pass_nic_list if int(slot) % 2 == 0], "uC_SW_IMG_PROG")
            run_swi_test([slot for slot in pass_nic_list if int(slot) % 2 == 1], "uC_SW_IMG_PROG")
            # Retry as program may fail as of USB related issue
            img_prog_fail_list = [slot for slot in saved_pass_nic_list if slot not in pass_nic_list]
            if img_prog_fail_list:
                run_swi_test(img_prog_fail_list, "NIC_PWRCYC")
                run_swi_test(img_prog_fail_list, "uC_SW_IMG_PROG")
                for slot in img_prog_fail_list:
                    if slot not in pass_nic_list:
                        pass_nic_list.append(slot)
                    if slot in fail_nic_list:
                        fail_nic_list.remove(slot)

            run_swi_test(pass_nic_list, "uC_BOOTING_CHK")
            run_swi_test(pass_nic_list, "VULCANO_BOOTING_CHK")
            run_swi_test(pass_nic_list, "uC_VERSION_CHK")
            run_swi_test(pass_nic_list, "uC_FRU_DUMP_CHK")
            run_swi_test(pass_nic_list, "VULCANO_VERSION_CHK")
            run_swi_test(pass_nic_list, "VULCANO_FRU_DUMP_CHK")
            run_swi_test(pass_nic_list, "VULCANO_FPGA_UART_STATS_DUMP")

        else:
            # power cycle all nic
            mtp_mgmt_ctrl.mtp_set_swmtestmode(Swm_Test_Mode.SW_DETECT)
            run_swi_test(pass_nic_list, "NIC_PWRCYC")

            run_swi_test(pass_nic_list, "CONSOLE_BOOT")
            run_swi_test(pass_nic_list, "NIC_DIAG_INIT", nic_util=True)

            # for ortano-ti PN update from C0->C1, need to program C1 field in FRU
            run_swi_test(fru_reprogram_list, "FRU_PROG")
            run_swi_test(fru_reprogram_list, "NIC_FRU_INIT")

            # Reprogram FRU with final SKU
            sku_fru_prog_list = get_slots_of_type(CTO_MODEL_TYPE_LIST)
            # Before programming, check that scanned SKU is valid for this card
            run_swi_test(sku_fru_prog_list, "SKU_VALIDATE")
            run_swi_test(sku_fru_prog_list, "FRU_PROG")
            run_swi_test(sku_fru_prog_list, "NIC_FRU_INIT")
            verify_boardid_list = get_slots_of_type([NIC_Type.ORTANO2SOLOL])
            run_swi_test(verify_boardid_list, "VERIFY_BOARD_ID")

            swi_update_fru_prog_list = get_slots_of_type(SWI_UPDATE_FRU_TYPE_LIST)
            run_swi_test(swi_update_fru_prog_list, "ERASE_MAINFW")

            for slot in pass_nic_list:
                swi_display_program_matrix(mtp_mgmt_ctrl, slot)

            run_swi_test(pass_nic_list, "NIC_POWER")
            run_swi_test(pass_nic_list, "NIC_PRSNT")
            run_swi_test(pass_nic_list, "NIC_INIT")
            run_swi_test(pass_nic_list, "NIC_DIAG_BOOT")

            fpga_type_list = get_slots_of_type(FPGA_TYPE_LIST)
            run_swi_test(fpga_type_list, "FPGA_PROG")
            run_swi_test(fpga_type_list, "FPGA_PROG_VERIFY")
            cpld_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST + [NIC_Type.ORTANO2])
            run_swi_test(cpld_type_list, "CPLD_PROG")
            fsafe_cpld_type_list = get_slots_of_type(FAILSAFE_CPLD_TYPE_LIST)
            run_swi_test(fsafe_cpld_type_list, "FSAFE_CPLD_PROG")
            refresh_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST + [NIC_Type.NAPLES25OCP])
            run_swi_test(refresh_type_list, "CPLD_REF")

            non_capri_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=CAPRI_NIC_TYPE_LIST)
            run_swi_test(non_capri_type_list, "DISABLE_ESEC_WP")
            # Powercycle and also fix diag.exe as needed for elba's efuse script
            run_swi_test(pass_nic_list, "NIC_DIAG_INIT")
            efuse_type_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST)
            run_swi_test(efuse_type_list, "NIC_INIT")
            run_swi_test(efuse_type_list, "EFUSE_PROG")
            run_swi_test(pass_nic_list, "SEC_KEY_PROG")
            run_swi_test(pass_nic_list, "NIC_DIAG_INIT")
            run_swi_test(pass_nic_list, "NIC_INIT")
            sec_cpld_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST + [NIC_Type.ORTANO2, NIC_Type.ORTANO2ADIMSFT])
            run_swi_test(sec_cpld_type_list, "SEC_CPLD_PROG")
            sec_ref_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST + [NIC_Type.ORTANO2, NIC_Type.ORTANO2ADIMSFT, NIC_Type.NAPLES25OCP])
            run_swi_test(sec_ref_type_list, "SEC_CPLD_REF")
            cpld_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST) # cant power up fpga only in 3.3v
            run_swi_test(cpld_type_list, "SEC_PROG_VERIFY")
            non_capri_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=CAPRI_NIC_TYPE_LIST)
            run_swi_test(non_capri_type_list, "ENABLE_ESEC_WP")

            run_swi_test(pass_nic_list, "NIC_DIAG_INIT")

            run_swi_test(pass_nic_list, "NIC_INIT")
            run_swi_test(pass_nic_list, "SEC_CPLD_VERIFY")
            run_swi_test(pass_nic_list, "COPY_GOLD")
            adiibm_type_list = get_slots_of_type(NIC_Type.ORTANO2ADIIBM)
            run_swi_test(adiibm_type_list, "COPY_CERT")
            # program sw image onto EMMC
            mainfw_type_list = get_slots_of_type(MAINFW_TYPE_LIST)
            run_swi_test(mainfw_type_list, "SW_INSTALL")
            cpld_type_list = get_slots_of_type(FAILSAFE_CPLD_TYPE_LIST)
            run_swi_test(cpld_type_list, "COMPARE_CPLD")
            run_swi_test(cpld_type_list, "COMPARE_FAILSAFE_CPLD")
            # program goldfw package copied earlier
            run_swi_test(pass_nic_list, "GOLDFW_PROG")
            run_swi_test(pass_nic_list, "NIC_PWRCYC")
            run_swi_test(pass_nic_list, "GOLDFW_BOOT")
            # if "GOLDFW_BOOT" not in args.skip_test:
            #     run_swi_test(pass_nic_list, "NIC_PWRCYC")
            adiibm_type_list = get_slots_of_type(NIC_Type.ORTANO2ADIIBM)
            run_swi_test(adiibm_type_list, "BOARD_CONFIG_CERT", cert_img_file=MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cert_img["68-0028"])
            secure_boot_type_list = get_slots_of_type(ELBA_NIC_TYPE_LIST)
            run_swi_test(secure_boot_type_list, "SEC_BOOT_VERIFY")
            sw_cfg_type_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST)
            run_swi_test(sw_cfg_type_list, "CFG_VERIFY")
            fpga_type_list = get_slots_of_type(FPGA_TYPE_LIST)
            run_swi_test(fpga_type_list, "SET_EXTDIAGFW")
            mainfw_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST + [NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICRS4, NIC_Type.GINESTRA_S4, NIC_Type.GINESTRA_CIS])
            run_swi_test(mainfw_type_list, "SET_MAINFWA")
            run_swi_test(pass_nic_list, "SW_CLEANUP")
            run_swi_test(pass_nic_list, "NIC_PWRCYC")
            libmfg_utils.count_down(MTP_Const.NIC_SW_BOOTUP_DELAY)

            # Verify the NIC Software boot
            mainfw_boot_type_list = get_slots_of_type(MAINFW_TYPE_LIST)
            run_swi_test(mainfw_type_list, "SW_BOOT")
            netapp_type_list = get_slots_of_type(NIC_Type.NAPLES100)
            run_swi_test(netapp_type_list, "SW_MGMT_INIT")
            run_swi_test(netapp_type_list, "CONF_VERIFY")
            run_swi_test(netapp_type_list, "SW_PROFILE", nic_profile="netapp_nic_profile.py")
            adimsft_type_list = get_slots_of_type([NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICRMSFT])
            run_swi_test(adimsft_type_list, "SW_MODE_SWITCH")
            run_swi_test(adimsft_type_list, "SW_MODE_SWITCH_VERIFY")
            run_swi_test(adimsft_type_list, "SW_BOOT") # again
            monterey_type_list = get_slots_of_type(FPGA_TYPE_LIST)
            run_swi_test(monterey_type_list, "EXTDIAG_BOOT_SMODE")
            run_swi_test(monterey_type_list, "EXTDIAG_BOOT")
            run_swi_test(monterey_type_list, "KEYS_CHECK")
            fw_boot_type_list = get_slots_of_type(MAINFW_TYPE_LIST + CTO_MODEL_TYPE_LIST)
            run_swi_test(fw_boot_type_list, "SW_SHUTDOWN")

        if MTP_HEALTH_MONITOR:
            mtp_mgmt_ctrl.get_mtp_health_monitor().set_event_status()
            thread_health.join()

        # power off nic
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.cli_log_inf("MTP Software Install Test Complete", level=0)

        for slot in pass_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

        for slot in fail_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        # err_msg = str(e)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)
        if MTP_HEALTH_MONITOR and 'thread_health' in locals():
            mtp_mgmt_ctrl.get_mtp_health_monitor().set_event_status()
            thread_health.join()

    logfile_close(open_file_track_list)
    return

if __name__ == "__main__":
    main()
