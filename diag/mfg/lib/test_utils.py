import sys, os
import traceback
from libdefs import *
from libmfg_cfg import *
import barcode_field as bf
import libmfg_utils
import libmtp_utils
import testlog
import scanning
import parallelize

@parallelize.sequential_nic_test
def test_start_nic_log_message(mtp_mgmt_ctrl, slot, stage, test):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, stage, test))
    return True

@parallelize.sequential_nic_test
def test_skip_nic_log_message(mtp_mgmt_ctrl, slot, stage, test):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    mtp_mgmt_ctrl.cli_log_slot_wrn(slot, MTP_DIAG_Report.NIC_DIAG_TEST_SKIPPED.format(sn, stage, test))
    return True

@parallelize.sequential_nic_test
def test_fail_nic_log_message(mtp_mgmt_ctrl, slot, stage, test, start_ts, swmtestmode=Swm_Test_Mode.SW_DETECT):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, stage, test, "FAILED", duration))
    if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
        alom_sn = mtp_mgmt_ctrl.get_scanned_alom_sn(slot)
        mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(alom_sn, stage, test, "FAILED", duration))
    return True

@parallelize.sequential_nic_test
def test_pass_nic_log_message(mtp_mgmt_ctrl, slot, stage, test, start_ts, swmtestmode=Swm_Test_Mode.SW_DETECT):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, stage, test, duration))
    if mtp_mgmt_ctrl.mtp_get_nic_type(slot) == NIC_Type.NAPLES25SWM and swmtestmode == Swm_Test_Mode.ALOM:
        alom_sn = mtp_mgmt_ctrl.get_scanned_alom_sn(slot)
        mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(alom_sn, stage, test, duration))
    return True

def get_test_constants(stage, mtp_id, subcommand):
    testsuite_config = {
        FF_Stage.FF_DL:
            {
                "timeout": MTP_Const.MFG_DL_TEST_TIMEOUT
            },
        FF_Stage.SCAN_DL:
            {
                "timeout": MTP_Const.MFG_DL_TEST_TIMEOUT
            },
        FF_Stage.FF_P2C:
            {
                "timeout": MTP_Const.MFG_P2C_TEST_TIMEOUT
            },
        FF_Stage.FF_2C_H:
            {
                "timeout": MTP_Const.MFG_4C_TEST_TIMEOUT
            },
        FF_Stage.FF_2C_L:
            {
                "timeout": MTP_Const.MFG_4C_TEST_TIMEOUT
            },
        FF_Stage.FF_4C_H:
            {
                "timeout": MTP_Const.MFG_4C_TEST_TIMEOUT
            },
        FF_Stage.FF_4C_L:
            {
                "timeout": MTP_Const.MFG_4C_TEST_TIMEOUT
            },
        FF_Stage.FF_ORT:
            {
                "timeout": MTP_Const.MFG_ORT_TEST_TIMEOUT
            },
        FF_Stage.FF_RDT:
            {
                "timeout": MTP_Const.MFG_RDT_TEST_TIMEOUT
            },
        FF_Stage.FF_SWI:
            {
                "timeout": MTP_Const.MFG_SW_TEST_TIMEOUT
            },
        FF_Stage.FF_FST:
            {
                "timeout": MTP_Const.MFG_FST_TEST_TIMEOUT
            },
        FF_Stage.FF_SRN:
            {
                "timeout": MTP_Const.MFG_MTPSCREEN_TEST_TIMEOUT
            },
        FF_Stage.CONVERT:
            {
                "timeout": MTP_Const.MFG_DL_TEST_TIMEOUT
            }
    }
    if stage not in list(testsuite_config.keys()):
        libmfg_utils.cli_err("Script not defined for stage {:s}".format(stage))
        return None, None, None, None
    mtp_script_dir = "mfg_test_script/"
    mtp_script_pkg = "mfg_test_script.{:s}.tar".format(mtp_id)
    script_cmd = "python3 ./mfg_test.py {:s}".format(subcommand)
    test_timeout = testsuite_config[stage]["timeout"]
    mtp_script_dir = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + mtp_script_dir
    return mtp_script_dir, mtp_script_pkg, script_cmd, test_timeout

def mtp_test_cleanup(mtp_mgmt_ctrl):
    mtp_mgmt_ctrl.close_file_handles()
    os.system("sync")


