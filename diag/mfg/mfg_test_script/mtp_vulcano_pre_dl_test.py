#!/usr/bin/env python3

import sys
import os
import argparse
import re
import time
import traceback

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_SIG
from libdefs import MFG_DIAG_CMDS
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import PSLC_MODE_TYPE_LIST
from libmfg_cfg import CAPRI_NIC_TYPE_LIST
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import GIGLIO_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmfg_cfg import CTO_MODEL_TYPE_LIST
from libmfg_cfg import FAILSAFE_CPLD_TYPE_LIST
from libmfg_cfg import MFG_VALID_NIC_TYPE_LIST
from libmfg_cfg import ADI_VRM_TYPE_LIST
from libmfg_cfg import MFG_VALID_NIC_TYPE_LIST
from libsku_cfg import PART_NUMBERS_MATCH
from libmfg_cfg import MTP_HEALTH_MONITOR
from libmfg_cfg import DRY_RUN
from libmfg_cfg import SALINA_NIC_TYPE_LIST
from libmfg_cfg import VULCANO_NIC_TYPE_LIST
from libmfg_cfg import SALINA_DPU_NIC_TYPE_LIST
from libmfg_cfg import SALINA_AI_NIC_TYPE_LIST
from libdefs import MTP_TYPE
from libdefs import FF_Stage
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode
import image_control
import testlog
import test_utils
import parallelize
import scanning

def logfile_close(filep_list):
    for fp in filep_list:
        fp.close()
    os.system("sync")

def load_mtp_cfg(cfg_yaml=None):
    # DL/P2C MTP Chassis
    mtp_chassis_cfg_file_list = list()
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/"+cfg_yaml))
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
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

def dl_display_program_matrix(mtp_mgmt_ctrl, slot, swmtestmode=Swm_Test_Mode.SW_DETECT):
    sn = mtp_mgmt_ctrl.get_scanned_sn(slot)
    mac = mtp_mgmt_ctrl.get_scanned_mac(slot)
    pn = mtp_mgmt_ctrl.get_scanned_pn(slot)
    dpn = mtp_mgmt_ctrl.get_scanned_dpn(slot)
    prog_date = mtp_mgmt_ctrl.get_scanned_ts(slot)
    mac_ui = libmfg_utils.mac_address_format(mac)
    alom_sn = None
    alom_pn = None
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
        alom_sn = mtp_mgmt_ctrl.get_scanned_alom_sn(slot)
        alom_pn = mtp_mgmt_ctrl.get_scanned_alom_pn(slot)

    riser_sn = None
    if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25OCP:
        riser_sn = mtp_mgmt_ctrl.mtp_get_nic_ocp_adapter_sn(slot)

    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

    print("")
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix:")
    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
        alom_sn = mtp_mgmt_ctrl.get_scanned_alom_sn(slot)
        alom_pn = mtp_mgmt_ctrl.get_scanned_alom_pn(slot)
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}; SN_ALOM = {:s}; PN_ALOM = {:s}".format(sn, mac_ui, pn, alom_sn, alom_pn))
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "SN = {:s}; MAC = {:s}; PN = {:s}".format(sn, mac_ui, pn))
    if dpn:
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "DPN = {:s}".format(dpn))
    if nic_type == NIC_Type.NAPLES25OCP:
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, "OCP Adapter SN = {:s}".format(riser_sn))

    dl_image_dict = image_control.get_all_images_for_stage(mtp_mgmt_ctrl, slot, FF_Stage.FF_DL)
    for image_name, image_file_path in dl_image_dict.items():
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, image_name + " image: " + os.path.basename(image_file_path))
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "FW Program Matrix end")

@parallelize.parallel_nic_using_ssh
def dl_uc_img_program(mtp_mgmt_ctrl, slot, override_fd_descriptors=False):
    dsp = FF_Stage.FF_DL
    uc_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_suc_diag_img(mtp_mgmt_ctrl, slot, dsp)["filename"]
    cmd_format = MFG_DIAG_CMDS().PANAREA_SUC_DIAG_IMAGE_PROG
    return mtp_mgmt_ctrl.mtp_nic_uc_image_program(slot, cmd_format, uc_img_file, override_fd_descriptors)

