#!/usr/bin/env python

import sys
import os
import time
import datetime
import pexpect
import argparse
import re
import random

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libpro_srv_db import pro_srv_db


def logfile_close(filep_list):
    for fp in filep_list:
        fp.close()
    os.system("sync")


def logfile_cleanup(file_list):
    for _file in file_list:
        os.system("rm -f {:s}".format(_file))


def mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    duration = mtp_stop_ts - mtp_start_ts

    with open(test_log_file, 'r') as fp:
        buf = fp.read()

    # MTP related error, don't post any report
    if MTP_DIAG_Report.MTP_DIAG_REGRESSION_FAIL in buf:
        libmfg_utils.cli_inf(mtp_cli_id_str + "MTP Setup fails, no report will be generated")
        return

    libmfg_utils.cli_inf(mtp_cli_id_str + "Start posting test report")
    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL in buf:
        nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
        match = re.findall(nic_fail_reg_exp, buf)
        for slot, nic_type, sn in match:
            test_list = list()
            test_rslt_list = list()
            err_dsc_list = list()
            err_code_list = list()
            nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
            # find all test status
            nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
            sub_match = re.findall(nic_test_rslt_reg_exp, buf)
            for dsp, test, result in sub_match:
                test_list.append("{:s}-{:s}".format(dsp, test))
                test_rslt_list.append(result)
                err_dsc_list.append(nic_cli_id_str)
                err_code_list.append(result)
            ret = libmfg_utils.flx_web_srv_post_uut_report("DL", nic_type, sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list)
            if not ret:
                libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
            else:
                libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))

    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS in buf:
        nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
        match = re.findall(nic_pass_reg_exp, buf)
        for slot, nic_type, sn in match:
            test_list = list()
            test_rslt_list = list()
            err_dsc_list = list()
            err_code_list = list()
            nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
            # find all test status
            nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
            sub_match = re.findall(nic_test_rslt_reg_exp, buf)
            for dsp, test, result in sub_match:
                test_list.append("{:s}-{:s}".format(dsp, test))
                test_rslt_list.append(result)
                err_dsc_list.append(nic_cli_id_str)
                err_code_list.append(result)
            ret = libmfg_utils.flx_web_srv_post_uut_report("DL", nic_type, sn, "PASS", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list)
            if not ret:
                libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
            else:
                libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))


def get_pro_srv_id():
    product_server_cfg_file = os.path.abspath("config/pensando_pro_srv1_cfg.yaml")
    pro_srv_cfg_db = pro_srv_db(pro_srv_cfg_file = product_server_cfg_file)
    pro_srv_list = list(pro_srv_cfg_db.get_pro_srv_id_list())
    if len(pro_srv_list) > 1:
        pro_srv_id = libmfg_utils.single_select_menu("Select Product Server", pro_srv_list)
        if not pro_srv_id:
            return None
    else:
        pro_srv_id = pro_srv_list[0]
    return pro_srv_id


def load_mtp_cfg():
    product_server_cfg_file = os.path.abspath("config/pensando_pro_srv1_cfg.yaml")
    pro_srv_cfg_db = pro_srv_db(pro_srv_cfg_file = product_server_cfg_file)
    pro_srv_list = list(pro_srv_cfg_db.get_pro_srv_id_list())
    if len(pro_srv_list) > 1:
        pro_srv_id = libmfg_utils.single_select_menu("Select Product Server", pro_srv_list)
        if not pro_srv_id:
            return None
    else:
        pro_srv_id = pro_srv_list[0]
    filename = pro_srv_cfg_db.get_pro_srv_mtp_chassis_cfg_file(pro_srv_id)
    mtp_chassis_cfg_file = os.path.abspath("config/" + filename)
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)
    return mtp_cfg_db


def get_mtpid_list(mtp_cfg_db):
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    sub_mtpid_list = libmfg_utils.multiple_select_menu("Select MTP Chassis", mtpid_list)
    return sub_mtpid_list


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg)
    return mtp_mgmt_ctrl


