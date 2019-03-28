#!/usr/bin/env python

import sys
import os
import time
import datetime
import pexpect
import argparse
import re
import random

sys.path.append(os.path.relpath("../lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libpro_srv_db import pro_srv_db


def get_pro_srv_id():
    product_server_cfg_file = os.path.abspath("../config/pensando_pro_srv1_cfg.yaml")
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
    product_server_cfg_file = os.path.abspath("../config/pensando_pro_srv1_cfg.yaml")
    pro_srv_cfg_db = pro_srv_db(pro_srv_cfg_file = product_server_cfg_file)
    pro_srv_list = list(pro_srv_cfg_db.get_pro_srv_id_list())
    if len(pro_srv_list) > 1:
        pro_srv_id = libmfg_utils.single_select_menu("Select Product Server", pro_srv_list)
        if not pro_srv_id:
            return None
    else:
        pro_srv_id = pro_srv_list[0]
    filename = pro_srv_cfg_db.get_pro_srv_mtp_chassis_cfg_file(pro_srv_id)
    mtp_chassis_cfg_file = os.path.abspath("../config/" + filename)
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)
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
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg, dbg_mode=True)
    return mtp_mgmt_ctrl


def main():
    parser = argparse.ArgumentParser(description="NIC MGMT test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtp", help="MTP Chassis ID", required=True)
    parser.add_argument("--apc", help="MTP Chassis is powered down, need to power on APC", action='store_true')
    parser.add_argument("--mtp-reload", help="Iterations of the MTP reload", type=int, required=True)
    parser.add_argument("--nic-reload", help="Iterations of the NIC reload", type=int, required=True)

    args = parser.parse_args()
    mtp_id = args.mtp
    mtp_reload = args.mtp_reload
    nic_reload = args.nic_reload
    if args.apc:
        apc = True
    else:
        apc = False

    mtp_cfg_db = load_mtp_cfg()
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    diag_log_filep = open("../log/nic_mgmt_diag.log", 'w+')
    diag_nic_log_filep_list = [diag_log_filep] * MTP_Const.MTP_SLOT_NUM 
    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list)

    if apc:
        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    # power cycle nic
    for mtp_loop in range(mtp_reload):
        mtp_mgmt_ctrl.cli_log_inf("##########################################", level=0)
        mtp_mgmt_ctrl.cli_log_inf("####### Power cycle MTP Iter - {:2d} #######".format(mtp_loop), level=0)
        mtp_mgmt_ctrl.cli_log_inf("##########################################", level=0)
        mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP chassis", level=0)
            return
        mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected\n", level=0)

        # get the diag version info
        sw_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
        if not sw_ver:
            mtp_mgmt_ctrl.cli_log_err("Get MTP SW version fails", level=0)
            return 
        mtp_mgmt_ctrl.cli_log_inf("MTP SW version: {:s}".format(sw_ver), level=0)

        # get the asic version info
        asic_ver = mtp_mgmt_ctrl.mtp_get_asic_version()
        if not asic_ver:
            mtp_mgmt_ctrl.cli_log_err("Get MTP ASIC version fails", level=0)
            return 
        mtp_mgmt_ctrl.cli_log_inf("MTP ASIC version: {:s}".format(asic_ver), level=0)


        # diag environment pre init
        if not mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null"):
            mtp_mgmt_ctrl.cli_log_err("Init MTP Diag Environment fails", level=0)
            return

        # get the hw version info
        cpld_ver_list = mtp_mgmt_ctrl.mtp_get_hw_version()
        if not cpld_ver_list:
            mtp_mgmt_ctrl.cli_log_err("Get MTP CPLD version fails", level=0)
            return
        mtp_mgmt_ctrl.cli_log_inf("MTP IO-CPLD version: {:s}, JTAG-CPLD version: {:s}".format(cpld_ver_list[0], cpld_ver_list[1]), level=0)

        if not mtp_mgmt_ctrl.mtp_hw_init(MTP_Const.MFG_EDVT_NORM_FAN_SPD):
            mtp_mgmt_ctrl.cli_log_err("Init MTP HW fails", level=0)
            return

        for nic_loop in range(nic_reload):
            mtp_mgmt_ctrl.cli_log_inf("##########################################", level=0)
            mtp_mgmt_ctrl.cli_log_inf("####### Power cycle NIC Iter - {:2d} #######".format(nic_loop), level=0)
            mtp_mgmt_ctrl.cli_log_inf("##########################################", level=0)
            mtp_mgmt_ctrl.mtp_power_off_nic()
            mtp_mgmt_ctrl.mtp_power_on_nic()
            if not mtp_mgmt_ctrl.mtp_nic_init():
                mtp_mgmt_ctrl.mtp_enter_user_ctrl()
            if not mtp_mgmt_ctrl.mtp_nic_diag_init():
                mtp_mgmt_ctrl.mtp_enter_user_ctrl()

        if mtp_loop == mtp_reload - 1:
            break

        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC\n".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
        mtp_mgmt_ctrl.mtp_apc_pwr_off()

        time.sleep(MTP_Const.MTP_POWER_CYCLE_DELAY)

        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    diag_log_filep.close()

    return

if __name__ == "__main__":
    main()

