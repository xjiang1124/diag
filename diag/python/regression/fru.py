#!/usr/bin/env python

import sys
import re

sys.path.append("../lib")
import common
from nic_con import nic_con
import sal_con

def _swap_smbus(slot):
    session = common.session_start()
    common.session_cmd(session, "swap_smbus.sh {}".format(slot))
    common.session_stop(session)

def _program(slot, fru_bus=1, fru_addr=0x52, needs_smbus_swap=False, warm_reset=False):
    ret = 0
    nc = nic_con()
    bash_session = common.session_start()
    uart_session = common.session_start()
    if sal_con.enter_a35_uboot(slot, uart_session, warm_reset=warm_reset):
        print("===== FAILED: slot {} couldn't boot a35 uboot".format(slot))
        return -1

    if needs_smbus_swap:
        _swap_smbus(slot)
    nc.uart_session_connect(uart_session, slot, uart_id=0)
    nc.uart_session_cmd(uart_session, "", ending="DSC# ")
    nc.uart_session_cmd(uart_session, "i2c dev {}".format(fru_bus), ending="DSC#")

    fn = "eeprom_{}".format(slot)
    cmd = "eeutil -uut=uut_{} -dump -numBytes 512 -fn {}".format(slot, fn)
    common.session_cmd(bash_session, cmd)

    # Write DPU FRU from uboot cli
    # Write one byte each time
    numBytes = 512
    for offset in range(numBytes):
        cmd = "od -An -tx1 -j {} -N 1 {}".format(offset, fn)
        common.session_cmd(bash_session, cmd)

        cmd = "i2c mw 0x{:x} {}.2 {}".format(fru_addr, str(hex(offset)[2:]).zfill(4), bash_session.before.splitlines()[-2])
        print(cmd)
        cmdret, output = nc.uart_session_cmd_w_ot(uart_session, cmd, ending="DSC#")
        if cmdret != 0:
            print("FRU PROG command {} failed".format(cmd))
            ret = -1
        if "Error writing the chip" in output:
            print("FRU PROG command {} returned error".format(cmd))
            ret = -1

    cmd = "i2c md 0x{:x} 0.2 0x200".format(fru_addr)
    cmdret, output = nc.uart_session_cmd_w_ot(uart_session, cmd, ending="DSC#")
    if cmdret != 0:
        print("\nFRU PROG command {} failed".format(cmd))
        ret = -1
    if "Error reading the chip" in output:
        print("\nFRU PROG command {} returned error".format(cmd))
        ret = -1

    nc.uart_session_stop(uart_session)
    common.session_stop(bash_session)
    return ret

def _verify(slot, fru_bus=1, fru_addr=0x52, needs_smbus_swap=False, warm_reset=False):
    ret = 0
    nc = nic_con()
    uart_session = common.session_start()
    if sal_con.enter_a35_uboot(slot, uart_session, warm_reset=warm_reset):
        print("===== FAILED: slot {} couldn't boot".format(slot))
        return -1
    if needs_smbus_swap:
        _swap_smbus(slot)
    nc.uart_session_connect(uart_session, slot, uart_id=0)
    nc.uart_session_cmd(uart_session, "i2c dev {}".format(fru_bus), ending="DSC#")
    cmd = "i2c md 0x{:x} 0.2 0x200".format(fru_addr)
    cmdret, output = nc.uart_session_cmd_w_ot(uart_session, cmd, ending="DSC#")
    if cmdret != 0:
        print("\nFRU VERIFY command {} failed".format(cmd))
        ret = -1
    if "Error reading the chip" in output:
        print("\nFRU VERIFY command {} returned error".format(cmd))
        ret = -1
    nc.uart_session_stop(uart_session)
    common.session_stop(uart_session)

    bash_session = common.session_start()
    print("===== Original FRU Content =====")
    fn = "eeprom_{}".format(slot)
    cmd = "eeutil -uut=uut_{} -dump -numBytes 512 -fn {}".format(slot, fn)
    common.session_cmd(bash_session, cmd)
    common.session_cmd(bash_session, "hexdump -C " + fn)
    common.session_stop(bash_session)
    return ret

def program_dpu_fru(slot):
    return _program(slot, 1, 0x52)

def verify_dpu_fru(slot):
    return _verify(slot, 1, 0x52)

def program_2nd_pcie_fru(slot):
    return _program(slot, 2, 0x57, needs_smbus_swap=True)

def verify_2nd_pcie_fru(slot):
    return _verify(slot, 2, 0x57, needs_smbus_swap=True)
