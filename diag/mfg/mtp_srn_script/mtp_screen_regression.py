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
import json

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
import testlog
from libdefs import MTP_Const
from libdefs import NIC_Type
from libdefs import MTP_ASIC_SUPPORT
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import Swm_Test_Mode
from libdefs import MFG_DIAG_CMDS
from libdefs import MFG_DIAG_SIG
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Path
from libdefs import Voltage_Margin
from libdiag_db import diag_db
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import GIGLIO_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST



# test cleanup.
def mtp_test_cleanup(error_code, fp_list=None):
    # if fp_list:
    #     for fp in fp_list:
    #         fp.close()
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

    if card_type in ELBA_NIC_TYPE_LIST or card_type in GIGLIO_NIC_TYPE_LIST:
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
    elif nic_type == NIC_Type.POMONTEDELL:
        mode = "nod"
    elif nic_type == NIC_Type.LACONA32DELL or nic_type == NIC_Type.LACONA32:
        mode = "nod_550"
    else:
        mode = ""

    return mode

def mtp_nic_poll_set(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, skip_testlist, testlist):
    fail_nic_list = list()

    for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
        for slot in nic_list:
            if not mtp_mgmt_ctrl._nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                continue
            # if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            #     continue
            dsp = "BOOT"
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
                    fail_nic_list.append(slot)
                    mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                    break
                else:
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
    return fail_nic_list

def mtp_nic_diag_init_pre(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, skip_testlist):
    """
    setup for regression test
    """
    mtp_mgmt_ctrl.cli_log_inf("NIC Diag Setup started", level = 0)
    fail_nic_list = mtp_nic_poll_set(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, skip_testlist, testlist=["PCIE_POLL_DISABLE"])
    mtp_mgmt_ctrl.cli_log_inf("NIC Diag Setup complete\n", level = 0)
    return fail_nic_list

def mtp_nic_diag_init_post(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, skip_testlist):
    """
    cleanup after regression test
    """
    mtp_mgmt_ctrl.cli_log_inf("NIC Diag Cleanup started", level = 0)
    fail_nic_list = mtp_nic_poll_set(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, skip_testlist, testlist=["PCIE_POLL_ENABLE"])
    mtp_mgmt_ctrl.cli_log_inf("NIC Diag Cleanup complete\n", level = 0)
    return fail_nic_list

def naples_exec_pre_check(mtp_mgmt_ctrl, nic_type, nic_list, nic_check_list, vmarg, swmtestmode, skip_testlist):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Pre Check Start".format(nic_type), level=0)
    nic_test_list = nic_list[:]
    fail_list = list()
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
                mtp_mgmt_ctrl.mtp_mgmt_nic_diag_sys_clean(slot)
            
    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Pre Check Complete\n".format(nic_type), level=0)

    return fail_list


def naples_diag_para_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, test_list, stop_on_err, vmarg, aapl, swmtestmode, skip_testlist):
    if aapl == False:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel DSP Test Start".format(nic_type), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel PRBS Test Start".format(nic_type), level=0)

    sub_test_list = test_list[:]

    if aapl:
        if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            sub_test_list = [("NIC_ASIC","PCIE_PRBS"), ("NIC_ASIC","ETH_PRBS"), ("NIC_ASIC","L1")]
        else:
            sub_test_list = [("NIC_ASIC","PCIE_PRBS")]
    else:
        if ("NIC_ASIC","PCIE_PRBS") in sub_test_list:
            sub_test_list.remove(("NIC_ASIC","PCIE_PRBS"))
        if ("NIC_ASIC","ETH_PRBS") in sub_test_list:
            sub_test_list.remove(("NIC_ASIC","ETH_PRBS"))
        if ("NIC_ASIC","L1") in sub_test_list:
            sub_test_list.remove(("NIC_ASIC","L1"))

    # Remove QSFP loopbacks in chamber
    if vmarg != Voltage_Margin.normal and nic_type == NIC_Type.ORTANO2:
        if ("QSFP","I2C") in sub_test_list:
            sub_test_list.remove(("QSFP","I2C"))

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
    fail_save_list = mtp_mgmt_ctrl.mtp_mgmt_save_nic_diag_logfile(nic_list, FF_Stage.FF_SRN, "NIC_LOG_SAVE", aapl)
    for slot in fail_save_list:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Collecting NIC onboard diag logfile failed")
        if slot not in fail_list:
            fail_list.append(slot)

    if aapl == False:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel DSP Test Complete\n".format(nic_type), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel PRBS Test Complete\n".format(nic_type), level=0)

    return fail_list


