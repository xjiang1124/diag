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
from libdefs import MTP_ASIC_SUPPORT
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import Env_Cond
from libdefs import Swm_Test_Mode
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

    if card_type == NIC_Type.ORTANO2:
        para_test_list = [("MVL", "ACC"), ("MVL", "STUB")]
        mtp_mgmt_ctrl.cli_log_inf("NIC Parallel Additional Test List:")
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

def get_mode_param(mtp_mgmt_ctrl, slot, test):
    """
    For NIC_ASIC L1 test parameter.
    """
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.ORTANO2 and test == "L1":
        if mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
            mode = "hod"
        else:
            mode = "hod_1100"
    else:
        mode = ""

    return mode

def naples_exec_pre_check(mtp_mgmt_ctrl, nic_type, nic_list, nic_check_list, vmarg, swmtestmode):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Pre Check Start".format(nic_type), level=0)
    nic_test_list = nic_list[:]
    fail_list = list()
    if vmarg > 0:
        dsp = "HV_PRE_CHECK"
    elif vmarg < 0:
        dsp = "LV_PRE_CHECK"
    else:
        dsp = "PRE_CHECK"

    for intf in nic_check_list:
        for slot in nic_test_list[:]:

            if (nic_type == NIC_Type.NAPLES25SWM) and (mtp_mgmt_ctrl.mtp_get_swmtestmode(slot) == Swm_Test_Mode.SWM) and (intf == "NIC_ALOM_CABLE"):
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, intf))
            start_ts = libmfg_utils.timestamp_snapshot()
            ret = mtp_mgmt_ctrl.mtp_mgmt_pre_post_diag_check(intf, slot, vmarg)
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)
            if ret == "SUCCESS":
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, intf, duration))
            else:
                fail_list.append(slot)
                nic_test_list.remove(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, intf, ret, duration))
                mtp_mgmt_ctrl.mtp_mgmt_nic_diag_sys_clean(slot)
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, intf, ret, duration))
                    mtp_mgmt_ctrl.mtp_mgmt_nic_diag_sys_clean(slot)
            
    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Pre Check Complete\n".format(nic_type), level=0)

    return fail_list


def naples_exec_mtp_para_test(mtp_mgmt_ctrl, nic_type, nic_list, para_test_list, vmarg, stop_on_err, swmtestmode):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Start".format(nic_type), level=0)
    fail_list = list()
    nic_top_test_list = list()
    nic_bottom_test_list = list()

    if vmarg > 0:
        dsp = "HV_ASIC"
    elif vmarg < 0:
        dsp = "LV_ASIC"
    else:
        dsp = "ASIC"

    # separate lists for ORC ortano and PEN ortano 
    if nic_type == NIC_Type.ORTANO2:
        orc_list, pen_list = [], []
        for slot in nic_list:
            if mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
                orc_list.append(slot)
            else:
                pen_list.append(slot)
        nic_top_test_list = orc_list[:]
        nic_bot_test_list = pen_list[:]

    if len(nic_top_test_list) == 0:
        nic_top_test_list = nic_list[:]
        nic_bot_test_list = []

    for nic_test_list in nic_top_test_list, nic_bot_test_list:
        if not nic_test_list:
            continue
        fail_slot_test_list = list()
        for test in para_test_list:
            for slot in nic_test_list[:]:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))

            start_ts = libmfg_utils.timestamp_snapshot()
            test_fail_list = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(test, nic_test_list, vmarg)
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)

            # failed nic display
            for slot in test_fail_list:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                mtp_mgmt_ctrl.mtp_mgmt_nic_diag_sys_clean(slot)
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
                mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
                mtp_mgmt_ctrl.mtp_mgmt_nic_diag_sys_clean(slot)
                if stop_on_err:
                    nic_test_list.remove(slot)
                if slot not in fail_list:
                    fail_list.append(slot)
                fail_slot_test_list.append((slot, test))

            # passed nic display
            for slot in nic_test_list:
                if slot not in test_fail_list:
                    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        # stop on error, don't collect logfile
        if fail_list and stop_on_err:
            pass
        else:
            naples_get_nic_logfile(mtp_mgmt_ctrl, nic_test_list, para_test_list)
            # extract error message if test fail
            for slot, test in fail_slot_test_list:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                if not sn:
                    continue
                err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_mtp_para_err(sn, test)
                for err_msg in err_msg_list:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp, test, err_msg))
                    card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                    if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(alom_sn, dsp, test, err_msg))
        if GLB_CFG_MFG_TEST_MODE:
            mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Complete\n".format(nic_type), level=0)

    return fail_list


def naples_diag_para_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, test_list, stop_on_err, vmarg, aapl, swmtestmode):
    if aapl == False:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel DSP Test Start".format(nic_type), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel PRBS Test Start".format(nic_type), level=0)

    sub_test_list = test_list[:]

    if aapl:
        if nic_type == NIC_Type.ORTANO2:
            sub_test_list = [("NIC_ASIC","PCIE_PRBS"), ("NIC_ASIC","ETH_PRBS"), ("NIC_ASIC","L1")]
        else:
            sub_test_list = [("NIC_ASIC","PCIE_PRBS"), ("NIC_ASIC","ETH_PRBS")]
    else:
        if ("NIC_ASIC","PCIE_PRBS") in sub_test_list:
            sub_test_list.remove(("NIC_ASIC","PCIE_PRBS"))
        if ("NIC_ASIC","ETH_PRBS") in sub_test_list:
            sub_test_list.remove(("NIC_ASIC","ETH_PRBS"))
        if ("NIC_ASIC","L1") in sub_test_list:
            sub_test_list.remove(("NIC_ASIC","L1"))

    fail_list = list()

    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    for slot in nic_list:
        nic_thread = threading.Thread(target = single_nic_diag_regression,
                                      args = (mtp_mgmt_ctrl,
                                              slot,
                                              test_db,
                                              sub_test_list,
                                              nic_test_rslt_list,
                                              stop_on_err,
                                              vmarg,
                                              swmtestmode))
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
    
    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))

    # Collect NIC onboard logfiles
    mtp_mgmt_ctrl.cli_log_inf("Collecting NIC onboard diag logfiles...", level=0)
    for slot in nic_list:
        if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_diag_logfile(slot, aapl):
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Collecting NIC onboard diag logfile failed")

    if aapl == False:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel DSP Test Complete\n".format(nic_type), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel PRBS Test Complete\n".format(nic_type), level=0)

    return fail_list

