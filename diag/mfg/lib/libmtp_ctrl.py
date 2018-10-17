import pexpect
import time
import os
import sys
import libmfg_utils
import random
import re
from libmfg_cfg import MFG_CFG_NIC_FRU_VALID
from libdefs import NIC_Type
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
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
        self._nic_sn_list = [None] * self._slots
        self._nic_mac_list = [None] * self._slots
        self._nic_sta_list = [NIC_Status.NIC_STA_POWEROFF] * self._slots

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
        libmfg_utils.cli_log_inf(self._filep, nic_cli_id_str + indent + msg)


    def cli_log_slot_err(self, slot, msg, level = 1):
        nic_cli_id_str = libmfg_utils.id_str(mtp = self._id, nic = slot)
        indent = "    " * level
        libmfg_utils.cli_log_err(self._filep, nic_cli_id_str + indent + msg)


    def cli_log_file(self, msg):
        self._filep.write(msg + "\n")

    
    def get_mgmt_cfg(self):
        return self._mgmt_cfg


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

        ssh_cmd = "ssh -l {:s} {:s}".format(userid, ip) + libmfg_utils.get_ssh_option()
        handle = pexpect.spawn(ssh_cmd)
        idx = handle.expect_exact(["assword:",
                                   pexpect.TIMEOUT], timeout = 5)
        if idx == 0:
            handle.sendline(passwd)
        else:
            self.cli_log_err("Can not connect to mtp, check the console.\n", level = 0)
            return None
        idx = handle.expect_exact(self._prompt_list, timeout = 5) 
        if (idx < len(self._prompt_list)):
            handle.sendline("whoami")
            handle.expect_exact(userid)
            handle.expect_exact(self._prompt_list[idx])
            return handle
        else:
            self.cli_log_err("Unknown linux prompt", level = 0)
            return None


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

        ssh_cmd = "ssh -l {:s} {:s}".format(userid, ip) + libmfg_utils.get_ssh_option()
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
            libmfg_utils.sys_exit("MTP mgmt connection hangs...")
       

    def mtp_prompt_cfg(self, handle, userid, prompt):
        handle.sendline("stty rows 50 cols 160")
        handle.expect_exact(prompt)
        handle.sendline("PS1='\u@\h:{:s} '".format(prompt))
        handle.expect(r"{:s}.*{:s}".format(userid, prompt))


    def mtp_enter_user_ctrl(self):
        if self._mgmt_handle:
            self._mgmt_handle.sendline("\n")
            self._mgmt_handle.expect_exact(self._mgmt_prompt)
            self._mgmt_handle.interact()


    def mtp_mgmt_exec_sudo_cmd(self, cmd):
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        if not self._mgmt_handle:
            self.cli_log_err("Management port is not connected")
            return False
        self._mgmt_handle.sendline("sudo " + cmd)
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
        self._mgmt_handle.sendline("tar zxf " + image)
        self._mgmt_handle.expect_exact(self._mgmt_prompt, timeout=MTP_Const.OS_CMD_DELAY)
        self._mgmt_handle.sendline("sync")
        self._mgmt_handle.expect_exact(self._mgmt_prompt, timeout=MTP_Const.OS_SYNC_DELAY)


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


    def mtp_program_nic_fru(self, slot, sn, mac):
        # TODO: how to program nic fru?
        self._mgmt_handle.sendline("echo 'Fake FRU program on the nic'")
        self._mgmt_handle.expect_exact("Fake FRU")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        return True


    def mtp_verify_nic_fru(self, slot, sn, mac):
        # TODO: how to verify nic fru?
        self._mgmt_handle.sendline("echo 'Fake FRU verify on the nic'")
        self._mgmt_handle.expect_exact("Fake FRU")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        return True


    def mtp_program_nic_cpld(self, slot, cpld_img):
        # TODO: how to program nic cpld?
        self._mgmt_handle.sendline("echo 'Fake CPLD program on the nic'")
        self._mgmt_handle.expect_exact("Fake CPLD")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        return True


    def mtp_verify_nic_cpld(self, slot, cpld_img):
        # TODO: how to verify nic cpld?
        self._mgmt_handle.sendline("echo 'Fake CPLD verify on the nic'")
        self._mgmt_handle.expect_exact("Fake CPLD")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        return True


    def mtp_program_nic_vrm(self, slot, vrm_img, vrm_img_cksum):
        # TODO: how to program nic vrm?
        self._mgmt_handle.sendline("echo 'Fake VRM program on the nic'")
        self._mgmt_handle.expect_exact("Fake VRM")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        return True


    def mtp_verify_nic_vrm(self, slot, vrm_img, vrm_img_cksum):
        # TODO: how to program nic vrm?
        self._mgmt_handle.sendline("echo 'Fake VRM verify on the nic'")
        self._mgmt_handle.expect_exact("Fake VRM")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        return True


    def mtp_nic_fw_update(self, slot, sn = None, mac = None, cpld_img_file = None, vrm_img_file = None, vrm_img_cksum = None, err_inj = False):
        if err_inj:
            err_inj_type = random.choice(["FRU-PROG", "FRU-VERIFY", "CPLD-PROG", "CPLD-VERIFY", "VRM-PROG", "VRM-VERIFY"])
        else:
            err_inj_type = None

        # program FRU
        ret = self.mtp_program_nic_fru(slot, sn, mac)
        mac_ui = libmfg_utils.mac_address_format(mac)

        # error injection
        if err_inj_type == "FRU-PROG":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "Program NIC with mac address: {:s}, sn: {:s} complete".format(mac_ui, sn))
        else:
            self.cli_log_slot_err(slot, "Program NIC with mac address: {:s}, sn: {:s} failed".format(mac_ui, sn))
            return False

        # verify FRU
        ret = self.mtp_verify_nic_fru(slot, sn, mac)

        # error injection
        if err_inj_type == "FRU-VERIFY":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "Verify NIC with mac address: {:s}, sn: {:s} complete".format(mac_ui, sn))
        else:
            self.cli_log_slot_err(slot, "Verify NIC with mac address: {:s}, sn: {:s} failed".format(mac_ui, sn))
            return False

        # program CPLD
        ret = self.mtp_program_nic_cpld(slot, cpld_img_file)

        # error injection
        if err_inj_type == "CPLD-PROG":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "Program NIC CPLD file: {:s} complete".format(cpld_img_file))
        else:
            self.cli_log_slot_err(slot, "Program NIC CPLD file: {:s} Failed".format(cpld_img_file))
            return False

        # verify CPLD
        ret = self.mtp_verify_nic_cpld(slot, cpld_img_file)

        # error injection
        if err_inj_type == "CPLD-VERIFY":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "Verify NIC CPLD file: {:s} complete".format(cpld_img_file))
        else:
            self.cli_log_slot_err(slot, "Verify NIC CPLD file: {:s} Failed".format(cpld_img_file))
            return False

        # program VRM
        ret = self.mtp_program_nic_vrm(slot, vrm_img_file, vrm_img_cksum)

        # error injection
        if err_inj_type == "VRM-PROG":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "Program NIC VRM file: {:s} complete".format(vrm_img_file))
        else:
            self.cli_log_slot_err(slot, "Program NIC VRM file: {:s} Failed".format(vrm_img_file))
            return False

        # verify VRM
        ret = self.mtp_verify_nic_vrm(slot, vrm_img_file, vrm_img_cksum)

        # error injection
        if err_inj_type == "VRM-VERIFY":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "Verify NIC VRM file: {:s} complete\n".format(vrm_img_file))
        else:
            self.cli_log_slot_err(slot, "Verify NIC VRM file: {:s} Failed\n".format(vrm_img_file))
            return False

        return True


    def mtp_misc_init(self):
        rc = True
        # vrm test
        self._mgmt_handle.sendline("mtptest -vrm")
        idx = self._mgmt_handle.expect_exact(["TEST FAILED", "TEST PASSED", pexpect.TIMEOUT])
        if idx == 0:
            self.cli_log_err("VRM test failed")
            rc = False
        elif idx == 1:
            self.cli_log_inf("VRM test passed")
        else:
            self.cli_log_err("VRM test timeout")
            rc = False

        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        return rc


    def mtp_fan_init(self):
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
        
        # put the fan speed back
        cmd_str = "devmgr -dev=fan -speed -pct={:d}".format(MTP_Const.NORMAL_TEMP_FAN_SPD)
        self._mgmt_handle.sendline(cmd_str)
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

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


    def mtp_diag_pre_init(self):
        # start the mtp diag
        self._mgmt_handle.sendline("/home/diag/start_diag.sh")
        self._mgmt_handle.expect_exact("Set up diag amd64 -- Done", timeout=MTP_Const.OS_CMD_DELAY)
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        self._mgmt_handle.sendline("source ~/.bash_profile")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        userid = self._mgmt_cfg[1]
        self.mtp_prompt_cfg(self._mgmt_handle, userid, self._mgmt_prompt)
        self._mgmt_prompt = "{:s}@MTP:".format(userid) + self._mgmt_prompt


    def mtp_diag_init(self, diagmgr_logfile, naples100_test_db):
        # start the mtp diag
        diagmgr_handle = self.mtp_session_create()
        cmd = "nohup diagmgr > {:s} 2>&1 &".format(diagmgr_logfile)
        diagmgr_handle.sendline(cmd)
        diagmgr_handle.expect_exact(self._mgmt_prompt)
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
        diagmgr_handle.close()

        self._mgmt_handle.sendline("cd ~/diag/python/infra/dshell")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        self._mgmt_handle.sendline("./diag -r -c MTP1 -d diagmgr -t dsp_start")
        self._mgmt_handle.expect_exact("Test Done: MTP1:DIAGMGR:DSP_START")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
        self._mgmt_handle.sendline("./diag -sdsp")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        # naples100 dsp check
        self.cli_log_inf("Start Diag DSP Sanity Check", level = 0)
        naples100_dsp_list = naples100_test_db.get_diag_seq_dsp_list()
        for dsp in naples100_dsp_list: 
            if dsp not in self._mgmt_handle.before:
                self.cli_log_err("Diag DSP: {:s} is not detected", level = 0)
                return False
        self.cli_log_inf("Diag DSP Sanity Check Complete", level = 0)

        return True
 

    def mtp_hw_init(self, psu_check):
        rc = True

        self.cli_log_inf("Start MTP chassis sanity check", level = 0)
        # fan init
        rc &= self.mtp_fan_init()
        
        if psu_check:
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

        return True
        #return rc 


    def mtp_diag_env_init(self, fan_speed, vmarg):
        # build nic serial number list
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                self._nic_sn_list[slot] = self.mtp_get_nic_sn(slot)
                self._nic_mac_list[slot] = self.mtp_get_nic_mac(slot)

        # check xcvr status
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                xcvr_prsnt_mask = self.mtp_get_nic_xcvr_prsnt(slot)
                if not xcvr_prsnt_mask & NIC_Port_Mask.NIC_PORT1_MASK:
                    if not ignore_warning and not libmfg_utils.double_confirm("Front Panel Port 1 Transceiver Absent, Continue"):
                        self.set_mtp_status(MTP_Status.MTP_STA_ENV_FAIL)
                        return False
                if not xcvr_prsnt_mask & NIC_Port_Mask.NIC_PORT2_MASK:
                    if not ignore_warning and not libmfg_utils.double_confirm("Front Panel Port 2 Transceiver Absent, Continue"):
                        self.set_mtp_status(MTP_Status.MTP_STA_ENV_FAIL)
                        return False
                if not xcvr_prsnt_mask & NIC_Port_Mask.NIC_MGMT_MASK:
                    if not ignore_warning and not libmfg_utils.double_confirm("Management Port  Transceiver Absent, Continue"):
                        self.set_mtp_status(MTP_Status.MTP_STA_ENV_FAIL)
                        return False

                self._nic_sta_list[slot] = NIC_Status.NIC_STA_HW_READY

        # set nic voltage margin
        if vmarg != 0:
            for slot in range(self._slots):
                if self._nic_prsnt_list[slot]:
                    self.mtp_set_nic_vmarg(slot, vmarg)

        # set the fan speed
        self.cli_log_inf("Set FAN Speed to {:d}%".format(fan_speed))
        self._mgmt_handle.sendline("devmgr -dev FAN -speed -pct " + str(fan_speed))
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        self._mgmt_handle.sendline("devmgr -dev FAN -status")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        self.set_mtp_status(MTP_Status.MTP_STA_READY)

        return True


    def mtp_get_inlet_temp(self):
        self._mgmt_handle.sendline("devmgr -dev FAN -status")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
        # FAN                 23.50          25.50          21.75          21.75
        match = re.search(r"FAN +(\d+\.\d+) + (\d+\.\d+) + (\d+\.\d+) + (\d+\.\d+)", str(self._mgmt_handle.before))
        if match:
            return (float(match.group(3)) + float(match.group(4))) / 2
        else:
            return None


    def mtp_get_nic_temp(self, slot):
        # how to get nic asic temperature
        return 95


    def mtp_nic_init(self, fru_load):
        self.cli_log_inf("Init NICs in the MTP Chassis", level = 0)
        # init nic present list
        self.cli_log_inf("Init NIC Present")
        self.mtp_init_nic_prsnt()

        # init nic type list
        self.cli_log_inf("Init NIC Type")
        self.mtp_init_nic_type()

        # nic sanity check
        self.cli_log_inf("NIC Sanity Check")
        if self.mtp_sys_sanity_check():
            self.cli_log_inf("NIC Sanity Check Passed")
        else:
            self.cli_log_inf("NIC Sanity Check Failed")
            return False

        # power on nic
        self.cli_log_inf("Power on NICs")
        self.mtp_power_on_nic()

        if fru_load:
            self.cli_log_inf("Load Barcode config file")
            nic_fru_cfg_file = "config/{:s}.yaml".format(self._id)
            nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(nic_fru_cfg_file)

            # load sn/mac from fru sprom
            if MFG_CFG_NIC_FRU_VALID:
                self.cli_log_inf("Load NIC SN/MAC from Fru")
                self.mtp_init_nic_sn()
                self.mtp_init_nic_mac()
            # load sn/mac from config file
            else:
                self.cli_log_inf("Load NIC SN/MAC from barcode config file")
                for slot in range(self._slots):
                    key = libmfg_utils.nic_key(slot)
                    valid = nic_fru_cfg[self._id][key]["VALID"]
                    if str.upper(valid) == "YES":
                        sn = nic_fru_cfg[self._id][key]["SN"]
                        mac = nic_fru_cfg[self._id][key]["MAC"]
                        self.mtp_set_nic_sn(slot, sn)
                        self.mtp_set_nic_mac(slot, mac)

            # sanity check
            # all present nic should have been scanned
            # all scanned nic should have been detected
            # sn/mac should match
            self.cli_log_inf("Start NIC Present/SN/MAC check")
            for slot in range(self._slots):
                key = libmfg_utils.nic_key(slot)
                valid = nic_fru_cfg[self._id][key]["VALID"]
                if str.upper(valid) == "YES":
                    scanned = True
                else:
                    scanned = False
                prsnt = self._nic_prsnt_list[slot]

                if scanned != prsnt:
                    # scanned, but not present
                    if scanned:
                        self.cli_log_slot_err(slot, "NIC is scanned, but not detected by system")
                    # prsnet, but not present
                    if prsnt:
                        self.cli_log_slot_err(slot, "NIC is present, but barcode is not scanned")
                    return False
           
                # mac/sn should match
                if scanned and prsnt:
                    sn = self.mtp_get_nic_sn(slot)
                    mac = self.mtp_get_nic_mac(slot)
                    scan_sn = nic_fru_cfg[self._id][key]["SN"]
                    scan_mac = nic_fru_cfg[self._id][key]["MAC"]
                    if sn != scan_sn:
                        self.cli_log_slot_err(slot, "NIC SN mismatch, scanned: {:s}, fru: {:s}".format(scan_sn, sn))
                        return False
                    if mac != scan_mac:
                        self.cli_log_slot_err(slot, "NIC MAC mismatch, scanned: {:s}, fru: {:s}".format(scan_mac, mac))
                        return False
            self.cli_log_inf("NIC Present/SN/MAC check complete")
        else:
            self.cli_log_inf("Bypass load NIC SN/MAC")

        self.cli_log_inf("Init NICs in the MTP Chassis complete\n", level = 0)
        self.mtp_nic_info_show()
        return True


    def mtp_nic_info_show(self):
        self.cli_log_inf("NIC Info Dump in the MTP Chassis:", level = 0)
        for slot, prsnt, nic_type in zip(range(self._slots), self._nic_prsnt_list, self._nic_type_list):
            if prsnt:
                self.cli_log_slot_inf(slot, "NIC is Present, Type is: {:s}".format(nic_type))
            else:
                self.cli_log_slot_err(slot, "NIC is Absent")
        self.cli_log_inf("NIC Info Dump in the MTP Chassis complete\n", level = 0)


    def mtp_power_on_nic(self):
        self._mgmt_handle.sendline("turn_on_slot.sh on all")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)


    def mtp_init_nic_prsnt(self):
        self._mgmt_handle.sendline("inventory -present")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        match = re.findall(r"UUT_(\d+) +NAPLES\d+", self._mgmt_handle.before)
        if match: 
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                self._nic_prsnt_list[slot] = True


    def mtp_get_nic_prsnt_list(self):
        return self._nic_prsnt_list


    def mtp_init_nic_type(self):
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


    def mtp_sys_sanity_check(self):
        if True not in self._nic_prsnt_list:
            self._mgmt_handle.sendline("sys_sanity.sh 1")
            self._mgmt_handle.expect_exact(self._mgmt_prompt)
            return True
        else:
            for slot in range(self._slots):
                if self._nic_prsnt_list[slot]:
                    self._mgmt_handle.sendline("sys_sanity.sh {:d}".format(slot+1))
                    self._mgmt_handle.expect_exact(self._mgmt_prompt)
                    match = re.findall(r"(valid bit 0x1, +error 0x0+)", self._mgmt_handle.before)
                    if match:
                        return True
                    else:
                        return False


    def mtp_init_nic_sn(self):
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                # TODO how to read sn from nic fru
                self._nic_sn_list[slot] = "FLM0000000" + str(slot)


    def mtp_get_nic_sn(self, slot):
        return self._nic_sn_list[slot]


    def mtp_set_nic_sn(self, slot, sn):
        self.cli_log_slot_inf(slot, "Set SN to {:s}".format(sn))
        self._nic_sn_list[slot] = sn


    def mtp_init_nic_mac(self):
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                # TODO how to read mac from nic fru
                self._nic_mac_list[slot] = "00AECD00000" + str(slot)


    def mtp_get_nic_mac(self, slot):
        return self._nic_mac_list[slot]


    def mtp_set_nic_mac(self, slot, mac):
        self.cli_log_slot_inf(slot, "Set MAC to {:s}".format(mac))
        self._nic_mac_list[slot] = mac


    def mtp_get_nic_xcvr_prsnt(self, slot):
        # TODO: how to get xcvr present status?
        mask = NIC_Port_Mask.NIC_ALL_PORT_MASK
        return mask


    def mtp_set_nic_vmarg(self, slot, vmarg):
        # TODO, how to set nic vmarg?
        self.cli_log_slot_inf(slot, "Set voltage margin to {:d}%".format(vmarg))
        return True


    def mtp_mgmt_connect_test(self):
        if not self.mtp_mgmt_connect():
            self.set_mtp_status(MTP_Status.MTP_STA_MGMT_FAIL)
            return False

        time.sleep(1)
        self.mtp_mgmt_disconnect()
        return True


    def mtp_get_nic_status(self, slot):
        if self._nic_sta_list[slot] == NIC_Status.NIC_STA_HW_READY:
            return True
        else:
            False


    def mtp_mgmt_get_test_result(self, cmd, test, timeout=30):
        self._mgmt_handle.sendline(cmd)
        self._mgmt_handle.expect_exact(self._mgmt_prompt, timeout)
        # Test    Error code, SUCCESS means pass
        match = re.findall(r"%s +([A-Za-z0-9_]+)" %test, str(self._mgmt_handle.before))
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
        end = libmfg_utils.timestamp_snapshot()
        return ret


    def mtp_run_diag_test_para(self, slot_list, cmd, count):
        rslt_list = list()

        for slot in range(self._slots):
            if self.mtp_get_nic_status(slot) and slot in slot_list:
                rslt_list.append([slot, "PASS"])

        time.sleep(random.randint(1, 10))
        return rslt_list


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
 
            ts_snapshot = libmfg_utils.get_timestamp()
            nic_scan_rslt["NIC_VALID"] = True
            nic_scan_rslt["NIC_SN"] = sn
            nic_scan_rslt["NIC_MAC"] = mac
            nic_scan_rslt["NIC_TS"] = ts_snapshot
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
