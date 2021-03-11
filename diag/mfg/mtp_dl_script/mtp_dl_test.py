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
from libdefs import FF_Stage
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


def single_nic_fw_program(mtp_mgmt_ctrl, fru_cfg, cpld_img_file, qspi_img_file, slot, swmtestmode, skip_testlist, nic_test_rslt_list):
    sn = fru_cfg["SN"]
    mac = fru_cfg["MAC"]
    pn = fru_cfg["PN"]
    prog_date = str(fru_cfg["TS"])

    dsp = FF_Stage.FF_DL
    testseqlist = ["FRU_PROG", "CPLD_PROG", "QSPI_PROG", "CPLD_REF"]                                                                
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.NAPLES25OCP:
        testseqlist = ["FRU_PROG", "QSPI_PROG", "CPLD_PROG"]
    if nic_type == NIC_Type.NAPLES25SWM:
        testseqlist = ["FRU_PROG", "QSPI_PROG", "CPLD_PROG", "CPLD_REF"]
    if nic_type == NIC_Type.ORTANO:
        testseqlist = ["FRU_PROG", "QSPI_PROG", "CPLD_PROG", "CPLD_REF", "NIC_PWRCYC"]
    if nic_type == NIC_Type.NAPLES25 or nic_type == NIC_Type.NAPLES25SWM:
        ### REWORK VERIFICATION FOR CAP CHANGE ###
        ### PERFORM AFTER FRU_VERIFY ###
        testseqlist.insert(1, "REWORK_VERIFY")
    for skip_test in skip_testlist:
        if skip_test in testseqlist:
            testseqlist.remove(skip_test)
    for test in testseqlist:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        # program FRU
        if test == "FRU_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            #skip ALOM programming if Naples25 SWM test mode is SWM only
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:  
                alom_sn = fru_cfg["SN_ALOM"]
                alom_pn = fru_cfg["PN_ALOM"] 
                ret = mtp_mgmt_ctrl.mtp_program_nic_alom_fru(slot, prog_date, alom_sn, alom_pn)
        elif test == "REWORK_VERIFY":
            ### REWORK VERIFICATION FOR CAP CHANGE ###
            ### For NAPLES25(HPE) and NAPLES25SWM(HPE), Product Version/Revision Code must be 0B or 0x30 0x42 ###
            nic_fru_info = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_fru()
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            nic_vendor = nic_fru_info[4]
            if nic_type == NIC_Type.NAPLES25 and nic_vendor == NIC_Vendor.HPE:
                arm_fru = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_info(MFG_DIAG_CMDS.NIC_HP_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH))
                if not arm_fru:
                    mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "REWORK VERIFICATION: command didn't work: {}".format(arm_fru))
                    ret1 = False
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
                    ret1 = False
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
            ret = ret1 and ret2
        # program CPLD
        elif test == "CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
        # program QSPI
        elif test == "QSPI_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_qspi(slot, qspi_img_file)
        # refresh CPLD
        elif test == "CPLD_REF":
            ret = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(slot)
        # extra powercycle to refresh CPLD
        elif test == "NIC_PWRCYC":
            ret = mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
            ret &= mtp_mgmt_ctrl.mtp_power_on_single_nic(slot)
            #ret &= mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)
            # CPLD_VERIFY test is done later. Any quick way to verify that powercycle worked?
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
            continue
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            nic_test_rslt_list[slot] = False
            mtp_mgmt_ctrl.mtp_dump_err_msg(mtp_mgmt_ctrl.mtp_get_nic_err_msg(slot))
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

def set_pslc(mtp_mgmt_ctrl,mtp_id):
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if not (card_type == NIC_Type.VOMERO2 or card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2):
            continue
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, 'Set NIC pSLC mode')
        
        start_ts = libmfg_utils.timestamp_snapshot()        
        ret = mtp_mgmt_ctrl.mtp_setting_partition(slot)
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, 'Set NIC pSLC mode FAILED')
            return False
        else:
            mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, 'Set NIC pSLC mode complete')
    mtp_mgmt_ctrl.mtp_power_on_nic()
    return True

