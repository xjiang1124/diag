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
from libdefs import MTP_DIAG_Logfile
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libpro_srv_db import pro_srv_db


def main():
    parser = argparse.ArgumentParser(description="Diag QA login onto NIC utility", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtp", help="MTP ID")
    parser.add_argument("--apc", help="MTP is power down, need to power on apc first", action='store_true')
    parser.add_argument("--slot", help="slot number to be connected", type=int, required=True)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')

    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    else:
        verbosity = False

    if args.apc:
        apc = True
    else:
        apc = False

    if args.mtp:
        mtp_id = args.mtp
    else:
        mtp_id = None

    if verbosity:
        diag_log_filep = sys.stdout
    else:
        diag_log_filep = None

    slot = args.slot - 1
    
    # get the absolute file path
    product_server_cfg_file = os.path.abspath("../config/pensando_pro_srv1_cfg.yaml")
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
    mtp_chassis_cfg_file = os.path.abspath("../config/" + filename)
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)

    if not mtp_id:
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

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, None, diag_log_filep, mgmt_cfg = mtp_mgmt_cfg, apc_cfg = mtp_apc_cfg)
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    if apc:
        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        libmfg_utils.cli_inf(mtp_cli_id_str + "Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY))
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP chassis", level=0)
        return
    mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected\n", level=0)

    # get the sw version info
    sw_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
    mtp_mgmt_ctrl.cli_log_inf("MTP SW version: {:s}".format(sw_ver), level=0)

    # diag environment pre init
    mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null")

    # power cycle the nic.
    mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
    time.sleep(MTP_Const.NIC_POWER_OFF_DELAY)
    mtp_mgmt_ctrl.mtp_power_on_single_nic(slot)

    # init nic.
    mtp_mgmt_ctrl.mtp_nic_diag_init(slot)

    # user ctrl
    mtp_mgmt_ctrl.mtp_enter_user_ctrl()

    return

if __name__ == "__main__":
    main()

