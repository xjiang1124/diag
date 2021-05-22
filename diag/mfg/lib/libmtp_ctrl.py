import pexpect
import time
import os
import sys
import libmfg_utils
import re
import threading
from datetime import datetime
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_BYPASS_PSU_CHECK
from libmfg_cfg import MTP_INTERNAL_MGMT_IP_ADDR
from libmfg_cfg import MTP_INTERNAL_MGMT_NETMASK
from libmfg_cfg import NIC_MGMT_USERNAME
from libmfg_cfg import NIC_MGMT_PASSWORD
from libmfg_cfg import NAPLES_DISP_SN_FMT
from libmfg_cfg import NAPLES_DISP_MAC_FMT
from libmfg_cfg import NAPLES_DISP_PN_FMT
from libmfg_cfg import NAPLES_DISP_DATE_FMT
from libmfg_cfg import MFG_MTP_CPLD_IO_VERSION
from libmfg_cfg import MFG_MTP_CPLD_JTAG_VERSION
from libmfg_cfg import MFG_MTP_CPLD_IO_ELBA_VERSION
from libmfg_cfg import MFG_MTP_CPLD_JTAG_ELBA_VERSION
from libmfg_cfg import MFG_VALID_NIC_TYPE_LIST
from libmfg_cfg import MFG_PROTO_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import PART_NUMBERS_MATCH

