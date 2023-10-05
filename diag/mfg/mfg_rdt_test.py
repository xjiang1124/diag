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
from libdefs import NIC_Type
from libdefs import Swm_Test_Mode
from libdefs import FF_Stage
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libdefs import FLEX_TWO_WAY_COMM
from libmfg_cfg import *
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db
import test_utils


def load_mtp_cfg(cfg_yaml = None):
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/rdt_mtp_chassis_cfg.yaml"))
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath(cfg_yaml))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, skip_slots=[]):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    if len(skip_slots) > 0 and not mtp_cfg_db.set_mtp_slots_to_skip(mtp_id, skip_slots):
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to set skip slots")
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg, slots_to_skip=mtp_slots_to_skip)
    return mtp_mgmt_ctrl

def single_mtp_rdt_test(mtp_script_dir, mtp_mgmt_ctrl, mtp_id, fail_nic_list, mtp_test_summary, swm_test_mode, l1_sequence, skip_test=[], only_test=[], mtp_cfg_file = None):
    stage = FF_Stage.FF_RDT

    if skip_test:
        skipped_testlist = " --skip-test {:s}".format('"'+'" "'.join(skip_test).strip()+'"')
    else:
        skipped_testlist = ""
    if only_test:
        only_testlist = " --only-test {:s}".format('"'+'" "'.join(only_test).strip()+'"')
    else:
        only_testlist = ""
    if fail_nic_list:
        fail_slots = " --fail-slots "
        fail_slots += ' '.join(map(str,fail_nic_list))
    else:
        fail_slots = ""

    # go to mtp_regression and start the test
    cmd = "cd {:s}".format(mtp_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MFG RDT Test Start", level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
    cmd = "./mtp_diag_regression.py --mtpid {:s} --swm {:s} --stage {:s}".format(mtp_id, swm_test_mode, FF_Stage.FF_RDT)
    if skip_test:
        cmd += skipped_testlist
    if only_test:
        cmd += only_testlist
    if fail_slots:
        cmd += fail_slots
    if mtp_cfg_file:
        mtp_cfg_file_opt = " --mtpcfg " + mtp_cfg_file
        cmd += mtp_cfg_file_opt
    if l1_sequence:
        cmd += " --l1-seq "

    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_RDT_TEST_TIMEOUT)
    #mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("MFG RDT Test Complete", level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_script_dir, mtp_id, mtp_test_summary, stage)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("MTP Collect RDT Test result failed", level=0)
        return
    libmfg_utils.assign_nic_retest_flag(test_log_file, mtp_test_summary, stage)
    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, stage, mtp_test_summary)
    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)
    return


def main():
    parser = argparse.ArgumentParser(description="MFG ORT Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip-test", help="skip a particular test or test section", nargs="*", default=[])
    parser.add_argument("--only-test", help="run particular tests only", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", help="pre-select MTPs", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--skip-slots", "--skip-slot", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--l1-seq", help="asic L1 run under sequence mode", action='store_true')
    parser.add_argument("--iteration", help="Iteration to run with MTP power cycle", type=int, required=False, default=1)
    parser.add_argument("--jobd_logdir", "--logdir", help="Store final log to different path", default=None)

    result = False
    verbosity = False
    l1_sequence = False
    swmtestmode = Swm_Test_Mode.SW_DETECT
    iteration = 1
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    if args.swm:
        swmtestmode = args.swm
    if args.l1_seq:
        l1_sequence = True
    if args.iteration:
        iteration = args.iteration


    stage = FF_Stage.FF_RDT
    mtpcfg_file = None
    if args.mtpcfg:
        mtpcfg_file = os.path.relpath(args.mtpcfg)
        mtp_cfg_db = load_mtp_cfg(mtpcfg_file)
    else:
        mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)

    for loop in range(1, iteration+1):

        mtpid_fail_list = list()
        mtp_mgmt_ctrl_list = list()
        fail_nic_list = dict()
        nic_sn_list = dict()
        invalid_nic_list = dict()

        mtp_diag_image = os.getenv("DIAG_AMD64_IMAGE_PATH", default=MFG_IMAGE_FILES.MTP_AMD64_IMAGE)
        nic_diag_image = os.getenv("DIAG_ARM64_IMAGE_PATH", default=MFG_IMAGE_FILES.MTP_ARM64_IMAGE)
        # init mtp_ctrl list
        for mtp_id in mtpid_list:
            if verbosity:
                diag_log_filep = sys.stdout
                diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
            else:
                diag_log_filep = None
                diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
            mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)
            mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)
            fail_nic_list[mtp_id] = list()
            nic_sn_list[mtp_id] = list()
            invalid_nic_list[mtp_id] = list()

        # logfiles
        open_file_track_mtp_list = dict()
        logfile_dir_list = dict()
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id] = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)

        mfg_rdt_start_ts = libmfg_utils.timestamp_snapshot()

        libmfg_utils.cli_inf("#" * 320)
        mtp_mgmt_ctrl_list[0].cli_log_inf("RDT TEST ITERATION-{:06d} START".format(loop), level=0)

        if loop == 1:
            # power off all the test mtp
            libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list, safely=False)
        # power on the mtp chassis
        libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

        mtp_thread_list = list()
        mfg_rdt_summary = dict()
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
            mfg_rdt_summary[mtp_id] = list()
            mtp_thread = threading.Thread(target = test_utils.single_mtp_test,
                                          args = (
                                                    stage,
                                                    mtp_mgmt_ctrl,
                                                    mfg_rdt_summary[mtp_id],
                                                    logfile_dir_list[mtp_id],
                                                    open_file_track_mtp_list[mtp_id],
                                                    args.skip_test,
                                                    args.jobd_logdir,
                                                    args.skip_slots),
                                        kwargs = ({
                                                    "mtpcfg_file": mtpcfg_file,
                                                    "testsuite_name": stage,
                                                    "swm_test_mode": swmtestmode,
                                                    "only_test": args.only_test,
                                                    "l1_sequence": l1_sequence}))
            mtp_thread.daemon = True
            mtp_thread.start()
            mtp_thread_list.append(mtp_thread)
            time.sleep(2)

        # monitor all the thread
        while True:
            if len(mtp_thread_list) == 0:
                break
            for mtp_thread in mtp_thread_list[:]:
                if not mtp_thread.is_alive():
                    mtp_thread.join()
                    mtp_thread_list.remove(mtp_thread)
            time.sleep(5)
        mfg_rdt_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG RDT Test Duration:{:s}".format(mfg_rdt_stop_ts - mfg_rdt_start_ts))

        # dump the summary
        result = libmfg_utils.mfg_summary_disp("{:s} ITERATION-{:06d}".format(stage, loop), mfg_rdt_summary, mtpid_fail_list)

        # power off all the test mtp
        if loop == iteration or not result:
            libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

        mtp_mgmt_ctrl_list[0].cli_log_inf("RDT TEST ITERATION-{:06d} END".format(loop), level=0)
        libmfg_utils.cli_inf("#" * 320 + "\n" * 3)

        if not result:
            libmfg_utils.cli_inf("******AT LEAST ONE SLOT FAILED IN RDT TEST, SO EXIT RDT TEST******")
            break

    # print return code for JobD to pick up
    if result:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
