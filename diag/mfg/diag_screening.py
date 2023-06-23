#!/usr/bin/env python

from email import iterators
import sys
import os
import time
import argparse
import threading

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
import libmtp_utils
from ddr_test_parameters import test2args
from libdefs import NIC_Type
from libdefs import Voltage_Margin
from libdefs import MTP_Const
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import FLEX_SHOP_FLOOR_CONTROL
from libmfg_cfg import FLEX_ERR_CODE_MAP
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db
from libdefs import Swm_Test_Mode

def load_mtp_cfg(suite_name, cfg_yaml=None):

    # stage to MTP chassis cfg file mapping dict
    mtp_chassis_cfg_map = {
        "DL"   : "dl_p2c_mtp_chassis_cfg.yaml",
        "P2C"  : "dl_p2c_mtp_chassis_cfg.yaml",
        "2C"   : "4c_mtp_chassis_cfg.yaml",
        "4C"   : "4c_mtp_chassis_cfg.yaml",
        "SWI"  : "swi_mtp_chassis_cfg.yaml",
        "FST"  : "fst_mtps_chassis_cfg.yaml",
        "DDR"  : ""
    }
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    yaml_file_name = mtp_chassis_cfg_map.get(suite_name, "")
    if yaml_file_name:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/" + yaml_file_name))
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath(cfg_yaml))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db

def mtp_test_cleanup(error_code, fp_list=None):
    if fp_list:
        for fp in fp_list:
            fp.close()
    os.system("sync")

def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg, slots_to_skip=mtp_slots_to_skip)
    return mtp_mgmt_ctrl

def single_mtp_ddr_test(mtp_script_dir, mtp_mgmt_ctrl, mtp_id, stage, fail_nic_list, mtp_test_summary, swm_test_mode, l1_sequence, test_suite_cfg, vmarg, stop_on_err, iteration=1):

    if fail_nic_list:
        fail_slots = " --fail-slots "
        fail_slots += ' '.join(map(str,fail_nic_list))
    else:
        fail_slots = ""

    for loop in range(1, iteration+1):
        mtp_mgmt_ctrl.cli_log_inf("DDR Test Iteration-{:03d} start".format(loop), level=0)

        mfg_4c_start_ts = libmfg_utils.timestamp_snapshot()

        # go to mtp_regression and Start the regression
        cmd = "cd {:s}".format(mtp_script_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        mtp_start_ts = libmfg_utils.timestamp_snapshot()
        mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
        if stage == FF_Stage.FF_2C_H:
            env_temp = "High Temperature"
            cmd = "./diag_screening_ddr.py --mtpid {:s} --stage {:s} --swm {:s}".format(mtp_id, FF_Stage.FF_2C_H, swm_test_mode)
        elif stage == FF_Stage.FF_2C_L:
            env_temp = "High Temperature"
            cmd = "./diag_screening_ddr.py --mtpid {:s} --stage {:s} --swm {:s}".format(mtp_id, FF_Stage.FF_2C_L, swm_test_mode)
        else:
            env_temp = "Room Temperature"
            cmd = "./diag_screening_ddr.py --mtpid {:s} --stage {:s} --swm {:s}".format(mtp_id, FF_Stage.FF_P2C, swm_test_mode)
        if fail_slots:
            cmd += fail_slots
        if test_suite_cfg:
            cmd += " --cfgyaml " + test_suite_cfg
        if l1_sequence:
            cmd += " --l1-seq "
        if stop_on_err:
            cmd += " --stop_on_error"
        if vmarg:
            cmd += " --vmarg " + " ".join(vmarg)
        
        mtp_mgmt_ctrl.cli_log_inf("DDR Test At {:s} Start ...".format(env_temp), level=0)
        mtp_mgmt_ctrl.cli_log_inf("Calling Command {:s}".format(cmd), level=0)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_4C_TEST_TIMEOUT)
        mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
        mtp_mgmt_ctrl.cli_log_inf("\n", level=0)
        mtp_mgmt_ctrl.cli_log_inf("DDR Test At {:s} Complete".format(stage), level=0)
        mtp_stop_ts = libmfg_utils.timestamp_snapshot()

        test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_script_dir, mtp_id, mtp_test_summary, stage, vmarg)
        if not test_log_file:
            mtp_mgmt_ctrl.cli_log_err("MTP Collect {:s} Test result failed".format(stage), level=0)
            return
        libmfg_utils.assign_nic_retest_flag(test_log_file, mtp_test_summary, stage)
        if GLB_CFG_MFG_TEST_MODE:
            libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, stage, mtp_test_summary)
        cmd = "rm -rf {:s}".format(test_log_file)
        os.system(cmd)

        mfg_4c_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("DDR Test At {:s} Test Duration:{:s}".format(env_temp, mfg_4c_stop_ts - mfg_4c_start_ts))

        libmfg_utils.mfg_summary_disp(stage, {mtp_id: mtp_test_summary}, [])

        #mtp_mgmt_ctrl.mtp_chassis_shutdown()

        if loop != iteration:
            mtp_mgmt_ctrl.mtp_apc_pwr_on()
            mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
            libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
            if not mtp_mgmt_ctrl.mtp_mgmt_connect():
                mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
                return
            else:
                mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

    return

