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
import libmtp_utils
from libdefs import NIC_Type
from libdefs import Swm_Test_Mode
from libdefs import FF_Stage
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libdefs import MFG_DIAG_SIG
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db


def load_mtp_cfg():
    # MTP Screen Chassis
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/mtp_screen_chassis_cfg.yaml"))
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
    setup_rslt_list[mtp_mgmt_ctrl._id] = libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl)

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
    mtp_setup(mtp_mgmt_ctrl, setup_rslt_list)

    if not setup_rslt_list[mtp_id]:
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")

    #fail_nic_list = libmfg_utils.loopback_sanity_check(mtpid_list, mtp_mgmt_ctrl_list)
    fail_nic_list = dict()
    for mtp_id in mtpid_list:
        fail_nic_list[mtp_id] = list()

    # if all slots in an MTP fail, assert stop on failure here
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        if len(fail_nic_list[mtp_id]) == mtp_mgmt_ctrl._slots:
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP completely failed Sanity Check. Test abort..")
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)

    # close NIC ssh sessions
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mtp_mgmt_ctrl.mtp_nic_para_session_end()

    return fail_nic_list

def single_mtp_screen_test(mtp_script_dir, mtp_mgmt_ctrl, mtp_id, fail_nic_list, mtp_test_summary, swm_test_mode, mtp_sn, skip_test=[]):
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
    cmd = "mkdir {:s}".format(mtp_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)    
    cmd = "cd {:s}".format(mtp_script_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_start_ts = libmfg_utils.timestamp_snapshot()
    mtp_mgmt_ctrl.cli_log_inf("MFG MTP Screen Test Start", level=0)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)

    cmd = "./mtp_screen_regression.py --mtpid {:s} --swm {:s} --mtpsn {:s} ".format(mtp_id, swm_test_mode, mtp_sn)
    if skip_test:
        cmd += skipped_testlist
    if fail_slots:
        cmd += fail_slots

    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MFG_MTPSCREEN_TEST_TIMEOUT)
    mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
    mtp_mgmt_ctrl.cli_log_inf("MFG MTP Screen Test Complete", level=0)
    mtp_stop_ts = libmfg_utils.timestamp_snapshot()

    test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_script_dir, mtp_id, mtp_test_summary, FF_Stage.FF_SRN)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("MTP Collect MTP Screen Test result failed", level=0)
        return
    if GLB_CFG_MFG_TEST_MODE:
        libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, FF_Stage.FF_SRN, mtp_test_summary) 
        sn_type = ""
        duration = mtp_stop_ts - mtp_start_ts

        # dump the summary
        for slot, sn, nic_type, rc in mtp_test_summary:
            nic_cli_id_str = id_str(mtp=mtp_id, nic=int(slot), base=0)
            if rc:
                mtp_mgmt_ctrl.cli_log_inf("[{:s}] {:s} PASS".format(mtp_id, mtp_sn))
            else:
                mtp_mgmt_ctrl.cli_log_inf("[{:s}] {:s} FAIL".format(mtp_id, mtp_sn))


        ret = libmfg_utils.flx_web_srv_post_uut_report(FF_Stage.FF_SRN, sn_type, mtp_sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, "MTP_SCREEN", "FAIL", err_dsc_list, err_code_list)
        if not ret:
            mtp_mgmt_ctrl.cli_log_inf(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
        else:
            mtp_mgmt_ctrl.cli_log_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))

    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)
    return


