import sys, os
import re
import libmfg_utils
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MTP_DIAG_Report
from libdefs import FF_Stage
from libdefs import MFG_DIAG_CMDS
from libdefs import NIC_Type
from libdefs import MTP_TYPE
from libdefs import Voltage_Margin
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import RUNNING_EDVT
from libmfg_cfg import MTP_HEALTH_MONITOR


QA_LOG_DIR          = "/vol/hw/diag/diag_qa/regression_log/"
MFG_STAGE_LOG_DIR   = "/mfg_log/{:s}/{:s}/{:s}/"
MFG_CSP_LOG_DIR     = "/mfg_log/CSP_REC/{:s}/"
MODEL_STAGE_LOG_DIR = "/tmp/mfg_log/{:s}/{:s}/{:s}/"
MODEL_CSP_LOG_DIR   = "/tmp/mfg_log/CSP_REC/{:s}/"
STAGE_LOG_FOLDER    = "{:s}_{:s}_{:s}"


def set_mtp_test_log_folder(mtp_mgmt_ctrl, log_path):
    mtp_mgmt_ctrl._test_log_folder = log_path + "/"

def get_mtp_test_log_folder(mtp_mgmt_ctrl):
    return mtp_mgmt_ctrl._test_log_folder

def get_logfile_name(mtp_mgmt_ctrl):
    return os.path.basename(os.path.normpath(get_mtp_test_log_folder(mtp_mgmt_ctrl)))

def get_logfile_parent(mtp_mgmt_ctrl):
    return os.path.dirname(os.path.normpath(get_mtp_test_log_folder(mtp_mgmt_ctrl)))

def get_logfile_pkg_name(mtp_mgmt_ctrl):
    return get_logfile_name(mtp_mgmt_ctrl) + ".tar.gz"


###
#   START OF TEST ROUTINES
###


def find_logfile_path(mtp_mgmt_ctrl, stage):
    if stage == FF_Stage.FF_P2C:
        stage = "NT"
    log_parent_dir = os.path.join(os.getcwd(), "log/")
    mtp_id = mtp_mgmt_ctrl._id
    stage = str(stage)
    search_rgx = r"%s_MTPS?-[0-9A-Za-z\-]{3,}_[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}" % stage
    for item in sorted(os.listdir(log_parent_dir))[::-1]:
        if "tar.gz" in item:
            continue
        if re.search(search_rgx, item):
            return os.path.join(log_parent_dir, item)
    mtp_mgmt_ctrl.cli_log_err("Could not find logfile directory after deploying", level=0)
    return None

def create_logfile_path(mtp_mgmt_ctrl, stage, log_parent_dir="log/"):
    if stage == FF_Stage.FF_P2C:
        stage = "NT"
    cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(log_parent_dir)
    err = os.system(cmd) # make sure it exists
    if err:
        mtp_mgmt_ctrl.cli_log_err("Unable to create directory {:s} for the log".format(log_parent_dir), level=0)
        return None
    log_timestamp = libmfg_utils.get_timestamp()
    mtp_id = mtp_mgmt_ctrl._id
    log_dir = STAGE_LOG_FOLDER.format(stage, mtp_id, log_timestamp)
    os.system(MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(log_parent_dir + log_dir))
    logfile_path = os.path.join(log_parent_dir, log_dir)
    return logfile_path

def replace_logfile_path(mtp_mgmt_ctrl, mtp_script_dir):
    """ at end of test, get the new ONBOARD logfile path """
    tlvl_logfile_path = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    log_dir = os.path.split(os.path.normpath(tlvl_logfile_path))[1] # extract "log//DL_MTP-XXXX/" --> "DL_MTP-XXXX"
    set_mtp_test_log_folder(mtp_mgmt_ctrl, os.path.join(mtp_script_dir, "log", log_dir))