def fail_mtp_test(mtp_mgmt_ctrl, mtp_test_summary):
    mtp_test_summary.append((0, mtp_mgmt_ctrl._id, None, False, False))
    # NZ TODO: update record instead of append


def single_mtp_test(stage, mtp_mgmt_ctrl, mtp_test_summary, skip_test_list, *args, **kwargs):
    # Handle outer-test args
    mtp_id = mtp_mgmt_ctrl._id
    loop_cnt      = kwargs.get("iteration", 1)
    no_pc         = kwargs.get("no_pc", None)
    stop_on_err   = kwargs.get("stop_on_err", False)
    mirror_logdir = kwargs.get("jobd_logdir", None)
    swm_test_mode = kwargs.get("swm_test_mode", Swm_Test_Mode.SW_DETECT)
    testsuite     = kwargs.get("testsuite_name", stage)
    mtp_type      = kwargs.get("mtp_type", None)

    for loop_idx in range(1, loop_cnt+1):
        ### Begin logging
        testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)

        ### Barcode scanning
        if loop_idx == 1:
            if not ENABLE_SCAN_VERIFY:
                skip_test_list.append("SCAN_VERIFY") # allow skipping via global var or arg

            if stage == FF_Stage.FF_DL and testsuite in (FF_Stage.SCAN_DL, FF_Stage.CONVERT):
                scanning.mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, stage, swmtestmode=swm_test_mode)
            elif stage in (FF_Stage.FF_DL, FF_Stage.FF_SWI):
                if "SCAN_VERIFY" not in skip_test_list:
                    scanning.mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, stage, swmtestmode=swm_test_mode)
            elif FST_SCAN_ENABLE and stage == FF_Stage.FF_FST:
                if "SCAN_VERIFY" not in skip_test_list:
                    scanning.mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, stage)

            elif stage == FF_Stage.FF_SRN:
                if mtp_type == MTP_TYPE.TURBO_ELBA:
                    mtp_mgmt_ctrl.cli_log_inf("Start the Barcode Scan Process", level=0)
                    while True:
                        scan_rslt = scanning.mtp_screen_barcode_scan(mtp_mgmt_ctrl)
                        if scan_rslt and scan_rslt["VALID"]:
                            mtp_mgmt_ctrl.cli_log_inf("Scan validate MTP SN", level=0)
                            break
                        mtp_mgmt_ctrl.cli_log_inf("Restart the Barcode Scan Process", level=0)
                    mtp_mgmt_ctrl.set_mtp_sn(scan_rslt["MTP_SN"].strip())
                    mtp_mgmt_ctrl.set_mtp_mac(scan_rslt["MTP_MAC"].strip())

        if loop_cnt > 1:
            mtp_mgmt_ctrl.cli_log_inf("\n" * 3)
            mtp_mgmt_ctrl.cli_log_inf("#" * 80)
            mtp_mgmt_ctrl.cli_log_inf("==== {:s} TEST ITERATION #{:06d} START ====".format(stage, loop_idx))
            mtp_mgmt_ctrl.cli_log_inf("\n" * 3)
            mtp_mgmt_ctrl.cli_log_inf("#" * 80)

        ### Power cycle MTP
        if stage in (FF_Stage.FF_RDT, FF_Stage.FF_ORT):
            # overwrite no_pc option for these stages,
            if stage == FF_Stage.FF_ORT:
                libmfg_utils.mtpid_list_poweroff([mtp_mgmt_ctrl], safely=False)
                libmfg_utils.mtpid_list_poweron([mtp_mgmt_ctrl])
            if stage == FF_Stage.FF_RDT:
                if loop_idx == 1:
                    libmfg_utils.mtpid_list_poweroff([mtp_mgmt_ctrl], safely=False)
                libmfg_utils.mtpid_list_poweron([mtp_mgmt_ctrl])
        else:
            if not no_pc:
                libmfg_utils.mtpid_list_poweroff([mtp_mgmt_ctrl], safely=False)
                libmfg_utils.mtpid_list_poweron([mtp_mgmt_ctrl])

        ### Deploy & run the test
        mtp_start_ts = libmfg_utils.timestamp_snapshot()
        single_test_result = single_mtp_test_iteration(stage, mtp_mgmt_ctrl, mtp_test_summary, skip_test_list, loop_idx=loop_idx, *args, **kwargs)
        # False only if MTP setup fails. NIC failure is captured in mtp_test_summary
        mtp_stop_ts = libmfg_utils.timestamp_snapshot()

        if loop_cnt > 1:
            if stage in (FF_Stage.FF_RDT, FF_Stage.FF_ORT):
                libmfg_utils.cli_inf("MFG {:s} Test Duration:{:s}".format(stage, str(mtp_stop_ts - mtp_start_ts)))
            mtp_mgmt_ctrl.cli_log_inf("\n" * 3)
            mtp_mgmt_ctrl.cli_log_inf("#" * 80)
            mtp_mgmt_ctrl.cli_log_inf("==== {:s} TEST ITERATION #{:06d} END   ====".format(stage, loop_idx))
            mtp_mgmt_ctrl.cli_log_inf("\n" * 3)
            mtp_mgmt_ctrl.cli_log_inf("#" * 80)

        if (stop_on_err or stage==FF_Stage.FF_RDT) and not single_test_result:
            if stage==FF_Stage.FF_RDT:
                mtp_mgmt_ctrl.cli_log_inf("******AT LEAST ONE SLOT FAILED IN RDT TEST, SO EXIT RDT TEST******", level=0)
            break

        ### Handle test logs
        # If MTP failed, fail all slots and dont post to FF
        # otherwise, logs_local=False meaning logs need to be accessed from MTP
        if single_test_result:
            logs_local = False
            send_report = True
        else: 
            libmfg_utils.fail_all_slots(mtp_mgmt_ctrl)
            logs_local = True
            send_report = False

        if not testlog.save_logs(mtp_mgmt_ctrl, stage, mtp_test_summary, mtp_start_ts, mtp_stop_ts, mirror_logdir, logs_local, send_report):
            fail_mtp_test(mtp_mgmt_ctrl, mtp_test_summary)

    ### Final power off
    if not no_pc:
        libmfg_utils.mtpid_list_poweroff([mtp_mgmt_ctrl])

