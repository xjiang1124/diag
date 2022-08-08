import time
import os
import libmfg_utils
import re
from datetime import datetime
from libmfg_cfg import *
from libdefs import NIC_Type
from libdefs import MTP_ASIC_SUPPORT
from libdefs import NIC_Vendor
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
from libdefs import NIC_IP_Address

class nic_ctrl():
    def __init__(self, slot, diag_log_filep, diag_cmd_log_filep=None, dbg_mode = False):
        self._slot = slot
        self._debug_mode = dbg_mode
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._nic_status = NIC_Status.NIC_STA_POWEROFF
        self._nic_con_prompt = "# "

        self._diag_ver = None
        self._diag_util_ver = None
        self._diag_asic_ver = None
        self._cpld_ver = None
        self._cpld_timestamp = None
        self._sn = None
        self._mac = None
        self._pn = None
        self._date = None
        self._img_timestamp = None
        self._boot_image = None
        self._vendor = None
        self._alom_sn = None
        self._alom_pn = None
        self._assettagnumber = None
        self._kernel_timestamp = None
        
        self._nic_type = None
        self._nic_handle = None
        self._nic_prompt = None
        self._err_msg = ""
        self._cmd_buf = None

        self._asic_type = None

        self._in_mainfw = None


    def nic_handle_init(self, handle, prompt):
        self._nic_handle = handle
        self._nic_prompt = prompt
        self._nic_handle.logfile_read = self._diag_filep
        self._nic_handle.logfile_send = self._diag_cmd_filep


    def nic_set_type(self, nic_type):
        self._nic_type = nic_type
        self._nic_status = NIC_Status.NIC_STA_OK
        self.nic_set_asic_type()

    def nic_set_pn(self, new_pn):
        self._pn = new_pn

    def nic_set_err_msg(self, err_msg):
        if not self._err_msg:
            self._err_msg = ""
        self._err_msg += "\n" + err_msg


    def nic_set_cmd_buf(self, cmd_buf):
        self._cmd_buf = cmd_buf


    def nic_set_status(self, status):
        self._nic_status = status


    def nic_check_status(self):
        if self._nic_status == NIC_Status.NIC_STA_OK:
            return True
        else:
            return False

    def nic_set_asic_type(self):
        if self._nic_type == None:
            self._asic_type = None
        elif self._nic_type == NIC_Type.ORTANO or self._nic_type == NIC_Type.ORTANO2 or self._nic_type == NIC_Type.TAORMINA:
            self._asic_type = "elba"
        else:
            self._asic_type = "capri"

    def mtp_exec_cmd(self, cmd, timeout=MTP_Const.OS_CMD_DELAY, sig_list=[]):
        self._nic_handle.sendline(cmd)
        cmd_before = ""
        rc = True
        for sig in sig_list:
            idx = libmfg_utils.mfg_expect(self._nic_handle, [sig], timeout)
            if idx < 0:
                rc = False
                cmd_before = self._nic_handle.before
                break
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
        if not rc:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(cmd_before)
            return False
        elif idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False
        self.nic_set_cmd_buf(self._nic_handle.before)
        return True

    def mtp_get_info(self, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False
        info_buf = self._nic_handle.before
        self.nic_set_cmd_buf(self._nic_handle.before)

        return info_buf


    def nic_exec_rst_cmd(self, nic_rst_cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY, dontwait=False):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot, self._nic_type)
        if self._in_mainfw: 
            cmd = MFG_DIAG_CMDS.TOR_DSM_SSH_CONNECT_FMT.format(NIC_MGMT_PASSWORD, NIC_MGMT_USERNAME, NIC_IP_Address.DSM_LAG_IP[self._slot])
        else:
            cmd = libmfg_utils.get_ssh_connect_cmd(NIC_MGMT_USERNAME, ipaddr)
        self._nic_handle.sendline(cmd)
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:", self._nic_con_prompt], timeout=MTP_Const.SSH_PASSWORD_DELAY)
            if idx < 0:
                libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_err_msg(self._nic_handle.before)
                return False
            if idx == 0:
                self._nic_handle.sendline(NIC_MGMT_PASSWORD)
                continue
            else:
                break

        self._nic_handle.sendline(nic_rst_cmd)
        # Here ssh should disconnected automatically, unless dontwait=True..in which case kill console ourselves and powercycle.
        if not dontwait:
            nic_exp_prompts = [self._nic_prompt]
        else:
            nic_exp_prompts = [self._nic_prompt, self._nic_con_prompt]
        idx = libmfg_utils.mfg_expect(self._nic_handle, nic_exp_prompts, timeout)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False
        if idx == 1 and dontwait:
            print("CPLD refresh needs powercycle")
            self._nic_handle.sendline("exit")
            return True
        else:
            return True


    def nic_exec_cmds(self, nic_cmd_list, timeout=MTP_Const.NIC_CON_CMD_DELAY, fail_sig=None):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot, self._nic_type)
        if self._in_mainfw: 
            cmd = MFG_DIAG_CMDS.TOR_DSM_SSH_CONNECT_FMT.format(NIC_MGMT_PASSWORD, NIC_MGMT_USERNAME, NIC_IP_Address.DSM_LAG_IP[self._slot])
        else:
            cmd = libmfg_utils.get_ssh_connect_cmd(NIC_MGMT_USERNAME, ipaddr)
        self._nic_handle.sendline(cmd)
        retries = 0
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:", self._nic_con_prompt], timeout=MTP_Const.SSH_PASSWORD_DELAY)
            if idx < 0:
                # try one more time:
                if retries == 0:
                    retries += 1
                    continue
                libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
            if idx == 0:
                self._nic_handle.sendline(NIC_MGMT_PASSWORD)
                continue
            else:
                break

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


    def nic_get_info(self, nic_cmd):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot, self._nic_type)
        if self._in_mainfw: 
            cmd = MFG_DIAG_CMDS.TOR_DSM_SSH_CONNECT_FMT.format(NIC_MGMT_PASSWORD, NIC_MGMT_USERNAME, NIC_IP_Address.DSM_LAG_IP[self._slot])
        else:
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

        self._nic_handle.sendline(nic_cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], MTP_Const.NIC_CON_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            info_buf = None
        else:
            info_buf = self._nic_handle.before

        cmd = "exit"
        if not self.mtp_exec_cmd(cmd):
            return False

        self.nic_set_cmd_buf(info_buf)

        return info_buf


    def nic_get_err_msg(self):
        ret = self._err_msg
        self._err_msg = "" #clear it out
        return ret


    def nic_get_cmd_buf(self):
        return self._cmd_buf


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
        if self._nic_type == NIC_Type.TAORMINA:
            self.mtp_exec_cmd("systemctl stop dsm-uart-log")
            self.mtp_exec_cmd("cd {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH))
            con_cmd = "./econ.bash {:d}".format(self._slot)
        else:
            con_cmd = MFG_DIAG_CMDS.NIC_CON_ATTACH_FMT.format(self._slot+1)
        self._nic_handle.sendline(con_cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["Terminal ready"], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            return False
        time.sleep(5)
        # send return
        self._nic_handle.sendline("")
        # TODO: Forio need another enter to connect console
        if self._nic_type == NIC_Type.FORIO or self._nic_type == NIC_Type.VOMERO:
            self._nic_handle.sendline("")

        #if self._nic_type == NIC_Type.VOMERO2:
            #self._nic_handle.sendline("")
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
                self.nic_set_err_msg(self._nic_handle.before)
                self.nic_set_err_msg("Timeout connecting to NIC console")
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

    def nic_send_ctrl_c(self):
        self._nic_handle.sendcontrol('c')
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            return False
        else:
            return True

    def nic_mgmt_config(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # config the mgmt port
        cmd = MFG_DIAG_CMDS.NIC_SET_MGMT_IP_FMT.format(self._slot+101)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_err_msg(self._nic_handle.after)
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self.nic_set_status(NIC_Status.NIC_STA_OK)
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

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
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

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True
    def nic_set_goldfw_boot(self):
        self.mtp_exec_cmd("killall picocom")

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

        # sync
        self._nic_handle.sendline("sync")
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
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
            self.nic_set_err_msg(self._nic_handle.before)
            self.nic_console_detach()
            return False

        self.nic_console_detach()
        return True

    def nic_sw_shutdown(self, cloud=False):
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
        for nic_cmd in nic_shutdown_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_console_detach()
                return False

        # poweroff ... Cloud build do not support this command
        if cloud == False:
            self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_OS_SHUTDOWN_FMT)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [MFG_DIAG_SIG.NIC_OS_SHUTDOWN_OK_SIG], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_err_msg(self._nic_handle.before)
                self.nic_console_detach()
                return False

        self.nic_console_detach()
        return True

    def nic_mgmt_sw_cleanup(self):
        # 1. remove diag utils on NIC
        # 2. sync
        emmc_fsck_cmd = MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT
        emmc_mount_cmd = MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT
        nic_shutdown_cmd_list = [emmc_fsck_cmd,
                                 emmc_mount_cmd,
                                 MFG_DIAG_CMDS.NIC_IMG_DISP_FMT,
                                 MFG_DIAG_CMDS.NIC_IMG_DISP1_FMT,
                                 MFG_DIAG_CMDS.NIC_DIAG_CLEANUP_FMT,
                                 MFG_DIAG_CMDS.NIC_TOR_CLEANUP_FMT,
                                 MFG_DIAG_CMDS.NIC_EMMC_LS_FMT]
        if not self.nic_exec_cmds(nic_shutdown_cmd_list):
            return False
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
                self.nic_set_err_msg(self._nic_handle.before)
                self.nic_console_detach()
                return False

        self._nic_handle.sendline("sysreset.sh")
        time.sleep(MTP_Const.NIC_SYSRESET_DELAY)
        self._nic_handle.sendline()
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_SYSRESET_DELAY)
        if idx < 0:
            self.nic_set_err_msg(self._nic_handle.before)
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
            self.nic_set_err_msg(cmd_buf)
            self.nic_console_detach()
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_SW_DEVICE_CHK_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_err_msg(cmd_buf)
            self.nic_console_detach()
            return False

        cmd_buf = self._nic_handle.before
        dev_profile_match = re.findall(MFG_DIAG_SIG.NIC_SW_DEVICE_CHK_SIG1, cmd_buf)
        if dev_profile_match:
            pass
        else:
            self.nic_set_err_msg(cmd_buf)
            self.nic_console_detach()
            return False

        mode_match = re.findall(MFG_DIAG_SIG.NIC_SW_DEVICE_CHK_SIG2, cmd_buf)
        if mode_match:
            pass
        else:
            self.nic_set_err_msg(cmd_buf)
            self.nic_console_detach()
            return False

        self.nic_console_detach()
        return True


    def nic_boot_info_init(self):
        # get boot image info
        loop = 0
        while loop < MTP_Const.NIC_CON_CMD_RETRY:
            if not self.nic_console_attach():
                loop += 1
                continue

            self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_DISP_FMT)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_console_detach()
                loop += 1
                continue

            # remove the potential special character
            buf = libmfg_utils.special_char_removal(self._nic_handle.before)
            match = re.findall(r"(\w+fw\w?)", buf)
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
            self.nic_set_err_msg(self._nic_handle.before)
            return False

        # get kernel build timestamp
        loop = 0
        while loop < MTP_Const.NIC_CON_CMD_RETRY:
            if not self.nic_console_attach():
                loop += 1
                continue

            self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_IMG_VER_DISP_FMT)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
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
                    # Tue Jun 22 15:28:57 PDT 2021
                    dt = datetime.strptime(kernel_ver, "%a %b %d %X %Z %Y")
                    self._kernel_timestamp = dt.strftime("%m-%d-%Y")
                    self.nic_console_detach()
                    break
                except ValueError:
                    # this version of datetime may not accept timezone as PDT/PST
                    try:
                        # Wed Feb 24 12:51:26 PST 2021
                        kernel_ver = kernel_ver[:-8] + kernel_ver[-4:] #remove the timezone
                        dt = datetime.strptime(kernel_ver, "%a %b %d %X %Y")
                        self._kernel_timestamp = dt.strftime("%m-%d-%Y")
                        self.nic_console_detach()
                        break
                    except ValueError:
                        self.nic_console_detach()
                        loop += 1
                        continue
            else:
                print("No match!")
                self.nic_console_detach()
                loop += 1
                continue

        if loop >= MTP_Const.NIC_CON_CMD_RETRY:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False

        return True


    def nic_pcie_poll_enable(self, enable):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if enable:
            sig = MFG_DIAG_SIG.NIC_UBOOT_PCIE_ENA_SIG
            cmd = MFG_DIAG_CMDS.MTP_NIC_PCIE_LINK_POLL_ENABLE_FMT.format(self._slot+1)
        else:
            sig = MFG_DIAG_SIG.NIC_UBOOT_PCIE_DIS_SIG
            cmd = MFG_DIAG_CMDS.MTP_NIC_PCIE_LINK_POLL_DISABLE_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, MTP_Const.NIC_CON_CMD_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        if sig in self.nic_get_cmd_buf():
            return True
        else:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
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

        sig_list = ["valid bit 0x1", "error 0x00"]
        if asic_support == MTP_ASIC_SUPPORT.ELBA:
            sig_list = ["status bit 0x1"]

        error_flag = False

        if not self.mtp_exec_cmd(cmd):
            error_flag = True

        cmd_buf = self.nic_get_cmd_buf()
        if not True in [sig in cmd_buf for sig in sig_list]:
            error_flag = True

        if error_flag:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            self.nic_set_err_msg(cmd_buf)

            # Some additional error printing
            if not self.mtp_exec_cmd("inventory -sts -slot {:d}".format(self._slot)):
                self.nic_set_err_msg(self.nic_get_cmd_buf())
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


    def nic_program_fru(self, date, sn, mac, pn, nic_type=None):
        if not self.nic_vendor_init(sn):
            return False

        if self.nic_2nd_fru_exist(pn):
            if self._vendor == NIC_Vendor.HPE:
                #Program HPE
                if nic_type == NIC_Type.NAPLES25OCP:
                    cmd = MFG_DIAG_CMDS.MTP_HP_OCP_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
                    if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
                        #print("****MTP FRU PROG 1st****")
                        return False

                elif nic_type == NIC_Type.NAPLES25SWM:
                    #Program HPE SWM
                    cmd = MFG_DIAG_CMDS.MTP_HP_SWM_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
                    if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
                        #print("****MTP FRU PROG 1st****")
                        return False

                elif nic_type == NIC_Type.NAPLES100HPE:
                    cmd = MFG_DIAG_CMDS.MTP_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
                    if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
                        return False
                else:
                    #Program HPE
                    cmd = MFG_DIAG_CMDS.MTP_HP_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
                    if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
                        #print("****MTP FRU PROG 3rd****")
                        return False
            else:
                #Program Non HPE

                if nic_type == NIC_Type.ORTANO2:
                    cmd = MFG_DIAG_CMDS.MTP_ORTANO_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
                    if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
                        return False

                cmd = MFG_DIAG_CMDS.MTP_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
                if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
                    #print("****MTP FRU PROG 4th****")
                    return False
            #VERIFY FRU PROGRAMMING
            cmd_buf = self.nic_get_cmd_buf()
            match = re.findall(r"FRU Checkum and Type/Length Checks Passed", cmd_buf)
            if not match:
                self.nic_set_err_msg(" SMB FRU PROGRAMMING FAILED\n")
                self.nic_set_err_msg(" BUF =  {:s}".format(cmd_buf))
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

               

        nic_cmd_list = list()
        if self._vendor == NIC_Vendor.HPE:
            if nic_type == NIC_Type.NAPLES25OCP:
                #In NIC Program HPE SWM
                nic_cmd = MFG_DIAG_CMDS.NIC_HP_OCP_FRU_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, date, sn, mac, pn)
                nic_cmd_list.append(nic_cmd)

            elif nic_type == NIC_Type.NAPLES25SWM:
                #In NIC Program HPE SWM
                nic_cmd = MFG_DIAG_CMDS.NIC_HP_SWM_FRU_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, date, sn, mac, pn)
                nic_cmd_list.append(nic_cmd)
         
            elif nic_type == NIC_Type.NAPLES100HPE:
                nic_cmd = MFG_DIAG_CMDS.NIC_FRU_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, date, sn, mac, pn)
                nic_cmd_list.append(nic_cmd)
            else:    
                #In NIC Program HPE
                nic_cmd = MFG_DIAG_CMDS.NIC_HP_FRU_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, date, sn, mac, pn)
                nic_cmd_list.append(nic_cmd)
          
        else:
            #In NIC Program Non HPE
            if nic_type == NIC_Type.ORTANO2:
                nic_cmd = MFG_DIAG_CMDS.NIC_ORTANO_FRU_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, date, sn, mac, pn)
            elif nic_type == NIC_Type.TAORMINA:
                nic_cmd = MFG_DIAG_CMDS.NIC_ORTANO_FRU_PROG_FMT.format("export CARD_TYPE=ORTANO2 && /data/nic_util/", date, sn, mac, pn)
            else:
                nic_cmd = MFG_DIAG_CMDS.NIC_FRU_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, date, sn, mac, pn)
            nic_cmd_list.append(nic_cmd)
  
            
        cmd_buf = self.nic_get_info(nic_cmd)
        if not cmd_buf:
            return False
        #VERIFY FRU PROGRAMMING
        match = re.findall(r"FRU Checkum and Type/Length Checks Passed", cmd_buf)
        if not match:
            self.nic_set_err_msg(" ASIC FRU PROGRAMMING FAILED\n")
            self.nic_set_err_msg(" BUF =  {:s}".format(cmd_buf))
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        return True


    def nic_program_alom_fru(self, date, alom_sn, alom_pn):
        if not self.nic_vendor_init(alom_sn):
            return False

               
        cmd = MFG_DIAG_CMDS.MTP_HP_ALOM_FRU_PROG_FMT.format(date, alom_sn, alom_pn, self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
           return False

        cmd = MFG_DIAG_CMDS.MTP_HP_ALOM_FRU_DISP_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
           return False
           
        return True

    def mtp_read_alom_fru(self, slot):
        cmd = MFG_DIAG_CMDS.MTP_HP_ALOM_FRU_DISP_FMT.format(slot+1)
        return self.mtp_get_info(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY)

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

    def nic_copy_image(self, img_name, directory="/"):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot, self._nic_type)
        cmd = "scp {:s} -r {:s} {:s}@{:s}:{:s}".format(libmfg_utils.get_ssh_option(), img_name, NIC_MGMT_USERNAME, ipaddr, directory)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt, "assword:"], timeout=MTP_Const.SSH_PASSWORD_DELAY)
        if idx < 0:
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False
        elif idx == 1:
            self._nic_handle.sendline(NIC_MGMT_PASSWORD)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            if idx < 0:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_err_msg(self._nic_handle.before)
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
            self.nic_set_err_msg(self._nic_handle.before)
            return False

        self._nic_handle.sendline(NIC_MGMT_PASSWORD)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False

        return True

    def nic_copy_compressed_image(self, src_directory, src_img, dst_directory):
        """
        Send file to NIC from MTP.

        Same function as nic_copy_image but uses ssh connection to transfer characters, 
        while doing tar & untar before & after. Tar on MTP and untar on NIC.
        """
        if self._in_mainfw:
            ip_addr = NIC_IP_Address.DSM_LAG_IP[self._slot]
            cmd = MFG_DIAG_CMDS.NIC_SCP_COMPRESSED_MAINFW_FMT.format(src_directory, src_img, NIC_MGMT_USERNAME, ip_addr, libmfg_utils.get_ssh_option(), dst_directory)
        else:
            ip_addr = libmfg_utils.get_nic_ip_addr(self._slot, self._nic_type)
            cmd = MFG_DIAG_CMDS.NIC_SCP_COMPRESSED_FMT.format(src_directory, src_img, NIC_MGMT_USERNAME, ip_addr, libmfg_utils.get_ssh_option(), dst_directory)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt, "assword:"], timeout=MTP_Const.NIC_NETCOPY_DELAY)
        if idx < 0:
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg("No prompt back in time")
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        elif idx == 1:
            self._nic_handle.sendline(NIC_MGMT_PASSWORD)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt, "No such file", "Exiting with failure"], timeout=MTP_Const.OS_CMD_DELAY)
            if idx < 0:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_err_msg(self._nic_handle.before)
                return False
            if idx == 1 or idx == 2:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                self.nic_set_err_msg("Missing file {:s}".format(src_directory+"/"+src_img))
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False

        self.nic_exec_cmds([]) #sync

        return True

    def nic_sw_profile(self, profile):
        if not self.nic_copy_image("/home/diag/mtp_swi_script/{:s}".format(profile)):
            return False

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_SW_PROFILE_CMD_FMT.format(profile)
        profile_sig = MFG_DIAG_SIG.NIC_SW_PROFILE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, fail_sig=profile_sig):
            return False

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
        if self._nic_type == NIC_Type.ORTANO or self._nic_type == NIC_Type.ORTANO2 or self._nic_type == NIC_Type.TAORMINA:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_CPLD_PROG_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, img_name, partition))
        # Capri-based:
        else:
            nic_cmd_list.append(MFG_DIAG_CMDS.NIC_CPLD_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, img_name))

        if self._nic_type == NIC_Type.NAPLES25OCP:
            if not self.nic_exec_rst_cmd(nic_cmd_list[0], timeout=MTP_Const.OS_CMD_DELAY):
                return False
        else:
            if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
                return False

        return True


    def nic_refresh_cpld(self, dontwait=False):
        # Capri-based:
        nic_cpld_ref_cmd = MFG_DIAG_CMDS.NIC_CPLD_REF_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        # Elba-based:
        if self._nic_type == NIC_Type.ORTANO or self._nic_type == NIC_Type.ORTANO2 or self._nic_type == NIC_Type.TAORMINA:
            nic_cpld_ref_cmd = MFG_DIAG_CMDS.NIC_CPLD_REF_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        if not self.nic_exec_rst_cmd(nic_cpld_ref_cmd, timeout=MTP_Const.OS_CMD_DELAY, dontwait=dontwait):
            return False

        return True

    def nic_check_cpld_partition(self):
        reg_addr = 1
        cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(self._slot+1) + " ;" + MFG_DIAG_CMDS.MTP_SMB_RD_CPLD_FMT.format(reg_addr, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            # try again one more time
            time.sleep(1)
            if not self.mtp_exec_cmd(cmd):
                self.nic_set_err_msg(self.nic_get_cmd_buf())
                return False
        match = re.findall(MFG_DIAG_CMDS.MTP_SMB_RE % reg_addr, self.nic_get_cmd_buf())
        if not match:
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False
        else:
            read_data = int(match[0], 16)
            if (read_data & 0x02) == 0:
                return True
            else:
                self.nic_set_err_msg("Incorrect CPLD boot partition")
                return False

    def nic_setting_partition(self):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_SETTING_PARTITION_FMT
        nic_cmd_list.append(nic_cmd)
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

    def nic_dump_cpld(self, partition):
        cmd = MFG_DIAG_CMDS.NIC_CPLD_DUMP_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, "/home/diag/cplddump", partition)
        nic_cmd_list = list()
        nic_cmd_list.append(cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.nic_set_err_msg(self.nic_get_cmd_buf())
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

        if self._nic_type == NIC_Type.ORTANO2:
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

        if not self._nic_type == NIC_Type.ORTANO2:
            return False

        cmd = MFG_DIAG_CMDS.NIC_EFUSE_PROG_ELBA_FMT.format(self._slot+1,
                                                     self._sn,
                                                     self._pn,
                                                     self._mac.replace('-',':'),
                                                     self._nic_type)
        if not GLB_CFG_MFG_TEST_MODE:
            cmd = MFG_DIAG_CMDS.NIC_EFUSE_PROG_ELBA_MODEL_FMT.format(self._slot+1,
                                                                     self._sn,
                                                                     self._pn,
                                                                     self._mac.replace('-',':'),
                                                                     self._nic_type)
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
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False

        return True

    def nic_copy_gold(self, gold_img):
        if not self.nic_copy_image(gold_img):
            return False
            
        return True

    def nic_program_gold(self, gold_img):

        img_name = os.path.basename(gold_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_GOLDFW_PROG_FMT.format(img_name, img_name)
        gold_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, fail_sig=gold_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False

        return True
    def nic_program_gold_naples100(self, gold_img):
        #if not self.nic_copy_image(gold_img):
            #return False
        img_name = os.path.basename(gold_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_GOLDFW_PROG_FMT_NAPLES100.format(img_name)
        gold_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, fail_sig=gold_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False

        return True


    def nic_init_emmc(self, init = False):
        nic_cmd_list = list()
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
                return True
            else:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                self.nic_set_err_msg(mount_buf)
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
            
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
                self.nic_set_err_msg(perf_buf)
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
                self.nic_set_err_msg(perf_buf)
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
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_B_PROG_FMT.format(img_name, img_name)
        emmc_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY, fail_sig=emmc_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False

        return True
      
    def nic_program_emmc_ibm(self, emmc_img):
        if not self.nic_copy_image_IBM(emmc_img):
            return False
        img_name = os.path.basename(emmc_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_INIT_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_PROG_FMT_IBM.format(img_name, img_name)
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_B_PROG_FMT_IBM.format(img_name, img_name)
        emmc_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY, fail_sig=emmc_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False

        return True
    def nic_program_emmc_naples100(self, emmc_img):
        if not self.nic_copy_image(emmc_img, directory=MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH):
            return False
        img_name = os.path.basename(emmc_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_INIT_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_PROG_FMT_NAPLES100.format(img_name)
        nic_cmd_list.append(nic_cmd)
        emmc_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY, fail_sig=emmc_fail_sig):
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            return False

        return True


    def nic_copy_diag_img(self, emmc_utils=False):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH)
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        nic_diag_list = ["diag", "start_diag.arm64.sh"]
        for util in nic_diag_list:
            if not self.nic_copy_compressed_image(
                src_directory=MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH,
                src_img=util,
                dst_directory=MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH): #MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH):
                return False

        nic_cmd_list = list()
        nic_cmd = "ln -s /data/diag/ {:s}".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH)
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        if emmc_utils:
            nic_diag_list = ["nic_arm", "nic_util"]
            for util in nic_diag_list:
                if not self.nic_copy_compressed_image(
                    src_directory=MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH,
                    src_img=util,
                    dst_directory=MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH):
                    return False

        return True


    def nic_save_logfile(self, logfile_list):
        if not self._sn:
            return False

        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot, self._nic_type)
        for log in logfile_list:
            logfile = MTP_DIAG_Logfile.NIC_ONBOARD_ASIC_LOG_DIR + log
            dst_logfile = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR + self._sn + "_" + log
            cmd = "scp {:s} {:s}@{:s}:{:s} {:s}".format(libmfg_utils.get_ssh_option(), NIC_MGMT_USERNAME, ipaddr, logfile, dst_logfile)
            self._nic_handle.sendline(cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:"], timeout=MTP_Const.SSH_PASSWORD_DELAY)
            if idx < 0:
                libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_err_msg(self._nic_handle.before)
                return False

            self._nic_handle.sendline(NIC_MGMT_PASSWORD)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            if idx < 0:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_err_msg(self._nic_handle.before)
                return False
                
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_PICOCOM_FMT
        nic_cmd_list.append(nic_cmd)
        for cmd in nic_cmd_list:
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
                return False
        return True


    def nic_save_diag_logfile(self, aapl):
        if not self._sn:
            return False

        if aapl:
            dst_log_dir = MTP_DIAG_Logfile.ONBOARD_NIC_LOG_DIR + "AAPL-NIC-{:02d}/".format(self._slot+1)
        else:
            dst_log_dir = MTP_DIAG_Logfile.ONBOARD_NIC_LOG_DIR + "NIC-{:02d}/".format(self._slot+1)
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(dst_log_dir)
        if not self.mtp_exec_cmd(cmd):
            return False

        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot, self._nic_type)
        logfile = MTP_DIAG_Logfile.NIC_ONBOARD_DIAG_LOG_FILES
        cmd = "scp {:s} {:s}@{:s}:{:s} {:s}".format(libmfg_utils.get_ssh_option(), NIC_MGMT_USERNAME, ipaddr, logfile, dst_log_dir)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:"], timeout=MTP_Const.SSH_PASSWORD_DELAY)
        if idx < 0:
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False

        self._nic_handle.sendline(NIC_MGMT_PASSWORD)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_FINI_FMT
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False
        cmd = "/home/diag/diag/scripts/sys_clean.sh"
        self._nic_handle.sendline(cmd)

        return True


    def nic_diag_clean(self):
  
        cmd = MFG_DIAG_CMDS.NIC_SYS_CLEAN_FMT.format(MTP_DIAG_Path.ONBOARD_MTP_MTP_DIAG_PATH)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False
        return True
    def nic_kill_hal(self):
        for x in range(6):
            nic_cmd_list = list()
            nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_HAL_FMT
            nic_cmd_list.append(nic_cmd)
            if not self.nic_exec_cmds(nic_cmd_list, timeout=30): #timeout=MTP_Const.OS_CMD_DELAY):
                return False

            nic_cmd = MFG_DIAG_CMDS.NIC_HAL_RUNNING_FMT
            cmd_buf = self.nic_get_info(nic_cmd)
            if not cmd_buf:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            
            match = re.findall("/nic/bin/hal", cmd_buf)
            if not match:
                break

            time.sleep(5)

    def nic_start_diag(self, aapl):
        # setup diag env on nic
        nic_cmd_list = list()

        time.sleep(2)

        time_str = str(libmfg_utils.timestamp_snapshot())
        nic_cmd = MFG_DIAG_CMDS.NIC_DATE_SET_FMT.format(time_str)
        nic_cmd_list.append(nic_cmd)
        if not aapl:
            self.nic_kill_hal()
            if self._nic_type == NIC_Type.TAORMINA:
                # dont count this as failure
                self.nic_set_status(NIC_Status.NIC_STA_OK)
            nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_HAL_FMT
            nic_cmd_list.append(nic_cmd)
            nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_CONFIG_FMT
            nic_cmd_list.append(nic_cmd)
        if self._nic_type == NIC_Type.TAORMINA:
            # Skip start_diag.arm64.sh for Taormina
            nic_cmd = "export CARD_TYPE=TAORMINA"
            nic_cmd_list.append(nic_cmd)
        else:
            nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_INIT_FMT.format(self._slot+1)
            nic_cmd_list.append(nic_cmd)

        nic_cmd = "source /etc/profile"
        nic_cmd_list.append(nic_cmd)

        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            print("Unable to stop HAL")
            if self._nic_type != NIC_Type.TAORMINA:
                return False

        # Start NIC DSP
        cmd = MFG_DIAG_CMDS.NIC_DSP_START_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
            print("Unable to start diagmgr")
            if self._nic_type != NIC_Type.TAORMINA:
                return False

        # get asic lib version
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_ASIC_VERSION_FMT.format(self._asic_type)
        cmd_buf = self.nic_get_info(nic_cmd)
        match = re.findall(r"Date: +(.*20\d{2})", cmd_buf)
        if match:
            self._diag_asic_ver = match[0]
        else:
            print("Unable to find nic asic version")
            if self._nic_type != NIC_Type.TAORMINA:
                return False

        # get emmc nic utils version
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_UTIL_VERSION_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        match = re.findall(r"Date: +(.*20\d{2})", cmd_buf)
        if match:
            self._diag_util_ver = match[0]
        else:
            print("Unable to find nic utils version")
            if self._nic_type != NIC_Type.TAORMINA:
                return False

        # get nic diag version
        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_VERSION_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        match = re.findall(r"Date: +(.*20\d{2})", cmd_buf)
        if match:
            self._diag_ver = match[0]
        else:
            print("Unable to find nic diag version")
            return False

        # check if hal is running
        nic_cmd = MFG_DIAG_CMDS.NIC_HAL_RUNNING_FMT
        cmd_buf = self.nic_get_info(nic_cmd)
        if MFG_DIAG_SIG.NIC_HAL_RUNNING_SIG in cmd_buf:
            hal_running = True
        else:
            hal_running = False

        # aapl and hal_running should be both True or both False
        if hal_running != aapl:
            print("AAPL or HAL not running")
            if self._nic_type != NIC_Type.TAORMINA:
                return False

        return True


    def nic_set_vmarg(self, vmarg_param):
        nic_cmd_list = list()
        if self._nic_type == NIC_Type.TAORMINA:
            nic_cmd = MFG_DIAG_CMDS.TOR_NIC_VMARG_SET_FMT.format(vmarg_param)
        else:
            nic_cmd = MFG_DIAG_CMDS.NIC_VMARG_SET_FMT.format(vmarg_param)
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
        if not self.nic_exec_cmds(nic_cmd_list):
            return False

        return True


    def nic_set_gold_boot(self):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_SET_GOLD_BOOT_FMT
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list):
            return False

        return True


    # for the Naples100 before PP, no 2nd fru instance
    def nic_2nd_fru_exist(self, pn):
        for item in ["68-0003-01", "68-0003-02", "68-0003-03", "68-0004-02", "68-0004-03", "68-0018", "73-0040"]:
            if item in pn:
                return False
        return True


    # check nic mfg vendor based on the sn format
    def nic_vendor_init(self, sn=None):
        nic_type = self._nic_type
        if sn == None:
            if self._nic_type == NIC_Type.NAPLES25OCP:
                nic_cmd = MFG_DIAG_CMDS.NIC_VENDOR_DISP_FMT_OCP.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
            elif self._nic_type == NIC_Type.NAPLES25SWM:
                nic_cmd = MFG_DIAG_CMDS.NIC_HPESWM_VENDOR_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
            elif self._nic_type == NIC_Type.TAORMINA:
                nic_cmd = MFG_DIAG_CMDS.NIC_VENDOR_DISP_FMT.format("export CARD_TYPE=ORTANO2 && "+MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
            else:
                nic_cmd = MFG_DIAG_CMDS.NIC_VENDOR_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
            fru_buf = self.nic_get_info(nic_cmd)

        else:
            fru_buf = sn

        match = re.findall(NAPLES_SN_FMT+"|"+TOR_SN_FMT, fru_buf)
        if match:
            self._vendor = NIC_Vendor.PENSANDO
            return True
        match = re.findall(HP_SN_FMT, fru_buf)
        if match:
            self._vendor = NIC_Vendor.HPE
            return True

        self.nic_set_err_msg(fru_buf)
        self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
        return False


    def get_nic_fru_hpe_pn(self):

        if self._nic_type == NIC_Type.NAPLES25SWM:
            nic_cmd = MFG_DIAG_CMDS.NIC_HP_SWM_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        elif self._nic_type == NIC_Type.NAPLES100HPE:
            nic_cmd = MFG_DIAG_CMDS.NIC_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        elif self._vendor == NIC_Vendor.HPE:
            nic_cmd = MFG_DIAG_CMDS.NIC_HP_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        else:
            nic_cmd = MFG_DIAG_CMDS.NIC_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        fru_buf = self.nic_get_info(nic_cmd)
        if not fru_buf:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
            
        pro_no = None
        match = None
        
        #retrieve SWM card Product Number PN
        if self._vendor == NIC_Vendor.HPE:
            if self._nic_type == NIC_Type.NAPLES25SWM:
                                                               
                                                        
                match = re.findall(HP_SWN_PN_FMT, fru_buf)
            elif self._nic_type == NIC_Type.NAPLES100HPE:
                match = re.findall(NAPLES_DISP_PN_FMT, fru_buf)
            else:
                match = re.findall(HP_DISP_PN_FMT, fru_buf)
        else:
            match = re.findall(NAPLES_DISP_PN_FMT, fru_buf)
        if match:
            pro_no = match[0]
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            
        return pro_no
        
    def nic_fru_init(self, init_date=True, swmtestmode=Swm_Test_Mode.SWMALOM):
        if not self.nic_vendor_init():
            return False

        if self._nic_type == NIC_Type.NAPLES25OCP:
            nic_cmd = MFG_DIAG_CMDS.NIC_HP_OCP_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        elif self._nic_type == NIC_Type.NAPLES25SWM:
            nic_cmd = MFG_DIAG_CMDS.NIC_HP_SWM_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        elif self._nic_type == NIC_Type.NAPLES100HPE:
            nic_cmd = MFG_DIAG_CMDS.NIC_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        elif self._vendor == NIC_Vendor.HPE:
            nic_cmd = MFG_DIAG_CMDS.NIC_HP_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        elif self._nic_type == NIC_Type.TAORMINA:
            nic_cmd = MFG_DIAG_CMDS.NIC_FRU_DISP_FMT.format("export CARD_TYPE=ORTANO2 && "+MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        else:
            nic_cmd = MFG_DIAG_CMDS.NIC_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        fru_buf = self.nic_get_info(nic_cmd)
        if not fru_buf:
            print ("fru_buf 1 match: ")
            self.nic_set_err_msg("Unable to read ASIC FRU")
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        match = None
        # retrieve card serial number
        if self._vendor == NIC_Vendor.HPE:
            #match = re.findall(HP_DISP_SN_FMT, fru_buf)
            if self._nic_type == NIC_Type.NAPLES25SWM or self._nic_type == NIC_Type.NAPLES100HPE:
               match = re.findall(ALOM_SN_FMT, fru_buf)
            else:
               match = re.findall(HP_DISP_SN_FMT, fru_buf)
        elif self._nic_type == NIC_Type.TAORMINA:
            # match = re.findall(TOR_SN_FMT, fru_buf)
            match = re.findall(TOR_NIC_DISP_SN_FMT, fru_buf)
        else:
            match = re.findall(NAPLES_DISP_SN_FMT, fru_buf)
        if match:
            self._sn = match[0]
        else:
            print ("fru_buf 2: {}".format(fru_buf))
            self.nic_set_err_msg("Serial number doesn't match any known formats in ASIC FRU:\n {}".format(fru_buf))
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        match = None
        # retrieve card MAC address
        match = re.findall(NAPLES_DISP_MAC_FMT, fru_buf)
        if self._nic_type == NIC_Type.TAORMINA:
            match = re.findall(TOR_DISP_MAC_FMT, fru_buf)
        if match:
            self._mac = match[0].replace("-","")
        else:
            print ("fru_buf 3 match: ")
            self.nic_set_err_msg("MAC address doesn't match any known formats in ASIC FRU:\n {}".format(fru_buf))
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        match = None
        # retrieve program date if it is valid
        if init_date:
            match = re.findall(NAPLES_DISP_DATE_FMT, fru_buf)
            if match:
                self._date = match[0].replace('/','')
            else:
                print ("fru_buf 4 match: ")
                self.nic_set_err_msg("Date field doesn't match any known formats in ASIC FRU:\n {}".format(fru_buf))
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
        else:
            self._date = None
        match = None
        # retrieve card PN
        #print("******READ SWM TEST MODE***********")
        #print(swmtestmode)
        #print("***********************************")
        if self._vendor == NIC_Vendor.HPE:
            if (self._nic_type == NIC_Type.NAPLES25SWM or self._nic_type == NIC_Type.NAPLES25OCP or self._nic_type == NIC_Type.NAPLES100HPE):
                match = re.findall(HP_SWM_DISP_PN_FMT, fru_buf)
            else:
                match = re.findall(HP_DISP_PN_FMT, fru_buf)
        else:
            if self._nic_type == NIC_Type.NAPLES100IBM:
                match = re.findall(IBM_DISP_ASSEMBLY_FMT, fru_buf)
            elif self._nic_type == NIC_Type.VOMERO2:
                match = re.findall(VOMERO2_DISP_ASSEMBLY_FMT, fru_buf)
            elif self._nic_type == NIC_Type.NAPLES25SWMDELL:
                match = re.findall(PEN_DISP_ASSEMBLY_FMT, fru_buf)
            elif self._nic_type == NIC_Type.ORTANO or self._nic_type == NIC_Type.ORTANO2:
                match = re.findall(ORTANO_DISP_ASSEMBLY_FMT, fru_buf)
            elif self._nic_type == NIC_Type.NAPLES25OCP:
                match = re.findall(OCP_DELL_DISP_PN_FMT, fru_buf)
            elif self._nic_type == NIC_Type.TAORMINA:
                match = re.findall(TOR_DISP_PN_FMT, fru_buf)
            else:
                match = re.findall(NAPLES_DISP_PN_FMT, fru_buf)
                if not match:
                    #Try a 2nd match for the new FRU format which moves the pensando part number into the assembly field
                    match = re.findall(PEN_DISP_ASSEMBLY_FMT, fru_buf)

        if match:
            self._pn = match[0]
        else:
            print ("fru_buf 6 match: ")
            self.nic_set_err_msg("Assembly/Part number doesn't match any known formats in ASIC FRU:\n {}".format(fru_buf))
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        
        # retrieve SWM card Product Number PN
        #if self._vendor == NIC_Vendor.HPE:
            #if self._nic_type == NIC_Type.NAPLES25SWM:
                #match = re.findall(HP_SWN_PN_FMT, fru_buf)
            #else:
                #match = re.findall(HP_DISP_PN_FMT, fru_buf)
        #else:
            #match = re.findall(NAPLES_DISP_PN_FMT, fru_buf)
        #if match:
            #self._pro_no = match[0]
        #else:
            #print ("fru_buf 6 match: ")
            #self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            #return False
        
            
        # Asset Tag Type/Length
        #match = None
        #match = re.findall(HPESWM_DISP_ASSET_FMT, fru_buf)
 
        #if match:
            #self._assettagnumber = match[0]
        #else:
            #print ("No asset Tag Number")

        if self.nic_2nd_fru_exist(self._pn):
            if self._nic_type == NIC_Type.NAPLES25OCP:
                cmd = MFG_DIAG_CMDS.MTP_HP_OCP_FRU_DISP_FMT.format(self._slot+1)
            elif self._nic_type == NIC_Type.NAPLES25SWM:
                cmd = MFG_DIAG_CMDS.MTP_HP_SWM_FRU_DISP_FMT.format(self._slot+1)
            elif self._nic_type == NIC_Type.NAPLES100HPE:
                cmd = MFG_DIAG_CMDS.MTP_FRU_DISP_FMT.format(self._slot+1)
            elif self._vendor == NIC_Vendor.HPE:
                cmd = MFG_DIAG_CMDS.MTP_HP_FRU_DISP_FMT.format(self._slot+1)
            else:
                cmd = MFG_DIAG_CMDS.MTP_FRU_DISP_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd):
                print ("fru_buf 7 match: ")
                self.nic_set_err_msg("Unable to read SMB FRU")
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            # secondary SN
            match = None
            if self._vendor == NIC_Vendor.HPE:
                if self._nic_type == NIC_Type.NAPLES25SWM or self._nic_type == NIC_Type.NAPLES100HPE or self._nic_type == NIC_Type.NAPLES25OCP:
                    match = re.findall(ALOM_SN_FMT, fru_buf)
                else:    
                    match = re.findall(HP_DISP_SN_FMT, self.nic_get_cmd_buf())
            else:
                match = re.findall(NAPLES_DISP_SN_FMT, self.nic_get_cmd_buf())
            if match:
                sn = match[0]
            else:
                print ("fru_buf 8 match: ")
                self.nic_set_err_msg("Serial number doesn't match any known formats in SMB FRU:\n {}".format(self.nic_get_cmd_buf()))
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
                
            # secondary MAC
            match = re.findall(NAPLES_DISP_MAC_FMT, self.nic_get_cmd_buf())
            if match:
                mac = match[0]
            else:
                print ("fru_buf 9 match: ")
                self.nic_set_err_msg("MAC address doesn't match any known formats in SMB FRU:\n {}".format(self.nic_get_cmd_buf()))
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            # secondary date
            if init_date:
                match = re.findall(NAPLES_DISP_DATE_FMT, self.nic_get_cmd_buf())
                if match:
                    date = match[0].replace('/','')
                else:
                    print ("fru_buf 10 match: ")
                    self.nic_set_err_msg("Date field doesn't match any known formats in SMB FRU:\n {}".format(self.nic_get_cmd_buf()))
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
            else:
                date = None
            # secondary PN
            match = None            
            if self._vendor == NIC_Vendor.HPE:
                if (self._nic_type == NIC_Type.NAPLES25SWM or self._nic_type == NIC_Type.NAPLES25OCP or self._nic_type == NIC_Type.NAPLES100HPE):
                    match = re.findall(HP_SWM_DISP_PN_FMT, self.nic_get_cmd_buf())
                else:
                    match = re.findall(HP_DISP_PN_FMT, self.nic_get_cmd_buf())
            else:
                if self._nic_type == NIC_Type.NAPLES100IBM:
                    match = re.findall(IBM_DISP_ASSEMBLY_FMT, self.nic_get_cmd_buf())
             
                                                 
                elif self._nic_type == NIC_Type.VOMERO2:
                    match = re.findall(VOMERO2_DISP_ASSEMBLY_FMT, self.nic_get_cmd_buf())
                elif self._nic_type == NIC_Type.NAPLES25SWMDELL:
                    match = re.findall(PEN_DISP_ASSEMBLY_FMT, self.nic_get_cmd_buf())
                elif self._nic_type == NIC_Type.NAPLES25OCP:
                    match = re.findall(OCP_DELL_DISP_PN_FMT, self.nic_get_cmd_buf())
                elif self._nic_type == NIC_Type.ORTANO or self._nic_type == NIC_Type.ORTANO2:
                    match = re.findall(ORTANO_DISP_ASSEMBLY_FMT, self.nic_get_cmd_buf())
                else:
                    match = re.findall(NAPLES_DISP_PN_FMT, self.nic_get_cmd_buf())
                    if not match:
                        #Try a 2nd match for the new FRU format which moves the pensando part number into the assembly field
                        match = re.findall(PEN_DISP_ASSEMBLY_FMT, fru_buf)
            if match:
                pn = match[0]
            else:
                print ("fru_buf 11 match: ")
                self.nic_set_err_msg("Assembly/Part number doesn't match any known formats in SMB FRU:\n {}".format(self.nic_get_cmd_buf()))
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            

            if self._sn != sn or self._mac != mac or self._pn != pn or self._date != date:
                err_msg = " ERR: FRU MISMATCH BETWEEN ASIC FRU AND SMB FRU \n"
                err_msg += " SN  " + self._sn + " " + sn + "\n"
                err_msg += " MAC " + self._mac + " " + mac + "\n"
                err_msg += " PN  " + self._pn + " " + pn + "\n"
                if date != None:
                    err_msg += " DT  " + self._date + " " + date + "\n"
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                self.nic_set_err_msg(err_msg)
                return False


        #ALOM CARD WITH SWM IF ATTACHED
        if self._nic_type == NIC_Type.NAPLES25SWM:
            if swmtestmode == Swm_Test_Mode.SWMALOM or swmtestmode == Swm_Test_Mode.ALOM:
                errlist = list()
                rc = self.nic_swm_check_alom_present(errlist)
                if not rc:
                    print(" NIC_FRU_INIT: ALOM IS NOT SHOWING PRESENT")
                    self.nic_set_err_msg(" NIC_FRU_INIT: ALOM IS NOT SHOWING PRESENT")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                else:
                    print(" ALOM PRESENT")

                fru_buf = self.mtp_read_alom_fru(self._slot)    
                
                if not fru_buf:
                    print ("fru_buf 12: {}".format(nic_cmd))
                    self.nic_set_err_msg("Unable to read ALOM FRU")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False        
                
                match = None
                match = re.findall(ALOM_SN_FMT, fru_buf)
                if match:
                    self._alom_sn = match[0]
                else:
                    print ("fru_buf 13: {}".format(fru_buf))
                    self.nic_set_err_msg("ALOM Serial number doesn't match any known formats:\n {}".format(fru_buf))
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False

                # retrieve ALOM card PN
                match = None
                match = re.findall(ALOM_DISP_BIA_PN_FMT, fru_buf)
                if match:
                    self._alom_pn = match[0]
                else:
                    print ("fru_buf 14: {}".format(fru_buf))

                    self.nic_set_err_msg("ALOM BIA part number doesn't match any known formats:\n {}".format(fru_buf))
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
            
           
                # retrieve ALOM card Product Number PN
                match = None
                match = re.findall(ALOM_DISP_PIA_PN_FMT, fru_buf)
                if match:
                    self._alom_pro_no = match[0]
                    #print("******ALOM PRODUCT NUMBER******")
                    #print(self._alom_pro_no)
                    #print("******************************")
                else:
                    print ("fru_buf 15: {}".format(fru_buf))

                    self.nic_set_err_msg("ALOM PIA part number doesn't match any known formats:\n {}".format(fru_buf))
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
            
                
        return True
        
    def nic_disp_fru(self):
        if self._nic_type == NIC_Type.NAPLES25SWM:
            nic_cmd = MFG_DIAG_CMDS.NIC_HP_SWM_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        elif self._nic_type == NIC_Type.NAPLES100HPE:
            nic_cmd = MFG_DIAG_CMDS.NIC_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        elif self._vendor == NIC_Vendor.HPE:
            nic_cmd = MFG_DIAG_CMDS.NIC_HP_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        elif self._nic_type == NIC_Type.TAORMINA:
            nic_cmd = MFG_DIAG_CMDS.NIC_FRU_DISP_FMT.format("export CARD_TYPE=ORTANO2 && /data/nic_util/")
        else:
            nic_cmd = MFG_DIAG_CMDS.NIC_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        '''
        if self._nic_type == NIC_Type.NAPLES25SWM and 
        (swmtestmode == Swm_Test_Mode.SWMALOM or swmtestmode == Swm_Test_Mode.ALOM):
                errlist = list()
                rc = self.nic_swm_check_alom_present(errlist)
                if not rc:
                    print(" NIC_FRU_DISPLAY: ALOM IS NOT SHOWING PRESENT")
                    self.nic_set_err_msg(" NIC_FRU_DISPLAY: ALOM IS NOT SHOWING PRESENT")
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
                fru_buf = self.mtp_read_alom_fru(self._slot)
                if not fru_buf:
                    self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                    return False
        '''
        fru_buf = self.nic_get_info(nic_cmd)
        if not fru_buf:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        return True

    def nic_disp_2nd_fru(self):
        #SMB FRU dump
        if self._nic_type == NIC_Type.NAPLES25OCP:
            cmd = MFG_DIAG_CMDS.MTP_HP_OCP_FRU_DISP_FMT.format(self._slot+1)
        elif self._nic_type == NIC_Type.NAPLES25SWM:
            cmd = MFG_DIAG_CMDS.MTP_HP_SWM_FRU_DISP_FMT.format(self._slot+1)
        elif self._nic_type == NIC_Type.NAPLES100HPE:
            cmd = MFG_DIAG_CMDS.MTP_FRU_DISP_FMT.format(self._slot+1)
        elif self._vendor == NIC_Vendor.HPE:
            cmd = MFG_DIAG_CMDS.MTP_HP_FRU_DISP_FMT.format(self._slot+1)
        else:
            cmd = MFG_DIAG_CMDS.MTP_FRU_DISP_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg(self.nic_get_cmd_buf())
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        return True

    def nic_get_fru(self):
        if not self._sn or not self._mac or not self._pn or not self._vendor:

            return None
        else:
            return [self._sn, self._mac, self._pn, self._date, self._vendor]

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
    def nic_get_naples_pn(self):
        if not self._pn:
            return None
        else:
            return self._pn                            

    def nic_cpld_init(self):
        read_data = [0]
        rc = self.nic_read_cpld(0x00, read_data)
        if not rc:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        self._cpld_ver = "0x{:X}".format(read_data[0])

        if self._nic_type == NIC_Type.ORTANO or self._nic_type == NIC_Type.ORTANO2:
            # there are no CPLD timestamps; use major revision + minor revision
            read_data = [0]
            rc = self.nic_read_cpld(0x1e, read_data)
            if not rc:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            self._cpld_timestamp = "0x{:02d}".format(read_data[0])
            return True
        elif self._nic_type == NIC_Type.NAPLES25SWMDELL:
            # no timestamp, minor revision at 0x22 only
            read_data = [0]
            rc = self.nic_read_cpld(0x22, read_data)
            if not rc:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            self._cpld_timestamp = "{:02d}".format(read_data[0])
            return True
        elif self._nic_type == NIC_Type.TAORMINA:
            # ver and timestamp are not maintained...use fpgautil on host to read usercode
            cmd = "{:s}fpgautil elba {:d} cpld uc".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, self._slot)
            cmd_buf = self.mtp_get_info(cmd, timeout=100)
            if not cmd_buf:
                self.nic_set_err_msg("{:s} failed".format(cmd))
                return False
            uc_match = re.search("= ?(0x\d{4}(\d{4}))", cmd_buf)
            if uc_match:
                self._cpld_timestamp = uc_match.group(2)
            else:
                return False
            return True
        else:
            # get the month timestamp
            read_data = [0]
            rc = self.nic_read_cpld(0x22, read_data)
            if not rc:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            month = read_data[0]

            # get the date timestamp
            read_data = [0]
            rc = self.nic_read_cpld(0x23, read_data)
            if not rc:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            date = read_data[0]

            self._cpld_timestamp = "{:02d}-{:02d}".format(month, date)
            return True
    
    
    def nic_get_cpld(self):
        if not self._cpld_ver or not self._cpld_timestamp:
            return None
        else:
            return [self._cpld_ver, self._cpld_timestamp]


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
        if self._nic_type == NIC_Type.ORTANO or self._nic_type == NIC_Type.ORTANO2 or self._nic_type == NIC_Type.TAORMINA:
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
        if self._nic_type == NIC_Type.ORTANO or self._nic_type == NIC_Type.ORTANO2 or self._nic_type == NIC_Type.TAORMINA:
            nic_cmd = MFG_DIAG_CMDS.NIC_CPLD_WRITE_ELBA_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, reg_addr, write_data)
        cpld_buf = self.nic_get_info(nic_cmd)
        if not cpld_buf:
            return False
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
                    errlist.append(" ERROR: OCP CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} Clear".format(row[3], adapt_read_data[0], row[4]) )
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
                    errlist.append(" ERROR: OCP CPLD REG 0x{:x}:  READ 0x{:X}  Expect BIT 0x{:X} CLEAR".format(row[3], adapt_read_data[0], row[4]) )
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
        scan_chain_reg0_mask = 0xFE
        scan_chain_reg0_exp  = 0x5E
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
            self.nic_set_err_msg(cmd_buf)
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

        """
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS.GET_BOARD_CONFIG_FMT)
        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS.SET_BOARD_CONFIG_FMT.format(preset_config))
        if ("brdcfg0 write OK"  in cmd_buf
        and "brdcfg0 verify OK" in cmd_buf
        and "brdcfg1 write OK"  in cmd_buf
        and "brdcfg1 verify OK" in cmd_buf):
            pass
        else:
            self.nic_set_err_msg(cmd_buf)
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        cmd_buf = self.nic_get_info(MFG_DIAG_CMDS.GET_BOARD_CONFIG_FMT)

        return True

    def nic_console_uboot_env(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        self._nic_handle.sendline('sysreset.sh')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["Autoboot"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)

        #Send Ctrl-C by '\x03'
        self._nic_handle.sendline('\x03')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["DSC# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
        if idx < 0:
            self.nic_set_err_msg("Unable to reach uboot prompt in time")
            return False

        nic_cmd_list = list()
        nic_cmd_list.append('setenv memdp_tot_size 12G')
        nic_cmd_list.append('setenv mem_bypass_size 0')
        nic_cmd_list.append('setenv core_clock_freq 1100000000')
        nic_cmd_list.append('setenv bootargs isolcpus=2,3,6,7,10,11,14,15 nohz_full=2,3,6,7,10,11,14,15 rcu_nocbs=2,3,6,7,10,11,14,15 rcu_nocb_poll irqaffinity=0-1 console=ttyS0,115200n8')
        nic_cmd_list.append('saveenv')
        nic_cmd_list.append('env print')
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, ["DSC#"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False

        self._nic_handle.sendline('reset')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["Press enter"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
        if idx < 0:
            self.nic_set_err_msg("Unable to reach elba linux shell")
            return False

        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    def nic_setup_device_config(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        nic_cmd_list = list()
        # nic_cmd_list.append("\n")
        # nic_cmd_list.append("\n")
        # nic_cmd_list.append("\n")
        # nic_cmd_list.append("\n")
        nic_cmd_list.append("mount -t ext4 /dev/mmcblk0p6 /sysconfig/config0")

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False


        nic_cmd_list = list()
        nic_cmd_list.append("rm /sysconfig/config0/device.conf")
        nic_cmd_list.append('echo { >> /sysconfig/config0/device.conf')
        nic_cmd_list.append('echo \\"device-profile\\": \\"bitw-smart-service\\", >> /sysconfig/config0/device.conf')
        nic_cmd_list.append('echo \\"memory-profile\\": \\"default\\", >> /sysconfig/config0/device.conf')
        nic_cmd_list.append('echo \\"oper-mode\\": \\"bitw-smart-service\\", >> /sysconfig/config0/device.conf')
        nic_cmd_list.append('echo \\"port-admin-state\\": \\"PORT_ADMIN_STATE_ENABLE\\", >> /sysconfig/config0/device.conf')
        nic_cmd_list.append('echo \\"delay-host-bringup\\": \\"false\\" >> /sysconfig/config0/device.conf')
        nic_cmd_list.append('echo } >> /sysconfig/config0/device.conf')
        nic_cmd_list.append("sync")

        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False


        nic_cmd_list = list()
        nic_cmd_list.append("cat /sysconfig/config0/device.conf")
        for nic_cmd in nic_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            if idx < 0:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.nic_console_detach()
                return False
        cmd_buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        if not cmd_buf:
            self.nic_set_err_msg("Output empty for command {:s}".format(nic_cmd_list[-1]))
            self.nic_console_detach()
            return False
        if "delay-host-bringup" not in cmd_buf:
            self.nic_console_detach()
            self.nic_set_cmd_buf(cmd_buf)
            self.nic_set_err_msg("Setup of device.conf failed")
            return False


        


        """
        self._nic_handle.sendline("\n")
        self._nic_handle.sendline("\n")
        self._nic_handle.sendline("\n")
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
        self._nic_handle.sendline("\n")
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
        #self._nic_handle.sendline('mount -t ext4 /dev/mmcblk0p6 /sysconfig/config0')
        #idx = libmfg_utils.mfg_expect(self._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
        time.sleep(1)
        self._nic_handle.sendline('mount -t ext4 /dev/mmcblk0p6 /sysconfig/config0')
        time.sleep(1)
        self._nic_handle.sendline('rm /sysconfig/config0/device.conf')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["exists", "# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
        time.sleep(1)
        self._nic_handle.sendline('echo { >> /sysconfig/config0/device.conf')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
        self._nic_handle.sendline('echo \\"device-profile\\": \\"bitw-smart-service\\", >> /sysconfig/config0/device.conf')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
        self._nic_handle.sendline('echo \\"memory-profile\\": \\"default\\", >> /sysconfig/config0/device.conf')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
        self._nic_handle.sendline('echo \\"oper-mode\\": \\"bitw-smart-service\\", >> /sysconfig/config0/device.conf')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
        self._nic_handle.sendline('echo \\"port-admin-state\\": \\"PORT_ADMIN_STATE_ENABLE\\", >> /sysconfig/config0/device.conf')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
        self._nic_handle.sendline('echo \\"delay-host-bringup\\": \\"false\\" >> /sysconfig/config0/device.conf')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
        self._nic_handle.sendline('echo } >> /sysconfig/config0/device.conf')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
        time.sleep(1)
        self._nic_handle.sendline('sync')
        time.sleep(1)
        self._nic_handle.sendline('cat /sysconfig/config0/device.conf')
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["delay-host-bringup"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
        if idx < 0:
            self.cli_log_err("setup device.conf failed", level=0)
            ret = False
        time.sleep(2)

        """


        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True

    def nic_memtun_init(self):
        cmd = "ps -A | grep memtun"
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            return False

        if self._slot == 0: #assuming slot 0 is always already configured first
            cmd = "killall memtun"
            if not self.mtp_exec_cmd(cmd):
                self.nic_set_err_msg("{:s} failed".format(cmd))
                return False

        time.sleep(5)
    
        memtun_ip = NIC_IP_Address.MEMTUN_IP[self._slot]
        mgmt_ip   = NIC_IP_Address.MGMT_IP[self._slot]
        pci_bus = NIC_IP_Address.MEMTUN_PCI_BUS[self._slot]

        cmd = "{:s}memtun -s {:s} {:s} &".format("/fs/nos/home_diag/diag/tools/", pci_bus, memtun_ip)
        if not self.mtp_exec_cmd(cmd, timeout=60):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            return False
        time.sleep(2)

        cmd = "ping -c 1 {:s}".format(mgmt_ip)
        pingsuccess = False
        for x in range(2):
            if self.mtp_exec_cmd(cmd, sig_list=["1 received"], timeout=30):
                pingsuccess = True
            # else:
            #     self.nic_set_err_msg("NIC-0{} : {:s} failed, try again".format(slot+1, cmd))
            if pingsuccess:
                break
        if not pingsuccess:
            self.nic_set_err_msg("NIC-0{} : {:s} failed,".format(slot+1, cmd))
            return False

        return True

    def nic_memtun_validate(self):
        slot = self._slot
        mgmt_ip = NIC_IP_Address.MGMT_IP[slot]
        cmd = "ping -c 4 {:s}".format(mgmt_ip)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            return False
        time.sleep(4)
        cmd_buf = self.nic_get_cmd_buf()
        if "100% packet loss" in cmd_buf:
            self.nic_set_err_msg(cmd_buf)
            return False
        return True

    def nic_config_erase(self):
        cmd = "board_config -e"
        nic_cmd_list = list()
        nic_cmd_list.append(cmd)
        if not self.nic_exec_cmds(nic_cmd_list):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            return False

        return True

    def nic_fwenv_erase(self):
        cmd = "fwenv -E"
        nic_cmd_list = list()
        nic_cmd_list.append(cmd)
        if not self.nic_exec_cmds(nic_cmd_list):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            return False

        return True

    def nic_config_verify(self):
        # check `board_config -r` shows "config not set" in both brdcfg0 and brdcfg1
        cmd = "board_config -r"
        sig = "config not set"

        cmd_buf = self.nic_get_info(cmd)

        if not cmd_buf:
            self.nic_set_err_msg("{:s} failed".format(cmd))
            return False
        elif sig not in cmd_buf:
            self.nic_set_err_msg("board_config not erased")
            return False


        # fwenv shows "Flashed erased; using default values"
        cmd = "fwenv"
        sig = "Flash erased; using defaults"
        
        cmd_buf = self.nic_get_info(cmd)
        if not cmd_buf:
            self.nic_set_err_msg("{:s} failed".format(cmd))
            return False
        elif sig not in cmd_buf:
            self.nic_set_err_msg("Uboot variables are not defaults")
            return False


        # pdsctl show system --frequency shows 1100, 3000, 1500
        cmd = "pdsctl show system --frequency"
        sig_list = ["1100", "3000", "1500"]
        
        cmd_buf = self.nic_get_info(cmd)
        if False in [sig in cmd_buf for sig in sig_list]:
            self.nic_set_err_msg("Incorrect operating frequency")
            return False

        return True

    def nic_fw_verify(self):

        # dump
        cmd = MFG_DIAG_CMDS.NIC_IMG_DISP1_FMT
        nic_cmd_list = list()
        nic_cmd_list.append(cmd)
        if not self.nic_exec_cmds(nic_cmd_list):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            return False


        # get boot image info

        cmd = MFG_DIAG_CMDS.NIC_BOOT_DISP_FMT
        nic_cmd_list = list()
        nic_cmd_list.append(cmd)
        if not self.nic_exec_cmds(nic_cmd_list):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            return False
        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self.nic_get_cmd_buf())
        match = re.findall(r"(\w+fw\w?)", buf)
        if match:
            self._boot_image = match[0]
            # check if boot image is valid
            if self._boot_image == "mainfwa":
                pass
            else:
                self.nic_set_err_msg("Incorrect boot image: {:s}".format(self._boot_image))
                return False
        else:
            self.nic_set_err_msg("Unable to read boot image")
            return False


        cmd = MFG_DIAG_CMDS.NIC_IMG_VER_DISP_FMT
        nic_cmd_list = list()
        nic_cmd_list.append(cmd)
        if not self.nic_exec_cmds(nic_cmd_list):
            self.nic_set_err_msg("{:s} failed".format(cmd))
            return False

        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self.nic_get_cmd_buf())
        match = re.findall(r"SMP(?: PREEMPT)? (.* 20\d{2})", buf)
        if match:
            kernel_ver = match[0]
            # check if timestamp is valid
            try:
                # Tue Jun 22 15:28:57 PDT 2021
                dt = datetime.strptime(kernel_ver, "%a %b %d %X %Z %Y")
                self._kernel_timestamp = dt.strftime("%m-%d-%Y")
            except ValueError:
                # this version of datetime may not accept timezone as PDT/PST
                try:
                    # Wed Feb 24 12:51:26 PST 2021
                    kernel_ver = kernel_ver[:-8] + kernel_ver[-4:] #remove the timezone
                    dt = datetime.strptime(kernel_ver, "%a %b %d %X %Y")
                    self._kernel_timestamp = dt.strftime("%m-%d-%Y")
                except ValueError:
                    return False

            exp_version = NIC_IMAGES.mainfw_dat[self._nic_type]
            got_version = self._kernel_timestamp
            if got_version == exp_version:
                return True
            else:
                self.nic_set_err_msg("Incorrect mainfw version. Expected: {:s}, got: {:s}".format(exp_version, got_version))
        else:
            self.nic_set_err_msg("Unable to read FW date")
            return False