def open_logfiles(mtp_mgmt_ctrl, run_from_mtp, stage):
    if run_from_mtp:
        logfile_path = find_logfile_path(mtp_mgmt_ctrl, stage)
        MODIFIER = "a+"
    else:
        logfile_path = create_logfile_path(mtp_mgmt_ctrl, stage)
        MODIFIER = "w+"

    open_file_track_list = list()

    mtp_test_log_file = logfile_path + "/mtp_test.log"
    mtp_diag_log_file = logfile_path + "/mtp_diag.log"
    mtp_health_test_log_file = logfile_path + "/mtp_health_test.log"
    mtp_health_diag_log_file = logfile_path + "/mtp_health_diag.log"
    mtp_health_diag_cmd_file = logfile_path + "/mtp_health_diag_cmd.log"
    mtp_diag_cmd_log_file = logfile_path + "/mtp_diag_cmd.log"
    mtp_diagmgr_log_file = logfile_path + "/mtp_diagmgr.log"

    # so we dont break compatability with parser, mfg tracker, and other things
    if stage == FF_Stage.FF_FST:
        mtp_test_log_file = logfile_path + "/test_fst.log"
        mtp_diag_log_file = logfile_path + "/diag_fst.log"

    mtp_test_log_filep = open(mtp_test_log_file, MODIFIER)
    open_file_track_list.append(mtp_test_log_filep)
    mtp_diag_log_filep = open(mtp_diag_log_file, MODIFIER)
    open_file_track_list.append(mtp_diag_log_filep)
    mtp_diag_cmd_log_filep = open(mtp_diag_cmd_log_file, MODIFIER)
    open_file_track_list.append(mtp_diag_cmd_log_filep)
    if MTP_HEALTH_MONITOR:
        mtp_health_test_log_filep = open(mtp_health_test_log_file, MODIFIER)
        open_file_track_list.append(mtp_health_test_log_filep)
        mtp_health_diag_log_filep = open(mtp_health_diag_log_file, MODIFIER)
        open_file_track_list.append(mtp_health_diag_log_filep)
        mtp_health_diag_cmd_filep = open(mtp_health_diag_cmd_file, MODIFIER)
        open_file_track_list.append(mtp_health_diag_cmd_filep)

    diag_nic_log_filep_list = list()
    for slot in range(mtp_mgmt_ctrl._slots):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = logfile_path + "/mtp_{:s}_diag.log".format(key)
        if stage == FF_Stage.FF_FST:
            diag_nic_log_file = logfile_path + "/diag_{:s}_fst.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, MODIFIER)
        open_file_track_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    set_mtp_test_log_folder(mtp_mgmt_ctrl, logfile_path)
    mtp_mgmt_ctrl._filep = mtp_test_log_filep
    mtp_mgmt_ctrl._open_file_handles = open_file_track_list
    mtp_mgmt_ctrl._diag_filep = mtp_diag_log_filep
    mtp_mgmt_ctrl._diag_cmd_filep = mtp_diag_cmd_log_filep
    mtp_mgmt_ctrl._diag_nic_filep_list = diag_nic_log_filep_list[:]
    mtp_mgmt_ctrl._diagmgr_logfile = mtp_diagmgr_log_file
    if MTP_HEALTH_MONITOR:
        mtp_mgmt_ctrl._mtp_health._filep = mtp_health_test_log_filep
        mtp_mgmt_ctrl._mtp_health._diag_filep = mtp_health_diag_log_filep
        mtp_mgmt_ctrl._mtp_health._diag_cmd_filep = mtp_health_diag_cmd_filep

    return logfile_path, open_file_track_list


