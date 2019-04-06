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
from libmfg_cfg import MFG_NAPLES100_CPLD_VERSION
from libmfg_cfg import MFG_NAPLES100_CPLD_TIMESTAMP
from libmfg_cfg import MFG_NAPLES100_QSPI_TIMESTAMP
from libmfg_cfg import MFG_NAPLES25_CPLD_VERSION
from libmfg_cfg import MFG_NAPLES25_CPLD_TIMESTAMP
from libmfg_cfg import MFG_NAPLES25_QSPI_TIMESTAMP
from libmfg_cfg import MFG_NIC_FRU_PROGRAM
from libmfg_cfg import MFG_NIC_CPLD_PROGRAM
from libmfg_cfg import MFG_NIC_QSPI_PROGRAM
from libmfg_cfg import MFG_NIC_EMMC_PROGRAM

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

from libnic_ctrl import nic_ctrl

class mtp_ctrl():
    def __init__(self, mtpid, filep, diag_log_filep, diag_nic_log_filep_list, diag_cmd_log_filep=None, ts_cfg = None, mgmt_cfg = None, apc_cfg = None, dbg_mode = False):
        self._id = mtpid
        self._ts_handle = None
        self._mgmt_handle = None
        self._mgmt_prompt = None
        self._mgmt_timeout = MTP_Const.MTP_POWER_ON_TIMEOUT
        self._ts_cfg = ts_cfg
        self._mgmt_cfg = mgmt_cfg
        self._apc_cfg = apc_cfg
        self._prompt_list = libmfg_utils.get_linux_prompt_list()
        self._slots = 10
        self._fans = 3
        self._status = MTP_Status.MTP_STA_POWEROFF

        self._nic_ctrl_list = [None] * self._slots
        self._nic_type_list = [None] * self._slots
        self._nic_prsnt_list = [False] * self._slots
        self._nic_scan_prsnt_list = [False] * self._slots
        self._nic_sn_list = [None] * self._slots
        self._nic_scan_sn_list = [None] * self._slots

        self._nic_thread_list = [None] * self._slots
        self._lock = threading.Lock()

        self._debug_mode = dbg_mode
        self._filep = filep
        self._cmd_buf = None
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._diag_nic_filep_list = diag_nic_log_filep_list[:]


    def cli_log_inf(self, msg, level = 1):
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(cli_id_str + indent + msg)


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
            handle.close()
            time.sleep(1)
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False


    def _mtp_single_apc_pwr_on(self, apc, userid, passwd, port_list):
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
        idx = libmfg_utils.mfg_expect(handle, ["assword:"], timeout = 5)
        if idx < 0:
            self.cli_log_err("Can not connect to mtp, check the console.\n", level = 0)
            return None
        else:
            handle.sendline(passwd)

        idx = libmfg_utils.mfg_expect(handle, self._prompt_list, timeout = 5)
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


    def mtp_mgmt_connect(self):
        retries = self._mgmt_timeout / 30
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
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["assword:"], timeout = 5)
            if idx < 0:
                if retries > 0:
                    self.cli_log_inf("Connect to mtp timeout, wait 30s and retry...", level = 0)
                    time.sleep(30)
                    retries -= 1
                    self._mgmt_handle = pexpect.spawn(ssh_cmd)
                    continue
                else:
                    self.cli_log_err("Connect to mtp failed\n", level = 0)
                    return None
            else:
                self._mgmt_handle.sendline(passwd)
                break

        idx = libmfg_utils.mfg_expect(self._mgmt_handle, self._prompt_list, timeout = 5)
        if idx < 0:
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
        return self._mgmt_prompt


    def mtp_prompt_cfg(self, handle, userid, prompt, slot=None):
        handle.sendline("stty rows 50 cols 160")
        idx = libmfg_utils.mfg_expect(handle, [prompt])
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            return False

        if slot != None:
            handle.sendline("PS1='\u@NIC-{:02d}:{:s} '".format(slot+1, prompt))
        else:
            handle.sendline("PS1='\u@MTP:{:s} '".format(prompt))
        idx = libmfg_utils.mfg_expect_re(handle, [r"{:s}.*{:s}".format(userid, prompt)])
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
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
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            return False

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


    def mtp_get_hw_version(self):
        reg_addr = 0x0
        cmd = MFG_DIAG_CMDS.MTP_CPLD_READ_FMT.format(reg_addr)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get MTP IO-CPLD image version info", level = 0)
            return None
        match = re.findall(r"addr 0x{:x} with data (0x[0-9a-fA-F]+)".format(reg_addr), self.mtp_get_cmd_buf())
        if match:
            io_cpld_ver = match[0]
        else:
            self.cli_log_err("Failed to get MTP IO-CPLD image version info", level = 0)
            return None

        reg_addr = 0x19
        cmd = MFG_DIAG_CMDS.MTP_CPLD_READ_FMT.format(reg_addr)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get MTP JTAG-CPLD image version info", level = 0)
            return None
        match = re.findall(r"addr 0x{:x} with data (0x[0-9a-fA-F]+)".format(reg_addr), self.mtp_get_cmd_buf())
        if match:
            jtag_cpld_ver = match[0]
        else:
            self.cli_log_err("Failed to get MTP JTAG-CPLD image version info", level = 0)
            return None

        return [io_cpld_ver, jtag_cpld_ver]


    def mtp_get_sw_version(self):
        cmd = MFG_DIAG_CMDS.MTP_DIAG_VERSION_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get diag image version", level = 0)
            return None
        match = re.findall(r"Date: +(.*20\d{2})", self.mtp_get_cmd_buf())
        if match:
            return match[0]
        else:
            self.cli_log_err("Failed to get diag image version", level = 0)
            return None


    def mtp_get_asic_version(self):
        cmd = MFG_DIAG_CMDS.MTP_ASIC_VERSION_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get asic util version", level = 0)
            return None
        match = re.findall(r"Date: +(.*20\d{2})", self.mtp_get_cmd_buf())
        if match:
            return match[0]
        else:
            self.cli_log_err("Failed to get asic util version", level = 0)
            return None


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

        cmd = "mkdir -p {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH)
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


    def mtp_power_cycle(self):
        self.mtp_mgmt_poweroff()
        self.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC\n".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        self.cli_log_inf("Power off APC", level=0)
        self.mtp_apc_pwr_off()
        time.sleep(MTP_Const.MTP_POWER_CYCLE_DELAY)
        self.mtp_apc_pwr_on()
        self.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up\n".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)


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

        self.cli_log_inf("Init NIC Connections", level = 0)
        ret = self.mtp_nic_para_session_init()
        if not ret:
            self.cli_log_err("Init NIC Connections Failed", level = 0)
            return False

        self.cli_log_inf("Pre Diag SW Environment Init complete\n", level=0)

        return True


    def mtp_diag_post_init(self, mtp_capability):
        self.cli_log_inf("Post Diag SW Environment Init", level=0)
        cmd = "rm -f {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to remove previous ASIC test logfile", level=0)
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
        nic_firmware_cfg_file = os.path.abspath("config/nic_firmware_cfg.yaml")
        nic_fw_cfg = libmfg_utils.load_cfg_from_yaml(nic_firmware_cfg_file)
        if mtp_capability & 0x1:
            naples100_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["CPLD_FILE"]
            naples100_qspi_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["QSPI_FILE"]
            naples100_emmc_img_file = nic_fw_cfg[NIC_Type.NAPLES100]["EMMC_FILE"]
            cmd = "ls {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd), level=0)
                return False
            cmd_buf = self.mtp_get_cmd_buf()

            for img_file in [naples100_cpld_img_file, naples100_qspi_img_file, naples100_emmc_img_file]:
                if not os.path.basename(img_file) in cmd_buf:
                    self.cli_log_err("Firmware {:s} doesn't exist".format(img_file), level=0)
                    self.mtp_dump_err_msg(cmd_buf)
                    return False

        if mtp_capability & 0x2:
            naples25_cpld_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["CPLD_FILE"]
            naples25_qspi_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["QSPI_FILE"]
            naples25_emmc_img_file = nic_fw_cfg[NIC_Type.NAPLES25]["EMMC_FILE"]
            cmd = "ls {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd), level=0)
                return False
            cmd_buf = self.mtp_get_cmd_buf()

            for img_file in [naples25_cpld_img_file, naples25_qspi_img_file, naples25_emmc_img_file]:
                if not os.path.basename(img_file) in cmd_buf:
                    self.cli_log_err("Firmware {:s} doesn't exist".format(img_file), level=0)
                    self.mtp_dump_err_msg(cmd_buf)
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
        rc = True

        self.cli_log_inf("Start MTP chassis sanity check", level = 0)
        # mtp cpld test
        rc &= self.mtp_cpld_test()
        # mtp sensor test
        rc &= self.mtp_inlet_sensor_test()
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
            if not inlet:
                return False
            self.cli_log_inf("Current Environment temperature is {:2.2f}".format(inlet))
            self.cli_log_inf("No threshold set, bypass ambient temperature check")
            return True

        timeout = MTP_Const.MFG_TEMP_WAIT_TIMEOUT
        while timeout > 0:
            inlet = self.mtp_get_inlet_temp(low_threshold, high_threshold)
            if not inlet:
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

        # Soaking process
        if GLB_CFG_MFG_TEST_MODE:
            timeout = MTP_Const.MFG_TEMP_SOAK_TIMEOUT
        else:
            timeout = MTP_Const.MFG_MODEL_TEMP_SOAK_TIMEOUT
        self.cli_log_inf("Start soaking process, wait for {:d} seconds".format(timeout * MTP_Const.MFG_TEMP_CHECK_INTERVAL))
        libmfg_utils.count_down(timeout)

        self.cli_log_inf("Soaking process complete, current inlet reading is {:2.2f}".format(inlet))

        return True


    def mtp_cpld_test(self):
        cpld_ver_list = self.mtp_get_hw_version()
        if not cpld_ver_list:
            self.cli_log_err("Unable to retrieve MTP CPLD version")
            self.cli_log_err("MTP CPLD test failed")
            return False

        if cpld_ver_list[0] != MFG_MTP_CPLD_IO_VERSION:
            self.cli_log_err("MTP IO CPLD Version: {:s}, expect: {:s}".format(cpld_ver_list[0], MFG_MTP_CPLD_IO_VERSION))
            self.cli_log_err("MTP CPLD test failed")
            return False

        if cpld_ver_list[1] != MFG_MTP_CPLD_JTAG_VERSION:
            self.cli_log_err("MTP JTAG CPLD Version: {:s}, expect: {:s}".format(cpld_ver_list[1], MFG_MTP_CPLD_JTAG_VERSION))
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
            # if the difference is more than 5, something is wrong, relay on any inlet near the threshold
            if inlet_diff > 5.0:
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP Inlet sensor test failed")
                return False
            else:
                self.cli_log_inf("MTP Inlet sensor test passed")
                return True
        else:
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP Inlet sensor test failed")
            return False


    def mtp_get_inlet_temp(self, low_threshold, high_threshold):
        cmd = MFG_DIAG_CMDS.MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
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
            # if the difference is more than 5, something is wrong, relay on any inlet near the threshold
            if inlet_diff > 5.0:
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
        else:
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("Unable to get inlet temperature")
            return None


    # return list of error message
    def mtp_mgmt_retrieve_nic_l1_err(self, sn):
        err_msg_list = list()
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR
        logfile_exp = r"cap_l1_screen_board_{:s}.*log".format(sn)
        for filename in os.listdir(path):
            if re.match(logfile_exp, filename):
                with open(os.path.join(path, filename), 'r') as f:
                    for line in f:
                        if MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG in line:
                            err_msg = line.replace('\n', '')
                            err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG):]
                            err_msg_list.append(err_msg)
        return err_msg_list


    # return list of error message
    def mtp_mgmt_retrieve_mtp_para_err(self, sn, test):
        err_msg_list = list()
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR

        if test == "PRBS_ETH":
            filename = "{:s}_prbs_eth.log".format(sn)
        elif test == "SNAKE_HBM":
            filename = "{:s}_snake_hbm.log".format(sn)
        elif test == "SNAKE_PCIE":
            filename = "{:s}_snake_pcie.log".format(sn)
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return err_msg_list

        with open(os.path.join(path, filename), 'r') as f:
            for line in f:
                if MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG in line:
                    err_msg = line.replace('\n', '')
                    err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG):]
                    err_msg_list.append(err_msg)
        return err_msg_list


