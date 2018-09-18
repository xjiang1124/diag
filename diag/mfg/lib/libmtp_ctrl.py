import pexpect
import time
import os
import sys
import libmfg_utils
import random
import re
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import NIC_Status
from libdefs import MTP_Status
from libdefs import NIC_Port_Mask

class mtp_ctrl():
    def __init__(self, mtpid, filep, diag_logfile_p, ts_cfg = None, mgmt_cfg = None, apc_cfg = None, dbg_mode = False):
        self._id = mtpid
        self._ts_handle = None
        self._mgmt_handle = None
        self._mgmt_prompt = None
        self._mgmt_timeout = MTP_Const.MTP_POWER_ON_TIMEOUT
        self._ts_cfg = ts_cfg
        self._mgmt_cfg = mgmt_cfg
        self._apc_cfg = apc_cfg
        self._prompt_list = ["#", "$", ">"]
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
        self._diag_filep = diag_logfile_p


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


    def set_MTP_Status(self, status):
        if status < MTP_Status.MTP_STA_MAX:
            self._status = status


    def get_mtp_slot_num(self):
        return self._slots


    def _mtp_single_apc_pwr_off(self, apc, userid, passwd, port_list):
        handle = pexpect.spawn("telnet " + apc)
        if self._debug_mode:
            handle.logfile = sys.stdout
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
            handle.logfile = sys.stdout
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
            handle.logfile = sys.stdout
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

        os.system("ssh-keygen -R " + ip + " > /dev/null")

        self._mgmt_handle = pexpect.spawn("ssh -l " + userid + " " + ip)
        while True:
            idx = self._mgmt_handle.expect_exact(["continue connecting (yes/no)?",
                                                  "assword:",
                                                  pexpect.TIMEOUT], timeout = 5)
            if idx == 0:
               self._mgmt_handle.sendline("yes")
               continue
            elif idx == 1:
                self._mgmt_handle.sendline(passwd)
                break
            else:
                if retries > 0:
                    self.cli_log_inf("Connect to mtp timeout, wait 30s and retry...", level = 0)
                    time.sleep(30)
                    retries -= 1
                    self._mgmt_handle = pexpect.spawn("ssh -l " + userid + " " + ip)
                    continue
                else:
                    self.cli_log_err("Can not connect to mtp, check the console.\n", level = 0)
                    return None

        idx = self._mgmt_handle.expect_exact(self._prompt_list, timeout = 5) 
        if (idx < len(self._prompt_list)):
            self._mgmt_handle.sendline("whoami")
            self._mgmt_handle.expect_exact(userid)
            self._mgmt_handle.expect_exact(self._prompt_list[idx])
            self._mgmt_prompt = self._prompt_list[idx]
            # set logfile
            if self._debug_mode:
                self._mgmt_handle.logfile = sys.stdout
            else:
                self._mgmt_handle.logfile = self._diag_filep
            return self._mgmt_prompt
        else:
            self.cli_log_err("Unknown linux prompt", level = 0)
            return None
        

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
            self._mgmt_handle.logfile = None
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


    def mtp_update_sw_image(self, image):
        self._mgmt_handle.sendline("tar zxf " + image)
        self._mgmt_handle.expect_exact(self._mgmt_prompt)


    def mtp_mgmt_poweroff(self):
        if not self.mtp_mgmt_exec_sudo_cmd("poweroff"):
            self.cli_log_err("Failed to execute poweroff command")
            return False

        return True


    def mtp_mgmt_exec_cmd(self, cmd):

        if not self._mgmt_handle:
            self.cli_log_err("management port is not connected")
            return False

        self._mgmt_handle.sendline(cmd)
        self._mgmt_handle.expect_exact(self._mgmt_prompt)
        self.cli_log_file(self._mgmt_handle.before)

        return True


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
            self.cli_log_slot_inf(slot, "-- Program NIC with mac address: {:s}, sn: {:s} complete".format(mac_ui, sn))
        else:
            self.cli_log_slot_err(slot, "-- Program NIC with mac address: {:s}, sn: {:s} failed".format(mac_ui, sn))
            return False

        # verify FRU
        ret = self.mtp_verify_nic_fru(slot, sn, mac)

        # error injection
        if err_inj_type == "FRU-VERIFY":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "-- Verify NIC with mac address: {:s}, sn: {:s} complete".format(mac_ui, sn))
        else:
            self.cli_log_slot_err(slot, "-- Verify NIC with mac address: {:s}, sn: {:s} failed".format(mac_ui, sn))
            return False

        # program CPLD
        ret = self.mtp_program_nic_cpld(slot, cpld_img_file)

        # error injection
        if err_inj_type == "CPLD-PROG":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "-- Program NIC CPLD file: {:s} complete".format(cpld_img_file))
        else:
            self.cli_log_slot_err(slot, "-- Program NIC CPLD file: {:s} Failed".format(cpld_img_file))
            return False

        # verify CPLD
        ret = self.mtp_verify_nic_cpld(slot, cpld_img_file)

        # error injection
        if err_inj_type == "CPLD-VERIFY":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "-- Verify NIC CPLD file: {:s} complete".format(cpld_img_file))
        else:
            self.cli_log_slot_err(slot, "-- Verify NIC CPLD file: {:s} Failed".format(cpld_img_file))
            return False

        # program VRM
        ret = self.mtp_program_nic_vrm(slot, vrm_img_file, vrm_img_cksum)

        # error injection
        if err_inj_type == "VRM-PROG":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "-- Program NIC VRM file: {:s} complete".format(vrm_img_file))
        else:
            self.cli_log_slot_err(slot, "-- Program NIC VRM file: {:s} Failed".format(vrm_img_file))
            return False

        # verify VRM
        ret = self.mtp_verify_nic_vrm(slot, vrm_img_file, vrm_img_cksum)

        # error injection
        if err_inj_type == "VRM-VERIFY":
            ret = False
        if ret:
            self.cli_log_slot_inf(slot, "-- Verify NIC VRM file: {:s} complete\n".format(vrm_img_file))
        else:
            self.cli_log_slot_err(slot, "-- Verify NIC VRM file: {:s} Failed\n".format(vrm_img_file))
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


    def mtp_hw_init(self):
        rc = True
        self.cli_log_inf("Start MTP chassis sanity check", level = 0)
        # start the mtp diag
        self._mgmt_handle.sendline("/home/diag/start_diag.sh")
        self._mgmt_handle.expect_exact("Set up diag amd64 -- Done")
        self._mgmt_handle.expect_exact(self._mgmt_prompt)

        # fan init
        rc &= self.mtp_fan_init()
        
        # psu init
        rc &= self.mtp_psu_init()

        # other platform init
        rc &= self.mtp_misc_init()

        if rc:
            self.cli_log_inf("MTP chassis sanity check passed\n", level = 0)
        else:
            self.cli_log_inf("MTP chassis sanity check failed\n", level = 0)

        return rc 


    def mtp_diag_env_init(self, fan_speed, vmarg):
        # build nic serial number list
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                self._nic_sn_list[slot] = self.mtp_get_nic_serial_number(slot)
                self._nic_mac_list[slot] = self.mtp_get_nic_mac_address(slot)

        # check xcvr status
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                xcvr_prsnt_mask = self.mtp_get_nic_xcvr_prsnt(slot)
                if not xcvr_prsnt_mask & NIC_Port_Mask.NIC_PORT1_MASK:
                    if not ignore_warning and not libmfg_utils.double_confirm("Front Panel Port 1 Transceiver Absent, Continue"):
                        self.set_MTP_Status(MTP_Status.MTP_STA_ENV_FAIL)
                        return False
                if not xcvr_prsnt_mask & NIC_Port_Mask.NIC_PORT2_MASK:
                    if not ignore_warning and not libmfg_utils.double_confirm("Front Panel Port 2 Transceiver Absent, Continue"):
                        self.set_MTP_Status(MTP_Status.MTP_STA_ENV_FAIL)
                        return False
                if not xcvr_prsnt_mask & NIC_Port_Mask.NIC_MGMT_MASK:
                    if not ignore_warning and not libmfg_utils.double_confirm("Management Port  Transceiver Absent, Continue"):
                        self.set_MTP_Status(MTP_Status.MTP_STA_ENV_FAIL)
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

        self.set_MTP_Status(MTP_Status.MTP_STA_READY)

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


    def mtp_power_on_nic(self):
        # how to poweron the nic, and get the present status?
        self._nic_prsnt_list = [True] * self._slots


    def mtp_get_nic_type(self, slot):
        # TODO, how to get nic type?
        return random.choice([NIC_Type.NAPLES100, NIC_Type.NAPLES25])


    def mtp_get_nic_serial_number(self, slot):
        # TODO, how to get sn?
        sn = "FLX0000000" + str(slot) 
        if not libmfg_utils.serial_number_validate(sn):
            self._nic_sta_list[slot] = NIC_Status.NIC_STA_NO_SN
            return None
        else:
            return sn


    def mtp_get_nic_mac_address(self, slot):
        # TODO, how to get mac?
        mac = "00AECD00000" + str(slot) 
        if not libmfg_utils.mac_address_validate(mac):
            self._nic_sta_list[slot] = NIC_Status.NIC_STA_NO_MAC
            return None
        else:
            return mac


    def mtp_get_nic_xcvr_prsnt(self, slot):
        # TODO: how to get xcvr present status?
        mask = NIC_Port_Mask.NIC_ALL_PORT_MASK
        return mask


    def mtp_get_prsnt_nic_list(self):
        return self._nic_prsnt_list


    def mtp_set_nic_vmarg(self, slot, vmarg):
        # TODO, how to set nic vmarg?
        nic_cli_id_str = libmfg_utils.id_str(nic = slot)
        self.cli_log_inf(nic_cli_id_str + "Set voltage margin to {:d}%".format(vmarg))
        return True


    def mtp_mgmt_connect_test(self):
        if not self.mtp_mgmt_connect():
            self.set_MTP_Status(MTP_Status.MTP_STA_MGMT_FAIL)
            return False

        time.sleep(1)
        self.mtp_mgmt_disconnect()
        return True


    def mtp_get_NIC_Status(self, slot):
        if self._nic_sta_list[slot] == NIC_Status.NIC_STA_HW_READY:
            return True
        else:
            False


    def mtp_run_diag_test_seq(self, slot, cmd, count):
        if self.mtp_get_NIC_Status(slot):
            self.mtp_mgmt_exec_cmd(cmd)
            time.sleep(random.randint(1, 5))
            return "PASS"


    def mtp_run_diag_test_para(self, slot_list, cmd, count):
        rslt_list = list()

        for slot in range(self._slots):
            if self.mtp_get_NIC_Status(slot) and slot in slot_list:
                rslt_list.append([slot, "PASS"])

        time.sleep(random.randint(1, 10))
        return rslt_list

