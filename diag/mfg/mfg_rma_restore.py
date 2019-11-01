#!/usr/bin/env python

import sys
import os
import time
import pexpect
import argparse
import re

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl


def main():
    parser = argparse.ArgumentParser(description="MTP Set NIC to Diag boot", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--apc", help="MTP is power down, need to power on apc first", action='store_true')

    apc = False
    args = parser.parse_args()
    if args.apc:
        apc = True

    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    sub_mtpid_list = libmfg_utils.multiple_select_menu("Select MTP Chassis", mtpid_list)
    mtp_mgmt_ctrl_list = list()

    for mtp_id in sub_mtpid_list:
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
        # power on the mtp chassis
        libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to connect MTP chassis")
        mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected", level=0)

        # init MTP diag environment
        if not mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null"):
            mtp_mgmt_ctrl.cli_log_err("MTP Diag Pre Init failed", level=0)
            return

        if not mtp_mgmt_ctrl.mtp_sys_info_disp():
            mtp_mgmt_ctrl.cli_log_err("Unable to retrieve MTP system info", level=0)
            return

        if not mtp_mgmt_ctrl.mtp_hw_init(MTP_Const.MFG_EDVT_NORM_FAN_SPD):
            mtp_mgmt_ctrl.cli_log_err("Init MTP HW fails", level=0)
            return

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        # init nic type list
        mtp_mgmt_ctrl.mtp_init_nic_type()

        # get nic present list
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        # power cycle the NICs
        mtp_mgmt_ctrl.mtp_power_cycle_nic()

        # init the nic diag environment
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if nic_prsnt_list[slot]:
                if not mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(slot):
                    continue

        # power off the NICs
        mtp_mgmt_ctrl.mtp_power_off_nic()

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

if __name__ == "__main__":
    main()