def naples_diag_mvl_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, test_list, stop_on_err, vmarg, aapl, swmtestmode):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel MVL DSP Test Start".format(nic_type), level=0)
    
    if nic_type == NIC_Type.ORTANO2:
        sub_test_list = [("MVL","ACC"), ("MVL","STUB")]
    else:
        sub_test_list = [()]
    
    fail_list = list()

    for slot in nic_list:
        for dsp, test in sub_test_list:
            if vmarg > 0:
                dsp_disp = "HV_" + dsp
            elif vmarg < 0:
                dsp_disp = "LV_" + dsp
            else:
                dsp_disp = dsp

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

            if dsp == "MVL" and test == "STUB":
                mtp_mgmt_ctrl.mtp_run_diag_test_para_lock()

            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            if dsp == "MVL" and test == "ACC":
                ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_mvl_acc_test(slot)
            elif dsp == "MVL" and test == "STUB":
                ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_mvl_stub_test(slot)
            else:
                ret, err_msg_list = "FAILURE", ["Not the right function for this kind of test"]
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)

            if ret == "SUCCESS":
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp_disp, test, duration))
            else:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, test, ret, duration))
                mtp_mgmt_ctrl.mtp_mgmt_nic_diag_sys_clean(slot)
                if slot not in fail_list:
                    fail_list.append(slot)

                # only display first 3 and last 3 error messages
                if len(err_msg_list) < 6:
                    err_msg_disp_list = err_msg_list
                else:
                    err_msg_disp_list = err_msg_list[:3] + err_msg_list[-3:]
                for err_msg in err_msg_disp_list:
                    mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, test, err_msg))
                    if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(alom_sn, dsp_disp, test, err_msg))

            if dsp == "MVL" and test == "STUB":
                mtp_mgmt_ctrl.mtp_run_diag_test_para_unlock()

            if ret != "SUCCESS" and stop_on_err:
                break
    
    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel MVL DSP Test Complete\n".format(nic_type), level=0)
    return fail_list

def naples_diag_seq_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, test_list, vmarg, stop_on_err, swmtestmode):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Sequential Test Start".format(nic_type), level=0)
    fail_list = list()

    if len(nic_list) <= 5:
        nic_top_test_list = nic_list[:]
        nic_bottom_test_list = []
    # split test nic list into half & half
    else:
        nic_split = len(nic_list)/2
        nic_top_test_list = nic_list[:nic_split]
        nic_bottom_test_list = nic_list[nic_split:]

    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM

    lock = threading.Lock()
#    if not mtp_mgmt_ctrl.mtp_diag_zmq_init():
#        for slot in nic_top_test_list:
#            nic_test_rslt_list[slot] = False
    if False:
        pass
    else:
        # top half of the NICs
        for slot in nic_top_test_list[:]:
            nic_thread = threading.Thread(target = single_nic_zmq_diag_regression,
                                          args = (mtp_mgmt_ctrl,
                                                  slot,
                                                  test_db,
                                                  test_list,
                                                  nic_test_rslt_list,
                                                  stop_on_err,
                                                  vmarg,
                                                  lock,
                                                  swmtestmode))
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

    # reinit the diagmgr for next half zmq test
#    if not mtp_mgmt_ctrl.mtp_diag_zmq_init():
#        for slot in nic_bottom_test_list:
#            nic_test_rslt_list[slot] = False
    if False:
        pass
    else:
        # bottom half of the NICs
        for slot in nic_bottom_test_list[:]:
            nic_thread = threading.Thread(target = single_nic_zmq_diag_regression,
                                          args = (mtp_mgmt_ctrl,
                                                  slot,
                                                  test_db,
                                                  test_list,
                                                  nic_test_rslt_list,
                                                  stop_on_err,
                                                  vmarg,
                                                  lock,
                                                  swmtestmode))
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

    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Sequential Test Complete\n".format(nic_type), level=0)
    return fail_list


def naples_get_nic_logfile(mtp_mgmt_ctrl, nic_list, mtp_para_test_list):
    # power cycle all the NICs
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Init NIC Diag Environment failed", level=0)
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        return False

    mtp_mgmt_ctrl.cli_log_inf("Collecting MTP parallel test logfiles....", level=0)
    for slot in nic_list:
        logfile_list = list()
        if "SNAKE_HBM" in mtp_para_test_list:
            logfile_list.append("snake_hbm.log")
        if "SNAKE_PCIE" in mtp_para_test_list:
            logfile_list.append("snake_pcie.log")
        if "PRBS_ETH" in mtp_para_test_list:
            logfile_list.append("prbs_eth.log")
        if "SNAKE_ELBA" in mtp_para_test_list:
            logfile_list.append("snake_elba.log")

        if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_logfile(slot, logfile_list):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Collecting MTP parallel test logfile failed")
    return


def single_nic_zmq_diag_regression(mtp_mgmt_ctrl, slot, diag_test_db, diag_seq_test_list, nic_test_rslt_list, stop_on_err, vmarg, lock, swmtestmode):
    if lock:
        lock.acquire()
    for dsp, test in diag_seq_test_list:
        if vmarg > 0:
            dsp_disp = "HV_" + dsp
        elif vmarg < 0:
            dsp_disp = "LV_" + dsp
        else:
            dsp_disp = dsp

        test_cfg = diag_test_db.get_diag_seq_test(dsp, test)
        init_cmd = None
        post_cmd = None
        if test_cfg["INIT"] != "":
            init_cmd = test_cfg["INIT"]
        if test_cfg["POST"] != "":
            post_cmd = test_cfg["POST"]

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        opts = test_cfg["OPTS"]
        mode = get_mode_param(mtp_mgmt_ctrl, slot, test)
        diag_cmd = diag_test_db.get_diag_seq_test_run_cmd(dsp, test, slot, opts, sn, vmarg, mode)
        rslt_cmd = diag_test_db.get_diag_seq_test_errcode_cmd(dsp, slot, opts)
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test))

        start_ts = libmfg_utils.timestamp_snapshot()
        ret, err_msg_list = mtp_mgmt_ctrl.mtp_run_diag_test_seq(slot, diag_cmd, rslt_cmd, test, init_cmd, post_cmd)
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)

        # double check the L1 test even it pass
        if dsp == "ASIC" and test == "L1":
            pass_count, log_err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_nic_l1_err(sn)
            # L1 sub test count is 11, err_msg_list should be empty
            number_of_l1_tests = 9
            # But for Elba, there are 13 sub tests
            if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.ORTANO or mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.ORTANO2:
                number_of_l1_tests = 14
            if pass_count != number_of_l1_tests:
                err_msg_list.append("L1 Sub Test only passed: {:d}".format(pass_count))
                if ret == "SUCCESS":
                    ret = "FAIL"
            if log_err_msg_list:
                err_msg_list += log_err_msg_list

        if ret == "SUCCESS":
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp_disp, test, duration))
        else:
            if dsp == "ASIC" and test == "L1" and ret != "SUCCESS":
                mtp_mgmt_ctrl.mtp_run_diag_test_para_lock()
                mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
                mtp_mgmt_ctrl.mtp_run_diag_test_para_unlock()
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, test, ret, duration))
            mtp_mgmt_ctrl.mtp_mgmt_nic_diag_sys_clean(slot)
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp_disp, test, ret, duration))
                mtp_mgmt_ctrl.mtp_mgmt_nic_diag_sys_clean(slot)
            nic_test_rslt_list[slot] = False

            # only display first 3 and last 3 error messages
            if len(err_msg_list) < 6:
                err_msg_disp_list = err_msg_list
            else:
                err_msg_disp_list = err_msg_list[:3] + err_msg_list[-3:]
            for err_msg in err_msg_disp_list:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, test, err_msg))
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(alom_sn, dsp_disp, test, err_msg))
            if stop_on_err:
                break;
    if lock:
        lock.release()


