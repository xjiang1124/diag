#!/usr/bin/env python

import sys
import os
import time
import datetime
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
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libpro_srv_db import pro_srv_db


def logfile_close(filep_list):
    for fp in filep_list:
        fp.close()
    os.system("sync")


def logfile_cleanup(file_list):
    for _file in file_list:
        os.system("rm -rf {:s}".format(_file))


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


def load_mtp_cfg():
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file = os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml")
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)
    return mtp_cfg_db


def get_mtpid_list(mtp_cfg_db):
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    sub_mtpid_list = libmfg_utils.multiple_select_menu("Select MTP Chassis", mtpid_list)
    return sub_mtpid_list


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg)
    return mtp_mgmt_ctrl


def single_nic_fw_program(mtp_mgmt_ctrl, fru_cfg, cpld_img_file, qspi_img_file, slot, prog_fail_nic_list, prog_fail_sn_list):
    sn = fru_cfg["SN"]
    mac = fru_cfg["MAC"]
    pn = fru_cfg["PN"]
    prog_date = str(fru_cfg["TS"])

    # program FRU
    dsp = "DL_FRU"
    test = "FRU_PROG"
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
    start_ts = datetime.datetime.now().replace(microsecond=0)
    ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn)
    stop_ts = datetime.datetime.now().replace(microsecond=0)
    duration = str(stop_ts - start_ts)
    if not ret:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
        prog_fail_nic_list.append(slot)
        prog_fail_sn_list.append(sn)
        return
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

    # program CPLD
    dsp = "DL_CPLD"
    test = "CPLD_PROG"
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
    start_ts = datetime.datetime.now().replace(microsecond=0)
    ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
    stop_ts = datetime.datetime.now().replace(microsecond=0)
    duration = str(stop_ts - start_ts)
    if not ret:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
        prog_fail_nic_list.append(slot)
        prog_fail_sn_list.append(sn)
        return
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

    # program QSPI
    dsp = "DL_QSPI"
    test = "QSPI_PROG"
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
    start_ts = datetime.datetime.now().replace(microsecond=0)
    ret = mtp_mgmt_ctrl.mtp_program_nic_qspi(slot, qspi_img_file)
    stop_ts = datetime.datetime.now().replace(microsecond=0)
    duration = str(stop_ts - start_ts)
    if not ret:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
        prog_fail_nic_list.append(slot)
        prog_fail_sn_list.append(sn)
        return
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)


