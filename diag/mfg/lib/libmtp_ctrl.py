import pexpect
import time
import os
import sys
import libmfg_utils
import random
import re
import threading
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_BYPASS_PSU_CHECK
from libmfg_cfg import MTP_INTERNAL_MGMT_IP_ADDR
from libmfg_cfg import MTP_INTERNAL_MGMT_NETMASK
from libmfg_cfg import NIC_MGMT_USERNAME
from libmfg_cfg import NIC_MGMT_PASSWORD
from libmfg_cfg import NAPLES_DISP_SN_FMT
from libmfg_cfg import NAPLES_DISP_MAC_FMT
from libmfg_cfg import NAPLES_DISP_DATE_FMT
from libmfg_cfg import MFG_NAPLES100_CPLD_VERSION
from libmfg_cfg import MFG_NAPLES100_VRM_PROGRAM
from libmfg_cfg import MFG_NAPLES100_QSPI_PROGRAM
from libmfg_cfg import MFG_NAPLES100_UPDATE_MAC_ADDR

from libdefs import NIC_Type
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MTP_Const
from libdefs import NIC_Status
from libdefs import MTP_Status
from libdefs import NIC_Port_Mask

class mtp_ctrl():
    def __init__(self, mtpid, filep, diag_log_filep, diag_cmd_log_filep=None, ts_cfg = None, mgmt_cfg = None, apc_cfg = None, dbg_mode = False):
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
        self._psus = 2
        self._status = MTP_Status.MTP_STA_POWEROFF

        self._nic_type_list = [None] * self._slots
        self._nic_prsnt_list = [False] * self._slots
        self._nic_scan_prsnt_list = [False] * self._slots
        self._nic_sn_list = [None] * self._slots
        self._nic_scan_sn_list = [None] * self._slots
        self._nic_mac_list = [None] * self._slots
        self._nic_scan_mac_list = [None] * self._slots
        self._nic_sta_list = [NIC_Status.NIC_STA_OK] * self._slots

        self._nic_handle_list = [None] * self._slots
        self._nic_prompt_list = [None] * self._slots
        self._nic_thread_list = [None] * self._slots
        self._lock = threading.Lock()

        self._debug_mode = dbg_mode
        self._filep = filep
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep


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


    def cli_log_slot_inf(self, slot, msg, level = 1):
        nic_cli_id_str = libmfg_utils.id_str(mtp = self._id, nic = slot)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(nic_cli_id_str + indent + msg)


    def cli_log_slot_err(self, slot, msg, level = 1):
        nic_cli_id_str = libmfg_utils.id_str(mtp = self._id, nic = slot)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_err(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_err(nic_cli_id_str + indent + msg)


    def cli_log_slot_inf_lock(self, slot, msg, level = 1):
        self._lock.acquire()
        self.cli_log_slot_inf(slot, msg, level)
        self._lock.release()


    def cli_log_slot_err_lock(self, slot, msg, level = 1):
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


    def dump_err_msg(self, buf):
        self.cli_log_err("==== Error Message Start: ====")
        self.cli_log_inf(buf)
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
        idx = handle.expect_exact(["assword:",
                                   pexpect.TIMEOUT], timeout = 5)
        if idx == 0:
            handle.sendline(passwd)
        else:
            self.cli_log_err("Can not connect to mtp, check the console.\n", level = 0)
            return None
        try:
            idx = handle.expect_exact(self._prompt_list, timeout = 5)
            if (idx < len(self._prompt_list)):
                handle.sendline("whoami")
                handle.expect_exact(userid)
                handle.expect_exact(self._prompt_list[idx])
                return handle
            else:
                self.cli_log_err("Unknown linux prompt", level = 0)
                return None
        except pexpect.TIMEOUT:
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            self.mtp_enter_user_ctrl()
            return None


    def mtp_para_nic_session_init(self):
        userid = self._mgmt_cfg[1]
        for slot in range(self._slots):
            handle = self.mtp_session_create()
            if handle:
                handle.logfile_read = self._diag_filep
                self.mtp_prompt_cfg(handle, userid, "$", slot)
                self._nic_handle_list[slot] = handle
                self._nic_prompt_list[slot] = "{:s}@NIC-{:02d}:".format(userid, slot+1) + "$"
                para_cmd = "cd ~/diag/python/infra/dshell"
                self.mtp_mgmt_exec_cmd_para(slot, para_cmd)
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
            idx = self._mgmt_handle.expect_exact(["assword:",
                                                  pexpect.TIMEOUT], timeout = 5)
            if idx == 0:
                self._mgmt_handle.sendline(passwd)
                break
            else:
                if retries > 0:
                    self.cli_log_inf("Connect to mtp timeout, wait 30s and retry...", level = 0)
                    time.sleep(30)
                    retries -= 1
                    self._mgmt_handle = pexpect.spawn(ssh_cmd)
                    continue
                else:
                    self.cli_log_err("Can not connect to mtp, check the console.\n", level = 0)
                    return None

        try:
            idx = self._mgmt_handle.expect_exact(self._prompt_list, timeout = 5)
            if (idx < len(self._prompt_list)):
                self._mgmt_prompt = self._prompt_list[idx]
                self._mgmt_handle.sendline("whoami")
                self._mgmt_handle.expect_exact(userid)
                self._mgmt_handle.expect_exact(self._mgmt_prompt)
                # set logfile
                if self._debug_mode:
                    self._mgmt_handle.logfile_read = sys.stdout
                else:
                    self._mgmt_handle.logfile_read = self._diag_filep
                    self._mgmt_handle.logfile_send = self._diag_cmd_filep
                return self._mgmt_prompt
            else:
                self.cli_log_err("Unknown linux prompt", level = 0)
                return None
        except pexpect.TIMEOUT:
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            self.mtp_enter_user_ctrl()
            return None


    def mtp_mgmt_expect_exact(self, exp, delay=None):
        if self._mgmt_handle:
            try:
                if delay:
                    self._mgmt_handle.expect_exact(exp, timeout=delay)
                else:
                    self._mgmt_handle.expect_exact(exp)
                return True
            except pexpect.TIMEOUT:
                return False
        else:
            libmfg_utils.sys_exit("MTP MGMT handle is not initialized")


    def mtp_prompt_cfg(self, handle, userid, prompt, slot=None):
        handle.sendline("stty rows 50 cols 160")
        handle.expect_exact(prompt)
        if slot != None:
            handle.sendline("PS1='\u@NIC-{:02d}:{:s} '".format(slot+1, prompt))
        else:
            handle.sendline("PS1='\u@MTP:{:s} '".format(prompt))
        handle.expect(r"{:s}.*{:s}".format(userid, prompt))


    def mtp_mgmt_refresh(self):
        # mgmt_cfg is a list with format [ip, userid, passwd]
        userid = self._mgmt_cfg[1]
        if self._mgmt_handle:
            self._mgmt_handle.sendline("whoami")
            self._mgmt_handle.expect_exact(userid)
            self._mgmt_handle.expect_exact(self._mgmt_prompt)


    def mtp_enter_user_ctrl(self):
        if self._mgmt_handle and not GLB_CFG_MFG_TEST_MODE:
            self._mgmt_handle.interact()


    def mtp_mgmt_exec_sudo_cmd(self, cmd):
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        if not self._mgmt_handle:
            self.cli_log_err("Management port is not connected")
            return False
        self._mgmt_handle.sendline("sudo -k " + cmd)
        self._mgmt_handle.expect_exact(userid + ":")
        self._mgmt_handle.sendline(passwd)
        if cmd == "reboot" or cmd == "poweroff":
            self._mgmt_handle.expect_exact(pexpect.EOF)
            self._mgmt_handle.logfile_read = None
            self._mgmt_handle.logfile_send = None
            self.mtp_mgmt_disconnect()
        else:
            self._mgmt_handle.expect_exact(self._mgmt_prompt)

        return True


    def mtp_get_hw_version(self):
        self._mgmt_handle.sendline("cpldutil -cpld-rd -addr=0x0")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        match = re.findall(r"addr 0x0 with data (0x[0-9a-fA-F]+)", self._mgmt_handle.before)
        if match:
            io_cpld_ver = match[0]
        else:
            libmfg_utils.sys_exit("Failed to get MTP IO-CPLD image version info")

        self._mgmt_handle.sendline("cpldutil -cpld-rd -addr=0x19")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        match = re.findall(r"addr 0x19 with data (0x[0-9a-fA-F]+)", self._mgmt_handle.before)
        if match:
            jtag_cpld_ver = match[0]
        else:
            libmfg_utils.sys_exit("Failed to get MTP JTAG-CPLD image version info")

        return [io_cpld_ver, jtag_cpld_ver]


    def mtp_get_sw_version(self):
        self._mgmt_handle.sendline("version")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        match = re.search(r"Date: +(.*20\d{2})", self._mgmt_handle.before)
        if match:
            return match.group(1)
        else:
            libmfg_utils.sys_exit("Failed to get diag image version info")


    def mtp_get_asic_version(self):
        self._mgmt_handle.sendline("head /home/diag/diag/asic/asic_version.txt")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        match = re.search(r"Date: +(.*20\d{2})", self._mgmt_handle.before)
        if match:
            return match.group(1)
        else:
            libmfg_utils.sys_exit("Failed to get asic image version info")


    def mtp_update_sw_image(self, image):
        cmd = "rm -rf /home/diag/diag"
        self.mtp_mgmt_exec_cmd(cmd)
        cmd = "tar zxf {:s}".format(image)
        self.mtp_mgmt_exec_cmd(cmd)
        cmd = "sync"
        self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY)


    def mtp_mgmt_poweroff(self):
        if not self.mtp_mgmt_exec_sudo_cmd("poweroff"):
            self.cli_log_err("Failed to execute poweroff command")
            return False

        return True


    def mtp_mgmt_exec_cmd(self, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        self._mgmt_handle.sendline(cmd)
        try:
            self._mgmt_handle.expect_exact(self._mgmt_prompt, timeout)
        except pexpect.TIMEOUT:
            return False
        return True


    def mtp_mgmt_exec_cmd_para(self, slot, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        self._nic_handle_list[slot].sendline(cmd)
        try:
            self._nic_handle_list[slot].expect_exact(self._nic_prompt_list[slot], timeout)
        except pexpect.TIMEOUT:
            return False
        return True


    def mtp_diag_fail_report(self, msg):
        err_msg = MTP_DIAG_Report.MTP_DIAG_REGRESSION_FAIL + ", ERR_MSG: {:s}".format(msg)
        self.cli_log_err(err_msg, level=0)


    def mtp_nic_diag_fail_report(self, slot, sn):
        err_msg = "SN[{:s}]".format(sn) + MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL
        self.cli_log_slot_err(slot, err_msg, level=0)


    def mtp_nic_diag_pass_report(self, slot, sn):
        err_msg = MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS
        self.cli_log_slot_inf(slot, err_msg, level=0)


    def mtp_set_psu_led(self, status):
        pass


    def mtp_set_fan_led(self, status):
        pass


    def mtp_set_sys_led(self, status):
        pass


    def mtp_update_nic_mac_address(self, slot):
        if MFG_NAPLES100_UPDATE_MAC_ADDR:
            self.cli_log_slot_inf(slot, "Update NIC MGMT MAC Address")
            nic_cmd_list = list()
            nic_cmd = "cd /mnt"
            nic_cmd_list.append(nic_cmd)
            nic_cmd = "python update_mac.py"
            nic_cmd_list.append(nic_cmd)
            self.mtp_mgmt_exec_nic_cmds(slot, nic_cmd_list)
            self.cli_log_slot_inf(slot, "Update NIC MGMT MAC Address complete")
            return True
        else:
            self.cli_log_slot_inf(slot, "Update NIC MGMT MAC Address bypassed")


    def mtp_program_nic_fru(self, slot, date, sn, mac):
        self.cli_log_slot_inf(slot, "Program NIC FRU date={:s}, sn={:s}, mac={:s}".format(date, sn, mac))
        nic_cmd_list = list()
        nic_cmd = "{:s}eeutil -date='{:s}' -sn='{:s}' -mac='{:s}' -update".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, date, sn, mac)
        nic_cmd_list.append(nic_cmd)
        self.mtp_mgmt_exec_nic_cmds(slot, nic_cmd_list)
        self.cli_log_slot_inf(slot, "Program NIC FRU complete")
        return True


    def mtp_verify_nic_fru(self, slot, sn, mac):
        self.cli_log_slot_inf(slot, "Verify NIC FRU sn={:s}, mac={:s}".format(sn, mac))
        nic_fru_info = self.mtp_mgmt_get_nic_fru_info(slot)
        if not nic_fru_info:
            self.cli_log_slot_err(slot, "Verify NIC FRU Failed, can not retrieve FRU content")
            return False
        else:
            nic_sn = nic_fru_info[0]
            nic_mac = nic_fru_info[1]

        if nic_sn != sn:
            self.cli_log_slot_err(slot, "SN Verify Failed, get {:s}, expect {:s}".format(nic_sn, sn))
            return False
        if nic_mac != mac:
            self.cli_log_slot_err(slot, "MAC Verify Failed, get {:s}, expect {:s}".format(nic_mac, mac))
            return False

        return True


    def mtp_program_nic_cpld(self, slot, cpld_img):
        self.cli_log_slot_inf(slot, "Program NIC CPLD")
        hw_info = self.mtp_mgmt_get_nic_hw_info(slot)
        if not hw_info:
            self.cli_log_slot_err(slot, "Retrieve NIC CPLD version failed")
            return False

        cur_ver = hw_info[0]
        if cur_ver == MFG_NAPLES100_CPLD_VERSION:
            self.cli_log_slot_inf(slot, "NIC CPLD is up-to-date, bypass the upgrade")
            return True
        else:
            self.cli_log_slot_inf(slot, "Program NIC CPLD, current version: {:s}, upgrade to: {:s}".format(cur_ver, MFG_NAPLES100_CPLD_VERSION))
            # copy the image
            ipaddr = libmfg_utils.get_nic_ip_addr(slot)
            cmd = "scp {:s} {:s} {:s}@{:s}:/".format(libmfg_utils.get_ssh_option(), cpld_img, NIC_MGMT_USERNAME, ipaddr)
            self._mgmt_handle.sendline(cmd)
            self._mgmt_handle.expect_exact("assword:")
            self._mgmt_handle.sendline(NIC_MGMT_PASSWORD)
            self._mgmt_handle.expect_exact(self._mgmt_prompt, timeout=MTP_Const.NIC_NETCOPY_DELAY)

            # program the cpld
            img_name = os.path.basename(cpld_img)
            nic_cmd_list = list()
            nic_cmd = "{:s}cpld -prog /{:s}".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, img_name)
            nic_cmd_list.append(nic_cmd)
            self.mtp_mgmt_exec_nic_cmds(slot, nic_cmd_list)
            self.cli_log_slot_inf(slot, "Program NIC CPLD complete")
            return True


    def mtp_verify_nic_cpld(self, slot):
        self.cli_log_slot_inf(slot, "Verify NIC CPLD")
        hw_info = self.mtp_mgmt_get_nic_hw_info(slot)
        if not hw_info:
            self.cli_log_slot_err(slot, "Retrieve NIC CPLD version failed")
            return False

        cur_ver = hw_info[0]
        if cur_ver != MFG_NAPLES100_CPLD_VERSION:
            self.cli_log_slot_err(slot, "Verify NIC CPLD Failed, exp: {:s}, get: {:s}".format(MFG_NAPLES100_CPLD_VERSION, cur_ver))
            return False
        else:
            self.cli_log_slot_inf(slot, "Verify NIC CPLD complete")
            return True


    def mtp_program_nic_vrm(self, slot, vrm_img, vrm_img_cksum):
        if MFG_NAPLES100_VRM_PROGRAM:
            self.cli_log_slot_inf(slot, "Program NIC VRM")
            # copy the image
            ipaddr = libmfg_utils.get_nic_ip_addr(slot)
            cmd = "scp {:s} {:s} {:s}@{:s}:/".format(libmfg_utils.get_ssh_option(), vrm_img, NIC_MGMT_USERNAME, ipaddr)
            self._mgmt_handle.sendline(cmd)
            self._mgmt_handle.expect_exact("assword:")
            self._mgmt_handle.sendline(NIC_MGMT_PASSWORD)
            self._mgmt_handle.expect_exact(self._mgmt_prompt, timeout=MTP_Const.NIC_NETCOPY_DELAY)

            # program the vrm
            img_name = os.path.basename(vrm_img)
            nic_cmd_list = list()
            nic_cmd = "{:s}devmgr -program -file=/{:s}".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, img_name)
            nic_cmd_list.append(nic_cmd)
            nic_cmd = "{:s}devmgr -verify -file=/{:s}".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, img_name)
            nic_cmd_list.append(nic_cmd)
            self.mtp_mgmt_exec_nic_cmds(slot, nic_cmd_list)
            self.cli_log_slot_inf(slot, "Program NIC VRM AVS")
            self.cli_log_slot_inf(slot, "Program NIC VRM AVS complete")
            self.cli_log_slot_inf(slot, "Program NIC VRM complete")
        else:
            self.cli_log_slot_inf(slot, "Program NIC VRM bypassed")
        return True


    def mtp_verify_nic_vrm(self, slot, vrm_img, vrm_img_cksum):
        if MFG_NAPLES100_VRM_PROGRAM:
            return True
        return True


    def mtp_program_nic_qspi(self, slot, qspi_img):
        if MFG_NAPLES100_QSPI_PROGRAM:
            self.cli_log_slot_inf(slot, "Program NIC QSPI")
            # copy the image
            ipaddr = libmfg_utils.get_nic_ip_addr(slot)
            cmd = "scp {:s} {:s} {:s}@{:s}:/".format(libmfg_utils.get_ssh_option(), qspi_img, NIC_MGMT_USERNAME, ipaddr)
            self._mgmt_handle.sendline(cmd)
            self._mgmt_handle.expect_exact("assword:")
            self._mgmt_handle.sendline(NIC_MGMT_PASSWORD)
            self._mgmt_handle.expect_exact(self._mgmt_prompt, timeout=MTP_Const.NIC_NETCOPY_DELAY)

            # program the qspi
            img_name = os.path.basename(qspi_img)
            nic_cmd_list = list()
            nic_cmd = "fwupdate -p /{:s} -i 'diagfw'".format(img_name)
            nic_cmd_list.append(nic_cmd)
            self.mtp_mgmt_exec_nic_cmds(slot, nic_cmd_list)
            self.cli_log_slot_inf(slot, "Program NIC QSPI complete")
        else:
            self.cli_log_slot_inf(slot, "Program NIC QSPI bypassed")
        return True


    def mtp_install_nic_emmc(self, slot, emmc_img):
        self.cli_log_slot_inf(slot, "Install NIC EMMC")
        # copy the image
        ipaddr = libmfg_utils.get_nic_ip_addr(slot)
        cmd = "scp {:s} {:s} {:s}@{:s}:/".format(libmfg_utils.get_ssh_option(), emmc_img, NIC_MGMT_USERNAME, ipaddr)
        self._mgmt_handle.sendline(cmd)
        self._mgmt_handle.expect_exact("assword:")
        self._mgmt_handle.sendline(NIC_MGMT_PASSWORD)
        self._mgmt_handle.expect_exact(self._mgmt_prompt, timeout=MTP_Const.NIC_NETCOPY_DELAY)

        # install the emmc
        img_name = os.path.basename(emmc_img)
        nic_cmd_list = list()
        nic_cmd = "fwupdate --init-emmc"
        nic_cmd_list.append(nic_cmd)
        nic_cmd = "fwupdate -l"
        nic_cmd_list.append(nic_cmd)
        nic_cmd = "fwupdate -p /{:s} -i 'uboot mainfwa mainfwb'".format(img_name)
        nic_cmd_list.append(nic_cmd)
        nic_cmd = "fwupdate -s diagfw"
        nic_cmd_list.append(nic_cmd)
        self.mtp_mgmt_exec_nic_cmds(slot, nic_cmd_list)
        self.cli_log_slot_inf(slot, "Install NIC EMMC complete")
        return True


    def mtp_verify_nic_qspi(self, slot, qspi_img):
        if MFG_NAPLES100_QSPI_PROGRAM:
            return True
        return True


    def mtp_misc_init(self):
        rc = True
        # vrm test
        self._mgmt_handle.sendline("mtptest -vrm")
        idx = self._mgmt_handle.expect_exact(["TEST FAILED", "TEST PASSED", pexpect.TIMEOUT])
        if idx == 0:
            self.dump_err_msg(self._mgmt_handle.before)
            self.cli_log_err("VRM test failed")
            rc = False
        elif idx == 1:
            self.cli_log_inf("VRM test passed")
        else:
            self.cli_log_err("VRM test timeout")
            rc = False

        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        return rc


    def mtp_fan_init(self, fan_spd):
        rc = True
        # scan the devices
        self._mgmt_handle.sendline("mtptest -present")
        self._mgmt_handle.expect_exact("Present TEST")

        # fan absent, check cpld present signal
        for fan in range(self._fans):
            fan_cli_id_str = libmfg_utils.fan_key(fan)
            if "Fan " + str(fan) + " is present" not in self._mgmt_handle.before:
                self.cli_log_err(fan_cli_id_str + " is not present")
                rc = False
            else:
                self.cli_log_inf(fan_cli_id_str + " is present")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        # fan test, check if fan speed can be adjusted
        self._mgmt_handle.sendline("mtptest -fanspd")
        idx = self._mgmt_handle.expect_exact(["TEST FAILED", "TEST PASSED", pexpect.TIMEOUT])
        if idx == 0:
            self.dump_err_msg(self._mgmt_handle.before)
            match = re.findall(r"idx=(\d)", str(self._mgmt_handle.before))
            if match:
                fan_fail_list = list()
                for idx in range(len(match)):
                    fan_cli_id_str = libmfg_utils.fan_key(int(match[idx])/2)
                    if fan_cli_id_str not in fan_fail_list:
                        fan_fail_list.append(fan_cli_id_str)
                self.cli_log_err("[{:s}] speed test failed".format(", ".join(fan_fail_list)))
            else:
                self.cli_log_err("Fan speed test failed, but no instance specified")
            rc = False
        elif idx == 1:
            for fan in range(self._fans):
                fan_cli_id_str = libmfg_utils.fan_key(fan)
                self.cli_log_inf(fan_cli_id_str + " speed test passed")
        else:
            self.cli_log_err("Fan speed diag test timeout.")
            rc = False
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        # set the fan speed
        self.cli_log_inf("Set FAN Speed to {:d}%".format(fan_spd))
        cmd = "devmgr -dev=fan -speed -pct={:d}".format(fan_spd)
        self.mtp_mgmt_exec_cmd(cmd)
        cmd = "devmgr -dev FAN -status"
        self.mtp_mgmt_exec_cmd(cmd)

        return rc


    def mtp_psu_init(self):
        rc = True
        # apc_cfg is a list with format [apc1, apc1_port, apc1_userid, apc1_passwd, apc2, apc2_port, apc2_userid, apc2_passwd]
        apc1 = self._apc_cfg[0]
        apc2 = self._apc_cfg[4]

        if apc1 != "":
            psu_cli_id_str = libmfg_utils.psu_key(0)
            self._mgmt_handle.sendline("mtptest -psu -psumask 0x1")
            idx = self._mgmt_handle.expect_exact(["TEST FAILED", "TEST PASSED", pexpect.TIMEOUT])
            if idx == 0:
                self.cli_log_err(psu_cli_id_str + " is not present")
                rc = False
            elif idx == 1:
                # double check if the apc is on.
                match = re.findall(r"-\.-", self._mgmt_handle.before)
                if match:
                    self.cli_log_err(psu_cli_id_str + " is present, but input power is off")
                    rc = False
                else:
                    self.cli_log_inf(psu_cli_id_str + " is present, and input power is on")
            else:
                self.cli_log_err(psu_cli_id_str + " diag test timeout.")
                rc = False
            self._mgmt_handle.expect_exact(self._mgmt_prompt)

        if apc2 != "":
            psu_cli_id_str = libmfg_utils.psu_key(1)
            self._mgmt_handle.sendline("mtptest -psu -psumask 0x2")
            idx = self._mgmt_handle.expect_exact(["TEST FAILED", "TEST PASSED", pexpect.TIMEOUT])
            if idx == 0:
                self.cli_log_err(psu_cli_id_str + " is not present")
                rc = False
            elif idx == 1:
                # double check if the apc is on.
                match = re.findall(r"-\.-", self._mgmt_handle.before)
                if match:
                    self.cli_log_err(psu_cli_id_str + " is present, but input power is off")
                    rc = False
                else:
                    self.cli_log_inf(psu_cli_id_str + " is present, and input power is on")
            else:
                self.cli_log_err(psu_cli_id_str + " diag test timeout.")
                rc = False
            self._mgmt_handle.expect_exact(self._mgmt_prompt)

        return rc


    def mtp_diag_pre_init(self, diagmgr_logfile):
        # start the mtp diag
        self.cli_log_inf("Init Diag SW Environment", level=0)
        self._mgmt_handle.sendline("/home/diag/start_diag.sh")
        self._mgmt_handle.expect_exact("Set up diag amd64 -- Done", timeout=MTP_Const.OS_CMD_DELAY)
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        cmd = "source ~/.bash_profile"
        self.mtp_mgmt_exec_cmd(cmd)

        # start the mtp diagmgr
        diagmgr_handle = self.mtp_session_create()
        cmd = "nohup diagmgr > {:s} 2>&1 &".format(diagmgr_logfile)
        diagmgr_handle.sendline(cmd)
        diagmgr_handle.expect_exact(self._mgmt_prompt)
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
        diagmgr_handle.close()

        # config the prompt
        userid = self._mgmt_cfg[1]
        self.mtp_prompt_cfg(self._mgmt_handle, userid, self._mgmt_prompt)
        self._mgmt_prompt = "{:s}@MTP:".format(userid) + self._mgmt_prompt

        # register MTP diagsp
        cmd = "cd ~/diag/python/infra/dshell"
        self.mtp_mgmt_exec_cmd(cmd)
        self._mgmt_handle.sendline("./diag -r -c MTP1 -d diagmgr -t dsp_start")
        self._mgmt_handle.expect_exact("Test Done: MTP1:DIAGMGR:DSP_START")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        self.cli_log_inf("Init Diag SW Environment complete\n", level=0)


    def mtp_diag_init(self, naples100_test_db):
        cmd = "cd ~/diag/python/infra/dshell"
        self.mtp_mgmt_exec_cmd(cmd)
        self._mgmt_handle.sendline("./diag -sdsp")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        # naples100 dsp check
        self.cli_log_inf("Start Diag DSP Sanity Check", level = 0)
        naples100_dsp_list = naples100_test_db.get_diag_seq_dsp_list()
        naples100_dsp_list += naples100_test_db.get_diag_para_dsp_list()
        for dsp in naples100_dsp_list:
            if dsp not in self._mgmt_handle.before:
                self.cli_log_err("Diag DSP: {:s} is not detected".format(dsp), level = 0)
                return False
        self.cli_log_inf("Diag DSP Sanity Check Complete", level = 0)

        self.cli_log_inf("Create Parallel MTP Connections", level = 0)
        ret = self.mtp_para_nic_session_init()
        if not ret:
            self.cli_log_err("Create Parallel MTP Connections Failed", level = 0)
            return False
        self.cli_log_inf("Create Parallel MTP Connections Complete\n", level = 0)
        return True


    def mtp_hw_init(self, psu_check, fan_spd):
        rc = True

        self.cli_log_inf("Start MTP chassis sanity check", level = 0)
        # fan init
        rc &= self.mtp_fan_init(fan_spd)

        if psu_check and not MFG_BYPASS_PSU_CHECK:
            # psu init
            rc &= self.mtp_psu_init()
        else:
            self.cli_log_inf("PSU Check bypassed")

        # other platform init
        rc &= self.mtp_misc_init()

        if rc:
            self.cli_log_inf("MTP chassis sanity check passed\n", level = 0)
        else:
            self.cli_log_inf("MTP chassis sanity check failed\n", level = 0)

        return rc


    def mtp_diag_env_init(self, fan_speed, vmarg):
        # set nic voltage margin
        if vmarg != 0:
            for slot in range(self._slots):
                if self._nic_prsnt_list[slot]:
                    self.mtp_set_nic_vmarg(slot, vmarg)

        self.set_mtp_status(MTP_Status.MTP_STA_READY)

        return True


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
            self.cli_log_inf("No threshold set, bypass ambient temperature check")
            return True

        timeout = MTP_Const.MFG_TEMP_WAIT_TIMEOUT
        while timeout > 0:
            inlet = self.mtp_get_inlet_temp(low_threshold, high_threshold)
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
        while timeout > 0:
            time.sleep(MTP_Const.MFG_TEMP_CHECK_INTERVAL)
            timeout -= 1
            inlet = self.mtp_get_inlet_temp(low_threshold, high_threshold)
            #if inlet > upper_limit or inlet < lower_limit:
            #    self.cli_log_err("Soaking process failed, current inlet reading is {:2.2f}".format(inlet))
            #    self.cli_log_err("Temperature is out of range [{:2.2f}, {:2.2g}], check the chamber".format(lower_limit, upper_limit))
            #    return False
        self.cli_log_inf("Soaking process complete, current inlet reading is {:2.2f}".format(inlet))

        return True


    def mtp_get_inlet_temp(self, low_threshold, high_threshold):
        self._mgmt_handle.sendline("devmgr -dev FAN -status")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
        # FAN                 23.50          25.50          21.75          21.75
        match = re.search(r"FAN +(-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+)", str(self._mgmt_handle.before))
        if match:
            # validate the readings
            inlet_1 = float(match.group(3))
            inlet_2 = float(match.group(4))
            inlet_diff = abs(inlet_1 - inlet_2)
            # if the difference is more than 5, something is wrong, relay on any inlet near the threshold
            if inlet_diff > 5.0:
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
            self.dump_err_msg(self._mgmt_handle.before)
            self.cli_log_err("Unable to get inlet temperature")
            return 0.0


    def mtp_get_nic_temp(self, slot):
        # how to get nic asic temperature
        return 95


    def mtp_mgmt_copy_nic_diag(self, slot):
        ipaddr = libmfg_utils.get_nic_ip_addr(slot)

        # create diag dir on NIC
        nic_prompt = self.mtp_mgmt_init_nic_handle(slot)
        if not nic_prompt:
            return False
        nic_cmd = "mkdir -p {:s}".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH)
        self._mgmt_handle.sendline(nic_cmd)
        if not self.mtp_mgmt_expect_exact(nic_prompt):
            self.cli_log_slot_err(slot, "Create diag directory {:s} Failed".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH))
            return False
        cmd = "exit"
        self.mtp_mgmt_exec_cmd(cmd)

        # copy nic diag image onto nic
        nic_diag_list = ["diag", "start_diag.arm64.sh"]
        for util in nic_diag_list:
            cmd = "scp {:s} -r {:s}{:s} {:s}@{:s}:{:s}".format(libmfg_utils.get_ssh_option(), MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH, util, NIC_MGMT_USERNAME, ipaddr, MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH)
            self._mgmt_handle.sendline(cmd)
            idx = self._mgmt_handle.expect_exact(["assword:", pexpect.TIMEOUT])
            if idx == 0:
                self._mgmt_handle.sendline(NIC_MGMT_PASSWORD)
                self._mgmt_handle.expect_exact(self._mgmt_prompt, timeout=MTP_Const.NIC_NETCOPY_DELAY)
            else:
                self.mtp_mgmt_refresh()
                self._nic_sta_list[slot] = NIC_Status.NIC_STA_MGMT_FAIL
                return False

        # check nic diag image are on the nic
        nic_prompt = self.mtp_mgmt_init_nic_handle(slot)
        if not nic_prompt:
            return False
        nic_cmd = "ls {:s}".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH)
        self._mgmt_handle.sendline(nic_cmd)
        self._mgmt_handle.expect_exact(nic_prompt)
        for util in nic_diag_list:
            if util not in self._mgmt_handle.before:
                self.cli_log_slot_err(slot, "Copy NIC Diag image '{:s}' Failed".format(util))
                return False

        # setup diag env
        nic_cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH)
        self._mgmt_handle.sendline(nic_cmd)
        self._mgmt_handle.expect_exact(nic_prompt)

        nic_cmd = "./start_diag.arm64.sh {:d}".format(slot+1)
        self._mgmt_handle.sendline(nic_cmd)
        self._mgmt_handle.expect_exact(nic_prompt, timeout=MTP_Const.OS_CMD_DELAY)

        nic_cmd = "source /etc/profile"
        self._mgmt_handle.sendline(nic_cmd)
        self._mgmt_handle.expect_exact(nic_prompt)

        self._mgmt_handle.sendline("exit")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        # Start NIC DSP
        cmd = "diag -r -c NIC{:d} -d diagmgr -t dsp_start".format(slot+1)
        self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY)

        return True


    def mtp_mgmt_exec_nic_con_cmd(self, slot, nic_con_cmd, pass_match=None, fail_match=None):
        # goto the nic_con dir
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        self.mtp_mgmt_exec_cmd(cmd)
        self._mgmt_handle.sendline(nic_con_cmd)

        # extra match to deal with identical output
        if pass_match and fail_match:
            idx = self._mgmt_handle.expect_exact([pass_match, fail_match, pexpect.TIMEOUT], timeout=MTP_Const.NIC_CON_CMD_DELAY)
            if idx == 0:
                extra_timeout = False
            else:
                extra_timeout = True
        else:
            extra_timeout = False

        idx = self._mgmt_handle.expect_exact(["Thanks for using picocom", "TIMEOUT", pexpect.TIMEOUT], timeout=MTP_Const.NIC_CON_CMD_DELAY)
        if idx == 0 and "TIMEOUT" not in self._mgmt_handle.before and not extra_timeout:
            self._mgmt_handle.expect_exact("exit")
            self._mgmt_handle.expect_exact(self._mgmt_prompt)
            return True
        else:
            self._nic_sta_list[slot] = NIC_Status.NIC_STA_MGMT_FAIL
            return False


    def mtp_mgmt_test_nic_mem(self, slot):
        nic_con_cmd = "nic_con.py -mtest -slot {:d}".format(slot+1)
        if not self.mtp_mgmt_exec_nic_con_cmd(slot, nic_con_cmd, "MTEST PASSED", "MTEST FAILED"):
            return False
        else:
            return True


    def mtp_mgmt_init_nic_handle(self, slot):
        ipaddr = libmfg_utils.get_nic_ip_addr(slot)
        cmd = libmfg_utils.get_ssh_connect_cmd(NIC_MGMT_USERNAME, ipaddr)
        self._mgmt_handle.sendline(cmd)
        exp_list = ["assword:", "#", pexpect.TIMEOUT]
        while True:
            idx = self._mgmt_handle.expect_exact(exp_list)
            if idx == 0:
                self._mgmt_handle.sendline(NIC_MGMT_PASSWORD)
                continue
            elif idx == 1:
                nic_prompt = exp_list[idx]
                break
            else:
                self.cli_log_slot_err(slot, "Connect to NIC managment port failed")
                self._nic_sta_list[slot] = NIC_Status.NIC_STA_MGMT_FAIL
                return None

        return nic_prompt


    def mtp_mgmt_exec_nic_cmds(self, slot, nic_cmd_list):
        nic_prompt = self.mtp_mgmt_init_nic_handle(slot)
        if not nic_prompt:
            return False

        for nic_cmd in nic_cmd_list:
            self._mgmt_handle.sendline(nic_cmd)
            self._mgmt_handle.expect_exact(nic_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY)
            time.sleep(1)
        self._mgmt_handle.sendline("sync")
        self._mgmt_handle.expect_exact(nic_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY)
        self._mgmt_handle.sendline("exit")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        return True


    # retrieve fru info from nic
    # return [sn, date, mac]
    def mtp_mgmt_get_nic_fru_info(self, slot):
        nic_prompt = self.mtp_mgmt_init_nic_handle(slot)
        if not nic_prompt:
            return None

        # dump the fru
        self._mgmt_handle.sendline("{:s}cpld -r 0".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH))
        self._mgmt_handle.expect_exact(nic_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY)
        self._mgmt_handle.sendline("{:s}devmgr -status".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH))
        self._mgmt_handle.expect_exact(nic_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY)
        self._mgmt_handle.sendline("{:s}eeutil -disp".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH))
        self._mgmt_handle.expect_exact(nic_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY)
        match = re.findall(NAPLES_DISP_SN_FMT, self._mgmt_handle.before)
        if match:
            sn = match[0]
        else:
            sn = ""
        match = re.findall(NAPLES_DISP_MAC_FMT, self._mgmt_handle.before)
        if match:
            mac = match[0]
        else:
            mac = ""
        self._mgmt_handle.sendline("exit")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        if sn == "" or mac == "":
            return None

        return [sn, mac]


    # retrieve misc hw info from nic
    # return [cpld_ver, etc]
    def mtp_mgmt_get_nic_hw_info(self, slot):
        nic_prompt = self.mtp_mgmt_init_nic_handle(slot)
        if not nic_prompt:
            return None
        # dump the fru
        self._mgmt_handle.sendline("{:s}cpld -r 0".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH))
        self._mgmt_handle.expect_exact(nic_prompt)
        match = re.findall(r"(0x[0-9a-fA-F]+)", self._mgmt_handle.before)
        if match:
            cpld_ver = match[0]
        else:
            cpld_ver = "0xdeadbeef"

        self._mgmt_handle.sendline("exit")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        return [cpld_ver]


    def mtp_nic_mini_init(self, slot):
        # 1. change baud rate to 9600
        loop = 0
        while loop < MTP_Const.NIC_CON_INIT_RETRY:
            self.cli_log_slot_inf(slot, "Set NIC Console baudrate - <{:d}> try".format(loop+1))
            nic_con_cmd = "nic_con.py -br -slot {:d}".format(slot+1)
            if not self.mtp_mgmt_exec_nic_con_cmd(slot, nic_con_cmd):
                # retry
                self.mtp_power_off_single_nic(slot)
                self.mtp_power_on_single_nic(slot)
                loop += 1
                continue
            else:
                self._nic_sta_list[slot] = NIC_Status.NIC_STA_OK
                break

        if loop >= MTP_Const.NIC_CON_INIT_RETRY:
            self.cli_log_slot_err(slot, "Set NIC Console baudrate failed")
            return False

        # 2. config nic ip address
        loop = 0
        while loop < MTP_Const.NIC_MGMT_IP_INIT_RETRY:
            self.cli_log_slot_inf(slot, "Set NIC MGMT ip address - <{:d}> try".format(loop+1))
            nic_con_cmd = "nic_con.py -mgmt -slot {:d}".format(slot+1)
            if not self.mtp_mgmt_exec_nic_con_cmd(slot, nic_con_cmd, "ifconfig oob_mnic0", "FAIL to enable management port"):
                # retry
                loop += 1
                continue
            else:
                self._nic_sta_list[slot] = NIC_Status.NIC_STA_OK
                break

        if loop >= MTP_Const.NIC_MGMT_IP_INIT_RETRY:
            self.cli_log_slot_err(slot, "Set NIC MGMT ip address failed")
            return False

        time.sleep(MTP_Const.NIC_MGMT_IP_SET_DELAY)
        return True


    def mtp_nic_diag_init(self, slot = None):
        if slot != None:
            if not self.mtp_nic_mini_init(slot):
                return False

            self.cli_log_slot_inf(slot, "Download NIC Diag image")
            if not self.mtp_mgmt_copy_nic_diag(slot):
                self.cli_log_slot_err(slot, "Download NIC Diag image failed")
                self._nic_sta_list[slot] = NIC_Status.NIC_STA_MGMT_FAIL
                return False

            return True
        else:
            ret = True
            for slot in range(self._slots):
                if self._nic_prsnt_list[slot]:
                    ret &= self.mtp_nic_diag_init(slot)
            return ret


    def mtp_nic_load_sn(self, sn_tag):
        ret = self.mtp_nic_diag_init()
        self.mtp_init_nic_sn(sn_tag)
        self.mtp_init_nic_mac(sn_tag)
        return ret


    def mtp_nic_load_scan_sn(self):
        self.cli_log_inf("Load Barcode config file")
        nic_fru_cfg_file = "config/{:s}.yaml".format(self._id)
        nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(nic_fru_cfg_file)
        for slot in range(self._slots):
            key = libmfg_utils.nic_key(slot)
            valid = nic_fru_cfg[self._id][key]["VALID"]
            if str.upper(valid) == "YES":
                sn = nic_fru_cfg[self._id][key]["SN"]
                mac = nic_fru_cfg[self._id][key]["MAC"]
                self.mtp_set_nic_scan_sn(slot, sn)
                self.mtp_set_nic_scan_mac(slot, mac)
        return True


    def mtp_nic_init(self, fru_load, sn_tag=True):
        self.cli_log_inf("Init NICs in the MTP Chassis", level = 0)

        # init nic present list
        self.mtp_init_nic_prsnt(sn_tag)

        # init nic type list
        self.mtp_init_nic_type()

        if fru_load:
            # power on nic
            self.mtp_power_on_nic()
            self.mtp_nic_load_sn(sn_tag)
            if sn_tag:
                self.mtp_nic_load_scan_sn()
        else:
            self.cli_log_inf("Bypass load NIC SN/MAC")

        self.cli_log_inf("Init NICs in the MTP Chassis complete\n", level = 0)
        self.mtp_nic_info_show()
        return True


    def mtp_nic_info_show(self):
        self.cli_log_inf("NIC Info Dump in the MTP Chassis:", level = 0)
        for slot, prsnt, nic_type in zip(range(self._slots), self._nic_prsnt_list, self._nic_type_list):
            if prsnt:
                self.cli_log_slot_inf(slot, "NIC is Present, Type is: {:s}".format(nic_type), level=0)
            else:
                self.cli_log_slot_err(slot, "NIC is Absent", level=0)
        self.cli_log_inf("NIC Info Dump in the MTP Chassis complete\n", level = 0)


    def mtp_power_on_nic(self):
        self.cli_log_inf("Power on all NIC, wait {:03d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY))
        cmd = "turn_on_slot.sh on all"
        self.mtp_mgmt_exec_cmd(cmd)
        libmfg_utils.count_down(MTP_Const.NIC_POWER_ON_DELAY)


    def mtp_power_off_nic(self):
        self.cli_log_inf("Power off all NIC")
        cmd = "turn_on_slot.sh off all"
        self.mtp_mgmt_exec_cmd(cmd)
        time.sleep(MTP_Const.NIC_POWER_OFF_DELAY)


    def mtp_power_on_single_nic(self, slot):
        self.cli_log_slot_inf(slot, "Power on NIC, wait {:03d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY))
        cmd = "turn_on_slot.sh on {:d}".format(slot+1)
        self.mtp_mgmt_exec_cmd(cmd)
        libmfg_utils.count_down(MTP_Const.NIC_POWER_ON_DELAY)


    def mtp_power_off_single_nic(self, slot):
        self.cli_log_slot_inf(slot, "Power off NIC")
        cmd = "turn_on_slot.sh off {:d}".format(slot+1)
        self.mtp_mgmt_exec_cmd(cmd)
        time.sleep(MTP_Const.NIC_POWER_OFF_DELAY)


    def mtp_init_nic_prsnt(self, sn_tag=True):
        self.cli_log_inf("Init NIC Present")
        self._mgmt_handle.sendline("inventory -present")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        match = re.findall(r"UUT_(\d+) +NAPLES\d+", self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                self._nic_prsnt_list[slot] = True
                if not sn_tag:
                    self._nic_scan_prsnt_list[slot] = True


    def mtp_get_nic_prsnt_list(self):
        return self._nic_prsnt_list


    def mtp_get_nic_prsnt(self, slot):
        return self._nic_prsnt_list[slot]


    def mtp_init_nic_type(self):
        self.cli_log_inf("Init NIC Type")
        self._mgmt_handle.sendline("inventory -present")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        match = re.findall(r"UUT_(\d+) +NAPLES100", self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                self._nic_type_list[slot] = NIC_Type.NAPLES100

        match = re.findall(r"UUT_(\d+) +NAPLES25", self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                self._nic_type_list[slot] = NIC_Type.NAPLES25


    def mtp_get_nic_type(self, slot):
        return self._nic_type_list[slot]


    def mtp_init_nic_sn(self, sn_tag):
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot] and self._nic_sta_list[slot] == NIC_Status.NIC_STA_OK:
                nic_fru_info = self.mtp_mgmt_get_nic_fru_info(slot)
                if not nic_fru_info:
                    self.cli_log_slot_err(slot, "Unable to retrieve NIC FRU content")
                    self._nic_sn_list[slot] = "FLMDEADBEEF"
                    self._nic_sta_list[slot] = NIC_Status.NIC_STA_MGMT_FAIL
                    if not sn_tag:
                        self._nic_scan_sn_list[slot] = "FLMDEADBEEF"
                else:
                    self.cli_log_slot_inf(slot, "Set SN to {:s}".format(nic_fru_info[0]))
                    self._nic_sn_list[slot] = nic_fru_info[0]
                    if not sn_tag:
                        self._nic_scan_sn_list[slot] = nic_fru_info[0]


    def mtp_get_nic_sn(self, slot):
        return self._nic_sn_list[slot]


    def mtp_set_nic_sn(self, slot, sn):
        self.cli_log_slot_inf(slot, "Set SN to {:s}".format(sn), level=0)
        self._nic_sn_list[slot] = sn


    def mtp_get_nic_scan_sn(self, slot):
        return self._nic_scan_sn_list[slot]


    def mtp_set_nic_scan_sn(self, slot, sn):
        self.cli_log_slot_inf(slot, "Set Scan SN to {:s}".format(sn), level=0)
        self._nic_scan_sn_list[slot] = sn
        self._nic_scan_prsnt_list[slot] = True


    def mtp_init_nic_mac(self, sn_tag):
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot] and self._nic_sta_list[slot] == NIC_Status.NIC_STA_OK:
                nic_fru_info = self.mtp_mgmt_get_nic_fru_info(slot)
                if not nic_fru_info:
                    self.cli_log_slot_err(slot, "Unable to retrieve NIC FRU content")
                    self._nic_mac_list[slot] = "00AEDEADBEEF"
                    if not sn_tag:
                        self._nic_scan_mac_list[slot] = "00AEDEADBEEF"
                else:
                    self._nic_mac_list[slot] = str.upper(nic_fru_info[1]).replace('-', '')
                    if not sn_tag:
                        self._nic_scan_mac_list[slot] = str.upper(nic_fru_info[1]).replace('-', '')


    def mtp_get_nic_mac(self, slot):
        return self._nic_mac_list[slot]


    def mtp_set_nic_mac(self, slot, mac):
        self.cli_log_slot_inf(slot, "Set MAC to {:s}".format(mac), level=0)
        self._nic_mac_list[slot] = mac


    def mtp_get_nic_scan_mac(self, slot):
        return self._nic_scan_mac_list[slot]


    def mtp_set_nic_scan_mac(self, slot, mac):
        self.cli_log_slot_inf(slot, "Set Scan MAC to {:s}".format(mac), level=0)
        self._nic_scan_mac_list[slot] = mac


    def mtp_get_nic_xcvr_prsnt(self, slot):
        # TODO: how to get xcvr present status?
        mask = NIC_Port_Mask.NIC_ALL_PORT_MASK
        return mask


    def mtp_mgmt_set_nic_diag_boot(self, slot):
        self.cli_log_slot_inf(slot, "Set NIC default boot with diag image")
        nic_prompt = self.mtp_mgmt_init_nic_handle(slot)
        if not nic_prompt:
            self.cli_log_slot_inf(slot, "Set NIC default boot with diag failed")
            return False
        nic_cmd_list = list()
        nic_cmd = "fwupdate -s diagfw"
        nic_cmd_list.append(nic_cmd)
        self.mtp_mgmt_exec_nic_cmds(slot, nic_cmd_list)
        self.cli_log_slot_inf(slot, "Set NIC default boot with diag complete")

        return True


    def mtp_mgmt_set_nic_sw_boot(self, slot):
        self.cli_log_slot_inf(slot, "Set NIC default boot with sw image")
        nic_prompt = self.mtp_mgmt_init_nic_handle(slot)
        if not nic_prompt:
            self.cli_log_slot_inf(slot, "Set NIC default boot with sw failed")
            return False
        nic_cmd_list = list()
        nic_cmd = "fwupdate -s mainfwa"
        nic_cmd_list.append(nic_cmd)
        self.mtp_mgmt_exec_nic_cmds(slot, nic_cmd_list)
        self.cli_log_slot_inf(slot, "Set NIC default boot with sw complete")

        return True


    def mtp_mgmt_verify_nic_sw_boot(self, slot):
        self.cli_log_slot_inf(slot, "Verify NIC default boot with sw image")
        nic_prompt = self.mtp_mgmt_init_nic_handle(slot)
        if not nic_prompt:
            self.cli_log_slot_inf(slot, "Verify NIC default boot with sw failed")
            return False
        nic_cmd = "fwupdate -r"
        self._mgmt_handle.sendline(nic_cmd)
        self._mgmt_handle.expect_exact("mainfwa")
        self._mgmt_handle.expect_exact(nic_prompt)
        self._mgmt_handle.sendline("exit")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        self.cli_log_slot_inf(slot, "Verify NIC default boot with sw complete")

        return True


    def mtp_set_nic_vmarg(self, slot, vmarg):
        if vmarg > 0:
            vmarg_param = "high"
        elif vmarg == 0:
            vmarg_param = "normal"
        else:
            vmarg_param = "low"

        self.cli_log_slot_inf(slot, "Set voltage margin to {:s}".format(vmarg_param), level=0)
        nic_prompt = self.mtp_mgmt_init_nic_handle(slot)
        if not nic_prompt:
            self.cli_log_slot_inf(slot, "Set voltage margin to {:s} failed".format(vmarg_param), level=0)
            return False
        nic_cmd = "vmarg.sh {:s}".format(vmarg_param)
        self._mgmt_handle.sendline(nic_cmd)
        self._mgmt_handle.expect_exact(nic_prompt)
        self._mgmt_handle.sendline("exit")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        self.cli_log_slot_inf(slot, "Set voltage margin to {:s} complete".format(vmarg_param), level=0)

        return True


    def mtp_mgmt_connect_test(self):
        if not self.mtp_mgmt_connect():
            self.set_mtp_status(MTP_Status.MTP_STA_MGMT_FAIL)
            return False

        time.sleep(1)
        self.mtp_mgmt_disconnect()
        return True


    def mtp_check_nic_status(self, slot):
        if self._nic_sta_list[slot] == NIC_Status.NIC_STA_OK:
            return True
        else:
            False


    def mtp_mgmt_pre_post_diag_check(self, intf, slot):
        if intf == "NIC_JTAG":
            cmd = "sys_sanity.sh {:d}".format(slot+1)
            self._mgmt_handle.sendline(cmd)
            self._mgmt_handle.expect_exact(self._mgmt_prompt)
            match = re.findall(r"(valid bit 0x1, +error 0x00)", self._mgmt_handle.before)
            if match:
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_MEM":
            if self.mtp_mgmt_test_nic_mem(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_MGMT":
            if self.mtp_check_nic_status(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_FRU":
            # sanity check
            # all present nic should have been scanned
            # all scanned nic should have been detected
            # sn/mac should match
            if self._nic_scan_prsnt_list[slot] != self._nic_prsnt_list[slot]:
                # scanned, but not present
                if self._nic_scan_prsnt_list[slot]:
                    self.cli_log_slot_err(slot, "NIC is scanned, but not detected by system")
                    return MTP_DIAG_Error.NIC_DIAG_FAIL
                    # prsnet, but not present
                if self._nic_prsnt_list[slot]:
                    self.cli_log_slot_err(slot, "NIC is present, but barcode is not scanned")
                    return MTP_DIAG_Error.NIC_DIAG_FAIL

                # mac/sn should match
            if self._nic_scan_prsnt_list[slot] and self._nic_prsnt_list[slot]:
                if self._nic_scan_sn_list[slot] != self._nic_sn_list[slot]:
                    self.cli_log_slot_err(slot, "NIC SN mismatch, scanned: {:s}, fru: {:s}".format(self._nic_scan_sn_list[slot], self._nic_sn_list[slot]))
                    return MTP_DIAG_Error.NIC_DIAG_FAIL
                if self._nic_scan_mac_list[slot] != self._nic_mac_list[slot]:
                    self.cli_log_slot_err(slot, "NIC MAC mismatch, scanned: {:s}, fru: {:s}".format(self._nic_scan_mac_list[slot], self._nic_mac_list[slot]))
                    return MTP_DIAG_Error.NIC_DIAG_FAIL
            return "SUCCESS"
        else:
            self.mtp_cli_log_slot_err(slot, "Unknown pre diag check module")
            return MTP_DIAG_Error.NIC_DIAG_FAIL


    def mtp_mgmt_get_test_result(self, cmd, test, timeout=30):
        self._mgmt_handle.sendline(cmd)
        self._mgmt_handle.expect_exact(self._mgmt_prompt, timeout)

        # Test    Error code, SUCCESS means pass
        match = re.findall(r"%s +([A-Za-z0-9_]+)" %test, str(self._mgmt_handle.before))
        if match:
            return match[0]
        else:
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT


    def mtp_mgmt_get_test_result_para(self, slot, cmd, test, timeout=30):
        self._nic_handle_list[slot].sendline(cmd)
        self._nic_handle_list[slot].expect_exact(self._nic_prompt_list[slot], timeout)

        # Test    Error code, SUCCESS means pass
        match = re.findall(r"%s +([A-Za-z0-9_]+)" %test, str(self._nic_handle_list[slot].before))
        if match:
            return match[0]
        else:
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT


    def mtp_run_diag_test_seq(self, slot, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None):
        # init command
        if init_cmd:
            if not self.mtp_mgmt_exec_cmd(init_cmd):
                return MTP_DIAG_Error.NIC_DIAG_FAIL

        # log the timestamp in diag log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(test, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd(ts_record_cmd)

        if not self.mtp_mgmt_exec_cmd(diag_cmd, timeout=MTP_Const.DIAG_TEST_TIMEOUT):
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT

        # log the timestamp in diag log
        stop = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(test, str(stop), str(stop-start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd(ts_record_cmd)

        # post command
        if post_cmd:
            if not self.mtp_mgmt_exec_cmd(post_cmd):
                return MTP_DIAG_Error.NIC_DIAG_FAIL

        ret = self.mtp_mgmt_get_test_result(rslt_cmd, test)
        if ret == "TIMEOUT":
            self.mtp_mgmt_jtag_rst()

        return ret


    def mtp_mgmt_jtag_rst(self):
        self.cli_log_inf("Reset the MTP JTAG Interface", level = 0)
        cmd = "cd ~/diag/python/infra/dshell"
        self.mtp_mgmt_exec_cmd(cmd)
        cmd = "./diag -r -c MTP1 -d diagmgr -t dsp_stop"
        self.mtp_mgmt_exec_cmd(cmd)
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
        cmd = "cleantcl.sh"
        self.mtp_mgmt_exec_cmd(cmd)
        self._mgmt_handle.sendline("./diag -r -c MTP1 -d diagmgr -t dsp_start")
        self._mgmt_handle.expect_exact("Test Done: MTP1:DIAGMGR:DSP_START")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
        self.cli_log_inf("Reset the MTP JTAG Interface complete", level = 0)


    def mtp_run_diag_test_para(self, slot, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None):
        # init command
        if init_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, init_cmd):
                return MTP_DIAG_Error.NIC_DIAG_FAIL

        # log the timestamp in diag log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(test, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)

        if not self.mtp_mgmt_exec_cmd_para(slot, diag_cmd, timeout=MTP_Const.DIAG_TEST_TIMEOUT):
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT

        # log the timestamp in diag log
        stop = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(test, str(stop), str(stop-start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)

        # post command
        if post_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, post_cmd):
                return MTP_DIAG_Error.NIC_DIAG_FAIL

        ret = self.mtp_mgmt_get_test_result_para(slot, rslt_cmd, test)
        return ret



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

            nic_scan_rslt["NIC_VALID"] = True
            nic_scan_rslt["NIC_SN"] = sn
            nic_scan_rslt["NIC_MAC"] = mac
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
                tmp = "        TS: " + scan_rslt[key]["NIC_TS"]
                config_lines.append(tmp)
            else:
                tmp = "        VALID: \"No\""
                config_lines.append(tmp)

        for line in config_lines:
            file_p.write(line + "\n")
