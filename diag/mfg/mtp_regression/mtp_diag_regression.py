#!/usr/bin/env python

import sys
import os
import time
import pexpect
import re
import argparse
import random
import datetime 

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import MTP_Const
from libdefs import NIC_Type
from libdefs import MTP_DIAG_Error
from libdiag_db import diag_db
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl


# report pre defined error code 
def mtp_error_report(error_code):
    if error_code != MTP_DIAG_Error.MTP_DIAG_PASS:
        libmfg_utils.cli_err(error_code)
    else:
        libmfg_utils.cli_inf(error_code)


# test cleanup.
def mtp_test_cleanup(error_code, fp_list=None):
    if fp_list:
        for fp in fp_list:
            fp.close()
        os.system("sync")

    mtp_error_report(error_code)


def naples_diag_cfg_show(card_type, naples_test_db, mtp_mgmt_ctrl):
    mtp_mgmt_ctrl.cli_log_inf("{:s} Diag Regression Test List:".format(card_type), level = 0)
    cmd_list = naples_test_db.get_init_cmd_list()
    mtp_mgmt_ctrl.cli_log_inf("-- Init Command List:")
    for item in cmd_list:
        mtp_mgmt_ctrl.cli_log_inf("-- {:s}".format(item), level = 2)
 
    skip_list = naples_test_db.get_skip_test_list()
    mtp_mgmt_ctrl.cli_log_inf("-- Skip Test List:")
    for item in skip_list:
        mtp_mgmt_ctrl.cli_log_inf("-- {:s}".format(item), level = 2)
 
    param_list = naples_test_db.get_test_param_list()
    mtp_mgmt_ctrl.cli_log_inf("-- Parameter List:")
    for item in param_list:
        mtp_mgmt_ctrl.cli_log_inf("-- {:s}".format(item), level = 2)
 
    seq_test_list = naples_test_db.get_diag_seq_test_list()
    mtp_mgmt_ctrl.cli_log_inf("-- Sequential Test List:")
    for item in seq_test_list:
        mtp_mgmt_ctrl.cli_log_inf("-- {:s}".format(item), level = 2)
 
    para_test_list = naples_test_db.get_diag_para_test_list()
    mtp_mgmt_ctrl.cli_log_inf("-- Parallel Test List:")
    for item in para_test_list:
        mtp_mgmt_ctrl.cli_log_inf("-- {:s}".format(item), level = 2)

    return


def naples_exec_init_cmd(naples_test_db, mtp_mgmt_ctrl):
    cmd_list = naples_test_db.get_init_cmd_list()
    mtp_mgmt_ctrl.cli_log_inf("Execute Command in Init Command List:", level = 0)
    for cmd in cmd_list:
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
 
    return


def naples_exec_skip_cmd(nic_list, naples_test_db, mtp_mgmt_ctrl):
    cmd_list = naples_test_db.get_skip_test_cmd_list(nic_list)
    mtp_mgmt_ctrl.cli_log_inf("Execute Command in Skip Command List:", level = 0)
    for cmd in cmd_list:
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
 
    return


def naples_exec_param_cmd(nic_list, naples_test_db, mtp_mgmt_ctrl):
    cmd_list = naples_test_db.get_test_param_cmd_list(nic_list)
    mtp_mgmt_ctrl.cli_log_inf("Execute Command in Parameter set List:", level = 0)
    for cmd in cmd_list:
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
 
    return