def main():
    parser = argparse.ArgumentParser(description="MFG DL Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--force-scan", help="Need to scan barcode", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    if args.force_scan:
        force_scan = True
    else:
        force_scan = False

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = get_mtpid_list(mtp_cfg_db)
    mtp_id = mtpid_list[0]
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    # local log files
    log_file_list = list()
    log_filep_list = list()
    log_dir = "log/"
    log_timestamp = libmfg_utils.get_timestamp()
    log_sub_dir = MTP_DIAG_Logfile.MFG_DL_LOG_DIR.format(mtp_id, log_timestamp)
    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir + log_sub_dir))
    test_log_file = log_dir + log_sub_dir + "test_dl.log"
    log_file_list.append(test_log_file)
    test_log_filep = open(test_log_file, "w+")
    log_filep_list.append(test_log_filep)

    if verbosity:
        diag_log_filep = sys.stdout
    else:
        diag_log_file = log_dir + log_sub_dir + "diag_dl.log"
        log_file_list.append(diag_log_file)
        diag_log_filep = open(diag_log_file, "w+")
        log_filep_list.append(diag_log_filep)

    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = log_dir + log_sub_dir + "diag_{:s}_dl.log".format(key)
        log_file_list.append(diag_nic_log_file)
        diag_nic_log_filep = open(diag_nic_log_file, "w+")
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list)

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    if force_scan:
        pass_rslt_list = list()
        fail_rslt_list = list()
        mtp_mgmt_ctrl.cli_log_inf("Start the Barcode Scan Process", level=0)
        while True:
            scan_rslt = mtp_mgmt_ctrl.mtp_barcode_scan(False)
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
    else:
        mtp_mgmt_ctrl.cli_log_inf("Skip Barcode Scan Process", level=0)

    # get the absolute file path
    nic_firmware_cfg_file = os.path.abspath("config/nic_firmware_cfg.yaml")
    nic_fw_cfg = libmfg_utils.load_cfg_from_yaml(nic_firmware_cfg_file)
    naples100_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["CPLD_FILE"]
    naples100_qspi_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["QSPI_FILE"]
    naples25_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["CPLD_FILE"]
    naples25_qspi_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["QSPI_FILE"]

    mtp_mgmt_ctrl.mtp_apc_pwr_on()
    mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP chassis", level=0)
        logfile_close(log_filep_list)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected\n", level=0)

    # diag environment pre init
    if not mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null"):
        mtp_mgmt_ctrl.cli_log_err("Unable to pre-init diag environment", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # diag environment post init
    if not mtp_mgmt_ctrl.mtp_diag_post_init(mtp_capability):
        mtp_mgmt_ctrl.cli_log_err("Unable to post-init diag environment", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # get the mtp system info
    if not mtp_mgmt_ctrl.mtp_sys_info_disp():
        mtp_mgmt_ctrl.cli_log_err("Unable to retrieve MTP system info", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # PSU/FAN absent, powerdown MTP
    if not mtp_mgmt_ctrl.mtp_hw_init(MTP_Const.MFG_EDVT_NORM_FAN_SPD):
        mtp_mgmt_ctrl.cli_log_err("MTP HW Init Fail", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # init all the nic.
    if not mtp_mgmt_ctrl.mtp_nic_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC type, present failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # power on all nic
    mtp_mgmt_ctrl.mtp_power_on_nic()

    # init nic diag env.
    if force_scan:
        rc = mtp_mgmt_ctrl.mtp_nic_diag_init(emmc_format=True, fru_valid=False, sn_tag=True, fru_cfg=nic_fru_cfg)
    else:
        rc = mtp_mgmt_ctrl.mtp_nic_diag_init(emmc_format=True)

    if not rc:
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    pass_nic_list = list()
    pass_sn_list = list()
    fail_nic_list = list()
    fail_sn_list = list()
    naples100_sn_list = list()
    naples25_sn_list = list()

    # no tag to scan, construct the nic_fru_cfg
    if not force_scan:
        nic_fru_cfg = dict()
        nic_fru_cfg[mtp_id] = dict()
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            key = libmfg_utils.nic_key(slot)
            nic_fru_cfg[mtp_id][key] = dict()
            if mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot):
                if mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                    nic_fru_cfg[mtp_id][key]["VALID"] = "YES"
                    nic_fru_info = mtp_mgmt_ctrl.mtp_get_nic_fru(slot)
                    nic_fru_cfg[mtp_id][key]["SN"] = nic_fru_info[0]
                    nic_fru_cfg[mtp_id][key]["MAC"] = nic_fru_info[1].replace('-', '')
                    nic_fru_cfg[mtp_id][key]["PN"] = nic_fru_info[2]
                    nic_fru_cfg[mtp_id][key]["TS"] = libmfg_utils.get_fru_date()
                else:
                    nic_fru_cfg[mtp_id][key]["VALID"] = "NO"
                    fail_nic_list.append(key)
                    fail_sn_list.append("FLMDEADBEEF")
            else:
                nic_fru_cfg[mtp_id][key]["VALID"] = "NO"

    mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Started", level=0)
    mtp_start_ts = libmfg_utils.timestamp_snapshot()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) == "YES":
            sn = nic_fru_cfg[mtp_id][key]["SN"]
            mac = nic_fru_cfg[mtp_id][key]["MAC"]
            pn = nic_fru_cfg[mtp_id][key]["PN"]
            prog_date = str(nic_fru_cfg[mtp_id][key]["TS"])
            mac_ui = libmfg_utils.mac_address_format(mac)

            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES100 or card_type == NIC_Type.FORIO:
                if not mtp_capability & 0x1:
                    mtp_mgmt_ctrl.cli_log_err("MTP doesn't support Naples100")
                    mtp_mgmt_ctrl.mtp_chassis_shutdown()
                    logfile_close(log_filep_list)
                    return
                cpld_img_file = naples100_cpld_img_file
                qspi_img_file = naples100_qspi_img_file
                naples100_sn_list.append(sn)
            elif card_type == NIC_Type.NAPLES25:
                if not mtp_capability & 0x2:
                    mtp_mgmt_ctrl.cli_log_err("MTP doesn't support Naples25")
                    mtp_mgmt_ctrl.mtp_chassis_shutdown()
                    logfile_close(log_filep_list)
                    return
                cpld_img_file = naples25_cpld_img_file
                qspi_img_file = naples25_qspi_img_file
                naples25_sn_list.append(sn)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")

            # nic power status check
            dsp = "DL_PRE_CHECK"
            test = "NIC_POWER"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
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

            # nic type check
            dsp = "DL_PRE_CHECK"
            test = "NIC_TYPE"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_nic_type_valid(slot)
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

            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix:", level=0)
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}".format(sn, mac_ui, pn))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD image: " + os.path.basename(cpld_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "QSPI image: " + os.path.basename(qspi_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end\n", level=0)

            # nic present check
            dsp = "DL_PRE_CHECK"
            test = "NIC_PRSNT"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
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

            # check nic init status
            dsp = "DL_PRE_CHECK"
            test = "NIC_INIT"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
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

            # check if nic comes up from diagfw
            dsp = "DL_PRE_CHECK"
            test = "NIC_DIAG_BOOT"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
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

    # program the NIC firmware
    nic_thread_list = list()
    prog_fail_nic_list = list()
    prog_fail_sn_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        if key in fail_nic_list:
            continue
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) == "YES":
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES100 or card_type == NIC_Type.FORIO:
                qspi_img_file = naples100_qspi_img_file
                cpld_img_file = naples100_cpld_img_file
            elif card_type == NIC_Type.NAPLES25:
                qspi_img_file = naples25_qspi_img_file
                cpld_img_file = naples25_cpld_img_file
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")
                continue

            nic_thread = threading.Thread(target = single_nic_fw_program, args = (mtp_mgmt_ctrl, nic_fru_cfg[mtp_id][key], cpld_img_file, qspi_img_file, slot, prog_fail_nic_list, prog_fail_sn_list))
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

    for slot, sn in zip(prog_fail_nic_list, prog_fail_sn_list):
        key = libmfg_utils.nic_key(slot)
        mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC FW Update Failed\n", level=0)
        fail_nic_list.append(key)
        fail_sn_list.append(sn)

    # power cycle MTP
    mtp_mgmt_ctrl.mtp_power_cycle()

    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP chassis", level=0)
        logfile_close(log_filep_list)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected\n", level=0)

    # diag environment pre init
    if not mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null"):
        mtp_mgmt_ctrl.cli_log_err("Unable to pre-init diag environment", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # init all the nic.
    if not mtp_mgmt_ctrl.mtp_nic_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC type, present failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # power on all nic
    mtp_mgmt_ctrl.mtp_power_on_nic()

    # init nic diag env.
    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

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

            # nic power status check
            dsp = "DL_PRE_CHECK"
            test = "NIC_POWER"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
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

            # nic present check
            dsp = "DL_PRE_CHECK"
            test = "NIC_PRSNT"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
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

            # check nic init status
            dsp = "DL_PRE_CHECK"
            test = "NIC_INIT"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
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

            # verify QSPI
            dsp = "DL_QSPI"
            test = "QSPI_VERIFY"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_verify_nic_qspi(slot)
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

            # set avs at last
            dsp = "DL_AVS"
            test = "AVS_SET"
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_avs(slot)
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

            pass_nic_list.append(key)
            pass_sn_list.append(sn)
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot\n")

    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Complete", level=0)

    mtp_mgmt_ctrl.mtp_chassis_shutdown()

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

    # pkg the logfile
    log_pkg_file = MTP_DIAG_Logfile.MFG_DL_LOG_PKG_FILE.format(mtp_id, log_timestamp)
    os.system(MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format(log_dir+log_pkg_file, log_dir, log_sub_dir))

    # move the logs to the log root dir
    if len(naples100_sn_list) > 0:
        if GLB_CFG_MFG_TEST_MODE:
            dl_log_path = MTP_DIAG_Logfile.DIAG_MFG_NAPLES100_DL_LOG_DIR
        else:
            dl_log_path = MTP_DIAG_Logfile.DIAG_MFG_MODEL_NAPLES100_DL_LOG_DIR
        for sn in naples100_sn_list:
            mfg_log_dir = dl_log_path + sn + "/"
            os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir))
            os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))

    if len(naples25_sn_list) > 0:
        if GLB_CFG_MFG_TEST_MODE:
            dl_log_path = MTP_DIAG_Logfile.DIAG_MFG_NAPLES25_DL_LOG_DIR
        else:
            dl_log_path = MTP_DIAG_Logfile.DIAG_MFG_MODEL_NAPLES25_DL_LOG_DIR
        for sn in naples25_sn_list:
            mfg_log_dir = dl_log_path + sn + "/"
            os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir))
            os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))

    if GLB_CFG_MFG_TEST_MODE:
        mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file)

    # cleanup the log dir
    logfile_cleanup([log_dir+log_sub_dir, log_dir+log_pkg_file])

    return

if __name__ == "__main__":
    main()