def single_mtp_test_iteration(stage, mtp_mgmt_ctrl, mtp_test_summary, skip_test_list=[], skip_slot_list=[], **kwargs):
    """
        1) Handle args 2) setup MTP 3) deploy script

        Returns False only if there is a failure in steps 1 or 2.
    """
    try:
        ####### Intercept args at inner-test
        mtp_id = mtp_mgmt_ctrl._id
        mtpcfg_file   = kwargs.get("mtpcfg", None)
        scanned_dpn   = kwargs.get("dpn", None)
        scanned_sku   = kwargs.get("sku", None)
        testsuite     = kwargs.get("testsuite_name", stage)
        mtp_type      = kwargs.get("mtp_type", None)

        ####### MTP SETUP: start_diag, MTP sanity check, ...
        mtp_mgmt_ctrl.mtp_mgmt_disconnect()

        if stage == FF_Stage.FF_DL and testsuite in (FF_Stage.SCAN_DL, FF_Stage.CONVERT):
            tlf = testlog.get_mtp_test_log_folder(mtp_mgmt_ctrl)
            scan_cfg_file = os.path.join(tlf, MTP_DIAG_Logfile.SCAN_BARCODE_FILE)
            nic_fru_cfg = libmfg_utils.load_cfg_from_yaml(scan_cfg_file)
            if not mtp_common_setup_fpo_scandl(mtp_mgmt_ctrl, stage, nic_fru_cfg, skip_test_list):
                return False
        elif stage == FF_Stage.FF_FST:
            if not mtp_common_setup_fst(mtp_mgmt_ctrl, stage, skip_test_list):
                return False
        elif stage == FF_Stage.FF_SRN:
            if not mtp_common_setup_srn(mtp_mgmt_ctrl, stage, skip_test_list, mtp_type):
                return False
            mtp_type = mtp_mgmt_ctrl.mtp_get_mtp_type()
        else:
            if kwargs['subcommand'] == 'cpld':
                # Get New CPLD binary file list
                new_cpld_json_dict = libmtp_utils.load_cpld_info_json(kwargs['cpldfile'], kwargs['verbosity'])
                if not new_cpld_json_dict:
                    mtp_mgmt_ctrl.cli_log_err("Failed to Load CPLD JSON file, abort...")
                    return False
                new_cpld_files_path = libmtp_utils.generate_cpld_img_full_path_list(new_cpld_json_dict, kwargs['verbosity'])
                if not new_cpld_files_path:
                    mtp_mgmt_ctrl.cli_log_err("Failed to Got CPLD Binary file name and path from JSON file, abort...")
                    return False
                new_cpld_files = [os.path.basename(file) for file in new_cpld_files_path]
                # force stage to DL to update MTP CPLD image files specified in libmfg_cfg.py, using the libmfg_cfg.py specified cpld image as downgrade target
                if not mtp_common_setup_fpo_cpld_validation(mtp_mgmt_ctrl, new_cpld_files=new_cpld_files):
                    fail_mtp_test(mtp_mgmt_ctrl, mtp_test_summary)
                    return False
            else:
                if not mtp_common_setup_fpo(mtp_mgmt_ctrl, stage, skip_test_list, scanned_dpn, scanned_sku):
                    return False

        fail_nic_list = list()
        pass_nic_list = list()

        ####### NIC SETUP: load SN/PN, flexflow pre-post, loopback sanity check
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not nic_prsnt_list[slot]:
                continue
            pass_nic_list.append(slot)

        if stage != FF_Stage.FF_FST and kwargs['subcommand'] not in ('cpld', 'emmc', 'ddr'):  # skip these tests until FST scanning is implemented
            fail_nic_list += nic_common_setup(mtp_mgmt_ctrl, stage, pass_nic_list, skip_test_list)

        #re-assembly command line arguments to call next level script, which running on MTP locally
        cmd_options = []
        for k, v in kwargs.items():
            # remove or convert options which not support by next layer script
            if k == 'func':
                continue
            if k == 'subcommand':
                continue
            if k == 'iteration':
                continue
            if k == 'loop_idx':
                if kwargs["subcommand"] in ('2c', 'p2c', '4c', 'ort', 'rdt'):
                    #reuse iteration as loop index passdown to next layer
                    cmd_options.append('--iteration')
                    cmd_options.append(str(v))
                continue
            if k == 'no_pc':
                continue
            if k == 'testsuite_name':
                continue
            if k == 'mtpcfg':
                if v:
                    cmd_options.append('--'+ k)
                    cmd_options.append(os.path.basename(v)) # file has been packaged into config/, discard full path
                continue
            if k == 'jobd_logdir':
                continue
            # assemly by option value type
            if isinstance(v, list):
                if v:
                    cmd_options.append('--'+ k)
                    cmd_options.append(' '.join(v))
                continue
            elif isinstance(v, bool):
                if v:
                    cmd_options.append('--'+ k)
                continue
            else:
                if v:
                    cmd_options.append('--'+ k)
                    cmd_options.append(str(v))
        # assemble arguments determined in inner function
        if stage == FF_Stage.FF_SRN:
            if mtp_type == MTP_TYPE.TURBO_ELBA:
                cmd_options.append("--mtpsn")
                cmd_options.append(mtp_mgmt_ctrl.get_mtp_sn())
                cmd_options.append("--mtpmac")
                cmd_options.append(mtp_mgmt_ctrl.get_mtp_mac())
        if fail_nic_list:
            cmd_options.append("--fail_slots")
            cmd_options.append(' '.join(map(str,fail_nic_list)))
        test_cmd_args = " " + " ".join(cmd_options)

        ####### COPY script, config file on to each MTP Chassis
        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP {:s} Test script".format(stage), level=0)
        mtp_script_dir, mtp_script_pkg, script_cmd, test_timeout = get_test_constants(testsuite, mtp_id, kwargs['subcommand'])
        if mtp_script_dir is None:
            return False

        # Login the remote command to log file, before close and set log file handler to STDOUT
        mtp_mgmt_ctrl.cli_log_inf("", level=0)
        mtp_mgmt_ctrl.cli_log_inf("", level=0)
        mtp_mgmt_ctrl.cli_log_inf("*" *80, level=0)
        mtp_mgmt_ctrl.cli_log_inf("After Deploy, will execute remote command: " + script_cmd + test_cmd_args, level=0)
        mtp_mgmt_ctrl.cli_log_inf("*" * 80, level=0)
        mtp_mgmt_ctrl.cli_log_inf("", level=0)
        mtp_mgmt_ctrl.cli_log_inf("", level=0)

        mtp_test_cleanup(mtp_mgmt_ctrl) # Close file handles before zip
        mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)
        if not testlog.mtp_init_test_script(mtp_mgmt_ctrl, mtp_script_dir, mtp_script_pkg, extra_config=mtpcfg_file):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP {:s} Test script failed".format(stage), level=0)
            return False
        mtp_mgmt_ctrl.cli_log_inf("Deploy MTP {:s} Test script complete".format(stage), level=0)

        if stage == FF_Stage.FF_SRN:
            cmd = "mkdir {:s}".format(mtp_script_dir)
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "cd {:s}".format(mtp_script_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

        # RUN script command
        mtp_mgmt_ctrl.cli_log_inf("MFG {:s} Test Start".format(stage), level=0)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(script_cmd + test_cmd_args, timeout=test_timeout)
        mtp_mgmt_ctrl.cli_log_inf("MFG {:s} Test Complete".format(stage), level=0)
        mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
        testlog.replace_logfile_path(mtp_mgmt_ctrl, mtp_script_dir)
        return True
    except Exception as e:
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.cli_log_err(err_msg)
        return False

def mtp_common_setup(mtp_mgmt_ctrl, stage, skip_test_list=[]):
    test_list = ["MTP_CONNECT", "MTP_HEALTH_CONNECT", "DSP_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "NIC_INIT"]
    if not MTP_HEALTH_MONITOR: test_list.remove("MTP_HEALTH_CONNECT")
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list):
        return False
    return True

def mtp_common_setup_scandl(mtp_mgmt_ctrl, stage, scanned_fru_cfg, skip_test_list=[]):
    test_list = ["MTP_CONNECT", "MTP_HEALTH_CONNECT", "DSP_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "SCAN_NIC_INIT"]
    if not MTP_HEALTH_MONITOR: test_list.remove("MTP_HEALTH_CONNECT")
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list, scanned_fru_cfg=scanned_fru_cfg):
        return False
    return True

def mtp_common_setup2(mtp_mgmt_ctrl, stage, skip_test_list=[]):
    mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    test_list = ["MTP_CONNECT", "MTP_HEALTH_CONNECT", "DSP_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID"]
    if not MTP_HEALTH_MONITOR: test_list.remove("MTP_HEALTH_CONNECT")
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list):
        return False
    mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    return True

