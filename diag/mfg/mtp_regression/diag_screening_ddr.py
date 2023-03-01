#!/usr/bin/env python

import sys
import os
import time
import re
import argparse
import threading
import traceback
import copy

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from ddr_test_parameters import test2args as ddrtest2args
import mtp_diag_regression as diag_reg
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
from libdefs import MFG_DIAG_SIG
from libdiag_db import diag_db
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libmfg_cfg import *

def get_test_arguments(test_case_name=None, part_number=None, test2args=ddrtest2args):

    if test_case_name is None:
        return None
    test_case = test_case_name
    if test_case not in test2args:
        return None
    partnumber = part_number if part_number else "DEFAULT"
    no_rev_partnumber =  "-".join(partnumber.split("-")[0:2])

    argdict = dict()
    # load test_case arguments
    for idx, argument in enumerate(test2args[test_case]["ARGUMENT_SPEC"].split()):
        if  partnumber in test2args[test_case]:
            value = test2args[test_case][partnumber].split()[idx]
            if value.upper() == "N/A":
                value = test2args[test_case]["DEFAULT"].split()[idx]
        elif no_rev_partnumber in test2args[test_case]:
            value = test2args[test_case][no_rev_partnumber].split()[idx]
            if value.upper() == "N/A":
                value = test2args[test_case]["DEFAULT"].split()[idx]
        else:
            value = test2args[test_case]["DEFAULT"].split()[idx]
        argdict[argument] = value
    # load test case level common arguments
    apply_test_case_arg = test2args[test_case].get("IS_CASE_COMMON_ARGS_APPLY", True)
    if apply_test_case_arg and "ARGUMENT_SPEC" in test2args["TEST_CASE_COMMON"]:
        for idx, argument in enumerate(test2args["TEST_CASE_COMMON"]["ARGUMENT_SPEC"].split()):
            if  partnumber in test2args["TEST_CASE_COMMON"]:
                value = test2args["TEST_CASE_COMMON"][partnumber].split()[idx]
                if value.upper() == "N/A":
                    value = test2args["TEST_CASE_COMMON"]["DEFAULT"].split()[idx]
            elif no_rev_partnumber in test2args["TEST_CASE_COMMON"]:
                value = test2args["TEST_CASE_COMMON"][no_rev_partnumber].split()[idx]
                if value.upper() == "N/A":
                    value = test2args["TEST_CASE_COMMON"]["DEFAULT"].split()[idx]
            else:
                value = test2args["TEST_CASE_COMMON"]["DEFAULT"].split()[idx]
            argdict[argument] = value
    # load test suite level common arguments
    apply_test_suite_arg = test2args[test_case].get("IS_SUITE_COMMON_ARGS_APPLY", True)
    if apply_test_suite_arg and "ARGUMENT_SPEC" in test2args["TEST_SUITE_COMMON"]:
        for idx, argument in enumerate(test2args["TEST_SUITE_COMMON"]["ARGUMENT_SPEC"].split()):
            if  partnumber in test2args["TEST_SUITE_COMMON"]:
                value = test2args["TEST_SUITE_COMMON"][partnumber].split()[idx]
                if value.upper() == "N/A":
                    value = test2args["TEST_SUITE_COMMON"]["DEFAULT"].split()[idx]
            elif no_rev_partnumber in test2args["TEST_SUITE_COMMON"]:
                value = test2args["TEST_SUITE_COMMON"][no_rev_partnumber].split()[idx]
                if value.upper() == "N/A":
                    value = test2args["TEST_SUITE_COMMON"]["DEFAULT"].split()[idx]
            else:
                value = test2args["TEST_SUITE_COMMON"]["DEFAULT"].split()[idx]
            argdict[argument] = value
    return argdict

def args2optionstring(argdict):
    """
    this function to handle some args which have a value of + or - in config file, inidate this args exist or not 
    """
    args_str = ""
    for k, v in argdict.items():
        if v == "+":
            args_str += " {:s}".format(k)
        elif v == "-":
            pass
        else:
            args_str += " {:s}".format(k)
            args_str += " {:s}".format(str(v))
    return args_str

