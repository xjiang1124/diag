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
import traceback

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
import libmtp_utils
from libdefs import MTP_Const
from libdefs import NIC_Type
from libdefs import MTP_ASIC_SUPPORT
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import Swm_Test_Mode
from libdefs import MFG_DIAG_CMDS
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Path
from libdefs import Voltage_Margin
from libdiag_db import diag_db
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libmfg_cfg import *
import test_utils
import testlog


# test cleanup.
def mtp_test_cleanup(error_code, fp_list=None):
    if fp_list:
        for fp in fp_list:
            fp.close()
    os.system("sync")

def naples_diag_cfg_show(card_type, naples_test_db, stage, mtp_mgmt_ctrl):
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
    if stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_4C_L, FF_Stage.FF_4C_H):
        mtp_para_test_list = libmfg_utils.list_subtract(mtp_para_test_list, ["ETH_PRBS"])
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

    if card_type in (ELBA_NIC_TYPE_LIST) and card_type not in (FPGA_TYPE_LIST + [NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT,
                                                                                                        NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4]):
        para_test_list = [("MVL", "ACC"), ("MVL", "STUB")]
        mtp_mgmt_ctrl.cli_log_inf("NIC Sequential Additional Test List:")
        for item in para_test_list:
            mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)
    if card_type in FPGA_TYPE_LIST:
        para_test_list = [("PHY", "XCVR")]
        mtp_mgmt_ctrl.cli_log_inf("NIC Sequential Additional Test List:")
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

def mtp_nic_poll_set(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, skip_testlist, testlist, stage):
    fail_nic_list = list()

    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
        for slot in nic_list:
            if not mtp_mgmt_ctrl._nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue
            # if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            #     continue
            dsp = stage
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            for skip_test in skip_testlist:
                if skip_test in testlist:
                    testlist.remove(skip_test)
            for test in testlist:
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                if test == "PCIE_POLL_DISABLE":
                    ret = mtp_mgmt_ctrl.mtp_nic_pcie_poll_enable(slot, False)
                elif test == "PCIE_POLL_ENABLE":
                    ret = mtp_mgmt_ctrl.mtp_nic_pcie_poll_enable(slot, True)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown Test: {:s}, Ignore".format(test))
                    continue

                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                    break
                else:
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
    return fail_nic_list

def mtp_nic_diag_init_pre(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, skip_testlist, stage):
    """
    setup for regression test
    """
    mtp_mgmt_ctrl.cli_log_inf("NIC Diag Setup started", level = 0)
    testlist=["PCIE_POLL_DISABLE"]
    fail_nic_list = mtp_nic_poll_set(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, skip_testlist, testlist, stage)
    mtp_mgmt_ctrl.cli_log_inf("NIC Diag Setup complete\n", level = 0)
    return fail_nic_list

def mtp_nic_diag_init_post(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, skip_testlist, stage):
    """
    cleanup after regression test
    """
    mtp_mgmt_ctrl.cli_log_inf("NIC Diag Cleanup started", level = 0)
    testlist=["PCIE_POLL_ENABLE"]
    fail_nic_list = mtp_nic_poll_set(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, skip_testlist, testlist, stage)
    mtp_mgmt_ctrl.cli_log_inf("NIC Diag Cleanup complete\n", level = 0)
    return fail_nic_list

def naples_exec_pre_check(mtp_mgmt_ctrl, nic_type, nic_list, nic_check_list, vmarg, swmtestmode, skip_testlist):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Pre Check Start".format(nic_type), level=0)
    nic_test_list = nic_list[:]
    fail_list = list()
    if vmarg == Voltage_Margin.high:
        dsp = "HV_PRE_CHECK"
    elif vmarg == Voltage_Margin.low:
        dsp = "LV_PRE_CHECK"
    else:
        dsp = "PRE_CHECK"

    for skipped_test in skip_testlist:
        if skipped_test in nic_check_list:
            nic_check_list.remove(skipped_test)
    for intf in nic_check_list:
        for slot in nic_test_list[:]:

            if (nic_type == NIC_Type.NAPLES25SWM) and (mtp_mgmt_ctrl.mtp_get_swmtestmode(slot) == Swm_Test_Mode.SWM) and (intf == "NIC_ALOM_CABLE"):
                continue

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, intf))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, intf)
            ret = mtp_mgmt_ctrl.mtp_mgmt_pre_post_diag_check(intf, slot, vmarg)
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, intf, start_ts)
            if ret == "SUCCESS":
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, intf, duration))
            else:
                fail_list.append(slot)
                nic_test_list.remove(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, intf, ret, duration))
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, intf, ret, duration))
                mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, intf, ret, mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot), [])
            
    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Pre Check Complete\n".format(nic_type), level=0)

    return fail_list


def naples_diag_para_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, test_list, stop_on_err, vmarg, aapl, swmtestmode, skip_testlist, stage):
    if aapl == False:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel DSP Test Start".format(nic_type), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel PRBS Test Start".format(nic_type), level=0)

    sub_test_list = test_list[:]

    for skipped_test in skip_testlist:
        sub_test_list = [ (s,t) for s,t in sub_test_list if s != skipped_test ]
        sub_test_list = [ (s,t) for s,t in sub_test_list if t != skipped_test ]

    fail_list = list()

    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    for slot in nic_list:
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            nic_test_rslt_list[slot] = False
            continue
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
            if slot not in fail_list:
                fail_list.append(slot)

    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))

    # Collect NIC onboard logfiles
    mtp_mgmt_ctrl.cli_log_inf("Collecting NIC onboard diag logfiles...", level=0)
    fail_save_list = mtp_mgmt_ctrl.mtp_mgmt_save_nic_diag_logfile(nic_list, stage, "NIC_LOG_SAVE", aapl)
    for slot in fail_save_list:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Collecting NIC onboard diag logfile failed")
        if slot not in fail_list:
            fail_list.append(slot)

    if aapl == False:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel DSP Test Complete\n".format(nic_type), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel PRBS Test Complete\n".format(nic_type), level=0)

    return fail_list

def naples_diag_mvl_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, test_list, stop_on_err, vmarg, aapl, swmtestmode, loopback, skip_testlist):
    
    if nic_type in (ELBA_NIC_TYPE_LIST) and nic_type not in FPGA_TYPE_LIST:
        if loopback:
            sub_test_list = [("MVL","ACC"), ("MVL","STUB"), ("MVL","LINK")]
        else:
            sub_test_list = [("MVL","ACC"), ("MVL","STUB")]
    elif nic_type in (NIC_Type.POMONTEDELL, NIC_Type.LACONA32, NIC_Type.LACONA32DELL) and vmarg == Voltage_Margin.normal:
        sub_test_list = [("PHY", "XCVR")]
    else:
        sub_test_list = [()]

    if len(sub_test_list) == 0 or sub_test_list == [()]:
        pass
    else:
        for skipped_test in skip_testlist:
            sub_test_list = [ (s,t) for s,t in sub_test_list if s != skipped_test ]
            sub_test_list = [ (s,t) for s,t in sub_test_list if t != skipped_test ]
    
    fail_list = list()

    if len(sub_test_list) == 0 or sub_test_list == [()]:
        return []


    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Bash Test Start".format(nic_type), level=0)

    if True in ["MVL" in (s,t) for (s,t) in sub_test_list]:
        if not mtp_mgmt_ctrl.mtp_nic_para_init(nic_list, stop_on_err=False):
            return nic_list
    if True in ["PHY" in (s,t) for (s,t) in sub_test_list]:
        if not mtp_mgmt_ctrl.mtp_nic_mgmt_para_init(nic_list, False, stop_on_err=False):
            return nic_list

    for slot in nic_list:
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            if slot not in fail_list:
                fail_list.append(slot)
            continue
        for dsp, test in sub_test_list:
            if vmarg == Voltage_Margin.high:
                dsp_disp = "HV_" + dsp
            elif vmarg == Voltage_Margin.low:
                dsp_disp = "LV_" + dsp
            else:
                dsp_disp = dsp

            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            if dsp == "MVL" and test == "ACC":
                ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_mvl_acc_test(slot)
            elif dsp == "MVL" and test == "STUB":
                ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_mvl_stub_test(slot, loopback)
            elif dsp == "MVL" and test == "LINK":
                ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_mvl_link_test(slot)
            elif dsp == "PHY" and test == "XCVR":
                ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_phy_xcvr_test(slot)
            else:
                ret, err_msg_list = "FAIL", ["Not the right function for this kind of test"]
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)

            if ret == "SUCCESS":
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp_disp, test, duration))
            else:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, test, ret, duration))
                if not stop_on_err:
                    mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, test, ret, mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot), err_msg_list)
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

            if ret != "SUCCESS" and stop_on_err:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                raise Exception

    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))

    # PHY test bug: previous nic_type's PHY-XCVR test leaves the phy in weird state for next nic_type's para_init. So power off the card to prevent it.
    mtp_mgmt_ctrl.mtp_power_off_nic(nic_list)

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel Bash Test Complete\n".format(nic_type), level=0)
    return fail_list

