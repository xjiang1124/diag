import sys, os, re

sys.path.append(os.path.relpath("../../lib"))
import libtest_config
import libmfg_utils
from libsku_utils import *

param_cfg = libtest_config.parse_config("lib/tests/barcode/parameters.yaml")

# Field display names
SYS_SN = "CHASSIS Serial Number"
SYS_PN = "CHASSIS Part Number"
MAC    = "MAC Address"
CPU_SN = "CPU Serial Number"
CPU_PN = "CPU Part Number"
SWI_SN = "SWITCH Serial Number"
SWI_PN = "SWITCH Part Number"
BMC_SN = "BMC Serial Number"
BMC_PN = "BMC Part Number"


def handle_uut_id_scan(usr_input, uut_scan_rslt, valid_uut_list):
    if usr_input in uut_scan_rslt.keys():
        libmfg_utils.cli_err("UUT ID Barcode: {:s} is double scanned, please restart the scan process\n".format(usr_input))
        return None
    if usr_input in valid_uut_list:
        return usr_input
    elif len(valid_uut_list) == 0:
        return usr_input
    elif usr_input not in valid_uut_list:
        libmfg_utils.cli_err("UUT ID Barcode: {:s} not found in config".format(usr_input))
        return None
    else:
        return None

def part_number_validate(tmp, dev):
    if dev == "SWITCH":
        pn_format = PART_NUMBERS_MATCH.LIPARI_SWI_PN
    elif dev == "BMC":
        pn_format = PART_NUMBERS_MATCH.LIPARI_BMC_PN
    elif dev == "SYSTEM":
        pn_format = PART_NUMBERS_MATCH.LIPARI_SYS_PN
    else:
        pn_format = PART_NUMBERS_MATCH.LIPARI_CPU_PN

    match = re.match(pn_format, tmp)
    if match:
        matchg = match.group(0)
    else:
        return None

    if matchg == tmp:
        # check no truncation happened during regex match
        return tmp
    else:
        return None

def cpu_pn_validate(tmp):
    return part_number_validate(tmp, "CPU")

def swi_pn_validate(tmp):
    return part_number_validate(tmp, "SWITCH")

def bmc_pn_validate(tmp):
    return part_number_validate(tmp, "BMC")

def sys_pn_validate(tmp):
    return part_number_validate(tmp, "SYSTEM")

def mac_address_validate(tmp):
    if re.match(PEN_MAC_NO_DASHES_FMT, tmp) and (len(tmp) == 12):
        return tmp
    else:
        return None

def serial_number_validate(buf, dev="CPU", exact_match=True):
    """
        This is a "LOOSE" validation compared to libnic_ctrl::nic_fru_validate_sn().
        Check that the 'buf' containing serial number matches *ANY* of the rules.
        If exact_match=True, 'buf' must contain whole serial number and nothing else.
    """
    all_sn_regexes = [p[s] for p in SN_FORMAT_TABLE.values() for s in p] # flatten dict
    for sn_regex in all_sn_regexes:
        if exact_match:
            match = re.match(sn_regex, buf)
            if match:
                if match.group(0) == buf:
                    # check no truncation happened during regex match
                    return buf
                else:
                    return None
        else:
            if dev == "SYSTEM" or dev == "ELBA":
                disp_field = "Serial Number"
            else:
                disp_field = "PCBA Serial Number"
            sn_disp_regex = r"%s +(%s)" % (disp_field, sn_regex)
            match = re.findall(sn_disp_regex, buf)
            if match:
                return match[0]

    return None

def handle_scan(scan_item_str, usr_input, scanned_list):
    scan_item_to_validation_func = {
        SYS_SN: serial_number_validate,
        SYS_PN: sys_pn_validate,
        MAC:    mac_address_validate,
        CPU_SN: serial_number_validate,
        CPU_PN: cpu_pn_validate,
        SWI_SN: serial_number_validate,
        SWI_PN: swi_pn_validate,
        BMC_SN: serial_number_validate,
        BMC_PN: bmc_pn_validate
    }
    validation_func = scan_item_to_validation_func.get(scan_item_str)
    if validation_func(usr_input):
        if usr_input not in scanned_list:
            return True
        elif usr_input in scanned_list and ("Part Number" in scan_item_str): #pns are not unique
            return True
        else:
            libmfg_utils.cli_err("UUT {:s}: {:s} is double scanned, please rescan".format(scan_item_str, usr_input))
            return False
    elif usr_input == "KEEP":
        return True
    else:
        libmfg_utils.cli_err("Invalid {:s}: {:s} detected, please rescan".format(scan_item_str, usr_input))
        return False