def mtp_mgmt_run_nic_test_py(mtp_mgmt_ctrl, test, nic_list, vmarg=None):
    nic_fail_list = list()
    sig_list = [MFG_DIAG_SIG.MTP_PARA_TEST_SIG]
    cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Execute command {:s} failed".format(cmd))
        return ["TIMEOUT", nic_list[:]]
    
    # Figure out the unique partnumber
    pn_list= list()
    for slot in nic_list:
        pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot) # get the PN format like this 68-0015-02 01
        pn = pn.split()[0]
        if pn not in pn_list:
            pn_list.append(pn)
    if len(pn_list) != 1:
        mtp_mgmt_ctrl.cli_log_err("Not Support Mix NIC with Different Part Number")
        return ["Not Support", nic_list[:]]
    pn = pn_list[0]
    argsdict = get_test_arguments(test, pn)
    nic_list_param = ",".join(str(slot+1) for slot in nic_list)
    slot_list_arg_name = "-slot_list" if "-slot_list" in argsdict else "--slot_list"
    argsdict[slot_list_arg_name] = nic_list_param
    vmar_arg_name = "-vmarg" if "-vmarg" in argsdict else "--vmarg"
    if vmarg is not None:
        argsdict[vmar_arg_name] = vmarg
    cmd_options =  args2optionstring(argsdict)

    if test == "PRBS_ETH":
        cmd = "nic_test.py -prbs"
    elif test == "SNAKE_HBM":
        cmd = "nic_test.py -snake"
    elif test == "SNAKE_PCIE":
        cmd = "nic_test.py -snake"
    elif test == "SNAKE_ELBA":
        cmd = "nic_test.py -snake"
    elif test == "ETH_PRBS":
        cmd = "nic_test.py -prbs"
    else:
        mtp_mgmt_ctrl.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
        return ["FAIL", nic_list[:]]

    cmd += " " + cmd_options
    mtp_mgmt_ctrl.cli_log_inf("Calling Command: {:s}".format(cmd), level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_TEST_TIMEOUT):
        mtp_mgmt_ctrl.cli_log_err("Run MTP Parallel Test {:s} Failed".format(test))
        return ["TIMEOUT", nic_list[:]]

    ret = "SUCCESS"
    match = re.findall(r"Slot (\d+) ?: +(\w+)", mtp_mgmt_ctrl.mtp_get_cmd_buf())
    for _slot, rslt in match:
        slot = int(_slot) - 1
        if (rslt != "PASS" and rslt != "PASSED") and slot not in nic_fail_list:
            nic_fail_list.append(slot)
            ret = "FAIL"

    return [ret, nic_fail_list]

def mtp_run_ddr_bist(mtp_mgmt_ctrl, slot=None, ddr_bist_cmdline_args_str=None):
    """
    cd ~diag/scripts/asic/
    tclsh ddr_bist.tcl cmdline_args_str
    """

    rs = True
    cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd_para(slot, cmd):
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Command {:s} failed")
        rs = False

    cmd = "tclsh ddr_bist.tcl {:s}".format(ddr_bist_cmdline_args_str)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd_para(slot, cmd, timeout=MTP_Const.MTP_PARA_ASIC_L1_TEST_TIMEOUT):
        rs = False
        mtp_mgmt_ctrl.cli_log_slot_err(slot, cmd_buf)
        # kill the process in case it's hung/timed out
        # ctrl-c doesnt work
        # needs to be killed from separate session
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd_para(slot, "## killall tclsh"): # notify in log
            pass
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("killall tclsh"): # use mtp session to kill it
            pass
    cmd_buf = mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot)
    if MFG_DIAG_SIG.NIC_PARA_DDR_BIST_OK_SIG not in cmd_buf:
        rs = False

    return rs

