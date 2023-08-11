import sys, os
import time
import traceback
import threading
from libdefs import *
from libmfg_cfg import *
import libmfg_utils
import libmtp_utils
import testlog

def single_nic_test_start(mtp_mgmt_ctrl, slot, test_name):
    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test_name)
    return start_ts

def single_nic_test_stop(mtp_mgmt_ctrl, slot, test_name, start_ts):
    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test_name, start_ts)
    return duration

def log_test_start(mtp_mgmt_ctrl, slot, test_section, test_name):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, test_section, test_name))

def log_test_result(mtp_mgmt_ctrl, slot, test_section, test_name, rslt, duration):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    if not rslt:
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, test_section, test_name, "FAILED", duration))
    else:
        mtp_mgmt_ctrl.cli_log_slot_inf_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, test_section, test_name, duration))

def map_rslt_to_slot(rslt_list):
    # rslt_list as e.g. [True, True, False, False, True, True, True, True, True, True]
    # return fail_nic_list as e.g. [3,4]
    fail_nic_list = list()
    for idx, slot_rslt in enumerate(rslt_list):
        if not slot_rslt:
            fail_nic_list.append(idx)
    return fail_nic_list

"""
    Wrapper to run a function on multiple slots, passing in a nic_list and returning a fail_nic_list.

    Define the function as:
        @test_utils.semi_parallel_test_section
        def function_name(mtp_mgmt_ctrl, slot, ...):

    First two arguments MUST match exactly. Return value must be True/False.


    Call the function as:
        test_fail_nic_list = function_name(mtp_mgmt_ctrl, nic_list, ...)

"""
def semi_parallel_test_section(func):

    def single_slot_func(func, mtp_mgmt_ctrl, slot, test_rslt_list, *args, **kwargs):
        try:
            ###### RUN THE TEST #####
            ret = func(mtp_mgmt_ctrl, slot, *args, **kwargs)
            #########################
            if ret:
                test_rslt_list[slot] = True
            else:
                test_rslt_list[slot] = False
        except Exception:
            test_rslt_list[slot] = False
            err_msg = traceback.format_exc()
            mtp_mgmt_ctrl.cli_log_slot_err(slot, err_msg)

    def start_end(mtp_mgmt_ctrl, nic_list=None, *test_args, **test_kwargs):
        test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
        for slot in nic_list:
            single_slot_func(func, mtp_mgmt_ctrl, slot, test_rslt_list, *test_args, **test_kwargs)
        return map_rslt_to_slot(test_rslt_list)

    return start_end

"""
    Wrapper to run a function on multiple slots in parallel, passing in a nic_list and returning a fail_nic_list.

    Define the function as:
        @test_utils.single_slot_test
        def function_name(mtp_mgmt_ctrl, slot, ...):

    First 2 arguments MUST match exactly. Return value must be True/False.


    Call the function with the following required arguments:
        ret = function_name(mtp_mgmt_ctrl, nic_list, "test section name", "test name", ...)

"""
def parallel_threaded_test(func):

    def threaded_func(func, mtp_mgmt_ctrl, slot, test_section, test_name, thread_rslt_list, *args, **kwargs):
        try:
            log_test_start(mtp_mgmt_ctrl, slot, test_section, test_name)
            start_ts = single_nic_test_start(mtp_mgmt_ctrl, slot, test_name)
            ###### RUN THE TEST #####
            ret = func(mtp_mgmt_ctrl, slot, *args, **kwargs)
            #########################
            duration = single_nic_test_stop(mtp_mgmt_ctrl, slot, test_name, start_ts)
            log_test_result(mtp_mgmt_ctrl, slot, test_section, test_name, ret, duration)
            if ret:
                thread_rslt_list[slot] = True
            else:
                thread_rslt_list[slot] = False
        except Exception:
            err_msg = traceback.format_exc()
            mtp_mgmt_ctrl.cli_log_slot_err(slot, err_msg)
            duration = single_nic_test_stop(mtp_mgmt_ctrl, slot, test_name, start_ts)
            log_test_result(mtp_mgmt_ctrl, slot, test_section, test_name, False, duration)
            thread_rslt_list[slot] = False

    def start_end(mtp_mgmt_ctrl, nic_list, test_section, test_name, *test_args, **test_kwargs):
        nic_thread_list = list()
        thread_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM

        for slot in nic_list:
            thread_args = tuple([func, mtp_mgmt_ctrl, slot, test_section, test_name, thread_rslt_list]) + test_args
            nic_thread = threading.Thread(
                target = threaded_func,
                args = thread_args,
                kwargs = test_kwargs
            )
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)
            time.sleep(1)

        # monitor all the thread
        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(1)

        return map_rslt_to_slot(thread_rslt_list)

    return start_end


