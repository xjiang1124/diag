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
from libdefs import MTP_ASIC_SUPPORT
from libdefs import UUT_Type
from libdefs import MTP_Const
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_IMAGES
from libmfg_cfg import TOR_IMAGES
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db

def logfile_close(filep_list):
    os.system("sync")
    os.system("sync")
    for fp in filep_list:
        fp.close()
    os.system("sync")


def logfile_cleanup(file_list):
    os.system("sync")
    for _file in file_list:
        os.system("rm -rf {:s}".format(_file))
    os.system("sync")

def exit_fail(mtp_mgmt_ctrl, log_filep_list, err_msg=""):
    mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)
    # logfile_close(log_filep_list)
    mtp_mgmt_ctrl.mtp_console_disconnect()

def exit_pass(mtp_mgmt_ctrl, log_filep_list):
    logfile_close(log_filep_list)
    mtp_mgmt_ctrl.mtp_console_disconnect()

def load_mtp_cfg():
    # Same station as DL/P2C right now
    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_tor_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, telnet=False):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    if telnet:
        mtp_ts_cfg = mtp_cfg_db.get_mtp_console(mtp_id)
        if not mtp_ts_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find termserver config")
            return
    else:
        mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
        if not mtp_mgmt_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
            return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, ts_cfg=mtp_ts_cfg, apc_cfg=mtp_apc_cfg, num_of_slots=2, slots_to_skip=mtp_slots_to_skip)
    if telnet:
        mtp_mgmt_ctrl.set_uut_type(UUT_Type.TOR)
    return mtp_mgmt_ctrl

def single_tor_setup(mtp_mgmt_ctrl, uut_id, dsp, skip_test):
    mtp_mgmt_ctrl.print_script_version()

    for test in ["OS_BOOT", "PRESENT_CHECK", "LINK_CHECK", "USB_PRESENT_CHECK", "NIC_INIT", "NIC_MAINFW_SET", "SSH_SETUP", "OS_BOOT"]: #, "NIC_INIT", "MAINFW_VERIFY"]:
        if test in skip_test:
            continue

        start_ts = mtp_mgmt_ctrl.log_test_start(test)

        if test == "PRESENT_CHECK":
            libmfg_utils.cli_log_rslt("Begin Sanity Check .. Please monitor until complete", [], [], mtp_mgmt_ctrl._filep)

        # boot test OS
        if test == "OS_BOOT":
            ret = mtp_mgmt_ctrl.tor_boot_select(1, console_sanity_check=True)
        elif test == "CONSOLE_CLEAR":
            ret = libmfg_utils.mtp_clear_console(mtp_mgmt_ctrl)
        elif test == "CONSOLE_CONNECT":
            ret = mtp_mgmt_ctrl.mtp_console_connect()
        # Sanity check eth loopbacks, psus and fans
        elif test == "PRESENT_CHECK":
            ret = mtp_mgmt_ctrl.tor_present_sanity_check()
        # Sanity check eth loopbacks
        elif test == "LINK_CHECK":
            ret = mtp_mgmt_ctrl.tor_linkup_sanity_check()
        # Sanity check USB
        elif test == "USB_PRESENT_CHECK":
            ret = mtp_mgmt_ctrl.tor_usb_sanity_check()
        elif test == "NIC_INIT":
            ret = mtp_mgmt_ctrl.tor_nic_init()
        elif test == "NIC_MAINFW_SET":
            ret  = mtp_mgmt_ctrl.mtp_mgmt_set_nic_mainfw_boot(0)
            ret &= mtp_mgmt_ctrl.mtp_mgmt_set_nic_mainfw_boot(1)
        elif test == "MAINFW_VERIFY":
            mtp_mgmt_ctrl._nic_ctrl_list[0]._in_mainfw = True
            mtp_mgmt_ctrl._nic_ctrl_list[1]._in_mainfw = True
            ret  = mtp_mgmt_ctrl.tor_nic_fw_verify(0)
            ret &= mtp_mgmt_ctrl.tor_nic_fw_verify(1)
        elif test == "SSH_SETUP":
            ret  = mtp_mgmt_ctrl.mtp_mgmt_clear_nic_ssh(0)
            ret &= mtp_mgmt_ctrl.mtp_mgmt_clear_nic_ssh(1)

        duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)

        if not ret:
            sn = mtp_mgmt_ctrl._sn #refresh to get latest
            mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
            return False

        if test == "USB_PRESENT_CHECK":
            if ret:
                pass_uut_list = [uut_id]
                fail_uut_list = []
            else:
                pass_uut_list = []
                fail_uut_list = [uut_id]
            libmfg_utils.cli_log_rslt("{:s} Sanity Check complete".format(uut_id), pass_uut_list, fail_uut_list, mtp_mgmt_ctrl._filep)

    if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="2C-SSH"):
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

    return True

