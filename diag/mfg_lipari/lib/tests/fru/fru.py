import sys, os, re

sys.path.append(os.path.relpath("../../lib"))
import libtest_config
import libmfg_utils
from libsku_utils import *

from ..barcode import barcode

param_cfg = libtest_config.parse_config("lib/tests/fru/parameters.yaml")

### FRU_PROG ###
def fru_prog(test_ctrl, fru_config):

    date =       fru_config["UUT_TS"]
    sn =         fru_config[barcode.CPU_SN]
    mac =        fru_config[barcode.MAC]
    pn =         fru_config[barcode.CPU_PN]
    switch_sn =  fru_config[barcode.SWI_SN]
    switch_pn =  fru_config[barcode.SWI_PN]
    # bmc_sn =     fru_config[barcode.BMC_SN]
    # bmc_pn =     fru_config[barcode.BMC_PN]
    chassis_sn = fru_config[barcode.SYS_SN]
    chassis_pn = fru_config[barcode.SYS_PN]

    if not tor_write_fru(test_ctrl, date, chassis_sn, mac, chassis_pn, sn, pn, dev="CPU"):
        return False
    tor_read_fru(test_ctrl, dev="CPU")

    if not tor_write_fru(test_ctrl, date, chassis_sn, mac, chassis_pn, switch_sn, switch_pn, dev="SWITCH"):
        return False
    tor_read_fru(test_ctrl, dev="SWITCH")

    # if not tor_write_fru(test_ctrl, date, chassis_sn, mac, chassis_pn, bmc_sn, bmc_pn, dev="BMC"):
    #     return False
    # tor_read_fru(test_ctrl, dev="BMC")

    return True

### FRU_VERIFY ###
def fru_verify(test_ctrl, fru_config):
    if not fru_init(test_ctrl):
        test_ctrl.cli_log_err("FRU read failed", level=0)
        return False

    tbl = [
            ("CPU FRU Serial Number",   test_ctrl.mtp._sn["CPU"],       fru_config[barcode.CPU_SN]),
            ("CPU FRU Part Number",     test_ctrl.mtp._pn["CPU"],       fru_config[barcode.CPU_PN]),
            ("CPU FRU MAC Address",     test_ctrl.mtp._mac["CPU"],      fru_config[barcode.MAC]),
            ("Switch FRU Serial Number",test_ctrl.mtp._sn["SWITCH"],    fru_config[barcode.SWI_SN]),
            ("Switch FRU MAC Address",  test_ctrl.mtp._mac["SWITCH"],   fru_config[barcode.MAC]),
            ("Switch FRU Part Number",  test_ctrl.mtp._pn["SWITCH"],    fru_config[barcode.SWI_PN]),
            # ("BMC FRU Serial Number", test_ctrl.mtp._sn["BMC"],       fru_config[barcode.BMC_SN]),
            # ("BMC FRU MAC Address",   test_ctrl.mtp._mac["BMC"],      fru_config[barcode.MAC]),
            # ("BMC FRU Part Number",   test_ctrl.mtp._pn["BMC"],       fru_config[barcode.BMC_PN]),
            ("Chassis Serial Number",   test_ctrl.mtp._sn["SYSTEM"],    fru_config[barcode.SYS_SN]),
            ("Chassis Part Number",     test_ctrl.mtp._pn["SYSTEM"],    fru_config[barcode.SYS_PN])
        ]

    ret = True
    for field, got, exp in tbl:
        if got != exp:
            test_ctrl.cli_log_err("Incorrect {:s}: {:s}, expected {:s}".format(field, got, exp), level=0)
            ret &= False

    return ret

