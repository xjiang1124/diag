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
    parser = argparse.ArgumentParser(description="Diag connect to MTP", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--apc", help="MTP is power down, need to power on apc first", action='store_true')
    parser.add_argument("--init", help="Init the diag environment", action='store_true')
    parser.add_argument("--mtp", help="MTP ID")

    apc = False
    diag_init = False
    mtp_id = None
    args = parser.parse_args()
    if args.apc:
        apc = True
    if args.init:
        diag_init = True
    if args.mtp:
        mtp_id = args.mtp

    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/kpt_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)

    if not mtp_id:
        mtpid_list = list(mtp_cfg_db.get_mtpid_list())
        mtp_id = libmfg_utils.single_select_menu("Select MTP Chassis", mtpid_list)

    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    # find the mtp management config based on the mtpid
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")

    # find the apc config based on the mtpid
    if apc:
        mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
        if not mtp_apc_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    else:
        mtp_apc_cfg = None

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, None, None, [None] * 10, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg, dbg_mode=True)

    if apc:
        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP chassis", level=0)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected", level=0)

    if diag_init:
        # init MTP diag environment
        if not mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null"):
            mtp_mgmt_ctrl.cli_log_err("MTP Diag Pre Init failed", level=0)
            return

        if not mtp_mgmt_ctrl.mtp_sys_info_disp():
            mtp_mgmt_ctrl.cli_log_err("Unable to retrieve system info", level=0)
            return

        if not mtp_mgmt_ctrl.mtp_hw_init(MTP_Const.MFG_EDVT_NORM_FAN_SPD):
            mtp_mgmt_ctrl.cli_log_err("Init MTP HW fails", level=0)
            return

        if not mtp_mgmt_ctrl.mtp_nic_init():
            mtp_mgmt_ctrl.cli_log_err("Init NIC fails", level=0)
            return

        mtp_mgmt_ctrl.mtp_power_cycle_nic()

        if not mtp_mgmt_ctrl.mtp_nic_diag_init():
            mtp_mgmt_ctrl.cli_log_err("Init NIC Diag fails", level=0)
            return

    mtp_mgmt_ctrl.mtp_enter_user_ctrl()

if __name__ == "__main__":
    main()