def single_tor_diag_update(mtp_mgmt_ctrl, uut_id, dsp, skip_test):
    for test in ["TIME_SET", "DIAG_UPDATE", "PYPKG_UPDATE"]:
        if test in skip_test:
            continue

        start_ts = mtp_mgmt_ctrl.log_test_start(test)

        # Sync timestamp to server
        if test == "TIME_SET":
            timestamp_str = str(libmfg_utils.timestamp_snapshot())
            ret = mtp_mgmt_ctrl.mtp_mgmt_set_date(timestamp_str)

        # copy diag image
        elif test == "DIAG_UPDATE":
            asic_type = MTP_ASIC_SUPPORT.ELBA
            x86_image = MTP_IMAGES.AMD64_IMG[asic_type]
            arm_image = MTP_IMAGES.ARM64_IMG[asic_type]
            homedir = mtp_mgmt_ctrl.get_homedir()
            onboard_images = mtp_mgmt_ctrl.mtp_diag_get_img_files(homedir)
            ret = libmfg_utils.mtp_update_diag_image(mtp_mgmt_ctrl, x86_image, arm_image, onboard_images, homedir=homedir)

        # copy python packages
        elif test == "PYPKG_UPDATE":
            homedir = mtp_mgmt_ctrl.get_homedir()
            python_lib_dir = homedir + "python_files/"
            ret = libmfg_utils.mtp_update_packages(mtp_mgmt_ctrl, "release/packages/", python_lib_dir)

        duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)

        if not ret:
            sn = mtp_mgmt_ctrl._sn
            mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
            return False

    return True

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

    if card_type == NIC_Type.TAORMINA:
        seq_test_list = naples_test_db.get_tor_dsp_test_list()
        mtp_mgmt_ctrl.cli_log_inf("TOR DSP Test List:")
    else:
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




def tor_precheck_test(mtp_mgmt_ctrl, vmarg, test_list, skip_testlist):
    test_rslt = True
    if vmarg > 0:
        dsp = "HV_PRE_CHECK"
    elif vmarg < 0:
        dsp = "LV_PRE_CHECK"
    else:
        dsp = "PRE_CHECK"

    for test in test_list:
        sn = mtp_mgmt_ctrl._sn
        mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
        start_ts = mtp_mgmt_ctrl.log_test_start(test)
        ret = mtp_mgmt_ctrl.mtp_mgmt_pre_post_diag_check(test, 0, vmarg)
        duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
        if ret == "SUCCESS":
            mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)
        else:
            mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, ret, duration), level=0)
            test_rslt &= False

    return test_rslt

def tor_diag_binary_test(mtp_mgmt_ctrl, vmarg, test_list, skip_testlist):
    test_rslt = True
    if vmarg > 0:
        dsp = "HV_ASIC"
    elif vmarg < 0:
        dsp = "LV_ASIC"
    else:
        dsp = "ASIC"

    for test in test_list:
        sn = mtp_mgmt_ctrl._sn
        mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), level=0)
        start_ts = mtp_mgmt_ctrl.log_test_start(test)
        ret = mtp_mgmt_ctrl.tor_diag_test_binary(test, vmarg)
        duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)

        if ret:
            mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration), level=0)
        else:
            mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
            test_rslt &= False

            mtp_mgmt_ctrl.tor_dsp_failure_dump()
            if mtp_mgmt_ctrl.hard_failure():
                # stop further testing
                return False

    return test_rslt

