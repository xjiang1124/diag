import pexpect
import time
import os
import sys
import libmfg_utils
import re
import threading
import shutil
import json
from datetime import datetime
import ipaddress
import traceback
import barcode_field as bf
from libmfg_cfg import *
from libsku_utils import *
from libsku_cfg import *

from libdefs import NIC_Type
from libdefs import PRODUCT_SKU
from libdefs import MTP_TYPE
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
from libdefs import Voltage_Margin
from libdefs import Factory
from libnic_ctrl import nic_ctrl
from libmtp_health import mtp_health_ctrl

import test_utils
import parallelize
import image_control
import scanning




class mtp_ctrl():
    def __init__(self, mtpid, filep, diag_log_filep, diag_nic_log_filep_list, diag_cmd_log_filep=None, ts_cfg=None, mgmt_cfg=None, apc_cfg=None, slots_to_skip=[False]*MTP_Const.MTP_SLOT_NUM, dbg_mode=False):
        self._id = mtpid
        self._mtp_sn = None
        self._mtp_mac = None
        self._ts_handle = None
        self._mgmt_handle = None
        self._mgmt_prompt = None
        self._mgmt_timeout = MTP_Const.MTP_POWER_ON_TIMEOUT
        self._ts_cfg = ts_cfg
        self._mgmt_cfg = mgmt_cfg
        self._apc_cfg = apc_cfg
        self._prompt_list = libmfg_utils.get_linux_prompt_list()
        self._valid_type_list = MFG_VALID_NIC_TYPE_LIST
        self._proto_type_list = MFG_PROTO_NIC_TYPE_LIST
        self._valid_pn_list = MFG_VALID_NIC_PN_LIST
        self._slots = MTP_Const.MTP_SLOT_NUM
        self._slots_to_skip = slots_to_skip
        self._fans = 3
        self._psu_num = 2
        self._status = MTP_Status.MTP_STA_POWEROFF
        self._fanspd = MTP_Const.MFG_EDVT_NORM_FAN_SPD    # variable to track the fan speed (%) set by the script
        self._factory_location = Factory.UNKNOWN
        self._mtp_health = mtp_health_ctrl(mtpid, mgmt_health_cfg=mgmt_cfg, apc_health_cfg=apc_cfg)

        self._nic_ctrl_list = [None] * self._slots
        self._nic_alom_ctrl_list = [None] * self._slots
        self._nic_type_list = [None] * self._slots
        self._nic_prsnt_list = [False] * self._slots
        self._nic_scan_prsnt_list = [False] * self._slots
        self._nic_sn_list = [None] * self._slots
        self._nic_scan_sn_list = [None] * self._slots
        self._nic_alom_sn_list = [None] * self._slots
        self._nic_status_before_hide_list = [NIC_Status.NIC_STA_OK] * self._slots
        self._nic_sw_pn_list = [None] * self._slots
        self.barcode_scans = dict()

        self._nic_thread_list = [None] * self._slots
        # lock for printing
        self._lock = threading.Lock()
        # locks for sequential portion inside parallel test
        self._nic_console_lock = threading.Lock()
        self._j2c_lock = threading.Lock()
        # lock for coordinating j2c tests on turbo MTP
        self._turbo_j2c_lock = [threading.Lock() for x in range(self._slots)]

        self._io_cpld_ver = None
        self._jtag_cpld_ver = None
        # self._fpga_ver = (version, datecode, timestamp) if assigned
        self._fpga_ver = None
        self._mtp_type = None
        self._mtp_rev = None
        self._os_ver = None
        self._diag_ver = None
        self._asic_ver = None
        self._asic_hashtag = None
        self._cns_pmci_ver = None
        self._script_ver = ""
        self._swmtestmode = [Swm_Test_Mode.SWMALOM] * self._slots
        self._fst_ver = None
        self._psu_sn = dict()

        self._debug_mode = dbg_mode
        self._filep = filep
        self._cmd_buf = None
        self._buf_before_sig = None
        self._diag_filep = diag_log_filep
        self._diag_cmd_filep = diag_cmd_log_filep
        self._diag_nic_filep_list = diag_nic_log_filep_list[:]
        self._diagmgr_logfile = None
        self._temppn = None
        self._test_log_folder = None  # relative path to log folder
        self._open_file_handles = []
        self.stop_on_err = False
        self.CMDLINE_PASSIN_VMARG = ""

    def _propogate_properties_to_nic(self, slot):
        if self._nic_ctrl_list[slot]:
            self._nic_ctrl_list[slot]._mtp_type = self._mtp_type
            self._nic_ctrl_list[slot].stop_on_err = self.stop_on_err

    def cli_log_inf(self, msg, level=0):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp=self._id)
        indent = "    " * level
        if self._filep and not self._filep.closed:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(cli_id_str + indent + msg)

    def cli_log_report_inf(self, msg):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp=self._id)
        prefix = "==> "
        postfix = " <=="
        if self._filep and not self._filep.closed:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + prefix + msg + postfix)
        else:
            libmfg_utils.cli_inf(cli_id_str + prefix + msg + postfix)

    def cli_log_err(self, msg, level=0):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp=self._id)
        indent = "    " * level
        if self._filep and not self._filep.closed:
            libmfg_utils.cli_log_err(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_err(cli_id_str + indent + msg)

    def cli_log_wrn(self, msg, level=0):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp=self._id)
        indent = "    " * level
        if self._filep and not self._filep.closed:
            libmfg_utils.cli_log_wrn(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_wrn(cli_id_str + indent + msg)

    def cli_log_inf_lock(self, msg, level=0):
        self._lock.acquire()
        self.cli_log_inf(msg, level)
        self._lock.release()

    def cli_log_err_lock(self, msg, level=0):
        self._lock.acquire()
        self.cli_log_err(msg, level)
        self._lock.release()

    def cli_log_slot_inf(self, slot, msg, level=0):
        if msg is None:
            msg = ""
        nic_cli_id_str = libmfg_utils.id_str(mtp=self._id, nic=slot)
        indent = "    " * level
        if self._filep and not self._filep.closed:
            libmfg_utils.cli_log_inf(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(nic_cli_id_str + indent + msg)

    def cli_log_slot_err(self, slot, msg, level=0):
        if msg is None:
            msg = ""
        nic_cli_id_str = libmfg_utils.id_str(mtp=self._id, nic=slot)
        indent = "    " * level
        if self._filep and not self._filep.closed:
            libmfg_utils.cli_log_err(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_err(nic_cli_id_str + indent + msg)

    def cli_log_slot_wrn(self, slot, msg, level=0):
        if msg is None:
            msg = ""
        nic_cli_id_str = libmfg_utils.id_str(mtp=self._id, nic=slot)
        indent = "    " * level
        if self._filep and not self._filep.closed:
            libmfg_utils.cli_log_wrn(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_wrn(nic_cli_id_str + indent + msg)

    def cli_log_slot_inf_lock(self, slot, msg, level=0):
        self._lock.acquire()
        self.cli_log_slot_inf(slot, msg, level)
        self._lock.release()

    def cli_log_slot_err_lock(self, slot, msg, level=0):
        self._lock.acquire()
        self.cli_log_slot_err(slot, msg, level)
        self._lock.release()

    def cli_log_file(self, msg):
        self._filep.write(msg + "\n")

    def log_mtp_file(self, msg):
        self._diag_filep.write("\n[" + libmfg_utils.get_timestamp() + "] " + msg)
        # extra sendline to clean up log
        if self._mgmt_handle and self._mgmt_prompt:
            self.mtp_mgmt_exec_cmd("")

    def log_nic_file(self, slot, msg):
        self._diag_nic_filep_list[slot].write("\n[" + libmfg_utils.get_timestamp() + "] " + msg)
        # extra sendline to clean up log
        if self._nic_ctrl_list[slot] is not None:
            if self._nic_ctrl_list[slot]._nic_handle:
                self._nic_ctrl_list[slot].mtp_exec_cmd("")

    def log_slot_test_start(self, slot, testname):
        # log the timestamp in NIC log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started".format(testname)
        ts_record_cmd = "#######= {:s} =#######".format(ts_record)
        self.log_nic_file(slot, ts_record_cmd)
        return start

    def log_slot_test_stop(self, slot, testname, start):
        # log the timestamp in NIC log
        stop = libmfg_utils.timestamp_snapshot()
        duration = stop - start
        ts_record = "{:s} Stopped - duration {:s}".format(testname, str(duration))
        ts_record_cmd = "#######= {:s} =#######".format(ts_record)
        self.log_nic_file(slot, ts_record_cmd)
        return str(duration)

    def log_test_start(self, testname):
        # log the timestamp in MTP log
        start = libmfg_utils.timestamp_snapshot()
        ts_record = "{:s} Started".format(testname)
        ts_record_cmd = "#######= {:s} =#######".format(ts_record)
        self.log_mtp_file(ts_record_cmd)
        return start

    def log_test_stop(self, testname, start):
        # log the timestamp in MTP log
        stop = libmfg_utils.timestamp_snapshot()
        duration = stop - start
        ts_record = "{:s} Stopped - duration {:s}".format(testname, str(duration))
        ts_record_cmd = "#######= {:s} =#######".format(ts_record)
        self.log_mtp_file(ts_record_cmd)
        return str(duration)

    def get_mtp_health_monitor(self):
        return self._mtp_health

    def mtp_sys_info_disp(self):
        self.cli_log_inf("MTP System Info Dump:", level=0)

        if not self._mgmt_cfg[0]:
            self.cli_log_err("Unable to retrieve MTP MGMT IP")
            return False
        self.cli_log_report_inf("MTP Chassis IP: {:s}".format(self._mgmt_cfg[0]))

        if not self.get_mtp_factory_location():
            self.cli_log_err("Unable to get MTP factory location")
            return False
        self.cli_log_report_inf("MTP Location: {:s}".format(self.get_mtp_factory_location()))

        for psu in list(self._psu_sn.keys()):
            if self._psu_sn[psu]:
                self.cli_log_report_inf("MTP PSU_{:s} MFR ID: {:s}".format(psu, self._psu_sn[psu]))

        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            if not self._fpga_ver:
                self.cli_log_err("Unable to retrieve MTP FPGA Version")
                return False
            self.cli_log_report_inf("MTP FPGA Version: {:s}, datecode: {:s}, timestamp: {:s}".format(self._fpga_ver[0], self._fpga_ver[1], self._fpga_ver[2]))
        else:
            if not self._io_cpld_ver:
                self.cli_log_err("Unable to retrieve MTP IO-CPLD Version")
                return False
            self.cli_log_report_inf("MTP IO-CPLD Version: {:s}".format(self._io_cpld_ver))

            if not self._jtag_cpld_ver:
                self.cli_log_err("Unable to retrieve MTP JTAG-CPLD Version")
                return False
            self.cli_log_report_inf("MTP JTAG-CPLD Version: {:s}".format(self._jtag_cpld_ver))

        if not self._mtp_type:
            self.cli_log_err("Unable to retrieve MTP TYPE")
            return False
        self.cli_log_report_inf("MTP CPLD supports: {:s}".format(self._mtp_type))

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

        if libmfg_utils.MFG_GIT_VERSION:
            self.cli_log_report_inf("Diag Build Hashtag: {:s}".format(libmfg_utils.MFG_GIT_VERSION))

        if self._asic_hashtag:
            self.cli_log_report_inf("MTP ASIC Hashtag: {:s}".format(self._asic_hashtag))

        if self._cns_pmci_ver:
            self.cli_log_report_inf("MTP CNS-PMCI Tool version: {:s}".format(self._cns_pmci_ver))

        if libmfg_utils.MFG_PKG_VERSION:
            self.cli_log_report_inf("MFG Script Version: {:s}".format(libmfg_utils.MFG_PKG_VERSION))
        else:
            script_ver_match = re.search(r"image_amd64_.....(.){0,2}_(.*)\.tar", MFG_IMAGE_FILES.MTP_AMD64_IMAGE)
            if script_ver_match:
                self._script_ver = script_ver_match.group(2)
            self.cli_log_report_inf("MFG Script Version: {:s}".format(self._script_ver))

        self.cli_log_inf("MTP System Info Dump End\n", level=0)
        return True

    def fst_sys_info_disp(self):
        self.cli_log_inf("MTPS System Info Dump:", level=0)

        if not self._mgmt_cfg[0]:
            self.cli_log_err("Unable to retrieve MTPS MGMT IP")
            return False
        self.cli_log_report_inf("MTPS Chassis IP: {:s}".format(self._mgmt_cfg[0]))

        if not self.get_mtp_factory_location():
            self.cli_log_err("Unable to get MTP factory location")
            return False
        self.cli_log_report_inf("MTPS Location: {:s}".format(self.get_mtp_factory_location()))

        script_ver_match = re.search(r"image_amd64_....(.){0,2}_(.*)\.tar", MFG_IMAGE_FILES.MTP_AMD64_IMAGE)
        if script_ver_match:
            self._script_ver = script_ver_match.group(2)
        self.cli_log_report_inf("MFG Script Version: {:s}".format(self._script_ver))

        self.cli_log_inf("MTPS System Info Dump End\n", level=0)
        return True

    def get_mgmt_cfg(self):
        return self._mgmt_cfg

    def set_mtp_logfile(self, filep):
        self._filep = filep

    def set_mtp_diag_logfile(self, diag_filep):
        self._diag_filep = diag_filep
        self._mgmt_handle.logfile = None
        self._mgmt_handle.logfile_read = self._diag_filep
        self._mgmt_handle.logfile_send = None

    def mtp_get_cmd_buf_before_sig(self):
        return self._buf_before_sig

    def mtp_get_cmd_buf(self):
        return self._cmd_buf

    def mtp_dump_err_msg(self, err_msg):
        self.cli_log_err("==== Error Message Start: ====")
        if err_msg:
            if (len(err_msg) > 512):
                top_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[:256])
                for line in top_err_msg.splitlines():
                    if self._mgmt_prompt in line:
                        continue  # skip so it doesnt mess with pexpect
                    self.cli_log_err(line)
                self.cli_log_err("<============================>")
                bottom_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[-256:])
                for line in bottom_err_msg.splitlines():
                    if self._mgmt_prompt in line:
                        continue  # skip so it doesnt mess with pexpect
                    self.cli_log_err(line)
            else:
                err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg)
                for line in err_msg.splitlines():
                    self.cli_log_err(line)
        self.cli_log_err("==== Error Message End: ====")

    def mtp_dump_nic_err_msg(self, slot):
        err_msg = self.mtp_get_nic_cmd_buf(slot)
        if err_msg is None:
            err_msg = ""
        self.cli_log_slot_err(slot, "==== Error Message Start: ====")
        if err_msg:
            if (len(err_msg) > 512):
                top_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[:256])
                for line in top_err_msg.splitlines():
                    if self._mgmt_prompt in line:
                        continue  # skip so it doesnt mess with pexpect
                    self.cli_log_slot_err(slot, line)
                self.cli_log_slot_err(slot, "<============================>")
                bottom_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[-256:])
                for line in bottom_err_msg.splitlines():
                    if self._mgmt_prompt in line:
                        continue  # skip so it doesnt mess with pexpect
                    self.cli_log_slot_err(slot, line)
            else:
                err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg)
                for line in err_msg.splitlines():
                    if self._mgmt_prompt in line:
                        continue  # skip so it doesnt mess with pexpect
                    self.cli_log_slot_err(slot, line)
        self.cli_log_slot_err(slot, "==== Error Message End: ====")

    def set_mtp_status(self, status):
        if status < MTP_Status.MTP_STA_MAX:
            self._status = status

    def get_mtp_slot_num(self):
        return self._slots

    def get_mtp_factory_location(self):
        if self._factory_location == Factory.UNKNOWN:
            self.set_mtp_factory_location()

        return self._factory_location

    def set_mtp_factory_location(self, set_to=""):
        if set_to == "":
            self._factory_location = self._detect_factory_location()
        return self._factory_location

    def _detect_factory_location(self):
        # cmd = "ifconfig enp4s0 | grep 'inet '"
        # if not self.mtp_mgmt_exec_cmd(cmd):
        #     self.cli_log_err("Failed to execute command: {:s}".format(cmd), level = 0)
        #     return None
        # cmd_buf = self.mtp_get_cmd_buf()

        # if cmd_buf is None or cmd_buf == "":
        #     self.cli_log_err("Can't get network connection to MTP: {:s}".format(cmd), level = 0)
        #     return None

        # if "Device not found" in cmd_buf:
        #     self.cli_log_err("Unable to get MTP ethernet port details: {:s}".format(cmd), level = 0)
        #     return None
        if not self._mgmt_cfg:
            self.cli_log_err("Unable to retrieve MTP MGMT IP for factory detection")
            return Factory.UNKNOWN

        mtp_ipaddr = self._mgmt_cfg[0]

        # check which network subnet mask this IP address falls into
        for factory in list(Factory_network_config.keys()):
            if "Networks" not in list(Factory_network_config[factory].keys()):
                self.cli_log_err("Bad network config for factory {:s}".format(factory))
                return Factory.UNKNOWN
            for subnet in Factory_network_config[factory]["Networks"]:
                if ipaddress.ip_address(str(mtp_ipaddr)) in ipaddress.ip_network(str(subnet)):
                    return factory

        self.cli_log_err("MTP IP does not belong in any valid network range")
        return Factory.UNKNOWN

    def get_mtp_sn(self):
        return "" if self._mtp_sn is None else self._mtp_sn

    def set_mtp_sn(self, sn):
        self._mtp_sn = sn
        self.cli_log_inf("Set MTP SN to {:s}".format(sn), level=0)

    def get_mtp_mac(self):
        return self._mtp_mac

    def set_mtp_mac(self, mac):
        self._mtp_mac = mac
        self.cli_log_inf("Set MTP MAC to {:s}".format(mac), level=0)

    def close_file_handles(self):
        fp_list = self._open_file_handles
        for fp in fp_list:
            fp.close()

    def _apc_model_check(self, handle):
        """
        Check that the model is a Digital Logger V222.
        This model supports the uom commands we are using in the script.
        """
        retry = 0
        while True:
            handle.send("uom dump relay/model\r")
            idx = handle.expect_exact(["V222", "#", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.expect_exact("#")
                return True
            elif idx == 1:
                self.cli_log_err("This APC model not supported")
                return False
            elif idx > 1 and retry < 5:
                retry += 1
                continue
            else:
                self.cli_log_err("APC: Unable to check model")
                return False

    def _mtp_single_apc_pwr_off_ssh(self, apc, userid, passwd, port_list):
        """
        Digital Logger V222: Set persistent state: uom set "relay/outlets/2/state" false
        """
        retry = 0
        handle = pexpect.spawn("ssh " + userid + "@" + apc, encoding='utf-8', codec_errors='ignore')
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(passwd + "\r")
                break
            elif idx > 0 and retry < 5:
                retry += 1
                handle = pexpect.spawn("ssh " + userid + "@" + apc, encoding='utf-8', codec_errors='ignore')
                continue
            else:
                self.cli_log_err("Unable to ssh to APC: " + apc)
                return False

        idx = handle.expect_exact(["root@", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            if not self._apc_model_check(handle):
                handle.close()
                return False
            for port in port_list:
                handle.send("uom set relay/outlets/{:d}/state false\r".format(int(port)-1))
                idx = handle.expect_exact(["#", "not found", pexpect.TIMEOUT])
                if idx != 0:
                    self.cli_log_err("APC does not support uom command")
                    handle.close()
                    return False
            handle.close()
            time.sleep(1)
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False

    def _mtp_single_apc_pwr_on_ssh(self, apc, userid, passwd, port_list):
        """
        Digital Logger V222: Set persistent state: uom set "relay/outlets/2/state" true
        """
        retry = 0
        handle = pexpect.spawn("ssh " + userid + "@" + apc, encoding='utf-8', codec_errors='ignore')
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(passwd + "\r")
                break
            elif idx > 0 and retry < 5:
                retry += 1
                handle = pexpect.spawn("ssh " + userid + "@" + apc, encoding='utf-8', codec_errors='ignore')
                continue
            else:
                self.cli_log_err("Unable to ssh to APC: " + apc)
                return False

        idx = handle.expect_exact(["root@", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            if not self._apc_model_check(handle):
                handle.close()
                return False
            for port in port_list:
                handle.send("uom set relay/outlets/{:d}/state true\r".format(int(port)-1))
                idx = handle.expect_exact(["#", "not found", pexpect.TIMEOUT])
                if idx != 0:
                    self.cli_log_err("APC does not support uom command")
                    handle.close()
                    return False
            handle.close()
            time.sleep(1)
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False

    def _mtp_single_apc_pwr_get_state_ssh(self, apc, userid, passwd, port_list):
        """
        Digital Logger V222: Get persistent state: uom get relay/outlets/0/state
        """
        retry = 0
        handle = pexpect.spawn("ssh " + userid + "@" + apc, encoding='utf-8', codec_errors='ignore')
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["assword *:", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(passwd + "\r")
                break
            elif idx > 0 and retry < 5:
                retry += 1
                handle = pexpect.spawn("ssh " + userid + "@" + apc, encoding='utf-8', codec_errors='ignore')
                continue
            else:
                self.cli_log_err("Unable to ssh to APC: " + apc)
                return False

        idx = handle.expect_exact(["root@", pexpect.TIMEOUT], timeout=10)
        if idx == 0:
            handle.expect_exact("#")
            if not self._apc_model_check(handle):
                handle.close()
                return False
            for port in port_list:
                handle.send("uom get relay/outlets/{:d}/state\r".format(int(port)-1))
                idx = handle.expect_exact(["#", "not found", pexpect.TIMEOUT])
                if idx != 0:
                    self.cli_log_err("APC does not support uom command")
                    handle.close()
                    return False
            handle.close()
            time.sleep(1)
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False

    def _mtp_single_apc_pwr_off(self, apc, userid, passwd, port_list):
        retry = 0
        handle = pexpect.spawn("telnet " + apc, encoding='utf-8', codec_errors='ignore')
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["ame *:", "assword *:", "Connection refused", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
            elif idx == 2:
                # no telnet, try as ssh
                handle.close()
                return self._mtp_single_apc_pwr_off_ssh(apc, userid, passwd, port_list)
            elif idx > 2 and retry < 5:
                retry += 1
                handle = pexpect.spawn("telnet " + apc, encoding='utf-8', codec_errors='ignore')
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
                handle.send("olOff " + str(port) + "\r")
                handle.expect_exact(">")
            handle.close()
            time.sleep(1)
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False

    def _mtp_single_apc_pwr_on(self, apc, userid, passwd, port_list):
        retry = 0
        handle = pexpect.spawn("telnet " + apc, encoding='utf-8', codec_errors='ignore')
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["ame *:", "assword *:", "Connection refused", pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
            elif idx == 2:
                # no telnet, try as ssh
                handle.close()
                return self._mtp_single_apc_pwr_on_ssh(apc, userid, passwd, port_list)
            elif idx > 2 and retry < 5:
                retry += 1
                handle = pexpect.spawn("telnet " + apc, encoding='utf-8', codec_errors='ignore')
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
                handle.send("olOn " + str(port) + "\r")
                handle.expect_exact(">")
            handle.close()
            return True
        else:
            self.cli_log_err("Unknown APC: " + apc)
            return False

    def _mtp_single_apc_pwr_cycle(self, apc, userid, passwd, port_list):
        handle = pexpect.spawn("telnet " + apc, encoding='utf-8', codec_errors='ignore')
        if self._debug_mode:
            handle.logfile_read = sys.stdout
        while True:
            idx = handle.expect(["ame *:", "assword *:", "Connection refused", pexpect.TIMEOUT])
            if idx == 0:
                handle.send(userid + "\r")
                continue
            elif idx == 1:
                handle.send(passwd + "\r")
                break
            elif idx == 2:
                # no telnet, try as ssh
                handle.close()
                if not self._mtp_single_apc_pwr_off_ssh(apc, userid, passwd, port_list):
                    return False
                time.sleep(1)
                if not self._mtp_single_apc_pwr_on_ssh(apc, userid, passwd, port_list):
                    return False
                return True
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
                handle.send("olOff " + str(port) + "\r")
                handle.expect_exact(">")
            time.sleep(1)
            for port in port_list:
                handle.send("olOn " + str(port) + "\r")
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

        """
        create a ssh session to MTP or MTP local bash session base on env vaiable CARD_TYPE
        """

        # using enviroment variable CARD_TYPE as a indicator to create a remote ssh session or a local bash session
        running_on_mtp = True if os.getenv('CARD_TYPE') and 'MTP' in os.getenv('CARD_TYPE') else False

        # mgmt_cfg is a list with format [ip, userid, passwd]
        ip = self._mgmt_cfg[0]
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        # SSH session to MTP
        if not running_on_mtp:
            ssh_cmd = libmfg_utils.get_ssh_connect_cmd(userid, ip)
            handle = pexpect.spawn(ssh_cmd, encoding='utf-8', codec_errors='ignore')
            idx = libmfg_utils.mfg_expect(handle, ["assword:"])
            if idx < 0:
                self.cli_log_err("Can not connect to mtp, check the console.\n", level=0)
                return None
            else:
                handle.sendline(passwd)

            idx = libmfg_utils.mfg_expect(handle, self._prompt_list)
            if idx < 0:
                self.cli_log_err("Connect to mtp mgmt timeout", level=0)
                return None
        # MTP local bash session
        else:
            mtp_local_cmd = 'bash'
            handle = pexpect.spawn(mtp_local_cmd, encoding='utf-8', codec_errors='ignore')
            idx = libmfg_utils.mfg_expect(handle, self._prompt_list)
            if idx < 0:
                self.cli_log_err("spawn new bash session timeout", level=0)
                return None

            mtp_local_cmd = 'source /home/diag/.bash_profile'
            handle.sendline(mtp_local_cmd)
            idx = libmfg_utils.mfg_expect(handle, self._prompt_list, 10)
            if idx < 0:
                self.cli_log_err("source bash profile on new created bash session timeout", level=0)
                return None

        sig_list = [userid]

        cmd = MFG_DIAG_CMDS().MTP_LOGIN_VERIFY_FMT
        handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(handle, sig_list, 5)
        if idx < 0:
            self.cli_log_err("Unable to locate diag user", level=0)
            return None

        idx = libmfg_utils.mfg_expect(handle, self._prompt_list, 5)
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt failed", level=0)
            return None
        else:
            return handle

    def mtp_nic_para_session_init(self, slot_list=[], fpo=True):
        if self._fst_ver is not None:
            mtp_prompt = "#"
        else:
            mtp_prompt = "$"
        if slot_list == []:
            slot_list = list(range(self._slots))
        userid = self._mgmt_cfg[1]
        # number of CPUs the current process can use
        current_process_cores = len(os.sched_getaffinity(0))
        # Toggle comment or uncomment this snippet with above depends on the need of David's Matera UART new driver implement
        # #####-->
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            # using enviroment variable CARD_TYPE as a indicator to create a remote ssh session or a local bash session
            running_on_mtp = True if os.getenv('CARD_TYPE') and 'MTP' in os.getenv('CARD_TYPE') else False
            if running_on_mtp:
                # assign task sshd to cpu core 0
                pid_cmd = """ppid=$(ps -o ppid= -p $$) && ps -elf | grep " $ppid " | grep sshd | awk '{print $4}' | cat """
                if not self.mtp_mgmt_exec_cmd(pid_cmd):
                    self.cli_log_err("Executing command {:s} failed".format(pid_cmd))
                    return False
                sshd_pid_match = re.findall(r'(\d+)', self.mtp_get_cmd_buf())
                if not sshd_pid_match:
                    self.cli_log_err("Failed to Get sshd pid")
                    return False
                sshd_pid = sshd_pid_match[0]
                if not self.mtp_mgmt_exec_cmd(pid_cmd):
                    self.cli_log_err("Executing command {:s} failed".format(pid_cmd))
                    return False
                pid_cmd = 'ps -o pid,psr,comm -p {:s}'.format(sshd_pid)
                if not self.mtp_mgmt_exec_cmd(pid_cmd):
                    self.cli_log_err("Executing command {:s} failed".format(pid_cmd))
                    return False
        # <--#####

        for index, slot in enumerate(slot_list):
            cpu_core_index = index % (current_process_cores - 1) + 1
            handle = self.mtp_session_create()
            if handle:
                if not self.mtp_prompt_cfg(handle, userid, mtp_prompt, slot):
                    self.cli_log_err("Unable to config MTP session")
                    return False
                prompt = "{:s}@NIC-{:02d}:".format(userid, slot+1) + mtp_prompt
                if fpo:
                    self._nic_ctrl_list[slot] = nic_ctrl(slot, self._diag_nic_filep_list[slot])
                    self._propogate_properties_to_nic(slot)
                self._nic_ctrl_list[slot].nic_handle_init(handle, prompt)
                para_cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
                if not self.mtp_mgmt_exec_cmd_para(slot, para_cmd):
                    self.cli_log_slot_err(slot, "Failed to execute para command: {:s}".format(para_cmd))
                    return False
                # Toggle comment or uncomment this snippet with above depends on the need of David's Matera UART new driver implement
                # #####-->
                # if running_on_mtp:
                #     # assign task bash to any cpu core except core 0
                #     para_cmd = 'echo $$'
                #     if not self.mtp_mgmt_exec_cmd_para(slot, para_cmd):
                #         self.cli_log_slot_err(slot, "Failed to execute para command: {:s}".format(para_cmd))
                #         return False
                #     bash_pid = re.findall(r'\d+', self.mtp_get_nic_cmd_buf(slot).split('\n')[1])[0]
                #     para_cmd = 'taskset -pc {:d} {:s}'.format(cpu_core_index, bash_pid)
                #     if not self.mtp_mgmt_exec_cmd_para(slot, para_cmd):
                #         self.cli_log_slot_err(slot, "Failed to execute para command: {:s}".format(para_cmd))
                #         return False
                #     para_cmd = 'ps -o pid,psr,comm -p {:s}'.format(bash_pid)
                #     if not self.mtp_mgmt_exec_cmd_para(slot, para_cmd):
                #         self.cli_log_slot_err(slot, "Failed to execute para command: {:s}".format(para_cmd))
                #         return False
                #     para_cmd = 'echo $$'
                #     if not self.mtp_mgmt_exec_cmd_para(slot, para_cmd):
                #         self.cli_log_slot_err(slot, "Failed to execute para command: {:s}".format(para_cmd))
                #         return False
                # <--#####
            else:
                self.cli_log_err("Unable to create MTP session")
                return False
        return True

    def mtp_nic_para_session_end(self, slot_list=[]):
        self.cli_log_inf("Close NIC Connections", level=0)
        if slot_list == []:
            slot_list = list(range(self._slots))
        for slot in slot_list:
            self._nic_ctrl_list[slot].nic_handle_close()
        return True

    def mtp_mgmt_connect(self, prompt_cfg=False, prompt_id=None, retry_with_powercycle=False, max_retry=3):
        delay = 200  # make sure this delay covers FST boot
        # retries = self._mgmt_timeout / delay
        # retries = retries + 4
        retries = max_retry
        if not self._mgmt_cfg:
            self.cli_log_err("management port config is empty")
            return None

        self.mtp_mgmt_disconnect()

        # mgmt_cfg is a list with format [ip, userid, passwd]
        ip = self._mgmt_cfg[0]
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        ssh_cmd = libmfg_utils.get_ssh_connect_cmd(userid, ip)
        self._mgmt_handle = pexpect.spawn(ssh_cmd, encoding='utf-8', codec_errors='ignore', logfile=self._diag_filep)
        while True:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, ["assword:"])
            if idx < 0:
                if retries > 0:
                    if retry_with_powercycle:
                        self.cli_log_err("Connect to mtp timeout. Powercycle and retry...{:d} attempts remaining...".format(retries))
                        libmfg_utils.mtpid_list_poweroff([self], safely=False)
                        libmfg_utils.mtpid_list_poweron([self])
                    else:
                        self.cli_log_inf("Connect to mtp timeout, wait {:d}s and retry...".format(delay), level=0)
                        time.sleep(delay)
                    retries -= 1
                    self._mgmt_handle = pexpect.spawn(ssh_cmd, encoding='utf-8', codec_errors='ignore', logfile=self._diag_filep)
                    continue
                else:
                    self.cli_log_err("Connect to mtp failed\n", level=0)
                    return None
            else:
                self._mgmt_handle.sendline(passwd)
                break

        idx = libmfg_utils.mfg_expect(self._mgmt_handle, self._prompt_list)
        if idx < 0:
            self.cli_log_err(self._mgmt_handle.before)
            self.cli_log_err("Connect to mtp failed", level=0)
            return None

        self._mgmt_prompt = self._prompt_list[idx]

        cmd = MFG_DIAG_CMDS().MTP_LOGIN_VERIFY_FMT
        sig_list = [userid]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
            self.cli_log_err("Connect to mtp mgmt failed", level=0)
            return None

        # set logfile
        # self._mgmt_handle.logfile_read = self._diag_filep
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
            self._mgmt_prompt = "{:s}@MTP:".format(userid) + self._mgmt_prompt

        return self._mgmt_prompt

    def mtp_prompt_cfg(self, handle, userid, prompt, slot=None):
        handle.sendline("stty rows 50 cols 160")
        idx = libmfg_utils.mfg_expect(handle, [prompt])
        if idx < 0:
            self.cli_log_err("Connect to mtp mgmt timeout", level=0)
            return False

        if slot != None:
            prompt_str = "{:s}@NIC-{:02d}:{:s} ".format(userid, slot+1, prompt)
        else:
            prompt_str = "{:s}@MTP:{:s} ".format(userid, prompt)
        handle.sendline(r"PS1='[\D{%Y-%m-%d_%H:%M:%S}] " + prompt_str + "'")

        # refresh
        handle.sendline("uname")
        idx = libmfg_utils.mfg_expect(handle, ["Linux"])
        if idx < 0:
            self.cli_log_err("Refresh mtp mgmt timeout", level=0)
            return False
        idx = libmfg_utils.mfg_expect(handle, [prompt_str])
        if idx < 0:
            self.cli_log_err("Refresh mtp mgmt timeout", level=0)
            return False

        return True

    def mtp_enter_user_ctrl(self):
        if self._mgmt_handle and self._debug_mode:
            self._mgmt_handle.interact()

    def mtp_mgmt_exec_sudo_cmd(self, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]

        if not self._mgmt_handle:
            self.cli_log_err("Management port is not connected")
            return False

        self._mgmt_handle.sendline("sudo -k " + cmd)
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [userid + ":", self._mgmt_prompt])
        if idx < 0:
            self._mgmt_handle.logfile_read = None
            self._mgmt_handle.logfile_send = None
            self.mtp_mgmt_disconnect()
            if cmd != "reboot" and  cmd != "poweroff":
                return False

        if idx == 0:
            self._mgmt_handle.sendline(passwd)
            if cmd == "reboot" or cmd == "poweroff":
                self._mgmt_handle.expect_exact(pexpect.EOF)
                self._mgmt_handle.logfile_read = None
                self._mgmt_handle.logfile_send = None
                self.mtp_mgmt_disconnect()
            else:
                idx = libmfg_utils.mfg_expect(self._mgmt_handle, [self._mgmt_prompt], timeout=timeout)
                if idx < 0:
                    self.cli_log_err("Connect to mtp mgmt timeout", level=0)
                    return False

        return True

    def mtp_mgmt_exec_sudo_cmd_resp(self, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        userid = self._mgmt_cfg[1]
        passwd = self._mgmt_cfg[2]
        rs = ""

        if not self._mgmt_handle:
            self.cli_log_err("Management port is not connected")
            return "[FAIL]: Management port is not connected"

        self._mgmt_handle.sendline("sudo -k " + cmd)
        idx = libmfg_utils.mfg_expect(self._mgmt_handle, [userid + ":", self._mgmt_prompt], timeout=timeout)
        if idx < 0:
            rs = self._mgmt_handle.before
            self._mgmt_handle.logfile_read = None
            self._mgmt_handle.logfile_send = None
            self.mtp_mgmt_disconnect()
            return rs
        elif idx == 0:
            self._mgmt_handle.sendline(passwd)
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, [self._mgmt_prompt], timeout=timeout)
            if idx < 0:
                self.cli_log_err("Connect to mtp mgmt timeout", level=0)
                return "[FAIL]: Connect to mtp mgmt timeout"
            else:
                rs = self._mgmt_handle.before
        elif idx == 1:
            # for FST server, since diag user already belong to root group, so it will not prompt for password
            rs = self._mgmt_handle.before
        return rs

    def mtp_get_mac(self):
        # MTP MAC info
        rs = ""
        cmd = MFG_DIAG_CMDS().MTP_MAC_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute cmd to get MTP MAC info", level=0)
            return "[FAIL]: Failed to execute cmd to get MTP MAC info"
        match = re.findall(r"(([0-9a-f]{2}[:]){5}([0-9a-f]{2}))", self.mtp_get_cmd_buf())
        if match:
            return match[0][0]
        else:
            self.cli_log_err("Failed to locate MTP MAC info." + self.mtp_get_cmd_buf(), level=0)
            return "[FAIL]: Failed to locate MTP MAC info"

    def mtp_get_memory_size(self):
        """
        return mtp memory size in KB to differntiate if it is 4G Tubor MTP or 8G Turbo MTP;
        Since for run_l1 test, 4G memory can run 5 NIC card in parallel while 8G memory can run all 10 NIC in parallel
        """
        memorysize = ""
        cmd = "cat /proc/meminfo"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute cmd to get MTP Memory info", level=0)
            return memorysize
        match = re.findall(r"MemTotal:\s+(\d+)\s+kB", self.mtp_get_cmd_buf())
        if match:
            memorysize = match[0]
            self.cli_log_inf("MTP Total Memory is {:.2f} GB".format(int(memorysize) / 1024.0 / 1024.0), level=0)
        else:
            self.cli_log_err("Failed to locate MTP MAC info." + self.mtp_get_cmd_buf(), level=0)
        return memorysize

    def mtp_set_sn_rev_mac_command(self, sn, maj, mac):
        cmd = MFG_DIAG_CMDS().MTP_FRU_PROG_SN_MAJ_MAC_FMT.format(sn, maj, mac)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Unable to set MTP SN, REV and MAC")
            return False
        match = re.findall(r"Programming", self.mtp_get_cmd_buf())
        if match:
            cmd = "eeutil -disp"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Unable to display MTP SN, REV and MAC info")
                return False

            match = re.findall(r"SERIAL_NUM\s+([A-Z0-9]+)", self.mtp_get_cmd_buf())
            if match:
                prog_sn = match[0].strip()
                if prog_sn != sn:
                    self.cli_log_err("Failed to set MTP SN info; got {:s} expected {:s}".format(prog_sn, sn), level=0)
                    return False
            else:
                self.cli_log_err("Failed to locate MTP SN info", level=0)
                return False

            match = re.findall(r"HW_MAJOR_REV\s+([0-9]+)", self.mtp_get_cmd_buf())
            if match:
                prog_maj = match[0].strip()
                if prog_maj != maj:
                    self.cli_log_err("Failed to set MTP REV info; got {:s} expected {:s}".format(prog_maj, maj), level=0)
                    return False
            else:
                self.cli_log_err("Failed to locate MTP REV info", level=0)
                return False

            match = re.findall(r"MAC_ADDR\s+([A-F0-9]+)", self.mtp_get_cmd_buf())
            if match:
                prog_mac = match[0].strip()
                if prog_mac != mac:
                    self.cli_log_err("Failed to set MTP MAC info; got {:s} expected {:s}".format(prog_mac, mac), level=0)
                    return False
            else:
                self.cli_log_err("Failed to locate MTP MAC info", level=0)
                return False

            return True
        else:
            self.cli_log_err("Failed to set MTP SN, REV and MAC info", level=0)
            return False
        return True

    def mtp_nic_send_ctrl_c(self, slot):
        if self._nic_ctrl_list[slot] == None:
            # script not running anything.
            return True
        if not self._nic_ctrl_list[slot].nic_send_ctrl_c():
            self.mtp_dump_nic_err_msg(slot)
            self.cli_log_slot_err(slot, "Couldn't send C+C")
            return False
        return True

    def mtp_nic_stop_test(self, slot):
        cmd_buf = self._nic_ctrl_list[slot]._cmd_buf  # save failure buffer
        self.mtp_nic_send_ctrl_c(slot)
        self.mtp_nic_stop_tclsh(slot)
        self._nic_ctrl_list[slot]._cmd_buf = cmd_buf  # restore failure buffer

    def mtp_mgmt_set_date(self, stage=None):
        timestamp_str = str(libmfg_utils.timestamp_snapshot())
        cmd = MFG_DIAG_CMDS().NIC_DATE_SET_FMT.format(timestamp_str)
        cmd1 = MFG_DIAG_CMDS().MTP_HWCLOCK_WRITE_FMT
        if stage == FF_Stage.FF_FST:
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Unable to set MTP date")
                return False
        if stage == FF_Stage.FF_FST:
            if not self.mtp_mgmt_exec_cmd(cmd1):
                self.cli_log_err("Unable to write hwclock")
                return False
            return True
        # else:
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_err("Unable to set MTP date")
            return False
        if not self.mtp_mgmt_exec_sudo_cmd(cmd1):
            self.cli_log_err("Unable to write hwclock")
            return False

        return True

    def mtp_mgmt_set_time_zone(self, stage=None):
        cmd = "timedatectl set-timezone America/Los_Angeles"
        if stage != FF_Stage.FF_FST:
            if not self.mtp_mgmt_exec_sudo_cmd(cmd):
                self.cli_log_err("Unable to set MTP timezone")
                return False

        return True

    def mtp_sys_info_init(self):

        # MTP_TYPE
        cmd = MFG_DIAG_CMDS().MTP_TYPE_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to send command for getting MTP type", level = 0)
            return False
        match = re.findall(r"MTP_TYPE=MTP_([a-zA-Z_]+)", self.mtp_get_cmd_buf())
        if match:
            self._mtp_type = match[0].strip().upper()
        else:
            self.cli_log_err("Failed to get MTP type", level = 0)
            return False

        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            # MTP FPGA version
            reg_addr = '0x00'
            cmd = MFG_DIAG_CMDS().MTP_FPGA_UTIL_READ32_FMT.format(reg_addr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("FPGA Command Failed to get MTP FPGA version info", level=0)
                return False
            match = re.findall(r"RD \[0x0000\] = 0x(\w+)", self.mtp_get_cmd_buf())
            if match:
                version = match[0][-4:]
                if not version.upper().startswith("A"):
                    self.cli_log_wrn("FPGA version {:s} of {:s} MTP NOT support Salina NIC cards".format(version, str(self._mtp_type)))
            else:
                self.cli_log_err("Failed to parse get MTP FPGA version info", level=0)
                return False
            # MTP FPGA datecode
            reg_addr = '0x04'
            cmd = MFG_DIAG_CMDS().MTP_FPGA_UTIL_READ32_FMT.format(reg_addr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("FPGA Command Failed to get MTP FPGA datecode info", level=0)
                return False
            match = re.findall(r"RD \[0x0004\] = 0x(\w+)", self.mtp_get_cmd_buf())
            if match:
                datecode = match[0]
            else:
                self.cli_log_err("Failed to parse get MTP FPGA datecode info", level=0)
                return False
            # MTP FPGA timestamp
            reg_addr = '0x08'
            cmd = MFG_DIAG_CMDS().MTP_FPGA_UTIL_READ32_FMT.format(reg_addr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("FPGA Command Failed to get MTP FPGA timestamp info", level=0)
                return False
            match = re.findall(r"RD \[0x0008\] = 0x(\w+)", self.mtp_get_cmd_buf())
            if match:
                timestamp = match[0][-6:]
            else:
                self.cli_log_err("Failed to parse get MTP FPGA timestamp info", level=0)
                return False
            self._fpga_ver = (version, datecode, timestamp)
        else:
            # MTP IO cpld version
            reg_addr = 0x0
            cmd = MFG_DIAG_CMDS().MTP_CPLD_READ_FMT.format(reg_addr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to get MTP IO-CPLD image version info", level=0)
                return False
            match = re.findall(r"addr 0x{:x} with data (0x[0-9a-fA-F]+)".format(reg_addr), self.mtp_get_cmd_buf())
            if match:
                self._io_cpld_ver = match[0]
            else:
                self.cli_log_err("Failed to get MTP IO-CPLD image version info", level=0)
                return False

            # MTP JTAG cpld version
            reg_addr = 0x19
            cmd = MFG_DIAG_CMDS().MTP_CPLD_READ_FMT.format(reg_addr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to get MTP JTAG-CPLD image version info", level=0)
                return False
            match = re.findall(r"addr 0x{:x} with data (0x[0-9a-fA-F]+)".format(reg_addr), self.mtp_get_cmd_buf())
            if match:
                self._jtag_cpld_ver = match[0]
            else:
                self.cli_log_err("Failed to get MTP JTAG-CPLD image version info", level=0)
                return False

        # MTP_REV
        cmd = MFG_DIAG_CMDS().MTP_REV_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to send command for getting MTP revision", level=0)
            return False
        match = re.findall(r"MTP_REV=REV_([0-9]{2}|NONE)", self.mtp_get_cmd_buf())
        if match:
            self._mtp_rev = match[0]
        else:
            self.cli_log_err("Failed to get MTP revision", level=0)
            return False

        # MTP OS version
        cmd = MFG_DIAG_CMDS().MTP_IMG_VER_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get os image version", level=0)
            return False
        match = re.findall(r"SMP (.* 20\d{2})", self.mtp_get_cmd_buf())
        if match:
            self._os_ver = match[0]
        else:
            self.cli_log_err("Failed to get os image version", level=0)
            return False

        # MTP Diag image version
        if not self.mtp_init_diag_img_version():
            return False

        # MTP ASIC image version
        if not self.mtp_init_diag_asiclib_version():
            return False

        return True

    def mtp_init_diag_img_version(self):
        cmd = MFG_DIAG_CMDS().MTP_DIAG_VERSION_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to get diag image version", level=0)
            return False
        self._diag_ver = libmfg_utils.rgx_extract_commit_date(self.mtp_get_cmd_buf())
        if not self._diag_ver:
            self.cli_log_err("Failed to find diag image version", level=0)
            return False
        return True

    def mtp_init_diag_asiclib_version(self):
        cmd = MFG_DIAG_CMDS().MTP_ASIC_VERSION_FMT
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=120):
            self.cli_log_err("Failed to get asic util version", level=0)
            return False
        self._asic_ver = libmfg_utils.rgx_extract_commit_date(self.mtp_get_cmd_buf())
        if not self._asic_ver:
            self.cli_log_err("Failed to find asic util version", level=0)
            return False
        self._asic_hashtag = libmfg_utils.rgx_extract_commit_hashtag(self.mtp_get_cmd_buf())
        if not self._asic_hashtag:
            self.cli_log_err("Failed to find asic lib hashtag", level=0)
            return False
        return True

    def mtp_get_mtp_type(self):
        return self._mtp_type

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
                # See if we can read the MTP Adapter CPLD ID.  This would indicate an ALOM should be present
                # Skip mtp_adapt_cpld read on Panarea MTP
                if self.mtp_get_mtp_type() != MTP_TYPE.PANAREA:
                    rc = self._nic_ctrl_list[slot].nic_read_mtp_adapt_cpld(0x80, read_data)
                if read_data[0] == 0x1b:
                    self.cli_log_slot_inf(slot, "NAPLES25SWM ALOM DETECTED")
                    self._swmtestmode[slot] = Swm_Test_Mode.SWMALOM
                else:
                    self._swmtestmode[slot] = Swm_Test_Mode.SWM
        return True

    def mtp_set_nic_status_fail(self, slot, skip_fa=False, testname="", stage=""):
        if self._nic_ctrl_list:
            # was previously OK, this is first failure
            if self.mtp_check_nic_status(slot) and not skip_fa:
                libmfg_utils.post_fail_steps(self, slot, testname, stage)

            # failed inside libnic_ctrl, didnt trigger post_fail_steps
            elif self.mtp_check_nic_missed_fa(slot) and not skip_fa:
                libmfg_utils.post_fail_steps(self, slot, testname, stage)
            self._nic_ctrl_list[slot].nic_set_status(NIC_Status.NIC_STA_DIAG_FAIL)

    def mtp_clear_nic_status(self, slot):
        if self._nic_ctrl_list:
            self._nic_ctrl_list[slot].nic_set_status(NIC_Status.NIC_STA_OK)

    def mtp_stale_image_cleanup(self):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        cmd = "rm -f naples* image_a*"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        return True

    def mtp_update_mtp_diag_image(self, image):
        cmd = "rm -rf {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_MTP_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        cmd = "tar zxf {:s}".format(image)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        return True

    def mtp_update_python36_site_package(self, image):

        cmd = "mkdir -p /home/diag/.local/lib"
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)

            return False

        cmd = "tar zxf {:s} -C /home/diag/.local/lib".format(image)
        self.cli_log_inf(cmd, level=0)
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        return True

    def mtp_update_cns_pmci_package(self, image):
        # Remove the old tool
        cmd = "rm -rf /home/diag/cns-pmci"
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        # Extract the new tool package
        cmd = "tar zxf {:s} -C /home/diag/".format(image)
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        # Get tool directory by removing suffix '.tar.gz'
        tool_dir = image[:-7]

        # Rename tool directory to common name 'cns-pmci'
        cmd = "mv {:s} /home/diag/cns-pmci".format(tool_dir)
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        # Do a sync to make sure all write done.
        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        return True

    def mtp_update_nic_diag_image(self, image):
        cmd = "rm -rf {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        cmd = "tar zxf {:s} -C {:s}".format(image, MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        cmd = "sync"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
            return False

        return True

    def mtp_mgmt_poweroff(self):
        if not self.mtp_mgmt_exec_cmd("sync", timeout=MTP_Const.OS_SYNC_DELAY):
            self.cli_log_err("Failed to execute sync command")
            return False

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

    def mtp_chassis_shutdown(self):
        self.mtp_mgmt_poweroff()
        self.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        self.mtp_apc_pwr_off()
        self.cli_log_inf("Power off APC, Wait {:d} seconds for APC shutdown".format(MTP_Const.MTP_POWER_CYCLE_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)

    def mtp_power_cycle(self):
        self.mtp_mgmt_poweroff()
        self.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
        self.cli_log_inf("Power off APC", level=0)
        self.mtp_apc_pwr_off()
        libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
        self.mtp_apc_pwr_on()
        self.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.MTP_POWER_ON_DELAY)
        return True

    def mtp_mgmt_exec_cmd(self, cmd, sig_list=[], timeout=MTP_Const.OS_CMD_DELAY):
        rc = True
        self._mgmt_handle.sendline(cmd)
        cmd_before = ""
        self._buf_before_sig = ""
        for sig in sig_list:
            idx = libmfg_utils.mfg_expect(self._mgmt_handle, [sig], timeout)
            self._buf_before_sig += self._mgmt_handle.before
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
            self._cmd_buf = self._buf_before_sig + self._mgmt_handle.before
            return True

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
        cmd = MFG_DIAG_CMDS().MTP_VRM_TEST_FMT
        pass_sig_list = [MFG_DIAG_SIG.MTP_VRM_OK_SIG]
        rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list, timeout=MTP_Const.MTP_OS_CMD_DELAY)
        if rc:
            self.cli_log_inf("VRM test passed")
        else:
            self.cli_log_err("VRM test failed")

        return rc

    def mtp_psu_init(self):
        rc = True
        # store serial number
        for psu in range(self._psu_num):
            psu = str(psu+1)
            cmd = MFG_DIAG_CMDS().MTP_PSU_DISP_FMT.format(psu) if self._mtp_type not in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA) else MFG_DIAG_CMDS().MTP_MATERA_PSU_DISP_FMT.format(psu)
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
                self.cli_log_err("Executing command {:s} failed".format(cmd))
                rc = False
                continue
            psu_sn_pattern = r"MFR_SERIAL: *(.*)"  if self._mtp_type not in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA) else r'PSU_' + psu + r'.*S\/N:\s+(\w+)'
            psu_sn_match = re.search(psu_sn_pattern, self.mtp_get_cmd_buf())
            if not psu_sn_match:
                self.cli_log_err("Failed to read PSU_{:s} Serial Number".format(psu))
                if not MFG_BYPASS_PSU_CHECK and self._mtp_type not in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
                    rc = False
                continue
            self._psu_sn[psu] = psu_sn_match.group(1).strip()

        # PSU check
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA) :
            if not MFG_BYPASS_PSU_CHECK:
                # get and parse psu status data
                cmd = MFG_DIAG_CMDS().MTP_MATERA_DEVMGR_STATUS_FMT
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("MTP command {:s} failed".format(cmd))
                    return False
                devmgr_status_output = self.mtp_get_cmd_buf().splitlines()
                psu1_data = []
                psu2_data = []
                for line_num, line in enumerate(devmgr_status_output):
                    if 'PSU_1' in line:
                        previous_line = devmgr_status_output[line_num-1]
                        self.cli_log_inf(previous_line)
                        self.cli_log_inf(line)
                        psu_lines = [i for i in zip([item.strip() for item in previous_line[36:].split()], [j.strip() for j in line[36:].split()])]
                        if "ERROR" not in line:
                            for i in psu_lines:
                                if i not in psu1_data:
                                    psu1_data.append(i)
                    if 'PSU_2' in line:
                        previous_line = devmgr_status_output[line_num-1]
                        self.cli_log_inf(previous_line)
                        self.cli_log_inf(line)
                        psu_lines = [i for i in zip([item.strip() for item in previous_line[36:].split()], [j.strip() for j in line[36:].split()])]
                        if "ERROR" not in line:
                            for i in psu_lines:
                                if i not in psu2_data:
                                    psu2_data.append(i)
                psu_data = [i for i in [psu1_data, psu2_data] if i]

                # check PSU related items
                if len(psu_data) != 2:
                    self.cli_log_err("PSU count check failed")
                    return False
                for psu_d in psu_data:
                    for i, v in psu_d[1:]:
                        if i == 'VOUT' and abs(float(v) - 12) > 5:
                            self.cli_log_err("{:s} {:s} check failed, exceed 5V difference".format(psu_d[0][1], i))
                            return False
                        if re.match(r'TEMP\d', i) and float(v) > 80:
                            self.cli_log_err("{:s} {:s} check failed, over 80C".format(psu_d[0][1], i))
                            return False
                        if 'FAN-RPM' in i and float(v) < 6000:
                            self.cli_log_err("{:s} {:s} check failed, below 6000".format(psu_d[0][1], i))
                            return False
                        if 'STS' in i and int(v, base=16) != 0:
                            if i == 'STS_WORD' or i == 'STS_TEMP':
                                self.cli_log_inf("{:s} {:s} check ignore, value {:s}".format(psu_d[0][1], i, v))
                                continue
                            self.cli_log_err("{:s} {:s} check failed, not zero".format(psu_d[0][1], i))
                            return False
        else:
            cmd = MFG_DIAG_CMDS().MTP_PSU_TEST_FMT
            pass_sig_list = []

            # apc_cfg is a list with format [apc1, apc1_port, apc1_userid, apc1_passwd, apc2, apc2_port, apc2_userid, apc2_passwd]
            if not MFG_BYPASS_PSU_CHECK and self._mtp_rev is not None and self._mtp_rev != "NONE" and len(self._mtp_rev) > 0:
                if int(self._mtp_rev) > 3:
                    apc1 = self._apc_cfg[0]
                    apc2 = self._apc_cfg[4]
                    if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
                        self.cli_log_err("Failed to get MTP PSU info", level=0)
                        return False

                    if apc1 != "":
                        match = re.search(MFG_DIAG_SIG.MTP_PSU1_OK_SIG, self.mtp_get_cmd_buf())
                        if match:
                            match_psu = re.search(r"PSU_1\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+", self.mtp_get_cmd_buf())
                            if match_psu:
                                pout = match_psu.group(1)
                                pin = match_psu.group(4)
                                if "-" in pin or "-" in pout:
                                    self.cli_log_err("PSU1 test failed (pout:{:s}, pin:{:s})".format(pout, pin))
                                    rc = False
                            else:
                                self.cli_log_err("PSU1 test failed.")
                                rc = False
                        else:
                            self.cli_log_err("PSU1 result test failed.")
                            rc = False

                    if apc2 != "":
                        match = re.search(MFG_DIAG_SIG.MTP_PSU2_OK_SIG, self.mtp_get_cmd_buf())
                        if match:
                            match_psu = re.search(r"PSU_2\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+([\d|\.|\-]+)\s+", self.mtp_get_cmd_buf())
                            if match_psu:
                                pout = match_psu.group(1)
                                pin = match_psu.group(4)
                                if "-" in pin or "-" in pout:
                                    self.cli_log_err("PSU2 test failed (pout:{:s}, pin:{:s})".format(pout, pin))
                                    rc = False
                            else:
                                self.cli_log_err("PSU2 test failed")
                                rc = False
                        else:
                            self.cli_log_err("PSU2 result test failed.")
                            rc = False
                    if rc:
                        self.cli_log_inf("PSU test passed")

        return rc

    def matera_penarea_mtp_psu_fw_chk_test(self):
        """
            if PSU Firmware is not the follwoing version, we need remind MFG to update PSU firmware, otherwise it's easy to trigger 4C error
            this is the updated version from Delta, which lift warning/fail trigger threshold
            and the utility to update PSU firmware only works on Matera MTP now, MFG need update PSU
            [2026-01-20_19:02:18] diag@MTP:$ fpgautil show psu
            PSU_1: DELTA DPS-2100BB K    H/W Rev: S0F     S/N: LFCD2545000521
            PSU_1: FW Rev:  Primary:01  Secondary:f9  Major:00  Downgrade:00
            PSU_2: DELTA DPS-2100BB K    H/W Rev: S0F     S/N: LFCD2545000585
            PSU_2: FW Rev:  Primary:01  Secondary:f9  Major:00  Downgrade:00
            [2026-01-20_19:02:33] diag@MTP:$
        """

        rc = True
        # PSU check
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA) :
            if not MFG_BYPASS_PSU_CHECK:
                # get and parse psu status data
                cmd = MFG_DIAG_CMDS().MTP_MATERA_SHOW_PSU_FMT
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("MTP command {:s} failed".format(cmd))
                    return False
                fw_check_pass = True
                if "PSU_1: FW Rev:  Primary:01  Secondary:f9  Major:00  Downgrade:00" not in  self.mtp_get_cmd_buf():
                    self.cli_log_err("PSU_1 FW is NOT match to 'Primary:01 Secondary:f9'")
                    fw_check_pass = False
                if "PSU_2: FW Rev:  Primary:01  Secondary:f9  Major:00  Downgrade:00" not in  self.mtp_get_cmd_buf():
                    self.cli_log_err("PSU_2 FW is NOT match to 'Primary:01 Secondary:f9'")
                    fw_check_pass = False
                if not fw_check_pass:
                    self.cli_log_err("PSU FW Version Check Failed")
                return fw_check_pass
            self.cli_log_inf("SKIP PSU FW Check, since MFG_BYPASS_PSU_CHECK set to True")
        else:
            self.cli_log_inf("No PSU FW check for legacy MTPs")

        return rc

    def mtp_fan_init(self, fan_pwm):

        def parse_fpga_show_fan(data):
            '''
            parse matera mtp fpgautil show fan output data
            return a dict
            data example:
            NAME                prsnt     error     pwm       inRPM     outRPM
            ----                -----     -----     ---       -----     ------
            PSU_1               1         0                             10908
            PSU_2               1         0                             10932
            FAN-1               1         0         128       5449      6279
            FAN-2               1         0         128       5438      6293
            FAN-3               1         0         128       5443      6279
            FAN-4               1         0         128       5454      6257
            FAN-5               1         0         128       5443      6264
            '''
            parsed_data = {}
            lines = [line for line in data.splitlines() if 'NAME' in line or 'PSU' in line or 'FAN' in line]
            feilds_name = lines[0].split()
            for line in lines[1:]:
                i = 1
                fan_info = {}
                fan_name = line[:20].strip()
                fan_info[feilds_name[i]] = line[20:30].strip()
                i += 1
                fan_info[feilds_name[i]] = line[30:40].strip()
                i += 1
                fan_info[feilds_name[i]] = line[40:50].strip()
                i += 1
                fan_info[feilds_name[i]] = line[50:60].strip()
                i += 1
                fan_info[feilds_name[i]] = line[60:].strip()
                parsed_data[fan_name] = fan_info
            return parsed_data

        rc = True
        if self._mtp_type not in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            # Fan present test
            cmd = MFG_DIAG_CMDS().MTP_FAN_PRSNT_FMT
            if self.get_mtp_factory_location() == Factory.LAB:
                pass_sig_list = [MFG_DIAG_SIG.MTP_FAN0_PRSNT_SIG, MFG_DIAG_SIG.MTP_FAN1_PRSNT_SIG, MFG_DIAG_SIG.MTP_FAN2_PRSNT_SIG]
            else:
                pass_sig_list = [MFG_DIAG_SIG.MTP_PRSNT_SIG]
            rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list, timeout=MTP_Const.MTP_OS_CMD_DELAY)
            if rc:
                self.cli_log_inf("FAN present test passed")
            else:
                self.cli_log_err("FAN present test failed")
                return rc

            # Fan speed test
            cmd = MFG_DIAG_CMDS().MTP_FAN_TEST_FMT
            pass_sig_list = [MFG_DIAG_SIG.MTP_FAN_OK_SIG]
            rc = self.mtp_mgmt_exec_cmd(cmd, pass_sig_list, timeout=MTP_Const.MTP_OS_CMD_DELAY)
            if rc:
                self.cli_log_inf("FAN speed test passed")
            else:
                self.cli_log_err("FAN speed test failed")
                return rc

            # Fan speed set
            self.cli_log_inf("Set FAN PWM to {:d}%".format(fan_pwm))
            cmd = MFG_DIAG_CMDS().MTP_FAN_SET_SPD_FMT.format(fan_pwm)
            rc = self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY)
            if not rc:
                self.cli_log_err("Failed to set fan speed to {:d}%".format(fan_pwm))
                return rc
            self._fanspd = fan_pwm          # update class variable

            # fan speed verify after set
            fan_read_ite = 1
            fan_read_interval = 10
            fan1_spd_chk_ret = False
            fan2_spd_chk_ret = False
            fan3_spd_chk_ret = False
            cmd = MFG_DIAG_CMDS().MTP_FAN_STATUS_FMT
            while fan_read_ite <= 6:
                self.cli_log_inf("Wait for {:d}th {:d} seconds, before check fan speed".format(fan_read_ite, fan_read_interval))
                libmfg_utils.count_down(fan_read_interval)
                fan_read_ite += 1

                # Fan status dump
                if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
                    self.cli_log_err("Read fan speed failed by command {:s}".format(cmd))
                    rc = False
                    break

                # Fan speed verify, if PWM 60%, RPM = 6000 +-20%; if PWM 100%, RPM >= 9000
                matcher = re.search(r'FAN\s+(\d{2,})\s+(\d{2,})\s+(\d{2,})\s+(\d{2,})\s+(\d{2,})\s+(\d{2,})(\s+\d{2,}){2}', self.mtp_get_cmd_buf())
                if not matcher:
                    self.cli_log_err("Parse Read Fan speed command output failed")
                    rc = False
                    break
                fan1_inlet = int(matcher.group(1))
                fan1_outlet = int(matcher.group(2))
                fan2_inlet = int(matcher.group(3))
                fan2_outlet = int(matcher.group(4))
                fan3_inlet = int(matcher.group(5))
                fan3_outlet = int(matcher.group(6))

                if fan_pwm == 60:
                    if abs(fan1_inlet - 6000) <= 6000 * 0.2 and abs(fan1_outlet - 6000) <= 6000 * 0.2:
                        fan1_spd_chk_ret = True
                    if abs(fan2_inlet - 6000) <= 6000 * 0.2 and abs(fan2_outlet - 6000) <= 6000 * 0.2:
                        fan2_spd_chk_ret = True
                    if abs(fan3_inlet - 6000) <= 6000 * 0.2 and abs(fan3_outlet - 6000) <= 6000 * 0.2:
                        fan3_spd_chk_ret = True
                elif fan_pwm == 100:
                    if (fan1_inlet - 9000) >= 0 and (fan1_outlet - 9000) >= 0:
                        fan1_spd_chk_ret = True
                    if (fan2_inlet - 9000) >= 0 and (fan2_outlet - 9000) >= 0:
                        fan2_spd_chk_ret = True
                    if (fan3_inlet - 9000) >= 0 and (fan3_outlet - 9000) >= 0:
                        fan3_spd_chk_ret = True
                else:
                    # Not verify fan rpm for other pwm currently, just baseline check, rpm >=1000
                    if (fan1_inlet - 1000) >= 0 and (fan1_outlet - 1000) >= 0:
                        fan1_spd_chk_ret = True
                    if (fan2_inlet - 1000) >= 0 and (fan2_outlet - 1000) >= 0:
                        fan2_spd_chk_ret = True
                    if (fan3_inlet - 1000) >= 0 and (fan3_outlet - 1000) >= 0:
                        fan3_spd_chk_ret = True

                if fan1_spd_chk_ret and fan2_spd_chk_ret and fan2_spd_chk_ret:
                    break

            for fan_idx, fan_spd_chk_ret in enumerate([fan1_spd_chk_ret, fan2_spd_chk_ret, fan3_spd_chk_ret]):
                if not fan_spd_chk_ret:
                    self.cli_log_err("FAN{:d} Speed at PWM {:d} verify FAIL".format(fan_idx+1, fan_pwm))
                    rc = False
                else:
                    self.cli_log_inf("FAN{:d} Speed at PWM {:d} verify PASS".format(fan_idx+1, fan_pwm))
        else:
            # Fan present test
            cmd = MFG_DIAG_CMDS().MTP_MATERA_FPGA_SHOW_FAN_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("MTP command {:s} failed".format(cmd))
                return False
            fan_info = parse_fpga_show_fan(self.mtp_get_cmd_buf())
            fan_count = 0
            psu_count = 0
            for k, v in fan_info.items():
                if "PSU" in k:
                    psu_count += 1
                if "FAN" in k:
                    fan_count += 1
                if v['prsnt'] != '1':
                    self.cli_log_err("MTP FAN: {:s} present check failed".format(k))
                    return False
                if v['error'] != '0':
                    self.cli_log_err("MTP FAN: {:s} status check failed".format(k))
                    return False
            if psu_count != 2:
                self.cli_log_err("MTP PSU count check failed, got {:d}, but expect 2".format(psu_count))
                return False
            if fan_count != 5:
                self.cli_log_err("MTP FAN count check failed, got {:d}, but expect 5".format(fan_count))
                return False
            self.cli_log_inf("MTP FAN present and status check passed")
            # Fan speed test
            ## Set Fan PWM to 50%, check fan speed RPM
            # cmd = MFG_DIAG_CMDS().MTP_MATERA_FAN_SET_SPD_FMT.format(50)
            # rc = self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY)
            # if not rc:
            #     self.cli_log_err("Failed to set fan speed to {:d}%".format(50))
            #     return rc
            # time.sleep(30)
            # cmd = MFG_DIAG_CMDS().MTP_MATERA_FPGA_SHOW_FAN_FMT
            # if not self.mtp_mgmt_exec_cmd(cmd):
            #     self.cli_log_err("MTP command {:s} failed".format(cmd))
            #     return False
            # fan_info = parse_fpga_show_fan(self.mtp_get_cmd_buf())
            # for k, v in fan_info.items():
            #     if "PSU" in k:
            #         if int(v['outRPM']) < 6000:
            #             self.cli_log_err("{:s} FAN Outlet RPM {:s} out of range".format(k, v['outRPM']))
            #             return False
            #     if "FAN" in k:
            #         if v['pwm'] != '128':
            #             self.cli_log_err("{:s} read back pwm {:s}, not match setting value 50%".format(k, v['pwm']))
            #             return False
            #         if abs(int(v['inRPM']) - 5440) > 1000:
            #             self.cli_log_err("{:s} Inlet RPM {:s} at PWM 50 out of range".format(k, v['inRPM']))
            #             return False
            #         if abs(int(v['outRPM']) - 6220) > 1000:
            #             self.cli_log_err("{:s} Outlet RPM {:s} at PWM 50 out of range".format(k, v['outRPM']))
            #             return False
            # ## Set Fan PWM to 100%, check fan speed RPM
            # cmd = MFG_DIAG_CMDS().MTP_MATERA_FAN_SET_SPD_FMT.format(100)
            # rc = self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY)
            # if not rc:
            #     self.cli_log_err("Failed to set fan speed to {:d}%".format(100))
            #     return rc
            # time.sleep(30)
            # cmd = MFG_DIAG_CMDS().MTP_MATERA_FPGA_SHOW_FAN_FMT
            # if not self.mtp_mgmt_exec_cmd(cmd):
            #     self.cli_log_err("MTP command {:s} failed".format(cmd))
            #     return False
            # fan_info = parse_fpga_show_fan(self.mtp_get_cmd_buf())
            # for k, v in fan_info.items():
            #     if "PSU" in k:
            #         if int(v['outRPM']) < 6000:
            #             self.cli_log_err("{:s} FAN Outlet RPM {:s} out of range".format(k, v['outRPM']))
            #             return False
            #     if "FAN" in k:
            #         if v['pwm'] != '255':
            #             self.cli_log_err("{:s} read back pwm {:s}, not match setting value 100%".format(k, v['pwm']))
            #             return False
            #         if abs(int(v['inRPM']) - 10400) > 1000:
            #             self.cli_log_err("{:s} Inlet RPM {:s} at PWM 100 out of range".format(k, v['inRPM']))
            #             return False
            #         if abs(int(v['outRPM']) - 12100) > 1000:
            #             self.cli_log_err("{:s} Outlet RPM {:s} at PWM 100 out of range".format(k, v['outRPM']))
            #             return False
            # self.cli_log_inf("MTP FAN speed test passed")
            # Fan speed set target value
            self.cli_log_inf("Set FAN PWM to target {:d}%".format(fan_pwm))
            cmd = MFG_DIAG_CMDS().MTP_MATERA_FAN_SET_SPD_FMT.format(fan_pwm)
            rc = self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY)
            if not rc:
                self.cli_log_err("Failed to set fan speed to {:d}%".format(fan_pwm))
                return rc
            self._fanspd = fan_pwm          # update class variable
            # fan speed verify after set
            time.sleep(20)
            cmd = MFG_DIAG_CMDS().MTP_MATERA_FPGA_SHOW_FAN_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("MTP command {:s} failed".format(cmd))
                return False
            fan_info = parse_fpga_show_fan(self.mtp_get_cmd_buf())
            for k, v in fan_info.items():
                if "FAN" in k:
                    if abs(int(v['pwm']) - round(255 * fan_pwm /100)) > 1:
                        self.cli_log_err("{:s} read back pwm {:s}, not match setting value {:s}".format(k, v['pwm'], str(fan_pwm)))
                        return False
        return rc

    def mtp_get_nic_sn_start(self, slot=0):
        rc = ""
        cmd = "eeutil -uut=UUT_{:s} -disp -field=sn".format(str(slot + 1))
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP get Serial Number Failed.")
            return rc

        # [INFO]    [2022-04-22-14:36:41.01 ] Serial Number                                FPN21370231
        match = re.search(r"Serial\sNumber\s+([A-Za-z0-9]{8,})", self.mtp_get_cmd_buf())
        if match:
            # validate the readings
            sn = match.group(1)
            rc = sn

        return rc

    def mtp_diag_pre_init(self, start_dsp=True, stage=FF_Stage.FF_DL):
        # start the mtp diag
        self.cli_log_inf("Pre Diag SW Environment Init", level=0)

        cmd = "touch /dev/prompt"
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_err("{:s} command failed".format(cmd), level=0)
            return False

        cmd = MFG_DIAG_CMDS().MTP_STOP_REDIS_FMT
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_slot_err("Command sudo {:s} failed".format(cmd))
            return False

        cmd = MFG_DIAG_CMDS().MTP_DIAG_INIT_FMT
        sig_list = [MFG_DIAG_SIG.MTP_DIAG_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = "source ~/.bash_profile"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=5):
            self.cli_log_err("Failed to Init Diag SW Environment", level=0)
            return False

        cmd = "env | grep UUT"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute env command", level=0)
            return False

        # MTP_TYPE
        cmd = MFG_DIAG_CMDS().MTP_TYPE_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to send command for getting MTP type", level = 0)
            return False
        match = re.findall(r"MTP_TYPE=MTP_([a-zA-Z_]+)", self.mtp_get_cmd_buf())
        if match:
            self._mtp_type = match[0].strip().upper()
        else:
            self.cli_log_err("Failed to get MTP type", level = 0)
            return False

        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            cmd = "killall fpga_uart"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Command {:s} failed".format(cmd), level=0)
                return False
            if not start_dsp:
                cmd = "fstrim -v /home/diag/"
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("Command {:s} failed".format(cmd), level=0)
                    return False
            if stage == FF_Stage.FF_SWI:
                # python package version
                cmd = MFG_DIAG_CMDS().MTP_MATERA_SWI_CHECK_FMT
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("Failed to send command to check python package version", level = 0)
                    return False
                match = re.findall(r"MTP is ready for SWI", self.mtp_get_cmd_buf())
                if not match:
                    self.cli_log_err("MTP do not have correct python package version", level = 0)
                    return False

        if start_dsp:
            # kill other diagmgr instances
            cmd = "killall diagmgr"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Command {:s} failed".format(cmd), level=0)
                return False

            cmd = "ps -elf | grep diagmgr"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Command {:s} failed".format(cmd), level=0)
                return False

            cmd = "ps -elf | grep redis"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Command {:s} failed".format(cmd), level=0)
                return False

            # start the mtp diagmgr
            diagmgr_handle = self.mtp_session_create()
            if not diagmgr_handle:
                self.cli_log_err("Failed to create diagmgr session", level=0)
                return False

            cmd = MFG_DIAG_CMDS().MTP_DIAG_MGR_START_FMT.format(self._diagmgr_logfile)
            diagmgr_handle.sendline(cmd)
            idx = libmfg_utils.mfg_expect(diagmgr_handle, [self._mgmt_prompt])
            if idx < 0:
                self.cli_log_err("Failed to start diagmgr", level=0)
                return False
            time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
            diagmgr_handle.close()

            # register MTP diagsp
            cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to access dshell", level=0)
                return False

            cmd = "ps -elf | grep diagmgr"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Command {:s} failed".format(cmd), level=0)
                return False

            cmd = "ps -elf | grep redis"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Command {:s} failed".format(cmd), level=0)
                return False

            if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
                cmd = "redis-cli hkeys CARD_DICT"
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("Command {:s} failed".format(cmd), level=0)
                    return False

            cmd = MFG_DIAG_CMDS().MTP_DSP_START_FMT
            sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
                self.cli_log_err("Failed to start dsp", level=0)
                return False

            cmd = "ps -elf | grep diagmgr"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Command {:s} failed".format(cmd), level=0)
                return False

            time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        if not self.mtp_sys_info_init():
            self.cli_log_err("Failed to Init MTP system information", level=0)
            return False

        self.cli_log_inf("Pre Diag SW Environment Init complete\n", level=0)
        return True

    def mtp_inlet_temp_test(self, stage=None, sanity=False):
        rc = True
        inlet_1, inlet_2 = None, None
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            cmd = "devmgr_v2 status -d TSENSOR_IOBL"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("{:s} command failed".format(cmd))
                return False
            cmd_buf_1 = self.mtp_get_cmd_buf()
            cmd = "devmgr_v2 status -d TSENSOR_IOBR"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP get inlet temperature failed")
                return False
            cmd_buf_2 = self.mtp_get_cmd_buf()
            match_1 = re.search(r"TSENSOR.* (-?\d+\.\d+)", cmd_buf_1)
            match_2 = re.search(r"TSENSOR.* (-?\d+\.\d+)", cmd_buf_2)
            inlet_1 = float(match_1.group(1))
            inlet_2 = float(match_2.group(1))
        else:
            cmd = MFG_DIAG_CMDS().MTP_FAN_STATUS_FMT
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY):
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP get inlet temperature failed")
                return False

            # Current Fan Speed display
            ret = re.findall(r'NAME\s+FAN\d-Inlet\s+|FAN\d-Inlet\s+|FAN\d-Outlet\s', self.mtp_get_cmd_buf())
            if not ret:
                self.cli_log_err("MTP get fan name failed")
                return False
            if not sanity:
                self.cli_log_inf("".join(ret).strip('\n'))
            ret = re.search(r'FAN(\s+\d{3,}){6}(\s+\d{2,}){2}', self.mtp_get_cmd_buf())
            if not ret:
                self.cli_log_err("MTP get fan speed failed")
                return False
            if not sanity:
                self.cli_log_inf(ret.group(0))

            # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
            # FAN                 23.50          25.50          21.75          21.75
            match = re.search(r"FAN +(-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+)", self.mtp_get_cmd_buf())
            if match:
                # validate the readings
                inlet_1 = float(match.group(3))
                inlet_2 = float(match.group(4))
        if inlet_1 != None and inlet_2 != None:
            inlet_1_rs = True
            inlet_2_rs = True
            max_temp = 70
            min_temp = -10

            if (inlet_1 < min_temp or inlet_1 > max_temp):
                inlet_1_rs = False
                rc = False
            if (inlet_2 < min_temp or inlet_2 > max_temp):
                inlet_2_rs = False
                rc = False

            if not rc:
                if not inlet_1_rs and not inlet_2_rs:
                    if inlet_1 < min_temp and inlet_2 < min_temp:
                        self.cli_log_err("Inlet1 ({:s}) is lesser than {:s} degree, Inlet2 ({:s}) is lesser than {:s} degree, temperature test failed".format(
                            str(inlet_1), str(min_temp), str(inlet_2), str(min_temp)))
                    elif inlet_1 < min_temp and inlet_2 > max_temp:
                        self.cli_log_err("Inlet1 ({:s}) is lesser than {:s} degree, Inlet2 ({:s}) is greater than {:s} degree, temperature test failed".format(
                            str(inlet_1), str(min_temp), str(inlet_2), str(max_temp)))
                    elif inlet_1 > max_temp and inlet_2 < min_temp:
                        self.cli_log_err("Inlet1 ({:s}) is geater than {:s} degree, Inlet2 ({:s}) is lesswe than {:s} degree, temperature test failed".format(
                            str(inlet_1), str(max_temp), str(inlet_2), str(min_temp)))
                    else:
                        self.cli_log_err("Inlet1 ({:s}) is geater than {:s} degree, Inlet2 ({:s}) is greater than {:s} degree, temperature test failed".format(
                            str(inlet_1), str(max_temp), str(inlet_2), str(max_temp)))
                elif not inlet_1_rs:
                    if inlet_1 < min_temp:
                        self.cli_log_err("Inlet1 ({:s}) is lesser than {:s} degree, Inlet2 ({:s}), temperature test failed".format(str(inlet_1), str(min_temp), str(inlet_2)))
                    else:
                        self.cli_log_err("Inlet1 ({:s}) is greater than {:s} degree, Inlet2 ({:s}), temperature test failed".format(str(inlet_1), str(max_temp), str(inlet_2)))
                elif not inlet_2_rs:
                    if inlet_2 < min_temp:
                        self.cli_log_err("Inlet1 ({:s}), Inlet2 ({:s}) is lesser than {:s} degree, temperature test failed".format(str(inlet_1), str(inlet_2), str(min_temp)))
                    else:
                        self.cli_log_err("Inlet1 ({:s}), Inlet2 ({:s}) is greater than {:s} degree, temperature test failed".format(str(inlet_1), str(inlet_2), str(max_temp)))

            else:
                self.cli_log_inf("Inlet1 ({:s}), Inlet2 ({:s}) temperature test passed".format(str(inlet_1), str(inlet_2)))

        else:
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP get inlet temperature failed")
            return False

        return rc

    def mtp_diag_dsp_restart(self):
        self.cli_log_inf("DSP Restart", level=0)

        # stop MTP DSP
        cmd = MFG_DIAG_CMDS().MTP_DSP_STOP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        # sys cleanup
        cmd = MFG_DIAG_CMDS().MTP_DSP_CLEANUP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        # kill other diagmgr instances
        cmd = "killall diagmgr"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False

        # start the mtp diagmgr
        diagmgr_handle = self.mtp_session_create()
        if not diagmgr_handle:
            self.cli_log_err("Failed to create new diagmgr handle", level=0)
            return False

        cmd = MFG_DIAG_CMDS().MTP_DIAG_MGR_RESTART_FMT.format(self._diagmgr_logfile)
        diagmgr_handle.sendline(cmd)
        idx = libmfg_utils.mfg_expect(diagmgr_handle, ["$"])
        if idx < 0:
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            self.cli_log_err("{:s}".format(diagmgr_handle.before))
            return False
        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)
        diagmgr_handle.close()

        # register MTP diagsp
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False

        cmd = MFG_DIAG_CMDS().MTP_DSP_START_FMT
        sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False

        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        self.cli_log_inf("DSP restart complete\n", level=0)

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
            cmd = MFG_DIAG_CMDS().MTP_ZMQ_STOP_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False

            # 2. stop MTP DSP
            cmd = MFG_DIAG_CMDS().MTP_DSP_STOP_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False
            time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

            # 3. sys cleanup
            cmd = MFG_DIAG_CMDS().MTP_DSP_CLEANUP_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False

            # 4. start MTP DSP
            cmd = MFG_DIAG_CMDS().MTP_DSP_START_FMT
            sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
                self.cli_log_err("Failed to execute command {:s}".format(cmd))
                return False
            time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

            # 5. start ZMQ
            cmd = MFG_DIAG_CMDS().MTP_ZMQ_START_FMT
            sig_list = [MFG_DIAG_SIG.MTP_ZMQ_OK_SIG]
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.OS_CMD_DELAY):
                continue
            else:
                break

        if retry >= 3:
            self.cli_log_err("Failed to Init Diag ZMQ Environment", level=0)
            return False

        self.cli_log_inf("Init Diag ZMQ Environment complete\n", level=0)
        return True

    def mtp_diag_get_img_files(self):
        cmd = "ls --color=never {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd), level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf().split()
        return cmd_buf

    def mtp_diag_post_init(self):
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

        cmd = MFG_DIAG_CMDS().MTP_DSP_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Dump DSP failed", level=0)
            return False

        self.cli_log_inf("Post Diag SW Environment Init complete\n", level=0)
        return True

    # make sure mtp_hw_init is always done after mtp_sys_info_init, as it needs info collected from it

    def mtp_hw_init(self, stage=None):
        rc = True

        fan_spd = libmfg_utils.pick_fan_speed(stage, self._mtp_type)

        self.cli_log_inf("Start MTP chassis sanity check", level=0)
        if self._mtp_type == MTP_TYPE.MATERA:
            # cpu expected cores and temperature check
            rc &= self.matera_mtp_cpu_chk_test()
            # ddr capacity and frequency check
            rc &= self.matera_mtp_ddr_chk_test()
            # board temperature check
            rc &= self.matera_mtp_board_temp_chk_test()
            # fan test and fan spd set
            rc &= self.mtp_fan_init(fan_spd)
            # PSU fan temp and status check
            rc &= self.mtp_psu_init()
            # PSU Firmware Check
            rc &= self.matera_penarea_mtp_psu_fw_chk_test()
            # FPGA revsion, register RW and lspci( gen1 by 1, maybe) check
            rc &= self.mtp_fpga_chk_test()
            # MTP FRU check and display, Serial Number is valid
            rc &= self.matera_mtp_fru_chk_test()
            rc = True
        elif self._mtp_type == MTP_TYPE.PANAREA:
            # cpu expected cores and temperature check
            rc &= self.matera_mtp_cpu_chk_test()
            # ddr capacity and frequency check
            rc &= self.matera_mtp_ddr_chk_test()
            # board temperature check
            rc &= self.matera_mtp_board_temp_chk_test()
            # fan test and fan spd set
            rc &= self.mtp_fan_init(fan_spd)
            # PSU fan temp and status check
            rc &= self.mtp_psu_init()
            # PSU Firmware Check
            rc &= self.matera_penarea_mtp_psu_fw_chk_test()
            # FPGA revsion, register RW and lspci( gen1 by 1, maybe) check
            rc &= self.mtp_fpga_chk_test()
            # MTP FRU check and display, Serial Number is valid
            rc &= self.matera_mtp_fru_chk_test()
            rc = True

            # Extract the cns-pmic version for Panarea, string starts with 'v'
            cmd = "head -1 /home/diag/cns-pmci/VERSION"
            if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
                self.cli_log_err("Failed to execute command: {:s}".format(cmd), level=0)
                return False
            match = re.findall(r"(v[\w.]+)", self.mtp_get_cmd_buf())
            if match:
                self._cns_pmci_ver = match[0]
        else:
            rc &= self.mtp_cpld_test()
            # fan init
            rc &= self.mtp_fan_init(fan_spd)
            # read psu info and test psu
            rc &= self.mtp_psu_init()
            # mtp inlet temperature
            rc &= self.mtp_inlet_temp_test(stage, sanity=True)

            # other platform init
            rc &= self.mtp_misc_init()

        if rc:
            self.cli_log_inf("MTP chassis sanity check passed\n", level=0)
        else:
            self.cli_log_err("MTP chassis sanity check failed\n", level=0)

        return rc

    def mtp_wait_temp_ready(self, low_threshold=None, high_threshold=None):
        if low_threshold != None:
            self.cli_log_inf("Wait the environment temperature drop to {:2.2f}".format(low_threshold))
            upper_limit = MTP_Const.LOW_CHAMBER_UPPER_LIMIT
            lower_limit = MTP_Const.LOW_CHAMBER_LOWER_LIMIT
            if not GLB_CFG_MFG_TEST_MODE:
                upper_limit = MTP_Const.HIGH_CHAMBER_UPPER_LIMIT
                lower_limit = MTP_Const.LOW_CHAMBER_LOWER_LIMIT
        elif high_threshold != None:
            self.cli_log_inf("Wait the environment temperature rise to {:2.2f}".format(high_threshold))
            upper_limit = MTP_Const.HIGH_CHAMBER_UPPER_LIMIT
            lower_limit = MTP_Const.HIGH_CHAMBER_LOWER_LIMIT
            if not GLB_CFG_MFG_TEST_MODE:
                upper_limit = MTP_Const.HIGH_CHAMBER_UPPER_LIMIT
                lower_limit = MTP_Const.LOW_CHAMBER_LOWER_LIMIT
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
            if not MFG_BYPASS_PSU_CHECK and self._mtp_rev is not None and self._mtp_rev != "NONE" and len(self._mtp_rev) > 0 and int(self._mtp_rev) > 3:
                cmd = MFG_DIAG_CMDS().MTP_PSU_TEST_FMT
                self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_OS_CMD_DELAY)

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

        # mtp sensor test, make sure two inlet sensor reading difference is less than 10
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
        for ver_info in cpld_ver_list:
            if not ver_info:
                self.cli_log_err("Unable to retrieve MTP CPLD version")
                self.cli_log_err("MTP CPLD test failed")
                return False

        io_version = MTP_IMAGES.mtp_io_cpld_ver[self._mtp_type]
        jtag_version = MTP_IMAGES.mtp_jtag_cpld_ver[self._mtp_type]

        if self._mtp_rev is not None and self._mtp_rev != "NONE" and len(self._mtp_rev) > 0 and int(self._mtp_rev) > 2:
            if int(cpld_ver_list[0], 16) < int(io_version, 16):
                self.cli_log_err("MTP IO CPLD Version: {:s}, expect: {:s}".format(cpld_ver_list[0], io_version))
                self.cli_log_err("MTP CPLD test failed")
                return False

            if cpld_ver_list[1] != jtag_version:
                self.cli_log_err("MTP JTAG CPLD Version: {:s}, expect: {:s}".format(cpld_ver_list[1], jtag_version))
                self.cli_log_err("MTP CPLD test failed")
                return False
            self.cli_log_inf("MTP CPLD test passed")
        else:
            self.cli_log_inf("MTP CPLD test skipped for REV_{:s}".format(self._mtp_rev))
        return True

    def matera_mtp_cpu_chk_test(self, exp_cpu_cores=6):
        '''
        This function only works on Matera MTP, call "inventory -cpu" command, parse the message and check cpu cores, temperature.
        '''

        cmd = MFG_DIAG_CMDS().MTP_MATERA_INVENTORY_CPU_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("MTP command {:s} failed".format(cmd))
            return False
        cpu_info = self.mtp_get_cmd_buf()
        # check cpu cores info from dmidecode
        found_cpu_cores = re.findall(r'CPU Model:.*(\d+)\-Core Processor', cpu_info)
        cpu_core = found_cpu_cores[0] if found_cpu_cores else None
        if not cpu_core:
            self.cli_log_err("Failed to parse number of CPU cores info")
            self.cli_log_err(cpu_info)
            return False
        if int(cpu_core) != exp_cpu_cores:
            self.cli_log_err("Expect {:s} CPU cores, but get {:s}".format(str(exp_cpu_cores), str(cpu_core)))
            return False
        self.cli_log_inf('Got CPU core number: {:s}, match expected: {:s}'.format(str(cpu_core), str(exp_cpu_cores)))

        # check cpu temp, k10temp is AMD cpu kermel driver,
        # Tctl: This is the control temperature. It is an abstract value used by the system's thermal management to control cooling.
        # It might not correspond directly to a physical temperature but is used to trigger thermal throttling and cooling mechanisms.
        # Tccd1: This is the temperature of a specific core complex die (CCD) on the CPU.
        # Modern AMD CPUs, particularly those in the Ryzen and EPYC families, are composed of multiple core complexes.
        # Tccd1 refers to the temperature of the first CCD.
        found_tctl = re.findall(r'Tctl:\s+([\+\-]\d+\.\d+)°C', cpu_info)
        tctl = found_tctl[0] if found_tctl else None
        if not tctl:
            self.cli_log_err('Failed to parse Tctl temp')
            self.cli_log_err(cpu_info)
            return False
        if float(tctl) < 0 or float(tctl) > 100:
            self.cli_log_err('Senor Tctl reading out of range 0<>100')
            self.cli_log_err(cpu_info)
            return False
        self.cli_log_inf('Got CPU control temperature sensor Tctl {:s}°C'.format(tctl))
        found_tccd1 = re.findall(r'Tccd1:\s+([\+\-]\d+\.\d+)°C', cpu_info)
        tccd1 = found_tccd1[0] if found_tccd1 else None
        if not tccd1:
            self.cli_log_err('Failed to parse Tccd1 temp')
            self.cli_log_err(cpu_info)
            return False
        if float(tccd1) < 0 or float(tccd1) > 100:
            self.cli_log_err('Sensor Tccd1 reading out of range 0<>100')
            self.cli_log_err(cpu_info)
            return False
        self.cli_log_inf('Got CPU specific core complex die temperature sensor Tccd1 {:s}°C'.format(tccd1))

        return True

    def matera_mtp_ddr_chk_test(self):
        '''
        This function only works on Matera MTP, call "inventory -ddr" command, parse the message and dispaly memory capacity and speed.
        '''

        cmd = MFG_DIAG_CMDS().MTP_MATERA_INVENTORY_DDR_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("MTP command {:s} failed".format(cmd))
            return False
        memory_info = self.mtp_get_cmd_buf()
        # check ddr info from dmidecode
        found_size = re.findall(r'Size:\s+(\d+)\s+GB', memory_info)
        if not found_size:
            self.cli_log_err("Failed to parse DDR memory size")
            self.cli_log_err(memory_info)
            return False
        total_mem_size = sum([int(i) for i in found_size])
        found_type = re.findall(r'Type:\s+(DDR\d)', memory_info)
        if not found_type:
            self.cli_log_err("Failed to parse DDR memory type")
            self.cli_log_err(memory_info)
            return False
        mem_type = found_type[0]
        found_speed = re.findall(r'\s{2,10}Speed:\s+(\d+\s+.*)', memory_info)
        if not found_speed:
            self.cli_log_err("Failed to parse DDR memory speed")
            self.cli_log_err(memory_info)
            return False
        mem_speed = found_speed[0]
        self.cli_log_inf("Got {:s} memory in total {:d}GB with speed {:s}".format(mem_type, total_mem_size, mem_speed))
        return True

    def matera_mtp_board_temp_chk_test(self):
        '''
        This function only works for Matera MTP, call "devmgr_v2 status" command, parse the data and check board temperature in range.
        '''

        cmd = MFG_DIAG_CMDS().MTP_MATERA_DEVMGR_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("MTP command {:s} failed".format(cmd))
            return False
        devmgr_status_output = self.mtp_get_cmd_buf()
        found_iobl = re.findall(r'TSENSOR_IOBL\(°C\)\s+(\-?\d+\.\d+)', devmgr_status_output)
        if not found_iobl:
            self.cli_log_err("Failed to parse TSENSOR_IOBL reading")
            self.cli_log_err(devmgr_status_output)
            return False
        iobl_reading = found_iobl[0]
        found_iobr = re.findall(r'TSENSOR_IOBR\(°C\)\s+(\-?\d+\.\d+)', devmgr_status_output)
        if not found_iobr:
            self.cli_log_err("Failed to parse TSENSOR_IOBR reading")
            self.cli_log_err(devmgr_status_output)
            return False
        iobr_reading = found_iobr[0]
        found_mb = re.findall(r'TSENSOR_MB\(°C\)\s+(\-?\d+\.\d+)', devmgr_status_output)
        if not found_mb:
            self.cli_log_err("Failed to parse TSENSOR_MB reading")
            self.cli_log_err(devmgr_status_output)
            return False
        mb_reading = found_mb[0]
        self.cli_log_inf("Got board temperature sensor TSENSOR_IOBL {:s}C, TSENSOR_IOBR {:s}C, TSENSOR_MB {:s}C".format(iobl_reading, iobr_reading, mb_reading))

        # Chassis inlet temp check
        # According Matera MTP design, we can use TSENSOR_IOBL and TSENSOR_IOBR as chassis inlet temperature for test
        max_temp = 70
        min_temp = -10
        if float(iobl_reading) > max_temp or float(iobl_reading) < min_temp:
            self.cli_log_err("Inlet temp sensor TSENSOR_IOBL reading out of range {:s}<>{:s}".format(str(min_temp), str(max_temp)))
            return False
        if float(iobr_reading) > max_temp or float(iobr_reading) < min_temp:
            self.cli_log_err("Inlet temp sensor TSENSOR_IOBR reading out of range {:s}<>{:s}".format(str(min_temp), str(max_temp)))
            return False
        if abs(float(iobl_reading) - float(iobr_reading)) > 15:
            self.cli_log_err("Difference between inlet temp sensor TSENSOR_IOBL and TSENSOR_IOBL exceed 15")
            return False

        return True


    def matera_mtp_fru_chk_test(self):
        '''
        This function only works for Matera MTP, call "eeutil -info" command, parse the data and check fru presence and serial number is valid.
        '''

        frus_list = ['FRU', 'IOBL', 'IOBR', 'FPIC']
        # Fru presence check
        cmd = MFG_DIAG_CMDS().MTP_MATERA_EEUTIL_INFO_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("MTP command {:s} failed".format(cmd))
            return False
        eeutil_info_output = self.mtp_get_cmd_buf()

        for fru in frus_list:
            if fru not in eeutil_info_output:
                self.cli_log_err("Failed to find {:S}".format(fru))
                self.cli_log_err(eeutil_info_output)
                return False
        self.cli_log_inf("FRU, IOBL, IOBR and FPIC founded in eeutil info")

        # FRU serial number check
        for fru in frus_list:
            fru_sn = ""
            cmd = MFG_DIAG_CMDS().MTP_MATERA_DISP_DEV_FMT.format(fru)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("MTP command {:s} failed".format(cmd))
                return False
            fru_info_output = self.mtp_get_cmd_buf()
            if "Failed to display tlv-based eeprom".lower() in fru_info_output.lower():
                self.cli_log_err("{:s} eeprom not program".format(fru))
                return False
            for line in fru_info_output.splitlines():
                if 'Serial Number' in line:
                    fru_sn = line.split('Serial Number')[-1].strip().replace('\x00', '')
            if not fru_sn:
                self.cli_log_err("Failed to parse {:s} serial number".format(fru))
                return False
            # if eeprom is blank, we fake one for validation script logic with command: eeutil -update -dev=IOBR -pn="102-P10400-00" -sn="IOB_R000000" -mac="000000000000" -date="050324"
            # one example, eeutil -update -dev=FRU -pn="102-P10200-00 21" -sn="FPF24390192" -mac="049081568E48" -date="121824"
            if not re.match(r'FPF\w{8}', fru_sn):
                self.cli_log_err("{:s} serial number {:s} format check failed".format(fru, fru_sn))
                return False
            self.cli_log_inf('{:s} serial number {:s} check pass'.format(fru, fru_sn))

        return True

    def mtp_fpga_chk_test(self):

        # version check
        fpga_running_ver, fpga_running_date, fpga_running_timestamp = self._fpga_ver
        fpga_img_ver = MTP_IMAGES.mtp_fpga_ver[self._mtp_type]
        fpga_img_date = MTP_IMAGES.mtp_fpga_date[self._mtp_type]
        if fpga_running_ver != fpga_img_ver:
            self.cli_log_err("MTP FPGA Runing Version: {:s}, expect: {:s}".format(fpga_running_ver, fpga_img_ver))
            self.cli_log_err("MTP FPGA Version Check Test failed")
            return False
        if fpga_running_date != fpga_img_date:
            self.cli_log_err("MTP FPGA Runing datecode: {:s}, expect: {:s}".format(fpga_running_date, fpga_img_date))
            self.cli_log_err("MTP FPGA datecode Check Test failed")
            return False
        self.cli_log_inf("MTP FPGA Version Check pass. version: {:s}, datecode: {:s}, timestamp: {:s}".format(fpga_running_ver, fpga_running_date, fpga_running_timestamp))

        # Register read write check, Write scratch register then read back and compare
        reg_addr = '0x10' # SCRATCH_0_REG
        test_value = '0xffffffff'
        cmd = MFG_DIAG_CMDS().MTP_FPGA_UTIL_WRITE32_FMT.format(reg_addr, test_value)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("FPGA Command Failed to write scratch register 0", level=0)
            return False
        match = re.findall(r"WR \[0x0010\] = (0x\w+)", self.mtp_get_cmd_buf())
        if match:
            if test_value.lower() != match[0].lower():
                self.cli_log_err("FPGA Command Failed, echo back not match the write value of scratch register 0", level=0)
        else:
            self.cli_log_err("Failed to parse echo back message of write scratch register 0", level=0)
            return False

        cmd = MFG_DIAG_CMDS().MTP_FPGA_UTIL_READ32_FMT.format(reg_addr)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("FPGA Command Failed to read scratch register 0", level=0)
            return False
        match = re.findall(r"RD \[0x0010\] = (0x\w+)", self.mtp_get_cmd_buf())
        if match:
            if test_value.lower() != match[0].lower():
                self.cli_log_err("FPGA Command Failed, read back value not match the write value of scratch register 0", level=0)
        else:
            self.cli_log_err("Failed to parse read scratch register 0", level=0)
            return False
        self.cli_log_inf("MTP FPGA scratch register read/write check pass")
        # dump all registers for information
        cmd = MFG_DIAG_CMDS().MTP_FPGA_UTIL_REGDUMP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("FPGA DUMP Registers Command Failed", level=0)
            return False

        # lspci check speed and width
        cmd = "lspci -vvv -d 1dd8:000b"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("MTP command {:s} failed".format(cmd))
            return False
        lspci_output = self.mtp_get_cmd_buf()
        for line in lspci_output.splitlines():
            if 'LnkCap:' in line:
                speed = re.findall(r'Speed\s+(\d.*)GT\/s\,', line)
                if not speed:
                    self.cli_log_err("Failed to parse FPGA device pcie bus speed")
                    return False
                speed = speed[0]
                width = re.findall(r'Width\s+x(\d+)\,', line)
                if not width:
                    self.cli_log_err("Failed to parse FPGA device pcie bus width")
                    return False
                width = width[0]
                break
        if float(speed) < 2.5 or int(width) < 1:
            self.cli_log_err("FPGA PCI connection speed and width check failed")
            return False

        self.cli_log_inf("FPGA running {:s}GB/s at by x{:s} pcie bus".format(speed, width))
        return True

    def mtp_inlet_sensor_test(self):
        inlet_1, inlet_2 = None, None

        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            cmd = "devmgr_v2 status -d TSENSOR_IOBL"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP get inlet temperature failed")
                return False
            cmd_buf_1 = self.mtp_get_cmd_buf()
            cmd = "devmgr_v2 status -d TSENSOR_IOBR"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP get inlet temperature failed")
                return False
            cmd_buf_2 = self.mtp_get_cmd_buf()
            match_1 = re.search(r"TSENSOR.* (-?\d+\.\d+)", cmd_buf_1)
            match_2 = re.search(r"TSENSOR.* (-?\d+\.\d+)", cmd_buf_2)
            inlet_1 = float(match_1.group(1))
            inlet_2 = float(match_2.group(1))

        else:
            cmd = MFG_DIAG_CMDS().MTP_FAN_STATUS_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("MTP Inlet sensor test failed when execute command {:s}".format(cmd))
                return False

            # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
            # FAN                 23.50          25.50          21.75          21.75
            match = re.search(r"FAN +(-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+)", self.mtp_get_cmd_buf())
            # validate the readings
            inlet_1 = float(match.group(3))
            inlet_2 = float(match.group(4))

        if inlet_1 != None and inlet_2 != None:
            inlet_diff = abs(inlet_1 - inlet_2)
            # if the difference is more than 10, something is wrong, relay on any inlet near the threshold
            if inlet_diff > 10.0:
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP Inlet sensor test failed, the difference between inlet1 reading {:.2f} and inlet2 reading {:.2f} is more than 10".format(inlet_1, inlet_2))
                return False
            else:
                self.cli_log_inf("MTP Inlet sensor test passed")
                return True
            return True
        else:
            self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
            self.cli_log_err("MTP Inlet sensor test failed, command output Not Match sensor reading search pattern")
            return False

    def mtp_get_inlet_temp(self, low_threshold, high_threshold):
        inlet_1, inlet_2 = None, None
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            cmd = "devmgr_v2 status -d TSENSOR_IOBL"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP get inlet temperature failed")
                return 0.00
            cmd_buf_1 = self.mtp_get_cmd_buf()
            cmd = "devmgr_v2 status -d TSENSOR_IOBR"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP get inlet temperature failed")
                return 0.00
            cmd_buf_2 = self.mtp_get_cmd_buf()
            match_1 = re.search(r"TSENSOR.* (-?\d+\.\d+)", cmd_buf_1)
            if not match_1:
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP get sensor TSENSOR_IOBL reading failed")
                return 0.00
            match_2 = re.search(r"TSENSOR.* (-?\d+\.\d+)", cmd_buf_2)
            if not match_2:
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP get sensor TSENSOR_IOBR reading failed")
                return 0.00
            inlet_1 = float(match_1.group(1))
            inlet_2 = float(match_2.group(1))
        else:
            cmd = MFG_DIAG_CMDS().MTP_FAN_STATUS_FMT
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.mtp_dump_err_msg(self.mtp_get_cmd_buf())
                self.cli_log_err("MTP get inlet temperature failed")
                return 0.00

            # [Device name]      [Local]       [Outlet]       [Inlet 1]      [Inlet 2]
            # FAN                 23.50          25.50          21.75          21.75
            match = re.search(r"FAN +(-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+) + (-?\d+\.\d+)", self.mtp_get_cmd_buf())
            if match:
                inlet_1 = float(match.group(3))
                inlet_2 = float(match.group(4))

        if inlet_1 != None and inlet_2 != None:
            # validate the readings
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
            return 0.00

    def mtp_get_fanspd(self):
        """
         Returns the fanspeed (in percent) that had been set by the script.
         Does NOT return live status --> use mtp_get_inlet_temp() for that.
        """
        return self._fanspd

    # return list of error message
    def mtp_mgmt_retrieve_nic_l1_err(self, sn, ow=False):
        err_msg_list = list()
        pass_count = 0
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR
        # logfile_exp = r"(cap|elb)_l1_screen_board_{:s}.*log".format(sn)
        if ow:
            logfile_exp = r"l1_ow_screen_board_{:s}.*log".format(sn)
        else:
            logfile_exp = r"l1_screen_board_{:s}.*log".format(sn)
        for filename in os.listdir(path):
            if re.match(logfile_exp, filename):
                with open(os.path.join(path, filename), 'r') as f:
                    for line in f:
                        # if MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG in line:
                        #    err_msg = line.replace('\n', '')
                        #    err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG):]
                        #    err_msg_list.append(err_msg)
                        # if MFG_DIAG_SIG.MFG_ASIC_CTC_ERR_MSG_SIG in line:
                        #    err_msg = line.replace('\n', '')
                        #    err_msg_list.append(err_msg)
                        # if MFG_DIAG_SIG.MFG_ASIC_PCIE_MAPPING_MSG_SIG in line:
                        #    err_msg = line.replace('\n', '')
                        #    err_msg_list.append(err_msg)
                        if MFG_DIAG_SIG.MFG_ASIC_FAIL_MSG_SIG in line:
                            err_msg = line.replace('\n', '')
                            err_msg_list.append(err_msg)
                        if MFG_DIAG_SIG.MFG_ASIC_PASS_MSG_SIG in line:
                            pass_count += 1

        return pass_count, err_msg_list

    # return list of error message
    def mtp_nic_retrieve_arm_l1_err(self, sn):
        err_msg_list = list()
        pass_count = 0
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR
        logfile_exp = r"{:s}_elba_arm_l1_test\.log".format(sn)
        for filename in os.listdir(path):
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
    def mtp_mgmt_retrieve_mtp_para_err(self, slot, test):
        err_msg_list = list()
        path = MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_DIR
        nic_type = self.mtp_get_nic_type(slot)
        sn = self.mtp_get_nic_sn(slot)

        if test == "PRBS_ETH":
            filename = "{:s}_prbs_eth.log".format(sn)
        elif test == "PRBS_PCIE":
            filename = "{:s}_prbs_pcie.log".format(sn)
        elif test == "SNAKE_HBM":
            filename = "{:s}_snake_hbm.log".format(sn)
        elif test == "SNAKE_PCIE":
            filename = "{:s}_snake_pcie.log".format(sn)
        elif test == "SNAKE_ELBA":
            if nic_type in GIGLIO_NIC_TYPE_LIST:
                filename = "{:s}_snake_giglio.log".format(sn)
            elif nic_type in ELBA_NIC_TYPE_LIST:
                filename = "{:s}_snake_elba.log".format(sn)
            else:
                return []
        elif test == "ETH_PRBS":
            if nic_type in GIGLIO_NIC_TYPE_LIST:
                filename = "{:s}_giglio_PRBS_MX.log".format(sn)
            elif nic_type in ELBA_NIC_TYPE_LIST:
                filename = "{:s}_elba_PRBS_MX.log".format(sn)
            else:
                return []
        elif test == "PCIE_PRBS":
            if nic_type in GIGLIO_NIC_TYPE_LIST:
                filename = "{:s}_giglio_PRBS_PCIE.log".format(sn)
            elif nic_type in ELBA_NIC_TYPE_LIST:
                filename = "{:s}_elba_PRBS_PCIE.log".format(sn)
            else:
                return []
        elif test == "ARM_L1":
            if nic_type in GIGLIO_NIC_TYPE_LIST:
                filename = "{:s}_giglio_arm_l1_test.log".format(sn)
            elif nic_type in ELBA_NIC_TYPE_LIST:
                filename = "{:s}_elba_arm_l1_test.log".format(sn)
            else:
                return []
        elif test == "DDR_BIST":
            filename = "{:s}_arm_ddr_bist_0.log".format(sn)
            filename = "{:s}_arm_ddr_bist_1.log".format(sn)
        else:
            return err_msg_list

        try:
            with open(os.path.join(path, filename), 'r') as f:
                for line in f:
                    if MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG in line:
                        err_msg = line.replace('\n', '')
                        err_msg = err_msg[err_msg.find(MFG_DIAG_SIG.MFG_ASIC_ERR_MSG_SIG):]

                        if "ERROR :: cap0.ms.em.int_groups.intreg: axi_interrupt : 1 EN 1 hier_enabled 1" in err_msg and nic_type in CAPRI_NIC_TYPE_LIST:
                            # expected error found, ignore
                            continue
                        if "ERROR :: Unexpected int set: cap0.ms.em" in err_msg and nic_type in CAPRI_NIC_TYPE_LIST:
                            # expected error found, ignore
                            continue

                        err_msg_list.append(err_msg)
        except:
            err_msg_list.append("{:s} doesn't exist".format(filename))

        return err_msg_list

    def mtp_nic_check_extdiag_boot(self, slot):
        qspi_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not qspi_info:
            self.cli_log_slot_err_lock(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = qspi_info[0]
        if boot_image != "extdiag":
            self.cli_log_slot_err_lock(slot, "NIC is booted from {:s}".format(boot_image))
            return False

        return True

    @parallelize.parallel_nic_using_console
    def mtp_verify_nic_extdiag_boot(self, slot):
        if slot in self.mtp_nic_boot_info_init(slot, skip_check=True):
            self.cli_log_slot_err(slot, "Init NIC sw boot info failed")
            return False

        return self.mtp_nic_check_extdiag_boot(slot)

    @parallelize.parallel_nic_using_console
    def mtp_verify_nic_extdiag_smode_boot(self, slot):
        if slot in self.mtp_nic_boot_info_init(slot, smode=True):
            self.cli_log_slot_err(slot, "Init NIC sw boot info failed")
            return False

        return self.mtp_nic_check_extdiag_boot(slot)

    @parallelize.parallel_nic_using_j2c
    def mtp_salina_nic_get_qsfp_present(self, slot, port_num):
        cmd = "i2cget -y {:d} 0x4a 0x02".format(int(slot)+3)
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            self.cli_log_slot_err(slot, "Command {:s} failed")
            rs = False

        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        match = re.findall(r"(0x[0-9a-fA-F]+)", cmd_buf)

        if len(match) > 2:
            read_val = int(match[2], 16)
            if (read_val & (1 << 4 + int(port_num))):
                return True
            else:
                return False
        else:
            return False

########################################
######  NIC CTRL Routines ##############
########################################

# 1. Routines that need console, can not be run in parallel
    @parallelize.parallel_nic_using_console
    def mtp_nic_boot_info_init(self, slot, smode=False, skip_check=True):
        if self._nic_ctrl_list[slot]._boot_image and self._nic_ctrl_list[slot]._kernel_timestamp and skip_check:
            # no need to do this
            self.cli_log_slot_inf(slot, "NIC boot info already present")
            return True
        nic_type = self.mtp_get_nic_type(slot)
        self.cli_log_slot_inf(slot, "Init NIC boot info")
        if nic_type not in SALINA_AI_NIC_TYPE_LIST + VULCANO_NIC_TYPE_LIST  and not self._nic_ctrl_list[slot].nic_boot_info_init(smode=smode):
            self.cli_log_slot_err(slot, "Init NIC boot info failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)

            cmd = MFG_DIAG_CMDS().NIC_DIAG_STOP_PICOCOM_FMT
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=10):
                self.cli_log_err("Execute command {:s} failed".format(cmd))
                return False

            return False

        cmd = MFG_DIAG_CMDS().NIC_DIAG_STOP_PICOCOM_FMT
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout=10):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_check_diag_boot(self, slot):
        qspi_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not qspi_info:
            self.cli_log_slot_err_lock(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = qspi_info[0]
        if boot_image != "diagfw":
            self.cli_log_slot_err_lock(slot, "NIC is booted from {:s}".format(boot_image))
            return False

        return True

    @parallelize.parallel_nic_using_console
    def mtp_verify_nic_diag_boot(self, slot):
        if slot in self.mtp_nic_boot_info_init(slot):
            self.cli_log_slot_err(slot, "Init NIC sw boot info failed")
            return False

        return slot not in self.mtp_nic_check_diag_boot(slot)

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_verify_nic_gold_boot(self, slot):
        if slot in self.mtp_nic_boot_info_init(slot):
            self.cli_log_slot_err(slot, "Init NIC gold boot info failed")
            return False

        gold_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not gold_info:
            self.cli_log_slot_err(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = gold_info[0]
        kernel_timestamp = gold_info[1]

        if (boot_image != "goldfw"):
            self.cli_log_slot_err_lock(slot, "Checking Boot Image is GoldFW Failed, NIC is booted from {:s}".format(boot_image))
            return False

        # comment out timestamp compare
        # expected_timestamp = image_control.get_goldfw(self, slot, FF_Stage.FF_SWI)["timestamp"]
        # if (expected_timestamp != kernel_timestamp):
        #     self.cli_log_slot_err_lock(slot, "goldfw Verify Failed, Expect: {:s}   Read: {:s}".format(expected_timestamp, kernel_timestamp))
        #     return False

        self.cli_log_slot_inf(slot, "NIC boot from {:s}({:s})".format(boot_image, kernel_timestamp))
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_verify_nic_sw_boot(self, slot, targetfw=None):
        if slot in self.mtp_nic_boot_info_init(slot, skip_check=False):
            self.cli_log_slot_err(slot, "Init NIC sw boot info failed")
            return False

        sw_info = self._nic_ctrl_list[slot].nic_get_boot_info()
        if not sw_info:
            self.cli_log_slot_err(slot, "Fail to retrieve NIC boot info")
            return False

        boot_image = sw_info[0]
        kernel_timestamp = sw_info[1]
        acceptable_fw_list = ["mainfwa", "mainfwb"] if targetfw is None else [targetfw]
        if boot_image not in acceptable_fw_list:
            self.cli_log_slot_err(slot, "SW boot failed, NIC is booted from {:s}, expect {:s}".format(boot_image, str(acceptable_fw_list)))
            return False
        nic_type = self.mtp_get_nic_type(slot)
        if targetfw and nic_type in SALINA_DPU_NIC_TYPE_LIST:
            # check if a35 running image pair with N1 image, namely A35 extosa pair with N1 mainfwa, A35 goldfw pari with N1 goldfw
            n1_to_a35 = {
                'goldfw' : 'goldfw',
                'mainfwa' : 'extosa',
                'mainfwb' : 'extosb'
            }
            n1_pair2a35_boot_img = n1_to_a35.get(targetfw, "")
            if not self._nic_ctrl_list[slot].salina_nic_verify_a35_boot_fw_version(n1_pair2a35_boot_img):
                self.cli_log_slot_err(slot, "Verify A35 running fw info failed")
                self.mtp_get_nic_err_msg(slot)
                return False

        self.cli_log_slot_inf(slot, "NIC default boot from {:s}({:s})".format(boot_image, kernel_timestamp))
        return True


    @parallelize.parallel_nic_using_console
    def mtp_salina_nic_verify_loaded_fw_version(self, slot):
        """
        verify the fw version displayed by "fwupdate -l" match specified in config file
        """

        goldfw_ver = image_control.get_goldfw(self, slot, FF_Stage.FF_SWI)["version"]
        mainfw_ver = image_control.get_mainfw(self, slot, FF_Stage.FF_SWI)["version"]

        if not self._nic_ctrl_list[slot].salina_nic_verify_loaded_fw_version(goldfw_ver=goldfw_ver, mainfw_ver=mainfw_ver):
            self.cli_log_slot_err(slot, "Verify loaded fw version info failed")
            self.mtp_get_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_sw_mode_switch(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_mode_switch():
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_sw_mode_switch_verify(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_mode_switch_verify():
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_pdsctl_system_show(self, slot):
        if not self._nic_ctrl_list[slot].nic_pdsctl_system_show():
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_execute_nic_cmd_from_console(self, slot, cmd, timeout=MTP_Const.OS_CMD_DELAY):
        if not self._nic_ctrl_list[slot].nic_exec_cmd_from_console(cmd, timeout):
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_sw_profile(self, slot, profile):
        if not self._nic_ctrl_list[slot].nic_sw_profile(profile):
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_nic_mgmt_reinit(self, slot):
        loop = 0
        while loop < MTP_Const.NIC_MGMT_IP_INIT_RETRY:
            loop += 1
            time.sleep(MTP_Const.NIC_MGMT_IP_SET_DELAY)
            self.cli_log_slot_inf(slot, "Reinit NIC MGMT port <{:d}> try".format(loop))
            if self._nic_ctrl_list[slot].nic_mgmt_config():
                break
            time.sleep(10)
        if loop >= MTP_Const.NIC_MGMT_IP_INIT_RETRY:
            return False

        return True

    def mtp_nic_mgmt_init(self, slot, fpo):
        # self.cli_log_slot_inf(slot, "Init NIC MGMT port")
        if not self._nic_ctrl_list[slot].nic_mgmt_init(fpo):
            # retry
            if not self.mtp_nic_mgmt_reinit(slot):
                self.cli_log_slot_err(slot, "Init NIC MGMT port failed")
                return False

        # delete the arp entry
        ipaddr = libmfg_utils.get_nic_ip_addr(slot)
        cmd = MFG_DIAG_CMDS().MTP_ARP_DELET_FMT.format(ipaddr)
        if not self.mtp_mgmt_exec_sudo_cmd(cmd):
            self.cli_log_slot_err(slot, "Command sudo {:s} failed".format(cmd))
            return False
        # ping to update the arp cache
        for x in range(2):
            time.sleep(11)
            cmd = MFG_DIAG_CMDS().MTP_NIC_PING_FMT.format(ipaddr)
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_slot_err(slot, "Command {:s} failed".format(cmd))
                return False

        cmd_buf = self.mtp_get_cmd_buf()
        match = re.findall(r" 0% packet loss", cmd_buf)
        if not match:
            self.cli_log_slot_err(slot, "Ping MTP to NIC failed")
            self._nic_ctrl_list[slot].nic_set_status(NIC_Status.NIC_STA_MGMT_FAIL)
            return False

        return True

    def mtp_nic_mini_init(self, slot, fpo=False):
        if not self.mtp_nic_mgmt_init(slot, fpo):
            return False
        if slot in self.mtp_nic_boot_info_init(slot):
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_test_nic_mem(self, slot):
        if not self._nic_ctrl_list[slot].nic_test_mem():
            return False
        else:
            return True

    @parallelize.parallel_nic_using_console
    def mtp_check_nic_jtag(self, slot):
        asic_type = "elba" if self.mtp_get_nic_type(slot) in ELBA_NIC_TYPE_LIST+GIGLIO_NIC_TYPE_LIST else "capri"
        if not self._nic_ctrl_list[slot].nic_check_jtag(asic_type):
            self.mtp_dump_nic_err_msg(slot)
            return False
        else:
            return True

    @parallelize.parallel_nic_using_smbus
    def mtp_check_nic_list_pwr_status(self, slot, testname=""):
        return self.mtp_mgmt_check_nic_pwr_status(slot, testname)

    def mtp_mgmt_check_nic_pwr_status(self, slot, testname=""):
        if not self._nic_ctrl_list[slot].nic_power_check():
            self.mtp_dump_nic_err_msg(slot)
            sub_error = " :POWER_GOOG_ERROR"
            self.cli_log_slot_err(slot, testname + sub_error)
            return False

        return True

    def mtp_mgmt_dump_nic_pll_sta(self, slot):
        reg_data_list = self._nic_ctrl_list[slot].nic_get_pll_sta()
        if not reg_data_list:
            self.cli_log_slot_err(slot, "Failed to extract ASIC PLL status")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return

        reg26_data = reg_data_list[0]
        self.cli_log_slot_inf(slot, "CPLD 0x26 = {:x}".format(reg26_data))
        core_pll_lock = reg26_data & 0x1
        cpu_pll_lock = reg26_data & 0x2
        flash_pll_lock = reg26_data & 0x4
        proto_mode_disabled = reg26_data & 0x20
        if not core_pll_lock:
            self.cli_log_slot_err(slot, "ASIC core pll is not locked")
        if not cpu_pll_lock:
            self.cli_log_slot_err(slot, "ASIC cpu pll is not locked")
        if not flash_pll_lock:
            self.cli_log_slot_err(slot, "ASIC flash pll is not locked")
        if not proto_mode_disabled:
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


    def mtp_power_on_single_nic(self, slot, dl=False):
        self.mtp_nic_lock()
        self.cli_log_slot_inf(slot, "Power on NIC, wait {:02d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY))
        if not self._nic_ctrl_list[slot].nic_power_on():
            self.mtp_nic_unlock()
            self.cli_log_slot_err(slot, "Failed to power on NIC")
            return False
        self.mtp_nic_unlock()

        self.mtp_nic_lock()
        if self._nic_type_list[slot] in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4) and not dl:
            if not self._nic_ctrl_list[slot].nic_set_i2c_after_pw_cycle():
                self.mtp_get_nic_err_msg(slot)
            else:
                self.cli_log_slot_inf(slot, "I2C value setting complete")
        self.mtp_nic_unlock()

        return True

    def mtp_power_off_single_nic(self, slot):
        self.mtp_nic_lock()
        self.cli_log_slot_inf(slot, "Power off NIC, wait {:02d} seconds for NIC power down".format(MTP_Const.NIC_POWER_OFF_DELAY))
        if not self._nic_ctrl_list[slot].nic_power_off():
            self.mtp_nic_unlock()
            self.cli_log_slot_err(slot, "Failed to power off NIC")
            return False
        self.mtp_nic_unlock()
        return True


# 4. Routines use mgmt port, can be run in parallel


    def mtp_mgmt_exec_cmd_para(self, slot, cmd, timeout=MTP_Const.OS_CMD_DELAY, sig_list=[]):
        rc = self._nic_ctrl_list[slot].mtp_exec_cmd(cmd, timeout, sig_list)
        if not rc:
            self.mtp_dump_nic_err_msg(slot)
        return rc

    def mtp_get_nic_cmd_buf(self, slot):
        return self._nic_ctrl_list[slot].nic_get_cmd_buf()

    def mtp_get_nic_cmd_buf_before_sig(self, slot):
        return self._nic_ctrl_list[slot]._buf_before_sig

    def mtp_exec_nic_cmd_get_info(self, slot, cmd, timeout=None):
        return self._nic_ctrl_list[slot].nic_get_info(cmd, timeout)

    def mtp_exec_nic_cmds_get_lastcmd_info(self, slot, cmds, timeout=None):
        rc = self._nic_ctrl_list[slot].nic_exec_cmds(cmds, timeout)
        if not rc:
            return False
        if self._nic_ctrl_list[slot].nic_get_cmd_buf():
            return self._nic_ctrl_list[slot].nic_get_cmd_buf()
        return True

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

    def mtp_nic_fst_exec_cmd(self, slot, cmd, timeout=MTP_Const.NIC_CON_CMD_DELAY):
        if not self._nic_ctrl_list[slot].nic_fst_exec_cmd(cmd, timeout):
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_ocp_rmii_linkup(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type != NIC_Type.LINGUA:
            return True
        if not self._nic_ctrl_list[slot].nic_ocp_rmii_linkup():
            self.cli_log_slot_err_lock(slot, "RMII Linkup test failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_ocp_connect(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type != NIC_Type.LINGUA:
            return True
        if not self._nic_ctrl_list[slot].nic_ocp_connect():
            self.cli_log_slot_err_lock(slot, "OCP Connect test failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_parse_nic_ocp_fru(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type != NIC_Type.LINGUA:
            return True

        fru_buf = self._nic_ctrl_list[slot].nic_read_fru(smb_fru=True, dev="fru_adap")
        if not fru_buf:
            self.cli_log_slot_err_lock(slot, "Display SMB OCP FRU failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        else:
            # [INFO]    [2022-04-22-14:36:41.01 ] Serial Number                                FPN21370231
            match = re.search(r"Serial\sNumber\s+([A-Za-z0-9]{8,})", fru_buf)
            if match:
                sn = match.group(1)
                self.cli_log_slot_inf_lock(slot, "Parse OCP SN={:s}".format(sn))
            else:
                self.cli_log_slot_err_lock(slot, "Parse OCP SN failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
        return True

    def mtp_program_nic_fru(self, slot, date, sn, mac, pn, dpn=None, sku=None, stage=None):
        nic_type = self.mtp_get_nic_type(slot)
        self.cli_log_slot_inf_lock(slot, "Program NIC FRU date={:s}, sn={:s}, mac={:s}, pn={:s}".format(date, sn, mac, pn))
        if dpn:
            self.cli_log_slot_inf_lock(slot, "Program NIC FRU dpn={:s}".format(dpn))
        if sku:
            self.cli_log_slot_inf_lock(slot, "Program NIC FRU SKU={:s}".format(sku))

        pnIn6Digits = "-".join(pn.split('-')[0:2]) if "-" in pn[0:6] else pn[0:6]
        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Failed to retrieve CPLD ID info")
            return False
        cpldId = nic_cpld_info[2]
        boardId, pciSubSysId = PN_CPLD2BOARDID_PCI_SUBSYS_ID.get((pnIn6Digits, cpldId), (None, None))
        if stage == FF_Stage.FF_SWI:
            boardId, pciSubSysId = SKU2BOARDID_PCI_SUBSYS_ID.get(sku, (None, None))
        if boardId:
            self.cli_log_slot_inf_lock(slot, "Program NIC FRU BOARD ID={:s}".format(boardId))

        if nic_type == NIC_Type.LINGUA:
            if not self._nic_ctrl_list[slot].nic_write_fru(date, sn, mac, pn, nic_type, dpn, sku, smb_fru=True, dev="cpld_fru"):
                self.cli_log_slot_err_lock(slot, "Program ASIC NIC CPLD FRU failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_power_cycle():
                self.cli_log_slot_err_lock(slot, "Failed to Power cycle after FRU program")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_read_fru(smb_fru=True, dev="cpld_fru"):
                self.cli_log_slot_err_lock(slot, "Display SMB NIC CPLD FRU failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_read_fru(smb_fru=True, dev="fru"):
                self.cli_log_slot_err_lock(slot, "Display SMB NIC FRU failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
        elif nic_type in VULCANO_NIC_TYPE_LIST:
            # for Vucano cards need program Smb FRU and micron controller FRU
            smb_fru = True
            if not self._nic_ctrl_list[slot].nic_write_fru(date, sn, mac, pn, nic_type, dpn, sku, smb_fru=smb_fru, boardid=boardId):
                self.cli_log_slot_err_lock(slot, "Program VULCANAO Smbus FRU failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_write_fru(date, sn, mac, pn, nic_type, dpn, sku, smb_fru=True, dev="SUCFRU", boardid=boardId):
                self.cli_log_slot_err_lock(slot, "Program VULCANAO NIC SUC FRU Failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_power_cycle():
                self.cli_log_slot_err_lock(slot, "Failed to Power cycle after FRU program")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_read_fru(smb_fru=True, dev="FRU"):
                self.cli_log_slot_err_lock(slot, "Display SMB NIC FRU failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_read_fru(smb_fru=True, dev="SUCFRU"):
                self.cli_log_slot_err_lock(slot, "Display SMB NIC FRU failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False
        else:
            # for Salina cards need program SMBus FRU first, then DPU_FRU/2nd PCIe FRU, put smb_fru to True to program smbus FRU
            smb_fru = True if nic_type in SALINA_NIC_TYPE_LIST else False
            if not self._nic_ctrl_list[slot].nic_write_fru(date, sn, mac, pn, nic_type, dpn, sku, smb_fru=smb_fru):
                self.cli_log_slot_err_lock(slot, "Program ASIC NIC FRU failed")
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False

            # for Salina cards need program cpld_fru
            if smb_fru:
                if not self._nic_ctrl_list[slot].nic_write_fru(date, sn, mac, pn, nic_type, dpn, sku, smb_fru=smb_fru, dev="cpld_fru"):
                    self.cli_log_slot_err_lock(slot, "Program ASIC NIC CPLD FRU failed")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                if not self._nic_ctrl_list[slot].nic_power_cycle():
                    self.cli_log_slot_err_lock(slot, "Failed to Power cycle after FRU program")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                if not self._nic_ctrl_list[slot].nic_read_fru(smb_fru=True, dev="cpld_fru"):
                    self.cli_log_slot_err_lock(slot, "Display SMB NIC CPLD FRU failed")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                # for Salina cpld_fru_i2c address will need to match with cpld rev
                if not self._nic_ctrl_list[slot].nic_read_fru(smb_fru=True, dev="cpld_fru_i2c"):
                    self.cli_log_slot_err_lock(slot, "Display SMB NIC CPLD I2C FRU failed")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False

            if self._nic_ctrl_list[slot].nic_2nd_fru_exist(pn):
                # for Salina cards need program SMBus FRU first, then DPU_FRU/2nd PCIe FRU, put smb_fru to False to program DPU FRU
                smb_fru = False if nic_type in SALINA_NIC_TYPE_LIST else True
                if not self._nic_ctrl_list[slot].nic_write_fru(date, sn, mac, pn, nic_type, dpn, sku, smb_fru=smb_fru):
                    self.cli_log_slot_err_lock(slot, "Program SMB NIC FRU failed")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                if nic_type in SALINA_NIC_TYPE_LIST and not self._nic_ctrl_list[slot].nic_power_cycle():
                    self.cli_log_slot_err_lock(slot, "Failed to Power cycle after FRU program")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                if not self._nic_ctrl_list[slot].nic_read_fru(smb_fru=True):
                    self.cli_log_slot_err_lock(slot, "Display SMB NIC FRU failed")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False

        if nic_type not in SALINA_NIC_TYPE_LIST + VULCANO_NIC_TYPE_LIST and not self._nic_ctrl_list[slot].nic_read_fru():
            self.cli_log_slot_err_lock(slot, "Display NIC FRU failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_program_nic_alom_fru(self, slot, date, alom_sn, alom_pn):
        self.cli_log_slot_inf_lock(slot, "Program NIC ALOM FRU date={:s}, alom_sn={:s}, alom_pn={:s}".format(date, alom_sn, alom_pn))
        if not self._nic_ctrl_list[slot].nic_program_alom_fru(date, alom_sn, alom_pn):
            self.cli_log_slot_err_lock(slot, "Program NIC ALOM FRU failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_dump_nic_fru(self, slot, expect_sn="", expect_mac="", expect_pn=""):
        if not self._nic_ctrl_list[slot].nic_dump_fru(expect_mac=expect_mac):
            self.cli_log_slot_err_lock(slot, "Dump ASIC FRU failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        if not self._nic_ctrl_list[slot].mtp_nic_dump_fru(expect_mac=expect_mac):
            self.cli_log_slot_err_lock(slot, "Dump SMB FRU failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_get_nic_fru(self, slot):
        return self._nic_ctrl_list[slot].nic_get_fru()

    def mtp_get_nic_alom_fru(self, slot):
        return self._nic_ctrl_list[slot].nic_alom_get_fru()

    def mtp_get_nic_alom_sn(self, slot):
        return self._nic_ctrl_list[slot].nic_alom_sn_get_fru()

    def mtp_verify_nic_fru(self, slot, sn, mac, pn, date, dpn=None):
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
            self.cli_log_slot_err_lock(slot, "SN Verify Failed, get {:s}, expect {:s}".format(nic_sn, sn))
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
        if dpn:
            nic_dpn = self._nic_ctrl_list[slot]._dpn
            if nic_dpn != dpn:
                self.cli_log_slot_err_lock(slot, "DPN Verify Failed, get {:s}, expect {:s}".format(nic_dpn, dpn))
                return False
        self.cli_log_slot_inf_lock(slot, "Verify NIC FRU Pass, sn={:s}, mac={:s}, pn={:s}, date={:s}".format(sn, mac, pn, date))
        if dpn:
            self.cli_log_slot_inf_lock(slot, "Verify NIC FRU Pass, dpn={:s}".format(dpn))

        return True

    def mtp_verify_hpe_pn_fru(self, slot, hpe_pn):
        got_pn = self._nic_ctrl_list[slot]._prod_num
        if not got_pn:
            return False

        if got_pn != hpe_pn:
            self.cli_log_slot_err_lock(slot, "Read HPE PN: {:s}, expect {:s}".format(got_pn, hpe_pn))
            return False

        self.cli_log_slot_inf_lock(slot, "Verify HPE PN FRU Pass, PN={:s}".format(hpe_pn))

        return True

    def mtp_verify_nic_alom_fru(self, slot, alom_sn, alom_pn, date):
        alom_fru_info = self.mtp_get_nic_alom_fru(slot)
        got_alom_sn = alom_fru_info[0]
        got_alom_pn = alom_fru_info[1]
        got_alom_date = alom_fru_info[2]

        if got_alom_sn != alom_sn:
            self.cli_log_slot_err_lock(slot, "ALOM SN Verify Failed, got {:s}, expecting {:s}".format(got_alom_sn, alom_sn))
            return False
        if got_alom_pn != alom_pn:
            self.cli_log_slot_err_lock(slot, "ALOM PN Verify Failed, got {:s}, expecting {:s}".format(got_alom_pn, alom_pn))
            return False
        if got_alom_date != alom_date:
            self.cli_log_slot_err_lock(slot, "ALOM Date Verify Failed, got {:s}, expecting {:s}".format(got_alom_date, alom_date))
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


    @parallelize.parallel_nic_using_ssh
    def mtp_nic_hpe_rework_verify(self, slot):
        """ REWORK VERIFICATION FOR CAP CHANGE 
            For NAPLES25(HPE) and NAPLES25SWM(HPE), Product Version/Revision Code must be 0B or 0x30 0x42
            With WDC flash/new heatsink/new FRU table, Product Version must be 0C
        """
        if not self._nic_ctrl_list[slot].nic_fru_init_hpe_version():
            self.mtp_get_nic_err_msg(slot)
            return False

        got_prod_ver = self._nic_ctrl_list[slot].nic_get_hpe_version()
        if not got_prod_ver:
            self.cli_log_slot_err(slot, "Failed to parse Product Version/Revision Code")
            return False

        if self._nic_ctrl_list[slot]._pn_format == PART_NUMBERS_MATCH.N25_SWM_HPE_001_PN_FMT:
            exp_prod_ver = "0B"
        else:
            exp_prod_ver = "0C"

        if got_prod_ver != exp_prod_ver:
            self.cli_log_slot_err(slot, "Looking for Product Version/Revision Code = {:s}, got {}".format(exp_prod_ver, got_prod_ver))
            return False

        return True

    def mtp_nic_program_ocp_adapter_fru(self, slot, date, sn, mac, pn):
        """
        sn  = scanned
        mac = FF:FF:FF:FF:FF (fixed)
        pn  = 73-0024-03 (fixed)
        date= generated
        """

        nic_type = self.mtp_get_nic_type(slot)

        if nic_type != NIC_Type.NAPLES25OCP:
            self.cli_log_err("This function cannot be used without an OCP card plugged in")
            return False

        self.cli_log_slot_inf_lock(slot, "Program OCP Adapter FRU date={:s}, sn={:s}, mac={:s}, pn={:s}".format(date, sn, mac, pn))
        if not self._nic_ctrl_list[slot].nic_program_ocp_adapter_fru(date, sn, mac, pn):
            self.cli_log_slot_err_lock(slot, "Program OCP Adapter FRU failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_nic_verify_ocp_adapter_fru(self, slot, exp_date, exp_sn, exp_mac, exp_pn):
        """ check programmed sn and date only. MAC and PN have no validation rules. """
        sn = self.mtp_get_nic_ocp_adapter_sn(slot)
        date = self.mtp_get_nic_ocp_adapter_progdate(slot)
        mac = exp_mac
        pn = exp_pn

        if sn != exp_sn:
            self.cli_log_slot_err_lock(slot, "SN Verify Failed, get {:s}, expect {:s}".format(sn, exp_sn))
            return False
        if date != exp_date:
            self.cli_log_slot_err_lock(slot, "Date Verify Failed, get {:s}, expect {:s}".format(date, exp_date))
            return False
        self.cli_log_slot_inf_lock(slot, "Verify NIC FRU Pass, sn={:s}, mac={:s}, pn={:s}, date={:s}".format(sn, mac, pn, date))

        return True

    # Check the SWI scanned in software part number to see if it's a cloud image or not.
    # Cloud images have slight deviation on how SWI runs
    def check_is_cloud_software_image(self, slot, software_pn):
        print(" Check if software image is cloud: {:s}".format(software_pn))
        if (software_pn == "90-0004-0001" or
                software_pn == "90-0006-0001" or
                software_pn == "90-0006-0002" or
                software_pn == "90-0011-0003" or
                software_pn == "90-0012-0001" or
                software_pn == "90-0019-0001"
            ):
            return True
        return False

    # Check if the loaded image correct for the cards p/n.  i.e. cloud card gets a cloud image,
    # and etnerprise card get an enterprise image
    def check_swi_software_image(self, slot, pn_check=True):
        naples_pn = self._nic_ctrl_list[slot].nic_get_naples_pn()
        if not naples_pn:
            self.cli_log_slot_err_lock(slot, "Check SWI Software Image: Retreive PN Failed")
            return False
        if naples_pn[0:7] == "68-0003":  # NAPLES 100 PENSANDO
            return "90-0001-0003"

        elif naples_pn[0:9] == "111-05363":  # NAPLES 100 NETAPP
            return "90-0001-0002"

        elif naples_pn[0:7] == "68-0013":  # NAPLES100 IBM
            return "90-0004-0001"

        elif naples_pn[0:6] == "P37692":  # NAPLES100 HPE
            return "90-0002-0009"

        elif naples_pn[0:6] == "P41854":  # NAPLES100 HPE CLOUD
            return "90-0006-0002"

        elif naples_pn[0:7] == "68-0024":  # NAPLES100 DELL
            return "90-0013-0001"

        elif naples_pn[0:7] == "68-0005":  # NAPLES25 PENSANDO
            return "90-0002-0003"

        elif naples_pn[0:6] == "P18669":  # NAPLES25 HPE
            return "90-0006-0001"

        elif naples_pn[0:7] == "68-0008":  # NAPLES25 EQUINIX
            return "90-0006-0001"

        elif naples_pn[0:6] == "P26968":  # NAPLES25 SWM HPE
            return "90-0002-0010"

        elif naples_pn[0:6] == "P41851":  # NAPLES25 SWM HPE CLOUD
            return "90-0006-0002"

        elif naples_pn[0:6] == "P46653":    # NAPLES25 SWM HPE TAA
            return "90-0014-0001"

        elif (naples_pn[0:7] == "68-0016") or (naples_pn[0:7] == "68-0017"):  # NAPLES25 SWM PENSANDO & TAA
            return "90-0002-0005"

        elif naples_pn[0:7] == "68-0014":  # NAPLES25 SWM DELL
            return "90-0007-0004"

        elif naples_pn[0:7] == "68-0019":  # NAPLES25 SWM 833
            return "90-0002-0007"

        elif naples_pn[0:7] == "68-0023":  # NAPLES25 OCP PENSANDO
            return "90-0002-0007"

        elif naples_pn[0:6] == "P37689":  # NAPLES25 OCP HPE
            return "90-0002-0011"

        elif naples_pn[0:6] == "P41857":  # NAPLES25 OCP HPE CLOUD
            return "90-0006-0002"

        elif naples_pn[0:7] == "68-0010":  # NAPLES25 OCP DELL
            return "90-0007-0004"

        elif ((naples_pn[0:7] == "68-0007") or (naples_pn[0:7] == "68-0009") or (naples_pn[0:7] == "68-0011")):  # FORIO/VOMERO/VOMERO2
            return "90-0003-0001"

        elif naples_pn[0:7] == "68-0015":  # ORTANO
            if pn_check and not naples_pn.endswith("C1"):
                self.cli_log_slot_err_lock(slot, "Check PN REV: Software Image match to nic part number failed")
                self.cli_log_slot_err_lock(slot, "Expected: {:s}, Got: {:s}".format(naples_pn[:PEN_PN_MINUS_REV_MASK]+" C1", naples_pn))
                return ""
            else:
                return "90-0021-0001"

        elif naples_pn[0:7] == "68-0021":  # ORTANO PENSANDO
            return "90-0019-0001"

        elif naples_pn[0:6] == "0PCFPC":  # POMONTE DELL
            return "90-0017-0003"

        elif naples_pn[0:6] in ("0X322F", "0W5WGK"):  # LACONA32 DELL
            return "90-0017-0003"

        elif naples_pn[0:6] == "P47930":  # LACONA32 HPE
            return "90-0017-0003"

        elif naples_pn[0:7] == "68-0026":  # ORTANO2 ADI ORACLE
            return "90-0021-0001"

        elif naples_pn[0:7] == "68-0028":  # ORTANO2 ADI IBM
            return "90-0016-0004"

        elif naples_pn[0:7] == "68-0034":  # ORTANO2 ADI MICROSOFT
            return "90-0019-0002"

        elif naples_pn[0:7] == "68-0029":  # ORTANO2 INTERPOSER
            return "90-0021-0001"

        elif naples_pn[0:7] == "68-0077":  # ORTANO2 SOLO
            return "90-0021-0002"

        elif naples_pn[0:7] == "68-0095":  # ORTANO2 SOLO-L
            return "90-0021-0002"

        elif naples_pn[0:7] == "68-0089":  # ORTANO2 SOLO Tall Heat Sink
            return "90-0021-0002"

        elif naples_pn[0:7] == "68-0090":  # ORTANO2 SOLO MICROSOFT
            return "90-0019-0002"

        elif naples_pn[0:7] == "68-0092":  # ORTANO2 (ADI CR/ SOLO) S4
            return "90-0022-0001"

        elif naples_pn[0:7] == "68-0049":  # ORTANO2 ADI CR
            return "90-0021-0002"

        elif naples_pn[0:7] == "68-0091":  # ORTANO2 ADI CR MICROSOFT
            return "90-0019-0002"

        elif naples_pn[0:7] == "68-0074":  # GINESTRA_D4
            return "90-0023-0001"

        elif naples_pn[0:7] == "68-0075":  # GINESTRA_D5
            return "90-0023-0002"

        elif naples_pn[0:7] == "68-0076":     #GINESTRA_S4
            return "90-0023-0003"

        elif naples_pn[0:7] == "68-0094":     #GINESTRA_CIS
            return "90-0023-0005"

        else:
            self.cli_log_slot_err_lock(slot, "check_swi_software_image Unknown Part Number {:s} !!".format(naples_pn))
            return ""

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_sw_pn_search(self, slot, sw_pn_list, check_naples_pn):
        """ for each slot, match it to one of the SW PNs; fail slot if no match """
        for sw_pn in sw_pn_list:
            if not self.check_swi_software_image(slot, sw_pn, check_naples_pn):
                continue
            else:
                self.mtp_set_nic_sw_pn(slot, sw_pn)
                break
        # search exhausted
        if not self.mtp_get_nic_sw_pn(slot):
            self.cli_log_slot_err(slot, "No correct SW PN supplied")
            return False
        else:
            return True

    def mtp_get_alom_fru(self, slot):
        return self._nic_ctrl_list[slot].alom_get_fru()

    @parallelize.parallel_nic_using_console
    def mtp_setting_partition(self, slot):
        # copy script to detect the emmc part size
        if not self._nic_ctrl_list[slot].nic_copy_image("{:s}diag/scripts/emmc_format.sh".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)):
            self.cli_log_slot_err_lock(slot, "Failed to copy emmc format script")
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

    @parallelize.parallel_nic_using_console
    def mtp_nic_emmc_bkops_en(self, slot):
        # copy script to detect the emmc part size
        if not self._nic_ctrl_list[slot].nic_copy_image("{:s}nic_util/mmc.latest".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_DIAG_PATH)):
            self.cli_log_slot_err_lock(slot, "Failed to copy emmc util")
            return False
        if not self._nic_ctrl_list[slot].nic_emmc_bkops_verify():
            self.mtp_clear_nic_err_msg(slot)  # clear out the error message
            if not self._nic_ctrl_list[slot].nic_emmc_bkops_en():
                self.cli_log_slot_err_lock(slot, "Failed to enable eMMC bkops")
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_emmc_bkops_verify():
                self.cli_log_slot_err_lock(slot, "Incorrect eMMC bkops value reflected")
                self.mtp_get_nic_err_msg(slot)
                return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_fwupdate_init_emmc(self, slot, mount=True):

        if not self._nic_ctrl_list[slot].nic_fwupdate_init_emmc(mount):
            self.mtp_clear_nic_err_msg(slot)
            if not self._nic_ctrl_list[slot].nic_emmc_bkops_en():
                self.cli_log_slot_err_lock(slot, "Fwupdate failed to init eMMC")
                self.mtp_dump_nic_err_msg(slot)
                return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_emmc_hwreset_set(self, slot):
        if not self._nic_ctrl_list[slot].nic_emmc_hwreset_verify():
            self.mtp_clear_nic_err_msg(slot)  # clear out the error message
            if not self._nic_ctrl_list[slot].nic_emmc_hwreset_set():
                self.cli_log_slot_err_lock(slot, "Failed to enable eMMC hwreset setting")
                self.mtp_dump_nic_err_msg(slot)
                return False
            if not self._nic_ctrl_list[slot].nic_emmc_hwreset_verify():
                self.cli_log_slot_err_lock(slot, "Incorrect eMMC hwreset setting reflected")
                self.mtp_get_nic_err_msg(slot)
                return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_set_nic_diagfw_boot(self, slot):
        if not self._nic_ctrl_list[slot].set_nic_diagfw_boot():
            self.cli_log_slot_err(slot, "Set boot diagfw failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set boot diagfw")
        self._nic_ctrl_list[slot].nic_boot_info_reset()
        return True

    @parallelize.parallel_nic_using_console
    def mtp_vulcano_reset_code_status(self, slot):
        self._mtp_type = MTP_TYPE.PANAREA
        if self._mtp_type != MTP_TYPE.PANAREA:
            return True
        if not self._nic_ctrl_list[slot].nic_vulcano_reset_code():
            self.cli_log_slot_err(slot, "Retrieve reset code failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Retrieve reset code")
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_vulcano_fpga_uart_stats_dump(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in VULCANO_NIC_TYPE_LIST:
            return True
        if not self._nic_ctrl_list[slot].nic_vulcano_fpga_uart_stats_dump():
            self.cli_log_slot_err(slot, "dump fpga uart stats failed")
            self.mtp_get_nic_err_msg(slot)
            return False
        return True

    def mtp_program_nic_adi_ibm_cpld(self, slot, cpld_img, dl_step=True):
        # check the current cpld version
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type != NIC_Type.ORTANO2ADIIBM:
            self.cli_log_slot_err(slot, "This cpld update function not meant for this card {:s}".format(nic_type))
            return False

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "cfg0"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_adi_ibm_failsafe_cpld(self, slot, cpld_img):
        # check the current cpld version
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type != NIC_Type.ORTANO2ADIIBM:
            self.cli_log_slot_err(slot, "This failsafe cpld update function not meant for this card {:s}".format(nic_type))
            return False

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "cfg1"):
            self.cli_log_slot_err_lock(slot, "Program NIC Failsafe CPLD failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_cpld(self, slot, cpld_img, dl_step=True):
        # check the current cpld version
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type in FPGA_TYPE_LIST:
            self.cli_log_slot_err(slot, "This cpld update function not meant for this card {:s}".format(nic_type))
            return False

        if dl_step:
            stage = FF_Stage.FF_DL
        else:
            stage = FF_Stage.FF_SWI

        if nic_type not in SALINA_NIC_TYPE_LIST:
            nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
            if not nic_cpld_info:
                self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed, can not retrieve CPLD info")
                return False
            cur_ver = nic_cpld_info[0]
            cur_timestamp = nic_cpld_info[1]

            expected_version = image_control.get_cpld(self, slot, stage)["version"]
            expected_timestamp = image_control.get_cpld(self, slot, stage)["timestamp"]

            if nic_type in self._proto_type_list:
                self.cli_log_slot_inf_lock(slot, "Skip CPLD update for Proto NIC")
                return True

            if cur_ver == expected_version and cur_timestamp == expected_timestamp:
                self.cli_log_slot_inf_lock(slot, "NIC CPLD is up-to-date, But Program Again")

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "cfg0"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        self._nic_ctrl_list[slot].nic_require_cpld_refresh(True)

        return True

    def mtp_program_nic_failsafe_cpld(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST and nic_type not in SALINA_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no failsafe CPLD for {:s}".format(nic_type))
            return False
        if nic_type in FPGA_TYPE_LIST:
            self.cli_log_slot_err(slot, "This function not support for this NIC type!")
            return False
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip failsafe CPLD update for Proto NIC")
            return True

        if nic_type in ELBA_NIC_TYPE_LIST and nic_type not in (FPGA_TYPE_LIST + [NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4]):
            # can't check the version without loading backup partition into the running partition
            self.cli_log_slot_inf(slot, "Skip checking failsafe CPLD version")

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "cfg1"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_ufm1(self, slot, ufm1_img):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in SALINA_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no ufm1 image for {:s}".format(nic_type))
            return False

        if not self._nic_ctrl_list[slot].nic_program_cpld(ufm1_img, "ufm1"):
            self.cli_log_slot_err_lock(slot, "Program NIC UFM1 failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_ufm1_cfg0(self, slot, ufm1_img, cfg0_img_file):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in SALINA_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no ufm1 image for {:s}".format(nic_type))
            return False

        combin_with = dict()
        combin_with["cfg0"] = cfg0_img_file
        if not self._nic_ctrl_list[slot].nic_program_cpld(ufm1_img, "ufm1", combin_with):
            self.cli_log_slot_err_lock(slot, "Program NIC UFM1_CFG0 failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_program_nic_fpga(self, slot, partition_list=None, alternate_image_list=None):
        """
        This sequence has to be followed:
        # cpldapp -writeflash ./lac2_dell_golden_2_3.bin cfg1
        # cpldapp -writeflash ./timer1.bin cfg2
        # cpldapp -writeflash ./lac2_dell_main_2_3.bin
        # cpldapp -writeflash ./timer2.bin cfg3

        or (in FW older than E-24)

        ./artix7fpga -prog ${part_number}_gold.bin gold
        ./artix7fpga -prog timer1.bin timer1
        ./artix7fpga -prog ${part_number}_main.bin main
        ./artix7fpga -prog timer2.bin timer2
        """
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type not in FPGA_TYPE_LIST:
            self.cli_log_slot_err(slot, "This fpga program function not supported for this NIC type!")
            return False

        # Dont skip programming the image right now
        # # check the current cpld version
        # nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        # if not nic_cpld_info:
        #     self.cli_log_slot_err_lock(slot, "Program NIC FPGA failed, can not retrieve FPGA revision info")
        #     return False
        # cur_ver = nic_cpld_info[0]
        # cur_timestamp = nic_cpld_info[1]
        # expected_version   = image_control.get_cpld(self, slot, stage)["version"]
        # expected_timestamp = image_control.get_cpld(self, slot, stage)["timestamp"]

        # if nic_type in self._proto_type_list:
        #     self.cli_log_slot_inf_lock(slot, "Skip CPLD update for Proto NIC")
        #     return True

        # if cur_ver == expected_version and cur_timestamp == expected_timestamp:
        #     self.cli_log_slot_inf_lock(slot, "NIC FPGA is up-to-date")
        #     self._nic_ctrl_list[slot].nic_require_cpld_refresh(False)
        #     return True

        partition_img_dict = {
            "cfg0": image_control.get_cpld(self, slot, FF_Stage.FF_DL)["filename"],
            "cfg1": image_control.get_fail_cpld(self, slot, FF_Stage.FF_DL)["filename"],
            "cfg2": image_control.get_timer1(self, slot, FF_Stage.FF_DL)["filename"],
            "cfg3": image_control.get_timer2(self, slot, FF_Stage.FF_DL)["filename"]
        }
        program_sequence = ["cfg1", "cfg2", "cfg0", "cfg3"]

        if partition_list is not None:
            program_sequence = partition_list
            if alternate_image_list is not None:
                for prt, img in zip(partition_list, alternate_image_list):
                    partition_img_dict[prt] = img

        for partition in program_sequence:
            img = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + partition_img_dict[partition]
            if not self._nic_ctrl_list[slot].nic_program_cpld(img, partition):
                self.cli_log_slot_err_lock(slot, "Program NIC FPGA to partition {:s} failed".format(partition))
                self.mtp_dump_nic_err_msg(slot)
                return False

        self._nic_ctrl_list[slot].nic_require_cpld_refresh(True)

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_verify_nic_fpga(self, slot, main_only=False):
        """
        Following the same partition sequence as writing:
        # cpldapp -verifyflash ./lac2_dell_golden_2_3.bin cfg1
        # cpldapp -verifyflash ./timer1.bin cfg2
        # cpldapp -verifyflash ./lac2_dell_main_2_3.bin
        # cpldapp -verifyflash ./timer2.bin cfg3
        """
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type not in FPGA_TYPE_LIST:
            self.cli_log_slot_err(slot, "This fpga verify function not support for this NIC type!")
            return False

        partition_img_dict = {
            "cfg0": image_control.get_cpld(self, slot, FF_Stage.FF_DL)["filename"],
            "cfg1": image_control.get_fail_cpld(self, slot, FF_Stage.FF_DL)["filename"],
            "cfg2": image_control.get_timer1(self, slot, FF_Stage.FF_DL)["filename"],
            "cfg3": image_control.get_timer2(self, slot, FF_Stage.FF_DL)["filename"]
        }
        if not main_only:
            program_sequence = ["cfg1", "cfg2", "cfg0", "cfg3"]
        else:
            program_sequence = ["cfg0"]
        for partition in program_sequence:
            img = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + partition_img_dict[partition]
            if not self._nic_ctrl_list[slot].nic_verify_fpga(img, partition):
                self.cli_log_slot_err_lock(slot, "Verify NIC FPGA from partition {:s} failed".format(partition))
                self.mtp_get_nic_err_msg(slot)
                self.mtp_dump_nic_err_msg(slot)
                return False

        return True

    def mtp_program_nic_cpld_feature_row(self, slot, cpld_img):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST + FPGA_TYPE_LIST + GIGLIO_NIC_TYPE_LIST + SALINA_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no feature row for {:s}".format(nic_type))
            return False
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "No feature row update for Proto NIC")
            return True

        cpld_img = "/home/diag/"+image_control.get_fea_cpld(self, slot, FF_Stage.FF_DL)["filename"]

        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img, "fea"):
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD feature row failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_refresh_nic_cpld(self, slot, dontwait=False):
        if not self._nic_ctrl_list[slot].nic_is_cpld_refresh_required():
            self.cli_log_slot_inf_lock(slot, "No CPLD refresh needed")
            return True

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

        self._nic_ctrl_list[slot].nic_require_cpld_refresh(True)
        if not self._nic_ctrl_list[slot].nic_program_cpld(cpld_img):
            self.cli_log_slot_err_lock(slot, "Program NIC Secure CPLD failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_console
    def mtp_verify_nic_sec_cpld(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Secure CPLD verify for Proto NIC")
            return True

        if nic_type not in CAPRI_NIC_TYPE_LIST:
            if not self._nic_ctrl_list[slot].nic_dump_esec_qspi(libmfg_utils.get_mode_param(self, slot, "SEC_PROG_VERIFY")):
                self.cli_log_slot_err(slot, "Dumping esec failed")
                return False

        if not self._nic_ctrl_list[slot].nic_verify_sec_cpld():
            self.cli_log_slot_err(slot, "Verify NIC Secure CPLD failed")
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_verify_nic_cpld_fea(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no feature row for {:s}".format(nic_type))
            return False

        fea_regex = r"00000000  (.*)  \|.*\|"  # first 16 bytes

        cmd = "hexdump -C /home/diag/"+image_control.get_fea_cpld(self, slot, FF_Stage.FF_DL)["filename"]
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False
        fea_mtp_hex = self.mtp_get_cmd_buf()
        fea_mtp_match = re.search(fea_regex, fea_mtp_hex)

        if not self._nic_ctrl_list[slot].nic_dump_cpld("fea"):
            self.mtp_dump_nic_err_msg(slot)
            return False

        fea_nic_hex = self._nic_ctrl_list[slot].nic_get_info("hexdump -C /home/diag/cplddump")
        if not fea_nic_hex:
            self.mtp_dump_nic_err_msg(slot)
            return False
        fea_nic_match = re.search(fea_regex, fea_nic_hex)

        if fea_mtp_match and fea_nic_match:
            if fea_mtp_match.group(1) == fea_nic_match.group(1):
                return True
            self.cli_log_slot_err_lock(slot, "Feature row programmed incorrectly. Dump doesn't match original file.")
            return False
        self.cli_log_slot_err_lock(slot, "Unable to dump feature row.")
        return False

    @parallelize.parallel_nic_using_ssh
    def mtp_verify_nic_cpld_fea_salina(self, slot, binary_fea_file):
        """
        For Salina CPLD Feature row verify only.
        """

        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST  + FPGA_TYPE_LIST + GIGLIO_NIC_TYPE_LIST + SALINA_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: there is no feature row for {:s}".format(nic_type))
            return False

        fea_regex = r"00000000  (.*)  \|.*\|"  # first 16 bytes

        cmd = "hexdump -C " + binary_fea_file
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False
        fea_mtp_hex = self.mtp_get_nic_cmd_buf(slot)
        fea_mtp_match = re.search(fea_regex, fea_mtp_hex)

        cmd = MFG_DIAG_CMDS().MTP_MATERA_FPGAUTIL_CPLD_CMD_FMT.format(str(slot +1), "generate", "fea", "/home/diag/cpld_fea_dump_slot" + str(slot +1) + ".bin")
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        cmd = "hexdump -C " + "/home/diag/cpld_fea_dump_slot" + str(slot +1) + ".bin"
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False
        fea_nic_hex = self.mtp_get_nic_cmd_buf(slot)
        if not fea_nic_hex:
            self.mtp_dump_nic_err_msg(slot)
            return False
        fea_nic_match = re.search(fea_regex, fea_nic_hex)

        if fea_mtp_match and fea_nic_match:
            if fea_mtp_match.group(1) == fea_nic_match.group(1):
                if not self.mtp_power_on_nic([slot]):
                    return False
                return True
            self.cli_log_slot_err_lock(slot, "Feature row programmed incorrectly. Dump doesn't match original file.")
            return False
        self.cli_log_slot_err_lock(slot, "Unable to dump feature row.")

        return False

    def matera_mtp_fpgauti_cpld_fea_jed2bin(self, cpld_fea_jed_file):
        """
        single mtp session run only once command
        Since the released salina CPLD feature row file salina.fea is jed file, we need call fpgauti to covert it to a binary file
        Then compare with dumped running feature row file.
        """

        # before Andrew's update of fpgautil ready, we need fake a slot id
        # Turn off slots to avoid program fea, we just using program function to covert jed file to binary file
        # pick last slot as fake one to run this command
        slot = [9]
        if not self.mtp_power_off_nic(slot):
            return False
        cmd = MFG_DIAG_CMDS().MTP_MATERA_FPGAUTIL_CPLD_CMD_FMT.format(str(slot[0]+1), "program", "fea", cpld_fea_jed_file)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False
        output = self.mtp_get_cmd_buf()
        match_obj = re.search(r'BIN FILENAME\s* =\s*(.*\.bin)', output)
        if not match_obj:
            self.cli_log_err("Failed to parse salina jed to bin file")
            return False
        binary_fea_file =  match_obj.group(1)
        if not self.mtp_power_on_nic(slot):
            return False
        return binary_fea_file

    def mtp_check_nic_cpld_partition(self, slot, console=False):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
            # No cpld partition bit
            return True

        self.cli_log_slot_inf(slot, "Check CPLD partition")
        if not self._nic_ctrl_list[slot].nic_check_cpld_partition(console):
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_verify_cpld_feature_row(self, slot, fea_cpld_img_file):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in SALINA_NIC_TYPE_LIST:
            self.cli_log_slot_err_lock(slot, "Should not be here: this only support salina fea image, not {:s}".format(nic_type))
            return False

        if not self._nic_ctrl_list[slot].nic_verify_cpld_feature_row(fea_cpld_img_file):
            self.cli_log_slot_err_lock(slot, "Verify NIC CPLD FEA image failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_recover_nic_console(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in FPGA_TYPE_LIST:
            self.cli_log_slot_err(slot, "Not applicable for this NIC")
            return False

        self.cli_log_slot_inf(slot, "Recover NIC console")
        if not self._nic_ctrl_list[slot].nic_recover_console():
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_console
    def mtp_program_nic_efuse(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST + SALINA_NIC_TYPE_LIST:
            return False

        if not self._nic_ctrl_list[slot].nic_program_efuse():
            self.cli_log_slot_err(slot, "Program NIC Efuse failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    @parallelize.sequential_nic_test
    def mtp_program_nic_sec_key(self, slot, skip_hmac_list=[]):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Secure Key program for Proto NIC")
            return True

        if nic_type in SALINA_NIC_TYPE_LIST:
            if not self._nic_ctrl_list[slot].nic_salina_clear_j2c():
                self.cli_log_slot_err(slot, "Pre init clear j2c failed")
                return False

        if not self._nic_ctrl_list[slot].nic_program_sec_key_pre():
            self.cli_log_slot_err(slot, "Pre init key programming failed")
            self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        if nic_type in SALINA_NIC_TYPE_LIST:
            # Salina require power cycle
            self.mtp_power_cycle_nic(slot, dl=False)

        if not self._nic_ctrl_list[slot].nic_program_sec_key(self._id):
            self.cli_log_slot_err(slot, "Program NIC Secure Key failed")
            if nic_type not in SALINA_NIC_TYPE_LIST: self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        if nic_type in SALINA_NIC_TYPE_LIST:
            if not self._nic_ctrl_list[slot].nic_program_dice_sec_key():
                self.cli_log_slot_err(slot, "Program NIC Dice Program failed")
                return False

            if not self._nic_ctrl_list[slot].nic_program_dice_img_sec_key():
                self.cli_log_slot_err(slot, "Program NIC Dice Image Program failed")
                return False

            if not self._nic_ctrl_list[slot].nic_check_uboot_sec_key():
                self.cli_log_slot_err(slot, "Program NIC check Uboot failed")
                return False

            if nic_type in SALINA_AI_NIC_TYPE_LIST:
                image_path = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_qspi_prog_secure_sh_img(self, slot, FF_Stage.FF_SWI)["filename"]
                if not self.matera_mtp_program_nic_qspi(slot, image_path, img_type="secure"):
                    self.cli_log_slot_err(slot, "Program NIC secure qspi imgage failed")
                    return False

            if not self._nic_ctrl_list[slot].nic_check_uds_cert():
                self.cli_log_slot_err(slot, "Program NIC check UDS cert failed")
                return False

            if SALINA_HMAC_PROGRAM_ENABLE:
                if slot not in skip_hmac_list and not self._nic_ctrl_list[slot].nic_hmac_fuse_prog():
                    self.cli_log_slot_err(slot, "Program HMAC fuse failed")
                    return False

                if slot not in skip_hmac_list and not self._nic_ctrl_list[slot].nic_val_uds_cert():
                    self.cli_log_slot_err(slot, "Check NIC UDS cert failed")
                    return False

        if not self._nic_ctrl_list[slot].nic_program_sec_key_post():
            self.cli_log_slot_err(slot, "Post cleanup key programming failed")
            if nic_type not in SALINA_NIC_TYPE_LIST: self._nic_ctrl_list[slot].nic_program_sec_key_dump()
            return False

        return True

    @parallelize.sequential_nic_test
    def mtp_nic_esecure_hw_unlock(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Secure Key program for Proto NIC")
            return True

        if nic_type in SALINA_NIC_TYPE_LIST:
            if not self._nic_ctrl_list[slot].nic_salina_clear_j2c():
                self.cli_log_slot_err(slot, "Pre init clear j2c failed")
                return False

            if not self._nic_ctrl_list[slot].nic_esecure_hw_unlock():
                self.cli_log_slot_err(slot, "Esecure hw unlock failed")
                return False

        return True

    @parallelize.sequential_nic_test
    def mtp_nic_hmac_programmed_status_check(self, slot, expect_status, stage=FF_Stage.FF_DL):
        """
        call ./esec_ctrl.py -hmac_fuse_prog -slot $slo -hmac_file check_only
        'HMAC HAS BEEN PROGRAMMED' or 'HMAC HAS NOT BEEN PROGRAMMED'
        """

        if not self._nic_ctrl_list[slot].nic_salina_clear_j2c():
            self.cli_log_slot_err(slot, "Pre init clear j2c failed")
            return False

        if not self._nic_ctrl_list[slot].nic_hmac_program_status_check(expect_status, stage):
            self.cli_log_slot_err(slot, "HMAC PROGRAMMED STATUS Check Failed, Expected Status String: '{:s}' NOT Found".format(expect_status))
            return False

        return True

    @parallelize.sequential_nic_test_category
    def mtp_nic_hmac_programmed_category(self, slot, stage=FF_Stage.FF_DL):
        """
        call ./esec_ctrl.py -hmac_fuse_prog -slot $slo -hmac_file check_only
        'HMAC HAS BEEN PROGRAMMED' or 'HMAC HAS NOT BEEN PROGRAMMED'
        """

        if not self._nic_ctrl_list[slot].nic_salina_clear_j2c():
            self.cli_log_slot_err(slot, "Pre init clear j2c failed")
            return -1

        ret = self._nic_ctrl_list[slot].nic_hmac_program_category(stage)
        if ret < 0:
            self.cli_log_slot_err(slot, "HMAC PROGRAMMED STATUS Check Failed, Expected Status String List NOT Found")
            return -1

        return ret

    @parallelize.sequential_nic_test_category
    def mtp_nic_val_uds_cert_category(self, slot, stage=FF_Stage.FF_DL):
        """
        call ./esec_ctrl.py -val_uds_cert -slot -slot $slot
        'DICE VALIDATION PASSED'
       """

        if not self._nic_ctrl_list[slot].nic_salina_clear_j2c():
            self.cli_log_slot_err(slot, "Pre init clear j2c failed")
            return -1

        ret = self._nic_ctrl_list[slot].nic_val_uds_cert_category(stage)
        if ret < 0:
            self.cli_log_slot_err(slot, "NIC validate UDS cert failed")
            return -1

        return ret

    @parallelize.sequential_nic_test
    def mtp_nic_val_uds_cert(self, slot):
        """
        call ./esec_ctrl.py -val_uds_cert -slot -slot $slot
        'DICE VALIDATION PASSED'
        """

        if not self._nic_ctrl_list[slot].nic_salina_clear_j2c():
            self.cli_log_slot_err(slot, "Pre init clear j2c failed")
            return False

        if not self._nic_ctrl_list[slot].nic_val_uds_cert():
            self.cli_log_slot_err(slot, "NIC validate UDS cert failed")
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_verify_nic_cpld(self, slot, sec_cpld=False, timestamp_check=True, dl_step=True, console=False):
        # cpld_has_timestamp = 1
        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err(slot, "Verify NIC CPLD failed, can not retrieve CPLD info")
            return False

        cur_ver = nic_cpld_info[0]
        cur_timestamp = nic_cpld_info[1]
        nic_type = self.mtp_get_nic_type(slot)

        if dl_step:
            stage = FF_Stage.FF_DL
        else:
            stage = FF_Stage.FF_SWI
        expected_version = image_control.get_cpld(self, slot, stage)["version"]
        expected_timestamp = image_control.get_cpld(self, slot, stage)["timestamp"]
        if sec_cpld:
            expected_version = image_control.get_sec_cpld(self, slot, stage)["version"]
            expected_timestamp = image_control.get_sec_cpld(self, slot, stage)["timestamp"]

        if cur_ver != expected_version or (timestamp_check and cur_timestamp != expected_timestamp):
            self.cli_log_slot_err_lock(slot, "Verify NIC CPLD Failed")
            self.cli_log_slot_err_lock(slot, "Expect Version: {:s}, get: {:s}".format(expected_version, cur_ver))
            self.cli_log_slot_err_lock(slot, "Expect Timestamp: {:s}, get: {:s}".format(expected_timestamp, cur_timestamp))
            return False

        if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            if not self._nic_ctrl_list[slot].nic_check_cpld_partition(console):
                self.cli_log_slot_err(slot, "NIC not booted from cfg0 CPLD/FPGA")
                self.mtp_dump_nic_err_msg(slot)
                return False

        return True

    @parallelize.parallel_nic_using_console
    def mtp_verify_nic_cpld_console(self, slot, sec_cpld=False, timestamp_check=True, dl_step=True):
        if slot in self.mtp_verify_nic_cpld(slot, sec_cpld, timestamp_check, dl_step, console=True):
            return False
        return True

    def mtp_program_nic_qspi(self, slot, qspi_img, force_update=True):
        if not force_update:
            # check for the desired qspi version
            if not self.mtp_verify_nic_qspi(slot):
                pass
            else:
                self.cli_log_slot_inf_lock(slot, "NIC QSPI is up-to-date")
                return True
        if not self._nic_ctrl_list[slot].nic_program_qspi(qspi_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC QSPI failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def matera_mtp_program_nic_qspi(self, slot, image_path, img_type="standalone"):
        if not self._nic_ctrl_list[slot].salina_nic_program_qspi(image_path, img_type):
            self.cli_log_slot_inf_lock(slot, "Program NIC QSPI failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def matera_mtp_erase_nic_qspi(self, slot):
        if not self._nic_ctrl_list[slot].salina_nic_erase_qspi():
            self.cli_log_slot_err_lock(slot, "Erase NIC QSPI failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def matera_mtp_dump_nic_boot(self, slot):
        if not self._nic_ctrl_list[slot].salina_nic_dump_boot():
            self.cli_log_slot_err_lock(slot, "Dumo NIC boot failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def matera_mtp_erase_nic_boot0(self, slot, image_path):
        if not self._nic_ctrl_list[slot].salina_nic_erase_boot0(image_path):
            self.cli_log_slot_inf_lock(slot, "Erase NIC Boot0 failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def matera_mtp_program_nic_boot0(self, slot, image_path):
        if not self._nic_ctrl_list[slot].salina_nic_program_boot0(image_path):
            self.cli_log_slot_inf_lock(slot, "Program NIC Boot0 failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_clear_pre_uboot_section(self, slot):
        if not self._nic_ctrl_list[slot].nic_clear_pre_uboot_section():
            self.cli_log_slot_err(slot, "erase pre-uboot section test failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    def mtp_copy_nic_cert(self, slot, cert_img, directory="/data/"):
        if not self._nic_ctrl_list[slot].nic_copy_cert(cert_img, directory):
            self.cli_log_slot_inf_lock(slot, "Copy NIC cert failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_copy_nic_gold(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_copy_gold(gold_img):
            self.cli_log_slot_inf_lock(slot, "Copy NIC goldfw failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_compare_nic_cpld_img(self, slot, cpld_img, partition):
        if not self._nic_ctrl_list[slot].nic_copy_cpld_img(cpld_img):
            self.cli_log_slot_inf_lock(slot, "Copy NIC cpld image failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        dump_cpld_image_path = "/tmp_{:s}_cpld_image.bin".format(partition)
        if not self._nic_ctrl_list[slot].nic_dump_cpld(partition, file_path=dump_cpld_image_path):
            self.cli_log_slot_inf_lock(slot, "Dump NIC cpld image failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        if not self._nic_ctrl_list[slot].nic_compare_cpld_file(cpld_img, dump_cpld_image_path, partition):
            self.cli_log_slot_inf_lock(slot, "Compare NIC cpld image failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_program_nic_gold(self, slot, gold_img):
        if not self._nic_ctrl_list[slot].nic_program_gold(gold_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC goldfw failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        if not self.mtp_mgmt_set_nic_gold_boot(slot):
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            return False

        return True

    def mtp_program_nic_uboot(self, slot, uboot_img=MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"boot0.rev7.img", installer=MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"install_file", uboot_pat="boot0", ubootg_img=""):
        if not self._nic_ctrl_list[slot].nic_program_uboot(uboot_img, installer, uboot_pat, ubootg_img):
            self.cli_log_slot_inf_lock(slot, "Program NIC uboot failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_erase_main_fw_partition(self, slot):
        if not self._nic_ctrl_list[slot].nic_erase_main_fw_partition():
            self.cli_log_slot_inf_lock(slot, "Erase mainfw failed")
            self.mtp_dump_nic_err_msg(slot)
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
        expected_timestamp = image_control.get_diagfw(self, slot, FF_Stage.FF_DL)["timestamp"]
        if (boot_image != "diagfw"):
            self.cli_log_slot_err_lock(slot, "Checking Boot Image is Diagfw Failed, NIC is booted from {:s}".format(boot_image))
            return False

        if (expected_timestamp != kernel_timestamp):
            self.cli_log_slot_err_lock(slot, "Diagfw Verify Failed, Expect: {:s}   Read: {:s}".format(expected_timestamp, kernel_timestamp))
            return False

        # additional: check has correct uboot
        if nic_type in (NIC_Type.ORTANO2) or nic_type in FPGA_TYPE_LIST:
            self.mtp_nic_console_lock()
            if not self._nic_ctrl_list[slot].nic_console_read_uboot():
                self.mtp_nic_console_unlock()
                self.mtp_get_nic_err_msg(slot)
                self.cli_log_slot_inf(slot, "Uboot update needed")
                if not GLB_CFG_MFG_TEST_MODE:
                    self.cli_log_slot_err(slot, self.mtp_dump_nic_err_msg(slot))
                return False
            self.mtp_nic_console_unlock()
            self.cli_log_slot_inf(slot, "Uboot is OK - no update needed")

        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_read_secure_boot_keys(self, slot):
        if not self._nic_ctrl_list[slot].nic_console_read_secure_boot_keys():
            self.mtp_get_nic_err_msg(slot)
            if not GLB_CFG_MFG_TEST_MODE:
                self.cli_log_slot_err(slot, self.mtp_dump_nic_err_msg(slot))
            return False
        self.cli_log_slot_inf(slot, "Uboot is OK - no update needed")
        return True

    def mtp_copy_nic_file(self, slot, filename, directory="/data/"):
        if not self._nic_ctrl_list[slot].nic_copy_image(filename, directory):
            self.cli_log_slot_inf_lock(slot, "Copy File {:s} to NIC {:d} {:s} Failed".format(filename, slot, directory))
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
            self.mtp_dump_nic_err_msg(slot)
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


    def mtp_mgmt_setup_nic_diag(self, slot, nic_utils=False):
        if nic_utils:
            msg = "Copy and Setup NIC Diag Image"
        else:
            msg = "Setup NIC Diag Image"
        self.cli_log_slot_inf_lock(slot, msg)

        nic_diag_image = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + MFG_IMAGE_FILES.MTP_ARM64_IMAGE

        if not self._nic_ctrl_list[slot].nic_setup_diag_img(nic_diag_image, "", nic_utils):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_set_nic_status_fail(slot)
            return False

        return True

    def mtp_mgmt_save_nic_logfile(self, slot, logfile_list):
        self.cli_log_slot_inf(slot, "Collecting NIC tclsh logfiles")
        if not self._nic_ctrl_list[slot].nic_save_logfile(logfile_list):
            self.cli_log_slot_err_lock(slot, "Save NIC Logfile failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_mgmt_save_nic_diag_logfile(self, slot, aapl):
        self.cli_log_slot_inf(slot, "Collecting NIC diag logfiles")
        if not self._nic_ctrl_list[slot].nic_save_diag_logfile(aapl):
            self.cli_log_slot_err_lock(slot, "Save NIC Diag Logfile failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        # self.mtp_mgmt_nic_diag_sys_clean()

        return True

    def mtp_post_dsp_fail_steps(self, slot, test, rslt, rslt_cmd_buf, err_msg_list, skip_vrm_check=None, stage=""):
        """
        1. ping slot with 10 packets        <= whether management port is down
        2. connect console and do "env"     <= Check if card rebooted
        3. inventory -sts -slot <>          <= Clue of reboot reason/power/clk
        """
        ret = True
        dsp_timeout_sig = "_NOT_ a live card: NIC"
        nic_type = self.mtp_get_nic_type(slot)

        # if rslt == "TIMEOUT":
        # if dsp_timeout_sig in rslt_cmd_buf:
        self.cli_log_slot_err(slot, "Performing post DSP {:s} fail steps".format(test))
        self.log_nic_file(slot, "#######= {:s} =#######".format("START post dsp {:s} fail debug".format(test)))

        powered_on = self.mtp_mgmt_check_nic_pwr_status(slot, test)

        # dump cpld status bits
        if not self.mtp_mgmt_set_nic_avs_post(slot):
            ret = False

        # ping test (try twice) only for DPU card
        if nic_type  not in SALINA_AI_NIC_TYPE_LIST + VULCANO_NIC_TYPE_LIST:
            ipaddr = libmfg_utils.get_nic_ip_addr(slot)
            for x in range(2):
                self.cli_log_slot_inf(slot, "Ping NIC MGMT port <{:d}> try".format(x+1))
                time.sleep(5)
                cmd = "ping -c 10 {:s}".format(ipaddr)
                if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                    ret = False

        # check if card rebooted, but not valid for bash mvl tests
        if "ACC" not in test and "STUB" not in test and test != "L1":
            self.mtp_nic_console_lock()
            if not self.mtp_check_nic_rebooted(slot):
                ret = False
            self.mtp_nic_console_unlock()

        # VRM check in get_nic_sts causes a reboot.
        # so skip it for all dsp tests where we need to keep card state.
        # can skip it for tests that have powercycle right after, such as all nic_test.py tests in mtp_para.
        if skip_vrm_check is None:
            skip_vrm_check = True

        # check ECC for elba cards
        # dont check ECC after L1 test
        # or if ddr_bist is offloaded from L1, check ecc after L1 but dont check ecc after DDR_BIST
        if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            if nic_type in CONSOLE_DDR_BIST_NIC_LIST and "DDR_BIST" in test:
                pass
            elif test in ("L1"):
                pass
            else:
                self.mtp_single_j2c_lock()
                self.mtp_nic_console_lock()
                self.mtp_get_nic_sts(slot, skip_vrm_check, test)
                self.mtp_sal_check_j2c(slot, test)
                self.mtp_nic_console_unlock()
                self.mtp_single_j2c_unlock()

        # For Salina Cards run get_nic_sts.tcl for every failure
        if nic_type in SALINA_NIC_TYPE_LIST + VULCANO_NIC_TYPE_LIST:
            self.mtp_single_j2c_lock()
            self.mtp_nic_console_lock()
            self.mtp_nic_dump_reg(slot)
            if self.mtp_get_nic_type(slot) in VULCANO_NIC_TYPE_LIST:
                self.mtp_vulcano_fpga_uart_stats_dump(slot)
            self.mtp_get_nic_sts(slot, skip_vrm_check, test)
            self.mtp_sal_check_j2c(slot, test)
            self.mtp_nic_console_unlock()
            self.mtp_single_j2c_unlock()
            self.mtp_nic_prp_test(slot)
            self.mtp_clear_nic_uart(slot)
            self.mtp_nic_qspi_verify_test(slot, test=test, stage=stage)

        self.mtp_mgmt_nic_diag_sys_clean()

        self.log_nic_file(slot, "#######= {:s} =#######".format("END post dsp {:s} fail debug".format(test)))

        return ret

    def mtp_mgmt_nic_diag_sys_clean(self):
        cmd = "diag -csys"
        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_CMD_DELAY):
            self.cli_log_err("Command {:s} failed".format(cmd), level=0)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_killall_tclsh_picocom(self, slot):
        self.mtp_nic_stop_tclsh(slot)

        cmd = MFG_DIAG_CMDS().NIC_DIAG_STOP_PICOCOM_FMT
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            self.cli_log_slot_err(slot, "Execute command {:s} failed".format(cmd))
            return False
        return True

    def mtp_mgmt_start_nic_diag(self, slot, aapl, dis_hal=False):
        if dis_hal:
            msg = "Start NIC Diag with HAL"
        else:
            if aapl:
                msg = "Start NIC Diag with HAL"
            else:
                msg = "Start NIC Diag without HAL"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_start_diag(aapl, dis_hal, mtp_type=self._mtp_type):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_set_nic_status_fail(slot)
            return False

        return True

    def mtp_set_nic_vmarg(self, slot, vmarg, percentage=""):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip Vmargin for Proto NIC")
            return True

        if percentage:
            self.cli_log_slot_inf_lock(slot, "Set voltage margin to {:s} with percentage {:s}".format(vmarg, percentage))
        else:
            self.cli_log_slot_inf_lock(slot, "Set voltage margin to {:s}".format(vmarg))

        if not self._nic_ctrl_list[slot].nic_set_vmarg(vmarg, percentage):
            self.cli_log_slot_err_lock(slot, "Set voltage margin to {:s} failed".format(vmarg))
            self.mtp_set_nic_status_fail(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_set_salina_dpu_nic_ddr_vmarg(self, slot, vmarg):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip DDR Vmargin for Proto NIC")
            return True

        if nic_type not in SALINA_DPU_NIC_TYPE_LIST:
            self.cli_log_slot_inf_lock(slot, "This DDR Vmarg setting only for salina DPU")
            return False

        self.cli_log_slot_inf_lock(slot, "Set Salina DPU DDR voltage margin to {:s}".format(str(vmarg)))

        if not self._nic_ctrl_list[slot].salina_nic_set_ddr_vmarg(vmarg):
            self.cli_log_slot_err_lock(slot, "Set Salina DPU DDR voltage margin to {:s} failed".format(vmarg))
            self.mtp_set_nic_status_fail(slot)
            return False

        return True

    def mtp_nic_display_voltage(self, slot):
        if not self._nic_ctrl_list[slot].nic_display_voltage():
            self.cli_log_slot_err_lock(slot, "Voltage display failed")
            return False

        return True

    def mtp_nic_emmc_init(self, slot, emmc_format=False, emmc_check=False):
        nic_type = self.mtp_get_nic_type(slot)
        if emmc_format:
            msg = "Format and Init NIC EMMC"
        else:
            msg = "Init NIC EMMC"
        self.cli_log_slot_inf_lock(slot, msg)
        if not self._nic_ctrl_list[slot].nic_init_emmc(emmc_format, emmc_check=emmc_check):
            self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_set_nic_status_fail(slot)
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
        if nic_type in (NIC_Type.ORTANO, NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL,
                        NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4):
            msg = "Set NIC in performance mode"
            if not self._nic_ctrl_list[slot].nic_emmc_set_perf_mode():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
                self.mtp_dump_nic_err_msg(slot)
                self.mtp_set_nic_status_fail(slot)
                return False
            self.cli_log_slot_inf_lock(slot, msg)
        return True

    def mtp_nic_emmc_check_perf_mode(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in (NIC_Type.ORTANO, NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL,
                        NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4):
            msg = "NIC in performance mode"
            if not self._nic_ctrl_list[slot].nic_emmc_check_perf_mode():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(msg))
                self.mtp_dump_nic_err_msg(slot)
                return False
            self.cli_log_slot_inf_lock(slot, msg)
        return True

    def fst_nic_set_perf_mode(self, slot):
        # Ensure performance mode even though this step is not needed with newer mainfw anymore.
        self.cli_log_slot_inf(slot, "Set performance mode")
        cmd = "touch /sysconfig/config0/.perf_mode"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to set performance mode")
            return False
        return True

    def mtp_nic_fru_init(self, slot, init_date=True, nic_type=None, fru_fpo=False):
        if init_date:
            msg = "Init NIC FRU info with date"
        else:
            msg = "Init NIC FRU info without date"
        if fru_fpo:
            msg += " with FPO"
        self.cli_log_slot_inf(slot, msg)

        if not self._nic_ctrl_list[slot].nic_fru_init(self._factory_location, init_date, self._swmtestmode[slot], fpo=fru_fpo):
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        # sku is unique, save it without reading fru
        self._nic_ctrl_list[slot]._sku = self.get_scanned_sku(slot)
        return True

    def mtp_nic_ocp_adapter_fru_init(self, slot, fpo=False):
        if self.mtp_get_nic_type(slot) != NIC_Type.NAPLES25OCP:
            self.cli_log_slot_err(slot, "OCP Adapter FRU init function is not for type {:s}".format(self.mtp_get_nic_type(slot)))
            return False

        if not self._nic_ctrl_list[slot].nic_ocp_adapter_fru_init(self._factory_location, fpo):
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_get_nic_ocp_adapter_sn(self, slot):
        if self.mtp_get_nic_type(slot) != NIC_Type.NAPLES25OCP:
            self.cli_log_slot_err(slot, "OCP Adapter FRU init function is not for type {:s}".format(self.mtp_get_nic_type(slot)))
            return None

        if self._nic_ctrl_list[slot]._riser_sn is None:
            if not self.mtp_nic_ocp_adapter_fru_init(slot):
                return None

        return self._nic_ctrl_list[slot]._riser_sn

    def mtp_get_nic_ocp_adapter_progdate(self, slot):
        if self.mtp_get_nic_type(slot) != NIC_Type.NAPLES25OCP:
            self.cli_log_slot_err(slot, "OCP Adapter FRU init function is not for type {:s}".format(self.mtp_get_nic_type(slot)))
            return None

        if self._nic_ctrl_list[slot]._riser_progdate is None:
            if not self.mtp_nic_ocp_adapter_fru_init(slot):
                return None

        return self._nic_ctrl_list[slot]._riser_progdate

    def mtp_nic_sn_init(self, slot, fpo=False):
        if not self._nic_ctrl_list[slot]._sn:
            if not self._nic_ctrl_list[slot].nic_smb_fru_init(self._factory_location, fpo=fpo):
                return False
            self.mtp_set_nic_sn(slot, self._nic_ctrl_list[slot]._sn)
        return True

    def mtp_nic_dpn_init(self, slot, fpo=False):
        if not self._nic_ctrl_list[slot]._dpn:
            if not self._nic_ctrl_list[slot].nic_smb_dpn_fru_init(self._factory_location, fpo=fpo):
                return False
        return True

    def mtp_nic_sku_init(self, slot, fpo=False):
        # already initialized
        if self._nic_ctrl_list[slot]._sku is not None and self._nic_ctrl_list[slot]._sku != "":
            return True

        # not initialized, but present in barcode scans
        scanned_sku = self.get_scanned_sku(slot)
        if scanned_sku is not None and scanned_sku != "":
            self._nic_ctrl_list[slot]._sku = self.get_scanned_sku(slot)
            return True

        else:
            # corner case, somehow it's not scanned, need to read the FRU:
            return False

    def mtp_nic_cpld_init(self, slot, smb=False):
        self.cli_log_slot_inf_lock(slot, "Init NIC CPLD info")
        if not self._nic_ctrl_list[slot].nic_cpld_init(smb):
            self.cli_log_slot_err_lock(slot, "Init NIC CPLD failed")
            return False

        if self.mtp_get_nic_type(slot) in VULCANO_NIC_TYPE_LIST:
            cpld_id = self._nic_ctrl_list[slot]._cpld_id
            cpld_ver = '.'.join([self._nic_ctrl_list[slot]._cpld_ver, self._nic_ctrl_list[slot]._cpld_ver_min])
            cpld_ts = self._nic_ctrl_list[slot]._cpld_timestamp
            cpld_info = "ID: {}, Version: {}, Timestamp: {}".format(cpld_id, cpld_ver, cpld_ts)
            self.cli_log_slot_inf(slot, "CPLD Info: {}".format(cpld_info))
        return True

    def mtp_mgmt_set_nic_sw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_sw_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default sw boot failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default sw boot")
        return True

    def mtp_mgmt_set_nic_gold_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_gold_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default gold boot failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default gold boot")
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_set_nic_goldfw_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_goldfw_boot():
            self.cli_log_slot_err_lock(slot, "Set NIC default gold boot failed")
            return False
        self.cli_log_slot_inf_lock(slot, "Set NIC default gold boot")
        return True

    def mtp_nic_load_scan_fru(self, slot):
        self.cli_log_slot_inf(slot, "Load NIC FRU config")
        sn = self.get_scanned_sn(slot)
        self.mtp_set_nic_scan_sn(slot, sn)
        return True

    def mtp_populate_fru_to_scans(self, slot, nic_fru_cfg, dpn="", sku=""):
        """
            When skipping scanning (e.g. for modeling/QA), still need the barcode_scans object to be filled.
            So copy the values from actual FRU.
        """
        key = libmfg_utils.nic_key(slot)
        self.barcode_scans[key] = dict()
        self.barcode_scans[key][bf.SN] = nic_fru_cfg[key][bf.SN]
        self.barcode_scans[key][bf.MAC] = nic_fru_cfg[key][bf.MAC]
        self.barcode_scans[key][bf.PN] = nic_fru_cfg[key][bf.PN]
        self.barcode_scans[key]["TS"] = nic_fru_cfg[key]["TS"]
        if dpn:
            self.barcode_scans[key][bf.DPN] = dpn
        if sku:
            self.barcode_scans[key][bf.SKU] = sku

    def mtp_populate_dpn_sku_to_scans(self, slot, dpn="", sku=""):
        """
            When skipping scanning (e.g. for modeling/QA), still need the barcode_scans object to be filled.
            This is in case FRU has not been read yet. Just save DPN or SKU.
        """
        key = libmfg_utils.nic_key(slot)
        self.barcode_scans[key] = dict()
        if dpn:
            self.cli_log_slot_inf(slot, "Scanned DPN {:s}".format(dpn))
            self.barcode_scans[key][bf.DPN] = dpn
        if sku:
            self.cli_log_slot_inf(slot, "Scanned SKU {:s}".format(sku))
            self.barcode_scans[key][bf.SKU] = sku

    def mtp_nic_info_disp(self, nic_list, fru_valid=True):
        self.cli_log_inf("MTP NIC Info Dump:")

        for slot in nic_list:
            prsnt = slot not in self.mtp_nic_check_prsnt(slot)
            nic_type = self.mtp_get_nic_type(slot)

            if prsnt:
                self.cli_log_slot_inf(slot, "NIC is Present, Type is: {:s}".format(nic_type))
                if fru_valid:
                    fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
                    dpn = self.mtp_get_nic_dpn(slot)

                    riser_sn = None
                    riser_progdate = None
                    if nic_type == NIC_Type.NAPLES25OCP:
                        riser_sn = self.mtp_get_nic_ocp_adapter_sn(slot)
                        riser_progdate = self.mtp_get_nic_ocp_adapter_progdate(slot)

                    if not fru_info_list:
                        self.cli_log_slot_err_lock(slot, "Retrieve NIC FRU failed")
                        if nic_type == NIC_Type.NAPLES25OCP:
                            if riser_sn is None or riser_progdate is None:
                                self.cli_log_slot_err_lock(slot, "Retrieve OCP Adapter FRU failed")
                    else:
                        self.cli_log_slot_inf(slot, "==> FRU: {:s}, {:s}, {:s}".format(fru_info_list[0],fru_info_list[1],fru_info_list[2]))
                        if dpn:
                            self.cli_log_slot_inf(slot, "==> DPN: {:s}".format(dpn))
                        if fru_info_list[3]:
                            self.cli_log_slot_inf(slot, "==> FRU Program Date: {:s}".format(fru_info_list[3]))
                        if nic_type == NIC_Type.NAPLES25OCP:
                            self.cli_log_slot_inf(slot, "==> OCP Adapter SN: {:s}, FRU Program Date: {:s}".format(riser_sn, riser_progdate))
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

        return []

    def mtp_nic_init(self, stage=None, new_ssh_sessions=True, scanned_fru=None, scanned_dpn=None, scanned_sku=None, prog_inter_diagsuc=None):
        self.cli_log_inf("Init NICs in the MTP Chassis", level=0)
        # open ssh session to each NIC
        if new_ssh_sessions:
            self.cli_log_inf("Init NIC Connections", level=0)
            if not self.mtp_nic_para_session_init():
                self.cli_log_err("Init NIC Connections Failed", level=0)
                return False

        # init nic present list
        if stage == FF_Stage.FF_FST:
            if not self.fst_init_nic_type(scanned_fru):
                self.cli_log_inf("Failed to init NICs in the FST", level=0)
                return False
        else:
            if not self.mtp_init_nic_type(stage, scanned_fru, scanned_dpn, scanned_sku, prog_inter_diagsuc):
                self.cli_log_inf("Failed to init NICs in the MTP Chassis", level=0)
                return False

        self.cli_log_inf("Init NICs in the MTP Chassis complete\n", level=0)

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_l1_setup(self, slot):
        slot_num = slot + 1

        cmd = "export MTP_REV=REV_04"
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            self.cli_log_slot_err(slot, "Execute command {:s} failed".format(cmd))
            return False

        cmd = "/home/diag/diag/util/jtag_accpcie_salina clr {:d}".format(slot_num)
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            self.cli_log_slot_err(slot, "Execute command {:s} failed".format(cmd))
            return False

        cmd = MFG_DIAG_CMDS().NIC_DIAG_STOP_PICOCOM_FMT
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            self.cli_log_slot_err(slot, "Execute command {:s} failed".format(cmd))
            return False

        return True

    def mtp_i2c_show(self, nic_list):
        self.cli_log_inf("Show I2C device in the MTP Chassis", level=0)
        cmd = MFG_DIAG_CMDS().MTP_MATERA_DEVMGR_STATUS_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to show I2C device in the MTP Chassis", level=0)
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False

        self.cli_log_inf("Show I2C device in the MTP Chassis complete\n", level=0)
        return True

    def mtp_set_mem_vddio(self, nic_list, margin=0):
        self.cli_log_inf("Set MEM VDDIO margin in the MTP Chassis", level=0)
        cmd = MFG_DIAG_CMDS().MTP_DEVICE_MARGIN_SET_FMT.format("MEM_VDDIO",margin)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to set mem vddio margin in the MTP Chassis", level=0)
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False

        self.cli_log_inf("Set MEM VDDIO margin in the MTP Chassis complete\n", level=0)
        return True

    # validate the fru to double confirm scan process
    def mtp_nic_scan_fru_validate(self, nic_list):
        if not nic_list:
            self.cli_log_err("No NICs passed to validate scanned FRU")
            return False

        for slot in nic_list:
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
                scan_sn = self.get_scanned_sn(slot)
                read_sn = self.mtp_get_nic_sn(slot)
                if scan_sn != read_sn:
                    self.cli_log_slot_err(slot, "SN mismatch, scanned: {:s}, fru: {:s}".format(scan_sn, read_sn))
                    return False
        return True

    def mtp_nic_mgmt_seq_init(self, nic_list, fpo, stop_on_err=False):
        for slot in nic_list:
            if self._nic_prsnt_list[slot] and self.mtp_check_nic_status(slot):
                if not self.mtp_nic_mini_init(slot, fpo):
                    self.mtp_set_nic_status_fail(slot)
                    if stop_on_err:
                        return False
                    else:
                        continue
        return True

    @parallelize.parallel_nic_using_nic_test
    def mtp_nic_test_setup_multi(self, nic_list, mgmt=True, fpo=False, aapl=False, swm_lp=False):
        fail_nic_list = list()

        if not nic_list:
            # self.cli_log_err("No NICs passed")
            return fail_nic_list

        # first slot will be the "main" slot to issue the commands on.
        slot_main = nic_list[0]

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd_para(slot_main, cmd):
            self.cli_log_slot_err(slot_main, "Execute command {:s} failed".format(cmd))
            return nic_list[:]

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        nic_type_list = [self.mtp_get_nic_type(slot) for slot in nic_list]
        if  False not in [nic_type in ELBA_NIC_TYPE_LIST+GIGLIO_NIC_TYPE_LIST for nic_type in nic_type_list]:
            asic_type = "elba"
        elif False not in [nic_type in SALINA_NIC_TYPE_LIST for nic_type in nic_type_list]:
            asic_type = "salina"
        elif False not in [nic_type in VULCANO_NIC_TYPE_LIST for nic_type in nic_type_list]:
            asic_type = "vulcano"
        else:
            asic_type = "capri"

        if asic_type == "capri" and self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            self.cli_log_slot_err(slot_main, "Unable to run capri in {:s} mtp".format(self._mtp_type))
            return [slot_main]
        sig_list = [MFG_DIAG_SIG.NIC_MGMT_PARA_SIG]
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA): sig_list = [MFG_DIAG_SIG.MATERA_NIC_MGMT_PARA_SIG]

        if not mgmt:
            for slot in nic_list:
                self.cli_log_slot_inf(slot, "Para Init NIC environment")
            cmd = MFG_DIAG_CMDS().MTP_PARA_INIT_FMT.format(nic_list_param, asic_type)
            if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA): cmd = MFG_DIAG_CMDS().MATERA_MTP_SINGLE_INIT_FMT.format(nic_list_param, asic_type)
        elif fpo:
            for slot in nic_list:
                self.cli_log_slot_inf(slot, "Para Init NIC MGMT port with FPO")
            cmd = MFG_DIAG_CMDS().MTP_PARA_MGMT_FPO_FMT.format(nic_list_param, asic_type)
            if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA): cmd = MFG_DIAG_CMDS().MATERA_MTP_SINGLE_MGMT_FPO_FMT.format(nic_list_param, asic_type)
            if asic_type == "salina": cmd = MFG_DIAG_CMDS().MATERA_SALINA_SINGLE_MGMT_INIT_FMT.format(nic_list_param, asic_type)
        elif aapl:
            for slot in nic_list:
                self.cli_log_slot_inf(slot, "Para Init NIC MGMT/AAPL port")
            cmd = MFG_DIAG_CMDS().MTP_PARA_MGMT_AAPL_FMT.format(nic_list_param, asic_type)
        else:
            for slot in nic_list:
                self.cli_log_slot_inf(slot, "Para Init NIC MGMT port")
            cmd = MFG_DIAG_CMDS().MTP_PARA_MGMT_INIT_FMT.format(nic_list_param, asic_type)
            if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA): cmd = MFG_DIAG_CMDS().MATERA_MTP_SINGLE_MGMT_INIT_FMT.format(nic_list_param, asic_type)
            if asic_type == "salina": cmd = MFG_DIAG_CMDS().MATERA_SALINA_SINGLE_MGMT_INIT_FMT.format(nic_list_param, asic_type)
            if swm_lp:
                cmd = "".join((cmd, " -swm_lp"))

        if not self.mtp_mgmt_exec_cmd_para(slot_main, cmd, sig_list=sig_list, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
            self.cli_log_slot_err(slot_main, "Execute command {:s} failed".format(cmd))
            return nic_list[:]
        # self.nic_semi_parallel_log(nic_list, self.mtp_get_cmd_buf_before_sig())
        if "failed" in self.mtp_get_nic_cmd_buf(slot_main):
            match = re.search("failed slot:.*'([0-9,]+)'", self.mtp_get_nic_cmd_buf(slot_main))
            if match:
                for slot in libmfg_utils.expand_range_of_numbers(match.group(1), range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot-1
                    self.cli_log_slot_err(slot, "Para Init NIC MGMT failed")
                    self.mtp_set_nic_status_fail(slot)
                    fail_nic_list.append(slot)

        return fail_nic_list


    def mtp_nic_mgmt_para_init_fpo(self, nic_list, stop_on_err=False):
        # dump MTP Marvel Switch Port status
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            self.cli_log_inf("Dump MTP Marvel Switch Port Status", level=0)
            port = '-1'
            for mvl_instance in ("0", "1"):
                cmd = MFG_DIAG_CMDS().MTP_MATERA_FPGAUTIL_MVLDUMP_CMD_FMT.format(mvl_instance, port)
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("Dump MTP Marvel Switch Port Status Failed", level=0)
                    self.mtp_dump_err_msg(self._mgmt_handle.before)
                    return False
            self.cli_log_inf("Dump MTP Marvel Switch Port Status complete", level=0)

        fail_setup_multi_list = self.mtp_nic_test_setup_multi(nic_list, fpo=True)
        if stop_on_err:
            return fail_setup_multi_list
        fail_mac_refresh_list = self.mtp_nic_mgmt_mac_refresh(nic_list)
        return libmfg_utils.list_union(fail_setup_multi_list, fail_mac_refresh_list)

    def nic_semi_parallel_log(self, nic_list, buf):
        buf = buf[:]  # make a copy
        capture = [True] * self._slots
        logbuf = [""] * self._slots
        for line in buf.splitlines():
            for slot in nic_list:
                if re.search(r"Starting [\w ]+ on slot %s" % str(slot+1), line) or re.search(r"Checking [\w ]*result on slot %s" % str(slot+1), line):
                    capture = [False] * self._slots
                    capture[slot] = True
                elif re.search("Setup env on slot %s env setup done" % str(slot+1), line) or re.search("on slot %s started" % str(slot+1), line) or re.search(r"Check?ing [\w ]*result on slot %s Done" % str(slot+1), line):
                    capture = [False] * self._slots
                    logbuf[slot] += line + "\n"  # final line
                if capture[slot]:
                    if line.strip():  # skip empty new line
                        logbuf[slot] += line + "\n"

        for slot in nic_list:
            self._nic_ctrl_list[slot]._nic_handle.logfile_read.write(": <<'////'\nCopied log from mtp_diag.log:\n{:s}\n////".format(logbuf[slot]))

        return True

    def mtp_nic_mgmt_para_init(self, nic_list, aapl, swm_lp=False, stop_on_err=False):
        fail_setup_multi_list = self.mtp_nic_test_setup_multi(nic_list, aapl=aapl, swm_lp=swm_lp)
        if stop_on_err:
            return fail_setup_multi_list
        fail_mac_refresh_list = self.mtp_nic_mgmt_mac_refresh(nic_list)
        return libmfg_utils.list_union(fail_setup_multi_list, fail_mac_refresh_list)

    @parallelize.parallel_nic_using_nic_test
    def mtp_nic_edma_env_init(self, nic_list):
        fail_nic_list = list()
        if not nic_list:
            return fail_nic_list

        # first slot will be the "main" slot to issue the commands on.
        slot_main = nic_list[0]

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd_para(slot_main, cmd):
            self.cli_log_slot_err(slot_main, "Execute command {:s} failed".format(cmd))
            return False

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.NIC_PARA_EDMA_ENV_INIT_SIG]
        cmd = MFG_DIAG_CMDS().MTP_PARA_EDMA_ENV_INIT_FMT.format(nic_list_param)

        if not self.mtp_mgmt_exec_cmd_para(slot_main, cmd, sig_list=sig_list, timeout=MTP_Const.NIC_EDMA_ENV_INIT_CMD_DELAY):
            self.cli_log_slot_err(slot_main, "Execute command {:s} failed".format(cmd))
            return nic_list[:]
        if "FAIL list:" in self.mtp_get_nic_cmd_buf(slot_main):
            match = re.search(r"FAIL list:', \[([0-9,']+)\]", self.mtp_get_nic_cmd_buf(slot_main))
            if match:
                fail_slot_str = match.group(1).replace("'", "")
                for slot in libmfg_utils.expand_range_of_numbers(fail_slot_str, range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot-1
                    self.cli_log_slot_err_lock(slot, "Para Init EDMA environment init failed")
                    fail_nic_list.append(slot)

        return fail_nic_list

    def mtp_nic_para_init(self, nic_list, stop_on_err=False):
        fail_setup_multi_list = self.mtp_nic_test_setup_multi(nic_list, mgmt=False)
        return fail_setup_multi_list

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_mgmt_mac_refresh(self, slot):
        # delete the arp entry
        if self._nic_prsnt_list[slot]:
            ipaddr = libmfg_utils.get_nic_ip_addr(slot)
            cmd = MFG_DIAG_CMDS().MTP_ARP_DELET_FMT.format(ipaddr)
            if not self.mtp_mgmt_exec_sudo_cmd(cmd):
                return False

            ###Have seen failures on Naples25SWM where ping fails and ARP table is not populated
            ###Add a 2nd ping try as a work around.   
            # first ping, send only 1 packet to wake it up

            # time.sleep(5)
            cmd = "ping -c 1 {:s}".format(ipaddr)
            if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
                return False

            # time.sleep(5)
            cmd = MFG_DIAG_CMDS().MTP_NIC_PING_FMT.format(ipaddr)
            if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
                return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_diag_init_start_diag(self, slot, emmc_format, emmc_check, aapl, dis_hal):
        if not self.mtp_nic_emmc_init(slot, emmc_format, emmc_check=emmc_check):
            return False
        if not self.mtp_mgmt_setup_nic_diag(slot, emmc_format):
            return False
        if not self.mtp_mgmt_start_nic_diag(slot, aapl, dis_hal):
            return False
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_diag_init_cpld_diag(self, slot, emmc_format):
        nic_type = self.mtp_get_nic_type(slot)
        smb = False
        if nic_type in SALINA_NIC_TYPE_LIST:
            smb = True
        if not self.mtp_nic_cpld_init(slot, smb):
            return False
        if not emmc_format:
            if not self.mtp_check_nic_cpld_partition(slot):
                return False
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_diag_init_fru_init(self, slot, init_date, fru_fpo):
        ret = True
        nic_type = self.mtp_get_nic_type(slot)
        if not self.mtp_nic_fru_init(slot, init_date, nic_type, fru_fpo):
            ret = False
        fru_info_list = self._nic_ctrl_list[slot].nic_get_fru()
        if fru_info_list:
            self.mtp_set_nic_sn(slot, fru_info_list[0])
        else:
            self.cli_log_slot_err(slot, "Unable to load SN")
            ret = False
        return ret

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_diag_init_nic_vmarg(self, slot, vmargin):
        vmarg_percentage = ""
        if vmargin in (Voltage_Margin.high, Voltage_Margin.low):
            partnumber = ""
            for nic_controller in  self._nic_ctrl_list:
                if nic_controller._pn:
                    partnumber = nic_controller._pn
                    break
            vmarg_percentage = libmfg_utils.pick_voltage_margin_percentage(partnumber)
            vmarg_percentage = vmarg_percentage.strip("_")
            self.cli_log_slot_inf(slot, "Got Vmargin Percentage: {:s} With Part Number: {:s} ".format(vmarg_percentage, partnumber))

        if not self.mtp_set_nic_vmarg(slot, vmargin, vmarg_percentage):
            return False
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in SALINA_NIC_TYPE_LIST:
            if not self.mtp_nic_display_voltage(slot):
                return False
        return True

    def mtp_nic_diag_init(self, nic_list, emmc_format=False, emmc_check=False, fru_valid=True, sn_tag=False, fru_cfg=None, vmargin=Voltage_Margin.normal, aapl=False, swm_lp=False, nic_util=False, dis_hal=False, stop_on_err=False, skip_info_dump=False, fru_fpo=False, skip_test_list=[], dsp="DIAG_INIT"):
        fail_nic_list = list()
        nic_list = nic_list[:]
        if not nic_list:
            return []
        # if 2D list passed from regression, need to flatten it
        if isinstance(nic_list[0], list):
            nic_list = libmfg_utils.flatten_list_of_lists(nic_list)

        # parse args
        # emmc_format will be true only for the first time boot up
        fpo = emmc_format
        if nic_util:
            # for QA only not DL: do mgmt para init but do emmc format.
            emmc_format = True
        if fru_valid:
            if fpo:
                init_date = False
            else:
                init_date = True

        # construct test_list
        test_list = []
        if fpo:
            self.cli_log_inf("Init NIC Diag Environment with FPO set", level=0)
        else:
            self.cli_log_inf("Init NIC Diag Environment", level=0)

        if sn_tag:
            test_list.append("SCANS_LOAD")
        else:
            self.cli_log_inf("Bypass NIC SN/MAC load")
        if fpo:
            test_list.append("NIC_PARA_MGMT_FPO_INIT")
        elif aapl:
            test_list.append("NIC_PARA_MGMT_AAPL_INIT")
        else:
            test_list.append("NIC_PARA_MGMT_INIT")
        test_list.append("NIC_BOOT_INIT")
        test_list.append("MAC_VALIDATE")
        test_list.append("START_DIAG")
        test_list.append("CPLD_DIAG")
        if fru_valid:
            test_list.append("NIC_FRU_INIT")
        # For Salina Cards, set vmarg before booting A35, otherwise i2c is occupied & zephyr may reboot the card with reason "DPU internal reset GPIO8
        # so put set vmarg as first list element
        for slot in nic_list:
            if self._nic_ctrl_list[slot] and self._nic_type_list[slot] in SALINA_NIC_TYPE_LIST:
                test_list.insert(0, "NIC_VMARG")
                break
        else:
            test_list.append("NIC_VMARG")

        if fru_valid and sn_tag:
            test_list.append("SCANS_VALIDATE")
        if not skip_info_dump:
            test_list.append("INFO_DUMP")

        ### Redefine nic diag init test suite for Salina
        for slot in nic_list:
            if self._nic_ctrl_list[slot] and self._nic_type_list[slot] in SALINA_DPU_NIC_TYPE_LIST:
                test_list = ['NIC_VMARG', 'NIC_PARA_MGMT_INIT', 'NIC_BOOT_INIT', 'MAC_VALIDATE', 'START_DIAG', 'CPLD_DIAG', 'INFO_DUMP']
                break 

        for test in test_list:
            if test in skip_test_list:
                test_utils.test_skip_nic_log_message(self, nic_list, dsp, test)
                continue

            start_ts = self.log_test_start(test)
            test_utils.test_start_nic_log_message(self, nic_list, dsp, test)

            if test == "SCANS_LOAD":
                rlist = self.mtp_nic_load_scan_fru(nic_list)
            elif test == "SCANS_VALIDATE":
                rlist = self.mtp_nic_scan_fru_validate(nic_list)
            elif test == "NIC_PARA_MGMT_FPO_INIT":
                rlist = self.mtp_nic_mgmt_para_init_fpo(nic_list, stop_on_err)
            elif test == "NIC_PARA_MGMT_INIT":
                rlist = self.mtp_nic_mgmt_para_init(nic_list, aapl, swm_lp, stop_on_err)
            elif test == "NIC_PARA_MGMT_AAPL_INIT":
                rlist = self.mtp_nic_mgmt_para_init(nic_list, aapl, swm_lp, stop_on_err)
            elif test == "NIC_BOOT_INIT":
                rlist = self.mtp_nic_boot_info_init(nic_list)
            elif test == "MAC_VALIDATE":
                rlist = self.mtp_mgmt_nic_mac_validate(nic_list)
            elif test == "START_DIAG":
                rlist = self.mtp_nic_diag_init_start_diag(nic_list, emmc_format, emmc_check, aapl, dis_hal)
            elif test == "CPLD_DIAG":
                rlist = self.mtp_nic_diag_init_cpld_diag(nic_list, emmc_format)
            elif test == "NIC_FRU_INIT":
                rlist = self.mtp_nic_diag_init_fru_init(nic_list, init_date, fru_fpo)
            elif test == "NIC_VMARG":
                rlist = self.mtp_nic_diag_init_nic_vmarg(nic_list, vmargin)
            elif test == "INFO_DUMP":
                rlist = self.mtp_nic_info_disp(nic_list, fru_valid)
            else:
                self.cli_log_err("Unknown test '{:s}'".format(test), level=0)
                rlist = nic_list[:]

            # if any slot failed and not counted in fail list, fail it
            for slot in nic_list:
                if not self.mtp_check_nic_status(slot) and slot not in rlist:
                    rlist.append(slot)

            # catch bad return value
            if not isinstance(rlist, list):
                self.cli_log_err("Test failed with '{}', expected slot list".format(repr(rlist)))
                rlist = nic_list[:]

            for slot in rlist:
                self.mtp_set_nic_status_fail(slot)
                nic_list.remove(slot)
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)

            duration = self.log_test_stop(test, start_ts)
            test_utils.test_fail_nic_log_message(self, rlist, dsp, test, start_ts)
            test_utils.test_pass_nic_log_message(self, nic_list, dsp, test, start_ts)

            if rlist and stop_on_err:
                self.cli_log_err("caught stop_on_err in {:s}".format(test), level=0)
                break

        self.mtp_mgmt_killall_tclsh_picocom(nic_list)

        self.cli_log_inf("Init NIC Diag Environment complete\n", level = 0)
        return fail_nic_list

    @parallelize.parallel_nic_using_ssh
    def mtp_mgmt_nic_mac_validate(self, slot):
        """ check if any duplicate mac address in the internal network """
        self.cli_log_slot_inf(slot, "Validating NIC MAC address")
        nic_mac_addr_list = []
        nic_ip_addr_list = []
        # mac_addr_reg_exp = r"([a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2})"
        mac_addr_reg_exp = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+([a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2})"
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            cmd = MFG_DIAG_CMDS().MATERA_MTP_NIC_MAC_DISP_FMT
        else:
            cmd = MFG_DIAG_CMDS().MTP_NIC_MAC_DISP_FMT
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            self.cli_log_slot_err(slot, "Failed to validate NIC MAC address")
            return False

        match = re.findall(mac_addr_reg_exp, self.mtp_get_nic_cmd_buf(slot))
        if match:
            for nic_info in match:
                if nic_info[0] in nic_ip_addr_list or nic_info[1] in nic_mac_addr_list:
                    slot = int(nic_info[0].split('.')[3]) - 101
                else:
                    slot = int(nic_info[0].split('.')[3]) - 101
            return True
        else:
            return False

    def mtp_power_on_nic(self, slot_list=[], dl=False, count_down=True):
        self.mtp_nic_lock()

        slot_list_param = ",".join(str(slot+1) for slot in slot_list)
        if not slot_list_param:
            slot_list_param = "all"
        cmd = MFG_DIAG_CMDS().MTP_POWER_ON_NIC_FMT.format(slot_list_param)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.mtp_nic_unlock()
            self.cli_log_err("Failed to power on NIC")
            return False

        ts_record = libmfg_utils.timestamp_snapshot()
        for slot in slot_list:
            if self._nic_ctrl_list[slot]:
                self.log_nic_file(slot, "#####  Power on NIC #####")

        if count_down:
            self.cli_log_inf("Power on all NIC, wait {:02d} seconds for NIC power up".format(MTP_Const.NIC_POWER_ON_DELAY), level=0)
            libmfg_utils.count_down(MTP_Const.NIC_POWER_ON_DELAY)
        else:
            self.cli_log_inf("Power on all NIC, NIC power up", level=0)

        self.mtp_nic_unlock()

        self.mtp_nic_lock()
        nic_list = list()
        if slot_list_param == "all":
            nic_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        else:
            nic_list = slot_list[:]

        for slot in nic_list:
            if self._nic_ctrl_list[slot] and self._nic_type_list[slot] in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4) and not dl:
                if not self._nic_ctrl_list[slot].nic_set_i2c_after_pw_cycle():
                    self.mtp_get_nic_err_msg(slot)
                else:
                    self.cli_log_slot_inf(slot, "I2C value setting complete")
        self.mtp_nic_unlock()

        return True

    def mtp_power_off_nic(self, slot_list=[]):
        self.mtp_nic_lock()
        slot_list_param = ",".join(str(slot+1) for slot in slot_list)
        if not slot_list_param:
            slot_list_param = "all"
        cmd = MFG_DIAG_CMDS().MTP_POWER_OFF_NIC_FMT.format(slot_list_param)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.mtp_nic_unlock()
            self.cli_log_err("Failed to power off NIC")
            return False

        ts_record = libmfg_utils.timestamp_snapshot()
        for slot in slot_list:
            if self._nic_ctrl_list[slot]:
                self.log_nic_file(slot, "##### Power off NIC #####")

        self.cli_log_inf("Power off all NIC, wait {:02d} seconds for NIC power down".format(MTP_Const.NIC_POWER_OFF_DELAY), level=0)
        libmfg_utils.count_down(MTP_Const.NIC_POWER_OFF_DELAY)
        self.mtp_nic_unlock()
        return True

    @parallelize.parallel_nic_using_nic_test
    def mtp_power_cycle_nic(self, slot_list=[], dl=False, count_down=True):
        rc = self.mtp_power_off_nic(slot_list)
        if not rc:
            return slot_list[:]

        rc = self.mtp_power_on_nic(slot_list, dl, count_down)
        if not rc:
            return slot_list[:]
        return []

    @parallelize.parallel_nic_using_ssh
    def mtp_i2cget_nic_register(self, slot, chip_addr='0x4a', reg_addr2exp_val={}):
        '''
        i2cget utility usage:
        Usage: i2cget [-f] [-y] [-a] I2CBUS CHIP-ADDRESS [DATA-ADDRESS [MODE [LENGTH]]]
            I2CBUS is an integer or an I2C bus name
            ADDRESS is an integer (0x08 - 0x77, or 0x00 - 0x7f if -a is given)
            MODE is one of:
                b (read byte data, default)
                w (read word data)
                c (write byte/read byte)
                s (read SMBus block data)
                i (read I2C block data)
                Append p for SMBus PEC
            LENGTH is the I2C block data length (between 1 and 32, default 32)

        For Matera MTP, I2CBUS number is the one based slotid + 2;
        For legacy MTP the I2CBUS number always 0, using turn_on_hub.sh to control i2c bus mux.

        Most of our user case DATA-ADDRESS is register address
        '''

        if not reg_addr2exp_val:
            return False

        if self._mtp_type not in  (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            cmd = MFG_DIAG_CMDS().MTP_SMB_SEL_FMT.format(slot+1)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                self.cli_log_slot_err(slot, "Execute command {:s} failed".format(cmd))
                return False
        bus_num = slot + 1 + 2 if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA) else 0
        nic_type = self.mtp_get_nic_type(slot)

        for reg_addr, exp_val in reg_addr2exp_val.items():
            cmd = "i2cget -y {:d} {:s} {:s}".format(bus_num, chip_addr, reg_addr)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                self.cli_log_slot_err(slot, "Execute command {:s} failed".format(cmd))
                return False
            match = re.findall(r"(0x[0-9a-fA-F]+)", self.mtp_get_nic_cmd_buf(slot).replace(cmd, ''))
            if not match:
                self.cli_log_slot_err(slot, "Failed to get command {:s} return value".format(cmd))
                return False
            if int(match[0], 16) != int(exp_val, 16):
                self.cli_log_slot_err(slot, "Register {:s} read value {:s} NOT match expect value {:s}".format(reg_addr, match[0], exp_val))
                return False
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_salina_jtag_mbist(self, slot, vmarg="normal", test_type="warm"):

        if not self._nic_ctrl_list[slot].nic_salina_jtag_mbist(vmarg, test_type):
            self.cli_log_slot_err(slot, "NIC JTAG MBIST FAILED")
            self.mtp_get_nic_err_msg(slot)
            return False
        else:
            self.cli_log_slot_inf(slot, "NIC JTAG MBIST PASS")

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_vulcano_jtag_mbist(self, slot, vmarg="normal", test_type="warm"):

        if not self._nic_ctrl_list[slot].nic_vulcano_jtag_mbist(vmarg, test_type):
            self.cli_log_slot_err(slot, "NIC JTAG MBIST FAILED")
            self.mtp_get_nic_err_msg(slot)
            return False
        else:
            self.cli_log_slot_inf(slot, "NIC JTAG MBIST PASS")

        return True

    def mtp_l1_pre_setup(self, slot):

        failed_slot_list = []
        slots_list = slot
        for slot in slots_list:
            if not self._nic_ctrl_list[slot].nic_l1_pre_setup():
                self.cli_log_slot_err(slot, "NIC L1 PRE-SETUP FAILED")
                self.mtp_get_nic_err_msg(slot)
                failed_slot_list.append(slot)
                continue
            self.cli_log_slot_inf(slot, "NIC L1 PRE-SETUP PASS")
        return failed_slot_list

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_salina_google_stress_mem(self, slot, vmarg='normal',  mem_copy_thread=16, seconds2run=60, slot_asic_dir_path="/home/diag/diag/asic/"):
        '''
        run google stress mem test by nic_test_v2.py subcommand
        '''

        if not self._nic_ctrl_list[slot].nic_google_stress_test(vmarg, mem_copy_thread, seconds2run, slot_asic_dir_path):
            self.cli_log_slot_err(slot, "NIC GOOGLE STRESS MEM TEST FAILED")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_salina_google_stress_emmc(self, slot, vmarg='normal',  iterations=1, seconds2run=60, slot_asic_dir_path="/home/diag/diag/asic/"):
        '''
        run google stress emmc test by nic_test_v2.py subcommand
        '''

        if not self._nic_ctrl_list[slot].nic_emmc_stress_test(vmarg, iterations, seconds2run, slot_asic_dir_path):
            self.cli_log_slot_err(slot, "NIC GOOGLE STRESS EMMC TEST FAILED")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_salina_edma(self, slot, vmarg='normal', seconds2run=60, slot_asic_dir_path="/home/diag/diag/asic/"):
        '''
        from salina run edma test from mtp script nic_test_v2.py
        ./nic_test_v2.py edma_test -slot <slot> -vmarg VMARG -dura DURA -tcl_path TCL_PATH
        '''

        if not self._nic_ctrl_list[slot].nic_test_v2_py_edma(vmarg, seconds2run, slot_asic_dir_path):
            self.cli_log_slot_err(slot, "NIC_TEST_V2 EDMA TEST FAILED")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True


    @parallelize.parallel_nic_using_ssh
    def mtp_nic_snake_mtp_salina(self, slot, snake_type='esam_pktgen_max_power_sor', vmarg="normal", dura=120, timeout=3600, asic_dir_path=None, ite='1', int_lpbk='0'):
        '''
        run salina max power snake
        '''

        if not asic_dir_path:
            return False

        slot_asic_dir_path = asic_dir_path[slot]

        if not self._nic_ctrl_list[slot].nic_snake_mtp_salina(snake_type, vmarg, dura, timeout, slot_asic_dir_path, ite, int_lpbk):
            self.cli_log_slot_err_lock(slot, "nic_test_v2 nic_snake_mtp {:s} TEST FAILED".format(snake_type))
            # self.mtp_get_nic_err_msg(slot) # this line print out error message on the screeen ehich includes diag MTP promtp, cause expect sendt script exit
            return False

        return True


    @parallelize.parallel_nic_using_ssh
    def mtp_ainic_snake_mtp_salina(self, slot, snake_type='esam_pktgen_pollara_max_power_pcie_arm', vmarg="normal", dura=900, timeout=3600, asic_dir_path=None, ite='1', int_lpbk='0'):
        '''
        run salina max power snake
        '''

        if not asic_dir_path:
            return False

        slot_asic_dir_path = asic_dir_path[slot]

        if not self._nic_ctrl_list[slot].ainic_snake_mtp_salina(snake_type, vmarg, dura, timeout, slot_asic_dir_path, ite, int_lpbk):
            self.cli_log_slot_err_lock(slot, "nic_test_v2 nic_snake_mtp {:s} TEST FAILED".format(snake_type))
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_pcie_prbs_salina(self, slot, vmarg="normal", timeout=300, asic_dir_path=None):
        '''
        run salina pcie prbs
        '''

        if not asic_dir_path:
            return False

        if not self._nic_ctrl_list[slot].nic_pcie_prbs_salina(vmarg, timeout, asic_dir_path):
            self.cli_log_slot_err(slot, "NIC PCIE PRBS TEST FAILED")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_set_piceawd_env_salina(self, slot, timeout=300):
        '''
        run salina set piceawd env
        '''

        if not self._nic_ctrl_list[slot].set_piceawd_env_salina(timeout):
            self.cli_log_slot_err(slot, "NIC SET PCIEAWD ENV TEST FAILED")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_erase_piceawd_env_salina(self, slot, timeout=300):
        '''
        run salina set piceawd env
        '''

        if not self._nic_ctrl_list[slot].erase_piceawd_env_salina(timeout):
            self.cli_log_slot_err(slot, "NIC ERASE PCIEAWD ENV TEST FAILED")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_i2c_qsfp_salina(self, slot, vmarg="normal", timeout=600):
        '''
        run salina i2c qsfp
        '''

        if not self._nic_ctrl_list[slot].i2c_qsfp_salina(vmarg, timeout):
            self.cli_log_slot_err(slot, "NIC I2C QSFP TEST FAILED")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_i2c_rtc_salina(self, slot, vmarg="normal", timeout=180):
        '''
        run salina i2c rtc
        '''

        if not self._nic_ctrl_list[slot].i2c_rtc_salina(vmarg, timeout):
            self.cli_log_slot_err(slot, "NIC I2C RTC TEST FAILED")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    def mtp_make_copies_of_asic_dir(self, slot_list=[]):
        """
        make copies of asic working directory to support Salina snake to run at different directory in parallel.
        """

        if not slot_list:
            return []

        for i in range(1, 10):
            cmd = f"rm -rf /home/diag/diag/asic{i}"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err(f"Failed to execute command: {cmd}")
                self.mtp_dump_err_msg(self._mgmt_handle.before)

        asic = "salina" if self._mtp_type == MTP_TYPE.MATERA else "vulcano"

        # check disk free capacity, return False if less then 4G per slot
        total, used, free = shutil.disk_usage("/home/diag")
        freeinGb = int( free / 1024 / 1024 /1024)
        if freeinGb <= 4 * len(slot_list):
            self.cli_log_err(f"Limited Available Disk Space, Not ready for Prallel Snake Test")
            return slot_list

        for slot in slot_list:
            if slot == 0:
                continue
            cmd = f"cp -r /home/diag/diag/asic_all/{asic} /home/diag/diag/asic{slot}"
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err(f"Failed to execute command: {cmd}")
                self.mtp_dump_err_msg(self._mgmt_handle.before)
                return slot_list
        return []

    def mtp_untar_snake_qspi_img(self, slot_list=[], stage=FF_Stage.FF_P2C):
        """
        untar special qspi image for salina snake test
        """
        if len(slot_list) == 0:
            return []

        image_path = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_qspi_snake_img(self, slot_list[0], stage)["filename"]

        cmd = f"tar -xzf {image_path} -C " + os.path.dirname(image_path)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err(f"Failed to execute command: {cmd}")
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return slot_list
        return []

    def mtp_untar_mbist_boot0_img(self, slot_list=[]):
        """
        untar special qspi image for salina snake test
        """
        if len(slot_list) == 0:
            return []

        dsp = FF_Stage.FF_P2C
        image_path = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_mbist_boot0_img(self, slot_list[0], dsp)["filename"]

        cmd = f"tar -xzf {image_path} -C " + os.path.dirname(image_path)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err(f"Failed to execute command: {cmd}")
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return slot_list
        return []

    @parallelize.parallel_nic_using_nic_test
    def mtp_power_cycle_boot_stage(self, slot_list=[], bootstage=None, warm_reset=False, new_layout=False, new_mem_layout=False):
        """
        argument bootstage and warmreset are only for Matera MTP and Salina cards
        """
        fail_nic_list = slot_list[:]
        verify_reg_map = {
            '0x14': '0x07',
            '0x30': '0x00',
            '0x31': '0x00',
            '0x32': '0x00'
        }

        if not slot_list:
            # self.cli_log_err("No NICs passed")
            return fail_nic_list
        slot_main = slot_list[0]

        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA) and bootstage:
            if bootstage not in ('a35_uboot', 'n1_uboot', 'zephyr', 'linux', 'diag', 'nondiag'):
                self.cli_log_slot_err(slot_main, f"Unsupported Salina boot stage {bootstage}")
                return fail_nic_list
            cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
            if not self.mtp_mgmt_exec_cmd_para(slot_main, cmd):
                self.cli_log_slot_err(slot_main, "Failed to execute command {:s}".format(cmd))
                return fail_nic_list
            cmd = MFG_DIAG_CMDS().MATERA_MTP_NIC_BOOT_TO.format(bootstage, ",".join(str(slot+1) for slot in slot_list))
            if warm_reset:
                verify_reg_map['0x30'] = '0x12'
                cmd += " --warm_reset"
            if new_layout:
                cmd += " --new_ainic_layout"
            if new_mem_layout:
                cmd += " --new_memory_layout"
                cmd += " --login_delay 120"
            if not self.mtp_mgmt_exec_cmd_para(slot_main, cmd, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
                self.cli_log_slot_err(slot_main, "Execute command {:s} failed".format(cmd))
                return fail_nic_list
            buf = self.mtp_get_nic_cmd_buf(slot_main)
            match_obj = re.findall(r"Slot\s+(\d+)\s+PASSED", buf)
            if match_obj:
                for m_obj in match_obj:
                    pass_slot = int(m_obj) - 1
                    fail_nic_list.remove(pass_slot)
            else:
                for slot in fail_nic_list:
                    self.cli_log_slot_err(slot, "Command {:s} failed of this slot".format(cmd))

            rlist = self.mtp_i2cget_nic_register(slot_list, reg_addr2exp_val=verify_reg_map)
            for slot in rlist:
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)

            return fail_nic_list

    def boot_n1_linux(self, nic_list):
        fail_nic_list = list()
        if not nic_list:
            # self.cli_log_err("No NICs passed")
            return fail_nic_list
        # first slot will be the "main" slot to issue the commands on.
        slot_main = nic_list[0]
        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        boot_stage = "a35_uboot"
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd_para(slot_main, cmd):
            self.cli_log_slot_err(slot_main, "Execute command {:s} failed".format(cmd))
            return False
        cmd = MFG_DIAG_CMDS().SALINA_BOOT_MODE_FMT.format(boot_stage, nic_list_param)
        if not self.mtp_mgmt_exec_cmd_para(slot_main, cmd, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
            self.cli_log_slot_err(slot_main, "Execute command {:s} failed".format(cmd))
            return nic_list[:]
        if "Failed" in self.mtp_get_nic_cmd_buf(slot_main):
            match = re.search(r"Failed slots: \[*([0-9,]+)\]", self.mtp_get_nic_cmd_buf(slot_main))
            if match:
                for slot in libmfg_utils.expand_range_of_numbers(match.group(1), range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot-1
                    self.cli_log_slot_err(slot, "Para Init NIC MGMT failed")
                    self.mtp_set_nic_status_fail(slot)
                    fail_nic_list.append(slot)
        return fail_nic_list


    def mtp_init_nic_type(self, stage=None, scanned_fru=None, scanned_dpn=None, scanned_sku=None, prog_inter_diagsuc=None):
        self._nic_type_list = [None] * self._slots      # reset nic types
        cmd = MFG_DIAG_CMDS().NIC_PRESENT_DISP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to init NIC presence")
            self.mtp_dump_err_msg(self._mgmt_handle.before)
            return False

        if prog_inter_diagsuc:
            self.cli_log_inf("Init Vulcano NIC Presence by check USB UART device present, Then Fake NIC Type")
            for slot in range(self._slots):
                usbsn = self._nic_ctrl_list[slot].suc_slot2_usb_sn()
                if "No such file or directory" in usbsn:
                    continue
                if usbsn:
                    self.cli_log_inf(f"Slot {slot + 1} present, USB serial number is {usbsn}")
                    self._nic_prsnt_list[slot] = True
                    self._nic_type_list[slot] = "VulcanoFakeNicType"
                    self._nic_ctrl_list[slot].nic_set_type("VulcanoFakeNicType")
        else:
            # find type
            self.cli_log_inf("Init NIC Presence, Type")
            regex_dict = {
                NIC_Type.NAPLES100:       MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100,
                NIC_Type.NAPLES100IBM:    MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100IBM,
                NIC_Type.NAPLES100HPE:    MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100HPE,
                NIC_Type.NAPLES100DELL:   MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES100DELL,
                NIC_Type.NAPLES25:        MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25,
                NIC_Type.FORIO:           MFG_DIAG_RE.MFG_NIC_TYPE_FORIO,
                NIC_Type.VOMERO:          MFG_DIAG_RE.MFG_NIC_TYPE_VOMERO,
                NIC_Type.VOMERO2:         MFG_DIAG_RE.MFG_NIC_TYPE_VOMERO2,
                NIC_Type.NAPLES25SWM:     MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWM,
                NIC_Type.NAPLES25OCP:     MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25OCP,
                NIC_Type.NAPLES25SWMDELL: MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWMDELL,
                NIC_Type.NAPLES25SWM833:  MFG_DIAG_RE.MFG_NIC_TYPE_NAPLES25SWM833,
                NIC_Type.ORTANO:          MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO,
                NIC_Type.ORTANO2:         MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2,
                NIC_Type.POMONTEDELL:     MFG_DIAG_RE.MFG_NIC_TYPE_POMONTEDELL,
                NIC_Type.LACONA32DELL:    MFG_DIAG_RE.MFG_NIC_TYPE_LACONA32DELL,
                NIC_Type.LACONA32:        MFG_DIAG_RE.MFG_NIC_TYPE_LACONA32,
                NIC_Type.ORTANO2ADI:      MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2ADI,
                NIC_Type.ORTANO2INTERP:   MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2INTERP,
                NIC_Type.ORTANO2SOLO:     MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2SOLO,
                NIC_Type.ORTANO2ADICR:    MFG_DIAG_RE.MFG_NIC_TYPE_ORTANO2ADICR,
                NIC_Type.GINESTRA_D4:     MFG_DIAG_RE.MFG_NIC_TYPE_GINESTRA_D4,
                NIC_Type.GINESTRA_D5:     MFG_DIAG_RE.MFG_NIC_TYPE_GINESTRA_D5,
                NIC_Type.LENI:            MFG_DIAG_RE.MFG_NIC_TYPE_LENI,
                NIC_Type.LENI48G:         MFG_DIAG_RE.MFG_NIC_TYPE_LENI48G,
                NIC_Type.MALFA:           MFG_DIAG_RE.MFG_NIC_TYPE_MALFA,
                NIC_Type.POLLARA:         MFG_DIAG_RE.MFG_NIC_TYPE_POLLARA,
                NIC_Type.LINGUA:          MFG_DIAG_RE.MFG_NIC_TYPE_LINGUA,
                NIC_Type.GELSOP:          MFG_DIAG_RE.MFG_NIC_TYPE_GELSOP,
                NIC_Type.GELSOX:          MFG_DIAG_RE.MFG_NIC_TYPE_GELSOX,
                NIC_Type.MORTARO:         MFG_DIAG_RE.MFG_NIC_TYPE_MORTARO,
                NIC_Type.SARACENO:        MFG_DIAG_RE.MFG_NIC_TYPE_SARACENO,
            }

            for nic_type in list(regex_dict.keys()):
                match = re.findall(regex_dict[nic_type], self._mgmt_handle.before)
                if match:
                    for idx in range(len(match)):
                        slot = int(match[idx]) - 1
                        if not self._slots_to_skip[slot]:
                            self._nic_prsnt_list[slot] = True
                            self._nic_type_list[slot] = nic_type
                            self._nic_ctrl_list[slot].nic_set_type(nic_type)
                        else:
                            self._nic_prsnt_list[slot] = False
                            self.cli_log_slot_wrn(slot, MTP_DIAG_Report.NIC_DIAG_SLOT_SKIPPED)

        if stage is None or stage == FF_Stage.FF_DL:
            fru_fpo = True
        else:
            fru_fpo = False

        if scanned_fru is None:
            self.cli_log_inf("Init NIC SN, PN")
        else:
            self.cli_log_inf("Init Scanned NIC SN, PN")

        for slot in range(self._slots):
            if not self._nic_prsnt_list[slot]:
                continue

            if scanned_fru is None:
                if not self.mtp_nic_sn_init(slot, fru_fpo):
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    self.mtp_set_nic_status_fail(slot)
                    continue
                if scanned_dpn or scanned_sku:
                    self.mtp_populate_dpn_sku_to_scans(slot, scanned_dpn, scanned_sku)
                nic_type = self.mtp_get_nic_type(slot)
                if nic_type in CTO_MODEL_TYPE_LIST and stage in (FF_Stage.FF_P2C, FF_Stage.FF_4C_H, FF_Stage.FF_4C_L, FF_Stage.FF_SWI):
                    if not self.mtp_nic_dpn_init(slot, fru_fpo):
                        self.mtp_get_nic_err_msg(slot)
                        self.mtp_dump_nic_err_msg(slot)
                        self.mtp_set_nic_status_fail(slot)
                        continue
            else:
                # In ScanDL, use scanned SN, PN as ground truth
                mtp_id = self._id
                key = libmfg_utils.nic_key(slot)
                valid = scanned_fru[key]["VALID"]
                if not valid:
                    self.cli_log_slot_err(slot, "Missing scan for this slot. Could not initialize.")
                    self.mtp_set_nic_status_fail(slot)
                    continue
                pn = self.get_scanned_pn(slot)
                sn = self.get_scanned_sn(slot)
                self.mtp_set_nic_sn(slot, sn)
                self.mtp_set_nic_pn(slot, pn)
                if prog_inter_diagsuc:
                    nic_type = "VulcanoFakeNicType"
                    if pn[0:10] == "102-P12300":
                        nic_type = NIC_Type.MORTARO
                    if pn[0:10] == "102-P12500":
                        nic_type = NIC_Type.SARACENO
                    self._nic_type_list[slot] = nic_type
                    self._nic_ctrl_list[slot].nic_set_type(nic_type)

        # set final nic_type
        for slot in range(self._slots):
            if not self._nic_prsnt_list[slot]:
                continue

            final_nic_type = self.mtp_get_nic_type(slot)
            if self.mtp_check_nic_status(slot) and self.mtp_get_nic_type(slot) == NIC_Type.ORTANO2ADI:
                pn = self.mtp_get_nic_pn(slot)
                final_nic_type = None
                if re.match(PART_NUMBERS_MATCH.ORTANO2ADI_ORC_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADI
                elif re.match(PART_NUMBERS_MATCH.ORTANO2ADI_IBM_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADIIBM
                elif re.match(PART_NUMBERS_MATCH.ORTANO2ADI_MSFT_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADIMSFT
                if final_nic_type:
                    self._nic_type_list[slot] = final_nic_type
                    self._nic_ctrl_list[slot].nic_set_type(final_nic_type)
                else:
                    self.cli_log_slot_err(slot, "{:s} with PN {:s} is not allowed".format(self.mtp_get_nic_type(slot), pn))
                    self.mtp_set_nic_status_fail(slot)
                    continue
            if self.mtp_check_nic_status(slot) and self.mtp_get_nic_type(slot) == NIC_Type.ORTANO2SOLO:
                pn = self.mtp_get_nic_pn(slot)
                final_nic_type = None
                if re.match(PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2SOLO
                elif re.match(PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_L_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2SOLOL
                elif re.match(PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_THS_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2SOLOORCTHS
                elif re.match(PART_NUMBERS_MATCH.ORTANO2SOLO_MSFT_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2SOLOMSFT
                elif re.match(PART_NUMBERS_MATCH.ORTANO2SOLO_S4_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2SOLOS4
                if final_nic_type:
                    self._nic_type_list[slot] = final_nic_type
                    self._nic_ctrl_list[slot].nic_set_type(final_nic_type)
                else:
                    self.cli_log_slot_err(slot, "{:s} with PN {:s} is not allowed".format(self.mtp_get_nic_type(slot), pn))
                    self.mtp_set_nic_status_fail(slot)
                    continue
            if self.mtp_check_nic_status(slot) and self.mtp_get_nic_type(slot) == NIC_Type.ORTANO2ADICR:
                pn = self.mtp_get_nic_pn(slot)
                final_nic_type = None
                if re.match(PART_NUMBERS_MATCH.ORTANO2ADI_CR_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADICR
                elif re.match(PART_NUMBERS_MATCH.ORTANO2ADI_CR_MSFT_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADICRMSFT
                elif re.match(PART_NUMBERS_MATCH.ORTANO2ADI_CR_S4_PN_FMT, pn):
                    final_nic_type = NIC_Type.ORTANO2ADICRS4
                if final_nic_type:
                    self._nic_type_list[slot] = final_nic_type
                    self._nic_ctrl_list[slot].nic_set_type(final_nic_type)
                else:
                    self.cli_log_slot_err(slot, "{:s} with PN {:s} is not allowed".format(self.mtp_get_nic_type(slot), pn))
                    self.mtp_set_nic_status_fail(slot)
                    continue
            if self.mtp_check_nic_status(slot) and self.mtp_get_nic_type(slot) == NIC_Type.GINESTRA_D5:
                pn = self.mtp_get_nic_pn(slot)
                final_nic_type = None
                if re.match(PART_NUMBERS_MATCH.GINESTRA_D5_PN_FMT, pn):
                    final_nic_type = NIC_Type.GINESTRA_D5
                elif re.match(PART_NUMBERS_MATCH.GINESTRA_S4_PN_FMT, pn):
                    final_nic_type = NIC_Type.GINESTRA_S4
                elif re.match(PART_NUMBERS_MATCH.GINESTRA_CIS_PN_FMT, pn):
                    final_nic_type = NIC_Type.GINESTRA_CIS
                if final_nic_type:
                    self._nic_type_list[slot] = final_nic_type
                    self._nic_ctrl_list[slot].nic_set_type(final_nic_type)
                else:
                    self.cli_log_slot_err(slot, "{:s} with PN {:s} is not allowed".format(self.mtp_get_nic_type(slot), pn))
                    self.mtp_set_nic_status_fail(slot)

            if final_nic_type:
                self.cli_log_slot_inf(slot, "Found {:s}".format(final_nic_type))

        # populate OCP adapter info
        for slot in range(self._slots):
            if self.mtp_get_nic_type(slot) == NIC_Type.NAPLES25OCP:
                if not self.mtp_get_nic_ocp_adapter_sn(slot):
                    self.cli_log_slot_err(slot, "OCP Adapter FRU missing")

        return True

    def fst_init_nic_type(self, scanned_fru=None):
        """
            Search lspci for DSCs
            And assign slot # in the order it appears in lspci
        """
        self.cli_log_inf("Init NIC Presence, Type")
        cmd = "lspci -d 1dd8:1004"
        if self._fst_ver == 0x6:
            # Try "lspci -d 1dd8:1004" first
            self.mtp_mgmt_exec_cmd(cmd)
            result = self.mtp_get_cmd_buf()
            bus_list_match = re.findall(r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]+) ", result)
            bus_list_match = list(set(bus_list_match))
            if len(bus_list_match) == 0:
                cmd = "lspci -d 1dd8:1002"

        self.mtp_mgmt_exec_cmd(cmd)
        result = self.mtp_get_cmd_buf()
        bus_list_match = re.findall(r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]+) ", result)
        bus_list_match = list(set(bus_list_match))

        # extra info dump
        cmd = "lspci -d 1dd8: -vvv"
        self.mtp_mgmt_exec_cmd(cmd)

        if len(bus_list_match) == 0:
            self.cli_log_err("No devices found")
            if not scanned_fru:
                return False

        # Map to Scaned slot id by card serial number
        sn2slot = dict()
        phy_present_bus_list = []
        phy_present_slot_list = []
        phy_present_sn_list = []
        fail_slot = list()
        if scanned_fru:
            # build scanned serial number to scanned nic slot id mapping table
            for slot in range(self._slots):
                key = libmfg_utils.nic_key(slot)
                if scanned_fru[key]["VALID"]:
                    sn2slot[scanned_fru[key][bf.SN]] = slot

            rc = True
            for bus in bus_list_match:
                cmd = "lspci -vvv -s {:s} | grep \"Serial number\" --color=never".format(bus)
                if not self.mtp_mgmt_exec_cmd(cmd):
                    rc = False
                result = self.mtp_get_cmd_buf()
                sn_match = re.search("Serial number: *([A-Z0-9]*)", result)
                if sn_match:
                    sn = sn_match.group(1)
                    if sn not in sn2slot:
                        self.cli_log_err("Physical Inserted Card {:s} NOT Scanned, Test Aborting ...".format(sn), level=0)
                        rc = False
                        continue
                    phy_slot = sn2slot[sn]
                    phy_present_slot_list.append(phy_slot)
                    phy_present_bus_list.append(bus)
                    phy_present_sn_list.append(sn)
            if not rc:
                return rc

            # Validate if there is scanned card not physical present
            for sn in sn2slot:
                if sn not in phy_present_sn_list:
                    key = libmfg_utils.nic_key(sn2slot[sn])
                    self.cli_log_err("Scanned Card {:s} {:s} NOT Physical Present, May Because Card Not Bootup, Fail This Card Out and Continue Test".format(key, sn), level=0)
                    self.mtp_set_nic_status_fail(sn2slot[sn], skip_fa=True)
                    self._nic_prsnt_list[sn2slot[sn]] = True
                    fail_slot.append(sn2slot[sn])
        else:
            phy_present_slot_list = list(range(len(bus_list_match)))
            phy_present_bus_list = bus_list_match[:]

        self.cli_log_inf("Found {:d} devices".format(len(bus_list_match)))
        self.cli_log_inf("Init NIC SN, PN")
        for slot, bus in zip(phy_present_slot_list, phy_present_bus_list):
            if not self._slots_to_skip[slot]:
                self._nic_prsnt_list[slot] = True
                self._nic_ctrl_list[slot]._fst_pcie_bus = bus

                cmd = "lspci -vvv -s {:s} | grep \"Serial number\" --color=never".format(bus)
                self.mtp_mgmt_exec_cmd_para(slot, cmd)
                cmd_buf = self.mtp_get_nic_cmd_buf(slot)
                sn_match = re.search("Serial number: *([A-Z0-9]*)", cmd_buf)
                if sn_match:
                    self.mtp_set_nic_sn(slot, sn_match.group(1))

                cmd = "lspci -vvv -s {:s} | grep \"Part number\" --color=never".format(bus)
                self.mtp_mgmt_exec_cmd_para(slot, cmd)
                cmd_buf = self.mtp_get_nic_cmd_buf(slot)
                pn_match = re.search(r"Part number: *([A-Z0-9\-]*)", cmd_buf)
                if pn_match:
                    nic_type = get_product_name_from_pn_and_sn(pn_match.group(1), sn_match.group(1))
                    self.mtp_set_nic_type(slot, nic_type)
                    if nic_type in CAPRI_NIC_TYPE_LIST:
                        self._nic_ctrl_list[slot]._asic_type = "capri"
                    if nic_type in ELBA_NIC_TYPE_LIST:
                        self._nic_ctrl_list[slot]._asic_type = "elba"
                    if nic_type in GIGLIO_NIC_TYPE_LIST:
                        self._nic_ctrl_list[slot]._asic_type = "giglio"
                    if nic_type in SALINA_NIC_TYPE_LIST:
                        self._nic_ctrl_list[slot]._asic_type = "salina"

                if scanned_fru:
                    if not sn_match:
                        self.cli_log_slot_inf(slot, "Could not read SN from PCIe properties...will resort to penctl")
                        self.mtp_set_nic_status_fail(slot, skip_fa=True)
                    if not pn_match or nic_type == NIC_Type.UNKNOWN:
                        self.cli_log_slot_inf(slot, "Could not determine NIC SKU from PCIe properties...will resort to penctl")
                        self.mtp_set_nic_type(slot, NIC_Type.NAPLES100)  # default to naples100 setup steps
                        self._nic_ctrl_list[slot]._asic_type = "capri"
                        self.mtp_set_nic_status_fail(slot, skip_fa=True)
                else:
                    if not sn_match:
                        self.cli_log_slot_inf(slot, "Could not read SN from PCIe properties...will resort to penctl")
                        self.mtp_set_nic_status_fail(slot, skip_fa=True)
                    if not pn_match or nic_type == NIC_Type.UNKNOWN:
                        self.cli_log_slot_inf(slot, "Could not determine NIC SKU from PCIe properties...will resort to penctl")
                        self.mtp_set_nic_type(slot, NIC_Type.NAPLES100)  # default to naples100 setup steps
                        self._nic_ctrl_list[slot]._asic_type = "capri"
                        self.mtp_set_nic_status_fail(slot, skip_fa=True)
        return True

    @parallelize.parallel_nic_using_ssh
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

    def mtp_is_nic_ortano_microsoft(self, slot):
        """
         Differentiate ortano by PN
         - 68-0015: Oracle version -> return False
         - 68-0021: Pensando version -> return True
         - 68-0090: Solo microsoft  -> return True
         - any other -> return False with err msg
        """
        if self._nic_type_list[slot] != NIC_Type.ORTANO2:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for Microsoft")
            return False
        slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for Ortano")
            return False
        microsoft_pn = re.match(PART_NUMBERS_MATCH.ORTANO2_PEN_PN_FMT, slot_pn)
        solo_microsoft_pn = re.match(PART_NUMBERS_MATCH.ORTANO2SOLO_MSFT_PN_FMT, slot_pn)

        if microsoft_pn or solo_microsoft_pn:
            return True
        else:
            return False

    def mtp_is_nic_ortanoadi_oracle(self, slot):
        """
         Differentiate ortano by PN
         - 68-0026: Oracle version -> return True
         - any other -> return False with err msg
        """
        if self._nic_type_list[slot] != NIC_Type.ORTANO2ADI:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for ADI")
            return False
        slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for Ortano ADI")
            return False
        oracle_pn = re.match(PART_NUMBERS_MATCH.ORTANO2ADI_ORC_PN_FMT, slot_pn)
        if oracle_pn:
            return True
        else:
            return False

    def mtp_is_nic_ortanoadi_ibm(self, slot):
        """
         Differentiate ortano by PN
         - 68-0028: Oracle version -> return True
         - any other -> return False with err msg
        """
        if self._nic_type_list[slot] != NIC_Type.ORTANO2ADIIBM:
            self.cli_log_slot_err_lock(slot, "Should not be here - this function only for ADI IBM")
            return False
        slot_pn = self.mtp_get_nic_pn(slot)
        if not slot_pn:
            self.cli_log_slot_err_lock(slot, "Unknown PN for ADI IBM")
            return False
        ibm_pn = re.match(PART_NUMBERS_MATCH.ORTANO2ADI_IBM_PN_FMT, slot_pn)
        if ibm_pn:
            return True
        else:
            return False

    @parallelize.parallel_nic_using_console
    def mtp_nic_erase_board_config(self, slot):
        if not self._nic_ctrl_list[slot].nic_erase_board_config():
            self.cli_log_slot_err(slot, "Erase NIC Board Config failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Erase NIC Board Config")
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_erase_board_config_ssh(self, slot):
        if not self._nic_ctrl_list[slot].nic_erase_board_config_ssh():
            self.cli_log_slot_err(slot, "Erase NIC Board Config failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Erase NIC Board Config")
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_cpld_update_request(self, slot):
        if not self._nic_ctrl_list[slot].nic_cpld_update_request():
            if not self._nic_ctrl_list[slot].nic_check_status():
                self.cli_log_slot_err(slot, "Check NIC Update CPLD request failed")
                self.mtp_get_nic_err_msg(slot)
                return False
            else:
                return False

        self.cli_log_slot_inf(slot, "Need to Update CPLD")
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_nic_console_access(self, slot):
        if not self._nic_ctrl_list[slot].nic_console_access():
            self.cli_log_slot_err(slot, "Get NIC Console Access failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Get NIC Console Access")
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_set_board_config_cert(self, slot, cert_img, directory="/data/"):
        if not self._nic_ctrl_list[slot].nic_set_board_config_cert(cert_img, directory):
            self.cli_log_slot_err(slot, "Set NIC board config cert failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set NIC board config cert")
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_nic_secboot_verify(self, slot):
        if not self._nic_ctrl_list[slot].nic_secboot_verify():
            self.cli_log_slot_err(slot, "NIC secure boot check failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "NIC secure boot check passed")
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_nic_cfg_verify(self, slot):
        if not self._nic_ctrl_list[slot].nic_cfg_verify():
            self.cli_log_slot_err(slot, "NIC cfg compare failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "NIC cfg compare passed")
        return True

    def mtp_get_nic_sw_pn(self, slot):
        if self._nic_sw_pn_list[slot] is None:
            return ""
        return self._nic_sw_pn_list[slot]

    def mtp_set_nic_sw_pn(self, slot, sw_pn):
        self._nic_sw_pn_list[slot] = sw_pn

    def mtp_get_nic_type(self, slot):
        nic_type = self._nic_type_list[slot]
        if not nic_type:
            nic_type = "UNKNOWN_NIC_TYPE"
        return nic_type

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
        nic_type = self._nic_type_list[slot]
        if nic_type is None:
            self.cli_log_slot_err(slot, "NIC Type was not initialized, still None")
            return False
        if nic_type in self._valid_type_list:
            return True
        else:
            self.cli_log_slot_err(slot, "'{:s}' Type not valid for this script folder".format(nic_type))
            return False

    def get_slots_of_type(self, nic_type, nic_list=range(MTP_Const.MTP_SLOT_NUM), except_type=[]):
        if isinstance(except_type, NIC_Type) or isinstance(except_type, str):
            except_type = list(except_type)
        if isinstance(nic_type, NIC_Type) or isinstance(nic_type, str):
            return [slot for slot in nic_list if self.mtp_get_nic_type(slot) == nic_type]
        elif isinstance(nic_type, list) or isinstance(nic_type, tuple):
            nic_type = libmfg_utils.list_subtract(nic_type, except_type)
            return [slot for slot in nic_list if self.mtp_get_nic_type(slot) in nic_type]
        else:
            return []

    def get_slots_of_sku(self, sku="", nic_list=range(MTP_Const.MTP_SLOT_NUM)):
        if not isinstance(sku, str):
            return []
        if not self._nic_ctrl_list:
            return []
        # initialize nic_ctrl sku property
        for slot in nic_list[:]:
            if self._nic_ctrl_list[slot]._sku is None:
                if not self.mtp_nic_sku_init(slot):
                    nic_list.remove(slot)
        return [slot for slot in nic_list if self._nic_ctrl_list[slot]._sku == sku]

    def mtp_nic_pn_valid(self, slot):
        if self._nic_ctrl_list[slot] is None:
            self.cli_log_slot_err(slot, "NIC not initialized")
            return False
        else:
            pn = self._nic_ctrl_list[slot].nic_get_naples_pn()
            if pn is None:
                self.cli_log_slot_err(slot, "No PN detected")
                return False
            # search for this PN in lib/libsku_cfg.py
            for pn_regex in self._valid_pn_list:
                pn_match = re.match(pn_regex, pn)
                if pn_match:
                    return True
            # end of search

            self.cli_log_slot_err(slot, "'{:s}' PN not valid for this script folder".format(pn))
            return False

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_type_test(self, slot):
        type_check = self.mtp_nic_type_valid(slot)
        pn_check = self.mtp_nic_pn_valid(slot)
        return type_check & pn_check

    def mtp_get_nic_sn(self, slot):
        sn = self._nic_sn_list[slot]
        if not sn:
            sn = "UNKNOWN_SN"
        return sn

    def mtp_set_nic_sn(self, slot, sn):
        self.cli_log_slot_inf(slot, "Set SN to {:s}".format(str(sn)))
        self._nic_sn_list[slot] = sn

    def mtp_get_nic_scan_sn(self, slot):
        return self._nic_scan_sn_list[slot]

    def mtp_set_nic_scan_sn(self, slot, sn):
        self.cli_log_slot_inf(slot, "Set Scan SN to {:s}".format(sn))
        self._nic_scan_sn_list[slot] = sn
        self._nic_scan_prsnt_list[slot] = True

    def get_scanned_sn(self, slot):
        return scanning.get_sn(self, slot)

    def get_scanned_mac(self, slot):
        return scanning.get_mac(self, slot)

    def get_scanned_pn(self, slot):
        return scanning.get_pn(self, slot)

    def get_scanned_alom_sn(self, slot):
        return scanning.get_alom_sn(self, slot)

    def get_scanned_alom_pn(self, slot):
        return scanning.get_alom_pn(self, slot)

    def get_scanned_rot_sn(self, slot):
        return scanning.get_rot_sn(self, slot)

    def get_scanned_dpn(self, slot):
        return scanning.get_dpn(self, slot)

    def get_scanned_swpn(self, slot):
        return scanning.get_swpn(self, slot)

    def get_scanned_sku(self, slot):
        return scanning.get_sku(self, slot)

    def get_scanned_ts(self, slot):
        return str(scanning.get_ts(self, slot))

    def mtp_get_nic_dpn(self, slot):
        if self._nic_ctrl_list:
            return self._nic_ctrl_list[slot]._dpn

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_set_nic_diag_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_diag_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with diag failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set NIC default diag boot")
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_set_nic_mainfwa_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_mainfwa_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with mainfwa failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set NIC default mainfwa boot")
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_set_nic_mainfwb_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_mainfwb_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with mainfwb failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set NIC default mainfwb boot")
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_set_nic_extosa_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_extosa_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with extosa failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set NIC default extosa boot")
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_set_nic_extosb_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_extosb_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with extosb failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self.cli_log_slot_inf(slot, "Set NIC default extosb boot")
        return True

    def fst_set_mainfw_boot(self, slot):
        self.cli_log_slot_inf(slot, "Switch to mainfw")
        cmd = "/nic/tools/fwupdate -s mainfwa"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to switch to mainfw")
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_nic_sw_shutdown(self, slot):
        software_pn = self.check_swi_software_image(slot)
        isCloud = self.check_is_cloud_software_image(slot, software_pn)
        isRelC = True if software_pn in ("90-0013-0001", "90-0014-0001", "90-0002-0010", "90-0007-0003", "90-0019-0001", "90-0002-0011", "90-0007-0004") else False
        if not self._nic_ctrl_list[slot].nic_sw_shutdown(cloud=isCloud, isRelC=isRelC):
            self.cli_log_slot_err(slot, "Graceful shut down NIC failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_nic_sw_cleanup_shutdown(self, slot):
        if not self._nic_ctrl_list[slot].nic_sw_cleanup_shutdown():
            self.cli_log_slot_err(slot, "Graceful clean up shut down NIC failed")
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_mgmt_nic_i2c_dump(self, slot):
        if not self._nic_ctrl_list[slot].nic_i2c_dump():
            self.cli_log_slot_err(slot, "Dump i2c value failed")
            return False
        return True

    def mtp_mgmt_set_elba_uboot_env(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_elba_uboot_env(slot):
            self.cli_log_slot_err(slot, "Setup uboot env variables failed")
            return False
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_check_nic_list_status(self, slot):
        return self._nic_ctrl_list[slot].nic_check_status()

    def mtp_check_nic_status(self, slot):
        return self._nic_ctrl_list[slot].nic_check_status()

    def mtp_check_nic_missed_fa(self, slot):
        return self._nic_ctrl_list[slot].nic_missed_fa()

    def mtp_hide_nic_status(self, slot):
        if not self.mtp_check_nic_status(slot):
            self.cli_log_slot_inf(slot, "Masking NIC fail status")
        self._nic_status_before_hide_list[slot] = self._nic_ctrl_list[slot]._nic_status
        self.mtp_clear_nic_status(slot)

    def mtp_unhide_nic_status(self, slot):
        if self._nic_status_before_hide_list[slot] != NIC_Status.NIC_STA_OK:
            self.cli_log_slot_inf(slot, "Unmasking NIC fail status")
        self._nic_ctrl_list[slot].nic_set_status(self._nic_status_before_hide_list[slot])
        self._nic_status_before_hide_list[slot] = NIC_Status.NIC_STA_OK

    # log the diag test history
    def mtp_mgmt_diag_history_disp(self):
        cmd = MFG_DIAG_CMDS().MTP_DIAG_SHIST_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            return False

        return True

    # clear the diag test history

    def mtp_mgmt_diag_history_clear(self):
        cmd = MFG_DIAG_CMDS().MTP_DIAG_CHIST_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            return False

        return True

    @parallelize.parallel_nic_using_console
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

    @parallelize.parallel_nic_using_console
    def mtp_mgmt_set_nic_extdiag_boot(self, slot):
        if not self._nic_ctrl_list[slot].nic_set_extdiag_boot():
            self.cli_log_slot_err(slot, "Set NIC default boot with extdiag failed")
            return False

        self.cli_log_slot_inf(slot, "Set NIC default extdiag boot")
        return True

    @parallelize.parallel_nic_using_nic_test
    def mtp_mgmt_run_test_mtp_para(self, nic_list, test, vmarg, edvt_loop_idx=1):
        if not nic_list:
            return []

        matera_mtp = True if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA) else False

        nic_fail_list = list()
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not matera_mtp:
            if not self.mtp_mgmt_exec_cmd(cmd):
                self.cli_log_err("Execute command {:s} failed".format(cmd))
                return nic_list[:]
        else:
            slot = nic_list[0]
            cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
            if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
                self.cli_log_err("Execute command {:s} failed".format(cmd))
                return nic_list[:]

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.MTP_PARA_TEST_SIG]

        n_vmarg = vmarg
        if vmarg in (Voltage_Margin.high, Voltage_Margin.low):
            partnumber = ""
            for nic_controller in self._nic_ctrl_list:
                if nic_controller._pn:
                    partnumber = nic_controller._pn
                    break
            n_vmarg += libmfg_utils.pick_voltage_margin_percentage(partnumber)
            self.cli_log_inf("Vmargin is: {:s} After Apply Percentage, which Got Using Part Number: {:s}".format(n_vmarg, partnumber), level=0)

        if test == "PRBS_ETH":
            cmd = MFG_DIAG_CMDS().MTP_PARA_PRBS_ETH_TEST_FMT.format(nic_list_param, n_vmarg)
        elif test == "SNAKE_HBM":
            cmd = MFG_DIAG_CMDS().MTP_PARA_SNAKE_HBM_FMT.format(nic_list_param, n_vmarg)
        elif test == "SNAKE_PCIE":
            cmd = MFG_DIAG_CMDS().MTP_PARA_SNAKE_PCIE_FMT.format(nic_list_param, n_vmarg)
        elif test == "SNAKE_ELBA":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)

            if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
                self.cli_log_err("Incorrect test for this NIC TYPE")
                return nic_list[:]
            elif nic_type == NIC_Type.ORTANO2:
                if self.mtp_is_nic_ortano_oracle(slot):
                    cmd = MFG_DIAG_CMDS().MTP_PARA_SNAKE_ELBA_ORC_FMT.format(nic_list_param, n_vmarg)
                    if matera_mtp: cmd = MFG_DIAG_CMDS().MATERA_MTP_PARA_SNAKE_ELBA_ORC_FMT.format(nic_list_param, n_vmarg)
                else:
                    cmd = MFG_DIAG_CMDS().MTP_PARA_SNAKE_ELBA_PEN_FMT.format(nic_list_param, n_vmarg)
                    if matera_mtp: cmd = MFG_DIAG_CMDS().MATERA_MTP_PARA_SNAKE_ELBA_PEN_FMT.format(nic_list_param, n_vmarg)
            elif nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2ADICR):
                cmd = MFG_DIAG_CMDS().MTP_PARA_SNAKE_ELBA_ORC_FMT.format(nic_list_param, n_vmarg)
                if matera_mtp: cmd = MFG_DIAG_CMDS().MATERA_MTP_PARA_SNAKE_ELBA_ORC_FMT.format(nic_list_param, n_vmarg)
            elif nic_type in (NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICRS4):
                cmd = MFG_DIAG_CMDS().MTP_PARA_SNAKE_ELBA_PEN_FMT.format(nic_list_param, n_vmarg)
                if matera_mtp: cmd = MFG_DIAG_CMDS().MATERA_MTP_PARA_SNAKE_ELBA_PEN_FMT.format(nic_list_param, n_vmarg)
            elif nic_type == NIC_Type.LACONA32DELL or nic_type == NIC_Type.LACONA32:
                cmd = MFG_DIAG_CMDS().MTP_PARA_SNAKE_LACONA_FMT.format(nic_list_param, n_vmarg)
                if matera_mtp: cmd = MFG_DIAG_CMDS().MATERA_MTP_PARA_SNAKE_LACONA_FMT.format(nic_list_param, n_vmarg)
            elif nic_type in GIGLIO_NIC_TYPE_LIST:
                cmd = MFG_DIAG_CMDS().MTP_PARA_SNAKE_GIGLIO_FMT.format(nic_list_param, n_vmarg)
                if matera_mtp: cmd = MFG_DIAG_CMDS().MATERA_MTP_PARA_SNAKE_GIGLIO_FMT.format(nic_list_param, n_vmarg)
            else:
                cmd = MFG_DIAG_CMDS().MTP_PARA_SNAKE_ELBA_FMT.format(nic_list_param, n_vmarg)
                if matera_mtp: cmd = MFG_DIAG_CMDS().MATERA_MTP_PARA_SNAKE_ELBA_FMT.format(nic_list_param, n_vmarg)

            # when running EDVT, cover both external loopback and internal loopback
            if RUNNING_EDVT:
                if edvt_loop_idx % 2 == 0:
                    self.cli_log_inf("Running EDVT of Test: {:s} at Iteration {:d} with external loopback".format(test, edvt_loop_idx), level=0)
                else:
                    self.cli_log_inf("Running EDVT of Test: {:s} at Iteration {:d} with internal loopback".format(test, edvt_loop_idx), level=0)
                    cmd += " -int_lpbk"
                    if matera_mtp: cmd += " True"
            else:
                # 2C/4C = internal loopback
                if vmarg != Voltage_Margin.normal:
                    cmd += " -int_lpbk"
                    if matera_mtp: cmd += " True"

        elif test == "ETH_PRBS":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)
            if nic_type not in ELBA_NIC_TYPE_LIST and nic_type not in GIGLIO_NIC_TYPE_LIST:
                self.cli_log_err("Incorrect test for this NIC TYPE")
                return nic_list[:]
            else:
                if nic_type in ELBA_NIC_TYPE_LIST:
                    cmd = MFG_DIAG_CMDS().MTP_PARA_PRBS_ETH_ELBA_FMT.format(nic_list_param, n_vmarg)
                elif nic_type in GIGLIO_NIC_TYPE_LIST:
                    cmd = MFG_DIAG_CMDS().MTP_PARA_PRBS_ETH_GIGLIO_FMT.format(nic_list_param, n_vmarg)
                # when running EDVT, cover both external loopback and internal loopback
                if RUNNING_EDVT:
                    if edvt_loop_idx % 2 == 0:
                        self.cli_log_inf("Running EDVT of Test: {:s} at Iteration {:d} with external loopback".format(test, edvt_loop_idx), level=0)
                    else:
                        self.cli_log_inf("Running EDVT of Test: {:s} at Iteration {:d} with internal loopback".format(test, edvt_loop_idx), level=0)
                        cmd += " -int_lpbk"
                else:
                    # 2C/4C = internal loopback
                    if vmarg != Voltage_Margin.normal:
                        cmd += " -int_lpbk"
        elif test == "ARM_L1":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)
            if nic_type == NIC_Type.POMONTEDELL:
                cmd = MFG_DIAG_CMDS().MTP_PARA_ARM_L1_ELBA_POMONTEDELL_FMT.format(nic_list_param, n_vmarg)
            elif nic_type in (NIC_Type.LACONA32, NIC_Type.LACONA32DELL):
                cmd = MFG_DIAG_CMDS().MTP_PARA_ARM_L1_ELBA_LACONA_FMT.format(nic_list_param, n_vmarg)
            elif nic_type in ARM_L1_MODE_HOD_1100 or (nic_type == NIC_Type.ORTANO2 and self.mtp_is_nic_ortano_microsoft(slot)):
                cmd = MFG_DIAG_CMDS().MTP_PARA_ARM_L1_ELBA_FMT.format(nic_list_param, n_vmarg, "hod_1100")
            else:
                cmd = MFG_DIAG_CMDS().MTP_PARA_ARM_L1_ELBA_FMT.format(nic_list_param, n_vmarg, "hod")
        elif test == "PCIE_PRBS":
            slot = nic_list[0]
            nic_type = self.mtp_get_nic_type(slot)
            if matera_mtp:
                cmd = MFG_DIAG_CMDS().MATERA_MTP_PARA_PCIE_PRBS_FMT.format(nic_list_param, n_vmarg, "PRBS31")
            else:
                cmd = MFG_DIAG_CMDS().MTP_PARA_PCIE_PRBS_FMT.format(nic_list_param, n_vmarg, "PRBS31")

        elif test == "DDR_BIST":
            cmd = MFG_DIAG_CMDS().MTP_PARA_DDR_BIST_ELBA_FMT.format(nic_list_param, n_vmarg)
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return nic_list[:]

        if matera_mtp:
            slot = nic_list[0]
            if not self.mtp_mgmt_exec_cmd_para(slot, cmd, timeout= MTP_Const.MTP_PARA_TEST_TIMEOUT, sig_list=sig_list):
                self.cli_log_err("Run MTP Parallel Test {:s} Failed".format(test))
                return nic_list[:]

            cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        else:
            if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_TEST_TIMEOUT):
                self.cli_log_err("Run MTP Parallel Test {:s} Failed".format(test))
                return nic_list[:]

            cmd_buf = self.mtp_get_cmd_buf()
            buf_before_sig = self.mtp_get_cmd_buf_before_sig()
            self.nic_semi_parallel_log(nic_list, buf_before_sig)

        match = re.findall(r"Slot (\d+) ?: +(\w+)", cmd_buf)
        rslt_list = [False] * MTP_Const.MTP_SLOT_NUM  # fail any slots whose result is not captured
        for _slot, rslt in match:
            slot = int(_slot) - 1
            if (rslt == "PASS" or rslt == "PASSED"):
                rslt_list[slot] = True

        for slot in nic_list:
            if not rslt_list[slot]:
                if slot not in nic_fail_list:
                    nic_fail_list.append(slot)

        return nic_fail_list

    @parallelize.parallel_nic_using_nic_test
    def mtp_mgmt_run_test_mtp_para_with_oneline_summary(self, nic_list, test, vmarg):
        if not nic_list:
            return []

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return nic_list

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)

        n_vmarg = vmarg
        if vmarg in (Voltage_Margin.high, Voltage_Margin.low):
            partnumber = ""
            for nic_controller in self._nic_ctrl_list:
                if nic_controller._pn:
                    partnumber = nic_controller._pn
                    break
            n_vmarg += libmfg_utils.pick_voltage_margin_percentage(partnumber)
            self.cli_log_inf("Vmargin is: {:s} After Apply Percentage, which Got Using Part Number: {:s}".format(n_vmarg, partnumber), level=0)

        if test == "RMII_LINKUP":
            cmd = MFG_DIAG_CMDS().MTP_NCSI_RMII_LINKUP_FMT.format(nic_list_param, n_vmarg)
            sig_list = ["rmii_linkup_test done"]
        elif test == "UART_LPBACK":
            cmd = MFG_DIAG_CMDS().MTP_NCSI_UART_LPBACK_FMT.format(nic_list_param, n_vmarg)
            sig_list = ["uart_loopback_test done"]
        else:
            self.cli_log_err("Unknown MTP Parallel Test {:s}".format(test))
            return nic_list

        if not self.mtp_mgmt_exec_cmd(cmd, sig_list, timeout=MTP_Const.MTP_PARA_TEST_TIMEOUT):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return nic_list

        self.nic_semi_parallel_log(nic_list, self.mtp_get_cmd_buf_before_sig())

        nic_fail_list = list()
        ret = "SUCCESS"
        if "failed;" in self.mtp_get_cmd_buf():
            match = re.search("failed slots: *([0-9,]+)", self.mtp_get_cmd_buf())
            if match:
                for slot_base_1 in libmfg_utils.expand_range_of_numbers(match.group(1), range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot_base_1 - 1
                    if slot not in nic_fail_list:
                        nic_fail_list.append(slot)
                        ret = "FAIL"

        return nic_fail_list

    def mtp_mgmt_get_test_result(self, cmd, test):
        if not self.mtp_mgmt_exec_cmd(cmd):
            return MTP_DIAG_Error.NIC_DIAG_TIMEOUT

        # Test    Error code, SUCCESS means pass
        match = re.findall(r"{:s} +([A-Za-z0-9_]+)".format(test), self.mtp_get_cmd_buf())
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

    def mtp_run_diag_test_seq(self, slot, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None):
        # init command
        if init_cmd:
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(init_cmd):
                err_msg = self.mtp_get_nic_cmd_buf(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        if not self._nic_ctrl_list[slot].mtp_exec_cmd(diag_cmd, timeout=MTP_Const.DIAG_SEQ_TEST_TIMEOUT):
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
        if test == "L1" and ret == "TIMEOUT":
            self.mtp_single_j2c_lock()
            self.mtp_mgmt_jtag_rst()
            self.mtp_single_j2c_unlock()

        return [ret, err_msg_list]

    def mtp_mgmt_jtag_rst(self):
        self.cli_log_inf("Reset the MTP JTAG Interface", level=0)
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DSHELL_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        cmd = MFG_DIAG_CMDS().MTP_DSP_STOP_FMT
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        cmd = "cleantcl.sh"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        cmd = MFG_DIAG_CMDS().MTP_DSP_START_FMT
        sig_list = [MFG_DIAG_SIG.MTP_DSP_START_OK_SIG]
        if not self.mtp_mgmt_exec_cmd(cmd, sig_list):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            return False

        time.sleep(MTP_Const.MTP_DIAGMGR_DELAY)

        self.cli_log_inf("Reset the MTP JTAG Interface complete", level=0)
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_board_config(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            if nic_type == NIC_Type.ORTANO2:
                if self.mtp_is_nic_ortano_oracle(slot):
                    preset_config = "5"
                else:
                    preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2ADI:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2ADIIBM:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2ADIMSFT:
                preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2INTERP:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2SOLO:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2SOLOL:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2SOLOORCTHS:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2SOLOMSFT:
                preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2SOLOS4:
                preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2ADICR:
                preset_config = "5"
            elif nic_type == NIC_Type.ORTANO2ADICRMSFT:
                preset_config = "8"
            elif nic_type == NIC_Type.ORTANO2ADICRS4:
                preset_config = "8"
            elif nic_type == NIC_Type.POMONTEDELL:
                preset_config = "1"
            elif nic_type in (NIC_Type.LACONA32, NIC_Type.LACONA32DELL):
                preset_config = "18"
            elif nic_type in GIGLIO_NIC_TYPE_LIST:
                preset_config = "8"
            else:
                self.cli_log_slot_err(slot, "Board config not supported on this NIC")
                return False

        else:
            self.cli_log_slot_err(slot, "Board config not supported on this NIC")
            return False

        if not self._nic_ctrl_list[slot].nic_set_board_config(preset_config):
            self.cli_log_slot_err(slot, "Set board config failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_nic_assign_board_id(self, slot, partNumber=None, verifyOnly=False):
        """
        Assign board id to provided slot, according retrieved CPLD ID and passed in part number.
        """

        if partNumber is None:
            self.cli_log_slot_err_lock(slot, "Please Provide Part Number")
            return False
        if not isinstance(partNumber, str):
            self.cli_log_slot_err_lock(slot, "Please Specify Part Number with String Format")
            return False

        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Failed to retrieve CPLD ID info")
            return False
        cpldId = nic_cpld_info[2]
        partNumberIn6Digits = "-".join(partNumber.split('-')[0:2]) if "-" in partNumber[0:6] else partNumber[0:6]
        (boardId, pciSubSysId) = PN_CPLD2BOARDID_PCI_SUBSYS_ID.get((partNumberIn6Digits, cpldId), (None, None))
        if not boardId:
            self.cli_log_slot_err_lock(slot, "Failed find board ID for PN {:s} and CPLD {:s}".format(partNumber, cpldId))
            return False

        if not self._nic_ctrl_list[slot].nic_assign_board_id(boardId, readOnly=verifyOnly):
            self.cli_log_slot_err_lock(slot, "Assign Board ID Failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_zephyr_boardid_pcisubsystemid_write(self, slot, stage=None):
        """
        Write board id from Zephyr console interface
        SWI will using SKU to board_id mapping
        Default using (partnumber, cpldid) to board_id mapping
        """

        partNumber = self.get_scanned_pn(slot)
        if partNumber is None:
            self.cli_log_slot_err_lock(slot, "Part Number Not set to MTP ctrl instance")
            return False
        partNumberIn6Digits = "-".join(partNumber.split('-')[0:2]) if "-" in partNumber[0:6] else partNumber[0:6]

        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Failed to retrieve CPLD ID info")
            return False
        cpldId = nic_cpld_info[2]
        (boardId, pciSubSysId) = PN_CPLD2BOARDID_PCI_SUBSYS_ID.get((partNumberIn6Digits, cpldId), (None, None))
        if stage == FF_Stage.FF_SWI:
            sku = self.get_scanned_sku(slot)
            (boardId, pciSubSysId) = SKU2BOARDID_PCI_SUBSYS_ID.get(sku, (None, None))
        if not self._nic_ctrl_list[slot].zephyr_assign_board_id_and_pci_subsystemid(boardId, pciSubSysId):
            self.cli_log_slot_err_lock(slot, "Zephyr Assign Board ID Failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_suc_version_read_check(self, slot, stage=None):
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

        nic_type = self.mtp_get_nic_type(slot)
        partNumber = self.get_scanned_pn(slot)
        if partNumber is None:
            self.cli_log_slot_err_lock(slot, "Part Number Not set to MTP ctrl instance")
            return False
        partNumberIn6Digits = "-".join(partNumber.split('-')[0:2]) if "-" in partNumber[0:6] else partNumber[0:6]

        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Failed to retrieve CPLD ID info")
            return False
        cpldId = nic_cpld_info[2]
        (boardId, pciSubSysId) = PN_CPLD2BOARDID_PCI_SUBSYS_ID.get((partNumberIn6Digits, cpldId), (None, None))
        if stage == FF_Stage.FF_SWI:
            sku = self.get_scanned_sku(slot)
            (boardId, pciSubSysId) = SKU2BOARDID_PCI_SUBSYS_ID.get(sku, (None, None))
        expected_suc_timestamp = image_control.get_suc_diag_img(self, slot, stage)["timestamp"]
        if stage == FF_Stage.FF_SWI:
            expected_suc_timestamp = image_control.get_suc_sw_img(self, slot, stage)["suctimestamp"]
        cpld_ver = f'{int(nic_cpld_info[0], 16)}.{int(nic_cpld_info[3], 16)}'
        if not self._nic_ctrl_list[slot].uc_zephyr_version_check(nic_type, boardId, expected_suc_timestamp, cpld_ver, stage):
            self.cli_log_slot_err_lock(slot, "Suc Zephyr Version Check Failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_suc_fru_dump_check(self, slot):
        """
        execute suc shell fru dump command, verify the contents with eeutil -disp
        command example:
            suc:~$ frudump raw  ==> for log only
            suc:~$ frudump parsed   ==> for contents compare
        """

        if not self._nic_ctrl_list[slot].suc_fru_dump_check():
            self.cli_log_slot_err_lock(slot, "Suc EEUTIL FRU compare Failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_vulcano_version_read_check(self, slot, stage=None):
        """
        execute vulcano zephyr shell 'show version' command, verify Build time and CPLD version
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

        nic_type = self.mtp_get_nic_type(slot)
        partNumber = self.get_scanned_pn(slot)
        if partNumber is None:
            self.cli_log_slot_err_lock(slot, "Part Number Not set to MTP ctrl instance")
            return False
        partNumberIn6Digits = "-".join(partNumber.split('-')[0:2]) if "-" in partNumber[0:6] else partNumber[0:6]

        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Failed to retrieve CPLD ID info")
            return False
        cpldId = nic_cpld_info[2]
        (boardId, pciSubSysId) = PN_CPLD2BOARDID_PCI_SUBSYS_ID.get((partNumberIn6Digits, cpldId), (None, None))
        if stage == FF_Stage.FF_SWI:
            sku = self.get_scanned_sku(slot)
            (boardId, pciSubSysId) = SKU2BOARDID_PCI_SUBSYS_ID.get(sku, (None, None))

        expected_soc_timestamp = image_control.get_suc_sw_img(self, slot, stage)["soctimestamp"]
        expected_soc_ver = image_control.get_suc_sw_img(self, slot, stage)["socver"]
        # set cpld_ver to None to skip version check, as sw bundle will overwrite cpld
        #cpld_ver = f'{int(nic_cpld_info[0], 16)}.{int(nic_cpld_info[3], 16)}'
        cpld_ver = None
        if not self._nic_ctrl_list[slot].zephyr_vulcano_version_check(expected_soc_ver, expected_soc_timestamp, cpld_ver):
            self.cli_log_slot_err_lock(slot, "Vulcano Zephyr Version Check Failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_vulcano_fru_dump_check(self, slot):
        """
        execute vulcano shell fru dump command, verify the contents with eeutil -disp
        command example:
            vulcano:~$ frudump raw  ==> for log only
            vulcano:~$ frudump parsed   ==> for contents compare
        """

        if not self._nic_ctrl_list[slot].vulcano_shell_fru_dump_check():
            self.cli_log_slot_err_lock(slot, "Vulcano and EEUTIL FRU compare Failed")
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_zephyr_debug_update_firmware(self, slot, bootfw='mainfwa', bootfw_verify=True):
        """
            update - Update commands
            Subcommands:
            firmware     :Configure system boot firmware selection
                            Usage:
                            debug update firmware --next-boot-image <mainfwa|mainfwb|goldfw>
            secure-boot  :Configure CPLD secure boot
                            Usage:
                                debug update secure-boot <enable|disable>
            secure       :secure debug commands to set boot alternate partition or ar
                          counter for bl1 and pentrust
        """

        if bootfw not in ('mainfwa', 'mainfwb', 'goldfw'):
            self.cli_log_slot_err_lock(slot, "Please provide correct Zephyr FW 'mainfwa' 'mainfwb' or 'goldfw'")
            return False

        if not self._nic_ctrl_list[slot].zephyr_debug_update_firmware(bootfw, bootfw_verify):
            self.cli_log_slot_err_lock(slot, "Zephyr Set zephyr bootfw failed")
            self.mtp_get_nic_err_msg(slot)
            return False
        return True

    def mtp_nic_uc_zephyr_cpld_update(self, slot, cpld_img_file, partition='0', dl_step=True):
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

        nic_type = self.mtp_get_nic_type(slot)

        if nic_type not in VULCANO_NIC_TYPE_LIST:
            self.cli_log_slot_err(slot, "This cpld update function not meant for this card {:s}".format(nic_type))
            return False

        if dl_step:
            stage = FF_Stage.FF_DL
        else:
            stage = FF_Stage.FF_SWI

        nic_cpld_info = self._nic_ctrl_list[slot].nic_get_cpld()
        if not nic_cpld_info:
            self.cli_log_slot_err_lock(slot, "Program NIC CPLD failed, can not retrieve CPLD info")
            return False
        cur_ver = nic_cpld_info[0]
        cur_timestamp = nic_cpld_info[1]

        expected_version = image_control.get_cpld(self, slot, stage)["version"]
        expected_timestamp = image_control.get_cpld(self, slot, stage)["timestamp"]

        if cur_ver == expected_version and cur_timestamp == expected_timestamp:
            self.cli_log_slot_inf_lock(slot, "NIC CPLD is up-to-date, But Program Again")

        support_partitions = ("0", "1")
        if partition not in support_partitions:
            self.cli_log_slot_err_lock(slot, "Please provide correct cpld partion , it should be in {:d}".format(str(support_partitions)))
            return False
        if not self._nic_ctrl_list[slot].uc_zephyr_cpld_update(cpld_img_file, partition):
            self.cli_log_slot_err_lock(slot, "Program CPLD Failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        self._nic_ctrl_list[slot].nic_require_cpld_refresh(True)

        return True

    def mtp_nic_uc_zephyr_boot_check(self, slot, monitor_timeout=40, stage=None):
        """
        sample microcontroller power cycle output as following:
            [00:00:00.000,000] <inf> part_core## Gelso bringup app loaded ##
            Boot info:
            magic=0x464e4942 size=40
            bootloader_source=1 bootloader_version=0x0000000300010000
            runtime_source=1
            Boot control:
            magic=0x4c544342 size=16
            target=0 tries_remaining=0
            ## PLDM is OK ##
            ## PFM Status ##
            pfm_swapped=0
            PFM_A seq_no=0. rc=0
            PFM_B seq_no=0. rc=0
            ## BFM status ##
            bfm_swapped=0
            BFM_A seq_no=1. rc=0
            BFM_B seq_no=0. rc=0
            : partition_init: with 5 devices, mask: 0x0000001f
            [00:00:00.004,000] <inf> usbd_cdc_acm: rx_en: trigger rx_fifo_work
            [00:00:00.004,000] <inf> usbd_cdc_acm: USB configuration is not enabled or suspended
            *** Booting Zephyr OS build v4.1.0 ***
            [00:00:00.004,000] <inf> usbd_init: interface 0 alternate 0
            [00:00:00.004,000] <inf> usbd_init:     ep 0x81 mps 0x0010 interface ep-bm 0x00020000
            [00:00:00.004,000] <inf> usbd_init: interface 1 alternate 0
            [00:00:00.004,000] <inf> usbd_init:     ep 0x82 mps 0x0200 interface ep-bm 0x00040000
            ............
        """
        def mtp_2nd_mgmt_exec_cmd(mtp_mgmt_ctrl, handle, cmd, sig_list=[], timeout=MTP_Const.OS_CMD_DELAY):

            rc = True
            handle.sendline(cmd)
            cmd_before = ""
            buf_before_sig = ""
            for sig in sig_list:
                idx = libmfg_utils.mfg_expect(handle, [sig], timeout)
                buf_before_sig += handle.before
                if idx < 0:
                    rc = False
                    cmd_before = handle.before
                    break
            idx = libmfg_utils.mfg_expect(handle, ["$"], timeout)
            # signature match fails
            if not rc:
                mtp_mgmt_ctrl.mtp_dump_err_msg(cmd_before)
                return (False, cmd_before)
            elif idx < 0:
                mtp_mgmt_ctrl.mtp_dump_err_msg(handle.before)
                return (False, buf_before_sig + handle.before)
            else:
                cmd_output = buf_before_sig + handle.before
                # print(cmd_buf + "$")

            # get command return code
            handle.sendline("echo $?")
            idx = libmfg_utils.mfg_expect(handle, ["$"], 3)
            idx = libmfg_utils.mfg_expect(handle, ["$"], 5)
            if idx < 0:
                mtp_mgmt_ctrl.cli_log_slot_wrn("Failed to Get Command Return Value" + handle.before)
                return (True, cmd_output)

            cmd_return_code = handle.before.splitlines()[2].strip("\r").strip()
            if cmd_return_code != '0':
                return (False, cmd_output + " echo $?" + handle.before)

            return (True, cmd_output)

        def power_cycle_slot_in_2nd_session(mtp_mgmt_ctrl, second_handle, slot):

            mtp_mgmt_ctrl.cli_log_inf_lock("Power Cylce slot slot {:d} in 2nd session".format(slot + 1) , level=0)
            result = False
            cmd = "turn_on_slot.sh off {:d}; sleep 10;turn_on_slot.sh on {:d}".format(slot + 1, slot +1)
            cmd_result = mtp_2nd_mgmt_exec_cmd(mtp_mgmt_ctrl, second_handle, cmd, timeout=30)
            if not cmd_result[0]:
                mtp_mgmt_ctrl.cli_log_err_lock("command {:s} on 2nd mtp mgmt session failed".format(cmd), level=0)
                mtp_mgmt_ctrl.cli_log_err_lock(cmd_result[1], level=0)
                return result
            result = True
            return result

        power_cycle_handle = self.mtp_session_create()
        boot_check_threads = []
        t1 = threading.Thread(target=self._nic_ctrl_list[slot].uc_get_zephyr_booting_msg, args=(monitor_timeout,))
        boot_check_threads.append(t1)
        t2 = threading.Thread(target=power_cycle_slot_in_2nd_session, args=(self, power_cycle_handle, slot))
        boot_check_threads.append(t2)

        for thread in boot_check_threads:
            thread.start()
            time.sleep(5)
        for thread in boot_check_threads:
            thread.join()

        power_cycle_handle.close()

        if "suc:~$".lower() not in self.mtp_get_nic_cmd_buf(slot).lower():
            self.cli_log_slot_err_lock(slot, "uc zephyr boot check Failed")
            self.mtp_get_nic_err_msg(slot)
            return False
        return True

    def mtp_nic_vulcano_boot_check(self, slot, monitor_timeout=60, stage=None):
        """
            Trying to boot from NOR
            TPL: Boot Device: B

            U-Boot SPL 2024.10-g84a590cd0c59 (Dec 06 2025 - 22:23:35 -0800)
            CPU Clock div is set to 07
            Trying to boot from NOR
            SPL: Boot Device: B


            U-Boot 2024.10-g84a590cd0c59 (Dec 06 2025 - 22:23:35 -0800)

            Model: Vulcano Gelso
            DRAM:  32 MiB
            Core:  21 devices, 11 uclasses, devicetree: separate
            Loading Environment from <NULL>... OK
            In:    serial@F0000
            Out:   serial@F0000
            Err:   serial@F0000
            U-Boot: Boot Device: B
            Auto-boot: FIT image detected at 0x711a1000
            Hit any key to stop autoboot:  0
            ## Loading kernel from FIT Image at 711a1000 ...
            Using 'vulcano-asic' configuration
            Trying 'kernel' kernel subimage
                Description:  AINIC Zephyr
                Type:         Kernel Image
                Compression:  uncompressed
                Data Start:   0x711a10c4
                Data Size:    4041496 Bytes = 3.9 MiB
                Architecture: RISC-V
                OS:           U-Boot
                Load Address: 0x810171c000
                Entry Point:  0x810171c000
                Hash algo:    crc32
                Hash value:   edec13f3
            Verifying Hash Integrity ... crc32+ OK
            Loading Kernel Image to 810171c000
            .......
            vulcano:~$
        """
        def mtp_2nd_mgmt_exec_cmd(mtp_mgmt_ctrl, handle, cmd, sig_list=[], timeout=MTP_Const.OS_CMD_DELAY):

            rc = True
            handle.sendline(cmd)
            cmd_before = ""
            buf_before_sig = ""
            for sig in sig_list:
                idx = libmfg_utils.mfg_expect(handle, [sig], timeout)
                buf_before_sig += handle.before
                if idx < 0:
                    rc = False
                    cmd_before = handle.before
                    break
            idx = libmfg_utils.mfg_expect(handle, ["$"], timeout)
            # signature match fails
            if not rc:
                mtp_mgmt_ctrl.mtp_dump_err_msg(cmd_before)
                return (False, cmd_before)
            elif idx < 0:
                mtp_mgmt_ctrl.mtp_dump_err_msg(handle.before)
                return (False, buf_before_sig + handle.before)
            else:
                cmd_output = buf_before_sig + handle.before
                # print(cmd_buf + "$")

            # get command return code
            handle.sendline("echo $?")
            idx = libmfg_utils.mfg_expect(handle, ["$"], 3)
            idx = libmfg_utils.mfg_expect(handle, ["$"], 5)
            if idx < 0:
                mtp_mgmt_ctrl.cli_log_slot_wrn("Failed to Get Command Return Value" + handle.before)
                return (True, cmd_output)

            cmd_return_code = handle.before.splitlines()[2].strip("\r").strip()
            if cmd_return_code != '0':
                return (False, cmd_output + " echo $?" + handle.before)

            return (True, cmd_output)

        def power_cycle_slot_in_2nd_session(mtp_mgmt_ctrl, second_handle, slot):

            mtp_mgmt_ctrl.cli_log_inf_lock("Power Cylce slot slot {:d} in 2nd session".format(slot + 1) , level=0)
            result = False
            cmd = "turn_on_slot.sh off {:d}; sleep 10;turn_on_slot.sh on {:d}".format(slot + 1, slot +1)
            cmd_result = mtp_2nd_mgmt_exec_cmd(mtp_mgmt_ctrl, second_handle, cmd, timeout=30)
            if not cmd_result[0]:
                mtp_mgmt_ctrl.cli_log_err_lock("command {:s} on 2nd mtp mgmt session failed".format(cmd), level=0)
                mtp_mgmt_ctrl.cli_log_err_lock(cmd_result[1], level=0)
                return result
            result = True
            return result

        power_cycle_handle = self.mtp_session_create()
        boot_check_threads = []
        t1 = threading.Thread(target=self._nic_ctrl_list[slot].uc_get_vulcano_booting_msg, args=(monitor_timeout,))
        boot_check_threads.append(t1)
        t2 = threading.Thread(target=power_cycle_slot_in_2nd_session, args=(self, power_cycle_handle, slot))
        boot_check_threads.append(t2)

        for thread in boot_check_threads:
            thread.start()
            time.sleep(5)
        for thread in boot_check_threads:
            thread.join()

        power_cycle_handle.close()

        if stage == FF_Stage.FF_SWI:
            if "vulcano:~$".lower() not in self.mtp_get_nic_cmd_buf(slot).lower():
                self.cli_log_slot_err_lock(slot, "vulcano boot check Failed")
                self.mtp_get_nic_err_msg(slot)
                return False
        return True


    @parallelize.parallel_nic_using_ssh
    def mtp_nic_i2c_device_screening(self, slot):
        """
        Run a bunch of I2C related commands, make sure they are work
        """

        if not self._nic_ctrl_list[slot].i2c_device_screening():
            self.cli_log_slot_err_lock(slot, "I2C Device Screening Failed")
            self.mtp_get_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_cpld_register_dump_check(self, slot, check=None):
        """
        dump all registers, and compare it's value if check parameter given 
        check parameter give with address to value dict
        """

        if not self._nic_ctrl_list[slot].cpld_register_dump_check(check):
            self.cli_log_slot_err_lock(slot, "CPLD Register dump and check Failed")
            self.mtp_get_nic_err_msg(slot)
            return False
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_vul_suc_i2c_device_test(self, slot, timeout=300):
        """
        nic_test_vul.py suc_i2c_ds4424_test -slot <slot> -index <index>
        nic_test_vul.py suc_i2c_tmp451_test -slot <slot>
        nic_test_vul.py suc_i2c_rc22308_test -slot <slot>
        """

        if not self._nic_ctrl_list[slot].vulcano_suc_i2c_device_test():
            self.cli_log_slot_err_lock(slot, "Vucano Suc I2C Device test Failed")
            self.mtp_get_nic_err_msg(slot)
            return False
        return True

    def mtp_nic_vul_qspi_erase(self, slot):
        if not self._nic_ctrl_list[slot].vul_nic_erase_qspi():
            self.cli_log_slot_err_lock(slot, "Erase NIC QSPI failed")
            self.mtp_dump_nic_err_msg(slot)
            return False
        return True

    def mtp_nic_uc_image_program(self, slot, cmd_format, uc_img_file, override_fd_descriptors=False):
        """
        lsusb
        lsusb -v -d 0438:0001
        lsusb -v -d 0438:0001 | grep -E 'iSerial|iProduct|iManufacturer'
        ./test_all.py --board-type AinicSuc --usb B4A7BA2756444B028820F0E180B0F82E:3 --print-hdrs --print-msgs -vvv --util pldmfwpkg=/home/diag/two_comp_gelso_v0_1_0_0.pldm --test-cases PldmFwUpdateSingleFDUpdateFlow
        """

        if not self._nic_ctrl_list[slot].uc_image_program(cmd_format, uc_img_file, override_fd_descriptors):
            self.cli_log_slot_err_lock(slot, "Program uC image Failed")
            self.mtp_get_nic_err_msg(slot)
            return False
        return True

    def mtp_uc_usb_resacn(self, slots_list, retry=1):
        """
        device 0000:06:00.3 is frist 6 slots
        device 0000:06:00.1 is the last 4 slots
        echo 1 | sudo tee /sys/bus/pci/devices/0000:06:00.3/remove; sleep 1; echo 1 | sudo tee /sys/bus/pci/rescan
        echo 1 | sudo tee /sys/bus/pci/devices/0000:06:00.1/remove; sleep 1; echo 1 | sudo tee /sys/bus/pci/rescan
        """

        card_path_dict = dict()
        card_path_dict[1] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-1"
        card_path_dict[2] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-2"
        card_path_dict[3] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-3"
        card_path_dict[4] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-4"
        card_path_dict[5] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-5"
        card_path_dict[6] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-6"
        card_path_dict[7] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.1/usb1/1-1/"
        card_path_dict[8] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.1/usb1/1-2/"
        card_path_dict[9] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.1/usb1/1-3/"
        card_path_dict[10] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.1/usb1/1-4/"

        for i in range(retry):
            failed_slots = []
            cmd = "echo 1 | sudo tee /sys/bus/pci/devices/0000:06:00.3/remove; sleep 1; echo 1 | sudo tee /sys/bus/pci/rescan"
            if not self.mtp_mgmt_exec_sudo_cmd(cmd):
                self.cli_log_err("Unable to send uC usb rescan command for slot1-6")
                return False
            cmd = "echo 1 | sudo tee /sys/bus/pci/devices/0000:06:00.1/remove; sleep 1; echo 1 | sudo tee /sys/bus/pci/rescan"
            if not self.mtp_mgmt_exec_sudo_cmd(cmd):
                self.cli_log_err("Unable to send uC usb rescan command for slot1-6")
                return False
            time.sleep(30)
            all_slots_usb_exist = True
            for slot in slots_list:
                slot += 1
                if not os.path.exists(card_path_dict[slot]):
                    self.cli_log_wrn(f"Slot { slot} USB device {card_path_dict[slot]} not ready ")

                    failed_slots.append(slot)
                    all_slots_usb_exist = False
            if all_slots_usb_exist:
                break

        for slot in failed_slots:
            self.cli_log_err(f"Slot { slot} USB device {card_path_dict[slot]} not ready after {retry} retry ")

        if all_slots_usb_exist:
            return []
        else:
            return slots_list

    @parallelize.parallel_nic_using_console
    def mtp_program_nic_goldfw_salina(self, slot, stage=FF_Stage.FF_SWI):
        goldfw_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_goldfw(self, slot, stage)["filename"]
        if not self._nic_ctrl_list[slot].salina_nic_call_sysypdate_prog_fw(goldfw_img_file):
            self.cli_log_slot_err_lock(slot, "Program NIC GOLDFW failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    @parallelize.parallel_nic_using_console
    def mtp_program_nic_mainfw_salina(self, slot, stage=FF_Stage.FF_SWI):
        emmc_mainfw_img_file = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + image_control.get_mainfw(self, slot, stage)["filename"]
        if not self._nic_ctrl_list[slot].salina_nic_call_sysypdate_prog_fw(emmc_mainfw_img_file):
            self.cli_log_slot_err_lock(slot, "Program NIC MAINFW failed")
            self.mtp_get_nic_err_msg(slot)
            return False

        return True

    def mtp_mgmt_dump_avs_info(self, slot, buf):
        self.cli_log_slot_inf(slot, "AVS Set Result Dump:")
        # find any error
        avs_passed_flag = re.findall(r"SET AVS PASSED", buf)
        if not avs_passed_flag:
            self.cli_log_slot_inf(slot, buf, level=0)
            return False

        # find the die id
        die_id_match = re.findall(r"(ASIC_DIE_ID: +0x[0-9a-fA-F]+|Salina.*DI.*ID\s+:\s+0x[0-9a-fA-F]+)", buf)
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


    @parallelize.parallel_nic_using_console
    def mtp_mgmt_set_nic_avs(self, slot):
        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.cli_log_err("Failed to execute command {:s}".format(cmd))
            self.mtp_dump_nic_err_msg(slot)
            return False

        nic_type = self.mtp_get_nic_type(slot)
        sn = self.mtp_get_nic_sn(slot)

        vdd_avs_cmd, arm_avs_cmd = None, None

        if nic_type in self._proto_type_list:
            self.cli_log_slot_inf_lock(slot, "Skip AVS for Proto NIC")
            return True
        elif nic_type == NIC_Type.NAPLES100:
            vdd_avs_cmd = MFG_DIAG_CMDS().NAPLES100_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().NAPLES100_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES100IBM:
            vdd_avs_cmd = MFG_DIAG_CMDS().NAPLES100IBM_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().NAPLES100IBM_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES100HPE:
            vdd_avs_cmd = MFG_DIAG_CMDS().NAPLES100HPE_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().NAPLES100HPE_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES100DELL:
            vdd_avs_cmd = MFG_DIAG_CMDS().NAPLES100DELL_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().NAPLES100DELL_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.VOMERO:
            vdd_avs_cmd = MFG_DIAG_CMDS().VOMERO_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().VOMERO_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.VOMERO2:
            vdd_avs_cmd = MFG_DIAG_CMDS().VOMERO2_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().VOMERO2_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25:
            vdd_avs_cmd = MFG_DIAG_CMDS().NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25SWM:
            # NAPLES25SWM uses same setting as Naples25
            vdd_avs_cmd = MFG_DIAG_CMDS().NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25SWMDELL:
            # NAPLES25SWM uses same setting as Naples25
            vdd_avs_cmd = MFG_DIAG_CMDS().NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25OCP:
            # NAPLES25OCP uses same setting as Naples25
            vdd_avs_cmd = MFG_DIAG_CMDS().NAPLES25_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().NAPLES25_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.NAPLES25SWM833:
            vdd_avs_cmd = MFG_DIAG_CMDS().NAPLES25SWM833_VDD_AVS_SET_FMT.format(sn, slot+1)
            arm_avs_cmd = MFG_DIAG_CMDS().NAPLES25SWM833_ARM_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO or nic_type == NIC_Type.ORTANO2:
            """
             Separate freq by PN:
             - For 68-0015 (Oracle) use 1033
             - For 68-0021 (Pensando) use 1100
            """
            if self.mtp_is_nic_ortano_oracle(slot):
                vdd_avs_cmd = MFG_DIAG_CMDS().ORTANO_ORC_AVS_SET_FMT.format(sn, slot+1)
            else:
                vdd_avs_cmd = MFG_DIAG_CMDS().ORTANO_PEN_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2INTERP:
            vdd_avs_cmd = MFG_DIAG_CMDS().ORTANO_ORC_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.POMONTEDELL:
            vdd_avs_cmd = MFG_DIAG_CMDS().POMONTEDELL_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.LACONA32DELL:
            vdd_avs_cmd = MFG_DIAG_CMDS().LACONA32DELL_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.LACONA32:
            vdd_avs_cmd = MFG_DIAG_CMDS().LACONA32_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2SOLO:
            vdd_avs_cmd = MFG_DIAG_CMDS().ORTANO_ORC_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2SOLOL:
            vdd_avs_cmd = MFG_DIAG_CMDS().ORTANO_ORC_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2SOLOORCTHS:
            vdd_avs_cmd = MFG_DIAG_CMDS().ORTANO_ORC_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2SOLOMSFT:
            vdd_avs_cmd = MFG_DIAG_CMDS().ORTANO_PEN_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.ORTANO2SOLOS4:
            vdd_avs_cmd = MFG_DIAG_CMDS().ORTANO_PEN_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.GINESTRA_D4:
            vdd_avs_cmd = MFG_DIAG_CMDS().GINESTRA_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.GINESTRA_D5:
            vdd_avs_cmd = MFG_DIAG_CMDS().GINESTRA_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.GINESTRA_S4:
            vdd_avs_cmd = MFG_DIAG_CMDS().GINESTRA_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type == NIC_Type.GINESTRA_CIS:
            vdd_avs_cmd = MFG_DIAG_CMDS.GINESTRA_AVS_SET_FMT.format(sn, slot+1)
        elif nic_type in SALINA_NIC_TYPE_LIST:
            # salina avs set command will set both vdd and arm
            vdd_avs_cmd = MFG_DIAG_CMDS().SALINA_AVS_SET_FMT.format(slot+1)
        else:
            self.cli_log_slot_err_lock(slot, "Unknown NIC Type")
            return False

        if vdd_avs_cmd:
            self.mtp_nic_stop_tclsh(slot)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(vdd_avs_cmd, timeout=MTP_Const.NIC_AVS_SET_DELAY):
                self.cli_log_slot_err(slot, "Timed out: Failed to execute command {:s}".format(vdd_avs_cmd))
                self.mtp_dump_nic_err_msg(slot)
                self.mtp_mgmt_set_nic_avs_post(slot)
                return False
            if not self.mtp_mgmt_dump_avs_info(slot, self.mtp_get_nic_cmd_buf(slot)):
                self.cli_log_slot_err(slot, "SET VDD AVS FAILED")
                return False
        if arm_avs_cmd:
            self.mtp_nic_stop_tclsh(slot)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(arm_avs_cmd, timeout=MTP_Const.NIC_AVS_SET_DELAY):
                self.cli_log_slot_err(slot, "Timed out: Failed to execute command {:s}".format(arm_avs_cmd))
                self.mtp_dump_nic_err_msg(slot)
                self.mtp_mgmt_set_nic_avs_post(slot)
                return False
            if not self.mtp_mgmt_dump_avs_info(slot, self.mtp_get_nic_cmd_buf(slot)):
                self.cli_log_slot_err(slot, "SET ARM AVS FAILED")
                return False
        self.mtp_mgmt_set_nic_avs_post(slot)

        return True

    def mtp_nic_stop_tclsh(self, slot):
        if self._mtp_type in (MTP_TYPE.MATERA,):
            self._nic_ctrl_list[slot].mtp_exec_cmd("{:s}diag/util/jtag_accpcie_salina clr {:d}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH, slot+1), timeout=MTP_Const.MTP_REBOOT_DELAY)
        else:
            self._nic_ctrl_list[slot].mtp_exec_cmd(MFG_DIAG_CMDS().NIC_DIAG_STOP_TCLSH_FMT, timeout=MTP_Const.OS_CMD_DELAY)

    def mtp_mgmt_set_nic_avs_post(self, slot):
        self.mtp_nic_send_ctrl_c(slot)  # kill any hung tclsh in this same session
        if self._mtp_type not in (MTP_TYPE.PANAREA,):
            cmd = MFG_DIAG_CMDS().NIC_AVS_POST_FMT.format(slot+1)
            self._nic_ctrl_list[slot].mtp_exec_cmd(cmd)

            cmd_buf = self.mtp_get_nic_cmd_buf(slot)

        # clear reg 0x50 after reading
        reg_addr = 0x50
        write_data = 0
        if self._mtp_type in (MTP_TYPE.MATERA,):
            cmd = MFG_DIAG_CMDS().NIC_I2C_DUMP_POST_FMT.format(slot+3) + " ;"
            cmd += MFG_DIAG_CMDS().NIC_I2C_DUMP_4B_POST_FMT.format(slot+3) + " ;"
        else:
            cmd = MFG_DIAG_CMDS().MTP_SMB_SEL_FMT.format(slot+1) + " ;"
        cmd += MFG_DIAG_CMDS().MTP_SMB_WR_CPLD_FMT.format(reg_addr, write_data, slot+1)
        if self._mtp_type in (MTP_TYPE.PANAREA,):
            cmd = ""
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.mtp_dump_nic_err_msg(slot)
            return False

        if self._mtp_type in (MTP_TYPE.MATERA,):
            cmd = ""
        else:
            cmd = MFG_DIAG_CMDS().MTP_SMB_SEL_FMT.format(slot+1) + " ;"
        cmd += MFG_DIAG_CMDS().MTP_SMB_RD_CPLD_FMT.format(reg_addr, slot+1)
        if self._mtp_type in (MTP_TYPE.PANAREA,):
            cmd = ""
        if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
            self.mtp_dump_nic_err_msg(slot)
            return False

        if self._mtp_type in (MTP_TYPE.MATERA,):
            cmd_list = list()
            cmd_list.append(MFG_DIAG_CMDS().NIC_I2C_GET_SPIMODE_FMT.format("17","20","0"))
            cmd_list.append(MFG_DIAG_CMDS().NIC_I2C_GET_SPIMODE_FMT.format("17","20","9"))
            cmd_list.append(MFG_DIAG_CMDS().NIC_I2C_GET_SPIMODE_FMT.format("18","20","0"))
            cmd_list.append(MFG_DIAG_CMDS().NIC_I2C_GET_SPIMODE_FMT.format("18","20","9"))
            for single_cmd in cmd_list:
                if not self._nic_ctrl_list[slot].mtp_exec_cmd(single_cmd):
                    self.mtp_dump_nic_err_msg(slot)
                    return False

        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_fix_vrm(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.ORTANO2:
            if self.mtp_is_nic_ortano_microsoft(slot):
                if not self._nic_ctrl_list[slot].nic_fix_vrm_oc():
                    self.cli_log_slot_err_lock(slot, "{:s} failed".format(MFG_DIAG_CMDS().ORTANO2_VRM_FIX_FMT))
                    self.mtp_dump_nic_err_msg(slot)
                    return False
            else:
                if not self._nic_ctrl_list[slot].nic_fix_vrm():
                    self.cli_log_slot_err_lock(slot, "{:s} failed".format(MFG_DIAG_CMDS().ORTANO2_VRM_FIX_FMT))
                    self.mtp_dump_nic_err_msg(slot)
                    return False
        elif nic_type in (NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4):
            if not self._nic_ctrl_list[slot].nic_fix_vrm():
                self.cli_log_slot_err_lock(slot, "{:s} failed".format(MFG_DIAG_CMDS().ORTANO2_VRM_FIX_FMT))
                self.mtp_dump_nic_err_msg(slot)
                return False
        elif nic_type in SALINA_NIC_TYPE_LIST:
            if not self._nic_ctrl_list[slot].nic_salina_fix_vrm():
                self.cli_log_slot_err_lock(slot, "nic_test_v2.py fix_sal_vrm failed")
                self.mtp_get_nic_err_msg(slot)
                return False

        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_naples25swm_alom_cable_signal_test(self, slot, highpowertest):
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_alom_cable_signal_test(errlist, highpowertest)
        if rc == False:
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        return rc

    def mtp_nic_naples25swm_high_power_mode_test(self, slot):
        self.cli_log_slot_inf(slot, "Starting Naples25 SWM High Power On Test")
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_high_power_mode_test(errlist)
        if rc == False:
            self.cli_log_slot_err(slot, "NIC NAPLES25SWM HIGH POWER MODE TEST FAILED")
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        else:
            self.cli_log_slot_inf(slot, "NIC NAPLES25SWM HIGH POWER MODE TEST PASSED")
        return rc

    @parallelize.parallel_nic_using_console
    def mtp_nic_naples25swm_low_power_mode_test(self, slot):
        self.cli_log_slot_inf(slot, "Starting Naples25 SWM Low Power On Test")
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_low_power_mode_test(errlist)
        if rc == False:
            self.cli_log_slot_err(slot, "NIC NAPLES25SWM LOW POWER MODE TEST FAILED")
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        else:
            self.cli_log_slot_inf(slot, "NIC NAPLES25SWM LOW POWER MODE TEST PASSED")
        return rc

    @parallelize.parallel_nic_using_console
    def mtp_nic_naples25swm_cpld_spi_to_smb_reg_test(self, slot):
        errlist = list()
        rc = self._nic_ctrl_list[slot].nic_naples25swm_cpld_reg_test(errlist)
        if rc == False:
            for errstr in errlist:
                self.cli_log_slot_err(slot, "{:s}".format(errstr))
        return rc

    @parallelize.parallel_nic_using_console
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
            if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
                cmd = ""
            else:
                cmd = MFG_DIAG_CMDS().MTP_SMB_SEL_FMT.format(slot+1) + " ;"
            cmd += MFG_DIAG_CMDS().MTP_SMB_RD_CPLD_FMT.format(reg_addr, slot+1)
            if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                # try again one more time
                time.sleep(1)
                if not self._nic_ctrl_list[slot].mtp_exec_cmd(cmd):
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    continue

    def mtp_run_asic_l1_bash(self, slot=None, sn=None, mode=None, vmarg=Voltage_Margin.normal, stage=FF_Stage.FF_P2C, joo='1', loopback='0', offload='0', esecure='0', simplified='0', ite='1', ddr="1", lt='1'):
        """
        cd ~diag/scripts/asic/
        ./run_l1.test -sn <sn> -slot <slot> -m <mode> -v <vmarg>
        ./run_l1.sh -sn <> -slot <> -joo <> -m <> -i <> -v <> -o <> -e <> -s <> -hc <> -ddr <> -ite <>
        sn:   SN
        slot: Slot number
        joo:  J2C or OW; J2C; 1: OW: 0; default: 0
        m:    Mode hod/hod_1100/nod/nod_525
        i:    0: external loopback; 1 internal loopback; default: 0
        v:    Voltage margin: normal/low/high; default: normal
        o:    0: offload diabled; 1: offload PCIe/ETH PRBS, TCAM, efuse tests to ARM; default: 1
        e:    0: esecure test disabled; 1: esecure test enabled; default: 1
        s:    0: simplified test disabled; 1: simlified test enabled; default: 0
        hc:   0: Soft training; 1: hardcoded DDR training; default: 0
        ddr:  0: DDR test skipped; 1: DDR test enabled
        lt:   0: fixed settings; 1: link training
        ite:  Number of iterations
        """
        rs = False

        nic_type = self.mtp_get_nic_type(slot)

        if nic_type in DDR_HARCODED_TRAINING_NIC_LIST:
            ddr_hc_training = "1"
        else:
            ddr_hc_training = "0"

        skip_ddr_bist = ddr
        if stage == FF_Stage.FF_SRN:
            skip_ddr_bist = "0"

        if nic_type == NIC_Type.POLLARA:
            lt = "0"

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_ASIC_PATH)
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            self.cli_log_slot_err(slot, "Command {:s} failed")
            rs = False

        # do not run esecure with one wire interface
        if stage == FF_Stage.FF_SRN or joo == '0' or nic_type in SALINA_NIC_TYPE_LIST: esecure = "0"

        if self._mtp_type not in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA):
            cmd = MFG_DIAG_CMDS().NIC_RUN_ASIC_L1_FMT.format(sn, slot+1, mode, vmarg, skip_ddr_bist, ddr_hc_training)
        elif self._mtp_type == MTP_TYPE.MATERA:
            # "./run_l1.sh -sn {:s} -slot {:d} -m {:s} -v {:s} -ddr {:s} -hc {:s} -joo {:s} -i {:s} -o {:s} -e {:s} -s {:s} -ite {:s} -lt {:s}"
            cmd = MFG_DIAG_CMDS().NIC_MATERA_RUN_ASIC_L1_FMT.format(sn, slot+1, mode, vmarg, skip_ddr_bist, ddr_hc_training, joo, loopback, offload, esecure, simplified, ite, lt)
        elif self._mtp_type == MTP_TYPE.PANAREA:
            cmd = MFG_DIAG_CMDS().NIC_PANAREA_RUN_ASIC_L1_FMT.format(sn, slot+1, vmarg, loopback, esecure, ite)

        self.cli_log_slot_inf(slot, cmd)

        l1_cmd_tout = MTP_Const.MTP_PARA_ASIC_L1_TEST_TIMEOUT
        if nic_type in SALINA_AI_NIC_TYPE_LIST:
            l1_cmd_tout = MTP_Const.SALINA_AI_ASIC_L1_TEST_TIMEOUT
        if nic_type in SALINA_DPU_NIC_TYPE_LIST:
            l1_cmd_tout = MTP_Const.SALINA_DPU_ASIC_L1_TEST_TIMEOUT
        if nic_type in VULCANO_NIC_TYPE_LIST:
            l1_cmd_tout = MTP_Const.VULCANO_ASIC_L1_TEST_TIMEOUT

        if not self.mtp_mgmt_exec_cmd_para(slot, cmd, timeout=l1_cmd_tout):
            rs = False
            # kill the process in case it's hung/timed out
            # ctrl-c doesnt work
            # needs to be killed from separate session
            if not self.mtp_mgmt_exec_cmd_para(slot, "## killall run_l1.sh", timeout=60):  # notify in log
                pass
            self.mtp_nic_stop_tclsh(slot)  # use mtp session to kill it

        cmd_buf = self.mtp_get_nic_cmd_buf(slot)

        if MFG_DIAG_SIG.NIC_PARA_ASIC_L1_OK_SIG in cmd_buf:
            rs = True

        return rs

    def mtp_reset_hub(self, slot=None):
        """
        cpldutil -cpld-wr -addr=0x2 -data=0xf
        cpldutil -cpld-wr -addr=0x2 -data=0x0
        """
        self.mtp_nic_lock()

        # on mtp_diag.log
        if slot is None:
            ts = libmfg_utils.timestamp_snapshot()
            ts_record_cmd = "#######= RESET I2C HUB =#######"
            self.log_mtp_file(ts_record_cmd)

            cmd = MFG_DIAG_CMDS().MTP_CPLD_WRITE_FMT.format(0x2, 0xf)
            self.mtp_mgmt_exec_cmd(cmd)

            cmd = MFG_DIAG_CMDS().MTP_CPLD_READ_FMT.format(0x2)
            self.mtp_mgmt_exec_cmd(cmd)

            cmd = MFG_DIAG_CMDS().MTP_CPLD_WRITE_FMT.format(0x2, 0x0)
            self.mtp_mgmt_exec_cmd(cmd)

            cmd = MFG_DIAG_CMDS().MTP_CPLD_READ_FMT.format(0x2)
            self.mtp_mgmt_exec_cmd(cmd)

        # on mtp_NIC*_diag.log
        else:
            ts = libmfg_utils.timestamp_snapshot()
            ts_record_cmd = "#######= RESET I2C HUB =#######"
            self.log_nic_file(slot, ts_record_cmd)

            cmd = MFG_DIAG_CMDS().MTP_CPLD_WRITE_FMT.format(0x2, 0xf)
            self.mtp_mgmt_exec_cmd_para(slot, cmd)

            cmd = MFG_DIAG_CMDS().MTP_CPLD_READ_FMT.format(0x2)
            self.mtp_mgmt_exec_cmd_para(slot, cmd)

            cmd = MFG_DIAG_CMDS().MTP_CPLD_WRITE_FMT.format(0x2, 0x0)
            self.mtp_mgmt_exec_cmd_para(slot, cmd)

            cmd = MFG_DIAG_CMDS().MTP_CPLD_READ_FMT.format(0x2)
            self.mtp_mgmt_exec_cmd_para(slot, cmd)

        self.mtp_nic_unlock()
        return True

    def mtp_nic_console_lock(self):
        # fpga implementation allows multiple console
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA): return
        self._nic_console_lock.acquire()

    def mtp_nic_console_unlock(self):
        # fpga implementation allows multiple console
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA): return
        self._nic_console_lock.release()

    def mtp_single_j2c_lock(self):
        # fpga implementation allows multiple j2c
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA): return
        self._j2c_lock.acquire()

    def mtp_single_j2c_unlock(self):
        # fpga implementation allows multiple j2c
        if self._mtp_type in (MTP_TYPE.MATERA, MTP_TYPE.PANAREA): return
        self._j2c_lock.release()

    def mtp_turbo_j2c_lock(self, slot):
        self._turbo_j2c_lock[slot].acquire()

    def mtp_turbo_j2c_unlock(self, slot):
        self._turbo_j2c_lock[slot].release()

    def mtp_nic_lock(self):
        self.mtp_single_j2c_lock()
        self.mtp_nic_console_lock()

    def mtp_nic_unlock(self):
        self.mtp_single_j2c_unlock()
        self.mtp_nic_console_unlock()

    def mtp_run_diag_test_para(self, slot, diag_cmd, rslt_cmd, test, init_cmd=None, post_cmd=None, timeout=MTP_Const.DIAG_PARA_TEST_TIMEOUT):
        # init command
        if init_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, init_cmd):
                err_msg = self.mtp_get_nic_err_msg(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        # run diag test
        if not self.mtp_mgmt_exec_cmd_para(slot, diag_cmd, timeout=timeout):
            err_msg = self.mtp_get_nic_err_msg(slot)
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

        # post command
        if post_cmd:
            if not self.mtp_mgmt_exec_cmd_para(slot, post_cmd):
                err_msg = self.mtp_get_nic_err_msg(slot)
                return [MTP_DIAG_Error.NIC_DIAG_FAIL, [err_msg]]

        result_msg = self.mtp_mgmt_get_test_result_para(slot, rslt_cmd, test)
        if result_msg == "SUCCESS":
            ret = True
        else:
            ret = False
        return [ret, err_msg_list]

    @parallelize.parallel_nic_using_console
    def mtp_nic_mvl_acc_test(self, slot):
        if not self._nic_ctrl_list[slot].nic_mvl_acc_test():
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_mvl_stub_test(self, slot, loopback=True):
        if not loopback:
            self.cli_log_slot_inf(slot, "Internal loopback")
        if not self._nic_ctrl_list[slot].nic_mvl_stub_test(loopback):
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_mvl_link_test(self, slot, ports=1):
        if not self._nic_ctrl_list[slot].nic_mvl_link_test(ports):
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_phy_xcvr_link_test(self, slot):
        if not self._nic_ctrl_list[slot].nic_phy_xcvr_link_test():
            return False
        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_phy_xcvr_test(self, slot):
        if not self._nic_ctrl_list[slot].nic_phy_xcvr_test():
            return False
        return True

    def mtp_nic_edma_test(self, slot):
        if not self._nic_ctrl_list[slot].nic_edma_test():
            return False
        return True

    def mtp_check_nic_rebooted(self, slot):
        self.cli_log_slot_inf(slot, "Init new NIC connection")
        ret = self.mtp_nic_para_session_init(slot_list=[slot], fpo=False)
        if not ret:
            self.cli_log_err("Init NIC Connection Failed", level=0)

        self.cli_log_slot_inf(slot, "Check if NIC rebooted")
        if not self._nic_ctrl_list[slot].nic_check_rebooted():
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False
        self.cli_log_slot_inf(slot, "No sign of reboot")
        return True

    def mtp_nic_prp_test(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in SALINA_NIC_TYPE_LIST:
            return True
        if not self._nic_ctrl_list[slot].nic_prp_test():
            self.cli_log_slot_err(slot, "Unable to run PRP test")
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_nic_stop_tclsh(slot)
            return False

    def mtp_nic_qspi_verify_test(self, slot, stage="", test=""):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in SALINA_AI_NIC_TYPE_LIST:
            return True
        if test not in ["SALINA_NEW_MEM_LAYOUT_QSPI_VERIFY","SALINA_NIC_BOOT_STAGE","SALINA_QSPI_VERIFY"]:
            return True
        if stage not in [FF_Stage.FF_DL, FF_Stage.FF_P2C, FF_Stage.FF_4C_H, FF_Stage.FF_4C_L]:
            return True

        if not self._nic_ctrl_list[slot].nic_qspi_verify_test(stage=stage, test=test):
            self.cli_log_slot_err(slot, "Unable to run qspi verify test")
            self.mtp_dump_nic_err_msg(slot)
            return False

    def mtp_nic_dump_reg(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in SALINA_NIC_TYPE_LIST + VULCANO_NIC_TYPE_LIST:
            return True
        if not self._nic_ctrl_list[slot].nic_dump_reg():
            self.cli_log_slot_err(slot, "Unable to run register dump")
            self.mtp_dump_nic_err_msg(slot)
            return False

    def mtp_nic_read_temp(self, slot):
        """
         Read board and die temp via j2c
         WARNING: this does an ARM reset, so need a powercycle to bring NIC back to fresh slate
        """
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST + SALINA_NIC_TYPE_LIST + VULCANO_NIC_TYPE_LIST:
            return True
        if not self._nic_ctrl_list[slot].read_nic_temp():
            self.cli_log_slot_err(slot, "Unable to read NIC temperature")
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_nic_stop_tclsh(slot)
            return False

        cmd_buf = self.mtp_get_nic_cmd_buf(slot)

        if nic_type in ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST:
            # [21-08-03 19:00:29] MSG :: ASIC           core_temp(C)   core_volt(V)   brd_temp(C)    r_die_temp(C)  VDD_VOUT(V)    ARM_VOUT(V)    PIN(W)
            # [21-08-03 19:00:29] MSG ::                71.80          0.73           45             83             0.730          0.860          60.0
            found_column_heading = False
            board_temp = "0"
            die_temp = "0"
            for line in cmd_buf.split("\r\n"):
                match = re.search(r"MSG ::.*core_temp.*brd_temp.*die_temp", line)
                if match:
                    found_column_heading = True
                    continue
                if found_column_heading:
                    match = re.search(r"MSG :: +(-?\d+\.?\d+) + (-?\d+\.?\d+) + (-?\d+\.?\d+) + (-?\d+\.?\d+)", line)
                    if match:
                        board_temp = match.group(3)
                        die_temp = match.group(4)
                    else:
                        self.cli_log_slot_err(slot, "Missing readings for NIC temperature")
                        self.mtp_dump_nic_err_msg(slot)
                    break

            self.cli_log_slot_inf(slot, "NIC board temperature = {:s}C".format(board_temp))
            self.cli_log_slot_inf(slot, "NIC die temperature   = {:s}C".format(die_temp))
            self.mtp_nic_stop_tclsh(slot)

            # Use this dump to check ECC errors as well
            ecc_regs = re.findall(r"Reg 0x(.*); value: 0x(.*)", cmd_buf)
            if ecc_regs:
                errors_found = False
                for reg, val in ecc_regs:
                    if int(val.strip(), 16) != 0:
                        self.cli_log_slot_err(slot, "Reg 0x{:s}; value: 0x{:s}".format(reg, val))
                        errors_found = True

                if not errors_found:
                    self.cli_log_slot_inf(slot, "No ECC errors found")
                else:
                    self.cli_log_slot_err(slot, "ECC errors found")
        elif nic_type in SALINA_NIC_TYPE_LIST:
            die_temp = "0"
            for line in cmd_buf.split("\r\n"):
                match = re.search(r"CARD_DETAILS::.+TEMP:(.+)\(VRM\)\/(.+)\(FRONT\)", line)
                if match:
                    die_temp = match.group(1)
                    self.cli_log_slot_inf(slot, "NIC die temperature   = {:s}C".format(die_temp))
                    break
            self.mtp_nic_stop_tclsh(slot)

        return True

    def mtp_get_nic_sts(self, slot, skip_vrm_check=True, testname=None):
        """
         Read board and die temp via j2c
         WARNING: this does an ARM reset, so need a powercycle to bring NIC back to fresh slate
        """
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in ELBA_NIC_TYPE_LIST + GIGLIO_NIC_TYPE_LIST + SALINA_NIC_TYPE_LIST:
            return True
        if not self._nic_ctrl_list[slot].read_nic_temp(skip_reboot=skip_vrm_check):
            self.cli_log_slot_err(slot, "Unable to dump NIC sts")
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_nic_stop_tclsh(slot)
        cmd_buf = self._nic_ctrl_list[slot].nic_get_cmd_buf()
        sub_error = ""
        lines = cmd_buf.splitlines()
        for line in lines:
            if "GET_NIC_STS_DBG_INFO:" not  in line:
                continue
            if "ECC happaned" in line:
                sub_error += " :ECC_ERROR"
        self.cli_log_slot_err(slot, testname + sub_error)

        self.mtp_nic_stop_tclsh(slot)

        return True

    def mtp_clear_nic_uart(self, slot):
        """
         close previous uart
        """
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in SALINA_NIC_TYPE_LIST:
            return True
        if not self._nic_ctrl_list[slot].clear_nic_uart():
            self.cli_log_slot_err(slot, "Unable to kill NIC uart")
            self.mtp_dump_nic_err_msg(slot)

        return True

    def mtp_sal_check_j2c(self, slot, testname=None):
        """
         example command, tclsh /home/diag/diag/scripts/asic/sal_check_j2c.tcl -slot <> -ite 1
         ERROR :: ASIC PLL failure has happened
        """

        nic_type = self.mtp_get_nic_type(slot)
        if nic_type not in SALINA_NIC_TYPE_LIST:
            return True
        if not self._nic_ctrl_list[slot].sal_check_j2c():
            self.cli_log_slot_err(slot, "Unable to run sal_check_j2c.tcl")
            self.mtp_dump_nic_err_msg(slot)
            self.mtp_nic_stop_tclsh(slot)
        cmd_buf = self._nic_ctrl_list[slot].nic_get_cmd_buf()
        sub_error = ""
        lines = cmd_buf.splitlines()
        for line in lines:
            if "ERROR :: ASIC PLL failure has happened" not  in line:
                continue
            if "ASIC PLL" in line:
                sub_error += " :ASIC_PLL_FAILURE"
        self.cli_log_slot_err(slot, testname + sub_error)

        self.mtp_nic_stop_tclsh(slot)

        return True

    def mtp_thread_stop_on_err(self):
        # send SIGINT to parent thread
        import signal
        os.kill(os.getpid(), signal.SIGINT)

    def mtp_get_file_md5sum(self, filename):
        cmd = "md5sum {:s}".format(filename)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Failed to execute {:s}".format(cmd), level=0)
            return None
        cmd_buf = self.mtp_get_cmd_buf()
        md5sum_regex = r"([0-9a-fA-F]+) +.*"
        match = re.search(md5sum_regex, cmd_buf)
        if match:
            local_md5sum = match.group(1)
            return local_md5sum
        else:
            self.cli_log_err("Unable to verify {:s}".format(filename))
            return None

    def mtp_nic_port_counters(self, slot):
        self.cli_log_slot_inf(slot, "Dumping port counters")
        if not self._nic_ctrl_list[slot].nic_port_counters():
            self.mtp_dump_nic_err_msg(slot)
            return False

        return True

    def mtp_construct_nic_fru_config(self, slot, swmtestmode=Swm_Test_Mode.SW_DETECT):
        read_fru_cfg = dict()
        read_fru_cfg["VALID"] = True
        nic_fru_info = self.mtp_get_nic_fru(slot)
        if not nic_fru_info:
            self.cli_log_slot_err(slot, "Errors while loading FRU from this board")
            read_fru_cfg["VALID"] = False
            return read_fru_cfg
        read_fru_cfg["TS"] = libmfg_utils.get_fru_date()
        read_fru_cfg[bf.SN] = nic_fru_info[0]
        read_fru_cfg[bf.MAC] = nic_fru_info[1].replace('-', '')
        read_fru_cfg[bf.PN] = nic_fru_info[2]
        read_fru_cfg[bf.DPN] = self._nic_ctrl_list[slot]._dpn
        read_fru_cfg[bf.SKU] = self.get_scanned_sku(slot)
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            nic_fru_info = self.mtp_get_nic_alom_fru(slot)
            read_fru_cfg[bf.ALOM_SN] = nic_fru_info[0]
            read_fru_cfg[bf.ALOM_PN] = nic_fru_info[1]

        return read_fru_cfg

    @parallelize.parallel_nic_using_ssh
    def mtp_scan_verify(self, slot, ignore_pn_rev=False, swmtestmode=Swm_Test_Mode.SW_DETECT):
        fru_reprogram_list = list()
        scan_fru_cfg = dict()
        scan_fru_cfg[bf.SN] = self.get_scanned_sn(slot)
        scan_fru_cfg[bf.MAC] = self.get_scanned_mac(slot)
        scan_fru_cfg[bf.PN] = self.get_scanned_pn(slot)
        scan_fru_cfg[bf.DPN] = self.get_scanned_dpn(slot)
        scan_fru_cfg[bf.SKU] = self.get_scanned_sku(slot)
        nic_type = self.mtp_get_nic_type(slot)
        if nic_type == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
            scan_fru_cfg[bf.ALOM_SN] = self.get_scanned_alom_sn(slot)
            scan_fru_cfg[bf.ALOM_PN] = self.get_scanned_alom_pn(slot)

        read_fru_cfg = self.mtp_construct_nic_fru_config(slot, swmtestmode)
        if not read_fru_cfg["VALID"]:
            self.cli_log_slot_err(slot, "Failed to load current FRU")
            return False

        ret = True
        for item in [bf.SN, bf.MAC, bf.PN]:
            expected = scan_fru_cfg[item]
            received = read_fru_cfg[item]
            if not expected:
                self.cli_log_slot_err(slot, "Missing {:s} scan for this slot".format(item))
                ret = False
                continue
            if expected != received:
                if item == bf.PN and ignore_pn_rev:
                    expected = expected[:PEN_PN_MINUS_REV_MASK]
                    received = received[:PEN_PN_MINUS_REV_MASK]
                    if expected == received:
                        if slot not in fru_reprogram_list:
                            fru_reprogram_list.append(slot)
                        continue

                self.cli_log_slot_err(slot, "Incorrect {:s}. Scanned {:s}, read {:s}.".format(item, expected, received))
                ret = False
                continue

        return ret

    @parallelize.parallel_nic_using_ssh
    def fake_scan_verify(self, slot, swmtestmode=Swm_Test_Mode.SW_DETECT, scanned_dpn="", scanned_sku=""):
        fail_scan_list = list()
        read_fru_cfg = dict()
        # read in current FRU
        key = libmfg_utils.nic_key(slot)
        read_fru_cfg[key] = self.mtp_construct_nic_fru_config(slot, swmtestmode)
        if not read_fru_cfg[key]["VALID"]:
            self.cli_log_slot_err(slot, "Failed to load current FRU")
            return False
        self.mtp_populate_fru_to_scans(slot, read_fru_cfg, dpn=scanned_dpn, sku=scanned_sku)
        return True

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_validate_pn_dpn_match(self, slot):
        """
            Check that scanned DPN is allowed for the part number in the FRU
        """
        nic_type = self.mtp_get_nic_type(slot)
        pn = self.mtp_get_nic_pn(slot)
        dpn = self.get_scanned_dpn(slot)
        if nic_type not in CTO_MODEL_TYPE_LIST:
            self.cli_log_slot_err(slot, "PN-DPN check doesnt apply to this NIC")
            return False

        if libmfg_utils.check_dpn_allowed(self, pn, dpn):
            return True
        else:
            return False

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_validate_sku_dpn_match(self, slot):
        """
            Check that scanned SKU is allowed for the DPN in the FRU
        """
        nic_type = self.mtp_get_nic_type(slot)
        pn = self.mtp_get_nic_pn(slot)
        dpn = self.mtp_get_nic_dpn(slot)
        sku = self.get_scanned_sku(slot)
        if nic_type not in CTO_MODEL_TYPE_LIST:
            self.cli_log_slot_err(slot, "DPN-SKU check doesnt apply to this NIC")
            return False

        if libmfg_utils.check_sku_allowed(self, pn, dpn, sku):
            return True
        else:
            return False

    def mtp_nic_ping_test(self, slotA, slotB):
        if not self._nic_ctrl_list[slotA].nic_console_enable_network_port():
            self.cli_log_slot_err(slotA, "Setup mgmt failed")
            self.mtp_get_nic_err_msg(slotA)
            self.mtp_dump_nic_err_msg(slotA)
            return False
        if not self._nic_ctrl_list[slotB].nic_console_enable_network_port():
            self.cli_log_slot_err(slotB, "Setup mgmt failed")
            self.mtp_get_nic_err_msg(slotB)
            self.mtp_dump_nic_err_msg(slotB)
            return False

        keyA = libmfg_utils.nic_key(slotA)
        keyB = libmfg_utils.nic_key(slotB)
        self.cli_log_slot_inf(slotA, "Ping {:s} to {:s}".format(keyA, keyB))
        retA = self._nic_ctrl_list[slotA].nic_console_ping(slotB)
        if not retA:
            self.cli_log_slot_err(slotA, "Failed to ping link partner")
        self.cli_log_slot_inf(slotB, "Ping {:s} to {:s}".format(keyB, keyA))
        retB = self._nic_ctrl_list[slotB].nic_console_ping(slotA)
        if not retB:
            self.cli_log_slot_err(slotB, "Failed to ping link partner")

        if not self._nic_ctrl_list[slotA].nic_console_disable_network_port():
            self.cli_log_slot_err(slotA, "Enable MTP port failed")
            self.mtp_get_nic_err_msg(slotA)
            self.mtp_dump_nic_err_msg(slotA)
            return False
        if not self._nic_ctrl_list[slotB].nic_console_disable_network_port():
            self.cli_log_slot_err(slotB, "Enable MTP port failed")
            self.mtp_get_nic_err_msg(slotB)
            self.mtp_dump_nic_err_msg(slotB)
            return False

        if retA and retB:
            return True
        else:
            return False

    def mtp_nic_para_disp_ecc(self, vmarg, stop_on_err=False):
        nic_list = list()
        for slot in range(self._slots):
            if self._nic_prsnt_list[slot]:
                nic_list.append(slot)

        if not nic_list:
            self.cli_log_err("No NICs passed")
            return nic_list[:]

        # parallel init mgmt/aapl
        dsp = "FA"
        if vmarg == Voltage_Margin.low:
            dsp = "LV_FA"
        elif vmarg == Voltage_Margin.high:
            dsp = "HV_FA"
        sn = ""
        test = "ECC_DISP"
        start_ts = libmfg_utils.timestamp_snapshot()

        mtp_start_ts = self.log_test_start(test)
        for slot in nic_list:
            sn = self.mtp_get_nic_sn(int(slot))
            slot_start_ts = self.log_slot_test_start(slot, test)
            self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, dsp, test))

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return nic_list[:]

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.NIC_MGMT_PARA_SIG]
        cmd = MFG_DIAG_CMDS().MTP_DISP_ECC_FMT.format(nic_list_param)

        if not self.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.MTP_PARA_AAPL_INIT_DELAY):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            duration = self.log_test_stop(test, start_ts)
            for slot in nic_list:
                self.log_slot_test_stop(slot, test, start_ts)
                sn = self.mtp_get_nic_sn(int(slot))
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
                self.mtp_set_nic_status_fail(slot)
            return nic_list[:]

        cmd_buf = self.mtp_get_cmd_buf()
        ecc_fail_list = list()

        slot_bufs = cmd_buf.split("=== Slot ")
        for slot_buf in slot_bufs[1:]:  # skip first element
            slot = int(slot_buf[0:2])
            ecc_regs = re.findall(r"Reg 0x(.*): 0x(.*)", slot_buf)
            if ecc_regs:
                errors_found = False
                for reg, val in ecc_regs:
                    if int(val.strip(), 16) != 0:
                        self.cli_log_slot_err(slot, "Reg 0x{:s}: 0x{:s}".format(reg, val))
                        errors_found = True
                        if slot not in ecc_fail_list:
                            ecc_fail_list.append(slot)

                if not errors_found:
                    self.cli_log_slot_inf(slot, "No ECC errors found")
                else:
                    self.cli_log_slot_err(slot, "ECC errors found")

        duration = self.log_test_stop(test, start_ts)
        for slot in nic_list:
            self.log_slot_test_stop(slot, test, start_ts)
            sn = self.mtp_get_nic_sn(int(slot))
            if slot in ecc_fail_list:
                self.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, dsp, test, "FAILED", duration))
            else:
                self.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, dsp, test, duration))

        return ecc_fail_list[:]

    @parallelize.parallel_nic_using_console
    def mtp_nic_sw_mgmt_init(self, slot):
        if not self.mtp_nic_mgmt_reinit(slot):
            self.cli_log_slot_err(slot, "Failed to init mgmt port in production FW")
            return False

        if slot in self.mtp_nic_mgmt_mac_refresh(slot):
            self.cli_log_slot_err(slot, "MTP mac address refresh failed")
            return False

        if slot in self.mtp_mgmt_nic_mac_validate(slot):
            self.cli_log_slot_err(slot, "MTP detect duplicate mac address")
            return False

        return True

    def mtp_nic_disp_ecc(self, slot):
        err_msg_list = list()
        errors_found = False

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False, err_msg_list

        cmd = MFG_DIAG_CMDS().MTP_DISP_ECC_FMT.format(str(slot+1))

        ret = self.mtp_mgmt_exec_cmd_para(slot, cmd, timeout=5*60)

        if not ret:
            self.cli_log_err("Execute command {:s} failed".format(cmd))
            return False, err_msg_list

        cmd_buf = self.mtp_get_nic_cmd_buf(slot)

        slot_bufs = cmd_buf.split("=== Slot ")
        for slot_buf in slot_bufs[1:]:  # skip first element
            slot = int(slot_buf[0:2])-1
            ecc_regs = re.findall(r": Reg 0x(.*): 0x(.*)", slot_buf)
            if ecc_regs:
                errors_found = False
                for reg, val in ecc_regs:
                    if int(val.strip(), 16) != 0:
                        self.cli_log_slot_err(slot, "Reg 0x{:s}: 0x{:s}".format(reg, val))
                        errors_found = True
                    err_msg_list.append(slot_buf.split())

            ecc_intr = re.findall(r"MSG(.*FAIL.*$)", slot_buf)
            if ecc_intr:
                errors_found = True
                err_msg_list += ecc_intr[:]

            ecc_errs = re.findall(r"(.*orrectable.*)", slot_buf)
            if ecc_errs:
                errors_found = True
                err_msg_list += ecc_errs[:]

            if not errors_found:
                self.cli_log_slot_inf(slot, "No ECC errors found")
            else:
                self.cli_log_slot_err(slot, "ECC errors found")

        if errors_found:
            return False, err_msg_list
        else:
            return True, err_msg_list

    @parallelize.parallel_nic_using_console
    def mtp_nic_vdd_ddr_fix_console(self, slot):
        return slot not in self.mtp_nic_vdd_ddr_fix(slot, True)

    @parallelize.parallel_nic_using_ssh
    def mtp_nic_vdd_ddr_fix(self, slot, console=False):
        d3_val = "0xb7"  # vdd_ddr switching frequency
        d4_val = "0x0a"  # vdd_ddr margin
        vddq_prog = False  # prog vddq with same values

        nic_type = self.mtp_get_nic_type(slot)

        if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4, NIC_Type.LACONA32, NIC_Type.LACONA32DELL):
            self.cli_log_slot_err(slot, "This function is not applicable for this card type!")
            return False

        if nic_type in (NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4):
            d3_val = "0xb7"
            d4_val = "0x10"
            vddq_prog = True

        if nic_type == NIC_Type.POMONTEDELL or nic_type == NIC_Type.ORTANO2:
            d3_val = "0xb7"
            d4_val = "0x10"
            vddq_prog = False

        if nic_type in GIGLIO_NIC_TYPE_LIST:
            d3_val = "0x07"

        if console:
            if not self._nic_ctrl_list[slot].nic_console_vdd_ddr_check(d3_val, d4_val, vddq_prog):
                self.mtp_clear_nic_err_msg(slot)  # clear out the error message
                if not self._nic_ctrl_list[slot].nic_console_vdd_ddr_fix(d3_val, d4_val, vddq_prog):
                    self.cli_log_slot_err(slot, "Failed to set VDD_DDR margin")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                if not self._nic_ctrl_list[slot].nic_console_vdd_ddr_check(d3_val, d4_val, vddq_prog):
                    self.cli_log_slot_err(slot, "VDD_DDR values incorrect")
                    self.mtp_get_nic_err_msg(slot)
                    return False
        else:
            if nic_type in GIGLIO_NIC_TYPE_LIST:
                rc = self._nic_ctrl_list[slot].nic_vdd_ddr_check(d3_val=d3_val, i2cbus_num="2")
            else:
                rc = self._nic_ctrl_list[slot].nic_vdd_ddr_check(d3_val, d4_val, vddq_prog)
            if not rc:
                self.mtp_clear_nic_err_msg(slot) # clear out the error message
                if nic_type in GIGLIO_NIC_TYPE_LIST:
                    rc = self._nic_ctrl_list[slot].gigilo_nic_vdd_ddr_fix(d3_val=d3_val)
                else:
                    rc = self._nic_ctrl_list[slot].nic_vdd_ddr_fix(d3_val, d4_val, vddq_prog)
                if not rc:
                    self.cli_log_slot_err(slot, "Failed to set VDD_DDR margin")
                    self.mtp_get_nic_err_msg(slot)
                    self.mtp_dump_nic_err_msg(slot)
                    return False
                if nic_type in GIGLIO_NIC_TYPE_LIST:
                    rc = self._nic_ctrl_list[slot].nic_vdd_ddr_check(d3_val=d3_val, i2cbus_num="2")
                else:
                    rc = self._nic_ctrl_list[slot].nic_vdd_ddr_check(d3_val, d4_val, vddq_prog)
                if not rc:
                    self.cli_log_slot_err(slot, "VDD_DDR values incorrect")
                    self.mtp_get_nic_err_msg(slot)
                    return False

        return True

    def mtp_nic_failed_boot(self, slot):
        return self._nic_ctrl_list[slot].nic_failed_boot()

    def mtp_set_nic_failed_boot(self, slot):
        return self._nic_ctrl_list[slot].set_nic_failed_boot()

    def mtp_nic_l1_health_check(self, slot):
        self.cli_log_slot_inf(slot, "Running L1 health check")
        sn = self.mtp_get_nic_sn(slot)
        self.mtp_mgmt_exec_cmd_para(slot, MFG_DIAG_CMDS().NIC_L1_HEALTH_CHECK.format(sn, slot+1), timeout=MTP_Const.MTP_L1_HEALTH_CHECK_TIMEOUT)
        # check for 3 tests with "PASS" result in elb_l1_screen*.log
        self.mtp_nic_stop_test(slot)

    @parallelize.parallel_nic_using_console # should be j2c really but this test in parallel is not tested on turbo MTP
    def mtp_nic_l1_esecure_prog(self, slot):
        self.mtp_single_j2c_lock()
        self.mtp_nic_stop_tclsh(slot)

        if not self._nic_ctrl_list[slot].nic_l1_esecure_prog():
            self.mtp_single_j2c_unlock()
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        self.mtp_single_j2c_unlock()
        return True

    @parallelize.parallel_nic_using_nic_test
    def mtp_nic_esec_write_protect(self, nic_list, enable=False):
        fail_nic_list = list()

        if not nic_list:
            return []

        # first slot will be the "main" slot to issue the commands on.
        slot_main = nic_list[0]

        cmd = "cd {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_NIC_CON_PATH)
        if not self.mtp_mgmt_exec_cmd_para(slot_main, cmd):
            self.cli_log_slot_err(slot_main, "Execute command {:s} failed".format(cmd))
            return nic_list[:]

        nic_list_param = ",".join(str(slot+1) for slot in nic_list)
        sig_list = [MFG_DIAG_SIG.NIC_ESEC_WRITE_PROT_SIG]

        for slot in nic_list:
            if enable:
                self.cli_log_slot_inf(slot, "Start Enable Esec Write Protection")
            else:
                self.cli_log_slot_inf(slot, "Start Disable Esec Write Protection")
        if enable:
            cmd = MFG_DIAG_CMDS().NIC_ENA_ESEC_WRITE_PROT_FMT.format(nic_list_param)
        else:
            cmd = MFG_DIAG_CMDS().NIC_DIS_ESEC_WRITE_PROT_FMT.format(nic_list_param)

        if not self.mtp_mgmt_exec_cmd_para(slot_main, cmd, sig_list=sig_list, timeout=MTP_Const.NIC_ESEC_WRITE_PROT_DELAY):
            self.cli_log_slot_err(slot_main, "Execute command {:s} failed".format(cmd))
            return nic_list[:]
        if "failed;" in self.mtp_get_nic_cmd_buf(slot_main):
            match = re.search("failed slots: *([0-9,]+)", self.mtp_get_cmd_buf())
            if match:
                for slot in libmfg_utils.expand_range_of_numbers(match.group(1), range_min=1, range_max=self._slots, dev=self._id):
                    slot = slot-1
                    self.cli_log_slot_err(slot, "Esecure write-protect operation failed")
                    self.mtp_set_nic_status_fail(slot)
                    fail_nic_list.append(slot)
        return fail_nic_list

    def mtp_nic_i2c_bus_scan(self, slot):
        self._nic_ctrl_list[slot].nic_i2c_bus_scan()

        return True

    def mtp_nic_read_transceiver_sn(self, slot, port):
        if not self._nic_ctrl_list[slot].nic_read_transceiver_sn(port):
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        if port in list(self._nic_ctrl_list[slot]._loopback_sn.keys()):
            self.cli_log_slot_inf(slot, "Detected port {:s} loopback transceiver {:s}".format(port, self._nic_ctrl_list[slot]._loopback_sn[port]))
        else:
            self.cli_log_slot_inf(slot, "Missing port {:s} loopback info".format(port))
            return False

        return True

    def mtp_nic_read_salina_transceiver_sn(self, slot, port):
        if not self._nic_ctrl_list[slot].nic_read_salina_transceiver_sn(port):
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        if port in list(self._nic_ctrl_list[slot]._loopback_sn.keys()):
            self.cli_log_slot_inf(slot, "Detected port {:s} loopback transceiver {:s}".format(port, self._nic_ctrl_list[slot]._loopback_sn[port]))
        else:
            self.cli_log_slot_inf(slot, "Missing port {:s} loopback info".format(port))
            return False

        return True

    def mtp_nic_read_vulcano_transceiver_sn(self, slot, port):
        if not self._nic_ctrl_list[slot].nic_read_vulcano_transceiver_sn(port):
            self.mtp_get_nic_err_msg(slot)
            self.mtp_dump_nic_err_msg(slot)
            return False

        if port in list(self._nic_ctrl_list[slot]._loopback_sn.keys()):
            self.cli_log_slot_inf(slot, "Detected port {:s} loopback transceiver {:s}".format(port, self._nic_ctrl_list[slot]._loopback_sn[port]))
        else:
            self.cli_log_slot_inf(slot, "Missing port {:s} loopback info".format(port))
            return False

        return True

    def fst_setup_penctrl_ssh(self, slot, ip):
        cmd = "ls ~/.ssh/id_rsa"
        if not self.mtp_mgmt_exec_cmd(cmd):
            self.cli_log_err("Executing command {:s} failed".format(cmd), level=0)
            return False
        cmd_buf = self.mtp_get_cmd_buf()
        if "No such file" in cmd_buf:
            # create new ssh key-pair
            cmd_list = [
                "mkdir ~/.ssh",
                "chmod 700 ~/.ssh",
                "< /dev/zero ssh-keygen -q -N \"\" -f ~/.ssh/id_rsa"
            ]
            for cmd in cmd_list:
                if not self.mtp_mgmt_exec_cmd(cmd):
                    self.cli_log_err("Executing command failed {:s}".format(cmd), level=0)
                    return False

        cmd_list = [
            "export \"DSC_URL\"=\"http://{:s}\"".format(ip),                                                                              # set env variable used by penctl
            "{:s} -a {:s} system enable-sshd".format("/home/diag/penctl.linux.042021", "/home/diag/penctl.token"),                        # penctl enable-sshd
            "{:s} -a {:s} update ssh-pub-key -f ~/.ssh/id_rsa.pub".format("/home/diag/penctl.linux.042021", "/home/diag/penctl.token")    # penctl point to the pub key
        ]
        for cmd in cmd_list:
            if not self.mtp_mgmt_exec_cmd_para(slot, cmd):
                self.cli_log_slot_err(slot, "{:s} failed".format(cmd))
                return False

        return True

    def fst_get_eth_mnic(self, slot, bus):
        # FIND CORRESPONDING ETH INTF NAME
        cmd = "grep PCI_SLOT_NAME /sys/class/net/*/device/uevent | grep \"{:s}\"".format(bus)
        cmd_buf = self._nic_ctrl_list[slot].mtp_get_info(cmd)
        eth_pattern = r'/sys/class/net/(.*)/device/uevent:PCI_SLOT_NAME'
        matched = re.findall(eth_pattern, cmd_buf)
        eth = ""
        if matched:
            eth = matched[0]
        if not cmd_buf or not eth:
            self.cli_log_slot_err(slot, "Unable to find ethernet interface for PCI device {:s}".format(bus))
            self.log_nic_file(slot, "#############= FA DUMP =#############")
            self.mtp_mgmt_exec_cmd_para(slot, "grep PCI_SLOT_NAME /sys/class/net/*/device/uevent")
            self.mtp_mgmt_exec_cmd_para(slot, "lshw -c network -businfo")
            self.log_nic_file(slot, "#############= END FA DUMP =#############")
            return ""
        self._nic_ctrl_list[slot]._fst_eth_mnic = eth

        # DECODE IP ADDRESS
        bus_str = bus.split(":", 1)[0]
        bus_int = int(bus_str, 16)
        if self.mtp_get_nic_type(slot) == NIC_Type.NAPLES100:
            intf_ip_addr = "169.254.0.2/24"
            ssh_ip_addr = "169.254.0.1"
        else:
            intf_ip_addr = "169.254.{:d}.2/24".format(bus_int)
            ssh_ip_addr = "169.254.{:d}.1".format(bus_int)

        # ASSIGN IP ADDRESS TO ETH INTF
        self.cli_log_slot_inf(slot, "Enable NIC mnic {:s}".format(eth))
        self.mtp_mgmt_exec_cmd_para(slot, "ifconfig {:s} down".format(eth))
        time.sleep(1)
        self.mtp_mgmt_exec_cmd_para(slot, "ifconfig {:s} {:s}".format(eth, intf_ip_addr))
        self.mtp_mgmt_exec_cmd_para(slot, "ifconfig {:s} up".format(eth))
        time.sleep(1)
        if eth+": ERROR" in self.mtp_get_nic_cmd_buf(slot):
            self.cli_log_slot_err(slot, "Failed to enable NIC mnic")
            self.mtp_mgmt_exec_cmd_para(slot, "ifconfig {:s} down".format(eth))
            time.sleep(1)
            return ""
        return ssh_ip_addr

    def fst_disable_eth_mnic(self, slot):
        if not self.mtp_mgmt_exec_cmd_para(slot, "ifconfig {:s} down".format(self._nic_ctrl_list[slot]._fst_eth_mnic)):
            self.cli_log_slot_err(slot, "Failed to turn off eth interface {:s}".format(eth))
            return False
        return True

    def fst_setup_nic_ssh(self, slot):
        bus = self._nic_ctrl_list[slot]._fst_pcie_bus

        nic_mgmt_ip = self.fst_get_eth_mnic(slot, bus)
        if not nic_mgmt_ip:
            return False

        self._nic_ctrl_list[slot]._ip_addr = nic_mgmt_ip

        nic_type = self.mtp_get_nic_type(slot)
        if nic_type in CAPRI_NIC_TYPE_LIST and nic_type != NIC_Type.NAPLES100:
            if not self.fst_setup_penctrl_ssh(slot, nic_mgmt_ip):
                return False

        return True

    def fst_check_nic_pcie(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        bus = self._nic_ctrl_list[slot]._fst_pcie_bus
        if nic_type in ELBA_NIC_TYPE_LIST:
            expected_speed = "16"
        elif nic_type in GIGLIO_NIC_TYPE_LIST:
            expected_speed = "16"
        elif nic_type in SALINA_NIC_TYPE_LIST:
            expected_speed = "32"
        else:
            expected_speed = "8"

        if nic_type in (NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2INTERP, NIC_Type.POMONTEDELL, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL,
                        NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4,
                        NIC_Type.NAPLES100):
            expected_width = "16"
        elif nic_type in GIGLIO_NIC_TYPE_LIST:
            expected_width = "16"
        elif nic_type in SALINA_NIC_TYPE_LIST:
            expected_width = "16"
        else:
            expected_width = "8"

        if not self.mtp_mgmt_exec_cmd_para(slot, "lspci -vv -s {:s} | grep LnkSta:".format(bus)):
            self.cli_log_err("Unable to retrieve link speed and width")
            return False
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        if "Speed {:s}GT/s".format(expected_speed) not in cmd_buf:
            self.cli_log_slot_err(slot, "PCIE link came up as {:s}".format(cmd_buf))
            return False

        if "Width x{:s}".format(expected_width) not in cmd_buf:
            self.cli_log_slot_err(slot, "PCIE link came up as {:s}".format(cmd_buf))
            return False

        self.cli_log_slot_inf(slot, "PCIE link came up {:s}GT/s x{:s}".format(expected_speed, expected_width))
        return True

    def fst_fetch_nic_info(self, slot, scanned_fru=None):
        nic_type = self.mtp_get_nic_type(slot)

        if not self.fst_get_nic_fru_info(slot, scanned_fru):
            return False

        if not self.fst_get_nic_fw_info(slot):
            return False

        if nic_type in (NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4):
            if not self.fst_nic_set_perf_mode(slot):
                pass

        if not self.fst_check_boot_image(slot):
            return False

        # if nic_type in ELBA_NIC_TYPE_LIST:
        #     if nic_type in FPGA_TYPE_LIST:
        #         cmd = "/nic/bin/halctl show system --yaml"
        #         if not self.mtp_nic_fst_exec_cmd(slot, cmd)):
        #             self.cli_log_slot_err(slot, "failed to execute halctl show system")
        #             return False
        #     else:
        #         cmd = "/nic/bin/pdsctl show system --yaml"
        #         if not self.mtp_nic_fst_exec_cmd(slot, cmd)):
        #             self.cli_log_slot_err(slot, "failed to execute pdsctl show system")
        #             return False

        #     die_temp = False
        #     local_temp = False
        #     die_temp_match = re.search(r'dietemperature:\s([0-9]+)$', self.mtp_get_nic_cmd_buf(slot))
        #     if die_temp_match:
        #         die_temp_val=int(die_temp_match.group(0).strip())
        #         die_temp = True
        #     else:
        #         self.cli_log_slot_err(slot, "Failed to find die temperature value")

        #     local_temp_match = re.search(r'localtemperature:\s([0-9]+)$', self.mtp_get_nic_cmd_buf(slot))
        #     if local_temp_match:
        #         local_temp_val=int(local_temp_match.group(0).strip())
        #         local_temp = True
        #     else:
        #         self.cli_log_slot_err(slot, "Failed to find local temperature value")

        #     if die_temp: self.cli_log_slot_inf(slot, "dietemperature: {:d}".format(die_temp_val))
        #     if local_temp: self.cli_log_slot_inf(slot, "localtemperature: {:d}".format(local_temp_val))

        return True

    def fst_fetch_salina_info(self, slot):
        nic_type = self.mtp_get_nic_type(slot)
        bus = self._nic_ctrl_list[slot]._fst_pcie_bus
        sn = self.mtp_get_nic_sn(slot)

        if not self.mtp_mgmt_exec_cmd_para(slot, "cd {:s}".format("/home/diag")):
            self.cli_log_err("Unable to execute change directory command")
            return False

        if not self.mtp_mgmt_exec_cmd_para(slot, "./nicctl show card -d"):
            self.cli_log_err("Unable to retrieve card info")
            return False
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        # parse card info
        nic_info = self.fst_parse_salina_nic_info(cmd_buf, slot)
        if not nic_info:
            self.cli_log_err("Unable to parse nic info")
            return False

        if not self.mtp_mgmt_exec_cmd_para(slot, "./nicctl show firmware -d"):
            self.cli_log_err("Unable to retrieve firmware info")
            return False
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        # parse firmware info
        nic_firmware = self.fst_parse_salina_firmware_info(cmd_buf, slot, nic_info[sn]["Id"])
        if not nic_firmware:
            self.cli_log_err("Unable to parse firmware info")
            return False

        if not self.fst_get_salina_nic_fw_info(slot, nic_firmware):
            self.cli_log_err("Unable to parse correct firmware info format")
            return False

        self.cli_log_slot_inf(slot, "FETCH Salina nic card info")
        return True

    def fst_parse_salina_nic_info(self, data, slot):
        sn = self.mtp_get_nic_sn(slot)
        entries = data.strip().split('-------------------------------------------------------------------------------------')
        ipc_to_id = {}
        for entry in entries:
            lines = entry.strip().split('\n')
            entry_data = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    entry_data[key.strip()] = value.strip()
            if 'IPC BDF' in entry_data and 'Id' in entry_data and 'Serial number' in entry_data and entry_data['Serial number'] == sn:
                ipc_to_id[sn] = entry_data
                break
        return ipc_to_id

    def fst_parse_salina_firmware_info(self, data, slot, id):
        sn = self.mtp_get_nic_sn(slot)
        json_data = libmfg_utils.extract_json(data)
        fw_to_json = json.loads(json_data)
        nic_list = fw_to_json.get('nic', [])
        for nic in nic_list:
            if nic.get('id') == id:
                return nic
        return None

    def fst_get_salina_nic_fw_info(self, slot, fwlist):
        nic_type = self.mtp_get_nic_type(slot)
        sn = self.mtp_get_nic_sn(slot)
        self.cli_log_slot_inf(slot, "Retrieve FW info")

        if "boot0" in fwlist["firmware"]:
            if "boot0" in fwlist["firmware"]["boot0"] and "software_version" in fwlist["firmware"]["boot0"]["boot0"]:
                self.cli_log_slot_inf(slot, "boot0:     {:s}   {:s} rev{:s}".format(fwlist["firmware"]["boot0"]["boot0"]["software_version"],
                                  fwlist["firmware"]["boot0"]["boot0"]["build_date"], str(fwlist["firmware"]["boot0"]["boot0"]["image_version"])))

        for partition in ["mainfwa", "mainfwb", "goldfw"]:
            try:
                if partition == "mainfwa":
                    self.cli_log_slot_inf(slot, "{:s}(fw_a):   {:s}   {:s} ".format(partition, fwlist["firmware"][partition]["fw_a"]["software_version"], fwlist["firmware"][partition]["fw_a"]["build_date"]))
                    self.cli_log_slot_inf(slot, "{:s}(uboot_a):   {:15s}   {:s} ".format(partition, fwlist["firmware"][partition]["uboot_a"]["software_version"], fwlist["firmware"][partition]["uboot_a"]["build_date"]))
                elif partition == "mainfwb":
                    self.cli_log_slot_inf(slot, "{:s}(fw_b):   {:15s}   {:s} ".format(partition, fwlist["firmware"][partition]["fw_b"]["software_version"], fwlist["firmware"][partition]["fw_b"]["build_date"]))
                    self.cli_log_slot_inf(slot, "{:s}(uboot_b):   {:15s}   {:s} ".format(partition, fwlist["firmware"][partition]["uboot_b"]["software_version"], fwlist["firmware"][partition]["uboot_b"]["build_date"]))
                else:
                    self.cli_log_slot_inf(slot, "{:s}(goldfip):   {:15s}   {:s} ".format(partition, fwlist["firmware"][partition]["goldfip"]["software_version"], fwlist["firmware"][partition]["goldfip"]["build_date"]))
                    self.cli_log_slot_inf(slot, "{:s}(golduboot):   {:15s}   {:s} ".format(partition, fwlist["firmware"][partition]["golduboot"]["software_version"], fwlist["firmware"][partition]["golduboot"]["build_date"]))
            except KeyError as e:
                self.cli_log_slot_err(slot, "FWLIST missing {:s} info".format(partition))
                err_msg = traceback.format_exc()
                self._nic_ctrl_list[slot].nic_set_err_msg(err_msg)
                self.mtp_get_nic_err_msg(slot)
                return False
        self.cli_log_slot_inf(slot, "")

        return True


    def fst_get_nic_fru_info(self, slot, scanned_fru=None):
        cmd = "cat /tmp/fru.json"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to fetch SN")
            return False
        fru_json = re.findall(r"{.+}", self.mtp_get_nic_cmd_buf(slot), re.DOTALL)
        if not fru_json:
            self.cli_log_slot_err(slot, "Get FRU failed")
            return False
        fru = json.loads(fru_json[0])

        if fru["serial-number"]:
            sn = fru["serial-number"]
        else:
            self.cli_log_slot_err(slot, "Unable to parse serial-number from FRU")
            sn = "UNKNOWN"
        if self.mtp_get_nic_sn(slot) is None:
            self.mtp_set_nic_sn(slot, sn)
        if sn != self.mtp_get_nic_sn(slot):
            self.cli_log_slot_err(slot, "SN in FRU doesnt match: got {:s}, expected {:s}".format(sn, self.mtp_get_nic_sn(slot)))
            return False

        try:
            pn = fru["board-assembly-area"]
            pn = pn.strip()
        except KeyError:
            try:
                pn = fru["part-number"]
                pn = pn.strip()
            except KeyError:
                self.cli_log_slot_err(slot, "Unable to parse part-number from FRU")
                pn = ""
        nic_type = get_product_name_from_pn_and_sn(pn, sn)
        if nic_type != self.mtp_get_nic_type(slot):
            self.cli_log_slot_err(slot, "Unknown PN read from FRU: {:s} ({:s})".format(pn, str(nic_type)))
            return False
        self.cli_log_slot_inf(slot, "SN = {:s}, PN = {:s}, TYPE = {:s}".format(sn, pn, nic_type))

        if scanned_fru:
            scanned_pn = list()
            scanned_mac = list()
            for slot_index in range(self._slots):
                key = libmfg_utils.nic_key(slot_index)
                if scanned_fru[key]["VALID"]:
                    scanned_pn.append(scanned_fru[key][bf.PN].lower())
                    scanned_mac.append(scanned_fru[key][bf.MAC].lower())
            if pn.lower() not in scanned_pn:
                self.cli_log_slot_err(slot, "PN {:s} read from FRU file /tmp/fru.json not in scanned PN list: {:s}".format(pn, str(scanned_pn)))
                return False
            # get mac address from /tmp/fru.json and compare with scanned mac address
            try:
                mac = fru["mac-address"]
            except KeyError:
                self.cli_log_slot_err(slot, "Unable to parse mac-address from FRU")
                return False
            else:
                self.cli_log_slot_inf(slot, "MAC = {:s}".format(mac))
            if mac.replace(":", "").lower() not in scanned_mac:
                self.cli_log_slot_err(slot, "MAC {:s} read from FRU file /tmp/fru.json not in scanned MAC list: {:s}".format(mac, str(scanned_mac)))
                return False

        return True

    def fst_get_nic_fw_info(self, slot):
        verify_rc = True
        nic_type = self.mtp_get_nic_type(slot)
        self.cli_log_slot_inf(slot, "Retrieve FW info")

        if nic_type == NIC_Type.ORTANO2ADIIBM:
            cmd = "'export PATH=$PATH:/nic/bin; /nic/tools/fwupdate -l'"
        else:
            cmd = "/nic/tools/fwupdate -l"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to execute fwupdate -l")
            return False
        fw_json = re.findall(r"{.+}", self.mtp_get_nic_cmd_buf(slot), re.DOTALL)
        if not fw_json:
            self.cli_log_slot_err(slot, "failed to execute fwupdate -l")
            return False
        fwlist = json.loads(fw_json[0])
        if nic_type in SALINA_DPU_NIC_TYPE_LIST:
            goldfw_ver = image_control.get_goldfw(self, slot, FF_Stage.FF_SWI)["version"]
            mainfw_ver = image_control.get_mainfw(self, slot, FF_Stage.FF_SWI)["version"]
            try:
                ### Display FW version info
                # A35 boot0
                partition = "a35-boot0"
                self.cli_log_slot_inf(slot, "{:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["a35-boot0"]["software_version"], fwlist[partition]["a35-boot0"]["build_date"]))
                # A35 fwa and uboota 
                partition = "extosa"
                self.cli_log_slot_inf(slot, "A35 uboota {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["uboot-a"]["software_version"], fwlist[partition]["uboot-a"]["build_date"]))
                self.cli_log_slot_inf(slot, "A35 mainfwa {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["fw-a"]["software_version"], fwlist[partition]["fw-a"]["build_date"]))
                # self.cli_log_slot_inf(slot, "A35 uboota {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["uboot_a"]["software_version"], fwlist[partition]["uboot_a"]["build_date"]))
                # self.cli_log_slot_inf(slot, "A35 mainfwa {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["fw_a"]["software_version"], fwlist[partition]["fw_a"]["build_date"]))
                # A35 fwb and ubootb 
                partition = "extosb"
                self.cli_log_slot_inf(slot, "A35 ubootb {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["uboot-b"]["software_version"], fwlist[partition]["uboot-b"]["build_date"]))
                self.cli_log_slot_inf(slot, "A35 mainfwb {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["fw-b"]["software_version"], fwlist[partition]["fw-b"]["build_date"]))
                # self.cli_log_slot_inf(slot, "A35 ubootb {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["uboot_b"]["software_version"], fwlist[partition]["uboot_b"]["build_date"]))
                # self.cli_log_slot_inf(slot, "A35 mainfwb {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["fw_b"]["software_version"], fwlist[partition]["fw_b"]["build_date"]))
                # A35 goldfw and ubootg 
                partition = "extosgoldfw"
                self.cli_log_slot_inf(slot, "A35 ubootg {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["a35-golduboot"]["software_version"], fwlist[partition]["a35-golduboot"]["build_date"]))
                self.cli_log_slot_inf(slot, "A35 goldfw {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["a35-goldfip"]["software_version"], fwlist[partition]["a35-goldfip"]["build_date"]))
                # self.cli_log_slot_inf(slot, "A35 ubootg {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["golduboot"]["software_version"], fwlist[partition]["golduboot"]["build_date"]))
                # self.cli_log_slot_inf(slot, "A35 goldfw {:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["goldfip"]["software_version"], fwlist[partition]["goldfip"]["build_date"]))
                # N1 boot0
                partition = "n1-boot0"
                self.cli_log_slot_inf(slot, "{:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["n1-boot0"]["software_version"], fwlist[partition]["n1-boot0"]["build_date"]))
                # N1 mainfwa and uboota 
                partition = "mainfwa"
                self.cli_log_slot_inf(slot, "N1 {:s} uboota:   {:15s}   {:s} ".format(partition, fwlist[partition]["n1-uboot-a"]["software_version"], fwlist[partition]["n1-uboot-a"]["build_date"]))
                # self.cli_log_slot_inf(slot, "N1 {:s} uboota:   {:15s}   {:s} ".format(partition, fwlist[partition]["n1-uboot_a"]["software_version"], fwlist[partition]["n1-uboot_a"]["build_date"]))
                self.cli_log_slot_inf(slot, "N1 {:s} kernel_fit:   {:15s}   {:s} ".format(partition, fwlist[partition]["kernel_fit"]["software_version"], fwlist[partition]["kernel_fit"]["build_date"]))
                self.cli_log_slot_inf(slot, "N1 {:s} system_image:   {:15s}   {:s} ".format(partition, fwlist[partition]["system_image"]["software_version"], fwlist[partition]["system_image"]["build_date"]))
                # N1 mainfwb and ubootb
                partition = "mainfwb"
                self.cli_log_slot_inf(slot, "N1 {:s} ubootb:   {:15s}   {:s} ".format(partition, fwlist[partition]["n1-uboot-b"]["software_version"], fwlist[partition]["n1-uboot-b"]["build_date"]))
                # self.cli_log_slot_inf(slot, "N1 {:s} ubootb:   {:15s}   {:s} ".format(partition, fwlist[partition]["n1-uboot_b"]["software_version"], fwlist[partition]["n1-uboot_b"]["build_date"]))
                self.cli_log_slot_inf(slot, "N1 {:s} kernel_fit:   {:15s}   {:s} ".format(partition, fwlist[partition]["kernel_fit"]["software_version"], fwlist[partition]["kernel_fit"]["build_date"]))
                self.cli_log_slot_inf(slot, "N1 {:s} system_image:   {:15s}   {:s} ".format(partition, fwlist[partition]["system_image"]["software_version"], fwlist[partition]["system_image"]["build_date"]))
                # N1 goldfw and ubootg
                partition = "n1-goldfw"
                self.cli_log_slot_inf(slot, "N1 {:s} ubootg:   {:15s}   {:s} ".format(partition, fwlist[partition]["n1-uboot-g"]["software_version"], fwlist[partition]["n1-uboot-g"]["build_date"]))
                self.cli_log_slot_inf(slot, "N1 {:s} kernel:   {:15s}   {:s} ".format(partition, fwlist[partition]["n1-kernel-g"]["software_version"], fwlist[partition]["n1-kernel-g"]["build_date"]))

                # # Verify loaded fw version
                # # verify goldfw version
                # for k, v in fwlist["n1-goldfw"].items():
                #     if v["software_version"] != goldfw_ver:
                #         self.cli_log_slot_err(slot, "n1-goldfw {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                #         verify_rc = False
                # for k, v in fwlist["extosgoldfw"].items():
                #     if v["software_version"] != goldfw_ver:
                #         self.cli_log_slot_err(slot, "extosgoldfw {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                #         verify_rc = False
                # # verify mainfw version
                # for k, v in fwlist["mainfwa"].items():
                #     if v["software_version"] != mainfw_ver:
                #         self.cli_log_slot_err(slot, "mainfwa {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                #         verify_rc = False
                # for k, v in fwlist["extosa"].items():
                #     if v["software_version"] != mainfw_ver:
                #         self.cli_log_slot_err(slot, "extosa {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                #         verify_rc = False
                # for k, v in fwlist["mainfwb"].items():
                #     if v["software_version"] != mainfw_ver:
                #         self.cli_log_slot_err(slot, "mainfwb {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                #         verify_rc = False
                # for k, v in fwlist["extosb"].items():
                #     if v["software_version"] != mainfw_ver:
                #         self.cli_log_slot_err(slot, "extosb {:s} version not match, {:s} <--> {:s}".format(k, v["software_version"], goldfw_ver))
                #         verify_rc = False
            except KeyError as e:
                self.cli_log_slot_err(slot, "FWLIST missing {:s} info".format(partition))
                err_msg = traceback.format_exc()
                self._nic_ctrl_list[slot].nic_set_err_msg(err_msg)
                self.mtp_get_nic_err_msg(slot)
                return False
        else:
            if "boot0" in fwlist:
                self.cli_log_slot_inf(slot, "boot0:     {:15s}   {:s} rev{:d}".format(fwlist["boot0"]["image"]["software_version"],
                                    fwlist["boot0"]["image"]["build_date"], fwlist["boot0"]["image"]["image_version"]))
            else:
                if nic_type == NIC_Type.NAPLES100:
                    if "uboot" in fwlist:
                        self.cli_log_slot_inf(slot, "uboot:     {:15s}   {:s}".format(fwlist["uboot"]["image"]["software_version"], fwlist["uboot"]["image"]["build_date"]))
                    else:
                        self.cli_log_slot_err(slot, "FWLIST missing uboot info")
                elif nic_type != NIC_Type.ORTANO2ADIIBM:
                    self.cli_log_slot_err(slot, "FWLIST missing boot0 info")
            for partition in ["mainfwa", "mainfwb", "goldfw", "diagfw", "extdiag"]:
                if nic_type in FPGA_TYPE_LIST and (partition == "mainfwa" or partition == "mainfwb"):
                    continue
                if nic_type not in FPGA_TYPE_LIST and partition == "extdiag":
                    continue
                try:
                    if nic_type == NIC_Type.ORTANO2ADIIBM and partition in ["mainfwa", "mainfwb"]:
                        if "fip" in fwlist[partition]:
                            self.cli_log_slot_inf(slot, "{:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["fip"]["software_version"], fwlist[partition]["fip"]["build_date"]))
                        else:
                            self.cli_log_slot_err(slot, "FWLIST missing fip info for ADI IBM")
                            return False
                    elif nic_type in GIGLIO_NIC_TYPE_LIST and partition in ["mainfwa", "mainfwb"]:
                        self.cli_log_slot_inf(slot, "NO {:s} needed for {:s}".format(partition, nic_type))
                    else:
                        self.cli_log_slot_inf(slot, "{:s}:   {:15s}   {:s} ".format(partition, fwlist[partition]["kernel_fit"]["software_version"], fwlist[partition]["kernel_fit"]["build_date"]))
                except KeyError as e:
                    self.cli_log_slot_err(slot, "FWLIST missing {:s} info".format(partition))
                    err_msg = traceback.format_exc()
                    self._nic_ctrl_list[slot].nic_set_err_msg(err_msg)
                    self.mtp_get_nic_err_msg(slot)
                    return False
        self.cli_log_slot_inf(slot, "")

        return verify_rc

    def fst_check_boot_image(self, slot):
        cmd = "/nic/tools/fwupdate -r"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to execute fwupdate -r")
            return False
        cmd_buf = self.mtp_get_nic_cmd_buf(slot)
        match = re.findall(r"(\w+fw\w?|extdiag)", cmd_buf)
        if match:
            self._nic_ctrl_list[slot]._boot_image = match[0]
        else:
            self.cli_log_slot_err(slot, "Unable to read current boot image")
            return False

        boot_image = self._nic_ctrl_list[slot]._boot_image
        nic_type = self.mtp_get_nic_type(slot)

        if nic_type in FPGA_TYPE_LIST:
            if boot_image != "extdiag":
                self.cli_log_slot_err(slot, "Booted from {:s}, expecting extdiag".format(boot_image))
                return False
        elif nic_type in (NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICRS4, NIC_Type.GINESTRA_S4, NIC_Type.GINESTRA_CIS):
            if boot_image != "goldfw":
                self.cli_log_slot_err(slot, "Booted from {:s}, expecting goldfw".format(boot_image))
                return False
        else:
            if boot_image != "mainfwa":
                self.cli_log_slot_err(slot, "Booted from {:s}, expecting mainfwa".format(boot_image))
                return False

        return True

    def fst_board_config(self, slot):
        # SET BOARD CONFIG
        cmd = "'export LD_LIBRARY_PATH=$LD_LIBRAY_PATH:/nic/lib;/nic/bin/board_config -G 1 -F 0 -O 1'"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to set board config")
            return False

        # DISPLAY BOARD CONFIG
        cmd = "'export LD_LIBRARY_PATH=$LD_LIBRAY_PATH:/nic/lib;/nic/bin/board_config -r'"
        if not self.mtp_nic_fst_exec_cmd(slot, cmd):
            self.cli_log_slot_err(slot, "failed to set board config")
            return False

        # VERIFY BOARD CONFIG
        buf = self.mtp_get_nic_cmd_buf(slot)
        match = re.findall(r"(gold_on_stop\s+1)", buf)
        match1 = re.findall(r"(gold_no_hostif\s+0)", buf)
        match2 = re.findall(r"(gold_oob\s+1)", buf)
        if not match or not match1 or not match2:
            self.cli_log_slot_err(slot, "board config verify failed")
            return False

        return True

    @parallelize.parallel_nic_using_console
    def mtp_nic_device_conf_verify(self, slot):
        if not self._nic_ctrl_list[slot].device_conf_verify():
            self.mtp_get_nic_err_msg(slot)
            return False
        return True
