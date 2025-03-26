#!/usr/bin/env python3

import sys
import os
import argparse
import re
import traceback

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
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


#### functions for keeping old behavior. these can be eliminated if we move these steps into corresponding libmtp function.
@parallelize.parallel_nic_using_ssh
def dl_diagfw_store(mtp_mgmt_ctrl, slot):
    # keep an copy of diagfw in emmc, just incase we need recover it if mgmt fail and dongle is not available
    # not put DL results to fail even if the copy image to emmc failed.
    dsp = FF_Stage.FF_DL
    qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_diagfw(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_copy_nic_copy_file(slot, qspi_img_file)

@parallelize.parallel_nic_using_ssh
def dl_diagfw_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    qspi_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_diagfw(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_qspi(slot, qspi_img_file)

@parallelize.parallel_nic_using_ssh
def dl_salina_qspi_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    image_path = os.path.dirname(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_qspi_prog_sh_img(mtp_mgmt_ctrl, slot, dsp)["filename"])
    return mtp_mgmt_ctrl.matera_mtp_program_nic_qspi(slot, image_path)

@parallelize.parallel_nic_using_ssh
def dl_salina_swi_qspi_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_SWI
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.POLLARA:
        image_path = os.path.dirname(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.qspi_prog_sh_img["POLLARA-1Q400P"])
    elif nic_type == NIC_Type.LINGUA:
        image_path = os.path.dirname(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.qspi_prog_sh_img["LINGUA-1Q400P"])
    else:
        image_path = os.path.dirname(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_qspi_prog_sh_img(mtp_mgmt_ctrl, slot, dsp)["filename"])
    return mtp_mgmt_ctrl.matera_mtp_program_nic_qspi(slot, image_path)

@parallelize.parallel_nic_using_ssh
def dl_goldfw_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    qspi_gold_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_goldfw(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_qspi(slot, qspi_gold_img_file, True)

@parallelize.parallel_nic_using_ssh
def dl_uboot_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    uboot_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_uboot(mtp_mgmt_ctrl, slot, dsp)["filename"]
    uboot_installer_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.uboot_img["INSTALLER"]
    return mtp_mgmt_ctrl.mtp_program_nic_uboot(slot, uboot_img_file, uboot_installer_file, uboot_pat="boot0")

@parallelize.parallel_nic_using_ssh
def dl_uboota_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    uboot_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_uboota(mtp_mgmt_ctrl, slot, dsp)["filename"]
    uboot_installer_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.uboot_img["INSTALLER"]
    return mtp_mgmt_ctrl.mtp_program_nic_uboot(slot, uboot_img_file, uboot_installer_file, uboot_pat="uboota")

@parallelize.parallel_nic_using_ssh
def dl_ubootb_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    uboot_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_ubootb(mtp_mgmt_ctrl, slot, dsp)["filename"]
    uboot_installer_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.uboot_img["INSTALLER"]
    return mtp_mgmt_ctrl.mtp_program_nic_uboot(slot, uboot_img_file, uboot_installer_file, uboot_pat="ubootb")

@parallelize.parallel_nic_using_ssh
def dl_verify_diagfw(mtp_mgmt_ctrl, slot):
    # need to pass through here, as inner function is called without wrapper elsewhere
    return mtp_mgmt_ctrl.mtp_verify_nic_qspi(slot)

@parallelize.parallel_nic_using_ssh
def dl_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)

@parallelize.parallel_nic_using_ssh
def dl_fail_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_failsafe_cpld(slot, failsafe_cpld_img_file)

@parallelize.parallel_nic_using_ssh
def dl_fea_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    fea_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fea_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_cpld_feature_row(slot, fea_cpld_img_file)

def cpld_running_ver_chk_from_mtp(mtp_mgmt_ctrl, slot):
    # cpld_ver["DSC3-2Q400-48R64E64P"] = "0x1"
    # cpld_dat["DSC3-2Q400-48R64E64P"] = "12-27-24_19:57" #mm-dd-YY_HH:MM

    stage = FF_Stage.FF_DL
    expected_version = image_control.get_cpld(mtp_mgmt_ctrl, slot[0], stage)["version"]
    expected_timestamp = image_control.get_cpld(mtp_mgmt_ctrl, slot[0], stage)["timestamp"]
    expected_date = expected_timestamp.split("_")[0]
    expected_time = expected_timestamp.split("_")[1]
    expected_month = '0x' + expected_date.split("-")[0]
    expected_day = '0x' + expected_date.split("-")[1]
    expected_year = '0x' + expected_date.split("-")[2]
    expected_hour = '0x' + expected_time.split(":")[0]
    expected_minute = '0x' + expected_time.split(":")[1]

    verify_reg_map = {
        '0x00': expected_version,
        '0x94': expected_year,
        '0x93': expected_month,
        '0x92': expected_day,
        '0x91': expected_hour,
        '0x90': expected_minute,
    }

    return mtp_mgmt_ctrl.mtp_i2cget_nic_register(slot, reg_addr2exp_val=verify_reg_map)

@parallelize.parallel_nic_using_ssh
def dl_ufm1_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    ufm1_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_ufm1(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_ufm1(slot, ufm1_img_file)

@parallelize.parallel_nic_using_ssh
def dl_ibm_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_adi_ibm_cpld(slot, cpld_img_file)

@parallelize.parallel_nic_using_ssh
def dl_ibm_fail_cpld_program(mtp_mgmt_ctrl, slot):
    dsp = FF_Stage.FF_DL
    failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, dsp)["filename"]
    return mtp_mgmt_ctrl.mtp_program_nic_adi_ibm_failsafe_cpld(slot, failsafe_cpld_img_file)

@parallelize.parallel_nic_using_ssh
def dl_fru_program(mtp_mgmt_ctrl, slot, swmtestmode):
    sn = mtp_mgmt_ctrl.get_scanned_sn(slot)
    mac = mtp_mgmt_ctrl.get_scanned_mac(slot)
    pn = mtp_mgmt_ctrl.get_scanned_pn(slot)
    dpn = mtp_mgmt_ctrl.get_scanned_dpn(slot)
    prog_date = mtp_mgmt_ctrl.get_scanned_ts(slot)

    ret = mtp_mgmt_ctrl.mtp_program_nic_fru(slot, prog_date, sn, mac, pn, dpn)
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    #skip ALOM programming if Naples25 SWM test mode is SWM only
    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:  
        alom_sn = mtp_mgmt_ctrl.get_scanned_alom_sn(slot)
        alom_pn = mtp_mgmt_ctrl.get_scanned_alom_pn(slot)
        ret = mtp_mgmt_ctrl.mtp_program_nic_alom_fru(slot, prog_date, alom_sn, alom_pn)
    return ret

@parallelize.parallel_nic_using_ssh
def dl_fru_verify(mtp_mgmt_ctrl, slot, swmtestmode):
    sn = mtp_mgmt_ctrl.get_scanned_sn(slot)
    mac = mtp_mgmt_ctrl.get_scanned_mac(slot)
    pn = mtp_mgmt_ctrl.get_scanned_pn(slot)
    dpn = mtp_mgmt_ctrl.get_scanned_dpn(slot)
    prog_date = mtp_mgmt_ctrl.get_scanned_ts(slot)
    exp_sn = sn
    exp_mac = "-".join(re.findall("..", mac))
    exp_pn = pn
    exp_dpn = dpn
    exp_date = prog_date
    alom_sn = None
    alom_pn = None
    exp_alom_sn = None
    exp_alom_pn = None
    exp_assettag = None
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
        alom_sn = mtp_mgmt_ctrl.get_scanned_alom_sn(slot)
        alom_pn = mtp_mgmt_ctrl.get_scanned_alom_pn(slot)
        exp_alom_sn = alom_sn
        exp_alom_pn = alom_pn
        exp_assettag = 'C0'
        hpe_pn = "000000-000"
    ret = mtp_mgmt_ctrl.mtp_verify_nic_fru(slot, exp_sn, exp_mac, exp_pn, exp_date, exp_dpn)
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
        if ret:
            ret = mtp_mgmt_ctrl.mtp_verify_hpe_pn_fru(slot, hpe_pn)
                                                        
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            if ret:
                ret = mtp_mgmt_ctrl.mtp_verify_nic_alom_fru(slot, exp_alom_sn, exp_alom_pn, exp_date)
    return ret

@parallelize.parallel_nic_using_ssh
def dl_parse_ocp_sn(mtp_mgmt_ctrl, slot):
    ret = mtp_mgmt_ctrl.mtp_parse_nic_ocp_fru(slot)
    return ret

@parallelize.parallel_nic_using_ssh
def ocp_rmii_linkup(mtp_mgmt_ctrl, slot):
    ret = mtp_mgmt_ctrl.mtp_ocp_rmii_linkup(slot)
    return ret

@parallelize.parallel_nic_using_ssh
def ocp_connect(mtp_mgmt_ctrl, slot):
    ret = mtp_mgmt_ctrl.mtp_ocp_connect(slot)
    return ret

@parallelize.parallel_nic_using_ssh
def dl_assign_board_id(mtp_mgmt_ctrl, slot):
    pn = mtp_mgmt_ctrl.get_scanned_pn(slot)
    return mtp_mgmt_ctrl.mtp_nic_assign_board_id(slot, pn)

@parallelize.parallel_nic_using_ssh
def salina_erase_qspi(mtp_mgmt_ctrl, slot):
    return mtp_mgmt_ctrl.matera_mtp_erase_nic_qspi(slot)

def health_status(mtp_health):
    mtp_health.monitr_mtp_health(timeout=MTP_Const.MTP_HEALTH_MONITOR_CYCLE)

def main():
    parser = argparse.ArgumentParser(description="MTP DL Test Script", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--dpn", help="Supply Diagnostic Part Number, for QA/lab only...MFG should enter DPN through scanning", default=None)
    parser.add_argument("--skip_test", help="skip a particular test", nargs="*", default=[])
    parser.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("--skip_slots", help="skip a particular slot", nargs="*", default=[])
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    parser.add_argument("--scandl", help="Run ScanDL, i.e. reprogram all NIC FRUs", action='store_true', default=False)

    args = parser.parse_args()
    if args.mtpid:
        mtp_id = args.mtpid

    mtp_cfg_db = load_mtp_cfg(args.mtpcfg)

    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    if not args.skip_test:
        args.skip_test = []

    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, sys.stdout, None, [], skip_slots=args.skip_slots)
    # local logfiles
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=FF_Stage.FF_DL)

    mtp_mgmt_ctrl.cli_log_inf("MTP DL Test Started", level=0)

    try:
        # read scanned barcode file except when we're skipping in dev environment
        scanned_nic_fru_cfg = dict()
        if args.scandl or "SCAN_VERIFY" not in args.skip_test:
            scanning.read_scanned_barcodes(mtp_mgmt_ctrl)
            scanned_nic_fru_cfg = mtp_mgmt_ctrl.barcode_scans

        if args.scandl:
            if not test_utils.mtp_common_setup_scandl(mtp_mgmt_ctrl, FF_Stage.FF_DL, scanned_nic_fru_cfg, args.skip_test):
                mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
                logfile_close(open_file_track_list)
                return
        else:
            if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, FF_Stage.FF_DL, args.skip_test):
                mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
                logfile_close(open_file_track_list)
                return

        if MTP_HEALTH_MONITOR:
            thread_health = threading.Thread(target=health_status, args=(mtp_mgmt_ctrl.get_mtp_health_monitor(),))
            thread_health.start()

        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        fail_nic_list = list()
        pass_nic_list = list()

        # Add failed slots from toplevel
        if args.fail_slots:
            for slot in args.fail_slots:
                fail_nic_list.append(int(slot))

        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if slot in fail_nic_list:
                continue
            if not nic_prsnt_list[slot]:
                continue
            if args.scandl:
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

            if test in args.skip_test:
                test_utils.test_skip_nic_log_message(mtp_mgmt_ctrl, nic_list, stage, test)
                return nic_list

            start_ts = mtp_mgmt_ctrl.log_test_start(test)
            test_utils.test_start_nic_log_message(mtp_mgmt_ctrl, nic_list, stage, test)

            if DRY_RUN:
                rlist = []
            elif test == "SCAN_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_scan_verify(nic_list)
            elif test == "FAKE_SCAN_VERIFY":
                rlist = mtp_mgmt_ctrl.fake_scan_verify(nic_list, scanned_dpn=args.dpn)
            elif test == "DPN_VALIDATE":
                rlist = mtp_mgmt_ctrl.mtp_nic_validate_pn_dpn_match(nic_list)

            elif test == "NIC_POWER":
                rlist = mtp_mgmt_ctrl.mtp_check_nic_list_pwr_status(nic_list, test)
            elif test == "NIC_TYPE":
                rlist = mtp_mgmt_ctrl.mtp_nic_type_test(nic_list)
            elif test == "NIC_INIT":
                rlist = mtp_mgmt_ctrl.mtp_check_nic_list_status(nic_list)
            elif test == "NIC_PRSNT":
                rlist = mtp_mgmt_ctrl.mtp_nic_check_prsnt(nic_list)
            elif test == "NIC_BOOT_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_boot_info_init(nic_list)
            elif test == "CONSOLE_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_nic_diag_boot(nic_list)
            elif test == "CONSOLE_BOOT_INIT":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_nic_console_access(nic_list)
            elif test == "SET_DIAGFW_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_set_nic_diagfw_boot(nic_list)
            elif test == "NIC_BOOT_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_diag_boot(nic_list)
            elif test == "NIC_DIAG_BOOT":
                rlist = mtp_mgmt_ctrl.mtp_nic_check_diag_boot(nic_list)

            elif test == "NIC_PWRCYC":
                rlist = mtp_mgmt_ctrl.mtp_power_cycle_nic(nic_list, dl=True)
            elif test == "NIC_PARA_MGMT_FPO_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_mgmt_para_init_fpo(nic_list)
            elif test == "NIC_DIAG_INIT":
                rlist = mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, skip_test_list=args.skip_test, **test_kwargs)

            elif test == "SET_PSLC":
                rlist = mtp_mgmt_ctrl.mtp_setting_partition(nic_list)
            elif test == "EMMC_HWRESET_SET":
                rlist = mtp_mgmt_ctrl.mtp_nic_emmc_hwreset_set(nic_list)
            elif test == "EMMC_BKOPS_EN":
                rlist = mtp_mgmt_ctrl.mtp_nic_emmc_bkops_en(nic_list)
            elif test == "NIC_FWUPDATE_INIT_EMMC":
                rlist = mtp_mgmt_ctrl.mtp_nic_fwupdate_init_emmc(nic_list)
            elif test == "SALINA_QSPI_ERASE":
                rlist = salina_erase_qspi(mtp_mgmt_ctrl, nic_list)
            elif test == "SALINA_QSPI_PROG":
                rlist = dl_salina_qspi_program(mtp_mgmt_ctrl, nic_list)
            elif test == "SALINA_QSPI_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_power_cycle_boot_stage(nic_list, bootstage=test_kwargs["bootstage"])
            elif test == "SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_power_cycle_boot_stage(nic_list, bootstage=test_kwargs["bootstage"], new_mem_layout=True)
            elif test == "QSPI_PROG":
                rlist = dl_diagfw_program(mtp_mgmt_ctrl, nic_list)
            elif test == "QSPI_GOLD_PROG":
                rlist = dl_goldfw_program(mtp_mgmt_ctrl, nic_list)
            elif test == "SALINA_SWI_QSPI_PROG":
                rlist = dl_salina_swi_qspi_program(mtp_mgmt_ctrl, nic_list)
            elif test == "UBOOT_PROG":
                rlist = dl_uboot_program(mtp_mgmt_ctrl, nic_list)
            elif test == "UBOOTA_PROG":
                rlist = dl_uboota_program(mtp_mgmt_ctrl, nic_list)
            elif test == "UBOOTB_PROG":
                rlist = dl_ubootb_program(mtp_mgmt_ctrl, nic_list)
            elif test == "ERASE_MAINFW":
                rlist = mtp_mgmt_ctrl.mtp_erase_main_fw_partition(nic_list)
            elif test == "DIAGFW_STORE":
                rlist = dl_diagfw_store(mtp_mgmt_ctrl, nic_list)
            elif test == "QSPI_VERIFY":
                rlist = dl_verify_diagfw(mtp_mgmt_ctrl, nic_list)

            elif test == "FRU_PROG":
                rlist = dl_fru_program(mtp_mgmt_ctrl, nic_list, swmtestmode)
            elif test == "FRU_VERIFY":
                rlist = dl_fru_verify(mtp_mgmt_ctrl, nic_list, swmtestmode)
            elif test == "REWORK_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_nic_hpe_rework_verify(nic_list)
            elif test == "OCP_FRU_SN":
                rlist = dl_parse_ocp_sn(mtp_mgmt_ctrl, nic_list)
            elif test == "OCP_RMII":
                rlist = ocp_rmii_linkup(mtp_mgmt_ctrl, nic_list)
            elif test == "OCP_CONN":
                rlist = ocp_connect(mtp_mgmt_ctrl, nic_list)

            elif test == "ASSIGN_BOARD_ID":
                rlist = dl_assign_board_id(mtp_mgmt_ctrl, nic_list)
            elif test == "ASSIGN_BOARDID_PCISUBSYSTEMID_FROM_ZEPHYR":
                rlist = mtp_mgmt_ctrl.mtp_nic_zephyr_boardid_pcisubsystemid_write(nic_list)
            elif test == "CON_ERASE_BOARD_CONFIG":
                rlist = mtp_mgmt_ctrl.mtp_nic_erase_board_config(nic_list)
            elif test == "ERASE_BOARD_CONFIG":
                rlist = mtp_mgmt_ctrl.mtp_nic_erase_board_config_ssh(nic_list)
            elif test == "BOARD_CONFIG":
                rlist = mtp_mgmt_ctrl.mtp_nic_board_config(nic_list)

            elif test == "CPLD_PROG":
                rlist = dl_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "NIC_CTRL_INSTANCE_CPLD_PROPERTY_UPDATE":
                rlist = mtp_mgmt_ctrl.mtp_nic_diag_init_cpld_diag(nic_list, emmc_format=False)
            elif test == "FSAFE_CPLD_PROG":
                rlist = dl_fail_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "FEA_CPLD_PROG":
                rlist = dl_fea_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "UMF1_PROG":
                rlist = dl_ufm1_program(mtp_mgmt_ctrl, nic_list)
            elif test == "CPLD_REF":
                rlist = mtp_mgmt_ctrl.mtp_refresh_nic_cpld(nic_list)
            elif test == "CHECK_CPLD_UPDATE_REQ":
                rlist = mtp_mgmt_ctrl.mtp_nic_cpld_update_request(nic_list)
            elif test == "NOSECURE_CPLD_PROG":
                rlist = dl_ibm_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "NOSECURE_FAILSAFE_CPLD_PROG":
                rlist = dl_ibm_fail_cpld_program(mtp_mgmt_ctrl, nic_list)
            elif test == "CPLD_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_cpld(nic_list)
            elif test == "CPLD_RUNNING_VER_CHK_FROM_MTP":
                rlist = cpld_running_ver_chk_from_mtp(mtp_mgmt_ctrl, nic_list)
            elif test == "FEA_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_cpld_fea(nic_list)
            elif test == "FPGA_PROG":
                rlist = mtp_mgmt_ctrl.mtp_program_nic_fpga(nic_list)
            elif test == "FPGA_PROG_VERIFY":
                rlist = mtp_mgmt_ctrl.mtp_verify_nic_fpga(nic_list)

            elif test == "DISABLE_ESEC_WP":
                rlist = mtp_mgmt_ctrl.mtp_nic_esec_write_protect(nic_list, enable=False)
            elif test == "L1_ESEC_PROG":
                rlist = mtp_mgmt_ctrl.mtp_nic_l1_esecure_prog(nic_list)

            elif test == "FIX_VRM":
                rlist = mtp_mgmt_ctrl.mtp_nic_fix_vrm(nic_list)
            elif test == "VDD_DDR_FIX":
                rlist = mtp_mgmt_ctrl.mtp_nic_vdd_ddr_fix(nic_list)
            elif test == "AVS_SET":
                rlist = mtp_mgmt_ctrl.mtp_mgmt_set_nic_avs(nic_list)

            elif test == "SALINA_SET_PCIEAWD_ENV":
                rlist = mtp_mgmt_ctrl.mtp_set_piceawd_env_salina(nic_list)

            else:
                mtp_mgmt_ctrl.cli_log_err("Unknown test '{:s}'".format(test))
                rlist = nic_list

            # catch bad return value
            if not isinstance(rlist, list):
                mtp_mgmt_ctrl.cli_log_err("Test {} failed with '{}', expected slot list".format(test, repr(rlist)))
                rlist = nic_list[:]

            rlist = list(set(rlist))

            # special pass/fail processing to keep old behavior
            for slot in nic_list:
                if test == "CHECK_CPLD_UPDATE_REQ":
                    if mtp_mgmt_ctrl.mtp_check_nic_status(slot): # not real failure
                        if slot in rlist:
                            rlist.remove(slot)
                elif test == "CONSOLE_BOOT_INIT" or test == "CONSOLE_BOOT":
                    if slot in rlist:
                        # rough way to track failure
                        mtp_mgmt_ctrl.mtp_set_nic_failed_boot(slot)

            for slot in rlist:
                mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot, testname=test)
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

        if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.MATERA:

            # power cycle all nic
            mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)
            run_dl_test(pass_nic_list, "NIC_PWRCYC")

            if not args.scandl:
                if "SCAN_VERIFY" in args.skip_test:
                    # only for QA, fake the scans
                    run_dl_test(pass_nic_list, "FAKE_SCAN_VERIFY")
                else:
                    run_dl_test(pass_nic_list, "SCAN_VERIFY")

            # validate the DPN is allowed for this PN
            dpn_test_nic_list = get_slots_of_type(CTO_MODEL_TYPE_LIST)
            run_dl_test(dpn_test_nic_list, "DPN_VALIDATE")

            for slot in pass_nic_list:
                dl_display_program_matrix(mtp_mgmt_ctrl, slot, swmtestmode)

            # FOR ADI IBM CARDS ONLY
            adi_ibm_reset_list = get_slots_of_type(NIC_Type.ORTANO2ADIIBM)
            run_dl_test(adi_ibm_reset_list, "CONSOLE_BOOT_INIT")
            run_dl_test(adi_ibm_reset_list, "CHECK_CPLD_UPDATE_REQ")
            run_dl_test(adi_ibm_reset_list, "CON_ERASE_BOARD_CONFIG")
            run_dl_test(adi_ibm_reset_list, "NIC_DIAG_INIT", emmc_format=True, emmc_check=True, fru_fpo=True, fru_valid=True if not args.scandl else False)
            run_dl_test(adi_ibm_reset_list, "NOSECURE_CPLD_PROG")
            run_dl_test(adi_ibm_reset_list, "NOSECURE_FAILSAFE_CPLD_PROG")
            run_dl_test(adi_ibm_reset_list, "SET_DIAGFW_BOOT")
            run_dl_test(adi_ibm_reset_list, "NIC_PWRCYC")

            # run_dl_test(pass_nic_list, "CONSOLE_BOOT")
            # if "CONSOLE_BOOT" not in args.skip_test:
            #     run_dl_test(pass_nic_list, "NIC_PWRCYC")

            # run_dl_test(pass_nic_list, "NIC_POWER")        # Not ready for Leni/Leni48G/Malfa
            run_dl_test(pass_nic_list, "NIC_TYPE")
            run_dl_test(pass_nic_list, "NIC_INIT")
            # run_dl_test(pass_nic_list, "NIC_BOOT_VERIFY")    # Not ready for Leni/Leni48G/Malfa

            # record ocp adapter fru
            run_dl_test(get_slots_of_type(NIC_Type.LINGUA), "OCP_FRU_SN")
            run_dl_test(get_slots_of_type(NIC_Type.LINGUA), "OCP_RMII")
            run_dl_test(get_slots_of_type(NIC_Type.LINGUA), "OCP_CONN")

            ## 0. program cpld in first place for Salina Cards Only, not affect rest of program sequence
            cpld_list = get_slots_of_type(SALINA_NIC_TYPE_LIST)
            run_dl_test(cpld_list, "UMF1_PROG")
            ecpld_list = get_slots_of_type(SALINA_NIC_TYPE_LIST)
            run_dl_test(cpld_list, "CPLD_PROG")
            cpld_list = get_slots_of_type(SALINA_NIC_TYPE_LIST)
            run_dl_test(ecpld_list, "FSAFE_CPLD_PROG")
            # run_dl_test(ecpld_list, "FEA_CPLD_PROG")
            run_dl_test(ecpld_list, "NIC_PWRCYC")
            chk_ver_list = get_slots_of_type(SALINA_NIC_TYPE_LIST)
            if len(chk_ver_list) > 0:
                run_dl_test(chk_ver_list, "CPLD_RUNNING_VER_CHK_FROM_MTP")

            # program the qspi, before initializing emmc
            ## 1. setup mgmt
            smart_nic_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=SALINA_NIC_TYPE_LIST)
            run_dl_test(smart_nic_list, "NIC_PARA_MGMT_FPO_INIT")
            run_dl_test(smart_nic_list, "NIC_BOOT_INIT")

            avs_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=ADI_VRM_TYPE_LIST)
            run_dl_test(avs_list, "AVS_SET")
            ## 2. program fw
            # non_cap_nic_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=CAPRI_NIC_TYPE_LIST)
            # run_dl_test(non_cap_nic_list, "ERASE_MAINFW")
            # run_dl_test(pass_nic_list, "QSPI_PROG")   # Not Support diagfw for Leni/Leni48G/Malfa
            # uboot_prog_nic_list = get_slots_of_type(ELBA_NIC_TYPE_LIST, except_type=[NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT])
            # run_dl_test(uboot_prog_nic_list, "UBOOT_PROG")
            # run_dl_test(get_slots_of_type(NIC_Type.ORTANO2ADIIBM), "UBOOTA_PROG")
            # run_dl_test(get_slots_of_type(NIC_Type.ORTANO2ADIIBM), "UBOOTB_PROG")
            # qspi_gold_nic_list = get_slots_of_type([NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4])
            # run_dl_test(qspi_gold_nic_list, "QSPI_GOLD_PROG")
            run_dl_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "SALINA_QSPI_ERASE")
            run_dl_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_QSPI_PROG")
            run_dl_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_SWI_QSPI_PROG")
            run_dl_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY", bootstage="linux")
            run_dl_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY", bootstage="zephyr")

            # ## 2a. Prog FRU before enableOOB for Salina
            run_dl_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "FRU_PROG")
            run_dl_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "FIX_VRM")

            # ## 2b. set emmc settings for elba
            run_dl_test(get_slots_of_type(SALINA_DPU_NIC_TYPE_LIST), "SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY", bootstage="linux")
            run_dl_test(get_slots_of_type(SALINA_NIC_TYPE_LIST, except_type=SALINA_AI_NIC_TYPE_LIST), "NIC_PARA_MGMT_FPO_INIT")
            run_dl_test(get_slots_of_type(SALINA_NIC_TYPE_LIST, except_type=SALINA_AI_NIC_TYPE_LIST), "NIC_BOOT_INIT")
            run_dl_test(get_slots_of_type(PSLC_MODE_TYPE_LIST), "SET_PSLC")
            run_dl_test(get_slots_of_type(PSLC_MODE_TYPE_LIST), "EMMC_HWRESET_SET")
            run_dl_test(get_slots_of_type(PSLC_MODE_TYPE_LIST), "EMMC_BKOPS_EN")
            run_dl_test(get_slots_of_type(PSLC_MODE_TYPE_LIST), "NIC_FWUPDATE_INIT_EMMC")

            # run_dl_test(pass_nic_list, "NIC_DIAG_INIT", emmc_format=True, emmc_check=True, fru_fpo=True, fru_valid=True if not args.scandl else False)

            ## 3. program fru, board settings
            # run_dl_test(pass_nic_list, "QSPI_VERIFY")
            vrmfix_list = get_slots_of_type((NIC_Type.ORTANO2, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOS4))
            run_dl_test(vrmfix_list, "FIX_VRM")
            # vddrfix_list = get_slots_of_type([NIC_Type.ORTANO2, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOS4, NIC_Type.POMONTEDELL] + GIGLIO_NIC_TYPE_LIST)
            # run_dl_test(vddrfix_list, "VDD_DDR_FIX")
            run_dl_test(get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=SALINA_NIC_TYPE_LIST), "FRU_PROG")
            # erase_brdcfg_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST)
            # run_dl_test(erase_brdcfg_list, "ERASE_BOARD_CONFIG")
            run_dl_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "NIC_CTRL_INSTANCE_CPLD_PROPERTY_UPDATE")
            run_dl_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY", bootstage="zephyr")
            run_dl_test(get_slots_of_type(SALINA_NIC_TYPE_LIST), "ASSIGN_BOARDID_PCISUBSYSTEMID_FROM_ZEPHYR")
            # brd_config_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST)
            # run_dl_test(brd_config_list, "BOARD_CONFIG")

            run_dl_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_QSPI_ERASE")
            run_dl_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_QSPI_PROG")
            run_dl_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_QSPI_VERIFY", bootstage="zephyr")
            ## 4. program cpld
            ################## Done########################################
            # fpga_list = get_slots_of_type(FPGA_TYPE_LIST)
            # run_dl_test(fpga_list, "FPGA_PROG")
            cpld_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST+SALINA_NIC_TYPE_LIST)
            run_dl_test(cpld_list, "UMF1_PROG")
            cpld_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST+SALINA_NIC_TYPE_LIST)
            run_dl_test(cpld_list, "CPLD_PROG")
            ecpld_list = get_slots_of_type(FAILSAFE_CPLD_TYPE_LIST, except_type=SALINA_NIC_TYPE_LIST)
            run_dl_test(ecpld_list, "FSAFE_CPLD_PROG")

            # run_dl_test(get_slots_of_type(SALINA_AI_NIC_TYPE_LIST), "SALINA_SET_PCIEAWD_ENV")
            # run_dl_test(ecpld_list, "FEA_CPLD_PROG")
            # cpld_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST + [NIC_Type.NAPLES25OCP])
            # run_dl_test(cpld_list, "CPLD_REF")
            ################## Done########################################
            # ## 5. flash asic esecure fw
            # non_capri_type_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST)
            # run_dl_test(non_capri_type_list, "DISABLE_ESEC_WP")

            # ## 6. verify everything
            # run_dl_test(pass_nic_list, "NIC_DIAG_INIT")

            # non_ibm_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=NIC_Type.NAPLES100IBM)
            # run_dl_test(non_ibm_list, "NIC_POWER")
            # run_dl_test(pass_nic_list, "NIC_PRSNT")
            # run_dl_test(pass_nic_list, "NIC_DIAG_BOOT")
            # run_dl_test(pass_nic_list, "FRU_VERIFY")
            # hpeswm_nic_list = get_slots_of_type(NIC_Type.NAPLES25SWM)
            # run_dl_test(hpeswm_nic_list, "REWORK_VERIFY")
            # run_dl_test(pass_nic_list, "CPLD_VERIFY")
            # run_dl_test(pass_nic_list, "DIAGFW_STORE")
            # ecpld_list = get_slots_of_type(FAILSAFE_CPLD_TYPE_LIST)
            # run_dl_test(ecpld_list, "FEA_VERIFY")
            # fpga_list = get_slots_of_type(FPGA_TYPE_LIST)
            # run_dl_test(fpga_list, "FPGA_PROG_VERIFY")
            # esec_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST)
            # run_dl_test(esec_list, "L1_ESEC_PROG")

        else:
            # power cycle all nic
            mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)
            run_dl_test(pass_nic_list, "NIC_PWRCYC")

            if not args.scandl:
                if "SCAN_VERIFY" in args.skip_test:
                    # only for QA, fake the scans
                    run_dl_test(pass_nic_list, "FAKE_SCAN_VERIFY")
                else:
                    run_dl_test(pass_nic_list, "SCAN_VERIFY")

            # validate the DPN is allowed for this PN
            dpn_test_nic_list = get_slots_of_type(CTO_MODEL_TYPE_LIST)
            run_dl_test(dpn_test_nic_list, "DPN_VALIDATE")

            for slot in pass_nic_list:
                dl_display_program_matrix(mtp_mgmt_ctrl, slot, swmtestmode)

            # FOR ADI IBM CARDS ONLY
            adi_ibm_reset_list = get_slots_of_type(NIC_Type.ORTANO2ADIIBM)
            run_dl_test(adi_ibm_reset_list, "CONSOLE_BOOT_INIT")
            run_dl_test(adi_ibm_reset_list, "CHECK_CPLD_UPDATE_REQ")
            run_dl_test(adi_ibm_reset_list, "CON_ERASE_BOARD_CONFIG")
            run_dl_test(adi_ibm_reset_list, "NIC_DIAG_INIT", emmc_format=True, emmc_check=True, fru_fpo=True, fru_valid=True if not args.scandl else False)
            run_dl_test(adi_ibm_reset_list, "NOSECURE_CPLD_PROG")
            run_dl_test(adi_ibm_reset_list, "NOSECURE_FAILSAFE_CPLD_PROG")
            run_dl_test(adi_ibm_reset_list, "SET_DIAGFW_BOOT")
            run_dl_test(adi_ibm_reset_list, "NIC_PWRCYC")

            run_dl_test(pass_nic_list, "CONSOLE_BOOT")
            if "CONSOLE_BOOT" not in args.skip_test:
                run_dl_test(pass_nic_list, "NIC_PWRCYC")

            run_dl_test(pass_nic_list, "NIC_POWER")
            run_dl_test(pass_nic_list, "NIC_TYPE")
            run_dl_test(pass_nic_list, "NIC_INIT")
            run_dl_test(pass_nic_list, "NIC_BOOT_VERIFY")

            # program the qspi, before initializing emmc
            ## 1. setup mgmt
            run_dl_test(pass_nic_list, "NIC_PARA_MGMT_FPO_INIT")
            run_dl_test(pass_nic_list, "NIC_BOOT_INIT")

            ## 2. program fw
            non_cap_nic_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=CAPRI_NIC_TYPE_LIST)
            run_dl_test(non_cap_nic_list, "ERASE_MAINFW")
            run_dl_test(pass_nic_list, "QSPI_PROG")
            uboot_prog_nic_list = get_slots_of_type(ELBA_NIC_TYPE_LIST, except_type=[NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT])
            run_dl_test(uboot_prog_nic_list, "UBOOT_PROG")
            run_dl_test(get_slots_of_type(NIC_Type.ORTANO2ADIIBM), "UBOOTA_PROG")
            run_dl_test(get_slots_of_type(NIC_Type.ORTANO2ADIIBM), "UBOOTB_PROG")
            qspi_gold_nic_list = get_slots_of_type([NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4])
            run_dl_test(qspi_gold_nic_list, "QSPI_GOLD_PROG")

            ## 2b. set emmc settings for elba
            run_dl_test(get_slots_of_type(PSLC_MODE_TYPE_LIST), "SET_PSLC")
            run_dl_test(get_slots_of_type(PSLC_MODE_TYPE_LIST), "EMMC_HWRESET_SET")
            run_dl_test(get_slots_of_type(PSLC_MODE_TYPE_LIST), "EMMC_BKOPS_EN")

            run_dl_test(pass_nic_list, "NIC_DIAG_INIT", emmc_format=True, emmc_check=True, fru_fpo=True, fru_valid=True if not args.scandl else False)

            ## 3. program fru, board settings
            run_dl_test(pass_nic_list, "QSPI_VERIFY")
            vrmfix_list = get_slots_of_type((NIC_Type.ORTANO2, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOS4))
            run_dl_test(vrmfix_list, "FIX_VRM")
            vddrfix_list = get_slots_of_type([NIC_Type.ORTANO2, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOS4, NIC_Type.POMONTEDELL] + GIGLIO_NIC_TYPE_LIST)
            run_dl_test(vddrfix_list, "VDD_DDR_FIX")
            run_dl_test(pass_nic_list, "FRU_PROG")
            erase_brdcfg_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST)
            run_dl_test(erase_brdcfg_list, "ERASE_BOARD_CONFIG")
            assign_boardid_list = get_slots_of_type(GIGLIO_NIC_TYPE_LIST + [NIC_Type.ORTANO2ADICRS4])
            run_dl_test(assign_boardid_list, "ASSIGN_BOARD_ID")
            brd_config_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST)
            run_dl_test(brd_config_list, "BOARD_CONFIG")

            ## 4. program cpld
            fpga_list = get_slots_of_type(FPGA_TYPE_LIST)
            run_dl_test(fpga_list, "FPGA_PROG")
            cpld_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST)
            run_dl_test(cpld_list, "CPLD_PROG")
            ecpld_list = get_slots_of_type(FAILSAFE_CPLD_TYPE_LIST)
            run_dl_test(ecpld_list, "FSAFE_CPLD_PROG")
            run_dl_test(ecpld_list, "FEA_CPLD_PROG")
            cpld_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=FPGA_TYPE_LIST + [NIC_Type.NAPLES25OCP])
            run_dl_test(cpld_list, "CPLD_REF")

            ## 5. flash asic esecure fw
            non_capri_type_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST)
            run_dl_test(non_capri_type_list, "DISABLE_ESEC_WP")

            ## 6. verify everything
            run_dl_test(pass_nic_list, "NIC_DIAG_INIT")

            non_ibm_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=NIC_Type.NAPLES100IBM)
            run_dl_test(non_ibm_list, "NIC_POWER")
            run_dl_test(pass_nic_list, "NIC_PRSNT")
            run_dl_test(pass_nic_list, "NIC_DIAG_BOOT")
            run_dl_test(pass_nic_list, "FRU_VERIFY")
            hpeswm_nic_list = get_slots_of_type(NIC_Type.NAPLES25SWM)
            run_dl_test(hpeswm_nic_list, "REWORK_VERIFY")
            run_dl_test(pass_nic_list, "CPLD_VERIFY")
            run_dl_test(pass_nic_list, "DIAGFW_STORE")
            ecpld_list = get_slots_of_type(FAILSAFE_CPLD_TYPE_LIST)
            run_dl_test(ecpld_list, "FEA_VERIFY")
            fpga_list = get_slots_of_type(FPGA_TYPE_LIST)
            run_dl_test(fpga_list, "FPGA_PROG_VERIFY")
            esec_list = get_slots_of_type(ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST)
            run_dl_test(esec_list, "L1_ESEC_PROG")
            avs_list = get_slots_of_type(MFG_VALID_NIC_TYPE_LIST, except_type=ADI_VRM_TYPE_LIST)
            run_dl_test(avs_list, "AVS_SET")

        if MTP_HEALTH_MONITOR:
            mtp_mgmt_ctrl.get_mtp_health_monitor().set_event_status()
            thread_health.join()

        # power off nic
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.cli_log_inf("MTP DL Test Complete", level=0)

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