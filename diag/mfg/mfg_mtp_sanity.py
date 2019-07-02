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

    args = parser.parse_args()
    if args.apc:
        apc = True
    else:
        apc = False

    mtp_chassis_cfg_file = os.path.abspath("config/pensando_pro_srv1_mtp_chassis_cfg.yaml")
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)
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
        for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
            mtp_mgmt_ctrl.mtp_apc_pwr_on()
            mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    for mtp_id, mtp_mgmt_ctrl in zip(sub_mtpid_list, mtp_mgmt_ctrl_list):
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

        # get the absolute file path
        nic_firmware_cfg_file = os.path.abspath("config/nic_firmware_cfg.yaml")
        nic_fw_cfg = libmfg_utils.load_cfg_from_yaml(nic_firmware_cfg_file)

        v02_img_file_list = list()
        v03_img_file_list = list()
        if mtp_capability & 0x1:
            naples100_cpld_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.NAPLES100]["CPLD_FILE"])
            v02_img_file_list.append(naples100_cpld_img_file)
            naples100_sec_cpld_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.NAPLES100]["SEC_CPLD_FILE"])
            v02_img_file_list.append(naples100_sec_cpld_img_file)
            naples100_qspi_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.NAPLES100]["QSPI_FILE"])
            v02_img_file_list.append(naples100_qspi_img_file)
            naples100_emmc_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.NAPLES100]["EMMC_FILE"])
            v02_img_file_list.append(naples100_emmc_img_file)

            vomero_cpld_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.VOMERO]["CPLD_FILE"])
            v02_img_file_list.append(vomero_cpld_img_file)
            vomero_sec_cpld_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.VOMERO]["SEC_CPLD_FILE"])
            v02_img_file_list.append(vomero_sec_cpld_img_file)
            vomero_qspi_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.VOMERO]["QSPI_FILE"])
            v02_img_file_list.append(vomero_qspi_img_file)
            vomero_emmc_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.VOMERO]["EMMC_FILE"])
            v02_img_file_list.append(vomero_emmc_img_file)

        if mtp_capability & 0x2:
            naples25_cpld_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.NAPLES25]["CPLD_FILE"])
            v03_img_file_list.append(naples25_cpld_img_file)
            naples25_sec_cpld_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.NAPLES25]["SEC_CPLD_FILE"])
            v03_img_file_list.append(naples25_sec_cpld_img_file)
            naples25_qspi_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.NAPLES25]["QSPI_FILE"])
            v03_img_file_list.append(naples25_qspi_img_file)
            naples25_emmc_img_file = "release/" + os.path.basename(nic_fw_cfg[NIC_Type.NAPLES25]["EMMC_FILE"])
            v03_img_file_list.append(naples25_emmc_img_file)

        for img_file in v02_img_file_list + v03_img_file_list:
            if not libmfg_utils.file_exist(img_file):
                mtp_mgmt_ctrl.cli_log_err("Firmware image {:s} doesn't exist... Abort", level=0)
                return

            mtp_mgmt_ctrl.cli_log_inf("Copy Firmware image: {:s}".format(img_file), level=0)
            mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
            mtp_ip_addr = mtp_mgmt_cfg[0]
            mtp_usrid = mtp_mgmt_cfg[1]
            mtp_passwd = mtp_mgmt_cfg[2]
            image_dir = "/home/diag/"
            if not libmfg_utils.network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, img_file, image_dir):
                mtp_mgmt_ctrl.cli_log_err("Copy Firmware image {:s} failed... Abort", level=0)
                return
            mtp_mgmt_ctrl.cli_log_inf("Copy Firmware image: {:s} complete".format(img_file), level=0)

        # diag environment post init
        if not mtp_mgmt_ctrl.mtp_diag_post_init(mtp_capability):
            mtp_mgmt_ctrl.cli_log_err("MTP Diag Post Init failed", level=0)
            return

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        if not mtp_mgmt_ctrl.mtp_sys_info_disp():
            mtp_mgmt_ctrl.cli_log_err("Unable to retrieve MTP system info", level=0)
            return

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC\n".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)

    libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)

    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
        mtp_mgmt_ctrl.mtp_apc_pwr_off()

    libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)

if __name__ == "__main__":
    main()
