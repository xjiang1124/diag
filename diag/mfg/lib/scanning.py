import sys, os, re
from libdefs import Swm_Test_Mode
from libdefs import MTP_DIAG_Logfile
from libdefs import FF_Stage
from libsku_utils import PART_NUMBERS_MATCH
from barcode_field import *
import libmfg_utils
import testlog

def mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, stage, skip_scan_list=[], swmtestmode=Swm_Test_Mode.SW_DETECT):
    mtp_mgmt_ctrl.cli_log_inf("Start the Barcode Scan Process", level=0)

    while True:
        scan_rslt = inner_mtp_barcode_scan(mtp_mgmt_ctrl, stage, skip_scan_list, swmtestmode)
        if scan_rslt:
            break;
        mtp_mgmt_ctrl.cli_log_inf("Restart the Barcode Scan Process", level=0)

    cli_log_scan_summary(mtp_mgmt_ctrl, scan_rslt)

    # Save to file so it can copied to MTP
    logfile_dir = testlog.get_mtp_test_log_folder(mtp_mgmt_ctrl)
    scan_cfg_file = logfile_dir + MTP_DIAG_Logfile.SCAN_BARCODE_FILE
    gen_barcode_config_file(mtp_mgmt_ctrl, scan_cfg_file, scan_rslt)

    ## also save the scans into mtp object
    if not read_scanned_barcodes(mtp_mgmt_ctrl):
        return False

def validate_nic_slot_scan(mtp_mgmt_ctrl, usr_input, mtp_scan_rslt):
    if usr_input in mtp_scan_rslt.keys():
        mtp_mgmt_ctrl.cli_log_err("NIC ID Barcode: {:s} is double scanned, please restart the scan process\n".format(usr_input), level=0)
        return None
    if not re.match("NIC-((0[1-9])|(10))", usr_input):
        mtp_mgmt_ctrl.cli_log_err("Invalid NIC ID: {:s}".format(usr_input), level=0)
        return None
    mtp_scan_rslt[usr_input] = dict()
    mtp_scan_rslt[usr_input]["VALID"] = False
    return usr_input

def validate_sn(usr_input):
    return libmfg_utils.serial_number_validate(usr_input)

def validate_mac(usr_input):
    return libmfg_utils.mac_address_validate(usr_input)

def validate_pn(usr_input):
    return libmfg_utils.part_number_validate(usr_input)

def validate_swpn(usr_input):
    if re.match("90-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}", usr_input):
        return usr_input
    return None

def validate_rot_sn(usr_input):
    return libmfg_utils.rot_cable_serial_number_validate(usr_input)

def validate_dpn(usr_input):
    return usr_input in libmfg_utils.get_all_valid_dpn()

def validate_sku(usr_input):
    return usr_input in libmfg_utils.get_all_valid_sku()

def handle_scan(mtp_mgmt_ctrl, scan_item_str, usr_input, already_scanned_list):
    scan_item_to_validation_func = {
        SN:      validate_sn,
        PN:      validate_pn,
        MAC:     validate_mac,
        DPN:     validate_dpn,
        SWPN:    validate_swpn,
        SKU:     validate_sku,
        ALOM_SN: validate_sn,
        ALOM_PN: validate_pn,
        ROT_SN:  validate_rot_sn,
    }
    validation_func = scan_item_to_validation_func.get(scan_item_str)
    if validation_func(usr_input):
        if usr_input not in already_scanned_list:
            return True
        elif usr_input in already_scanned_list and ("Part Number" in scan_item_str or "PN" in scan_item_str or scan_item_str == SKU): #pns are not unique
            return True
        else:
            mtp_mgmt_ctrl.cli_log_err("{:s}: {:s} is double scanned, please rescan".format(scan_item_str, usr_input))
            return False
    # elif usr_input == "KEEP":
    #     # TODO
    #     return True
    else:
        mtp_mgmt_ctrl.cli_log_err("Invalid {:s}: {:s} detected, please rescan".format(scan_item_str, usr_input))
        return False

