#!/usr/bin/env python

import sys
import os
import time
import argparse
import threading
import traceback
import binascii
import random

sys.path.append(os.path.relpath("lib"))
import libmfg_utils
import libmtp_utils
import image_control
import crc8
import testlog
import mtp_diag_regression as diag_reg
from libdefs import MTP_Const
from libdefs import NIC_Type
from libdefs import MTP_TYPE
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import Swm_Test_Mode
from libdefs import MFG_DIAG_CMDS
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Path
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libmfg_cfg import *

def single_nic_qsfp_read_stress_test(mtp_mgmt_ctrl, slot, nic_test_rslt_list, dsp, test_case_name, stop_on_err, read_cycles):

    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test_case_name))
    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test_case_name)
    qsfp_ports_sn = {"0": "", "1": ""}
    ret = True

    # build the refernce qsfp serial number
    for port in qsfp_ports_sn:
        nic_cmd_list = list()
        nic_cmd_list.append("/data/diag/scripts/eeprom_sn.sh -s -b {:s}".format(port))
        #nic_cmd_list.append("for i in $(seq 100); do /data/diag/scripts/eeprom_sn.sh -s -b 1; done")
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            ret = False
            nic_test_rslt_list[slot] = False
            mtp_mgmt_ctrl.cli_log_slot_err(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
            break
        qsfp_ref_sn = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf().split("\n")[1].strip("\r")
        if 'not detected' in qsfp_ref_sn.lower():
            ret = False
            nic_test_rslt_list[slot] = False
            mtp_mgmt_ctrl.cli_log_slot_err(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
            break
        qsfp_ports_sn[port] = qsfp_ref_sn
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, "Got refernce QSFP SN, {:s}".format(qsfp_ref_sn))

    # stress test start
    for port, ref_sn in list(qsfp_ports_sn.items()):
        nic_cmd_list = list()
        nic_cmd_list.append("for i in $(seq {:d}); do /data/diag/scripts/eeprom_sn.sh -s -b {:s}; done".format(read_cycles, port))
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.NIC_MGMT_IP_SET_DELAY * read_cycles):
            ret = False
            nic_test_rslt_list[slot] = False
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
            if stop_on_err:
                break
        sn_count = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf().count(ref_sn)
        if sn_count != read_cycles:
            ret = False
            nic_test_rslt_list[slot] = False
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Read back QSFP SN counts {:d} not matche read cycles {:d}".format(sn_count, read_cycles))
            if stop_on_err:
                break
        lines = []
        for line in mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf().split("\n")[1:-1]:
            line = line.strip("\r")
            if line not in lines:
                lines.append(line)
        if len(lines) != 1 or lines[0] != ref_sn:
            ret = False
            nic_test_rslt_list[slot] = False
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Read back Error SNs: {:s}".format(str(lines)))
            if stop_on_err:
                break

    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test_case_name, start_ts)
    if not ret:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test_case_name, "FAILED", duration))
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test_case_name, duration))
    return ret

def binary_file_2_hexstr(mtp_mgmt_ctrl, slot, binaryfile=None):
    """
    read out the give binary file an convert it to hex string
    return the hexstring
    """

    try:
        with open(binaryfile, "rb") as f1:
            bytearray_file1 = bytearray(f1.read())
            f1.close()
    except Exception as Err:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Open Read Binaryfile {:s} Failed with Error: {:s}".format(binaryfile, str(Err)))
        return False

    if not binaryfile:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Give Binaryfile {:s} is Empty".format(binaryfile))
        return False
    return binascii.hexlify(bytearray_file1)

def binary_file_compare(mtp_mgmt_ctrl, slot, binaryfile1=None, binaryfile2=None):
    """
    compare two binary files byte to byte
    if two binary files same, return True, otherwise return False.
    """

    if not binaryfile1 or not binaryfile2:
        return False

    hexstr_file1 = binary_file_2_hexstr(mtp_mgmt_ctrl, slot, binaryfile1)
    if not hexstr_file1:
        return False
    hexstr_file2 = binary_file_2_hexstr(mtp_mgmt_ctrl, slot, binaryfile2)
    if not hexstr_file2:
        return False

    if hexstr_file1 == hexstr_file2:
        return True

    compare_res = []
    min_lenth = min(len(hexstr_file1), len(hexstr_file2))
    for i in range(min_lenth):
        if  i % 2 != 0:
            continue
        j = i + 2
        if j > min_lenth:
            j = -1
        if hexstr_file1[i:j] == hexstr_file2[i:j]:
            compare_res.append(hexstr_file1[i:j])
        else:
            compare_res.append(hexstr_file1[i:j] + "|" +  hexstr_file2[i:j])
    mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, " ".join(compare_res))
    return False

