#!/usr/bin/env python

import sys
import os
import time
import pexpect
import re
import argparse
import threading

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import Env_Cond
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libpro_srv_db import pro_srv_db
from libdiag_db import diag_db


def get_mtp_logfile(mtp_mgmt_ctrl, log_dir, mtp_id, corner):
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]

    # create the log subdir
    sub_dir = "{:s}_{:s}_{:s}/".format(str(corner), mtp_id, libmfg_utils.get_timestamp())
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("mkdir -p {:s}".format(log_dir+sub_dir))

    # log pkg filename
    log_pkg_file = "{:s}mtp_regression.{:s}.tar.gz".format(log_dir, str(corner))

    # need to be sync'd with cleanup.sh
    diag_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_DIAG_LOG_FILES
    asic_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES
    test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES

    # regression logs
    logfile_list = list()
    # diag onboard log files
    cmd = "mkdir -p {:s}diag_logs/".format(log_dir+sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "mv {:s} {:s}diag_logs/".format(diag_onboard_log_files, log_dir+sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    # asic onboard log files
    cmd = "mkdir -p {:s}asic_logs/".format(log_dir+sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "mv {:s} {:s}asic_logs/".format(asic_onboard_log_files, log_dir+sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "mv {:s} {:s}".format(test_onboard_log_files, log_dir+sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "cleanup.sh"
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    # all the test logs
    test_log_file = "{:s}mtp_test.log".format(log_dir+sub_dir)

    # pkg the onboard logs
    cmd = "tar czvf {:s} -C {:s} {:s}".format(log_pkg_file, log_dir, sub_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    local_test_log_file = "log/{:s}_{:s}_mtp_test.log".format(str(corner), mtp_id)
    libmfg_utils.network_get_file(ipaddr, userid, passwd, local_test_log_file, test_log_file)

    with open(local_test_log_file, 'r') as fp:
        buf = fp.read()
    nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
    nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
    fail_match = re.findall(nic_fail_reg_exp, buf)
    pass_match = re.findall(nic_pass_reg_exp, buf)

    for slot, nic_type, sn in fail_match + pass_match:
        if nic_type == NIC_Type.NAPLES100:
            nic_log_dir = MTP_DIAG_Logfile.DIAG_MFG_NAPLES100_4C_LOG_DIR + "/" + str(corner) + "/" + sn + "/"
        elif nic_type == NIC_Type.NAPLES25:
            nic_log_dir = MTP_DIAG_Logfile.DIAG_MFG_NAPLES25_4C_LOG_DIR + "/" + str(corner) + "/" + sn + "/"
        else:
            nic_log_dir = MTP_DIAG_Logfile.DIAG_MFG_NAPLES100_4C_LOG_DIR + "/" + str(corner) + "/" + sn + "/"

        cmd = "mkdir -p {:s}".format(nic_log_dir)
        os.system(cmd)
        # copy the onboard logs
        ts = libmfg_utils.get_timestamp()
        qa_log_pkg_file = nic_log_dir + "{:s}_{:s}_{:s}".format(mtp_id, ts, os.path.basename(log_pkg_file))
        mtp_mgmt_ctrl.cli_log_inf("Collecting {:s} log files {:s}".format(sn, qa_log_pkg_file))
        libmfg_utils.network_get_file(ipaddr, userid, passwd, qa_log_pkg_file, log_pkg_file)

    # clear the onboard logs
    logfile_list.append(log_pkg_file)
    logfile_list.append(log_dir+sub_dir)
    cmd = "rm -rf {:s}".format(" ".join(logfile_list))
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    mtp_mgmt_ctrl.cli_log_inf("Collecting log files complete", level=0)

    return local_test_log_file


def mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file_list, corner_list, flex_station):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    duration = mtp_stop_ts - mtp_start_ts

    pass_sn_list = list()
    fail_sn_list = list()
    sn_test_dict = dict()
    sn_type_dict = dict()
    sn_test_rslt_dict = dict()
    sn_err_dsc_dict = dict()
    sn_err_code_dict = dict()

    for corner, test_log_file in zip(corner_list, test_log_file_list):
        with open(test_log_file, 'r') as fp:
            buf = fp.read()

        # MTP related error, don't post any report
        if MTP_DIAG_Report.MTP_DIAG_REGRESSION_FAIL in buf:
            libmfg_utils.cli_inf(mtp_cli_id_str + "MTP Setup fails, no report will be generated")
            cmd = "cp {:s} {:s}.bak".format(test_log_file, test_log_file)
            os.system(cmd)
            continue

        if MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL in buf:
            nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
            match = re.findall(nic_fail_reg_exp, buf)
            for slot, nic_type, sn in match:
                # init the list
                if sn not in sn_test_dict.keys():
                    sn_test_dict[sn] = list()
                    sn_test_rslt_dict[sn] = list()
                    sn_type_dict[sn] = nic_type
                    sn_err_dsc_dict[sn] = list()
                    sn_err_code_dict[sn] = list()

                if sn not in fail_sn_list:
                    fail_sn_list.append(sn)
                if sn in pass_sn_list:
                    pass_sn_list.remove(sn)

                nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
                # find all test status
                nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
                sub_match = re.findall(nic_test_rslt_reg_exp, buf)
                for dsp, test, result in sub_match:
                    sn_test_dict[sn].append("{:s}-{:s}-{:s}".format(str(corner), dsp, test))
                    sn_test_rslt_dict[sn].append(result)
                    sn_err_dsc_dict[sn].append(nic_cli_id_str)
                    sn_err_code_dict[sn].append(result)

        if MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS in buf:
            nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
            match = re.findall(nic_pass_reg_exp, buf)
            for slot, nic_type, sn in match:
                # init the list
                if sn not in sn_test_dict.keys():
                    sn_test_dict[sn] = list()
                    sn_test_rslt_dict[sn] = list()
                    sn_type_dict[sn] = nic_type
                    sn_err_dsc_dict[sn] = list()
                    sn_err_code_dict[sn] = list()

                if sn not in fail_sn_list and sn not in pass_sn_list:
                    pass_sn_list.append(sn)

                nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
                # find all test status
                nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
                sub_match = re.findall(nic_test_rslt_reg_exp, buf)
                for dsp, test, result in sub_match:
                    sn_test_dict[sn].append("{:s}-{:s}-{:s}".format(str(corner), dsp, test))
                    sn_test_rslt_dict[sn].append(result)
                    sn_err_dsc_dict[sn].append(nic_cli_id_str)
                    sn_err_code_dict[sn].append(result)

    libmfg_utils.cli_inf(mtp_cli_id_str + "Start posting test report")
    for sn in fail_sn_list:
        ret = libmfg_utils.flx_web_srv_post_uut_report(flex_station, sn_type_dict[sn], sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, sn_test_dict[sn], sn_test_rslt_dict[sn], sn_err_dsc_dict[sn], sn_err_code_dict[sn])
        if not ret:
            libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
        else:
            libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))

    for sn in pass_sn_list:
        ret = libmfg_utils.flx_web_srv_post_uut_report(flex_station, sn_type_dict[sn], sn, "PASS", mtp_start_ts, mtp_stop_ts, duration, sn_test_dict[sn], sn_test_rslt_dict[sn], sn_err_dsc_dict[sn], sn_err_code_dict[sn])
        if not ret:
            libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
        else:
            libmfg_utils.cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))


def get_pro_srv_id():
    product_server_cfg_file = os.path.abspath("config/pensando_pro_srv1_cfg.yaml")
    pro_srv_cfg_db = pro_srv_db(pro_srv_cfg_file = product_server_cfg_file)
    pro_srv_list = list(pro_srv_cfg_db.get_pro_srv_id_list())
    if len(pro_srv_list) > 1:
        pro_srv_id = libmfg_utils.single_select_menu("Select Product Server", pro_srv_list)
        if not pro_srv_id:
            return None
    else:
        pro_srv_id = pro_srv_list[0]
    return pro_srv_id


def load_mtp_cfg():
    product_server_cfg_file = os.path.abspath("config/pensando_pro_srv1_cfg.yaml")
    pro_srv_cfg_db = pro_srv_db(pro_srv_cfg_file = product_server_cfg_file)
    pro_srv_list = list(pro_srv_cfg_db.get_pro_srv_id_list())
    if len(pro_srv_list) > 1:
        pro_srv_id = libmfg_utils.single_select_menu("Select Product Server", pro_srv_list)
        if not pro_srv_id:
            return None
    else:
        pro_srv_id = pro_srv_list[0]
    filename = pro_srv_cfg_db.get_pro_srv_mtp_chassis_cfg_file(pro_srv_id)
    mtp_chassis_cfg_file = os.path.abspath("config/" + filename)
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)
    return mtp_cfg_db


