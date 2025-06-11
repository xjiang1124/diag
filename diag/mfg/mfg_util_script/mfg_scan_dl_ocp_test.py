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
from libmfg_cfg import *
from libsku_utils import *
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode

def mynotes():
    """
    dl_barcode.yaml
    MTP-001:
        NIC-01:
            SN: ABC
            MAC: FFFFFFFFFFFF
            PN: 00-0000-00 00
            TS: 123456
            VALID: Yes
        NIC-02:
            SN: ABC
            MAC: FFFFFFFFFFFF
            PN: 00-0000-00 00
            TS: 123456
            VALID: Yes



    scanned_list = dict()
    scanned_list = dict()
    scanned_list[key] = dict()
    scanned_list[key]["SN"] = "ABC"
    scanned_list[key]["MAC"] = "FFFFFFFFFFFF"
    scanned_list[key]["PN"] = "00-0000-00 00"
    scanned_list[key]["TS"] = "220199"
    scanned_list[key]["VALID"] = True

    Please scan MTP ID barcode: 
    [MTP-001] Please scan NIC ID barcode: 
    [MTP-001] [NIC-01] Please scan Adapter Serial Number barcode: 
    [MTP-001] Please scan next NIC ID barcode or enter STOP: 
    Please scan next MTP ID or enter STOP: 

    """
    pass

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

