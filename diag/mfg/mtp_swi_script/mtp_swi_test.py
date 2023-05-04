#!/usr/bin/env python

import sys
import os
import time
import pexpect
import threading
import argparse
import re
import ntpath
import traceback

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
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode


def logfile_close(filep_list):
    for fp in filep_list:
        fp.close()
    os.system("sync")


def load_mtp_cfg(cfg_yaml=None):
    mtp_chassis_cfg_file_list = list()
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/"+cfg_yaml))
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
    
def single_nic_fru_program(mtp_mgmt_ctrl, fru_cfg, slot, fail_nic_list, pass_nic_list, skip_testlist = []):
    sn = fru_cfg["SN"]
    mac = fru_cfg["MAC"]
    pn = fru_cfg["PN"]
    prog_date = str(fru_cfg["TS"])
    test_list = ["FRU_PROG"]

    dsp = FF_Stage.FF_SWI

    for skipped_test in skip_testlist:
        if skipped_test in test_list:
            test_list.remove(skipped_test)
    for test in test_list:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        # program FRU
        if test == "FRU_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn)
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown SWI Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)
            mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

def ping_precheck(mtp_mgmt_ctrl, pass_nic_list, fail_nic_list, slotA, slotB):
    # fail other slot if either in pair is failed
    if slotA in fail_nic_list or slotB in fail_nic_list:
        if slotA in fail_nic_list:
            keyA = libmfg_utils.nic_key(slotA)
            keyB = libmfg_utils.nic_key(slotB)
            mtp_mgmt_ctrl.cli_log_slot_err(slotB, "Skipping {:s} to {:s} ping test because {:s} failed".format(keyA, keyB, keyA))
        if slotB in fail_nic_list:
            keyA = libmfg_utils.nic_key(slotA)
            keyB = libmfg_utils.nic_key(slotB)
            mtp_mgmt_ctrl.cli_log_slot_err(slotA, "Skipping {:s} to {:s} ping test because {:s} failed".format(keyA, keyB, keyB))
        return False
    else:
        return True