def main():
    parser = argparse.ArgumentParser(description="MFG Barcode Scanner Utility", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    pro_srv_id = get_pro_srv_id()
    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = get_mtpid_list(mtp_cfg_db)
    mtp_id = mtpid_list[0]
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    # local log files
    log_file_list = list()
    log_filep_list = list()
    test_log_file = "_".join(["log/test_dl", pro_srv_id, mtp_id, libmfg_utils.get_timestamp()]) + ".log"
    log_file_list.append(test_log_file)
    test_log_filep = open(test_log_file, "w+")
    log_filep_list.append(test_log_filep)

    if verbosity:
        diag_log_filep = sys.stdout
    else:
        diag_log_file = "_".join(["log/diag_dl", pro_srv_id, mtp_id, libmfg_utils.get_timestamp()]) + ".log"
        log_file_list.append(diag_log_file)
        diag_log_filep = open(diag_log_file, "w+")
        log_filep_list.append(diag_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep)

    mtp_mgmt_ctrl.cli_log_inf("Start the Barcode Scan Process", level=0)
    while True:
        scan_rslt = mtp_mgmt_ctrl.mtp_barcode_scan(False)
        if scan_rslt:
            break;
        mtp_mgmt_ctrl.cli_log_inf("Restart the Barcode Scan Process", level=0)

    pass_rslt_list = list()
    fail_rslt_list = list()
    # print scan summary
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        nic_cli_id_str = libmfg_utils.id_str(mtp = mtp_id, nic = slot)
        if scan_rslt[key]["NIC_VALID"]:
            sn = scan_rslt[key]["NIC_SN"]
            pn = scan_rslt[key]["NIC_PN"]
            mac_ui = libmfg_utils.mac_address_format(scan_rslt[key]["NIC_MAC"])
            pass_rslt_list.append(nic_cli_id_str + "SN = " + sn + "; MAC = " + mac_ui + "; PN = " + pn)
        else:
            fail_rslt_list.append(nic_cli_id_str + "NIC Absent")
    libmfg_utils.cli_log_rslt("Barcode Scan Summary", pass_rslt_list, fail_rslt_list, test_log_filep)

    scan_cfg_file = "_".join(["log/barcode_cfg", pro_srv_id, mtp_id, libmfg_utils.get_timestamp()]) + ".yaml"
    scan_cfg_filep = open(scan_cfg_file, "w+")
    mtp_mgmt_ctrl.gen_barcode_config_file(pro_srv_id, scan_cfg_filep, scan_rslt)
    scan_cfg_filep.close()
    log_file_list.append(scan_cfg_file)

    # get the absolute file path
    nic_firmware_cfg_file = os.path.abspath("config/nic_firmware_cfg.yaml")
    nic_fw_cfg = libmfg_utils.load_cfg_from_yaml(nic_firmware_cfg_file)
    naples100_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["CPLD_FILE"]
    naples100_vrm_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["VRM_FILE"]
    naples100_vrm_img_cksum = nic_fw_cfg[NIC_Type.NAPLES100]["VRM_CKSUM"]
    naples100_qspi_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["QSPI_FILE"]
    naples100_emmc_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["EMMC_FILE"]

    naples25_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["CPLD_FILE"]
    naples25_vrm_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["VRM_FILE"]
    naples25_vrm_img_cksum = nic_fw_cfg[NIC_Type.NAPLES25]["VRM_CKSUM"]
    naples25_qspi_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["QSPI_FILE"]
    naples25_emmc_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["EMMC_FILE"]

    # reload the barcode config file
    nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(scan_cfg_file)

    mtp_mgmt_ctrl.mtp_apc_pwr_on()
    mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP chassis", level=0)
        logfile_close(log_filep_list)
        logfile_cleanup(log_file_list)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected\n", level=0)

    # get the sw version info
    sw_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
    if sw_ver:
        mtp_mgmt_ctrl.cli_log_inf("MTP SW version: {:s}".format(sw_ver), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_err("Unable to retrieve diag image version info", level=0)
        logfile_close(log_filep_list)
        logfile_cleanup(log_file_list)
        return

    # diag environment pre init
    if not mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null"):
        mtp_mgmt_ctrl.cli_log_err("Unable to pre-init diag environment", level=0)
        logfile_close(log_filep_list)
        logfile_cleanup(log_file_list)
        return

    # get the hw version info
    cpld_ver_list = mtp_mgmt_ctrl.mtp_get_hw_version()
    if not cpld_ver_list:
        mtp_mgmt_ctrl.cli_log_err("Retrieve MTP CPLD Version Fail", level=0)
        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
        mtp_mgmt_ctrl.mtp_apc_pwr_off()
        logfile_close(log_filep_list)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP IO-CPLD version: {:s}, JTAG-CPLD version: {:s}".format(str(cpld_ver_list[0]), str(cpld_ver_list[1])), level=0)

    # PSU/FAN absent, powerdown MTP
    if not mtp_mgmt_ctrl.mtp_hw_init(True, MTP_Const.MFG_EDVT_NORM_FAN_SPD):
        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
        mtp_mgmt_ctrl.mtp_apc_pwr_off()
        logfile_close(log_filep_list)
        return

    # init all the nic.
    if not mtp_mgmt_ctrl.mtp_nic_init(fru_load = False):
        mtp_mgmt_ctrl.cli_log_err("Diag Initialize NIC Fail", level=0)
        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
        mtp_mgmt_ctrl.mtp_apc_pwr_off()
        logfile_close(log_filep_list)
        return

    pass_nic_list = list()
    pass_sn_list = list()
    fail_nic_list = list()
    fail_sn_list = list()
    naples100_sn_list = list()
    naples25_sn_list = list()

    mtp_mgmt_ctrl.cli_log_inf("NIC SCAN Check Start", level=0)
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if mtp_mgmt_ctrl.mtp_get_nic_prsnt(slot) and str.upper(valid) != "YES":
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC is present, but barcode is not scanned", level=0)
            mtp_mgmt_ctrl.cli_log_err("NIC SCAN Check Failed, Please Restart", level=0)
            mtp_mgmt_ctrl.mtp_mgmt_poweroff()
            mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC\n".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
            libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
            mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
            mtp_mgmt_ctrl.mtp_apc_pwr_off()
            logfile_close(log_filep_list)
            logfile_cleanup(log_file_list)
            return
    mtp_mgmt_ctrl.cli_log_inf("NIC SCAN Check Complete\n", level=0)

    mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Started", level=0)
    mtp_start_ts = libmfg_utils.timestamp_snapshot()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) == "YES":
            sn = nic_fru_cfg[mtp_id][key]["SN"]
            mac = nic_fru_cfg[mtp_id][key]["MAC"]
            prog_date = str(nic_fru_cfg[mtp_id][key]["TS"])
            mac_ui = libmfg_utils.mac_address_format(mac)
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES100:
                cpld_img_file = naples100_cpld_img_file
                qspi_img_file = naples100_qspi_img_file
                # vrm_img_file = naples100_vrm_img_file
                # vrm_img_cksum = naples100_vrm_img_cksum
                emmc_img_file = naples100_emmc_img_file
                naples100_sn_list.append(sn)
            elif card_type == NIC_Type.NAPLES25:
                cpld_img_file = naples25_cpld_img_file
                qspi_img_file = naples25_qspi_img_file
                # vrm_img_file = naples25_vrm_img_file
                # vrm_img_cksum = naples25_vrm_img_cksum
                emmc_img_file = naples25_emmc_img_file
                naples25_sn_list.append(sn)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected: {:s}".format(card_type))
                mtp_mgmt_ctrl.cli_log_err("NIC PRSNT Check Failed, Please Restart", level=0)
                mtp_mgmt_ctrl.mtp_mgmt_poweroff()
                mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC\n".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
                libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
                mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
                mtp_mgmt_ctrl.mtp_apc_pwr_off()
                logfile_close(log_filep_list)
                logfile_cleanup(log_file_list)
                return

            mtp_mgmt_ctrl.mtp_set_nic_scan_sn(slot, sn)
            mtp_mgmt_ctrl.mtp_set_nic_sn(slot, sn)
            mtp_mgmt_ctrl.mtp_set_nic_scan_mac(slot, mac)
            mtp_mgmt_ctrl.mtp_set_nic_mac(slot, mac)

            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix:", level=0)
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; DATE = {:s}".format(sn, mac_ui, prog_date))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD image: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI image: " + os.path.basename(qspi_img_file))
            # mtp_mgmt_ctrl.cli_log_slot_inf(slot, "VRM image: " + os.path.basename(vrm_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "EMMC image: " + os.path.basename(emmc_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end", level=0)

            # nic present check
            dsp = "DL_PRE_CHECK"
            test = "NIC_PRSNT"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_mgmt_pre_post_diag_check("NIC_FRU", slot)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

    # power on all nic
    mtp_mgmt_ctrl.mtp_power_on_nic()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        if key in fail_nic_list:
            continue
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) == "YES":
            dsp = "DL_PRE_CHECK"
            test = "NIC_DIAG_BOOT"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(slot)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

    # power on all nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.mtp_power_on_nic()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        if key in fail_nic_list:
            continue
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) == "YES":
            sn = nic_fru_cfg[mtp_id][key]["SN"]
            mac = nic_fru_cfg[mtp_id][key]["MAC"]
            pn = nic_fru_cfg[mtp_id][key]["PN"]
            prog_date = str(nic_fru_cfg[mtp_id][key]["TS"])

            # init nic for fw update
            dsp = "DL_PRE_CHECK"
            test = "NIC_INIT"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_nic_diag_init(slot)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            # program FRU
            dsp = "DL_FRU"
            test = "FRU_PROG"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES100:
                cpld_img_file = naples100_cpld_img_file
                qspi_img_file = naples100_qspi_img_file
                # vrm_img_file = naples100_vrm_img_file
                # vrm_img_cksum = naples100_vrm_img_cksum
                emmc_img_file = naples100_emmc_img_file
            elif card_type == NIC_Type.NAPLES25:
                cpld_img_file = naples25_cpld_img_file
                qspi_img_file = naples25_qspi_img_file
                # vrm_img_file = naples25_vrm_img_file
                # vrm_img_cksum = naples25_vrm_img_cksum
                emmc_img_file = naples25_emmc_img_file
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected: {:s}".format(card_type))
                continue

            # program CPLD
            dsp = "DL_CPLD"
            test = "CPLD_PROG"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            # program VRM
            # dsp = "DL_VRM"
            # test = "VRM_PROG"
            # mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            # start_ts = datetime.datetime.now().replace(microsecond=0)
            # ret = mtp_mgmt_ctrl.mtp_program_nic_vrm(slot, vrm_img_file, vrm_img_cksum)
            # stop_ts = datetime.datetime.now().replace(microsecond=0)
            # duration = str(stop_ts - start_ts)
            # if not ret:
            #     mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
            #     mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
            #     mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
            #     fail_nic_list.append(key)
            #     fail_sn_list.append(sn)
            #     continue
            # else:
            #     mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            # program QSPI
            dsp = "DL_QSPI"
            test = "QSPI_PROG"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_program_nic_qspi(slot, qspi_img_file)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            # install EMMC
            dsp = "DL_EMMC"
            test = "EMMC_PROG"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_install_nic_emmc(slot, emmc_img_file)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

    # power cycle MTP
    mtp_mgmt_ctrl.mtp_mgmt_poweroff()
    libmfg_utils.cli_inf(mtp_cli_id_str + "Power off OS, Wait {:d} seconds to power off APC\n".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY))
    libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
    libmfg_utils.cli_inf(mtp_cli_id_str + "Power off APC")
    mtp_mgmt_ctrl.mtp_apc_pwr_off()

    time.sleep(MTP_Const.MTP_POWER_CYCLE_DELAY)

    mtp_mgmt_ctrl.mtp_apc_pwr_on()
    libmfg_utils.cli_inf(mtp_cli_id_str + "Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY))
    libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP chassis", level=0)
        logfile_close(log_filep_list)
        logfile_cleanup(log_file_list)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected\n", level=0)

    # diag environment pre init
    if not mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null"):
        mtp_mgmt_ctrl.cli_log_err("Unable to pre-init diag environment", level=0)
        logfile_close(log_filep_list)
        logfile_cleanup(log_file_list)
        return

    # power on all nic
    mtp_mgmt_ctrl.mtp_power_on_nic()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        if key in fail_nic_list:
            continue
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) == "YES":
            sn = nic_fru_cfg[mtp_id][key]["SN"]
            mac = nic_fru_cfg[mtp_id][key]["MAC"]
            pn = nic_fru_cfg[mtp_id][key]["PN"]
            prog_date = str(nic_fru_cfg[mtp_id][key]["TS"])

            # init nic for fw verify
            dsp = "DL_PRE_CHECK"
            test = "NIC_INIT"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_nic_diag_init(slot)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            # verify FRU
            exp_sn = sn
            exp_mac = "-".join(re.findall("..", mac))
            exp_pn = pn
            dsp = "DL_FRU"
            test = "FRU_VERIFY"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_verify_nic_fru(slot, exp_sn, exp_mac, exp_pn)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            # verify CPLD
            dsp = "DL_CPLD"
            test = "CPLD_VERIFY"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            # verify VRM
            # dsp = "DL_VRM"
            # test = "VRM_VERIFY"
            # mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            # start_ts = datetime.datetime.now().replace(microsecond=0)
            # ret = mtp_mgmt_ctrl.mtp_verify_nic_vrm(slot, vrm_img_file, vrm_img_cksum)
            # stop_ts = datetime.datetime.now().replace(microsecond=0)
            # duration = str(stop_ts - start_ts)
            # if not ret:
            #     mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
            #     mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
            #     mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
            #     fail_nic_list.append(key)
            #     fail_sn_list.append(sn)
            #     continue
            # else:
            #     mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            # verify QSPI
            dsp = "DL_QSPI"
            test = "QSPI_VERIFY"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_verify_nic_qspi(slot, qspi_img_file)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
                fail_nic_list.append(key)
                fail_sn_list.append(sn)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            # update MAC address
            # mtp_mgmt_ctrl.mtp_update_nic_mac_address(slot)

            pass_nic_list.append(key)
            pass_sn_list.append(sn)
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot\n")

    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Complete", level=0)

    mtp_mgmt_ctrl.mtp_mgmt_poweroff()
    mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC\n".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
    mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
    mtp_mgmt_ctrl.mtp_apc_pwr_off()

    for nic_key, nic_sn in zip(fail_nic_list, fail_sn_list):
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            key = libmfg_utils.nic_key(slot)
            if key == nic_key:
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                mtp_mgmt_ctrl.cli_log_err("{:s} {:s} {:s} {:s}".format(nic_key, nic_type, nic_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
                break
    for nic_key, nic_sn in zip(pass_nic_list, pass_sn_list):
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            key = libmfg_utils.nic_key(slot)
            if key == nic_key:
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(nic_key, nic_type, nic_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
                break

    logfile_close(log_filep_list)

    # move the logs to the log root dir
    if len(naples100_sn_list) > 0:
        dl_log_path = MTP_DIAG_Logfile.DIAG_MFG_DL_LOG_DIR
        for sn in naples100_sn_list:
            logdir = dl_log_path + sn + "/"
            os.system("mkdir -p " + logdir)
            for logfile in log_file_list:
                dst_logfile = "{:s}_{:s}".format(sn, os.path.basename(logfile))
                os.system("cp {:s} {:s}".format(logfile, logdir+os.path.basename(logfile)))

    mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file)
    logfile_cleanup(log_file_list)

    return

if __name__ == "__main__":
    main()