def single_nic_ufm3_rw_stress_test(mtp_mgmt_ctrl, slot, nic_test_rslt_list, dsp, test_case_name):

    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test_case_name))
    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test_case_name)
    #prog_cmd_list = ["cpldapp -writeflash {:s} {:s}", "/data/nic_util/xo3dcpld -prog {:s} {:s}"]
    prog_cmd_list = ["/data/nic_util/xo3dcpld -prog {:s} {:s}"]
    partition = "ufm3"
    orginal_ufm3_dump_file_name = "{:s}_read.bin".format(partition)
    tmp_test_bin_file = "{:s}_tmp_test.bin".format(partition)
    tmp_test_readback_bin_file = "{:s}_tmp_test_readback.bin".format(partition)
    ret = True

    # save current UFM3 values by dump it into a file
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_dump_cpld(partition, file_path=MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH + orginal_ufm3_dump_file_name):
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Dump NIC Original CPLD internal flash UFM3 failed")
        mtp_mgmt_ctrl.mtp_dump_nic_err_msg(slot)
        nic_test_rslt_list[slot] = False
        return False
    # copy dumped binary file to MTP
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_copy_file_from_nic(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH + orginal_ufm3_dump_file_name, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + orginal_ufm3_dump_file_name):
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Copy dumped binary file to MTP Failed, Source File is {:s}".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH + orginal_ufm3_dump_file_name))
        mtp_mgmt_ctrl.mtp_dump_nic_err_msg(slot)
        nic_test_rslt_list[slot] = False
        return False

    orginal_ufm3_hex = binary_file_2_hexstr(mtp_mgmt_ctrl, slot, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + orginal_ufm3_dump_file_name)
    if not orginal_ufm3_hex:
        nic_test_rslt_list[slot] = False
        return False
    orginal_ufm3_hex_list = [orginal_ufm3_hex[i:i+2] for i in range(0, len(orginal_ufm3_hex), 2)]
    ufm3_byte_length = len(orginal_ufm3_hex_list) # should be 16

    # [UFM3_data14, UFM3_data13, ... UFM3_data0, crc8]
    test_values = list()
    # exclude crc8 Byte since we need re-calculate crc8
    test_values.append(["01"] + ["00"] * (ufm3_byte_length - 2))  # enbale sec pattern
    test_values.append(["00"] * (ufm3_byte_length - 1))  # disable sec pattern
    test_values.append(["aa"] * (ufm3_byte_length - 1))  # random pattern
    test_values.append(["55"] * (ufm3_byte_length - 1))  # random pattern
    test_values.append(["ff"] * (ufm3_byte_length - 1))
    test_values.append(orginal_ufm3_hex_list[:-1])

    crc8hash = crc8.crc8()
    for test_index, test_value in enumerate(test_values):
        # calculate crc8
        crc8hash.reset()
        crc8hash.update(binascii.unhexlify("".join(test_value)))
        crc8_checksum = crc8hash.hexdigest()
        binary_line = test_value + [crc8_checksum]
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, str(binary_line))
        # create binary file
        try:
            with open(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + tmp_test_bin_file, "wb") as f:
                f.write(binascii.unhexlify("".join(binary_line)))
                f.flush()
                f.close()
        except Exception as Err:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, str(Err))
            nic_test_rslt_list[slot] = False
            return False
        # copy the binary to nic
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_copy_image(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + tmp_test_bin_file, directory=MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH):
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Copy Generated binary file to NIC Failed, Source File is {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + tmp_test_bin_file))
            mtp_mgmt_ctrl.mtp_dump_nic_err_msg(slot)
            nic_test_rslt_list[slot] = False
            return False
        # program UFM3
        progCmd = random.choice(prog_cmd_list).format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH + tmp_test_bin_file, "ufm3")
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, progCmd)
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_exec_cmds([progCmd], timeout=MTP_Const.OS_CMD_DELAY):
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
            nic_test_rslt_list[slot] = False
            ret = False
            break
        if "xo3dcpld" in prog_cmd_list and "Invalid region to erase" in mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf():
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Program UFM3 NOT SUPPORTED by current version of xo3dcpld utility")
            nic_test_rslt_list[slot] = False
            ret = False
            break
        if "end of programming" not in mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf():
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
            nic_test_rslt_list[slot] = False
            ret = False
            break
        # dump UFM3 back to a binary file
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_dump_cpld(partition, file_path=MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH + tmp_test_readback_bin_file):
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Read Back NIC CPLD internal flash UFM3 failed")
            mtp_mgmt_ctrl.mtp_dump_nic_err_msg(slot)
            nic_test_rslt_list[slot] = False
            ret = False
            break
        # copy dumped binary file to MTP
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_copy_file_from_nic(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH + tmp_test_readback_bin_file, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + tmp_test_readback_bin_file):
            ret = False
            break
        # compare two binary file
        if not binary_file_compare(mtp_mgmt_ctrl, slot, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + tmp_test_bin_file, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + tmp_test_readback_bin_file):
            nic_test_rslt_list[slot] = False
            ret = False
            break
        # enable cpld to access ufm3
        # """
        #     Write to spi/smbus reg 0xc0[0] =1 to enable cpld to access ufm3 or trigger the following 4 cases to enable hard power cycle the ASIC power( make sure reg 0xc0 [0]  = 0 when disable the MUX access for this SPI UFM module)
        #     AC power cycle
        #     GPIO 3 power cycle
        #     Voltage Regulator thermal trip fault
        #     PUF error
        # """
        cmd = "cpldapp -w 0xc0 0x01"
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_exec_cmds([cmd], timeout=MTP_Const.OS_CMD_DELAY):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
            nic_test_rslt_list[slot] = False
            ret = False
            break
        # read back 'UFM3 Read debug' register and compare with specified test UFM data
        # reverse binary_line, so that it's easy to compate with register value. [crc8, UFM3_data0,.. UFM3_data14]
        # reister 0xC1 is CRC byte, 0xc2 is UFM3_data0, ... 0xcf is UFM3_data13 0xd0 is UFM3_data14
        ufm3_data_reg_base = 0xc1
        for index, ufm3_data in enumerate(binary_line[::-1]):
            cmd = "cpldapp -r 0x{:02x}".format(ufm3_data_reg_base + index)
            if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_exec_cmds([cmd], timeout=MTP_Const.OS_CMD_DELAY):
                mtp_mgmt_ctrl.cli_log_slot_err(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
                nic_test_rslt_list[slot] = False
                ret = False
                break
            ufm3_read_debug_reg_val = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf().split("\n")[1].strip("\r")
            if int(ufm3_read_debug_reg_val, 16) != int(ufm3_data, 16):
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Value {:02x} from UFM3 Read debug NOT match Value {:02x} from dumped bin file".format(ufm3_read_debug_reg_val, ufm3_data))
                nic_test_rslt_list[slot] = False
                ret = False
                break
        # check register 0xD1
        cmd = "cpldapp -r 0xd1"
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_exec_cmds([cmd], timeout=MTP_Const.OS_CMD_DELAY):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
            nic_test_rslt_list[slot] = False
            ret = False
            break
        ufm3_read_debug_reg_val = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf().split("\n")[1].strip("\r")
        # check bit2 crc checkout, 1 means crc check error
        if (int(ufm3_read_debug_reg_val, 16) & 0b00000100):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Register 0xD1 bit2 check failed")
            nic_test_rslt_list[slot] = False
            ret = False
            break
        # only check for esec enable test pattern
        if test_index == 0:
            # check bit1 hw lock checkout
            if not (int(ufm3_read_debug_reg_val, 16) & 0b00000010):
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Register 0xD1 bit1 check failed")
                nic_test_rslt_list[slot] = False
                ret = False
                break
        # recover register 0xc0
        cmd = "cpldapp -w 0xc0 0x00"
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_exec_cmds([cmd], timeout=MTP_Const.OS_CMD_DELAY):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
            nic_test_rslt_list[slot] = False
            ret = False
            break

    # recover register 0xc0 if break out of above loop
    if not ret:
        if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_exec_cmds([cmd], timeout=MTP_Const.OS_CMD_DELAY):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
            nic_test_rslt_list[slot] = False

    # prog back original ufm3 dump, if original ufm3 are all FF, we have recovert it by direct prog the bin without cal checksum.
    progCmd = random.choice(prog_cmd_list).format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH + orginal_ufm3_dump_file_name, "ufm3")
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, progCmd)
    if not mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_exec_cmds([progCmd], timeout=MTP_Const.OS_CMD_DELAY):
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
        nic_test_rslt_list[slot] = False
        return False
    if "xo3dcpld" in prog_cmd_list and "Invalid region to erase" in mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf():
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, "Program UFM3 NOT SUPPORTED by current version of xo3dcpld utility")
        nic_test_rslt_list[slot] = False
        return False
    if "end of programming" not in mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf():
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_get_cmd_buf())
        nic_test_rslt_list[slot] = False
        return False

    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test_case_name, start_ts)
    if not ret:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test_case_name, "FAILED", duration))
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test_case_name, duration))
    return ret

