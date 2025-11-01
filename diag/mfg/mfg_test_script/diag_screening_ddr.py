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
import copy

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
import testlog
import test_utils
import parallelize
import image_control
import libmtp_utils
from ddr_test_parameters import test2args as ddrtest2args
from libdefs import MTP_Const
from libdefs import NIC_Type
from libdefs import MTP_TYPE
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
from mtp_dl_test import dl_salina_qspi_program

def get_test_arguments(test_case_name=None, part_number=None, test2args=ddrtest2args):

    if test_case_name is None:
        return None
    test_case = test_case_name
    if test_case not in test2args:
        return None
    partnumber = part_number if part_number else "DEFAULT"
    no_rev_partnumber =  "-".join(partnumber.split("-")[0:2])
    if partnumber != "DEFAULT" and partnumber == no_rev_partnumber:
        no_rev_partnumber = partnumber[0:6]

    argdict = dict()
    # load test_case arguments
    for idx, argument in enumerate(test2args[test_case]["ARGUMENT_SPEC"].split()):
        # same command line option may have differnce value, such as stressapptest_arm -M 400  -f file.1 -f file.2 -s
        values = []
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
        values.append(value)
        if argument in argdict:
            argdict[argument] += values
        else:
            argdict[argument] = values
    # load test case level common arguments
    apply_test_case_arg = test2args[test_case].get("IS_CASE_COMMON_ARGS_APPLY", True)
    if apply_test_case_arg and "ARGUMENT_SPEC" in test2args["TEST_CASE_COMMON"]:
        for idx, argument in enumerate(test2args["TEST_CASE_COMMON"]["ARGUMENT_SPEC"].split()):
            values = []
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
            values.append(value)
            if argument in argdict:
                argdict[argument] += values
            else:
                argdict[argument] = values
    # load test suite level common arguments
    apply_test_suite_arg = test2args[test_case].get("IS_SUITE_COMMON_ARGS_APPLY", True)
    if apply_test_suite_arg and "ARGUMENT_SPEC" in test2args["TEST_SUITE_COMMON"]:
        for idx, argument in enumerate(test2args["TEST_SUITE_COMMON"]["ARGUMENT_SPEC"].split()):
            values = []
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
            values.append(value)
            if argument in argdict:
                argdict[argument] += values
            else:
                argdict[argument] = values
    return argdict

def args2optionstring(argdict):
    """
    this function to handle some args which have a value of + or - in config file, inidate this args exist or not 
    """
    args_str = ""
    for k, valuses in list(argdict.items()):
        for v in valuses:
            if v == "+":
                args_str += " {:s}".format(k)
            elif v == "-":
                pass
            else:
                args_str += " {:s}".format(k)
                args_str += " {:s}".format(str(v))
    return args_str

# test cleanup.
def mtp_test_cleanup(error_code, fp_list=None):
    if fp_list:
        for fp in fp_list:
            fp.close()
    os.system("sync")

@parallelize.parallel_nic_using_ssh
def check_compatability(mtp_mgmt_ctrl, slot, mtp_capability):
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.VOMERO2:
        mtp_exp_capability = 0x3
    elif nic_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
        mtp_exp_capability = 0x2
    elif nic_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
        mtp_exp_capability = 0x1
    elif nic_type in MTP_MATERA_CAPABLE_NIC_TYPE_LIST:
        mtp_exp_capability = 0x4
    else:
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC Type {:s}'s MTP compatibility unknown".format(nic_type), level=0)
    if not mtp_capability & mtp_exp_capability:
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "MTP capability 0x{:x} doesn't support {:s}".format(mtp_capability, nic_type))
        return False
    return True

@parallelize.parallel_nic_using_console
def check_cpld_version(mtp_mgmt_ctrl, slot):
    return mtp_mgmt_ctrl.mtp_nic_cpld_init(slot, smb=True)

@parallelize.parallel_nic_using_ssh
def verify_diagfw(mtp_mgmt_ctrl, slot):
    # need to pass through here, as inner function is called without wrapper elsewhere
    return mtp_mgmt_ctrl.mtp_verify_nic_qspi(slot)

def single_nic_dsp_test(mtp_mgmt_ctrl, slot, test, dsp, vmarg, swmtestmode):
    def get_diag_para_test_run_cmd(dsp, test, slot, opts, sn, mode):
        card_name = "NIC{:d}".format(slot+1)
        param = '"'
        if "SN" in opts and opts["SN"]:
            param += 'sn={:s} '.format(sn)
        if "SLOT" in opts and opts["SLOT"]:
            param += 'slot={:d}'.format(slot+1)
        if "MODE" in opts and opts["MODE"]:
            param += 'mode={:s}'.format(mode)
        param += '"'
        return libmfg_utils.diag_para_run_cmd(card_name, dsp, test, param)

    def get_diag_para_test_errcode_cmd(dsp, slot, opts):
        card_name = "NIC{:d}".format(slot+1)
        return libmfg_utils.diag_para_errcode_cmd(card_name, dsp)

    diag_test_timeout = MTP_Const.DIAG_MEM_DDR_STRESS_TEST_TIMEOUT if dsp == "MEM" and test == "DDR_STRESS" else MTP_Const.DIAG_PARA_TEST_TIMEOUT
    opts = {"NIC_NAME": True, "SN": False, "SLOT": False}
    mode = libmfg_utils.get_mode_param(mtp_mgmt_ctrl, slot, test)
    diag_cmd = get_diag_para_test_run_cmd(dsp, test, slot, opts, None, mode)
    rslt_cmd = get_diag_para_test_errcode_cmd(dsp, slot, opts)

    card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if dsp == "NIC_ASIC" and test == "ETH_PRBS" and card_type in (NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT):
        # external loopback for P2C
        if vmarg == Voltage_Margin.normal:
            diag_cmd += " -p 'int_lpbk=0'"
        # internal loopback for 2C/4C
        else:
            diag_cmd += " -p 'int_lpbk=1'"

    ret, err_msg_list = mtp_mgmt_ctrl.mtp_run_diag_test_para(slot, diag_cmd, rslt_cmd, test, timeout=diag_test_timeout)

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
            ret = False

    if dsp == "NIC_ASIC" and test == "L1":
        pass_count, log_err_msg_list = mtp_mgmt_ctrl.mtp_nic_retrieve_arm_l1_err(sn)
        number_of_arm_l1_tests = 2
        if pass_count != number_of_arm_l1_tests:
            err_msg_list.append("ARM L1 Sub Test only passed: {:d}".format(pass_count))
            ret = False
        if log_err_msg_list:
            err_msg_list += log_err_msg_list

    # only display first 3 and last 3 error messages
    if len(err_msg_list) < 6:
        err_msg_disp_list = err_msg_list
    else:
        err_msg_disp_list = err_msg_list[:3] + err_msg_list[-3:]
    for err_msg in err_msg_disp_list:
        mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_set_err_msg(err_msg)

    return ret

@parallelize.parallel_nic_using_ssh
def single_nic_dsp_ssh_test(mtp_mgmt_ctrl, slot, test, dsp, vmarg, swmtestmode=Swm_Test_Mode.SW_DETECT):
    return single_nic_dsp_test(mtp_mgmt_ctrl, slot, test, dsp, vmarg, swmtestmode)

@parallelize.parallel_nic_using_console
def single_nic_dsp_console_test(mtp_mgmt_ctrl, slot, test, dsp, vmarg, swmtestmode=Swm_Test_Mode.SW_DETECT):
    return single_nic_dsp_test(mtp_mgmt_ctrl, slot, test, dsp, vmarg, swmtestmode)

@parallelize.parallel_nic_using_ssh
def naples_get_nic_logfile(mtp_mgmt_ctrl, slot, mtp_para_test_list):
    mtp_para_test_list = mtp_para_test_list[slot]
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
        elif nic_type in ELBA_NIC_TYPE_LIST:
            logfile_list.append(path+"snake_elba.log")
        logfile_list.append("/data/nic_util/asicutil*log")
    if "ETH_PRBS" in mtp_para_test_list:
        if nic_type in CAPRI_NIC_TYPE_LIST:
            # uses DSP log
            pass
        elif nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"giglio_PRBS_MX.log")
        elif nic_type in ELBA_NIC_TYPE_LIST:
            logfile_list.append(path+"elba_PRBS_MX.log")
    if "ARM_L1" in mtp_para_test_list:
        if nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"giglio_arm_l1_test.log")
        elif nic_type in ELBA_NIC_TYPE_LIST:
            logfile_list.append(path+"elba_arm_l1_test.log")
    if "PCIE_PRBS" in mtp_para_test_list:
        if nic_type in CAPRI_NIC_TYPE_LIST:
            # uses DSP log
            pass
        elif nic_type in GIGLIO_NIC_TYPE_LIST:
            logfile_list.append(path+"giglio_PRBS_PCIE.log")
        elif nic_type in ELBA_NIC_TYPE_LIST:
            logfile_list.append(path+"elba_PRBS_PCIE.log")
        logfile_list.append("/data/nic_util/asicutil*log")
    if "DDR_BIST" in mtp_para_test_list:
        logfile_list.append(path+"arm_ddr_bist_0.log")
        logfile_list.append(path+"arm_ddr_bist_1.log")

    if not mtp_mgmt_ctrl.mtp_mgmt_save_nic_logfile(slot, logfile_list):
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Collecting MTP parallel test logfile failed")
        return False

    ret = True
    for test in mtp_para_test_list:
        err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_mtp_para_err(slot, test)
        for err_msg in err_msg_list:
            mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_set_err_msg(err_msg)
            ret = False

    return ret

