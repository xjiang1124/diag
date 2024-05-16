#!/usr/bin/env python3

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
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import PSLC_MODE_TYPE_LIST
from libmfg_cfg import CAPRI_NIC_TYPE_LIST
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import GIGLIO_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmfg_cfg import CTO_MODEL_TYPE_LIST
from libsku_cfg import PART_NUMBERS_MATCH
from libmfg_cfg import MTP_HEALTH_MONITOR
from libdefs import FF_Stage
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode
import image_control
import testlog
import test_utils
import scanning

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
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/"+cfg_yaml))
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
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

def single_nic_qspi_program(mtp_mgmt_ctrl, qspi_img_file, qspi_gold_img_file, uboot_img_file, uboota_img_file, ubootb_img_file, uboot_installer_file, slot, skip_testlist, nic_test_rslt_list):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)

    dsp = FF_Stage.FF_DL
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    testlist = ["QSPI_PROG"] if nic_type in CAPRI_NIC_TYPE_LIST else ["ERASE_MAINFW", "QSPI_PROG"]
    if nic_type in (ELBA_NIC_TYPE_LIST) and nic_type not in (NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT):
        testlist = ["ERASE_MAINFW", "QSPI_PROG", "UBOOT_PROG"]
    if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4):
        testlist = ["ERASE_MAINFW", "QSPI_PROG", "UBOOT_PROG", "QSPI_GOLD_PROG"]
    if nic_type == NIC_Type.ORTANO2ADIIBM:
        testlist = ["ERASE_MAINFW", "QSPI_PROG", "UBOOT_PROG", "UBOOTA_PROG", "UBOOTB_PROG", "QSPI_GOLD_PROG"]
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
        elif test == "ERASE_MAINFW":
            ret = mtp_mgmt_ctrl.mtp_erase_main_fw_partition(slot)
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