def inner_mtp_barcode_scan(mtp_mgmt_ctrl, stage, skip_scan_list=[], swmtestmode=Swm_Test_Mode.SW_DETECT):
    """
        Two portions: 
        first, scan items that are always asked: SN, MAC, PN* -- PN is static but dynamic for Dell PPID
        second, scan dynamically decided items based on previously entered fields: e.g. SKU, DPN, SWPN
    """

    mtp_scan_rslt = dict()
    mtp_scan_rslt["MTP_ID"] = mtp_mgmt_ctrl._id
    mtp_scan_rslt["MTP_TS"] = libmfg_utils.get_timestamp()
    already_scanned_list = list()

    while True:
        #### SLOT BARCODE SCAN LOOP
        usr_prompt = "Please scan NIC ID barcode: "
        usr_input = keyboard_input(usr_prompt)
        if usr_input == "STOP":
            break
        else:
            slot = validate_nic_slot_scan(mtp_mgmt_ctrl, usr_input, mtp_scan_rslt)
        if slot is None:
            continue

        scan_item_list = [SN, MAC, PN, DPN, SKU, ROT_SN]
        if swmtestmode == Swm_Test_Mode.ALOM:
            scan_item_list = [ALOM_SN, ALOM_PN]

        for scan_item in scan_item_list:
            if scan_item in skip_scan_list:
                continue

            ####### conditional test selection
            if scan_item == PN:
                if libmfg_utils.dell_ppid_validate(mtp_scan_rslt[slot][SN]):
                    # it's Dell PPID, already part of SN, dont need to scan PN
                    raw_scan = mtp_scan_rslt[slot][SN]
                    mtp_scan_rslt[slot][SN] = libmfg_utils.extract_sn_from_dell_ppid(raw_scan)
                    mtp_scan_rslt[slot][PN] = libmfg_utils.extract_pn_from_dell_ppid(raw_scan)
                    continue

            if scan_item == DPN:
                if stage != FF_Stage.FF_DL:
                    continue
                if not re.match(PART_NUMBERS_MATCH.GINESTRA_S4_PN_FMT, mtp_scan_rslt[slot][PN]) and not mtp_scan_rslt[slot][PN].startswith("102-"):
                    continue

            if scan_item == SKU:
                if stage not in (FF_Stage.FF_SWI, FF_Stage.FF_FST):
                    continue
                if not re.match(PART_NUMBERS_MATCH.GINESTRA_S4_PN_FMT, mtp_scan_rslt[slot][PN]) and not mtp_scan_rslt[slot][PN].startswith("102-"):
                    continue

            if scan_item == SWPN:
                if stage != FF_Stage.FF_SWI:
                    continue
                if re.match(PART_NUMBERS_MATCH.GINESTRA_S4_PN_FMT, mtp_scan_rslt[slot][PN]) and not mtp_scan_rslt[slot][PN].startswith("102-"):
                    continue

            if scan_item == ROT_SN:
                if stage != FF_Stage.FF_FST:
                    continue
                if not libmfg_utils.part_number_match_rot_require_list(mtp_scan_rslt[slot][PN]):
                    continue
            ###################################

            # scan item loop
            while True:
                usr_prompt = "Please scan {:s} {:s} Barcode: ".format(slot, scan_item)
                usr_input = keyboard_input(usr_prompt)
                if handle_scan(mtp_mgmt_ctrl, scan_item, usr_input, already_scanned_list):
                    mtp_scan_rslt[slot][scan_item] = usr_input
                    already_scanned_list.append(usr_input)
                    break
                else:
                    continue

        mtp_scan_rslt[slot]["VALID"] = True
        mtp_scan_rslt[slot]["TS"] = libmfg_utils.get_fru_date()

    # initialize remaining slots as empty
    for slot in range(mtp_mgmt_ctrl._slots):
        key = libmfg_utils.nic_key(slot)
        if key not in mtp_scan_rslt.keys():
            mtp_scan_rslt[key] = dict()
            mtp_scan_rslt[key]["VALID"] = False

    return mtp_scan_rslt