def main():
    parser = argparse.ArgumentParser(description="Single MTP Diagnostics P2C Regression Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--fanspd", help="Fan speed parameter", type=int)
    parser.add_argument("--vmarg", help="Voltage margin", type=int)
    parser.add_argument("--iteration", help="Iteration to run", type=int)
    parser.add_argument("--skip-nic", help="skip the nic, nic number is 1 based and seperate by comma")
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--fru-load", help="Load the SN from Fru, instead of config file", action='store_true')
    parser.add_argument("--psu-check", help="force to check the psu", action='store_true')
    parser.add_argument("--stop-on-error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')

    args = parser.parse_args()

    fru_load = False
    mtp_id = "MTP-000"
    vmarg = 0
    fanspd = 40
    psu_check = False
    iteration = 1
    stop_on_err = False
    verbosity = False
    skip_nic_list = list()

    if args.fru_load:
        fru_load = True
    if args.mtpid:
        mtp_id = args.mtpid
    if args.vmarg:
        vmarg = args.vmarg
    if args.fanspd:
        fanspd = args.fanspd
    if args.psu_check:
        psu_check = True
    if args.iteration:
        iteration = args.iteration
    if args.stop_on_error:
        stop_on_err = True
    if args.verbosity:
        verbosity = True

    if args.skip_nic:
        tmp_str = args.skip_nic.replace(' ','')
        skip_list = tmp_str.split(',')
        for slot in skip_list:
            try:
                val = int(slot)
                if val > MTP_Const.MTP_SLOT_NUM or val <= 0: 
                    mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM)
                    libmfg_utils.sys_exit("Invalid slot number")
                skip_nic_list.append(libmfg_utils.nic_key(slot, base=0))
            except ValueError:
                mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM)
                libmfg_utils.sys_exit("Invalid nic parameter")

    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)

    # load the mtp config
    mtp_chassis_cfg_file = "config/pensando_pro_srv1_mtp_chassis_cfg.yaml"
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)

    # find the mtp management config based on the mtpid
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM)
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return

    # find the apc config based on the mtpid
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM)
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")

    open_file_track_list = list()
        
    mtp_test_log_file = "mtp_test.log"
    mtp_diag_log_file = "mtp_diag.log"
    mtp_diagmgr_log_file = "mtp_diagmgr.log"
    mtp_test_log_filep = open(mtp_test_log_file, "w+")
    open_file_track_list.append(mtp_test_log_filep)
    mtp_diag_log_filep = open(mtp_diag_log_file, "w+")
    open_file_track_list.append(mtp_diag_log_filep)
    mtp_diagmgr_log_filep = open(mtp_diagmgr_log_file, "w+")
    open_file_track_list.append(mtp_diagmgr_log_filep)

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id,
                             mtp_test_log_filep,
                             mtp_diag_log_filep,
                             mgmt_cfg = mtp_mgmt_cfg,
                             apc_cfg = mtp_apc_cfg,
                             dbg_mode = verbosity)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        libmfg_utils.cli_log_err(mtp_test_log_filep, mtp_cli_id_str + "Unable to connect MTP Chassis")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
        return

    mtp_mgmt_ctrl.mtp_diag_pre_init()

    # get the sw version info
    sw_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "MTP SW version: {:s}".format(sw_ver))

    # PSU/FAN absent, powerdown MTP
    ret = mtp_mgmt_ctrl.mtp_hw_init(psu_check)
    if not ret:
        libmfg_utils.cli_log_err(mtp_test_log_filep, mtp_cli_id_str + "MTP Sanity Check Failed")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_HW_SANITY, open_file_track_list)
        return

    # load the diag test config
    naples100_test_cfg_file = "config/naples100_mtp_test_cfg.yaml" 
    #naples25_test_cfg_file = "config/naples25_mtp_test_cfg.yaml" 
    naples100_test_db = diag_db(naples100_test_cfg_file)
    #naples25_test_db = diag_db(naples25_test_cfg_file)

    # get nic present, nic type, nic sn, etc
    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "MTP SW version: {:s}".format(sw_ver))
    mtp_mgmt_ctrl.mtp_nic_init(load_sn = fru_load, load_mac = fru_load)

    # if sn is not from fru,  from config file
    if not fru_load:
        nic_fru_cfg_file = "config/{:s}.yaml".format(mtp_id)
        nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(nic_fru_cfg_file)

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            key = libmfg_utils.nic_key(slot)
            nic_cli_id_str = libmfg_utils.id_str(mtp = mtp_id, nic = slot)
            valid = nic_fru_cfg[mtp_id][key]["VALID"]
            if str.upper(valid) == "YES":
                sn = nic_fru_cfg[mtp_id][key]["SN"]
                mac = nic_fru_cfg[mtp_id][key]["MAC"]
                mtp_mgmt_ctrl.mtp_set_nic_sn(slot, sn)
                mtp_mgmt_ctrl.mtp_set_nic_mac(slot, mac)
    # TODO, compare the nic present list and the config
    else:
        pass

    mtp_mgmt_ctrl.mtp_diag_init(mtp_diagmgr_log_filep)

    naples100_nic_list = list()
    #naples25_nic_list = list()
    pass_nic_list = list()
    fail_nic_list = list()
    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(len(nic_prsnt_list)):
        key = libmfg_utils.nic_key(slot)
        if nic_prsnt_list[slot] and key not in skip_nic_list:
            if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES100:
                naples100_nic_list.append(slot)
                pass_nic_list.append(key)
            #else:
            #    naples25_nic_list.append(slot)

    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "Diag Regression Test List:")
    if naples100_nic_list:
        naples_diag_cfg_show(NIC_Type.NAPLES100, naples100_test_db, mtp_mgmt_ctrl)
        naples_exec_init_cmd(naples100_test_db, mtp_mgmt_ctrl)
        naples_exec_skip_cmd(naples100_nic_list, naples100_test_db, mtp_mgmt_ctrl)
        naples_exec_param_cmd(naples100_nic_list, naples100_test_db, mtp_mgmt_ctrl)
    #if naples25_nic_list:
    #    naples_diag_cfg_show(NIC_Type.NAPLES25, mtp_test_log_filep, mtp_id, naples25_test_db)
    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "Diag Regression Test List End\n")

    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "Diag Regression Test Environment:")
    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "    Iteration = {:3d}".format(iteration))
    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "    Fan Speed = {:3d}%".format(fanspd))
    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "    Voltage Margin = {:d}%".format(vmarg))
    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "Diag Regression Test Environment End\n")

    # Fan speed, voltage margin setup
    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "Diag Regression Test Environment Setup")
    if not mtp_mgmt_ctrl.mtp_diag_env_init(fanspd, vmarg):
        libmfg_utils.cli_log_err(mtp_test_log_filep, mtp_cli_id_str + "Diag Regression Test Environment Setup Failed\n")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_ENV_SETUP, open_file_track_list)
        return
    else:
        libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "Diag Regression Test Environment Setup Complete\n")

    # run the naples100 MTP_SEQ diag test
    naples100_seq_test_list = naples100_test_db.get_diag_seq_test_list()
    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "MTP Diag Regression Test Start")
    for loop in range(iteration):
        libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "MTP Diag Regression Iteration - {:03d} Start\n".format(loop))
        for dsp, test in naples100_seq_test_list:
            test_cfg = naples100_test_db.get_diag_seq_test(dsp, test)
            init_cmd = None
            post_cmd = None
            if test_cfg["INIT"] != "":
                init_cmd = test_cfg["INIT"]
            if test_cfg["POST"] != "":
                post_cmd = test_cfg["POST"]
            for slot in naples100_nic_list: 
                opts = test_cfg["OPTS"]
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                diag_cmd = naples100_test_db.get_diag_seq_test_run_cmd(dsp, test, slot, opts, sn)
                rslt_cmd = naples100_test_db.get_diag_seq_test_errcode_cmd(dsp, slot, opts)
                clr_cmd = naples100_test_db.clear_diag_seq_test_errcode_cmd(dsp, slot, opts)
                nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=slot)
                nic_key = libmfg_utils.nic_key(slot)
                libmfg_utils.cli_log_inf(mtp_test_log_filep, nic_cli_id_str + "Diag Test {:s} Started".format(dsp))

                start_ts = datetime.datetime.now().replace(microsecond=0)
                ret = mtp_mgmt_ctrl.mtp_run_diag_test_seq(slot, diag_cmd, rslt_cmd, clr_cmd, test, init_cmd, post_cmd)
                stop_ts = datetime.datetime.now().replace(microsecond=0)

                if ret == MTP_DIAG_Error.MTP_DIAG_PASS:
                    libmfg_utils.cli_log_inf(mtp_test_log_filep, nic_cli_id_str + "Diag Test {:s} Passed".format(dsp))
                elif ret == MTP_DIAG_Error.NIC_DIAG_FAIL:
                    libmfg_utils.cli_log_err(mtp_test_log_filep, nic_cli_id_str + "Diag Test {:s} Failed".format(dsp))
                    mtp_error_report(MTP_DIAG_Error.NIC_DIAG_FAIL)
                    if stop_on_err:
                        naples100_nic_list.remove(slot)
                    if nic_key not in fail_nic_list: 
                        fail_nic_list.append(nic_key)
                    if nic_key in pass_nic_list:
                        pass_nic_list.remove(nic_key)
                else:
                    libmfg_utils.cli_log_err(mtp_test_log_filep, mtp_cli_id_str + "Diag Test {:s} Timeout".format(dsp))
                    mtp_error_report(MTP_DIAG_Error.NIC_DIAG_TIMEOUT)
                    if stop_on_err:
                        naples100_nic_list.remove(slot)
                    if nic_key not in fail_nic_list: 
                        fail_nic_list.append(nic_key)
                    if nic_key in pass_nic_list:
                        pass_nic_list.remove(nic_key)

                libmfg_utils.cli_log_inf(mtp_test_log_filep, nic_cli_id_str + "Diag Test {:s} Cost {:s}".format(dsp, stop_ts-start_ts))

        libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "MTP Diag Regression Iteration - {:03d} Complete\n".format(loop))
    libmfg_utils.cli_log_inf(mtp_test_log_filep, mtp_cli_id_str + "MTP Diag Regression Test Complete")

    diag_fail_rslt_list = list()
    diag_pass_rslt_list = list()
    if len(fail_nic_list) > 0:
        diag_fail_rslt_list.append(mtp_cli_id_str + ", ".join(fail_nic_list) + " Diag Regression Test Fail")

    if len(pass_nic_list) > 0:
        diag_pass_rslt_list.append(mtp_cli_id_str + ", ".join(pass_nic_list) + " Diag Regression Test Pass")

    libmfg_utils.cli_log_rslt("Diag Test Summary", diag_pass_rslt_list, diag_fail_rslt_list, mtp_test_log_filep)


if __name__ == "__main__":
    main()
