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
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import PSLC_MODE_TYPE_LIST
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import GIGLIO_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libsku_cfg import PART_NUMBERS_MATCH
from libdefs import FF_Stage
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode
import image_control
import testlog
import test_utils


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

def single_nic_cpld_program(mtp_mgmt_ctrl, cpld_img_file, failsafe_cpld_img_file, slot, skip_testlist, nic_test_rslt_list):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    dsp = FF_Stage.CONVERT
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

    if nic_type == NIC_Type.ORTANO2ADIIBM:
        test_list = ["NOSECURE_CPLD_PROG", "NOSECURE_FAILSAFE_CPLD_PROG", "SET_DIAGFW_BOOT"]
    elif nic_type in FPGA_TYPE_LIST:
        test_list = ["FPGA_PROG"]
    else:
        test_list = ["CPLD_PROG"]

    for skip_test in skip_testlist:
        if skip_test in test_list:
            test_list.remove(skip_test)

    for test in test_list:
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        if test == "NOSECURE_CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_adi_ibm_cpld(slot, cpld_img_file)
        elif test == "NOSECURE_FAILSAFE_CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_adi_ibm_failsafe_cpld(slot, failsafe_cpld_img_file)
        elif test == "SET_DIAGFW_BOOT":
            ret = mtp_mgmt_ctrl.mtp_set_nic_diagfw_boot(slot)
        elif test == "CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
        elif test == "FPGA_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_fpga(slot)
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            nic_test_rslt_list[slot] = False
            mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

def main():
    parser = argparse.ArgumentParser(description="NIC Convert Test Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--fail-slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("--skip-slots", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--cpld", help="Reprog CPLD only", action='store_true', default=False)

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

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    try:
        tlf = testlog.get_mtp_test_log_folder(mtp_mgmt_ctrl)
        scan_cfg_file = os.path.join(tlf, MTP_DIAG_Logfile.SCAN_BARCODE_FILE)
        nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(scan_cfg_file)

        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, FF_Stage.CONVERT, args.skip_test):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            logfile_close(open_file_track_list)
            return

        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        fail_nic_list = list()
        pass_nic_list = list()
        adi_ibm_reset_slot = list()

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
        mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.mtp_power_on_nic(pass_nic_list, dl=True)

        dsp = FF_Stage.CONVERT

        mtp_mgmt_ctrl.cli_log_inf("NIC CONVERT Test Started", level=0)
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            key = libmfg_utils.nic_key(slot)
            valid = nic_fru_cfg[mtp_id][key]["VALID"]
            if str.upper(valid) != "YES":
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot")
                continue

            sn = nic_fru_cfg[mtp_id][key]["SN"]
            mac = nic_fru_cfg[mtp_id][key]["MAC"]
            pn = nic_fru_cfg[mtp_id][key]["PN"]
            prog_date = str(nic_fru_cfg[mtp_id][key]["TS"])
            mac_ui = libmfg_utils.mac_address_format(mac)
            alom_sn = None
            alom_pn = None
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
               if "SN_ALOM" in nic_fru_cfg[mtp_id][key]:
                   alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
                   alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]

            riser_sn = None
            if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25OCP:
                riser_sn = mtp_mgmt_ctrl.mtp_get_nic_ocp_adapter_sn(slot)

            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

            print("")
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix:")
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
                alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}; SN_ALOM = {:s}; PN_ALOM = {:s}".format(sn, mac_ui, pn, alom_sn, alom_pn))
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}".format(sn, mac_ui, pn))
            if nic_type == NIC_Type.NAPLES25OCP:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "OCP Adapter SN = {:s}".format(riser_sn))

            dl_image_dict = image_control.get_all_images_for_stage(mtp_mgmt_ctrl, nic_type, dsp)
            for image_name, image_file_path in dl_image_dict.items():
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, image_name + " image: " + os.path.basename(image_file_path))
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end")


        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            if not nic_prsnt_list[slot]:
                continue
                
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

            test_list = []
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                test_list = ["CONSOLE_BOOT_INIT","ERASE_BOARD_CONFIG"]
            else:
                test_list = ["CONSOLE_BOOT"]

            for test in test_list:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                if test == "CONSOLE_BOOT":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(slot)
                elif test == "CONSOLE_BOOT_INIT":
                    ret = mtp_mgmt_ctrl.mtp_mgmt_nic_console_access(slot)
                elif test == "ERASE_BOARD_CONFIG":
                    ret = mtp_mgmt_ctrl.mtp_nic_erase_board_config(slot)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
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

        if not mtp_mgmt_ctrl.mtp_nic_diag_init(pass_nic_list, emmc_format=True, emmc_check=True, fru_fpo=True):
            mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                if not nic_prsnt_list[slot]:
                    continue
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        nic_thread_list = list()
        nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            if not nic_prsnt_list[slot]:
                continue

            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, nic_type, dsp)["filename"]
            failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, nic_type, dsp)["filename"]
            nic_thread = threading.Thread(target = single_nic_cpld_program, args = (mtp_mgmt_ctrl,
                                                                                    cpld_img_file,
                                                                                    failsafe_cpld_img_file,
                                                                                    slot,
                                                                                    args.skip_test,
                                                                                    nic_test_rslt_list))
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

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not nic_test_rslt_list[slot]:
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)



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

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                continue
            key = libmfg_utils.nic_key(slot)
            valid = nic_fru_cfg[mtp_id][key]["VALID"]
            if str.upper(valid) != "YES":
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot")
                continue

            # DL Verify process
            sn = nic_fru_cfg[mtp_id][key]["SN"]
            mac = nic_fru_cfg[mtp_id][key]["MAC"]
            pn = nic_fru_cfg[mtp_id][key]["PN"]
            prog_date = str(nic_fru_cfg[mtp_id][key]["TS"])
            exp_sn = sn
            exp_mac = "-".join(re.findall("..", mac))
            exp_pn = pn
            exp_date = prog_date
            alom_sn = None
            alom_pn = None
            exp_alom_sn = None
            exp_alom_pn = None
            exp_assettag = None
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = nic_fru_cfg[mtp_id][key]["SN_ALOM"]
                alom_pn = nic_fru_cfg[mtp_id][key]["PN_ALOM"]
                exp_alom_sn = alom_sn
                exp_alom_pn = alom_pn
                exp_assettag = 'C0'
                hpe_pn = "000000-000"

            testlist = ["NIC_POWER", "NIC_DIAG_BOOT", "CPLD_VERIFY", ]
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type in FPGA_TYPE_LIST:
                testlist = ["NIC_POWER", "NIC_DIAG_BOOT", "CPLD_VERIFY", "FPGA_PROG_VERIFY"]
            else:
                testlist = ["NIC_POWER", "NIC_DIAG_BOOT", "CPLD_VERIFY"]
            for skip_test in args.skip_test:
                if skip_test in testlist:
                    testlist.remove(skip_test)

            for test in testlist:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                # nic power status check
                if test == "NIC_POWER":
                    ret = True
                    if nic_type != NIC_Type.NAPLES100IBM:
                        ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)    
                # nic present check
                elif test == "NIC_PRSNT":
                    ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
                elif test == "NIC_DIAG_BOOT":
                    ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
                # verify CPLD
                elif test == "CPLD_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)
                # verify FPGA against original file
                elif test == "FPGA_PROG_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_fpga(slot)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                    continue

                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)
                    mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                    break
                else:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, dsp, test, duration))

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