def mtp_test_cleanup(error_code, fp_list=None):
    if fp_list:
        for fp in fp_list:
            fp.close()
    os.system("sync")

def fail_mtp_test(mtp_mgmt_ctrl, mtp_test_summary):
    # abort test without saving logfile
    mtp_test_summary.append((0, mtp_mgmt_ctrl._id, None, False, False))

def single_mtp_test(stage, mtp_mgmt_ctrl, mtp_test_summary, logfile_dir, open_file_track_list, skip_test_list=[], mirror_logdir=None, skip_slot_list=[], **kwargs):
    try:
        mtpcfg_file = None
        l1_sequence = None
        stop_on_err = None
        card_type = None
        swm_test_mode = None
        mtp_sn = None
        only_test_list = []
        nic_sw_img_file_list = []
        sw_pn_list = []
        profile_cfg_file_list = []
        if "mtpcfg_file" in kwargs:
            mtpcfg_file = kwargs["mtpcfg_file"]
        if "l1_sequence" in kwargs:
            l1_sequence = kwargs["l1_sequence"]
        if "stop_on_err" in kwargs:
            stop_on_err = kwargs["stop_on_err"]
        if "card_type" in kwargs:
            card_type = kwargs["card_type"]
        if "swm_test_mode" in kwargs:
            swm_test_mode = kwargs["swm_test_mode"]
        if "mtp_sn" in kwargs:
            mtp_sn = kwargs["mtp_sn"]
        if "only_test_list" in kwargs:
            only_test_list = kwargs["only_test_list"]
        if "nic_sw_img_file_list" in kwargs:
            nic_sw_img_file_list = kwargs["nic_sw_img_file_list"]
        if "sw_pn_list" in kwargs:
            sw_pn_list = kwargs["sw_pn_list"]
        if "profile_cfg_file_list" in kwargs:
            profile_cfg_file_list = kwargs["profile_cfg_file_list"]

        mtp_id = mtp_mgmt_ctrl._id
        mtp_mgmt_ctrl.set_mtp_sn(mtp_sn)
      
        ####### MTP SETUP: start_diag, MTP sanity check, ...
        if stage == FF_Stage.FF_FST:
            if not mtp_common_setup_fst(mtp_mgmt_ctrl, stage, skip_test_list):
                fail_mtp_test(mtp_mgmt_ctrl, mtp_test_summary)
                return False
        elif stage == FF_Stage.FF_SRN:
            if not mtp_common_setup_srn(mtp_mgmt_ctrl, stage, skip_test_list):
                return False
        else:
            if not mtp_common_setup_fpo(mtp_mgmt_ctrl, stage, skip_test_list):
                fail_mtp_test(mtp_mgmt_ctrl, mtp_test_summary)
                return False

        if stage == FF_Stage.FF_SWI:
            # upload mainfw image received via args
            if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, ["NIC_SW_IMG_UPDATE"], skip_test_list, nic_sw_img_file_list=nic_sw_img_file_list):
                fail_mtp_test(mtp_mgmt_ctrl, mtp_test_summary)
                return False

        fail_nic_list = list()
        pass_nic_list = list()

        ####### NIC SETUP: load SN/PN, flexflow pre-post, loopback sanity check
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if not nic_prsnt_list[slot]:
                continue
            pass_nic_list.append(slot)

        if stage != FF_Stage.FF_FST: # skip these tests until FST scanning is implemented
            fail_nic_list += nic_common_setup(mtp_mgmt_ctrl, stage, pass_nic_list, skip_test_list)

        # Close file handles
        mtp_test_cleanup(open_file_track_list)

        testsuite_config = {
            FF_Stage.FF_DL:
                {
                "mtp_script_dir": "mtp_dl_script/",
                "mtp_script_pkg": "mtp_dl_script.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_DL_TEST_TIMEOUT
                },
            FF_Stage.FF_P2C:
                {
                "mtp_script_dir": "mtp_regression/",
                "mtp_script_pkg": "mtp_regression.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_P2C_TEST_TIMEOUT
                },
            FF_Stage.FF_2C_H:
                {
                "mtp_script_dir": "mtp_regression/",
                "mtp_script_pkg": "mtp_regression.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_4C_TEST_TIMEOUT
                },
            FF_Stage.FF_2C_L:
                {
                "mtp_script_dir": "mtp_regression/",
                "mtp_script_pkg": "mtp_regression.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_4C_TEST_TIMEOUT
                },
            FF_Stage.FF_4C_H:
                {
                "mtp_script_dir": "mtp_regression/",
                "mtp_script_pkg": "mtp_regression.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_4C_TEST_TIMEOUT
                },
            FF_Stage.FF_4C_L:
                {
                "mtp_script_dir": "mtp_regression/",
                "mtp_script_pkg": "mtp_regression.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_4C_TEST_TIMEOUT
                },
            FF_Stage.FF_ORT:
                {
                "mtp_script_dir": "mtp_regression/",
                "mtp_script_pkg": "mtp_regression.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_ORT_TEST_TIMEOUT
                },
            FF_Stage.FF_RDT:
                {
                "mtp_script_dir": "mtp_regression/",
                "mtp_script_pkg": "mtp_regression.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_RDT_TEST_TIMEOUT
                },
            FF_Stage.FF_SWI:
                {
                "mtp_script_dir": "mtp_swi_script/",
                "mtp_script_pkg": "mtp_swi_script.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_SW_TEST_TIMEOUT
                },
            FF_Stage.FF_FST:
                {
                "mtp_script_dir": "mtp_fst_script/",
                "mtp_script_pkg": "mtp_fst_script.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_FST_TEST_TIMEOUT
                },
            FF_Stage.FF_SRN:
                {
                "mtp_script_dir": "mtp_srn_script/",
                "mtp_script_pkg": "mtp_srn_script.{:s}.tar".format(mtp_id),
                "timeout": MTP_Const.MFG_MTPSCREEN_TEST_TIMEOUT
                }
        }

        # Copy script, config file on to each MTP Chassis
        if stage not in testsuite_config.keys():
            mtp_mgmt_ctrl.cli_log_err("Script package not defined for stage {:s}".format(stage))
            return False
        mtp_script_dir = testsuite_config[stage]["mtp_script_dir"]
        mtp_script_pkg = testsuite_config[stage]["mtp_script_pkg"]
        test_timeout   = testsuite_config[stage]["timeout"]
        if profile_cfg_file_list:
            profile_cfg = profile_cfg_file_list[0] # multiple profiles not supported
        else:
            profile_cfg = None

        mtp_mgmt_ctrl.cli_log_inf("Start deploy MTP {:s} Test script".format(stage), level=0)
        if not testlog.mtp_init_test_script(mtp_mgmt_ctrl, mtp_script_dir, mtp_script_pkg, logfile_dir, extra_script=profile_cfg, extra_config=mtpcfg_file):
            mtp_mgmt_ctrl.cli_log_err("Deploy MTP {:s} Test script failed".format(stage), level=0)
            return False
        mtp_mgmt_ctrl.cli_log_inf("Deploy MTP {:s} Test script complete".format(stage), level=0)
        
        mtp_script_dir = MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH + mtp_script_dir
        if stage == FF_Stage.FF_SRN:
            cmd = "mkdir {:s}".format(mtp_script_dir)
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd = "cd {:s}".format(mtp_script_dir)
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

        mtp_start_ts = libmfg_utils.timestamp_snapshot()
        mtp_mgmt_ctrl.cli_log_inf("MFG {:s} Test Start".format(stage), level=0)
        mtp_mgmt_ctrl.set_mtp_diag_logfile(sys.stdout)

        if stage == FF_Stage.FF_DL:
            cmd = "./mtp_dl_test.py"
        elif stage in (FF_Stage.FF_P2C, FF_Stage.FF_2C_H, FF_Stage.FF_2C_L, FF_Stage.FF_4C_H, FF_Stage.FF_4C_L, FF_Stage.FF_ORT, FF_Stage.FF_RDT):
            cmd = "./mtp_diag_regression.py --stage {:s}".format(stage)
        elif stage == FF_Stage.FF_SWI:
            cmd = "./mtp_swi_test.py"
        elif stage == FF_Stage.FF_FST:
            cmd = "./mtp_fst_test.py"
        elif stage == FF_Stage.FF_SRN:
            cmd = "./mtp_screen_regression.py"
        else:
            mtp_mgmt_ctrl.cli_log_err("Script command not defined for stage {:s}".format(stage))
            fail_mtp_test(mtp_mgmt_ctrl, mtp_test_summary)
            return False

        # add arguments
        cmd += " --mtpid {:s}".format(mtp_id)
        if swm_test_mode:
            cmd += " --swm {:s}".format(swm_test_mode)
        if skip_test_list:
            cmd += " --skip-test {:s}".format('"'+'" "'.join(skip_test_list).strip()+'"')
        if only_test_list:
            cmd += " --only-test {:s}".format('"'+'" "'.join(only_test_list).strip()+'"')
        if fail_nic_list:
            cmd += " --fail-slots "
            cmd += ' '.join(map(str,fail_nic_list))
        if skip_slot_list:
            cmd += " --skip-slots "
            cmd += ' '.join(map(str,skip_slot_list))
        if mtpcfg_file:
            cmd += " --mtpcfg " + os.path.basename(mtpcfg_file) # file has been packaged into config/, discard full path
        if stop_on_err:
            cmd += " --stop-on-err"
        if l1_sequence:
            cmd += " --l1-seq "

        if stage == FF_Stage.FF_SWI:
            img_opts = ""
            for nic_sw_img_file in nic_sw_img_file_list:
                img_opts += nic_sw_img_file + " "
            cmd += " --image {:s}".format(img_opts)

            sw_pn_opts = ""
            for sw_pn in sw_pn_list:
                sw_pn_opts += sw_pn + " "
            cmd += " --swpn {:s}".format(sw_pn_opts)

            if profile_cfg_file_list:
                profile_cfg_file = profile_cfg_file_list[0] # multiple profiles not supported
                cmd += " --profile {:s}".format(profile_cfg_file)

        if stage == FF_Stage.FF_FST:
            cmd += " --card_type {:s}".format(card_type)

        if stage == FF_Stage.FF_SRN:
            cmd += " --mtpsn {:s}".format(mtp_sn)

        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=test_timeout)
        mtp_mgmt_ctrl.cli_log_inf("MFG {:s} Test Complete".format(stage), level=0)
        mtp_mgmt_ctrl.set_mtp_diag_logfile(None)
        mtp_stop_ts = libmfg_utils.timestamp_snapshot()

        if stage == FF_Stage.FF_DL or stage == FF_Stage.FF_SWI:
            # save the avs and ecc dump log files
            asic_sub_dir = "/asic_logs/"
            cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mtp_script_dir + asic_sub_dir)
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
            cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_LOG_FILES, mtp_script_dir + asic_sub_dir)
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
            cmd = "mv {:s} {:s}".format(MTP_DIAG_Logfile.ONBOARD_ASIC_DUMP_FILES, mtp_script_dir + asic_sub_dir)
            mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

        test_log_file = testlog.get_mtp_logfile(mtp_mgmt_ctrl, mtp_script_dir, mtp_id, mtp_test_summary, stage, mirror_logdir=mirror_logdir)
        if not test_log_file:
            mtp_mgmt_ctrl.cli_log_err("MTP Collect {:s} Test result failed".format(stage), level=0)
            return False
        libmfg_utils.assign_nic_retest_flag(test_log_file, mtp_test_summary, stage)
        if GLB_CFG_MFG_TEST_MODE:
            libmfg_utils.mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, stage, mtp_test_summary)

            if stage == FF_Stage.FF_SRN:
                sn_type = ""
                duration = mtp_stop_ts - mtp_start_ts

                # dump the summary
                for slot, sn, nic_type, rc in mtp_test_summary:
                    nic_cli_id_str = id_str(mtp=mtp_id, nic=int(slot), base=0)
                    if rc:
                        mtp_mgmt_ctrl.cli_log_inf("[{:s}] {:s} PASS".format(mtp_id, mtp_sn))
                    else:
                        mtp_mgmt_ctrl.cli_log_inf("[{:s}] {:s} FAIL".format(mtp_id, mtp_sn))

                ret = libmfg_utils.flx_web_srv_post_uut_report(FF_Stage.FF_SRN, sn_type, mtp_sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, "MTP_SCREEN", "FAIL", err_dsc_list, err_code_list)
                if not ret:
                    mtp_mgmt_ctrl.cli_log_inf(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
                else:
                    mtp_mgmt_ctrl.cli_log_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))

        cmd = "rm -rf {:s}".format(test_log_file)
        os.system(cmd)
        return True
    except Exception as e:
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.cli_log_err(err_msg)
        fail_mtp_test(mtp_mgmt_ctrl, mtp_test_summary)
        return False