def single_nic_diag_regression(mtp_mgmt_ctrl, slot, diag_test_db, diag_para_test_list, nic_test_rslt_list, stop_on_err, vmarg, swmtestmode):
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
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        alom_sn = None
        if card_type == NIC_Type.NAPLES25SWM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
        mode = get_mode_param(mtp_mgmt_ctrl, slot, test)
        diag_cmd = diag_test_db.get_diag_para_test_run_cmd(dsp, test, slot, opts, sn, mode)
        rslt_cmd = diag_test_db.get_diag_para_test_errcode_cmd(dsp, slot, opts)

        if dsp == "MVL" and test == "STUB":
            mtp_mgmt_ctrl.mtp_run_diag_test_para_lock()

        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        ret, err_msg_list = mtp_mgmt_ctrl.mtp_run_diag_test_para(slot, diag_cmd, rslt_cmd, test, init_cmd, post_cmd)
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)

        # Collect NIC onboard logfiles
        asic_dir_logfile_list = []
        if dsp == "NIC_ASIC" and test == "PCIE_PRBS":
            asic_dir_logfile_list.append("elba_PRBS_PCIE.log")
        if dsp == "NIC_ASIC" and test == "ETH_PRBS":
            asic_dir_logfile_list.append("elba_PRBS_MX.log")
        if dsp == "NIC_ASIC" and test == "L1":
            asic_dir_logfile_list.append("elba_arm_l1_test.log")

        if asic_dir_logfile_list:
            if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_logfile(slot, asic_dir_logfile_list):
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Collecting NIC onboard asic logfile for ({:s}, {:s}) test failed".format(dsp, test))

        if dsp == "NIC_ASIC" and test == "L1":
            pass_count, log_err_msg_list = mtp_mgmt_ctrl.mtp_nic_retrieve_arm_l1_err(sn)
            if card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2:
                number_of_arm_l1_tests = 2
            else:
                number_of_arm_l1_tests = 0
            if pass_count != number_of_arm_l1_tests:
                err_msg_list.append("ARM L1 Sub Test only passed: {:d}".format(pass_count))
                if ret == "SUCCESS":
                    ret = "FAIL"
            if log_err_msg_list:
                err_msg_list += log_err_msg_list

        if ret == "SUCCESS":
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp_disp, test, duration))
            if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, dsp_disp, test, duration))
        else:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, test, ret, duration))
            mtp_mgmt_ctrl.mtp_mgmt_nic_diag_sys_clean(slot)
            if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp_disp, test, ret, duration))
                mtp_mgmt_ctrl.mtp_mgmt_nic_diag_sys_clean(slot)
            nic_test_rslt_list[slot] = False

            # only display first 3 and last 3 error messages
            if len(err_msg_list) < 6:
                err_msg_disp_list = err_msg_list
            else:
                err_msg_disp_list = err_msg_list[:3] + err_msg_list[-3:]
            for err_msg in err_msg_disp_list:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, test, err_msg))
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(alom_sn, dsp_disp, test, err_msg))

        if dsp == "MVL" and test == "STUB":
            mtp_mgmt_ctrl.mtp_run_diag_test_para_unlock()

        if ret != "SUCCESS" and stop_on_err:
            break


