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
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
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
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg)
    return mtp_mgmt_ctrl


def single_nic_fw_program(mtp_mgmt_ctrl, fru_cfg, cpld_img_file, qspi_img_file, slot, fail_nic_list, pass_nic_list, swmtestmode):
    sn = fru_cfg["SN"]
    mac = fru_cfg["MAC"]
    pn = fru_cfg["PN"]
    prog_date = str(fru_cfg["TS"])
    test_list = ["FRU_PROG", "CPLD_PROG", "QSPI_PROG", "CPLD_REF"]
    
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.NAPLES25SWM:
        test_list = ["FRU_PROG", "QSPI_PROG", "CPLD_PROG", "CPLD_REF"]
    if (nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM):  #If SWM and only asking for ALOM, skip SWM FRU PROGRAMMING
        test_list = ["FRU_PROG"]

    if nic_type == NIC_Type.ORTANO:
        test_list = ["FRU_PROG", "CPLD_PROG", "QSPI_PROG", "CPLD_REF", "NIC_PWRCYC"]
    dsp = FF_Stage.FF_DL

    for test in test_list:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        # program FRU
        if test == "FRU_PROG":
            if not (nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM):  #If SWM and only asking for ALOM, skip SWM FRU PROGRAMMING
                ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn)
            if pn == '000000-000':
                alom_sn = fru_cfg["SN_ALOM"]
                alom_pn = fru_cfg["PN_ALOM"] 
                ret = mtp_mgmt_ctrl.mtp_program_nic_alom_fru(slot, prog_date, alom_sn, alom_pn)
                #ret = False
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
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
            continue
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
            fail_nic_list.append(slot)
            pass_nic_list.remove(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, dsp, test, duration))


def set_pslc(mtp_mgmt_ctrl,nic_fru_cfg,mtp_id,fail_nic_list,pass_nic_list):
    
    dsp = FF_Stage.FF_DL

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            continue    #NEXT
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            continue
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if not (card_type == NIC_Type.VOMERO2 or card_type == NIC_Type.ORTANO):
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
            pass_nic_list.remove(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, 'SET_PSLC', duration))
    return 0
