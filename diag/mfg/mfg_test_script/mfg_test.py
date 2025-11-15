#!/usr/bin/env python3

import argparse
import sys
import os
import time
import subprocess
import traceback
sys.path.append("lib")
from libdefs import Swm_Test_Mode
import libmfg_utils
import testlog
import test_utils
from libmfg_cfg import *
from libdefs import MTP_Const
from libdefs import FF_Stage
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
import scanning

def load_mtp_cfg(cfg_yaml=None, subcommand=None):
    """
    Load MTP configuration yaml files.

    Args:
        cfg_yaml (string, optional): additional yaml file to load. Defaults to None.
        subcommand (string, optional): categorize necessary yaml file to load. Defaults to None, Means load all.

    Returns:
        mtp_db object: mtpid to configue data mapping
    """

    mtp_chassis_cfg_file_list = list()
    if subcommand:
        subcommand = subcommand.lower()
    if cfg_yaml:
        mtp_chassis_cfg_file_list.append(os.path.abspath(cfg_yaml))
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    if subcommand in ["sdl", "dl", "p2c"]:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
    elif subcommand in ['2c', '4c']:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
    elif subcommand == 'swi':
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/swi_mtp_chassis_cfg.yaml"))
    elif subcommand == 'fst':
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/fst_mtps_chassis_cfg.yaml"))
    elif subcommand == 'rdt':
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/rdt_mtp_chassis_cfg.yaml"))
    elif subcommand == 'ort':
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/ort_mtp_chassis_cfg.yaml"))
    else:
        print('Warning: Loading all possiable mtp chassis cfg file, there might have duplicated overwrite')
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/dl_p2c_mtp_chassis_cfg.yaml"))
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/4c_mtp_chassis_cfg.yaml"))
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/swi_mtp_chassis_cfg.yaml"))
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/fst_mtps_chassis_cfg.yaml"))
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/rdt_mtp_chassis_cfg.yaml"))
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/ort_mtp_chassis_cfg.yaml"))
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/mtp_screen_chassis_cfg.yaml"))
    
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db

def mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, skip_slots=[]):
    mtp_cli_id_str = libmfg_utils.id_str(mtp = mtp_id)
    mtp_mgmt_cfg = mtp_cfg_db.get_mtp_mgmt(mtp_id)
    if not mtp_mgmt_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find management config")
        return
    mtp_apc_cfg = mtp_cfg_db.get_mtp_apc(mtp_id)
    if not mtp_apc_cfg:
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to find apc config")
    if len(skip_slots) > 0 and not mtp_cfg_db.set_mtp_slots_to_skip(mtp_id, skip_slots):
        libmfg_utils.sys_exit(mtp_cli_id_str + "Unable to set skip slots")
    mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
    mtp_mgmt_ctrl = mtp_ctrl(mtp_id, test_log_filep, diag_log_filep, diag_nic_log_filep_list, mgmt_cfg=mtp_mgmt_cfg, apc_cfg=mtp_apc_cfg, slots_to_skip=mtp_slots_to_skip)
    return mtp_mgmt_ctrl

def common_args2_cmd_options_list(args):
    """
    covert local MTP args to list for subprocss
    """

    cmd_options = []
    try:
        for k, v in args.items():
            if k == 'func':
                continue
            if k == 'jobd_logdir':
                continue
            if k == 'mtpcfg':
                continue
            if k == 'run_from_redmote':
                continue
            if k == 'subcommand':
                continue
            if k == 'iteration':
                continue
            if k == 'loop_idx':
                if args["subcommand"] in ('2c', 'p2c', '4c', 'ort', 'rdt'):
                    #reuse iteration as loop index passdown to next layer
                    cmd_options.append('--iteration')
                    cmd_options.append(str(v))
            if isinstance(v, list):
                if v:
                    cmd_options.append('--'+ k)
                    cmd_options.append(' '.join(v))
                continue
            if isinstance(v, bool):
                if v:
                    cmd_options.append('--'+ k)
                continue
            cmd_options.append('--'+ k)
            cmd_options.append(str(v))
    except Exception as Err:
        print("handle args error")
        print(Err)

    return cmd_options

def main(args):

    libmfg_utils.cli_inf(str(args))
    print((sys.argv))
    print("under developmenmt")