def mtp_screen_barcode_scan(mtp_mgmt_ctrl):
    mtp_scan_rslt = dict()
    mtp_ts_snapshot = libmfg_utils.get_timestamp()
    mtp_scan_rslt["MTP_ID"] = mtp_mgmt_ctrl._id
    mtp_scan_rslt["MTP_TS"] = mtp_ts_snapshot
    mtp_scan_rslt["VALID"] = False
    scan_sn_list = list()

    sn = ""
    sn_scanned = False
    mac_scanned = False
    while True:
        while not sn_scanned:
            usr_prompt = "Please Scan {:s} Serial Number Barcode: ".format(mtp_mgmt_ctrl._id)
            raw_scan = input(usr_prompt)
            if raw_scan == "STOP":
                break
            sn = libmfg_utils.serial_number_validate(raw_scan)

            if not sn:
                mtp_mgmt_ctrl.cli_log_err("Invalid MTP Serial Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                #return None
            elif sn in scan_sn_list:
                mtp_mgmt_ctrl.cli_log_err("MTP Serial Number: {:s} is double scanned, please restart the scan process\n".format(sn), level=0)
                #return None
            else:
                scan_sn_list.append(sn)
                sn_scanned = True
                mtp_scan_rslt["VALID"] = True
    
        mtp_scan_rslt["MTP_SN"] = sn

        while not mac_scanned:
            usr_prompt = "Please Scan {:s} MAC Address Barcode: ".format(mtp_mgmt_ctrl._id)
            raw_scan = input(usr_prompt)
            if raw_scan in scan_sn_list:
                mtp_mgmt_ctrl.cli_log_err("MTP MAC Address: {:s} is double scanned, please restart the scan process\n".format(raw_scan), level=0)
            else:
                scan_sn_list.append(raw_scan)
                mtp_scan_rslt["MTP_MAC"] = raw_scan
                mac_scanned = True

        if sn_scanned and mac_scanned:
            break

    return mtp_scan_rslt

def cli_log_scan_summary(mtp_mgmt_ctrl, scan_rslt):
    pass_rslt_list = list()
    fail_rslt_list = list()
    mtp_id = mtp_mgmt_ctrl._id
    # print scan summary
    for slot in range(mtp_mgmt_ctrl._slots):
        key = libmfg_utils.nic_key(slot)
        nic_cli_id_str = libmfg_utils.id_str(mtp = mtp_id, nic = slot)
        if scan_rslt[key]["VALID"]:
            valid_display_string = nic_cli_id_str
            for item in scan_rslt[key].keys():
                if item == "VALID": continue # dont need to display
                if item == "TS": continue # dont need to display
                valid_display_string += "{:s} = {:s}; ".format(item, scan_rslt[key][item])
            pass_rslt_list.append(valid_display_string)
        else:
            fail_rslt_list.append(nic_cli_id_str + "NIC Absent")
    libmfg_utils.cli_log_rslt("Barcode Scan Summary", pass_rslt_list, fail_rslt_list, mtp_mgmt_ctrl._filep)

def gen_barcode_config_file(mtp_mgmt_ctrl, file_p, scan_rslt):
    if not libmfg_utils.save_cfg_to_yaml(scan_rslt, file_p):
        mtp_mgmt_ctrl.cli_log_err("Failed to save Barcode scans to file", level=0)
        return False
    return True

def read_scanned_barcodes(mtp_mgmt_ctrl):
    # load the barcode config file made earlier
    mtp_id = mtp_mgmt_ctrl._id
    tlf = testlog.get_mtp_test_log_folder(mtp_mgmt_ctrl)
    scan_cfg_file = os.path.join(tlf, MTP_DIAG_Logfile.SCAN_BARCODE_FILE)
    scanned_fru_cfg_dict = libmfg_utils.load_cfg_from_yaml(scan_cfg_file)
    # basic check
    try:
        if mtp_id not in scanned_fru_cfg_dict["MTP_ID"]:
            mtp_mgmt_ctrl.cli_log_err("Not found information for MTP: {:s} in scan config file {:s}".format(mtp_id, scan_cfg_file), level=0)
            return False
    except KeyError:
        mtp_mgmt_ctrl.cli_log_err("Barcode scan file badly formatted, missing MTP", level=0)
    mtp_mgmt_ctrl.barcode_scans = scanned_fru_cfg_dict
    return True

def keyboard_input(prompt):
    # Support python2 and 3 compatability
    # try: input = raw_input
    # except NameError: pass

    return input(prompt)

# API to mtp functions
def retrieve_field(barcode_scans_dict, slot, field):
    key = libmfg_utils.nic_key(slot)
    if key not in barcode_scans_dict.keys():
        return None
    if field not in barcode_scans_dict[key].keys():
        return ""
    return barcode_scans_dict[key][field]

def get_sn(mtp_mgmt_ctrl, slot):
    return retrieve_field(mtp_mgmt_ctrl.barcode_scans, slot, SN)

def get_mac(mtp_mgmt_ctrl, slot):
    return retrieve_field(mtp_mgmt_ctrl.barcode_scans, slot, MAC)

def get_pn(mtp_mgmt_ctrl, slot):
    return retrieve_field(mtp_mgmt_ctrl.barcode_scans, slot, PN)

def get_alom_sn(mtp_mgmt_ctrl, slot):
    return retrieve_field(mtp_mgmt_ctrl.barcode_scans, slot, ALOM_SN)

def get_alom_pn(mtp_mgmt_ctrl, slot):
    return retrieve_field(mtp_mgmt_ctrl.barcode_scans, slot, ALOM_PN)

def get_rot_sn(mtp_mgmt_ctrl, slot):
    return retrieve_field(mtp_mgmt_ctrl.barcode_scans, slot, ROT_SN)

def get_dpn(mtp_mgmt_ctrl, slot):
    return retrieve_field(mtp_mgmt_ctrl.barcode_scans, slot, DPN)

def get_swpn(mtp_mgmt_ctrl, slot):
    return retrieve_field(mtp_mgmt_ctrl.barcode_scans, slot, SWPN)

def get_sku(mtp_mgmt_ctrl, slot):
    return retrieve_field(mtp_mgmt_ctrl.barcode_scans, slot, SKU)

def get_ts(mtp_mgmt_ctrl, slot):
    return retrieve_field(mtp_mgmt_ctrl.barcode_scans, slot, "TS")