def mtp_init_test_script(mtp_mgmt_ctrl, mtp_script_dir, mtp_script_pkg, extra_script=None, extra_config=None):
    mtp_script_dir = os.path.basename(os.path.normpath(mtp_script_dir))
    shared_script_dir = mtp_script_dir
    mtp_script_dir = mtp_script_dir + ".{:s}/".format(mtp_mgmt_ctrl._id)
    # remove previous copy to this MTP
    cmd = "rm -rf {:s}".format(mtp_script_dir)
    os.system(cmd)
    # make new staging folder for copy
    cmd = "cp -r {:s} {:s}".format(shared_script_dir, mtp_script_dir)
    os.system(cmd)
    os.system("sync")
    if extra_script:
        cmd = "cp {:s} {:s}".format(extra_script, mtp_script_dir)
        os.system(cmd)
    if extra_config:
        cmd = "cp {:s} config/".format(os.path.relpath(extra_config))
        os.system(cmd)
    cmd = "cp -r lib/ config/ {:s}".format(mtp_script_dir)
    os.system(cmd)
    logfile_dir = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    cmd = "mkdir {:s}/log/".format(mtp_script_dir)
    os.system(cmd)
    cmd = "mv {:s}/ {:s}/log/".format(logfile_dir, mtp_script_dir)
    os.system(cmd)
    cmd = "tar czf {:s} {:s}".format(mtp_script_pkg, mtp_script_dir)
    os.system(cmd)
    # remove the lib config for the next run
    if extra_script:
        cmd = "rm -f {:s}/{:s}".format(mtp_script_dir, os.path.basename(extra_script))
        os.system(cmd)
    os.system("sync")

    # download the test script pkg
    ipaddr, userid, passwd = mtp_mgmt_ctrl.get_mgmt_cfg()
    if not libmfg_utils.network_copy_file(ipaddr, userid, passwd, mtp_script_pkg, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH):
        mtp_mgmt_ctrl.cli_log_err("Copy Test script failed... Abort")
        return False
    # remove the stale test script
    cmd = "rm -rf {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"/"+shared_script_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False
    # unpack the test script pkg
    cmd = "tar zxf {:s} -C {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"/"+mtp_script_pkg, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False
    # move test script folder to common folder
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"/"+mtp_script_dir, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"/"+shared_script_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False
    # remove the test script pkg
    cmd = "rm -f {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"/"+mtp_script_pkg)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False

    # remove the MTP-specific test script folder
    cmd = "rm -rf {:s}".format(mtp_script_dir)
    os.system(cmd)
    # remove created tar file
    cmd = "rm -rf {:s}".format(mtp_script_pkg)
    os.system(cmd)
    # remove logfile dir and log file
    cmd = "rm -rf {:s}".format(logfile_dir)
    os.system(cmd)

    return True


###
#   END OF TEST ROUTINES
###


def save_logs(mtp_mgmt_ctrl, stage, mtp_test_summary, mtp_start_ts, mtp_stop_ts, mirror_logdir, logs_local, send_report):
    if not analyze_and_update(mtp_mgmt_ctrl, mtp_test_summary, stage, mtp_start_ts, mtp_stop_ts, logs_local, send_report):
        mtp_mgmt_ctrl.cli_log_err("Failed to read and update NIC test result", level=0)
        return False
    if not upload_testlogs(mtp_mgmt_ctrl, stage, mirror_logdir, logs_local):
        mtp_mgmt_ctrl.cli_log_err("Failed to read and update NIC test result", level=0)
        return False
    return True


def analyze_and_update(mtp_mgmt_ctrl, mtp_test_summary, stage, mtp_start_ts, mtp_stop_ts, logs_local=False, send_report=False):
    test_log_file = parse_test_summary(mtp_mgmt_ctrl, stage, logs_local)
    if not test_log_file:
        mtp_mgmt_ctrl.cli_log_err("Couldnt open mtp_test.log for analysis", level=0)
        return False
    pass_match, fail_match, skip_match = match_nics(test_log_file)
    update_test_summary(pass_match, fail_match, skip_match, mtp_test_summary, stage)
    assign_nic_retest_flag(test_log_file, mtp_test_summary, stage)

    if GLB_CFG_MFG_TEST_MODE and send_report:
        mtp_id = mtp_mgmt_ctrl._id
        mtp_sn = mtp_mgmt_ctrl._mtp_sn
        libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, stage, mtp_test_summary)

        if stage == FF_Stage.FF_SRN:
            sn_type = ""
            duration = mtp_stop_ts - mtp_start_ts

            # dump the summary
            for slot, sn, nic_type, rc, *_ in mtp_test_summary:
                nic_cli_id_str = libmfg_utils.id_str(mtp=mtp_id, nic=int(slot), base=0)
                if rc:
                    mtp_mgmt_ctrl.cli_log_inf("[{:s}] {:s} PASS".format(mtp_id, mtp_sn))
                else:
                    mtp_mgmt_ctrl.cli_log_inf("[{:s}] {:s} FAIL".format(mtp_id, mtp_sn))

            # ret = libmfg_utils.flx_web_srv_post_uut_report(FF_Stage.FF_SRN, sn_type, mtp_sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, "MTP_SCREEN", "FAIL", err_dsc_list, err_code_list)
            # if not ret:
            #     mtp_mgmt_ctrl.cli_log_inf(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
            # else:
            #     mtp_mgmt_ctrl.cli_log_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))

    return True

