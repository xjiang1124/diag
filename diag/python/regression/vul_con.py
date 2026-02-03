#!/usr/bin/env python

import argparse
import pexpect
import os
import sys
import time
import re

sys.path.append("../lib")
#import common
from nic_con import nic_con

class vul_con:

    def sendline_bytewise(self, session, line):
        for b in line:
            session.send(b)
        session.send('\r')
        session.send('\n')

    def uart_session_cmd_w_ot(self, session, cmd, timeout=30, ending="\#"):
        temp = session.timeout
        session.timeout = timeout
        ret = 0
        try:
            self.sendline_bytewise(session, cmd)
            session.expect(ending)
        except:
            print("=== TIMEOUT:", cmd, "===")
            session.send(chr(3))
            time.sleep(0.05)
            session.expect(ending)
            ret = -1
        session.timeout = temp
        return[ret, session.before]

    def usb_uart_session_connect(self, session, slot, timeout=15, uart_id="0"):
        ret = 0
        nc = nic_con()
        cmd = nc.get_connect_cmd(slot, uart_id=uart_id)
        expstr = "Terminal ready"
        errorstr1 = "cannot open /dev/SUCUART"
        errorstr2 = "cannot open /dev/ttySuC"
        retries = 20
        retry_delay = 1
        for attempt in range(retries):
            try:
                print("Attemp {} to connect...".format(attempt + 1))
                #session.sendline(cmd)
                self.sendline_bytewise(session, cmd)
                index = session.expect([expstr, errorstr1, errorstr2, pexpect.TIMEOUT], timeout)
                if index == 0:
                    # Connection successful
                    ret = 0
                    break
                elif index == 1 or index == 2:
                    if attempt < retries - 1:
                        print("SUCUART not ready. Retry in {} seconds...".format(retry_delay))
                        time.sleep(retry_delay)
                    else:
                        print("SUCUART not ready, exit")
                    ret = -1
                elif index == 3:
                    print("=== TIMEOUT: Failed to connect console.")
                    ret = -1
            except Exception as e:
                print("=== Exception occurred: {}".format(e))
                ret = -1
        if ret != 0:
            return -1
        try:
            #session.sendline("\r\n")
            #session.sendline("")
            self.sendline_bytewise(session, "")
            while True:
                index = session.expect(["uart:~\$", "suc:~\$", pexpect.TIMEOUT], 1)
                if index == 0 or index == 1:
                    # Console prompt detected
                    continue
                elif index == 2:
                    # No more prompts detected
                    break
        except pexpect.TIMEOUT:
            # didn't detect any prompt
            print("=== TIMEOUT: Failed to detect console prompt")
            ret = -1
        return ret