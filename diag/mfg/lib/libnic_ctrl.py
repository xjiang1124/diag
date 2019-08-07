import pexpect
import time
import os
import libmfg_utils
import re
from datetime import datetime
from libmfg_cfg import MTP_INTERNAL_MGMT_IP_ADDR
from libmfg_cfg import MTP_INTERNAL_MGMT_NETMASK
from libmfg_cfg import NIC_MGMT_USERNAME
from libmfg_cfg import NIC_MGMT_PASSWORD
from libmfg_cfg import HP_SN_FMT
from libmfg_cfg import HP_DISP_SN_FMT
from libmfg_cfg import HP_DISP_PN_FMT
from libmfg_cfg import NAPLES_SN_FMT
from libmfg_cfg import NAPLES_DISP_SN_FMT
from libmfg_cfg import NAPLES_DISP_PN_FMT
from libmfg_cfg import NAPLES_DISP_MAC_FMT
from libmfg_cfg import NAPLES_DISP_DATE_FMT
from libmfg_cfg import MFG_NIC_FRU_PROGRAM
from libmfg_cfg import MFG_NIC_CPLD_PROGRAM
from libmfg_cfg import MFG_NIC_QSPI_PROGRAM
from libmfg_cfg import MFG_NIC_EMMC_PROGRAM
from libmfg_cfg import MFG_VALID_FW_LIST

from libdefs import NIC_Type
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

