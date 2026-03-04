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
        # Convert string to list for consistency with pexpect.expect()
        if isinstance(ending, str):
            ending = [ending]
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
        return [ret, session.before]

    def vul_uart_session_connect(self, session, slot, timeout=15, uart_id="1"):
        ret = 0
        nc = nic_con()
        cmd = "con_connect.sh {} {}".format(slot, uart_id)
        expstr = "Terminal ready"
        errorstr1 = "cannot open /dev/SUCUART"
        errorstr2 = "cannot open /dev/ttySuC"
        errorstr3 = "cannot open /dev/ttyVul"
        retries = 10
        retry_delay = 1
        console_prompt = 0
        for attempt in range(retries):
            try:
                print("Attempt {} to connect...".format(attempt + 1))
                #session.sendline(cmd)
                self.sendline_bytewise(session, cmd)
                index = session.expect([expstr, errorstr1, errorstr2, errorstr3, pexpect.TIMEOUT], timeout)
                if index == 0:
                    # Connection successful
                    ret = 0
                    break
                elif index == 1 or index == 2 or index == 3:
                    if attempt < retries - 1:
                        print("uart console not ready. Retry in {} seconds...".format(retry_delay))
                        time.sleep(retry_delay)
                    else:
                        print("uart console not ready, exit")
                    ret = -1
                elif index == 4:
                    print("=== TIMEOUT: Failed to connect console.")
                    ret = -1
            except Exception as e:
                print("=== Exception occurred: {}".format(e))
                ret = -1
        if ret != 0:
            return -1
        try:
            # retry sending "\r\n" for up to 5 times to get full prompt string
            for retry in range(5):
                #session.sendline("\r\n")
                self.sendline_bytewise(session, "")
                for attempt in range(5):
                    index = session.expect(["uart:~\$", "suc:~\$", "vulcano:~\$", pexpect.TIMEOUT], 1)
                    if index == 0 or index == 1 or index == 2:
                        # Console prompt detected
                        console_prompt = 1
                        # right after power cycle, we might get prompt from UART before sending any commands
                        # clear the additional prompts before proceeding
                        continue
                    elif index == 3:
                        # No more prompts detected
                        if console_prompt == 1:
                            break
                        else:
                            continue
                if console_prompt == 1:
                    break
        except Exception as e:
            print("=== Exception occurred: {}".format(e))
            ret = -1
        if console_prompt != 1:
            print("Failed to detect console prompt")
            ret = -1
        return ret