def single_mtp_emmc_test(mtp_script_dir, mtp_mgmt_ctrl, mtp_id, stage, fail_nic_list, mtp_test_summary, swm_test_mode, test_suite_cfg, stop_on_err):

    if fail_nic_list:
        fail_slots = " --fail-slots "
        fail_slots += ' '.join(map(str, fail_nic_list))
    else:
        fail_slots = ""

    mfg_emmc_start_ts = libmfg_utils.timestamp_snapshot()

    # go to mtp_regression directory and Start the regression
    cmd = "cd {:s}".format(mtp_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
    if stage == FF_Stage.FF_2C_H:
        env_temp = "High Temperature"
        cmd = "./diag_screening_emmc.py --mtpid {:s} --stage {:s} --swm {:s}".format(mtp_id, FF_Stage.FF_2C_H, swm_test_mode)
    elif stage == FF_Stage.FF_2C_L:
        env_temp = "High Temperature"
        cmd = "./diag_screening_emmc.py --mtpid {:s} --stage {:s} --swm {:s}".format(mtp_id, FF_Stage.FF_2C_L, swm_test_mode)
    else:
        env_temp = "Room Temperature"
        cmd = "./diag_screening_emmc.py --mtpid {:s} --stage {:s} --swm {:s}".format(mtp_id, FF_Stage.FF_P2C, swm_test_mode)
    if fail_slots:
        cmd += fail_slots
    if test_suite_cfg:
        cmd += " --cfgyaml " + test_suite_cfg
    if stop_on_err:
        cmd += " --stop_on_error"

    mtp_mgmt_ctrl.cli_log_inf("EMMC Validation Test At {:s} Start ...".format(env_temp), level=0)
    mtp_mgmt_ctrl.cli_log_inf("Calling Command {:s}".format(cmd), level=0)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_4C_TEST_TIMEOUT)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("\n", level=0)
    mtp_mgmt_ctrl.cli_log_inf("EMMC Validation Test At {:s} Complete".format(stage), level=0)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    test_log_file = libmfg_utils.get_mtp_logfile(
        mtp_mgmt_ctrl, mtp_script_dir, mtp_id, mtp_test_summary, stage)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err(
            "MTP Collect {:s} Test result failed".format(stage), level=0)
        return
    libmfg_utils.assign_nic_retest_flag(test_log_file, mtp_test_summary, stage)
    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts,
                                mtp_stop_ts, test_log_file, stage, mtp_test_summary)
    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)

    mfg_emmc_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("EMMC Validation Test At {:s} Test Duration:{:s}".format(
        env_temp, mfg_emmc_stop_ts - mfg_emmc_start_ts))

    libmfg_utils.mfg_summary_disp(stage, {mtp_id: mtp_test_summary}, [])

    # mtp_mgmt_ctrl.mtp_chassis_shutdown()

    # May need process data here
    #
    #

    return


def get_test_arguments(test_case_name=None, part_number=None):

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