class nic_ctrl():
    def __init__(self, slot, diag_log_filep, diag_cmd_log_filep=None, dbg_mode = False):
        self._slot = slot
        self._debug_mode = dbg_mode
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._nic_status = NIC_Status.NIC_STA_POWEROFF
        self._nic_con_prompt = "#"

        self._cpld_ver = None
        self._cpld_timestamp = None
        self._sn = None
        self._mac = None
        self._pn = None
        self._img_timestamp = None
        self._boot_image = None
        self._vendor = None

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
        self._nic_status = NIC_Status.NIC_STA_OK


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


    def nic_exec_rst_cmd(self, nic_rst_cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
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

        self._nic_handle.sendline(nic_rst_cmd)
        # Here ssh should disconnected automatically
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
        if idx < 0:
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_err_msg(self._nic_handle.before)
            return False
        else:
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
            elif fail_sig != None:
                if fail_sig in self._nic_handle.before:
                    self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                    self.nic_set_err_msg(self._nic_handle.before)
                    ret = False
                    break
            else:
                pass
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


    def nic_console_attach(self):
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_CON_ATTACH_FMT.format(self._slot+1))
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["Terminal ready"], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            return False

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
            return False

        # dump the boot up image
        self._nic_handle.sendline(MFG_DIAG_CMDS.NIC_BOOT_DISP_FMT)
        idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.nic_console_detach()
            return False
        # remove the potential special character
        buf = libmfg_utils.special_char_removal(self._nic_handle.before)
        match = re.findall(r"(\w+fw\w?)", buf)

        # 1. remove diag utils on NIC
        # 2. kill all processes
        # 3. sync
        # 4. umount
        dev = "/dev/mmcblk0p10"
        mount_point = "/data"
        emmc_mount_cmd = MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT.format(dev, mount_point)
        nic_shutdown_cmd_list = [emmc_mount_cmd,
                                 MFG_DIAG_CMDS.NIC_DIAG_CLEANUP_FMT,
                                 MFG_DIAG_CMDS.NIC_KILL_PROCESS_FMT,
                                 MFG_DIAG_CMDS.NIC_SYNC_FS_FMT,
                                 MFG_DIAG_CMDS.NIC_SW_UMOUNT_FMT]
        for nic_cmd in nic_shutdown_cmd_list:
            self._nic_handle.sendline(nic_cmd)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
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

        if match:
            if match[0] == "mainfwa" or match[0] == "mainfwb":
                self.nic_console_detach()
                return True
            else:
                self.nic_set_err_msg(self._nic_handle.before)
                self.nic_console_detach()
                return False
        else:
            self.nic_set_err_msg(self._nic_handle.before)
            self.nic_console_detach()
            return False


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
            match = re.findall(r"SMP (.* 20\d{2})", buf)
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
            self.nic_set_err_msg(self._nic_handle.before)
            return False

        return True


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
        if not self.nic_vendor_init(sn):
            return False

        if self.nic_2nd_fru_exist(pn):
            if self._vendor == NIC_Vendor.HPE:
                cmd = MFG_DIAG_CMDS.MTP_HP_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
            else:
                cmd = MFG_DIAG_CMDS.MTP_FRU_PROG_FMT.format(date, sn, mac, pn, self._slot+1)
            if not self.mtp_exec_cmd(cmd, timeout=MTP_Const.MTP_FRU_UPDATE_DELAY):
                return False

        nic_cmd_list = list()
        if self._vendor == NIC_Vendor.HPE:
            nic_cmd = MFG_DIAG_CMDS.NIC_HP_FRU_PROG_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, date, sn, mac, pn)
        else:
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


    def nic_refresh_cpld(self):
        nic_cpld_ref_cmd = MFG_DIAG_CMDS.NIC_CPLD_REF_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        if not self.nic_exec_rst_cmd(nic_cpld_ref_cmd, timeout=MTP_Const.OS_CMD_DELAY):
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

        # check signature
        if MFG_DIAG_SIG.NIC_ESEC_CPLD_VERIFY_SIG not in self.nic_get_cmd_buf():
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


    def nic_program_qspi(self, qspi_img):
        if not self.nic_copy_image(qspi_img):
            return False
        img_name = os.path.basename(qspi_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_QSPI_PROG_FMT.format(img_name)
        qspi_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, fail_sig=qspi_fail_sig):
            return False

        return True


    def nic_init_emmc(self, init = False):
        nic_cmd_list = list()
        dev = "/dev/mmcblk0p10"
        mount_point = "/data"
        if init:
            nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_INIT_FMT
            nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT.format(dev, mount_point)
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        # check if mount is ok
        nic_cmd = MFG_DIAG_CMDS.NIC_MOUNT_DISP_FMT.format(dev)
        mount_sig = MFG_DIAG_SIG.NIC_MOUNT_OK_SIG.format(dev, mount_point)
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


    def nic_program_emmc(self, emmc_img):
        if not self.nic_copy_image(emmc_img):
            return False
        img_name = os.path.basename(emmc_img)

        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_INIT_FMT
        nic_cmd_list.append(nic_cmd)
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_PROG_FMT.format(img_name)
        emmc_fail_sig = MFG_DIAG_SIG.NIC_FWUPDATE_FAIL_SIG
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY, fail_sig=emmc_fail_sig):
            return False

        return True


    def nic_copy_diag_img(self):
        nic_cmd_list = list()
        nic_cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH)
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
            return False

        nic_diag_list = ["diag", "start_diag.arm64.sh"]
        for util in nic_diag_list:
            img = MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH + util
            if not self.nic_copy_image(img, directory=MTP_DIAG_Path.ONBOARD_NIC_DIAG_PATH):
                return False

        nic_diag_list = ["nic_arm", "nic_util"]
        for util in nic_diag_list:
            img = MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH + util
            if not self.nic_copy_image(img, directory=MTP_DIAG_Path.ONBOARD_NIC_DIAG_UTIL_PATH):
                return False

        return True


    def nic_save_logfile(self, logfile_list):
        ipaddr = libmfg_utils.get_nic_ip_addr(self._slot)
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
        nic_cmd = MFG_DIAG_CMDS.NIC_SET_SW_BOOT_FMT
        nic_cmd_list.append(nic_cmd)
        if not self.nic_exec_cmds(nic_cmd_list):
            return False

        return True


    # for the Naples100 before PP, no 2nd fru instance
    def nic_2nd_fru_exist(self, pn):
        for item in ["68-0003-01", "68-0003-02", "68-0003-03", "68-0004-02", "68-0004-03"]:
            if item in pn:
                return False
        return True


    # check nic mfg vendor based on the sn format
    def nic_vendor_init(self, sn=None):
        if sn == None:
            nic_cmd = MFG_DIAG_CMDS.NIC_VENDOR_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
            fru_buf = self.nic_get_info(nic_cmd)
        else:
            fru_buf = sn

        match = re.findall(NAPLES_SN_FMT, fru_buf)
        if match:
            self._vendor = NIC_Vendor.PENSANDO
            return True
        match = re.findall(HP_SN_FMT, fru_buf)
        if match:
            self._vendor = NIC_Vendor.HPE
            return True

        self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
        return False


    def nic_fru_init(self):
        if not self.nic_vendor_init():
            return False

        if self._vendor == NIC_Vendor.HPE:
            nic_cmd = MFG_DIAG_CMDS.NIC_HP_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        else:
            nic_cmd = MFG_DIAG_CMDS.NIC_FRU_DISP_FMT.format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH)
        fru_buf = self.nic_get_info(nic_cmd)
        if not fru_buf:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        # retrieve card serial number
        if self._vendor == NIC_Vendor.HPE:
            match = re.findall(HP_DISP_SN_FMT, fru_buf)
        else:
            match = re.findall(NAPLES_DISP_SN_FMT, fru_buf)
        if match:
            self._sn = match[0]
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        # retrieve card MAC address
        match = re.findall(NAPLES_DISP_MAC_FMT, fru_buf)
        if match:
            self._mac = match[0]
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        # retrieve card PN
        if self._vendor == NIC_Vendor.HPE:
            match = re.findall(HP_DISP_PN_FMT, fru_buf)
        else:
            match = re.findall(NAPLES_DISP_PN_FMT, fru_buf)

        if match:
            self._pn = match[0]
        else:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        if self.nic_2nd_fru_exist(self._pn):
            if self._vendor == NIC_Vendor.HPE:
                cmd = MFG_DIAG_CMDS.MTP_HP_FRU_DISP_FMT.format(self._slot+1)
            else:
                cmd = MFG_DIAG_CMDS.MTP_FRU_DISP_FMT.format(self._slot+1)
            if not self.mtp_exec_cmd(cmd):
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            # secondary SN
            if self._vendor == NIC_Vendor.HPE:
                match = re.findall(HP_DISP_SN_FMT, self.nic_get_cmd_buf())
            else:
                match = re.findall(NAPLES_DISP_SN_FMT, self.nic_get_cmd_buf())
            if match:
                sn = match[0]
            else:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            # secondary MAC
            match = re.findall(NAPLES_DISP_MAC_FMT, self.nic_get_cmd_buf())
            if match:
                mac = match[0]
            else:
                self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
                return False
            # secondary PN
            if self._vendor == NIC_Vendor.HPE:
                match = re.findall(HP_DISP_PN_FMT, self.nic_get_cmd_buf())
            else:
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
        if not self._sn or not self._mac or not self._pn or not self._vendor:
            return None
        else:
            return [self._sn, self._mac, self._pn, self._vendor]


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
            return None
        else:
            reg28_data = int(match[0], 16)

        return [reg26_data, reg28_data]
