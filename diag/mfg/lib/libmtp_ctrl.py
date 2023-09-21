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

from libdefs import NIC_Type
from libdefs import MTP_ASIC_SUPPORT
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MTP_Const
from libdefs import NIC_Status
from libdefs import MTP_Status
from libdefs import NIC_Port_Mask
from libdefs import MFG_DIAG_CMDS
from libdefs import MFG_DIAG_SIG
from libdefs import MFG_DIAG_RE
from libdefs import FF_Stage
from libdefs import Swm_Test_Mode
from libdefs import Voltage_Margin
from libdefs import Factory
from libnic_ctrl import nic_ctrl
import test_utils
import image_control

class mtp_ctrl():
    def __init__(self, mtpid, filep, diag_log_filep, diag_nic_log_filep_list, diag_cmd_log_filep=None, ts_cfg = None, mgmt_cfg = None, apc_cfg = None, slots_to_skip = [False]*MTP_Const.MTP_SLOT_NUM, dbg_mode = False):
        self._id = mtpid
        self._ts_handle = None
        self._mgmt_handle = None
        self._mgmt_prompt = None
        self._mgmt_timeout = MTP_Const.MTP_POWER_ON_TIMEOUT
        self._ts_cfg = ts_cfg
        self._mgmt_cfg = mgmt_cfg
        self._apc_cfg = apc_cfg
        self._prompt_list = libmfg_utils.get_linux_prompt_list()
        self._valid_type_list = MFG_VALID_NIC_TYPE_LIST
        self._proto_type_list = MFG_PROTO_NIC_TYPE_LIST
        self._valid_pn_list = MFG_VALID_NIC_PN_LIST
        self._slots = MTP_Const.MTP_SLOT_NUM
        self._slots_to_skip = slots_to_skip
        self._fans = 3
        self._psu_num = 2
        self._status = MTP_Status.MTP_STA_POWEROFF
        self._fanspd = MTP_Const.MFG_EDVT_NORM_FAN_SPD    # variable to track the fan speed (%) set by the script
        self._factory_location = Factory.UNKNOWN

        self._nic_ctrl_list = [None] * self._slots
        self._nic_alom_ctrl_list = [None] * self._slots
        self._nic_type_list = [None] * self._slots
        self._nic_prsnt_list = [False] * self._slots
        self._nic_scan_prsnt_list = [False] * self._slots
        self._nic_sn_list = [None] * self._slots
        self._nic_scan_sn_list = [None] * self._slots
        self._nic_alom_sn_list = [None] * self._slots
        self._nic_status_before_hide_list = [NIC_Status.NIC_STA_OK] * self._slots
        self._nic_sw_pn_list = [None] * self._slots

        self._nic_thread_list = [None] * self._slots
        # lock for printing
        self._lock = threading.Lock()
        # locks for sequential portion inside parallel test
        self._nic_console_lock = threading.Lock()
        self._j2c_lock = threading.Lock()
        # lock for coordinating j2c tests on turbo MTP
        self._turbo_j2c_lock = [threading.Lock() for x in range(self._slots)]

        self._io_cpld_ver = None
        self._jtag_cpld_ver = None
        self._asic_support = None
        self._mtp_rev = None
        self._os_ver = None
        self._diag_ver = None
        self._asic_ver = None
        self._swmtestmode = [Swm_Test_Mode.SWMALOM] * self._slots
        self._fst_ver = None
        self._psu_sn = dict()

        self._debug_mode = dbg_mode
        self._filep = filep
        self._cmd_buf = None
        self._buf_before_sig = None
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._diag_nic_filep_list = diag_nic_log_filep_list[:]
        self._diagmgr_logfile = None
        self._temppn = None

        self._cicd_run = False

    def cli_log_inf(self, msg, level = 1):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(cli_id_str + indent + msg)


    def cli_log_report_inf(self, msg):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        prefix = "==> "
        postfix = " <=="
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + prefix + msg + postfix)
        else:
            libmfg_utils.cli_inf(cli_id_str + prefix + msg + postfix)


    def cli_log_err(self, msg, level = 1):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_err(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_err(cli_id_str + indent + msg)


    def cli_log_wrn(self, msg, level = 1):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_wrn(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_wrn(cli_id_str + indent + msg)


    def cli_log_slot_inf(self, slot, msg, level = 0):
        if msg is None:
            msg = ""
        nic_cli_id_str = libmfg_utils.id_str(mtp = self._id, nic = slot)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(nic_cli_id_str + indent + msg)


    def cli_log_slot_err(self, slot, msg, level = 0):
        if msg is None:
            msg = ""
        nic_cli_id_str = libmfg_utils.id_str(mtp = self._id, nic = slot)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_err(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_err(nic_cli_id_str + indent + msg)


    def cli_log_slot_wrn(self, slot, msg, level = 0):
        if msg is None:
            msg = ""
        nic_cli_id_str = libmfg_utils.id_str(mtp = self._id, nic = slot)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_wrn(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_wrn(nic_cli_id_str + indent + msg)


    def cli_log_slot_inf_lock(self, slot, msg, level = 0):
        self._lock.acquire()
        self.cli_log_slot_inf(slot, msg, level)
        self._lock.release()


    def cli_log_slot_err_lock(self, slot, msg, level = 0):
        self._lock.acquire()
        self.cli_log_slot_err(slot, msg, level)
        self._lock.release()


    def cli_log_file(self, msg):
        self._filep.write(msg + "\n")

    def log_mtp_file(self, msg):
        self._diag_filep.write("\n[" + libmfg_utils.get_timestamp() + "] " + msg)
        # extra sendline to clean up log
        if self._mgmt_handle and self._mgmt_prompt:
            self.mtp_mgmt_exec_cmd("")

    def log_nic_file(self, slot, msg):
        self._diag_nic_filep_list[slot].write("\n[" + libmfg_utils.get_timestamp() + "] " + msg)
        # extra sendline to clean up log
        if self._nic_ctrl_list[slot] is not None:
            if self._nic_ctrl_list[slot]._nic_handle:
                self._nic_ctrl_list[slot].mtp_exec_cmd("")

    def log_slot_test_start(self, slot, testname):
        # log the timestamp in NIC log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started".format(testname)
        ts_record_cmd = "#######= {:s} =#######".format(ts_record)
        self.log_nic_file(slot, ts_record_cmd)
        return start

    def log_slot_test_stop(self, slot, testname, start):
        # log the timestamp in NIC log
        stop = libmfg_utils.timestamp_snapshot()
        duration = stop - start
        ts_record = "{:s} Stopped - duration {:s}".format(testname, str(duration))
        ts_record_cmd = "#######= {:s} =#######".format(ts_record)
        self.log_nic_file(slot, ts_record_cmd)
        return duration

    def log_test_start(self, testname):
        # log the timestamp in MTP log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started".format(testname)
        ts_record_cmd = "#######= {:s} =#######".format(ts_record)
        self.log_mtp_file(ts_record_cmd)
        return start

    def log_test_stop(self, testname, start):
        # log the timestamp in MTP log
        stop = libmfg_utils.timestamp_snapshot()
        duration = stop - start
        ts_record = "{:s} Stopped - duration {:s}".format(testname, str(duration))
        ts_record_cmd = "#######= {:s} =#######".format(ts_record)
        self.log_mtp_file(ts_record_cmd)
        return duration

    def mtp_sys_info_disp(self):
        self.cli_log_inf("MTP System Info Dump:", level=0)

        if not self._mgmt_cfg[0]:
            self.cli_log_err("Unable to retrieve MTP MGMT IP")
            return False
        self.cli_log_report_inf("MTP Chassis IP: {:s}".format(self._mgmt_cfg[0]))

        if not self.get_mtp_factory_location():
            self.cli_log_err("Unable to get MTP factory location")
            return False
        self.cli_log_report_inf("MTP Location: {:s}".format(self.get_mtp_factory_location()))

        for psu in self._psu_sn.keys():
            if self._psu_sn[psu]:
                self.cli_log_report_inf("MTP PSU_{:s} MFR ID: {:s}".format(psu, self._psu_sn[psu]))

        if not self._io_cpld_ver:
            self.cli_log_err("Unable to retrieve MTP IO-CPLD Version")
            return False
        self.cli_log_report_inf("MTP IO-CPLD Version: {:s}".format(self._io_cpld_ver))

        if not self._jtag_cpld_ver:
            self.cli_log_err("Unable to retrieve MTP JTAG-CPLD Version")
            return False
        self.cli_log_report_inf("MTP JTAG-CPLD Version: {:s}".format(self._jtag_cpld_ver))

        if not self._asic_support:
            self.cli_log_err("Unable to retrieve ASIC version supported by CPLD")
            return False
        self.cli_log_report_inf("MTP CPLD supports: {:s}".format(self._asic_support))

        if not self._mtp_rev:
            self.cli_log_err("Unable to retrieve MTP revision")
            return False
        self.cli_log_report_inf("MTP Rev: Rev_{:s}".format(self._mtp_rev))

        if not self._os_ver:
            self.cli_log_err("Unable to retrieve MTP Kernel Version")
            return False
        self.cli_log_report_inf("MTP Kernel Version: {:s}".format(self._os_ver))

        if not self._diag_ver:
            self.cli_log_err("Unable to retrieve MTP Diag Version")
            return False
        self.cli_log_report_inf("MTP Diag Version: {:s}".format(self._diag_ver))

        if not self._asic_ver:
            self.cli_log_err("Unable to retrieve MTP ASIC Version")
            return False
        self.cli_log_report_inf("MTP ASIC Version: {:s}".format(self._asic_ver))

        script_ver_match = re.search("image_amd64_....(.){0,2}_(.*)\.tar", MFG_IMAGE_FILES.MTP_AMD64_IMAGE)
        if script_ver_match:
            script_ver = script_ver_match.group(2)
        else:
            script_ver = ""
        self.cli_log_report_inf("MFG Script Version: {:s}".format(script_ver))

        self.cli_log_inf("MTP System Info Dump End\n", level=0)
        return True


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

    def mtp_dump_nic_err_msg(self, slot):
        err_msg = self.mtp_get_nic_cmd_buf(slot)
        if err_msg is None:
            err_msg = ""
        self.cli_log_slot_err(slot, "==== Error Message Start: ====")
        if err_msg:
            if (len(err_msg) > 512):
                top_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[:256])
                for line in top_err_msg.splitlines():
                    if self._mgmt_prompt in line:
                        continue # skip so it doesnt mess with pexpect
                    self.cli_log_slot_err(slot, line)
                self.cli_log_slot_err(slot, "<============================>")
                bottom_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[-256:])
                for line in bottom_err_msg.splitlines():
                    if self._mgmt_prompt in line:
                        continue # skip so it doesnt mess with pexpect
                    self.cli_log_slot_err(slot, line)
            else:
                err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg)
                for line in err_msg.splitlines():
                    if self._mgmt_prompt in line:
                        continue # skip so it doesnt mess with pexpect
                    self.cli_log_slot_err(slot, line)
        self.cli_log_slot_err(slot, "==== Error Message End: ====")


    def set_mtp_status(self, status):
        if status < MTP_Status.MTP_STA_MAX:
            self._status = status


    def get_mtp_slot_num(self):
        return self._slots

    def get_mtp_factory_location(self):
        if self._factory_location == Factory.UNKNOWN:
            self.set_mtp_factory_location()

        return self._factory_location

    def set_mtp_factory_location(self, set_to=""):
        if set_to == "":
            self._factory_location = self._detect_factory_location()
        return self._factory_location

    def _detect_factory_location(self):
        # cmd = "ifconfig enp4s0 | grep 'inet '"
        # if not self.mtp_mgmt_exec_cmd(cmd):
        #     self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
        #     return None
        # cmd_buf = self.mtp_get_cmd_buf()

        # if cmd_buf is None or cmd_buf == "":
        #     self.cli_log_err("Can't get network connection to MTP: {:s}".format(cmd), level = 0)
        #     return None

        # if "Device not found" in cmd_buf:
        #     self.cli_log_err("Unable to get MTP ethernet port details: {:s}".format(cmd), level = 0)
        #     return None
        if not self._mgmt_cfg:
            self.cli_log_err("Unable to retrieve MTP MGMT IP for factory detection")
            return Factory.UNKNOWN

        mtp_ipaddr = self._mgmt_cfg[0]

        # check which network subnet mask this IP address falls into
        for factory in Factory_network_config.keys():
            if "Networks" not in Factory_network_config[factory].keys():
                self.cli_log_err("Bad network config for factory {:s}".format(factory))
                return Factory.UNKNOWN
            for subnet in Factory_network_config[factory]["Networks"]:
                if ipaddress.ip_address(unicode(mtp_ipaddr)) in ipaddress.ip_network(unicode(subnet)):
                    return factory

        self.cli_log_err("MTP IP does not belong in any valid network range")
        return Factory.UNKNOWN

    def _apc_model_check(self, handle):
        """
        Check that the model is a Digital Logger V222.
        This model supports the uom commands we are using in the script.
        """
        retry = 0
        while True:
            handle.send("uom dump relay/model\r")
            idx = handle.expect_exact(["V222", "#", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.expect_exact("#")
                return True
            elif idx == 1:
                self.cli_log_err("This APC model not supported")
                return False
            elif idx > 1 and retry < 5:
                retry += 1
                continue
            else:
                self.cli_log_err("APC: Unable to check model")
                return False

    def _mtp_single_apc_pwr_off_ssh(self, apc, userid, passwd, port_list):
        """
        Digital Logger V222: Set persistent state: uom set "relay/outlets/2/state" false
        """
        retry = 0
        handle = pexpect.spawn("ssh " + userid + "@" + apc)
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(passwd + "\r")
                break
            elif idx > 0 and retry < 5:
                retry += 1
                handle = pexpect.spawn("ssh " + userid + "@" + apc)
                continue
            else:
                self.cli_log_err("Unable to ssh to APC: " + apc)
                return False

        idx = handle.expect_exact(["root@", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            if not self._apc_model_check(handle):
                handle.close()
                return False
            for port in port_list:
                handle.send("uom set relay/outlets/{:d}/state false\r".format(int(port)-1))
                idx = handle.expect_exact(["#", "not found", pexpect.TIMEOUT])
                if idx != 0:
                    self.cli_log_err("APC does not support uom command")
                    handle.close()
                    return False
            handle.close()
            time.sleep(1)
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False

    def _mtp_single_apc_pwr_on_ssh(self, apc, userid, passwd, port_list):
        """
        Digital Logger V222: Set persistent state: uom set "relay/outlets/2/state" true
        """
        retry = 0
        handle = pexpect.spawn("ssh " + userid + "@" + apc)
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(passwd + "\r")
                break
            elif idx > 0 and retry < 5:
                retry += 1
                handle = pexpect.spawn("ssh " + userid + "@" + apc)
                continue
            else:
                self.cli_log_err("Unable to ssh to APC: " + apc)
                return False

        idx = handle.expect_exact(["root@", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            if not self._apc_model_check(handle):
                handle.close()
                return False
            for port in port_list:
                handle.send("uom set relay/outlets/{:d}/state true\r".format(int(port)-1))
                idx = handle.expect_exact(["#", "not found", pexpect.TIMEOUT])
                if idx != 0:
                    self.cli_log_err("APC does not support uom command")
                    handle.close()
                    return False
            handle.close()
            time.sleep(1)
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False

    def _mtp_single_apc_pwr_get_state_ssh(self, apc, userid, passwd, port_list):
        """
        Digital Logger V222: Get persistent state: uom get relay/outlets/0/state
        """
        retry = 0
        handle = pexpect.spawn("ssh " + userid + "@" + apc)
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(passwd + "\r")
                break
            elif idx > 0 and retry < 5:
                retry += 1
                handle = pexpect.spawn("ssh " + userid + "@" + apc)
                continue
            else:
                self.cli_log_err("Unable to ssh to APC: " + apc)
                return False

        idx = handle.expect_exact(["root@", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            if not self._apc_model_check(handle):
                handle.close()
                return False
            for port in port_list:
                handle.send("uom get relay/outlets/{:d}/state\r".format(int(port)-1))
                idx = handle.expect_exact(["#", "not found", pexpect.TIMEOUT])
                if idx != 0:
                    self.cli_log_err("APC does not support uom command")
                    handle.close()
                    return False
            handle.close()
            time.sleep(1)
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False


    def _mtp_single_apc_pwr_off(self, apc, userid, passwd, port_list):
        retry = 0
        handle = pexpect.spawn("telnet " + apc)
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["ame *:", "assword *:", "Connection refused", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
            elif idx == 2:
                # no telnet, try as ssh
                handle.close()
                return self._mtp_single_apc_pwr_off_ssh(apc, userid, passwd, port_list)
            elif idx > 2 and retry < 5:
                retry += 1
                handle = pexpect.spawn("telnet " + apc)
                continue
            else:
                self.cli_log_err("Unable to connect APC: " + apc)
                return False

        idx = handle.expect_exact(["PX2", "Schneider", "American Power Conversion", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            self.cli_log_err("Need to add PX2 support")
            return False
        # Supported apc
        elif idx == 1 or idx == 2:
            handle.expect_exact(">")
            for port in port_list:
                handle.send("olOff " + str(port) + "\r")
                handle.expect_exact(">")
            handle.close()
            time.sleep(1)
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False


    def _mtp_single_apc_pwr_on(self, apc, userid, passwd, port_list):
        retry = 0
        handle = pexpect.spawn("telnet " + apc)
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["ame *:", "assword *:", "Connection refused", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
            elif idx == 2:
                # no telnet, try as ssh
                handle.close()
                return self._mtp_single_apc_pwr_on_ssh(apc, userid, passwd, port_list)
            elif idx > 2 and retry < 5:
                retry += 1
                handle = pexpect.spawn("telnet " + apc)
                continue
            else:
                self.cli_log_err("Unable to connect APC: " + apc)
                return False

        idx = handle.expect_exact(["PX2", "Schneider", "American Power Conversion", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            self.cli_log_err("Need to add PX2 support")
            return False
        # Supported apc
        elif idx == 1 or idx == 2:
            handle.expect_exact(">")
            for port in port_list:
                handle.send("olOn " + str(port) + "\r")
                handle.expect_exact(">")
            handle.close()
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False


    def _mtp_single_apc_pwr_cycle(self, apc, userid, passwd, port_list):
        handle = pexpect.spawn("telnet " + apc)
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["ame *:", "assword *:", "Connection refused", pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
            elif idx == 2:
                # no telnet, try as ssh
                handle.close()
                if not self._mtp_single_apc_pwr_off_ssh(apc, userid, passwd, port_list):
                    return False
                time.sleep(1)
                if not self._mtp_single_apc_pwr_on_ssh(apc, userid, passwd, port_list):
                    return False
                return True
            else:
                self.cli_log_err("Unable to connect APC: " + apc)
                return False

        idx = handle.expect_exact(["PX2", "Schneider", "American Power Conversion", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            self.cli_log_err("Need to add PX2 support")
            return False
        # Supported apc
        elif idx == 1 or idx == 2:
            handle.expect_exact(">")
            for port in port_list:
                handle.send("olOff " + str(port) + "\r")
                handle.expect_exact(">")
            time.sleep(1)
            for port in port_list:
                handle.send("olOn " + str(port) + "\r")
                handle.expect_exact(">")
            handle.close()
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False


    def mtp_apc_pwr_off(self):
        if not self._apc_cfg:
            self.cli_log_err("APC config is empty")
            return False

        # apc_cfg is a list with format [apc1, apc1_port, apc1_userid, apc1_passwd, apc2, apc2_port, apc2_userid, apc2_passwd]
        apc1 = self._apc_cfg[0]
        apc1_port = self._apc_cfg[1]
        apc1_userid = self._apc_cfg[2]
        apc1_passwd = self._apc_cfg[3]

        apc2 = self._apc_cfg[4]
        apc2_port = self._apc_cfg[5]
        apc2_userid = self._apc_cfg[6]
        apc2_passwd = self._apc_cfg[7]

        # no apc control
        if apc1 == "" and apc2 == "":
            self.cli_log_err("No APC connection, power cycle mtp failed")
            return False

        # most cases, single apc controller, two ports
        if apc1 == apc2:
            apc_port_list = [apc1_port, apc2_port]
            return self._mtp_single_apc_pwr_off(apc1, apc1_userid, apc1_passwd, apc_port_list)
        # only apc1 is connected, single apc controller, 1 port
        elif apc2 == "":
            apc_port_list = [apc1_port]
            return self._mtp_single_apc_pwr_off(apc1, apc1_userid, apc1_passwd, apc_port_list)
        # only apc2 is connected, single apc controller, 1 port
        elif apc1 == "":
            apc_port_list = [apc2_port]
            return self._mtp_single_apc_pwr_off(apc2, apc2_userid, apc2_passwd, apc_port_list)
        # two apc controllers, each have a port
        else:
            self.cli_log_err("Currently no support for two apc controllers")
            return False


    def mtp_apc_pwr_on(self):
        if not self._apc_cfg:
            self.cli_log_err("APC config is empty")
            return False

        # apc_cfg is a list with format [apc1, apc1_port, apc1_userid, apc1_passwd, apc2, apc2_port, apc2_userid, apc2_passwd]
        apc1 = self._apc_cfg[0]
        apc1_port = self._apc_cfg[1]
        apc1_userid = self._apc_cfg[2]
        apc1_passwd = self._apc_cfg[3]

        apc2 = self._apc_cfg[4]
        apc2_port = self._apc_cfg[5]
        apc2_userid = self._apc_cfg[6]
        apc2_passwd = self._apc_cfg[7]

        # no apc control
        if apc1 == "" and apc2 == "":
            self.cli_log_err("No APC connection, power cycle mtp failed")
            return False

        # most cases, single apc controller, two ports
        if apc1 == apc2:
            apc_port_list = [apc1_port, apc2_port]
            return self._mtp_single_apc_pwr_on(apc1, apc1_userid, apc1_passwd, apc_port_list)
        # only apc1 is connected, single apc controller, 1 port
        elif apc2 == "":
            apc_port_list = [apc1_port]
            return self._mtp_single_apc_pwr_on(apc1, apc1_userid, apc1_passwd, apc_port_list)
        # only apc2 is connected, single apc controller, 1 port
        elif apc1 == "":
            apc_port_list = [apc2_port]
            return self._mtp_single_apc_pwr_on(apc2, apc2_userid, apc2_passwd, apc_port_list)
        # two apc controllers, each have a port
        else:
            self.cli_log_err("Currently no support for two apc controllers")
            return False


    def mtp_apc_pwr_cycle(self):
        if not self._apc_cfg:
            self.cli_log_err("APC config is empty")
            return False

        # apc_cfg is a list with format [apc1, apc1_port, apc1_userid, apc1_passwd, apc2, apc2_port, apc2_userid, apc2_passwd]
        apc1 = self._apc_cfg[0]
        apc1_port = self._apc_cfg[1]
        apc1_userid = self._apc_cfg[2]
        apc1_passwd = self._apc_cfg[3]

        apc2 = self._apc_cfg[4]
        apc2_port = self._apc_cfg[5]
        apc2_userid = self._apc_cfg[6]
        apc2_passwd = self._apc_cfg[7]

        # no apc control
        if apc1 == "" and apc2 == "":
            self.cli_log_err("No APC connection, power cycle mtp failed")
            return False

        # most cases, single apc controller, two ports
        if apc1 == apc2:
            apc_port_list = [apc1_port, apc2_port]
            return self._mtp_single_apc_pwr_cycle(apc1, apc1_userid, apc1_passwd, apc_port_list)
        # only apc1 is connected, single apc controller, 1 port
        elif apc2 == "":
            apc_port_list = [apc1_port]
            return self._mtp_single_apc_pwr_cycle(apc1, apc1_userid, apc1_passwd, apc_port_list)
        # only apc2 is connected, single apc controller, 1 port
        elif apc1 == "":
            apc_port_list = [apc2_port]
            return self._mtp_single_apc_pwr_cycle(apc2, apc2_userid, apc2_passwd, apc_port_list)
        # two apc controllers, each have a port
        else:
            self.cli_log_err("Currently no support for two apc controllers")
            return False


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

        cmd = MFG_DIAG_CMDS.MTP_LOGIN_VERIFY_FMT
        sig_list = [userid]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
            self.cli_log_err("Connect to mtp mgmt failed", level = 0)
            return None
        else:
            return handle


    def mtp_nic_para_session_init(self, slot_list=[], fpo=True):
        if self._fst_ver is not None:
            mtp_prompt = "#"
        else:
            mtp_prompt = "$"
        if slot_list == []:
            slot_list = range(self._slots)
        userid = self._mgmt_cfg[1]
        for slot in slot_list:
            handle = self.mtp_session_create()
            if handle:
                if not self.mtp_prompt_cfg(handle, userid, mtp_prompt, slot):
                    self.cli_log_err("Unable to config MTP session")
                    return False
                prompt = "{:s}@NIC-{:02d}:".format(userid, slot+1) + mtp_prompt
                if fpo:
                    self._nic_ctrl_list[slot] = nic_ctrl(slot, self._diag_nic_filep_list[slot])
                self._nic_ctrl_list[slot].nic_handle_init(handle, prompt)
                para_cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
                if not self.mtp_mgmt_exec_cmd_para(slot, para_cmd):
                    self.cli_log_slot_err(slot, "Failed to execute para command: {:s}".format(para_cmd))
                    return False
            else:
                self.cli_log_err("Unable to create MTP session")
                return False
        return True

    def mtp_nic_para_session_end(self, slot_list=[]):
        self.cli_log_inf("Close NIC Connections", level=0)
        if slot_list == []:
            slot_list = range(self._slots)
        for slot in slot_list:
            self._nic_ctrl_list[slot].nic_handle_close()
        return True


    def mtp_mgmt_connect(self, prompt_cfg=False, prompt_id=None, retry_with_powercycle=False, max_retry=3):
        delay = 200 # make sure this delay covers FST boot
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
        self._mgmt_handle = pexpect.spawn(ssh_cmd)
        while True:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["assword:"])
            if idx < 0:
                if retries > 0:
                    if retry_with_powercycle:
                        self.cli_log_err("Connect to mtp timeout. Powercycle and retry...{:d} attempts remaining...".format(retries))
                        libmfg_utils.mtpid_list_poweroff([self], safely=False)
                        libmfg_utils.mtpid_list_poweron([self])
                    else:
                        self.cli_log_inf("Connect to mtp timeout, wait {:d}s and retry...".format(delay), level = 0)
                        time.sleep(delay)
                    retries -= 1
                    self._mgmt_handle = pexpect.spawn(ssh_cmd)
                    continue
                else:
                    self.cli_log_err("Connect to mtp failed\n", level = 0)
                    return None
            else:
                self._mgmt_handle.sendline(passwd)
                break

        idx = libmfg_utils.mfg_expect(self._mgmt_handle, self._prompt_list)
        if idx < 0:
            self.cli_log_err(self._mgmt_handle.before)
            self.cli_log_err("Connect to mtp failed", level = 0)
            return None

        self._mgmt_prompt = self._prompt_list[idx]

        cmd = MFG_DIAG_CMDS.MTP_LOGIN_VERIFY_FMT
        sig_list = [userid]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
            self.cli_log_err("Connect to mtp mgmt failed", level = 0)
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
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            return False

        if slot != None:
            prompt_str = "{:s}@NIC-{:02d}:{:s} ".format(userid, slot+1, prompt)
        else:
            prompt_str = "{:s}@MTP:{:s} ".format(userid, prompt)
        handle.sendline("PS1='[\D{%Y-%m-%d_%H:%M:%S}] "+ prompt_str + "'")

        # refresh
        handle.sendline("uname")
        idx = libmfg_utils.mfg_expect(handle, ["Linux"])
        if idx < 0:
            self.cli_log_err("Refresh mtp mgmt timeout", level = 0)
            return False
        idx = libmfg_utils.mfg_expect(handle, [prompt_str])
        if idx < 0:
            self.cli_log_err("Refresh mtp mgmt timeout", level = 0)
            return False

        return True


    def mtp_enter_user_ctrl(self):
        if self._mgmt_handle and self._debug_mode:
            self._mgmt_handle.interact()


    def mtp_mgmt_exec_sudo_cmd(self, cmd):
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        if not self._mgmt_handle:
            self.cli_log_err("Management port is not connected")
            return False

        self._mgmt_handle.sendline("sudo -k " + cmd)
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [userid + ":"])
        if idx < 0:
            self._mgmt_handle.logfile_read = None
            self._mgmt_handle.logfile_send = None
            self.mtp_mgmt_disconnect()
            return True
        self._mgmt_handle.sendline(passwd)

        if cmd == "reboot" or cmd == "poweroff":
            self._mgmt_handle.expect_exact(pexpect.EOF)
            self._mgmt_handle.logfile_read = None
            self._mgmt_handle.logfile_send = None
            self.mtp_mgmt_disconnect()
        else:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, [self._mgmt_prompt])
            if idx < 0:
                self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
                return False

        return True

    def mtp_mgmt_exec_sudo_cmd_resp(self, cmd):
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]
        rs = ""

        if not self._mgmt_handle:
            self.cli_log_err("Management port is not connected")
            return "[FAIL]: Management port is not connected"

        self._mgmt_handle.sendline("sudo -k " + cmd)
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [userid + ":"])
        if idx < 0:
            rs = self._mgmt_handle.before
            self._mgmt_handle.logfile_read = None
            self._mgmt_handle.logfile_send = None
            self.mtp_mgmt_disconnect()
            return rs
        self._mgmt_handle.sendline(passwd)

        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [self._mgmt_prompt])
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            return "[FAIL]: Connect to mtp mgmt timeout"
        else:
            rs = self._mgmt_handle.before

        return rs  

    def mtp_get_mac(self):
        # MTP MAC info
        rs = ""
        cmd = MFG_DIAG_CMDS.MTP_MAC_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute cmd to get MTP MAC info", level = 0)
            return "[FAIL]: Failed to execute cmd to get MTP MAC info"
        match = re.findall(r"(([0-9a-f]{2}[:]){5}([0-9a-f]{2}))", self.mtp_get_cmd_buf())
        if match:
            return match[0][0]
        else:
            self.cli_log_err("Failed to locate MTP MAC info." + self.mtp_get_cmd_buf(), level = 0)
            return "[FAIL]: Failed to locate MTP MAC info"

    def mtp_get_memory_size(self):
        """
        return mtp memory size in KB to differntiate if it is 4G Tubor MTP or 8G Turbo MTP;
        Since for run_l1 test, 4G memory can run 5 NIC card in parallel while 8G memory can run all 10 NIC in parallel
        """
        memorysize = ""
        cmd = "cat /proc/meminfo"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute cmd to get MTP Memory info", level = 0)
            return memorysize
        match = re.findall(r"MemTotal:\s+(\d+)\s+kB", self.mtp_get_cmd_buf())
        if match:
            memorysize = match[0]
            self.cli_log_inf("MTP Total Memory is {:.2f} GB".format(int(memorysize) / 1024.0 / 1024.0), level = 0)
        else:
            self.cli_log_err("Failed to locate MTP MAC info." + self.mtp_get_cmd_buf(), level = 0)
        return memorysize

    def mtp_set_sn_rev_mac_command(self, sn, maj, mac):
        cmd = MFG_DIAG_CMDS.MTP_FRU_PROG_SN_MAJ_MAC_FMT.format(sn, maj, mac)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Unable to set MTP SN, REV and MAC")
            return False
        match = re.findall(r"Programming", self.mtp_get_cmd_buf())
        if match:
            cmd = "eeutil -disp"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Unable to display MTP SN, REV and MAC info")
                return False                
            
            match = re.findall(r"SERIAL_NUM\s+(\S+)", self.mtp_get_cmd_buf())
            if match:
                prog_sn = match[0]
                if prog_sn != sn:
                    self.cli_log_err("Failed to set MTP SN info", level = 0)
                    return False
            else:
                self.cli_log_err("Failed to locate MTP SN info", level = 0)
                return False

            match = re.findall(r"HW_MAJOR_REV\s+(\S+)", self.mtp_get_cmd_buf())        
            if match:
                prog_maj = match[0]
                if prog_maj != maj:
                    self.cli_log_err("Failed to set MTP REV info", level = 0)
                    return False
            else:
                self.cli_log_err("Failed to locate MTP REV info", level = 0)
                return False                

            match = re.findall(r"MAC_ADDR\s+(\S+)", self.mtp_get_cmd_buf())        
            if match:
                prog_mac = match[0]
                if prog_mac != mac:
                    self.cli_log_err("Failed to set MTP MAC info", level = 0)
                    return False
            else:
                self.cli_log_err("Failed to locate MTP MAC info", level = 0)
                return False 

            return True
        else:
            self.cli_log_err("Failed to set MTP SN, REV and MAC info", level = 0)
            return False
        return True

    def mtp_nic_send_ctrl_c(self, slot):
        if self._nic_ctrl_list[slot] == None:
            # script not running anything.
            return True
        if not self._nic_ctrl_list[slot].nic_send_ctrl_c():
            self.mtp_dump_nic_err_msg(slot)
            self.cli_log_slot_err(slot, "Couldn't send C+C")
            return False
        return True

    def mtp_nic_stop_test(self, slot):
        cmd_buf = self._nic_ctrl_list[slot]._cmd_buf  #save failure buffer
        self.mtp_nic_send_ctrl_c(slot)
        self.mtp_mgmt_exec_cmd_para(slot, MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT)
        self._nic_ctrl_list[slot]._cmd_buf = cmd_buf  #restore failure buffer

    def mtp_mgmt_set_date(self, stage=None):
        timestamp_str = str(libmfg_utils.timestamp_snapshot())
        cmd = MFG_DIAG_CMDS.NIC_DATE_SET_FMT.format(timestamp_str)
        if stage == FF_Stage.FF_FST:
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Unable to set MTP date")
                return False
            return True
        #else:
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_err("Unable to set MTP date")
            return False

        return True


    def mtp_sys_info_init(self):
        # MTP IO cpld version
        reg_addr = 0x0
        cmd = MFG_DIAG_CMDS.MTP_CPLD_READ_FMT.format(reg_addr)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get MTP IO-CPLD image version info", level = 0)
            return False
        match = re.findall(r"addr 0x{:x} with data (0x[0-9a-fA-F]+)".format(reg_addr), self.mtp_get_cmd_buf())
        if match:
            self._io_cpld_ver = match[0]
        else:
            self.cli_log_err("Failed to get MTP IO-CPLD image version info", level = 0)
            return False

        # MTP JTAG cpld version
        reg_addr = 0x19
        cmd = MFG_DIAG_CMDS.MTP_CPLD_READ_FMT.format(reg_addr)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get MTP JTAG-CPLD image version info", level = 0)
            return False
        match = re.findall(r"addr 0x{:x} with data (0x[0-9a-fA-F]+)".format(reg_addr), self.mtp_get_cmd_buf())
        if match:
            self._jtag_cpld_ver = match[0]
        else:
            self.cli_log_err("Failed to get MTP JTAG-CPLD image version info", level = 0)
            return False

        # MTP_TYPE
        cmd = MFG_DIAG_CMDS.MTP_ASIC_SUPPORTED_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to send command for getting asic supported version", level = 0)
            return False
        match = re.findall(r"MTP_TYPE=MTP_([a-zA-Z_]+)", self.mtp_get_cmd_buf())
        if match:
            self._asic_support = match[0].strip().upper()
        else:
            self.cli_log_err("Failed to get asic supported version", level = 0)
            return False

        # MTP_REV
        cmd = MFG_DIAG_CMDS.MTP_REV_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to send command for getting MTP revision", level = 0)
            return False
        match = re.findall(r"MTP_REV=REV_([0-9]{2}|NONE)", self.mtp_get_cmd_buf())
        if match:
            self._mtp_rev = match[0]
        else:
            self.cli_log_err("Failed to get MTP revision", level = 0)
            return False

        # MTP OS version
        cmd = MFG_DIAG_CMDS.MTP_IMG_VER_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get os image version", level = 0)
            return False
        match = re.findall(r"SMP (.* 20\d{2})", self.mtp_get_cmd_buf())
        if match:
            self._os_ver = match[0]
        else:
            self.cli_log_err("Failed to get os image version", level = 0)
            return False

        # MTP Diag image version
        cmd = MFG_DIAG_CMDS.MTP_DIAG_VERSION_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get diag image version", level = 0)
            return False
        match = re.findall(r"Date: +(.*20\d{2})", self.mtp_get_cmd_buf())
        if match:
            self._diag_ver = match[0]
        else:
            self.cli_log_err("Failed to get diag image version", level = 0)
            return False

        # MTP ASIC image version
        cmd = MFG_DIAG_CMDS.MTP_ASIC_VERSION_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get asic util version", level = 0)
            return False
        match = re.findall(r"Date: +(.*20\d{2})", self.mtp_get_cmd_buf())
        if match:
            self._asic_ver = match[0]
        else:
            self.cli_log_err("Failed to get asic util version", level = 0)
            return False

        return True

    def mtp_get_asic_support(self):
        return self._asic_support

    def mtp_get_hw_version(self):
        return [self._io_cpld_ver, self._jtag_cpld_ver]


    def mtp_get_os_version(self):
        return self._os_ver


    def mtp_get_sw_version(self):
        return self._diag_ver


    def mtp_get_asic_version(self):
        return self._asic_ver

    def mtp_get_swmtestmode(self, slot):
        return self._swmtestmode[slot]

    def mtp_set_swmtestmode(self, swmtestmode):
        read_data = [0]
        for slot in range(self._slots):
            self._swmtestmode[slot] = swmtestmode

        for slot in range(self._slots):
            if self._swmtestmode[slot] == Swm_Test_Mode.SW_DETECT:
                read_data[0] = 0x00
                #See if we can read the MTP Adapter CPLD ID.  This would indicate an ALOM should be present
                rc = self._nic_ctrl_list[slot].nic_read_mtp_adapt_cpld(0x80, read_data)
                if read_data[0] == 0x1b:
                    self.cli_log_slot_inf(slot, "NAPLES25SWM ALOM DETECTED")
                    self._swmtestmode[slot] = Swm_Test_Mode.SWMALOM
                else:
                    self._swmtestmode[slot] = Swm_Test_Mode.SWM
        return True

    def mtp_set_nic_status_fail(self, slot, skip_fa=False):
        if self._nic_ctrl_list:
            # was previously OK, this is first failure
            if self.mtp_check_nic_status(slot) and not skip_fa:
                libmfg_utils.post_fail_steps(self, slot)

            # failed inside libnic_ctrl, didnt trigger post_fail_steps
            elif self.mtp_check_nic_missed_fa(slot) and not skip_fa:
                libmfg_utils.post_fail_steps(self, slot)
            self._nic_ctrl_list[slot].nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)

    def mtp_clear_nic_status(self, slot):
        if self._nic_ctrl_list:
            self._nic_ctrl_list[slot].nic_set_status(NIC_Status.NIC_STA_OK)

    def mtp_stale_image_cleanup(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = "rm -f naples* image_a*"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        return True


    def mtp_update_mtp_diag_image(self, image):
        cmd = "rm -rf {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_MTP_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = "tar zxf {:s}".format(image)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        return True


    def mtp_update_nic_diag_image(self, image):
        cmd = "rm -rf {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = "tar zxf {:s} -C {:s}".format(image, MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        return True


    def mtp_mgmt_poweroff(self):
        if not self.mtp_mgmt_exec_cmd("sync", timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute sync command")
            return False

        if not self.mtp_mgmt_exec_sudo_cmd("poweroff"):
            self.cli_log_err("Failed to execute poweroff command")
            return False

        return True

    def mtp_mgmt_reboot(self):
        if not self.mtp_mgmt_exec_cmd("sync", timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute sync command")
            return False

        if not self.mtp_mgmt_exec_sudo_cmd("reboot"):
            self.cli_log_err("Failed to execute reboot command")
            return False

        self.cli_log_inf("Reboot occured, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_REBOOT_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_REBOOT_DELAY)

        return True


    def mtp_chassis_shutdown(self):
        self.mtp_mgmt_poweroff()
        self.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        self.mtp_apc_pwr_off()
        self.cli_log_inf("Power off APC, Wait {:d} seconds for APC shutdown".format(MTP_Const.MTP_POWER_CYCLE_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)


    def mtp_power_cycle(self):
        self.mtp_mgmt_poweroff()
        self.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        self.cli_log_inf("Power off APC", level=0)
        self.mtp_apc_pwr_off()
        libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
        self.mtp_apc_pwr_on()
        self.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
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


    def mtp_nic_diag_fail_report(self, slot, sn):
        msg = "SN[{:s}]".format(sn) + MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL
        self.cli_log_slot_err(slot, msg)


    def mtp_nic_diag_pass_report(self, slot, sn):
        msg = "SN[{:s}]".format(sn) + MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS
        self.cli_log_slot_inf(slot, msg)


    def mtp_misc_init(self):
        # vrm test
        cmd = MFG_DIAG_CMDS.MTP_VRM_TEST_FMT
        pass_sig_list = [MFG_DIAG_SIG.MTP_VRM_OK_SIG]
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list, timeout=MTP_Const.MTP_OS_CMD_DELAY)
        if rc:
            self.cli_log_inf("VRM test passed")
        else:
            self.cli_log_err("VRM test failed")

        return rc

    def mtp_psu_init(self):
        rc = True
        # store serial number
        for psu in range(self._psu_num):
            psu = str(psu+1)
            cmd = MFG_DIAG_CMDS.MTP_PSU_DISP_FMT.format(psu)
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
                self.cli_log_err("Executing command {:s} failed".format(cmd))
                rc = False
                continue
            psu_sn_match = re.search("MFR_SERIAL: *(.*)", self.mtp_get_cmd_buf())
            if not psu_sn_match:
                self.cli_log_err("Failed to read PSU_{:s} Serial Number".format(psu))
                if not MFG_BYPASS_PSU_CHECK:
                    rc = False
                continue
            self._psu_sn[psu] = psu_sn_match.group(1).strip()

        # PSU test
        cmd = MFG_DIAG_CMDS.MTP_PSU_TEST_FMT
        pass_sig_list = []

        # apc_cfg is a list with format [apc1, apc1_port, apc1_userid, apc1_passwd, apc2, apc2_port, apc2_userid, apc2_passwd]
        if not MFG_BYPASS_PSU_CHECK and self._mtp_rev is not None and self._mtp_rev != "NONE" and len(self._mtp_rev) > 0:
            if int(self._mtp_rev) > 3:
                apc1 = self._apc_cfg[0]
                apc2 = self._apc_cfg[4]
                if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
                    self.cli_log_err("Failed to get MTP PSU info", level = 0)
                    return False

                if apc1 != "" :
                    match = re.search(MFG_DIAG_SIG.MTP_PSU1_OK_SIG, self.mtp_get_cmd_buf())
                    if match:
                        match_psu = re.search(r"PSU_1\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+", self.mtp_get_cmd_buf())
                        if match_psu:
                            pout = match_psu.group(1)
                            pin = match_psu.group(4)
                            if "-" in pin or "-" in pout:
                                self.cli_log_err("PSU1 test failed (pout:{:s}, pin:{:s})".format(pout, pin))
                                rc = False
                        else:
                            self.cli_log_err("PSU1 test failed.")
                            rc = False
                    else:
                        self.cli_log_err("PSU1 result test failed.")
                        rc = False

                if apc2 != "" :
                    match = re.search(MFG_DIAG_SIG.MTP_PSU2_OK_SIG, self.mtp_get_cmd_buf())
                    if match:
                        match_psu = re.search(r"PSU_2\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+", self.mtp_get_cmd_buf())
                        if match_psu:
                            pout = match_psu.group(1)
                            pin = match_psu.group(4)
                            if "-" in pin or "-" in pout:
                                self.cli_log_err("PSU2 test failed (pout:{:s}, pin:{:s})".format(pout, pin))
                                rc = False
                        else:
                            self.cli_log_err("PSU2 test failed")
                            rc = False
                    else:
                        self.cli_log_err("PSU2 result test failed.")
                        rc = False
                if rc:
                    self.cli_log_inf("PSU test passed")

        return rc

    def mtp_fan_init(self, fan_spd):
        rc = True
        # Fan present test
        cmd = MFG_DIAG_CMDS.MTP_FAN_PRSNT_FMT
        if self.get_mtp_factory_location() == Factory.LAB:
            pass_sig_list = [MFG_DIAG_SIG.MTP_FAN0_PRSNT_SIG, MFG_DIAG_SIG.MTP_FAN1_PRSNT_SIG, MFG_DIAG_SIG.MTP_FAN2_PRSNT_SIG]
        else:
            pass_sig_list = [MFG_DIAG_SIG.MTP_PRSNT_SIG]
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list, timeout=MTP_Const.MTP_OS_CMD_DELAY)
        if rc:
            self.cli_log_inf("FAN present test passed")
        else:
            self.cli_log_err("FAN present test failed")
            return rc

        # Fan speed test
        cmd = MFG_DIAG_CMDS.MTP_FAN_TEST_FMT
        pass_sig_list = [MFG_DIAG_SIG.MTP_FAN_OK_SIG]
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list, timeout=MTP_Const.MTP_OS_CMD_DELAY)
        if rc:
            self.cli_log_inf("FAN speed test passed")
        else:
            self.cli_log_err("FAN speed test failed")
            return rc

        # Fan speed set
        self.cli_log_inf("Set FAN Speed to {:d}%".format(fan_spd))
        cmd = MFG_DIAG_CMDS.MTP_FAN_SET_SPD_FMT.format(fan_spd)
        rc = self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY)
        if not rc:
            self.cli_log_err("Failed to set fan speed to {:d}%".format(fan_spd))

        self._fanspd = fan_spd          # update class variable

        # Fan status dump
        cmd = MFG_DIAG_CMDS.MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
            rc = False

        return rc

    def mtp_get_nic_sn_start(self, slot=0):
        rc = ""
        cmd = "eeutil -uut=UUT_{:s} -disp -field=sn".format(str(slot + 1))
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP get Serial Number Failed.")
            return rc

        #[INFO]    [2022-04-22-14:36:41.01 ] Serial Number                                FPN21370231
        match = re.search(r"Serial\sNumber\s+([A-Za-z0-9]{8,})", self.mtp_get_cmd_buf())
        if match:
            # validate the readings
            sn = match.group(1)
            rc = sn

        return rc

    def mtp_diag_pre_init(self, start_dsp=True):
        # start the mtp diag
        self.cli_log_inf("Pre Diag SW Environment Init", level=0)

        cmd = "touch /dev/prompt"
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_err("{:s} command failed".format(cmd), level=0)
            return False

        cmd = MFG_DIAG_CMDS.MTP_DIAG_INIT_FMT
        sig_list = [MFG_DIAG_SIG.MTP_DIAG_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = "source ~/.bash_profile"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=5):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = "env | grep UUT"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute env command", level=0)
            return False

        if start_dsp:
            # kill other diagmgr instances
            cmd = "killall diagmgr"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Command {:s} failed".format(cmd), level=0)
                return False

            # start the mtp diagmgr
            diagmgr_handle = self.mtp_session_create()
            if not diagmgr_handle:
                self.cli_log_err("Failed to create diagmgr session", level=0)
                return False

            cmd = MFG_DIAG_CMDS.MTP_DIAG_MGR_START_FMT.format(self._diagmgr_logfile)
            diagmgr_handle.sendline(cmd)
            idx = libmfg_utils.mfg_expect(diagmgr_handle, [self._mgmt_prompt])
            if idx < 0:
                self.cli_log_err("Failed to start diagmgr", level=0)
                return False
            time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
            diagmgr_handle.close()

            # register MTP diagsp
            cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to access dshell", level=0)
                return False

            cmd = MFG_DIAG_CMDS.MTP_DSP_START_FMT
            sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
                self.cli_log_err("Failed to start dsp", level=0)
                return False

            time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        if not self.mtp_sys_info_init():
            self.cli_log_err("Failed to Init MTP system information", level=0)
            return False

        self.cli_log_inf("Pre Diag SW Environment Init complete\n", level=0)
        return True

    def mtp_inlet_temp_test(self, stage=None, sanity=False):
        rc = True
        cmd = MFG_DIAG_CMDS.MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP get inlet temperature failed")
            return False

        # Current Fan Speed display
        ret = re.findall(r'NAME\s+FAN\d-Inlet\s+|FAN\d-Inlet\s+|FAN\d-Outlet\s', self.mtp_get_cmd_buf())
        if not ret:
            self.cli_log_err("MTP get fan name failed")
            return False
        if not sanity:
            self.cli_log_inf("".join(ret).strip('\n'))
        ret = re.search(r'FAN(\s+\d{3,}){6}(\s+\d{2,}){2}', self.mtp_get_cmd_buf())
        if not ret:
            self.cli_log_err("MTP get fan speed failed")
            return False
        if not sanity:
            self.cli_log_inf(ret.group(0))

        # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
        # FAN                 23.50          25.50          21.75          21.75
        match = re.search(r"FAN +(-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+)", self.mtp_get_cmd_buf())
        if match:
            # validate the readings
            inlet_1 = float(match.group(3))
            inlet_2 = float(match.group(4))
            inlet_1_rs = True
            inlet_2_rs = True
            max_temp = 70
            min_temp = -10

            if (inlet_1 < min_temp or inlet_1 > max_temp):
                inlet_1_rs = False
                rc = False
            if (inlet_2 < min_temp or inlet_2 > max_temp):
                inlet_2_rs = False
                rc = False

            if not rc:
                if not inlet_1_rs and not inlet_2_rs:
                    if inlet_1 < min_temp and inlet_2 < min_temp:
                        self.cli_log_err("Inlet1 ({:s}) is lesser than {:s} degree, Inlet2 ({:s}) is lesser than {:s} degree, temperature test failed".format(str(inlet_1), str(min_temp), str(inlet_2), str(min_temp)))
                    elif inlet_1 < min_temp and inlet_2 > max_temp:
                        self.cli_log_err("Inlet1 ({:s}) is lesser than {:s} degree, Inlet2 ({:s}) is greater than {:s} degree, temperature test failed".format(str(inlet_1), str(min_temp), str(inlet_2), str(max_temp)))
                    elif inlet_1 > max_temp and inlet_2 < min_temp:
                        self.cli_log_err("Inlet1 ({:s}) is geater than {:s} degree, Inlet2 ({:s}) is lesswe than {:s} degree, temperature test failed".format(str(inlet_1), str(max_temp), str(inlet_2), str(min_temp)))
                    else:
                        self.cli_log_err("Inlet1 ({:s}) is geater than {:s} degree, Inlet2 ({:s}) is greater than {:s} degree, temperature test failed".format(str(inlet_1), str(max_temp), str(inlet_2), str(max_temp)))
                elif not inlet_1_rs:
                    if inlet_1 < min_temp:
                        self.cli_log_err("Inlet1 ({:s}) is lesser than {:s} degree, Inlet2 ({:s}), temperature test failed".format(str(inlet_1), str(min_temp), str(inlet_2)))
                    else:
                        self.cli_log_err("Inlet1 ({:s}) is greater than {:s} degree, Inlet2 ({:s}), temperature test failed".format(str(inlet_1), str(max_temp), str(inlet_2)))
                elif not inlet_2_rs:
                    if inlet_2 < min_temp:
                        self.cli_log_err("Inlet1 ({:s}), Inlet2 ({:s}) is lesser than {:s} degree, temperature test failed".format(str(inlet_1), str(inlet_2), str(min_temp)))
                    else:
                        self.cli_log_err("Inlet1 ({:s}), Inlet2 ({:s}) is greater than {:s} degree, temperature test failed".format(str(inlet_1), str(inlet_2), str(max_temp)))

            else:
                self.cli_log_inf("Inlet1 ({:s}), Inlet2 ({:s}) temperature test passed".format(str(inlet_1), str(inlet_2)))

        else:
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP get inlet temperature failed")
            return False

        return rc

    def mtp_diag_dsp_restart(self):
        self.cli_log_inf("DSP Restart", level=0)

        # stop MTP DSP
        cmd = MFG_DIAG_CMDS.MTP_DSP_STOP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        # sys cleanup
        cmd = MFG_DIAG_CMDS.MTP_DSP_CLEANUP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        # kill other diagmgr instances
        cmd = "killall diagmgr"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False

        # start the mtp diagmgr
        diagmgr_handle = self.mtp_session_create()
        if not diagmgr_handle:
            self.cli_log_err("Failed to create new diagmgr handle", level=0)
            return False

        cmd = MFG_DIAG_CMDS.MTP_DIAG_MGR_RESTART_FMT.format(self._diagmgr_logfile)
        diagmgr_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(diagmgr_handle, ["$"])
        if idx < 0:
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            self.cli_log_err("{:s}".format(diagmgr_handle.before))
            return False
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
        diagmgr_handle.close()

        # register MTP diagsp
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False

        cmd = MFG_DIAG_CMDS.MTP_DSP_START_FMT
        sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False

        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        self.cli_log_inf("DSP restart complete\n", level=0)

        return True

    def mtp_diag_zmq_init(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        retry = 0

        while retry < 3:
            retry += 1
            self.cli_log_inf("Init Diag ZMQ Environment <{:d}>...".format(retry), level=0)
            # 1. stop ZMQ
            cmd = MFG_DIAG_CMDS.MTP_ZMQ_STOP_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False

            # 2. stop MTP DSP
            cmd = MFG_DIAG_CMDS.MTP_DSP_STOP_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False
            time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

            # 3. sys cleanup
            cmd = MFG_DIAG_CMDS.MTP_DSP_CLEANUP_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False

            # 4. start MTP DSP
            cmd = MFG_DIAG_CMDS.MTP_DSP_START_FMT
            sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False
            time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

            # 5. start ZMQ
            cmd = MFG_DIAG_CMDS.MTP_ZMQ_START_FMT
            sig_list = [MFG_DIAG_SIG.MTP_ZMQ_OK_SIG]
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
                continue
            else:
                break

        if retry >= 3:
            self.cli_log_err("Failed to Init Diag ZMQ Environment", level=0)
            return False

        self.cli_log_inf("Init Diag ZMQ Environment complete\n", level=0)
        return True


    def mtp_diag_get_img_files(self):
        cmd = "ls --color=never {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd), level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf().split()
        return cmd_buf


    def mtp_diag_post_init(self):
        self.cli_log_inf("Post Diag SW Environment Init", level=0)
        cmd = "rm -f {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to remove previous ASIC test logfile", level=0)
            return False
        cmd = "rm -f {:s}".format(MTP_DIAG_Logfile.ONBOARD_CSP_LOG_FILES)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to remove previous CSP test logfile", level=0)
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to Init DiagSP", level=0)
            return False

        cmd = MFG_DIAG_CMDS.MTP_DSP_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Dump DSP failed", level=0)
            return False

        self.cli_log_inf("Post Diag SW Environment Init complete\n", level=0)
        return True


    # make sure mtp_hw_init is always done after mtp_sys_info_init, as it needs info collected from it
    def mtp_hw_init(self, stage=None):
        rc = True

        fan_spd = libmfg_utils.pick_fan_speed(stage)

        self.cli_log_inf("Start MTP chassis sanity check", level = 0)
        # mtp cpld test
        rc &= self.mtp_cpld_test()
        # fan init
        rc &= self.mtp_fan_init(fan_spd)
        # read psu info and test psu
        rc &= self.mtp_psu_init()
        # mtp inlet temperature
        rc &= self.mtp_inlet_temp_test(stage, sanity=True)

        # other platform init
        rc &= self.mtp_misc_init()
        if rc:
            self.cli_log_inf("MTP chassis sanity check passed\n", level = 0)
        else:
            self.cli_log_err("MTP chassis sanity check failed\n", level = 0)

        return rc


    def mtp_wait_temp_ready(self, low_threshold=None, high_threshold=None):
        if low_threshold != None:
            self.cli_log_inf("Wait the environment temperature drop to {:2.2f}".format(low_threshold))
            upper_limit = MTP_Const.LOW_CHAMBER_UPPER_LIMIT
            lower_limit = MTP_Const.LOW_CHAMBER_LOWER_LIMIT
            if not GLB_CFG_MFG_TEST_MODE:
                upper_limit = MTP_Const.HIGH_CHAMBER_UPPER_LIMIT
                lower_limit = MTP_Const.LOW_CHAMBER_LOWER_LIMIT
        elif high_threshold != None:
            self.cli_log_inf("Wait the environment temperature rise to {:2.2f}".format(high_threshold))
            upper_limit = MTP_Const.HIGH_CHAMBER_UPPER_LIMIT
            lower_limit = MTP_Const.HIGH_CHAMBER_LOWER_LIMIT
            if not GLB_CFG_MFG_TEST_MODE:
                upper_limit = MTP_Const.HIGH_CHAMBER_UPPER_LIMIT
                lower_limit = MTP_Const.LOW_CHAMBER_LOWER_LIMIT
        else:
            # in NT, just read the inlet temp
            inlet = self.mtp_get_inlet_temp(low_threshold, high_threshold)
            if inlet == None:
                return False
            self.cli_log_inf("Current Environment temperature is {:2.2f}".format(inlet))
            self.cli_log_inf("No threshold set, bypass ambient temperature check")
            return True

        timeout = MTP_Const.MFG_TEMP_WAIT_TIMEOUT
        while timeout > 0:
            inlet = self.mtp_get_inlet_temp(low_threshold, high_threshold)
            if not MFG_BYPASS_PSU_CHECK and self._mtp_rev is not None and self._mtp_rev != "NONE" and len(self._mtp_rev) > 0 and int(self._mtp_rev) > 3:
                cmd = MFG_DIAG_CMDS.MTP_PSU_TEST_FMT
                self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY)

            if inlet == None:
                return False
            if low_threshold != None:
                if inlet > upper_limit:
                    time.sleep(MTP_Const.MFG_TEMP_CHECK_INTERVAL)
                    timeout -= 1
                else:
                    break
            else:
                if inlet < lower_limit:
                    time.sleep(MTP_Const.MFG_TEMP_CHECK_INTERVAL)
                    timeout -= 1
                else:
                    break

        if timeout <= 0:
            total_time = MTP_Const.MFG_TEMP_WAIT_TIMEOUT * MTP_Const.MFG_TEMP_CHECK_INTERVAL
            if low_threshold != None:
                self.cli_log_err("Environment temperature can not reach {:2.2f} after {:d} seconds".format(upper_limit, total_time))
            else:
                self.cli_log_err("Environment temperature can not reach {:2.2f} after {:d} seconds".format(lower_limit, total_time))
            self.cli_log_err("Current Environment temperature is {:2.2f}".format(inlet))
            return False
        self.cli_log_inf("Environment temperature is reached, current inlet reading is {:2.2f}".format(inlet))

        # mtp sensor test, make sure two inlet sensor reading difference is less than 5
        if not self.mtp_inlet_sensor_test():
            self.cli_log_err("MTP temp sensor test failed")
            return False

        return True


    def mtp_wait_soaking(self):
        # Soaking process
        if GLB_CFG_MFG_TEST_MODE:
            timeout = MTP_Const.MFG_TEMP_SOAK_TIMEOUT
        else:
            timeout = MTP_Const.MFG_MODEL_TEMP_SOAK_TIMEOUT
        self.cli_log_inf("Start soaking process, wait for {:d} seconds".format(timeout * MTP_Const.MFG_TEMP_CHECK_INTERVAL))
        libmfg_utils.count_down(timeout * MTP_Const.MFG_TEMP_CHECK_INTERVAL)

        self.cli_log_inf("Soaking process complete")

        return True


    def mtp_cpld_test(self):
        cpld_ver_list = self.mtp_get_hw_version()
        if not cpld_ver_list:
            self.cli_log_err("Unable to retrieve MTP CPLD version")
            self.cli_log_err("MTP CPLD test failed")
            return False

        io_version = MTP_IMAGES.mtp_io_cpld_ver[self._asic_support]
        jtag_version = MTP_IMAGES.mtp_jtag_cpld_ver[self._asic_support]

        if self._mtp_rev is not None and self._mtp_rev != "NONE" and len(self._mtp_rev) > 0 and int(self._mtp_rev) > 2:
            if int(cpld_ver_list[0],16) < int(io_version,16):
                self.cli_log_err("MTP IO CPLD Version: {:s}, expect: {:s}".format(cpld_ver_list[0], io_version))
                self.cli_log_err("MTP CPLD test failed")
                return False

            if cpld_ver_list[1] != jtag_version:
                self.cli_log_err("MTP JTAG CPLD Version: {:s}, expect: {:s}".format(cpld_ver_list[1], jtag_version))
                self.cli_log_err("MTP CPLD test failed")
                return False
            self.cli_log_inf("MTP CPLD test passed")
        else:
            self.cli_log_inf("MTP CPLD test skipped for REV_{:s}".format(self._mtp_rev))
        return True


    def mtp_inlet_sensor_test(self):
        cmd = MFG_DIAG_CMDS.MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("MTP Inlet sensor test failed")
            return False

        # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
        # FAN                 23.50          25.50          21.75          21.75
        match = re.search(r"FAN +(-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+)", self.mtp_get_cmd_buf())
        if match:
            # validate the readings
            inlet_1 = float(match.group(3))
            inlet_2 = float(match.group(4))
            inlet_diff = abs(inlet_1 - inlet_2)
            # if the difference is more than 10, something is wrong, relay on any inlet near the threshold
            if inlet_diff > 10.0:
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP Inlet sensor test failed")
                return False
            else:
                self.cli_log_inf("MTP Inlet sensor test passed")
                return True
            return True
        else:
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP Inlet sensor test failed")
            return False


    def mtp_get_inlet_temp(self, low_threshold, high_threshold):
        cmd = MFG_DIAG_CMDS.MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP get inlet temperature failed")
            return 0.00

        # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
        # FAN                 23.50          25.50          21.75          21.75
        match = re.search(r"FAN +(-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+)", self.mtp_get_cmd_buf())
        if match:
            # validate the readings
            inlet_1 = float(match.group(3))
            inlet_2 = float(match.group(4))
            inlet_diff = abs(inlet_1 - inlet_2)
            # if the difference is more than 10, something is wrong, relay on any inlet near the threshold
            if inlet_diff > 10.0:
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                if low_threshold != None:
                    temp = low_threshold
                elif high_threshold != None:
                    temp = high_threshold
                else:
                    temp = 25

                # return the nearest inlet reading
                if abs(inlet_1 - temp) < abs(inlet_2 - temp):
                    return inlet_1
                else:
                    return inlet_2
            else:
                return (inlet_1 + inlet_2) / 2
            return 25
        else:
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("Unable to get inlet temperature")
            return 0.00

    def mtp_get_fanspd(self):
        """
         Returns the fanspeed (in percent) that had been set by the script.
         Does NOT return live status --> use mtp_get_inlet_temp() for that.
        """
        return self._fanspd

    # return list of error message
    def mtp_mgmt_retrieve_nic_l1_err(self, sn):
        err_msg_list = list()
        pass_count = 0
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR
        #logfile_exp = r"(cap|elb)_l1_screen_board_{:s}.*log".format(sn)
        logfile_exp = r"l1_screen_board_{:s}.*log".format(sn)
        for filename in os.listdir(path):
            if re.match(logfile_exp, filename):
                with open(os.path.join(path, filename), 'r') as f:
                    for line in f:
                        #if MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG in line:
                        #    err_msg = line.replace('\n', '')
                        #    err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG):]
                        #    err_msg_list.append(err_msg)
                        #if MFG_DIAG_SIG.MFG_ASIC_CTC_ERR_MSG_SIG in line:
                        #    err_msg = line.replace('\n', '')
                        #    err_msg_list.append(err_msg)
                        #if MFG_DIAG_SIG.MFG_ASIC_PCIE_MAPPING_MSG_SIG in line:
                        #    err_msg = line.replace('\n', '')
                        #    err_msg_list.append(err_msg)
                        if MFG_DIAG_SIG.MFG_ASIC_FAIL_MSG_SIG in line:
                            err_msg = line.replace('\n', '')
                            err_msg_list.append(err_msg)
                        if MFG_DIAG_SIG.MFG_ASIC_PASS_MSG_SIG in line:
                            pass_count += 1

        return pass_count, err_msg_list

    # return list of error message
    def mtp_nic_retrieve_arm_l1_err(self, sn):
        err_msg_list = list()
        pass_count = 0
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR
        logfile_exp = r"{:s}_elba_arm_l1_test\.log".format(sn)
        for filename in os.listdir(path):
            if re.match(logfile_exp, filename):
                with open(os.path.join(path, filename), 'r') as f:
                    for line in f:
                        if MFG_DIAG_SIG.MFG_ASIC_FAIL_MSG2_SIG in line:
                            err_msg = line.replace('\n', '')
                            err_msg_list.append(err_msg)
                        if MFG_DIAG_SIG.MFG_ASIC_PASS_MSG2_SIG in line:
                            pass_count += 1

        return pass_count, err_msg_list


    # return list of error message
    def mtp_mgmt_retrieve_mtp_para_err(self, sn, test):
        err_msg_list = list()
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR

        if test == "PRBS_ETH":
            filename = "{:s}_prbs_eth.log".format(sn)
        elif test == "PRBS_PCIE":
            filename = "{:s}_prbs_pcie.log".format(sn)
        elif test == "SNAKE_HBM":
            filename = "{:s}_snake_hbm.log".format(sn)
        elif test == "SNAKE_PCIE":
            filename = "{:s}_snake_pcie.log".format(sn)
        elif test == "SNAKE_ELBA":
            filename = "{:s}_snake_elba.log".format(sn)
        elif test == "ETH_PRBS":
            filename = "{:s}_elba_PRBS_MX.log".format(sn)
        elif test == "ARM_L1":
            filename = "{:s}_elba_arm_l1_test.log".format(sn)
        elif test == "DDR_BIST":
            filename = "{:s}_arm_ddr_bist_0.log".format(sn)
            filename = "{:s}_arm_ddr_bist_1.log".format(sn)
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return err_msg_list

        try:
            with open(os.path.join(path, filename), 'r') as f:
                for line in f:
                    if MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG in line:
                        err_msg = line.replace('\n', '')
                        err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG):]
                        err_msg_list.append(err_msg)
        except:
            err_msg_list.append("{:s} doesn't exist".format(filename))

        return err_msg_list

    def mtp_nic_check_extdiag_boot(self, slot):
        qspi_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not qspi_info:
            self.cli_log_slot_err_lock(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = qspi_info[0]
        if boot_image != "extdiag":
            self.cli_log_slot_err_lock(slot, "NIC is booted from {:s}".format(boot_image))
            return False

        return True

    def mtp_verify_nic_extdiag_boot(self, slot):
        if not self.mtp_nic_boot_info_init(slot, skip_check=True):
            self.cli_log_slot_err(slot, "Init NIC sw boot info failed")
            return False

        return self.mtp_nic_check_extdiag_boot(slot)

    def mtp_verify_nic_extdiag_smode_boot(self, slot):
        if not self.mtp_nic_boot_info_init(slot, smode=True):
            self.cli_log_slot_err(slot, "Init NIC sw boot info failed")
            return False

        return self.mtp_nic_check_extdiag_boot(slot)

########################################
######  NIC CTRL Routines ##############
########################################

# 1. Routines that need console, can not be run in parallel
    def mtp_nic_boot_info_init(self, slot, smode=False, skip_check=False):
        if self._nic_ctrl_list[slot]._boot_image is not None and self._nic_ctrl_list[slot]._kernel_timestamp is not None and not skip_check:
            # no need to do this
            self.cli_log_slot_inf(slot, "NIC boot info already present")
            return True
        self.cli_log_slot_inf(slot, "Init NIC boot info")
        if not self._nic_ctrl_list[slot].nic_boot_info_init(smode=smode):
            self.cli_log_slot_err(slot, "Init NIC boot info failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)

            cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_PICOCOM_FMT
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=10):
                self.cli_log_err("Execute command {:s} failed".format(cmd))
                return False

            return False

        cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_PICOCOM_FMT
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=10):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        return True


    def mtp_nic_check_diag_boot(self, slot):
        qspi_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not qspi_info:
            self.cli_log_slot_err_lock(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = qspi_info[0]
        if boot_image != "diagfw":
            self.cli_log_slot_err_lock(slot, "NIC is booted from {:s}".format(boot_image))
            return False

        return True

    def mtp_verify_nic_diag_boot(self, slot):
        if not self.mtp_nic_boot_info_init(slot):
            self.cli_log_slot_err(slot, "Init NIC sw boot info failed")
            return False

        return self.mtp_nic_check_diag_boot(slot)

    def mtp_mgmt_verify_nic_gold_boot(self, slot):
        if not self.mtp_nic_boot_info_init(slot):
            self.cli_log_slot_err(slot, "Init NIC gold boot info failed")
            return False

        gold_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not gold_info:
            self.cli_log_slot_err(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = gold_info[0]
        kernel_timestamp = gold_info[1]

        nic_type = self.mtp_get_nic_type(slot)
        expected_timestamp = image_control.get_goldfw(self, nic_type, FF_Stage.FF_SWI)["timestamp"]

        if ( boot_image != "goldfw" ):
            self.cli_log_slot_err_lock(slot, "Checking Boot Image is GoldFW Failed, NIC is booted from {:s}".format(boot_image))
            return False

        if ( expected_timestamp != kernel_timestamp ):
            self.cli_log_slot_err_lock(slot, "goldfw Verify Failed, Expect: {:s}   Read: {:s}".format(expected_timestamp, kernel_timestamp))
            return False

        self.cli_log_slot_inf(slot, "NIC boot from {:s}({:s})".format(boot_image, kernel_timestamp))
        return True


    def mtp_mgmt_verify_nic_sw_boot(self, slot):
        if not self.mtp_nic_boot_info_init(slot):
            self.cli_log_slot_err(slot, "Init NIC sw boot info failed")
            return False

        sw_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not sw_info:
            self.cli_log_slot_err(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = sw_info[0]
        kernel_timestamp = sw_info[1]
        if boot_image not in ["mainfwa", "mainfwb"]:
            self.cli_log_slot_err(slot, "SW boot failed, NIC is booted from {:s}".format(boot_image))
            return False

        self.cli_log_slot_inf(slot, "NIC default boot from {:s}({:s})".format(boot_image, kernel_timestamp))
        return True

    def mtp_nic_sw_mode_switch(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_mode_switch():
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_nic_sw_mode_switch_verify(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_mode_switch_verify():
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_pdsctl_system_show(self, slot):
        if not self._nic_ctrl_list[slot].nic_pdsctl_system_show():
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_nic_sw_profile(self, slot, profile):
        if not self._nic_ctrl_list[slot].nic_sw_profile(profile):
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True


    def mtp_nic_mgmt_reinit(self, slot):
        loop = 0
        while loop < MTP_Const.NIC_MGMT_IP_INIT_RETRY:
            loop += 1
            time.sleep(MTP_Const.NIC_MGMT_IP_SET_DELAY)
            self.cli_log_slot_inf(slot, "Reinit NIC MGMT port <{:d}> try".format(loop))
            if self._nic_ctrl_list[slot].nic_mgmt_config():
                break
            time.sleep(10)
        if loop >= MTP_Const.NIC_MGMT_IP_INIT_RETRY:
            return False

        return True


    def mtp_nic_mgmt_init(self, slot, fpo):
        #self.cli_log_slot_inf(slot, "Init NIC MGMT port")
        dsp = "DIAG_INIT"
        sn = self.mtp_get_nic_sn(slot)
        test = "NIC_MGMT_INIT"
        self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = self.log_slot_test_start(slot, test)

        if not self._nic_ctrl_list[slot].nic_mgmt_init(fpo):
            # retry
            if not self.mtp_nic_mgmt_reinit(slot):
                self.cli_log_slot_err(slot, "Init NIC MGMT port failed")
                duration = self.log_slot_test_stop(slot, test, start_ts)
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                return False

        # delete the arp entry
        ipaddr = libmfg_utils.get_nic_ip_addr(slot)
        cmd = MFG_DIAG_CMDS.MTP_ARP_DELET_FMT.format(ipaddr)
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_slot_err(slot, "Command sudo {:s} failed".format(cmd))
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            return False
        # ping to update the arp cache
        for x in range(2):
            time.sleep(11)
            cmd = MFG_DIAG_CMDS.MTP_NIC_PING_FMT.format(ipaddr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_slot_err(slot, "Command {:s} failed".format(cmd))
                duration = self.log_slot_test_stop(slot, test, start_ts)
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                return False

        cmd_buf = self.mtp_get_cmd_buf()
        match = re.findall(r" 0% packet loss", cmd_buf)
        if not match:
            self.cli_log_slot_err(slot, "Ping MTP to NIC failed")
            self._nic_ctrl_list[slot].nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            return False

        duration = self.log_slot_test_stop(slot, test, start_ts)
        self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        return True


    def mtp_nic_mini_init(self, slot, fpo=False):
        if not self.mtp_nic_mgmt_init(slot, fpo):
            return False        
        sn = self.mtp_get_nic_sn(slot)
        dsp = "DIAG_INIT"
        test = "NIC_BOOT_INIT"  
        self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = self.log_slot_test_start(slot, test)

        if not self.mtp_nic_boot_info_init(slot):
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            return False
        else:
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        return True


    def mtp_mgmt_test_nic_mem(self, slot):
        if not self._nic_ctrl_list[slot].nic_test_mem():
            return False
        else:
            return True

    def mtp_check_nic_jtag(self, slot):
        if not self._nic_ctrl_list[slot].nic_check_jtag(self._asic_support):
            self.mtp_dump_nic_err_msg(slot)
            return False
        else:
            return True

# 2. Routines that need smb bus, can not be run in parallel
    def mtp_mgmt_check_nic_pwr_status(self, slot):
        if not self._nic_ctrl_list[slot].nic_power_check():
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True


    def mtp_mgmt_dump_nic_pll_sta(self, slot):
        reg_data_list = self._nic_ctrl_list[slot].nic_get_pll_sta()
        if not reg_data_list:
            self.cli_log_slot_err(slot, "Failed to extract ASIC PLL status")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return

        reg26_data = reg_data_list[0]
        self.cli_log_slot_inf(slot, "CPLD 0x26 = {:x}".format(reg26_data))
        core_pll_lock = reg26_data & 0x1
        cpu_pll_lock = reg26_data & 0x2
        flash_pll_lock = reg26_data & 0x4
        proto_mode = reg26_data & 0x20
        if not core_pll_lock:
            self.cli_log_slot_err(slot, "ASIC core pll is not locked")
        if not cpu_pll_lock:
            self.cli_log_slot_err(slot, "ASIC cpu pll is not locked")
        if not flash_pll_lock:
            self.cli_log_slot_err(slot, "ASIC flash pll is not locked")
        if proto_mode:
            self.cli_log_slot_err(slot, "ASIC proto mode is set")

        reg28_data = reg_data_list[1]
        self.cli_log_slot_inf(slot, "CPLD 0x28 = {:x}".format(reg28_data))
        pcie_pll_lock = reg28_data & 0x40
        if not pcie_pll_lock:
            self.cli_log_slot_err(slot, "ASIC pcie pll is not locked")
        if not (core_pll_lock or cpu_pll_lock or flash_pll_lock or pcie_pll_lock):
            # print some more debug info
            self.mtp_mgmt_set_nic_avs_post(slot)


# 3. Routines that need spi bus, can not be run in parallel
    def mtp_power_on_single_nic(self, slot, dl=False):
        self.mtp_nic_lock()
        self.cli_log_slot_inf(slot, "Power on NIC, wait {:02d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY))
        if not self._nic_ctrl_list[slot].nic_power_on():
            self.mtp_nic_unlock()
            self.cli_log_slot_err(slot, "Failed to power on NIC")
            return False
        self.mtp_nic_unlock()

        self.mtp_nic_lock()
        if self._nic_type_list[slot] in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4) and not dl:
            if not self._nic_ctrl_list[slot].nic_set_i2c_after_pw_cycle():
                self.mtp_get_nic_err_msg(slot)
            else:
                self.cli_log_slot_inf(slot, "I2C value setting complete")
        self.mtp_nic_unlock() 

        return True


    def mtp_power_off_single_nic(self, slot):
        self.mtp_nic_lock()
        self.cli_log_slot_inf(slot, "Power off NIC, wait {:02d} seconds for NIC power down".format(MTP_Const.NIC_POWER_OFF_DELAY))
        if not self._nic_ctrl_list[slot].nic_power_off():
            self.mtp_nic_unlock()
            self.cli_log_slot_err(slot, "Failed to power off NIC")
            return False
        self.mtp_nic_unlock()
        return True


# 4. Routines use mgmt port, can be run in parallel
    def mtp_mgmt_exec_cmd_para(self, slot, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        rc = self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout)
        if not rc:
            self.mtp_dump_nic_err_msg(slot)
        return rc


    def mtp_get_nic_cmd_buf(self, slot):
        return self._nic_ctrl_list[slot].nic_get_cmd_buf()

    def mtp_exec_nic_cmd_get_info(self, slot, cmd, timeout=None):
        return self._nic_ctrl_list[slot].nic_get_info(cmd, timeout)

    def mtp_exec_nic_cmds_get_lastcmd_info(self, slot, cmds, timeout=None):
        rc = self._nic_ctrl_list[slot].nic_exec_cmds(cmds, timeout)
        if not rc:
            return False
        if self._nic_ctrl_list[slot].nic_get_cmd_buf():
            return self._nic_ctrl_list[slot].nic_get_cmd_buf()
        return True

    def mtp_get_nic_err_msg(self, slot):
        err_msg_str = self._nic_ctrl_list[slot].nic_get_err_msg()
        if err_msg_str:
            err_msg_list = err_msg_str.splitlines()
            for err_msg in err_msg_list:
                if err_msg:
                    self.cli_log_slot_err(slot, err_msg)
        return

    def mtp_clear_nic_err_msg(self, slot):
        return self._nic_ctrl_list[slot].nic_get_err_msg()

    def mtp_nic_fst_exec_cmd(self, slot, cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
        if not self._nic_ctrl_list[slot].nic_fst_exec_cmd(cmd, timeout):
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_program_nic_fru(self, slot, date, sn, mac, pn):
        nic_type = self.mtp_get_nic_type(slot)
        self.cli_log_slot_inf_lock(slot, "Program NIC FRU date={:s}, sn={:s}, mac={:s}, pn={:s}".format(date, sn, mac, pn))
        if not self._nic_ctrl_list[slot].nic_write_fru(date, sn, mac, pn, nic_type, smb_fru=False):
            self.cli_log_slot_err_lock(slot, "Program ASIC NIC FRU failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        if self._nic_ctrl_list[slot].nic_2nd_fru_exist(pn):
            if not self._nic_ctrl_list[slot].nic_write_fru(date, sn, mac, pn, nic_type, smb_fru=True):
                self.cli_log_slot_err_lock(slot, "Program SMB NIC FRU failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_read_fru(smb_fru=True):
                self.cli_log_slot_err_lock(slot, "Display SMB NIC FRU failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
        if not self._nic_ctrl_list[slot].nic_read_fru():
            self.cli_log_slot_err_lock(slot, "Display NIC FRU failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_program_nic_alom_fru(self, slot, date, alom_sn, alom_pn):
        self.cli_log_slot_inf_lock(slot, "Program NIC ALOM FRU date={:s}, alom_sn={:s}, alom_pn={:s}".format(date, alom_sn, alom_pn))
        if not self._nic_ctrl_list[slot].nic_program_alom_fru(date, alom_sn, alom_pn):
            self.cli_log_slot_err_lock(slot, "Program NIC ALOM FRU failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_dump_nic_fru(self, slot, expect_sn="", expect_mac="", expect_pn=""):
        if not self._nic_ctrl_list[slot].nic_dump_fru(expect_mac=expect_mac):
            self.cli_log_slot_err_lock(slot, "Dump ASIC FRU failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        if not self._nic_ctrl_list[slot].mtp_nic_dump_fru(expect_mac=expect_mac):
            self.cli_log_slot_err_lock(slot, "Dump SMB FRU failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_get_nic_fru(self, slot):
        return self._nic_ctrl_list[slot].nic_get_fru()

    def mtp_get_nic_alom_fru(self, slot):
        return self._nic_ctrl_list[slot].nic_alom_get_fru()
        
    def mtp_get_nic_alom_sn(self, slot):
        return self._nic_ctrl_list[slot].nic_alom_sn_get_fru()

    def mtp_verify_nic_fru(self, slot, sn, mac, pn, date):
        nic_fru_info = self._nic_ctrl_list[slot].nic_get_fru()
        if not nic_fru_info:
            self.cli_log_slot_err_lock(slot, "Verify NIC FRU Failed, can not retrieve FRU content")
            return False

        nic_sn = nic_fru_info[0]
        nic_mac = nic_fru_info[1]
        nic_pn = nic_fru_info[2]
        nic_date = nic_fru_info[3]
        nic_type = self.mtp_get_nic_type(slot)
        if nic_sn != sn:
            self.cli_log_slot_err_lock(slot, "SN Verify Failed, get {:s}, expect {:s}".format(nic_sn, sn))
            return False
        if nic_mac != mac:
            self.cli_log_slot_err_lock(slot, "MAC Verify Failed, get {:s}, expect {:s}".format(nic_mac, mac))
            return False
        if nic_pn != pn:
            self.cli_log_slot_err_lock(slot, "PN Verify Failed, get {:s}, expect {:s}".format(nic_pn, pn))
            return False
        if nic_date != date:
            self.cli_log_slot_err_lock(slot, "Date Verify Failed, get {:s}, expect {:s}".format(nic_date, date))
            return False
        self.cli_log_slot_inf_lock(slot, "Verify NIC FRU Pass, sn={:s}, mac={:s}, pn={:s}, date={:s}".format(sn, mac, pn, date))

        return True

    def mtp_verify_hpe_pn_fru(self, slot, hpe_pn):
        got_pn = self._nic_ctrl_list[slot]._prod_num
        if not got_pn:
            return False

        if got_pn != hpe_pn:
            self.cli_log_slot_err_lock(slot, "Read HPE PN: {:s}, expect {:s}".format(got_pn, hpe_pn))
            return False

        self.cli_log_slot_inf_lock(slot, "Verify HPE PN FRU Pass, PN={:s}".format(hpe_pn))

        return True
        
    def mtp_verify_nic_alom_fru(self, slot, alom_sn, alom_pn, date):
        alom_fru_info = self.mtp_get_nic_alom_fru(slot)
        got_alom_sn = alom_fru_info[0]
        got_alom_pn = alom_fru_info[1]
        got_alom_date = alom_fru_info[2]
    
        if got_alom_sn != alom_sn:
            self.cli_log_slot_err_lock(slot, "ALOM SN Verify Failed, got {:s}, expecting {:s}".format(got_alom_sn, alom_sn))
            return False
        if got_alom_pn != alom_pn:
            self.cli_log_slot_err_lock(slot, "ALOM PN Verify Failed, got {:s}, expecting {:s}".format(got_alom_pn, alom_pn))
            return False
        if got_alom_date != alom_date:
            self.cli_log_slot_err_lock(slot, "ALOM Date Verify Failed, got {:s}, expecting {:s}".format(got_alom_date, alom_date))
            return False

        self.cli_log_slot_inf_lock(slot, "Verify NIC ALOM FRU Pass, sn={:s}, pn={:s}, date={:s}".format(alom_sn, alom_pn, date))
        return True

    def mtp_verify_nic_assettag(self, slot, exp_assettag):
    
        assettag = self._nic_ctrl_list[slot].nic_get_assettag()
        if not assettag:
            self.cli_log_slot_err_lock(slot, "Verify NIC assettag Failed, can not retrieve assettag content")
            return False

        if assettag != exp_assettag:
            self.cli_log_slot_err_lock(slot, "assettag Verify Failed, get {:s}, expect {:s}".format(assettag, exp_assettag))
        self.cli_log_slot_inf_lock(slot, "Verify NIC assettag FRU Pass, assettag={:s}".format(assettag))
        return True


    def mtp_nic_hpe_rework_verify(self, slot):
        """ REWORK VERIFICATION FOR CAP CHANGE 
            For NAPLES25(HPE) and NAPLES25SWM(HPE), Product Version/Revision Code must be 0B or 0x30 0x42
            With WDC flash/new heatsink/new FRU table, Product Version must be 0C
        """
        if not self._nic_ctrl_list[slot].nic_fru_init_hpe_version():
            self.mtp_get_nic_err_msg(slot)
            return False

        got_prod_ver = self._nic_ctrl_list[slot].nic_get_hpe_version()
        if not got_prod_ver:
            self.cli_log_slot_err(slot, "Failed to parse Product Version/Revision Code")
            return False

        if self._nic_ctrl_list[slot]._pn_format == PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT:
            exp_prod_ver = "0B"
        else:
            exp_prod_ver = "0C"

        if got_prod_ver != exp_prod_ver:
            self.cli_log_slot_err(slot, "Looking for Product Version/Revision Code = {:s}, got {}".format(exp_prod_ver, got_prod_ver))
            return False

        return True

    def mtp_nic_program_ocp_adapter_fru(self, slot, date, sn, mac, pn):
        """
        sn  = scanned
        mac = FF:FF:FF:FF:FF (fixed)
        pn  = 73-0024-03 (fixed)
        date= generated
        """

        nic_type = self.mtp_get_nic_type(slot)

        if nic_type != NIC_Type.NAPLES25OCP:
            self.cli_log_err("This function cannot be used without an OCP card plugged in")
            return False

        self.cli_log_slot_inf_lock(slot, "Program OCP Adapter FRU date={:s}, sn={:s}, mac={:s}, pn={:s}".format(date, sn, mac, pn))
        if not self._nic_ctrl_list[slot].nic_program_ocp_adapter_fru(date, sn, mac, pn):
            self.cli_log_slot_err_lock(slot, "Program OCP Adapter FRU failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_nic_verify_ocp_adapter_fru(self, slot, exp_date, exp_sn, exp_mac, exp_pn):
        """ check programmed sn and date only. MAC and PN have no validation rules. """
        sn = self.mtp_get_nic_ocp_adapter_sn(slot)
        date = self.mtp_get_nic_ocp_adapter_progdate(slot)
        mac = exp_mac
        pn = exp_pn

        if sn != exp_sn:
            self.cli_log_slot_err_lock(slot, "SN Verify Failed, get {:s}, expect {:s}".format(sn, exp_sn))
            return False
        if date != exp_date:
            self.cli_log_slot_err_lock(slot, "Date Verify Failed, get {:s}, expect {:s}".format(date, exp_date))
            return False
        self.cli_log_slot_inf_lock(slot, "Verify NIC FRU Pass, sn={:s}, mac={:s}, pn={:s}, date={:s}".format(sn, mac, pn, date))

        return True

    #Check the SWI scanned in software part number to see if it's a cloud image or not.
    #Cloud images have slight deviation on how SWI runs
    def check_is_cloud_software_image(self, slot, software_pn):
        print(" Check if software image is cloud: {:s}".format(software_pn))            
        if (software_pn == "90-0004-0001" or
            software_pn == "90-0006-0001" or
            software_pn == "90-0006-0002" or
            software_pn == "90-0011-0003" or
            software_pn == "90-0012-0001" or
            software_pn == "90-0019-0001"
            ):
            return True
        return False
            
    #Check if the loaded image correct for the cards p/n.  i.e. cloud card gets a cloud image, 
    #and etnerprise card get an enterprise image
    def check_swi_software_image(self, slot, software_pn, pn_check=True):
        naples_pn = self._nic_ctrl_list[slot].nic_get_naples_pn()
        if not naples_pn:
            self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Retreive PN Failed")
            return False
        if naples_pn[0:7] == "68-0003":        #NAPLES 100 PENSANDO
            if software_pn != "90-0001-0003":
                return False
        elif naples_pn[0:9] == "111-05363": #NAPLES 100 NETAPP
            if software_pn != "90-0001-0002":
                return False
        elif naples_pn[0:7] == "68-0013":   #NAPLES100 IBM
            if software_pn != "90-0004-0001":
                return False
        elif naples_pn[0:6] == "P37692":    #NAPLES100 HPE 
            if software_pn != "90-0002-0009":
                return False    
        elif naples_pn[0:6] == "P41854":    #NAPLES100 HPE CLOUD
            if software_pn != "90-0006-0002":
                return False
        elif naples_pn[0:7] == "68-0024":    #NAPLES100 DELL 
            if software_pn != "90-0013-0001":
                return False
        elif naples_pn[0:7] == "68-0005":    #NAPLES25 PENSANDO
            if software_pn != "90-0002-0003":
                return False 
        elif naples_pn[0:6] == "P18669":     #NAPLES25 HPE
            if software_pn != "90-0006-0001":
                return False 
        elif naples_pn[0:7] == "68-0008":    #NAPLES25 EQUINIX
            if software_pn != "90-0006-0001":
                return False 
        elif naples_pn[0:6] == "P26968":     #NAPLES25 SWM HPE
            if software_pn != "90-0002-0011":
                return False 
        elif naples_pn[0:6] == "P41851":     #NAPLES25 SWM HPE CLOUD
            if software_pn != "90-0006-0002":
                return False
        elif naples_pn[0:6] == "P46653":    # NAPLES25 SWM HPE TAA
            if software_pn != "90-0014-0001":
                return False
        elif (naples_pn[0:7] == "68-0016") or (naples_pn[0:7] == "68-0017"):    #NAPLES25 SWM PENSANDO & TAA
            if software_pn != "90-0002-0005":
                return False
        elif naples_pn[0:7] == "68-0014":     #NAPLES25 SWM DELL
            if software_pn != "90-0007-0004":
                return False
        elif naples_pn[0:7] == "68-0019":     #NAPLES25 SWM 833
            if software_pn != "90-0002-0007":
                return False
        elif naples_pn[0:7] == "68-0023":     #NAPLES25 OCP PENSANDO
            if software_pn != "90-0002-0007":
                return False
        elif naples_pn[0:6] == "P37689":      #NAPLES25 OCP HPE
            if software_pn != "90-0002-0011":
                return False
        elif naples_pn[0:6] == "P41857":      #NAPLES25 OCP HPE CLOUD
            if software_pn != "90-0006-0002":
                return False
        elif naples_pn[0:7] == "68-0010":     #NAPLES25 OCP DELL
            if software_pn != "90-0007-0004":
                return False
        elif ((naples_pn[0:7] == "68-0007") or (naples_pn[0:7] == "68-0009") or (naples_pn[0:7] == "68-0011")):      #FORIO/VOMERO/VOMERO2
            if software_pn != "90-0003-0001":
                return False
        elif naples_pn[0:7] == "68-0015":     #ORTANO
            if software_pn != "90-0021-0001":
                return False
            if pn_check and not naples_pn.endswith("C1"):
                self.cli_log_slot_err_lock(slot, "Check PN REV: Software Image match to nic part number failed")
                self.cli_log_slot_err_lock(slot, "Expected: {:s}, Got: {:s}".format(naples_pn[:PEN_PN_MINUS_REV_MASK]+" C1", naples_pn))
                return False
        elif naples_pn[0:7] == "68-0021":     #ORTANO PENSANDO
            if software_pn != "90-0019-0001":
                return False
        elif naples_pn[0:6] == "0PCFPC":      #POMONTE DELL
            if software_pn != "90-0017-0003":
                return False
        elif naples_pn[0:6] in ("0X322F","0W5WGK"):      #LACONA32 DELL
            if software_pn != "90-0017-0003":
                return False
        elif naples_pn[0:6] == "P47930":      #LACONA32 HPE
            if software_pn != "90-0017-0003":
                return False
        elif naples_pn[0:7] == "68-0026":     #ORTANO2 ADI ORACLE
            if software_pn != "90-0021-0001":
                return False
        elif naples_pn[0:7] == "68-0028":     #ORTANO2 ADI IBM
            if software_pn != "90-0016-0004":
                return False
        elif naples_pn[0:7] == "68-0034":     #ORTANO2 ADI MICROSOFT
            if software_pn != "90-0019-0001":
                return False
        elif naples_pn[0:7] == "68-0029":     #ORTANO2 INTERPOSER
            if software_pn != "90-0021-0001":
                return False
        elif naples_pn[0:7] == "68-0077":     #ORTANO2 SOLO
            if software_pn != "90-0021-0001":
                return False
        elif naples_pn[0:7] == "68-0089":     #ORTANO2 SOLO Tall Heat Sink
            if software_pn != "90-0021-0001":
                return False
        elif naples_pn[0:7] == "68-0090":     #ORTANO2 SOLO MICROSOFT
            if software_pn != "90-0020-0003":
                return False
        elif naples_pn[0:7] == "68-0092":     #ORTANO2 (ADI CR/ SOLO) S4
            if software_pn != "90-0022-0001":
                return False
        elif naples_pn[0:7] == "68-0049":     #ORTANO2 ADI CR
            if software_pn != "90-0021-0001":
                return False
        elif naples_pn[0:7] == "68-0091":     #ORTANO2 ADI CR MICROSOFT
            if software_pn != "90-0020-0003":
                return False
        elif naples_pn[0:7] == "68-0074":     #GINESTRA_D4
            if software_pn != "90-0023-0001":
                return False
        elif naples_pn[0:7] == "68-0075":     #GINESTRA_D5
            if software_pn != "90-0023-0002":
                return False
        else:
            self.cli_log_slot_err_lock(slot, "check_swi_software_image Unknown Part Number {:s} !!".format(naples_pn))
            return False

        self.cli_log_slot_inf_lock(slot, "==> SOFTWARE IMAGE PN {:s}    CARD PN {:s} ".format(software_pn, naples_pn))
        return True

    def mtp_nic_sw_pn_search(self, slot, sw_pn_list, check_naples_pn):
        """ for each slot, match it to one of the SW PNs; fail slot if no match """
        for sw_pn in sw_pn_list:
            if not self.check_swi_software_image(slot, sw_pn, check_naples_pn):
                continue
            else:
                self.mtp_set_nic_sw_pn(slot, sw_pn)
                break
        # search exhausted
        if not self.mtp_get_nic_sw_pn(slot):
            self.cli_log_slot_err(slot, "No correct SW PN supplied")
            return False
        else:
            return True

    def mtp_get_alom_fru(self, slot):
        return self._nic_ctrl_list[slot].alom_get_fru()

    def mtp_setting_partition(self, slot):
        # copy script to detect the emmc part size
        if not self._nic_ctrl_list[slot].nic_copy_image("{:s}diag/scripts/emmc_format.sh".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)):
            self.cli_log_slot_err_lock(slot, "Failed to copy emmc format script")
            return False
        # Run command twice: first time does it, 2nd time says 'already partitioned'
        if not self._nic_ctrl_list[slot].nic_setting_partition():
            self.cli_log_slot_err_lock(slot, "Could not complete partition command")
            return False
        if not self._nic_ctrl_list[slot].nic_setting_partition(): 
            self.cli_log_slot_err_lock(slot, "Partition table was not updated")
            return False
        self.cli_log_slot_inf_lock(slot, "Partition table updated")
        return True

    def mtp_nic_partition_check(self, slot):
        if not self._nic_ctrl_list[slot].nic_verify_partition():
            self.cli_log_slot_err_lock(slot, "PSLC Verify failed")
            return False
        self.cli_log_slot_inf_lock(slot, "Verify PSCL Pass")
        return True

    def mtp_nic_emmc_bkops_en(self, slot):
        # copy script to detect the emmc part size
        if not self._nic_ctrl_list[slot].nic_copy_image("{:s}nic_util/mmc.latest".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH)):
            self.cli_log_slot_err_lock(slot, "Failed to copy emmc util")
            return False
        if not self._nic_ctrl_list[slot].nic_emmc_bkops_verify():
            self.mtp_clear_nic_err_msg(slot) # clear out the error message
            if not self._nic_ctrl_list[slot].nic_emmc_bkops_en(): 
                self.cli_log_slot_err_lock(slot, "Failed to enable eMMC bkops")
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_emmc_bkops_verify():
                self.cli_log_slot_err_lock(slot, "Incorrect eMMC bkops value reflected")
                self.mtp_get_nic_err_msg(slot)
                return False
        return True

    def mtp_nic_emmc_hwreset_set(self, slot):
        if not self._nic_ctrl_list[slot].nic_emmc_hwreset_verify():
            self.mtp_clear_nic_err_msg(slot) # clear out the error message
            if not self._nic_ctrl_list[slot].nic_emmc_hwreset_set(): 
                self.cli_log_slot_err_lock(slot, "Failed to enable eMMC hwreset setting")
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_emmc_hwreset_verify():
                self.cli_log_slot_err_lock(slot, "Incorrect eMMC hwreset setting reflected")
                self.mtp_get_nic_err_msg(slot)
                return False
        return True

    def mtp_set_nic_diagfw_boot(self, slot):
        if not self._nic_ctrl_list[slot].set_nic_diagfw_boot():
            self.cli_log_slot_err(slot, "Set boot diagfw failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set boot diagfw")
        return True

    def mtp_program_nic_adi_ibm_cpld(self, slot, cpld_img, dl_step=True):
        # check the current cpld version
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type != NIC_Type.ORTANO2ADIIBM:
            self.cli_log_slot_err(slot, "This cpld update function not meant for this card {:s}".format(nic_type))
            return False

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "cfg0"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_adi_ibm_failsafe_cpld(self, slot, cpld_img):
        # check the current cpld version
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type != NIC_Type.ORTANO2ADIIBM:
            self.cli_log_slot_err(slot, "This failsafe cpld update function not meant for this card {:s}".format(nic_type))
            return False

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "cfg1"):
            self.cli_log_slot_err_lock(slot, "Program NIC Failsafe CPLD failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_cpld(self, slot, cpld_img, dl_step=True):
        # check the current cpld version
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type in FPGA_TYPE_LIST:
            self.cli_log_slot_err(slot, "This cpld update function not meant for this card {:s}".format(nic_type))
            return False

        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed, can not retrieve CPLD info")
            return False
        cur_ver = nic_cpld_info[0]
        cur_timestamp = nic_cpld_info[1]

        if dl_step:
            stage = FF_Stage.FF_DL
        else:
            stage = FF_Stage.FF_SWI
        expected_version   = image_control.get_cpld(self, nic_type, stage)["version"]
        expected_timestamp = image_control.get_cpld(self, nic_type, stage)["timestamp"]

        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip CPLD update for Proto NIC")
            return True

        if cur_ver == expected_version and cur_timestamp == expected_timestamp:
            self.cli_log_slot_inf_lock(slot, "NIC CPLD is up-to-date")
            self._nic_ctrl_list[slot].nic_require_cpld_refresh(False)
            return True

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "cfg0"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        self._nic_ctrl_list[slot].nic_require_cpld_refresh(True)

        return True

    def mtp_program_nic_failsafe_cpld(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no failsafe CPLD for {:s}".format(nic_type))
            return False
        if nic_type in FPGA_TYPE_LIST:
            self.cli_log_slot_err(slot, "This function not support for this NIC type!")
            return False
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip failsafe CPLD update for Proto NIC")
            return True

        if nic_type in ELBA_NIC_TYPE_LIST and nic_type not in (FPGA_TYPE_LIST + [NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4]):
            # can't check the version without loading backup partition into the running partition
            self.cli_log_slot_inf(slot, "Skip checking failsafe CPLD version")

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "cfg1"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_fpga(self, slot, partition_list=None, alternate_image_list=None):
        """
        This sequence has to be followed:
        # cpldapp -writeflash ./lac2_dell_golden_2_3.bin cfg1
        # cpldapp -writeflash ./timer1.bin cfg2
        # cpldapp -writeflash ./lac2_dell_main_2_3.bin
        # cpldapp -writeflash ./timer2.bin cfg3

        or (in FW older than E-24)

        ./artix7fpga -prog ${part_number}_gold.bin gold
        ./artix7fpga -prog timer1.bin timer1
        ./artix7fpga -prog ${part_number}_main.bin main
        ./artix7fpga -prog timer2.bin timer2
        """
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type not in FPGA_TYPE_LIST:
            self.cli_log_slot_err(slot, "This fpga program function not supported for this NIC type!")
            return False

        #### Dont skip programming the image right now
        # # check the current cpld version
        # nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        # if not nic_cpld_info:
        #     self.cli_log_slot_err_lock(slot, "Program NIC FPGA failed, can not retrieve FPGA revision info")
        #     return False
        # cur_ver = nic_cpld_info[0]
        # cur_timestamp = nic_cpld_info[1]
        # expected_version   = image_control.get_cpld(self, nic_type, stage)["version"]
        # expected_timestamp = image_control.get_cpld(self, nic_type, stage)["timestamp"]

        # if nic_type in self._proto_type_list:
        #     self.cli_log_slot_inf_lock(slot, "Skip CPLD update for Proto NIC")
        #     return True

        # if cur_ver == expected_version and cur_timestamp == expected_timestamp:
        #     self.cli_log_slot_inf_lock(slot, "NIC FPGA is up-to-date")
        #     self._nic_ctrl_list[slot].nic_require_cpld_refresh(False)
        #     return True

        partition_img_dict = {
            "cfg0": image_control.get_cpld(self, nic_type, FF_Stage.FF_DL)["filename"],
            "cfg1": image_control.get_fail_cpld(self, nic_type, FF_Stage.FF_DL)["filename"],
            "cfg2": image_control.get_timer1(self, nic_type, FF_Stage.FF_DL)["filename"],
            "cfg3": image_control.get_timer2(self, nic_type, FF_Stage.FF_DL)["filename"]
        }
        program_sequence = ["cfg1", "cfg2", "cfg0", "cfg3"]
        
        if partition_list is not None:
            program_sequence = partition_list
            if alternate_image_list is not None:
                for prt, img in zip(partition_list, alternate_image_list):
                    partition_img_dict[prt] = img

        for partition in program_sequence:
            img = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + partition_img_dict[partition]
            if not self._nic_ctrl_list[slot].nic_program_cpld(img, partition):
                self.cli_log_slot_err_lock(slot, "Program NIC FPGA to partition {:s} failed".format(partition))
                self.mtp_dump_nic_err_msg(slot)
                return False

        self._nic_ctrl_list[slot].nic_require_cpld_refresh(True)

        return True

    def mtp_verify_nic_fpga(self, slot, main_only=False):
        """
        Following the same partition sequence as writing:
        # cpldapp -verifyflash ./lac2_dell_golden_2_3.bin cfg1
        # cpldapp -verifyflash ./timer1.bin cfg2
        # cpldapp -verifyflash ./lac2_dell_main_2_3.bin
        # cpldapp -verifyflash ./timer2.bin cfg3
        """
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type not in FPGA_TYPE_LIST:
            self.cli_log_slot_err(slot, "This fpga verify function not support for this NIC type!")
            return False

        partition_img_dict = {
            "cfg0": image_control.get_cpld(self, nic_type, FF_Stage.FF_DL)["filename"],
            "cfg1": image_control.get_fail_cpld(self, nic_type, FF_Stage.FF_DL)["filename"],
            "cfg2": image_control.get_timer1(self, nic_type, FF_Stage.FF_DL)["filename"],
            "cfg3": image_control.get_timer2(self, nic_type, FF_Stage.FF_DL)["filename"]
        }
        if not main_only:
            program_sequence = ["cfg1", "cfg2", "cfg0", "cfg3"]
        else:
            program_sequence = ["cfg0"]
        for partition in program_sequence:
            img = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + partition_img_dict[partition]
            if not self._nic_ctrl_list[slot].nic_verify_fpga(img, partition):
                self.cli_log_slot_err_lock(slot, "Verify NIC FPGA from partition {:s} failed".format(partition))
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False

        return True

    def mtp_program_nic_cpld_feature_row(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no feature row for {:s}".format(nic_type))
            return False
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "No feature row update for Proto NIC")
            return True

        cpld_img = "/home/diag/"+image_control.get_fea_cpld(self, nic_type, FF_Stage.FF_DL)["filename"]

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "fea"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD feature row failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_refresh_nic_cpld(self, slot, dontwait=False):
        if not self._nic_ctrl_list[slot].nic_is_cpld_refresh_required():
            self.cli_log_slot_inf_lock(slot, "No CPLD refresh needed")
            return True

        if not self._nic_ctrl_list[slot].nic_refresh_cpld(dontwait):
            self.cli_log_slot_err_lock(slot, "Refresh NIC CPLD failed")
            return False

        return True

    def mtp_program_nic_sec_cpld(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in self._valid_type_list:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
            return False

        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Secure CPLD program for Proto NIC")
            return True

        self._nic_ctrl_list[slot].nic_require_cpld_refresh(True)
        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img):
            self.cli_log_slot_err_lock(slot, "Program NIC Secure CPLD failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True


    def mtp_verify_nic_sec_cpld(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Secure CPLD verify for Proto NIC")
            return True

        if nic_type not in CAPRI_NIC_TYPE_LIST:
            if not self._nic_ctrl_list[slot].nic_dump_esec_qspi(libmfg_utils.get_mode_param(self, slot, "SEC_PROG_VERIFY")):
                self.cli_log_slot_err(slot, "Dumping esec failed")
                return False

        if not self._nic_ctrl_list[slot].nic_verify_sec_cpld():
            self.cli_log_slot_err(slot, "Verify NIC Secure CPLD failed")
            return False

        return True

    def mtp_verify_nic_cpld_fea(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no feature row for {:s}".format(nic_type))
            return False

        fea_regex = r"00000000  (.*)  \|.*\|" #first 16 bytes

        cmd = "hexdump -C /home/diag/"+image_control.get_fea_cpld(self, nic_type, FF_Stage.FF_DL)["filename"]
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False
        fea_mtp_hex = self.mtp_get_cmd_buf()
        fea_mtp_match = re.search(fea_regex, fea_mtp_hex)

        if not self._nic_ctrl_list[slot].nic_dump_cpld("fea"):
            self.mtp_dump_nic_err_msg(slot)
            return False
        
        fea_nic_hex = self._nic_ctrl_list[slot].nic_get_info("hexdump -C /home/diag/cplddump")
        if not fea_nic_hex:
            self.mtp_dump_nic_err_msg(slot)
            return False
        fea_nic_match = re.search(fea_regex,fea_nic_hex)

        if fea_mtp_match and fea_nic_match:
            if fea_mtp_match.group(1) == fea_nic_match.group(1):
                return True
            self.cli_log_slot_err_lock(slot, "Feature row programmed incorrectly. Dump doesn't match original file.")
            return False
        self.cli_log_slot_err_lock(slot, "Unable to dump feature row.")
        return False

    def mtp_check_nic_cpld_partition(self, slot, console=False):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
            # No cpld partition bit
            return True

        self.cli_log_slot_inf(slot, "Check CPLD partition")
        if not self._nic_ctrl_list[slot].nic_check_cpld_partition(console):
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_recover_nic_console(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
            self.cli_log_slot_err(slot, "Not applicable for this NIC")
            return False

        self.cli_log_slot_inf(slot, "Recover NIC console")
        if not self._nic_ctrl_list[slot].nic_recover_console():
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_efuse(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
            return False

        if not self._nic_ctrl_list[slot].nic_program_efuse():
            self.cli_log_slot_err(slot, "Program NIC Efuse failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_sec_key(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Secure Key program for Proto NIC")
            return True

        if not self._nic_ctrl_list[slot].nic_program_sec_key_pre():
            self.cli_log_slot_err(slot, "Pre init key programming failed")
            self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        if not self._nic_ctrl_list[slot].nic_program_sec_key(self._id):
            self.cli_log_slot_err(slot, "Program NIC Secure Key failed")
            self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        if not self._nic_ctrl_list[slot].nic_program_sec_key_post():
            self.cli_log_slot_err(slot, "Post cleanup key programming failed")
            self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        return True

    def mtp_verify_nic_cpld(self, slot, sec_cpld=False, timestamp_check=True, dl_step=True, console=False):
        # cpld_has_timestamp = 1
        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Verify NIC CPLD failed, can not retrieve CPLD info")
            return False

        cur_ver = nic_cpld_info[0]
        cur_timestamp = nic_cpld_info[1]
        nic_type = self.mtp_get_nic_type(slot)

        if dl_step:
            stage = FF_Stage.FF_DL
        else:
            stage = FF_Stage.FF_SWI
        expected_version   = image_control.get_cpld(self, nic_type, stage)["version"]
        expected_timestamp = image_control.get_cpld(self, nic_type, stage)["timestamp"]
        if sec_cpld:
            expected_version   = image_control.get_sec_cpld(self, nic_type, stage)["version"]
            expected_timestamp = image_control.get_sec_cpld(self, nic_type, stage)["timestamp"]

        if cur_ver != expected_version or (timestamp_check and cur_timestamp != expected_timestamp):
                self.cli_log_slot_err_lock(slot, "Verify NIC CPLD Failed")
                self.cli_log_slot_err_lock(slot, "Expect Version: {:s}, get: {:s}".format(expected_version, cur_ver))
                self.cli_log_slot_err_lock(slot, "Expect Timestamp: {:s}, get: {:s}".format(expected_timestamp, cur_timestamp))
                return False

        if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            if not self._nic_ctrl_list[slot].nic_check_cpld_partition(console):
                self.cli_log_slot_err(slot, "NIC not booted from cfg0 CPLD/FPGA")
                self.mtp_dump_nic_err_msg(slot)
                return False

        return True

    def mtp_program_nic_qspi(self, slot, qspi_img, force_update=True):
        if not force_update:
            # check for the desired qspi version
            if not self.mtp_verify_nic_qspi(slot):
                pass
            else:
                self.cli_log_slot_inf_lock(slot, "NIC QSPI is up-to-date")
                return True
        if not self._nic_ctrl_list[slot].nic_program_qspi(qspi_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC QSPI failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_copy_nic_cert(self, slot, cert_img, directory="/data/"):
        if not self._nic_ctrl_list[slot].nic_copy_cert(cert_img, directory):
            self.cli_log_slot_inf_lock(slot, "Copy NIC cert failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
            
        return True
        
    def mtp_copy_nic_gold(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_copy_gold(gold_img):
            self.cli_log_slot_inf_lock(slot, "Copy NIC goldfw failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
            
        return True

    def mtp_compare_nic_cpld_img(self, slot, cpld_img, partition):
        if not self._nic_ctrl_list[slot].nic_copy_cpld_img(cpld_img):
            self.cli_log_slot_inf_lock(slot, "Copy NIC cpld image failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        dump_cpld_image_path = "/tmp_{:s}_cpld_image.bin".format(partition)
        if not self._nic_ctrl_list[slot].nic_dump_cpld(partition, file_path=dump_cpld_image_path):
            self.cli_log_slot_inf_lock(slot, "Dump NIC cpld image failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        if not self._nic_ctrl_list[slot].nic_compare_cpld_file(cpld_img, dump_cpld_image_path, partition):
            self.cli_log_slot_inf_lock(slot, "Compare NIC cpld image failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_gold(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_program_gold(gold_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC goldfw failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        if not self.mtp_mgmt_set_nic_gold_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True

    def mtp_program_nic_uboot(self, slot, uboot_img=MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"boot0.rev7.img", installer=MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"install_file", uboot_pat="boot0", ubootg_img=""):
        if not self._nic_ctrl_list[slot].nic_program_uboot(uboot_img, installer, uboot_pat, ubootg_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC uboot failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True


    def mtp_verify_nic_qspi(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        qspi_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not qspi_info:
            self.cli_log_slot_err_lock(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = qspi_info[0]
        kernel_timestamp = qspi_info[1]
        nic_type = self.mtp_get_nic_type(slot)
        expected_timestamp = image_control.get_diagfw(self, nic_type, FF_Stage.FF_DL)["timestamp"]

        if ( boot_image != "diagfw" ):
            self.cli_log_slot_err_lock(slot, "Checking Boot Image is Diagfw Failed, NIC is booted from {:s}".format(boot_image))
            return False

        if ( expected_timestamp != kernel_timestamp ):
            self.cli_log_slot_err_lock(slot, "Diagfw Verify Failed, Expect: {:s}   Read: {:s}".format(expected_timestamp, kernel_timestamp))
            return False

        # additional: check has correct uboot
        if nic_type in (NIC_Type.ORTANO2) or nic_type in FPGA_TYPE_LIST:
            self.mtp_nic_console_lock()
            if not self._nic_ctrl_list[slot].nic_console_read_uboot():
                self.mtp_nic_console_unlock()
                self.mtp_get_nic_err_msg(slot)
                self.cli_log_slot_inf(slot, "Uboot update needed")
                if not GLB_CFG_MFG_TEST_MODE:
                    self.cli_log_slot_err(slot, self.mtp_dump_nic_err_msg(slot))
                return False
            self.mtp_nic_console_unlock()
            self.cli_log_slot_inf(slot, "Uboot is OK - no update needed")

        return True

    def mtp_nic_read_secure_boot_keys(self, slot):
        if not self._nic_ctrl_list[slot].nic_console_read_secure_boot_keys():
            self.mtp_get_nic_err_msg(slot)
            if not GLB_CFG_MFG_TEST_MODE:
                self.cli_log_slot_err(slot, self.mtp_dump_nic_err_msg(slot))
            return False
        self.cli_log_slot_inf(slot, "Uboot is OK - no update needed")
        return True

    def mtp_copy_nic_emmc(self, slot, emmc_img):
        if not self._nic_ctrl_list[slot].nic_copy_emmc(emmc_img):
            self.cli_log_slot_err_lock(slot, "Program NIC EMMC failed")
            return False
            
        return True
        
    def mtp_set_nic_sw_boot(self, slot, emmc_img):

        if not self.mtp_mgmt_set_nic_sw_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True

    def mtp_program_nic_emmc(self, slot, emmc_img):
        if not self._nic_ctrl_list[slot].nic_program_emmc(emmc_img):
            self.cli_log_slot_err_lock(slot, "Program NIC EMMC failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True


#    def mtp_program_single_nic_emmc(self, slot, emmc_img, nic_rslt_list):
#        self.cli_log_slot_inf_lock(slot, "Program NIC EMMC")
#        if not self._nic_ctrl_list[slot].nic_program_emmc(emmc_img):
#            self.cli_log_slot_inf_lock(slot, "Program NIC EMMC failed")
#            return
#
#        if not self.mtp_mgmt_set_nic_sw_boot(slot):
#            return
#
#        self.cli_log_slot_inf_lock(slot, "Program NIC EMMC complete")
#        nic_rslt_list[slot] = True
#        return
#
#
#    def mtp_program_nic_emmc(self, nic_list, emmc_img):
#        fail_list = list()
#        nic_thread_list = list()
#        nic_rslt_list = [False] * self._slots
#
#        for slot in nic_list:
#            nic_thread = threading.Thread(target = self.mtp_program_single_nic_emmc,
#                                          args = (slot, emmc_img, nic_rslt_list))
#            nic_thread.daemon = True
#            nic_thread.start()
#            nic_thread_list.append(nic_thread)
#
#        while True:
#            if len(nic_thread_list) == 0:
#                break
#            for nic_thread in nic_thread_list[:]:
#                if not nic_thread.is_alive():
#                    ret = nic_thread.join()
#                    nic_thread_list.remove(nic_thread)
#            time.sleep(5)
#
#        for slot in nic_list:
#            if not nic_rslt_list[slot]:
#                fail_list.append(slot)
#
#        return fail_list


    def mtp_mgmt_setup_nic_diag(self, slot, nic_utils=False):
        if nic_utils:
            msg = "Copy and Setup NIC Diag Image"
        else:
            msg = "Setup NIC Diag Image"
        self.cli_log_slot_inf_lock(slot, msg)

        nic_diag_image = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.MTP_ARM64_IMAGE
        if self._cicd_run:
            nic_asic_image = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.ASIC_ARM64_IMAGE
        else:
            nic_asic_image = ""
        if not self._nic_ctrl_list[slot].nic_setup_diag_img(nic_diag_image, nic_asic_image, nic_utils):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_set_nic_status_fail(slot)
            return False

        return True


    def mtp_mgmt_save_nic_logfile(self, slot, logfile_list):
        self.cli_log_slot_inf(slot, "Collecting NIC tclsh logfiles")
        if not self._nic_ctrl_list[slot].nic_save_logfile(logfile_list):
            self.cli_log_slot_err_lock(slot, "Save NIC Logfile failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True


    @test_utils.parallel_threaded_test
    def mtp_mgmt_save_nic_diag_logfile(self, slot, aapl):
        self.cli_log_slot_inf(slot, "Collecting NIC diag logfiles")
        if not self._nic_ctrl_list[slot].nic_save_diag_logfile(aapl):
            self.cli_log_slot_err_lock(slot, "Save NIC Diag Logfile failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        # self.mtp_mgmt_nic_diag_sys_clean()

        return True

    def mtp_post_dsp_fail_steps(self, slot, test, rslt, rslt_cmd_buf, err_msg_list, skip_vrm_check=None):
        """
        1. ping slot with 10 packets        <= whether management port is down
        2. connect console and do "env"     <= Check if card rebooted
        3. inventory -sts -slot <>          <= Clue of reboot reason/power/clk
        """
        ret = True
        dsp_timeout_sig = "_NOT_ a live card: NIC"

        # if rslt == "TIMEOUT":
        # if dsp_timeout_sig in rslt_cmd_buf:
        self.cli_log_slot_err(slot, "Performing post DSP {:s} fail steps".format(test))
        self.log_nic_file(slot, "#######= {:s} =#######".format("START post dsp {:s} fail debug".format(test)))

        # dump cpld status bits
        if not self.mtp_mgmt_set_nic_avs_post(slot):
            ret = False

        # ping test (try twice)
        ipaddr = libmfg_utils.get_nic_ip_addr(slot)
        for x in range(2):
            self.cli_log_slot_inf(slot, "Ping NIC MGMT port <{:d}> try".format(x+1))
            time.sleep(5)
            cmd = "ping -c 10 {:s}".format(ipaddr)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                ret = False

        # check if card rebooted, but not valid for bash mvl tests
        if "ACC" not in test and "STUB" not in test and test != "L1":
            self.mtp_nic_console_lock()
            if not self.mtp_check_nic_rebooted(slot):
                ret = False
            self.mtp_nic_console_unlock()

        # VRM check in get_nic_sts causes a reboot. 
        # so skip it for all dsp tests where we need to keep card state.
        # can skip it for tests that have powercycle right after, such as all nic_test.py tests in mtp_para.
        if skip_vrm_check is None:
            skip_vrm_check = True

        nic_type = self.mtp_get_nic_type(slot)
        # check ECC for elba cards
        # dont check ECC after L1 test
        # or if ddr_bist is offloaded from L1, check ecc after L1 but dont check ecc after DDR_BIST
        if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            if nic_type in CONSOLE_DDR_BIST_NIC_LIST and "DDR_BIST" in test:
                pass
            elif test in ("L1"):
                pass
            else:
                self.mtp_single_j2c_lock()
                self.mtp_nic_console_lock()
                self.mtp_get_nic_sts(slot, skip_vrm_check)
                self.mtp_nic_console_unlock()
                self.mtp_single_j2c_unlock()

        self.mtp_mgmt_nic_diag_sys_clean()

        self.log_nic_file(slot, "#######= {:s} =#######".format("END post dsp {:s} fail debug".format(test)))

        return ret

    def mtp_mgmt_nic_diag_sys_clean(self):
        cmd = "diag -csys"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False
        return True
        # self.mtp_nic_console_lock()
        # self.mtp_single_j2c_lock()
        # self.cli_log_inf("NIC Diag Sys Clean", level=0)

        # cmd = MFG_DIAG_CMDS.NIC_SYS_CLEAN_FMT.format(MTP_DIAG_Path.ONBOARD_MTP_MTP_DIAG_PATH)

        # if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
        #     ret = False

        # cmd_buf = self._cmd_buf
        # if ret and not cmd_buf:
        #     self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
        #     ret = False

        # if ret:
        #     # wait for completion sig to avoid interfering with other tests
        #     if self._asic_support != "capri":
        #     # issue with capri diag image... 
        #         if "sys_clean done" in cmd_buf:
        #             ret = True
        #         else:
        #             ret = False
            
        # self.mtp_single_j2c_unlock()
        # self.mtp_nic_console_unlock()
        # return ret

    def mtp_mgmt_killall_tclsh_picocom(self):
        cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False
        cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_PICOCOM_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False
        return True

    def mtp_mgmt_start_nic_diag(self, slot, aapl, dis_hal=False):
        if dis_hal:
            msg = "Start NIC Diag with HAL"
        else:
            if aapl:
                msg = "Start NIC Diag with HAL"
            else:
                msg = "Start NIC Diag without HAL"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_start_diag(aapl, dis_hal):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_set_nic_status_fail(slot)
            return False

        return True


    def mtp_set_nic_vmarg(self, slot, vmarg, percentage=""):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Vmargin for Proto NIC")
            return True

        if percentage:
            self.cli_log_slot_inf_lock(slot, "Set voltage margin to {:s} with percentage {:s}".format(vmarg, percentage))
        else:
            self.cli_log_slot_inf_lock(slot, "Set voltage margin to {:s}".format(vmarg))

        if not self._nic_ctrl_list[slot].nic_set_vmarg(vmarg, percentage):
            self.cli_log_slot_err_lock(slot, "Set voltage margin to {:s} failed".format(vmarg))
            self.mtp_set_nic_status_fail(slot)
            return False

        return True

    def mtp_nic_display_voltage(self, slot):
        if not self._nic_ctrl_list[slot].nic_display_voltage():
            self.cli_log_slot_err_lock(slot, "Voltage display failed")
            return False

        return True

    def mtp_nic_emmc_init(self, slot, emmc_format=False, emmc_check=False):
        nic_type = self.mtp_get_nic_type(slot)
        if emmc_format:
            msg = "Format and Init NIC EMMC"
        else:
            msg = "Init NIC EMMC"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_init_emmc(emmc_format, emmc_check=emmc_check):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_set_nic_status_fail(slot)
            return False

        if emmc_format:
            if not self.mtp_nic_emmc_set_perf_mode(slot):
                return False
        else:
            if not self.mtp_nic_emmc_check_perf_mode(slot):
                return False

        return True

    def mtp_nic_emmc_set_perf_mode(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in (NIC_Type.ORTANO, NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO,
                        NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4):
            msg = "Set NIC in performance mode"
            if not self._nic_ctrl_list[slot].nic_emmc_set_perf_mode():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
                self.mtp_dump_nic_err_msg(slot)
                self.mtp_set_nic_status_fail(slot)
                return False
            self.cli_log_slot_inf_lock(slot, msg)
        return True

    def mtp_nic_emmc_check_perf_mode(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in (NIC_Type.ORTANO, NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO,
                        NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4):
            msg = "NIC in performance mode"
            if not self._nic_ctrl_list[slot].nic_emmc_check_perf_mode():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
                self.mtp_dump_nic_err_msg(slot)
                return False
            self.cli_log_slot_inf_lock(slot, msg)
        return True

    def fst_nic_set_perf_mode(self, slot):
        # Ensure performance mode even though this step is not needed with newer mainfw anymore.
        self.cli_log_slot_inf(slot, "Set performance mode")
        cmd = "touch /sysconfig/config0/.perf_mode"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to set performance mode")
            return False
        return True

    def mtp_nic_fru_init(self, slot, init_date=True, nic_type=None, fru_fpo=False):
        if init_date:
            msg = "Init NIC FRU info with date"
        else:
            msg = "Init NIC FRU info without date"

        if fru_fpo:
            msg += " with FPO"

        dsp = "DIAG_INIT"
        sn = self.mtp_get_nic_sn(slot)
        test = "NIC_FRU_INIT"
        self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = self.log_slot_test_start(slot, test)

        if not self._nic_ctrl_list[slot].nic_fru_init(self._factory_location, init_date, self._swmtestmode[slot], fpo=fru_fpo):
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_set_nic_status_fail(slot)
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            return False

        duration = self.log_slot_test_stop(slot, test, start_ts)
        self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        return True

    def mtp_nic_ocp_adapter_fru_init(self, slot, fpo=False):
        if self.mtp_get_nic_type(slot) != NIC_Type.NAPLES25OCP:
            self.cli_log_slot_err(slot, "OCP Adapter FRU init function is not for type {:s}".format(self.mtp_get_nic_type(slot)))
            return False

        if not self._nic_ctrl_list[slot].nic_ocp_adapter_fru_init(self._factory_location, fpo):
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_get_nic_ocp_adapter_sn(self, slot):
        if self.mtp_get_nic_type(slot) != NIC_Type.NAPLES25OCP:
            self.cli_log_slot_err(slot, "OCP Adapter FRU init function is not for type {:s}".format(self.mtp_get_nic_type(slot)))
            return None

        if self._nic_ctrl_list[slot]._riser_sn is None:
            if not self.mtp_nic_ocp_adapter_fru_init(slot):
                return None

        return self._nic_ctrl_list[slot]._riser_sn

    def mtp_get_nic_ocp_adapter_progdate(self, slot):
        if self.mtp_get_nic_type(slot) != NIC_Type.NAPLES25OCP:
            self.cli_log_slot_err(slot, "OCP Adapter FRU init function is not for type {:s}".format(self.mtp_get_nic_type(slot)))
            return None

        if self._nic_ctrl_list[slot]._riser_progdate is None:
            if not self.mtp_nic_ocp_adapter_fru_init(slot):
                return None

        return self._nic_ctrl_list[slot]._riser_progdate

    def mtp_nic_sn_init(self, slot, fpo=False):
        if not self._nic_ctrl_list[slot]._sn:
            if not self._nic_ctrl_list[slot].nic_smb_fru_init(self._factory_location, fpo=fpo):
                return False
            self.mtp_set_nic_sn(slot, self._nic_ctrl_list[slot]._sn)
        return True

    def mtp_nic_cpld_init(self, slot, smb=False):
        self.cli_log_slot_inf_lock(slot, "Init NIC CPLD info")
        if not self._nic_ctrl_list[slot].nic_cpld_init(smb):
            self.cli_log_slot_err_lock(slot, "Init NIC CPLD failed")
            return False

        return True


    def mtp_mgmt_set_nic_sw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_sw_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default sw boot")
        return True


    def mtp_mgmt_set_nic_gold_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_gold_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default gold boot failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default gold boot")
        return True

            
    def mtp_mgmt_set_nic_goldfw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_goldfw_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default gold boot failed")
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default gold boot")
        return True
    def mtp_nic_load_scan_fru(self, nic_fru_cfg=None):
        self.cli_log_inf("Load NIC FRU config")
        if not nic_fru_cfg:
            nic_fru_cfg_file = "config/{:s}.yaml".format(self._id)
            self.cli_log_inf("Load from config file: {:s}".format(nic_fru_cfg_file))
            nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(nic_fru_cfg_file)

        for slot in range(self._slots):
            key = libmfg_utils.nic_key(slot)
            valid = nic_fru_cfg[self._id][key]["VALID"]
            if str.upper(valid) == "YES":
                sn = nic_fru_cfg[self._id][key]["SN"]
                self.mtp_set_nic_scan_sn(slot, sn)
        self.cli_log_inf("Load NIC FRU config complete\n")
        return True


    def mtp_nic_info_disp(self, nic_list, fru_valid=True):
        self.cli_log_inf("MTP NIC Info Dump:")

        for slot in nic_list:
            prsnt = self.mtp_nic_check_prsnt(slot)
            nic_type = self.mtp_get_nic_type(slot)

            if prsnt:
                self.cli_log_slot_inf(slot, "NIC is Present, Type is: {:s}".format(nic_type))
                if fru_valid:
                    fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()

                    riser_sn = None
                    riser_progdate = None
                    if nic_type == NIC_Type.NAPLES25OCP:
                        riser_sn = self.mtp_get_nic_ocp_adapter_sn(slot)
                        riser_progdate = self.mtp_get_nic_ocp_adapter_progdate(slot)

                    if not fru_info_list:
                        self.cli_log_slot_err_lock(slot, "Retrieve NIC FRU failed")
                        if nic_type == NIC_Type.NAPLES25OCP:
                            if riser_sn is None or riser_progdate is None:
                                self.cli_log_slot_err_lock(slot, "Retrieve OCP Adapter FRU failed")
                    else:
                        self.cli_log_slot_inf(slot, "==> FRU: {:s}, {:s}, {:s}".format(fru_info_list[0],fru_info_list[1],fru_info_list[2]))
                        if fru_info_list[3]:
                            self.cli_log_slot_inf(slot, "==> FRU Program Date: {:s}".format(fru_info_list[3]))
                        if nic_type == NIC_Type.NAPLES25OCP:
                            self.cli_log_slot_inf(slot, "==> OCP Adapter SN: {:s}, FRU Program Date: {:s}".format(riser_sn, riser_progdate))
                boot_info_list = self._nic_ctrl_list[slot].nic_get_boot_info()
                if not boot_info_list:
                    self.cli_log_slot_err(slot, "Retrieve NIC boot info failed")
                else:
                    self.cli_log_slot_inf(slot, "==> Boot image: {:s}({:s})".format(boot_info_list[0], boot_info_list[1]))

                cpld_info_list = self._nic_ctrl_list[slot].nic_get_cpld()
                if not cpld_info_list:
                    self.cli_log_slot_err(slot, "Retrieve NIC CPLD info failed")
                else:
                    self.cli_log_slot_inf(slot, "==> CPLD: {:s}({:s})".format(cpld_info_list[0], cpld_info_list[1]))

                diag_info_list = self._nic_ctrl_list[slot].nic_get_diag()
                if not diag_info_list:
                    self.cli_log_slot_err(slot, "Retrieve NIC Diag info failed")
                else:
                    self.cli_log_slot_inf(slot, "==> Diag version: {:s}".format(diag_info_list[0]))
                    self.cli_log_slot_inf(slot, "==> EMMC Util version: {:s}".format(diag_info_list[1]))
                    self.cli_log_slot_inf(slot, "==> NIC ASIC version: {:s}".format(diag_info_list[2]))

                if not self._nic_ctrl_list[slot].nic_check_status():
                    self.cli_log_slot_err(slot, "NIC in failure state")
            elif self._slots_to_skip[slot]:
                self.cli_log_slot_err(slot, "NIC is Skipped")
            else:
                self.cli_log_slot_err(slot, "NIC is Absent")
        self.cli_log_inf("End MTP NIC Info Dump")


    def mtp_nic_init(self, stage=None, new_ssh_sessions=True, scanned_fru=None):
        self.cli_log_inf("Init NICs in the MTP Chassis", level = 0)

        # open ssh session to each NIC
        if new_ssh_sessions:
            self.cli_log_inf("Init NIC Connections", level = 0)
            if not self.mtp_nic_para_session_init():
                self.cli_log_err("Init NIC Connections Failed", level = 0)
                return False

        # init nic present list
        if stage == FF_Stage.FF_FST:
            if not self.fst_init_nic_type(scanned_fru):
                self.cli_log_inf("Failed to init NICs in the FST", level = 0)
                return False
        else:
            if not self.mtp_init_nic_type(stage, scanned_fru):
                self.cli_log_inf("Failed to init NICs in the MTP Chassis", level = 0)
                return False

        self.cli_log_inf("Init NICs in the MTP Chassis complete\n", level = 0)

        return True

    # validate the fru to double confirm scan process
    def mtp_nic_scan_fru_validate(self, nic_list):
        if not nic_list:
            self.cli_log_err("No NICs passed to validate scanned FRU")
            return False

        for slot in nic_list:
            if self._nic_scan_prsnt_list[slot] != self._nic_prsnt_list[slot]:
                # NIC present, but not scanned
                if self._nic_prsnt_list[slot]:
                    self.cli_log_slot_err(slot, "NIC is present, but barcode is not scanned")
                    return False

            if not self.mtp_check_nic_status(slot):
                self.cli_log_slot_err(slot, "NIC is in failure state, bypass fru validation")
                continue

            # NIC sn should match
            if self._nic_scan_prsnt_list[slot] and self._nic_prsnt_list[slot]:
                if self._nic_scan_sn_list[slot] != self._nic_sn_list[slot]:
                    self.cli_log_slot_err(slot, "SN mismatch, scanned: {:s}, fru: {:s}".format(self._nic_scan_sn_list[slot], self._nic_sn_list[slot]))
                    return False
        return True


    def mtp_single_nic_diag_init(self, slot, emmc_format, emmc_check, fru_valid, vmargin, aapl, dis_hal, fru_fpo, stop_on_err, vmarg_percentage=""):
        ret = True
        nic_type = self.mtp_get_nic_type(slot)

        start_ts = self.log_slot_test_start(slot, "NIC_DIAG_INIT")

        # (DIAG_INIT, START_DIAG) START
        dsp = "DIAG_INIT"
        sn = self.mtp_get_nic_sn(slot)
        test = "START_DIAG"
        self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = self.log_slot_test_start(slot, test)

        if ret and not self.mtp_nic_emmc_init(slot, emmc_format, emmc_check=emmc_check):
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            ret = False

        if ret and not self.mtp_mgmt_setup_nic_diag(slot, emmc_format):
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            ret = False

        if ret and not self.mtp_mgmt_start_nic_diag(slot, aapl, dis_hal):
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            ret = False
        
        if ret:
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        # (DIAG_INIT, START_DIAG) END

        # (DIAG_INIT, CPLD_DIAG) START
        test = "CPLD_DIAG"
        self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        #self._nic_test_block_log_list[slot].append(self.get_cli_log_slot_msg(slot,MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test), 0, "INF") )
        start_ts = self.log_slot_test_start(slot, test)


        if ret and not self.mtp_nic_cpld_init(slot):
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            ret = False

        if not emmc_format:
            if ret and not self.mtp_check_nic_cpld_partition(slot):
                duration = self.log_slot_test_stop(slot, test, start_ts)
                self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                ret = False
        
        if ret:
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration)) 
        # (DIAG_INIT, CPLD_DIAG) END           

        if ret and fru_valid:
            if emmc_format:
                init_date = False
            else:
                init_date = True
            if not self.mtp_nic_fru_init(slot, init_date, nic_type, fru_fpo):
                ret = False
            fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
            if fru_info_list:
                self.mtp_set_nic_sn(slot, fru_info_list[0])
            else:
                self.cli_log_slot_err(slot, "Unable to load SN")
                ret = False
        elif not fru_valid:
            self.mtp_set_nic_sn(slot, self.mtp_get_nic_scan_sn(slot))

        if ret:
            # (DIAG_INIT, NIC_VMARG) START
            test = "NIC_VMARG"
            self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = self.log_slot_test_start(slot, test)

            if ret and not self.mtp_set_nic_vmarg(slot, vmargin, vmarg_percentage):
                ret = False

            if ret and not self.mtp_nic_display_voltage(slot):
                ret = False

            duration = self.log_slot_test_stop(slot, test, start_ts)
            if not ret:
                self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            else:
                self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration)) 
            # (DIAG_INIT, NIC_VMARG) END 

        duration = self.log_slot_test_stop(slot, "NIC_DIAG_INIT", start_ts)

        if not ret:
            self.mtp_set_nic_status_fail(slot)

        return ret

    def mtp_nic_mgmt_seq_init(self, nic_list, fpo, stop_on_err=False):
        for slot in nic_list:
            if self._nic_prsnt_list[slot] and self.mtp_check_nic_status(slot):
                if not self.mtp_nic_mini_init(slot, fpo):
                    self.mtp_set_nic_status_fail(slot)
                    if stop_on_err:
                        return False
                    else:
                        continue
        return True

    def mtp_nic_mgmt_para_init_fpo(self, nic_list, stop_on_err=False):
        nic_test_list = list()
        for slot in nic_list:
            if self._nic_prsnt_list[slot]:
                if not self.mtp_check_nic_status(slot):
                    self.cli_log_slot_err(slot, "Para Init NIC MGMT port bypassed for failed NIC")
                    if stop_on_err:
                        return False
                    else:
                        continue
                nic_test_list.append(slot)
        nic_list = nic_test_list

        if not nic_list:
            self.cli_log_err("No NICs passed")
            return False

        # parallel init mgmt
        dsp = "DIAG_INIT"
        sn = ""
        test = "NIC_PARA_MGMT_FPO_INIT"
        start_ts = libmfg_utils.timestamp_snapshot()

        mtp_start_ts = self.log_test_start(test)
        for slot in nic_list:
            sn = self.mtp_get_nic_sn(int(slot))
            slot_start_ts = self.log_slot_test_start(slot, test)
            self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        asic_type = "elba" if self._asic_support == MTP_ASIC_SUPPORT.ELBA or self._asic_support == MTP_ASIC_SUPPORT.TURBO_ELBA else "capri"
        sig_list = [MFG_DIAG_SIG.NIC_MGMT_PARA_SIG]
        for slot in nic_list:
            self.cli_log_slot_inf(slot, "Para Init NIC MGMT port with FPO")
        cmd = MFG_DIAG_CMDS.MTP_PARA_MGMT_FPO_FMT.format(nic_list_param, asic_type)

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            duration = self.log_test_stop(test, start_ts)
            for slot in nic_list:
                self.log_slot_test_stop(slot, test, start_ts)
                sn = self.mtp_get_nic_sn(int(slot))
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                self.mtp_set_nic_status_fail(slot)
            return False
        if "failed" in self.mtp_get_cmd_buf():
            match = re.search("failed! *([0-9,]+)", self.mtp_get_cmd_buf())
            if match:
                for slot in libmfg_utils.expand_range_of_numbers(match.group(1), range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot-1
                    self.cli_log_slot_err_lock(slot, "Para Init NIC MGMT failed")
                    self.mtp_set_nic_status_fail(slot)

        if not self.mtp_nic_mgmt_mac_refresh(nic_list):
            duration = self.log_test_stop(test, start_ts)
            for slot in nic_list:
                self.log_slot_test_stop(slot, test, start_ts)
                sn = self.mtp_get_nic_sn(int(slot))
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                self.mtp_set_nic_status_fail(slot)
            return False

        duration = self.log_test_stop(test, start_ts)
        for slot in nic_list:
            self.log_slot_test_stop(slot, test, start_ts)
            sn = self.mtp_get_nic_sn(int(slot))
            if not self.mtp_check_nic_status(slot):
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            else:
                self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


        for slot in nic_list:
            sn = self.mtp_get_nic_sn(slot)
            dsp = "DIAG_INIT"
            test = "NIC_BOOT_INIT"
            if not self.mtp_check_nic_status(slot):
                continue
            self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = self.log_slot_test_start(slot, test)

            if not self.mtp_nic_boot_info_init(slot):
                duration = self.log_slot_test_stop(slot, test, start_ts)
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                self.mtp_set_nic_status_fail(slot)
                if stop_on_err:
                    return False
                else:
                    continue
            else:
                duration = self.log_slot_test_stop(slot, test, start_ts)
                self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        return True

    def nic_semi_parallel_log(self, nic_list, buf):
        buf = buf[:] # make a copy
        capture = [True] * self._slots
        logbuf = [""] * self._slots
        for line in buf.splitlines():
            for slot in nic_list:
                if re.search("Starting [\w ]+ on slot %s" % str(slot+1), line) or re.search("Checking [\w ]*result on slot %s" % str(slot+1), line):
                    capture = [False] * self._slots
                    capture[slot] = True
                elif re.search("Setup env on slot %s env setup done" % str(slot+1), line) or re.search("on slot %s started" % str(slot+1), line) or re.search("Check?ing [\w ]*result on slot %s Done" % str(slot+1), line):
                    capture = [False] * self._slots
                    logbuf[slot] += line + "\n" #final line
                if capture[slot]:
                    if line.strip(): # skip empty new line
                        logbuf[slot] += line + "\n"

        for slot in nic_list:
            self._nic_ctrl_list[slot].mtp_exec_cmd(": <<'////'\nCopied log from mtp_diag.log:\n{:s}\n////".format(logbuf[slot]))

        return True

    def mtp_nic_mgmt_para_init(self, nic_list, aapl, swm_lp=False, stop_on_err=False):
        nic_test_list = list()
        for slot in nic_list:
            if self._nic_prsnt_list[slot]:
                if not self.mtp_check_nic_status(slot):
                    self.cli_log_slot_err(slot, "Para Init NIC MGMT port bypassed for failed NIC")
                    if stop_on_err:
                        return False
                    else:
                        continue
                nic_test_list.append(slot)
        nic_list = nic_test_list

        if not nic_list:
            self.cli_log_err("No NICs passed")
            return False

        # parallel init mgmt/aapl
        dsp = "DIAG_INIT"
        sn = ""
        test = "NIC_PARA_MGMT_AAPL_INIT" if aapl else "NIC_PARA_MGMT_INIT"
        start_ts = libmfg_utils.timestamp_snapshot()

        mtp_start_ts = self.log_test_start(test)
        for slot in nic_list:
            sn = self.mtp_get_nic_sn(int(slot))
            slot_start_ts = self.log_slot_test_start(slot, test)
            self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        asic_type = "elba" if self._asic_support == MTP_ASIC_SUPPORT.ELBA or self._asic_support == MTP_ASIC_SUPPORT.TURBO_ELBA else "capri"
        sig_list = [MFG_DIAG_SIG.NIC_MGMT_PARA_SIG]
        if aapl:
            for slot in nic_list:
                self.cli_log_slot_inf(slot, "Para Init NIC MGMT/AAPL port")
            cmd = MFG_DIAG_CMDS.MTP_PARA_MGMT_AAPL_FMT.format(nic_list_param, asic_type)
        else:
            for slot in nic_list:
                self.cli_log_slot_inf(slot, "Para Init NIC MGMT port")
            cmd = MFG_DIAG_CMDS.MTP_PARA_MGMT_INIT_FMT.format(nic_list_param, asic_type)
            if swm_lp:
                cmd = "".join((cmd, " -swm_lp"))
            # in case of nic-to-nic loopback, disable network ports:
            if asic_type == "elba":
                cmd = "".join((cmd, " -dis_net_port"))

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            duration = self.log_test_stop(test, start_ts)
            for slot in nic_list:
                self.log_slot_test_stop(slot, test, start_ts)
                sn = self.mtp_get_nic_sn(int(slot))
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                self.mtp_set_nic_status_fail(slot)
            return False
        self.nic_semi_parallel_log(nic_list, self.mtp_get_cmd_buf_before_sig())
        if "failed" in self.mtp_get_cmd_buf():
            match = re.search("failed! *([0-9,]+)", self.mtp_get_cmd_buf())
            if match:
                for slot in libmfg_utils.expand_range_of_numbers(match.group(1), range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot-1
                    self.cli_log_slot_err_lock(slot, "Para Init NIC MGMT failed")
                    self.mtp_set_nic_status_fail(slot)

        if not self.mtp_nic_mgmt_mac_refresh(nic_list):
            duration = self.log_test_stop(test, start_ts)
            for slot in nic_list:
                self.log_slot_test_stop(slot, test, start_ts)
                sn = self.mtp_get_nic_sn(int(slot))
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                self.mtp_set_nic_status_fail(slot)
            return False

        duration = self.log_test_stop(test, start_ts)
        for slot in nic_list:
            self.log_slot_test_stop(slot, test, start_ts)
            sn = self.mtp_get_nic_sn(int(slot))
            if not self.mtp_check_nic_status(slot):
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            else:
                self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))


        for slot in nic_list:
            sn = self.mtp_get_nic_sn(slot)
            dsp = "DIAG_INIT"
            test = "NIC_BOOT_INIT"
            if not self.mtp_check_nic_status(slot):
                continue
            self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
            start_ts = self.log_slot_test_start(slot, test)
            
            if not self.mtp_nic_boot_info_init(slot):
                duration = self.log_slot_test_stop(slot, test, start_ts)
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                self.mtp_set_nic_status_fail(slot)
                if stop_on_err:
                    return False
                else:
                    continue
            else:
                duration = self.log_slot_test_stop(slot, test, start_ts)
                self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))                

        return True

    def mtp_nic_edma_env_init(self, nic_list, stop_on_err=False):
        if not nic_list:
            self.cli_log_err("No NICs passed")
            return False

        # if 2D list passed from regression, need to flatten it
        if isinstance(nic_list[0], list):
            nic_list = libmfg_utils.flatten_list_of_lists(nic_list)
            
        nic_test_list = list()
        for slot in nic_list:
            if self._nic_prsnt_list[slot]:
                if not self.mtp_check_nic_status(slot):
                    self.cli_log_slot_err(slot, "Para Init EDMA environment init bypassed for failed NIC")
                    if stop_on_err:
                        return False
                    else:
                        continue
                nic_test_list.append(slot)
        nic_list = nic_test_list

        if not nic_list:
            self.cli_log_err("No NICs passed")
            return False

        # parallel init mgmt/aapl
        dsp = "EDMA_INIT"
        sn = ""
        test = "NIC_PARA_EDMA_ENV_INIT"
        start_ts = libmfg_utils.timestamp_snapshot()

        mtp_start_ts = self.log_test_start(test)
        for slot in nic_list:
            sn = self.mtp_get_nic_sn(int(slot))
            slot_start_ts = self.log_slot_test_start(slot, test)
            self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.NIC_PARA_EDMA_ENV_INIT_SIG]
        cmd = MFG_DIAG_CMDS.MTP_PARA_EDMA_ENV_INIT_FMT.format(nic_list_param)

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.NIC_EDMA_ENV_INIT_CMD_DELAY):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            duration = self.log_test_stop(test, start_ts)
            for slot in nic_list:
                self.log_slot_test_stop(slot, test, start_ts)
                sn = self.mtp_get_nic_sn(int(slot))
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                self.mtp_set_nic_status_fail(slot)
            return False
        if "FAIL list:" in self.mtp_get_cmd_buf_before_sig():
            match = re.search("FAIL list:', \[([0-9,']+)\]", self.mtp_get_cmd_buf_before_sig())
            if match:
                fail_slot_str = match.group(1).replace("'","")
                for slot in libmfg_utils.expand_range_of_numbers(fail_slot_str, range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot-1
                    self.cli_log_slot_err_lock(slot, "Para Init EDMA environment init failed")
                    self.mtp_set_nic_status_fail(slot)

        duration = self.log_test_stop(test, start_ts)
        for slot in nic_list:
            self.log_slot_test_stop(slot, test, start_ts)
            sn = self.mtp_get_nic_sn(int(slot))
            if not self.mtp_check_nic_status(slot):
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            else:
                self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))             

        return True

    def mtp_nic_para_init(self, nic_list, stop_on_err=False):
        nic_test_list = list()
        for slot in nic_list:
            if self._nic_prsnt_list[slot]:
                if not self.mtp_check_nic_status(slot):
                    self.cli_log_slot_err(slot, "Para Init NIC MGMT port bypassed for failed NIC")
                    if stop_on_err:
                        return False
                    else:
                        continue
                nic_test_list.append(slot)
        nic_list = nic_test_list

        if not nic_list:
            self.cli_log_err("No NICs passed")
            return False

        # parallel init nic
        dsp = "DIAG_INIT"
        sn = ""
        test = "NIC_PARA_INIT"
        start_ts = libmfg_utils.timestamp_snapshot()

        mtp_start_ts = self.log_test_start(test)
        for slot in nic_list:
            sn = self.mtp_get_nic_sn(int(slot))
            slot_start_ts = self.log_slot_test_start(slot, test)
            self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        asic_type = "elba" if self._asic_support == MTP_ASIC_SUPPORT.ELBA or self._asic_support == MTP_ASIC_SUPPORT.TURBO_ELBA else "capri"
        sig_list = [MFG_DIAG_SIG.NIC_PARA_SIG]
        for slot in nic_list:
            self.cli_log_slot_inf(slot, "Para Init NIC port")
        cmd = MFG_DIAG_CMDS.MTP_PARA_INIT_FMT.format(nic_list_param, asic_type)

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            duration = self.log_slot_test_stop(slot, test, start_ts)
            for slot in nic_list:
                sn = self.mtp_get_nic_sn(int(slot))
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            return False
        self.nic_semi_parallel_log(nic_list, self.mtp_get_cmd_buf_before_sig())
        if "failed" in self.mtp_get_cmd_buf():
            match = re.search("failed! *([0-9,]+)", self.mtp_get_cmd_buf())
            if match:
                for slot in libmfg_utils.expand_range_of_numbers(match.group(1), range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot-1
                    self.cli_log_slot_err_lock(slot, "Para Init NIC failed")
                    self.mtp_set_nic_status_fail(slot)

        duration = self.log_test_stop(test, start_ts)
        for slot in nic_list:
            self.log_slot_test_stop(slot, test, start_ts)
            sn = self.mtp_get_nic_sn(int(slot))
            if not self.mtp_check_nic_status(slot):
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                if stop_on_err:
                    return False
                else:
                    continue
            else:
                self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        return True

    def mtp_nic_mgmt_mac_refresh(self, nic_list):
        # delete the arp entry
        for slot in nic_list:
            if self._nic_prsnt_list[slot]:
                ipaddr = libmfg_utils.get_nic_ip_addr(slot)
                cmd = MFG_DIAG_CMDS.MTP_ARP_DELET_FMT.format(ipaddr)
                if not self.mtp_mgmt_exec_sudo_cmd(cmd):
                    return False

                ###Have seen failures on Naples25SWM where ping fails and ARP table is not populated
                ###Add a 2nd ping try as a work around.   
                # first ping, send only 1 packet to wake it up

                # time.sleep(5)
                cmd = "ping -c 1 {:s}".format(ipaddr)
                if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
                    return False

                # time.sleep(5)
                cmd = MFG_DIAG_CMDS.MTP_NIC_PING_FMT.format(ipaddr)
                if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
                    return False

        return True


    def mtp_nic_diag_init(self, nic_list, emmc_format=False, emmc_check=False, fru_valid=True, sn_tag=False, fru_cfg=None, vmargin=Voltage_Margin.normal, aapl=False, swm_lp=False, nic_util=False, dis_hal=False, stop_on_err=False, skip_info_dump=False, fru_fpo=False):
        ret = True
        if not nic_list:
            self.cli_log_err("No NICs passed")
            return False

        # if 2D list passed from regression, need to flatten it
        if isinstance(nic_list[0], list):
            nic_list = libmfg_utils.flatten_list_of_lists(nic_list)

        # emmc_format will be true only for the first time boot up
        fpo = emmc_format
        if fpo:
            self.cli_log_inf("Init NIC Diag Environment with FPO set", level = 0)
        else:
            self.cli_log_inf("Init NIC Diag Environment", level = 0)

        if sn_tag:
            self.mtp_nic_load_scan_fru(fru_cfg)
        else:
            self.cli_log_inf("Bypass NIC SN/MAC load")

        if fpo:
            # ret = self.mtp_nic_mgmt_seq_init(nic_list, fpo, stop_on_err)
            ret = self.mtp_nic_mgmt_para_init_fpo(nic_list, stop_on_err)
        else:
            ret = self.mtp_nic_mgmt_para_init(nic_list, aapl, swm_lp, stop_on_err)

        if not ret:
            return False

        if not self.mtp_mgmt_nic_mac_validate():
            return False

        if nic_util:
            # for QA only not DL: do mgmt para init but do emmc format. 
            emmc_format = True

        vmarg_percentage = ""
        if vmargin in (Voltage_Margin.high, Voltage_Margin.low):
            partnumber = ""
            for nic_controller in  self._nic_ctrl_list:
                if nic_controller._pn:
                    partnumber = nic_controller._pn
                    break
            vmarg_percentage = libmfg_utils.pick_voltage_margin_percentage(partnumber)
            vmarg_percentage = vmarg_percentage.strip("_")
            self.cli_log_inf("Got Vmargin Percentage: {:s} With Part Number: {:s} ".format(vmarg_percentage, partnumber),  level=0)

        nic_thread_list = list()
        for slot in nic_list:
            if not self._nic_prsnt_list[slot] or not self.mtp_check_nic_status(slot):
                continue
            nic_thread = threading.Thread(target = self.mtp_single_nic_diag_init,
                                          args = (slot,
                                                  emmc_format,
                                                  emmc_check,
                                                  fru_valid,
                                                  vmargin,
                                                  aapl,
                                                  dis_hal,
                                                  fru_fpo,
                                                  stop_on_err,
                                                  vmarg_percentage))
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)

        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(5)

        if fru_valid and sn_tag:
            if not self.mtp_nic_scan_fru_validate(nic_list):
                return False

        if not skip_info_dump:
            self.mtp_nic_info_disp(nic_list, fru_valid)

        self.mtp_mgmt_killall_tclsh_picocom()

        # if any slot failed, return false
        for slot in nic_list:
            if not self.mtp_check_nic_status(slot):
                ret = False

        self.cli_log_inf("Init NIC Diag Environment complete\n", level = 0)
        return ret

    # check if any duplicate mac address in the internal network
    def mtp_mgmt_nic_mac_validate(self):
        #self.cli_log_inf("NIC MAC address validate started")
        dsp = "DIAG_INIT"
        test = "MAC_VALIDATE"   
        start_ts = libmfg_utils.timestamp_snapshot()
        nic_mac_addr_list = []
        nic_ip_addr_list = []
        #mac_addr_reg_exp = r"([a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2})"
        mac_addr_reg_exp = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+([a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2})"
        cmd = MFG_DIAG_CMDS.MTP_NIC_MAC_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            #self.cli_log_err("Failed to validate NIC MAC address")
            self.cli_log_slot_inf(None, MTP_DIAG_Report.NIC_DIAG_TEST_START.format("", dsp, test))
            duration = libmfg_utils.timestamp_snapshot() - start_ts
            self.cli_log_slot_err(None, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format("", dsp, test, "FAILED", duration))
            return False

        match = re.findall(mac_addr_reg_exp, self.mtp_get_cmd_buf())
        if match:
            for nic_info in match:
                if nic_info[0] in nic_ip_addr_list or nic_info[1] in nic_mac_addr_list:
                    slot = int(nic_info[0].split('.')[3]) - 101
                    sn = self.mtp_get_nic_sn(slot)
                    self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                    duration = libmfg_utils.timestamp_snapshot() - start_ts
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                    return False
                else:
                    slot = int(nic_info[0].split('.')[3]) - 101
                    sn = self.mtp_get_nic_sn(slot)
                    self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
                    duration = libmfg_utils.timestamp_snapshot() - start_ts
                    self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
                    start_ts = libmfg_utils.timestamp_snapshot()

            return True
        else:
            self.cli_log_slot_inf(None, MTP_DIAG_Report.NIC_DIAG_TEST_START.format("", dsp, test))
            duration = libmfg_utils.timestamp_snapshot() - start_ts
            self.cli_log_slot_err(None, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format("", dsp, test, "FAILED", duration))
            return False


    def mtp_power_on_nic(self, slot_list=[], dl=False, count_down=True):
        self.mtp_nic_lock()

        slot_list_param = ",".join(str(slot+1) for slot in slot_list)
        if not slot_list_param:
            slot_list_param = "all"
        cmd = MFG_DIAG_CMDS.MTP_POWER_ON_NIC_FMT.format(slot_list_param)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.mtp_nic_unlock()
            self.cli_log_err("Failed to power on NIC")
            return False

        ts_record = libmfg_utils.timestamp_snapshot()
        for slot in range(self._slots):
            if self._nic_ctrl_list[slot]:
                self.log_nic_file(slot, "#####  Power on NIC #####")

        if count_down:
            self.cli_log_inf("Power on all NIC, wait {:02d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY), level=0)
            libmfg_utils.count_down(MTP_Const.NIC_POWER_ON_DELAY)
        else:
            self.cli_log_inf("Power on all NIC, NIC power up", level=0)

        self.mtp_nic_unlock()

        self.mtp_nic_lock()
        nic_list = list()
        if slot_list_param == "all":
            nic_list = [0,1,2,3,4,5,6,7,8,9]
        else:
            nic_list = slot_list[:]

        for slot in nic_list:
            if self._nic_ctrl_list[slot] and self._nic_type_list[slot] in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4) and not dl:
                if not self._nic_ctrl_list[slot].nic_set_i2c_after_pw_cycle():
                    self.mtp_get_nic_err_msg(slot)
                else:
                    self.cli_log_slot_inf(slot, "I2C value setting complete")             
        self.mtp_nic_unlock()

        return True


    def mtp_power_off_nic(self, slot_list=[]):
        self.mtp_nic_lock()
        slot_list_param = ",".join(str(slot+1) for slot in slot_list)
        if not slot_list_param:
            slot_list_param = "all"
        cmd = MFG_DIAG_CMDS.MTP_POWER_OFF_NIC_FMT.format(slot_list_param)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.mtp_nic_unlock()
            self.cli_log_err("Failed to power off NIC")
            return False

        ts_record = libmfg_utils.timestamp_snapshot()
        for slot in range(self._slots):
            if self._nic_ctrl_list[slot]:
                self.log_nic_file(slot, "##### Power off NIC #####")

        self.cli_log_inf("Power off all NIC, wait {:02d} seconds for NIC power down".format(MTP_Const.NIC_POWER_OFF_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.NIC_POWER_OFF_DELAY)
        self.mtp_nic_unlock()
        return True


    def mtp_power_cycle_nic(self, slot_list=[], dl=False, count_down=True):
        rc = self.mtp_power_off_nic(slot_list)
        if not rc:
            return rc

        rc = self.mtp_power_on_nic(slot_list, dl, count_down)
        return rc

    def mtp_init_nic_type(self, stage=None, scanned_fru=None):
        self._nic_type_list = [None] * self._slots      # reset nic types
        cmd = MFG_DIAG_CMDS.NIC_PRESENT_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to init NIC presence")
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False

        # find type
        self.cli_log_inf("Init NIC Presence, Type")
        regex_dict = {
                      NIC_Type.NAPLES100:       MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100,
                      NIC_Type.NAPLES100IBM:    MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100IBM,
                      NIC_Type.NAPLES100HPE:    MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100HPE,
                      NIC_Type.NAPLES100DELL:   MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100DELL,
                      NIC_Type.NAPLES25:        MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25,
                      NIC_Type.FORIO:           MFG_DIAG_RE.MFG_NIC_TYPE_FORIO,
                      NIC_Type.VOMERO:          MFG_DIAG_RE.MFG_NIC_TYPE_VOMERO,
                      NIC_Type.VOMERO2:         MFG_DIAG_RE.MFG_NIC_TYPE_VOMERO2,
                      NIC_Type.NAPLES25SWM:     MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWM,
                      NIC_Type.NAPLES25OCP:     MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25OCP,
                      NIC_Type.NAPLES25SWMDELL: MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWMDELL,
                      NIC_Type.NAPLES25SWM833:  MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWM833,
                      NIC_Type.ORTANO:          MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO,
                      NIC_Type.ORTANO2:         MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2,
                      NIC_Type.POMONTEDELL:     MFG_DIAG_RE.MFG_NIC_TYPE_POMONTEDELL,
                      NIC_Type.LACONA32DELL:    MFG_DIAG_RE.MFG_NIC_TYPE_LACONA32DELL,
                      NIC_Type.LACONA32:        MFG_DIAG_RE.MFG_NIC_TYPE_LACONA32,
                      NIC_Type.ORTANO2ADI:      MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2ADI,
                      NIC_Type.ORTANO2INTERP:   MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2INTERP,
                      NIC_Type.ORTANO2SOLO:     MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2SOLO,
                      NIC_Type.ORTANO2ADICR:    MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2ADICR,
                      NIC_Type.GINESTRA_D4:     MFG_DIAG_RE.MFG_NIC_TYPE_GINESTRA_D4,
                      NIC_Type.GINESTRA_D5:     MFG_DIAG_RE.MFG_NIC_TYPE_GINESTRA_D5
                      }
        
        for nic_type in regex_dict.keys():
            match = re.findall(regex_dict[nic_type], self._mgmt_handle.before)
            if match:
                for idx in range(len(match)):
                    slot = int(match[idx]) - 1
                    if not self._slots_to_skip[slot]:
                        self._nic_prsnt_list[slot] = True
                        self._nic_type_list[slot] = nic_type
                        self._nic_ctrl_list[slot].nic_set_type(nic_type)
                    else:
                        self._nic_prsnt_list[slot] = False
                        self.cli_log_slot_wrn(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)

        if stage is None or stage == FF_Stage.FF_DL:
            fru_fpo = True
        else:
            fru_fpo = False

        if scanned_fru is None:
            self.cli_log_inf("Init NIC SN, PN")
        else:
            self.cli_log_inf("Init Scanned NIC SN, PN")

        for slot in range(self._slots):
            if not self._nic_prsnt_list[slot]:
                continue

            if scanned_fru is None:
                if not self.mtp_nic_sn_init(slot, fru_fpo):
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    self.mtp_set_nic_status_fail(slot)
                    continue
            else:
                # In ScanDL, use scanned SN, PN as ground truth
                mtp_id = self._id
                key = libmfg_utils.nic_key(slot)
                valid = scanned_fru[mtp_id][key]["VALID"]
                if str.upper(valid) != "YES":
                    self.cli_log_slot_err(slot, "Missing scan for this slot. Could not initialize.")
                    self.mtp_set_nic_status_fail(slot)
                    continue
                pn = scanned_fru[mtp_id][key]["PN"]
                sn = scanned_fru[mtp_id][key]["SN"]
                self.mtp_set_nic_sn(slot, sn)
                self.mtp_set_nic_pn(slot, pn)

        # set final nic_type
        for slot in range(self._slots):
            if self.mtp_check_nic_status(slot) and self.mtp_get_nic_type(slot) == NIC_Type.ORTANO2ADI:
                pn = self.mtp_get_nic_pn(slot)
                if re.match(PART_NUMBERS_MATCH.ORTANO2ADI_ORC_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADI
                elif re.match(PART_NUMBERS_MATCH.ORTANO2ADI_IBM_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADIIBM
                elif re.match(PART_NUMBERS_MATCH.ORTANO2ADI_MSFT_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADIMSFT
                self._nic_type_list[slot] = final_nic_type
                self._nic_ctrl_list[slot].nic_set_type(final_nic_type)
            if self.mtp_check_nic_status(slot) and self.mtp_get_nic_type(slot) == NIC_Type.ORTANO2SOLO:
                pn = self.mtp_get_nic_pn(slot)
                if re.match(PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2SOLO
                elif re.match(PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_THS_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2SOLOORCTHS
                elif re.match(PART_NUMBERS_MATCH.ORTANO2SOLO_MSFT_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2SOLOMSFT
                elif re.match(PART_NUMBERS_MATCH.ORTANO2SOLO_S4_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2SOLOS4
                self._nic_type_list[slot] = final_nic_type
                self._nic_ctrl_list[slot].nic_set_type(final_nic_type)
            if self.mtp_check_nic_status(slot) and self.mtp_get_nic_type(slot) == NIC_Type.ORTANO2ADICR:
                pn = self.mtp_get_nic_pn(slot)
                if re.match(PART_NUMBERS_MATCH.ORTANO2ADI_CR_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADICR
                elif re.match(PART_NUMBERS_MATCH.ORTANO2ADI_CR_MSFT_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADICRMSFT
                elif re.match(PART_NUMBERS_MATCH.ORTANO2ADI_CR_S4_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADICRS4
                self._nic_type_list[slot] = final_nic_type
                self._nic_ctrl_list[slot].nic_set_type(final_nic_type)

        # populate OCP adapter info
        for slot in range(self._slots):
            if self.mtp_get_nic_type(slot) == NIC_Type.NAPLES25OCP:
                if not self.mtp_get_nic_ocp_adapter_sn(slot):
                    self.cli_log_slot_err(slot, "OCP Adapter FRU missing")

        return True

    def fst_init_nic_type(self, scanned_fru=None):
        """
            Search lspci for DSCs
            And assign slot # in the order it appears in lspci
        """
        self.cli_log_inf("Init NIC Presence, Type")

        cmd = "lspci -d 1dd8:1004"
        self.mtp_mgmt_exec_cmd(cmd)
        result = self.mtp_get_cmd_buf()
        bus_list_match = re.findall(r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]+) ", result)

        # extra info dump
        cmd = "lspci -d 1dd8: -vvv"
        self.mtp_mgmt_exec_cmd(cmd)

        if len(bus_list_match) == 0:
            self.cli_log_err("No devices found")
            return False

        if scanned_fru:
            # build scanned serial number to scanned nic slot id mapping table
            sn2slot = dict()
            for slot in range(self._slots):
                key = libmfg_utils.nic_key(slot)
                if scanned_fru[key]["VALID"] == "Yes":
                    sn2slot[scanned_fru[key]["SN"]] = slot

            # Map to Scaned slot id by card serial number
            phy_present_slot_list = []
            phy_present_sn_list = []
            rc = True
            for bus in bus_list_match:
                cmd = "lspci -vvv -s {:s} | grep \"Serial number\" --color=never".format(bus)
                if not self.mtp_mgmt_exec_cmd(cmd):
                    rc = False
                result = self.mtp_get_cmd_buf()
                sn_match = re.search("Serial number: *([A-Z0-9]*)", result)
                if sn_match:
                    sn = sn_match.group(1)
                    if sn not in sn2slot:
                        self.cli_log_err("Physical Inserted Card {:s} NOT Scanned, Test Aborting ...".format(sn), level=0)
                        rc = False
                    phy_slot = sn2slot[sn]
                    phy_present_slot_list.append(phy_slot)
                    phy_present_sn_list.append(sn)
            if not rc:
                return rc

            # Validate if there is scanned card not physical present
            for sn in sn2slot:
                if sn not in phy_present_sn_list:
                    key = libmfg_utils.nic_key(slot)
                    self.cli_log_err("Scanned Card {:s} {:s} NOT Physical Present, Test Aborting ...".format(key, sn), level=0)
                    rc = False
            if not rc:
                return rc
            if not phy_present_slot_list:
                phy_present_slot_list = range(len(bus_list_match))
        else:
            phy_present_slot_list = range(len(bus_list_match))

        self.cli_log_inf("Found {:d} devices".format(len(bus_list_match)))
        self.cli_log_inf("Init NIC SN, PN")
        for slot, bus in zip(phy_present_slot_list, bus_list_match):
            if not self._slots_to_skip[slot]:
                self._nic_prsnt_list[slot] = True
                self._nic_ctrl_list[slot]._fst_pcie_bus = bus

                cmd = "lspci -vvv -s {:s} | grep \"Serial number\" --color=never".format(bus)
                self.mtp_mgmt_exec_cmd_para(slot, cmd)
                cmd_buf = self.mtp_get_nic_cmd_buf(slot)
                sn_match = re.search("Serial number: *([A-Z0-9]*)", cmd_buf)
                if sn_match:
                    self.mtp_set_nic_sn(slot, sn_match.group(1))

                cmd = "lspci -vvv -s {:s} | grep \"Part number\" --color=never".format(bus)
                self.mtp_mgmt_exec_cmd_para(slot, cmd)
                cmd_buf = self.mtp_get_nic_cmd_buf(slot)
                pn_match = re.search("Part number: *([A-Z0-9\-]*)", cmd_buf)
                if pn_match:
                    nic_type = get_product_name_from_pn_and_sn(pn_match.group(1), sn_match.group(1))
                    self.mtp_set_nic_type(slot, nic_type)
                    if nic_type in CAPRI_NIC_TYPE_LIST:
                        self._nic_ctrl_list[slot]._asic_type = "capri"
                    if nic_type in ELBA_NIC_TYPE_LIST:
                        self._nic_ctrl_list[slot]._asic_type = "elba"
                
                if not sn_match:
                    self.cli_log_slot_inf(slot, "Could not read SN from PCIe properties...will resort to penctl")
                if not pn_match or nic_type == NIC_Type.UNKNOWN:
                    self.cli_log_slot_inf(slot, "Could not determine NIC SKU from PCIe properties...will resort to penctl")
                    self.mtp_set_nic_type(slot, NIC_Type.NAPLES100) #default to naples100 setup steps
                    self._nic_ctrl_list[slot]._asic_type = "capri"
        return True


    def mtp_nic_check_prsnt(self, slot):
        return self._nic_prsnt_list[slot]


    def mtp_get_nic_prsnt_list(self):
        return self._nic_prsnt_list

    def mtp_get_nic_skip_list(self):
        return self._slots_to_skip

    def mtp_get_nic_pn(self, slot):
        return self._nic_ctrl_list[slot].nic_get_naples_pn()

    def mtp_set_nic_pn(self, slot, pn):
        self.cli_log_slot_inf(slot, "Set PN to {:s}".format(pn))
        self._nic_ctrl_list[slot].nic_set_pn(pn)

    def mtp_is_nic_ortano_oracle(self, slot):
        """
         Differentiate ortano by PN
         - 68-0015: Oracle version -> return True
         - 68-0021: Pensando version -> return False
         - any other -> return False with err msg
        """
        if self._nic_type_list[slot] != NIC_Type.ORTANO2:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for Ortano")
            return False
        slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for Ortano")
            return False
        oracle_pn = re.match(PART_NUMBERS_MATCH.ORTANO2_ORC_PN_FMT, slot_pn)
        if oracle_pn:
            return True
        else:
            return False

    def mtp_is_nic_ortano_microsoft(self, slot):
        """
         Differentiate ortano by PN
         - 68-0015: Oracle version -> return False
         - 68-0021: Pensando version -> return True
         - any other -> return False with err msg
        """
        if self._nic_type_list[slot] != NIC_Type.ORTANO2:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for Microsoft")
            return False
        slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for Ortano")
            return False
        microsoft_pn = re.match(PART_NUMBERS_MATCH.ORTANO2_PEN_PN_FMT, slot_pn)
        if microsoft_pn:
            return True
        else:
            return False

    def mtp_is_nic_ortanoadi_oracle(self, slot):
        """
         Differentiate ortano by PN
         - 68-0026: Oracle version -> return True
         - any other -> return False with err msg
        """
        if self._nic_type_list[slot] != NIC_Type.ORTANO2ADI:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for ADI")
            return False
        slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for Ortano ADI")
            return False
        oracle_pn = re.match(PART_NUMBERS_MATCH.ORTANO2ADI_ORC_PN_FMT, slot_pn)
        if oracle_pn:
            return True
        else:
            return False

    def mtp_is_nic_ortanoadi_ibm(self, slot):
        """
         Differentiate ortano by PN
         - 68-0028: Oracle version -> return True
         - any other -> return False with err msg
        """
        if self._nic_type_list[slot] != NIC_Type.ORTANO2ADIIBM:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for ADI IBM")
            return False
        slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for ADI IBM")
            return False
        ibm_pn = re.match(PART_NUMBERS_MATCH.ORTANO2ADI_IBM_PN_FMT, slot_pn)
        if ibm_pn:
            return True
        else:
            return False

    def mtp_nic_erase_board_config(self, slot):
        if not self._nic_ctrl_list[slot].nic_erase_board_config():
            self.cli_log_slot_err(slot, "Erase NIC Board Config failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Erase NIC Board Config")
        return True

    def mtp_nic_erase_board_config_ssh(self, slot):
        if not self._nic_ctrl_list[slot].nic_erase_board_config_ssh():
            self.cli_log_slot_err(slot, "Erase NIC Board Config failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Erase NIC Board Config")
        return True

    def mtp_nic_cpld_update_request(self, slot):
        if not self._nic_ctrl_list[slot].nic_cpld_update_request():
            if not self._nic_ctrl_list[slot].nic_check_status():
                self.cli_log_slot_err(slot, "Check NIC Update CPLD request failed")
                self.mtp_get_nic_err_msg(slot)
                return False
            else:
                return False

        self.cli_log_slot_inf(slot, "Need to Update CPLD")
        return True

    def mtp_mgmt_nic_console_access(self, slot):
        if not self._nic_ctrl_list[slot].nic_console_access():
            self.cli_log_slot_err(slot, "Get NIC Console Access failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Get NIC Console Access")
        return True

    def mtp_mgmt_set_board_config_cert(self, slot, cert_img, directory="/data/"):
        if not self._nic_ctrl_list[slot].nic_set_board_config_cert(cert_img, directory):
            self.cli_log_slot_err(slot, "Set NIC board config cert failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set NIC board config cert")
        return True

    def mtp_mgmt_nic_secboot_verify(self, slot):
        if not self._nic_ctrl_list[slot].nic_secboot_verify():
            self.cli_log_slot_err(slot, "NIC secure boot check failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "NIC secure boot check passed")
        return True

    def mtp_mgmt_nic_cfg_verify(self, slot):
        if not self._nic_ctrl_list[slot].nic_cfg_verify():
            self.cli_log_slot_err(slot, "NIC cfg compare failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "NIC cfg compare passed")
        return True

    def mtp_get_nic_sw_pn(self, slot):
        if self._nic_sw_pn_list[slot] is None:
            return ""
        return self._nic_sw_pn_list[slot]

    def mtp_set_nic_sw_pn(self, slot, sw_pn):
        self._nic_sw_pn_list[slot] = sw_pn

    def mtp_get_nic_type(self, slot):
        return self._nic_type_list[slot]

    def mtp_set_nic_type(self, slot, nic_type):
        """
         Don't use this function for MTP. Instead use mtp_init_nic_type().
         This is only for, for e.g. FST setup, which does not have `inventory` command.
         and for rework script which changes the type during runtime.
        """
        self.cli_log_slot_inf(slot, "Set TYPE to {:s}".format(nic_type))
        self._nic_type_list[slot] = nic_type
        if self._nic_ctrl_list[slot]:
            self._nic_ctrl_list[slot].nic_set_type(nic_type)

    def mtp_nic_type_valid(self, slot):
        nic_type = self._nic_type_list[slot]
        if nic_type in self._valid_type_list:
            return True
        else:
            self.cli_log_slot_err(slot, "'{:s}' Type not valid for this script folder".format(nic_type))
            return False

    def mtp_nic_pn_valid(self, slot):
        if self._nic_ctrl_list[slot] is None:
            self.cli_log_slot_err(slot, "NIC not initialized")
            return False
        else:
            pn = self._nic_ctrl_list[slot].nic_get_naples_pn()
            if pn is None:
                self.cli_log_slot_err(slot, "No PN detected")
                return False
            # search for this PN in lib/libsku_cfg.py
            for pn_regex in self._valid_pn_list:
                pn_match = re.match(pn_regex, pn)
                if pn_match:
                    return True
            # end of search

            self.cli_log_slot_err(slot, "'{:s}' PN not valid for this script folder".format(pn))
            return False

    @test_utils.semi_parallel_test_section
    def mtp_nic_list_type_test(self, slot):
        # same as mtp_nic_type_test but call on a nic_list instead of single slot
        return self.mtp_nic_type_test(slot)

    def mtp_nic_type_test(self, slot):
        type_check = self.mtp_nic_type_valid(slot)
        pn_check = self.mtp_nic_pn_valid(slot)
        return type_check & pn_check

    def mtp_get_nic_sn(self, slot):
        return self._nic_sn_list[slot]


    def mtp_set_nic_sn(self, slot, sn):
        self.cli_log_slot_inf(slot, "Set SN to {:s}".format(sn))
        self._nic_sn_list[slot] = sn


    def mtp_get_nic_scan_sn(self, slot):
        return self._nic_scan_sn_list[slot]


    def mtp_set_nic_scan_sn(self, slot, sn):
        self.cli_log_slot_inf(slot, "Set Scan SN to {:s}".format(sn))
        self._nic_scan_sn_list[slot] = sn
        self._nic_scan_prsnt_list[slot] = True


    def mtp_mgmt_set_nic_diag_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_diag_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with diag failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set NIC default diag boot")
        return True
        
    def mtp_mgmt_set_nic_mainfw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_mainfw_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with mainfw failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set NIC default mainfw boot")
        return True

    def mtp_mgmt_set_nic_extos_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_extos_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with diag failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set NIC default diag boot")
        return True

    def fst_set_mainfw_boot(self, slot):
        self.cli_log_slot_inf(slot, "Switch to mainfw")
        cmd = "/nic/tools/fwupdate -s mainfwa"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to switch to mainfw")
            return False
        return True

    def mtp_mgmt_nic_sw_shutdown(self, slot, software_pn):
        isCloud =  self.check_is_cloud_software_image(slot, software_pn)
        isRelC = True if software_pn in ("90-0013-0001", "90-0014-0001", "90-0002-0010", "90-0007-0003", "90-0019-0001", "90-0002-0011", "90-0007-0004") else False
        if not self._nic_ctrl_list[slot].nic_sw_shutdown(cloud=isCloud, isRelC=isRelC):
            self.cli_log_slot_err(slot, "Graceful shut down NIC failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_mgmt_nic_sw_cleanup_shutdown(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_cleanup_shutdown():
            self.cli_log_slot_err(slot, "Graceful clean up shut down NIC failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_mgmt_set_elba_uboot_env(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_elba_uboot_env(slot):
            self.cli_log_slot_err(slot, "Setup uboot env variables failed")
            return False
        return True

    def mtp_check_nic_status(self, slot):
        return self._nic_ctrl_list[slot].nic_check_status()

    def mtp_check_nic_missed_fa(self, slot):
        return self._nic_ctrl_list[slot].nic_missed_fa()

    def mtp_hide_nic_status(self, slot):
        if not self.mtp_check_nic_status(slot):
            self.cli_log_slot_inf(slot, "Masking NIC fail status")
        self._nic_status_before_hide_list[slot] = self._nic_ctrl_list[slot]._nic_status
        self.mtp_clear_nic_status(slot)

    def mtp_unhide_nic_status(self, slot):
        if self._nic_status_before_hide_list[slot] != NIC_Status.NIC_STA_OK:
            self.cli_log_slot_inf(slot, "Unmasking NIC fail status")
        self._nic_ctrl_list[slot].nic_set_status(self._nic_status_before_hide_list[slot])
        self._nic_status_before_hide_list[slot] = NIC_Status.NIC_STA_OK

    # log the diag test history
    def mtp_mgmt_diag_history_disp(self):
        cmd = MFG_DIAG_CMDS.MTP_DIAG_SHIST_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            return False

        return True


    # clear the diag test history
    def mtp_mgmt_diag_history_clear(self):
        cmd = MFG_DIAG_CMDS.MTP_DIAG_CHIST_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            return False

        return True


    def mtp_mgmt_pre_post_diag_check(self, intf, slot, vmarg=Voltage_Margin.normal):
        if intf == "NIC_JTAG":
            if self.mtp_check_nic_jtag(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_POWER":
            if self.mtp_mgmt_check_nic_pwr_status(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_MEM":
            if self.mtp_mgmt_test_nic_mem(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_STATUS":
            if self.mtp_check_nic_status(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_DIAG_BOOT":
            if self.mtp_nic_check_diag_boot(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_CPLD":
            if self.mtp_verify_nic_cpld(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_FPGA":
            if self.mtp_verify_nic_cpld(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_ALOM_CABLE":
            if self._swmtestmode[slot] == Swm_Test_Mode.SWMALOM or self._swmtestmode[slot] == Swm_Test_Mode.ALOM:
                if self.mtp_nic_naples25swm_alom_cable_signal_test(slot, 1):
                    return "SUCCESS"
                else:
                    return MTP_DIAG_Error.NIC_DIAG_FAIL
            else:
                return "SUCCESS"
        elif intf == "NIC_N25SWM_CPLD":
            if self._swmtestmode[slot] == Swm_Test_Mode.SWMALOM or self._swmtestmode[slot] == Swm_Test_Mode.SWM:
                if self.mtp_nic_naples25swm_cpld_spi_to_smb_reg_test(slot):
                    return "SUCCESS"
                else:
                    return MTP_DIAG_Error.NIC_DIAG_FAIL
            else:
                return "SUCCESS"
        elif intf == "NIC_OCP_SIGNALS":
            if self.mtp_nic_naples25ocp_signal_test(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_TYPE":
            if self.mtp_nic_type_test(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        else:
            self.cli_log_slot_err(slot, "Unknown pre diag check module")
            return MTP_DIAG_Error.NIC_DIAG_FAIL


    def mtp_nic_pcie_poll_enable(self, slot, enable=True):
        if enable:
            self.cli_log_slot_inf(slot, "Enable NIC PCIE Polling")
        else:
            self.cli_log_slot_inf(slot, "Disable NIC PCIE Polling")

        if not self._nic_ctrl_list[slot].nic_pcie_poll_enable(enable):
            if enable:
                self.cli_log_slot_err(slot, "Enable NIC PCIE Polling failed")
            else:
                self.cli_log_slot_err(slot, "Disable NIC PCIE Polling failed")
            return False

        return True

    def mtp_mgmt_set_nic_extdiag_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_extdiag_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with extdiag failed")
            return False

        self.cli_log_slot_inf(slot, "Set NIC default extdiag boot")
        return True

    def mtp_mgmt_run_test_mtp_para(self, test, nic_list, vmarg):
        nic_fail_list = list()
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return ["TIMEOUT", nic_list[:]]

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.MTP_PARA_TEST_SIG]

        n_vmarg = vmarg
        if vmarg in (Voltage_Margin.high, Voltage_Margin.low):
            partnumber = ""
            for nic_controller in  self._nic_ctrl_list:
                if nic_controller._pn:
                    partnumber = nic_controller._pn
                    break
            n_vmarg += libmfg_utils.pick_voltage_margin_percentage(partnumber)
            self.cli_log_inf("Vmargin is: {:s} After Apply Percentage, which Got Using Part Number: {:s}".format(n_vmarg, partnumber))

        if test == "PRBS_ETH":
            cmd = MFG_DIAG_CMDS.MTP_PARA_PRBS_ETH_TEST_FMT.format(nic_list_param, n_vmarg)
        elif test == "SNAKE_HBM":
            cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_HBM_FMT.format(nic_list_param, n_vmarg)
        elif test == "SNAKE_PCIE":
            cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_PCIE_FMT.format(nic_list_param, n_vmarg)
        elif test == "SNAKE_ELBA":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)

            if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
                self.cli_log_err("Incorrect test for this NIC TYPE")
                return ["FAIL", nic_list[:]]
            elif nic_type == NIC_Type.ORTANO2:
                if self.mtp_is_nic_ortano_oracle(slot):
                    cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_ORC_FMT.format(nic_list_param, n_vmarg)
                else:
                    cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_PEN_FMT.format(nic_list_param, n_vmarg)
            elif nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2ADICR):
                cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_ORC_FMT.format(nic_list_param, n_vmarg)
            elif nic_type in (NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICRS4):
                cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_PEN_FMT.format(nic_list_param, n_vmarg)
            elif nic_type == NIC_Type.LACONA32DELL or nic_type == NIC_Type.LACONA32:
                cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_LACONA_FMT.format(nic_list_param, n_vmarg)
            elif nic_type in GIGLIO_NIC_TYPE_LIST:
                cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_GIGLIO_FMT.format(nic_list_param, n_vmarg)
            else:
                cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_FMT.format(nic_list_param, n_vmarg)

            # 2C/4C = internal loopback
            if vmarg != Voltage_Margin.normal:
                cmd += " -int_lpbk"

        elif test == "ETH_PRBS":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)
            if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
                self.cli_log_err("Incorrect test for this NIC TYPE")
                return ["FAIL", nic_list[:]]
            else:
                if nic_type in ELBA_NIC_TYPE_LIST:
                    cmd = MFG_DIAG_CMDS.MTP_PARA_PRBS_ETH_ELBA_FMT.format(nic_list_param, n_vmarg)
                elif nic_type in GIGLIO_NIC_TYPE_LIST:
                    cmd = MFG_DIAG_CMDS.MTP_PARA_PRBS_ETH_GIGLIO_FMT.format(nic_list_param, n_vmarg)
                # 2C/4C = internal loopback
                if vmarg != Voltage_Margin.normal:
                    cmd += " -int_lpbk"
        elif test == "ARM_L1":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.POMONTEDELL:
                cmd = MFG_DIAG_CMDS.MTP_PARA_ARM_L1_ELBA_POMONTEDELL_FMT.format(nic_list_param, n_vmarg)
            elif nic_type in (NIC_Type.LACONA32, NIC_Type.LACONA32DELL):
                cmd = MFG_DIAG_CMDS.MTP_PARA_ARM_L1_ELBA_LACONA_FMT.format(nic_list_param, n_vmarg)
            elif nic_type in ARM_L1_MODE_HOD_1100 or (nic_type == NIC_Type.ORTANO2 and self.mtp_is_nic_ortano_microsoft(slot)):
                cmd = MFG_DIAG_CMDS.MTP_PARA_ARM_L1_ELBA_FMT.format(nic_list_param, n_vmarg, "hod_1100")
            else:
                cmd = MFG_DIAG_CMDS.MTP_PARA_ARM_L1_ELBA_FMT.format(nic_list_param, n_vmarg, "hod")
        elif test == "PCIE_PRBS":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)
            cmd = MFG_DIAG_CMDS.MTP_PARA_PCIE_PRBS_FMT.format(nic_list_param, n_vmarg, "PRBS31")
        elif test == "DDR_BIST":
            cmd = MFG_DIAG_CMDS.MTP_PARA_DDR_BIST_ELBA_FMT.format(nic_list_param, n_vmarg)
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return ["FAIL", nic_list[:]]

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_TEST_TIMEOUT):
            self.cli_log_err("Run MTP Parallel Test {:s} Failed".format(test))
            return ["TIMEOUT", nic_list[:]]
        ret = "SUCCESS"
        cmd_buf = self.mtp_get_cmd_buf()
        buf_before_sig = self.mtp_get_cmd_buf_before_sig()

        self.nic_semi_parallel_log(nic_list, buf_before_sig)

        match = re.findall(r"Slot (\d+) ?: +(\w+)", cmd_buf)

        rslt_list = [False] * MTP_Const.MTP_SLOT_NUM # fail any slots whose result is not captured
        for _slot, rslt in match:
            slot = int(_slot) - 1
            if (rslt == "PASS" or rslt == "PASSED"):
                rslt_list[slot] = True

        for slot in nic_list:
            if not rslt_list[slot]:
                if slot not in nic_fail_list:
                    nic_fail_list.append(slot)
                    ret = "FAIL"

        return [ret, nic_fail_list]

    def mtp_mgmt_run_test_mtp_para_with_oneline_summary(self, test, nic_list, vmarg):
        if not nic_list:
            return [True, nic_list[:]]

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return ["TIMEOUT", nic_list[:]]

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)

        n_vmarg = vmarg
        if vmarg in (Voltage_Margin.high, Voltage_Margin.low):
            partnumber = ""
            for nic_controller in  self._nic_ctrl_list:
                if nic_controller._pn:
                    partnumber = nic_controller._pn
                    break
            n_vmarg += libmfg_utils.pick_voltage_margin_percentage(partnumber)
            self.cli_log_inf("Vmargin is: {:s} After Apply Percentage, which Got Using Part Number: {:s}".format(n_vmarg, partnumber))

        if test == "RMII_LINKUP":
            cmd = MFG_DIAG_CMDS.MTP_NCSI_RMII_LINKUP_FMT.format(nic_list_param, n_vmarg)
            sig_list = ["rmii_linkup_test done"]
        elif test == "UART_LPBACK":
            cmd = MFG_DIAG_CMDS.MTP_NCSI_UART_LPBACK_FMT.format(nic_list_param, n_vmarg)
            sig_list = ["uart_loopback_test done"]
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return ["FAIL", nic_list[:]]

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_TEST_TIMEOUT):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return ["FAIL", nic_list[:]]

        self.nic_semi_parallel_log(nic_list, self.mtp_get_cmd_buf_before_sig())

        nic_fail_list = list()
        ret = "SUCCESS"
        if "failed;" in self.mtp_get_cmd_buf():
            match = re.search("failed slots: *([0-9,]+)", self.mtp_get_cmd_buf())
            if match:
                for slot_base_1 in libmfg_utils.expand_range_of_numbers(match.group(1), range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot_base_1 - 1
                    if slot not in nic_fail_list:
                        nic_fail_list.append(slot)
                        ret = "FAIL"

        return [ret, nic_fail_list]

    def mtp_mgmt_get_test_result(self, cmd, test):
        if not self.mtp_mgmt_exec_cmd(cmd):
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT

        # Test    Error code, SUCCESS means pass
        match = re.findall(r"{:s} +([A-Za-z0-9_]+)".format(test), self.mtp_get_cmd_buf())
        if match:
            return match[0]
        else:
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT


    def mtp_mgmt_get_test_result_para(self, slot, cmd, test):
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.cli_log_slot_err_lock(slot, "Execute {:s} failed".format(cmd))
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT

        # Test    Error code, SUCCESS means pass
        match = re.findall(r"{:s} +([A-Za-z0-9_]+)".format(test), self.mtp_get_nic_cmd_buf(slot))
        if match:
            return match[0]
        else:
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT


    def mtp_run_diag_test_seq(self, slot, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None):
        # init command
        if init_cmd:
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(init_cmd):
                err_msg = self.mtp_get_nic_cmd_buf(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        if not self._nic_ctrl_list[slot].mtp_exec_cmd(diag_cmd, timeout=MTP_Const.DIAG_SEQ_TEST_TIMEOUT):
            err_msg = self.mtp_get_nic_cmd_buf(slot)
            return [MTP_DIAG_Error.NIC_DIAG_TIMEOUT, [err_msg]]

        # diag test error ouput
        err_msg_list = list()
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        if MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG in cmd_buf:
            for line in cmd_buf.split('\n'):
                if MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG in line:
                    err_msg = line.replace('\r', '')
                    err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG):]
                    err_msg_list.append(err_msg)

        # post command
        if post_cmd:
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(post_cmd):
                err_msg = self.mtp_get_nic_cmd_buf(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # for zmq, get result at the test end instead of sresult.
        # zmq_l1_result_re = r"MTP1 +ASIC +L1 +(\w+)"
        # match = re.findall(zmq_l1_result_re, cmd_buf)
        # if match:
        #     ret = match[0]
        # else:
        #     ret = "TIMEOUT"
        ret = self.mtp_mgmt_get_test_result_para(slot, rslt_cmd, test)
        if test == "L1" and ret == "TIMEOUT":
            self.mtp_single_j2c_lock()
            self.mtp_mgmt_jtag_rst()
            self.mtp_single_j2c_unlock()

        return [ret, err_msg_list]


    def mtp_mgmt_jtag_rst(self):
        self.cli_log_inf("Reset the MTP JTAG Interface", level = 0)
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        cmd = MFG_DIAG_CMDS.MTP_DSP_STOP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        cmd = "cleantcl.sh"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        cmd = MFG_DIAG_CMDS.MTP_DSP_START_FMT
        sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        self.cli_log_inf("Reset the MTP JTAG Interface complete", level = 0)
        return True

    def mtp_nic_board_config(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            if nic_type == NIC_Type.ORTANO2:
                if self.mtp_is_nic_ortano_oracle(slot):
                    preset_config = "5"
                else:
                    preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2ADI:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2ADIIBM:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2ADIMSFT:
                preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2INTERP:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2SOLO:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2SOLOORCTHS:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2SOLOMSFT:
                preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2SOLOS4:
                preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2ADICR:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2ADICRMSFT:
                preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2ADICRS4:
                preset_config = "8"
            elif nic_type == NIC_Type.POMONTEDELL:
                preset_config = "1"
            elif nic_type in (NIC_Type.LACONA32, NIC_Type.LACONA32DELL):
                preset_config = "18"
            elif nic_type in (NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5):
                preset_config = "8"
            else:
                self.cli_log_slot_err_lock(slot, "Board config not supported on this NIC")
                return False

        else:
            self.cli_log_slot_err_lock(slot, "Board config not supported on this NIC")
            return False

        if not self._nic_ctrl_list[slot].nic_set_board_config(preset_config):
            self.cli_log_slot_err_lock(slot, "Set board config failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_nic_assign_board_id(self, slot, partNumber=None):
        """
        Assign board id to provided slot, according retrieved CPLD ID and passed in part number.
        """

        if partNumber is None:
            self.cli_log_slot_err_lock(slot, "Please Provide Part Number")
            return False
        if not isinstance(partNumber, str):
            self.cli_log_slot_err_lock(slot, "Please Specify Part Number with String Format")
            return False

        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Failed to retrieve CPLD ID info")
            return False
        cpldId = nic_cpld_info[2]
        partNumberIn6Digits = partNumber[0:7] if "-" in partNumber[0:6] else partNumber[0:6]
        boardId = PN_AND_CPLD_TO_BOARDID.get((partNumberIn6Digits, cpldId), None)
        if not boardId:
            self.cli_log_slot_err_lock(slot, "Failed find board ID for PN {:s} and CPLD {:s}".format(partNumber, cpldId))
            return False

        if not self._nic_ctrl_list[slot].nic_assign_board_id(boardId):
            self.cli_log_slot_err_lock(slot, "Assign Board ID Failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_mgmt_dump_avs_info(self, slot, buf):
        self.cli_log_slot_inf(slot, "AVS Set Result Dump:")
        # find any error
        avs_passed_flag = re.findall(r"SET AVS PASSED", buf)
        if not avs_passed_flag:
            self.cli_log_slot_inf(slot, buf, level=0)
            return False

        # find the die id
        die_id_match = re.findall(r"(ASIC_DIE_ID: +0x[0-9a-fA-F]+)", buf)
        if die_id_match:
            self.cli_log_slot_inf(slot, die_id_match[0], level=1)
        osc_count_id_match = re.findall(r"(osc_count_id: +[0-9]+)", buf)
        if osc_count_id_match:
            self.cli_log_slot_inf(slot, osc_count_id_match[0], level=1)
        vdd_core_offset_match = re.findall(r"(vdd_core_offset: +[0-9a-fA-F]+)", buf)
        if vdd_core_offset_match:
            self.cli_log_slot_inf(slot, vdd_core_offset_match[0], level=1)
        vdd_arm_offset_match = re.findall(r"(vdd_arm_offset: +[0-9a-fA-F]+)", buf)
        if vdd_arm_offset_match:
            self.cli_log_slot_inf(slot, vdd_arm_offset_match[0], level=1)
        return True


    def mtp_mgmt_set_nic_avs(self, slot):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            self.mtp_dump_nic_err_msg(slot)
            return False

        nic_type = self.mtp_get_nic_type(slot)
        sn = self.mtp_get_nic_sn(slot)

        vdd_avs_cmd, arm_avs_cmd = None, None

        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip AVS for Proto NIC")
            return True
        elif nic_type == NIC_Type.NAPLES100:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES100_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES100_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES100IBM:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES100IBM_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES100IBM_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES100HPE:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES100HPE_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES100HPE_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES100DELL:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES100DELL_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES100DELL_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.VOMERO:
            vdd_avs_cmd = MFG_DIAG_CMDS.VOMERO_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.VOMERO_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.VOMERO2:
            vdd_avs_cmd = MFG_DIAG_CMDS.VOMERO2_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.VOMERO2_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25SWM:  
            #NAPLES25SWM uses same setting as Naples25
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25SWMDELL:  
            #NAPLES25SWM uses same setting as Naples25
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25OCP:  
            #NAPLES25OCP uses same setting as Naples25
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25SWM833:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25SWM833_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25SWM833_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
            """
             Separate freq by PN:
             - For 68-0015 (Oracle) use 1033
             - For 68-0021 (Pensando) use 1100
            """
            if self.mtp_is_nic_ortano_oracle(slot):
                vdd_avs_cmd = MFG_DIAG_CMDS.ORTANO_ORC_AVS_SET_FMT.format(sn, slot+1)
            else:
                vdd_avs_cmd = MFG_DIAG_CMDS.ORTANO_PEN_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2INTERP:
            vdd_avs_cmd = MFG_DIAG_CMDS.ORTANO_ORC_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.POMONTEDELL:
            vdd_avs_cmd = MFG_DIAG_CMDS.POMONTEDELL_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.LACONA32DELL:
            vdd_avs_cmd = MFG_DIAG_CMDS.LACONA32DELL_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.LACONA32:
            vdd_avs_cmd = MFG_DIAG_CMDS.LACONA32_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2SOLO:
            vdd_avs_cmd = MFG_DIAG_CMDS.ORTANO_ORC_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2SOLOORCTHS:
            vdd_avs_cmd = MFG_DIAG_CMDS.ORTANO_ORC_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2SOLOMSFT:
            vdd_avs_cmd = MFG_DIAG_CMDS.ORTANO_PEN_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2SOLOS4:
            vdd_avs_cmd = MFG_DIAG_CMDS.ORTANO_PEN_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.GINESTRA_D4:
            vdd_avs_cmd = MFG_DIAG_CMDS.GINESTRA_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.GINESTRA_D5:
            vdd_avs_cmd = MFG_DIAG_CMDS.GINESTRA_AVS_SET_FMT.format(sn, slot+1)
        else:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
            return False

        if vdd_avs_cmd:
            self.mtp_mgmt_set_nic_avs_pre(slot)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(vdd_avs_cmd, timeout=MTP_Const.NIC_AVS_SET_DELAY):
                self.cli_log_slot_err(slot, "Timed out: Failed to execute command {:s}".format(vdd_avs_cmd))
                self.mtp_dump_nic_err_msg(slot)
                self.mtp_mgmt_set_nic_avs_post(slot)
                return False
            if not self.mtp_mgmt_dump_avs_info(slot, self.mtp_get_nic_cmd_buf(slot)):
                self.cli_log_slot_err(slot, "SET VDD AVS FAILED")
                return False
        if arm_avs_cmd:
            self.mtp_mgmt_set_nic_avs_pre(slot)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(arm_avs_cmd, timeout=MTP_Const.NIC_AVS_SET_DELAY):
                self.cli_log_slot_err(slot, "Timed out: Failed to execute command {:s}".format(arm_avs_cmd))
                self.mtp_dump_nic_err_msg(slot)
                self.mtp_mgmt_set_nic_avs_post(slot)
                return False
            if not self.mtp_mgmt_dump_avs_info(slot, self.mtp_get_nic_cmd_buf(slot)):
                self.cli_log_slot_err(slot, "SET ARM AVS FAILED")
                return False
        self.mtp_mgmt_set_nic_avs_post(slot)

        return True

    def mtp_mgmt_set_nic_avs_pre(self, slot):
        self._nic_ctrl_list[slot].mtp_exec_cmd(MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT, timeout=MTP_Const.OS_CMD_DELAY)

    def mtp_mgmt_set_nic_avs_post(self, slot):
        self.mtp_nic_send_ctrl_c(slot) # kill any hung tclsh in this same session
        cmd = MFG_DIAG_CMDS.NIC_AVS_POST_FMT.format(slot+1)
        self._nic_ctrl_list[slot].mtp_exec_cmd(cmd)

        cmd_buf = self.mtp_get_nic_cmd_buf(slot)

        # clear reg 0x50 after reading
        reg_addr = 0x50
        write_data = 0
        cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(slot+1) + " ;" + MFG_DIAG_CMDS.MTP_SMB_WR_CPLD_FMT.format(reg_addr, write_data, slot+1)
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.mtp_dump_nic_err_msg(slot)
            return False
        cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(slot+1) + " ;" + MFG_DIAG_CMDS.MTP_SMB_RD_CPLD_FMT.format(reg_addr, slot+1)
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_nic_fix_vrm(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.ORTANO2:
            if self.mtp_is_nic_ortano_microsoft(slot):
                if not self._nic_ctrl_list[slot].nic_fix_vrm_oc():
                    self.cli_log_slot_err_lock(slot, "{:s} failed".format(MFG_DIAG_CMDS.ORTANO2_VRM_FIX_FMT))
                    self.mtp_dump_nic_err_msg(slot)
                    return False
            else:
                if not self._nic_ctrl_list[slot].nic_fix_vrm():
                    self.cli_log_slot_err_lock(slot, "{:s} failed".format(MFG_DIAG_CMDS.ORTANO2_VRM_FIX_FMT))
                    self.mtp_dump_nic_err_msg(slot)
                    return False
        elif nic_type in (NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4):
            if not self._nic_ctrl_list[slot].nic_fix_vrm():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(MFG_DIAG_CMDS.ORTANO2_VRM_FIX_FMT))
                self.mtp_dump_nic_err_msg(slot)
                return False
        return True

    def mtp_nic_naples25swm_alom_cable_signal_test(self, slot, highpowertest):
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_alom_cable_signal_test(errlist, highpowertest)
        if rc == False:
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        return rc

    def mtp_nic_naples25swm_high_power_mode_test(self, slot):
        self.cli_log_slot_inf(slot, "Starting Naples25 SWM High Power On Test")
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_high_power_mode_test(errlist)
        if rc == False:
            self.cli_log_slot_err(slot, "NIC NAPLES25SWM HIGH POWER MODE TEST FAILED")
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        else:
            self.cli_log_slot_inf(slot, "NIC NAPLES25SWM HIGH POWER MODE TEST PASSED")
        return rc

    def mtp_nic_naples25swm_low_power_mode_test(self, slot):
        self.cli_log_slot_inf(slot, "Starting Naples25 SWM Low Power On Test")
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_low_power_mode_test(errlist)
        if rc == False:
            self.cli_log_slot_err(slot, "NIC NAPLES25SWM LOW POWER MODE TEST FAILED")
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        else:
            self.cli_log_slot_inf(slot, "NIC NAPLES25SWM LOW POWER MODE TEST PASSED")
        return rc

    def mtp_nic_naples25swm_cpld_spi_to_smb_reg_test(self, slot):
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_cpld_reg_test(errlist)
        if rc == False:
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        return rc

    def mtp_nic_naples25ocp_signal_test(self, slot):
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25ocp_signal_test(errlist)
        if rc == False:
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        return rc

    def mtp_nic_naples25swm_mgmt_port_test(self, slot):
        rc = self._nic_ctrl_list[slot].nic_naples25swm_mgmt_port_test(slot)

    def mtp_mgmt_check_cpld_debug_bits(self, slot):
        """
            Dump registers 0xa, 0x12, 0x24
        """
        for reg_addr in [0xa, 0x12, 0x24]:
            cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(slot+1) + " ;" + MFG_DIAG_CMDS.MTP_SMB_RD_CPLD_FMT.format(reg_addr, slot+1)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                # try again one more time
                time.sleep(1)
                if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    continue

    def mtp_run_asic_l1_bash(self, slot=None, sn=None, mode=None, vmarg=Voltage_Margin.normal):
        """
        cd ~diag/scripts/asic/
        ./run_l1.test -sn <sn> -slot <slot> -m <mode> -v <vmarg>
        """
        rs = False

        nic_type = self.mtp_get_nic_type(slot)

        # 0 = skip l1_ddr_bist; 1 = default
        skip_ddr_bist = "1"

        if nic_type in DDR_HARCODED_TRAINING_NIC_LIST:
            ddr_hc_training = "1"
        else:
            ddr_hc_training = "0"

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            self.cli_log_slot_err(slot, "Command {:s} failed")
            rs = False

        cmd = MFG_DIAG_CMDS.NIC_RUN_ASIC_L1_FMT.format(sn, slot+1, mode, vmarg, skip_ddr_bist, ddr_hc_training)
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd, timeout=MTP_Const.MTP_PARA_ASIC_L1_TEST_TIMEOUT):
            rs = False
            # kill the process in case it's hung/timed out
            # ctrl-c doesnt work
            # needs to be killed from separate session
            if not self.mtp_mgmt_exec_cmd_para(slot, "## killall run_l1.sh"): # notify in log
                pass
            if not self.mtp_mgmt_exec_cmd("killall run_l1.sh"): # use mtp session to kill it
                pass

        cmd_buf = self.mtp_get_nic_cmd_buf(slot)

        if MFG_DIAG_SIG.NIC_PARA_ASIC_L1_OK_SIG in cmd_buf:
            rs = True

        return rs

    def mtp_reset_hub(self, slot=None):
        """
        cpldutil -cpld-wr -addr=0x2 -data=0xf
        cpldutil -cpld-wr -addr=0x2 -data=0x0
        """
        self.mtp_nic_lock()

        # on mtp_diag.log
        if slot is None:
            ts = libmfg_utils.timestamp_snapshot()
            ts_record_cmd = "#######= RESET I2C HUB =#######"
            self.log_mtp_file(ts_record_cmd)

            cmd = MFG_DIAG_CMDS.MTP_CPLD_WRITE_FMT.format(0x2, 0xf)
            self.mtp_mgmt_exec_cmd(cmd)

            cmd = MFG_DIAG_CMDS.MTP_CPLD_READ_FMT.format(0x2)
            self.mtp_mgmt_exec_cmd(cmd)

            cmd = MFG_DIAG_CMDS.MTP_CPLD_WRITE_FMT.format(0x2, 0x0)
            self.mtp_mgmt_exec_cmd(cmd)

            cmd = MFG_DIAG_CMDS.MTP_CPLD_READ_FMT.format(0x2)
            self.mtp_mgmt_exec_cmd(cmd)

        # on mtp_NIC*_diag.log
        else:
            ts = libmfg_utils.timestamp_snapshot()
            ts_record_cmd = "#######= RESET I2C HUB =#######"
            self.log_nic_file(slot, ts_record_cmd)

            cmd = MFG_DIAG_CMDS.MTP_CPLD_WRITE_FMT.format(0x2, 0xf)
            self.mtp_mgmt_exec_cmd_para(slot, cmd)

            cmd = MFG_DIAG_CMDS.MTP_CPLD_READ_FMT.format(0x2)
            self.mtp_mgmt_exec_cmd_para(slot, cmd)

            cmd = MFG_DIAG_CMDS.MTP_CPLD_WRITE_FMT.format(0x2, 0x0)
            self.mtp_mgmt_exec_cmd_para(slot, cmd)

            cmd = MFG_DIAG_CMDS.MTP_CPLD_READ_FMT.format(0x2)
            self.mtp_mgmt_exec_cmd_para(slot, cmd)

        self.mtp_nic_unlock()
        return True


    def mtp_nic_console_lock(self):
        self._nic_console_lock.acquire()

    def mtp_nic_console_unlock(self):
        self._nic_console_lock.release()

    def mtp_single_j2c_lock(self):
        self._j2c_lock.acquire()

    def mtp_single_j2c_unlock(self):
        self._j2c_lock.release()

    def mtp_turbo_j2c_lock(self, slot):
        self._turbo_j2c_lock[slot].acquire()

    def mtp_turbo_j2c_unlock(self, slot):
        self._turbo_j2c_lock[slot].release()

    def mtp_nic_lock(self):
        self.mtp_single_j2c_lock()
        self.mtp_nic_console_lock()

    def mtp_nic_unlock(self):
        self.mtp_single_j2c_unlock()
        self.mtp_nic_console_unlock()


    def mtp_run_diag_test_para(self, slot, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT):
        # init command
        if init_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, init_cmd):
                err_msg = self.mtp_get_nic_err_msg(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # run diag test
        if not self.mtp_mgmt_exec_cmd_para(slot, diag_cmd, timeout=timeout):
            err_msg = self.mtp_get_nic_err_msg(slot)
            return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # diag test error ouput
        err_msg_list = list()
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        if MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG in cmd_buf:
            for line in cmd_buf.split('\n'):
                if MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG in line:
                    err_msg = line.replace('\r', '')
                    err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG):]
                    err_msg_list.append(err_msg)

        # post command
        if post_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, post_cmd):
                err_msg = self.mtp_get_nic_err_msg(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        ret = self.mtp_mgmt_get_test_result_para(slot, rslt_cmd, test)
        return [ret, err_msg_list]


    def mtp_barcode_scan(self, present_check=True, swmtestmode=Swm_Test_Mode.SWMALOM, no_slot=False, is_fst_test=False):
        mtp_scan_rslt = dict()
        mtp_ts_snapshot = libmfg_utils.get_timestamp()
        mtp_scan_rslt["MTP_ID"] = self._id
        mtp_scan_rslt["MTP_TS"] = mtp_ts_snapshot
        valid_nic_key_list = list()

        unscanned_nic_key_list = list()
        scan_nic_key_list = list()
        scan_sn_list = list()
        scan_mac_list = list()
        scan_atom_sn_list = list()
        scan_rot_sn_list = list()
        slot_num = 1

        # build all valid nic key list
        for slot in range(self._slots):
            key = libmfg_utils.nic_key(slot)
            valid_nic_key_list.append(key)
            if present_check and self._nic_prsnt_list[slot]:
                unscanned_nic_key_list.append(key)

        while True:
            if len(scan_nic_key_list) == self._slots:
                print("\033[1;93m")
                libmfg_utils.cli_log_inf(self._filep, "!!! NO More Available Slot, Please Scan STOP !!!")
                print("\033[0m")

            if present_check:
                unscanned_nic_list_cli_str = ", ".join(unscanned_nic_key_list)
                usr_prompt = "\nUnscanned NIC list [{:s}]\nPlease Scan NIC ID Barcode:".format(unscanned_nic_list_cli_str)
            else:
                usr_prompt = "\nPlease Scan NIC ID Barcode:"
            nic_scan_rslt = dict()
            if not no_slot:
                raw_scan = raw_input(usr_prompt)

            if raw_scan == "STOP":
                if present_check and len(unscanned_nic_key_list) != 0:
                    self.cli_log_err("{:s} have not scanned yet".format(unscanned_nic_list_cli_str), level=0)
                    continue
                else:
                    break
            elif no_slot:
                key = "NIC-{:>02d}".format(slot_num)
                slot_num =+ 1
                scan_nic_key_list.append(key)
                unscanned_nic_key_list.remove(key)
            elif raw_scan in scan_nic_key_list:
                self.cli_log_err("NIC ID Barcode: {:s} is double scanned, please restart the scan process\n".format(raw_scan), level=0)
                return None
            else:
                key = raw_scan
                # basic sanity check
                if present_check:
                    if key not in unscanned_nic_key_list:
                        self.cli_log_err("Invalid NIC ID: {:s}".format(key), level=0)
                        continue
                    else:
                        scan_nic_key_list.append(key)
                        unscanned_nic_key_list.remove(key)
                else:
                    if key not in valid_nic_key_list:
                        self.cli_log_err("Invalid NIC ID: {:s}".format(key), level=0)
                        continue
                    else:
                        scan_nic_key_list.append(key)

            #Scan SN loop
            sn = "0"
            mac = "000000000000"
            pn = "0"
            if swmtestmode != Swm_Test_Mode.ALOM:
                sn_scanned = False
                mac_scanned = False
                pn_scanned = False
                rot_scanned = False
                while not sn_scanned:
                    usr_prompt = "Please Scan {:s} Serial Number Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    if raw_scan == "STOP":
                        break
                    if libmfg_utils.dell_ppid_validate(raw_scan):
                        # Dell PPID
                        sn = libmfg_utils.extract_sn_from_dell_ppid(raw_scan)
                        pn = libmfg_utils.extract_pn_from_dell_ppid(raw_scan)
                        pn_scanned = True
                    else:
                        sn = libmfg_utils.serial_number_validate(raw_scan)
                    if not sn:
                        self.cli_log_err("Invalid NIC Serial Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                        #return None
                    elif sn in scan_sn_list:
                        self.cli_log_err("NIC Serial Number: {:s} is double scanned, please restart the scan process\n".format(sn), level=0)
                        #return None
                    else:
                        scan_sn_list.append(sn)
                        sn_scanned = True

                    if pn_scanned and not pn:
                        pn_scanned = False

                #Scan Mac Loop
                while not mac_scanned and sn_scanned:
                    usr_prompt = "Please scan {:s} MAC Address Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    mac = libmfg_utils.mac_address_validate(raw_scan)
                    if not mac:
                        self.cli_log_err("Invalid NIC MAC Address: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                        #return None
                    elif mac in scan_mac_list:
                        mac_ui = libmfg_utils.mac_address_format(mac)
                        self.cli_log_err("NIC MAC Address: {:s} is double scanned, please restart the scan process\n".format(mac_ui), level=0)
                        #return None
                    else:
                        scan_mac_list.append(mac)
                        mac_scanned = True

                #Scan PN Loop
                while not pn_scanned:
                    usr_prompt = "Please scan {:s} Part Number Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    pn = libmfg_utils.part_number_validate(raw_scan)
                    if not pn:
                        self.cli_log_err("Invalid NIC Part Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                        #return None
                    else:
                        pn_scanned = True

                #Scan ROT cable if FST Station
                if is_fst_test:
                    if libmfg_utils.part_number_match_rot_require_list(pn):
                        while not rot_scanned:
                            usr_prompt = "Please Scan {:s} ROT Cable Barcode:".format(key)
                            rot_sn = raw_input(usr_prompt).strip()
                            if not rot_sn:
                                continue
                            if not libmfg_utils.rot_cable_serial_number_validate(rot_sn):
                                self.cli_log_err("Invalid ROT Cable SN: {:s}, please re-scan\n".format(rot_sn), level=0)
                            elif rot_sn in scan_rot_sn_list:
                                self.cli_log_err("ROT Cable: {:s} has already scanned, please re-scan\n".format(rot_sn), level=0)
                            else:
                                scan_rot_sn_list.append(rot_sn)
                                rot_scanned = True
                        nic_scan_rslt["ROTSN"] = rot_sn
                    else:
                        print("\033[1;92m")
                        libmfg_utils.cli_log_inf(self._filep, "!!! NO NEED ROT CABLE FOR THIS CARD TYPE !!!")
                        print("\033[0m")

                #Scan ALOM SN Loop
                alom_sn = None
                alom_pn = None


            if swmtestmode == Swm_Test_Mode.ALOM:  #if only scanning Alom we need to manually put in the SWM part number
                pn="000000-000"

            if pn == '000000-000':
                while True:
                    usr_prompt = "Please Scan {:s} ALOM Serial Number Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    alom_sn = libmfg_utils.serial_number_validate(raw_scan)
                    if not alom_sn:
                        self.cli_log_err("Invalid ALOM Serial Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                    #return None
                    elif alom_sn in scan_atom_sn_list:
                        self.cli_log_err("ALOM Serial Number: {:s} is double scanned, please restart the scan process\n".format(sn), level=0)
                    #return None
                    else:
                        scan_atom_sn_list.append(alom_sn)
                        break
                #Scan ALOM PN Loop
                
                while True:
                    usr_prompt = "Please scan {:s} ALOM Part Number Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    alom_pn = libmfg_utils.part_number_validate(raw_scan)
                    if not alom_pn:
                        self.cli_log_err("Invalid ALOM Part Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                    #return None
                    else:
                        break

            nic_scan_rslt["VALID"] = True
            nic_scan_rslt["SN"] = sn
            nic_scan_rslt["MAC"] = mac
            nic_scan_rslt["PN"] = pn
            nic_scan_rslt["TS"] = libmfg_utils.get_fru_date()
            if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
                nic_scan_rslt["SN_ALOM"] = alom_sn
                nic_scan_rslt["PN_ALOM"] = alom_pn
            mtp_scan_rslt[key] = nic_scan_rslt

        nic_empty_list = list(set(valid_nic_key_list).difference(set(scan_nic_key_list)))
        for key in nic_empty_list:
            nic_scan_rslt = dict()
            nic_scan_rslt["VALID"] = False
            mtp_scan_rslt[key] = nic_scan_rslt

        return mtp_scan_rslt

    def mtp_screen_barcode_scan(self):
        mtp_scan_rslt = dict()
        mtp_ts_snapshot = libmfg_utils.get_timestamp()
        mtp_scan_rslt["MTP_ID"] = self._id
        mtp_scan_rslt["MTP_TS"] = mtp_ts_snapshot
        mtp_scan_rslt["VALID"] = False
        scan_sn_list = list()

        sn = ""
        sn_scanned = False
        while not sn_scanned:
            usr_prompt = "Please Scan {:s} Serial Number Barcode:".format(self._id)
            raw_scan = raw_input(usr_prompt)
            if raw_scan == "STOP":
                break
            sn = libmfg_utils.serial_number_validate(raw_scan)

            if not sn:
                self.cli_log_err("Invalid MTP Serial Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                #return None
            elif sn in scan_sn_list:
                self.cli_log_err("MTP Serial Number: {:s} is double scanned, please restart the scan process\n".format(sn), level=0)
                #return None
            else:
                scan_sn_list.append(sn)
                sn_scanned = True
                mtp_scan_rslt["VALID"] = True
        
        mtp_scan_rslt["MTP_SN"] = sn

        return mtp_scan_rslt


    # generate the local barcode config file
    def gen_barcode_config_file(self, file_p, scan_rslt, swmtestmode=Swm_Test_Mode.ALOM):
        config_lines = [str(scan_rslt["MTP_ID"]) + ":"]
        tmp = "    TS: " +  scan_rslt["MTP_TS"]
        config_lines.append(tmp)
        for slot in range(self._slots):
            key = libmfg_utils.nic_key(slot)
            tmp = "    " + key + ":"
            config_lines.append(tmp)

            if scan_rslt[key]["VALID"]:
                tmp = "        VALID: \"Yes\""
                config_lines.append(tmp)
                tmp = "        SN: \"" + scan_rslt[key]["SN"] + "\""
                config_lines.append(tmp)
                tmp = "        MAC: \"" + scan_rslt[key]["MAC"] + "\""
                config_lines.append(tmp)
                tmp = "        PN: \"" + scan_rslt[key]["PN"] + "\""
                config_lines.append(tmp)
                tmp = "        TS: \"" + scan_rslt[key]["TS"] + "\""
                config_lines.append(tmp)
                pn = scan_rslt[key]["PN"]
                if pn == '000000-000':
                    tmp = "        SN_ALOM: \"" + scan_rslt[key]["SN_ALOM"] + "\""
                    config_lines.append(tmp)
                    tmp = "        PN_ALOM: \"" + scan_rslt[key]["PN_ALOM"] + "\""
                    config_lines.append(tmp)
                rot_sn = scan_rslt[key].get("ROTSN", "")
                if rot_sn:
                    tmp = '        ROTSN: "' + rot_sn + '"'
                    config_lines.append(tmp)
            else:
                tmp = "        VALID: \"No\""
                config_lines.append(tmp)

        for line in config_lines:
            file_p.write(line + "\n")

    def mtp_nic_mvl_acc_test(self, slot):
        test = "ACC"

        retval = ""
        err_msg_list = list()
        if self._nic_ctrl_list[slot].nic_mvl_acc_test():
            retval = "SUCCESS"
        else:
            retval = "FAIL"
        err_msg_list.append(self.mtp_get_nic_err_msg(slot))
        err_msg_list.append(self.mtp_get_nic_cmd_buf(slot))

        return retval, err_msg_list

    def mtp_nic_mvl_stub_test(self, slot, loopback=True):
        test = "STUB"
        if not loopback:
            self.cli_log_slot_inf(slot, "Internal loopback")

        retval = ""
        err_msg_list = list()
        if self._nic_ctrl_list[slot].nic_mvl_stub_test(loopback):
            retval = "SUCCESS"
        else:
            retval = "FAIL"
        err_msg_list.append(self.mtp_get_nic_err_msg(slot))
        err_msg_list.append(self.mtp_get_nic_cmd_buf(slot))

        return retval, err_msg_list

    def mtp_nic_mvl_link_test(self, slot):
        test = "LINK"

        retval = ""
        err_msg_list = list()
        if self._nic_ctrl_list[slot].nic_mvl_link_test():
            retval = "SUCCESS"
        else:
            retval = "FAIL"
        err_msg_list.append(self.mtp_get_nic_err_msg(slot))
        err_msg_list.append(self.mtp_get_nic_cmd_buf(slot))

        return retval, err_msg_list

    def mtp_nic_phy_xcvr_link_test(self, slot):
        test = "PHY"

        retval = ""
        err_msg_list = list()
        if self._nic_ctrl_list[slot].nic_phy_xcvr_link_test():
            retval = "SUCCESS"
        else:
            retval = "FAIL"
        err_msg_list.append(self.mtp_get_nic_err_msg(slot))
        err_msg_list.append(self.mtp_get_nic_cmd_buf(slot))

        return retval, err_msg_list

    def mtp_nic_phy_xcvr_test(self, slot):
        test = "PHY"

        retval = ""
        err_msg_list = list()
        if self._nic_ctrl_list[slot].nic_phy_xcvr_test():
            retval = "SUCCESS"
        else:
            retval = "FAIL"
        err_msg_list.append(self.mtp_get_nic_err_msg(slot))
        err_msg_list.append(self.mtp_get_nic_cmd_buf(slot))

        return retval, err_msg_list

    def mtp_nic_edma_test(self, slot):
        test = "EDMA"

        retval = ""
        err_msg_list = list()
        if self._nic_ctrl_list[slot].nic_edma_test():
            retval = "SUCCESS"
        else:
            retval = "FAIL"
        err_msg_list.append(self.mtp_get_nic_err_msg(slot))
        err_msg_list.append(self.mtp_get_nic_cmd_buf(slot))

        return retval, err_msg_list

    def mtp_check_nic_rebooted(self, slot):
        self.cli_log_slot_inf(slot, "Init new NIC connection")
        ret = self.mtp_nic_para_session_init(slot_list=[slot], fpo=False)
        if not ret:
            self.cli_log_err("Init NIC Connection Failed", level = 0)

        self.cli_log_slot_inf(slot, "Check if NIC rebooted")
        if not self._nic_ctrl_list[slot].nic_check_rebooted():
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        self.cli_log_slot_inf(slot, "No sign of reboot")
        return True

    def mtp_nic_read_temp(self, slot):
        """
         Read board and die temp via j2c
         WARNING: this does an ARM reset, so need a powercycle to bring NIC back to fresh slate
        """
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
            return True
        if not self._nic_ctrl_list[slot].read_nic_temp():
            self.cli_log_slot_err(slot, "Unable to read NIC temperature")
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT)
            return False

        cmd_buf = self.mtp_get_nic_cmd_buf(slot)

        # [21-08-03 19:00:29] MSG :: ASIC           core_temp(C)   core_volt(V)   brd_temp(C)    r_die_temp(C)  VDD_VOUT(V)    ARM_VOUT(V)    PIN(W)
        # [21-08-03 19:00:29] MSG ::                71.80          0.73           45             83             0.730          0.860          60.0
        found_column_heading = False
        board_temp = "0"
        die_temp = "0"
        for line in cmd_buf.split("\r\n"):
            match = re.search(r"MSG ::.*core_temp.*brd_temp.*die_temp", line)
            if match:
                found_column_heading = True
                continue
            if found_column_heading:
                match = re.search(r"MSG :: +(-?\d+\.?\d+) + (-?\d+\.?\d+) + (-?\d+\.?\d+) + (-?\d+\.?\d+)", line)
                if match:
                    board_temp = match.group(3)
                    die_temp = match.group(4)
                else:
                    self.cli_log_slot_err(slot, "Missing readings for NIC temperature")
                    self.mtp_dump_nic_err_msg(slot)
                break

        self.cli_log_slot_inf(slot, "NIC board temperature = {:s}C".format(board_temp))
        self.cli_log_slot_inf(slot, "NIC die temperature   = {:s}C".format(die_temp))
        self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT)

        ##### Use this dump to check ECC errors as well
        ecc_regs = re.findall(r"Reg 0x(.*); value: 0x(.*)", cmd_buf)
        if ecc_regs:
            errors_found = False
            for reg, val in ecc_regs:
                if int(val.strip(),16) != 0:
                    self.cli_log_slot_err(slot, "Reg 0x{:s}; value: 0x{:s}".format(reg,val))
                    errors_found = True

            if not errors_found:
                self.cli_log_slot_inf(slot, "No ECC errors found")
            else:
                self.cli_log_slot_err(slot, "ECC errors found")

        return True

    def mtp_get_nic_sts(self, slot, skip_vrm_check=True):
        """
         Read board and die temp via j2c
         WARNING: this does an ARM reset, so need a powercycle to bring NIC back to fresh slate
        """
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
            return True
        if not self._nic_ctrl_list[slot].read_nic_temp(skip_reboot=skip_vrm_check):
            self.cli_log_slot_err(slot, "Unable to dump NIC sts")
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT)
            return False

        self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT)

        return True

    def mtp_thread_stop_on_err(self):
        # send SIGINT to parent thread
        import signal
        os.kill(os.getpid(), signal.SIGINT)

    def mtp_get_file_md5sum(self, filename):
        cmd = "md5sum {:s}".format(filename)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute {:s}".format(cmd), level=0)
            return None
        cmd_buf = self.mtp_get_cmd_buf()
        md5sum_regex = r"([0-9a-fA-F]+) +.*"
        match = re.search(md5sum_regex, cmd_buf)
        if match:
            local_md5sum = match.group(1)
            return local_md5sum
        else:
            self.cli_log_err("Unable to verify {:s}".format(filename))
            return None

    def mtp_nic_port_counters(self, slot):
        self.cli_log_slot_inf(slot, "Dumping port counters")
        if not self._nic_ctrl_list[slot].nic_port_counters():
            self.mtp_dump_err_msg(self.mtp_get_nic_cmd_buf(slot))
            return False

        return True

    def mtp_construct_nic_fru_config(self, fail_nic_list, swmtestmode=Swm_Test_Mode.SW_DETECT):
        # construct nic fru config file
        temp_fru_cfg = dict()
        temp_fru_cfg["MTP_ID"] = self._id
        temp_fru_cfg["MTP_TS"] = libmfg_utils.get_timestamp()
        for slot in range(self._slots):
            key = libmfg_utils.nic_key(slot)
            temp_fru_cfg[key] = dict()
            if slot in fail_nic_list or not self.mtp_check_nic_status(slot):
                temp_fru_cfg[key]["VALID"] = False
                continue
            if self.mtp_nic_check_prsnt(slot):
                nic_type = self.mtp_get_nic_type(slot)
                temp_fru_cfg[key]["VALID"] = True
                temp_fru_cfg[key]["TS"] = libmfg_utils.get_fru_date()
                nic_fru_info = self.mtp_get_nic_fru(slot)
                if nic_fru_info:
                    temp_fru_cfg[key]["SN"] = nic_fru_info[0]
                    temp_fru_cfg[key]["MAC"] = nic_fru_info[1].replace('-', '')
                    temp_fru_cfg[key]["PN"] = nic_fru_info[2]
                    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        nic_fru_info = self.mtp_get_nic_alom_fru(slot)
                        temp_fru_cfg[key]["SN_ALOM"] = nic_fru_info[0]
                        temp_fru_cfg[key]["PN_ALOM"] = nic_fru_info[1]
                else:
                    temp_fru_cfg[key]["SN"] = "DEADBEEF"
                    temp_fru_cfg[key]["MAC"] = "DEADBEEF"
                    temp_fru_cfg[key]["PN"] = "DEADBEEF"
                    if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
                        temp_fru_cfg[key]["SN_ALOM"] = "DEADBEEF"
                        temp_fru_cfg[key]["PN_ALOM"] = "DEADBEEF"
            else:
                temp_fru_cfg[key]["VALID"] = False

        return temp_fru_cfg

    def mtp_scan_verify(self, temp_fru_cfg, scan_fru_cfg, pass_nic_list, fail_nic_list, dsp, ignore_pn_rev=False):
        fru_reprogram_list = list()

        test = "SCAN_VERIFY"
        for slot in range(self._slots):
            start_ts = self.log_slot_test_start(slot, test)
            key = libmfg_utils.nic_key(slot)
            if slot in fail_nic_list:
                continue
            if not self.mtp_check_nic_status(slot):
                continue
            if not temp_fru_cfg[key]["VALID"]:
                continue
            if scan_fru_cfg[key]["VALID"] == 'No':
                self.cli_log_slot_err_lock(slot, "Missing scan for this slot")
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
                self.mtp_set_nic_status_fail(slot, skip_fa=True)
                duration = self.log_slot_test_stop(slot, test, start_ts)
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(temp_fru_cfg[key]["SN"], dsp, test, "FAILED", duration))
                continue

            for item in ["SN", "MAC", "PN"]:
                expected = scan_fru_cfg[key][item]
                received = temp_fru_cfg[key][item]

                if expected != received:
                    if item == "PN" and ignore_pn_rev:
                        expected = expected[:PEN_PN_MINUS_REV_MASK]
                        received = received[:PEN_PN_MINUS_REV_MASK]
                        if expected == received:
                            if slot not in fru_reprogram_list:
                                fru_reprogram_list.append(slot)
                            continue

                    self.cli_log_slot_err_lock(slot, "Incorrect {:s}. Scanned {:s}, read {:s}.".format(item, expected, received))
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)
                    self.mtp_set_nic_status_fail(slot, skip_fa=True)
                    break
            duration = self.log_slot_test_stop(slot, test, start_ts)

            if slot in fail_nic_list:
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(temp_fru_cfg[key]["SN"], dsp, test, "FAILED", duration))
            else:
                self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(temp_fru_cfg[key]["SN"], dsp, test, duration))

        return fru_reprogram_list

    def mtp_nic_ping_test(self, slotA, slotB):
        if not self._nic_ctrl_list[slotA].nic_console_enable_network_port():
            self.cli_log_slot_err(slotA, "Setup mgmt failed")
            self.mtp_get_nic_err_msg(slotA)
            self.mtp_dump_nic_err_msg(slotA)
            return False
        if not self._nic_ctrl_list[slotB].nic_console_enable_network_port():
            self.cli_log_slot_err(slotB, "Setup mgmt failed")
            self.mtp_get_nic_err_msg(slotB)
            self.mtp_dump_nic_err_msg(slotB)
            return False

        keyA = libmfg_utils.nic_key(slotA)
        keyB = libmfg_utils.nic_key(slotB)
        self.cli_log_slot_inf(slotA, "Ping {:s} to {:s}".format(keyA, keyB))
        retA = self._nic_ctrl_list[slotA].nic_console_ping(slotB)
        if not retA:
            self.cli_log_slot_err(slotA, "Failed to ping link partner")
        self.cli_log_slot_inf(slotB, "Ping {:s} to {:s}".format(keyB, keyA))
        retB = self._nic_ctrl_list[slotB].nic_console_ping(slotA)
        if not retB:
            self.cli_log_slot_err(slotB, "Failed to ping link partner")

        if not self._nic_ctrl_list[slotA].nic_console_disable_network_port():
            self.cli_log_slot_err(slotA, "Enable MTP port failed")
            self.mtp_get_nic_err_msg(slotA)
            self.mtp_dump_nic_err_msg(slotA)
            return False
        if not self._nic_ctrl_list[slotB].nic_console_disable_network_port():
            self.cli_log_slot_err(slotB, "Enable MTP port failed")
            self.mtp_get_nic_err_msg(slotB)
            self.mtp_dump_nic_err_msg(slotB)
            return False

        if retA and retB:
            return True
        else:
            return False

    def mtp_nic_para_disp_ecc(self, vmarg, stop_on_err=False):
        nic_list = list()
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                nic_list.append(slot)

        if not nic_list:
            self.cli_log_err("No NICs passed")
            return nic_list[:]

        # parallel init mgmt/aapl
        dsp = "FA"
        if vmarg == Voltage_Margin.low:
            dsp = "LV_FA"
        elif vmarg == Voltage_Margin.high:
            dsp = "HV_FA"
        sn = ""
        test = "ECC_DISP"
        start_ts = libmfg_utils.timestamp_snapshot()

        mtp_start_ts = self.log_test_start(test)
        for slot in nic_list:
            sn = self.mtp_get_nic_sn(int(slot))
            slot_start_ts = self.log_slot_test_start(slot, test)
            self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return nic_list[:]

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.NIC_MGMT_PARA_SIG]
        cmd = MFG_DIAG_CMDS.MTP_DISP_ECC_FMT.format(nic_list_param)

        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            duration = self.log_test_stop(test, start_ts)
            for slot in nic_list:
                self.log_slot_test_stop(slot, test, start_ts)
                sn = self.mtp_get_nic_sn(int(slot))
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                self.mtp_set_nic_status_fail(slot)
            return nic_list[:]

        cmd_buf = self.mtp_get_cmd_buf()
        ecc_fail_list = list()

        slot_bufs = cmd_buf.split("=== Slot ")
        for slot_buf in slot_bufs[1:]: #skip first element
            slot = int(slot_buf[0:2])
            ecc_regs = re.findall(r"Reg 0x(.*): 0x(.*)", slot_buf)
            if ecc_regs:
                errors_found = False
                for reg, val in ecc_regs:
                    if int(val.strip(),16) != 0:
                        self.cli_log_slot_err(slot, "Reg 0x{:s}: 0x{:s}".format(reg,val))
                        errors_found = True
                        if slot not in ecc_fail_list:
                            ecc_fail_list.append(slot)

                if not errors_found:
                    self.cli_log_slot_inf(slot, "No ECC errors found")
                else:
                    self.cli_log_slot_err(slot, "ECC errors found")

        duration = self.log_test_stop(test, start_ts)
        for slot in nic_list:
            self.log_slot_test_stop(slot, test, start_ts)
            sn = self.mtp_get_nic_sn(int(slot))
            if slot in ecc_fail_list:
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            else:
                self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        return ecc_fail_list[:]

    def mtp_nic_sw_mgmt_init(self, slot):
        if not self.mtp_nic_mgmt_reinit(slot):
            self.cli_log_slot_err(slot, "Failed to init mgmt port in production FW")
            return False

        if not self.mtp_nic_mgmt_mac_refresh([slot]):
            self.cli_log_slot_err(slot, "MTP mac address refresh failed")
            return False

        if not self.mtp_mgmt_nic_mac_validate():
            self.cli_log_slot_err(slot, "MTP detect duplicate mac address")
            return False

        return True

    def mtp_nic_disp_ecc(self, slot):
        err_msg_list = list()
        errors_found = False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False, err_msg_list
            
        cmd = MFG_DIAG_CMDS.MTP_DISP_ECC_FMT.format(str(slot+1))

        ret = self.mtp_mgmt_exec_cmd_para(slot, cmd, timeout=5*60)

        if not ret:
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False, err_msg_list

        cmd_buf = self.mtp_get_nic_cmd_buf(slot)

        slot_bufs = cmd_buf.split("=== Slot ")
        for slot_buf in slot_bufs[1:]: #skip first element
            slot = int(slot_buf[0:2])-1
            ecc_regs = re.findall(r": Reg 0x(.*): 0x(.*)", slot_buf)
            if ecc_regs:
                errors_found = False
                for reg, val in ecc_regs:
                    if int(val.strip(),16) != 0:
                        self.cli_log_slot_err(slot, "Reg 0x{:s}: 0x{:s}".format(reg,val))
                        errors_found = True
                    err_msg_list.append(slot_buf.split())

            ecc_intr = re.findall(r"MSG(.*FAIL.*$)", slot_buf)
            if ecc_intr:
                errors_found = True
                err_msg_list += ecc_intr[:]

            ecc_errs = re.findall(r"(.*orrectable.*)", slot_buf)
            if ecc_errs:
                errors_found = True
                err_msg_list += ecc_errs[:]

            if not errors_found:
                self.cli_log_slot_inf(slot, "No ECC errors found")
            else:
                self.cli_log_slot_err(slot, "ECC errors found")

        if errors_found:
            return False, err_msg_list
        else:
            return True, err_msg_list

    def mtp_nic_vdd_ddr_fix(self, slot, console=False):
        d3_val = "0xb7" #vdd_ddr switching frequency
        d4_val = "0x0a" #vdd_ddr margin
        vddq_prog = False #prog vddq with same values

        nic_type = self.mtp_get_nic_type(slot)

        if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4, NIC_Type.LACONA32, NIC_Type.LACONA32DELL):
            self.cli_log_slot_err(slot, "This function is not applicable for this card type!")
            return False

        if nic_type in (NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4):
            d3_val = "0xb7"
            d4_val = "0x10"
            vddq_prog = True

        if nic_type == NIC_Type.POMONTEDELL or nic_type == NIC_Type.ORTANO2:
            d3_val = "0xb7"
            d4_val = "0x10"
            vddq_prog = False

        if nic_type in (NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5):
            d3_val = "0x07"

        if console:
            if not self._nic_ctrl_list[slot].nic_console_vdd_ddr_check(d3_val, d4_val, vddq_prog):
                self.mtp_clear_nic_err_msg(slot) # clear out the error message
                if not self._nic_ctrl_list[slot].nic_console_vdd_ddr_fix(d3_val, d4_val, vddq_prog):
                    self.cli_log_slot_err(slot, "Failed to set VDD_DDR margin")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                if not self._nic_ctrl_list[slot].nic_console_vdd_ddr_check(d3_val, d4_val, vddq_prog):
                    self.cli_log_slot_err(slot, "VDD_DDR values incorrect")
                    self.mtp_get_nic_err_msg(slot)
                    return False
        else:
            if nic_type in (NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5):
                rc = self._nic_ctrl_list[slot].nic_vdd_ddr_check(d3_val=d3_val, i2cbus_num="2")
            else:
                rc = self._nic_ctrl_list[slot].nic_vdd_ddr_check(d3_val, d4_val, vddq_prog)
            if not rc:
                self.mtp_clear_nic_err_msg(slot) # clear out the error message
                if nic_type in (NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5):
                    rc = self._nic_ctrl_list[slot].gigilo_nic_vdd_ddr_fix(d3_val=d3_val)
                else:
                    rc = self._nic_ctrl_list[slot].nic_vdd_ddr_fix(d3_val, d4_val, vddq_prog)
                if not rc:
                    self.cli_log_slot_err(slot, "Failed to set VDD_DDR margin")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                if nic_type in (NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5):
                    rc = self._nic_ctrl_list[slot].nic_vdd_ddr_check(d3_val=d3_val, i2cbus_num="2")
                else:
                    rc = self._nic_ctrl_list[slot].nic_vdd_ddr_check(d3_val, d4_val, vddq_prog)
                if not rc:
                    self.cli_log_slot_err(slot, "VDD_DDR values incorrect")
                    self.mtp_get_nic_err_msg(slot)
                    return False

        return True

    def mtp_nic_failed_boot(self, slot):
        return self._nic_ctrl_list[slot].nic_failed_boot()

    def mtp_set_nic_failed_boot(self, slot):
        return self._nic_ctrl_list[slot].set_nic_failed_boot()

    def mtp_nic_l1_health_check(self, slot):
        self.cli_log_slot_inf(slot, "Running L1 health check")
        sn = self.mtp_get_nic_sn(slot)
        self.mtp_mgmt_exec_cmd_para(slot, MFG_DIAG_CMDS.NIC_L1_HEALTH_CHECK.format(sn, slot+1), timeout=MTP_Const.MTP_L1_HEALTH_CHECK_TIMEOUT)
        ## check for 3 tests with "PASS" result in elb_l1_screen*.log
        self.mtp_nic_stop_test(slot)

    def mtp_nic_l1_esecure_prog(self, slot):
        self.mtp_single_j2c_lock()
        self.mtp_mgmt_exec_cmd_para(slot, "killall tclsh")

        if not self._nic_ctrl_list[slot].nic_l1_esecure_prog():
            self.mtp_single_j2c_unlock()
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        self.mtp_single_j2c_unlock()
        return True

    def mtp_nic_esec_write_protect(self, pass_nic_list=[], fail_nic_list=[], enable=False, dsp="DL"):
        nic_list = list()
        for slot in pass_nic_list:
            nic_type = self.mtp_get_nic_type(slot)
            if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
                nic_list.append(slot)

        if not nic_list:
            return True

        if enable:
            test = "ENABLE_ESEC_WP"
        else:
            test = "DISABLE_ESEC_WP"
        sn = ""
        start_ts = libmfg_utils.timestamp_snapshot()

        mtp_start_ts = self.log_test_start(test)
        for slot in nic_list:
            sn = self.mtp_get_nic_sn(int(slot))
            slot_start_ts = self.log_slot_test_start(slot, test)
            self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.NIC_ESEC_WRITE_PROT_SIG]

        for slot in nic_list:
            if enable:
                self.cli_log_slot_inf(slot, "Start Enable Esec Write Protection")
            else:
                self.cli_log_slot_inf(slot, "Start Disable Esec Write Protection")
        if enable:
            cmd = MFG_DIAG_CMDS.NIC_ENA_ESEC_WRITE_PROT_FMT.format(nic_list_param)
        else:
            cmd = MFG_DIAG_CMDS.NIC_DIS_ESEC_WRITE_PROT_FMT.format(nic_list_param)

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.NIC_ESEC_WRITE_PROT_DELAY):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            duration = self.log_test_stop(test, start_ts)
            for slot in nic_list:
                self.log_slot_test_stop(slot, test, start_ts)
                sn = self.mtp_get_nic_sn(int(slot))
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                self.mtp_set_nic_status_fail(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                if slot in pass_nic_list:
                    pass_nic_list.remove(slot)
            return False
        if "failed;" in self.mtp_get_cmd_buf():
            match = re.search("failed slots: *([0-9,]+)", self.mtp_get_cmd_buf())
            if match:
                for slot in libmfg_utils.expand_range_of_numbers(match.group(1), range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot-1
                    self.log_slot_test_stop(slot, test, start_ts)
                    sn = self.mtp_get_nic_sn(int(slot))
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                    self.mtp_set_nic_status_fail(slot)
                    if slot in nic_list:
                        nic_list.remove(slot)
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)
                    if slot in pass_nic_list:
                        pass_nic_list.remove(slot)
        if len(nic_list) > 0:
            duration = self.log_test_stop(test, start_ts)
            for slot in nic_list:
                self.log_slot_test_stop(slot, test, start_ts)
                sn = self.mtp_get_nic_sn(int(slot))
                self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))
            return True
        else:
            return False

    def mtp_nic_i2c_bus_scan(self, slot):
        self._nic_ctrl_list[slot].nic_i2c_bus_scan()

        return True

    def mtp_nic_read_transceiver_sn(self, slot, port):
        if not self._nic_ctrl_list[slot].nic_read_transceiver_sn(port):
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        if port in self._nic_ctrl_list[slot]._loopback_sn.keys():
            self.cli_log_slot_inf(slot, "Detected port {:s} loopback transceiver {:s}".format(port, self._nic_ctrl_list[slot]._loopback_sn[port]))
        else:
            self.cli_log_slot_inf(slot, "Missing port {:s} loopback info".format(port))
            return False

        return True

    def fst_setup_penctrl_ssh(self, slot, ip):
        cmd = "ls ~/.ssh/id_rsa"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Executing command {:s} failed".format(cmd), level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf()
        if "No such file" in cmd_buf:
            # create new ssh key-pair
            cmd_list = [
                "mkdir ~/.ssh",
                "chmod 700 ~/.ssh",
                "< /dev/zero ssh-keygen -q -N \"\" -f ~/.ssh/id_rsa"
            ]
            for cmd in cmd_list:
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("Executing command failed {:s}".format(cmd), level=0)
                    return False

        cmd_list = [
                "export \"DSC_URL\"=\"http://{:s}\"".format(ip),                                                                              # set env variable used by penctl
                "{:s} -a {:s} system enable-sshd".format("/home/diag/penctl.linux.042021", "/home/diag/penctl.token"),                        # penctl enable-sshd
                "{:s} -a {:s} update ssh-pub-key -f ~/.ssh/id_rsa.pub".format("/home/diag/penctl.linux.042021", "/home/diag/penctl.token")    # penctl point to the pub key
        ]
        for cmd in cmd_list:
            if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
                self.cli_log_slot_err(slot, "{:s} failed".format(cmd))
                return False

        return True

    def fst_get_eth_mnic(self, slot, bus):
        #### FIND CORRESPONDING ETH INTF NAME
        cmd = "grep PCI_SLOT_NAME /sys/class/net/*/device/uevent | grep \"{:s}\" | cut -d'/' -f5".format(bus)
        cmd_buf = self._nic_ctrl_list[slot].mtp_get_info(cmd)
        eth = cmd_buf.splitlines()[-1].strip()
        if not cmd_buf or "grep" in eth:
            self.cli_log_slot_err(slot, "Unable to find ethernet interface for PCI device {:s}".format(bus))
            self.log_nic_file(slot, "#############= FA DUMP =#############")
            self.mtp_mgmt_exec_cmd_para(slot, "grep PCI_SLOT_NAME /sys/class/net/*/device/uevent")
            self.mtp_mgmt_exec_cmd_para(slot, "lshw -c network -businfo")
            self.log_nic_file(slot, "#############= END FA DUMP =#############")
            return ""
        self._nic_ctrl_list[slot]._fst_eth_mnic = eth

        #### DECODE IP ADDRESS
        bus_str = bus.split(":", 1)[0]
        bus_int = int(bus_str, 16)
        if self.mtp_get_nic_type(slot) == NIC_Type.NAPLES100:
            intf_ip_addr = "169.254.0.2/24"
            ssh_ip_addr  = "169.254.0.1"
        else:
            intf_ip_addr = "169.254.{:d}.2/24".format(bus_int)
            ssh_ip_addr  = "169.254.{:d}.1".format(bus_int)

        #### ASSIGN IP ADDRESS TO ETH INTF
        self.cli_log_slot_inf(slot, "Enable NIC mnic {:s}".format(eth))
        self.mtp_mgmt_exec_cmd_para(slot, "ifconfig {:s} down".format(eth))
        time.sleep(1)
        self.mtp_mgmt_exec_cmd_para(slot, "ifconfig {:s} {:s}".format(eth, intf_ip_addr))
        self.mtp_mgmt_exec_cmd_para(slot, "ifconfig {:s} up".format(eth))
        time.sleep(1)
        if eth+": ERROR" in self.mtp_get_nic_cmd_buf(slot):
            self.cli_log_slot_err(slot, "Failed to enable NIC mnic")
            self.mtp_mgmt_exec_cmd_para(slot, "ifconfig {:s} down".format(eth))
            time.sleep(1)
            return ""
        return ssh_ip_addr

    def fst_disable_eth_mnic(self, slot):
        if not self.mtp_mgmt_exec_cmd_para(slot, "ifconfig {:s} down".format(self._nic_ctrl_list[slot]._fst_eth_mnic)):
            self.cli_log_slot_err(slot, "Failed to turn off eth interface {:s}".format(eth))
            return False
        return True

    def fst_setup_nic_ssh(self, slot):
        bus = self._nic_ctrl_list[slot]._fst_pcie_bus

        nic_mgmt_ip = self.fst_get_eth_mnic(slot, bus)
        if not nic_mgmt_ip:
            return False

        self._nic_ctrl_list[slot]._ip_addr = nic_mgmt_ip

        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in CAPRI_NIC_TYPE_LIST and nic_type != NIC_Type.NAPLES100:
            if not self.fst_setup_penctrl_ssh(slot, nic_mgmt_ip):
                return False

        return True

    def fst_check_nic_pcie(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        bus = self._nic_ctrl_list[slot]._fst_pcie_bus
        if nic_type in ELBA_NIC_TYPE_LIST:
            expected_speed = "16"
        elif nic_type in GIGLIO_NIC_TYPE_LIST:
            expected_speed = "16"
        else:
            expected_speed = "8"

        if nic_type in (NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2INTERP, NIC_Type.POMONTEDELL, NIC_Type.ORTANO2SOLO,
                    NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4,
                    NIC_Type.NAPLES100):
            expected_width = "16"
        elif nic_type in GIGLIO_NIC_TYPE_LIST:
            expected_width = "16"
        else:
            expected_width = "8"

        if not self.mtp_mgmt_exec_cmd_para(slot, "lspci -vv -s {:s} | grep LnkSta:".format(bus)):
            self.cli_log_err("Unable to retrieve link speed and width")
            return False
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        if "Speed {:s}GT/s".format(expected_speed) not in cmd_buf:
            self.cli_log_slot_err(slot, "PCIE link came up as {:s}".format(cmd_buf))
            return False

        if "Width x{:s}".format(expected_width) not in cmd_buf:
            self.cli_log_slot_err(slot, "PCIE link came up as {:s}".format(cmd_buf))
            return False

        self.cli_log_slot_inf(slot, "PCIE link came up {:s}GT/s x{:s}".format(expected_speed, expected_width))
        return True

    def fst_fetch_nic_info(self, slot):
        nic_type = self.mtp_get_nic_type(slot)

        if not self.fst_get_nic_fru_info(slot):
            return False

        if not self.fst_get_nic_fw_info(slot):
            return False

        if nic_type in (NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4):
            if not self.fst_nic_set_perf_mode(slot):
                pass

        if not self.fst_check_boot_image(slot):
            return False

        # if nic_type in ELBA_NIC_TYPE_LIST:
        #     if nic_type in FPGA_TYPE_LIST:
        #         cmd = "/nic/bin/halctl show system --yaml"
        #         if not self.mtp_nic_fst_exec_cmd(slot, cmd)):
        #             self.cli_log_slot_err(slot, "failed to execute halctl show system")
        #             return False
        #     else:
        #         cmd = "/nic/bin/pdsctl show system --yaml"
        #         if not self.mtp_nic_fst_exec_cmd(slot, cmd)):
        #             self.cli_log_slot_err(slot, "failed to execute pdsctl show system")
        #             return False

        #     die_temp = False
        #     local_temp = False
        #     die_temp_match = re.search(r'dietemperature:\s([0-9]+)$', self.mtp_get_nic_cmd_buf(slot))
        #     if die_temp_match:
        #         die_temp_val=int(die_temp_match.group(0).strip())
        #         die_temp = True
        #     else:
        #         self.cli_log_slot_err(slot, "Failed to find die temperature value")

        #     local_temp_match = re.search(r'localtemperature:\s([0-9]+)$', self.mtp_get_nic_cmd_buf(slot))
        #     if local_temp_match:
        #         local_temp_val=int(local_temp_match.group(0).strip())
        #         local_temp = True
        #     else:
        #         self.cli_log_slot_err(slot, "Failed to find local temperature value")        

        #     if die_temp: self.cli_log_slot_inf(slot, "dietemperature: {:d}".format(die_temp_val))
        #     if local_temp: self.cli_log_slot_inf(slot, "localtemperature: {:d}".format(local_temp_val))

        return True

    def fst_get_nic_fru_info(self, slot):
        cmd = "cat /tmp/fru.json"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to fetch SN")
            return False
        fru_json = re.findall(r"{.+}", self.mtp_get_nic_cmd_buf(slot),re.DOTALL)
        if not fru_json:
            self.cli_log_slot_err(slot, "Get FRU failed")
            return False
        fru = json.loads(fru_json[0])

        if fru["serial-number"]:
            sn = fru["serial-number"]
        else:
            self.cli_log_slot_err(slot, "Unable to parse serial-number from FRU")
            sn = "UNKNOWN"
        if self.mtp_get_nic_sn(slot) is None:
            self.mtp_set_nic_sn(slot, sn)
        if sn != self.mtp_get_nic_sn(slot):
           self.cli_log_slot_err(slot, "SN in FRU doesnt match: got {:s}, expected {:s}".format(sn, self.mtp_get_nic_sn(slot)))
           return False

        try:
            pn = fru["board-assembly-area"]
        except KeyError:
            try:
                pn = fru["part-number"]
            except KeyError:
                self.cli_log_slot_err(slot, "Unable to parse part-number from FRU")
                pn = ""

        nic_type = get_product_name_from_pn_and_sn(pn, sn)
        if nic_type != self.mtp_get_nic_type(slot):
            self.cli_log_slot_err(slot, "Unknown PN read from FRU: {:s} ({:s})".format(pn, str(nic_type)))
            return False

        self.cli_log_slot_inf(slot, "SN = {:s}, PN = {:s}, TYPE = {:s}".format(sn, pn, nic_type))
        return True

    def fst_get_nic_fw_info(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        self.cli_log_slot_inf(slot, "Retrieve FW info")

        if nic_type == NIC_Type.ORTANO2ADIIBM:
            cmd = "'export PATH=$PATH:/nic/bin; /nic/tools/fwupdate -l'"
        else:
            cmd = "/nic/tools/fwupdate -l"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to execute fwupdate -l")
            return False
        fw_json = re.findall(r"{.+}", self.mtp_get_nic_cmd_buf(slot),re.DOTALL)
        if not fw_json:
            self.cli_log_slot_err(slot, "failed to execute fwupdate -l")
            return False
        fwlist = json.loads(fw_json[0])
        if "boot0" in fwlist:
            self.cli_log_slot_inf(slot, "boot0:     {:15s}   {:s} rev{:d}".format(fwlist["boot0"]["image"]["software_version"], fwlist["boot0"]["image"]["build_date"], fwlist["boot0"]["image"]["image_version"]))
        else:
            if nic_type == NIC_Type.NAPLES100:
                if "uboot" in fwlist:
                    self.cli_log_slot_inf(slot, "uboot:     {:15s}   {:s}".format(fwlist["uboot"]["image"]["software_version"], fwlist["uboot"]["image"]["build_date"]))
                else:
                    self.cli_log_slot_err(slot, "FWLIST missing uboot info")
            elif nic_type != NIC_Type.ORTANO2ADIIBM:
                self.cli_log_slot_err(slot, "FWLIST missing boot0 info")
        for partition in ["mainfwa", "mainfwb", "goldfw", "diagfw", "extdiag"]:
            if nic_type in FPGA_TYPE_LIST and (partition == "mainfwa" or partition == "mainfwb"):
                continue
            if nic_type not in FPGA_TYPE_LIST and partition == "extdiag":
                continue
            try:
                if nic_type == NIC_Type.ORTANO2ADIIBM and partition in ["mainfwa","mainfwb"]:
                    if "fip" in fwlist[partition]:
                        self.cli_log_slot_inf(slot, "{:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["fip"]["software_version"], fwlist[partition]["fip"]["build_date"]) )
                    else:
                        self.cli_log_slot_err(slot, "FWLIST missing fip info for ADI IBM")
                        return False
                elif nic_type in (NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICRS4) and partition in ["mainfwa","mainfwb"]:
                    self.cli_log_slot_inf(slot, "NO {:s} needed for {:s}".format(partition, nic_type))
                else:
                    self.cli_log_slot_inf(slot, "{:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["kernel_fit"]["software_version"], fwlist[partition]["kernel_fit"]["build_date"]) )
            except KeyError as e:
                self.cli_log_slot_err(slot, "FWLIST missing {:s} info".format(partition))
                err_msg = traceback.format_exc()
                self._nic_ctrl_list[slot].nic_set_err_msg(err_msg)
                self.mtp_get_nic_err_msg(slot)
                return False
        self.cli_log_slot_inf(slot, "")

        return True

    def fst_check_boot_image(self, slot):
        cmd = "/nic/tools/fwupdate -r"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to execute fwupdate -r")
            return False
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        match = re.findall(r"(\w+fw\w?|extdiag)", cmd_buf)
        if match:
            self._nic_ctrl_list[slot]._boot_image = match[0]
        else:
            self.cli_log_slot_err(slot, "Unable to read current boot image")
            return False

        boot_image = self._nic_ctrl_list[slot]._boot_image
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type in FPGA_TYPE_LIST:
            if boot_image != "extdiag":
                self.cli_log_slot_err(slot, "Booted from {:s}, expecting extdiag".format(boot_image))
                return False
        elif nic_type == NIC_Type.ORTANO2ADIIBM:
            if boot_image != "goldfw":
                self.cli_log_slot_err(slot, "Booted from {:s}, expecting goldfw".format(boot_image))
                return False
        elif nic_type == NIC_Type.ORTANO2SOLOS4:
            if boot_image != "goldfw":
                self.cli_log_slot_err(slot, "Booted from {:s}, expecting goldfw".format(boot_image))
                return False
        elif nic_type == NIC_Type.ORTANO2ADICRS4:
            if boot_image != "goldfw":
                self.cli_log_slot_err(slot, "Booted from {:s}, expecting goldfw".format(boot_image))
                return False
        else:
            if boot_image != "mainfwa":
                self.cli_log_slot_err(slot, "Booted from {:s}, expecting mainfwa".format(boot_image))
                return False

        return True

    def fst_board_config(self, slot):
        ### SET BOARD CONFIG
        cmd = "'export LD_LIBRARY_PATH=$LD_LIBRAY_PATH:/nic/lib;/nic/bin/board_config -G 1 -F 0 -O 1'"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to set board config")
            return False

        ### DISPLAY BOARD CONFIG
        cmd = "'export LD_LIBRARY_PATH=$LD_LIBRAY_PATH:/nic/lib;/nic/bin/board_config -r'"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to set board config")
            return False

        ### VERIFY BOARD CONFIG
        buf = self.mtp_get_nic_cmd_buf(slot)
        match = re.findall(r"(gold_on_stop\s+1)", buf)
        match1 = re.findall(r"(gold_no_hostif\s+0)", buf)
        match2 = re.findall(r"(gold_oob\s+1)", buf)
        if not match or not match1 or not match2:
            self.cli_log_slot_err(slot, "board config verify failed")
            return False

        return True


