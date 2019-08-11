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
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/kpt_mtp_chassis_cfg.yaml"))
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


def single_nic_sec_cpld_program(mtp_mgmt_ctrl, sec_cpld_img_file, slot, sn, prog_fail_nic_list):
    # program secure cpld
    dsp = "KPT"
    test = "SEC_CPLD_PROG"
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
    start_ts = datetime.datetime.now().replace(microsecond=0)
    ret = mtp_mgmt_ctrl.mtp_program_nic_sec_cpld(slot, sec_cpld_img_file)
    stop_ts = datetime.datetime.now().replace(microsecond=0)
    duration = str(stop_ts - start_ts)
    if not ret:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
        prog_fail_nic_list.append(slot)
        return
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)


def single_nic_emmc_program(mtp_mgmt_ctrl, emmc_img_file, slot, sn, prog_fail_nic_list):
    # program EMMC
    dsp = "KPT"
    test = "SW_INSTALL"
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
    start_ts = datetime.datetime.now().replace(microsecond=0)
    ret = mtp_mgmt_ctrl.mtp_program_nic_emmc(slot, emmc_img_file)
    stop_ts = datetime.datetime.now().replace(microsecond=0)
    duration = str(stop_ts - start_ts)
    if not ret:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
        prog_fail_nic_list.append(slot)
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)


def main():
    parser = argparse.ArgumentParser(description="MTP Key Programming Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid

    mtp_cfg_db = load_mtp_cfg()

    # local log files
    log_filep_list = list()
    test_log_file = "test_kpt.log"
    test_log_filep = open(test_log_file, "w+")
    log_filep_list.append(test_log_filep)

    diag_log_file = "diag_kpt.log"
    diag_log_filep = open(diag_log_file, "w+")
    log_filep_list.append(diag_log_filep)

    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = "diag_{:s}_kpt.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, "w+")
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list)

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    # get the absolute file path
    nic_firmware_cfg_file = os.path.abspath("config/nic_firmware_cfg.yaml")
    nic_fw_cfg = libmfg_utils.load_cfg_from_yaml(nic_firmware_cfg_file)
    naples100_sec_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["SEC_CPLD_FILE"]
    naples100_emmc_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["EMMC_FILE"]
    vomero_sec_cpld_img_file = nic_fw_cfg[NIC_Type.VOMERO]["SEC_CPLD_FILE"]
    vomero_emmc_img_file = nic_fw_cfg[NIC_Type.VOMERO]["EMMC_FILE"]
    naples25_sec_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["SEC_CPLD_FILE"]
    naples25_emmc_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["EMMC_FILE"]

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

    # get the sw version info
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

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    dsp = "KPT"
    pass_nic_list = list()
    fail_nic_list = list()

    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot\n")
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        pass_nic_list.append(slot)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES100:
            emmc_img_file = naples100_emmc_img_file
            sec_cpld_img_file = naples100_sec_cpld_img_file
        elif card_type == NIC_Type.VOMERO:
            emmc_img_file = vomero_emmc_img_file
            sec_cpld_img_file = vomero_sec_cpld_img_file
        elif card_type == NIC_Type.NAPLES25:
            emmc_img_file = naples25_emmc_img_file
            sec_cpld_img_file = naples25_sec_cpld_img_file
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC Type", level=0)
            continue
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "KPT Program Matrix:", level=0)
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "EMMC image: " + os.path.basename(emmc_img_file))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Secure CPLD image: " + os.path.basename(sec_cpld_img_file))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "KPT Program Matrix end\n", level=0)

        for test in ["NIC_POWER", "NIC_TYPE", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT"]: 
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            # nic power status check
            if test == "NIC_POWER":
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
            elif test == "NIC_DIAG_BOOT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown KPT Test: {:s}, Ignore".format(test))
                continue
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

    # Secure key programming
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        for test in ["PCIE_ENA", "SEC_KEY_PROG"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            # disable PCIE Poll
            if test == "PCIE_ENA":
                ret = mtp_mgmt_ctrl.mtp_nic_pcie_poll_enable(slot, True)
            elif test == "SEC_KEY_PROG":
                ret = mtp_mgmt_ctrl.mtp_program_nic_sec_key(slot)
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown KPT Test: {:s}, Ignore".format(test))
                continue
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

    # power cycle NIC
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # program the NIC Secure CPLD
    nic_thread_list = list()
    prog_fail_nic_list = list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES100 or card_type == NIC_Type.FORIO:
            sec_cpld_img_file = naples100_sec_cpld_img_file
        elif card_type == NIC_Type.VOMERO:
            sec_cpld_img_file = vomero_sec_cpld_img_file
        elif card_type == NIC_Type.NAPLES25:
            sec_cpld_img_file = naples25_sec_cpld_img_file
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")
            continue

        nic_thread = threading.Thread(target = single_nic_sec_cpld_program, args = (mtp_mgmt_ctrl,
                                                                                    sec_cpld_img_file,
                                                                                    slot,
                                                                                    sn,
                                                                                    prog_fail_nic_list))
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

    for slot in prog_fail_nic_list:
        fail_nic_list.append(slot)
        pass_nic_list.remove(slot)

    # Secure CPLD Check
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        for test in ["SEC_CPLD_VERIFY"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            if test === "SEC_CPLD_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_sec_cpld(slot)
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown KPT Test: {:s}, Ignore".format(test))
                continue
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

    # power cycle NIC
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # program the NIC EMMC image
    nic_thread_list = list()
    prog_fail_nic_list = list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES100 or card_type == NIC_Type.FORIO:
            emmc_img_file = naples100_emmc_img_file
        elif card_type == NIC_Type.VOMERO:
            emmc_img_file = vomero_emmc_img_file
        elif card_type == NIC_Type.NAPLES25:
            emmc_img_file = naples25_emmc_img_file
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")
            continue

        nic_thread = threading.Thread(target = single_nic_emmc_program, args = (mtp_mgmt_ctrl,
                                                                                emmc_img_file,
                                                                                slot,
                                                                                sn,
                                                                                prog_fail_nic_list))
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

    for slot in prog_fail_nic_list:
        fail_nic_list.append(slot)
        pass_nic_list.remove(slot)

    # power cycle NIC
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    mtp_mgmt_ctrl.cli_log_inf("NIC SW Boot Delay Started\n", level=0)
    libmfg_utils.count_down(MTP_Const.NIC_SW_BOOTUP_DELAY)
    mtp_mgmt_ctrl.cli_log_inf("NIC SW Boot Delay Stopped\n", level=0)

    # verify the NIC EMMC
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        for test in ["SW_BOOT"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            if test == "SW_BOOT":
                ret = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_sw_boot(slot)
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown KPT Test: {:s}, Ignore".format(test))
                continue
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MTP Key Programming Test Complete", level=0)

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