def mtp_common_setup_fpo(mtp_mgmt_ctrl, stage, skip_test_list=[], scanned_dpn=None, scanned_sku=None):
    test_list = ["MTP_FPO_CONNECT", "MTP_TIME_SET", "DIAG_UPDATE", "PYTHON_UPDATE", "DIAG_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "NIC_INIT", "NIC_FW_UPDATE"]
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list, scanned_dpn=scanned_dpn, scanned_sku=scanned_sku):
        return False
    return True

def mtp_common_setup_srn(mtp_mgmt_ctrl, stage, skip_test_list=[], mtp_type=MTP_TYPE.MATERA):
    mtp_mgmt_ctrl._mtp_type = mtp_type
    if mtp_type == MTP_TYPE.TURBO_ELBA:
        test_list = ["MTP_FPO_CONNECT", "MTP_TIME_SET", "I210_PRSNT_CHECK", "I210_IMAGE_CHECK", "MTP_POWERCYCLE",
                     "MTP_FPO_CONNECT", "MTP_TIME_SET", "DIAG_UPDATE", "PYTHON_UPDATE", "DIAG_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "NIC_INIT", "NIC_FW_UPDATE"]
    else:
        test_list = ["MTP_FPO_CONNECT", "MTP_TIME_SET", "MTP_USB_SANITY_CHECK", "DIAG_UPDATE", "AMD_AVT_TOOL_INSTALL", "PYTHON_UPDATE",
                     "DIAG_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "NIC_INIT"]

    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list, mtp_type=mtp_type):
        return False
    return True

def mtp_common_setup_fst(mtp_mgmt_ctrl, stage, skip_test_list=[]):
    test_list = ["FST_CONNECT", "MTP_TIME_SET", "FST_UPDATE", "PYTHON_UPDATE", "FST_ID"]
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list):
        return False
    return True

