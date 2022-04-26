#!/usr/bin/env python

import sys
import os
import time
import pexpect
import threading
import argparse
import re
import traceback

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_ASIC_SUPPORT
from libdefs import UUT_Type
from libdefs import MTP_Const
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_IMAGES
from libmfg_cfg import TOR_IMAGES
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl


def logfile_close(filep_list):
    os.system("sync")
    os.system("sync")
    for fp in filep_list:
        fp.close()
    os.system("sync")


def logfile_cleanup(file_list):
    for _file in file_list:
        os.system("rm -rf {:s}".format(_file))

def exit_fail(mtp_mgmt_ctrl, log_filep_list, err_msg=""):
    mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)
    # logfile_close(log_filep_list)
    mtp_mgmt_ctrl.mtp_console_disconnect()

def exit_pass(mtp_mgmt_ctrl, log_filep_list):
    logfile_close(log_filep_list)
    mtp_mgmt_ctrl.mtp_console_disconnect()

def load_mtp_cfg():
    # Same station as DL/P2C right now
    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_tor_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, telnet=False):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    if telnet:
        mtp_ts_cfg = mtp_cfg_db.get_mtp_console(mtp_id)
        if not mtp_ts_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find termserver config")
            return
    else:
        mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
        if not mtp_mgmt_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
            return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, ts_cfg=mtp_ts_cfg, apc_cfg=mtp_apc_cfg, num_of_slots=2, slots_to_skip=mtp_slots_to_skip)
    if telnet:
        mtp_mgmt_ctrl.set_uut_type(UUT_Type.TOR)
    return mtp_mgmt_ctrl