########################################
######  NIC CTRL Routines ##############
########################################

# 1. Routines that need console, can not be run in parallel
    def mtp_nic_con_baudrate_init(self, slot):
        self.cli_log_slot_inf(slot, "Init NIC console baudrate")
        if not self._nic_ctrl_list[slot].nic_console_init():
            self.cli_log_slot_err(slot, "Init NIC console baudrate failed")
            return False

        return True


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


    def mtp_nic_mgmt_init(self, slot, fru_valid):
        self.cli_log_slot_inf(slot, "Init NIC MGMT port")
        if not self._nic_ctrl_list[slot].nic_mgmt_init(fru_valid):
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            self.cli_log_slot_err(slot, "Init NIC MGMT port failed")
            return False

        # delete the arp entry
        ipaddr = libmfg_utils.get_nic_ip_addr(slot)
        cmd = MFG_DIAG_CMDS.MTP_ARP_DELET_FMT.format(ipaddr)
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            return False
        # ping to update the arp cache
        cmd = MFG_DIAG_CMDS.MTP_NIC_PING_FMT.format(ipaddr)
        if not self.mtp_mgmt_exec_cmd(cmd):
            return False

        return True


    def mtp_nic_emmc_init(self, slot, emmc_format=False):
        self.cli_log_slot_inf(slot, "Init NIC EMMC")
        if not self._nic_ctrl_list[slot].nic_init_emmc(emmc_format):
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            self.cli_log_slot_err(slot, "Init NIC EMMC failed")
            return False

        return True


    def mtp_nic_mini_init(self, slot, fru_valid=True):
        if not self.mtp_nic_con_baudrate_init(slot):
            return False

        if not self.mtp_nic_boot_info_init(slot):
            return False

        if not self.mtp_nic_mgmt_init(slot, fru_valid):
            return False

        return True


    def mtp_mgmt_test_nic_mem(self, slot):
        if not self._nic_ctrl_list[slot].nic_test_mem():
            return False
        else:
            return True