def mtp_common_setup(mtp_mgmt_ctrl, stage, skip_test_list=[]):
    test_list = ["MTP_CONNECT",                                    "DSP_START",  "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "NIC_INIT"]
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list):
        return False
    return True

def mtp_common_setup2(mtp_mgmt_ctrl, stage, skip_test_list=[]):
    mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    test_list = ["MTP_CONNECT",                                    "DSP_START",  "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID"]
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list):
        return False
    mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    return True

def mtp_common_setup_fpo(mtp_mgmt_ctrl, stage, skip_test_list=[]):
    test_list = ["MTP_FPO_CONNECT", "MTP_TIME_SET", "DIAG_UPDATE", "DIAG_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "NIC_INIT",     "NIC_FW_UPDATE"]
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list):
        return False
    return True

def mtp_common_setup_srn(mtp_mgmt_ctrl, stage, skip_test_list=[]):
    test_list = ["MTP_FPO_CONNECT", "MTP_TIME_SET", "I210_PRSNT_CHECK", "I210_IMAGE_CHECK", "MTP_POWERCYCLE",
                                                    "DIAG_UPDATE", "DIAG_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "NIC_INIT",     "NIC_FW_UPDATE"]
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list):
        return False
    return True

def mtp_common_setup_fst(mtp_mgmt_ctrl, stage, skip_test_list=[]):
    test_list = ["FST_CONNECT",     "MTP_TIME_SET", "FST_UPDATE"]
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list):
        return False
    return True

