#!/usr/bin/env python

import sys
import os
import time
import pexpect
import re
import argparse
import threading
import traceback

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
import test_utils
import testlog
from libdefs import Swm_Test_Mode
from libdefs import FF_Stage
from libdefs import MTP_Const
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE

def load_mtp_cfg():
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db

def mtp_test_cleanup(error_code, fp_list=None):
    if fp_list:
        for fp in fp_list:
            fp.close()
    os.system("sync")


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg)
    return mtp_mgmt_ctrl

def mtp_setup(mtp_mgmt_ctrl, setup_rslt_list):
    setup_rslt_list[mtp_mgmt_ctrl._id] = libmfg_utils.mtp_common_setup2(mtp_mgmt_ctrl, FF_Stage.FF_P2C)

def sanity_check(mtp_cfg_db, mtpid_list, mtp_mgmt_ctrl_list, mtpid_fail_list):
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        
        # find any slots to skip
        mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
        mtp_mgmt_ctrl._slots_to_skip = mtp_slots_to_skip

        # find the mtp capability
        mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    libmfg_utils.cli_log_rslt("Begin Sanity Check .. Please monitor until complete", [], [], mtp_mgmt_ctrl._filep)

    mtp_thread_list = list()
    setup_rslt_list = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mtp_thread = threading.Thread(target = mtp_setup, args = (mtp_mgmt_ctrl, setup_rslt_list))
        mtp_thread.daemon = True
        mtp_thread.start()
        mtp_thread_list.append(mtp_thread)
        time.sleep(2)

    #monitor all the thread
    while True:
        if len(mtp_thread_list) == 0:
            break
        for mtp_thread in mtp_thread_list[:]:
            if not mtp_thread.is_alive():
                mtp_thread.join()
                mtp_thread_list.remove(mtp_thread)
        time.sleep(5)

    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        if not setup_rslt_list[mtp_id]:
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)

    #fail_nic_list = libmfg_utils.loopback_sanity_check(mtpid_list, mtp_mgmt_ctrl_list)

    # if all slots in an MTP fail, assert stop on failure here
    # for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
    #     if len(fail_nic_list[mtp_id]) == mtp_mgmt_ctrl._slots:
    #         mtp_mgmt_ctrl.mtp_diag_fail_report("MTP completely failed Sanity Check. Test abort..")
    #         mtpid_list.remove(mtp_id)
    #         mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
    #         mtpid_fail_list.append(mtp_id)

    # close NIC ssh sessions
    # for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
    #     mtp_mgmt_ctrl.mtp_nic_para_session_end()

    return None

def single_mtp_p2c_test(mtp_script_dir, mtp_mgmt_ctrl, mtp_id, fail_nic_list, mtp_test_summary, swm_test_mode, skip_test=[]):
    if skip_test:
        skipped_testlist = " --skip-test {:s}".format('"'+'" "'.join(skip_test).strip()+'"')
    else:
        skipped_testlist = ""
    if fail_nic_list:
        fail_slots = " --fail-slots "
        fail_slots += ' '.join(map(str,fail_nic_list))
    else:
        fail_slots = ""

    # go to mtp_regression and start the test
    cmd = "cd {:s}".format(mtp_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MFG P2C Test Start", level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
    cmd = "./mtp_diag_regression.py --mtpid {:s} --swm {:s}".format(mtp_id, swm_test_mode)
    if skip_test:
        cmd += skipped_testlist
    if fail_slots:
        cmd += fail_slots
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_P2C_TEST_TIMEOUT)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("MFG P2C Test Complete", level=0)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    if not save_logs(mtp_mgmt_ctrl, stage, mtp_test_summary, mtp_start_ts, mtp_stop_ts, None, False, True):
        return

    return