def tor_diag_dsp_test(mtp_mgmt_ctrl, vmarg, diag_test_db, test_list, skip_testlist):
    test_rslt = True
    sn = mtp_mgmt_ctrl._sn
    for dsp, test in test_list:
        if vmarg > 0:
            dsp_disp = "HV_" + dsp
        elif vmarg < 0:
            dsp_disp = "LV_" + dsp
        else:
            dsp_disp = dsp

        test_cfg = diag_test_db.get_tor_dsp_test(dsp, test)
        init_cmd = None
        post_cmd = None
        if test_cfg["INIT"] != "":
            init_cmd = test_cfg["INIT"]
        if test_cfg["POST"] != "":
            post_cmd = test_cfg["POST"]
        opts = test_cfg["OPTS"]
        mode = ""
        diag_cmd = diag_test_db.get_diag_tor_test_run_cmd(dsp, test, opts, sn, vmarg, mode)
        rslt_cmd = diag_test_db.get_diag_tor_test_errcode_cmd(dsp, opts)
        mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp_disp, test), level=0)

        if test == "L1":
            mtp_mgmt_ctrl.cli_log_inf("Do not login to the system during this test!")
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("echo $ELBA0_J2C_ID")
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("echo $ELBA1_J2C_ID")

        start_ts = libmfg_utils.timestamp_snapshot()
        ret, err_msg_list = mtp_mgmt_ctrl.mtp_run_diag_test_tor(diag_cmd, rslt_cmd, test, init_cmd, post_cmd)
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)

        # double check the L1 test even it pass
        if dsp == "ASIC" and test == "L1":
            pass_count, log_err_msg_list = mtp_mgmt_ctrl.mtp_mgmt_retrieve_nic_l1_err(sn)
            # Fixed L1 sub test count + err_msg_list should be empty
            number_of_l1_tests = 8
            if mtp_mgmt_ctrl._uut_type == UUT_Type.TOR:
                number_of_l1_tests = 8 * 2
            if pass_count != number_of_l1_tests:
                err_msg_list.append("L1 Sub Test only passed: {:d}".format(pass_count))
                if ret == "SUCCESS":
                    ret = "FAIL"
            if log_err_msg_list:
                err_msg_list += log_err_msg_list

        if ret == "SUCCESS":
            mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp_disp, test, duration), level=0)
        else:
            test_rslt = False
            if dsp == "ASIC" and test == "L1":
                mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("echo $ELBA0_J2C_ID")
                mtp_mgmt_ctrl.cli_log_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
                mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("echo $ELBA1_J2C_ID")
                mtp_mgmt_ctrl.cli_log_err(mtp_mgmt_ctrl.mtp_get_cmd_buf())
            mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp_disp, test, ret, duration), level=0)
            # only display first 3 and last 3 error messages
            if len(err_msg_list) < 6:
                err_msg_disp_list = err_msg_list
            else:
                err_msg_disp_list = err_msg_list[:3] + err_msg_list[-3:]
            for err_msg in err_msg_disp_list:
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG.format(sn, dsp_disp, test, err_msg), level=0)

            mtp_mgmt_ctrl.tor_dsp_failure_dump()
            if mtp_mgmt_ctrl.hard_failure():
                # stop further testing
                return False

    return test_rslt

