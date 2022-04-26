#!/usr/bin/env python

import sys
import os
import time
import pexpect
import re
import argparse
import threading

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_ASIC_SUPPORT
from libdefs import UUT_Type
from libdefs import Swm_Test_Mode
from libdefs import FF_Stage
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import MTP_IMAGES
from libmfg_cfg import TOR_IMAGES
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db


def load_mtp_cfg():
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    # if not GLB_CFG_MFG_TEST_MODE:
    #     mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    # mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_tor_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db

def mtp_test_cleanup(error_code, fp_list=None):
    if fp_list:
        for fp in fp_list:
            fp.close()
    os.system("sync")

def save_logfile(mtp_id, mtp_mgmt_ctrl, log_dir, logfile_list, stage="NT"):
    # Package this UUT's logfile
    log_sub_dir = os.path.basename(os.path.dirname(log_dir)) # aka MFG_STAGE_LOG_DIR

    # extract log timestamp from one of the filenames
    if logfile_list:
        timestamp_length = 19
        log_timestamp = log_sub_dir[-19:]
    else:
        log_timestamp = libmfg_utils.get_timestamp()

    # pkg the logfile
    # MFG_DL_LOG_PKG_FILE = "NT_{:s}_{:s}.tar.gz"
    # MFG_DL_LOG_DIR = "NT_{:s}_{:s}/"
    # MFG_LOG_PKG_FMT = "tar czf {:s} -C {:s} {:s}"
    log_pkg_file = MTP_DIAG_Logfile.MFG_STAGE_LOG_PKG_FILE.format(stage, mtp_id, log_timestamp)
    os.system(MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format(log_dir+log_pkg_file, log_dir, log_sub_dir))

    # move the logs to the log root dir
    sn = mtp_mgmt_ctrl._sn
    nic_type = mtp_mgmt_ctrl._uut_type
    if stage == FF_Stage.FF_SWI:
        if GLB_CFG_MFG_TEST_MODE:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_SWI_LOG_DIR_FMT.format(nic_type, sn)
        else:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_SWI_LOG_DIR_FMT.format(nic_type, sn)
    else:
        if GLB_CFG_MFG_TEST_MODE:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_P2C_LOG_DIR_FMT.format(nic_type, sn)
        else:
            mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_P2C_LOG_DIR_FMT.format(nic_type, sn)
    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir))
    libmfg_utils.cli_inf("[{:s}] Collecting log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
    os.system("cp {:s} {:s}".format(log_dir+log_pkg_file, mfg_log_dir+os.path.basename(log_pkg_file)))

    # cleanup the log dir
    for _file in [log_dir+log_sub_dir, log_dir+log_pkg_file]:
        os.system("rm -rf {:s}".format(_file))

def mtp_fail_process(mtp_id, mtp_mgmt_ctrl, logfile_dir, open_file_mtp, stage=FF_Stage.FF_P2C):
    mtp_mgmt_ctrl.cli_log_inf("Power off APC", level=0)
    mtp_mgmt_ctrl.mtp_apc_pwr_off()
    libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
    save_logfile(mtp_id, mtp_mgmt_ctrl, logfile_dir, open_file_mtp, stage)

def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, telnet=False):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    if telnet:
        mtp_ts_cfg = mtp_cfg_db.get_mtp_console(mtp_id)
        if not mtp_ts_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find termserver config")
            return
    else:
        mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
        if not mtp_mgmt_cfg:
            libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
            return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, ts_cfg=mtp_ts_cfg, apc_cfg=mtp_apc_cfg, num_of_slots=2, slots_to_skip=mtp_slots_to_skip)
    if telnet:
        mtp_mgmt_ctrl.set_uut_type(UUT_Type.TOR)
    return mtp_mgmt_ctrl

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

    test_log_file = libmfg_utils.get_mtp_logfile(mtp_mgmt_ctrl, mtp_script_dir, mtp_id, mtp_test_summary, FF_Stage.FF_P2C)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("MTP Collect P2C Test result failed", level=0)
        return
    if mtp_mgmt_ctrl._uut_type != UUT_Type.TOR:
        libmfg_utils.mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, FF_Stage.FF_P2C)
    cmd = "rm -rf {:s}".format(test_log_file)
    os.system(cmd)
    
    # shut down system
    mtp_mgmt_ctrl.uut_chassis_shutdown()

    return


