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
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_IMAGES
from libmfg_cfg import TOR_IMAGES
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libtest_db import *
from libmes import *

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
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    # if not GLB_CFG_MFG_TEST_MODE:
    #     mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    # mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_tor_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, console_log_filep, diag_nic_log_filep_list, telnet=False):
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
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, console_log_filep, diag_nic_log_filep_list, ts_cfg=mtp_ts_cfg, apc_cfg=mtp_apc_cfg, num_of_slots=2, slots_to_skip=mtp_slots_to_skip)
    if telnet:
        mtp_mgmt_ctrl.set_uut_type(UUT_Type.TOR)
    return mtp_mgmt_ctrl

def single_uut_fw_program(stage,
                          fru_cfg,
                          fail_uut_list, pass_uut_list,
                          log_file_list,
                          verbosity,
                          mes_obj,
                          scan_rslt,
                          skip_testlist = []):

    dsp = stage #FF_Stage.FF_DL
    uut_id = fru_cfg["ID"]
    sn = fru_cfg["SN"]
    mac = fru_cfg["MAC"]
    pn = fru_cfg["PN"]
    prog_date = str(fru_cfg["TS"])
    edc = fru_cfg["EDC"]

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

        console_log_file = log_dir + log_sub_dir + "mtp_console.log"
        log_file_list.append(console_log_file)
        console_log_filep = open(console_log_file, "w+", buffering=0)
        log_filep_list.append(console_log_filep)

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
    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, uut_id, test_log_filep, diag_log_filep, console_log_filep, diag_nic_log_filep_list, telnet=True)
    mtp_mgmt_ctrl._test_log_folder = log_dir + log_sub_dir

    # hardcode all these for now
    card_type = NIC_Type.TAORMINA
    uut_type = UUT_Type.TOR
    asic_type = MTP_ASIC_SUPPORT.ELBA
    x86_image = MTP_IMAGES.AMD64_IMG[asic_type]
    arm_image = MTP_IMAGES.ARM64_IMG[asic_type]
    mtp_mgmt_ctrl.set_homedir(MTP_DIAG_Path.ONBOARD_TOR_DIAG_PATH)
    mtp_mgmt_ctrl._slots = 2

    svos_img_file = TOR_IMAGES.svos_test_img[uut_type]
    os_test_img_file = TOR_IMAGES.os_test_img[uut_type]
    os_test_exp_version = TOR_IMAGES.os_test_dat[uut_type]
    os_ship_img_file = TOR_IMAGES.os_ship_img[uut_type]
    os_ship_exp_version = TOR_IMAGES.os_ship_dat[uut_type]
    tpm_img = TOR_IMAGES.tpm_img[uut_type]
    svos_util_img_file = TOR_IMAGES.svos_fpga_image[uut_type]

    fpga_img_file = TOR_IMAGES.fpga_img[uut_type]
    test_fpga_img_file = TOR_IMAGES.test_fpga_img[uut_type]
    gpio_cpld_img_file = TOR_IMAGES.gpio_cpld_test_img[uut_type]
    cpu_cpld_img_file = TOR_IMAGES.cpu_cpld_test_img[uut_type]
    cpld_img_file = NIC_IMAGES.cpld_img[card_type]
    fail_cpld_img_file = NIC_IMAGES.fail_cpld_img[card_type]
    fea_cpld_img_file = NIC_IMAGES.fea_cpld_img[card_type]

    boot0_img_file = TOR_IMAGES.flash_boot0[uut_type]
    ubootg_img_file = TOR_IMAGES.flash_uboot_gold[uut_type]
    kernelg_img_file = TOR_IMAGES.flash_fw_gold[uut_type]
    uboota_img_file = TOR_IMAGES.flash_uboot_primary[uut_type]
    kernela_img_file = TOR_IMAGES.flash_fw_primary[uut_type]

    if stage == "DL1":
        fru_valid = False
    else:
        fru_valid = True

    try:
        if not fru_cfg["SN"]:
            fru_cfg["SN"] = "UNKNOWN"

        testlist = ["SVOS_BOOT", "CONSOLE_CLEAR", "CONSOLE_CONNECT",]

        if isinstance(mes_obj, MES):
            # Add MES tasks, if applicable
            testlist.extend(["MES_ACCESS", "OK_TEST_STN_CHK",])

        for test in testlist:
            start_ts = mtp_mgmt_ctrl.log_test_start(test)

            if test == "SVOS_BOOT":
                ret = mtp_mgmt_ctrl.tor_boot_select(0, fru_valid=fru_valid, console_sanity_check=True)
            elif test == "CONSOLE_CLEAR":
                ret = libmfg_utils.mtp_clear_console(mtp_mgmt_ctrl)
            elif test == "CONSOLE_CONNECT":
                ret = mtp_mgmt_ctrl.mtp_console_connect()
                if not ret:
                    mtp_mgmt_ctrl.cli_log_err("Failed to connect to UUT console", level=0)
                else:
                    mtp_mgmt_ctrl.cli_log_inf("UUT console is connected", level=0)

            elif test == "MES_ACCESS":
                # Access MES data
                mtp_mgmt_ctrl.cli_log_inf("Access MES data", level=0)
                mes_obj.store_mgmt_ctrl(mtp_mgmt_ctrl)
                ret = mes_obj.pull_mes_info(scan_rslt[uut_id]['UUT_SN'])

            elif test == "OK_TEST_STN_CHK":
                # Verify if UUT is allowed to undergo this test station
                ret = mes_obj.verify_next_test_station(stage)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_err("UUT is NOT allowed to run " + stage, level=0)
                    mtp_mgmt_ctrl.cli_log_inf("Test data will NOT be pushed to MES")
                    mes_obj.clear_push_to_mes()
                else:
                    mtp_mgmt_ctrl.cli_log_inf("UUT is allowed to run " + stage, level=0)

            duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)

            if not ret:
                mtp_mgmt_ctrl.cli_log_err("Failed to complete test initialization", level=0)
                mtp_mgmt_ctrl.tor_sys_failure_dump()
                exit_fail(mtp_mgmt_ctrl, log_filep_list)
                if uut_id not in fail_uut_list:
                    fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)

                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)

                # FAIL: Save the following to be uploaded to MES later:
                # - Test Status
                # - Test Fail Mode
                # - Test Fail Signature
                # - Test End Time
                # - (Clear the passmark just in case)
                if isinstance(mes_obj, MES):
                    mes_obj.save_res_test_status("FAIL")
                    mes_obj.save_res_fail_mode(test)
                    mes_obj.save_res_fail_signature('TBD')
                    mes_obj.save_res_test_end_timestamp(libmfg_utils.timestamp_snapshot())
                    mes_obj.save_res_passmark("N/A")

                    mes_obj.push_results_to_mes()

                return

        mtp_mgmt_ctrl.cli_log_inf("UUT Chassis is connected", level=0)

        if stage == "DL2":
            # read FRU
            # mtp_mgmt_ctrl.tor_fru_init()
            sn = mtp_mgmt_ctrl._sn
            fru_cfg["SN"] = sn

        if uut_id not in pass_uut_list:
            pass_uut_list.append(uut_id)

        mtp_mgmt_ctrl.print_script_version()

        if stage == "DL2":
            mtp_mgmt_ctrl.cli_log_inf("Programming Matrix:", level=0)
            mtp_mgmt_ctrl.cli_log_inf("SvOS: {:s}".format(svos_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("CX-OS: {:s}".format(os_test_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("FPGA: {:s}".format(test_fpga_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("CPU CPLD: {:s}".format(cpu_cpld_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("GPIO CPLD: {:s}".format(gpio_cpld_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("ELBA CPLD main: {:s}".format(cpld_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("ELBA CPLD gold: {:s}".format(fail_cpld_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("ELBA boot0: {:s}".format(boot0_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("ELBA ubootg: {:s}".format(ubootg_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("ELBA goldfw: {:s}".format(kernelg_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("ELBA uboota: {:s}".format(uboota_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("ELBA mainfw: {:s}".format(kernela_img_file), level=1)
            mtp_mgmt_ctrl.cli_log_inf("Programming Matrix end\n", level=0)

        mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Started", level=0)
        mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

        ### X86 HOST TESTS
        if stage == "DL1":
            testlist = [
                        "MES_SCAN_INPUT_CHK",
                        "GET_PCBA_SN",
                        "SSD_FORMAT",
                        "I210_NIC_PROG",
                        "SVOS_BOOT",
                        "I210_MAC_PROG",
                        "FRU_PROG",
                        "FRU_TPM_SN_PROG",
                        "SVOS_BOOT",
                        "FRU_VERIFY"]

        elif stage == "DL2":
            testlist = [
                        "MES_SCAN_INPUT_CHK",
                        "MGMT_INIT",
                        "SVOS_PROG_UTIL",
                        "MES_FRU_EEPROM_CHK",
                        "BOARD_ID",
                        "SVOS_TEST_PROG",
                        "SVOS_BOOT",
                        "MGMT_INIT",
                        "SVOS_VERIFY",
                        "GPIO_CPLD_PROG",
                        "ELBA_CPLD_PROG",
                        "ELBA_FEA_PROG",
                        "CPU_CPLD_PROG",
                        "TEST_FPGA_PROG",
                        "CPLD_REF",
                        "SVOS_BOOT",
                        "MGMT_INIT",
                        "BOARD_ID",
                        "CPLD_VERIFY",
                        "OS_PROG_TEST",
                        "NIC_QSPI_UPDATE",
                        "OS_BOOT",
                        "OS_TEST_VERIFY",
                        "UL_FRU_PROG",
                        "OS_BOOT",
                        "UL_FRU_VERIFY",
                        "MES_MFG_EEPROM_CHK",
                        "DIAG_INIT",
                        "TD_GEARBOX_VERIFY",
                        "TD_AVS_SET"
                        ]
        for skipped_test in skip_testlist:
            if skipped_test in testlist:
                testlist.remove(skipped_test)
        for test in testlist:
            mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = mtp_mgmt_ctrl.log_test_start(test)

            if test.startswith("PWRCYC"):
                ret = mtp_mgmt_ctrl.uut_powercycle()

            elif test == "MES_SCAN_INPUT_CHK" and isinstance(mes_obj, MES):
                # Verify scanned input against MES data
                mtp_mgmt_ctrl.cli_log_inf("Verify scanned input against MES data", level=0)
                ret = mes_obj.verify_scanned_input_against_mes(scan_rslt[uut_id])

            elif test == "MES_FRU_EEPROM_CHK" and isinstance(mes_obj, MES):

                # Verify FRU EEPROM contents against MES data
                eeprom_contents = dict()
                msg = "Verify FRU EEPROM contents against MES data"
                mtp_mgmt_ctrl.cli_log_inf(msg, level=0)
                ret, eeprom_contents = mtp_mgmt_ctrl.get_eeprom_contents()
                if ret:
                    ret = mes_obj.verify_eeprom_against_mes(
                        eeprom_contents, eeprom_type='fru')

            elif test == "MES_MFG_EEPROM_CHK" and isinstance(mes_obj, MES):

                # Verify Locked MFG EEPROM contents against MES data
                eeprom_contents = dict()
                msg = "Verify Locked MFG EEPROM contents against MES data"
                mtp_mgmt_ctrl.cli_log_inf(msg, level=0)
                ret, eeprom_contents = \
                    mtp_mgmt_ctrl.get_eeprom_contents(eeprom_location='mfg_l')
                if ret:
                    ret = mes_obj.verify_eeprom_against_mes(
                        eeprom_contents, eeprom_type='mfg_l')

                    # Verify Unlocked MFG EEPROM contents against MES data
                    if ret:
                        msg = "Verify Unlocked MFG EEPROM contents against MES data"
                        mtp_mgmt_ctrl.cli_log_inf(msg, level=0)
                        ret, eeprom_contents = \
                            mtp_mgmt_ctrl.get_eeprom_contents(eeprom_location='mfg_ul')
                        if ret:
                            ret = mes_obj.verify_eeprom_against_mes(
                                eeprom_contents, eeprom_type='mfg_ul')


            elif test == "USB_BOOT":
                ret = mtp_mgmt_ctrl.tor_usb_boot()
            elif test.startswith("SVOS_BOOT"):
                ret = mtp_mgmt_ctrl.tor_boot_select(0, fru_valid=fru_valid)
            elif test.startswith("OS_BOOT"):
                ret = mtp_mgmt_ctrl.tor_boot_select(1)
            elif test.startswith("BIOS_BOOT"):
                ret = mtp_mgmt_ctrl.tor_boot_bios()


            elif test == "MGMT_INIT":
                ret = mtp_mgmt_ctrl.tor_mgmt_init()
            elif test == "MGMT_INIT_OS":
                ret = mtp_mgmt_ctrl.tor_mgmt_init(False)


            elif test == "SSD_FORMAT":
                ret = mtp_mgmt_ctrl.tor_ssd_format()
            elif test == "NIC_QSPI_FORMAT":
                ret = mtp_mgmt_ctrl.tor_nic_qspi_first_article()
            elif test == "NIC_QSPI_UPDATE":
                ret = mtp_mgmt_ctrl.tor_nic_qspi_prog()


            elif test == "I210_NIC_PROG":
                ret = mtp_mgmt_ctrl.i210_nic_prog()
            elif test == "I210_MAC_PROG":
                ret = mtp_mgmt_ctrl.i210_mac_prog(fru_cfg)


            elif test == "FRU_PROG":
                ret = mtp_mgmt_ctrl.tor_fru_prog(sn, mac, pn, edc, prog_date)
            elif test == "UL_FRU_PROG":
                if isinstance(mes_obj, MES):
                    # Pull PCA EDC from MES
                    ret = mtp_mgmt_ctrl.tor_mfg_fru_prog(edc=mes_obj.get_mes_uut_edc())
                else:
                    ret = mtp_mgmt_ctrl.tor_mfg_fru_prog()
            elif test == "FRU_TPM_SN_PROG":
                ret = mtp_mgmt_ctrl.tor_fru_prog_tpm_pcbasn(pcbasn)
            elif test == "FRU_VERIFY":
                ret = mtp_mgmt_ctrl.tor_fru_verify(sn, mac, pn, prog_date)
            elif test == "UL_FRU_VERIFY":
                ret = mtp_mgmt_ctrl.tor_mfg_fru_verify()
            elif test == "GET_PCBA_SN":
                if isinstance(mes_obj, MES):
                    # Pull PCBA SN from MES
                    msg = "Pull PCBA SN from MES"
                    mtp_mgmt_ctrl.cli_log_inf(msg, level=0)
                    pcbasn = mes_obj.get_mes_uut_wsn()
                else:
                    pcbasn = mtp_mgmt_ctrl.get_pchasn_by_yaml(sn)
                if not pcbasn:
                    ret = False
                else:
                    ret = True


            elif test == "GPIO_CPLD_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("gpio", gpio_cpld_img_file, False)
            elif test == "ELBA_CPLD_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("elba 0", cpld_img_file, False)
                ret &= mtp_mgmt_ctrl.tor_cpld_prog("elba 1", cpld_img_file, False)
            elif test == "ELBA_FEA_PROG":
                ret = mtp_mgmt_ctrl.tor_fea_cpld_prog("elba 0", fea_cpld_img_file)
                ret &= mtp_mgmt_ctrl.tor_fea_cpld_prog("elba 1", fea_cpld_img_file)
            elif test == "CPU_CPLD_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("cpu", cpu_cpld_img_file, False)
            elif test == "TEST_FPGA_PROG":
                ret = mtp_mgmt_ctrl.tor_cpld_prog("fpga", test_fpga_img_file, False)
            elif test == "CPLD_REF":
                ret = mtp_mgmt_ctrl.tor_cpld_ref()
            elif test == "CPLD_VERIFY":
                ret = mtp_mgmt_ctrl.tor_cpld_verify()


            elif test == "TPM_CONFIG_IMAGE":
                ret = mtp_mgmt_ctrl.tor_svos_bio_tpm_config_image_setup(tpm_img)
            elif test == "BIOS_CONFIG_TPM":
                ret = mtp_mgmt_ctrl.tor_bios_config_tpm()


            elif test == "TD_AVS_SET":
                ret = mtp_mgmt_ctrl.tor_td_avs_set()
            elif test == "TD_GEARBOX_VERIFY":
                ret = mtp_mgmt_ctrl.tor_td_gearbox_verify()


            elif test == "BIOS_VERIFY":
                ret = mtp_mgmt_ctrl.tor_bios_verify()

            elif test == "SVOS_TEST_PROG":
                ret = mtp_mgmt_ctrl.tor_svos_prog(svos_img_file)
            elif test == "SVOS_VERIFY":
                ret = mtp_mgmt_ctrl.tor_svos_verify()
            elif test == "SVOS_PROG_UTIL":
                ret = mtp_mgmt_ctrl.tor_util_prog(svos_util_img_file)

            elif test == "OS_PROG_TEST":
                ret = mtp_mgmt_ctrl.tor_os_prog(os_test_img_file)
            elif test == "OS_PROG_SHIP":
                ret = mtp_mgmt_ctrl.tor_os_prog(os_ship_img_file)
            elif test == "OS_UPDATE":
                ret = mtp_mgmt_ctrl.tor_mgmt_os_prog(os_ship_img_file)
            elif test == "OS_TEST_VERIFY":
                ret = mtp_mgmt_ctrl.tor_os_verify(os_test_exp_version)
                if ret:
                    mtp_mgmt_ctrl._svos_boot = False
            elif test == "OS_VERIFY":
                ret = mtp_mgmt_ctrl.tor_os_verify(os_ship_exp_version)


            elif test == "BOARD_ID":
                ret = mtp_mgmt_ctrl.tor_board_id()
            elif test == "DIAG_INIT":
                ret = mtp_mgmt_ctrl.tor_diag_init(FF_Stage.FF_DL, fpo=True)
            elif test == "DIAG_INIT2":
                ret = mtp_mgmt_ctrl.tor_diag_init(FF_Stage.FF_DL, fpo=False)

            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.tor_sys_failure_dump()
                if test in ("NIC_QSPI_FORMAT", "NIC_QSPI_UPDATE", "others..."):
                    mtp_mgmt_ctrl.tor_nic_failure_dump(0)
                    mtp_mgmt_ctrl.tor_nic_failure_dump(1)
                if uut_id not in fail_uut_list:
                    fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)

                # FAIL: Save the following to be uploaded to MES later:
                # - Test Fail Mode
                # - Test Fail Signature
                if isinstance(mes_obj, MES):
                    mes_obj.save_res_fail_mode(test)
                    mes_obj.save_res_fail_signature('TBD')

                break
            else:
                mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

        mtp_mgmt_ctrl.cli_log_inf("Host tests completed\n", level=0)

        if stage == "DL2" and uut_id not in fail_uut_list:
            mtp_mgmt_ctrl.cli_log_inf("Begin ARM tests", level=0)

            # FRU program prep
            for slot in range(mtp_mgmt_ctrl._slots):
                key = libmfg_utils.nic_key(slot)
                fru_cfg[key] = dict()
                fru_cfg[key]["SN"] = mtp_mgmt_ctrl.get_mtp_sn()
                fru_cfg[key]["PN"] = mtp_mgmt_ctrl.get_mtp_pn()
                fru_cfg[key]["MAC"] = mtp_mgmt_ctrl.get_mtp_mac()
                fru_cfg[key]["TS"] = libmfg_utils.get_fru_date()
                fru_cfg[key]["VALID"] = "YES"

            time.sleep(5)

            testlist = [
                        "NIC_GOLDFW_BOOT",
                        "NIC_PWRCYC",
                        "NIC_GOLDFW_VERIFY",
                        "MEMTUN_INIT",
                        "NIC_EMMC_FORMAT",
                        "EMMC_HWRESET_SET",
                        "EMMC_BKOPS_EN",
                        "NIC_PWRCYC",
                        "NIC_GOLDFW_VERIFY",
                        "MEMTUN_INIT",
                        "NIC_DIAG_INIT",
                        "NIC_PROFILE_CONFIG"
                        ]
            for skipped_test in skip_testlist:
                if skipped_test in testlist:
                    testlist.remove(skipped_test)
            for test in testlist:
                mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
                start_ts = mtp_mgmt_ctrl.log_test_start(test)

                # Set goldfw to bootup
                if test == "NIC_GOLDFW_BOOT":
                    ret =  mtp_mgmt_ctrl.tor_nic_gold_boot(0)
                    ret &= mtp_mgmt_ctrl.tor_nic_gold_boot(1)
                # Powercycle including rescan to bring changes into effect
                elif test == "NIC_PWRCYC":
                    ret = mtp_mgmt_ctrl.mtp_power_cycle_nic()
                # Verify they booted into goldfw
                elif test == "NIC_GOLDFW_VERIFY":
                    ret  = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_gold_boot(0)
                    ret &= mtp_mgmt_ctrl.mtp_mgmt_verify_nic_gold_boot(1)
                # Create new memtun interfaces
                elif test == "MEMTUN_INIT":
                    ret  = mtp_mgmt_ctrl.tor_nic_memtun_init(0)
                    ret &= mtp_mgmt_ctrl.tor_nic_memtun_init(1)
                # Set emmcs to pSLC mode
                elif test == "NIC_EMMC_FORMAT":
                    ret  = mtp_mgmt_ctrl.tor_nic_emmc_format(0)
                    ret &= mtp_mgmt_ctrl.tor_nic_emmc_format(1)
                elif test == "EMMC_HWRESET_SET":
                    ret  = mtp_mgmt_ctrl.tor_nic_emmc_hwreset_set(0)
                    ret &= mtp_mgmt_ctrl.tor_nic_emmc_hwreset_set(1)
                elif test == "EMMC_BKOPS_EN":
                    ret  = mtp_mgmt_ctrl.tor_nic_emmc_bkops_en(0)
                    ret &= mtp_mgmt_ctrl.tor_nic_emmc_bkops_en(1)
                # Init ARM Diag Environment
                elif test == "NIC_DIAG_INIT":
                    ret = mtp_mgmt_ctrl.mtp_nic_diag_init(emmc_format=True, fru_valid=False, sn_tag=True, fru_cfg=fru_cfg)
                # Write device.conf
                elif test == "NIC_PROFILE_CONFIG":
                    ret  = mtp_mgmt_ctrl.tor_nic_Setup_device_config(0)
                    ret &= mtp_mgmt_ctrl.tor_nic_Setup_device_config(1)
                else:
                    mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
                    continue
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                    mtp_mgmt_ctrl.tor_sys_failure_dump()
                    mtp_mgmt_ctrl.tor_nic_failure_dump(0)
                    mtp_mgmt_ctrl.tor_nic_failure_dump(1)
                    if uut_id not in fail_uut_list:
                        fail_uut_list.append(uut_id)
                    if uut_id in pass_uut_list:
                        pass_uut_list.remove(uut_id)

                    # FAIL: Save the following to be uploaded to MES later:
                    # - Test Fail Mode
                    # - Test Fail Signature
                    if isinstance(mes_obj, MES):
                        mes_obj.save_res_fail_mode(test)
                        mes_obj.save_res_fail_signature('TBD')

                    break
                else:
                    mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

        if stage == "DL2" and uut_id not in fail_uut_list:
            for slot in range(mtp_mgmt_ctrl._slots):
                key = libmfg_utils.nic_key(slot)
                sn = fru_cfg[key]["SN"]
                pn = "73-0040-03 A2"
                mac = fru_cfg[key]["MAC"]
                prog_date = fru_cfg[key]["TS"]

                testlist = ["NIC_FRU_PROG",
                            "NIC_FRU_VERIFY",
                            "NIC_MAINFW_SET",
                            "AVS_SET"]
                for skipped_test in skip_testlist:
                    if skipped_test in testlist:
                        testlist.remove(skipped_test)
                for test in testlist:
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                    if test == "NIC_FRU_PROG":
                        ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn)
                    elif test == "NIC_FRU_VERIFY":
                        ret = mtp_mgmt_ctrl.tor_nic_fru_verify(slot, sn, mac, pn, prog_date)
                    elif test == "NIC_MAINFW_SET":
                        ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_mainfw_boot(slot)
                    elif test == "AVS_SET":
                        ret = mtp_mgmt_ctrl.tor_nic_avs_set(slot)
                    else:
                        mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
                        if uut_id not in fail_uut_list:
                            fail_uut_list.append(uut_id)
                        if uut_id in pass_uut_list:
                            pass_uut_list.remove(uut_id)

                        # FAIL: Save the following to be uploaded to MES later:
                        # - Test Fail Mode
                        # - Test Fail Signature
                        if isinstance(mes_obj, MES):
                            mes_obj.save_res_fail_mode("Unknown DL Test")
                            mes_obj.save_res_fail_signature('TBD')

                        break
                    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                    if not ret:
                        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                        mtp_mgmt_ctrl.tor_nic_failure_dump(slot)
                        if uut_id not in fail_uut_list:
                            fail_uut_list.append(uut_id)
                        if uut_id in pass_uut_list:
                            pass_uut_list.remove(uut_id)

                        # FAIL: Save the following to be uploaded to MES later:
                        # - Test Fail Mode
                        # - Test Fail Signature
                        if isinstance(mes_obj, MES):
                            mes_obj.save_res_fail_mode(test)
                            mes_obj.save_res_fail_signature('TBD')

                        break
                    else:
                        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        if uut_id not in fail_uut_list and stage == "DL2":
            if not mtp_mgmt_ctrl.tor_fru_passmark(stage):
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)
                if uut_id not in fail_uut_list:
                    fail_uut_list.append(uut_id)

                # FAIL: Save the following to be uploaded to MES later:
                # - Test Fail Mode
                # - Test Fail Signature
                if isinstance(mes_obj, MES):
                    mes_obj.save_res_fail_mode('Failed to program DL2 passmark')
                    mes_obj.save_res_fail_signature('TBD')

            if uut_id not in fail_uut_list and isinstance(mes_obj, MES):
                # PASS: Save the following to be uploaded to MES later:
                # - Passmark Timestamp
                if isinstance(mes_obj, MES):
                    mes_obj.save_res_passmark(mtp_mgmt_ctrl.get_passmark_timestamp())

        # copy additional logs
        mtp_mgmt_ctrl.tor_copy_sys_log(log_dir + log_sub_dir)

        mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Complete", level=0)

        # shut down system
        if uut_id in pass_uut_list:
            mtp_mgmt_ctrl.uut_chassis_shutdown()
        else:
            # if OS has been installed and system failed,
            # reboot to get last session's logs
            if not mtp_mgmt_ctrl._svos_boot:
                mtp_mgmt_ctrl.tor_boot_select(1)
                mtp_mgmt_ctrl.save_prev_sys_logs()


        mfg_dl_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG DL Test Duration:{:s}".format(mfg_dl_stop_ts - mfg_dl_start_ts))

        # ########### TEST SUMMARY
        # all_slots_hist = dict()
        # all_slots_hist["NIC_GOLDFW_BOOT"] = mtp_mgmt_ctrl.tor_nic_gold_boot(operation=PRINT_TEST_HISTORY)
        # all_slots_hist["NIC_GOLDFW_VERIFY"] = mtp_mgmt_ctrl.mtp_mgmt_verify_nic_gold_boot(operation=PRINT_TEST_HISTORY)
        # all_slots_hist["MEMTUN_INIT"] = mtp_mgmt_ctrl.tor_nic_memtun_init(operation=PRINT_TEST_HISTORY)
        # all_slots_hist["NIC_PROFILE_CONFIG"] = mtp_mgmt_ctrl.tor_nic_Setup_device_config(operation=PRINT_TEST_HISTORY)
        # print(all_slots_hist)

        if uut_id in pass_uut_list:
            if stage == "DL2":
                sn = mtp_mgmt_ctrl.get_mtp_sn()
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(uut_id, card_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

            # PASS: Save the following to be uploaded to MES later:
            # - Test Status
            # - Test End Time
            # - (Clear the fail mode and signature just in case)
            if isinstance(mes_obj, MES):
                mes_obj.save_res_test_status("PASS")
                mes_obj.save_res_test_end_timestamp(libmfg_utils.timestamp_snapshot())
                mes_obj.save_res_fail_mode("N/A")
                mes_obj.save_res_fail_signature("N/A")

                mes_obj.push_results_to_mes()

        if uut_id in fail_uut_list:
            # if stage == "DL2":
            #     sn = mtp_mgmt_ctrl.get_mtp_sn()
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(uut_id, card_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

            # FAIL: Save the following to be uploaded to MES later:
            # - Test Status
            # - Test End Time
            # - (Clear the passmark just in case)
            if isinstance(mes_obj, MES):
                mes_obj.save_res_test_status("FAIL")
                mes_obj.save_res_test_end_timestamp(libmfg_utils.timestamp_snapshot())
                mes_obj.save_res_passmark("N/A")

                mes_obj.push_results_to_mes()

    except Exception as e:
        if uut_id not in fail_uut_list:
            fail_uut_list.append(uut_id)
        if uut_id in pass_uut_list:
            pass_uut_list.remove(uut_id)
        exit_fail(mtp_mgmt_ctrl, log_filep_list, traceback.format_exc())

def main():
    parser = argparse.ArgumentParser(description="MFG DL Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--DL1", "-DL1", "--dl1", "-dl1", "-1", help="station to program system FRU MAC", action="store_true")
    parser.add_argument("--DL2", "-DL2", "--dl2", "-dl2", "-2", help="station for rest of the things", action="store_true")
    parser.add_argument("--mtpid", "--mtp-id", "--uut-id", "--uutid", "-uutid", "-mtpid", help="pre-select UUTs", nargs="*", default=[])
    parser.add_argument("--no_mes", help="do not access Foxconn MES system", action='store_true')

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    mes_obj = None
    if args.no_mes:
        print("Script will NOT access the Foxconn MES Shop Floor System")
    else:
        print("Script will access the Foxconn MES Shop Floor System")
        mes_obj = MES()

        # Save the following to be uploaded to MES later:
        # - Test Start Time
        mes_obj.save_res_test_start_timestamp(libmfg_utils.timestamp_snapshot())


    if args.DL1:
        stage = "DL1"
    else:
        stage = "DL2"

    TAORMINA_TEST = True
    if TAORMINA_TEST:

        ######################################
        mtp_cfg_db = load_mtp_cfg()

        pass_rslt_list = list()
        fail_rslt_list = list()
        log_dir = "log/"
        os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir))

        # Get the scanned barcode information from Operator
        scan_rslt = {}
        if stage == 'DL2' and not isinstance(mes_obj, MES):
            # Non-MES CMs skip this section during DL2
            pass
        else:
            print("Start the Barcode Scan Process")
            while True:
                scan_rslt = libmfg_utils.uut_barcode_scan(mtp_cfg_db._mtpid_list)
                if scan_rslt:
                    break;
                print("Restart the Barcode Scan Process")

            # print scan summary
            for uut_id in scan_rslt.keys():
                uut_cli_id_str = libmfg_utils.id_str(mtp = uut_id)
                if scan_rslt[uut_id]["UUT_VALID"]:
                    sn = scan_rslt[uut_id]["UUT_SN"]
                    pn = scan_rslt[uut_id]["UUT_PN"]
                    edc = scan_rslt[uut_id]["UUT_EDC"]
                    mac_ui = libmfg_utils.mac_address_format(scan_rslt[uut_id]["UUT_MAC"])
                    pass_rslt_list.append(uut_cli_id_str + "SN = " + sn + "; MAC = " + mac_ui + "; PN = " + pn + "; EDC = " + edc)
                else:
                    fail_rslt_list.append(uut_cli_id_str + "UUT Absent")
            libmfg_utils.cli_log_rslt("Barcode Scan Summary", pass_rslt_list, fail_rslt_list, open("/dev/null", "w"))


        if isinstance(mes_obj, MES):
            uut_id_list = scan_rslt.keys()

            # Save the following to be uploaded to MES later:
            # - Test Station
            # - Test Rack location
            # - Chassis Base SN
            mes_obj.save_res_test_station(stage)
            mes_obj.save_res_test_location(uut_id_list[0])
            mes_obj.save_res_chassis_sn(scan_rslt[uut_id_list[0]]['UUT_SN'])

        if stage == "DL1":
            # save scanned barcodes
            scan_cfg_file = log_dir + "dl_barcode.yaml"
            with open(scan_cfg_file, "w+") as scan_cfg_filep:
                libmfg_utils.gen_barcode_config_file(scan_cfg_filep, scan_rslt)
            # log_file_list.append(scan_cfg_file)

            # reload the barcode config file
            fru_cfg = libmfg_utils.load_cfg_from_yaml(scan_cfg_file)

        elif stage == "DL2":

            if isinstance(mes_obj, MES):
                uut_id_list = scan_rslt.keys()
            else:
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
                fru_cfg[uut_id]["EDC"] = None

        ######################################

        pass_uut_list = list()
        fail_uut_list = list()

        uut_thread_list = list()
        logfile_dict = dict()


        if stage == "DL1":
            # sequential
            for uut in fru_cfg.keys():
                if uut in fail_uut_list:
                    continue
                if not fru_cfg[uut]["VALID"]:
                    continue

                logfile_dict[uut] = list()
                single_uut_fw_program(stage,
                                        fru_cfg[uut],
                                        fail_uut_list,
                                        pass_uut_list,
                                        logfile_dict[uut],
                                        verbosity,
                                        mes_obj,
                                        scan_rslt,
                                        args.skip_test)

        elif stage == "DL2":
            # parallel
            for uut in fru_cfg.keys():
                if uut in fail_uut_list:
                    continue
                if not fru_cfg[uut]["VALID"]:
                    continue

                logfile_dict[uut] = list()
                uut_thread = threading.Thread(
                                        target = single_uut_fw_program,
                                        args = (stage,
                                                fru_cfg[uut],
                                                fail_uut_list,
                                                pass_uut_list,
                                                logfile_dict[uut],
                                                verbosity,
                                                mes_obj,
                                                scan_rslt,
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
            sn = fru_cfg[uut_id]["SN"]
            nic_type = NIC_Type.TAORMINA
            if not sn:
                continue
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_DL_LOG_DIR_FMT.format(nic_type, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_DL_LOG_DIR_FMT.format(nic_type, sn)
            os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir))
            libmfg_utils.cli_inf("[{:s}] Collecting log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
            os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))
            os.system("./aruba-log.sh {:s}".format(mfg_log_dir+os.path.basename(log_pkg_file)))

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
        #### END OF TAORMINA TEST

if __name__ == "__main__":
    main()