def get_mtpid(mtp_cfg_db):
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    mtp_id = libmfg_utils.single_select_menu("Select MTP Chassis", mtpid_list)
    return mtp_id


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


def mtp_script_pkg_init(mtp_script_dir, mtp_script_pkg):
    cmd = "cp -r lib/ config/ {:s}".format(mtp_script_dir)
    os.system(cmd)
    cmd = "tar czf {:s} {:s}".format(mtp_script_pkg, mtp_script_dir)
    os.system(cmd)
    # remove the lib config for the next run
    cmd = "rm -rf {:s}/lib {:s}/config".format(mtp_script_dir, mtp_script_dir)
    os.system(cmd)


def mtp_download_test_script(mtp_mgmt_ctrl, mtp_script_pkg):
    mtp_mgmt_ctrl.cli_log_inf("Copy MTP Regression script: {:s}".format(mtp_script_pkg), level=0)
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
    if not libmfg_utils.network_copy_file(ipaddr, userid, passwd, mtp_script_pkg, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH):
        mtp_mgmt_ctrl.cli_log_err("Download regression script onto MTP Chassis failed", level=0)
        return
    mtp_mgmt_ctrl.cli_log_inf("Copy MTP Regression script: {:s} complete".format(mtp_script_pkg), level=0)
    cmd = "tar zxf {:s}".format(mtp_script_pkg)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return
    mtp_mgmt_ctrl.cli_log_inf("Unpack MTP Regression script: {:s} complete".format(mtp_script_pkg), level=0)