def parse_test_summary(mtp_mgmt_ctrl, stage, logs_local=False):
    """
        Read in mtp_test.log. Download it if run from outside MTP.
    """
    mtp_id = mtp_mgmt_ctrl._id
    tlf = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    test_log_file = "{:s}/mtp_test.log".format(tlf)
    if stage == FF_Stage.FF_FST:
        test_log_file = "{:s}/test_fst.log".format(tlf)
    local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
    
    if logs_local:
        os.system("cp {:s} {:s}".format(test_log_file, local_test_log_file))
    else:
        ipaddr, userid, passwd = mtp_mgmt_ctrl.get_mgmt_cfg()
        if not libmfg_utils.network_get_file(ipaddr, userid, passwd, local_test_log_file, test_log_file):
            mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test summary file {:}".format(test_log_file), level=0)
            return None

    # analyze test summary logfile
    try:
        with open(local_test_log_file, 'r') as fp:
            buf = fp.read()
        cmd = "rm -rf {:s}".format(local_test_log_file)
        os.system(cmd)
        return buf
    except Exception as e:
        print(e)
        mtp_mgmt_ctrl.cli_log_err("Unable to open MTP test summary file {:}".format(local_test_log_file), level=0)
        return None

def match_nics(test_log_file):
    # search for MTP_DIAG_REGRESSION_{PASS/FAIL/SKIP} for each NIC
    nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
    nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
    nic_skip_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_SKIP_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_SKIP)
    fail_match = re.findall(nic_fail_reg_exp, test_log_file)
    pass_match = re.findall(nic_pass_reg_exp, test_log_file)
    skip_match = re.findall(nic_skip_reg_exp, test_log_file)

    if len(fail_match + pass_match) == 0:
        # no cards tested, save log to UNKNOWN folder
        fail_match = [(0, NIC_Type.UNKNOWN, NIC_Type.UNKNOWN)]

    return pass_match, fail_match, skip_match

def update_test_summary(pass_match, fail_match, skip_match, mtp_test_summary, stage):
    """
        Update NIC test result dictionary based on parsing mtp_test.log
    """

    retest_block_default = False

    if stage != FF_Stage.FF_SRN:
        for slot in skip_match:
            mtp_test_summary.append([slot, "SKIPPED", "SLOT", True, retest_block_default])

        for slot, nic_type, sn in fail_match:
            mtp_test_summary.append([slot, sn, nic_type, False, retest_block_default])

        for slot, nic_type, sn in pass_match:
            mtp_test_summary.append([slot, sn, nic_type, True, retest_block_default])

    else:
        ret = True
        first_rcd = True
        for slot, nic_type, sn in fail_match:
            if first_rcd:
                mtp_test_summary.append([slot, sn, nic_type, False, retest_block_default])
                first_rcd = False
                ret = False
        if ret:
            for slot, nic_type, sn in pass_match:
                if first_rcd:
                    mtp_test_summary.append([slot, sn, nic_type, True, retest_block_default])

def is_retest_blocked(test, stage):
    if test in [
                "NIC_POWER",
                "SNAKE_ELBA",
                "L1",
                "EMMC",
                "DDR_STRESS",
                "I2C",
                "RTC",
                "EDMA"
                ]:
        return True
    elif test in ["ETH_PRBS"] and stage in (FF_Stage.FF_4C_L, FF_Stage.FF_4C_H, FF_Stage.FF_2C_H, FF_Stage.FF_2C_L):
        return True 
    else:
        return False

