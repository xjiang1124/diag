import sys, os
import re
import libmfg_utils
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Path
from libdefs import MTP_DIAG_Report
from libdefs import FF_Stage
from libdefs import MFG_DIAG_CMDS
from libdefs import NIC_Type
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE


QA_LOG_DIR          = "/vol/hw/diag/diag_qa/regression_log/"
MFG_STAGE_LOG_DIR   = "/mfg_log/{:s}/{:s}/{:s}/"
MFG_CSP_LOG_DIR     = "/mfg_log/CSP_REC/{:s}/"
MODEL_STAGE_LOG_DIR = "/tmp/mfg_log/{:s}/{:s}/{:s}/"
MODEL_CSP_LOG_DIR   = "/tmp/mfg_log/CSP_REC/{:s}/"
STAGE_LOG_FOLDER    = "{:s}_{:s}_{:s}"


def set_mtp_test_log_folder(mtp_mgmt_ctrl, log_path):
    mtp_mgmt_ctrl._test_log_folder = log_path

def get_mtp_test_log_folder(mtp_mgmt_ctrl):
    return mtp_mgmt_ctrl._test_log_folder

def find_logfile_path(mtp_mgmt_ctrl, stage):
    if stage == FF_Stage.FF_P2C:
        stage = "NT"
    log_parent_dir = os.getcwd()
    mtp_id = mtp_mgmt_ctrl._id
    stage = str(stage)
    search_rgx = r"%s_MTPS?-[0-9A-Za-z\-]{3,}_[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}" % stage
    for item in os.listdir(log_parent_dir):
        if re.search(search_rgx, item):
            return os.path.join(log_parent_dir, item)
    mtp_mgmt_ctrl.cli_log_err("Could not find logfile directory after deploying", level=0)
    return None

def create_logfile_path(mtp_mgmt_ctrl, stage, log_parent_dir="log/"):
    if stage == FF_Stage.FF_P2C:
        stage = "NT"
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_parent_dir)
    err = os.system(cmd) # make sure it exists
    if err:
        mtp_mgmt_ctrl.cli_log_err("Unable to create directory {:s} for the log".format(log_parent_dir), level=0)
        return None
    log_timestamp = libmfg_utils.get_timestamp()
    mtp_id = mtp_mgmt_ctrl._id
    log_dir = STAGE_LOG_FOLDER.format(stage, mtp_id, log_timestamp)
    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_parent_dir + log_dir))
    logfile_path = os.path.join(log_parent_dir, log_dir)
    return logfile_path

def replace_logfile_path(mtp_mgmt_ctrl, mtp_script_dir):
    """ at end of test, get the new ONBOARD logfile path """
    tlvl_logfile_path = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    log_dir = os.path.split(os.path.normpath(tlvl_logfile_path))[1] # extract "log//DL_MTP-XXXX/" --> "DL_MTP-XXXX"
    set_mtp_test_log_folder(mtp_mgmt_ctrl, os.path.join(mtp_script_dir, log_dir))

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
    mtp_diag_cmd_log_file = logfile_path + "/mtp_diag_cmd.log"
    mtp_diagmgr_log_file = logfile_path + "/mtp_diagmgr.log"

    # so we dont break compatability with parser, mfg tracker, and other things
    if stage == FF_Stage.FF_FST:
        mtp_test_log_file = logfile_path + "/test_fst.log"
        mtp_diag_log_file = logfile_path + "/diag_fst.log"

    mtp_test_log_filep = open(mtp_test_log_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_test_log_filep)
    mtp_diag_log_filep = open(mtp_diag_log_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_diag_log_filep)
    mtp_diag_cmd_log_filep = open(mtp_diag_cmd_log_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_diag_cmd_log_filep)

    diag_nic_log_filep_list = list()
    for slot in range(mtp_mgmt_ctrl._slots):
        key = libmfg_utils.nic_key(slot)
        diag_nic_log_file = logfile_path + "/mtp_{:s}_diag.log".format(key)
        if stage == FF_Stage.FF_FST:
            diag_nic_log_file = logfile_path + "/diag_{:s}_fst.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, MODIFIER, buffering=0)
        open_file_track_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    set_mtp_test_log_folder(mtp_mgmt_ctrl, logfile_path)
    mtp_mgmt_ctrl._filep = mtp_test_log_filep
    mtp_mgmt_ctrl._open_file_handles = open_file_track_list
    mtp_mgmt_ctrl._diag_filep = mtp_diag_log_filep
    mtp_mgmt_ctrl._diag_cmd_filep = mtp_diag_cmd_log_filep
    mtp_mgmt_ctrl._diag_nic_filep_list = diag_nic_log_filep_list[:]
    mtp_mgmt_ctrl._diagmgr_logfile = mtp_diagmgr_log_file

    return logfile_path, open_file_track_list