def mtp_common_setup_fpo_scandl(mtp_mgmt_ctrl, stage, scanned_fru_cfg, skip_test_list=[]):
    test_list = ["MTP_FPO_CONNECT", "MTP_TIME_SET", "DIAG_UPDATE", "DIAG_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "SCAN_NIC_INIT", "NIC_FW_UPDATE"]
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list, scanned_fru_cfg=scanned_fru_cfg):
        return False
    return True

def mtp_common_setup_fpo_cpld_validation(mtp_mgmt_ctrl, stage=FF_Stage.FF_DL, skip_test_list=[], new_cpld_files=[]):
    test_list = ["MTP_FPO_CONNECT", "MTP_TIME_SET", "DIAG_UPDATE", "DIAG_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "NIC_INIT", "NIC_FW_UPDATE"]
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list):
        return False
    # copy new version of CPLD binary files, which will be use as upgrade target
    if not libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, new_cpld_files):
        mtp_mgmt_ctrl.mtp_diag_fail_report("Sync new CPLD Binary files with MTP failed, test abort...")
        return False
    return True

def mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list, **kwargs):
    sn = "MTP"
    for test in test_list:
        if test in skip_test_list:
            continue

        start_ts = mtp_mgmt_ctrl.log_test_start(test)
        mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, stage, test), level=0)

        if test == "MTP_FPO_CONNECT":
            ret = mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, retry_with_powercycle=True)

        elif test == "MTP_CONNECT":
            ret = mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True)

        elif test == "MTP_HEALTH_CONNECT":
            ret = mtp_mgmt_ctrl.get_mtp_health_monitor().mtp_health_mgmt_connect(prompt_cfg=True)

        elif test == "FST_CONNECT":
            ret = mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, max_retry=10)

        elif test == "MTP_TIME_SET":
            ret = mtp_mgmt_ctrl.mtp_mgmt_set_date(stage)

        elif test == "DIAG_UPDATE":
            ret = libmfg_utils.mtp_update_diag_image(mtp_mgmt_ctrl)

        elif test == "NIC_FW_UPDATE":
            ret = libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, libmfg_utils.mtp_get_sw_image_list(mtp_mgmt_ctrl, stage))

        elif test == "FST_UPDATE":
            ret = libmfg_utils.mtp_update_fst_image(mtp_mgmt_ctrl)

        elif test == "PYTHON_UPDATE":
            ret = libmfg_utils.mtp_python369_sitepackage_update(mtp_mgmt_ctrl)

        elif test == "AMD_AVT_TOOL_INSTALL":
            # Install AMD CPU validation tool AVT onto MTP
            ret = libmfg_utils.mtp_avt_tool_installation(mtp_mgmt_ctrl)

        elif test == "DIAG_START":
            ret = mtp_mgmt_ctrl.mtp_diag_pre_init(start_dsp=False, stage=stage)

        elif test == "DSP_START":
            ret = mtp_mgmt_ctrl.mtp_diag_pre_init(start_dsp=True, stage=stage)

        elif test == "DIAG_POST":
            ret = mtp_mgmt_ctrl.mtp_diag_post_init()

        elif test == "MTP_SANITY_CHECK":
            ret = mtp_mgmt_ctrl.mtp_hw_init(stage)

        elif test == "MTP_USB_SANITY_CHECK":
            ret = libmtp_utils.mtp_usb_sanity_check(mtp_mgmt_ctrl)

        elif test == "I210_PRSNT_CHECK":
            ret = libmtp_utils.check_mtp_host_nic_presence(mtp_mgmt_ctrl)

        elif test == "I210_IMAGE_CHECK":
            ret = libmtp_utils.verify_img_mtp_host_nic(mtp_mgmt_ctrl)

        elif test == "MTP_ID":
            ret = mtp_mgmt_ctrl.mtp_sys_info_disp()

        elif test == "FST_ID":
            ret = mtp_mgmt_ctrl.fst_sys_info_disp()

        elif test == "NIC_INIT":
            ret = mtp_mgmt_ctrl.mtp_nic_init(stage, scanned_dpn=kwargs.get("scanned_dpn", None), scanned_sku=kwargs.get("scanned_sku", None))

        elif test == "SCAN_NIC_INIT":
            ret = mtp_mgmt_ctrl.mtp_nic_init(stage, scanned_fru=kwargs["scanned_fru_cfg"])

        elif test == "MTP_POWERCYCLE":
            ret  = libmfg_utils.mtpid_list_poweroff([mtp_mgmt_ctrl])
            ret &= libmfg_utils.mtpid_list_poweron([mtp_mgmt_ctrl])

        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown test {}".format(test))

        duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
        if not ret:
            mtp_mgmt_ctrl.cli_log_err(MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, stage, test, "FAILED", duration), level=0)
            return False
        else:
            mtp_mgmt_ctrl.cli_log_inf(MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, stage, test, duration), level=0)
    return True

