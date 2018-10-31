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
        self.fmt_con_cmd = "picocom -b {} -f h /dev/ttyS1\n"
        self.fmt_change_rate = "stty speed {}"

    def uart_session_start(self, session, baud=115200):
        cmd = self.fmt_con_cmd.format(baud)
        expstr = ["capri login: ", "\# "]
        try:
            session.send(cmd)
            session.send("\r")
            i = session.expect(expstr, 15)
            if i == 0:
                session.sendline(self.usr)
                session.expect("Password: ")
                session.sendline(self.pwd)
                session.expect("\# ")
        except pexpect.TIMEOUT:
            print "=== TIMEOUT: Can not connect to NIC on UART!"
            return -1

    def uart_session_stop(self, session):
        session.timeout = 15
        try:
            session.sendcontrol('a')
            session.sendcontrol('x')
            session.expect("\$ ")
            return 0
        except pexpect.TIMEOUT:
            print "=== TIMEOUT: Faled to stop UART session ==="
            return -1

    def change_rate(self, orig_rate=115200, tgt_rate=9600):
        session = common.session_start()
        self.uart_session_start(session, orig_rate)

        cmd = self.fmt_change_rate.format(tgt_rate)
        session.sendline(cmd)
        session.sendline("\r")

        self.uart_session_stop(session)
        common.session_stop(session)

    def enable_mgmt(self, rate=9600):
        session = common.session_start()
        self.uart_session_start(session, rate)

        session.timeout = 60
        cmd = "sh /mnt/load_mnic.sh"
        try:
            session.sendline(cmd)
            session.expect("\# ")
        except:
            print "=== TIMEOUT: Faled to enable management port ==="
            return -1

        self.uart_session_stop(session)
        common.session_stop(session)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()

    group.add_argument("-br", "--change_baud_rate", help="Change baud rate", action='store_true')
    group.add_argument("-mgmt", "--ena_mgmt_port", help="Enable managment port", action='store_true')

    parser.add_argument("-or", "--orig_rate", help="Original baud rate", type=int, default=115200)
    parser.add_argument("-tr", "--tgt_rate", help="Target baud rate", type=int, default=9600)
    args = parser.parse_args()
    
    con = nic_con()

    if args.change_baud_rate == True:
        con.change_rate(args.orig_rate, args.tgt_rate)
        sys.exit()

    if args.ena_mgmt_port == True:
        con.enable_mgmt(args.tgt_rate)
        sys.exit()