def main():
    parser = argparse.ArgumentParser(description="MFG DL Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))

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
    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir + log_sub_dir))
    test_log_file = log_dir + log_sub_dir + "test_dl.log"
    log_file_list.append(test_log_file)
    test_log_filep = open(test_log_file, "w+", buffering=0)
    log_filep_list.append(test_log_filep)

    if verbosity:
        diag_log_filep = sys.stdout
    else:
        diag_log_file = log_dir + log_sub_dir + "diag_dl.log"
        log_file_list.append(diag_log_file)
        diag_log_filep = open(diag_log_file, "w+", buffering=0)
        log_filep_list.append(diag_log_filep)

    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = log_dir + log_sub_dir + "diag_{:s}_dl.log".format(key)
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

    # print scan summary
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        nic_cli_id_str = libmfg_utils.id_str(mtp = mtp_id, nic = slot)
        if scan_rslt[key]["NIC_VALID"]:
            sn = scan_rslt[key]["NIC_SN"]
            pn = scan_rslt[key]["NIC_PN"]
            mac_ui = libmfg_utils.mac_address_format(scan_rslt[key]["NIC_MAC"])
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

    scan_cfg_file = log_dir + log_sub_dir + "dl_barcode.yaml"
    scan_cfg_filep = open(scan_cfg_file, "w+")
    mtp_mgmt_ctrl.gen_barcode_config_file(scan_cfg_filep, scan_rslt)
    scan_cfg_filep.close()
    log_file_list.append(scan_cfg_file)

    # reload the barcode config file
    nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(scan_cfg_file)
    pass_nic_list = list()
    fail_nic_list = list()

    # get the absolute file path
    naples100_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES100_CPLD_IMAGE
    naples100_qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE
    naples100ibm_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES100IBM_CPLD_IMAGE
    naples100ibm_qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE
    naples100hpe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES100HPE_CPLD_IMAGE
    naples100hpe_qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_HPE_NAPLES100
    naples25_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES25_CPLD_IMAGE
    naples25_qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE
    vomero_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.VOMERO_CPLD_IMAGE
    vomero_qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE
    vomero2_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.VOMERO2_CPLD_IMAGE
    vomero2_qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_VOMERO2
    naples25swm_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES25SWM_CPLD_IMAGE
    naples25swm_qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE
    naples25ocp_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES25_HPE_OCP_CPLD_IMAGE
    naples25ocp_qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_HPE_OCP
    naples25swmdell_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES25SWMDELL_CPLD_IMAGE
    naples25swmdell_qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_SWMDELL
    ortano_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.ORTANO_CPLD_IMAGE
    ortano_qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_ORTANO

    mtp_mgmt_ctrl.mtp_apc_pwr_on()
    mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)
    # Check if image update is needed
    mtp_dl_image_list = list()
    mtp_dl_image_list.append(MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE)
    mtp_dl_image_list.append(MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_HPE_NAPLES100)
    mtp_dl_image_list.append(MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_NAPLES100)
    mtp_dl_image_list.append(MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_VOMERO2)
    mtp_dl_image_list.append(MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_SWMDELL)
    mtp_dl_image_list.append(MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_HPE_OCP)
    mtp_dl_image_list.append(MFG_IMAGE_FILES.NIC_DIAGFW_IMAGE_ORTANO)
    if (mtp_capability & 0x1):
        # FIXME: Xin - Dedicated image
        mtp_dl_image_list.append(MFG_IMAGE_FILES.NAPLES100_CPLD_IMAGE)
        mtp_dl_image_list.append(MFG_IMAGE_FILES.NAPLES100IBM_CPLD_IMAGE)
        mtp_dl_image_list.append(MFG_IMAGE_FILES.NAPLES100HPE_CPLD_IMAGE)
        mtp_dl_image_list.append(MFG_IMAGE_FILES.VOMERO_CPLD_IMAGE)
        mtp_dl_image_list.append(MFG_IMAGE_FILES.VOMERO2_CPLD_IMAGE)
        mtp_dl_image_list.append(MFG_IMAGE_FILES.ORTANO_CPLD_IMAGE)
    if (mtp_capability & 0x2):
        # FIXME: Xin - Dedicated image
        mtp_dl_image_list.append(MFG_IMAGE_FILES.NAPLES25_CPLD_IMAGE)
        mtp_dl_image_list.append(MFG_IMAGE_FILES.NAPLES25SWM_CPLD_IMAGE)    
        mtp_dl_image_list.append(MFG_IMAGE_FILES.NAPLES25_HPE_OCP_CPLD_IMAGE)
        mtp_dl_image_list.append(MFG_IMAGE_FILES.NAPLES25SWMDELL_CPLD_IMAGE)
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
    # init the nic diag environment
    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if nic_prsnt_list[slot]:
            if not mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(slot):
                continue
    
    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    # init nic diag env.
    rc = mtp_mgmt_ctrl.mtp_nic_diag_init(emmc_format=True, fru_valid=False, sn_tag=True, fru_cfg=nic_fru_cfg)
    if not rc:
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Started", level=0)
    mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

    dsp = FF_Stage.FF_DL
    pass_nic_list = list()
    fail_nic_list = list()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) != "YES":
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot\n")
            continue
        sn = nic_fru_cfg[mtp_id][key]["SN"]
        mac = nic_fru_cfg[mtp_id][key]["MAC"]
        pn = nic_fru_cfg[mtp_id][key]["PN"]
        mac_ui = libmfg_utils.mac_address_format(mac)
        if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
            alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]

        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES100 or card_type == NIC_Type.FORIO:
            mtp_exp_capability = 0x1
            cpld_img_file = naples100_cpld_img_file
            qspi_img_file = naples100_qspi_img_file
        elif card_type == NIC_Type.VOMERO:
            mtp_exp_capability = 0x1
            cpld_img_file = vomero_cpld_img_file
            qspi_img_file = vomero_qspi_img_file
        elif card_type == NIC_Type.NAPLES100IBM:
            mtp_exp_capability = 0x1
            cpld_img_file = naples100ibm_cpld_img_file
            qspi_img_file = naples100ibm_qspi_img_file
        elif card_type == NIC_Type.NAPLES100HPE:
            mtp_exp_capability = 0x1
            cpld_img_file = naples100hpe_cpld_img_file
            qspi_img_file = naples100hpe_qspi_img_file
        elif card_type == NIC_Type.VOMERO2:
            mtp_exp_capability = 0x1
            cpld_img_file = vomero2_cpld_img_file
            qspi_img_file = vomero2_qspi_img_file
        elif card_type == NIC_Type.ORTANO:
            mtp_exp_capability = 0x1
            cpld_img_file = ortano_cpld_img_file
            qspi_img_file = ortano_qspi_img_file
        elif card_type == NIC_Type.NAPLES25:
            mtp_exp_capability = 0x2
            cpld_img_file = naples25_cpld_img_file
            qspi_img_file = naples25_qspi_img_file
        elif card_type == NIC_Type.NAPLES25SWM:
            mtp_exp_capability = 0x2
            cpld_img_file = naples25swm_cpld_img_file
            qspi_img_file = naples25swm_qspi_img_file
        elif card_type == NIC_Type.NAPLES25OCP:
            mtp_exp_capability = 0x2
            cpld_img_file = naples25ocp_cpld_img_file
            qspi_img_file = naples25ocp_qspi_img_file
        elif card_type == NIC_Type.NAPLES25SWMDELL:
            mtp_exp_capability = 0x2
            cpld_img_file = naples25swmdell_cpld_img_file
            qspi_img_file = naples25swmdell_qspi_img_file
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")
            continue

        if not mtp_capability & mtp_exp_capability:
            mtp_mgmt_ctrl.cli_log_err("MTP doesn't support {:s}".format(card_type))
            mtp_mgmt_ctrl.mtp_chassis_shutdown()
            logfile_close(log_filep_list)
            # cleanup the log dir
            logfile_cleanup([log_dir+log_sub_dir])
            return

        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix:")
        if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
            alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}; SN_ALOM = {:s}; PN_ALOM = {:s}".format(sn, mac_ui, pn, alom_sn, alom_pn))
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}".format(sn, mac_ui, pn))
            
        if card_type == NIC_Type.ORTANO:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD1 image: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD2 image: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI image: " + os.path.basename(qspi_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end\n")
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD image: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI image: " + os.path.basename(qspi_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end\n")

        pass_nic_list.append(slot)

        # DL precheck
        for test in ["NIC_POWER", "NIC_TYPE", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
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
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                   mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
                   fail_nic_list.append(slot)
                   pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
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

        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES100 or card_type == NIC_Type.FORIO:
            qspi_img_file = naples100_qspi_img_file
            cpld_img_file = naples100_cpld_img_file
        elif card_type == NIC_Type.VOMERO:
            qspi_img_file = vomero_qspi_img_file
            cpld_img_file = vomero_cpld_img_file
        elif card_type == NIC_Type.NAPLES100IBM:
            qspi_img_file = naples100ibm_qspi_img_file
            cpld_img_file = naples100ibm_cpld_img_file
        elif card_type == NIC_Type.NAPLES100HPE:
            qspi_img_file = naples100hpe_qspi_img_file
            cpld_img_file = naples100hpe_cpld_img_file
        elif card_type == NIC_Type.VOMERO2:
            qspi_img_file = vomero2_qspi_img_file
            cpld_img_file = vomero2_cpld_img_file
        elif card_type == NIC_Type.ORTANO:
            qspi_img_file = ortano_qspi_img_file
            cpld_img_file = ortano_cpld_img_file
        elif card_type == NIC_Type.NAPLES25:
            qspi_img_file = naples25_qspi_img_file
            cpld_img_file = naples25_cpld_img_file
        elif card_type == NIC_Type.NAPLES25SWM:
            qspi_img_file = naples25swm_qspi_img_file
            cpld_img_file = naples25swm_cpld_img_file
        elif card_type == NIC_Type.NAPLES25OCP:
            qspi_img_file = naples25ocp_qspi_img_file
            cpld_img_file = naples25ocp_cpld_img_file
        elif card_type == NIC_Type.NAPLES25SWMDELL:
            qspi_img_file = naples25swmdell_qspi_img_file
            cpld_img_file = naples25swmdell_cpld_img_file
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")
            continue

        nic_thread = threading.Thread(target = single_nic_fw_program, args = (mtp_mgmt_ctrl,
                                                                              nic_fru_cfg[mtp_id][key],
                                                                              cpld_img_file,
                                                                              qspi_img_file,
                                                                              slot,
                                                                              fail_nic_list,
                                                                              pass_nic_list,
                                                                              swmtestmode))
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

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    # init nic diag env.
    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return
    #set_pslc(mtp_mgmt_ctrl,nic_fru_cfg,mtp_id,fail_nic_list,pass_nic_list)

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

        # power cycle all nic (Debug Power Failure Issue)
        mtp_mgmt_ctrl.mtp_power_cycle_nic()
    
        # nic power status check
        testlists = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY", "AVS_SET"]
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM:
            testlists = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY", "AVS_SET"]
            if swmtestmode == Swm_Test_Mode.ALOM:
                testlists = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_ALOM_VERIFY", "CPLD_VERIFY"]
        if card_type == NIC_Type.ORTANO:
            testlists = ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "FRU_VERIFY", "CPLD_VERIFY", "QSPI_VERIFY"]
        for test in testlists:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
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
            # verify cpld
            elif test == "CPLD_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)
            # verify qspi
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
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
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
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
        
    for slot in fail_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if not swmtestmode == Swm_Test_Mode.ALOM:
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
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
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if not sn:
            continue
        if GLB_CFG_MFG_TEST_MODE:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_DL_LOG_DIR_FMT.format(nic_type, sn)
        else:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_DL_LOG_DIR_FMT.format(nic_type, sn)
        os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir))
        if log_hard_copy_flag:
            libmfg_utils.cli_inf("[{:s}] Collecting log file {:s}".format(sn, log_pkg_file))
            os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))
            log_relative_link = "../{:s}/{:s}".format(sn, os.path.basename(log_pkg_file))
            log_hard_copy_flag = False
        else:
            libmfg_utils.cli_inf("[{:s}] Create link log file {:s}".format(sn, log_relative_link))
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

