#!/usr/bin/env python

import sys
import os
import time
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


def main():
    parser = argparse.ArgumentParser(description="Diagnostics P2C Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--stop-on-error", help="Leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--iteration", help="Iteration to run with MTP power cycle", type=int, required=True)
    parser.add_argument("--image", help="MTP diag image")
    parser.add_argument("--email", help="send report to email address")
    parser.add_argument("--error-injection", help="randomly inject error", action='store_true')
    parser.add_argument("--apc", help="MTP Chassis is powered down, need to power on APC", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')

    args = parser.parse_args()

    verbosity = False
    stop_on_err = False
    err_inj = False
    apc = False
    skip_image_update = True

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

    product_server_cfg_file = os.path.abspath("config/pensando_pro_srv1_cfg.yaml")
    pro_srv_cfg_db = pro_srv_db(pro_srv_cfg_file = product_server_cfg_file)
    pro_srv_list = list(pro_srv_cfg_db.get_pro_srv_id_list())
    if len(pro_srv_list) > 1:
        pro_srv_id = libmfg_utils.single_select_menu("Select Product Server", pro_srv_list)
        if not pro_srv_id:
            return
    else:
        pro_srv_id = pro_srv_list[0]

    # find the mtp config files controlled by the chosen product server
    filename = pro_srv_cfg_db.get_pro_srv_mtp_chassis_cfg_file(pro_srv_id)
    mtp_chassis_cfg_file = os.path.abspath("config/" + filename)
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    mtp_id = libmfg_utils.single_select_menu("Select MTP Chassis", mtpid_list)
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    test_log_filep = sys.stdout
    diag_log_filep = sys.stdout

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
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, test_log_filep, diag_log_filep, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg, dbg_mode = verbosity)

    # wait MTP coming up
    if apc: 
        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        libmfg_utils.cli_inf(mtp_cli_id_str + "Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY))
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to connect MTP Chassis")

    # update the MTP image
    remote_dir = "/home/diag/"
    if not skip_image_update:
        libmfg_utils.cli_inf(mtp_cli_id_str + "Copy MTP Chassis image: {:s}".format(mtp_image_file))
        mtp_ip_addr = mtp_mgmt_cfg[0]
        mtp_usrid = mtp_mgmt_cfg[1]
        mtp_passwd = mtp_mgmt_cfg[2]
        if not libmfg_utils.network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir):
            libmfg_utils.sys_exit(mtp_cli_id_str + "Copy MTP Chassis image: {:s} failed".format(mtp_image_file))
        else:
            libmfg_utils.cli_inf(mtp_cli_id_str + "Copy MTP Chassis image: {:s} complete".format(mtp_image_file))
        pre_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
        libmfg_utils.cli_inf(mtp_cli_id_str + "Update MTP Chassis image: {:s}".format(os.path.basename(mtp_image_file)))
        mtp_mgmt_ctrl.mtp_update_sw_image(remote_dir + os.path.basename(mtp_image_file))
        post_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
        libmfg_utils.cli_inf(mtp_cli_id_str + "Update MTP chassis image from {:s} to {:s} complete".format(pre_ver, post_ver))

    # Copy script, config file to each MTP Chassis
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
    if not libmfg_utils.network_copy_file(ipaddr, userid, passwd, mtp_script_pkg, mtp_diag_dir):
        libmfg_utils.sys_exit(mtp_cli_id_str + "Download regression script onto MTP Chassis failed")
    cmd = "tar zxf {:s}".format(mtp_script_pkg)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to execute {:s} on MTP Chassis".format(cmd))
    cmd = "sync"
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=300):
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to execute {:s} on MTP Chassis".format(cmd))
    cmd = "rm -f {:s}".format(mtp_script_pkg)
    os.system(cmd)

    for loop in range(iteration):
        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        libmfg_utils.cli_inf(mtp_cli_id_str + "Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY))
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        libmfg_utils.cli_inf(mtp_cli_id_str + "Power off APC")
        mtp_mgmt_ctrl.mtp_apc_pwr_off()

        time.sleep(1)

        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        libmfg_utils.cli_inf(mtp_cli_id_str + "Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY))
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to connect MTP Chassis")

        # go to mtp_regression and Start the regression
        cmd = "cd {:s}".format(mtp_script_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "./mtp_diag_regression.py --mtpid {:s}".format(mtp_id)
        cmd += " --psu-check"
        if stop_on_err:
            cmd += " --stop-on-error &"
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=3000)
            
        # Copy log file from MTP Chassis
        mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
        ipaddr = mtp_mgmt_cfg[0]
        userid = mtp_mgmt_cfg[1]
        passwd = mtp_mgmt_cfg[2]
 
        mtp_test_log_file = mtp_diag_dir + mtp_script_dir + "mtp_test.log"
        mtp_diag_input_log_file = mtp_diag_dir + mtp_script_dir + "mtp_diag_input.log"
        mtp_diag_output_log_file = mtp_diag_dir + mtp_script_dir + "mtp_diag_output.log"
        mtp_diagmgr_log_file = mtp_diag_dir + mtp_script_dir + "mtp_diagmgr.log"
        local_test_log_file = "log/mtp_test.{:d}.log".format(loop)
        local_diag_input_log_file = "log/mtp_diag_input.{:d}.log".format(loop)
        local_diag_output_log_file = "log/mtp_diag_output.{:d}.log".format(loop)
        local_diagmgr_log_file = "log/mtp_diagmgr.{:d}.log".format(loop)

        libmfg_utils.network_get_file(ipaddr, userid, passwd, local_test_log_file, mtp_test_log_file)
        libmfg_utils.network_get_file(ipaddr, userid, passwd, local_diag_input_log_file, mtp_diag_input_log_file)
        libmfg_utils.network_get_file(ipaddr, userid, passwd, local_diag_output_log_file, mtp_diag_output_log_file)
        libmfg_utils.network_get_file(ipaddr, userid, passwd, local_diagmgr_log_file, mtp_diagmgr_log_file)
        os.system("sync")
 
        if "Diag Regression Test Fail" in open(local_test_log_file).read():
            libmfg_utils.email_report(email_to, mtp_cli_id_str + "Diag Regression Test Iteration - {:d} Failed".format(loop))
        else:
            libmfg_utils.email_report(email_to, mtp_cli_id_str + "Diag Regression Test Iteration - {:d} Passed".format(loop))


if __name__ == "__main__":
    main()