def single_nic_programe_boot0(mtp_mgmt_ctrl, slot, nic_test_rslt_list, dsp, test_case_name, stop_on_err, boot0_img_file, boot0_installer_file):

    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test_case_name))
    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test_case_name)

    ret = mtp_mgmt_ctrl.mtp_program_nic_uboot(slot, boot0_img_file, boot0_installer_file, uboot_pat="boot0")
    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test_case_name, start_ts)
    if not ret:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test_case_name, "FAILED", duration))
        nic_test_rslt_list[slot] = False
        mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test_case_name, duration))

    return ret

def cpld_qsfp_sn_read_stress_test(mtp_mgmt_ctrl, nic_type, nic_list, dsp, test_case_name, stop_on_err, read_cycles=10000):

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} {:s} {:s} Start....".format(nic_type, dsp, test_case_name), level=0)
    fail_list = list()
    new_nic_list = nic_list[:]
    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM

    for slot in new_nic_list:
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            nic_test_rslt_list[slot] = False
            if slot not in fail_list:
                fail_list.append(slot)
            continue
        nic_thread = threading.Thread(target = single_nic_qsfp_read_stress_test,
                                        args = (mtp_mgmt_ctrl,
                                                slot,
                                                nic_test_rslt_list,
                                                dsp,
                                                test_case_name,
                                                stop_on_err,
                                                read_cycles))
        nic_thread.daemon = True
        nic_thread.start()
        nic_thread_list.append(nic_thread)

    while True:
        if len(nic_thread_list) == 0:
            break
        for nic_thread in nic_thread_list[:]:
            if not nic_thread.is_alive():
                ret = nic_thread.join()
                nic_thread_list.remove(nic_thread)
        time.sleep(5)

    for slot in new_nic_list:
        if not nic_test_rslt_list[slot]:
            if slot not in fail_list:
                fail_list.append(slot)
            if stop_on_err:
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                    raise Exception
            new_nic_list.remove(slot)

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} {:s} {:s} Complete\n".format(nic_type, dsp, test_case_name), level=0)
    return fail_list

