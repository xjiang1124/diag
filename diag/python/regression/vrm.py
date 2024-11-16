#!/usr/bin/env python

import sys
import re
import time

sys.path.append("../lib")
import common
from nic_con import nic_con
import sal_con

def vrm_uboot_cmd(uart_session, cmd):
    print(cmd)
    cmdret, output = nc.uart_session_cmd_w_ot(uart_session, cmd, ending="DSC#")
    if cmdret != 0:
        print("Command {} failed".format(cmd))
        return -1
    if "Error writing the chip" in output or "Error reading the chip" in output:
        print("Command {} returned error".format(cmd))
        return -1
    return 0

def vrm_zephyr_cmd(uart_session, cmd):
    ret = 0
    nc = nic_con()
    cmdret, output = nc.uart_session_cmd_w_ot(uart_session, cmd, ending="uart:~\$")
    if cmdret != 0:
        print("Command {} failed".format(cmd))
        ret = -1
    if "Failed to" in output:
        print("Command {} returned error".format(cmd))
        ret = -1
    return ret, output

def verify_smbalert_mask(slot, warm_reset=False):
    ret = 0
    nc = nic_con()
    uart_session = common.session_start()
    if sal_con.enter_a35_zephyr(slot, uart_session, warm_reset=warm_reset):
        print("===== FAILED: slot {} couldn't boot zephyr".format(slot))
        ret = -1
    nc.uart_session_connect(uart_session, slot, uart_id=0)
    nc.uart_session_cmd(uart_session, "help", ending="uart:~\$")

    if ret == 0:
        ## Cannot check COMM and CML_OTHER as i2c driver doesnt support BlockProcessRead
        ## Check RD_GRP is masked
        cmd = "i2c read i2c@30000 0x60 0xCF 8" # read 7 bytes, first return byte contains length
        cmdret, output = vrm_zephyr_cmd(uart_session, cmd)
        if cmdret != 0:
            ret = -1
        if "07 00 00 00 00 00 00 20" not in output:
            # not programmed, needs programming
            ret = 1

    nc.uart_session_stop(uart_session)
    return ret

def prog_smbalert_mask(slot, warm_reset=False):
    ret = 0
    nc = nic_con()
    uart_session = common.session_start()
    # Start with powercycle is required
    # to reset VRM to default settings,
    # make sure no extra settings get saved
    # except the ones changed in this session
    if sal_con.enter_a35_zephyr(slot, uart_session, warm_reset=warm_reset):
        print("===== FAILED: slot {} couldn't boot zephyr".format(slot))
        return -1
    ret = nc.uart_session_connect(uart_session, slot, uart_id=0)
    if ret != 0:
        print("=== Failed to connect")
        return ret
    # nc.uart_session_cmd(uart_session, "help", ending="uart:~\$")

    if ret == 0:
        print("\n====== Masking COMM and CML_OTHER faults\n")
        # Write word - CMD Address: 0x1B, Address Pointer = 7E, Mask = 03
        cmd = "i2c write i2c@30000 0x60 0x1B 0x7E 0x3"
        ret, _ = vrm_zephyr_cmd(uart_session, cmd)

    if ret == 0:
        print("\n====== Masking EXT fault\n")
        # Write word - CMD Address: 0x1B, Address pointer = 80, Mask = 46
        cmd = "i2c write i2c@30000 0x60 0x1B 0x80 0x46"
        ret, _ = vrm_zephyr_cmd(uart_session, cmd)

    if ret == 0:
        print("\n====== Write all registers to NVM\n")
        # Send byte - CMD Address: 0x15
        cmd = "i2c write i2c@30000 0x60 0x15"
        ret, _ = vrm_zephyr_cmd(uart_session, cmd)
        time.sleep(0.1) # 100ms to guarantee storage

    nc.uart_session_stop(uart_session)
    return ret

def mask_smbalert(slot, warm_reset=False):
    ### No way to verify from zephyr currently.
    # if 0 == verify_smbalert_mask(slot, warm_reset=warm_reset):
    #     print("\n====== VRM already has correct mask settings. Skipping test\n")
    #     return 0

    if 0 != prog_smbalert_mask(slot, warm_reset=warm_reset):
        print("\n====== FAILED to program SMB_ALERT mask\n")
        return -1

    ### No way to verify from zephyr currently.
    # if 0 == verify_smbalert_mask(slot, warm_reset=warm_reset):
    #     print("\n====== New VRM mask verified\n")
    #     return 0
    # else:
    #     print("\n====== New VRM settings failed to apply\n")
    #     return -1
    return 0
