import sys, os
import time
from libmfg_cfg import *
from libdefs import *
import libmfg_utils

NIC_MGMT_USERNAME = "root"
NIC_MGMT_PASSWORD = "pen123"

SSH_FAIL_SIG_LIST = ["Connection refused", "Network is unreachable", "Exiting with failure", "closed by remote host", "timed out", "lost connection", "No such file"]

class nic_ctrl():
    def __init__(self, slot, diag_log_filep, diag_cmd_log_filep=None, test_inst=None):
        self._slot = slot
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._nic_status = NIC_Status.NIC_STA_POWEROFF
        self._nic_missed_fa = False
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
        self._prod_num = None
        self._kernel_timestamp = None
        self._fw_json = None
        self._nic_type = None
        self._nic_handle = None
        self._nic_prompt = None # the NIC session's prompt on MTP
        self._err_msg = None
        self._cmd_buf = None

        self._asic_type = None
        self._ip_addr = None
        self._pcie_root_bus = None
        self._pcie_mgmt_bus = None
        self._fst_pcie_bus = None
        self._emmc_mfr_id = ""

        self._refresh_required = True
        self._failed_console_boot = False

        self._test_inst = test_inst

    def nic_handle_init(self, handle, prompt):
        self._nic_handle = handle
        self._nic_prompt = prompt
        self._nic_handle.logfile = None
        self._nic_handle.logfile_read = self._diag_filep
        self._nic_handle.logfile_send = self._diag_cmd_filep

    def nic_handle_close(self):
        self._nic_handle.logfile_send = None
        self._nic_handle.logfile_read = None
        self._nic_handle.close()

    def nic_get_cmd_buf(self):
        return self._cmd_buf

    def nic_set_cmd_buf(self, cmd_buf):
        self._cmd_buf = cmd_buf

    def log_nic_file(self, *args, **kwargs):
        return self._test_inst.log_nic_file(self._slot, *args, **kwargs)

    def cli_log_slot_inf(self, *args, **kwargs):
        return self._test_inst.cli_log_slot_inf(self._slot, *args, **kwargs)

    def cli_log_slot_err(self, *args, **kwargs):
        return self._test_inst.cli_log_slot_err(self._slot, *args, **kwargs)

    def nic_set_err_msg(self, err_msg):
        """ for backwards compatibility """
        return self.cli_log_slot_err(self._slot, err_msg)

    def nic_console_attach(self):
        cmd = "{:s}fpga_uart {:d}".format("/home/admin/eeupdate/", self._slot)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, ["Terminal ready", "connecting to serial port"], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.cli_log_slot_err("{:s} failed - no response".format(cmd))
            return False
        time.sleep(5)
        # send return
        self._nic_handle.sendline("")

        exp_list = [self._nic_con_prompt, "login:", "assword:", "No boot path found"]
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
            elif idx == 3:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.cli_log_slot_err("No firmware image found")
                self.nic_console_detach()
                return False
            else:
                self.nic_set_cmd_buf(self._nic_handle.before)
                self.cli_log_slot_err("Timeout connecting to NIC console")
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

    def nic_ssh_connect(self):
        ipaddr = self._ip_addr
        userid = NIC_MGMT_USERNAME
        passwd = NIC_MGMT_PASSWORD
        libmfg_utils.expect_clear_buffer(self._nic_handle)
        time.sleep(1)
        cmd = libmfg_utils.get_ssh_connect_cmd(userid, ipaddr)
        self._nic_handle.sendline(cmd)
        retries = 0
        while True:
            idx = libmfg_utils.mfg_expect(self._nic_handle, SSH_FAIL_SIG_LIST + ["assword:", self._nic_con_prompt], timeout=5)
            if idx < 0:
                # try one more time:
                if retries == 0:
                    retries += 1
                    continue
                libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
                self.cli_log_slot_err("Timed out waiting for NIC password prompt")
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
            elif idx < len(SSH_FAIL_SIG_LIST):
                libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
                self.cli_log_slot_err("ssh to NIC failed")
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False
            elif idx == len(SSH_FAIL_SIG_LIST):
                self._nic_handle.sendline(NIC_MGMT_PASSWORD)
                continue
            else:
                break

        return True

    def nic_console_test_section(func):
        def start_end(self, *args, **kwargs):
            if not self.nic_console_attach():
                return False
            ret = func(self, *args, **kwargs)
            if not self.nic_console_detach():
                return False
            return ret

        return start_end

    def nic_ssh_test_section(func):
        def start_end(self, *args, **kwargs):
            if not self.nic_ssh_connect():
                return False
            ret = func(self, *args, **kwargs)
            buf_before = self.nic_get_cmd_buf()
            if not self._nic_exec_cmd("exit"):
                self.nic_set_cmd_buf(buf_before)
                return False
            self.nic_set_cmd_buf(buf_before) # restore buffer before exit command
            return ret

        return start_end

    @nic_console_test_section
    def nic_exec_console_cmds(self, cmd_list, fail_sig_list=[], timeout=10):
        if isinstance(cmd_list, str):
            cmd_list = [cmd_list]
        for nic_cmd in cmd_list:
            if not self._nic_exec_cmd(nic_cmd, fail_sig_list, timeout):
                return False
        buf_before = self.nic_get_cmd_buf()
        if not self._nic_exec_cmd("sync"):
            self.nic_set_cmd_buf(buf_before)
            return False
        self.nic_set_cmd_buf(buf_before) # restore buffer before sync command
        return True

    @nic_ssh_test_section
    def nic_exec_ssh_cmds(self, cmd_list, fail_sig_list=[], timeout=10):
        if isinstance(cmd_list, str):
            cmd_list = [cmd_list]
        for nic_cmd in cmd_list:
            if not self._nic_exec_cmd(nic_cmd, fail_sig_list, timeout):
                return False
        buf_before = self.nic_get_cmd_buf()
        if not self._nic_exec_cmd("sync"):
            self.nic_set_cmd_buf(buf_before)
            return False
        self.nic_set_cmd_buf(buf_before) # restore buffer before sync command
        return True

    def _nic_exec_cmd(self, nic_cmd, fail_sig_list=[], timeout=10):
        libmfg_utils.expect_clear_buffer(self._nic_handle)
        self._nic_handle.sendline(nic_cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, SSH_FAIL_SIG_LIST + fail_sig_list + [self._nic_con_prompt], timeout)
        if idx < 0:
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt, self._nic_con_prompt], timeout)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.cli_log_slot_err("{:s} command failed".format(nic_cmd))
            return False
        elif idx < len(SSH_FAIL_SIG_LIST):
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.cli_log_slot_err("Connection to NIC interrupted")
            return False
        elif idx < len(SSH_FAIL_SIG_LIST + fail_sig_list):
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_con_prompt], timeout)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        else:
            self.nic_set_cmd_buf(self._nic_handle.before)
            pass

        return True

    def mtp_exec_cmd(self, *args, **kwargs):
        """ for backwards compatibility """
        return self._test_inst.mtp.nic_mtp_exec_cmd(self._slot, *args, **kwargs)

    def copy_file_to_nic(self, src, dst="/"):
        ipaddr = self._ip_addr
        userid = NIC_MGMT_USERNAME
        passwd = NIC_MGMT_PASSWORD
        libmfg_utils.expect_clear_buffer(self._nic_handle)
        time.sleep(1)
        cmd = "scp {:s} -r {:s} {:s}@{:s}:{:s}".format(libmfg_utils.get_ssh_option(), src, userid, ipaddr, dst)
        self._nic_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(self._nic_handle, SSH_FAIL_SIG_LIST + [self._nic_prompt, "assword:"], timeout=MTP_Const.SSH_PASSWORD_DELAY)
        if idx < 0:
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False
        elif idx < len(SSH_FAIL_SIG_LIST):
            libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout)
            self.nic_set_cmd_buf(self._nic_handle.before)
            self.cli_log_slot_err("Connection to NIC interrupted")
            return False
        elif idx == len(SSH_FAIL_SIG_LIST) + 1:
            self._nic_handle.sendline(NIC_MGMT_PASSWORD)
            idx = libmfg_utils.mfg_expect(self._nic_handle, [self._nic_prompt], timeout=MTP_Const.OS_CMD_DELAY)
            if idx < 0:
                self.nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
                self.nic_set_cmd_buf(self._nic_handle.before)
                return False

        return True


    def set_pcie_root_bus(self, pcie_bus):
        self._pcie_root_bus = pcie_bus

    def set_pcie_mgmt_bus(self, pcie_bus):
        self._pcie_mgmt_bus = pcie_bus

    def get_pcie_root_bus(self):
        return self._pcie_root_bus

    def get_pcie_mgmt_bus(self):
        return self._pcie_mgmt_bus

    @nic_console_test_section
    def nic_dummy_fru(self):
        fmt_dummy_fru_json = """
{{
    "manufacturing-date": "1612915200",
    "manufacturer": "Pensando",
    "product-name": "DSS-28400",
    "serial-number": "FSJ2115002D",
    "part-number": "DSS-28400",
    "frufileid": "06\/04\/21",
    "board-id": "1",
    "engineering-change-level": "0",
    "num-mac-address": "16",
    "mac-address": "04:90:81:00:12:26"
}}

        """
        dummy_fru_json = fmt_dummy_fru_json.format(self._slot)

        self._nic_handle.send("cat > /tmp/fru.json")
        self._nic_handle.send("\r")
        self._nic_handle.send(dummy_fru_json)
        self._nic_handle.send(chr(3))

        idx = libmfg_utils.mfg_expect_new(self._nic_handle, [self._nic_con_prompt], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
        if idx < 0:
            self.nic_set_cmd_buf(self._nic_handle.before)
            return False

        return True
