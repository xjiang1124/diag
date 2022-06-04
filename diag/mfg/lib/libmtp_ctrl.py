import pexpect
import time
import os
import sys
import libmfg_utils
import re
import threading
from datetime import datetime
from libmfg_cfg import *
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

from libnic_ctrl import nic_ctrl

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
        self._status = MTP_Status.MTP_STA_POWEROFF
        self._fanspd = MTP_Const.MFG_EDVT_NORM_FAN_SPD    # variable to track the fan speed (%) set by the script

        self._nic_ctrl_list = [None] * self._slots
        self._nic_alom_ctrl_list = [None] * self._slots
        self._nic_type_list = [None] * self._slots
        self._nic_prsnt_list = [False] * self._slots
        self._nic_scan_prsnt_list = [False] * self._slots
        self._nic_sn_list = [None] * self._slots
        self._nic_scan_sn_list = [None] * self._slots
        self._nic_alom_sn_list = [None] * self._slots
        self._nic_status_before_hide_list = [NIC_Status.NIC_STA_OK] * self._slots

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

        self._debug_mode = dbg_mode
        self._filep = filep
        self._cmd_buf = None
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._diag_nic_filep_list = diag_nic_log_filep_list[:]
        self._diagmgr_logfile = None
        self._temppn = None


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

    def log_slot_test_start(self, slot, testname):
        # log the timestamp in NIC log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(testname, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)
        return start

    def log_slot_test_stop(self, slot, testname, start):
        # log the timestamp in NIC log
        stop = libmfg_utils.timestamp_snapshot()
        duration = stop - start
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(testname, str(stop), str(duration))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)
        return duration

    def log_test_start(self, testname):
        # log the timestamp in MTP log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(testname, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd(ts_record_cmd)
        return start

    def log_test_stop(self, testname, start):
        # log the timestamp in MTP log
        stop = libmfg_utils.timestamp_snapshot()
        duration = stop - start
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(testname, str(stop), str(duration))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd(ts_record_cmd)
        return duration

    def mtp_sys_info_disp(self):
        self.cli_log_inf("MTP System Info Dump:", level=0)

        if not self._mgmt_cfg[0]:
            self.cli_log_err("Unable to retrieve MTP MGMT IP")
            return False
        self.cli_log_report_inf("MTP Chassis IP: {:s}".format(self._mgmt_cfg[0]))

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

        script_ver_match = re.search("image_amd64_.....?_(.*)\.tar", MFG_IMAGE_FILES.MTP_AMD64_IMAGE)
        if script_ver_match:
            script_ver = script_ver_match.group(1)
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


    def mtp_get_cmd_buf(self):
        return self._cmd_buf


    def mtp_dump_err_msg(self, err_msg):
        self.cli_log_err("==== Error Message Start: ====")
        if err_msg:
            if (len(err_msg) > 512):
                top_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[:256])
                self.cli_log_err(top_err_msg)
                self.cli_log_err("<============================>")
                bottom_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[-256:])
                self.cli_log_err(bottom_err_msg)
            else:
                err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg)
                self.cli_log_err(err_msg)
        self.cli_log_err("==== Error Message End: ====")

    def mtp_dump_nic_err_msg(self, slot):
        err_msg = self.mtp_get_nic_cmd_buf(slot)
        if err_msg is None:
            err_msg = ""
        self.cli_log_slot_err(slot, "==== Error Message Start: ====")
        if err_msg:
            if (len(err_msg) > 512):
                top_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[:256])
                self.cli_log_slot_err(slot, top_err_msg)
                self.cli_log_slot_err(slot, "<============================>")
                bottom_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[-256:])
                self.cli_log_slot_err(slot, bottom_err_msg)
            else:
                err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg)
                self.cli_log_slot_err(slot, err_msg)
        self.cli_log_slot_err(slot, "==== Error Message End: ====")


    def set_mtp_status(self, status):
        if status < MTP_Status.MTP_STA_MAX:
            self._status = status


    def get_mtp_slot_num(self):
        return self._slots


    def _mtp_single_apc_pwr_off(self, apc, userid, passwd, port_list):
        retry = 0
        handle = pexpect.spawn("telnet " + apc)
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["ame *:", "assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
            elif idx > 1 and retry < 5:
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
            idx = handle.expect(["ame *:", "assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
            elif idx > 1 and retry < 5:
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
            idx = handle.expect(["ame *:", "assword *:", pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
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
        if slot_list == []:
            slot_list = range(self._slots)
        userid = self._mgmt_cfg[1]
        for slot in slot_list:
            handle = self.mtp_session_create()
            if handle:
                if not self.mtp_prompt_cfg(handle, userid, "$", slot):
                    self.cli_log_err("Unable to config MTP session")
                    return False
                prompt = "{:s}@NIC-{:02d}:".format(userid, slot+1) + "$"
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
        handle.sendline("PS1='{:s}'".format(prompt_str))

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

    def mtp_mgmt_set_date(self, timestamp_str, fst=False):
        cmd = MFG_DIAG_CMDS.NIC_DATE_SET_FMT.format(timestamp_str)
        if fst:
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
        for sig in sig_list:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, [sig], timeout)
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
            self._cmd_buf = self._mgmt_handle.before
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


    def mtp_fan_init(self, fan_spd):
        rc = True
        # Fan present test
        cmd = MFG_DIAG_CMDS.MTP_FAN_PRSNT_FMT
        pass_sig_list = [MFG_DIAG_SIG.MTP_FAN0_PRSNT_SIG, MFG_DIAG_SIG.MTP_FAN1_PRSNT_SIG, MFG_DIAG_SIG.MTP_FAN2_PRSNT_SIG]
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

        # PSU test
        cmd = MFG_DIAG_CMDS.MTP_PSU_TEST_FMT
        pass_sig_list = []

        # apc_cfg is a list with format [apc1, apc1_port, apc1_userid, apc1_passwd, apc2, apc2_port, apc2_userid, apc2_passwd]
        if self._mtp_rev is not None and len(self._mtp_rev) > 0 and not MFG_BYPASS_PSU_CHECK:
            if int(self._mtp_rev) > 3:
                apc1 = self._apc_cfg[0]
                apc2 = self._apc_cfg[4]

                if apc1 != "" :
                    pass_sig_list.append(MFG_DIAG_SIG.MTP_PSU1_OK_SIG)
                if apc2 != "":
                    pass_sig_list.append(MFG_DIAG_SIG.MTP_PSU2_OK_SIG)

                rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list, timeout=MTP_Const.MTP_OS_CMD_DELAY)
                if rc:
                    self.cli_log_inf("PSU test passed")
                else:
                    self.cli_log_err("PSU test failed")
                    return rc

        return rc


    def mtp_diag_pre_init_start(self):
        if not self.mtp_mgmt_connect():
            self.cli_log_err("Unable to connect MTP chassis", level=0)
            return False
        self.cli_log_inf("MTP chassis connected\n", level=0)

        # start the mtp diag
        self.cli_log_inf("Pre Short Diag SW Environment Init", level=0)

        cmd = MFG_DIAG_CMDS.MTP_DIAG_INIT_FMT
        sig_list = [MFG_DIAG_SIG.MTP_DIAG_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = "source ~/.bash_profile"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=5):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        self.cli_log_inf("Init NIC Connections", level = 0)
        ret = self.mtp_nic_para_session_init()
        if not ret:
            self.cli_log_err("Init NIC Connections Failed", level = 0)
            return False

        if not self.mtp_nic_init():
            self.cli_log_err("Initialize NIC type, present failed", level=0)
            return False

        return True

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

    def mtp_diag_pre_init(self):
        # start the mtp diag
        self.cli_log_inf("Pre Diag SW Environment Init", level=0)

        cmd = MFG_DIAG_CMDS.MTP_DIAG_INIT_FMT
        sig_list = [MFG_DIAG_SIG.MTP_DIAG_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = "source ~/.bash_profile"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = "env | grep UUT"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute env command", level=0)
            return False

        # kill other diagmgr instances
        cmd = "killall diagmgr"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False

        # start the mtp diagmgr
        diagmgr_handle = self.mtp_session_create()
        if not diagmgr_handle:
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = MFG_DIAG_CMDS.MTP_DIAG_MGR_START_FMT.format(self._diagmgr_logfile)
        diagmgr_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(diagmgr_handle, [self._mgmt_prompt])
        if idx < 0:
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
        diagmgr_handle.close()

        # config the prompt
        userid = self._mgmt_cfg[1]
        if not self.mtp_prompt_cfg(self._mgmt_handle, userid, self._mgmt_prompt):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False
        self._mgmt_prompt = "{:s}@MTP:".format(userid) + self._mgmt_prompt

        # register MTP diagsp
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = MFG_DIAG_CMDS.MTP_DSP_START_FMT
        sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        if not self.mtp_sys_info_init():
            self.cli_log_err("Failed to Init MTP system information", level=0)
            return False

        self.cli_log_inf("Init NIC Connections", level = 0)
        ret = self.mtp_nic_para_session_init()
        if not ret:
            self.cli_log_err("Init NIC Connections Failed", level = 0)
            return False

        self.cli_log_inf("Pre Diag SW Environment Init complete\n", level=0)

        return True

    def mtp_inlet_temp_test(self, stage=None):
        rc = True
        cmd = MFG_DIAG_CMDS.MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP get inlet temperature failed")
            return False

        # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
        # FAN                 23.50          25.50          21.75          21.75
        match = re.search(r"FAN +(-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+)", self.mtp_get_cmd_buf())
        if match:
            # validate the readings
            inlet_1 = float(match.group(3))
            inlet_2 = float(match.group(4))

            # if stage in (FF_Stage.FF_4C_L, FF_Stage.FF_2C_L):
            #     if (inlet_1 < -5 or inlet_1 > 15) or (inlet_2 < -5 or inlet_2 > 15):
            #         rc = False

            # elif stage in (FF_Stage.FF_4C_H, FF_Stage.FF_2C_H):
            #     if (inlet_1 < 40 or inlet_1 > 60) or (inlet_2 < 40 or inlet_2 > 60):
            #         rc = False
            # else:
            #     if (inlet_1 < 15 or inlet_1 > 40) or (inlet_2 < 15 or inlet_2 > 40):
            #         rc = False
            if (inlet_1 < -10 or inlet_1 > 70) or (inlet_2 < -10 or inlet_2 > 70):
                rc = False

            if not rc:
                self.cli_log_err("Inlet1 ({:s}), Inlet2 ({:s}) temperature test failed".format(str(inlet_1), str(inlet_2)))
            else:
                self.cli_log_inf("Inlet1 ({:s}), Inlet2 ({:s}) temperature test passed".format(str(inlet_1), str(inlet_2)))

        else:
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("Unable to get inlet temperature")
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
        return True;


    def mtp_diag_get_img_files(self):
        cmd = "ls --color=never {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd), level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf().split()
        return cmd_buf


    def mtp_diag_post_init(self, mtp_capability, stage):
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

        # check if firmware image exist
        img_list = []
        if (mtp_capability & 0x1):
            for card_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
                if stage in (
                    FF_Stage.FF_DL,
                    FF_Stage.FF_P2C,
                    FF_Stage.FF_4C_L,
                    FF_Stage.FF_4C_H,
                    FF_Stage.FF_2C_L,
                    FF_Stage.FF_2C_H):
                    # CPLD and diagfw images.
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.diagfw_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(card_type))
                        pass

                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.diagfw_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing diagfw timestamp for {:s}".format(card_type))
                        return False
                elif stage == FF_Stage.FF_CFG:
                    # CPLD image
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                elif stage == FF_Stage.FF_SWI:
                    # Secure CPLD and goldfw images
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.sec_cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.goldfw_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing goldfw image for {:s}".format(card_type))
                        pass

                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        expected_version = NIC_IMAGES.sec_cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.sec_cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.goldfw_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing goldfw timestamp for {:s}".format(card_type))
                        return False
                else:
                    # no images needed in this stage
                    continue

        if (mtp_capability & 0x2):
            for card_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST + ["P41851", "P46653", "68-0016", "68-0017"]:
                if stage == FF_Stage.FF_DL:
                    # CPLD, failsafe, feature row and diagfw images
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.diagfw_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(card_type))
                        pass
                    try:
                        if card_type in ELBA_NIC_TYPE_LIST:
                            img = NIC_IMAGES.fail_cpld_img[card_type]
                            if img.strip() == "":
                                raise KeyError
                            img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing failsafe cpld image for {:s}".format(card_type))
                        pass
                    try:
                        if card_type in ELBA_NIC_TYPE_LIST and card_type not in FPGA_TYPE_LIST:
                            img = NIC_IMAGES.fea_cpld_img[card_type]
                            if img.strip() == "":
                                raise KeyError
                            img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing feature row image for {:s}".format(card_type))
                        pass

                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.diagfw_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing diagfw timestamp for {:s}".format(card_type))
                        return False
                    try:
                        if card_type in ELBA_NIC_TYPE_LIST:
                            expected_timestamp = NIC_IMAGES.fail_cpld_dat[card_type]
                            if expected_timestamp.strip() == "":
                                raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing failsafe cpld timestamp for {:s}".format(card_type))
                        pass
                elif stage in (
                    FF_Stage.FF_P2C,
                    FF_Stage.FF_4C_L,
                    FF_Stage.FF_4C_H,
                    FF_Stage.FF_2C_L,
                    FF_Stage.FF_2C_H):
                    # CPLD, failsafe, feature row and diagfw images
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.diagfw_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(card_type))
                        pass

                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.diagfw_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing diagfw timestamp for {:s}".format(card_type))
                        return False
                elif stage == FF_Stage.FF_CFG:
                    # CPLD image
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                elif stage == FF_Stage.FF_SWI:
                    # CPLD, Secure CPLD and goldfw images. Failsafe for Elba cards.
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.sec_cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld image for {:s}".format(card_type))
                        pass
                    try:
                        if card_type in ELBA_NIC_TYPE_LIST:
                            img = NIC_IMAGES.fail_cpld_img[card_type]
                            if img.strip() == "":
                                raise KeyError
                            img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing failsafe cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.goldfw_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing goldfw image for {:s}".format(card_type))
                        pass
                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        expected_version = NIC_IMAGES.sec_cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.sec_cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        if card_type in ELBA_NIC_TYPE_LIST:
                            expected_timestamp = NIC_IMAGES.fail_cpld_dat[card_type]
                            if expected_timestamp.strip() == "":
                                raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing failsafe cpld timestamp for {:s}".format(card_type))
                        pass
                    try:
                        expected_timestamp = NIC_IMAGES.goldfw_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing goldfw timestamp for {:s}".format(card_type))
                        return False

                if stage in (FF_Stage.FF_P2C, FF_Stage.FF_4C_L, FF_Stage.FF_4C_H, FF_Stage.FF_2C_L, FF_Stage.FF_2C_H):
                    try:
                        if card_type == NIC_Type.LACONA32 or card_type == NIC_Type.LACONA32DELL:
                            img = NIC_IMAGES.uboot_img[card_type]
                            if img.strip() == "":
                                raise KeyError
                            img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing uboot image for {:s}".format(card_type))
                        pass

                else:
                    # no images needed in this stage
                    continue

        cmd = "ls {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd), level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf()
        for img_file in img_list:
            if not os.path.basename(img_file) in cmd_buf:
                self.cli_log_err("Firmware {:s} doesn't exist".format(img_file), level=0)
                return False

        self.cli_log_inf("Post Diag SW Environment Init complete\n", level=0)
        # naples100 dsp check
#        self.cli_log_inf("Start Diag DSP Sanity Check", level = 0)
#        naples100_dsp_list = naples100_test_db.get_diag_seq_dsp_list()
#        naples100_dsp_list += naples100_test_db.get_diag_para_dsp_list()
#        for dsp in naples100_dsp_list:
#            if dsp not in self._mgmt_handle.before:
#                self.cli_log_err("Diag DSP: {:s} is not detected".format(dsp), level = 0)
#                return False
#        self.cli_log_inf("Diag DSP Sanity Check Complete", level = 0)

        return True


    def mtp_hw_init(self, fan_spd, stage=None):
        rc = True

        self.cli_log_inf("Start MTP chassis sanity check", level = 0)
        # mtp cpld test
        rc &= self.mtp_cpld_test()
        # fan init
        rc &= self.mtp_fan_init(fan_spd)
        # mtp inlet temperature
        rc &= self.mtp_inlet_temp_test(stage)

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
            self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
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

        try:
            expected_timestamp = NIC_IMAGES.goldfw_dat[nic_type]
            if nic_type == NIC_Type.ORTANO2 and self.mtp_is_nic_ortano_oracle(slot):
                expected_timestamp = NIC_IMAGES.goldfw_dat["68-0015"]
            if nic_type == NIC_Type.ORTANO2ADI and self.mtp_is_nic_ortanoadi_oracle(slot):
                expected_timestamp = NIC_IMAGES.goldfw_dat["68-0026"]
            if nic_type == NIC_Type.POMONTEDELL:
                expected_timestamp = NIC_IMAGES.goldfw_dat["90-0017"]
            if nic_type == NIC_Type.NAPLES25SWM:
                expected_timestamp = NIC_IMAGES.goldfw_dat[self.mtp_lookup_nic_swm_type(slot)]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing goldfw timestamp for {:s}".format(nic_type))
            return False

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
            time.sleep(5)
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
            self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
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
        if self._nic_type_list[slot] == NIC_Type.ORTANO2ADI and not dl:
            if not self._nic_ctrl_list[slot].nic_set_i2c_after_pw_cycle():
                self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
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


    def mtp_get_nic_err_msg(self, slot):
        return self._nic_ctrl_list[slot].nic_get_err_msg()


    def mtp_program_nic_fru(self, slot, date, sn, mac, pn):
        nic_type = self.mtp_get_nic_type(slot)
        self.cli_log_slot_inf_lock(slot, "Program NIC FRU date={:s}, sn={:s}, mac={:s}, pn={:s}".format(date, sn, mac, pn))
        if not self._nic_ctrl_list[slot].nic_program_fru(date, sn, mac, pn, nic_type):
            self.cli_log_slot_err_lock(slot, "Program NIC FRU failed")
            self.cli_log_slot_err_lock(slot, self.mtp_get_nic_err_msg(slot))
            self.mtp_dump_nic_err_msg(slot)
            return False
        if self._nic_ctrl_list[slot].nic_2nd_fru_exist(pn):
            if not self._nic_ctrl_list[slot].nic_disp_2nd_fru():
                self.cli_log_slot_err_lock(slot, "Display SMB NIC FRU failed")
                self.mtp_dump_nic_err_msg(slot)
                return False
        if not self._nic_ctrl_list[slot].nic_disp_fru():
            self.cli_log_slot_err_lock(slot, "Display NIC FRU failed")
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
    
        fru_pn = self._nic_ctrl_list[slot].get_nic_fru_hpe_pn()

        if fru_pn != hpe_pn:
            self.cli_log_slot_err_lock(slot, "HPE PN Verify Failed expect {:s}".format(hpe_pn))
            return False
        self.cli_log_slot_inf_lock(slot, "Verify HPE PN FRU Pass, PN={:s}".format(hpe_pn))

        return True
        
    def mtp_verify_nic_alom_fru(self, slot, alom_sn, alom_pn, date):
    
        fru_buf = self._nic_ctrl_list[slot].mtp_read_alom_fru(slot)

        if not fru_buf:
            self.mtp_set_nic_status_fail(slot)
            return False

        # retrieve card serial number
        
        newdate = date[0] + date[1] + '/' + date[2] + date[3] + '/' + date[4] + date[5]
            
        if not re.findall(alom_sn, fru_buf):
            self.cli_log_slot_err_lock(slot, "ALOM SN Verify Failed expect {:s}".format(alom_sn))
            return False
        if not re.findall(alom_pn, fru_buf):
            self.cli_log_slot_err_lock(slot, "ALOM PN Verify Failed expect {:s}".format(alom_pn))
            return False
        if not re.findall(newdate, fru_buf):           
            self.cli_log_slot_err_lock(slot, "Date Verify Failed expect {:s}".format(newdate))
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

    def mtp_reverse_lookup_naples_pn(self, slot):
        """
         Get NIC type from PN
        """
        naples_pn = self._nic_ctrl_list[slot].nic_get_naples_pn()
        
        if not naples_pn:
            self.cli_log_slot_err_lock(slot, "Verify NIC:  Retreive PN Failed")
            return False

        if re.match(PART_NUMBERS_MATCH.N100_PN_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES100

        elif re.match(PART_NUMBERS_MATCH.N100_IBM_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES100IBM

        elif re.match(PART_NUMBERS_MATCH.N100_HPE_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES100HPE

        elif re.match(PART_NUMBERS_MATCH.N100_DELL_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES100DELL

        elif re.match(PART_NUMBERS_MATCH.N25_PN_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES25

        elif re.match(PART_NUMBERS_MATCH.N25_SWM_HPE_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES25SWM

        elif re.match(PART_NUMBERS_MATCH.N25_SWM_DEL_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES25SWMDELL

        elif re.match(PART_NUMBERS_MATCH.N25_SWM_833_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES25SWM833

        elif re.match(PART_NUMBERS_MATCH.N25_OCP_PN_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES25OCP

        elif re.match(PART_NUMBERS_MATCH.FORIO_FMT_ALL, naples_pn):
            nic_type = NIC_Type.FORIO

        elif re.match(PART_NUMBERS_MATCH.VOMERO_FMT_ALL, naples_pn):
            nic_type = NIC_Type.VOMERO

        elif re.match(PART_NUMBERS_MATCH.VOMERO2_FMT_ALL, naples_pn):
            nic_type = NIC_Type.VOMERO2

        elif re.match(PART_NUMBERS_MATCH.ORTANO_FMT_ALL, naples_pn):
            nic_type = NIC_Type.ORTANO

        elif re.match(PART_NUMBERS_MATCH.ORTANO2_FMT_ALL, naples_pn):
            nic_type = NIC_Type.ORTANO2

        elif re.match(PART_NUMBERS_MATCH.ORTANO2ADI_FMT_ALL, naples_pn):
            nic_type = NIC_Type.ORTANO2ADI

        else:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type for PN {:s}".format(naples_pn))
            return False

        self.mtp_set_nic_type(slot, nic_type)
        return True

    def mtp_verify_naples_pn(self, slot):
        naples_pn = self._nic_ctrl_list[slot].nic_get_naples_pn()
        
        if not naples_pn:
            self.cli_log_slot_err_lock(slot, "Verify NIC:  Retreive PN Failed")
            return False

        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES100:
            exp_pn = PART_NUMBERS_MATCH.N100_PN_FMT_ALL
        elif nic_type == NIC_Type.NAPLES100IBM:
            exp_pn = PART_NUMBERS_MATCH.N100_IBM_FMT_ALL
        elif nic_type == NIC_Type.NAPLES100HPE:
            exp_pn = PART_NUMBERS_MATCH.N100_HPE_FMT_ALL
        elif nic_type == NIC_Type.NAPLES100DELL:
            exp_pn = PART_NUMBERS_MATCH.N100_DELL_FMT_ALL
        elif nic_type == NIC_Type.NAPLES25:
            exp_pn = PART_NUMBERS_MATCH.N25_PN_FMT_ALL
        elif nic_type == NIC_Type.NAPLES25SWM:
            exp_pn = PART_NUMBERS_MATCH.N25_SWM_HPE_FMT_ALL
        elif nic_type == NIC_Type.NAPLES25SWMDELL:
            exp_pn = PART_NUMBERS_MATCH.N25_SWM_DEL_FMT_ALL
        elif nic_type == NIC_Type.NAPLES25SWM833:
            exp_pn = PART_NUMBERS_MATCH.N25_SWM_833_FMT_ALL
        elif nic_type == NIC_Type.NAPLES25OCP:
            exp_pn = PART_NUMBERS_MATCH.N25_OCP_PN_FMT_ALL
        elif nic_type == NIC_Type.FORIO:
            exp_pn = PART_NUMBERS_MATCH.FORIO_FMT_ALL
        elif nic_type == NIC_Type.VOMERO:
            exp_pn = PART_NUMBERS_MATCH.VOMERO_FMT_ALL
        elif nic_type == NIC_Type.VOMERO2:
            exp_pn = PART_NUMBERS_MATCH.VOMERO2_FMT_ALL
        elif nic_type == NIC_Type.ORTANO:
            exp_pn = PART_NUMBERS_MATCH.ORTANO_FMT_ALL
        elif nic_type == NIC_Type.ORTANO2:
            exp_pn = PART_NUMBERS_MATCH.ORTANO2_FMT_ALL
        elif nic_type == NIC_Type.POMONTEDELL:
            exp_pn = PART_NUMBERS_MATCH.POMONTEDELL_PN_FMT
        elif nic_type == NIC_Type.LACONA32DELL:
            exp_pn = PART_NUMBERS_MATCH.LACONA32DELL_PN_FMT
        elif nic_type == NIC_Type.LACONA32:
            exp_pn = PART_NUMBERS_MATCH.LACONA32_PN_FMT
        elif nic_type == NIC_Type.ORTANO2ADI:
            exp_pn = PART_NUMBERS_MATCH.ORTANO2ADI_FMT_ALL
        else:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
            return False

        match = re.findall(exp_pn, naples_pn)
        if match:
            self.cli_log_slot_inf_lock(slot, "==> Verify Naples_PN Pass, naples_pn={:s}".format(naples_pn))
            return True
        else:
            self.cli_log_slot_err_lock(slot, "NAPLES_PN Verify Failed, Read {:s}".format(naples_pn))
            return False

    def mtp_nic_program_ocp_adapter_fru(self, slot, date, sn, mac, pn):
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type != NIC_Type.NAPLES25OCP:
            self.cli_log_err("This function cannot be used without an OCP card plugged in")
            return False

        self.cli_log_slot_inf_lock(slot, "Program OCP Adapter FRU date={:s}, sn={:s}, mac={:s}, pn={:s}".format(date, sn, mac, pn))
        if not self._nic_ctrl_list[slot].nic_program_ocp_adapter_fru(date, sn, mac, pn):
            self.cli_log_slot_err_lock(slot, "Program OCP Adapter FRU failed")
            self.cli_log_slot_err_lock(slot, self.mtp_get_nic_err_msg(slot))
            self.mtp_dump_nic_err_msg(slot)
            return False
        if not self._nic_ctrl_list[slot].nic_ocp_adapter_fru_init():
            self.cli_log_slot_err_lock(slot, "Display OCP Adapter FRU failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_nic_verify_ocp_adapter_fru(self, slot, exp_date, exp_sn, exp_mac, exp_pn):
        if not self._nic_ctrl_list[slot].nic_ocp_adapter_fru_init():
            self.cli_log_slot_err_lock(slot, "Load OCP Adapter FRU failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        sn = self._riser_sn
        date = self._riser_progdate

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
            software_pn == "90-0012-0001"
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
        self.cli_log_slot_inf_lock(slot, "==> Check SOFTWARE IMAGE PN {:s}    CARD PN {:s} ".format(software_pn, naples_pn))   
        if naples_pn[0:7] == "68-0003":        #NAPLES 100 PENSANDO
            if software_pn != "90-0001-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:9] == "111-04635": #NAPLES 100 NETAPP
            if software_pn != "90-0001-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0013":   #NAPLES100 IBM
            if software_pn != "90-0004-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:6] == "P37692":    #NAPLES100 HPE 
            if software_pn != "90-0002-0008":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False    
        elif naples_pn[0:6] == "P41854":    #NAPLES100 HPE CLOUD
            if software_pn != "90-0006-0002":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0024":    #NAPLES100 DELL 
            if software_pn != "90-0013-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0005":    #NAPLES25 PENSANDO
            if software_pn != "90-0002-0003":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False 
        elif naples_pn[0:6] == "P18669":     #NAPLES25 HPE
            if software_pn != "90-0006-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False 
        elif naples_pn[0:7] == "68-0008":    #NAPLES25 EQUINIX
            if software_pn != "90-0006-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False 
        elif naples_pn[0:6] == "P26968":     #NAPLES25 SWM HPE
            if software_pn != "90-0002-0008":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False 
        elif naples_pn[0:6] == "P41851":     #NAPLES25 SWM HPE CLOUD
            if software_pn != "90-0006-0002":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:6] == "P46653":    # NAPLES25 SWM HPE TAA
            if software_pn != "90-0014-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif (naples_pn[0:7] == "68-0016") or (naples_pn[0:7] == "68-0017"):    #NAPLES25 SWM PENSANDO & TAA
            if software_pn != "90-0002-0005":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0014":     #NAPLES25 SWM DELL
            if software_pn != "90-0007-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0019":     #NAPLES25 SWM 833
            if software_pn != "90-0002-0007":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0023":     #NAPLES25 OCP PENSANDO
            if software_pn != "90-0002-0007":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:6] == "P37689":      #NAPLES25 OCP HPE
            if software_pn != "90-0002-0008":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:6] == "P41857":      #NAPLES25 OCP HPE CLOUD
            if software_pn != "90-0006-0002":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0010":     #NAPLES25 OCP DELL
            if software_pn != "90-0007-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif ((naples_pn[0:7] == "68-0007") or (naples_pn[0:7] == "68-0009") or (naples_pn[0:7] == "68-0011")):      #FORIO/VOMERO/VOMERO2
            if software_pn != "90-0003-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0015":     #ORTANO
            if software_pn != "90-0009-0006":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
            if pn_check and not naples_pn.endswith("C1"):
                self.cli_log_slot_err_lock(slot, "Check PN REV: Software Image match to nic part number failed")
                self.cli_log_slot_err_lock(slot, "Expected: {:s}, Got: {:s}".format(naples_pn[:PN_MINUS_REV_MASK]+" C1", naples_pn))
                return False
        elif naples_pn[0:7] == "68-0021":     #ORTANO PENSANDO
            if software_pn != "90-0011-0003":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:6] == "0PCFPC":      #POMONTE DELL
            if software_pn != "90-0017-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:6] == "0X322F":      #LACONA32 DELL
            if software_pn != "90-0017-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:6] == "P47930":      #LACONA32 HPE
            if software_pn != "90-0017-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0026":     #ORTANO2 ADI ORACLE
            if software_pn != "90-0009-0006":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        else:
            self.cli_log_slot_err_lock(slot, "check_swi_software_image Unknown Part Number {:s} !!".format(naples_pn))
            return False             
        '''
        *** AS OF 11/30/2020.. 
        90-0001-0001   netapp  PNSO-1.0.0-E-7-netapp-09162019-1911.tar
        90-0002-0001   goldman  PNSO-1.1.1-E-15-goldman-10042019-1722.tar ??
        90-0002-0002    PNSO-1.3.2-E-3-basicdsc-ga-022420202-1611
        90-0002-0003   naples_fw_1.8.0-E-48_B-_0608.tar
        90-0002-0004   naples_fw_iris_RELB_1.12.0-E-52_0728.tar
        90-0002-0005   //standup swm naples_fw_iris_1.17.0-54_1120.tar
        90-0002-0007   //RelB++ (SWM833, OCP). Updated 03/02/2021
        90-0002-0008   //1.14.5 (All HPE Ent: SWM, 100, OCP). Updated 05/28/2021
        90-0003-0001   //Oracle Capri cards.. dont care
        90-0004-0001   //IBM  naples_fw_apulu_1.17.0-42_1117.tar
        90-0005-0001   //OCP  naples_fw_iris_1.14.0-E-25_2020.08.31.tar
        90-0006-0001   //CLOUD-A  naples_fw_apulu_1.10.3-C-26_CloudA_0806.tar
        90-0006-0002   //HPE SWM AND NAPLES100 CLOUD naples_fw_apulu_1.16.2-C-10_2021.04.08.tar
        90-0007-0001   //naples_fw_iris_1.14.4-E-12_20210408.tar. Updated 04/12/2021
        90-0008-0001   //DELL SWM  dsc_fw_1.14.0-E-45.tar
        90-0009-0002   //Ortano2-oracle dsc_fw_athena_elba_1.15.8-C-9_2021.05.22.tar
        90-0010-0001   //1.14.5 (OCP). Updated 04/26/2021
        90-0017-0001   naples_uefidiag_fw_elba_1.46.0-E-15_2022.04.27.tar (pomontedell & lacona32)
        '''
        return True

    def mtp_get_alom_fru(self, slot):
        return self._nic_ctrl_list[slot].alom_get_fru()

    def mtp_setting_partition(self, slot):
        # copy script to detect the emmc part size
        if not self._nic_ctrl_list[slot].nic_copy_image("{:s}diag/scripts/emmc_format.sh".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)):
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

    def mtp_program_nic_cpld(self, slot, cpld_img, dl_step=True):
        # check the current cpld version
        nic_type = self.mtp_get_nic_type(slot)
        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            if nic_type in FPGA_TYPE_LIST:
                dev = "FPGA"
            else:
                dev = "CPLD"
            self.cli_log_slot_err_lock(slot, "Program NIC {:s} failed, can not retrieve {:s} info".format(dev))
            return False
        cur_ver = nic_cpld_info[0]
        cur_timestamp = nic_cpld_info[1]
        try:
            expected_version = NIC_IMAGES.cpld_ver[nic_type]
            if nic_type == NIC_Type.NAPLES25SWM:
                expected_version = NIC_IMAGES.cpld_ver[self.mtp_lookup_nic_swm_type(slot)]
            if nic_type == NIC_Type.NAPLES100HPE and self.mtp_is_nic_cloud(slot):
                expected_version = NIC_IMAGES.cpld_ver["P41854"]
            if nic_type == NIC_Type.ORTANO2ADI and not dl_step:
                expected_version = NIC_IMAGES.cpld_ver["68-0026"]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD version for {:s}".format(nic_type))
            return False
        try:
            expected_timestamp = NIC_IMAGES.cpld_dat[nic_type]
            if nic_type == NIC_Type.NAPLES25SWM:
                expected_timestamp = NIC_IMAGES.cpld_dat[self.mtp_lookup_nic_swm_type(slot)]
            if nic_type == NIC_Type.NAPLES100HPE and self.mtp_is_nic_cloud(slot):
                expected_timestamp = NIC_IMAGES.cpld_dat["P41854"]
            if nic_type == NIC_Type.ORTANO2ADI and not dl_step:
                expected_timestamp = NIC_IMAGES.cpld_dat["68-0026"]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD timestamp for {:s}".format(nic_type))
            return False

        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip CPLD update for Proto NIC")
            return True

        if cur_ver == expected_version and cur_timestamp == expected_timestamp:
            if nic_type in FPGA_TYPE_LIST:
                dev = "FPGA"
            else:
                dev = "CPLD"
            self.cli_log_slot_inf_lock(slot, "NIC {:s} is up-to-date".format(dev))
            self._nic_ctrl_list[slot].nic_require_cpld_refresh(False)
            return True

        if nic_type in FPGA_TYPE_LIST:
            partition = ""
        elif nic_type in ELBA_NIC_TYPE_LIST:
            partition = "cfg0"
        else:
            partition = ""
        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, partition):
            if nic_type in FPGA_TYPE_LIST:
                dev = "FPGA"
            else:
                dev = "CPLD"
            self.cli_log_slot_err_lock(slot, "Program NIC {:s} failed".format(dev))
            self.mtp_dump_nic_err_msg(slot)
            return False

        self._nic_ctrl_list[slot].nic_require_cpld_refresh(True)
        if nic_type in FPGA_TYPE_LIST:
            self._nic_ctrl_list[slot].nic_set_fpga_updated(val=True, gold=False)

        return True

    def mtp_program_nic_failsafe_cpld(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if not nic_type in ELBA_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no failsafe CPLD for {:s}".format(nic_type))
            return False
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip failsafe CPLD update for Proto NIC")
            return True

        if nic_type in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST and nic_type != NIC_Type.ORTANO2ADI:
            # can't check the version without loading backup partition into the running partition
            self.cli_log_slot_inf(slot, "Skip checking failsafe CPLD version")

        if nic_type in FPGA_TYPE_LIST:
            partition = "cfg1"
        elif nic_type in ELBA_NIC_TYPE_LIST:
            partition = "cfg1"
        else:
            partition = ""
        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, partition):
            if nic_type in FPGA_TYPE_LIST:
                dev = "FPGA"
            else:
                dev = "CPLD"
            self.cli_log_slot_err_lock(slot, "Program NIC {:s} failed".format(dev))
            self.mtp_dump_nic_err_msg(slot)
            return False

        if nic_type in FPGA_TYPE_LIST:
            self._nic_ctrl_list[slot].nic_set_fpga_updated(val=True, gold=True)

        return True

    def mtp_verify_nic_fpga(self, slot, cpld_img_file, gold=False):
        if not self._nic_ctrl_list[slot].nic_get_fpga_updated(gold):
            self.cli_log_slot_inf_lock(slot, "No FPGA verify needed")
            return True

        if not self._nic_ctrl_list[slot].nic_verify_fpga(cpld_img_file, gold):
            if gold:
                self.cli_log_slot_err_lock(slot, "NIC GOLD FPGA verify failed")
            else:
                self.cli_log_slot_err_lock(slot, "NIC FPGA verify failed")
            self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_cpld_feature_row(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no feature row for {:s}".format(nic_type))
            return False
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "No feature row update for Proto NIC")
            return True

        cpld_img = "/home/diag/"+NIC_IMAGES.fea_cpld_img[nic_type]

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

        if not self._nic_ctrl_list[slot].nic_verify_sec_cpld():
            self.cli_log_slot_err(slot, "Verify NIC Secure CPLD failed")
            return False

        return True

    def mtp_verify_nic_cpld_fea(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no feature row for {:s}".format(nic_type))
            return False

        fea_regex = r"00000000  (.*)  \|.*\|" #first 16 bytes

        cmd = "hexdump -C /home/diag/"+NIC_IMAGES.fea_cpld_img[nic_type]
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
        if nic_type not in ELBA_NIC_TYPE_LIST:
            return False

        if not self._nic_ctrl_list[slot].nic_program_efuse():
            self.cli_log_slot_err(slot, "Program NIC Efuse failed")
            self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
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

    def mtp_verify_nic_cpld(self, slot, sec_cpld=False, timestamp_check=True, dl_step=True):
        # cpld_has_timestamp = 1
        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Verify NIC CPLD failed, can not retrieve CPLD info")
            return False

        cur_ver = nic_cpld_info[0]
        cur_timestamp = nic_cpld_info[1]
        nic_type = self.mtp_get_nic_type(slot)

        try:
            expected_version = NIC_IMAGES.cpld_ver[nic_type]
            if nic_type == NIC_Type.NAPLES25SWM:
                expected_version = NIC_IMAGES.cpld_ver[self.mtp_lookup_nic_swm_type(slot)]
            if nic_type == NIC_Type.NAPLES100HPE and self.mtp_is_nic_cloud(slot):
                expected_version = NIC_IMAGES.cpld_ver["P41854"]
            if nic_type == NIC_Type.ORTANO2ADI and not dl_step:
                expected_version = NIC_IMAGES.cpld_ver["68-0026"]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD version for {:s}".format(nic_type))
            return False
        try:
            expected_timestamp = NIC_IMAGES.cpld_dat[nic_type]
            if nic_type == NIC_Type.NAPLES25SWM:
                expected_timestamp = NIC_IMAGES.cpld_dat[self.mtp_lookup_nic_swm_type(slot)]
            if nic_type == NIC_Type.NAPLES100HPE and self.mtp_is_nic_cloud(slot):
                expected_timestamp = NIC_IMAGES.cpld_dat["P41854"]
            if nic_type == NIC_Type.ORTANO2ADI and not dl_step:
                expected_timestamp = NIC_IMAGES.cpld_dat["68-0026"]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD timestamp for {:s}".format(nic_type))
            return False
        if sec_cpld:
            try:
                expected_version = NIC_IMAGES.sec_cpld_ver[nic_type]
                if nic_type == NIC_Type.NAPLES25SWM:
                    expected_version = NIC_IMAGES.sec_cpld_ver[self.mtp_lookup_nic_swm_type(slot)]
                if nic_type == NIC_Type.NAPLES100HPE and self.mtp_is_nic_cloud(slot):
                    expected_version = NIC_IMAGES.sec_cpld_ver["P41854"]
                if nic_type == NIC_Type.ORTANO2ADI and not dl_step:
                    expected_version = NIC_IMAGES.sec_cpld_ver["68-0026"]
            except KeyError:
                self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD version for {:s}".format(nic_type))
                return False
            try:
                expected_timestamp = NIC_IMAGES.sec_cpld_dat[nic_type]
                if nic_type == NIC_Type.NAPLES25SWM:
                    expected_timestamp = NIC_IMAGES.sec_cpld_dat[self.mtp_lookup_nic_swm_type(slot)]
                if nic_type == NIC_Type.NAPLES100HPE and self.mtp_is_nic_cloud(slot):
                    expected_timestamp = NIC_IMAGES.sec_cpld_dat["P41854"]
                if nic_type == NIC_Type.ORTANO2ADI and not dl_step:
                    expected_timestamp = NIC_IMAGES.sec_cpld_dat["68-0026"]
            except KeyError:
                self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD timestamp for {:s}".format(nic_type))
                return False

        if cur_ver != expected_version or (timestamp_check and cur_timestamp != expected_timestamp):
                self.cli_log_slot_err_lock(slot, "Verify NIC CPLD Failed")
                self.cli_log_slot_err_lock(slot, "Expect Version: {:s}, get: {:s}".format(expected_version, cur_ver))
                self.cli_log_slot_err_lock(slot, "Expect Timestamp: {:s}, get: {:s}".format(expected_timestamp, cur_timestamp))
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
        
    def mtp_copy_nic_gold(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_copy_gold(gold_img):
            self.cli_log_slot_inf_lock(slot, "Copy NIC goldfw failed")
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
    def mtp_program_nic_gold_naples100(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_program_gold_naples100(gold_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC goldfw failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        if not self.mtp_mgmt_set_nic_gold_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True

    def mtp_program_nic_uboot(self, slot, uboot_img, installer=MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"install_file"):
        if not self._nic_ctrl_list[slot].nic_program_uboot(uboot_img, installer):
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

        try:
            expected_timestamp = NIC_IMAGES.diagfw_dat[nic_type]
            if nic_type == NIC_Type.NAPLES25OCP and self.mtp_is_nic_ocp_dell(slot):
                expected_timestamp = NIC_IMAGES.diagfw_dat["68-0010"]
            if nic_type == NIC_Type.NAPLES25SWM:
                expected_timestamp = NIC_IMAGES.diagfw_dat[self.mtp_lookup_nic_swm_type(slot)]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing diagfw timestamp for {:s}".format(nic_type))
            return False

        if ( boot_image != "diagfw" ):
            self.cli_log_slot_err_lock(slot, "Checking Boot Image is Diagfw Failed, NIC is booted from {:s}".format(boot_image))
            return False

        if ( expected_timestamp != kernel_timestamp ):
            self.cli_log_slot_err_lock(slot, "Diagfw Verify Failed, Expect: {:s}   Read: {:s}".format(expected_timestamp, kernel_timestamp))
            return False

        # additional: check has diag uboot
        if nic_type in (NIC_Type.ORTANO2):
            if not self._nic_ctrl_list[slot].nic_console_read_uboot():
                self.cli_log_slot_inf(slot, self.mtp_get_nic_err_msg(slot))
                self.cli_log_slot_inf(slot, "Uboot update needed")
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
        
    def mtp_program_nic_emmc_ibm(self, slot, emmc_img):
        if not self._nic_ctrl_list[slot].nic_program_emmc_ibm(emmc_img):
            self.cli_log_slot_err_lock(slot, "Program NIC EMMC failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        if not self.mtp_mgmt_set_nic_sw_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True
    def mtp_program_nic_emmc_naples100(self, slot, emmc_img):
        if not self._nic_ctrl_list[slot].nic_program_emmc_naples100(emmc_img):
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


    def mtp_mgmt_copy_nic_diag(self, slot, nic_utils=False):
        if nic_utils:
            msg = "Copy NIC Diag/Utils Image"
        else:
            msg = "Copy NIC Diag Image"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_copy_diag_img(nic_utils):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_set_nic_status_fail(slot)
            return False

        return True


    def mtp_mgmt_save_nic_logfile(self, slot, logfile_list):
        self.cli_log_slot_inf(slot, "Collecting NIC tclsh logfiles")
        if not self._nic_ctrl_list[slot].nic_save_logfile(logfile_list):
            self.cli_log_slot_err_lock(slot, "Save NIC Logfile failed")
            self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True


    def mtp_mgmt_save_nic_diag_logfile(self, slot, aapl):
        self.cli_log_slot_inf(slot, "Collecting NIC diag logfiles")
        if not self._nic_ctrl_list[slot].nic_save_diag_logfile(aapl):
            self.cli_log_slot_err_lock(slot, "Save NIC Diag Logfile failed")
            self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
            self.mtp_dump_nic_err_msg(slot)
            return False

        # self.mtp_mgmt_nic_diag_sys_clean()

        return True

    def mtp_post_dsp_fail_steps(self, slot, test, rslt, rslt_cmd_buf, err_msg_list):
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
        self._nic_ctrl_list[slot].mtp_exec_cmd("######## {:s} ########".format("START post dsp {:s} fail debug".format(test)))

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

        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in ELBA_NIC_TYPE_LIST and "L1" not in test:
            self.mtp_single_j2c_lock()
            self.mtp_nic_console_lock()
            ret, _ = self.mtp_nic_disp_ecc(slot)
            self.mtp_nic_console_unlock()
            self.mtp_single_j2c_unlock()

        self.mtp_mgmt_nic_diag_sys_clean()

        self._nic_ctrl_list[slot].mtp_exec_cmd("######## {:s} ########".format("END post dsp {:s} fail debug".format(test)))

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
            self.cli_log_slot_err_lock(slot, self.mtp_get_nic_err_msg(slot))
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_set_nic_status_fail(slot)
            return False

        return True


    def mtp_set_nic_vmarg(self, slot, vmarg):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Vmargin for Proto NIC")
            return True

        self.cli_log_slot_inf_lock(slot, "Set voltage margin to {:s}".format(vmarg))

        if not self._nic_ctrl_list[slot].nic_set_vmarg(vmarg):
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
        if nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2 or nic_type == NIC_Type.ORTANO2ADI:
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
        if nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2 or nic_type == NIC_Type.ORTANO2ADI:      
            msg = "NIC in performance mode"
            if not self._nic_ctrl_list[slot].nic_emmc_check_perf_mode():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
                self.mtp_dump_nic_err_msg(slot)
                return False
            self.cli_log_slot_inf_lock(slot, msg)
        return True

    def mtp_nic_fru_init(self, slot, init_date=True, nic_type=None):
        if init_date:
            msg = "Init NIC FRU info with date"
        else:
            msg = "Init NIC FRU info without date"

        dsp = "DIAG_INIT"
        sn = self.mtp_get_nic_sn(slot)
        test = "NIC_FRU_INIT"
        self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))
        start_ts = self.log_slot_test_start(slot, test)
        #self.cli_log_slot_inf_lock(slot, msg)

        if not self._nic_ctrl_list[slot].nic_fru_init(init_date, self._swmtestmode[slot]):
            #self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.cli_log_slot_err_lock(slot, self.mtp_get_nic_err_msg(slot))
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_set_nic_status_fail(slot)
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            return False

        duration = self.log_slot_test_stop(slot, test, start_ts)
        self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        return True

    def mtp_nic_ocp_adapter_fru_init(self, slot):
        if self.mtp_get_nic_type(slot) != NIC_Type.NAPLES25OCP:
            self.cli_log_slot_err(slot, "OCP Adapter FRU init function is not for type {:s}".format(self.mtp_get_nic_type(slot)))
            return False

        if not self._nic_ctrl_list[slot].nic_ocp_adapter_fru_init():
            self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
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

    def mtp_nic_sn_init(self, slot):
        if not self._nic_ctrl_list[slot]._sn:
            self._nic_ctrl_list[slot].nic_sn_init()
        self.mtp_set_nic_sn(slot, self._nic_ctrl_list[slot]._sn)

    def mtp_nic_pn_init(self, slot):
        if not self._nic_ctrl_list[slot]._pn:
            self._nic_ctrl_list[slot].nic_pn_init()
        self.mtp_set_nic_pn(slot, self._nic_ctrl_list[slot]._pn)

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
                        self.cli_log_slot_inf(slot, "==> Manufacture Vendor: {:s}".format(fru_info_list[4]))
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


    def mtp_nic_init(self):
        self.cli_log_inf("Init NICs in the MTP Chassis", level = 0)

        # init nic present list
        if not self.mtp_init_nic_type():
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


    def mtp_single_nic_diag_init(self, slot, emmc_format, emmc_check, fru_valid, vmargin, aapl, dis_hal, stop_on_err):
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

        if ret and not self.mtp_mgmt_copy_nic_diag(slot, emmc_format):
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            ret = False

        if ret and not self.mtp_mgmt_start_nic_diag(slot, aapl, dis_hal):
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            ret = False
        elif ret:
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

        if ret and not self.mtp_check_nic_cpld_partition(slot):
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            ret = False
        elif ret:
            duration = self.log_slot_test_stop(slot, test, start_ts)
            self.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration)) 
        # (DIAG_INIT, CPLD_DIAG) END           

        if ret and fru_valid:
            if emmc_format:
                init_date = False
            else:
                init_date = True
            if not self.mtp_nic_fru_init(slot, init_date, nic_type):
                ret = False
            fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
            if fru_info_list:
                self.mtp_set_nic_sn(slot, fru_info_list[0])
            else:
                self.cli_log_slot_err(slot, "Unable to load SN")
        elif not fru_valid:
            self.mtp_set_nic_sn(slot, self.mtp_get_nic_scan_sn(slot))

        if ret and not self.mtp_set_nic_vmarg(slot, vmargin):
            ret = False

        if ret and not self.mtp_nic_display_voltage(slot):
            ret = False
        
        duration = self.log_slot_test_stop(slot, "NIC_DIAG_INIT", start_ts)

        if not ret:
            libmfg_utils.post_fail_steps(self, slot)

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

    # def mtp_nic_mgmt_para_init(self, aapl, swm_lp=False, stop_on_err=False):
    #     nic_list = list()
    #     for slot in range(self._slots):
    #         if self._nic_prsnt_list[slot]:
    #             if not self.mtp_check_nic_status(slot):
    #                 self.cli_log_slot_err(slot, "Para Init NIC MGMT port bypassed for failed NIC")
    #                 if stop_on_err:
    #                     return False
    #                 else:
    #                     continue
    #             if not self.mtp_nic_boot_info_init(slot):
    #                 self.mtp_set_nic_status_fail(slot)
    #                 if stop_on_err:
    #                     return False
    #                 else:
    #                     continue
    #             nic_list.append(slot)

    #     if not nic_list:
    #         self.cli_log_err("No NICs passed")
    #         return False

    #     # parallel init mgmt/aapl
    #     cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
    #     if not self.mtp_mgmt_exec_cmd(cmd):
    #         self.cli_log_err("Execute command {:s} failed".format(cmd))
    #         return False

    #     nic_list_param = ",".join(str(slot+1) for slot in nic_list)
    #     if self._asic_support == MTP_ASIC_SUPPORT.ELBA or self._asic_support == MTP_ASIC_SUPPORT.TURBO_ELBA:
    #         asic_type = "elba"
    #     else:
    #         asic_type = "capri"
    #     sig_list = [MFG_DIAG_SIG.NIC_MGMT_PARA_SIG]
    #     if aapl:
    #         for slot in nic_list:
    #             self.cli_log_slot_inf(slot, "Para Init NIC MGMT/AAPL port")
    #         cmd = MFG_DIAG_CMDS.MTP_PARA_MGMT_AAPL_FMT.format(nic_list_param, asic_type)
    #     else:
    #         for slot in nic_list:
    #             self.cli_log_slot_inf(slot, "Para Init NIC MGMT port")
    #         cmd = MFG_DIAG_CMDS.MTP_PARA_MGMT_INIT_FMT.format(nic_list_param, asic_type)
    #         if swm_lp:
    #             cmd = "".join((cmd, " -swm_lp")) 

    #     if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
    #         self.cli_log_err("Execute command {:s} failed".format(cmd))
    #         return False
    #     if "failed" in self.mtp_get_cmd_buf():
    #         match = re.search("failed! *([0-9,]+)", self.mtp_get_cmd_buf())
    #         if match:
    #             for slot in libmfg_utils.expand_range_of_numbers(match.group(1), range_min=1, range_max=self._slots, dev=self._id):
    #                 slot = slot-1
    #                 self.cli_log_slot_err_lock(slot, "Para Init NIC MGMT failed")
    #                 self.mtp_set_nic_status_fail(slot)

    #     if not self.mtp_nic_mgmt_mac_refresh():
    #         return False

    #     return True

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
                if not self.mtp_mgmt_exec_cmd(cmd):
                    return False

                # time.sleep(5)
                cmd = MFG_DIAG_CMDS.MTP_NIC_PING_FMT.format(ipaddr)
                if not self.mtp_mgmt_exec_cmd(cmd):
                    return False

        return True


    def mtp_nic_diag_init(self, nic_list, emmc_format=False, emmc_check=False, fru_valid=True, sn_tag=False, fru_cfg=None, vmargin=Voltage_Margin.normal, aapl=False, swm_lp=False, nic_util=False, dis_hal=False, stop_on_err=False, skip_info_dump=False):
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
            ret = self.mtp_nic_mgmt_seq_init(nic_list, fpo, stop_on_err)
        else:
            ret = self.mtp_nic_mgmt_para_init(nic_list, aapl, swm_lp, stop_on_err)

        if not ret:
            return False

        if not self.mtp_mgmt_nic_mac_validate():
            return False

        if nic_util:
            # for QA only not DL: do mgmt para init but do emmc format. 
            emmc_format = True

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
                                                  stop_on_err))
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

        self.cli_log_inf("Init NIC Diag Environment complete\n", level = 0)
        return True

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
                self._nic_ctrl_list[slot].mtp_exec_cmd("#####  Power on NIC at {:s} #####".format(str(ts_record)))

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
            if self._nic_ctrl_list[slot] and self._nic_type_list[slot] == NIC_Type.ORTANO2ADI and not dl:
                if not self._nic_ctrl_list[slot].nic_set_i2c_after_pw_cycle():
                    self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
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
                self._nic_ctrl_list[slot].mtp_exec_cmd("##### Power off NIC at {:s} #####".format(str(ts_record)))

        self.cli_log_inf("Power off all NIC, wait {:02d} seconds for NIC power down".format(MTP_Const.NIC_POWER_OFF_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.NIC_POWER_OFF_DELAY)
        self.mtp_nic_unlock()
        return True


    def mtp_power_cycle_nic(self, slot_list=[], dl=False, count_down=True):
        rc = self.mtp_power_off_nic(slot_list)
        if not rc:
            return rc

        rc = self.mtp_power_on_nic(slot_list, dl, count_down)
        if not rc:
            return rc

    def mtp_init_nic_type(self):
        self._nic_type_list = [None] * self._slots      # reset nic types
        cmd = MFG_DIAG_CMDS.NIC_PRESENT_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to init NIC presence")
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False

        # find type
        self.cli_log_inf("Init NIC Present/Type")
        regex_dict = {
                      NIC_Type.NAPLES100:       MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100,
                      NIC_Type.NAPLES100IBM:    MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100IBM,
                      NIC_Type.NAPLES100HPE:    MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100HPE,
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
                      NIC_Type.ORTANO2ADI:      MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2ADI
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
                        self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)

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
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for Ortano")
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
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for Ortano ADI")
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

    def mtp_is_nic_ocp_dell(self, slot):
        """
         Differentiate OCP by PN
         - 68-0010: Dell version -> return True
         - P37689-001: HPE version -> return False
         - any other -> return False with err msg
        """
        if self._nic_type_list[slot] != NIC_Type.NAPLES25OCP:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for OCP")
            return False
        slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for OCP: ".format(slot_pn))
            return False
        nic_pn = re.match(PART_NUMBERS_MATCH.N25_OCP_DEL_PN_FMT, slot_pn)
        if nic_pn:
            return True
        else:
            return False

    def mtp_lookup_nic_swm_type(self, slot, slot_pn=None):
        """
         Differentiate SWM cards by PN

            PN : lookup
            -----------
            P26968-001 : NAPLES25SWM
            P41851-001 : P41851
            P46653-001 : P46653
            68-0016-XX XX : 68-0016
            68-0017-XX XX : 68-0016
            else : nic_type
        """
        if slot_pn is None:
            slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for SWM: ".format(slot_pn))
            return slot_pn

        if self._nic_type_list[slot] != NIC_Type.NAPLES25SWM:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for SWM")
            return slot_pn

        swm_skus = ("P26968", "P41851", "P46653", "68-0016", "68-0017")
        for sku in swm_skus:
            if sku in slot_pn:
                if sku == "P26968":
                    return "NAPLES25SWM"
                else:
                    return sku

    def mtp_is_nic_cloud(self, slot):
        if self._nic_type_list[slot] != NIC_Type.NAPLES100HPE:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for HPE")
            return False
        slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for HPE: ".format(slot_pn))
            return False
        nic_pn = re.match(PART_NUMBERS_MATCH.N100_HPE_CLD_PN_FMT, slot_pn)
        if nic_pn:
            return True
        else:
            return False


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

            # search for this PN in lib/libsku_cfg.py
            for pn_regex in self._valid_pn_list:
                pn_match = re.match(pn_regex, pn)
                if pn_match:
                    return True
            # end of search

            self.cli_log_slot_err(slot, "'{:s}' PN not valid for this script folder".format(pn))
            return False

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
            return False

        self.cli_log_slot_inf(slot, "Set NIC default diag boot")
        return True
        
    def mtp_mgmt_set_nic_mainfw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_mainfw_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with mainfw failed")
            return False

        self.cli_log_slot_inf(slot, "Set NIC default mainfw boot")
        return True

    def mtp_mgmt_set_nic_extos_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_extos_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with diag failed")
            return False

        self.cli_log_slot_inf(slot, "Set NIC default diag boot")
        return True


    def mtp_mgmt_nic_sw_shutdown(self, slot, software_pn):
        isCloud =  self.check_is_cloud_software_image(slot, software_pn)
        isRelC = True if software_pn in ("90-0013-0001", "90-0014-0001") else False
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


        if test == "PRBS_ETH":
            cmd = MFG_DIAG_CMDS.MTP_PARA_PRBS_ETH_TEST_FMT.format(nic_list_param, vmarg)
        elif test == "SNAKE_HBM":
            cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_HBM_FMT.format(nic_list_param, vmarg)
        elif test == "SNAKE_PCIE":
            cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_PCIE_FMT.format(nic_list_param, vmarg)
        elif test == "SNAKE_ELBA":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)

            if nic_type not in ELBA_NIC_TYPE_LIST:
                self.cli_log_err("Incorrect test for this NIC TYPE")
                return ["FAIL", nic_list[:]]
            elif nic_type == NIC_Type.ORTANO2:
                if self.mtp_is_nic_ortano_oracle(slot):
                    cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_ORC_FMT.format(nic_list_param, vmarg)
                else:
                    cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_PEN_FMT.format(nic_list_param, vmarg)
            elif nic_type == NIC_Type.ORTANO2ADI:
                if self.mtp_is_nic_ortanoadi_oracle(slot):
                    cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_ORC_FMT.format(nic_list_param, vmarg)
            elif nic_type == NIC_Type.LACONA32DELL or nic_type == NIC_Type.LACONA32:
                cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_LACONA_FMT.format(nic_list_param, vmarg)
            else:
                cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_FMT.format(nic_list_param, vmarg)

            # 2C/4C = internal loopback
            if vmarg != Voltage_Margin.normal or nic_type == NIC_Type.POMONTEDELL:
                cmd += " -int_lpbk"

        elif test == "ETH_PRBS":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)
            if nic_type not in ELBA_NIC_TYPE_LIST:
                self.cli_log_err("Incorrect test for this NIC TYPE")
                return ["FAIL", nic_list[:]]
            else:
                cmd = MFG_DIAG_CMDS.MTP_PARA_PRBS_ETH_ELBA_FMT.format(nic_list_param, vmarg)
                # 2C/4C = internal loopback
                if vmarg != Voltage_Margin.normal:
                    cmd += " -int_lpbk"
        elif test == "ARM_L1":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.POMONTEDELL:
                cmd = MFG_DIAG_CMDS.MTP_PARA_ARM_L1_ELBA_POMONTEDELL_FMT.format(nic_list_param, vmarg)
            else:
                cmd = MFG_DIAG_CMDS.MTP_PARA_ARM_L1_ELBA_FMT.format(nic_list_param, vmarg) 
        elif test == "PCIE_PRBS":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)
            cmd = MFG_DIAG_CMDS.MTP_PARA_PCIE_PRBS_FMT.format(nic_list_param, vmarg, "PRBS31")
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return ["FAIL", nic_list[:]]

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_TEST_TIMEOUT):
            self.cli_log_err("Run MTP Parallel Test {:s} Failed".format(test))
            return ["TIMEOUT", nic_list[:]]

        ret = "SUCCESS"

        match = re.findall(r"Slot (\d+) ?: +(\w+)", self.mtp_get_cmd_buf())
        for _slot, rslt in match:
            slot = int(_slot) - 1
            if (rslt != "PASS" and rslt != "PASSED") and slot not in nic_fail_list:
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
        if nic_type in ELBA_NIC_TYPE_LIST:
            if nic_type == NIC_Type.ORTANO2:
                if self.mtp_is_nic_ortano_oracle(slot):
                    preset_config = "5"
                else:
                    preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2ADI:
                preset_config = "5"
            elif nic_type == NIC_Type.POMONTEDELL:
                preset_config = "1"

        else:
            self.cli_log_slot_err_lock(slot, "Board config not supported on this NIC")
            return False

        if not self._nic_ctrl_list[slot].nic_set_board_config(preset_config):
            self.cli_log_slot_err_lock(slot, "Set board config failed")
            self.cli_log_slot_err_lock(slot, self.mtp_get_nic_err_msg(slot))
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
        elif nic_type == NIC_Type.POMONTEDELL:
            vdd_avs_cmd = MFG_DIAG_CMDS.POMONTEDELL_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.LACONA32DELL:
            vdd_avs_cmd = MFG_DIAG_CMDS.LACONA32DELL_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.LACONA32:
            vdd_avs_cmd = MFG_DIAG_CMDS.LACONA32_AVS_SET_FMT.format(sn, slot+1)
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
        if nic_type == NIC_Type.ORTANO2 or nic_type == NIC_Type.ORTANO2ADI:
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
                    self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
                    self.mtp_dump_nic_err_msg(slot)
                    continue

    def mtp_run_asic_l1_bash(self, slot=None, sn=None, mode=None, vmarg=Voltage_Margin.normal):
        """
        cd ~diag/scripts/asic/
        ./run_l1.test -sn <sn> -slot <slot> -m <mode> -v <vmarg>
        """
        rs = False

        nic_type = self.mtp_get_nic_type(slot)

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        self.mtp_mgmt_exec_cmd_para(slot, cmd)

        cmd = MFG_DIAG_CMDS.NIC_RUN_ASIC_L1_FMT.format(sn, slot+1, mode, vmarg)
        self.mtp_mgmt_exec_cmd_para(slot, cmd, timeout=MTP_Const.MTP_PARA_ASIC_L1_TEST_TIMEOUT)

        cmd_buf = self.mtp_get_nic_cmd_buf(slot)

        if MFG_DIAG_SIG.NIC_PARA_ASIC_L1_OK_SIG in cmd_buf:
            rs = True

        # kill the process in case it's hung/timed out
        # ctrl-c doesnt work
        # needs to be killed from separate session
        self.mtp_mgmt_exec_cmd_para(slot, "## killall run_l1.sh") # notify in log
        self.mtp_mgmt_exec_cmd("killall run_l1.sh") # use mtp session to kill it

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
            ts_record = "{:s} - at {:s}".format("RESET I2C HUB", str(ts))
            ts_record_cmd = "######## {:s} ########".format(ts_record)
            self.mtp_mgmt_exec_cmd(ts_record_cmd)

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
            ts_record = "{:s} - at {:s}".format("RESET I2C HUB", str(ts))
            ts_record_cmd = "######## {:s} ########".format(ts_record)
            self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)

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


    def mtp_run_diag_test_para(self, slot, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None):
        # init command
        if init_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, init_cmd):
                err_msg = self.mtp_get_nic_err_msg(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # run diag test
        if not self.mtp_mgmt_exec_cmd_para(slot, diag_cmd, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT):
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


    def mtp_barcode_scan(self, present_check=True, swmtestmode=Swm_Test_Mode.SWMALOM, no_slot=False):
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
        slot_num = 1

        # build all valid nic key list
        for slot in range(self._slots):
            key = libmfg_utils.nic_key(slot)
            valid_nic_key_list.append(key)
            if present_check and self._nic_prsnt_list[slot]:
                unscanned_nic_key_list.append(key)

        while True:
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
            self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
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
        if nic_type not in ELBA_NIC_TYPE_LIST:
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
            self.mtp_dump_err_msg(self.mtp_get_nic_err_msg(slot))
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
                        expected = expected[:PN_MINUS_REV_MASK]
                        received = received[:PN_MINUS_REV_MASK]
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
            self.cli_log_slot_err(slotA, self.mtp_get_nic_err_msg(slotA))
            self.mtp_dump_nic_err_msg(slotA)
            return False
        if not self._nic_ctrl_list[slotB].nic_console_enable_network_port():
            self.cli_log_slot_err(slotB, "Setup mgmt failed")
            self.cli_log_slot_err(slotB, self.mtp_get_nic_err_msg(slotB))
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
            self.cli_log_slot_err(slotA, self.mtp_get_nic_err_msg(slotA))
            self.mtp_dump_nic_err_msg(slotA)
            return False
        if not self._nic_ctrl_list[slotB].nic_console_disable_network_port():
            self.cli_log_slot_err(slotB, "Enable MTP port failed")
            self.cli_log_slot_err(slotB, self.mtp_get_nic_err_msg(slotB))
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

            ecc_errs = re.findall(r"(^.*orrectable.*$)", slot_buf)
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

        nic_type = self.mtp_get_nic_type(slot)

        if nic_type == NIC_Type.ORTANO2ADI:
            self.cli_log_slot_err(slot, "This function is not applicable for ADI card!")
            return False

        if console:
            if not self._nic_ctrl_list[slot].nic_console_vdd_ddr_check(d3_val, d4_val):
                if not self._nic_ctrl_list[slot].nic_console_vdd_ddr_fix(d3_val, d4_val):
                    self.cli_log_slot_err(slot, "Failed to set VDD_DDR margin")
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                if not self._nic_ctrl_list[slot].nic_console_vdd_ddr_check(d3_val, d4_val):
                    self.cli_log_slot_err(slot, "VDD_DDR values incorrect")
                    self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
                    return False
        else:
            if not self._nic_ctrl_list[slot].nic_vdd_ddr_check(d3_val, d4_val):
                if not self._nic_ctrl_list[slot].nic_vdd_ddr_fix(d3_val, d4_val):
                    self.cli_log_slot_err(slot, "Failed to set VDD_DDR margin")
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                if not self._nic_ctrl_list[slot].nic_vdd_ddr_check(d3_val, d4_val):
                    self.cli_log_slot_err(slot, "VDD_DDR values incorrect")
                    self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
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
            self.cli_log_slot_err(slot, self.mtp_get_nic_err_msg(slot))
            self.mtp_dump_nic_err_msg(slot)
            return False

        self.mtp_single_j2c_unlock()
        return True

    def mtp_nic_esec_write_protect(self, pass_nic_list=[], fail_nic_list=[], enable=False):
        nic_list = list()
        for slot in pass_nic_list:
            nic_type = self.mtp_get_nic_type(slot)
            if nic_type in ELBA_NIC_TYPE_LIST:
                nic_list.append(slot)

        if not nic_list:
            return True

        dsp = "DL"
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
                fail_nic_list.append(slot)
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
                    fail_nic_list.append(slot)
                    nic_list.remove(slot)
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