def save_2c_logs(mtp_mgmt_ctrl, vmarg, uut_test_rslt_list, uut_id, log_dir):
    rslt = True
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
    mtp_script_dir = log_dir
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + diag_sub_dir)
    os.system(cmd)
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + nic_sub_dir)
    os.system(cmd)
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + asic_sub_dir)
    os.system(cmd)
    # save the asic/diag log files
    if rslt and not libmfg_utils.network_get_file(mtp_mgmt_ctrl, mtp_script_dir + diag_sub_dir, MTP_DIAG_Logfile.ONBOARD_DIAG_LOG_FILES):
        mtp_mgmt_ctrl.cli_log_err("Unable to save diag logs")
        rslt = False

    if rslt and not libmfg_utils.network_get_file(mtp_mgmt_ctrl, mtp_script_dir + asic_sub_dir, MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES):
        mtp_mgmt_ctrl.cli_log_err("Unable to save asic logs")
        rslt = False

    if rslt and not libmfg_utils.network_get_file(mtp_mgmt_ctrl, mtp_script_dir + nic_sub_dir, MTP_DIAG_Logfile.ONBOARD_NIC_LOG_FILES):
        mtp_mgmt_ctrl.cli_log_err("Unable to save NIC logs")
        rslt = False

    # save the x86 system logs
    if rslt and not mtp_mgmt_ctrl.tor_copy_sys_log(mtp_script_dir, local_copy=False):
        mtp_mgmt_ctrl.cli_log_err("Unable to save x86 system logs")
        rslt = False

    # clean up logfiles for the next run
    cmd = "cleanup.sh"
    if rslt and not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Log cleanup failed")
        rslt = False

    if not rslt:
        uut_test_rslt_list[uut_id] = False

    sn = mtp_mgmt_ctrl.get_mtp_sn()
    if uut_test_rslt_list[uut_id]:
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(uut_id, NIC_Type.TAORMINA, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

    if not uut_test_rslt_list[uut_id]:
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(uut_id, NIC_Type.TAORMINA, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    # Package this UUT's logfile
    log_sub_dir = os.path.basename(os.path.dirname(log_dir))
    log_pkg_file = "{:s}.tar.gz".format(log_sub_dir)
    cmd = MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format("log/"+log_pkg_file, "log/", log_sub_dir)
    os.system(cmd)

    # move the logs to the log root dir
    sn = mtp_mgmt_ctrl._sn
    nic_type = mtp_mgmt_ctrl._uut_type
    if GLB_CFG_MFG_TEST_MODE:
        mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_2C_LOG_DIR_FMT.format(nic_type, sn)
    else:
        mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_2C_LOG_DIR_FMT.format(nic_type, sn)

    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir))
    libmfg_utils.cli_inf("[{:s}] Collecting log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
    os.system("cp {:s} {:s}".format("log/"+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))
    os.system("./aruba-log.sh {:s}".format(mfg_log_dir+os.path.basename(log_pkg_file)))

    # cleanup the log dir
    logfile_cleanup([log_dir, "log/"+log_pkg_file])


def single_uut_2c_test(stage,
                       uut_id,
                       uut_test_rslt_list,
                       uut_sn_list,
                       log_file_list,
                       verbosity,
                       skip_testlist = []):
    dsp = stage
    if verbosity:
        test_log_filep = None
        diag_log_filep = sys.stdout
        diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
    else:
        test_log_filep = None
        diag_log_filep = None
        diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM

    open_file_track_list = list()
    log_dir = list()

    # Begin test
    mtp_cfg_db = load_mtp_cfg()
    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, uut_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, telnet=True)

    # hardcode all these for now
    card_type = NIC_Type.TAORMINA
    uut_type = UUT_Type.TOR
    asic_type = MTP_ASIC_SUPPORT.ELBA
    x86_image = MTP_IMAGES.AMD64_IMG[asic_type]
    arm_image = MTP_IMAGES.ARM64_IMG[asic_type]
    mtp_mgmt_ctrl.set_homedir(MTP_DIAG_Path.ONBOARD_TOR_DIAG_PATH)
    mtp_mgmt_ctrl._slots = 2

    try:
        for idx, stage in enumerate([FF_Stage.FF_2C_HV, FF_Stage.FF_2C_LV]):
            if stage in skip_testlist:
                continue

            if stage == FF_Stage.FF_2C_HV:
                vmarg = MTP_Const.MFG_EDVT_HIGH_VOLT
            elif stage == FF_Stage.FF_2C_LV:
                vmarg = MTP_Const.MFG_EDVT_LOW_VOLT

            # start new logfile
            log_dir, open_file_track_list = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)

            # only do sanity check on first-time setup
            if idx > 0:
                if "PRESENT_CHECK" not in skip_testlist:
                    skip_testlist.append("PRESENT_CHECK")
                if "LINK_CHECK" not in skip_testlist:
                    skip_testlist.append("LINK_CHECK")
                if "USB_PRESENT_CHECK" not in skip_testlist:
                    skip_testlist.append("USB_PRESENT_CHECK")

            if not single_tor_setup(mtp_mgmt_ctrl, uut_id, stage, skip_testlist):
                uut_test_rslt_list[uut_id] = False
                uut_sn_list[uut_id] = mtp_mgmt_ctrl._sn
                save_2c_logs(mtp_mgmt_ctrl, vmarg, uut_test_rslt_list, uut_id, log_dir)
                continue
            uut_sn_list[uut_id] = mtp_mgmt_ctrl._sn

            if idx == 0:
                if not single_tor_diag_update(mtp_mgmt_ctrl, uut_id, stage, skip_testlist):
                    uut_test_rslt_list[uut_id] = False
                    save_2c_logs(mtp_mgmt_ctrl, vmarg, uut_test_rslt_list, uut_id, log_dir)
                    continue

            sn = mtp_mgmt_ctrl._sn
            mtp_mgmt_ctrl.cli_log_inf("2C Test Started", level=0)
            mfg_2c_start_ts = libmfg_utils.timestamp_snapshot()

            if not mtp_mgmt_ctrl.tor_diag_init(stage, fpo=True):
                uut_test_rslt_list[uut_id] = False
                save_2c_logs(mtp_mgmt_ctrl, vmarg, uut_test_rslt_list, uut_id, log_dir)
                continue

            # reapply the mainfw flag after nic_init
            for slot in range(mtp_mgmt_ctrl._slots):
                mtp_mgmt_ctrl._nic_ctrl_list[slot]._in_mainfw = True
            mtp_mgmt_ctrl._svos_boot = False



            # load the diag test config
            taormina_test_cfg_file = "config/taormina_uut_test_cfg.yaml"
            taormina_test_db = diag_db(stage, taormina_test_cfg_file)
            taormina_pre_test_check_list = taormina_test_db.get_pre_diag_test_intf_list()
            taormina_mtp_para_test_list = taormina_test_db.get_mtp_para_test_list()
            taormina_seq_test_list = taormina_test_db.get_tor_dsp_test_list()
            taormina_para_test_list = taormina_test_db.get_diag_para_test_list()
            taormina_post_test_check_list = taormina_test_db.get_post_diag_test_intf_list()
            nic_type_full_list = [NIC_Type.TAORMINA]
            nic_test_full_list = [range(mtp_mgmt_ctrl._slots)]
            test_db = taormina_test_db
            for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
                naples_diag_cfg_show(nic_type, test_db, mtp_mgmt_ctrl)
                naples_exec_init_cmd(test_db, mtp_mgmt_ctrl)
                naples_exec_skip_cmd(nic_list, test_db, mtp_mgmt_ctrl)
                naples_exec_param_cmd(nic_list, test_db, mtp_mgmt_ctrl)

            fanspd = mtp_mgmt_ctrl.mtp_get_fanspd()
            inlet = mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)
            mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment:", level=0)
            if vmarg > 0:
                mtp_mgmt_ctrl.cli_log_report_inf("******* HV Corner *******")
            elif vmarg < 0:
                mtp_mgmt_ctrl.cli_log_report_inf("******* LV Corner *******")
            else:
                mtp_mgmt_ctrl.cli_log_report_inf("******* NV Corner *******")
            mtp_mgmt_ctrl.cli_log_report_inf("MTP Fan Speed = {:3d}%".format(fanspd))
            if inlet is not None and isinstance(inlet, float):
                mtp_mgmt_ctrl.cli_log_report_inf("UUT temp = {:2.2f}".format(inlet))
            mtp_mgmt_ctrl.cli_log_report_inf("NIC Voltage Margin = {:d}%".format(vmarg))
            mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment End\n", level=0)

            for slot in range(mtp_mgmt_ctrl._slots):
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Initialize NIC info")
                mtp_mgmt_ctrl.mtp_set_nic_sn(slot, mtp_mgmt_ctrl._sn)
                mtp_mgmt_ctrl.mtp_set_nic_pn(slot, mtp_mgmt_ctrl._pn)
                mtp_mgmt_ctrl.mtp_mgmt_verify_nic_sw_boot(slot)

            if not mtp_mgmt_ctrl.tor_set_vmarg(vmarg):
                mtp_mgmt_ctrl.cli_log_err("Failed to voltage margin UUT", level=0)
                uut_test_rslt_list[uut_id] = False
                save_2c_logs(mtp_mgmt_ctrl, vmarg, uut_test_rslt_list, uut_id, log_dir)
                continue

            if not mtp_mgmt_ctrl.mtp_nic_diag_init(vmargin=vmarg, nic_util=True):
                mtp_mgmt_ctrl.cli_log_err("Initialized NIC Diag Environment failed", level=0)
                uut_test_rslt_list[uut_id] = False
                save_2c_logs(mtp_mgmt_ctrl, vmarg, uut_test_rslt_list, uut_id, log_dir)
                continue

            test_section_list = ["PRE_CHECK", "SNAKE", "DSP", "EDMA", "J2C_L1", "TD3"]
            if stage == FF_Stage.FF_2C_LV:
                test_section_list.append("PASSMARK")

            for skipped_test in skip_testlist:
                if skipped_test in test_section_list:
                    test_section_list.remove(skipped_test)

            for test_section in test_section_list:
                if test_section == "PRE_CHECK":
                    if not tor_precheck_test(mtp_mgmt_ctrl, vmarg, taormina_pre_test_check_list, skip_testlist):
                        uut_test_rslt_list[uut_id] = False
                        continue

                elif test_section == "SNAKE":
                    bash_test_list = taormina_mtp_para_test_list[:]
                    if not tor_diag_binary_test(mtp_mgmt_ctrl, vmarg, bash_test_list, skip_testlist):
                        uut_test_rslt_list[uut_id] = False

                elif test_section == "DSP":
                    dsp_test_list = taormina_seq_test_list[:]
                    test_db = taormina_test_db
                    if ("SWITCH", "ELBA_EDMA_TEST") in dsp_test_list:
                        dsp_test_list.remove(("SWITCH", "ELBA_EDMA_TEST"))
                    if ("ASIC", "L1") in dsp_test_list:
                        dsp_test_list.remove(("ASIC", "L1"))
                    if ("BCM", "TD3DIAG") in dsp_test_list:
                        dsp_test_list.remove(("BCM", "TD3DIAG"))
                    if not tor_diag_dsp_test(mtp_mgmt_ctrl, vmarg, test_db, dsp_test_list, skip_testlist):
                        uut_test_rslt_list[uut_id] = False

                elif test_section == "EDMA":
                    dsp_test_list = taormina_seq_test_list[:]
                    test_db = taormina_test_db
                    new_dsp_test_list = list()
                    if ("SWITCH", "ELBA_EDMA_TEST") in dsp_test_list:
                        new_dsp_test_list.append(("SWITCH", "ELBA_EDMA_TEST"))
                    if not tor_diag_dsp_test(mtp_mgmt_ctrl, vmarg, test_db, new_dsp_test_list, skip_testlist):
                        uut_test_rslt_list[uut_id] = False

                elif test_section == "J2C_L1":
                    dsp_test_list = taormina_seq_test_list[:]
                    test_db = taormina_test_db
                    new_dsp_test_list = list()
                    if ("ASIC", "L1") in dsp_test_list:
                        new_dsp_test_list.append(("ASIC", "L1"))
                    if not tor_diag_dsp_test(mtp_mgmt_ctrl, vmarg, test_db, new_dsp_test_list, skip_testlist):
                        uut_test_rslt_list[uut_id] = False

                elif test_section == "TD3":
                    dsp_test_list = taormina_seq_test_list[:]
                    test_db = taormina_test_db
                    new_dsp_test_list = list()
                    if ("BCM", "TD3DIAG") in dsp_test_list:
                        new_dsp_test_list.append(("BCM", "TD3DIAG"))
                    if not tor_diag_dsp_test(mtp_mgmt_ctrl, vmarg, test_db, new_dsp_test_list, skip_testlist):
                        uut_test_rslt_list[uut_id] = False

                elif test_section == "PASSMARK":
                    if uut_test_rslt_list[uut_id]:
                        if not mtp_mgmt_ctrl.tor_fru_passmark(stage):
                            uut_test_rslt_list[uut_id] = False

                else:
                    mtp_mgmt_ctrl.cli_log_err("Unknown 2C Test: {:s}, Ignore".format(test_section))
                    continue

                if mtp_mgmt_ctrl.hard_failure():
                    # stop further testing
                    break



            # log the diag test history
            mtp_mgmt_ctrl.mtp_mgmt_diag_history_disp()
            # clear the diag test history
            mtp_mgmt_ctrl.mtp_mgmt_diag_history_clear()

            mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Test Complete\n", level=0)

            save_2c_logs(mtp_mgmt_ctrl, vmarg, uut_test_rslt_list, uut_id, log_dir)

            mfg_2c_stop_ts = libmfg_utils.timestamp_snapshot()
            libmfg_utils.cli_inf("MFG 2C Test Duration:{:s}".format(mfg_2c_stop_ts - mfg_2c_start_ts))
    
        mtp_mgmt_ctrl.cli_log_inf("2C Test Process Complete", level=0)
        # shut down system
        if not uut_test_rslt_list[uut_id]:
            mtp_mgmt_ctrl.uut_chassis_shutdown()

    except Exception as e:
        uut_test_rslt_list[uut_id] = False
        exit_fail(mtp_mgmt_ctrl, open_file_track_list, traceback.print_exc())
        save_2c_logs(mtp_mgmt_ctrl, vmarg, uut_test_rslt_list, uut_id, log_dir)