def nic_common_setup(mtp_mgmt_ctrl, stage, pass_nic_list, skip_test_list):
    test_list = list()

    ## all cards (failed or passed) need to go through FF_AREA_CHECK. so make it the first test.
    if GLB_CFG_MFG_TEST_MODE and FLEX_SHOP_FLOOR_CONTROL and stage not in (FF_Stage.FF_ORT, FF_Stage.FF_RDT):
        test_list.append("FF_AREA_CHECK")

    test_list.append("NIC_TYPE")

    if stage in (FF_Stage.FF_P2C, FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_ORT, FF_Stage.FF_RDT):
        test_list.append("SANITY_CHECK_SETUP")
    if stage in (FF_Stage.FF_P2C, FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_ORT, FF_Stage.FF_RDT) or (mtp_mgmt_ctrl._mtp_type == MTP_TYPE.MATERA and stage in (FF_Stage.FF_4C_L, FF_Stage.FF_4C_H)):
        test_list.append("QSFP_SANITY_CHECK")
    if stage in (FF_Stage.FF_P2C, FF_Stage.FF_2C_L, FF_Stage.FF_2C_H, FF_Stage.FF_ORT, FF_Stage.FF_RDT):
        test_list.append("RJ45_SANITY_CHECK")
    return nic_common_setup_test_picker(mtp_mgmt_ctrl, stage, pass_nic_list, test_list, skip_test_list)

