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

    def uart_session_cmd(self, session, cmd, timeout=30, ending="\#"):
        session.timeout = timeout
        try:
            session.sendline(cmd)
            session.expect(ending)
        except:
            print "=== TIMEOUT:", cmd, "==="
            session.send(chr(3))
            time.sleep(0.05)
            session.expect(ending)
            return -1

    def change_rate(self, orig_rate=115200, tgt_rate=9600, slot=0):
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        session = common.session_start()

        cmd = "cpldutil -cpld-wr -addr=0x18 -data=0"
        common.session_cmd(session, cmd) 
        time.sleep(3)
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(3)

        self.uart_session_start(session, orig_rate)

        cmd = self.fmt_change_rate.format(tgt_rate)
        session.sendline(cmd)
        session.sendline("\r")

        self.uart_session_stop(session)
        common.session_stop(session)

    def get_mgmt_rdy(self, rate=9600, slot=0, ping=False, pre_cl=False):
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        print "ping:", ping

        session = common.session_start()
        session.timeout = 30
        if ping == True:
            session.sendline("ping -w3 10.1.1.{}".format(100+slot))
            session.expect("\$")
            if ", 0% packet loss" not in session.before:
                self.enable_mgmt(rate, slot, True)
        else:
            self.enable_mgmt(rate, slot, pre_cl)

        session = common.session_stop(session)

    def enable_mgmt(self, rate=9600, slot=0, pre_cl=False):
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        session = common.session_start()

        cmd = "cpldutil -cpld-wr -addr=0x18 -data=0"
        common.session_cmd(session, cmd) 
        time.sleep(3)
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(3)

        self.uart_session_start(session, rate)

        session.timeout = 60
        if pre_cl == True:
            self.uart_session_cmd(session, "rmmod ionic-mnic", 30)

        cmd = "sh /mnt/load_mnic.sh"
        try:
            for i in range(10):

                session.sendline("ifconfig -a")
                session.expect("\#")
                temp = session.after
                if 'eth0' in session.before:
                    print 'eth0 enabled'
                    break
                else:
                    self.uart_session_cmd(session, "rmmod ionic-mnic", 30)

                    # Depending on different version of QSPI, there are two different method
                    self.uart_session_cmd(session, "sh /platform/tools/load_mnic.sh", 120)

                    session.sendline("ifconfig -a")
                    session.expect("\#")
                    temp = session.after
                    if 'eth0' in session.before:
                        print 'eth0 enabled'
                        break

                    self.uart_session_cmd(session, "echo \"#! /bin/sh\" > /mnt/load_mnic.sh")
                    self.uart_session_cmd(session, "echo \"insmod /platform/ionic_mnic.ko\" >> /mnt/load_mnic.sh")
                    self.uart_session_cmd(session, "echo \"tx_intr=\`cat /proc/interrupts | grep ionic-lif0-tx | cut -d\':\' -f1 | cut -d\' \' -f2\`\" >> /mnt/load_mnic.sh")
                    self.uart_session_cmd(session, "echo \"echo 8 > /proc/irq/\$tx_intr/smp_affinity\" >> /mnt/load_mnic.sh")
                    self.uart_session_cmd(session, "echo \"echo 8 > /sys/class/net/eth0/queues/tx-0/xps_cpus\" >> /mnt/load_mnic.sh")
                    self.uart_session_cmd(session, "echo \"rx_intr=\`cat /proc/interrupts | grep ionic-lif0-rx | cut -d\':\' -f1 | cut -d\' \' -f2\`\" >> /mnt/load_mnic.sh")
                    self.uart_session_cmd(session, "echo \"echo 4 > /proc/irq/\$rx_intr/smp_affinity\" >> /mnt/load_mnic.sh")
                    self.uart_session_cmd(session, "echo \"echo 4 > /sys/class/net/eth0/queues/rx-0/rps_cpus\" >> /mnt/load_mnic.sh")
                    self.uart_session_cmd(session, "sync")
                    self.uart_session_cmd(session, "sh /mnt/load_mnic.sh", 120)

            # Configure IP
            self.uart_session_cmd(session, "ifconfig eth0 10.1.1.{} netmask 255.255.255.0".format(slot+100))

        except pexpect.TIMEOUT:
            self.uart_session_stop(session)
            print "=== TIMEOUT: Faled to enable management port ==="
            return -1

        self.uart_session_stop(session)
        print temp
        common.session_stop(session)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()

    group.add_argument("-br", "--change_baud_rate", help="Change baud rate", action='store_true')
    group.add_argument("-mgmt", "--ena_mgmt_port", help="Enable managment port", action='store_true')

    parser.add_argument("-or", "--orig_rate", help="Original baud rate", type=int, default=115200)
    parser.add_argument("-tr", "--tgt_rate", help="Target baud rate", type=int, default=9600)
    parser.add_argument("-slot", "--slot", help="NIC slot number", type=int, default=0)
    parser.add_argument("-ping", "--ping", help="Ping test before enable management port", action='store_true')
    parser.add_argument("-pre_cl", "--pre_cl", help="Pre-clean before enable management port", action='store_true')
    args = parser.parse_args()
    
    con = nic_con()

    if args.change_baud_rate == True:
        con.change_rate(args.orig_rate, args.tgt_rate, args.slot)
        sys.exit()

    if args.ena_mgmt_port == True:
        #con.enable_mgmt(args.tgt_rate, args.slot)
        con.get_mgmt_rdy(args.tgt_rate, args.slot, args.ping, args.pre_cl)
        sys.exit()
