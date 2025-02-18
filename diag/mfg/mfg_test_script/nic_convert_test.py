#!/usr/bin/env python3

import sys
import os
import threading
import argparse
import re
import traceback

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import PSLC_MODE_TYPE_LIST
from libmfg_cfg import CAPRI_NIC_TYPE_LIST
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import GIGLIO_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmfg_cfg import MFG_VALID_NIC_TYPE_LIST
from libmfg_cfg import DRY_RUN
from libdefs import FF_Stage
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode
import image_control
import testlog
import test_utils
import parallelize
import scanning

def logfile_close(filep_list):
    for fp in filep_list:
        fp.close()
    os.system("sync")


def logfile_cleanup(file_list):
    for _file in file_list:
        os.system("rm -rf {:s}".format(_file))


def load_mtp_cfg(cfg_yaml=None):
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/"+cfg_yaml))
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, skip_slots=[]):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    if len(skip_slots) > 0 and not mtp_cfg_db.set_mtp_slots_to_skip(mtp_id, skip_slots):
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to set skip slots")
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg, slots_to_skip=mtp_slots_to_skip)
    return mtp_mgmt_ctrl

#### functions for keeping old behavior. these can be eliminated if we move these steps into corresponding libmtp function.
@parallelize.parallel_nic_using_ssh
def dl_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)

@parallelize.parallel_nic_using_ssh
def dl_fail_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_failsafe_cpld(slot, failsafe_cpld_img_file)

@parallelize.parallel_nic_using_ssh
def dl_ibm_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_adi_ibm_cpld(slot, cpld_img_file)

@parallelize.parallel_nic_using_ssh
def dl_ibm_fail_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_adi_ibm_failsafe_cpld(slot, failsafe_cpld_img_file)

def main():
    parser = argparse.ArgumentParser(description="NIC Convert Test Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip_test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("--skip_slots", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid

    mtp_cfg_db = load_mtp_cfg(args.mtpcfg)

    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    if not args.skip_test:
        args.skip_test = []

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, sys.stdout, None, [], skip_slots=args.skip_slots)
    # local logfiles
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=FF_Stage.FF_DL)

    mtp_mgmt_ctrl.cli_log_inf("MTP Convert Test Started", level=0)

    try:
        scanning.read_scanned_barcodes(mtp_mgmt_ctrl)
        nic_fru_cfg = mtp_mgmt_ctrl.barcode_scans

        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, FF_Stage.CONVERT, args.skip_test):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            logfile_close(open_file_track_list)
            return

        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        fail_nic_list = list()
        pass_nic_list = list()

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

        def get_slots_of_type(nic_type, except_type=[]):
            return mtp_mgmt_ctrl.get_slots_of_type(nic_type, pass_nic_list, except_type)

        def run_dl_test(nic_list_orig, test, *test_args, **test_kwargs):
            """ unconventional to define in main() space, but easier to get access to mtp_mgmt_ctrl, pass_nic_list, fail_nic_list, args this way"""
            stage = FF_Stage.CONVERT
            nic_list = nic_list_orig[:]

            if test in args.skip_test:
                test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, stage, test)
                return nic_list

            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            test_utils.test_start_nic_log_message(mtp_mgmt_ctrl, nic_list, stage, test)

            if DRY_RUN:
                rlist = []
            elif test == "NIC_PWRCYC":
                rlist = mtp_mgmt_ctrl.mtp_power_cycle_nic(nic_list, dl=True)
            elif test == "CONSOLE_BOOT_INIT":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_nic_console_access(nic_list)
            elif test == "CON_ERASE_BOARD_CONFIG":
                rlist = mtp_mgmt_ctrl.mtp_nic_erase_board_config(nic_list)
            elif test == "NIC_DIAG_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, skip_test_list=args.skip_test, **test_kwargs)
            elif test == "NOSECURE_CPLD_PROG":
                rlist = dl_ibm_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "NOSECURE_FAILSAFE_CPLD_PROG":
                rlist = dl_ibm_fail_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "SET_DIAGFW_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_set_nic_diagfw_boot(nic_list)
            elif test == "NIC_DIAG_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(nic_list)
            elif test == "CPLD_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_cpld(nic_list)
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown test '{:s}'".format(test))
                rlist = nic_list

            # catch bad return value
            if not isinstance(rlist, list):
                mtp_mgmt_ctrl.cli_log_err("Test {} failed with '{}', expected slot list".format(test, repr(rlist)))
                rlist = nic_list[:]

            # special pass/fail processing to keep old behavior
            for slot in nic_list:
                if test == "CONSOLE_BOOT_INIT":
                    if slot in rlist:
                        # rough way to track failure
                        mtp_mgmt_ctrl.mtp_set_nic_failed_boot(slot)

            for slot in rlist:
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot, testname=test)
                # update input list, could be pass_nic_list or a subset
                if slot in nic_list_orig:
                    nic_list_orig.remove(slot)
                # update global pass/fail list
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)

            duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
            test_utils.test_fail_nic_log_message(mtp_mgmt_ctrl, rlist, stage, test, start_ts, swmtestmode)
            test_utils.test_pass_nic_log_message(mtp_mgmt_ctrl, nic_list_orig, stage, test, start_ts, swmtestmode)
            return rlist

        # power cycle all nic
        mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)
        dsp = FF_Stage.CONVERT

        # FOR ADI IBM CARDS ONLY
        adi_ibm_reset_list = get_slots_of_type(NIC_Type.ORTANO2ADIIBM)
        run_dl_test(adi_ibm_reset_list, "NIC_PWRCYC")
        run_dl_test(adi_ibm_reset_list, "CONSOLE_BOOT_INIT")
        run_dl_test(adi_ibm_reset_list, "CON_ERASE_BOARD_CONFIG")
        run_dl_test(adi_ibm_reset_list, "NIC_DIAG_INIT", emmc_format=True, emmc_check=True, fru_fpo=True)
        run_dl_test(adi_ibm_reset_list, "NOSECURE_CPLD_PROG")
        run_dl_test(adi_ibm_reset_list, "NOSECURE_FAILSAFE_CPLD_PROG")
        run_dl_test(adi_ibm_reset_list, "SET_DIAGFW_BOOT")
        run_dl_test(adi_ibm_reset_list, "NIC_DIAG_INIT")
        run_dl_test(adi_ibm_reset_list, "NIC_DIAG_BOOT")
        run_dl_test(adi_ibm_reset_list, "CPLD_VERIFY")

        # power off nic
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.cli_log_inf("MTP DL Test Complete", level=0)

        for slot in pass_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

        for slot in fail_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        # err_msg = str(e)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)

    logfile_close(open_file_track_list)
    return


if __name__ == "__main__":
    main()