def naples_diag_ncsi_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, para_test_list, vmarg, stop_on_err, skip_testlist):
    if nic_type in FPGA_TYPE_LIST:
        para_test_list = ["RMII_LINKUP", "UART_LPBACK"]
    else:
        para_test_list = []

    for skipped_test in skip_testlist:
        if skipped_test in para_test_list:
            para_test_list.remove(skipped_test)

    dsp = "NC-SI"
    fail_list = list()
    nic_test_list = nic_list[:]
    if not mtp_mgmt_ctrl.mtp_nic_mgmt_para_init(nic_test_list, False, stop_on_err=stop_on_err):
        mtp_mgmt_ctrl.cli_log_err("Failed to initialize NICs", level=0)
    for slot in nic_test_list:
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            nic_test_list.remove(slot)
            if slot not in fail_list:
                fail_list.append(slot)

    for test in para_test_list:
        for slot in nic_test_list[:]:
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                nic_test_list.remove(slot)
                if slot not in fail_list:
                    fail_list.append(slot)

        if not nic_test_list:
            continue

        for slot in nic_test_list[:]:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)

        mtp_start_ts = mtp_mgmt_ctrl.log_test_start(test)

        ret, test_fail_list = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para_with_oneline_summary(test, nic_test_list, vmarg)
        
        duration = mtp_mgmt_ctrl.log_test_stop(test, mtp_start_ts)
        for slot in nic_test_list[:]:
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, mtp_start_ts)

        # failed nic display
        for slot in test_fail_list:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if not stop_on_err:
                mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, test, ret, mtp_mgmt_ctrl.mtp_get_cmd_buf(), [])
            if stop_on_err:
                nic_test_list.remove(slot)
            if slot not in fail_list:
                fail_list.append(slot)

        # passed nic display
        for slot in nic_test_list:
            if slot not in test_fail_list:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

    # stop on error, don't collect logfile
    if fail_list and stop_on_err:
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
        raise Exception

    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))

    return fail_list

def naples_exec_mtp_para_test(mtp_mgmt_ctrl, nic_type, nic_list, para_test_list, vmarg, stop_on_err, swmtestmode, skip_testlist):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Start".format(nic_type), level=0)

    for skipped_test in skip_testlist:
        if skipped_test in para_test_list:
            para_test_list.remove(skipped_test)

    fail_list = list()
    nic_top_test_list = list()
    nic_bottom_test_list = list()

    if vmarg == Voltage_Margin.high:
        dsp = "HV_ASIC"
    elif vmarg == Voltage_Margin.low:
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

    # separate lists for ortano adi non-msft & msft
    if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADIIBM):
        orc_list, msft_list = [], []
        for slot in nic_list:
            if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM):
                orc_list.append(slot)
            else:
                msft_list.append(slot)
        nic_top_test_list = orc_list[:]
        nic_bot_test_list = msft_list[:]

    if len(nic_top_test_list) == 0:
        nic_top_test_list = nic_list[:]
        nic_bot_test_list = []

    for nic_test_list in nic_top_test_list, nic_bot_test_list:
        fail_slot_test_list = list() # another list to track failure that includes test name with it
        for test in para_test_list:
            for slot in nic_test_list[:]:
                if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                    nic_test_list.remove(slot)
                    if slot not in fail_list:
                        fail_list.append(slot)

            if not nic_test_list:
                continue

            for slot in nic_test_list[:]:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)

            mtp_start_ts = mtp_mgmt_ctrl.log_test_start(test)

            ret, test_fail_list = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(test, nic_test_list, vmarg)
            
            duration = mtp_mgmt_ctrl.log_test_stop(test, mtp_start_ts)
            for slot in nic_test_list[:]:
                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, mtp_start_ts)

            # failed nic display
            for slot in test_fail_list:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
                mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
                if not stop_on_err:
                    mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, test, ret, mtp_mgmt_ctrl.mtp_get_cmd_buf(), [], skip_vrm_check=False)
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
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
            raise Exception

        if GLB_CFG_MFG_TEST_MODE:
            mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Complete\n".format(nic_type), level=0)

    return fail_list, fail_slot_test_list

