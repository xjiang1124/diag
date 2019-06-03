#!/usr/bin/env python

import sys
import os
import time
import pexpect
import argparse
import re
import random

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libpro_srv_db import pro_srv_db


def main():
    parser = argparse.ArgumentParser(description="MFG MTP Sanity", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--apc", help="MTP is power down, need to power on apc first", action='store_true')
    parser.add_argument("--group", help="MFG MTP group", required=True)

    args = parser.parse_args()
    group = args.group
    if args.apc:
        apc = True
    else:
        apc = False

    if group == "DL":
        filename = "dl_p2c_mtp_chassis_cfg.yaml"
    elif group == "P2C":
        filename = "dl_p2c_mtp_chassis_cfg.yaml"
    elif group == "4C":
        filename = "4c_mtp_chassis_cfg.yaml"
    elif group == "FST":
        filename = "fst_mtp_chassis_cfg.yaml"
    else:
        libmfg_utils.sys_exit("Unknown MFG MTP Group: {:s}".format(group))

    mtp_chassis_cfg_file = os.path.abspath("config/" + filename)
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    mtp_mgmt_ctrl_list = list()

    for mtp_id in mtpid_list:
        mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

        # find the mtp management config based on the mtpid
        mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
        if not mtp_mgmt_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")

        # find the apc config based on the mtpid
        mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
        if not mtp_apc_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")

        mtp_mgmt_ctrl = mtp_ctrl(mtp_id, None, None, [None]*10, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg)
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)

    if apc:
        for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
            mtp_mgmt_ctrl.mtp_apc_pwr_on()
            mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to connect MTP chassis")
        mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected", level=0)

        # init MTP diag environment
        if not mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null"):
            mtp_mgmt_ctrl.cli_log_err("MTP Diag Pre Init failed", level=0)
            return

        if not mtp_mgmt_ctrl.mtp_hw_init(MTP_Const.MFG_EDVT_NORM_FAN_SPD):
            mtp_mgmt_ctrl.cli_log_err("Init MTP HW fails", level=0)
            return

        # find the mtp capability
        mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
        # diag environment post init
        if not mtp_mgmt_ctrl.mtp_diag_post_init(mtp_capability):
            mtp_mgmt_ctrl.cli_log_err("MTP Diag Post Init failed", level=0)
            return

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        sw_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
        os_ver = mtp_mgmt_ctrl.mtp_get_os_version()
        asic_ver = mtp_mgmt_ctrl.mtp_get_asic_version()
        cpld_io_ver, cpld_jtag_ver = mtp_mgmt_ctrl.mtp_get_hw_version()
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag version={:s}".format(sw_ver), level=0)
        mtp_mgmt_ctrl.cli_log_inf("MTP OS version={:s}".format(os_ver), level=0)
        mtp_mgmt_ctrl.cli_log_inf("MTP ASIC version={:s}".format(asic_ver), level=0)
        mtp_mgmt_ctrl.cli_log_inf("MTP IO CPLD version={:s}, JTAG CPLD version={:s}".format(cpld_io_ver,cpld_jtag_ver), level=0)

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to connect MTP chassis")
        mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected", level=0)
        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC\n".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)

    libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
        mtp_mgmt_ctrl.mtp_apc_pwr_off()

    libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)

if __name__ == "__main__":
    main()