def ufm3_read_write_stress_test_from_spi(mtp_mgmt_ctrl, nic_type, nic_list, dsp, test_case_name, stop_on_err):

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} {:s} {:s} Start....".format(nic_type, dsp, test_case_name), level=0)
    fail_list = list()
    new_nic_list = nic_list[:]
    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM

    for slot in new_nic_list:
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            nic_test_rslt_list[slot] = False
            if slot not in fail_list:
                fail_list.append(slot)
            continue
        nic_thread = threading.Thread(target = single_nic_ufm3_rw_stress_test,
                                        args = (mtp_mgmt_ctrl,
                                                slot,
                                                nic_test_rslt_list,
                                                dsp,
                                                test_case_name))
        nic_thread.daemon = True
        nic_thread.start()
        nic_thread_list.append(nic_thread)

    while True:
        if len(nic_thread_list) == 0:
            break
        for nic_thread in nic_thread_list[:]:
            if not nic_thread.is_alive():
                ret = nic_thread.join()
                nic_thread_list.remove(nic_thread)
        time.sleep(5)

    for slot in new_nic_list:
        if not nic_test_rslt_list[slot]:
            if slot not in fail_list:
                fail_list.append(slot)
            if stop_on_err:
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                    raise Exception
            new_nic_list.remove(slot)

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} {:s} {:s} Complete\n".format(nic_type, dsp, test_case_name), level=0)
    return fail_list

def cpld_programe_boot0(mtp_mgmt_ctrl, nic_type, nic_list, dsp, test_case_name, stop_on_err=False, boot0_img_file=None, boot0_installer_file=None,):

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} {:s} {:s} Start....".format(nic_type, dsp, test_case_name), level=0)
    fail_list = list()
    new_nic_list = nic_list[:]
    nic_thread_list = list()
    nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM

    if not boot0_img_file or not boot0_installer_file:
        # return nic_list as fail_list
        mtp_mgmt_ctrl.cli_log_err("Both boot0_img_file and boot0_installer_file must provid")
        return new_nic_list

    if not boot0_img_file or not boot0_installer_file:
        return new_nic_list

    for slot in new_nic_list:
        if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
            nic_test_rslt_list[slot] = False
            if slot not in fail_list:
                fail_list.append(slot)
            continue
        nic_thread = threading.Thread(target = single_nic_programe_boot0,
                                        args = (mtp_mgmt_ctrl,
                                                slot,
                                                nic_test_rslt_list,
                                                dsp,
                                                test_case_name,
                                                stop_on_err,
                                                boot0_img_file,
                                                boot0_installer_file))
        nic_thread.daemon = True
        nic_thread.start()
        nic_thread_list.append(nic_thread)

    while True:
        if len(nic_thread_list) == 0:
            break
        for nic_thread in nic_thread_list[:]:
            if not nic_thread.is_alive():
                ret = nic_thread.join()
                nic_thread_list.remove(nic_thread)
        time.sleep(5)

    for slot in new_nic_list:
        if not nic_test_rslt_list[slot]:
            if slot not in fail_list:
                fail_list.append(slot)
            if stop_on_err:
                if stop_on_err:
                    mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                    raise Exception
            new_nic_list.remove(slot)

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} {:s} {:s} Complete\n".format(nic_type, dsp, test_case_name), level=0)
    return fail_list

def cpld_console_seq_test(mtp_mgmt_ctrl, nic_type, nic_list, dsp, test_case_name, new_cpld_json_dict, stop_on_err, pc_cycles=100):

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} {:s} {:s} Start....".format(nic_type, dsp, test_case_name), level=0)
    fail_list = list()
    nic_list = nic_list[:]

    for slot in nic_list:
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test_case_name))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test_case_name)

        if test_case_name == "3V3_POWER_CYCLE":
            ret = libmtp_utils.cpld_3v3_powercycle_test(mtp_mgmt_ctrl, slot, new_cpld_json_dict, pc_cycles=pc_cycles)
        elif test_case_name == "GPIO3_POWER_CYCLE":
            ret = libmtp_utils.cpld_gpio3_powercycle_test(mtp_mgmt_ctrl, slot, pc_cycles=pc_cycles, stop_on_err=stop_on_err)
        elif test_case_name == "AC_POWER_CYCLE":
            ret = libmtp_utils.cpld_ac_powercycle_test(mtp_mgmt_ctrl, slot, pc_cycles=pc_cycles, stop_on_err=stop_on_err)
        elif test_case_name == "UPGRADE_DOWNGRADE_UTILITY_FUNCTION_STRESS_AND_FAILSAFE_NEGTIVE":
            ret = libmtp_utils.cpld_upgrade_downgrade_utility_function_test(mtp_mgmt_ctrl, slot, new_cpld_json_dict, pc_cycles=pc_cycles, stop_on_err=stop_on_err)
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown {:s}: {:s}, Fail this slot".format(dsp, test_case_name))
            ret = False

        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test_case_name, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test_case_name, "FAILED", duration))
            if slot not in fail_list:
                fail_list.append(slot)
            if stop_on_err:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                raise Exception
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test_case_name, duration))

    mtp_mgmt_ctrl.cli_log_inf("MTP {:s} {:s} {:s} Complete\n".format(nic_type, dsp, test_case_name), level=0)
    return fail_list