def naples_diag_seq_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, test_list, vmarg, stop_on_err, swmtestmode, l1_sequence, skip_testlist):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Sequential Test Start".format(nic_type), level=0)
    
    for skipped_test in skip_testlist:
        test_list = [ (s,t) for s,t in test_list if s != skipped_test ]
        test_list = [ (s,t) for s,t in test_list if t != skipped_test ]

    fail_list = list()

    if len(nic_list) <= 5:
        nic_top_test_list = nic_list[:]
        nic_bottom_test_list = []
    # split test nic list into half & half
    else:
        nic_split = len(nic_list)/2
        nic_top_test_list = nic_list[:nic_split]
        nic_bottom_test_list = nic_list[nic_split:]

    if (mtp_mgmt_ctrl._asic_support == MTP_ASIC_SUPPORT.TURBO_ELBA or
        mtp_mgmt_ctrl._asic_support == MTP_ASIC_SUPPORT.TURBO_CAPRI):
        nic_top_test_list    = [x for x in nic_list if x in [0,2,4,6,8]] # odd slots
        nic_bottom_test_list = [x for x in nic_list if x in [1,3,5,7,9]] # even slots
    else:
        l1_sequence = True

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
        if len(nic_top_test_list) > 0:
            adi_nic_list = list()
            for slot in nic_top_test_list:
                if mtp_mgmt_ctrl.mtp_get_nic_type(slot) in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT):
                    adi_nic_list.append(slot)
            if len(adi_nic_list) > 0:
                mtp_mgmt_ctrl.mtp_power_cycle_nic(adi_nic_list, dl=True, count_down=False)

        for slot in nic_top_test_list[:]:
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                nic_test_rslt_list[slot] = False
                continue
            nic_thread = threading.Thread(target = single_nic_zmq_diag_regression,
                                          args = (mtp_mgmt_ctrl,
                                                  slot,
                                                  test_db,
                                                  test_list,
                                                  nic_test_rslt_list,
                                                  stop_on_err,
                                                  vmarg,
                                                  lock,
                                                  l1_sequence,
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
        if len(nic_bottom_test_list) > 0:
            adi_nic_list = list()
            for slot in nic_bottom_test_list:
                if mtp_mgmt_ctrl.mtp_get_nic_type(slot) in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT):
                    adi_nic_list.append(slot)
            if len(adi_nic_list) > 0:
                mtp_mgmt_ctrl.mtp_power_cycle_nic(adi_nic_list, dl=True, count_down=False)

        # bottom half of the NICs
        for slot in nic_bottom_test_list[:]:
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                nic_test_rslt_list[slot] = False
                continue
            nic_thread = threading.Thread(target = single_nic_zmq_diag_regression,
                                          args = (mtp_mgmt_ctrl,
                                                  slot,
                                                  test_db,
                                                  test_list,
                                                  nic_test_rslt_list,
                                                  stop_on_err,
                                                  vmarg,
                                                  lock,
                                                  l1_sequence,
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
            if stop_on_err:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                raise Exception
            if slot not in fail_list:
                fail_list.append(slot)

    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Sequential Test Complete\n".format(nic_type), level=0)
    return fail_list

def single_nic_diag_regression(mtp_mgmt_ctrl, slot, diag_test_db, diag_para_test_list, nic_test_rslt_list, stop_on_err, vmarg, swmtestmode):
    for dsp, test in diag_para_test_list:
        diag_test_timeout= MTP_Const.DIAG_MEM_DDR_STRESS_TEST_TIMEOUT if dsp == "MEM" and test == "DDR_STRESS" else MTP_Const.DIAG_PARA_TEST_TIMEOUT
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            nic_test_rslt_list[slot] = False
            continue
        if vmarg == Voltage_Margin.high:
            dsp_disp = "HV_" + dsp
        elif vmarg == Voltage_Margin.low:
            dsp_disp = "LV_" + dsp
        else:
            dsp_disp = dsp

        # special test, not dsp-based
        if test.startswith("DISP_ECC"):
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test))
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_disp_ecc(slot)
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)

            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, test, "FAILED", duration))
                nic_test_rslt_list[slot] = False
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp_disp, test, duration))
            continue

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
        mode = libmfg_utils.get_mode_param(mtp_mgmt_ctrl, slot, test)
        diag_cmd = diag_test_db.get_diag_para_test_run_cmd(dsp, test, slot, opts, sn, mode)
        rslt_cmd = diag_test_db.get_diag_para_test_errcode_cmd(dsp, slot, opts)

        if dsp == "MVL" and test == "STUB":
            mtp_mgmt_ctrl.mtp_nic_console_lock()

        # quick hack for parameter ETH_PRBS. need to move into yaml config
        if dsp == "NIC_ASIC" and test == "ETH_PRBS" and card_type in (NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT):
            # external loopback for P2C
            if vmarg == Voltage_Margin.normal:
                diag_cmd += " -p 'int_lpbk=0'"
            # internal loopback for 2C/4C
            else:
                diag_cmd += " -p 'int_lpbk=1'"

        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        ret, err_msg_list = mtp_mgmt_ctrl.mtp_run_diag_test_para(slot, diag_cmd, rslt_cmd, test, init_cmd, post_cmd, diag_test_timeout)
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)

        if test == "I2C":
            mtp_mgmt_ctrl.mtp_nic_i2c_bus_scan(slot)

        # Collect NIC onboard logfiles
        asic_dir_logfile_list = []
        path = MTP_DIAG_Logfile.NIC_ONBOARD_ASIC_LOG_DIR
        if dsp == "NIC_ASIC" and test == "PCIE_PRBS" and card_type in ELBA_NIC_TYPE_LIST:
            asic_dir_logfile_list.append(path+"elba_PRBS_PCIE.log")
        if dsp == "NIC_ASIC" and test == "ETH_PRBS" and card_type in ELBA_NIC_TYPE_LIST:
            asic_dir_logfile_list.append(path+"elba_PRBS_MX.log")
        if dsp == "NIC_ASIC" and test == "L1" and card_type in ELBA_NIC_TYPE_LIST:
            asic_dir_logfile_list.append(path+"elba_arm_l1_test.log")

        if dsp == "NIC_ASIC" and test == "PCIE_PRBS" and card_type in GIGLIO_NIC_TYPE_LIST:
            asic_dir_logfile_list.append(path+"giglio_PRBS_PCIE.log")
        if dsp == "NIC_ASIC" and test == "ETH_PRBS" and card_type in GIGLIO_NIC_TYPE_LIST:
            asic_dir_logfile_list.append(path+"giglio_PRBS_MX.log")
        if dsp == "NIC_ASIC" and test == "L1" and card_type in GIGLIO_NIC_TYPE_LIST:
            asic_dir_logfile_list.append(path+"giglio_arm_l1_test.log")
        if dsp == "MEM" and test == "DDR_STRESS":
            asic_dir_logfile_list.append("/data/nic_util/" + "stressapptest.log")

        if asic_dir_logfile_list:
            if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_logfile(slot, asic_dir_logfile_list):
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Collecting NIC onboard asic logfile for ({:s}, {:s}) test failed".format(dsp, test))

        if dsp == "NIC_ASIC" and test == "L1":
            pass_count, log_err_msg_list = mtp_mgmt_ctrl.mtp_nic_retrieve_arm_l1_err(sn)
            if card_type in ELBA_NIC_TYPE_LIST or card_type in GIGLIO_NIC_TYPE_LIST:
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
            if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp_disp, test, ret, duration))

            if not stop_on_err:
                mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, test, ret, mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot), err_msg_list)

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
            mtp_mgmt_ctrl.mtp_nic_console_unlock()

        if ret != "SUCCESS" and stop_on_err:
            break

@test_utils.parallel_threaded_test
def naples_get_nic_logfile(mtp_mgmt_ctrl, slot, mtp_para_test_list, stop_on_err):
    logfile_list = list()
    path = MTP_DIAG_Logfile.NIC_ONBOARD_ASIC_LOG_DIR
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if "SNAKE_HBM" in mtp_para_test_list:
        logfile_list.append(path+"snake_hbm.log")
        logfile_list.append("/data/nic_util/asicutil*log")
    if "SNAKE_PCIE" in mtp_para_test_list:
        logfile_list.append(path+"snake_pcie.log")
        logfile_list.append("/data/nic_util/asicutil*log")
    if "PRBS_ETH" in mtp_para_test_list:
        logfile_list.append(path+"prbs_eth.log")
        logfile_list.append("/data/nic_util/asicutil*log")
    if "SNAKE_ELBA" in mtp_para_test_list:
        if nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"snake_giglio.log")
        else:
            logfile_list.append(path+"snake_elba.log")
        logfile_list.append("/data/nic_util/asicutil*log")
    if "ETH_PRBS" in mtp_para_test_list:
        if nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"giglio_PRBS_MX.log")
        else:
            logfile_list.append(path+"elba_PRBS_MX.log")
    if "ARM_L1" in mtp_para_test_list:
        if nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"giglio_arm_l1_test.log")
        else:
            logfile_list.append(path+"elba_arm_l1_test.log")
    if "PCIE_PRBS" in mtp_para_test_list:
        if nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"giglio_PRBS_PCIE.log")
        else:
            logfile_list.append(path+"elba_PRBS_PCIE.log")
        logfile_list.append("/data/nic_util/asicutil*log")
    if "DDR_BIST" in mtp_para_test_list:
        logfile_list.append(path+"arm_ddr_bist_0.log")
        logfile_list.append(path+"arm_ddr_bist_1.log")

    if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_logfile(slot, logfile_list):
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Collecting MTP parallel test logfile failed")
        return False
    return True

def parse_nic_test_logfile(mtp_mgmt_ctrl, fstl, vmarg):
    if vmarg == Voltage_Margin.high:
        dsp = "HV_ASIC"
    elif vmarg == Voltage_Margin.low:
        dsp = "LV_ASIC"
    else:
        dsp = "ASIC"
    # extract error message if test fail
    for slot, test in fstl:
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if not sn:
            continue
        err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_mtp_para_err(sn, test)
        # only display first 3 and last 3 error messages
        if len(err_msg_list) < 6:
            err_msg_disp_list = err_msg_list
        else:
            err_msg_disp_list = err_msg_list[:3] + err_msg_list[-3:]
        for err_msg in err_msg_disp_list:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp, test, err_msg))
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(alom_sn, dsp, test, err_msg))
    return