def mtp_common_setup_fpo_scandl(mtp_mgmt_ctrl, stage, scanned_fru_cfg, skip_test_list=[]):
    test_list = ["MTP_FPO_CONNECT", "MTP_TIME_SET", "DIAG_UPDATE", "DIAG_START", "DIAG_POST", "MTP_SANITY_CHECK", "MTP_ID", "SCAN_NIC_INIT", "NIC_FW_UPDATE"]
    if not mtp_common_setup_test_picker(mtp_mgmt_ctrl, stage, test_list, skip_test_list, scanned_fru_cfg=scanned_fru_cfg):
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

        elif test == "FST_CONNECT":
            ret = mtp_mgmt_ctrl.mtp_mgmt_connect(prompt_cfg=True, max_retry=10)

        elif test == "MTP_TIME_SET":
            ret = mtp_mgmt_ctrl.mtp_mgmt_set_date(stage)

        elif test == "DIAG_UPDATE":
            ret = libmfg_utils.mtp_update_diag_image(mtp_mgmt_ctrl)

        elif test == "NIC_FW_UPDATE":
            ret = libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, libmfg_utils.mtp_get_sw_image_list(mtp_mgmt_ctrl, stage))

        elif test == "NIC_SW_IMG_UPDATE":
            ret = libmfg_utils.mtp_update_firmware(mtp_mgmt_ctrl, kwargs["nic_sw_img_file_list"])

        elif test == "FST_UPDATE":
            ret = libmfg_utils.mtp_update_fst_image(mtp_mgmt_ctrl)

        elif test == "DIAG_START":
            ret = mtp_mgmt_ctrl.mtp_diag_pre_init(start_dsp=False)

        elif test == "DSP_START":
            ret = mtp_mgmt_ctrl.mtp_diag_pre_init(start_dsp=True)

        elif test == "DIAG_POST":
            ret = mtp_mgmt_ctrl.mtp_diag_post_init()

        elif test == "MTP_SANITY_CHECK":
            ret = mtp_mgmt_ctrl.mtp_hw_init(stage)

        elif test == "I210_PRSNT_CHECK":
            ret = libmtp_utils.check_mtp_host_nic_presence(mtp_mgmt_ctrl)

        elif test == "I210_IMAGE_CHECK":
            ret = libmtp_utils.verify_img_mtp_host_nic(mtp_mgmt_ctrl)

        elif test == "MTP_ID":
            ret = mtp_mgmt_ctrl.mtp_sys_info_disp()

        elif test == "NIC_INIT":
            ret = mtp_mgmt_ctrl.mtp_nic_init(stage)

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

    if stage in (FF_Stage.FF_P2C, FF_Stage.FF_2C_L, FF_Stage.FF_2C_H):
        test_list.append("SANITY_CHECK_SETUP")
    if stage in (FF_Stage.FF_P2C, FF_Stage.FF_2C_L, FF_Stage.FF_2C_H):
        test_list.append("QSFP_SANITY_CHECK")
    if stage in (FF_Stage.FF_P2C, FF_Stage.FF_2C_L, FF_Stage.FF_2C_H):
        test_list.append("RJ45_SANITY_CHECK")
    return nic_common_setup_test_picker(mtp_mgmt_ctrl, stage, pass_nic_list, test_list, skip_test_list)