# 2. Routines that need smb bus, can not be run in parallel
    def mtp_mgmt_check_nic_pwr_status(self, slot):
        self.cli_log_slot_inf(slot, "Check NIC Power Status")
        if not self._nic_ctrl_list[slot].nic_power_check():
            err_msg = self._nic_ctrl_list[slot].nic_get_cmd_buf()
            self.mtp_dump_err_msg(err_msg)
            return False

        self.cli_log_slot_inf(slot, "Check NIC Power Status passed")
        return True


    def mtp_mgmt_dump_nic_pll_sta(self, slot):
        reg_data_list = self._nic_ctrl_list[slot].nic_get_capri_pll_sta()
        if not reg_data_list:
            self.cli_log_slot_err(slot, "Failed to extract Capri PLL status")
            return

        reg26_data = reg_data_list[0]
        self.cli_log_slot_inf(slot, "CPLD 0x26 = {:x}".format(reg26_data))
        core_pll_lock = reg26_data & 0x1
        cpu_pll_lock = reg26_data & 0x2
        flash_pll_lock = reg26_data & 0x4
        proto_mode = reg26_data & 0x20
        if not core_pll_lock:
            self.cli_log_slot_err(slot, "Capri core pll is not locked")
        if not cpu_pll_lock:
            self.cli_log_slot_err(slot, "Capri cpu pll is not locked")
        if not flash_pll_lock:
            self.cli_log_slot_err(slot, "Capri flash pll is not locked")
        if proto_mode:
            self.cli_log_slot_err(slot, "Capri proto mode is set")

        reg28_data = reg_data_list[1]
        self.cli_log_slot_inf(slot, "CPLD 0x28 = {:x}".format(reg28_data))
        pcie_pll_lock = reg28_data & 0x40
        if not pcie_pll_lock:
            self.cli_log_slot_err(slot, "Capri pcie pll is not locked")


