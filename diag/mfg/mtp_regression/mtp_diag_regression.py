#!/usr/bin/env python

import sys
import os
import time
import pexpect
import re
import argparse
import random
import datetime
import threading

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import MTP_Const
from libdefs import NIC_Type
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import Env_Cond
from libdefs import MFG_DIAG_CMDS
from libdiag_db import diag_db
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE


# test cleanup.
def mtp_test_cleanup(error_code, fp_list=None):
    if fp_list:
        for fp in fp_list:
            fp.close()
    os.system("sync")


def naples_diag_cfg_show(card_type, naples_test_db, mtp_mgmt_ctrl):
    mtp_mgmt_ctrl.cli_log_inf("{:s} Diag Regression Test List:".format(card_type), level = 0)
    cmd_list = naples_test_db.get_init_cmd_list()
    mtp_mgmt_ctrl.cli_log_inf("Init Command List:")
    for item in cmd_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)

    skip_list = naples_test_db.get_skip_test_list()
    mtp_mgmt_ctrl.cli_log_inf("Skip Test List:")
    for item in skip_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)

    param_list = naples_test_db.get_test_param_list()
    mtp_mgmt_ctrl.cli_log_inf("Parameter List:")
    for item in param_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)

    pre_test_check_list = naples_test_db.get_pre_diag_test_intf_list()
    mtp_mgmt_ctrl.cli_log_inf("Pre Diag Test Check List:")
    for item in pre_test_check_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)

    post_test_check_list = naples_test_db.get_post_diag_test_intf_list()
    mtp_mgmt_ctrl.cli_log_inf("Post Diag Test Check List:")
    for item in post_test_check_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)

    mtp_para_test_list = naples_test_db.get_mtp_para_test_list()
    mtp_mgmt_ctrl.cli_log_inf("MTP Parallel Test List:")
    for item in mtp_para_test_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)

    seq_test_list = naples_test_db.get_diag_seq_test_list()
    mtp_mgmt_ctrl.cli_log_inf("MTP Sequential Test List:")
    for item in seq_test_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)

    para_test_list = naples_test_db.get_diag_para_test_list()
    mtp_mgmt_ctrl.cli_log_inf("NIC Parallel Test List:")
    for item in para_test_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)
    mtp_mgmt_ctrl.cli_log_inf("{:s} Diag Regression Test List End\n".format(card_type), level = 0)

    return


def naples_exec_init_cmd(naples_test_db, mtp_mgmt_ctrl):
    cmd_list = naples_test_db.get_init_cmd_list()
    mtp_mgmt_ctrl.cli_log_inf("Execute Command in Init Command List:", level = 0)
    for cmd in cmd_list:
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    return


def naples_exec_skip_cmd(nic_list, naples_test_db, mtp_mgmt_ctrl):
    cmd_list = naples_test_db.get_skip_test_cmd_list(nic_list)
    mtp_mgmt_ctrl.cli_log_inf("Execute Command in Skip Command List:", level = 0)
    for cmd in cmd_list:
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    return


def naples_exec_param_cmd(nic_list, naples_test_db, mtp_mgmt_ctrl):
    cmd_list = naples_test_db.get_test_param_cmd_list()
    mtp_mgmt_ctrl.cli_log_inf("Set Diag Test Parameters:", level = 0)
    for cmd in cmd_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(cmd))
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    mtp_mgmt_ctrl.cli_log_inf("Set Diag Test Parameters complete\n", level = 0)

    return


def naples_exec_pre_check(mtp_mgmt_ctrl, nic_type, nic_list, nic_check_list, vmarg):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Pre Check Start".format(nic_type), level=0)
    fail_list = list()
    if vmarg > 0:
        dsp = "HV_PRE_CHECK"
    elif vmarg < 0:
        dsp = "LV_PRE_CHECK"
    else:
        dsp = "PRE_CHECK"

    for intf in nic_check_list:
        for slot in nic_list:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, intf), level=0)
            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret = mtp_mgmt_ctrl.mtp_mgmt_pre_post_diag_check(intf, slot)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)
            if ret == "SUCCESS":
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, intf, duration), level=0)
            else:
                fail_list.append(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, intf, ret, duration), level=0)
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Pre Check Complete\n".format(nic_type), level=0)

    return fail_list