def main():
    parser = argparse.ArgumentParser(description="MFG SWI Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", "--uut-id", "--uutid", "-uutid", "-mtpid", help="pre-select UUTs", nargs="*", default=[])

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    ######################################
    mtp_cfg_db = load_mtp_cfg()

    pass_rslt_list = list()
    fail_rslt_list = list()
    log_dir = "log/"
    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir))

    stage = FF_Stage.FF_2C

    uut_id_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)

    ######################################

    pass_uut_list = list()
    fail_uut_list = list()
    uut_test_rslt_list = dict()
    uut_sn_list = dict()
    uut_thread_list = list()
    logfile_dict = dict()

    for uut_id in uut_id_list:
        pass_uut_list.append(uut_id)
        uut_test_rslt_list[uut_id] = True
        uut_sn_list[uut_id] = ""

    for uut_id in uut_id_list:
        if uut_id in fail_uut_list:
            continue

        logfile_dict[uut_id] = list()
        uut_thread = threading.Thread(target = single_uut_2c_test, args = (stage,
                                                                           uut_id,
                                                                           uut_test_rslt_list,
                                                                           uut_sn_list,
                                                                           logfile_dict[uut_id],
                                                                           verbosity,
                                                                           args.skip_test))
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
        if not uut_test_rslt_list[uut_id]:
            if uut_id not in fail_uut_list:
                fail_uut_list.append(uut_id)
            if uut_id in pass_uut_list:
                pass_uut_list.remove(uut_id)

    ######## TEST SUMMARY ########
    test_summary_dict = dict()
    for uut_id in pass_uut_list:
        sn = uut_sn_list[uut_id]
        card_type = NIC_Type.TAORMINA
        test_summary_dict[uut_id] = [(uut_id, sn, card_type, True)]
    
    for uut_id in fail_uut_list:
        sn = uut_sn_list[uut_id]
        card_type = NIC_Type.TAORMINA
        test_summary_dict[uut_id] = [(uut_id, sn, card_type, False)]

    libmfg_utils.mfg_summary_disp(stage, test_summary_dict, [])

    return

if __name__ == "__main__":
    main()

