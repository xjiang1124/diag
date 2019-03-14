#!/usr/bin/env python

import sys
import os
import time
import pexpect
import argparse
import re
import random

sys.path.append(os.path.relpath("../lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libpro_srv_db import pro_srv_db


def main():
    parser = argparse.ArgumentParser(description="Diag MTP Reload", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--image", help="New MTP image file")
    parser.add_argument("--nic-image", help="New NIC image file")
    parser.add_argument("--qspi-image", help="New QSPI image file")
    parser.add_argument("--emmc-image", help="New EMMC image file")
    parser.add_argument("--cpld-image", help="New CPLD image file")
    parser.add_argument("--reset-nic", help="Reset NIC boot with diag image", action='store_true')
    parser.add_argument("--apc", help="MTP is power down, need to power on apc first", action='store_true')
    parser.add_argument("--mtp", help="MTP ID")

    skip_image_update = True
    nic_image_file = None
    qspi_image_file = None
    emmc_image_file = None
    cpld_image_file = None
    apc = False
    mtp_id = None
    reset_nic = False

    args = parser.parse_args()
    if args.apc:
        apc = True
    if args.mtp:
        mtp_id = args.mtp
    if args.image:
        mtp_image_file = args.image
        skip_image_update = False
    if args.nic_image:
        nic_image_file = args.nic_image
    if args.emmc_image:
        emmc_image_file = args.emmc_image
    if args.qspi_image:
        qspi_image_file = args.qspi_image
    if args.cpld_image:
        cpld_image_file = args.cpld_image
    if args.reset_nic:
        reset_nic = True

    # get the absolute file path
    product_server_cfg_file = os.path.abspath("../config/pensando_pro_srv1_cfg.yaml")

    # load the product server config
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
    mtp_chassis_cfg_file = os.path.abspath("../config/" + filename)
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())

    if not mtp_id:
        mtp_id = libmfg_utils.single_select_menu("Select MTP Chassis", mtpid_list)
    elif mtp_id not in mtpid_list:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Invalid MTP ID: {:s}".format(mtp_id))

    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    # find the mtp management config based on the mtpid
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")

    # find the apc config based on the mtpid
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, None, None, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg)

    if apc:
        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to connect MTP chassis")
    mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected", level=0)

    if not skip_image_update:
        if "amd64" not in mtp_image_file:
            mtp_mgmt_ctrl.cli_log_err("Wrong MTP Chassis image: {:s}".format(mtp_image_file), level=0)
            return
        mtp_mgmt_ctrl.cli_log_inf("Copy MTP Chassis image: {:s}".format(mtp_image_file), level=0)
        mtp_ip_addr = mtp_mgmt_cfg[0]
        mtp_usrid = mtp_mgmt_cfg[1]
        mtp_passwd = mtp_mgmt_cfg[2]
        remote_dir = "/home/diag/"
        if not libmfg_utils.network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir):
            libmfg_utils.sys_exit(mtp_cli_id_str + "Copy MTP Chassis image: {:s} failed".format(mtp_image_file))
        else:
            mtp_mgmt_ctrl.cli_log_inf("Copy MTP Chassis image: {:s} complete".format(mtp_image_file), level=0)

        pre_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
        mtp_mgmt_ctrl.cli_log_inf("Update MTP Chassis image: {:s}".format(os.path.basename(mtp_image_file)), level=0)
        mtp_mgmt_ctrl.mtp_update_sw_image(remote_dir + os.path.basename(mtp_image_file))
        post_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
        mtp_mgmt_ctrl.cli_log_inf("Update MTP chassis image from {:s} to {:s} complete".format(pre_ver, post_ver), level=0)

    if nic_image_file:
        if "arm64" not in nic_image_file:
            mtp_mgmt_ctrl.cli_log_err("Wrong NIC image: {:s}".format(nic_image_file), level=0)
            return
        mtp_mgmt_ctrl.cli_log_inf("Copy NIC Diag image: {:s}".format(nic_image_file), level=0)
        mtp_ip_addr = mtp_mgmt_cfg[0]
        mtp_usrid = mtp_mgmt_cfg[1]
        mtp_passwd = mtp_mgmt_cfg[2]
        nic_image_dir = "/home/diag/nic_diag/"
        cmd = "mkdir -p {:s}".format(nic_image_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        if not libmfg_utils.network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, nic_image_file, nic_image_dir):
            libmfg_utils.sys_exit(mtp_cli_id_str + "Copy NIC Diag image: {:s} failed".format(nic_image_file))
        else:
            mtp_mgmt_ctrl.cli_log_inf("Copy NIC Diag image: {:s} complete".format(nic_image_file), level=0)

        mtp_mgmt_ctrl.cli_log_inf("Unpack NIC Diag image: {:s}".format(os.path.basename(nic_image_file)), level=0)
        cmd = "tar zxf {:s} -C {:s}".format(nic_image_dir+os.path.basename(nic_image_file), nic_image_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        mtp_mgmt_ctrl.cli_log_inf("Unpack NIC Diag image {:s} complete".format(os.path.basename(nic_image_file)), level=0)

    for image_file in [emmc_image_file, qspi_image_file, cpld_image_file]:
        if image_file:
            mtp_mgmt_ctrl.cli_log_inf("Copy NIC image: {:s}".format(image_file), level=0)
            mtp_ip_addr = mtp_mgmt_cfg[0]
            mtp_usrid = mtp_mgmt_cfg[1]
            mtp_passwd = mtp_mgmt_cfg[2]
            image_dir = "/home/diag/"
            if not libmfg_utils.network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, image_file, image_dir):
                libmfg_utils.sys_exit(mtp_cli_id_str + "Copy NIC image: {:s} failed".format(image_file))
            else:
                mtp_mgmt_ctrl.cli_log_inf("Copy NIC image: {:s} complete".format(image_file), level=0)

    mtp_mgmt_ctrl.mtp_power_cycle()

    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to connect MTP Chassis")
    mtp_mgmt_ctrl.cli_log_inf("MTP Chassis Reload Complete", level=0)

    # init MTP diag environment
    mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null")

    sw_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
    asic_ver = mtp_mgmt_ctrl.mtp_get_asic_version()
    cpld_io_ver, cpld_jtag_ver = mtp_mgmt_ctrl.mtp_get_hw_version()
    mtp_mgmt_ctrl.cli_log_inf("Diag version={:s}, ASIC version={:s}".format(sw_ver,asic_ver), level=0)
    mtp_mgmt_ctrl.cli_log_inf("MTP IO CPLD version={:s}, JTAG CPLD version={:s}".format(cpld_io_ver,cpld_jtag_ver), level=0)

    if reset_nic:
        # init nic present list
        mtp_mgmt_ctrl.mtp_init_nic_prsnt()

        # init nic type list
        mtp_mgmt_ctrl.mtp_init_nic_type()

        # get nic present list
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        # power cycle the NICs
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.mtp_power_on_nic()

        # init the nic diag environment
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if nic_prsnt_list[slot]:
                if not mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(slot):
                    continue
                if not mtp_mgmt_ctrl.mtp_power_off_single_nic(slot):
                    continue

    mtp_mgmt_ctrl.mtp_enter_user_ctrl()

if __name__ == "__main__":
    main()
