import sys, os, re
import ipaddress
import libmfg_utils
import libtest_config
import libtest_utils
from libmtp_ctrl import mtp_ctrl
from libpdu_ctrl import pdu_ctrl
from libnic_ctrl import nic_ctrl
from libdefs import *
from libmfg_cfg import *
from tests import *

class test_inst:
    def __init__(self, testsuite_file, skip_test_list = [], repeat_test_list = [()], stop_on_test_failure = []):
        self.test_config = dict()
        self.barcode_scans = dict()
        self.stage = ""
        self.uut_name = ""
        self.uut_type = ""
        self.uut_id = None
        self.test_list = list()
        self.image = dict()
        self.test_parameters = dict()
        self.stop_on_test_failure = stop_on_test_failure
        self.testsuite = self.parse_testsuite(testsuite_file)
        self.skip_test_list = skip_test_list
        self.repeat_test_list = repeat_test_list
        if not self.parse_test_list():
            raise Exception("Test aborted")

        self.mtp = None
        self.nic = [None] * MTP_Const.MTP_SLOT_NUM
        self.pdu = None

        self._filep = None
        self._diag_filep = None
        self._diag_cmd_filep = None
        self._diag_nic_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        self._console_filep = None
        self._pdu_filep = None

        self._factory_location = Factory.UNKNOWN

        self.logfile_dir_list = None
        self.open_file_track_list = None

    def parse_testsuite(self, testsuite_file):
        yaml_config = libtest_config.parse_config(testsuite_file)
        if "Stage" not in yaml_config.keys():
            libmfg_utils.cli_err("{:s} missing key field: STAGE".format(testsuite_file))
            return None
        else:
            self.stage = self.parse_stage(yaml_config["Stage"])

        if "UUT_Name" not in yaml_config.keys():
            libmfg_utils.cli_err("{:s} missing key field: UUT_Name".format(testsuite_file))
            return None
        else:
            self.parse_uut_name(yaml_config["UUT_Name"])

        if "Test list" not in yaml_config.keys():
            libmfg_utils.cli_err("{:s} missing key field: Test list".format(testsuite_file))
            return None
        else:
            self.test_list = yaml_config["Test list"]

        if "Images" not in yaml_config.keys():
            libmfg_utils.cli_err("{:s} missing key field: Images".format(testsuite_file))
            return None
        else:
            self.image = yaml_config["Images"]

        if "Parameters" not in yaml_config.keys():
            pass
        else:
            self.test_parameters = yaml_config["Parameters"]

        return yaml_config

    def parse_stage(self, stage_str):
        if stage_str.upper() == "DL":
            return FF_Stage.FF_DL
        elif stage_str.upper() == "DL1":
            return FF_Stage.FF_DL1
        elif stage_str.upper() == "P2C":
            return FF_Stage.FF_P2C
        elif stage_str.upper() == "2C-H":
            return FF_Stage.FF_2C_H
        elif stage_str.upper() == "2C-L":
            return FF_Stage.FF_2C_L
        elif stage_str.upper() == "4C-H":
            return FF_Stage.FF_4C_H
        elif stage_str.upper() == "4C-L":
            return FF_Stage.FF_4C_L
        elif stage_str.upper() == "SWI":
            return FF_Stage.FF_SWI
        elif stage_str.upper() == "FST":
            return FF_Stage.FF_FST
        else:
            return None

    def parse_uut_name(self, uut_str):
        if uut_str.upper() == "LIPARI":
            self.uut_type = UUT_Type.TOR
            self.uut_name = uut_str.upper()
        else:
            return None

    def parse_test_list(self):
        ### REMOVE SKIPPED TESTS FROM THE TEST_LIST
        if self.skip_test_list:
            new_test_list = []
            for test in self.test_list:
                if test in self.skip_test_list:
                    continue
                else:
                    new_test_list.append(test)

            self.test_list = new_test_list[:]


        ### ADD REPEATED TESTS AS MULTIPLE TESTS
        ### improvement: print iteration number somehow
        if self.repeat_test_list:
            repeat_test_list = self.parse_repeat_test_list(self.repeat_test_list)
            if repeat_test_list is None:
                return False

            for iterations, testname in repeat_test_list:
                new_test_list = list()
                # find where in the test sequence
                test_idx = 0
                while test_idx < len(self.test_list):
                    if self.test_list[test_idx] == testname:
                        # insert added iterations
                        new_test_list = self.test_list[:test_idx+1] + [testname] * (iterations-1) + self.test_list[test_idx+1:]
                        test_idx += (iterations-1)
                        self.test_list = new_test_list[:]
                    test_idx += 1
                self.test_list = new_test_list[:]

        return True

    def parse_repeat_test_list(self, x):
        """
            list to 2-d structure
            [1, a, 2, b] --> [(1,a), (2,b)]
        """
        try:
            y = [(int(x[i]),x[i+1]) for i in range(0,len(x),2)]
        except ValueError as e:
            libmfg_utils.cli_err("Bad iteration# in repeat test list: {}".format(e))
            return None
        except IndexError as e:
            libmfg_utils.cli_err("Missing test name in repeat test list")
            return None
        return y

    def mtp_mgmt_ctrl_init(self, mtp_cfg_db, mtp_id):
        mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
        mtp_ts_cfg = mtp_cfg_db.get_mtp_console(mtp_id)
        if not mtp_ts_cfg:
            libmfg_utils.cli_err(mtp_cli_id_str + "Unable to find termserver config")
            return None
        mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
        if not mtp_mgmt_cfg:
            libmfg_utils.cli_err(mtp_cli_id_str + "Unable to find access credentials in config")
            return False
        mtp_pdu_cfg = mtp_cfg_db.get_mtp_pdu(mtp_id)
        if not mtp_pdu_cfg:
            libmfg_utils.cli_err(mtp_cli_id_str + "Unable to find apc config")
            return False
        mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
        if self.uut_name == "TAORMINA":
            num_of_slots = 2
        elif self.uut_name == "LIPARI":
            num_of_slots = 8
        else:
            num_of_slots = 10
        mtp_mgmt_ctrl = mtp_ctrl(
            mtp_id, 
            None, 
            None, 
            [None], 
            ts_cfg=mtp_ts_cfg, 
            mgmt_cfg=mtp_mgmt_cfg, 
            slots_to_skip=mtp_slots_to_skip, 
            test_inst=self,
            num_of_slots=num_of_slots)
        if not mtp_mgmt_ctrl:
            libmfg_utils.cli_err(mtp_cli_id_str + "Unable to initialize MTP info")
            return None
        self.mtp = mtp_mgmt_ctrl
        self.nic = [None] * self.mtp._slots # re-init

        # init logfiles
        self.open_logfiles()

        # maintain in both places for now
        self.mtp._diag_filep = self._diag_filep
        self.mtp._diag_cmd_filep = self._diag_cmd_filep

        self.get_mtp_factory_location()
        self.pdu_init(mtp_pdu_cfg)

        return mtp_mgmt_ctrl

    def pdu_init(self, pdu_cfg):
        self.pdu = pdu_ctrl(self, pdu_cfg)
        return True

    def cli_log_inf(self, msg, level = 1):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self.mtp._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(cli_id_str + indent + msg)

    def cli_log_report_inf(self, msg):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self.mtp._id)
        prefix = "==> "
        postfix = " <=="
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, cli_id_str + prefix + msg + postfix)
        else:
            libmfg_utils.cli_inf(cli_id_str + prefix + msg + postfix)

    def cli_log_err(self, msg, level = 1):
        if msg is None:
            msg = ""
        cli_id_str = libmfg_utils.id_str(mtp = self.mtp._id)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_err(self._filep, cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_err(cli_id_str + indent + msg)

    def cli_log_slot_inf(self, slot, msg, level = 0):
        if msg is None:
            msg = ""
        nic_cli_id_str = libmfg_utils.id_str(mtp = self.mtp._id, nic = slot)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_inf(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_inf(nic_cli_id_str + indent + msg)

    def cli_log_slot_err(self, slot, msg, level = 0):
        if msg is None:
            msg = ""
        nic_cli_id_str = libmfg_utils.id_str(mtp = self.mtp._id, nic = slot)
        indent = "    " * level
        if self._filep:
            libmfg_utils.cli_log_err(self._filep, nic_cli_id_str + indent + msg)
        else:
            libmfg_utils.cli_err(nic_cli_id_str + indent + msg)

    def cli_log_slot_inf_lock(self, slot, msg, level = 0):
        self.mtp._lock.acquire()
        self.cli_log_slot_inf(slot, msg, level)
        self.mtp._lock.release()

    def cli_log_slot_err_lock(self, slot, msg, level = 0):
        self.mtp._lock.acquire()
        self.cli_log_slot_err(slot, msg, level)
        self.mtp._lock.release()

    def cli_log_file(self, msg):
        self._filep.write("\n" + msg + "\n")

    def log_mtp_file(self, msg):
        self._diag_filep.write("\n[" + libmfg_utils.get_timestamp() + "] " + msg)
        # extra sendline to clean up log
        if self.mtp._mgmt_handle:
            self.mtp._mgmt_handle.sendline()

    def log_nic_file(self, slot, msg):
        self._diag_nic_filep_list[slot].write("\n[" + libmfg_utils.get_timestamp() + "] " + msg)
        # extra sendline to clean up log
        if self.nic[slot] is not None:
            if self.nic[slot]._nic_handle:
                self.nic[slot]._nic_handle.sendline()

    def log_pdu_file(self, msg):
        self._pdu_filep.write("\n" + msg)
        # extra sendline to clean up log
        if self.pdu._handle:
            self.pdu._handle.sendline()

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
        return duration

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
        return duration

    def mtp_get_nic_cmd_buf(self, slot):
        return self.nic[slot].nic_get_cmd_buf()

    def mtp_dump_cmd_buf(self, err_msg):
        self.cli_log_err("==== Error Message Start: ====")
        if err_msg:
            if (len(err_msg) > 512):
                top_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[:256])
                self.mtp_dump_err_msg(top_err_msg)
                self.cli_log_err("<============================>")
                bottom_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[-256:])
                self.mtp_dump_err_msg(bottom_err_msg)
            else:
                err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg)
                self.mtp_dump_err_msg(err_msg)
        self.cli_log_err("==== Error Message End: ====")

    def mtp_dump_nic_cmd_buf(self, slot):
        err_msg = self.mtp_get_nic_cmd_buf(slot)
        if err_msg is None:
            err_msg = ""
        self.cli_log_slot_err(slot, "==== Error Message Start: ====")
        if err_msg:
            if (len(err_msg) > 512):
                top_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[:256])
                self.mtp_dump_nic_err_msg(slot, top_err_msg)
                self.cli_log_slot_err(slot, "<============================>")
                bottom_err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg[-256:])
                self.mtp_dump_nic_err_msg(slot, bottom_err_msg)
            else:
                err_msg = re.sub(r'[\x00-\x1F]+', '\n', err_msg)
                self.mtp_dump_nic_err_msg(slot, err_msg)
                
        self.cli_log_slot_err(slot, "==== Error Message End: ====")

    def mtp_dump_err_msg(self, err_msg):
        for line in err_msg.splitlines():
            if self.mtp._mgmt_prompt is not None and self.mtp._mgmt_prompt in line:
                continue # skip so it doesnt mess with pexpect
            self.cli_log_err(line, level=0)

    def mtp_dump_nic_err_msg(self, slot, err_msg):
        for line in err_msg.splitlines():
            if self.mtp._mgmt_prompt in line:
                continue # skip so it doesnt mess with pexpect
            self.cli_log_slot_err(slot, line)

    def mtp_diag_fail_report(self, msg):
        err_msg = MTP_DIAG_Report.MTP_DIAG_REGRESSION_FAIL + ", ERR_MSG: {:s}".format(msg)
        self.cli_log_err(err_msg, level=0)

    def mfg_uut_summary_disp(self, summary_dict):
        final_result = True
        libmfg_utils.cli_inf("##########  MFG {:s} Test Summary  ##########".format(self.stage))
        libmfg_utils.cli_inf("-------------------- Report: ------------------")
        for mtp_id in summary_dict.keys():
            for slot, sn, nic_type, rc, retest_blocked in summary_dict[mtp_id]:
                nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id)
                if rc:
                    libmfg_utils.cli_inf("{:s}{:s} {:s} FINAL RESULT PASS".format(nic_cli_id_str, nic_type, sn))
                else:
                    final_result = False
                    if not retest_blocked:
                        libmfg_utils.cli_err("{:s}{:s} {:s} FINAL RESULT FAIL".format(nic_cli_id_str, nic_type, sn))
                    else:
                        libmfg_utils.cli_err("{:s}{:s} {:s} FINAL RESULT FAIL {:s}".format(nic_cli_id_str, nic_type, sn, MTP_DIAG_Report.NIC_RETEST_BLOCKED_MSG))
        libmfg_utils.cli_inf("------------------ Report End -----------------\n")
        return final_result

    def open_logfiles(self, run_from_mtp=False):
        if run_from_mtp:
            # Running python/pexpect on the MTP
            # Fixed directory name, always cleaned up before starting
            logfile_path = os.getcwd()
            MODIFIER = "a+"
        else:
            # Running python/pexpect outside MTP
            # Directory name contains timestamp and MTP id
            log_dir = "log/"
            log_timestamp = libmfg_utils.get_timestamp()
            mtp_id = self.mtp._id
            log_sub_dir = MTP_DIAG_Logfile.MFG_STAGE_LOG_DIR.format(self.stage, mtp_id, log_timestamp)
            os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir + log_sub_dir))

            logfile_path = log_dir + log_sub_dir
            MODIFIER = "w+"

        open_file_track_list = list()

        mtp_test_log_file = logfile_path + "/mtp_test.log"
        mtp_diag_log_file = logfile_path + "/mtp_diag.log"
        mtp_diag_cmd_log_file = logfile_path + "/mtp_diag_cmd.log"
        mtp_diagmgr_log_file = logfile_path + "/mtp_diagmgr.log"
        mtp_console_log_file = logfile_path + "/mtp_console.log"
        mtp_pdu_log_file = logfile_path + "/mtp_pdu.log"
        mtp_test_log_filep = open(mtp_test_log_file, MODIFIER)
        open_file_track_list.append(mtp_test_log_filep)
        mtp_diag_log_filep = open(mtp_diag_log_file, MODIFIER)
        open_file_track_list.append(mtp_diag_log_filep)
        mtp_diag_cmd_log_filep = open(mtp_diag_cmd_log_file, MODIFIER)
        open_file_track_list.append(mtp_diag_cmd_log_filep)
        mtp_diagmgr_log_filep = open(mtp_diagmgr_log_file, MODIFIER)
        mtp_console_log_filep = open(mtp_console_log_file, MODIFIER)
        open_file_track_list.append(mtp_console_log_filep)
        mtp_pdu_log_filep = open(mtp_pdu_log_file, MODIFIER)
        open_file_track_list.append(mtp_pdu_log_filep)

        diag_nic_log_filep_list = list()
        for slot in range(self.mtp._slots):
            key = libmfg_utils.nic_key(slot)
            diag_nic_log_file = logfile_path + "/mtp_{:s}_diag.log".format(key)
            diag_nic_log_filep = open(diag_nic_log_file, MODIFIER)
            open_file_track_list.append(diag_nic_log_filep)
            diag_nic_log_filep_list.append(diag_nic_log_filep)

        self._filep = mtp_test_log_filep
        self._diag_filep = mtp_diag_log_filep
        self._diag_cmd_filep = mtp_diag_cmd_log_filep
        self._diag_nic_filep_list = diag_nic_log_filep_list[:]
        self._console_filep = mtp_console_log_filep
        self._pdu_filep = mtp_pdu_log_filep


        self.logfile_dir = logfile_path
        self.open_file_track_list = open_file_track_list

        return logfile_path, open_file_track_list

    def close_logfiles(self, extra_fp = None):
        fp_list = self.open_file_track_list
        if extra_fp:
            fp_list = fp_list + extra_fp
        for fp in fp_list:
            fp.flush()
            fp.close()
        os.system("sync")

    def save_logfiles(self, mirror_logdir=None):
        stage = self.stage
        sn = self.mtp.get_mtp_sn()
        uut_type = self.uut_name

        if GLB_CFG_MFG_TEST_MODE:
            mfg_log_dir = "/mfg_log/{:s}/{:s}/{:s}/".format(uut_type, stage, sn)
        elif mirror_logdir:
            mfg_log_dir = mirror_logdir + "/{:s}/{:s}/{:s}/".format(uut_type, stage, sn)
        else:
            mfg_log_dir = "/tmp/mfg_log/{:s}/{:s}/{:s}/".format(uut_type, stage, sn)

        log_sub_dir = os.path.basename(os.path.dirname(self.logfile_dir))
        log_pkg_file = "{:s}.tar.gz".format(log_sub_dir)
        log_orig_path = "log/" + log_pkg_file
        log_dest_path = mfg_log_dir + os.path.basename(log_pkg_file)

        # self.mtp.cli_log_inf("Collecting {:s} log files".format(stage), level=0)
        self.cli_log_inf("[{:s}] Collecting log file {:s}".format(sn, log_dest_path), level=0)

        # package: tar czf <>.tar.gz log/<>/*
        cmd = MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format(log_orig_path, "log/", log_sub_dir)
        libmfg_utils.host_shell_cmd(self, cmd)

        # save: cp <>.tar.gz /mfg_log/<>
        self.create_log_dir(log_dest_path)
        libmfg_utils.host_shell_cmd(self, "cp {:s} {:s}".format(log_orig_path, log_dest_path))

        # cleanup
        os.system("sync")
        os.system("rm -rf {:s}".format(log_orig_path))
        os.system("sync")

        self.close_logfiles()

    def create_log_dir(self, log_path):
        """
            mkdir -p -m 777 /mfg_log/uut/stage/sn/
            if dont have ownership, put in different directory
        """
        mfg_log_dir = os.path.dirname(log_path)
        if GLB_CFG_MFG_TEST_MODE:
            cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir)
            os.system(cmd)
        else:
            err_code = os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(mfg_log_dir))
            if not err_code:
                # try to change permission of the stage if this is first time created
                # this will fail if someone else created them...ask them to chmod 777
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))
            else:
                # chdir from mfg_log/type/stage/sn --> mfg_log/MERGE/type/stage/sn
                mfg_log_dir = mfg_log_dir.replace(nic_type, "MERGE/"+nic_type)
                os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(mfg_log_dir))
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))

    def inspect_logfile(self, logfile):
        return True

    def print_script_version(self):
        script_ver_match = re.search("image_amd64_.....?_(.*)\.tar", self.image["amd64_img"])
        if script_ver_match:
            script_ver = script_ver_match.group(1)
        else:
            script_ver = ""
        self.cli_log_report_inf("MFG Script Version: {:s}".format(script_ver))

    def get_mtp_factory_location(self):
        if self._factory_location == Factory.UNKNOWN:
            self.set_mtp_factory_location()

        return self._factory_location

    def set_mtp_factory_location(self, set_to=""):
        if set_to == "":
            self._factory_location = self._detect_factory_location()
        return self._factory_location

    def _detect_factory_location(self):
        if not self.mtp._ts_cfg:
            self.cli_log_err("Unable to retrieve chassis Terminal Server IP for factory detection")
            return Factory.UNKNOWN

        ipaddr = self.mtp._ts_cfg[0]

        # check which network subnet mask this IP address falls into
        for factory in Factory_network_config.keys():
            if "Networks" not in Factory_network_config[factory].keys():
                self.cli_log_err("Bad network config for factory {:s}".format(factory))
                return Factory.UNKNOWN
            for subnet in Factory_network_config[factory]["Networks"]:
                if ipaddress.ip_address(str(ipaddr)) in ipaddress.ip_network(str(subnet)):
                    return factory

        self.cli_log_err("Chassis IP does not belong in any valid network range")
        return Factory.UNKNOWN

    def mtp_ac_pwr_off(self, no_wait = False):
        self.cli_log_inf("Power off UUT", level=0)
        self.pdu.mtp_pdu_pwr_off()
        if not no_wait:
            libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
        return True

    def mtp_ac_pwr_on(self, no_wait = False):
        self.cli_log_inf("Power on UUT", level=0)
        self.pdu.mtp_pdu_pwr_on()
        if not no_wait:
            libmfg_utils.count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)
        return True

    @libtest_utils.parallel_threaded_test_section
    def mtp_nic_para_session_init(self, slot):
        userid = self.mtp._mgmt_cfg[1]
        if self.uut_type == UUT_Type.TOR:
            mtp_prompt = "#"
        else:
            mtp_prompt = "$"
        handle = self.mtp.mtp_session_create(slot)
        if handle:
            if not self.mtp.mtp_prompt_cfg(handle, userid, mtp_prompt, slot):
                self.cli_log_slot_err(slot, "Unable to config new ssh session for NIC")
                return False
            prompt = "{:s}@NIC-{:02d}:".format(userid, slot+1) + mtp_prompt
            self.nic[slot] = nic_ctrl(slot, self._diag_nic_filep_list[slot], test_inst=self)
            self.nic[slot].nic_handle_init(handle, prompt)

            if not diag.diag_env_init(self, slot):
                self.cli_log_slot_err(slot, "Failed to init Diag SW Environment")
                return False
        else:
            self.cli_log_slot_err(slot, "Unable to create MTP session")
            return False
        return True

    def mtp_nic_para_session_end(self, slot_list=[]):
        self.cli_log_inf("Close NIC Connections", level=0)
        if slot_list == []:
            slot_list = range(self.mtp._slots)
        for slot in slot_list:
            self.nic[slot].nic_handle_close()
        return True