def main():
    parser = argparse.ArgumentParser(description="MTP DL Test Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid

    mtp_cfg_db = load_mtp_cfg()

    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    if not args.skip_test:
        args.skip_test = []

    # local log files
    log_filep_list = list()
    test_log_file = "test_dl.log"
    test_log_filep = open(test_log_file, "w+", buffering=0)
    log_filep_list.append(test_log_filep)

    diag_log_file = "diag_dl.log"
    diag_log_filep = open(diag_log_file, "w+", buffering=0)
    log_filep_list.append(diag_log_filep)

    fru_cfg_file = "dl_barcode.yaml"

    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = "diag_{:s}_dl.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, "w+", buffering=0)
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list)

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)


    if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, stage=FF_Stage.FF_DL):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
        logfile_close(log_filep_list)
        return

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)
    mtp_mgmt_ctrl.mtp_power_cycle_nic()
       
    # init the nic diag environment
    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if nic_prsnt_list[slot]:
            if not mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(slot):
                continue

    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    # if applicable, set pslc mode and powercycle
    mtp_mgmt_ctrl.mtp_nic_mgmt_seq_init(fpo=True)
    if not mtp_mgmt_ctrl.mtp_mgmt_nic_mac_validate():
        mtp_mgmt_ctrl.cli_log_err("No connection to NICs", level=0)
        return False
    if not set_pslc(mtp_mgmt_ctrl,mtp_id):
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return
    
    rc = mtp_mgmt_ctrl.mtp_nic_diag_init(emmc_format=True)
    if not rc:
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    dsp = FF_Stage.FF_DL
    # construct nic fru config file
    tmp_fru_cfg = dict()
    tmp_fru_cfg["MTP_ID"] = mtp_id
    tmp_fru_cfg["MTP_TS"] = libmfg_utils.get_timestamp()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        tmp_fru_cfg[key] = dict()
        if mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot):
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            tmp_fru_cfg[key]["NIC_VALID"] = True
            tmp_fru_cfg[key]["NIC_TS"] = libmfg_utils.get_fru_date()
            if mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                    nic_fru_info = mtp_mgmt_ctrl.mtp_get_nic_fru(slot)
                    if nic_fru_info:
                        tmp_fru_cfg[key]["NIC_SN"] = nic_fru_info[0]
                        tmp_fru_cfg[key]["NIC_MAC"] = nic_fru_info[1].replace('-', '')
                        tmp_fru_cfg[key]["NIC_PN"] = nic_fru_info[2]
                        if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            nic_fru_info = mtp_mgmt_ctrl.mtp_get_nic_alom_fru(slot)
                            tmp_fru_cfg[key]["SN_ALOM"] = nic_fru_info[0]
                            tmp_fru_cfg[key]["PN_ALOM"] = nic_fru_info[1]
                    else:
                        tmp_fru_cfg[key]["NIC_SN"] = "DEADBEEF"
                        tmp_fru_cfg[key]["NIC_MAC"] = "DEADBEEF"
                        tmp_fru_cfg[key]["NIC_PN"] = "DEADBEEF"
                        if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            tmp_fru_cfg[key]["SN_ALOM"] = "DEADBEEF"
                            tmp_fru_cfg[key]["PN_ALOM"] = "DEADBEEF"
            else:
                    tmp_fru_cfg[key]["NIC_SN"] = "DEADBEEF"
                    tmp_fru_cfg[key]["NIC_MAC"] = "DEADBEEF"
                    tmp_fru_cfg[key]["NIC_PN"] = "DEADBEEF"
                    if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        tmp_fru_cfg[key]["SN_ALOM"] = "DEADBEEF"
                        tmp_fru_cfg[key]["PN_ALOM"] = "DEADBEEF"
        else:
            tmp_fru_cfg[key]["NIC_VALID"] = False

    fru_cfg_filep = open(fru_cfg_file, "w+")
    mtp_mgmt_ctrl.gen_barcode_config_file(fru_cfg_filep, tmp_fru_cfg)
    fru_cfg_filep.close()
    # reload the barcode config file
    nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(fru_cfg_file)

    mtp_mgmt_ctrl.cli_log_inf("MTP DL Test Started", level=0)

    fail_nic_list = list()
    pass_nic_list = list()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot")
            continue

        sn = nic_fru_cfg[mtp_id][key]["SN"]
        mac = nic_fru_cfg[mtp_id][key]["MAC"]
        pn = nic_fru_cfg[mtp_id][key]["PN"]
        prog_date = str(nic_fru_cfg[mtp_id][key]["TS"])
        mac_ui = libmfg_utils.mac_address_format(mac)
        alom_sn = None
        alom_pn = None
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
           if "SN_ALOM" in nic_fru_cfg[mtp_id][key]:
               alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
               alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]

        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[card_type]
        qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img[card_type]

        if card_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
            mtp_exp_capability = 0x1
        elif card_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
            mtp_exp_capability = 0x2
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")
            continue
        if not mtp_capability & mtp_exp_capability:
            mtp_mgmt_ctrl.cli_log_err("MTP doesn't support {:s}".format(card_type))
            mtp_mgmt_ctrl.mtp_chassis_shutdown()
            logfile_close(log_filep_list)
            return

        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix:")
        if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
            alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}; SN_ALOM = {:s}; PN_ALOM = {:s}".format(sn, mac_ui, pn, alom_sn, alom_pn))
        if card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}".format(sn, mac_ui, pn))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD image1: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD image2: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI image: " + os.path.basename(qspi_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end\n")
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}".format(sn, mac_ui, pn))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD image: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI image: " + os.path.basename(qspi_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end\n")

        pass_nic_list.append(slot)
        pre_check_testlist = ["NIC_POWER", "NIC_TYPE", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT"]
        for skipped_test in args.skip_test:
            if skipped_test in pre_check_testlist:
                pre_check_testlist.remove(skipped_test)
        for test in pre_check_testlist:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            # nic power status check
            if test == "NIC_POWER":
                ret = True
                if card_type != NIC_Type.NAPLES100IBM:
                    ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
            # nic type check
            elif test == "NIC_TYPE":
                ret = mtp_mgmt_ctrl.mtp_nic_type_valid(slot)
            # nic present check
            elif test == "NIC_PRSNT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
            # check nic init status
            elif test == "NIC_INIT":
                ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
            # check if nic comes up from diagfw
            elif test == "NIC_DIAG_BOOT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                continue
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


    # program the NIC firmware
    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue

        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.diagfw_img[card_type]
        cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[card_type]

        nic_thread = threading.Thread(target = single_nic_fw_program, args = (mtp_mgmt_ctrl,
                                                                              nic_fru_cfg[mtp_id][key],
                                                                              cpld_img_file,
                                                                              qspi_img_file,
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
            fail_nic_list.append(slot)
            pass_nic_list.remove(slot)

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()
    # init nic diag env.
    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return
    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot")
            continue

        # DL Verify process
        sn = nic_fru_cfg[mtp_id][key]["SN"]
        mac = nic_fru_cfg[mtp_id][key]["MAC"]
        pn = nic_fru_cfg[mtp_id][key]["PN"]
        prog_date = str(nic_fru_cfg[mtp_id][key]["TS"])
        exp_sn = sn
        exp_mac = "-".join(re.findall("..", mac))
        exp_pn = pn
        exp_date = prog_date
        alom_sn = None
        alom_pn = None
        exp_alom_sn = None
        exp_alom_pn = None
        exp_assettag = None
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
            alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]
            exp_alom_sn = alom_sn
            exp_alom_pn = alom_pn
            exp_assettag = 'C0'
            hpe_pn = "000000-000"

        #for test in ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "FRU_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY", "AVS_SET", "PCIE_DIS"]:
        testlists = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY", "AVS_SET"]
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM:
            testlists = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY", "AVS_SET"]
        if card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2:
            testlists = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY"]
        for skip_test in args.skip_test:
            if skip_test in testlists:
                testlists.remove(skip_test)
        for test in testlists:
        
        
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            # nic power status check
            if test == "NIC_POWER":
                ret = True
                if card_type != NIC_Type.NAPLES100IBM:
                    ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)    
            # nic present check
            elif test == "NIC_PRSNT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
            # nic status check
            elif test == "NIC_INIT":
                ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
            elif test == "NIC_DIAG_BOOT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
            # verify FRU
            elif test == "FRU_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_fru(slot, exp_sn, exp_mac, exp_pn, exp_date)
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    if ret:
                        ret = mtp_mgmt_ctrl.mtp_verify_hpe_pn_fru(slot, hpe_pn)
                                                                    
                    if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        if ret:
                            ret = mtp_mgmt_ctrl.mtp_verify_nic_alom_fru(slot, exp_alom_sn, exp_alom_pn, exp_date)
            # verify CPLD
            elif test == "CPLD_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)
            # verify QSPI
            elif test == "QSPI_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_qspi(slot)
            # set avs
            elif test == "AVS_SET":
                ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_avs(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                continue
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, dsp, test, duration))

    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.cli_log_inf("MTP DL Test Complete", level=0)

    for slot in pass_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

    for slot in fail_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    logfile_close(log_filep_list)
    return


if __name__ == "__main__":
    main()