def run_ddr_test_suite(args):
    verbosity = args.verbosity
    parameter_cfg_yaml = args.cfgyaml
    test_suite = args.suite.upper()
    l1_sequence = args.l1_seq
    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    # Display DDR test suite test cases
    ddr_suite = libmfg_utils.load_cfg_from_yaml_file_list([parameter_cfg_yaml])
    libmfg_utils.cli_inf("Running TEST SUITE: {:s} With Following Test Case".format(ddr_suite["TEST_SUITE_NAME"]))
    for test_case in ddr_suite["TEST_CASE"]:
        libmfg_utils.cli_inf("Test Case: {:s} With {:d} Iterations".format(test_case["NAME"], test_case["ITER"]))

    if verbosity:
        diag_log_filep = sys.stdout
        diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
    else:
        diag_log_filep = None
        diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM

    mtp_cfg_db = load_mtp_cfg(test_suite)
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
    mtpid_fail_list = list()
    mtp_mgmt_ctrl_list = list()
    fail_nic_list = dict()
    nic_sn_list = dict()
    invalid_nic_list = dict()

    # init mtp_ctrl list
    for mtp_id in mtpid_list:
        if verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list)
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)
        fail_nic_list[mtp_id] = list()
        nic_sn_list[mtp_id] = list()
        invalid_nic_list[mtp_id] = list()

    # wait operator set chamber temperature
    if args.high_temp:
        libmfg_utils.cli_inf("RUNNING TEST WITH TEMPERATURE SET TO {:d} DEGREE CENTIGRADE\n".format(MTP_Const.MFG_EDVT_HIGH_TEMP))
        stage = FF_Stage.FF_2C_H
    elif args.low_temp:
        libmfg_utils.cli_inf("RUNNING TEST WITH TEMPERATURE SET TO TO {:d} DEGREE CENTIGRADE\n".format(MTP_Const.MFG_EDVT_LOW_TEMP))
        stage = FF_Stage.FF_2C_L
    else:
        libmfg_utils.cli_inf("RUNNING TEST WITH ROOM TEMPERATURE\n")
        stage = FF_Stage.FF_P2C

    # logfiles
    open_file_track_mtp_list = dict()
    logfile_dir_list = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id] = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list, safely=False)
    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not libmfg_utils.mtp_common_setup_fpo(mtp_mgmt_ctrl, stage, args.skip_test):
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)
        mtp_mgmt_ctrl.mtp_get_memory_size()

    # type check
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list[mtp_id]:
                continue
            test = "NIC_TYPE"
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            ret = mtp_mgmt_ctrl.mtp_nic_type_test(slot)
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, "DDR", test, "FAILED", duration))
                if slot not in fail_nic_list[mtp_id]:
                    fail_nic_list[mtp_id].append(slot)

    # close file handles
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])
    for mtp_id in mtpid_fail_list:
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])

    # Copy script, config file on to each MTP Chassis
    mtp_diag_screening_script_dir = "mtp_regression/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        ddr_script_pkg = "mtp_diag_screening_script.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP {:s} Test script".format("DDR"), level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_diag_screening_script_dir, ddr_script_pkg, logfile_dir_list[mtp_id]):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP {:s} Test script failed".format("DDR"), level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Deploy MTP {:s} Test script complete".format("DDR"), level=0)


    mtp_thread_list = list()
    ddr_test_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        ddr_test_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_ddr_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_diag_screening_script_dir,
                                                                           mtp_mgmt_ctrl,
                                                                           mtp_id,
                                                                           stage,
                                                                           fail_nic_list[mtp_id],
                                                                           ddr_test_summary[mtp_id],
                                                                           swmtestmode,
                                                                           l1_sequence,
                                                                           args.cfgyaml,
                                                                           args.vmarg,
                                                                           args.stop_on_error,
                                                                           args.iteration))
        mtp_thread.daemon = True
        mtp_thread.start()
        mtp_thread_list.append(mtp_thread)
        time.sleep(2)

    # monitor all the thread
    while True:
        if len(mtp_thread_list) == 0:
            break
        for mtp_thread in mtp_thread_list[:]:
            if not mtp_thread.is_alive():
                mtp_thread.join()
                mtp_thread_list.remove(mtp_thread)
        time.sleep(5)