def naples_exec_mtp_para_test(mtp_mgmt_ctrl, nic_type, nic_list, para_test_list, vmarg, stop_on_err):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Start".format(nic_type), level=0)
    fail_list = list()
    nic_test_list = nic_list[:]
    fail_slot_sn_test_list = list()

    if vmarg > 0:
        dsp = "HV_CAPRI"
    elif vmarg < 0:
        dsp = "LV_CAPRI"
    else:
        dsp = "CAPRI"

    for test in para_test_list:
        # track nic without report
        nic_no_rslt_list = nic_test_list[:]
        for slot in nic_test_list[:]:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)

        start_ts = datetime.datetime.now().replace(microsecond=0)
        test_rslt_list = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(test, nic_test_list[:], vmarg)
        stop_ts = datetime.datetime.now().replace(microsecond=0)
        duration = str(stop_ts - start_ts)

        if not test_rslt_list:
            mtp_mgmt_ctrl.cli_log_err("MTP {:s} Diag Regression MTP Parallel Test failed\n".format(nic_type), level=0)
        else:
            for _slot, rslt in test_rslt_list:
                slot = int(_slot) - 1
                nic_no_rslt_list.remove(slot)
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                if rslt == "PASS":
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)
                else:
                    fail_slot_sn_test_list.append((slot, sn, test))
                    if stop_on_err:
                        nic_test_list.remove(slot)
                    if slot not in fail_list:
                        fail_list.append(slot)
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, rslt, duration), level=0)
                    mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)

        # all the slot without report, treat as fail
        if nic_no_rslt_list:
            for slot in nic_no_rslt_list:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                fail_slot_sn_test_list.append((slot, sn, test))
                if stop_on_err:
                    nic_test_list.remove(slot)
                if slot not in fail_list:
                    fail_list.append(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "TIMEOUT", duration), level=0)
                mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)

    # collect logfile
    naples_get_mtp_para_logfile(mtp_mgmt_ctrl, nic_list, para_test_list)

    # extract error message if test fail
    if fail_slot_sn_test_list:
        for slot, sn, test in fail_slot_sn_test_list:
            err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_mtp_para_err(sn, test)
            if err_msg_list:
                for err_msg in err_msg_list:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp, test, err_msg), level=0)

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Complete\n".format(nic_type), level=0)

    return fail_list


def naples_diag_para_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, test_list, stop_on_err, vmarg):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel Test Start".format(nic_type), level=0)
    fail_list = list()

    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    for slot in nic_list:
        nic_thread = threading.Thread(target = single_nic_diag_regression,
                                      args = (mtp_mgmt_ctrl,
                                              slot,
                                              test_db,
                                              test_list,
                                              nic_test_rslt_list,
                                              stop_on_err,
                                              vmarg))
        nic_thread.daemon = True
        nic_thread.start()
        nic_thread_list.append(nic_thread)

    while True:
        if len(nic_thread_list) == 0:
            break
        for nic_thread in nic_thread_list[:]:
            if not nic_thread.is_alive():
                ret = nic_thread.join()
                nic_thread_list.remove(nic_thread)
        time.sleep(5)

    for slot in nic_list:
        if not nic_test_rslt_list[slot]:
            fail_list.append(slot)

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel Test Complete\n".format(nic_type), level=0)
    return fail_list


def naples_diag_seq_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, test_list, vmarg, stop_on_err):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Sequential Test Start".format(nic_type), level=0)
    fail_list = list()

    for dsp, test in test_list:
        if vmarg > 0:
            dsp_disp = "HV_" + dsp
        elif vmarg < 0:
            dsp_disp = "LV_" + dsp
        else:
            dsp_disp = dsp

        test_cfg = test_db.get_diag_seq_test(dsp, test)
        init_cmd = None
        post_cmd = None
        if test_cfg["INIT"] != "":
            init_cmd = test_cfg["INIT"]
        if test_cfg["POST"] != "":
            post_cmd = test_cfg["POST"]
        for slot in nic_list[:]:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            opts = test_cfg["OPTS"]
            diag_cmd = test_db.get_diag_seq_test_run_cmd(dsp, test, slot, opts, sn, vmarg)
            rslt_cmd = test_db.get_diag_seq_test_errcode_cmd(dsp, slot, opts)
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test), level=0)

            start_ts = datetime.datetime.now().replace(microsecond=0)
            ret, err_msg_list = mtp_mgmt_ctrl.mtp_run_diag_test_seq(slot, diag_cmd, rslt_cmd, test, init_cmd, post_cmd)
            stop_ts = datetime.datetime.now().replace(microsecond=0)
            duration = str(stop_ts - start_ts)

            if ret == "SUCCESS":
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp_disp, test, duration), level=0)
            elif ret == MTP_DIAG_Error.NIC_DIAG_TIMEOUT:
                if stop_on_err:
                    nic_list.remove(slot)
                fail_list.append(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_TIMEOUT.format(sn, dsp_disp, test, duration), level=0)
                if dsp == "ASIC" and test == "L1":
                    mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
            else:
                if stop_on_err:
                    nic_list.remove(slot)
                fail_list.append(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, test, ret, duration), level=0)
                if dsp == "ASIC" and test == "L1":
                    mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
                    err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_nic_l1_err(sn)
                    for err_msg in err_msg_list:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, test, err_msg), level=0)
                else:
                    for err_msg in err_msg_list:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, test, err_msg), level=0)

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Sequential Test Complete\n".format(nic_type), level=0)

    return fail_list


