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
from libmfg_cfg import *
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
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
        usb_ts_cfg = mtp_cfg_db.get_mtp_usb_console(mtp_id)
        if not usb_ts_cfg:
            if ALLOW_TEST_FROM_TERMSERVER:
                pass
            else:
                libmfg_utils.sys_exit(mtp_cli_id_str + "Missing USB console server config")
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
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, console_log_filep, diag_nic_log_filep_list, ts_cfg=mtp_ts_cfg, usb_ts_cfg=usb_ts_cfg, apc_cfg=mtp_apc_cfg, num_of_slots=2, slots_to_skip=mtp_slots_to_skip)
    if telnet:
        mtp_mgmt_ctrl.set_uut_type(UUT_Type.TOR)

    if not ALLOW_TEST_FROM_TERMSERVER:
        mtp_mgmt_ctrl.set_usb_console() # For LED test, access from USB console server instead of regular terminal server

    return mtp_mgmt_ctrl

def single_uut_led_checks(stage,
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
    error_msg = ""

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

    qspi_fa_img_file = TOR_IMAGES.first_article_img[uut_type]
    os_test_img_file = TOR_IMAGES.os_test_img[uut_type]
    os_test_exp_version = TOR_IMAGES.os_test_dat[uut_type]
    os_ship_img_file = TOR_IMAGES.os_ship_img[uut_type]
    os_ship_exp_version = TOR_IMAGES.os_ship_dat[uut_type]
    tpm_img = TOR_IMAGES.tpm_img[uut_type]
    svos_util_img_file = TOR_IMAGES.svos_fpga_image[uut_type]
    usb_img = TOR_IMAGES.usb_img[uut_type]

    fpga_img_file = TOR_IMAGES.fpga_img[uut_type]
    test_fpga_img_file = TOR_IMAGES.test_fpga_img[uut_type]
    gpio_cpld_img_file = TOR_IMAGES.gpio_cpld_test_img[uut_type]
    cpu_cpld_img_file = TOR_IMAGES.cpu_cpld_test_img[uut_type]
    cpld_img_file = NIC_IMAGES.cpld_img[card_type]
    fail_cpld_img_file = NIC_IMAGES.fail_cpld_img[card_type]
    fea_cpld_img_file = NIC_IMAGES.fea_cpld_img[card_type]

    try:
        if not fru_cfg["SN"]:
            fru_cfg["SN"] = "UNKNOWN"

        testlist = ["SVOS_BOOT", "CONSOLE_CLEAR", "CONSOLE_CONNECT"]

        if isinstance(mes_obj, MES):
            # Add MES tasks in front, if applicable
            testlist = ["MES_ACCESS", "OK_TEST_STN_CHK",] + testlist

        for test in testlist:
            start_ts = mtp_mgmt_ctrl.log_test_start(test)

            if test == "SVOS_BOOT":
                ret = mtp_mgmt_ctrl.tor_boot_select(0, console_sanity_check=True)
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
                ret = mes_obj.verify_next_test_station("LED TEST")
                if not ret:
                    mtp_mgmt_ctrl.cli_log_err("UUT is NOT allowed to run " + stage, level=0)
                    mtp_mgmt_ctrl.cli_log_inf("TEST STATION EXPECTED: " + \
                        mes_obj.get_mes_next_test_station(), level=0)
                    mtp_mgmt_ctrl.cli_log_inf("Test data will NOT be pushed to MES")
                    mes_obj.clear_push_to_mes()
                    return
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
                    mes_obj.save_res_fail_signature(error_msg)
                    mes_obj.save_res_test_end_timestamp(libmfg_utils.timestamp_snapshot())
                    mes_obj.save_res_passmark("N/A")

                    mes_obj.push_results_to_mes()

                return

        mtp_mgmt_ctrl.cli_log_inf("UUT Chassis is connected", level=0)

        if stage == "LED":
            # read FRU
            # mtp_mgmt_ctrl.tor_fru_init()
            sn = mtp_mgmt_ctrl._sn
            fru_cfg["SN"] = sn

        if uut_id not in pass_uut_list:
            pass_uut_list.append(uut_id)

        mtp_mgmt_ctrl.print_script_version()

        mtp_mgmt_ctrl.cli_log_inf("Firmware Download Process Started", level=0)
        mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

        ### X86 HOST TESTS
        if stage == "LED":
            testlist = [
                        "MES_SCAN_INPUT_CHK",
                        "MES_FRU_EEPROM_CHK",
                        "MGMT_INIT",
                        "DOWNLOAD_USB_LED_TOOL",
                        "TEST_LED_GREEN",
                        "TEST_LED_ORANGE",
                        "OS_BOOT",
                        "MES_MFG_EEPROM_CHK",
                        ]

        for skipped_test in skip_testlist:
            if skipped_test in testlist:
                testlist.remove(skipped_test)
        for test in testlist:
            mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
            start_ts = mtp_mgmt_ctrl.log_test_start(test)

            if test == "MGMT_INIT":
                ret = mtp_mgmt_ctrl.tor_mgmt_init()
            elif test == "DOWNLOAD_USB_LED_TOOL":
                ret = mtp_mgmt_ctrl.tor_svos_led_usb_setup(usb_img)
            elif test == "TEST_LED_GREEN":
                ret = mtp_mgmt_ctrl.tor_led_test('green')
            elif test == "TEST_LED_ORANGE":
                ret = mtp_mgmt_ctrl.tor_led_test('orange')
            elif test.startswith("OS_BOOT"):
                ret = mtp_mgmt_ctrl.tor_boot_select(1)

            elif test == "MES_SCAN_INPUT_CHK":
                if not isinstance(mes_obj, MES):
                    continue

                # Verify scanned input against MES data
                mtp_mgmt_ctrl.cli_log_inf("Verify scanned input against MES data", level=0)
                ret = mes_obj.verify_scanned_input_against_mes(scan_rslt[uut_id])

            elif test == "MES_FRU_EEPROM_CHK":
                if not isinstance(mes_obj, MES):
                    continue

                # Verify FRU EEPROM contents against MES data
                eeprom_contents = dict()
                msg = "Verify FRU EEPROM contents against MES data"
                mtp_mgmt_ctrl.cli_log_inf(msg, level=0)
                ret, eeprom_contents = mtp_mgmt_ctrl.get_eeprom_contents()
                if ret:
                    ret = mes_obj.verify_eeprom_against_mes(eeprom_contents, eeprom_type='fru')

            elif test == "MES_MFG_EEPROM_CHK":
                if not isinstance(mes_obj, MES):
                    continue

                # Verify Locked MFG EEPROM contents against MES data
                eeprom_contents = dict()
                msg = "Verify Locked MFG EEPROM contents against MES data"
                mtp_mgmt_ctrl.cli_log_inf(msg, level=0)
                ret, eeprom_contents = \
                    mtp_mgmt_ctrl.get_eeprom_contents(eeprom_location='mfg_l')
                if ret:
                    ret = mes_obj.verify_eeprom_against_mes(eeprom_contents,
                        eeprom_type='mfg_l')

                    # Verify Unlocked MFG EEPROM contents against MES data
                    if ret:
                        msg = "Verify Unlocked MFG EEPROM contents against MES data"
                        mtp_mgmt_ctrl.cli_log_inf(msg, level=0)
                        ret, eeprom_contents = \
                            mtp_mgmt_ctrl.get_eeprom_contents(eeprom_location='mfg_ul')
                        if ret:
                            ret = mes_obj.verify_eeprom_against_mes(eeprom_contents,
                                eeprom_type='mfg_ul')

            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown DL Test: {:s}, Ignore".format(test))
                continue
            duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_mgmt_ctrl.tor_sys_failure_dump()
                if uut_id not in fail_uut_list:
                    fail_uut_list.append(uut_id)
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)

                # FAIL: Save the following to be uploaded to MES later:
                # - Test Fail Mode
                # - Test Fail Signature
                if isinstance(mes_obj, MES):
                    mes_obj.save_res_fail_mode(test)
                    mes_obj.save_res_fail_signature(error_msg)

                break
            else:
                mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)

            if test == "TEST_LED_ORANGE":
                mtp_mgmt_ctrl.cli_log_inf("Question Process Complete", level=0)

        mtp_mgmt_ctrl.cli_log_inf("Host tests completed\n", level=0)

        if uut_id not in fail_uut_list and stage == "LED":
            if not mtp_mgmt_ctrl.tor_fru_passmark(stage):
                if uut_id in pass_uut_list:
                    pass_uut_list.remove(uut_id)
                if uut_id not in fail_uut_list:
                    fail_uut_list.append(uut_id)

                # FAIL: Save the following to be uploaded to MES later:
                # - Test Fail Mode
                # - Test Fail Signature
                if isinstance(mes_obj, MES):
                    mes_obj.save_res_fail_mode('Failed to program LED passmark')
                    mes_obj.save_res_fail_signature(error_msg)

            else:
                # PASS: Save the following to be uploaded to MES later:
                # - Passmark Timestamp
                if isinstance(mes_obj, MES):
                    mes_obj.save_res_passmark(mtp_mgmt_ctrl.get_passmark_timestamp())

        # copy additional logs
        mtp_mgmt_ctrl.tor_copy_sys_log(log_dir + log_sub_dir)

        time.sleep(5) #?

        if uut_id in fail_uut_list:
            # if OS has been installed and system failed,
            # reboot to get last session's logs
            if not mtp_mgmt_ctrl._svos_boot:
                mtp_mgmt_ctrl.tor_boot_select(1)
                mtp_mgmt_ctrl.save_prev_sys_logs()

        # shut down system
        mtp_mgmt_ctrl.uut_chassis_shutdown()

        mfg_dl_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG LED Test Duration:{:s}".format(mfg_dl_stop_ts - mfg_dl_start_ts))

        if uut_id in pass_uut_list:
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
        exit_fail(mtp_mgmt_ctrl, log_filep_list, traceback.print_exc())

