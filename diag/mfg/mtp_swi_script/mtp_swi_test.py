#!/usr/bin/env python

import sys
import os
import time
import pexpect
import threading
import argparse
import re
import ntpath

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libdefs import FF_Stage
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode


def logfile_close(filep_list):
    for fp in filep_list:
        fp.close()
    os.system("sync")


def load_mtp_cfg():
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/swi_mtp_chassis_cfg.yaml"))
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


def single_nic_sec_cpld_program(mtp_mgmt_ctrl, sec_cpld_img_file, slot, sn, prog_fail_nic_list):
    dsp = FF_Stage.FF_SWI
    for test in ["SEC_CPLD_PROG", "SEC_CPLD_REF"]:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        # program secure cpld
        if test == "SEC_CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_sec_cpld(slot, sec_cpld_img_file)
        elif test == "SEC_CPLD_REF":
            ret = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(slot)
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown SWI Test: {:s}, Ignore".format(test))
            continue
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            prog_fail_nic_list.append(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


def single_nic_gold_program(mtp_mgmt_ctrl, gold_img_file, slot, sn, prog_fail_nic_list):
    dsp = FF_Stage.FF_SWI
    for test in ["SEC_CPLD_VERIFY", "GOLD_PROG"]:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        if test == "SEC_CPLD_VERIFY":
            ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot, sec_cpld=True)
        elif test == "GOLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_gold(slot, gold_img_file)
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown SW Test: {:s}, Ignore".format(test))
            continue
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            prog_fail_nic_list.append(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


def single_nic_emmc_program(mtp_mgmt_ctrl, emmc_img_file, slot, sn, prog_fail_nic_list):
    dsp = FF_Stage.FF_SWI
    for test in ["SW_INSTALL"]:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        # program sw image onto EMMC
        if test == "SW_INSTALL":
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES100IBM:
                ret = mtp_mgmt_ctrl.mtp_program_nic_emmc_ibm(slot, emmc_img_file)
            else:
                ret = mtp_mgmt_ctrl.mtp_program_nic_emmc(slot, emmc_img_file)
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown SW Test: {:s}, Ignore".format(test))
            continue
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            prog_fail_nic_list.append(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


def main():
    parser = argparse.ArgumentParser(description="MTP Software Install Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--image", help="NIC eMMC image", required=True)
    parser.add_argument("--profile", help="NIC Profile")

    nic_profile = None
    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid
    if args.image:
        img_file = args.image
    if args.profile:
        #nic_profile = args.profile
        nic_profile = ntpath.basename(args.profile)

    mtp_cfg_db = load_mtp_cfg()

    # local log files
    log_filep_list = list()
    test_log_file = "test_swi.log"
    test_log_filep = open(test_log_file, "w+", buffering=0)
    log_filep_list.append(test_log_filep)

    diag_log_file = "diag_swi.log"
    diag_log_filep = open(diag_log_file, "w+", buffering=0)
    log_filep_list.append(diag_log_filep)

    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = "diag_{:s}_swi.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, "w+", buffering=0)
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list)

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    # get the absolute file path
    naples100_sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES100_SEC_CPLD_IMAGE
    naples100ibm_sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES100IBM_SEC_CPLD_IMAGE
    naples25_sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES25_SEC_CPLD_IMAGE
    vomero_sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.VOMERO_SEC_CPLD_IMAGE
    vomero2_sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.VOMERO2_SEC_CPLD_IMAGE
    naples25swm_sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES25SWM_SEC_CPLD_IMAGE
    naples25ocp_sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NAPLES25_HPE_OCP_SEC_CPLD_IMAGE
    gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_GOLDFW_IMAGE
    
    emmc_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + img_file

    if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, stage=FF_Stage.FF_SWI):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
        logfile_close(log_filep_list)
        return

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()


    # Set Naples25SWM test mode
    mtp_mgmt_ctrl.mtp_set_swmtestmode(Swm_Test_Mode.SW_DETECT)

    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    dsp = FF_Stage.FF_SWI
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
        if card_type == NIC_Type.NAPLES100 or card_type == NIC_Type.FORIO:
            sec_cpld_img_file = naples100_sec_cpld_img_file
        elif card_type == NIC_Type.NAPLES100IBM:
            sec_cpld_img_file = naples100ibm_sec_cpld_img_file
            gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_GOLDFW_IMAGE_IBM
        elif card_type == NIC_Type.VOMERO:
            sec_cpld_img_file = vomero_sec_cpld_img_file
        elif card_type == NIC_Type.VOMERO2:
            sec_cpld_img_file = vomero2_sec_cpld_img_file
            gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_GOLDFW_IMAGE_VOMERO2                                             
        elif card_type == NIC_Type.NAPLES25:
            sec_cpld_img_file = naples25_sec_cpld_img_file
        elif card_type == NIC_Type.NAPLES25SWM:
            sec_cpld_img_file = naples25swm_sec_cpld_img_file
            gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_GOLDFW_IMAGE_SWM 
        elif card_type == NIC_Type.NAPLES25OCP:
            sec_cpld_img_file = naples25ocp_sec_cpld_img_file
            gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.NIC_GOLDFW_IMAGE_HPE_OCP 
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC Type")
            continue

        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Software Program Matrix:")
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Secure CPLD image: " + os.path.basename(sec_cpld_img_file))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Main image: " + os.path.basename(emmc_img_file))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Gold image: " + os.path.basename(gold_img_file))
        if nic_profile:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Profile: " + os.path.basename(nic_profile))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Software Program Matrix end\n")

        for test in ["NIC_POWER", "NIC_TYPE", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
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
            # check nic boot from diagfw
            elif test == "NIC_DIAG_BOOT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
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

    # Secure key programming
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        for test in ["SEC_KEY_PROG"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "SEC_KEY_PROG":
                ret = mtp_mgmt_ctrl.mtp_program_nic_sec_key(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
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
        elif card_type == NIC_Type.NAPLES100IBM:
            sec_cpld_img_file = naples100ibm_sec_cpld_img_file
        elif card_type == NIC_Type.VOMERO:
            sec_cpld_img_file = vomero_sec_cpld_img_file
        elif card_type == NIC_Type.VOMERO2:
            sec_cpld_img_file = vomero2_sec_cpld_img_file
        elif card_type == NIC_Type.NAPLES25:
            sec_cpld_img_file = naples25_sec_cpld_img_file
        elif card_type == NIC_Type.NAPLES25SWM:
            sec_cpld_img_file = naples25swm_sec_cpld_img_file
        elif card_type == NIC_Type.NAPLES25OCP:
            sec_cpld_img_file = naples25ocp_sec_cpld_img_file
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
        for test in ["SEC_PROG_VERIFY"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "SEC_PROG_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_sec_cpld(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
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

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # program the NIC Gold image
    nic_thread_list = list()
    prog_fail_nic_list = list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        nic_thread = threading.Thread(target = single_nic_gold_program, args = (mtp_mgmt_ctrl,
                                                                                gold_img_file,
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

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    # verify the NIC goldfw boot
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        for test in ["GOLD_BOOT"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "GOLD_BOOT":
                ret = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_gold_boot(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SW Test: {:s}, Ignore".format(test))
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

    # Set NIC diagfw boot to install sw
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        for test in ["DIAG_BOOT"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "DIAG_BOOT":
                ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SW Test: {:s}, Ignore".format(test))
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

    # power cycle all nic
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

    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        ret = mtp_mgmt_ctrl.mtp_mgmt_nic_sw_cleanup_shutdown(slot)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            fail_nic_list.append(slot)
            pass_nic_list.remove(slot)
            break

    # power cycle NIC
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    mtp_mgmt_ctrl.cli_log_inf("NIC SW Boot Delay Started\n", level=0)
    libmfg_utils.count_down(MTP_Const.NIC_SW_BOOTUP_DELAY)
    mtp_mgmt_ctrl.cli_log_inf("NIC SW Boot Delay Stopped\n", level=0)

    # INIt the sw mgmt port
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        if not mtp_mgmt_ctrl.mtp_nic_mgmt_reinit(slot):
            pass_nic_list.remove(slot)
            fail_nic_list.append(slot)

    if not mtp_mgmt_ctrl.mtp_nic_mgmt_mac_refresh():
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP mac address refresh failed, test abort...")
        logfile_close(log_filep_list)
        return

    if not mtp_mgmt_ctrl.mtp_mgmt_nic_mac_validate():
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP detect duplicate mac address, test abort...")
        logfile_close(log_filep_list)
        return

    # Verify the NIC Software boot
    if nic_profile:
        sw_test_list = ["SW_BOOT", "SW_PROFILE", "SW_SHUTDOWN"]
    else:
        sw_test_list = ["SW_BOOT", "SW_SHUTDOWN"]
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        for test in sw_test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "SW_BOOT":
                ret = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_sw_boot(slot)
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES100IBM:
                    if ret:
                        ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_gold_boot(slot)
            elif test == "SW_PROFILE"and nic_profile:
                ret = mtp_mgmt_ctrl.mtp_nic_sw_profile(slot, nic_profile)
            elif test == "SW_SHUTDOWN":
                ret = mtp_mgmt_ctrl.mtp_mgmt_nic_sw_shutdown(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SW Test: {:s}, Ignore".format(test))
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

    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.cli_log_inf("MTP Software Install Test Complete", level=0)

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