def run_emmc_test_suite(args):
    verbosity = args.verbosity
    parameter_cfg_yaml = args.cfgyaml
    test_suite = args.suite.upper()
    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    # Display EMMC test suite test cases
    ddr_suite = libmfg_utils.load_cfg_from_yaml_file_list([parameter_cfg_yaml])
    libmfg_utils.cli_inf("Running TEST SUITE: {:s} With Following Test Case {:d} Iterations".format(
        ddr_suite["TEST_SUITE_NAME"], ddr_suite["ITER"]))
    for test_case in ddr_suite["TEST_CASE"]:
        libmfg_utils.cli_inf("Test Case: {:s}".format(test_case["NAME"]))

    if verbosity:
        diag_log_filep = sys.stdout
        diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
    else:
        diag_log_filep = None
        diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM

    mtp_cfg_db = load_mtp_cfg(test_suite)
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
    mtpid_fail_list = list()
    mtp_mgmt_ctrl_list = list()
    fail_nic_list = dict()
    nic_sn_list = dict()
    invalid_nic_list = dict()

    # init mtp_ctrl list
    for mtp_id in mtpid_list:
        if verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(
            mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list)
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)
        fail_nic_list[mtp_id] = list()
        nic_sn_list[mtp_id] = list()
        invalid_nic_list[mtp_id] = list()

    # wait operator set chamber temperature
    if args.high_temp:
        libmfg_utils.cli_inf("RUNNING TEST WITH TEMPERATURE SET TO {:d} DEGREE CENTIGRADE\n".format(
            MTP_Const.MFG_EDVT_HIGH_TEMP))
        stage = FF_Stage.FF_2C_H
    elif args.low_temp:
        libmfg_utils.cli_inf("RUNNING TEST WITH TEMPERATURE SET TO TO {:d} DEGREE CENTIGRADE\n".format(
            MTP_Const.MFG_EDVT_LOW_TEMP))
        stage = FF_Stage.FF_2C_L
    else:
        libmfg_utils.cli_inf("RUNNING TEST WITH ROOM TEMPERATURE\n")
        stage = FF_Stage.FF_P2C

    # logfiles
    open_file_track_mtp_list = dict()
    logfile_dir_list = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id] = libmfg_utils.open_logfiles(
            mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)

    # power off all the test mtp
    #libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list, safely=False)
    # power on the mtp chassis
    # libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not libmfg_utils.mtp_common_setup_fpo(mtp_mgmt_ctrl, stage, args.skip_test):
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)
        mtp_mgmt_ctrl.mtp_get_memory_size()

    # type check
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list[mtp_id]:
                continue
            test = "NIC_TYPE"
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
            ret = mtp_mgmt_ctrl.mtp_nic_type_test(slot)
            duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(
                    sn, "EMMC", test, "FAILED", duration))
                if slot not in fail_nic_list[mtp_id]:
                    fail_nic_list[mtp_id].append(slot)

    # close file handles
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])
    for mtp_id in mtpid_fail_list:
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])

    # Copy script, config file on to each MTP Chassis
    mtp_diag_screening_script_dir = "mtp_regression/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        ddr_script_pkg = "mtp_diag_screening_script.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf(
            "Start deploy MTP {:s} Test script".format("EMMC"), level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_diag_screening_script_dir, ddr_script_pkg, logfile_dir_list[mtp_id]):
            mtp_mgmt_ctrl.cli_log_err(
                "Deploy MTP {:s} Test script failed".format("EMMC"), level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf(
                "Deploy MTP {:s} Test script complete".format("EMMC"), level=0)

    mtp_thread_list = list()
    ddr_test_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        ddr_test_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target=single_mtp_emmc_test, args=(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_diag_screening_script_dir,
                                                                         mtp_mgmt_ctrl,
                                                                         mtp_id,
                                                                         stage,
                                                                         fail_nic_list[mtp_id],
                                                                         ddr_test_summary[mtp_id],
                                                                         swmtestmode,
                                                                         args.cfgyaml,
                                                                         args.stop_on_error))
        mtp_thread.daemon = True
        mtp_thread.start()
        mtp_thread_list.append(mtp_thread)
        time.sleep(2)

    # monitor all the thread
    while True:
        if len(mtp_thread_list) == 0:
            break
        for mtp_thread in mtp_thread_list[:]:
            if not mtp_thread.is_alive():
                mtp_thread.join()
                mtp_thread_list.remove(mtp_thread)
        time.sleep(5)


def run_dl_tests(args):

    print("running DL testing with following arguments")
    print(args)
    return True

def run_p2c_tests(args):

    print("running P2C testing with following arguments")
    print(args)
    return True

def run_4c_tests(args):

    print("running 4C testing with following arguments")
    print(args)
    return True