def single_uut_fw_program(stage,
                          fru_cfg, 
                          fail_uut_list, pass_uut_list, 
                          log_file_list, 
                          verbosity, 
                          skip_testlist = []):
    dsp = stage
    uut_id = fru_cfg["ID"]
    sn = fru_cfg["SN"]
    # mac = fru_cfg["MAC"]
    # pn = fru_cfg["PN"]
    # prog_date = str(fru_cfg["TS"])

    # Prepare local log files
    log_filep_list = list()
    log_dir = "log/"
    log_timestamp = libmfg_utils.get_timestamp()
    log_sub_dir = MTP_DIAG_Logfile.MFG_STAGE_LOG_DIR.format(stage, uut_id, log_timestamp)
    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir + log_sub_dir))
    test_log_file = log_dir + log_sub_dir + "mtp_test.log"
    log_file_list.append(test_log_file)
    test_log_filep = open(test_log_file, "w+", buffering=0)
    log_filep_list.append(test_log_filep)

    if verbosity:
        diag_log_filep = sys.stdout
    else:
        diag_log_file = log_dir + log_sub_dir + "mtp_diag.log"
        log_file_list.append(diag_log_file)
        diag_log_filep = open(diag_log_file, "w+", buffering=0)
        log_filep_list.append(diag_log_filep)

    diag_nic_log_filep_list = list()
    for slot in range(0,2):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = log_dir + log_sub_dir + "mtp_{:s}_diag.log".format(key)
        log_file_list.append(diag_nic_log_file)
        diag_nic_log_filep = open(diag_nic_log_file, "w+", buffering=0)
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    # Begin test
    mtp_cfg_db = load_mtp_cfg()
    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, uut_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, telnet=True)

    # hardcode all these for now
    card_type = NIC_Type.TAORMINA
    uut_type = UUT_Type.TOR
    asic_type = MTP_ASIC_SUPPORT.ELBA
    x86_image = MTP_IMAGES.AMD64_IMG[asic_type]
    arm_image = MTP_IMAGES.ARM64_IMG[asic_type]
    mtp_mgmt_ctrl.set_homedir(MTP_DIAG_Path.ONBOARD_TOR_DIAG_PATH)
    mtp_mgmt_ctrl._slots = 2
    
    qspi_fa_img_file = TOR_IMAGES.first_article_img[uut_type]
    os_ship_img_file = TOR_IMAGES.os_ship_img[uut_type]
    os_ship_exp_version = TOR_IMAGES.os_ship_dat[uut_type]
    tpm_img = TOR_IMAGES.tpm_img[uut_type]
    svos_img_file = TOR_IMAGES.svos_ship_img[uut_type]
    svos_util_img_file = TOR_IMAGES.svos_fpga_image[uut_type]

    fpga_img_file = TOR_IMAGES.fpga_img[uut_type]
    gpio_cpld_img_file = TOR_IMAGES.gpio_cpld_ship_img[uut_type]
    cpu_cpld_img_file = TOR_IMAGES.cpu_cpld_ship_img[uut_type]
    cpld_img_file = NIC_IMAGES.sec_cpld_img[card_type]
    fail_cpld_img_file = NIC_IMAGES.fail_cpld_img[card_type]
    fea_cpld_img_file = NIC_IMAGES.fea_cpld_img[card_type]

    try:
        if not mtp_mgmt_ctrl.tor_boot_select(0):
            mtp_mgmt_ctrl.cli_log_err("Unable to connect UUT Chassis", level=0)
            exit_fail(mtp_mgmt_ctrl, log_filep_list)
            if not fru_cfg["SN"]:
                fru_cfg["SN"] = "UNKNOWN"
            mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, "SVOS_BOOT", "FAILED", "0:00:00"), level=0)
            fail_uut_list.append(uut_id)
            mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
            mtp_mgmt_ctrl.mtp_apc_pwr_off()
            libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
            return

        if not libmfg_utils.mtp_clear_console(mtp_mgmt_ctrl):
            exit_fail(mtp_mgmt_ctrl, log_filep_list)

        if not mtp_mgmt_ctrl.mtp_console_connect():
            mtp_mgmt_ctrl.cli_log_err("Unable to connect UUT Chassis", level=0)
            exit_fail(mtp_mgmt_ctrl, log_filep_list)
            if uut_id not in fail_uut_list:
                fail_uut_list.append(uut_id)
            if uut_id in pass_uut_list:
                pass_uut_list.remove(uut_id)
            return
        mtp_mgmt_ctrl.cli_log_inf("UUT Chassis is connected", level=0)

        # Sync timestamp to server
        timestamp_str = str(libmfg_utils.timestamp_snapshot())
        if not mtp_mgmt_ctrl.mtp_mgmt_set_date(timestamp_str):
            mtp_mgmt_ctrl.cli_log_err("UUT Chassis timestamp sync failed", level=0)
            exit_fail(mtp_mgmt_ctrl, log_filep_list)
            if uut_id not in fail_uut_list:
                fail_uut_list.append(uut_id)
            if uut_id in pass_uut_list:
                pass_uut_list.remove(uut_id)
            return
        else:
            mtp_mgmt_ctrl.cli_log_inf("UUT Chassis timestamp sync'd", level=0)

        # read FRU
        mtp_mgmt_ctrl.tor_fru_init()
        sn = mtp_mgmt_ctrl._sn
        fru_cfg["SN"] = sn

        if uut_id not in pass_uut_list:
            pass_uut_list.append(uut_id)

        mtp_mgmt_ctrl.cli_log_inf("SW Install Process Started", level=0)
        mfg_swi_start_ts = libmfg_utils.timestamp_snapshot()

        testlist = [
                    "MGMT_INIT",
                    "SVOS_PROG_UTIL",
                    "BOARD_ID",
                    "GPIO_CPLD_PROG",
                    "ELBA_CPLD_PROG",
                    "CPU_CPLD_PROG",
                    "FPGA_PROG",
                    "CPLD_REF",
                    "SVOS_BOOT",
                    "MGMT_INIT",
                    "CPLD_VERIFY",
                    "SVOS_PROG",
                    "SVOS_BOOT",
                    "MGMT_INIT",
                    "SVOS_VERIFY",
                    "ISP_ENABLE",
                    "SHIP_OS_PROG",
                    "OS_S_BOOT",
                    "MGMT_INIT_OS",
                    "ISP_DISABLE",
                    "OS_VERIFY",
                    "DIAG_INIT",
                    "PCIE_SCAN",
                    "CLEAR_UT_MARK"
                    ]
        for skipped_test in skip_testlist:
            if skipped_test in testlist:
                testlist.remove(skipped_test)
        for test in testlist:
            mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = mtp_mgmt_ctrl.log_test_start(test)

            if test.startswith("PWRCYC"):
                ret = mtp_mgmt_ctrl.uut_powercycle()


            elif test.startswith("SVOS_BOOT"):
                ret = mtp_mgmt_ctrl.tor_boot_select(0)
            elif test.startswith("OS_BOOT"):
                ret = mtp_mgmt_ctrl.tor_boot_select(1)
            elif test.startswith("OS_S_BOOT"):
                ret = mtp_mgmt_ctrl.tor_boot_select(1, secure_login=True)

            elif test == "MGMT_INIT":
                ret = mtp_mgmt_ctrl.tor_mgmt_init()
            elif test == "MGMT_INIT_OS":
                ret = mtp_mgmt_ctrl.tor_mgmt_init(False)
            elif test == "SVOS_PROG_UTIL":
                ret = mtp_mgmt_ctrl.tor_util_prog(svos_util_img_file)

            elif test == "GPIO_CPLD_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("gpio", gpio_cpld_img_file, True)
            elif test == "ELBA_CPLD_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("elba 0", cpld_img_file, True)
                ret &= mtp_mgmt_ctrl.tor_cpld_prog("elba 1", cpld_img_file, True)
            elif test == "CPU_CPLD_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("cpu", cpu_cpld_img_file, True)
            elif test == "FPGA_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("fpga", fpga_img_file, True)
            elif test == "CPLD_REF":
                ret = mtp_mgmt_ctrl.tor_cpld_ref()
            elif test == "CPLD_VERIFY":
                ret = mtp_mgmt_ctrl.tor_cpld_verify(ship_img = True)


            elif test == "BIOS_VERIFY":
                ret = mtp_mgmt_ctrl.tor_bios_verify()


            elif test == "SVOS_PROG":
                ret = mtp_mgmt_ctrl.tor_svos_prog(svos_img_file, ship_img=True)
            elif test == "SVOS_VERIFY":
                ret = mtp_mgmt_ctrl.tor_svos_verify(ship_img=True)


            elif test == "SHIP_OS_PROG":
                ret = mtp_mgmt_ctrl.tor_os_prog(os_ship_img_file)
            elif test == "OS_VERIFY":
                ret = mtp_mgmt_ctrl.tor_os_verify(os_ship_exp_version)


            elif test == "BOARD_ID":
                ret = mtp_mgmt_ctrl.tor_board_id()
            elif test == "DIAG_INIT":
                ret = mtp_mgmt_ctrl.tor_diag_init(FF_Stage.FF_SWI, fpo=True)


            elif test == "ISP_ENABLE":
                ret = mtp_mgmt_ctrl.tor_isp_enable()
            elif test == "ISP_DISABLE":
                ret = mtp_mgmt_ctrl.tor_isp_disable()
            elif test == "PCIE_SCAN":
                ret = mtp_mgmt_ctrl.tor_pcie_scan()
            elif test == "CLEAR_UT_MARK":
                ret = mtp_mgmt_ctrl.tor_clear_ut_mark()

            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown SWI Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                if uut_id not in fail_uut_list:
                    fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)
                break
            else:
                mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

        mtp_mgmt_ctrl.cli_log_inf("Host tests completed\n", level=0)

        mtp_mgmt_ctrl.cli_log_inf("Begin ARM tests", level=0)

        # everything in mainfw
        if uut_id not in fail_uut_list:
            for slot in range(mtp_mgmt_ctrl._slots):
                mtp_mgmt_ctrl._nic_ctrl_list[slot]._in_mainfw = True


        if uut_id not in fail_uut_list:
            for slot in range(mtp_mgmt_ctrl._slots):
                sn = fru_cfg["SN"]

                testlist = [
                    "FWENV_ERASE",
                    "BOARD_CONFIG_ERASE"
                    ]
                for skipped_test in skip_testlist:
                    if skipped_test in testlist:
                        testlist.remove(skipped_test)
                for test in testlist:
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                    if test == "FWENV_ERASE":
                        ret = mtp_mgmt_ctrl.tor_nic_fwenv_erase(slot)
                    elif test == "BOARD_CONFIG_ERASE":
                        ret = mtp_mgmt_ctrl.tor_nic_config_erase(slot)
                    else:
                        mtp_mgmt_ctrl.cli_log_err("Unknown SWI Test: {:s}, Ignore".format(test))
                        if uut_id not in fail_uut_list:
                            fail_uut_list.append(uut_id)
                        if uut_id in pass_uut_list:
                            pass_uut_list.remove(uut_id)
                        break
                    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                    if not ret:
                        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                        if uut_id not in fail_uut_list:
                            fail_uut_list.append(uut_id)
                        if uut_id in pass_uut_list:
                            pass_uut_list.remove(uut_id)
                        break
                    else:
                        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        if uut_id not in fail_uut_list:

            testlist = ["OS_S_BOOT", "MGMT_INIT_OS", "NIC_INIT"]

            for skipped_test in skip_testlist:
                if skipped_test in testlist:
                    testlist.remove(skipped_test)
            for test in testlist:
                mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
                start_ts = mtp_mgmt_ctrl.log_test_start(test)
                if test.startswith("OS_S_BOOT"):
                    ret = mtp_mgmt_ctrl.tor_boot_select(1, secure_login=True)
                elif test == "MGMT_INIT_OS":
                    ret = mtp_mgmt_ctrl.tor_mgmt_init(False)
                elif test == "DIAG_INIT":
                    ret = mtp_mgmt_ctrl.tor_diag_init(FF_Stage.FF_SWI, fpo=False)
                elif test == "NIC_INIT":
                    ret = mtp_mgmt_ctrl.tor_nic_init()
                else:
                    mtp_mgmt_ctrl.cli_log_err("Unknown SWI Test: {:s}, Ignore".format(test))
                    continue
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                    if uut_id not in fail_uut_list:
                        fail_uut_list.append(uut_id)
                    if uut_id in pass_uut_list:
                        pass_uut_list.remove(uut_id)
                    break
                else:
                    mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

        # reapply the mainfw flag after nic_init
        if uut_id not in fail_uut_list:
            for slot in range(mtp_mgmt_ctrl._slots):
                mtp_mgmt_ctrl._nic_ctrl_list[slot]._in_mainfw = True

        if uut_id not in fail_uut_list:
            for slot in range(mtp_mgmt_ctrl._slots):
                sn = fru_cfg["SN"]

                testlist = [
                    "MAINFW_VERIFY",
                    "BOARD_CONFIG_VERIFY",
                    "NIC_CLEANUP"
                    ]

                for skipped_test in skip_testlist:
                    if skipped_test in testlist:
                        testlist.remove(skipped_test)
                for test in testlist:
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                    if test == "MAINFW_VERIFY":
                        ret = mtp_mgmt_ctrl.tor_nic_fw_verify(slot)
                    elif test == "BOARD_CONFIG_VERIFY":
                        ret = mtp_mgmt_ctrl.tor_nic_config_verify(slot)
                    elif test == "NIC_CLEANUP":
                        ret = mtp_mgmt_ctrl.tor_nic_sw_cleanup(slot)
                    else:
                        mtp_mgmt_ctrl.cli_log_err("Unknown SWI Test: {:s}, Ignore".format(test))
                        if uut_id not in fail_uut_list:
                            fail_uut_list.append(uut_id)
                        if uut_id in pass_uut_list:
                            pass_uut_list.remove(uut_id)
                        break
                    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                    if not ret:
                        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                        if uut_id not in fail_uut_list:
                            fail_uut_list.append(uut_id)
                        if uut_id in pass_uut_list:
                            pass_uut_list.remove(uut_id)
                        break
                    else:
                        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


        if uut_id not in fail_uut_list:

            testlist = ["SW_CLEANUP"]

            for skipped_test in skip_testlist:
                if skipped_test in testlist:
                    testlist.remove(skipped_test)
            for test in testlist:
                mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
                start_ts = mtp_mgmt_ctrl.log_test_start(test)
                if test == "SW_CLEANUP":
                    ret = mtp_mgmt_ctrl.tor_sw_cleanup()
                else:
                    mtp_mgmt_ctrl.cli_log_err("Unknown SWI Test: {:s}, Ignore".format(test))
                    continue
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                    if uut_id not in fail_uut_list:
                        fail_uut_list.append(uut_id)
                    if uut_id in pass_uut_list:
                        pass_uut_list.remove(uut_id)
                    break
                else:
                    mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

        # copy additional logs
        mtp_mgmt_ctrl.tor_copy_sys_log(log_dir + log_sub_dir)
    
        mtp_mgmt_ctrl.cli_log_inf("SW Install Process Complete", level=0)
        # shut down system
        if uut_id in pass_uut_list:
            mtp_mgmt_ctrl.uut_chassis_shutdown()

        mfg_swi_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG SWI Test Duration:{:s}".format(mfg_swi_stop_ts - mfg_swi_start_ts))

        if uut_id in pass_uut_list:
            sn = mtp_mgmt_ctrl.get_mtp_sn()
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(uut_id, card_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

        if uut_id in fail_uut_list:
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(uut_id, card_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    except Exception as e:
        if uut_id not in fail_uut_list:
            fail_uut_list.append(uut_id)
        if uut_id in pass_uut_list:
            pass_uut_list.remove(uut_id)
        exit_fail(mtp_mgmt_ctrl, log_filep_list, traceback.print_exc())

def main():
    parser = argparse.ArgumentParser(description="MFG SWI Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", "--uut-id", "--uutid", "-uutid", "-mtpid", help="pre-select UUTs", nargs="*", default=[])

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    ######################################
    mtp_cfg_db = load_mtp_cfg()

    pass_rslt_list = list()
    fail_rslt_list = list()
    log_dir = "log/"
    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir))

    stage = FF_Stage.FF_SWI

    uut_id_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
    fru_cfg = dict()
    for uut_id in uut_id_list:
        fru_cfg[uut_id] = dict()
        fru_cfg[uut_id]["ID"] = uut_id
        fru_cfg[uut_id]["VALID"] = True
        fru_cfg[uut_id]["SN"] = None
        fru_cfg[uut_id]["MAC"] = None
        fru_cfg[uut_id]["PN"] = None
        fru_cfg[uut_id]["TS"] = None

    ######################################

    pass_uut_list = list()
    fail_uut_list = list()

    uut_thread_list = list()
    logfile_dict = dict()

    for uut in fru_cfg.keys():
        if uut in fail_uut_list:
            continue
        if not fru_cfg[uut]["VALID"]:
            continue

        logfile_dict[uut] = list()
        uut_thread = threading.Thread(target = single_uut_fw_program, args = (stage,
                                                                              fru_cfg[uut], 
                                                                              fail_uut_list,
                                                                              pass_uut_list,
                                                                              logfile_dict[uut],
                                                                              verbosity,
                                                                              args.skip_test))
        uut_thread.daemon = True
        uut_thread.start()
        uut_thread_list.append(uut_thread)
        time.sleep(2)

    # monitor all the thread
    while True:
        if len(uut_thread_list) == 0:
            break
        for uut_thread in uut_thread_list[:]:
            if not uut_thread.is_alive():
                uut_thread.join()
                uut_thread_list.remove(uut_thread)
        time.sleep(5)

    # Package each UUT's logfile
    for uut_id in logfile_dict.keys():
        logfile_list = logfile_dict[uut_id]

        log_sub_dir = os.path.basename(os.path.dirname(logfile_list[0])) # aka MFG_STAGE_LOG_DIR

        # extract log timestamp from one of the filenames
        if logfile_list:
            timestamp_length = 19
            log_timestamp = log_sub_dir[-19:]
        else:
            log_timestamp = libmfg_utils.get_timestamp()

        # pkg the logfile
        # MFG_DL_LOG_PKG_FILE = "DL_{:s}_{:s}.tar.gz"
        # MFG_DL_LOG_DIR = "DL_{:s}_{:s}/"
        # MFG_LOG_PKG_FMT = "tar czf {:s} -C {:s} {:s}"
        log_pkg_file = MTP_DIAG_Logfile.MFG_STAGE_LOG_PKG_FILE.format(stage, uut_id, log_timestamp)
        os.system(MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format(log_dir+log_pkg_file, log_dir, log_sub_dir))

        # move the logs to the log root dir
        for slot in fail_uut_list + pass_uut_list:
            sn = fru_cfg[uut_id]["SN"]
            nic_type = NIC_Type.TAORMINA
            if not sn:
                continue
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_SWI_LOG_DIR_FMT.format(nic_type, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_SWI_LOG_DIR_FMT.format(nic_type, sn)
            os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir))
            libmfg_utils.cli_inf("[{:s}] Collecting log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
            os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))

        # cleanup the log dir
        logfile_cleanup([log_dir+log_sub_dir, log_dir+log_pkg_file])

    ######## TEST SUMMARY ########
    test_summary_dict = dict()
    for uut_id in pass_uut_list:
        sn = fru_cfg[uut_id]["SN"]
        card_type = NIC_Type.TAORMINA
        test_summary_dict[uut_id] = [(uut_id, sn, card_type, True)]
    
    for uut_id in fail_uut_list:
        sn = fru_cfg[uut_id]["SN"]
        card_type = NIC_Type.TAORMINA
        test_summary_dict[uut_id] = [(uut_id, sn, card_type, False)]

    libmfg_utils.mfg_summary_disp(stage, test_summary_dict, [])

    return

if __name__ == "__main__":
    main()