def naples_get_mtp_para_logfile(mtp_mgmt_ctrl, nic_list, mtp_para_test_list):
    mtp_mgmt_ctrl.cli_log_inf("Collecting NIC logfile for MTP Parallel tests", level=0)

    # power cycle all the NICs
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Init NIC Diag Environment failed\n", level=0)
        return False

    for slot in nic_list:
        logfile_list = list()
        if "SNAKE_HBM" in mtp_para_test_list:
            logfile_list.append("snake_hbm.log")
        if "SNAKE_PCIE" in mtp_para_test_list:
            logfile_list.append("snake_pcie.log")
        if "PRBS_ETH" in mtp_para_test_list:
            logfile_list.append("prbs_eth.log")
        if "PRBS_PCIE" in mtp_para_test_list:
            logfile_list.append("prbs_pcie.log")

        if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_logfile(slot, logfile_list):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Collecting NIC logfile for MTP Parallel tests failed\n")
            continue

    mtp_mgmt_ctrl.cli_log_inf("Collecting NIC logfile for MTP Parallel tests complete\n", level=0)


def single_nic_diag_regression(mtp_mgmt_ctrl, slot, diag_test_db, diag_para_test_list, nic_test_rslt_list, stop_on_err, vmarg):
    for dsp, test in diag_para_test_list:
        if vmarg > 0:
            dsp_disp = "HV_" + dsp
        elif vmarg < 0:
            dsp_disp = "LV_" + dsp
        else:
            dsp_disp = dsp

        test_cfg = diag_test_db.get_diag_para_test(dsp, test)
        init_cmd = None
        post_cmd = None
        if test_cfg["INIT"] != "":
            init_cmd = test_cfg["INIT"]
        if test_cfg["POST"] != "":
            post_cmd = test_cfg["POST"]
        opts = test_cfg["OPTS"]
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        diag_cmd = diag_test_db.get_diag_para_test_run_cmd(dsp, test, slot, opts, sn)
        rslt_cmd = diag_test_db.get_diag_para_test_errcode_cmd(dsp, slot, opts)
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test), level=0)

        start_ts = datetime.datetime.now().replace(microsecond=0)
        ret, err_msg_list = mtp_mgmt_ctrl.mtp_run_diag_test_para(slot, diag_cmd, rslt_cmd, test, init_cmd, post_cmd)
        stop_ts = datetime.datetime.now().replace(microsecond=0)
        duration = str(stop_ts - start_ts)

        if ret == "SUCCESS":
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp_disp, test, duration), level=0)
        elif ret == MTP_DIAG_Error.NIC_DIAG_TIMEOUT:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_TIMEOUT.format(sn, dsp_disp, test, duration), level=0)
            nic_test_rslt_list[slot] = False
            if stop_on_err:
                return
        else:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, test, ret, duration), level=0)
            for err_msg in err_msg_list:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, test, err_msg), level=0)
            nic_test_rslt_list[slot] = False
            if stop_on_err:
                return


