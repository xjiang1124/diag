#!/usr/bin/env python

import sys
import os
import time
import pexpect
import threading
import argparse
import re

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libdefs import FF_Stage
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl


def logfile_close(filep_list):
    for fp in filep_list:
        fp.close()
    os.system("sync")


def logfile_cleanup(file_list):
    for _file in file_list:
        os.system("rm -rf {:s}".format(_file))


def load_mtp_cfg():
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/swi_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db


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


def single_nic_fw_program(mtp_mgmt_ctrl, fru_cfg, cpld_img_file, slot):
    sn = fru_cfg[0]
    mac = fru_cfg[1]
    pn = fru_cfg[2]
    prog_date = fru_cfg[3]

    dsp = FF_Stage.FF_CFG
    for test in ["FRU_PROG", "CPLD_PROG", "CPLD_REF"]:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = libmfg_utils.timestamp_snapshot()
        # program FRU
        if test == "FRU_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn)
        # program CPLD
        elif test == "CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
        # refresh CPLD
        elif test == "CPLD_REF":
            ret = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(slot)
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown CFG Test: {:s}, Ignore".format(test))
            continue
        stop_ts = libmfg_utils.timestamp_snapshot()
        duration = str(stop_ts - start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


def main():
    parser = argparse.ArgumentParser(description="MTP FRU Config Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid

    mtp_cfg_db = load_mtp_cfg()

    # local log files
    log_filep_list = list()
    test_log_file = "test_cfg.log"
    test_log_filep = open(test_log_file, "w+", buffering=0)
    log_filep_list.append(test_log_filep)

    diag_log_file = "diag_cfg.log"
    diag_log_filep = open(diag_log_file, "w+", buffering=0)
    log_filep_list.append(diag_log_filep)

    fru_cfg_file = "fru_cfg.yaml"

    diag_nic_log_filep_list = list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = "diag_{:s}_cfg.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, "w+", buffering=0)
        log_filep_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list)

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, stage=FF_Stage.FF_CFG):
        mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
        logfile_close(log_filep_list)
        return

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    rc = mtp_mgmt_ctrl.mtp_nic_diag_init()
    if not rc:
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    dsp = FF_Stage.FF_CFG
    # load the fru config file
    nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(fru_cfg_file)

    mtp_mgmt_ctrl.cli_log_inf("MTP CFG Test Started", level=0)

    fail_nic_list = list()
    pass_nic_list = list()

    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Bypass empty slot")
            continue

        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if (
            card_type == NIC_Type.NAPLES100
            or card_type == NIC_Type.NAPLES100IBM
            or card_type == NIC_Type.NAPLES100HPE
            or card_type == NIC_Type.FORIO
            or card_type == NIC_Type.VOMERO
            or card_type == NIC_Type.VOMERO2
            ):
            mtp_exp_capability = 0x1
        elif (
            card_type == NIC_Type.NAPLES25
            or card_type == NIC_Type.NAPLES25SWM
            or card_type == NIC_Type.NAPLES25OCP
            or card_type == NIC_Type.NAPLES25SWMDELL
            or card_type == NIC_Type.NAPLES25SWM833
            or card_type == NIC_Type.ORTANO
            ):
            mtp_exp_capability = 0x2
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown NIC type detected")
            continue

        if not mtp_capability & mtp_exp_capability:
            mtp_mgmt_ctrl.cli_log_err("MTP doesn't support {:s}".format(card_type))
            mtp_mgmt_ctrl.mtp_chassis_shutdown()
            logfile_close(log_filep_list)
            return

        pass_nic_list.append(slot)

        for test in ["NIC_POWER", "NIC_TYPE", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            # nic power status check
            if test == "NIC_POWER":
                ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
            # nic type check
            elif test == "NIC_TYPE":
                ret = mtp_mgmt_ctrl.mtp_nic_type_valid(slot)
            # nic present check
            elif test == "NIC_PRSNT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
            # check nic init status
            elif test == "NIC_INIT":
                ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
            # check if nic comes up from diagfw
            elif test == "NIC_DIAG_BOOT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown CFG Test: {:s}, Ignore".format(test))
                continue
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

    # program the NIC firmware
    nic_thread_list = list()
    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        try:
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.cpld_img[card_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing cpld image for {:s}".format(card_type))
            fail_nic_list.append(slot)
            pass_nic_list.remove(slot)
            continue

        nic_fru_info = mtp_mgmt_ctrl.mtp_get_nic_fru(slot)
        mac = nic_fru_info[1].replace('-', '')
        date = nic_fru_info[3]

        if mac not in nic_fru_cfg.keys():
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "No config entry found for mac {:s}\n".format(mac))
            continue

        sn = nic_fru_cfg[mac]["NEW_SN"]
        pre_sn = nic_fru_cfg[mac]["ORG_SN"]
        pn = nic_fru_cfg[mac]["NEW_PN"]
        pre_pn = nic_fru_cfg[mac]["ORG_PN"]
        if pre_sn != nic_fru_info[0]:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "FRU SN mismatch, Onboard: {:s}, CFG: {:s}".format(nic_fru_info[0], pre_sn))
            continue
        if pre_pn != nic_fru_info[2]:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "FRU PN mismatch, Onboard: {:s}, CFG: {:s}".format(nic_fru_info[2], pre_pn))
            continue

        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FRU Config Matrix:")
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Stale SN = {:s}; MAC = {:s}; PN = {:s}".format(pre_sn, mac, pre_pn))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "====> SN = {:s}; MAC = {:s}; PN = {:s}".format(sn, mac, pn))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "CPLD image: " + os.path.basename(cpld_img_file))
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FRU Config Matrix end\n")

        fru_cfg_list = [sn, mac, pn, date]
        nic_thread = threading.Thread(target = single_nic_fw_program, args = (mtp_mgmt_ctrl,
                                                                              fru_cfg_list,
                                                                              cpld_img_file,
                                                                              slot))
        nic_thread.daemon = True
        nic_thread.start()
        nic_thread_list.append(nic_thread)
        time.sleep(2)

    # monitor all the thread
    while True:
        if len(nic_thread_list) == 0:
            break
        for nic_thread in nic_thread_list[:]:
            if not nic_thread.is_alive():
                nic_thread.join()
                nic_thread_list.remove(nic_thread)
        time.sleep(5)

    # power cycle all nic
    mtp_mgmt_ctrl.mtp_power_cycle_nic()

    # init nic diag env.
    if not mtp_mgmt_ctrl.mtp_nic_diag_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC Diag Environment failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        logfile_close(log_filep_list)
        return

    for slot in range(len(nic_prsnt_list)):
        if not nic_prsnt_list[slot]:
            continue
        if slot in fail_nic_list:
            continue

        for test in ["NIC_POWER", "NIC_PRSNT", "NIC_INIT", "NIC_DIAG_BOOT"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            # nic power status check
            if test == "NIC_POWER":
                ret = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
            # nic present check
            elif test == "NIC_PRSNT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_prsnt(slot)
            # nic status check
            elif test == "NIC_INIT":
                ret = mtp_mgmt_ctrl.mtp_check_nic_status(slot)
            elif test == "NIC_DIAG_BOOT":
                ret = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown CFG Test: {:s}, Ignore".format(test))
                continue
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        # CFG Verify process
        nic_fru_info = mtp_mgmt_ctrl.mtp_get_nic_fru(slot)
        mac = nic_fru_info[1].replace('-', '')
        if mac not in nic_fru_cfg.keys():
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "No config entry found for mac {:s}\n".format(mac))
            continue

        exp_sn = nic_fru_cfg[mac]["NEW_SN"]
        exp_mac = nic_fru_info[1]
        exp_pn = nic_fru_cfg[mac]["NEW_PN"]
        exp_date = nic_fru_info[3]

        for test in ["FRU_VERIFY", "CPLD_VERIFY"]:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = libmfg_utils.timestamp_snapshot()
            # verify FRU
            if test == "FRU_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_fru(slot, exp_sn, exp_mac, exp_pn, exp_date)
            # verify CPLD
            elif test == "CPLD_VERIFY":
                ret = mtp_mgmt_ctrl.mtp_verify_nic_cpld(slot)
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown CFG Test: {:s}, Ignore".format(test))
                continue
            stop_ts = libmfg_utils.timestamp_snapshot()
            duration = str(stop_ts - start_ts)
            if not ret:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                fail_nic_list.append(slot)
                pass_nic_list.remove(slot)
                break
            else:
                mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

    # power off nic
    mtp_mgmt_ctrl.mtp_power_off_nic()
    mtp_mgmt_ctrl.cli_log_inf("MTP CFG Test Complete", level=0)

    for slot in pass_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

    for slot in fail_nic_list:
        key = libmfg_utils.nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    logfile_close(log_filep_list)
    return


if __name__ == "__main__":
    main()

