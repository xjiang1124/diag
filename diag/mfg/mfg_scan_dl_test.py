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
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libdefs import NIC_Vendor
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
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
    for fp in filep_list:
        fp.close()
    os.system("sync")


def logfile_cleanup(file_list):
    for _file in file_list:
        os.system("rm -rf {:s}".format(_file))


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
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg, slots_to_skip=mtp_slots_to_skip)
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

def single_nic_fw_program(mtp_mgmt_ctrl, fru_cfg, cpld_img_file, fail_cpld_img_file, qspi_img_file, slot, fail_nic_list, pass_nic_list, swmtestmode, skip_testlist = []):
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

    if nic_type == NIC_Type.ORTANO:
        test_list = ["FRU_PROG", "QSPI_PROG", "CPLD_PROG", "FSAFE_CPLD_PROG", "CPLD_REF", "NIC_PWRCYC"]
    if nic_type == NIC_Type.ORTANO2:
        test_list = ["FIX_VRM", "FRU_PROG", "QSPI_PROG", "CPLD_PROG", "FSAFE_CPLD_PROG", "CPLD_REF"]
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
        # refresh CPLD
        elif test == "CPLD_REF":
            ret = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(slot)
        # check booted from correct CPLD partition
        elif test == "BOOT_CHECK":
            ret = mtp_mgmt_ctrl.mtp_check_nic_cpld_partition(slot)
        # extra powercycle to refresh CPLD
        elif test == "NIC_PWRCYC":
            ret = mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
            ret &= mtp_mgmt_ctrl.mtp_power_on_single_nic(slot)
        elif test == "FIX_VRM":
            ret = mtp_mgmt_ctrl.mtp_nic_fix_vrm(slot)
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

def main():
    parser = argparse.ArgumentParser(description="MFG DL Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--fru_mapping_file", "-f", help="Mapping file of allowed MACs, SNs, PNs", action="store_true")
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    if args.fru_mapping_file:
        ALLOWED_FRU_ONLY_FLAG = True
        fru_mapping = libmfg_utils.load_cfg_from_yaml("config/new_fru_cfg.yaml")
        # remove store_true to allow getting filename in args.
    else:
        ALLOWED_FRU_ONLY_FLAG = False
        fru_mapping = dict()

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db)
    mtp_id = mtpid_list[0]

    # local log files
    log_file_list = list()
    log_filep_list = list()
    log_dir = "log/"
    log_timestamp = libmfg_utils.get_timestamp()
    log_sub_dir = MTP_DIAG_Logfile.MFG_DL_LOG_DIR.format(mtp_id, log_timestamp)
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
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = log_dir + log_sub_dir + "mtp_{:s}_diag.log".format(key)
        log_file_list.append(diag_nic_log_file)
        diag_nic_log_filep = open(diag_nic_log_file, "w+", buffering=0)
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list)

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

    # Pomonte P1 build: refactor the SN and PN from the ones scanned
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        if scan_rslt[key]["VALID"]:
            pn = scan_rslt[key]["PN"]
            if pn.startswith("68-0022") or pn.startswith("68-0025"):
                # fru_date = scan_rslt[key]["TS"]
                # year_digit = fru_date[-1:]
                # month_digit = '{:x}'.format(int(fru_date[0:2]))
                # if int(fru_date[2:4]) < 10:
                #     day_digit = fru_date[2:4]
                # else:
                #     day_digit = chr(55+int(fru_date[2:4]))
                year_digit = "1"
                month_digit = "9"
                day_digit = "G"
                scan_rslt[key]["SN"] = "USFLUPK" + year_digit + month_digit + day_digit + scan_rslt[key]["SN"][-4:]
                scan_rslt[key]["PN"] = "0PCFPCX00"
                if pn.startswith("68-0025"):
                    scan_rslt[key]["PN"] = "0X322FX01"

    scan_cfg_file = log_dir + log_sub_dir + "dl_barcode.yaml"
    scan_cfg_filep = open(scan_cfg_file, "w+")
    mtp_mgmt_ctrl.gen_barcode_config_file(scan_cfg_filep, scan_rslt)
    scan_cfg_filep.close()
    log_file_list.append(scan_cfg_file)

    # reload the barcode config file
    nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(scan_cfg_file)

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
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(nic_type))
                continue
            try:
                mtp_dl_image_list.append(NIC_IMAGES.diagfw_img[nic_type])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(nic_type))
                continue
    if (mtp_capability & 0x2):
        for nic_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
            try:
                mtp_dl_image_list.append(NIC_IMAGES.cpld_img[nic_type])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(nic_type))
                continue
            try:
                mtp_dl_image_list.append(NIC_IMAGES.diagfw_img[nic_type])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(nic_type))
                continue
            if nic_type in ELBA_NIC_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.fail_cpld_img[nic_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing failsafe cpld image for {:s}".format(nic_type))
                    continue
            if nic_type in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.fea_cpld_img[nic_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing feature row image for {:s}".format(nic_type))
                    continue

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

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()
    pass_nic_list = list()
    fail_nic_list = list()
    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    dsp = FF_Stage.FF_DL
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
        mtp_mgmt_ctrl.mtp_power_cycle_nic()

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
    mtp_mgmt_ctrl.mtp_power_on_nic()

    # init nic diag env.
    rc = mtp_mgmt_ctrl.mtp_nic_diag_init(emmc_format=True, fru_valid=False, sn_tag=True, fru_cfg=nic_fru_cfg)
    if not rc:
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

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

        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img[nic_type]
        cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[nic_type]
        failsafe_cpld_img_file = ""
        if nic_type in ELBA_NIC_TYPE_LIST:
            failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img[nic_type]

        nic_thread = threading.Thread(target = single_nic_fw_program, args = (mtp_mgmt_ctrl,
                                                                              nic_fru_cfg[mtp_id][key],
                                                                              cpld_img_file,
                                                                              failsafe_cpld_img_file,
                                                                              qspi_img_file,
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
        if nic_type == NIC_Type.ORTANO2:
            testlist = ["CPLD_BOOT_CHECK", "NIC_PWRCYC"]
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
            # extra powercycle to refresh CPLD
            elif test == "NIC_PWRCYC":
                ret = mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                ret &= mtp_mgmt_ctrl.mtp_power_on_single_nic(slot)
                #ret &= mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)
                # CPLD_VERIFY test is done later. Any quick way to verify that powercycle worked?
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

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()
    # init nic diag env.
    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

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

        # # power cycle all nic (Debug Power Failure Issue)   #NZ: but why inside for loop -> cycling 10 times?
        # mtp_mgmt_ctrl.mtp_power_cycle_nic()
    
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
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "FEA_VERIFY", "QSPI_VERIFY", "BOARD_CONFIG", "AVS_SET"]
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

        # mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)

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

