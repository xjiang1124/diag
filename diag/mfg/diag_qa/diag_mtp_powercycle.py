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
    parser = argparse.ArgumentParser(description="Diag MTP Power Cycle", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtp", help="MTP ID")

    libmfg_utils.cli_inf("!!! Only use this command when mtp can not connected, console is stuck!!!")
    libmfg_utils.double_confirm("to continue")

    mtp_id = None

    args = parser.parse_args()
    if args.mtp:
        mtp_id = args.mtp

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

    mtp_mgmt_ctrl.mtp_apc_pwr_off()
    time.sleep(1)
    mtp_mgmt_ctrl.mtp_apc_pwr_on()
    libmfg_utils.cli_inf(mtp_cli_id_str + "Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY))
    libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)

    libmfg_utils.cli_inf(mtp_cli_id_str + "Try to connect MTP chassis")
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to connect MTP chassis")
    libmfg_utils.cli_inf(mtp_cli_id_str + "MTP chassis connected")

    mtp_mgmt_ctrl.mtp_enter_user_ctrl()

if __name__ == "__main__":
    main()