def run_sdl_tests(args):
    """
    trigger the Scan Download script to run
    """

    mtpcfg_file = None
    test_cmd = ["python3", "./mtp_dl_test.py", '--scandl']
    test_cmd_option = sys.argv[2:]
    stage = FF_Stage.FF_DL
    libmfg_utils.cli_inf(str(args))

    mfg_test_start_ts = libmfg_utils.timestamp_snapshot()
    if not args.run_from_remote:
        if args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))

        scanning.mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, stage)
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove iteration option since mtp_dl_test.py does not have this option.
    if "--iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--iteration")] + test_cmd_option[test_cmd_option.index("--iteration")+2:]
    if "-iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-iteration")] + test_cmd_option[test_cmd_option.index("-iteration")+2:]
    # remove jobd_logdir option since mtp_dl_test.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))

    return exist_code

def run_convert_nic_tests(args):
    """
    trigger the Scan Download script to run
    """

    mtpcfg_file = None
    test_cmd = ["python3", "./nic_convert_test.py"]
    test_cmd_option = sys.argv[2:]
    stage = FF_Stage.FF_DL
    libmfg_utils.cli_inf(str(args))

    mfg_test_start_ts = libmfg_utils.timestamp_snapshot()
    if not args.run_from_remote:
        if args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))

        if not ENABLE_SCAN_VERIFY:
            if "SCAN_VERIFY" not in args.skip_test:
                args.skip_test.append("SCAN_VERIFY")
        if "SCAN_VERIFY" not in args.skip_test:
            scanning.mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, stage)
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove iteration option since mtp_dl_test.py does not have this option.
    if "--iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--iteration")] + test_cmd_option[test_cmd_option.index("--iteration")+2:]
    if "-iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-iteration")] + test_cmd_option[test_cmd_option.index("-iteration")+2:]
    # remove jobd_logdir option since mtp_dl_test.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))

    return exist_code

def run_dl_tests(args):
    """
    trigger the download script to run
    """

    # launching script from MTP
    test_cmd = ["python3", "./mtp_dl_test.py"]
    test_cmd_option = sys.argv[2:]
    stage = FF_Stage.FF_DL
    libmfg_utils.cli_inf(str(args))

    if not args.run_from_remote:
        mtpcfg_file = None

        if args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))

        if not ENABLE_SCAN_VERIFY:
            if "SCAN_VERIFY" not in args.skip_test:
                args.skip_test.append("SCAN_VERIFY")
        if "SCAN_VERIFY" not in args.skip_test:
            scanning.mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, stage)
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove iteration option since mtp_dl_test.py does not have this option.
    if "--iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--iteration")] + test_cmd_option[test_cmd_option.index("--iteration")+2:]
    if "-iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-iteration")] + test_cmd_option[test_cmd_option.index("-iteration")+2:]
    # remove jobd_logdir option since mtp_dl_test.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        exist_code = Err.returncode
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def run_2c_tests(args):
    """
    trigger 2c script to run
    """

    test_cmd = ["python3", "./mtp_diag_regression.py"]
    test_cmd_option = sys.argv[2:]

    # wait operator set chamber temperature
    if args.high_temp:
        stage = FF_Stage.FF_2C_H
    elif args.low_temp:
        stage = FF_Stage.FF_2C_L

    # launching script from MTP
    if not args.run_from_remote:
        mtpcfg_file = None

        if args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    libmfg_utils.cli_inf(str(args))
    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove low_temp/high_temp option since it converted to stage
    if "--low_temp" in test_cmd_option:
        test_cmd_option.remove("--low_temp")
    if "-low_temp" in test_cmd_option:
        test_cmd_option.remove("-low_temp")
    if "--high_temp" in test_cmd_option:
        test_cmd_option.remove("--high_temp")
    if "-high_temp" in test_cmd_option:
        test_cmd_option.remove("-high_temp")
    # remove iteration option since mtp_diag_regression.py does not have this option.
    if "--iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--iteration")] + test_cmd_option[test_cmd_option.index("--iteration")+2:]
    if "-iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-iteration")] + test_cmd_option[test_cmd_option.index("-iteration")+2:]
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    # re-use iteration option as loop_index for next layer
    test_cmd_option += ["--stage", str(stage), "--loop_idx", str(args.iteration)]
    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def run_p2c_tests(args):
    """
    trigger pre 2c script to run
    """

    test_cmd = ["python3", "./mtp_diag_regression.py"]
    test_cmd_option = sys.argv[2:]
    stage = FF_Stage.FF_P2C

    # launching script from MTP
    if not args.run_from_remote:
        mtpcfg_file = None

        if args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    libmfg_utils.cli_inf(str(args))
    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    # remove iteration option since mtp_diag_regression.py does not have this option.
    if "--iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--iteration")] + test_cmd_option[test_cmd_option.index("--iteration")+2:]
    if "-iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-iteration")] + test_cmd_option[test_cmd_option.index("-iteration")+2:]
    # re-use iteration option as loop_index for next layer
    test_cmd_option += ["--stage", str(stage), "--loop_idx", str(args.iteration)]
    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def run_4c_tests(args):
    """
    trigger 4c script to run
    """
    test_cmd = ["python3", "./mtp_diag_regression.py"]
    test_cmd_option = sys.argv[2:]
    if args.high_temp:
        stage = FF_Stage.FF_4C_H
    elif args.low_temp:
        stage = FF_Stage.FF_4C_L

    # launching script from MTP
    if not args.run_from_remote:
        mtpcfg_file = None

        if args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    libmfg_utils.cli_inf(str(args))
    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove low_temp/high_temp option since it converted to stage
    if "--low_temp" in test_cmd_option:
        test_cmd_option.remove("--low_temp")
    if "-low_temp" in test_cmd_option:
        test_cmd_option.remove("-low_temp")
    if "--high_temp" in test_cmd_option:
        test_cmd_option.remove("--high_temp")
    if "-high_temp" in test_cmd_option:
        test_cmd_option.remove("-high_temp")
    # remove iteration option since mtp_diag_regression.py does not have this option.
    if "--iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--iteration")] + test_cmd_option[test_cmd_option.index("--iteration")+2:]
    if "-iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-iteration")] + test_cmd_option[test_cmd_option.index("-iteration")+2:]
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    # re-use iteration option as loop_index for next layer
    test_cmd_option += ["--stage", str(stage), "--loop_idx", str(args.iteration)]
    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def run_swi_tests(args):
    """
    trigger SWI(Software Installation Script) to run
    """

    mtpcfg_file = None
    test_cmd = ["python3", "./mtp_swi_test.py"]
    test_cmd_option = sys.argv[2:]
    stage = FF_Stage.FF_SWI
    libmfg_utils.cli_inf(str(args))

    mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

    if args.mtpcfg:
        mtpcfg_file = "./config/" + os.path.relpath(args.mtpcfg)
        mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
    else:
        mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
    if args.mtpid:
        mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
        if not mtp_ids:
            sys.exit(1)
        mtp_id = mtp_ids[0]
    else:
        mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
        args.mtpid = mtp_id

    # init mtp_ctrl
    if args.verbosity:
        diag_log_filep = sys.stdout
        diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
    else:
        diag_log_filep = None
        diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
    mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)

    # running from remote
    if not args.run_from_remote:

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, run_from_mtp=False, stage=stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))

        if not ENABLE_SCAN_VERIFY:
            if "SCAN_VERIFY" not in args.skip_test:
                args.skip_test.append("SCAN_VERIFY")
        if "SCAN_VERIFY" not in args.skip_test:
            scanning.mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, stage)
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))

    return exist_code

