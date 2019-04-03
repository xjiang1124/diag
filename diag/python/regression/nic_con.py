#!/usr/bin/env python

import argparse
import pexpect
import re
import sys
import time

sys.path.append("../lib")
import common

class nic_con:
    def __init__(self):
        self.usr = "root"
        self.pwd = "pen123"
        self.fmt_con_cmd = "picocom -b {} -f h /dev/ttyS1"
        self.fmt_change_rate = "stty speed {}"

    def uart_session_start(self, session, baud=115200):
        cmd = self.fmt_con_cmd.format(baud)
        expstr = ["capri login:", "\#"]
        try:
            session.sendline(cmd)
            session.expect("Terminal ready")
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

    def uart_session_cmd_sig(self, session, cmd, timeout=30, ending="\#", sig=["PASS", "FAIL"]):
        temp = session.timeout
        session.timeout = timeout
        ret = -1
        try:
            session.sendline(cmd)
            i = session.expect(sig)
            ret = i

        except:
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
            for i in range(10):
                cmd = "picocom -b {} -f h /dev/ttyS1".format(rate)
                session.sendline(cmd)
                session.expect("Terminal ready")
                #time.sleep(1)
                session.timeout = 3
                try:
                    print "C+C", i
                    #session.send("\r")
                    session.send(chr(3))
                    session.expect("Capri# ")
                    time.sleep(5)
                    self.uart_session_stop(session)
                    ret = 0
                    break
                except pexpect.TIMEOUT:
                    ret = -1
                    self.uart_session_stop(session)
            if ret == 0:
                break

        if ret == -1:
            print "=== Failed to enter uboot ==="
        return ret

    def conn_uboot(self, session, rate=115200):
        exprStr = "Capri# "
        session.timeout = 15
        ret = 0
        try:
            cmd = "picocom -b {} -f h /dev/ttyS1".format(rate)
            session.sendline(cmd)
            session.expect("Terminal ready")
            time.sleep(1)
            session.send("\r")
            session.expect(exprStr)
        except pexpect.TIMEOUT:
            self.uart_session_stop(session)
            ret = -1
        return ret

    def change_rate_uboot_i(self, session, orig_rate=115200, tgt_rate=9600, save=False):
        if orig_rate == tgt_rate:
            print "=== No need to change baud rate ==="
            return 0

        exprStr = "Capri# "
        ret = 0
        session.timeout=15
        try:
            ret = self.conn_uboot(session, orig_rate)
            if ret != 0:
                return ret
            cmd = "setenv bootargs earlycon=uart8250,mmio32,0x4800 console=ttyS0,{}n8".format(tgt_rate)
            session.sendline(cmd)
            session.expect(exprStr)
            self.uart_session_stop(session)

            ret = self.conn_uboot(session, orig_rate)
            if ret != 0:
                return ret
            cmd = "setenv baudrate {}".format(tgt_rate)
            session.sendline(cmd)
            session.expect("press ENTER")
            #self.uart_session_cmd(session, cmd, 3, "press ENTER")

            self.uart_session_stop(session)

            if save == True:
                ret = self.conn_uboot(session, tgt_rate)
                if ret != 0:
                    return ret
                self.uart_session_cmd(session, "saveenv", 10, exprStr)
                session.send("reset\r")
                time.sleep(1)
                self.uart_session_stop(session)
                

        except pexpect.TIMEOUT:
            print "=== TIMEOUT: Faled to change uboot baud rate ==="
            self.uart_session_stop(session)
            ret = -1
        return ret


    def change_rate_uboot(self, orig_rate=115200, tgt_rate=9600, slot=0, save=False):
        numRetry = 3
        if orig_rate == tgt_rate:
            print "=== No need to change baud rate ==="
            return 0

        session = common.session_start()
        for i in range(numRetry):
            print "=== Enter uboot", i, " ==="
            ret = self.enter_uboot(session, slot, orig_rate)

            if ret == 0:
                break

            common.session_stop(session)
            if i == numRetry-1:
                print "=== Failed to enter uboot ==="
                return -1

        time.sleep(15)

        ret = self.change_rate_uboot_i(session, orig_rate, tgt_rate, save)
        common.session_stop(session)
        return ret

    def mtest_uboot(self, orig_rate=115200, tgt_rate=9600, slot=0):
        err = 0
        numRetry = 3
        #session = common.session_start()
        #self.enter_uboot(session, slot, orig_rate)
        #time.sleep(15)
        #ret = self.change_rate_uboot_i(session, orig_rate, tgt_rate, False)
        #if ret != 0:
        #    print "=== MTEST FAILED ==="
        #    return -1
        for i in range(numRetry):
            print "=== Change uboot rate", i, " ==="
            ret = self.change_rate_uboot(orig_rate, tgt_rate, slot)
            if ret == 0:
                break
        if ret == -1:
            print "=== Failed to change uboot board rate! ==="
            print "=== MTEST FAILED ==="
            return ret

        session = common.session_start()
        exprStr = "Capri# "
        mtest_cmd = "mtest {} {} 0xaaaaaaaa 1"
        session.timeout = 30
        try:
            cmd = "picocom -b {} -f h /dev/ttyS1".format(tgt_rate)
            session.sendline(cmd)
            session.expect("Terminal ready")
            time.sleep(1)
            session.send("\r")
            #session.send("\r")
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

    def change_rate_pw(self, orig_rate=115200, tgt_rate=9600, slot=0):
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
            time.sleep(15)

            print "=== Start Uart Session {} ===".format(i)
            ret = self.uart_session_start(session, orig_rate)
            if ret == 0:
                break

            self.uart_session_stop(session)

        if ret == 0:
            cmd = self.fmt_change_rate.format(tgt_rate)
            session.sendline(cmd)
            session.sendline("\r")
            self.uart_session_stop(session)

        common.session_stop(session)
        return ret

    def change_rate(self, orig_rate=115200, tgt_rate=9600, slot=0):
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        session = common.session_start()
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(1)

        ret = self.uart_session_start(session, orig_rate)
        if ret == 0:
            cmd = self.fmt_change_rate.format(tgt_rate)
            session.sendline(cmd)
            session.sendline("\r")

        self.uart_session_stop(session)
        common.session_stop(session)

    def enable_mnic(self, rate=9600, slot=0):
        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            return -1

        session = common.session_start()
        self.uart_session_start(session, rate)

        session.timeout = 60

        cmd_pre = "ulimit -c unlimited"
        cmd_mac = "echo \'00:11:22:33:44:{:02}\' > /sysconfig/config0/sysuuid"
        cmd_mac = cmd_mac.format(slot)
        #print "MAC:", cmd_mac

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
            self.uart_session_stop(session)
            print "=== TIMEOUT: Faled to enable management port ==="
            ret = -1

        self.uart_session_stop(session)
        common.session_stop(session)
        return ret

    def config_mnic(self, rate=9600, slot=0):
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
            else:
                print 'oob_mnic0 NOT enabled!'
                ret = 1

        except pexpect.TIMEOUT:
            self.uart_session_stop(session)
            print "=== TIMEOUT: Faled to enable management port ==="
            ret = -1

        self.uart_session_stop(session)
        common.session_stop(session)
        return ret

    def get_mgmt_rdy(self, rate, slot=0):
        numRetry = 6
        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            return -1

        session = common.session_start()
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(1)
        common.session_stop(session)

        ret = self.enable_mnic(rate, slot)
        if ret != 0:
            print "=== FAIL to enable management port! ==="
            return ret

        for i in range(numRetry):
            time.sleep(10)
            ret = self.config_mnic(rate, slot)
            if ret == -1:
                print "=== FAIL to enable management port! ==="
                return ret
            elif ret == 0:
                break

            if i == (numRetry-1):
                print "=== FAIL to enable management port! Max retry reached!"
                return -1

        print "=== Management port is ready ==="
        return ret

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()

    group.add_argument("-br", "--change_baud_rate", help="Change baud rate", action='store_true')
    group.add_argument("-mgmt", "--ena_mgmt_port", help="Enable managment port", action='store_true')
    group.add_argument("-mtest", "--mtest", help="Change baud rate", action='store_true')

    parser.add_argument("-or", "--orig_rate", help="Original baud rate", type=int, default=115200)
    parser.add_argument("-tr", "--tgt_rate", help="Target baud rate", type=int, default=9600)
    parser.add_argument("-slot", "--slot", help="NIC slot number", type=int, default=0)
    parser.add_argument("-ping", "--ping", help="Ping test before enable management port", action='store_true')
    parser.add_argument("-old", "--old", help="New management port configure", action='store_true')
    parser.add_argument("-uboot", "--uboot", help="Uboot operations", action='store_true')
    parser.add_argument("-save", "--save", help="Save uboot settings", action='store_true')
    args = parser.parse_args()
    
    con = nic_con()

    if args.change_baud_rate == True:
        if args.uboot == True:
            con.change_rate_uboot(args.orig_rate, args.tgt_rate, args.slot, args.save)
        else:
            con.change_rate(args.orig_rate, args.tgt_rate, args.slot)
        sys.exit()

    if args.ena_mgmt_port == True:
        con.get_mgmt_rdy(args.tgt_rate, args.slot)
        sys.exit()

    if args.mtest == True:
        con.mtest_uboot(args.orig_rate, args.tgt_rate, args.slot)
        sys.exit()
