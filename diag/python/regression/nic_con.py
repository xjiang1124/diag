#!/usr/bin/env python

import argparse
import pexpect
import re
import sys
import time
from time import sleep

sys.path.append("../lib")
import common

class nic_con:
    def __init__(self):
        self.usr = "root"
        self.pwd = "pen123"
        self.fmt_con_cmd = "picocom -q -b {} -f h /dev/ttyS1"
        self.fmt_change_rate = "stty speed {}"

    def uart_session_start(self, session, baud=115200):
        ret = 0
        cmd = self.fmt_con_cmd.format(baud)
        expstr = ["capri login:", "\#"]
        session.sendline(cmd)
        for ite in range(2):
            print "ite: ", ite
            if ite == 2:
                # Vomero case, may need two tims
                timeout = 30
                print "Last try to connenct UART, wait for", timeout, "sec"
            else:
                timeout = 1

            try:
                #session.expect("Terminal ready")
                session.send("\r")

                i = session.expect(expstr, timeout)
                if i == 0:
                    session.sendline(self.usr)
                    session.expect("assword:")
                    session.sendline(self.pwd)
                    session.expect("\#")
                ret = 0
                break
            except pexpect.TIMEOUT:
                print "=== TIMEOUT: Can not connect to NIC on UART!"
                ret = -1
        return ret

    def uart_session_start_slot(self, session, baud=115200, slot=0):
        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            return -1

        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 

        cmd = self.fmt_con_cmd.format(baud)
        expstr = ["capri login:", "\#"]
        try:
            session.sendline(cmd)
            #session.expect("Terminal ready")
            session.send("\r")
            i = session.expect(expstr, 15)
            if i == 0:
                session.sendline(self.usr)
                session.expect("assword:")
                session.sendline(self.pwd)
                session.expect("\#")
        except pexpect.TIMEOUT:
            print "=== TIMEOUT: Can not connect to NIC on UART!"
            return -1
        return 0

    def uart_session_stop(self, session):
        session.timeout = 15
        try:
            session.sendcontrol('a')
            session.sendcontrol('x')
            session.expect("\$")
            return 0
        except pexpect.TIMEOUT:
            print "=== TIMEOUT: Faled to stop UART session ==="
            return -1

    def uart_session_cmd_sig(self, session, cmd, timeout=30, ending="\#", sig=["PASS", "FAIL"], verbose=True):
        temp = session.timeout
        session.timeout = timeout
        ret = -1
        try:
            session.sendline(cmd)
            i = session.expect(sig)
            ret = i

        except:
            if verbose == True:
                print "=== TIMEOUT:", cmd, "==="
            session.send(chr(3))
            time.sleep(0.05)
            session.expect(ending)
            ret = -1
        session.timeout = temp
        return ret

    def uart_session_cmd(self, session, cmd, timeout=30, ending="\#"):
        temp = session.timeout
        session.timeout = timeout
        ret = 0
        try:
            session.sendline(cmd)
            session.expect(ending)
        except:
            print "=== TIMEOUT:", cmd, "==="
            session.send(chr(3))
            time.sleep(0.05)
            session.expect(ending)
            ret = -1
        session.timeout = temp
        return ret

    def power_cycle_uart(self, baud_rate=115200, slot=0):
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        numRetry = 3

        session = common.session_start()
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(1)

        for i in range(numRetry):
            cmd = "turn_on_slot.sh off {}".format(slot)
            common.session_cmd(session, cmd)
            cmd = "turn_on_slot.sh on {}".format(slot)
            common.session_cmd(session, cmd)

            # Wait for nic to boot
            time.sleep(30)

            print "=== Start Uart Session {} ===".format(i)
            ret = self.uart_session_start(session, baud_rate)
            if ret == 0:
                break
            self.uart_session_stop(session)

        self.uart_session_stop(session)
        common.session_stop(session)
        return ret


    def power_cycle_multi(self, baud_rate=115200, slot_list="", wtime=30):
        ret = 0
        session = common.session_start()

        #cmd = "turn_on_slot_multi.sh off {}".format(slot_list)
        cmd = "turn_on_slot.sh off {}".format(slot_list)
        common.session_cmd(session, cmd)
        #cmd = "turn_on_slot_multi.sh on {}".format(slot_list)
        cmd = "turn_on_slot.sh on {}".format(slot_list)
        common.session_cmd(session, cmd)

        # Wait for nic to boot
        print "Wait", wtime, "after power cycle"
        time.sleep(wtime)

        common.session_stop(session)
        return ret

    def enter_uboot(self, session, slot=0, rate=115200, timeout=30):
        ret = -1
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        numRetry = 3

        session.timeout = timeout
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(1)
        for retry in range(3):
            print "Trying enter uboot {}".format(retry)
            cmd = "turn_on_slot.sh off {}".format(slot)
            common.session_cmd(session, cmd) 
            cmd = "turn_on_slot.sh on {}".format(slot)
            common.session_cmd(session, cmd) 
            #time.sleep(2)
            cmd = self.fmt_con_cmd.format(rate)
            session.sendline(cmd)
            #session.expect("Terminal ready")

            for i in range(40):
                session.timeout = 0.5
                try:
                    print "C+C", i
                    session.send(chr(3))
                    session.expect("Capri# ")
                    #time.sleep(1)
                    ret = 0
                    break
                except pexpect.TIMEOUT:
                    print "timeout:", i
                    ret = -1
            self.uart_session_stop(session)
            if ret == 0:
                break

        if ret == -1:
            print "=== Failed to enter uboot ==="
        return ret

    def enter_uboot_after_reset(self, session, slot=0, rate=115200, timeout=30,):
        ret = -1
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        session.timeout = timeout

        for i in range(60):
            session.timeout = 0.3
            try:
                print "C+C", i
                session.send(chr(3))
                session.expect("Capri# ")
                #time.sleep(1)
                ret = 0
                break
            except pexpect.TIMEOUT:
                print "timeout:", i
                ret = -1

	return ret

    def conn_uboot(self, session, rate=115200):
        exprStr = "Capri# "
        session.timeout = 15
        ret = 0
        try:
            cmd = self.fmt_con_cmd.format(rate)
            session.sendline(cmd)
            #session.expect("Terminal ready")
            session.sendline("\r")
            session.expect(exprStr)
        except pexpect.TIMEOUT:
            print "Failed to connet uboot"
            self.uart_session_stop(session)
            ret = -1
        return ret

    def mtest_uboot(self, baud_rate=115200, slot=0):
        err = 0
        numRetry = 3
        session = common.session_start()
        ret = self.enter_uboot(session, slot, baud_rate)
        if ret == -1:
            print "=== Failed to change uboot board rate! ==="
            print "=== MTEST FAILED ==="
            return ret

        exprStr = "Capri# "
        mtest_cmd = "mtest {} {} 0xaaaaaaaa 1"
        session.timeout = 30
        try:
            cmd = self.fmt_con_cmd.format(baud_rate)
            #session.sendline(cmd)
            #session.expect("Terminal ready")
            #time.sleep(1)
            session.send("\r")
            session.expect(exprStr)

            session.sendline("bdinfo")
            session.expect(exprStr)

            start = "0xC0000000"
            if "start    = 0x140000000" in session.before:
                print "=== 4G HBM detected ==="
                end = "0x17fffffff"
                timeout = 60
            elif "start    = 0x240000000" in session.before:
                print "=== 8G HBM detected ==="
                end = "0x27fffffff"
                timeout = 150

            session.timeout = 30
            cmd = mtest_cmd.format("0x80000000", "0xBE9FFFFF")
            session.sendline(cmd)
            session.expect(exprStr)
            if "with 0 errors" in session.before:
                print "=== MTEST PASSED LOW 1G ==="
            else:
                print "=== MTEST FAILED LOW 1G ==="
                err = err + 1

            session.timeout = timeout
            cmd = mtest_cmd.format(start, end)
            session.sendline(cmd)
            session.expect(exprStr)
            if "with 0 errors" in session.before:
                print "=== MTEST PASSED HIGH 3G ==="
            else:
                print "=== MTEST FAILED HIGH 3G ==="
                err = err + 1

        except pexpect.TIMEOUT:
            print "=== TIMEOUT: Faled to perform uboot mtest ==="
            err = -1

        if err == 0:
            print "=== MTEST PASSED ==="
        else:
            print "=== MTEST FAILED ==="

        self.uart_session_stop(session)
        common.session_stop(session)

    def enable_mnic(self, rate=115200, slot=0, first_pwr_on=False):
        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            return -1

        session = common.session_start()
        self.uart_session_start(session, rate)

        session.timeout = 60

        cmd_pre = "ulimit -c unlimited"
        cmd_mac = "echo \'00:11:22:33:{:02}:00\' > /sysconfig/config0/sysuuid"
        cmd_mac = cmd_mac.format(slot)
        #print "MAC:", cmd_mac
        if first_pwr_on == True:
            self.uart_session_cmd(session, "cd /nic/conf/")
            self.uart_session_cmd(session, "cp catalog_hw_68-0003.json catalog_hw_")

        try:
            session.sendline("ifconfig -a")
            session.expect("\#")
            temp = session.after
            if 'oob_mnic0' in session.before:
                print 'oob_mnic0 enabled'
            else:
                self.uart_session_cmd(session, cmd_pre)
                self.uart_session_cmd(session, cmd_mac)
                self.uart_session_cmd(session, "sysinit.sh classic hw diag", 15)

        except pexpect.TIMEOUT:
            print "=== TIMEOUT: Faled to enable management port ==="
            ret = -1

        self.uart_session_stop(session)
        common.session_stop(session)
        return ret

    def config_mnic(self, rate=115200, slot=0):
        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            return -1

        session = common.session_start()
        self.uart_session_start(session, rate)

        session.timeout = 30

        try:
            session.sendline("ifconfig -a")
            session.expect("\#")
            temp = session.after
            if 'oob_mnic0' in session.before:
                print 'oob_mnic0 enabled'
                self.uart_session_cmd(session, "ifconfig oob_mnic0 10.1.1.{} netmask 255.255.255.0".format(slot+100))
                self.uart_session_cmd(session, "ifconfig")
            else:
                print 'oob_mnic0 NOT enabled!'
                ret = 1

        except pexpect.TIMEOUT:
            self.uart_session_stop(session)
            print "=== TIMEOUT: Faled to config management port ==="
            ret = -1

        self.uart_session_stop(session)
        common.session_stop(session)
        return ret

    def turn_off_sgmii(self, slot=0):
        cmd = "swm_dis_sgmii.sh {}".format(slot)

        session = common.session_start()
        common.session_cmd(session, cmd)
        common.session_stop(session)

    def get_mgmt_rdy(self, rate, slot=0, first_pwr_on=False, skip_enable=False):
        numRetry = 6
        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            return -1

        self.switch_console(slot)

        if skip_enable == False:
            ret = self.enable_mnic(rate, slot, first_pwr_on)
            if ret != 0:
                print "=== FAIL to enable management port! ==="
                return ret

        for i in range(numRetry):
            ret = self.config_mnic(rate, slot)
            if ret == -1:
                print "=== FAIL to enable management port! ==="
                return ret
            elif ret == 0:
                break

            time.sleep(10)

        if ret != 0:
            print "=== FAIL to enable management port! Max retry reached!"
            return -1
        else:
            print "=== Management port is ready ==="
            return ret

    def disable_pcie_uboot(self, slot):
        ret = 0
        session = common.session_start()
        ret = self.enter_uboot(session, slot)
        if ret != 0:
            print "Failed to enter uboot"
            return ret
        ret = self.conn_uboot(session)
        if ret != 0:
            print "Failed to connect uboot"
            return ret

        self.uart_session_cmd(session, "setenv pcie_poll_disable 1", 30, "Capri# ")
        self.uart_session_cmd(session, "saveenv", 30, "Capri# ")
        self.uart_session_cmd(session, "saveenv", 30, "Capri# ")
        self.uart_session_stop(session)
        common.session_stop(session)
        return ret

    def enable_pcie_uboot(self, slot):
        ret = 0
        session = common.session_start()
        ret = self.enter_uboot(session, slot)
        if ret != 0:
            print "Failed to enter uboot"
            return ret
        ret = self.conn_uboot(session)
        if ret != 0:
            print "Failed to connect uboot"
            return ret

        self.uart_session_cmd(session, "setenv pcie_poll_disable", 30, "Capri# ")
        self.uart_session_cmd(session, "saveenv", 30, "Capri# ")
        self.uart_session_cmd(session, "saveenv", 30, "Capri# ")
        self.uart_session_stop(session)
        common.session_stop(session)
        return ret

    def switch_console(self, slot=0):
        if int(slot) > 10:
            print "Invalide slot {}!".format(slot)
            return -1

        session = common.session_start()
        cmd = "cpldutil -cpld-wr -addr=0x18 -data=0"
        common.session_cmd(session, cmd)
        sleep(0.5)
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        sleep(0.5)
        common.session_cmd(session, cmd)
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()

    group.add_argument("-mgmt", "--ena_mgmt_port", help="Enable managment port", action='store_true')
    group.add_argument("-mtest", "--mtest", help="Change baud rate", action='store_true')
    group.add_argument("-dis_pcie", "--dis_pcie", help="Disable PCIe", action='store_true')
    group.add_argument("-ena_pcie", "--ena_pcie", help="Enable PCIe", action='store_true')

    parser.add_argument("-br", "--baud_rate", help="Original baud rate", type=int, default=115200)
    parser.add_argument("-slot", "--slot", help="NIC slot number", type=int, default=0)
    parser.add_argument("-ping", "--ping", help="Ping test before enable management port", action='store_true')
    parser.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    args = parser.parse_args()
    
    con = nic_con()

    if args.ena_mgmt_port == True:
        con.get_mgmt_rdy(args.baud_rate, args.slot, args.first_pwr_on)
        sys.exit()

    if args.mtest == True:
        con.mtest_uboot(args.baud_rate, args.slot)
        sys.exit()

    if args.dis_pcie == True:
        con.disable_pcie_uboot(args.slot)
        sys.exit()

    if args.ena_pcie == True:
        con.enable_pcie_uboot(args.slot)
        sys.exit()