def single_mtp_diag_regression(mtp_script_dir, mtp_mgmt_ctrl, mtp_id, corner):
    mtp_mgmt_ctrl.cli_log_inf("Regression Test start @{:s}".format(str(corner)), level=0)
    # go to mtp_regression and Start the regression
    cmd = "cd {:s}".format(mtp_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "./mtp_diag_regression.py --mtpid {:s} --corner {:s}".format(mtp_id, str(corner))
    cmd += " --psu-check"

    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.DIAG_REGRESSION_TIMEOUT)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)

    mtp_mgmt_ctrl.cli_log_inf("Regression Test complete @{:s}".format(str(corner)), level=0)
    mtp_mgmt_ctrl.cli_log_inf("Regression Test Duration @{:s}:{:s}".format(str(corner), mtp_stop_ts-mtp_start_ts), level=0)

    get_mtp_logfile(mtp_mgmt_ctrl, mtp_script_dir, mtp_id, corner)

    mtp_mgmt_ctrl.mtp_mgmt_poweroff()
    mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
    mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
    mtp_mgmt_ctrl.mtp_apc_pwr_off()
    time.sleep(MTP_Const.MTP_POWER_CYCLE_DELAY)

    return


def main():
    parser = argparse.ArgumentParser(description="Diagnostics 4C Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--high-temp", help="high temperature environment", action='store_true')
    parser.add_argument("--low-temp", help="low temperature environment", action='store_true')
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')

    verbosity = False
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    if args.high_temp:
        corner_list = [Env_Cond.HTHV, Env_Cond.HTLV]
        flex_station = "4C-H"
    elif args.low_temp:
        corner_list = [Env_Cond.LTHV, Env_Cond.LTLV]
        flex_station = "4C-L"
    else:
        corner_list = [Env_Cond.HTHV, Env_Cond.HTLV, Env_Cond.LTHV, Env_Cond.LTLV]
        flex_station = "4C"

    if verbosity:
        diag_log_filep = sys.stdout
        diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
    else:
        diag_log_filep = None
        diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM

    mtp_cfg_db = load_mtp_cfg()

    mtp_mgmt_ctrl_list = list()
    mtpid_list = list()

    while True:
        mtp_id = get_mtpid(mtp_cfg_db)
        if not mtp_id:
            break

        if mtp_id in mtpid_list:
            libmfg_utils.sys_exit("Duplicate MTPID: {:s} is selected".format(mtp_id))

        mtpid_list.append(mtp_id)
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list)
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)

    regression_start_ts = libmfg_utils.timestamp_snapshot()

    if args.high_temp:
        libmfg_utils.cli_inf("PLEASE CLOSE THE CHAMBER AND SET TEMPERATURE TO {:d} DEGREE CENTIGRADE\n".format(MTP_Const.MFG_EDVT_HIGH_TEMP))
        libmfg_utils.action_confirm("Close Chamber and set chamber temperature to {:d} degree centigrade".format(MTP_Const.MFG_EDVT_HIGH_TEMP), "STOP")
    elif args.low_temp:
        libmfg_utils.cli_inf("PLEASE CLOSE THE CHAMBER AND SET TEMPERATURE TO {:d} DEGREE CENTIGRADE\n".format(MTP_Const.MFG_EDVT_LOW_TEMP))
        libmfg_utils.action_confirm("close chamber and set chamber temperature to {:d} degree centigrade".format(MTP_Const.MFG_EDVT_LOW_TEMP), "STOP")

    for corner in corner_list:
        # Power on the MTP
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
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
            mtp_script_dir = "mtp_regression/"
            mtp_script_pkg = "mtp_regression.{:s}.tar".format(mtp_id)
            mtp_script_pkg_init(mtp_script_dir, mtp_script_pkg)
            mtp_download_test_script(mtp_mgmt_ctrl, mtp_script_pkg)
            cmd = "rm -f {:s}".format(mtp_script_pkg)
            os.system(cmd)

        mtp_thread_list = list()
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
            mtp_thread = threading.Thread(target = single_mtp_diag_regression, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_script_dir, mtp_mgmt_ctrl, mtp_id, corner))
            mtp_thread.daemon = True
            mtp_thread.start()
            mtp_thread_list.append(mtp_thread)
            time.sleep(2)

        # monitor all the thread
        while True:
            if len(mtp_thread_list) == 0:
                break
            for mtp_thread in mtp_thread_list:
                if not mtp_thread.is_alive():
                    mtp_thread.join()
                    mtp_thread_list.remove(mtp_thread)
            time.sleep(5)

    regression_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("Regression Test Duration:{:s}".format(regression_stop_ts - regression_start_ts))

    # mfg report
    for mtp_id in mtpid_list:
        test_log_file_list = list()
        for corner in corner_list:
            test_log_file_list.append("log/{:s}_{:s}_mtp_test.log".format(str(corner), mtp_id))
        mfg_report(mtp_id, regression_start_ts, regression_stop_ts, test_log_file_list, corner_list, flex_station)

        cmd = "rm -f {:s}".format(" ".join(test_log_file_list))
        os.system(cmd)


if __name__ == "__main__":
    main()
