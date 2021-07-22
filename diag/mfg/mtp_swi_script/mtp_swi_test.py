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
from libmfg_cfg import NIC_IMAGES
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
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg, slots_to_skip=mtp_slots_to_skip)
    return mtp_mgmt_ctrl
    
def single_nic_fw_program(mtp_mgmt_ctrl, cpld_img_file, slot, sn, prog_fail_nic_list, skip_testlist):
    dsp = FF_Stage.FF_SWI
    testseqlist = ["CPLD_PROG", "CPLD_REF"]                                                                
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.NAPLES25OCP:
        testseqlist = ["CPLD_PROG"]
    if nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
        testseqlist = ["CPLD_PROG", "CPLD_REF", "NIC_PWRCYC"]
    for skip_test in skip_testlist:
        if skip_test in testseqlist:
            testseqlist.remove(skip_test)
    for test in testseqlist:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        # program CPLD
        if test == "CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
        # refresh CPLD
        elif test == "CPLD_REF":
            ret = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(slot)
        # extra powercycle to refresh CPLD
        elif test == "NIC_PWRCYC":
            ret = mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
            ret &= mtp_mgmt_ctrl.mtp_power_on_single_nic(slot)
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
            continue
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


def single_nic_sec_cpld_program(mtp_mgmt_ctrl, sec_cpld_img_file, slot, sn, prog_fail_nic_list, skip_testlist):
    dsp = FF_Stage.FF_SWI

    testseqlist = ["SEC_CPLD_PROG", "SEC_CPLD_REF"]                                                                
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.NAPLES25OCP:
        testseqlist = ["SEC_CPLD_PROG"]
    if nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
        testseqlist = ["SEC_CPLD_PROG", "SEC_CPLD_REF", "NIC_PWRCYC"]
    for skip_test in skip_testlist:
        if skip_test in testseqlist:
            testseqlist.remove(skip_test)
    for test in testseqlist:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        # program secure cpld
        if test == "SEC_CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_sec_cpld(slot, sec_cpld_img_file)
        elif test == "SEC_CPLD_REF":
            ret = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(slot)
        # extra powercycle to refresh CPLD
        elif test == "NIC_PWRCYC":
            ret = mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
            ret &= mtp_mgmt_ctrl.mtp_power_on_single_nic(slot)
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


def single_nic_copy_gold_program(mtp_mgmt_ctrl, gold_img_file, slot, sn, prog_fail_nic_list, skip_testlist):
    dsp = FF_Stage.FF_SWI
    testseqlist = ["SEC_CPLD_VERIFY", "COPY_GOLD"]
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    for skip_test in skip_testlist:
        if skip_test in testseqlist:
            testseqlist.remove(skip_test)
    for test in testseqlist:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        if test == "SEC_CPLD_VERIFY":
            ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot, sec_cpld=True)
        elif test == "COPY_GOLD":
            ret = mtp_mgmt_ctrl.mtp_copy_nic_gold(slot, gold_img_file)
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


def single_nic_emmc_program(mtp_mgmt_ctrl, emmc_img_file, slot, sn, prog_fail_nic_list, skip_testlist):
    dsp = FF_Stage.FF_SWI
    testseqlist = ["SW_INSTALL"]
    for skip_test in skip_testlist:
        if skip_test in testseqlist:
            testseqlist.remove(skip_test)
    for test in testseqlist:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        # program sw image onto EMMC
        if test == "SW_INSTALL":
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES100:
                ret = mtp_mgmt_ctrl.mtp_program_nic_emmc_naples100(slot, emmc_img_file)
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

def single_nic_gold_program(mtp_mgmt_ctrl, gold_img_file, slot, sn, prog_fail_nic_list, skip_testlist):
    dsp = FF_Stage.FF_SWI
    testseqlist = ["GOLD_PROG"]
    for skip_test in skip_testlist:
        if skip_test in testseqlist:
            testseqlist.remove(skip_test)
    for test in testseqlist:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        if test == "GOLD_PROG":
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES100:
                ret = mtp_mgmt_ctrl.mtp_program_nic_gold_naples100(slot, gold_img_file)
            else:
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