def single_nic_para_cpld_program(mtp_mgmt_ctrl, slot, nic_test_rslt_list, cpld_img_file=None, fail_cpld_img_file=None, fea_cpld_img_file=None):

    dsp = FF_Stage.FF_DL
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    ret = True
    testlist = []
    if cpld_img_file:
        testlist.append("CPLD_PROG")
    if fail_cpld_img_file:
        testlist.append("FSAFE_CPLD_PROG")
    if fea_cpld_img_file:
        testlist.append("FEA_PROG")

    for test in testlist:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
        # program CPLD
        if test == "CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld(slot, cpld_img_file)
        # program failsafe CPLD
        elif test == "FSAFE_CPLD_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_failsafe_cpld(slot, fail_cpld_img_file)
        # program feature row
        elif test == "FEA_PROG":
            ret = mtp_mgmt_ctrl.mtp_program_nic_cpld_feature_row(slot, fea_cpld_img_file)
        else:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unknown DL Test: {:s}, Ignore".format(test))
            continue
        duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            nic_test_rslt_list[slot] = False
            # mtp_mgmt_ctrl.mtp_dump_err_msg(mtp_mgmt_ctrl.mtp_get_nic_err_msg(slot))
            mtp_mgmt_ctrl.mtp_set_nic_status_fail(slot)
            break
        else:
            mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

    return ret