def single_nic_ddr_bist_test(mtp_mgmt_ctrl, slot, ddr_test_db, test_case_name, nic_test_rslt_list, stop_on_err, vmarg, lock, l1_sequence, swmtestmode, power_cycle_count):

    try:
        if l1_sequence:
            lock.acquire()
        else: # turbo-parallel l1
            mtp_mgmt_ctrl.mtp_turbo_j2c_lock(slot)
            
        err_msg_list = list()
        iteration = ddr_test_db[test_case_name].get("ITER_PER_PC", 1)
        # Figure out the unique partnumber
        pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot) # get the PN format like this 68-0015-02 01
        pn = pn.split()[0]
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        argsdict = copy.deepcopy(get_test_arguments(test_case_name, pn))
        slot_arg_name = "-slot" if "-slot" in argsdict else "--slot"
        argsdict[slot_arg_name] = slot + 1
        sn_arg_name = "-sn" if "-sn" in argsdict else "--sn"
        argsdict[sn_arg_name] = sn
        vmar_arg_name = "-vmarg" if "-vmarg" in argsdict else "--vmarg"
        if vmarg is not None:
            argsdict[vmar_arg_name] = vmarg
        ddr_bist_cmdline_args_str =  args2optionstring(argsdict)
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "ddr_bist args string: {:s}".format(ddr_bist_cmdline_args_str))
        dsp = "DDR_SUITE"
        if vmarg == Voltage_Margin.high:
            dsp_disp = "HV_" + dsp
        elif vmarg == Voltage_Margin.low:
            dsp_disp = "LV_" + dsp
        else:
            dsp_disp = dsp

        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, "DDR_BIST"))
        for iter in range(1, int(iteration)+1):
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "    Iteration: {:d}......".format(iter))
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                nic_test_rslt_list[slot] = False
                break
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, "DDR_BIST")
            if not mtp_run_ddr_bist(mtp_mgmt_ctrl, slot, ddr_bist_cmdline_args_str):
                ret = "FAIL"
                err_msg_list.append("DDR_BIST Failed at {:d} Iteration".format(iter))
            else:
                ret = "SUCCESS"
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, "DDR_BIST", start_ts)
            # double check the L1 test even it pass
            # pass_count, log_err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_nic_l1_err(sn)
            # single_run_expect_pass_count = 9
            # esec_arg_name = "-e" if "-e" in argsdict else "--esec_en"
            # if argsdict[esec_arg_name] == "0":
            #     single_run_expect_pass_count -= 1
            # ddr_arg_name = "-ddr" if "-ddr" in argsdict else "--ddr"
            # if argsdict[ddr_arg_name] == "0":
            #     single_run_expect_pass_count -= 1
            # number_of_l1_tests = single_run_expect_pass_count * iter + (single_run_expect_pass_count * iteration) * (power_cycle_count -1)

            # mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "number_of_l1_tests {:d}".format(number_of_l1_tests))
            # mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "pass_count {:d}".format(pass_count))
            # if pass_count != number_of_l1_tests:
            #     err_msg_list.append("Some L1 Sub Test Failed, current passed_count: {:d}".format(pass_count))
            #     if ret == "SUCCESS":
            #         ret = "FAIL"
            # if log_err_msg_list:
            #     err_msg_list += log_err_msg_list

            if ret == "SUCCESS":
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp_disp, "DDR_BIST", duration))
            else:
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, "DDR_BIST", ret, duration))
                card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                    mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, "DDR_BIST", ret, duration))
                nic_test_rslt_list[slot] = False

                # only display first 3 and last 3 error messages
                if len(err_msg_list) < 6:
                    err_msg_disp_list = err_msg_list
                else:
                    err_msg_disp_list = err_msg_list[:3] + err_msg_list[-3:]
                for err_msg in err_msg_disp_list:
                    mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, "DDR_BIST", err_msg))
                    card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                    if card_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, "DDR_BIST", err_msg))
                
                # Post Failure check
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "=== Post Fail Check Steps Start ===>")
                try:
                    libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot)
                except Exception:
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "Post Fail Check Issue, Ignore")
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "<=== Post Fail Check Steps End ===")

                if stop_on_err:
                    break

        if l1_sequence:
            if not stop_on_err:
                if  not nic_test_rslt_list[slot]:
                    mtp_mgmt_ctrl._lock.acquire()
                    mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
                    mtp_mgmt_ctrl._lock.release()
            lock.release()
        else: # turbo-parallel l1
            mtp_mgmt_ctrl.mtp_turbo_j2c_unlock(slot)
            # wait for all slots to complete
            while True in [x.locked() for x in mtp_mgmt_ctrl._turbo_j2c_lock]:
                continue
            if not stop_on_err:
                if  not nic_test_rslt_list[slot]:
                    mtp_mgmt_ctrl._lock.acquire()
                    mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
                    mtp_mgmt_ctrl._lock.release()
    except Exception as Err:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, str(Err))
        nic_test_rslt_list[slot] = False

def diag_seq_ddr_bist_test(mtp_mgmt_ctrl, nic_type, nic_list, ddr_test_db, test_case_name, vmarg, stop_on_err, swmtestmode, l1_sequence):

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag DDR_BIST Sequential Test Start".format(nic_type), level=0)
    power_cycle_iterations =ddr_test_db[test_case_name].get("ITER", 1)
    fail_list = list()
    nic_list = nic_list[:]
    lock = threading.Lock()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM

    for ite in range(1, power_cycle_iterations+1):
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
            # if Tubor MTP got 8G memory, it can run all 10 NIC in parallel
            if int(mtp_mgmt_ctrl.mtp_get_memory_size()) >= 8 * 1000 * 1000:
                nic_top_test_list = nic_list[:]
                nic_bottom_test_list = []
            else:
                nic_top_test_list    = [x for x in nic_list if x in [0,2,4,6,8]] # odd slots
                nic_bottom_test_list = [x for x in nic_list if x in [1,3,5,7,9]] # even slots
        else:
            l1_sequence = True

        nic_thread_list = list()

        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag DDR_BIST iteration: {:d}".format(nic_type, ite), level=0)
        # Directely call mtp_nic_diag_init instead of call mtp_nic_diag_init after call mtp_power_cycle_nic since mtp_nic_diag_init will call 
        # nic_test.py, which will do the power cycle.
        if ite > 1:
            mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Calling MTP_NIC_DIAG_INIT To Power Cycle NIC Card and Re-init it ".format(nic_type), level=0)
            if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, vmargin=vmarg, nic_util=True, stop_on_err=stop_on_err):
                mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                for slot in nic_list:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        nic_test_rslt_list[slot] = False
                        if slot not in fail_list:
                            fail_list.append(slot)
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_err("STOP_ON_ERR asserted when diag initial")
                    raise Exception
                    #return fail_list

        # top half of the NICs
        if len(nic_top_test_list) > 0:
            adi_nic_list = list()
            for slot in nic_top_test_list:
                if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.ORTANO2ADI or  mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.ORTANO2ADICR:
                    adi_nic_list.append(slot)
            if len(adi_nic_list) > 0:
                mtp_mgmt_ctrl.mtp_power_cycle_nic(adi_nic_list, dl=True, count_down=False)

        for slot in nic_top_test_list[:]:
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                nic_test_rslt_list[slot] = False
                continue
            nic_thread = threading.Thread(target = single_nic_ddr_bist_test,
                                          args = (mtp_mgmt_ctrl,
                                                  slot,
                                                  ddr_test_db,
                                                  test_case_name,
                                                  nic_test_rslt_list,
                                                  stop_on_err,
                                                  vmarg,
                                                  lock,
                                                  l1_sequence,
                                                  swmtestmode,
                                                  ite))
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)

        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(5)


        # bottom half of the NICs
        if len(nic_bottom_test_list) > 0:
            adi_nic_list = list()
            for slot in nic_bottom_test_list:
                if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.ORTANO2ADI or mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.ORTANO2ADICR:
                    adi_nic_list.append(slot)
            if len(adi_nic_list) > 0:
                mtp_mgmt_ctrl.mtp_power_cycle_nic(adi_nic_list, dl=True, count_down=False)

        for slot in nic_bottom_test_list[:]:
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                nic_test_rslt_list[slot] = False
                continue
            nic_thread = threading.Thread(target = single_nic_ddr_bist_test,
                                          args = (mtp_mgmt_ctrl,
                                                  slot,
                                                  ddr_test_db,
                                                  test_case_name,
                                                  nic_test_rslt_list,
                                                  stop_on_err,
                                                  vmarg,
                                                  lock,
                                                  l1_sequence,
                                                  swmtestmode,
                                                  ite))
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)

        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(5)

        for slot in nic_list[:]:
            if not nic_test_rslt_list[slot]:
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                    raise Exception
                if slot not in fail_list:
                    fail_list.append(slot)
                nic_list.remove(slot)

    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Sequential Test Complete\n".format(nic_type), level=0)
    return fail_list

