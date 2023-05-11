import sys
import os
import time
import pexpect
import threading
import re
import traceback
from datetime import datetime
import ipaddress

import libmfg_utils

class pdu_ctrl():
    def __init__(self, test_ctrl, pdu_cfg):
        self._handle = None
        self._test_inst = test_ctrl
        self._filep = test_ctrl._pdu_filep
        self._pdu_cfg = pdu_cfg

    def _telnet_to_pdu(self, ip, userid, passwd):
        self._handle = pexpect.spawn("telnet " + ip, logfile = self._filep, encoding='ascii', codec_errors='ignore')
        retry = 0
        while True:
            idx = self._handle.expect(["ame *:", "assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                self._handle.send(userid + "\r")
                continue
            elif idx == 1:
                self._handle.send(passwd + "\r")
                break
            elif idx > 1 and retry < 5:
                retry += 1
                self._handle = pexpect.spawn("telnet " + ip, logfile=self._filep, encoding='ascii', codec_errors='ignore')
                continue
            else:
                return False

        return True

    def _single_pdu_pwr_off(self, ip, userid, passwd, port_list):
        if not self._telnet_to_pdu(ip, userid, passwd):
            self._test_inst.cli_log_err("Unable to connect to PDU: " + ip)
            return False

        idx = self._handle.expect_exact(["PX2", "Schneider", "American Power Conversion", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            self._handle.expect_exact("#")
            self._test_inst.cli_log_err("Need to add PX2 support")
            return False
        # Supported pdu
        elif idx == 1 or idx == 2:
            self._handle.expect_exact(">")
            for port in port_list:
                self._handle.send("olOff " + port + "\r")
                self._handle.expect_exact(">")
            self._filep.flush()
            self._handle.close()
            time.sleep(1)
            return True
        else:
            self._test_inst.cli_log_err("Unknown PDU: " + ip)
            return False


    def _single_pdu_pwr_on(self, ip, userid, passwd, port_list):
        if not self._telnet_to_pdu(ip, userid, passwd):
            self._test_inst.cli_log_err("Unable to connect to PDU: " + ip)
            return False

        idx = self._handle.expect_exact(["PX2", "Schneider", "American Power Conversion", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            self._handle.expect_exact("#")
            self._test_inst.cli_log_err("Need to add PX2 support")
            return False
        # Supported pdu
        elif idx == 1 or idx == 2:
            self._handle.expect_exact(">")
            for port in port_list:
                self._handle.send("olOn " + port + "\r")
                self._handle.expect_exact(">")
            self._filep.flush()
            self._handle.close()
            return True
        else:
            self._test_inst.cli_log_err("Unknown PDU: " + ip)
            return False

    def mtp_pdu_pwr_off(self):
        if not self._pdu_cfg:
            self._test_inst.cli_log_err("PDU config is empty")
            return False

        # pdu_cfg is a list with format [pdu1, pdu1_port, pdu1_userid, pdu1_passwd, pdu2, pdu2_port, pdu2_userid, pdu2_passwd]
        pdu1 = self._pdu_cfg[0]
        pdu1_port = self._pdu_cfg[1]
        pdu1_userid = self._pdu_cfg[2]
        pdu1_passwd = self._pdu_cfg[3]

        pdu2 = self._pdu_cfg[4]
        pdu2_port = self._pdu_cfg[5]
        pdu2_userid = self._pdu_cfg[6]
        pdu2_passwd = self._pdu_cfg[7]

        # no pdu control
        if pdu1 == "" and pdu2 == "":
            self._test_inst.cli_log_err("No PDU connection, power cycle mtp failed")
            return False

        # most cases, single pdu controller, two ports
        if pdu1 == pdu2:
            pdu_port_list = [pdu1_port, pdu2_port]
            return self._single_pdu_pwr_off(pdu1, pdu1_userid, pdu1_passwd, pdu_port_list)
        # only pdu1 is connected, single pdu controller, 1 port
        elif pdu2 == "":
            pdu_port_list = [pdu1_port]
            return self._single_pdu_pwr_off(pdu1, pdu1_userid, pdu1_passwd, pdu_port_list)
        # only pdu2 is connected, single pdu controller, 1 port
        elif pdu1 == "":
            pdu_port_list = [pdu2_port]
            return self._single_pdu_pwr_off(pdu2, pdu2_userid, pdu2_passwd, pdu_port_list)
        # two pdu controllers, each have a port
        else:
            self._test_inst.cli_log_err("Currently no support for two pdu controllers")
            return False


    def mtp_pdu_pwr_on(self):
        if not self._pdu_cfg:
            self._test_inst.cli_log_err("PDU config is empty")
            return False

        # pdu_cfg is a list with format [pdu1, pdu1_port, pdu1_userid, pdu1_passwd, pdu2, pdu2_port, pdu2_userid, pdu2_passwd]
        pdu1 = self._pdu_cfg[0]
        pdu1_port = self._pdu_cfg[1]
        pdu1_userid = self._pdu_cfg[2]
        pdu1_passwd = self._pdu_cfg[3]

        pdu2 = self._pdu_cfg[4]
        pdu2_port = self._pdu_cfg[5]
        pdu2_userid = self._pdu_cfg[6]
        pdu2_passwd = self._pdu_cfg[7]

        # no pdu control
        if pdu1 == "" and pdu2 == "":
            self._test_inst.cli_log_err("No PDU connection, power cycle mtp failed")
            return False

        # most cases, single pdu controller, two ports
        if pdu1 == pdu2:
            pdu_port_list = [pdu1_port, pdu2_port]
            return self._single_pdu_pwr_on(pdu1, pdu1_userid, pdu1_passwd, pdu_port_list)
        # only pdu1 is connected, single pdu controller, 1 port
        elif pdu2 == "":
            pdu_port_list = [pdu1_port]
            return self._single_pdu_pwr_on(pdu1, pdu1_userid, pdu1_passwd, pdu_port_list)
        # only pdu2 is connected, single pdu controller, 1 port
        elif pdu1 == "":
            pdu_port_list = [pdu2_port]
            return self._single_pdu_pwr_on(pdu2, pdu2_userid, pdu2_passwd, pdu_port_list)
        # two pdu controllers, each have a port
        else:
            self._test_inst.cli_log_err("Currently no support for two pdu controllers")
            return False
