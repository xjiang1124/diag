#!/usr/bin/env python

import sys
import os
import time
import pexpect
import threading
import argparse
import re
import traceback

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_ASIC_SUPPORT
from libdefs import UUT_Type
from libdefs import MTP_Const
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libdefs import NIC_Vendor
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_IMAGES
from libmfg_cfg import TOR_IMAGES
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import PSLC_MODE_TYPE_LIST
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmfg_cfg import PART_NUMBERS_MATCH
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode


def logfile_close(filep_list):
    os.system("sync")
    os.system("sync")
    for fp in filep_list:
        fp.close()
    os.system("sync")


def logfile_cleanup(file_list):
    for _file in file_list:
        os.system("rm -rf {:s}".format(_file))

def exit_fail(mtp_mgmt_ctrl, log_filep_list, err_msg=""):
    mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)
    # logfile_close(log_filep_list)
    mtp_mgmt_ctrl.mtp_console_disconnect()

def exit_pass(mtp_mgmt_ctrl, log_filep_list):
    logfile_close(log_filep_list)
    mtp_mgmt_ctrl.mtp_console_disconnect()

def load_mtp_cfg():
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    # if not GLB_CFG_MFG_TEST_MODE:
    #     mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    # mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_tor_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, telnet=False):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    if telnet:
        mtp_ts_cfg = mtp_cfg_db.get_mtp_console(mtp_id)
        if not mtp_ts_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find termserver config")
            return
    else:
        mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
        if not mtp_mgmt_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
            return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, ts_cfg=mtp_ts_cfg, apc_cfg=mtp_apc_cfg, num_of_slots=2, slots_to_skip=mtp_slots_to_skip)
    if telnet:
        mtp_mgmt_ctrl.set_uut_type(UUT_Type.TOR)
    return mtp_mgmt_ctrl

def hpe_rework_verify(mtp_mgmt_ctrl, slot):
    ### REWORK VERIFICATION FOR CAP CHANGE ###
    ### For NAPLES25(HPE) and NAPLES25SWM(HPE), Product Version/Revision Code must be 0B or 0x30 0x42 ###
    nic_fru_info = mtp_mgmt_ctrl.mtp_get_nic_fru(slot)
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_fru_info:
        nic_vendor = nic_fru_info[4]
    else:
        return False
    if nic_type == NIC_Type.NAPLES25 and nic_vendor == NIC_Vendor.HPE:
        arm_fru = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_info(MFG_DIAG_CMDS.NIC_HP_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH))
        if not arm_fru:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: command didn't work: {}".format(arm_fru))
            return False
        arm_match = re.findall("\] Revision Code +([0-9A-Za-z]*)[ \n\r]", arm_fru)
        if arm_match:
            if arm_match[0] == "0B":
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "REWORK VERIFICATION: Found Revision Code = 0B on ASIC FRU")
                ret1 = True
            else:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: Looking for Revision Code = 0B, got {}".format(arm_match[0]))
                ret1 = False
        else:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: Couldn't find Revision Code field in: \n{}".format(arm_fru))
            ret1 = False

        mtp_mgmt_ctrl._nic_ctrl_list[slot].mtp_exec_cmd(MFG_DIAG_CMDS.MTP_HP_FRU_DISP_FMT.format(slot+1))
        smb_fru = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf()
        smb_match = re.findall("\] Revision Code +([0-9A-Za-z]*)[ \n\r]", smb_fru)
        if smb_match:
            if smb_match[0] == "0B":
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "REWORK VERIFICATION: Found Revision Code = 0B on SMB FRU")
                ret2 = True
            else:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: Looking for Revision Code = 0B, got {}".format(smb_match[0]))
                ret2 = False
        else:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: Couldn't find Revision Code field in: \n{}".format(smb_fru))
            ret2 = False

    if nic_type == NIC_Type.NAPLES25SWM and nic_vendor == NIC_Vendor.HPE:
        arm_fru = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_info(MFG_DIAG_CMDS.NIC_HP_SWM_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH))
        if not arm_fru:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: command didn't work: {}".format(arm_fru))
            return False
        cloud_arm_match = re.findall(PART_NUMBERS_MATCH.N25_SWM_HPE_CLD_PN_FMT, arm_fru)
        if cloud_arm_match:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Skip rework verification for cloud card")
            return True
        arm_match = re.findall("\] Product Version +([0-9A-Za-z]*)[ \n\r]", arm_fru)
        if arm_match:
            if arm_match[0] == "0B":
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "REWORK VERIFICATION: Found Product Version = 0B on ASIC FRU")
                ret1 = True
            else:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: Looking for Product Version = 0B, got {}".format(arm_match[0]))
                ret1 = False
        else:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: Couldn't find Product Version field in: \n{}".format(arm_fru))
            ret1 = False

        mtp_mgmt_ctrl._nic_ctrl_list[slot].mtp_exec_cmd(MFG_DIAG_CMDS.MTP_HP_SWM_FRU_DISP_FMT.format(slot+1))
        smb_fru = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf()
        cloud_smb_match = re.findall(PART_NUMBERS_MATCH.N25_SWM_HPE_CLD_PN_FMT, smb_fru)
        if cloud_smb_match:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Skip rework verification for cloud card")
            return True
        smb_match = re.findall("\] Product Version +([0-9A-Za-z]*)[ \n\r]", smb_fru)
        if smb_match:
            if smb_match[0] == "0B":
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "REWORK VERIFICATION: Found Product Version = 0B on SMB FRU")
                ret2 = True
            else:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: Looking for Product Version = 0B, got {}".format(smb_match[0]))
                ret2 = False
        else:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: Couldn't find Product Version field in: \n{}".format(smb_fru))
            ret2 = False
    else:
        ret1 = True
        ret2 = True
    return ret1 and ret2

def single_nic_fw_program(mtp_mgmt_ctrl, fru_cfg, cpld_img_file, fail_cpld_img_file, qspi_img_file, qspi_gold_img_file, slot, fail_nic_list, pass_nic_list, swmtestmode, skip_testlist = []):
    sn = fru_cfg["SN"]
    mac = fru_cfg["MAC"]
    pn = fru_cfg["PN"]
    prog_date = str(fru_cfg["TS"])
    test_list = ["FRU_PROG", "QSPI_PROG", "CPLD_PROG", "CPLD_REF"]
    
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.NAPLES25OCP:
        test_list = ["FRU_PROG", "QSPI_PROG", "CPLD_PROG"]
    if (nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM):  #If SWM and only asking for ALOM, skip SWM FRU PROGRAMMING
        test_list = ["FRU_PROG"]

    if nic_type == NIC_Type.ORTANO2:
        test_list = ["FIX_VRM", "VDD_DDR_FIX", "FRU_PROG", "QSPI_PROG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    if nic_type == NIC_Type.ORTANO2ADI:
        test_list = ["FRU_PROG", "QSPI_GOLD_PROG", "QSPI_PROG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    if nic_type in FPGA_TYPE_LIST:
        test_list = ["FRU_PROG", "QSPI_PROG", "FPGA_PROG", "FPGA_GOLD_PROG"]
    dsp = FF_Stage.FF_DL

    for skipped_test in skip_testlist:
        if skipped_test in test_list:
            test_list.remove(skipped_test)
    for test in test_list:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        # program FRU
        if test == "FRU_PROG":
            if not (nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM):  #If SWM and only asking for ALOM, skip SWM FRU PROGRAMMING
                ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn)
            if pn == '000000-000':
                alom_sn = fru_cfg["SN_ALOM"]
                alom_pn = fru_cfg["PN_ALOM"] 
                ret = mtp_mgmt_ctrl.mtp_program_nic_alom_fru(slot, prog_date, alom_sn, alom_pn)
                #ret = False
        # read old FRU via hexdump
        elif test == "FRU_DUMP":
            ret = mtp_mgmt_ctrl.mtp_dump_nic_fru(slot, expect_mac=mac, expect_pn=pn)
        # program CPLD
        elif test == "CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
        elif test == "FPGA_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
        # program failsafe CPLD
        elif test == "FSAFE_CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_failsafe_cpld(slot, fail_cpld_img_file)
        elif test == "FPGA_GOLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_failsafe_cpld(slot, fail_cpld_img_file)
        # program feature row
        elif test == "FEA_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld_feature_row(slot, "/home/diag/"+NIC_IMAGES.fea_cpld_img["ORTANO2"]) # just for temporary lab use
        # program QSPI
        elif test == "QSPI_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_qspi(slot, qspi_img_file)
        # program GOLD QSPI
        elif test == "QSPI_GOLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_qspi(slot, qspi_gold_img_file, True)
        # refresh CPLD
        elif test == "CPLD_REF":
            ret = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(slot)
        # check booted from correct CPLD partition
        elif test == "BOOT_CHECK":
            ret = mtp_mgmt_ctrl.mtp_check_nic_cpld_partition(slot)
        elif test == "FIX_VRM":
            ret = mtp_mgmt_ctrl.mtp_nic_fix_vrm(slot)
        elif test == "VDD_DDR_FIX":
            ret = mtp_mgmt_ctrl.mtp_nic_vdd_ddr_fix(slot)
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)
            mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, dsp, test, duration))