def main():
    parser = argparse.ArgumentParser(description="MFG P2C Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--skip-test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--mtpid", "--mtp-id", "--uut-id", "--uutid", "-uutid", "-mtpid", help="pre-select UUTs", nargs="*", default=[])

    verbosity = False
    swmtestmode = Swm_Test_Mode.SW_DETECT
    args = parser.parse_args()
    if args.verbosity:
        verbosity = True
    if args.swm:
        swmtestmode = args.swm

    TAORMINA_TEST = True

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
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

        if TAORMINA_TEST:
            mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, telnet=True)
        else:
            mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list)
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)
        fail_nic_list[mtp_id] = list()

    # logfiles
    open_file_track_mtp_list = dict()
    logfile_dir_list = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id] = libmfg_utils.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=FF_Stage.FF_P2C)

    mfg_p2c_start_ts = libmfg_utils.timestamp_snapshot()
    dsp = FF_Stage.FF_P2C

    if not TAORMINA_TEST:
        # power on the mtp chassis
        libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)
    else:
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
            mtp_mgmt_ctrl.set_homedir(MTP_DIAG_Path.ONBOARD_TOR_DIAG_PATH)
            mtp_mgmt_ctrl._slots = 2

            sn = NIC_Type.UNKNOWN

            # boot test OS
            test="OS_BOOT"
            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            if not mtp_mgmt_ctrl.tor_boot_select(1):
                mtp_mgmt_ctrl.cli_log_err("Unable to connect UUT Chassis", level=0)
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_fail_process(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id])
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
                continue

            if not libmfg_utils.mtp_clear_console(mtp_mgmt_ctrl):
                mtp_fail_process(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id])
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
                continue

            # read FRU
            test="FRU_INIT"
            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            if not mtp_mgmt_ctrl.tor_fru_init():
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_fail_process(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id])
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
                continue

            test = "MGMT_INIT_OS"
            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            if not mtp_mgmt_ctrl.tor_mgmt_init(False):
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_fail_process(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id])
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
                continue

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, prompt_id="P2C-SSH"):
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            mtp_fail_process(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id])
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)
        sn = mtp_mgmt_ctrl._sn

        if not TAORMINA_TEST:
            onboard_image_files = mtp_mgmt_ctrl.mtp_diag_get_img_files()
            mtp_diag_image = MFG_IMAGE_FILES.MTP_AMD64_IMAGE
            nic_diag_image = MFG_IMAGE_FILES.MTP_ARM64_IMAGE
            if not libmfg_utils.mtp_update_diag_image(mtp_mgmt_ctrl, mtp_diag_image, nic_diag_image, onboard_image_files):
                mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis diag image", level=0)
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
                continue
            mtp_mgmt_ctrl.cli_log_inf("MTP Diag Image is updated", level=0)
        else:
            # copy diag image
            test="DIAG_UPDATE"
            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            asic_type = MTP_ASIC_SUPPORT.ELBA
            x86_image = MTP_IMAGES.AMD64_IMG[asic_type]
            arm_image = MTP_IMAGES.ARM64_IMG[asic_type]
            homedir = mtp_mgmt_ctrl.get_homedir()
            onboard_images = mtp_mgmt_ctrl.mtp_diag_get_img_files(homedir)
            if not libmfg_utils.mtp_update_diag_image(mtp_mgmt_ctrl, x86_image, arm_image, onboard_images, homedir=homedir):
                mtp_mgmt_ctrl.cli_log_err("Unable to update diag image", level=0)
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_fail_process(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id])
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
                continue
        if mtp_mgmt_ctrl._uut_type == UUT_Type.TOR:
            test = "PYPKG_UPDATE"
            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            homedir = mtp_mgmt_ctrl.get_homedir()
            python_lib_dir = homedir + "python_files/"
            if not libmfg_utils.mtp_update_packages(mtp_mgmt_ctrl, "release/packages/", python_lib_dir):
                mtp_mgmt_ctrl.cli_log_err("Unable to update python packages", level=0)
                duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
                mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration), level=0)
                mtp_fail_process(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id])
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
                continue

    # Sync timestamp to server
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        timestamp_str = str(libmfg_utils.timestamp_snapshot())
        if not mtp_mgmt_ctrl.mtp_mgmt_set_date(timestamp_str):
            mtp_mgmt_ctrl.cli_log_err("MTP Chassis timestamp sync failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Chassis timestamp sync'd", level=0)

    # close file handles
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])
    for mtp_id in mtpid_fail_list:
        mtp_test_cleanup(open_file_track_mtp_list[mtp_id])

    # Copy script, config file on to each MTP Chassis
    mtp_p2c_script_dir = "mtp_regression/"
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        mtp_p2c_script_pkg = "mtp_regression.{:s}.tar".format(mtp_id)
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP P2C Test script", level=0)
        if not libmfg_utils.mtp_init_test_script(mtp_mgmt_ctrl, mtp_p2c_script_dir, mtp_p2c_script_pkg, logfile_dir_list[mtp_id]):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP P2C Test script failed", level=0)
            mtp_fail_process(mtp_id, mtp_mgmt_ctrl, logfile_dir_list[mtp_id], open_file_track_mtp_list[mtp_id])
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Deploy MTP P2C Test script complete", level=0)

    mtp_thread_list = list()
    mfg_p2c_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_p2c_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_p2c_test, args = (mtp_mgmt_ctrl.get_homedir()+mtp_p2c_script_dir,
                                                                            mtp_mgmt_ctrl,
                                                                            mtp_id,
                                                                            fail_nic_list[mtp_id],
                                                                            mfg_p2c_summary[mtp_id],
                                                                            swmtestmode,
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

    mfg_p2c_stop_ts = libmfg_utils.timestamp_snapshot()
    libmfg_utils.cli_inf("MFG P2C Test Duration:{:s}".format(mfg_p2c_stop_ts - mfg_p2c_start_ts))

    # power off all the test mtp
    # libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)



    # dump the summary
    libmfg_utils.mfg_summary_disp(FF_Stage.FF_P2C, mfg_p2c_summary, mtpid_fail_list)


if __name__ == "__main__":
    main()
