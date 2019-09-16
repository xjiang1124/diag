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
    parser = argparse.ArgumentParser(description="MTP Update NIC CPLD", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--apc", help="MTP is power down, need to power on apc first", action='store_true')

    apc = False
    args = parser.parse_args()
    if args.apc:
        apc = True

    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    mtp_id = libmfg_utils.single_select_menu("Select MTP Chassis", mtpid_list)
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    # find the mtp management config based on the mtpid
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")

    # find the apc config based on the mtpid
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")

    log_filep_list = list()
    diag_log_filep = open("log/{:s}_cpld_update.log".format(mtp_id), 'w+')
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = "log/{:s}_{:s}_cpld_update.log".format(mtp_id, key)
        diag_nic_log_filep = open(diag_nic_log_file, "w+")
        log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, None, diag_log_filep, log_filep_list, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg)

    if apc:
        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

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

    # get the absolute file path
    nic_firmware_cfg_file = os.path.abspath("config/nic_firmware_cfg.yaml")
    nic_fw_cfg = libmfg_utils.load_cfg_from_yaml(nic_firmware_cfg_file)
    naples100_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["CPLD_FILE"]
    vomero_cpld_img_file = nic_fw_cfg[NIC_Type.VOMERO]["CPLD_FILE"]
    naples25_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["CPLD_FILE"]

    # init nic type list
    mtp_mgmt_ctrl.mtp_init_nic_type()

    # get nic present list
    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

    # power cycle the NICs
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    mtp_mgmt_ctrl.mtp_nic_diag_init()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if nic_prsnt_list[slot]:
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES100 or card_type == NIC_Type.FORIO:
                cpld_img_file = naples100_cpld_img_file
            elif card_type == NIC_Type.VOMERO:
                cpld_img_file = vomero_cpld_img_file
            elif card_type == NIC_Type.NAPLES25:
                cpld_img_file = naples25_cpld_img_file
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")
                continue
            mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
            mtp_mgmt_ctrl.mtp_refresh_nic_cpld(slot)

    # power cycle the NICs
    mtp_mgmt_ctrl.mtp_power_cycle_nic()
    mtp_mgmt_ctrl.mtp_nic_diag_init()

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if nic_prsnt_list[slot]:
            mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)

    # power off the NICs
    mtp_mgmt_ctrl.mtp_power_off_nic()

    mtp_mgmt_ctrl.mtp_mgmt_poweroff()
    mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
    mtp_mgmt_ctrl.mtp_apc_pwr_off()
    mtp_mgmt_ctrl.cli_log_inf("Power off APC, Wait {:d} seconds for APC shutdown".format(MTP_Const.MTP_POWER_CYCLE_DELAY), level=0)
    libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)

    diag_log_filep.close()
    for log_filep in log_filep_list:
        log_filep.close()

if __name__ == "__main__":
    main()