def fru_init(test_ctrl):
    """ Read FRU and save it into object's _sn, _mac, _pn """

    for dev in ("CPU", "SWITCH"): #, "BMC"):
        fru_buf = tor_read_fru(test_ctrl, dev)
        if not fru_buf:
            test_ctrl.cli_log_err("Unable to read {:s} FRU".format(dev), level=0)
            return False
        fru_buf = fru_buf.replace("\t","  ") # keep regex easy

        if not tor_fru_parse_pn(test_ctrl, fru_buf, dev):
            test_ctrl.cli_log_err("Part number doesn't match any known formats in {:s} FRU".format(dev), level=0)
            test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(fru_buf)))
            return False

        if not tor_fru_parse_sn(test_ctrl, fru_buf, dev):
            test_ctrl.cli_log_err("Serial number doesn't match any known formats in {:s} FRU".format(dev), level=0)
            test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(fru_buf)))
            return False

        if not tor_fru_validate_sn(test_ctrl, dev):
            test_ctrl.cli_log_err("Serial number in {:s} FRU does not match this factory location".format(dev), level=0)
            test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(fru_buf)))
            return False

        if not tor_fru_parse_mac(test_ctrl, fru_buf, dev):
            test_ctrl.cli_log_err("MAC address doesn't match any known formats in {:s} FRU".format(dev), level=0)
            test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(fru_buf)))
            return False

        if not tor_fru_parse_date(test_ctrl, fru_buf, dev, init_date=True):
            test_ctrl.cli_log_err("Date field doesn't match any known formats in {:s} FRU".format(dev), level=0)
            test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(fru_buf)))
            return False

        # Extended table
        if dev == "CPU":
            if not tor_fru_parse_pn(test_ctrl, fru_buf, "SYSTEM"):
                test_ctrl.cli_log_err("Chassis Part number doesn't match any known formats in {:s} FRU".format(dev), level=0)
                test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(fru_buf)))
                return False

            if not tor_fru_parse_sn(test_ctrl, fru_buf, "SYSTEM"):
                test_ctrl.cli_log_err("Chassis Serial number doesn't match any known formats in {:s} FRU".format(dev), level=0)
                test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(fru_buf)))
                return False

            if not tor_fru_validate_sn(test_ctrl, "SYSTEM"):
                test_ctrl.cli_log_err("Chassis Serial number in {:s} FRU does not match this factory location".format(dev), level=0)
                test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(fru_buf)))
                return False

    return True

def tor_write_fru(test_ctrl, date, sn, mac, pn, pcba_sn, pcba_pn, dev="CPU"):
    cmd = "/home/admin/eeupdate/eeutil -update -erase -numBytes=512 -smbus=False"
    cmd += " -dev='{:s}'".format(dev)
    cmd += " -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}'".format(date, sn, mac, pn)
    cmd += " -pcbsn='{:s}' -pcbpn='{:s}'".format(pcba_sn, pcba_pn)
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=param_cfg["FRU_PROG_DELAY"]):
    	test_ctrl.cli_log_err("{:s} command timed out".format(cmd), level=0)
    	return False
    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    if not cmd_buf:
        test_ctrl.cli_log_err("Unable to program {:s} FRU".format(dev), level=0)
        return False

    match = re.findall(r"FRU Checkum and Type\/Length Checks Passed|EEPROM updated", cmd_buf)
    if not match:
        test_ctrl.cli_log_err("{:s} FRU programming failed".format(dev), level=0)
        return False

    return True

def tor_read_fru(test_ctrl, dev="CPU"):
    cmd = "/home/admin/eeupdate/eeutil -disp -smbus=False"
    cmd += " -dev='{:s}'".format(dev)
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=param_cfg["FRU_PROG_DELAY"]):
    	test_ctrl.cli_log_err("{:s} command timed out".format(cmd), level=0)
    	return ""
    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    return cmd_buf

def tor_fru_parse_pn(test_ctrl, fru_buf, dev):
    """ Save to mtp._pn and return True/False """
    PART_NUM_FIELD = r"Part Number"
    PCBA_NUM_FIELD = r"PCBA Part Number"
    ASSY_NUM_FIELD = r"Assembly Number"
    pn_table = {
            "CPU":    (PCBA_NUM_FIELD, PART_NUMBERS_MATCH.LIPARI_CPU_PN),
            "SWITCH": (PCBA_NUM_FIELD, PART_NUMBERS_MATCH.LIPARI_SWI_PN),
            "BMC":    (PCBA_NUM_FIELD, PART_NUMBERS_MATCH.LIPARI_BMC_PN),
            "SYSTEM": (PART_NUM_FIELD, PART_NUMBERS_MATCH.LIPARI_SYS_PN),
            "ELBA":   (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.LIPARI_ELB_PN)
    }

    disp_field, pn_regex = pn_table[dev]
    pn_disp_regex = r"%s +(%s)" % (disp_field, pn_regex)
    match = re.findall(pn_disp_regex, fru_buf)
    if match:
        test_ctrl.mtp._pn[dev] = match[0]
    else:
        return False
    return True