def ocp_adapter_barcode_scan(mtp_mgmt_ctrl, present_check=True, swmtestmode=Swm_Test_Mode.SWMALOM, no_slot=False):
    mtp_scan_rslt = dict()
    mtp_ts_snapshot = libmfg_utils.get_timestamp()
    mtp_scan_rslt["MTP_ID"] = mtp_mgmt_ctrl._id
    mtp_scan_rslt["MTP_TS"] = mtp_ts_snapshot
    valid_nic_key_list = list()

    unscanned_nic_key_list = list()
    scan_nic_key_list = list()
    scan_sn_list = list()
    scan_mac_list = list()
    scan_atom_sn_list = list()
    slot_num = 1

    # build all valid nic key list
    for slot in range(mtp_mgmt_ctrl._slots):
        key = libmfg_utils.nic_key(slot)
        valid_nic_key_list.append(key)
        if present_check and mtp_mgmt_ctrl._nic_prsnt_list[slot]:
            unscanned_nic_key_list.append(key)

    while True:
        if present_check:
            unscanned_nic_list_cli_str = ", ".join(unscanned_nic_key_list)
            usr_prompt = "\nUnscanned NIC list [{:s}]\nPlease Scan NIC ID Barcode:".format(unscanned_nic_list_cli_str)
        else:
            usr_prompt = "\nPlease Scan NIC ID Barcode:"
        nic_scan_rslt = dict()
        if not no_slot:
            raw_scan = raw_input(usr_prompt)

        if raw_scan == "STOP":
            if present_check and len(unscanned_nic_key_list) != 0:
                mtp_mgmt_ctrl.cli_log_err("{:s} have not scanned yet".format(unscanned_nic_list_cli_str), level=0)
                continue
            else:
                break
        elif no_slot:
            key = "NIC-{:>02d}".format(slot_num)
            slot_num =+ 1
            scan_nic_key_list.append(key)
            unscanned_nic_key_list.remove(key)
        elif raw_scan in scan_nic_key_list:
            mtp_mgmt_ctrl.cli_log_err("NIC ID Barcode: {:s} is double scanned, please restart the scan process\n".format(raw_scan), level=0)
            return None
        else:
            key = raw_scan
            # basic sanity check
            if present_check:
                if key not in unscanned_nic_key_list:
                    mtp_mgmt_ctrl.cli_log_err("Invalid NIC ID: {:s}".format(key), level=0)
                    continue
                else:
                    scan_nic_key_list.append(key)
                    unscanned_nic_key_list.remove(key)
            else:
                if key not in valid_nic_key_list:
                    mtp_mgmt_ctrl.cli_log_err("Invalid NIC ID: {:s}".format(key), level=0)
                    continue
                else:
                    scan_nic_key_list.append(key)

        #Scan SN loop
        sn = "0"
        mac = "000000000000"
        pn = "0"
        if swmtestmode != Swm_Test_Mode.ALOM:
            sn_scanned = False
            mac_scanned = True
            pn_scanned = True
            while not sn_scanned:
                usr_prompt = "Please Scan {:s} Serial Number Barcode:".format(key)
                raw_scan = raw_input(usr_prompt)
                if raw_scan == "STOP":
                    break
                if libmfg_utils.dell_ppid_validate(raw_scan):
                    # Dell PPID
                    sn = libmfg_utils.extract_sn_from_dell_ppid(raw_scan)
                    pn = libmfg_utils.extract_pn_from_dell_ppid(raw_scan)
                    pn_scanned = True
                else:
                    sn = libmfg_utils.serial_number_validate(raw_scan)
                if not sn:
                    mtp_mgmt_ctrl.cli_log_err("Invalid NIC Serial Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                    #return None
                elif sn in scan_sn_list:
                    mtp_mgmt_ctrl.cli_log_err("NIC Serial Number: {:s} is double scanned, please restart the scan process\n".format(sn), level=0)
                    #return None
                else:
                    scan_sn_list.append(sn)
                    sn_scanned = True

                if pn_scanned and not pn:
                    pn_scanned = False

            mac = OCP_ADAPTER_FIXED_MAC
            pn = OCP_ADAPTER_FIXED_PN

            #Scan ALOM SN Loop
            alom_sn = None
            alom_pn = None


        if swmtestmode == Swm_Test_Mode.ALOM:  #if only scanning Alom we need to manually put in the SWM part number
            pn="000000-000"

        if pn == '000000-000':
            while True:
                usr_prompt = "Please Scan {:s} ALOM Serial Number Barcode:".format(key)
                raw_scan = raw_input(usr_prompt)
                alom_sn = libmfg_utils.serial_number_validate(raw_scan)
                if not alom_sn:
                    mtp_mgmt_ctrl.cli_log_err("Invalid ALOM Serial Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                #return None
                elif alom_sn in scan_atom_sn_list:
                    mtp_mgmt_ctrl.cli_log_err("ALOM Serial Number: {:s} is double scanned, please restart the scan process\n".format(sn), level=0)
                #return None
                else:
                    scan_atom_sn_list.append(alom_sn)
                    break
            #Scan ALOM PN Loop
            
            while True:
                usr_prompt = "Please scan {:s} ALOM Part Number Barcode:".format(key)
                raw_scan = raw_input(usr_prompt)
                alom_pn = libmfg_utils.part_number_validate(raw_scan)
                if not alom_pn:
                    mtp_mgmt_ctrl.cli_log_err("Invalid ALOM Part Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                #return None
                else:
                    break

        nic_scan_rslt["VALID"] = True
        nic_scan_rslt["SN"] = sn
        nic_scan_rslt["MAC"] = mac
        nic_scan_rslt["PN"] = pn
        nic_scan_rslt["TS"] = libmfg_utils.get_fru_date()
        if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
            nic_scan_rslt["SN_ALOM"] = alom_sn
            nic_scan_rslt["PN_ALOM"] = alom_pn
        mtp_scan_rslt[key] = nic_scan_rslt

    nic_empty_list = list(set(valid_nic_key_list).difference(set(scan_nic_key_list)))
    for key in nic_empty_list:
        nic_scan_rslt = dict()
        nic_scan_rslt["VALID"] = False
        mtp_scan_rslt[key] = nic_scan_rslt

    return mtp_scan_rslt

def main():
    parser = argparse.ArgumentParser(description="MFG DL Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test section", nargs="*", default=[])

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db)
    mtp_id = mtpid_list[0]

    # local log files
    log_file_list = list()
    log_filep_list = list()
    log_dir = "log/"
    log_timestamp = libmfg_utils.get_timestamp()
    log_sub_dir = MTP_DIAG_Logfile.MFG_DL_LOG_DIR.format(mtp_id, log_timestamp)
    os.system(MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(log_dir + log_sub_dir))
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
        scan_rslt = ocp_adapter_barcode_scan(mtp_mgmt_ctrl, False, swmtestmode)
        if scan_rslt:
            break;
        mtp_mgmt_ctrl.cli_log_inf("Restart the Barcode Scan Process", level=0)

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

    if not libmfg_utils.mtp_common_setup_fpo(mtp_mgmt_ctrl, FF_Stage.FF_DL, args.skip_test):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
        logfile_close(log_filep_list)
        return

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

            valid = nic_fru_cfg[key]["VALID"]
            if not valid:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "NIC present but not scanned")
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                continue

    mtp_mgmt_ctrl.cli_log_inf("Program Process Started", level=0)
    mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[key]["VALID"]
        if not valid:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot")
            continue
        sn = nic_fru_cfg[key]["SN"]
        mac = nic_fru_cfg[key]["MAC"]
        pn = nic_fru_cfg[key]["PN"]
        mac_ui = libmfg_utils.mac_address_format(mac)
        if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = nic_fru_cfg[key]["SN_ALOM"]
            alom_pn = nic_fru_cfg[key]["PN_ALOM"]

        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

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
            alom_sn = nic_fru_cfg[key]["SN_ALOM"]
            alom_pn = nic_fru_cfg[key]["PN_ALOM"]
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}; SN_ALOM = {:s}; PN_ALOM = {:s}".format(sn, mac_ui, pn, alom_sn, alom_pn))
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}".format(sn, mac_ui, pn))

        if slot not in pass_nic_list:
            pass_nic_list.append(slot)

        # DL precheck
        pre_check_testlist = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT"]
        for skipped_test in args.skip_test:
            if skipped_test in pre_check_testlist:
                pre_check_testlist.remove(skipped_test)
        for test in pre_check_testlist:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            if test == "NIC_POWER":
                ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot, test)
            elif test == "NIC_PRSNT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
            elif test == "NIC_INIT":
                ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
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
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot, testname=test)
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
        valid = nic_fru_cfg[key]["VALID"]
        if not valid:
            continue


        sn = nic_fru_cfg[key]["SN"]
        mac = nic_fru_cfg[key]["MAC"]
        pn = nic_fru_cfg[key]["PN"]
        prog_date = str(nic_fru_cfg[key]["TS"])

        test_list = [""]
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25OCP:
            test_list = ["ADAP_FRU_PROG", "ADAP_FRU_INIT", "ADAP_FRU_VERIFY"]

        dsp = FF_Stage.FF_DL

        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)
        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            # write
            if test == "ADAP_FRU_PROG":
                ret = mtp_mgmt_ctrl.mtp_nic_program_ocp_adapter_fru(slot, prog_date, sn, mac, pn)
            # read
            elif test == "ADAP_FRU_INIT":
                ret = mtp_mgmt_ctrl.mtp_nic_ocp_adapter_fru_init(slot)
            # verify
            elif test == "ADAP_FRU_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_nic_verify_ocp_adapter_fru(slot, prog_date, sn, mac, pn)
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot, testname=test)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

    mtp_mgmt_ctrl.cli_log_inf("Program Process Complete", level=0)
    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.mtp_chassis_shutdown()
    mfg_dl_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP DL Test Duration:{:s}".format(mfg_dl_stop_ts - mfg_dl_start_ts))

    for slot in pass_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = nic_fru_cfg[key]["SN"]
        if not swmtestmode == Swm_Test_Mode.ALOM:
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
        
    for slot in fail_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        valid = nic_fru_cfg[key]["VALID"]
        if not valid:
            sn = None
        else:
            sn = nic_fru_cfg[key]["SN"]
        if not swmtestmode == Swm_Test_Mode.ALOM:
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
    logfile_close(log_filep_list)

    # pkg the logfile
    log_pkg_file = MTP_DIAG_Logfile.MFG_DL_LOG_PKG_FILE.format(mtp_id, log_timestamp)
    os.system(MFG_DIAG_CMDS().MFG_LOG_PKG_FMT.format(log_dir+log_pkg_file, log_dir, log_sub_dir))

    # move the logs to the log root dir
    log_hard_copy_flag = True
    log_relative_link = None
    for slot in fail_nic_list + pass_nic_list:
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[key]["VALID"]
        if not valid:
            sn = None
        else:
            sn = nic_fru_cfg[key]["SN"]
        if not sn:
            continue
        if GLB_CFG_MFG_TEST_MODE:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_DL_LOG_DIR_FMT.format(nic_type, sn)
        else:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_DL_LOG_DIR_FMT.format(nic_type, sn)
        os.system(MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(mfg_log_dir))
        if log_hard_copy_flag:
            libmfg_utils.cli_inf("[{:s}] Collecting log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
            os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))
            log_relative_link = "../{:s}/{:s}".format(sn, os.path.basename(log_pkg_file))
            log_hard_copy_flag = False
        else:
            libmfg_utils.cli_inf("[{:s}] Create link log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
            chdir_cmd = "cd {:s}".format(mfg_log_dir)
            ln_cmd = MFG_DIAG_CMDS().MFG_LOG_LINK_FMT.format(log_relative_link, os.path.basename(log_pkg_file))
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
            os.system(MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(mfg_log_dir))
            if log_hard_copy_flag:
                libmfg_utils.cli_inf("[{:s}] Collecting log file {:s}".format(alom_sn, log_pkg_file))
                os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))
                log_relative_link = "../{:s}/{:s}".format(alom_sn, os.path.basename(log_pkg_file))
                log_hard_copy_flag = False
            else:
                libmfg_utils.cli_inf("[{:s}] Create link log file {:s}".format(alom_sn, log_relative_link))
                chdir_cmd = "cd {:s}".format(mfg_log_dir)
                ln_cmd = MFG_DIAG_CMDS().MFG_LOG_LINK_FMT.format(log_relative_link, os.path.basename(log_pkg_file))
                cmd = "{:s} && {:s}".format(chdir_cmd, ln_cmd)
                os.system(cmd)            

    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mfg_dl_start_ts, mfg_dl_stop_ts, test_log_file, FF_Stage.FF_DL)

    # cleanup the log dir
    logfile_cleanup([log_dir+log_sub_dir, log_dir+log_pkg_file])

    return

if __name__ == "__main__":
    main()