def main():
    parser = argparse.ArgumentParser(description="Single MTP Diagnostics Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--stop-on-error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--corner", type=Env_Cond, help="diagnostic environment condition", choices=list(Env_Cond), default=Env_Cond.MFG_NT)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))

    args = parser.parse_args()

    mtp_id = "MTP-000"
    stop_on_err = False
    verbosity = False
    corner = Env_Cond.MFG_NT
    swm_lp_boot_mode = False
    if args.mtpid:
        mtp_id = args.mtpid
        mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    if args.stop_on_error:
        stop_on_err = True
    if args.verbosity:
        verbosity = True
    if args.corner:
        corner = args.corner
    if args.swm:
        swmtestmode = args.swm
        print(" SWMTESTMODE=" + str(swmtestmode))

    # Normal temperature, no voltage corner
    if corner == Env_Cond.MFG_NT:
        fanspd = MTP_Const.MFG_EDVT_NORM_FAN_SPD
        low_temp_threshold = None
        high_temp_threshold = None
        vmarg_list = [0]
    # QA test, normal temperature, two voltage corner
    elif corner == Env_Cond.MFG_QA:
        fanspd = MTP_Const.MFG_EDVT_NORM_FAN_SPD
        low_temp_threshold = None
        high_temp_threshold = None
        vmarg_list = [MTP_Const.MFG_EDVT_HIGH_VOLT, MTP_Const.MFG_EDVT_LOW_VOLT]
    # Low temperature, two voltage corner
    # this is changed to single voltage corner after mtp setup step
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
    # this is changed to single voltage corner after mtp setup step
    elif corner == Env_Cond.MFG_HT:
        if GLB_CFG_MFG_TEST_MODE:
            fanspd = MTP_Const.MFG_EDVT_HIGH_FAN_SPD
            high_temp_threshold = MTP_Const.MFG_EDVT_HIGH_TEMP
        else:
            fanspd = MTP_Const.MFG_MODEL_EDVT_HIGH_FAN_SPD
            high_temp_threshold = MTP_Const.MFG_MODEL_EDVT_HIGH_TEMP
        low_temp_threshold = None
        vmarg_list = [MTP_Const.MFG_EDVT_LOW_VOLT, MTP_Const.MFG_EDVT_HIGH_VOLT]
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
        vmarg_list = [MTP_Const.MFG_EDVT_LOW_VOLT, MTP_Const.MFG_EDVT_HIGH_VOLT]
    # EDVT, low temperature, two voltage corner
    elif corner == Env_Cond.MFG_EDVT_LT:
        fanspd = MTP_Const.MFG_EDVT_LOW_FAN_SPD
        low_temp_threshold = MTP_Const.MFG_EDVT_LOW_TEMP
        high_temp_threshold = None
        vmarg_list = [MTP_Const.MFG_EDVT_HIGH_VOLT, MTP_Const.MFG_EDVT_LOW_VOLT]
    else:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unknown Test Corner")

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

    # find any slots to skip
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)

    # load the diag test config
    naples100_test_cfg_file = "config/naples100_mtp_test_cfg.yaml"
    naples100ibm_test_cfg_file = "config/naples100ibm_mtp_test_cfg.yaml"
    naples100hpe_test_cfg_file = "config/naples100hpe_mtp_test_cfg.yaml"
    naples25_test_cfg_file = "config/naples25_mtp_test_cfg.yaml"
    forio_test_cfg_file = "config/forio_mtp_test_cfg.yaml"
    vomero_test_cfg_file = "config/vomero_mtp_test_cfg.yaml"
    vomero2_test_cfg_file = "config/vomero2_mtp_test_cfg.yaml"
    naples25swm_test_cfg_file = "config/naples25swm_mtp_test_cfg.yaml"
    naples25ocp_test_cfg_file = "config/naples25ocp_mtp_test_cfg.yaml"
    naples25swmdell_test_cfg_file = "config/naples25swmdell_mtp_test_cfg.yaml"
    naples25swm833_test_cfg_file = "config/naples25swm833_mtp_test_cfg.yaml"
    ortano_test_cfg_file = "config/ortano_mtp_test_cfg.yaml"
    
    naples100_test_db = diag_db(corner, naples100_test_cfg_file)
    naples100ibm_test_db = diag_db(corner, naples100ibm_test_cfg_file)
    naples100hpe_test_db = diag_db(corner, naples100hpe_test_cfg_file)
    naples25_test_db = diag_db(corner, naples25_test_cfg_file)
    forio_test_db = diag_db(corner, forio_test_cfg_file)
    vomero_test_db = diag_db(corner, vomero_test_cfg_file)
    vomero2_test_db = diag_db(corner, vomero2_test_cfg_file)
    naples25swm_test_db = diag_db(corner, naples25swm_test_cfg_file)
    naples25ocp_test_db = diag_db(corner, naples25ocp_test_cfg_file)
    naples25swmdell_test_db = diag_db(corner, naples25swmdell_test_cfg_file)
    naples25swm833_test_db = diag_db(corner, naples25swm833_test_cfg_file)
    ortano_test_db = diag_db(corner, ortano_test_cfg_file)

    naples100_seq_test_list = naples100_test_db.get_diag_seq_test_list()
    naples100_mtp_para_test_list = naples100_test_db.get_mtp_para_test_list()
    naples100_para_test_list = naples100_test_db.get_diag_para_test_list()
    naples100_pre_test_check_list = naples100_test_db.get_pre_diag_test_intf_list()
    naples100_post_test_check_list = naples100_test_db.get_post_diag_test_intf_list()
    
    naples100ibm_seq_test_list = naples100ibm_test_db.get_diag_seq_test_list()
    naples100ibm_mtp_para_test_list = naples100ibm_test_db.get_mtp_para_test_list()
    naples100ibm_para_test_list = naples100ibm_test_db.get_diag_para_test_list()
    naples100ibm_pre_test_check_list = naples100ibm_test_db.get_pre_diag_test_intf_list()
    naples100ibm_post_test_check_list = naples100ibm_test_db.get_post_diag_test_intf_list()
    
    naples100hpe_seq_test_list = naples100hpe_test_db.get_diag_seq_test_list()
    naples100hpe_mtp_para_test_list = naples100hpe_test_db.get_mtp_para_test_list()
    naples100hpe_para_test_list = naples100hpe_test_db.get_diag_para_test_list()
    naples100hpe_pre_test_check_list = naples100hpe_test_db.get_pre_diag_test_intf_list()
    naples100hpe_post_test_check_list = naples100hpe_test_db.get_post_diag_test_intf_list()

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

    vomero2_seq_test_list = vomero2_test_db.get_diag_seq_test_list()
    vomero2_mtp_para_test_list = vomero2_test_db.get_mtp_para_test_list()
    vomero2_para_test_list = vomero2_test_db.get_diag_para_test_list()
    vomero2_pre_test_check_list = vomero2_test_db.get_pre_diag_test_intf_list()
    vomero2_post_test_check_list = vomero2_test_db.get_post_diag_test_intf_list()

    naples25swm_seq_test_list = naples25swm_test_db.get_diag_seq_test_list()
    naples25swm_mtp_para_test_list = naples25swm_test_db.get_mtp_para_test_list()
    naples25swm_para_test_list = naples25swm_test_db.get_diag_para_test_list()
    naples25swm_pre_test_check_list = naples25swm_test_db.get_pre_diag_test_intf_list()
    naples25swm_post_test_check_list = naples25swm_test_db.get_post_diag_test_intf_list()

    naples25ocp_seq_test_list = naples25ocp_test_db.get_diag_seq_test_list()
    naples25ocp_mtp_para_test_list = naples25ocp_test_db.get_mtp_para_test_list()
    naples25ocp_para_test_list = naples25ocp_test_db.get_diag_para_test_list()
    naples25ocp_pre_test_check_list = naples25ocp_test_db.get_pre_diag_test_intf_list()
    naples25ocp_post_test_check_list = naples25ocp_test_db.get_post_diag_test_intf_list()

    naples25swmdell_seq_test_list = naples25swmdell_test_db.get_diag_seq_test_list()
    naples25swmdell_mtp_para_test_list = naples25swmdell_test_db.get_mtp_para_test_list()
    naples25swmdell_para_test_list = naples25swmdell_test_db.get_diag_para_test_list()
    naples25swmdell_pre_test_check_list = naples25swmdell_test_db.get_pre_diag_test_intf_list()
    naples25swmdell_post_test_check_list = naples25swmdell_test_db.get_post_diag_test_intf_list()

    naples25swm833_seq_test_list = naples25swm833_test_db.get_diag_seq_test_list()
    naples25swm833_mtp_para_test_list = naples25swm833_test_db.get_mtp_para_test_list()
    naples25swm833_para_test_list = naples25swm833_test_db.get_diag_para_test_list()
    naples25swm833_pre_test_check_list = naples25swm833_test_db.get_pre_diag_test_intf_list()
    naples25swm833_post_test_check_list = naples25swm833_test_db.get_post_diag_test_intf_list()

    ortano_seq_test_list = ortano_test_db.get_diag_seq_test_list()
    ortano_mtp_para_test_list = ortano_test_db.get_mtp_para_test_list()
    ortano_para_test_list = ortano_test_db.get_diag_para_test_list()
    ortano_pre_test_check_list = ortano_test_db.get_pre_diag_test_intf_list()
    ortano_post_test_check_list = ortano_test_db.get_post_diag_test_intf_list()


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
        diag_nic_log_filep = open(diag_nic_log_file, "w+", buffering=0)
        open_file_track_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id,
                             mtp_test_log_filep,
                             mtp_diag_log_filep,
                             diag_nic_log_filep_list,
                             diag_cmd_log_filep = mtp_diag_cmd_log_filep,
                             mgmt_cfg = mtp_mgmt_cfg,
                             apc_cfg = mtp_apc_cfg,
                             slots_to_skip = mtp_slots_to_skip,
                             dbg_mode = verbosity)

    if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, fanspd):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
        return

    # Set Naples25SWM test mode
    mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)

    # Readjust the voltage corners
    # capri = HTHV, HTLV, LTHV, LTLV (old way)
    # elba  = HTLV, HTHV, LTHV, LTLV
    if mtp_mgmt_ctrl.mtp_get_asic_support() == MTP_ASIC_SUPPORT.CAPRI:
        if corner == Env_Cond.MFG_LT or corner == Env_Cond.MFG_HT:
            vmarg_list = [MTP_Const.MFG_EDVT_HIGH_VOLT, MTP_Const.MFG_EDVT_LOW_VOLT]

    # Wait the Chamber temperature, if HT or LT is set
    mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Ambient Temperature Check", level=0)
    rdy = mtp_mgmt_ctrl.mtp_wait_temp_ready(low_temp_threshold, high_temp_threshold)
    if not rdy:
        mtp_mgmt_ctrl.mtp_diag_fail_report("Diag Regression Test Ambient Temperature Check Failed")
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        mtp_test_cleanup(MTP_DIAG_Error.MTP_ENV_SETUP, open_file_track_list)
        return
    # only MFG HT/LT need soaking process
    if corner == Env_Cond.MFG_HT or corner == Env_Cond.MFG_LT:
        mtp_mgmt_ctrl.mtp_wait_soaking()
    mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Ambient Temperature Check Complete\n", level=0)

    naples100_nic_list = list()
    naples100ibm_nic_list = list()
    naples100hpe_nic_list = list()
    naples25_nic_list = list()
    forio_nic_list = list()
    vomero_nic_list = list()
    vomero2_nic_list = list()
    naples25swm_nic_list = list()
    naples25ocp_nic_list = list()
    naples25swmdell_nic_list = list()
    naples25swm833_nic_list = list()
    ortano_nic_list = list()
    ortano2_nic_list = list()
    pass_nic_list = list()
    fail_nic_list = list()
    skip_nic_list = list()

    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(len(nic_prsnt_list)):
        if nic_prsnt_list[slot]:
            if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES100:
                naples100_nic_list.append(slot)
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES100IBM:
                naples100ibm_nic_list.append(slot)
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES100HPE:
                naples100hpe_nic_list.append(slot)
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
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.VOMERO2:
                vomero2_nic_list.append(slot)
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWM:
                naples25swm_nic_list.append(slot)
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25OCP:
                naples25ocp_nic_list.append(slot)                
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWMDELL:
                naples25swmdell_nic_list.append(slot)
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWM833:
                naples25swm833_nic_list.append(slot)
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.ORTANO:
                ortano_nic_list.append(slot)
                pass_nic_list.append(slot)
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.ORTANO2:
                ortano2_nic_list.append(slot)
                pass_nic_list.append(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC Type")
                continue

    nic_type_full_list = [NIC_Type.NAPLES100, NIC_Type.NAPLES25, NIC_Type.FORIO, NIC_Type.VOMERO, NIC_Type.NAPLES25SWM, NIC_Type.VOMERO2, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES25OCP, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.ORTANO, NIC_Type.ORTANO2]
    nic_test_full_list = [naples100_nic_list, naples25_nic_list, forio_nic_list, vomero_nic_list, naples25swm_nic_list, vomero2_nic_list, naples100ibm_nic_list, naples100hpe_nic_list, naples25ocp_nic_list, naples25swmdell_nic_list, naples25swm833_nic_list, ortano_nic_list, ortano2_nic_list]

    nic_skipped_list = mtp_mgmt_ctrl.mtp_get_nic_skip_list()
    for slot in range(len(nic_skipped_list)):
        if nic_skipped_list[slot]:
            skip_nic_list.append(slot)

    # check if MTP support present NIC
    mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression compatibility check started", level=0)
    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
        if nic_type == NIC_Type.NAPLES100:
            mtp_exp_capability = 0x1
            test_db = naples100_test_db
        elif nic_type == NIC_Type.NAPLES100IBM:
            mtp_exp_capability = 0x1
            test_db = naples100ibm_test_db
        elif nic_type == NIC_Type.NAPLES100HPE:
            mtp_exp_capability = 0x1
            test_db = naples100hpe_test_db
        elif nic_type == NIC_Type.NAPLES25:
            mtp_exp_capability = 0x2
            test_db = naples25_test_db
        elif nic_type == NIC_Type.FORIO:
            mtp_exp_capability = 0x1
            test_db = forio_test_db
        elif nic_type == NIC_Type.VOMERO:
            mtp_exp_capability = 0x1
            test_db = vomero_test_db
        elif nic_type == NIC_Type.VOMERO2:
            mtp_exp_capability = 0x3
            test_db = vomero2_test_db
        elif nic_type == NIC_Type.NAPLES25SWM:
            mtp_exp_capability = 0x2
            test_db = naples25swm_test_db
            if len(nic_list):
                for var in range(len(nic_list)):
                    if (mtp_mgmt_ctrl.mtp_get_swmtestmode(nic_list[var]) == Swm_Test_Mode.SWMALOM or mtp_mgmt_ctrl.mtp_get_swmtestmode(nic_list[var]) == Swm_Test_Mode.ALOM):
                        swm_lp_boot_mode=True
            else:
                swm_lp_boot_mode=False

            if (corner != Env_Cond.MFG_NT and corner != Env_Cond.MFG_QA):  #Skip SWM Low Power Test for 4C
                swm_lp_boot_mode=False
        elif nic_type == NIC_Type.NAPLES25OCP:
            mtp_exp_capability = 0x2
            test_db = naples25ocp_test_db
        elif nic_type == NIC_Type.NAPLES25SWMDELL:
            mtp_exp_capability = 0x2
            test_db = naples25swmdell_test_db
        elif nic_type == NIC_Type.NAPLES25SWM833:
            mtp_exp_capability = 0x2
            test_db = naples25swm833_test_db
        elif nic_type == NIC_Type.ORTANO:
            mtp_exp_capability = 0x2
            test_db = ortano_test_db
        elif nic_type == NIC_Type.ORTANO2:
            mtp_exp_capability = 0x2
            test_db = ortano_test_db
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown NIC Type: {:s}".format(nic_type), level=0)
            continue

        if nic_list:
            if not mtp_capability & mtp_exp_capability:
                mtp_mgmt_ctrl.mtp_diag_fail_report("MTP capability 0x{:x} doesn't support {:s}".format(mtp_capability, nic_type))
                libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
                return
            naples_diag_cfg_show(nic_type, test_db, mtp_mgmt_ctrl)
            naples_exec_init_cmd(test_db, mtp_mgmt_ctrl)
            naples_exec_skip_cmd(nic_list, test_db, mtp_mgmt_ctrl)
            naples_exec_param_cmd(nic_list, test_db, mtp_mgmt_ctrl)
    mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression compatibility check complete\n", level=0)

    mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Test Start", level=0)

    # Disable PCIe poll
    diag_pre_fail_list = mtp_mgmt_ctrl.mtp_nic_diag_init_pre()

    for vmarg in vmarg_list:
        do_once = 0
        # stop the next vmarg corner if stop_on_err is set and some nic fails
        if fail_nic_list and stop_on_err:
            break
        fanspd = mtp_mgmt_ctrl.mtp_get_fanspd()
        inlet = mtp_mgmt_ctrl.mtp_get_inlet_temp(low_temp_threshold, high_temp_threshold)
        mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment:", level=0)
        if vmarg > 0:
            mtp_mgmt_ctrl.cli_log_report_inf("******* HV Corner *******")
        elif vmarg < 0:
            mtp_mgmt_ctrl.cli_log_report_inf("******* LV Corner *******")
        else:
            mtp_mgmt_ctrl.cli_log_report_inf("******* NV Corner *******")
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Fan Speed = {:3d}%".format(fanspd))
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(inlet))
        mtp_mgmt_ctrl.cli_log_report_inf("NIC Voltage Margin = {:d}%".format(vmarg))
        mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment End\n", level=0)

        # power cycle all the NIC
        mtp_mgmt_ctrl.mtp_power_cycle_nic()

        if not GLB_CFG_MFG_TEST_MODE:
            # Format the EMMC and get latest diag image for QA only
            nic_util = True
        else:
            # Don't format EMMC to keep diag image installed in previous (DL) stage
            nic_util = True #False
        if not mtp_mgmt_ctrl.mtp_nic_diag_init(vmargin=vmarg, swm_lp=swm_lp_boot_mode, nic_util=nic_util):
            mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
            return


        #NAPLES25 SWM LOW POWER BOOT MODE TEST
        if (corner == Env_Cond.MFG_NT or corner == Env_Cond.MFG_QA):   #Skip SWM Low Power Test for 4 corner
            alom_fail_list = list()
            swm_lp_test_performed = 0
            for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                for var in range(len(nic_list)):
                    slot = nic_list[var]
                    if nic_type == NIC_Type.NAPLES25SWM and (mtp_mgmt_ctrl.mtp_get_swmtestmode(slot) == Swm_Test_Mode.SWMALOM or mtp_mgmt_ctrl.mtp_get_swmtestmode(slot) == Swm_Test_Mode.ALOM):
                            if swm_lp_test_performed == 0:
                                mtp_mgmt_ctrl.cli_log_inf("Starting Naples25 SWM Low Power On Test", level=0)
                            swm_lp_test_performed = 1
                            if not mtp_mgmt_ctrl.mtp_nic_naples25swm_low_power_mode_test(slot):
                                alom_fail_list.append(slot)

            if swm_lp_test_performed > 0:
                mtp_mgmt_ctrl.cli_log_inf("Setting Naples25 SWM Back to High Power Mode (requires a nic reboot)", level=0)
                if not mtp_mgmt_ctrl.mtp_nic_diag_init(vmargin=vmarg, swm_lp=False):
                    mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                    libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                    mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
                    return

            for slot in alom_fail_list:
                if slot in nic_list:
                    nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)


        # Diag Pre Check
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_type == NIC_Type.NAPLES100:
                pre_test_check_list = naples100_pre_test_check_list
            elif nic_type == NIC_Type.NAPLES100IBM:
                pre_test_check_list = naples100ibm_pre_test_check_list
            elif nic_type == NIC_Type.NAPLES100HPE:
                pre_test_check_list = naples100hpe_pre_test_check_list
            elif nic_type == NIC_Type.NAPLES25:
                pre_test_check_list = naples25_pre_test_check_list
            elif nic_type == NIC_Type.FORIO:
                pre_test_check_list = forio_pre_test_check_list
            elif nic_type == NIC_Type.VOMERO:
                pre_test_check_list = vomero_pre_test_check_list
            elif nic_type == NIC_Type.VOMERO2:
                pre_test_check_list = vomero2_pre_test_check_list
            elif nic_type == NIC_Type.NAPLES25SWM:
                pre_test_check_list = naples25swm_pre_test_check_list
            elif nic_type == NIC_Type.NAPLES25OCP:
                pre_test_check_list = naples25ocp_pre_test_check_list
            elif nic_type == NIC_Type.NAPLES25SWMDELL:
                pre_test_check_list = naples25swmdell_pre_test_check_list
            elif nic_type == NIC_Type.NAPLES25SWM833:
                pre_test_check_list = naples25swm833_pre_test_check_list
            elif nic_type == NIC_Type.ORTANO:
                pre_test_check_list = ortano_pre_test_check_list
            elif nic_type == NIC_Type.ORTANO2:
                pre_test_check_list = ortano_pre_test_check_list
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown NIC Type: {:s}".format(nic_type), level=0)
                continue

            if nic_list:
                pre_check_fail_list = naples_exec_pre_check(mtp_mgmt_ctrl,
                                                            nic_type,
                                                            nic_list,
                                                            pre_test_check_list,
                                                            vmarg,
                                                            swmtestmode)
                for slot in pre_check_fail_list:
                    if slot in nic_list:
                        nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)
        
        # NIC Parallel test NON HAL / NON APPL
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_type == NIC_Type.NAPLES100:
                nic_para_test_list = naples100_para_test_list[:]
                test_db = naples100_test_db
            elif nic_type == NIC_Type.NAPLES100IBM:
                nic_para_test_list = naples100ibm_para_test_list[:]
                test_db = naples100ibm_test_db
            elif nic_type == NIC_Type.NAPLES100HPE:
                nic_para_test_list = naples100hpe_para_test_list[:]
                test_db = naples100hpe_test_db
            elif nic_type == NIC_Type.NAPLES25:
                nic_para_test_list = naples25_para_test_list[:]
                test_db = naples25_test_db
            elif nic_type == NIC_Type.FORIO:
                nic_para_test_list = forio_para_test_list[:]
                test_db = forio_test_db
            elif nic_type == NIC_Type.VOMERO:
                nic_para_test_list = vomero_para_test_list[:]
                test_db = vomero_test_db
            elif nic_type == NIC_Type.VOMERO2:
                nic_para_test_list = vomero2_para_test_list[:]
                test_db = vomero2_test_db
            elif nic_type == NIC_Type.NAPLES25SWM:
                if swmtestmode == Swm_Test_Mode.ALOM:
                    continue
                nic_para_test_list = naples25swm_para_test_list[:]
                test_db = naples25swm_test_db
            elif nic_type == NIC_Type.NAPLES25OCP:
                nic_para_test_list = naples25ocp_para_test_list[:]
                test_db = naples25ocp_test_db
            elif nic_type == NIC_Type.NAPLES25SWMDELL:
                nic_para_test_list = naples25swmdell_para_test_list[:]
                test_db = naples25swmdell_test_db
            elif nic_type == NIC_Type.NAPLES25SWM833:
                nic_para_test_list = naples25swm833_para_test_list[:]
                test_db = naples25swmdell_test_db
            elif nic_type == NIC_Type.ORTANO:
                nic_para_test_list = ortano_para_test_list[:]
                test_db = ortano_test_db
            elif nic_type == NIC_Type.ORTANO2:
                nic_para_test_list = ortano_para_test_list[:]
                test_db = ortano_test_db
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown NIC Type: {:s}".format(nic_type), level=0)
                continue

            if nic_list:
                # first round, non-aapl tests
                diag_para_fail_list = naples_diag_para_test(mtp_mgmt_ctrl,
                                                            nic_type,
                                                            nic_list,
                                                            test_db,
                                                            nic_para_test_list,
                                                            stop_on_err,
                                                            vmarg,
                                                            False,
                                                            swmtestmode)
                for slot in diag_para_fail_list:
                    if slot in nic_list and stop_on_err:
                        nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)

        # NIC Parallel test 2nd loop with HAL/APPL for Capri
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_type == NIC_Type.NAPLES100:
                nic_para_test_list = naples100_para_test_list[:]
                test_db = naples100_test_db
            elif nic_type == NIC_Type.NAPLES100IBM:
                nic_para_test_list = naples100ibm_para_test_list[:]
                test_db = naples100ibm_test_db
            elif nic_type == NIC_Type.NAPLES100HPE:
                nic_para_test_list = naples100hpe_para_test_list[:]
                test_db = naples100hpe_test_db
            elif nic_type == NIC_Type.NAPLES25:
                nic_para_test_list = naples25_para_test_list[:]
                test_db = naples25_test_db
            elif nic_type == NIC_Type.FORIO:
                nic_para_test_list = forio_para_test_list[:]
                test_db = forio_test_db
            elif nic_type == NIC_Type.VOMERO:
                nic_para_test_list = vomero_para_test_list[:]
                test_db = vomero_test_db
            elif nic_type == NIC_Type.VOMERO2:
                nic_para_test_list = vomero2_para_test_list[:]
                test_db = vomero2_test_db
            elif nic_type == NIC_Type.NAPLES25SWM:
                if swmtestmode == Swm_Test_Mode.ALOM:
                    continue
                nic_para_test_list = naples25swm_para_test_list[:]
                test_db = naples25swm_test_db
            elif nic_type == NIC_Type.NAPLES25OCP:
                nic_para_test_list = naples25ocp_para_test_list[:]
                test_db = naples25ocp_test_db
            elif nic_type == NIC_Type.NAPLES25SWMDELL:
                nic_para_test_list = naples25swmdell_para_test_list[:]
                test_db = naples25swmdell_test_db
            elif nic_type == NIC_Type.NAPLES25SWM833:
                nic_para_test_list = naples25swm833_para_test_list[:]
                test_db = naples25swmdell_test_db
            elif nic_type == NIC_Type.ORTANO:
                nic_para_test_list = ortano_para_test_list[:]
                test_db = ortano_test_db
            elif nic_type == NIC_Type.ORTANO2:
                nic_para_test_list = ortano_para_test_list[:]
                test_db = ortano_test_db
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown NIC Type: {:s}".format(nic_type), level=0)
                continue

            if nic_list:
                # second round, aapl tests
                if nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
                    aapl = False
                else:
                    aapl = True
                if do_once == 0:
                    if not mtp_mgmt_ctrl.mtp_nic_diag_init(vmargin=vmarg, aapl=aapl):
                        mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment (aapl=True) failed")
                        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                        mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
                        return
                    do_once = 1

                diag_para_fail_list = naples_diag_para_test(mtp_mgmt_ctrl,
                                                            nic_type,
                                                            nic_list,
                                                            test_db,
                                                            nic_para_test_list,
                                                            stop_on_err,
                                                            vmarg,
                                                            True,
                                                            swmtestmode)
                for slot in diag_para_fail_list:
                    if slot in nic_list and stop_on_err:
                        nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)

        # NIC Parallel test for MVL only
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_type == NIC_Type.ORTANO2:
                nic_para_test_list = ortano_para_test_list[:]
                test_db = ortano_test_db
            else:
                continue

            if nic_list:
                mtp_mgmt_ctrl.mtp_power_cycle_nic()
                diag_para_fail_list = naples_diag_mvl_test(mtp_mgmt_ctrl,
                                                           nic_type,
                                                           nic_list,
                                                           test_db,
                                                           nic_para_test_list,
                                                           stop_on_err,
                                                           vmarg,
                                                           True,
                                                           swmtestmode)
                for slot in diag_para_fail_list:
                    if slot in nic_list and stop_on_err:
                        nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)

        # NIC MTP Parallel test
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_type == NIC_Type.NAPLES100:
                mtp_para_test_list = naples100_mtp_para_test_list
            elif nic_type == NIC_Type.NAPLES100IBM:
                mtp_para_test_list = naples100ibm_mtp_para_test_list
            elif nic_type == NIC_Type.NAPLES100HPE:
                mtp_para_test_list = naples100hpe_mtp_para_test_list
            elif nic_type == NIC_Type.NAPLES25:
                mtp_para_test_list = naples25_mtp_para_test_list
            elif nic_type == NIC_Type.FORIO:
                mtp_para_test_list = forio_mtp_para_test_list
            elif nic_type == NIC_Type.VOMERO:
                mtp_para_test_list = vomero_mtp_para_test_list
            elif nic_type == NIC_Type.VOMERO2:
                mtp_para_test_list = vomero2_mtp_para_test_list
            elif nic_type == NIC_Type.NAPLES25SWM:
                if swmtestmode == Swm_Test_Mode.ALOM:
                    continue
                mtp_para_test_list = naples25swm_mtp_para_test_list
            elif nic_type == NIC_Type.NAPLES25OCP:
                mtp_para_test_list = naples25ocp_mtp_para_test_list
            elif nic_type == NIC_Type.NAPLES25SWMDELL:
                mtp_para_test_list = naples25swmdell_mtp_para_test_list
            elif nic_type == NIC_Type.NAPLES25SWM833:
                mtp_para_test_list = naples25swm833_mtp_para_test_list
            elif nic_type == NIC_Type.ORTANO:
                mtp_para_test_list = ortano_mtp_para_test_list
            elif nic_type == NIC_Type.ORTANO2:
                mtp_para_test_list = ortano_mtp_para_test_list
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown NIC Type: {:s}".format(nic_type), level=0)

            if nic_list:
                mtp_para_fail_list = naples_exec_mtp_para_test(mtp_mgmt_ctrl,
                                                               nic_type,
                                                               nic_list,
                                                               mtp_para_test_list,
                                                               vmarg,
                                                               stop_on_err,
                                                               swmtestmode)
                for slot in mtp_para_fail_list:
                    if slot in nic_list and stop_on_err:
                        nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)

        # NIC Sequential test
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_type == NIC_Type.NAPLES100:
                nic_seq_test_list = naples100_seq_test_list[:]
                test_db = naples100_test_db
            elif nic_type == NIC_Type.NAPLES100IBM:
                nic_seq_test_list = naples100ibm_seq_test_list[:]
                test_db = naples100ibm_test_db
            elif nic_type == NIC_Type.NAPLES100HPE:
                nic_seq_test_list = naples100hpe_seq_test_list[:]
                test_db = naples100hpe_test_db
            elif nic_type == NIC_Type.NAPLES25:
                nic_seq_test_list = naples25_seq_test_list[:]
                test_db = naples25_test_db
            elif nic_type == NIC_Type.FORIO:
                nic_seq_test_list = forio_seq_test_list[:]
                test_db = forio_test_db
            elif nic_type == NIC_Type.VOMERO:
                nic_seq_test_list = vomero_seq_test_list[:]
                test_db = vomero_test_db
            elif nic_type == NIC_Type.VOMERO2:
                nic_seq_test_list = vomero2_seq_test_list[:]
                test_db = vomero2_test_db
            elif nic_type == NIC_Type.NAPLES25SWM:
                if swmtestmode == Swm_Test_Mode.ALOM:
                    continue
                nic_seq_test_list = naples25swm_seq_test_list[:]
                test_db = naples25swm_test_db
            elif nic_type == NIC_Type.NAPLES25OCP:
                nic_seq_test_list = naples25ocp_seq_test_list[:]
                test_db = naples25ocp_test_db
            elif nic_type == NIC_Type.NAPLES25SWMDELL:
                nic_seq_test_list = naples25swmdell_seq_test_list[:]
            elif nic_type == NIC_Type.NAPLES25SWM833:
                nic_seq_test_list = naples25swm833_seq_test_list[:]
                test_db = naples25swmdell_test_db
            elif nic_type == NIC_Type.ORTANO:
                nic_seq_test_list = ortano_seq_test_list[:]
                test_db = ortano_test_db
            elif nic_type == NIC_Type.ORTANO2:
                nic_seq_test_list = ortano_seq_test_list[:]
                test_db = ortano_test_db
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown NIC Type: {:s}".format(nic_type), level=0)
                continue

            if nic_list:
                diag_seq_fail_list = naples_diag_seq_test(mtp_mgmt_ctrl,
                                                          nic_type,
                                                          nic_list,
                                                          test_db,
                                                          nic_seq_test_list,
                                                          vmarg,
                                                          stop_on_err,
                                                          swmtestmode)
                for slot in diag_seq_fail_list:
                    if slot in nic_list and stop_on_err:
                        nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)

        # log the diag test history
        mtp_mgmt_ctrl.mtp_mgmt_diag_history_disp()

        # clear the diag test history
        if not stop_on_err:
            mtp_mgmt_ctrl.mtp_mgmt_diag_history_clear()

        if vmarg == MTP_Const.MFG_EDVT_LOW_VOLT:
            diag_sub_dir = "/lv_diag_logs/"
            nic_sub_dir = "/lv_nic_logs/"
            asic_sub_dir = "/lv_asic_logs/"
        elif vmarg == MTP_Const.MFG_EDVT_HIGH_VOLT:
            diag_sub_dir = "/hv_diag_logs/"
            nic_sub_dir = "/hv_nic_logs/"
            asic_sub_dir = "/hv_asic_logs/"
        else:
            diag_sub_dir = "/diag_logs/"
            nic_sub_dir = "/nic_logs/"
            asic_sub_dir = "/asic_logs/"
        # create log dir
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + diag_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + nic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        # save the asic/diag log files
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_DIAG_LOG_FILES, mtp_script_dir + diag_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, mtp_script_dir + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_NIC_LOG_FILES, mtp_script_dir + nic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        # clean up logfiles for the next run
        cmd = "cleanup.sh"
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