def diag_para_mem_edma_ddr_stress_test(mtp_mgmt_ctrl, nic_type, nic_list, test_db, test_list, stop_on_err, vmarg, aapl, swmtestmode, skip_testlist, iterations):
    """
    This funtion run MEM EDMA test and MEM DDR_STRESS test in parallel on individual NIC card by calling existing existing function single_nic_diag_regression on thread
    """

    sub_test_list = test_list[:]
    new_nic_list = nic_list[:]

    if aapl == False:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag DDR Memory {:s}:{:s} Test Start".format(nic_type, "MEM", "EDMA#DDR_STRESS"), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag DDR Memory {:s}:{:s} Test Start with aapl initiaize".format(nic_type, "MEM", "EDMA#DDR_STRESS"), level=0)

    for skipped_test in skip_testlist:
        sub_test_list = [ (s,t) for s,t in sub_test_list if s != skipped_test ]
        sub_test_list = [ (s,t) for s,t in sub_test_list if t != skipped_test ]

    fail_list = list()
    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    for ite in range(1, iterations+1):
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag {:s} {:s} Test In {:d}th Power Cycle Iteration".format(nic_type, "MEM", "EDMA#DDR_STRESS", ite), level=0)
        # Directely call mtp_nic_diag_init instead of call mtp_nic_diag_init after call mtp_power_cycle_nic since mtp_nic_diag_init will call 
        # nic_test.py, which will do the power cycle.
        if ite >= 1:
            mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Calling MTP_NIC_DIAG_INIT To Power Cycle NIC Card and Re-init it ".format(nic_type), level=0)
            if not mtp_mgmt_ctrl.mtp_nic_diag_init(new_nic_list, vmargin=vmarg, nic_util=True, stop_on_err=stop_on_err):
                mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                for slot in new_nic_list:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        nic_test_rslt_list[slot] = False
                        if slot not in fail_list:
                            fail_list.append(slot)
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_err("STOP_ON_ERR asserted when diag initial")
                    raise Exception

        for slot in new_nic_list:
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                nic_test_rslt_list[slot] = False
                if slot not in fail_list:
                    fail_list.append(slot)
                continue
            nic_thread = threading.Thread(target = diag_reg.single_nic_diag_regression,
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

        # Collect NIC onboard logfiles, we need copy log before NIC power cycle for EDMA and DDR_STRESS Test. 
        for slot in new_nic_list:
            if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_diag_logfile(slot, aapl):
                mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Collecting NIC onboard diag logfile failed")

        for slot in new_nic_list:
            if not nic_test_rslt_list[slot]:
                if slot not in fail_list:
                    fail_list.append(slot)
                if stop_on_err:
                    if stop_on_err:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                        raise Exception
                new_nic_list.remove(slot)

    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))

    if aapl == False:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel DSP Test Complete\n".format(nic_type), level=0)
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel PRBS Test Complete\n".format(nic_type), level=0)

    return fail_list