def run_swi_tests(args):

    print("running SWI testing with following arguments")
    print(args)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic Test Main Entry", epilog='''Examples: %(prog)s DDR --type BIST\n          %(prog)s P2C --mtpid MTP-100''', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    subparsers = parser.add_subparsers(title="subcommands list", dest="suite", description="'%(prog)s {subcommand} --help' for detail usage of specified subcommand", help='sub-command description')
    #aliases only support in python2.7
    #parser_ddr = subparsers.add_parser('ddr', aliases=["DDR", "dDr"], help='invoke DDR memory test suite')
    parser_ddr = subparsers.add_parser('ddr', help='invoke DDR Validation test suite')
    parser_emmc = subparsers.add_parser('emmc', help='invoke EMMC Validation test suite')
    parser_dl = subparsers.add_parser('dl', help='invoke Download test suite')
    parser_p2c = subparsers.add_parser('p2c', help='invoke Pre 2 Coner test suite')
    parser_4c = subparsers.add_parser('4c', help='invoke 4 Coner test suite')
    parser_swi = subparsers.add_parser('swi', help='invoke SWI test suite')

    parser_ddr.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser_ddr.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser_ddr.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser_ddr.add_argument("--high-temp", help="high temperature environment", action='store_true')
    parser_ddr.add_argument("--low-temp", help="low temperature environment", action='store_true')
    parser_ddr.add_argument("--iteration", help="Iteration to run with MTP power cycle", type=int, required=False, default=1)
    parser_ddr.add_argument("--l1-seq", help="asic L1 run under sequence mode", action='store_true')
    parser_ddr.add_argument("--vmarg", help="specify the vmargin, deduced from environment temperature(normal temperature => no voltage margin; low/high temperature => low and low voltage margin) if not specified", nargs="*",  choices=["normal", "high", "low"], default=[])
    parser_ddr.add_argument("--stop_on_error", help="leave the MTP in error state if error happens", action='store_true')
    parser_ddr.add_argument("-cfg", "--cfgyaml", help="Test case config file for DDR Validation test suite, default to %(default)s", default="./config/ddr_test_suite.yaml")
    parser_ddr.set_defaults(func=run_ddr_test_suite)

    parser_emmc.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser_emmc.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser_emmc.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    group_emmc = parser_emmc.add_mutually_exclusive_group()
    group_emmc.add_argument("--high-temp", help="high temperature environment with both low and high voltage margin", action='store_true')
    group_emmc.add_argument("--low-temp", help="low temperature environment with both low and high voltage margin", action='store_true')
    #parser_emmc.add_argument("--iteration", help="Iteration to run with MTP power cycle", type=int, required=False, default=1)
    #parser_emmc.add_argument("--vmarg", help="specify the vmargin, deduced from environment temperature(normal temperature => no voltage margin; low/high temperature => low and high voltage margin) if not specified", nargs="*",  choices=["normal", "high", "low"], default=[])
    parser_emmc.add_argument("--stop_on_error", help="leave the MTP in error state if error happens", action='store_true')
    parser_emmc.add_argument("-cfg", "--cfgyaml", help="Test case config file for EMMC Validation test suite, default to %(default)s", default="./config/emmc_test_suite.yaml")
    parser_emmc.set_defaults(func=run_emmc_test_suite)

    parser_dl.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser_dl.add_argument("-r", "--rework", help="Call rework script", action='store_true')
    parser_dl.add_argument("--swm", help="SWM test mode")
    #parser_dl.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser_dl.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser_dl.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser_dl.set_defaults(func=run_dl_tests)

    parser_p2c.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser_p2c.add_argument("--swm", help="SWM test mode")
    # parser_p2c.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser_p2c.add_argument("--skip-test", help="skip a particular test or test section", nargs="*", default=[])
    parser_p2c.add_argument("--only-test", help="run particular tests only", nargs="*", default=[])
    parser_p2c.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser_p2c.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser_p2c.add_argument("--l1-seq", help="asic L1 run under sequence mode", action='store_true')
    parser_p2c.set_defaults(func=run_p2c_tests)

    parser_4c.add_argument("--high-temp", help="high temperature environment", action='store_true')
    parser_4c.add_argument("--low-temp", help="low temperature environment", action='store_true')
    parser_4c.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser_4c.add_argument("--swm", help="SWM test mode")
    #parser_4c.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser_4c.add_argument("--skip-test", help="skip a particular test or test section", nargs="*", default=[])
    parser_4c.add_argument("--only-test", help="run particular tests only", nargs="*", default=[])
    parser_4c.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser_4c.add_argument("--l1-seq", help="asic L1 run under sequence mode", action='store_true')
    parser_4c.add_argument("--iteration", help="Iteration to run with MTP power cycle", type=int, required=False, default=1)
    parser_4c.set_defaults(func=run_4c_tests)

    parser_swi.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser_swi.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser_swi.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser_swi.add_argument("--sw-pn", "-swpn", "--swpn", "-sw-pn", help="pre-select SW PN", default="")
    parser_swi.set_defaults(func=run_swi_tests)

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)
        #parser.exit(status=1, message=parser.print_help())

    sys.exit(not args.func(args))


