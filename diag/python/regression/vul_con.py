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
        try:
            session.sendline(cmd)
            session.expect(expstr, timeout)
        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Failed to connect console")
            ret = -1
        return ret