def diag_exec_mtp_para_test(mtp_mgmt_ctrl, nic_type, nic_list, para_test_list, vmarg, stop_on_err, swmtestmode, skip_testlist):
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Start".format(nic_type), level=0)

    for skipped_test in skip_testlist:
        if skipped_test in para_test_list:
            para_test_list.remove(skipped_test)

    fail_list = list()
    nic_top_test_list = list()
    nic_bot_test_list = list()

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

    # separate lists for ORC ortano adi and IBM ortano adi 
    if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADICR):
        orc_list, ibm_list = [], []
        for slot in nic_list:
            if nic_type == NIC_Type.ORTANO2ADI or nic_type == NIC_Type.ORTANO2ADICR:
                orc_list.append(slot)
            else:
                ibm_list.append(slot)
        nic_top_test_list = orc_list[:]
        nic_bot_test_list = ibm_list[:]

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

            ret, test_fail_list = mtp_mgmt_run_nic_test_py(mtp_mgmt_ctrl, test, nic_test_list, vmarg)
            
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
                    nic_test_list.remove(slot)
                    #for DDR validation test, set skip_vrm_check to False so that command 'nic_sts.tcl SN slotID skip_vrm_check' using the default
                    mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, test, ret, mtp_mgmt_ctrl.mtp_get_cmd_buf(), [], False)
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                    raise Exception
                if slot not in fail_list:
                    fail_list.append(slot)
                fail_slot_test_list.append((slot, test))

            # passed nic display
            for slot in nic_test_list:
                if slot not in test_fail_list:
                    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

            # Post Failure check
            if fail_list:
                mtp_mgmt_ctrl.cli_log_inf("=== Post Fail Check Steps Start ===>")
                try:
                    for slot in fail_list[:]:
                        libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot)
                except Exception:
                    mtp_mgmt_ctrl.cli_log_inf("Post Fail Check Issue, Ignore")
                mtp_mgmt_ctrl.cli_log_inf("<=== Post Fail Check Steps End ===")

        if GLB_CFG_MFG_TEST_MODE:
            mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Complete\n".format(nic_type), level=0)
    return fail_list, fail_slot_test_list

def diag_exec_mtp_para_test_multiple_times(mtp_mgmt_ctrl, nic_type, nic_list, para_test_list, vmarg, stop_on_err, swmtestmode, skip_testlist, iterations, iterations_per_pc=1):

    fail_list = list()
    new_nic_list = nic_list[:]
    fail_slot_test_list = list()
    for ite in range(1, iterations+1):
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag {:s} {:s} Test In {:d}th Power Cycle Iteration".format(nic_type, "MEM", "SNAKE", ite), level=0)
        # Directely call mtp_nic_diag_init instead of call mtp_nic_diag_init after call mtp_power_cycle_nic since mtp_nic_diag_init will call 
        # nic_test.py, which will do the power cycle.
        if ite > 1:
            mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Calling MTP_NIC_DIAG_INIT To Power Cycle NIC Card and Re-init it ".format(nic_type), level=0)
            if not mtp_mgmt_ctrl.mtp_nic_diag_init(new_nic_list, vmargin=vmarg, nic_util=True, stop_on_err=stop_on_err):
                mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                for slot in new_nic_list:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        new_nic_list.remove(slot)
                        if slot not in fail_list:
                            fail_list.append(slot)
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_err("STOP_ON_ERR asserted when diag initial")
                    raise Exception

        for ite_pc in range(1, iterations_per_pc+1):
            mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Running DDR MEM SNAKE test at iteration {:d} ".format(nic_type, ite_pc), level=0)
            mtp_para_fail_list, fstl = diag_exec_mtp_para_test(mtp_mgmt_ctrl,
                                                               nic_type,
                                                               new_nic_list,
                                                               para_test_list,
                                                               vmarg,
                                                               stop_on_err,
                                                               swmtestmode,
                                                               skip_testlist)
            for slot in mtp_para_fail_list:
                if slot in new_nic_list:
                    if stop_on_err:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                        raise Exception
                    new_nic_list.remove(slot)
                if slot not in fail_list:
                    fail_list.append(slot)
                    fail_slot_test_list += fstl

        if fail_list and stop_on_err:
            mtp_mgmt_ctrl.cli_log_err("STOP_ON_ERR asserted, exiting powercycle iteration {:d} ".format(ite), level=0)
            break
    return fail_list, fail_slot_test_list

def nic_power_cycle_only_test(mtp_mgmt_ctrl, nic_type, nic_list, vmarg, stop_on_err, swmtestmode, iterations):

    fail_list = list()
    new_nic_list = nic_list[:]
    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    for ite in range(1, iterations+1):
        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Running NIC Power Cycle Only Test Iteration: {:d}".format(nic_type, ite), level=0)
        # Directely call mtp_nic_diag_init instead of call mtp_nic_diag_init after call mtp_power_cycle_nic since mtp_nic_diag_init will call 
        # nic_test.py, which will do the power cycle.
        if ite > 1:
            mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Calling MTP_NIC_DIAG_INIT To Power Cycle NIC Card and Re-init it ".format(nic_type), level=0)
            if not mtp_mgmt_ctrl.mtp_nic_diag_init(new_nic_list, vmargin=vmarg, nic_util=True, stop_on_err=stop_on_err):
                mtp_mgmt_ctrl.mtp_diag_fail_report("Initialize NIC diag environment failed")
                for slot in new_nic_list:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        nic_test_rslt_list[slot] = False
                        if slot not in fail_list:
                            fail_list.append(slot)
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_err("STOP_ON_ERR asserted when diag initial")
                    raise Exception
    
        for slot in new_nic_list[:]:
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                nic_test_rslt_list[slot] = False
                continue
            nic_thread = threading.Thread(target = single_nic_post_powercycle_check,
                                          args = (mtp_mgmt_ctrl,
                                                  slot,
                                                  nic_test_rslt_list,
                                                  stop_on_err,
                                                  ite))
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

        for slot in new_nic_list[:]:
            if not nic_test_rslt_list[slot]:
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                    raise Exception
                if slot not in fail_list:
                    fail_list.append(slot)
                new_nic_list.remove(slot)

    if GLB_CFG_MFG_TEST_MODE:
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    else:
        mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))

    # # Collect NIC onboard logfiles
    # for slot in nic_list:
    #     if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_diag_logfile(slot, False):
    #         mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Collecting NIC onboard diag logfile failed")

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} NIC Power Cycle Only Test Complete\n".format(nic_type), level=0)

    return fail_list

