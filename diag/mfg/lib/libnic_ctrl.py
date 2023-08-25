import time
import os
import libmfg_utils
import re
import json
import traceback
import pexpect

from datetime import datetime
from libdefs import NIC_Type
from libdefs import MTP_ASIC_SUPPORT
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

        self._diag_ver = None
        self._diag_util_ver = None
        self._diag_asic_ver = None
        self._cpld_ver = None
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
        self._err_msg = None
        self._cmd_buf = None

        self._asic_type = None
        self._ip_addr = None
        self._fst_pcie_bus = None
        self._fst_eth_mnic = None
        self._emmc_mfr_id = ""

        self._refresh_required = True
        self._failed_console_boot = False

        self._fpga_updated = False
        self._gold_fpga_updated = False 

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

    def mtp_exec_cmd(self, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        self.nic_set_cmd_buf(self._nic_handle.before)
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

    def nic_prompt_cfg(self, timeout=MTP_Const.NIC_CON_CMD_DELAY):
        """
        try to set vaiable PS1 to '[$(date +%Y-%m-%d_%H:%M:%S)]\u# '
        return False if timeout, otherwise return True
        """

        self._nic_handle.sendline('PS1="[$(date +%Y-%m-%d_)\\t] \u' + self._nic_con_prompt + '"')
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

    def nic_power_off(self):
        cmd = MFG_DIAG_CMDS.NIC_POWER_OFF_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False
        libmfg_utils.count_down(MTP_Const.NIC_POWER_OFF_DELAY)
        return True


    def nic_power_on(self):
        cmd = MFG_DIAG_CMDS.NIC_POWER_ON_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False

        libmfg_utils.count_down(MTP_Const.NIC_POWER_ON_DELAY)
        return True


    def nic_power_cycle(self):
        if not self.nic_power_off():
            return False
        if not self.nic_power_on():
            return False
        return True


    def nic_console_attach(self):
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_DIAG_STOP_PICOCOM_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["$"], timeout=10)

        # Check if there is still got picocom process running
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_DIAG_CHECK_PICOCOM_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["$"], timeout=10)

        cmd = MFG_DIAG_CMDS.NIC_CON_ATTACH_FMT.format(self._slot+1)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["Terminal ready"], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_err_msg("{:s} failed - occupied or missing".format(cmd))
            return False
        time.sleep(5)
        # send return
        self._nic_handle.sendline("")
        # TODO: Forio need another enter to connect console
        if self._nic_type == NIC_Type.FORIO or self._nic_type == NIC_Type.VOMERO:
            self._nic_handle.sendline("")

        exp_list = [self._nic_con_prompt, "login:", "assword:"]
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, exp_list, timeout=MTP_Const.NIC_CON_INIT_DELAY)
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
                self.nic_set_err_msg("Timeout connecting to UART console")
                self.nic_console_detach()
                return False

        if not self.nic_sync_mtp_timestamp():
            return False
        if not self.nic_prompt_cfg():
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
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_DIAG_STOP_PICOCOM_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["$"], timeout=3)

        con_ts = libmfg_utils.timestamp_snapshot()
        ts_record_cmd = "#######= {:s} =#######".format(str(con_ts))
        self._nic_handle.sendline(ts_record_cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["$"], timeout=4)

        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_CON_ATTACH_FMT.format(self._slot+1))
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["Terminal ready"], timeout=2)
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
            return False
        if not self.nic_prompt_cfg():
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
        self.mtp_exec_cmd(MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT)
        self._cmd_buf = cmd_buf             #reset the cmd_buf to failure buffer

    def nic_mgmt_config(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # config the mgmt port
        cmd = MFG_DIAG_CMDS.NIC_SET_MGMT_IP_FMT.format(self._slot+101)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.after)
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self.nic_set_status(NIC_Status.NIC_STA_OK)
        return True

    def nic_set_extdiag_boot(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # set default to extdiag boot
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_SET_EXTDIAG_BOOT_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS.NIC_SET_EXTDIAG_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
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

    def nic_erase_board_config(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # earse board config
        self._nic_handle.sendline(MFG_DIAG_CMDS.ERASE_BOARD_CONFIG_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    def nic_cpld_update_request(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # get diag boot
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_SHOW_RUNNING_IMG_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"(goldfw)", buf)
        if not match:
            self.nic_console_detach()
            return False

        #self.nic_boot_info_reset()


        # get cpld version
        self._nic_handle.sendline("cpldapp -r 0")
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"(0x83)", buf)
        if not match:
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    def nic_set_board_config_cert(self, cert_img, directory="/data/"):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        img_name = os.path.basename(cert_img)
        # set ibm board config
        self._nic_handle.sendline(MFG_DIAG_CMDS.SET_IBM_BOARD_CONFIG_FMT.format(directory, img_name))
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"(Config successfully)", buf)
        if not match:
            self.nic_console_detach()
            return False

        # show cert info
        self._nic_handle.sendline(MFG_DIAG_CMDS.GET_BOARD_CONFIG_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"(cert 1 serial: 34:f7:c4:37:67:cf:39:e7:4a:a5:6d:80:b6:b1:66:bf:29:53:f9:7f)", buf)
        if not match:
            self.nic_console_detach()
            return False

        # show fwupdate -l info
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_IMG_DISP1_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    def nic_secboot_verify(self):
        if not self.nic_console_attach():
            self.nic_set_err_msg("Unable to connect to NIC console")
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # send bash command elba-chk-secboot-rdy.sh and it's leading commands
        nic_secboot_verify_cmd_list = [MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT, MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT, MFG_DIAG_CMDS.NIC_CHK_SECBOOT_FMT]
        for nic_cmd in nic_secboot_verify_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
                self.nic_console_detach()
                return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"SUCCESS", buf)
        if not match:
            self.nic_console_detach()
            return False          

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    def nic_cfg_verify(self):
        if not self.nic_console_attach():
            self.nic_set_err_msg("Unable to connect to NIC console")
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # dump cfg0
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_CFG_DUMP_FMT.format("4","0"))
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_err_msg("Unable to get response after issue dump cfg0 command")
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # dump cfg1
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_CFG_DUMP_FMT.format("5","1"))
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_err_msg("Unable to get response after issue dump cfg1 command")
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # md5sum cfg0
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_CFG_CHECKSUM_FMT.format("0"))
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_err_msg("Unable to get response after issue md5sum cfg0 command")
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # md5sum cfg1
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_CFG_CHECKSUM_FMT.format("1"))
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_err_msg("Unable to get response after issue md5sum cfg1 command")
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    def nic_set_diag_boot(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # set default to diag boot
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_SET_DIAG_BOOT_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS.NIC_SET_DIAG_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True
        
    def nic_set_mainfw_boot(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # set default to mainfw boot
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_SET_SW_BOOT_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS.NIC_SET_SW_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True
    def nic_set_goldfw_boot(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # set default to goldfw boot
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_SET_GOLD_BOOT_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS.NIC_SET_GOLD_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    def nic_set_extos_boot(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # set default to extosa boot
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_SET_EXTOSA_BOOT_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        self.nic_boot_info_reset()

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # show and compare startup image
        expect_startup_img = MFG_DIAG_CMDS.NIC_SET_EXTOSA_BOOT_FMT.replace("fwupdate -s", "").strip()
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FW_SET_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False
        if expect_startup_img not in self._nic_handle.before:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True


    def nic_sw_cleanup_shutdown(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # 1. remove diag utils on NIC
        # 2. kill all processes
        # 3. sync
        # 4. umount
        emmc_fsck_cmd = MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT
        emmc_mount_cmd = MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT
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
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_console_detach()
                return False

        # poweroff
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_OS_SHUTDOWN_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [MFG_DIAG_SIG.NIC_OS_SHUTDOWN_OK_SIG], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_console_detach()
            return False

        self.nic_console_detach()
        return True

    def nic_sw_shutdown(self, cloud=False, isRelC=False):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # 1. remove diag utils on NIC
        # 2. kill all processes
        # 3. sync
        # 4. umount
        emmc_fsck_cmd = MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT
        emmc_mount_cmd = MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT
        nic_shutdown_cmd_list = [emmc_fsck_cmd,
                                 emmc_mount_cmd,
                                 MFG_DIAG_CMDS.NIC_IMG_DISP_FMT,
                                 MFG_DIAG_CMDS.NIC_IMG_DISP1_FMT,
                                 MFG_DIAG_CMDS.NIC_DIAG_CLEANUP_FMT,
                                 MFG_DIAG_CMDS.NIC_EMMC_LS_FMT,
                                 MFG_DIAG_CMDS.NIC_KILL_PROCESS_FMT,
                                 MFG_DIAG_CMDS.NIC_SYNC_FS_FMT,
                                 MFG_DIAG_CMDS.NIC_SW_UMOUNT_FMT]

        if self._nic_type == NIC_Type.ORTANO2ADIMSFT:
            nic_shutdown_cmd_list.pop()
            nic_shutdown_cmd_list.append(MFG_DIAG_CMDS.NIC_SYNC_FS_FMT)
            nic_shutdown_cmd_list.append(MFG_DIAG_CMDS.NIC_SYNC_FS_FMT)
            
        for nic_cmd in nic_shutdown_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_console_detach()
                return False

        # poweroff ... Cloud build do not support this command & different command for Rel C
        if isRelC == True:
            self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_OS_SHUTDOWN_PEN_FMT)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [MFG_DIAG_SIG.NIC_OS_SHUTDOWN_OK_SIG], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False           
        elif cloud == False:
            self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_OS_SHUTDOWN_FMT)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [MFG_DIAG_SIG.NIC_OS_SHUTDOWN_OK_SIG], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False

        self.nic_console_detach()
        return True

    def nic_set_elba_uboot_env(self, slot):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("Execute command {:s} failed".format(cmd))
            return False
        nic_test_uboot_env = MFG_DIAG_CMDS.MTP_PARA_UBOOT_ENV_FMT.format(str(slot+1))
        if not self.mtp_exec_cmd(nic_test_uboot_env):
            self.nic_set_err_msg("nic_test.py -setup_uboot_env failed")
            return False
        return True

    def nic_sw_mode_switch(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        mode_switch_cmd_list = [MFG_DIAG_CMDS.NIC_SW_MODE_SWITCH_FMT,
                                MFG_DIAG_CMDS.NIC_SW_MODE_SWITCH_FMT,
                                "sync"]
        for nic_cmd in mode_switch_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False

        self._nic_handle.sendline("sysreset.sh")
        time.sleep(MTP_Const.NIC_SYSRESET_DELAY)
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_console_detach()
            return False
        self.nic_console_detach()
        return True

    def nic_sw_mode_switch_verify(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_console_detach()
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_SW_DEVICE_CHK_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_console_detach()
            return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        dev_profile_match = re.findall(MFG_DIAG_SIG.NIC_SW_DEVICE_CHK_SIG1, cmd_buf)
        if dev_profile_match:
            pass
        else:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_console_detach()
            return False

        mode_match = re.findall(MFG_DIAG_SIG.NIC_SW_DEVICE_CHK_SIG2, cmd_buf)
        if mode_match:
            pass
        else:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_console_detach()
            return False

        self.nic_console_detach()
        return True

    def nic_pdsctl_system_show(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_console_detach()
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_SW_SYSTEM_CHK_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_console_detach()
            return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        die_id_match = re.findall(MFG_DIAG_SIG.NIC_SW_SYSTEM_CHK_SIG1, cmd_buf)
        if die_id_match:
            pass
        else:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_console_detach()
            return False

        self.nic_console_detach()
        return True

    def nic_set_i2c_after_pw_cycle(self):
        if not self.nic_console_attach_fast():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_err_msg("Unable to connect to NIC console")
            return False
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Unable to get expected prompt")
            self.nic_console_detach_fast()
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_I2C_SET_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Execute command {:s} failed".format(MFG_DIAG_CMDS.NIC_I2C_SET_FMT))
            self.nic_console_detach_fast()
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Execute command {:s} failed".format(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT))
            self.nic_console_detach_fast()
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Execute command {:s} failed".format(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT))
            self.nic_console_detach_fast()
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_WRITE_CPLD_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Execute command {:s} failed".format(MFG_DIAG_CMDS.NIC_WRITE_CPLD_FMT))
            self.nic_console_detach_fast()
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_READ_CPLD_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=2)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_set_err_msg("Execute command {:s} failed".format(MFG_DIAG_CMDS.NIC_READ_CPLD_FMT))
            self.nic_console_detach_fast()
            return False
        
        # cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        # match = re.findall(r".*(0x44).*", cmd_buf)
        # if match:
        #     pass
        # else:
        #     self.nic_set_cmd_buf(cmd_buf)
        #     self.nic_set_err_msg("Incorrect I2C value, expecting {:s}, got {:s}".format("0x44", cmd_buf.strip()))
        #     self.nic_console_detach_fast()
        #     return False

        self.nic_console_detach_fast()
        return True

    def nic_boot_info_init(self, smode=False):
        # save boot image info into self._boot_image and self._kernel_timestamp
        loop = 0
        while loop < MTP_Const.NIC_CON_CMD_RETRY:
            if not self.nic_console_attach():
                loop += 1
                continue

            if smode:
                self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_SHOW_STARTUP_IMG_FMT)
            else:
                self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_SHOW_RUNNING_IMG_FMT)

            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
            if idx < 0:
                self.nic_console_detach()
                loop += 1
                continue

            # remove the potential special character
            buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            match = re.findall(r"(\w+fw\w?|extdiag)", buf)
            if match:
                self._boot_image = match[0]
                # check if boot image is valid
                if self._boot_image in MFG_VALID_FW_LIST:
                    self.nic_console_detach()
                    break
                else:
                    self.nic_console_detach()
                    loop += 1
                    continue
            else:
                self.nic_console_detach()
                loop += 1
                continue

        if loop >= MTP_Const.NIC_CON_CMD_RETRY:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        # get kernel build timestamp
        loop = 0
        while loop < MTP_Const.NIC_CON_CMD_RETRY:
            if not self.nic_console_attach():
                loop += 1
                continue

            self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_IMG_VER_DISP_FMT)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_CMD_DELAY_10)
            if idx < 0:
                self.nic_console_detach()
                loop += 1
                continue

            # remove the potential special character
            buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            match = re.findall(r"SMP(?: PREEMPT)? (.* 20\d{2})", buf)
            if match:
                kernel_ver = match[0]
                # check if timestamp is valid
                try:
                    dt = datetime.strptime(kernel_ver, "%a %b %d %X %Z %Y")
                    self._kernel_timestamp = dt.strftime("%m-%d-%Y")
                    self.nic_console_detach()
                    break
                except ValueError:
                    self.nic_console_detach()
                    loop += 1
                    continue
            else:
                self.nic_console_detach()
                loop += 1
                continue

        if loop >= MTP_Const.NIC_CON_CMD_RETRY:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

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
            cmd = MFG_DIAG_CMDS.MTP_NIC_PCIE_LINK_POLL_ENABLE_FMT.format(self._slot+1)
        else:
            sig = MFG_DIAG_SIG.NIC_UBOOT_PCIE_DIS_SIG
            cmd = MFG_DIAG_CMDS.MTP_NIC_PCIE_LINK_POLL_DISABLE_FMT.format(self._slot+1)
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
            cmd = MFG_DIAG_CMDS.NIC_FPO_MGMT_INIT_FMT.format(self._slot+1)
        else:
            cmd = MFG_DIAG_CMDS.NIC_MGMT_INIT_FMT.format(self._slot+1)
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

        cmd = MFG_DIAG_CMDS.NIC_CON_MTEST_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
            return False
        if MFG_DIAG_SIG.NIC_CON_MTEST_PASS_SIG in self.nic_get_cmd_buf():
            return True
        else:
            return False

    def nic_check_jtag(self, asic_support):
        cmd = MFG_DIAG_CMDS.NIC_JTAG_TEST_FMT.format(self._slot+1)

        fail_sig_list = ["JTAG Read failed!"]

        sig_list = ["valid bit 0x1", "error 0x00"]
        if asic_support == MTP_ASIC_SUPPORT.ELBA:
            sig_list = ["0x00000001"]
        elif asic_support == MTP_ASIC_SUPPORT.TURBO_ELBA:
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
        cmd = MFG_DIAG_CMDS.NIC_POWER_CHECK_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_PWR_FAIL)
            return False

        if MFG_DIAG_SIG.NIC_POWER_OK_SIG in self.nic_get_cmd_buf():
            return True
        else:
            self.nic_set_status(NIC_Status.NIC_STA_PWR_FAIL)
            # dump power rail status
            cmd = MFG_DIAG_CMDS.NIC_POWER_RAIL_DISP_FMT.format(self._slot+1)
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
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FRU_DUMP_FMT)
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
        cmd = MFG_DIAG_CMDS.MTP_NIC_FRU_DUMP_FMT.format(self._slot+1)
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
        cmd = MFG_DIAG_CMDS.MTP_OCP_ADAP_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
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

    def nic_copy_compressed_image(self, src_directory, src_img, dst_directory, timeout=MTP_Const.OS_CMD_DELAY):
        """
        Send file to NIC from MTP.

        Same function as nic_copy_image but uses ssh connection to transfer characters, 
        while doing tar & untar before & after. Tar on MTP and untar on NIC.
        """
        signatures = ["No such file", "Exiting with failure"]
        cmd = MFG_DIAG_CMDS.NIC_SCP_COMPRESSED_FMT.format(src_directory, src_img, NIC_MGMT_USERNAME, libmfg_utils.get_nic_ip_addr(self._slot), libmfg_utils.get_ssh_option(), dst_directory)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, signatures + ["assword:"], timeout=MTP_Const.SSH_PASSWORD_DELAY)
        if idx < 0:
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg("Couldn't get password prompt")
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        if idx == 0 or idx == 1:
            self.nic_set_err_msg("Missing file {:s}".format(src_directory+"/"+src_img))
            self.nic_set_cmd_buf(self._nic_handle.before + signatures[idx])
            return False

        self._nic_handle.sendline(NIC_MGMT_PASSWORD)
        idx = libmfg_utils.mfg_expect(self._nic_handle, signatures + [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg("NIC hung while copying")
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        if idx == 0 or idx == 1:
            self.nic_set_err_msg("Missing file {:s}".format(src_directory+"/"+src_img))
            self.nic_set_cmd_buf(self._nic_handle.before + signatures[idx])
            return False

        # send a sync on NIC
        self.nic_exec_cmds(["ls -l {:s}/{:s}".format(dst_directory, src_img)])

        return True

    def nic_verify_fpga(self, cpld_img, partition=""):
        if not self.nic_copy_image(cpld_img):
            return False
        img_name = os.path.basename(cpld_img)
        if self._nic_type in ELBA_NIC_TYPE_LIST and self._nic_type in FPGA_TYPE_LIST:
            nic_cmd_list = list()
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FPGA_DUMP_FMT.format("", img_name, partition))
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
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
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
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            self.nic_set_err_msg("Missing file {:s}".format(src_file))
            self.nic_set_cmd_buf(self._nic_handle.before + fail_signatures[idx])
            return False

        self.mtp_exec_cmd("ls -l {:s}".format(os.path.dirname(dst_file)))

        return True

    def nic_sw_profile(self, profile):
        if not self.nic_copy_image("/home/diag/mtp_swi_script/{:s}".format(profile)):
            return False

        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd = MFG_DIAG_CMDS.NIC_SW_PROFILE_CMD_FMT.format(profile)
        self._nic_handle.sendline(nic_cmd)
        idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_console_detach()
            return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        if MFG_DIAG_SIG.NIC_SW_PROFILE_FAIL_SIG in cmd_buf:
            self.nic_set_err_msg("Failed to apply profile")
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return False

        self.nic_set_cmd_buf(self._nic_handle.before)
        self.nic_console_detach()
        return True


    def nic_program_cpld(self, cpld_img, partition="cfg0"):
        """
          Program CPLD or Secure CPLD
        """
        if not self.nic_copy_image(cpld_img):
            return False
        img_name = os.path.basename(cpld_img)
        # failsafe_name = os.path.basename(failsafe_img)

        nic_cmd_list = list()
        # Elba-based:
        if self._nic_type in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) and self._nic_type not in FPGA_TYPE_LIST:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_CPLD_PROG_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, img_name, partition))
            timeout = MTP_Const.OS_CMD_DELAY
        elif self._nic_type in ELBA_NIC_TYPE_LIST and self._nic_type in FPGA_TYPE_LIST:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FPGA_PROG_FMT.format("", img_name, partition))
            timeout = MTP_Const.NIC_FPGA_PROG_DELAY
        # Capri-based:
        else:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_CPLD_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, img_name))
            timeout = MTP_Const.OS_CMD_DELAY

        if self._nic_type == NIC_Type.NAPLES25OCP:
            if not self.nic_exec_rst_cmd(nic_cmd_list[0], timeout=MTP_Const.OS_CMD_DELAY):
                return False
        else:
            if not self.nic_exec_cmds(nic_cmd_list, timeout=timeout):
                return False

        return True

    def set_nic_diagfw_boot(self):
        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_SET_DIAG_BOOT_FMT)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.NIC_FW_SET_DELAY):
            return False

        return True

    def nic_refresh_cpld(self, dontwait=False):
        # Capri-based:
        nic_cpld_ref_cmd = MFG_DIAG_CMDS.NIC_CPLD_REF_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        # Elba-based:
        if self._nic_type in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) and self._nic_type not in FPGA_TYPE_LIST:
            nic_cpld_ref_cmd = MFG_DIAG_CMDS.NIC_CPLD_REF_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
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

        nic_cmd = MFG_DIAG_CMDS.NIC_SETTING_PARTITION_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
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
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_EMMC_HWRESET_SET_FMT)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=10):
            return False
        return True

    def nic_emmc_hwreset_verify(self):
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_HWRESET_CHECK_FMT
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
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_EMMC_BKOPS_EN_FMT)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=10):
            return False
        return True

    def nic_emmc_bkops_verify(self):
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_BKOPS_CHECK_FMT
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

    def nic_read_emmc_id(self):
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_READ_ID_FMT
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

        cmd = MFG_DIAG_CMDS.NIC_ESEC_PROG_QSPI_DUMP_FMT.format(self._slot+1, mode)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_dump_cpld(self, partition, file_path="/home/diag/cplddump"):
        cmd = MFG_DIAG_CMDS.NIC_CPLD_DUMP_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, file_path, partition)
        nic_cmd_list = list()
        nic_cmd_list.append(cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        return True

    def nic_compare_cpld_file(self, cpld_image, dump_cpld_image, partition):
        nic_cmd = MFG_DIAG_CMDS.NIC_CPLD_DUMP_COMPARE_FMT.format(os.path.basename(cpld_image), os.path.basename(dump_cpld_image))
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

        cmd = MFG_DIAG_CMDS.NIC_ESEC_CPLD_CHECK_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        # save result buffer
        cmd_buf = self.nic_get_cmd_buf()

        cmd = MFG_DIAG_CMDS.NIC_ESEC_ERR_CHECK_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_ESEC_CPLD_VERIFY_SIG not in cmd_buf:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_program_sec_key_dump(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS.NIC_ESEC_PROG_DUMP_FMT.format(self._sn, self._slot+1, self._nic_type)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True


    def nic_program_sec_key_pre(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        cmd = MFG_DIAG_CMDS.NIC_ESEC_PROG_PRE_FMT.format(self._slot+1)
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

        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            cmd = MFG_DIAG_CMDS.NIC_ESEC_PROG_ELBA_FMT.format(self._slot+1,
                                                         self._sn,
                                                         self._pn,
                                                         self._mac.replace('-',':'),
                                                         self._nic_type,
                                                         mtpid)
        else:
            # program secure key with (slot, sn, pn, mac, type, mtpid)
            cmd = MFG_DIAG_CMDS.NIC_ESEC_PROG_FMT.format(self._slot+1,
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

        cmd = MFG_DIAG_CMDS.NIC_ESEC_PROG_POST_FMT
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_ESEC_PROG_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_program_efuse(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ESEC_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if self._nic_type not in ELBA_NIC_TYPE_LIST and self._nic_type not in GIGLIO_NIC_TYPE_LIST:
            return False

        cmd = MFG_DIAG_CMDS.NIC_EFUSE_PROG_ELBA_FMT.format(self._slot+1,
                                                     self._sn,
                                                     self._pn,
                                                     self._mac.replace('-',':'),
                                                     self._nic_type)
        # if not GLB_CFG_MFG_TEST_MODE:
        #     cmd = MFG_DIAG_CMDS.NIC_EFUSE_PROG_ELBA_MODEL_FMT.format(self._slot+1,
        #                                                              self._sn,
        #                                                              self._pn,
        #                                                              self._mac.replace('-',':'),
        #                                                              self._nic_type)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_EFUSE_PROG_DELAY):
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_EFUSE_PROG_FAIL_SIG in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False
        if MFG_DIAG_SIG.NIC_EFUSE_PROG_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_program_qspi(self, qspi_img):
        if not self.nic_copy_image(qspi_img):
            return False
        img_name = os.path.basename(qspi_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_QSPI_PROG_FMT.format(img_name)
        qspi_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)
  
        if not self.nic_exec_cmds(nic_cmd_list, fail_sig=qspi_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        cmd_buf = self._nic_handle.before
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False

        self.nic_boot_info_reset()

        return True

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
        nic_cmd = MFG_DIAG_CMDS.NIC_GOLDFW_PROG_FMT.format(img_name, img_name)
        if self._nic_type == NIC_Type.NAPLES100:
            nic_cmd = MFG_DIAG_CMDS.NIC_GOLDFW_PROG_FMT_NAPLES100.format(img_name)
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
        nic_cmd = MFG_DIAG_CMDS.NIC_UBOOT_PROG_FMT.format(installer_path, uboot_pat, img_name)
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
            nic_cmd = MFG_DIAG_CMDS.NIC_UBOOT_PROG_FMT.format(installer_path, "golduboot", img_name)
            qspi_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
            nic_cmd_list.append(nic_cmd)

            if not self.nic_exec_cmds(nic_cmd_list, fail_sig=qspi_fail_sig):
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

        self.nic_boot_info_reset()

        return True

    def nic_init_emmc(self, init=False, emmc_check=False):
        if init:
            if not self.nic_read_emmc_id():
                return False

        nic_cmd_list = list()
        if emmc_check and self._nic_type in PSLC_MODE_TYPE_LIST:
            nic_cmd = MFG_DIAG_CMDS.NIC_CHECK_EMMC_FMT
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
            nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_INIT_FMT
            nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_PARTITION_DISP_FMT)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        # check if mount is ok
        nic_cmd = MFG_DIAG_CMDS.NIC_MOUNT_DISP_FMT
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

        nic_cmd = MFG_DIAG_CMDS.NIC_IMG_DISP1_FMT
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
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_PERF_MODE
        nic_cmd_list.append(nic_cmd)
        nic_cmd_list.append("sync")
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        # check if successful
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_PERF_MODE_CHECK
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
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_PERF_MODE_CHECK
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
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_INIT_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_PROG_FMT.format(img_name, img_name)
        # if self._nic_type == NIC_Type.NAPLES100:
        #     nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_PROG_FMT_NAPLES100.format(img_name) # 90-0001-0001 does not have fwupdate binary packaged
        nic_cmd_list.append(nic_cmd)
        if self._nic_type not in FPGA_TYPE_LIST:
            nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_B_PROG_FMT.format(img_name, img_name)
            nic_cmd_list.append(nic_cmd)
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd = MFG_DIAG_CMDS.NIC_BOOT0_PROG_FMT.format(img_name, img_name)
            nic_cmd_list.append(nic_cmd)
        emmc_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY, fail_sig=emmc_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        self.nic_boot_info_reset()

        return True


    def nic_setup_diag_img(self, nic_diag_image, nic_asic_image="", emmc_utils=False):
        # if emmc_utils: arm64 diag image on NIC will be updated
        if emmc_utils:
            if self._nic_type == NIC_Type.NAPLES100:
                # programmed fw does not support unpacking gzip. untar on MTP and copy one by one into /data/.
                nic_diag_list = ["diag", "nic_arm", "nic_util", "start_diag.arm64.sh"]
                for util in nic_diag_list:
                    if not self.nic_copy_compressed_image(
                        src_directory=MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH,
                        src_img=util,
                        dst_directory=MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH,
                        timeout=180):
                        return False

            else:
                # copy image_arm64 from MTP and untar it into /data/
                if not self.nic_copy_image(nic_diag_image, MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH):
                    return False

                nic_cmd_list = list()
                nic_cmd = MFG_DIAG_CMDS.NIC_UNTAR_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+os.path.basename(nic_diag_image), MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH)
                nic_cmd_list.append(nic_cmd)
                if not self.nic_exec_cmds(nic_cmd_list, timeout=300):
                    return False

                # for CI/CD, copy independent asic lib to /data
                if nic_asic_image:
                    if not self.nic_copy_image(nic_asic_image, MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH):
                        return False

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH)
        nic_cmd_list.append(nic_cmd)
        nic_cmd = "sync"
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.MFG_DIR_LINK_FMT.format("/data/diag/", MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH+"/diag")
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.MFG_DIR_LINK_FMT.format("/data/start_diag.arm64.sh", MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH+"/start_diag.arm64.sh")
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
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(dst_log_dir)
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
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_FINI_FMT
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        return True


    def nic_diag_clean(self):
  
        cmd = MFG_DIAG_CMDS.NIC_SYS_CLEAN_FMT.format(MTP_DIAG_Path.ONBOARD_MTP_MTP_DIAG_PATH)
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
                nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_HAL_FMT
                nic_cmd_list.append(nic_cmd)
                if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
                    return False

                nic_cmd = MFG_DIAG_CMDS.NIC_HAL_RUNNING_FMT
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
                nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_SYSMGR_FMT
                nic_cmd_list.append(nic_cmd)
                if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
                    return False

                nic_cmd = MFG_DIAG_CMDS.NIC_SYSMGR_RUNNING_FMT
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
                nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_SYSMOND_FMT
                nic_cmd_list.append(nic_cmd)
                if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
                    return False

                nic_cmd = MFG_DIAG_CMDS.NIC_SYSMOND_RUNNING_FMT
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

    def nic_start_diag(self, aapl, dis_hal=False):
        # setup diag env on nic
        nic_cmd_list = list()

        time_str = str(libmfg_utils.timestamp_snapshot())
        nic_cmd = MFG_DIAG_CMDS.NIC_DATE_SET_FMT.format(time_str)
        nic_cmd_list.append(nic_cmd)
        if not dis_hal:
            if not aapl:
                self.nic_kill_hal()
                nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_HAL_FMT
                nic_cmd_list.append(nic_cmd)
                # prevent cpldapp lock getting stuck which depends on hal
                nic_cmd = "rm /var/lock/cpldapp_lock"
                nic_cmd_list.append(nic_cmd)
                nic_cmd = "rm /dev/shm/cpld_lock"
                nic_cmd_list.append(nic_cmd)
                nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_CONFIG_FMT
                nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_INIT_FMT.format(self._slot+1)
        nic_cmd_list.append(nic_cmd)
        nic_cmd = "source /etc/profile"
        nic_cmd_list.append(nic_cmd)

        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.nic_set_err_msg("Unable to stop HAL")
            return False

        # Start NIC DSP
        cmd = MFG_DIAG_CMDS.NIC_DSP_START_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
            self.nic_set_err_msg("Unable to start diagmgr")
            return False

        # get asic lib version
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_ASIC_VERSION_FMT.format(self._asic_type)
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to get nic asic version")
            return False
        match = re.findall(r"Date: +(.*20\d{2})", cmd_buf)
        if match:
            self._diag_asic_ver = match[0]
        else:
            self.nic_set_err_msg("Unable to find nic asic version. Is this MTP converted for this ASIC?")
            return False

        if self._nic_type in GIGLIO_NIC_TYPE_LIST:
            self.nic_exec_cmds(["ls /data/nic_arm/", "du -a /data/nic_arm/giglio/ -d3"])
        else:
            self.nic_exec_cmds(["ls /data/nic_arm/", "du -a /data/nic_arm/elba/ -d3"])

        # get emmc nic utils version
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_UTIL_VERSION_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to get nic utils version")
            return False
        match = re.findall(r"Date: +(.*20\d{2})", cmd_buf)
        if match:
            self._diag_util_ver = match[0]
        else:
            self.nic_set_err_msg("Unable to find nic utils version")
            return False

        # get nic diag version
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_VERSION_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to get nic diag version")
            return False
        match = re.findall(r"Date: +(.*20\d{2})", cmd_buf)
        if match:
            self._diag_ver = match[0]
        else:
            self.nic_set_err_msg("Unable to find nic diag version")
            return False

        # check if hal is running
        nic_cmd = MFG_DIAG_CMDS.NIC_HAL_RUNNING_FMT
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
        nic_cmd = MFG_DIAG_CMDS.NIC_VMARG_SET_FMT.format(vmarg_param, str(percentage))
        nic_cmd_list.append(nic_cmd)

        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        return True

    def nic_display_voltage(self):
        nic_cmd = [MFG_DIAG_CMDS.NIC_DISP_VOLT_FMT]
        if not self.nic_exec_cmds(nic_cmd):
            return False
        return True

    def nic_set_sw_boot(self):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_SET_SW_BOOT_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_BOOT_SHOW_STARTUP_IMG_FMT)
        if not self.nic_exec_cmds(nic_cmd_list):
            return False

        return True


    def nic_set_gold_boot(self):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_SET_GOLD_BOOT_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_BOOT_SHOW_STARTUP_IMG_FMT)
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
            NIC_Type.ORTANO2SOLO: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_PN_FMT)               #68-0077-01 XX    ORTANO2 SOLO
                ],
            NIC_Type.ORTANO2SOLOORCTHS: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_THS_PN_FMT)           #68-0089-01 XX    ORTANO2 SOLO Tall Heat Sink
                ],
            NIC_Type.ORTANO2SOLOMSFT: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2SOLO_MSFT_PN_FMT)              #68-0090-01 XX    ORTANO2 SOLO MICROSOFT
                ],
            NIC_Type.ORTANO2SOLOALI: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2SOLO_ALI_PN_FMT)               #68-0092-01 XX    ORTANO2 SOLO Alibaba
                ],
            NIC_Type.ORTANO2ADICR: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2ADI_CR_PN_FMT)                 #68-0049-03 XX    ORTANO2ADI CR
                ],
            NIC_Type.ORTANO2ADICRMSFT: [
                (ASSY_NUM_FIELD, PART_NUMBERS_MATCH.ORTANO2ADI_CR_MSFT_PN_FMT)            #68-0091-01 XX    ORTANO2ADI CR MICROSOFT
                ],
            NIC_Type.POMONTEDELL: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.POMONTEDELL_PN_FMT)                   #0PCFPC X/A       POMONTE DELL
                ],
            NIC_Type.LACONA32DELL: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.LACONA32DELL_PN_FMT)                  #0X322F X/A       LACONA32 DELL
                ],
            NIC_Type.LACONA32: [
                (PART_NUM_FIELD, PART_NUMBERS_MATCH.LACONA32_PN_FMT)                      #P47930-001       LACONA32 HPE
                ]

        }
        if self._nic_type not in pn_table.keys():
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
        if self._nic_type not in pn_table.keys():
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
                (PROD_NUM_FIELD, "P26969\-B21")
                ]
        }
        if self._nic_type not in pn_table.keys():
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

    def nic_read_fru(self, fpo=False, smb_fru=False, alom=False, ocp_adap=False):
        cmd = "eeutil -disp -dev=fru"
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
            cmd += " -uut=UUT_{:d}".format(self._slot+1)
            fru_buf = self.mtp_get_info(cmd)
        else:
            fru_buf = self.nic_get_info(cmd)

        return fru_buf

    def nic_write_fru(self, date, sn, mac, pn, nic_type=None, smb_fru=False):
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
        else:
            cmd = "eeutil -dev=fru -update -erase -numBytes=512"
        
        cmd += " -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}'".format(date, sn, mac, pn)

        if smb_fru:
            cmd += " -uut=UUT_{:d}".format(self._slot+1)
            cmd_buf = self.mtp_get_info(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY)
        else:
            cmd_buf = self.nic_get_info(cmd)

        if not cmd_buf:
            if smb_fru:
                self.nic_set_err_msg("Unable to program SMB FRU")
            else:
                self.nic_set_err_msg("Unable to program ASIC FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        match = re.findall(r"FRU Checkum and Type\/Length Checks Passed|EEPROM updated", cmd_buf)
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

    def nic_cpld_init(self, smb=False):
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

        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
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
            return [self._cpld_ver, self._cpld_timestamp, self._cpld_id]


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

    def nic_console_read_i2c(self, bus_num, dev_addr, reg_addr, read_data):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd = "i2cget -y {:d} {:x} {:x}".format(bus_num, dev_addr, reg_addr)
        self._nic_handle.sendline(nic_cmd)
        idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.nic_console_detach()
            return False
        cpld_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cpld_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        match = re.findall(r"(0x[0-9a-fA-F]+)", cpld_buf)

        if len(match) >= 1:
            read_data[0] = int(match[0], 16)
        else:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cpld_buf)
            return False

        self.nic_set_cmd_buf(self._nic_handle.before)
        self.nic_console_detach()
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
        cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return None

        reg_addr = 0x26
        cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(self._slot+1) + " ;" + MFG_DIAG_CMDS.MTP_SMB_RD_CPLD_FMT.format(reg_addr, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return None
        match = re.findall(pll_sta_reg_exp % reg_addr, self.nic_get_cmd_buf())
        if not match:
            return None
        else:
            reg26_data = int(match[0], 16)

        reg_addr = 0x28
        cmd = MFG_DIAG_CMDS.MTP_SMB_RD_CPLD_FMT.format(reg_addr, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return None
        match = re.findall(pll_sta_reg_exp % reg_addr, self.nic_get_cmd_buf())
        if not match:
            return None
        else:
            reg28_data = int(match[0], 16)

        return [reg26_data, reg28_data]

    def nic_read_cpld(self, reg_addr, read_data):
        nic_cmd = MFG_DIAG_CMDS.NIC_CPLD_READ_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, reg_addr)
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd = MFG_DIAG_CMDS.NIC_CPLD_READ_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, reg_addr)
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
        nic_cmd = MFG_DIAG_CMDS.NIC_CPLD_WRITE_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, reg_addr, write_data)
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd = MFG_DIAG_CMDS.NIC_CPLD_WRITE_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, reg_addr, write_data)
        cpld_buf = self.nic_get_info(nic_cmd)
        if not cpld_buf:
            return False
        return True

    def nic_console_read_cpld(self, reg_addr, read_data):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_CPLD_READ_ELBA_FMT.format("./", reg_addr))
        else:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_CPLD_READ_FMT.format("./", reg_addr))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cpld_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cpld_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        match = re.findall(r"(0x[0-9a-fA-F]+)", cpld_buf)
  
        if len(match) > 1:
            read_data[0] = int(match[1], 16)
        else:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cpld_buf)
            return False

        self.nic_set_cmd_buf(self._nic_handle.before)
        self.nic_console_detach()
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
        cmd = MFG_DIAG_CMDS.MTP_NIC_PING_FMT.format(ipaddr)
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
        cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS.MTP_RD_ALOM_CPLD_FMT.format(reg_addr, self._slot+1)
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
        cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS.MTP_WR_ALOM_CPLD_FMT.format(reg_addr, write_data, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False
        match = re.findall(r"failed", self.nic_get_cmd_buf())
        if match:
            return False
        return True

    def nic_read_cpld_via_smbus(self, reg_addr, read_data):
        cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS.MTP_SMB_RD_CPLD_FMT.format(reg_addr, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False
        match = re.findall(r"data=(0x[0-9a-fA-F]+)", self.nic_get_cmd_buf())
        if not match:
            return False
        else:
            read_data[0] = int(match[0], 16)
        return True

    def nic_write_cpld_via_smbus(self, reg_addr, write_data):
        cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return False

        cmd = MFG_DIAG_CMDS.MTP_SMB_WR_CPLD_FMT.format(reg_addr, write_data, self._slot+1)
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
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS.ORTANO2_VRM_FIX_FMT)
        if "Ortano2 VRM fix done" not in cmd_buf:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True

    def nic_fix_vrm_oc(self):
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS.ORTANO2_VRM_FIX_OC_FMT)
        if "FIX O2 VRM OC DONE" not in cmd_buf:
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

        """
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS.GET_BOARD_CONFIG_FMT)
        if not cmd_buf:
            self.nic_set_err_msg("Unable to get board config")
            return False
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS.SET_BOARD_CONFIG_FMT.format(preset_config))
        if not cmd_buf:
            self.nic_set_err_msg("Unable to set board config")
            return False
        if "Mode successfully set" in cmd_buf or "Config successfully set" in cmd_buf:
            pass
        else:
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS.GET_BOARD_CONFIG_FMT)
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

    def nic_assign_board_id(self, boardId=None):
        """
        assign passed in Board ID String to this board by utility board_config
        example:
        # assign, board_config -B 0x03610001
        # read and verify, board_config -b, got 0x03610001
        """

        if boardId is None:
            self.nic_set_err_msg("Please Provide Board ID")
            return False
        if not isinstance(boardId, str):
            self.nic_set_err_msg("Please Specify Board ID with String Format")
            return False

        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS.ASSIGN_BOARD_ID_FMT.format(boardId))
        if not cmd_buf:
            self.nic_set_err_msg("Assign Board ID Command 'board_config -B' Failed")
            return False
        # test string "Config successfully set" in command return buffer
        if "configsuccessfullyset" not in cmd_buf.replace(" ", "").lower():
            self.nic_set_err_msg("Assign Board ID NOT Success")
            self.nic_set_err_msg(cmd_buf)
            return False

        # Read Board ID back and compare
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS.READ_BOARD_ID_FMT)
        if not cmd_buf:
            self.nic_set_err_msg("Read Board ID Command 'board_config -b' Failed")
            return False
        if boardId.lower() not in cmd_buf.lower():
            self.nic_set_err_msg("Read Back and Compare Board ID Failed")
            self.nic_set_err_msg(cmd_buf)
            return False

        return True

    def nic_mvl_acc_test(self):
        if self._nic_type not in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) or self._nic_type in FPGA_TYPE_LIST:
            return False

        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_CHECK_HAL_FMT)
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MVL_ACC_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        if MFG_DIAG_SIG.NIC_MVL_ACC_SIG in cmd_buf:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return False

    def nic_mvl_stub_test(self, loopback=True):
        if self._nic_type not in (ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST) or self._nic_type in FPGA_TYPE_LIST:
            return False

        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_CHECK_HAL_FMT)
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        if loopback:
            external_loopback = "1"
        else:
            external_loopback = "0"
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MVL_STUB_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        if MFG_DIAG_SIG.NIC_MVL_STUB_SIG in cmd_buf:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return False

    def nic_mvl_link_test(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_BRINGUP_MGMT_FMT)
        nic_cmd_list.append("sleep 5") # wait for hal to come up before killing it
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_CHECK_HAL_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        if self._nic_type in CAPRI_NIC_TYPE_LIST:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MVL_LINK_CAPRI_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))
        else:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MVL_LINK_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        if MFG_DIAG_SIG.NIC_MVL_LINK_SIG in cmd_buf:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return False

    def nic_phy_xcvr_test(self):
        if self._nic_type not in FPGA_TYPE_LIST:
            return False

        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_CHECK_HAL_FMT)
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FPGA_PHY_TEST_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        if MFG_DIAG_SIG.NIC_FPGA_PHY_TEST_SIG in cmd_buf:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return False

    def nic_phy_xcvr_link_test(self):
        if self._nic_type not in FPGA_TYPE_LIST:
            return False

        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_CHECK_HAL_FMT)
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FPGA_PHY_LINK_TEST_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        if MFG_DIAG_SIG.NIC_FPGA_PHY_LINK_TEST_SIG in cmd_buf:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return False

    def nic_edma_test(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_STOP_HAL_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_DIAG_CHECK_HAL_FMT)
        if not self.nic_check_emmc_mounted():
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT)
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        nic_cmd_list.append("tar xf edma_test.tar.gz")

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_EDMA_TEST_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH+"nic_util/"))
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        if MFG_DIAG_SIG.NIC_EDMA_TEST_SIG in cmd_buf:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return True
        else:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return False

    def nic_check_emmc_mounted(self):
        # check if emmc is mounted. For use with console already attached.
        nic_cmd = MFG_DIAG_CMDS.NIC_MOUNT_DISP_FMT
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

    def nic_check_rebooted(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        nic_cmd_list.append("uptime")
        nic_cmd_list.append("dmesg | tail -n20")
        nic_cmd_list.append("dmesg | grep mmc")
        nic_cmd_list.append("mount")

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=10)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False

        ret = True
        if "/dev/mmcblk0p10" not in cmd_buf:
            self.nic_set_err_msg("EMMC not mounted")
            self.nic_set_cmd_buf(cmd_buf)
            ret &= False



        nic_cmd_list = list()
        nic_cmd_list.append("env | grep -v PS1")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=10)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = self._nic_handle.before
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False

        # if "CARD_NAME=NIC{:d}".format(self._slot+1) in cmd_buf:
        if "CARD_ENV=" in cmd_buf:
            ret &= True
        else:
            self.nic_set_err_msg("NIC was rebooted")
            ret &= False

        self.nic_console_detach()
        return ret

    def read_nic_temp(self, skip_reboot=False):
        if not self.mtp_exec_cmd(MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT):
            return False
        if not self.mtp_exec_cmd("cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)):
            return False

        cmd = "tclsh get_nic_sts.tcl {:s} {:d}".format(self._sn, self._slot+1)
        if skip_reboot:
            cmd += " 0" #skips VRM
        if not self.mtp_exec_cmd(cmd, timeout=180):
            self.nic_stop_test()
            return False
        self.nic_stop_test()
        return True

    def nic_port_counters(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        nic_cmd_list.append("halctl show port status")
        nic_cmd_list.append("halctl show port statistics --port eth1/3")    # BX port counters
        nic_cmd_list.append("halctl show port internal")                    # MVL switch port status
        nic_cmd_list.append("halctl show port internal statistics")         # all port counters

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=10)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False

        self.nic_console_detach()
        return True

    def nic_console_read_sgmii(self, port, reg_addr, read_data):

        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_SGMII_READ_ELBA_FMT.format("./", port, reg_addr))
        else:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_SGMII_READ_FMT.format("./", port, reg_addr))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cpld_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cpld_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        match = re.findall(r"0x%x\r\n(0x[0-9a-fA-F]+)" % reg_addr, cpld_buf)
        if len(match) > 0:
            read_data[0] = int(match[0], 16)
        else:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cpld_buf)
            return False

        self.nic_set_cmd_buf(self._nic_handle.before)
        self.nic_console_detach()
        return True

    def nic_console_write_sgmii(self, port, reg_addr, write_data):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT)
        nic_cmd_list.append(MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT)
        nic_cmd_list.append("cd {:s}nic_util/".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH))
        if self._nic_type in ELBA_NIC_TYPE_LIST or self._nic_type in GIGLIO_NIC_TYPE_LIST:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_SGMII_WRITE_ELBA_FMT.format("./", port, reg_addr, write_data))
        else:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_SGMII_WRITE_FMT.format("./", port, reg_addr, write_data))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False

        time.sleep(5)
        self.nic_set_cmd_buf(self._nic_handle.before)
        self.nic_console_detach()
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

    def nic_console_ping(self, to_slot):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        ipaddr = libmfg_utils.get_nic_ip_addr(to_slot)

        nic_cmd_list = list()
        nic_cmd_list.append(MFG_DIAG_CMDS.MTP_NIC_PING_FMT.format(ipaddr))

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False

        match = re.findall(r" 0% packet loss", cmd_buf)
        if match:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            return True

        self.nic_console_detach()
        self.nic_set_cmd_buf(cmd_buf)
        return False

    def nic_console_read_uboot(self):
        exp_boot0_version = ""
        exp_golduboot_version = ""

        if self._nic_type in FPGA_TYPE_LIST:
            exp_boot0_version = NIC_IMAGES.uboot_dat[self._nic_type]

        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        for loop in range(0,2):
            nic_cmd = "fwupdate -l"
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                self.nic_console_detach()
                return False
        
            try:
                fw_info = json.loads(r'{}'.format(self.nic_hide_prompt(cmd_buf.split("fwupdate -l")[1])))

                if exp_boot0_version != "" and 'boot0' not in fw_info:
                    self.nic_set_err_msg("Incorrect uboot type")
                    self.nic_console_detach()
                    self.nic_set_cmd_buf(cmd_buf)
                    return False

                if exp_boot0_version != "":
                    got_boot0_version = str(fw_info['boot0']['image']['image_version'])
                    if got_boot0_version != exp_boot0_version:
                        self.nic_set_err_msg("Incorrect boot0 version: {:s}, expecting: {:s}".format(got_boot0_version, exp_boot0_version))
                        self.nic_console_detach()
                        self.nic_set_cmd_buf(cmd_buf)
                        return False

                if exp_golduboot_version != "":
                    got_golduboot_version = str(fw_info['goldfw']['uboot']['software_version'])
                    if got_golduboot_version != exp_golduboot_version:
                        self.nic_set_err_msg("Incorrect uboot version")
                        self.nic_console_detach()
                        self.nic_set_cmd_buf(cmd_buf)
                        return False

                break

            except Exception as e:
                if loop == 1:
                    # weird characters read
                    self.nic_set_err_msg("Couldn't read uboot version")
                    self.nic_set_err_msg(traceback.format_exc())
                    self.nic_console_detach()
                    self.nic_set_cmd_buf(cmd_buf)
                    return False
                else:
                    continue

        self.nic_set_cmd_buf(self._nic_handle.before)
        self.nic_console_detach()
        return True

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

        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        for loop in range(0,2):
            nic_cmd = "fwupdate -l"
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                self.nic_console_detach()
                return False
        
            try:
                fw_info = json.loads(r'{}'.format(self.nic_hide_prompt(cmd_buf.split("fwupdate -l")[1])))
                if 'extosa' not in fw_info:
                    self.nic_set_err_msg("Missing extosa image")
                    self.nic_console_detach()
                    self.nic_set_cmd_buf(cmd_buf)
                    return False

                if exp_secure_boot != "":
                    got_secure_boot = str(fw_info['extosa']['kernel_fit']['secure_boot'])
                    if got_secure_boot != exp_secure_boot:
                        self.nic_set_err_msg("Incorrect secure_boot value: {:s}, expecting: {:s}".format(got_secure_boot, exp_secure_boot))
                        self.nic_console_detach()
                        self.nic_set_cmd_buf(cmd_buf)
                        return False

                if exp_secure_boot_keys != "":
                    got_secure_boot_keys = str(fw_info['extosa']['kernel_fit']['secure_boot_keys'])
                    if got_secure_boot_keys != exp_secure_boot_keys:
                        self.nic_set_err_msg("Incorrect secure_boot_keys value: {:s}, expecting: {:s}".format(got_secure_boot_keys, exp_secure_boot_keys))
                        self.nic_console_detach()
                        self.nic_set_cmd_buf(cmd_buf)
                        return False

                break

            except Exception as e:
                if loop == 1:
                    # weird characters read
                    self.nic_set_err_msg("Couldn't read extosa secure_boot fields")
                    self.nic_set_err_msg(traceback.format_exc())
                    self.nic_console_detach()
                    self.nic_set_cmd_buf(cmd_buf)
                    return False
                else:
                    continue

        self.nic_set_cmd_buf(self._nic_handle.before)
        self.nic_console_detach()
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

    def nic_console_vdd_ddr_fix(self, d3_val, d4_val, vddq_prog):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False


        nic_cmd_list = list()
        nic_cmd_list.append("i2cset -y 0 0x1c 0xd4 {:s}".format(d4_val))
        nic_cmd_list.append("i2cset -y 0 0x1c 0xd3 {:s}".format(d3_val))
        nic_cmd_list.append("i2cset -y 0 0x1c 0x11 c")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False

        if vddq_prog:
            nic_cmd_list = list()
            nic_cmd_list.append("i2cset -y 0 0x1b 0xd4 {:s}".format(d4_val))
            nic_cmd_list.append("i2cset -y 0 0x1b 0xd3 {:s}".format(d3_val))
            nic_cmd_list.append("i2cset -y 0 0x1b 0x11 c")
            for nic_cmd in nic_cmd_list:
                self._nic_handle.sendline(nic_cmd)
                idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
                if idx < 0:
                    self.nic_set_cmd_buf(self._nic_handle.before)
                    self.nic_console_detach()
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
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
    
        self.nic_console_detach()
        self.nic_set_cmd_buf(cmd_buf)
        return True

    def nic_console_vdd_ddr_check(self, d3_val, d4_val, vddq_prog):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False



        ### check frequency set ###
        nic_cmd_list = list()
        nic_cmd_list.append("i2cget -y 0 0x1c 0xd3")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        if d3_val not in cmd_buf:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("Incorrect VDD_DDR switching freq, expecting {:s}, got {:s}".format(d3_val, cmd_buf))
            return False



        ### check margin set ###
        nic_cmd_list = list()
        nic_cmd_list.append("i2cget -y 0 0x1c 0xd4")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        if d4_val not in cmd_buf:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("Incorrect VDD_DDR margin, expecting {:s}, got {:s}".format(d4_val, cmd_buf))
            return False



        ### check fwenvs cleared ###
        nic_cmd_list = list()
        nic_cmd_list.append("fwenv")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_console_detach()
            return False
        if any(x in cmd_buf for x in ["ddr_freq", "ddr_use_hardcoded_training", "ddr_vdd_margin", "ddr_ecc_writeback", "ddr_periodic_trg_en"]):
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("DDR fwenv setting not cleared")
            return False


        if vddq_prog:
            ### check frequency set ###
            nic_cmd_list = list()
            nic_cmd_list.append("i2cget -y 0 0x1b 0xd3")
            for nic_cmd in nic_cmd_list:
                self._nic_handle.sendline(nic_cmd)
                idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
                if idx < 0:
                    self.nic_set_cmd_buf(self._nic_handle.before)
                    self.nic_console_detach()
                    return False
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                self.nic_console_detach()
                return False
            if d3_val not in cmd_buf:
                self.nic_console_detach()
                self.nic_set_cmd_buf(cmd_buf)
                self.nic_set_err_msg("Incorrect VDDQ_DDR switching freq, expecting {:s}, got {:s}".format(d3_val, cmd_buf))
                return False



            ### check margin set ###
            nic_cmd_list = list()
            nic_cmd_list.append("i2cget -y 0 0x1b 0xd4")
            for nic_cmd in nic_cmd_list:
                self._nic_handle.sendline(nic_cmd)
                idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
                if idx < 0:
                    self.nic_set_cmd_buf(self._nic_handle.before)
                    self.nic_console_detach()
                    return False
            cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            if not cmd_buf:
                self.nic_set_err_msg("Buffer empty")
                self.nic_console_detach()
                return False
            if d4_val not in cmd_buf:
                self.nic_console_detach()
                self.nic_set_cmd_buf(cmd_buf)
                self.nic_set_err_msg("Incorrect VDDQ_DDR margin, expecting {:s}, got {:s}".format(d4_val, cmd_buf))
                return False

        self.nic_console_detach()
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
            cmd = MFG_DIAG_CMDS.NIC_L1_ESEC_PROG_FMT.format(self._slot+1)
        elif self._nic_type in GIGLIO_NIC_TYPE_LIST:
            cmd = MFG_DIAG_CMDS.NIC_L1_ESEC_GIGLIO_PROG_FMT.format(self._slot+1)

        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_L1_ESEC_PROG_DELAY):
            return False

        # check signature
        if MFG_DIAG_SIG.NIC_L1_ESEC_PROG_OK_SIG not in self.nic_get_cmd_buf():
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def nic_i2c_bus_scan(self):
        bus_list = [0, 1, 2]

        nic_cmd_list = list()

        for i2c_bus in bus_list:
            nic_cmd = MFG_DIAG_CMDS.NIC_I2C_DETECT_FMT.format(i2c_bus)
            nic_cmd_list.append(nic_cmd)

        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.NIC_I2C_DETECT_DELAY):
            return False

        return True

    def nic_read_transceiver_sn(self, port):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        if port not in ("0","1","2"):
            self.nic_set_err_msg("Script error: invalid port specified")
            return False

        nic_cmd_list = list()
        nic_cmd_list.append("chmod +x {:s}/diag/scripts/eeprom_sn.sh".format("/data/"))
        nic_cmd_list.append("{:s}/diag/scripts/eeprom_sn.sh -s -b {:s}".format("/data/", port))
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_set_err_msg("Can't read transceiver EEPROM")
                self.nic_console_detach()
                return False

        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Buffer empty")
            self.nic_set_err_msg("No output when reading loopback transceiver EEPROM")
            self.nic_console_detach()
            return False

        sn_match = re.search("Bus %s: SN (.*)" % port, cmd_buf)
        if sn_match is None or len(sn_match.groups()) == 0:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("Failed to parse Port {:s} loopback transceiver EEPROM".format(port))
            return False
        self._loopback_sn[port] = sn_match.group(1).strip()
    
        self.nic_console_detach()
        self.nic_set_cmd_buf(cmd_buf)
        return True