def single_nic_zmq_diag_regression(mtp_mgmt_ctrl, slot, diag_test_db, diag_seq_test_list, nic_test_rslt_list, stop_on_err, vmarg, lock, l1_sequence, swmtestmode):
    if l1_sequence:
        lock.acquire()
    else: # turbo-parallel l1
        mtp_mgmt_ctrl.mtp_turbo_j2c_lock(slot)        
        
    err_msg_list = list()
    for dsp, test in diag_seq_test_list:
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            nic_test_rslt_list[slot] = False
            continue
        if vmarg == Voltage_Margin.high:
            dsp_disp = "HV_" + dsp
        elif vmarg == Voltage_Margin.low:
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
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        opts = test_cfg["OPTS"]
        mode = libmfg_utils.get_mode_param(mtp_mgmt_ctrl, slot, test)
        diag_cmd = diag_test_db.get_diag_seq_test_run_cmd(dsp, test, slot, opts, sn, vmarg, mode)
        rslt_cmd = diag_test_db.get_diag_seq_test_errcode_cmd(dsp, slot, opts)
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test))

        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        if dsp == "ASIC" and test == "L1":
            if not mtp_mgmt_ctrl.mtp_run_asic_l1_bash(slot, sn, mode, vmarg):
                ret = "FAIL"
            else:
                ret = "SUCCESS"
        else:
            ret, err_msg_list = mtp_mgmt_ctrl.mtp_run_diag_test_seq(slot, diag_cmd, rslt_cmd, test, init_cmd, post_cmd)
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)

        # double check the L1 test even it pass
        if dsp == "ASIC" and test == "L1":
            pass_count, log_err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_nic_l1_err(sn)
            number_of_l1_tests = 9
            if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
                number_of_l1_tests = 9
            if pass_count != number_of_l1_tests:
                err_msg_list.append("L1 Sub Test only passed: {:d}".format(pass_count))
                if ret == "SUCCESS":
                    ret = "FAIL"
            if log_err_msg_list:
                err_msg_list += log_err_msg_list

        if ret == "SUCCESS":
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp_disp, test, duration))
        else:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, test, ret, duration))
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp_disp, test, ret, duration))

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

    if l1_sequence:
        if not stop_on_err:
            for dsp, test in diag_seq_test_list:
                if dsp == "ASIC" and test == "L1" and not nic_test_rslt_list[slot]:
                    mtp_mgmt_ctrl._lock.acquire()
                    mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
                    mtp_mgmt_ctrl._lock.release()

                    mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, test, ret, mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot), err_msg_list)
        lock.release()

    else: # turbo-parallel l1
        mtp_mgmt_ctrl.mtp_turbo_j2c_unlock(slot)

        # wait for all slots to complete
        while True in [x.locked() for x in mtp_mgmt_ctrl._turbo_j2c_lock]:
            continue

        if not stop_on_err:
            for dsp, test in diag_seq_test_list:
                if dsp == "ASIC" and test == "L1" and not nic_test_rslt_list[slot]:
                    mtp_mgmt_ctrl._lock.acquire()
                    mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
                    mtp_mgmt_ctrl._lock.release()

                    mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, test, ret, mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot), err_msg_list)


def naples_image_verify(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, fail_nic_list, skip_testlist, dsp, stop_on_err):
    # hook to skip this portion
    if "PROG_UPDATE" in skip_testlist:
        return fail_nic_list

    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
        for slot in nic_list:
            if slot in fail_nic_list:
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                continue
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            testlist = ["CPLD_INIT", "NIC_BOOT_INIT", "CPLD_VERIFY", "QSPI_VERIFY"]

            if nic_type in (NIC_Type.ORTANO2, NIC_Type.POMONTEDELL):
                testlist.insert(0, "VDD_DDR_VERIFY")

            for skip_test in skip_testlist:
                if skip_test in testlist:
                    testlist.remove(skip_test)
            for test in testlist:
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                
                # load CPLD version
                if test == "CPLD_INIT":
                    ret = mtp_mgmt_ctrl.mtp_nic_cpld_init(slot, smb=True)
                # load diagfw version
                elif test == "NIC_BOOT_INIT":
                    ret = mtp_mgmt_ctrl.mtp_nic_boot_info_init(slot)
                # check CPLD version
                elif test == "CPLD_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot, timestamp_check=False, console=True) # cant read timestamp from smb
                    if not ret:
                        ret = True
                # check diagfw version
                elif test == "QSPI_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_verify_nic_qspi(slot)

                    if not ret:
                        ret = True
                elif test == "VDD_DDR_VERIFY":
                    ret = mtp_mgmt_ctrl.mtp_nic_vdd_ddr_fix(slot, console=True)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
                    continue

                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                    mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    break
                else:
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

    return fail_nic_list

def single_nic_test_fpga_program(mtp_mgmt_ctrl, slot, skip_testlist, nic_test_rslt_list, dsp):
    return single_nic_fpga_prog(mtp_mgmt_ctrl, slot, skip_testlist, nic_test_rslt_list, dsp, test_fpga=True)

def single_nic_prod_fpga_program(mtp_mgmt_ctrl, slot, skip_testlist, nic_test_rslt_list, dsp):
    return single_nic_fpga_prog(mtp_mgmt_ctrl, slot, skip_testlist, nic_test_rslt_list, dsp, test_fpga=False)