def ping_test(mtp_mgmt_ctrl, pass_nic_list, fail_nic_list, skip_testlist):
    import itertools

    dsp = FF_Stage.FF_SWI

    ping_test_fail_list = list()
    ping_test_slots = list()
    ping_test_tuples = list()

    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot")
            continue
        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) != NIC_Type.ORTANO2:
            continue
        if slot in fail_nic_list:
            continue
        ping_test_slots.append(slot)


    if len(ping_test_slots) > 0:    
        for cnt in range(5):
            nic_start_slot = 0
            test = "PING_PRE_PAIRING"
            slot_A = nic_start_slot + (cnt * 2)
            slot_B = nic_start_slot + (cnt * 2) + 1
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot_A, test)
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot_B, test)
            if slot_A in ping_test_slots and slot_B in ping_test_slots:
                ping_test_tuples.append([slot_A, slot_B])
                sn_A = mtp_mgmt_ctrl.mtp_get_nic_sn(slot_A) 
                sn_B = mtp_mgmt_ctrl.mtp_get_nic_sn(slot_B)
                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot_A, test, start_ts)
                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot_B, test, start_ts)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot_A, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn_A, dsp, test, duration))
                mtp_mgmt_ctrl.cli_log_slot_inf(slot_B, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn_B, dsp, test, duration))
            elif slot_A in ping_test_slots and slot_B not in ping_test_slots:
                sn_A = mtp_mgmt_ctrl.mtp_get_nic_sn(slot_A)            
                mtp_mgmt_ctrl.cli_log_slot_inf(slot_A, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn_A, dsp, test))
                if slot_A not in fail_nic_list:
                    fail_nic_list.append(slot_A)
                if slot_A in pass_nic_list:
                    pass_nic_list.remove(slot_A)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot_A)
                ping_test_fail_list.append(slot_A)
                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot_A, test, start_ts)
                mtp_mgmt_ctrl.cli_log_slot_err(slot_A, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn_A, dsp, test, "FAILED", duration))
            elif slot_A not in ping_test_slots and slot_B in ping_test_slots:
                sn_B = mtp_mgmt_ctrl.mtp_get_nic_sn(slot_B)            
                mtp_mgmt_ctrl.cli_log_slot_inf(slot_B, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn_B, dsp, test))
                if slot_B not in fail_nic_list:
                    fail_nic_list.append(slot_B)
                if slot_B in pass_nic_list:
                    pass_nic_list.remove(slot_B)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot_B)
                ping_test_fail_list.append(slot_B)
                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot_B, test, start_ts)
                mtp_mgmt_ctrl.cli_log_slot_err(slot_A, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn_B, dsp, test, "FAILED", duration))

    # a = iter(ping_test_slots)
    # ping_test_tuples = zip(a,a)

    for slotA, slotB in ping_test_tuples:
        sn_A = mtp_mgmt_ctrl.mtp_get_nic_sn(slotA)
        sn_B = mtp_mgmt_ctrl.mtp_get_nic_sn(slotB)
        nic_type_A = mtp_mgmt_ctrl.mtp_get_nic_type(slotA)
        nic_type_B = mtp_mgmt_ctrl.mtp_get_nic_type(slotB)

        test_list = ["PING_PRE", "PING_TEST"]
        for skipped_test in skip_testlist:
            if skipped_test in test_list:
                test_list.remove(skipped_test)

        for test in test_list:
            mtp_mgmt_ctrl.cli_log_slot_inf(slotA, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn_A, dsp, test))
            mtp_mgmt_ctrl.cli_log_slot_inf(slotB, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn_B, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slotA, test)
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slotB, test)
            if test == "PING_PRE":
                ret = ping_precheck(mtp_mgmt_ctrl, pass_nic_list, fail_nic_list, slotA, slotB)
            elif test == "PING_TEST":
                ret = mtp_mgmt_ctrl.mtp_nic_ping_test(slotA, slotB)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slotA, test, start_ts)
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slotB, test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slotA, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn_A, dsp, test, "FAILED", duration))
                mtp_mgmt_ctrl.cli_log_slot_err(slotB, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn_B, dsp, test, "FAILED", duration))
                if slotA not in fail_nic_list:
                    fail_nic_list.append(slotA)
                if slotB not in fail_nic_list:
                    fail_nic_list.append(slotB)
                if slotA in pass_nic_list:
                    pass_nic_list.remove(slotA)
                if slotB in pass_nic_list:
                    pass_nic_list.remove(slotB)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slotA)
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slotB)
                ping_test_fail_list.append(slotA)
                ping_test_fail_list.append(slotB)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slotA, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn_A, dsp, test, duration))
                mtp_mgmt_ctrl.cli_log_slot_inf(slotB, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn_B, dsp, test, duration))

    return ping_test_fail_list

def single_nic_fw_program(mtp_mgmt_ctrl, cpld_img_file, fail_cpld_img_file, slot, sn, prog_fail_nic_list, skip_testlist):
    dsp = FF_Stage.FF_SWI
    test_list = ["CPLD_PROG", "CPLD_REF"]
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.NAPLES25OCP:
        test_list = ["CPLD_PROG"]
    if nic_type in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
        test_list = ["CPLD_PROG", "FSAFE_CPLD_PROG", "CPLD_REF"]
    if nic_type in (NIC_Type.POMONTEDELL):
        test_list = ["FPGA_PROG"]
    if nic_type in (NIC_Type.LACONA32, NIC_Type.LACONA32DELL):
        test_list = ["FPGA_PROG", "FPGA_PROG_VERIFY"]
    if nic_type == NIC_Type.ORTANO2:
        test_list = ["FSAFE_CPLD_PROG", "CPLD_REF"]
    for skip_test in skip_testlist:
        if skip_test in test_list:
            test_list.remove(skip_test)
    for test in test_list:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        # program CPLD
        if test == "CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file, dl_step=False)
        # program all FPGA partitions
        elif test == "FPGA_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_fpga(slot)
        # verify program of all FPGA partitions
        elif test == "FPGA_PROG_VERIFY":
            ret = mtp_mgmt_ctrl.mtp_verify_nic_fpga(slot)
        # program failsafe CPLD
        elif test == "FSAFE_CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_failsafe_cpld(slot, fail_cpld_img_file)
        # refresh CPLD
        elif test == "CPLD_REF":
            ret = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(slot)
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            prog_fail_nic_list.append(slot)
            mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


