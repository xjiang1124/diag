#!/usr/bin/env python

import sys
import os
import time
import datetime
import pexpect
import threading
import argparse
import re

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libpro_srv_db import pro_srv_db


def get_mtp_logfile(mtp_mgmt_ctrl, log_dir, mtp_id, mtp_test_summary):
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]

    mtp_mgmt_ctrl.cli_log_inf("Collecting log files started", level=0)

    # create the log subdir
    log_timestamp = libmfg_utils.get_timestamp()
    sub_dir = MTP_DIAG_Logfile.MFG_KPT_LOG_DIR.format(mtp_id, log_timestamp)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir+sub_dir))

    # log pkg filename
    log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_KPT_LOG_PKG_FILE.format(mtp_id, log_timestamp)

    # need to be sync'd with cleanup.sh
    test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_KPT_LOG_FILES

    # kpt test logs
    logfile_list = list()
    # diag onboard log files
    cmd = "mv {:s} {:s}".format(test_onboard_log_files, log_dir+sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    # all the test logs
    test_log_file = "{:s}test_kpt.log".format(log_dir+sub_dir)

    # pkg the onboard logs
    cmd = MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format(log_pkg_file, log_dir, sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    local_test_log_file = "log/{:s}_test_kpt.log".format(mtp_id)
    libmfg_utils.network_get_file(ipaddr, userid, passwd, local_test_log_file, test_log_file)

    with open(local_test_log_file, 'r') as fp:
        buf = fp.read()
    nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
    nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
    fail_match = re.findall(nic_fail_reg_exp, buf)
    pass_match = re.findall(nic_pass_reg_exp, buf)

    for slot, nic_type, sn in fail_match + pass_match:
        if GLB_CFG_MFG_TEST_MODE:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_KPT_LOG_DIR_FMT.format(nic_type, sn)
        else:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_KPT_LOG_DIR_FMT.format(nic_type, sn)

        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir)
        os.system(cmd)
        # copy the onboard logs
        ts = libmfg_utils.get_timestamp()
        qa_log_pkg_file = mfg_log_dir + os.path.basename(log_pkg_file)
        mtp_mgmt_ctrl.cli_log_inf("Collecting {:s} log files {:s}".format(sn, qa_log_pkg_file))
        libmfg_utils.network_get_file(ipaddr, userid, passwd, qa_log_pkg_file, log_pkg_file)

    for slot, nic_type, sn in fail_match:
        mtp_test_summary.append((slot, sn, nic_type, False))

    for slot, nic_type, sn in pass_match:
        mtp_test_summary.append((slot, sn, nic_type, True))

    # clear the onboard logs
    logfile_list.append(log_pkg_file)
    logfile_list.append(log_dir+sub_dir)
    cmd = "rm -rf {:s}".format(" ".join(logfile_list))
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    mtp_mgmt_ctrl.cli_log_inf("Collecting log files complete", level=0)

    return local_test_log_file


def mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    duration = mtp_stop_ts - mtp_start_ts

    with open(test_log_file, 'r') as fp:
        buf = fp.read()

    # MTP related error, don't post any report
    if MTP_DIAG_Report.MTP_DIAG_REGRESSION_FAIL in buf:
        libmfg_utils.cli_inf(mtp_cli_id_str + "MTP Setup fails, no report will be generated")
        return

    libmfg_utils.cli_inf(mtp_cli_id_str + "Start posting test report")
    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL in buf:
        nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
        match = re.findall(nic_fail_reg_exp, buf)
        for slot, nic_type, sn in match:
            test_list = list()
            test_rslt_list = list()
            err_dsc_list = list()
            err_code_list = list()
            nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
            # find all test status
            nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
            sub_match = re.findall(nic_test_rslt_reg_exp, buf)
            for dsp, test, result in sub_match:
                test_list.append("{:s}-{:s}".format(dsp, test))
                test_rslt_list.append(result)
                err_dsc_list.append(nic_cli_id_str)
                err_code_list.append(result)
            ret = libmfg_utils.flx_web_srv_post_uut_report("KPT", nic_type, sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list)
            if not ret:
                libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
            else:
                libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))

    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS in buf:
        nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
        match = re.findall(nic_pass_reg_exp, buf)
        for slot, nic_type, sn in match:
            test_list = list()
            test_rslt_list = list()
            err_dsc_list = list()
            err_code_list = list()
            nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
            # find all test status
            nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
            sub_match = re.findall(nic_test_rslt_reg_exp, buf)
            for dsp, test, result in sub_match:
                test_list.append("{:s}-{:s}".format(dsp, test))
                test_rslt_list.append(result)
                err_dsc_list.append(nic_cli_id_str)
                err_code_list.append(result)
            ret = libmfg_utils.flx_web_srv_post_uut_report("KPT", nic_type, sn, "PASS", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list)
            if not ret:
                libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
            else:
                libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))


