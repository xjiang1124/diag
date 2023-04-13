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
import libtest_utils
from libtest import test_inst
from libdefs import *
from libmfg_cfg import *
# from libmtp_ctrl import mtp_ctrl
from tests import *


def single_uut_test(uut_id, mtp_cfg_db, uut_test_rslt_dict, test_ctrl_list):

    for test_ctrl in test_ctrl_list:
        # init mtp_ctrl
        mtp_mgmt_ctrl = test_ctrl.mtp_mgmt_ctrl_init(mtp_cfg_db, uut_id)
        if not mtp_mgmt_ctrl:
            uut_test_rslt_dict[uut_id] = False
            libmfg_utils.sys_exit("Test Aborted")
            return

        test_ctrl.cli_log_inf("MFG {:s} Test Start".format(test_ctrl.stage), level=0)

        # move this outside script into testsuite parameters
        if test_ctrl.stage == FF_Stage.FF_DL:
            pcie_fpo = True
        else:
            pcie_fpo = False


        try:
            # start test
            mfg_test_start_ts = libmfg_utils.timestamp_snapshot()
            test_ctrl.print_script_version()

            test_ctrl.mtp._sn["SYSTEM"] = test_ctrl.barcode_scans[uut_id][barcode.SYS_SN]
            sn = test_ctrl.mtp.get_mtp_sn()

            barcode.log_barcodes(test_ctrl, test_ctrl.barcode_scans[uut_id])

            if test_ctrl.stage == FF_Stage.FF_DL1:
                test_ctrl.cli_log_inf("Programming Matrix:", level=0)
                test_ctrl.cli_log_inf("==> RT8116: {:s} <==".format(test_ctrl.image["rt_img"]), level=1)
                # test_ctrl.cli_log_inf("==> ONIE: {:s} <==".format(test_ctrl.image["onie_img"]), level=1)
                test_ctrl.cli_log_inf("==> SONiC: {:s} <==".format(test_ctrl.image["os_img"]), level=1)
                test_ctrl.cli_log_inf("Programming Matrix end\n", level=0)
            elif test_ctrl.stage == FF_Stage.FF_DL:
                test_ctrl.cli_log_inf("Programming Matrix:", level=0)
                test_ctrl.cli_log_inf("==> SONiC: {:s} <==".format(test_ctrl.image["os_img"]), level=1)
                test_ctrl.cli_log_inf("==> BIOS: {:s} <==".format(test_ctrl.image["bios_img"]), level=1)
                test_ctrl.cli_log_inf("==> FPGA0: {:s} <==".format(test_ctrl.image["fpga0_img"]), level=1)
                test_ctrl.cli_log_inf("==> FPGA1: {:s} <==".format(test_ctrl.image["fpga1_img"]), level=1)
                test_ctrl.cli_log_inf("==> CPU CPLD: {:s} <==".format(test_ctrl.image["cpu_cpld_img"]), level=1)
                test_ctrl.cli_log_inf("==> ELBA CPLD: {:s} <==".format(test_ctrl.image["nic_cpld_img"]), level=1)
                test_ctrl.cli_log_inf("==> ELBA boot0: {:s} <==".format(test_ctrl.image["boot0_img"]), level=1)
                test_ctrl.cli_log_inf("==> ELBA ubootg: {:s} <==".format(test_ctrl.image["ubootg_img"]), level=1)
                test_ctrl.cli_log_inf("==> ELBA goldfw: {:s} <==".format(test_ctrl.image["goldfw_img"]), level=1)
                test_ctrl.cli_log_inf("==> ELBA uboota: {:s} <==".format(test_ctrl.image["uboota_img"]), level=1)
                test_ctrl.cli_log_inf("==> ELBA mainfw: {:s} <==".format(test_ctrl.image["mainfwa_img"]), level=1)
                test_ctrl.cli_log_inf("Programming Matrix end\n", level=0)

            test_list = test_ctrl.test_list
            for test in test_list:
                if test in test_ctrl.skip_test_list:
                    continue
                sn = test_ctrl.mtp.get_mtp_sn() #refresh to get latest
                test_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, test_ctrl.stage, test), level=0)
                start_ts = test_ctrl.log_test_start(test)
                for slot in range(test_ctrl.mtp._slots):
                    test_ctrl.log_slot_test_start(slot, test)

                # boot test OS
                if test == "OS_BOOT":
                    ret = boot.tor_os_boot(test_ctrl)
                elif test == "ONIE_BOOT":
                    ret = boot.tor_onie_boot(test_ctrl)
                elif test == "CONSOLE_CLEAR":
                    ret = test_ctrl.mtp.mtp_clear_console()
                elif test == "CONSOLE_CONNECT":
                    ret = test_ctrl.mtp.mtp_console_connect()
                elif test == "MGMT_INIT":
                    ret = test_ctrl.mtp.tor_mgmt_init()
                elif test == "DIAG_INIT":
                    ret = diag.tor_diag_init(test_ctrl)
                elif test == "NIC_INIT":
                    ret = test_ctrl.mtp.tor_nic_init()
                elif test == "BOARD_ID":
                    ret = test_ctrl.mtp.mtp_sys_info_disp(fru_valid=True)

                elif test == "SSD_ERASE":
                    ret = tor_os.erase_ssd(test_ctrl)
                elif test == "FRU_PROG":
                    ret = fru.fru_prog(test_ctrl, test_ctrl.barcode_scans[uut_id])
                elif test == "FRU_VERIFY":
                    ret = fru.fru_verify(test_ctrl, test_ctrl.barcode_scans[uut_id])
                elif test == "FRU_ERASE":
                    ret = fru.fru_erase(test_ctrl)
                elif test == "ONIE_UPDATE":
                    ret = onie.onie_prog(test_ctrl, test_ctrl.image)
                elif test == "ONIE_VERIFY":
                    ret = onie.onie_verify(test_ctrl, test_ctrl.image)
                elif test == "SONIC_UPDATE":
                    ret = tor_os.os_prog(test_ctrl, test_ctrl.image)
                elif test == "SONIC_VERIFY":
                    ret = tor_os.os_verify(test_ctrl, test_ctrl.image)
                elif test == "BIOS_UPDATE":
                    ret = bios.bios_prog(test_ctrl, test_ctrl.image)
                elif test == "BIOS_VERIFY":
                    ret = bios.bios_verify(test_ctrl, test_ctrl.image)
                elif test == "RT_NIC_PROG":
                    ret = realtek.rt_nic_prog(test_ctrl, test_ctrl.image)
                elif test == "RT_NIC_VERIFY":
                    ret = realtek.rt_nic_verify(test_ctrl, test_ctrl.image)
                elif test == "RT_MAC_PROG":
                    ret = realtek.rt_mac_prog(test_ctrl, test_ctrl.barcode_scans[uut_id])
                elif test == "RT_MAC_VERIFY":
                    ret = realtek.rt_mac_verify(test_ctrl, test_ctrl.barcode_scans[uut_id])
                elif test == "CPU_CPLD_PROG":
                    ret = cpld.cpu_cpld_prog(test_ctrl, test_ctrl.image)
                elif test == "NIC_CPLD_PROG":
                    ret = cpld.nic_cpld_prog(test_ctrl, test_ctrl.image)
                elif test == "NIC_FEA_CPLD_PROG":
                    ret = cpld.nic_fea_cpld_prog(test_ctrl, test_ctrl.image)
                elif test == "CPLD_REF":
                    ret = cpld.cpld_refresh(test_ctrl)

                elif test == "CPLD_VERIFY":
                    ret = cpld.cpld_verify(test_ctrl, test_ctrl.image)
                elif test == "FPGA_PROG":
                    ret = fpga.fpga_prog(test_ctrl, test_ctrl.image)
                elif test == "FPGA_VERIFY":
                    ret = fpga.fpga_verify(test_ctrl, test_ctrl.image)
                elif test == "NIC_QSPI_PROG":
                    ret = nic_qspi.nic_qspi_prog(test_ctrl, test_ctrl.image)
                elif test == "NIC_QSPI_VERIFY":
                    ret = nic_qspi.nic_qspi_verify(test_ctrl, test_ctrl.image)
                elif test == "NIC_GOLDFW_BOOT":
                    ret = nic_fw.set_goldfw_boot(test_ctrl, [])
                elif test == "NIC_GOLDFW_VERIFY":
                    ret = nic_fw.verify_goldfw_boot(test_ctrl)
                elif test == "NIC_PWRCYC":
                    ret = test_ctrl.mtp.mtp_power_cycle_nic()
                elif test == "MEMTUN_INIT":
                    ret = nic_pcie.memtun_init(test_ctrl)
                elif test == "NIC_PCIE_VERIFY":
                    ret = nic_pcie.nic_pcie_scan(test_ctrl, pcie_fpo)
                elif test == "NIC_EMMC_FORMAT":
                    ret = nic_emmc.format_emmc(test_ctrl)
                elif test == "EMMC_HWRESET_SET":
                    ret = nic_emmc.set_emmc_hwreset(test_ctrl)
                elif test == "EMMC_BKOPS_EN":
                    ret = nic_emmc.enable_emmc_bkops(test_ctrl)

                else:
                    test_ctrl.cli_log_err("Unknown test {:s}".format(test))
                    ret = False

                duration = test_ctrl.log_test_stop(test, start_ts)
                for slot in range(test_ctrl.mtp._slots):
                    test_ctrl.log_slot_test_stop(slot, test, start_ts)

                if not ret:
                    sn = test_ctrl.mtp.get_mtp_sn() #refresh to get latest
                    test_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, test_ctrl.stage, test, "FAILED", str(duration)), level=0)
                    uut_test_rslt_dict[uut_id] = False

                    # In 2C/4C, continue testing after failure, unless test was run with --stop-on-err
                    if test_ctrl.stage in (FF_Stage.FF_DL, FF_Stage.FF_DL1, FF_Stage.FF_SWI):
                        break
                    if test_ctrl.stop_on_test_failure:
                        break
                else:
                    test_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, test_ctrl.stage, test, str(duration)), level=0)


            sn = test_ctrl.mtp.get_mtp_sn()
            if not uut_test_rslt_dict[uut_id]:
                test_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(uut_id, "LIPARI", sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
            else:
                test_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(uut_id, "LIPARI", sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

            mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
            test_ctrl.cli_log_inf("MFG {:s} Test Duration:{:s}".format(test_ctrl.stage, str(mfg_test_stop_ts - mfg_test_start_ts)), level=0)
            test_ctrl.cli_log_inf("{:s} Test Process Complete".format(test_ctrl.stage), level=0)
            # shut down system
            if not uut_test_rslt_dict[uut_id]:
                test_ctrl.uut_chassis_shutdown()
            test_ctrl.save_logfiles()

            # dont continue testing
            if not uut_test_rslt_dict[uut_id] or test_ctrl.stop_on_test_failure:
                break

        except Exception as e:
            # err_msg = str(e)
            err_msg = traceback.format_exc()
            test_ctrl.mtp.mtp_dump_err_msg(err_msg)
            uut_test_rslt_dict[uut_id] = False
            test_ctrl.cli_log_err("{:s} {:s} {:s} {:s}".format(uut_id, "LIPARI", test_ctrl.mtp.get_mtp_sn(), MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
            test_ctrl.cli_log_inf("{:s} Test Aborted".format(test_ctrl.stage), level=0)
            test_ctrl.save_logfiles()
            return

    return

def main():
    parser = argparse.ArgumentParser(description="MFG Test Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--testsuite", "-testsuite", "-ts", "--ts", help="YAML testsuite file(s) to load", nargs="+", required=True)
    parser.add_argument("--barcode_file", "-scan_cfg", "--scan_cfg", "-scan", "--scan", help="load barcode scan from a file", default="")
    parser.add_argument("--mtpid", "--mtp-id", "--uut-id", "--uutid", "-uutid", "-mtpid", help="pre-select UUTs", nargs="*", default=[])
    parser.add_argument("--skip-test", help="skip particular test(s)", nargs="*", default=[])
    parser.add_argument("--repeat-test", help="repeat particular test(s) X times: e.g. --repeat-test 10 EDMA 5 SNAKE", nargs="*", default=[])
    parser.add_argument("--stop-on-failure", "--stop-on-err", help="stop on the failure of a particular test", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="Load setup configs from a different file", default=None)
    parser.add_argument("--logdir", help="Store final log to different path", default=None)

    args = parser.parse_args()

    testsuite_file_list = []
    for testsuite_file in args.testsuite:
        if not os.path.exists(testsuite_file):
            libmfg_utils.cli_err("Testsuite file {:s} cannot be found".format(testsuite_file))
            sys.exit(1)
        testsuite_file_list.append(testsuite_file)

    test_ctrl_list = []
    for testsuite_file in testsuite_file_list:
        test_ctrl = test_inst(testsuite_file, args.skip_test, args.repeat_test, args.stop_on_failure)
        if not test_ctrl:
            sys.exit(1)
        test_ctrl_list.append(test_ctrl)


    BARCODE_SCAN = True

    if args.mtpcfg:
        mtpcfg_file = os.path.relpath(args.mtpcfg)
        mtp_cfg_db = libtest_utils.load_mtp_cfg(mtpcfg_file)
    else:
        mtp_cfg_db = libtest_utils.load_mtp_cfg()

    if BARCODE_SCAN: #testconfig["Barcode Scan"] or testconfig["SCAN_VERIFY"]:
        if args.mtpid:
            valid_uut_list = list(args.mtpid)
        else:
            valid_uut_list = list(mtp_cfg_db.get_mtpid_list())

        if args.barcode_file:
            uut_fru_cfg = barcode.load_barcode_file(args.barcode_file, valid_uut_list)
        else:
            uut_fru_cfg = barcode.uut_barcode_scan(valid_uut_list)

        if uut_fru_cfg is None:
            sys.exit(1)

        uut_id_list = uut_fru_cfg.keys()

    else:
        # MTP Select Menu
        uut_id_list = libtest_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
        uut_fru_cfg = dict()
        for uut_id in uut_id_list:
            uut_fru_cfg[uut_id] = {barcode.SYS_SN: "SN_UNKNOWN"}

    for test_ctrl in test_ctrl_list:
        """
            if "Barcode Scan: Yes" in any testsuites or "SCAN_VERIFY" in any test_lists:
            do the barcode scan/file only once for all testsuites entered
            save it to each test_ctrl obj that needed it
        """
        test_ctrl.barcode_scans = uut_fru_cfg


    pass_uut_list = list()
    fail_uut_list = list()
    uut_test_rslt_dict = dict()
    uut_thread_list = list()

    for uut_id in uut_id_list:
        pass_uut_list.append(uut_id)
        uut_test_rslt_dict[uut_id] = True

    for uut_id in uut_id_list:
        if uut_id in fail_uut_list:
            continue

        uut_thread = threading.Thread(target = single_uut_test, args = (uut_id,
                                                                       mtp_cfg_db,
                                                                       uut_test_rslt_dict,
                                                                       test_ctrl_list))
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

    for uut_id in uut_id_list:
        if not uut_test_rslt_dict[uut_id]:
            if uut_id not in fail_uut_list:
                fail_uut_list.append(uut_id)
            if uut_id in pass_uut_list:
                pass_uut_list.remove(uut_id)

    ######## TEST SUMMARY ########
    test_summary_dict = dict()
    for uut_id in pass_uut_list:
        sn = uut_fru_cfg[uut_id]["CHASSIS Serial Number"]
        test_summary_dict[uut_id] = [(uut_id, sn, "LIPARI", True, False)]
    
    for uut_id in fail_uut_list:
        sn = uut_fru_cfg[uut_id]["CHASSIS Serial Number"]
        test_summary_dict[uut_id] = [(uut_id, sn, "LIPARI", False, False)]

    test_result = test_ctrl.mfg_uut_summary_disp(test_summary_dict)

    # print return code for JobD to pick up
    if test_result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