@parallelize.parallel_nic_using_ssh
def dl_inter_uc_img_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    inter_uc_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_inter_suc_diag_img(mtp_mgmt_ctrl, slot, dsp)["filename"]
    cmd_format = MFG_DIAG_CMDS().PANAREA_SUC_INTER_DIAG_IMAGE_PROG
    return mtp_mgmt_ctrl.mtp_nic_uc_image_program(slot, cmd_format, inter_uc_img_file)

@parallelize.parallel_nic_using_ssh
def dl_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.PANAREA:
        return mtp_mgmt_ctrl.mtp_nic_uc_zephyr_cpld_update(slot, cpld_img_file)
    else:
        return mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)

@parallelize.parallel_nic_using_ssh
def dl_fail_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]

    if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.PANAREA:
        return mtp_nic_uc_zephyr_cpld_update(mtp_mgmt_ctrl, slot, failsafe_cpld_img_file, partition='1')
    else:
        return mtp_mgmt_ctrl.mtp_program_nic_failsafe_cpld(slot, failsafe_cpld_img_file)


def mtp_nic_uc_zephyr_cpld_update(mtp_mgmt_ctrl, slot, cpld_img_file, partition='0', dl_step=True):
    """
    update CPLD through micro controller zpher shell cpld command
        Subcommands:
        interface  : (debug) Show interface details
        id         : (debug) Read device ID
        cfgen      : (debug) Enable config mode - non-debug commands may disable again!
        cfgdis     : (debug) Disable config mode
        status0    : (debug) Read status reg 0
        status1    : (debug) Read status reg 1
        feabits    : (debug) Read feature bits
        sector     : (debug) <n> Select sector and reset address
        read       : (debug) Read next 16-byte page
        erase      : (debug) <n> Erase sector
        crc        : <0|1> Show CRC32 of CFG0 or CFG1
        load_buf   : <0|1> Load CFG0 or CFG1 into local buffer
        crc_buf    : Show CRC of local buffer
        prog_buf   : <0|1> Program CFG0 or CFG1 from local buffer
        refresh    : Reboot CPLD via 'Refresh' config interface command
        rcr        : <addr> Read common register (hex args)
        wcr        : <addr> <byte> Write common register (hex args)
        op         : <byte> [<byte>...] Raw reg interface SPI op (hex args)
    """

    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

    if nic_type not in VULCANO_NIC_TYPE_LIST:
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "This cpld update function not meant for this card {:s}".format(nic_type))
        return False

    if dl_step:
        stage = FF_Stage.FF_DL
    else:
        stage = FF_Stage.FF_SWI

    nic_cpld_info = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cpld()
    if not nic_cpld_info:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Program NIC CPLD failed, can not retrieve CPLD info")
        return False
    cur_ver = nic_cpld_info[0]
    cur_timestamp = nic_cpld_info[1]

    expected_version = image_control.get_cpld(mtp_mgmt_ctrl, slot, stage)["version"]
    expected_timestamp = image_control.get_cpld(mtp_mgmt_ctrl, slot, stage)["timestamp"]

    if cur_ver == expected_version and cur_timestamp == expected_timestamp:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "NIC CPLD is up-to-date, But Program Again")

    support_partitions = ("0", "1")
    if partition not in support_partitions:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Please provide correct cpld partion , it should be in {:d}".format(str(support_partitions)))
        return False
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].uc_zephyr_cpld_update(cpld_img_file, partition):
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Program CPLD Failed")
        mtp_mgmt_ctrl.mtp_get_nic_err_msg(slot)
        return False
    mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_require_cpld_refresh(True)

    return True


def health_status(mtp_health):
    mtp_health.monitr_mtp_health(timeout=MTP_Const.MTP_HEALTH_MONITOR_CYCLE)