def avs_set_para_test(mtp_mgmt_ctrl, nic_type, nic_list):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} AVS SET Test Start".format(nic_type), level=0)
    fail_list = list()

    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    for slot in nic_list:
        nic_thread = threading.Thread(target = single_avs_set_para_regression,
                                      args = (mtp_mgmt_ctrl,
                                              slot,
                                              nic_test_rslt_list))
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

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} AVS SET Test Complete\n".format(nic_type), level=0)

    return fail_list


def single_avs_set_para_regression(mtp_mgmt_ctrl, slot, nic_test_rslt_list):
    dsp = "MTP_SCREEN"
    test = "AVS_SET"
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)


    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)

    ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_avs(slot)

    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
    if not ret:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
        nic_test_rslt_list[slot] = False
        # mtp_mgmt_ctrl.mtp_dump_err_msg(mtp_mgmt_ctrl.mtp_get_nic_err_msg(slot))
        mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


def naples_exec_mtp_para_test(mtp_mgmt_ctrl, nic_type, nic_list, para_test_list, vmarg, stop_on_err, swmtestmode, skip_testlist):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Start".format(nic_type), level=0)

    for skipped_test in skip_testlist:
        if skipped_test in para_test_list:
            para_test_list.remove(skipped_test)

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
        fail_slot_test_list = list()
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
            ret, test_fail_list = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(test, nic_test_list, vmarg)
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)

            # failed nic display
            for slot in test_fail_list:
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, dsp, test, "FAILED", duration))
                mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
                if not stop_on_err:
                    mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, test, ret, mtp_mgmt_ctrl.mtp_get_cmd_buf(), [])
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
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
            raise Exception
        else:
            naples_get_nic_logfile(mtp_mgmt_ctrl, nic_test_list, para_test_list, stop_on_err)
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
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            nic_test_rslt_list[slot] = False
            continue
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
            mtp_mgmt_ctrl.mtp_nic_console_lock()

        # quick hack for parameter ETH_PRBS. need to move into yaml config
        if dsp == "NIC_ASIC" and test == "ETH_PRBS" and card_type == NIC_Type.ORTANO2:
            # external loopback for P2C
            if vmarg == Voltage_Margin.normal:
                diag_cmd += " -p 'int_lpbk=0'"
            # internal loopback for 2C/4C
            else:
                diag_cmd += " -p 'int_lpbk=1'"

        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        ret, err_msg_list = mtp_mgmt_ctrl.mtp_run_diag_test_para(slot, diag_cmd, rslt_cmd, test, init_cmd, post_cmd)
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)

        # Collect NIC onboard logfiles
        asic_dir_logfile_list = []
        path = MTP_DIAG_Logfile.NIC_ONBOARD_ASIC_LOG_DIR
        if dsp == "NIC_ASIC" and test == "PCIE_PRBS":
            asic_dir_logfile_list.append(path+"elba_PRBS_PCIE.log")
        if dsp == "NIC_ASIC" and test == "ETH_PRBS":
            asic_dir_logfile_list.append(path+"elba_PRBS_MX.log")
        if dsp == "NIC_ASIC" and test == "L1":
            asic_dir_logfile_list.append(path+"elba_arm_l1_test.log")

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
            mtp_mgmt_ctrl.mtp_nic_console_unlock()

        if ret != "SUCCESS" and stop_on_err:
            break

def naples_get_nic_logfile(mtp_mgmt_ctrl, nic_list, mtp_para_test_list, stop_on_err):
    mtp_mgmt_ctrl.mtp_nic_mgmt_para_init(False, stop_on_err=stop_on_err)

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


def sanity_check(mtp_cfg_db, mtp_id, mtp_mgmt_ctrl):
    # find any slots to skip
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl._slots_to_skip = mtp_slots_to_skip

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    libmfg_utils.cli_log_rslt("Begin Sanity Check .. Please monitor until complete", [], [], mtp_mgmt_ctrl._filep)

    mtp_thread_list = list()
    setup_rslt_list = dict()

    # mtp_setup(mtp_mgmt_ctrl, mtp_capability, setup_rslt_list)

    if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")

    fail_nic_list = libmfg_utils.loopback_sanity_check([mtp_id], [mtp_mgmt_ctrl])

    # if all slots in an MTP fail, assert stop on failure here
    if len(fail_nic_list[mtp_id]) == mtp_mgmt_ctrl._slots:
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP completely failed Sanity Check. Test abort..")

    # close NIC ssh sessions
    mtp_mgmt_ctrl.mtp_nic_para_session_end()

    return fail_nic_list