def run_j2c_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, stage, force_sequential, joo='1', loopback='0', offload='0', esecure='0', simplified='0', ite='1', ddr="1"):

    @parallelize.parallel_nic_using_j2c
    def run_j2c_test_normally(mtp_mgmt_ctrl, slot, test, vmarg):
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot)
        mode = libmfg_utils.get_mode_param(mtp_mgmt_ctrl, slot, test)
        n_vmarg = vmarg
        if vmarg in (Voltage_Margin.high, Voltage_Margin.low):
            n_vmarg += libmfg_utils.pick_voltage_margin_percentage(pn)
            mtp_mgmt_ctrl.cli_log_inf("Vmargin is: {:s} After Apply Percentage using Part Number: {:s} For before run_l1.sh".format(n_vmarg, pn), level=0)

        return mtp_mgmt_ctrl.mtp_run_asic_l1_bash(slot, sn, mode, n_vmarg, stage, joo, loopback, offload, esecure, simplified, ite, ddr)

    @parallelize.sequential_nic_test
    def run_j2c_test_sequentially(mtp_mgmt_ctrl, slot, test, vmarg):
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot)
        mode = libmfg_utils.get_mode_param(mtp_mgmt_ctrl, slot, test)
        n_vmarg = vmarg
        if vmarg in (Voltage_Margin.high, Voltage_Margin.low):
            n_vmarg += libmfg_utils.pick_voltage_margin_percentage(pn)
            mtp_mgmt_ctrl.cli_log_inf("Vmargin is: {:s} After Apply Percentage using Part Number: {:s} For before run_l1.sh".format(n_vmarg, pn), level=0)

        return mtp_mgmt_ctrl.mtp_run_asic_l1_bash(slot, sn, mode, n_vmarg, stage, joo, loopback, offload, esecure, simplified, ite, ddr)

    if force_sequential:
        fail_j2c_list = run_j2c_test_sequentially(mtp_mgmt_ctrl, nic_list, test, vmarg)
    else:
        fail_j2c_list = run_j2c_test_normally(mtp_mgmt_ctrl, nic_list, test, vmarg)

    # double check the L1 test even if it passed
    if dsp == "ASIC" and (test == "L1" or  test == "L1_OW"):
        for slot in nic_list:
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            pass_count, log_err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_nic_l1_err(sn, ow=True if test == "L1_OW" else False)
            number_of_l1_tests = 9 if mtp_mgmt_ctrl.mtp_get_mtp_type() != MTP_TYPE.MATERA else 6
            if nic_type in (NIC_Type.LENI48G, NIC_Type.MALFA, NIC_Type.LENI):
                # assuming running ASIC L1 from j2c first then run from one wire,  run only ONCE from both J2C  and one wire
                number_of_l1_tests = 9 if joo == '1' else 5
            if nic_type in (NIC_Type.POLLARA, NIC_Type.LINGUA):
                number_of_l1_tests = 8 if joo == '1' else 5
            err_msg_list = list()
            if pass_count != number_of_l1_tests:
                err_msg_list = ["L1 Sub Test only passed: {:d}".format(pass_count)]
                fail_j2c_list += [slot]
            if log_err_msg_list:
                err_msg_list += log_err_msg_list

            for err_msg in err_msg_list:
                mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_set_err_msg(err_msg)

    return fail_j2c_list

@parallelize.parallel_nic_using_ssh
def ncsi_test_fpga_program(mtp_mgmt_ctrl, slot):
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    return slot not in mtp_mgmt_ctrl.mtp_program_nic_fpga(slot, ["cfg0"], [NIC_IMAGES.test_fpga_img[nic_type]])

@parallelize.parallel_nic_using_ssh
def ncsi_prod_fpga_program(mtp_mgmt_ctrl, slot):
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    return slot not in mtp_mgmt_ctrl.mtp_program_nic_fpga(slot, ["cfg0"], [NIC_IMAGES.cpld_img[nic_type]])

@parallelize.parallel_nic_using_ssh
def salina_snake_qspi_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_P2C
    image_file = image_control.get_qspi_snake_img(mtp_mgmt_ctrl, slot, dsp)["filename"]
    image_path = os.path.dirname(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_file) + os.sep + os.path.basename(image_file)[:-len(".tar.gz")]
    return mtp_mgmt_ctrl.matera_mtp_program_nic_qspi(slot, image_path)

@parallelize.parallel_nic_using_ssh
def salina_erase_qspi(mtp_mgmt_ctrl, slot):
    return mtp_mgmt_ctrl.matera_mtp_erase_nic_qspi(slot)

def health_status(mtp_health):
    mtp_health.monitr_mtp_health(timeout=MTP_Const.MTP_HEALTH_MONITOR_CYCLE)

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
    if mtp_mgmt_ctrl._nic_ctrl_list[slot]._asic_type == "giglio":
        cmd = "tclsh gig_ddr_bist.tcl {:s}".format(ddr_bist_cmdline_args_str)
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "Calling command: {:s}".format(cmd))
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd_para(slot, cmd, timeout=MTP_Const.MTP_PARA_ASIC_L1_TEST_TIMEOUT):
        rs = False
        cmd_buf = mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot)
        # kill the process in case it's hung/timed out
        # ctrl-c doesnt work
        # needs to be killed from separate session
        mtp_mgmt_ctrl._nic_ctrl_list[slot]._nic_handle.logfile_read.write("## killall tclsh") # notify in log
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
        argsdict[slot_arg_name] = [slot + 1]
        sn_arg_name = "-sn" if "-sn" in argsdict else "--sn"
        argsdict[sn_arg_name] = [sn]
        vmar_arg_name = "-vmarg" if "-vmarg" in argsdict else "--vmarg"
        if vmarg is not None:
            argsdict[vmar_arg_name] = [vmarg]
        ddr_bist_cmdline_args_str =  args2optionstring(argsdict)
        # mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "ddr_bist args string: {:s}".format(ddr_bist_cmdline_args_str))
        dsp = "DDR_SUITE"
        if vmarg == Voltage_Margin.high:
            dsp_disp = "HV_" + dsp
        elif vmarg == Voltage_Margin.low:
            dsp_disp = "LV_" + dsp
        else:
            dsp_disp = dsp

        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, "DDR_BIST"))
        for iter in range(1, int(iteration)+1):
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "Internal Iteration: {:d} Within {:d}th Power Cycle Loop Iteration".format(iter, power_cycle_count))
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
                    libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot, "DDR_BIST")
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

def diag_seq_ddr_bist_test(mtp_mgmt_ctrl, nic_list, ddr_test_db, test_case_name, vmarg, stop_on_err, swmtestmode, l1_sequence):

    fail_list = list()
    nic_list = nic_list[:]
    lock = threading.Lock()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    nic_type = list(set([mtp_mgmt_ctrl.mtp_get_nic_type(s_lot) for s_lot in nic_list]))[0]
    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag DDR_BIST Sequential Test Start".format(nic_type), level=0)
    power_cycle_iterations =ddr_test_db[test_case_name].get("ITER", 1)

    for ite in range(1, power_cycle_iterations+1):
        if len(nic_list) <= 5:
            nic_top_test_list = nic_list[:]
            nic_bottom_test_list = []
        # split test nic list into half & half
        else:
            nic_split = len(nic_list)/2
            nic_top_test_list = nic_list[:nic_split]
            nic_bottom_test_list = nic_list[nic_split:]

        if (mtp_mgmt_ctrl._mtp_type == MTP_TYPE.TURBO_ELBA or
            mtp_mgmt_ctrl._mtp_type == MTP_TYPE.TURBO_CAPRI):
            # if Tubor MTP got 8G memory, it can run all 10 NIC in parallel
            if int(mtp_mgmt_ctrl.mtp_get_memory_size()) >= 8 * 1000 * 1000:
                nic_top_test_list = nic_list[:]
                nic_bottom_test_list = []
            else:
                nic_top_test_list    = [x for x in nic_list if x in [0,2,4,6,8]] # odd slots
                nic_bottom_test_list = [x for x in nic_list if x in [1,3,5,7,9]] # even slots
        elif mtp_mgmt_ctrl._mtp_type == MTP_TYPE.MATERA:
            # if Matera MTP, it can run all 10 NIC in parallel
            nic_top_test_list = nic_list[:]
            nic_bottom_test_list = []
        else:
            l1_sequence = True

        nic_thread_list = list()

        mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag DDR_BIST Test Iteration: {:d} (Power Cycle Per Iteration)".format(nic_type, ite), level=0)
        if ite > 1:
            mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Calling MTP_POWER_CYCLE_NIC To Power Cycle Card".format(nic_type), level=0)
            if not mtp_mgmt_ctrl.mtp_power_cycle_nic(nic_list):
                mtp_mgmt_ctrl.mtp_diag_fail_report("Power Cycle NIC list {:s} Failed".format(str(nic_list)))
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
                if mtp_mgmt_ctrl.mtp_get_nic_type(slot) in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT):
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
                if mtp_mgmt_ctrl.mtp_get_nic_type(slot) in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT):
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
                # Post Failure check
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "=== Post Fail Check Steps Start ===>")
                try:
                    libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot, "DDR_BIST")
                except Exception:
                    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "Post Fail Check Issue, Ignore")
                mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "<=== Post Fail Check Steps End ===")
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