def main():
    parser = argparse.ArgumentParser(description="Single MTP CPLD Validation Test", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mtpid", help="MTP ID, like MTP-001, etc", required=True)
    parser.add_argument("--stop_on_error", help="leave the MTP in error state if error happens", action='store_true')
    parser.add_argument("--verbosity", help="increase output verbosity", action='store_true', default=False)
    parser.add_argument("--stage", "--corner", type=FF_Stage, help="diagnostic environment condition", choices=list(FF_Stage), default=FF_Stage.FF_P2C)
    parser.add_argument("--swm", type=Swm_Test_Mode, help="SWM test mode", choices=list(Swm_Test_Mode))
    parser.add_argument("--fail-slots", help="consider these slots failed", nargs="*", default=[])
    parser.add_argument("-cfile", "--cpldfile", help="New CPLD Binary file Json files for Validation, default to %(default)s", default="config/latest_release_cpld_4validation.json")
    parser.add_argument("--mtpcfg", help="JobD reserved MTP", default=None)
    args = parser.parse_args()

    mtp_id = args.mtpid
    mtp_cli_id_str = libmfg_utils.id_str(mtp=mtp_id)
    latest_cpld_json = args.cpldfile
    
    swm_lp_boot_mode = False 
    stop_on_err = args.stop_on_error
    verbosity = args.verbosity
    stage = args.stage
    swmtestmode = Swm_Test_Mode.SW_DETECT
    if args.swm:
        swmtestmode = args.swm

    # load the mtp config
    mtp_chassis_cfg_file_list = list()
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    if args.mtpcfg:
        mtp_chassis_cfg_file_list.append(os.path.abspath(args.mtpcfg))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)

    # find the mtp management config based on the mtpid
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")

    # find the apc config based on the mtpid
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")

    # find the mtp capability
    mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    # find any slots to skip
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)

    mtp_mgmt_ctrl = mtp_ctrl(mtp_id,
                             sys.stdout,
                             None,
                             [],
                             None,
                             mgmt_cfg = mtp_mgmt_cfg,
                             apc_cfg = mtp_apc_cfg,
                             slots_to_skip = mtp_slots_to_skip,
                             dbg_mode = verbosity)

    # load new CPLD json file 
    new_cpld_json_dict = libmtp_utils.load_cpld_info_json(latest_cpld_json, verbosity)
    if not new_cpld_json_dict:
        print("Failed to Load CPLD JSON file, abort...")
        return 

    # logfiles
    mtp_script_dir, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=stage)

    try:
        if not libmfg_utils.mtp_common_setup(mtp_mgmt_ctrl, stage):
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP common setup fails, test abort...")
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_INV_PARAM, open_file_track_list)
            return

        # Set Naples25SWM test mode
        mtp_mgmt_ctrl.mtp_set_swmtestmode(swmtestmode)

        # Construct data structures for cards to test
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        pass_nic_list = list()
        fail_nic_list = list()
        skip_nic_list = list()

        # Add failed slots from toplevel
        if args.fail_slots:
            for slot in args.fail_slots:
                fail_nic_list.append(int(slot))

        nic_type_full_list = MFG_VALID_NIC_TYPE_LIST
        nic_test_full_list = list() # list of lists, NOT dict. order of insertion matters

        for nic_type in nic_type_full_list:
            nic_type_list = list()
            # make a list for all NICs of this type in MTP
            for slot in range(MTP_Const.MTP_SLOT_NUM):
                if slot in fail_nic_list:
                    continue
                if not nic_prsnt_list[slot]:
                    continue
                if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == nic_type:
                    nic_type_list.append(slot)
                    pass_nic_list.append(slot)
            nic_test_full_list.append(nic_type_list)

        nic_skipped_list = mtp_mgmt_ctrl.mtp_get_nic_skip_list()
        for slot in range(len(nic_skipped_list)):
            if nic_skipped_list[slot]:
                skip_nic_list.append(slot)

        # check if MTP support present NIC
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag CPLD Validation Test compatibility check started", level=0)
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if nic_type == NIC_Type.VOMERO2:
                mtp_exp_capability = 0x3
            elif nic_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
                mtp_exp_capability = 0x2
            elif nic_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
                mtp_exp_capability = 0x1
            elif nic_type in MTP_MATERA_CAPABLE_NIC_TYPE_LIST:
                mtp_exp_capability = 0x4
            else:
                mtp_mgmt_ctrl.cli_log_err("NIC Type {:s}'s MTP compatibility unknown".format(nic_type), level=0)
                continue

            if nic_type == NIC_Type.NAPLES25SWM:
                if nic_list:
                    for slot in range(len(nic_list)):
                        if (mtp_mgmt_ctrl.mtp_get_swmtestmode(nic_list[slot]) in (Swm_Test_Mode.SWMALOM, Swm_Test_Mode.ALOM)):
                            swm_lp_boot_mode=True
                else:
                    swm_lp_boot_mode=False

                if stage not in (FF_Stage.FF_P2C, FF_Stage.QA):    #Skip SWM Low Power Test for 4C
                    swm_lp_boot_mode=False

            if nic_list:
                if not mtp_capability & mtp_exp_capability:
                    mtp_mgmt_ctrl.mtp_diag_fail_report("MTP capability 0x{:x} doesn't support {:s}".format(mtp_capability, nic_type))
                    libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
                    diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_SANITY, open_file_track_list)
                    return
        mtp_mgmt_ctrl.cli_log_inf("MTP Diag CPLD Validation Test compatibility check complete\n", level=0)

        mtp_mgmt_ctrl.cli_log_inf("Diag CPLD Validation Test Environment Started", level=0)
        fanspd = mtp_mgmt_ctrl.mtp_get_fanspd()
        inlet = mtp_mgmt_ctrl.mtp_get_inlet_temp(low_threshold=None, high_threshold=None)
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Fan Speed = {:3d}%".format(fanspd))
        mtp_mgmt_ctrl.cli_log_report_inf("MTP Inlet temp = {:2.2f}".format(inlet))
        mtp_mgmt_ctrl.cli_log_inf("Diag CPLD Validation Test Environment End\n", level=0)

        # program to config file specified CPLD, namely the MFG released CPLD, in case of some lab cards are running test version.
        dsp = "CPLD_VALIDATION"
        mtp_mgmt_ctrl.cli_log_inf("Diag CPLD Validation program CPLD to config file specified version Started", level=0)
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.mtp_power_on_nic(slot_list=pass_nic_list, dl=False)
        if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_test_full_list, swm_lp=swm_lp_boot_mode, nic_util=True, stop_on_err=stop_on_err):
            for nic_list in nic_test_full_list:
                for slot in nic_list:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        if slot not in fail_nic_list:
                            fail_nic_list.append(slot)
                        if slot in pass_nic_list:
                            pass_nic_list.remove(slot)
                        if stop_on_err:
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                            return

        nic_thread_list = list()
        nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not nic_prsnt_list[slot]:
                continue
            if slot in fail_nic_list:
                nic_test_rslt_list[slot] = False
                continue
            if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                nic_test_rslt_list[slot] = False
                continue

            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_cpld(mtp_mgmt_ctrl, slot, FF_Stage.FF_DL)["filename"]
            failsafe_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fail_cpld(mtp_mgmt_ctrl, slot, FF_Stage.FF_DL)["filename"]
            fea_cpld_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_fea_cpld(mtp_mgmt_ctrl, slot, FF_Stage.FF_DL)["filename"]
            nic_thread = threading.Thread(target=single_nic_para_cpld_program, args = (mtp_mgmt_ctrl,
                                                                                        slot,
                                                                                        nic_test_rslt_list,
                                                                                        cpld_img_file,
                                                                                        failsafe_cpld_img_file,
                                                                                        fea_cpld_img_file))
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
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not nic_test_rslt_list[slot]:
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)

        # # cpld & qspi image check
        mtp_mgmt_ctrl.mtp_power_off_nic()
        mtp_mgmt_ctrl.mtp_power_on_nic(slot_list=pass_nic_list, dl=False)
        dl_check_fail_list = diag_reg.naples_image_verify(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, fail_nic_list, "", dsp, stop_on_err)
        for slot in dl_check_fail_list:
            if slot in nic_list:
                nic_list.remove(slot)
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot)
        mtp_mgmt_ctrl.cli_log_inf("Diag CPLD Validation program CPLD to config file specified version end\n\n", level=0)

        mtp_mgmt_ctrl.cli_log_inf("Single MTP CPLD Validation Test Start",  level=0)
        # Disable PCIe polling
        if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.CAPRI:
            mtp_mgmt_ctrl.cli_log_inf("Wait {:02d} seconds for NIC power up before disable PCIE poll".format(MTP_Const.MTP_PCIE_EN_DIS_DELAY), level=0)
            libmfg_utils.count_down(MTP_Const.MTP_PCIE_EN_DIS_DELAY)
            diag_pre_fail_list = diag_reg.mtp_nic_diag_init_pre(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, args.skip_test, stage)
            for slot in diag_pre_fail_list:
                if slot in nic_list:
                    nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
        if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_test_full_list, swm_lp=swm_lp_boot_mode, nic_util=True, stop_on_err=stop_on_err):
            for nic_list in nic_test_full_list:
                for slot in nic_list:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        if slot not in fail_nic_list:
                            fail_nic_list.append(slot)
                        if slot in pass_nic_list:
                            pass_nic_list.remove(slot)
                        if stop_on_err:
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "STOP_ON_ERR asserted")
                            return
        mtp_mgmt_ctrl.cli_log_inf("\n",  level=0)

        test_case_list = ["PROGRAM_SPECIAL_BOOT0", "UPGRADE_DOWNGRADE_UTILITY_FUNCTION_STRESS_AND_FAILSAFE_NEGTIVE", "QSFP_SN_READ_STRESS",  "GPIO3_POWER_CYCLE", "3V3_POWER_CYCLE", "AC_POWER_CYCLE"]
        for nic_type, nic_list in zip(nic_type_full_list, nic_test_full_list):
            if not nic_list:
                continue
            # determin the 6-digits pn for nic_list of this card type
            for slot in nic_list:
                pn = mtp_mgmt_ctrl.mtp_get_nic_pn(slot) # get the PN format like this 68-0015-02 01 or 0X322F X/A
                pn = pn.split()[0]
                first6_pn = pn[0:7] if "-" in pn else pn[0:6]
                pn = first6_pn
                if pn:
                    break
            if new_cpld_json_dict[pn]["working_imge"]["name"] == new_cpld_json_dict[pn]["secure_imge"]["name"] and new_cpld_json_dict[pn]["working_imge"]["sha512sum"] == new_cpld_json_dict[pn]["secure_imge"]["sha512sum"]:
                test_case_list.append("UFM3_RW_STRESS_FROM_SPI")
            test_case_list.append("RECOVER_BOOT0")

            for test_case in test_case_list:
                if test_case in ("UPGRADE_DOWNGRADE_UTILITY_FUNCTION_STRESS_AND_FAILSAFE_NEGTIVE", "3V3_POWER_CYCLE", "GPIO3_POWER_CYCLE", "AC_POWER_CYCLE"):
                    ##########################################################################################################################################################
                    #  CPLD upgrade and downgrade functional and utility test, Power Cycle Test, Which need console connection to monitor boot, so run one by one sequencially
                    ##########################################################################################################################################################
                    pc_cycles = 50 if test_case == "UPGRADE_DOWNGRADE_UTILITY_FUNCTION_STRESS_AND_FAILSAFE_NEGTIVE" else 100
                    if nic_list:
                        testing_fail_list = cpld_console_seq_test(mtp_mgmt_ctrl,
                                                                    nic_type,
                                                                    nic_list,
                                                                    dsp,
                                                                    test_case,
                                                                    new_cpld_json_dict,
                                                                    stop_on_err,
                                                                    pc_cycles)
                        for slot in testing_fail_list:
                            if slot in nic_list and (test_case == "UPGRADE_DOWNGRADE_UTILITY_FUNCTION_STRESS_AND_FAILSAFE_NEGTIVE" or stop_on_err):
                                nic_list.remove(slot)
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)

                elif test_case == "QSFP_SN_READ_STRESS":
                    ##########################################################################################################################################################
                    #  QSFP Seerial Number Read Stress Test
                    ##########################################################################################################################################################
                    if nic_list:
                        if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, nic_util=True, stop_on_err=stop_on_err):
                            for slot in nic_list:
                                if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                    if slot in nic_list and stop_on_err:
                                        nic_list.remove(slot)
                                    if slot not in fail_nic_list:
                                        fail_nic_list.append(slot)
                                    if slot in pass_nic_list:
                                        pass_nic_list.remove(slot)
                        testing_fail_list = cpld_qsfp_sn_read_stress_test(mtp_mgmt_ctrl, nic_type, nic_list, dsp, test_case, stop_on_err)
                        for slot in testing_fail_list:
                            if slot in nic_list and stop_on_err:
                                nic_list.remove(slot)
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)
                elif test_case == "PROGRAM_SPECIAL_BOOT0":
                    ##########################################################################################################################################################
                    #  Program special boot0, which will read and print the value to console of registers 0x0, 0x1E, 0x80, 0x12 for 10k cycles every boot
                    ##########################################################################################################################################################
                    if nic_list:
                        # get special_boot0_img_file name
                        special_boot0_img_file =  MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + new_cpld_json_dict[pn]["special_boot0_imge"]["name"]
                        boot0_installer_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.uboot_img["INSTALLER"]
                        testing_fail_list = cpld_programe_boot0(mtp_mgmt_ctrl, nic_type, nic_list, dsp, test_case, stop_on_err, special_boot0_img_file, boot0_installer_file)
                        for slot in testing_fail_list:
                            if slot in nic_list and stop_on_err:
                                nic_list.remove(slot)
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)
                elif test_case == "UFM3_RW_STRESS_FROM_SPI":
                    ##########################################################################################################################################################
                    #  CPLD internal flash UFM3 read and write stress tests from SPI
                    ##########################################################################################################################################################
                        if not mtp_mgmt_ctrl.mtp_nic_diag_init(nic_list, nic_util=True, stop_on_err=stop_on_err):
                            for slot in nic_list:
                                if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                                    if slot in nic_list and stop_on_err:
                                        nic_list.remove(slot)
                                    if slot not in fail_nic_list:
                                        fail_nic_list.append(slot)
                                    if slot in pass_nic_list:
                                        pass_nic_list.remove(slot)
                        testing_fail_list = ufm3_read_write_stress_test_from_spi(mtp_mgmt_ctrl, nic_type, nic_list, dsp, test_case, stop_on_err)
                        for slot in testing_fail_list:
                            if slot in nic_list and stop_on_err:
                                nic_list.remove(slot)
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)
                elif test_case == "RECOVER_BOOT0":
                    ##########################################################################################################################################################
                    #  Recover boot0 to MFG released one
                    ##########################################################################################################################################################
                    if not image_control.get_uboot(mtp_mgmt_ctrl, nic_type, dsp)["filename"]:
                        mtp_mgmt_ctrl.cli_log_wrn("No boot0 specified in libmfg_cfg, skip RECOVER_BOOT0", level=0)
                        continue
                    if nic_list:
                        testing_fail_list = cpld_programe_boot0(mtp_mgmt_ctrl, nic_type, nic_list, dsp, test_case, stop_on_err)
                        for slot in testing_fail_list:
                            if slot in nic_list and stop_on_err:
                                nic_list.remove(slot)
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            if slot in pass_nic_list:
                                pass_nic_list.remove(slot)

        # log the diag test history
        mtp_mgmt_ctrl.mtp_mgmt_diag_history_disp()

        # clear the diag test history
        if not stop_on_err:
            mtp_mgmt_ctrl.mtp_mgmt_diag_history_clear()

        diag_sub_dir = "/diag_logs/"
        nic_sub_dir = "/nic_logs/"
        asic_sub_dir = "/asic_logs/"
        # create log dir
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + diag_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + nic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        # save the asic/diag log files
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_DIAG_LOG_FILES, mtp_script_dir + diag_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, mtp_script_dir + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_NIC_LOG_FILES, mtp_script_dir + nic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        # clean up logfiles for the next run
        cmd = "cleanup.sh"
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

        # Enable PCIe poll
        if not stop_on_err:
            if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.CAPRI:
                mtp_mgmt_ctrl.mtp_power_cycle_nic(slot_list=pass_nic_list, dl=False)
                mtp_mgmt_ctrl.cli_log_inf("Wait {:02d} seconds for NIC power up before enable PCIE poll".format(MTP_Const.MTP_PCIE_EN_DIS_DELAY), level=0)
                libmfg_utils.count_down(MTP_Const.MTP_PCIE_EN_DIS_DELAY)
                diag_post_fail_list = diag_reg.mtp_nic_diag_init_post(mtp_mgmt_ctrl, nic_type_full_list, nic_test_full_list, args.skip_test, stage)
                # failed enable pcie poll, fail the card
                for slot in diag_post_fail_list:
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)

        mtp_mgmt_ctrl.cli_log_inf("CPLD Validation Test Complete\n", level=0)

        for slot in pass_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            if not swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES25SWM and (swmtestmode == Swm_Test_Mode.ALOM):
                alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS), level=0)

        for slot in fail_nic_list:
            key = libmfg_utils.nic_key(slot)
            nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            if not swmtestmode == Swm_Test_Mode.ALOM:
                mtp_mgmt_ctrl.cli_log_err("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
            card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
            if card_type == NIC_Type.NAPLES25SWM and (swmtestmode == Swm_Test_Mode.ALOM):
                alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
                mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

        for slot in skip_nic_list:
            key = libmfg_utils.nic_key(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s}".format(key, MTP_DIAG_Report.NIC_DIAG_REGRESSION_SKIP), level=0)

    except Exception as e:
        libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.mtp_diag_fail_report(err_msg)

    diag_reg.mtp_test_cleanup(MTP_DIAG_Error.MTP_DIAG_PASS, open_file_track_list)

if __name__ == "__main__":
    main()