def single_nic_program(mtp_mgmt_ctrl, cpld_img_file, fail_cpld_img_file, fea_cpld_img_file, slot, swmtestmode, skip_testlist, nic_test_rslt_list):
    sn = mtp_mgmt_ctrl.get_scanned_sn(slot)
    mac = mtp_mgmt_ctrl.get_scanned_mac(slot)
    pn = mtp_mgmt_ctrl.get_scanned_pn(slot)
    dpn = mtp_mgmt_ctrl.get_scanned_dpn(slot)
    prog_date = mtp_mgmt_ctrl.get_scanned_ts(slot)

    dsp = FF_Stage.FF_DL
    testlist = ["QSPI_VERIFY", "FRU_PROG", "CPLD_PROG", "CPLD_REF"]
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type in ELBA_NIC_TYPE_LIST:
        testlist = ["QSPI_VERIFY", "FRU_PROG", "ERASE_BOARD_CONFIG", "BOARD_CONFIG", "CPLD_PROG", "CPLD_REF"]
    if (nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM):
        testlist = ["QSPI_VERIFY", "FRU_PROG"]
    if nic_type == NIC_Type.NAPLES25OCP:
        testlist = ["QSPI_VERIFY", "FRU_PROG", "CPLD_PROG"]
    if nic_type == NIC_Type.ORTANO2:
        testlist = ["QSPI_VERIFY", "FIX_VRM", "VDD_DDR_FIX", "FRU_PROG", "ERASE_BOARD_CONFIG", "BOARD_CONFIG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT):
        testlist = ["QSPI_VERIFY", "FRU_PROG", "ERASE_BOARD_CONFIG", "BOARD_CONFIG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    if nic_type in (NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT):
        testlist = ["QSPI_VERIFY", "FIX_VRM", "VDD_DDR_FIX", "FRU_PROG", "ERASE_BOARD_CONFIG", "BOARD_CONFIG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    if nic_type in [NIC_Type.ORTANO2SOLOS4]:
        testlist = ["QSPI_VERIFY", "FIX_VRM", "VDD_DDR_FIX", "FRU_PROG", "ERASE_BOARD_CONFIG", "BOARD_CONFIG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    if nic_type in [NIC_Type.ORTANO2ADICRS4]:
        testlist = ["QSPI_VERIFY", "FRU_PROG", "ERASE_BOARD_CONFIG", "ASSIGN_BOARD_ID", "BOARD_CONFIG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    if nic_type == NIC_Type.POMONTEDELL:
        testlist = ["QSPI_VERIFY", "VDD_DDR_FIX", "FRU_PROG", "BOARD_CONFIG", "FPGA_PROG"]
    if nic_type == NIC_Type.LACONA32DELL or nic_type == NIC_Type.LACONA32:
        testlist = ["QSPI_VERIFY", "FRU_PROG", "BOARD_CONFIG", "FPGA_PROG"]
    if nic_type in GIGLIO_NIC_TYPE_LIST:
        testlist = ["QSPI_VERIFY", "VDD_DDR_FIX", "FRU_PROG", "ERASE_BOARD_CONFIG", "ASSIGN_BOARD_ID", "BOARD_CONFIG", "CPLD_PROG", "FSAFE_CPLD_PROG", "FEA_PROG", "CPLD_REF"]
    for skip_test in skip_testlist:
        if skip_test in testlist:
            testlist.remove(skip_test)
    for test in testlist:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        # program FRU
        if test == "FRU_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn, dpn)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            #skip ALOM programming if Naples25 SWM test mode is SWM only
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:  
                alom_sn = mtp_mgmt_ctrl.get_scanned_alom_sn(slot)
                alom_pn = mtp_mgmt_ctrl.get_scanned_alom_pn(slot)
                ret = mtp_mgmt_ctrl.mtp_program_nic_alom_fru(slot, prog_date, alom_sn, alom_pn)
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
        elif test == "FIX_VRM":
            ret = mtp_mgmt_ctrl.mtp_nic_fix_vrm(slot)
        elif test == "VDD_DDR_FIX":
            ret = mtp_mgmt_ctrl.mtp_nic_vdd_ddr_fix(slot)
        elif test == "QSPI_VERIFY":
            ret = mtp_mgmt_ctrl.mtp_verify_nic_qspi(slot)
        # assign borad id
        elif test == "ASSIGN_BOARD_ID":
            ret = mtp_mgmt_ctrl.mtp_nic_assign_board_id(slot, pn)
        elif test == "ERASE_BOARD_CONFIG":
            ret = mtp_mgmt_ctrl.mtp_nic_erase_board_config_ssh(slot)
        # set board config
        elif test == "BOARD_CONFIG":
            ret = mtp_mgmt_ctrl.mtp_nic_board_config(slot)
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

def health_status(mtp_health):
    mtp_health.monitr_mtp_health(timeout=MTP_Const.MTP_HEALTH_MONITOR_CYCLE)

def main():
    parser = argparse.ArgumentParser(description="MTP DL Test Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--dpn", help="Supply Diagnostic Part Number, for QA/lab only...MFG should enter DPN through scanning", default=None)
    parser.add_argument("--skip_test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("--skip_slots", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--scandl", help="Run ScanDL, i.e. reprogram all NIC FRUs", action='store_true', default=False)

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid

    mtp_cfg_db = load_mtp_cfg(args.mtpcfg)

    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    if not args.skip_test:
        args.skip_test = []

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, sys.stdout, None, [], skip_slots=args.skip_slots)
    # local logfiles
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=FF_Stage.FF_DL)

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    mtp_mgmt_ctrl.cli_log_inf("MTP DL Test Started", level=0)

    try:
        # read scanned barcode file except when we're skipping in dev environment
        scanned_nic_fru_cfg = dict()
        if args.scandl or "SCAN_VERIFY" not in args.skip_test:
            scanning.read_scanned_barcodes(mtp_mgmt_ctrl)
            scanned_nic_fru_cfg = mtp_mgmt_ctrl.barcode_scans

        if args.scandl:
            if not test_utils.mtp_common_setup_scandl(mtp_mgmt_ctrl, FF_Stage.FF_DL, scanned_nic_fru_cfg, args.skip_test):
                mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
                logfile_close(open_file_track_list)
                return
        else:
            if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, FF_Stage.FF_DL, args.skip_test):
                mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
                logfile_close(open_file_track_list)
                return

        if MTP_HEALTH_MONITOR:
            thread_health = threading.Thread(target=health_status, args=(mtp_mgmt_ctrl.get_mtp_health_monitor(),))
            thread_health.start()

        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        fail_nic_list = list()
        pass_nic_list = list()
        adi_ibm_reset_slot = list()

        # Add failed slots from toplevel
        if args.fail_slots:
            for slot in args.fail_slots:
                fail_nic_list.append(int(slot))

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            if not nic_prsnt_list[slot]:
                continue
            if args.scandl:
                key = libmfg_utils.nic_key(slot)
                if not scanned_nic_fru_cfg[key]["VALID"]:
                    continue
            if slot not in pass_nic_list:
                pass_nic_list.append(slot)

        # power cycle all nic
        mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.mtp_power_on_nic(pass_nic_list, dl=True)

        dsp = FF_Stage.FF_DL
        if not args.scandl:
            # read in current FRU
            nic_fru_cfg = mtp_mgmt_ctrl.mtp_construct_nic_fru_config(fail_nic_list, swmtestmode)
            # failures from construct_nic_fru_config
            for slot in pass_nic_list[:]:
                key = libmfg_utils.nic_key(slot)
                if not nic_fru_cfg[key]["VALID"]:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Failed to load current FRU")
                    mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)

            if "SCAN_VERIFY" not in args.skip_test:
                mtp_mgmt_ctrl.mtp_scan_verify(nic_fru_cfg, scanned_nic_fru_cfg, pass_nic_list, fail_nic_list, dsp)
            else:
                # only for QA, fake the scans
                mtp_mgmt_ctrl.mtp_populate_fru_to_scans(nic_fru_cfg, pass_nic_list, dpn=args.dpn)

        # validate the DPN is allowed for this PN
        test_list = ["DPN_VALIDATE"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)
        for slot in pass_nic_list[:]:
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type not in CTO_MODEL_TYPE_LIST:
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            for test in test_list:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)

                if test == "DPN_VALIDATE":
                    ret = mtp_mgmt_ctrl.mtp_nic_validate_pn_dpn_match(slot)

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

        for slot in pass_nic_list:
            sn = mtp_mgmt_ctrl.get_scanned_sn(slot)
            mac = mtp_mgmt_ctrl.get_scanned_mac(slot)
            pn = mtp_mgmt_ctrl.get_scanned_pn(slot)
            dpn = mtp_mgmt_ctrl.get_scanned_dpn(slot)
            prog_date = mtp_mgmt_ctrl.get_scanned_ts(slot)
            mac_ui = libmfg_utils.mac_address_format(mac)
            alom_sn = None
            alom_pn = None
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = mtp_mgmt_ctrl.get_scanned_alom_sn(slot)
                alom_pn = mtp_mgmt_ctrl.get_scanned_alom_pn(slot)

            riser_sn = None
            if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25OCP:
                riser_sn = mtp_mgmt_ctrl.mtp_get_nic_ocp_adapter_sn(slot)

            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

            print("")
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix:")
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = mtp_mgmt_ctrl.get_scanned_alom_sn(slot)
                alom_pn = mtp_mgmt_ctrl.get_scanned_alom_pn(slot)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}; SN_ALOM = {:s}; PN_ALOM = {:s}".format(sn, mac_ui, pn, alom_sn, alom_pn))
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}".format(sn, mac_ui, pn))
            if dpn:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "DPN = {:s}".format(dpn))
            if nic_type == NIC_Type.NAPLES25OCP:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "OCP Adapter SN = {:s}".format(riser_sn))

            dl_image_dict = image_control.get_all_images_for_stage(mtp_mgmt_ctrl, slot, dsp)
            for image_name, image_file_path in dl_image_dict.items():
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, image_name + " image: " + os.path.basename(image_file_path))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end")

        #identify adi ibm pass slot
        for slot in pass_nic_list:
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                adi_ibm_reset_slot.append(slot)

        for slot in pass_nic_list[:]:
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

        if len(adi_ibm_reset_slot) > 0 and not mtp_mgmt_ctrl.mtp_nic_diag_init(adi_ibm_reset_slot, emmc_format=True, emmc_check=True, fru_fpo=True, fru_valid=True if not args.scandl else False):
            mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)

        test_utils.update_pass_list(mtp_mgmt_ctrl, pass_nic_list, fail_nic_list)
        for slot in fail_nic_list:
            if slot in adi_ibm_reset_slot:
                adi_ibm_reset_slot.remove(slot)


        for slot in adi_ibm_reset_slot[:]:
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            test_list = []
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                test_list = ["NOSECURE_CPLD_PROG", "NOSECURE_FAILSAFE_CPLD_PROG", "SET_DIAGFW_BOOT"]
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
                failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
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


        for slot in pass_nic_list[:]:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)

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
                    if test == "CONSOLE_BOOT":
                        # rough way to track failure
                        mtp_mgmt_ctrl.mtp_set_nic_failed_boot(slot)
                    mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                    break
                else:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                       mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, dsp, test, duration))

        if "CONSOLE_BOOT" not in args.skip_test:
            mtp_mgmt_ctrl.mtp_power_cycle_nic(pass_nic_list, dl=True)

        for slot in pass_nic_list[:]:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            if nic_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
                mtp_exp_capability = 0x1
            elif nic_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
                mtp_exp_capability = 0x2
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")
                continue
            if not mtp_capability & mtp_exp_capability:
                mtp_mgmt_ctrl.cli_log_err("MTP doesn't support {:s}".format(nic_type))

            pre_check_testlist = ["NIC_POWER", "NIC_TYPE", "NIC_INIT", "NIC_DIAG_BOOT"]
            for skipped_test in args.skip_test:
                if skipped_test in pre_check_testlist:
                    pre_check_testlist.remove(skipped_test)
            for test in pre_check_testlist:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                # nic power status check
                if test == "NIC_POWER":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
                # nic type check
                elif test == "NIC_TYPE":
                    ret = mtp_mgmt_ctrl.mtp_nic_type_test(slot)
                # check nic init status
                elif test == "NIC_INIT":
                    ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
                # check if nic comes up from diagfw
                elif test == "NIC_DIAG_BOOT":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_diag_boot(slot)
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




        # program the qspi, before initializing emmc
        ## 1. setup mgmt
        if not mtp_mgmt_ctrl.mtp_nic_mgmt_para_init_fpo(pass_nic_list):
            mtp_mgmt_ctrl.cli_log_err("Initialize NIC MGMT failed", level=0)
        test_utils.update_pass_list(mtp_mgmt_ctrl, pass_nic_list, fail_nic_list)

        ## 2. program fw
        nic_thread_list = list()
        nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
        for slot in pass_nic_list[:]:
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_diagfw(mtp_mgmt_ctrl, slot, dsp)["filename"]
            qspi_gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_goldfw(mtp_mgmt_ctrl, slot, dsp)["filename"]
            uboot_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_uboot(mtp_mgmt_ctrl, slot, dsp)["filename"]
            uboota_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_uboota(mtp_mgmt_ctrl, slot, dsp)["filename"]
            ubootb_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_ubootb(mtp_mgmt_ctrl, slot, dsp)["filename"]
            uboot_installer_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.uboot_img["INSTALLER"]

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

        test_utils.update_pass_list(mtp_mgmt_ctrl, pass_nic_list, fail_nic_list, nic_test_rslt_list)

        ## 2b. set emmc settings for elba
        for slot in pass_nic_list[:]:
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)

            if nic_type not in PSLC_MODE_TYPE_LIST:
                continue

            testlist = ["SET_PSLC", "EMMC_HWRESET_SET", "EMMC_BKOPS_EN"]

            for skip_test in args.skip_test:
                if skip_test in testlist:
                    testlist.remove(skip_test)
            for test in testlist:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                if test == "SET_PSLC":
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

        if not mtp_mgmt_ctrl.mtp_nic_diag_init(pass_nic_list, emmc_format=True, emmc_check=True, fru_fpo=True, fru_valid=True if not args.scandl else False):
            mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        test_utils.update_pass_list(mtp_mgmt_ctrl, pass_nic_list, fail_nic_list)

        # 4. program the fru, cpld
        nic_thread_list = list()
        nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
        for slot in pass_nic_list[:]:
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
            failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
            fea_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fea_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]

            nic_thread = threading.Thread(target = single_nic_program, args = (mtp_mgmt_ctrl,
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

        test_utils.update_pass_list(mtp_mgmt_ctrl, pass_nic_list, fail_nic_list, nic_test_rslt_list)

        ## 5. flash asic esecure fw
        if not mtp_mgmt_ctrl.mtp_nic_esec_write_protect(pass_nic_list=pass_nic_list ,fail_nic_list=fail_nic_list ,enable=False, dsp=dsp):
            mtp_mgmt_ctrl.cli_log_err("Disable ESEC Write Protection failed", level=0)

        ## 6. verify everything
        # init nic diag env.
        if not mtp_mgmt_ctrl.mtp_nic_diag_init(pass_nic_list):
            mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        test_utils.update_pass_list(mtp_mgmt_ctrl, pass_nic_list, fail_nic_list)

        for slot in pass_nic_list[:]:
            # DL Verify process
            sn = mtp_mgmt_ctrl.get_scanned_sn(slot)
            mac = mtp_mgmt_ctrl.get_scanned_mac(slot)
            pn = mtp_mgmt_ctrl.get_scanned_pn(slot)
            dpn = mtp_mgmt_ctrl.get_scanned_dpn(slot)
            prog_date = mtp_mgmt_ctrl.get_scanned_ts(slot)
            exp_sn = sn
            exp_mac = "-".join(re.findall("..", mac))
            exp_pn = pn
            exp_dpn = dpn
            exp_date = prog_date
            alom_sn = None
            alom_pn = None
            exp_alom_sn = None
            exp_alom_pn = None
            exp_assettag = None
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = mtp_mgmt_ctrl.get_scanned_alom_sn(slot)
                alom_pn = mtp_mgmt_ctrl.get_scanned_alom_pn(slot)
                exp_alom_sn = alom_sn
                exp_alom_pn = alom_pn
                exp_assettag = 'C0'
                hpe_pn = "000000-000"

            testlist = ["NIC_POWER", "NIC_PRSNT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "DIAGFW_STORE", "AVS_SET"]
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25:
                testlist = ["NIC_POWER", "NIC_PRSNT", "NIC_DIAG_BOOT", "FRU_VERIFY", "REWORK_VERIFY", "CPLD_VERIFY", "DIAGFW_STORE", "AVS_SET"]
            elif nic_type == NIC_Type.NAPLES25SWM:
                testlist = ["NIC_POWER", "NIC_PRSNT", "NIC_DIAG_BOOT", "FRU_VERIFY", "REWORK_VERIFY", "CPLD_VERIFY", "DIAGFW_STORE", "AVS_SET"]
            elif nic_type in (NIC_Type.ORTANO2, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4):
                testlist = ["NIC_POWER", "NIC_PRSNT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "DIAGFW_STORE", "FEA_VERIFY", "L1_ESEC_PROG", "AVS_SET"]
            elif nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4):
                testlist = ["NIC_POWER", "NIC_PRSNT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "DIAGFW_STORE", "FEA_VERIFY", "L1_ESEC_PROG"]
            elif nic_type in FPGA_TYPE_LIST:
                testlist = ["NIC_POWER", "NIC_PRSNT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "DIAGFW_STORE", "FPGA_PROG_VERIFY", "L1_ESEC_PROG", "AVS_SET"]
            elif nic_type in ELBA_NIC_TYPE_LIST:
                testlist = ["NIC_POWER", "NIC_PRSNT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "DIAGFW_STORE", "L1_ESEC_PROG", "AVS_SET"]
            elif nic_type in GIGLIO_NIC_TYPE_LIST:
                testlist = ["NIC_POWER", "NIC_PRSNT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "DIAGFW_STORE", "FEA_VERIFY", "L1_ESEC_PROG", "AVS_SET"]
            for skip_test in args.skip_test:
                if skip_test in testlist:
                    testlist.remove(skip_test)

            for test in testlist:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                # nic power status check
                if test == "NIC_POWER":
                    ret = True
                    if nic_type != NIC_Type.NAPLES100IBM:
                        ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)    
                # nic present check
                elif test == "NIC_PRSNT":
                    ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
                elif test == "NIC_DIAG_BOOT":
                    ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
                # verify FRU
                elif test == "FRU_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_fru(slot, exp_sn, exp_mac, exp_pn, exp_date, exp_dpn)
                    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        if ret:
                            ret = mtp_mgmt_ctrl.mtp_verify_hpe_pn_fru(slot, hpe_pn)
                                                                        
                        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            if ret:
                                ret = mtp_mgmt_ctrl.mtp_verify_nic_alom_fru(slot, exp_alom_sn, exp_alom_pn, exp_date)
                elif test == "REWORK_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_nic_hpe_rework_verify(slot)
                # verify CPLD
                elif test == "CPLD_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)
                # verify FPGA against original file
                elif test == "FPGA_PROG_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_fpga(slot)
                # verify Feature Row
                elif test == "FEA_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld_fea(slot)
                elif test == "L1_ESEC_PROG":
                    ret = mtp_mgmt_ctrl.mtp_nic_l1_esecure_prog(slot)
                # set avs
                elif test == "AVS_SET":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_avs(slot)
                # keep an copy of diagfw in emmc, just incase we need recover it if mgmt fail and dongle is not available
                # not put DL results to fail even if the copy image to emmc failed.
                elif test == "DIAGFW_STORE":
                    mtp_mgmt_ctrl.mtp_copy_nic_copy_file(slot, qspi_img_file)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                    continue

                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
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
                    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, dsp, test, duration))

        if MTP_HEALTH_MONITOR:
            mtp_mgmt_ctrl.get_mtp_health_monitor().set_event_status()
            thread_health.join()

        # power off nic
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.cli_log_inf("MTP DL Test Complete", level=0)

        for slot in pass_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

        for slot in fail_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

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