def run_fst_tests(args):
    """
    trigger the Final Stage Test 
    """

    # launching script from MTP
    test_cmd = ["python3", "./mtp_fst_test.py"]
    test_cmd_option = sys.argv[2:]
    stage = FF_Stage.FF_FST
    libmfg_utils.cli_inf(str(args))

    if not args.run_from_remote:
        card_type = args.card_type.upper()
        mtpcfg_file = None

        if args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))

        if not ENABLE_SCAN_VERIFY:
            if "SCAN_VERIFY" not in args.skip_test:
                args.skip_test.append("SCAN_VERIFY")
        if "SCAN_VERIFY" not in args.skip_test:
            scanning.mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, stage)
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        exist_code = Err.returncode
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def run_ort_tests(args):
    """
    Triger ORT Test to run
    """

    test_cmd = ["python3", "./mtp_diag_regression.py"]
    test_cmd_option = sys.argv[2:]
    stage = FF_Stage.FF_ORT

    # launching script from MTP
    if not args.run_from_remote:
        mtpcfg_file = None

        if args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    libmfg_utils.cli_inf(str(args))
    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    # remove iteration option since mtp_diag_regression.py does not have this option.
    if "--iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--iteration")] + test_cmd_option[test_cmd_option.index("--iteration")+2:]
    if "-iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-iteration")] + test_cmd_option[test_cmd_option.index("-iteration")+2:]
    # re-use iteration option as loop_index for next layer
    test_cmd_option += ["--stage", str(stage), "--loop_idx", str(args.iteration)]
    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def run_rdt_tests(args):
    """
    Triger RDT Test to run
    """

    test_cmd = ["python3", "./mtp_diag_regression.py"]
    test_cmd_option = sys.argv[2:]
    stage = FF_Stage.FF_RDT

    # launching script from MTP
    if not args.run_from_remote:
        mtpcfg_file = None

        if args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=args.skip_slots)
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    libmfg_utils.cli_inf(str(args))
    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    # remove iteration option since mtp_diag_regression.py does not have this option.
    if "--iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--iteration")] + test_cmd_option[test_cmd_option.index("--iteration")+2:]
    if "-iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-iteration")] + test_cmd_option[test_cmd_option.index("-iteration")+2:]
    # re-use iteration option as loop_index for next layer
    test_cmd_option += ["--stage", str(stage), "--loop_idx", str(args.iteration)]
    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def run_mtp_screening_tests(args):
    """
    Triger MTP Screening Test to run
    """

    test_cmd = ["python3", "./mtp_screen_regression.py"]
    test_cmd_option = sys.argv[2:]
    stage = FF_Stage.FF_SRN

    # launching script from MTP
    if not args.run_from_remote:
        mtpcfg_file = None

        if args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        skip_slots = []
        if hasattr(args, 'skip_slots'):
            skip_slots = args.skip_slots
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=skip_slots)
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))

        if not args.mtpsn:
            mtp_mgmt_ctrl.cli_log_inf("Start the Barcode Scan Process", level=0)
            while True:
                scan_rslt = mtp_mgmt_ctrl.mtp_screen_barcode_scan()
                if scan_rslt and scan_rslt["VALID"]:
                    mtp_mgmt_ctrl.cli_log_inf("Scan validate MTP SN", level=0)
                    break
                mtp_mgmt_ctrl.cli_log_inf("Restart the Barcode Scan Process", level=0)
            mtp_mgmt_ctrl.set_mtp_sn(scan_rslt["MTP_SN"].strip())
            mtp_mgmt_ctrl.set_mtp_mac(scan_rslt["MTP_MAC"].strip())
            args.mtpsn = mtp_mgmt_ctrl.get_mtp_sn()
            args.mtpmac = mtp_mgmt_ctrl.get_mtp_mac()

        test_cmd_option = common_args2_cmd_options_list(vars(args))

    libmfg_utils.cli_inf(str(args))
    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def run_emmc_validation_tests(args):
    """
    trigger emmc validation script to run
    """

    test_cmd = ["python3", "./diag_screening_emmc.py"]
    test_cmd_option = sys.argv[2:]
    if args.high_temp:
        stage = FF_Stage.FF_2C_H
    elif args.low_temp:
        stage = FF_Stage.FF_2C_L
    else:
        stage = FF_Stage.FF_P2C

    # launching script from MTP
    if not args.run_from_remote:
        # Display test suite test cases
        ddr_suite = libmfg_utils.load_cfg_from_yaml_file_list([args.cfgyaml])
        libmfg_utils.cli_inf("Running TEST SUITE: {:s} With Following Test Case {:d} Iterations".format(
            ddr_suite["TEST_SUITE_NAME"], ddr_suite["ITER"]))
        for test_case in ddr_suite["TEST_CASE"]:
            libmfg_utils.cli_inf("Test Case: {:s}".format(test_case["NAME"]))

        mtpcfg_file = None

        if hasattr(args, 'mtpcfg') and args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=[])
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    libmfg_utils.cli_inf(str(args))
    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove low_temp/high_temp option since it converted to stage
    if "--low_temp" in test_cmd_option:
        test_cmd_option.remove("--low_temp")
    if "-low_temp" in test_cmd_option:
        test_cmd_option.remove("-low_temp")
    if "--high_temp" in test_cmd_option:
        test_cmd_option.remove("--high_temp")
    if "-high_temp" in test_cmd_option:
        test_cmd_option.remove("-high_temp")
    # remove iteration option since mtp_diag_regression.py does not have this option.
    if "--iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--iteration")] + test_cmd_option[test_cmd_option.index("--iteration")+2:]
    if "-iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-iteration")] + test_cmd_option[test_cmd_option.index("-iteration")+2:]
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    test_cmd_option += ["--stage", str(stage)]
    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def run_ddr_validation_tests(args):
    """
    trigger ddr validation script to run
    """

    test_cmd = ["python3", "./diag_screening_ddr.py"]
    test_cmd_option = sys.argv[2:]
    if args.high_temp:
        stage = FF_Stage.FF_2C_H
    elif args.low_temp:
        stage = FF_Stage.FF_2C_L
    else:
        stage = FF_Stage.FF_P2C

    # launching script from MTP
    if not args.run_from_remote:
        # Display test suite test cases
        test_suite = libmfg_utils.load_cfg_from_yaml_file_list([args.cfgyaml])
        libmfg_utils.cli_inf("Running TEST SUITE: {:s} With Following Test Case".format(test_suite["TEST_SUITE_NAME"]))
        for test_case in test_suite["TEST_CASE"]:
            libmfg_utils.cli_inf("Test Case: {:s} With {:d} Iterations".format(test_case["NAME"], test_case["ITER"]))

        mtpcfg_file = None

        if hasattr(args, 'mtpcfg') and args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=[])
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    libmfg_utils.cli_inf(str(args))
    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove low_temp/high_temp option since it converted to stage
    if "--low_temp" in test_cmd_option:
        test_cmd_option.remove("--low_temp")
    if "-low_temp" in test_cmd_option:
        test_cmd_option.remove("-low_temp")
    if "--high_temp" in test_cmd_option:
        test_cmd_option.remove("--high_temp")
    if "-high_temp" in test_cmd_option:
        test_cmd_option.remove("-high_temp")
    # remove iteration option since mtp_diag_regression.py does not have this option.
    if "--iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--iteration")] + test_cmd_option[test_cmd_option.index("--iteration")+2:]
    if "-iteration" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-iteration")] + test_cmd_option[test_cmd_option.index("-iteration")+2:]
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    test_cmd_option += ["--stage", str(stage)]
    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def run_cpld_validation_tests(args):
    """
    trigger cpld validation script to run
    """

    test_cmd = ["python3", "./diag_screening_cpld.py"]
    test_cmd_option = sys.argv[2:]
    stage = FF_Stage.FF_P2C

    # launching script from MTP
    if not args.run_from_remote:
        mtpcfg_file = None

        if hasattr(args, 'mtpcfg') and args.mtpcfg:
            mtpcfg_file = os.path.relpath(args.mtpcfg)
            mtp_cfg_db = load_mtp_cfg(mtpcfg_file, subcommand=args.subcommand)
        else:
            mtp_cfg_db = load_mtp_cfg(subcommand=args.subcommand)
        if args.mtpid:
            mtp_ids = libmfg_utils.mtpid_list_select(mtp_cfg_db, [args.mtpid])
            if not mtp_ids:
                sys.exit(1)
            mtp_id = mtp_ids[0]
        else:
            mtp_id = libmfg_utils.mtpid_list_select(mtp_cfg_db, args.mtpid)[0]
            args.mtpid = mtp_id

        # init mtp_ctrl
        if args.verbosity:
            diag_log_filep = sys.stdout
            diag_nic_log_filep_list = [sys.stdout] * MTP_Const.MTP_SLOT_NUM
        else:
            diag_log_filep = None
            diag_nic_log_filep_list = [None] * MTP_Const.MTP_SLOT_NUM
        mtp_mgmt_ctrl = mtp_mgmt_ctrl_init(mtp_cfg_db, mtp_id, None, diag_log_filep, diag_nic_log_filep_list, skip_slots=[])
        mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

        logfile_path, open_file_track_list = testlog.open_logfiles(mtp_mgmt_ctrl, False, stage)
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log will be in in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        test_cmd_option = common_args2_cmd_options_list(vars(args))

    libmfg_utils.cli_inf(str(args))
    # test_cmd = [os.path.basename(sys.argv[0])]
    # remove log-server command line option
    if "--run_from_remote" in test_cmd_option:
        test_cmd_option.remove("--run_from_remote")
    if "-run_from_remote" in test_cmd_option:
        test_cmd_option.remove("-run_from_remote")
    # remove jobd_logdir option since mtp_diag_regression.py does not have this option.
    if "--jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("--jobd_logdir")] + test_cmd_option[test_cmd_option.index("--jobd_logdir")+2:]
    if "-jobd_logdir" in test_cmd_option:
        test_cmd_option = test_cmd_option[:test_cmd_option.index("-jobd_logdir")] + test_cmd_option[test_cmd_option.index("-jobd_logdir")+2:]

    test_cmd_option += ["--stage", str(stage)]
    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Re-assembly command line arguments, and calling Inner Layer Script .....")
    libmfg_utils.cli_inf(str(" ".join(test_cmd)))

    try:
        com_proc = subprocess.run(test_cmd, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as Err:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Failed with exit code:{:s}".format(args.subcommand.upper(), str(Err.returncode)))
        err_msg = traceback.format_exc()
        print("-*"*50)
        print(Err.output)
        print("-*"*50)
        print(err_msg)
        exist_code = Err.returncode
    else:
        libmfg_utils.cli_inf("MFG MTP {:s} Test Passed with exit code:{:s}".format(args.subcommand.upper(), str(com_proc.returncode)))
        exist_code = com_proc.returncode

    if not args.run_from_remote:
        mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
        libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(args.subcommand.upper(), str(mfg_test_stop_ts - mfg_test_start_ts)))
        libmfg_utils.cli_inf("MFG MTP {:s} Test Log in ./{:s} To Copy Out ".format(args.subcommand.upper(), logfile_path))
        # upload test log to remote log server
        # under development

    return exist_code