def main():
    parser = argparse.ArgumentParser(description="Single MTP Screen Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--stop-on-error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--stage", "--corner", type=FF_Stage, help="diagnostic environment condition", choices=list(FF_Stage), default=FF_Stage.FF_SRN)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--fail-slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("--skip-slots", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--mtpsn", help="MTP SN, like FLM0021330001, etc", required=True)
    parser.add_argument("--l1-seq", help="asic L1 run under sequence mode", action='store_true')
    args = parser.parse_args()

    mtp_id = "MTP-000"
    mtp_sn = ""
    stop_on_err = False
    verbosity = False
    swm_lp_boot_mode = False
    l1_sequence = False
    if args.mtpid:
        mtp_id = args.mtpid
        mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    if args.stop_on_error:
        stop_on_err = True
    if args.verbosity:
        verbosity = True
    if args.stage:
        stage = args.stage
    if args.swm:
        swmtestmode = args.swm
        print(" SWMTESTMODE=" + str(swmtestmode))
    if args.mtpsn:
        mtp_sn = args.mtpsn
    if args.l1_seq:
        l1_sequence = True

    fail_step = ""
    fail_desc = ""

    low_temp_threshold, high_temp_threshold = libmfg_utils.pick_temperature_thresholds(stage)
    fanspd = libmfg_utils.pick_fan_speed(stage)
    vmarg_list = libmfg_utils.pick_voltage_margin(stage)

    # load the mtp config
    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/mtp_screen_chassis_cfg.yaml"))
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
    naples100_test_cfg_file = "config/naples100_mtp_test_cfg.yaml"
    naples100ibm_test_cfg_file = "config/naples100ibm_mtp_test_cfg.yaml"
    naples100hpe_test_cfg_file = "config/naples100hpe_mtp_test_cfg.yaml"
    naples100dell_test_cfg_file = "config/naples100dell_mtp_test_cfg.yaml"
    naples25_test_cfg_file = "config/naples25_mtp_test_cfg.yaml"
    forio_test_cfg_file = "config/forio_mtp_test_cfg.yaml"
    vomero_test_cfg_file = "config/vomero_mtp_test_cfg.yaml"
    vomero2_test_cfg_file = "config/vomero2_mtp_test_cfg.yaml"
    naples25swm_test_cfg_file = "config/naples25swm_mtp_test_cfg.yaml"
    naples25ocp_test_cfg_file = "config/naples25ocp_mtp_test_cfg.yaml"
    naples25swmdell_test_cfg_file = "config/naples25swmdell_mtp_test_cfg.yaml"
    naples25swm833_test_cfg_file = "config/naples25swm833_mtp_test_cfg.yaml"
    ortano_test_cfg_file = "config/ortano_mtp_test_cfg.yaml"
    pomontedell_test_cfg_file = "config/pomontedell_mtp_test_cfg.yaml"
    lacona32dell_test_cfg_file = "config/lacona32dell_mtp_test_cfg.yaml"
    lacona32_test_cfg_file = "config/lacona32_mtp_test_cfg.yaml"
    mtp_screen_test_cfg_file = "config/mtp_screen_test_cfg.yaml"
    
    naples100_test_db = diag_db(stage, naples100_test_cfg_file)
    naples100ibm_test_db = diag_db(stage, naples100ibm_test_cfg_file)
    naples100hpe_test_db = diag_db(stage, naples100hpe_test_cfg_file)
    naples100dell_test_db = diag_db(stage, naples100dell_test_cfg_file)
    naples25_test_db = diag_db(stage, naples25_test_cfg_file)
    forio_test_db = diag_db(stage, forio_test_cfg_file)
    vomero_test_db = diag_db(stage, vomero_test_cfg_file)
    vomero2_test_db = diag_db(stage, vomero2_test_cfg_file)
    naples25swm_test_db = diag_db(stage, naples25swm_test_cfg_file)
    naples25ocp_test_db = diag_db(stage, naples25ocp_test_cfg_file)
    naples25swmdell_test_db = diag_db(stage, naples25swmdell_test_cfg_file)
    naples25swm833_test_db = diag_db(stage, naples25swm833_test_cfg_file)
    ortano_test_db = diag_db(stage, ortano_test_cfg_file)
    pomontedell_test_db = diag_db(stage, pomontedell_test_cfg_file)
    lacona32dell_test_db = diag_db(stage, lacona32dell_test_cfg_file)
    lacona32_test_db = diag_db(stage, lacona32_test_cfg_file)
    mtp_screen_test_db = diag_db(stage, mtp_screen_test_cfg_file)

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

    naples100dell_seq_test_list = naples100dell_test_db.get_diag_seq_test_list()
    naples100dell_mtp_para_test_list = naples100dell_test_db.get_mtp_para_test_list()
    naples100dell_para_test_list = naples100dell_test_db.get_diag_para_test_list()
    naples100dell_pre_test_check_list = naples100dell_test_db.get_pre_diag_test_intf_list()
    naples100dell_post_test_check_list = naples100dell_test_db.get_post_diag_test_intf_list()

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

    pomontedell_seq_test_list = pomontedell_test_db.get_diag_seq_test_list()
    pomontedell_mtp_para_test_list = pomontedell_test_db.get_mtp_para_test_list()
    pomontedell_para_test_list = pomontedell_test_db.get_diag_para_test_list()
    pomontedell_pre_test_check_list = pomontedell_test_db.get_pre_diag_test_intf_list()
    pomontedell_post_test_check_list = pomontedell_test_db.get_post_diag_test_intf_list()

    lacona32dell_seq_test_list = lacona32dell_test_db.get_diag_seq_test_list()
    lacona32dell_mtp_para_test_list = lacona32dell_test_db.get_mtp_para_test_list()
    lacona32dell_para_test_list = lacona32dell_test_db.get_diag_para_test_list()
    lacona32dell_pre_test_check_list = lacona32dell_test_db.get_pre_diag_test_intf_list()
    lacona32dell_post_test_check_list = lacona32dell_test_db.get_post_diag_test_intf_list()

    lacona32_seq_test_list = lacona32_test_db.get_diag_seq_test_list()
    lacona32_mtp_para_test_list = lacona32_test_db.get_mtp_para_test_list()
    lacona32_para_test_list = lacona32_test_db.get_diag_para_test_list()
    lacona32_pre_test_check_list = lacona32_test_db.get_pre_diag_test_intf_list()
    lacona32_post_test_check_list = lacona32_test_db.get_post_diag_test_intf_list()

    mtp_screen_seq_test_list = mtp_screen_test_db.get_diag_seq_test_list()
    mtp_screen_mtp_para_test_list = mtp_screen_test_db.get_mtp_para_test_list()
    mtp_screen_para_test_list = mtp_screen_test_db.get_diag_para_test_list()
    mtp_screen_pre_test_check_list = mtp_screen_test_db.get_pre_diag_test_intf_list()
    mtp_screen_post_test_check_list = mtp_screen_test_db.get_post_diag_test_intf_list()

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
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True)


    try:

        naples100_nic_list = list()
        naples100ibm_nic_list = list()
        naples100hpe_nic_list = list()
        naples100dell_nic_list = list()
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
        pomontedell_nic_list = list()
        lacona32dell_nic_list = list()
        lacona32_nic_list = list()
        mtp_screen_nic_list = list()
        pass_nic_list = list()
        fail_nic_list = list()
        skip_nic_list = list()
        rs = True
        mac = ""

        # for slot in range(10):
        #     pass_nic_list.append(slot) 

        #MTP connect
        if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="SRN-SSH", retry_with_powercycle=True):
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis. Abort test", level=0)
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            fail_step = "connect MTP failed"
            fail_desc = "Unable to connect MTP Chassis. Abort test"
            for slot in range(10):
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot) 
            return False
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

        if rs:
            if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, stage=stage):
                mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
                libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
                fail_step = "MTP common setup failed"
                fail_desc = "MTP common setup fails"
                for slot in range(10):
                    fail_nic_list.append(slot)
                    pass_nic_list.remove(slot) 
                rs = False
            else:
                mtp_mgmt_ctrl.cli_log_inf("MTP common setup passed", level=0)

        #get MTP MAC AA:BB:CC:DD:EE:FF
        if rs:
            # mac = mtp_mgmt_ctrl.mtp_get_mac()
            # if mac.startswith("[FAIL]:"):
            #     mtp_mgmt_ctrl.mtp_diag_fail_report("Failed to retrieve MTP MAC Address")
            #     libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            #     mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
            #     fail_step = "Unable to get MTP MAC Address"
            #     fail_desc = "Unable to get MTP MAC Address"
            #     for slot in range(10):
            #         fail_nic_list.append(slot)
            #         pass_nic_list.remove(slot) 
            #     rs = False
            # else:
            #     mtp_mgmt_ctrl.cli_log_inf("Retrieve MTP Mac Address passed", level=0)


            mac_dict = {
                        "FLM21330006" : "BBBBBBBBBBAF",
                        "FLM21330004" : "BBBBBBBBBBAE",
                        "FLM21330005" : "BBBBBBBBBBA8",
                        "FLM2133000B" : "BBBBBBBBBBA0",
                        "FLM21330001" : "BBBBBBBBBBA1",
                        "FLM21330013" : "BBBBBBBBBBA2",
                        "FLM21330002" : "BBBBBBBBBBA7",
                        "FLM2133000F" : "BBBBBBBBBBAD",
                        "FLM21330008" : "BBBBBBBBBBAC",
                        "FLM2133000D" : "BBBBBBBBBBA4",
                        "FLM21330009" : "BBBBBBBBBBA5",
                        "FLM21330003" : "BBBBBBBBBBA6",
                        "FLM21330011" : "BBBBBBBBBBA9",
                        "FLM21330012" : "BBBBBBBBBBAA",
                        "FLM2133000E" : "BBBBBBBBBBAF",
                        "FLM2133000C" : "BBBBBBBBBBAB",
                        "FLM21400023" : "BBBBBBBBBBB0",
                        "FLM2140001F" : "BBBBBBBBBBB1",
                        "FLM21400018" : "BBBBBBBBBBB2",
                        "FLM2140002D" : "BBBBBBBBBBB3",
                        "FLM2140002A" : "BBBBBBBBBBB4",
                        "FLM21400008" : "BBBBBBBBBBB5",
                        "FLM2140000D" : "BBBBBBBBBBB6",
                        "FLM21400004" : "BBBBBBBBBBB7",
                        "FLM2140001C" : "BBBBBBBBBBB8",
                        "FLM2140000E" : "BBBBBBBBBBB9",
                        "FLM2140000C" : "BBBBBBBBBBBA",
                        "FLM21400002" : "BBBBBBBBBBBB",
                        "FLM21400007" : "BBBBBBBBBBBC",
                        "FLM21400005" : "BBBBBBBBBBBD",
                        "FLM21400024" : "BBBBBBBBBBBE",
                        "FLM21400010" : "BBBBBBBBBBBF",
                        "FLM21400021" : "BBBBBBBBBBC0",
                        "FLM21400015" : "BBBBBBBBBBC1",
                        "FLM21400006" : "BBBBBBBBBBC2",
                        "FLM21400012" : "BBBBBBBBBBC3",
                        "FLM21400001" : "BBBBBBBBBBC4",
                        "FLM2140002C" : "BBBBBBBBBBC5",
                        "FLM2140002F" : "BBBBBBBBBBC6",
                        "FLM2140001E" : "BBBBBBBBBBC7",
                        "FLM2140000A" : "BBBBBBBBBBC8",
                        "FLM2140000B" : "BBBBBBBBBBC9",
                        "FLM21400025" : "BBBBBBBBBBCA",
                        "FLM21400028" : "BBBBBBBBBBCB",
                        "FLM21400029" : "BBBBBBBBBBCC",
                        "FLM2140001A" : "BBBBBBBBBBCD",
                        "FLM21400009" : "BBBBBBBBBBCE",
                        "FLM21400003" : "BBBBBBBBBBCF",
                        "FLM2140001D" : "BBBBBBBBBBD0",
                        "FLM21400032" : "BBBBBBBBBBD1",
                        "FLM21400027" : "BBBBBBBBBBD2",
                        "FLM21400031" : "BBBBBBBBBBD3",
                        "FLM21400026" : "BBBBBBBBBBD4",
                        "FLM21400011" : "BBBBBBBBBBD5",
                        "FLM2140002B" : "BBBBBBBBBBD6",
                        "FLM21400017" : "BBBBBBBBBBD7",
                        "FLM21400016" : "BBBBBBBBBBD8",
                        "FLM21400014" : "BBBBBBBBBBD9",
                        "FLM2140000F" : "BBBBBBBBBBDA",
                        "FLM21400020" : "BBBBBBBBBBDB",
                        "FLM2140002E" : "BBBBBBBBBBDC",
                        "FLM2140001B" : "BBBBBBBBBBDD",
                        "FLM21400019" : "BBBBBBBBBBDE",
                        "FLM21400013" : "BBBBBBBBBBDF"
                        }
            if mtp_sn not in mac_dict:
                mtp_mgmt_ctrl.mtp_diag_fail_report("Failed to retrieve MTP MAC Address")
                libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
                fail_step = "Unable to get MTP MAC Address"
                fail_desc = "Unable to get MTP MAC Address"
                for slot in range(10):
                    fail_nic_list.append(slot)
                    pass_nic_list.remove(slot) 
                rs = False
            else:
                mac = mac_dict[mtp_sn].strip()
                mtp_mgmt_ctrl.cli_log_inf("Retrieve MTP Mac Address passed", level=0)


        mac = mac.upper().replace(':','')

        #program FRU
        if rs:
            cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

            if not mtp_mgmt_ctrl.mtp_set_sn_rev_mac_command(sn=mtp_sn, maj="04", mac=mac):
                mtp_mgmt_ctrl.cli_log_err("MTP program FRU command failed", level=0)
                libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
                fail_step = "MTP program FRU failed"
                fail_desc = "MTP program FRU fails"
                for slot in range(10):
                    fail_nic_list.append(slot)
                    pass_nic_list.remove(slot) 
                rs = False
            else:
                mtp_mgmt_ctrl.cli_log_inf("MTP program FRU command passed", level=0)


        # Set Naples25SWM test mode
        mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)

        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if nic_prsnt_list[slot]:
                pass_nic_list.append(slot)

        if rs:
            if len(nic_prsnt_list) != 10:
                mtp_mgmt_ctrl.mtp_diag_fail_report("Not able to detect 10 NICs")
                libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
                miss_slot_list = ""
                for slot in range(len(nic_prsnt_list)):
                    if not nic_prsnt_list[slot]:
                        fail_nic_list.append(slot)
                        pass_nic_list.remove(slot)
                        if len(miss_slot_list) > 0: 
                            miss_slot_list += "," + str(slot + 1)
                        else:
                            miss_slot_list = str(slot + 1)
                fail_step = "MTP not able to detect 10 NICs. --> (missing slots: " + miss_slot_list + ")"
                fail_desc = "MTP not able to detect 10 NICs. --> (missing slots: " + miss_slot_list + ")"
                rs = False
            else:
                mtp_mgmt_ctrl.cli_log_inf("MTP detect 10 NIC passed", level=0)               

        if rs:
            mismatch_slot_list = ""
            for slot in range(len(nic_prsnt_list)):
                if nic_prsnt_list[slot]:
                    mtp_screen_nic_list.append(slot)
                    
                    if not mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.ORTANO2:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Incorrect NIC Type")
                        fail_nic_list.append(slot)
                        pass_nic_list.remove(slot)
                        if len(mismatch_slot_list) > 0: 
                            mismatch_slot_list += "," + str(slot + 1)
                        else:
                            mismatch_slot_list = str(slot + 1)
                        rs = False

            if not rs:
                fail_step = "MTP not able to detect 10 ORTANO2 NICs. --> (slots: " + mismatch_slot_list + ")"
                fail_desc = "MTP not able to detect 10 ORTANO2 NICs. --> (slots: " + mismatch_slot_list + ")"
            else:
                mtp_mgmt_ctrl.cli_log_inf("MTP detect 10 ORTANO2 NIC passed", level=0)   

        # if rs and len(pass_nic_list) != 10:
        #     mtp_mgmt_ctrl.mtp_diag_fail_report("Not able to detect 10 NICs")
        #     libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        #     mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
        #     fail_step = "MTP not able to detect 10 ORTANO2 NICs"
        #     fail_desc = "MTP not able to detect 10 ORTANO2 NICs"
        #     rs = False

        nic_type_full_list = [NIC_Type.NAPLES100, NIC_Type.NAPLES25, NIC_Type.FORIO, NIC_Type.VOMERO, NIC_Type.NAPLES25SWM, NIC_Type.VOMERO2, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL, NIC_Type.NAPLES25OCP, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.ORTANO, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, "MTP_SCREEN"]
        nic_test_full_list = [naples100_nic_list, naples25_nic_list, forio_nic_list, vomero_nic_list, naples25swm_nic_list, vomero2_nic_list, naples100ibm_nic_list, naples100hpe_nic_list, naples100dell_nic_list, naples25ocp_nic_list, naples25swmdell_nic_list, naples25swm833_nic_list, ortano_nic_list, ortano2_nic_list, pomontedell_nic_list, lacona32dell_nic_list, lacona32_nic_list, mtp_screen_nic_list]

        vmarg = Voltage_Margin.normal
        # #power cycle
        if rs:
            nic_para_test_list = mtp_screen_para_test_list[:]
            naples_diag_cfg_show("MTP_SCREEN", mtp_screen_test_db, mtp_mgmt_ctrl)
            naples_exec_init_cmd(mtp_screen_test_db, mtp_mgmt_ctrl)
            naples_exec_skip_cmd(pass_nic_list, mtp_screen_test_db, mtp_mgmt_ctrl)
            naples_exec_param_cmd(pass_nic_list, mtp_screen_test_db, mtp_mgmt_ctrl)

        # Disable PCIe poll
        if rs:
            diag_pre_fail_list = mtp_nic_diag_init_pre(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, args.skip_test)
            if len(diag_pre_fail_list) > 0:
                rs = False
                libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                mtp_mgmt_ctrl.cli_log_err("Fail to diasable PCIe poll", level=0)
                fail_step += "Fail to disable PCIe poll"
                fail_desc += "Fail to disable PCIe poll"
                for slot in range(10):
                    fail_nic_list.append(slot)
                    pass_nic_list.remove(slot)

        if rs:   
            mtp_mgmt_ctrl.mtp_power_cycle_nic()

        if rs:
            pre_test_check_list = mtp_screen_pre_test_check_list[:]
            pre_check_fail_list = naples_exec_pre_check(mtp_mgmt_ctrl,
                                                        "MTP_SCREEN",
                                                        pass_nic_list,
                                                        pre_test_check_list,
                                                        vmarg,
                                                        swmtestmode,
                                                        args.skip_test)
            for slot in pre_check_fail_list:
                rs = False
                if len(fail_step) == 0:
                    fail_step = "Fail to Pre check(slot:" + str(slot + 1) + ")"
                    fail_desc = "Fail to Pre check(slot:" + str(slot + 1) + ")"
                else:
                    fail_step += ", Fail to Pre check(slot:" + str(slot + 1) + ")"
                    fail_desc += ", Fail to Pre check(slot:" + str(slot + 1) + ")"

                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)         

        # NIC test
        if rs and not mtp_mgmt_ctrl.mtp_nic_diag_init(pass_nic_list, vmargin=vmarg, swm_lp=swm_lp_boot_mode, nic_util=True, stop_on_err=stop_on_err):
            mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
            fail_step = "Initialize NIC diag environment failed"
            fail_desc = "Initialize NIC diag environment failed"
            for slot in range(10):
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot) 
            rs = False

        if rs:
            # Parallel Test
            nic_para_test_list = mtp_screen_para_test_list[:]
            diag_para_fail_list = naples_diag_para_test(mtp_mgmt_ctrl,
                                                        "MTP_SCREEN",
                                                        pass_nic_list,
                                                        mtp_screen_test_db,
                                                        nic_para_test_list,
                                                        stop_on_err,
                                                        vmarg,
                                                        True,
                                                        swmtestmode,
                                                        args.skip_test)
            for slot in diag_para_fail_list:
                rs = False
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                if len(fail_step) == 0:
                    fail_step = "Fail to PCIE_PRBS check(slot:" + str(slot + 1) + ")"
                    fail_desc = "Fail to PCIE_PRBS check(slot:" + str(slot + 1) + ")"
                else:
                    fail_step += ", Fail to PCIE_PRBS check(slot:" + str(slot + 1) + ")"
                    fail_desc += ", Fail to PCIE_PRBS check(slot:" + str(slot + 1) + ")"

        if rs:
            nic_seq_test_list = mtp_screen_seq_test_list[:]
            diag_seq_fail_list = naples_diag_seq_test(mtp_mgmt_ctrl,
                                                      "MTP_SCREEN",
                                                      pass_nic_list,
                                                      mtp_screen_test_db,
                                                      nic_seq_test_list,
                                                      vmarg,
                                                      stop_on_err,
                                                      swmtestmode,
                                                      l1_sequence,
                                                      args.skip_test)
            for slot in diag_seq_fail_list:
                rs = False
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                if len(fail_step) == 0:
                    fail_step = "Fail to L1 check(slot:" + str(slot + 1) + ")"
                    fail_desc = "Fail to L1 check(slot:" + str(slot + 1) + ")"
                else:
                    fail_step += ", Fail to L1 check(slot:" + str(slot + 1) + ")"
                    fail_desc += ", Fail to L1 check(slot:" + str(slot + 1) + ")"

        if rs:
            diag_post_fail_list = mtp_nic_diag_init_post(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, args.skip_test)
         
            if len(diag_post_fail_list) > 0:
                libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                rs = False
                mtp_mgmt_ctrl.cli_log_err("Fail to enable PCIe poll", level=0)
                fail_step = "Fail to enable PCIe poll"
                fail_desc = "Fail to enable PCIe poll"
                for slot in range(10):
                    fail_nic_list.append(slot)
                    pass_nic_list.remove(slot) 

        # # AVS_SET
        # if rs:
        #     mtp_mgmt_ctrl.cli_log_inf("AVS_SET test started", level=0)

        #     # avs_set_para_fail_list = avs_set_para_test(mtp_mgmt_ctrl, "MTP_SCREEN", pass_nic_list)

        #     # if len(avs_set_para_fail_list) > 0:
        #     #     rs = False
        #     #     mtp_mgmt_ctrl.cli_log_err("AVS_SET test failed", level=0)
        #     # else:
        #     #     mtp_mgmt_ctrl.cli_log_inf("AVS_SET test passed", level=0)      

        #     for slot in pass_nic_list:
        #         ret = mtp_mgmt_ctrl.mtp_mgmt_set_nic_avs(slot)
        #         if not ret:
        #             mtp_mgmt_ctrl.cli_log_err("AVS_SET test failed", level=0)
        #             mtp_mgmt_ctrl.mtp_set_nic_status_fail(int(slot), skip_fa=True)
        #             fail_nic_list.append(slot)
        #             pass_nic_list.remove(slot)
        #             rs = False

        #     mtp_mgmt_ctrl.cli_log_inf("AVS_SET test complete", level=0)
        #     # if len(pass_nic_list) != 10:
        #     #     rs = False
        #     #     mtp_mgmt_ctrl.cli_log_err("AVS_SET test failed", level=0)
        #     # else:
        #     #     mtp_mgmt_ctrl.cli_log_inf("AVS_SET test passed", level=0)


        # if rs and not mtp_mgmt_ctrl.mtp_nic_diag_init(vmargin=vmarg, swm_lp=swm_lp_boot_mode, nic_util=False, stop_on_err=stop_on_err):
        #     mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
        #     libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        #     mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
        #     rs = False
        #     return False

        if rs:
            mtp_mgmt_ctrl.mtp_power_cycle_nic()

        # Secure key programming (only program one slot)
        if rs:
            first_nic = True
            ret = False
            for slot in pass_nic_list:
                if not first_nic:
                    break
                first_nic = False
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                
                test_list = ["SEC_KEY_PROG"]
                dsp = "SCREEN_TEST"
                for test in test_list:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
                    ret = mtp_mgmt_ctrl.mtp_program_nic_sec_key(slot)
                    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
                    if not ret:
                        rs = False
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                        fail_nic_list.append(slot)
                        pass_nic_list.remove(slot)
                        mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
                        fail_step = "Fail to SEC_KEY_PROG"
                        fail_desc = "Fail to SEC_KEY_PROG"
                    else:
                        mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))



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

        #write final result
        mtp_mgmt_ctrl.cli_log_inf("##########  MFG {:s} Test Summary  ##########".format("MTP_SCREEN"))
        mtp_mgmt_ctrl.cli_log_inf("---------- {:s} Report: ----------".format(mtp_id))

        if len(fail_nic_list) != 0 or len(pass_nic_list) != 10 or len(fail_step) > 0:
            mtp_mgmt_ctrl.cli_log_err("[{:s}] {:s} FAIL --> {:s}".format(mtp_id, mtp_sn, fail_step))
        else:
            mtp_mgmt_ctrl.cli_log_inf("[{:s}] {:s} PASS".format(mtp_id, mtp_sn))

        mtp_mgmt_ctrl.cli_log_inf("--------- {:s} Report End --------\n".format(mtp_id))


        return True

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        # err_msg = str(e)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)

    mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_PASS, open_file_track_list)


if __name__ == "__main__":
    main()