def single_nic_sec_cpld_program(mtp_mgmt_ctrl, sec_cpld_img_file, slot, sn, prog_fail_nic_list, skip_testlist):
    dsp = FF_Stage.FF_SWI

    test_list = ["NIC_INIT", "SEC_CPLD_PROG", "SEC_CPLD_REF"]
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.NAPLES25OCP:
        test_list = ["NIC_INIT", "SEC_CPLD_PROG"]
    if nic_type in ELBA_NIC_TYPE_LIST:
        test_list = ["NIC_INIT", "SEC_CPLD_PROG", "SEC_CPLD_REF"]
    if nic_type in FPGA_TYPE_LIST:
        test_list = ["NIC_INIT"]
    if nic_type == NIC_Type.ORTANO2 or nic_type == NIC_Type.ORTANO2ADIMSFT:
        test_list = ["NIC_INIT"]

    for skip_test in skip_testlist:
        if skip_test in test_list:
            test_list.remove(skip_test)
    for test in test_list:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        # program secure cpld
        if test == "SEC_CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_sec_cpld(slot, sec_cpld_img_file)
        elif test == "SEC_CPLD_REF":
            ret = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(slot)
        # nic diag init status
        elif test == "NIC_INIT":
            ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown SWI Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            prog_fail_nic_list.append(slot)
            mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


def single_nic_copy_gold_program(mtp_mgmt_ctrl, gold_img_file, cert_img_file, slot, sn, prog_fail_nic_list, skip_testlist):
    dsp = FF_Stage.FF_SWI
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    test_list = ["NIC_INIT", "SEC_CPLD_VERIFY", "COPY_GOLD"]
    if nic_type == NIC_Type.ORTANO2ADIIBM:
        test_list = ["NIC_INIT", "SEC_CPLD_VERIFY", "COPY_GOLD", "COPY_CERT"]
    for skip_test in skip_testlist:
        if skip_test in test_list:
            test_list.remove(skip_test)
    for test in test_list:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        if test == "SEC_CPLD_VERIFY":
            ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot, sec_cpld=True, dl_step=False)
        elif test == "COPY_GOLD":
            ret = mtp_mgmt_ctrl.mtp_copy_nic_gold(slot, gold_img_file)
        elif test == "COPY_CERT":
            ret = mtp_mgmt_ctrl.mtp_copy_nic_cert(slot, cert_img_file, directory="/data/")
        elif test == "NIC_INIT":
            ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown SW Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            prog_fail_nic_list.append(slot)
            mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