#       if not stop_on_err and pass_nic_list:
#           # Re-init EMMC for Elba cards after L1's destructive emmc test
#           nic_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
#           mtp_mgmt_ctrl.mtp_power_off_nic()
#           mtp_mgmt_ctrl.mtp_power_on_nic()
#           mtp_mgmt_ctrl.mtp_nic_emmc_reformat(nic_rslt_list=nic_rslt_list, nic_list=pass_nic_list)
#
#           for slot in range(MTP_Const.MTP_SLOT_NUM):
#               if not nic_rslt_list[slot]:
#                   mtp_mgmt_ctrl.cli_log_slot_err(slot, "Failed to re-initialize EMMC")
#                   if slot not in fail_nic_list:
#                       fail_nic_list.append(slot)
#                   if slot in pass_nic_list:
#                       pass_nic_list.remove(slot)

    # Enable PCIe poll
    #ADD - Bypass shutting down slot right now for debug
    print("STOP ON ERR=" + str(stop_on_err))
    if not stop_on_err:
        diag_post_fail_list = mtp_mgmt_ctrl.mtp_nic_diag_init_post()
        # failed enable pcie poll, fail the card
        for slot in diag_post_fail_list:
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)

    mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Test Complete\n", level=0)

    for slot in pass_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if not swmtestmode == Swm_Test_Mode.ALOM:
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM and (swmtestmode == Swm_Test_Mode.ALOM):
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

    for slot in fail_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if not swmtestmode == Swm_Test_Mode.ALOM:
            mtp_mgmt_ctrl.cli_log_err("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM and (swmtestmode == Swm_Test_Mode.ALOM):
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    for slot in skip_nic_list:
        key = libmfg_utils.nic_key(slot)
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s}".format(key, MTP_DIAG_Report.NIC_DIAG_REGRESSION_SKIP), level=0)

    mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_PASS, open_file_track_list)


if __name__ == "__main__":
    main()
