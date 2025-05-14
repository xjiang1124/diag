#!/usr/bin/env python

import sys
import os
import time
import pexpect
import threading
import argparse
import re
import copy
import json
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
from libdefs import FLEX_TWO_WAY_COMM
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import FLEX_SHOP_FLOOR_CONTROL
from libmfg_cfg import ROT_CABLE_REQUIRED_FOR_FST_TYPE_LIST
from libmfg_cfg import FST_SCAN_ENABLE
from libmfg_cfg import FLEX_ERR_CODE_MAP
from libmfg_cfg import SALINA_NIC_TYPE_LIST
from libmfg_cfg import SALINA_AI_NIC_TYPE_LIST
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
import test_utils
import testlog
import scanning
import barcode_field as bf

def load_mtp_usb_serial_port(mtp_mgmt_ctrl):
    usb_serial = []
    for port in range(5):
        port_pre = os.system("ls /dev/ttyUSB{} > /dev/null 2>&1".format(port))
        if port_pre == 0:
            usb_serial.append("ttyUSB{}".format(port))
            mtp_mgmt_ctrl.cli_log_inf("Found /dev/ttyUSB{}".format(port))
    return usb_serial

def check_rot(mtp_mgmt_ctrl, nic_list, s4_family):
    if len(nic_list) == 0:
        mtp_mgmt_ctrl.cli_log_err("No NICs passed", level=0)
        return [], []
    # not support run multiple cards with different card type in one batch
    nic_types = [mtp_mgmt_ctrl.mtp_get_nic_type(slot) for slot in nic_list]
    nic_types = list(set(nic_types))
    if len(nic_types) > 1:
        return [], []
    nic_type = nic_types[0]

    pass_list, fail_list = [], []
    serial_ports = []
    serial_ports = load_mtp_usb_serial_port(mtp_mgmt_ctrl)

    if len(serial_ports) == 0:
        mtp_mgmt_ctrl.cli_log_err("No NICs connected to ROT - maybe USB hub not connected?")
        return [], nic_list

    result = ""
    for port in serial_ports:
        if s4_family:
            cmd = "mfg_test_script/rotctrl -b 115200 -d elba-gold -c ortano -p {:s}".format(port)
        elif nic_type in SALINA_NIC_TYPE_LIST:
            cmd = "mfg_test_script/rotctrl_salina -b 115200 -d salina -c {:s} -p {:s}".format(nic_type.lower(), port)
        else:
            cmd = "mfg_test_script/rotctrl -b 115200 -d elba -c ortano -p {:s}".format(port)

        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_FST_TEST_TIMEOUT):
            mtp_mgmt_ctrl.cli_log_err("Executing ROT test over usb port {:s} Failed".format(port), level=0)
        cmd_buf = mtp_mgmt_ctrl.mtp_get_cmd_buf()
        if "FAIL" in cmd_buf:
            mtp_mgmt_ctrl.cli_log_err("NIC at serial port {:s} failed".format(port), level=0)
            mtp_mgmt_ctrl.cli_log_err(cmd_buf)
        result += cmd_buf
    pass_reg_exp_rot = re.compile("ROT test PASSED ([A-Za-z0-9]*)")
    fail_reg_exp_rot = re.compile("ROT test FAILED ([A-Za-z0-9]*)")
    pass_match_rot = pass_reg_exp_rot.findall(result)
    fail_match_rot = fail_reg_exp_rot.findall(result)

    # Matching game
    # match slot to SN, finding missing ones.
    for slot in nic_list:
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if sn in pass_match_rot:
            pass_list.append(slot)
        elif sn in fail_match_rot:
            fail_list.append(slot)
        else:
            fail_list.append(slot)

    # Save the logs
    testlog_path = testlog.find_logfile_path(mtp_mgmt_ctrl, FF_Stage.FF_FST)
    for sn in pass_match_rot + fail_match_rot:
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("cp /home/diag/{:s}.log {:s}/rot_{:s}.log".format(sn, testlog_path, sn), timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("rm /home/diag/{:s}.log".format(sn), timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)
    for port in serial_ports:
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("cp /home/diag/{:s}.log {:s}/rot_{:s}.log".format(port, testlog_path, port), timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("rm /home/diag/{:s}.log".format(port), timeout=MTP_Const.MFG_FST_TEST_TIMEOUT)

    return pass_list, fail_list

def logfile_close(filep_list):
    for fp in filep_list:
        fp.close()
    os.system("sync")


def load_mtp_cfg(cfgyml = None):
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/fst_mtps_chassis_cfg.yaml"))
    if cfgyml:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/"+cfgyml))
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

def main():
    parser = argparse.ArgumentParser(description="MTP Final Stage Test Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTPS-001, etc", required=True)
    parser.add_argument("-card_type", "--card_type", help="card type", type=str, default="general")
    parser.add_argument("-stage", "--stage", help="stage", type=str, default="FETCH_SN")
    parser.add_argument("--skip_test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--skip_slots", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--swm", help="SWM test mode")

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid
    stage = args.stage.upper()
    if not args.skip_test:
        args.skip_test = []

    mtp_cfg_db = load_mtp_cfg(args.mtpcfg)

    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
    fst = 0
    if mtp_capability == 0x4:
        fst = 1
    elif mtp_capability == 0x5:
        fst = 2
    elif mtp_capability == 0x6:
        fst = 3

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, sys.stdout, None, [], skip_slots=args.skip_slots)
    # local logfiles
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=FF_Stage.FF_FST)

    mtp_mgmt_ctrl._fst_ver = mtp_capability
    if mtp_cfg_db.get_mtp_max_slots(mtp_id):
        mtp_mgmt_ctrl._slots = mtp_cfg_db.get_mtp_max_slots(mtp_id)

    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTPS chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg = True):
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTPS chassis", level=0)
        logfile_close(open_file_track_list)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTPS chassis connected", level=0)

    mtp_mgmt_ctrl.cli_log_inf("MTP Final Stage Test Start", level=0)
    start_ts = libmfg_utils.timestamp_snapshot()

    pass_nic_list = list()
    fail_nic_list = list()
    nic_prsnt_list = list()
    test_ROT = False
    s4_family = False

    # load scanned fru
    scanned_fru_cfg = dict()
    if "SCAN_VERIFY" not in args.skip_test and FST_SCAN_ENABLE:
        # load the barcode config file made in toplevel
        scanning.read_scanned_barcodes(mtp_mgmt_ctrl)
        scanned_fru_cfg = mtp_mgmt_ctrl.barcode_scans
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(mtp_mgmt_ctrl._slots):
            key = libmfg_utils.nic_key(slot)
            if not nic_prsnt_list[slot]:
                continue
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)

    try:
        dsp = FF_Stage.FF_FST

        # SETUP & detect NICs
        testlist = ["NIC_INIT"]

        for skip_test in args.skip_test:
            if skip_test in testlist:
                testlist.remove(skip_test)
        for test in testlist:
            start_ts = libmfg_utils.timestamp_snapshot()

            if test == "NIC_INIT":
                ret = mtp_mgmt_ctrl.mtp_nic_init(FF_Stage.FF_FST, scanned_fru=scanned_fru_cfg)
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown FST Test: {:s}, Ignore".format(test))
                continue

            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)

            if not ret:
                mtp_mgmt_ctrl.mtp_diag_fail_report("Test aborted.")
                logfile_close(open_file_track_list)
                return


        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(mtp_mgmt_ctrl._slots):
            if not nic_prsnt_list[slot]:
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot) and slot not in fail_nic_list:
                fail_nic_list.append(slot)
                continue
            pass_nic_list.append(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            # add ROT test to testlist
            if nic_type in ROT_CABLE_REQUIRED_FOR_FST_TYPE_LIST:
                test_ROT = True

        # Pre-post check
        if GLB_CFG_MFG_TEST_MODE and FLEX_SHOP_FLOOR_CONTROL:
            pre_post_fail_list = test_utils.nic_common_setup_test_picker(mtp_mgmt_ctrl, FF_Stage.FF_FST, pass_nic_list + fail_nic_list, ["FF_AREA_CHECK"], args.skip_test)
            for slot in pre_post_fail_list:
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # TESTS
        for slot in range(mtp_mgmt_ctrl._slots):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

            testlist = ["SETUP_SSH", "FETCH_SN", "PCIE_LINK", "SSH_DISABLE"]
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                testlist = ["SETUP_SSH", "FETCH_SN", "SET_BOARD_CONFIG", "PCIE_LINK", "SSH_DISABLE"]
            if nic_type in SALINA_AI_NIC_TYPE_LIST:
                testlist = ["PCIE_LINK", "FETCH_FRU_INFO"]

            if nic_type in (NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICRS4):
                s4_family = True

            for skip_test in args.skip_test:
                if skip_test in testlist:
                    testlist.remove(skip_test)
            for test in testlist:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
                start_ts = libmfg_utils.timestamp_snapshot()
                if test == "FETCH_SN":
                    ret = mtp_mgmt_ctrl.fst_fetch_nic_info(slot, scanned_fru=scanned_fru_cfg)
                elif test == "PCIE_LINK":
                    ret = mtp_mgmt_ctrl.fst_check_nic_pcie(slot)
                elif test == "FETCH_FRU_INFO":
                    ret = mtp_mgmt_ctrl.fst_fetch_salina_info(slot)
                elif test == "SET_BOARD_CONFIG":
                    ret = mtp_mgmt_ctrl.fst_board_config(slot)
                elif test == "SETUP_SSH":
                    ret = mtp_mgmt_ctrl.fst_setup_nic_ssh(slot)
                elif test == "SSH_DISABLE":
                    ret = mtp_mgmt_ctrl.fst_disable_eth_mnic(slot)
                else:
                    mtp_mgmt_ctrl.cli_log_err("Unknown FST Test: {:s}, Ignore".format(test))
                    continue
                stop_ts = libmfg_utils.timestamp_snapshot()
                duration = str(stop_ts - start_ts)
                if not ret:
                    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot) #pull fresh sn after fetch_sn test
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if test != "SSH_DISABLE" and nic_type not in SALINA_NIC_TYPE_LIST:
                        mtp_mgmt_ctrl.fst_disable_eth_mnic(slot)
                    break
                else:
                    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot) #pull fresh sn after fetch_sn test
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))




        # Test ROT if ORTANO
        if test_ROT:
            testlist = ["ROT"]
        else:
            testlist = []

        # build scanned slot id to scanned rot cable serial number mapping table
        slot2rotsn = dict()
        if scanned_fru_cfg:
            for slot in range(mtp_mgmt_ctrl._slots):
                key = libmfg_utils.nic_key(slot)
                if scanned_fru_cfg[key]["VALID"] and bf.ROT_SN in scanned_fru_cfg[key]:
                    slot2rotsn[slot] = scanned_fru_cfg[key][bf.ROT_SN]

        for skip_test in args.skip_test:
            if skip_test in testlist:
                testlist.remove(skip_test)
        for test in testlist:
            start_ts = libmfg_utils.timestamp_snapshot()

            for slot in pass_nic_list:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)

            if test == "ROT":
                test_pass_list, test_fail_list = check_rot(mtp_mgmt_ctrl, pass_nic_list, s4_family)
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown FST Test: {:s}, Ignore".format(test))
                continue

            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)
            for slot in test_pass_list:
                if slot in slot2rotsn:
                    test = "ROT WITH ROT CABLE " + slot2rotsn[slot]
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

                # update global result list also.
                if slot not in pass_nic_list and slot not in fail_nic_list:
                    pass_nic_list.append(slot)

            for slot in test_fail_list:
                if slot in slot2rotsn:
                    test = "ROT WITH ROT CABLE " + slot2rotsn[slot]
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))

                # update global result list also.
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                    fail_nic_list.append(slot)

                if slot not in pass_nic_list and slot not in fail_nic_list:
                    fail_nic_list.append(slot)

    except Exception as e:
        # err_msg = str(e)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)
        # fail all slots
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not nic_prsnt_list[slot]:
                continue
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)

    for slot in pass_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

    for slot in fail_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        mtp_mgmt_ctrl.cli_log_err("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    logfile_close(open_file_track_list)
    return

if __name__ == "__main__":
    main()

