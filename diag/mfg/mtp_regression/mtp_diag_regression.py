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
from libdefs import MTP_DIAG_Report
from libdiag_db import diag_db
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl


# test cleanup.
def mtp_test_cleanup(error_code, fp_list=None):
    if fp_list:
        for fp in fp_list:
            fp.close()
    os.system("sync")


def naples_diag_cfg_show(card_type, naples_test_db, mtp_mgmt_ctrl):
    mtp_mgmt_ctrl.cli_log_inf("{:s} Diag Regression Test List:".format(card_type), level = 0)
    cmd_list = naples_test_db.get_init_cmd_list()
    mtp_mgmt_ctrl.cli_log_inf("Init Command List:")
    for item in cmd_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)
 
    skip_list = naples_test_db.get_skip_test_list()
    mtp_mgmt_ctrl.cli_log_inf("Skip Test List:")
    for item in skip_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)
 
    param_list = naples_test_db.get_test_param_list()
    mtp_mgmt_ctrl.cli_log_inf("Parameter List:")
    for item in param_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)
 
    seq_test_list = naples_test_db.get_diag_seq_test_list()
    mtp_mgmt_ctrl.cli_log_inf("Sequential Test List:")
    for item in seq_test_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)
 
    para_test_list = naples_test_db.get_diag_para_test_list()
    mtp_mgmt_ctrl.cli_log_inf("Parallel Test List:")
    for item in para_test_list:
        mtp_mgmt_ctrl.cli_log_inf("{:s}".format(item), level = 2)

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
    parser.add_argument("--psu-check", help="force to check the psu", action='store_true')
    parser.add_argument("--stop-on-error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--skip-test", help="Test will not run, debug purpose", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true')

    args = parser.parse_args()

    mtp_id = "MTP-000"
    vmarg = 0
    fanspd = 40
    psu_check = False
    iteration = 1
    stop_on_err = False
    verbosity = False
    skip_test = False
    skip_nic_list = list()

    if args.mtpid:
        mtp_id = args.mtpid
        mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
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
    if args.skip_test:
        skip_test = True
    if args.verbosity:
        verbosity = True

    if args.skip_nic:
        tmp_str = args.skip_nic.replace(' ','')
        skip_list = tmp_str.split(',')
        for slot in skip_list:
            try:
                val = int(slot)
                if val > MTP_Const.MTP_SLOT_NUM or val <= 0: 
                    libmfg_utils.sys_exit(mtp_cli_id_str + "Invalid slot number")
                skip_nic_list.append(libmfg_utils.nic_key(slot, base=0))
            except ValueError:
                libmfg_utils.sys_exit(mtp_cli_id_str + "Invalid nic parameter")

    # load the mtp config
    mtp_chassis_cfg_file = "config/pensando_pro_srv1_mtp_chassis_cfg.yaml"
    mtp_cfg_db = mtp_db(mtp_cfg_file = mtp_chassis_cfg_file)

    # find the mtp management config based on the mtpid
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return

    # find the apc config based on the mtpid
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")

    open_file_track_list = list()
        
    mtp_script_dir = os.getcwd()
    mtp_test_log_file = mtp_script_dir + "/mtp_test.log"
    mtp_diag_log_file = mtp_script_dir + "/mtp_diag.log"
    mtp_diag_cmd_log_file = mtp_script_dir + "/mtp_diag_cmd.log"
    mtp_diagmgr_log_file = mtp_script_dir + "/mtp_diagmgr.log"
    mtp_test_log_filep = open(mtp_test_log_file, "w+", buffering=0)
    open_file_track_list.append(mtp_test_log_filep)
    mtp_diag_log_filep = open(mtp_diag_log_file, "w+", buffering=0)
    open_file_track_list.append(mtp_diag_log_filep)
    mtp_diag_cmd_log_filep = open(mtp_diag_cmd_log_file, "w+", buffering=0)
    open_file_track_list.append(mtp_diag_cmd_log_filep)
    mtp_diagmgr_log_filep = open(mtp_diagmgr_log_file, "w+", buffering=0)

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id,
                             mtp_test_log_filep,
                             mtp_diag_log_filep,
                             diag_cmd_log_filep = mtp_diag_cmd_log_filep,
                             mgmt_cfg = mtp_mgmt_cfg,
                             apc_cfg = mtp_apc_cfg,
                             dbg_mode = verbosity)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.mtp_diag_fail_report("Unable to connect MTP Chassis")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
        return

    mtp_mgmt_ctrl.mtp_diag_pre_init(mtp_diagmgr_log_file)

    # get the sw version info
    sw_ver = mtp_mgmt_ctrl.mtp_get_sw_version()
    mtp_mgmt_ctrl.cli_log_inf("MTP SW version: {:s}".format(sw_ver), level=0)

    # get the sw version info
    asic_ver = mtp_mgmt_ctrl.mtp_get_asic_version()
    mtp_mgmt_ctrl.cli_log_inf("MTP ASIC version: {:s}".format(asic_ver), level=0)

    # PSU/FAN absent, powerdown MTP
    ret = mtp_mgmt_ctrl.mtp_hw_init(psu_check)
    if not ret:
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP Sanity Check Failed")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_HW_SANITY, open_file_track_list)
        return

    # load the diag test config
    naples100_test_cfg_file = "config/naples100_mtp_test_cfg.yaml" 
    #naples25_test_cfg_file = "config/naples25_mtp_test_cfg.yaml" 
    naples100_test_db = diag_db(naples100_test_cfg_file)
    #naples25_test_db = diag_db(naples25_test_cfg_file)

    if not mtp_mgmt_ctrl.mtp_nic_init(fru_load = True):
        mtp_mgmt_ctrl.mtp_diag_fail_report("Diag Initialize NIC Fail")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
        return

    if not mtp_mgmt_ctrl.mtp_diag_init(naples100_test_db):
        mtp_mgmt_ctrl.mtp_diag_fail_report("Diag Environment Setup Fail")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
        return

    naples100_nic_list = list()
    #naples25_nic_list = list()
    pass_nic_list = list()
    pass_sn_list = list()
    fail_nic_list = list()
    fail_sn_list = list()
    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(len(nic_prsnt_list)):
        key = libmfg_utils.nic_key(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        if nic_prsnt_list[slot] and key not in skip_nic_list:
            if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES100:
                naples100_nic_list.append(slot)
                pass_nic_list.append(key)
                pass_sn_list.append(sn)
            #else:
            #    naples25_nic_list.append(slot)

    mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test List:", level=0)
    if naples100_nic_list:
        naples_diag_cfg_show(NIC_Type.NAPLES100, naples100_test_db, mtp_mgmt_ctrl)
        naples_exec_init_cmd(naples100_test_db, mtp_mgmt_ctrl)
        naples_exec_skip_cmd(naples100_nic_list, naples100_test_db, mtp_mgmt_ctrl)
        naples_exec_param_cmd(naples100_nic_list, naples100_test_db, mtp_mgmt_ctrl)
    #if naples25_nic_list:
    #    naples_diag_cfg_show(NIC_Type.NAPLES25, mtp_test_log_filep, mtp_id, naples25_test_db)
    mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test List End\n", level=0)

    mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment:", level=0)
    mtp_mgmt_ctrl.cli_log_inf("Iteration = {:3d}".format(iteration))
    mtp_mgmt_ctrl.cli_log_inf("Fan Speed = {:3d}%".format(fanspd))
    mtp_mgmt_ctrl.cli_log_inf("Voltage Margin = {:d}%".format(vmarg))
    mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment End\n", level=0)

    # Fan speed, voltage margin setup
    mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment Setup", level=0)
    if not mtp_mgmt_ctrl.mtp_diag_env_init(fanspd, vmarg):
        mtp_mgmt_ctrl.mtp_diag_fail_report("Diag Regression Test Environment Setup Failed")
        mtp_test_cleanup(MTP_DIAG_Error.MTP_ENV_SETUP, open_file_track_list)
        return
    else:
        mtp_mgmt_ctrl.cli_log_inf("Diag Regression Test Environment Setup Complete\n", level=0)

    # get the inlet temperature info
    env_temp = mtp_mgmt_ctrl.mtp_get_inlet_temp()
    mtp_mgmt_ctrl.cli_log_inf("MTP Inlet Temperature: {:.2f}".format(env_temp), level=0)

    if skip_test:
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s}".format(nic_key, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
        for nic_key in pass_nic_list:
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s}".format(nic_key, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

        for fp in open_file_track_list:
            fp.close()
        return

    # run the naples100 MTP_SEQ diag test
    naples100_seq_test_list = naples100_test_db.get_diag_seq_test_list()

    mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Test Start", level=0)
    for loop in range(iteration):
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Iteration - {:03d} Start".format(loop))
        for dsp, test in naples100_seq_test_list:
            test_cfg = naples100_test_db.get_diag_seq_test(dsp, test)
            init_cmd = None
            post_cmd = None
            if test_cfg["INIT"] != "":
                init_cmd = test_cfg["INIT"]
            if test_cfg["POST"] != "":
                post_cmd = test_cfg["POST"]
            for slot in naples100_nic_list[:]: 
                opts = test_cfg["OPTS"]
                sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
                diag_cmd = naples100_test_db.get_diag_seq_test_run_cmd(dsp, test, slot, opts, sn)
                rslt_cmd = naples100_test_db.get_diag_seq_test_errcode_cmd(dsp, slot, opts)
                nic_key = libmfg_utils.nic_key(slot)
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))

                start_ts = datetime.datetime.now().replace(microsecond=0)
                ret = mtp_mgmt_ctrl.mtp_run_diag_test_seq(slot, diag_cmd, rslt_cmd, test, init_cmd, post_cmd)
                stop_ts = datetime.datetime.now().replace(microsecond=0)
                duration = str(stop_ts - start_ts)

                if ret == "SUCCESS":
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                elif ret == MTP_DIAG_Error.NIC_DIAG_TIMEOUT:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_TIMEOUT.format(sn, dsp, test, duration))
                    if stop_on_err:
                        naples100_nic_list.remove(slot)
                    if nic_key not in fail_nic_list: 
                        fail_nic_list.append(nic_key)
                        fail_sn_list.append(sn)
                    if nic_key in pass_nic_list:
                        pass_nic_list.remove(nic_key)
                        pass_sn_list.remove(sn)
                else:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, ret, duration))
                    if stop_on_err:
                        naples100_nic_list.remove(slot)
                    if nic_key not in fail_nic_list: 
                        fail_nic_list.append(nic_key)
                        fail_sn_list.append(sn)
                    if nic_key in pass_nic_list:
                        pass_nic_list.remove(nic_key)
                        pass_sn_list.remove(sn)

        mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Iteration - {:03d} Complete".format(loop))
    mtp_mgmt_ctrl.cli_log_inf("MTP Diag Regression Test Complete\n", level=0)

    # log the diag test history
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("./diag -shist")
    # clear the diag test history
    if not stop_on_err:
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("./diag -chist")

    for nic_key, nic_sn in zip(fail_nic_list, fail_sn_list):
        mtp_mgmt_ctrl.cli_log_err("{:s} {:s} {:s}".format(nic_key, nic_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    for nic_key, nic_sn in zip(pass_nic_list, pass_sn_list):
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s}".format(nic_key, nic_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

    for fp in open_file_track_list:
        fp.close()

    os.system("sync")


if __name__ == "__main__":
    main()