def nic_common_setup_test_picker(mtp_mgmt_ctrl, stage, pass_nic_list, test_list, skip_test_list):
    fail_nic_list = list()

    for test in test_list:
        if test in skip_test_list:
            continue

        start_ts = mtp_mgmt_ctrl.log_test_start(test)
        test_start_nic_log_message(mtp_mgmt_ctrl, pass_nic_list, stage, test)

        if test == "NIC_TYPE":
            test_fail_nic_list = mtp_mgmt_ctrl.mtp_nic_list_type_test(pass_nic_list)
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
                elif nic_type in GIGLIO_NIC_TYPE_LIST:
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

@semi_parallel_test_section
def test_start_nic_log_message(mtp_mgmt_ctrl, slot, stage, test):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_START.format(sn, stage, test))
    return True

@semi_parallel_test_section
def test_fail_nic_log_message(mtp_mgmt_ctrl, slot, stage, test, start_ts):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
    mtp_mgmt_ctrl.cli_log_slot_err(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, stage, test, "FAILED", duration))
    return True

@semi_parallel_test_section
def test_pass_nic_log_message(mtp_mgmt_ctrl, slot, stage, test, start_ts):
    sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, MTP_DIAG_Report.NIC_DIAG_TEST_PASS.format(sn, stage, test, duration))
    return True