def main():
    parser = argparse.ArgumentParser(description="MFG LED Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--LED", "-LED", "--led", "-led", "-1", help="station to LED test", action="store_true")
    parser.add_argument("--mtpid", "--mtp-id", "--uut-id", "--uutid", "-uutid", "-mtpid", help="pre-select UUTs", nargs="*", default=[])
    parser.add_argument("--no_mes", help="do not access Foxconn MES system", action='store_true')
    parser.add_argument("--operator", help="specify Operator name")


    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    if args.LED:
        stage = "LED"

    mes_obj = None
    if args.no_mes:
        print("Script will NOT access the Foxconn MES Shop Floor System")
    else:
        print("Script will access the Foxconn MES Shop Floor System")
        mes_obj = MES()

        # Save the following to be uploaded to MES later:
        # - Test Start Time
        # - Test Station
        # - Operator ID
        mes_obj.save_res_test_start_timestamp(libmfg_utils.timestamp_snapshot())
        mes_obj.save_res_test_station("LED TEST")
        if args.operator:
            mes_obj.save_res_operator_id(args.operator)


    TAORMINA_TEST = True
    if TAORMINA_TEST:

        ######################################
        mtp_cfg_db = load_mtp_cfg()

        pass_rslt_list = list()
        fail_rslt_list = list()
        log_dir = "log/"
        os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir))

        if stage == "LED":

            scan_rslt = {}
            if isinstance(mes_obj, MES):
                # Get the scanned barcode information from Operator
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
                        pass_rslt_list.append(uut_cli_id_str + "SN = " + sn + \
                            "; MAC = " + mac_ui + "; PN = " + pn + "; EDC = " + edc)
                    else:
                        fail_rslt_list.append(uut_cli_id_str + "UUT Absent")
                libmfg_utils.cli_log_rslt("Barcode Scan Summary", pass_rslt_list,
                    fail_rslt_list, open("/dev/null", "w"))

            if isinstance(mes_obj, MES):
                uut_id_list = scan_rslt.keys()

                # Save the following to be uploaded to MES later:
                # - Test Rack location
                # - Chassis Base SN
                mes_obj.save_res_test_location(uut_id_list[0])
                mes_obj.save_res_chassis_sn(scan_rslt[uut_id_list[0]]['UUT_SN'])

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

        ######################################

        pass_uut_list = list()
        fail_uut_list = list()

        uut_thread_list = list()
        logfile_dict = dict()


        if stage == "LED":
            # sequential
            for uut in fru_cfg.keys():
                if uut in fail_uut_list:
                    continue
                if not fru_cfg[uut]["VALID"]:
                    continue

                logfile_dict[uut] = list()
                single_uut_led_checks(stage,
                                        fru_cfg[uut],
                                        fail_uut_list,
                                        pass_uut_list,
                                        logfile_dict[uut],
                                        verbosity,
                                        mes_obj,
                                        scan_rslt,
                                        args.skip_test)


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