def assign_nic_retest_flag(test_log_file, mtp_test_summary, stage):
    """
        1. Open mtp_test.log to search for "<SN> NIC_DIAG_REGRESSION_TEST_FAIL" (usually at the end)
        2. For those SN's failing, search for which test they failed "<SN> DIAG TEST <DSP> <TEST> <RESULT> "
    """
    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL in test_log_file:
        nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
        fail_match = re.findall(nic_fail_reg_exp, test_log_file)
        for slot, sn_type, sn in fail_match:
            test_list = list()
            # find all test status
            nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
            sub_match = re.findall(nic_test_rslt_reg_exp, test_log_file)
            for dsp, test, result in sub_match:
                # EXCLUDE PASSING TESTS
                if result == "PASS":
                    continue
                test_list.append(test)

            if libmfg_utils.FindDellSN(sn):
                nic_pn_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_PN_BY_FRU_RE.format(sn)
                matchsn = re.findall(nic_pn_reg_exp, test_log_file)
                if matchsn:
                    sn = sn[:2] + matchsn[0][:6] + sn[2:] + matchsn[0][6:]
                else:
                    nic_pn_reg_exp2 = MTP_DIAG_Report.NIC_DIAG_REGRESSION_PN_BY_FRU2_RE.format(sn)
                    matchsn2 = re.findall(nic_pn_reg_exp2, test_log_file)
                    if matchsn2:
                        sn = sn[:2] + matchsn2[0][:6] + sn[2:] + matchsn2[0][6:]

            block_retest = False
            for test in test_list:
                block_retest |= is_retest_blocked(test, stage)

            # replace the 5th field in matrix
            if block_retest:
                for idx in range(len(mtp_test_summary)):
                    # locate this SN's record
                    if mtp_test_summary[idx][1] == sn:
                        # block it
                        mtp_test_summary[idx][4] = True


def upload_testlogs(mtp_mgmt_ctrl, stage, mirror_logdir, logs_local=False):
    mtp_mgmt_ctrl.cli_log_inf("Collecting {:s} log files started".format(stage), level=0)

    if not gather_final_logs(mtp_mgmt_ctrl, stage, logs_local):
        mtp_mgmt_ctrl.cli_log_err("Failed to collect NIC logfiles", level=0)
        pass

    if mtp_mgmt_ctrl._mgmt_handle: # if test failed before MTP connected, cant save to logfile
        mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)

    if not create_log_tarball(mtp_mgmt_ctrl, logs_local):
        mtp_mgmt_ctrl.cli_log_err("Failed to package logfile on MTP", level=0)
        return False

    test_log_file = parse_test_summary(mtp_mgmt_ctrl, stage, logs_local)
    if not test_log_file:
        # NZ TODO
        return False
    pass_match, fail_match, skip_match = match_nics(test_log_file)

    if not upload_log_tarball(mtp_mgmt_ctrl, stage, pass_match, fail_match, mirror_logdir, logs_local):
        mtp_mgmt_ctrl.cli_log_err("Failed to save logfiles", level=0)
        return False

    mtp_mgmt_ctrl.cli_log_inf("Collecting {:s} log files complete".format(stage), level=0)

    return True