def load_mtp_cfg():
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/kpt_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db


def get_mtpid_list(mtp_cfg_db):
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    sub_mtpid_list = libmfg_utils.multiple_select_menu("Select MTP Chassis", mtpid_list)
    return sub_mtpid_list


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg)
    return mtp_mgmt_ctrl


def mtp_script_pkg_init(mtp_kpt_script_dir, mtp_kpt_script_pkg):
    cmd = "cp -r lib/ config/ {:s}".format(mtp_kpt_script_dir)
    os.system(cmd)
    cmd = "tar czf {:s} {:s}".format(mtp_kpt_script_pkg, mtp_kpt_script_dir)
    os.system(cmd)
    # remove the lib config for the next run
    cmd = "rm -rf {:s}/lib {:s}/config".format(mtp_kpt_script_dir, mtp_kpt_script_dir)
    os.system(cmd)


def mtp_download_test_script(mtp_mgmt_ctrl, mtp_kpt_script_pkg):
    mtp_mgmt_ctrl.cli_log_inf("Copy MTP KPT Test script: {:s}".format(mtp_kpt_script_pkg), level=0)
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
    if not libmfg_utils.network_copy_file(ipaddr, userid, passwd, mtp_kpt_script_pkg, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH):
        mtp_mgmt_ctrl.cli_log_err("Copy KPT Test script failed... Abort", level=0)
        return
    mtp_mgmt_ctrl.cli_log_inf("Copy MTP KPT Test script complete", level=0)
    cmd = "tar zxf {:s}".format(mtp_kpt_script_pkg)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return
    mtp_mgmt_ctrl.cli_log_inf("Unpack MTP KPT Test script complete", level=0)


def single_mtp_kpt_test(mtp_kpt_script_dir, mtp_mgmt_ctrl, mtp_id, mtp_test_summary):
    mtp_mgmt_ctrl.cli_log_inf("MTP KPT Test Start", level=0)
    # go to mtp_kpt_script and Start the test
    cmd = "cd {:s}".format(mtp_kpt_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "./mtp_kpt_test.py --mtpid {:s}".format(mtp_id)

    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.DIAG_KPT_TEST_TIMEOUT)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)

    mtp_mgmt_ctrl.cli_log_inf("MTP KPT Test complete", level=0)
    mtp_mgmt_ctrl.cli_log_inf("MTP KPT Test Duration:{:s}".format(mtp_stop_ts-mtp_start_ts), level=0)

    test_log_file = get_mtp_logfile(mtp_mgmt_ctrl, mtp_kpt_script_dir, mtp_id, mtp_test_summary)
    if GLB_CFG_MFG_TEST_MODE:
        mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file)

    cmd = "rm -rf {:s}".format(test_log_file)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    return


def main():
    parser = argparse.ArgumentParser(description="MFG Key Programming Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = get_mtpid_list(mtp_cfg_db)
    mtp_mgmt_ctrl_list = list()

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

    mfg_kpt_start_ts = libmfg_utils.timestamp_snapshot()
    # power on the mtp chassis
    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            return
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

    # Copy script, config file on to each MTP Chassis
    mtp_kpt_script_dir = "mtp_kpt_script/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mtp_kpt_script_pkg = "mtp_kpt_script.{:s}.tar".format(mtp_id)
        mtp_script_pkg_init(mtp_kpt_script_dir, mtp_kpt_script_pkg)
        mtp_download_test_script(mtp_mgmt_ctrl, mtp_kpt_script_pkg)
        cmd = "rm -f {:s}".format(mtp_kpt_script_pkg)
        os.system(cmd)

    mtp_thread_list = list()
    mfg_kpt_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_kpt_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_kpt_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_kpt_script_dir, mtp_mgmt_ctrl, mtp_id, mfg_kpt_summary[mtp_id]))
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

    mfg_kpt_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP Key Programming Test Duration:{:s}".format(mfg_kpt_stop_ts - mfg_kpt_start_ts))

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.mtp_apc_pwr_off()
        mtp_mgmt_ctrl.cli_log_inf("Power off APC, Wait {:d} seconds for APC shutdown".format(MTP_Const.MTP_POWER_CYCLE_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)

    libmfg_utils.cli_inf("##########  MFG KPT Test Summary  ##########")
    for mtp_id in mfg_kpt_summary.keys():
        libmfg_utils.cli_inf("---------- {:s} Report: ----------".format(mtp_id))
        for slot, sn, nic_type, rc in mfg_kpt_summary[mtp_id]:
            nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
            if rc:
                libmfg_utils.cli_inf("{:s} {:s} {:s} PASS".format(nic_cli_id_str, sn, nic_type))
            else:
                libmfg_utils.cli_err("{:s} {:s} {:s} FAIL".format(nic_cli_id_str, sn, nic_type))

    return

if __name__ == "__main__":
    main()

