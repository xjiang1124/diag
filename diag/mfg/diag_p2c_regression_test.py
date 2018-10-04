#!/usr/bin/env python

import sys
import os
import time
import datetime 
import pexpect
import re
import argparse
import threading
import Queue
import random

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Error
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libpro_srv_db import pro_srv_db
from libdiag_db import diag_db


def get_mtp_logfile(mtp_mgmt_ctrl, log_dir, mtp_id, loop):
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]

     # log pkg filename
    log_pkg_file = "{:s}mtp_regression.{:d}.tar.gz".format(log_dir, loop)

    # need to be sync'd with cleanup.sh
    diag_onboard_log_files = "/home/diag/diag/log/*txt"  
    asic_onboard_log_files = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/*log" 

    # regression logs
    logfile_list = list()
    test_log_file = "{:s}mtp_test.log".format(log_dir)
    diag_log_file = "{:s}mtp_diag.log".format(log_dir)
    diag_log_cmd_file = "{:s}mtp_diag_cmd.log".format(log_dir)
    diagmgr_log_file = "{:s}mtp_diagmgr.log".format(log_dir)
    # diag onboard log files
    cmd = "mkdir -p {:s}diag_logs/".format(log_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "mv {:s} {:s}diag_logs/".format(diag_onboard_log_files, log_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    # asic onboard log files
    cmd = "mkdir -p {:s}asic_logs/".format(log_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "mv {:s} {:s}asic_logs/".format(asic_onboard_log_files, log_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "cleanup.sh"
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    # all the test logs
    logfile_list.append(test_log_file)
    logfile_list.append(diag_log_file)
    logfile_list.append(diag_log_cmd_file)
    logfile_list.append(diagmgr_log_file)
    logfile_list.append("{:s}diag_logs/".format(log_dir))
    logfile_list.append("{:s}asic_logs/".format(log_dir))

    # pkg the onboard logs
    cmd = "tar czvf {:s} {:s}".format(log_pkg_file, " ".join(logfile_list))
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    ts = libmfg_utils.get_timestamp()
    # create the log dir if not exist
    qa_log_dir = "/vol/hw/diag/diag_qa/regression_log/{:s}/".format(str(datetime.datetime.now().date()))
    cmd = "mkdir -p {:s}".format(qa_log_dir)
    os.system(cmd)
    # copy the onboard logs
    local_test_log_file = "log/{:s}_mtp_test.iter-{:d}.log".format(mtp_id, loop)
    qa_log_pkg_file = qa_log_dir + "{:s}_{:s}_{:s}".format(mtp_id, ts, os.path.basename(log_pkg_file))
    libmfg_utils.network_get_file(ipaddr, userid, passwd, qa_log_pkg_file, log_pkg_file)
    libmfg_utils.network_get_file(ipaddr, userid, passwd, local_test_log_file, test_log_file)
    # clear the onboard logs
    logfile_list.append(log_pkg_file)
    cmd = "rm -rf {:s}".format(" ".join(logfile_list))
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    return local_test_log_file


def test_report(email_to, mtp_id, loop, test_log_file):
    ret = True
    mtp_cli_id_str = libmfg_utils.id_str(mtp=mtp_id)
    report_title = ""
    report_body = ""

    with open(test_log_file, 'r') as fp:
        buf = fp.read()

    if MTP_DIAG_Error.MTP_DIAG_REGRESSION_FAIL in buf:
        report_title = mtp_cli_id_str + "Diag Regression Test Iteration - {:d}, MTP Setup Failed".format(loop)
        ret = False
    else:
        if MTP_DIAG_Error.NIC_DIAG_REGRESSION_FAIL in buf: 
            report_title = mtp_cli_id_str + "Diag Regression Test Iteration - {:d}, NIC Test Failed".format(loop)
            match = re.findall(r"NIC-(\d{2}) %s" %MTP_DIAG_Error.NIC_DIAG_REGRESSION_FAIL, buf)
            for slot in match:
                nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
                report_body += nic_cli_id_str + "Diag Regression Test Failed\n"
                # find all test status
                sub_match = re.findall(r"\[NIC-%s\]: Diag Test (.*)#(.*) (.*), Duration" %slot, buf)
                for dsp, test, result in sub_match:
                    report_body += "    Test ({:s}, {:s}) Result: {:s}\n".format(dsp, test, result)
                ret = False

        if MTP_DIAG_Error.NIC_DIAG_REGRESSION_PASS in buf: 
            if report_title == "":
                report_title = mtp_cli_id_str + "Diag Regression Test Iteration - {:d}, NIC Test Passed".format(loop)
            match = re.findall(r"NIC-(\d{2}) %s" %MTP_DIAG_Error.NIC_DIAG_REGRESSION_PASS, buf)
            for slot in match:
                nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
                report_body += nic_cli_id_str + "Diag Regression Test Passed\n"
                # find all test status
                sub_match = re.findall(r"\[NIC-%s\]: Diag Test (.*)#(.*) (.*), Duration" %slot, buf)
                for dsp, test, result in sub_match:
                    report_body += "    Test ({:s}, {:s}) Result: {:s}\n".format(dsp, test, result)
    if email_to:
        libmfg_utils.email_report(email_to, report_title, report_body)

    return ret


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


def get_mtpid_list(mtp_cfg_db):
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    sub_mtpid_list = libmfg_utils.multiple_select_menu("Select MTP Chassis", mtpid_list)
    return sub_mtpid_list


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg)
    return mtp_mgmt_ctrl

    
def mtp_barcode_scan(pro_srv_id, mtp_id, mtp_mgmt_ctrl, log_filep):
    scan_cfg_filep = open("config/{:s}.yaml".format(mtp_id), "w+")
    mtp_mgmt_ctrl.cli_log_inf("Start the Barcode Scan Process", level=0)
    while True:
        scan_rslt = mtp_mgmt_ctrl.mtp_barcode_scan(False)
        if scan_rslt:
            break;
        mtp_mgmt_ctrl.cli_log_inf("Restart the Barcode Scan Process", level=0)
    pass_rslt_list = list()
    fail_rslt_list = list()
    # print scan summary
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        nic_cli_id_str = libmfg_utils.id_str(mtp = mtp_id, nic = slot)
        if scan_rslt[key]["NIC_VALID"]:
            sn = scan_rslt[key]["NIC_SN"]
            mac_ui = libmfg_utils.mac_address_format(scan_rslt[key]["NIC_MAC"])
            pass_rslt_list.append(nic_cli_id_str + "SN = " + sn + "; MAC = " + mac_ui)
        else:
            fail_rslt_list.append(nic_cli_id_str + "NIC Absent")
    libmfg_utils.cli_log_rslt("Barcode Scan Summary", pass_rslt_list, fail_rslt_list, log_filep)
    mtp_mgmt_ctrl.gen_barcode_config_file(pro_srv_id, scan_cfg_filep, scan_rslt)
    scan_cfg_filep.close()
    os.system("sync")


def mtp_script_pkg_init(mtp_script_dir, mtp_script_pkg):
    cmd = "cp -r lib/ config/ {:s}".format(mtp_script_dir)
    os.system(cmd)
    cmd = "tar czf {:s} {:s}".format(mtp_script_pkg, mtp_script_dir)
    os.system(cmd)
    # remove the lib config for the next run
    cmd = "rm -rf {:s}/lib {:s}/config".format(mtp_script_dir, mtp_script_dir)
    os.system(cmd)


def mtp_download_diag_image(mtp_mgmt_ctrl, mtp_image_file, mtp_diag_dir):
    mtp_mgmt_ctrl.cli_log_inf("Copy MTP Chassis image: {:s}".format(mtp_image_file), level=0)
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    mtp_ip_addr = mtp_mgmt_cfg[0]
    mtp_usrid = mtp_mgmt_cfg[1]
    mtp_passwd = mtp_mgmt_cfg[2]
    if not libmfg_utils.network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, mtp_diag_dir):
        mtp_mgmt_ctrl.cli_log_err("Copy MTP Chassis image: {:s} failed".format(mtp_image_file), level=0)
        libmfg_utils.sys_exit("Network error")
    else:
        mtp_mgmt_ctrl.cli_log_inf("Copy MTP Chassis image: {:s} complete".format(mtp_image_file), level=0)
    pre_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
    mtp_mgmt_ctrl.cli_log_inf("Update MTP Chassis image: {:s}".format(os.path.basename(mtp_image_file)), level=0)
    mtp_mgmt_ctrl.mtp_update_sw_image(mtp_diag_dir + os.path.basename(mtp_image_file))
    post_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
    mtp_mgmt_ctrl.cli_log_inf("Update MTP chassis image complete [{:s}] --> [{:s}]".format(pre_ver, post_ver), level=0)


def mtp_download_test_script(mtp_mgmt_ctrl, mtp_script_pkg, mtp_diag_dir):
    mtp_mgmt_ctrl.cli_log_inf("Copy MTP Regression script: {:s}".format(mtp_script_pkg), level=0)
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
    if not libmfg_utils.network_copy_file(ipaddr, userid, passwd, mtp_script_pkg, mtp_diag_dir):
        mtp_mgmt_ctrl.cli_log_err("Download regression script onto MTP Chassis failed", level=0)
        return
    mtp_mgmt_ctrl.cli_log_inf("Copy MTP Regression script: {:s} complete".format(mtp_script_pkg), level=0)
    cmd = "tar zxf {:s}".format(mtp_script_pkg)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return
    mtp_mgmt_ctrl.cli_log_inf("Unpack MTP Regression script: {:s} complete".format(mtp_script_pkg), level=0)


def single_mtp_diag_regression(mtp_script_dir, mtp_mgmt_ctrl, mtp_id, iteration, stop_on_err, skip_test, email_to):
    for loop in range(iteration):
        mtp_mgmt_ctrl.cli_log_inf("Regression Test Iteration-{:03d} start".format(loop), level=0)
        # go to mtp_regression and Start the regression
        cmd = "cd {:s}".format(mtp_script_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "./mtp_diag_regression.py --mtpid {:s}".format(mtp_id)
        cmd += " --psu-check"
        if stop_on_err:
            cmd += " --stop-on-error"
        if skip_test:
            cmd += " --skip-test"

        mtp_start_ts = libmfg_utils.timestamp_snapshot()
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.DIAG_REGRESSION_TIMEOUT)
        mtp_stop_ts = libmfg_utils.timestamp_snapshot()

        mtp_mgmt_ctrl.cli_log_inf("Regression Test Iteration-{:03d} complete".format(loop), level=0)
        mtp_mgmt_ctrl.cli_log_inf("Regression Test Iteration-{:03d} Duration:{:s}".format(loop, mtp_stop_ts-mtp_start_ts), level=0)

        test_log_file = get_mtp_logfile(mtp_mgmt_ctrl, mtp_script_dir, mtp_id, loop)
        result = test_report(email_to, mtp_id, loop, test_log_file)
        cmd = "rm -rf {:s}".format(test_log_file)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

        if not result and stop_on_err:
            return

        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
        mtp_mgmt_ctrl.mtp_apc_pwr_off()
 
        time.sleep(10)
 
        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            return
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

    return

 
def main():
    parser = argparse.ArgumentParser(description="Diagnostics P2C Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--stop-on-error", help="Leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--iteration", help="Iteration to run with MTP power cycle", type=int, required=True)
    parser.add_argument("--image", help="MTP Chassis diag image")
    parser.add_argument("--email", help="Send report to email address")
    parser.add_argument("--error-injection", help="Randomly inject error", action='store_true')
    parser.add_argument("--apc", help="MTP Chassis is powered down, need to power on APC", action='store_true')
    parser.add_argument("--pwr-cycle", help="Power cycle MTP before test", action='store_true')
    parser.add_argument("--skip-test", help="Test will not run", action='store_true')
    parser.add_argument("--skip-scan", help="Skip the barcode scan process, diag use only", action='store_true')
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')

    args = parser.parse_args()

    verbosity = False
    stop_on_err = False
    err_inj = False
    apc = False
    skip_image_update = True
    email_to = None
    pwr_cycle = False
    skip_test = False
    skip_scan = False

    if args.stop_on_error:
        libmfg_utils.cli_inf("Test will stop if any test error out")
        stop_on_err = True
    if args.error_injection:
        libmfg_utils.cli_inf("Error injection is enabled")
        err_inj = True
    if args.apc:
        apc = True
    if args.verbosity:
        verbosity = True
    if args.email:
        email_to = args.email
    iteration = args.iteration
    if args.image:
        mtp_image_file = args.image
        skip_image_update = False
    if args.pwr_cycle:
        pwr_cycle = True
    if args.skip_test:
        skip_test = True
    if args.skip_scan:
        skip_scan = True

    pro_srv_id = get_pro_srv_id()
    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = get_mtpid_list(mtp_cfg_db)
    mtp_mgmt_ctrl_list = list()
    regression_log_filep = open("log/regression.log", "w+")

    # init mtp_ctrl list
    for mtp_id in mtpid_list: 
        if verbosity:
            diag_log_filep = sys.stdout
        else:
            diag_log_filep = None
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, regression_log_filep, diag_log_filep)
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)

    # scan and generate nic barcode config file
    if not skip_scan:
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list): 
            mtp_barcode_scan(pro_srv_id, mtp_id, mtp_mgmt_ctrl, regression_log_filep)

    # generate the regression script pkg
    mtp_diag_dir = "/home/diag/"
    mtp_script_dir = "mtp_regression/"
    mtp_script_pkg = "mtp_regression.tar"
    mtp_script_pkg_init(mtp_script_dir, mtp_script_pkg)

    regression_start_ts = libmfg_utils.timestamp_snapshot()

    # power on the mtp chassis, if --apc is set
    if apc:
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

    # Update the MTP image, if --image is on
    if not skip_image_update:
        for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list: 
            mtp_download_diag_image(mtp_mgmt_ctrl, mtp_image_file, mtp_diag_dir)

    # Copy script, config file on to each MTP Chassis
    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list: 
        mtp_download_test_script(mtp_mgmt_ctrl, mtp_script_pkg, mtp_diag_dir)
    cmd = "rm -f {:s}".format(mtp_script_pkg)
    os.system(cmd)

    if pwr_cycle:
        for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list: 
            mtp_mgmt_ctrl.mtp_mgmt_poweroff()
            mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list: 
            mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
            mtp_mgmt_ctrl.mtp_apc_pwr_off()

        time.sleep(10)

        for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list: 
            mtp_mgmt_ctrl.mtp_apc_pwr_on()
            mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
        for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list: 
            if not mtp_mgmt_ctrl.mtp_mgmt_connect():
                mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
                return
            else:
                mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

    mtp_thread_list = list()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list): 
        mtp_thread = threading.Thread(target = single_mtp_diag_regression, args = (mtp_diag_dir+mtp_script_dir, mtp_mgmt_ctrl, mtp_id, iteration, stop_on_err, skip_test, email_to))
        mtp_thread.daemon = True
        mtp_thread.start()
        mtp_thread_list.append(mtp_thread)

    # monitor all the thread
    while True:
        if len(mtp_thread_list) == 0:
            break 
        for mtp_thread in mtp_thread_list:
            if not mtp_thread.is_alive():
                ret = mtp_thread.join()
                mtp_thread_list.remove(mtp_thread)
        time.sleep(5)
    regression_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_log_inf(regression_log_filep, "Regression Test Duration:{:s}".format(regression_stop_ts - regression_start_ts))
    regression_log_filep.close()
    os.system("sync")


if __name__ == "__main__":
    main()