def gather_dsp_logs(mtp_mgmt_ctrl, vmarg):
    tlf = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    if vmarg == Voltage_Margin.low:
        diag_sub_dir = "/lv_diag_logs/"
        nic_sub_dir = "/lv_nic_logs/"
        asic_sub_dir = "/lv_asic_logs/"
    elif vmarg == Voltage_Margin.high:
        diag_sub_dir = "/hv_diag_logs/"
        nic_sub_dir = "/hv_nic_logs/"
        asic_sub_dir = "/hv_asic_logs/"
    else:
        diag_sub_dir = "/diag_logs/"
        nic_sub_dir = "/nic_logs/"
        asic_sub_dir = "/asic_logs/"
    # create log dir
    ret = True
    cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(tlf + diag_sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        ret = False
    cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(tlf + nic_sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        ret = False
    cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(tlf + asic_sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        ret = False
    # save the asic/diag log files
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_DIAG_LOG_FILES, tlf + diag_sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        ret = False
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, tlf + asic_sub_dir)
    if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.MATERA:
        cmd = MTP_DIAG_Logfile.MATERA_ONBOARD_ASIC_LOG_FILES.format(tlf + asic_sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        ret = False
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_DUMP_FILES, tlf + asic_sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        ret = False
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_NIC_LOG_FILES, tlf + nic_sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        ret = False

    return ret

def gather_asic_logs(mtp_mgmt_ctrl, logs_local):
    ret = True
    tlf = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    asic_sub_dir = tlf +  "asic_logs/"

    if not logs_local:
        cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(asic_sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            ret = False

        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, asic_sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            ret = False

        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_DUMP_FILES, asic_sub_dir)    
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            ret = False
    else:
        # scan_dl
        cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(asic_sub_dir)
        err_code = os.system(cmd)
        if err_code:
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on host".format(cmd), level=0)
            ret = False
        ipaddr, userid, passwd = mtp_mgmt_ctrl._mgmt_cfg
        libmfg_utils.network_get_file(ipaddr, userid, passwd, asic_sub_dir, MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES)
        libmfg_utils.network_get_file(ipaddr, userid, passwd, asic_sub_dir, MTP_DIAG_Logfile.ONBOARD_ASIC_DUMP_FILES)

    return ret

def gather_csp_n_bin_logs(mtp_mgmt_ctrl):
    ret = True
    tlf = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    asic_sub_dir = tlf +  "asic_logs/"
    cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(asic_sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        ret = False
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_CSP_LOG_FILES, asic_sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        ret = False
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_BIN_LOG_FILES, asic_sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        ret = False
    return ret

def gather_final_logs(mtp_mgmt_ctrl, stage, logs_local):
    """
        Gather all logs from asic & dsp directories into one place onboard MTP
    """
    ret = True

    if not mtp_mgmt_ctrl._mgmt_handle:
        # test didnt connect to MTP yet, skip gathering final logs
        return True

    if stage in (FF_Stage.FF_DL, FF_Stage.FF_SWI):
        # copy AVS log and ECC dump
        if not gather_asic_logs(mtp_mgmt_ctrl, logs_local):
            ret = False

    if stage == FF_Stage.FF_SWI:
        if not gather_csp_n_bin_logs(mtp_mgmt_ctrl):
            ret = False

    return ret

def create_log_tarball(mtp_mgmt_ctrl, logs_local=False):
    logfile_path = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    logfile_name = get_logfile_name(mtp_mgmt_ctrl)
    logfile_parent = get_logfile_parent(mtp_mgmt_ctrl)
    log_pkg_file = get_logfile_pkg_name(mtp_mgmt_ctrl)

    cmd = "cd {:s}; tar czf {:s} {:s}".format(logfile_parent, log_pkg_file, logfile_name)
    if logs_local:
        err_code = os.system(cmd)
        if err_code:
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on host".format(cmd), level=0)
            return False
    else:
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return False

    return True

def upload_log_tarball(mtp_mgmt_ctrl, stage, pass_match, fail_match, mirror_logdir, logs_local=False):
    csp_log_dir = None
    ret = True

    for slot, nic_type, sn in fail_match + pass_match:
        # report doesn't have valid serial number
        if sn == "None":
            sn = NIC_Type.UNKNOWN

        if not upload_nic_logfile(mtp_mgmt_ctrl, stage, nic_type, sn, mirror_logdir, logs_local):
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Failed to upload logfiles")
            ret = False
            continue
        
        if stage == FF_Stage.FF_SWI and not logs_local:
            # only search csp* if SWI actually ran. `logs_local` would be True if test failed before SWI script deployed.
            if not upload_csp_logfile(mtp_mgmt_ctrl, nic_type, sn):
                mtp_mgmt_ctrl.cli_log_err("Failed to upload CSP logfiles", level=0)
                ret = False

    return ret

def upload_nic_logfile(mtp_mgmt_ctrl, stage, nic_type, sn, mirror_logdir, logs_local=False):
    if stage in (FF_Stage.FF_4C_L, FF_Stage.FF_4C_H):
        stage_str = "4C/"+str(stage)
    elif stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H):
        stage_str = "2C/"+str(stage)
    else:
        stage_str = str(stage)

    if GLB_CFG_MFG_TEST_MODE:
        mfg_log_dir = MFG_STAGE_LOG_DIR.format(nic_type, stage_str, sn)
    elif mirror_logdir:
        mfg_log_dir = mirror_logdir
    else:
        mfg_log_dir = MODEL_STAGE_LOG_DIR.format(nic_type, stage_str, sn)

    logfile_parent = get_logfile_parent(mtp_mgmt_ctrl)
    log_pkg_file = get_logfile_pkg_name(mtp_mgmt_ctrl)
    log_upload_path = os.path.join(mfg_log_dir, log_pkg_file)
    # save all final gz log filename in a file for EDVT
    if RUNNING_EDVT:
        try:
            with open("EDVT_LOG_FILENAME.log", 'a+') as edvt_log_filename:
                cli_id_str = libmfg_utils.id_str(mtp = mtp_mgmt_ctrl._id)
                edvt_log_filename.write("{:s} {:s} {:s}\n".format(cli_id_str, sn, log_upload_path))
        except Exception as Err:
            mtp_mgmt_ctrl.cli_log_inf("Somthing Wrong when save final edvt log, ignore")
            print(Err)
    mtp_mgmt_ctrl.cli_log_inf("[{:s}] Collecting log file {:s}".format(sn, log_upload_path))

    if GLB_CFG_MFG_TEST_MODE:
        cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(mfg_log_dir)
        os.system(cmd)
    else:
        err_code = os.system(MFG_DIAG_CMDS().MFG_MK_DIR_777_FMT.format(mfg_log_dir))
        if not err_code:
            # try to change permission of the stage if this is first time created
            # this will fail if someone else created them...ask them to chmod 777
            os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))
            if stage in (FF_Stage.FF_4C_H, FF_Stage.FF_4C_L, FF_Stage.FF_2C_H, FF_Stage.FF_2C_L):
                # since 4C directory is organized as /mfg_log/type/4C/4C-H/...
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/../.."))
        else:
            # chdir from mfg_log/type/stage/sn --> mfg_log/MERGE/type/stage/sn
            mfg_log_dir = mfg_log_dir.replace(nic_type, "MERGE/"+nic_type)
            os.system(MFG_DIAG_CMDS().MFG_MK_DIR_777_FMT.format(mfg_log_dir))
            os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))
            if stage in (FF_Stage.FF_4C_H, FF_Stage.FF_4C_L, FF_Stage.FF_2C_H, FF_Stage.FF_2C_L):
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/../.."))

    if logs_local:
        cmd = "cp {:s} {:s}".format(os.path.join(logfile_parent, log_pkg_file), log_upload_path)
        err_code = os.system(cmd)
        if err_code:
            mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file to {:}".format(log_upload_path), level=0)
            return False
    else:
        ipaddr, userid, passwd = mtp_mgmt_ctrl.get_mgmt_cfg()
        if not libmfg_utils.network_get_file(ipaddr, userid, passwd, log_upload_path, os.path.join(logfile_parent, log_pkg_file)):
            mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file to {:}".format(log_upload_path), level=0)
            return False

    return True

