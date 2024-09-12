#!/usr/bin/env python

import sys
import re

sys.path.append("../lib")
import common
from nic_con import nic_con
import sal_con

def program_dpu_fru(slot):
    nc = nic_con()
    bash_session = common.session_start()
    uart_session = common.session_start()
    if sal_con.enter_a35_zephyr(slot, uart_session, warm_reset=False):
        print("===== FAILED: slot {} couldn't boot zephyr".format(slot))
        return -1

    nc.uart_session_connect(uart_session, slot, uart_id=0)
    nc.uart_session_cmd(uart_session, "", ending="uart:~\$")

    fn = "eeprom_{}".format(slot)
    cmd = "eeutil -uut=uut_{} -dump -numBytes 256 -fn {}".format(slot, fn)
    common.session_cmd(bash_session, cmd)

    # Write DPU FRU from Zephuy cli
    # Write one byte each time
    numBytes = 256
    for offset in range(numBytes):
        cmd = "od -An -tx1 -j {} -N 1 {}".format(offset, fn)
        common.session_cmd(bash_session, cmd)
        #print ("\n===\n"+bash_session.before+"\n===\n")

        cmd = "i2c write i2c@30000 0x52 {}{}".format(str(hex(offset)[2:]).zfill(4), bash_session.before.splitlines()[-2])
        print(cmd)
        nc.uart_session_cmd(uart_session, cmd, ending="uart:~\$")

    nc.uart_session_cmd(uart_session, "i2c read i2c@30000 0x52 0000", ending="uart:~\$")

    nc.uart_session_stop(uart_session)
    common.session_stop(bash_session)
    return 0


def verify_dpu_fru(slot):
    nc = nic_con()
    uart_session = common.session_start()
    if sal_con.enter_a35_uboot(slot, uart_session, warm_reset=False):
        print("===== FAILED: slot {} couldn't boot zephyr".format(slot))
        return -1
    nc.uart_session_connect(uart_session, slot, uart_id=0)
    nc.uart_session_cmd(uart_session, "i2c md 0x52 0.2 128", ending="DSC#")
    nc.uart_session_stop(uart_session)
    common.session_stop(uart_session)

    bash_session = common.session_start()
    print("===== Original FRU Content =====")
    fn = "eeprom_{}".format(slot)
    cmd = "eeutil -uut=uut_{} -dump -numBytes 256 -fn {}".format(slot, fn)
    common.session_cmd(bash_session, cmd)
    common.session_cmd(bash_session, "hexdump -C " + fn)
    common.session_stop(bash_session)
    return 0
