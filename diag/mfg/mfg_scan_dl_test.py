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
from libdefs import FLEX_TWO_WAY_COMM
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import FLEX_SHOP_FLOOR_CONTROL
from libmfg_cfg import FLEX_ERR_CODE_MAP
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import PSLC_MODE_TYPE_LIST
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import GIGLIO_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmfg_cfg import NEED_UBOOT_IMG_CARD_TYPE_LIST
from libsku_cfg import PART_NUMBERS_MATCH
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


def load_mtp_cfg(cfg_yaml=None):
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath(cfg_yaml))
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

def single_nic_qspi_program(mtp_mgmt_ctrl, qspi_img_file, qspi_gold_img_file, uboot_img_file, uboota_img_file, ubootb_img_file, uboot_installer_file, slot, skip_testlist, nic_test_rslt_list):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)

    dsp = FF_Stage.FF_DL
    testlist = ["QSPI_PROG"]
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) and nic_type not in (NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT):
        testlist = ["QSPI_PROG", "UBOOT_PROG"]
    if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT):
        testlist = ["QSPI_PROG", "UBOOT_PROG", "QSPI_GOLD_PROG"]
    if nic_type == NIC_Type.ORTANO2ADIIBM:
        testlist = ["QSPI_PROG", "UBOOT_PROG", "UBOOTA_PROG", "UBOOTB_PROG", "QSPI_GOLD_PROG"]
    for skip_test in skip_testlist:
        if skip_test in testlist:
            testlist.remove(skip_test)
    for test in testlist:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        if test == "QSPI_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_qspi(slot, qspi_img_file)
        elif test == "QSPI_GOLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_qspi(slot, qspi_gold_img_file, True)
        elif test == "UBOOT_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_uboot(slot, uboot_img_file, uboot_installer_file, uboot_pat="boot0")
        elif test == "UBOOTA_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_uboot(slot, uboota_img_file, uboot_installer_file, uboot_pat="uboota")
        elif test == "UBOOTB_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_uboot(slot, ubootb_img_file, uboot_installer_file, uboot_pat="ubootb")
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            nic_test_rslt_list[slot] = False
            # mtp_mgmt_ctrl.mtp_dump_err_msg(mtp_mgmt_ctrl.mtp_get_nic_err_msg(slot))
            mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

