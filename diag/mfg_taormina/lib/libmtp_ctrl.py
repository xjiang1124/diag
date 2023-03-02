import pexpect
import time
import os
import sys
import libmfg_utils
import re
import threading
from datetime import datetime
from libmfg_cfg import *

from libdefs import NIC_Type
from libdefs import MTP_ASIC_SUPPORT
from libdefs import UUT_Type
from libdefs import MTP_DIAG_Error
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MTP_Const
from libdefs import NIC_Status
from libdefs import MTP_Status
from libdefs import NIC_Port_Mask
from libdefs import MFG_DIAG_CMDS
from libdefs import MFG_DIAG_SIG
from libdefs import MFG_DIAG_RE
from libdefs import FF_Stage
from libdefs import Swm_Test_Mode
from libdefs import NIC_IP_Address

from libnic_ctrl import nic_ctrl
from libtest_db import *

class mtp_ctrl():
    def __init__(self, mtpid, filep, diag_log_filep, diag_nic_log_filep_list, diag_cmd_log_filep=None, ts_cfg = None, usb_ts_cfg = None, mgmt_cfg = None, apc_cfg = None, num_of_slots = MTP_Const.MTP_SLOT_NUM, slots_to_skip = [False]*MTP_Const.MTP_SLOT_NUM, dbg_mode = False):
        self._id = mtpid
        self._ts_handle = None
        self._mgmt_handle = None
        self._mgmt_prompt = None
        self._mgmt_timeout = MTP_Const.MTP_POWER_ON_TIMEOUT
        self._diagmgr_handle = None
        self._ts_cfg = ts_cfg
        self._usb_ts_cfg = usb_ts_cfg
        self._mgmt_cfg = mgmt_cfg
        self._apc_cfg = apc_cfg
        self._prompt_list = libmfg_utils.get_linux_prompt_list()
        self._valid_type_list = MFG_VALID_NIC_TYPE_LIST
        self._proto_type_list = MFG_PROTO_NIC_TYPE_LIST
        self._slots = num_of_slots
        self._slots_to_skip = slots_to_skip
        self._fans = 3
        self._status = MTP_Status.MTP_STA_POWEROFF
        self._fanspd = MTP_Const.MFG_EDVT_NORM_FAN_SPD    # variable to track the fan speed (%) set by the script

        self._nic_ctrl_list = [None] * self._slots
        self._nic_alom_ctrl_list = [None] * self._slots
        self._nic_type_list = [None] * self._slots
        self._nic_prsnt_list = [False] * self._slots
        self._nic_scan_prsnt_list = [False] * self._slots
        self._nic_sn_list = [None] * self._slots
        self._nic_scan_sn_list = [None] * self._slots
        self._nic_alom_sn_list = [None] * self._slots

        self._nic_thread_list = [None] * self._slots
        # lock for nic cli
        self._lock = threading.Lock()
        # lock for parallel test run sequentially
        self._test_lock = threading.Lock()

        self._io_cpld_ver = None
        self._jtag_cpld_ver = None
        self._asic_support = None
        self._mtp_rev = None
        self._os_ver = None
        self._bio_ver = None
        self._svos_dat = None
        self._svos_ver = None
        self._diag_ver = None
        self._asic_ver = None
        self._uut_type = None
        self._uut_name = None
        self._cpld_dat = None
        self._swmtestmode = [Swm_Test_Mode.SWMALOM] * self._slots

        self._debug_mode = dbg_mode
        self._filep = filep
        self._cmd_buf = None
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._diag_nic_filep_list = diag_nic_log_filep_list[:]
        self._temppn = None

        self._sn = None
        self._mac = None
        self._pn = None
        self._maj = None
        self._prog_date = None
        self._edc = ""
        self._pcbasn = None

        self._homedir = "."
        self._tpm_skip = False
        self.uut_type = "TAORMINA"

        self._svos_boot = True # set to False once OS is installed
        # self._secure_login = False  #set to True when using signed OS
        self._use_usb_console = False

        self._hard_failure = False

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
                "FAN-4": "",
                "FAN-5": "",
                "FAN-6": ""
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

    def cli_log_inf(self, msg, level = 1):
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(cli_id_str + indent + msg)


    def cli_log_report_inf(self, msg):
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        prefix = "==> "
        postfix = " <=="
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + prefix + msg + postfix)
        else:
            libmfg_utils.cli_inf(cli_id_str + prefix + msg + postfix)


    def cli_log_err(self, msg, level = 1):
        cli_id_str = libmfg_utils.id_str(mtp = self._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_err(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_err(cli_id_str + indent + msg)


    def cli_log_slot_inf(self, slot, msg, level = 0):
        nic_cli_id_str = libmfg_utils.id_str(mtp = self._id, nic = slot)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(nic_cli_id_str + indent + msg)


    def cli_log_slot_err(self, slot, msg, level = 0):
        nic_cli_id_str = libmfg_utils.id_str(mtp = self._id, nic = slot)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_err(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_err(nic_cli_id_str + indent + msg)


    def cli_log_slot_inf_lock(self, slot, msg, level = 0):
        self._lock.acquire()
        self.cli_log_slot_inf(slot, msg, level)
        self._lock.release()


    def cli_log_slot_err_lock(self, slot, msg, level = 0):
        self._lock.acquire()
        self.cli_log_slot_err(slot, msg, level)
        self._lock.release()


    def cli_log_file(self, msg):
        self._filep.write(msg + "\n")

    def log_slot_test_start(self, slot, testname):
        # log the timestamp in NIC log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(testname, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)
        return start

    def log_slot_test_stop(self, slot, testname, start):
        # log the timestamp in NIC log
        stop = libmfg_utils.timestamp_snapshot()
        duration = stop - start
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(testname, str(stop), str(duration))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)
        return duration

    def log_test_start(self, testname):
        # log the timestamp in diag log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(testname, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self._diag_filep.write("\n"+ts_record_cmd+"\n")
        return start

    def log_test_stop(self, testname, start):
        # log the timestamp in diag log
        stop = libmfg_utils.timestamp_snapshot()
        duration = stop - start
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(testname, str(stop), str(duration))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self._diag_filep.write("\n"+ts_record_cmd+"\n")
        return duration


    def mtp_sys_info_disp(self):
        if self._uut_type == UUT_Type.TOR:
            return self.tor_sys_info_disp()

        self.cli_log_inf("MTP System Info Dump:", level=0)

        if not self._mgmt_cfg[0]:
            self.cli_log_err("Unable to retrieve MTP MGMT IP")
            return False
        self.cli_log_report_inf("MTP Chassis IP: {:s}".format(self._mgmt_cfg[0]))

        if not self._io_cpld_ver:
            self.cli_log_err("Unable to retrieve MTP IO-CPLD Version")
            return False
        self.cli_log_report_inf("MTP IO-CPLD Version: {:s}".format(self._io_cpld_ver))

        if not self._jtag_cpld_ver:
            self.cli_log_err("Unable to retrieve MTP JTAG-CPLD Version")
            return False
        self.cli_log_report_inf("MTP JTAG-CPLD Version: {:s}".format(self._jtag_cpld_ver))

        if not self._asic_support:
            self.cli_log_err("Unable to retrieve ASIC version supported by CPLD")
            return False
        self.cli_log_report_inf("MTP CPLD supports: {:s}".format(self._asic_support))

        if not self._mtp_rev:
            self.cli_log_err("Unable to retrieve MTP revision")
            return False
        self.cli_log_report_inf("MTP Rev: Rev_{:s}".format(self._mtp_rev))

        if not self._os_ver:
            self.cli_log_err("Unable to retrieve MTP Kernel Version")
            return False
        self.cli_log_report_inf("MTP Kernel Version: {:s}".format(self._os_ver))

        if not self._diag_ver:
            self.cli_log_err("Unable to retrieve MTP Diag Version")
            return False
        self.cli_log_report_inf("MTP Diag Version: {:s}".format(self._diag_ver))

        if not self._asic_ver:
            self.cli_log_err("Unable to retrieve MTP ASIC Version")
            return False
        self.cli_log_report_inf("MTP ASIC Version: {:s}".format(self._asic_ver))

        self.cli_log_inf("MTP System Info Dump End\n", level=0)
        return True

    def tor_sys_info_disp(self):
        self.cli_log_inf("TOR System Info Dump:", level=0)

        if not self._mgmt_cfg[0]:
            self.cli_log_err("Unable to retrieve TOR MGMT IP")
            return False
        self.cli_log_report_inf("TOR Chassis IP: {:s}".format(self._mgmt_cfg[0]))

        if not self._os_ver:
            self.cli_log_err("Unable to retrieve TOR Kernel Version")
            return False
        self.cli_log_report_inf("TOR Kernel Version: {:s}".format(self._os_ver))

        if not self._diag_ver:
            self.cli_log_err("Unable to retrieve TOR Diag Version")
            return False
        self.cli_log_report_inf("TOR Diag Version: {:s}".format(self._diag_ver))

        if not self._asic_ver:
            self.cli_log_err("Unable to retrieve TOR ASIC Version")
            return False
        self.cli_log_report_inf("TOR ASIC Version: {:s}".format(self._asic_ver))

        self.cli_log_inf("TOR System Info Dump End\n", level=0)
        return True


    def get_mgmt_cfg(self):
        return self._mgmt_cfg

    def get_ts_cfg(self):
        return self._ts_cfg

    def get_usb_ts_cfg(self):
        return self._usb_ts_cfg

    def set_usb_console(self):
        self._use_usb_console = True

    def unset_usb_console(self):
        self._use_usb_console = False

    def set_mtp_logfile(self, filep):
        self._filep = filep


    def set_mtp_diag_logfile(self, diag_filep):
        self._diag_filep = diag_filep
        self._mgmt_handle.logfile_read = self._diag_filep


    def mtp_get_cmd_buf(self):
        return self._cmd_buf


    def mtp_dump_err_msg(self, err_msg):
        self.cli_log_err("==== Error Message Start: ====")
        if err_msg:
            if (len(err_msg) > 512):
                top_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[:256])
                self.cli_log_err(top_err_msg)
                self.cli_log_err("<============================>")
                bottom_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[-256:])
                self.cli_log_err(bottom_err_msg)
            else:
                err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg)
                self.cli_log_err(err_msg)
        self.cli_log_err("==== Error Message End: ====")

    def mtp_dump_nic_err_msg(self, slot):
        err_msg = self.mtp_get_nic_cmd_buf(slot)
        if err_msg is None:
            err_msg = ""
        self.cli_log_slot_err(slot, "==== Error Message Start: ====")
        if err_msg:
            if (len(err_msg) > 512):
                top_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[:256])
                self.cli_log_slot_err(slot, top_err_msg)
                self.cli_log_slot_err(slot, "<============================>")
                bottom_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[-256:])
                self.cli_log_slot_err(slot, bottom_err_msg)
            else:
                err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg)
                self.cli_log_slot_err(slot, err_msg)
        self.cli_log_slot_err(slot, "==== Error Message End: ====")

    def set_mtp_status(self, status):
        if status < MTP_Status.MTP_STA_MAX:
            self._status = status


    def get_mtp_slot_num(self):
        return self._slots

    def set_uut_type(self, uut_type):
        self._uut_type = uut_type
        # make other changes here based on uut_type
        if self._uut_type == UUT_Type.TOR:
            self._mgmt_timeout = MTP_Const.TOR_POWER_ON_TIMEOUT
        else:
            self._mgmt_timeout = MTP_Const.MTP_POWER_ON_TIMEOUT

    def set_mtp_sn(self, sn):
        self._sn = sn

    def get_mtp_sn(self):
        return self._sn

    def set_mtp_mac(self, mac):
        self._mac = mac

    def get_mtp_mac(self):
        return self._mac

    def set_mtp_pn(self, pn):
        self._pn = pn

    def get_mtp_pn(self):
        return self._pn

    def set_mtp_prog_date(self, prog_date):
        self._prog_date = prog_date

    def get_mtp_prog_date(self):
        return self._prog_date

    def set_homedir(self, homedir):
        self._homedir = homedir

    def get_homedir(self):
        return self._homedir

    def set_hard_failure(self):
        self._hard_failure = True

    def hard_failure(self):
        return self._hard_failure

    def _mtp_single_apc_pwr_off(self, apc, userid, passwd, port_list):
        retry = 0
        handle = pexpect.spawn("telnet " + apc)
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["ame *:", "assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
            elif idx > 1 and retry < 5:
                retry += 1
                handle = pexpect.spawn("telnet " + apc)
                continue
            else:
                self.cli_log_err("Unable to connect APC: " + apc)
                return False

        idx = handle.expect_exact(["PX2", "Schneider", "American Power Conversion", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            self.cli_log_err("Need to add PX2 support")
            return False
        # Supported apc
        elif idx == 1 or idx == 2:
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
        retry = 0
        handle = pexpect.spawn("telnet " + apc)
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["ame *:", "assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
            elif idx > 1 and retry < 5:
                retry += 1
                handle = pexpect.spawn("telnet " + apc)
                continue
            else:
                self.cli_log_err("Unable to connect APC: " + apc)
                return False

        idx = handle.expect_exact(["PX2", "Schneider", "American Power Conversion", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            self.cli_log_err("Need to add PX2 support")
            return False
        # Supported apc
        elif idx == 1 or idx == 2:
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

        idx = handle.expect_exact(["PX2", "Schneider", "American Power Conversion", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            self.cli_log_err("Need to add PX2 support")
            return False
        # Supported apc
        elif idx == 1 or idx == 2:
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


    def mtp_session_create(self, logfile=None):
        if logfile is None:
            logfile = "/tmp/mtpsession.log"
        logfilep = open(logfile, "w")

        # mgmt_cfg is a list with format [ip, userid, passwd]
        ip = self._mgmt_cfg[0]
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        ssh_cmd = libmfg_utils.get_ssh_connect_cmd(userid, ip)
        handle = pexpect.spawn(ssh_cmd, logfile=logfilep)
        idx = libmfg_utils.mfg_expect(handle, ["assword:"], timeout=60)
        if idx < 0:
            self.cli_log_err("Can not connect to mtp, check the console.\n", level = 0)
            return None
        else:
            handle.sendline(passwd)

        idx = libmfg_utils.mfg_expect(handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            return None

        ## new CXOS:
        handle.sendline("sudo su")
        idx = libmfg_utils.mfg_expect(handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err(handle.before)
            self.cli_log_err("Cant reach shell after ssh login", level = 0)
            return None
        ## end new CXOS

        cmd = MFG_DIAG_CMDS.MTP_LOGIN_VERIFY_FMT
        sig_list = [userid]
        handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(handle, sig_list, timeout=60)
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt failed", level = 0)
            return None
        
        handle.sendline("stty rows 50 cols 200")
        idx = libmfg_utils.mfg_expect(handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err(handle.before)
            self.cli_log_err("Cant resize shell after ssh login", level = 0)
            return None

        return handle


    def mtp_nic_para_session_init(self):
        userid = self._mgmt_cfg[1]
        if self._uut_type == UUT_Type.TOR:
            mtp_prompt = "#"
        else:
            mtp_prompt = "$"
        for slot in range(self._slots):
            handle = self.mtp_session_create()
            if handle:
                if not self.mtp_prompt_cfg(handle, userid, mtp_prompt, slot):
                    self.cli_log_err("Unable to config new ssh session for NIC")
                    return False
                prompt = "{:s}@NIC-{:02d}:".format(userid, slot+1) + mtp_prompt
                self._nic_ctrl_list[slot] = nic_ctrl(slot, self._diag_nic_filep_list[slot])
                self._nic_ctrl_list[slot].nic_handle_init(handle, prompt)
                if self._uut_type == UUT_Type.TOR:            
                    para_cmd = "export PYTHONPATH=/home/diag/python_files/lib/python2.7/site-packages"
                    if not self.mtp_mgmt_exec_cmd_para(slot, para_cmd):
                        self.cli_log_slot_err(slot, "{:s} failed".format(para_cmd))
                        return False
                para_cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
                if not self.mtp_mgmt_exec_cmd_para(slot, para_cmd):
                    self.cli_log_slot_err(slot, "Failed to execute para command: {:s}".format(para_cmd))
                    return False
            else:
                self.cli_log_err("Unable to create MTP session")
                return False
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
        self._mgmt_handle = pexpect.spawn(ssh_cmd)
        while True:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["assword:"], timeout=60)
            if idx < 0:
                if retries > 0:
                    self.cli_log_inf("Connect to mtp timeout, wait {:d}s and retry...".format(delay), level = 0)
                    time.sleep(delay)
                    retries -= 1
                    self._mgmt_handle = pexpect.spawn(ssh_cmd)
                    continue
                else:
                    self.cli_log_err("Connect to mtp failed\n", level = 0)
                    return None
            else:
                self._mgmt_handle.sendline(passwd)
                break
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err(self._mgmt_handle.before)
            self.cli_log_err("Cant reach shell after ssh login", level = 0)
            return None

        ## new CXOS:
        self._mgmt_handle.sendline("sudo su")
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, self._prompt_list, timeout=60)
        if idx < 0:
            self.cli_log_err(self._mgmt_handle.before)
            self.cli_log_err("Cant reach shell after ssh login", level = 0)
            return None
        ## end new CXOS

        self._mgmt_prompt = self._prompt_list[idx]

        cmd = MFG_DIAG_CMDS.MTP_LOGIN_VERIFY_FMT
        sig_list = [userid]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
            self.cli_log_err("Connect to mtp mgmt failed", level = 0)
            return None

        # set logfile
        self._mgmt_handle.logfile_read = self._diag_filep
        self._mgmt_handle.logfile_send = self._diag_cmd_filep
        if prompt_cfg:
            # config the prompt
            if prompt_id:
                userid = prompt_id
            else:
                userid = self._mgmt_cfg[1]
            if not self.mtp_prompt_cfg(self._mgmt_handle, userid, self._mgmt_prompt):
                self.cli_log_err("Failed to Init Diag SW Environment", level=0)
                return None
            self._mgmt_prompt = "{:s}@{:s}:".format(userid, UUT_Type.dsp_type[self._uut_type]) + self._mgmt_prompt

        return self._mgmt_prompt


    def mtp_prompt_cfg(self, handle, userid, prompt, slot=None):
        handle.sendline("stty rows 50 cols 200")
        idx = libmfg_utils.mfg_expect(handle, [prompt])
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
            return False

        if slot != None:
            prompt_str = "{:s}@NIC-{:02d}:{:s} ".format(userid, slot+1, prompt)
        else:
            prompt_str = "{:s}@{:s}:{:s} ".format(userid, UUT_Type.dsp_type[self._uut_type], prompt)
        handle.sendline("PS1='{:s}'".format(prompt_str))

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


    def mtp_enter_user_ctrl(self):
        if self._mgmt_handle and self._debug_mode:
            self._mgmt_handle.interact()


    def mtp_mgmt_exec_sudo_cmd(self, cmd):
        if self._uut_type == UUT_Type.TOR:
            # already in sudo, ignore this part
            return self.mtp_mgmt_exec_cmd(cmd)

        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        if not self._mgmt_handle:
            self.cli_log_err("Management port is not connected")
            return False

        self._mgmt_handle.sendline("sudo -k " + cmd)
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [userid + ":"])
        if idx < 0:
            self._mgmt_handle.logfile_read = None
            self._mgmt_handle.logfile_send = None
            self.mtp_mgmt_disconnect()
            return True
        self._mgmt_handle.sendline(passwd)

        if cmd == "reboot" or cmd == "poweroff":
            self._mgmt_handle.expect_exact(pexpect.EOF)
            self._mgmt_handle.logfile_read = None
            self._mgmt_handle.logfile_send = None
            self.mtp_mgmt_disconnect()
        else:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, [self._mgmt_prompt])
            if idx < 0:
                self.cli_log_err("Connect to mtp mgmt timeout", level = 0)
                return False

        return True

    def mtp_nic_send_ctrl_c(self, slot):
        if self._nic_ctrl_list[slot] == None:
            # script not running anything.
            return True
        if not self._nic_ctrl_list[slot].nic_send_ctrl_c():
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            self.cli_log_slot_err(slot, "Couldn't send C+C")
            return False
        return True

    def mtp_mgmt_set_date(self, timestamp_str):
        if self._uut_type == UUT_Type.TOR:
            cmd = "hwclock --set --date '{:s}'".format(timestamp_str)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Unable to set UUT date")
                return False

            cmd = "hwclock -s"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Unable to save UUT date")
                return False

            return True

        cmd = MFG_DIAG_CMDS.NIC_DATE_SET_FMT.format(timestamp_str)
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_err("Unable to set MTP date")
            return False

        mtp_mgmt_ctrl.cli_log_inf("UUT Chassis timestamp sync'd", level=0)
        return True

    def mtp_console_enter_shell(self, shell="sh"):

        successentersh = False
        for x in range(3):
            self._mgmt_handle.sendline(shell)

            time.sleep(2)
            if self.mtp_console_connect():
                time.sleep(2)
                self.mtp_mgmt_exec_cmd("echo $SHELL")
                successentersh = True
            if shell == "sh":
                successentersh = False
                if self.mtp_mgmt_exec_cmd("stty rows 50 cols 160", sig_list=["#"]):
                    successentersh = True

            if shell == "svcli":
                successentersh = False
                if self.mtp_mgmt_exec_cmd("", sig_list=[">"]):
                    successentersh = True

            if successentersh:
                break

        return successentersh

    def mtp_console_connect(self, prompt_cfg=False, prompt_id=None, secure_login=False):
        # if not self.mtp_console_disconnect():
        #     return None
        self.mtp_console_spawn()

        # secure_login = secure_login or self._secure_login #set either by argument or class variable

        delay = MTP_Const.TOR_CONSOLE_CON_DELAY
        retries = 0
        #max_retries = self._mgmt_timeout / delay
        max_retries = 10
        prompt_list = ["Connection refused", "ServiceOS login:", "Last login:", " login:", "assword:", "$", "#", ">"]

        # secure_login = True #always
        fresh_login = False
        while True:
            time.sleep(1) # this is crucial so that the prompt is safely out of the console buffer (not pexpect buffer)
            self.clear_buffer()
            time.sleep(1)
            self._mgmt_handle.sendline()
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, prompt_list)
            if idx < 0:
                if retries < max_retries:
                    self.cli_log_inf("Console to uut timeout, wait {:d}s and retry...".format(delay))
                    libmfg_utils.count_down(delay)
                    retries += 1
                    # self.mtp_console_disconnect()
                    self.mtp_console_spawn()
                    self._mgmt_handle.sendline()
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
                        libmfg_utils.mtp_clear_console(self)
                    # self.mtp_console_disconnect()
                    self.mtp_console_spawn()
                else:
                    self.cli_log_err("Console to uut failed. Connection refused.\n", level = 0)
                    return None
            elif idx == 1:
                self._mgmt_handle.sendline("admin")
            elif idx == 2:
                continue
            elif idx == 3:
                self._mgmt_handle.sendline("admin")
                fresh_login = True
            elif idx == 4:
                self._mgmt_handle.sendline("")
            elif idx == 5:
                self._mgmt_handle.sendline("sudo su")
                # allow scp from outside:
                self._mgmt_handle.sendline('sed -i "s/admin:\/usr\/bin\/vtysh/admin:\/bin\/sh/g" /etc/passwd')
                fresh_login = False
            elif idx == 6 and fresh_login:
                self._mgmt_handle.sendline("start-shell")
            else:
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

        # set logfile
        self._mgmt_handle.logfile_read = self._diag_filep
        self._mgmt_handle.logfile_send = self._diag_cmd_filep
        if prompt_cfg:
            # config the prompt
            if prompt_id:
                userid = prompt_id
            else:
                userid = self._mgmt_cfg[1]
            if not self.mtp_prompt_cfg(self._mgmt_handle, userid, self._mgmt_prompt):
                self.cli_log_err("Failed to Init Diag SW Environment", level=0)
                return None
            self._mgmt_prompt = "{:s}@UUT:".format(userid) + self._mgmt_prompt

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

        if len(self._ts_cfg[1]) == 2:
            port = "40" + self._ts_cfg[1]
        elif len(self._ts_cfg[1]) == 4:
            port = "40" + self._ts_cfg[1][-2:]
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

        if len(self._usb_ts_cfg[1]) == 2:
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
        self._mgmt_handle = pexpect.spawn(telnet_cmd, logfile=self._diag_filep)
        self._mgmt_handle.setecho(False)
        # self._mgmt_handle.logfile = sys.stdout
        self._mgmt_handle.logfile_read = self._diag_filep
        self._mgmt_handle.logfile_send = self._diag_cmd_filep

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

    def mtp_nic_console_attach(self, slot):
        if self._uut_type == NIC_Type.TAORMINA:
            self.mtp_mgmt_exec_cmd("cd {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH))
            con_cmd = "./econ.bash {:d}".format(slot)
        else:
            con_cmd = MFG_DIAG_CMDS.NIC_CON_ATTACH_FMT.format(slot+1)
        self._mgmt_handle.sendline(con_cmd)
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Terminal ready"], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            self.cli_log_slot_err(slot, "Unable to connect console")
            self.cli_log_slot_err(slot, self._mgmt_handle.before)
            return False
        time.sleep(5)
        # send return
        self._mgmt_handle.sendline("")

        exp_list = ["# ", "login:", "assword:"]
        while True:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, exp_list, timeout=MTP_Const.NIC_CON_INIT_DELAY)
            if idx == 0:
                break
            elif idx == 1:
                self._mgmt_handle.sendline(NIC_MGMT_USERNAME)
                continue
            elif idx == 2:
                self._mgmt_handle.sendline(NIC_MGMT_PASSWORD)
                continue
            else:
                self.cli_log_slot_err(slot, "Unable to connect console")
                self.cli_log_slot_err(slot, self._mgmt_handle.before)
                self.mtp_nic_console_detach()
                return False

        return True

    def mtp_nic_console_detach(self):
        self._mgmt_handle.sendcontrol('a')
        self._mgmt_handle.sendcontrol('x')
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Terminating", self._mgmt_prompt], timeout=MTP_Const.NIC_CON_INIT_DELAY)
        if idx < 0:
            return False
        else:
            return True

    def mtp_sys_info_init(self):

        if self._uut_type != UUT_Type.TOR:
            # MTP IO cpld version
            reg_addr = 0x0
            cmd = MFG_DIAG_CMDS.MTP_CPLD_READ_FMT.format(reg_addr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to get MTP IO-CPLD image version info", level = 0)
                return False
            match = re.findall(r"addr 0x{:x} with data (0x[0-9a-fA-F]+)".format(reg_addr), self.mtp_get_cmd_buf())
            if match:
                self._io_cpld_ver = match[0]
            else:
                self.cli_log_err("Failed to get MTP IO-CPLD image version info", level = 0)
                return False

            # MTP JTAG cpld version
            reg_addr = 0x19
            cmd = MFG_DIAG_CMDS.MTP_CPLD_READ_FMT.format(reg_addr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to get MTP JTAG-CPLD image version info", level = 0)
                return False
            match = re.findall(r"addr 0x{:x} with data (0x[0-9a-fA-F]+)".format(reg_addr), self.mtp_get_cmd_buf())
            if match:
                self._jtag_cpld_ver = match[0]
            else:
                self.cli_log_err("Failed to get MTP JTAG-CPLD image version info", level = 0)
                return False

        # MTP_TYPE
        cmd = MFG_DIAG_CMDS.MTP_ASIC_SUPPORTED_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to send command for getting asic supported version", level = 0)
            return False
        match = re.findall(r"MTP_TYPE=MTP_([a-zA-Z]{3,4}.?)", self.mtp_get_cmd_buf())
        if match:
            self._asic_support = match[0].strip().upper()
        else:
            self.cli_log_err("Failed to get asic supported version", level = 0)
            return False

        if self._uut_type == UUT_Type.NAPLES_MTP:
            # MTP_REV
            cmd = MFG_DIAG_CMDS.MTP_REV_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to send command for getting MTP revision", level = 0)
                return False
            match = re.findall(r"MTP_REV=REV_([0-9]{2}|NONE)", self.mtp_get_cmd_buf())
            if match:
                self._mtp_rev = match[0]
            else:
                self.cli_log_err("Failed to get MTP revision", level = 0)
                return False

        # MTP OS version
        cmd = MFG_DIAG_CMDS.MTP_IMG_VER_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get os image version", level = 0)
            return False
        match = re.findall(r"SMP (.* 20\d{2})", self.mtp_get_cmd_buf())
        if match:
            self._os_ver = match[0]
        else:
            self.cli_log_err("Failed to get os image version", level = 0)
            return False

        # MTP Diag image version
        if self._uut_type == UUT_Type.NAPLES_MTP:
            cmd = MFG_DIAG_CMDS.MTP_DIAG_VERSION_FMT
        else:
            cmd = "cat /home/diag/diag/scripts/version.txt"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get diag image version", level = 0)
            return False
        match = re.findall(r"Date: +(.*20\d{2})", self.mtp_get_cmd_buf())
        if match:
            self._diag_ver = match[0]
        else:
            self.cli_log_err("Failed to get diag image version", level = 0)
            return False

        # MTP ASIC image version
        cmd = MFG_DIAG_CMDS.MTP_ASIC_VERSION_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get asic util version", level = 0)
            return False
        match = re.findall(r"Date: +(.*20\d{2})", self.mtp_get_cmd_buf())
        if match:
            self._asic_ver = match[0]
        else:
            self.cli_log_err("Failed to get asic util version", level = 0)
            return False

        if self._uut_type == UUT_Type.TOR:
            if not self.mtp_mgmt_exec_cmd("fpgautil inventory"):
                self.cli_log_err("Failed to get inventory from fpgautil", level=0)
                return False

        return True

    def mtp_get_asic_support(self):
        return self._asic_support

    def mtp_get_hw_version(self):
        return [self._io_cpld_ver, self._jtag_cpld_ver]


    def mtp_get_os_version(self):
        return self._os_ver


    def mtp_get_sw_version(self):
        return self._diag_ver


    def mtp_get_asic_version(self):
        return self._asic_ver

    def mtp_get_swmtestmode(self, slot):
        return self._swmtestmode[slot]

    def mtp_set_swmtestmode(self, swmtestmode):
        read_data = [0]
        for slot in range(self._slots):
            self._swmtestmode[slot] = swmtestmode

        for slot in range(self._slots):
            if self._swmtestmode[slot] == Swm_Test_Mode.SW_DETECT:
                read_data[0] = 0x00
                #See if we can read the MTP Adapter CPLD ID.  This would indicate an ALOM should be present
                rc = self._nic_ctrl_list[slot].nic_read_mtp_adapt_cpld(0x80, read_data)
                if read_data[0] == 0x1b:
                    self.cli_log_slot_inf(slot, "NAPLES25SWM ALOM DETECTED")
                    self._swmtestmode[slot] = Swm_Test_Mode.SWMALOM
                else:
                    self._swmtestmode[slot] = Swm_Test_Mode.SWM
        return True

    def mtp_stale_image_cleanup(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = "rm -f naples* image_a*"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        return True


    def mtp_update_mtp_diag_image(self, image):
        if self._uut_type == UUT_Type.TOR:
            diag_folder = self._homedir + "diag/"
        else:
            diag_folder = MTP_DIAG_Path.ONBOARD_MTP_MTP_DIAG_PATH
        diag_folder_parent = os.path.abspath(os.path.join(diag_folder, os.pardir))

        cmd = "rm -rf {:s}".format(diag_folder)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = "tar zxf {:s} -C {:s}".format(image, diag_folder_parent)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        return True


    def mtp_update_nic_diag_image(self, image):
        if self._uut_type == UUT_Type.TOR:
            nic_diag_folder = self._homedir + "nic_diag/"
        else:
            nic_diag_folder = MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH

        cmd = "rm -rf {:s}".format(nic_diag_folder)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(nic_diag_folder)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = "tar zxf {:s} -C {:s}".format(image, nic_diag_folder)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
            return False

        return True


    def mtp_mgmt_poweroff(self):
        if not self.mtp_mgmt_exec_cmd("sync", timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute sync command")
            return False
        if self._uut_type == UUT_Type.TOR:
            if not self.mtp_mgmt_exec_cmd("shutdown now"):
                self.cli_log_err("Failed to execute shutdown command")
                return False
        else:
            if not self.mtp_mgmt_exec_sudo_cmd("poweroff"):
                self.cli_log_err("Failed to execute poweroff command")
                return False

        return True

    def mtp_mgmt_reboot(self):
        if not self.mtp_mgmt_exec_cmd("sync", timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute sync command")
            return False

        if not self.mtp_mgmt_exec_sudo_cmd("reboot"):
            self.cli_log_err("Failed to execute reboot command")
            return False

        self.cli_log_inf("Reboot occured, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_REBOOT_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_REBOOT_DELAY)

        return True


    def mtp_chassis_shutdown(self, mtp=True):
        if mtp:
            self.mtp_mgmt_poweroff()
            self.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
            libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        self.mtp_apc_pwr_off()
        self.cli_log_inf("Power off APC, Wait {:d} seconds for APC shutdown".format(MTP_Const.MTP_POWER_CYCLE_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)


    def mtp_power_cycle(self, mtp=True):
        if mtp:
            self.mtp_mgmt_poweroff()
            self.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
            libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        self.cli_log_inf("Power off APC", level=0)
        self.mtp_apc_pwr_off()
        if mtp:
            libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
        else:
            libmfg_utils.count_down(MTP_Const.TOR_POWER_CYCLE_DELAY)
        self.mtp_apc_pwr_on()
        self.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        if mtp:
            libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
        else:
            libmfg_utils.count_down(MTP_Const.TOR_POWER_ON_DELAY)
        return True


    def mtp_mgmt_exec_cmd(self, cmd, sig_list=[], fail_sig_list=[], timeout=MTP_Const.OS_CMD_DELAY):
        # return self.mtp_mgmt_exec_cmd2(cmd, sig_list, fail_sig_list, timeout)
        return self.mtp_mgmt_exec_cmd_no_error_printout(cmd, sig_list, timeout)

        rc = True
        self._mgmt_handle.sendline(cmd)
        cmd_before = ""
        for sig in sig_list:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, [sig], timeout)
            if idx < 0:
                rc = False
                cmd_before = self._mgmt_handle.before
                break
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [self._mgmt_prompt], timeout)
        # signature match fails
        if not rc:
            self.mtp_dump_err_msg(cmd_before)
            return False
        elif idx < 0:
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False
        else:
            self._cmd_buf = self._mgmt_handle.before
            return True

    def mtp_mgmt_exec_cmd_no_error_printout(self, cmd, sig_list=[], timeout=MTP_Const.OS_CMD_DELAY):
        self.clear_buffer()
        rc = True
        self._mgmt_handle.sendline(cmd)
        cmd_before = ""
        for sig in sig_list:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, [sig], timeout)
            if idx < 0:
                rc = False
                cmd_before = self._mgmt_handle.before
                break
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [self._mgmt_prompt], timeout)
        # signature match fails
        if not rc:
            #self.mtp_dump_err_msg(cmd_before)
            return False
        elif idx < 0:
            #self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False
        else:
            self._cmd_buf = self._mgmt_handle.before
            if self._use_usb_console:
                self._mgmt_handle.sendline("") # extra newline for USB console server
            return True

    def mtp_mgmt_exec_cmd2(self, cmd, pass_sig_list=[], fail_sig_list=[], timeout=MTP_Const.OS_CMD_DELAY):
        self.clear_buffer()
        rc = True
        self._mgmt_handle.sendline(cmd)
        cmd_before = ""
        if sig_list:
            sig_list = pass_sig_list + fail_sig_list
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, sig_list, timeout)
            cmd_before = self._mgmt_handle.before
            if idx < 0:
                rc = False
            elif idx < len(pass_sig_list):
                rc = True
            else:
                rc = False
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [self._mgmt_prompt], timeout)
        # signature match fails
        if not rc:
            self.mtp_dump_err_msg(cmd_before)
            return False
        elif idx < 0:
            print("idx < 0")
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False
        else:
            self._cmd_buf = self._mgmt_handle.before
            return True

    def clear_buffer(self):

        buff = None
        try:
            buff = self._mgmt_handle.read_nonblocking(16384, timeout = 1)
            #print("clear_buffer(): read_nonblocking: ***{}***".format(buff))
        except pexpect.exceptions.TIMEOUT as toe:
            #print("clear_buffer(): TIMEOUT, buff: ***{}***".format(buff))
            pass
        except pexpect.exceptions.EOF:
            pass

    def mtp_diag_fail_report(self, msg):
        err_msg = MTP_DIAG_Report.MTP_DIAG_REGRESSION_FAIL + ", ERR_MSG: {:s}".format(msg)
        self.cli_log_err(err_msg, level=0)


    def mtp_nic_diag_fail_report(self, slot, sn):
        msg = "SN[{:s}]".format(sn) + MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL
        self.cli_log_slot_err(slot, msg)


    def mtp_nic_diag_pass_report(self, slot, sn):
        msg = "SN[{:s}]".format(sn) + MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS
        self.cli_log_slot_inf(slot, msg)


    def mtp_misc_init(self):
        # vrm test
        cmd = MFG_DIAG_CMDS.MTP_VRM_TEST_FMT
        pass_sig_list = [MFG_DIAG_SIG.MTP_VRM_OK_SIG]
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list)
        if rc:
            self.cli_log_inf("VRM test passed")
        else:
            self.cli_log_err("VRM test failed")

        return rc


    def mtp_fan_init(self, fan_spd):
        rc = True
        # Fan present test
        cmd = MFG_DIAG_CMDS.MTP_FAN_PRSNT_FMT
        pass_sig_list = [MFG_DIAG_SIG.MTP_FAN0_PRSNT_SIG, MFG_DIAG_SIG.MTP_FAN1_PRSNT_SIG, MFG_DIAG_SIG.MTP_FAN2_PRSNT_SIG]
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list)
        if rc:
            self.cli_log_inf("FAN present test passed")
        else:
            self.cli_log_err("FAN present test failed")
            return rc

        # Fan speed test
        cmd = MFG_DIAG_CMDS.MTP_FAN_TEST_FMT
        pass_sig_list = [MFG_DIAG_SIG.MTP_FAN_OK_SIG]
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list)
        if rc:
            self.cli_log_inf("FAN speed test passed")
        else:
            self.cli_log_err("FAN speed test failed")
            return rc

        # Fan speed set
        self.cli_log_inf("Set FAN Speed to {:d}%".format(fan_spd))
        cmd = MFG_DIAG_CMDS.MTP_FAN_SET_SPD_FMT.format(fan_spd)
        rc = self.mtp_mgmt_exec_cmd(cmd)
        if not rc:
            self.cli_log_err("Failed to set fan speed to {:d}%".format(fan_spd))

        self._fanspd = fan_spd          # update class variable

        # Fan status dump
        cmd = MFG_DIAG_CMDS.MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            rc = False

        return rc


    def mtp_diag_pre_init(self, diagmgr_logfile):
        # start the mtp diag
        self.cli_log_inf("Pre Diag SW Environment Init", level=0)

        if self._uut_type == UUT_Type.TOR:
            cmd = "./start_diag_tor.sh"
            sig_list = [MFG_DIAG_SIG.TOR_DIAG_OK_SIG]
        else:
            cmd = MFG_DIAG_CMDS.MTP_DIAG_INIT_FMT
            sig_list = [MFG_DIAG_SIG.MTP_DIAG_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        if self._uut_type == UUT_Type.TOR:
            cmd = "source /home/root/.profile"
        else:
            cmd = "source ~/.bash_profile"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = "env | grep UUT"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute env command", level=0)
            return False

        # start the mtp diagmgr
        diagmgr_handle = self.mtp_session_create()
        if not diagmgr_handle:
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        diagmgr_handle.sendline("source /home/root/.profile")
        idx = libmfg_utils.mfg_expect(diagmgr_handle, libmfg_utils.get_linux_prompt_list())
        if idx < 0:
            self.cli_log_err("Failed to Init DiagMgr SW Environment", level=0)
            return False

        cmd = MFG_DIAG_CMDS.MTP_DIAG_MGR_START_FMT.format(diagmgr_logfile)
        diagmgr_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(diagmgr_handle, libmfg_utils.get_linux_prompt_list())
        if idx < 0:
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
        # diagmgr_handle.close()
        self._diagmgr_handle = diagmgr_handle

        # config the prompt
        userid = self._mgmt_cfg[1]
        if not self.mtp_prompt_cfg(self._mgmt_handle, userid, self._mgmt_prompt):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False
        self._mgmt_prompt = "{:s}@{:s}:".format(userid, UUT_Type.dsp_type[self._uut_type]) + self._mgmt_prompt

        # register MTP diagsp
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        if self._uut_type == UUT_Type.TOR:
            cmd = MFG_DIAG_CMDS.TOR_DSP_START_FMT
            sig_list = [MFG_DIAG_SIG.TOR_DSP_START_OK_SIG]
        else:
            cmd = MFG_DIAG_CMDS.MTP_DSP_START_FMT
            sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        if not self.mtp_sys_info_init():
            self.cli_log_err("Failed to Init MTP system information", level=0)
            return False

        if self._uut_type == UUT_Type.TOR:
            if not self.tor_fru_init():
                self.cli_log_err("Failed to init TOR FRU", level=0)
                return False

            if not self.tor_board_id():
                self.cli_log_err("Failed to Init TOR board info", level=0)
                return False


        self.cli_log_inf("Pre Diag SW Environment Init complete\n", level=0)

        return True


    def mtp_diag_zmq_init(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        retry = 0

        while retry < 3:
            retry += 1
            self.cli_log_inf("Init Diag ZMQ Environment <{:d}>...".format(retry), level=0)
            # 1. stop ZMQ
            cmd = MFG_DIAG_CMDS.MTP_ZMQ_STOP_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False

            # 2. stop MTP DSP
            cmd = MFG_DIAG_CMDS.MTP_DSP_STOP_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False
            time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

            # 3. sys cleanup
            cmd = MFG_DIAG_CMDS.MTP_DSP_CLEANUP_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False

            # 4. start MTP DSP
            cmd = MFG_DIAG_CMDS.MTP_DSP_START_FMT
            sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False
            time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

            # 5. start ZMQ
            cmd = MFG_DIAG_CMDS.MTP_ZMQ_START_FMT
            sig_list = [MFG_DIAG_SIG.MTP_ZMQ_OK_SIG]
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
                continue
            else:
                break

        if retry >= 3:
            self.cli_log_err("Failed to Init Diag ZMQ Environment", level=0)
            return False

        self.cli_log_inf("Init Diag ZMQ Environment complete\n", level=0)
        return True;


    def mtp_diag_get_img_files(self, folder=MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH):
        cmd = "ls --color=never {:s}".format(folder)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd), level=0)
            return ""
        cmd_buf = self.mtp_get_cmd_buf().split()
        return cmd_buf


    def mtp_diag_post_init(self, mtp_capability, stage):
        self.cli_log_inf("Post Diag SW Environment Init", level=0)
        cmd = "rm -f {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to remove previous ASIC test logfile", level=0)
            return False
        cmd = "rm -f {:s}".format(MTP_DIAG_Logfile.ONBOARD_CSP_LOG_FILES)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to remove previous CSP test logfile", level=0)
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to Init DiagSP", level=0)
            return False

        cmd = MFG_DIAG_CMDS.MTP_DSP_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Dump DSP failed", level=0)
            return False

        if self._uut_type == UUT_Type.TOR:
            # kill these processes to prevent conflict with diags
            cmd = "killall pmd; killall hhmd; killall tempd; killall vrfmgrd; killall fand ;killall powerd"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to kill daemons", level=0)
                return False

        # check if firmware image exist
        img_list = []
        mtp_capability = 0 # hard-ignoring image check for taormina
        if (mtp_capability & 0x1):
            for card_type in MTP_REV02_CAPABLE_NIC_TYPE_LIST:
                if stage == FF_Stage.FF_DL:
                    # CPLD and diagfw images. Failsafe image for Elba cards
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.diagfw_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(card_type))
                        pass

                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.diagfw_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing diagfw timestamp for {:s}".format(card_type))
                        return False
                elif stage == FF_Stage.FF_CFG:
                    # CPLD image
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                elif stage == FF_Stage.FF_SWI:
                    # Secure CPLD and goldfw images
                    try:
                        img = NIC_IMAGES.sec_cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.goldfw_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing goldfw image for {:s}".format(card_type))
                        pass

                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.sec_cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.sec_cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.goldfw_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing goldfw timestamp for {:s}".format(card_type))
                        return False
                else:
                    # no images needed in this stage
                    continue

        if (mtp_capability & 0x2):
            for card_type in MTP_REV03_CAPABLE_NIC_TYPE_LIST:
                if stage == FF_Stage.FF_DL:
                    # CPLD and diagfw images
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.diagfw_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing diagfw image for {:s}".format(card_type))
                        pass
                    try:
                        if card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2:
                            img = NIC_IMAGES.fail_cpld_img[card_type]
                            if img.strip() == "":
                                raise KeyError
                            img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing failsafe cpld image for {:s}".format(card_type))
                        pass

                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.diagfw_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing diagfw timestamp for {:s}".format(card_type))
                        return False
                    try:
                        if card_type == NIC_Type.ORTANO or card_type == NIC_Type.ORTANO2:
                            expected_timestamp = NIC_IMAGES.fail_cpld_dat[card_type]
                            if expected_timestamp.strip() == "":
                                raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing failsafe cpld timestamp for {:s}".format(card_type))
                        pass
                elif stage == FF_Stage.FF_CFG:
                    # CPLD image
                    try:
                        img = NIC_IMAGES.cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld image for {:s}".format(card_type))
                        pass
                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing cpld timestamp for {:s}".format(card_type))
                        return False
                elif stage == FF_Stage.FF_SWI:
                    # Secure CPLD and goldfw images
                    try:
                        img = NIC_IMAGES.sec_cpld_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld image for {:s}".format(card_type))
                        pass
                    try:
                        img = NIC_IMAGES.goldfw_img[card_type]
                        if img.strip() == "":
                            raise KeyError
                        img_list.append(img)
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing goldfw image for {:s}".format(card_type))
                        pass

                    # In addition to images, check the version & timestamp fields as well here
                    try:
                        expected_version = NIC_IMAGES.sec_cpld_ver[card_type]
                        if expected_version.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld version for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.sec_cpld_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing sec_cpld timestamp for {:s}".format(card_type))
                        return False
                    try:
                        expected_timestamp = NIC_IMAGES.goldfw_dat[card_type]
                        if expected_timestamp.strip() == "":
                            raise KeyError
                    except KeyError:
                        self.cli_log_err("mfg_cfg is missing goldfw timestamp for {:s}".format(card_type))
                        return False

                else:
                    # no images needed in this stage
                    continue

        cmd = "ls {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd), level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf()
        for img_file in img_list:
            if not os.path.basename(img_file) in cmd_buf:
                self.cli_log_err("Firmware {:s} doesn't exist".format(img_file), level=0)
                return False

        self.cli_log_inf("Post Diag SW Environment Init complete\n", level=0)
        # naples100 dsp check
#        self.cli_log_inf("Start Diag DSP Sanity Check", level = 0)
#        naples100_dsp_list = naples100_test_db.get_diag_seq_dsp_list()
#        naples100_dsp_list += naples100_test_db.get_diag_para_dsp_list()
#        for dsp in naples100_dsp_list:
#            if dsp not in self._mgmt_handle.before:
#                self.cli_log_err("Diag DSP: {:s} is not detected".format(dsp), level = 0)
#                return False
#        self.cli_log_inf("Diag DSP Sanity Check Complete", level = 0)

        return True


    def mtp_hw_init(self, fan_spd):
        """
         Elba cards need higher fan_spd
         40% -> 50%     : elba LT, NT
         90% -> 100%    : elba HT
         max = 100%
        """
        if self._asic_support == MTP_ASIC_SUPPORT.ELBA:
            fan_spd = min(100, fan_spd + 20)
        rc = True

        self.cli_log_inf("Start MTP chassis sanity check", level = 0)
        # mtp cpld test
        rc &= self.mtp_cpld_test()
        # fan init
        rc &= self.mtp_fan_init(fan_spd)

        # other platform init
        rc &= self.mtp_misc_init()
        if rc:
            self.cli_log_inf("MTP chassis sanity check passed\n", level = 0)
        else:
            self.cli_log_err("MTP chassis sanity check failed\n", level = 0)

        return rc


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
            # in NT, just read the inlet temp
            inlet = self.mtp_get_inlet_temp(low_threshold, high_threshold)
            if inlet == None:
                return False
            self.cli_log_inf("Current Environment temperature is {:2.2f}".format(inlet))
            self.cli_log_inf("No threshold set, bypass ambient temperature check")
            return True

        timeout = MTP_Const.MFG_TEMP_WAIT_TIMEOUT
        while timeout > 0:
            inlet = self.mtp_get_inlet_temp(low_threshold, high_threshold)
            if inlet == None:
                return False
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

        # mtp sensor test, make sure two inlet sensor reading difference is less than 5
        if not self.mtp_inlet_sensor_test():
            self.cli_log_err("MTP temp sensor test failed")
            return False

        return True


    def mtp_wait_soaking(self):
        # Soaking process
        if GLB_CFG_MFG_TEST_MODE:
            timeout = MTP_Const.MFG_TEMP_SOAK_TIMEOUT
        else:
            timeout = MTP_Const.MFG_MODEL_TEMP_SOAK_TIMEOUT
        self.cli_log_inf("Start soaking process, wait for {:d} seconds".format(timeout * MTP_Const.MFG_TEMP_CHECK_INTERVAL))
        libmfg_utils.count_down(timeout * MTP_Const.MFG_TEMP_CHECK_INTERVAL)

        self.cli_log_inf("Soaking process complete")

        return True


    def mtp_cpld_test(self):
        cpld_ver_list = self.mtp_get_hw_version()
        if not cpld_ver_list:
            self.cli_log_err("Unable to retrieve MTP CPLD version")
            self.cli_log_err("MTP CPLD test failed")
            return False
        io_version = MFG_MTP_CPLD_IO_VERSION
        jtag_version = MFG_MTP_CPLD_JTAG_VERSION
        if self._asic_support == MTP_ASIC_SUPPORT.ELBA:
            io_version = MFG_MTP_CPLD_IO_ELBA_VERSION
            jtag_version = MFG_MTP_CPLD_JTAG_ELBA_VERSION

        if int(cpld_ver_list[0],16) < int(io_version,16):
            self.cli_log_err("MTP IO CPLD Version: {:s}, expect: {:s}".format(cpld_ver_list[0], io_version))
            self.cli_log_err("MTP CPLD test failed")
            return False

        if cpld_ver_list[1] != jtag_version:
            self.cli_log_err("MTP JTAG CPLD Version: {:s}, expect: {:s}".format(cpld_ver_list[1], jtag_version))
            self.cli_log_err("MTP CPLD test failed")
            return False
        self.cli_log_inf("MTP CPLD test passed")
        return True


    def mtp_inlet_sensor_test(self):
        cmd = MFG_DIAG_CMDS.MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("MTP Inlet sensor test failed")
            return False

        # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
        # FAN                 23.50          25.50          21.75          21.75
        match = re.search(r"FAN +(-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+)", self.mtp_get_cmd_buf())
        if match:
            # validate the readings
            inlet_1 = float(match.group(3))
            inlet_2 = float(match.group(4))
            inlet_diff = abs(inlet_1 - inlet_2)
            # if the difference is more than 10, something is wrong, relay on any inlet near the threshold
            if inlet_diff > 10.0:
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP Inlet sensor test failed")
                return False
            else:
                self.cli_log_inf("MTP Inlet sensor test passed")
                return True
            return True
        else:
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP Inlet sensor test failed")
            return False


    def mtp_get_inlet_temp(self, low_threshold, high_threshold):
        if self._uut_type == UUT_Type.TOR:
            return self.tor_get_inlet_temp()
        cmd = MFG_DIAG_CMDS.MTP_FAN_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP get inlet temperature failed")
            return None

        # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
        # FAN                 23.50          25.50          21.75          21.75
        match = re.search(r"FAN +(-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+)", self.mtp_get_cmd_buf())
        if match:
            # validate the readings
            inlet_1 = float(match.group(3))
            inlet_2 = float(match.group(4))
            inlet_diff = abs(inlet_1 - inlet_2)
            # if the difference is more than 10, something is wrong, relay on any inlet near the threshold
            if inlet_diff > 10.0:
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
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
            return 25
        else:
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("Unable to get inlet temperature")
            return None

    def tor_get_inlet_temp(self):
        # [INFO]    [2021-08-18-04:55:43.576] TSENSOR-1(.C)   31.437
        # [INFO]    [2021-08-18-04:55:43.577] TSENSOR-2(.C)   36.5
        # [INFO]    [2021-08-18-04:55:43.578] TSENSOR-3(.C)   38.5
        
        temp_readings = { "TSENSOR-1": None, "TSENSOR-2": None, "TSENSOR-3": None }
        for tsensor in temp_readings.keys():
            cmd = "devmgr -dev={:s} -status".format(tsensor)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("{:s} failed".format(cmd))
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                return None
            match = re.search("%s.* (-?\d+.?\d*)" % tsensor, self.mtp_get_cmd_buf())
            if match:
                temp_readings[tsensor] = float(match.group(1))
            else:
                self.cli_log_err("TOR get temperature failed")
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                return None

        return max(temp_readings["TSENSOR-1"], temp_readings["TSENSOR-2"], temp_readings["TSENSOR-3"])

    def mtp_get_fanspd(self):
        """
         Returns the fanspeed (in percent) that had been set by the script.
         Does NOT return live status --> use mtp_get_inlet_temp() for that.
        """
        return self._fanspd

    # return list of error message
    def mtp_mgmt_retrieve_nic_l1_err(self, sn):
        err_msg_list = list()
        pass_count = 0
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR
        logfile_exp = r"(cap|elb)_l1_screen_board_{:s}.*log".format(sn)

        cmd = "ls --color=never {:s}".format(path)
        self.mtp_mgmt_exec_cmd(cmd)
        file_list = self.mtp_get_cmd_buf().split()
        for filename in file_list:
            if re.match(logfile_exp, filename):
                cmd = "grep '{:s}' {:s}".format(MFG_DIAG_SIG.MFG_ASIC_FAIL_MSG_SIG, os.path.join(path,filename))
                self.mtp_mgmt_exec_cmd(cmd)
                cmd_buf = self.mtp_get_cmd_buf()
                if cmd_buf:
                    for line in cmd_buf.splitlines():
                        if cmd in line:
                            # skip first line where command is part of buffer
                            continue
                        if MFG_DIAG_SIG.MFG_ASIC_FAIL_MSG_SIG in line:
                            err_msg = line.replace('\n', '')
                            err_msg_list.append(err_msg)

                cmd = "grep '{:s}' {:s}".format(MFG_DIAG_SIG.MFG_ASIC_PASS_MSG_SIG, os.path.join(path,filename))
                self.mtp_mgmt_exec_cmd(cmd)
                cmd_buf = self.mtp_get_cmd_buf()
                if cmd_buf:
                    for line in cmd_buf.splitlines():
                        if cmd in line:
                            # skip first line where command is part of buffer
                            continue
                        if MFG_DIAG_SIG.MFG_ASIC_PASS_MSG_SIG in line:
                            pass_count += 1

        return pass_count, err_msg_list

    # return list of error message
    def mtp_nic_retrieve_arm_l1_err(self, sn):
        err_msg_list = list()
        pass_count = 0
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR
        logfile_exp = r"{:s}_elba_arm_l1_test\.log".format(sn)

        cmd = "ls --color=never {:s}".format(path)
        self.mtp_mgmt_exec_cmd(cmd)
        file_list = self.mtp_get_cmd_buf().splitlines()
        for filename in file_list:
            if re.match(logfile_exp, filename):
                with open(os.path.join(path, filename), 'r') as f:
                    for line in f:
                        if MFG_DIAG_SIG.MFG_ASIC_FAIL_MSG2_SIG in line:
                            err_msg = line.replace('\n', '')
                            err_msg_list.append(err_msg)
                        if MFG_DIAG_SIG.MFG_ASIC_PASS_MSG2_SIG in line:
                            pass_count += 1

        return pass_count, err_msg_list


    # return list of error message
    def mtp_mgmt_retrieve_mtp_para_err(self, sn, test):
        err_msg_list = list()
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR

        if test == "PRBS_ETH":
            filename = "{:s}_prbs_eth.log".format(sn)
        elif test == "PRBS_PCIE":
            filename = "{:s}_prbs_pcie.log".format(sn)
        elif test == "SNAKE_HBM":
            filename = "{:s}_snake_hbm.log".format(sn)
        elif test == "SNAKE_PCIE":
            filename = "{:s}_snake_pcie.log".format(sn)
        elif test == "SNAKE_ELBA":
            filename = "{:s}_snake_elba.log".format(sn)
        elif test == "SNAKE_TOR":
            # No logfile for SNAKE_TOR
            return err_msg_list
        elif test == "PRBS_TOR":
             # No logfile
             return err_msg_list
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return err_msg_list

        try:
            with open(os.path.join(path, filename), 'r') as f:
                for line in f:
                    if MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG in line:
                        err_msg = line.replace('\n', '')
                        err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG):]
                        err_msg_list.append(err_msg)
        except:
            err_msg_list.append("{:s} doesn't exist".format(filename))

        return err_msg_list