def main():
    parser = argparse.ArgumentParser(description="Single MTP Diagnostics P2C Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--stop-on-error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--corner", type=Env_Cond, help="diagnostic environment condition", choices=list(Env_Cond), default=Env_Cond.MFG_NT)

    args = parser.parse_args()

    mtp_id = "MTP-000"
    stop_on_err = False
    verbosity = False
    skip_test = False
    corner = Env_Cond.MFG_NT

    if args.mtpid:
        mtp_id = args.mtpid
        mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    if args.stop_on_error:
        stop_on_err = True
    if args.verbosity:
        verbosity = True
    if args.corner:
        corner = args.corner

    # Normal temperature, no voltage corner
    if corner == Env_Cond.MFG_NT:
        fanspd = MTP_Const.MFG_EDVT_NORM_FAN_SPD
        low_temp_threshold = None
        high_temp_threshold = None
        vmarg_list = [0]
    # Low temperature, two voltage corner
    elif corner == Env_Cond.MFG_LT:
        if GLB_CFG_MFG_TEST_MODE:
            fanspd = MTP_Const.MFG_EDVT_LOW_FAN_SPD
            low_temp_threshold = MTP_Const.MFG_EDVT_LOW_TEMP
        else:
            fanspd = MTP_Const.MFG_MODEL_EDVT_LOW_FAN_SPD
            low_temp_threshold = MTP_Const.MFG_MODEL_EDVT_LOW_TEMP
        high_temp_threshold = None
        vmarg_list = [MTP_Const.MFG_EDVT_HIGH_VOLT, MTP_Const.MFG_EDVT_LOW_VOLT]
    # High temperature, two voltage corner
    elif corner == Env_Cond.MFG_HT:
        if GLB_CFG_MFG_TEST_MODE:
            fanspd = MTP_Const.MFG_EDVT_HIGH_FAN_SPD
            high_temp_threshold = MTP_Const.MFG_EDVT_HIGH_TEMP
        else:
            fanspd = MTP_Const.MFG_MODEL_EDVT_HIGH_FAN_SPD
            high_temp_threshold = MTP_Const.MFG_MODEL_EDVT_HIGH_TEMP
        low_temp_threshold = None
        vmarg_list = [MTP_Const.MFG_EDVT_HIGH_VOLT, MTP_Const.MFG_EDVT_LOW_VOLT]
    # RDT runs @high temperature, no voltage corner
    elif corner == Env_Cond.MFG_RDT:
        fanspd = MTP_Const.MFG_EDVT_HIGH_FAN_SPD
        high_temp_threshold = MTP_Const.MFG_EDVT_HIGH_TEMP
        low_temp_threshold = None
        vmarg_list = [0]
    # EDVT, high temperature, two voltage corner
    elif corner == Env_Cond.MFG_EDVT_HT:
        fanspd = MTP_Const.MFG_EDVT_HIGH_FAN_SPD
        high_temp_threshold = MTP_Const.MFG_EDVT_HIGH_TEMP
        low_temp_threshold = None
        vmarg_list = [MTP_Const.MFG_EDVT_HIGH_VOLT, MTP_Const.MFG_EDVT_LOW_VOLT]
    # EDVT, low temperature, two voltage corner
    elif corner == Env_Cond.MFG_EDVT_LT:
        fanspd = MTP_Const.MFG_EDVT_LOW_FAN_SPD
        low_temp_threshold = MTP_Const.MFG_EDVT_LOW_TEMP
        high_temp_threshold = None
        vmarg_list = [MTP_Const.MFG_EDVT_HIGH_VOLT, MTP_Const.MFG_EDVT_LOW_VOLT]
    else:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")

    # load the mtp config
    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)

    # find the mtp management config based on the mtpid
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")

    # find the apc config based on the mtpid
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    # load the diag test config
    naples100_test_cfg_file = "config/naples100_mtp_test_cfg.yaml"
    naples25_test_cfg_file = "config/naples25_mtp_test_cfg.yaml"
    forio_test_cfg_file = "config/forio_mtp_test_cfg.yaml"
    vomero_test_cfg_file = "config/vomero_mtp_test_cfg.yaml"
    naples100_test_db = diag_db(corner, naples100_test_cfg_file)
    naples25_test_db = diag_db(corner, naples25_test_cfg_file)
    forio_test_db = diag_db(corner, forio_test_cfg_file)
    vomero_test_db = diag_db(corner, vomero_test_cfg_file)

    # logfiles
    open_file_track_list = list()

    mtp_script_dir = os.getcwd()
    mtp_test_log_file = mtp_script_dir + "/mtp_test.log"
    mtp_diag_log_file = mtp_script_dir + "/mtp_diag.log"
    mtp_diag_cmd_log_file = mtp_script_dir + "/mtp_diag_cmd.log"
    mtp_diagmgr_log_file = mtp_script_dir + "/mtp_diagmgr.log"
    mtp_test_log_filep = open(mtp_test_log_file, "w+", buffering=0)
    open_file_track_list.append(mtp_test_log_filep)
    mtp_diag_log_filep = open(mtp_diag_log_file, "w+", buffering=0)
    open_file_track_list.append(mtp_diag_log_filep)
    mtp_diag_cmd_log_filep = open(mtp_diag_cmd_log_file, "w+", buffering=0)
    open_file_track_list.append(mtp_diag_cmd_log_filep)
    mtp_diagmgr_log_filep = open(mtp_diagmgr_log_file, "w+", buffering=0)

    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        nic_key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = mtp_script_dir + "/mtp_{:s}_diag.log".format(nic_key)
        diag_nic_log_filep = open(diag_nic_log_file, "w+")
        open_file_track_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id,
                             mtp_test_log_filep,
                             mtp_diag_log_filep,
                             diag_nic_log_filep_list,
                             diag_cmd_log_filep = mtp_diag_cmd_log_filep,
                             mgmt_cfg = mtp_mgmt_cfg,
                             apc_cfg = mtp_apc_cfg,
                             dbg_mode = verbosity)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.mtp_diag_fail_report("Unable to connect MTP Chassis")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
        return

    if not mtp_mgmt_ctrl.mtp_diag_pre_init(mtp_diagmgr_log_file):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP Diag Environment Pre init failed")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_HW_SANITY, open_file_track_list)
        return

    if not mtp_mgmt_ctrl.mtp_diag_post_init(mtp_capability):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP Diag Environment Post init Fail")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
        return

    if not mtp_mgmt_ctrl.mtp_sys_info_disp():
        mtp_mgmt_ctrl.mtp_diag_fail_report("Unable to retrieve MTP system info")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
        return

    # PSU/FAN absent, powerdown MTP
    ret = mtp_mgmt_ctrl.mtp_hw_init(fanspd)
    if not ret:
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP Sanity Check Failed")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_HW_SANITY, open_file_track_list)
        return

    # Wait the Chamber temperature, if HT or LT is set
    mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Ambient Temperature Check", level=0)
    # RDT/EDVT, don't wait soaking time
    if corner == Env_Cond.MFG_RDT or corner == Env_Cond.MFG_EDVT_HT or corner == Env_Cond.MFG_EDVT_LT:
        rdy = mtp_mgmt_ctrl.mtp_wait_temp_ready(None, None)
    else:
        rdy = mtp_mgmt_ctrl.mtp_wait_temp_ready(low_temp_threshold, high_temp_threshold)
    if not rdy:
        mtp_mgmt_ctrl.mtp_diag_fail_report("Diag Regression Test Ambient Temperature Check Failed")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_ENV_SETUP, open_file_track_list)
        return
    mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Ambient Temperature Check Complete\n", level=0)

    naples100_nic_list = list()
    naples25_nic_list = list()
    forio_nic_list = list()
    vomero_nic_list = list()
    pass_nic_list = list()
    fail_nic_list = list()

    if not mtp_mgmt_ctrl.mtp_nic_init():
        mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC type, present failed")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
        return

    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

    for slot in range(len(nic_prsnt_list)):
        if nic_prsnt_list[slot]:
            if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES100:
                naples100_nic_list.append(slot)
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25:
                naples25_nic_list.append(slot)
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.FORIO:
                forio_nic_list.append(slot)
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.VOMERO:
                vomero_nic_list.append(slot)
                pass_nic_list.append(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC Type", level=0)

    if naples100_nic_list:
        if not mtp_capability & 0x1:
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP <{:x}> doesn't support Naples100".format(mtp_capability))
            mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
            return
        naples_diag_cfg_show(NIC_Type.NAPLES100, naples100_test_db, mtp_mgmt_ctrl)
        naples_exec_init_cmd(naples100_test_db, mtp_mgmt_ctrl)
        naples_exec_skip_cmd(naples100_nic_list, naples100_test_db, mtp_mgmt_ctrl)
        naples_exec_param_cmd(naples100_nic_list, naples100_test_db, mtp_mgmt_ctrl)
    if naples25_nic_list:
        if not mtp_capability & 0x2:
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP <{:x}> doesn't support Naples25".format(mtp_capability))
            mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
            return
        naples_diag_cfg_show(NIC_Type.NAPLES25, naples25_test_db, mtp_mgmt_ctrl)
        naples_exec_init_cmd(naples25_test_db, mtp_mgmt_ctrl)
        naples_exec_skip_cmd(naples25_nic_list, naples25_test_db, mtp_mgmt_ctrl)
        naples_exec_param_cmd(naples25_nic_list, naples25_test_db, mtp_mgmt_ctrl)
    if forio_nic_list:
        if not mtp_capability & 0x1:
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP <{:x}> doesn't support Forio".format(mtp_capability))
            mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
            return
        naples_diag_cfg_show(NIC_Type.FORIO, forio_test_db, mtp_mgmt_ctrl)
        naples_exec_init_cmd(forio_test_db, mtp_mgmt_ctrl)
        naples_exec_skip_cmd(forio_nic_list, forio_test_db, mtp_mgmt_ctrl)
        naples_exec_param_cmd(forio_nic_list, forio_test_db, mtp_mgmt_ctrl)
    if vomero_nic_list:
        if not mtp_capability & 0x1:
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP <{:x}> doesn't support Vomero".format(mtp_capability))
            mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
            return
        naples_diag_cfg_show(NIC_Type.VOMERO, vomero_test_db, mtp_mgmt_ctrl)
        naples_exec_init_cmd(vomero_test_db, mtp_mgmt_ctrl)
        naples_exec_skip_cmd(vomero_nic_list, vomero_test_db, mtp_mgmt_ctrl)
        naples_exec_param_cmd(vomero_nic_list, vomero_test_db, mtp_mgmt_ctrl)

    naples100_seq_test_list = naples100_test_db.get_diag_seq_test_list()
    naples100_mtp_para_test_list = naples100_test_db.get_mtp_para_test_list()
    naples100_para_test_list = naples100_test_db.get_diag_para_test_list()
    naples100_pre_test_check_list = naples100_test_db.get_pre_diag_test_intf_list()
    naples100_post_test_check_list = naples100_test_db.get_post_diag_test_intf_list()

    naples25_seq_test_list = naples25_test_db.get_diag_seq_test_list()
    naples25_mtp_para_test_list = naples25_test_db.get_mtp_para_test_list()
    naples25_para_test_list = naples25_test_db.get_diag_para_test_list()
    naples25_pre_test_check_list = naples25_test_db.get_pre_diag_test_intf_list()
    naples25_post_test_check_list = naples25_test_db.get_post_diag_test_intf_list()

    forio_seq_test_list = forio_test_db.get_diag_seq_test_list()
    forio_mtp_para_test_list = forio_test_db.get_mtp_para_test_list()
    forio_para_test_list = forio_test_db.get_diag_para_test_list()
    forio_pre_test_check_list = forio_test_db.get_pre_diag_test_intf_list()
    forio_post_test_check_list = forio_test_db.get_post_diag_test_intf_list()

    vomero_seq_test_list = vomero_test_db.get_diag_seq_test_list()
    vomero_mtp_para_test_list = vomero_test_db.get_mtp_para_test_list()
    vomero_para_test_list = vomero_test_db.get_diag_para_test_list()
    vomero_pre_test_check_list = vomero_test_db.get_pre_diag_test_intf_list()
    vomero_post_test_check_list = vomero_test_db.get_post_diag_test_intf_list()

    mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Test Start", level=0)
    for vmarg in vmarg_list:
        inlet = mtp_mgmt_ctrl.mtp_get_inlet_temp(low_temp_threshold, high_temp_threshold)
        mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment:", level=0)
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Fan Speed = {:3d}%".format(fanspd))
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(inlet))
        mtp_mgmt_ctrl.cli_log_report_inf("NIC Voltage Margin = {:d}%".format(vmarg))
        mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment End\n", level=0)

        # power cycle all the NIC
        mtp_mgmt_ctrl.mtp_power_cycle_nic()

        if not mtp_mgmt_ctrl.mtp_nic_diag_init(vmargin=vmarg):
            mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
            mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
            return

        # Naples100 Diag Pre Check
        if naples100_nic_list:
            pre_check_fail_list = naples_exec_pre_check(mtp_mgmt_ctrl,
                                                        NIC_Type.NAPLES100,
                                                        naples100_nic_list,
                                                        naples100_pre_test_check_list,
                                                        vmarg)
            for slot in pre_check_fail_list:
                if slot in naples100_nic_list:
                    naples100_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Naples25 Diag Pre Check
        if naples25_nic_list:
            pre_check_fail_list = naples_exec_pre_check(mtp_mgmt_ctrl,
                                                        NIC_Type.NAPLES25,
                                                        naples25_nic_list,
                                                        naples25_pre_test_check_list,
                                                        vmarg)
            for slot in pre_check_fail_list:
                if slot in naples25_nic_list:
                    naples25_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Forio Diag Pre Check
        if forio_nic_list:
            pre_check_fail_list = naples_exec_pre_check(mtp_mgmt_ctrl,
                                                        NIC_Type.FORIO,
                                                        forio_nic_list,
                                                        forio_pre_test_check_list,
                                                        vmarg)
            for slot in pre_check_fail_list:
                if slot in forio_nic_list:
                    forio_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Vomero Diag Pre Check
        if vomero_nic_list:
            pre_check_fail_list = naples_exec_pre_check(mtp_mgmt_ctrl,
                                                        NIC_Type.VOMERO,
                                                        vomero_nic_list,
                                                        vomero_pre_test_check_list,
                                                        vmarg)
            for slot in pre_check_fail_list:
                if slot in vomero_nic_list:
                    vomero_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)


        # Naples100 Parallel test
        if naples100_nic_list:
            diag_para_fail_list = naples_diag_para_test(mtp_mgmt_ctrl,
                                                        NIC_Type.NAPLES100,
                                                        naples100_nic_list,
                                                        naples100_test_db,
                                                        naples100_para_test_list,
                                                        stop_on_err,
                                                        vmarg)
            for slot in diag_para_fail_list:
                if slot in naples100_nic_list and stop_on_err:
                    naples100_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Naples25 Parallel test
        if naples25_nic_list:
            diag_para_fail_list = naples_diag_para_test(mtp_mgmt_ctrl,
                                                        NIC_Type.NAPLES25,
                                                        naples25_nic_list,
                                                        naples25_test_db,
                                                        naples25_para_test_list,
                                                        stop_on_err,
                                                        vmarg)
            for slot in diag_para_fail_list:
                if slot in naples25_nic_list and stop_on_err:
                    naples25_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Forio Parallel test
        if forio_nic_list:
            diag_para_fail_list = naples_diag_para_test(mtp_mgmt_ctrl,
                                                        NIC_Type.FORIO,
                                                        forio_nic_list,
                                                        forio_test_db,
                                                        forio_para_test_list,
                                                        stop_on_err,
                                                        vmarg)
            for slot in diag_para_fail_list:
                if slot in forio_nic_list and stop_on_err:
                    forio_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Vomero Parallel test
        if vomero_nic_list:
            diag_para_fail_list = naples_diag_para_test(mtp_mgmt_ctrl,
                                                        NIC_Type.VOMERO,
                                                        vomero_nic_list,
                                                        vomero_test_db,
                                                        vomero_para_test_list,
                                                        stop_on_err,
                                                        vmarg)
            for slot in diag_para_fail_list:
                if slot in vomero_nic_list and stop_on_err:
                    vomero_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Naples100 Sequential test
        if naples100_nic_list:
            diag_seq_fail_list = naples_diag_seq_test(mtp_mgmt_ctrl,
                                                      NIC_Type.NAPLES100,
                                                      naples100_nic_list,
                                                      naples100_test_db,
                                                      naples100_seq_test_list,
                                                      vmarg,
                                                      stop_on_err)
            for slot in diag_seq_fail_list:
                if slot in naples100_nic_list and stop_on_err:
                    naples100_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Naples25 Sequential test
        if naples25_nic_list:
            diag_seq_fail_list = naples_diag_seq_test(mtp_mgmt_ctrl,
                                                      NIC_Type.NAPLES25,
                                                      naples25_nic_list,
                                                      naples25_test_db,
                                                      naples25_seq_test_list,
                                                      vmarg,
                                                      stop_on_err)
            for slot in diag_seq_fail_list:
                if slot in naples25_nic_list and stop_on_err:
                    naples25_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Forio Sequential test
        if forio_nic_list:
            diag_seq_fail_list = naples_diag_seq_test(mtp_mgmt_ctrl,
                                                      NIC_Type.FORIO,
                                                      forio_nic_list,
                                                      forio_test_db,
                                                      forio_seq_test_list,
                                                      vmarg,
                                                      stop_on_err)
            for slot in diag_seq_fail_list:
                if slot in forio_nic_list and stop_on_err:
                    forio_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # Vomero Sequential test
        if vomero_nic_list:
            diag_seq_fail_list = naples_diag_seq_test(mtp_mgmt_ctrl,
                                                      NIC_Type.VOMERO,
                                                      vomero_nic_list,
                                                      vomero_test_db,
                                                      vomero_seq_test_list,
                                                      vmarg,
                                                      stop_on_err)
            for slot in diag_seq_fail_list:
                if slot in vomero_nic_list and stop_on_err:
                    vomero_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)


        # log the diag test history
        mtp_mgmt_ctrl.mtp_mgmt_diag_history_disp()

        # clear the diag test history
        if not stop_on_err:
            mtp_mgmt_ctrl.mtp_mgmt_diag_history_clear()

        # # Naples100 MTP Parallel test
        # if naples100_nic_list:
        #     mtp_para_fail_list = naples_exec_mtp_para_test(mtp_mgmt_ctrl,
        #                                                    NIC_Type.NAPLES100,
        #                                                    naples100_nic_list,
        #                                                    naples100_mtp_para_test_list,
        #                                                    vmarg,
        #                                                    stop_on_err)
        #     for slot in mtp_para_fail_list:
        #         if slot in naples100_nic_list and stop_on_err:
        #             naples100_nic_list.remove(slot)
        #         if slot not in fail_nic_list:
        #             fail_nic_list.append(slot)
        #         if slot in pass_nic_list:
        #             pass_nic_list.remove(slot)

        # # Naples25 MTP Parallel test
        # if naples25_nic_list:
        #     mtp_para_fail_list = naples_exec_mtp_para_test(mtp_mgmt_ctrl,
        #                                                    NIC_Type.NAPLES25,
        #                                                    naples25_nic_list,
        #                                                    naples25_mtp_para_test_list,
        #                                                    vmarg,
        #                                                    stop_on_err)
        #     for slot in mtp_para_fail_list:
        #         if slot in naples25_nic_list and stop_on_err:
        #             naples25_nic_list.remove(slot)
        #         if slot not in fail_nic_list:
        #             fail_nic_list.append(slot)
        #         if slot in pass_nic_list:
        #             pass_nic_list.remove(slot)

        # # Forio MTP Parallel test
        # if forio_nic_list:
        #     mtp_para_fail_list = naples_exec_mtp_para_test(mtp_mgmt_ctrl,
        #                                                    NIC_Type.FORIO,
        #                                                    forio_nic_list,
        #                                                    forio_mtp_para_test_list,
        #                                                    vmarg,
        #                                                    stop_on_err)
        #     for slot in mtp_para_fail_list:
        #         if slot in forio_nic_list and stop_on_err:
        #             forio_nic_list.remove(slot)
        #         if slot not in fail_nic_list:
        #             fail_nic_list.append(slot)
        #         if slot in pass_nic_list:
        #             pass_nic_list.remove(slot)

        # # Vomero MTP Parallel test
        # if vomero_nic_list:
        #     mtp_para_fail_list = naples_exec_mtp_para_test(mtp_mgmt_ctrl,
        #                                                    NIC_Type.VOMERO,
        #                                                    vomero_nic_list,
        #                                                    vomero_mtp_para_test_list,
        #                                                    vmarg,
        #                                                    stop_on_err)
        #     for slot in mtp_para_fail_list:
        #         if slot in vomero_nic_list and stop_on_err:
        #             vomero_nic_list.remove(slot)
        #         if slot not in fail_nic_list:
        #             fail_nic_list.append(slot)
        #         if slot in pass_nic_list:
        #             pass_nic_list.remove(slot)

        if vmarg == MTP_Const.MFG_EDVT_LOW_VOLT:
            diag_sub_dir = "/lv_diag_logs/"
            asic_sub_dir = "/lv_asic_logs/"
        elif vmarg == MTP_Const.MFG_EDVT_HIGH_VOLT:
            diag_sub_dir = "/hv_diag_logs/"
            asic_sub_dir = "/hv_asic_logs/"
        else:
            diag_sub_dir = "/diag_logs/"
            asic_sub_dir = "/asic_logs/"
        # create log dir
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + diag_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        # save the asic/diag log files
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_DIAG_LOG_FILES, mtp_script_dir + diag_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, mtp_script_dir + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        # clean up logfiles for the next run
        cmd = "cleanup.sh"
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Test Complete\n", level=0)

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

    mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_PASS, open_file_track_list)


if __name__ == "__main__":
    main()