def single_nic_program(mtp_mgmt_ctrl, fru_cfg, cpld_img_file, fail_cpld_img_file, fea_cpld_img_file, slot, swmtestmode, skip_testlist, nic_test_rslt_list):
    sn = fru_cfg["SN"]
    mac = fru_cfg["MAC"]
    pn = fru_cfg["PN"]
    prog_date = str(fru_cfg["TS"])
    dsp = FF_Stage.FF_DL
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

    testlist = ["QSPI_VERIFY", "FRU_PROG", "CPLD_PROG", "CPLD_REF"]
    if (nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM):
        testlist = ["QSPI_VERIFY", "FRU_PROG"]
    if nic_type == NIC_Type.NAPLES25OCP:
        testlist = ["QSPI_VERIFY", "FRU_PROG", "CPLD_PROG"]
    if nic_type == NIC_Type.ORTANO2:
        testlist = ["QSPI_VERIFY", "FIX_VRM", "VDD_DDR_FIX", "FRU_PROG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT):
        testlist = ["QSPI_VERIFY", "FRU_PROG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    if nic_type in (NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOALI):
        testlist = ["QSPI_VERIFY", "FIX_VRM", "VDD_DDR_FIX", "FRU_PROG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    if nic_type == NIC_Type.POMONTEDELL:
        testlist = ["QSPI_VERIFY", "VDD_DDR_FIX", "FRU_PROG", "FPGA_PROG"]
    if nic_type == NIC_Type.LACONA32DELL or nic_type == NIC_Type.LACONA32:
        testlist = ["QSPI_VERIFY", "FRU_PROG", "FPGA_PROG"]
    for skipped_test in skip_testlist:
        if skipped_test in testlist:
            testlist.remove(skipped_test)
    for test in testlist:
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
        # read old FRU via hexdump
        elif test == "FRU_DUMP":
            ret = mtp_mgmt_ctrl.mtp_dump_nic_fru(slot, expect_mac=mac, expect_pn=pn)
        # program CPLD
        elif test == "CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
        # program all FPGA partitions
        elif test == "FPGA_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_fpga(slot)
        # program failsafe CPLD
        elif test == "FSAFE_CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_failsafe_cpld(slot, fail_cpld_img_file)
        # program feature row
        elif test == "FEA_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld_feature_row(slot, fea_cpld_img_file)
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
        elif test == "QSPI_VERIFY":
            ret = mtp_mgmt_ctrl.mtp_verify_nic_qspi(slot)
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
            nic_test_rslt_list[slot] = False
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
    parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--jobd_logdir", "--logdir", help="Store final log to different path", default=None)

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

    stage = FF_Stage.FF_DL

    mtpcfg_file = None
    if args.mtpcfg:
        mtpcfg_file = os.path.relpath(args.mtpcfg)
        mtp_cfg_db = load_mtp_cfg(mtpcfg_file)
    else:
        mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
    mtp_id = mtpid_list[0]
    mtpid_fail_list = list()

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

    pass_nic_list = list()
    fail_nic_list = list()
    adi_ibm_reset_slot = list()
    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
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
        mtpid_list.remove(mtp_id)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

    # Sync timestamp to server
    timestamp_str = str(libmfg_utils.timestamp_snapshot())
    if not mtp_mgmt_ctrl.mtp_mgmt_set_date(timestamp_str):
        mtp_mgmt_ctrl.cli_log_err("MTP Chassis timestamp sync failed", level=0)
        mtpid_list.remove(mtp_id)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP Chassis timestamp sync'd", level=0)

    # Check if diag image update is needed
    mtp_diag_image = MFG_IMAGE_FILES.MTP_AMD64_IMAGE
    nic_diag_image = MFG_IMAGE_FILES.MTP_ARM64_IMAGE

    onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
    if not libmfg_utils.mtp_update_diag_image(mtp_mgmt_ctrl, mtp_diag_image, nic_diag_image, onboard_image_files):
        mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis diag image", level=0)
        mtpid_list.remove(mtp_id)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP Diag Image is updated", level=0)

    # init NIC types

    if not mtp_mgmt_ctrl.mtp_diag_pre_init_start(skip_nic_pn_init=True):
        mtp_mgmt_ctrl.cli_log_err("MTP diag init failed", level=0)
        mtpid_list.remove(mtp_id)
        return

    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue
        if str.upper(nic_fru_cfg[mtp_id][key]["VALID"]) != "YES":
            continue
        pass_nic_list.append(slot)
        pn = nic_fru_cfg[mtp_id][key]["PN"]
        mtp_mgmt_ctrl.mtp_set_nic_pn(slot, pn)

    # type check
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue
        if str.upper(nic_fru_cfg[mtp_id][key]["VALID"]) != "YES":
            continue
        dsp = stage
        test = "NIC_TYPE"
        sn = nic_fru_cfg[mtp_id][key]["SN"]
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        ret = mtp_mgmt_ctrl.mtp_nic_type_test(slot)
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)

    # Check that firmware images are present
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
                if nic_type == NIC_Type.ORTANO2ADI:
                    mtp_dl_image_list.append(NIC_IMAGES.goldfw_img["ORTANO2ADI"])
                if nic_type == NIC_Type.ORTANO2ADIIBM:
                    mtp_dl_image_list.append(NIC_IMAGES.goldfw_img["ORTANO2ADIIBM"])
                if nic_type == NIC_Type.ORTANO2ADIMSFT:
                    mtp_dl_image_list.append(NIC_IMAGES.goldfw_img["ORTANO2ADIMSFT"])
                if nic_type == NIC_Type.ORTANO2ADICR:
                    mtp_dl_image_list.append(NIC_IMAGES.goldfw_img["ORTANO2ADICR"])
                if nic_type == NIC_Type.ORTANO2ADICRMSFT:
                    mtp_dl_image_list.append(NIC_IMAGES.goldfw_img["ORTANO2ADICRMSFT"])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing goldfw image for {:s}".format(nic_type))
            try:
                mtp_dl_image_list.append(NIC_IMAGES.diagfw_img[nic_type])
                mtp_dl_image_list.append(NIC_IMAGES.diagfw_img["68-0010"])
                mtp_dl_image_list.append(NIC_IMAGES.diagfw_img["68-0015"])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(nic_type))
            if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.fail_cpld_img[nic_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing failsafe cpld image for {:s}".format(nic_type))
            if nic_type in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
                try:
                    mtp_dl_image_list.append(NIC_IMAGES.fea_cpld_img[nic_type])
                except KeyError:
                    mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing feature row image for {:s}".format(nic_type))
        for nic_type in FPGA_TYPE_LIST:
            try:
                mtp_dl_image_list.append(NIC_IMAGES.timer1_img[nic_type])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing timer1 image for {:s}".format(nic_type))
            try:
                mtp_dl_image_list.append(NIC_IMAGES.timer2_img[nic_type])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing timer2 image for {:s}".format(nic_type))
            try:
                mtp_dl_image_list.append(NIC_IMAGES.uboot_img[nic_type])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing uboot image for {:s}".format(nic_type))
        for card_type in NEED_UBOOT_IMG_CARD_TYPE_LIST:
            try:
                mtp_dl_image_list.append(NIC_IMAGES.uboot_img[card_type])
                if card_type == NIC_Type.ORTANO2ADIIBM:
                    mtp_dl_image_list.append(NIC_IMAGES.uboota_img[card_type])
                    mtp_dl_image_list.append(NIC_IMAGES.ubootb_img[card_type])
            except KeyError:
                mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing uboot image for {:s}".format(card_type))

    mtp_dl_image_list.append(NIC_IMAGES.uboot_img["INSTALLER"])
    
    onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
    mtp_dl_image_list = list(set(mtp_dl_image_list))
    if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, mtp_dl_image_list, onboard_image_files):
        mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis firmware", level=0)
        mtpid_list.remove(mtp_id)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP NIC firmware is updated", level=0)

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
        if GLB_CFG_MFG_TEST_MODE and FLEX_SHOP_FLOOR_CONTROL:
            pre_post_fail_list = libmfg_utils.flx_web_srv_two_way_comm_precheck_uut(mtp_mgmt_ctrl, fail_nic_list, sn, stage, slot, retry=FLEX_TWO_WAY_COMM.PRE_POST_RETRY)
        if slot in pass_nic_list and slot in fail_nic_list:
            pass_nic_list.remove(slot)

    if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, stage=stage, skip_nic_pn_init=True):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
        logfile_close(log_filep_list)
        return

    # Set Naples25SWM test mode
    mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)
    dsp = stage

    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.mtp_power_on_nic(pass_nic_list, dl=True)

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        test = "GET_NIC_TYPE_BY_PN"
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        if nic_prsnt_list[slot]:
            key = libmfg_utils.nic_key(slot)
            valid = nic_fru_cfg[mtp_id][key]["VALID"]
            if str.upper(valid) != "YES":
                continue
            pn = nic_fru_cfg[mtp_id][key]["PN"]
            sn = nic_fru_cfg[mtp_id][key]["SN"]
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            mtp_mgmt_ctrl.mtp_set_nic_sn(slot, sn)
            mtp_mgmt_ctrl.mtp_set_nic_pn(slot, pn)
            nic_type = libmfg_utils.get_nic_type_by_part_number(pn)
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            if nic_type:
                if nic_type == NIC_Type.ORTANO2ADIIBM and slot not in adi_ibm_reset_slot:
                    adi_ibm_reset_slot.append(slot)
                mtp_mgmt_ctrl.mtp_set_nic_type(slot, nic_type)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
            else:
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))

    mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Started", level=0)
    mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        if not nic_prsnt_list[slot]:
            continue
        if slot not in adi_ibm_reset_slot:
            continue
            
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

        test_list = []
        if nic_type == NIC_Type.ORTANO2ADIIBM:
            test_list = ["CONSOLE_BOOT_INIT","CHECK_CPLD_UPDATE_REQ","ERASE_BOARD_CONFIG"]

        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            if test == "CONSOLE_BOOT_INIT":
                ret = mtp_mgmt_ctrl.mtp_mgmt_nic_console_access(slot)
            elif test == "CHECK_CPLD_UPDATE_REQ":
                ret = mtp_mgmt_ctrl.mtp_nic_cpld_update_request(slot)
            elif test == "ERASE_BOARD_CONFIG":
                ret = mtp_mgmt_ctrl.mtp_nic_erase_board_config(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            if not ret:
                if test == "CHECK_CPLD_UPDATE_REQ":
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                        if slot not in fail_nic_list:
                            fail_nic_list.append(slot)
                        if slot in pass_nic_list:
                            pass_nic_list.remove(slot)
                        if slot in adi_ibm_reset_slot:
                            adi_ibm_reset_slot.remove(slot)
                        mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                        break
                    else:
                        mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                        if slot in adi_ibm_reset_slot:
                            adi_ibm_reset_slot.remove(slot)
                        break
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)
                    if slot in adi_ibm_reset_slot:
                        adi_ibm_reset_slot.remove(slot)
                    if test == "CONSOLE_BOOT_INIT":
                        # rough way to track failure
                        mtp_mgmt_ctrl.mtp_set_nic_failed_boot(slot)
                    mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                    break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

    if len(adi_ibm_reset_slot) > 0 and not mtp_mgmt_ctrl.mtp_nic_diag_init(adi_ibm_reset_slot, emmc_format=True, emmc_check=True, fru_fpo=True):
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            if not nic_prsnt_list[slot]:
                continue
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)
            if slot in adi_ibm_reset_slot:
                adi_ibm_reset_slot.remove(slot)


    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        if not nic_prsnt_list[slot]:
            continue
        if slot not in adi_ibm_reset_slot:
            continue

        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        test_list = []
        if nic_type == NIC_Type.ORTANO2ADIIBM:
            test_list = ["NOSECURE_CPLD_PROG", "NOSECURE_FAILSAFE_CPLD_PROG", "SET_DIAGFW_BOOT"]
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[nic_type]
            failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img[nic_type]
        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            if test == "NOSECURE_CPLD_PROG":
                ret = mtp_mgmt_ctrl.mtp_program_nic_adi_ibm_cpld(slot, cpld_img_file)
            elif test == "NOSECURE_FAILSAFE_CPLD_PROG":
                ret = mtp_mgmt_ctrl.mtp_program_nic_adi_ibm_failsafe_cpld(slot, failsafe_cpld_img_file)
            elif test == "SET_DIAGFW_BOOT":
                ret = mtp_mgmt_ctrl.mtp_set_nic_diagfw_boot(slot)
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
                if slot in adi_ibm_reset_slot:
                    adi_ibm_reset_slot.remove(slot)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

    if len(adi_ibm_reset_slot) > 0:
        mtp_mgmt_ctrl.mtp_power_cycle_nic(pass_nic_list, dl=True)

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

    # program the qspi, before initializing emmc
    ## 1. setup mgmt
    if not mtp_mgmt_ctrl.mtp_nic_mgmt_para_init_fpo(pass_nic_list):
        for slot in pass_nic_list:
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)


    ## 2. program fw
    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        if not nic_prsnt_list[slot]:
            continue
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue

        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img[nic_type]
        if nic_type == NIC_Type.ORTANO2 and mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
            qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img["68-0015"]
        if nic_type == NIC_Type.NAPLES25OCP and mtp_mgmt_ctrl.mtp_is_nic_ocp_dell(slot):
            qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img["68-0010"]
        if nic_type == NIC_Type.NAPLES25SWM:
            qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot)]
        qspi_gold_img_file = ""
        if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT):
            qspi_gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[nic_type]

        uboot_img_file = ""
        uboota_img_file = ""
        ubootb_img_file = ""
        uboot_installer_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.uboot_img["INSTALLER"]
        if nic_type in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) and nic_type not in (NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT):
            uboot_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.uboot_img[nic_type]
        if nic_type == NIC_Type.ORTANO2ADIIBM:
            uboota_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.uboota_img[nic_type]
            ubootb_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.ubootb_img[nic_type]

        nic_thread = threading.Thread(target = single_nic_qspi_program, args = (mtp_mgmt_ctrl,
                                                                                qspi_img_file,
                                                                                qspi_gold_img_file,
                                                                                uboot_img_file,
                                                                                uboota_img_file,
                                                                                ubootb_img_file,
                                                                                uboot_installer_file,
                                                                                slot,
                                                                                args.skip_test,
                                                                                nic_test_rslt_list))
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

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if not nic_test_rslt_list[slot]:
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)


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
        test_list = ["SET_PSLC", "EMMC_HWRESET_SET", "EMMC_BKOPS_EN"]

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
            elif test == "EMMC_HWRESET_SET":
                ret = mtp_mgmt_ctrl.mtp_nic_emmc_hwreset_set(slot)
            elif test == "EMMC_BKOPS_EN":
                ret = mtp_mgmt_ctrl.mtp_nic_emmc_bkops_en(slot)
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
    rc = mtp_mgmt_ctrl.mtp_nic_diag_init(pass_nic_list, emmc_format=True, fru_valid=False, sn_tag=True, emmc_check=True, fru_cfg=nic_fru_cfg)
    if not rc:
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            if not nic_prsnt_list[slot]:
                continue
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)

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
        riser_sn = None
        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25OCP:
            riser_sn = mtp_mgmt_ctrl.mtp_get_nic_ocp_adapter_sn(slot)

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
        if nic_type == NIC_Type.ORTANO2 and mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
            qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img["68-0015"]
        failsafe_cpld_img_file = ""
        if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img[nic_type]
        uboot_img_file = ""
        if nic_type in FPGA_TYPE_LIST:
            uboot_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.uboot_img[nic_type]

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
            if nic_type == NIC_Type.NAPLES25OCP:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "OCP Adapter SN = {:s}".format(riser_sn))

        if nic_type in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) and nic_type not in FPGA_TYPE_LIST:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD1 image: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD2 image: " + os.path.basename(failsafe_cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI image: " + os.path.basename(qspi_img_file))
            if nic_type in FPGA_TYPE_LIST:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI uboot image: " + os.path.basename(uboot_img_file))
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
                ret = mtp_mgmt_ctrl.mtp_nic_type_test(slot)
            elif test == "NIC_PRSNT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
            elif test == "NIC_INIT":
                ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
            elif test == "NIC_DIAG_BOOT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
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
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    nic_thread_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if not nic_prsnt_list[slot]:
            continue
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
        if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img[nic_type]
        fea_cpld_img_file = ""
        if nic_type in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
            failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img[nic_type]
            fea_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fea_cpld_img[nic_type]

        nic_thread = threading.Thread(target = single_nic_program, args = (mtp_mgmt_ctrl,
                                                                           nic_fru_cfg[mtp_id][key],
                                                                           cpld_img_file,
                                                                           failsafe_cpld_img_file,
                                                                           fea_cpld_img_file,
                                                                           slot,
                                                                           swmtestmode,
                                                                           args.skip_test,
                                                                           nic_test_rslt_list))
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

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if not nic_test_rslt_list[slot]:
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)

    if not mtp_mgmt_ctrl.mtp_nic_esec_write_protect(pass_nic_list=pass_nic_list ,fail_nic_list=fail_nic_list, enable=False, dsp=dsp):
        mtp_mgmt_ctrl.cli_log_err("Disable ESEC Write Protection failed", level=0)

    # init nic diag env.
    if not mtp_mgmt_ctrl.mtp_nic_diag_init(pass_nic_list):
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            if not nic_prsnt_list[slot]:
                continue
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)

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
        test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "AVS_SET"]
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25:
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "REWORK_VERIFY", "CPLD_VERIFY", "AVS_SET"]
        if nic_type == NIC_Type.NAPLES25SWM:
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "REWORK_VERIFY", "CPLD_VERIFY", "AVS_SET"]
            if swmtestmode == Swm_Test_Mode.ALOM:
                test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_ALOM_VERIFY", "CPLD_VERIFY"]
        if nic_type == NIC_Type.ORTANO:
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY"]
        if nic_type in (NIC_Type.ORTANO2, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOALI):
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "FEA_VERIFY", "BOARD_CONFIG", "L1_ESEC_PROG", "AVS_SET"]
        if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT):
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "FEA_VERIFY", "BOARD_CONFIG", "L1_ESEC_PROG"] 
        if nic_type == NIC_Type.POMONTEDELL:
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "BOARD_CONFIG", "L1_ESEC_PROG", "AVS_SET"]
        if nic_type in (NIC_Type.LACONA32, NIC_Type.LACONA32DELL):
            test_list = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "FPGA_PROG_VERIFY", "BOARD_CONFIG", "L1_ESEC_PROG", "AVS_SET"]
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
                ret = mtp_mgmt_ctrl.mtp_nic_hpe_rework_verify(slot)
            # verify FPGA against original file
            elif test == "FPGA_PROG_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_fpga(slot)
            # verify cpld
            elif test == "CPLD_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)
            # verify Feature Row
            elif test == "FEA_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld_fea(slot)
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

    # save the avs and ecc dump log files
    log_location = log_dir+log_sub_dir
    asic_sub_dir = "/asic_logs/"
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_location + asic_sub_dir)
    os.system(cmd)
    ipaddr, userid, passwd = mtp_mgmt_ctrl._mgmt_cfg
    libmfg_utils.network_get_file(ipaddr, userid, passwd, log_location + asic_sub_dir, MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES)
    libmfg_utils.network_get_file(ipaddr, userid, passwd, log_location + asic_sub_dir, MTP_DIAG_Logfile.ONBOARD_ASIC_DUMP_FILES)

    mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Complete", level=0)
    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.mtp_chassis_shutdown()
    mfg_dl_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP DL Test Duration:{:s}".format(mfg_dl_stop_ts - mfg_dl_start_ts))
    mfg_dl_summary = list()
    retest_block_default = False

    for slot in pass_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if not swmtestmode == Swm_Test_Mode.ALOM:
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
        mfg_dl_summary.append([slot + 1, sn, nic_type, True, retest_block_default])
        
    for slot in fail_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue
        sn = nic_fru_cfg[mtp_id][key]["SN"]
        if not swmtestmode == Swm_Test_Mode.ALOM:
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
        mfg_dl_summary.append([slot + 1, sn, nic_type, False, retest_block_default])
    logfile_close(log_filep_list)


    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot not in pass_nic_list and slot not in fail_nic_list:
            mfg_dl_summary.append([slot + 1, "SKIPPED", "SLOT", True, retest_block_default])

    # pkg the logfile
    log_pkg_file = MTP_DIAG_Logfile.MFG_DL_LOG_PKG_FILE.format(mtp_id, log_timestamp)
    os.system(MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format(log_dir+log_pkg_file, log_dir, log_sub_dir))

    # move the logs to the log root dir
    log_hard_copy_flag = True
    log_relative_link = None
    for slot in fail_nic_list + pass_nic_list:
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue
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

            qa_log_pkg_file = mfg_log_dir+os.path.basename(log_pkg_file)
            if args.jobd_logdir:
                dest = args.jobd_logdir + "/" + os.path.basename(qa_log_pkg_file)
                cmd = "cp {:s} {:s}".format(qa_log_pkg_file, args.jobd_logdir)
                os.system(cmd)
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
        libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mfg_dl_start_ts, mfg_dl_stop_ts, test_log_file, stage, mfg_dl_summary)

    # cleanup the log dir
    logfile_cleanup([log_dir+log_sub_dir, log_dir+log_pkg_file])

    mtp_dl_summary = dict()
    mtp_dl_summary[mtp_id] = mfg_dl_summary
    # dump the summary
    test_result = libmfg_utils.mfg_summary_disp(stage, mtp_dl_summary, mtpid_fail_list)

    # print return code for JobD to pick up
    if test_result:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

