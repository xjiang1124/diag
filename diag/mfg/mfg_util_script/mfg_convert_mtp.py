#!/usr/bin/env python

"""
   Convert MTP from supporting Capri cards to supporting Elba cards, and vice versa.
   The different ASICs require a different JTAG CPLD, along with IO CPLD.

   Run this script with:
   ./mfg_convert_mtp.py -to ELBA
   or
   ./mfg_convert_mtp.py -to CAPRI

"""

import sys
import os
import time
import pexpect
import re
import argparse
import threading

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdiag_db import diag_db
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MTP_IMAGES
from libdefs import MTP_Const
from libdefs import MTP_TYPE
from libdefs import MFG_DIAG_CMDS
from libdefs import MFG_DIAG_SIG
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path


def load_mtp_cfg():
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/swi_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db


def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list=[], mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg)
    return mtp_mgmt_ctrl

def mtp_diag_pre_init(mtp_mgmt_ctrl):
    # start the mtp diag
    mtp_mgmt_ctrl.cli_log_inf("Pre Diag SW Environment Init", level=0)

    cmd = MFG_DIAG_CMDS().MTP_DIAG_INIT_FMT
    sig_list = [MFG_DIAG_SIG.MTP_DIAG_OK_SIG]
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
        mtp_mgmt_ctrl.cli_log_err("Failed to Init Diag SW Environment", level=0)
        return False

    cmd = "source ~/.bash_profile"
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Failed to Init Diag SW Environment", level=0)
        return False

    cmd = "env | grep UUT"
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Failed to execute env command", level=0)
        return False

    # config the prompt
    userid = mtp_mgmt_ctrl._mgmt_cfg[1]
    if not mtp_mgmt_ctrl.mtp_prompt_cfg(mtp_mgmt_ctrl._mgmt_handle, userid, mtp_mgmt_ctrl._mgmt_prompt):
        mtp_mgmt_ctrl.cli_log_err("Failed to Init Diag SW Environment", level=0)
        return False
    mtp_mgmt_ctrl._mgmt_prompt = "{:s}@MTP:".format(userid) + mtp_mgmt_ctrl._mgmt_prompt

    # register MTP diagsp
    cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Failed to Init Diag SW Environment", level=0)
        return False

    if not mtp_mgmt_ctrl.mtp_sys_info_init():
        mtp_mgmt_ctrl.cli_log_err("Failed to Init MTP system information", level=0)
        return False

    mtp_mgmt_ctrl.cli_log_inf("Pre Diag SW Environment Init complete\n", level=0)

    return True