def single_nic_fpga_prog(mtp_mgmt_ctrl, slot, skip_testlist, nic_test_rslt_list, dsp, test_fpga):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

    if nic_type not in FPGA_TYPE_LIST:
        testlist = []
        return True

    if test_fpga:
        testlist = ["TEST_FPGA_PROG"]
        cpld_img_file = NIC_IMAGES.test_fpga_img[nic_type]
    else:
        testlist = ["PROD_FPGA_PROG"]
        cpld_img_file = NIC_IMAGES.cpld_img[nic_type]

    for skip_test in skip_testlist:
        if skip_test in testlist:
            testlist.remove(skip_test)

    for test in testlist:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        if test == "TEST_FPGA_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_fpga(slot, ["cfg0"], [cpld_img_file])
        elif test == "PROD_FPGA_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_fpga(slot, ["cfg0"], [cpld_img_file])
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown Test: {:s}, Ignore".format(test))
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
    parser = argparse.ArgumentParser(description="Single MTP Diagnostics Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--stop-on-error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--stage", "--corner", type=FF_Stage, help="diagnostic environment condition", choices=list(FF_Stage), default=FF_Stage.FF_P2C)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip-test", help="skip a particular test or test section", nargs="*", default=[])
    parser.add_argument("--only-test", help="run particular tests only", nargs="*", default=[])
    parser.add_argument("--fail-slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("--skip-slots", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--l1-seq", help="asic L1 run under sequence mode", action='store_true')
    args = parser.parse_args()

    mtp_id = "MTP-000"
    stop_on_err = False
    verbosity = False
    l1_sequence = False
    stage = FF_Stage.FF_P2C
    swm_lp_boot_mode = False
    if args.mtpid:
        mtp_id = args.mtpid
        mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    if args.stop_on_error:
        stop_on_err = True
    if args.verbosity:
        verbosity = True
    if args.stage:
        stage = args.stage
    if args.l1_seq:
        l1_sequence = True
    if args.swm:
        swmtestmode = args.swm
        print(" SWMTESTMODE=" + str(swmtestmode))

    low_temp_threshold, high_temp_threshold = libmfg_utils.pick_temperature_thresholds(stage)
    fanspd = libmfg_utils.pick_fan_speed(stage)
    vmarg_list = libmfg_utils.pick_voltage_margin(stage)

    # load the mtp config
    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    if stage == FF_Stage.FF_ORT: 
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/ort_mtp_chassis_cfg.yaml"))
    if stage == FF_Stage.FF_RDT:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/rdt_mtp_chassis_cfg.yaml"))
    if args.mtpcfg:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/"+args.mtpcfg))
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

    # set skip slots when pass in skip_slots
    if len(args.skip_slots) > 0 and not mtp_cfg_db.set_mtp_slots_to_skip(mtp_id, args.skip_slots):
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to set skip slots")

    # find any slots to skip
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)

    # load the diag test config
    test_cfg_file = dict()
    test_cfg_file[NIC_Type.NAPLES100] = "config/naples100_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.NAPLES100IBM] = "config/naples100ibm_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.NAPLES100HPE] = "config/naples100hpe_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.NAPLES100DELL] = "config/naples100dell_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.NAPLES25] = "config/naples25_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.FORIO] = "config/forio_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.VOMERO] = "config/vomero_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.VOMERO2] = "config/vomero2_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.NAPLES25SWM] = "config/naples25swm_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.NAPLES25OCP] = "config/naples25ocp_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.NAPLES25SWMDELL] = "config/naples25swmdell_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.NAPLES25SWM833] = "config/naples25swm833_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO] = "config/ortano_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2] = "config/ortano_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2ADI] = "config/ortano_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2ADIIBM] = "config/ortanoadi_ibm_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2ADIMSFT] = "config/ortanoadi_msft_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2ADICR] = "config/ortanoadi_cr_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2ADICRMSFT] = "config/ortanoadi_cr_msft_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2ADICRS4] = "config/ortanoadi_cr_s4_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2INTERP] = "config/ortanoi_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2SOLO] = "config/ortanos_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2SOLOORCTHS] = "config/ortanos_ths_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2SOLOMSFT] = "config/ortanos_msft_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2SOLOS4] = "config/ortanos_s4_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.POMONTEDELL] = "config/pomontedell_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.LACONA32DELL] = "config/lacona32dell_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.LACONA32] = "config/lacona32_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.GINESTRA_D4] = "config/ginestra_d4_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.GINESTRA_D5] = "config/ginestra_d5_mtp_test_cfg.yaml"
    
    test_db = dict()
    for nic_type in test_cfg_file.keys():
        test_db[nic_type] = diag_db(stage, test_cfg_file[nic_type])

    seq_test_list = dict()
    for nic_type in test_db.keys():
        seq_test_list[nic_type] = test_db[nic_type].get_diag_seq_test_list()

    mtp_para_test_list = dict()
    for nic_type in test_db.keys():
        mtp_para_test_list[nic_type] = test_db[nic_type].get_mtp_para_test_list()
        if stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_4C_L, FF_Stage.FF_4C_H):
            mtp_para_test_list[nic_type] = libmfg_utils.list_subtract(mtp_para_test_list[nic_type], ["ETH_PRBS"])

    para_test_list = dict()
    for nic_type in test_db.keys():
        para_test_list[nic_type] = test_db[nic_type].get_diag_para_test_list()

    pre_test_check_list = dict()
    for nic_type in test_db.keys():
        pre_test_check_list[nic_type] = test_db[nic_type].get_pre_diag_test_intf_list()

    post_test_check_list = dict()
    for nic_type in test_db.keys():
        post_test_check_list[nic_type] = test_db[nic_type].get_post_diag_test_intf_list()

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id,
                             sys.stdout,
                             None,
                             [],
                             None,
                             mgmt_cfg = mtp_mgmt_cfg,
                             apc_cfg = mtp_apc_cfg,
                             slots_to_skip = mtp_slots_to_skip,
                             dbg_mode = verbosity)

    # logfiles
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=stage)

    try:
        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, stage=stage):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
            return

        # Set Naples25SWM test mode
        mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)

        # Wait the Chamber temperature, if HT or LT is set
        mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Ambient Temperature Check", level=0)
        rdy = mtp_mgmt_ctrl.mtp_wait_temp_ready(low_temp_threshold, high_temp_threshold)
        if not rdy:
            mtp_mgmt_ctrl.mtp_diag_fail_report("Diag Regression Test Ambient Temperature Check Failed")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            mtp_test_cleanup(MTP_DIAG_Error.MTP_ENV_SETUP, open_file_track_list)
            return
        # only MFG HT/LT need soaking process
        if stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_4C_L, FF_Stage.FF_4C_H):
            mtp_mgmt_ctrl.mtp_wait_soaking()
        mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Ambient Temperature Check Complete\n", level=0)

        inlet = mtp_mgmt_ctrl.mtp_get_inlet_temp(low_temp_threshold, high_temp_threshold)
        if stage in (FF_Stage.FF_2C_H, FF_Stage.FF_4C_H, FF_Stage.FF_ORT, FF_Stage.FF_RDT) and inlet > MTP_Const.HIGH_CHAMBER_UPPER_LIMIT:
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP temperature is over 60 degree")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            mtp_test_cleanup(MTP_DIAG_Error.MTP_ENV_SETUP, open_file_track_list)
            return

        # Construct data structures for cards to test
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        pass_nic_list = list()
        fail_nic_list = list()
        skip_nic_list = list()

        # Add failed slots from toplevel
        if args.fail_slots:
            for slot in args.fail_slots:
                fail_nic_list.append(int(slot))

        nic_type_full_list = MFG_VALID_NIC_TYPE_LIST
        nic_test_full_list = list() # list of lists, NOT dict. order of insertion matters
        nic_type_prsnt_list = list() # list of types present
        for nic_type in nic_type_full_list:
            nic_type_list = list()
            # make a list for all NICs of this type in MTP
            for slot in range(MTP_Const.MTP_SLOT_NUM):
                if slot in fail_nic_list:
                    continue
                if not nic_prsnt_list[slot]:
                    continue
                if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == nic_type:
                    nic_type_list.append(slot)
                    pass_nic_list.append(slot)
                    if nic_type not in nic_type_prsnt_list:
                        nic_type_prsnt_list.append(nic_type)
            nic_test_full_list.append(nic_type_list)

        nic_skipped_list = mtp_mgmt_ctrl.mtp_get_nic_skip_list()
        for slot in range(len(nic_skipped_list)):
            if nic_skipped_list[slot]:
                skip_nic_list.append(slot)

        nic_type_prsnt_list = [type_present for type_present,nic_present in zip(nic_type_full_list, nic_test_full_list) if nic_present]

        # check if MTP support present NIC
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression compatibility check started", level=0)
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_type == NIC_Type.VOMERO2:
                mtp_exp_capability = 0x3
            elif nic_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
                mtp_exp_capability = 0x2
            elif nic_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
                mtp_exp_capability = 0x1
            else:
                mtp_mgmt_ctrl.cli_log_err("NIC Type {:s}'s MTP compatibility unknown".format(nic_type), level=0)
                continue

            if nic_type == NIC_Type.NAPLES25SWM:
                if nic_list:
                    for slot in range(len(nic_list)):
                        if (mtp_mgmt_ctrl.mtp_get_swmtestmode(nic_list[slot]) in (Swm_Test_Mode.SWMALOM, Swm_Test_Mode.ALOM)):
                            swm_lp_boot_mode=True
                else:
                    swm_lp_boot_mode=False

                if stage not in (FF_Stage.FF_P2C, FF_Stage.QA, FF_Stage.FF_ORT, FF_Stage.FF_RDT):    #Skip SWM Low Power Test for 4C
                    swm_lp_boot_mode=False

            if nic_list:
                if not mtp_capability & mtp_exp_capability:
                    mtp_mgmt_ctrl.mtp_diag_fail_report("MTP capability 0x{:x} doesn't support {:s}".format(mtp_capability, nic_type))
                    libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                    mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
                    return
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression compatibility check complete\n", level=0)

        # Print the dsp configs
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_list:
                nic_test_db = test_db[nic_type]
                naples_diag_cfg_show(nic_type, nic_test_db, stage, mtp_mgmt_ctrl)
                naples_exec_init_cmd(nic_test_db, mtp_mgmt_ctrl)
                naples_exec_skip_cmd(nic_list, nic_test_db, mtp_mgmt_ctrl)
                naples_exec_param_cmd(nic_list, nic_test_db, mtp_mgmt_ctrl)

        mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Test Start", level=0)

        programmables_checked = False

        for vmarg_idx, vmarg in enumerate(vmarg_list):
            do_once = 0
            # stop the next vmarg corner if stop_on_err is set and some nic fails
            if fail_nic_list and stop_on_err:
                break
            fanspd = mtp_mgmt_ctrl.mtp_get_fanspd()
            inlet = mtp_mgmt_ctrl.mtp_get_inlet_temp(low_temp_threshold, high_temp_threshold)
            mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment:", level=0)
            if vmarg == Voltage_Margin.high:
                mtp_mgmt_ctrl.cli_log_report_inf("******* HV Corner *******")
            elif vmarg == Voltage_Margin.low:
                mtp_mgmt_ctrl.cli_log_report_inf("******* LV Corner *******")
            else:
                mtp_mgmt_ctrl.cli_log_report_inf("******* NV Corner *******")
            mtp_mgmt_ctrl.cli_log_report_inf("MTP Fan Speed = {:3d}%".format(fanspd))
            mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(inlet))
            mtp_mgmt_ctrl.cli_log_report_inf("NIC Voltage Margin = {:s}".format(vmarg))
            mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment End\n", level=0)

            if vmarg_idx > 0:
                mtp_mgmt_ctrl.mtp_diag_dsp_restart()

            if vmarg_idx == 0:
                ######################################################################
                #
                #  One-time steps
                #
                ######################################################################

                if not programmables_checked and stage in (FF_Stage.FF_P2C, FF_Stage.FF_2C_L, FF_Stage.FF_4C_L):
                    mtp_mgmt_ctrl.mtp_power_off_nic()
                    mtp_mgmt_ctrl.mtp_power_on_nic(slot_list=pass_nic_list, dl=False)

                    dsp = stage

                    # cpld & qspi image check
                    dl_check_fail_list = naples_image_verify(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, fail_nic_list, args.skip_test, dsp, stop_on_err)
                    programmables_checked = True
                    for slot in dl_check_fail_list:
                        if slot in nic_list:
                            nic_list.remove(slot)
                        if slot not in fail_nic_list:
                            fail_nic_list.append(slot)
                        if slot in pass_nic_list:
                            pass_nic_list.remove(slot)

                # Disable PCIe polling
                mtp_mgmt_ctrl.mtp_power_off_nic()
                mtp_mgmt_ctrl.mtp_power_on_nic(slot_list=pass_nic_list, dl=False)
                if mtp_mgmt_ctrl.mtp_get_asic_support() == MTP_ASIC_SUPPORT.CAPRI:
                    mtp_mgmt_ctrl.cli_log_inf("Wait {:02d} seconds for NIC power up before disable PCIE poll".format(MTP_Const.MTP_PCIE_EN_DIS_DELAY), level=0)
                    libmfg_utils.count_down(MTP_Const.MTP_PCIE_EN_DIS_DELAY)
                    diag_pre_fail_list = mtp_nic_diag_init_pre(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, args.skip_test, stage)

                if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_test_full_list, vmargin=vmarg, swm_lp=swm_lp_boot_mode, nic_util=True, stop_on_err=stop_on_err):
                    #mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                    for nic_list in nic_test_full_list:
                        for slot in nic_list:
                            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)
                                if stop_on_err:
                                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                                    return
            else:
                if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_test_full_list, vmargin=vmarg, swm_lp=swm_lp_boot_mode, nic_util=False, stop_on_err=stop_on_err):
                    #mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                    for nic_list in nic_test_full_list:
                        for slot in nic_list:
                            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)
                                if stop_on_err:
                                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                                    return

            ### CAPRI TEST ORDER
            if mtp_mgmt_ctrl._asic_support in (MTP_ASIC_SUPPORT.CAPRI, MTP_ASIC_SUPPORT.TURBO_CAPRI):
                test_section_list = ["ALOM_LP_MODE", "PRE_CHECK", "ARM_DSP", "NIC_DIAG_INIT_AAPL", "ARM_PRBS", "SNAKE", "J2C_SEQ"]
            ### ELBA TEST ORDER
            if mtp_mgmt_ctrl._asic_support in (MTP_ASIC_SUPPORT.ELBA, MTP_ASIC_SUPPORT.TURBO_ELBA):
                test_section_list = ["PRE_CHECK", "MVL", "SNAKE", "ARM_PRBS", "ARM_DSP", "NIC_DIAG_INIT", "NIC_EDMA_ENV_INIT", "EDMA", "J2C_SEQ"]
            ### ELBA TEST ORDER WITH SPECIAL NC-SI IMAGE
            if stage == FF_Stage.FF_P2C and libmfg_utils.list_intersection(FPGA_TYPE_LIST, nic_type_prsnt_list):
                test_section_list = ["TEST_FPGA_PROG", "NC-SI", "NIC_DIAG_INIT", "PROD_FPGA_PROG", "NIC_DIAG_INIT", "PRE_CHECK", "MVL", "SNAKE", "ARM_PRBS", "ARM_DSP", "NIC_DIAG_INIT", "NIC_EDMA_ENV_INIT", "EDMA", "J2C_SEQ"]

                if stage not in (FF_Stage.FF_P2C, FF_Stage.QA, FF_Stage.FF_ORT, FF_Stage.FF_RDT):   #Skip SWM Low Power Test for 4 corner
                    test_section_list.remove("ALOM_LP_MODE")

            if args.skip_test:
                test_section_list = libmfg_utils.list_subtract(test_section_list, args.skip_test)
            if args.only_test:
                test_section_list = libmfg_utils.list_intersection(test_section_list, args.only_test)

            for test_section in test_section_list:
                # check MTP PSU PIN before each test stage
                mtp_mgmt_ctrl.cli_log_inf("Check MTP PSU PIN Before Test Stage", level=0)
                if not mtp_mgmt_ctrl.mtp_psu_init():
                    # Fail all cards
                    mtp_mgmt_ctrl.cli_log_err("PSU PIN Check Failed, Fail All Card Out", level=0)
                    for nic_list in nic_test_full_list:
                        for slot in nic_list:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)
                    break
                # check MTP HOST NIC Device before each test stage
                mtp_mgmt_ctrl.cli_log_inf("Check MTP HOST NIC Device Before Test Stage", level=0)
                if not libmtp_utils.check_mtp_host_nic_presence(mtp_mgmt_ctrl):
                    # Fail all cards
                    mtp_mgmt_ctrl.cli_log_err("MTP HOST NIC Device Check Failed, Fail All Card Out", level=0)
                    for nic_list in nic_test_full_list:
                        for slot in nic_list:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)
                    break
                # check MTP FAN SPEED before each test stage
                mtp_mgmt_ctrl.cli_log_inf("Check MTP Fan Speed Before Test Stage", level=0)
                if not mtp_mgmt_ctrl.mtp_inlet_temp_test():
                    # Fail all cards
                    mtp_mgmt_ctrl.cli_log_err("MTP Fan Speed Check Failed, Fail All Card Out", level=0)
                    for nic_list in nic_test_full_list:
                        for slot in nic_list:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)
                    break

                if test_section == "PRE_CHECK":
                    ######################################################################
                    #
                    #  Diag Pre Check
                    #
                    ######################################################################
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        nic_pre_test_check_list = pre_test_check_list[nic_type]

                        if nic_list:
                            pre_check_fail_list = naples_exec_pre_check(mtp_mgmt_ctrl,
                                                                        nic_type,
                                                                        nic_list,
                                                                        nic_pre_test_check_list,
                                                                        vmarg,
                                                                        swmtestmode,
                                                                        args.skip_test)
                            for slot in pre_check_fail_list:
                                if slot in nic_list:
                                    nic_list.remove(slot)
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)

                elif test_section == "MVL":
                    ######################################################################
                    #
                    #  NIC Sequential test for MVL only
                    #
                    ######################################################################
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        if nic_type not in (ELBA_NIC_TYPE_LIST) or nic_type in (NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4):
                            continue

                        nic_para_test_list = para_test_list[nic_type]
                        nic_test_db = test_db[nic_type]

                        if stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_4C_L, FF_Stage.FF_4C_H):
                            loopback = False
                        else:
                            loopback = True
                        if nic_list:
                            diag_para_fail_list = naples_diag_mvl_test(mtp_mgmt_ctrl,
                                                                       nic_type,
                                                                       nic_list,
                                                                       nic_test_db,
                                                                       nic_para_test_list,
                                                                       stop_on_err,
                                                                       vmarg,
                                                                       True,
                                                                       swmtestmode,
                                                                       loopback,
                                                                       args.skip_test)
                            for slot in diag_para_fail_list:
                                if slot in nic_list and stop_on_err:
                                    nic_list.remove(slot)
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)

                elif test_section == "NC-SI":
                    ######################################################################
                    #
                    #  NIC Parallel test for NC-SI loopback only
                    #
                    ######################################################################
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
                            continue

                        nic_para_test_list = para_test_list[nic_type]
                        nic_test_db = test_db[nic_type]

                        if nic_list:
                            diag_para_fail_list = naples_diag_ncsi_test(mtp_mgmt_ctrl,
                                                                       nic_type,
                                                                       nic_list,
                                                                       nic_test_db,
                                                                       nic_para_test_list,
                                                                       vmarg,
                                                                       stop_on_err,
                                                                       args.skip_test)
                            for slot in diag_para_fail_list:
                                if slot in nic_list and stop_on_err:
                                    nic_list.remove(slot)
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)

                elif test_section == "SNAKE":
                    ######################################################################
                    #
                    #  NIC MTP Parallel test
                    #
                    ######################################################################
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        if nic_type == NIC_Type.NAPLES25SWM:
                            if swmtestmode == Swm_Test_Mode.ALOM:
                                continue
                        nic_mtp_para_test_list = mtp_para_test_list[nic_type]

                        if ("RMII_LINKUP") in nic_mtp_para_test_list:
                            nic_mtp_para_test_list.remove("RMII_LINKUP")
                        if ("UART_LPBACK") in nic_mtp_para_test_list:
                            nic_mtp_para_test_list.remove("UART_LPBACK")

                        fstl = list()
                        if nic_list:
                            mtp_para_fail_list, fstl = naples_exec_mtp_para_test(mtp_mgmt_ctrl,
                                                                           nic_type,
                                                                           nic_list,
                                                                           nic_mtp_para_test_list,
                                                                           vmarg,
                                                                           stop_on_err,
                                                                           swmtestmode,
                                                                           args.skip_test)
                            for slot in mtp_para_fail_list:
                                if slot in nic_list and stop_on_err:
                                    nic_list.remove(slot)
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)

                        # copy logfiles out
                        if nic_list and not stop_on_err:

                            # include failed slots
                            for slot in nic_list:
                                mtp_mgmt_ctrl.mtp_hide_nic_status(slot)

                            if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, vmargin=vmarg, nic_util=False, stop_on_err=stop_on_err):
                                for nic_list in nic_test_full_list:
                                    for slot in nic_list:
                                        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                            if slot in nic_list and stop_on_err:
                                                nic_list.remove(slot)
                                                mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                                                return
                                            if slot not in fail_nic_list:
                                                fail_nic_list.append(slot)
                                            if slot in pass_nic_list:
                                                pass_nic_list.remove(slot)
                            naples_get_nic_logfile(mtp_mgmt_ctrl, nic_list, stage, "ASIC_LOG_SAVE", nic_mtp_para_test_list, stop_on_err)
                            parse_nic_test_logfile(mtp_mgmt_ctrl, fstl, vmarg)

                            for slot in nic_list:
                                mtp_mgmt_ctrl.mtp_unhide_nic_status(slot)

                elif test_section == "ARM_PRBS":
                    ######################################################################
                    #
                    #  NIC Parallel PRBS tests with HAL/AAPL for Capri
                    #
                    ######################################################################
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        if nic_type == NIC_Type.NAPLES25SWM:
                            if swmtestmode == Swm_Test_Mode.ALOM:
                                continue

                        nic_para_test_list = para_test_list[nic_type][:]
                        nic_test_db = test_db[nic_type]

                        if nic_list:
                            # aapl tests
                            new_nic_para_test_list = list()
                            if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
                                # no elba tests here
                                pass
                            else:
                                if ("NIC_ASIC","PCIE_PRBS") in nic_para_test_list:
                                    new_nic_para_test_list.append(("NIC_ASIC","PCIE_PRBS"))
                                if ("NIC_ASIC","ETH_PRBS") in nic_para_test_list:
                                    new_nic_para_test_list.append(("NIC_ASIC","ETH_PRBS"))
                            nic_para_test_list = new_nic_para_test_list[:]

                            if len(nic_para_test_list) > 0:
                                diag_para_fail_list = naples_diag_para_test(mtp_mgmt_ctrl,
                                                                            nic_type,
                                                                            nic_list,
                                                                            nic_test_db,
                                                                            nic_para_test_list,
                                                                            stop_on_err,
                                                                            vmarg,
                                                                            True,
                                                                            swmtestmode,
                                                                            args.skip_test,
                                                                            stage)
                                for slot in diag_para_fail_list:
                                    if slot in nic_list and stop_on_err:
                                        nic_list.remove(slot)
                                    if slot not in fail_nic_list:
                                        fail_nic_list.append(slot)
                                    if slot in pass_nic_list:
                                        pass_nic_list.remove(slot)

                elif test_section == "ARM_DSP":
                    ######################################################################
                    #
                    #  NIC Parallel DSP tests (no HAL / no AAPL)
                    #
                    ######################################################################
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        if nic_type == NIC_Type.NAPLES25SWM:
                            if swmtestmode == Swm_Test_Mode.ALOM:
                                continue

                        nic_para_test_list = para_test_list[nic_type][:]
                        nic_test_db = test_db[nic_type]

                        if nic_list:
                            # skip tests done in other loops
                            if ("NIC_ASIC","PCIE_PRBS") in nic_para_test_list:
                                nic_para_test_list.remove(("NIC_ASIC","PCIE_PRBS"))
                            if ("NIC_ASIC","ETH_PRBS") in nic_para_test_list:
                                nic_para_test_list.remove(("NIC_ASIC","ETH_PRBS"))
                            if ("NIC_ASIC","L1") in nic_para_test_list:
                                nic_para_test_list.remove(("NIC_ASIC","L1"))
                            if ("MEM", "EDMA") in nic_para_test_list:
                                nic_para_test_list.remove(("MEM", "EDMA"))

                            # Remove QSFP loopbacks in chamber
                            if vmarg != Voltage_Margin.normal and stage != FF_Stage.QA and (nic_type in ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST):
                                if ("QSFP","I2C") in nic_para_test_list:
                                    nic_para_test_list.remove(("QSFP","I2C"))

                            diag_para_fail_list = naples_diag_para_test(mtp_mgmt_ctrl,
                                                                        nic_type,
                                                                        nic_list,
                                                                        nic_test_db,
                                                                        nic_para_test_list,
                                                                        stop_on_err,
                                                                        vmarg,
                                                                        False,
                                                                        swmtestmode,
                                                                        args.skip_test,
                                                                        stage)
                            for slot in diag_para_fail_list:
                                if slot in nic_list and stop_on_err:
                                    nic_list.remove(slot)
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)

                elif test_section == "EDMA":
                    ######################################################################
                    #
                    #  EDMA test
                    #
                    ######################################################################
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
                            continue

                        nic_para_test_list = para_test_list[nic_type][:]
                        nic_test_db = test_db[nic_type]

                        if nic_list:
                            # skip all tests except edma in this loop
                            new_nic_para_test_list = list()
                            if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
                                if ("MEM", "EDMA") in nic_para_test_list:
                                    for loop in range(1,10+1):   # 10 iterations
                                        new_nic_para_test_list.append(("MEM", "EDMA"))
                            nic_para_test_list = new_nic_para_test_list[:]

                            if len(nic_para_test_list) > 0:
                                diag_para_fail_list = naples_diag_para_test(mtp_mgmt_ctrl,
                                                                            nic_type,
                                                                            nic_list,
                                                                            nic_test_db,
                                                                            nic_para_test_list,
                                                                            stop_on_err,
                                                                            vmarg,
                                                                            True,
                                                                            swmtestmode,
                                                                            args.skip_test,
                                                                            stage)
                                for slot in diag_para_fail_list:
                                    if slot in nic_list and stop_on_err:
                                        nic_list.remove(slot)
                                    if slot not in fail_nic_list:
                                        fail_nic_list.append(slot)
                                    if slot in pass_nic_list:
                                        pass_nic_list.remove(slot)

                elif test_section == "J2C_SEQ":
                    ######################################################################
                    #
                    #  NIC sequential test
                    #
                    ######################################################################
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        if nic_type == NIC_Type.NAPLES25SWM:
                            if swmtestmode == Swm_Test_Mode.ALOM:
                                continue

                        nic_seq_test_list = seq_test_list[nic_type]
                        nic_test_db = test_db[nic_type]

                        if nic_list:
                            diag_seq_fail_list = naples_diag_seq_test(mtp_mgmt_ctrl,
                                                                      nic_type,
                                                                      nic_list,
                                                                      nic_test_db,
                                                                      nic_seq_test_list,
                                                                      vmarg,
                                                                      stop_on_err,
                                                                      swmtestmode,
                                                                      l1_sequence,
                                                                      args.skip_test)
                            for slot in diag_seq_fail_list:
                                if slot in nic_list and stop_on_err:
                                    nic_list.remove(slot)
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)

                elif test_section == "ALOM_LP_MODE":
                    ######################################################################
                    #
                    #  NAPLES25 SWM LOW POWER BOOT MODE TEST
                    #
                    ######################################################################
                    alom_fail_list = list()
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        if nic_type != NIC_Type.NAPLES25SWM:
                            continue
                        if mtp_mgmt_ctrl.mtp_get_swmtestmode(slot) not in (Swm_Test_Mode.SWMALOM, Swm_Test_Mode.ALOM):
                            continue
                        if nic_list:
                            for slot in nic_list:
                                test = "SWM_LP_MODE"
                                dsp = stage
                                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                                start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                                swm_lp_ret = mtp_mgmt_ctrl.mtp_nic_naples25swm_low_power_mode_test(slot)
                                duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                                if not swm_lp_ret:
                                    mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                                    alom_fail_list.append(slot)
                                    mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                                else:
                                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

                            for slot in alom_fail_list:
                                if slot in nic_list and stop_on_err:
                                    nic_list.remove(slot)
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)

                            # only do this diag init if swm lp_mode test was performed
                            mtp_mgmt_ctrl.cli_log_inf("Setting Naples25 SWM Back to High Power Mode (requires a nic reboot)", level=0)
                            if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, vmargin=vmarg, swm_lp=False,stop_on_err=stop_on_err):
                                #mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                                for slot in nic_list:
                                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                        if slot not in fail_nic_list:
                                            fail_nic_list.append(slot)
                                        if slot in pass_nic_list:
                                            pass_nic_list.remove(slot)
                                        if stop_on_err:
                                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                                            return

                elif test_section == "NIC_DIAG_INIT":
                    ######################################################################
                    #
                    #  NIC Setup
                    #
                    ######################################################################
                    if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_test_full_list, vmargin=vmarg, nic_util=False, dis_hal=True, stop_on_err=stop_on_err):
                        #mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                        for nic_list in nic_test_full_list:
                            for slot in nic_list:
                                if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                    if slot not in fail_nic_list:
                                        fail_nic_list.append(slot)
                                    if slot in pass_nic_list:
                                        pass_nic_list.remove(slot)
                                    if stop_on_err:
                                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                                        return

                elif test_section == "NIC_DIAG_INIT_AAPL":
                    ######################################################################
                    #
                    #  NIC Parallel PRBS tests setup for Capri
                    #
                    ######################################################################
                    if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_test_full_list, vmargin=vmarg, aapl=True, nic_util=False, dis_hal=True, stop_on_err=stop_on_err):
                        #mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                        for nic_list in nic_test_full_list:
                            for slot in nic_list:
                                if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                    if slot not in fail_nic_list:
                                        fail_nic_list.append(slot)
                                    if slot in pass_nic_list:
                                        pass_nic_list.remove(slot)
                                    if stop_on_err:
                                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                                        return
                                        
                elif test_section == "NIC_EDMA_ENV_INIT":
                    ######################################################################
                    #
                    #  NIC EDMA Environment Setup
                    #
                    ######################################################################
                    if not mtp_mgmt_ctrl.mtp_nic_edma_env_init(nic_test_full_list):
                        for nic_list in nic_test_full_list:
                            for slot in nic_list:
                                if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                    if slot not in fail_nic_list:
                                        fail_nic_list.append(slot)
                                    if slot in pass_nic_list:
                                        pass_nic_list.remove(slot)


                elif test_section == "TEST_FPGA_PROG":
                    ######################################################################
                    #
                    #  Program NC-SI specific FPGA image
                    #
                    ######################################################################
                    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
                    nic_thread_list = list()
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        for slot in nic_list:
                            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                continue

                            nic_thread = threading.Thread(target = single_nic_test_fpga_program, args = (mtp_mgmt_ctrl,
                                                                                                  slot,
                                                                                                  args.skip_test,
                                                                                                  nic_test_rslt_list,
                                                                                                  dsp))
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

                elif test_section == "PROD_FPGA_PROG":
                    ######################################################################
                    #
                    #  Program production FPGA image
                    #
                    ######################################################################
                    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
                    nic_thread_list = list()
                    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                        for slot in nic_list:
                            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                continue

                            nic_thread = threading.Thread(target = single_nic_prod_fpga_program, args = (mtp_mgmt_ctrl,
                                                                                                  slot,
                                                                                                  args.skip_test,
                                                                                                  nic_test_rslt_list,
                                                                                                  dsp))
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

                # check MTP PSU PIN after each test stage
                mtp_mgmt_ctrl.cli_log_inf("Check MTP PSU PIN After Test Stage", level=0)
                if not mtp_mgmt_ctrl.mtp_psu_init():
                    # Fail all cards
                    mtp_mgmt_ctrl.cli_log_err("PSU PIN Check Failed, Fail All Card Out", level=0)
                    for nic_list in nic_test_full_list:
                        for slot in nic_list:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)
                    break
                # check MTP HOST NIC Device after each test stage
                mtp_mgmt_ctrl.cli_log_inf("Check MTP HOST NIC Device After Test Stage", level=0)
                if not libmtp_utils.check_mtp_host_nic_presence(mtp_mgmt_ctrl):
                    # Fail all cards
                    mtp_mgmt_ctrl.cli_log_err("MTP HOST NIC Device Check Failed, Fail All Card Out", level=0)
                    for nic_list in nic_test_full_list:
                        for slot in nic_list:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)
                    break
                # check MTP FAN SPEED after each test stage
                mtp_mgmt_ctrl.cli_log_inf("Check MTP Fan Speed After Test Stage", level=0)
                if not mtp_mgmt_ctrl.mtp_inlet_temp_test():
                    # Fail all cards
                    mtp_mgmt_ctrl.cli_log_err("MTP Fan Speed Check Failed, Fail All Card Out", level=0)
                    for nic_list in nic_test_full_list:
                        for slot in nic_list:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)
                    break

            # log the diag test history
            mtp_mgmt_ctrl.mtp_mgmt_diag_history_disp()

            # clear the diag test history
            if not stop_on_err:
                mtp_mgmt_ctrl.mtp_mgmt_diag_history_clear()

            testlog.gather_dsp_logs(mtp_mgmt_ctrl, vmarg)

            # clean up logfiles for the next run
            cmd = "cleanup.sh"
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)


        # Enable PCIe poll
        #ADD - Bypass shutting down slot right now for debug
        print("STOP ON ERR=" + str(stop_on_err))
        if not stop_on_err:
            if mtp_mgmt_ctrl.mtp_get_asic_support() == MTP_ASIC_SUPPORT.CAPRI:
                mtp_mgmt_ctrl.mtp_power_cycle_nic(slot_list=pass_nic_list, dl=False)
                mtp_mgmt_ctrl.cli_log_inf("Wait {:02d} seconds for NIC power up before enable PCIE poll".format(MTP_Const.MTP_PCIE_EN_DIS_DELAY), level=0)
                libmfg_utils.count_down(MTP_Const.MTP_PCIE_EN_DIS_DELAY)
                diag_post_fail_list = mtp_nic_diag_init_post(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, args.skip_test, stage)
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
                mtp_mgmt_ctrl.cli_log_err("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

        for slot in skip_nic_list:
            key = libmfg_utils.nic_key(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s}".format(key, MTP_DIAG_Report.NIC_DIAG_REGRESSION_SKIP), level=0)

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        # err_msg = str(e)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)

    mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_PASS, open_file_track_list)


if __name__ == "__main__":
    main()