def main():
    parser = argparse.ArgumentParser(description="MFG MTP SCREEN Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip-test", help="skip a particular test section", nargs="*", default=[])

    verbosity = False
    swmtestmode = Swm_Test_Mode.SW_DETECT
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    if args.swm:
        swmtestmode = args.swm

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db)
    mtpid_fail_list = list()
    mtp_mgmt_ctrl_list = list()
    fail_nic_list = dict()
    scan_rslt = dict()
    mtp_sn = ""

    # only allow one per time
    if len(mtpid_list) > 1:
        mtp_mgmt_ctrl.cli_log_err("One MTP per time", level=0)
        return

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
    open_file_track_mtp_list = dict()
    logfile_dir_list = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id] = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=FF_Stage.FF_SRN)

    mfg_srn_start_ts = libmfg_utils.timestamp_snapshot()

    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_mgmt_ctrl.cli_log_inf("Start the Barcode Scan Process", level=0)
        while True:
            scan_rslt = mtp_mgmt_ctrl.mtp_screen_barcode_scan()
            if scan_rslt and scan_rslt["VALID"]:
                mtp_mgmt_ctrl.cli_log_inf("Scan validate MTP SN", level=0)
                break;
            mtp_mgmt_ctrl.cli_log_inf("Restart the Barcode Scan Process", level=0)

    mtp_sn = scan_rslt["MTP_SN"].strip()
    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    # onnect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="SRN-SSH", retry_with_powercycle=True):
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis. Abort test", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)


    # i210
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):    
        ret = libmtp_utils.check_mtp_host_nic_presence(mtp_mgmt_ctrl)
        if not ret:
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue

        if ret:
            cmd = "./eeupdate64e /NIC=1 /D=Dev_Start_I210_SerdesBX_NOMNG_16Mb_A2.bin"
            rs = mtp_mgmt_ctrl.mtp_mgmt_exec_sudo_cmd_resp(cmd)
            if rs.startswith("[FAIL]:"):
                ret = False
                mtp_mgmt_ctrl.cli_log_err("MTP I210 command failed.{:s}".format(cmd), level=0)
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
                continue
            else:
                if "8086-1537" in rs and "8086-1533" in rs: 
                    mtp_mgmt_ctrl.cli_log_inf("MTP I210 second command response Pass.", level=0)
                else:
                    mtp_mgmt_ctrl.cli_log_err("MTP I210 second command response Fail.", level=0)
                    mtpid_list.remove(mtp_id)
                    mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                    mtpid_fail_list.append(mtp_id)
                    continue

        if ret:
            # power cycle all the test mtp
            mtp_mgmt_ctrl.mtp_power_cycle()

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, stage=FF_Stage.FF_SRN, level=0):
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue

    fail_nic_list = dict()
    # Sanity check
    try:
        if len(mtpid_list) > 0:    
            for mtp_id in mtpid_list:
                fail_nic_list[mtp_id] = list()          
            #fail_nic_list = sanity_check(mtp_cfg_db, mtpid_list, mtp_mgmt_ctrl_list, mtpid_fail_list)

    except Exception as e:
        err_msg = traceback.format_exc()
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
            mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)
          
    # close file handles
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])
    for mtp_id in mtpid_fail_list:
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])

    # Copy script, config file on to each MTP Chassis
    # mtp_srn_script_dir = "mtp_regression/"
    mtp_srn_script_dir = "mtp_srn_script/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_srn_script_pkg = "mtp_regression.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP SCREEN Test script", level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_srn_script_dir, mtp_srn_script_pkg, logfile_dir_list[mtp_id]):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP SCREEN Test script failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Deploy MTP SCREEN Test script complete", level=0)

    mtp_thread_list = list()
    mfg_srn_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_srn_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_screen_test, args = (MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+mtp_srn_script_dir,
                                                                            mtp_mgmt_ctrl,
                                                                            mtp_id,
                                                                            fail_nic_list[mtp_id],
                                                                            mfg_srn_summary[mtp_id],
                                                                            swmtestmode,
                                                                            mtp_sn,
                                                                            args.skip_test))
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
    mfg_srn_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG MTP SCREEN Test Duration:{:s}".format(mfg_srn_stop_ts - mfg_srn_start_ts))

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

    # dump the summary
    libmfg_utils.mfg_summary_srn_disp(FF_Stage.FF_SRN, mfg_srn_summary, mtpid_fail_list, mtp_sn)


if __name__ == "__main__":
    main()
