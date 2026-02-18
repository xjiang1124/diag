#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import traceback
sys.path.append("lib")
import libmfg_utils
import libmtp_utils
import test_utils
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libdefs import Swm_Test_Mode
from libmtp_ctrl import mtp_ctrl
from libmtp_db import mtp_db
from libdefs import FF_Stage
from libdefs import MTP_Const


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
    """
    Initilize mtp_ctrl object according actual config data

    Args:
        mtp_cfg_db (mtp_db): mtp configure mapping data
        mtp_id (string): mtp id
        test_log_filep (file object): mtp test log file handler
        diag_log_filep (file object): diag log file handler
        diag_nic_log_filep_list (file object): nic log file handler
        skip_slots (list, optional): slots to skip running test. Defaults to [].

    Returns:
        mtp_ctrl object: mtp controler for specified mtp id
    """

    mtp_cli_id_str = libmfg_utils.id_str(mtp=mtp_id)
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


def main(args):
    """
    Main entry 

    Args:
        args (argparse namespace): command line arguments

    Returns:
        boolean: test results
    """

    # print(args)
    # print((sys.argv))

    if args.subcommand == 'sdl':
        stage = FF_Stage.FF_DL
        args.testsuite_name = FF_Stage.SCAN_DL
    if args.subcommand == 'dl':
        stage = FF_Stage.FF_DL
        args.testsuite_name = stage
    if args.subcommand == 'predl':
        stage = FF_Stage.FF_DL
        args.testsuite_name = FF_Stage.SCAN_DL
    elif args.subcommand == '2c':
        # wait operator set chamber temperature
        if args.high_temp:
            libmfg_utils.cli_inf("CLOSE THE CHAMBER AND SET TEMPERATURE TO {:d} DEGREE CENTIGRADE\n".format(MTP_Const.MFG_EDVT_HIGH_TEMP))
            #libmfg_utils.action_confirm("SCAN *STOP* AFTER TEMPERATURE RISE TO {:d}".format(MTP_Const.MFG_EDVT_HIGH_TEMP), "STOP")
            stage = FF_Stage.FF_2C_H
        elif args.low_temp:
            libmfg_utils.cli_inf("CLOSE THE CHAMBER AND SET TEMPERATURE TO {:d} DEGREE CENTIGRADE\n".format(MTP_Const.MFG_EDVT_LOW_TEMP))
            #libmfg_utils.action_confirm("SCAN *STOP* AFTER TEMPERATURE DROP TO {:d}".format(MTP_Const.MFG_EDVT_LOW_TEMP), "STOP")
            stage = FF_Stage.FF_2C_L
        else:
            libmfg_utils.sys_exit("Unknown 2C Corner... Abort")
    elif args.subcommand == 'p2c':
        stage = FF_Stage.FF_P2C
        args.testsuite_name = stage
    elif args.subcommand == '4c':
        # wait operator set chamber temperature
        if args.high_temp:
            libmfg_utils.cli_inf("CLOSE THE CHAMBER AND SET TEMPERATURE TO {:d} DEGREE CENTIGRADE\n".format(MTP_Const.MFG_EDVT_HIGH_TEMP))
            # libmfg_utils.action_confirm("SCAN *STOP* TO START TEST", "STOP")
            stage = FF_Stage.FF_4C_H
        elif args.low_temp:
            libmfg_utils.cli_inf("CLOSE THE CHAMBER AND SET TEMPERATURE TO {:d} DEGREE CENTIGRADE\n".format(MTP_Const.MFG_EDVT_LOW_TEMP))
            # libmfg_utils.action_confirm("SCAN *STOP* TO START TEST", "STOP")
            stage = FF_Stage.FF_4C_L
        else:
            libmfg_utils.sys_exit("Unknown 4C Corner... Abort")
    elif args.subcommand == 'swi':
        stage = FF_Stage.FF_SWI
    elif args.subcommand == 'fst':
        stage = FF_Stage.FF_FST
    elif args.subcommand == 'ort':
        stage = FF_Stage.FF_ORT
    elif args.subcommand == 'rdt':
        stage = FF_Stage.FF_RDT
    elif args.subcommand == 'mtp':
        stage = FF_Stage.FF_SRN
    elif args.subcommand == 'cnic':
        stage = FF_Stage.FF_DL
        args.testsuite_name = FF_Stage.CONVERT
    elif args.subcommand == 'ddr':
        # Display test suite test cases
        test_suite = libmfg_utils.load_cfg_from_yaml_file_list([args.cfgyaml])
        libmfg_utils.cli_inf("Running TEST SUITE: {:s} With Following Test Case".format(test_suite["TEST_SUITE_NAME"]))
        for test_case in test_suite["TEST_CASE"]:
            libmfg_utils.cli_inf("Test Case: {:s} With {:d} Iterations".format(test_case["NAME"], test_case["ITER"]))
        # wait operator set chamber temperature
        if args.high_temp:
            libmfg_utils.cli_inf("RUNNING TEST WITH TEMPERATURE SET TO {:d} DEGREE CENTIGRADE\n".format(
                MTP_Const.MFG_EDVT_HIGH_TEMP))
            stage = FF_Stage.FF_2C_H
        elif args.low_temp:
            libmfg_utils.cli_inf("RUNNING TEST WITH TEMPERATURE SET TO TO {:d} DEGREE CENTIGRADE\n".format(
                MTP_Const.MFG_EDVT_LOW_TEMP))
            stage = FF_Stage.FF_2C_L
        else:
            libmfg_utils.cli_inf("RUNNING TEST WITH ROOM TEMPERATURE\n")
            stage = FF_Stage.FF_P2C
    elif args.subcommand == 'emmc':
        # Display EMMC test suite test cases
        ddr_suite = libmfg_utils.load_cfg_from_yaml_file_list([args.cfgyaml])
        libmfg_utils.cli_inf("Running TEST SUITE: {:s} With Following Test Case {:d} Iterations".format(
            ddr_suite["TEST_SUITE_NAME"], ddr_suite["ITER"]))
        for test_case in ddr_suite["TEST_CASE"]:
            libmfg_utils.cli_inf("Test Case: {:s}".format(test_case["NAME"]))
        # wait operator set chamber temperature
        if args.high_temp:
            libmfg_utils.cli_inf("RUNNING TEST WITH TEMPERATURE SET TO {:d} DEGREE CENTIGRADE\n".format(
                MTP_Const.MFG_EDVT_HIGH_TEMP))
            stage = FF_Stage.FF_2C_H
        elif args.low_temp:
            libmfg_utils.cli_inf("RUNNING TEST WITH TEMPERATURE SET TO TO {:d} DEGREE CENTIGRADE\n".format(
                MTP_Const.MFG_EDVT_LOW_TEMP))
            stage = FF_Stage.FF_2C_L
        else:
            libmfg_utils.cli_inf("RUNNING TEST WITH ROOM TEMPERATURE\n")
            stage = FF_Stage.FF_P2C
    elif args.subcommand == 'cpld':
        stage = FF_Stage.FF_P2C

        # Get New CPLD binary file list
        new_cpld_json_dict = libmtp_utils.load_cpld_info_json(args.cpldfile, args.verbosity)
        if not new_cpld_json_dict:
            libmfg_utils.cli_err("Failed to Load CPLD JSON file, abort...")
            return False
        new_cpld_files_path = libmtp_utils.generate_cpld_img_full_path_list(new_cpld_json_dict, args.verbosity)
        if not new_cpld_files_path:
            libmfg_utils.cli_err("Failed to Got CPLD Binary file name and path from JSON file, abort...")
            return False
        new_cpld_files = [os.path.basename(file) for file in new_cpld_files_path]

        # Copy New CPLD image files to the script running directory, since existing architecture will delivery these images to every MTP from this directory
        dest_dir = os.getcwd() + os.sep + "release"
        for src_file in new_cpld_files_path:
            try:
                rc = os.system("cp {:s} {:s}".format(src_file, dest_dir))
            except OSError as Err:
                libmfg_utils.cli_err(str(Err))
                libmfg_utils.cli_err("Copy {:s} to {:s} run into OSError Exceprion, abort...".format(src_file, dest_dir))
                return False
            else:
                if rc == 0:
                    if args.verbosity:
                        libmfg_utils.cli_inf("Copied {:s} to {:s}".format(src_file, dest_dir))
                else:
                    libmfg_utils.cli_err("Copy {:s} to {:s} run into CMD failed, abort...".format(src_file, dest_dir))

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

    fail_nic_list = dict()
    nic_sn_list = dict()
    invalid_nic_list = dict()

    # init mtp_ctrl list
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
    fail_nic_list[mtp_id] = list()
    nic_sn_list[mtp_id] = list()
    invalid_nic_list[mtp_id] = list()

    mfg_test_start_ts = libmfg_utils.timestamp_snapshot()

    mfg_test_summary = dict()
    mfg_test_summary[mtp_id] = list()
    skip_test = []
    if hasattr(args, 'skip_test'):
        skip_test = args.skip_test
    rc = test_utils.single_mtp_test(stage,
                                    mtp_mgmt_ctrl,
                                    mfg_test_summary[mtp_id],
                                    skip_test,
                                    skip_slots,
                                    **vars(args)
                                    )

    mfg_test_stop_ts = libmfg_utils.timestamp_snapshot()
    sub_com_disp_str = 'SCREEN' if args.subcommand == 'mtp' else args.subcommand.upper()
    libmfg_utils.cli_inf("MFG MTP {:s} Test Duration:{:s}".format(sub_com_disp_str, str(mfg_test_stop_ts - mfg_test_start_ts)))

    # dump the summary
    if args.subcommand == 'mtp':
        mtp_sn = mtp_mgmt_ctrl.get_mtp_sn()
        test_result = libmfg_utils.mfg_summary_srn_disp(FF_Stage.FF_SRN, mfg_test_summary, [], mtp_sn)
    else:
        test_result = libmfg_utils.mfg_summary_disp(stage, mfg_test_summary, [])

    # print return code for JobD to pick up
    if test_result:
        return True
    else:
        return False


