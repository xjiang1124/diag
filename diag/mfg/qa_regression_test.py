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
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import DIAG_NIGHTLY_REPORT_RECEIPIENT
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db


def get_mtp_logfile(mtp_mgmt_ctrl, log_dir, mtp_id, corner):
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]

    log_timestamp = libmfg_utils.get_timestamp()
    # log subdir
    sub_dir = MTP_DIAG_Logfile.MFG_4C_LOG_DIR.format(corner, mtp_id, log_timestamp)
    # log pkg filename
    log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_4C_LOG_PKG_FILE.format(corner, mtp_id, log_timestamp)
    # onboard log files
    test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES
    # test summary logfile
    test_log_file = "{:s}mtp_test.log".format(log_dir+sub_dir)
    # local copy of summary logfile
    local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)

    # temperary dir for log files
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir+sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None
    # move onboard log files
    cmd = "mv {:s} {:s}".format(test_onboard_log_files, log_dir+sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

    if corner == Env_Cond.MFG_NT or corner == Env_Cond.MFG_RDT:
        diag_log_dir = log_dir + "diag_logs/"
        asic_log_dir = log_dir + "asic_logs/"
        nic_log_dir = log_dir + "nic_logs/"
        # move the extra logfile
        cmd = "mv {:s} {:s}".format(diag_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(asic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(nic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
    else:
        hv_diag_log_dir = log_dir + "hv_diag_logs/"
        hv_asic_log_dir = log_dir + "hv_asic_logs/"
        hv_nic_log_dir = log_dir + "hv_nic_logs/"
        lv_diag_log_dir = log_dir + "lv_diag_logs/"
        lv_asic_log_dir = log_dir + "lv_asic_logs/"
        lv_nic_log_dir = log_dir + "lv_nic_logs/"
        # move the extra logfile
        cmd = "mv {:s} {:s}".format(hv_diag_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(hv_asic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(hv_nic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        # move the extra logfile
        cmd = "mv {:s} {:s}".format(lv_diag_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(lv_asic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(lv_nic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None

    # pkg the onboard logs
    cmd = MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format(log_pkg_file, log_dir, sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

    # create the log dir if not exist
    qa_log_dir = MTP_DIAG_Logfile.DIAG_QA_LOG_DIR + libmfg_utils.get_date() + "/"
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(qa_log_dir)
    os.system(cmd)
    qa_log_pkg_file = qa_log_dir + os.path.basename(log_pkg_file)

    if not libmfg_utils.network_get_file(ipaddr, userid, passwd, local_test_log_file, test_log_file):
        mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test summary file {:}".format(test_log_file), level=0)
        return None

    if not libmfg_utils.network_get_file(ipaddr, userid, passwd, qa_log_pkg_file, log_pkg_file):
        mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file {:}".format(log_pkg_file), level=0)
        return None

    # clear the onboard logs
    logfile_list = list()
    logfile_list.append(log_pkg_file)
    logfile_list.append(log_dir+sub_dir)
    cmd = "rm -rf {:s}".format(" ".join(logfile_list))
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

    return [local_test_log_file, qa_log_pkg_file]


def test_report(email_to, mtp_id, loop, test_log_file, qa_log_pkg, corner, duration):
    ret = True
    mtp_cli_id_str = libmfg_utils.id_str(mtp=mtp_id)
    report_title = ""
    report_body = ""

    with open(test_log_file, 'r') as fp:
        buf = fp.read()

    if MTP_DIAG_Report.MTP_DIAG_REGRESSION_FAIL in buf:
        report_title = mtp_cli_id_str + "Diag Regression {:s} Test Iteration - {:d}, MTP Setup Failed".format(corner, loop)
        ret = False
    else:
        if MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL in buf:
            report_title = mtp_cli_id_str + "Diag Regression {:s} Test Iteration - {:d}, NIC Test Failed".format(corner, loop)
            nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
            match = re.findall(nic_fail_reg_exp, buf)
            for slot, nic_type, sn in match:
                nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
                report_body += nic_cli_id_str + "[* {:s} *] [* {:s} *] Diag Regression Test Failed\n".format(nic_type, sn)
                # find all test status
                nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
                sub_match = re.findall(nic_test_rslt_reg_exp, buf)
                for dsp, test, result in sub_match:
                    report_body += "        ---- Test ({:s}, {:s}) Result: {:s}\n".format(dsp, test, result)
                    # find test error message
                    nic_test_err_msg_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_ERR_MSG_RE.format(slot, sn, dsp, test)
                    err_msg_match = re.findall(nic_test_err_msg_reg_exp, buf)
                    if err_msg_match:
                        for err_msg in err_msg_match:
                            report_body += "             [* Error Message *]: {:s}\n".format(err_msg)
                report_body += "\n"
                ret = False

        if MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS in buf:
            if report_title == "":
                report_title = mtp_cli_id_str + "Diag Regression {:s} Test Iteration - {:d}, NIC Test Passed".format(corner, loop)
            nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
            match = re.findall(nic_pass_reg_exp, buf)
            for slot, nic_type, sn in match:
                nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
                report_body += nic_cli_id_str + "[* {:s} *] [* {:s} *] Diag Regression Test Passed\n".format(nic_type, sn)
                # find all test status
                nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
                sub_match = re.findall(nic_test_rslt_reg_exp, buf)
                for dsp, test, result in sub_match:
                    report_body += "        ---- Test ({:s}, {:s}) Result: {:s}\n".format(dsp, test, result)
                report_body += "\n"

    # testbed info
    match = re.findall(r"==> (.*) <==", buf)
    if match:
        report_body += "[**** MTP Testbed info ****]\n"
        for item in match:
            report_body += "    {:s}\n".format(item)
    report_body += "    Test Time: {:s}\n".format(duration)
    report_body += "\n"

    # test logfile
    report_body += "[**** QA Logfile ****]\n".format(qa_log_pkg)
    report_body += "    {:s}\n".format(qa_log_pkg)
    if email_to:
        libmfg_utils.email_report(email_to, report_title, report_body)

    # clean the logfile
    os.system("rm -f {:s}".format(test_log_file))
    return ret


def load_mtp_cfg():
    # Pensando Lab/Debug MTP Chassis
    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
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


def single_mtp_diag_regression(mtp_script_dir, mtp_mgmt_ctrl, mtp_id, iteration, stop_on_err, skip_test, email_to, corner):
    for loop in range(1, iteration+1):
        mtp_mgmt_ctrl.cli_log_inf("Regression Test Iteration-{:03d} start".format(loop), level=0)
        # go to mtp_regression and Start the regression
        cmd = "cd {:s}".format(mtp_script_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        #cmd += " --psu-check"

        cmd = "./mtp_diag_regression.py --mtpid {:s} --corner {:s}".format(mtp_id, corner)
        if stop_on_err:
            cmd += " --stop-on-error"
        if skip_test:
            cmd += " --skip-test"

        mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
        mtp_start_ts = libmfg_utils.timestamp_snapshot()
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_4C_TEST_TIMEOUT)
        mtp_stop_ts = libmfg_utils.timestamp_snapshot()
        mtp_test_time = mtp_stop_ts-mtp_start_ts
        mtp_mgmt_ctrl.set_mtp_diag_logfile(None)

        mtp_mgmt_ctrl.cli_log_inf("Collecting Regression Test Iteration-{:03d} logfiles....".format(loop), level=0)
        test_log_file, qa_log_pkg = get_mtp_logfile(mtp_mgmt_ctrl, mtp_script_dir, mtp_id, corner)
        mtp_mgmt_ctrl.cli_log_inf("Sending Regression Test Iteration-{:03d} report....".format(loop), level=0)
        result = test_report(email_to, mtp_id, loop, test_log_file, qa_log_pkg, corner, mtp_test_time)
        cmd = "rm -rf {:s}".format(test_log_file)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

        if not result and stop_on_err:
            return

        mtp_mgmt_ctrl.mtp_chassis_shutdown()

        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            return
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

        mtp_mgmt_ctrl.cli_log_inf("Regression Test Iteration-{:03d} complete".format(loop), level=0)
        mtp_mgmt_ctrl.cli_log_inf("Regression Test Iteration-{:03d} Duration:{:s}".format(loop, mtp_test_time), level=0)

    return


def main():
    parser = argparse.ArgumentParser(description="Diagnostics P2C Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--stop-on-error", help="Leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--iteration", help="Iteration to run with MTP power cycle", type=int, required=True)
    parser.add_argument("--email", help="Send report to email address")
    parser.add_argument("--apc", help="MTP Chassis is powered down, need to power on APC", action='store_true')
    parser.add_argument("--pwr-cycle", help="Power cycle MTP before test", action='store_true')
    parser.add_argument("--skip-test", help="Test will not run", action='store_true')
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--corner", type=Env_Cond, help="diagnostic environment condition", choices=list(Env_Cond))

    args = parser.parse_args()

    verbosity = False
    stop_on_err = False
    apc = False
    email_to = DIAG_NIGHTLY_REPORT_RECEIPIENT
    pwr_cycle = False
    skip_test = False
    corner = Env_Cond.MFG_QA

    if args.stop_on_error:
        libmfg_utils.cli_inf("Test will stop if any test error out")
        stop_on_err = True
    if args.apc:
        apc = True
    if args.verbosity:
        verbosity = True
    if args.email:
        email_to = args.email
    iteration = args.iteration
    if args.pwr_cycle:
        pwr_cycle = True
    if args.skip_test:
        skip_test = True
    if args.corner:
        corner = args.corner

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = get_mtpid_list(mtp_cfg_db)
    mtpid_fail_list = list()
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

    # power on the mtp chassis, if --apc is set
    if apc:
        libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)
    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            mtpid_list.remove(mtp_id)
            mtpid_fail_list.append(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

    if pwr_cycle:
        libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)
        libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            if not mtp_mgmt_ctrl.mtp_mgmt_connect():
                mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
                mtpid_list.remove(mtp_id)
                mtpid_fail_list.append(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            else:
                mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

    regression_start_ts = libmfg_utils.timestamp_snapshot()

    # Sync timestamp to server
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        timestamp_str = str(libmfg_utils.timestamp_snapshot())
        if not mtp_mgmt_ctrl.mtp_mgmt_set_date(timestamp_str):
            mtp_mgmt_ctrl.cli_log_err("MTP Chassis timestamp sync failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Chassis timestamp sync'd", level=0)

    # Copy script, config file on to each MTP Chassis
    mtp_regression_script_dir = "mtp_regression/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_regression_script_pkg = "mtp_regression.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP Regression Test script", level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_regression_script_dir, mtp_regression_script_pkg):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP Regression Test script failed", level=0)
            mtpid_list.remove(mtp_id)
            mtpid_fail_list.append(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Deploy MTP Regression Test script complete", level=0)

    mtp_thread_list = list()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mtp_thread = threading.Thread(target = single_mtp_diag_regression, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_regression_script_dir, mtp_mgmt_ctrl, mtp_id, iteration, stop_on_err, skip_test, email_to, corner))
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
    regression_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("Regression Test Duration:{:s}".format(regression_stop_ts - regression_start_ts))


if __name__ == "__main__":
    main()
