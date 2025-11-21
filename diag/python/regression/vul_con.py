#!/usr/bin/env python

import argparse
import pexpect
import os
import sys
import time
import re

sys.path.append("../lib")
import common
from nic_con import nic_con

class vul_con:

    def usb_uart_session_connect(self, session, slot, timeout=15, uart_id="0"):
        ret = 0
        nc = nic_con()
        cmd = nc.get_connect_cmd(slot, uart_id=uart_id)
        expstr = "Terminal ready"
        errorstr = "cannot open /dev/SUCUART"
        retries = 20
        retry_delay = 1
        for attempt in range(retries):
            try:
                print("Attemp {} to connect...".format(attempt + 1))
                session.sendline(cmd)
                index = session.expect([expstr, errorstr, pexpect.TIMEOUT], timeout)
                if index == 0:
                    # Connection successful
                    ret = 0
                    break
                elif index == 1:
                    print("SUCUART not ready. Retry in {} seconds...".format(retry_delay))
                    time.sleep(retry_delay)
                    ret = -1
                elif index == 2:
                    print("=== TIMEOUT: Failed to connect console.")
                    ret = -1
            except Exception as e:
                print("=== Exception occurred: {}".format(e))
                ret = -1
        if ret != 0:
            return -1
        try:
            session.sendline("")
            while True:
                index = session.expect(["uart:~\$", pexpect.TIMEOUT], 1)
                if index == 0:
                    # Console prompt detected
                    continue
                elif index == 1:
                    # No more prompts detected
                    break
        except pexpect.TIMEOUT:
            # didn't detect any prompt
            print("=== TIMEOUT: Failed to detect console prompt")
            ret = -1
        return ret