def main():
    parser = argparse.ArgumentParser(description="MTP Software Install Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--image", help="NIC eMMC image", required=True)
    parser.add_argument("--profile", help="NIC Profile")
    parser.add_argument("--swpn", help="Software Part Number")
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])

    nic_profile = None
    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid
    if args.image:
        img_file = args.image
    if args.profile:
        #nic_profile = args.profile
        nic_profile = ntpath.basename(args.profile)
    if args.swpn:
        sw_pn = args.swpn 
    if not args.skip_test:
        args.skip_test = []

    mtp_cfg_db = load_mtp_cfg()

    # local log files
    log_filep_list = list()
    test_log_file = "mtp_test.log"
    test_log_filep = open(test_log_file, "w+", buffering=0)
    log_filep_list.append(test_log_filep)

    diag_log_file = "mtp_diag.log"
    diag_log_filep = open(diag_log_file, "w+", buffering=0)
    log_filep_list.append(diag_log_filep)

                              
    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = "mtp_{:s}_diag.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, "w+", buffering=0)
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list)

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    # get the absolute file path
    emmc_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + img_file

    if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, stage=FF_Stage.FF_SWI):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
        logfile_close(log_filep_list)
        return

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

    # Set Naples25SWM test mode
    mtp_mgmt_ctrl.mtp_set_swmtestmode(Swm_Test_Mode.SW_DETECT)

    if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_util=True):
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return
        
    dsp = FF_Stage.FF_SWI
    pass_nic_list = list()
    fail_nic_list = list()
    NAPLES100IBM = 0


    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot")
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        pass_nic_list.append(slot)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[card_type]
        sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img[card_type]
        gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[card_type]

        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Software Program Matrix:")
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Non Secure CPLD image: " + os.path.basename(cpld_img_file))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Secure CPLD image: " + os.path.basename(sec_cpld_img_file))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Main image: " + os.path.basename(emmc_img_file))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Gold image: " + os.path.basename(gold_img_file))
        if nic_profile:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Profile: " + os.path.basename(nic_profile))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Software Program Matrix end\n")

        if card_type == NIC_Type.NAPLES100IBM:
            NAPLES100IBM = 1

        test_list = ["SW_PN_CHECK", "NIC_POWER", "NIC_TYPE", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT", "NAPLES_PN_VERIFY"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)

        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "SW_PN_CHECK":
                ret = mtp_mgmt_ctrl.check_swi_software_image(slot, sw_pn)
            # nic power status check
            elif test == "NIC_POWER":
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
            elif test == "NAPLES_PN_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_naples_pn(slot)
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
            
    # program the NIC firmware
    nic_thread_list = list()
    prog_fail_nic_list = list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[card_type]
        nic_thread = threading.Thread(target = single_nic_fw_program, args = (mtp_mgmt_ctrl,
                                                                              cpld_img_file,
                                                                              slot,
                                                                              sn,
                                                                              prog_fail_nic_list,
                                                                              args.skip_test))
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

    # Failure analysis
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot)

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    # Ensure nic_util and nic_arm as needed for elba's efuse script
    if "EFUSE_PROG" not in args.skip_test:
        if not mtp_mgmt_ctrl.mtp_nic_diag_init():
            mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            mtp_mgmt_ctrl.mtp_chassis_shutdown()
            logfile_close(log_filep_list)
            return

    # Efuse programming for Elba
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue
        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) != NIC_Type.ORTANO2:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        test_list = ["EFUSE_PROG"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)
        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "EFUSE_PROG":
                ret = mtp_mgmt_ctrl.mtp_program_nic_efuse(slot)
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
        test_list = ["SEC_KEY_PROG"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)
        for test in test_list:
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
    if "EFUSE_PROG" not in args.skip_test and "SEC_KEY_PROG" not in args.skip_test:
        mtp_mgmt_ctrl.mtp_power_cycle_nic()

    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
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
        sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img[card_type]

        nic_thread = threading.Thread(target = single_nic_sec_cpld_program, args = (mtp_mgmt_ctrl,
                                                                                    sec_cpld_img_file,
                                                                                    slot,
                                                                                    sn,
                                                                                    prog_fail_nic_list,
                                                                                    args.skip_test))
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
        test_list = ["SEC_PROG_VERIFY"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)
        for test in test_list:
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

    # Failure analysis
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot)

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    # Copy the NIC Gold image
    nic_thread_list = list()
    prog_fail_nic_list = list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[card_type]

        nic_thread = threading.Thread(target = single_nic_copy_gold_program, args = (mtp_mgmt_ctrl,
                                                                                gold_img_file,
                                                                                slot,
                                                                                sn,
                                                                                prog_fail_nic_list,
                                                                                args.skip_test))
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

    # Failure analysis
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot)

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
                                                                                prog_fail_nic_list,
                                                                                args.skip_test))
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

    # Failure analysis
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot)

    # program the NIC Gold image
    nic_thread_list = list()
    prog_fail_nic_list = list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[card_type]

        nic_thread = threading.Thread(target = single_nic_gold_program, args = (mtp_mgmt_ctrl,
                                                                                gold_img_file,
                                                                                slot,
                                                                                sn,
                                                                                prog_fail_nic_list,
                                                                                args.skip_test))
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
        if slot in pass_nic_list:
            pass_nic_list.remove(slot)
        if slot not in fail_nic_list:
            fail_nic_list.append(slot)

    # Failure analysis
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot in fail_nic_list:
            libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot)

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()
    
    # verify the NIC goldfw boot
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        test_list = ["GOLD_BOOT"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)
        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "GOLD_BOOT":
                ret = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_gold_boot(slot)
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
    if "GOLD_BOOT" not in args.skip_test:
        mtp_mgmt_ctrl.mtp_power_cycle_nic()
    
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
        if slot in pass_nic_list:
            pass_nic_list.remove(slot)
        if slot not in fail_nic_list:
            fail_nic_list.append(slot)

    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        test_list = ["SET_MAINFW", "SW_CLEANUP"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)

        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "SET_MAINFW":
                ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_mainfw_boot(slot)
            elif test == "SW_CLEANUP":
                ret = mtp_mgmt_ctrl.mtp_mgmt_nic_sw_cleanup_shutdown(slot)
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

    # Set uboot env variables
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if card_type != NIC_Type.ORTANO and card_type != NIC_Type.ORTANO2:
            continue
        if mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
            continue

        test_list = ["UBOOT_ENV"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)
        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "UBOOT_ENV":
                ret = mtp_mgmt_ctrl.mtp_mgmt_set_elba_uboot_env(slot)
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
    libmfg_utils.count_down(MTP_Const.NIC_SW_BOOTUP_DELAY)

    # INIt the sw mgmt port
    if not NAPLES100IBM:
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
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            logfile_close(log_filep_list)
            return

        if not mtp_mgmt_ctrl.mtp_mgmt_nic_mac_validate():
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP detect duplicate mac address, test abort...")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            logfile_close(log_filep_list)
            return

    # Verify the NIC Software boot
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        isCloud =  mtp_mgmt_ctrl.check_is_cloud_software_image(slot, sw_pn)

        sw_test_list = ["SW_BOOT", "SW_SHUTDOWN"]
        if isCloud or card_type == NIC_Type.NAPLES100IBM:
            sw_test_list = ["SW_BOOT", "SET_GOLDFW", "SW_SHUTDOWN"]
        if card_type == NIC_Type.ORTANO2 and not mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
            sw_test_list = ["SW_BOOT", "SW_MODE_SWITCH", "SW_BOOT", "SW_SHUTDOWN"]
        if nic_profile:
            if "SW_PROFILE" not in sw_test_list:
                sw_test_list.insert(-1, "SW_PROFILE")

        for skipped_test in args.skip_test:
            if skipped_test in sw_test_list:
                sw_test_list.remove(skipped_test)
        for test in sw_test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if test == "SW_BOOT":
                ret = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_sw_boot(slot)
            elif test == "SW_PROFILE" and nic_profile:
                ret = mtp_mgmt_ctrl.mtp_nic_sw_profile(slot, nic_profile)
            elif test == "SW_MODE_SWITCH":
                ret = mtp_mgmt_ctrl.mtp_nic_sw_mode_switch(slot)
                ret &= mtp_mgmt_ctrl.mtp_nic_sw_mode_switch_verify(slot)
            elif test == "PERF_MODE":
                if isCloud:
                    # powercycle out of mainfw into goldfw, if Cloud.
                    mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
                    mtp_mgmt_ctrl.mtp_power_on_single_nic(slot)
                    mtp_mgmt_ctrl.mtp_nic_mgmt_seq_init(fpo=True)
                    if not mtp_mgmt_ctrl.mtp_mgmt_nic_mac_validate():
                        mtp_mgmt_ctrl.cli_log_err("No connection to NICs", level=0)
                        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                        return
                ret = mtp_mgmt_ctrl.mtp_nic_emmc_set_perf_mode(slot)
            elif test == "SET_GOLDFW":
                ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_goldfw_boot(slot)
            elif test == "SW_SHUTDOWN":
                ret = mtp_mgmt_ctrl.mtp_mgmt_nic_sw_shutdown(slot, sw_pn)
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