def mtp_init_test_script(mtp_mgmt_ctrl, mtp_script_dir, mtp_script_pkg, extra_script=None, extra_config=None):
    shared_script_dir = os.path.dirname(mtp_script_dir)
    mtp_script_dir = os.path.dirname(mtp_script_dir) + ".{:s}/".format(mtp_mgmt_ctrl._id)
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
    cmd = "cp -r {:s}/ {:s}".format(logfile_dir, mtp_script_dir)
    os.system(cmd)
    cmd = "tar czf {:s} {:s}".format(mtp_script_pkg, mtp_script_dir)
    os.system(cmd)
    # remove the lib config for the next run
    if extra_script:
        cmd = "rm -f {:s}/{:s}".format(mtp_script_dir, os.path.basename(extra_script))
        os.system(cmd)
    os.system("sync")

    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
    # download the test script pkg
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
    os.system(cmd)
    # remove the MTP-specific test script folder
    cmd = "rm -rf {:s}".format(mtp_script_dir)
    os.system(cmd)
    return True

def save_nic_logfiles(mtp_mgmt_ctrl, sn, stage, nic_type, mirror_logdir=None):
    if stage == FF_Stage.FF_P2C:
        stage = "NT"

    if GLB_CFG_MFG_TEST_MODE:
        mfg_log_dir = MFG_STAGE_LOG_DIR.format(nic_type, stage, sn)
    elif mirror_logdir:
        mfg_log_dir = mirror_logdir
    else:
        mfg_log_dir = MODEL_STAGE_LOG_DIR.format(nic_type, stage, sn)

    logfile_path = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    logfile_name = os.path.basename(os.path.normpath(logfile_path))
    logfile_parent = os.path.dirname(os.path.normpath(logfile_path))
    log_pkg_file = logfile_name + ".tar.gz"
    log_upload_path = mfg_log_dir + log_pkg_file

    mtp_mgmt_ctrl.cli_log_inf("[{:s}] Collecting log file {:s}".format(sn, log_upload_path))

    # package: tar czf <>.tar.gz mtp_script/<>/
    cmd = "tar czf {:s} -C {:s} {:s}".format(log_pkg_file, logfile_parent, logfile_name)
    if not libmfg_utils.host_shell_cmd(mtp_mgmt_ctrl, cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return False

    # save: scp <>.tar.gz /mfg_log/<>
    create_log_dir(log_upload_path)

    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
    if not libmfg_utils.network_get_file(ipaddr, userid, passwd, log_upload_path, os.path.join(logfile_parent, log_pkg_file)):
        mtp_mgmt_ctrl.cli_log_err("Unable to copy log file to {:}".format(log_upload_path), level=0)
        return False

    return True

def get_mtp_logfile(mtp_mgmt_ctrl, log_dir, mtp_id, mtp_test_summary, stage, vmarg=[], mirror_logdir=None):
    if stage in (FF_Stage.FF_4C_L, FF_Stage.FF_4C_H):
        stage_str = "4C/"+str(stage)
    elif stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H):
        stage_str = "2C/"+str(stage)
    else:
        stage_str = str(stage)

    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]

    mtp_mgmt_ctrl.cli_log_inf("Collecting {:s} log files started".format(stage), level=0)

    logfile_path = get_mtp_test_log_folder(mtp_mgmt_ctrl)
    logfile_name = os.path.basename(os.path.normpath(logfile_path))
    logfile_parent = log_dir #os.path.dirname(os.path.normpath(logfile_path))
    log_pkg_file = logfile_name + ".tar.gz"
    test_log_file = "{:s}/mtp_test.log".format(logfile_path)
    local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
    if stage == FF_Stage.FF_FST:
        test_log_file = "{:s}/test_fst.log".format(logfile_path)
    if stage == FF_Stage.FF_DL:
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_DL_LOG_FILES
    elif stage == FF_Stage.FF_CFG:
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_CFG_LOG_FILES
    elif stage == FF_Stage.FF_P2C:
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES
    elif stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L:
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES
    elif stage == FF_Stage.FF_2C_H or stage == FF_Stage.FF_2C_L:
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES
    elif stage == FF_Stage.FF_SWI:
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_SWI_LOG_FILES
        # copy csp files from MTP to Server
        test_onboard_csp_log_files = MTP_DIAG_Logfile.ONBOARD_CSP_LOG_FILES
    elif stage == FF_Stage.FF_FST:
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_FST_LOG_FILES
    elif stage == FF_Stage.FF_SRN:
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_SRN_TEST_LOG_FILES
    elif stage == FF_Stage.FF_ORT:
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES
    elif stage == FF_Stage.FF_RDT:
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES
    else:
        mtp_mgmt_ctrl.cli_log_err("Unknown FF Stage: {:s}".format(stage), level=0)
        return None

    if stage == FF_Stage.FF_DL or stage == FF_Stage.FF_SWI:
        # save the avs and ecc dump log files
        asic_sub_dir = "/asic_logs/"
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(logfile_path + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, logfile_path + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_DUMP_FILES, logfile_path + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    if stage == FF_Stage.FF_SWI:
        asic_sub_dir = "/asic_logs/"
        cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_CSP_LOG_FILES, logfile_path + asic_sub_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    # move onboard log files
    cmd = "mv {:s} {:s}".format(test_onboard_log_files, logfile_path)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

    # for DL/P2C/4C test, extra logfiles are needed
    if stage == FF_Stage.FF_DL or stage == FF_Stage.FF_SWI:
        asic_log_dir = log_dir + "asic_logs/"
        cmd = "mv {:s} {:s}".format(asic_log_dir, logfile_path)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None

    elif stage == FF_Stage.FF_P2C or stage == FF_Stage.FF_SRN or stage == FF_Stage.FF_ORT or stage == FF_Stage.FF_RDT:
        if not vmarg:
            diag_log_dir = log_dir + "diag_logs/"
            asic_log_dir = log_dir + "asic_logs/"
            nic_log_dir = log_dir + "nic_logs/"
            # move the extra logfile
            cmd = "mv {:s} {:s}".format(diag_log_dir, logfile_path)
            if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
                mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
                return None
            cmd = "mv {:s} {:s}".format(asic_log_dir, logfile_path)
            if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
                mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
                return None
            cmd = "mv {:s} {:s}".format(nic_log_dir, logfile_path)
            if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
                mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
                return None
        else:
            for vmag in vmarg:
                if vmag.lower() == "high":
                    diag_log_dir = log_dir + "hv_diag_logs/"
                    asic_log_dir = log_dir + "hv_asic_logs/"
                    nic_log_dir = log_dir + "hv_nic_logs/"
                elif vmag.lower() == "low":
                    diag_log_dir = log_dir + "lv_diag_logs/"
                    asic_log_dir = log_dir + "lv_asic_logs/"
                    nic_log_dir = log_dir + "lv_nic_logs/"
                else:
                    diag_log_dir = log_dir + "diag_logs/"
                    asic_log_dir = log_dir + "asic_logs/"
                    nic_log_dir = log_dir + "nic_logs/"
                # move the extra logfile
                cmd = "mv {:s} {:s}".format(diag_log_dir, logfile_path)
                if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
                    mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
                    return None
                cmd = "mv {:s} {:s}".format(asic_log_dir, logfile_path)
                if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
                    mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
                    return None
                cmd = "mv {:s} {:s}".format(nic_log_dir, logfile_path)
                if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
                    mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
                    return None

    elif stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L or stage == FF_Stage.FF_2C_H or stage == FF_Stage.FF_2C_L:
        hv_diag_log_dir = log_dir + "hv_diag_logs/"
        hv_asic_log_dir = log_dir + "hv_asic_logs/"
        hv_nic_log_dir = log_dir + "hv_nic_logs/"
        lv_diag_log_dir = log_dir + "lv_diag_logs/"
        lv_asic_log_dir = log_dir + "lv_asic_logs/"
        lv_nic_log_dir = log_dir + "lv_nic_logs/"
        # move the extra logfile
        cmd = "mv {:s} {:s}".format(hv_diag_log_dir, logfile_path)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(hv_asic_log_dir, logfile_path)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(hv_nic_log_dir, logfile_path)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        # move the extra logfile
        cmd = "mv {:s} {:s}".format(lv_diag_log_dir, logfile_path)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(lv_asic_log_dir, logfile_path)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(lv_nic_log_dir, logfile_path)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        if vmarg and "normal" in vmarg:
            diag_log_dir = log_dir + "diag_logs/"
            asic_log_dir = log_dir + "asic_logs/"
            nic_log_dir = log_dir + "nic_logs/"
            # move the extra logfile
            cmd = "mv {:s} {:s}".format(diag_log_dir, logfile_path)
            if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
                mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
                return None
            cmd = "mv {:s} {:s}".format(asic_log_dir, logfile_path)
            if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
                mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
                return None
            cmd = "mv {:s} {:s}".format(nic_log_dir, logfile_path)
            if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
                mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
                return None
    # for SWI/FST, no extra logfiles
    else:
        pass

    logfile_list = list()
    # pkg the onboard logs
    cmd = "tar czf {:s} -C {:s} {:s}".format(log_pkg_file, log_dir, logfile_name)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

    if not libmfg_utils.network_get_file(ipaddr, userid, passwd, local_test_log_file, test_log_file):
        mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test summary file {:}".format(test_log_file), level=0)
        return None

    # analyze test summary logfile
    try:
        with open(local_test_log_file, 'r') as fp:
            buf = fp.read()
    except:
        mtp_mgmt_ctrl.cli_log_err("Unable to open MTP test summary file {:}".format(test_log_file), level=0)
        return None

    nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
    nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
    nic_skip_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_SKIP_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_SKIP)
    fail_match = re.findall(nic_fail_reg_exp, buf)
    pass_match = re.findall(nic_pass_reg_exp, buf)
    skip_match = re.findall(nic_skip_reg_exp, buf)

    log_hard_copy_flag = True
    log_relative_link = None
    temp_nic_type = None
    csp_log_dir = None

    if len(fail_match + pass_match) == 0:
        # no cards tested, save log to UNKNOWN folder
        fail_match = [(0, NIC_Type.UNKNOWN, NIC_Type.UNKNOWN)]

    for slot, nic_type, sn in fail_match + pass_match:
        # report doesn't have valid serial number
        if nic_type:
            temp_nic_type = nic_type
        if sn == "None":
            sn = NIC_Type.UNKNOWN
        if GLB_CFG_MFG_TEST_MODE:
            mfg_log_dir = MFG_STAGE_LOG_DIR.format(nic_type, stage_str, sn)
        else:
            mfg_log_dir = MODEL_STAGE_LOG_DIR.format(nic_type, stage_str, sn)

        if GLB_CFG_MFG_TEST_MODE:
            cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir)
            os.system(cmd)
        else:
            err_code = os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(mfg_log_dir))
            if not err_code:
                # try to change permission of the stage if this is first time created
                # this will fail if someone else created them...ask them to chmod 777
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))
                if stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L or stage == FF_Stage.FF_2C_H or stage == FF_Stage.FF_2C_L:
                    # since 4C directory is organized as /mfg_log/type/4C/4C-H/...
                    os.system("chmod 777 {:s}".format(mfg_log_dir+"/../.."))
            else:
                # chdir from mfg_log/type/stage/sn --> mfg_log/MERGE/type/stage/sn
                mfg_log_dir = mfg_log_dir.replace(nic_type, "MERGE/"+nic_type)
                os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(mfg_log_dir))
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))
                if stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L or stage == FF_Stage.FF_2C_H or stage == FF_Stage.FF_2C_L:
                    os.system("chmod 777 {:s}".format(mfg_log_dir+"/../.."))

        # copy the onboard logs only once
        if log_hard_copy_flag:
            qa_log_pkg_file = mfg_log_dir + os.path.basename(log_pkg_file)
            if not libmfg_utils.network_get_file(ipaddr, userid, passwd, qa_log_pkg_file, os.path.join(logfile_parent, log_pkg_file)):
                mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file to {:}".format(qa_log_pkg_file), level=0)
                continue

            mtp_mgmt_ctrl.cli_log_inf("[{:s}] Collecting log file {:s}".format(sn, qa_log_pkg_file))

            # It is fine to do hard copy
            #log_hard_copy_flag = False
            # relative link is ../sn/log_pkg_file
            log_relative_link = "../{:s}/{:s}".format(sn, os.path.basename(log_pkg_file))

            if mirror_logdir:
                dest = mirror_logdir + "/" + os.path.basename(qa_log_pkg_file)
                cmd = "cp {:s} {:s}".format(qa_log_pkg_file, mirror_logdir)
                os.system(cmd)
                mtp_mgmt_ctrl.cli_log_inf("Log also stored to {:s}".format(dest))

        # create hard link
        else:
            mtp_mgmt_ctrl.cli_log_inf("[{:s}] Create link log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
            chdir_cmd = "cd {:s}".format(mfg_log_dir)
            ln_cmd = MFG_DIAG_CMDS.MFG_LOG_LINK_FMT.format(log_relative_link, os.path.basename(log_pkg_file))
            cmd = "{:s} && {:s}".format(chdir_cmd, ln_cmd)
            os.system(cmd)
        
    if stage == FF_Stage.FF_SWI:
        # csp log files    
        cmd = "ls --color=never /home/diag/diag/asic/asic_src/ip/cosim/tclsh/csp*"
     
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        listoffileoutput = mtp_mgmt_ctrl.mtp_get_cmd_buf()
        listoffile = listoffileoutput.split()
        
        listcspfiletoupload = list()
        for cspfile in listoffile:
            if 'txt' in cspfile:
                listcspfiletoupload.append(cspfile)
        for cspfilepath in listcspfiletoupload:
            if not csp_log_dir:
                mtp_mgmt_ctrl.cli_log_err("Unable to copy CSP log file", level=0)
                break
            if GLB_CFG_MFG_TEST_MODE:
                cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(csp_log_dir)
                os.system(cmd)
            else:
                err_code = os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(csp_log_dir))
                if not err_code:
                    os.system("chmod 777 {:s}".format(csp_log_dir+"/.."))
                else:
                    csp_log_dir = csp_log_dir.replace("CSP_REC", "MERGE/CSP_REC")
                    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(csp_log_dir))
                    os.system("chmod 777 {:s}".format(csp_log_dir+"/.."))
            csp_log_file = csp_log_dir + os.path.basename(cspfilepath)
            if not libmfg_utils.network_get_file(ipaddr, userid, passwd, csp_log_file, cspfilepath):
                mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file {:}".format(csp_log_file), level=0)
                continue
            mtp_mgmt_ctrl.cli_log_inf("Collecting csp log file {:s}".format(csp_log_file))

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

    # clear the onboard logs
    logfile_list.append(log_pkg_file)
    logfile_list.append(logfile_path)
    #cmd = "rm -rf {:s}".format(" ".join(logfile_list))
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

    mtp_mgmt_ctrl.cli_log_inf("Collecting {:s} log files complete".format(stage), level=0)

    return local_test_log_file
