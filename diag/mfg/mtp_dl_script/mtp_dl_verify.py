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
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg)
    return mtp_mgmt_ctrl


def main():
    parser = argparse.ArgumentParser(description="MTP DL Verify Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid
        mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    mtp_cfg_db = load_mtp_cfg()

    # local log files
    log_file_list = list()
    log_filep_list = list()
    test_log_file = "test_dl.log"
    log_file_list.append(test_log_file)
    test_log_filep = open(test_log_file, "a+")
    log_filep_list.append(test_log_filep)

    diag_log_file = "diag_dl.log"
    log_file_list.append(diag_log_file)
    diag_log_filep = open(diag_log_file, "a+")
    log_filep_list.append(diag_log_filep)

    fru_cfg_file = "dl_barcode.yaml" 
    log_file_list.append(fru_cfg_file) 

    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = "diag_{:s}_dl.log".format(key)
        log_file_list.append(diag_nic_log_file)
        diag_nic_log_filep = open(diag_nic_log_file, "a+")
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list)

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

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    # init nic diag env.
    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    fail_nic_list = list()
    pass_nic_list = list()

    # load the barcode config file
    nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(fru_cfg_file)

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) == "YES":
            pass_nic_list.append(slot)
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
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
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
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
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
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
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
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
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
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
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
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
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
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                continue
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot\n")

    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.cli_log_inf("MTP DL Verify Test Complete", level=0)

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

    logfile_close(log_filep_list)
    return

if __name__ == "__main__":
    main()

