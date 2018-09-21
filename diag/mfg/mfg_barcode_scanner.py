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
from libpro_srv_ctrl import pro_srv_ctrl


# generate the local barcode config file
def gen_barcode_config_file(pro_srv_id, file_p, scan_rslt):
    config_lines = [str(scan_rslt["MTP_ID"]) + ":"]
    tmp = "    SRV: " + pro_srv_id
    config_lines.append(tmp)
    tmp = "    TS: " +  scan_rslt["MTP_TS"]
    config_lines.append(tmp)
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        tmp = "    " + key + ":"
        config_lines.append(tmp)

        if scan_rslt[key]["NIC_VALID"]:
            tmp = "        VALID: \"Yes\""
            config_lines.append(tmp)
            tmp = "        SN: \"" + scan_rslt[key]["NIC_SN"] + "\""
            config_lines.append(tmp)
            tmp = "        MAC: \"" + scan_rslt[key]["NIC_MAC"] + "\""
            config_lines.append(tmp)
            tmp = "        TS: " + scan_rslt[key]["NIC_TS"]
            config_lines.append(tmp)
        else:
            tmp = "        VALID: \"No\""
            config_lines.append(tmp)

    for line in config_lines:
        file_p.write(line + "\n")


def main():
    parser = argparse.ArgumentParser(description="MFG Barcode Scanner Utility", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--error-injection", help="The utility will randomly generate error", action='store_true')
    parser.add_argument("--verbosity", help="display more debug information", action='store_true')

    err_inj = False
    verbosity = False
    args = parser.parse_args()
    if args.error_injection:
        err_inj = True
    if args.verbosity:
        verbosity = True

    # get the absolute file path
    nic_firmware_cfg_file = os.path.abspath("config/nic_firmware_cfg.yaml")
    product_server_cfg_file = os.path.abspath("config/pensando_pro_srv1_cfg.yaml")

    # load the product server config
    pro_srv_cfg_db = pro_srv_db(pro_srv_cfg_file = product_server_cfg_file)
    pro_srv_list = list(pro_srv_cfg_db.get_pro_srv_id_list())
    if len(pro_srv_list) > 1:
        pro_srv_id = libmfg_utils.single_select_menu("Choose Product Server", pro_srv_list)
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
    # find the mtp management config based on the mtpid
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")

    # find the apc config based on the mtpid
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")

    # local log files
    scan_cfg_file = "_".join(["barcode_cfg", pro_srv_id, mtp_id, libmfg_utils.get_timestamp()]) + ".yaml"
    test_log_file = "_".join(["test_dl", pro_srv_id, mtp_id, libmfg_utils.get_timestamp()]) + ".log"
    diag_log_file = "_".join(["diag_dl", pro_srv_id, mtp_id, libmfg_utils.get_timestamp()]) + ".log"
    asic_log_file = "_".join(["asic_dl", pro_srv_id, mtp_id, libmfg_utils.get_timestamp()]) + ".log"
    scan_cfg_filep = open(scan_cfg_file, "w+")
    diag_log_filep = open(diag_log_file, "w+")
    test_log_filep = open(test_log_file, "w+")

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg, dbg_mode = verbosity)
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    mtp_mgmt_ctrl.mtp_apc_pwr_on()
    libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY))
    libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "Try to connect MTP chassis")
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        libmfg_utils.cli_log_err(test_log_filep, mtp_cli_id_str + "Unable to connect MTP chassis")
        return
    libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "MTP chassis connected")

    # get the sw version info
    sw_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
    libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "MTP SW version: {:s}".format(sw_ver))

    # PSU/FAN absent, powerdown MTP
    ret = mtp_mgmt_ctrl.mtp_hw_init(True)
    if not ret:
        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY))
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "Power off APC")
        mtp_mgmt_ctrl.mtp_apc_pwr_off()
        return

    # power on all the nic.
    mtp_mgmt_ctrl.mtp_power_on_nic()
    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_prsnt_nic_list()

    nic_fw_cfg = libmfg_utils.load_cfg_from_yaml(nic_firmware_cfg_file)
    naples100_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["CPLD_FILE"]
    naples100_vrm_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["VRM_FILE"]
    naples100_vrm_img_cksum = nic_fw_cfg[NIC_Type.NAPLES100]["VRM_CKSUM"]
    naples25_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["CPLD_FILE"]
    naples25_vrm_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["VRM_FILE"]
    naples25_vrm_img_cksum = nic_fw_cfg[NIC_Type.NAPLES25]["VRM_CKSUM"]

    libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "Start the Barcode Scan Process")
    while True:
        scan_rslt = mtp_mgmt_ctrl.mtp_barcode_scan()
        if scan_rslt:
            break;
        libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "Restart the Barcode Scan Process")

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
    libmfg_utils.cli_log_rslt("Barcode Scan Summary", pass_rslt_list, fail_rslt_list, test_log_filep)

    gen_barcode_config_file(pro_srv_id, scan_cfg_filep, scan_rslt)
    scan_cfg_filep.close()
    os.system("sync")

    # reload the barcode config file
    nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(scan_cfg_file)
    libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "Use the barcode configuration file generated on {:s}\n".format(nic_fru_cfg[mtp_id]["TS"]))
    libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "FRU Program Matrix:")

    err_inj_slot_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        nic_cli_id_str = libmfg_utils.id_str(mtp = mtp_id, nic = slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]
        if str.upper(valid) == "YES":
            sn = nic_fru_cfg[mtp_id][key]["SN"]
            mac = nic_fru_cfg[mtp_id][key]["MAC"]
            mac_ui = libmfg_utils.mac_address_format(mac)
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES100:
                cpld_img_file = naples100_cpld_img_file
                vrm_img_file = naples100_vrm_img_file
                vrm_img_cksum = naples100_vrm_img_cksum
            elif card_type == NIC_Type.NAPLES25:
                cpld_img_file = naples25_cpld_img_file
                vrm_img_file = naples25_vrm_img_file
                vrm_img_cksum = naples25_vrm_img_cksum
            else:
                libmfg_utils.sys_exit("Unknown NIC type detected: {:s}".format(card_type))

            libmfg_utils.cli_log_inf(test_log_filep, nic_cli_id_str + "SN = " + sn + "; MAC = " + mac_ui)
            libmfg_utils.cli_log_inf(test_log_filep, nic_cli_id_str + "CPLD image: " + os.path.basename(cpld_img_file))
            libmfg_utils.cli_log_inf(test_log_filep, nic_cli_id_str + "VRM image: " + os.path.basename(vrm_img_file) + "\n")
            err_inj_slot_list.append(slot)

    if len(err_inj_slot_list) == 0:
        libmfg_utils.cli_log_err(test_log_filep, mtp_cli_id_str + "No NIC present, firmware update is not required")
        test_log_filep.close()
        diag_log_filep.close()
        return

    # start the programming
    libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "NIC firmware update process started\n")

    if err_inj:
        err_inj_slot = random.choice(err_inj_slot_list)
    else:
        err_inj_slot = MTP_Const.MTP_SLOT_INVALID

    fail_nic_list = list()
    pass_nic_list = list()
    naples100_sn_list = list()
    naples25_sn_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        nic_cli_id_str = libmfg_utils.id_str(mtp = mtp_id, nic = slot)
        valid = nic_fru_cfg[mtp_id][key]["VALID"]

        if err_inj_slot == slot:
            slot_err_inj = True
        else:
            slot_err_inj = False

        if str.upper(valid) == "YES":
            sn = nic_fru_cfg[mtp_id][key]["SN"]
            mac = nic_fru_cfg[mtp_id][key]["MAC"]
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES100:
                cpld_img_file = naples100_cpld_img_file
                vrm_img_file = naples100_vrm_img_file
                vrm_img_cksum = naples100_vrm_img_cksum
                naples100_sn_list.append(sn)
            elif card_type == NIC_Type.NAPLES25:
                cpld_img_file = naples25_cpld_img_file
                vrm_img_file = naples25_vrm_img_file
                vrm_img_cksum = naples25_vrm_img_cksum
                naples25_sn_list.append(sn)
            else:
                libmfg_utils.sys_exit("Unknown NIC type detected: {:s}".format(card_type))

            if not mtp_mgmt_ctrl.mtp_nic_fw_update(slot, sn, mac, cpld_img_file, vrm_img_file, vrm_img_cksum, slot_err_inj):
                fail_nic_list.append(key)
            else:
                pass_nic_list.append(key)
        else:
            libmfg_utils.cli_log_inf(test_log_filep, nic_cli_id_str + "    -- Bypass empty slot\n")

    mtp_mgmt_ctrl.mtp_mgmt_poweroff()
    libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "Power off OS, Wait {:d} seconds to power off APC\n".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY))
    libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
    libmfg_utils.cli_log_inf(test_log_filep, mtp_cli_id_str + "Power off APC")
    mtp_mgmt_ctrl.mtp_apc_pwr_off()

    # print summary
    pass_rslt_list = list()
    fail_rslt_list = list()
    if len(fail_nic_list) > 0:
        fail_rslt_list.append(mtp_cli_id_str + ", ".join(fail_nic_list) + " Firmware Program Failed")
    if len(pass_nic_list) > 0:
        pass_rslt_list.append(mtp_cli_id_str + ", ".join(pass_nic_list) + " Firmware Program Passed")
    libmfg_utils.cli_log_rslt("NIC Fimrware Update Summary", pass_rslt_list, fail_rslt_list, test_log_filep)

    test_log_filep.close()
    diag_log_filep.close()
    os.system("sync")

    # move the logs to the log root dir
    if len(naples100_sn_list) > 0:
        dl_log_path = pro_srv_cfg_db.get_pro_srv_dl_logpath(pro_srv_id, NIC_Type.NAPLES100)
        for sn in naples100_sn_list:
            logdir = dl_log_path + sn + "/"
            os.system("mkdir -p " + logdir)
            logfile = sn + "_" + test_log_file
            os.system("cp " + test_log_file + " " + logdir + logfile)
            logfile = sn + "_" + diag_log_file
            os.system("cp " + diag_log_file + " " + logdir + logfile)

        barcode_cfg_path = pro_srv_cfg_db.get_pro_srv_barcode_cfgpath(pro_srv_id, NIC_Type.NAPLES100)
        for sn in naples100_sn_list:
            logdir = barcode_cfg_path + sn + "/"
            os.system("mkdir -p " + logdir)
            logfile = sn + "_" + scan_cfg_file
            os.system("cp " + scan_cfg_file + " " + logdir + logfile)

    if len(naples25_sn_list) > 0:
        dl_log_path = pro_srv_cfg_db.get_pro_srv_dl_logpath(pro_srv_id, NIC_Type.NAPLES25)
        for sn in naples25_sn_list:
            logdir = dl_log_path + sn + "/"
            os.system("mkdir -p " + logdir)
            logfile = sn + "_" + test_log_file
            os.system("cp " + test_log_file + " " + logdir + logfile)
            logfile = sn + "_" + diag_log_file
            os.system("cp " + diag_log_file + " " + logdir + logfile)

        barcode_cfg_path = pro_srv_cfg_db.get_pro_srv_barcode_cfgpath(pro_srv_id, NIC_Type.NAPLES25)
        for sn in naples25_sn_list:
            logdir = barcode_cfg_path + sn + "/"
            os.system("mkdir -p " + logdir)
            logfile = sn + "_" + scan_cfg_file
            os.system("cp " + scan_cfg_file + " " + logdir + logfile)

    # remove the local log files
    os.system("rm -f " + scan_cfg_file + " " + test_log_file + " " + diag_log_file)

    return

if __name__ == "__main__":
    main()
