import pexpect
import time
import os
import sys
import libmfg_utils
import random
import re
import threading
from datetime import datetime
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
from libmfg_cfg import MFG_NIC_VRM_PROGRAM
from libmfg_cfg import MFG_NIC_QSPI_PROGRAM
from libmfg_cfg import MFG_NIC_EMMC_PROGRAM

from libdefs import NIC_Type
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MTP_Const
from libdefs import NIC_Status
from libdefs import NIC_Port_Mask
from libdefs import MFG_DIAG_CMDS
from libdefs import MFG_DIAG_SIG

class nic_ctrl():
    def __init__(self, slot, diag_log_filep, diag_cmd_log_filep=None, dbg_mode = False):
        self._slot = slot
        self._debug_mode = dbg_mode
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._nic_status = NIC_Status.NIC_STA_OK
        self._nic_con_prompt = "#"

        self._cpld_ver = None
        self._cpld_timestamp = None
        self._sn = None
        self._mac = None
        self._pn = None
        self._img_timestamp = None
        self._boot_image = None

        self._nic_type = None
        self._nic_handle = None
        self._nic_prompt = None
        self._nic_sn = None
        self._err_msg = None
        self._cmd_buf = None


    def nic_handle_init(self, handle, prompt):
        self._nic_handle = handle
        self._nic_prompt = prompt
        self._nic_handle.logfile_read = self._diag_filep
        self._nic_handle.logfile_send = self._diag_cmd_filep


    def nic_set_type(self, nic_type):
        self._nic_type = nic_type


    def nic_set_err_msg(self, err_msg):
        self._err_msg = err_msg


    def nic_set_cmd_buf(self, cmd_buf):
        self._cmd_buf = cmd_buf


    def nic_set_status(self, status):
        self._nic_status = status


    def nic_check_status(self):
        if self._nic_status == NIC_Status.NIC_STA_OK:
            return True
        else:
            return False


    def mtp_exec_cmd(self, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False
        self.nic_set_cmd_buf(self._nic_handle.before)
        return True


    def nic_exec_cmds(self, nic_cmd_list, timeout=MTP_Const.NIC_CON_CMD_DELAY):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot)
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

        ret = True
        cmd_list = nic_cmd_list[:]
        cmd_list.append("sync")
        for nic_cmd in cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout)
            if idx < 0:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_err_msg(self._nic_handle.before)
                ret = False
                break
            time.sleep(1)

        cmd = "exit"
        if not self.mtp_exec_cmd(cmd):
            return False

        return ret


    def nic_get_info(self, nic_cmd):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot)
        cmd = libmfg_utils.get_ssh_connect_cmd(NIC_MGMT_USERNAME, ipaddr)
        self._nic_handle.sendline(cmd)
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, ["assword:", self._nic_con_prompt], timeout=MTP_Const.SSH_PASSWORD_DELAY)
            if idx < 0:
                libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_err_msg(self._nic_handle.before)
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
            self.nic_set_err_msg(self._nic_handle.before)
            info_buf = None
        else:
            info_buf = self._nic_handle.before

        cmd = "exit"
        if not self.mtp_exec_cmd(cmd):
            return False

        return info_buf


    def nic_get_err_msg(self):
        return self._err_msg


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


    def nic_console_init(self):
        loop = 0
        # goto the nic_con dir
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        while loop < MTP_Const.NIC_CON_INIT_RETRY:
            cmd = MFG_DIAG_CMDS.NIC_CON_INIT_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.NIC_CON_INIT_DELAY):
                loop += 1
                continue

            if MFG_DIAG_SIG.NIC_CON_OK_SIG in self.nic_get_cmd_buf():
                break
            else:
                # retry
                if not self.nic_power_cycle():
                    self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
                    return False
                loop += 1
                continue

        if loop >= MTP_Const.NIC_CON_INIT_RETRY:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True


    def nic_console_attach(self):
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_CON_ATTACH_FMT.format(self._slot+1))
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["Terminal ready"], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            return False

        # check if console prompt is shown
        try:
            self._nic_handle.expect_exact(self._nic_con_prompt)
        except pexpect.TIMEOUT:
            # if prompt is not there, just send return
            self._nic_handle.sendline("")
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx < 0:
                self.nic_set_err_msg(self._nic_handle.before)
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


    def nic_set_diag_boot(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # set default to diag boot
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_SET_DIAG_BOOT_FMT)
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


    def nic_verify_sw_boot(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # dump the boot up image
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_DISP_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_err_msg(self._nic_handle.before)
            self.nic_console_detach()
            return False

        match = re.findall(r"(\w+fw\w?)", self._nic_handle.before)
        if match:
            if match[0] == "mainfwa" or match[0] == "mainfwb":
                return True
            else:
                self.nic_set_err_msg(self._nic_handle.before)
                self.nic_console_detach()
                return False
        else:
            self.nic_set_err_msg(self._nic_handle.before)
            self.nic_console_detach()
            return False

        # detach the console connection
        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        return True


    def nic_boot_info_init(self):
        if not self.nic_console_attach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        # get boot image info
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_DISP_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_console_detach()
            return False

        match = re.findall(r"(\w+fw\w?)", self._nic_handle.before)
        if match:
            self._boot_image = match[0]
        else:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            self.nic_console_detach()
            return False

        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_IMG_VER_DISP_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            self.nic_console_detach()
            return False

        # get kernel build timestamp
        match = re.findall(r"SMP (.* 20\d{2})", self._nic_handle.before)
        if match:
            kernel_ver = match[0]
        else:
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            self.nic_console_detach()
            return False

        if not self.nic_console_detach():
            self.nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
            return False

        dt = datetime.strptime(kernel_ver, "%a %b %d %X %Z %Y")
        self._kernel_timestamp = dt.strftime("%m-%d-%Y")

        return True


    def nic_mgmt_init(self):
        # goto the nic_con dir
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_exec_cmd(cmd):
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

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


    def nic_program_fru(self, date, sn, mac, pn):
        if self._nic_type != NIC_Type.NAPLES100:
            cmd = MFG_DIAG_CMDS.MTP_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
            if not self.mtp_exec_cmd(cmd):
                return False

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_FRU_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, date, sn, mac, pn)
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
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
            self.nic_set_err_msg(self._nic_handle.before)
            return False

        self._nic_handle.sendline(NIC_MGMT_PASSWORD)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False

        return True


    def nic_program_cpld(self, cpld_img):
        if not self.nic_copy_image(cpld_img):
            return False
        img_name = os.path.basename(cpld_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_CPLD_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, img_name)
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        return True


    def nic_get_cpld(self):
        if self._nic_type == NIC_Type.NAPLES100:
            if cpld_ver != MFG_NAPLES100_CPLD_VERSION or cpld_timestamp != MFG_NAPLES100_CPLD_TIMESTAMP:
                return False
            else:
                return True
        elif self._nic_type == NIC_Type.NAPLES25:
            if cpld_ver != MFG_NAPLES25_CPLD_VERSION or cpld_timestamp != MFG_NAPLES25_CPLD_TIMESTAMP:
                return False
            else:
                return True
        else:
            return False

        return True


    def nic_program_vrm(self, vrm_img, vrm_img_cksum):
        if not self.nic_copy_image(vrm_img):
            return False
        img_name = os.path.basename(vrm_img)

        nic_cmd_list = list()
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        return True


    def nic_verify_vrm(self, vrm_img, vrm_img_cksum):
        return True


    def nic_program_qspi(self, qspi_img):
        if not self.nic_copy_image(qspi_img):
            return False
        img_name = os.path.basename(qspi_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_QSPI_PROG_FMT.format(img_name)
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list):
            return False

        return True


    def nic_program_emmc(self, emmc_img):
        if not self.nic_copy_image(emmc_img):
            return False
        img_name = os.path.basename(emmc_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_INIT_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_PROG_FMT.format(img_name)
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=OS_CMD_DELAY):
            return False

        return True


    def nic_copy_diag_img(self):
        nic_cmd_list = list()
        nic_cmd = "mkdir -p {:s}".format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH)
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        nic_diag_list = ["diag", "start_diag.arm64.sh"]
        for util in nic_diag_list:
            img = MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH + util
            if not self.nic_copy_image(img, directory=MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH):
                return False

        return True


    def nic_start_diag(self):
        # setup diag env on nic
        nic_cmd_list = list()

        nic_cmd = MFG_DIAG_CMDS.NIC_DIAG_INIT_FMT.format(self._slot+1)
        nic_cmd_list.append(nic_cmd)
        nic_cmd = "source /etc/profile"
        nic_cmd_list.append(nic_cmd)

        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        # Start NIC DSP
        cmd = MFG_DIAG_CMDS.NIC_DSP_START_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        return True


    def nic_set_vmarg(self, vmarg_param):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_VMARG_SET_FMT.format(vmarg_param)
        nic_cmd_list.append(nic_cmd)

        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        return True


    def nic_set_sw_boot(self):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_SET_DIAG_BOOT_FMT
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list):
            return False

        return True


    def nic_fru_init(self):
        nic_cmd = MFG_DIAG_CMDS.NIC_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        fru_buf = self.nic_get_info(nic_cmd)
        if not fru_buf:
            return False
        match = re.findall(NAPLES_DISP_SN_FMT, fru_buf)
        if match:
            self._sn = match[0]
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        match = re.findall(NAPLES_DISP_MAC_FMT, fru_buf)
        if match:
            self._mac = match[0]
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False
        match = re.findall(NAPLES_DISP_PN_FMT, fru_buf)
        if match:
            self._pn = match[0]
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if self._nic_type != NIC_Type.NAPLES100:
            cmd = MFG_DIAG_CMDS.MTP_FRU_DISP_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd):
                return False
            match = re.findall(NAPLES_DISP_SN_FMT, self.nic_get_cmd_buf())
            if match:
                sn = match[0]
            else:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            match = re.findall(NAPLES_DISP_MAC_FMT, self.nic_get_cmd_buf())
            if match:
                mac = match[0]
            else:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            match = re.findall(NAPLES_DISP_PN_FMT, self.nic_get_cmd_buf())
            if match:
                pn = match[0]
            else:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

            if self._sn != sn or self._mac != mac or self._pn != pn:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False

        return True


    def nic_get_fru(self):
        if not self._sn or not self._mac or not self._pn:
            return None
        else:
            return [self._sn, self._mac, self._pn]


    def nic_cpld_init(self):
        cpld_reg = 0
        nic_cmd = MFG_DIAG_CMDS.NIC_CPLD_READ_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, cpld_reg)
        cpld_buf = self.nic_get_info(nic_cmd)
        if not cpld_buf:
            return False
        match = re.findall(r"(0x[0-9a-fA-F]+)", cpld_buf)
        if match:
            self._cpld_ver = match[0]
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        # get the month timestamp
        cpld_reg = 34
        nic_cmd = MFG_DIAG_CMDS.NIC_CPLD_READ_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, cpld_reg)
        cpld_buf = self.nic_get_info(nic_cmd)
        if not cpld_buf:
            return False
        match = re.findall(r"(0x[0-9a-fA-F]+)", cpld_buf)
        if match:
            month = int(match[0], 16)
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        # get the date timestamp
        cpld_reg = 35
        nic_cmd = MFG_DIAG_CMDS.NIC_CPLD_READ_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, cpld_reg)
        cpld_buf = self.nic_get_info(nic_cmd)
        if not cpld_buf:
            return False
        match = re.findall(r"(0x[0-9a-fA-F]+)", cpld_buf)
        if match:
            date = int(match[0], 16)
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        self._cpld_timestamp = "{:02d}-{:02d}".format(month, date)

        return True


    def nic_get_cpld(self):
        if not self._cpld_ver or not self._cpld_timestamp:
            return None
        else:
            return [self._cpld_ver, self._cpld_timestamp]


    def nic_get_boot_info(self):
        if not self._boot_image or not self._kernel_timestamp:
            return None
        else:
            return [self._boot_image, self._kernel_timestamp]


    def nic_get_capri_pll_sta(self):
        pll_sta_reg_exp = r"data=(0x[0-9a-fA-F]+)"

        cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return None

        reg_addr = 0x26
        cmd = MFG_DIAG_CMDS.MTP_SMB_CMD_FMT.format(reg_addr, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return None
        match = re.findall(pll_sta_reg_exp, self.nic_get_cmd_buf())
        if not match:
            return None
        else:
            reg26_data = int(match[0], 16)

        reg_addr = 0x28
        cmd = MFG_DIAG_CMDS.MTP_SMB_CMD_FMT.format(reg_addr, self._slot+1)
        if not self.mtp_exec_cmd(cmd):
            return None
        match = re.findall(pll_sta_reg_exp, self.nic_get_cmd_buf())
        if not match:
            self.cli_log_slot_err(slot, "Failed to run command {:s} on MTP".format(cmd))
            return None
        else:
            reg28_data = int(match[0], 16)

        return [reg26_data, reg28_data]