def nic_power_cycle_stress_test(mtp_mgmt_ctrl, nic_list, vmarg, stop_on_err, iterations):

    fail_list = list()
    new_nic_list = nic_list[:]
    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    nic_type = list(set([mtp_mgmt_ctrl.mtp_get_nic_type(s_lot) for s_lot in new_nic_list]))[0]
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
        
        new_failed_list = single_nic_post_powercycle_check(mtp_mgmt_ctrl, new_nic_list, stop_on_err, ite, "Power_Cycle_Only_Test")

        for slot in new_failed_list:
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

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} NIC Power Cycle Only Test Complete\n".format(nic_type), level=0)

    return fail_list

@parallelize.parallel_nic_using_ssh
def single_nic_post_powercycle_check(mtp_mgmt_ctrl, slot, stop_on_err, current_iter, testname):

    rc = True
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "{:s} NIC Status Routines Check At Iteration {:s} ".format(sn, str(current_iter)))
    ### Verify NIC FW running well
    # rlist is failed card list
    rlist = mtp_mgmt_ctrl.mtp_verify_nic_diag_boot(slot)
    if rlist:
        rc = False
    result = mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot)
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, result)
    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
        rc = False

    if not rc and stop_on_err:
        # Post Failure check
        mtp_mgmt_ctrl.cli_log_inf("=== Post Fail Check Steps Start ===>")
        try:
            libmfg_utils.post_fail_steps(mtp_mgmt_ctrl, slot, testname)
        except Exception:
            mtp_mgmt_ctrl.cli_log_inf("Post Fail Check Issue, Ignore")
        mtp_mgmt_ctrl.cli_log_inf("<=== Post Fail Check Steps End ===")

    return rc