def single_mtp_convert(mtp_mgmt_ctrl, mtp_images_list, mtp_expected_ver, mtp_id, diag_log_filep, mtp_test_summary, expected_mtp_type):
    """
    Steps to convert MTP from MTP_CAPRI to MTP_ELBA or vice versa:

        cpldutil -cpld-flash-prog -type IO -input <io_cpld_image>
        cpldutil -cpld-flash-prog -type JTAG -input <jtag_cpld_image>

        # Determine current MTP configuration
        Do an AC powercycle
        diag@MTP:~$ ./start_diag.sh
        diag@MTP:~$ source ~/.bash_profile
        diag@MTP:~$ env | grep MTP
        MTP_REV=REV_04      <== MTP Rev4
        CARD_NAME=MTP1
        CARD_TYPE=MTP
        UUT_TYPE=NAPLES_MTP
        MTP_TYPE=MTP_CAPRI  <== Capri MTP
        or
        MTP_TYPE=MTP_ELBA   <== Elba MTP

    """
    try: 
        # diag environment pre init once before programming
        if not mtp_diag_pre_init(mtp_mgmt_ctrl):
            mtp_mgmt_ctrl.cli_log_err("Unable to pre-init diag environment", level=0)
            mtp_mgmt_ctrl.mtp_chassis_shutdown()
            raise Exception

        # print the mtp system info before programming
        if not mtp_mgmt_ctrl.mtp_sys_info_disp():
            mtp_mgmt_ctrl.cli_log_err("Unable to retrieve MTP system info", level=0)
            mtp_mgmt_ctrl.mtp_chassis_shutdown()
            raise Exception

        # do the cpld programming
        sig_list = ["error", "fault", "exception"]
        cmd = "cpldutil -cpld-flash-prog -type IO -input /home/diag/{:s}".format(mtp_images_list[0])
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Failed to program IO-CPLD image", level = 0)
            raise Exception
        if True in [sig in mtp_mgmt_ctrl.mtp_get_cmd_buf() for sig in sig_list]:
            mtp_mgmt_ctrl.cli_log_err("Failed to program IO-CPLD image", level = 0)
            mtp_mgmt_ctrl.cli_log_err(mtp_mgmt_ctrl.mtp_get_cmd_buf(), level = 1)
            raise Exception

        cmd = "cpldutil -cpld-flash-prog -type JTAG -input /home/diag/{:s}".format(mtp_images_list[1])
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Failed to program JTAG-CPLD image", level = 0)
            raise Exception
        if True in [sig in mtp_mgmt_ctrl.mtp_get_cmd_buf() for sig in sig_list]:
            mtp_mgmt_ctrl.cli_log_err("Failed to program JTAG-CPLD image", level = 0)
            mtp_mgmt_ctrl.cli_log_err(mtp_mgmt_ctrl.mtp_get_cmd_buf(), level = 1)
            raise Exception

        # power cycle with enough wait time
        # if powercycle too quickly, CPLD won't have changed yet and could cause other issues (such as fan speed)
        if MTP_Const.MTP_OS_SHUTDOWN_DELAY + MTP_Const.MTP_POWER_CYCLE_DELAY < 60:
            mtp_mgmt_ctrl.cli_log_err("Please increase MTP_POWER_CYCLE_DELAY for running this script.", level=0)
            raise Exception

        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.mtp_power_cycle()

        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            raise Exception
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

        # Program new diag images
        mtp_diag_image = mtp_images_list[2]
        nic_diag_image = mtp_images_list[3]
        if not libmfg_utils.mtp_update_diag_image(mtp_mgmt_ctrl, mtp_diag_image, nic_diag_image, force_update=True):
            mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis diag image", level=0)
            raise Exception
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag Image is updated", level=0)

        # diag environment pre init after programming
        if not mtp_diag_pre_init(mtp_mgmt_ctrl):
            mtp_mgmt_ctrl.cli_log_err("Unable to pre-init diag environment", level=0)
            mtp_mgmt_ctrl.mtp_chassis_shutdown()
            raise Exception

        # get the mtp system info
        if not mtp_mgmt_ctrl.mtp_sys_info_disp():
            mtp_mgmt_ctrl.cli_log_err("Unable to retrieve MTP system info", level=0)
            mtp_mgmt_ctrl.mtp_chassis_shutdown()
            raise Exception

        # establish PSU/FAN control
        if not mtp_mgmt_ctrl.mtp_hw_init(MTP_Const.MFG_EDVT_NORM_FAN_SPD):
            mtp_mgmt_ctrl.cli_log_err("MTP HW Init Fail", level=0)
            mtp_mgmt_ctrl.mtp_chassis_shutdown()
            raise Exception

        # read back the IO cpld version
        if mtp_mgmt_ctrl._io_cpld_ver != mtp_expected_ver[0]:
            mtp_mgmt_ctrl.cli_log_err("Fail to program correct MTP IO-CPLD")
            raise Exception

        # read back the JTAG cpld version
        if mtp_mgmt_ctrl._jtag_cpld_ver != mtp_expected_ver[1]:
            mtp_mgmt_ctrl.cli_log_err("Fail to program correct MTP JTAG-CPLD")
            raise Exception

        # confirm environment variable has been set
        if mtp_mgmt_ctrl._mtp_type != expected_mtp_type:
            mtp_mgmt_ctrl.cli_log_err("Fail to set correct MTP_TYPE")
            raise Exception

    except Exception as e:
        mtp_test_summary.append((mtp_id, "", "MTP_"+str(mtp_mgmt_ctrl._mtp_type), False, False))
        mtp_mgmt_ctrl.cli_log_err(str(e))
        return False

    mtp_test_summary.append((mtp_id, "", "MTP_"+str(mtp_mgmt_ctrl._mtp_type), True, False))
    return True