def upload_csp_logfile(mtp_mgmt_ctrl, nic_type, sn):
    if GLB_CFG_MFG_TEST_MODE:
        mfg_log_dir = MFG_CSP_LOG_DIR.format(nic_type)
    else:
        mfg_log_dir = MODEL_CSP_LOG_DIR.format(nic_type)

    tlf = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    cmd = "ls --color=never {:s}/asic_logs/csp*{:s}*".format(tlf, sn)
 
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    listoffileoutput = mtp_mgmt_ctrl.mtp_get_cmd_buf()
    listoffile = listoffileoutput.split()
    
    listcspfiletoupload = list()
    for cspfile in listoffile:
        if 'txt' in cspfile:
            listcspfiletoupload.append(cspfile)
    for cspfilepath in listcspfiletoupload:
        if GLB_CFG_MFG_TEST_MODE:
            cmd = MFG_DIAG_CMDS().MFG_MK_DIR_FMT.format(mfg_log_dir)
            os.system(cmd)
        else:
            err_code = os.system(MFG_DIAG_CMDS().MFG_MK_DIR_777_FMT.format(mfg_log_dir))
            if not err_code:
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))
            else:
                mfg_log_dir = mfg_log_dir.replace("CSP_REC", "MERGE/CSP_REC")
                os.system(MFG_DIAG_CMDS().MFG_MK_DIR_777_FMT.format(mfg_log_dir))
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))
        log_upload_path = mfg_log_dir + os.path.basename(cspfilepath)

        ipaddr, userid, passwd = mtp_mgmt_ctrl.get_mgmt_cfg()
        if not libmfg_utils.network_get_file(ipaddr, userid, passwd, log_upload_path, cspfilepath):
            mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file {:}".format(cspfilepath), level=0)
            continue
        mtp_mgmt_ctrl.cli_log_inf("Collecting csp log file {:s}".format(log_upload_path))

    return True