def main():
    parser = argparse.ArgumentParser(description="MFG FAN Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser.add_argument("--loop", "-loop", help="Step up loop time")

    verbosity = False
    swmtestmode = Swm_Test_Mode.SW_DETECT
    args = parser.parse_args()
    #print(args)
    
    if args.verbosity:
        verbosity = True
    if args.swm:
        swmtestmode = args.swm

    running_loop = 5
    if args.loop:
        running_loop = int(args.loop)
        
    print("MFG FAN Test SET LOOPS: {}".format(running_loop))

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
    mtpid_fail_list = list()
    mtp_mgmt_ctrl_list = list()
    fail_nic_list = dict()

    # init mtp_ctrl list
    for mtp_id in mtpid_list:
        if verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list)
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)
        fail_nic_list[mtp_id] = list()

    # logfiles
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=FF_Stage.FF_P2C)

    mfg_p2c_start_ts = libmfg_utils.timestamp_snapshot()

    
    for x in range(running_loop):
        mfg_p2c_start_ts2 = libmfg_utils.timestamp_snapshot()
        # power off the mtp chassis
        libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list, safely=False)

        # power on the mtp chassis
        libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

        # Connect to MTP
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            if not test_utils.mtp_common_setup_fpo(mtp_mgmt_ctrl, FF_Stage.FF_P2C, args.skip_test):
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
                continue

        # Sanity check
        try:
            fail_nic_list = sanity_check(mtp_cfg_db, mtpid_list, mtp_mgmt_ctrl_list, mtpid_fail_list)
        except Exception as e:
            err_msg = traceback.format_exc()
            for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
                mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)
            sys.exit()

        #print(mtpid_fail_list)

        # close file handles
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            mtp_test_cleanup(mtp_mgmt_ctrl)

        # # Copy script, config file on to each MTP Chassis
        # mtp_p2c_script_dir = "mtp_regression/"
        # for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        #     mtp_p2c_script_pkg = "mtp_regression.{:s}.tar".format(mtp_id)
        #     mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP P2C Test script", level=0)
        #     if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_p2c_script_dir, mtp_p2c_script_pkg, logfile_dir_list[mtp_id]):
        #         mtp_mgmt_ctrl.cli_log_err("Deploy MTP P2C Test script failed", level=0)
        #         mtpid_list.remove(mtp_id)
        #         mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
        #         mtpid_fail_list.append(mtp_id)
        #     else:
        #         mtp_mgmt_ctrl.cli_log_inf("Deploy MTP P2C Test script complete", level=0)

        # mtp_thread_list = list()
        # mfg_p2c_summary = dict()
        # for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        #     mfg_p2c_summary[mtp_id] = list()
        #     mtp_thread = threading.Thread(target = single_mtp_p2c_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_p2c_script_dir,
        #                                                                         mtp_mgmt_ctrl,
        #                                                                         mtp_id,
        #                                                                         fail_nic_list[mtp_id],
        #                                                                         mfg_p2c_summary[mtp_id],
        #                                                                         swmtestmode,
        #                                                                         args.skip_test))
        #     mtp_thread.daemon = True
        #     mtp_thread.start()
        #     mtp_thread_list.append(mtp_thread)
        #     time.sleep(2)

        # # monitor all the thread
        # while True:
        #     if len(mtp_thread_list) == 0:
        #         break
        #     for mtp_thread in mtp_thread_list[:]:
        #         if not mtp_thread.is_alive():
        #             mtp_thread.join()
        #             mtp_thread_list.remove(mtp_thread)
        #     time.sleep(5)
        mfg_p2c_stop_ts2 = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("LOOP: {} MFG FAN Test Duration:{:s}".format(x+1, mfg_p2c_stop_ts2 - mfg_p2c_start_ts2))

        # power off all the test mtp
        libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

        # dump the summary
        #libmfg_utils.mfg_summary_disp(FF_Stage.FF_P2C, mfg_p2c_summary, mtpid_fail_list)
    mfg_p2c_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("Complete {} Loop in MFG FAN Test Duration:{:s}".format(running_loop, mfg_p2c_stop_ts - mfg_p2c_start_ts))

if __name__ == "__main__":
    main()