def main():
    parser = argparse.ArgumentParser(description="MFG MTP upgrade", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", help="Increase output verbosity", action='store_true')
    parser.add_argument("--mtpid", "-mtpid", help="pre-select MTPs", nargs="*", default=[])
    parser.add_argument("-to", "--convert_to", help="Convert this MTP to ", choices=["ELBA", "CAPRI", "TURBO_ELBA"], required=True)

    args = parser.parse_args()
    if args.convert_to:
        mtp_type = args.convert_to
    else:
        sys.exit("Missing -to flag. argparser should not let us be here.")
    verbosity = False
    if args.verbosity:
        verbosity = True

    mtp_cfg_db = load_mtp_cfg()
    mtpid_list = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)
    mtp_mgmt_ctrl_list = list()
    mtpid_fail_list = list()
    test_log_filep_list = dict()
    diag_log_filep_list = dict()

    # init mtp_ctrl list
    for mtp_id in mtpid_list:
        test_log_filep_list[mtp_id] = None
        diag_log_filep_list[mtp_id] = None
        if verbosity:
            diag_log_filep_list[mtp_id] = sys.stdout
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep_list[mtp_id], diag_log_filep_list[mtp_id])
        mtp_mgmt_ctrl_list.append(mtp_mgmt_ctrl)

    mfg_dl_start_ts = libmfg_utils.timestamp_snapshot()

    # power on the mtp chassis
    libmfg_utils.mtpid_list_poweron(mtp_mgmt_ctrl_list)

    # Collect IO and JTAG CPLD image names
    try:
        mtp_images_list  = [MTP_IMAGES.mtp_io_cpld_img[mtp_type], MTP_IMAGES.mtp_jtag_cpld_img[mtp_type]]
        mtp_expected_ver = [MTP_IMAGES.mtp_io_cpld_ver[mtp_type], MTP_IMAGES.mtp_jtag_cpld_ver[mtp_type]]
    except KeyError:
        mtp_mgmt_ctrl.cli_log_err("Missing CPLD image for {:s}".format(mtp_type), level=0)
        return
    # Collect amd and arm diag images
    try:
        mtp_images_list.append(MTP_IMAGES.amd64_img[mtp_type])
        mtp_images_list.append(MTP_IMAGES.arm64_img[mtp_type])
    except KeyError:
        mtp_mgmt_ctrl.cli_log_err("Missing diag image for {:s}".format(mtp_type), level=0)
        return

    # Connect to MTP
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_connect():
            mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP Chassis", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        mtp_mgmt_ctrl.cli_log_inf("MTP Chassis is connected", level=0)

        mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)
        if mtp_capability < 2:
            mtp_mgmt_ctrl.cli_log_err("This upgrade is not allowed for MTP capability {:s}".format(mtp_capability), level=0)

        # MTP_REV
        cmd = MFG_DIAG_CMDS().MTP_REV_FMT
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Failed to send command for getting MTP revision", level = 0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue
        match = re.findall(r"MTP_REV=REV_([0-9]{2})", mtp_mgmt_ctrl.mtp_get_cmd_buf())
        if match:
            mtp_rev = match[0]
            if mtp_rev == "NONE":
                mtp_mgmt_ctrl.cli_log_err("This upgrade is not allowed for MTP Rev_{:s}".format(mtp_rev), level=0)
                mtpid_list.remove(mtp_id)
                mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
                mtpid_fail_list.append(mtp_id)
                continue

            if int(mtp_rev) < 3 and mtp_type != MTP_TYPE.CAPRI:
                ######################################################################
                # MTP Rev_01 and Rev_02 only support changing to Capri-compatible CPLD
                ######################################################################
                mtp_mgmt_ctrl.cli_log_err("This upgrade is not allowed for MTP Rev_{:s}".format(mtp_rev), level=0)
        else:
            mtp_mgmt_ctrl.cli_log_err("Failed to get MTP revision", level = 0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue

        # Copy over images if needed
        if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, mtp_images_list):
            mtp_mgmt_ctrl.cli_log_err("Unable to update MTP Chassis firmware", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
            continue

        # # Start logfile
        # test_log_filep_list[mtp_id] = list()
        # diag_log_filep_list[mtp_id] = list()
        # test_log_filep = open("test_convert.log", "w+", buffering=0)
        # test_log_filep_list[mtp_id].append(test_log_filep)
        # diag_log_filep = open("diag_convert.log", "w+", buffering=0)
        # diag_log_filep_list[mtp_id].append(diag_log_filep)

    # Sync timestamp to server
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list[:], mtp_mgmt_ctrl_list[:]):
        if not mtp_mgmt_ctrl.mtp_mgmt_set_date():
            mtp_mgmt_ctrl.cli_log_err("MTP Chassis timestamp sync failed", level=0)
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)
        else:
            mtp_mgmt_ctrl.cli_log_inf("MTP Chassis timestamp sync'd", level=0)

    # Copy script, config file on to each MTP Chassis
    mtp_thread_list = list()
    mfg_convert_summary = dict()
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mfg_convert_summary[mtp_id] = list()
        mtp_thread = threading.Thread(target = single_mtp_convert, args = (mtp_mgmt_ctrl,
                                                                           mtp_images_list,
                                                                           mtp_expected_ver,
                                                                           mtp_id,
                                                                           diag_log_filep_list[mtp_id],
                                                                           mfg_convert_summary[mtp_id], 
                                                                           mtp_type))
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

    # power off all the test mtp
    libmfg_utils.mtpid_list_poweroff(mtp_mgmt_ctrl_list)

    # dump the summary
    libmfg_utils.mfg_mtp_summary_disp("CONVERT", mfg_convert_summary, mtpid_fail_list)


if __name__ == "__main__":
    main()