def main():
    parser = argparse.ArgumentParser(description="MTP Pre DL Test Script to program the intermediate suc image, Vulcano Only", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid

    mtp_cfg_db = load_mtp_cfg()

    swmtestmode = Swm_Test_Mode.SW_DETECT

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, sys.stdout, None, [], skip_slots=[])
    # local logfiles
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=FF_Stage.FF_DL)

    mtp_mgmt_ctrl.cli_log_inf("MTP Pre DL Test Started", level=0)

    try:
        # read scanned barcode file except when we're skipping in dev environment
        scanned_nic_fru_cfg = dict()
        scanning.read_scanned_barcodes(mtp_mgmt_ctrl)
        scanned_nic_fru_cfg = mtp_mgmt_ctrl.barcode_scans

        if not test_utils.mtp_common_setup_scandl(mtp_mgmt_ctrl, FF_Stage.FF_DL, scanned_nic_fru_cfg, [], True):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            logfile_close(open_file_track_list)
            return

        if MTP_HEALTH_MONITOR:
            thread_health = threading.Thread(target=health_status, args=(mtp_mgmt_ctrl.get_mtp_health_monitor(),))
            thread_health.start()

        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        fail_nic_list = list()
        pass_nic_list = list()

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            if not nic_prsnt_list[slot]:
                continue
            key = libmfg_utils.nic_key(slot)
            if not scanned_nic_fru_cfg[key]["VALID"]:
                continue
            if slot not in pass_nic_list:
                pass_nic_list.append(slot)

        def get_slots_of_type(nic_type, except_type=[]):
            return mtp_mgmt_ctrl.get_slots_of_type(nic_type, pass_nic_list, except_type)

        def run_dl_test(nic_list_orig, test, *test_args, **test_kwargs):
            """ unconventional to define in main() space, but easier to get access to mtp_mgmt_ctrl, pass_nic_list, fail_nic_list, args this way"""
            stage = FF_Stage.FF_DL
            nic_list = nic_list_orig[:]

            if test in []:
                test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, stage, test)
                return nic_list

            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            test_utils.test_start_nic_log_message(mtp_mgmt_ctrl, nic_list, stage, test)

            if DRY_RUN:
                rlist = []
            elif test == "SCAN_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_scan_verify(nic_list)
            elif test == "DPN_VALIDATE":
                rlist = mtp_mgmt_ctrl.mtp_nic_validate_pn_dpn_match(nic_list)
            elif test == "NIC_TYPE":
                rlist = mtp_mgmt_ctrl.mtp_nic_type_test(nic_list)
            elif test == "NIC_INIT":
                rlist = mtp_mgmt_ctrl.mtp_check_nic_list_status(nic_list)
            elif test == "NIC_PWRCYC":
                rlist = mtp_mgmt_ctrl.mtp_power_cycle_nic(nic_list, dl=True)
            elif test == "inter_uC_DIAG_IMG_PROG":
                rlist = dl_inter_uc_img_program(mtp_mgmt_ctrl, nic_list)
            elif test == "CPLD_PROG":
                rlist = dl_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "NIC_CTRL_INSTANCE_CPLD_PROPERTY_UPDATE":
                rlist = mtp_mgmt_ctrl.mtp_nic_diag_init_cpld_diag(nic_list, emmc_format=False)
            elif test == "CPLD_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_cpld(nic_list)
            elif test == "FSAFE_CPLD_PROG":
                rlist = dl_fail_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "uC_DIAG_IMG_PROG_OVERRIDE_FD_DESCRIPTORS":
                rlist = dl_uc_img_program(mtp_mgmt_ctrl, nic_list, override_fd_descriptors=True)
            elif test == "uC_VERSION_CHK":
                rlist = mtp_mgmt_ctrl.mtp_nic_suc_version_read_check(nic_list)
            elif test == "VULVANO_FOGA_UART_STATS_DUMP":
                rlist = mtp_mgmt_ctrl.mtp_vulcano_fpga_uart_stats_dump(nic_list)
            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown test '{:s}'".format(test))
                rlist = nic_list

            # catch bad return value
            if not isinstance(rlist, list):
                mtp_mgmt_ctrl.cli_log_err("Test {} failed with '{}', expected slot list".format(test, repr(rlist)))
                rlist = nic_list[:]

            rlist = list(set(rlist))

            for slot in rlist:
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot, testname=test, stage=stage)
                # update input list, could be pass_nic_list or a subset
                if slot in nic_list_orig:
                    nic_list_orig.remove(slot)
                # update global pass/fail list
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)

            duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
            test_utils.test_fail_nic_log_message(mtp_mgmt_ctrl, rlist, stage, test, start_ts, swmtestmode)
            test_utils.test_pass_nic_log_message(mtp_mgmt_ctrl, nic_list_orig, stage, test, start_ts, swmtestmode)

            return rlist

        dsp = FF_Stage.FF_DL
        mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)
        # run_dl_test(pass_nic_list, "SCAN_VERIFY")
        # validate the DPN is allowed for this PN
        dpn_test_nic_list = get_slots_of_type(CTO_MODEL_TYPE_LIST)
        run_dl_test(dpn_test_nic_list, "DPN_VALIDATE")
        for slot in pass_nic_list:
            dl_display_program_matrix(mtp_mgmt_ctrl, slot, swmtestmode)

        if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.PANAREA:
            run_dl_test([slot for slot in pass_nic_list if int(slot) % 2 == 0], "inter_uC_DIAG_IMG_PROG")
            run_dl_test([slot for slot in pass_nic_list if int(slot) % 2 == 1], "inter_uC_DIAG_IMG_PROG")
            run_dl_test(pass_nic_list, "NIC_PWRCYC")
            time.sleep(15)
            run_dl_test(pass_nic_list, "NIC_CTRL_INSTANCE_CPLD_PROPERTY_UPDATE")
            run_dl_test(pass_nic_list, "NIC_TYPE")
            run_dl_test(pass_nic_list, "NIC_INIT")
            run_dl_test(pass_nic_list, "CPLD_PROG")
            run_dl_test(pass_nic_list, "NIC_PWRCYC")
            run_dl_test(pass_nic_list, "NIC_CTRL_INSTANCE_CPLD_PROPERTY_UPDATE")
            run_dl_test(pass_nic_list, "CPLD_VERIFY")
            run_dl_test(pass_nic_list, "FSAFE_CPLD_PROG")
            run_dl_test(pass_nic_list, "NIC_PWRCYC")
            run_dl_test([slot for slot in pass_nic_list if int(slot) % 2 == 0], "uC_DIAG_IMG_PROG_OVERRIDE_FD_DESCRIPTORS")
            run_dl_test([slot for slot in pass_nic_list if int(slot) % 2 == 1], "uC_DIAG_IMG_PROG_OVERRIDE_FD_DESCRIPTORS")
            run_dl_test(pass_nic_list, "NIC_PWRCYC")
            run_dl_test(pass_nic_list, "uC_VERSION_CHK")
            run_dl_test(pass_nic_list, "VULVANO_FOGA_UART_STATS_DUMP")
        else:
            mtp_mgmt_ctrl.cli_log_err("The Pre DL test only for Vulcano based cards!", level=0)

        if MTP_HEALTH_MONITOR:
            mtp_mgmt_ctrl.get_mtp_health_monitor().set_event_status()
            thread_health.join()

        # power off nic
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.cli_log_inf("MTP Pre DL Test Complete", level=0)

        for slot in pass_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

        for slot in fail_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        # err_msg = str(e)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)
        if MTP_HEALTH_MONITOR and 'thread_health' in locals():
            mtp_mgmt_ctrl.get_mtp_health_monitor().set_event_status()
            thread_health.join()

    logfile_close(open_file_track_list)
    return


if __name__ == "__main__":
    main()