def launch_remote_server_only_script(args):
    """
    trigger scripts utility only run from remote server
    """

    subcom_2script_name = {
        'cmtp' : 'mfg_convert_mtp.py',
        'msanityl' : 'mfg_loop_sanity_check_test.py',
        'mconn' : 'mfg_mtp_connect.py',
        'mpcl' : 'mfg_mtp_powercycle_loop.py',
        'mpc' : 'mfg_mtp_powercycle.py',
        'mpo' : 'mfg_mtp_poweroff.py',
        'mreload' : 'mfg_mtp_reload.py',
        'mrestore' : 'mfg_rma_restore.py',
        'msanity' : 'mtp_sanity_test.py',
        'pocp' : 'mfg_scan_dl_ocp_test.py',
    }

    if args.subcommand not in subcom_2script_name:
        print("Unspported sub command")
        return None

    test_cmd = ["python3"]
    mfg_util_script_path = 'mfg_util_script'
    test_cmd += [mfg_util_script_path + os.sep + subcom_2script_name[args.subcommand]]
    print(test_cmd)
    test_cmd_option = sys.argv[2:]

    test_cmd += test_cmd_option
    libmfg_utils.cli_inf("Calling Inner Layer Script .....")
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NIC Card and MTP Diagnostic Test Main Entry",
                                     epilog='''Examples: %(prog)s cpld --mtpid MTP-100\n          %(prog)s p2c --mtpid MTP-100 --skip_test SCAN_VERIFY''', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    subparsers = parser.add_subparsers(title="subcommands list", dest="subcommand",
                                       description="'%(prog)s {subcommand} -h or --help' for detail usage of specified subcommand", help='sub-command description')
    parser_sdl = subparsers.add_parser('sdl', help='Invoke NIC card Scan Download test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_cnic = subparsers.add_parser('cnic', help='Invoke Convert NIC card test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_dl = subparsers.add_parser('dl', help='Invoke NIC card Download test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_predl = subparsers.add_parser('predl', help='Invoke NIC card Pre Download test suite, Vulcano Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_2c = subparsers.add_parser('2c', help='Invoke NIC card 2 Coner test suite,', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_p2c = subparsers.add_parser('p2c', help='Invoke NIC card Pre 2 Coner test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_4c = subparsers.add_parser('4c', help='Invoke NIC card 4 Coner test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_swi = subparsers.add_parser('swi', help='Invoke NIC card SoftWare Installation test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_fst = subparsers.add_parser('fst', help='Invoke NIC card Final Stage Test test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_ort = subparsers.add_parser('ort', help='Invoke NIC card MFG Ongoing Reliability Test test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_rdt = subparsers.add_parser('rdt', help='Invoke NIC card MFG Reliability Demonstration Test test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_ddr = subparsers.add_parser('ddr', help='Invoke NIC card DDR Validation test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_emmc = subparsers.add_parser('emmc', help='Invoke NIC card EMMC Validation test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_cpld = subparsers.add_parser('cpld', help='Invoke NIC card CPLD Validation test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_mtp = subparsers.add_parser('mtp', help='Invoke MFG MTP SCREEN Test test suite', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_cmtp = subparsers.add_parser('cmtp', help='Invoke Convert MTP test suite; Lauch From Remote Server Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_mconn = subparsers.add_parser('mconn', help='Invoke Diag connect to MTP test suite; Lauch From Remote Server Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_mpc = subparsers.add_parser('mpc', help='Invoke Diag MTP Powercycle test suite; Lauch From Remote Server Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_mpcl = subparsers.add_parser('mpcl', help='Invoke Diag MTP Powercycle test suite in loop mode; Lauch From Remote Server Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_mpo = subparsers.add_parser('mpo', help='Invoke Diag MTP Poweroff test suite; Lauch From Remote Server Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_mreload = subparsers.add_parser('mreload', help='Invoke Diag MTP Reload test suite; Lauch From Remote Server Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_mrestore = subparsers.add_parser('mrestore', help='Invoke MTP Set NIC to Diag boot test suite; Lauch From Remote Server Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_msanity = subparsers.add_parser('msanity', help='Invoke MTP Sanity test suite; Lauch From Remote Server Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_msanityl = subparsers.add_parser('msanityl', help='Invoke MTP Sanity test suite loop mode; Lauch From Remote Server Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))
    parser_pocp = subparsers.add_parser('pocp', help='Invoke Program OCP test suite; Lauch From Remote Server Only', formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=200))

    # python3.10
    # subparsers = parser.add_subparsers(title="subcommands list", dest="subcommand", required=True, description="'%(prog)s {subcommand} -h or --help' for detail usage of specified subcommand", help='sub-command description')
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
    parser_ddr.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle by PDU, depends on '-no_pc' option, default to %(default)s ", type=int, required=False, default=1)
    parser_ddr.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_ddr.add_argument("--vmarg", "-vmarg", help="specify the vmargin, deduced from environment temperature(normal temperature => no voltage margin; low/high temperature => low and high voltage margin) if not specified",
                            nargs="*",  choices=["normal", "high", "low"], default=[])
    parser_ddr.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_ddr.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_ddr.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP before test; default to %(default)s", action='store_true', required=False, default=False)
    parser_ddr.add_argument("--cfgyaml", "-cfgyaml", help="Test case config file for DDR Validation test suite, default to %(default)s", default="./config/ddr_test_suite.yaml")
    parser_ddr.set_defaults(func=main)

    parser_emmc.add_argument("--verbosity", "-verbosity", help="Increase output verbosity", action='store_true')
    parser_emmc.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_emmc.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    group_emmc = parser_emmc.add_mutually_exclusive_group()
    group_emmc.add_argument("--high_temp", "-high_temp", help="high temperature environment with both low and high voltage margin", action='store_true')
    group_emmc.add_argument("--low_temp", "-low_temp", help="low temperature environment with both low and high voltage margin", action='store_true')
    parser_emmc.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_emmc.add_argument("--cfgyaml", "-cfgyaml", help="Test case config file for EMMC Validation test suite, default to %(default)s", default="./config/emmc_test_suite.yaml")
    parser_emmc.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_emmc.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP before test; default to %(default)s", action='store_true', required=False, default=False)
    parser_emmc.set_defaults(func=main)

    parser_cpld.add_argument("--verbosity", "-verbosity", help="Increase output verbosity", action='store_true', default=False)
    parser_cpld.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_cpld.add_argument("--cpldfile", "-cpldfile", help="Validation Target, The New CPLD Binary files information Json files, default to %(default)s",
                             default="config/latest_release_cpld_4validation.json")
    parser_cpld.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_cpld.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_cpld.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP before test; default to %(default)s", action='store_true', required=False, default=False)
    parser_cpld.set_defaults(func=main)

    parser_sdl.add_argument("--verbosity", "-verbosity", help="Increase output verbosity; default to %(default)s", action='store_true', default=False)
    parser_sdl.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_sdl.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_sdl.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_sdl.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_sdl.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_sdl.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_sdl.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP before test; default to %(default)s", action='store_true', required=False, default=False)
    parser_sdl.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle by PDU, depends on '-no_pc' option, default to %(default)s", type=int, required=False, default=1)
    parser_sdl.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="c", default=None)
    parser_sdl.add_argument('--proginterimg', '-proginterimg', action='store_true', default=False)
    parser_sdl.set_defaults(func=main)

    parser_dl.add_argument("--verbosity", "-verbosity", help="Increase output verbosity; default to %(default)s", action='store_true', default=False)
    parser_dl.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_dl.add_argument("--dpn", "-dpn", help="Supply Diagnostic Part Number, for QA/lab only...MFG should enter DPN through scanning", default=None)
    parser_dl.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_dl.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_dl.add_argument("--skip_slots", "-skip_slots", metavar=('1', '1 2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_dl.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_dl.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_dl.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP before test; default to %(default)s", action='store_true', required=False, default=False)
    parser_dl.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle by PDU, depends on '-no_pc' option, default to %(default)s", type=int, required=False, default=1)
    parser_dl.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_dl.set_defaults(func=main)

    parser_predl.add_argument("--verbosity", "-verbosity", help="Increase output verbosity; default to %(default)s", action='store_true', default=False)
    parser_predl.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_predl.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_predl.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP before test; default to %(default)s", action='store_true', required=False, default=False)
    parser_predl.set_defaults(func=main)

    parser_2c.add_argument("--high_temp", "-high_temp", help="high temperature environment", action='store_true')
    parser_2c.add_argument("--low_temp", "-low_temp", help="low temperature environment", action='store_true')
    parser_2c.add_argument("--verbosity", "-verbosity", help="Increase output verbosity", action='store_true')
    parser_2c.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_2c.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_2c.add_argument("--only_test", "-only_test", metavar=('testname1', 'testname2'), help="run particular tests only", nargs="*", default=[])
    parser_2c.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_2c.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_2c.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_2c.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_2c.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_2c.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_2c.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle by PDU, depends on '-no_pc' option, default to %(default)s", type=int, required=False, default=1)
    parser_2c.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP between iterations; default to %(default)s", action='store_true', required=False, default=False)
    parser_2c.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_2c.set_defaults(func=main)

    parser_p2c.add_argument("--verbosity", "-verbosity", help="Increase output verbosity; default to %(default)s", action='store_true', default=False)
    parser_p2c.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_p2c.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_p2c.add_argument("--only_test", "-only_test", metavar=('testname1', 'testname2'), help="run particular tests only", nargs="*", default=[])
    parser_p2c.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_p2c.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_p2c.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_p2c.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_p2c.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle by PDU, depends on '-no_pc' option, default to %(default)s", type=int, required=False, default=1)
    parser_p2c.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP between iterations; default to %(default)s", action='store_true', required=False, default=False)
    parser_p2c.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_p2c.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_p2c.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_p2c.set_defaults(func=main)

    parser_4c.add_argument("--high_temp", "-high_temp", help="high temperature environment", action='store_true')
    parser_4c.add_argument("--low_temp", "-low_temp", help="low temperature environment", action='store_true')
    parser_4c.add_argument("--verbosity", "-verbosity", help="Increase output verbosity", action='store_true')
    parser_4c.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_4c.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_4c.add_argument("--only_test", "-only_test", metavar=('testname1', 'testname2'), help="run particular tests only", nargs="*", default=[])
    parser_4c.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_4c.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_4c.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle by PDU, depends on '-no_pc' option, default to %(default)s", type=int, required=False, default=1)
    parser_4c.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP between iterations; default to %(default)s", action='store_true', required=False, default=False)
    parser_4c.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_4c.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_4c.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_4c.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_4c.add_argument("--stop_on_err", "-stop_on_err", help="Break out of test on failure; default to %(default)s", required=False, action='store_true', default=False)
    parser_4c.add_argument("--vmarg", "-vmarg", help="sspecify the vmargin in percentage to overwrite internal default, interal defined high and low will be used if not specified", nargs="*", default=[])
    parser_4c.set_defaults(func=main)

    parser_swi.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_swi.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_swi.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_swi.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP before test; default to %(default)s", action='store_true', required=False, default=False)
    parser_swi.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_swi.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_swi.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_swi.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_swi.add_argument("--sku", "-sku", help="Supply CTO SKU, for QA/lab only...MFG should enter SKU through scanning", default=None)
    parser_swi.set_defaults(func=main)

    parser_fst.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_fst.add_argument("--card_type", "-card_type", help="card type", type=str, default="general")
    parser_fst.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_fst.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_fst.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP before test; default to %(default)s", action='store_true', required=False, default=False)
    parser_fst.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_fst.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_fst.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_fst.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_fst.set_defaults(func=main)

    parser_ort.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_ort.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_ort.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_ort.add_argument("--only_test", "-only_test", metavar=('testname1', 'testname2'), help="run particular tests only", nargs="*", default=[])
    parser_ort.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_ort.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_ort.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_ort.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_ort.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_ort.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle by PDU, depends on '-no_pc' option, default to %(default)s", type=int, required=False, default=1)
    parser_ort.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_ort.set_defaults(func=main)

    parser_rdt.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_rdt.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_rdt.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_rdt.add_argument("--only_test", "-only_test", metavar=('testname1', 'testname2'), help="run particular tests only", nargs="*", default=[])
    parser_rdt.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_rdt.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_rdt.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_rdt.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_rdt.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_rdt.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle by PDU, depends on '-no_pc' option, default to %(default)s", type=int, required=False, default=1)
    parser_rdt.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_rdt.set_defaults(func=main)

    parser_mtp.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_mtp.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_mtp.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_mtp.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_mtp.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_mtp.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_mtp.add_argument("--no_pc", "-no_pc", help="Don't powercycle MTP before test; default to %(default)s", action='store_true', required=False, default=False)
    parser_mtp.add_argument("--mtp_type", "-mtp_type", help="specify the mtp type TURBO_ELBA or MATERA", nargs="?",  choices=["TURBO_ELBA", "MATERA", "PANAREA"], default="PANAREA", const="PANAREA")
    parser_mtp.add_argument("--l1_seq", "-l1_seq",  help="asic L1 run under sequence mode", action='store_true')
    parser_mtp.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_mtp.set_defaults(func=main)

    parser_cnic.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_cnic.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_cnic.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_cnic.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_cnic.add_argument("--skip_slots", "-skip_slots", metavar=('1', '2'), help="skip one or more particular slot", nargs="*", default=[])
    parser_cnic.add_argument("--mtpcfg", "-mtpcfg", help="JobD reserved MTP", default=None)
    parser_cnic.add_argument("--jobd_logdir", "--logdir", "-jobd_logdir", help="Store final log to different path for CI/CD", default=None)
    parser_cnic.add_argument("--iteration", "-iteration", help="Iteration to run with or without MTP power cycle by PDU, depends on '-no_pc' option, default to %(default)s", type=int, required=False, default=1)
    parser_cnic.add_argument("--run_from_remote", "-run_from_remote", help='kick in test test from MTP or remote server, default to %(default)s', action='store_true', default=True)
    parser_cnic.set_defaults(func=main)

    parser_cmtp.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_cmtp.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_cmtp.add_argument("-to", "--convert_to", help="Convert this MTP to ", choices=["ELBA", "CAPRI", "TURBO_ELBA"], required=True)
    parser_cmtp.set_defaults(func=launch_remote_server_only_script)

    parser_mconn.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_mconn.add_argument("--apc" "-apc", help="MTP is power down, need to power on apc first", action='store_true')
    parser_mconn.add_argument("--init", '-init', help="Init the diag environment", action='store_true')
    parser_mconn.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_mconn.set_defaults(func=launch_remote_server_only_script)

    parser_mpc.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_mpc.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_mpc.set_defaults(func=launch_remote_server_only_script)

    parser_mpcl.set_defaults(func=launch_remote_server_only_script)

    parser_mpo.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_mpo.set_defaults(func=launch_remote_server_only_script)

    parser_mreload.add_argument("--image", "-image", help="New MTP image file")
    parser_mreload.add_argument("--nic_image", "-nic_image", help="New NIC image file")
    parser_mreload.add_argument("--apc", "-apc", help="MTP is power down, need to power on apc first", action='store_true')
    parser_mreload.add_argument("--mtpid", "-mtpid", help="pre-select MTPs", nargs="*", default=[])
    parser_mreload.set_defaults(func=launch_remote_server_only_script)

    parser_mrestore.add_argument("--apc", "-apc", help="MTP is power down, need to power on apc first", action='store_true')
    parser_mrestore.set_defaults(func=launch_remote_server_only_script)

    parser_msanity.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_msanity.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_msanity.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_msanity.set_defaults(func=launch_remote_server_only_script)

    parser_msanityl.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_msanityl.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_msanityl.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_msanityl.add_argument("--mtpid", "-mtpid", help="pre-select MTP",  nargs="?", default=[])
    parser_msanityl.add_argument("--loop", "-loop", help="Step up loop time")
    parser_msanityl.set_defaults(func=launch_remote_server_only_script)

    parser_pocp.add_argument("--verbosity", "-verbosity", help="increase output verbosity", action='store_true')
    parser_pocp.add_argument("--swm", "-swm", type=Swm_Test_Mode, help="SWM test mode; default to %(default)s", choices=list(Swm_Test_Mode), default=Swm_Test_Mode.SW_DETECT)
    parser_pocp.add_argument("--skip_test", "-skip_test", metavar=('testname1', 'testname2'), help="skip a particular test or test sectio, e.g. SCAN_VERIFY", nargs="*", default=[])
    parser_pocp.set_defaults(func=launch_remote_server_only_script)

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)
        # parser.exit(status=1, message=parser.print_help())
    else:
        if not args.subcommand:
            parser.print_help()
            sys.exit(1)

    sys.exit(not args.func(args))