def tor_fru_parse_sn(test_ctrl, fru_buf, dev):
    sn = barcode.serial_number_validate(fru_buf, dev, exact_match=False)
    if not sn:
        test_ctrl.cli_log_err("SN read failed")
        return False
    test_ctrl.mtp._sn[dev] = sn
    return True

def validate_serial_number_strict(test_ctrl, sn, factory_location, pn_format, pn):
    if factory_location == Factory.LAB:
        return barcode.serial_number_validate(sn)

    try:
        sn_regex = SN_FORMAT_TABLE[factory_location][pn_format]
    except KeyError:
        try:
            sn_regex = SN_FORMAT_TABLE[factory_location]["DEFAULT"]
        except KeyError:
            test_ctrl.cli_log_err("factory_location not initialized correctly to validate Serial Number", level=0)
            return False

    if re.match(sn_regex, sn):
        return True
    else:
        test_ctrl.cli_log_err("Serial Number did not match formatting for {:s} at site {:s}".format(pn, factory_location), level=0)
        return False

def tor_fru_validate_sn(test_ctrl, dev):
    sn = test_ctrl.mtp._sn[dev]
    pn = test_ctrl.mtp._pn[dev]
    if dev == "SWITCH":
        pn_format = PART_NUMBERS_MATCH.LIPARI_SWI_PN
    elif dev == "BMC":
        pn_format = PART_NUMBERS_MATCH.LIPARI_BMC_PN
    elif dev == "SYSTEM":
        pn_format = PART_NUMBERS_MATCH.LIPARI_SYS_PN
    else:
        pn_format = PART_NUMBERS_MATCH.LIPARI_CPU_PN

    if not validate_serial_number_strict(test_ctrl, sn, test_ctrl._factory_location, pn_format, pn):
        return False
    return True

def tor_fru_parse_mac(test_ctrl, fru_buf, dev):
    """ Save to mtp._mac and return True/False """
    disp_field = r"MAC Address Base"
    if dev == "ELBA":
        mac_regex = PEN_MAC_DASHES_FMT
    else:
        mac_regex = "0x(" + PEN_MAC_COLONS_FMT + r")"
    mac_disp_regex = r"%s +%s" % (disp_field, mac_regex)
    match = re.findall(mac_disp_regex, fru_buf)
    if match:
    	test_ctrl.mtp._mac[dev] = libmfg_utils.mac_address_remove_separator(match[0])
    else:
        return False
    return True

def tor_fru_parse_date(test_ctrl, fru_buf, dev, init_date):
    """ Save to mtp._date and return True/False """
    if init_date:
        if dev == "ELBA":
            disp_field = r"Manufacturing Date/Time"
            date_hex = r"0x[A-Z0-9]+"
            date_regex = r"\d{2}/\d{2}/\d{2}"
        else:
            disp_field = r"MFG Date/Time"
            date_hex = r""
            date_regex = r"\d{6}"
        date_disp_regex = r"%s +%s +(%s)" % (disp_field, date_hex, date_regex)
        match = re.findall(date_disp_regex, fru_buf)
        if match:
            test_ctrl.mtp._prog_date[dev] = match[0].replace('/','')
        else:
            return False
    else:
        test_ctrl.mtp._prog_date[dev] = None
    return True

def fru_erase(test_ctrl):
    erase_cmd = "/home/admin/eeupdate/eeutil -update -erase -numBytes=512 -smbus=False"

    if not test_ctrl.mtp.exec_cmd(erase_cmd + " -dev=CPU"):
        return False
    tor_read_fru(test_ctrl, dev="CPU")

    if not test_ctrl.mtp.exec_cmd(erase_cmd + " -dev=SWITCH"):
        return False
    tor_read_fru(test_ctrl, dev="SWITCH")

    # if not test_ctrl.mtp.exec_cmd(erase_cmd + "dev=BMC"):
    #     return False
    # tor_read_fru(test_ctrl, dev="BMC")

    return True