########################################
######  NIC CTRL Routines ##############
########################################

# 1. Routines that need console, can not be run in parallel
    def mtp_nic_boot_info_init(self, slot):
        self.cli_log_slot_inf(slot, "Init NIC boot info")
        if not self._nic_ctrl_list[slot].nic_boot_info_init():
            self.mtp_get_nic_err_msg(slot)
            self.cli_log_slot_err(slot, "Init NIC boot info failed")
            return False

        return True


    def mtp_nic_check_diag_boot(self, slot):
        qspi_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not qspi_info:
            self.cli_log_slot_err_lock(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = qspi_info[0]
        if boot_image != "diagfw" and self._uut_type != UUT_Type.TOR:
            self.cli_log_slot_err_lock(slot, "NIC is booted from {:s}".format(boot_image))
            return False

        return True

    @single_slot_test("DL", "NIC_GOLDFW_VERIFY")
    def mtp_mgmt_verify_nic_gold_boot(self, slot):
        if not self.mtp_nic_boot_info_init(slot):
            self.cli_log_slot_err(slot, "Init NIC gold boot info failed")
            return False

        gold_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not gold_info:
            self.cli_log_slot_err(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = gold_info[0]
        kernel_timestamp = gold_info[1]

        nic_type = self.mtp_get_nic_type(slot)

        try:
            expected_timestamp = NIC_IMAGES.goldfw_dat[nic_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing goldfw timestamp for {:s}".format(nic_type))
            return False

        if ( boot_image != "goldfw" ):
            self.cli_log_slot_err_lock(slot, "goldfw Boot check failed, NIC is booted from {:s}".format(boot_image))
            return False

        if self._uut_type != UUT_Type.TOR:
            if ( expected_timestamp != kernel_timestamp ):
                self.cli_log_slot_err_lock(slot, "goldfw Verify Failed, Expect: {:s}   Read: {:s}".format(expected_timestamp, kernel_timestamp))
                return False

        self.cli_log_slot_inf(slot, "NIC boot from {:s}({:s})".format(boot_image, kernel_timestamp))
        return True


    def mtp_mgmt_verify_nic_sw_boot(self, slot):
        if not self.mtp_nic_boot_info_init(slot):
            self.cli_log_slot_err(slot, "Init NIC sw boot info failed")
            return False

        sw_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not sw_info:
            self.cli_log_slot_err(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = sw_info[0]
        kernel_timestamp = sw_info[1]
        if boot_image not in ["mainfwa", "mainfwb"]:
            self.cli_log_slot_err(slot, "SW boot failed, NIC is booted from {:s}".format(boot_image))
            return False

        self.cli_log_slot_inf(slot, "NIC default boot from {:s}({:s})".format(boot_image, kernel_timestamp))
        return True

    def mtp_nic_sw_mode_switch(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_mode_switch():
            err_msg = self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_err_msg(err_msg)
            return False
        return True

    def mtp_nic_sw_mode_switch_verify(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_mode_switch_verify():
            err_msg = self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_err_msg(err_msg)
            return False
        return True

    def mtp_nic_sw_profile(self, slot, profile):
        return self._nic_ctrl_list[slot].nic_sw_profile(profile)


    def mtp_nic_mgmt_reinit(self, slot):
        loop = 0
        while loop < MTP_Const.NIC_MGMT_IP_INIT_RETRY:
            loop += 1
            time.sleep(MTP_Const.NIC_MGMT_IP_SET_DELAY)
            self.cli_log_slot_inf(slot, "Reinit NIC MGMT port <{:d}> try".format(loop))
            if self._nic_ctrl_list[slot].nic_mgmt_config():
                self.mtp_get_nic_err_msg(slot)
                break
            time.sleep(10)
        if loop >= MTP_Const.NIC_MGMT_IP_INIT_RETRY:
            return False

        return True


    def mtp_nic_mgmt_init(self, slot, fpo):
        self.cli_log_slot_inf(slot, "Init NIC MGMT port")
        if not self._nic_ctrl_list[slot].nic_mgmt_init(fpo):
            # retry
            if not self.mtp_nic_mgmt_reinit(slot):
                self.cli_log_slot_err(slot, "Init NIC MGMT port failed")
                return False

        # delete the arp entry
        ipaddr = libmfg_utils.get_nic_ip_addr(slot)
        cmd = MFG_DIAG_CMDS.MTP_ARP_DELET_FMT.format(ipaddr)
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            return False
        # ping to update the arp cache
        for x in range(2):
            time.sleep(5)
            cmd = MFG_DIAG_CMDS.MTP_NIC_PING_FMT.format(ipaddr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                return False

        return True


    def mtp_nic_mini_init(self, slot, fpo=False):
        if not self.mtp_nic_boot_info_init(slot):
            return False

        if not self.mtp_nic_mgmt_init(slot, fpo):
            return False

        return True


    def mtp_mgmt_test_nic_mem(self, slot):
        if not self._nic_ctrl_list[slot].nic_test_mem():
            return False
        else:
            return True

    def mtp_check_nic_jtag(self, slot):
        if not self._nic_ctrl_list[slot].nic_check_jtag(self._asic_support):
            return False
        else:
            return True

# 2. Routines that need smb bus, can not be run in parallel
    def mtp_mgmt_check_nic_pwr_status(self, slot):
        if not self._nic_ctrl_list[slot].nic_power_check():
            err_msg = self._nic_ctrl_list[slot].nic_get_cmd_buf()
            self.mtp_dump_err_msg(err_msg)
            return False

        return True


    def mtp_mgmt_dump_nic_pll_sta(self, slot):
        reg_data_list = self._nic_ctrl_list[slot].nic_get_pll_sta()
        if not reg_data_list:
            self.cli_log_slot_err(slot, "Failed to extract ASIC PLL status")
            self.cli_log_err(self._nic_ctrl_list[slot].nic_get_cmd_buf())
            return

        reg26_data = reg_data_list[0]
        self.cli_log_slot_inf(slot, "CPLD 0x26 = {:x}".format(reg26_data))
        core_pll_lock = reg26_data & 0x1
        cpu_pll_lock = reg26_data & 0x2
        flash_pll_lock = reg26_data & 0x4
        proto_mode = reg26_data & 0x20
        if not core_pll_lock:
            self.cli_log_slot_err(slot, "ASIC core pll is not locked")
        if not cpu_pll_lock:
            self.cli_log_slot_err(slot, "ASIC cpu pll is not locked")
        if not flash_pll_lock:
            self.cli_log_slot_err(slot, "ASIC flash pll is not locked")
        if proto_mode:
            self.cli_log_slot_err(slot, "ASIC proto mode is set")

        reg28_data = reg_data_list[1]
        self.cli_log_slot_inf(slot, "CPLD 0x28 = {:x}".format(reg28_data))
        pcie_pll_lock = reg28_data & 0x40
        if not pcie_pll_lock:
            self.cli_log_slot_err(slot, "ASIC pcie pll is not locked")
        if not (core_pll_lock or cpu_pll_lock or flash_pll_lock or pcie_pll_lock):
            # print some more debug info
            self.mtp_mgmt_set_nic_avs_post(slot)


# 3. Routines that need spi bus, can not be run in parallel
    def mtp_power_on_single_nic(self, slot):
        self.cli_log_slot_inf(slot, "Power on NIC, wait {:02d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY))
        if not self._nic_ctrl_list[slot].nic_power_on():
            self.cli_log_slot_err(slot, "Failed to power on NIC")
            return False

        return True


    def mtp_power_off_single_nic(self, slot):
        self.cli_log_slot_inf(slot, "Power off NIC, wait {:02d} seconds for NIC power down".format(MTP_Const.NIC_POWER_OFF_DELAY))
        if not self._nic_ctrl_list[slot].nic_power_off():
            self.cli_log_slot_err(slot, "Failed to power off NIC")
            return False
        return True


# 4. Routines use mgmt port, can be run in parallel
    def mtp_mgmt_exec_cmd_para(self, slot, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        rc = self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout)
        if not rc:
            self.mtp_get_nic_err_msg(slot)
        return rc


    def mtp_get_nic_cmd_buf(self, slot):
        return self._nic_ctrl_list[slot].nic_get_cmd_buf()


    def mtp_get_nic_err_msg(self, slot):
        err_msg_str = self._nic_ctrl_list[slot].nic_get_err_msg()
        if err_msg_str:
            err_msg_list = err_msg_str.splitlines()
            for err_msg in err_msg_list:
                if err_msg:
                    self.cli_log_slot_err(slot, err_msg)
        return

    def mtp_clear_nic_err_msg(self, slot):
        return self._nic_ctrl_list[slot].nic_get_err_msg()


    def mtp_program_nic_fru(self, slot, date, sn, mac, pn):
        nic_type = self.mtp_get_nic_type(slot)
        self.cli_log_slot_inf_lock(slot, "Program NIC FRU date={:s}, sn={:s}, mac={:s}, pn={:s}".format(date, sn, mac, pn))
        if not self._nic_ctrl_list[slot].nic_program_fru(date, sn, mac, pn, nic_type):
            self.cli_log_slot_err_lock(slot, "Program NIC FRU failed")
            return False
        if self._nic_ctrl_list[slot].nic_2nd_fru_exist(pn):
            if not self._nic_ctrl_list[slot].nic_disp_2nd_fru():
                self.cli_log_slot_err_lock(slot, "Display SMB NIC FRU failed")
                return False
        if not self._nic_ctrl_list[slot].nic_disp_fru():
            self.cli_log_slot_err_lock(slot, "Display NIC FRU failed")
            return False
        return True

    def mtp_program_nic_alom_fru(self, slot, date, alom_sn, alom_pn):
        self.cli_log_slot_inf_lock(slot, "Program NIC ALOM FRU date={:s}, alom_sn={:s}, alom_pn={:s}".format(date, alom_sn, alom_pn))
        if not self._nic_ctrl_list[slot].nic_program_alom_fru(date, alom_sn, alom_pn):
            self.cli_log_slot_err_lock(slot, "Program NIC ALOM FRU failed")
            return False
        return True

    def mtp_dump_nic_fru(self, slot, expect_sn="", expect_mac="", expect_pn=""):
        if not self._nic_ctrl_list[slot].nic_dump_fru(expect_mac=expect_mac):
            self.cli_log_slot_err_lock(slot, "Dump ASIC FRU failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        if not self._nic_ctrl_list[slot].mtp_nic_dump_fru(expect_mac=expect_mac):
            self.cli_log_slot_err_lock(slot, "Dump SMB FRU failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        return True

    def mtp_get_nic_fru(self, slot):
        return self._nic_ctrl_list[slot].nic_get_fru()

    def mtp_get_nic_alom_fru(self, slot):
        return self._nic_ctrl_list[slot].nic_alom_get_fru()
        
    def mtp_get_nic_alom_sn(self, slot):
        return self._nic_ctrl_list[slot].nic_alom_sn_get_fru()

    def mtp_verify_nic_fru(self, slot, sn, mac, pn, date):
        nic_fru_info = self._nic_ctrl_list[slot].nic_get_fru()
        if not nic_fru_info:
            self.cli_log_slot_err_lock(slot, "Verify NIC FRU Failed, can not retrieve FRU content")
            return False

        nic_sn = nic_fru_info[0]
        nic_mac = nic_fru_info[1]
        nic_pn = nic_fru_info[2]
        nic_date = nic_fru_info[3]
        nic_type = self.mtp_get_nic_type(slot)
        if nic_sn != sn:
            self.cli_log_slot_err_lock(slot, "SN Verify Failed, get '{:s}', expect {:s}".format(nic_sn, sn))
            return False
        if nic_mac != mac:
            self.cli_log_slot_err_lock(slot, "MAC Verify Failed, get {:s}, expect {:s}".format(nic_mac, mac))
            return False
        if nic_pn != pn:
            self.cli_log_slot_err_lock(slot, "PN Verify Failed, get {:s}, expect {:s}".format(nic_pn, pn))
            return False
        if nic_date != date:
            self.cli_log_slot_err_lock(slot, "Date Verify Failed, get {:s}, expect {:s}".format(nic_date, date))
            return False
        self.cli_log_slot_inf_lock(slot, "Verify NIC FRU Pass, sn={:s}, mac={:s}, pn={:s}, date={:s}".format(sn, mac, pn, date))

        return True
    def mtp_verify_hpe_pn_fru(self, slot, hpe_pn):
    
        fru_pn = self._nic_ctrl_list[slot].get_nic_fru_hpe_pn()

        if fru_pn != hpe_pn:
            self.cli_log_slot_err_lock(slot, "HPE PN Verify Failed expect {:s}".format(hpe_pn))
            return False
        self.cli_log_slot_inf_lock(slot, "Verify HPE PN FRU Pass, PN={:s}".format(hpe_pn))

        return True
        
    def mtp_verify_nic_alom_fru(self, slot, alom_sn, alom_pn, date):
    
        fru_buf = self._nic_ctrl_list[slot].mtp_read_alom_fru(slot)

        if not fru_buf:
            self.nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)
            return False

        # retrieve card serial number
        
        newdate = date[0] + date[1] + '/' + date[2] + date[3] + '/' + date[4] + date[5]
            
        if not re.findall(alom_sn, fru_buf):
            self.cli_log_slot_err_lock(slot, "ALOM SN Verify Failed expect {:s}".format(alom_sn))
            return False
        if not re.findall(alom_pn, fru_buf):
            self.cli_log_slot_err_lock(slot, "ALOM PN Verify Failed expect {:s}".format(alom_pn))
            return False
        if not re.findall(newdate, fru_buf):           
            self.cli_log_slot_err_lock(slot, "Date Verify Failed expect {:s}".format(newdate))
            return False
        self.cli_log_slot_inf_lock(slot, "Verify NIC ALOM FRU Pass, sn={:s}, pn={:s}, date={:s}".format(alom_sn, alom_pn, date))

        return True

    def mtp_verify_nic_assettag(self, slot, exp_assettag):
    
        assettag = self._nic_ctrl_list[slot].nic_get_assettag()
        if not assettag:
            self.cli_log_slot_err_lock(slot, "Verify NIC assettag Failed, can not retrieve assettag content")
            return False

        if assettag != exp_assettag:
            self.cli_log_slot_err_lock(slot, "assettag Verify Failed, get {:s}, expect {:s}".format(assettag, exp_assettag))
        self.cli_log_slot_inf_lock(slot, "Verify NIC assettag FRU Pass, assettag={:s}".format(assettag))
        return True

    def mtp_reverse_lookup_naples_pn(self, slot):
        """
         Get NIC type from PN
        """
        naples_pn = self._nic_ctrl_list[slot].nic_get_naples_pn()
        
        if not naples_pn:
            self.cli_log_slot_err_lock(slot, "Verify NIC:  Retreive PN Failed")
            return False

        if re.match(PART_NUMBERS_MATCH.N100_PN_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES100

        elif re.match(PART_NUMBERS_MATCH.N100_IBM_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES100IBM

        elif re.match(PART_NUMBERS_MATCH.N100_HPE_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES100HPE

        elif re.match(PART_NUMBERS_MATCH.N25_PN_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES25

        elif re.match(PART_NUMBERS_MATCH.N25_SWM_HPE_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES25SWM

        elif re.match(PART_NUMBERS_MATCH.N25_SWM_DEL_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES25SWMDELL

        elif re.match(PART_NUMBERS_MATCH.N25_SWM_833_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES25SWM833

        elif re.match(PART_NUMBERS_MATCH.N25_OCP_PN_FMT_ALL, naples_pn):
            nic_type = NIC_Type.NAPLES25OCP

        elif re.match(PART_NUMBERS_MATCH.FORIO_FMT_ALL, naples_pn):
            nic_type = NIC_Type.FORIO

        elif re.match(PART_NUMBERS_MATCH.VOMERO_FMT_ALL, naples_pn):
            nic_type = NIC_Type.VOMERO

        elif re.match(PART_NUMBERS_MATCH.VOMERO2_FMT_ALL, naples_pn):
            nic_type = NIC_Type.VOMERO2

        elif re.match(PART_NUMBERS_MATCH.ORTANO_FMT_ALL, naples_pn):
            nic_type = NIC_Type.ORTANO

        elif re.match(PART_NUMBERS_MATCH.ORTANO2_FMT_ALL, naples_pn):
            nic_type = NIC_Type.ORTANO2

        else:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type for PN {:s}".format(naples_pn))
            return False

        self.mtp_set_nic_type(slot, nic_type)
        return True

    def mtp_verify_naples_pn(self, slot):
        naples_pn = self._nic_ctrl_list[slot].nic_get_naples_pn()
        
        if not naples_pn:
            self.cli_log_slot_err_lock(slot, "Verify NIC:  Retreive PN Failed")
            return False

        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES100:
            exp_pn = PART_NUMBERS_MATCH.N100_PN_FMT_ALL
        elif nic_type == NIC_Type.NAPLES100IBM:
            exp_pn = PART_NUMBERS_MATCH.N100_IBM_FMT_ALL
        elif nic_type == NIC_Type.NAPLES100HPE:
            exp_pn = PART_NUMBERS_MATCH.N100_HPE_FMT_ALL
        elif nic_type == NIC_Type.NAPLES25:
            exp_pn = PART_NUMBERS_MATCH.N25_PN_FMT_ALL
        elif nic_type == NIC_Type.NAPLES25SWM:
            exp_pn = PART_NUMBERS_MATCH.N25_SWM_HPE_FMT_ALL
        elif nic_type == NIC_Type.NAPLES25SWMDELL:
            exp_pn = PART_NUMBERS_MATCH.N25_SWM_DEL_FMT_ALL
        elif nic_type == NIC_Type.NAPLES25SWM833:
            exp_pn = PART_NUMBERS_MATCH.N25_SWM_833_FMT_ALL
        elif nic_type == NIC_Type.NAPLES25OCP:
            exp_pn = PART_NUMBERS_MATCH.N25_OCP_PN_FMT_ALL
        elif nic_type == NIC_Type.FORIO:
            exp_pn = PART_NUMBERS_MATCH.FORIO_FMT_ALL
        elif nic_type == NIC_Type.VOMERO:
            exp_pn = PART_NUMBERS_MATCH.VOMERO_FMT_ALL
        elif nic_type == NIC_Type.VOMERO2:
            exp_pn = PART_NUMBERS_MATCH.VOMERO2_FMT_ALL
        elif nic_type == NIC_Type.ORTANO:
            exp_pn = PART_NUMBERS_MATCH.ORTANO_FMT_ALL
        elif nic_type == NIC_Type.ORTANO2:
            exp_pn = PART_NUMBERS_MATCH.ORTANO2_FMT_ALL
        else:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
            return False

        match = re.findall(exp_pn, naples_pn)
        if match:
            self.cli_log_slot_inf_lock(slot, "==> Verify Naples_PN Pass, naples_pn={:s}".format(naples_pn))
            return True
        else:
            self.cli_log_slot_err_lock(slot, "NAPLES_PN Verify Failed, Read {:s}".format(naples_pn))
            return False


    #Check the SWI scanned in software part number to see if it's a cloud image or not.
    #Cloud images have slight deviation on how SWI runs
    def check_is_cloud_software_image(self, slot, software_pn):
        print(" Check if software image is cloud: {:s}".format(software_pn))            
        if ((software_pn == "90-0004-0001") or (software_pn == "90-0006-0001") or (software_pn == "90-0006-0002") or (software_pn == "90-0011-0001")):
            return True
        return False

    def mtp_get_alom_fru(self, slot):
        return self._nic_ctrl_list[slot].alom_get_fru()

    def mtp_setting_partition(self, slot):
        # copy script to detect the emmc part size
        if not self._nic_ctrl_list[slot].nic_copy_image("{:s}diag/scripts/emmc_format.sh".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)):
            self.cli_log_slot_err_lock(slot, "Could not copy emmc_format.sh")
            return False
        # Run command twice: first time does it, 2nd time says 'already partitioned'
        if not self._nic_ctrl_list[slot].nic_setting_partition():
            self.cli_log_slot_err_lock(slot, "Could not complete partition command")
            return False
        if not self._nic_ctrl_list[slot].nic_setting_partition(): 
            self.cli_log_slot_err_lock(slot, "Partition table was not updated")
            return False
        self.cli_log_slot_inf_lock(slot, "Partition table updated")
        return True

    def mtp_nic_partition_check(self, slot):
        if not self._nic_ctrl_list[slot].nic_verify_partition():
            self.cli_log_slot_err_lock(slot, "PSLC Verify failed")
            return False
        self.cli_log_slot_inf_lock(slot, "Verify PSCL Pass")
        return True

    @single_slot_test("DL", "NIC_EMMC_FORMAT")
    def tor_nic_emmc_format(self, slot):
        return self.mtp_setting_partition(slot)

    @single_slot_test("DL", "EMMC_BKOPS_EN")
    def tor_nic_emmc_bkops_en(self, slot):
        # copy script to detect the emmc part size
        if not self._nic_ctrl_list[slot].nic_copy_image("{:s}nic_util/mmc.latest".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH)):
            self.cli_log_slot_err_lock(slot, "Failed to copy emmc util")
            return False
        if not self._nic_ctrl_list[slot].nic_emmc_bkops_verify():
            self.mtp_clear_nic_err_msg(slot)
            if not self._nic_ctrl_list[slot].nic_emmc_bkops_en(): 
                self.cli_log_slot_err_lock(slot, "Failed to enable eMMC bkops")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_emmc_bkops_verify():
                self.cli_log_slot_err_lock(slot, "Incorrect eMMC bkops value reflected")
                self.mtp_get_nic_err_msg(slot)
                return False
        return True

    @single_slot_test("DL", "EMMC_HWRESET_SET")
    def tor_nic_emmc_hwreset_set(self, slot):
        if not self._nic_ctrl_list[slot].nic_emmc_hwreset_verify():
            self.mtp_clear_nic_err_msg(slot)
            if not self._nic_ctrl_list[slot].nic_emmc_hwreset_set(): 
                self.cli_log_slot_err_lock(slot, "Failed to enable eMMC hwreset setting")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_emmc_hwreset_verify():
                self.cli_log_slot_err_lock(slot, "Incorrect eMMC hwreset setting reflected")
                self.mtp_get_nic_err_msg(slot)
                return False
        return True


    def mtp_program_nic_cpld(self, slot, cpld_img):
        # check the current cpld version
        cpld_has_timestamp = 1
        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed, can not retrieve CPLD info")
            return False
        cur_ver = nic_cpld_info[0]
        cur_timestamp = nic_cpld_info[1]
        nic_type = self.mtp_get_nic_type(slot)
        try:
            expected_version = NIC_IMAGES.cpld_ver[nic_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD version for {:s}".format(nic_type))
            return False
        try:
            expected_timestamp = NIC_IMAGES.cpld_dat[nic_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD timestamp for {:s}".format(nic_type))
            return False

        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip CPLD update for Proto NIC")
            return True

        if cur_ver == expected_version and cur_timestamp == expected_timestamp:
            self.cli_log_slot_inf_lock(slot, "NIC CPLD is up-do-date")
            return True

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
            return False

        return True

    def mtp_program_nic_failsafe_cpld(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if not nic_type == NIC_Type.ORTANO and not nic_type == NIC_Type.ORTANO2:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no failsafe CPLD for {:s}".format(nic_type))
            return False
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip failsafe CPLD update for Proto NIC")
            return True

        # can't check the version without loading backup partition into the running partition
        self.cli_log_slot_inf(slot, "Skip checking failsafe CPLD version")

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "cfg1"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
            return False

        return True

    def mtp_program_nic_cpld_feature_row(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if not nic_type == NIC_Type.ORTANO2 and not nic_type == NIC_Type.TAORMINA:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no feature row for {:s}".format(nic_type))
            return False
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "No feature row update for Proto NIC")
            return True

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "fea"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD feature row failed")
            return False

        return True

    def mtp_refresh_nic_cpld(self, slot, dontwait=False):
        if not self._nic_ctrl_list[slot].nic_refresh_cpld(dontwait):
            self.cli_log_slot_err_lock(slot, "Refresh NIC CPLD failed")
            return False

        return True

    def mtp_program_nic_sec_cpld(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in self._valid_type_list:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
            return False

        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Secure CPLD program for Proto NIC")
            return True

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img):
            self.cli_log_slot_err_lock(slot, "Program NIC Secure CPLD failed")
            return False

        return True


    def mtp_verify_nic_sec_cpld(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Secure CPLD verify for Proto NIC")
            return True

        if not self._nic_ctrl_list[slot].nic_verify_sec_cpld():
            self.cli_log_slot_err(slot, "Verify NIC Secure CPLD failed")
            return False

        return True

    def mtp_verify_nic_cpld_fea(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if not nic_type == NIC_Type.ORTANO2 and not nic_type == NIC_Type.TAORMINA:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no feature row for {:s}".format(nic_type))
            return False

        fea_regex = r"00000000  (.*)  \|.*\|" #first 16 bytes

        cmd = "hexdump -C /home/diag/"+NIC_IMAGES.fea_cpld_img[nic_type]
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False
        fea_mtp_hex = self.mtp_get_cmd_buf()
        fea_mtp_match = re.search(fea_regex, fea_mtp_hex)

        if not self._nic_ctrl_list[slot].nic_dump_cpld("fea"):
            self.mtp_get_nic_err_msg(slot)
            return False
        
        fea_nic_hex = self._nic_ctrl_list[slot].nic_get_info("hexdump -C /home/diag/cplddump")
        if not fea_nic_hex:
            self.mtp_get_nic_err_msg(slot)
            return False
        fea_nic_match = re.search(fea_regex,fea_nic_hex)

        if fea_mtp_match and fea_nic_match:
            if fea_mtp_match.group(1) == fea_nic_match.group(1):
                return True
            self.cli_log_slot_err_lock(slot, "Feature row programmed incorrectly. Dump doesn't match original file.")
            return False
        self.cli_log_slot_err_lock(slot, "Unable to dump feature row.")
        return False

    def mtp_check_nic_cpld_partition(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if not nic_type == NIC_Type.ORTANO2:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no cpld partition for {:s}".format(nic_type))
            return False

        if not self._nic_ctrl_list[slot].nic_check_cpld_partition():
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_efuse(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type != NIC_Type.ORTANO2:
            return False

        if not self._nic_ctrl_list[slot].nic_program_efuse():
            self.cli_log_slot_err(slot, "Program NIC Efuse failed")
            self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        self._nic_ctrl_list[slot].nic_program_sec_key_dump()
        return True

    def mtp_program_nic_sec_key(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Secure Key program for Proto NIC")
            return True

        if not self._nic_ctrl_list[slot].nic_program_sec_key_pre():
            self.cli_log_slot_err(slot, "Pre init key programming failed")
            self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        if not self._nic_ctrl_list[slot].nic_program_sec_key(self._id):
            self.cli_log_slot_err(slot, "Program NIC Secure Key failed")
            self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        if not self._nic_ctrl_list[slot].nic_program_sec_key_post():
            self.cli_log_slot_err(slot, "Post cleanup key programming failed")
            self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        self._nic_ctrl_list[slot].nic_program_sec_key_dump()
        return True

    def mtp_verify_nic_cpld(self, slot, sec_cpld=False):
        cpld_has_timestamp = 1
        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Verify NIC CPLD failed, can not retrieve CPLD info")
            return False

        cur_ver = nic_cpld_info[0]
        cur_timestamp = nic_cpld_info[1]
        nic_type = self.mtp_get_nic_type(slot)

        try:
            expected_version = NIC_IMAGES.cpld_ver[nic_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD version for {:s}".format(nic_type))
            return False
        try:
            expected_timestamp = NIC_IMAGES.cpld_dat[nic_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD timestamp for {:s}".format(nic_type))
            return False
        if sec_cpld:
            try:
                expected_version = NIC_IMAGES.sec_cpld_ver[nic_type]
            except KeyError:
                self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD version for {:s}".format(nic_type))
                return False
            try:
                expected_timestamp = NIC_IMAGES.sec_cpld_dat[nic_type]
            except KeyError:
                self.cli_log_slot_err_lock(slot, "mfg_cfg is missing CPLD timestamp for {:s}".format(nic_type))
                return False

        if cur_ver != expected_version or cur_timestamp != expected_timestamp:
                self.cli_log_slot_err_lock(slot, "Verify NIC CPLD Failed")
                self.cli_log_slot_err_lock(slot, "Expect Version: {:s}, get: {:s}".format(expected_version, cur_ver))
                self.cli_log_slot_err_lock(slot, "Expect Timestamp: {:s}, get: {:s}".format(expected_timestamp, cur_timestamp))
                return False

        return True

    def mtp_program_nic_qspi(self, slot, qspi_img):
        if not self._nic_ctrl_list[slot].nic_program_qspi(qspi_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC QSPI failed")
            self.mtp_get_nic_err_msg(slot)
            return False
        return True
        
    def mtp_copy_nic_gold(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_copy_gold(gold_img):
            self.cli_log_slot_inf_lock(slot, "Copy NIC goldfw failed")
            return False
            
        return True

    def mtp_program_nic_gold(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_program_gold(gold_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC goldfw failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        if not self.mtp_mgmt_set_nic_gold_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True
    def mtp_program_nic_gold_naples100(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_program_gold_naples100(gold_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC goldfw failed")
            return False

        if not self.mtp_mgmt_set_nic_gold_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True


    def mtp_verify_nic_qspi(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        qspi_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not qspi_info:
            self.cli_log_slot_err_lock(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = qspi_info[0]
        kernel_timestamp = qspi_info[1]
        nic_type = self.mtp_get_nic_type(slot)

        try:
            expected_timestamp = NIC_IMAGES.diagfw_dat[nic_type]
        except KeyError:
            self.cli_log_slot_err_lock(slot, "mfg_cfg is missing diagfw timestamp for {:s}".format(nic_type))
            return False

        if ( boot_image != "diagfw" ):
            self.cli_log_slot_err_lock(slot, "Checking Boot Image is Diagfw Failed, NIC is booted from {:s}".format(boot_image))
            return False

        if ( expected_timestamp != kernel_timestamp ):
            self.cli_log_slot_err_lock(slot, "Diagfw Verify Failed, Expect: {:s}   Read: {:s}".format(expected_timestamp, kernel_timestamp))
            return False

        return True

    def mtp_copy_nic_emmc(self, slot, emmc_img):
        if not self._nic_ctrl_list[slot].nic_copy_emmc(emmc_img):
            self.cli_log_slot_err_lock(slot, "Program NIC EMMC failed")
            return False
            
        return True
        
    def mtp_set_nic_sw_boot(self, slot, emmc_img):

        if not self.mtp_mgmt_set_nic_sw_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True

    def mtp_program_nic_emmc(self, slot, emmc_img):
        if not self._nic_ctrl_list[slot].nic_program_emmc(emmc_img):
            self.cli_log_slot_err_lock(slot, "Program NIC EMMC failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True
        
    def mtp_program_nic_emmc_ibm(self, slot, emmc_img):
        if not self._nic_ctrl_list[slot].nic_program_emmc_ibm(emmc_img):
            self.cli_log_slot_err_lock(slot, "Program NIC EMMC failed")
            self.mtp_dump_err_msg(self.mtp_get_nic_err_msg(slot))
            return False

        if not self.mtp_mgmt_set_nic_sw_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True
    def mtp_program_nic_emmc_naples100(self, slot, emmc_img):
        if not self._nic_ctrl_list[slot].nic_program_emmc_naples100(emmc_img):
            self.cli_log_slot_err_lock(slot, "Program NIC EMMC failed")
            self.mtp_dump_err_msg(self.mtp_get_nic_err_msg(slot))
            return False
        return True


#    def mtp_program_single_nic_emmc(self, slot, emmc_img, nic_rslt_list):
#        self.cli_log_slot_inf_lock(slot, "Program NIC EMMC")
#        if not self._nic_ctrl_list[slot].nic_program_emmc(emmc_img):
#            self.cli_log_slot_inf_lock(slot, "Program NIC EMMC failed")
#            return
#
#        if not self.mtp_mgmt_set_nic_sw_boot(slot):
#            return
#
#        self.cli_log_slot_inf_lock(slot, "Program NIC EMMC complete")
#        nic_rslt_list[slot] = True
#        return
#
#
#    def mtp_program_nic_emmc(self, nic_list, emmc_img):
#        fail_list = list()
#        nic_thread_list = list()
#        nic_rslt_list = [False] * self._slots
#
#        for slot in nic_list:
#            nic_thread = threading.Thread(target = self.mtp_program_single_nic_emmc,
#                                          args = (slot, emmc_img, nic_rslt_list))
#            nic_thread.daemon = True
#            nic_thread.start()
#            nic_thread_list.append(nic_thread)
#
#        while True:
#            if len(nic_thread_list) == 0:
#                break
#            for nic_thread in nic_thread_list[:]:
#                if not nic_thread.is_alive():
#                    ret = nic_thread.join()
#                    nic_thread_list.remove(nic_thread)
#            time.sleep(5)
#
#        for slot in nic_list:
#            if not nic_rslt_list[slot]:
#                fail_list.append(slot)
#
#        return fail_list


    def mtp_mgmt_copy_nic_diag(self, slot, nic_utils=False):
        if nic_utils:
            msg = "Copy NIC Diag/Utils Image"
        else:
            msg = "Copy NIC Diag Image"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_copy_diag_img(nic_utils):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True


    def mtp_mgmt_save_nic_logfile(self, slot, logfile_list):
        if not self._nic_ctrl_list[slot].nic_save_logfile(logfile_list):
            self.cli_log_slot_err_lock(slot, "Save NIC Logfile failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        return True


    def mtp_mgmt_save_nic_diag_logfile(self, slot, aapl):
        if not self._nic_ctrl_list[slot].nic_save_diag_logfile(aapl):
            self.cli_log_slot_err_lock(slot, "Save NIC Diag Logfile failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        return True
    def mtp_mgmt_nic_diag_sys_clean(self, slot):
        self.cli_log_slot_inf_lock(slot, "NIC Diag Sys Clean")
        if not self._nic_ctrl_list[slot].nic_diag_clean():
            self.cli_log_slot_err_lock(slot, "NIC Diag Sys Clean failed")
            self.mtp_dump_err_msg(self._nic_ctrl_list[slot].nic_get_err_msg())
            return False

        return True

    def mtp_mgmt_killall_tclsh_picocom(self):
        cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False
        cmd = MFG_DIAG_CMDS.NIC_DIAG_STOP_PICOCOM_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False
        return True

    def mtp_mgmt_start_nic_diag(self, slot, aapl):
        if aapl:
            msg = "Start NIC Diag with HAL"
        else:
            msg = "Start NIC Diag without HAL"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_start_diag(aapl):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            return False

        return True


    def mtp_set_nic_vmarg(self, slot, vmarg):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Vmargin for Proto NIC")
            return True

        if vmarg > 0:
            vmarg_param = "high"
        elif vmarg == 0:
            vmarg_param = "normal"
        else:
            vmarg_param = "low"
        self.cli_log_slot_inf_lock(slot, "Set voltage margin to {:s}".format(vmarg_param))

        if not self._nic_ctrl_list[slot].nic_set_vmarg(vmarg_param):
            self.cli_log_slot_err_lock(slot, "Set voltage margin to {:s} failed".format(vmarg_param))
            return False

        return True

    def mtp_nic_display_voltage(self, slot):
        if not self._nic_ctrl_list[slot].nic_display_voltage():
            self.cli_log_slot_err_lock(slot, "Voltage display failed")
            return False

        return True

    def mtp_nic_emmc_init(self, slot, emmc_format=False):
        nic_type = self.mtp_get_nic_type(slot)
        if emmc_format:
            msg = "Format and Init NIC EMMC"
        else:
            msg = "Init NIC EMMC"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_init_emmc(emmc_format):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            return False

        if emmc_format:
            if not self.mtp_nic_emmc_set_perf_mode(slot):
                return False
        else:
            if not self.mtp_nic_emmc_check_perf_mode(slot):
                return False

        return True

    def mtp_nic_emmc_set_perf_mode(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
            msg = "Set NIC in performance mode"
            if not self._nic_ctrl_list[slot].nic_emmc_set_perf_mode():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
                err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
                self.mtp_dump_err_msg(err_msg)
                return False
            self.cli_log_slot_inf_lock(slot, msg)
        return True

    def mtp_nic_emmc_check_perf_mode(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
            msg = "NIC in performance mode"
            if not self._nic_ctrl_list[slot].nic_emmc_check_perf_mode():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
                err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
                self.mtp_dump_err_msg(err_msg)
                return False
            self.cli_log_slot_inf_lock(slot, msg)
        return True

    def mtp_nic_fru_init(self, slot, init_date=True, nic_type=None):
        if init_date:
            msg = "Init NIC FRU info with date"
        else:
            msg = "Init NIC FRU info without date"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_fru_init(init_date, self._swmtestmode[slot]):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.mtp_get_nic_err_msg(slot)
            return False

        return True


    def mtp_nic_cpld_init(self, slot):
        self.cli_log_slot_inf_lock(slot, "Init NIC CPLD info")
        if not self._nic_ctrl_list[slot].nic_cpld_init():
            self.cli_log_slot_err_lock(slot, "Init NIC CPLD failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True


    def mtp_mgmt_set_nic_sw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_sw_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default sw boot")
        return True


    def mtp_mgmt_set_nic_gold_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_gold_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default gold boot failed")
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default gold boot")
        return True

            
    def mtp_mgmt_set_nic_goldfw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_goldfw_boot():
            self.cli_log_err(self._nic_ctrl_list[slot].nic_get_err_msg())
            self.cli_log_slot_err_lock(slot, "Set NIC default gold boot failed")
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default gold boot")
        return True
    def mtp_nic_load_scan_fru(self, nic_fru_cfg=None):
        self.cli_log_inf("Load NIC FRU config")
        if not nic_fru_cfg:
            nic_fru_cfg_file = "config/{:s}.yaml".format(self._id)
            self.cli_log_inf("Load from config file: {:s}".format(nic_fru_cfg_file))
            nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(nic_fru_cfg_file)

        for slot in range(self._slots):
            key = libmfg_utils.nic_key(slot)
            valid = nic_fru_cfg[key]["VALID"]
            if str.upper(valid) == "YES":
                sn = nic_fru_cfg[key]["SN"]
                self.mtp_set_nic_scan_sn(slot, sn)
        self.cli_log_inf("Load NIC FRU config complete\n")
        return True


    def mtp_nic_info_disp(self, fru_valid=True):
        self.cli_log_inf("MTP NIC Info Dump:")
        for slot, prsnt, nic_type in zip(range(self._slots), self._nic_prsnt_list, self._nic_type_list):
            if prsnt:
                self.cli_log_slot_inf(slot, "NIC is Present, Type is: {:s}".format(nic_type))
                if fru_valid:
                    fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
                    if not fru_info_list:
                        self.cli_log_slot_err_lock(slot, "Retrieve NIC FRU failed")
                    else:
                        self.cli_log_slot_inf(slot, "==> Manufacture Vendor: {:s}".format(fru_info_list[4]))
                        self.cli_log_slot_inf(slot, "==> FRU: {:s}, {:s}, {:s}".format(fru_info_list[0],fru_info_list[1],fru_info_list[2]))
                        if fru_info_list[3]:
                            self.cli_log_slot_inf(slot, "==> FRU Program Date: {:s}".format(fru_info_list[3]))
                boot_info_list = self._nic_ctrl_list[slot].nic_get_boot_info()
                if not boot_info_list:
                    self.cli_log_slot_err(slot, "Retrieve NIC boot info failed")
                else:
                    self.cli_log_slot_inf(slot, "==> Boot image: {:s}({:s})".format(boot_info_list[0], boot_info_list[1]))

                cpld_info_list = self._nic_ctrl_list[slot].nic_get_cpld()
                if not cpld_info_list:
                    self.cli_log_slot_err(slot, "Retrieve NIC CPLD info failed")
                else:
                    self.cli_log_slot_inf(slot, "==> CPLD: {:s}({:s})".format(cpld_info_list[0], cpld_info_list[1]))

                diag_info_list = self._nic_ctrl_list[slot].nic_get_diag()
                if not diag_info_list:
                    self.cli_log_slot_err(slot, "Retrieve NIC Diag info failed")
                else:
                    self.cli_log_slot_inf(slot, "==> Diag version: {:s}".format(diag_info_list[0]))
                    self.cli_log_slot_inf(slot, "==> EMMC Util version: {:s}".format(diag_info_list[1]))
                    self.cli_log_slot_inf(slot, "==> NIC ASIC version: {:s}".format(diag_info_list[2]))

                if not self._nic_ctrl_list[slot].nic_check_status():
                    self.cli_log_slot_err(slot, "NIC in failure state")
            elif self._slots_to_skip[slot]:
                self.cli_log_slot_err(slot, "NIC is Skipped")
            else:
                self.cli_log_slot_err(slot, "NIC is Absent")
        self.cli_log_inf("End MTP NIC Info Dump")


    def mtp_nic_init(self):
        self.cli_log_inf("Init NICs in the MTP Chassis", level = 0)

        # init nic present list
        if not self.mtp_init_nic_type():
            self.cli_log_inf("Failed to init NICs in the MTP Chassis", level = 0)
            return False

        self.cli_log_inf("Init NICs in the MTP Chassis complete\n", level = 0)

        return True


    # validate the fru to double confirm scan process
    def mtp_nic_scan_fru_validate(self):
        for slot in range(self._slots):
            if self._nic_scan_prsnt_list[slot] != self._nic_prsnt_list[slot]:
                # NIC present, but not scanned
                if self._nic_prsnt_list[slot]:
                    self.cli_log_slot_err(slot, "NIC is present, but barcode is not scanned")
                    return False

            if not self.mtp_check_nic_status(slot):
                self.cli_log_slot_err(slot, "NIC is in failure state, bypass fru validation")
                continue

            # NIC sn should match
            if self._nic_scan_prsnt_list[slot] and self._nic_prsnt_list[slot]:
                if self._nic_scan_sn_list[slot] != self._nic_sn_list[slot]:
                    self.cli_log_slot_err(slot, "SN mismatch, scanned: {:s}, fru: {:s}".format(self._nic_scan_sn_list[slot], self._nic_sn_list[slot]))
                    return False
        return True

    def mtp_single_nic_diag_init(self, slot, emmc_format, fru_valid, vmargin, aapl, nic_test_rslt_list):
        ret = True
        nic_type = self.mtp_get_nic_type(slot)
        if ret and not self.mtp_check_nic_status(slot):
            ret = False

        if ret and not self.mtp_nic_emmc_init(slot, emmc_format):
            ret = False

        if ret and not self.mtp_mgmt_copy_nic_diag(slot, emmc_format):
            ret = False

        if ret and not self.mtp_mgmt_start_nic_diag(slot, aapl):
            ret = False

        if ret and not self.mtp_nic_cpld_init(slot):
            ret = False

        if ret and fru_valid:
            if emmc_format:
                init_date = False
            else:
                init_date = True
            if ret and not self.mtp_nic_fru_init(slot, init_date, nic_type):
                ret = False
            fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
            self.mtp_set_nic_sn(slot, fru_info_list[0])
        elif not fru_valid:
            self.mtp_set_nic_sn(slot, self.mtp_get_nic_scan_sn(slot))

        if ret and not self.mtp_set_nic_vmarg(slot, vmargin):
            ret = False

        if ret and not self.mtp_nic_display_voltage(slot):
            ret = False

        if not ret:
            nic_test_rslt_list[slot] = False

        return ret


    # pre setup for the diag test
    def mtp_nic_diag_init_pre(self):
        fail_list = list()
        self.cli_log_inf("NIC Diag Setup started", level = 0)
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                if not self.mtp_nic_pcie_poll_enable(slot, False):
                    fail_list.append(slot)
        self.cli_log_inf("NIC Diag Setup complete\n", level = 0)
        return fail_list


    # cleanup for the diag test
    def mtp_nic_diag_init_post(self):
        fail_list = list()
        self.cli_log_inf("NIC Diag Cleanup started", level = 0)
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                if not self.mtp_nic_pcie_poll_enable(slot, True):
                    fail_list.append(slot)
        self.cli_log_inf("NIC Diag Cleanup complete\n", level = 0)
        return fail_list


    def mtp_nic_mgmt_seq_init(self, fpo):
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                self.mtp_nic_mini_init(slot, fpo)


    def mtp_nic_mgmt_para_init(self, aapl, swm_lp=False):
        nic_list = list()
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                self.mtp_nic_boot_info_init(slot)
                nic_list.append(slot)

        # parallel init mgmt/aapl
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        asic_type = "elba" if self._asic_support == MTP_ASIC_SUPPORT.ELBA else "capri"
        sig_list = [MFG_DIAG_SIG.NIC_MGMT_PARA_SIG]
        if aapl:
            for slot in nic_list:
                self.cli_log_slot_inf(slot, "Para Init NIC MGMT/AAPL port")
            cmd = MFG_DIAG_CMDS.MTP_PARA_MGMT_AAPL_FMT.format(nic_list_param, asic_type)
        else:
            for slot in nic_list:
                self.cli_log_slot_inf(slot, "Para Init NIC MGMT port")
            cmd = MFG_DIAG_CMDS.MTP_PARA_MGMT_INIT_FMT.format(nic_list_param, asic_type)
            if swm_lp:
                cmd = "".join((cmd, " -swm_lp")) 

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        if not self.mtp_nic_mgmt_mac_refresh():
            return False

        return True


    def mtp_nic_mgmt_mac_refresh(self):
        # delete the arp entry
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                ipaddr = libmfg_utils.get_nic_ip_addr(slot)
                cmd = MFG_DIAG_CMDS.MTP_ARP_DELET_FMT.format(ipaddr)
                if not self.mtp_mgmt_exec_sudo_cmd(cmd):
                    return False

                ###Have seen failures on Naples25SWM where ping fails and ARP table is not populated
                ###Add a 2nd ping try as a work around.   
                for x in range(2):
                    time.sleep(5)
                    # ping to update the arp cache
                    cmd = MFG_DIAG_CMDS.MTP_NIC_PING_FMT.format(ipaddr)
                    if not self.mtp_mgmt_exec_cmd(cmd):
                        return False

                

        return True

    # def mtp_nic_connection_init(self):
    #     successsetupconnection = False
    #     for x in range(3):
    #         ret = self.mtp_nic_connection_init_run()
    #         if ret:
    #             successsetupconnection = True
    #             break
    #         if x == 2:
    #             break
    #         if not self.tor_boot_select(1):
    #             return False
    #         if not self.tor_mgmt_init(False):
    #             return False
    #         if not self.tor_diag_init(FF_Stage.FF_DL, fpo=False):
    #             return False

    #     return successsetupconnection

    # def mtp_nic_connection_init_run(self):

    #     if not self.tor_nic_gold_boot():
    #         self.cli_log_err("Failed to set NIC goldfw", level=0)
    #         return False

    #     # Powercycle including rescan
    #     if not self.mtp_power_cycle_nic():
    #         return False

    #     # Validate previous step
    #     for slot in range(self._slots):
    #         if not self.mtp_mgmt_verify_nic_gold_boot(slot):
    #             self.cli_log_slot_err(slot, "Failed to boot into goldfw")
    #             return False

    #     if self._uut_type == UUT_Type.TOR:
    #         if not self.tor_nic_memtun_init():
    #             self.cli_log_err("memtun init failed", level=0)
    #             return False

    #         for slot in range(self._slots):
    #             self.mtp_nic_boot_info_init(slot)

    #     return True

    def mtp_nic_diag_init(self, emmc_format=False, fru_valid=True, sn_tag=False, fru_cfg=None, vmargin=0, aapl=False, swm_lp=False, nic_util=False):
        ret = True

        # emmc_format will be true only for the first time boot up
        fpo = emmc_format
        if fpo:
            self.cli_log_inf("Init NIC Diag Environment with FPO set", level = 0)
        else:
            self.cli_log_inf("Init NIC Diag Environment", level = 0)

        if sn_tag:
            self.mtp_nic_load_scan_fru(fru_cfg)
        else:
            self.cli_log_inf("Bypass NIC SN/MAC load")

        if self._uut_type == UUT_Type.TOR:
            for slot in range(self._slots):
                ret &= self.mtp_nic_boot_info_init(slot)
        else:
            if fpo:
                ret = self.mtp_nic_mgmt_seq_init(fpo)
            else:
                ret = self.mtp_nic_mgmt_para_init(aapl, swm_lp)

            if not self.mtp_mgmt_nic_mac_validate():
                return False

        if nic_util:
            # for QA only not DL: do mgmt para init but do emmc format. 
            emmc_format = True

        for slot in range(self._slots):
            start_ts = self.log_slot_test_start(slot, "NIC_DIAG_INIT")

        nic_thread_list = list()
        nic_test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
        for slot in range(self._slots):
            if not self._nic_prsnt_list[slot]:
                nic_test_rslt_list[slot] = False
                continue
            nic_thread = threading.Thread(target = self.mtp_single_nic_diag_init,
                                          args = (slot,
                                                  emmc_format,
                                                  fru_valid,
                                                  vmargin,
                                                  aapl,
                                                  nic_test_rslt_list))
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)

        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(5)

        for slot in range(self._slots):
            duration = self.log_slot_test_stop(slot, "NIC_DIAG_INIT", start_ts)

        for slot in range(self._slots):
            if not nic_test_rslt_list[slot]:
                ret &= False

        if fru_valid and sn_tag:
            if not self.mtp_nic_scan_fru_validate():
                return False

        self.mtp_nic_info_disp(fru_valid)

        self.mtp_mgmt_killall_tclsh_picocom()

        self.cli_log_inf("Init NIC Diag Environment complete\n", level = 0)
        return ret

    def mtp_single_nic_emmc_reformat(self, slot, nic_rslt_list, emmc_format=True):
        if not self.mtp_nic_emmc_init(slot, emmc_format):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Failed to re-initialize EMMC")
            nic_rslt_list[slot] = False
            return

        if not self.mtp_mgmt_copy_nic_diag(slot, emmc_format):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Failed to copy diag")
            nic_rslt_list[slot] = False
            return

        if not self._nic_ctrl_list[slot].mtp_exec_cmd("sync"):
            err_msg = self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_err_msg(err_msg)
            return

    def mtp_nic_emmc_reformat(self, nic_rslt_list, nic_list, emmc_format=True):
        """
          copy of mtp_nic_diag_init(), but without the FRU, CPLD inits.
          re-init emmc after a desctructive emmc test, to prepare for next stage.
        """
        self.mtp_nic_mgmt_para_init(aapl=False)
        if not self.mtp_mgmt_nic_mac_validate():
            return False

        nic_thread_list = list()
        for slot in nic_list:
            nic_type = self.mtp_get_nic_type(slot)
            if not (nic_type == NIC_Type.ORTANO2 or nic_type == NIC_Type.ORTANO):
                continue
            if not self._nic_prsnt_list[slot]:
                continue
            nic_thread = threading.Thread(target = self.mtp_single_nic_emmc_reformat,
                                          args = (slot, nic_rslt_list, emmc_format))
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)

        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(5)

        return nic_rslt_list

    # check if any duplicate mac address in the internal network
    def mtp_mgmt_nic_mac_validate(self):
        self.cli_log_inf("NIC MAC address validate started")
        mac_addr_reg_exp = r"([a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2})"
        cmd = MFG_DIAG_CMDS.MTP_NIC_MAC_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to validate NIC MAC address")
            return False

        match = re.findall(mac_addr_reg_exp, self.mtp_get_cmd_buf())
        if match:
            for mac in match:
                if match.count(mac) > 1:
                    self.cli_log_err("NIC MAC address validate failed - duplicate entry: {:s}".format(mac))
                    return False
            self.cli_log_inf("NIC MAC address validate complete - {:d} entries found".format(len(match)))
            return True
        else:
            self.cli_log_err("NIC MAC address validate failed - 0 entry found")
            return False


    def mtp_power_on_nic(self, pre_diag_method=False):
        if self._uut_type is None or self._uut_type == UUT_Type.NAPLES_MTP:
            power_on_delay = MTP_Const.NIC_POWER_ON_DELAY
            cmd = MFG_DIAG_CMDS.MTP_POWER_ON_NIC_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to power on NIC")
                return False

        elif self._uut_type == UUT_Type.TOR:
            power_on_delay = MTP_Const.TOR_NIC_POWER_ON_DELAY
            if pre_diag_method:

                cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("Failed to find eeupdate directory")
                    return False
                # cmd = "./td.bash all on"
                # if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["turning on elba0", "turning on elba1"], timeout=power_on_delay+MTP_Const.TOR_PCIE_SCAN_DELAY):
                #     self.cli_log_err("Failed to power on elbas")
                #     return False
                
                cmd = "./td.bash e0 on"
                if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["turning on elba0"], timeout=power_on_delay+MTP_Const.TOR_PCIE_SCAN_DELAY):
                    self.cli_log_err("Failed to power on elba0")

                cmd = "./td.bash e1 on"
                if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["turning on elba1"], timeout=power_on_delay+MTP_Const.TOR_PCIE_SCAN_DELAY):
                    self.cli_log_err("Failed to power on elba1")

            else:
            
                cmd = "/home/diag/diag/util/fpgautil power on e0 nopciscan"
                if not self.mtp_mgmt_exec_cmd(cmd, timeout=power_on_delay + MTP_Const.TOR_PCIE_SCAN_DELAY):
                    self.cli_log_err("Failed to power on elba0")
                    return False

                cmd = "/home/diag/diag/util/fpgautil power on e1"
                if not self.mtp_mgmt_exec_cmd(cmd, timeout=power_on_delay + MTP_Const.TOR_PCIE_SCAN_DELAY):
                    self.cli_log_err("Failed to power on elba1")
                    return False

        self.cli_log_inf("Power on all NIC, wait {:02d} seconds for NIC power up".format(power_on_delay), level=0)
        libmfg_utils.count_down(power_on_delay)
        return True


    def mtp_power_off_nic(self, pre_diag_method=False):
        if self._uut_type is None or self._uut_type == UUT_Type.NAPLES_MTP:
            power_off_delay = MTP_Const.NIC_POWER_OFF_DELAY
            cmd = MFG_DIAG_CMDS.MTP_POWER_OFF_NIC_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to power off NIC")
                return False
        elif self._uut_type == UUT_Type.TOR:
            power_off_delay = MTP_Const.TOR_NIC_POWER_OFF_DELAY
            if pre_diag_method:

                cmd = "echo 1 > /sys/bus/pci/devices/0000:0b:00.0/remove"   #elba0
                if not self.mtp_mgmt_exec_cmd(cmd): #, sig_list=["# "]):
                    self.cli_log_err("{:s} failed".format(cmd))
                    return False
                cmd = "echo 1 > /sys/bus/pci/devices/0000:05:00.0/remove"   #elba1
                if not self.mtp_mgmt_exec_cmd(cmd): #, sig_list=["# "]):
                    self.cli_log_err("{:s} failed".format(cmd))
                    return False

                cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("Failed to find eeupdate directory")
                    return False
                # cmd = "./td.bash all off"
                # if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["turning off elba0", "turning off elba1"], timeout=power_off_delay):
                #     self.cli_log_err("Failed to power off elbas")
                #     return False

                cmd = "./td.bash e0 off"
                if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["turning off elba0"], timeout=5):
                    if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["turning off elba0"]):
                        self.cli_log_err("Failed to power off elba0")
                        return False
                cmd = "./td.bash e1 off"
                if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["turning off elba1"], timeout=5):
                    if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["turning off elba1"]):
                        self.cli_log_err("Failed to power off elba1")
                        return False
            else:

                cmd = "/home/diag/diag/util/fpgautil power off e0"
                if not self.mtp_mgmt_exec_cmd(cmd, timeout=power_off_delay):
                    self.cli_log_err("Failed to power off elba0")
                    return False

                cmd = "/home/diag/diag/util/fpgautil power off e1"
                if not self.mtp_mgmt_exec_cmd(cmd, timeout=power_off_delay):
                    self.cli_log_err("Failed to power off elba1")
                    return False

        self.cli_log_inf("Power off all NIC, wait {:02d} seconds for NIC power down".format(power_off_delay), level=0)
        libmfg_utils.count_down(power_off_delay)
        return True       


    def mtp_power_cycle_nic(self, pre_diag_method=False):
        cmd = "ps -A | grep memtun"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd))
            return False

        cmd = "killall memtun"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd))
            return False

        rc = self.mtp_power_off_nic(pre_diag_method)
        if not rc:
            return rc

        rc = self.mtp_power_on_nic(pre_diag_method)
        if not rc:
            return rc

        return True


    def mtp_init_nic_type(self):
        self._nic_type_list = [None] * self._slots      # reset nic types
        cmd = MFG_DIAG_CMDS.NIC_PRESENT_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to init NIC presence")
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False

        # find type
        self.cli_log_inf("Init NIC Present/Type")
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES100
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES100)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100IBM, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES100IBM
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES100IBM)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100HPE, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES100HPE
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES100HPE)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES25
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_FORIO, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.FORIO
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.FORIO)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_VOMERO, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.VOMERO
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.VOMERO)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_VOMERO2, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.VOMERO2
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.VOMERO2)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWM, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES25SWM
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25SWM)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25OCP, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES25OCP
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25OCP)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWMDELL, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES25SWMDELL
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25SWMDELL)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWM833, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.NAPLES25SWM833
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.NAPLES25SWM833)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.ORTANO
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.ORTANO)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        match = re.findall(MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2, self._mgmt_handle.before)
        if match:
            for idx in range(len(match)):
                slot = int(match[idx]) - 1
                if not self._slots_to_skip[slot]:
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = NIC_Type.ORTANO2
                    self._nic_ctrl_list[slot].nic_set_type(NIC_Type.ORTANO2)
                else:
                    self._nic_prsnt_list[slot] = False
                    self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)
        return True


    def mtp_nic_check_prsnt(self, slot):
        return self._nic_prsnt_list[slot]


    def mtp_get_nic_prsnt_list(self):
        return self._nic_prsnt_list

    def mtp_get_nic_skip_list(self):
        return self._slots_to_skip

    def mtp_get_nic_pn(self, slot):
        return self._nic_ctrl_list[slot].nic_get_naples_pn()

    def mtp_set_nic_pn(self, slot, pn):
        self.cli_log_slot_inf(slot, "Set PN to {:s}".format(pn))
        self._nic_ctrl_list[slot].nic_set_pn(pn)

    def mtp_is_nic_ortano_oracle(self, slot):
        """
         Differentiate ortano by PN
         - 68-0015: Oracle version -> return True
         - 68-0021: Pensando version -> return False
         - any other -> return False with err msg
        """
        if self._nic_type_list[slot] != NIC_Type.ORTANO2:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for Ortano")
            return False
        slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for Ortano")
            return False
        oracle_pn = re.match(PART_NUMBERS_MATCH.ORTANO2_ORC_PN_FMT, slot_pn)
        if oracle_pn:
            return True
        else:
            return False

    def mtp_get_nic_type(self, slot):
        return self._nic_type_list[slot]

    def mtp_set_nic_type(self, slot, nic_type):
        """
         Don't use this function for MTP. Instead use mtp_init_nic_type().
         This is only for, for e.g. FST setup, which does not have `inventory` command.
         and for rework script which changes the type during runtime.
        """
        self.cli_log_slot_inf(slot, "Set TYPE to {:s}".format(nic_type))
        self._nic_type_list[slot] = nic_type
        if self._nic_ctrl_list[slot]:
            self._nic_ctrl_list[slot].nic_set_type(nic_type)

    def mtp_nic_type_valid(self, slot):
        return self._nic_type_list[slot] in self._valid_type_list


    def mtp_get_nic_sn(self, slot):
        return self._nic_sn_list[slot]


    def mtp_set_nic_sn(self, slot, sn):
        self.cli_log_slot_inf(slot, "Set SN to {:s}".format(sn))
        self._nic_sn_list[slot] = sn


    def mtp_get_nic_scan_sn(self, slot):
        return self._nic_scan_sn_list[slot]


    def mtp_set_nic_scan_sn(self, slot, sn):
        self.cli_log_slot_inf(slot, "Set Scan SN to {:s}".format(sn))
        self._nic_scan_sn_list[slot] = sn
        self._nic_scan_prsnt_list[slot] = True


    def mtp_mgmt_set_nic_diag_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_diag_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with diag failed")
            return False

        self.cli_log_slot_inf(slot, "Set NIC default diag boot")
        return True
        
    def mtp_mgmt_set_nic_mainfw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_mainfw_boot():
            self.mtp_get_nic_err_msg(slot)
            self.cli_log_slot_err(slot, "Set NIC default boot with mainfw failed")
            return False

        self.cli_log_slot_inf(slot, "Set NIC default mainfw boot")
        return True


    def mtp_mgmt_nic_sw_shutdown(self, slot, software_pn):
        isCloud =  self.check_is_cloud_software_image(slot, software_pn)
        if not self._nic_ctrl_list[slot].nic_sw_shutdown(isCloud):
            self.cli_log_slot_err(slot, "Graceful shut down NIC failed")
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            return False

        return True

    def tor_nic_sw_cleanup(self, slot):
        if not self._nic_ctrl_list[slot].nic_mgmt_sw_cleanup():
            self.cli_log_slot_err(slot, "Cleanup NIC failed")
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            return False

        return True

    def mtp_mgmt_nic_sw_cleanup_shutdown(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_cleanup_shutdown():
            self.cli_log_slot_err(slot, "Graceful clean up shut down NIC failed")
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            self.mtp_dump_err_msg(err_msg)
            return False

        return True

    def mtp_mgmt_set_elba_uboot_env(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_elba_uboot_env(slot):
            self.cli_log_slot_err(slot, "Setup uboot env variables failed")
            return False
        return True

    def mtp_check_nic_status(self, slot):
        return self._nic_ctrl_list[slot].nic_check_status()


    # log the diag test history
    def mtp_mgmt_diag_history_disp(self):
        cmd = MFG_DIAG_CMDS.MTP_DIAG_SHIST_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            return False

        return True


    # clear the diag test history
    def mtp_mgmt_diag_history_clear(self):
        cmd = MFG_DIAG_CMDS.MTP_DIAG_CHIST_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            return False

        return True


    def mtp_mgmt_pre_post_diag_check(self, intf, slot, vmarg=0):
        if intf == "NIC_JTAG":
            if self.mtp_check_nic_jtag(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_POWER":
            if self.mtp_mgmt_check_nic_pwr_status(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_MEM":
            if self.mtp_mgmt_test_nic_mem(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_STATUS":
            if self.mtp_check_nic_status(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_DIAG_BOOT":
            if self._uut_type == UUT_Type.NAPLES_MTP:
                if self.mtp_nic_check_diag_boot(slot):
                    return "SUCCESS"
                else:
                    return MTP_DIAG_Error.NIC_DIAG_FAIL
            elif self._uut_type == UUT_Type.TOR:
                if self.mtp_mgmt_verify_nic_gold_boot(slot):
                    return "SUCCESS"
                else:
                    return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_CPLD":
            if self.mtp_verify_nic_cpld(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "NIC_ALOM_CABLE":
            if self._swmtestmode[slot] == Swm_Test_Mode.SWMALOM or self._swmtestmode[slot] == Swm_Test_Mode.ALOM:
                if self.mtp_nic_naples25swm_alom_cable_signal_test(slot, 1):
                    return "SUCCESS"
                else:
                    return MTP_DIAG_Error.NIC_DIAG_FAIL
            else:
                return "SUCCESS"
        elif intf == "NIC_N25SWM_CPLD":
            if self._swmtestmode[slot] == Swm_Test_Mode.SWMALOM or self._swmtestmode[slot] == Swm_Test_Mode.SWM:
                if self.mtp_nic_naples25swm_cpld_spi_to_smb_reg_test(slot):
                    return "SUCCESS"
                else:
                    return MTP_DIAG_Error.NIC_DIAG_FAIL
            else:
                return "SUCCESS"
        elif intf == "NIC_OCP_SIGNALS":
            if self.mtp_nic_naples25ocp_signal_test(slot):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "TOR_CPLD":
            if self.tor_cpld_verify():
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "TOR_OS":
            if self.tor_os_verify(TOR_IMAGES.os_test_dat[self._uut_type]):
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        elif intf == "TOR_BIOS":
            if self.tor_bios_verify():
                return "SUCCESS"
            else:
                return MTP_DIAG_Error.NIC_DIAG_FAIL
        else:
            self.cli_log_slot_err(slot, "Unknown pre diag check module")
            return MTP_DIAG_Error.NIC_DIAG_FAIL


    def mtp_nic_pcie_poll_enable(self, slot, enable=True):
        if enable:
            self.cli_log_slot_inf(slot, "Enable NIC PCIE Polling")
        else:
            self.cli_log_slot_inf(slot, "Disable NIC PCIE Polling")

        if not self._nic_ctrl_list[slot].nic_pcie_poll_enable(enable):
            if enable:
                self.cli_log_slot_err(slot, "Enable NIC PCIE Polling failed")
            else:
                self.cli_log_slot_err(slot, "Disable NIC PCIE Polling failed")
            return False

        return True


    def mtp_mgmt_run_test_mtp_para(self, test, nic_list, vmarg):
        nic_fail_list = list()

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return nic_list[:]

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.MTP_PARA_TEST_SIG]

        if test == "SNAKE_TOR":
            self.mtp_mgmt_exec_cmd("cd /home/diag/diag/util")
            snake_port_mask = "0xff"
            snake_duration = "150"
            snake_loopback = "ext"
            cmd = "./switch td3 snake {:s} {:s} {:s}".format(snake_port_mask, snake_duration, snake_loopback)
            sig_list = ["SWITCH SNAKE TEST "]
            test_timeout = self.get_test_timeout(cmd, test)
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=test_timeout+int(snake_duration)):
                self.cli_log_err("{:s} failed".format(cmd))
                return nic_list[:]
            if "PASSED" not in self.mtp_get_cmd_buf():
                return nic_list[:]
            else:
                return []
        elif test == "PRBS_TOR":
            #switch td3 prbs <time> <prbs7/prbs9/prbs11/prbs15/prbs23/prbs31/prbs58>
            self.mtp_mgmt_exec_cmd("cd /home/diag/diag/util")
            prbs_type = "prbs58"
            prbs_duration = "60"
            cmd = "./switch td3 prbs {:s} {:s}".format(prbs_duration, prbs_type)
            test_timeout = self.get_test_timeout(cmd, test)
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=test_timeout+int(prbs_duration)):
                self.cli_log_err("{:s} failed".format(cmd))
                return nic_list[:]
            cmd_buf = self.mtp_get_cmd_buf()
            if "PRBS PASSED" not in cmd_buf:
                self.mtp_dump_err_msg(cmd_buf)
                return nic_list[:]
            else:
                return []
        elif test == "PCI_TOR":
            self.mtp_mgmt_exec_cmd("cd /home/diag/diag/util")
            cmd = "./switch cpu pciscan"
            test_timeout = self.get_test_timeout(cmd, test)
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=test_timeout+int(test_timeout)):
                self.cli_log_err("{:s} failed".format(cmd))
                return nic_list[:]
            cmd_buf = self.mtp_get_cmd_buf()
            if "PCISCAN TEST PASSED" not in cmd_buf:
                self.mtp_dump_err_msg(cmd_buf)
                return nic_list[:]
            else:
                return []
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return nic_list[:]

    def tor_diag_test_binary(self, test, vmarg):
        cmd = "cd /home/diag/diag/util"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        if test == "SNAKE_TOR":
            snake_port_mask = "0xff"
            snake_duration = "150"
            snake_loopback = "ext"
            cmd = "./switch td3 snake {:s} {:s} {:s}".format(snake_port_mask, snake_duration, snake_loopback)
            sig_list = ["SWITCH SNAKE TEST "]
            test_timeout = self.get_test_timeout(cmd, test)
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=test_timeout+int(snake_duration)):
                self.cli_log_err("{:s} failed".format(cmd))
                return False
            if "PASSED" not in self.mtp_get_cmd_buf():
                return False
            else:
                return True
        elif test == "PRBS_TOR":
            #switch td3 prbs <time> <prbs7/prbs9/prbs11/prbs15/prbs23/prbs31/prbs58>
            prbs_type = "prbs58"
            prbs_duration = "60"
            cmd = "./switch td3 prbs {:s} {:s}".format(prbs_duration, prbs_type)
            test_timeout = self.get_test_timeout(cmd, test)
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=test_timeout+int(prbs_duration)):
                self.cli_log_err("{:s} failed".format(cmd))
                return False
            cmd_buf = self.mtp_get_cmd_buf()
            if "PRBS PASSED" not in cmd_buf:
                self.mtp_dump_err_msg(cmd_buf)
                return False
            else:
                return True
        elif test == "PCI_TOR":
            cmd = "./switch cpu pciscan"
            test_timeout = self.get_test_timeout(cmd, test)
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=test_timeout+int(test_timeout)):
                self.cli_log_err("{:s} failed".format(cmd))
                return False
            cmd_buf = self.mtp_get_cmd_buf()
            if "PCISCAN TEST PASSED" not in cmd_buf:
                self.mtp_dump_err_msg(cmd_buf)
                return False
            else:
                return True
        else:
            self.cli_log_err("Unknown Diag Bash Test {:s}".format(test))
            return False

    def mtp_mgmt_get_test_result(self, cmd, test):
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Unable to execute cmd {:s}".format(cmd))
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT

        # Test    Error code, SUCCESS means pass
        match = re.findall(r"{:s} *([A-Za-z0-9_]+)".format(test), self.mtp_get_cmd_buf())
        if match:
            return match[0]
        else:
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT


    def mtp_mgmt_get_test_result_para(self, slot, cmd, test):
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.cli_log_slot_err_lock(slot, "Execute {:s} failed".format(cmd))
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT

        # Test    Error code, SUCCESS means pass
        match = re.findall(r"{:s} +([A-Za-z0-9_]+)".format(test), self.mtp_get_nic_cmd_buf(slot))
        if match:
            return match[0]
        else:
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT

    def get_test_timeout(self, cmd, test):
        if test in ("SNAKE_TOR"):
            return 360
        elif test in ("PRBS_TOR"):
            return 180
        elif test in ("ELBA_ARM_MEMORY"):
            return 360
        elif test in ("ELBA_EDMA_TEST"):
            return 360
        elif test in ("PCI_TOR"):
            return 30    
        elif test in ("TD3DIAG"):
            return 360
        elif test in ("L1"):
            return 40*60
        else:
            return MTP_Const.TOR_DIAG_TEST_TIMEOUT

    def mtp_run_diag_test_seq(self, slot, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None):
        # init command
        if init_cmd:
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(init_cmd):
                err_msg = self.mtp_get_nic_cmd_buf(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # log the timestamp in diag log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(test, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self._nic_ctrl_list[slot].mtp_exec_cmd(ts_record_cmd)

        if not self._nic_ctrl_list[slot].mtp_exec_cmd(diag_cmd, timeout=MTP_Const.DIAG_TEST_TIMEOUT):
            err_msg = self.mtp_get_nic_cmd_buf(slot)
            return [MTP_DIAG_Error.NIC_DIAG_TIMEOUT, [err_msg]]

        # diag test error ouput
        err_msg_list = list()
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        if MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG in cmd_buf:
            for line in cmd_buf.split('\n'):
                if MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG in line:
                    err_msg = line.replace('\r', '')
                    err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG):]
                    err_msg_list.append(err_msg)

        # log the timestamp in diag log
        stop = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(test, str(stop), str(stop-start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self._nic_ctrl_list[slot].mtp_exec_cmd(ts_record_cmd)

        # post command
        if post_cmd:
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(post_cmd):
                err_msg = self.mtp_get_nic_cmd_buf(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # for zmq, get result at the test end instead of sresult.
        # zmq_l1_result_re = r"MTP1 +ASIC +L1 +(\w+)"
        # match = re.findall(zmq_l1_result_re, cmd_buf)
        # if match:
        #     ret = match[0]
        # else:
        #     ret = "TIMEOUT"
        ret = self.mtp_mgmt_get_test_result_para(slot, rslt_cmd, test)

        return [ret, err_msg_list]

    def mtp_run_diag_test_tor(self, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None):
        # init command
        if init_cmd:
            if not self.mtp_mgmt_exec_cmd(init_cmd):
                err_msg = self.mtp_get_cmd_buf()
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # log the timestamp in diag log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(test, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd(ts_record_cmd)

        test_timeout = self.get_test_timeout(diag_cmd, test)

        if not self.mtp_mgmt_exec_cmd(diag_cmd, sig_list=["Test Result Done"], timeout=test_timeout):
            err_msg = self.mtp_get_cmd_buf()
            return [MTP_DIAG_Error.NIC_DIAG_TIMEOUT, [err_msg]]

        # diag test error ouput
        err_msg_list = list()
        cmd_buf = self.mtp_get_cmd_buf()
        if MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG in cmd_buf:
            for line in cmd_buf.split('\n'):
                if MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG in line:
                    err_msg = line.replace('\r', '')
                    err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG):]
                    err_msg_list.append(err_msg)

        # log the timestamp in diag log
        stop = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(test, str(stop), str(stop-start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd(ts_record_cmd)

        # post command
        if post_cmd:
            if not self.mtp_mgmt_exec_cmd(post_cmd):
                err_msg = self.mtp_get_cmd_buf()
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        ret = self.mtp_mgmt_get_test_result(rslt_cmd, test)

        return [ret, err_msg_list]


    def mtp_mgmt_jtag_rst(self):
        self.cli_log_inf("Reset the MTP JTAG Interface", level = 0)
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        cmd = MFG_DIAG_CMDS.MTP_DSP_STOP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        cmd = "cleantcl.sh"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        cmd = MFG_DIAG_CMDS.MTP_DSP_START_FMT
        sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        self.cli_log_inf("Reset the MTP JTAG Interface complete", level = 0)
        return True

    def mtp_nic_board_config(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.ORTANO2:
            if self.mtp_is_nic_ortano_oracle(slot):
                preset_config = "5"
            else:
                preset_config = "8"
            if not self._nic_ctrl_list[slot].nic_set_board_config(preset_config):
                self.cli_log_slot_err_lock(slot, "Set board config failed")
                err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
                self.mtp_dump_err_msg(err_msg)
                return False
        else:
            self.cli_log_slot_err_lock(slot, "Need to QA this card")
        return True

    def mtp_mgmt_dump_avs_info(self, slot, buf):
        self.cli_log_slot_inf(slot, "AVS Set Result Dump:")
        # find any error
        avs_passed_flag = re.findall(r"SET AVS PASSED", buf)
        if not avs_passed_flag:
            self.mtp_dump_nic_err_msg(slot)
            return False

        # find the die id
        die_id_match = re.findall(r"(ASIC_DIE_ID: +0x[0-9a-fA-F]+)", buf)
        if die_id_match:
            self.cli_log_slot_inf(slot, die_id_match[0], level=1)
        osc_count_id_match = re.findall(r"(osc_count_id: +[0-9]+)", buf)
        if osc_count_id_match:
            self.cli_log_slot_inf(slot, osc_count_id_match[0], level=1)
        vdd_core_offset_match = re.findall(r"(vdd_core_offset: +[0-9a-fA-F]+)", buf)
        if vdd_core_offset_match:
            self.cli_log_slot_inf(slot, vdd_core_offset_match[0], level=1)
        vdd_arm_offset_match = re.findall(r"(vdd_arm_offset: +[0-9a-fA-F]+)", buf)
        if vdd_arm_offset_match:
            self.cli_log_slot_inf(slot, vdd_arm_offset_match[0], level=1)
        return True


    def mtp_mgmt_set_nic_avs(self, slot):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        nic_type = self.mtp_get_nic_type(slot)
        sn = self.mtp_get_nic_sn(slot)

        vdd_avs_cmd, arm_avs_cmd = None, None

        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip AVS for Proto NIC")
            return True
        elif nic_type == NIC_Type.NAPLES100:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES100_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES100_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES100IBM:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES100IBM_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES100IBM_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES100HPE:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES100HPE_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES100HPE_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.VOMERO:
            vdd_avs_cmd = MFG_DIAG_CMDS.VOMERO_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.VOMERO_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.VOMERO2:
            vdd_avs_cmd = MFG_DIAG_CMDS.VOMERO2_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.VOMERO2_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25SWM:  
            #NAPLES25SWM uses same setting as Naples25
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25SWMDELL:  
            #NAPLES25SWM uses same setting as Naples25
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25OCP:  
            #NAPLES25OCP uses same setting as Naples25
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25SWM833:
            vdd_avs_cmd = MFG_DIAG_CMDS.NAPLES25SWM833_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS.NAPLES25SWM833_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
            """
             Separate freq by PN:
             - For 68-0015 (Oracle) use 1033
             - For 68-0021 (Pensando) use 1100
            """
            if self.mtp_is_nic_ortano_oracle(slot):
                vdd_avs_cmd = MFG_DIAG_CMDS.ORTANO_ORC_AVS_SET_FMT.format(sn, slot+1)
            else:
                vdd_avs_cmd = MFG_DIAG_CMDS.ORTANO_PEN_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.TAORMINA:
            vdd_avs_cmd = MFG_DIAG_CMDS.TOR_AVS_SET_FMT.format(sn, slot+1)
        else:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
            return False

        if vdd_avs_cmd:
            self.mtp_mgmt_set_nic_avs_pre(slot)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(vdd_avs_cmd, timeout=MTP_Const.NIC_AVS_SET_DELAY):
                self.cli_log_slot_err(slot, "Timed out: Failed to execute command {:s}".format(vdd_avs_cmd))
                self.mtp_mgmt_set_nic_avs_post(slot)
                return False
            if not self.mtp_mgmt_dump_avs_info(slot, self.mtp_get_nic_cmd_buf(slot)):
                self.cli_log_slot_err(slot, "SET VDD AVS FAILED")
                return False
        if arm_avs_cmd:
            self.mtp_mgmt_set_nic_avs_pre(slot)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(arm_avs_cmd, timeout=MTP_Const.NIC_AVS_SET_DELAY):
                self.cli_log_slot_err(slot, "Timed out: Failed to execute command {:s}".format(arm_avs_cmd))
                self.mtp_mgmt_set_nic_avs_post(slot)
                return False
            if not self.mtp_mgmt_dump_avs_info(slot, self.mtp_get_nic_cmd_buf(slot)):
                self.cli_log_slot_err(slot, "SET ARM AVS FAILED")
                return False
        self.mtp_mgmt_set_nic_avs_post(slot)

        return True

    def mtp_mgmt_set_nic_avs_pre(self, slot):
        self._nic_ctrl_list[slot].mtp_exec_cmd(MFG_DIAG_CMDS.NIC_DIAG_STOP_TCLSH_FMT, timeout=MTP_Const.OS_CMD_DELAY)

    def mtp_mgmt_set_nic_avs_post(self, slot):
        self.mtp_nic_send_ctrl_c(slot) # kill any hung tclsh in this same session
        cmd = MFG_DIAG_CMDS.NIC_AVS_POST_FMT.format(slot+1)
        self._nic_ctrl_list[slot].mtp_exec_cmd(cmd)

    def mtp_nic_fix_vrm(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.ORTANO2:
            if not self._nic_ctrl_list[slot].nic_fix_vrm():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(MFG_DIAG_CMDS.ORTANO2_VRM_FIX_FMT))
                err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
                self.mtp_dump_err_msg(err_msg)
                return False
        return True

    def mtp_nic_naples25swm_alom_cable_signal_test(self, slot, highpowertest):
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_alom_cable_signal_test(errlist, highpowertest)
        if rc == False:
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        return rc

    def mtp_nic_naples25swm_high_power_mode_test(self, slot):
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_high_power_mode_test(errlist)
        if rc == False:
            self.cli_log_slot_err(slot, "NIC NAPLES25SWM HIGH POWER MODE TEST FAILED")
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        else:
            self.cli_log_slot_inf(slot, "NIC NAPLES25SWM HIGH POWER MODE TEST PASSED")
        return rc

    def mtp_nic_naples25swm_low_power_mode_test(self, slot):
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_low_power_mode_test(errlist)
        if rc == False:
            self.cli_log_slot_err(slot, "NIC NAPLES25SWM LOW POWER MODE TEST FAILED")
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        else:
            self.cli_log_slot_inf(slot, "NIC NAPLES25SWM LOW POWER MODE TEST PASSED")
        return rc

    def mtp_nic_naples25swm_cpld_spi_to_smb_reg_test(self, slot):
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_cpld_reg_test(errlist)
        if rc == False:
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        return rc

    def mtp_nic_naples25ocp_signal_test(self, slot):
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25ocp_signal_test(errlist)
        if rc == False:
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        return rc

    def mtp_nic_naples25swm_mgmt_port_test(self, slot):
        rc = self._nic_ctrl_list[slot].nic_naples25swm_mgmt_port_test(slot)

    def mtp_mgmt_check_cpld_debug_bits(self, slot):
        """
            Dump registers 0xa, 0x12, 0x24
        """
        for reg_addr in [0xa, 0x12, 0x24]:
            cmd = MFG_DIAG_CMDS.MTP_SMB_SEL_FMT.format(slot+1) + " ;" + MFG_DIAG_CMDS.MTP_SMB_RD_CPLD_FMT.format(reg_addr, slot+1)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                # try again one more time
                time.sleep(1)
                if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                    self.cli_log_slot_err(slot, self._nic_ctrl_list[slot].nic_get_cmd_buf())
                    continue

    def mtp_run_diag_test_para_lock(self):
        self._test_lock.acquire()


    def mtp_run_diag_test_para_unlock(self):
        self._test_lock.release()


    def mtp_run_diag_test_para(self, slot, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None):
        # init command
        if init_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, init_cmd):
                err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # log the timestamp in diag log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started - at {:s}".format(test, str(start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)

        # run diag test
        if not self.mtp_mgmt_exec_cmd_para(slot, diag_cmd, timeout=MTP_Const.DIAG_TEST_TIMEOUT):
            err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
            return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # diag test error ouput
        err_msg_list = list()
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        if MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG in cmd_buf:
            for line in cmd_buf.split('\n'):
                if MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG in line:
                    err_msg = line.replace('\r', '')
                    err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_DIAG_ERR_MSG_SIG):]
                    err_msg_list.append(err_msg)

        # log the timestamp in diag log
        stop = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Stopped - at {:s} - duration {:s}".format(test, str(stop), str(stop-start))
        ts_record_cmd = "######## {:s} ########".format(ts_record)
        self.mtp_mgmt_exec_cmd_para(slot, ts_record_cmd)

        # post command
        if post_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, post_cmd):
                err_msg = self._nic_ctrl_list[slot].nic_get_err_msg()
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        ret = self.mtp_mgmt_get_test_result_para(slot, rslt_cmd, test)
        return [ret, err_msg_list]


    def mtp_barcode_scan(self, present_check=True, swmtestmode=Swm_Test_Mode.SWMALOM):
        mtp_scan_rslt = dict()
        mtp_ts_snapshot = libmfg_utils.get_timestamp()
        mtp_scan_rslt["MTP_ID"] = self._id
        mtp_scan_rslt["MTP_TS"] = mtp_ts_snapshot
        valid_nic_key_list = list()

        unscanned_nic_key_list = list()
        scan_nic_key_list = list()
        scan_sn_list = list()
        scan_mac_list = list()
        scan_atom_sn_list = list()

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

            #Scan SN loop
            sn = "0"
            mac = "000000000000"
            pn = "0"
            if swmtestmode != Swm_Test_Mode.ALOM:
                while True:
                    usr_prompt = "Please Scan {:s} Serial Number Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    sn = libmfg_utils.serial_number_validate(raw_scan)
                    if not sn:
                        self.cli_log_err("Invalid NIC Serial Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                        #return None
                    elif sn in scan_sn_list:
                        self.cli_log_err("NIC Serial Number: {:s} is double scanned, please restart the scan process\n".format(sn), level=0)
                        #return None
                    else:
                        scan_sn_list.append(sn)
                        break

                #Scan Mac Loop
                while True:
                    usr_prompt = "Please scan {:s} MAC Address Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    mac = libmfg_utils.mac_address_validate(raw_scan)
                    if not mac:
                        self.cli_log_err("Invalid NIC MAC Address: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                        #return None
                    elif mac in scan_mac_list:
                        mac_ui = libmfg_utils.mac_address_format(mac)
                        self.cli_log_err("NIC MAC Address: {:s} is double scanned, please restart the scan process\n".format(mac_ui), level=0)
                        #return None
                    else:
                        scan_mac_list.append(mac)
                        break

                #Scan PN Loop
                while True:
                    usr_prompt = "Please scan {:s} Part Number Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    pn = libmfg_utils.part_number_validate(raw_scan)
                    if not pn:
                        self.cli_log_err("Invalid NIC Part Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                        #return None
                    else:
                        break
                #Scan ALOM SN Loop
                alom_sn = None
                alom_pn = None


            if swmtestmode == Swm_Test_Mode.ALOM:  #if only scanning Alom we need to manually put in the SWM part number
                pn="000000-000"

            if pn == '000000-000':
                while True:
                    usr_prompt = "Please Scan {:s} ALOM Serial Number Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    alom_sn = libmfg_utils.serial_number_validate(raw_scan)
                    if not alom_sn:
                        self.cli_log_err("Invalid ALOM Serial Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                    #return None
                    elif alom_sn in scan_atom_sn_list:
                        self.cli_log_err("ALOM Serial Number: {:s} is double scanned, please restart the scan process\n".format(sn), level=0)
                    #return None
                    else:
                        scan_atom_sn_list.append(alom_sn)
                        break
                #Scan ALOM PN Loop
                
                while True:
                    usr_prompt = "Please scan {:s} ALOM Part Number Barcode:".format(key)
                    raw_scan = raw_input(usr_prompt)
                    alom_pn = libmfg_utils.part_number_validate(raw_scan)
                    if not alom_pn:
                        self.cli_log_err("Invalid ALOM Part Number: {:s} detected, please restart the scan process\n".format(raw_scan), level=0)
                    #return None
                    else:
                        break

            nic_scan_rslt["NIC_VALID"] = True
            nic_scan_rslt["NIC_SN"] = sn
            nic_scan_rslt["NIC_MAC"] = mac
            nic_scan_rslt["NIC_PN"] = pn
            nic_scan_rslt["NIC_TS"] = libmfg_utils.get_fru_date()
            if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
                nic_scan_rslt["SN_ALOM"] = alom_sn
                nic_scan_rslt["PN_ALOM"] = alom_pn
            mtp_scan_rslt[key] = nic_scan_rslt

        nic_empty_list = list(set(valid_nic_key_list).difference(set(scan_nic_key_list)))
        for key in nic_empty_list:
            nic_scan_rslt = dict()
            nic_scan_rslt["NIC_VALID"] = False
            mtp_scan_rslt[key] = nic_scan_rslt

        return mtp_scan_rslt


    # generate the local barcode config file
    def gen_barcode_config_file(self, file_p, scan_rslt, swmtestmode=Swm_Test_Mode.ALOM):
        config_lines = [str(scan_rslt["MTP_ID"]) + ":"]
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
                tmp = "        PN: \"" + scan_rslt[key]["NIC_PN"] + "\""
                config_lines.append(tmp)
                tmp = "        TS: \"" + scan_rslt[key]["NIC_TS"] + "\""
                config_lines.append(tmp)
                pn = scan_rslt[key]["NIC_PN"]
                if pn == '000000-000':
                    tmp = "        SN_ALOM: \"" + scan_rslt[key]["SN_ALOM"] + "\""
                    config_lines.append(tmp)
                    tmp = "        PN_ALOM: \"" + scan_rslt[key]["PN_ALOM"] + "\""
                    config_lines.append(tmp)

            else:
                tmp = "        VALID: \"No\""
                config_lines.append(tmp)

        for line in config_lines:
            file_p.write(line + "\n")

    def uut_chassis_shutdown(self):
        return self.mtp_chassis_shutdown(mtp=False)

    def uut_powercycle(self):
        # self.cli_log_inf("Disconnect UUT chassis...", level=0)
        # self.mtp_console_disconnect()
        if not self.mtp_power_cycle(mtp=False):
            self.cli_log_err("Unable to reboot UUT Chassis", level=0)
            return False
        else:
            self.cli_log_inf("UUT Chassis is power cycled", level=0)
        if not self.mtp_console_connect():
            self.cli_log_err("Unable to connect UUT Chassis", level=0)
            #powercycle one more time
            if not self.mtp_power_cycle(mtp=False):
                self.cli_log_err("Unable to reboot UUT Chassis", level=0)
                return False
            if not self.mtp_console_connect():
                return False
        self.cli_log_inf("UUT Chassis is connected", level=0)
        return True

    def uut_powercycle_with_intr(self):
        # self._mgmt_handle.close()
        if self._mgmt_handle is not None:
            self.mtp_console_disconnect()
        telnet_cmd = self.mtp_get_telnet_command()
        telnet_cmd = telnet_cmd[:-4]+"20"+telnet_cmd[-2:] #replace port 40xx with 20xx
        self._mgmt_handle = pexpect.spawn(telnet_cmd, logfile_read=self._diag_filep)
        while libmfg_utils.mfg_expect(self._mgmt_handle, ["Connection refused"], timeout=1) == 0:
            self._mgmt_handle.close()
            self._mgmt_handle = pexpect.spawn(telnet_cmd, logfile_read=self._diag_filep)
        self._mgmt_handle.setecho(True)

        self.cli_log_inf("Power off APC", level=0)
        self.mtp_apc_pwr_off()
        libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
        self.mtp_apc_pwr_on()
        self.cli_log_inf("Power on APC", level=0)

        idx = -1
        while idx < 0:
            # time.sleep(3)
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["System is initializing"], timeout=MTP_Const.TOR_POWER_ON_DELAY)
            print("waiting for System is initializing")
            print(idx)
        
        idx = -1
        while idx < 0:
            ret = self._mgmt_handle.send('\x1b')    # trying
            ret = self._mgmt_handle.send('\x03')
            ret = self._mgmt_handle.send('\x1b')    # trying
            ret = self._mgmt_handle.send('c')       # trying
            # ret = self._mgmt_handle.expect("Created symlink")
            # print(ret)
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Created symlink"], timeout=10)
            print("waiting for Created symlink")
            print(idx)
            time.sleep(7)

        if not self.mtp_console_connect():
            self.cli_log_err("Failed to login after powercycle", level=0)
            return False

        return True

    def tor_usb_boot(self):
        """ Stop at BIOS screen and select USB boot """
        if self._mgmt_handle is not None:
            self.mtp_console_disconnect()
        print(self._mgmt_handle)
        telnet_cmd = self.mtp_get_telnet_command()
        telnet_cmd = telnet_cmd[:-4]+"20"+telnet_cmd[-2:] #replace port 40xx with 20xx
        self._mgmt_handle = pexpect.spawn(telnet_cmd, logfile = sys.stdout)
        while libmfg_utils.mfg_expect(self._mgmt_handle, ["Connection refused"], timeout=1) == 0:
            self._mgmt_handle.close()
            self._mgmt_handle = pexpect.spawn(telnet_cmd, logfile = sys.stdout)
        self._mgmt_handle.setecho(True)

        while True:
            self.cli_log_inf("Power off APC", level=0)
            self.mtp_apc_pwr_off()
            libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
            self.mtp_apc_pwr_on()
            self.cli_log_inf("Power on APC", level=0)

            # Keep pressing Esc
            idx = -1
            while idx < 0:
                self._mgmt_handle.send("\x1b")
                idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Esc is pressed", "Looking for SvOS."], timeout=0.5)
                print("Esc key")
                print(idx)
                if idx == 1:
                    self.cli_log_inf("Power off APC", level=0)
                    self.mtp_apc_pwr_off()
                    libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
                    self.mtp_apc_pwr_on()
                    self.cli_log_inf("Power on APC", level=0)
            
            # Go to Boot Menu -> EFI USB
            idx = -1
            while idx < 0:
                ret = self._mgmt_handle.send('\x1b[B')  # Down
                idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["you to the Boot Manager"])
            ret = self._mgmt_handle.send('\r')      # Enter
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["EFI USB"], timeout=3)
            if idx < 0:
                self.cli_log_err("No USB detected")
                return False
            ret = self._mgmt_handle.send('\x1b[2B') # Down x2 to USB
            ret = self._mgmt_handle.send('\r')      # Enter

        self.cli_log_inf("Wait {:d} seconds for system coming up".format(MTP_Const.TOR_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.TOR_POWER_ON_DELAY)

        if not self.mtp_console_connect():
            self.cli_log_err("Failed to connect console", level=0)
            return False

        return True

    def tor_boot_select(self, selection=0, stopreboot=True, secure_login=False, fru_valid=True):

        # if selection > 0:
        #     secure_login = True
        #     self._secure_login = True

        for x in range(3):
            if self.tor_boot_select_secondlevel(selection,stopreboot=stopreboot,secure_login=secure_login):
                # read FRU as soon as console is ready, to have an SN to save logs to.
                if fru_valid:
                    if not self.tor_fru_init():
                        return False
                if selection > 0:
                    if not self.tor_boot_devices_ready():
                        return False
                return True
            else:
                self.cli_log_inf("Cannot Get UUT console, will Power cycle", level=0)

        # if secure_login:
        #     self._secure_login = False

        return False

    def tor_boot_select_secondlevel(self, selection=0, stopreboot=True, secure_login=False):
        """ Stop at OS selection screen and choose """

        if isinstance(selection, str):
            selection = int(selection)

        self.cli_log_inf("Power off APC", level=0)
        self.mtp_apc_pwr_off()
        libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)

        if not libmfg_utils.mtp_clear_console(self):
            return False

        self.mtp_apc_pwr_on()
        self.cli_log_inf("Power on APC", level=0)

        # reconnect console after powerup instead of before; 
        # SLC 8xxx console line disconnects when unit is powered on
        if self._mgmt_handle is not None:
            self.mtp_console_disconnect()
        telnet_cmd = self.mtp_get_telnet_command()
        telnet_cmd = telnet_cmd[:-4]+"20"+telnet_cmd[-2:] #replace port 40xx with 20xx
        self._mgmt_handle = pexpect.spawn(telnet_cmd, logfile = self._diag_filep)
        countconnectrefusedissue = 10
        while libmfg_utils.mfg_expect(self._mgmt_handle, ["Connection refused"], timeout=1) == 0:
            if not libmfg_utils.mtp_clear_console(self):
                return False
            self._mgmt_handle.close()
            self._mgmt_handle = pexpect.spawn(telnet_cmd)
            countconnectrefusedissue -= 1
            if countconnectrefusedissue < 0:
                return False
        self._mgmt_handle.setecho(True)

        self.mtp_apc_pwr_on()
        self.cli_log_inf("Power on APC", level=0)

        # Keep entering selection number
        idx = -1
        start=datetime.now()
        starttosendselection = True
        waittimetopowercycleretry = MTP_Const.TOR_POWER_ON_DELAY
        # if secure_login:
        #     waittimetopowercycleretry = 1800
        #     self.cli_log_inf("OS UPGRADE IMAGE PROCESS, WILL TAKE LONG TIME.", level=0)
        waittimetopowercycleretry = 1800
        
        if selection == 0:
            self.cli_log_inf("Booting to SvOS", level=0)
        else:
            self.cli_log_inf("Booting to CX-OS", level=0)

        while True:
            if starttosendselection:
                self._mgmt_handle.send(str(selection))
            else:
                self._mgmt_handle.sendline()
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["ServiceOS login:", " login:", "Select profile","Looking for SvOS.", "Starting update"], timeout=1)
            difftime = datetime.now()-start
            seconds = difftime.total_seconds()
            #print("{} vs {} : {} s".format(idx, selection, seconds))
            if seconds > waittimetopowercycleretry:
                self.cli_log_err("Failed to get UUT console Login or Select profile prompt in {} ({}) seconds".format(seconds,waittimetopowercycleretry) , level=0)
                return False
            if idx < 0:
                continue
            elif idx == 2:
                self._mgmt_handle.sendline(str(selection))
                #start=datetime.now()
                starttosendselection = False
            elif idx == 3:
                start=datetime.now()
                #pass
            elif idx == selection:
                break
            # elif idx == 4:
            #     #start=datetime.now()
            #     self.cli_log_inf("Get the \"Looking for SvOS\" begin Console message", level=0)
            #     starttosendselection = True
            #     continue
            elif idx == 4:
                continue
            elif idx != selection:
                self.cli_log_inf("Power off APC", level=0)
                self.mtp_apc_pwr_off()
                libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
                self.mtp_apc_pwr_on()
                self.cli_log_inf("Power on APC", level=0)

        if not self.mtp_console_connect():
            self.cli_log_err("Failed to connect console", level=0)
            return False

        if selection > 0:
            self.mtp_mgmt_exec_cmd("ovs-appctl -t hpe-cardd park_chassis 1", timeout=10)

            # get IP
            if not self.tor_get_ip():
                self.cli_log_err("Failed to obtain IP", level=0)
                return False

            # switch to ssh
            if not self.mtp_mgmt_connect(prompt_cfg=True):
                self.cli_log_err("Unable to connect UUT chassis", level=0)
                return False

        if selection == 0:
            if not self.svos_usb_mount():
                self.cli_log_err("Unable to mount usb", level=0)
                return False
            if not self.mtp_console_enter_shell("sh"):
                self.cli_log_err("Unable to init bash shell", level=0)
                return False

        return True

    def tor_boot_devices_ready(self):
        """
        Usually takes 2-3 minutes for Elbas to be 'ready' or 'down'
        In case of the Elba ssh dir issue, it would take 10 minutes.
        """
        start=datetime.now()
        # if stopreboot and not self._secure_login:
        self.mtp_mgmt_exec_cmd("ovs-appctl -t hpe-cardd park_chassis 1", timeout=10)
        self.cli_log_inf("Wait for {} (s) for NIC boot up".format(MTP_Const.TOR_LAGS_POWER_ON_DELAY))
        elba0_ready, elba1_ready, gearbox_ready = False, False, False
        while False in (elba0_ready, elba1_ready, gearbox_ready):
            if False in (elba0_ready, elba1_ready):
                self.mtp_mgmt_exec_cmd("vtysh -c \"show dsm\"", timeout=10)
                sig1 = "ready"
                sig2 = "down"
                cmd_buf = self.mtp_get_cmd_buf()
                if cmd_buf is not None:
                    for line in cmd_buf.splitlines():
                        if "DSS-4825-6100" in line and (sig1 in line or sig2 in line):
                            if "1/1" in line:
                                elba0_ready = True
                            if "1/2" in line:
                                elba1_ready = True
                    if elba0_ready and elba1_ready:
                        self.cli_log_inf("LAGs ready")
                    if not self.mtp_mgmt_exec_cmd("date", sig_list=["UTC"], timeout=10):
                        return False

            if not gearbox_ready:
                self.mtp_mgmt_exec_cmd("vtysh -c \"show module 1/1\"", timeout=10)
                gearbox_sig = "Line module 1/1 is ready"
                cmd_buf = self.mtp_get_cmd_buf()
                if cmd_buf is not None:
                    for line in cmd_buf.splitlines():
                        if gearbox_sig in line:
                            gearbox_ready = True
                            self.cli_log_inf("TD3/GB/retimer module ready")

            difftime = datetime.now()-start
            seconds = difftime.total_seconds()
            if seconds > MTP_Const.TOR_LAGS_POWER_ON_DELAY:
                break
            sys.stdout.write("Time left: {:03d} seconds....\r".format(int(MTP_Const.TOR_LAGS_POWER_ON_DELAY - seconds)))
            sys.stdout.flush()
            time.sleep(5)

        self.mtp_mgmt_exec_cmd("vtysh -c \"show environment\"", timeout=10)

        if not elba0_ready:
            self.cli_log_slot_err(0, "Elba0 initialization timed out")
            return False
        if not elba1_ready:
            self.cli_log_slot_err(1, "Elba1 initialization timed out")
            return False
        if not gearbox_ready:
            self.cli_log_err("TD3/GB/retimer initialization timed out", level=0)
            return False

        return True

    def tor_bios_config_tpm(self):
        """
        Shell> fs0:
        FS0:\> TPMFactoryUpd.efi -update config-file -config TPM12_latest.cfg

          **********************************************************************
          *    Infineon Technologies AG   TPMFactoryUpd   Ver 01.01.2212.00    *
          **********************************************************************

               TPM update information:
               -----------------------
               Firmware valid                    :    Yes
               TPM family                        :    1.2
               TPM enabled                       :    Yes
               TPM activated                     :    Yes
               TPM owner set                     :    No
               TPM deferred physical presence    :    No (Settable)
               TPM firmware version              :    6.43.243.0
               Remaining updates                 :    64
               New firmware valid for TPM        :    No
               The current TPM firmware version is already up to date!

        Shell> TPMFactoryUpd.efi -info
          **********************************************************************
          *    Infineon Technologies AG   TPMFactoryUpd   Ver 01.01.2212.00    *
          **********************************************************************

               TPM information:
               ----------------
               Firmware valid                    :    Yes
               TPM family                        :    1.2
               TPM firmware version              :    6.43.243.0
               TPM enabled                       :    Yes
               TPM activated                     :    Yes
               TPM owner set                     :    No
               TPM deferred physical presence    :    No (Settable)
               Remaining updates                 :    64

        POWER CYCLE TAORMINA AND GO BACK INTO THE EFI SHELL

        Shell> fs0:
        Shell> TPMFactoryUpd.efi -tpm12-clearownership
          **********************************************************************
          *    Infineon Technologies AG   TPMFactoryUpd   Ver 01.01.2212.00    *
          **********************************************************************

               TPM1.2 Clear Ownership:
               -----------------------
               Clear TPM1.2 Ownership operation failed. (0xE0295523)

          ----------------------------------------------------------------------
          *    Error Information                                               *
          ----------------------------------------------------------------------

          Error Code:     0xE0295523
          Message:        TPM1.2: The TPM has no owner.

        Shell> TPMFactoryUpd.efi -info
        """
        if self._tpm_skip:
            #SKIP
            return True

        self.cli_log_inf("Use BIOS mode to config/enable TPM")

        if not self.tor_boot_bios():
            return False

        if not self.tor_bios_enableTPM():
            return False

        #time.sleep(5)

        if not self.tor_boot_bios():
            return False

        #if not self.tor_enter_bios_after_softreset():
        #    return False

        if not self.tor_bios_efi():
            return False

        if not self.tor_bios_efi_tpmfactory_update():
            return False
        #sys.exit()

        if not self.tor_boot_bios():
            return False

        if not self.tor_bios_efi():
            return False

        if not self.tor_bios_efi_tpmfactory_clear():
            return False
        #sys.exit()
        if not self.tor_boot_bios():
            return False

        if not self.tor_bios_enableTPM():
            return False

        time.sleep(5)

        return True

    def tor_enter_bios_after_softreset(self):
        """ Stop at OS selection screen and choose """
        self.cli_log_inf("ENTER TO BIOS MODE AFTER SOFTRESET", level=0)
        libmfg_utils.count_down_by_time(15)

        if not libmfg_utils.mtp_clear_console(self):
            return False

        if self._mgmt_handle is not None:
            self.mtp_console_disconnect()
        telnet_cmd = self.mtp_get_telnet_command()
        telnet_cmd = telnet_cmd[:-4]+"20"+telnet_cmd[-2:] #replace port 40xx with 20xx
        self._mgmt_handle = pexpect.spawn(telnet_cmd, logfile = self._diag_filep)
        while libmfg_utils.mfg_expect(self._mgmt_handle, ["Connection refused"], timeout=1) == 0:
            self._mgmt_handle.close()
            self._mgmt_handle = pexpect.spawn(telnet_cmd)
        self._mgmt_handle.setecho(True)

        idx = -1
        start=datetime.now()
        starttosendselection = True
        countpowercycle = 0
        while True:
            if starttosendselection:
                self._mgmt_handle.send('\x1b')

            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Front Page", "Press Esc", "Looking for SvOS."], timeout=1)
            difftime = datetime.now()-start
            seconds = difftime.total_seconds()
            #print("{} : {} s".format(idx, seconds))
            if seconds > MTP_Const.TOR_POWER_ON_DELAY:
                self.cli_log_err("Failed to get UUT boot to BIOS mode in {} ({}) seconds".format(seconds,MTP_Const.TOR_POWER_ON_DELAY) , level=0)
                return False
            if idx < 0:
                continue
            elif idx == 0:
                self.cli_log_inf("LOGIN BIOS section", level=0)
                time.sleep(2)
                break
            elif idx == 1:
                start=datetime.now()
                self.cli_log_inf("Get the \"Press Esc for boot\" begin Console message", level=0)
                self._mgmt_handle.send('\x1b')
                continue
            elif idx == 2:
                countpowercycle += 1
                self.cli_log_inf("Get \"Looking for SvOS\" message, powercycle to re-try login BIOS<{}>".format(countpowercycle), level=0)
                self.cli_log_inf("Power off APC", level=0)
                self.mtp_apc_pwr_off()
                libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
                self.mtp_apc_pwr_on()
                self.cli_log_inf("Power on APC", level=0)


        #self.tor_bios_enableTPM()

        return True

    def tor_boot_bios(self):

        for x in range(3):
            if self.tor_boot_bios_secondlevel():
                return True
            else:
                self.cli_log_inf("Cannot Get UUT console, will Power cycle", level=0)

        return False

    def tor_boot_bios_secondlevel(self):
        """ Stop at OS selection screen and choose """
        self.cli_log_inf("BOOT TO BIOS MODE", level=0)
        self.cli_log_inf("Power off APC", level=0)
        self.mtp_apc_pwr_off()
        libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)

        if not libmfg_utils.mtp_clear_console(self):
            return False

        if self._mgmt_handle is not None:
            self.mtp_console_disconnect()
        telnet_cmd = self.mtp_get_telnet_command()
        telnet_cmd = telnet_cmd[:-4]+"20"+telnet_cmd[-2:] #replace port 40xx with 20xx
        self._mgmt_handle = pexpect.spawn(telnet_cmd, logfile = self._diag_filep)
        while libmfg_utils.mfg_expect(self._mgmt_handle, ["Connection refused"], timeout=1) == 0:
            self._mgmt_handle.close()
            self._mgmt_handle = pexpect.spawn(telnet_cmd)
        self._mgmt_handle.setecho(True)

        self.mtp_apc_pwr_on()
        self.cli_log_inf("Power on APC", level=0)

        #libmfg_utils.mfg_expect(self._mgmt_handle, ["Looking for SvOS."], timeout=MTP_Const.TOR_POWER_ON_DELAY)
        # Keep entering selection number
        idx = -1
        start=datetime.now()
        starttosendselection = True
        countpowercycle = 0
        while True:
            if starttosendselection:
                self._mgmt_handle.send('\x1b')

            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Front Page", "Press Esc", "Looking for SvOS."], timeout=1)
            difftime = datetime.now()-start
            seconds = difftime.total_seconds()
            #print("{} : {} s".format(idx, seconds))
            if seconds > MTP_Const.TOR_POWER_ON_DELAY:
                self.cli_log_err("Failed to get UUT boot to BIOS mode in {} ({}) seconds".format(seconds,MTP_Const.TOR_POWER_ON_DELAY) , level=0)
                return False
            if idx < 0:
                continue
            elif idx == 0:
                self.cli_log_inf("LOGIN BIOS section", level=0)
                time.sleep(2)
                break
            elif idx == 1:
                #start=datetime.now()
                self.cli_log_inf("Get the \"Press Esc for boot\" begin Console message", level=0)
                self._mgmt_handle.send('\x1b')
                continue
            elif idx == 2:
                countpowercycle += 1
                self.cli_log_inf("Get \"Looking for SvOS\" message, powercycle to re-try login BIOS<{}>".format(countpowercycle), level=0)
                self.cli_log_inf("Power off APC", level=0)
                self.mtp_apc_pwr_off()
                libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
                self.mtp_apc_pwr_on()
                self.cli_log_inf("Power on APC", level=0)


        #self.tor_bios_enableTPM()

        return True

    def tor_bios_enableTPM(self):
        self.cli_log_inf("ENABLE TPM AT BIOS MODE", level=0)
        self.tor_bios_down()
        self.tor_bios_down()
        self.tor_bios_down()
        self.tor_bios_down()
        self.tor_bios_down()
        self.tor_bios_enter()
        self.tor_bios_right()
        self.tor_bios_right()
        self.tor_bios_down()
        self.tor_bios_enter()
        self.tor_bios_down()
        self.tor_bios_down()
        self.tor_bios_enter()
        self.tor_bios_right()
        self.tor_bios_right()
        self.tor_bios_right()
        self.tor_bios_enter()
        self.tor_bios_enter()

        return True

    def tor_bios_efi(self):
        self.cli_log_inf("ENTER TO EFI MODE", level=0)
        if not self.tor_bios_down():
            return False
        if not self.tor_bios_enter():
            return False
        if not self.tor_bios_down():
            return False
        if not self.tor_bios_enter():
            return False
        if not self.tor_bios_enter():
            return False
        if not self.tor_bios_send_cmd_in_efi_mode(cmd="",sendcmdwait=5):
            return False
        #print(self._cmd_buf)
        if not self.tor_bios_send_cmd_in_efi_mode(cmd="fs0:",selectmode=1,sendcmdwait=5):
            return False
        #print(self._cmd_buf)
        return True

    def tor_bios_send_cmd_in_efi_mode(self,cmd="",timeout=60,selectmode=0,sendcmdwait=0):

        self._mgmt_handle.before = ""
        self._mgmt_handle.buffer = ""
        self._mgmt_handle.send(cmd)
        self._mgmt_handle.send('\x0d')
        libmfg_utils.count_down_by_time(sendcmdwait)
        start=datetime.now()
        modelist = ["SHELL", "FS0:"]
        while True:        
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Shell>", "FS0:\\>"], timeout=1)
            #print("IDX: {}".format(idx))
            difftime = datetime.now()-start
            seconds = int(difftime.total_seconds())
            #print(seconds)
            #if seconds % 5 == 0:
                #self._mgmt_handle.send('\x0d')
            if seconds > timeout:
                self.cli_log_err("Failed to get {} mode in {} ({}) seconds".format(modelist[selectmode],seconds,timeout) , level=0)
                return False
            if idx < 0:
                continue
            elif idx == selectmode:
                self.cli_log_inf("ENTER TO {} mode".format(modelist[selectmode], level=0))
                break
        self._cmd_buf = self._mgmt_handle.before
        return True

    def tor_bios_efi_tpmfactory_update(self):
        self.cli_log_inf("TPM FACTORY UPDATE AT EFI MODE", level=0)
        self.tor_bios_send_cmd_in_efi_mode(selectmode=1,sendcmdwait=2)
        self.tor_bios_send_cmd_in_efi_mode(selectmode=1,sendcmdwait=2)
        #self.mtp_mgmt_exec_cmd("TPMFactoryUpd.efi -update config-file -config TPM12_latest.cfg", sig_list=[">"], timeout=120)
        #self._mgmt_handle.send('TPMFactoryUpd.efi -update config-file -config TPM12_latest.cfg')
        self.tor_bios_send_cmd_in_efi_mode(cmd='TPMFactoryUpd.efi -update config-file -config TPM12_latest.cfg',selectmode=1,sendcmdwait=20)
        #print(self._cmd_buf)
        #self._mgmt_handle.send('TPMFactoryUpd.efi -info')
        self.tor_bios_send_cmd_in_efi_mode(selectmode=1,sendcmdwait=2)
        self.tor_bios_send_cmd_in_efi_mode(selectmode=1,sendcmdwait=2)
        self.tor_bios_send_cmd_in_efi_mode(cmd='TPMFactoryUpd.efi -info',selectmode=1,sendcmdwait=20)
        cmd_buf = self._cmd_buf
        enabled_match = re.match("TPM enabled .*:.* Yes", cmd_buf)
        if enabled_match:
            return True
        else:
            self.cli_log_err("Cannot see TPM enabled")
            return False

    def tor_bios_efi_tpmfactory_clear(self):
        self.cli_log_inf("tor_bios_efi_tpmfactory_setup", level=0)
        self.tor_bios_send_cmd_in_efi_mode(selectmode=1,sendcmdwait=2)
        self.tor_bios_send_cmd_in_efi_mode(selectmode=1,sendcmdwait=2)
        self.tor_bios_send_cmd_in_efi_mode(cmd='TPMFactoryUpd.efi -tpm12-clearownership',selectmode=1,sendcmdwait=20)
        self.tor_bios_send_cmd_in_efi_mode(selectmode=1,sendcmdwait=2)
        self.tor_bios_send_cmd_in_efi_mode(selectmode=1,sendcmdwait=2)
        self.tor_bios_send_cmd_in_efi_mode(cmd='TPMFactoryUpd.efi -info',selectmode=1,sendcmdwait=20)

        cmd_buf = self._cmd_buf
        enabled_match = re.match("TPM owner set .*:.* No", cmd_buf)
        if enabled_match:
            return True
        else:
            self.cli_log_err("Cannot see TPM ownership cleared")
            return False

    def tor_bios_enter(self):
        # :down
        #     send $0d
        #     pause 1
        #     return
        self._mgmt_handle.send('\x0d')
        time.sleep(2)

        return True

    def tor_bios_up(self):
        # :up
        #     send $1b $5b $41
        #     pause 1
        #     return
        self._mgmt_handle.send("\x1b\x5b\x41")
        time.sleep(1)

        return True

    def tor_bios_left(self):
        # :left
        #     send $1b $5b $44
        #     pause 1
        #     return
        self._mgmt_handle.send("\x1b\x5b\x44")
        time.sleep(1)

        return True

    def tor_bios_right(self):
        # :right
        #     send $1b $5b $43
        #     pause 1
        #     return
        self._mgmt_handle.send("\x1b\x5b\x43")
        time.sleep(1)

        return True

    def tor_bios_down(self):
        # :down
        #     send $1b $5b $42
        #     pause 1
        #     return
        self._mgmt_handle.send("\x1b\x5b\x42")
        time.sleep(1)

        return True

    def tor_ssd_format(self):
        return self.tor_prepare_eeupdate(ssd_format=True, usb_method=True)

    def tor_prepare_eeupdate(self, ssd_format=False, usb_method=False):
        if not usb_method: # copying from USB vs copying from network
            usb_tarball = TOR_IMAGES.usb_tarball[self.uut_type]
            self.cli_log_inf("Downloading USB tarball")
            if not self.mtp_mgmt_exec_cmd("tftp -g -r {:s}/{:s} {:s} -b 65000".format(TOR_IMAGES.TFTP_SERVER_DIR, usb_tarball, TOR_IMAGES.TFTP_SERVER_IP), sig_list=["100%"]):
                return False
            self.mtp_mgmt_exec_cmd("tar xf /cli/fs/home/{:s} -C /".format(usb_tarball))

        if ssd_format:
            if not self.mtp_mgmt_exec_cmd("/usr/bin/storage_fdisk_format.sh", sig_list=["Removed /run"]):
                self.cli_log_err("Unable to storage fdisk format", level=0)
                return False
        self.mtp_mgmt_exec_cmd("mkdir -p {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH))
        
        if usb_method:
            self.cli_log_inf("Mounting USB")
            self.mtp_mgmt_exec_cmd("mkdir -p /mnt/usb")
            self.mtp_mgmt_exec_cmd("mount /dev/sdb2 /mnt/usb")
            self.mtp_mgmt_exec_cmd("cp /mnt/usb/bin/* {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH))
            time.sleep(1)
            self.mtp_mgmt_exec_cmd("sync")
            self.mtp_mgmt_exec_cmd("umount /dev/sdb2")
        else:
            self.mtp_mgmt_exec_cmd("cp /Taormina-USB-small/bin/* {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH))
            time.sleep(1)
            if "No such file" in self.mtp_get_cmd_buf():
                return False

        self.mtp_mgmt_exec_cmd("sync")
        # self.mtp_mgmt_exec_cmd("exit")
        return True

    def svos_usb_mount(self):
        """ 
            Already need to be in svcli for this function
            as mount usb needs to be done in original svos shell (fresh boot), not an svcli later down the stack
        """
        self.mtp_mgmt_exec_cmd("mount usb")
        if not self.mtp_console_enter_shell("sh"):
            self.cli_log_err("Unable to init bash shell", level=0)
            return False
        self.mtp_mgmt_exec_cmd("lsusb")

        return True

    def i210_nic_prog(self):
        """ Setup i210 """
        i210_img = "Dev_Start_I210_Copper_NOMNG_4Mb_A2.bin"
        i210_prog_cmd = "./eeupdate64e.dat /nic=1 /d {:s}".format(i210_img)
        i210_pass_sig = "Shared Flash image updated successfully."
        self.mtp_mgmt_exec_cmd("cd {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH))
        if not self.mtp_mgmt_exec_cmd(i210_prog_cmd, sig_list=[i210_pass_sig], timeout=MTP_Const.TOR_I210_PROG_DELAY):
            return False
        time.sleep(1)   # NZ: is this needed?
        self.mtp_mgmt_exec_cmd("sync")
        # self.mtp_mgmt_exec_cmd("exit")
        return True

    def i210_mac_prog(self, fru_cfg):
        """ program mac to bring up network """
        # mac = libmfg_utils.mac_address_offset(fru_cfg["MAC"], 1) # base MAC plus 1
        mac = fru_cfg["MAC"]

        i210_prog_cmd = "./eeupdate64e.dat /nic=1 /mac={:s}".format(mac)
        i210_pass_sig = "Updating Checksum and CRCs...Done"
        self.mtp_mgmt_exec_cmd("cd {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH))
        if not self.mtp_mgmt_exec_cmd(i210_prog_cmd, sig_list=[i210_pass_sig]):
            return False

        self.mtp_mgmt_exec_cmd("sync")
        # self.mtp_mgmt_exec_cmd("exit")
        return True

    def tor_get_ip(self):
        cmd = "ifconfig eth0 | grep 'inet addr:'"
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=['inet addr'], timeout=60):
            self.cli_log_err("{:s} failed".format(cmd))
            return False
        cmd_buf = self.mtp_get_cmd_buf()
        ip_match = re.search("inet addr:((?:[0-9]{1,3}\.){3}[0-9]{1,3})", cmd_buf)

        if ip_match:
            self.cli_log_inf("Obtained IP {:s}".format(ip_match.group(1)))
            self._mgmt_cfg = list()
            self._mgmt_cfg.append(ip_match.group(1))
            self._mgmt_cfg.append("admin")
            self._mgmt_cfg.append("")
            return True
        else:
            return False
            

    def tor_mgmt_init(self, svos_boot=True):
        """
        if booted in svos, need to trigger ip dhcp.
        in halonos, ip acquired at startup.
        """
        retries = 3
        while retries >= 0:
            if retries == 0:
                self.cli_log_err(self.mtp_get_cmd_buf())
                return False
            retries -= 1
            if svos_boot:
                if not self.mtp_console_enter_shell("svcli"):
                    self.cli_log_err("Unable to init svos shell", level=0)
                    return False
                if not self.mtp_mgmt_exec_cmd("svcli", timeout=30):
                    self.cli_log_err("Couldn't run command ip dhcp")
                    continue
                if not self.mtp_mgmt_exec_cmd("ip dhcp", timeout=30):
                    self.cli_log_err("Couldn't run command ip dhcp")
                    continue
                if not self.mtp_mgmt_exec_cmd("ip show", sig_list=["IP Address"], timeout=30):
                    self.cli_log_err("Couldn't run command ip show")
                    continue
                if not self.mtp_console_enter_shell("sh"):
                    self.cli_log_err("Unable to init bash shell", level=0)
                    return False

            if not self.tor_get_ip():
                continue
            else:
                if not svos_boot:
                    if not self.mtp_mgmt_connect(prompt_cfg=True):
                        self.cli_log_err("Unable to ssh to UUT chassis, falling back to console")
                        if not self.mtp_console_connect():
                            self.cli_log_err("Unable to telnet to UUT chassis")
                            return False
                break
        return True

    def mtp_nic_flash_qspi(self, slot, qspi_image):
        self.cli_log_slot_inf(slot, "Flashing QSPI image")
        # cmd = "chmod 777 {:s}taorfpga".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)
        # if not self.mtp_mgmt_exec_cmd(cmd):
        #     self.cli_log_err("{:s} failed".format(cmd))
        #     return False
        cmd = "{:s}fpgautil elba {:s} flash writeimage allflash {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH, str(slot), qspi_image)
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Flashing Partition allflash passed"], timeout=MTP_Const.TOR_QSPI_PROG_DELAY):
            self.cli_log_slot_err(slot, "Programming Elba{:d} QSPI failed".format(slot))
            return False

        cmd = "{:s}fpgautil elba {:s} flash verifyimage allflash {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH, str(slot), qspi_image)
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Verification passed"], timeout=MTP_Const.TOR_QSPI_PROG_DELAY):
            self.cli_log_slot_err(slot, "Verifying Elba{:d} QSPI failed".format(slot))
            return False

        return True

    def tor_tpm_config_init(self):
        cmd = "cat /sys/class/tpm/tpm0/caps"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        self._tpm_dat = "0.0"
        match = re.search("Firmware version: ([\d.]+)", self.mtp_get_cmd_buf())
        if match:
            self._tpm_dat = match.group(1)
            return True
        else:
            self.cli_log_err("Unable to read TPM image, Will download it", level=0)
            return False

    def tor_svos_bio_tpm_config_image_setup(self, tpm_img):
        if not self.mtp_console_enter_shell("sh"):
            self.cli_log_err("Unable to init bash shell", level=0)
            return False

        if self.tor_tpm_config_init():
            exp_tpm = TOR_IMAGES.tpm_dat[self._uut_type]
            if self._tpm_dat == exp_tpm:
                # skip update
                # This is not update, it is unlock TPM
                # self._tpm_skip = True
                # return True
                pass
            #return False

        self.cli_log_inf("Downloading TPM CONFIG image")

        time.sleep(4)
        if not libmfg_utils.console_copy_file(self, TOR_IMAGES.TFTP_SERVER_IP, MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH, TOR_IMAGES.TFTP_SERVER_DIR+tpm_img):
            self.cli_log_err("Unable to get {:s}".format(tpm_img), level=0)
            return False
        time.sleep(10)
        self.mtp_mgmt_exec_cmd("cp {:s} /fs/selftest".format(tpm_img))
        self.mtp_mgmt_exec_cmd("cd /fs/selftest")
        self.mtp_mgmt_exec_cmd("tar xvf {:s}".format(tpm_img)) 
        self.mtp_mgmt_exec_cmd("sync")
        time.sleep(4)
        return True

    def tor_led_test(self, color):
        result = True

        self.mtp_mgmt_exec_cmd("cd /fs/selftest")
        self.mtp_mgmt_exec_cmd("./led.bash {}".format(color)) 
        libmfg_utils.aruba_gui_clear_buffer()
        self.cli_log_inf("DO YOU SEE LED COLOR CHANGE to {}?".format(color), level=0)
        result_input = raw_input("                                  YES/NO: ").replace(' ','')
        
        if result_input.upper() != "YES":
            result &= False

        if color.upper() == 'GREEN':
            self.cli_log_inf("CAN YOU FIND BLUE LED close to Console Port?".format(color), level=0)
            result_input = raw_input("                                  YES/NO: ").replace(' ','')
            
            if result_input.upper() != "YES":
                result &= False           

        self.cli_log_inf("CAN YOU CHECK SYSTEM FAN LED at BACK SIDE Color is {}?".format(color), level=0)
        result_input = raw_input("                                  YES/NO: ").replace(' ','')
        
        if result_input.upper() != "YES":
            result &= False
        
        return result

    def tor_svos_led_usb_setup(self, usb_img):

        self.cli_log_inf("Downloading USB image")

        time.sleep(4)
        if not libmfg_utils.console_copy_file(self, TOR_IMAGES.TFTP_SERVER_IP, MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH, TOR_IMAGES.TFTP_SERVER_DIR+usb_img):
            self.cli_log_err("Unable to get {:s}".format(usb_img), level=0)
            return False
        time.sleep(10)
        self.mtp_mgmt_exec_cmd("cp {:s} /fs/selftest".format(usb_img))
        self.mtp_mgmt_exec_cmd("cd /fs/selftest")
        self.mtp_mgmt_exec_cmd("tar xvf {:s}".format(usb_img)) 
        self.mtp_mgmt_exec_cmd("sync")
        time.sleep(4)
        return True

    def tor_check_fpgautil(self):
        util_img = TOR_IMAGES.TFTP_SERVER_DIR+"diag/util/fpgautil"

        cmd = "ls {:s}*".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        if "{:s}fpgautil".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH) not in self.mtp_get_cmd_buf():
            self.cli_log_inf("Downloading fpgautil")
            if not libmfg_utils.console_copy_file(self, TOR_IMAGES.TFTP_SERVER_IP, MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH, util_img):
                self.cli_log_err("Unable to get {:s}".format(util_img), level=0)
                return False

            cmd = "chmod 777 {:s}fpgautil".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("{:s} failed".format(cmd), level=0)
                return False

        return True

    def tor_nic_qspi_first_article(self):
        """ 
        1. Copy fpga util
        2. Copy spi image
        3. Flash spi image
        """

        qspi_img = TOR_IMAGES.first_article_img[self._uut_type]

        if not self.tor_check_fpgautil():
            return False

        self.cli_log_inf("Downloading QSPI {:s} image".format(article))
        time.sleep(4)
        if not libmfg_utils.console_copy_file(self, TOR_IMAGES.TFTP_SERVER_IP, MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH, TOR_IMAGES.TFTP_SERVER_DIR+qspi_img):
            self.cli_log_err("Unable to get {:s}".format(article), level=0)
            return False
        time.sleep(10)

        if not self.mtp_power_on_nic(pre_diag_method=True):
            self.cli_log_err("Failed to power on nic", level=0)
            return False

        for slot in range(0,2):
            if not self.mtp_nic_flash_qspi(slot, MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH+os.path.basename(qspi_img)):
                self.cli_log_err("qspi update failed for slot {:s}".format(str(slot)), level=0)
                return False

        if not self.mtp_power_cycle_nic(pre_diag_method=True):
            self.cli_log_err("Failed to power cycle nic", level=0)
            return False

        return True

    def tor_nic_qspi_prog(self):
        #using HPE terms for these. Pensando terms = boot0, ubootg, goldfw
        img_location = {
            "flash_boot0": TOR_IMAGES.flash_boot0[self._uut_type],
            "flash_uboot_gold": TOR_IMAGES.flash_uboot_gold[self._uut_type],
            "flash_fw_gold": TOR_IMAGES.flash_fw_gold[self._uut_type],
            "flash_uboot_primary": TOR_IMAGES.flash_uboot_primary[self._uut_type],
            "flash_fw_primary": TOR_IMAGES.flash_fw_primary[self._uut_type]
        }

        articles = ["flash_boot0", "flash_uboot_gold", "flash_fw_gold", "flash_uboot_primary", "flash_fw_primary"]

        if not self.tor_check_fpgautil():
            return False

        for article in articles:
            qspi_img = img_location[article]

            self.cli_log_inf("Downloading QSPI {:s} image".format(article))
            time.sleep(4)
            if not libmfg_utils.console_copy_file(self, TOR_IMAGES.TFTP_SERVER_IP, MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH, TOR_IMAGES.TFTP_SERVER_DIR+qspi_img):
                self.cli_log_err("Unable to get {:s}".format(article), level=0)
                return False
            time.sleep(10)

        # if not self.mtp_power_on_nic(pre_diag_method=True):
        #     self.cli_log_err("Failed to power on nic", level=0)
        #     return False

        for slot in range(0,2):
            for article in articles:
                qspi_img = img_location[article]
                if not self.tor_nic_qspi_prog_fw(slot, article, MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH+os.path.basename(qspi_img)):
                    self.cli_log_err("QSPI update failed for elba {:s}".format(str(slot)), level=0)
                    return False

        # if not self.mtp_power_cycle_nic(pre_diag_method=True):
        #     self.cli_log_err("Failed to power cycle nic", level=0)
        #     return False

        return True

    def tor_nic_qspi_prog_fw(self, slot, article, qspi_img):
        self.cli_log_slot_inf(slot, "Updating {:s}".format(article))
        cmd = "ISP_SKIP_PRECOMPARE=1 hpe-isp update mod sc slot {:s} dev {:s} file {:s} force".format(str(slot+1), article, qspi_img)
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Update successful"], timeout=MTP_Const.TOR_QSPI_PROG_DELAY):
            self.cli_log_slot_err(slot, "Programming Elba{:d} QSPI {:s} failed".format(slot, article))
            return False

        return True

    def tor_util_prog(self, util_img, download=True, powercycle_after_prog=False):
        uut_img_dir = MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH

        if not self.tor_prepare_eeupdate():
            self.cli_log_err("Unable to update eeupdate directory", level=0)
            return False

        if not self.mtp_mgmt_exec_cmd("mkdir -p {}".format(uut_img_dir)):
            self.cli_log_err("Unable to create util folder", level=0)
            return False
        if download:
            for eachutil_img in util_img:
                if not libmfg_utils.console_copy_file(self, TOR_IMAGES.TFTP_SERVER_IP, uut_img_dir, TOR_IMAGES.TFTP_SERVER_FPGA_DIR+eachutil_img):
                    self.cli_log_err("Failed to get {:s}".format(eachutil_img), level=0)
                    return False
                cmd="chmod +x {}".format(uut_img_dir+eachutil_img)
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("{:s} failed".format(cmd), level=0)
                    return False
                cmd = "sync"
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("{:s} failed".format(cmd), level=0)
                    return False

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        cmd = "ls {}".format(uut_img_dir)
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=[util_img[0]]):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        
        if powercycle_after_prog:
            return self.uut_powercycle_with_intr()
        else:
            time.sleep(5)
            # self.mtp_mgmt_exec_cmd("exit")

        return True

    def tor_os_prog(self, os_img, download=True, powercycle_after_prog=False):
        uut_img_dir = MTP_DIAG_Path.ONBOARD_TOR_IMG_PATH

        if download:
            self.cli_log_inf("Downloading OS image")
            if not libmfg_utils.console_copy_file(self, TOR_IMAGES.TFTP_SERVER_IP, "/", TOR_IMAGES.TFTP_SERVER_DIR+os_img):
                self.cli_log_err("Failed to get {:s}".format(os_img), level=0)
                return False

        cmd = "cd /"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd = "rm {:s}secondary.swi {:s}primary.swi".format(uut_img_dir,uut_img_dir)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd = "cp {:s}{:s} {:s}primary.swi ; ls -l {:s}primary.swi".format("/",os.path.basename(os_img),uut_img_dir,uut_img_dir)
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["primary.swi"]):
            self.cli_log_err("Failed to place {:s}".format(os_img), level=0)
            return False
        self.cli_log_inf("Saved OS image to primary image")
        time.sleep(1)

        cmd = "cp {:s}{:s} {:s}secondary.swi ; ls -l {:s}secondary.swi".format("/",os.path.basename(os_img),uut_img_dir,uut_img_dir)
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["secondary.swi"]):
            self.cli_log_err("Failed to place {:s}".format(os_img), level=0)
            return False
        self.cli_log_inf("Saved OS image to secondary image")
        time.sleep(1)

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        cmd = "ls /fs/nos/"
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["primary.swi"]):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        
        if powercycle_after_prog:
            return self.uut_powercycle_with_intr()
        else:
            time.sleep(5)
            # self.mtp_mgmt_exec_cmd("exit")

        return True

    def tor_store_edc(self, edc):
        if not self.mtp_mgmt_exec_cmd("echo {:s} > {:s}/edc".format(edc, MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)):
            return False
        return True

    def tor_retrieve_edc(self):
        if not self.mtp_mgmt_exec_cmd("cat {:s}/edc".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)):
            return False
        cmd_buf = self.mtp_get_cmd_buf()
        if not cmd_buf:
            return False

        match = re.search(ARUBA_EDC_FMT, cmd_buf)
        if not match:
            return False
        self._edc = match.group(0)

        return True

    def tor_fru_prog(self, sn, mac, pn, edc, prog_date):
        # if not self.mtp_console_connect():
        #     self.cli_log_err("Unable to telnet to UUT Chassis", level=0)
        #     return
        mac_ui = libmfg_utils.mac_address_format(mac, ":")     #00ABCDEFGH -> 00:AB:CD:EF:GH
        prog_date = libmfg_utils.hpe_date_format(prog_date) #YYYY-MM-DD_hh-mm-ss -> MM/DD/YYYY HH:MM:SS
        if not self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.TOR_FRU_DISP_FMT):
            self.cli_log_err("Unable to display fru")
            return False
        if not self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.TOR_FRU_ERASE_FMT, sig_list=["Success"]):
            self.cli_log_err("Unable to erase fru")
            return False
        fru_prog_cmd = MFG_DIAG_CMDS.TOR_FRU_PROG_FMT.format(pn, sn, mac_ui, prog_date, "Mon Jul 08 10:10:10 2021 -0700")
        # if not self.mtp_mgmt_exec_cmd(fru_prog_cmd, sig_list=['Success']):
        if not self.mtp_mgmt_exec_cmd(fru_prog_cmd, sig_list=["TPM Serial Number:"]):
            self.cli_log_err("Unable to program fru")
            return False

        if not self.tor_store_edc(edc):
            self.cli_log_err("Unable to store EDC", level=0)
            return False

        self._sn = sn
        self._mac = mac
        self._pn = pn
        self._prog_date = prog_date
        self._edc = edc

        time.sleep(1)
        return True

    def tor_mfg_fru_prog(self):
        """
        Program the MFG portion of "Locked" EEPROM
        Program relevant sections of the "Unlocked" EEPROM
        """
        if not self.tor_retrieve_edc():
            self.cli_log_err("Failed to parse EDC from FRU - please rerun DL1", level=0)
            return False

        if not self.mtp_mgmt_exec_cmd('vtysh -c "diag" -c "diag fruwrite chassis_ul 1 clear_all"'):
            self.cli_log_err("Failed to clear unlocked FRU", level=0)
            return False

        eeprom1_fields = {
            "id_reg": "0x0d0201f1",
            "serial_nr": self._sn,
            "assy_rev_ver": "0x01",
            "assy_rev_edc": self._edc
        }

        eeprom2_fields = {
            "assembly_info pca_rev": "0x01",
            "assembly_info rework_rev": "0x01",
            "assembly_info bom_rev": "0x01",
            "assembly_info num_of_prgm_dev": "13",
            "pca_edc": self._edc,
            "pca_serial_num": self._pcbasn
        }

        for eeprom_field in eeprom1_fields.keys():
            if not self.mtp_mgmt_exec_cmd('yes | vtysh -c "diag" -c "diag mfgwrite chassis 1 {:s} {:s}"'.format(eeprom_field, eeprom1_fields[eeprom_field])):
                self.cli_log_err("Failed to write FRU field {:s}".format(eeprom_field), level=0)
                return False

        for eeprom_field in eeprom2_fields.keys():
            if not self.mtp_mgmt_exec_cmd('yes | vtysh -c "diag" -c "diag mfgwrite chassis_ul 1 {:s} {:s}"'.format(eeprom_field, eeprom2_fields[eeprom_field])):
                self.cli_log_err("Failed to write FRU field {:s}".format(eeprom_field), level=0)
                return False

        return True

    def tor_fru_passmark(self, stage):
        """
        yes | vtysh -c "diag" -c "diag mfgwrite chassis_ul 1 passmark_loc 6 pass_mark DL2:20220718090000"
        yes | vtysh -c "diag" -c "diag mfgwrite chassis_ul 1 passmark_loc 7 pass_mark LED:20220718100000"
        yes | vtysh -c "diag" -c "diag mfgwrite chassis_ul 1 passmark_loc 8 pass_mark  2C:20220718110000"
        yes | vtysh -c "diag" -c "diag mfgwrite chassis_ul 1 passmark_loc 9 pass_mark SWI:20220718120000"
        """
        pass_timestamp = libmfg_utils.get_passmark_timestamp()

        if stage == "DL2":
            prog_val = "passmark_loc 6 pass_mark DL2:"+pass_timestamp
        elif stage == "LED":
            prog_val = "passmark_loc 7 pass_mark LED:"+pass_timestamp
        elif stage in ("2C-LV", "2C_LV", FF_Stage.FF_2C_LV):
            prog_val = "passmark_loc 8 pass_mark 2C:"+pass_timestamp
        elif stage in ("SWI", FF_Stage.FF_SWI):
            prog_val = "passmark_loc 9 pass_mark SWI:"+pass_timestamp
        else:
            self.cli_log_err("This stage {:s} does not have a passmark defined".format(stage), level=0)
            return True

        if not self.mtp_mgmt_exec_cmd('yes | vtysh -c "diag" -c "diag mfgwrite chassis_ul 1 {:s}"'.format(prog_val)):
            self.cli_log_err("Failed to store passmark into FRU", level=0)
            return False

        return True

    def tor_mfg_fru_verify(self):
        """
        Read the MFG portion of "Locked" EEPROM
        Read relevant sections of the "Unlocked" EEPROM
        """

        if not self.mtp_mgmt_exec_cmd('vtysh -c "diag" -c "diag mfgread chassis 1"'):
            self.cli_log_err("Failed to read mfg portion of locked FRU", level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf()
        if not cmd_buf:
            self.cli_log_err("Failed to read content of mfg portion of locked FRU", level=0)
            return False

        eeprom1_fields = {
            "id_reg": "0x0d0201f1",
            "serial_nr": self._sn,
            "assy_rev_ver": "0x01",
            "assy_rev_edc": self._edc
        }

        for eeprom_field in eeprom1_fields.keys():
            exp_val = eeprom1_fields[eeprom_field]
            match = re.search("%s: *\'%s\x00?\'" % (eeprom_field, exp_val), cmd_buf)            
            if match:
                continue
            else:
                self.cli_log_err("Incorrect FRU value for {:s}, expected: {:s}".format(eeprom_field, exp_val))
                return False


        eeprom2_fields = {
            "pca_rev": "0x01",
            "rework_rev": "0x01",
            "bom_rev": "0x01",
            "num_of_prgm_dev": "13",
            "pca_edc": self._edc,
            "pca_serial_num": self._pcbasn
        }

        if not self.mtp_mgmt_exec_cmd('vtysh -c "diag" -c "diag mfgread chassis_ul 1"'):
            self.cli_log_err("Failed to read unlocked FRU", level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf()
        if not cmd_buf:
            self.cli_log_err("Failed to read content of unlocked FRU", level=0)
            return False

        for eeprom_field in eeprom2_fields.keys():
            exp_val = eeprom2_fields[eeprom_field]
            match = re.search("%s: *\'%s\x00?\'" % (eeprom_field, exp_val), cmd_buf)
            if match:
                continue
            else:
                self.cli_log_err("Incorrect FRU value for {:s}, expected: {:s}".format(eeprom_field, exp_val))
                return False

        return True

    def get_pchasn_by_yaml(self, sn):
        sn_pcbasn_cfg_file = "config/taormina_sn_pcbasn_cfg.yaml"
        sn_pcbasn_cfg = libmfg_utils.load_cfg_from_yaml(sn_pcbasn_cfg_file)
        #print(sn_pcbasn_cfg)      
        pcbasn = None
        for eachdata in sn_pcbasn_cfg:
            if eachdata["SN"] == sn:
                pcbasn = eachdata["PCBA_SN"]
                break
        self.cli_log_inf("Retrieved PCBA SN: {}".format(pcbasn), level=0)
        return pcbasn

    def tor_fru_prog_tpm_pcbasn(self, pcbasn):
        # if not self.mtp_console_connect():
        #     self.cli_log_err("Unable to telnet to UUT Chassis", level=0)
        #     return
        if not self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.TOR_FRU_DISP_FMT):
            self.cli_log_err("Unable to display fru")
            return False
        #time.sleep(1)
        #print(self._cmd_buf)
        frureadata = self.parse_fruread(self._cmd_buf)
        #print(frureadata)
        #sys.exit()
        for x in range(3):
            if not "TPM Serial Number" in frureadata:
                time.sleep(3)
                if not self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.TOR_FRU_DISP_FMT):
                    self.cli_log_err("Unable to display fru")
                    return False
                #time.sleep(1)
                #print(self._cmd_buf)
                frureadata = self.parse_fruread(self._cmd_buf)
                #print(frureadata)
            else:
                break

        if not frureadata["TPM Serial Number"] == pcbasn:
            fru_prog_cmd = MFG_DIAG_CMDS.TOR_FRU_PROG_TPM_FMT.format(pcbasn)
            if not self.mtp_mgmt_exec_cmd(fru_prog_cmd):
                self.cli_log_err("Unable to program fru")
                return False

        self._pcbasn = pcbasn

        time.sleep(1)

        if not self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.TOR_FRU_DISP_FMT):
            self.cli_log_err("Unable to display fru")
            return False
        #time.sleep(1)
        #print(self._cmd_buf)
        frureadata = self.parse_fruread(self._cmd_buf)
        #print(frureadata)
        #sys.exit()
        for x in range(3):
            if not "TPM Serial Number" in frureadata:
                time.sleep(3)
                if not self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.TOR_FRU_DISP_FMT):
                    self.cli_log_err("Unable to display fru")
                    return False
                #time.sleep(1)
                #print(self._cmd_buf)
                frureadata = self.parse_fruread(self._cmd_buf)
                #print(frureadata)
            else:
                break

        time.sleep(1)
        if not frureadata["TPM Serial Number"] == pcbasn:
            self.cli_log_err("Unable to program fru for TPM or Product Name")
            return False            
        else:
            self.cli_log_inf("Verified TPM SN: {} and Product Name: {} are correct".format(frureadata["TPM Serial Number"],frureadata["Product Name"]), level=0)
        return True

    def parse_fruread(self, cmd_buffer):
        frureadata = dict()
        sub_match = re.findall(r"(\w.*\w):\s\'(.*)\'", cmd_buffer)
        #print(sub_match)
        if sub_match:
            for eachdata in sub_match:
                frureadata[eachdata[0]] = eachdata[1]
        return frureadata


    def tor_fru_verify(self, expected_sn, expected_mac, expected_pn, expected_prog_date):
        # if not self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.TOR_FRU_DISP_FMT, sig_list=['TPM Serial Number:']):
        #     self.cli_log_err("Unable to display fru", level=0)
        #     return False

        self.clear_buffer()
        time.sleep(3)
        self._mgmt_handle.sendline(MFG_DIAG_CMDS.TOR_FRU_DISP_FMT)
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["TPM Serial Number:"])
        cmd_buf = self._mgmt_handle.before
        if not cmd_buf:
            self.cli_log_err("Unable to read fru", level=0)
            return False

        # Verify SN
        sn_match = re.search("Serial Number: '(.*)'", cmd_buf)
        if sn_match:
            if sn_match.group(1) != expected_sn:
                self.cli_log_err("Incorrect SN programmed: {:s}".format(sn_match.group(1)), level=0)
                return False
        else:
            self.cli_log_err("Unable to read SN", level=0)
            return False

        # Verify MAC
        mac_match = re.search("MAC Address: '(.*)'", cmd_buf)
        if mac_match:
            if ":" in expected_mac:
                mac = expected_mac
            else:
                mac = libmfg_utils.mac_address_format(expected_mac, delimiter=":")
            if mac_match.group(1) != mac:
                self.cli_log_err("Incorrect MAC programmed: {:s}".format(mac_match.group(1)), level=0)
                return False
        else:
            self.cli_log_err("Unable to read MAC", level=0)
            return False     

        # Verify PN
        pn_match = re.search("Part Number: '(.*)'", cmd_buf)
        if pn_match:
            if pn_match.group(1) != expected_pn:
                self.cli_log_err("Incorrect PN programmed: {:s}".format(pn_match.group(1)), level=0)
                return False
        else:
            self.cli_log_err("Unable to read PN", level=0)
            return False

        # Verify Prod Name #TODO: move this to libmfg_cfg
        prod_match = re.search("Product Name: '(.*)'", cmd_buf)
        if prod_match:
            if prod_match.group(1) != "CX 10000-48Y6C switch":
                self.cli_log_err("Incorrect Product name programmed: {:s}".format(prod_match.group(1)), level=0)
                return False
        else:
            self.cli_log_err("Unable to read Product Name from FRU", level=0)
            return False

        return True

    def tor_fru_init(self):
        """ Read FRU and save it into object's _sn, _mac, _pn """
        self._mgmt_handle.sendline(MFG_DIAG_CMDS.TOR_FRU_DISP_FMT)
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["TPM Serial Number:"])
        cmd_buf = self._mgmt_handle.before
        if not cmd_buf:
            self.cli_log_err("Unable to read fru", level=0)
            return False

        # Save system SN
        sn_match = re.search("[^TPM] Serial Number: '(.*)'", cmd_buf)
        if sn_match:
            self._sn = sn_match.group(1)
        else:
            self.cli_log_err("Unable to read SN", level=0)
            return False

        # Save MAC
        mac_match = re.search("MAC Address: '(.*)'", cmd_buf)
        if mac_match:
            self._mac = mac_match.group(1).replace(":","")
        else:
            self.cli_log_err("Unable to read MAC", level=0)
            return False     

        # Save PN
        pn_match = re.search("Part Number: '(.*)'", cmd_buf)
        if pn_match:
            self._pn = pn_match.group(1)
        else:
            self.cli_log_err("Unable to read PN", level=0)
            return False

        # Save prog date
        date_match = re.search("Manufacture Date: '(.*)'", cmd_buf)
        if date_match:
            self._prog_date = date_match.group(1)
        else:
            self.cli_log_err("Unable to read Date", level=0)
            return False

        # Save pcba SN
        cmd = MFG_DIAG_CMDS.TOR_PCBASN_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf()
        if not cmd_buf:
            self.cli_log_err("{:s} returned no output".format(cmd), level=0)
            return False
        pcbasn_match = re.search(TOR_SN_FMT, cmd_buf)
        if pcbasn_match:
            self._pcbasn = pcbasn_match.group(0)
        else:
            self.cli_log_err("Unable to read PCBA SN", level=0)
            return False

        self.clear_buffer()
        time.sleep(1)

        return True

    def tor_nic_fru_verify(self, slot, sn, mac, pn, prog_date):
        if not self.mtp_nic_fru_init(slot, init_date=True, nic_type=self.mtp_get_nic_type(slot)):
            return False
        if not self.mtp_verify_nic_fru(slot, sn, mac, pn, prog_date):
            return False
        return True

    def tor_info_disp(self, fru_valid=True):
        self.cli_log_inf("UUT Info Dump:")
        if fru_valid:
            self.cli_log_inf("==> FRU: {:s}, {:s}, {:s}".format(self._sn,libmfg_utils.mac_address_format(self._mac),self._pn))
            self.cli_log_inf("==> PCBA SN: {:s}".format(self._pcbasn))
            self.cli_log_inf("==> FRU Program Date: {:s}".format(self._prog_date))
            self.cli_log_inf("==> Engineering Date Code: {:s}".format(self._edc))

        if self._bio_ver:
            self.cli_log_inf("==> BIOS version: {:s}".format(self._bio_ver))

        if self._svos_ver:
            self.cli_log_inf("==> SVOS version: {:s}".format(self._svos_ver))

        # if not self._boot_image or not self._kernel_timestamp:
        #     self.cli_log_err("Retrieve boot info failed")
        # else:
        #     self.cli_log_inf("==> Boot image: {:s}({:s})".format(self._boot_image, self._os_ver))

        if not self._cpld_dat:
            self.cli_log_err("Retrieve CPLD info failed")
        else:
            devices = {
            "fpga", 
            "cpu",
            "gpio0",
            "gpio1",
            "gpio2",
            "elba 0",
            "elba 1"
            }
            for device in devices:
                cpld_uc = self._cpld_dat[device]
                self.cli_log_inf("==> {:s} CPLD: {:s}".format(device.upper(), cpld_uc))


        # for slot, prsnt, nic_type in zip(range(self._slots), self._nic_prsnt_list, self._nic_type_list):
        #     if prsnt:
        #         self.cli_log_slot_inf(slot, "NIC is Present, Type is: {:s}".format(nic_type))
        #         if fru_valid:
        #             fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
        #             if not fru_info_list:
        #                 self.cli_log_slot_err_lock(slot, "Retrieve NIC FRU failed")
        #             else:
        #                 self.cli_log_slot_inf(slot, "==> Manufacture Vendor: {:s}".format(fru_info_list[4]))
        #                 self.cli_log_slot_inf(slot, "==> FRU: {:s}, {:s}, {:s}".format(fru_info_list[0],fru_info_list[1],fru_info_list[2]))
        #                 if fru_info_list[3]:
        #                     self.cli_log_slot_inf(slot, "==> FRU Program Date: {:s}".format(fru_info_list[3]))
        #         boot_info_list = self._nic_ctrl_list[slot].nic_get_boot_info()
        #         if not boot_info_list:
        #             self.cli_log_slot_err(slot, "Retrieve NIC boot info failed")
        #         else:
        #             self.cli_log_slot_inf(slot, "==> Boot image: {:s}({:s})".format(boot_info_list[0], boot_info_list[1]))

        #         cpld_info_list = self._nic_ctrl_list[slot].nic_get_cpld()
        #         if not cpld_info_list:
        #             self.cli_log_slot_err(slot, "Retrieve NIC CPLD info failed")
        #         else:
        #             self.cli_log_slot_inf(slot, "==> CPLD: {:s}({:s})".format(cpld_info_list[0], cpld_info_list[1]))

        #         diag_info_list = self._nic_ctrl_list[slot].nic_get_diag()
        #         if not diag_info_list:
        #             self.cli_log_slot_err(slot, "Retrieve NIC Diag info failed")
        #         else:
        #             self.cli_log_slot_inf(slot, "==> Diag version: {:s}".format(diag_info_list[0]))
        #             self.cli_log_slot_inf(slot, "==> EMMC Util version: {:s}".format(diag_info_list[1]))
        #             self.cli_log_slot_inf(slot, "==> NIC ASIC version: {:s}".format(diag_info_list[2]))

        #         if not self._nic_ctrl_list[slot].nic_check_status():
        #             self.cli_log_slot_err(slot, "NIC in failure state")
        #     elif self._slots_to_skip[slot]:
        #         self.cli_log_slot_err(slot, "NIC is Skipped")
        #     else:
        #         self.cli_log_slot_err(slot, "NIC is Absent")
        self.cli_log_inf("End UUT Info Dump")

        return True


    def tor_board_id(self):
        if not self._mgmt_cfg:

            if not self.tor_check_fpgautil():
                return False

        cmd = "{:s}fpgautil inventory".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        if not self.tor_cpld_init():
            self.cli_log_err("CPLD init failed", level=0)
            return False

        # if not self.tor_os_init():
        #     self.cli_log_err("OS init failed", level=0)
        #     return False

        if not self.tor_bios_init():
            self.cli_log_err("BIOS init failed", level=0)
            return False

        self.tor_info_disp()

        return True

    def tor_nic_init(self):
        self.cli_log_inf("Init NIC Type", level=0)
        if not self.mtp_nic_para_session_init():
            return False

        self._nic_type_list = [None] * self._slots

        # init nic present list
        for slot in range(self._slots):
            if not self._slots_to_skip[slot]:
                self._nic_prsnt_list[slot] = True
                self._nic_type_list[slot] = NIC_Type.TAORMINA
                self._nic_ctrl_list[slot].nic_set_type(NIC_Type.TAORMINA)
            else:
                self._nic_prsnt_list[slot] = False
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)

            if not self.mtp_mgmt_exec_cmd_para(slot, "source /home/root/.profile"):
                self.cli_log_slot_err(slot, "Couldn't initialize NIC env vars")

        return True

    def tor_diag_init(self, stage, fpo=False):
        homedir = self.get_homedir()
        if fpo:
            # One-time steps related to running the diag image
            python_lib_dir = homedir + "python_files/"
            cmd = "mkdir {:s}".format(homedir)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("{:s} failed".format(cmd))
                return False

            # copy diag image
            asic_type = MTP_ASIC_SUPPORT.ELBA
            x86_image = MTP_IMAGES.AMD64_IMG[asic_type]
            arm_image = MTP_IMAGES.ARM64_IMG[asic_type]
            onboard_images = self.mtp_diag_get_img_files(homedir)
            if not libmfg_utils.mtp_update_diag_image(self, x86_image, arm_image, onboard_images, homedir=homedir):
                self.cli_log_err("Unable to update diag image", level=0)
                return False

            cmd = "mkdir {:s}".format(python_lib_dir)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("{:s} failed".format(cmd))
                return False

            # copy python lib
            if not libmfg_utils.mtp_update_packages(self, "release/packages/", python_lib_dir):
                self.cli_log_err("Unable to update diag image", level=0)
                return False

        # diag environment init
        cmd = "cd {:s}".format(homedir)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd))
            return False

        # diag environment pre init
        if not self.mtp_diag_pre_init("diagmgr.log"):
            self.cli_log_err("Unable to pre-init diag environment", level=0)
            return False

        # diag environment post init
        if not self.mtp_diag_post_init(0, stage):
            self.cli_log_err("Unable to post-init diag environment", level=0)
            return False

        # get the tor system info
        if not self.mtp_sys_info_disp():
            self.cli_log_err("Unable to retrieve TOR system info", level=0)
            return False

        # init all the nic.
        if not self.tor_nic_init():
            self.cli_log_err("Initialize NIC type, present failed", level=0)
            return False
        return True

    def tor_pcie_rescan(self, slot):
        """ remove pcie resources and scan back """
        # cmd = "/home/diag/diag/util/fpgautil power on e{:d}".format(slot)
        # if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.TOR_POWER_ON_DELAY + MTP_Const.TOR_PCIE_SCAN_DELAY):
        #     return False

        bus = NIC_IP_Address.PCI_BUS[slot]
        cmd = "echo 1 > /sys/bus/pci/devices/00{:s}.0/remove".format(bus)
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            return False

        cmd = "rmmod ionic"
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            return False

        cmd = "echo 1 > /sys/bus/pci/rescan"
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            return False

        cmd = "lspci -s {:s}".format(bus)
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            return False

        return True

    @single_slot_test("DL", "NIC_MEMTUN_INIT")
    def tor_nic_memtun_init(self, slot):
        bus = NIC_IP_Address.PCI_BUS[slot]
        cmd = "lspci -s {:s}".format(bus)
        if not self._nic_ctrl_list[slot].mtp_get_info(cmd):
            return False
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        if cmd_buf:
            if bus in cmd_buf and "1dd8:0002" in cmd_buf:
                fpo = False
            else:
                # try to bringup pcie with first-power-on procedure
                fpo = True
        else:
            # try to bringup pcie with first-power-on procedure
            fpo = True

        if fpo:
            if not self._nic_ctrl_list[slot].nic_dummy_fru():
                self.cli_log_slot_err(slot, "Failed to bringup PCIE with dummy FRU")
                return False

            # pcie rescan is included in power on
            if not self.tor_pcie_rescan(slot):
                self.cli_log_slot_err(slot, "Failed to rescan pcie")
                return False

        ret = False
        for x in range(2):
            self.cli_log_slot_inf(slot, "Opening memtun")
            ret = self._nic_ctrl_list[slot].nic_memtun_init()
            if ret:
                break
            else:
                self.cli_log_slot_err(slot, "Failed to init memtun")
                cmd = "ps -A | grep memtun"
                if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                    self.cli_log_slot_err(slot, "{:s} failed".format(cmd))

        return ret

    # def tor_nic_memtun_init_run(self):
    #     cmd = "ps -A | grep memtun"
    #     if not self.mtp_mgmt_exec_cmd(cmd):
    #         self.cli_log_err("{:s} failed".format(cmd))
    #         return False

    #     cmd = "killall memtun"
    #     if not self.mtp_mgmt_exec_cmd(cmd):
    #         self.cli_log_err("{:s} failed".format(cmd))
    #         return False

    #     """
    #      NZ: Move into libnic later
    #     """
    #     time.sleep(5)

    #     for slot in range(self._slots):
    #         start_ts = self.log_slot_test_start(slot, "NIC_GOLDFW_VERIFY")
    #         self.cli_log_slot_inf(slot, "Init memtun")
        
    #         memtun_ip = NIC_IP_Address.MEMTUN_IP[slot]
    #         mgmt_ip   = NIC_IP_Address.MGMT_IP[slot]
    #         pci_bus = NIC_IP_Address.MEMTUN_PCI_BUS[slot]

    #         cmd = "{:s}memtun -s {:s} {:s} &".format("/fs/nos/home_diag/diag/tools/", pci_bus, memtun_ip)
    #         # if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["# "]):
    #         if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=60):
    #             self.cli_log_err("{:s} failed".format(cmd))
    #             duration = self.log_slot_test_stop(slot, "NIC_GOLDFW_VERIFY", start_ts)
    #             return False
    #         time.sleep(2)

    #         cmd = "ping -c 1 {:s}".format(mgmt_ip)
    #         # if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["# "]):
    #         pingsuccess = False
    #         for x in range(2):
    #             if self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, sig_list=["1 received"], timeout=30):
    #                 pingsuccess = True
    #             else:
    #                 self.cli_log_err("NIC-0{} : {:s} failed, try again".format(slot+1, cmd))
    #                 #return False
    #             if pingsuccess:
    #                 break
    #         if not pingsuccess:
    #             self.cli_log_err("NIC-0{} : {:s} failed,".format(slot+1, cmd))
    #             duration = self.log_slot_test_stop(slot, "NIC_GOLDFW_VERIFY", start_ts)
    #             return False
    #         duration = self.log_slot_test_stop(slot, "NIC_GOLDFW_VERIFY", start_ts)
    #     return True

    def tor_nic_memtun_validate(self):
        for slot in range(self._slots):
            if not self._nic_ctrl_list[slot].nic_memtun_validate():
                self.cli_log_err(self._nic_ctrl_list[slot].nic_get_err_msg())
                return False
        return True

    def tor_os_init(self):
        """
        root@Taormina:~# vtysh -c "show version"
        -----------------------------------------------------------------------------
        ArubaOS-CX
        (c) Copyright 2017-2021 Hewlett Packard Enterprise Development LP
        -----------------------------------------------------------------------------
        Version      : DL.XX.XX.XXXX
        Build Date   : 2021-06-09 21:39:59 UTC
        Build ID     : ArubaOS-CX:DL.XX.XX.XXXX:1ae7536780dc:202106092133
        Build SHA    : 1ae7536780dc6ea36b786542945ad10be84d6524
        Active Image : primary

        Service OS Version :
        BIOS Version       : DL-01-0001
        """

        ## Kernel timestamp... just reading it and not verifying
        cmd = MFG_DIAG_CMDS.MTP_IMG_VER_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["SMP"]):
            self.cli_log_err("Failed to get os image version", level = 0)
            return False
        match = re.findall(r"SMP(?: PREEMPT)? (.* 20\d{2})", self.mtp_get_cmd_buf())
        if match:
            kernel_ver = match[0]
            # check if timestamp is valid
            try:
                dt = datetime.strptime(kernel_ver, "%a %b %d %X %Z %Y")
                self._kernel_timestamp = dt.strftime("%m-%d-%Y")
            except ValueError:
                self.cli_log_err("Invalid date")
                return False
        else:
            self.cli_log_err("Failed to read kernel timestamp")
            return False

        cmd = "vtysh -c \"show version\""
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=20):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf()

        os_ver_match = re.search("Build Date.*:.*(\d{4}\-\d{2}\-\d{2})", cmd_buf)
        if os_ver_match:
            self._os_ver = os_ver_match.group(1)
        else:
            self.cli_log_err("Couldn't read OS version", level=0)
            return False

        active_os_match = re.search("Active Image.*: *([a-zA-Z]+)", cmd_buf)
        if active_os_match:
            self._boot_image = active_os_match.group(1)
        else:
            self.cli_log_err("Couldn't read active image", level=0)
        # # cmd = "bootconftool read boot user_selection" # can't get this command's output to work with pexpect
        # cmd = "cat /fs/security/serviceos/boot.conf"
        # if not self.mtp_mgmt_exec_cmd(cmd, timeout=100):
        #     self.cli_log_err("Failed to get selected boot image", level=0)
        #     return False
        # cmd_buf = self.mtp_get_cmd_buf()
        # print(cmd_buf)
        # match = re.search("user_selection=(serviceos|primary|secondary)", cmd_buf)
        # if match:
        #     self._boot_image = match[0]
        # else:
        #     self.cli_log_err("Failed to read selected boot image")
        #     return False 

        return True

    def tor_bios_init(self):

        for x in range(5):
            cmd = "dmidecode -s bios-version"
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=20):
                self.cli_log_err("{:s} failed".format(cmd), level=0)
                #return False
            cmd_buf = self.mtp_get_cmd_buf()

            bio_ver_match = re.search("(\w\w-\d+-\d+\w?)", cmd_buf)
            if bio_ver_match:
                self._bio_ver = bio_ver_match.group(1)
                return True
            else:
                self.cli_log_err("Couldn't read BIOS version", level=0)
                #return False

        return False

    def tor_os_verify(self, exp_os_version):

        getversionsuccess = False
        for x in range(5):
            if self.tor_os_init():
                getversionsuccess = True
                break
        if not getversionsuccess:
            return False

        if not self._os_ver:
            return False
        if not self._boot_image:
            return False

        got_version = self._os_ver
        exp_version = exp_os_version
        if got_version != exp_version:
            self.cli_log_err("Incorrect OS version: {:s}, expected {:s}".format(got_version, exp_version), level=0)
            return False
        
        exp_boot_image = "primary"
        if self._boot_image != exp_boot_image:
            self.cli_log_err("Incorrect boot: {:s}, expected {:s}".format(self._boot_image, exp_boot_image), level=0)
            return False

        return True

    def tor_bios_verify(self):
        if not self._bio_ver:
            if not self.tor_bios_init():
                return False

        got_version = self._bio_ver
        exp_version = TOR_IMAGES.bios_dat[self._uut_type]
        if got_version != exp_version:
            self.cli_log_err("Incorrect BIOS version: {:s}, expected {:s}".format(got_version, exp_version), level=0)
            return False

        return True

    def tor_mgmt_os_prog(self, os_img, force_download=True):
        ip_addr = self._mgmt_cfg[0]
        usrid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]
        uut_img_dir = MTP_DIAG_Path.ONBOARD_TOR_IMG_PATH

        cmd = "ls /fs/nos/"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        if force_download or os.path.basename(os_img) not in self.mtp_get_cmd_buf():
            if not libmfg_utils.network_copy_file(ip_addr, usrid, passwd, os_img, uut_img_dir, self._diag_filep):
                self.cli_log_err("Copy OS image failed", level=0)
                return False

        cmd = "rm {:s}secondary.swi {:s}primary.swi".format(uut_img_dir,uut_img_dir)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd = "cp {:s}{:s} {:s}primary.swi ; ls -l {:s}primary.swi".format(uut_img_dir,os.path.basename(os_img),uut_img_dir,uut_img_dir)
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["primary.swi"]):
            self.cli_log_err("Failed to place {:s}".format(os_img), level=0)
            return False
        # time.sleep(1)

        cmd = "cp {:s}{:s} {:s}secondary.swi ; ls -l {:s}secondary.swi".format(uut_img_dir,os.path.basename(os_img),uut_img_dir,uut_img_dir)
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["secondary.swi"]):
            self.cli_log_err("Failed to place {:s}".format(os_img), level=0)
            return False
        time.sleep(1)

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False
        
        time.sleep(5)
        return True

    def tor_svos_init(self):
        ### IMPROVEMENT: load the SHA version of the image here too, to avoid forged SVOS
        ret = False
        for x in range(3):
            if ret:
                continue

            if not self.mtp_console_enter_shell("svcli"):
                self.cli_log_err("Unable to enter svcli")
                return False        
            
            cmd = "version"
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Information:"], timeout=10):
                self.cli_log_err("Failed to get SVOS version", level=0)
                self.mtp_mgmt_exec_cmd("exit")
                ret = False
                continue

            cmd_buf = self.mtp_get_cmd_buf()
            date_match = re.search("Build Date.*:.*(\d{4}\-\d{2}\-\d{2})", cmd_buf)
            ver_match = re.search("Version.*:.*(..\...\...\.[\w\-]*)", cmd_buf)

            if date_match:
                self._svos_dat = date_match.group(1)
                #self.mtp_mgmt_exec_cmd("exit")
                self._mgmt_handle.sendline("exit")
                self.mtp_console_enter_shell("sh")
                ret = True
                if ver_match:
                    self._svos_ver = ver_match.group(1)
                break

            else:
                self.cli_log_err("Failed to read SVOS version")
                #self.mtp_mgmt_exec_cmd("exit")
                self._mgmt_handle.sendline("exit")
                self.mtp_console_enter_shell("sh")
                ret = False
                continue

        if not self.mtp_console_enter_shell("sh"):
            self.cli_log_err("Unable to init bash shell", level=0)
            return False

        return ret

    def tor_svos_prog(self, img, download=True, ship_img=False):
        # uut_img_dir = MTP_DIAG_Path.ONBOARD_TOR_IMG_PATH
        uut_img_dir = "/"

        # if download:
        if not self.tor_svos_verify(ship_img):
            self.cli_log_inf("Downloading SVOS image")

            cmd = "cd {:s}".format(uut_img_dir)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("{:s} failed".format(cmd), level=0)
                return False

            if not libmfg_utils.console_copy_file(self, TOR_IMAGES.TFTP_SERVER_IP, uut_img_dir, TOR_IMAGES.TFTP_SERVER_DIR+img):
                self.cli_log_err("Failed to get {:s}".format(img), level=0)
                return False

            self.cli_log_inf("Writing SVOS image")
            cmd = "hpe-isp update mod mc dev svos_primary file {:s} unsafe".format(img)
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Update successful"], timeout=MTP_Const.TOR_SVOS_PROG_DELAY):
                self.cli_log_err("{:s} failed".format(cmd), level=0)
                return False

            cmd = "hpe-isp update mod mc dev svos_secondary file {:s} unsafe".format(img)
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Update successful"], timeout=MTP_Const.TOR_SVOS_PROG_DELAY):
                self.cli_log_err("{:s} failed".format(cmd), level=0)
                return False

        return True

    def tor_svos_verify(self, ship_img=False):
        if not self.tor_svos_init():
            return False

        got_date = self._svos_dat
        got_ver = self._svos_ver

        if ship_img:
            exp_date = TOR_IMAGES.svos_ship_dat[self._uut_type]
            exp_ver = TOR_IMAGES.svos_ship_ver[self._uut_type]
        else:
            exp_date = TOR_IMAGES.svos_test_dat[self._uut_type]
            exp_ver = TOR_IMAGES.svos_test_ver[self._uut_type]

        if got_date != exp_date:
            self.cli_log_err("Incorrect SVOS version: {:s}, expected {:s}".format(got_date, exp_date), level=0)
            return False

        if got_ver:
            if got_ver != exp_ver:
                self.cli_log_err("Incorrect SVOS version: {:s}, expected {:s}".format(got_ver, exp_ver), level=0)
                return False

        return True

    def tor_td_avs_set(self):
        # switch to console
        if not self.mtp_console_connect():
            self.cli_log_err("Unable to telnet to UUT chassis")
            return False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd))
            return False
        cmd = "sudo su"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd))
            return False
        if not self.mtp_console_enter_shell("start_bcm_shell"):
            self.cli_log_err("Failed to enter BCM shell".format(cmd))
            return False
        time.sleep(1)
        cmd = "g TOP_AVS_SEL_REG"
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["top0"]):
            self.cli_log_err("{:s} failed".format(cmd))
            return False
        #TOP_AVS_SEL_REG.top0[7][0x2009800]=0x7e: <RESERVED_0=0,AVS_SEL=0x7e>
        avs_sel_sig = "AVS_SEL=(0x[0-9a-fA-F]+)"
        cmd_buf = self.mtp_get_cmd_buf()
        match = re.search(avs_sel_sig, cmd_buf)
        if match: 
            avs_sel_reg = match.group(1)
        else:
            return False
        self._mgmt_handle.sendline("exit")
        if not self.mtp_console_enter_shell("sh"):
            self.cli_log_err("Failed to return to bash shell".format(cmd))
            return False
        if not self.mtp_mgmt_exec_cmd("{:s}scripts/taormina/avs.bash program {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_MTP_DIAG_PATH, avs_sel_reg)):
            self.cli_log_err("Failed to program TD3 AVS", level=0)
            return False
        if not self.mtp_mgmt_exec_cmd("{:s}scripts/taormina/avs.bash read".format(MTP_DIAG_Path.ONBOARD_MTP_MTP_DIAG_PATH), sig_list=["vboot="]):
            self.cli_log_err("Failed to read back programmed TD3 voltage", level=0)
            return False 

        # switch back
        if not self.mtp_mgmt_connect(prompt_cfg=True):
            self.cli_log_err("Unable to telnet to UUT chassis")
            return False
        return True

    @single_slot_test("DL", "NIC_GOLDFW_BOOT")
    def tor_nic_gold_boot(self, slot):
        self.cli_log_slot_inf(slot, "Set goldfw boot")
        if not self._nic_ctrl_list[slot].nic_set_goldfw_boot():
            self.mtp_get_nic_err_msg(slot)
            self.cli_log_slot_err(slot, "Failed to set goldfw")
            return False
        return True

    def tor_nic_Setup_Elba_uboot_env(self, svos_boot=True, initemmc=True):
        successsetupenv = False
        for x in range(3):
            ret = self.tor_nic_Setup_Elba_uboot_env_run(svos_boot=svos_boot, initemmc=initemmc)
            if ret:
                successsetupenv = True
                break
            if x == 2:
                break
            if not self.tor_boot_select(1):
                return False
            if not self.tor_mgmt_init(False):
                return False
            if not self.tor_diag_init(FF_Stage.FF_DL, fpo=False):
                return False

        return successsetupenv

    def tor_nic_Setup_Elba_uboot_env_run(self, svos_boot=True, initemmc=True):
        ret = True
        if not self.tor_nic_init():
            self.cli_log_err("Initialize NIC type, present failed", level=0)
            return False

        if not self.mtp_mgmt_exec_cmd("killall picocom"):
            self.cli_log_err("killall picocom failed", level=0)
            return False

        for slot in range(self._slots):
            start_ts = self.log_slot_test_start(slot, "SETUP_ELBA_UBOOT_ENV")
            self.cli_log_slot_inf(slot, "Setup Elba uboot env")

            if not self._nic_ctrl_list[slot].nic_console_attach():
                self._nic_ctrl_list[slot].nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
                duration = self.log_slot_test_stop(slot, "SETUP_ELBA_UBOOT_ENV", start_ts)
                ret = False
                continue

            self._nic_ctrl_list[slot]._nic_handle.sendline("fwupdate -r")
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline("fwupdate -l")
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)

            if initemmc:
                self._nic_ctrl_list[slot]._nic_handle.sendline("fwupdate --init-emmc")
                idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["Done", "cannot"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
                if idx < 0:
                    self.cli_log_err("[NIC-0{}] init-emmc failure".format(slot+1))
                    duration = self.log_slot_test_stop(slot, "SETUP_ELBA_UBOOT_ENV", start_ts)
                    ret = False
                    continue
                elif idx == 1:
                    self.cli_log_err("[NIC-0{}] cannot init-emmc, will failure".format(slot+1))
                    duration = self.log_slot_test_stop(slot, "SETUP_ELBA_UBOOT_ENV", start_ts)
                    ret = False
                    continue
                else:
                    self.cli_log_slot_inf(slot, "init-emmc successfully")
                time.sleep(2)

            # set default to goldfw boot
            self._nic_ctrl_list[slot]._nic_handle.sendline("fwupdate -s mainfwa")
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# ", "not found"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            if idx == 1:
                self.cli_log_err("[NIC-0{}] Setup boot to goldfw failure".format(slot+1))
                duration = self.log_slot_test_stop(slot, "SETUP_ELBA_UBOOT_ENV", start_ts)
                ret = False
                continue
            else:
                self.cli_log_slot_inf(slot, "Setup boot to goldfw successfully")
            time.sleep(2)

            self._nic_ctrl_list[slot]._nic_handle.sendline("sysreset.sh")
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["Press enter"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)

            self._nic_ctrl_list[slot]._nic_handle.sendline("\n")
            time.sleep(1)
            self._nic_ctrl_list[slot]._nic_handle.sendline("\n")
            time.sleep(1)
            self._nic_ctrl_list[slot]._nic_handle.sendline("\n")
            time.sleep(1)
            self._nic_ctrl_list[slot]._nic_handle.sendline("\n")
            time.sleep(1)
            self._nic_ctrl_list[slot]._nic_handle.sendline("\n")
            time.sleep(1)

            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline("\n")
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            #self._nic_ctrl_list[slot]._nic_handle.sendline('mount -t ext4 /dev/mmcblk0p6 /sysconfig/config0')
            #idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            time.sleep(1)
            self._nic_ctrl_list[slot]._nic_handle.sendline('mount -t ext4 /dev/mmcblk0p6 /sysconfig/config0')
            time.sleep(1)
            self._nic_ctrl_list[slot]._nic_handle.sendline('rm /sysconfig/config0/device.conf')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["exists", "# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            time.sleep(1)
            self._nic_ctrl_list[slot]._nic_handle.sendline('echo { >> /sysconfig/config0/device.conf')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('echo \\"device-profile\\": \\"bitw-smart-service\\", >> /sysconfig/config0/device.conf')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('echo \\"memory-profile\\": \\"default\\", >> /sysconfig/config0/device.conf')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('echo \\"oper-mode\\": \\"bitw-smart-service\\", >> /sysconfig/config0/device.conf')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('echo \\"port-admin-state\\": \\"PORT_ADMIN_STATE_ENABLE\\", >> /sysconfig/config0/device.conf')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('echo \\"delay-host-bringup\\": \\"false\\" >> /sysconfig/config0/device.conf')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('echo } >> /sysconfig/config0/device.conf')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            time.sleep(1)
            self._nic_ctrl_list[slot]._nic_handle.sendline('sync')
            time.sleep(1)
            self._nic_ctrl_list[slot]._nic_handle.sendline('cat /sysconfig/config0/device.conf')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["}"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            time.sleep(2)
            self._nic_ctrl_list[slot]._nic_handle.sendline('board_config -w 8')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["successfully"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)

            if idx < 0:
                self.cli_log_err("[NIC-0{}] Setup board_config failure".format(slot+1))
                duration = self.log_slot_test_stop(slot, "SETUP_ELBA_UBOOT_ENV", start_ts)
                ret = False
                continue
            else:
                self.cli_log_slot_inf(slot, "Setup board_config successfully")
            time.sleep(2)

            #pdsctl show system --frequency
            self._nic_ctrl_list[slot]._nic_handle.sendline('pdsctl show system --frequency')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            time.sleep(5)

            self._nic_ctrl_list[slot]._nic_handle.sendline('/nic/tools/fwupdate -s goldfw')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            time.sleep(5)
            self._nic_ctrl_list[slot]._nic_handle.sendline('sync')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)

            self._nic_ctrl_list[slot]._nic_handle.sendline('rm /sysconfig/config0/prensando_pre_init.sh')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)

            self._nic_ctrl_list[slot]._nic_handle.sendline('rm /sysconfig/config0/pensando_pre_init.sh')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            ##!/bin/sh
            # self._nic_ctrl_list[slot]._nic_handle.sendline('echo \'#!/bin/sh\' >> /sysconfig/config0/pensando_pre_init.sh')
            # idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            # self._nic_ctrl_list[slot]._nic_handle.sendline('echo \'/nic/tools/fwupdate -s goldfw\' >> /sysconfig/config0/pensando_pre_init.sh')
            # idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            # self._nic_ctrl_list[slot]._nic_handle.sendline('echo \'sync\' >> /sysconfig/config0/pensando_pre_init.sh')
            # idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            # self._nic_ctrl_list[slot]._nic_handle.sendline('cat /sysconfig/config0/pensando_pre_init.sh')
            # idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            # time.sleep(5)

            # self._nic_ctrl_list[slot]._nic_handle.sendline('chmod +x /sysconfig/config0/pensando_pre_init.sh')
            # idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)

            # self._nic_ctrl_list[slot]._nic_handle.sendline('sh /sysconfig/config0/pensando_pre_init.sh')
            # idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["# "], timeout=MTP_Const.NIC_FSETUP_ELBA_UBOOT_DELAY)
            # time.sleep(5)

            self._nic_ctrl_list[slot]._nic_handle.sendline('sysreset.sh')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["Autoboot"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)

            #Send Ctrl-C by '\x03'
            self._nic_ctrl_list[slot]._nic_handle.sendline('\x03')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["DSC# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)          

            self._nic_ctrl_list[slot]._nic_handle.sendline('setenv memdp_tot_size 12G')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["DSC# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('setenv mem_bypass_size 0')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["DSC# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('setenv core_clock_freq 1100000000')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["DSC# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('setenv bootargs isolcpus=2,3,6,7,10,11,14,15 nohz_full=2,3,6,7,10,11,14,15 rcu_nocbs=2,3,6,7,10,11,14,15 rcu_nocb_poll irqaffinity=0-1 console=ttyS0,115200n8')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["DSC# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('saveenv')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["DSC# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('env print')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["DSC# "], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)
            self._nic_ctrl_list[slot]._nic_handle.sendline('reset')
            idx = libmfg_utils.mfg_expect(self._nic_ctrl_list[slot]._nic_handle, ["Press enter"], timeout=MTP_Const.TOR_ELBA_UBOOT_DELAY)


            if not self._nic_ctrl_list[slot].nic_console_detach():
                self._nic_ctrl_list[slot].nic_set_status(NIC_Status.NIC_STA_TERM_FAIL)
                duration = self.log_slot_test_stop(slot, "SETUP_ELBA_UBOOT_ENV", start_ts)
                ret = False
                continue

            duration = self.log_slot_test_stop(slot, "SETUP_ELBA_UBOOT_ENV", start_ts)

        return ret

    @single_slot_test("DL", "NIC_PROFILE_CONFIG")
    def tor_nic_Setup_device_config(self, slot):
        # removing this since not running this function before diag_init anymore
        # if not self.tor_nic_init():
        #     self.cli_log_err("Initialize NIC type, present failed", level=0)
        #     return False

        self.cli_log_slot_inf(slot, "Writing device.conf to NIC")
        if not self._nic_ctrl_list[slot].nic_setup_device_config():
            self.mtp_get_nic_err_msg(slot)
            self.cli_log_slot_err(slot, "Failed to save device.conf")
            return False

        # # Uboot env step removed for OS newer than Nov1 2021
        # if not self._nic_ctrl_list[slot].nic_console_uboot_env():
        #     self.mtp_get_nic_err_msg(slot)
        #     self.cli_log_slot_err(slot, "Failed to write env to uboot")
        #     return False

        return True

    def mtp_mgmt_set_nic_goldfw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_goldfw_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default gold boot failed")
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default gold boot")
        return True

    def tor_cpld_init(self, fpgautil_path=MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH):
        self._cpld_dat = dict()
        devices = { 
        "fpga", 
        "cpu",
        "gpio0",
        "gpio1",
        "gpio2",
        "elba 0",
        "elba 1"
        }
        for device in devices:
            uut_type = self._uut_type

            if device == "fpga":
                cmd = "{:s}fpgautil r32 0 0".format(fpgautil_path)
                if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["RD"], timeout=100):
                    self.cli_log_err("{:s} failed".format(cmd))
                    return False
            elif device.startswith("elba"):
                cmd = "{:s}fpgautil {:s} cpld uc".format(fpgautil_path, device)
                if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["UCODE"], timeout=100):
                    self.cli_log_err("{:s} failed".format(cmd))
                    return False
            else:
                cmd = "{:s}fpgautil cpld {:s} uc".format(fpgautil_path, device)
                if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["UCODE"], timeout=100):
                    self.cli_log_err("{:s} failed".format(cmd))
                    return False
            cmd_buf = self.mtp_get_cmd_buf()
            uc_match = re.search("= ?(0x[A-Fa-f0-9]{4}([A-Fa-f0-9]{4}))", cmd_buf)
            if uc_match:
                self._cpld_dat[device] = uc_match.group(2)
            else:
                return False

        return True

    def tor_cpld_prog(self, device, cpld_img_file, shipping_version, fpgautil_path=MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH):
        if self.tor_cpld_verify(shipping_version, device, True):
            self.cli_log_inf("CPLD is up-to-date")
            return True
        self.cli_log_inf("Downloading CPLD image")

        if not libmfg_utils.console_copy_file(self, TOR_IMAGES.TFTP_SERVER_IP, "/", TOR_IMAGES.TFTP_SERVER_DIR+cpld_img_file):
            self.cli_log_err("Unable to get {:s}".format(cpld_img_file), level=0)
            return False
        # else:
        #     ip_addr = self._mgmt_cfg[0]
        #     usrid = self._mgmt_cfg[1]
        #     passwd = self._mgmt_cfg[2]

        #     if not libmfg_utils.network_copy_file(ip_addr, usrid, passwd, cpld_img_file, "/", self._diag_filep):
        #         self.cli_log_err("Download CPLD image failed", level=0)
        #         return False

        devices = {
        "fpga": ["fpga"],
        "fpgatest": ["fpga"],
        "cpu": ["cpu"],
        "gpio": ["gpio0", "gpio1", "gpio2"],
        "elba 0": ["elba 0"],
        "elba 1": ["elba 1"]
        }
        for _device in devices[device]:
            if _device.startswith("fpga"):
                if "-dual-" in cpld_img_file:
                    self.cli_log_inf("Programming {:s}".format(_device))
                    cmd = "{:s}fpgautil flash program allflash /{:s}".format(fpgautil_path, os.path.basename(cpld_img_file))
                    if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Verification passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                        self.cli_log_err("{:s} failed".format(cmd))
                        return False

                    self.cli_log_inf("Verifying programmed {:s}".format(_device))
                    cmd = "{:s}fpgautil flash verify allflash /{:s}".format(fpgautil_path, os.path.basename(cpld_img_file))
                    if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Verification passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                        self.cli_log_err("{:s} failed".format(cmd))
                        return False
                else:
                    self.cli_log_inf("Programming primary {:s} partition".format(_device))
                    cmd = "{:s}fpgautil flash program primary /{:s}".format(fpgautil_path, os.path.basename(cpld_img_file))
                    if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Verification passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                        self.cli_log_err("{:s} failed".format(cmd))
                        return False

                    self.cli_log_inf("Verifying programmed primary {:s} partition".format(_device))
                    cmd = "{:s}fpgautil flash verify primary /{:s}".format(fpgautil_path, os.path.basename(cpld_img_file))
                    if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Verification passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                        self.cli_log_err("{:s} failed".format(cmd))
                        return False

                    self.cli_log_inf("Programming secondary {:s} partition".format(_device))
                    cmd = "{:s}fpgautil flash program secondary /{:s}".format(fpgautil_path, os.path.basename(cpld_img_file))
                    if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Verification passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                        self.cli_log_err("{:s} failed".format(cmd))
                        return False

                    self.cli_log_inf("Verifying programmed secondary {:s} partition".format(_device))
                    cmd = "{:s}fpgautil flash verify secondary /{:s}".format(fpgautil_path, os.path.basename(cpld_img_file))
                    if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Verification passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                        self.cli_log_err("{:s} failed".format(cmd))
                        return False

                continue

            elif _device.startswith("elba"):
                slot = int(_device[-1:])
                for partition in ["cfg0", "cfg1"]:
                    self.cli_log_slot_inf(slot, "Programming CPLD {:s} partition".format(partition))
                    cmd = "{:s}fpgautil {:s} cpld program {:s} /{:s}".format(fpgautil_path, _device, partition, os.path.basename(cpld_img_file))
                    if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Programming passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                        self.cli_log_err("Programming Elba{:d} CPLD failed".format(slot))
                        return False

                    self.cli_log_slot_inf(slot, "Verifying CPLD {:s} partition".format(partition))
                    cmd = "{:s}fpgautil {:s} cpld verifyimage {:s} /{:s}".format(fpgautil_path, _device, partition, os.path.basename(cpld_img_file))
                    if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Verification passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                        self.cli_log_err("Verifying Elba{:d} CPLD failed".format(slot))
                        return False

                continue

            self.cli_log_inf("Programming {:s} CPLD".format(_device))
            cmd = "{:s}fpgautil cpld {:s} program /{:s}".format(fpgautil_path, _device, os.path.basename(cpld_img_file))
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Programming passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                self.cli_log_err("{:s} failed".format(cmd))
                return False

            self.cli_log_inf("Verifying programmed {:s} CPLD".format(_device))
            cmd = "{:s}fpgautil cpld {:s} verifyimage /{:s}".format(fpgautil_path, _device, os.path.basename(cpld_img_file))
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Verification"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                self.cli_log_err("{:s} failed".format(cmd))
                return False
        return True

    def tor_cpld_ref(self, fpgautil_path=MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH):
        devices = ["gpio0", "gpio1", "gpio2"]
        for _device in devices:
            self.cli_log_inf("Refreshing {:s} CPLD".format(_device))
            cmd = "{:s}fpgautil cpld {:s} refresh".format(fpgautil_path, _device)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("{:s} failed".format(cmd))
                return False

        # refresh cpu cpld last, where we lose connection
        _device = "cpu"
        self.cli_log_inf("Refreshing {:s} CPLD".format(_device))
        self._mgmt_handle.sendline("{:s}fpgautil cpld {:s} refresh".format(fpgautil_path, _device))
        time.sleep(3)
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Timeout", "not responding."])
        while idx > 0:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Timeout", "not responding."])

        return True
    
    def tor_cpld_verify(self, ship_img=False, device="", silently=False):
        """
            ship_img: True for SWI, False otherwise
            device: verify only single device image
            silently: dont print an error message on version mismatch 
        """
        from itertools import chain

        devices = {
        "fpga": ["fpga"],
        "cpu": ["cpu"],
        "gpio": ["gpio0", "gpio1", "gpio2"],
        "elba 0": ["elba 0"],
        "elba 1": ["elba 1"]
        }
        
        if not self._cpld_dat or device == "":
            # reload all device versions
            if not self.tor_cpld_init():
                return False

        if device == "":
            # verify all devices if nothing supplied
            dlist = list(set(chain(*devices.values())))
        else:
            dlist = devices[device]

        for _device in dlist:
            if device == "":
                device = _device
            got_cpld_dat = self._cpld_dat[_device]
            if device.startswith("fpga"):
                if ship_img:
                    exp_cpld_dat = TOR_IMAGES.fpga_dat[self._uut_type]
                else:
                    exp_cpld_dat = TOR_IMAGES.test_fpga_dat[self._uut_type]
            elif device.startswith("cpu"):
                if ship_img:
                    exp_cpld_dat = TOR_IMAGES.cpu_cpld_ship_dat[self._uut_type]
                else:
                    exp_cpld_dat = TOR_IMAGES.cpu_cpld_test_dat[self._uut_type]
            elif device.startswith("gpio"):
                if ship_img:
                    exp_cpld_dat = TOR_IMAGES.gpio_cpld_ship_dat[self._uut_type]
                else:
                    exp_cpld_dat = TOR_IMAGES.gpio_cpld_test_dat[self._uut_type]
            elif device.startswith("elba"):
                if ship_img:
                    exp_cpld_dat = NIC_IMAGES.sec_cpld_dat[self._uut_type]
                else:
                    exp_cpld_dat = NIC_IMAGES.cpld_dat[self._uut_type]
            else:
                self.cli_log_err("Unknown device {:s}".format(device))
                return False

            if got_cpld_dat == exp_cpld_dat:
                return True
            else:
                if not silently:
                    self.cli_log_err("{:s} Incorrect CPLD version: {:s}, expect: {:s}".format(_device, got_cpld_dat, exp_cpld_dat))
                return False

        return True

    def tor_fea_cpld_prog(self, device, cpld_img_file, fpgautil_path=MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH):
        self.cli_log_inf("Downloading CPLD feature row image")

        if not libmfg_utils.console_copy_file(self, TOR_IMAGES.TFTP_SERVER_IP, "/", TOR_IMAGES.TFTP_SERVER_DIR+cpld_img_file):
            self.cli_log_err("Unable to get {:s}".format(cpld_img_file), level=0)
            return False
        # else:
        #     ip_addr = self._mgmt_cfg[0]
        #     usrid = self._mgmt_cfg[1]
        #     passwd = self._mgmt_cfg[2]

        #     if not libmfg_utils.network_copy_file(ip_addr, usrid, passwd, cpld_img_file, "/", self._diag_filep):
        #         self.cli_log_err("Download CPLD image failed", level=0)
        #         return False

        devices = {
        "elba 0": ["elba 0"],
        "elba 1": ["elba 1"]
        }
        for _device in devices[device]:
            slot = int(_device[-1:])
            for partition in ["fea"]:
                # dump programmed
                cmd = "{:s}fpgautil {:s} cpld featurerow".format(fpgautil_path, _device)
                dumprowdatasuccess = False
                for x in range(3):
                    if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                        self.cli_log_err("Dumping Elba{:d} CPLD feature row failed".format(slot))
                        time.sleep(5)
                        #return False
                    else:
                        fea_nic_dump = self.mtp_get_cmd_buf()
                        fea_nic_regex = r" ([0-9 ]*) "
                        fea_nic_match = re.search(fea_nic_regex,fea_nic_dump)

                        if fea_nic_match:
                            dumprowdatasuccess = True
                            break
                        else:
                            time.sleep(5)
                if not dumprowdatasuccess:
                    return False
                fea_nic_dump = self.mtp_get_cmd_buf()
                fea_nic_regex = r" ([0-9 ]*) "
                fea_nic_match = re.search(fea_nic_regex,fea_nic_dump)

                if fea_nic_match:
    
                    if fea_nic_match.group(1) == NIC_IMAGES.fea_cpld_dat[self._uut_type]:
                        self.cli_log_slot_inf(slot, "CPLD feature row up-to-date")
                        return True
                    self.cli_log_slot_inf(slot, "Verifying CPLD feature row image")
                    cmd = "{:s}fpgautil {:s} cpld verifyimage {:s} /{:s}".format(fpgautil_path, _device, partition, os.path.basename(cpld_img_file))
                    if self.mtp_mgmt_exec_cmd_no_error_printout(cmd, sig_list=["Verification passed"], timeout=MTP_Const.TOR_VERIFY_FEATURE_ROW_DELAY):
                        self.cli_log_slot_inf(slot, "Verifying Elba{:d} CPLD feature row Passed, CPLD feature row up-to-date".format(slot))
                        return True
                    # else: go ahead & program
                    # self.cli_log_slot_err_lock(slot, "Feature row programmed incorrectly. Dump doesn't match original file.")
                    # return False
                else:
                    self.cli_log_slot_err_lock(slot, "Unable to dump feature row.")
                    return False

                self.cli_log_slot_inf(slot, "Programming CPLD feature row image")
                cmd = "{:s}fpgautil {:s} cpld program {:s} /{:s}".format(fpgautil_path, _device, partition, os.path.basename(cpld_img_file))
                if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Programming passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                    self.cli_log_err("Programming Elba{:d} CPLD feature row failed".format(slot))
                    return False

                self.cli_log_slot_inf(slot, "Verifying CPLD feature row image")
                cmd = "{:s}fpgautil {:s} cpld verifyimage {:s} /{:s}".format(fpgautil_path, _device, partition, os.path.basename(cpld_img_file))
                if not self.mtp_mgmt_exec_cmd(cmd, sig_list=["Verification passed"], timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
                    self.cli_log_err("Verifying Elba{:d} CPLD feature row failed".format(slot))
                    return False

        return True

    def tor_td_gearbox_verify(self):
        """
            Screen for Rev B gearbox
        """
        # libmfg_utils.count_down(180) # waiting for bcm shell to bring up port 1943
        cmd = "{:s}fpgautil td3 checkgb".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list="PASS:", timeout=120):
            return False
        return True

    def tor_nic_cpld_prog(self, slot, cpld_img_file, fpgautil_path=MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH):
        ip_addr = self._mgmt_cfg[0]
        usrid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        self.cli_log_slot_inf(slot, "Downloading CPLD image")
        if not libmfg_utils.network_copy_file(ip_addr, usrid, passwd, cpld_img_file, "/", self._nic_ctrl_list[slot]._diag_filep):
            self.cli_log_err("Copy CPLD image failed", level=0)
            return False

        self.cli_log_slot_inf(slot, "Programming CPLD cfg0 partition")
        cmd = "{:s}fpgautil elba {:d} cpld program cfg0 /{:s}".format(fpgautil_path, slot, os.path.basename(cpld_img_file))
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
            self.cli_log_err("{:s} failed".format(cmd))
            return False
        cmd_buf = self._nic_ctrl_list[slot].nic_get_cmd_buf()
        if "Programming passed" not in cmd_buf:
            self.cli_log_err("Programming Elba{:d} CPLD failed".format(slot))
            return False

        self.cli_log_slot_inf(slot, "Verifying CPLD cfg0 partition")
        cmd = "{:s}fpgautil elba {:d} cpld verifyimage cfg0 /{:s}".format(fpgautil_path, slot, os.path.basename(cpld_img_file))
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
            self.cli_log_err("{:s} failed".format(cmd))
            return False
        cmd_buf = self._nic_ctrl_list[slot].nic_get_cmd_buf()
        if "Verification passed" not in cmd_buf:
            self.cli_log_err("Verifying Elba{:d} CPLD failed".format(slot))
            return False

        return True

    def tor_nic_failsalfe_cpld_prog(self, slot, cpld_img_file):
        ip_addr = self._mgmt_cfg[0]
        usrid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        self.cli_log_slot_inf(slot, "Downloading failsafe CPLD image")
        if not libmfg_utils.network_copy_file(ip_addr, usrid, passwd, cpld_img_file, "/", self._nic_ctrl_list[slot]._diag_filep):
            self.cli_log_err("Copy CPLD image failed", level=0)
            return False

        self.cli_log_slot_inf(slot, "Programming CPLD cfg1 partition")
        cmd = "{:s}fpgautil elba {:d} cpld program cfg1 /{:s}".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, slot, os.path.basename(cpld_img_file))
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
            self.cli_log_err("{:s} failed".format(cmd))
            return False
        cmd_buf = self._nic_ctrl_list[slot].nic_get_cmd_buf()
        if "Programming passed" not in cmd_buf:
            self.cli_log_err("Programming Elba{:d} CPLD failed".format(slot))
            return False

        self.cli_log_slot_inf(slot, "Verifying CPLD cfg1 partition")
        cmd = "{:s}fpgautil elba {:d} cpld verifyimage cfg1 /{:s}".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, slot, os.path.basename(cpld_img_file))
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
            self.cli_log_err("{:s} failed".format(cmd))
            return False
        cmd_buf = self._nic_ctrl_list[slot].nic_get_cmd_buf()
        if "Verification passed" not in cmd_buf:
            self.cli_log_err("Verifying Elba{:d} CPLD failed".format(slot))
            return False


        return True

    def tor_nic_fea_cpld_prog(self, slot, cpld_img_file):
        ip_addr = self._mgmt_cfg[0]
        usrid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        self.cli_log_slot_inf(slot, "Downloading CPLD feature row image")
        if not libmfg_utils.network_copy_file(ip_addr, usrid, passwd, cpld_img_file, "/", self._nic_ctrl_list[slot]._diag_filep):
            self.cli_log_err("Copy CPLD feature row image failed", level=0)
            return False

        self.cli_log_slot_inf(slot, "Programming CPLD feature row")
        cmd = "{:s}fpgautil elba {:d} cpld program fea /{:s}".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, slot, os.path.basename(cpld_img_file))
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
            self.cli_log_err("{:s} failed".format(cmd))
            return False
        cmd_buf = self._nic_ctrl_list[slot].nic_get_cmd_buf()
        if "Programming passed" not in cmd_buf:
            self.cli_log_err("Programming Elba{:d} CPLD feature row failed".format(slot))
            return False

        self.cli_log_slot_inf(slot, "Verifying CPLD feature row  partition")
        cmd = "{:s}fpgautil elba {:d} cpld verifyimage fea /{:s}".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, slot, os.path.basename(cpld_img_file))
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=MTP_Const.TOR_CPLD_PROG_DELAY):
            self.cli_log_err("{:s} failed".format(cmd))
            return False
        cmd_buf = self._nic_ctrl_list[slot].nic_get_cmd_buf()
        if "Verification passed" not in cmd_buf:
            self.cli_log_err("Verifying Elba{:d} CPLD feature row failed".format(slot))
            return False


        return True

    def tor_nic_cpld_refresh(self, slot):
        self._mgmt_handle.sendline("{:s}fpgautil elba {:d} cpld refresh".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, slot))
        time.sleep(3)
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Refresh performed"])
        while idx > 0:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["Refresh performed"])

        return True

    def tor_pcie_enum(self, slot):
        """
            Enumerate and verify PCIE linkup between x86 and ASIC
        """

        # cmd = "/home/diag/diag/tools/td.bash rescan"
        cmd = "/fs/nos/eeupdate/td.bash rescan"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.TOR_PCIE_SCAN_DELAY):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        if not self.mtp_mgmt_exec_cmd("lspci -d 1dd8:0002"):
            print("6")
            self.mtp_mgmt_exec_cmd("lspci -tv")

        if not self.mtp_mgmt_exec_cmd("lspci -vvv -s 0:3.2 | grep LnkSta:"):
            print("7")

        if not self.mtp_mgmt_exec_cmd("lspci -vvv -s 0:3.0 | grep LnkSta:"):
            print("8")

        return True

    def tor_nic_avs_set(self, slot):
        cmd = "{:s}fpgautil i2c 2 {:d} 0x4a w 0x22 0xA0".format(MTP_DIAG_Path.ONBOARD_NIC_UTIL_PATH, slot+2)
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, sig_list="WR:"):
            return False

        if not self.mtp_mgmt_set_nic_avs(slot):
            return False

        return True

    def tor_nic_config_erase(self, slot):
        if not self._nic_ctrl_list[slot].nic_config_erase():
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def tor_nic_fwenv_erase(self, slot):
        if not self._nic_ctrl_list[slot].nic_fwenv_erase():
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def tor_nic_config_verify(self, slot):
        if not self._nic_ctrl_list[slot].nic_config_verify():
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def tor_nic_fw_verify(self, slot):
        if not self._nic_ctrl_list[slot].nic_fw_verify():
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def tor_isp_enable(self):

        cmd = "hpe-isp config show"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd = "hpe-isp config default"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd_buf = ""

        time.sleep(5)

        cmd = "hpe-isp config enable"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd_buf += self.mtp_get_cmd_buf()

        time.sleep(5)

        cmd = "hpe-isp config unsafe 60"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd_buf += self.mtp_get_cmd_buf()

        time.sleep(5)

        cmd = "hpe-isp config show"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd_buf += self.mtp_get_cmd_buf()

        time.sleep(5)
        
        if "enabled" not in cmd_buf:
            self.cli_log_err("ISP not enabled", level=0)
            return False

        if "allowed" not in cmd_buf:
            self.cli_log_err("Unsafe updates blocked", level=0)
            return False

        # reboot required to reflect changes

        return True

    def tor_isp_disable(self):
        cmd = "hpe-isp config default"
        cmd_buf = ""
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd_buf += self.mtp_get_cmd_buf()

        time.sleep(5)

        cmd = "hpe-isp config show"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd_buf += self.mtp_get_cmd_buf()

        time.sleep(5)

        if "enabled" in cmd_buf:
            self.cli_log_err("ISP still enabled", level=0)
            return False

        if "not allowed" not in cmd_buf:
            self.cli_log_err("Unsafe updates not blocked", level=0)
            return False

        return True

    def tor_sw_cleanup(self):
        cmd = MFG_DIAG_CMDS.TOR_CLEANUP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd = "ls /fs/nos/"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd = MFG_DIAG_CMDS.TOP_CLEANUP_SELTTEST_FILE
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd = "ls /fs/selftest/"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        return True
        
    def tor_set_vmarg(self, vmarg):
        if vmarg > 0:
            vmarg_param = "high"
        elif vmarg == 0:
            vmarg_param = "normal"
        else:
            vmarg_param = "low"
        self.cli_log_inf("Set voltage margin to {:s}".format(vmarg_param), level=0)

        cmd = MFG_DIAG_CMDS.TOR_VMARG_SET_FMT.format(MTP_DIAG_Path.ONBOARD_TOR_DIAG_PATH, vmarg_param)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Set voltage margin to {:s} failed".format(vmarg_param), level=0)
            return False
        return True

    def tor_clear_ut_mark(self):
        """
        root@tb57-host2-cimc:/fs/nos/home_diag/diag/scripts/taormina# ./verify-ut-mark.sh
        verify-ut-mark: product name : 10000
        verify-ut-mark: part #       : R8S96A
        verify-ut-mark: serial #     : FSJ2144000F
        verify-ut-mark: UT mark is set.
        root@tb57-host2-cimc:/fs/nos/home_diag/diag/scripts/taormina# ./clear-ut-mark.sh
        clear-ut-mark: product name : 10000
        clear-ut-mark: part #       : R8S96A
        clear-ut-mark: serial #     : FSJ2144000F
        root@tb57-host2-cimc:/fs/nos/home_diag/diag/scripts/taormina# ./verify-ut-mark.sh
        verify-ut-mark: product name : 10000
        verify-ut-mark: part #       : R8S96A
        verify-ut-mark: serial #     : FSJ2144000F
        verify-ut-mark: UT mark is clear.
        """

        cmd = "{:s}verify-ut-mark.sh".format(MTP_DIAG_Path.ONBOARD_TOR_DIAG_PATH + "/diag/scripts/taormina/")
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Unable to verify UT mark", level=0)
            return False

        cmd = "{:s}clear-ut-mark.sh".format(MTP_DIAG_Path.ONBOARD_TOR_DIAG_PATH + "/diag/scripts/taormina/")
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Unable to clear UT mark", level=0)
            return False

        cmd = "{:s}verify-ut-mark.sh".format(MTP_DIAG_Path.ONBOARD_TOR_DIAG_PATH + "/diag/scripts/taormina/")
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Unable to verify UT mark", level=0)
            return False

        cmd_buf = self.mtp_get_cmd_buf()
        if "UT mark is clear" not in cmd_buf:
            self.cli_log_err("UT mark still not cleared", level=0)
            return False

        return True

    def tor_pcie_scan(self):
        """
        root@host1:~# lspci -s b:00.00 -vvv | grep LnkSta:
                LnkSta: Speed 8GT/s (ok), Width x4 (ok)
        root@host1:~# lspci -s 5:00.00 -vvv | grep LnkSta:
                LnkSta: Speed 8GT/s (ok), Width x1 (downgraded)
        """
        for slot in range(0,2):
            bus = NIC_IP_Address.PCI_BUS[slot]

            cmd = "lspci -s {:s} -vvv | grep LnkSta:".format(bus)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_slot_err(slot, "Executing command {:s} failed".format(cmd))
                return False
            cmd_buf = self.mtp_get_cmd_buf()

            if "Speed 8GT/s" in cmd_buf and "Width x4" in cmd_buf:
                continue
            else:
                self.cli_log_slot_err(slot, "PCIe link to Elba {:s} failed speed and width check".format(slot))
                self.mtp_dump_nic_err_msg(cmd_buf)
                return False

        return True

    def tor_copy_sys_log(self, dest_folder, local_copy=False):
        self.cli_log_inf("Copying system logs", level=0)

        logfiles = (
            "/var/log/messages",
            "/var/log/critical.log",
            "/var/log/event.log",
            "/var/log/pensando/dsm0_uart.log",
            "/var/log/pensando/dsm1_uart.log"
            )

        for filename in logfiles:
            if not self.tor_file_exists(filename):
                continue
            # copy them so they stop changing
            cmd = "cp {:s} /{:s}".format(filename, os.path.basename(filename))
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Couldn't save system logfile safely", level=0)
                continue
            cmd = "chmod +r /{:s}".format(os.path.basename(filename))
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Couldn't change system logfile permissions", level=0)
                continue
            filename = "/"+os.path.basename(filename)
            dest_name = dest_folder + filename
            if not dest_name.endswith(".log"):
                dest_name = dest_name + ".log"
            if local_copy:
                if not self.mtp_mgmt_exec_cmd("cp {:s} {:s}".format(filename, dest_name)):
                    self.cli_log_err("Unable to copy UUT system log file {:} locally".format(filename), level=0)
                    continue
            else:
                if not libmfg_utils.network_get_file(self, dest_name, filename): #open("scp.log", "w+")):
                    self.cli_log_err("Unable to copy UUT system log file {:}".format(filename), level=0)
                    continue

        handle = pexpect.spawn("ls {:s}".format(dest_folder))
        handle.expect("$")
        handle.sendline("ls {:s}".format(dest_folder))
        handle.expect("$")
        handle.close()

        return True

    def tor_ping_test(self):
        # cmd = "#== Testing connection to UUT"
        # cmd_buf = libmfg_utils.host_shell_cmd(self, cmd)
        # if cmd_buf is None:
        #     self.cli_log_err("Command {:s} failed".format(cmd))
        #     return False

        ip = self._mgmt_cfg[0]
        cmd = "ping -c 4 {:s}".format(ip)
        cmd_buf = libmfg_utils.host_shell_cmd(self, cmd, timeout=10)
        if cmd_buf is None:
            self.cli_log_err("Command {:s} failed".format(cmd))
            return False
        match = re.findall(r" 0% packet loss", cmd_buf)
        if not match:
            return False

        return True

    def tor_dsp_failure_dump(self):
        """
            - check IP is pingable
            - dont create new session
        """
        if self._svos_boot:
            self.cli_log_err("Script error: this function is only for 2C")
            return False

        if not self._mgmt_cfg:
            return False

        if not self.tor_ping_test():
            self.cli_log_err("Ping to UUT failed")
            self.set_hard_failure()
            return False

        if not self.tor_get_ip():
            self.cli_log_err("UUT chassis lost IP")
            self.set_hard_failure()
            return False

        if not self.mtp_mgmt_exec_cmd("uptime"):
            self.set_hard_failure()
            return False

        if not self.mtp_mgmt_exec_cmd("ls /fs/nos/"):
            self.set_hard_failure()
            return False

        return True

    def tor_sys_failure_dump(self):
        """
            At any test failure on x86 side:
            - check IP is pingable
            - check console is alive
            - check trident is alive: dump show module to see if trident is ready or down, check bcmshell responsive, pcie
            - If we have fpga version 1 and above, we can dump resetcause0 register as well

        """
        if not self.mtp_console_connect():
            self.cli_log_err("Unable to telnet to UUT chassis")

        if not self._svos_boot:
            if not self.tor_get_ip():
                self.cli_log_err("UUT chassis lost IP")
                return False

            if not self.mtp_mgmt_connect():
                self.cli_log_err("Unable to ssh to UUT chassis")
                return False

        if not self.mtp_mgmt_exec_cmd("uptime"):
            return False

        if not self.mtp_mgmt_exec_cmd("ls /fs/nos/"):
            return False

        return True

    def tor_file_exists(self, filename):
        cmd = "ls --color=never {:s}".format(os.path.dirname(filename))
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False

        cmd_buf = self.mtp_get_cmd_buf().split()
        if os.path.basename(filename) in cmd_buf:
            return True
        else:
            return False

    def tor_nic_failure_dump(self, slot):
        self.cli_log_slot_inf(slot, "Getting NIC status for failure dump")
        self._nic_ctrl_list[slot].mtp_exec_cmd("######## {:s} ########".format("START failure dump"))
        self._nic_ctrl_list[slot].mtp_exec_cmd("killall tclsh")
        self.mtp_mgmt_exec_cmd(MFG_DIAG_CMDS.TOR_NIC_STS_FMT.format(MTP_DIAG_Path.ONBOARD_TOR_DIAG_PATH, int(slot)-1))
        self._nic_ctrl_list[slot].mtp_exec_cmd("killall tclsh")
        self._nic_ctrl_list[slot].mtp_exec_cmd("######## {:s} ########".format("END failure dump"))

    def parse_fpgautil(self, cmd_buf):
        missing_list = list()

        module_regexp = {
            "PSU": r'%s.*H/W Rev: *(.*) *S/N: *(.*) *F/W.*: *(.*)',
            "FAN": r'%s: *PRESENT',
            "SSD": r'%s MODEL: *(.*) *S/N: *(.*) *Capacity: *(.*[TGMK]B)',
            "MEMORY": r'%s: *PN: *(.*) SN: *(.*) SIZE: *(.*)',
            "SFP":  r'[^Q]%s *(.*)PN: *(.*)SN: *([A-Za-z0-9]*) *BITRATE: *([1-9][0-9\.]* [GMK]b/s)',
            "QSFP": r'%s *(.*)PN: *(.*)SN: *([A-Za-z0-9]*) *BITRATE: *([1-9][0-9\.]* [GMK]b/s)'
        }

        for module in self.sys_modules["PSU"].keys():
            regexp = module_regexp["PSU"] % module
            match = re.search(regexp, cmd_buf)
            if not match:
                missing_list.append(module)
                continue
            module_info_list = list()
            module_info_list.append(match.group(1).strip()) #H/W Rev
            module_info_list.append(match.group(2).strip()) #S/N
            module_info_list.append(match.group(3).strip()) #F/W
            self.sys_modules["PSU"][module] = module_info_list[:]

        for module in self.sys_modules["FAN"].keys():
            regexp = module_regexp["FAN"] % module
            match = re.search(regexp, cmd_buf)
            if not match:
                missing_list.append(module)
                continue
            self.sys_modules["FAN"][module] = "PRESENT"

        for module in self.sys_modules["SSD"].keys():
            regexp = module_regexp["SSD"] % module
            match = re.search(regexp, cmd_buf)
            if not match:
                missing_list.append(module)
                continue
            module_info_list = list()
            module_info_list.append(match.group(1).strip()) #MODEL
            module_info_list.append(match.group(2).strip()) #S/N
            module_info_list.append(match.group(3).strip()) #CAPACITY
            self.sys_modules["SSD"][module] = module_info_list[:]

        for module in self.sys_modules["MEMORY"].keys():
            regexp = module_regexp["MEMORY"] % module
            match = re.search(regexp, cmd_buf)
            if not match:
                missing_list.append(module)
                continue
            module_info_list = list()
            module_info_list.append(match.group(1).strip()) #PN
            module_info_list.append(match.group(2).strip()) #SN
            module_info_list.append(match.group(3).strip()) #SIZE
            self.sys_modules["MEMORY"][module] = module_info_list[:]

        for module in self.sys_modules["SFP"].keys():
            regexp = module_regexp["SFP"] % module
            match = re.search(regexp, cmd_buf)
            if not match:
                missing_list.append(module)
                continue
            module_info_list = list()
            module_info_list.append(match.group(1).strip()) #PN
            module_info_list.append(match.group(2).strip()) #SN
            module_info_list.append(match.group(3).strip()) #BITRATE
            self.sys_modules["SFP"][module] = module_info_list[:]

        for module in self.sys_modules["QSFP"].keys():
            regexp = module_regexp["QSFP"] % module
            match = re.search(regexp, cmd_buf)
            if not match:
                missing_list.append(module)
                continue
            module_info_list = list()
            module_info_list.append(match.group(1).strip()) #PN
            module_info_list.append(match.group(2).strip()) #SN
            module_info_list.append(match.group(3).strip()) #BITRATE
            self.sys_modules["QSFP"][module] = module_info_list[:]

        return missing_list

    def tor_present_sanity_check(self):
        # check presence of PSUs, FANs, SFPs, QSFPs
        test = "PRESENT_CHECK"

        retry_cnt = 3
        while True:
            cmd = "{:s}fpgautil inventory".format(MTP_DIAG_Path.ONBOARD_TOR_EEUPDATE_PATH)
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=120):
                self.cli_log_err("{:s} failed".format(cmd), level=0)
                return False

            cmd_buf = self.mtp_get_cmd_buf()
            if not cmd_buf:
                self.cli_log_err("{:s} returned nothing".format(cmd), level=0)
                return False

            missing_list = self.parse_fpgautil(cmd_buf)
            if len(missing_list) == 0:
                return True
            else:
                for module in missing_list:
                    self.cli_log_err("[{:s}] {:s} module missing".format(test, module))

            retry_cnt -= 1
            if retry_cnt >= 0:
                libmfg_utils.aruba_gui_clear_buffer2()
                raw_input("Please re-insert the modules above then press any key to continue.\n")
                self.cli_log_inf("Rerunning sanity check...")
                continue
            else:
                break

        return False

    def tor_linkup_sanity_check(self):
        # since ports are not enabled by default, need diag PRBS to take care of enabling the ports.
        test = "LINK_CHECK"

        retry_cnt = 3
        while retry_cnt > 0:
            cmd = "cd /fs/nos/home_diag/diag/util"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("{:s} failed".format(cmd), level=0)
                return False

            prbs_type = "prbs58"
            prbs_duration = "5"
            cmd = "./switch td3 prbs {:s} {:s}".format(prbs_duration, prbs_type)
            test_timeout = self.get_test_timeout(cmd, "PRBS_TOR")
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=test_timeout+int(prbs_duration)):
                self.cli_log_err("{:s} failed".format(cmd))
                return False
            cmd_buf = self.mtp_get_cmd_buf()
            if "PRBS PASSED" not in cmd_buf:
                # self.mtp_dump_err_msg(cmd_buf)
                ports_down = re.findall(r'(Port-\d+) .*LINK DOWN', cmd_buf)
                ports_missing = re.findall(r'(Q?SFP\-\d+) is not detecting presence', cmd_buf)
                if len(ports_down) == 0 and len(ports_missing) == 0:
                    self.cli_log_err("Failed to run PRBS", level=0)
                    return False

                for port in ports_down + ports_missing:
                    self.cli_log_err("[{:s}] {:s} module missing".format(test, port))

                libmfg_utils.aruba_gui_clear_buffer2()
                raw_input("Please re-insert the modules above then press any key to continue.\n")
                self.cli_log_inf("Rerunning sanity check...")

                retry_cnt -= 1
                continue
            else:
                return True

        return False

    def tor_usb_sanity_check(self):
        # check presence of PSUs, FANs, SFPs, QSFPs
        test = "PRESENT_CHECK"

        cmd = "lsusb"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=120):
            self.cli_log_err("{:s} failed".format(cmd), level=0)
            return False

        retry_cnt = 3
        while True:
            cmd = 'dmesg | grep "USB Mass Storage"'
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=120):
                self.cli_log_err("{:s} failed".format(cmd), level=0)
                return False

            cmd_buf = self.mtp_get_cmd_buf()
            if not cmd_buf:
                self.cli_log_err("{:s} returned with no output".format(cmd), level=0)
                return False

            if "USB Mass Storage device detected" in cmd_buf:
                # USB is present, now check that it's formatted correctly

                cmd = "fdisk -l /dev/sdb"
                if not self.mtp_mgmt_exec_cmd(cmd, timeout=120):
                    self.cli_log_err("{:s} failed".format(cmd), level=0)
                    return False

                cmd_buf = self.mtp_get_cmd_buf()
                if not cmd_buf:
                    self.cli_log_err("{:s} returned with no output".format(cmd), level=0)
                    return False

                if "FAT32" in cmd_buf:
                    return True
                else:
                    self.cli_log_err("USB has bad formatting", level=0)
                    self.cli_log_err("[{:s}] {:s} module missing".format(test, "USB"))
            else:
                self.cli_log_err("[{:s}] {:s} module missing".format(test, "USB"))

            retry_cnt -= 1
            if retry_cnt >= 0:
                libmfg_utils.aruba_gui_clear_buffer2()
                raw_input("Please re-insert the modules above then press any key to continue.\n")
                self.cli_log_inf("Rerunning sanity check...")
                continue
            else:
                break

        return False

    def print_script_version(self):
        script_ver_match = re.search("image_amd64_.....?_(.*)\.tar", MTP_IMAGES.AMD64_IMG["ELBA"])
        if script_ver_match:
            script_ver = script_ver_match.group(1)
        else:
            script_ver = ""
        self.cli_log_report_inf("MFG Script Version: {:s}".format(script_ver))

    def mtp_mgmt_clear_nic_ssh(self, slot):
        if not self._nic_ctrl_list[slot].nic_console_check_ssh_folder():
            self.cli_log_slot_inf(slot, "Required SSH files missing on NIC... clearing folder to reset")
            self.mtp_clear_nic_err_msg() # clear out the error message
            if not self._nic_ctrl_list[slot].nic_console_clear_ssh_folder():
                self.cli_log_slot_err(slot, "Failed to setup NIC ssh folder")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False

        return True