def mtp_validation(args):
    libmfg_utils.cli_inf(str(args))
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NIC Card and MTP Diagnostic Test Main Entry", epilog='''Examples: %(prog)s cpld --mtpid MTP-100\n          %(prog)s p2c --mtpid MTP-100 --skip_test SCAN_VERIFY''', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    subparsers = parser.add_subparsers(title="subcommands list", dest="subcommand", description="'%(prog)s {subcommand} -h or --help' for detail usage of specified subcommand", help='sub-command description')
    parser_sdl = subparsers.add_parser('sdl', help='Invoke NIC card Scan Download test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_cnic = subparsers.add_parser('cnic', help='Invoke Convert NIC card test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_dl = subparsers.add_parser('dl', help='Invoke NIC card Download test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_2c = subparsers.add_parser('2c', help='Invoke NIC card 2 Coner test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_p2c = subparsers.add_parser('p2c', help='Invoke NIC card Pre 2 Coner test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_4c = subparsers.add_parser('4c', help='Invoke NIC card 4 Coner test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_swi = subparsers.add_parser('swi', help='Invoke NIC card SoftWare Installation test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_fst = subparsers.add_parser('fst', help='Invoke NIC card Final Stage Test test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_ort = subparsers.add_parser('ort', help='Invoke NIC card MFG Ongoing Reliability Test test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_rdt = subparsers.add_parser('rdt', help='Invoke NIC card MFG Reliability Demonstration Test test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_ddr = subparsers.add_parser('ddr', help='Invoke NIC card DDR Validation test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_emmc = subparsers.add_parser('emmc', help='Invoke NIC card EMMC Validation test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_cpld = subparsers.add_parser('cpld', help='Invoke NIC card CPLD Validation test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_mtp = subparsers.add_parser('mtp', help='Invoke MTP Iteself Validation test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))

    #python3.10 
    #subparsers = parser.add_subparsers(title="subcommands list", dest="subcommand", required=True, description="'%(prog)s {subcommand} -h or --help' for detail usage of specified subcommand", help='sub-command description')
    # parser_sdl = subparsers.add_parser('sdl', aliases=["SDL", "Sdl"], help='Invoke NIC card Scan Download test suite')
    # parser_dl = subparsers.add_parser('dl', aliases=["DL", "Dl"], help='Invoke NIC card Download test suite')
    # parser_2c = subparsers.add_parser('2c', aliases=["2C"], help='Invoke NIC card 2 Coner test suite')
    # parser_p2c = subparsers.add_parser('p2c', aliases=["P2C", "P2c"], help='Invoke NIC card Pre 2 Coner test suite')
    # parser_4c = subparsers.add_parser('4c', aliases=["4C"], help='Invoke NIC card 4 Coner test suite')
    # parser_swi = subparsers.add_parser('swi', aliases=["SWI", "Swi"], help='Invoke NIC card SoftWare Installation test suite')
    # parser_fst = subparsers.add_parser('fst', aliases=["FST", "Fst"], help='Invoke NIC card Final Stage Test test suite')
    # parser_ort = subparsers.add_parser('ort', aliases=["ORT", "Ort"], help='Invoke NIC card MFG Ongoing Reliability Test test suite')
    # parser_rdt = subparsers.add_parser('rdt', aliases=["RDT", "Rdt"], help='Invoke NIC card MFG Reliability Demonstration Test test suite')
    # parser_ddr = subparsers.add_parser('ddr', aliases=["DDR", "Ddr"], help='Invoke NIC card DDR Validation test suite')
    # parser_emmc = subparsers.add_parser('emmc', aliases=["EMMC", "Emmc"], help='Invoke NIC card EMMC Validation test suite')
    # parser_cpld = subparsers.add_parser('cpld', aliases=["CPLD", "Cpld"], help='Invoke NIC card CPLD Validation test suite')
    # parser_mtp = subparsers.add_parser('mtp', aliases=["MTP", "Mtp"], help='Invoke MTP Iteself Validation test suite')

    parser_ddr.add_argument("--verbosity", "-verbosity", help="Increase output verbosity", action='store_true')
    parser_ddr.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_ddr.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_ddr.add_argument("--high_temp", "-high_temp", help="high temperature environment", action='store_true')
    parser_ddr.add_argument("--low_temp", "-low_temp", help="low temperature environment", action='store_true')
    parser_ddr.add_argument("--iteration", "--NthIteration", "-iteration", "-NthIteration", help="The Index(Nth Iteration), Some Test may define parameter according the index. E.g. Snake, odd Ite use extrernal loopback, even Ite use internal loopback", type=int, required=False, default=1)
    parser_ddr.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_ddr.add_argument("--vmarg", "-vmarg", help="specify the vmargin, deduced from environment temperature(normal temperature => no voltage margin; low/high temperature => low and high voltage margin) if not specified", nargs="*",  choices=["normal", "high", "low"], default=[])
    parser_ddr.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_ddr.add_argument("--cfgyaml", "-cfgyaml", help="Test case config file for DDR Validation test suite, default to %(default)s", default="./config/ddr_test_suite.yaml")
    parser_ddr.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_ddr.set_defaults(func=run_ddr_validation_tests)

    parser_emmc.add_argument("--verbosity", "-verbosity", help="Increase output verbosity", action='store_true')
    parser_emmc.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_emmc.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    group_emmc = parser_emmc.add_mutually_exclusive_group()
    group_emmc.add_argument("--high_temp", "-high_temp", help="high temperature environment with both low and high voltage margin", action='store_true')
    group_emmc.add_argument("--low_temp", "-low_temp", help="low temperature environment with both low and high voltage margin", action='store_true')
    parser_emmc.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_emmc.add_argument("--cfgyaml", "-cfgyaml", help="Test case config file for EMMC Validation test suite, default to %(default)s", default="./config/emmc_test_suite.yaml")
    parser_emmc.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_emmc.set_defaults(func=run_emmc_validation_tests)

    parser_cpld.add_argument("--verbosity", "-verbosity", help="Increase output verbosity", action='store_true', default=False)
    parser_cpld.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_cpld.add_argument( "--cpldfile", "-cpldfile", help="Validation Target, The New CPLD Binary files information Json files, default to %(default)s", default="config/latest_release_cpld_4validation.json")
    parser_cpld.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_cpld.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_cpld.set_defaults(func=run_cpld_validation_tests)

    parser_sdl.add_argument("--verbosity", "-verbosity", help="Increase output verbosity; default to %(default)s", action='store_true', default=False)
    parser_sdl.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_sdl.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_sdl.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_sdl.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_sdl.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_sdl.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_sdl.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    # parser_sdl.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP between iterations; default to %(default)s", action='store_true', required=False, default=False)
    parser_sdl.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle", type=int, required=False, default=1)
    parser_sdl.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="c", default=None)
    parser_sdl.set_defaults(func=run_sdl_tests)

    parser_dl.add_argument("--verbosity", "-verbosity", help="Increase output verbosity; default to %(default)s", action='store_true', default=False)
    parser_dl.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_dl.add_argument("--dpn", "-dpn", help="Supply Diagnostic Part Number, for QA/lab only...MFG should enter DPN through scanning", default=None)
    parser_dl.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_dl.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_dl.add_argument("--skip_slots", "-skip_slots", metavar=('1', '1 2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_dl.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_dl.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_dl.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    # parser_dl.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP between iterations; default to %(default)s", action='store_true', required=False, default=False)
    parser_dl.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle", type=int, required=False, default=1)
    parser_dl.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_dl.set_defaults(func=run_dl_tests)

    parser_2c.add_argument("--high_temp", "-high_temp", help="high temperature environment", action='store_true')
    parser_2c.add_argument("--low_temp", "-low_temp", help="low temperature environment", action='store_true')
    parser_2c.add_argument("--verbosity", "-verbosity", help="Increase output verbosity", action='store_true')
    parser_2c.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_2c.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_2c.add_argument("--only_test", "-only_test", metavar=('testname1', 'testname2'), help="run particular tests only", nargs="*", default=[])
    parser_2c.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_2c.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_2c.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_2c.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_2c.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_2c.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_2c.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_2c.add_argument("--iteration", "--NthIteration", "-iteration", "-NthIteration", help="The Index(Nth Iteration), Some Test may define parameter according the index. E.g. Snake, odd Ite use extrernal loopback, even Ite use internal loopback", type=int, required=False, default=1)
    #parser_2c.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP between iterations; default to %(default)s", action='store_true', required=False, default=False)
    parser_2c.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_2c.set_defaults(func=run_2c_tests)

    parser_p2c.add_argument("--verbosity", "-verbosity", help="Increase output verbosity; default to %(default)s", action='store_true', default=False)
    parser_p2c.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_p2c.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_p2c.add_argument("--only_test", "-only_test", metavar=('testname1', 'testname2'), help="run particular tests only", nargs="*", default=[])
    parser_p2c.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_p2c.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_p2c.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_p2c.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_p2c.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_p2c.add_argument("--iteration", "--NthIteration", "-iteration", "-NthIteration", help="The Index(Nth Iteration), Some Test may define parameter according the index. E.g. Snake, odd Ite use extrernal loopback, even Ite use internal loopback", type=int, required=False, default=1)
    #parser_p2c.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP between iterations; default to %(default)s", action='store_true', required=False, default=False)
    parser_p2c.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_p2c.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_p2c.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_p2c.set_defaults(func=run_p2c_tests)

    parser_4c.add_argument("--high_temp", "-high_temp", help="high temperature environment", action='store_true')
    parser_4c.add_argument("--low_temp", "-low_temp", help="low temperature environment", action='store_true')
    parser_4c.add_argument("--verbosity", "-verbosity", help="Increase output verbosity", action='store_true')
    parser_4c.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_4c.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_4c.add_argument("--only_test", "-only_test", metavar=('testname1', 'testname2'), help="run particular tests only", nargs="*", default=[])
    parser_4c.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_4c.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_4c.add_argument("--iteration", "--NthIteration", "-iteration", "-NthIteration", help="The Index(Nth Iteration), Some Test may define parameter according the index. E.g. Snake, odd Ite use extrernal loopback, even Ite use internal loopback", type=int, required=False, default=1)
    # parser_4c.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP between iterations; default to %(default)s", action='store_true', required=False, default=False)
    parser_4c.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_4c.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_4c.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_4c.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_4c.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_4c.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_4c.set_defaults(func=run_4c_tests)

    parser_swi.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_swi.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_swi.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_swi.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_swi.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_swi.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_swi.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_swi.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_swi.add_argument("--sku", "-sku", help="Supply CTO SKU, for QA/lab only...MFG should enter SKU through scanning", default=None)
    parser_swi.set_defaults(func=run_swi_tests)

    parser_fst.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_fst.add_argument("--card_type", "-card_type", help="card type", type=str, default="general")
    parser_fst.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_fst.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_fst.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_fst.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_fst.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_fst.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_fst.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_fst.set_defaults(func=run_fst_tests)

    parser_ort.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_ort.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_ort.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_ort.add_argument("--only_test", "-only_test", metavar=('testname1', 'testname2'), help="run particular tests only", nargs="*", default=[])
    parser_ort.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_ort.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_ort.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_ort.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_ort.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_ort.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_ort.add_argument("--iteration", "--NthIteration", "-iteration", "-NthIteration", help="The Index(Nth Iteration), Some Test may define parameter according the index. E.g. Snake, odd Ite use extrernal loopback, even Ite use internal loopback", type=int, required=False, default=1)
    parser_ort.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_ort.set_defaults(func=run_ort_tests)

    parser_rdt.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_rdt.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_rdt.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_rdt.add_argument("--only_test", "-only_test", metavar=('testname1', 'testname2'), help="run particular tests only", nargs="*", default=[])
    parser_rdt.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_rdt.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_rdt.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_rdt.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_rdt.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_rdt.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_rdt.add_argument("--iteration", "--NthIteration", "-iteration", "-NthIteration", help="The Index(Nth Iteration), Some Test may define parameter according the index. E.g. Snake, odd Ite use extrernal loopback, even Ite use internal loopback", type=int, required=False, default=1)
    parser_rdt.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_rdt.set_defaults(func=run_rdt_tests)

    parser_mtp.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_mtp.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_mtp.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_mtp.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_mtp.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_mtp.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_mtp.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_mtp.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_mtp.add_argument("--mtp_type", "-mtp_type", help="specify the mtp type TURBO_ELBA or MATERA", nargs="?", choices=["TURBO_ELBA", "MATERA", "PANAREA"], default="PANAREA", const="PANAREA")
    parser_mtp.add_argument("--mtpsn", "-mtpsn",  help="MTP SN, like FLM0021330001, etc", default=None)
    parser_mtp.add_argument("--mtpmac", help="MTP MAC, like BBBBBBBBBBAF, etc", default=None)
    parser_mtp.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_mtp.set_defaults(func=run_mtp_screening_tests)

    parser_cnic.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_cnic.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_cnic.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_cnic.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_cnic.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_cnic.add_argument("--fail_slots", help="consider these slots failed", nargs="*", default=[])
    parser_cnic.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_cnic.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_cnic.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle, default to %(default)s", type=int, required=False, default=1)
    parser_cnic.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=False)
    parser_cnic.set_defaults(func=run_convert_nic_tests)

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)
        #parser.exit(status=1, message=parser.print_help())
    else:
        if not args.subcommand:
            parser.print_help()
            sys.exit(1)

    sys.exit(args.func(args))

