import sys
import os
import time
import pexpect
import threading
import re
import traceback
from datetime import datetime
import ipaddress

import libtest_utils
from libdefs import *
import libmfg_utils
from libmfg_cfg import *
from libnic_ctrl import nic_ctrl
from tests import *

class mtp_ctrl():
    def __init__(self, mtpid, filep, diag_log_filep, diag_nic_log_filep_list, diag_cmd_log_filep=None, ts_cfg = None, usb_ts_cfg = None, mgmt_cfg = None, num_of_slots = MTP_Const.MTP_SLOT_NUM, slots_to_skip = [False]*MTP_Const.MTP_SLOT_NUM, dbg_mode = False, test_inst = None):
        self._id = mtpid
        self._ts_handle = None
        self._mgmt_handle = None
        self._mgmt_prompt = None
        self._mgmt_timeout = MTP_Const.MTP_POWER_ON_TIMEOUT
        self._diagmgr_handle = None
        self._console_handle = None
        self._ts_cfg = ts_cfg
        self._usb_ts_cfg = usb_ts_cfg
        self._mgmt_cfg = mgmt_cfg
        self._prompt_list = libmfg_utils.get_linux_prompt_list()
        self._slots = num_of_slots
        self._slots_to_skip = slots_to_skip
        self._fans = 4
        self._num_pdu = 2
        self._status = MTP_Status.MTP_STA_POWEROFF
        self._fanspd = MTP_Const.MFG_EDVT_NORM_FAN_SPD    # variable to track the fan speed (%) set by the script

        self._io_cpld_ver = None
        self._jtag_cpld_ver = None
        self._asic_support = None
        self._mtp_rev = None
        self._os_name = None
        self._os_ver = None
        self._os_dat = None
        self._bios_ver = None
        self._bios_dat = None
        self._svos_dat = None
        self._svos_ver = None
        self._onie_ver = None
        self._onie_dat = None
        self._diag_ver = None
        self._asic_ver = None
        self._uut_type = test_inst.uut_type
        self._cpld_ver = None
        self._fea_cpld_ver = None
        self._fpga_ver = None
        self._fpga_dat = None

        self._debug_mode = dbg_mode
        self._cmd_buf = None
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._console_filep = None
        self._temppn = None

        self._sn = {"CPU": "", "BMC": "", "SWITCH": "", "SYSTEM": "SN_UNKNOWN"}
        self._mac = {"CPU": "", "BMC": "", "SWITCH": ""}
        self._pn = {"CPU": "", "BMC": "", "SWITCH": "", "SYSTEM": ""}
        self._maj = None
        self._prog_date = {"CPU": "", "BMC": "", "SWITCH": ""}
        self._edc = ""
        self._pcbasn = None

        self._homedir = "."
        self._tpm_skip = False

        self._svos_boot = True # set to False once OS is installed
        self._onie_boot = False
        self._use_usb_console = False

        self._hard_failure = False

        self._test_inst = test_inst

        # name is defined by its name in diag fpgautil
        # None/"" = not present
        self.sys_modules = {
            "PSU": {
                "PSU_1": "",
                "PSU_2": ""
                },
            "FAN": {
                "FAN-1": "",
                "FAN-2": "",
                "FAN-3": "",
                "FAN-4": ""
                },
            "FAN AIRFLOW": "",
            "SSD": {
                "SSD": ""
                },
            "MEMORY": {
                "MEMORY CHANNEL-0": "",
                "MEMORY CHANNEL-2": ""
                },
            "SFP": {
                "SFP-01": "",
                "SFP-02": "",
                "SFP-03": "",
                "SFP-04": "",
                "SFP-05": "",
                "SFP-06": "",
                "SFP-07": "",
                "SFP-08": "",
                "SFP-09": "",
                "SFP-10": "",
                "SFP-11": "",
                "SFP-12": "",
                "SFP-13": "",
                "SFP-14": "",
                "SFP-15": "",
                "SFP-16": "",
                "SFP-17": "",
                "SFP-18": "",
                "SFP-19": "",
                "SFP-20": "",
                "SFP-21": "",
                "SFP-22": "",
                "SFP-23": "",
                "SFP-24": "",
                "SFP-25": "",
                "SFP-26": "",
                "SFP-27": "",
                "SFP-28": "",
                "SFP-29": "",
                "SFP-30": "",
                "SFP-31": "",
                "SFP-32": "",
                "SFP-33": "",
                "SFP-34": "",
                "SFP-35": "",
                "SFP-36": "",
                "SFP-37": "",
                "SFP-38": "",
                "SFP-39": "",
                "SFP-40": "",
                "SFP-41": "",
                "SFP-42": "",
                "SFP-43": "",
                "SFP-44": "",
                "SFP-45": "",
                "SFP-46": "",
                "SFP-47": "",
                "SFP-48": ""
                },
            "QSFP": {
                "QSFP-01": "",
                "QSFP-02": "",
                "QSFP-03": "",
                "QSFP-04": "",
                "QSFP-05": "",
                "QSFP-06": ""
                }
            }

    def mtp_get_cmd_buf(self):
        return self._cmd_buf

    def mtp_get_nic_err_msg(self, slot):
        err_msg_str = self._test_inst.nic[slot].nic_get_err_msg()
        if err_msg_str:
            err_msg_list = err_msg_str.splitlines()
            for err_msg in err_msg_list:
                if err_msg:
                    self._test_inst.cli_log_slot_err(slot, err_msg)
        return

    def mtp_clear_nic_err_msg(self, slot):
        return self._test_inst.nic[slot].nic_get_err_msg()

    def mtp_dump_cmd_buf(self, *args, **kwargs):
        return self._test_inst.mtp_dump_cmd_buf(*args, **kwargs)

    def mtp_dump_nic_cmd_buf(self, *args, **kwargs):
        return self._test_inst.mtp_dump_nic_cmd_buf(*args, **kwargs)

    def mtp_dump_err_msg(self, *args, **kwargs):
        return self._test_inst.mtp_dump_err_msg(*args, **kwargs)

    def mtp_dump_nic_err_msg(self, *args, **kwargs):
        return self._test_inst.mtp_dump_nic_err_msg(*args, **kwargs)

    def exec_cmd(self, cmd, pass_sig_list=[], fail_sig_list=[], timeout=MTP_Const.OS_CMD_DELAY):
        handle = self._mgmt_handle
        prompt = self._mgmt_prompt

        libmfg_utils.expect_clear_buffer(handle)
        rc = True
        idx = -1
        handle.sendline(cmd)
        cmd_before = ""
        cmd_after = ""
        sig_list = pass_sig_list + fail_sig_list
        if sig_list:
            idx = libmfg_utils.mfg_expect(handle, sig_list + [prompt], timeout)
            cmd_before = handle.before
            cmd_after = handle.after
            if idx < 0:
                rc = False
            elif idx < len(pass_sig_list) or idx == len(sig_list):
                rc = True
            else:
                rc = False

        if idx == len(sig_list): 
            # no pass/fail sig, got prompt already
            idx = 99999999
        else:
            # no sig_list, OR found a signature in previous expect, now expect a prompt
            idx = libmfg_utils.mfg_expect(handle, [prompt], timeout)

        if sig_list:
            self._cmd_buf = cmd_before + cmd_after + handle.before
        else:
            self._cmd_buf = handle.before

        # signature match fails
        if not rc:
            return False
        elif idx < 0:
            return False
        else:
            return True

    def nic_mtp_exec_cmd(self, slot, cmd, pass_sig_list=[], fail_sig_list=[], timeout=MTP_Const.OS_CMD_DELAY):
        """
            Same implementation as exec_cmd, but save to nic cmd_buf
        """
        handle = self._test_inst.nic[slot]._nic_handle
        prompt = self._test_inst.nic[slot]._nic_prompt

        libmfg_utils.expect_clear_buffer(handle)
        rc = True
        idx = -1
        handle.sendline(cmd)
        cmd_before = ""
        cmd_after = ""
        sig_list = pass_sig_list + fail_sig_list
        if sig_list:
            idx = libmfg_utils.mfg_expect(handle, sig_list + [prompt], timeout)
            cmd_before = handle.before
            cmd_after = handle.after
            if idx < 0:
                rc = False
            elif idx < len(pass_sig_list) or idx == len(sig_list):
                rc = True
            else:
                rc = False

        if idx == len(sig_list): 
            # no pass/fail sig, got prompt already
            idx = 99999999
        else:
            # no sig_list, OR found a signature in previous expect, now expect a prompt
            idx = libmfg_utils.mfg_expect(handle, [prompt], timeout)

        if sig_list:
            self._test_inst.nic[slot]._cmd_buf = cmd_before + cmd_after + handle.before
        else:
            self._test_inst.nic[slot]._cmd_buf = handle.before

        # signature match fails
        if not rc:
            return False
        elif idx < 0:
            return False
        else:
            return True

    def copy_file_to_mtp(self, src, dst, logfile=None, nopasswd=False):
        """ 
            copy file host to UUT 
            scp src userid@UUT:/dst
        """
        if logfile is None:
            logfile = self._diag_filep
        if not self._mgmt_cfg:
            self.cli_log_err("Lost IP - cant connect to UUT", level=0)
            return False
        ip_addr = self._mgmt_cfg[0]
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        if not ip_addr:
            self.cli_log_err("IP not set - cant connect to UUT", level=0)
            return False

        cmd = "scp {:s} {:s} {:s}@{:s}:{:s}".format(libmfg_utils.get_ssh_option(), src, userid, ip_addr, dst)
        self.log_mtp_file(cmd)
        session = libmfg_utils.expect_spawn(cmd, logfile=logfile)
        if not nopasswd:
            if libmfg_utils.mfg_expect(session, ["ssword:"]) < 0:
                self.cli_log_err("File copy: could not get password prompt")
                return False
            if not libmfg_utils.expect_sendline(session, passwd, timeout=MTP_Const.MTP_NETCOPY_DELAY):
                self.cli_log_err("File copy {:s} failed".format(src))
                return False
        fail_sig_list = ["No such file", "Exiting with failure"]
        idx = libmfg_utils.mfg_expect(session, fail_sig_list, timeout=MTP_Const.MTP_NETCOPY_DELAY)
        session.close()
        # if idx < 0:
        #     self.cli_log_err("Missing file or session hung while transfering file", level=0)
        #     return False
        if idx == 0 or idx == 1:
            self.cli_log_err("Missing file {:s}".format(src))
            return False

        cmd = "sync"
        if not self.exec_cmd(cmd):
            self.cli_log_err("Command {:s} failed".format(cmd))
            return False

        cmd = "md5sum " + src
        cmd_buf = libmfg_utils.host_shell_cmd(self, cmd, timeout=10, logfile=logfile)
        if cmd_buf is None:
            self.cli_log_err("Command {:s} failed".format(cmd))
            return False
        match = re.search(r"([0-9a-fA-F]+) +.*", str(cmd_buf))
        session.close()
        if match:
            local_md5sum = match.group(1)
        else:
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            self.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(cmd_buf)))
            return False

        self._mgmt_handle.sendline() # press enter to keep log clean; separate host command output from MTP command

        if "*" not in src: #skip md5sum checksum for wildcard/multifile copies
            cmd = "md5sum " + dst + "/" + os.path.basename(src)
            self.exec_cmd(cmd, timeout=10)
            cmd_buf = self.mtp_get_cmd_buf()
            if not cmd_buf:
                self.cli_log_err("No result from command {:s}".format(cmd))
                return False
            if "No such file" in cmd_buf:
                self.cli_log_err("File transfer failed", level=0)
                return False
            match = re.search(r"([0-9a-fA-F]+) +.*", str(cmd_buf))
            if match:
                if match.group(1) == local_md5sum:
                    return True
                else:
                    self.cli_log_err("File {:s} md5sum mismatch".format(src))
                    return False
            else:
                self.cli_log_err("Execute command {:s} on {:s} failed".format(cmd, ip_addr))
                return False

        return True

    def copy_file_from_mtp(self, src, dst, logfile=None):
        """ 
            copy file UUT to host 
            scp userid@UUT:/src dst
        """
        if logfile is None:
            logfile = self._diag_filep
        if not self._mgmt_cfg:
            self.cli_log_err("Lost IP - cant connect to UUT", level=0)
            return False
        ip_addr = self._mgmt_cfg[0]
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        if not ip_addr:
            self.cli_log_err("IP not set - cant connect to UUT", level=0)
            return False

        cmd = "scp {:s} {:s}@{:s}:{:s} {:s}".format(libmfg_utils.get_ssh_option(), userid, ip_addr, src, dst)
        self.log_mtp_file(ssh_cmd)
        session = libmfg_utils.expect_spawn(cmd, logfile=logfile)
        if libmfg_utils.mfg_expect(session, ["ssword:"]) < 0:
            self.cli_log_err("File copy: could not get password prompt")
            return False
        if not libmfg_utils.expect_sendline(session, passwd, timeout=MTP_Const.MTP_NETCOPY_DELAY):
            self.cli_log_err("File copy {:s} failed".format(src))
            return False
        fail_sig_list = ["No such file", "Exiting with failure"]
        idx = libmfg_utils.mfg_expect(session, fail_sig_list, timeout=MTP_Const.MTP_NETCOPY_DELAY)
        # if idx < 0:
        #     self.cli_log_err("Session hung while transfering file", level=0)
        #     return False
        if idx == 0 or idx == 1:
            self.cli_log_err("Missing file {:s}".format(src))
            return False
        session.close()

        cmd = "sync"
        cmd_buf = libmfg_utils.host_shell_cmd(self, cmd, logfile=logfile)
        if cmd_buf is None:
            self.cli_log_err("Command {:s} failed".format(cmd))
            return False

        cmd = "md5sum " + os.path.dirname(dst) + os.path.basename(src)
        cmd_buf = libmfg_utils.host_shell_cmd(self, cmd, timeout=10, logfile=logfile)
        if cmd_buf is None:
            self.cli_log_err("Command {:s} failed".format(cmd))
            return False
        match = re.search(r"([0-9a-fA-F]+) +.*", str(cmd_buf))
        session.close()
        if match:
            local_md5sum = match.group(1)
        else:
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        self._mgmt_handle.sendline() # press enter to keep log clean; separate host command output from MTP command

        if "*" not in src: #skip md5sum checksum for wildcard/multifile copies
            cmd = "md5sum " + src
            self.exec_cmd(cmd)
            cmd_buf = self.mtp_get_cmd_buf()
            if not cmd_buf:
                self.cli_log_err("No result from command {:s}".format(cmd))
                return False
            if "No such file" in cmd_buf:
                self.cli_log_err("File transfer failed", level=0)
                return False
            match = re.search(r"([0-9a-fA-F]+) +.*", str(cmd_buf))
            if match:
                if match.group(1) == local_md5sum:
                    return True
                else:
                    self.cli_log_err("File {:s} md5sum mismatch".format(dst))
                    return False
            else:
                self.cli_log_err("Execute command {:s} on {:s} failed".format(cmd, ip_addr))
                return False

        return True

    def cli_log_inf(self, *args, **kwargs):
        return self._test_inst.cli_log_inf(*args, **kwargs)

    def cli_log_err(self, *args, **kwargs):
        return self._test_inst.cli_log_err(*args, **kwargs)

    def log_mtp_file(self, *args, **kwargs):
        """ added here for now since we dont always have access to test inst ... which should be improved """
        return self._test_inst.log_mtp_file(*args, **kwargs)

    def get_mtp_sn(self):
        return self._sn["SYSTEM"]

    def mtp_handle_init(self):
        self._mgmt_handle.setecho(False)
        self._mgmt_handle.logfile = None
        self._mgmt_handle.logfile_read = self._diag_filep
        self._mgmt_handle.logfile_send = self._diag_cmd_filep

    def nic_handle_close(self):
        self._mgmt_handle.logfile_send = None
        self._mgmt_handle.logfile_read = None
        self._mgmt_handle.close()

    def mtp_console_enter_shell(self, shell="sh"):

        successentersh = False
        for x in range(3):
            self._mgmt_handle.sendline(shell)

            time.sleep(2)
            if self.mtp_console_connect(): # calling this to change self._mgmt_prompt
                time.sleep(2)
                self.exec_cmd("echo $SHELL", timeout=60)
                successentersh = True
            if shell == "sh":
                successentersh = False
                if self.exec_cmd("stty rows 50 cols 160", pass_sig_list=["#"], timeout=60):
                    successentersh = True

            if shell == "svcli":
                successentersh = False
                if self.exec_cmd("", pass_sig_list=[">"], timeout=60):
                    successentersh = True

            if successentersh:
                break

        return successentersh

    def mtp_console_connect(self, prompt_cfg=False, prompt_id=None):
        self.mtp_console_spawn()

        delay = MTP_Const.TOR_CONSOLE_CON_DELAY
        retries = 0
        #max_retries = self._mgmt_timeout / delay
        max_retries = 10
        prompt_list = ["Connection refused", "Last login:", " login:", "assword:", "$", "#", ">"]

        try_respawn = False
        while True:
            time.sleep(1) # this is crucial so that the prompt is safely out of the console buffer (not pexpect buffer)
            libmfg_utils.expect_clear_buffer(self._mgmt_handle)
            if try_respawn:
                self.mtp_console_spawn()
            time.sleep(1)
            self._mgmt_handle.sendline()
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, prompt_list)
            if idx < 0:
                if retries < max_retries:
                    self.cli_log_inf("Console to uut timeout, wait {:d}s and retry...".format(delay))
                    libmfg_utils.count_down(delay)
                    retries += 1
                    try_respawn = True
                    continue
                else:
                    self.cli_log_err("Console to uut failed\n", level = 0)
                    return None
            elif idx == 0:
                if retries < max_retries:
                    if retries > 1:
                        self.cli_log_inf("Unable to {:s}. Connection refused. Clearing console then retrying...".format(self.mtp_get_telnet_command()))
                    retries += 1
                    libmfg_utils.count_down(delay*(retries-1))
                    if retries > 1:
                        self.mtp_clear_console()
                    try_respawn = True
                else:
                    self.cli_log_err("Console to uut failed. Connection refused.\n", level = 0)
                    return None
            elif idx == 1:
                continue
            elif idx == 2:
                self._mgmt_handle.sendline(self._mgmt_cfg[1]) #userid
                self._mgmt_handle.sendline(self._mgmt_cfg[2]) #passwd
            elif idx == 3:
                self._mgmt_handle.sendline(self._mgmt_cfg[2])
            elif idx == 4:
                self._mgmt_handle.sendline("sudo su")
            else:
                # ctrl-C anything left behind from previous session
                self._mgmt_handle.send("\003")
                self._mgmt_handle.send("\003")
                break

        # check its still alive or finally fail
        self._mgmt_handle.sendline()
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, self._prompt_list)
        if idx < 0:
            self.cli_log_inf("Console cannot get the prompt, will retry...\n")
            time.sleep(1)
            self._mgmt_handle.sendline()
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, self._prompt_list)
            if idx < 0:
                self.cli_log_err(self._mgmt_handle.before)
                self.cli_log_err("Login to uut failed", level = 0)
                return None

        self._mgmt_prompt = self._prompt_list[idx]

        self.mtp_handle_init()

        if prompt_cfg:
            # config the prompt
            if prompt_id:
                userid = prompt_id
            else:
                userid = self._mgmt_cfg[1]
            if not self.mtp_prompt_cfg(self._mgmt_handle, userid, self._mgmt_prompt):
                self.cli_log_err("Failed to Init Diag SW Environment", level=0)
                return None
            self._mgmt_prompt = "{:s}@{:s}:".format(userid, self._uut_type) + self._mgmt_prompt

        return self._mgmt_prompt
    
    def mtp_get_telnet_command(self):
        if self._use_usb_console:
            return self.mtp_get_usb_console_command()

        if not self._ts_cfg:
            self.cli_log_err("telnet port config is empty")
            return None
        
        ip = self._ts_cfg[0]
        if not libmfg_utils.ip_address_validate(ip):
            self.cli_log_err("Invalid telnet IP: {:s}".format(ip))
            return None

        if len(self._ts_cfg[1]) == 1:
            port = "200" + self._ts_cfg[1]
        elif len(self._ts_cfg[1]) == 2:
            port = "20" + self._ts_cfg[1] #"40" + self._ts_cfg[1]
        elif len(self._ts_cfg[1]) == 4:
            port = "20" + self._ts_cfg[1][-2:] #"40" + self._ts_cfg[1][-2:]
        else:
            self.cli_log_err("Unable to decipher telnet port {:s}".format(self._ts_cfg[1]))
            return None

        return "telnet "+ip+" "+port

    def mtp_get_usb_console_command(self):
        if not self._usb_ts_cfg:
            self.cli_log_err("USB console server config is empty")
            return None
        
        ip = self._usb_ts_cfg[0]
        if not libmfg_utils.ip_address_validate(ip):
            self.cli_log_err("Invalid USB console server IP: {:s}".format(ip))
            return None

        if len(self._ts_cfg[1]) == 1:
            port = "200" + self._usb_ts_cfg[1]
        elif len(self._usb_ts_cfg[1]) == 2:
            port = "20" + self._usb_ts_cfg[1]
        elif len(self._usb_ts_cfg[1]) == 4:
            port = "20" + self._usb_ts_cfg[1][-2:]
        else:
            self.cli_log_err("Unable to decipher USB console server port {:s}".format(self._usb_ts_cfg[1]))
            return None

        return "telnet "+ip+" "+port

    def mtp_console_spawn(self):
        telnet_cmd = self.mtp_get_telnet_command()
        if self._mgmt_handle is not None:
            self.mtp_console_disconnect()
        self.log_mtp_file(telnet_cmd)
        self._mgmt_handle = libmfg_utils.expect_spawn(telnet_cmd, logfile=self._diag_filep)
        self.mtp_handle_init()

    def mtp_console_disconnect(self):
        """
        Ctrl-] q
        and also close() pexpect
        """
        if self._mgmt_handle:
            if not self._mgmt_cfg:
                self._mgmt_handle.send('\x1b')
                self._mgmt_handle.send("q")
            self._mgmt_handle.close()
            self._mgmt_handle = None
        return True

    def mtp_clear_console(self):
        if self._ts_cfg:
            if self._use_usb_console:
                self.cli_log_inf("Clearing USB console line", level=0)
                ts_cfg = self._usb_ts_cfg
            else:
                self.cli_log_inf("Clearing console line", level=0)
                ts_cfg = self._ts_cfg
            ts_ip = ts_cfg[0]
            ts_port = ts_cfg[1]
            ts_user = ts_cfg[2]
            ts_pass = ts_cfg[3]
            telnet_cmd = self.mtp_get_telnet_command()
            telnet_cmd = telnet_cmd[:-4] #remove port
            session = libmfg_utils.expect_spawn(telnet_cmd, logfile=self._diag_filep)
            prompt_list = ["ogin:","assword:", "]>", ">", "#"]
            while True:
                idx = libmfg_utils.mfg_expect(session, prompt_list)
                if idx < 0:
                    self.cli_log_err("Terminal server is unavailable", level=0)
                    return False
                elif idx == 0:
                    session.sendline(ts_user)
                elif idx == 1:
                    session.setecho(False)
                    session.waitnoecho()
                    session.sendline(ts_pass)
                    # session.setecho(True)
                elif idx == 2:
                     session.sendline("set deviceport port {:s} reset".format(ts_port))
                     session.sendline()
                     session.expect("Device Port settings successfully updated.")
                     session.sendline("logout")
                     session.sendline()
                     break
                elif idx == 3:
                    session.sendline("en")
                elif idx == 4:
                    session.sendline("clear line {:s}".format(ts_port))
                    session.sendline()
                    session.sendline()
                    session.expect("OK")
                    session.sendline("clear line {:s}".format(ts_port))
                    session.sendline()
                    session.sendline()
                    session.expect("OK")
                    break
            session.close()
            return True

    def mtp_mgmt_connect(self, prompt_cfg=False, prompt_id=None):
        delay = 30
        retries = self._mgmt_timeout / delay
        retries = retries + 4
        if not self._mgmt_cfg:
            self.cli_log_err("management port config is empty")
            return None

        self.mtp_mgmt_disconnect()

        self.cli_log_inf("Connecting to UUT over management port", level=0)

        # mgmt_cfg is a list with format [ip, userid, passwd]
        ip = self._mgmt_cfg[0]
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        ssh_cmd = libmfg_utils.get_ssh_connect_cmd(userid, ip)
        self.log_mtp_file(ssh_cmd)
        self._mgmt_handle = libmfg_utils.expect_spawn(ssh_cmd, logfile=self._diag_filep)
        while True:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["assword:"], timeout=60)
            if idx < 0:
                if retries > 0:
                    self.cli_log_inf("Connect to UUT timeout, wait {:d}s and retry...".format(delay), level = 0)
                    time.sleep(delay)
                    retries -= 1
                    self._diag_filep.write("\n"+ssh_cmd+"\n")
                    self._mgmt_handle = libmfg_utils.expect_spawn(ssh_cmd, logfile=self._diag_filep)
                    continue
                else:
                    self.cli_log_err("Connect to UUT failed\n", level = 0)
                    return None
            else:
                libmfg_utils.expect_clear_buffer(self._mgmt_handle)
                self._mgmt_handle.sendline(passwd)
                break
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err(self._mgmt_handle.before)
            self.cli_log_err("Cant reach shell after ssh login", level = 0)
            return None

        libmfg_utils.expect_clear_buffer(self._mgmt_handle)
        self._mgmt_handle.sendline("sudo su")
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err(self._mgmt_handle.before)
            self.cli_log_err("Cant reach shell in root", level = 0)
            return None

        self._mgmt_prompt = self._prompt_list[idx]

        cmd = MFG_DIAG_CMDS.MTP_LOGIN_VERIFY_FMT
        sig_list = [userid]
        if not self.exec_cmd(cmd, sig_list):
            self.cli_log_err("Connect to UUT mgmt failed", level = 0)
            return None

        self.mtp_handle_init()

        if prompt_cfg:
            # config the prompt
            if prompt_id:
                userid = prompt_id
            else:
                userid = self._mgmt_cfg[1]
            if not self.mtp_prompt_cfg(self._mgmt_handle, userid, self._mgmt_prompt):
                self.cli_log_err("Failed to Init Diag SW Environment", level=0)
                return None
            self._mgmt_prompt = "{:s}@{:s}:".format(userid, self._uut_type) + self._mgmt_prompt

        return self._mgmt_prompt

    def mtp_prompt_cfg(self, handle, userid, prompt, slot=None):
        # change terminal emulator to get rid of the ANSI escape characters showing in pexpect
        handle.sendline("export TERM=dumb")
        idx = libmfg_utils.mfg_expect(handle, [prompt], timeout=60)
        if idx < 0:
            self.cli_log_err("Cannot set terminal env", level=0)
            return None

        handle.sendline("stty rows 50 cols 200")
        idx = libmfg_utils.mfg_expect(handle, [prompt], timeout=60)
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            return False

        datetime_format = "%Y-%m-%d_%H-%M-%S"
        ps1_timestamp = "[\\D{"+datetime_format+"}] "
        if self._onie_boot:
            ps1_timestamp = "[\\d \\t] " #\D{} not supported, use \d\t
        if slot != None:
            prompt_str = "{:s}@NIC-{:02d}:{:s} ".format(userid, slot+1, prompt)
        else:
            prompt_str = "{:s}@{:s}:{:s} ".format(userid, self._uut_type, prompt)
        handle.sendline("PS1='{:s}'".format(ps1_timestamp + prompt_str))

        # refresh
        handle.sendline("uname")
        idx = libmfg_utils.mfg_expect(handle, ["Linux"])
        if idx < 0:
            self.cli_log_err("Refresh mtp mgmt timeout", level = 0)
            return False
        idx = libmfg_utils.mfg_expect(handle, [prompt_str])
        if idx < 0:
            self.cli_log_err("Prompt not saved", level = 0)
            return False

        return True

    def mtp_mgmt_disconnect(self):
        if self._mgmt_handle:
            self._mgmt_handle.close()
            self._mgmt_handle = None

    def tor_get_ip(self):
        cmd = "ifconfig eth0 | grep 'inet '"
        if not self.exec_cmd(cmd, timeout=5):
            self.cli_log_err("{:s} failed".format(cmd))
            self.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(self.mtp_get_cmd_buf())))
            return False
        cmd_buf = self.mtp_get_cmd_buf()
        ip_match = re.search("inet (?:addr:)?((?:[0-9]{1,3}\.){3}[0-9]{1,3})", cmd_buf)

        if ip_match:
            self.cli_log_inf("Obtained IP {:s}".format(ip_match.group(1)), level=0)
            self._mgmt_cfg[0] = ip_match.group(1)
            return True
        else:
            return False

    def tor_mgmt_init(self):
        retries = 3
        while retries >= 0:
            if retries == 0:
                self.cli_log_err(self.mtp_get_cmd_buf())
                return False
            retries -= 1
            if not self.tor_get_ip():
                # if not self.exec_cmd("dhclient", timeout=30):
                #     self.cli_log_err("Couldn't run command dhclient")
                time.sleep(5)
                continue
            else:
                if not self.mtp_mgmt_connect(prompt_cfg=True):
                    self.cli_log_err("Unable to ssh to UUT chassis, falling back to console")
                    if not self.mtp_console_connect():
                        self.cli_log_err("Unable to telnet to UUT chassis")
                        return False
                break
        return True


    def mtp_session_create(self, slot=None):
        if slot is None:
            logfile = self._diag_filep
        else:
            logfile = self._test_inst._diag_nic_filep_list[slot]

        ip = self._mgmt_cfg[0]
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        ssh_cmd = libmfg_utils.get_ssh_connect_cmd(userid, ip)
        if slot is None:
            self.log_mtp_file(ssh_cmd)
        else:
            self._test_inst.log_nic_file(slot, ssh_cmd)
        handle = libmfg_utils.expect_spawn(ssh_cmd, logfile=logfile)
        idx = libmfg_utils.mfg_expect(handle, ["assword:"], timeout=60)
        if idx < 0:
            self.cli_log_err("Can not connect to mtp, check the console.\n", level = 0)
            return None
        else:
            handle.sendline(passwd)

        handle.logfile = None
        handle.logfile_read = logfile

        idx = libmfg_utils.mfg_expect(handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            return None

        handle.sendline("sudo su")
        idx = libmfg_utils.mfg_expect(handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err(handle.before)
            self.cli_log_err("Cant reach shell after ssh login", level = 0)
            return None

        cmd = MFG_DIAG_CMDS.MTP_LOGIN_VERIFY_FMT
        sig_list = [userid]
        handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(handle, sig_list, timeout=60)
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt failed", level = 0)
            return None

        # change terminal emulator to get rid of the ANSI escape characters showing in pexpect
        handle.sendline("export TERM=dumb")
        idx = libmfg_utils.mfg_expect(handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err(handle.before)
            return None
        
        handle.sendline("stty rows 50 cols 200")
        idx = libmfg_utils.mfg_expect(handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err(handle.before)
            self.cli_log_err("Cant resize shell after ssh login", level = 0)
            return None

        return handle

    def tor_nic_init(self):
        fail_nic_list = self._test_inst.mtp_nic_para_session_init(range(self._slots))
        for slot in fail_nic_list:
            self._test_inst.cli_log_slot_err(slot, "Failed to init Diag SW Environment")
            return False

        # self.cli_log_inf("Init NIC Type", level=0)
        # self._nic_type_list = [None] * self._slots

        # # init nic present list
        # for slot in range(self._slots):
        #     if not self._slots_to_skip[slot]:
        #         self._nic_prsnt_list[slot] = True
        #         self._nic_type_list[slot] = NIC_Type.LIPARI
        #         self._test_inst.nic[slot].nic_set_type(NIC_Type.LIPARI)
        #     else:
        #         self._nic_prsnt_list[slot] = False
        #         self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)

        #     if not self.exec_cmd_para(slot, "source /home/root/.profile"):
        #         self.cli_log_slot_err(slot, "Couldn't initialize NIC env vars")

        return True

    def tor_file_exists(self, filename):
        cmd = "ls --color=never {:s}".format(os.path.dirname(filename))
        if not self.exec_cmd(cmd):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False

        cmd_buf = self.mtp_get_cmd_buf().split()
        if os.path.basename(filename) in cmd_buf:
            return True
        else:
            return False

    def tor_copy_sys_log(self, dest_folder, local_copy=False):
        self.cli_log_inf("Copying system logs", level=0)

        logfiles = (
            "/var/log/messages",
            "/var/log/syslog",
            "/var/log/debug"
            )

        for filename in logfiles:
            if not self.tor_file_exists(filename):
                continue
            # copy them so they stop changing
            cmd = "cp {:s} /{:s}".format(filename, os.path.basename(filename))
            if not self.exec_cmd(cmd):
                self.cli_log_err("Couldn't save system logfile safely", level=0)
                continue
            cmd = "chmod +r /{:s}".format(os.path.basename(filename))
            if not self.exec_cmd(cmd):
                self.cli_log_err("Couldn't change system logfile permissions", level=0)
                continue
            filename = "/"+os.path.basename(filename)
            dest_name = dest_folder + filename
            if not dest_name.endswith(".log"):
                dest_name = dest_name + ".log"
            if local_copy:
                if not self.exec_cmd("cp {:s} {:s}".format(filename, dest_name)):
                    self.cli_log_err("Unable to copy UUT system log file {:} locally".format(filename), level=0)
                    continue
            else:
                if not self.copy_file_from_mtp(filename, dest_name):
                    self.cli_log_err("Unable to copy UUT system log file {:}".format(filename), level=0)
                    continue

        libmfg_utils.host_shell_cmd(self, "ls {:s}".format(dest_folder))
        return True

    def tor_prepare_eeupdate(self, ssd_format=False, usb_method=True):
        if not usb_method: # copying from USB vs copying from network
            usb_tarball = ""
            ip = Factory_network_config[self.get_mtp_factory_location()]["TFTP server"]
            src_folder = Factory_network_config[self.get_mtp_factory_location()]["TFTP directory"]
            self.cli_log_inf("Downloading USB tarball")
            if not self.exec_cmd("tftp -g -r {:s}/{:s} {:s} -b 65000".format(src_folder, usb_tarball, ip), sig_list=["100%"]):
                return False
            self.exec_cmd("tar xf /cli/fs/home/{:s} -C /".format(usb_tarball))

        # if ssd_format:
        #     if not self.exec_cmd("/usr/bin/storage_fdisk_format.sh", sig_list=["Removed /run"]):
        #         self.cli_log_err("Unable to storage fdisk format", level=0)
        #         return False
        self.exec_cmd("mkdir -p {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH))
        
        if usb_method:
            self.cli_log_inf("Mounting USB folder", level=0)
            self.exec_cmd("mkdir -p /mnt/usb")
            self.exec_cmd("mount /dev/sdb2 /mnt/usb")
            self.exec_cmd("cp /mnt/usb/bin/* {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH))
            time.sleep(1)
            self.exec_cmd("sync")
            self.exec_cmd("umount /dev/sdb2")
        else:
            self.exec_cmd("cp /Taormina-USB-small/bin/* {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH))
            time.sleep(1)
            if "No such file" in self.mtp_get_cmd_buf():
                return False

        self.exec_cmd("sync")
        return True

    def tor_board_id(self):
        if not self.tor_fru_init():
            self.cli_log_err("FRU init failed", level=0)
            return False

        if not self.tor_cpld_init():
            self.cli_log_err("CPLD init failed", level=0)
            return False

        if not self.tor_os_init():
            self.cli_log_err("OS init failed", level=0)
            return False

        if not self.tor_bios_init():
            self.cli_log_err("BIOS init failed", level=0)
            return False

        self.tor_info_disp()

        return True

    def mtp_power_on_off_nic(self, direction, slot_list=[], count_down=True):
        if direction == "off":
            if not nic_pcie.close_memtun(self._test_inst):
                pass

        if slot_list != []:
            self.cli_log_err("Multiple Elba power on not supported at this time", level=0)
            return False

        if direction == "on":
            timeout = MTP_Const.TOR_NIC_POWER_ON_DELAY
        elif direction == "off":
            timeout = MTP_Const.TOR_NIC_POWER_OFF_DELAY

        cmd = "/home/admin/eeupdate/fpgautil power {:s} all -nopciscan".format(direction)
        if not self.exec_cmd(cmd, timeout=timeout):
            self.cli_log_err("Failed to power {:s} NIC".format(direction))
            return False

        for slot in range(self._slots):
            self._test_inst.log_nic_file(slot, "{:s}".format(cmd))

        if count_down:
            self.cli_log_inf("Power {:s} all NIC, wait {:02d} seconds for NIC power up".format(direction, timeout), level=0)
            libmfg_utils.count_down(timeout)
        else:
            self.cli_log_inf("Power {:s} all NIC, NIC power up".format(direction), level=0)

        return True

    def mtp_power_cycle_nic(self, slot_list=[], count_down=True):
        rc = self.mtp_power_on_off_nic("off", slot_list)
        if not rc:
            return rc

        rc = self.mtp_power_on_off_nic("on", slot_list, count_down)
        if not rc:
            return rc

        return True

    def mtp_sync_clock(self):
        timestamp_str = str(libmfg_utils.timestamp_snapshot())
        cmd = "hwclock --set --date '{:s}'".format(timestamp_str)
        if not self.exec_cmd(cmd):
            self.cli_log_err("Unable to set UUT date")
            return False

        cmd = "hwclock -s"
        if not self.exec_cmd(cmd):
            self.cli_log_err("Unable to save UUT date")
            return False

        self.cli_log_inf("UUT Chassis timestamp sync'd", level=0)
        return True

    def mtp_sys_info_disp(self, fru_valid):
        self.cli_log_inf("UUT Info Dump:")
        if fru_valid:
            self.cli_log_inf("==> SYSTEM FRU: {:s}, {:s}, {:s}".format(self._sn["SYSTEM"],libmfg_utils.mac_address_add_separator(self._mac["SWITCH"],":"), self._pn["SYSTEM"]))
            self.cli_log_inf("==> SWITCH FRU: {:s}, {:s}, {:s}".format(self._sn["SWITCH"],libmfg_utils.mac_address_add_separator(self._mac["SWITCH"],":"), self._pn["SWITCH"]))
            self.cli_log_inf("==>    CPU FRU: {:s}, {:s}, {:s}".format(self._sn["CPU"], libmfg_utils.mac_address_add_separator(self._mac["CPU"],":"), self._pn["CPU"]))
            # self.cli_log_inf("==> BMC    FRU: {:s}, {:s}, {:s}".format(self._sn["BMC"],   self._mac["BMC"],    self._pn["BMC"]))
            self.cli_log_inf("==> FRU Program Date: {:s}".format(self._prog_date["CPU"]))

        if self._bios_ver:
            self.cli_log_inf("==> BIOS version: {:s} ({:s})".format(self._bios_ver, self._bios_dat))

        if self._os_ver:
            self.cli_log_inf("==> SONiC version: {:s} ({:s})".format(self._os_ver, self._os_dat))

        if self._fpga_ver and self._fpga_dat:
            self.cli_log_inf("==> FGPA0: {:s} ({:s})".format(self._fpga_ver["fpga 0"], self._fpga_dat["fpga 0"]))
            self.cli_log_inf("==> FGPA1: {:s} ({:s})".format(self._fpga_ver["fpga 1"], self._fpga_dat["fpga 1"]))
        else:
            self.cli_log_err("Retrieve FPGA info failed")

        if self._cpld_ver:
            devices = [
            "cpu",
            "elba 0",
            "elba 1",
            "elba 2",
            "elba 3",
            "elba 4",
            "elba 5",
            "elba 6",
            "elba 7"
            ]
            for device in devices:
                if device not in self._cpld_ver.keys():
                    self.cli_log_err("Retrieve {:s} CPLD info failed".format(device.upper()))
                    continue
                cpld_uc = self._cpld_ver[device]
                self.cli_log_inf("==> {:s} CPLD: {:s}".format(device.upper(), cpld_uc))
        else:
            self.cli_log_err("Retrieve CPLD info failed")

        self.cli_log_inf("End UUT Info Dump")

        return True


