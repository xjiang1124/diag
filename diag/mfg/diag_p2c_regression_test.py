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


def get_mtp_logfile(log_dir, mtp_cfg_db, mtp_id, loop):
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
 
    mtp_test_log_file = log_dir + "mtp_test.log"
    mtp_diag_log_file = log_dir + "mtp_diag.log"
    mtp_diagmgr_log_file = log_dir + "mtp_diagmgr.log"
    local_test_log_file = "log/{:s}_mtp_test.iter-{:d}.log".format(mtp_id, loop)
    local_diag_log_file = "log/{:s}_mtp_diag.iter-{:d}.log".format(mtp_id, loop)
    local_diagmgr_log_file = "log/{:s}_mtp_diagmgr.iter-{:d}.log".format(mtp_id, loop)

    libmfg_utils.network_get_file(ipaddr, userid, passwd, local_test_log_file, mtp_test_log_file)
    libmfg_utils.network_get_file(ipaddr, userid, passwd, local_diag_log_file, mtp_diag_log_file)
    libmfg_utils.network_get_file(ipaddr, userid, passwd, local_diagmgr_log_file, mtp_diagmgr_log_file)
 

def test_report(email_to, mtp_id, loop):
    mtp_cli_id_str = libmfg_utils.id_str(mtp=mtp_id)
    local_test_log_file = "log/{:s}_mtp_test.iter-{:d}.log".format(mtp_id, loop)
    if email_to:
        if "Diag Regression Test Fail" in open(local_test_log_file).read():
            libmfg_utils.email_report(email_to, mtp_cli_id_str + "Diag Regression Test Iteration - {:d} Failed".format(loop))
            return False
        else:
            libmfg_utils.email_report(email_to, mtp_cli_id_str + "Diag Regression Test Iteration - {:d} Passed".format(loop))
            return True


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

    # find the mtp config files controlled by the chosen product server
    filename = pro_srv_cfg_db.get_pro_srv_mtp_chassis_cfg_file(pro_srv_id)
    mtp_chassis_cfg_file = os.path.abspath("config/" + filename)
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)
    return mtp_cfg_db


def get_mtpid(mtp_cfg_db):
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    mtp_id = libmfg_utils.single_select_menu("Select MTP Chassis", mtpid_list)
    return mtp_id


def main():
    parser = argparse.ArgumentParser(description="Diagnostics P2C Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--stop-on-error", help="Leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--iteration", help="Iteration to run with MTP power cycle", type=int, required=True)
    parser.add_argument("--image", help="MTP diag image")
    parser.add_argument("--email", help="send report to email address")
    parser.add_argument("--error-injection", help="randomly inject error", action='store_true')
    parser.add_argument("--apc", help="MTP Chassis is powered down, need to power on APC", action='store_true')
    parser.add_argument("--pwr-cycle", help="Power cycle MTP with each iteration", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')

    args = parser.parse_args()

    verbosity = False
    stop_on_err = False
    err_inj = False
    apc = False
    skip_image_update = True
    email_to = None
    pwr_cycle = False

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

    mtp_cfg_db = load_mtp_cfg()
    mtp_id = get_mtpid(mtp_cfg_db)
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    srv_log_filep = open("log/srv.log", "w+")

    srv_start_ts = datetime.datetime.now().replace(microsecond=0)

    # copy lib, config
    cmd = "cp -r lib/ config/ mtp_regression/"
    os.system(cmd)
    # package the test script
    mtp_script_dir = "mtp_regression/"
    mtp_script_pkg = "mtp_regression.tar"
    mtp_diag_dir = "/home/diag/"
    cmd = "tar czf {:s} {:s}".format(mtp_script_pkg, mtp_script_dir)
    os.system(cmd)
    # remove the lib config for the next run
    cmd = "rm -rf mtp_regression/lib mtp_regression/config"
    os.system(cmd)

    # Init MTP Control
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, srv_log_filep, sys.stdout, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg, dbg_mode = verbosity)

    # Power on MTP, if --apc is on 
    if apc: 
        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY))
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    # Connect to MTP
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        libmfg_utils.cli_log_err(srv_log_filep, mtp_cli_id_str + "Unable to connect MTP Chassis")
        return

    # Update the MTP image, if --image is on
    if not skip_image_update:
        libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Copy MTP Chassis image: {:s}".format(mtp_image_file))
        mtp_ip_addr = mtp_mgmt_cfg[0]
        mtp_usrid = mtp_mgmt_cfg[1]
        mtp_passwd = mtp_mgmt_cfg[2]
        if not libmfg_utils.network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, mtp_diag_dir):
            libmfg_utils.cli_log_err(srv_log_filep, mtp_cli_id_str + "Copy MTP Chassis image: {:s} failed".format(mtp_image_file))
            return
        else:
            libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Copy MTP Chassis image: {:s} complete".format(mtp_image_file))
        pre_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
        libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Update MTP Chassis image: {:s}".format(os.path.basename(mtp_image_file)))
        mtp_mgmt_ctrl.mtp_update_sw_image(mtp_diag_dir + os.path.basename(mtp_image_file))
        post_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
        libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Update MTP chassis image from {:s} to {:s} complete".format(pre_ver, post_ver))

    # Copy script, config file on to each MTP Chassis
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
    if not libmfg_utils.network_copy_file(ipaddr, userid, passwd, mtp_script_pkg, mtp_diag_dir):
        libmfg_utils.cli_log_err(srv_log_filep, mtp_cli_id_str + "Download regression script onto MTP Chassis failed")
        return
    cmd = "tar zxf {:s}".format(mtp_script_pkg)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        libmfg_utils.cli_log_err(srv_log_filep, mtp_cli_id_str + "Unable to execute {:s} on MTP Chassis".format(cmd))
        return
    cmd = "rm -f {:s}".format(mtp_script_pkg)
    os.system(cmd)

    for loop in range(iteration):
        libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Regression Test - {:03d} on {:s} start".format(loop, mtp_id))
        start_ts = datetime.datetime.now().replace(microsecond=0)
        # go to mtp_regression and Start the regression
        cmd = "cd {:s}".format(mtp_script_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "./mtp_diag_regression.py --mtpid {:s}".format(mtp_id)
        cmd += " --psu-check"
        if stop_on_err:
            cmd += " --stop-on-error"
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.DIAG_REGRESSION_TIMEOUT)
            
        stop_ts = datetime.datetime.now().replace(microsecond=0)
        libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Regression Test - {:03d} on {:s} complete".format(loop, mtp_id))
        libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Regression Test - {:03d} Cost time:{:s}".format(loop, stop_ts-start_ts))

        get_mtp_logfile(mtp_diag_dir+mtp_script_dir, mtp_cfg_db, mtp_id, loop)
        if not test_report(email_to, mtp_id, loop) and stop_on_err:
            return

        if pwr_cycle:
            mtp_mgmt_ctrl.mtp_mgmt_poweroff()
            libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY))
            libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
            libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Power off APC")
            mtp_mgmt_ctrl.mtp_apc_pwr_off()

            time.sleep(1)

            mtp_mgmt_ctrl.mtp_apc_pwr_on()
            libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY))
            libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
            if not mtp_mgmt_ctrl.mtp_mgmt_connect():
                libmfg_utils.cli_log_err(srv_log_filep, mtp_cli_id_str + "Unable to connect MTP Chassis")
                return

    srv_stop_ts = datetime.datetime.now().replace(microsecond=0)
    libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Regression Test Total Cost time:{:s}".format(srv_stop_ts - srv_start_ts))
    srv_log_filep.close()
    os.system("sync")


if __name__ == "__main__":
    main()