def uut_barcode_scan(valid_uut_list=[]):
    uut_scan_rslt = dict()
    already_scanned_list  = list()
    while True:
        # STEP 1: Scan UUT-XXX
        uut_id = None
        usr_prompt = "Please scan UUT ID barcode: "
        usr_input = input(usr_prompt)

        if usr_input == "STOP":
            break
        else:
            uut_id = handle_uut_id_scan(usr_input, uut_scan_rslt, valid_uut_list)
        if uut_id is None:
            libmfg_utils.cli_err("Invalid UUT ID: {:s}".format(usr_input))
            continue

        uut_scan_rslt[uut_id] = dict()
        usr_prompt_prefix = libmfg_utils.id_str(mtp = uut_id)

        # STEPS 2-4: Scan SN, MAC, PN, etc
        scan_item_list = [
            SYS_SN,
            SYS_PN,
            MAC,
            CPU_SN,
            CPU_PN,
            SWI_SN,
            SWI_PN
            # BMC_SN,
            # BMC_PN
        ]
        for scan_item in scan_item_list:
            while True:
                usr_prompt = usr_prompt_prefix + "Please scan {:s} {:s} barcode: ".format(uut_id, scan_item)
                usr_input = input(usr_prompt)
                if handle_scan(scan_item, usr_input, already_scanned_list):
                    uut_scan_rslt[uut_id][scan_item] = usr_input
                    already_scanned_list.append(usr_input)
                    break
                else:
                    continue

        # remove ':' in entered MAC address
        if re.match(r"([0-9a-fA-F]{2}.){5}[0-9a-fA-F]{2}", uut_scan_rslt[uut_id][MAC]):
            uut_scan_rslt[uut_id][MAC] = libmfg_utils.mac_address_remove_separator(uut_scan_rslt[uut_id][MAC])

        uut_scan_rslt[uut_id]["UUT_VALID"] = True
        uut_scan_rslt[uut_id]["UUT_ID"]  = uut_id
        uut_scan_rslt[uut_id]["UUT_TS"]  = libmfg_utils.get_fru_date()

    return uut_scan_rslt


def load_barcode_file(barcode_file, valid_uut_list=[]):
    yaml_config = libmfg_utils.load_cfg_from_yaml(barcode_file)

    for uut_id in yaml_config.keys():
        if uut_id not in valid_uut_list:
            libmfg_utils.cli_err("Barcode file encountered invalid UUT ID: {:s}".format(uut_id))
            return None

        # add auto generated fields
        if "UUT_VALID" not in yaml_config[uut_id].keys():
            yaml_config[uut_id]["UUT_VALID"] = True
        if "UUT_ID" not in yaml_config[uut_id].keys():
            yaml_config[uut_id]["UUT_ID"] = uut_id.upper()
        if "UUT_TS" not in yaml_config[uut_id].keys():
            yaml_config[uut_id]["UUT_TS"] = libmfg_utils.get_fru_date()

        # change None to "" to avoid exceptions
        for field in yaml_config[uut_id].keys():
            if yaml_config[uut_id][field] is None:
                yaml_config[uut_id][field] = ""

        # check for missing scannable fields 
        scan_item_list = [
            SYS_SN,
            SYS_PN,
            MAC,
            CPU_SN,
            CPU_PN,
            SWI_SN,
            SWI_PN
            # BMC_SN,
            # BMC_PN
        ]
        for field in scan_item_list:
            if field not in yaml_config[uut_id].keys():
                libmfg_utils.cli_err("{:s} missing {:s} field in barcode file".format(uut_id, field))
                return None

        # check for dupes and validate
        already_scanned_list = list()
        for field in scan_item_list:
            if not handle_scan(field, yaml_config[uut_id][field], already_scanned_list):
                return None
            else:
                already_scanned_list.append(yaml_config[uut_id][field])


    return yaml_config


def log_barcodes(test_ctrl, fru_config):
    scan_item_list = [
            SYS_SN,
            SYS_PN,
            MAC,
            CPU_SN,
            CPU_PN,
            SWI_SN,
            SWI_PN
            # BMC_SN,
            # BMC_PN
        ]
    test_ctrl.cli_log_inf("Barcode scans:", level=0)
    for field in scan_item_list:
        test_ctrl.cli_log_inf("==> Scanned {:s}: {:s} <==".format(field, fru_config[field]), level=1)
    test_ctrl.cli_log_inf("Barcode scans end\n", level=0)
