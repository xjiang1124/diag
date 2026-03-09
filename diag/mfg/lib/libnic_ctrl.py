import time
import os
import libmfg_utils
import re
import json
import traceback
import pexpect
import threading

from datetime import datetime
from libdefs import NIC_Type
from libdefs import MTP_TYPE
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MTP_Const
from libdefs import NIC_Status
from libdefs import NIC_Port_Mask
from libdefs import MFG_DIAG_CMDS
from libdefs import MFG_DIAG_SIG
from libdefs import Swm_Test_Mode
from libdefs import FF_Stage
from libdefs import FF_Stage

from libmfg_cfg import *
from libsku_utils import *

class nic_ctrl():
    def __init__(self, slot, diag_log_filep, diag_cmd_log_filep=None, dbg_mode = False):
        self._slot = slot
        self._debug_mode = dbg_mode
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._nic_status = NIC_Status.NIC_STA_POWEROFF
        self._nic_missed_fa = False
        self._nic_con_prompt = "# "
        self._nic_con_zephyr_prompt = "uart:~$ "
        self._nic_con_suc_prompt = "suc:~$ "
        self._nic_con_vulcano_prompt = "vulcano:~$ "

        self._diag_ver = None
        self._diag_util_ver = None
        self._diag_asic_ver = None
        self._cpld_ver = None
        self._cpld_ver_min = None
        self._cpld_id = None
        self._cpld_timestamp = None
        self._sn = None
        self._mac = None
        self._pn = None
        self._date = None
        self._pn_format = None # store a regex from class PART_NUMBERS_MATCH
        self._img_timestamp = None
        self._boot_image = None
        self._prod_num = None
        self._hpe_prod_ver = None
        self._dpn = None
        self._sku = None
        self._alom_sn = None
        self._alom_pn = None
        self._alom_prod_num = None
        self._assettagnumber = None
        self._kernel_timestamp = None
        self._fw_json = None
        self._riser_sn = None
        self._riser_progdate = None
        self._loopback_sn = dict()
        self._nic_type = None
        self._nic_handle = None
        self._nic_prompt = None
        self._err_msg = ""
        self._cmd_buf = None
        self._buf_before_sig = ""

        self._asic_type = None
        self._ip_addr = None
        self._fst_pcie_bus = None
        self._fst_eth_mnic = None
        self._emmc_mfr_id = ""

        self._refresh_required = True
        self._failed_console_boot = False

        self._fpga_updated = False
        self._gold_fpga_updated = False 

        self._mtp_type = ""
        self.stop_on_err = False

    def nic_handle_init(self, handle, prompt):
        self._nic_handle = handle
        self._nic_prompt = prompt
        self._nic_handle.logfile_read = self._diag_filep
        self._nic_handle.logfile_send = self._diag_cmd_filep

    def nic_handle_close(self):
        self._nic_handle.logfile_send = None
        self._nic_handle.logfile_read = None
        self._nic_handle.close()

    def nic_set_type(self, nic_type):
        self._nic_type = nic_type
        self._nic_status = NIC_Status.NIC_STA_OK
        self.nic_set_asic_type()

    def nic_set_pn(self, new_pn):
        self._pn = new_pn
        # needed for capri:
        pn, pn_regex = libmfg_utils.part_number_lookup(new_pn)
        if pn:
            self._pn_format = pn_regex

    def nic_set_err_msg(self, err_msg):
        if "$" in err_msg:
            err_msg = err_msg.replace("$", "DOLLOR")
        if "#" in err_msg:
            err_msg = err_msg.replace("#", "HASH")
        if not self._err_msg:
            self._err_msg = ""
        self._err_msg += "\n" + err_msg


    def nic_set_cmd_buf(self, cmd_buf):
        self._cmd_buf = cmd_buf


    def nic_set_status(self, status):
        self._nic_status = status
        if self._nic_status != NIC_Status.NIC_STA_OK:
            self._nic_missed_fa = True


    def nic_check_status(self):
        if self._nic_status == NIC_Status.NIC_STA_OK:
            return True
        else:
            return False

    def nic_missed_fa(self):
        return self._nic_missed_fa

    def nic_clear_fa(self):
        self._nic_missed_fa = False

    def nic_hide_prompt(self, cmd_buf):
        # "[timestamp] root# abcd" --> "# abcd"
        prompt_rgx = r'\[\d{4}-\d{1,2}-\d{1,2}_\d{1,2}:\d{1,2}.*\] '+NIC_MGMT_USERNAME
        return re.split(prompt_rgx, cmd_buf)[0]

    def nic_set_asic_type(self):
        if self._nic_type == None:
            self._asic_type = None
        elif self._nic_type in ELBA_NIC_TYPE_LIST:
            self._asic_type = "elba"
        elif self._nic_type in CAPRI_NIC_TYPE_LIST:
            self._asic_type = "capri"
        elif self._nic_type in GIGLIO_NIC_TYPE_LIST:
            self._asic_type = "giglio"
        elif self._nic_type in SALINA_NIC_TYPE_LIST:
            self._asic_type = "salina"
        elif self._nic_type in VULCANO_NIC_TYPE_LIST:
            self._asic_type = "vulcano"

    def mtp_exec_cmd(self, cmd, timeout=MTP_Const.OS_CMD_DELAY, sig_list=[]):
        rc = True
        self._nic_handle.sendline(cmd)
        cmd_before = ""
        self._buf_before_sig = ""
        for sig in sig_list:
            idx = libmfg_utils.mfg_expect(self._nic_handle, [sig], timeout)
            self._buf_before_sig += self._nic_handle.before
            if idx < 0:
                rc = False
                cmd_before = self._nic_handle.before
                break
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
        # signature match fails
        if not rc:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        elif idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            com_buffer_lines = self._nic_handle.before.splitlines()
            self.nic_set_err_msg("Encountered script timeout with command buffer:")
            if len(com_buffer_lines) > 50:
                com_buffer_lines = com_buffer_lines[-50:]
            for line in com_buffer_lines:
                self.nic_set_err_msg(str(repr(line)))
            return False
        else:
            self.nic_set_cmd_buf(self._buf_before_sig + self._nic_handle.before)
        return True

    def mtp_get_info(self, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        info_buf = self._nic_handle.before
        info_buf = re.split(r'\[\d{4}-\d{1,2}-\d{1,2}_\d{1,2}:\d{1,2}.*\]', info_buf)[0]
        self.nic_set_cmd_buf(self._nic_handle.before)

        return info_buf

    def nic_prompt_cfg(self, timeout=MTP_Const.NIC_CON_CMD_DELAY_10):
        r"""
        try to set vaiable PS1 to '[$(date +%Y-%m-%d_%H:%M:%S)]\u# '
        return False if timeout, otherwise return True
        """

        self._nic_handle.sendline(r'PS1="[$(date +%Y-%m-%d_)\\t] \u' + self._nic_con_prompt + '"')
        idx = libmfg_utils.mfg_expect(self._nic_handle, [("root" + self._nic_con_prompt)], timeout)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        return True

    def nic_sync_mtp_timestamp(self, timeout=MTP_Const.NIC_CON_CMD_DELAY):
        """
        try to set nic system time
        this function only called when console login, since for ssh login, nic system time will set by nic_test.py
        return False if timeout, otherwise return True
        """
        currentTime = datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
        self._nic_handle.sendline("date -s " + currentTime)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        return True

    def nic_exec_rst_cmd(self, nic_rst_cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY, dontwait=False):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot)
        cmd = libmfg_utils.get_ssh_connect_cmd(NIC_MGMT_USERNAME, ipaddr)
        self._nic_handle.sendline(cmd)
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:", self._nic_con_prompt], timeout=MTP_Const.SSH_PASSWORD_DELAY)
            if idx < 0:
                libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
            if idx == 0:
                self._nic_handle.sendline(NIC_MGMT_PASSWORD)
                continue
            else:
                break
        cmd_buf = self._nic_handle.before

        if not self.nic_prompt_cfg():
            return False

        self._nic_handle.sendline(nic_rst_cmd)
        # Here ssh should disconnected automatically, unless dontwait=True..in which case kill console ourselves and powercycle.
        if not dontwait:
            nic_exp_prompts = [self._nic_prompt]
        else:
            nic_exp_prompts = [self._nic_prompt, self._nic_con_prompt]
        idx = libmfg_utils.mfg_expect(self._nic_handle, nic_exp_prompts, timeout)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        if idx == 1 and dontwait:
            print("CPLD refresh needs powercycle")
            self._nic_handle.sendline("exit")
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_set_cmd_buf(cmd_buf)
            return True

    def nic_exec_cmds(self, nic_cmd_list, timeout=MTP_Const.NIC_CON_CMD_DELAY, fail_sig=None):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot)
        cmd = libmfg_utils.get_ssh_connect_cmd(NIC_MGMT_USERNAME, ipaddr)
        self._nic_handle.sendline(cmd)
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:", self._nic_con_prompt], timeout=MTP_Const.SSH_PASSWORD_DELAY)
            if idx < 0:
                libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
            if idx == 0:
                self._nic_handle.sendline(NIC_MGMT_PASSWORD)
                continue
            else:
                break

        if not self.nic_prompt_cfg():
            return False

        ret = True
        cmd_list = nic_cmd_list[:]
        cmd_list.append("sync")
        for nic_cmd in cmd_list:
            prev_cmd_buf = self._nic_handle.before
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout)
            if idx < 0:
                libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt])
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_cmd_buf(self._nic_handle.before)
                ret = False
                break
            elif fail_sig != None:
                if fail_sig in self._nic_handle.before:
                    self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                    self.nic_set_cmd_buf(self._nic_handle.before)
                    ret = False
                    break
            else:
                pass
            time.sleep(1)

        if ret:
            cmd = "exit"
            if not self.mtp_exec_cmd(cmd):
                return False

            # overwrite buffer from "exit" cmd
            self.nic_set_cmd_buf(prev_cmd_buf) # 2nd last cmd buffer, dont need it for sync command

        return ret


    def nic_get_info(self, nic_cmd, timeout=None):
        tout = MTP_Const.NIC_CON_CMD_DELAY if timeout is None else timeout
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot)
        cmd = libmfg_utils.get_ssh_connect_cmd(NIC_MGMT_USERNAME, ipaddr)
        self._nic_handle.sendline(cmd)
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:", self._nic_con_prompt], timeout=MTP_Const.SSH_PASSWORD_DELAY)
            if idx < 0:
                libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
            elif idx == 0:
                self._nic_handle.sendline(NIC_MGMT_PASSWORD)
                continue
            else:
                break

        if not self.nic_prompt_cfg():
            return False

        self._nic_handle.sendline(nic_cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], tout)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            info_buf = None
        else:
            info_buf = self.nic_hide_prompt(self._nic_handle.before)

        cmd = "exit"
        if not self.mtp_exec_cmd(cmd):
            return False

        self.nic_set_cmd_buf(info_buf)

        return info_buf

    def nic_fst_exec_cmd(self, nic_cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
        """ same function as nic_get_info, except for NIC IP and ssh uses a private key to connect, so no password prompt """
        if self._ip_addr is None:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            self.nic_set_err_msg("No NIC IP defined!")
            return False

        if self._asic_type == "capri":
            cmd = libmfg_utils.get_fst_nic_ssh_cmd_penctl(self._ip_addr, NIC_MGMT_USERNAME)
        else:
            cmd = libmfg_utils.get_fst_nic_ssh_cmd(self._ip_addr, NIC_MGMT_USERNAME, NIC_MGMT_PASSWORD)
        
        self._nic_handle.sendline(cmd + " " + nic_cmd)
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword", self._nic_con_prompt], MTP_Const.NIC_CON_CMD_DELAY)
            if idx < 0:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_cmd_buf(self._nic_handle.before)
                info_buf = None
            elif idx == 0:
                self._nic_handle.sendline(NIC_MGMT_PASSWORD)
            else:
                info_buf = self._nic_handle.before
                break

        self.nic_set_cmd_buf(info_buf)

        return info_buf

    def nic_get_err_msg(self):
        ret = self._err_msg
        self._err_msg = "" #clear it out
        return ret

    def nic_get_cmd_buf(self):
        return self._cmd_buf

    def nic_is_cpld_refresh_required(self):
        return self._refresh_required

    def nic_require_cpld_refresh(self, val):
        """
         Use:
         1. cpld update
         2. nic_require_refresh(True)
         3. if nic_is_refresh_required(): (cpld ref)

         1. cpld update skipped
         2. nic_require_refresh(False)
         3. if nic_is_refresh_required(): (pass)
        """
        self._refresh_required = val

    def mbist_nic_power_on(self):
        cmd = MFG_DIAG_CMDS().SALINA_MBIST_POWER_ON_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False
        libmfg_utils.count_down(MTP_Const.NIC_POWER_ON_DELAY)
        return True

    def nic_power_off(self):
        cmd = MFG_DIAG_CMDS().NIC_POWER_OFF_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False
        libmfg_utils.count_down(MTP_Const.NIC_POWER_OFF_DELAY)
        return True


    def nic_power_on(self, uart_selection='0', proto_mode='1'):
        '''
        Parameter uart_selection and prod_mode are only for Salina cards
        uart_selection, 0(detault) means switch uart to A35 when boot, 1 means switch uart to N1
        proto_mode, 0 mean put salina into proto_mode(A1 and A35 won't boot), non-zero means normal mode
        '''
        cmd = MFG_DIAG_CMDS().NIC_POWER_ON_FMT.format(self._slot+1)
        if self._nic_type in SALINA_NIC_TYPE_LIST:
            cmd += " " + uart_selection + " " + proto_mode
        if not self.mtp_exec_cmd(cmd):
            return False
        # For Matera + Malfa, if Such error happend, workaround is sleep 10 seconds then re-send the turn on command again
        if "Error: Read failed".lower() in self.nic_get_cmd_buf().lower() and "Empty slot".lower() in self.nic_get_cmd_buf().lower():
            libmfg_utils.count_down(10)
            cmd = MFG_DIAG_CMDS().NIC_POWER_ON_FMT.format(self._slot+1)
            if self._nic_type in SALINA_NIC_TYPE_LIST:
                cmd += " " + uart_selection + " " + proto_mode
            if not self.mtp_exec_cmd(cmd):
                return False
        libmfg_utils.count_down(MTP_Const.NIC_POWER_ON_DELAY)
        return True


    def nic_power_cycle(self, delay=0):
        if not self.nic_power_off():
            return False
        if delay > 0:
            libmfg_utils.count_down(delay)
        if not self.nic_power_on():
            return False
        return True

    def nic_console_attach_without_login(self, consoleObj=None, maxRetry=5, timeOut=None):
        """
        this method send "spawn console connection" command to current self._nic_handle or passed in console connection object, so self._nic_handle become console connection.
        if console object arugument provided, means setup console connection could be from three pin header
        otherwise, setup conosle connection though con_connect
        """

        linux_prompts = libmfg_utils.get_linux_prompt_list()
        time_out = timeOut if timeOut else MTP_Const.NIC_CON_INIT_DELAY
        console_login_screen = ""
        if consoleObj:
            # under construnction
            pass
        else:
            for _ in range(maxRetry):
                self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_DIAG_STOP_PICOCOM_FMT)
                idx = libmfg_utils.mfg_expect(self._nic_handle, linux_prompts, timeout=time_out)
                console_login_screen += self._nic_handle.before
                if idx < 0:
                    continue
                con_ts = libmfg_utils.timestamp_snapshot()
                ts_record_cmd = "#######= {:s} =#######".format(str(con_ts))
                self._nic_handle.sendline(ts_record_cmd)
                idx = libmfg_utils.mfg_expect(self._nic_handle, linux_prompts, timeout=time_out)
                console_login_screen += self._nic_handle.before
                if idx < 0:
                    continue
                cmd = MFG_DIAG_CMDS().NIC_CON_ATTACH_FMT.format(self._slot+1)
                self._nic_handle.sendline(cmd)
                idx = libmfg_utils.mfg_expect(self._nic_handle, ["Terminal ready", "buffer cleared"], timeout=time_out)
                console_login_screen += self._nic_handle.before
                if idx >= 0:
                    break
            else:
                self.nic_set_err_msg("{:s} failed in {:d} retries- occupied or missing".format(cmd, maxRetry))
                self.nic_set_cmd_buf(console_login_screen)
                return False
            self.nic_set_cmd_buf(console_login_screen)
            return True

    def wait_nic_bootup(self, pc_iter, expect_str=None, consoleObj=None, timeOut=None):
        """
        wait for nic fw to boot up from console connection, which established from self._nic_handle or passed in console connection object.
        return the boot screen
        """

        time_out = timeOut if timeOut else MTP_Const.NIC_CON_INIT_DELAY + 20   # 20 seconds is the power cycle command execution time
        time_out *= pc_iter
        exp_list = [pexpect.TIMEOUT, pexpect.EOF]
        see_expect_str = True
        if expect_str:
            exp_list.append(expect_str)
            see_expect_str = False
        nic_boot_screen = ""

        while True:
            idx =  self._nic_handle.expect(exp_list, timeout=time_out)
            if idx == 0:
                nic_boot_screen += self._nic_handle.before
                break
            elif idx == 1:
                # EOF, need re-establish console session
                nic_boot_screen += self._nic_handle.before
                if not self.nic_console_attach_without_login(consoleObj, time_out):
                    nic_boot_screen += self.nic_get_cmd_buf()
                    break
            elif idx == 2:
                nic_boot_screen += self._nic_handle.before + self._nic_handle.after
                see_expect_str = True
                break

        self.nic_set_cmd_buf(nic_boot_screen)
        return see_expect_str

    def nic_console_probe_login_prompt(self, consoleObj=None, maxRetry=5, timeOut=None):
        """
        this method trying to probe if card boot to login prompt from console connection, which established from self._nic_handle or passed in console connection object
        return True if see login prompt otherwise return False
        """

        time_out = timeOut if timeOut else MTP_Const.NIC_CON_INIT_DELAY
        exp_list = [pexpect.TIMEOUT, pexpect.EOF] + [self._nic_con_prompt, "login:", "assword:"]
        console_login_screen = ""
        see_login_prompt = False

        # send return
        self._nic_handle.sendline("")
        # Forio need another enter to connect console
        if self._nic_type == NIC_Type.FORIO or self._nic_type == NIC_Type.VOMERO:
            self._nic_handle.sendline("")

        retry = 1
        while True:
            idx =  self._nic_handle.expect(exp_list, timeout=time_out)
            # print(self._nic_handle.before)
            if idx == 0:
                # timeout, just send a carriage return and retry
                console_login_screen += self._nic_handle.before
                if retry == maxRetry:
                    break
                self._nic_handle.sendline("")
                retry += 1
                time_out = 10
            elif idx == 1:
                # EOF, need re-establish console session
                console_login_screen += self._nic_handle.before
                if self.nic_console_attach_without_login(consoleObj, maxRetry, time_out):
                    self._nic_handle.sendline("")
                    retry += 1
                    continue
                else:
                    break
            elif idx == 2:
                self._nic_handle.sendline("exit")
                continue
            elif idx == 3 or idx == 4:
                console_login_screen += self._nic_handle.before + self._nic_handle.after
                see_login_prompt = True
                break

        # expect extral login prompt "login:"
        while True:
            idx =  self._nic_handle.expect(exp_list, timeout=3)
            if idx == 0:
                break
            else:
                continue

        self.nic_set_cmd_buf(console_login_screen)
        if not see_login_prompt:
            self.nic_set_err_msg("failed to probe login prompt in {:d} retries".format(maxRetry))
            return False
        return True

    def nic_console_login(self, consoleObj=None, username=NIC_MGMT_USERNAME, password=NIC_MGMT_PASSWORD, maxRetry=5, timeOut=None):
        """
        this method trying to login to card with specified username and password from console connection, which established from self._nic_handle or passed in console connection object
        """

        if not self.nic_console_probe_login_prompt(consoleObj, maxRetry, timeOut):
            return False

        time_out = timeOut if timeOut else MTP_Const.NIC_CON_INIT_DELAY
        exp_list = [pexpect.TIMEOUT, pexpect.EOF] + [self._nic_con_prompt, "login:", "assword:"]
        console_login_screen = ""
        sucess_logon = False

        retry = 1
        while True:
            idx =  self._nic_handle.expect(exp_list, timeout=time_out)
            # print(self._nic_handle.before)
            if idx == 0:
                # timeout, just send a carriage return and retry
                console_login_screen += self._nic_handle.before
                if retry == maxRetry:
                    break
                self._nic_handle.sendline("")
                retry += 1
                time_out = 10
            elif idx == 1:
                # EOF, need re-establish console session
                console_login_screen += self._nic_handle.before
                if self.nic_console_attach_without_login(consoleObj, maxRetry, time_out):
                    self._nic_handle.sendline("")
                    retry += 1
                    continue
                else:
                    break
            elif idx == 2:
                console_login_screen += self._nic_handle.before + self._nic_handle.after
                sucess_logon = True
                break
            elif idx == 3:
                self._nic_handle.sendline(username)
                console_login_screen += self._nic_handle.before + self._nic_handle.after
                time_out = 5
                continue
            elif idx == 4:
                self._nic_handle.sendline(password)
                console_login_screen +=  self._nic_handle.before + self._nic_handle.after
                time_out = 10
                continue

        self.nic_set_cmd_buf(console_login_screen)
        if not sucess_logon:
            self.nic_set_err_msg("failed to login in {:d} retries".format(maxRetry))
            return False

        if not self.nic_sync_mtp_timestamp():
            return False
        if not self.nic_prompt_cfg():
            return False

        return True

    def nic_console_exec_cmd(self, cmd=None):
        """
        execute passed in command in a existing NIC console connection, which established from self._nic_handle.
        """

        rc = True
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_err_msg("{:s} failed - occupied or missing".format(cmd))
            rc = False
        self.nic_set_cmd_buf(self._nic_handle.before)
        return rc

    def nic_console_attach(self, uart_selecttor=None):
        # Terminate connected device before the new connection
        if self._mtp_type == MTP_TYPE.PANAREA:
            if str(uart_selecttor) == "0":
                cmd = MFG_DIAG_CMDS().PANAREA_NIC_DIAG_STOP_PICOCOM_FMT.format(str(self._slot + 1))
            elif str(uart_selecttor) == "2":
                cmd = MFG_DIAG_CMDS().PANAREA_NIC_DIAG_STOP_VULCANO_UART_FMT.format(str(self._slot))
            elif str(uart_selecttor) == "1":
                cmd = MFG_DIAG_CMDS().PANAREA_NIC_DIAG_STOP_FPGA_UART_FMT.format(str(self._slot))
            else:
                cmd = MFG_DIAG_CMDS().PANAREA_NIC_DIAG_STOP_FPGA_UART_FMT.format(str(self._slot))
            self._nic_handle.sendline(cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [":$"], timeout=10)
            # Check if there is still got picocom process running
            if str(uart_selecttor) == "0":
                cmd = MFG_DIAG_CMDS().PANAREA_NIC_DIAG_CHECK_PICOCOM_FMT.format(str(self._slot + 1))
            elif str(uart_selecttor) == "2":
                cmd = MFG_DIAG_CMDS().PANAREA_NIC_DIAG_CHECK_VULCANO_FMT.format(str(self._slot))
            elif str(uart_selecttor) == "1":
                cmd = MFG_DIAG_CMDS().PANAREA_NIC_DIAG_CHECK_SOC_FMT.format(str(self._slot))
            else:
                cmd = MFG_DIAG_CMDS().PANAREA_NIC_DIAG_CHECK_SOC_FMT.format(str(self._slot))
            self._nic_handle.sendline(cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [":$"], timeout=10)
        elif self._mtp_type == MTP_TYPE.MATERA:
            cmd = MFG_DIAG_CMDS().MATERA_NIC_DIAG_STOP_PICOCOM_FMT.format(str(self._slot))
            self._nic_handle.sendline(cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["$"], timeout=10)
            # Check if there is still got picocom process running
            self._nic_handle.sendline(MFG_DIAG_CMDS().MATERA_NIC_DIAG_CHECK_PICOCOM_FMT.format(str(self._slot)))
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["$"], timeout=10)
        else:
            self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_DIAG_STOP_PICOCOM_FMT)
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["$"], timeout=10)
            # Check if there is still got picocom process running
            self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_DIAG_CHECK_PICOCOM_FMT)
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["$"], timeout=10)

        cmd = MFG_DIAG_CMDS().NIC_CON_ATTACH_FMT.format(self._slot+1)
        if uart_selecttor is not None:
            cmd += ' ' + str(uart_selecttor)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["Terminal ready", "buffer cleared"], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_err_msg("{:s} failed - occupied or missing".format(cmd))
            return False
        if self._nic_type in SALINA_NIC_TYPE_LIST and ( not uart_selecttor ):
            self.nic_send_ctrl_c()
        time.sleep(5)
        # send return
        if self._nic_type in VULCANO_NIC_TYPE_LIST:
            self._nic_handle.send('\r\n')
        else:
            self._nic_handle.sendline("")
        # TODO: Forio need another enter to connect console
        if self._nic_type == NIC_Type.FORIO or self._nic_type == NIC_Type.VOMERO:
            self._nic_handle.sendline("")

        exp_list = [self._nic_con_prompt, "login:", "assword:", self._nic_con_zephyr_prompt,  self._nic_con_suc_prompt,  self._nic_con_vulcano_prompt]
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, exp_list, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx in [0, 3, 4, 5]:
                break
            elif idx == 1:
                self._nic_handle.sendline(NIC_MGMT_USERNAME)
                continue
            elif idx == 2:
                self._nic_handle.sendline(NIC_MGMT_PASSWORD)
                continue
            else:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_set_err_msg("Timeout connecting to UART console")
                self.nic_console_detach()
                return False
        # for Salina, we still need sync time for leni, only skip zephyr console
        if self._mtp_type in [MTP_TYPE.MATERA]:
            if str(uart_selecttor) == "0":
                while True:
                    idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt, self._nic_con_zephyr_prompt], timeout=3)
                    if idx == 0:
                        break
                    elif idx == 1:
                        continue
                    else:
                        break
                return True

        # for vulcano, skip sync time for all no matter the uart selector
        if self._mtp_type in [MTP_TYPE.PANAREA]:
            while True:
                idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt, self._nic_con_zephyr_prompt, self._nic_con_suc_prompt,  self._nic_con_vulcano_prompt], timeout=3)
                if idx == 0:
                    break
                elif idx == 1:
                    continue
                else:
                    break
            return True

        if not self.nic_sync_mtp_timestamp():
            self.nic_console_detach()
            return False
        if not self.nic_prompt_cfg():
            self.nic_console_detach()
            return False

        return True


    def nic_console_detach(self):
        self._nic_handle.sendcontrol('a')
        self._nic_handle.sendcontrol('x')
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            return False
        else:
            return True

    def nic_console_attach_fast(self):
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_DIAG_STOP_PICOCOM_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["$"], timeout=3)

        con_ts = libmfg_utils.timestamp_snapshot()
        ts_record_cmd = "#######= {:s} =#######".format(str(con_ts))
        self._nic_handle.sendline(ts_record_cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["$"], timeout=4)

        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_CON_ATTACH_FMT.format(self._slot+1))
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["Terminal ready", "buffer cleared"], timeout=2)
        if idx < 0:
            return False
        time.sleep(2)
        # send return
        self._nic_handle.sendline("")
        # TODO: Forio need another enter to connect console
        if self._nic_type == NIC_Type.FORIO or self._nic_type == NIC_Type.VOMERO:
            self._nic_handle.sendline("")

        exp_list = [self._nic_con_prompt, "login:", "assword:"]
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, exp_list, timeout=2)
            if idx == 0:
                break
            elif idx == 1:
                self._nic_handle.sendline(NIC_MGMT_USERNAME)
                continue
            elif idx == 2:
                self._nic_handle.sendline(NIC_MGMT_PASSWORD)
                continue
            else:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach_fast()
                return False

        if not self.nic_sync_mtp_timestamp():
            self.nic_console_detach_fast()
            return False
        if not self.nic_prompt_cfg():
            self.nic_console_detach_fast()
            return False

        return True


    def nic_console_detach_fast(self):
        self._nic_handle.sendcontrol('a')
        self._nic_handle.sendcontrol('x')
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=2)
        if idx < 0:
            return False
        else:
            return True

    def nic_console_test(uart_selecttor=None):
        def nic_console_test_section(func):
            def start_end(self, *args, **kwargs):
                uart_sel = uart_selecttor
                # For Salina DPU cards, made the default uart_sekector to N1, namely uart selector to 1
                if self._nic_type in SALINA_DPU_NIC_TYPE_LIST:
                    if uart_selecttor is None:
                        uart_sel = "1"
                # For Vulcano cards, made the default uart_sekector to uC, namely uart selector to 1
                if self._nic_type in VULCANO_NIC_TYPE_LIST:
                    if uart_selecttor is None:
                        uart_sel = "1"
                if not self.nic_console_attach(uart_sel):
                    self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
                    return False
                ret = func(self, *args, **kwargs)
                if not self.nic_console_detach():
                    self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
                    return False
                return ret
            return start_end
        return nic_console_test_section

    def nic_fast_console_test_section(func):
        def start_end(self, *args, **kwargs):
            if not self.nic_console_attach_fast():
                self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
                return False
            ret = func(self, *args, **kwargs)
            if not self.nic_console_detach_fast():
                self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
                return False
            return ret
        return start_end

    def nic_send_ctrl_c(self):
        self._nic_handle.sendcontrol('c')
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            return False
        
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            return False

        return True

    def nic_stop_test(self):
        cmd_buf = self.nic_get_cmd_buf()    #save failure buffer
        self.nic_send_ctrl_c()
        self.mtp_exec_cmd(MFG_DIAG_CMDS().NIC_DIAG_STOP_TCLSH_FMT)
        self._cmd_buf = cmd_buf             #reset the cmd_buf to failure buffer

    def nic_salina_jtag_mbist(self, vmarg="normal", test_type="warm"):
        '''
        run mbist from jtag, salina cards only
        '''

        if not self.nic_power_cycle(delay=10):
            return False

        # goto the asic dir
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        if test_type in ("warm", "cold"):
            cmd = MFG_DIAG_CMDS().MATERA_MTP_SALINA_NIC_JTAG_MBIST.format(self._sn, str(self._slot+1), vmarg, test_type)
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
                return False
            if MFG_DIAG_SIG.MATERA_NIC_SALINA_JTAG_MBIST_SIG not in self.nic_get_cmd_buf():
                return False
        else:
            cmd = MFG_DIAG_CMDS().MATERA_MTP_SALINA_NIC_JTAG_MBIST_WITH_TEST_LIST.format(self._sn, str(self._slot+1), vmarg, "cold", "ALGO22")
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
                return False

        return True

    def nic_vulcano_jtag_mbist(self, vmarg="normal", test_type="warm"):
        '''
        run pcie prbs, vulcano cards only
        '''

        if not self.nic_power_cycle(delay=10):
            return False

        # goto the asic dir
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().PANAREA_MTP_VULCANO_NIC_JTAG_MBIST.format(self._sn, str(self._slot+1), vmarg)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
            return False

        return True

    def nic_snake_mtp_salina(self, snake_type='esam_pktgen_max_power_sor', vmarg="normal", dura=120, timeout=3600, slot_asic_dir_path=None, ite='1', int_lpbk='0'):
        '''
            run salina snake from mtp without mgmt
        '''

        if not slot_asic_dir_path:
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MATERA_NIC_SNAKE_MTP_FMT.format(str(self._slot + 1), timeout, dura, snake_type, vmarg, self._nic_type, slot_asic_dir_path, ite, int_lpbk)
        cmd += " | tee {:s}/snake_{:s}_{:s}_slot{:s}.log".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR, snake_type, str(self._sn), str(self._slot + 1))
        print(cmd)
        if not self.mtp_exec_cmd(cmd, timeout=timeout+30):
            return False

        if MFG_DIAG_SIG.MATERA_NIC_SNAKE_MTP_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def ainic_snake_mtp_salina(self, snake_type='esam_pktgen_pollara_max_power_pcie_arm', vmarg="normal", dura=900, timeout=3600, slot_asic_dir_path=None, ite='1', int_lpbk='0'):
        '''
            run salina snake from mtp without mgmt
        '''

        if not slot_asic_dir_path:
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        test_name = "max_pwr" if snake_type == "esam_pktgen_pollara_max_power_pcie_arm" else "p4net"
        lt = "0" if self._nic_type == NIC_Type.POLLARA else "1"

        cmd = MFG_DIAG_CMDS().MATERA_AINIC_SNAKE_MTP_FMT.format(str(self._slot + 1), timeout, dura, snake_type, vmarg, self._nic_type, slot_asic_dir_path, ite, int_lpbk, lt)
        cmd += " | tee {:s}/snake_{:s}_{:s}_slot{:s}.log".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR, test_name, str(self._sn), str(self._slot + 1))
        print(cmd)
        if not self.mtp_exec_cmd(cmd, timeout=timeout+30):
            return False

        if MFG_DIAG_SIG.MATERA_AINIC_SNAKE_MTP_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_pcie_prbs_salina(self, vmarg="normal", timeout=300, slot_asic_dir_path=None):
        '''
            run salina snake from mtp without mgmt
        '''

        if not slot_asic_dir_path:
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        test_name = "pcie_prbs"

        cmd = MFG_DIAG_CMDS().MATERA_NIC_PCIE_PRBS_FMT.format(str(self._slot + 1), vmarg, self._nic_type, slot_asic_dir_path)
        cmd += " | tee {:s}/snake_{:s}_{:s}_slot{:s}.log".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR, test_name, str(self._sn), str(self._slot + 1))
        print(cmd)
        if not self.mtp_exec_cmd(cmd, timeout=timeout+30):
            return False

        if MFG_DIAG_SIG.MATERA_AINIC_PCIE_PRBS_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def set_piceawd_env_salina(self, timeout=300):
        '''
            set salina pcieawd env
        '''
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MATERA_SET_PCIEAWD_ENV_FMT.format(str(self._slot + 1))
        print(cmd)
        if not self.mtp_exec_cmd(cmd, timeout=timeout):
            return False

        return True

    def erase_piceawd_env_salina(self, timeout=300):
        '''
            set salina pcieawd env
        '''
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MATERA_ERASE_PCIEAWD_ENV_FMT.format(str(self._slot + 1))
        print(cmd)
        if not self.mtp_exec_cmd(cmd, timeout=timeout):
            return False

        return True

    def i2c_qsfp_salina(self, vmarg="normal", timeout=180):
        '''
            set salina i2c qsfp
        '''
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MATERA_I2C_QSFP_FMT.format(str(self._slot + 1), vmarg)
        if not self.mtp_exec_cmd(cmd, timeout=timeout):
            return False

        if MFG_DIAG_SIG.MATERA_I2C_QSFP_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def i2c_rtc_salina(self, vmarg="normal", timeout=180):
        '''
            set salina i2c rtc
        '''
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MATERA_I2C_RTC_FMT.format(str(self._slot + 1), vmarg)
        if not self.mtp_exec_cmd(cmd, timeout=timeout):
            return False

        if MFG_DIAG_SIG.MATERA_I2C_RTC_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_salina_fix_vrm(self, timeout=300):
        '''
            salina vrm fix
        '''
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MATERA_MTP_SALINA_NIC_VRM_FIX_FMT.format(str(self._slot + 1))
        if not self.mtp_exec_cmd(cmd, timeout=timeout):
            return False

        if MFG_DIAG_SIG.MATERA_SALINA_FIX_VRM_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_i2c_dump(self, timeout=10):
        '''
            dump i2c value
        '''
        cmd = MFG_DIAG_CMDS().NIC_I2C_DUMP_POST_FMT.format(self._slot + 3)
        if not self.mtp_exec_cmd(cmd, timeout=timeout):
            return False

        return True

    @nic_console_test()
    def nic_mgmt_config(self):
        # config the mgmt port
        cmd = MFG_DIAG_CMDS().NIC_SET_MGMT_IP_FMT.format(self._slot+101)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.after)
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self.nic_set_status(NIC_Status.NIC_STA_OK)
        return True

    @nic_console_test()
    def nic_set_extdiag_boot(self):
        # set default to extdiag boot
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_SET_EXTDIAG_BOOT_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS().NIC_SET_EXTDIAG_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    def nic_console_access(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    @nic_console_test()
    def nic_erase_board_config(self):
        # earse board config
        self._nic_handle.sendline(MFG_DIAG_CMDS().ERASE_BOARD_CONFIG_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False
        return True

    @nic_console_test()
    def nic_cpld_update_request(self):
        # get diag boot
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_BOOT_SHOW_RUNNING_IMG_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"(goldfw)", buf)
        if not match:
            return False

        #self.nic_boot_info_reset()


        # get cpld version
        self._nic_handle.sendline("cpldapp -r 0")
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"(0x83)", buf)
        if not match:
            return False

        return True

    @nic_console_test()
    def nic_set_board_config_cert(self, cert_img, directory="/data/"):
        img_name = os.path.basename(cert_img)
        # set ibm board config
        self._nic_handle.sendline(MFG_DIAG_CMDS().SET_IBM_BOARD_CONFIG_FMT.format(directory, img_name))
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"(Config successfully)", buf)
        if not match:
            return False

        # show cert info
        self._nic_handle.sendline(MFG_DIAG_CMDS().GET_BOARD_CONFIG_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"(cert 1 serial: 34:f7:c4:37:67:cf:39:e7:4a:a5:6d:80:b6:b1:66:bf:29:53:f9:7f)", buf)
        if not match:
            return False

        # show fwupdate -l info
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_IMG_DISP1_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    @nic_console_test()
    def nic_secboot_verify(self):
        # send bash command elba-chk-secboot-rdy.sh and it's leading commands
        nic_secboot_verify_cmd_list = [MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT, MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT, MFG_DIAG_CMDS().NIC_CHK_SECBOOT_FMT]
        for nic_cmd in nic_secboot_verify_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
                return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"SUCCESS", buf)
        if not match:
            return False          

        return True

    @nic_console_test()
    def nic_cfg_verify(self):
        # dump cfg0
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_CFG_DUMP_FMT.format("4","0"))
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_err_msg("Unable to get response after issue dump cfg0 command")
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # dump cfg1
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_CFG_DUMP_FMT.format("5","1"))
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_err_msg("Unable to get response after issue dump cfg1 command")
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # md5sum cfg0
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_CFG_CHECKSUM_FMT.format("0"))
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_err_msg("Unable to get response after issue md5sum cfg0 command")
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # md5sum cfg1
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_CFG_CHECKSUM_FMT.format("1"))
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_err_msg("Unable to get response after issue md5sum cfg1 command")
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    @nic_console_test()
    def nic_set_diag_boot(self):
        # set default to diag boot
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_SET_DIAG_BOOT_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS().NIC_SET_DIAG_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    @nic_console_test()
    def nic_set_mainfwa_boot(self):
        # set default to mainfwa boot
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_SET_MAINFWA_BOOT_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS().NIC_SET_MAINFWA_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    @nic_console_test()
    def nic_set_mainfwb_boot(self):
        # set default to mainfwb boot
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_SET_MAINFWB_BOOT_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS().NIC_SET_MAINFWB_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    @nic_console_test()
    def nic_set_goldfw_boot(self):

        if self._nic_type in SALINA_DPU_NIC_TYPE_LIST:
            # set A35 goldfw 
            self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_SET_EXTOSGOLDFW_BOOT_FMT)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
            if idx < 0:
                self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
                return False

        # set default to goldfw boot
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_SET_GOLD_BOOT_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS().NIC_SET_GOLD_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    @nic_console_test()
    def nic_set_extosa_boot(self):
        # set default to extosa boot
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_SET_EXTOSA_BOOT_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS().NIC_SET_EXTOSA_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    @nic_console_test()
    def nic_set_extosb_boot(self):
        # set default to extosb boot
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_SET_EXTOSB_BOOT_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS().NIC_SET_EXTOSB_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    @nic_console_test()
    def nic_sw_cleanup_shutdown(self):
        # 1. remove diag utils on NIC
        # 2. kill all processes
        # 3. sync
        # 4. umount
        emmc_fsck_cmd = MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT
        emmc_mount_cmd = MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT
        nic_shutdown_cmd_list = [emmc_fsck_cmd,
                                 emmc_mount_cmd,
                                 "clear_nic_config.sh factory-default"]

        if self._nic_type == NIC_Type.ORTANO2ADIIBM:
            nic_shutdown_cmd_list += [
                                 "fwenv -n gold -E",
                                 "fwenv -E"
                                 ]
        elif self._nic_type in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) and self._nic_type != NIC_Type.ORTANO2ADIIBM:
            nic_shutdown_cmd_list += [
                                 "fwenv -n gold -E",
                                 "fwenv -n gold",
                                 "fwenv -E",
                                 "fwenv"
                                 ]

        for nic_cmd in nic_shutdown_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                return False

        # poweroff
        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_OS_SHUTDOWN_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [MFG_DIAG_SIG.NIC_OS_SHUTDOWN_OK_SIG], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        return True

    @nic_console_test()
    def nic_sw_shutdown(self, cloud=False, isRelC=False):
        # 1. remove diag utils on NIC
        # 2. kill all processes
        # 3. sync
        # 4. umount
        emmc_fsck_cmd = MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT
        emmc_mount_cmd = MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT
        nic_shutdown_cmd_list = [emmc_fsck_cmd]

        # Rahul: also only for msft remove the mount command as well
        if self._nic_type not in [NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2ADICRMSFT]:
            nic_shutdown_cmd_list.append(emmc_mount_cmd)

        if self._nic_type != NIC_Type.GINESTRA_CIS:
            nic_shutdown_cmd_list += [
                                     MFG_DIAG_CMDS().NIC_IMG_DISP_FMT,
                                     MFG_DIAG_CMDS().NIC_IMG_DISP1_FMT,
                                     MFG_DIAG_CMDS().NIC_DIAG_CLEANUP_FMT,
                                     MFG_DIAG_CMDS().NIC_EMMC_LS_FMT,
                                     MFG_DIAG_CMDS().NIC_KILL_PROCESS_FMT,
                                     MFG_DIAG_CMDS().NIC_SYNC_FS_FMT,
                                     MFG_DIAG_CMDS().NIC_SW_UMOUNT_FMT
                                     ]
        else:
            nic_shutdown_cmd_list += [
                                     MFG_DIAG_CMDS().NIC_IMG_DISP_FMT,
                                     MFG_DIAG_CMDS().NIC_IMG_DISP1_FMT,
                                     MFG_DIAG_CMDS().NIC_DIAG_CLEANUP_FMT,
                                     MFG_DIAG_CMDS().NIC_EMMC_LS_FMT,
                                     MFG_DIAG_CMDS().NIC_SYNC_FS_FMT,
                                     MFG_DIAG_CMDS().NIC_SW_UMOUNT_FMT
                                     ]

        if self._nic_type in [NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2ADICRMSFT]:
            nic_shutdown_cmd_list.pop()
            nic_shutdown_cmd_list.append(MFG_DIAG_CMDS().NIC_SYNC_FS_FMT)
            nic_shutdown_cmd_list.append(MFG_DIAG_CMDS().NIC_SYNC_FS_FMT)
            
        for nic_cmd in nic_shutdown_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                return False

        # Rahul: use penvisorctl command if it msft since msft using use penvisor container and just poweroff if non msft
        # so force isRelC to True so that following call MFG_DIAG_CMDS().NIC_OS_SHUTDOWN_PEN_FMT
        if  self._nic_type in [NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2ADICRMSFT]:
            isRelC = True

        # poweroff ... Cloud build do not support this command & different command for Rel C
        if self._nic_type == NIC_Type.GINESTRA_CIS:
            nic_sync_cmd_list = list()
            nic_sync_cmd_list.append(MFG_DIAG_CMDS().NIC_SYNC_FS_FMT)
            nic_sync_cmd_list.append(MFG_DIAG_CMDS().NIC_SYNC_FS_FMT)
            nic_sync_cmd_list.append(MFG_DIAG_CMDS().NIC_SYNC_FS_FMT)

            for nic_cmd in nic_sync_cmd_list:
                self._nic_handle.sendline(nic_cmd)
                idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
                time.sleep(1)
                if idx < 0:
                    return False
        elif isRelC == True:
            self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_OS_SHUTDOWN_PEN_FMT)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [MFG_DIAG_SIG.NIC_OS_SHUTDOWN_OK_SIG], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False           
        elif cloud == False:
            self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_OS_SHUTDOWN_FMT)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [MFG_DIAG_SIG.NIC_OS_SHUTDOWN_OK_SIG], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False

        return True

    def nic_set_elba_uboot_env(self, slot):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("Execute command {:s} failed".format(cmd))
            return False
        nic_test_uboot_env = MFG_DIAG_CMDS().MTP_PARA_UBOOT_ENV_FMT.format(str(slot+1))
        if not self.mtp_exec_cmd(nic_test_uboot_env):
            self.nic_set_err_msg("nic_test.py -setup_uboot_env failed")
            return False
        return True

    @nic_console_test()
    def nic_sw_mode_switch(self):
        mode_switch_cmd_list = [MFG_DIAG_CMDS().NIC_SW_MODE_SWITCH_FMT,
                                MFG_DIAG_CMDS().NIC_SW_MODE_SWITCH_FMT,
                                "sync"]
        for nic_cmd in mode_switch_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.OS_CMD_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False

        self._nic_handle.sendline("sysreset.sh")
        time.sleep(MTP_Const.NIC_SYSRESET_DELAY)
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        return True

    @nic_console_test()
    def nic_sw_mode_switch_verify(self):
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_SW_DEVICE_CHK_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        dev_profile_match = re.findall(MFG_DIAG_SIG.NIC_SW_DEVICE_CHK_SIG1, cmd_buf)
        if dev_profile_match:
            pass
        else:
            self.nic_set_cmd_buf(cmd_buf)
            return False

        mode_match = re.findall(MFG_DIAG_SIG.NIC_SW_DEVICE_CHK_SIG2, cmd_buf)
        if mode_match:
            pass
        else:
            self.nic_set_cmd_buf(cmd_buf)
            return False

        return True

    @nic_console_test()
    def nic_pdsctl_system_show(self):
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_SW_SYSTEM_CHK_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        die_id_match = re.findall(MFG_DIAG_SIG.NIC_SW_SYSTEM_CHK_SIG1, cmd_buf)
        if die_id_match:
            pass
        else:
            self.nic_set_cmd_buf(cmd_buf)
            return False

        return True

    @nic_console_test()
    def nic_exec_cmd_from_console(self, cmd, timeout=MTP_Const.OS_CMD_DELAY, cmd_prompt=None):
        if cmd_prompt is None:
            cmd_prompt= self._nic_con_prompt
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [cmd_prompt], cmd_prompt, timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [cmd_prompt], cmd_prompt, timeout=timeout)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        self.nic_set_cmd_buf(cmd_buf)
        return True

    @nic_console_test('0')
    def nic_exec_cmd_from_zephyr_console(self, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_zephyr_prompt], self._nic_con_zephyr_prompt, timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_zephyr_prompt], self._nic_con_zephyr_prompt, timeout=timeout)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        self.nic_set_cmd_buf(cmd_buf)
        return True

    @nic_console_test('1')
    def nic_exec_cmd_from_suc_console1(self, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        self._nic_handle.send('\r\n')
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_suc_prompt], self._nic_con_suc_prompt, timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_suc_prompt], self._nic_con_suc_prompt, timeout=timeout)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        self.nic_set_cmd_buf(cmd_buf)
        return True

    @nic_console_test('2')
    def nic_exec_cmd_from_soc_console(self, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        self._nic_handle.sendline('\r\n')
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_vulcano_prompt], self._nic_con_vulcano_prompt, timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_vulcano_prompt], self._nic_con_vulcano_prompt, timeout=timeout)
        if idx < 0:
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            self.nic_set_cmd_buf(cmd_buf)
            return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        self.nic_set_cmd_buf(cmd_buf)
        return True

    @nic_console_test('1')
    def uc_get_zephyr_booting_msg(self, monitor_timeout=30):
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_suc_prompt], self._nic_con_suc_prompt, timeout=monitor_timeout, nic_type=self._nic_type)
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if idx == 0:
            cmd_buf += self._nic_con_suc_prompt
        self.nic_set_cmd_buf(cmd_buf)
        return True

    @nic_console_test('2')
    def uc_get_vulcano_booting_msg(self, monitor_timeout=60):
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_vulcano_prompt], self._nic_con_vulcano_prompt, timeout=monitor_timeout)
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if idx == 0:
            cmd_buf += self._nic_con_vulcano_prompt

        self.nic_set_cmd_buf(cmd_buf)
        return True

    @nic_fast_console_test_section
    def nic_set_i2c_after_pw_cycle(self):
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Unable to get expected prompt")
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_I2C_SET_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Execute command {:s} failed".format(MFG_DIAG_CMDS().NIC_I2C_SET_FMT))
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Execute command {:s} failed".format(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT))
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Execute command {:s} failed".format(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT))
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_WRITE_CPLD_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Execute command {:s} failed".format(MFG_DIAG_CMDS().NIC_WRITE_CPLD_FMT))
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS().NIC_READ_CPLD_FMT)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Execute command {:s} failed".format(MFG_DIAG_CMDS().NIC_READ_CPLD_FMT))
            return False
        
        # cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        # match = re.findall(r".*(0x44).*", cmd_buf)
        # if match:
        #     pass
        # else:
        #     self.nic_set_cmd_buf(cmd_buf)
        #     self.nic_set_err_msg("Incorrect I2C value, expecting {:s}, got {:s}".format("0x44", cmd_buf.strip()))
        #     return False

        return True

    @nic_console_test()
    def nic_read_firmware_image(self, smode=False):
        if smode:
            cmd = MFG_DIAG_CMDS().NIC_BOOT_SHOW_STARTUP_IMG_FMT
        else:
            cmd = MFG_DIAG_CMDS().NIC_BOOT_SHOW_RUNNING_IMG_FMT
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
        if idx < 0:
            self.nic_set_err_msg("Command {:s} failed".format(cmd))
            return False
        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"(\w+fw\w?|extdiag)", buf)
        if match:
            self._boot_image = match[0]
            # check if boot image is valid
            if self._boot_image in MFG_VALID_FW_LIST:
                return True
            else:
                self.nic_set_err_msg("NIC booted from {:s} not allowed here".format(self._boot_image))
                return False

    @nic_console_test()
    def nic_read_kernel_version(self):
        cmd = MFG_DIAG_CMDS().NIC_IMG_VER_DISP_FMT
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
        if idx < 0:
            self.nic_set_err_msg("Command {:s} failed".format(cmd))
            return False
        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"SMP(?: PREEMPT)? (.* 20\d{2})", buf)
        if match:
            kernel_ver = match[0]
            # The %Z specifier in strptime() matches the full name of a timezone (e.g., Pacific Standard Time) or an abbreviation (e.g., PST).
            # However, Python relies on the underlying C library to parse timezone names and abbreviations, and many implementations do not include abbreviations
            # like PST, EST, etc., because they are ambiguous.
            # For example:PST could mean "Pacific Standard Time" or another timezone with the same abbreviation in different contexts.
            if 'PST' in kernel_ver:
                kernel_ver = kernel_ver.replace("PST", "-0800")
                timestamp_format_string =  "%a %b %d %X %z %Y"
            elif 'PDT' in kernel_ver:
                kernel_ver = kernel_ver.replace("PDT", "-0800")
                timestamp_format_string =  "%a %b %d %X %z %Y"
            else:
                timestamp_format_string = "%a %b %d %X %Z %Y"
            # check if timestamp is valid
            try:
                dt = datetime.strptime(kernel_ver, timestamp_format_string)
                self._kernel_timestamp = dt.strftime("%m-%d-%Y")
                return True
            except ValueError:
                self.nic_set_err_msg("Invalid NIC FW kernel version")
                return False

    @nic_console_test()
    def salina_nic_verify_a35_boot_fw_version(self, tartbootver):
        """
        Verify Salina A35 boot image same as specified.
        """
        cmd = MFG_DIAG_CMDS().NIC_BOOT_SHOW_RUNNING_IMG_FMT
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
        if idx < 0:
            self.nic_set_err_msg("Command {:s} failed".format(cmd))
            return False
        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"System\s+firmware\s+:(\w+)", buf)
        if not match:
            self.nic_set_err_msg("Failed to parse a35 boot image from {:s}". format(buf))
            return False
        a35_boot_image = match[0]
        if tartbootver.lower() != a35_boot_image.lower():
            self.nic_set_err_msg("A35 boot to {:s}, while expect it boot to {:s}". format(a35_boot_image, tartbootver))
            return False
        return True

    @nic_console_test()
    def salina_nic_verify_loaded_fw_version(self, goldfw_ver=None, mainfw_ver=None):
        """
        run "fwupdate -l command"
        verify the pass in FW version
        """

        cmd = cmd = MFG_DIAG_CMDS().NIC_IMG_DISP1_FMT
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
        if idx < 0:
            self.nic_set_err_msg("Command {:s} failed".format(cmd))
            return False
        # remove the potential special character
        fw_info_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not fw_info_buf:
            self.nic_set_err_msg("Unable to get 'fwupdate -l' command output")
            return False
        # preprocess fwupdate output for json load 
        sanitized_output = []
        open_brace_cnt = 0
        json_data_start = False
        for line in fw_info_buf.strip().split('\n'):
            if line.startswith("{"):
                json_data_start = True
            if "{" in line:
                open_brace_cnt += 1
            if json_data_start and open_brace_cnt > 0:
                if "{" in line or "}" in line or ":" in line:
                    sanitized_output.append(line)
            if "}" in line:
                open_brace_cnt -= 1

        try:
            fw_info = json.loads('\n'.join(sanitized_output))
        except:
            self.nic_set_err_msg("'fwupdate -l' command output is not formatted as JSON")
            return False

        verify_rc = True
        if goldfw_ver:
            for k, v in fw_info["n1-goldfw"].items():
                if v["software_version"] != goldfw_ver:
                    self.nic_set_err_msg("n1-goldfw {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                    verify_rc = False
            for k, v in fw_info["extosgoldfw"].items():
                if v["software_version"] != goldfw_ver:
                    self.nic_set_err_msg("extosgoldfw {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                    verify_rc = False

        if mainfw_ver:
            for k, v in fw_info["mainfwa"].items():
                if v["software_version"] != mainfw_ver:
                    self.nic_set_err_msg("mainfwa {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                    verify_rc = False
            for k, v in fw_info["extosa"].items():
                if v["software_version"] != mainfw_ver:
                    self.nic_set_err_msg("extosa {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                    verify_rc = False
            for k, v in fw_info["mainfwb"].items():
                if v["software_version"] != mainfw_ver:
                    self.nic_set_err_msg("mainfwb {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                    verify_rc = False
            for k, v in fw_info["extosb"].items():
                if v["software_version"] != mainfw_ver:
                    self.nic_set_err_msg("extosb {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                    verify_rc = False

        return verify_rc

    def nic_google_stress_test(self, vmarg='normal',  mem_copy_thread=16, seconds2run=60, slot_asic_dir_path="/home/diag/diag/asic/"):
        '''
        ./nic_test_v2.py mem_test -slot <slot> -vmarg VMARG -dura DURA -tcl_path TCL_PATH -threads THREADS
        '''

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MATERA_NIC_MEM_TEST_MTP_FMT.format(str(self._slot + 1), slot_asic_dir_path, str(seconds2run), str(vmarg), str(mem_copy_thread))
        nic_test_v2_sub_cmd = "mem_test"
        cmd += " | tee {:s}/nic_test_v2_{:s}_{:s}_slot{:s}.log".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR, nic_test_v2_sub_cmd, str(self._sn), str(self._slot + 1))
        if not self.mtp_exec_cmd(cmd, timeout=int(seconds2run)+1800):
            return False

        if MFG_DIAG_SIG.MATERA_NIC_MEM_TEST_MTP_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_emmc_stress_test(self, vmarg='normal', iterations=1, seconds2run=60, slot_asic_dir_path="/home/diag/diag/asic/"):
        '''
        ./nic_test_v2.py emmc_test -slot <slot> -vmarg VMARG -dura DURA
        '''

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MATERA_NIC_EMMC_TEST_MTP_FMT.format(str(self._slot + 1), str(seconds2run), str(iterations), str(vmarg))
        nic_test_v2_sub_cmd = "emmc_test"
        cmd += " | tee {:s}/nic_test_v2_{:s}_{:s}_slot{:s}.log".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR, nic_test_v2_sub_cmd, str(self._sn), str(self._slot + 1))
        if not self.mtp_exec_cmd(cmd, timeout=int(seconds2run) * int(iterations) + 300):
            return False

        test_result = True
        for iteration in range(iterations):
            if MFG_DIAG_SIG.MATERA_NIC_EMMC_TEST_MTP_SIG.format(iteration) not in self.nic_get_cmd_buf():
                self.nic_set_err_msg("{:s} failed at {:d} ite of {:d}".format(cmd, iteration, iterations))
                test_result = False
        return test_result

    def nic_test_v2_py_edma(self, vmarg='normal', seconds2run=60, slot_asic_dir_path="/home/diag/diag/asic/"):
        '''
        ./nic_test_v2.py edma_test -slot <slot> -vmarg VMARG -dura DURA -tcl_path TCL_PATH
        '''

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MATERA_NIC_EDMA_MTP_FMT.format(str(self._slot + 1), slot_asic_dir_path, str(seconds2run), str(vmarg))
        nic_test_v2_sub_cmd = "edma_test"
        cmd += " | tee {:s}/nic_test_v2_{:s}_{:s}_slot{:s}.log".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR, nic_test_v2_sub_cmd, str(self._sn), str(self._slot + 1))
        if not self.mtp_exec_cmd(cmd, timeout=int(seconds2run)+1800):
            return False

        if MFG_DIAG_SIG.MATERA_NIC_EDMA_MTP_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_clear_pre_uboot_section(self):
        '''
        ./esec_qspi_erase.sh slot <slot>
        '''

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_SCRIPT_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().SALINA_ESEC_QSPI_ERASE_FMT.format(str(self._slot + 1))
        if not self.mtp_exec_cmd(cmd):
            return False

        if MFG_DIAG_SIG.NIC_CLEAR_UBOOT_FAIL_SIG in self.nic_get_cmd_buf():
            return False

        return True

    def nic_boot_info_init(self, smode=False):
        # save boot image info into self._boot_image and self._kernel_timestamp
        previous_card_status = self.nic_check_status()

        loop = 0
        while loop < MTP_Const.NIC_CON_CMD_RETRY:
            if not self.nic_read_firmware_image(smode):
                loop += 1
                continue
            else:
                break

        if loop >= MTP_Const.NIC_CON_CMD_RETRY:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        elif previous_card_status:
            self.nic_set_status(NIC_Status.NIC_STA_OK)

        # get kernel build timestamp
        loop = 0
        while loop < MTP_Const.NIC_CON_CMD_RETRY:
            if not self.nic_read_kernel_version():
                loop += 1
                continue
            else:
                break

        if loop >= MTP_Const.NIC_CON_CMD_RETRY:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        elif previous_card_status:
            self.nic_set_status(NIC_Status.NIC_STA_OK)

        return True

    def nic_boot_info_reset(self):
        self._boot_image = None
        self._kernel_timestamp = None


    def nic_pcie_poll_enable(self, enable):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        if enable:
            sig = MFG_DIAG_SIG.NIC_UBOOT_PCIE_ENA_SIG
            cmd = MFG_DIAG_CMDS().MTP_NIC_PCIE_LINK_POLL_ENABLE_FMT.format(self._slot+1)
        else:
            sig = MFG_DIAG_SIG.NIC_UBOOT_PCIE_DIS_SIG
            cmd = MFG_DIAG_CMDS().MTP_NIC_PCIE_LINK_POLL_DISABLE_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, MTP_Const.NIC_CON_CMD_DELAY):
            return False

        if sig in self.nic_get_cmd_buf():
            return True
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False


    def nic_mgmt_init(self, fpo):
        # goto the nic_con dir
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if fpo:
            cmd = MFG_DIAG_CMDS().NIC_FPO_MGMT_INIT_FMT.format(self._slot+1)
        else:
            cmd = MFG_DIAG_CMDS().NIC_MGMT_INIT_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if MFG_DIAG_SIG.NIC_MGMT_OK_SIG in self.nic_get_cmd_buf():
            return True
        else:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True


    def nic_test_mem(self):
        # goto the nic_con dir
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().NIC_CON_MTEST_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
            return False
        if MFG_DIAG_SIG.NIC_CON_MTEST_PASS_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_check_jtag(self, mtp_type):
        cmd = MFG_DIAG_CMDS().NIC_JTAG_TEST_FMT.format(self._slot+1)

        fail_sig_list = ["JTAG Read failed!"]

        sig_list = ["valid bit 0x1", "error 0x00"]
        if mtp_type == MTP_TYPE.ELBA:
            sig_list = ["0x00000001"]
        elif mtp_type == MTP_TYPE.TURBO_ELBA:
            sig_list = ["0x00000001"]

        error_flag = False

        if not self.mtp_exec_cmd(cmd):
            error_flag = True

        cmd_buf = self.nic_get_cmd_buf()

        # Skip checking for now
        # if not True in [sig in cmd_buf for sig in sig_list]:
        #     error_flag = True

        if True in [sig in cmd_buf for sig in fail_sig_list]:
            error_flag = True

        if error_flag:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            self.nic_set_cmd_buf(cmd_buf)

        if error_flag:
            return False

        return True

    def nic_power_check(self):
        cmd = MFG_DIAG_CMDS().NIC_POWER_CHECK_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_PWR_FAIL)
            return False

        if MFG_DIAG_SIG.NIC_POWER_OK_SIG in self.nic_get_cmd_buf():
            return True
        else:
            self.nic_set_status(NIC_Status.NIC_STA_PWR_FAIL)
            # dump power rail status
            cmd = MFG_DIAG_CMDS().NIC_POWER_RAIL_DISP_FMT.format(self._slot+1)
            self.mtp_exec_cmd(cmd)
            return False

    def nic_dump_fru(self, expect_sn="", expect_mac="", expect_pn=""):
        """
         Use-case 1:
         - dump fru and print to log (no expect_* arguments supplied)
         Use-case 2:
         - dump fru and match any/all of 
            - expect_sn
            - expect_mac [format as 00AECDXXXXXX]
            - expect_pn

        Hexdump steps:
            eeutil -dump -numBytes=512
            hexdump -C eeprom
            xxd -p -l6 -sOFFSET eeprom      --> get MAC
            strings eeprom                  --> get SN, PN
        """
        nic_cmd_list = list()
        nic_cmd_list.append("rm eeprom")
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FRU_DUMP_FMT)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False

        mac_address_offset = "115"  # hardcoded for naples25swm
        cmd_buf = self.nic_get_info("xxd -p -l6 -s{:s} eeprom".format(mac_address_offset))

        mac_dump_match = re.search("([A-Fa-f0-9]{12})", cmd_buf)
        if not mac_dump_match:
            self.nic_set_err_msg("Failed to extract mac address from NIC FRU dump")
            self.nic_set_err_msg(cmd_buf)
            return False
        mac_address_dump = mac_dump_match.group(0).upper()
        mac = libmfg_utils.mac_address_validate(mac_address_dump)
        if not mac:
            self.nic_set_err_msg("Invalid NIC MAC Address: {:s} detected\n".format(mac_address_dump))
            return False
        if expect_mac != "":
            if expect_mac.upper() != mac.upper():
                self.nic_set_err_msg("NIC MAC Address did not match: expect {:s}, read {:s}\n".format(expect_mac, mac))
                return False

        return True

    def mtp_nic_dump_fru(self, expect_sn="", expect_mac="", expect_pn=""):
        cmd = "rm eeprom"
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False
        cmd = MFG_DIAG_CMDS().MTP_NIC_FRU_DUMP_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False
        mac_address_offset = "115"  # hardcoded for naples25swm
        cmd = "xxd -p -l6 -s{:s} eeprom".format(mac_address_offset)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False
        cmd_buf = self.nic_get_cmd_buf()

        mac_dump_match = re.search("([A-Fa-f0-9]{12})", cmd_buf)
        if not mac_dump_match:
            self.nic_set_err_msg("Failed to extract mac address from NIC FRU dump")
            self.nic_set_err_msg(cmd_buf)
            return False
        mac_address_dump = mac_dump_match.group(0).upper()
        mac = libmfg_utils.mac_address_validate(mac_address_dump)
        if not mac:
            self.nic_set_err_msg("Invalid NIC MAC Address: {:s} detected\n".format(mac_address_dump))
            return False
        if expect_mac != "":
            if expect_mac.upper() != mac.upper():
                self.nic_set_err_msg("NIC MAC Address did not match: expect {:s}, read {:s}\n".format(expect_mac, mac))
                return False

        return True

    def nic_program_ocp_adapter_fru(self, date, sn, mac, pn):
        """
        sn  = scanned
        mac = FF:FF:FF:FF:FF
        pn  = 00-0000-00 00
        date= generated
        """

        if self._nic_type != NIC_Type.NAPLES25OCP:
            self.nic_set_err_msg("This function is only for OCP")
            return False

        # PROGRAM
        cmd = MFG_DIAG_CMDS().MTP_OCP_ADAP_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
            self.nic_set_err_msg("OCP Adapter FRU checksum failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        # VERIFY
        cmd_buf = self.nic_get_cmd_buf()
        match = re.findall(r"FRU Checkum and Type/Length Checks Passed", cmd_buf)
        if not match:
            self.nic_set_err_msg("OCP Adapter FRU checksum failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_copy_image(self, img_name, directory="/"):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot)
        cmd = "scp {:s} -r {:s} {:s}@{:s}:{:s}".format(libmfg_utils.get_ssh_option(), img_name, NIC_MGMT_USERNAME, ipaddr, directory)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:"], timeout=MTP_Const.SSH_PASSWORD_DELAY)
        if idx < 0:
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        signatures = ["No such file", "Exiting with failure"]
        self._nic_handle.sendline(NIC_MGMT_PASSWORD)
        idx = libmfg_utils.mfg_expect(self._nic_handle, signatures + [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg("NIC hung while copying")
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        if idx == 0 or idx == 1:
            self.nic_set_err_msg("Missing file {:s}".format(img_name))
            self.nic_set_cmd_buf(self._nic_handle.before + signatures[idx])
            return False

        mtp_cmd = "md5sum {:s}".format(img_name)
        self._nic_handle.sendline(mtp_cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, signatures + [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        match = re.search(r"([0-9a-fA-F]+) +.*", str(self._nic_handle.before))
        if match:
            local_md5sum = match.group(1)
        else:
            self.nic_set_err_msg("Execute command {:s} failed".format(mtp_cmd))
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        ssh_pipe_cmd = "ssh {:s} {:s}@{:s}".format(libmfg_utils.get_ssh_option(), NIC_MGMT_USERNAME, ipaddr)
        nic_cmd = "{} \" md5sum {:s} \"".format(ssh_pipe_cmd, directory+os.path.basename(img_name))
        self._nic_handle.sendline(nic_cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:"], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        self._nic_handle.sendline(NIC_MGMT_PASSWORD)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt, "No such file"], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        elif idx == 1:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        match = re.search(r"([0-9a-fA-F]+) +.*", str(self._nic_handle.before))
        if match:
            nic_md5sum = match.group(1)
        else:
            self.nic_set_err_msg("Execute command {:s} failed".format(nic_cmd))
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if local_md5sum != nic_md5sum:
            self.nic_set_err_msg("Checksums for {:s} don't match after copying to NIC".format(os.path.basename(img_name)))
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        ssh_pipe_cmd = "ssh {:s} {:s}@{:s}".format(libmfg_utils.get_ssh_option(), NIC_MGMT_USERNAME, ipaddr)
        nic_cmd = "{} \" sync;sleep 5;sync;sync \"".format(ssh_pipe_cmd)
        self._nic_handle.sendline(nic_cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:"], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        self._nic_handle.sendline(NIC_MGMT_PASSWORD)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt, "No such file"], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        elif idx == 1:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        return True
    def nic_copy_image_IBM(self, img_name, directory="/update"):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot)
        cmd = "scp {:s} -r {:s} {:s}@{:s}:{:s}".format(libmfg_utils.get_ssh_option(), img_name, NIC_MGMT_USERNAME, ipaddr, directory)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:"], timeout=MTP_Const.SSH_PASSWORD_DELAY)
        if idx < 0:
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        self._nic_handle.sendline(NIC_MGMT_PASSWORD)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        return True

    def nic_verify_fpga(self, cpld_img, partition=""):
        if not self.nic_copy_image(cpld_img):
            return False
        img_name = os.path.basename(cpld_img)
        if self._nic_type in ELBA_NIC_TYPE_LIST and self._nic_type in FPGA_TYPE_LIST:
            nic_cmd_list = list()
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FPGA_DUMP_FMT.format("", img_name, partition))
            if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.NIC_FPGA_PROG_DELAY):
                return False

            cmd_buf = self.nic_get_cmd_buf()
            match = re.findall(r"FPGA flash verified", cmd_buf)
            if not match:
                return False

        return True

    def nic_copy_file_from_nic(self, src_file, dst_file):
        if not src_file or not dst_file:
            self.nic_set_err_msg("No file specified to copy!")
            return False

        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot)
        cmd = "scp {:s} {:s}@{:s}:{:s} {:s}".format(libmfg_utils.get_ssh_option(), NIC_MGMT_USERNAME, ipaddr, src_file, dst_file)

        fail_signatures = ["No such file", "Exiting with failure"]
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, fail_signatures + ["assword:"], timeout=MTP_Const.SSH_PASSWORD_DELAY)
        if idx < 0:
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg("Couldn't get password prompt")
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        elif idx < len(fail_signatures):
            self.nic_set_err_msg("Missing file {:s}".format(src_file))
            self.nic_set_cmd_buf(self._nic_handle.before + fail_signatures[idx])
            return False

        self._nic_handle.sendline(NIC_MGMT_PASSWORD)
        idx = libmfg_utils.mfg_expect(self._nic_handle, fail_signatures + [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg("NIC hung while copying")
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        elif idx < len(fail_signatures):
            self.nic_set_err_msg("Missing file {:s}".format(src_file))
            self.nic_set_cmd_buf(self._nic_handle.before + fail_signatures[idx])
            return False

        self.mtp_exec_cmd("ls -l {:s}".format(os.path.dirname(dst_file)))

        return True

    @nic_console_test()
    def nic_console_set_sw_profile(self, profile):
        nic_cmd = MFG_DIAG_CMDS().NIC_SW_PROFILE_CMD_FMT.format(profile)
        self._nic_handle.sendline(nic_cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if MFG_DIAG_SIG.NIC_SW_PROFILE_FAIL_SIG in cmd_buf:
            self.nic_set_err_msg("Failed to apply profile")
            self.nic_set_cmd_buf(cmd_buf)
            return False

        self.nic_set_cmd_buf(self._nic_handle.before)
        return True

    def nic_sw_profile(self, profile):
        if not self.nic_copy_image("/home/diag/mfg_test_script/{:s}".format(profile)):
            return False
        if not self.nic_console_set_sw_profile(profile):
            return False
        return True

    def nic_verify_cpld_feature_row(self, cpld_fea_img, partition="fea"):
        """
          Verify Fea CPLD
        """

        cmd = MFG_DIAG_CMDS().MTP_MATERA_FPGAUTIL_CPLD_CMD_FMT.format(str(self._slot + 1), "verify", partition, cpld_fea_img)
        if not self.mtp_exec_cmd(cmd):
            return False
        if 'Verification passed'.lower() in self.nic_get_cmd_buf().lower():
            return True
        return False

    def nic_program_cpld(self, cpld_img, partition="cfg0", combo_partition2_img={}):
        """
        Program CPLD or Secure CPLD
        combo_partition2_img parameter only for Salina, there will no power cycle between combo partition program
        """

        if self._mtp_type == "MATERA":
            program_sequence =[]
            combo_partition2_img[partition] = cpld_img
            if "ufm1" in combo_partition2_img or "cfg0" in combo_partition2_img:
                if not ("ufm1" in combo_partition2_img  and "cfg0" in combo_partition2_img):
                    self.nic_set_err_msg("For Salina, ufm1 and cfg0 have to program in combo, and no power cycle in between")
                    return False
            # put the card into proto mode before program QSPI
            if not self.nic_power_off():
                return False
            if not self.nic_power_on(proto_mode='0'):
                return False
            # fpgautil cpld <slot#> generate/verify/erase/program <cfg0/cfg1/ufm1/fea> <filename>
            # program
            if "ufm1" in combo_partition2_img or "cfg0" in combo_partition2_img:
                program_sequence.append(("ufm1", combo_partition2_img["ufm1"]))
                del combo_partition2_img["ufm1"]
                program_sequence.append(("cfg0", combo_partition2_img["cfg0"]))
                del combo_partition2_img["cfg0"]

            for part, img in combo_partition2_img.items():
                program_sequence.append((part, img))

            for part, img in program_sequence:
                cmd = MFG_DIAG_CMDS().MTP_MATERA_FPGAUTIL_CPLD_CMD_FMT.format(str(self._slot + 1), "program", part, img)
                if not self.mtp_exec_cmd(cmd):
                    return False
                if 'Verification failed'.lower() in self.nic_get_cmd_buf().lower() or 'error' in self.nic_get_cmd_buf().lower():
                    return False
                # verify
                cmd = MFG_DIAG_CMDS().MTP_MATERA_FPGAUTIL_CPLD_CMD_FMT.format(str(self._slot + 1), "verify", part, img)
                if not self.mtp_exec_cmd(cmd):
                    return False
                if 'Verification failed'.lower() in self.nic_get_cmd_buf().lower() or 'error' in self.nic_get_cmd_buf().lower():
                    return False
        else:
            if not self.nic_copy_image(cpld_img):
                return False
            img_name = os.path.basename(cpld_img)
            # failsafe_name = os.path.basename(failsafe_img)

            nic_cmd_list = list()
            # Elba-based:
            if self._nic_type in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) and self._nic_type not in FPGA_TYPE_LIST:
                nic_cmd_list.append(MFG_DIAG_CMDS().NIC_CPLD_PROG_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, img_name, partition))
                timeout = MTP_Const.OS_CMD_DELAY
            elif self._nic_type in ELBA_NIC_TYPE_LIST and self._nic_type in FPGA_TYPE_LIST:
                nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FPGA_PROG_FMT.format("", img_name, partition))
                timeout = MTP_Const.NIC_FPGA_PROG_DELAY
            # Capri-based:
            else:
                nic_cmd_list.append(MFG_DIAG_CMDS().NIC_CPLD_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, img_name))
                timeout = MTP_Const.OS_CMD_DELAY

            if self._nic_type == NIC_Type.NAPLES25OCP:
                if not self.nic_exec_rst_cmd(nic_cmd_list[0], timeout=MTP_Const.OS_CMD_DELAY):
                    return False
            else:
                if not self.nic_exec_cmds(nic_cmd_list, timeout=timeout):
                    return False

        return True

    def nic_vulcano_reset_code(self):
        cmd = MFG_DIAG_CMDS().NIC_RESET_CODE_FMT
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            self.nic_set_err_msg("Zephyr command '{:s}' Failed".format(cmd))
            return False
        cmd_buf = self.nic_get_cmd_buf()

        cmd = MFG_DIAG_CMDS().NIC_HWINFO_RESET_CODE_FMT
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            self.nic_set_err_msg("Zephyr command '{:s}' Failed".format(cmd))
            return False

        return True

    def nic_vulcano_fpga_uart_stats_dump(self):
        cmd = MFG_DIAG_CMDS().PANAREA_MTP_FPGA_UART_STATS_FMT
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
            return False
        return True

    def set_nic_diagfw_boot(self):
        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_SET_DIAG_BOOT_FMT)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.NIC_FW_SET_DELAY):
            return False

        return True

    def nic_refresh_cpld(self, dontwait=False):

        if self._nic_type in VULCANO_NIC_TYPE_LIST:
            # program cpld partition
            cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_CPLD_REFRESH
            if not self.nic_exec_cmd_from_zephyr_console(cmd):
                self.nic_set_err_msg("Zephyr CPLD Command '{:s}' Failed".format(cmd))
                return False
            cmd_buf = self.nic_get_cmd_buf()
            sanitized_cmd_buf = self.zephyr_output_sanitize(cmd_buf)
            if "Done!".lower() not in sanitized_cmd_buf.lower():
                self.nic_set_err_msg("Zephyr CPLD refresh Failed")
                self.nic_set_err_msg(cmd_buf)
                return False
        else:
            # Capri-based:
            nic_cpld_ref_cmd = MFG_DIAG_CMDS().NIC_CPLD_REF_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
            # Elba-based:
            if self._nic_type in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) and self._nic_type not in FPGA_TYPE_LIST:
                nic_cpld_ref_cmd = MFG_DIAG_CMDS().NIC_CPLD_REF_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
            if not self.nic_exec_rst_cmd(nic_cpld_ref_cmd, timeout=MTP_Const.OS_CMD_DELAY, dontwait=dontwait):
                return False

        return True

    def nic_recover_console(self):
        # write 0x25 to reg 0x21
        read_data = [0]
        rc = self.nic_read_cpld_via_smbus(reg_addr=0x21, read_data=read_data)
        if not rc:
            self.nic_set_err_msg(" ERROR: nic_read_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        rc = self.nic_write_cpld_via_smbus(reg_addr=0x21, write_data=0x25)
        if not rc: 
            self.nic_set_err_msg(" ERROR: nic_write_cpld_via_smbus Failed") 
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        rc = self.nic_read_cpld_via_smbus(reg_addr=0x21, read_data=read_data)
        if not rc:
            self.nic_set_err_msg(" ERROR: nic_read_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if read_data[0] != 0x25:
            self.nic_set_err_msg(" ERROR: failed to set CPLD")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        # write 0xA0 to reg 0x22
        rc = self.nic_read_cpld_via_smbus(reg_addr=0x22, read_data=read_data)
        if not rc:
            self.nic_set_err_msg(" ERROR: nic_read_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        rc = self.nic_write_cpld_via_smbus(reg_addr=0x22, write_data=0xa0)
        if not rc: 
            self.nic_set_err_msg(" ERROR: nic_write_cpld_via_smbus Failed") 
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        rc = self.nic_read_cpld_via_smbus(reg_addr=0x22, read_data=read_data)
        if not rc:
            self.nic_set_err_msg(" ERROR: nic_read_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if read_data[0] != 0xA0:
            self.nic_set_err_msg(" ERROR: failed to set CPLD")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_check_cpld_partition(self, console=False):
        """
        Read reg 0x1 bit 2.
        0: PASS (booted from main/cfg0)
        1: FAIL (booted from gold/failsafe)
        """
        reg_addr = 1
        read_data = [0]
        if console:
            rc = self.nic_console_read_cpld(reg_addr, read_data)
        else:
            rc = self.nic_read_cpld(reg_addr, read_data)
        if not rc:
            self.nic_set_err_msg("Unable to read CPLD reg 0x1")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if (read_data[0] & 0x04) == 0:
            return True
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            self.nic_set_err_msg("Incorrect CPLD boot partition")
            return False            

    def nic_setting_partition(self):
        nic_cmd_list = list()
        nic_cmd_list.append("chmod +x /emmc_format.sh")
        if not self.nic_exec_cmds(nic_cmd_list, timeout=10):
            return False

        nic_cmd_list.append("dmesg")
        if not self.nic_exec_cmds(nic_cmd_list, timeout=60):
            return False

        nic_cmd = MFG_DIAG_CMDS().NIC_SETTING_PARTITION_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        nic_cmd = "dmesg | grep mmc"
        dmesg_cmd_buf = self.nic_get_info(nic_cmd).lower()
        if not cmd_buf or not dmesg_cmd_buf:
            return False
        if "error" in dmesg_cmd_buf or "fail" in dmesg_cmd_buf:
            return False
        if MFG_DIAG_SIG.NIC_PARTITION1_OK_SIG in cmd_buf:
            return True
        elif MFG_DIAG_SIG.NIC_PARTITION_OK_SIG in cmd_buf:
            return True
        else:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False                                

    def nic_emmc_hwreset_set(self):
        """
        # mmc hwreset enable /dev/mmcblk0
        # mmc extcsd read /dev/mmcblk0|grep -i reset
        H/W reset function [RST_N_FUNCTION]: 0x01
        """
        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_EMMC_HWRESET_SET_FMT)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=10):
            return False
        return True

    def nic_emmc_hwreset_verify(self):
        nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_HWRESET_CHECK_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            return False
        if MFG_DIAG_SIG.NIC_EMMC_HWRESET_PASS_SIG in cmd_buf:
            return True
        elif MFG_DIAG_SIG.NIC_EMMC_HWRESET_FAIL_SIG in cmd_buf:
            return False
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

    def nic_emmc_bkops_en(self):
        """
        -------------------------
        ENABLE BKOPS INSTRUCTIONS
        -------------------------
        Enable auto background mmc ops.  SEE warning below.
        # /data/nic_util/mmc.latest bkops_en auto /dev/mmcblk0

        Example:

        BEFORE:
        # mmc extcsd read /dev/mmcblk0|grep -i ops
        Background operations support [BKOPS_SUPPORT: 0x01]
        Background operations status [BKOPS_STATUS: 0x00]
        Enable background operations handshake [BKOPS_EN]: 0x00    <==== OFF

        AFTER:
        # mmc extcsd read /dev/mmcblk0|grep -i ops
        Background operations support [BKOPS_SUPPORT: 0x01]
        Background operations status [BKOPS_STATUS: 0x00]
        Enable background operations handshake [BKOPS_EN]: 0x02    <==== AUTO

        WARNING DO NOT SET MANUAL, this is a OTP setting and can't be undone

        # /data/nic_util/mmc.latest bkops --help
        Usage:
                mmc.latest bkops_en <auto|manual> <device>
                        Enable the eMMC BKOPS feature on <device>.
                        The auto (AUTO_EN) setting is only supported on eMMC 5.0 or newer.
                        Setting auto won't have any effect if manual is set.
                        NOTE!  Setting manual (MANUAL_EN) is one-time programmable (unreversible) change.
        """
        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_EMMC_BKOPS_EN_FMT)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=10):
            return False
        return True

    def nic_emmc_bkops_verify(self):
        nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_BKOPS_CHECK_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            return False
        if MFG_DIAG_SIG.NIC_EMMC_BKOPS_PASS_SIG in cmd_buf:
            return True
        elif MFG_DIAG_SIG.NIC_EMMC_BKOPS_FAIL_SIG in cmd_buf:
            return False
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

    def nic_fwupdate_init_emmc(self, mount=True):

        nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_INIT_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            return False
        if (MFG_DIAG_SIG.NIC_FWUPDATE_INIT_EMMC_PASS_SIG.lower() not in cmd_buf.lower()) or ("Done".lower() not in cmd_buf.lower()):
            return False

        if mount:
            nic_cmd_list = list()
            nic_cmd = MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT
            nic_cmd_list.append(nic_cmd)
            if not self.nic_exec_cmds(nic_cmd_list):
                self.nic_set_err_msg("Command {:s} failed".format(nic_cmd))
                return False

        return True

    def nic_read_emmc_id(self):
        nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_READ_ID_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            self.nic_set_err_msg("Command {:s} failed".format(nic_cmd))
            return False
        id_match = re.search("0x([0-9A-Za-z]+)", cmd_buf)
        if not id_match:
            self.nic_set_err_msg("Failed to parse emmc manufacturer id")
            return False
        self._emmc_mfr_id = id_match.group(1)

        # also find mfr id dumped by kernel
        nic_cmd_list = list()
        nic_cmd = "dmesg | grep mmc"
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list):
            self.nic_set_err_msg("Command {:s} failed".format(nic_cmd))
            return False

        return True

    def nic_dump_esec_qspi(self, mode):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS().NIC_ESEC_PROG_QSPI_DUMP_FMT.format(self._slot+1, mode)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_dump_cpld(self, partition, file_path="/home/diag/cplddump"):
        cmd = MFG_DIAG_CMDS().NIC_CPLD_DUMP_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, file_path, partition)
        nic_cmd_list = list()
        nic_cmd_list.append(cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        return True

    def nic_compare_cpld_file(self, cpld_image, dump_cpld_image, partition):
        nic_cmd = MFG_DIAG_CMDS().NIC_CPLD_DUMP_COMPARE_FMT.format(os.path.basename(cpld_image), os.path.basename(dump_cpld_image))
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        # check fail
        buf_line = cmd_buf.split('\n')
        if len(buf_line) > 3:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False
        else:
            if "EOF" in cmd_buf or "cmp:" in cmd_buf:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

        return True

    def nic_verify_sec_cpld(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if self._nic_type not in SALINA_NIC_TYPE_LIST:
            cmd = MFG_DIAG_CMDS().NIC_ESEC_CPLD_CHECK_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

            # save result buffer
            cmd_buf = self.nic_get_cmd_buf()

            cmd = MFG_DIAG_CMDS().NIC_ESEC_ERR_CHECK_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

            # check signature
            if MFG_DIAG_SIG.NIC_ESEC_CPLD_VERIFY_SIG not in cmd_buf:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False
        else:
            cmd = MFG_DIAG_CMDS().NIC_ESEC_SALINA_CPLD_CHECK_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

            # save result buffer
            cmd_buf = self.nic_get_cmd_buf()

            # check signature
            if MFG_DIAG_SIG.NIC_SALINA_ESEC_CPLD_VERIFY_SIG not in cmd_buf:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

        return True

    def nic_salina_clear_j2c(self):
        cmd = MFG_DIAG_CMDS().MATERA_MTP_CLEAR_J2C_IF_LOCK.format(str(self._slot+1))
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_esecure_hw_unlock(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS().NIC_ESEC_HW_UNLOCK_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if MFG_DIAG_SIG.NIC_ESEC_HW_UNLOCK_OK_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_program_sec_key_dump(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS().NIC_ESEC_PROG_DUMP_FMT.format(self._sn, self._slot+1, self._nic_type)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True


    def nic_program_sec_key_pre(self):
        if self._nic_type in SALINA_NIC_TYPE_LIST:
            cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_SCRIPT_PATH)
            if not self.mtp_exec_cmd(cmd):
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

            softrom_rev = MFG_AI_NIC_SOFT_ROM_VERSION if self._nic_type in SALINA_AI_NIC_TYPE_LIST else MFG_DPU_NIC_SOFT_ROM_VERSION
            if softrom_rev not in GETSOFTROM_FILE_NAME or "qspi_softrom" not in GETSOFTROM_FILE_NAME[softrom_rev]:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

            cmd = MFG_DIAG_CMDS().SALINA_NIC_ESEC_PROG_PRE_FMT.format(GETSOFTROM_FILE_NAME[softrom_rev]["qspi_softrom"], self._slot+1)
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

            # check signature
            if MFG_DIAG_SIG.NIC_ESEC_PROG_PRE_SIG not in self.nic_get_cmd_buf():
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False
        else:
            cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
            if not self.mtp_exec_cmd(cmd):
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

            cmd = MFG_DIAG_CMDS().NIC_ESEC_PROG_PRE_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

            # check signature
            if MFG_DIAG_SIG.NIC_ESEC_PROG_PRE_SIG not in self.nic_get_cmd_buf():
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

        return True


    def nic_program_sec_key(self, mtpid):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST or self._nic_type in SALINA_NIC_TYPE_LIST:
            cmd = MFG_DIAG_CMDS().NIC_ESEC_PROG_ELBA_FMT.format(self._slot+1,
                                                         self._sn,
                                                         self._pn,
                                                         self._mac.replace('-',':'),
                                                         self._nic_type,
                                                         mtpid)
        else:
            # program secure key with (slot, sn, pn, mac, type, mtpid)
            cmd = MFG_DIAG_CMDS().NIC_ESEC_PROG_FMT.format(self._slot+1,
                                                         self._sn,
                                                         self._pn,
                                                         self._mac.replace('-',':'),
                                                         self._nic_type,
                                                         mtpid)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_ESEC_PROG_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True


    def nic_program_sec_key_post(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS().NIC_ESEC_PROG_POST_FMT
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_program_dice_sec_key(self):
        if self._nic_type not in SALINA_NIC_TYPE_LIST:
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS().NIC_ESEC_PROG_DICE_SALINA_FMT.format(self._slot+1, self._sn)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_ESEC_DICE_PROG_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_program_dice_img_sec_key(self):
        if self._nic_type not in SALINA_NIC_TYPE_LIST:
            return False

        softrom_rev = MFG_AI_NIC_SOFT_ROM_VERSION if self._nic_type in SALINA_AI_NIC_TYPE_LIST else MFG_DPU_NIC_SOFT_ROM_VERSION
        if softrom_rev not in GETSOFTROM_FILE_NAME or "qspi_pentrust" not in GETSOFTROM_FILE_NAME[softrom_rev]:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_SCRIPT_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS().NIC_ESEC_PENTRUST_SALINA_FMT.format(GETSOFTROM_FILE_NAME[softrom_rev]["qspi_pentrust"], self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_ESEC_PENTRUST_FAIL_SIG in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if MFG_DIAG_SIG.NIC_ESEC_PENTRUST_PASS_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_check_uboot_sec_key(self):
        if self._nic_type not in SALINA_NIC_TYPE_LIST:
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS().NIC_ESEC_SALINA_CPLD_CHECK_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_SALINA_ESEC_CPLD_VERIFY_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        # check signature
        if self._nic_type in SALINA_DPU_NIC_TYPE_LIST:
            pass_sign = "SoftROM version: {:s}".format(MFG_DPU_NIC_SOFT_ROM_VERSION)
        if self._nic_type in SALINA_AI_NIC_TYPE_LIST:
            pass_sign = "SoftROM version: {:s}".format(MFG_AI_NIC_SOFT_ROM_VERSION)

        if pass_sign not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_hmac_fuse_prog(self):
        if self._nic_type not in SALINA_NIC_TYPE_LIST:
            return False

        softrom_rev = MFG_AI_NIC_SOFT_ROM_VERSION if self._nic_type in SALINA_AI_NIC_TYPE_LIST else MFG_DPU_NIC_SOFT_ROM_VERSION
        if softrom_rev not in GETSOFTROM_FILE_NAME or "hmac_file" not in GETSOFTROM_FILE_NAME[softrom_rev]:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS().NIC_ESEC_SALINA_HMAC_FUSE_PROG_FMT.format(self._slot+1, GETSOFTROM_FILE_NAME[softrom_rev]["hmac_file"])
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return False

        # check fail signature
        if MFG_DIAG_SIG.NIC_EFUSE_PROG_FAIL_SIG in self.nic_get_cmd_buf() or MFG_DIAG_SIG.NIC_ESEC_J2C_FAIL_SIG in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        # check pass signature
        if MFG_DIAG_SIG.NIC_EFUSE_PROG_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_hmac_program_status_check(self, expect_status=MFG_DIAG_SIG.NIC_HMAC_NOT_PROG_SIG, stage=FF_Stage.FF_DL):
        """
        Run HMAC program status check command, ./esec_ctrl.py -hmac_fuse_prog -slot {:d} -hmac_file check_only.
        Compare with expected programming status,
        if expect "HMAC HAS NOT BEEN PROGRAMMED", then when this string show up in command buffer, return True otherwise return False
        if expect "NIC_HMAC_BEEN_PROG_SIG", then when this string show up in command buffer, return True otherwise return False
        """
        if self._nic_type not in SALINA_NIC_TYPE_LIST:
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False
        cmd = MFG_DIAG_CMDS().NIC_ESEC_SALINA_HMAC_FUSE_CHK_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return False

        # check fail signature
        if MFG_DIAG_SIG.NIC_EFUSE_PROG_FAIL_SIG in self.nic_get_cmd_buf() or MFG_DIAG_SIG.NIC_ESEC_J2C_FAIL_SIG in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if MFG_DIAG_SIG.NIC_EFUSE_PROG_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        # check expect hmac programming status
        if expect_status not in (MFG_DIAG_SIG.NIC_HMAC_NOT_PROG_SIG, MFG_DIAG_SIG.NIC_HMAC_BEEN_PROG_SIG):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg("PASSED IN INVALID HMAC PROGRMMED STATUS FOR COMPARE")
            return False

        if expect_status not in self.nic_get_cmd_buf():
            if stage != FF_Stage.FF_SWI:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_hmac_program_category(self, stage=FF_Stage.FF_DL):
        """
        Run HMAC program status check command, ./esec_ctrl.py -hmac_fuse_prog -slot {:d} -hmac_file check_only.
        Compare with expected programming status,
        if expect "HMAC HAS NOT BEEN PROGRAMMED", then when this string show up in command buffer, return True otherwise return False
        if expect "NIC_HMAC_BEEN_PROG_SIG", then when this string show up in command buffer, return True otherwise return False
        """
        if self._nic_type not in SALINA_NIC_TYPE_LIST:
            return -1

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return -1

        cmd = MFG_DIAG_CMDS().NIC_ESEC_SALINA_HMAC_FUSE_CHK_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return -1

        # check fail signature
        if MFG_DIAG_SIG.NIC_EFUSE_PROG_FAIL_SIG in self.nic_get_cmd_buf() or MFG_DIAG_SIG.NIC_ESEC_J2C_FAIL_SIG in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return -1

        if MFG_DIAG_SIG.NIC_EFUSE_PROG_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return -1

        # check expect hmac not programmed status
        if MFG_DIAG_SIG.NIC_HMAC_NOT_PROG_SIG in self.nic_get_cmd_buf():
            return 0

        # check expect hmac programmed status
        if MFG_DIAG_SIG.NIC_HMAC_BEEN_PROG_SIG in self.nic_get_cmd_buf():
            return 1

        return -1

    def nic_val_uds_cert_category(self, stage=FF_Stage.FF_DL):
        if self._nic_type not in SALINA_NIC_TYPE_LIST:
            return -1

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return -1

        cmd = MFG_DIAG_CMDS.NIC_ESEC_SALINA_VAL_UDS_CERT_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return -1

        # check signature
        if MFG_DIAG_SIG.NIC_ESEC_DICE_CERT_SIG in self.nic_get_cmd_buf():
            return 0
        else:
            return 1

        return -1

    def nic_check_uds_cert(self):
        if self._nic_type not in SALINA_NIC_TYPE_LIST:
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS().NIC_ESEC_SALINA_UDS_CERT_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_ESEC_DICE_CERT_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_val_uds_cert(self):
        if self._nic_type not in SALINA_NIC_TYPE_LIST:
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS().NIC_ESEC_SALINA_VAL_UDS_CERT_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_ESEC_DICE_CERT_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_program_efuse(self):
        if self._nic_type in SALINA_NIC_TYPE_LIST and not self.nic_salina_clear_j2c():
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if self._nic_type not in ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST + SALINA_NIC_TYPE_LIST:
            return False

        cmd = MFG_DIAG_CMDS().NIC_EFUSE_PROG_ELBA_FMT.format(self._slot+1,
                                                     self._sn,
                                                     self._pn,
                                                     self._mac.replace('-',':'),
                                                     self._nic_type)
        # if not GLB_CFG_MFG_TEST_MODE:
        #     cmd = MFG_DIAG_CMDS().NIC_EFUSE_PROG_ELBA_MODEL_FMT.format(self._slot+1,
        #                                                              self._sn,
        #                                                              self._pn,
        #                                                              self._mac.replace('-',':'),
        #                                                              self._nic_type)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_EFUSE_PROG_DELAY):
            return False

        # check fail signature
        if MFG_DIAG_SIG.NIC_EFUSE_PROG_FAIL_SIG in self.nic_get_cmd_buf() or MFG_DIAG_SIG.NIC_ESEC_J2C_FAIL_SIG in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False
        # check pass signature
        if MFG_DIAG_SIG.NIC_EFUSE_PROG_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def salina_nic_program_qspi(self, image_path=None, img_type="standalone"):
        '''
        This funtion is for Matera capability NIC cards to program NIC QSPI Flash
        image_path is the path of program qspi bash script in with file name or path only
        '''

        # fpgautil flash <slot#> <qspi#> writefile/verifyfile <addr> <filename>
        #### PROGRAM SLOT 1, QSPI 1, uboot0 ###
        # fpgautil flash 1 1 writefile  0x00100000 uboot0.img
        # ### PROGRAM SLOT 1, QSPI 1, uboot-a ###
        # fpgautil flash 1 1 writefile  0x06800000 uboota.img
        # ### PROGRAM SLOT 1, QSPI 1, zephyr llc image ###
        # fpgautil flash 1 1 writefile  0x04A00000 zerphy_llc.img

        if not image_path:
            return False

        prog_cmd = ""
        if os.path.isfile(image_path):
            prog_cmd = os.path.basename(image_path)
            image_path = os.path.dirname(image_path)

        # put the card into proto mode before program QSPI
        if not self.nic_power_off():
            return False
        if not self.nic_power_on(proto_mode='0'):
            return False

        cmd = "cd {:s}".format(image_path)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        # call qspi_prog.sh to program qspi flash
        if not prog_cmd:
            if self._nic_type in SALINA_AI_NIC_TYPE_LIST:
                if img_type == "secure":
                    cmd = "chmod +x {:s}".format("./qspi_prog_secure.v2.sh")
                elif img_type == "nonsecure":
                    cmd = "chmod +x {:s}".format("./qspi_prog.v2.sh")
                else:
                    cmd = "chmod +x {:s}".format("./qspi_prog.sh")
            else:
                cmd = "chmod +x {:s}".format("./qspi_prog.sh")
            if not self.mtp_exec_cmd(cmd):
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False

            if self._nic_type in SALINA_AI_NIC_QSPI_V3_TYPE_LIST:
                if img_type == "secure":
                    cmd = MFG_DIAG_CMDS().MTP_MATERA_POLLARA_QSPI_PROG_SECURE_SH_CMD_FMT.format(str(self._slot + 1))
                elif img_type == "nonsecure":
                    cmd = MFG_DIAG_CMDS().MTP_MATERA_POLLARA_QSPI_PROG_SH_CMD_FMT.format(str(self._slot + 1))
                else:
                    cmd = MFG_DIAG_CMDS().MTP_MATERA_QSPI_PROG_SH_CMD_FMT.format(str(self._slot + 1))
            elif self._nic_type in SALINA_AI_NIC_QSPI_V2_TYPE_LIST:
                if img_type == "secure":
                    cmd = MFG_DIAG_CMDS().MTP_MATERA_POLLARA_QSPI_PROG_SECURE_V2_SH_CMD_FMT.format(str(self._slot + 1))
                elif img_type == "nonsecure":
                    cmd = MFG_DIAG_CMDS().MTP_MATERA_POLLARA_QSPI_PROG_V2_SH_CMD_FMT.format(str(self._slot + 1))
                else:
                    cmd = MFG_DIAG_CMDS().MTP_MATERA_QSPI_PROG_SH_CMD_FMT.format(str(self._slot + 1))
            else:
                cmd = MFG_DIAG_CMDS().MTP_MATERA_QSPI_PROG_SH_CMD_FMT.format(str(self._slot + 1))
        else:
            cmd = "chmod +x {:s}".format(prog_cmd)
            if not self.mtp_exec_cmd(cmd):
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                return False
            cmd = "./" + prog_cmd + " " + str(self._slot + 1)

        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            return False
        if 'FAILED' in self.nic_get_cmd_buf():
            return False

        if 'No such file' in self.nic_get_cmd_buf():
            return False

        self.nic_boot_info_reset()

        return True

    def nic_program_qspi(self, qspi_img):
        if not self.nic_copy_image(qspi_img):
            return False
        img_name = os.path.basename(qspi_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS().NIC_QSPI_PROG_FMT.format(img_name)
        qspi_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, fail_sig=qspi_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        cmd_buf = self._nic_handle.before
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False

        self.nic_boot_info_reset()

        return True

    def salina_nic_erase_qspi(self):
        cmd = MFG_DIAG_CMDS().NIC_ERASE_QSPI_FMT.format(str(self._slot + 1))
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ERASE_QSPI_IMG_DELAY):
            return False

        cmd_buf = self.nic_get_cmd_buf()
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        cmd_buf = cmd_buf
        if "Erasing QSPI of slot" in cmd_buf:
            self.nic_set_err_msg(cmd_buf)
            return False
        return True

    def vul_nic_erase_qspi(self):
        qspi_erase_cmd = "cd /home/diag/diag/scripts/asic/; tclsh vul_qspi_erase.tcl -slot {:s}".format(str(self._slot + 1))
        if not self.mtp_exec_cmd(qspi_erase_cmd, timeout=MTP_Const.NIC_ERASE_QSPI_IMG_DELAY):
            return False
        if "QSPI ERASE PASSED" not in self.nic_get_cmd_buf():
            return False
        return True

    def salina_nic_dump_boot(self):
        cmd = MFG_DIAG_CMDS().NIC_DUMP_BOOT_FMT.format(str(self._slot + 1), MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR, str(self._sn))
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ERASE_QSPI_IMG_DELAY):
            return False

        cmd_buf = self.nic_get_cmd_buf()
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False

        return True

    def salina_nic_erase_boot0(self, image_path=""):
        cmd = "cd {:s}".format(image_path)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_PROG_BOOT0_IMG_DELAY):
            return False

        cmd = MFG_DIAG_CMDS().SALINA_NIC_ERASE_BOOT0_FMT.format(str(self._slot + 1))
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ERASE_BOOT0_IMG_DELAY):
            return False

        if MFG_DIAG_SIG.SALINA_NIC_ERASE_BOOT0_OK_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def salina_nic_program_boot0(self, image_path=""):
        cmd = "cd {:s}".format(image_path)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_PROG_BOOT0_IMG_DELAY):
            return False

        cmd = MFG_DIAG_CMDS().SALINA_NIC_PROGRAM_BOOT0_FMT.format(str(self._slot + 1))
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_PROG_BOOT0_IMG_DELAY):
            return False

        if MFG_DIAG_SIG.SALINA_NIC_PROG_BOOT0_OK_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_copy_cpld_img(self, cpld_img):
        if not self.nic_copy_image(cpld_img):
            return False

        return True

    def nic_copy_gold(self, gold_img):
        if not self.nic_copy_image(gold_img):
            return False
            
        return True

    def nic_copy_cert(self, cert_img, directory="/data/"):
        if not self.nic_copy_image(cert_img, directory):
            return False
            
        return True

    def nic_program_gold(self, gold_img):

        img_name = os.path.basename(gold_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS().NIC_GOLDFW_PROG_FMT.format(img_name, img_name)
        if self._nic_type == NIC_Type.NAPLES100:
            nic_cmd = MFG_DIAG_CMDS().NIC_GOLDFW_PROG_FMT_NAPLES100.format(img_name)
        gold_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, fail_sig=gold_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        self.nic_boot_info_reset()

        return True

    def nic_program_uboot(self, boot_img, installer, uboot_pat="boot0", ubootg_img=""):
        if not self.nic_copy_image(installer):
            return False
        if not self.nic_copy_image(boot_img):
            return False
        installer_path = os.path.basename(installer)
        img_name = os.path.basename(boot_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS().NIC_UBOOT_PROG_FMT.format(installer_path, uboot_pat, img_name)
        qspi_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)

        if not self.nic_exec_cmds(nic_cmd_list, fail_sig=qspi_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False


        if ubootg_img:
            if not self.nic_copy_image(ubootg_img):
                return False
            img_name = os.path.basename(ubootg_img)

            nic_cmd_list = list()
            nic_cmd = MFG_DIAG_CMDS().NIC_UBOOT_PROG_FMT.format(installer_path, "golduboot", img_name)
            qspi_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
            nic_cmd_list.append(nic_cmd)

            if not self.nic_exec_cmds(nic_cmd_list, fail_sig=qspi_fail_sig):
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

        self.nic_boot_info_reset()

        return True

    def nic_erase_main_fw_partition(self):
        # check mainfwa & mainfwb block info existing any content
        cmd = MFG_DIAG_CMDS().NIC_IMG_DISP1_FMT
        fw_info_buf = self.nic_get_info(cmd)
        if not fw_info_buf:
            self.nic_set_err_msg("Unable to execute list fw info")
            return False
        try:
            fw_info = json.loads('\n'.join(fw_info_buf.strip().split('\n')[1:]))
            if ("mainfwa" in fw_info.keys() and fw_info["mainfwa"]) or ("mainfwb" in fw_info.keys() and fw_info["mainfwb"]):
                pass
            else:
                return True
        except:
            self.nic_set_err_msg("Get complete fw list failed")
            return False

        # get qspi partition
        cmd = MFG_DIAG_CMDS().NIC_GET_QSPI_PARTITION_FMT
        qspi_part_buf = self.nic_get_info(cmd)
        if not qspi_part_buf:
            self.nic_set_err_msg("Unable to get qspi partition")
            return False

        nic_erase_qspi_cmd_list = []
        matchs = re.findall(r"mtd(\d+):.*\s\"(mainfwa|mainfwb|uboota|ubootb)\"", qspi_part_buf)
        for match in matchs:
            fw_num = int(match[0])
            fw_name = match[1]
            nic_erase_qspi_cmd_list.append(MFG_DIAG_CMDS().NIC_ERASE_QSPI_PARTITION_FMT.format(fw_num))

        # erase qspi partition
        for erase_cmd in nic_erase_qspi_cmd_list:
            erase_qspi_cmd_buf = self.nic_get_info(erase_cmd, 300)
            if not erase_qspi_cmd_buf:
                self.nic_set_err_msg("Unable to execute erase qspi partition")
                return False
            match = re.search(r"100 % complete", erase_qspi_cmd_buf)
            if not match:
                self.nic_set_err_msg("After execute Command {:s}, unable to locate pass key word failed".format(erase_cmd))
                return False

        # get emmc partition
        cmd = MFG_DIAG_CMDS().NIC_GET_EMMC_PARTITION_FMT
        emmc_part_buf = self.nic_get_info(cmd)
        if not emmc_part_buf:
            self.nic_set_err_msg("Unable to get emmc partition")
            return False

        nic_erase_emmc_cmd_list = []
        matchs = re.findall(r"(\d+)\s.+\s(System Image A|System Image B)", emmc_part_buf)
        for match in matchs:
            fw_num = int(match[0])
            fw_name = match[1]
            nic_erase_emmc_cmd_list.append(MFG_DIAG_CMDS().NIC_ERASE_EMMC_PARTITION_FMT.format(fw_num))

        # erase emmc partition
        for erase_cmd in nic_erase_emmc_cmd_list:
            erase_emmc_cmd_buf = self.nic_get_info(erase_cmd, 10)
            if not erase_emmc_cmd_buf:
                self.nic_set_err_msg("Unable to execute erase emmc partition")
                return False
            match = re.search(r"16\+0 records in",erase_emmc_cmd_buf)
            if not match:
                self.nic_set_err_msg("After execute Command {:s}, unable to locate pass key word \"{:s}\" failed".format(erase_cmd, "16+0 records in"))
                return False
            match = re.search(r"16\+0 records out",erase_emmc_cmd_buf)
            if not match:
                self.nic_set_err_msg("After execute Command {:s}, unable to locate pass key word \"{:s}\" failed".format(erase_cmd, "16+0 records out"))
                return False

        # verify mainfwa & mainfwb block info contant clear
        cmd = MFG_DIAG_CMDS().NIC_IMG_DISP1_FMT
        fw_info_buf = self.nic_get_info(cmd)
        if not fw_info_buf:
            self.nic_set_err_msg("Unable to execute list fw info")
            return False
        try:
            fw_info = json.loads('\n'.join(fw_info_buf.strip().split('\n')[1:]))
            if ("mainfwa" in fw_info.keys() and fw_info["mainfwa"]) or ("mainfwb" in fw_info.keys() and fw_info["mainfwb"]):
                self.nic_set_err_msg("Verify mainfw partition clear failed")
                return False
        except:
            self.nic_set_err_msg("Unable to get complete fw list to verify")
            return False

        return True

    def nic_init_emmc(self, init=False, emmc_check=False):
        if init:
            if not self.nic_read_emmc_id():
                return False

        nic_cmd_list = list()
        if emmc_check and self._nic_type in PSLC_MODE_TYPE_LIST:
            nic_cmd = MFG_DIAG_CMDS().NIC_CHECK_EMMC_FMT
            emmc_check_sig = MFG_DIAG_SIG.NIC_EMMC_CHECK_OK_SIG
            emmc_check_buf = self.nic_get_info(nic_cmd)
            if emmc_check_buf:
                if emmc_check_sig in emmc_check_buf:
                    pass
                else:
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    self.nic_set_err_msg("pSLC mode setting not found")
                    self.nic_set_cmd_buf(emmc_check_buf)
                    return False
            else:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False  

        if init:
            nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_INIT_FMT
            nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_PARTITION_DISP_FMT)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        # check if mount is ok
        nic_cmd = MFG_DIAG_CMDS().NIC_MOUNT_DISP_FMT
        mount_sig = MFG_DIAG_SIG.NIC_MOUNT_OK_SIG
        mount_buf = self.nic_get_info(nic_cmd)
        if mount_buf:
            if mount_sig in mount_buf:
                pass
            else:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                self.nic_set_err_msg("eMMC not mounted")
                self.nic_set_cmd_buf(mount_buf)
                return False
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        nic_cmd = MFG_DIAG_CMDS().NIC_IMG_DISP1_FMT
        nic_cmd_buf = self.nic_get_info(nic_cmd)
        if not nic_cmd_buf:
            return False

        try:
            fw_info = json.loads(nic_cmd_buf.split("/")[1].strip())
            if fw_info:
                self._fw_json = fw_info
        except:
            pass

        return True
            
    def nic_emmc_set_perf_mode(self):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_PERF_MODE
        nic_cmd_list.append(nic_cmd)
        nic_cmd_list.append("sync")
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        # check if successful
        nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_PERF_MODE_CHECK
        nic_cmd_list.append(nic_cmd)
        perf_sig = MFG_DIAG_SIG.NIC_EMMC_PERF_MODE_OK_SIG
        perf_buf = self.nic_get_info(nic_cmd)
        if perf_buf:
            if perf_sig in perf_buf:
                return True
            else:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                self.nic_set_cmd_buf(perf_buf)
                return False
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

    def nic_emmc_check_perf_mode(self):
        nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_PERF_MODE_CHECK
        perf_sig = MFG_DIAG_SIG.NIC_EMMC_PERF_MODE_OK_SIG
        perf_buf = self.nic_get_info(nic_cmd)
        if perf_buf:
            if perf_sig in perf_buf:
                return True
            else:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                self.nic_set_cmd_buf(perf_buf)
                return False
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

    def nic_program_emmc(self, emmc_img):
        if not self.nic_copy_image(emmc_img, directory=MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH):
            return False
        img_name = os.path.basename(emmc_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_INIT_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_PROG_FMT.format(img_name, img_name)
        # if self._nic_type == NIC_Type.NAPLES100:
        #     nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_PROG_FMT_NAPLES100.format(img_name) # 90-0001-0001 does not have fwupdate binary packaged
        nic_cmd_list.append(nic_cmd)
        if self._nic_type not in FPGA_TYPE_LIST:
            nic_cmd = MFG_DIAG_CMDS().NIC_EMMC_B_PROG_FMT.format(img_name, img_name)
            nic_cmd_list.append(nic_cmd)
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd = MFG_DIAG_CMDS().NIC_BOOT0_PROG_FMT.format(img_name, img_name)
            nic_cmd_list.append(nic_cmd)
        emmc_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY, fail_sig=emmc_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        self.nic_boot_info_reset()

        return True

    def salina_nic_call_sysypdate_prog_fw(self, fw_img):
        """
        for salina DPU, call sysupdate.sh -p <img> to update mainfw or goldfw
        make sure image file in emmc /data before update
        """

        img_name = os.path.basename(fw_img)

        cmd = MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT
        if not self.nic_exec_cmd_from_console(cmd, cmd_prompt=" root# "):
            self.nic_set_err_msg("Command '{:s}' Failed".format(cmd))
            return False

        cmd = MFG_DIAG_CMDS().NIC_EMMC_PROG_SALINA_FMT.format(img_name)
        if not self.nic_exec_cmd_from_console(cmd, cmd_prompt=" root# "):
            self.nic_set_err_msg("Command '{:s}' Failed".format(cmd))
            return False
        update_fw_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        cmd_buf = self.nic_get_cmd_buf()
        if update_fw_fail_sig in cmd_buf:
            self.nic_set_err_msg("Salina sysupdate.sh program image failed")
            self.nic_set_err_msg(cmd_buf)
            return False
        update_fw_pass_sig = MFG_DIAG_SIG.NIC_SYSUPDATE_PASS_SIG
        if cmd_buf.count(update_fw_pass_sig) != 2:
            self.nic_set_err_msg("Salina sysupdate.sh failed to see SUCCESS twice")
            self.nic_set_err_msg(cmd_buf)
            return False

        self.nic_boot_info_reset()

        return True


    def nic_setup_diag_img(self, nic_diag_image, nic_asic_image="", emmc_utils=False):
        # if emmc_utils: arm64 diag image on NIC will be updated
        if emmc_utils:
            nic_diag_list = ["diag", "nic_arm", "nic_util", "start_diag.arm64.sh", "nic.tar.gz"]

            # clear out old extracted lib
            nic_cmd_list = list()
            for util in nic_diag_list:
                nic_cmd_list.append("rm -r /data/{:s}".format(util))
            if not self.nic_exec_cmds(nic_cmd_list):
                return False

            # copy image_arm64 from MTP and untar it into /data/
            if not self.nic_copy_image(nic_diag_image, MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH):
                return False

            nic_cmd_list = list()
            nic_cmd = MFG_DIAG_CMDS().NIC_UNTAR_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+os.path.basename(nic_diag_image), MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH)
            nic_cmd_list.append(nic_cmd)
            if not self.nic_exec_cmds(nic_cmd_list, timeout=300):
                return False

            # copy unpackaged asic lib to /data
            if nic_asic_image:
                if not self.nic_copy_image(nic_asic_image, MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH):
                    return False

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH)
        nic_cmd_list.append(nic_cmd)
        nic_cmd = "sync"
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS().MFG_DIR_LINK_FMT.format("/data/diag/", MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH+"/diag")
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS().MFG_DIR_LINK_FMT.format("/data/start_diag.arm64.sh", MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH+"/start_diag.arm64.sh")
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        return True

    def nic_save_logfile(self, logfile_list):
        if not self._sn:
            self.nic_set_err_msg("No SN saved for this NIC")
            return False

        ret = True

        for logfile in logfile_list:
            if "*" in logfile:
                # copy to one directory and then perform renames
                temp_dir = "{:s}/{:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR, self._sn)
                self.mtp_exec_cmd("mkdir {:s}".format(temp_dir))
                dst_logfile = temp_dir
            else:
                log = os.path.basename(logfile)
                dst_logfile = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR + self._sn + "_" + log

            if not self.nic_copy_file_from_nic(logfile, dst_logfile):
                ret &= False

            if "*" in logfile:
                # move out of temp dir
                temp_dir = "{:s}/{:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR, self._sn)
                self.mtp_exec_cmd("for file in $(ls {:s}); do mv {:s}/$file {:s}/{:s}_$file ; done".format(temp_dir, temp_dir, MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR, self._sn))
                self.mtp_exec_cmd("rmdir {:s}".format(temp_dir))

        return ret


    def nic_save_diag_logfile(self, aapl):
        if aapl:
            dst_log_dir = MTP_DIAG_Logfile.ONBOARD_NIC_LOG_DIR + "AAPL-NIC-{:02d}/".format(self._slot+1)
        else:
            dst_log_dir = MTP_DIAG_Logfile.ONBOARD_NIC_LOG_DIR + "NIC-{:02d}/".format(self._slot+1)
        cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(dst_log_dir)
        if not self.mtp_exec_cmd(cmd):
            return False

        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot)
        logfile = MTP_DIAG_Logfile.NIC_ONBOARD_DIAG_LOG_FILES
        cmd = "scp {:s} {:s}@{:s}:{:s} {:s}".format(libmfg_utils.get_ssh_option(), NIC_MGMT_USERNAME, ipaddr, logfile, dst_log_dir)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:"], timeout=MTP_Const.SSH_PASSWORD_DELAY)
        if idx < 0:
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        self._nic_handle.sendline(NIC_MGMT_PASSWORD)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS().NIC_DIAG_FINI_FMT
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        return True


    def nic_diag_clean(self):
  
        cmd = MFG_DIAG_CMDS().NIC_SYS_CLEAN_FMT.format(MTP_DIAG_Path.ONBOARD_MTP_MTP_DIAG_PATH)
        mtp_cmd_buf = self.mtp_get_info(cmd, timeout=MTP_Const.OS_CMD_DELAY)
        if not mtp_cmd_buf:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if self._nic_type not in ELBA_NIC_TYPE_LIST and self._nic_type not in GIGLIO_NIC_TYPE_LIST:
            # issue with capri diag image...
            return True

        # wait for completion sig to avoid interfering with other tests
        if "sys_clean done" in mtp_cmd_buf:
            return True
        else:
            return False

    def nic_kill_hal(self):
        hal_stopped, sysmgr_stopped, sysmond_stopped = False, False, False

        if self._nic_type != NIC_Type.NAPLES25OCP:
            sysmgr_stopped = True #no need to kill for other than OCP..for now

        if self._nic_type not in ELBA_NIC_TYPE_LIST and self._nic_type not in GIGLIO_NIC_TYPE_LIST:
            sysmond_stopped = True

        for x in range(6):
            
            if not hal_stopped:
                nic_cmd_list = list()
                nic_cmd = MFG_DIAG_CMDS().NIC_DIAG_STOP_HAL_FMT
                nic_cmd_list.append(nic_cmd)
                if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
                    return False

                nic_cmd = MFG_DIAG_CMDS().NIC_HAL_RUNNING_FMT
                cmd_buf = self.nic_get_info(nic_cmd)
                if not cmd_buf:
                    self.nic_set_err_msg("Buffer empty")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                
                match = re.findall("/nic/bin/hal", cmd_buf)
                if not match:
                    hal_stopped = True

            if not sysmgr_stopped:
                nic_cmd_list = list()
                nic_cmd = MFG_DIAG_CMDS().NIC_DIAG_STOP_SYSMGR_FMT
                nic_cmd_list.append(nic_cmd)
                if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
                    return False

                nic_cmd = MFG_DIAG_CMDS().NIC_SYSMGR_RUNNING_FMT
                cmd_buf = self.nic_get_info(nic_cmd)
                if not cmd_buf:
                    self.nic_set_err_msg("Buffer empty")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                
                match = re.findall("/sysmgr", cmd_buf)
                if not match:
                    sysmgr_stopped = True

            if not sysmond_stopped:
                nic_cmd_list = list()
                nic_cmd = MFG_DIAG_CMDS().NIC_DIAG_STOP_SYSMOND_FMT
                nic_cmd_list.append(nic_cmd)
                if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
                    return False

                nic_cmd = MFG_DIAG_CMDS().NIC_SYSMOND_RUNNING_FMT
                cmd_buf = self.nic_get_info(nic_cmd)
                if not cmd_buf:
                    self.nic_set_err_msg("Buffer empty")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

                match = re.findall("/sysmond", cmd_buf)
                if not match:
                    sysmond_stopped = True

            if hal_stopped and sysmgr_stopped and sysmond_stopped:
                break

            time.sleep(5)

    def nic_start_diag(self, aapl, dis_hal=False, mtp_type=None):
        # setup diag env on nic
        nic_cmd_list = list()

        time_str = str(libmfg_utils.timestamp_snapshot())
        nic_cmd = MFG_DIAG_CMDS().NIC_DATE_SET_FMT.format(time_str)
        nic_cmd_list.append(nic_cmd)
        if not dis_hal:
            if not aapl:
                self.nic_kill_hal()
                nic_cmd = MFG_DIAG_CMDS().NIC_DIAG_STOP_HAL_FMT
                nic_cmd_list.append(nic_cmd)
                # prevent cpldapp lock getting stuck which depends on hal
                nic_cmd = "rm /var/lock/cpldapp_lock"
                nic_cmd_list.append(nic_cmd)
                nic_cmd = "rm /dev/shm/cpld_lock"
                nic_cmd_list.append(nic_cmd)
                nic_cmd = MFG_DIAG_CMDS().NIC_DIAG_CONFIG_FMT
                nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS().NIC_DIAG_INIT_FMT.format(self._slot+1)
        nic_cmd_list.append(nic_cmd)
        nic_cmd = "source /etc/profile"
        nic_cmd_list.append(nic_cmd)

        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.nic_set_err_msg("Unable to stop HAL")
            return False

        # Start NIC DSP
        cmd = MFG_DIAG_CMDS().NIC_DSP_START_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
            self.nic_set_err_msg("Unable to start diagmgr")
            return False

        # get asic lib version
        nic_cmd = MFG_DIAG_CMDS().NIC_DIAG_ASIC_VERSION_FMT.format(self._asic_type)
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to get nic asic version")
            return False
        match = libmfg_utils.rgx_extract_commit_date(cmd_buf)
        if match:
            self._diag_asic_ver = match
        else:
            self.nic_set_err_msg("Unable to find nic asic version")
            return False

        if self._nic_type in GIGLIO_NIC_TYPE_LIST:
            self.nic_exec_cmds(["ls /data/nic_arm/", "du -a /data/nic_arm/giglio/ -d3"])
        else:
            self.nic_exec_cmds(["ls /data/nic_arm/", "du -a /data/nic_arm/{:s}/ -d3".format(self._asic_type)])

        # get emmc nic utils version
        nic_cmd = MFG_DIAG_CMDS().NIC_DIAG_UTIL_VERSION_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to get nic utils version")
            return False
        match = libmfg_utils.rgx_extract_commit_date(cmd_buf)
        if match:
            self._diag_util_ver = match
        else:
            self.nic_set_err_msg("Unable to find nic utils version")
            return False

        # get nic diag version
        nic_cmd = MFG_DIAG_CMDS().NIC_DIAG_VERSION_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to get nic diag version")
            return False
        match = libmfg_utils.rgx_extract_commit_date(cmd_buf)
        if match:
            self._diag_ver = match
        else:
            self.nic_set_err_msg("Unable to find nic diag version")
            return False

        # check if hal is running
        nic_cmd = MFG_DIAG_CMDS().NIC_HAL_RUNNING_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to check hal")
            return False
        if MFG_DIAG_SIG.NIC_HAL_RUNNING_SIG in cmd_buf:
            hal_running = True
        else:
            hal_running = False

        # aapl and hal_running should be both True or both False
        if not dis_hal:
            if hal_running != aapl:
                self.nic_set_err_msg("AAPL or HAL not running")
                return False
        else:
            if hal_running == False:
                self.nic_set_err_msg("AAPL or HAL not running")
                return False

        return True


    def nic_set_vmarg(self, vmarg_param, percentage=""):
        nic_cmd_list = list()
        percentage = int(percentage) if percentage else 0
        if self._nic_type in SALINA_DPU_NIC_TYPE_LIST:
            # sleep let firmware fully up and enbaled the watchdog timer, then we using i2c command to diable it. 
            # otherwaise firmware enable watchdog timer after we disable it, which cause N1 reboot
            if vmarg_param.lower() == "high":
                normal_percentage = 3
            elif vmarg_param.lower() == "low":
                normal_percentage = -3
            else:
                normal_percentage = 0

            target_percentage = normal_percentage if abs(normal_percentage) > abs(percentage) else percentage
            cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
            if not self.mtp_exec_cmd(cmd):
                return False
            cmd = MFG_DIAG_CMDS().SALINA_NIC_VMARG_SET_FMT.format((self._slot+1), target_percentage)
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
                return False
            if MFG_DIAG_SIG.SALINA_NIC_VMARG_SET in self.nic_get_cmd_buf():
                return True
            else:
                return False
        else:
            nic_cmd = MFG_DIAG_CMDS().NIC_VMARG_SET_FMT.format(vmarg_param, str(percentage))
            nic_cmd_list.append(nic_cmd)

            if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
                return False

            return True

    def salina_nic_set_ddr_vmarg(self, vmarg_param='normal'):
        """
        Salina DDR vmargin only can be set by a35 uboot env variable, supported vmarg percentage range if from -2 to 3 

        Args:
            vmarg_param: specify the vmarg patameter by string or int, default to normal
            if string, one of 'high', 'low' and 'normal', or like '-2', '3', '0', caseinsensitive
            if int, -2, 3, 0

        Returns:
            _type_: boolean, True or False
        """

        if self._nic_type not in SALINA_DPU_NIC_TYPE_LIST:
            return False

        vmarg_str2_number = {
            'high'      : 3,
            'low'       : -2,
            'normal'    :  0
        }

        if isinstance(vmarg_param, str):
            vmarg_param = vmarg_param.lower()
            if vmarg_param in vmarg_str2_number:
                target_percentage = vmarg_str2_number[vmarg_param]
            else:
                try:
                    target_percentage = int(vmarg_param)
                except ValueError:
                    return False
        elif isinstance(vmarg_param, int):
            target_percentage = vmarg_param
        else:
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False
        cmd = MFG_DIAG_CMDS().SALINA_NIC_DDR_VMARG_SET_FMT.format((self._slot+1), target_percentage)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
            return False
        if "ddr_vmarg="+str(target_percentage) in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_display_voltage(self):
        nic_cmd = [MFG_DIAG_CMDS().NIC_DISP_VOLT_FMT]
        if not self.nic_exec_cmds(nic_cmd):
            return False
        return True

    def nic_set_sw_boot(self):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS().NIC_SET_MAINFWA_BOOT_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        if not self.nic_exec_cmds(nic_cmd_list):
            return False

        return True


    def nic_set_gold_boot(self):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS().NIC_SET_GOLD_BOOT_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        if not self.nic_exec_cmds(nic_cmd_list):
            return False

        return True


    # for the Naples100 before PP, no 2nd fru instance
    def nic_2nd_fru_exist(self, pn):
        for item in ["68-0003-01", "68-0003-02", "68-0003-03", "68-0004-02", "68-0004-03"]:
            if item in pn:
                return False
        return True

    def nic_fru_init(self, factory_location, init_date=True, swmtestmode=Swm_Test_Mode.SWMALOM, fpo=False):
        ### 1. Validate ASIC-facing FRU
        fru_buf = self.nic_read_fru(fpo, smb_fru=False)
        if not fru_buf:
            self.nic_set_err_msg("Unable to read ASIC FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_pn(fru_buf):
            self.nic_set_err_msg("Part number doesn't match any known formats in ASIC FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_sn(fru_buf):
            self.nic_set_err_msg("Serial number doesn't match any known formats in ASIC FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_validate_sn(factory_location):
            self.nic_set_err_msg("Serial number in ASIC FRU does not match this factory location")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_mac(fru_buf):
            self.nic_set_err_msg("MAC address doesn't match any known formats in ASIC FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_date(fru_buf, init_date):
            self.nic_set_err_msg("Date field doesn't match any known formats in ASIC FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        ### 1b. Validate HPE product number, if applicable
        if init_date:
            if self._pn_format in (
                PART_NUMBERS_MATCH.N25_SWM_HPE_PN_FMT,
                PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT
                ):
                if not self.nic_fru_parse_hpe_prod_num(fru_buf):
                    self.nic_set_err_msg("HPE Product Number doesn't match any known formats in ASIC FRU")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

        asic_sn = self._sn
        asic_pn = self._pn
        asic_mac = self._mac
        asic_date = self._date
        if self._prod_num != None:
            asic_prod_num = self._prod_num

        ### 1c. Validate Diagnostic part number, if applicable
        if init_date and self._nic_type in CTO_MODEL_TYPE_LIST:
            if not self.nic_fru_parse_dpn(fru_buf):
                self.nic_set_err_msg("DPN field doesn't match any known formats in ASIC FRU")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

        
        ### 2. Validate SMBUS (MTP-facing) FRU, if present
        if self.nic_2nd_fru_exist(self._pn):

            fru_buf = self.nic_read_fru(fpo, smb_fru=True)
            if not fru_buf:
                self.nic_set_err_msg("Unable to read SMB FRU")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            if not self.nic_fru_parse_pn(fru_buf):
                self.nic_set_err_msg("Part number doesn't match any known formats in SMB FRU")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            if not self.nic_fru_parse_sn(fru_buf):
                self.nic_set_err_msg("Serial number doesn't match any known formats in SMB FRU")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            if not self.nic_fru_parse_mac(fru_buf):
                self.nic_set_err_msg("MAC address doesn't match any known formats in SMB FRU")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            if not self.nic_fru_parse_date(fru_buf, init_date):
                self.nic_set_err_msg("Date field doesn't match any known formats in SMB FRU")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            ### 2b. Validate HPE product number, if applicable
            if init_date:
                if self._pn_format in (
                    PART_NUMBERS_MATCH.N25_SWM_HPE_PN_FMT,
                    PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT
                    ):
                    if not self.nic_fru_parse_hpe_prod_num(fru_buf):
                        self.nic_set_err_msg("HPE Product Number doesn't match any known formats in SMB FRU")
                        self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                        return False

            ### 2c. Validate Diagnostic part number, if applicable
            if init_date and self._nic_type in CTO_MODEL_TYPE_LIST:
                if not self.nic_fru_parse_dpn(fru_buf):
                    self.nic_set_err_msg("DPN field doesn't match any known formats in SMB FRU")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

            ### 3. COMPARE ASIC & SMBUS
            if self._sn != asic_sn or self._mac != asic_mac or self._pn != asic_pn or self._date != asic_date:
                err_msg = " ERR: FRU MISMATCH BETWEEN SMB FRU AND ASIC FRU \n"
                err_msg += " SN  " + self._sn + " " + asic_sn + "\n"
                err_msg += " MAC " + self._mac + " " + asic_mac + "\n"
                err_msg += " PN  " + self._pn + " " + asic_pn + "\n"
                if asic_date != None:
                    err_msg += " DT  " + self._date + " " + asic_date + "\n"
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                self.nic_set_err_msg(err_msg)
                return False
            if self._prod_num != None:
                if self._prod_num != asic_prod_num:
                    self.nic_set_err_msg("ERR: FRU MISMATCH BETWEEN SMB FRU AND ASIC FRU \n")
                    self.nic_set_err_msg(" HPE PROD NUM " + self._prod_num + " " + asic_prod_num + "\n")
                    return False

        ### 4. Validate ALOM FRU, if present
        if self._nic_type == NIC_Type.NAPLES25SWM and swmtestmode in (Swm_Test_Mode.SWMALOM, Swm_Test_Mode.ALOM):
            errlist = list()
            if not self.nic_swm_check_alom_present(errlist):
                self.nic_set_err_msg(" NIC_FRU_INIT: ALOM IS NOT SHOWING PRESENT")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            if not self.nic_alom_fru_init(factory_location):
                return False

        ### 5. Validate OCP Adapter FRU, if present
        if self._nic_type == NIC_Type.NAPLES25OCP:
            if not self.nic_ocp_adapter_fru_init(factory_location):
                return False

        return True

    def nic_smb_fru_init(self, factory_location, fpo=False):
        """ Same as nic_fru_init(), but SMB fru only, and no validation """
        fru_buf = self.nic_read_fru(fpo, smb_fru=True)
        if not fru_buf:
            self.nic_set_err_msg("Unable to read SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_pn(fru_buf):
            self.nic_set_err_msg("Part number doesn't match any known formats in SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_sn(fru_buf):
            self.nic_set_err_msg("Serial number doesn't match any known formats in SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_mac(fru_buf):
            self.nic_set_err_msg("MAC address doesn't match any known formats in SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_date(fru_buf, init_date = not fpo):
            self.nic_set_err_msg("Date field doesn't match any known formats in SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_smb_dpn_fru_init(self, factory_location, fpo=False):
        """ Same as nic_fru_init(), but SMB fru only, and no validation """
        fru_buf = self.nic_read_fru(fpo, smb_fru=True)
        if not fru_buf:
            self.nic_set_err_msg("Unable to read SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_set_dpn(fru_buf):
            self.nic_set_err_msg("DPN doesn't match any known formats in SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_alom_fru_init(self, factory_location, fpo=False):
        fru_buf = self.nic_read_fru(fpo, smb_fru=True, alom=True)
        if not fru_buf:
            self.nic_set_err_msg("Unable to read ALOM FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_alom_bia(fru_buf):
            self.nic_set_err_msg("ALOM BIA part number doesn't match any known formats")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_alom_pia(fru_buf):
            self.nic_set_err_msg("ALOM PIA part number doesn't match any known formats")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_sn(fru_buf, alom=True):
            self.nic_set_err_msg("ALOM serial number doesn't match any known formats")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_ocp_adapter_fru_init(self, factory_location, fpo=False):
        if self._nic_type != NIC_Type.NAPLES25OCP:
            self.nic_set_err_msg("OCP Adapter FRU init function is not for type {:s}".format(self._nic_type))
            return False

        fru_buf = self.nic_read_fru(fpo, smb_fru=True, ocp_adap=True)
        if not fru_buf:
            self.nic_set_err_msg("Unable to read OCP Adapter FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_sn(fru_buf, ocp_adap=True):
            self.nic_set_err_msg("OCP Adapter serial number doesn't match any known formats")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_date(fru_buf, init_date=True, ocp_adap=True):
            self.nic_set_err_msg("OCP Adapter date field doesn't match any known formats")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def validate_serial_number_strict(self, sn, factory_location, pn_format, pn):
        if factory_location == Factory.LAB:
            return libmfg_utils.serial_number_validate(sn)

        try:
            sn_regex = SN_FORMAT_TABLE[factory_location][pn_format]
        except KeyError:
            try:
                sn_regex = SN_FORMAT_TABLE[factory_location]["DEFAULT"]
            except KeyError:
                self.nic_set_err_msg("factory_location not initialized correctly to validate Serial Number")
                return False

        if re.match(sn_regex, sn):
            return True
        else:
            self.nic_set_err_msg("Serial Number did not match formatting for {:s} at site {:s}".format(pn, factory_location))
            return False

    def nic_fru_validate_sn(self, factory_location, alom=False, ocp_adap=False):
        if alom:
            sn = self._alom_sn
            pn = self._alom_pn
            pn_format = PART_NUMBERS_MATCH.ALOM_HPE_PN_FMT
        elif ocp_adap:
            sn = self._riser_sn
            pn = OCP_ADAPTER_FIXED_PN
            pn_format = PART_NUMBERS_MATCH.N25_OCP_ADAPTER_PN_FMT
        else:
            sn = self._sn
            pn = self._pn
            pn_format = self._pn_format

        if not self.validate_serial_number_strict(sn, factory_location, pn_format, pn):
            return False
        return True

    def nic_fru_parse_set_dpn(self, fru_buf):
        if not self.nic_fru_parse_dpn(fru_buf):
            self.nic_set_err_msg("Unable to parse dpn fru")
            return False
        return True

    def nic_fru_parse_sn(self, fru_buf, alom=False, ocp_adap=False):
        sn = libmfg_utils.serial_number_validate(fru_buf, exact_match=False)
        if not sn:
            self.nic_set_err_msg("SN read failed")
            return False
        if alom:
            self._alom_sn = sn
        elif ocp_adap:
            self._riser_sn = sn
        else:
            self._sn = sn
        return True

    def nic_fru_parse_pn(self, fru_buf):
        """ Save to self._pn and return True/False """
        PART_NUM_FIELD = r"Part Number"
        ASSY_NUM_FIELD = r"Assembly Number"
        PROD_NUM_FIELD = r"HPE Product Number"
        pn_table = {
            NIC_Type.NAPLES100: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N100_PEN_PN_FMT),                     #68-0003-01 01    NAPLES 100 PENSANDO
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.N100_NET_PN_FMT)                      #111-04635        NAPLES 100 NETAPP
                ],
            NIC_Type.NAPLES100IBM: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.N100_IBM_PN_FMT)                      #68-0013-01 03    NAPLES100 IBM
                ],
            NIC_Type.NAPLES100HPE: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N100_HPE_PN_FMT),                     #P37692-001       NAPLES100 HPE
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N100_HPE_CLD_PN_FMT)                  #P41854-001       NAPLES100 HPE CLOUD
                ],
            NIC_Type.NAPLES100DELL: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N100_DELL_PN_FMT)                     #68-0024-01 XX    NAPLES100 DELL
                ],

            NIC_Type.NAPLES25: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_PEN_PN_FMT),                      #68-0005-03 XX    NAPLES25 PENSANDO
                (PROD_NUM_FIELD, PART_NUMBERS_MATCH.N25_HPE_PN_FMT),                      #P18669-001       NAPLES25 HPE
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_EQI_PN_FMT)                       #68-0008-xx yy    NAPLES25 EQUINIX
                ],
            NIC_Type.NAPLES25SWM: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT),              #P26968-001       NAPLES25 SWM HPE
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_SWM_HPE_PN_FMT),                  #P26968-002       NAPLES25 SWM HPE
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_SWM_HPE_CLD_PN_FMT),              #P41851-001       NAPLES25 SWM HPE CLOUD
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_SWM_HPE_TAA_PN_FMT),              #P46653-001       NAPLES25 SWM HPE TAA
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_SWM_PEN_PN_FMT),                  #68-0016-01 XX    NAPLES25 SWM PENSANDO
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_SWM_PEN_TAA_PN_FMT),              #68-0017-01 XX    NAPLES25 SWM PENSANDO TAA
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.ALOM_HPE_PN_FMT)                      #P26971-001       NAPLES25 SWM HPE ALOM ADAPTER
                ],
            NIC_Type.NAPLES25SWMDELL: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.N25_SWM_DEL_PN_FMT)                   #68-0014-01 XX    NAPLES25 SWM DELL
                ],
            NIC_Type.NAPLES25SWM833: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_SWM_833_PN_FMT)                   #68-0019-01 XX    NAPLES25 SWM 833
                ],

            NIC_Type.NAPLES25OCP: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_OCP_PEN_PN_FMT),                  #68-00xx-xx       NAPLES25 OCP PENSANDO
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_OCP_HPE_PN_FMT),                  #P37689-001       NAPLES25 OCP HPE
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.N25_OCP_HPE_CLD_PN_FMT),              #P41857-001       NAPLES25 OCP HPE CLOUD
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.N25_OCP_DEL_PN_FMT)                   #68-0010-01       NAPLES25 OCP DELL
                ],

            NIC_Type.FORIO: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.FORIO_PN_FMT)                         #68-0007-01 XX    FORIO
                ],
            NIC_Type.VOMERO: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.VOMERO_PN_FMT)                        #68-0009-01 XX    VOMERO
                ],
            NIC_Type.VOMERO2: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.VOMERO2_PN_FMT)                       #68-0011-01 XX    VOMERO2
                ],

            NIC_Type.ORTANO: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO_PN_FMT)                        #68-0015-01 XX    ORTANO1
                ],
            NIC_Type.ORTANO2: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2_ORC_PN_FMT),                  #68-0015-02 XX    ORTANO2 ORACLE
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2_PEN_PN_FMT)                   #68-0021-02 XX    ORTANO2 MICROSOFT
                ],
            NIC_Type.ORTANO2ADI: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2ADI_ORC_PN_FMT)                #68-0026-01 XX    ORTANO2ADI ORACLE
                ],
            NIC_Type.ORTANO2ADIMSFT: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2ADI_MSFT_PN_FMT)               #68-0034-01 XX    ORTANO2ADI MICROSOFT
                ],
            NIC_Type.ORTANO2ADIIBM: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2ADI_IBM_PN_FMT)                #68-0028-01 XX    ORTANO2ADI IBM
                ],
            NIC_Type.ORTANO2INTERP: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2INTERP_ORC_PN_FMT)             #68-0029-01 XX    ORTANO2 Interposer
                ],
            NIC_Type.GINESTRA_D4: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.GINESTRA_D4_PN_FMT)                   #68-0074-01 XX    GINESTRA_D4
                ],
            NIC_Type.GINESTRA_D5: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.GINESTRA_D5_PN_FMT)                   #68-0075-01 XX    GINESTRA_D5
                ],
            NIC_Type.GINESTRA_S4: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.GINESTRA_S4_PN_FMT)                   #68-0076-01 XX    GINESTRA_S4
                ],
            NIC_Type.GINESTRA_CIS: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.GINESTRA_CIS_PN_FMT)                  #68-0094-01 XX    GINESTRA_CIS
                ],
            NIC_Type.ORTANO2SOLO: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_PN_FMT)               #68-0077-01 XX    ORTANO2 SOLO
                ],
            NIC_Type.ORTANO2SOLOL: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_L_PN_FMT)             #68-0095-01 XX    ORTANO2 SOLO-L
                ],
            NIC_Type.ORTANO2SOLOORCTHS: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_THS_PN_FMT)           #68-0089-01 XX    ORTANO2 SOLO Tall Heat Sink
                ],
            NIC_Type.ORTANO2SOLOMSFT: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2SOLO_MSFT_PN_FMT)              #68-0090-01 XX    ORTANO2 SOLO MICROSOFT
                ],
            NIC_Type.ORTANO2SOLOS4: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2SOLO_S4_PN_FMT)                #68-0092-01 XX    ORTANO2 SOLO S4
                ],
            NIC_Type.ORTANO2ADICR: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2ADI_CR_PN_FMT)                 #68-0049-03 XX    ORTANO2ADI CR
                ],
            NIC_Type.ORTANO2ADICRMSFT: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2ADI_CR_MSFT_PN_FMT)            #68-0091-01 XX    ORTANO2ADI CR MICROSOFT
                ],
            NIC_Type.ORTANO2ADICRS4: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2ADI_CR_S4_PN_FMT)              #68-0092-01 XX    ORTANO2ADI CR S4
                ],
            NIC_Type.POMONTEDELL: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.POMONTEDELL_PN_FMT)                   #0PCFPC X/A       POMONTE DELL
                ],
            NIC_Type.LACONA32DELL: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.LACONA32DELL_PN_FMT)                  #0X322F X/A       LACONA32 DELL
                ],
            NIC_Type.LACONA32: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.LACONA32_PN_FMT)                      #P47930-001       LACONA32 HPE
                ],
            NIC_Type.LENI: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.LENI_PN_FMT)                          #105-P10800-0 XX    LENI
                ],
            NIC_Type.LENI48G: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.LENI48G_PN_FMT)                       #102-P10600-0 XX    LENI48G
                ],
            NIC_Type.MALFA: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.MALFA_PN_FMT)                         #102-P10600-0 XX    MALFA
                ],
            NIC_Type.POLLARA: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.POLLARA_PN_FMT),                      #102-P11100-0 XX    POLLARA
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.POLLARA_HPE_PN_FMT)                   #102-P11101-0 XX    POLLARA HPE
                ],
            NIC_Type.LINGUA: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.LINGUA_PN_FMT)                        #102-P11500-0 XX    LINGUA
                ],
            NIC_Type.GELSOP: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.GELSOP_PN_FMT)                        #102-P12100-00C 04  GELSOP
                ],
            NIC_Type.GELSOX: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.GELSOX_PN_FMT)                        #102-P12200-00A 04  GELSOX
                ],
            NIC_Type.MORTARO: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.MORTARO_PN_FMT)                       #102-P12300-00B 04  MORTARO
                ],
            NIC_Type.SARACENO: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.SARACENO_PN_FMT)                      #102-P12500-00A 04  SARACENO
                ],
        }

        if self._nic_type not in list(pn_table.keys()):
            self.nic_set_err_msg("Could not find this NIC TYPE in part number table")
            return False

        pn_regex_list = []
        for nic_type in pn_table:
            pn_regex_list += pn_table[nic_type]

        for disp_field, pn_regex in pn_regex_list:
            pn_disp_regex = r"%s +(%s)" % (disp_field, pn_regex)
            match = re.findall(pn_disp_regex, fru_buf)
            if match:
                self._pn = match[0]
                self._pn_format = pn_regex
                return True

        self.nic_set_err_msg("Exhausted part number search")
        return False

    def nic_fru_parse_alom_bia(self, fru_buf):
        """ Save to self._alom_pn and return True/False """
        PART_NUM_FIELD = r"Part Number"
        pn_table = {
            NIC_Type.NAPLES25SWM: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.ALOM_HPE_PN_FMT)                      #P26971-001       NAPLES25 SWM HPE ALOM ADAPTER
                ]
        }
        if self._nic_type not in list(pn_table.keys()):
            self.nic_set_err_msg("Could not find this NIC TYPE in part number table")
            return False

        pn_regex_list = pn_table[self._nic_type]
        if not pn_regex_list:
            self.nic_set_err_msg("Script error: rules for this part number are not defined correctly")
            return False

        for disp_field, pn_regex in pn_regex_list:
            pn_disp_regex = r"%s +(%s)" % (disp_field, pn_regex)

            match = re.findall(pn_disp_regex, fru_buf)
            if match:
                self._alom_pn = match[0]
                return True

        return False

    def nic_fru_parse_alom_pia(self, fru_buf):
        """ Save to self._alom_prod_num and return True/False """
        PROD_NUM_FIELD = r"HPE Product Number"
        pn_table = {
            NIC_Type.NAPLES25SWM: [
                (PROD_NUM_FIELD, r"P26969\-B21")
                ]
        }
        if self._nic_type not in list(pn_table.keys()):
            self.nic_set_err_msg("Could not find this NIC TYPE in part number table")
            return False

        pn_regex_list = pn_table[self._nic_type]
        if not pn_regex_list:
            self.nic_set_err_msg("Script error: rules for this part number are not defined correctly")
            return False

        for disp_field, pn_regex in pn_regex_list:
            pn_disp_regex = r"%s +(%s)" % (disp_field, pn_regex)

            match = re.findall(pn_disp_regex, fru_buf)
            if match:
                self._alom_prod_num = match[0]
                return True

        return False

    def nic_fru_parse_mac(self, fru_buf):
        """ Save to self._mac and return True/False """
        disp_field = r"MAC Address Base"
        mac_regex = PEN_MAC_DASHES_FMT
        mac_disp_regex = r"%s +(%s)" % (disp_field, mac_regex)
        match = re.findall(mac_disp_regex, fru_buf)
        if match:
            self._mac = match[0]
        else:
            return False
        return True

    def nic_fru_parse_date(self, fru_buf, init_date, ocp_adap=False):
        """ Save to self._date and return True/False """
        if init_date:
            disp_field = r"Manufacturing Date/Time"
            date_hex = r"0x[A-Z0-9]+"
            date_regex = r"\d{2}/\d{2}/\d{2}"
            date_disp_regex = r"%s +%s +(%s)" % (disp_field, date_hex, date_regex)
            match = re.findall(date_disp_regex, fru_buf)
            if match:
                if ocp_adap:
                    self._riser_progdate = match[0].replace('/','')
                else:
                    self._date = match[0].replace('/','')
            else:
                return False
        else:
            self._date = None
        return True

    def nic_fru_parse_hpe_prod_num(self, fru_buf):
        """ Save to self._prod_num and return True/False """
        disp_field = r"HPE Product Number"
        pn_regex = HPE_PROD_NUM_FMT
        pn_disp_regex = r"%s +(%s)" % (disp_field, pn_regex)

        match = re.findall(pn_disp_regex, fru_buf)
        if match:
            self._prod_num = match[0]
            return True

        return False

    def nic_fru_parse_hpe_version(self, fru_buf):
        REVISION_FIELD = r"Revision Code"
        PROD_VER_FIELD = r"Product Version"
        VER_HEX_MATCH = "[0-9A-Fa-f]+"

        if self._pn_format == PART_NUMBERS_MATCH.N25_HPE_PN_FMT:
            disp_field = REVISION_FIELD
        elif self._pn_format == PART_NUMBERS_MATCH.N25_SWM_HPE_PN_FMT:
            disp_field = PROD_VER_FIELD
        elif self._pn_format == PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT:
            disp_field = PROD_VER_FIELD
        else:
            # not applicable
            self.nic_set_err_msg("parse_hpe_version function not for this nic type")
            return False
        hpe_version_disp_regex = r"%s +(%s)" % (disp_field, VER_HEX_MATCH)

        match = re.findall(hpe_version_disp_regex, fru_buf)
        if not match:
            self.nic_set_err_msg("Couldn't find {:s} field in FRU".format(disp_field))
            return False
        self._hpe_prod_ver = match[0]

        return True

    def nic_fru_init_hpe_version(self):
        fru_buf = self.nic_read_fru(smb_fru=False)
        if not fru_buf:
            self.nic_set_err_msg("Unable to read ASIC FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_hpe_version(fru_buf):
            self.nic_set_err_msg("Product Version/Revision doesn't match any known formats in ASIC FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        fru_buf = self.nic_read_fru(smb_fru=True)
        if not fru_buf:
            self.nic_set_err_msg("Unable to read SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_fru_parse_hpe_version(fru_buf):
            self.nic_set_err_msg("Product Version/Revision doesn't match any known formats in SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_fru_parse_dpn(self, fru_buf):
        """ Save to self._dpn and return True/False """
        disp_field = r"DPN \(Diagnostic Part Number\)"

        for dpn_regex in libmfg_utils.get_all_valid_dpn():
            dpn_disp_regex = r"%s +(%s)" % (disp_field, str(dpn_regex))
            match = re.findall(dpn_disp_regex, fru_buf)
            if match:
                self._dpn = dpn_regex
                return True

        self.nic_set_err_msg("Programmed DPN not a valid DPN")
        return False        

    def nic_get_fru(self):
        if not self._sn or not self._mac or not self._pn:

            return None
        else:
            return [self._sn, self._mac, self._pn, self._date]

    def nic_alom_get_fru(self):
        if not self._alom_sn or not self._alom_pn:
            return None
        else:
            return [self._alom_sn, self._alom_pn, self._date]

    def nic_alom_sn_get_fru(self):
        if not self._alom_sn:
            return None
        else:
            return self._alom_sn
            
    def nic_get_assettag(self):
        if not self._assettagnumber:
            return None
        else:
            return self._assettagnumber

    def nic_get_hpe_version(self):
        return self._hpe_prod_ver

    def nic_get_naples_pn(self):
        if not self._pn:
            return None
        else:
            return self._pn

    def nic_read_fru(self, fpo=False, smb_fru=False, alom=False, ocp_adap=False, dev=None):
        cmd = "eeutil -disp"
        if fpo:
            cmd += " -fpo"

        if alom:
            cmd += " -hpeAlom"
        elif ocp_adap:
            cmd += " -custType MTPOCPADAPTER"
        # legacy type specifications:
        elif self._nic_type == NIC_Type.NAPLES25SWM:
            cmd += " -hpeSwm"
        elif self._nic_type == NIC_Type.NAPLES25OCP:
            cmd += " -hpeOcp"
        elif self._nic_type == NIC_Type.NAPLES25 and libmfg_utils.part_number_match(self._pn, PART_NUMBERS_MATCH.N25_HPE_PN_FMT):
            cmd += " -hpe"

        if smb_fru:
            cmd += " -dev=fru" if dev is None else " -dev=" + dev
            cmd += " -uut=UUT_{:d}".format(self._slot+1)
            fru_buf = self.mtp_get_info(cmd)
        else:
            fru_buf = self.nic_get_info(cmd)

        return fru_buf

    def nic_write_fru(self, date, sn, mac, pn, nic_type=None, dpn=False, sku=False, smb_fru=False, dev=None, boardid=None):
        eeutil_cmd_lookup = {
            PART_NUMBERS_MATCH.N100_PEN_PN_FMT:         "eeutil -dev=fru -update",
            PART_NUMBERS_MATCH.N100_NET_PN_FMT:         "eeutil -dev=fru -update",
            PART_NUMBERS_MATCH.N100_IBM_PN_FMT:         "eeutil -dev=fru -update",
            PART_NUMBERS_MATCH.N100_HPE_PN_FMT:         "eeutil -dev=fru -update",
            PART_NUMBERS_MATCH.N100_HPE_CLD_PN_FMT:     "eeutil -dev=fru -update",
            PART_NUMBERS_MATCH.N100_DELL_PN_FMT:        "eeutil -dev=fru -update",

            PART_NUMBERS_MATCH.N25_PEN_PN_FMT:          "eeutil -dev=fru -update",
            PART_NUMBERS_MATCH.N25_HPE_PN_FMT:          "eeutil -dev=fru -update -hpe",
            PART_NUMBERS_MATCH.N25_EQI_PN_FMT:          "eeutil -dev=fru -update",

            PART_NUMBERS_MATCH.N25_SWM_HPE_PN_FMT:      "eeutil -dev=fru -update -erase -numBytes=256 -hpeSwm",
            PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT:  "eeutil -dev=fru -update -erase -numBytes=256 -hpeSwm",
            PART_NUMBERS_MATCH.N25_SWM_HPE_CLD_PN_FMT:  "eeutil -dev=fru -update -erase -numBytes=256 -hpeSwm",
            PART_NUMBERS_MATCH.N25_SWM_HPE_TAA_PN_FMT:  "eeutil -dev=fru -update -erase -numBytes=256 -hpeSwm",
            PART_NUMBERS_MATCH.N25_SWM_PEN_PN_FMT:      "eeutil -dev=fru -update",
            PART_NUMBERS_MATCH.N25_SWM_PEN_TAA_PN_FMT:  "eeutil -dev=fru -update",
            PART_NUMBERS_MATCH.N25_SWM_DEL_PN_FMT:      "eeutil -dev=fru -update",
            PART_NUMBERS_MATCH.N25_SWM_833_PN_FMT:      "eeutil -dev=fru -update",

            PART_NUMBERS_MATCH.N25_OCP_HPE_PN_FMT:      "eeutil -dev=fru -update -erase -numBytes=256 -hpeOcp",
            PART_NUMBERS_MATCH.N25_OCP_DEL_PN_FMT:      "eeutil -dev=fru -update -erase -numBytes=256"
        }

        if nic_type is None:
            # allow passing in nic_type, for rework script purposes
            nic_type = self._nic_type

        if nic_type in CAPRI_NIC_TYPE_LIST:
            if not self._pn_format:
                self.nic_set_err_msg("FRU not initialized correctly")
                return False
            cmd = eeutil_cmd_lookup[self._pn_format]
        elif nic_type in SALINA_NIC_TYPE_LIST + VULCANO_NIC_TYPE_LIST:
            cmd = "eeutil -update"
        else:
            cmd = "eeutil -dev=fru -update -erase -numBytes=512"
        
        cmd += " -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}'".format(date, sn, mac, pn)

        if dpn or sku:
            cmd += " -dpn='{:s}'".format(dpn)
        if sku:
            cmd += " -skuMode -sku='{:s}'".format(sku)

        if smb_fru:
            cmd += " -uut=UUT_{:d}".format(self._slot+1)
            if nic_type in SALINA_NIC_TYPE_LIST:
                if dev:
                    cmd += " -dev=" + dev
                else:
                    cmd += " -dev=FRU"
            if nic_type in VULCANO_NIC_TYPE_LIST:
                if dev:
                    cmd += " -dev=" + dev
                else:
                    cmd += " -dev=FRU"
                if not boardid:
                    self.nic_set_err_msg("For Vulcano cards, please Provide Board ID")
                    return False
                cmd += " -boardid=" + boardid
            print(cmd)
            cmd_buf = self.mtp_get_info(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY)
        else:
            if nic_type in SALINA_NIC_TYPE_LIST:
                cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
                if not self.mtp_exec_cmd(cmd):
                    self.nic_set_err_msg("Execute command {:s} failed".format(cmd))
                    return False
                cmd = MFG_DIAG_CMDS().MATERA_MTP_PROG_DPU_DRU_FMT.format(str(self._slot+1))
                if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
                    self.nic_set_err_msg("Execute command {:s} failed".format(cmd))
                    return False
                cmd_buf = self.nic_get_cmd_buf()
            elif nic_type in VULCANO_NIC_TYPE_LIST:
                cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
                if not self.mtp_exec_cmd(cmd):
                    self.nic_set_err_msg("Execute command {:s} failed".format(cmd))
                    return False
                cmd = MFG_DIAG_CMDS().PANAREA_MTP_PROG_DPU_DRU_FMT.format(str(self._slot+1))
                if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
                    self.nic_set_err_msg("Execute command {:s} failed".format(cmd))
                    return False
                cmd_buf = self.nic_get_cmd_buf()
            else:
                cmd_buf = self.nic_get_info(cmd)

        if not cmd_buf:
            if smb_fru:
                self.nic_set_err_msg("Unable to program SMB FRU")
            else:
                self.nic_set_err_msg("Unable to program ASIC FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        match = re.findall(r"FRU Checkum and Type\/Length Checks Passed|EEPROM updated|DPU_FRU\s+updated\s+successfully", cmd_buf)

        if not match:
            self.nic_set_err_msg(" FRU PROGRAMMING FAILED\n")
            self.nic_set_err_msg(" BUF =  {:s}".format(cmd_buf))
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_program_alom_fru(self, date, alom_sn, alom_pn):
        cmd = "eeutil -dev=fru -update -erase -numBytes=1024 -hpeAlom"

        cmd += " -date='{:s}' -sn='{:s}' -pn='{:s}'".format(date, alom_sn, alom_pn)

        cmd += " -uut=UUT_{:d}".format(self._slot+1)
        cmd_buf = self.mtp_get_info(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY)
    
        if not cmd_buf:
            self.nic_set_err_msg("Unable to program SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        match = re.findall(r"FRU Checkum and Type\/Length Checks Passed|EEPROM updated", cmd_buf)
        if not match:
            self.nic_set_err_msg(" FRU PROGRAMMING FAILED\n")
            self.nic_set_err_msg(" BUF =  {:s}".format(cmd_buf))
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
           
        return True

    def nic_program_ocp_adapter_fru(self, date, sn, mac, pn):
        if self._nic_type != NIC_Type.NAPLES25OCP:
            self.nic_set_err_msg("This function is only for OCP")
            return False
        
        cmd = "eeutil -dev=fru -update -erase -numBytes=128 -custType MTPOCPADAPTER"

        cmd += " -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}'".format(date, sn, mac, pn)
        
        cmd += " -uut=UUT_{:d}".format(self._slot+1)
        cmd_buf = self.mtp_get_info(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY)
    
        if not cmd_buf:
            self.nic_set_err_msg("Unable to program SMB FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        match = re.findall(r"FRU Checkum and Type\/Length Checks Passed|EEPROM updated", cmd_buf)
        if not match:
            self.nic_set_err_msg(" FRU PROGRAMMING FAILED\n")
            self.nic_set_err_msg(" BUF =  {:s}".format(cmd_buf))
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_ocp_rmii_linkup(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("Execute command {:s} failed".format(cmd))
            return False
        cmd = MFG_DIAG_CMDS().NIC_OCP_RMII_CHECK_FMT.format(str(self._slot+1))
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_OCP_RMII_DELAY):
            self.nic_set_err_msg("Execute command {:s} failed".format(cmd))
            return False
        if MFG_DIAG_SIG.NIC_OCP_RMII_OK_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_ocp_connect(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_SCRIPT_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("Execute command {:s} failed".format(cmd))
            return False
        cmd = MFG_DIAG_CMDS().NIC_OCP_CON_CHECK_FMT.format(str(self._slot+1))
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_OCP_CON_DELAY):
            self.nic_set_err_msg("Execute command {:s} failed".format(cmd))
            return False
        if MFG_DIAG_SIG.NIC_OCP_CON_OK_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_cpld_init(self, smb=False):

        # Panarea and vulcano cards
        if self._nic_type in VULCANO_NIC_TYPE_LIST:
            tout = 6
            parsed_dump = {}
            timestamp_registers = ['0x46', '0x45', '0x44', '0x43', '0x42']
            for address in ['0x40', '0x00', '0x01'] + timestamp_registers:
                cmd = f"sucutil cpld read -a {address} -s {self._slot + 1}"
                if not self.mtp_exec_cmd(cmd, timeout=tout):
                    return False
                dump_info = self.nic_get_cmd_buf()
                found_match = re.findall(r'cpld\s+read\s+([0-9a-fA-F]{2}),\s+value\s+([0-9a-fA-F]{2})', dump_info)
                if not found_match:
                    print("Error:")
                    print (dump_info)
                    return False
                for k, v in found_match:
                    parsed_dump[k] = v
            self._cpld_id = "0x{:X}".format(int(parsed_dump['40'], 16))
            self._cpld_ver = "0x{:X}".format(int(parsed_dump['00'], 16))
            self._cpld_ver_min = "0x{:X}".format(int(parsed_dump['01'], 16))
            self._cpld_timestamp = parsed_dump['40']
            date_time = []
            for register in timestamp_registers:
                date_time.append("{:02X}".format(int(parsed_dump[register.strip('0x')], 16)))
            self._cpld_timestamp = f'{date_time[1]}-{date_time[2]}-{date_time[0]}_{date_time[3]}:{date_time[4]}'
            cmd = f"export UUT_{self._slot + 1}={self._nic_type}"
            self.mtp_exec_cmd(cmd, timeout=tout)

            return True

        # Matera plus Salina and Turbo plus elba 
        read_data = [0]
        if smb:
            rc = self.nic_read_cpld_via_smbus(0x00, read_data)
        else:
            rc = self.nic_read_cpld(0x00, read_data)
        if not rc:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        self._cpld_ver = "0x{:X}".format(read_data[0])

        # init cpld id
        read_data = [0]
        if smb:
            rc = self.nic_read_cpld_via_smbus(0x80, read_data)
        else:
            rc = self.nic_read_cpld(0x80, read_data)
        if not rc:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        self._cpld_id = "0x{:X}".format(read_data[0])

        if self._nic_type in SALINA_NIC_TYPE_LIST:
            # There is date and time, return in format mm-dd-YY_HH:MM as libmfg_cfg.py defined
            # For salina cards, cpld timestamp register address mapping as following:
            # DATECODE_MM   0x90
            # DATECODE_HH   0x91
            # DATECODE_DD   0x92
            # DATECODE_mm   0x93
            # DATECODE_YY   0x94
            registers = [0x94, 0x93, 0x92, 0x91, 0x90]
            date_time = []
            for register in registers:
                read_data = [0]
                if smb:
                    rc = self.nic_read_cpld_via_smbus(register, read_data)
                else:
                    rc = self.nic_read_cpld(register, read_data)
                if not rc:
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                date_time.append("{:02X}".format(read_data[0]))

            self._cpld_timestamp = f'{date_time[1]}-{date_time[2]}-{date_time[0]}_{date_time[3]}:{date_time[4]}'
            return True
        elif self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            # there are no CPLD timestamps; use major revision + minor revision
            read_data = [0]
            if smb:
                rc = self.nic_read_cpld_via_smbus(0x1e, read_data)
            else:
                rc = self.nic_read_cpld(0x1e, read_data)
            if not rc:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            self._cpld_timestamp = "0x{:02X}".format(read_data[0])
            return True
        elif self._nic_type == NIC_Type.NAPLES25SWMDELL:
            # no timestamp, minor revision at 0x22 only
            read_data = [0]
            if smb:
                rc = True
                pass
            else:
                rc = self.nic_read_cpld(0x22, read_data)
            if not rc:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            self._cpld_timestamp = "{:02}".format(read_data[0])
            return True
        else:
            # get the month timestamp
            read_data = [0]
            if smb:
                rc = True
                pass
            else:
                rc = self.nic_read_cpld(0x22, read_data)
            if not rc:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            month = read_data[0]

            # get the date timestamp
            read_data = [0]
            if smb:
                rc = True
                pass
            else:
                rc = self.nic_read_cpld(0x23, read_data)
            if not rc:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            date = read_data[0]

            self._cpld_timestamp = "{:02d}-{:02d}".format(month, date)
            return True
    
    
    def nic_get_cpld(self):
        if not self._cpld_ver or not self._cpld_timestamp or not self._cpld_id:
            return None
        else:
            return [self._cpld_ver, self._cpld_timestamp, self._cpld_id, self._cpld_ver_min]


    def nic_get_diag(self):
        if not self._diag_ver or not self._diag_util_ver or not self._diag_asic_ver:
            return None
        else:
            return [self._diag_ver, self._diag_util_ver, self._diag_asic_ver]


    def nic_get_boot_info(self):
        if not self._boot_image or not self._kernel_timestamp:
            return None
        else:
            return [self._boot_image, self._kernel_timestamp]

    @nic_console_test()
    def nic_console_read_i2c(self, bus_num, dev_addr, reg_addr, read_data):
        nic_cmd = "i2cget -y {:d} {:x} {:x}".format(bus_num, dev_addr, reg_addr)
        self._nic_handle.sendline(nic_cmd)
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt,  timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        cpld_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cpld_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        match = re.findall(r"(0x[0-9a-fA-F]+)", cpld_buf)

        if len(match) >= 1:
            read_data[0] = int(match[0], 16)
        else:
            self.nic_set_cmd_buf(cpld_buf)
            return False

        self.nic_set_cmd_buf(self._nic_handle.before)
        return True

    def nic_get_pll_sta(self):
        pll_sta_reg_exp = r"addr 0x%x; data=(0x[0-9a-fA-F]+)"

        """
        NZ: weird hack, have to do this command twice so pexpect picks up the correct buffer.
        some timing or buffer window issue I couldn't solve.

        Originally (fails):
        1) turn_on_uut.sh
        2) cpldutil -cpld-rd

        Fix:
        1) turn_on_uut.sh
        2) turn_on_uut.sh ; cpldutil -cpld-rd

        Removing (1) from original picks up the output of the command executed before entering this function.
        Removing (1) and joining it in (2) picks up only half of the output of turn_on_uut
            and none from cpldutil.
        Delaying (1) delays the buffer also, so nothing changes.
        Adding delay after (1) misses the output of cpldutil.

        """

        reg_addr = 0x26
        if self._mtp_type == MTP_TYPE.MATERA:
            cmd = ""
        else:
            cmd = MFG_DIAG_CMDS().MTP_SMB_SEL_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd):
                return None
            cmd = MFG_DIAG_CMDS().MTP_SMB_SEL_FMT.format(self._slot+1) + " ;"
        cmd += MFG_DIAG_CMDS().MTP_SMB_RD_CPLD_FMT.format(reg_addr, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return None
        match = re.findall(pll_sta_reg_exp % reg_addr, self.nic_get_cmd_buf())
        if not match:
            return None
        else:
            reg26_data = int(match[0], 16)

        reg_addr = 0x28
        cmd = MFG_DIAG_CMDS().MTP_SMB_RD_CPLD_FMT.format(reg_addr, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return None
        match = re.findall(pll_sta_reg_exp % reg_addr, self.nic_get_cmd_buf())
        if not match:
            return None
        else:
            reg28_data = int(match[0], 16)

        return [reg26_data, reg28_data]

    def nic_read_cpld(self, reg_addr, read_data):
        nic_cmd = MFG_DIAG_CMDS().NIC_CPLD_READ_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, reg_addr)
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd = MFG_DIAG_CMDS().NIC_CPLD_READ_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, reg_addr)
        cpld_buf = self.nic_get_info(nic_cmd)
        if not cpld_buf:
            return False
        match = re.findall(r"(0x[0-9a-fA-F]+)", cpld_buf)
  
        if len(match) > 1:
            read_data[0] = int(match[1], 16)
        else:
            return False

        return True

    def nic_write_cpld(self, reg_addr, write_data):
        nic_cmd = MFG_DIAG_CMDS().NIC_CPLD_WRITE_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, reg_addr, write_data)
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd = MFG_DIAG_CMDS().NIC_CPLD_WRITE_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, reg_addr, write_data)
        cpld_buf = self.nic_get_info(nic_cmd)
        if not cpld_buf:
            return False
        return True

    @nic_console_test()
    def nic_console_read_cpld(self, reg_addr, read_data):
        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_CPLD_READ_ELBA_FMT.format("./", reg_addr))
        else:
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_CPLD_READ_FMT.format("./", reg_addr))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cpld_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cpld_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        match = re.findall(r"(0x[0-9a-fA-F]+)", cpld_buf)
  
        if len(match) > 1:
            read_data[0] = int(match[1], 16)
        else:
            self.nic_set_cmd_buf(cpld_buf)
            return False

        self.nic_set_cmd_buf(self._nic_handle.before)
        return True

    def nic_swm_check_alom_present(self, errlist):
        cpld_ctrl_reg = 0x01
        if self._nic_type == NIC_Type.NAPLES25SWM:
            read_data = [0]
            rc = self.nic_read_cpld(cpld_ctrl_reg, read_data)
            if not rc:
                errlist.append("ERROR: nic_read_cpld reg 0x01 FAILED for checking nic_swm_check_alom_present") 
                return False
            if (read_data[0] & 0x20) != 0:
                return True
        return False
    
    def nic_naples25swm_alom_cable_signal_test(self, errlist, testhighpower=1):
        #funcDebug = 1
        nic_scan_chain_reg = 0x33
        mtp_adapt_scan_reg0 = 0x02   #mask 0x0F
        mtp_adapt_scan_reg1 = 0x03   #mask 0x33
        mtp_adapt_cpld_ctrl_reg = 0x01
        mtp_adapt_initiate_scan_bit = 0x20
        read_data = [0]
        #LIST VALUES ARE --> NIC CPLD SCAN CHAIN REG WR DATA, MTP ADAPT CPLD SCANREG0 EXPECTED, MTP ADAPT CPLD SCANREG1 EXPECTED
        data = [[0xFF, 0x0F, 0x33], \
                [0x00, 0x00, 0x00], \
                [0x55, 0x05, 0x11], \
                [0xAA, 0x0A, 0x22] ]

        rc = self.nic_swm_check_alom_present(errlist)
        if not rc:
            errlist.append(" ERROR: ALOM PRESENT STATUS is FALSE.  Check Cable")
            return False

        #Check Cable Present via SMBUS side   Reg 0x32 BIT5
        rc = self.nic_read_cpld_via_smbus(0x32, read_data)
        if not rc: 
            errlist.append(" ERROR: nic_read_cpld_via_smbus FAILED")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False 
        if (read_data[0] & 0x20) != 0x20:
            errlist.append(" ERROR: ALOM PRESENT BIT NOT SET.  SMBUS CPLD REG 0x32 BIT5 NOT SET") 
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        #else:
        #    print(" ALOM PRESENT BIT SET") 

        rc = self.nic_read_mtp_adapt_cpld(mtp_adapt_cpld_ctrl_reg, read_data)
        if not rc: 
            errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False 
        cpld_ctrl_def = read_data[0]      

        #print(" ADD FIXME ALOM REG01 = " + hex(cpld_ctrl_def))
        for row in data:
            #WR Scan Chain Push Data on SWM CPLD
            rc = self.nic_write_cpld(nic_scan_chain_reg, row[0])
            if not rc: 
                errlist.append(" ERROR: nic_write_cpld Failed")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            
            #tell MTP ADAPTER CPLD to request scan data
            wr_data = (cpld_ctrl_def | mtp_adapt_initiate_scan_bit)
            rc = self.nic_write_mtp_adapt_cpld(mtp_adapt_cpld_ctrl_reg, wr_data)
            if not rc:
                errlist.append(" ERROR: nic_write_mtp_adapt_cpld Failed")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            rc = self.nic_write_mtp_adapt_cpld(mtp_adapt_cpld_ctrl_reg, cpld_ctrl_def)
            if not rc: 
                errlist.append(" ERROR: nic_write_mtp_adapt_cpld Failed")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            #read data on MTP ADAPT CPLD SCAN LOW BYTE
            rc = self.nic_read_mtp_adapt_cpld(mtp_adapt_scan_reg0, read_data)
            if not rc: 
                errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False 
            if read_data[0] != row[1]:
                errlist.append(" ERROR: MTP ADAPTER SCAN CHAIN DATA REG0:  READ 0x{:X}  Expect 0x{:X}".format(read_data[0], row[1]) )
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            #read data on MTP ADAPT CPLD SCAN HIGH BYTE
            rc = self.nic_read_mtp_adapt_cpld(mtp_adapt_scan_reg1, read_data)
            if not rc:
                errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            if read_data[0] != row[2]:
                errlist.append(" ERROR: MTP ADAPTER SCAN CHAIN DATA REG0:  READ 0x{:X}  Expect 0x{:X}".format(read_data[0], row[2]) )
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False 


        #FAN ON/OFF SIGNAL
        CPLDREG12H = 0x12
        MTPADAPTREG04H = 0x04
        rc = self.nic_read_cpld(CPLDREG12H, read_data)
        if not rc:
            errlist.append(" ERROR: nic_read_cpld Failed") 
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        cpld12h = read_data[0]

        state = [0, 1, 0]  #0 = OFF, 1 = ON
        for i in state:
            if i == 0:
                cpld12h = cpld12h & (~0x10)
            else:
                cpld12h = cpld12h | 0x10

            rc = self.nic_write_cpld(CPLDREG12H, cpld12h)
            if not rc: 
                errlist.append(" ERROR: nic_write_cpld Failed") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            rc = self.nic_read_mtp_adapt_cpld(MTPADAPTREG04H, read_data)
            if not rc: 
                errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False 
            if i == 0:
                if (read_data[0] & 0x04) != 0x00:
                    errlist.append(" ERROR: CPLD FAN ENABLE. EXPECT BIT2 OFF") 
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
            else:
                if (read_data[0] & 0x04) != 0x04:
                    errlist.append(" ERROR: CPLD FAN ENABLE EXPECT BIT2 ON") 
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

        #Check we are in high power mode
        if testhighpower > 0:
            rc = self.nic_naples25swm_high_power_mode_test(errlist)
            if not rc:
                return False
        return True

    def nic_naples25swm_high_power_mode_test(self, errlist):
        read_data = [0]

        rc = self.nic_read_mtp_adapt_cpld(0x01, read_data)
        if not rc: 
            errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if (read_data[0] & 0x08) != 0x08:
            errlist.append(" ERROR: 12V EDGE ENABLE. MTP ADAPTER REG1 EXPECT BIT3 ON") 
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        rc = self.nic_read_cpld_via_smbus(0x21, read_data)
        if not rc:
            errlist.append(" ERROR: nic_read_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if (read_data[0] & 0x02) != 0x02:
            errlist.append(" ERROR: 12V EDGE ENABLE. SWM CPLD REG21 EXPECT BIT1 ON (force high power mode)") 
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        rc = self.nic_read_cpld(0x01, read_data)
        if not rc:
            errlist.append(" ERROR: nic_read_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if (read_data[0] & 0x80) != 0x80:
            errlist.append(" ERROR: 12V EDGE ENABLE. SWM CPLD REG1 EXPECT BIT7 ON") 
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        rc = self.nic_read_mtp_adapt_cpld(0x00, read_data)
        if not rc: 
            errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        mtp_adapt_cpld_rev = read_data[0]

        rc = self.nic_read_mtp_adapt_cpld(0x04, read_data)
        if not rc: 
            errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False 

        if mtp_adapt_cpld_rev < 4:   #BIT IS INVERTED ON LOWER REV CPLD
            if (read_data[0] & 0x40) != 0x00:
                errlist.append(" ERROR: 12V EDGE ENABLE. MTP ADAPTER CPLD REG4 EXPECT BIT6 OFF") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
        else: 
            if (read_data[0] & 0x40) != 0x40:
                errlist.append(" ERROR: 12V EDGE ENABLE. MTP ADAPTER CPLD REG4 EXPECT BIT6 ON") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
        return True

    def nic_naples25swm_low_power_mode_test(self, errlist):
        read_data = [0]

        if not self.nic_read_mtp_adapt_cpld(0x01, read_data): 
            errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if (read_data[0] & 0x08) != 0x00:
            errlist.append(" ERROR: 12V EDGE ENABLE. MTP ADAPTER REG1 EXPECT BIT3 (MAIN POWER) OFF") 
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_read_cpld_via_smbus(0x21, read_data):
            errlist.append(" ERROR: nic_read_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if (read_data[0] & 0x02) != 0x00:
            errlist.append(" ERROR: 12V EDGE ENABLE. SWM CPLD REG21 EXPECT BIT1 OFF (force high power mode)") 
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_read_cpld(0x01, read_data):
            errlist.append(" ERROR: nic_read_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if (read_data[0] & 0x80) != 0x00:
            errlist.append(" ERROR: 12V EDGE ENABLE. SWM CPLD REG1 EXPECT BIT7 OFF (Host Power)") 
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if not self.nic_read_mtp_adapt_cpld(0x00, read_data): 
            errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        mtp_adapt_cpld_rev = read_data[0]

        if not self.nic_read_mtp_adapt_cpld(0x04, read_data): 
            errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False 

        if mtp_adapt_cpld_rev < 4:   #BIT IS INVERTED ON LOWER REV CPLD
            if (read_data[0] & 0x40) != 0x40:
                errlist.append(" ERROR: 12V EDGE ENABLE. MTP ADAPTER CPLD REG4 EXPECT BIT6 ON") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
        else: 
            if (read_data[0] & 0x40) != 0x00:
                errlist.append(" ERROR: 12V EDGE ENABLE. MTP ADAPTER CPLD REG4 EXPECT BIT6 OFF") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
        return True

    #Test some registers that are set via SPI (for example software revision registers), and are read via SMBUS
    def nic_naples25swm_cpld_reg_test(self, errlist):
        spi_read_data = [0]
        smb_read_data = [0]
        test_data = [0xAA, 0x55, 0x00]


        #0x34 - 0x37 SFP optics temperature, make sure they read the same on SPI & SMBUS side.  S/W periodically updates value, so cannot run custom data
        sfp_temp_limit_reg = [0x34, 0x35, 0x36, 0x37]
        for i in sfp_temp_limit_reg:   
            rc = self.nic_read_cpld(i, spi_read_data)
            if not rc:
                errlist.append(" ERROR: nic_read_cpld Failed")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            rc = self.nic_read_cpld_via_smbus(i, smb_read_data)
            if not rc: 
                errlist.append(" ERROR: nic_read_cpld_via_smbus FAILED")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False 
            if spi_read_data[0] != smb_read_data[0]:
                errlist.append(" ERRPR: CPLD REG 0x{%x}  SMB READ 0x{:X}  Expect 0x{:X}".format(i, smb_read_data[0], spi_read_data[0]) )
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False                 
         
        #0x38 - 0x39 System health indication
        #0x3A - 0x3D f/w version
        system_health_reg = [0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D]
        for i in system_health_reg:
            for j in test_data:
                rc = self.nic_write_cpld(i, j)
                if not rc: 
                    errlist.append(" ERROR: nic_write_cpld Failed") 
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                rc = self.nic_read_cpld(i, spi_read_data)
                if not rc:
                    errlist.append(" ERROR: nic_read_cpld Failed")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                rc = self.nic_read_cpld_via_smbus(i, smb_read_data)
                if not rc: 
                    errlist.append(" ERROR: nic_read_cpld_via_smbus FAILED")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False 
                if spi_read_data[0] != smb_read_data[0] != j:
                    errlist.append(" ERRPR: CPLD REG 0x{%x}  Expect 0x{:X}   SPI READ=0x{:X}  SMB READ 0x{:X}  ".format(i, j, smb_read_data[0], spi_read_data[0]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False 

        #SMB TO SPI (0xB, 0xC)
        smb_to_spi_reg = [0x0B, 0x0C]
        for i in smb_to_spi_reg:
            for j in test_data:
                rc = self.nic_write_cpld_via_smbus(i, j)
                if not rc: 
                    errlist.append(" ERROR: nic_write_cpld_via_smbus Failed") 
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                rc = self.nic_read_cpld(i, spi_read_data)
                if not rc:
                    errlist.append(" ERROR: nic_read_cpld Failed")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                if spi_read_data[0] != j:
                    errlist.append(" ERRPR: CPLD REG 0x{%x}  Expect 0x{:X}   SPI READ=0x{:X}".format(i, j, spi_read_data[0]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

        #SPI TO SMB (0xD, 0xE)
        spi_to_smb_reg = [0x0D, 0x0E]
        for i in spi_to_smb_reg:
            for j in test_data:
                rc = self.nic_write_cpld(i, j)
                if not rc: 
                    errlist.append(" ERROR: nic_write_cpld Failed") 
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                rc = self.nic_read_cpld_via_smbus(i, smb_read_data)
                if not rc: 
                    errlist.append(" ERROR: nic_read_cpld_via_smbus FAILED")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False 
                if smb_read_data[0] != j:
                    errlist.append(" ERRPR: CPLD REG 0x{%x}  Expect 0x{:X}   SMB READ 0x{:X}  ".format(i, j, smb_read_data[0]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False 

        return True

    def nic_naples25swm_mgmt_port_test(self, slot):
        ipaddr = libmfg_utils.get_nic_ip_addr(slot)
        cmd = MFG_DIAG_CMDS().MTP_NIC_PING_FMT.format(ipaddr)
        if not self.mtp_exec_cmd(cmd):
            return False
        match = re.findall(r"0% packet loss", self.nic_get_cmd_buf())
        if not match:
            print(" PING FAILED")
            return False
        print(" PING PASSED")
        return True

    #
    # Used for SWM and OCP MTP ADAPTER TO READ the ADAPTER CPLD
    #
    def nic_read_mtp_adapt_cpld(self, reg_addr, read_data):
        cmd = MFG_DIAG_CMDS().MTP_SMB_SEL_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MTP_RD_ALOM_CPLD_FMT.format(reg_addr, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False
        match = re.findall(r"data=(0x[0-9a-fA-F]+)", self.nic_get_cmd_buf())
        if not match:
            return False
        else:
            read_data[0] = int(match[0], 16)
        return True

    #
    # Used for SWM and OCP MTP ADAPTER TO READ the ADAPTER CPLD
    #
    def nic_write_mtp_adapt_cpld(self, reg_addr, write_data):
        cmd = MFG_DIAG_CMDS().MTP_SMB_SEL_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MTP_WR_ALOM_CPLD_FMT.format(reg_addr, write_data, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False
        match = re.findall(r"failed", self.nic_get_cmd_buf())
        if match:
            return False
        return True

    def nic_read_cpld_via_smbus(self, reg_addr, read_data):
        if self._mtp_type in (MTP_TYPE.CAPRI, MTP_TYPE.ELBA, MTP_TYPE.TURBO_ELBA):
            cmd = MFG_DIAG_CMDS().MTP_SMB_SEL_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd):
                return False

        cmd = MFG_DIAG_CMDS().MTP_SMB_RD_CPLD_FMT.format(reg_addr, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False

        match = re.findall(r"data=(0x[0-9a-fA-F]+)", self.nic_get_cmd_buf())
        if not match:
            return False
        else:
            read_data[0] = int(match[0], 16)
        return True

    def nic_write_cpld_via_smbus(self, reg_addr, write_data):
        if self._mtp_type in (MTP_TYPE.CAPRI, MTP_TYPE.ELBA, MTP_TYPE.TURBO_ELBA):
            cmd = MFG_DIAG_CMDS().MTP_SMB_SEL_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd):
                return False

        cmd = MFG_DIAG_CMDS().MTP_SMB_WR_CPLD_FMT.format(reg_addr, write_data, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False
        match = re.findall(r"failed", self.nic_get_cmd_buf())
        if match:
            return False
        return True


    def nic_naples25ocp_signal_test(self, errlist):
        adapt_read_data = [0]
        ocp_read_data = [0]

        rc = self.nic_write_cpld(0x1E, 0x1F)    #ENABLE IRQ    MASK=0x1F
        if not rc:
            errlist.append(" ERROR: nic_write_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        rc = self.nic_read_cpld(0x1F, ocp_read_data)    #MAKE SURE NO IRQ SET ON OCP
        if not rc:
            errlist.append(" ERROR: nic_read_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if ocp_read_data[0] != 0x00 :
            errlist.append(" ERROR: OCP CPLD REG 0x1F (IRQ REG):  READ 0x{:X}  Expect 0x00".format(ocp_read_data[0]) )
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        #ADAPTER BIT TO READ (SIGNAL SHOULD BE HIGH AND DOES NOT TOGGLE)
        data = [[0x40, 0x08], \
                [0x42, 0x02], \
                [0x42, 0x04], \
                [0x42, 0x08]]
        for row in data:
            rc = self.nic_read_mtp_adapt_cpld(row[0], adapt_read_data)
            if not rc:
                errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            if (adapt_read_data[0] & row[1]) != row[1]:
                errlist.append(" ERROR: MTP ADAPTER CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} Set".format(row[0], adapt_read_data[0], row[1]) )
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False


        #OCP BIT TO READ (SIGNAL SHOULD BE HIGH AND DOES NOT TOGGLE)
        data = [[0x40, 0x01], \
                [0x41, 0x08]]
        for row in data:
            rc = self.nic_read_cpld(row[0], ocp_read_data)
            if not rc:
                errlist.append(" ERROR: nic_read_cpld Failed") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            if (ocp_read_data[0] & row[1]) != row[1]:
                errlist.append(" ERROR: OCP CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} Set".format(row[0], ocp_read_data[0], row[1]) )
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

        #ADAPTER REG/BIT TO SET/ DEFAULT STATE ->    OCP REG/BIT TO READ
        data = [[0x40, 0x02, True,  0x40, 0x02], \
                [0x40, 0x04, True,  0x40, 0x04], \
                [0x40, 0x40, False, 0x42, 0x01], \
                [0x40, 0x80, False, 0x42, 0x02], \
                [0x41, 0x01, False, 0x41, 0x01], \
                [0x41, 0x02, False, 0x41, 0x02], \
                [0x41, 0x04, False, 0x41, 0x04], \
                [0x41, 0x10, False, 0x41, 0x10], \
                [0x41, 0x20, False, 0x41, 0x20], \
                [0x41, 0x40, False, 0x41, 0x40]]

        for row in data:
            rc = self.nic_read_mtp_adapt_cpld(row[0], adapt_read_data)
            if not rc:
                errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            rc = self.nic_read_cpld(row[3], ocp_read_data)
            if not rc:
                errlist.append(" ERROR: nic_read_cpld Failed") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            if row[2] == True:  # Should be high by default
                if (adapt_read_data[0] & row[1]) != row[1]:
                    errlist.append(" ERROR: MTP ADAPTER CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} SET".format(row[0], adapt_read_data[0], row[1]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

                if (ocp_read_data[0] & row[4]) != row[4]:
                    errlist.append(" ERROR: OCP CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} SET".format(row[3], ocp_read_data[0], row[4]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

                #Clear BIT
                adapt_read_data[0] = adapt_read_data[0] & (~row[1])
                rc = self.nic_write_mtp_adapt_cpld(row[0], adapt_read_data[0])
                if not rc:
                    errlist.append(" ERROR: nic_write_mtp_adapt_cpld Failed")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                #Check OCP CPLD
                rc = self.nic_read_cpld(row[3], ocp_read_data)
                if not rc:
                    errlist.append(" ERROR: nic_read_cpld Failed") 
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                if (ocp_read_data[0] & row[4]) == row[4]:
                    errlist.append(" ERROR: OCP CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} Clear".format(row[3], ocp_read_data[0], row[4]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

                #Set BIT
                adapt_read_data[0] = adapt_read_data[0] | row[1]
                rc = self.nic_write_mtp_adapt_cpld(row[0], adapt_read_data[0])
                if not rc:
                    errlist.append(" ERROR: nic_write_mtp_adapt_cpld Failed")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                #Check OCP CPLD
                rc = self.nic_read_cpld(row[3], ocp_read_data)
                if not rc:
                    errlist.append(" ERROR: nic_read_cpld Failed") 
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                if (ocp_read_data[0] & row[4]) != row[4]:
                    errlist.append(" ERROR: OCP CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} SET".format(row[3], ocp_read_data[0], row[4]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

            else:  # Should be low by default
                if (adapt_read_data[0] & row[1]) == row[1]:
                    errlist.append(" ERROR: MTP ADAPTER CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} CLEAR".format(row[0], adapt_read_data[0], row[1]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

                if (ocp_read_data[0] & row[4]) == row[4]:
                    errlist.append(" ERROR: OCP CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} CLEAR".format(row[3], ocp_read_data[0], row[4]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

                #SET BIT
                adapt_read_data[0] = adapt_read_data[0] | row[1]
                rc = self.nic_write_mtp_adapt_cpld(row[0], adapt_read_data[0])
                if not rc:
                    errlist.append(" ERROR: nic_write_mtp_adapt_cpld Failed")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                #Check OCP CPLD
                rc = self.nic_read_cpld(row[3], ocp_read_data)
                if not rc:
                    errlist.append(" ERROR: nic_read_cpld Failed") 
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                if (ocp_read_data[0] & row[4]) != row[4]:
                    errlist.append(" ERROR: OCP CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} SET".format(row[3], ocp_read_data[0], row[4]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

                #CLEAR BIT
                adapt_read_data[0] = adapt_read_data[0] & (~row[1])
                rc = self.nic_write_mtp_adapt_cpld(row[0], adapt_read_data[0])
                if not rc:
                    errlist.append(" ERROR: nic_write_mtp_adapt_cpld Failed")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                #Check OCP CPLD
                rc = self.nic_read_cpld(row[3], ocp_read_data)
                if not rc:
                    errlist.append(" ERROR: nic_read_cpld Failed") 
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                if (ocp_read_data[0] & row[4]) == row[4]:
                    errlist.append(" ERROR: OCP CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} CLEAR".format(row[3], ocp_read_data[0], row[4]) )
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

        #Check OCP CPLD for MAIN POWER ON, MAIN POWER OFF, PWRBRK_L IRQ SET
        #These bits were toggled in the test above
        rc = self.nic_read_cpld(0x1F, ocp_read_data)    
        if not rc:
            errlist.append(" ERROR: nic_write_mtp_adapt_cpld Failed")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        if ocp_read_data[0] != 0x13 :
            errlist.append(" ERROR: OCP CPLD REG 0x1F (IRQ REG):  READ 0x{:X}  Expect 0x11".format(ocp_read_data[0]) )
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        #TEST SCAN CHAIN
        #REG 0x43 BIT0 & BIT5 & BIT6 SHOULD BE IGNORED.  BIT1,2,3,4,6 ARE ALWAYS HIGH.  BIT7 ALWAYS LOW
        #REG 0x44 ALL BITS CAN BE SET HIGH OR LOW
        scan_chain_reg0_mask = 0x9E
        scan_chain_reg0_exp  = 0x1E
        data = [[0x44, 0xFF, 0x45, 0xFF], \
                [0x44, 0x00, 0x45, 0x00], \
                [0x44, 0xAA, 0x45, 0xAA], \
                [0x44, 0x55, 0x45, 0x55], \
                [0x44, 0x01, 0x45, 0x01], \
                [0x44, 0x80, 0x45, 0x80]]

        for row in data:    
            # Write Scan Chain Reg 1     
            rc = self.nic_write_cpld(row[0], row[1])    
            if not rc:
                errlist.append(" ERROR: nic_write_cpld Failed")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            # Initiate a scan chain
            rc = self.nic_write_mtp_adapt_cpld(0x43, 0x01)  
            if not rc:
                errlist.append(" ERROR: nic_write_mtp_adapt_cpld Failed")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            # Scan Chain Reg 0
            rc = self.nic_read_mtp_adapt_cpld(0x44, adapt_read_data)
            if not rc:
                errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            if (adapt_read_data[0] & scan_chain_reg0_mask) != scan_chain_reg0_exp:
                errlist.append(" ERROR: MTP ADAPTER CPLD REG 0x44:  READ 0x{:X}  Mask=0x{:X} Expect 0x{:X}".format(adapt_read_data[0], scan_chain_reg0_mask, scan_chain_reg0_exp) )
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            # Scan Chain Reg 1
            rc = self.nic_read_mtp_adapt_cpld(0x45, adapt_read_data)
            if not rc:
                errlist.append(" ERROR: nic_read_mtp_adapt_cpld Failed") 
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            if (adapt_read_data[0] & row[3]) != row[3]:
                errlist.append(" ERROR: MTP ADAPTER CPLD REG 0x{:X}:  READ 0x{:X}  Expect 0x{:X}".format(row[2], adapt_read_data[0], row[3]) )
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

        #Test OCP Slot_ID[] Pins
        data = [[0x40, 0x3F, 0x50], \
                [0x40, 0x7F, 0x52], \
                [0x40, 0xBF, 0x54], \
                [0x40, 0xFF, 0x56], \
                [0x40, 0x3F, 0x50]]

        for row in data:
            rc = self.nic_write_mtp_adapt_cpld(row[0], row[1])  
            if not rc:
                errlist.append(" ERROR: nic_write_mtp_adapt_cpld Failed")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False


            cmd = "turn_on_hub.sh {:d}".format(self._slot+1)
            if not self.mtp_exec_cmd(cmd):
                return False

            cmd = "i2cset -y 0 0x{:X} 0x00 0x00".format(row[2])
            if not self.mtp_exec_cmd(cmd):
                return False
            
            match = re.findall(r"Error", self.nic_get_cmd_buf())
            if match:
                errlist.append(" ERROR: OCP Signal Slot_ID[] test failed. MTP ADAPTER REG 0x{:X} = 0x{:X}  I2C ACCESS TO EEPROM FAILED.  I2CSET DID NOT RETURN 0".format(row[0], row[1]) )
                return False
            
        return True

    def nic_fix_vrm(self):
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS().ORTANO2_VRM_FIX_FMT)
        if "Ortano2 VRM fix done" not in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_fix_vrm_oc(self):
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS().ORTANO2_VRM_FIX_OC_FMT)
        if "FIX O2 VRM OC DONE" not in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_erase_board_config_ssh(self):

        before_erase = self.nic_get_info(MFG_DIAG_CMDS().GET_BOARD_CONFIG_FMT)
        if not before_erase:
            self.nic_set_err_msg("Unable to get board config")
            return False

        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS().ERASE_BOARD_CONFIG_FMT)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to erase board config")
            return False

        after_release = self.nic_get_info(MFG_DIAG_CMDS().GET_BOARD_CONFIG_FMT)
        if not after_release:
            return False

        if "u-boot sets to board defaults" not in after_release and "Board config not set" not in after_release:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_set_board_config(self, preset_config):
        """
         Quick Start guide
         https://docs.google.com/document/d/1Vu9DzkR6PZmdeqFdQvBkJrxv6yMDcQq3GU5_4YEAxeY/preview

        # board_config -l
        Config     Core       Stage       CPU
           1    833333333  1137000000  3000000000
           2    833333333  1262000000  3000000000
           3    833333333  1500000000  3000000000
           4   1033000000  1137000000  3000000000
           5   1033000000  1262000000  3000000000
           6   1033000000  1500000000  3000000000
           7   1100000000  1262000000  3000000000
           8   1100000000  1500000000  3000000000
           9    833333333  1137000000  2000000000
          10    833333333  1262000000  2000000000
          11    833333333  1500000000  2000000000
          12   1033000000  1137000000  2000000000
          13   1033000000  1262000000  2000000000
          14   1033000000  1500000000  2000000000
          15   1100000000  1262000000  2000000000
          16   1100000000  1500000000  2000000000
          17   1033000000  1364000000  3000000000
          18    525000000   568000000  2000000000
          19    416666666   568000000  2000000000
          20    525000000   568000000  3000000000
          21    966666666  1262000000  3000000000

        """
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS().GET_BOARD_CONFIG_FMT)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to get board config")
            return False
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS().SET_BOARD_CONFIG_FMT.format(preset_config))
        if not cmd_buf:
            self.nic_set_err_msg("Unable to set board config")
            return False
        if "Mode successfully set" in cmd_buf or "Config successfully set" in cmd_buf:
            pass
        else:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS().GET_BOARD_CONFIG_FMT)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to get updated board config")
            return False

        if "cfg{:s}".format(str(preset_config)) in cmd_buf:
            pass
        else:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_assign_board_id(self, boardId=None, readOnly=False):
        """
        assign passed in Board ID String to this board by utility board_config
        example:
        # assign, board_config -B 0x03610001
        # read and verify, board_config -b, got 0x03610001
        #-------------------------------------------------
        # since board_config -b may report the board_id from FRU after we erase board_cfg and board_id
        # so SW team suggest using board_config -r to read board_id
        """

        if boardId is None:
            self.nic_set_err_msg("Please Provide Board ID")
            return False
        if not isinstance(boardId, str):
            self.nic_set_err_msg("Please Specify Board ID with String Format")
            return False

        if not readOnly:
            cmd_buf = self.nic_get_info(MFG_DIAG_CMDS().ASSIGN_BOARD_ID_FMT.format(boardId))
            if not cmd_buf:
                self.nic_set_err_msg("Assign Board ID Command 'board_config -B' Failed")
                return False
            # test string "Config successfully set" in command return buffer
            if "successfullyset" not in cmd_buf.replace(" ", "").lower():
                self.nic_set_err_msg("Assign Board ID NOT Success")
                self.nic_set_err_msg(cmd_buf)
                return False

        # Read Board ID back and compare
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS().GET_BOARD_CONFIG_FMT)
        if not cmd_buf:
            self.nic_set_err_msg("Read Board ID Command 'board_config -r' Failed")
            return False
        if boardId.lower() not in cmd_buf.lower():
            self.nic_set_err_msg("Read Back and Compare Board ID Failed")
            self.nic_set_err_msg(cmd_buf)
            return False

        return True

    def zephyr_assign_board_id_and_pci_subsystemid(self, boardId=None, pciSubsystemId=None):
        """
        assign passed in Board ID String and pci subsystem ID to this board by zephyr utility board_config and write subcommand
        uart:~$ board_config        
        board_config - Board config 
            Subcommands:                
            dump       :              
            erase      :              
            list_freq  :              
            list_pcie  :              
            write      :              
            board_id   :
        uart:~$ board_config write                                  
        usage: board_config write [opts]                            
                -w NUM   - Write board config                       
                -m NUM   - Write manufacturing default              
                -d       - Set to manufacturing default             
                -c [0|1] - Console to 3-pin header                  
                -k [0|1] - Enforce signature check                  
                -K name  - Public Key name                          
                -G [0|1] - Boot to goldfw on STOP                   
                -F [0|1] - No host visible interface in goldfw      
                -O [0|1] - Enable OOB in goldfw                     
                -B ID    - Board ID assigned to this board          
                -v VENID - PCI Vendor ID assigned to this board     
                -s ID    - PCI Subvendor ID assigned to this board  
                -S ID    - PCI Subsystem ID assigned to this board  
                -p       - PCI port cfg preset 16gt value           
                -T [0|1] - PCI port delay linkup on boot            
                -t [0|1] - PCI port delay linkup on internal boot   
                -P NUM   - Select PCIe config, 0 to disable         
                -M [0|1] - Diag mode with goldfw, 0 to disable      
                -x [0|1] - Enable secure mode                       
                -a [0|1] - Enable CPLD access                       
                -i [0|1] - Enable AINIC mode                        
                [0|1] - 0:disabled(default)  1:enable                           
        # example:
        # write, board_config write -B 0x04640002
        #        board_config write -S 0x5201
        # read and verify, board_config dump
        """

        if boardId is None:
            self.nic_set_err_msg("Please Provide Board ID")
            return False
        if not isinstance(boardId, str):
            self.nic_set_err_msg("Please Specify Board ID with String Format")
            return False
        if pciSubsystemId and not isinstance(pciSubsystemId, str):
            self.nic_set_err_msg("Please Specify PCI Subsystem ID with String Format")
            return False

        opts = '-B {:s}'.format(boardId)
        cmd = MFG_DIAG_CMDS().ZEPHYR_BOARD_CONFIG_WRITE_FMT.format(opts)
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            time.sleep(27)
            if not self.nic_exec_cmd_from_zephyr_console(cmd):
                self.nic_set_err_msg("Zephyr Write Board ID Command '{:s}' Failed Even With Retry".format(cmd))
                return False
        cmd_buf = self.nic_get_cmd_buf()
        cmd_buf = re.sub(r'\r\n', '\n', cmd_buf)
        cmd_buf = re.sub(r'\r', '', cmd_buf)
        cmd_buf = re.sub(r'Boot success set\n+', '', cmd_buf)
        cmd_buf = re.sub(r'\[\d{2}:\d{2}:\d{2}\.\d{3},\d{3}\].*\n+', '', cmd_buf)
        # test string "Config successfully set" in command return buffer
        if "successfullyset" not in cmd_buf.replace(" ", "").lower():
            self.nic_set_err_msg("Zephyr Write Board ID NOT Success")
            self.nic_set_err_msg(cmd_buf)
            return False

        if pciSubsystemId:
            opts = '-S {:s}'.format(pciSubsystemId)
            cmd = MFG_DIAG_CMDS().ZEPHYR_BOARD_CONFIG_WRITE_FMT.format(opts)
            if not self.nic_exec_cmd_from_zephyr_console(cmd):
                time.sleep(27)
                if not self.nic_exec_cmd_from_zephyr_console(cmd):
                    self.nic_set_err_msg("Zephyr Write PCI Subsystem ID Command '{:s}' Failed Even With Retry".format(cmd))
                    return False
            cmd_buf = self.nic_get_cmd_buf()
            cmd_buf = re.sub(r'\r\n', '\n', cmd_buf)
            cmd_buf = re.sub(r'\r', '', cmd_buf)
            cmd_buf = re.sub(r'Boot success set\n+', '', cmd_buf)
            cmd_buf = re.sub(r'\[\d{2}:\d{2}:\d{2}\.\d{3},\d{3}\].*\n+', '', cmd_buf)
            # test string "Config successfully set" in command return buffer
            if "successfullyset" not in cmd_buf.replace(" ", "").lower():
                self.nic_set_err_msg("Zephyr Write Board PCI Subsystem ID NOT Success")
                self.nic_set_err_msg(cmd_buf)
                return False

        # reboot
        cmd = "kernel reboot cold"
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            self.nic_set_err_msg("Zephyr command '{:s}' Failed".format(cmd))
            return False
        time.sleep(60)

        # Dump Board ID back and compare
        if not self.nic_exec_cmd_from_zephyr_console(MFG_DIAG_CMDS().ZEPHYR_BOARD_CONFIG_DUMP_FMT):
            time.sleep(27)
            if not self.nic_exec_cmd_from_zephyr_console(MFG_DIAG_CMDS().ZEPHYR_BOARD_CONFIG_DUMP_FMT):
                self.nic_set_err_msg("Zephyr Borad Config Dump Command '{:s}' Failed Even with Retry".format(MFG_DIAG_CMDS().ZEPHYR_BOARD_CONFIG_DUMP_FMT))
                return False
        cmd_buf = self.nic_get_cmd_buf()
        if boardId.lower() not in cmd_buf.lower():
            # Board ID not found in "board_config dump" command response
            # may because that there are ANSI escape code that resets text formatting (colors, bold, etc.) in terminal output
            # retry with "board_config board_id" command
            if not self.nic_exec_cmd_from_zephyr_console(MFG_DIAG_CMDS().ZEPHYR_BOARD_ID_READ_FMT):
                time.sleep(27)
                if not self.nic_exec_cmd_from_zephyr_console(MFG_DIAG_CMDS().ZEPHYR_BOARD_ID_READ_FMT):
                    self.nic_set_err_msg("Zephyr Borad ID READ Command '{:s}' Failed Even with Retry".format(MFG_DIAG_CMDS().ZEPHYR_BOARD_ID_READ_FMT))
                    return False
            cmd_buf = self.nic_get_cmd_buf()

        if boardId.lower() not in cmd_buf.lower():
            self.nic_set_err_msg("Zephr Read Back and Compare Board ID Failed")
            self.nic_set_err_msg(cmd_buf)
            return False

        # show fru dump
        cmd = "show frudump parse"
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            time.sleep(27)
            if not self.nic_exec_cmd_from_zephyr_console(cmd):
                self.nic_set_err_msg("Zephyr command '{:s}' Failed Even with Retry".format(cmd))
                return False
        return True

    def zephyr_debug_update_firmware(self, bootfw='mainfwa', bootfw_verify=True):
        """
        set zephyr bootfw by zephyr shell command 'debug update firmware --next-boot mainfwa'
        the command usage:
                debug update firmware --next-boot-image <mainfwa|mainfwb|goldfw>
        # example:
            uart:~$ debug update firmware --next-boot mainfwa
            Next boot firmware set to mainfwa"
            uart:~$  debug update firmware --next-boot goldfw
            Next boot firmware set to goldfw
            uart:~$  debug update firmware --next-boot mainfwb
            Next boot firmware set to mainfwb"
        """
        set2booting_map = {
            'mainfwa': ('extosa', 'mainfwa'),
            'mainfwb': ('extosb', 'mainfwb'),
            'goldfw': ('goldfw', 'gold'),
        }

        # set fwselection
        cmd = MFG_DIAG_CMDS().ZEPHYR_FW_SELECT_FMT.format(bootfw)
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            time.sleep(27)
            if not self.nic_exec_cmd_from_zephyr_console(cmd):
                self.nic_set_err_msg("Zephyr fwselect Command '{:s}' Failed Even with Retry".format(cmd))
                return False
        cmd_buf = self.zephyr_output_sanitize(self.nic_get_cmd_buf())
        if bootfw not in cmd_buf.lower():
            self.nic_set_err_msg("debug update firmware next-boot {:s} Failed".format(bootfw))
            self.nic_set_err_msg(cmd_buf)
            return False
        # verify
        cmd = "kernel reboot cold"
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            self.nic_set_err_msg("Zephyr command '{:s}' Failed".format(cmd))
            return False
        cmd_buf = self.nic_get_cmd_buf()
        if "## Booting {:s} image".lower().format(set2booting_map[bootfw][0]) not in cmd_buf.lower():
            self.nic_set_err_msg("Zephr did not boot to specified selection")
            self.nic_set_err_msg(cmd_buf)
            return False
        time.sleep(60)
        # show version
        if bootfw_verify:
            cmd = MFG_DIAG_CMDS().ZEPHYR_SHOW_VERSION_FMT
            if not self.nic_exec_cmd_from_zephyr_console(cmd):
                time.sleep(27)
                if not self.nic_exec_cmd_from_zephyr_console(cmd):
                    self.nic_set_err_msg("Zephyr show version Command '{:s}' Failed Even with Retry".format(cmd))
                    return False
            cmd_buf = self.zephyr_output_sanitize(self.nic_get_cmd_buf())
            match = re.findall(r"Current\sfirmware\s+:\s({:s})".format(set2booting_map[bootfw][1]), cmd_buf)
            if not match:
                self.nic_set_err_msg("Zephr did not boot to {:s}".format(bootfw))
                self.nic_set_err_msg(cmd_buf)
                return False

        return True

    def zephyr_output_sanitize(self, input_str):
        '''
        remove carriage return. new line and terminal color code
        '''

        output_str = re.sub(r'\r\n', '\n', input_str)
        output_str = re.sub(r'\r', '', output_str)
        output_str = re.sub(r'\[\d{2}:\d{2}:\d{2}\.\d{3},\d{3}\].*\n+', '', output_str)
        return output_str

    def uc_zephyr_cpld_update(self, cpld_img, partition='0'):
        """
        update CPLD through micro controller zpher shell cpld command
            Subcommands:
            interface  : (debug) Show interface details
            id         : (debug) Read device ID
            cfgen      : (debug) Enable config mode - non-debug commands may disable again!
            cfgdis     : (debug) Disable config mode
            status0    : (debug) Read status reg 0
            status1    : (debug) Read status reg 1
            feabits    : (debug) Read feature bits
            sector     : (debug) <n> Select sector and reset address
            read       : (debug) Read next 16-byte page
            erase      : (debug) <n> Erase sector
            crc        : <0|1> Show CRC32 of CFG0 or CFG1
            load_buf   : <0|1> Load CFG0 or CFG1 into local buffer
            crc_buf    : Show CRC of local buffer
            prog_buf   : <0|1> Program CFG0 or CFG1 from local buffer
            refresh    : Reboot CPLD via 'Refresh' config interface command
            rcr        : <addr> Read common register (hex args)
            wcr        : <addr> <byte> Write common register (hex args)
            op         : <byte> [<byte>...] Raw reg interface SPI op (hex args)
        """

        partition = partition.lower()
        support_partitions = ("0", "1")
        if partition not in support_partitions:
            self.nic_set_err_msg("Program partition {:s} not support yet, so far only support {:s}".format(partition, str(support_partitions)))
            return False

        # copy cpld image to microncontroller buffer
        cmd = "{:s} -s {:d} -u {:s}".format(MFG_DIAG_CMDS().PANAREA_SUC_USB_TOOL, self._slot+1, cpld_img)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("Upload CPLD image to device Command '{:s}' Failed".format(cmd))
            return False
        cmd_buf = self.nic_get_cmd_buf()
        sanitized_cmd_buf = self.zephyr_output_sanitize(cmd_buf)
        if "No such file or directory".lower() in sanitized_cmd_buf.lower() or "No suitable USB devices found".lower() in  sanitized_cmd_buf.lower() or "Uploading: 100%".lower() not in sanitized_cmd_buf.lower():
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False
        match = re.findall(r'Image\s+CRC\s+=\s+0x([a-fA-F0-9]+)', sanitized_cmd_buf)
        if not match:
            self.nic_set_err_msg("Faield to parse command buffer:")
            self.nic_set_err_msg(cmd_buf)
            return False
        image_crc = match[0]

        # calculate buffer crc befor program
        cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_CPLD_CRC_BUF.format(partition)
        if not self.nic_exec_cmd_from_suc_console1(cmd):
            self.nic_set_err_msg("Zephyr CPLD Command '{:s}' Failed".format(cmd))
            return False
        cmd_buf = self.nic_get_cmd_buf()
        sanitized_cmd_buf = self.zephyr_output_sanitize(cmd_buf)
        match = re.findall(r'CRC32\s+of\s+image\s+buffer\s+=\s+0x([a-fA-F0-9]+)', sanitized_cmd_buf)
        if not match:
            self.nic_set_err_msg("Faield to parse command buffer:")
            self.nic_set_err_msg(cmd_buf)
            return False
        crc_before_prog = match[0]
        if crc_before_prog != image_crc:
            self.nic_set_err_msg("CRC verify failed,  image crc:{} vs buffer crc:{}.".format(image_crc, crc_before_prog))
            return False

        # program cpld partition
        cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_CPLD_PROG_BUF.format(partition)
        if not self.nic_exec_cmd_from_suc_console1(cmd):
            self.nic_set_err_msg("Zephyr CPLD Command '{:s}' Failed".format(cmd))
            return False
        cmd_buf = self.nic_get_cmd_buf()
        sanitized_cmd_buf = self.zephyr_output_sanitize(cmd_buf)
        if ("Writing CFG{:s}...".format(partition)).lower() not in sanitized_cmd_buf.lower() or "Done!".lower() not in sanitized_cmd_buf.lower():
            self.nic_set_err_msg("Zephyr CPLD program {:s} Failed".format(partition))
            self.nic_set_err_msg(cmd_buf)
            return False

        # calculate partition crc and verify
        partition_number = partition.replace('cfg', '')
        cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_CPLD_CRC.format(partition)
        if not self.nic_exec_cmd_from_suc_console1(cmd):
            self.nic_set_err_msg("Zephyr CPLD Command '{:s}' Failed".format(cmd))
            return False
        cmd_buf = self.nic_get_cmd_buf()
        sanitized_cmd_buf = self.zephyr_output_sanitize(cmd_buf)
        match = re.findall(r'CRC32\s+of\s+sector\s+' + partition_number + r'\s+=\s+0x([a-fA-F0-9]+)', sanitized_cmd_buf)
        if not match:
            self.nic_set_err_msg("Faield to parse command buffer:")
            self.nic_set_err_msg(cmd_buf)
            return False
        crc_after_prog = match[0]
        if crc_before_prog != crc_before_prog:
            self.nic_set_err_msg("CRC verify failed, buffer crc:{} vs flash partion crc:{}.".format(crc_before_prog, crc_after_prog))
            return False

        return True

    def uc_zephyr_hwinfo_devid(self):
        """
        execute hwinfo devid subcomand in zeohyr shell, parse and return devid
        uart:~$ hwinfo
        hwinfo - HWINFO commands
        Subcommands:
            devid        : Show device id
            deveui64     : Show device eui64
            reset_cause  : Reset cause commands
        """

        cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_HWINFO_DEVID
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            self.nic_set_err_msg("Zephyr Hwinfo Command '{:s}' Failed".format(cmd))
            return False
        cmd_buf = self.nic_get_cmd_buf()
        sanitized_cmd_buf = self.zephyr_output_sanitize(cmd_buf)
        match = re.findall(r'ID:\s+0x([a-fA-F0-9]+)', sanitized_cmd_buf)
        if not match:
            self.nic_set_err_msg("Faield to parse command buffer of command {:s}".format(cmd))
            self.nic_set_err_msg(cmd_buf)
            return False
        devid = match[0]
        return devid

    def zephyr_vulcano_version_check(self, expected_soc_ver,  expected_soc_timestamp=None, cpld_ver=None):
        """
        execute vulcano zephyr shell 'show version' command, verify the Build time and CPLD version
        command example:
            vulcano:~$ show version
            SUC-firmware              : mainfwb
            Suc-boot                  : 0.0.1+dummy
            Suc-app                   : 0.2.7+commit.2f241db9b99e
            CPLD:                     : 1.2
            Soc-firmware              : mainfwb
            Firmware version          : 1.125.0-a-49
            Firmware build time       : Jan  1 2026 06:29:55
            Build tag                 : 1.XX.0-C-8-50282-g97c6dd2cc49c
            Pipeline                  : rudra
            P4 program                : pulsar
        """

        cmd = MFG_DIAG_CMDS().ZEPHYR_SHOW_VERSION_FMT
        if not self.nic_exec_cmd_from_soc_console(cmd):
            self.nic_set_err_msg("Vulcano show version Command '{:s}' Failed".format(cmd))
            return False

        cmd_buf = self.nic_get_cmd_buf()
        sanitized_cmd_buf = self.zephyr_output_sanitize(cmd_buf)
        current_soc_version = ""
        current_soc_build_time = ""
        current_cpld_ver = ""
        for line in sanitized_cmd_buf.splitlines():
            if "Firmware version" in line:
                current_soc_version = line.split(":", 1)[1].strip()
            if "Firmware build time" in line:
                current_soc_build_time = line.split(":", 1)[1].strip()
            if "CPLD:" in line:
                current_cpld_ver = line.split(":")[2].strip()

        if expected_soc_ver:
            if expected_soc_ver.lower() not in current_soc_version.lower():
                self.nic_set_err_msg("SOC version :{:s} not in version command output {:s}".format(expected_soc_timestamp, sanitized_cmd_buf))
                return False
        if expected_soc_timestamp:
            if expected_soc_timestamp.lower() not in current_soc_build_time.lower():
                self.nic_set_err_msg("SOC timestamp:{:s} not in version command output {:s}".format(expected_soc_timestamp, sanitized_cmd_buf))
                return False
        if cpld_ver:
            if cpld_ver.lower() not in current_cpld_ver.lower():
                self.nic_set_err_msg("SOC CPLD version:{:s} not in version command output {:s}".format(cpld_ver, sanitized_cmd_buf))
                return False
        return True

    def vulcano_shell_fru_dump_check(self,):
        """
        execute vulcano shell fru dump command, verify the contents with eeutil -disp
        command example:
            vulcano:~$ frudump raw  ==> for log only
            vulcano:~$ frudump parsed   ==> for contents compare
        """

        # read FRU from eeutil as reference
        if not self.nic_read_fru(smb_fru=True, dev="fru"):
            self.nic_set_err_msg("Display FRU From eeutil failed")
            return False
        eeutil_fru = self.zephyr_output_sanitize(self.nic_get_cmd_buf())

        # suc dump fru raw for log purpose only
        cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_FRUDUMP_RAW
        if not self.nic_exec_cmd_from_soc_console(cmd):
            self.nic_set_err_msg("SOC frudump Command '{:s}' Failed".format(cmd))
            return False

        # suc dump fru parsed
        cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_FRUDUMP_PARSED
        if not self.nic_exec_cmd_from_soc_console(cmd):
            self.nic_set_err_msg("SOC frudump Command '{:s}' Failed".format(cmd))
            return False
        soc_fru = self.zephyr_output_sanitize(self.nic_get_cmd_buf())

        # parse fru data and compare
        soc_fru_dict = {}
        for line in soc_fru.splitlines():
            if ": " not in line:
                continue
            k, v = re.split(r'\s*:\s+', line)
            if k == "serial-number":
                soc_fru_dict["serial-number"] = v.upper()
            if k == "part-number":
                soc_fru_dict["part-number"] = v.upper()
            if k == "board-id":
                soc_fru_dict["board-id"] = v.upper()
            if k == "product-name":
                soc_fru_dict["product-name"] = v.upper()

        eeutil_fru_dict = {}
        for line in eeutil_fru.splitlines():
            found = re.findall(r'Serial Number\s{5,}(\w+)', line)
            if found:
                eeutil_fru_dict["serial-number"] = found[0].upper()
            found = re.findall(r'Part Number\s{5,}([0-9\-]+)', line)
            if found:
                eeutil_fru_dict["part-number"] = found[0].upper()
            found = re.findall(r'Board ID\s{5,}(\w+)', line)
            if found:
                eeutil_fru_dict["board-id"] = found[0].upper()
            found = re.findall(r'Product Name\s{5,}(.*)', line)
            if found:
                eeutil_fru_dict["product-name"] = found[0].upper()

        # compare
        compare_pass = True
        for k, v in soc_fru_dict.items():
            v1 = eeutil_fru_dict.get(k,"")
            if v != v1:
                self.nic_set_err_msg("{:s} from soc is {:s}, not match the value {:s} from eeutil".format(k, v, v1))
                compare_pass = False
        return compare_pass

    def uc_zephyr_version_check(self, nic_type=None, board_id=None, expected_suc_timestamp=None, cpld_ver=None, stage=None):
        """
        execute suc zephyr shell version command, verify the board ID, board name, Suc Build time and CPLD version
        command example:
            uart:~$ version
            Board ID: 0x05700002
            SuC build type: Mortaro P1
            SuC build time: 2025-12-22 10:14:59
            SuC panel: A
            SUC_BOOT: 0.0.1+dummy
            SUC_RUNTIME: 0.2.6+commit.304312b46127
            SOC_CFGFPGA: 1.2
        """

        cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_VERSION
        if not self.nic_exec_cmd_from_suc_console1(cmd):
            self.nic_set_err_msg("SUC version Command '{:s}' Failed".format(cmd))
            return False

        cmd_buf = self.nic_get_cmd_buf()
        sanitized_cmd_buf = self.zephyr_output_sanitize(cmd_buf)
        current_board_id = ""
        current_board_name = ""
        current_suc_build_time = ""
        current_cpld_ver = ""
        for line in sanitized_cmd_buf.splitlines():
            if "Board ID" in line:
                current_board_id = line.split(":", 1)[1].strip()
            if "SuC build type" in line:
                current_board_name = line.split(":", 1)[1].strip()
            if "SuC build time" in line:
                current_suc_build_time = line.split(":", 1)[1].strip()
            if "SOC_CFGFPGA" in line:
                current_cpld_ver = line.split(":", 1)[1].strip()

        if board_id:
            if board_id.lower() not in current_board_id.lower():
                self.nic_set_err_msg("Board ID:{:s} not in version command output {:s}".format(board_id, sanitized_cmd_buf))
                return False
        if expected_suc_timestamp:
            if expected_suc_timestamp.lower() not in current_suc_build_time.lower():
                self.nic_set_err_msg("Suc version timestamp:{:s} not in version command output {:s}".format(expected_suc_timestamp, sanitized_cmd_buf))
                return False
        # # skip CPLD check here, since the cpld version from version command is the CPLD running version, its the cpld version form flash bianray.
        # if cpld_ver:
        #     if cpld_ver.lower() not in current_cpld_ver.lower():
        #         self.nic_set_err_msg("CPLD version:{:s} not in version command output {:s}".format(cpld_ver, sanitized_cmd_buf))
        #         return False
        if nic_type:
            if nic_type.lower() not in current_board_name.lower():
                self.nic_set_err_msg("Board Name:{:s} not in version command output {:s}".format(nic_type, sanitized_cmd_buf))
                return False
        return True

    def suc_fru_dump_check(self,):
        """
        execute suc shell fru dump command, verify the contents with eeutil -disp
        command example:
            suc:~$ frudump raw  ==> for log only
            suc:~$ frudump parsed   ==> for contents compare
        """

        # read FRU from eeutil as reference
        if not self.nic_read_fru(smb_fru=True, dev="fru"):
            self.nic_set_err_msg("Display FRU From eeutil failed")
            return False
        eeutil_fru = self.zephyr_output_sanitize(self.nic_get_cmd_buf())

        # suc dump fru raw for log purpose only
        cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_FRUDUMP_RAW
        if not self.nic_exec_cmd_from_suc_console1(cmd):
            self.nic_set_err_msg("SUC frudump Command '{:s}' Failed".format(cmd))
            return False

        # suc dump fru raw for log purpose only
        cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_FRUDUMP_PARSED
        if not self.nic_exec_cmd_from_suc_console1(cmd):
            self.nic_set_err_msg("SUC frudump Command '{:s}' Failed".format(cmd))
            return False
        suc_fru = self.zephyr_output_sanitize(self.nic_get_cmd_buf())

        # parse fru data and compare
        suc_fru_dict = {}
        for line in suc_fru.splitlines():
            if ": " not in line:
                continue
            k, v = re.split(r'\s*:\s+', line)
            if k == "serial-number":
                suc_fru_dict["serial-number"] = v.upper()
            if k == "part-number":
                suc_fru_dict["part-number"] = v.upper()
            if k == "board-id":
                suc_fru_dict["board-id"] = v.upper()
            if k == "product-name":
                suc_fru_dict["product-name"] = v.upper()

        eeutil_fru_dict = {}
        for line in eeutil_fru.splitlines():
            found = re.findall(r'Serial Number\s{5,}(\w+)', line)
            if found:
                eeutil_fru_dict["serial-number"] = found[0].upper()
            found = re.findall(r'Part Number\s{5,}([0-9\-]+)', line)
            if found:
                eeutil_fru_dict["part-number"] = found[0].upper()
            found = re.findall(r'Board ID\s{5,}(\w+)', line)
            if found:
                eeutil_fru_dict["board-id"] = found[0].upper()
            found = re.findall(r'Product Name\s{5,}(.*)', line)
            if found:
                eeutil_fru_dict["product-name"] = found[0].upper()

        # compare
        compare_pass = True
        for k, v in suc_fru_dict.items():
            v1 = eeutil_fru_dict.get(k,"")
            if v != v1:
                self.nic_set_err_msg("{:s} from suc is {:s}, not match the value {:s} from eeutil".format(k, v, v1))
                compare_pass = False
        return compare_pass

    def uc_zephyr_fru_boardid_program(self, date, sn, mac, pn, nic_type, dpn, sku, boardid):
        """
        uart:~$ fru
            Subcommands:
            write  : Write FRU data to cache at a starting address.
                    Usage: fru write <address> <format> <data>
                    Where format is 'string' or 'hex'
                    E.g
                    fru write 75 string XXXYYWW0000
                    E.g

        """

        fru_write_cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_FRU_WRITE
        # write serial number
        cmd = f'{fru_write_cmd} 75 string {sn}'
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            self.nic_set_err_msg("uC Zephyr fru write serial number command: '{:s}' Failed".format(cmd))
            return False
        # write mac address
        cmd = f'{fru_write_cmd} 143 hex {mac}'
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            self.nic_set_err_msg("uC Zephyr fru write mac address command: '{:s}' Failed".format(cmd))
            return False
        # write board id
        cmd = f'{fru_write_cmd} 132 hex {boardid}'
        if not self.nic_exec_cmd_from_zephyr_console(cmd):
            self.nic_set_err_msg("uC Zephyr fru write serial number command: '{:s}' Failed".format(cmd))
            return False
        # Update FRU cache to partition
        fru_save_cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_FRU_SAVE
        if not self.nic_exec_cmd_from_zephyr_console(fru_save_cmd):
            self.nic_set_err_msg("uC Zephyr Update FRU cache to partition command: '{:s}' Failed".format(fru_save_cmd))
            return False
        # FRU partition dump
        fru_dump_cmd = MFG_DIAG_CMDS().SUC_ZEPHYR_FRU_DUMP
        if not self.nic_exec_cmd_from_zephyr_console(fru_dump_cmd):
            self.nic_set_err_msg("uC Zephyr Dump FRU partition command: '{:s}' Failed".format(fru_dump_cmd))
            return False
        cmd_buf = self.nic_get_cmd_buf()
        print(cmd_buf)
        return True

    def suc_slot2_usb_sn(self):
        """
        according to rule /etc/udev/rules.d/99-suc-uart.rules, which map usb UART to slot
        find the bus number, device number and serial number for the slot
        """

        # check uart rules file exist
        usb_uart_rules_file = '/etc/udev/rules.d/99-suc-uart.rules'
        cmd = 'ls {:s}'.format(usb_uart_rules_file)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("Command '{:s}' Failed".format(cmd))
            return False
        if "No such file or directory".lower() in self.nic_get_cmd_buf().lower():
            self.nic_set_err_msg("uart rules file {:s} not exist".format(usb_uart_rules_file))
            return False

        # grep usb kernels
        usb_uart_dev = "SUCUART{:d}".format(self._slot + 1)
        cmd = """cat /etc/udev/rules.d/99-suc-uart.rules | grep 'SYMLINK+="{:s}"' | cat""".format(usb_uart_dev)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("Command '{:s}' Failed".format(cmd))
            return False
        cmd_buf = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', self.nic_get_cmd_buf()).strip()
        if "No such file or directory".lower() in cmd_buf.lower():
            self.nic_set_err_msg("Device {:s} not found in suc-uart.rules".format(usb_uart_dev))
            return False

        found_kernel = re.findall(r'KERNELS=="(\d+-\d+)"',  self.nic_get_cmd_buf())
        if not found_kernel:
            self.nic_set_err_msg("kernel pattern KERNELS==d-d not found in suc-uart.rules")
            return False
        kernel = found_kernel[0]

        # get serial
        filename = f'/sys/bus/usb/devices/{kernel}/serial'
        cmd = 'cat {:s}'.format(filename)

        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("Command '{:s}' Failed".format(cmd))
            return False
        cmd_buf = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', self.nic_get_cmd_buf()).strip()
        if "No such file or directory".lower() in cmd_buf:
            self.nic_set_err_msg("File {:s} not exist".format(filename))
            return False
        serial =  cmd_buf.split("\n")[1].strip("\r").strip()

        return serial

    def uc_image_program(self, cmd_format, uc_img, override_fd_descriptors=False):
        """
        Get usb device iserial according to self._slot, which mapping to device /dev/SUCUART(self._slot+1).
        For the usb device interface, so far we hardcode 3 here, unless uC firmware change it in the future
        Command example:
        /home/diag/cns-pmci/test_all.py --board-type AinicSuc --detach-usb-kernel-driver --allow-early-completion --usb 6453473646CF48AFA1C9EF3AA09994E7:3  --test-cases PldmFwUpdateSingleFDUpdateFlow --util pldmfwpkg=/home/diag/iteterev/ainic_fw_vulcano.pldmfw
        command output
        ---------------------------------------------------
        Test case PldmFwUpdateSingleFDUpdateFlow has PASSED
        ---------------------------------------------------

        --------------
        END OF TESTING
        --------------

        === SUMMARY (TEST CASES) ===
        PASS       PldmFwUpdateSingleFDUpdateFlow
        """

        device_iSerial = self.suc_slot2_usb_sn()
        if not device_iSerial:
            self.nic_set_err_msg("Failed to get usb device serial number")
            return False

        # program uC with MTCP
        cmd = cmd_format.format(device_iSerial, uc_img)
        if override_fd_descriptors:
            if self._nic_type == NIC_Type.MORTARO:
                cmd += " --override-fd-descriptors /home/diag/cns-pmci/board/mortaro_p1.json"
            elif self._nic_type == NIC_Type.SARACENO:
                cmd += " --override-fd-descriptors /home/diag/cns-pmci/board/saraceno_p0.json"
            elif self._nic_type == NIC_Type.GELSOP or self._nic_type == NIC_Type.GELSOX:
                cmd += " --override-fd-descriptors /home/diag/cns-pmci/board/gelso.json"
            else:
                cmd += ""
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            self.nic_set_err_msg("Program uC image Command '{:s}' Failed".format(cmd))
            return False
        if "No such file or directory" in self.nic_get_cmd_buf() or "No suitable USB devices found" in  self.nic_get_cmd_buf():
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False

        cmd = "echo My_CMD_RC:$?"
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_RETRY):
            self.nic_set_err_msg("Check Program uC image return code '{:s}' Failed".format(cmd))
            return False
        m = re.findall(r'My_CMD_RC:(\d+)', self.nic_get_cmd_buf())
        if not m:
                self.nic_set_err_msg("Get Program uC image return code failed")
                return False
        rc_code = m[0]
        if str(rc_code) != '0':
            self.nic_set_err_msg("Program uC image Command got non-zero return code:{}".format(rc_code))
            return False
        return True

    def i2c_device_screening(self):
        """
        Run a bunch of I2C Device Related commands, Make sure they are work
        """

        # devmgr_v2 margin info
        cmd = MFG_DIAG_CMDS().MTP_DEVICE_MARGIN_INFO_FMT + " -s {:d}".format(self._slot +1)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("'{:s}' Failed".format(cmd))
            return False
        margin_info = self.nic_get_cmd_buf()

        # devmgr_v2 status
        cmd = MFG_DIAG_CMDS().MTP_MATERA_DEVMGR_STATUS_FMT + " -s {:d}".format(self._slot +1)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("'{:s}' Failed".format(cmd))
            return False
        devmgr_v2_status = self.nic_get_cmd_buf()

        # devmgr_v2 list
        cmd = MFG_DIAG_CMDS().MTP_DEVMGR_LIST_FMT + " -s {:d}".format(self._slot +1)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("'{:s}' Failed".format(cmd))
            return False
        devmgr_v2_list = self.nic_get_cmd_buf()

        # check
        # [2025-11-14_10:31:48] diag@MTP:$ devmgr_v2 margin info -s 6
        # [INFO]    [2025-11-14-10:31:53.777] VDDIO_P1V2       | bus-1 addr 0x10 register 0xf8:  Reg=0x00  --> Margin=0  Volt=1.20V
        # [INFO]    [2025-11-14-10:31:53.777] VDD_0P75_PX      | bus-1 addr 0x10 register 0xf9:  Reg=0x00  --> Margin=0  Volt=0.77V
        # [INFO]    [2025-11-14-10:31:53.777] VDD_0P75_ETH     | bus-1 addr 0x10 register 0xfa:  Reg=0x00  --> Margin=0  Volt=0.77V
        # [INFO]    [2025-11-14-10:31:53.777] VDDCR_0P75       | bus-1 addr 0x10 register 0xfb:  Reg=0x00  --> Margin=0  Volt=0.88V
        # [INFO]    [2025-11-14-10:31:53.777] VDDAN_P1V8_PX    | bus-1 addr 0x30 register 0xf8:  Reg=0x00  --> Margin=0  Volt=1.79V
        # [INFO]    [2025-11-14-10:31:53.777] VDDAN_P1V8_ETH   | bus-1 addr 0x30 register 0xf9:  Reg=0x00  --> Margin=0  Volt=1.79V
        # [INFO]    [2025-11-14-10:31:53.777] VDDAN_P1V1_PX    | bus-1 addr 0x30 register 0xfa:  Reg=0x00  --> Margin=0  Volt=1.11V
        # [INFO]    [2025-11-14-10:31:53.777] VDDAN_P1V1_ETH   | bus-1 addr 0x30 register 0xfb:  Reg=0x00  --> Margin=0  Volt=1.11V
        # [INFO]    [2025-11-14-10:31:53.777] VDDPL_P1V2       | bus-1 addr 0x50 register 0xf8:  Reg=0x00  --> Margin=0  Volt=1.20V
        # [INFO]    [2025-11-14-10:31:53.777] VDDPL_P1V1_PX    | bus-1 addr 0x50 register 0xf9:  Reg=0x00  --> Margin=0  Volt=1.10V
        # [INFO]    [2025-11-14-10:31:53.777] VDDPL_P1V1_ETH   | bus-1 addr 0x50 register 0xfa:  Reg=0x00  --> Margin=0  Volt=1.11V
        # [INFO]    [2025-11-14-10:31:53.777] VDDPL_0P75       | bus-1 addr 0x50 register 0xfb:  Reg=0x00  --> Margin=0  Volt=0.75V
        if "Volt=" not in margin_info:
            self.nic_set_err_msg("devmgr_v2 margin info check failed")
            return False
        # [2025-11-14_11:38:06] diag@MTP:$ devmgr_v2 status -s 6
        # [INFO]    [2025-11-14-11:38:13.017] tmp451 temperature
        # [INFO]    [2025-11-14-11:38:13.017] LOCAL TEMP : 21.000
        # [INFO]    [2025-11-14-11:38:13.017] REMOTE TEMP: 21.000
        # [INFO]    [2025-11-14-11:38:13.017]
        # [INFO]    [2025-11-14-11:38:13.208] voltage ina3221_sensor
        # [INFO]    [2025-11-14-11:38:13.208] NAME            | VBOOT  |  VOUT   |  IOUT   |  POUT
        # [INFO]    [2025-11-14-11:38:13.208] -----------------------------------------------------
        # [INFO]    [2025-11-14-11:38:13.208] VDD_0P75_ETH    | 0.770  |  0.000  |  0.000  |  0.000
        # [INFO]    [2025-11-14-11:38:13.208] VDDAN_P1V1_ETH  | 1.110  |  0.000  |  0.000  |  0.000
        # [INFO]    [2025-11-14-11:38:13.208] VDDCR_0P75      | 0.880  |  0.000  |  0.000  |  0.000
        # [INFO]    [2025-11-14-11:38:13.208] VDDAN_P1V1_PX   | 1.110  |  0.000  |  0.000  |  0.000
        # [INFO]    [2025-11-14-11:38:13.208] VDD_0P75_PX     | 0.770  |  0.000  |  0.000  |  0.000
        # [INFO]    [2025-11-14-11:38:13.208] P3V3_NIC        | 3.300  |  3.328  |  0.160  |  0.532
        # [INFO]    [2025-11-14-11:38:13.208]
        # [INFO]    [2025-11-14-11:38:13.292] LOCAL TEMP : 21.062
        # [INFO]    [2025-11-14-11:38:13.292] REMOTE TEMP: 21.062
        if "ERROR:" in devmgr_v2_status:
            self.nic_set_err_msg("devmgr_v2 status info check failed")
            return False
        # [2025-11-14_10:28:33] diag@MTP:$ devmgr_v2 list -s 6
        # [INFO]    [2025-11-14-10:28:41.549] devices:
        # [INFO]    [2025-11-14-10:28:41.549] - eic@44800000 (READY)
        # [INFO]    [2025-11-14-10:28:41.549]   DT node labels: eic
        # [INFO]    [2025-11-14-10:28:41.549] - gpio@44840300 (READY)
        # [INFO]    [2025-11-14-10:28:41.549]   DT node labels: pg
        # [INFO]    [2025-11-14-10:28:41.549] - gpio@44840280 (READY)
        # [INFO]    [2025-11-14-10:28:41.549]   DT node labels: pf
        # [INFO]    [2025-11-14-10:28:41.549] - gpio@44840200 (READY)
        # [INFO]    [2025-11-14-10:28:41.549]   DT node labels: pe
        # [INFO]    [2025-11-14-10:28:41.549] - gpio@44840180 (READY)
        # [INFO]    [2025-11-14-10:28:41.549]   DT node labels: pd
        # [INFO]    [2025-11-14-10:28:41.549] - gpio@44840100 (READY)
        # [INFO]    [2025-11-14-10:28:41.549]   DT node labels: pc
        # [INFO]    [2025-11-14-10:28:41.549] - gpio@44840080 (READY)
        # [INFO]    [2025-11-14-10:28:41.549]   DT node labels: pb
        # [INFO]    [2025-11-14-10:28:41.549] - gpio@44840000 (READY)
        # [INFO]    [2025-11-14-10:28:41.549]   DT node labels: pa
        # [INFO]    [2025-11-14-10:28:41.549] - cdc_acm_uart0 (READY)
        # [INFO]    [2025-11-14-10:28:41.549]   DT node labels: cdc_acm_uart0
        # [INFO]    [2025-11-14-10:28:41.549] - flash-region@c000000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: pfm
        # [INFO]    [2025-11-14-10:28:41.55 ] - flash-region@8000000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: bfm
        # [INFO]    [2025-11-14-10:28:41.55 ] - flash-region@A000000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: cfm
        # [INFO]    [2025-11-14-10:28:41.55 ] - flash-controller@44002000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: nvmctrl0
        # [INFO]    [2025-11-14-10:28:41.55 ] - sercom@46004000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: sercom4
        # [INFO]    [2025-11-14-10:28:41.55 ] - usb@4f010000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: hsusb0 zephyr_udc0
        # [INFO]    [2025-11-14-10:28:41.55 ] - vulcano_flash@0 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ] - vulcano_flash_mux@0 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ] - sercom@45802000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: sercom3
        # [INFO]    [2025-11-14-10:28:41.55 ] - sercom@45800000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: sercom2
        # [INFO]    [2025-11-14-10:28:41.55 ] - sercom@46002000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: sercom1
        # [INFO]    [2025-11-14-10:28:41.55 ] - sercom@46000000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: sercom0
        # [INFO]    [2025-11-14-10:28:41.55 ] - sercom@45804000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: sercom5
        # [INFO]    [2025-11-14-10:28:41.55 ] - ixs@46030000 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: ixs0
        # [INFO]    [2025-11-14-10:28:41.55 ] - leds (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ] - ina3221_41@2 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: p3v3_nic
        # [INFO]    [2025-11-14-10:28:41.55 ] - ina3221_41@1 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: vdd_0p75_px
        # [INFO]    [2025-11-14-10:28:41.55 ] - ina3221_41@0 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: vddan_p1v1_px
        # [INFO]    [2025-11-14-10:28:41.55 ] - ina3221_40@2 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: vddcr_p075
        # [INFO]    [2025-11-14-10:28:41.55 ] - ina3221_40@1 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: vddan_p1v1_eth
        # [INFO]    [2025-11-14-10:28:41.55 ] - ina3221_40@0 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: vdd_0p75_eth
        # [INFO]    [2025-11-14-10:28:41.55 ] - ina3221@41 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ] - ina3221@40 (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ] - tmp451@4c (READY)
        # [INFO]    [2025-11-14-10:28:41.55 ]   DT node labels: temp_sensor
        if "READY" not in devmgr_v2_list:
            self.nic_set_err_msg("devmgr_v2 list info check failed")
            return False

        return True

    def cpld_register_dump_check(self, check=None):
        """
        dump all registers, and compare it's value if check parameter given 
        check parameter give with address to value dict
        """

        # dump cpld reg
        if not self.nic_dump_reg():
            self.nic_set_err_msg("Dump CPLD Register Failed")
            return False
        dump_info = self.nic_get_cmd_buf()
        # parse dumpped info
        parsed_dump = {}
        if self._nic_type in VULCANO_NIC_TYPE_LIST:
            found_match = re.findall(r'Addr:\s+0x([0-9a-fA-F]{2});\s+Value:\s+0x([0-9a-fA-F]{2})', dump_info)
            if found_match:
                for k, v in found_match:
                    parsed_dump[k] = v

        rc = True
        if check:
            for k, v in check.items():
                if k not in parsed_dump:
                    self.nic_set_err_msg(f"CPLD Register {k} not found in dump data")
                    rc = False
                    continue
                if v != parsed_dump[k]:
                    self.nic_set_err_msg(f"CPLD Register {k} check Failed, expect {v} while got {parsed_dump[k]}")
                    rc = False
        return rc

    def vulcano_suc_i2c_device_test(self, timeout=300):
        '''
        nic_test_vul.py suc_i2c_ds4424_test -slot <slot> -index <index>  index are 0 1 2 here
        nic_test_vul.py suc_i2c_tmp451_test -slot <slot>
        nic_test_vul.py suc_i2c_rc22308_test -slot <slot>
        '''

        suc_i2c_devices = ("suc_osfp_checksum_test", "suc_i2c_rc22308_test", "suc_i2c_ina3221_test",  "suc_i2c_ds4424_test", "suc_i2c_tmp451_test", "suc_i2c_mp2861_test", "suc_spi_cpldreg_test")
        if self._nic_type in (NIC_Type.SARACENO, NIC_Type.MORTARO):
            #For both Saraceno and Mortero, can you remove the ina3221 tests.
            suc_i2c_devices = ("suc_osfp_checksum_test", "suc_i2c_rc22308_test", "suc_i2c_ds4424_test", "suc_i2c_tmp451_test", "suc_i2c_mp2861_test", "suc_spi_cpldreg_test")
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        device2indexes = {
            'suc_i2c_ds4424_test' : ('0', '1', '2'),
            'suc_i2c_ina3221_test' : ('0', '1'),
        }
        if self._nic_type in (NIC_Type.SARACENO, NIC_Type.MORTARO):
            # for the ds4424, only device 0 is valid on both Saraceno and Mortero
            device2indexes = {
                'suc_i2c_ds4424_test' : ('0'),
                'suc_i2c_ina3221_test' : ('0', '1'),
            }

        if not self.mtp_exec_cmd(cmd):
            return False

        cmds = []
        for device in suc_i2c_devices:
            if device in ("suc_i2c_ds4424_test", "suc_i2c_ina3221_test"):
                for index in device2indexes[device]:
                    cmd = MFG_DIAG_CMDS().NIC_TEST_VULCANO_CMD + " {:s} -slot {:s} -index {:s}".format(device, str(self._slot + 1), index)
                    cmds.append(cmd)
            else:
                cmd = MFG_DIAG_CMDS().NIC_TEST_VULCANO_CMD + " {:s} -slot {:s}".format(device, str(self._slot + 1))
                cmds.append(cmd)

        for cmd in cmds:
            print(f'Slot {self._slot + 1} CMD: {cmd}')
            if not self.mtp_exec_cmd(cmd, timeout=timeout):
                return False
            if "=== test result at Slot {:s}: Passed".format(str(self._slot + 1)) not in self.nic_get_cmd_buf():
                self.nic_set_err_msg("Error found in command '{:s}'".format(cmd))
                print(f'Slot {self._slot + 1} FAILED: {cmd}')
                # return False

        return True

    @nic_console_test()
    def nic_mvl_acc_test(self):
        if self._nic_type not in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) or self._nic_type in FPGA_TYPE_LIST:
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_CHECK_HAL_FMT)
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MVL_ACC_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if MFG_DIAG_SIG.NIC_MVL_ACC_SIG in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_set_cmd_buf(cmd_buf)
            return False

    @nic_console_test()
    def nic_mvl_stub_test(self, loopback=True):
        if self._nic_type not in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) or self._nic_type in FPGA_TYPE_LIST:
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_CHECK_HAL_FMT)
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        if loopback:
            external_loopback = "1"
        else:
            external_loopback = "0"
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MVL_STUB_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if MFG_DIAG_SIG.NIC_MVL_STUB_SIG in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_set_cmd_buf(cmd_buf)
            return False

    @nic_console_test()
    def nic_mvl_link_test(self, ports=1):
        nic_cmd_list = list()
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_BRINGUP_MGMT_FMT)
        nic_cmd_list.append("sleep 5") # wait for hal to come up before killing it
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_CHECK_HAL_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        if self._nic_type in CAPRI_NIC_TYPE_LIST:
            if ports == 1:
                sig = MFG_DIAG_SIG.NIC_MVL_LINK1_SIG
                nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MVL_LINK_CAPRI_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/", "1"))
            elif ports == 2:
                sig = MFG_DIAG_SIG.NIC_MVL_LINK2_SIG
                nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MVL_LINK_CAPRI_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/", "2"))
        else:
            sig = MFG_DIAG_SIG.NIC_MVL_LINK_SIG
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MVL_LINK_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if sig in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_set_cmd_buf(cmd_buf)
            return False

    @nic_console_test()
    def nic_phy_xcvr_test(self):
        if self._nic_type not in FPGA_TYPE_LIST:
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_CHECK_HAL_FMT)
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FPGA_PHY_TEST_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if MFG_DIAG_SIG.NIC_FPGA_PHY_TEST_SIG in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_set_cmd_buf(cmd_buf)
            return False

    @nic_console_test()
    def nic_phy_xcvr_link_test(self):
        if self._nic_type not in FPGA_TYPE_LIST:
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_CHECK_HAL_FMT)
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FPGA_PHY_LINK_TEST_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if MFG_DIAG_SIG.NIC_FPGA_PHY_LINK_TEST_SIG in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_set_cmd_buf(cmd_buf)
            return False

    @nic_console_test()
    def nic_edma_test(self):
        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_DIAG_CHECK_HAL_FMT)
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        nic_cmd_list.append("tar xf edma_test.tar.gz")

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_EDMA_TEST_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if MFG_DIAG_SIG.NIC_EDMA_TEST_SIG in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_set_cmd_buf(cmd_buf)
            return False

    def nic_check_emmc_mounted(self):
        # check if emmc is mounted. For use with console already attached.
        nic_cmd = MFG_DIAG_CMDS().NIC_MOUNT_DISP_FMT
        mount_sig = MFG_DIAG_SIG.NIC_MOUNT_OK_SIG
        self._nic_handle.sendline(nic_cmd)
        idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if mount_sig in cmd_buf:
            return True
        else:
            return False

    @nic_console_test()
    def nic_check_rebooted(self):

        ret = True
        if self._nic_type in SALINA_AI_NIC_TYPE_LIST:
            nic_cmd_list = list()
            nic_cmd_list.append("kernel uptime")
            for nic_cmd in nic_cmd_list:
                self._nic_handle.sendline(nic_cmd)
                idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=10)
                if idx < 0:
                    self.nic_set_cmd_buf(self._nic_handle.before)
                    ret &= False
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                ret &= False
            return ret

        nic_cmd_list = list()
        nic_cmd_list.append("uptime")
        nic_cmd_list.append("dmesg")
        nic_cmd_list.append("mount")

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=10)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                ret &= False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            ret &= False

        if "/dev/mmcblk0p10" not in cmd_buf:
            self.nic_set_err_msg("EMMC not mounted")
            self.nic_set_cmd_buf(cmd_buf)
            ret &= False

        nic_cmd_list = list()
        nic_cmd_list.append("env | grep -v PS1")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=10)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                ret &= False
        cmd_buf = self._nic_handle.before
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            ret &= False

        # if "CARD_NAME=NIC{:d}".format(self._slot+1) in cmd_buf:
        if "CARD_ENV=" in cmd_buf:
            ret &= True
        else:
            self.nic_set_err_msg("NIC was rebooted")
            ret &= False

        return ret

    def nic_prp_test(self):
        if not self.mtp_exec_cmd(MFG_DIAG_CMDS().NIC_DIAG_STOP_TCLSH_FMT):
            return False
        if not self.mtp_exec_cmd("cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)):
            return False

        cmd = "tclsh ./sal_prp_test.tcl -slot {:d}".format(self._slot+1)

        if not self.mtp_exec_cmd(cmd, timeout=60):
            self.nic_stop_test()
            return False

        if MFG_DIAG_SIG.NIC_PRP_TEST_SIG not in self.nic_get_cmd_buf():
            self.nic_stop_test()
            return False

        self.nic_stop_test()
        return True

    def nic_qspi_verify_test(self, stage="", test=""):
        nic_type = self._nic_type
        if test in ["SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY"]:
            if nic_type == NIC_Type.POLLARA:
                img_path = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.qspi_verify_sh_img["POLLARA-1Q400P"]
            elif nic_type == NIC_Type.LINGUA:
                img_path = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.qspi_verify_sh_img["POLLARA-1Q400P-OCP"]
        else:
            img_path = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + NIC_IMAGES.qspi_verify_sh_img[nic_type]

        path = os.path.split(img_path)[0]
        script = os.path.split(img_path)[1]

        cmd = "cd {}".format(path)
        if not self.mtp_exec_cmd(cmd, timeout=10):
            return False

        cmd = "./" + script + " " + str(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=120):
            return False

        return True

    def nic_dump_reg(self):
        # dump all registers for information
        cmd = MFG_DIAG_CMDS().MTP_FPGA_UTIL_REGDUMP_FMT
        tout = 5
        if self._nic_type in VULCANO_NIC_TYPE_LIST:
            cmd = MFG_DIAG_CMDS().NIC_AVS_POST_FMT.format(self._slot + 1)
            tout = 60
        if not self.mtp_exec_cmd(cmd, timeout=tout):
            return False

        return True

    def read_nic_temp(self, skip_reboot=False):
        if not self.mtp_exec_cmd(MFG_DIAG_CMDS().NIC_DIAG_STOP_TCLSH_FMT):
            return False
        if not self.mtp_exec_cmd("cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)):
            return False

        if self._nic_type in SALINA_NIC_TYPE_LIST:
            cmd = "tclsh get_nic_sts.tcl {:s} {:d} {:s}".format(str(self._sn), self._slot+1, "1")
        elif self._nic_type in VULCANO_NIC_TYPE_LIST:
            cmd = "Read ASIC Temp placehold" 
        else:
            cmd = "tclsh get_nic_sts.tcl {:s} {:d}".format(str(self._sn), self._slot+1)

            if skip_reboot:
                cmd += " 0" #skips VRM
        if self._nic_type in SALINA_DPU_NIC_TYPE_LIST:
            # if ddr ecc happen, get_nic_sts.tcl will run eye margin for ddr. So it take 60-80 mins to complete.
            t_out = 3600 + 180
        else:
            t_out = 180

        if not self.mtp_exec_cmd(cmd, timeout=t_out):
            self.nic_stop_test()
            return False
        self.nic_stop_test()
        return True

    def clear_nic_uart(self):
        cmd = "ps -elf | grep -e 'fpga_uart {:d}' | grep -v grep".format(self._slot)
        if not self.mtp_exec_cmd(cmd, timeout=10):
            self.nic_stop_test()
            return False

        cmd_buf = libmfg_utils.special_char_removal(self.nic_get_cmd_buf())
        ps_info = re.findall(r"(\d+)\s+(\w+)\s+(\w+)\s+(\d+)\s+.*fpga_uart\s+({:d})".format(self._slot), cmd_buf)

        for ps in ps_info:
            ps_pid = str(ps[3])
            cmd = "kill -9 {:s}".format(ps_pid)
            if not self.mtp_exec_cmd(cmd, timeout=15):
                self.nic_stop_test()
                return False

        self.nic_stop_test()
        return True

    def sal_check_j2c(self):
        if not self.mtp_exec_cmd(MFG_DIAG_CMDS().NIC_DIAG_STOP_TCLSH_FMT):
            return False

        cmd = "tclsh /home/diag/diag/scripts/asic/sal_check_j2c.tcl -slot {:d} -ite 1".format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=600):
            self.nic_stop_test()
            return False
        self.nic_stop_test()
        return True

    @nic_console_test()
    def nic_port_counters(self):
        cmd = "halctl"
        if self._nic_type in SALINA_DPU_NIC_TYPE_LIST:
            cmd = "pdsctl"
        nic_cmd_list = list()
        nic_cmd_list.append("{:s} show port status".format(cmd))
        nic_cmd_list.append("{:s} show port statistics --port eth1/3".format(cmd))    # BX port counters
        nic_cmd_list.append("{:s} show port internal".format(cmd))                    # MVL switch port status
        nic_cmd_list.append("{:s} show port internal statistics".format(cmd))         # all port counters

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=10)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        return True

    @nic_console_test()
    def nic_console_read_sgmii(self, port, reg_addr, read_data):
        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_SGMII_READ_ELBA_FMT.format("./", port, reg_addr))
        else:
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_SGMII_READ_FMT.format("./", port, reg_addr))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cpld_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cpld_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        match = re.findall(r"0x%x\r\n(0x[0-9a-fA-F]+)" % reg_addr, cpld_buf)
        if len(match) > 0:
            read_data[0] = int(match[0], 16)
        else:
            self.nic_set_cmd_buf(cpld_buf)
            return False

        self.nic_set_cmd_buf(self._nic_handle.before)
        return True

    @nic_console_test()
    def nic_console_write_sgmii(self, port, reg_addr, write_data):
        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_FSCK_EMMC_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS().NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_SGMII_WRITE_ELBA_FMT.format("./", port, reg_addr, write_data))
        else:
            nic_cmd_list.append(MFG_DIAG_CMDS().NIC_SGMII_WRITE_FMT.format("./", port, reg_addr, write_data))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False

        time.sleep(5)
        self.nic_set_cmd_buf(self._nic_handle.before)
        return True

    def nic_console_enable_network_port(self):
        # Disable MTP port
        if not self.nic_console_write_sgmii(port=0, reg_addr=0xd, write_data=0x1940):
            self.nic_set_err_msg("Failed to write SGMII reg 0xd")
            return False

        # Verify 0xd is 0x1940
        read_data = [0]
        if not self.nic_console_read_sgmii(port=0, reg_addr=0xd, read_data=read_data):
            self.nic_set_err_msg("Failed to read SGMII reg 0xd")
            return False
        if read_data[0] != 0x1940:
            if not self.nic_console_write_sgmii(port=0, reg_addr=0xd, write_data=0x1940):
                self.nic_set_err_msg("Failed to write SGMII reg 0xd")
                return False
            if not self.nic_console_read_sgmii(port=0, reg_addr=0xd, read_data=read_data):
                self.nic_set_err_msg("Failed to read SGMII reg 0xd")
                return False
            if read_data[0] != 0x1940:
                return False

        # Enable Network port
        if not self.nic_console_write_sgmii(port=0, reg_addr=0x3, write_data=0x1140):
            self.nic_set_err_msg("Failed to write SGMII reg 0xd")
            return False

        # Verify 0x3 is 0x1140
        read_data = [0]
        if not self.nic_console_read_sgmii(port=0, reg_addr=0x3, read_data=read_data):
            self.nic_set_err_msg("Failed to read SGMII reg 0x3")
            return False
        if read_data[0] != 0x1140:
            if not self.nic_console_write_sgmii(port=0, reg_addr=0x3, write_data=0x1140):
                self.nic_set_err_msg("Failed to write SGMII reg 0x3")
                return False
            if not self.nic_console_read_sgmii(port=0, reg_addr=0x3, read_data=read_data):
                self.nic_set_err_msg("Failed to read SGMII reg 0x3")
                return False
            if read_data[0] != 0x1140:
                return False

        return True

    def nic_console_disable_network_port(self):
        # Disable Network port
        if not self.nic_console_write_sgmii(port=0, reg_addr=0x3, write_data=0x1940):
            self.nic_set_err_msg("Failed to write SGMII reg 0xd")
            return False

        # Verify 0x3 is 0x1940
        read_data = [0]
        if not self.nic_console_read_sgmii(port=0, reg_addr=0x3, read_data=read_data):
            self.nic_set_err_msg("Failed to read SGMII reg 0x3")
            return False
        if read_data[0] != 0x1940:
            if not self.nic_console_write_sgmii(port=0, reg_addr=0x3, write_data=0x1940):
                self.nic_set_err_msg("Failed to write SGMII reg 0x3")
                return False
            if not self.nic_console_read_sgmii(port=0, reg_addr=0x3, read_data=read_data):
                self.nic_set_err_msg("Failed to read SGMII reg 0x3")
                return False
            if read_data[0] != 0x1940:
                return False

        # ENable MTP port
        if not self.nic_console_write_sgmii(port=0, reg_addr=0xd, write_data=0x1140):
            self.nic_set_err_msg("Failed to write SGMII reg 0xd")
            return False

        # Verify 0xd is 0x1140
        read_data = [0]
        if not self.nic_console_read_sgmii(port=0, reg_addr=0xd, read_data=read_data):
            self.nic_set_err_msg("Failed to read SGMII reg 0xd")
            return False
        if read_data[0] != 0x1140:
            if not self.nic_console_write_sgmii(port=0, reg_addr=0xd, write_data=0x1140):
                self.nic_set_err_msg("Failed to write SGMII reg 0xd")
                return False
            if not self.nic_console_read_sgmii(port=0, reg_addr=0xd, read_data=read_data):
                self.nic_set_err_msg("Failed to read SGMII reg 0xd")
                return False
            if read_data[0] != 0x1140:
                return False

        return True

    @nic_console_test()
    def nic_console_ping(self, to_slot):
        ipaddr = libmfg_utils.get_nic_ip_addr(to_slot)

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS().MTP_NIC_PING_FMT.format(ipaddr))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False

        match = re.findall(r" 0% packet loss", cmd_buf)
        if match:
            self.nic_set_cmd_buf(cmd_buf)
            return True

        self.nic_set_cmd_buf(cmd_buf)
        return False

    @nic_console_test()
    def nic_console_read_uboot(self):
        exp_boot0_version = ""
        exp_golduboot_version = ""

        if self._nic_type in FPGA_TYPE_LIST:
            exp_boot0_version = NIC_IMAGES.uboot_dat[self._nic_type]

        for loop in range(0,2):
            nic_cmd = "fwupdate -l"
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                return False
        
            try:
                fw_info = json.loads(r'{}'.format(self.nic_hide_prompt(cmd_buf.split("fwupdate -l")[1])))

                if exp_boot0_version != "" and 'boot0' not in fw_info:
                    self.nic_set_err_msg("Incorrect uboot type")
                    self.nic_set_cmd_buf(cmd_buf)
                    return False

                if exp_boot0_version != "":
                    got_boot0_version = str(fw_info['boot0']['image']['image_version'])
                    if got_boot0_version != exp_boot0_version:
                        self.nic_set_err_msg("Incorrect boot0 version: {:s}, expecting: {:s}".format(got_boot0_version, exp_boot0_version))
                        self.nic_set_cmd_buf(cmd_buf)
                        return False

                if exp_golduboot_version != "":
                    got_golduboot_version = str(fw_info['goldfw']['uboot']['software_version'])
                    if got_golduboot_version != exp_golduboot_version:
                        self.nic_set_err_msg("Incorrect uboot version")
                        self.nic_set_cmd_buf(cmd_buf)
                        return False

                break

            except Exception as e:
                if loop == 1:
                    # weird characters read
                    self.nic_set_err_msg("Couldn't read uboot version")
                    self.nic_set_err_msg(traceback.format_exc())
                    self.nic_set_cmd_buf(cmd_buf)
                    return False
                else:
                    continue

        self.nic_set_cmd_buf(self._nic_handle.before)
        return True

    @nic_console_test()
    def nic_console_read_secure_boot_keys(self):
        """
          "extosa": {
            "kernel_fit": {
              "secure_boot": "yes",
              "secure_boot_keys": "eng",
            },
        """
        exp_secure_boot = "yes"
        exp_secure_boot_keys = "prod"

        if self._nic_type not in FPGA_TYPE_LIST:
            return False

        for loop in range(0,2):
            nic_cmd = "fwupdate -l"
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                return False
        
            try:
                fw_info = json.loads(r'{}'.format(self.nic_hide_prompt(cmd_buf.split("fwupdate -l")[1])))
                if 'extosa' not in fw_info:
                    self.nic_set_err_msg("Missing extosa image")
                    self.nic_set_cmd_buf(cmd_buf)
                    return False

                if exp_secure_boot != "":
                    got_secure_boot = str(fw_info['extosa']['kernel_fit']['secure_boot'])
                    if got_secure_boot != exp_secure_boot:
                        self.nic_set_err_msg("Incorrect secure_boot value: {:s}, expecting: {:s}".format(got_secure_boot, exp_secure_boot))
                        self.nic_set_cmd_buf(cmd_buf)
                        return False

                if exp_secure_boot_keys != "":
                    got_secure_boot_keys = str(fw_info['extosa']['kernel_fit']['secure_boot_keys'])
                    if got_secure_boot_keys != exp_secure_boot_keys:
                        self.nic_set_err_msg("Incorrect secure_boot_keys value: {:s}, expecting: {:s}".format(got_secure_boot_keys, exp_secure_boot_keys))
                        self.nic_set_cmd_buf(cmd_buf)
                        return False

                break

            except Exception as e:
                if loop == 1:
                    # weird characters read
                    self.nic_set_err_msg("Couldn't read extosa secure_boot fields")
                    self.nic_set_err_msg(traceback.format_exc())
                    self.nic_set_cmd_buf(cmd_buf)
                    return False
                else:
                    continue

        self.nic_set_cmd_buf(self._nic_handle.before)
        return True

    def nic_vdd_ddr_fix(self, d3_val, d4_val, vddq_prog):
        nic_cmd_list = list()
        nic_cmd_list.append("i2cset -y 0 0x1c 0xd4 {:s}".format(d4_val))
        nic_cmd_list.append("i2cset -y 0 0x1c 0xd3 {:s}".format(d3_val))
        nic_cmd_list.append("i2cset -y 0 0x1c 0x11 c")
        if not self.nic_exec_cmds(nic_cmd_list):
            return False

        if vddq_prog:
            nic_cmd_list = list()
            nic_cmd_list.append("i2cset -y 0 0x1b 0xd4 {:s}".format(d4_val))
            nic_cmd_list.append("i2cset -y 0 0x1b 0xd3 {:s}".format(d3_val))
            nic_cmd_list.append("i2cset -y 0 0x1b 0x11 c")
            if not self.nic_exec_cmds(nic_cmd_list):
                return False

        nic_cmd_list = list()
        nic_cmd_list.append("fwenv -d ddr_use_hardcoded_training")
        nic_cmd_list.append("fwenv -d ddr_freq")
        nic_cmd_list.append("fwenv -d ddr_vdd_margin")
        nic_cmd_list.append("fwenv -d ddr_periodic_trg_en")
        nic_cmd_list.append("fwenv -d ddr_ecc_writeback")
        nic_cmd_list.append("fwenv -n gold -d ddr_use_hardcoded_training")
        nic_cmd_list.append("fwenv -n gold -d ddr_freq")
        nic_cmd_list.append("fwenv -n gold -d ddr_vdd_margin")

        if not self.nic_exec_cmds(nic_cmd_list):
            return False

        nic_cmd = "fwenv"
        cmd_buf = self.nic_get_info(nic_cmd)

        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False

        if "ddr_freq" in cmd_buf or "ddr_use_hardcoded_training" in cmd_buf:
            self.nic_set_err_msg("Unable to clear DDR fwenv setting")
            return False
    
        return True

    def gigilo_nic_vdd_ddr_fix(self, i2cbus_num="2", chip_addr="0x1c", d3_val=None, d4_val=None):

        nic_cmd_list = list()
        # set vdd_ddr freq
        if d3_val:
            nic_cmd_list.append("i2cset -y {:s} {:s} 0xd3 {:s}".format(i2cbus_num, chip_addr, d3_val))
        if d4_val:
            nic_cmd_list.append("i2cset -y {:s} {:s} 0xd4 {:s}".format(i2cbus_num, chip_addr, d4_val))

        # save to nvram
        nic_cmd_list.append("i2cset -y {:s} {:s} 0x11 c".format(i2cbus_num, chip_addr))

        if not self.nic_exec_cmds(nic_cmd_list):
            return False
        return True

    def nic_vdd_ddr_check(self, d3_val=None, d4_val=None, vddq_prog=None, i2cbus_num="0", chip_addr="0x1c"):
        if d3_val:
            nic_cmd = "i2cget -y {:s} {:s} 0xd3".format(i2cbus_num, chip_addr)
            cmd_buf = self.nic_get_info(nic_cmd)

            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                return False

            if d3_val not in cmd_buf:
                self.nic_set_err_msg("Incorrect VDD_DDR switching freq, expecting {:s}, got {:s}".format(d3_val, cmd_buf))
                return False


        if d4_val:
            nic_cmd = "i2cget -y {:s} {:s} 0xd4".format(i2cbus_num, chip_addr)
            cmd_buf = self.nic_get_info(nic_cmd)

            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                return False

            if d4_val not in cmd_buf:
                self.nic_set_err_msg("Incorrect VDD_DDR margin, expecting {:s}, got {:s}".format(d4_val, cmd_buf))
                return False

        nic_cmd = "fwenv"
        cmd_buf = self.nic_get_info(nic_cmd)

        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False

        if any(x in cmd_buf for x in ["ddr_freq", "ddr_use_hardcoded_training", "ddr_vdd_margin", "ddr_ecc_writeback", "ddr_periodic_trg_en"]):
            self.nic_set_err_msg("DDR fwenv setting not cleared")
            return False


        if vddq_prog:
            nic_cmd = "i2cget -y 0 0x1b 0xd3"
            cmd_buf = self.nic_get_info(nic_cmd)

            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                return False

            if d3_val not in cmd_buf:
                self.nic_set_err_msg("Incorrect VDDQ_DDR switching freq, expecting {:s}, got {:s}".format(d3_val, cmd_buf))
                return False



            nic_cmd = "i2cget -y 0 0x1b 0xd4"
            cmd_buf = self.nic_get_info(nic_cmd)

            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                return False

            if d4_val not in cmd_buf:
                self.nic_set_err_msg("Incorrect VDDQ_DDR margin, expecting {:s}, got {:s}".format(d4_val, cmd_buf))
                return False

        return True

    @nic_console_test()
    def nic_console_vdd_ddr_fix(self, d3_val, d4_val, vddq_prog):
        nic_cmd_list = list()
        nic_cmd_list.append("i2cset -y 0 0x1c 0xd4 {:s}".format(d4_val))
        nic_cmd_list.append("i2cset -y 0 0x1c 0xd3 {:s}".format(d3_val))
        nic_cmd_list.append("i2cset -y 0 0x1c 0x11 c")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False

        if vddq_prog:
            nic_cmd_list = list()
            nic_cmd_list.append("i2cset -y 0 0x1b 0xd4 {:s}".format(d4_val))
            nic_cmd_list.append("i2cset -y 0 0x1b 0xd3 {:s}".format(d3_val))
            nic_cmd_list.append("i2cset -y 0 0x1b 0x11 c")
            for nic_cmd in nic_cmd_list:
                self._nic_handle.sendline(nic_cmd)
                idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
                if idx < 0:
                    self.nic_set_cmd_buf(self._nic_handle.before)
                    return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        nic_cmd_list = list()
        nic_cmd_list.append("fwenv -d ddr_use_hardcoded_training")
        nic_cmd_list.append("fwenv -d ddr_freq")
        nic_cmd_list.append("fwenv -d ddr_vdd_margin")
        nic_cmd_list.append("fwenv -d ddr_periodic_trg_en")
        nic_cmd_list.append("fwenv -d ddr_ecc_writeback")
        nic_cmd_list.append("fwenv -n gold -d ddr_use_hardcoded_training")
        nic_cmd_list.append("fwenv -n gold -d ddr_freq")
        nic_cmd_list.append("fwenv -n gold -d ddr_vdd_margin")
        nic_cmd_list.append("fwenv")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
    
        self.nic_set_cmd_buf(cmd_buf)
        return True

    @nic_console_test()
    def nic_console_vdd_ddr_check(self, d3_val, d4_val, vddq_prog):
        ### check frequency set ###
        nic_cmd_list = list()
        nic_cmd_list.append("i2cget -y 0 0x1c 0xd3")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if d3_val not in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("Incorrect VDD_DDR switching freq, expecting {:s}, got {:s}".format(d3_val, cmd_buf))
            return False



        ### check margin set ###
        nic_cmd_list = list()
        nic_cmd_list.append("i2cget -y 0 0x1c 0xd4")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if d4_val not in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("Incorrect VDD_DDR margin, expecting {:s}, got {:s}".format(d4_val, cmd_buf))
            return False



        ### check fwenvs cleared ###
        nic_cmd_list = list()
        nic_cmd_list.append("fwenv")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            return False
        if any(x in cmd_buf for x in ["ddr_freq", "ddr_use_hardcoded_training", "ddr_vdd_margin", "ddr_ecc_writeback", "ddr_periodic_trg_en"]):
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("DDR fwenv setting not cleared")
            return False


        if vddq_prog:
            ### check frequency set ###
            nic_cmd_list = list()
            nic_cmd_list.append("i2cget -y 0 0x1b 0xd3")
            for nic_cmd in nic_cmd_list:
                self._nic_handle.sendline(nic_cmd)
                idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
                if idx < 0:
                    self.nic_set_cmd_buf(self._nic_handle.before)
                    return False
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                return False
            if d3_val not in cmd_buf:
                self.nic_set_cmd_buf(cmd_buf)
                self.nic_set_err_msg("Incorrect VDDQ_DDR switching freq, expecting {:s}, got {:s}".format(d3_val, cmd_buf))
                return False



            ### check margin set ###
            nic_cmd_list = list()
            nic_cmd_list.append("i2cget -y 0 0x1b 0xd4")
            for nic_cmd in nic_cmd_list:
                self._nic_handle.sendline(nic_cmd)
                idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
                if idx < 0:
                    self.nic_set_cmd_buf(self._nic_handle.before)
                    return False
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                return False
            if d4_val not in cmd_buf:
                self.nic_set_cmd_buf(cmd_buf)
                self.nic_set_err_msg("Incorrect VDDQ_DDR margin, expecting {:s}, got {:s}".format(d4_val, cmd_buf))
                return False

        self.nic_set_cmd_buf(cmd_buf)
        return True

    def nic_failed_boot(self):
        ## replace this with a general test history lookup
        return self._failed_console_boot

    def set_nic_failed_boot(self):
        self._failed_console_boot = True

    def nic_l1_esecure_prog(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if self._nic_type not in ELBA_NIC_TYPE_LIST and self._nic_type not in GIGLIO_NIC_TYPE_LIST:
            return False
        
        if self._nic_type in ELBA_NIC_TYPE_LIST:
            cmd = MFG_DIAG_CMDS().NIC_L1_ESEC_PROG_FMT.format(self._slot+1)
        elif self._nic_type in GIGLIO_NIC_TYPE_LIST:
            cmd = MFG_DIAG_CMDS().NIC_L1_ESEC_GIGLIO_PROG_FMT.format(self._slot+1)

        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_L1_ESEC_PROG_DELAY):
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_L1_ESEC_PROG_OK_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_l1_pre_setup(self):
        '''
        run l1 res-setup, salina cards only
        '''

        # goto the asic dir
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS().MATERA_L1_PRE_SETUP_FMT.format(str(self._slot+1))
        if not self.mtp_exec_cmd(cmd):
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_L1_PRE_SETUP_OK_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_i2c_bus_scan(self):
        bus_list = [0, 1, 2]

        nic_cmd_list = list()

        for i2c_bus in bus_list:
            nic_cmd = MFG_DIAG_CMDS().NIC_I2C_DETECT_FMT.format(i2c_bus)
            nic_cmd_list.append(nic_cmd)

        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.NIC_I2C_DETECT_DELAY):
            return False

        return True

    @nic_console_test()
    def nic_detect_transceiver_presence(self, port):
        if port not in ("0","1","2"):
            self.nic_set_err_msg("Script error: invalid port specified")
            return False

        nic_cmd_list = list()
        nic_cmd_list.append("chmod +x {:s}/diag/scripts/eeprom_sn.sh".format("/data/"))
        nic_cmd_list.append("{:s}/diag/scripts/eeprom_sn.sh -d -b {:s}".format("/data/", port))
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_set_err_msg("Can't read detect transceiver")
                return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_set_err_msg("No output when reading loopback transceiver detect signal")
            return False
        self.nic_set_cmd_buf(cmd_buf)

        if "no device found" in cmd_buf:
            return False
        return True

    @nic_console_test()
    def nic_read_transceiver_sn(self, port):
        if port not in ("0","1","2"):
            self.nic_set_err_msg("Script error: invalid port specified")
            return False

        nic_cmd_list = list()
        nic_cmd_list.append("chmod +x {:s}/diag/scripts/eeprom_sn.sh".format("/data/"))
        nic_cmd_list.append("{:s}/diag/scripts/eeprom_sn.sh -s -b {:s}".format("/data/", port))
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [self._nic_con_prompt], self._nic_con_prompt, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_set_err_msg("Can't read transceiver EEPROM")
                return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_set_err_msg("No output when reading loopback transceiver EEPROM")
            return False

        sn_match = re.search("Bus %s: SN (.*)" % port, cmd_buf)
        if sn_match is None or len(sn_match.groups()) == 0:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("Failed to parse Port {:s} loopback transceiver EEPROM".format(port))
            return False
        self._loopback_sn[port] = sn_match.group(1).strip()
    
        self.nic_set_cmd_buf(cmd_buf)
        return True

    def nic_read_salina_transceiver_sn(self, port):
        if port not in ("0","1","2"):
            self.nic_set_err_msg("Script error: invalid port specified")
            return False

        cmd = "/home/diag/diag/scripts/xcvr_sn.sh -s {:s} -p {:s}".format(str(self._slot + 1), port)

        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
            return False

        cmd_buf = self.nic_get_cmd_buf()
        if "not present" in cmd_buf or "ERROR:" in cmd_buf:
            return False

        sn_match = re.search(r"XCVR SN:\s+(\w+)", cmd_buf)

        if sn_match is None or len(sn_match.groups()) == 0:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("Failed to parse Port {:s} loopback transceiver EEPROM".format(port))
            return False
        self._loopback_sn[port] = sn_match.group(1).strip()

        self.nic_set_cmd_buf(cmd_buf)
        return True

    def nic_read_vulcano_transceiver_sn(self, port):
        if port not in ("0","1","2"):
            self.nic_set_err_msg("Script error: invalid port specified")
            return False

        cmd = MFG_DIAG_CMDS().PANAREA_SUC_UTIL_OSFP_READ_SN + " -s {:s}".format(str(self._slot + 1))
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
            return False

        cmd_buf = self.nic_get_cmd_buf()
        if "osfp_read_sn Failed" in cmd_buf or "osfp: command not found" in cmd_buf or "No OSFP Detected" in cmd_buf:
            return False

        sn_match = re.search(r"OSFP\sS\/N:\s+(\w+)", cmd_buf)

        if sn_match is None or len(sn_match.groups()) == 0:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("Failed to parse Port {:s} loopback transceiver EEPROM".format(port))
            return False
        self._loopback_sn[port] = sn_match.group(1).strip()

        self.nic_set_cmd_buf(cmd_buf)
        return True

    @nic_console_test()
    def nic_console_call_sysresetsh(self, ending="login", checkPoints=[]):
        """
        Excute systeset.sh command in new establishe console session.
        """

        self._nic_handle.sendline("sysreset.sh")
        idx = libmfg_utils.mfg_expect_console_fuzzywuzzy(self._nic_handle, [ending], self._nic_con_prompt, timeout=MTP_Const.NIC_SYSRESET_DELAY)
        self.nic_set_cmd_buf(self._nic_handle.before)

        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        self.nic_set_cmd_buf(buf)

        # check checkpoints
        for check_point in checkPoints:
            match = re.findall(r"{:s}".format(check_point), buf)
            if not match:
                return False

        return True

    def device_conf_verify(self):
        """
        wait for file /sysconfig/config0/device.conf to be created
        issue sync command
        """

        max_polling_time = 120
        polled_time = 0
        while polled_time < max_polling_time:

            polled_time += 10
            time.sleep(10)

            self.nic_get_err_msg() # clear previous loop's error

            if not self.nic_exec_cmds(["cat /sysconfig/config0/device.conf"]):
                self.nic_set_err_msg("Failed to read device.conf")
                continue

            cmd_buf = self.nic_get_cmd_buf()
            if not cmd_buf:
                self.nic_set_err_msg("No output from device.conf")
                continue

            if "No such file" in cmd_buf:
                self.nic_set_err_msg("device.conf is missing")
                continue

            if "port-admin-state" in cmd_buf:
                # sync for sanity
                if not self.nic_exec_cmds(["sync", "sync"]):
                    self.nic_set_err_msg("Failed to issue sync commands")
                    return False
                return True

        self.nic_set_err_msg("Waited too long for device.conf to generate")
        return False
