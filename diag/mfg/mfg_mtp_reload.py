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
    parser = argparse.ArgumentParser(description="Diag MTP Reload", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--image", help="New MTP image file")
    parser.add_argument("--nic-image", help="New NIC image file")
    parser.add_argument("--apc", help="MTP is power down, need to power on apc first", action='store_true')
    parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])

    skip_image_update = True
    nic_image_file = None
    apc = False

    args = parser.parse_args()
    if args.apc:
        apc = True
    if args.image:
        mtp_image_file = args.image
        skip_image_update = False
    if args.nic_image:
        nic_image_file = args.nic_image

    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/swi_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/fst_mtps_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)

    sub_mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)

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

    if not skip_image_update:
        if "amd64" not in mtp_image_file:
            mtp_mgmt_ctrl.cli_log_err("Wrong MTP Chassis image: {:s}".format(mtp_image_file), level=0)
            return
        for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
            mtp_mgmt_ctrl.cli_log_inf("Copy MTP Chassis image: {:s}".format(mtp_image_file), level=0)
            mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
            mtp_ip_addr = mtp_mgmt_cfg[0]
            mtp_usrid = mtp_mgmt_cfg[1]
            mtp_passwd = mtp_mgmt_cfg[2]
            remote_dir = "/home/diag/"
            if not libmfg_utils.network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir):
                libmfg_utils.sys_exit(mtp_cli_id_str + "Copy MTP Chassis image: {:s} failed".format(mtp_image_file))
            else:
                mtp_mgmt_ctrl.cli_log_inf("Copy MTP Chassis image: {:s} complete".format(mtp_image_file), level=0)

            mtp_mgmt_ctrl.cli_log_inf("Update MTP Chassis image: {:s}".format(os.path.basename(mtp_image_file)), level=0)
            mtp_mgmt_ctrl.mtp_update_mtp_diag_image(remote_dir + os.path.basename(mtp_image_file))

    if nic_image_file:
        if "arm64" not in nic_image_file:
            mtp_mgmt_ctrl.cli_log_err("Wrong NIC image: {:s}".format(nic_image_file), level=0)
            return
        for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
            mtp_mgmt_ctrl.cli_log_inf("Copy NIC Diag image: {:s}".format(nic_image_file), level=0)
            mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
            mtp_ip_addr = mtp_mgmt_cfg[0]
            mtp_usrid = mtp_mgmt_cfg[1]
            mtp_passwd = mtp_mgmt_cfg[2]
            remote_dir = "/home/diag/"
            if not libmfg_utils.network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, nic_image_file, remote_dir):
                libmfg_utils.sys_exit(mtp_cli_id_str + "Copy NIC Diag image: {:s} failed".format(nic_image_file))
            else:
                mtp_mgmt_ctrl.cli_log_inf("Copy NIC Diag image: {:s} complete".format(nic_image_file), level=0)

            mtp_mgmt_ctrl.cli_log_inf("Update NIC Diag image: {:s}".format(os.path.basename(nic_image_file)), level=0)
            mtp_mgmt_ctrl.mtp_update_nic_diag_image(remote_dir + os.path.basename(nic_image_file))
            mtp_mgmt_ctrl.cli_log_inf("Update NIC Diag image {:s} complete".format(os.path.basename(nic_image_file)), level=0)

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to connect MTP chassis")
            mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected", level=0)

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis Reload Complete", level=0)

        # init MTP diag environment
        if not mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null"):
            mtp_mgmt_ctrl.cli_log_err("MTP Diag Pre Init failed", level=0)
            return

        if not mtp_mgmt_ctrl.mtp_sys_info_disp():
            mtp_mgmt_ctrl.cli_log_err("Unable to retrieve system info", level=0)

        if not mtp_mgmt_ctrl.mtp_hw_init(MTP_Const.MFG_EDVT_NORM_FAN_SPD):
            mtp_mgmt_ctrl.cli_log_err("Init MTP HW fails", level=0)

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.mtp_mgmt_disconnect()

if __name__ == "__main__":
    main()