def single_nic_emmc_program(mtp_mgmt_ctrl, emmc_img_file, slot, sn, prog_fail_nic_list, skip_testlist):
    dsp = FF_Stage.FF_SWI
    test_list = ["SW_INSTALL"]
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.ORTANO2ADIIBM:
        test_list = []
    for skip_test in skip_testlist:
        if skip_test in test_list:
            test_list.remove(skip_test)
    for test in test_list:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        # program sw image onto EMMC
        if test == "SW_INSTALL":
            ret = mtp_mgmt_ctrl.mtp_program_nic_emmc(slot, emmc_img_file)
        else:       
            mtp_mgmt_ctrl.cli_log_err("Unknown SW Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            prog_fail_nic_list.append(slot)
            mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

def single_nic_gold_program(mtp_mgmt_ctrl, gold_img_file, slot, sn, prog_fail_nic_list, skip_testlist):
    dsp = FF_Stage.FF_SWI
    test_list = ["GOLDFW_PROG"]
    for skip_test in skip_testlist:
        if skip_test in test_list:
            test_list.remove(skip_test)
    for test in test_list:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        if test == "GOLDFW_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_gold(slot, gold_img_file)
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown SW Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            prog_fail_nic_list.append(slot)
            mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


def main():
    parser = argparse.ArgumentParser(description="MTP Software Install Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--image", help="NIC eMMC image(s)", nargs="*", required=True, default=[])
    parser.add_argument("--profile", help="NIC Profile")
    parser.add_argument("--swpn", help="Software Part Number(s)", nargs="*", default=[])
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--fail-slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)

    nic_profile = None
    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid
    if args.image:
        img_file_list = args.image
    if args.profile:
        #nic_profile = args.profile
        nic_profile = ntpath.basename(args.profile)
    if args.swpn:
        sw_pn_list = args.swpn
    if not args.skip_test:
        args.skip_test = []

    mtp_cfg_db = load_mtp_cfg(args.mtpcfg)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, sys.stdout, None, [])
    # local logfiles
    mtp_script_dir, open_file_track_list = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True)

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    # get the absolute file path
    emmc_img_file_list = {"":""}
    for sw_pn, sw_img in zip(sw_pn_list, img_file_list):
        emmc_img_file_list[sw_pn] = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + sw_img

    try:
        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, stage=FF_Stage.FF_SWI):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            logfile_close(open_file_track_list)
            return

        fail_nic_list = list()
        pass_nic_list = list()

        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        # Add failed slots from toplevel
        if args.fail_slots:
            for slot in args.fail_slots:
                fail_nic_list.append(int(slot))

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            if not nic_prsnt_list[slot]:
                continue
            if slot not in pass_nic_list:
                pass_nic_list.append(slot)

        # power cycle all nic
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.mtp_power_on_nic(pass_nic_list)

        dsp = FF_Stage.FF_SWI
        NAPLES100IBM = 0

        # Set Naples25SWM test mode
        mtp_mgmt_ctrl.mtp_set_swmtestmode(Swm_Test_Mode.SW_DETECT)

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            if not nic_prsnt_list[slot]:
                continue
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
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
                    continue
                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)
                    mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                    break
                else:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

        # if "CONSOLE_BOOT" not in args.skip_test:
        #     # power cycle all nic
        #     mtp_mgmt_ctrl.mtp_power_cycle_nic(pass_nic_list)

        if not mtp_mgmt_ctrl.mtp_nic_diag_init(pass_nic_list, nic_util=True):
            mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                if not nic_prsnt_list[slot]:
                    continue
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        if "SCAN_VERIFY" not in args.skip_test:
            # load the barcode config file made in toplevel
            scan_cfg_file = mtp_script_dir + "/" + MTP_DIAG_Logfile.SCAN_BARCODE_FILE
            scanned_fru_cfg_dict = libmfg_utils.load_cfg_from_yaml(scan_cfg_file)
            if mtp_id not in scanned_fru_cfg_dict:
                mtp_mgmt_ctrl.cli_log_err("Not found information for MTP: {:s} in scan config file {:s}".format(mtp_id, scan_cfg_file), level=0)
                # fail all the mtp slots instead of exit by calling libmfg_utils.sys_exit, and fill scanned_fru_cfg with no valid flag
                scanned_fru_cfg = dict()
                for slot in range(MTP_Const.MTP_SLOT_NUM):
                    key = libmfg_utils.nic_key(slot)
                    if not nic_prsnt_list[slot]:
                        continue
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)
            else:
                scanned_fru_cfg = scanned_fru_cfg_dict[mtp_id]
            tmp_fru_cfg = mtp_mgmt_ctrl.mtp_construct_nic_fru_config(fail_nic_list)
            fru_reprogram_list = mtp_mgmt_ctrl.mtp_scan_verify(tmp_fru_cfg, scanned_fru_cfg, pass_nic_list, fail_nic_list, dsp, ignore_pn_rev=True)

            # reload the barcode config file
            nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(MTP_DIAG_Logfile.SCAN_BARCODE_FILE)

            nic_thread_list = list()
            for slot in fru_reprogram_list:
                key = libmfg_utils.nic_key(slot)
                valid = nic_fru_cfg[mtp_id][key]["VALID"]
                if str.upper(valid) != "YES":
                    continue
                nic_thread = threading.Thread(target = single_nic_fru_program, args = (mtp_mgmt_ctrl,
                                                                                      nic_fru_cfg[mtp_id][key],
                                                                                      slot,
                                                                                      fail_nic_list,
                                                                                      pass_nic_list,
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

            for slot in fru_reprogram_list:
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if not mtp_mgmt_ctrl.mtp_nic_fru_init(slot, True, nic_type, False):
                    mtp_mgmt_ctrl.cli_log_err("FRU re-init failed", level=0)

        check_naples_pn = "SCAN_VERIFY" not in args.skip_test

        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        test_list = ["SW_PN_CHECK"]
        for skipped_test in args.skip_test:
            if skipped_test in test_list:
                test_list.remove(skipped_test)
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue

            for test in test_list:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)

                if test == "SW_PN_CHECK":
                    ret = mtp_mgmt_ctrl.mtp_nic_sw_pn_search(slot, sw_pn_list, check_naples_pn)

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


        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot")
                continue
            if slot in fail_nic_list:
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sw_pn = mtp_mgmt_ctrl.mtp_get_nic_sw_pn(slot)
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[nic_type]
            sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img[nic_type]
            gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[nic_type]

            if nic_type == NIC_Type.ORTANO2 and mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0015"]
            if nic_type == NIC_Type.ORTANO2ADI:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0026"]
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0028"]
            if nic_type == NIC_Type.ORTANO2ADIMSFT:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0034"]
            if nic_type == NIC_Type.NAPLES25SWM:
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot)]
                sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot)]
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot)]
            if nic_type == NIC_Type.NAPLES100HPE and mtp_mgmt_ctrl.mtp_is_nic_cloud(slot):
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img["P41854"]
                sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img["P41854"]
            if nic_type in ELBA_NIC_TYPE_LIST:
                fail_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img[nic_type]
            else:
                fail_cpld_img_file = ""
            if nic_type == NIC_Type.ORTANO2ADI:
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img["68-0026"]
                sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img["68-0026"]
                fail_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img["68-0026"]
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img["68-0028"]
                sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img["68-0028"]
                fail_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img["68-0028"]
            if nic_type == NIC_Type.ORTANO2ADIMSFT:
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img["68-0034"]
                sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img["68-0034"]
                fail_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img["68-0034"]

            emmc_img_file = emmc_img_file_list[sw_pn]
            if emmc_img_file:
                emmc_img_chksum = mtp_mgmt_ctrl.mtp_get_file_md5sum(emmc_img_file)
            gold_img_chksum = mtp_mgmt_ctrl.mtp_get_file_md5sum(gold_img_file)

            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Software Program Matrix:")
            if nic_type in FPGA_TYPE_LIST:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FPGA main image: " + os.path.basename(cpld_img_file))
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FPGA gold image: " + os.path.basename(fail_cpld_img_file))
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Non Secure CPLD image: " + os.path.basename(cpld_img_file))
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Secure CPLD image: " + os.path.basename(sec_cpld_img_file))
                if fail_cpld_img_file:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Failsafe CPLD image: " + os.path.basename(fail_cpld_img_file))
            if nic_type != NIC_Type.ORTANO2ADIIBM:
                if emmc_img_file:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "MainFW image: " + os.path.basename(emmc_img_file))
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "MainFW MD5 checksum: " + emmc_img_chksum)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "MainFW image: " + "N/A")
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "MainFW MD5 checksum: " + "N/A")
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "GoldFW image: " + os.path.basename(gold_img_file))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "GoldFW MD5 checksum: " + gold_img_chksum)
            if nic_profile:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Profile: " + os.path.basename(nic_profile))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Software Program Matrix end\n")

            if nic_type == NIC_Type.NAPLES100IBM:
                NAPLES100IBM = 1

            test_list = ["NIC_POWER", "NIC_TYPE", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT"]
            for skipped_test in args.skip_test:
                if skipped_test in test_list:
                    test_list.remove(skipped_test)

            for test in test_list:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                # nic power status check
                if test == "NIC_POWER":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
                # nic type check
                elif test == "NIC_TYPE":
                    ret = mtp_mgmt_ctrl.mtp_nic_type_test(slot)
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


        # ping_test_fail_list = ping_test(mtp_mgmt_ctrl, pass_nic_list, fail_nic_list, args.skip_test)

        # program the NIC firmware
        nic_thread_list = list()
        prog_fail_nic_list = list()
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[nic_type]
            if nic_type == NIC_Type.NAPLES25SWM:
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot)]
            if nic_type == NIC_Type.NAPLES100HPE and mtp_mgmt_ctrl.mtp_is_nic_cloud(slot):
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img["P41854"]
            failsafe_cpld_img_file = ""
            if nic_type in ELBA_NIC_TYPE_LIST:
                failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img[nic_type]
            if nic_type == NIC_Type.ORTANO2ADI:
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img["68-0026"]
                failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img["68-0026"]
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img["68-0028"]
                failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img["68-0028"]
            if nic_type == NIC_Type.ORTANO2ADIMSFT:
                cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img["68-0034"]
                failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.fail_cpld_img["68-0034"]

            nic_thread = threading.Thread(target = single_nic_fw_program, args = (mtp_mgmt_ctrl,
                                                                                  cpld_img_file,
                                                                                  failsafe_cpld_img_file,
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
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)

        # # power cycle all nic
        # mtp_mgmt_ctrl.mtp_power_cycle_nic(pass_nic_list)

        if not mtp_mgmt_ctrl.mtp_nic_esec_write_protect(pass_nic_list=pass_nic_list ,fail_nic_list=fail_nic_list ,enable=False, dsp=dsp):
            mtp_mgmt_ctrl.cli_log_err("Disable ESEC Write Protection failed", level=0)

        # Ensure nic_util and nic_arm as needed for elba's efuse script
        if "EFUSE_PROG" not in args.skip_test:
            if not mtp_mgmt_ctrl.mtp_nic_diag_init(pass_nic_list):
                mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
            for slot in range(MTP_Const.MTP_SLOT_NUM):
                if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                    if not nic_prsnt_list[slot]:
                        continue
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)

        # Efuse programming for Elba
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue

            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type not in ELBA_NIC_TYPE_LIST:
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            test_list = ["NIC_INIT", "EFUSE_PROG"]
            for skipped_test in args.skip_test:
                if skipped_test in test_list:
                    test_list.remove(skipped_test)
            for test in test_list:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                if test == "EFUSE_PROG":
                    ret = mtp_mgmt_ctrl.mtp_program_nic_efuse(slot)
                elif test == "NIC_INIT":
                    ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
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

        # Secure key programming
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                continue
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

            test_list = ["SEC_KEY_PROG"]
            for skipped_test in args.skip_test:
                if skipped_test in test_list:
                    test_list.remove(skipped_test)
            for test in test_list:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                if test == "SEC_KEY_PROG":
                    ret = mtp_mgmt_ctrl.mtp_program_nic_sec_key(slot)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
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

        # # power cycle NIC
        # if "EFUSE_PROG" not in args.skip_test and "SEC_KEY_PROG" not in args.skip_test:
        #     mtp_mgmt_ctrl.mtp_power_cycle_nic(pass_nic_list)

        if not mtp_mgmt_ctrl.mtp_nic_diag_init(pass_nic_list):
            mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                if not nic_prsnt_list[slot]:
                    continue
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # program the NIC Secure CPLD
        nic_thread_list = list()
        prog_fail_nic_list = list()
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img[nic_type]
            if nic_type == NIC_Type.NAPLES25SWM:
                sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot)]
            if nic_type == NIC_Type.NAPLES100HPE and mtp_mgmt_ctrl.mtp_is_nic_cloud(slot):
                sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img["P41854"]
            if nic_type == NIC_Type.ORTANO2ADI:
                sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img["68-0026"]
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img["68-0028"]
            if nic_type == NIC_Type.ORTANO2ADIMSFT:
                sec_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.sec_cpld_img["68-0034"]

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
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)

        mtp_mgmt_ctrl.mtp_power_cycle_nic(pass_nic_list)

        # Secure CPLD Check
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                continue
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type in FPGA_TYPE_LIST:
                # cant power up fpga only in 3.3v
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            test_list = ["SEC_PROG_VERIFY"]
            for skipped_test in args.skip_test:
                if skipped_test in test_list:
                    test_list.remove(skipped_test)
            for test in test_list:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                if test == "SEC_PROG_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_sec_cpld(slot)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
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

        if not mtp_mgmt_ctrl.mtp_nic_esec_write_protect(pass_nic_list=pass_nic_list ,fail_nic_list=fail_nic_list ,enable=True, dsp=dsp):
            mtp_mgmt_ctrl.cli_log_err("Enable ESEC Write Protection failed", level=0)


        if not mtp_mgmt_ctrl.mtp_nic_diag_init(pass_nic_list):
            mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                if not nic_prsnt_list[slot]:
                    continue
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Copy the NIC Gold image
        nic_thread_list = list()
        prog_fail_nic_list = list()
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[nic_type]
            
            cert_img_file = ""
            if nic_type == NIC_Type.ORTANO2 and mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0015"]
            if nic_type == NIC_Type.ORTANO2ADI:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0026"]
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0028"]
                cert_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cert_img["68-0028"]
            if nic_type == NIC_Type.ORTANO2ADIMSFT:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0034"]
            if nic_type == NIC_Type.NAPLES25SWM:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot)]

            nic_thread = threading.Thread(target = single_nic_copy_gold_program, args = (mtp_mgmt_ctrl,
                                                                                    gold_img_file,
                                                                                    cert_img_file,
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
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)


        # program the NIC EMMC image
        nic_thread_list = list()
        prog_fail_nic_list = list()
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            sw_pn = mtp_mgmt_ctrl.mtp_get_nic_sw_pn(slot)
            emmc_img_file = emmc_img_file_list[sw_pn]
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
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)


        # program the NIC Gold image
        nic_thread_list = list()
        prog_fail_nic_list = list()
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[nic_type]

            if nic_type == NIC_Type.ORTANO2 and mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0015"]
            if nic_type == NIC_Type.ORTANO2ADI:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0026"]
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0028"]
            if nic_type == NIC_Type.ORTANO2ADIMSFT:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img["68-0034"]
            if nic_type == NIC_Type.NAPLES25SWM:
                gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.goldfw_img[mtp_mgmt_ctrl.mtp_lookup_nic_swm_type(slot)]

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

        # power cycle all nic
        mtp_mgmt_ctrl.mtp_power_cycle_nic(pass_nic_list)
        
        # verify the NIC goldfw boot
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            test_list = ["GOLDFW_BOOT"]
            for skipped_test in args.skip_test:
                if skipped_test in test_list:
                    test_list.remove(skipped_test)
            for test in test_list:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                if test == "GOLDFW_BOOT":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_gold_boot(slot)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
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

        # power cycle NIC
        if "GOLDFW_BOOT" not in args.skip_test:
            mtp_mgmt_ctrl.mtp_power_cycle_nic(pass_nic_list)
        
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
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                continue
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)                

            test_list = ["SET_MAINFW", "SW_CLEANUP"]
            if nic_type in ELBA_NIC_TYPE_LIST:
                test_list = ["CFG_VERIFY","SET_MAINFW", "SW_CLEANUP"]
            if nic_type in FPGA_TYPE_LIST:
                test_list = ["CFG_VERIFY", "SET_EXTDIAGFW", "SW_CLEANUP"]
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                test_list = ["BOARD_CONFIG_CERT", "CFG_VERIFY", "SW_CLEANUP"]
                cert_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cert_img["68-0028"]
            for skipped_test in args.skip_test:
                if skipped_test in test_list:
                    test_list.remove(skipped_test)

            for test in test_list:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                if test == "SET_MAINFW":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_mainfw_boot(slot)
                elif test == "SET_DIAGFW":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(slot)
                elif test == "BOARD_CONFIG_CERT":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_set_board_config_cert(slot, cert_img_file, directory="/data/")
                elif test == "CFG_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_nic_cfg_verify(slot)
                elif test == "SW_CLEANUP":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_nic_sw_cleanup_shutdown(slot)
                elif test == "SET_EXTDIAGFW":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_extdiag_boot(slot)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
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

        # power cycle NIC
        mtp_mgmt_ctrl.mtp_power_cycle_nic(pass_nic_list)
        libmfg_utils.count_down(MTP_Const.NIC_SW_BOOTUP_DELAY)

        # Verify the NIC Software boot
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sw_pn = mtp_mgmt_ctrl.mtp_get_nic_sw_pn(slot)
            isCloud =  mtp_mgmt_ctrl.check_is_cloud_software_image(slot, sw_pn)

            sw_test_list = ["SW_BOOT", "SW_SHUTDOWN"]
            if isCloud or nic_type == NIC_Type.NAPLES100IBM:
                sw_test_list = ["SW_BOOT", "SET_GOLDFW", "SW_SHUTDOWN"]
            if nic_type == NIC_Type.ORTANO2 and not mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
                sw_test_list = ["SW_BOOT", "SW_MODE_SWITCH", "SW_BOOT", "SW_SHUTDOWN"]
            if nic_type == NIC_Type.ORTANO2ADI or nic_type == NIC_Type.ORTANO2ADICR:
                sw_test_list = ["SW_BOOT", "SW_SHUTDOWN"]
            if nic_type == NIC_Type.ORTANO2ADIMSFT:
                sw_test_list = ["SW_BOOT", "SW_MODE_SWITCH", "SW_BOOT", "SW_SHUTDOWN"]
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                sw_test_list = []
            if nic_type in FPGA_TYPE_LIST:
                sw_test_list = ["EXTDIAG_BOOT_SMODE", "EXTDIAG_BOOT", "KEYS_CHECK", "SW_SHUTDOWN"]
            if nic_profile:
                if "SW_PROFILE" not in sw_test_list:
                    sw_test_list.insert(-1, "SW_MGMT_INIT")
                    sw_test_list.insert(-1, "SW_PROFILE")

            for skipped_test in args.skip_test:
                if skipped_test in sw_test_list:
                    sw_test_list.remove(skipped_test)
            for test in sw_test_list:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                if test == "SW_BOOT":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_sw_boot(slot)
                elif test == "DIAG_BOOT":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_diag_boot(slot)
                elif test == "EXTDIAG_BOOT":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_extdiag_boot(slot)
                elif test == "EXTDIAG_BOOT_SMODE":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_extdiag_smode_boot(slot)
                elif test == "SW_MGMT_INIT" and nic_profile:
                    ret = mtp_mgmt_ctrl.mtp_nic_sw_mgmt_init(slot)
                elif test == "SW_PROFILE" and nic_profile:
                    ret = mtp_mgmt_ctrl.mtp_nic_sw_profile(slot, nic_profile)
                elif test == "SW_MODE_SWITCH":
                    ret = mtp_mgmt_ctrl.mtp_nic_sw_mode_switch(slot)
                    ret &= mtp_mgmt_ctrl.mtp_nic_sw_mode_switch_verify(slot)
                elif test == "PDSCTL_SYSTEM":
                    ret = mtp_mgmt_ctrl.mtp_pdsctl_system_show(slot)
                elif test == "SET_GOLDFW":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_goldfw_boot(slot)
                elif test == "SET_EXTOS":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_extos_boot(slot)
                elif test == "SW_SHUTDOWN":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_nic_sw_shutdown(slot, sw_pn)
                elif test == "KEYS_CHECK":
                    ret = mtp_mgmt_ctrl.mtp_nic_read_secure_boot_keys(slot)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown SWI Test: {:s}, Ignore".format(test))
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

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        # err_msg = str(e)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)

    logfile_close(open_file_track_list)
    return

if __name__ == "__main__":
    main()

