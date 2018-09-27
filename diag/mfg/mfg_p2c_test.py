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


def get_mtp_logfile(log_dir, mtp_cfg_db, mtp_id):
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
 
    mtp_test_log_file = log_dir + "mtp_test.log"
    mtp_diag_log_file = log_dir + "mtp_diag.log"
    mtp_diagmgr_log_file = log_dir + "mtp_diagmgr.log"
    local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
    local_diag_log_file = "log/{:s}_mtp_diag.log".format(mtp_id)
    local_diagmgr_log_file = "log/{:s}_mtp_diagmgr.log".format(mtp_id)

    libmfg_utils.network_get_file(ipaddr, userid, passwd, local_test_log_file, mtp_test_log_file)
    libmfg_utils.network_get_file(ipaddr, userid, passwd, local_diag_log_file, mtp_diag_log_file)
    libmfg_utils.network_get_file(ipaddr, userid, passwd, local_diagmgr_log_file, mtp_diagmgr_log_file)
 

def test_report(mtp_id):
    mtp_cli_id_str = libmfg_utils.id_str(mtp=mtp_id)
    local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
    return
    if "Diag Regression Test Fail" in open(local_test_log_file).read():
        libmfg_utils._report(mtp_cli_id_str + "Diag Regression Test Failed")
        return False
    else:
        libmfg_utils._report(mtp_cli_id_str + "Diag Regression Test Passed")
        return True


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


def load_mtp_cfg(pro_srv_id):
    product_server_cfg_file = os.path.abspath("config/pensando_pro_srv1_cfg.yaml")
    pro_srv_cfg_db = pro_srv_db(pro_srv_cfg_file = product_server_cfg_file)
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
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')

    args = parser.parse_args()

    verbosity = False
    stop_on_err = False

    if args.stop_on_error:
        libmfg_utils.cli_inf("Test will stop if any test error out")
        stop_on_err = True
    if args.verbosity:
        verbosity = True

    srv_log_filep = open("log/srv.log", "w+")
    pro_srv_id = get_pro_srv_id()
    mtp_cfg_db = load_mtp_cfg(pro_srv_id)
    mtp_id = get_mtpid(mtp_cfg_db)
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    scan_cfg_filep  = open("config/{:s}.yaml".format(mtp_id), "w+")

    # Init MTP Control
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, srv_log_filep, sys.stdout, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg, dbg_mode = verbosity)

    # barcode scan process
    libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Start the Barcode Scan Process")
    while True:
        scan_rslt = mtp_mgmt_ctrl.mtp_barcode_scan(False)
        if scan_rslt:
            break;
        libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Restart the Barcode Scan Process")
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
    libmfg_utils.cli_log_rslt("Barcode Scan Summary", pass_rslt_list, fail_rslt_list, srv_log_filep)
    mtp_mgmt_ctrl.gen_barcode_config_file(pro_srv_id, scan_cfg_filep, scan_rslt)
    scan_cfg_filep.close()
    os.system("sync")

    # package the test script
    cmd = "cp -r lib/ config/ mtp_regression/"
    os.system(cmd)
    mtp_script_dir = "mtp_regression/"
    mtp_script_pkg = "mtp_regression.tar"
    mtp_diag_dir = "/home/diag/"
    cmd = "tar czf {:s} {:s}".format(mtp_script_pkg, mtp_script_dir)
    os.system(cmd)
    cmd = "rm -rf mtp_regression/lib mtp_regression/config"
    os.system(cmd)

    # Power on MTP 
    mtp_mgmt_ctrl.mtp_apc_pwr_on()
    libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY))
    libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        libmfg_utils.cli_log_err(srv_log_filep, mtp_cli_id_str + "Unable to connect MTP Chassis")
        return

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

    libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Regression Test on {:s} start".format(mtp_id))
    # go to mtp_regression and Start the regression
    cmd = "cd {:s}".format(mtp_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd = "./mtp_diag_regression.py --mtpid {:s}".format(mtp_id)
    cmd += " --psu-check"
    if stop_on_err:
        cmd += " --stop-on-error"
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.DIAG_REGRESSION_TIMEOUT)
        
    libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Regression Test on {:s} complete".format(mtp_id))

    get_mtp_logfile(mtp_diag_dir+mtp_script_dir, mtp_cfg_db, mtp_id)
    if not test_report(mtp_id) and stop_on_err:
        return

    mtp_mgmt_ctrl.mtp_mgmt_poweroff()
    libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY))
    libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
    libmfg_utils.cli_log_inf(srv_log_filep, mtp_cli_id_str + "Power off APC")
    mtp_mgmt_ctrl.mtp_apc_pwr_off()

    srv_log_filep.close()
    os.system("sync")


if __name__ == "__main__":
    main()