def single_nic_post_powercycle_check(mtp_mgmt_ctrl, slot, nic_test_rslt_list, stop_on_err, current_iter):

    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} NIC Status Routines Check At Iteration {:s} ".format(sn, str(current_iter)))
    ### Verify NIC FW running well
    if not mtp_mgmt_ctrl.mtp_verify_nic_diag_boot(slot):
        nic_test_rslt_list[slot] = False
    result = mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot)
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, result)
    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
        nic_test_rslt_list[slot] = False

    if not nic_test_rslt_list[slot] and stop_on_err:
        # Post Failure check
        mtp_mgmt_ctrl.cli_log_inf("=== Post Fail Check Steps Start ===>")
        try:
            libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot)
        except Exception:
            mtp_mgmt_ctrl.cli_log_inf("Post Fail Check Issue, Ignore")
        mtp_mgmt_ctrl.cli_log_inf("<=== Post Fail Check Steps End ===")
        return

def main():
    parser = argparse.ArgumentParser(description="Single MTP Diagnostics Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--stop_on_error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--stage", "--corner", type=FF_Stage, help="diagnostic environment condition", choices=list(FF_Stage), default=FF_Stage.FF_P2C)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--fail-slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("-cfg", "--cfgyaml", help="Test case config file for DDR test suite, default to %(default)s", default="config/ddr_test_suite.yaml")
    parser.add_argument("--vmarg", help="specify the vmargin, deduced from environment temperature if not specified", nargs="*",  choices=["normal", "high", "low"], default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--l1-seq", help="asic L1 run under sequence mode", action='store_true')
    args = parser.parse_args()

    mtp_id = args.mtpid
    mtp_cli_id_str = libmfg_utils.id_str(mtp=mtp_id)
    parameter_cfg_yaml = args.cfgyaml
    
    swm_lp_boot_mode = False 
    stop_on_err = args.stop_on_error
    verbosity = args.verbosity
    l1_sequence = args.l1_seq
    stage = args.stage
    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    high_temp_threshold, low_temp_threshold = libmfg_utils.pick_temperature_thresholds(stage)
    fanspd = libmfg_utils.pick_fan_speed(stage)
    vmarg_list = libmfg_utils.pick_voltage_margin(stage)

    # overwrite the varg_list if specified from command line arguments
    if args.vmarg:
        vmarg_list = args.vmarg

    # load the mtp config
    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    if args.mtpcfg:
        mtp_chassis_cfg_file_list.append(os.path.abspath(args.mtpcfg))
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
    test_cfg_file[NIC_Type.ORTANO2INTERP] = "config/ortanoi_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.ORTANO2SOLO] = "config/ortanos_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.POMONTEDELL] = "config/pomontedell_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.LACONA32DELL] = "config/lacona32dell_mtp_test_cfg.yaml"
    test_cfg_file[NIC_Type.LACONA32] = "config/lacona32_mtp_test_cfg.yaml"

    test_db = dict()
    for nic_type in test_cfg_file.keys():
        test_db[nic_type] = diag_db(stage, test_cfg_file[nic_type])

    mtp_para_test_list = dict()
    for nic_type in test_db.keys():
        mtp_para_test_list[nic_type] = test_db[nic_type].get_mtp_para_test_list()

    # load DDR test suite test cases and test steps
    ddr_suite = libmfg_utils.load_cfg_from_yaml_file_list([parameter_cfg_yaml])
    # libmfg_utils.cli_inf("TEST_SUITE_NAME: {:s}".format(ddr_suite["TEST_SUITE_NAME"]))
    ddr_test_db = dict()
    for test_case in ddr_suite["TEST_CASE"]:
        # libmfg_utils.cli_inf("Test Case: {:s} with iteration: {:d}".format(test_case["NAME"], test_case["ITER"]))
        temp_dict = dict()
        temp_dict["ITER"] = test_case["ITER"]
        if "ITER_PER_PC" in test_case:
            temp_dict["ITER_PER_PC"] = test_case["ITER_PER_PC"]
        ddr_test_db[test_case["NAME"]] = temp_dict

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
    mtp_script_dir, open_file_track_list = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True)

    try:
        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, stage=stage):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
            return

        # Set Naples25SWM test mode
        mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)

        # Wait the Chamber temperature, if HT or LT is set
        mtp_mgmt_ctrl.cli_log_inf("Diag DDR Test Ambient Temperature Check", level=0)
        rdy = mtp_mgmt_ctrl.mtp_wait_temp_ready(low_temp_threshold, high_temp_threshold)
        # hack for temp
        rdy = True
        if not rdy:
            mtp_mgmt_ctrl.mtp_diag_fail_report("Diag DDR Test Ambient Temperature Check Failed")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_ENV_SETUP, open_file_track_list)
            return
        # only MFG HT/LT need soaking process
        if stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_4C_L, FF_Stage.FF_4C_H):
            mtp_mgmt_ctrl.mtp_wait_soaking()
        mtp_mgmt_ctrl.cli_log_inf("Diag DDR Test Ambient Temperature Check Complete\n", level=0)


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
            nic_test_full_list.append(nic_type_list)

        nic_skipped_list = mtp_mgmt_ctrl.mtp_get_nic_skip_list()
        for slot in range(len(nic_skipped_list)):
            if nic_skipped_list[slot]:
                skip_nic_list.append(slot)

        # check if MTP support present NIC
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag DDR compatibility check started", level=0)
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

                if stage not in (FF_Stage.FF_P2C, FF_Stage.QA):    #Skip SWM Low Power Test for 4C
                    swm_lp_boot_mode=False

            if nic_list:
                if not mtp_capability & mtp_exp_capability:
                    mtp_mgmt_ctrl.mtp_diag_fail_report("MTP capability 0x{:x} doesn't support {:s}".format(mtp_capability, nic_type))
                    libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                    diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
                    return
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag DDR compatibility check complete\n", level=0)

        mtp_mgmt_ctrl.cli_log_inf("MTP Diag DDR Test Start", level=0)

        programmables_checked = False

        for vmarg_idx, vmarg in enumerate(vmarg_list):
            # stop the next vmarg corner if stop_on_err is set and some nic fails
            if fail_nic_list and stop_on_err:
                break
            fanspd = mtp_mgmt_ctrl.mtp_get_fanspd()
            inlet = mtp_mgmt_ctrl.mtp_get_inlet_temp(low_temp_threshold, high_temp_threshold)
            mtp_mgmt_ctrl.cli_log_inf("DDR TEST SUITE Runing Vmargin Environment:", level=0)
            if vmarg == Voltage_Margin.high:
                mtp_mgmt_ctrl.cli_log_report_inf("******* HV Corner *******")
            elif vmarg == Voltage_Margin.low:
                mtp_mgmt_ctrl.cli_log_report_inf("******* LV Corner *******")
            else:
                mtp_mgmt_ctrl.cli_log_report_inf("******* NV Corner *******")
            mtp_mgmt_ctrl.cli_log_report_inf("MTP Fan Speed = {:3d}%".format(fanspd))
            mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(inlet))
            mtp_mgmt_ctrl.cli_log_report_inf("NIC Voltage Margin = {:s}".format(vmarg))
            mtp_mgmt_ctrl.cli_log_inf("Diag DDR Test Environment End\n", level=0)

            if vmarg_idx > 0:
                mtp_mgmt_ctrl.mtp_diag_dsp_restart()

            if vmarg_idx == 0:
                ######################################################################
                #  One-time steps
                ######################################################################
                if not programmables_checked and stage in (FF_Stage.FF_P2C, FF_Stage.FF_2C_L, FF_Stage.FF_4C_L):
                    mtp_mgmt_ctrl.mtp_power_off_nic()
                    mtp_mgmt_ctrl.mtp_power_on_nic(slot_list=pass_nic_list, dl=False)

                    dsp = stage

                    # Update programmables if necessary
                    dl_check_fail_list = diag_reg.naples_update_prog(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, fail_nic_list, [], dsp, stop_on_err)
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
                    diag_pre_fail_list = diag_reg.mtp_nic_diag_init_pre(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, [], stage)

                if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_test_full_list, vmargin=vmarg, swm_lp=swm_lp_boot_mode, nic_util=True, stop_on_err=stop_on_err):
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

            test_case_list = [tc['NAME'] for tc in ddr_suite["TEST_CASE"]]
            for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                for test_case in test_case_list:
                    if test_case == "DDR_BIST":
                        ######################################################################
                        #  DDR BIST run by NIC sequential test
                        ######################################################################
                        if nic_list:
                            diag_seq_fail_list = diag_seq_ddr_bist_test(mtp_mgmt_ctrl,
                                                                        nic_type,
                                                                        nic_list,
                                                                        ddr_test_db,
                                                                        test_case,
                                                                        vmarg,
                                                                        stop_on_err,
                                                                        swmtestmode,
                                                                        l1_sequence)
                            for slot in diag_seq_fail_list:
                                if slot in nic_list and stop_on_err:
                                    nic_list.remove(slot)
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)
                    elif test_case == "EDMA#DDR_STRESS":
                        ######################################################################
                        #  EDMA and DDR_STRESS test by diag -r -c 
                        ######################################################################
                        # using a empty skip test list to leverage existing function 
                        skip_test = []
                        if nic_type not in ELBA_NIC_TYPE_LIST:
                            continue
                        nic_test_db = test_db[nic_type]
                        if nic_list:
                            # multiply by iterations per power cycle
                            iterations_per_pc = ddr_test_db["EDMA#DDR_STRESS"].get("ITER_PER_PC", 1)
                            iterations = ddr_test_db["EDMA#DDR_STRESS"].get("ITER", 1)
                            nic_para_test_list = [("MEM", "EDMA")] * int(iterations_per_pc) + [("MEM", "DDR_STRESS")] * int(iterations_per_pc)
                            diag_para_fail_list = diag_para_mem_edma_ddr_stress_test(mtp_mgmt_ctrl,
                                                                                    nic_type,
                                                                                    nic_list,
                                                                                    nic_test_db,
                                                                                    nic_para_test_list,
                                                                                    stop_on_err,
                                                                                    vmarg,
                                                                                    False,
                                                                                    swmtestmode,
                                                                                    skip_test,
                                                                                    iterations)
                            for slot in diag_para_fail_list:
                                if slot in nic_list and stop_on_err:
                                    nic_list.remove(slot)
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)
                    elif test_case == "SNAKE":
                        ######################################################################
                        #  DDR SNAKE TEST run by NIC MTP Parallel test 
                        ######################################################################
                        # using a empty skip test list to leverage existing function
                        iter_per_pc = ddr_test_db["SNAKE"].get("ITER_PER_PC", 1)
                        iterations = ddr_test_db["SNAKE"].get("ITER", 1)
                        skip_test = []
                        if nic_type == NIC_Type.NAPLES25SWM:
                            if swmtestmode == Swm_Test_Mode.ALOM:
                                continue
                        nic_mtp_para_test_list = mtp_para_test_list[nic_type]
                        # for DDR Sanke test, we only need "run nic_test.py -snake" here, so overwrite test list with "SNAKE_ELBA"
                        nic_mtp_para_test_list = ["SNAKE_ELBA"]

                        fstl = list()
                        if nic_list:
                            mtp_para_fail_list, fstl = diag_exec_mtp_para_test_multiple_times(mtp_mgmt_ctrl,
                                                                                            nic_type,
                                                                                            nic_list,
                                                                                            nic_mtp_para_test_list,
                                                                                            vmarg,
                                                                                            stop_on_err,
                                                                                            swmtestmode,
                                                                                            skip_test,
                                                                                            iterations,
                                                                                            iter_per_pc)
                            for slot in mtp_para_fail_list:
                                if slot in nic_list and stop_on_err:
                                    nic_list.remove(slot)
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                if slot in pass_nic_list:
                                    pass_nic_list.remove(slot)

                        # copy logfiles out, for snake test, before copy log we need re-init diag
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
                            diag_reg.naples_get_nic_logfile(mtp_mgmt_ctrl, nic_list, nic_mtp_para_test_list, stop_on_err)
                            diag_reg.parse_nic_test_logfile(mtp_mgmt_ctrl, fstl, vmarg)
                            for slot in nic_list:
                                mtp_mgmt_ctrl.mtp_unhide_nic_status(slot)
                    elif test_case == "POWER_CYCLE_ONLY":
                        ######################################################################
                        # NIC Power Cycle Only Test
                        ######################################################################
                        # using a empty skip test list to leverage existing function 
                        skip_test = []
                        if nic_type not in ELBA_NIC_TYPE_LIST:
                            continue
                        iterations = ddr_test_db["POWER_CYCLE_ONLY"].get("ITER", 1)
                        if nic_list:
                            diag_para_fail_list = nic_power_cycle_only_test(mtp_mgmt_ctrl,
                                                                            nic_type,
                                                                            nic_list,
                                                                            vmarg,
                                                                            stop_on_err,
                                                                            swmtestmode,
                                                                            iterations)
                            for slot in diag_para_fail_list:
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

            if vmarg == Voltage_Margin.low:
                diag_sub_dir = "/lv_diag_logs/"
                nic_sub_dir = "/lv_nic_logs/"
                asic_sub_dir = "/lv_asic_logs/"
            elif vmarg == Voltage_Margin.high:
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


        # Enable PCIe poll
        #ADD - Bypass shutting down slot right now for debug
        if not stop_on_err:
            if mtp_mgmt_ctrl.mtp_get_asic_support() == MTP_ASIC_SUPPORT.CAPRI:
                mtp_mgmt_ctrl.mtp_power_cycle_nic(slot_list=pass_nic_list, dl=False)
                mtp_mgmt_ctrl.cli_log_inf("Wait {:02d} seconds for NIC power up before enable PCIE poll".format(MTP_Const.MTP_PCIE_EN_DIS_DELAY), level=0)
                libmfg_utils.count_down(MTP_Const.MTP_PCIE_EN_DIS_DELAY)
                diag_post_fail_list = diag_reg.mtp_nic_diag_init_post(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, args.skip_test, stage)
                # failed enable pcie poll, fail the card
                for slot in diag_post_fail_list:
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)

        mtp_mgmt_ctrl.cli_log_inf("MTP DDR Verification Test Complete\n", level=0)

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

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)

    diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_PASS, open_file_track_list)


if __name__ == "__main__":
    main()
