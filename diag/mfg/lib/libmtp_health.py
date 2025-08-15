import pexpect
import time
import os
import sys
import libmfg_utils
import re
import threading
import json
from datetime import datetime
import ipaddress
import traceback
from libmfg_cfg import *
from libsku_utils import *
from libsku_cfg import *

from libdefs import MTP_TYPE
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MTP_Const
from libdefs import MTP_Status
from libdefs import MFG_DIAG_CMDS
from libdefs import MFG_DIAG_SIG
from libdefs import MFG_DIAG_RE
from libdefs import Factory
from libdefs import MTP_Health_Status
import test_utils

class mtp_health_ctrl():
    def __init__(self, mtpid, ts_cfg = None, mgmt_health_cfg = None, apc_health_cfg = None, dbg_mode = False):
        self._id = mtpid
        self._ts_handle = None
        self._mgmt_handle = None
        self._mgmt_prompt = None
        self._mgmt_timeout = MTP_Const.MTP_POWER_ON_TIMEOUT

        self._ts_cfg = ts_cfg
        self._mgmt_cfg = mgmt_health_cfg
        self._apc_cfg = apc_health_cfg
        self._prompt_list = libmfg_utils.get_linux_prompt_list()

        self._fans = 3
        self._psu_num = 2
        self._factory_location = Factory.UNKNOWN
        self._health_status = MTP_Health_Status.MTP_HEALTH
        self._mtp_rev = None
        self._lock = threading.Lock()

        self._debug_mode = dbg_mode
        self._filep = None
        self._cmd_buf = None
        self._buf_before_sig = None
        self._diag_filep = None
        self._diag_cmd_filep = None

        self._cycle_cnt = 1
        self._event = threading.Event()

    def monitor(self):
        try:
            cycle_cnt = self.get_cycle_cnt()
            rc = True
            rc &= self.mtp_health_test(cycle_cnt)
            if not rc: 
                self.set_event_status()
                self.cli_log_err("MTP Monitoring Status Failed")

        except:
            self.set_event_status()
            self.cli_log_err("MTP Monitoring Status Unexpected Error Occur")

    # Thread function that waits for the event to be set
    def monitr_mtp_health(self, timeout=180):
        while True:
            if self.get_cycle_cnt() > 1: time.sleep(timeout)
            self.monitor()
            if self.get_event_set_status():
                # Wait until the event is set
                break
            else:
                self.set_cycle_cnt_increment()

    def get_cycle_cnt(self):
        return self._cycle_cnt

    def set_cycle_cnt_increment(self, add=1):
        self._cycle_cnt += add

    def get_event_set_status(self):
        return True if self._event.is_set() else False 

    def set_event_status(self):
        self._event.set()

    def cli_log_inf(self, msg, level = 1):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + indent + msg, False)


    def cli_log_report_inf(self, msg):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        prefix = "==> "
        postfix = " <=="
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + prefix + msg + postfix, False)


    def cli_log_err(self, msg, level = 1):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_err(self._filep, cli_id_str + indent + msg, False)


    def cli_log_wrn(self, msg, level = 1):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_wrn(self._filep, cli_id_str + indent + msg, False)


    def cli_log_file(self, msg):
        self._filep.write(msg + "\n")


    def log_mtp_health_file(self, msg):
        self._diag_filep.write("\n[" + libmfg_utils.get_timestamp() + "] " + msg)
        # extra sendline to clean up log
        if self._mgmt_handle and self._mgmt_prompt:
            self.mtp_mgmt_exec_cmd("")

    def log_test_start(self, testname):
        # log the timestamp in MTP log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started".format(testname)
        ts_record_cmd = "#######= {:s} =#######".format(ts_record)
        self.log_mtp_health_file(ts_record_cmd)
        return start

    def log_test_stop(self, testname, start):
        # log the timestamp in MTP log
        stop = libmfg_utils.timestamp_snapshot()
        duration = stop - start
        ts_record = "{:s} Stopped - duration {:s}".format(testname, str(duration))
        ts_record_cmd = "#######= {:s} =#######".format(ts_record)
        self.log_mtp_health_file(ts_record_cmd)
        return duration


    def get_mgmt_cfg(self):
        return self._mgmt_cfg


    def set_mtp_logfile(self, filep):
        self._filep = filep


    def set_mtp_diag_logfile(self, diag_filep):
        self._diag_filep = diag_filep
        self._mgmt_handle.logfile_read = self._diag_filep


    def mtp_get_cmd_buf_before_sig(self):
        return self._buf_before_sig

    def mtp_get_cmd_buf(self):
        return self._cmd_buf


    def mtp_dump_err_msg(self, err_msg):
        self.cli_log_err("==== Error Message Start: ====")
        if err_msg:
            if (len(err_msg) > 512):
                top_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[:256])
                for line in top_err_msg.splitlines():
                    if self._mgmt_prompt in line:
                        continue # skip so it doesnt mess with pexpect
                    self.cli_log_err(line)
                self.cli_log_err("<============================>")
                bottom_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[-256:])
                for line in bottom_err_msg.splitlines():
                    if self._mgmt_prompt in line:
                        continue # skip so it doesnt mess with pexpect
                    self.cli_log_err(line)
            else:
                err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg)
                for line in err_msg.splitlines():
                    self.cli_log_err(line)
        self.cli_log_err("==== Error Message End: ====")


    def mtp_mgmt_disconnect(self):
        if self._mgmt_handle:
            self._mgmt_handle.close()
            self._mgmt_handle = None


    def mtp_session_create(self):
        # mgmt_cfg is a list with format [ip, userid, passwd]
        ip = self._mgmt_cfg[0]
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        ssh_cmd = libmfg_utils.get_ssh_connect_cmd(userid, ip)
        handle = pexpect.spawn(ssh_cmd)
        idx = libmfg_utils.mfg_expect(handle, ["assword:"])
        if idx < 0:
            self.cli_log_err("Can not connect to mtp, check the console.\n", level = 0)
            return None
        else:
            handle.sendline(passwd)

        idx = libmfg_utils.mfg_expect(handle, self._prompt_list)
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            return None

        cmd = MFG_DIAG_CMDS().MTP_LOGIN_VERIFY_FMT
        sig_list = [userid]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
            self.cli_log_err("Connect to mtp mgmt failed", level = 0)
            return None
        else:
            return handle


    def mtp_health_mgmt_connect(self, prompt_cfg=False, prompt_id=None, retry_with_powercycle=False, max_retry=3):
        delay = 10 # make sure this delay covers FST boot
        # retries = self._mgmt_timeout / delay
        # retries = retries + 4
        retries = max_retry
        if not self._mgmt_cfg:
            self.cli_log_err("management port config is empty")
            return None

        self.mtp_mgmt_disconnect()

        # mgmt_cfg is a list with format [ip, userid, passwd]
        ip = self._mgmt_cfg[0]
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        ssh_cmd = libmfg_utils.get_ssh_connect_cmd(userid, ip)
        self._mgmt_handle = pexpect.spawn(ssh_cmd, encoding='utf-8', codec_errors='ignore')
        while True:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["assword:"])
            if idx < 0:
                if retries > 0:
                    if retry_with_powercycle:
                        self.cli_log_err("Connect to mtp timeout. Powercycle and retry...{:d} attempts remaining...".format(retries))
                    else:
                        self.cli_log_inf("Connect to mtp timeout, wait {:d}s and retry...".format(delay), level=0)
                        time.sleep(delay)
                    retries -= 1
                    self._mgmt_handle = pexpect.spawn(ssh_cmd, encoding='utf-8', codec_errors='ignore')
                    continue
                else:
                    self.cli_log_err("Connect to mtp failed\n", level=0)
                    return None
            else:
                self._mgmt_handle.sendline(passwd)
                break

        idx = libmfg_utils.mfg_expect(self._mgmt_handle, self._prompt_list)
        if idx < 0:
            self.cli_log_err(self._mgmt_handle.before)
            self.cli_log_err("Connect to mtp failed", level=0)
            return None

        self._mgmt_prompt = self._prompt_list[idx]

        cmd = MFG_DIAG_CMDS().MTP_LOGIN_VERIFY_FMT
        sig_list = [userid]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
            self.cli_log_err("Connect to mtp mgmt failed", level=0)
            return None

        # set logfile
        self._mgmt_handle.logfile_read = self._diag_filep
        self._mgmt_handle.logfile_send = self._diag_cmd_filep
        if prompt_cfg:
            # config the prompt
            if prompt_id:
                userid = prompt_id
            else:
                userid = self._mgmt_cfg[1]
            if not self.mtp_prompt_cfg(self._mgmt_handle, userid, self._mgmt_prompt):
                self.cli_log_err("Failed to Init Diag SW Environment", level=0)
                return None
            self._mgmt_prompt = "{:s}@MTP:".format(userid) + self._mgmt_prompt

        return self._mgmt_prompt


    def mtp_prompt_cfg(self, handle, userid, prompt, slot=None):
        handle.sendline("stty rows 50 cols 160")
        idx = libmfg_utils.mfg_expect(handle, [prompt])
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt timeout", level=0)
            return False

        prompt_str = "{:s}@MTP:{:s} ".format(userid, prompt)
        handle.sendline(r"PS1='[\D{%Y-%m-%d_%H:%M:%S}] " + prompt_str + "'")

        # refresh
        handle.sendline("uname")
        idx = libmfg_utils.mfg_expect(handle, ["Linux"])
        if idx < 0:
            self.cli_log_err("Refresh mtp mgmt timeout", level=0)
            return False
        idx = libmfg_utils.mfg_expect(handle, [prompt_str])
        if idx < 0:
            self.cli_log_err("Refresh mtp mgmt timeout", level=0)
            return False

        return True


    def mtp_mgmt_exec_cmd(self, cmd, sig_list=[], timeout=MTP_Const.OS_CMD_DELAY):
        rc = True
        self._mgmt_handle.sendline(cmd)
        cmd_before = ""
        self._buf_before_sig = ""
        for sig in sig_list:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, [sig], timeout)
            self._buf_before_sig += self._mgmt_handle.before
            if idx < 0:
                rc = False
                cmd_before = self._mgmt_handle.before
                break
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [self._mgmt_prompt], timeout)
        # signature match fails
        if not rc:
            self.mtp_dump_err_msg(cmd_before)
            return False
        elif idx < 0:
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False
        else:
            self._cmd_buf = self._buf_before_sig + self._mgmt_handle.before
            return True


    def mtp_diag_fail_report(self, msg):
        err_msg = MTP_DIAG_Report.MTP_DIAG_REGRESSION_FAIL + ", ERR_MSG: {:s}".format(msg)
        self.cli_log_err(err_msg, level=0)


    def mtp_psu_init(self, cycle_cnt=1):
        rc = True
        mtp_start_ts = self.log_test_start(testname="PSU")
        # store serial number
        for psu in range(self._psu_num):
            psu = str(psu+1)
            cmd = MFG_DIAG_CMDS().MTP_PSU_DISP_FMT.format(psu)
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
                self.cli_log_err("{:d}th: Executing command {:s} failed".format(cycle_cnt, cmd))
                rc = False
                continue
            psu_sn_match = re.search("MFR_SERIAL: *(.*)", self.mtp_get_cmd_buf())
            if not psu_sn_match:
                self.cli_log_err("{:d}th: Failed to read PSU_{:s} Serial Number".format(cycle_cnt, psu))
                if not MFG_BYPASS_PSU_CHECK:
                    rc = False
                continue

        # PSU test
        cmd = MFG_DIAG_CMDS().MTP_PSU_TEST_FMT
        pass_sig_list = []

        # apc_cfg is a list with format [apc1, apc1_port, apc1_userid, apc1_passwd, apc2, apc2_port, apc2_userid, apc2_passwd]
        if not MFG_BYPASS_PSU_CHECK:
            apc1 = self._apc_cfg[0]
            apc2 = self._apc_cfg[4]
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
                self.cli_log_err("{:d}th: Failed to get MTP PSU info".format(cycle_cnt), level = 0)
                return False

            if apc1 != "" :
                match = re.search(MFG_DIAG_SIG.MTP_PSU1_OK_SIG, self.mtp_get_cmd_buf())
                if match:
                    match_psu = re.search(r"PSU_1\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+", self.mtp_get_cmd_buf())
                    if match_psu:
                        pout = match_psu.group(1)
                        pin = match_psu.group(4)
                        if "-" in pin or "-" in pout:
                            self.cli_log_err("{:d}th: PSU1 test failed (pout:{:s}, pin:{:s})".format(pout, pin))
                            rc = False
                    else:
                        self.cli_log_err("{:d}th: PSU1 test failed.".format(cycle_cnt))
                        rc = False
                else:
                    self.cli_log_err("{:d}th: PSU1 result test failed.".format(cycle_cnt))
                    rc = False

            if apc2 != "" :
                match = re.search(MFG_DIAG_SIG.MTP_PSU2_OK_SIG, self.mtp_get_cmd_buf())
                if match:
                    match_psu = re.search(r"PSU_2\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+", self.mtp_get_cmd_buf())
                    if match_psu:
                        pout = match_psu.group(1)
                        pin = match_psu.group(4)
                        if "-" in pin or "-" in pout:
                            self.cli_log_err("{:d}th: PSU2 test failed (pout:{:s}, pin:{:s})".format(cycle_cnt, pout, pin))
                            rc = False
                    else:
                        self.cli_log_err("{:d}th: PSU2 test failed".format(cycle_cnt))
                        rc = False
                else:
                    self.cli_log_err("{:d}th: PSU2 result test failed.".format(cycle_cnt))
                    rc = False
            if rc:
                self.cli_log_inf("{:d}th: PSU test passed".format(cycle_cnt))

        mtp_stop_ts = self.log_test_stop(testname="PSU",start=mtp_start_ts)
        return rc

    def mtp_fan_init(self, cycle_cnt=1):
        rc = True
        # Fan present test
        cmd = MFG_DIAG_CMDS().MTP_FAN_PRSNT_FMT
        pass_sig_list = [MFG_DIAG_SIG.MTP_PRSNT_SIG]
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list, timeout=MTP_Const.MTP_OS_CMD_DELAY)
        if rc:
            self.cli_log_inf("{:d}th: FAN present test passed".format(cycle_cnt))
        else:
            self.cli_log_err("{:d}th: FAN present test failed".format(cycle_cnt))
            return rc

        # Fan speed test
        cmd = MFG_DIAG_CMDS().MTP_FAN_TEST_FMT
        pass_sig_list = [MFG_DIAG_SIG.MTP_FAN_OK_SIG]
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list, timeout=MTP_Const.MTP_OS_CMD_DELAY)
        if rc:
            self.cli_log_inf("{:d}th: FAN speed test passed".format(cycle_cnt))
        else:
            self.cli_log_err("{:d}th: FAN speed test failed".format(cycle_cnt))
            return rc

        # Fan status dump
        cmd = MFG_DIAG_CMDS().MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
            rc = False

        return rc

    def mtp_health_test(self, cycle_cnt=1):
        rc = True
        mtp_start_ts = self.log_test_start(testname="MTP HEALTH")
        cmd = "devmgr -status"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
            self.cli_log_err("{:d}th: Executing command {:s} failed".format(cycle_cnt, cmd))
            rc = False
            return rc

        # apc_cfg is a list with format [apc1, apc1_port, apc1_userid, apc1_passwd, apc2, apc2_port, apc2_userid, apc2_passwd]
        apc1 = self._apc_cfg[0]
        apc2 = self._apc_cfg[4]

        if apc1 != "" :
            match_psu = re.search(r"PSU_1\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+", self.mtp_get_cmd_buf())
            if match_psu:
                pout = match_psu.group(1)
                pin = match_psu.group(4)
                if "-" in pin or "-" in pout:
                    self.cli_log_err("{:d}th: PSU1 test failed (pout:{:s}, pin:{:s})".format(pout, pin))
                    rc = False
            else:
                self.cli_log_err("{:d}th: PSU1 test failed.".format(cycle_cnt))
                rc = False

        if apc2 != "" :
            match_psu = re.search(r"PSU_2\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+", self.mtp_get_cmd_buf())
            if match_psu:
                pout = match_psu.group(1)
                pin = match_psu.group(4)
                if "-" in pin or "-" in pout:
                    self.cli_log_err("{:d}th: PSU2 test failed (pout:{:s}, pin:{:s})".format(pout, pin))
                    rc = False
            else:
                self.cli_log_err("{:d}th: PSU2 test failed.".format(cycle_cnt))
                rc = False
        if rc:
            self.cli_log_inf("{:d}th: PSU test passed".format(cycle_cnt))

        match_fan = re.search(r"FAN\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+", self.mtp_get_cmd_buf())
        if match_fan:
            fan1_in = match_fan.group(1)
            fan1_out = match_fan.group(2)
            fan2_in = match_fan.group(3)
            fan2_out = match_fan.group(4)
            fan3_in = match_fan.group(5)
            fan3_out = match_fan.group(6)
            if "-" in fan1_in or "-" in fan1_out or "-" in fan2_in or "-" in fan2_out or "-" in fan3_in or "-" in fan3_out:
                self.cli_log_err("{:d}th: FAN test failed".format(cycle_cnt))
                rc = False
        else:
            self.cli_log_err("{:d}th: FAN test failed.".format(cycle_cnt))
            rc = False

        mtp_stop_ts = self.log_test_stop(testname="MTP HEALTH",start=mtp_start_ts)
        return rc