def main():
    parser = argparse.ArgumentParser(description="Single MTP DDR Validation Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--stop_on_error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--stage", "--corner", type=FF_Stage, help="diagnostic environment condition", choices=list(FF_Stage), default=FF_Stage.FF_P2C)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip_test", help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser.add_argument("--only_test", help="run particular tests only", nargs="*", default=[])
    parser.add_argument("--fail-slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("--skip_slots", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("-cfg", "--cfgyaml", help="Test case config file for DDR test suite, default to %(default)s", default="config/ddr_test_suite.yaml")
    parser.add_argument("--vmarg", help="specify the vmargin, deduced from environment temperature if not specified", nargs="*",  choices=["normal", "high", "low"], default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--l1-seq", help="asic L1 run under sequence mode", action='store_true')
    parser.add_argument("--loop_idx", help="current loop index of uplevel loop calls; if MFG, this argument not used; if EDVT, for snake and eth_prbs, odd index internal loopback, even external loopback", default=1, type=int)

    args = parser.parse_args()

    mtp_id = "MTP-000"
    if args.mtpid:
        mtp_id = args.mtpid
        mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    parameter_cfg_yaml = args.cfgyaml
    stop_on_err = False
    if args.stop_on_error:
        stop_on_err = True
    verbosity = False
    if args.verbosity:
        verbosity = True
    l1_sequence = False
    if args.l1_seq:
        l1_sequence = True
    stage = FF_Stage.FF_P2C
    if args.stage:
        stage = args.stage
    swm_lp_boot_mode = False
    if args.swm:
        swmtestmode = args.swm
        print(" SWMTESTMODE=" + str(swmtestmode))
    loop_idx = args.loop_idx

    low_temp_threshold, high_temp_threshold = libmfg_utils.pick_temperature_thresholds(stage)
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
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=stage)

    try:
        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, stage=stage, skip_test_list=args.skip_test):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
            return

        if MTP_HEALTH_MONITOR:
            thread_health = threading.Thread(target=health_status, args=(mtp_mgmt_ctrl.get_mtp_health_monitor(),))
            thread_health.start()

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
            mtp_test_cleanup(MTP_DIAG_Error.MTP_ENV_SETUP, open_file_track_list)
            return
        # only MFG HT/LT need soaking process
        if stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_4C_L, FF_Stage.FF_4C_H):
            mtp_mgmt_ctrl.mtp_wait_soaking()
        mtp_mgmt_ctrl.cli_log_inf("Diag DDR Test Ambient Temperature Check Complete\n", level=0)

        inlet = mtp_mgmt_ctrl.mtp_get_inlet_temp(low_temp_threshold, high_temp_threshold)
        if stage in (FF_Stage.FF_2C_H, FF_Stage.FF_4C_H, FF_Stage.FF_ORT, FF_Stage.FF_RDT) and inlet > MTP_Const.HIGH_CHAMBER_UPPER_LIMIT:
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP temperature is over 60 degree")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            mtp_test_cleanup(MTP_DIAG_Error.MTP_ENV_SETUP, open_file_track_list)
            return

        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        pass_nic_list = list()
        fail_nic_list = list()

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

        for slot in pass_nic_list:
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM:
                if (mtp_mgmt_ctrl.mtp_get_swmtestmode(slot) in (Swm_Test_Mode.SWMALOM, Swm_Test_Mode.ALOM)):
                    swm_lp_boot_mode=True
                else:
                    swm_lp_boot_mode=False

                if stage not in (FF_Stage.FF_P2C, FF_Stage.QA, FF_Stage.FF_ORT, FF_Stage.FF_RDT):    #Skip SWM Low Power Test for 4C
                    swm_lp_boot_mode=False

        mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Test Start", level=0)

        programmables_checked = False
        if "PROG_UPDATE" in args.skip_test:
            # hook to skip this portion
            programmables_checked = True

        for vmarg_idx, vmarg in enumerate(vmarg_list):
            do_once = 0
            # stop the next vmarg corner if stop_on_err is set and some nic fails
            if fail_nic_list and stop_on_err:
                break

            # track test history for this vmargin
            nic_test_history = {slot: [] for slot in pass_nic_list}

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
            mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment End\n", level=0)

            @parallelize.parallel_nic_using_ssh
            def update_nic_test_history(mtp_mgmt_ctrl, slot, test):
                nic_test_history[slot].append(test)

            def get_slots_of_type(nic_type, except_type=[]):
                return mtp_mgmt_ctrl.get_slots_of_type(nic_type, pass_nic_list, except_type)

            def run_test(nic_list_orig, test, *test_args, **test_kwargs):
                """ If card fails any tests in here, it will be halted and not tested further. Use `run_regression_test`/`run_dsp_test` for other behavior. """

                nic_list = nic_list_orig[:]

                if test in args.skip_test:
                    test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, stage, test)
                    return nic_list

                start_ts = mtp_mgmt_ctrl.log_test_start(test)
                test_utils.test_start_nic_log_message(mtp_mgmt_ctrl, nic_list, stage, test)

                update_nic_test_history(mtp_mgmt_ctrl, nic_list, test)

                if DRY_RUN:
                    rlist = []
                elif test == "NIC_PWRCYC":
                    rlist = mtp_mgmt_ctrl.mtp_power_cycle_nic(nic_list, dl=False)
                elif test == "SALINA_NIC_BOOT_STAGE":
                    rlist = mtp_mgmt_ctrl.mtp_power_cycle_boot_stage(nic_list, bootstage=test_kwargs['bootstage'])
                elif test == "SALINA_NIC_WARM_RESET":
                    rlist = mtp_mgmt_ctrl.mtp_power_cycle_boot_stage(nic_list, bootstage=test_kwargs['bootstage'], warm_reset=test_kwargs['warm_reset'])
                elif test == "SALINA_JTAG_MBIST":
                    rlist = mtp_mgmt_ctrl.mtp_nic_salina_jtag_mbist(nic_list, vmarg=test_kwargs["vmarg"])
                elif test == "SALINA_CONSOLE_GOOGLE_STRESS":
                    rlist = mtp_mgmt_ctrl.mtp_nic_salina_console_google_stress(nic_list, vmarg==test_kwargs["vmarg"], mem_copy_thread=test_kwargs["mem_copy_thread"], seconds2run=test_kwargs["seconds2run"])
                elif test == "SNAKE_SALINA_ASIC_WORK_DIR_PREPARE":
                    rlist = mtp_mgmt_ctrl.mtp_make_copies_of_asic_dir(nic_list, number=test_kwargs["number"])
                elif test == "SNAKE_SALINA_NIC_SNAKE_MTP":
                    rlist = mtp_mgmt_ctrl.mtp_nic_snake_mtp_salina(nic_list, snake_type=test_kwargs["snake_type"], vmarg=test_kwargs["vmarg"], asic_dir_path=test_kwargs["asic_dir_path"])
                elif test == "SNAKE_SALINA_AINIC_SNAKE_MAX_PWR_MTP":
                    rlist = mtp_mgmt_ctrl.mtp_ainic_snake_mtp_salina(nic_list, snake_type=test_kwargs["snake_type"], vmarg=test_kwargs["vmarg"], asic_dir_path=test_kwargs["asic_dir_path"])
                elif test == "SNAKE_SALINA_AINIC_SNAKE_SOR_MTP":
                    rlist = mtp_mgmt_ctrl.mtp_ainic_snake_mtp_salina(nic_list, snake_type=test_kwargs["snake_type"], vmarg=test_kwargs["vmarg"], asic_dir_path=test_kwargs["asic_dir_path"])
                elif test == "SNAKE_SALINA_AINIC_PCIE_PRBS":
                    rlist = mtp_mgmt_ctrl.mtp_nic_pcie_prbs_salina(nic_list, vmarg=test_kwargs["vmarg"], asic_dir_path=test_kwargs["asic_dir_path"])
                elif test == "ADI_NIC_PWRCYC":
                    rlist = mtp_mgmt_ctrl.mtp_power_cycle_nic(adi_type_list, dl=True, count_down=False)

                elif test == "COMPATABILITY_CHECK":
                    rlist = check_compatability(mtp_mgmt_ctrl, nic_list, test_kwargs["mtp_capability"])
                elif test == "CPLD_INIT":
                    rlist = check_cpld_version(mtp_mgmt_ctrl, nic_list)
                elif test == "NIC_BOOT_INIT":
                    rlist = mtp_mgmt_ctrl.mtp_nic_boot_info_init(nic_list)
                elif test == "CPLD_VERIFY":
                    rlist = mtp_mgmt_ctrl.mtp_verify_nic_cpld_console(nic_list, timestamp_check=False) # cant read timestamp from smb
                elif test == "QSPI_VERIFY":
                    rlist = verify_diagfw(mtp_mgmt_ctrl, nic_list)
                elif test == "VDD_DDR_VERIFY":
                    rlist = mtp_mgmt_ctrl.mtp_nic_vdd_ddr_fix_console(nic_list)

                elif test == "TEST_FPGA_PROG":
                    rlist = ncsi_test_fpga_program(mtp_mgmt_ctrl, nic_list)
                elif test == "PROD_FPGA_PROG":
                    rlist = ncsi_prod_fpga_program(mtp_mgmt_ctrl, nic_list)

                elif test == "NIC_DIAG_INIT":
                    rlist = mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, skip_test_list=args.skip_test, vmargin=vmarg, **test_kwargs)
                elif test == "NIC_PARA_MGMT_INIT":
                    rlist = mtp_mgmt_ctrl.mtp_nic_mgmt_para_init(nic_list, aapl=test_kwargs["aapl"])
                elif test == "NIC_PARA_INIT":
                    rlist = mtp_mgmt_ctrl.mtp_nic_para_init(nic_list)
                elif test == "NIC_PARA_EDMA_ENV_INIT":
                    rlist = mtp_mgmt_ctrl.mtp_nic_edma_env_init(nic_list)

                elif test == "L1_SETUP":
                    rlist = mtp_mgmt_ctrl.mtp_l1_setup(nic_list)

                elif test == "PCIE_POLL_DISABLE":
                    rlist = mtp_mgmt_ctrl.mtp_nic_pcie_poll_enable(nic_list, False)
                elif test == "PCIE_POLL_ENABLE":
                    rlist = mtp_mgmt_ctrl.mtp_nic_pcie_poll_enable(nic_list, True)

                elif test == "NIC_JTAG":
                    rlist = mtp_mgmt_ctrl.mtp_check_nic_jtag(nic_list)
                elif test == "NIC_POWER":
                    rlist = mtp_mgmt_ctrl.mtp_check_nic_list_pwr_status(nic_list, test)
                elif test == "NIC_MEM":
                    rlist = mtp_mgmt_ctrl.mtp_mgmt_test_nic_mem(nic_list)
                elif test == "NIC_STATUS":
                    rlist = mtp_mgmt_ctrl.mtp_check_nic_list_status(nic_list)
                elif test == "NIC_DIAG_BOOT":
                    rlist = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(nic_list)
                elif test == "NIC_CPLD":
                    rlist = mtp_mgmt_ctrl.mtp_verify_nic_cpld_console(nic_list)
                elif test == "NIC_FPGA":
                    rlist = mtp_mgmt_ctrl.mtp_verify_nic_cpld_console(nic_list)
                elif test == "NIC_ALOM_CABLE":
                    rlist = mtp_mgmt_ctrl.mtp_nic_naples25swm_alom_cable_signal_test(nic_list, 1)
                elif test == "NIC_N25SWM_CPLD":
                    rlist = mtp_mgmt_ctrl.mtp_nic_naples25swm_cpld_spi_to_smb_reg_test(nic_list)
                elif test == "NIC_OCP_SIGNALS":
                    rlist = mtp_mgmt_ctrl.mtp_nic_naples25ocp_signal_test(nic_list)
                elif test == "NIC_TYPE":
                    rlist = mtp_mgmt_ctrl.mtp_nic_type_test(nic_list)

                elif test == "SWM_LP_MODE":
                    rlist = mtp_mgmt_ctrl.mtp_nic_naples25swm_low_power_mode_test(nic_list)
                elif test == "SALINA_QSPI_PROG":
                    rlist = dl_salina_qspi_program(mtp_mgmt_ctrl, nic_list)
                elif test == "SNAKE_SALINA_NIC_SNAKE_MTP_PREPARE":
                    rlist = mtp_mgmt_ctrl.mtp_untar_snake_qspi_img(nic_list)
                elif test == "SALINA_SNAKE_QSPI_IMG_PROG":
                    rlist = salina_snake_qspi_program(mtp_mgmt_ctrl, nic_list)
                elif test == "SALINA_QSPI_VERIFY":
                    rlist = mtp_mgmt_ctrl.mtp_power_cycle_boot_stage(nic_list, bootstage=test_kwargs["bootstage"])
                elif test == "SALINA_QSPI_ERASE":
                    rlist = salina_erase_qspi(mtp_mgmt_ctrl, nic_list)
                elif test == "DDR_BIST":
                    rlist = diag_seq_ddr_bist_test(mtp_mgmt_ctrl,
                                                    nic_list,
                                                    test_kwargs["ddr_test_db"],
                                                    test_kwargs["test_case"],
                                                    test_kwargs["vmarg"],
                                                    test_kwargs["stop_on_err"],
                                                    test_kwargs["swmtestmode"],
                                                    test_kwargs["l1_sequence"])
                elif test == "POWER_CYCLE_STRESS":
                    rlist = nic_power_cycle_stress_test(mtp_mgmt_ctrl, nic_list, test_kwargs["vmarg"], test_kwargs["stop_on_err"], test_kwargs["iterations"])
                else:
                    mtp_mgmt_ctrl.cli_log_err("Unknown test '{:s}'".format(test))
                    rlist = nic_list

                # catch bad return value
                if not isinstance(rlist, list):
                    mtp_mgmt_ctrl.cli_log_err("Test {} failed with '{}', expected slot list".format(test, repr(rlist)))
                    rlist = nic_list[:]

                rlist = list(set(rlist))

                for slot in nic_list:
                    # keeping old behavior, though old behavior might be wrong
                    if test in ("CPLD_VERIFY", "QSPI_VERIFY"):
                        if slot in rlist:
                            rlist.remove(slot)

                for slot in rlist:
                    mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot, testname=test)
                    if slot in nic_list_orig:
                        nic_list_orig.remove(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)

                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                test_utils.test_fail_nic_log_message(mtp_mgmt_ctrl, rlist, stage, test, start_ts, swmtestmode)
                test_utils.test_pass_nic_log_message(mtp_mgmt_ctrl, nic_list_orig, stage, test, start_ts, swmtestmode)

                if rlist and args.stop_on_error:
                    mtp_mgmt_ctrl.cli_log_err("stop_on_err raised")
                    raise Exception

                return rlist

            def run_regression_test(nic_list_orig, test, dsp=str(stage), *test_args, **test_kwargs):
                """ When card fails these tests, it doesnt halt testing that card """

                nic_list = nic_list_orig[:]
                dsp_disp = dsp[:]
                if dsp != str(stage):
                    if vmarg == Voltage_Margin.high:
                        dsp_disp = "HV_"+dsp
                    elif vmarg == Voltage_Margin.low:
                        dsp_disp = "LV_"+dsp

                if test in args.skip_test:
                    test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, dsp_disp, test)
                    return nic_list
                if dsp in args.skip_test:
                    test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, dsp_disp, test)
                    return nic_list
                if dsp_disp in args.skip_test:
                    test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, dsp_disp, test)
                    return nic_list

                start_ts = mtp_mgmt_ctrl.log_test_start(test)
                test_utils.test_start_nic_log_message(mtp_mgmt_ctrl, nic_list, dsp_disp, test)

                update_nic_test_history(mtp_mgmt_ctrl, nic_list, test)

                if DRY_RUN:
                    rlist = []

                elif test == "NIC_PARA_MGMT_INIT":
                    rlist = mtp_mgmt_ctrl.mtp_nic_mgmt_para_init(nic_list, aapl=test_kwargs["aapl"])
                elif dsp == "MVL" and test == "ACC":
                    rlist = mtp_mgmt_ctrl.mtp_nic_mvl_acc_test(nic_list)
                elif dsp == "MVL" and test == "STUB":
                    rlist = mtp_mgmt_ctrl.mtp_nic_mvl_stub_test(nic_list, test_kwargs["loopback"])
                elif dsp == "MVL" and test == "LINK":
                    rlist = mtp_mgmt_ctrl.mtp_nic_mvl_link_test(nic_list)
                elif dsp == "PHY" and test == "XCVR":
                    rlist = mtp_mgmt_ctrl.mtp_nic_phy_xcvr_test(nic_list)

                elif test == "RMII_LINKUP":
                    rlist = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para_with_oneline_summary(nic_list, test, vmarg)
                elif test == "UART_LPBACK":
                    rlist = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para_with_oneline_summary(nic_list, test, vmarg)

                elif test == "SNAKE_ELBA":
                    rlist = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(nic_list, test, vmarg, edvt_loop_idx=loop_idx)
                elif test == "SNAKE_HBM":
                    rlist = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(nic_list, test, vmarg, edvt_loop_idx=loop_idx)
                elif test == "SNAKE_PCIE":
                    rlist = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(nic_list, test, vmarg, edvt_loop_idx=loop_idx)
                elif test == "ETH_PRBS":
                    rlist = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(nic_list, test, vmarg, edvt_loop_idx=loop_idx)
                elif test == "PCIE_PRBS":
                    rlist = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(nic_list, test, vmarg, edvt_loop_idx=loop_idx)
                elif test == "ARM_L1":
                    rlist = mtp_mgmt_ctrl.mtp_mgmt_run_test_mtp_para(nic_list, test, vmarg, edvt_loop_idx=loop_idx)

                elif test == "L1":
                    rlist = run_j2c_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, str(stage), test_kwargs["l1_sequence"])
                elif test == "L1_OW":
                    rlist = run_j2c_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, str(stage), test_kwargs["l1_sequence"], test_kwargs["joo"], offload=test_kwargs["offload"], ddr=test_kwargs["ddr"])

                elif test == "ASIC_LOG_SAVE":
                    rlist = naples_get_nic_logfile(mtp_mgmt_ctrl, nic_list, nic_test_history)
                elif test == "NIC_LOG_SAVE":
                    rlist = mtp_mgmt_ctrl.mtp_mgmt_save_nic_diag_logfile(nic_list, aapl=test_kwargs["aapl"])

                else:
                    mtp_mgmt_ctrl.cli_log_err("Unknown test '{:s}'".format(test))
                    rlist = nic_list

                # catch bad return value
                if not isinstance(rlist, list):
                    mtp_mgmt_ctrl.cli_log_err("Test {} failed with '{}', expected slot list".format(test, repr(rlist)))
                    rlist = nic_list[:]

                rlist = list(set(rlist))

                for slot in rlist:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        # counts as hard failure
                        if slot in nic_list_orig:
                            nic_list_orig.remove(slot)
                        if slot in pass_nic_list:
                            pass_nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)

                for slot in rlist:

                    # special err msg display
                    err_msg_list = []
                    err_msg_list.append(mtp_mgmt_ctrl.mtp_clear_nic_err_msg(slot))
                    if dsp == "PHY" or dsp == "MVL":
                        err_msg_list.append(mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot))

                    # only display first 3 and last 3 error messages
                    if len(err_msg_list) < 6:
                        err_msg_disp_list = err_msg_list
                    else:
                        err_msg_disp_list = err_msg_list[:3] + err_msg_list[-3:]
                    for err_msg in err_msg_disp_list:
                        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, test, err_msg))
                        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(alom_sn, dsp_disp, test, err_msg))


                    # post-failure analysis
                    if test in ("SNAKE_ELBA", "ETH_PRBS", "PCIE_PRBS", "ARM_L1", "L1"):
                        mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)
                        mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, test, "FAIL", mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot), err_msg_list, skip_vrm_check=False)
                    else:
                        mtp_mgmt_ctrl.mtp_post_dsp_fail_steps(slot, test, "FAIL", mtp_mgmt_ctrl.mtp_get_nic_cmd_buf(slot), err_msg_list)

                pass_test_list = [slot for slot in nic_list_orig if slot not in rlist]
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                test_utils.test_fail_nic_log_message(mtp_mgmt_ctrl, rlist, dsp_disp, test, start_ts, swmtestmode)
                test_utils.test_pass_nic_log_message(mtp_mgmt_ctrl, pass_test_list, dsp_disp, test, start_ts, swmtestmode)

                if rlist and args.stop_on_error:
                    mtp_mgmt_ctrl.cli_log_err("STOP_ON_ERR asserted")
                    raise Exception

                return rlist

            def run_dsp_test(nic_list_orig, test, dsp, *test_args, **test_kwargs):
                """ When card fails these tests, it doesnt halt testing that card """

                nic_list = nic_list_orig[:]
                dsp_disp = dsp[:]
                if dsp != stage:
                    if vmarg == Voltage_Margin.high:
                        dsp_disp = "HV_"+dsp
                    elif vmarg == Voltage_Margin.low:
                        dsp_disp = "LV_"+dsp

                if test in args.skip_test:
                    test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, dsp_disp, test)
                    return nic_list
                if dsp in args.skip_test:
                    test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, dsp_disp, test)
                    return nic_list
                if dsp_disp in args.skip_test:
                    test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, dsp_disp, test)
                    return nic_list

                start_ts = mtp_mgmt_ctrl.log_test_start(test)
                test_utils.test_start_nic_log_message(mtp_mgmt_ctrl, nic_list, dsp_disp, test)

                update_nic_test_history(mtp_mgmt_ctrl, nic_list, test)

                if DRY_RUN:
                    rlist = []

                elif dsp == "MVL" and test == "ACC":
                    rlist = single_nic_dsp_console_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif dsp == "MVL" and test == "STUB":
                    rlist = single_nic_dsp_console_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "PCIE_PRBS" and dsp == "NIC_ASIC":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "ETH_PRBS" and dsp == "NIC_ASIC":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "RTC" and dsp == "RTC":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "EMMC" and dsp == "EMMC":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "I2C" and dsp == "I2C":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "I2C" and dsp == "QSFP":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "I2C" and dsp == "SFP":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "ACC" and dsp == "MVL":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "STUB" and dsp == "MVL":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "DDR_STRESS" and dsp == "MEM":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                elif test == "EDMA" and dsp == "MEM":
                    rlist = single_nic_dsp_ssh_test(mtp_mgmt_ctrl, nic_list, test, dsp, vmarg, swmtestmode)
                else:
                    mtp_mgmt_ctrl.cli_log_err("Unknown test '{:s}'".format(test))
                    rlist = nic_list

                # catch bad return value
                if not isinstance(rlist, list):
                    mtp_mgmt_ctrl.cli_log_err("Test {} failed with '{}', expected slot list".format(test, repr(rlist)))
                    rlist = nic_list[:]

                for slot in rlist:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        # counts as hard failure
                        if slot in nic_list_orig:
                            nic_list_orig.remove(slot)
                        if slot in pass_nic_list:
                            pass_nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)

                for slot in rlist:
                    # special err msg display
                    err_msg_list = []
                    err_msg_list.append(mtp_mgmt_ctrl.mtp_clear_nic_err_msg(slot))

                    # only display first 3 and last 3 error messages
                    if len(err_msg_list) < 6:
                        err_msg_disp_list = err_msg_list
                    else:
                        err_msg_disp_list = err_msg_list[:3] + err_msg_list[-3:]
                    for err_msg in err_msg_disp_list:
                        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, test, err_msg))
                        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(alom_sn, dsp_disp, test, err_msg))


                    # post-failure analysis
                    mtp_mgmt_ctrl.mtp_mgmt_dump_nic_pll_sta(slot)


                pass_test_list = [slot for slot in nic_list_orig if slot not in rlist]
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                test_utils.test_fail_nic_log_message(mtp_mgmt_ctrl, rlist, dsp_disp, test, start_ts, swmtestmode)
                test_utils.test_pass_nic_log_message(mtp_mgmt_ctrl, pass_test_list, dsp_disp, test, start_ts, swmtestmode)

                if rlist and args.stop_on_error:
                    mtp_mgmt_ctrl.cli_log_err("STOP_ON_ERR asserted")
                    raise Exception

                return rlist


            if vmarg_idx > 0:
                mtp_mgmt_ctrl.mtp_diag_dsp_restart()

            if vmarg_idx == 0:
                ######################################################################
                #  One-time steps
                ######################################################################
                run_test(pass_nic_list, "COMPATABILITY_CHECK", mtp_capability=mtp_cfg_db.get_mtp_capability(mtp_id)) # check if MTP support present NIC

                if not programmables_checked and stage in (FF_Stage.FF_P2C, FF_Stage.FF_2C_L, FF_Stage.FF_4C_L):
                    run_test(pass_nic_list, "NIC_PWRCYC")
                    vdd_ddr_check_list = get_slots_of_type([NIC_Type.ORTANO2, NIC_Type.POMONTEDELL])
                    run_test(vdd_ddr_check_list, "VDD_DDR_VERIFY")
                    run_test(pass_nic_list, "CPLD_INIT")
                    # run_test(pass_nic_list, "NIC_BOOT_INIT") # load diagfw version   ######## Not Read yet
                    all_except_cto = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=CTO_MODEL_TYPE_LIST)
                    run_test(all_except_cto, "CPLD_VERIFY")
                    run_test(all_except_cto, "QSPI_VERIFY")

                # Disable PCIe polling
                run_test(pass_nic_list, "NIC_PWRCYC")
                capri_nic_list = get_slots_of_type(CAPRI_NIC_TYPE_LIST)
                if capri_nic_list:
                    mtp_mgmt_ctrl.cli_log_inf("Wait {:02d} seconds for NIC power up before disable PCIE poll".format(MTP_Const.MTP_PCIE_EN_DIS_DELAY), level=0)
                    libmfg_utils.count_down(MTP_Const.MTP_PCIE_EN_DIS_DELAY)
                    mtp_mgmt_ctrl.cli_log_inf("NIC Diag Setup started", level = 0)
                    run_test(capri_nic_list, "PCIE_POLL_DISABLE")
                    mtp_mgmt_ctrl.cli_log_inf("NIC Diag Setup complete\n", level = 0)

                run_test(pass_nic_list, "NIC_DIAG_INIT", swm_lp=swm_lp_boot_mode, nic_util=True, stop_on_err=stop_on_err)
            else:
                run_test(pass_nic_list, "NIC_DIAG_INIT", swm_lp=swm_lp_boot_mode, nic_util=False, stop_on_err=stop_on_err)

            test_section_list = []

            ### CAPRI TEST ORDER
            if get_slots_of_type(CAPRI_NIC_TYPE_LIST):
                test_section_list = ["ALOM_LP_MODE", "PRE_CHECK", "ARM_DSP", "ARM_PRBS", "SNAKE", "J2C_SEQ"]

                if stage not in (FF_Stage.FF_P2C, FF_Stage.QA, FF_Stage.FF_ORT, FF_Stage.FF_RDT):   #Skip SWM Low Power Test for 4 corner
                    test_section_list.remove("ALOM_LP_MODE")

            ### ELBA TEST ORDER
            if get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST):
                test_section_list = ["PRE_CHECK", "MVL", "SNAKE", "ARM_DSP", "NIC_DIAG_INIT", "EDMA", "J2C_SEQ"]
            ### ELBA TEST ORDER WITH SPECIAL NC-SI IMAGE
            if stage == FF_Stage.FF_P2C and get_slots_of_type(FPGA_TYPE_LIST):
                test_section_list.insert(0, "NC-SI")

            ### SALINA TEST ORDER
            if get_slots_of_type(SALINA_NIC_TYPE_LIST):
                test_section_list = ["STRESS", "J2C_SEQ", "SALINA_SNAKE"]

            ### DDR Validation TEST ORDER
            test_section_list = ["DDR_VALIDATION"]

            if args.skip_test:
                test_section_list = libmfg_utils.list_subtract(test_section_list, args.skip_test)
            if args.only_test:
                test_section_list = libmfg_utils.list_intersection(test_section_list, args.only_test)

            for test_section in test_section_list:
                # # check MTP PSU PIN before each test stage
                mtp_mgmt_ctrl.cli_log_inf("Check MTP PSU PIN Before Test Stage", level=0)
                if not mtp_mgmt_ctrl.mtp_psu_init():
                    # Fail all cards
                    mtp_mgmt_ctrl.cli_log_err("PSU PIN Check Failed, Fail All Card Out", level=0)
                    for slot in pass_nic_list[:]:
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
                    for slot in pass_nic_list[:]:
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
                    for slot in pass_nic_list[:]:
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
                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Pre Check Start".format(nic_type), level=0)

                    run_test(pass_nic_list, "NIC_TYPE")
                    run_test(pass_nic_list, "NIC_POWER")
                    run_test(pass_nic_list, "NIC_JTAG")
                    run_test(pass_nic_list, "NIC_STATUS")
                    run_test(pass_nic_list, "NIC_DIAG_BOOT")
                    cpld_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST)
                    run_test(cpld_type_list, "NIC_CPLD")
                    fpga_type_list = get_slots_of_type(FPGA_TYPE_LIST)
                    run_test(fpga_type_list, "NIC_FPGA")
                    ocp_type_list = get_slots_of_type(NIC_Type.NAPLES25OCP)
                    run_test(ocp_type_list, "NIC_OCP_SIGNALS")
                    alom_type_list = get_slots_of_type(NIC_Type.NAPLES25SWM)
                    for slot in alom_type_list[:]:
                        if mtp_mgmt_ctrl.mtp_get_swmtestmode(slot) == Swm_Test_Mode.SWM:
                            alom_type_list.remove(slot)
                    for slot in alom_type_list[:]:
                        if mtp_mgmt_ctrl._swmtestmode[slot] not in (Swm_Test_Mode.SWMALOM, Swm_Test_Mode.ALOM):
                            alom_type_list.remove(slot)
                    run_test(alom_type_list, "NIC_ALOM_CABLE")
                    swm_type_list = get_slots_of_type(NIC_Type.NAPLES25SWM)
                    for slot in swm_type_list[:]:
                        if mtp_mgmt_ctrl._swmtestmode[slot] not in (Swm_Test_Mode.SWMALOM, Swm_Test_Mode.SWM):
                            swm_type_list.remove(slot)
                    run_test(swm_type_list, "NIC_N25SWM_CPLD")

                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Pre Check Complete\n".format(nic_type), level=0)

                elif test_section == "MVL":
                    ######################################################################
                    #
                    #  NIC Sequential test for MVL only
                    #
                    ######################################################################
                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Bash Test Start".format(nic_type), level=0)

                    if stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_4C_L, FF_Stage.FF_4C_H):
                        loopback = False
                    else:
                        loopback = True

                    elba_type_list = get_slots_of_type(ELBA_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST + NO_OOB_MGMT_PORT_TYPE_LIST)
                    run_test(elba_type_list, "NIC_PARA_INIT")
                    run_regression_test(elba_type_list, "ACC", "MVL")
                    run_regression_test(elba_type_list, "STUB", "MVL", loopback=loopback)
                    if loopback:
                        run_regression_test(elba_type_list, "LINK", "MVL")
                    if vmarg == Voltage_Margin.normal:
                        fpga_type_list = get_slots_of_type(FPGA_TYPE_LIST)
                        run_test(fpga_type_list, "NIC_PARA_MGMT_INIT", aapl=False)
                        run_regression_test(fpga_type_list, "XCVR", "PHY")

                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Bash Test Complete\n".format(nic_type), level=0)

                elif test_section == "NC-SI":
                    ######################################################################
                    #
                    #  NIC Parallel test for NC-SI loopback only
                    #
                    ######################################################################
                    fpga_type_list = get_slots_of_type(FPGA_TYPE_LIST)
                    run_test(fpga_type_list, "TEST_FPGA_PROG") # Program NC-SI specific FPGA image
                    run_regression_test(fpga_type_list, "NIC_PARA_MGMT_INIT", aapl=False)
                    run_regression_test(fpga_type_list, "RMII_LINKUP")
                    run_regression_test(fpga_type_list, "UART_LPBACK")
                    run_test(fpga_type_list, "NIC_DIAG_INIT")
                    run_test(fpga_type_list, "PROD_FPGA_PROG") # Program production FPGA image
                    run_test(fpga_type_list, "NIC_DIAG_INIT")

                elif test_section == "SNAKE":
                    ######################################################################
                    #
                    #  NIC MTP Parallel test
                    #
                    ######################################################################
                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Start".format(nic_type), level=0)

                    # run each nic_type separately for now to avoid wrong settings. TODO: allow this to be parallel
                    for cur_nic_type in ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST:
                        snake_type_list = get_slots_of_type(cur_nic_type)
                        if stage not in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_4C_L, FF_Stage.FF_4C_H):
                            run_regression_test(snake_type_list, "ETH_PRBS", "ASIC")
                        run_regression_test(snake_type_list, "PCIE_PRBS", "ASIC")
                        run_regression_test(snake_type_list, "SNAKE_ELBA", "ASIC")
                        run_regression_test(snake_type_list, "ARM_L1", "ASIC")

                    capri_type_list = get_slots_of_type(CAPRI_NIC_TYPE_LIST)
                    for slot in capri_type_list[:]:
                        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            capri_type_list.remove(slot)
                    run_regression_test(capri_type_list, "SNAKE_HBM", "ASIC")
                    run_regression_test(capri_type_list, "SNAKE_PCIE", "ASIC")

                    # re-init diag preparing for next Parallel DSP Test, and copy logfiles out
                    # include failed slots
                    log_save_list = libmfg_utils.list_union(pass_nic_list, fail_nic_list)
                    for slot in log_save_list:
                        mtp_mgmt_ctrl.mtp_hide_nic_status(slot)
                    run_test(log_save_list, "NIC_DIAG_INIT")
                    run_regression_test(log_save_list, "ASIC_LOG_SAVE")
                    for slot in log_save_list:
                        mtp_mgmt_ctrl.mtp_unhide_nic_status(slot)

                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression MTP Parallel Test Complete\n".format(nic_type), level=0)

                elif test_section == "ARM_PRBS":
                    ######################################################################
                    #
                    #  NIC Parallel PRBS tests with HAL/AAPL for Capri
                    #
                    ######################################################################
                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel PRBS Test Start".format(nic_type), level=0)

                    capri_type_list = get_slots_of_type(CAPRI_NIC_TYPE_LIST)
                    for slot in capri_type_list[:]:
                        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            capri_type_list.remove(slot)
                    run_test(capri_type_list, "NIC_DIAG_INIT", aapl=True, dis_hal=True)
                    run_dsp_test(capri_type_list, "PCIE_PRBS", "NIC_ASIC")
                    run_dsp_test(capri_type_list, "ETH_PRBS", "NIC_ASIC")
                    fail_save_list = run_regression_test(capri_type_list, "NIC_LOG_SAVE", aapl=True)
                    for slot in fail_save_list:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Collecting NIC onboard diag logfile failed")

                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel PRBS Test Complete\n".format(nic_type), level=0)

                elif test_section == "ARM_DSP":
                    ######################################################################
                    #
                    #  NIC Parallel DSP tests (no HAL / no AAPL)
                    #
                    ######################################################################
                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel DSP Test Start".format(nic_type), level=0)

                    dsp_test_list = pass_nic_list[:]
                    for slot in dsp_test_list[:]:
                        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            dsp_test_list.remove(slot)
                    run_dsp_test(dsp_test_list, "RTC", "RTC")
                    run_dsp_test(dsp_test_list, "EMMC", "EMMC")
                    run_dsp_test(dsp_test_list, "I2C", "I2C")
                    # Remove QSFP loopbacks in chamber for non-capri
                    if vmarg == Voltage_Margin.normal or stage == FF_Stage.QA:
                        qsfp_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=ETH_25G_TYPE_LIST)
                        run_dsp_test(qsfp_type_list, "I2C", "QSFP")
                    else:
                        # only capri
                        qsfp_type_list = get_slots_of_type(CAPRI_NIC_TYPE_LIST, except_type=ETH_25G_TYPE_LIST)
                        run_dsp_test(qsfp_type_list, "I2C", "QSFP")

                    sfp_type_list = get_slots_of_type(ETH_25G_TYPE_LIST)
                    for slot in sfp_type_list[:]:
                        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            sfp_type_list.remove(slot)
                    run_dsp_test(sfp_type_list, "I2C", "SFP")

                    capri_type_list = get_slots_of_type(CAPRI_NIC_TYPE_LIST)
                    for slot in capri_type_list[:]:
                        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            capri_type_list.remove(slot)
                    run_dsp_test(capri_type_list, "ACC", "MVL")
                    run_dsp_test(capri_type_list, "STUB", "MVL")
                    ddr_type_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST + [NIC_Type.LENI, NIC_Type.LENI48G, NIC_Type.MALFA])
                    run_dsp_test(ddr_type_list, "DDR_STRESS", "MEM")

                    mtp_mgmt_ctrl.cli_log_inf("Collecting NIC onboard diag logfiles...", level=0)
                    run_regression_test(pass_nic_list, "NIC_LOG_SAVE", aapl=False)

                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Parallel DSP Test Complete\n".format(nic_type), level=0)

                elif test_section == "EDMA":
                    ######################################################################
                    #
                    #  EDMA test
                    #
                    ######################################################################
                    ddr_type_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST + [NIC_Type.LENI, NIC_Type.LENI48G, NIC_Type.MALFA])
                    run_test(ddr_type_list, "NIC_PARA_EDMA_ENV_INIT")
                    for ii in range(1,10+1):
                        # 10 iterations without halting on failure
                        run_dsp_test(ddr_type_list, "EDMA", "MEM")
                    run_regression_test(ddr_type_list, "NIC_LOG_SAVE", aapl=False)

                elif test_section == "J2C_SEQ":
                    ######################################################################
                    #
                    #  NIC sequential test
                    #
                    ######################################################################
                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Sequential Test Start".format(nic_type), level=0)

                    adi_type_list = get_slots_of_type([NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT])
                    run_test(adi_type_list, "ADI_NIC_PWRCYC")

                    ######################################################################
                    #  Salina NIC JTAG BIST test
                    ######################################################################
                    jtag_mbist_list = get_slots_of_type(SALINA_NIC_TYPE_LIST)
                    run_test(jtag_mbist_list, "SALINA_JTAG_MBIST", vmarg=vmarg)

                    l1_setup_list = get_slots_of_type(SALINA_NIC_TYPE_LIST)
                    run_test(l1_setup_list, "L1_SETUP")

                    l1_type_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST)
                    for slot in l1_type_list[:]:
                        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                            l1_type_list.remove(slot)

                    run_regression_test(l1_type_list, "L1", "ASIC", l1_sequence=l1_sequence)
                    salina_type_list = get_slots_of_type(SALINA_NIC_TYPE_LIST)
                    run_regression_test(salina_type_list, "L1_OW", "ASIC", l1_sequence=l1_sequence, joo='0', ddr='0', offload='1')

                    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} Diag Regression Sequential Test Complete\n".format(nic_type), level=0)

                elif test_section == "ALOM_LP_MODE":
                    ######################################################################
                    #
                    #  NAPLES25 SWM LOW POWER BOOT MODE TEST
                    #
                    ######################################################################
                    alom_type_list = get_slots_of_type([NIC_Type.NAPLES25SWM])
                    for slot in alom_type_list[:]:
                        if mtp_mgmt_ctrl.mtp_get_swmtestmode(slot) not in (Swm_Test_Mode.SWMALOM, Swm_Test_Mode.ALOM):
                            alom_type_list.remove(slot)

                    run_test(alom_type_list, "SWM_LP_MODE")
                    mtp_mgmt_ctrl.cli_log_inf("Setting Naples25 SWM Back to High Power Mode (requires a nic reboot)", level=0)
                    run_test(alom_type_list, "NIC_DIAG_INIT", swm_lp=False)

                elif test_section == "NIC_DIAG_INIT":
                    ######################################################################
                    #
                    #  NIC Setup
                    #
                    ######################################################################
                    run_test(pass_nic_list, "NIC_DIAG_INIT", dis_hal=True)
                elif test_section == "STRESS":
                    ######################################################################
                    #  Salina NIC Power cycle test
                    ######################################################################
                    for i in range(5):
                        run_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_NIC_BOOT_STAGE", bootstage='linux')
                        run_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_NIC_WARM_RESET", bootstage='linux', warm_reset=True)
                        run_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_NIC_BOOT_STAGE", bootstage="zephyr")
                        run_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_QSPI_VERIFY", bootstage="zephyr", warm_reset=True)

                    ######################################################################
                    #  Salina NIC Google stress  test
                    ######################################################################
                    google_stress_list = get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST)
                    run_test(google_stress_list, "SALINA_NIC_BOOT_STAGE", bootstage='linux')
                    run_test(google_stress_list, "SALINA_CONSOLE_GOOGLE_STRESS", ram2test=None, mem_copy_thread=16, seconds2run=60, logfile=None)
                elif test_section == "SALINA_SNAKE":
                    salina_max_power_snake = get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST)
                    #prog special image
                    run_test(salina_max_power_snake, "SNAKE_SALINA_NIC_SNAKE_MTP_PREPARE")
                    run_test(salina_max_power_snake, "SALINA_SNAKE_QSPI_IMG_PROG")

                    # make copies of asic directory
                    run_test(salina_max_power_snake, "SNAKE_SALINA_ASIC_WORK_DIR_PREPARE", number=5)

                    # run snake test dpu
                    salina_max_power_snake = get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST)
                    max_power_snake = 'esam_pktgen_max_power_pcie_sor'
                    if len(salina_max_power_snake) > 5:
                        salina_max_power_snake_lists = [salina_max_power_snake[0:5], salina_max_power_snake[5:]]
                    else:
                        salina_max_power_snake_lists = [salina_max_power_snake]

                    for salina_max_power_snake_list in salina_max_power_snake_lists:
                        slot2asicdir = dict()
                        for index, slot in enumerate(salina_max_power_snake_list):
                            new_index = index % 5
                            if new_index == 0:
                                dir_path = '/home/diag/diag/asic'
                            else:
                                dir_path = '/home/diag/diag/asic' + str(new_index)
                            slot2asicdir[slot] = dir_path

                        print(slot2asicdir)
                        run_test(salina_max_power_snake_list, "SNAKE_SALINA_NIC_SNAKE_MTP", snake_type=max_power_snake, asic_dir_path=slot2asicdir, vmarg=vmarg)


                    salina_ainic_max_power_snake = get_slots_of_type(SALINA_AI_NIC_TYPE_LIST)
                    run_test(salina_ainic_max_power_snake, "SNAKE_SALINA_NIC_SNAKE_MTP_PREPARE")
                    run_test(salina_ainic_max_power_snake, "SALINA_SNAKE_QSPI_IMG_PROG")
                    # make copies of asic directory ai nic
                    run_test(salina_ainic_max_power_snake, "SNAKE_SALINA_ASIC_WORK_DIR_PREPARE", number=5)
                    run_test(salina_ainic_max_power_snake, "SNAKE_SALINA_AINIC_PCIE_PRBS", asic_dir_path='/home/diag/diag/asic', vmarg=vmarg)

                    # run snake test ai nic
                    salina_ai_max_power_snake = get_slots_of_type(SALINA_AI_NIC_TYPE_LIST)
                    max_power_snake = 'esam_pktgen_pollara_max_power_pcie_arm'
                    if len(salina_ai_max_power_snake) > 5:
                        salina_ai_max_power_snake_lists = [salina_ai_max_power_snake[0:5], salina_ai_max_power_snake[5:]]
                    else:
                        salina_ai_max_power_snake_lists = [salina_ai_max_power_snake]

                    for salina_ai_max_power_snake_list in salina_ai_max_power_snake_lists:
                        slot2asicdir = dict()
                        for index, slot in enumerate(salina_ai_max_power_snake_list):
                            new_index = index % 5
                            if new_index == 0:
                                dir_path = '/home/diag/diag/asic'
                            else:
                                dir_path = '/home/diag/diag/asic' + str(new_index)
                            slot2asicdir[slot] = dir_path

                        print(slot2asicdir)
                        run_test(salina_ai_max_power_snake_list, "SNAKE_SALINA_AINIC_SNAKE_MAX_PWR_MTP", snake_type="esam_pktgen_pollara_max_power_pcie_arm", asic_dir_path=slot2asicdir, vmarg=vmarg)

                    # recovery, prog normal qspi images
                    run_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "SALINA_QSPI_PROG")
                    run_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_QSPI_VERIFY", bootstage='linux')
                    run_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_QSPI_VERIFY", bootstage="zephyr")
                elif test_section == "DDR_VALIDATION":
                    test_case_list = [tc['NAME'] for tc in ddr_suite["TEST_CASE"]]
                    saved_pass_nic_list = pass_nic_list[:]
                    for test_case in test_case_list:
                        if test_case == "DDR_BIST":
                            pass_nic_list = []
                            ######################################################################
                            #  DDR BIST run by NIC sequential test
                            ######################################################################
                            if not stop_on_err:
                                pass_nic_list = saved_pass_nic_list[:]
                            if not pass_nic_list:
                                continue
                            mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} test case start".format(test_case))
                            run_test(pass_nic_list, "DDR_BIST", ddr_test_db=ddr_test_db, test_case=test_case, vmarg=vmarg, stop_on_err=stop_on_err, swmtestmode=swmtestmode, l1_sequence=l1_sequence)
                            mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} test case end".format(test_case))
                        elif test_case == "EDMA#DDR_STRESS":
                            ######################################################################
                            #  EDMA and DDR_STRESS test by diag -r -c 
                            ######################################################################
                            if not stop_on_err:
                                pass_nic_list = saved_pass_nic_list[:]
                            if not pass_nic_list:
                                continue
                            mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} test case start".format(test_case))
                            # multiply by iterations per power cycle
                            iterations_per_pc = ddr_test_db["EDMA#DDR_STRESS"].get("ITER_PER_PC", 1)
                            iterations = ddr_test_db["EDMA#DDR_STRESS"].get("ITER", 1)
                            for ite in range(1, iterations+1):
                                mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} with diag dsp {:s} test {:s} and {:s} In {:d}th Power Cycle Iteration".format(test_case, "MEM", "DDR_STRESS", "EDMA", ite), level=0)
                                # Directely call mtp_nic_diag_init instead of call mtp_nic_diag_init after call mtp_power_cycle_nic since mtp_nic_diag_init will call 
                                # nic_test.py, which will do the power cycle.
                                if ite > 1:
                                    mtp_mgmt_ctrl.cli_log_inf("Calling MTP_NIC_DIAG_INIT To Power Cycle NIC Card and Re-init it ", level=0)
                                    run_test(pass_nic_list, "NIC_DIAG_INIT", nic_util=False, dis_hal=True)
                                run_test(pass_nic_list, "NIC_PARA_EDMA_ENV_INIT")
                                for ite_pc in range(iterations_per_pc):
                                    mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} with diag dsp {:s} test {:s} and {:s} at iteration {:d} In {:d}th Power Cycle Loop".format(test_case, "MEM", "DDR_STRESS", "EDMA", ite_pc, ite), level=0)
                                    run_dsp_test(pass_nic_list, "EDMA", "MEM")
                                    run_dsp_test(pass_nic_list, "DDR_STRESS", "MEM")
                            mtp_mgmt_ctrl.cli_log_inf("Collecting NIC onboard diag logfiles...", level=0)
                            run_regression_test(pass_nic_list, "NIC_LOG_SAVE", aapl=False)
                            mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} test case end".format(test_case))
                        elif test_case == "SNAKE":
                            ######################################################################
                            #  DDR SNAKE TEST run by NIC MTP Parallel test 
                            ######################################################################
                            if not stop_on_err:
                                pass_nic_list = saved_pass_nic_list[:]
                            if not pass_nic_list:
                                continue
                            mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} test case start".format(test_case))
                            iterations_per_pc = ddr_test_db["SNAKE"].get("ITER_PER_PC", 1)
                            iterations = ddr_test_db["SNAKE"].get("ITER", 1)
                            for ite in range(1, iterations+1):
                                mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} In {:d}th Power Cycle Iteration".format(test_case, ite), level=0)
                                # Directely call mtp_nic_diag_init instead of call mtp_nic_diag_init after call mtp_power_cycle_nic since mtp_nic_diag_init will call 
                                # nic_test.py, which will do the power cycle.
                                if ite >= 1:
                                    mtp_mgmt_ctrl.cli_log_inf("Calling MTP_NIC_DIAG_INIT To Power Cycle NIC Card and Re-init it ", level=0)
                                    run_test(pass_nic_list, "NIC_DIAG_INIT", nic_util=True)
                                    for ite_pc in range(iterations_per_pc):
                                        mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} at iteration {:d} In {:d}th Power Cycle Loop".format(test_case, ite_pc, ite), level=0)
                                        for cur_nic_type in ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST + SALINA_DPU_NIC_TYPE_LIST:
                                            snake_type_list = get_slots_of_type(cur_nic_type)
                                            run_regression_test(snake_type_list, "SNAKE_ELBA", "ASIC")

                                        # re-init diag preparing for next Parallel DSP Test, and copy logfiles out
                                        # include failed slots
                                        log_save_list = libmfg_utils.list_union(pass_nic_list, fail_nic_list)
                                        for slot in log_save_list:
                                            mtp_mgmt_ctrl.mtp_hide_nic_status(slot)
                                        run_test(log_save_list, "NIC_DIAG_INIT")
                                        run_regression_test(log_save_list, "ASIC_LOG_SAVE")
                                        for slot in log_save_list:
                                            mtp_mgmt_ctrl.mtp_unhide_nic_status(slot)
                            mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} test case end".format(test_case))
                        elif test_case == "POWER_CYCLE_STRESS":
                            ######################################################################
                            # NIC Power Cycle Only Test
                            ######################################################################
                            if not stop_on_err:
                                pass_nic_list = saved_pass_nic_list[:]
                            if not pass_nic_list:
                                continue
                            mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} test case start".format(test_case))
                            iterations = ddr_test_db["POWER_CYCLE_STRESS"].get("ITER", 1)
                            run_test(pass_nic_list, "POWER_CYCLE_STRESS", vmarg=vmarg, stop_on_err=stop_on_err, iterations=iterations)
                            mtp_mgmt_ctrl.cli_log_inf("DDR Validation:{:s} test case end".format(test_case))

                # print temperature after the test
                if GLB_CFG_MFG_TEST_MODE:
                    mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
                else:
                    mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))

                # # check MTP PSU PIN after each test stage
                mtp_mgmt_ctrl.cli_log_inf("Check MTP PSU PIN After Test Stage", level=0)
                if not mtp_mgmt_ctrl.mtp_psu_init():
                    # Fail all cards
                    mtp_mgmt_ctrl.cli_log_err("PSU PIN Check Failed, Fail All Card Out", level=0)
                    for slot in pass_nic_list[:]:
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
                    for slot in pass_nic_list[:]:
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
                    for slot in pass_nic_list[:]:
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

        if MTP_HEALTH_MONITOR:
            mtp_mgmt_ctrl.get_mtp_health_monitor().set_event_status()
            thread_health.join()

        # Enable PCIe poll
        if not stop_on_err:
            capri_nic_list = get_slots_of_type(CAPRI_NIC_TYPE_LIST)
            if capri_nic_list:
                run_test(capri_nic_list, "NIC_PWRCYC")
                mtp_mgmt_ctrl.cli_log_inf("Wait {:02d} seconds for NIC power up before enable PCIE poll".format(MTP_Const.MTP_PCIE_EN_DIS_DELAY), level=0)
                libmfg_utils.count_down(MTP_Const.MTP_PCIE_EN_DIS_DELAY)
                mtp_mgmt_ctrl.cli_log_inf("NIC Diag Cleanup started", level = 0)
                run_test(capri_nic_list, "PCIE_POLL_ENABLE")
                mtp_mgmt_ctrl.cli_log_inf("NIC Diag Cleanup complete\n", level = 0)

        mtp_mgmt_ctrl.cli_log_inf("MTP DDR Verification Test Complete\n", level=0)

        # since we call it "pass_nic_list" in this file to mean all slots, not just passing ones,
        # have to re-compute pass_nic_list to mean just passing ones
        for slot in fail_nic_list:
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)

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

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        # err_msg = str(e)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)
        if MTP_HEALTH_MONITOR and 'thread_health' in locals():
            mtp_mgmt_ctrl.get_mtp_health_monitor().set_event_status()
            thread_health.join()

    mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_PASS, open_file_track_list)


if __name__ == "__main__":
    main()