def set_pslc(mtp_mgmt_ctrl,nic_fru_cfg,mtp_id,fail_nic_list):
    dsp = FF_Stage.FF_DL

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue    #NEXT
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if not (card_type == NIC_Type.VOMERO2 or card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2):
            continue
        sn = nic_fru_cfg[mtp_id][key]["SN"]
        mac = nic_fru_cfg[mtp_id][key]["MAC"]
        pn = nic_fru_cfg[mtp_id][key]["PN"]
        prog_date = str(nic_fru_cfg[mtp_id][key]["TS"])
      
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, 'SET_PSLC'))
        start_ts = libmfg_utils.timestamp_snapshot()        
        ret = mtp_mgmt_ctrl.mtp_setting_partition(slot)
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, 'SET_PSLC', "FAILED", duration))
            fail_nic_list.append(slot)
        else:
            mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, 'SET_PSLC', duration))
    mtp_mgmt_ctrl.mtp_power_on_nic()
    return len(fail_nic_list)

def single_uut_fw_program(stage,
                          fru_cfg, 
                          fail_uut_list, pass_uut_list, 
                          log_file_list, 
                          verbosity, 
                          skip_testlist = []):
    dsp = stage #FF_Stage.FF_DL
    uut_id = fru_cfg["ID"]
    sn = fru_cfg["SN"]
    mac = fru_cfg["MAC"]
    pn = fru_cfg["PN"]
    prog_date = str(fru_cfg["TS"])

    # Prepare local log files
    log_filep_list = list()
    log_dir = "log/"
    log_timestamp = libmfg_utils.get_timestamp()
    log_sub_dir = MTP_DIAG_Logfile.MFG_STAGE_LOG_DIR.format(stage, uut_id, log_timestamp)
    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir + log_sub_dir))
    test_log_file = log_dir + log_sub_dir + "mtp_test.log"
    log_file_list.append(test_log_file)
    test_log_filep = open(test_log_file, "w+", buffering=0)
    log_filep_list.append(test_log_filep)

    if verbosity:
        diag_log_filep = sys.stdout
    else:
        diag_log_file = log_dir + log_sub_dir + "mtp_diag.log"
        log_file_list.append(diag_log_file)
        diag_log_filep = open(diag_log_file, "w+", buffering=0)
        log_filep_list.append(diag_log_filep)

    diag_nic_log_filep_list = list()
    for slot in range(0,2):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = log_dir + log_sub_dir + "mtp_{:s}_diag.log".format(key)
        log_file_list.append(diag_nic_log_file)
        diag_nic_log_filep = open(diag_nic_log_file, "w+", buffering=0)
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    # Begin test
    mtp_cfg_db = load_mtp_cfg()
    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, uut_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, telnet=True)

    # hardcode all these for now
    card_type = NIC_Type.TAORMINA
    uut_type = UUT_Type.TOR
    asic_type = MTP_ASIC_SUPPORT.ELBA
    x86_image = MTP_IMAGES.AMD64_IMG[asic_type]
    arm_image = MTP_IMAGES.ARM64_IMG[asic_type]
    mtp_mgmt_ctrl.set_homedir(MTP_DIAG_Path.ONBOARD_TOR_DIAG_PATH)
    mtp_mgmt_ctrl._slots = 2
    
    qspi_fa_img_file = TOR_IMAGES.first_article_img[uut_type]
    os_test_img_file = TOR_IMAGES.os_test_img[uut_type]
    os_test_exp_version = TOR_IMAGES.os_test_dat[uut_type]
    os_ship_img_file = TOR_IMAGES.os_ship_img[uut_type]
    os_ship_exp_version = TOR_IMAGES.os_ship_dat[uut_type]
    tpm_img = TOR_IMAGES.tpm_img[uut_type]
    svos_util_img_file = TOR_IMAGES.svos_fpga_image[uut_type]
    usb_img = TOR_IMAGES.usb_img[uut_type]

    fpga_img_file = TOR_IMAGES.fpga_img[uut_type]
    test_fpga_img_file = TOR_IMAGES.test_fpga_img[uut_type]
    gpio_cpld_img_file = TOR_IMAGES.gpio_cpld_test_img[uut_type]
    cpu_cpld_img_file = TOR_IMAGES.cpu_cpld_test_img[uut_type]
    cpld_img_file = NIC_IMAGES.cpld_img[card_type]
    fail_cpld_img_file = NIC_IMAGES.fail_cpld_img[card_type]
    fea_cpld_img_file = NIC_IMAGES.fea_cpld_img[card_type]

    try:
        if not mtp_mgmt_ctrl.tor_boot_select(0):
            mtp_mgmt_ctrl.cli_log_err("Unable to connect UUT Chassis", level=0)
            exit_fail(mtp_mgmt_ctrl, log_filep_list)
            if not fru_cfg["SN"]:
                fru_cfg["SN"] = "UNKNOWN"
            mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, "SVOS_BOOT", "FAILED", "0:00:00"), level=0)
            fail_uut_list.append(uut_id)
            mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
            mtp_mgmt_ctrl.mtp_apc_pwr_off()
            libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
            return

        if not libmfg_utils.mtp_clear_console(mtp_mgmt_ctrl):
            exit_fail(mtp_mgmt_ctrl, log_filep_list)

        if not mtp_mgmt_ctrl.mtp_console_connect():
            mtp_mgmt_ctrl.cli_log_err("Unable to connect UUT Chassis", level=0)
            exit_fail(mtp_mgmt_ctrl, log_filep_list)
            if uut_id not in fail_uut_list:
                fail_uut_list.append(uut_id)
            if uut_id in pass_uut_list:
                pass_uut_list.remove(uut_id)
            return
        mtp_mgmt_ctrl.cli_log_inf("UUT Chassis is connected", level=0)

        if stage == "LED":
            # read FRU
            mtp_mgmt_ctrl.tor_fru_init()
            sn = mtp_mgmt_ctrl._sn
            fru_cfg["SN"] = sn

        if uut_id not in pass_uut_list:
            pass_uut_list.append(uut_id)

        mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Started", level=0)
        mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

        ### X86 HOST TESTS
        if stage == "LED":
            testlist = [
                        "MGMT_INIT",
                        "DOWNLOAD_USB_LED_TOOL",
                        "TEST_LED_GREEN",
                        "TEST_LED_ORANGE"
                        #"I210_NIC_PROG",
                        #"SVOS_BOOT",
                        #"I210_MAC_PROG",
                        #"FRU_PROG",
                        #"FRU_TPM_SN_PROG",
                        #"FRU_VERIFY"
                        ]

        for skipped_test in skip_testlist:
            if skipped_test in testlist:
                testlist.remove(skipped_test)
        for test in testlist:
            mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = mtp_mgmt_ctrl.log_test_start(test)

            if test.startswith("PWRCYC"):
                ret = mtp_mgmt_ctrl.uut_powercycle()


            elif test == "USB_BOOT":
                ret = mtp_mgmt_ctrl.tor_usb_boot()
            elif test.startswith("SVOS_BOOT"):
                ret = mtp_mgmt_ctrl.tor_boot_select(0)
            elif test.startswith("OS_BOOT"):
                ret = mtp_mgmt_ctrl.tor_boot_select(1)
            elif test.startswith("BIOS_BOOT"):
                ret = mtp_mgmt_ctrl.tor_boot_bios()


            elif test == "MGMT_INIT":
                ret = mtp_mgmt_ctrl.tor_mgmt_init()
            elif test == "MGMT_INIT_OS":
                ret = mtp_mgmt_ctrl.tor_mgmt_init(False)

            elif test == "DOWNLOAD_USB_LED_TOOL":
                ret = mtp_mgmt_ctrl.tor_svos_led_usb_setup(usb_img)
            elif test == "TEST_LED_GREEN":
                ret = mtp_mgmt_ctrl.tor_led_test('green')
            elif test == "TEST_LED_ORANGE":
                ret = mtp_mgmt_ctrl.tor_led_test('orange')

            elif test == "SSD_FORMAT":
                ret = mtp_mgmt_ctrl.tor_ssd_format()
            elif test == "QSPI_FLASH":
                ret = mtp_mgmt_ctrl.tor_nic_qspi_flash(qspi_fa_img_file)
            elif test == "SETUP_ELBA_UBOOT_ENV":
                ret = mtp_mgmt_ctrl.tor_nic_Setup_Elba_uboot_env()
            elif test == "SETUP_ELBA_DEVICE_CONFIG":
                ret = mtp_mgmt_ctrl.tor_nic_Setup_device_config()
            elif test == "SET_PSLC_CONNECTION":
                ret = mtp_mgmt_ctrl.mtp_nic_connection_init()
            elif test == "SET_PSLC":
                ret = mtp_mgmt_ctrl.mtp_setting_partition(0)
                ret &= mtp_mgmt_ctrl.mtp_setting_partition(1)


            elif test == "I210_NIC_PROG":
                ret = mtp_mgmt_ctrl.i210_nic_prog()
            elif test == "I210_MAC_PROG":
                ret = mtp_mgmt_ctrl.i210_mac_prog(fru_cfg)


            elif test == "FRU_PROG":
                ret = mtp_mgmt_ctrl.tor_fru_prog(sn, mac, pn, prog_date)
            elif test == "FRU_TPM_SN_PROG":
                ret = mtp_mgmt_ctrl.tor_fru_prog_tpm_pcbasn(pcbasn)
            elif test == "FRU_VERIFY":
                ret = mtp_mgmt_ctrl.tor_fru_verify()


            elif test == "GPIO_CPLD_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("gpio", gpio_cpld_img_file)
            elif test == "ELBA_CPLD_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("elba 0", cpld_img_file)
                ret &= mtp_mgmt_ctrl.tor_cpld_prog("elba 1", cpld_img_file)
            elif test == "ELBA_FEA_PROG":
                ret = mtp_mgmt_ctrl.tor_fea_cpld_prog("elba 0", fea_cpld_img_file)
                ret &= mtp_mgmt_ctrl.tor_fea_cpld_prog("elba 1", fea_cpld_img_file)
            elif test == "CPU_CPLD_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("cpu", cpu_cpld_img_file)
            elif test == "FPGA_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("fpga", fpga_img_file)
            elif test == "TEST_FPGA_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("fpgatest", test_fpga_img_file)
            elif test == "CPLD_REF":
                ret = mtp_mgmt_ctrl.tor_cpld_ref()
            elif test == "CPLD_VERIFY":
                ret = mtp_mgmt_ctrl.tor_cpld_verify()


            elif test == "TPM_CONFIG_IMAGE":
                ret = mtp_mgmt_ctrl.tor_svos_bio_tpm_config_image_setup(tpm_img)
            elif test == "BIOS_CONFIG_TPM":
                ret = mtp_mgmt_ctrl.tor_bios_config_tpm()


            elif test == "TD_AVS_SET":
                ret = mtp_mgmt_ctrl.tor_td_avs_set()
            elif test == "TD_GEARBOX_VERIFY":
                ret = mtp_mgmt_ctrl.tor_td_gearbox_verify()


            elif test == "BIOS_VERIFY":
                ret = mtp_mgmt_ctrl.tor_bios_verify()

            elif test == "SVOS_PROG_UTIL":
                ret = mtp_mgmt_ctrl.tor_util_prog(svos_util_img_file)

            elif test == "OS_PROG_TEST":
                ret = mtp_mgmt_ctrl.tor_os_prog(os_test_img_file)
            elif test == "OS_PROG_SHIP":
                ret = mtp_mgmt_ctrl.tor_os_prog(os_ship_img_file)
            elif test == "OS_UPDATE":
                ret = mtp_mgmt_ctrl.tor_mgmt_os_prog(os_ship_img_file)
            elif test == "OS_TEST_VERIFY":
                #ret = mtp_mgmt_ctrl.tor_os_verify(os_ship_exp_version)
                ret = mtp_mgmt_ctrl.tor_os_verify(os_test_exp_version)
            elif test == "OS_VERIFY":
                ret = mtp_mgmt_ctrl.tor_os_verify(os_ship_exp_version)
                #ret = mtp_mgmt_ctrl.tor_os_verify(os_test_exp_version)


            elif test == "BOARD_ID":
                ret = mtp_mgmt_ctrl.tor_board_id()
            elif test == "DIAG_INIT":
                ret = mtp_mgmt_ctrl.tor_diag_init(FF_Stage.FF_DL, fpo=True)
            elif test == "DIAG_INIT2":
                ret = mtp_mgmt_ctrl.tor_diag_init(FF_Stage.FF_DL, fpo=False)

            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                if uut_id not in fail_uut_list:
                    fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)
                break
            else:
                mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

        mtp_mgmt_ctrl.cli_log_inf("Host tests completed\n", level=0)

        #sys.exit()

        if stage == "DL2" and uut_id not in fail_uut_list:
            mtp_mgmt_ctrl.cli_log_inf("Begin ARM tests", level=0)

            # FRU program prep
            for slot in range(mtp_mgmt_ctrl._slots):
                key = libmfg_utils.nic_key(slot)
                fru_cfg[key] = dict()
                fru_cfg[key]["SN"] = mtp_mgmt_ctrl.get_mtp_sn()
                fru_cfg[key]["PN"] = mtp_mgmt_ctrl.get_mtp_pn()
                fru_cfg[key]["MAC"] = mtp_mgmt_ctrl.get_mtp_mac()
                fru_cfg[key]["TS"] = libmfg_utils.get_fru_date()
                fru_cfg[key]["VALID"] = "YES"

            time.sleep(5)
            # Bring up PCIe links
            if not mtp_mgmt_ctrl.tor_nic_gold_boot():
                mtp_mgmt_ctrl.cli_log_err("Failed to set NIC goldfw", level=0)
                fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)

            # Powercycle including rescan
            if not mtp_mgmt_ctrl.mtp_power_cycle_nic():
                if uut_id not in fail_uut_list:
                    fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)

            # Validate previous step
            for slot in range(mtp_mgmt_ctrl._slots):
                if not mtp_mgmt_ctrl.mtp_mgmt_verify_nic_gold_boot(slot):
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Failed to boot into goldfw")
                    if uut_id not in fail_uut_list:
                        fail_uut_list.append(uut_id)
                    if uut_id in pass_uut_list:
                        pass_uut_list.remove(uut_id)

            # Init ARM Diag Environment
            if not mtp_mgmt_ctrl.mtp_nic_diag_init(emmc_format=True, fru_valid=False, sn_tag=True, fru_cfg=fru_cfg):
                mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
                fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)

        if stage == "DL2" and uut_id not in fail_uut_list:

            for slot in range(mtp_mgmt_ctrl._slots):
                key = libmfg_utils.nic_key(slot)
                sn = fru_cfg[key]["SN"]
                pn = fru_cfg[key]["PN"]
                mac = fru_cfg[key]["MAC"]
                prog_date = fru_cfg[key]["TS"]

                testlist = ["NIC_FRU_PROG"]
                for skipped_test in skip_testlist:
                    if skipped_test in testlist:
                        testlist.remove(skipped_test)
                for test in testlist:
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                    if test == "NIC_FRU_PROG":
                        ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn)
                    else:
                        mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
                        if uut_id not in fail_uut_list:
                            fail_uut_list.append(uut_id)
                        if uut_id in pass_uut_list:
                            pass_uut_list.remove(uut_id)
                        break
                    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                    if not ret:
                        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                        if uut_id not in fail_uut_list:
                            fail_uut_list.append(uut_id)
                        if uut_id in pass_uut_list:
                            pass_uut_list.remove(uut_id)
                        break
                    else:
                        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        if stage == "DL2" and uut_id not in fail_uut_list:
            testlist = [
                        "SETUP_ELBA_UBOOT_ENV2"
                        ]
            for skipped_test in skip_testlist:
                if skipped_test in testlist:
                    testlist.remove(skipped_test)
            for test in testlist:
                mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
                start_ts = mtp_mgmt_ctrl.log_test_start(test)

                if test == "SETUP_ELBA_UBOOT_ENV2":
                    ret = mtp_mgmt_ctrl.tor_nic_Setup_Elba_uboot_env(initemmc=False)

                else:
                    mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
                    continue
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                    if uut_id not in fail_uut_list:
                        fail_uut_list.append(uut_id)
                    if uut_id in pass_uut_list:
                        pass_uut_list.remove(uut_id)
                    break
                else:
                    mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)
        if (stage == "DL2") and uut_id not in fail_uut_list:

            # Taormina P1 hack: elba0 might be hung after CPLD refresh
            #if not mtp_mgmt_ctrl.uut_powercycle():
            #if not mtp_mgmt_ctrl.tor_boot_select(0):
                #mtp_mgmt_ctrl.tor_boot_select(0)
            # if not mtp_mgmt_ctrl.tor_boot_select(1):
            #     mtp_mgmt_ctrl.cli_log_err("PWRCYC3 failed", level=0)
            #     if uut_id not in fail_uut_list:
            #         fail_uut_list.append(uut_id)
            #     if uut_id in pass_uut_list:
            #         pass_uut_list.remove(uut_id)

            # if not mtp_mgmt_ctrl.tor_mgmt_init(False):
            #     mtp_mgmt_ctrl.cli_log_err("MGMT_INIT_OS2 failed", level=0)
            #     if uut_id not in fail_uut_list:
            #         fail_uut_list.append(uut_id)
            #     if uut_id in pass_uut_list:
            #         pass_uut_list.remove(uut_id)

            # # Initialize ssh connections again
            # if not mtp_mgmt_ctrl.tor_diag_init(x86_image, arm_image, FF_Stage.FF_DL, fpo=False):
            #     mtp_mgmt_ctrl.cli_log_err("DIAG_INIT3 failed", level=0)
            #     if uut_id not in fail_uut_list:
            #         fail_uut_list.append(uut_id)
            #     if uut_id in pass_uut_list:
            #         pass_uut_list.remove(uut_id)

            # do the goldfw-memtun dance again..
            time.sleep(5)
            # Bring up PCIe links
            if not mtp_mgmt_ctrl.tor_nic_gold_boot():
                mtp_mgmt_ctrl.cli_log_err("Failed to set NIC goldfw", level=0)
                fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)

            # Powercycle including rescan
            if not mtp_mgmt_ctrl.mtp_power_cycle_nic():
                if uut_id not in fail_uut_list:
                    fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)

            # Validate previous step
            for slot in range(mtp_mgmt_ctrl._slots):
                if not mtp_mgmt_ctrl.mtp_mgmt_verify_nic_gold_boot(slot):
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Failed to boot into goldfw")
                    if uut_id not in fail_uut_list:
                        fail_uut_list.append(uut_id)
                    if uut_id in pass_uut_list:
                        pass_uut_list.remove(uut_id)

            # Finally, memtun
            if not mtp_mgmt_ctrl.mtp_nic_diag_init():
                mtp_mgmt_ctrl.cli_log_err("Initialized NIC Diag Environment failed", level=0)
                fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)

        if stage == "DL2" and uut_id not in fail_uut_list:
            for slot in range(mtp_mgmt_ctrl._slots):
                key = libmfg_utils.nic_key(slot)
                sn = fru_cfg[key]["SN"]
                pn = fru_cfg[key]["PN"]
                mac = fru_cfg[key]["MAC"]
                prog_date = fru_cfg[key]["TS"]

                testlist = ["NIC_FRU_VERIFY",
                            "AVS_SET"]
                for skipped_test in skip_testlist:
                    if skipped_test in testlist:
                        testlist.remove(skipped_test)
                for test in testlist:
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                    if test == "NIC_FRU_VERIFY":
                        ret = mtp_mgmt_ctrl.mtp_verify_nic_fru(slot, sn, mac, pn, prog_date)
                    elif test == "AVS_SET":
                        ret = mtp_mgmt_ctrl.tor_nic_avs_set(slot)
                    else:
                        mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
                        if uut_id not in fail_uut_list:
                            fail_uut_list.append(uut_id)
                        if uut_id in pass_uut_list:
                            pass_uut_list.remove(uut_id)
                        break
                    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                    if not ret:
                        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                        if uut_id not in fail_uut_list:
                            fail_uut_list.append(uut_id)
                        if uut_id in pass_uut_list:
                            pass_uut_list.remove(uut_id)
                        break
                    else:
                        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        if stage == "DL2" and uut_id not in fail_uut_list:
            testlist = [
                        #"SVOS_BOOT",
                        #"MGMT_INIT",
                        #"FPGA_PROG",
                        #"BOARD_ID",
                        #"OS_PROG_SHIP",
                        #"SVOS_BOOT",
                        #"MGMT_INIT",
                        #"BOARD_ID",
                        #"OS_BOOT",
                        #"MGMT_INIT_OS",
                        #"OS_VERIFY"
                        ]
            for skipped_test in skip_testlist:
                if skipped_test in testlist:
                    testlist.remove(skipped_test)
            for test in testlist:
                mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
                start_ts = mtp_mgmt_ctrl.log_test_start(test)

                if test.startswith("PWRCYC"):
                    ret = mtp_mgmt_ctrl.uut_powercycle()


                elif test == "USB_BOOT":
                    ret = mtp_mgmt_ctrl.tor_usb_boot()
                elif test.startswith("SVOS_BOOT"):
                    ret = mtp_mgmt_ctrl.tor_boot_select(0)
                elif test.startswith("OS_BOOT"):
                    ret = mtp_mgmt_ctrl.tor_boot_select(1)
                elif test.startswith("BIOS_BOOT"):
                    ret = mtp_mgmt_ctrl.tor_boot_bios()


                elif test == "MGMT_INIT":
                    ret = mtp_mgmt_ctrl.tor_mgmt_init()
                elif test == "MGMT_INIT_OS":
                    ret = mtp_mgmt_ctrl.tor_mgmt_init(False)


                elif test == "SSD_FORMAT":
                    ret = mtp_mgmt_ctrl.tor_ssd_format()
                elif test == "QSPI_FLASH":
                    ret = mtp_mgmt_ctrl.tor_nic_qspi_flash(qspi_fa_img_file)
                elif test == "SETUP_ELBA_UBOOT_ENV":
                    ret = mtp_mgmt_ctrl.tor_nic_Setup_Elba_uboot_env()
                elif test == "SET_PSLC":
                    ret = mtp_mgmt_ctrl.mtp_setting_partition(0)
                    ret &= mtp_mgmt_ctrl.mtp_setting_partition(1)


                elif test == "I210_NIC_PROG":
                    ret = mtp_mgmt_ctrl.i210_nic_prog()
                elif test == "I210_MAC_PROG":
                    ret = mtp_mgmt_ctrl.i210_mac_prog(fru_cfg)


                elif test == "FRU_PROG":
                    ret = mtp_mgmt_ctrl.tor_fru_prog(sn, mac, pn, prog_date)
                elif test == "FRU_TPM_SN_PROG":
                    ret = mtp_mgmt_ctrl.tor_fru_prog_tpm_pcbasn(pcbasn)
                elif test == "FRU_VERIFY":
                    ret = mtp_mgmt_ctrl.tor_fru_verify()


                elif test == "GPIO_CPLD_PROG":
                    ret = mtp_mgmt_ctrl.tor_cpld_prog("gpio", gpio_cpld_img_file)
                elif test == "ELBA_CPLD_PROG":
                    ret = mtp_mgmt_ctrl.tor_cpld_prog("elba 0", cpld_img_file)
                    ret &= mtp_mgmt_ctrl.tor_cpld_prog("elba 1", cpld_img_file)
                elif test == "ELBA_FEA_PROG":
                    ret = mtp_mgmt_ctrl.tor_fea_cpld_prog("elba 0", fea_cpld_img_file)
                    ret &= mtp_mgmt_ctrl.tor_fea_cpld_prog("elba 1", fea_cpld_img_file)
                elif test == "CPU_CPLD_PROG":
                    ret = mtp_mgmt_ctrl.tor_cpld_prog("cpu", cpu_cpld_img_file)
                elif test == "FPGA_PROG":
                    ret = mtp_mgmt_ctrl.tor_cpld_prog("fpga", fpga_img_file)
                elif test == "TEST_FPGA_PROG":
                    ret = mtp_mgmt_ctrl.tor_cpld_prog("fpgatest", test_fpga_img_file)
                elif test == "CPLD_REF":
                    ret = mtp_mgmt_ctrl.tor_cpld_ref()
                elif test == "CPLD_VERIFY":
                    ret = mtp_mgmt_ctrl.tor_cpld_verify()


                elif test == "TPM_CONFIG_IMAGE":
                    ret = mtp_mgmt_ctrl.tor_svos_bio_tpm_config_image_setup(tpm_img)
                elif test == "BIOS_CONFIG_TPM":
                    ret = mtp_mgmt_ctrl.tor_bios_config_tpm()


                elif test == "TD_AVS_SET":
                    ret = mtp_mgmt_ctrl.tor_td_avs_set()
                elif test == "TD_GEARBOX_VERIFY":
                    ret = mtp_mgmt_ctrl.tor_td_gearbox_verify()


                elif test == "BIOS_VERIFY":
                    ret = mtp_mgmt_ctrl.tor_bios_verify()

                elif test == "OS_PROG_TEST":
                    ret = mtp_mgmt_ctrl.tor_os_prog(os_test_img_file)
                elif test == "OS_PROG_SHIP":
                    ret = mtp_mgmt_ctrl.tor_os_prog(os_ship_img_file)
                elif test == "OS_UPDATE":
                    ret = mtp_mgmt_ctrl.tor_mgmt_os_prog(os_ship_img_file)
                elif test == "OS_TEST_VERIFY":
                    #ret = mtp_mgmt_ctrl.tor_os_verify(os_ship_exp_version)
                    ret = mtp_mgmt_ctrl.tor_os_verify(os_test_exp_version)
                elif test == "OS_VERIFY":
                    ret = mtp_mgmt_ctrl.tor_os_verify(os_ship_exp_version)
                    #ret = mtp_mgmt_ctrl.tor_os_verify(os_test_exp_version)

                elif test == "BOARD_ID":
                    ret = mtp_mgmt_ctrl.tor_board_id()
                elif test == "DIAG_INIT":
                    ret = mtp_mgmt_ctrl.tor_diag_init(FF_Stage.FF_DL, fpo=True)
                elif test == "DIAG_INIT2":
                    ret = mtp_mgmt_ctrl.tor_diag_init(FF_Stage.FF_DL, fpo=False)

                else:
                    mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
                    continue
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                    if uut_id not in fail_uut_list:
                        fail_uut_list.append(uut_id)
                    if uut_id in pass_uut_list:
                        pass_uut_list.remove(uut_id)
                    break
                else:
                    mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

        mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Complete", level=0)
        # shut down system
        #if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.uut_chassis_shutdown()

        mfg_dl_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG DL Test Duration:{:s}".format(mfg_dl_stop_ts - mfg_dl_start_ts))

        if uut_id in pass_uut_list:
            if stage == "DL2":
                sn = mtp_mgmt_ctrl.get_mtp_sn()
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(uut_id, card_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

        if uut_id in fail_uut_list:
            # if stage == "DL2":
            #     sn = mtp_mgmt_ctrl.get_mtp_sn()
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(uut_id, card_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    except Exception as e:
        if uut_id not in fail_uut_list:
            fail_uut_list.append(uut_id)
        if uut_id in pass_uut_list:
            pass_uut_list.remove(uut_id)
        exit_fail(mtp_mgmt_ctrl, log_filep_list, traceback.print_exc())

def main():
    parser = argparse.ArgumentParser(description="MFG LED Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--LED", "-LED", "--led", "-led", "-1", help="station to LED test", action="store_true")
    parser.add_argument("--mtpid", "--mtp-id", "--uut-id", "--uutid", help="pre-select UUTs", nargs="*", default=[])

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    if args.LED:
        stage = "LED"
    else:
        stage = "DL2"

    TAORMINA_TEST = True
    if TAORMINA_TEST: 

        ######################################
        mtp_cfg_db = load_mtp_cfg()

        pass_rslt_list = list()
        fail_rslt_list = list()
        log_dir = "log/"
        os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir))

        if stage == "LED":
            uut_id_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
            fru_cfg = dict()
            for uut_id in uut_id_list:
                fru_cfg[uut_id] = dict()
                fru_cfg[uut_id]["ID"] = uut_id
                fru_cfg[uut_id]["VALID"] = True
                fru_cfg[uut_id]["SN"] = None
                fru_cfg[uut_id]["MAC"] = None
                fru_cfg[uut_id]["PN"] = None
                fru_cfg[uut_id]["TS"] = None

        ######################################

        pass_uut_list = list()
        fail_uut_list = list()

        uut_thread_list = list()
        logfile_dict = dict()


        if stage == "LED":
            # sequential
            for uut in fru_cfg.keys():
                if uut in fail_uut_list:
                    continue
                if not fru_cfg[uut]["VALID"]:
                    continue

                logfile_dict[uut] = list()
                single_uut_fw_program                                                (stage,
                                                                                      fru_cfg[uut], 
                                                                                      fail_uut_list,
                                                                                      pass_uut_list,
                                                                                      logfile_dict[uut],
                                                                                      verbosity,
                                                                                      args.skip_test)


        # Package each UUT's logfile
        for uut_id in logfile_dict.keys():
            logfile_list = logfile_dict[uut_id]

            log_sub_dir = os.path.basename(os.path.dirname(logfile_list[0])) # aka MFG_STAGE_LOG_DIR

            # extract log timestamp from one of the filenames
            if logfile_list:
                timestamp_length = 19
                log_timestamp = log_sub_dir[-19:]
            else:
                log_timestamp = libmfg_utils.get_timestamp()

            # pkg the logfile
            # MFG_DL_LOG_PKG_FILE = "DL_{:s}_{:s}.tar.gz"
            # MFG_DL_LOG_DIR = "DL_{:s}_{:s}/"
            # MFG_LOG_PKG_FMT = "tar czf {:s} -C {:s} {:s}"
            log_pkg_file = MTP_DIAG_Logfile.MFG_STAGE_LOG_PKG_FILE.format(stage, uut_id, log_timestamp)
            os.system(MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format(log_dir+log_pkg_file, log_dir, log_sub_dir))

            # move the logs to the log root dir
            for slot in fail_uut_list + pass_uut_list:
                sn = fru_cfg[uut_id]["SN"]
                nic_type = NIC_Type.TAORMINA
                if not sn:
                    continue
                if GLB_CFG_MFG_TEST_MODE:
                    mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_DL_LOG_DIR_FMT.format(nic_type, sn)
                else:
                    mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_DL_LOG_DIR_FMT.format(nic_type, sn)
                os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir))
                libmfg_utils.cli_inf("[{:s}] Collecting log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
                os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))

            # if GLB_CFG_MFG_TEST_MODE:
            #     libmfg_utils.mfg_report(uut_id, mfg_dl_start_ts, mfg_dl_stop_ts, test_log_file, FF_Stage.FF_DL)

            # cleanup the log dir
            logfile_cleanup([log_dir+log_sub_dir, log_dir+log_pkg_file])

        ######## TEST SUMMARY ########
        test_summary_dict = dict()
        for uut_id in pass_uut_list:
            sn = fru_cfg[uut_id]["SN"]
            card_type = NIC_Type.TAORMINA
            test_summary_dict[uut_id] = [(uut_id, sn, card_type, True)]
        
        for uut_id in fail_uut_list:
            sn = fru_cfg[uut_id]["SN"]
            card_type = NIC_Type.TAORMINA
            test_summary_dict[uut_id] = [(uut_id, sn, card_type, False)]

        libmfg_utils.mfg_summary_disp(stage, test_summary_dict, [])

        return
        #### END OF TAORMINA TEST


    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    pass_rslt_list = list()
    fail_rslt_list = list()
    mtp_mgmt_ctrl.cli_log_inf("Start the Barcode Scan Process", level=0)
    while True:
        scan_rslt = mtp_mgmt_ctrl.mtp_barcode_scan(False, swmtestmode)
        if scan_rslt:
            break;
        mtp_mgmt_ctrl.cli_log_inf("Restart the Barcode Scan Process", level=0)

    # validate scanned barcodes if flag is set
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if not ALLOWED_FRU_ONLY_FLAG:
            break
        key = libmfg_utils.nic_key(slot)
        nic_cli_id_str = libmfg_utils.id_str(mtp = mtp_id, nic = slot)
        if scan_rslt[key]["VALID"]:
            sn = scan_rslt[key]["SN"]
            pn = scan_rslt[key]["PN"]
            mac = scan_rslt[key]["MAC"]
            mac_ui = libmfg_utils.mac_address_format(mac)
            
            ## ALOM:
            if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = scan_rslt[key]["SN_ALOM"]
                alom_pn = scan_rslt[key]["PN_ALOM"]
                if swmtestmode == Swm_Test_Mode.ALOM:
                    # no MAC identifier
                    continue
                else:
                    try:
                        fru_mapping[mac]
                    except KeyError:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Missing from FRU mapping table: {:s}".format(mac_ui))
                        scan_rslt[key]["VALID"] = False
                        continue
                    try:
                        if fru_mapping[mac]["SN"] != sn:
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Scanned SN does not match: expect {:s}, got {:s}".format(fru_mapping[mac]["SN"], sn))
                            scan_rslt[key]["VALID"] = False
                        if fru_mapping[mac]["PN"] != pn: 
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Scanned PN does not match: expect {:s}, got {:s}".format(fru_mapping[mac]["PN"], pn))
                            scan_rslt[key]["VALID"] = False
                        if fru_mapping[mac]["SN_ALOM"] != alom_sn: 
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Scanned PN does not match: expect {:s}, got {:s}".format(fru_mapping[mac]["SN_ALOM"], alom_sn))
                            scan_rslt[key]["VALID"] = False
                        if fru_mapping[mac]["PN_ALOM"] != alom_pn: 
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Scanned PN does not match: expect {:s}, got {:s}".format(fru_mapping[mac]["PN_ALOM"], alom_pn))
                            scan_rslt[key]["VALID"] = False
                    except KeyError as e:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Missing from FRU mapping table: {:s} for MAC {:s}".format(e, mac_ui))
                        scan_rslt[key]["VALID"] = False
                        continue
            ## not ALOM:
            else:
                try:
                    fru_mapping[mac]
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Missing from FRU mapping table: {:s}".format(mac_ui))
                    scan_rslt[key]["VALID"] = False
                    continue
                try:
                    if fru_mapping[mac]["SN"] != sn:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Scanned SN does not match: expect {:s}, got {:s}".format(fru_mapping[mac]["SN"], sn))
                        scan_rslt[key]["VALID"] = False
                    if fru_mapping[mac]["PN"] != pn: 
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Scanned PN does not match: expect {:s}, got {:s}".format(fru_mapping[mac]["PN"], pn))
                        scan_rslt[key]["VALID"] = False
                except KeyError as e:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Missing from FRU mapping table: {:s} for MAC {:s}".format(e, mac_ui))
                    scan_rslt[key]["VALID"] = False
                    continue

    # print scan summary
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        nic_cli_id_str = libmfg_utils.id_str(mtp = mtp_id, nic = slot)
        if scan_rslt[key]["VALID"]:
            sn = scan_rslt[key]["SN"]
            pn = scan_rslt[key]["PN"]
            mac_ui = libmfg_utils.mac_address_format(scan_rslt[key]["MAC"])
            if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = scan_rslt[key]["SN_ALOM"]
                alom_pn = scan_rslt[key]["PN_ALOM"]
                if swmtestmode == Swm_Test_Mode.ALOM:
                    pass_rslt_list.append(nic_cli_id_str + "SN_ALOM = " + alom_sn + " PN_ALOM = " + alom_pn)
                else:
                    pass_rslt_list.append(nic_cli_id_str + "SN = " + sn + "; MAC = " + mac_ui + "; PN = " + pn + "; SN_ALOM = " + alom_sn + "; PN_ALOM = " + alom_pn)
            else:
                pass_rslt_list.append(nic_cli_id_str + "SN = " + sn + "; MAC = " + mac_ui + "; PN = " + pn)
        else:
            fail_rslt_list.append(nic_cli_id_str + "NIC Absent")
    libmfg_utils.cli_log_rslt("Barcode Scan Summary", pass_rslt_list, fail_rslt_list, test_log_filep)

    scan_cfg_file = log_dir + log_sub_dir + MTP_DIAG_Logfile.SCAN_BARCODE_FILE
    scan_cfg_filep = open(scan_cfg_file, "w+")
    mtp_mgmt_ctrl.gen_barcode_config_file(scan_cfg_filep, scan_rslt)
    scan_cfg_filep.close()
    log_file_list.append(scan_cfg_file)

    # reload the barcode config file
    nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(scan_cfg_file)

    mtp_mgmt_ctrl.mtp_apc_pwr_off()
    mtp_mgmt_ctrl.cli_log_inf("Power off APC, Wait {:d} seconds for system coming down\n".format(MTP_Const.MTP_POWER_OFF_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_POWER_OFF_DELAY)

    mtp_mgmt_ctrl.mtp_apc_pwr_on()
    mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)
    # Check if image update is needed
    mtp_dl_image_list = list()
    if (mtp_capability & 0x1):
        for nic_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
            try:
                mtp_dl_image_list.append(NIC_IMAGES.cpld_img[nic_type])
                if nic_type == NIC_Type.NAPLES100HPE:
                    mtp_dl_image_list.append(NIC_IMAGES.cpld_img["P41854"])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(nic_type))
            try:
                mtp_dl_image_list.append(NIC_IMAGES.diagfw_img[nic_type])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(nic_type))

    if (mtp_capability & 0x2):
        for nic_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST + ["P41851", "P46653", "68-0016", "68-0017"]:
            try:
                mtp_dl_image_list.append(NIC_IMAGES.cpld_img[nic_type])
                if nic_type == NIC_Type.NAPLES100HPE:
                    mtp_dl_image_list.append(NIC_IMAGES.cpld_img["P41854"])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(nic_type))
            try:
                mtp_dl_image_list.append(NIC_IMAGES.diagfw_img[nic_type])
                mtp_dl_image_list.append(NIC_IMAGES.diagfw_img["68-0010"])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(nic_type))
            if nic_type in ELBA_NIC_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.fail_cpld_img[nic_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing failsafe cpld image for {:s}".format(nic_type))
            if nic_type in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.fea_cpld_img[nic_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing feature row image for {:s}".format(nic_type))

    mtp_dl_image_list.append(NIC_IMAGES.goldfw_img["ORTANO2ADI"])
    
    onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
    if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, mtp_dl_image_list, onboard_image_files):
        mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis firmware", level=0)
        mtpid_list.remove(mtp_id)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP NIC firmware is updated", level=0)

    mtp_diag_image = MFG_IMAGE_FILES.MTP_AMD64_IMAGE
    nic_diag_image = MFG_IMAGE_FILES.MTP_ARM64_IMAGE

    if not libmfg_utils.mtp_update_diag_image(mtp_mgmt_ctrl, mtp_diag_image, nic_diag_image, onboard_image_files):
        mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis diag image", level=0)
        mtpid_list.remove(mtp_id)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP Diag Image is updated", level=0)

    if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, stage=FF_Stage.FF_DL):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
        logfile_close(log_filep_list)
        return

    # Set Naples25SWM test mode
    mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)

    pass_nic_list = list()
    fail_nic_list = list()
    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    dsp = FF_Stage.FF_DL

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        if not nic_prsnt_list[slot]:
            continue
        if slot not in pass_nic_list:
            pass_nic_list.append(slot)

    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.mtp_power_on_nic(pass_nic_list, dl=True)

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if nic_prsnt_list[slot]:
            key = libmfg_utils.nic_key(slot)
            pn = nic_fru_cfg[mtp_id][key]["PN"]
            mtp_mgmt_ctrl.mtp_nic_sn_init(slot)
            mtp_mgmt_ctrl.mtp_set_nic_pn(slot, pn)

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        if not nic_prsnt_list[slot]:
            continue
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue
        sn = nic_fru_cfg[mtp_id][key]["SN"]

        test_list = ["CONSOLE_BOOT"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)
        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            if test == "CONSOLE_BOOT":
                ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                if test == "CONSOLE_BOOT":
                    # rough way to track failure
                    mtp_mgmt_ctrl.mtp_set_nic_failed_boot(slot)
                    # since post_fail won't be triggered for this, do it ourselves
                    libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                   mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, dsp, test, duration))

    if "CONSOLE_BOOT" not in args.skip_test:
        # power cycle all nic
        mtp_mgmt_ctrl.mtp_power_cycle_nic(pass_nic_list, dl=True)

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            continue
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue

        sn = nic_fru_cfg[mtp_id][key]["SN"]
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

        if nic_type not in PSLC_MODE_TYPE_LIST:
            continue
        test_list = ["NIC_BOOT_INIT", "NIC_MGMT_INIT", "SET_PSLC"]
        for skip_test in args.skip_test:
            if skip_test in test_list:
                test_list.remove(skip_test)
        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            if test == "NIC_BOOT_INIT":
                ret = mtp_mgmt_ctrl.mtp_nic_boot_info_init(slot)
            elif test == "NIC_MGMT_INIT":
                ret = mtp_mgmt_ctrl.mtp_nic_mgmt_init(slot, fpo=True)
            elif test == "SET_PSLC":
                ret = mtp_mgmt_ctrl.mtp_setting_partition(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
        # power cycle only the cards that went through set_pslc
        if slot not in fail_nic_list:
            mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
    mtp_mgmt_ctrl.mtp_power_on_nic(pass_nic_list, dl=True)

    # init nic diag env.
    rc = mtp_mgmt_ctrl.mtp_nic_diag_init(emmc_format=True, fru_valid=False, sn_tag=True, emmc_check=True, fru_cfg=nic_fru_cfg)
    if not rc:
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)


    mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Started", level=0)
    mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot")
            continue
        sn = nic_fru_cfg[mtp_id][key]["SN"]
        mac = nic_fru_cfg[mtp_id][key]["MAC"]
        pn = nic_fru_cfg[mtp_id][key]["PN"]
        mac_ui = libmfg_utils.mac_address_format(mac)
        if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
            alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]

        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[nic_type]
        qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img[nic_type]
        if nic_type == NIC_Type.NAPLES25OCP and mtp_mgmt_ctrl.mtp_is_nic_ocp_dell(slot):
            qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img["68-0010"]
        if nic_type == NIC_Type.NAPLES25SWM:
            qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot, pn)]
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot, pn)]
        if nic_type == NIC_Type.NAPLES100HPE and mtp_mgmt_ctrl.mtp_is_nic_cloud(slot):
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img["P41854"]
        failsafe_cpld_img_file = ""
        if nic_type in ELBA_NIC_TYPE_LIST:
            failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img[nic_type]

        if nic_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
            mtp_exp_capability = 0x1
        elif nic_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
            mtp_exp_capability = 0x2
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")
            continue

        if not mtp_capability & mtp_exp_capability:
            mtp_mgmt_ctrl.cli_log_err("MTP doesn't support {:s}".format(nic_type))
            mtp_mgmt_ctrl.mtp_chassis_shutdown()
            logfile_close(log_filep_list)
            # cleanup the log dir
            logfile_cleanup([log_dir+log_sub_dir])
            return

        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix:")
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
            alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}; SN_ALOM = {:s}; PN_ALOM = {:s}".format(sn, mac_ui, pn, alom_sn, alom_pn))
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}".format(sn, mac_ui, pn))
            
        if nic_type in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD1 image: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD2 image: " + os.path.basename(failsafe_cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI image: " + os.path.basename(qspi_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end\n")
        elif nic_type in ELBA_NIC_TYPE_LIST and nic_type in FPGA_TYPE_LIST:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FPGA main image: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FPGA gold image: " + os.path.basename(failsafe_cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI image: " + os.path.basename(qspi_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end\n")
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD image: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI image: " + os.path.basename(qspi_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end\n")

        if slot not in pass_nic_list:
            pass_nic_list.append(slot)

        # DL precheck
        pre_check_testlist = ["NIC_POWER", "NIC_TYPE", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT"]
        for skipped_test in args.skip_test:
            if skipped_test in pre_check_testlist:
                pre_check_testlist.remove(skipped_test)
        for test in pre_check_testlist:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            if test == "NIC_POWER":
                ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
            elif test == "NIC_TYPE":
                ret = mtp_mgmt_ctrl.mtp_nic_type_valid(slot)
            elif test == "NIC_PRSNT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
            elif test == "NIC_INIT":
                ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
            elif test == "NIC_DIAG_BOOT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
                #ret = False
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                   mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, dsp, test, duration))

                    
    # program the NIC firmware
    nic_thread_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue
        pn = nic_fru_cfg[mtp_id][key]["PN"]

        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img[nic_type]
        cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[nic_type]
        if nic_type == NIC_Type.NAPLES25OCP and mtp_mgmt_ctrl.mtp_is_nic_ocp_dell(slot):
            qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img["68-0010"]
        if nic_type == NIC_Type.NAPLES25SWM:
            qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot, pn)]
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot, pn)]
        if nic_type == NIC_Type.NAPLES100HPE and mtp_mgmt_ctrl.mtp_is_nic_cloud(slot):
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img["P41854"]
        failsafe_cpld_img_file = ""
        if nic_type in ELBA_NIC_TYPE_LIST:
            failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img[nic_type]

        qspi_gold_img_file = ""
        if nic_type == NIC_Type.ORTANO2ADI:
            qspi_gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[nic_type]

        nic_thread = threading.Thread(target = single_nic_fw_program, args = (mtp_mgmt_ctrl,
                                                                              nic_fru_cfg[mtp_id][key],
                                                                              cpld_img_file,
                                                                              failsafe_cpld_img_file,
                                                                              qspi_img_file,
                                                                              qspi_gold_img_file,
                                                                              slot,
                                                                              fail_nic_list,
                                                                              pass_nic_list,
                                                                              swmtestmode,
                                                                              args.skip_test))
        nic_thread.daemon = True
        nic_thread.start()
        nic_thread_list.append(nic_thread)
        time.sleep(2)

    # monitor all the thread
    while True:
        if len(nic_thread_list) == 0:
            break
        for nic_thread in nic_thread_list[:]:
            if not nic_thread.is_alive():
                nic_thread.join()
                nic_thread_list.remove(nic_thread)
        time.sleep(5)

    # Ortano Boot check moved out of parallel tests to sequential test
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            continue
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue
        sn = nic_fru_cfg[mtp_id][key]["SN"]
        dsp = FF_Stage.FF_DL
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.ORTANO2 or nic_type == NIC_Type.ORTANO2ADI: 
            testlist = ["CPLD_BOOT_CHECK"]
        else:
            continue
        for skip_test in args.skip_test:
            if skip_test in testlist:
                testlist.remove(skip_test)
        for test in testlist:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            
            # check CPLD partition
            if test == "CPLD_BOOT_CHECK":
                ret = mtp_mgmt_ctrl.mtp_recover_nic_console(slot)
                ret &= mtp_mgmt_ctrl.mtp_check_nic_cpld_partition(slot, console=True)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                continue

            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

    if not mtp_mgmt_ctrl.mtp_nic_esec_write_protect(pass_nic_list=pass_nic_list, enable=False):
        mtp_mgmt_ctrl.cli_log_err("Disable ESEC Write Protection failed", level=0)

    # init nic diag env.
    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)


    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue

        sn = nic_fru_cfg[mtp_id][key]["SN"]
        mac = nic_fru_cfg[mtp_id][key]["MAC"]
        pn = nic_fru_cfg[mtp_id][key]["PN"]
        prog_date = str(nic_fru_cfg[mtp_id][key]["TS"])
        exp_sn = sn
        exp_mac = "-".join(re.findall("..", mac))
        exp_pn = pn
        exp_date = prog_date
        if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
            alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]
            exp_alom_sn = alom_sn
            exp_alom_pn = alom_pn
            exp_assettag = 'C0'
    
        # nic power status check
        test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY", "AVS_SET"]
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25:
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "REWORK_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY", "AVS_SET"]
        if nic_type == NIC_Type.NAPLES25SWM:
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "REWORK_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY", "AVS_SET"]
            if swmtestmode == Swm_Test_Mode.ALOM:
                test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_ALOM_VERIFY", "CPLD_VERIFY"]
        if nic_type == NIC_Type.ORTANO:
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY"]
        if nic_type == NIC_Type.ORTANO2:
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "FEA_VERIFY", "QSPI_VERIFY", "BOARD_CONFIG", "L1_ESEC_PROG", "AVS_SET"]
        if nic_type == NIC_Type.ORTANO2ADI:
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "FEA_VERIFY", "L1_ESEC_PROG", "QSPI_VERIFY"] 
        if nic_type == NIC_Type.POMONTEDELL or nic_type == NIC_Type.LACONA32DELL or nic_type == NIC_Type.LACONA32:
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY", "BOARD_CONFIG", "L1_ESEC_PROG", "AVS_SET"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)
        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            if test == "NIC_POWER":
                ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
            elif test == "NIC_PRSNT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
            elif test == "NIC_INIT":
                ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
            # verify diagfw boot
            elif test == "NIC_DIAG_BOOT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
            # verify fru
            elif test == "FRU_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_fru(slot, exp_sn, exp_mac, exp_pn, exp_date)
            elif test == "FRU_ALOM_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_alom_fru(slot, exp_alom_sn, exp_alom_pn, exp_date)
            elif test == "REWORK_VERIFY":
                ret = hpe_rework_verify(mtp_mgmt_ctrl, slot)
            # verify cpld
            elif test == "CPLD_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)
            # verify Feature Row
            elif test == "FEA_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld_fea(slot)
            # verify qspi
            elif test == "QSPI_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_qspi(slot)
            elif test == "BOARD_CONFIG":
                ret = mtp_mgmt_ctrl.mtp_nic_board_config(slot)
            elif test == "L1_ESEC_PROG":
                ret = mtp_mgmt_ctrl.mtp_nic_l1_esecure_prog(slot)
            # set avs
            elif test == "AVS_SET":
                ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_avs(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, dsp, test, duration))


    mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Complete", level=0)
    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.mtp_chassis_shutdown()
    mfg_dl_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP DL Test Duration:{:s}".format(mfg_dl_stop_ts - mfg_dl_start_ts))

    for slot in pass_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if not swmtestmode == Swm_Test_Mode.ALOM:
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
        
    for slot in fail_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = nic_fru_cfg[mtp_id][key]["SN"]
        if not swmtestmode == Swm_Test_Mode.ALOM:
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
    logfile_close(log_filep_list)

    # pkg the logfile
    log_pkg_file = MTP_DIAG_Logfile.MFG_DL_LOG_PKG_FILE.format(mtp_id, log_timestamp)
    os.system(MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format(log_dir+log_pkg_file, log_dir, log_sub_dir))

    # move the logs to the log root dir
    log_hard_copy_flag = True
    log_relative_link = None
    for slot in fail_nic_list + pass_nic_list:
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        key = libmfg_utils.nic_key(slot)
        sn = nic_fru_cfg[mtp_id][key]["SN"]
        if not sn:
            continue
        if GLB_CFG_MFG_TEST_MODE:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_DL_LOG_DIR_FMT.format(nic_type, sn)
        else:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_DL_LOG_DIR_FMT.format(nic_type, sn)
        os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir))
        if log_hard_copy_flag:
            libmfg_utils.cli_inf("[{:s}] Collecting log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
            os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))
            log_relative_link = "../{:s}/{:s}".format(sn, os.path.basename(log_pkg_file))
            log_hard_copy_flag = False
        else:
            libmfg_utils.cli_inf("[{:s}] Create link log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
            chdir_cmd = "cd {:s}".format(mfg_log_dir)
            ln_cmd = MFG_DIAG_CMDS.MFG_LOG_LINK_FMT.format(log_relative_link, os.path.basename(log_pkg_file))
            cmd = "{:s} && {:s}".format(chdir_cmd, ln_cmd)
            os.system(cmd)
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            if not alom_sn:
                continue
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_DL_LOG_DIR_FMT.format(nic_type, alom_sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_DL_LOG_DIR_FMT.format(nic_type, alom_sn)
            os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir))
            if log_hard_copy_flag:
                libmfg_utils.cli_inf("[{:s}] Collecting log file {:s}".format(alom_sn, log_pkg_file))
                os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))
                log_relative_link = "../{:s}/{:s}".format(alom_sn, os.path.basename(log_pkg_file))
                log_hard_copy_flag = False
            else:
                libmfg_utils.cli_inf("[{:s}] Create link log file {:s}".format(alom_sn, log_relative_link))
                chdir_cmd = "cd {:s}".format(mfg_log_dir)
                ln_cmd = MFG_DIAG_CMDS.MFG_LOG_LINK_FMT.format(log_relative_link, os.path.basename(log_pkg_file))
                cmd = "{:s} && {:s}".format(chdir_cmd, ln_cmd)
                os.system(cmd)            

    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_id, mfg_dl_start_ts, mfg_dl_stop_ts, test_log_file, FF_Stage.FF_DL)

    # cleanup the log dir
    logfile_cleanup([log_dir+log_sub_dir, log_dir+log_pkg_file])

    return

if __name__ == "__main__":
    main()