# 3. Routines that need spi bus, can not be run in parallel
    def mtp_power_on_single_nic(self, slot):
        self.cli_log_slot_inf(slot, "Power on NIC, wait {:03d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY))
        if not self._nic_ctrl_list[slot].nic_power_on():
            self.cli_log_slot_err(slot, "Failed to power on NIC")
            return False

        return True


    def mtp_power_off_single_nic(self, slot):
        self.cli_log_slot_inf(slot, "Power off NIC, wait {:03d} seconds for NIC power down".format(MTP_Const.NIC_POWER_OFF_DELAY))
        if not self._nic_ctrl_list[slot].nic_power_off():
            self.cli_log_slot_err(slot, "Failed to power off NIC")
            return False
        self.cli_log_slot_inf(slot, "Power off NIC")
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
        if MFG_NIC_FRU_PROGRAM:
            self.cli_log_slot_inf_lock(slot, "Program NIC FRU date={:s}, sn={:s}, mac={:s}, pn={:s}".format(date, sn, mac, pn))
            if not self._nic_ctrl_list[slot].nic_program_fru(date, sn, mac, pn):
                self.cli_log_slot_err_lock(slot, "Program NIC FRU failed")
                return False
            self.cli_log_slot_inf_lock(slot, "Program NIC FRU complete")
        else:
            self.cli_log_slot_inf_lock(slot, "Program NIC FRU bypassed")
        return True


    def mtp_verify_nic_fru(self, slot, sn, mac, pn):
        if MFG_NIC_FRU_PROGRAM:
            self.cli_log_slot_inf_lock(slot, "Verify NIC FRU sn={:s}, mac={:s}, pn={:s}".format(sn, mac, pn))
            nic_fru_info = self._nic_ctrl_list[slot].nic_get_fru()
            if not nic_fru_info:
                self.cli_log_slot_err_lock(slot, "Verify NIC FRU Failed, can not retrieve FRU content")
                return False

            nic_sn = nic_fru_info[0]
            nic_mac = nic_fru_info[1]
            nic_pn = nic_fru_info[2]
            if nic_sn != sn:
                self.cli_log_slot_err_lock(slot, "SN Verify Failed, get {:s}, expect {:s}".format(nic_sn, sn))
                return False
            if nic_mac != mac:
                self.cli_log_slot_err_lock(slot, "MAC Verify Failed, get {:s}, expect {:s}".format(nic_mac, mac))
                return False
            if nic_pn != pn:
                self.cli_log_slot_err_lock(slot, "PN Verify Failed, get {:s}, expect {:s}".format(nic_pn, pn))
                return False

            return True
        else:
            return True


    def mtp_program_nic_cpld(self, slot, cpld_img):
        if MFG_NIC_CPLD_PROGRAM:
            self.cli_log_slot_inf_lock(slot, "Program NIC CPLD")

            # check the current cpld version
            nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
            if not nic_cpld_info:
                self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed, can not retrieve CPLD info")
                return False
            cur_ver = nic_cpld_info[0]
            cur_timestamp = nic_cpld_info[1]
            nic_type = self.mtp_get_nic_type(slot)

            if nic_type == NIC_Type.NAPLES100:
                if cur_ver == MFG_NAPLES100_CPLD_VERSION and cur_timestamp == MFG_NAPLES100_CPLD_TIMESTAMP:
                    self.cli_log_slot_inf_lock(slot, "NIC CPLD is up-do-date")
                    return True
            elif nic_type == NIC_Type.NAPLES25:
                if cur_ver == MFG_NAPLES25_CPLD_VERSION and cur_timestamp == MFG_NAPLES25_CPLD_TIMESTAMP:
                    self.cli_log_slot_inf_lock(slot, "NIC CPLD is up-do-date")
                    return True
            else:
                self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
                return False

            if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img):
                self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
                return False
            self.cli_log_slot_inf_lock(slot, "Program NIC CPLD complete")
        else:
            self.cli_log_slot_inf_lock(slot, "Program NIC CPLD bypassed")
        return True


    def mtp_verify_nic_cpld(self, slot):
        if MFG_NIC_CPLD_PROGRAM:
            self.cli_log_slot_inf_lock(slot, "Verify NIC CPLD")
            nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
            if not nic_cpld_info:
                self.cli_log_slot_err_lock(slot, "Verify NIC CPLD failed, can not retrieve CPLD info")
                return False

            cur_ver = nic_cpld_info[0]
            cur_timestamp = nic_cpld_info[1]
            nic_type = self.mtp_get_nic_type(slot)

            if nic_type == NIC_Type.NAPLES100:
                if cur_ver != MFG_NAPLES100_CPLD_VERSION or cur_timestamp != MFG_NAPLES100_CPLD_TIMESTAMP:
                    self.cli_log_slot_err_lock(slot, "Verify NIC CPLD Failed")
                    self.cli_log_slot_err_lock(slot, "Expect Version: {:s}, get: {:s}".format(MFG_NAPLES100_CPLD_VERSION, cur_ver))
                    self.cli_log_slot_err_lock(slot, "Expect Timestamp: {:s}, get: {:s}".format(MFG_NAPLES100_CPLD_TIMESTAMP, cur_timestamp))
                    return False
                else:
                    self.cli_log_slot_inf_lock(slot, "Verify NIC CPLD complete")
                    return True
            elif nic_type == NIC_Type.NAPLES25:
                if cur_ver != MFG_NAPLES25_CPLD_VERSION or cur_timestamp != MFG_NAPLES25_CPLD_TIMESTAMP:
                    self.cli_log_slot_err_lock(slot, "Verify NIC CPLD Failed")
                    self.cli_log_slot_err_lock(slot, "Expect Version: {:s}, get: {:s}".format(MFG_NAPLES25_CPLD_VERSION, cur_ver))
                    self.cli_log_slot_err_lock(slot, "Expect Timestamp: {:s}, get: {:s}".format(MFG_NAPLES25_CPLD_TIMESTAMP, cur_timestamp))
                    return False
                else:
                    self.cli_log_slot_inf_lock(slot, "Verify NIC CPLD complete")
                    return True
            else:
                self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
                return False

        return True


    def mtp_program_nic_qspi(self, slot, qspi_img):
        nic_type = self.mtp_get_nic_type(slot)
        if MFG_NIC_QSPI_PROGRAM or nic_type == NIC_Type.NAPLES25:
            self.cli_log_slot_inf_lock(slot, "Program NIC QSPI")
            if not self._nic_ctrl_list[slot].nic_program_qspi(qspi_img):
                self.cli_log_slot_inf_lock(slot, "Program NIC QSPI failed")
                return False
            self.cli_log_slot_inf_lock(slot, "Program NIC QSPI complete")
        else:
            self.cli_log_slot_inf_lock(slot, "Program NIC QSPI bypassed")
        return True


    def mtp_verify_nic_qspi(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if MFG_NIC_QSPI_PROGRAM or nic_type == NIC_Type.NAPLES25:
            self.cli_log_slot_inf_lock(slot, "Verify NIC QSPI")
            qspi_info = self._nic_ctrl_list[slot].nic_get_boot_info()
            if not qspi_info:
                self.cli_log_slot_err_lock(slot, "Fail to retrieve NIC boot info")
                return False

            boot_image = qspi_info[0]
            kernel_timestamp = qspi_info[1]
            nic_type = self.mtp_get_nic_type(slot)

            if boot_image != "diagfw":
                self.cli_log_slot_err_lock(slot, "NIC is booted from {:s}".format(boot_image))
                return False

            if nic_type == NIC_Type.NAPLES100:
                if kernel_timestamp != MFG_NAPLES100_QSPI_TIMESTAMP:
                    self.cli_log_slot_err_lock(slot, "Verify NIC QSPI Failed")
                    self.cli_log_slot_err_lock(slot, "Expect: {:s}, get: {:s}".format(MFG_NAPLES100_QSPI_TIMESTAMP, kernel_timestamp))
                    return False
                else:
                    self.cli_log_slot_inf(slot, "Verify NIC QSPI complete")
                    return True
            elif nic_type == NIC_Type.NAPLES25:
                if kernel_timestamp != MFG_NAPLES25_QSPI_TIMESTAMP:
                    self.cli_log_slot_err_lock(slot, "Verify NIC QSPI Failed")
                    self.cli_log_slot_err_lock(slot, "Expect: {:s}, get: {:s}".format(MFG_NAPLES25_QSPI_TIMESTAMP, kernel_timestamp))
                    return False
                else:
                    self.cli_log_slot_inf_lock(slot, "Verify NIC QSPI complete")
                    return True
            else:
                self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
                return False

        return True


    def mtp_program_single_nic_emmc(self, slot, emmc_img, nic_rslt_list):
        self.cli_log_slot_inf_lock(slot, "Program NIC EMMC")
        if not self._nic_ctrl_list[slot].nic_program_emmc(emmc_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC EMMC failed")
            return

        if not self.mtp_mgmt_set_nic_sw_boot(slot):
            return

        self.cli_log_slot_inf_lock(slot, "Program NIC EMMC complete")
        nic_rslt_list[slot] = True
        return


    def mtp_program_nic_emmc(self, nic_list, emmc_img):
        fail_list = list()
        nic_thread_list = list()
        nic_rslt_list = [False] * self._slots

        for slot in nic_list:
            nic_thread = threading.Thread(target = self.mtp_program_single_nic_emmc,
                                          args = (slot, emmc_img, nic_rslt_list))
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)

        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    ret = nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(5)

        for slot in nic_list:
            if not nic_rslt_list[slot]:
                fail_list.append(slot)

        return fail_list


    def mtp_mgmt_copy_nic_diag(self, slot):
        self.cli_log_slot_inf_lock(slot, "Copy NIC Diag Image")
        if not self._nic_ctrl_list[slot].nic_copy_diag_img():
            self.cli_log_slot_err_lock(slot, "Copy NIC Diag Image failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        return True


    def mtp_mgmt_save_nic_logfile(self, slot, logfile_list):
        self.cli_log_slot_inf_lock(slot, "Save NIC Logfile")
        if not self._nic_ctrl_list[slot].nic_save_logfile(logfile_list):
            self.cli_log_slot_err_lock(slot, "Save NIC Logfile failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        return True


    def mtp_mgmt_start_nic_diag(self, slot):
        self.cli_log_slot_inf_lock(slot, "Start NIC Diag")
        if not self._nic_ctrl_list[slot].nic_start_diag():
            self.cli_log_slot_err_lock(slot, "Start NIC Diag failed")
            return False

        return True


    def mtp_set_nic_vmarg(self, slot, vmarg):
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

        self.cli_log_slot_inf_lock(slot, "Set voltage margin to {:s} complete".format(vmarg_param))
        return True


    def mtp_nic_fru_init(self, slot):
        self.cli_log_slot_inf_lock(slot, "Init NIC FRU info")
        if not self._nic_ctrl_list[slot].nic_fru_init():
            self.cli_log_slot_err_lock(slot, "Init NIC FRU failed")
            return False

        return True


    def mtp_nic_cpld_init(self, slot):
        self.cli_log_slot_inf_lock(slot, "Init NIC CPLD info")
        if not self._nic_ctrl_list[slot].nic_cpld_init():
            self.cli_log_slot_err_lock(slot, "Init NIC CPLD failed")
            return False

        return True


    def mtp_mgmt_set_nic_sw_boot(self, slot):
        self.cli_log_slot_inf_lock(slot, "Set NIC default sw boot")
        if not self._nic_ctrl_list[slot].nic_set_sw_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default sw boot complete")
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
                if self._nic_ctrl_list[slot].nic_check_status():
                    boot_info_list = self._nic_ctrl_list[slot].nic_get_boot_info()
                    if not boot_info_list:
                        self.cli_log_slot_err(slot, "Retrieve NIC boot info failed")
                    else:
                        self.cli_log_slot_inf(slot, "==> Boot image: {:s}({:s})".format(boot_info_list[0], boot_info_list[1]))

                    if fru_valid:
                        fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
                        if not fru_info_list:
                            self.cli_log_slot_err_lock(slot, "Retrieve NIC FRU failed")
                        else:
                            self.cli_log_slot_inf(slot, "==> FRU: {:s}, {:s}, {:s}".format(fru_info_list[0], fru_info_list[1], fru_info_list[2]))

                    cpld_info_list = self._nic_ctrl_list[slot].nic_get_cpld()
                    if not cpld_info_list:
                        self.cli_log_slot_err(slot, "Retrieve NIC CPLD info failed")
                    else:
                        self.cli_log_slot_inf(slot, "==> CPLD: {:s}({:s})".format(cpld_info_list[0], cpld_info_list[1]))
                else:
                    self.cli_log_slot_err(slot, "NIC in failure state")
            else:
                self.cli_log_slot_err(slot, "NIC is Absent")
        self.cli_log_inf("End MTP NIC Info Dump\n")


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


    def mtp_single_nic_diag_init(self, slot, emmc_format, fru_valid, vmargin):
        if not self.mtp_check_nic_status(slot):
            return

        if not self.mtp_nic_emmc_init(slot, emmc_format):
            return

        if not self.mtp_mgmt_copy_nic_diag(slot):
            return

        if not self.mtp_mgmt_start_nic_diag(slot):
            return

        if not self.mtp_nic_cpld_init(slot):
            return

        if fru_valid:
            if not self.mtp_nic_fru_init(slot):
                return
            fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
            self.mtp_set_nic_sn(slot, fru_info_list[0])
        else:
            self.mtp_set_nic_sn(slot, self.mtp_get_nic_scan_sn(slot))

        if not self.mtp_set_nic_vmarg(slot, vmargin):
            return

        return


    def mtp_nic_diag_init(self, emmc_format=False, fru_valid=True, sn_tag=False, fru_cfg=None, vmargin=0):
        self.cli_log_inf("Init NIC Diag Environment", level = 0)
        if sn_tag:
            self.mtp_nic_load_scan_fru(fru_cfg)
        else:
            self.cli_log_inf("Bypass NIC SN/MAC load")

        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                if not self.mtp_nic_mini_init(slot, fru_valid):
                    continue

        if not self.mtp_mgmt_nic_mac_validate():
            return False

        nic_thread_list = list()
        for slot in range(self._slots):
            nic_thread = threading.Thread(target = self.mtp_single_nic_diag_init,
                                          args = (slot,
                                                  emmc_format,
                                                  fru_valid,
                                                  vmargin))
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)

        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    ret = nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(5)

        if fru_valid and sn_tag:
            if not self.mtp_nic_scan_fru_validate():
                return False

        self.mtp_nic_info_disp(fru_valid)

        self.cli_log_inf("Init NIC Diag Environment complete\n", level = 0)
        return True


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
            if len(match) != len(list(set(match))):
                self.cli_log_err("NIC MAC address validate failed - duplicate entry found")
                return False
            else:
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

        self.cli_log_inf("Power on all NIC, wait {:03d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY), level=0)
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


    def mtp_init_nic_type(self):
        self.cli_log_inf("Init NIC Present")
        cmd = MFG_DIAG_CMDS.NIC_PRESENT_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to init NIC presence")
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False
        # find present
        match = re.findall(r"UUT_(\d+) +NAPLES\d+", self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                self._nic_prsnt_list[slot] = True
        else:
            self.cli_log_err("No NIC present detected")
            return False

        # find type
        self.cli_log_inf("Init NIC Type")
        match = re.findall(r"UUT_(\d+) +NAPLES100", self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                self._nic_type_list[slot] = NIC_Type.NAPLES100
                self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES100)

        match = re.findall(r"UUT_(\d+) +NAPLES25", self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                self._nic_type_list[slot] = NIC_Type.NAPLES25
                self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25)

        return True


    def mtp_nic_check_prsnt(self, slot):
        return self._nic_prsnt_list[slot]


    def mtp_get_nic_prsnt_list(self):
        return self._nic_prsnt_list


    def mtp_get_nic_type(self, slot):
        return self._nic_type_list[slot]


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
        if not self.mtp_nic_con_baudrate_init(slot):
            return False

        if not self._nic_ctrl_list[slot].nic_set_diag_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with diag failed")
            return False

        self.cli_log_slot_inf(slot, "Set NIC default boot with diag complete")
        return True


    def mtp_mgmt_verify_nic_sw_boot(self, slot):
        if not self.mtp_nic_con_baudrate_init(slot):
            return False

        self.cli_log_slot_inf(slot, "Verify NIC default boot with sw image")
        if not self._nic_ctrl_list[slot].nic_verify_sw_boot():
            self.cli_log_slot_err(slot, "Verify NIC default boot with sw image failed")
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            return False

        self.cli_log_slot_inf(slot, "Verify NIC default boot with sw complete")
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


    def mtp_mgmt_pre_post_diag_check(self, intf, slot):
        if intf == "NIC_JTAG":
            cmd = MFG_DIAG_CMDS.NIC_JTAG_TEST_FMT.format(slot+1)
            sig_list = ["valid bit 0x1", "error 0x00"]
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
                return MTP_DIAG_Error.NIC_DIAG_FAIL
            else:
                return "SUCCESS"
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
        else:
            self.cli_log_slot_err(slot, "Unknown pre diag check module")
            return MTP_DIAG_Error.NIC_DIAG_FAIL


    def mtp_mgmt_run_test_mtp_para(self, test, nic_list, vmarg):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return None

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.MTP_PARA_TEST_SIG]

        if test == "PRBS_ETH":
            cmd = MFG_DIAG_CMDS.MTP_PARA_PRBS_TEST_FMT.format(nic_list_param, vmarg)
        elif test == "SNAKE_HBM":
            cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_HBM_FMT.format(nic_list_param, vmarg)
        elif test == "SNAKE_PCIE":
            cmd = MFG_DIAG_CMDS.MTP_PARA_SNAKE_PCIE_FMT.format(nic_list_param, vmarg)
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return None

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_TEST_DELAY):
            self.cli_log_err("Run MTP Parallel Test {:s} Failed".format(test))
            return None

        match = re.findall(r"Slot (\d+) ?: +(\w+)", self.mtp_get_cmd_buf())
        return match


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
            if not self.mtp_mgmt_exec_cmd(init_cmd):
                err_msg = self.mtp_get_cmd_buf()
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # log the timestamp in diag log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(test, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd(ts_record_cmd)

        if not self.mtp_mgmt_exec_cmd(diag_cmd, timeout=MTP_Const.DIAG_TEST_TIMEOUT):
            err_msg = self.mtp_get_cmd_buf()
            return [MTP_DIAG_Error.NIC_DIAG_TIMEOUT, [err_msg]]

        # diag test error ouput
        err_msg_list = list()
        cmd_buf = self.mtp_get_cmd_buf()
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
        self.mtp_mgmt_exec_cmd(ts_record_cmd)

        # post command
        if post_cmd:
            if not self.mtp_mgmt_exec_cmd(post_cmd):
                err_msg = self.mtp_get_cmd_buf()
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        ret = self.mtp_mgmt_get_test_result(rslt_cmd, test)
        if ret == "TIMEOUT":
            if not self.mtp_mgmt_jtag_rst():
                self.mtp_enter_user_ctrl()

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


    def mtp_mgmt_dump_avs_info(self, slot, buf):
        self.cli_log_slot_inf(slot, "AVS Set Result Dump:")
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


    def mtp_mgmt_set_nic_avs(self, slot):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        nic_type = self.mtp_get_nic_type(slot)
        sn = self.mtp_get_nic_sn(slot)

        if nic_type == NIC_Type.NAPLES100:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES100_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES100_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        else:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
            return False

        if not self.mtp_mgmt_exec_cmd(vdd_avs_cmd, timeout=MTP_Const.NIC_AVS_SET_DELAY):
            self.cli_log_slot_err(slot, "Failed to execute command {:s}".format(cmd))
            return False
        self.mtp_mgmt_dump_avs_info(slot, self.mtp_get_cmd_buf())

        if not self.mtp_mgmt_exec_cmd(arm_avs_cmd, timeout=MTP_Const.NIC_AVS_SET_DELAY):
            self.cli_log_slog_err(slot, "Failed to execute command {:s}".format(cmd))
            return False
        self.mtp_mgmt_dump_avs_info(slot, self.mtp_get_cmd_buf())

        return True


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


    def mtp_barcode_scan(self, present_check=True):
        mtp_scan_rslt = dict()
        mtp_ts_snapshot = libmfg_utils.get_timestamp()
        mtp_scan_rslt["MTP_ID"] = self._id
        mtp_scan_rslt["MTP_TS"] = mtp_ts_snapshot
        valid_nic_key_list = list()

        unscanned_nic_key_list = list()
        scan_nic_key_list = list()
        scan_sn_list = list()
        scan_mac_list = list()

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

            usr_prompt = "Please Scan {:s} Serial Number Barcode:".format(key)
            raw_scan = raw_input(usr_prompt)
            sn = libmfg_utils.serial_number_validate(raw_scan)
            if not sn:
                self.cli_log_err("Invalid NIC Serial Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                return None
            if sn in scan_sn_list:
                self.cli_log_err("NIC Serial Number: {:s} is double scanned, please restart the scan process\n".format(sn), level=0)
                return None
            else:
                scan_sn_list.append(sn)

            usr_prompt = "Please scan {:s} MAC Address Barcode:".format(key)
            raw_scan = raw_input(usr_prompt)
            mac = libmfg_utils.mac_address_validate(raw_scan)
            if not mac:
                self.cli_log_err("Invalid NIC MAC Address: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                return None
            mac_ui = libmfg_utils.mac_address_format(mac)
            if mac in scan_mac_list:
                self.cli_log_err("NIC MAC Address: {:s} is double scanned, please restart the scan process\n".format(mac_ui), level=0)
                return None
            else:
                scan_mac_list.append(mac)

            usr_prompt = "Please scan {:s} Part Number Barcode:".format(key)
            raw_scan = raw_input(usr_prompt)
            pn = libmfg_utils.part_number_validate(raw_scan)
            if not pn:
                self.cli_log_err("Invalid NIC Part Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                return None

            nic_scan_rslt["NIC_VALID"] = True
            nic_scan_rslt["NIC_SN"] = sn
            nic_scan_rslt["NIC_MAC"] = mac
            nic_scan_rslt["NIC_PN"] = pn
            nic_scan_rslt["NIC_TS"] = libmfg_utils.get_fru_date()
            mtp_scan_rslt[key] = nic_scan_rslt

        nic_empty_list = list(set(valid_nic_key_list).difference(set(scan_nic_key_list)))
        for key in nic_empty_list:
            nic_scan_rslt = dict()
            nic_scan_rslt["NIC_VALID"] = False
            mtp_scan_rslt[key] = nic_scan_rslt

        return mtp_scan_rslt


    # generate the local barcode config file
    def gen_barcode_config_file(self, pro_srv_id, file_p, scan_rslt):
        config_lines = [str(scan_rslt["MTP_ID"]) + ":"]
        tmp = "    SRV: " + pro_srv_id
        config_lines.append(tmp)
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
                tmp = "        TS: " + scan_rslt[key]["NIC_TS"]
                config_lines.append(tmp)
            else:
                tmp = "        VALID: \"No\""
                config_lines.append(tmp)

        for line in config_lines:
            file_p.write(line + "\n")