from libdefs import NIC_Type
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

        self._nic_thread_list = [None] * self._slots
        # lock for nic cli
        self._lock = threading.Lock()
        # lock for parallel test run sequentially
        self._test_lock = threading.Lock()

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
        self._temppn = None


    def cli_log_inf(self, msg, level = 1):
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(cli_id_str + indent + msg)


    def cli_log_report_inf(self, msg):
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        prefix = "==> "
        postfix = " <=="
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + prefix + msg + postfix)
        else:
            libmfg_utils.cli_inf(cli_id_str + prefix + msg + postfix)


    def cli_log_err(self, msg, level = 1):
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_err(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_err(cli_id_str + indent + msg)


    def cli_log_slot_inf(self, slot, msg, level = 0):
        nic_cli_id_str = libmfg_utils.id_str(mtp = self._id, nic = slot)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(nic_cli_id_str + indent + msg)


    def cli_log_slot_err(self, slot, msg, level = 0):
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

        idx = handle.expect_exact(["PX2", "Schneider", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            self.cli_log_err("Need to add PX2 support")
            return False
        # Schneider apc
        elif idx == 1:
            handle.expect_exact(">")
            for port in port_list:
                handle.send("olOff " + port + "\r")
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

        idx = handle.expect_exact(["PX2", "Schneider", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            self.cli_log_err("Need to add PX2 support")
            return False
        # Schneider apc
        elif idx == 1:
            handle.expect_exact(">")
            for port in port_list:
                handle.send("olOn " + port + "\r")
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

        idx = handle.expect_exact(["PX2", "Schneider", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            self.cli_log_err("Need to add PX2 support")
            return False
        # Schneider apc
        elif idx == 1:
            handle.expect_exact(">")
            for port in port_list:
                handle.send("olOff " + port + "\r")
                handle.expect_exact(">")
            time.sleep(1)
            for port in port_list:
                handle.send("olOn " + port + "\r")
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


    def mtp_nic_para_session_init(self):
        userid = self._mgmt_cfg[1]
        for slot in range(self._slots):
            handle = self.mtp_session_create()
            if handle:
                if not self.mtp_prompt_cfg(handle, userid, "$", slot):
                    self.cli_log_err("Unable to config MTP session")
                    return False
                prompt = "{:s}@NIC-{:02d}:".format(userid, slot+1) + "$"
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


    def mtp_mgmt_connect(self, prompt_cfg=False, prompt_id=None):
        delay = 30
        retries = self._mgmt_timeout / delay
        retries = retries + 4
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

    def mtp_nic_send_ctrl_c(self, slot):
        if self._nic_ctrl_list[slot] == None:
            # script not running anything.
            return True
        if not self._nic_ctrl_list[slot].nic_send_ctrl_c():
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            self.cli_log_slot_err(slot, "Couldn't send C+C")
            return False
        return True

    def mtp_mgmt_set_date(self, timestamp_str):
        cmd = MFG_DIAG_CMDS.NIC_DATE_SET_FMT.format(timestamp_str)
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
        match = re.findall(r"MTP_TYPE=MTP_([a-zA-Z]{4}.?)", self.mtp_get_cmd_buf())
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
        for sig in sig_list:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, [sig], timeout)
            if idx < 0:
                rc = False
                break
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [self._mgmt_prompt], timeout)

        # signature match fails
        if not rc or idx < 0:
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
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list)
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
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list)
        if rc:
            self.cli_log_inf("FAN present test passed")
        else:
            self.cli_log_err("FAN present test failed")
            return rc

        # Fan speed test
        cmd = MFG_DIAG_CMDS.MTP_FAN_TEST_FMT
        pass_sig_list = [MFG_DIAG_SIG.MTP_FAN_OK_SIG]
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list)
        if rc:
            self.cli_log_inf("FAN speed test passed")
        else:
            self.cli_log_err("FAN speed test failed")
            return rc

        # Fan speed set
        self.cli_log_inf("Set FAN Speed to {:d}%".format(fan_spd))
        cmd = MFG_DIAG_CMDS.MTP_FAN_SET_SPD_FMT.format(fan_spd)
        rc = self.mtp_mgmt_exec_cmd(cmd)
        if not rc:
            self.cli_log_err("Failed to set fan speed to {:d}%".format(fan_spd))

        self._fanspd = fan_spd          # update class variable

        # Fan status dump
        cmd = MFG_DIAG_CMDS.MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            rc = False

        return rc


    def mtp_diag_pre_init(self, diagmgr_logfile):
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

        # start the mtp diagmgr
        diagmgr_handle = self.mtp_session_create()
        if not diagmgr_handle:
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = MFG_DIAG_CMDS.MTP_DIAG_MGR_START_FMT.format(diagmgr_logfile)
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
                if stage == FF_Stage.FF_DL:
                    # CPLD and diagfw images. Failsafe image for Elba cards
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
            for card_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
                if stage == FF_Stage.FF_DL:
                    # CPLD and diagfw images
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
                        if card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2:
                            img = NIC_IMAGES.fail_cpld_img[card_type]
                            if img.strip() == "":
                                raise KeyError
                            img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing failsafe cpld image for {:s}".format(card_type))
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
                        if card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2:
                            expected_timestamp = NIC_IMAGES.fail_cpld_dat[card_type]
                            if expected_timestamp.strip() == "":
                                raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing failsafe cpld timestamp for {:s}".format(card_type))
                        pass
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


    def mtp_hw_init(self, fan_spd):
        """
         Elba cards need higher fan_spd
         40% -> 50%     : elba LT, NT
         90% -> 100%    : elba HT
         max = 100%
        """
        if self._asic_support == "ELBA":
            fan_spd = min(100, fan_spd + 20)
        rc = True

        self.cli_log_inf("Start MTP chassis sanity check", level = 0)
        # mtp cpld test
        rc &= self.mtp_cpld_test()
        # fan init
        rc &= self.mtp_fan_init(fan_spd)

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
            upper_limit = low_threshold + MTP_Const.MFG_EDVT_TEMP_DIFF
            lower_limit = low_threshold - MTP_Const.MFG_EDVT_TEMP_DIFF
        elif high_threshold != None:
            self.cli_log_inf("Wait the environment temperature rise to {:2.2f}".format(high_threshold))
            upper_limit = high_threshold + MTP_Const.MFG_EDVT_TEMP_DIFF
            lower_limit = high_threshold - MTP_Const.MFG_EDVT_TEMP_DIFF
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
        io_version = MFG_MTP_CPLD_IO_VERSION
        jtag_version = MFG_MTP_CPLD_JTAG_VERSION
        if self._asic_support.startswith("ELBA"):
            io_version = MFG_MTP_CPLD_IO_ELBA_VERSION
            jtag_version = MFG_MTP_CPLD_JTAG_ELBA_VERSION

        if int(cpld_ver_list[0],16) < int(io_version,16):
            self.cli_log_err("MTP IO CPLD Version: {:s}, expect: {:s}".format(cpld_ver_list[0], io_version))
            self.cli_log_err("MTP CPLD test failed")
            return False

        if cpld_ver_list[1] != jtag_version:
            self.cli_log_err("MTP JTAG CPLD Version: {:s}, expect: {:s}".format(cpld_ver_list[1], jtag_version))
            self.cli_log_err("MTP CPLD test failed")
            return False
        self.cli_log_inf("MTP CPLD test passed")
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
            return None

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
            return None

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
        logfile_exp = r"(cap|elb)_l1_screen_board_{:s}.*log".format(sn)
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


########################################
######  NIC CTRL Routines ##############
########################################

# 1. Routines that need console, can not be run in parallel
    def mtp_nic_boot_info_init(self, slot):
        self.cli_log_slot_inf(slot, "Init NIC boot info")
        if not self._nic_ctrl_list[slot].nic_boot_info_init():
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            self.cli_log_slot_err(slot, "Init NIC boot info failed")
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
            err_msg = self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_err_msg(err_msg)
            return False
        return True

    def mtp_nic_sw_mode_switch_verify(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_mode_switch_verify():
            err_msg = self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_err_msg(err_msg)
            return False
        return True

    def mtp_nic_sw_profile(self, slot, profile):
        return self._nic_ctrl_list[slot].nic_sw_profile(profile)


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
        self.cli_log_slot_inf(slot, "Init NIC MGMT port")
        if not self._nic_ctrl_list[slot].nic_mgmt_init(fpo):
            # retry
            if not self.mtp_nic_mgmt_reinit(slot):
                self.cli_log_slot_err(slot, "Init NIC MGMT port failed")
                return False

        # delete the arp entry
        ipaddr = libmfg_utils.get_nic_ip_addr(slot)
        cmd = MFG_DIAG_CMDS.MTP_ARP_DELET_FMT.format(ipaddr)
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            return False
        # ping to update the arp cache
        for x in range(2):
            time.sleep(5)
            cmd = MFG_DIAG_CMDS.MTP_NIC_PING_FMT.format(ipaddr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                return False

        return True


    def mtp_nic_mini_init(self, slot, fpo=False):
        if not self.mtp_nic_boot_info_init(slot):
            return False

        if not self.mtp_nic_mgmt_init(slot, fpo):
            return False

        return True


    def mtp_mgmt_test_nic_mem(self, slot):
        if not self._nic_ctrl_list[slot].nic_test_mem():
            return False
        else:
            return True

    def mtp_check_nic_jtag(self, slot):
        if not self._nic_ctrl_list[slot].nic_check_jtag(self._asic_support):
            return False
        else:
            return True

# 2. Routines that need smb bus, can not be run in parallel
    def mtp_mgmt_check_nic_pwr_status(self, slot):
        if not self._nic_ctrl_list[slot].nic_power_check():
            err_msg = self._nic_ctrl_list[slot].nic_get_cmd_buf()
            self.mtp_dump_err_msg(err_msg)
            return False

        return True


    def mtp_mgmt_dump_nic_pll_sta(self, slot):
        reg_data_list = self._nic_ctrl_list[slot].nic_get_pll_sta()
        if not reg_data_list:
            self.cli_log_slot_err(slot, "Failed to extract ASIC PLL status")
            self.cli_log_err(self._nic_ctrl_list[slot].nic_get_cmd_buf())
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
    def mtp_power_on_single_nic(self, slot):
        self.cli_log_slot_inf(slot, "Power on NIC, wait {:02d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY))
        if not self._nic_ctrl_list[slot].nic_power_on():
            self.cli_log_slot_err(slot, "Failed to power on NIC")
            return False

        return True


    def mtp_power_off_single_nic(self, slot):
        self.cli_log_slot_inf(slot, "Power off NIC, wait {:02d} seconds for NIC power down".format(MTP_Const.NIC_POWER_OFF_DELAY))
        if not self._nic_ctrl_list[slot].nic_power_off():
            self.cli_log_slot_err(slot, "Failed to power off NIC")
            return False
        return True


# 4. Routines use mgmt port, can be run in parallel
    def mtp_mgmt_exec_cmd_para(self, slot, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        rc = self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout)
        if not rc:
            err_msg = self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_err_msg(err_msg)
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
            return False
        if not self._nic_ctrl_list[slot].nic_disp_2nd_fru():
            self.cli_log_slot_err_lock(slot, "Display SMB NIC FRU failed")
            return False
        if not self._nic_ctrl_list[slot].nic_disp_fru():
            self.cli_log_slot_err_lock(slot, "Display NIC FRU failed")
            return False
        return True

    def mtp_program_nic_alom_fru(self, slot, date, alom_sn, alom_pn):
        self.cli_log_slot_inf_lock(slot, "Program NIC ALOM FRU date={:s}, alom_sn={:s}, alom_pn={:s}".format(date, alom_sn, alom_pn))
        if not self._nic_ctrl_list[slot].nic_program_alom_fru(date, alom_sn, alom_pn):
            self.cli_log_slot_err_lock(slot, "Program NIC ALOM FRU failed")
            return False
        return True

    def mtp_dump_nic_fru(self, slot, expect_sn="", expect_mac="", expect_pn=""):
        if not self._nic_ctrl_list[slot].nic_dump_fru(expect_mac=expect_mac):
            self.cli_log_slot_err_lock(slot, "Dump ASIC FRU failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        if not self._nic_ctrl_list[slot].mtp_nic_dump_fru(expect_mac=expect_mac):
            self.cli_log_slot_err_lock(slot, "Dump SMB FRU failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
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
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
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


    #Check the SWI scanned in software part number to see if it's a cloud image or not.
    #Cloud images have slight deviation on how SWI runs
    def check_is_cloud_software_image(self, slot, software_pn):
        print(" Check if software image is cloud: {:s}".format(software_pn))            
        if ((software_pn == "90-0004-0001") or (software_pn == "90-0006-0001") or (software_pn == "90-0006-0002") or (software_pn == "90-0011-0001")):
            return True
        return False
            
    #Check if the loaded image correct for the cards p/n.  i.e. cloud card gets a cloud image, 
    #and etnerprise card get an enterprise image
    def check_swi_software_image(self, slot, software_pn):
        naples_pn = self._nic_ctrl_list[slot].nic_get_naples_pn()
        if not naples_pn:
            self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Retreive PN Failed")
            return False
        self.cli_log_slot_inf_lock(slot, "==> Check SOFTWARE IMAGE PN {:s}    CARD PN {:s} ".format(software_pn, naples_pn))   
        if naples_pn[0:7] == "68-0003":        #NAPLES 100 PENSANDO
            if software_pn != "90-0002-0003":
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
        elif naples_pn[0:7] == "68-0005":    #NAPLES25 PENSANDO
            if software_pn != "90-0002-0005":
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
        elif (naples_pn[0:7] == "68-0016") or (naples_pn[0:7] == "68-0017"):     #NAPLES25 SWM PENSANDO
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
        elif naples_pn[0:7] == "68-0010":     #NAPLES25 OCP PENSANDO
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
        elif naples_pn[0:7] == "68-0023":     #NAPLES25 OCP DELL
            if software_pn != "90-0002-0007":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif ((naples_pn[0:7] == "68-0007") or (naples_pn[0:7] == "68-0009") or (naples_pn[0:7] == "68-0011")):      #FORIO/VOMERO/VOMERO2
            if software_pn != "90-0003-0001":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0015":     #ORTANO
            if software_pn != "90-0009-0002":
                self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Software Image match to nic part number failed")
                return False
        elif naples_pn[0:7] == "68-0021":     #ORTANO PENSANDO
            if software_pn != "90-0011-0001":
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
        '''
        return True

    def mtp_get_alom_fru(self, slot):
        return self._nic_ctrl_list[slot].alom_get_fru()

    def mtp_setting_partition(self, slot):
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

    def mtp_program_nic_cpld(self, slot, cpld_img):
        # check the current cpld version
        cpld_has_timestamp = 1
        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed, can not retrieve CPLD info")
            return False
        cur_ver = nic_cpld_info[0]
        cur_timestamp = nic_cpld_info[1]
        nic_type = self.mtp_get_nic_type(slot)
        try:
            expected_version = NIC_IMAGES.cpld_ver[nic_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD version for {:s}".format(nic_type))
            return False
        try:
            expected_timestamp = NIC_IMAGES.cpld_dat[nic_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD timestamp for {:s}".format(nic_type))
            return False

        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip CPLD update for Proto NIC")
            return True

        if cur_ver == expected_version and cur_timestamp == expected_timestamp:
            self.cli_log_slot_inf_lock(slot, "NIC CPLD is up-do-date")
            return True

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
            return False

        return True

    def mtp_program_nic_failsafe_cpld(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if not nic_type == NIC_Type.ORTANO and not nic_type == NIC_Type.ORTANO2:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no failsafe CPLD for {:s}".format(nic_type))
            return False
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip failsafe CPLD update for Proto NIC")
            return True

        # can't check the version without loading backup partition into the running partition
        self.cli_log_slot_inf(slot, "Skip checking failsafe CPLD version")

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "cfg1"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
            return False

        return True

    def mtp_program_nic_cpld_feature_row(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if not nic_type == NIC_Type.ORTANO2:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no feature row for {:s}".format(nic_type))
            return False
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "No feature row update for Proto NIC")
            return True

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "fea"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD feature row failed")
            return False

        return True

    def mtp_refresh_nic_cpld(self, slot, dontwait=False):
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

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img):
            self.cli_log_slot_err_lock(slot, "Program NIC Secure CPLD failed")
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
        if not nic_type == NIC_Type.ORTANO2:
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
            err_msg = self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_err_msg(err_msg)
            return False
        
        fea_nic_hex = self._nic_ctrl_list[slot].nic_get_info("hexdump -C /home/diag/cplddump")
        if not fea_nic_hex:
            err_msg = self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_err_msg(err_msg)
            return False
        fea_nic_match = re.search(fea_regex,fea_nic_hex)

        if fea_mtp_match and fea_nic_match:
            if fea_mtp_match.group(1) == fea_nic_match.group(1):
                return True
            self.cli_log_slot_err_lock(slot, "Feature row programmed incorrectly. Dump doesn't match original file.")
            return False
        self.cli_log_slot_err_lock(slot, "Unable to dump feature row.")
        return False

    def mtp_check_nic_cpld_partition(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if not nic_type == NIC_Type.ORTANO2:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no cpld partition for {:s}".format(nic_type))
            return False

        if not self._nic_ctrl_list[slot].nic_check_cpld_partition():
            err_msg = self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_err_msg(err_msg)
            return False

        return True

    def mtp_program_nic_efuse(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type != NIC_Type.ORTANO2:
            return False

        if not self._nic_ctrl_list[slot].nic_program_efuse():
            self.cli_log_slot_err(slot, "Program NIC Efuse failed")
            self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        self._nic_ctrl_list[slot].nic_program_sec_key_dump()
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

        self._nic_ctrl_list[slot].nic_program_sec_key_dump()
        return True

    def mtp_verify_nic_cpld(self, slot, sec_cpld=False):
        cpld_has_timestamp = 1
        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Verify NIC CPLD failed, can not retrieve CPLD info")
            return False

        cur_ver = nic_cpld_info[0]
        cur_timestamp = nic_cpld_info[1]
        nic_type = self.mtp_get_nic_type(slot)

        try:
            expected_version = NIC_IMAGES.cpld_ver[nic_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD version for {:s}".format(nic_type))
            return False
        try:
            expected_timestamp = NIC_IMAGES.cpld_dat[nic_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD timestamp for {:s}".format(nic_type))
            return False
        if sec_cpld:
            try:
                expected_version = NIC_IMAGES.sec_cpld_ver[nic_type]
            except KeyError:
                self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD version for {:s}".format(nic_type))
                return False
            try:
                expected_timestamp = NIC_IMAGES.sec_cpld_dat[nic_type]
            except KeyError:
                self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD timestamp for {:s}".format(nic_type))
                return False

        if cur_ver != expected_version or cur_timestamp != expected_timestamp:
                self.cli_log_slot_err_lock(slot, "Verify NIC CPLD Failed")
                self.cli_log_slot_err_lock(slot, "Expect Version: {:s}, get: {:s}".format(expected_version, cur_ver))
                self.cli_log_slot_err_lock(slot, "Expect Timestamp: {:s}, get: {:s}".format(expected_timestamp, cur_timestamp))
                return False

        return True

    def mtp_program_nic_qspi(self, slot, qspi_img):
        if not self._nic_ctrl_list[slot].nic_program_qspi(qspi_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC QSPI failed")
            return False
        return True
        
    def mtp_copy_nic_gold(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_copy_gold(gold_img):
            self.cli_log_slot_inf_lock(slot, "Copy NIC goldfw failed")
            return False
            
        return True

    def mtp_program_nic_gold(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_program_gold(gold_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC goldfw failed")
            return False

        if not self.mtp_mgmt_set_nic_gold_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True
    def mtp_program_nic_gold_naples100(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_program_gold_naples100(gold_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC goldfw failed")
            return False

        if not self.mtp_mgmt_set_nic_gold_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
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
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing diagfw timestamp for {:s}".format(nic_type))
            return False

        if ( boot_image != "diagfw" ):
            self.cli_log_slot_err_lock(slot, "Checking Boot Image is Diagfw Failed, NIC is booted from {:s}".format(boot_image))
            return False

        if ( expected_timestamp != kernel_timestamp ):
            self.cli_log_slot_err_lock(slot, "Diagfw Verify Failed, Expect: {:s}   Read: {:s}".format(expected_timestamp, kernel_timestamp))
            return False

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
            return False

        return True
        
    def mtp_program_nic_emmc_ibm(self, slot, emmc_img):
        if not self._nic_ctrl_list[slot].nic_program_emmc_ibm(emmc_img):
            self.cli_log_slot_err_lock(slot, "Program NIC EMMC failed")
            return False

        if not self.mtp_mgmt_set_nic_sw_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True
    def mtp_program_nic_emmc_naples100(self, slot, emmc_img):
        if not self._nic_ctrl_list[slot].nic_program_emmc_naples100(emmc_img):
            self.cli_log_slot_err_lock(slot, "Program NIC EMMC failed")
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
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        return True


    def mtp_mgmt_save_nic_logfile(self, slot, logfile_list):
        if not self._nic_ctrl_list[slot].nic_save_logfile(logfile_list):
            self.cli_log_slot_err_lock(slot, "Save NIC Logfile failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        return True


    def mtp_mgmt_save_nic_diag_logfile(self, slot, aapl):
        if not self._nic_ctrl_list[slot].nic_save_diag_logfile(aapl):
            self.cli_log_slot_err_lock(slot, "Save NIC Diag Logfile failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        return True
    def mtp_mgmt_nic_diag_sys_clean(self, slot):
        self.cli_log_slot_inf_lock(slot, "NIC Diag Sys Clean")
        if not self._nic_ctrl_list[slot].nic_diag_clean():
            self.cli_log_slot_err_lock(slot, "NIC Diag Sys Clean failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        return True


    def mtp_mgmt_start_nic_diag(self, slot, aapl):
        if aapl:
            msg = "Start NIC Diag with HAL"
        else:
            msg = "Start NIC Diag without HAL"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_start_diag(aapl):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            return False

        return True


    def mtp_set_nic_vmarg(self, slot, vmarg):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Vmargin for Proto NIC")
            return True

        if vmarg > 0:
            vmarg_param = "high"
        elif vmarg == 0:
            vmarg_param = "normal"
        else:
            vmarg_param = "low"
        self.cli_log_slot_inf_lock(slot, "Set voltage margin to {:s}".format(vmarg_param))

        if not self._nic_ctrl_list[slot].nic_set_vmarg(vmarg_param):
            self.cli_log_slot_err_lock(slot, "Set voltage margin to {:s} failed".format(vmarg_param))
            return False

        return True

    def mtp_nic_display_voltage(self, slot):
        if not self._nic_ctrl_list[slot].nic_display_voltage():
            self.cli_log_slot_err_lock(slot, "Voltage display failed")
            return False

        return True

    def mtp_nic_emmc_init(self, slot, emmc_format=False):
        nic_type = self.mtp_get_nic_type(slot)
        if emmc_format:
            msg = "Format and Init NIC EMMC"
        else:
            msg = "Init NIC EMMC"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_init_emmc(emmc_format):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
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
        if nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
            msg = "Set NIC in performance mode"
            if not self._nic_ctrl_list[slot].nic_emmc_set_perf_mode():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
                err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
                self.mtp_dump_err_msg(err_msg)
                return False
            self.cli_log_slot_inf_lock(slot, msg)
        return True

    def mtp_nic_emmc_check_perf_mode(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
            msg = "NIC in performance mode"
            if not self._nic_ctrl_list[slot].nic_emmc_check_perf_mode():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
                err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
                self.mtp_dump_err_msg(err_msg)
                return False
            self.cli_log_slot_inf_lock(slot, msg)
        return True

    def mtp_nic_fru_init(self, slot, init_date=True, nic_type=None):
        if init_date:
            msg = "Init NIC FRU info with date"
        else:
            msg = "Init NIC FRU info without date"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_fru_init(init_date, self._swmtestmode[slot]):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.mtp_dump_err_msg(self.mtp_get_nic_err_msg(slot))
            return False

        return True


    def mtp_nic_cpld_init(self, slot):
        self.cli_log_slot_inf_lock(slot, "Init NIC CPLD info")
        if not self._nic_ctrl_list[slot].nic_cpld_init():
            self.cli_log_slot_err_lock(slot, "Init NIC CPLD failed")
            return False

        return True


    def mtp_mgmt_set_nic_sw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_sw_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default sw boot")
        return True


    def mtp_mgmt_set_nic_gold_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_gold_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default gold boot failed")
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


    def mtp_nic_info_disp(self, fru_valid=True):
        self.cli_log_inf("MTP NIC Info Dump:")
        for slot, prsnt, nic_type in zip(range(self._slots), self._nic_prsnt_list, self._nic_type_list):
            if prsnt:
                self.cli_log_slot_inf(slot, "NIC is Present, Type is: {:s}".format(nic_type))
                if fru_valid:
                    fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
                    if not fru_info_list:
                        self.cli_log_slot_err_lock(slot, "Retrieve NIC FRU failed")
                    else:
                        self.cli_log_slot_inf(slot, "==> Manufacture Vendor: {:s}".format(fru_info_list[4]))
                        self.cli_log_slot_inf(slot, "==> FRU: {:s}, {:s}, {:s}".format(fru_info_list[0],fru_info_list[1],fru_info_list[2]))
                        if fru_info_list[3]:
                            self.cli_log_slot_inf(slot, "==> FRU Program Date: {:s}".format(fru_info_list[3]))
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
    def mtp_nic_scan_fru_validate(self):
        for slot in range(self._slots):
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


    def mtp_single_nic_diag_init(self, slot, emmc_format, fru_valid, vmargin, aapl):
        nic_type = self.mtp_get_nic_type(slot)
        if not self.mtp_check_nic_status(slot):
            return

        if not self.mtp_nic_emmc_init(slot, emmc_format):
            return

        if not self.mtp_mgmt_copy_nic_diag(slot, emmc_format):
            return

        if not self.mtp_mgmt_start_nic_diag(slot, aapl):
            return

        if not self.mtp_nic_cpld_init(slot):
            return

        if fru_valid:
            if emmc_format:
                init_date = False
            else:
                init_date = True
            if not self.mtp_nic_fru_init(slot, init_date, nic_type):
                return
            fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
            self.mtp_set_nic_sn(slot, fru_info_list[0])
        else:
            self.mtp_set_nic_sn(slot, self.mtp_get_nic_scan_sn(slot))

        if not self.mtp_set_nic_vmarg(slot, vmargin):
            return

        if not self.mtp_nic_display_voltage(slot):
            return

        return


    # pre setup for the diag test
    def mtp_nic_diag_init_pre(self):
        fail_list = list()
        self.cli_log_inf("NIC Diag Setup started", level = 0)
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                if not self.mtp_nic_pcie_poll_enable(slot, False):
                    fail_list.append(slot)
        self.cli_log_inf("NIC Diag Setup complete\n", level = 0)
        return fail_list


    # cleanup for the diag test
    def mtp_nic_diag_init_post(self):
        fail_list = list()
        self.cli_log_inf("NIC Diag Cleanup started", level = 0)
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                if not self.mtp_nic_pcie_poll_enable(slot, True):
                    fail_list.append(slot)
        self.cli_log_inf("NIC Diag Cleanup complete\n", level = 0)
        return fail_list


    def mtp_nic_mgmt_seq_init(self, fpo):
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                self.mtp_nic_mini_init(slot, fpo)


    def mtp_nic_mgmt_para_init(self, aapl, swm_lp=False):
        nic_list = list()
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                self.mtp_nic_boot_info_init(slot)
                nic_list.append(slot)

        # parallel init mgmt/aapl
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        asic_type = "elba" if self._asic_support == "ELBA" else "capri"
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

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        if not self.mtp_nic_mgmt_mac_refresh():
            return False

        return True


    def mtp_nic_mgmt_mac_refresh(self):
        # delete the arp entry
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                ipaddr = libmfg_utils.get_nic_ip_addr(slot)
                cmd = MFG_DIAG_CMDS.MTP_ARP_DELET_FMT.format(ipaddr)
                if not self.mtp_mgmt_exec_sudo_cmd(cmd):
                    return False

                ###Have seen failures on Naples25SWM where ping fails and ARP table is not populated
                ###Add a 2nd ping try as a work around.   
                for x in range(2):
                    time.sleep(5)
                    # ping to update the arp cache
                    cmd = MFG_DIAG_CMDS.MTP_NIC_PING_FMT.format(ipaddr)
                    if not self.mtp_mgmt_exec_cmd(cmd):
                        return False

                

        return True


    def mtp_nic_diag_init(self, emmc_format=False, fru_valid=True, sn_tag=False, fru_cfg=None, vmargin=0, aapl=False, swm_lp=False, nic_util=False):
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
            self.mtp_nic_mgmt_seq_init(fpo)
        else:
            self.mtp_nic_mgmt_para_init(aapl, swm_lp)

        if not self.mtp_mgmt_nic_mac_validate():
            return False

        if nic_util:
            # for QA only not DL: do mgmt para init but do emmc format. 
            emmc_format = True

        nic_thread_list = list()
        for slot in range(self._slots):
            if not self._nic_prsnt_list[slot]:
                continue
            nic_thread = threading.Thread(target = self.mtp_single_nic_diag_init,
                                          args = (slot,
                                                  emmc_format,
                                                  fru_valid,
                                                  vmargin,
                                                  aapl))
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
            if not self.mtp_nic_scan_fru_validate():
                return False

        self.mtp_nic_info_disp(fru_valid)

        self.cli_log_inf("Init NIC Diag Environment complete\n", level = 0)
        return True

    def mtp_single_nic_emmc_reformat(self, slot, nic_rslt_list, emmc_format=True):
        if not self.mtp_nic_emmc_init(slot, emmc_format):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Failed to re-initialize EMMC")
            nic_rslt_list[slot] = False
            return

        if not self.mtp_mgmt_copy_nic_diag(slot, emmc_format):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Failed to copy diag")
            nic_rslt_list[slot] = False
            return

        if not self._nic_ctrl_list[slot].mtp_exec_cmd("sync"):
            err_msg = self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_err_msg(err_msg)
            return

    def mtp_nic_emmc_reformat(self, nic_rslt_list, nic_list, emmc_format=True):
        """
          copy of mtp_nic_diag_init(), but without the FRU, CPLD inits.
          re-init emmc after a desctructive emmc test, to prepare for next stage.
        """
        self.mtp_nic_mgmt_para_init(aapl=False)
        if not self.mtp_mgmt_nic_mac_validate():
            return False

        nic_thread_list = list()
        for slot in nic_list:
            nic_type = self.mtp_get_nic_type(slot)
            if not (nic_type == NIC_Type.ORTANO2 or nic_type == NIC_Type.ORTANO):
                continue
            if not self._nic_prsnt_list[slot]:
                continue
            nic_thread = threading.Thread(target = self.mtp_single_nic_emmc_reformat,
                                          args = (slot, nic_rslt_list, emmc_format))
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

        return nic_rslt_list

    # check if any duplicate mac address in the internal network
    def mtp_mgmt_nic_mac_validate(self):
        self.cli_log_inf("NIC MAC address validate started")
        mac_addr_reg_exp = r"([a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2})"
        cmd = MFG_DIAG_CMDS.MTP_NIC_MAC_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to validate NIC MAC address")
            return False

        match = re.findall(mac_addr_reg_exp, self.mtp_get_cmd_buf())
        if match:
            for mac in match:
                if match.count(mac) > 1:
                    self.cli_log_err("NIC MAC address validate failed - duplicate entry: {:s}".format(mac))
                    return False
            self.cli_log_inf("NIC MAC address validate complete - {:d} entries found".format(len(match)))
            return True
        else:
            self.cli_log_err("NIC MAC address validate failed - 0 entry found")
            return False


    def mtp_power_on_nic(self):
        cmd = MFG_DIAG_CMDS.MTP_POWER_ON_NIC_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to power on NIC")
            return False

        self.cli_log_inf("Power on all NIC, wait {:02d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.NIC_POWER_ON_DELAY)
        return True


    def mtp_power_off_nic(self):
        cmd = MFG_DIAG_CMDS.MTP_POWER_OFF_NIC_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to power off NIC")
            return False

        self.cli_log_inf("Power off all NIC, wait {:02d} seconds for NIC power down".format(MTP_Const.NIC_POWER_OFF_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.NIC_POWER_OFF_DELAY)
        return True


    def mtp_power_cycle_nic(self):
        rc = self.mtp_power_off_nic()
        if not rc:
            return rc

        rc = self.mtp_power_on_nic()
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
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES100
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES100)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100IBM, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES100IBM
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES100IBM)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100HPE, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES100HPE
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES100HPE)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES25
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_FORIO, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.FORIO
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.FORIO)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_VOMERO, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.VOMERO
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.VOMERO)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_VOMERO2, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.VOMERO2
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.VOMERO2)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWM, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES25SWM
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25SWM)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25OCP, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES25OCP
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25OCP)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWMDELL, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES25SWMDELL
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25SWMDELL)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWM833, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES25SWM833
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25SWM833)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.ORTANO
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.ORTANO)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.ORTANO2
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.ORTANO2)
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
        return self._nic_type_list[slot] in self._valid_type_list


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


    def mtp_mgmt_nic_sw_shutdown(self, slot, software_pn):
        isCloud =  self.check_is_cloud_software_image(slot, software_pn)
        if not self._nic_ctrl_list[slot].nic_sw_shutdown(isCloud):
            self.cli_log_slot_err(slot, "Graceful shut down NIC failed")
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            return False

        return True

    def mtp_mgmt_nic_sw_cleanup_shutdown(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_cleanup_shutdown():
            self.cli_log_slot_err(slot, "Graceful clean up shut down NIC failed")
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            return False

        return True

    def mtp_mgmt_set_elba_uboot_env(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_elba_uboot_env(slot):
            self.cli_log_slot_err(slot, "Setup uboot env variables failed")
            return False
        return True

    def mtp_check_nic_status(self, slot):
        return self._nic_ctrl_list[slot].nic_check_status()


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


    def mtp_mgmt_pre_post_diag_check(self, intf, slot, vmarg=0):
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


    def mtp_mgmt_run_test_mtp_para(self, test, nic_list, vmarg):
        nic_fail_list = list()

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return nic_list[:]

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.MTP_PARA_TEST_SIG]


        if test == "PRBS_ETH":
            cmd = MFG_DIAG_CMDS.MTP_PARA_PRBS_ETH_TEST_FMT.format(nic_list_param, vmarg)
        elif test == "SNAKE_HBM":
            cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_HBM_FMT.format(nic_list_param, vmarg)
        elif test == "SNAKE_PCIE":
            cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_PCIE_FMT.format(nic_list_param, vmarg)
        elif test == "SNAKE_ELBA":
            if self.mtp_is_nic_ortano_oracle(nic_list[0]):
                cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_ORC_FMT.format(nic_list_param, vmarg)
            else:
                cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_ELBA_PEN_FMT.format(nic_list_param, vmarg)
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return nic_list[:]

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_TEST_DELAY):
            self.cli_log_err("Run MTP Parallel Test {:s} Failed".format(test))
            return nic_list[:]

        match = re.findall(r"Slot (\d+) ?: +(\w+)", self.mtp_get_cmd_buf())
        for _slot, rslt in match:
            slot = int(_slot) - 1
            if rslt != "PASS" and slot not in nic_fail_list:
                nic_fail_list.append(slot)

        return nic_fail_list


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

        # log the timestamp in diag log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(test, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self._nic_ctrl_list[slot].mtp_exec_cmd(ts_record_cmd)

        if not self._nic_ctrl_list[slot].mtp_exec_cmd(diag_cmd, timeout=MTP_Const.DIAG_TEST_TIMEOUT):
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

        # log the timestamp in diag log
        stop = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(test, str(stop), str(stop-start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self._nic_ctrl_list[slot].mtp_exec_cmd(ts_record_cmd)

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
        ret = self.mtp_mgmt_get_test_result(rslt_cmd, test)
        if test == "L1" and ret == "TIMEOUT":
            self.mtp_run_diag_test_para_lock()
            self.mtp_mgmt_jtag_rst()
            self.mtp_run_diag_test_para_unlock()

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
        if nic_type == NIC_Type.ORTANO2:
            if self.mtp_is_nic_ortano_oracle(slot):
                preset_config = "5"
            else:
                preset_config = "8"
            if not self._nic_ctrl_list[slot].nic_set_board_config(preset_config):
                self.cli_log_slot_err_lock(slot, "Set board config failed")
                err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
                self.mtp_dump_err_msg(err_msg)
                return False
        else:
            self.cli_log_slot_err_lock(slot, "Need to QA this card")
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
        else:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
            return False

        if vdd_avs_cmd:
            self.mtp_mgmt_set_nic_avs_pre(slot)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(vdd_avs_cmd, timeout=MTP_Const.NIC_AVS_SET_DELAY):
                self.cli_log_slot_err(slot, "Timed out: Failed to execute command {:s}".format(vdd_avs_cmd))
                self.mtp_mgmt_set_nic_avs_post(slot)
                return False
            if not self.mtp_mgmt_dump_avs_info(slot, self.mtp_get_nic_cmd_buf(slot)):
                self.cli_log_slot_err(slot, "SET VDD AVS FAILED")
                return False
        if arm_avs_cmd:
            self.mtp_mgmt_set_nic_avs_pre(slot)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(arm_avs_cmd, timeout=MTP_Const.NIC_AVS_SET_DELAY):
                self.cli_log_slot_err(slot, "Timed out: Failed to execute command {:s}".format(arm_avs_cmd))
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

    def mtp_nic_fix_vrm(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.ORTANO2:
            if not self._nic_ctrl_list[slot].nic_fix_vrm():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(MFG_DIAG_CMDS.ORTANO2_VRM_FIX_FMT))
                err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
                self.mtp_dump_err_msg(err_msg)
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


    def mtp_run_diag_test_para_lock(self):
        self._test_lock.acquire()


    def mtp_run_diag_test_para_unlock(self):
        self._test_lock.release()


    def mtp_run_diag_test_para(self, slot, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None):
        # init command
        if init_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, init_cmd):
                err_msg = self.mtp_get_nic_err_msg(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # log the timestamp in diag log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(test, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)

        # run diag test
        if not self.mtp_mgmt_exec_cmd_para(slot, diag_cmd, timeout=MTP_Const.DIAG_TEST_TIMEOUT):
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

        # log the timestamp in diag log
        stop = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(test, str(stop), str(stop-start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)

        # post command
        if post_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, post_cmd):
                err_msg = self.mtp_get_nic_err_msg(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        ret = self.mtp_mgmt_get_test_result_para(slot, rslt_cmd, test)
        return [ret, err_msg_list]


    def mtp_barcode_scan(self, present_check=True, swmtestmode=Swm_Test_Mode.SWMALOM):
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
            raw_scan = raw_input(usr_prompt)

            if raw_scan == "STOP":
                if present_check and len(unscanned_nic_key_list) != 0:
                    self.cli_log_err("{:s} have not scanned yet".format(unscanned_nic_list_cli_str), level=0)
                    continue
                else:
                    break
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
                while True:
                    usr_prompt = "Please Scan {:s} Serial Number Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    sn = libmfg_utils.serial_number_validate(raw_scan)
                    if not sn:
                        self.cli_log_err("Invalid NIC Serial Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                        #return None
                    elif sn in scan_sn_list:
                        self.cli_log_err("NIC Serial Number: {:s} is double scanned, please restart the scan process\n".format(sn), level=0)
                        #return None
                    else:
                        scan_sn_list.append(sn)
                        break

                #Scan Mac Loop
                while True:
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
                        break

                #Scan PN Loop
                while True:
                    usr_prompt = "Please scan {:s} Part Number Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    pn = libmfg_utils.part_number_validate(raw_scan)
                    if not pn:
                        self.cli_log_err("Invalid NIC Part Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                        #return None
                    else:
                        break
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

            nic_scan_rslt["NIC_VALID"] = True
            nic_scan_rslt["NIC_SN"] = sn
            nic_scan_rslt["NIC_MAC"] = mac
            nic_scan_rslt["NIC_PN"] = pn
            nic_scan_rslt["NIC_TS"] = libmfg_utils.get_fru_date()
            if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
                nic_scan_rslt["SN_ALOM"] = alom_sn
                nic_scan_rslt["PN_ALOM"] = alom_pn
            mtp_scan_rslt[key] = nic_scan_rslt

        nic_empty_list = list(set(valid_nic_key_list).difference(set(scan_nic_key_list)))
        for key in nic_empty_list:
            nic_scan_rslt = dict()
            nic_scan_rslt["NIC_VALID"] = False
            mtp_scan_rslt[key] = nic_scan_rslt

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

            if scan_rslt[key]["NIC_VALID"]:
                tmp = "        VALID: \"Yes\""
                config_lines.append(tmp)
                tmp = "        SN: \"" + scan_rslt[key]["NIC_SN"] + "\""
                config_lines.append(tmp)
                tmp = "        MAC: \"" + scan_rslt[key]["NIC_MAC"] + "\""
                config_lines.append(tmp)
                tmp = "        PN: \"" + scan_rslt[key]["NIC_PN"] + "\""
                config_lines.append(tmp)
                tmp = "        TS: \"" + scan_rslt[key]["NIC_TS"] + "\""
                config_lines.append(tmp)
                pn = scan_rslt[key]["NIC_PN"]
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