def nic_common_setup_test_picker(mtp_mgmt_ctrl, stage, pass_nic_list, test_list, skip_test_list):
    fail_nic_list = list()

    for test in test_list:
        if test in skip_test_list:
            test_skip_nic_log_message(mtp_mgmt_ctrl, pass_nic_list, stage, test)
            continue

        start_ts = mtp_mgmt_ctrl.log_test_start(test)
        test_start_nic_log_message(mtp_mgmt_ctrl, pass_nic_list, stage, test)

        if test == "NIC_TYPE":
            test_fail_nic_list = mtp_mgmt_ctrl.mtp_nic_type_test(pass_nic_list)
        elif test == "FF_AREA_CHECK":
            test_fail_nic_list = libmfg_utils.flx_web_srv_two_way_comm_precheck_uut(mtp_mgmt_ctrl, pass_nic_list, stage, retry=FLEX_TWO_WAY_COMM.PRE_POST_RETRY)
        elif test == "SANITY_CHECK_SETUP":
            test_fail_nic_list = libmfg_utils.sanity_check_setup(mtp_mgmt_ctrl, pass_nic_list)
        elif test == "QSFP_SANITY_CHECK":
            test_fail_nic_list = libmfg_utils.loopback_sanity_check(mtp_mgmt_ctrl, pass_nic_list)
        elif test == "RJ45_SANITY_CHECK":

            # shrink nic_list to only those that need rj45 check
            rj45_nic_list = list()
            for slot in pass_nic_list:
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type in [NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4]:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Skip {:s} For This Slot".format(test))
                elif nic_type in GIGLIO_NIC_TYPE_LIST  + SALINA_NIC_TYPE_LIST:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Skip {:s} For This Slot".format(test))
                else:
                    rj45_nic_list.append(slot)

            test_fail_nic_list = libmfg_utils.rj45_sanity_check(mtp_mgmt_ctrl, rj45_nic_list)
        else:
            mtp_mgmt_ctrl.cli_log_err("Unknown test {:s}".format(test))
            test_fail_nic_list = pass_nic_list[:]

        for slot in test_fail_nic_list:
            if slot not in fail_nic_list:
                fail_nic_list.append(slot)
            if slot in pass_nic_list:
                pass_nic_list.remove(slot) # dont proceed that slot

        duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)
        test_fail_nic_log_message(mtp_mgmt_ctrl, test_fail_nic_list, stage, test, start_ts)
        test_pass_nic_log_message(mtp_mgmt_ctrl, pass_nic_list, stage, test, start_ts)

    return fail_nic_list

