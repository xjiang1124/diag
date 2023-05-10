import sys, os, re
import time

sys.path.append(os.path.relpath("../../lib"))
import libtest_config

param_cfg = libtest_config.parse_config("lib/tests/fpga/parameters.yaml")
fpgautil_path = "/home/admin/eeupdate/"
file_store_path = "/home/admin/"

def fpga_init(test_ctrl):
    """
        fpgautil r32 0 0
        fpgautil r32 0 4
        fpgautil r32 0 8
        fpgautil r32 1 0
        fpgautil r32 1 4
        fpgautil r32 1 8
    """
    devices = [
        "fpga 0",
        "fpga 1"
    ]

    version_re  = "= ?(0x[A-Fa-f0-9]{4}([A-Fa-f0-9]{4}))"
    date_re     = "= ?(0x([A-Fa-f0-9]{4}[A-Fa-f0-9]{4}))"
    time_re     = "= ?(0x[A-Fa-f0-9]{4}([A-Fa-f0-9]{4}))"

    ret = True
    test_ctrl.mtp._fpga_ver = dict()
    test_ctrl.mtp._fpga_dat = dict()

    for device in devices:
        device_num = device.split(" ")[1].strip()

        ## VERSION
        cmd = "{:s}fpgautil r32 {:s} 0".format(fpgautil_path, device_num)
        if not fpgautil_cmd(test_ctrl, cmd, timeout=100):
            test_ctrl.cli_log_err("{:s} command failed".format(cmd))
            return False
        cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
        uc_match = re.search(version_re, cmd_buf)
        if uc_match:
            test_ctrl.mtp._fpga_ver[device] = uc_match.group(2)
        else:
            test_ctrl.cli_log_err("Failed to read {:s} version".format(device))
            ret = False
            continue

        ## DATE
        cmd = "{:s}fpgautil r32 {:s} 4".format(fpgautil_path, device_num)
        if not fpgautil_cmd(test_ctrl, cmd, timeout=100):
            test_ctrl.cli_log_err("{:s} command failed".format(cmd))
            return False
        cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
        uc_match = re.search(date_re, cmd_buf)
        if uc_match:
            test_ctrl.mtp._fpga_dat[device] = uc_match.group(2)
        else:
            test_ctrl.cli_log_err("Failed to read {:s} date timestamp".format(device))
            ret = False
            continue

        ## TIME
        cmd = "{:s}fpgautil r32 {:s} 8".format(fpgautil_path, device_num)
        if not fpgautil_cmd(test_ctrl, cmd, timeout=100):
            test_ctrl.cli_log_err("{:s} command failed".format(cmd))
            return False
        cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
        uc_match = re.search(time_re, cmd_buf)
        if uc_match:
            test_ctrl.mtp._fpga_dat[device] += "-" + uc_match.group(2)
        else:
            test_ctrl.cli_log_err("Failed to read {:s} timestamp".format(device))
            ret = False
            continue

    return ret


def fpga_verify(test_ctrl, test_config, silently=False):
    """
        if EITHER fpga version is incorrect, this returns False to update both
    """
    if not fpga_init(test_ctrl):
        return False

        # device,  expected version,         expected timestamp,         got version,                     got timestamp
    tbl = {
        "FPGA 0": (test_config["fpga0_ver"], test_config["fpga0_dat"], test_ctrl.mtp._fpga_ver["fpga 0"], test_ctrl.mtp._fpga_dat["fpga 0"]),
        "FPGA 1": (test_config["fpga1_ver"], test_config["fpga1_dat"], test_ctrl.mtp._fpga_ver["fpga 1"], test_ctrl.mtp._fpga_dat["fpga 1"])
    }

    for device in tbl.keys():
        exp_ver, exp_dat, got_ver, got_dat = tbl[device]
        if got_dat != exp_dat:
            if not silently:
                test_ctrl.cli_log_err("Incorrect {:s} timestamp: {:s}, expect: {:s}".format(device, got_dat, exp_dat), level=0)
            return False
        if got_ver != exp_ver:
            if not silently:
                test_ctrl.cli_log_err("Incorrect {:s} version: {:s}, expect: {:s}".format(device, got_ver, exp_ver), level=0)
            return False

    return True


def fpga_prog(test_ctrl, test_config):
    """
        ./fpgautil flash 0 program primary f0_img.bin
        ./fpgautil flash 0 verify primary f0_img.bin
        ./fpgautil flash 0 program secondary f0_img.bin
        ./fpgautil flash 0 verify secondary f0_img.bin
        ./fpgautil flash 1 program primary f1_img.bin
        ./fpgautil flash 1 verify primary f1_img.bin
        ./fpgautil flash 1 program secondary f1_img.bin
        ./fpgautil flash 1 verify secondary f1_img.bin
    """

    if not param_cfg["FORCE_UPDATE_FPGA"] and fpga_verify(test_ctrl, test_config, silently=True):
        test_ctrl.cli_log_inf("FPGAs already up-to-date", level=0)
        return True

    fpga_img_file = {
        "0": test_config["fpga0_img"],
        "1": test_config["fpga1_img"]
    }
    for fpga in fpga_img_file.keys():

        fpga_img = fpga_img_file[fpga]
        test_ctrl.cli_log_inf("Downloading FPGA {:s} image".format(fpga))
        if not test_ctrl.mtp.copy_file_to_mtp("release/"+fpga_img, file_store_path):
            # test_ctrl.cli_log_err("Unable to get {:s}".format(os.path.basename(fpga_img)), level=0)
            return False

        if "-dual-" in fpga_img:
            partitions = ("allflash")
        else:
            partitions = ("primary", "secondary")

        for partition in partitions:
            for task in ("program", "verify"):
                test_ctrl.cli_log_inf("{:s}ing FPGA {:s} {:s}".format(task.capitalize(), fpga, partition))
                cmd = "{:s}fpgautil flash {:s} {:s} {:s} {:s}/{:s}".format(fpgautil_path, fpga, task, partition, file_store_path, os.path.basename(fpga_img))
                if not fpgautil_cmd(test_ctrl, cmd, pass_sig_list=["Verification passed"], timeout=param_cfg["FPGA_PROG_DELAY"]):
                    test_ctrl.cli_log_err("{:s} failed".format(cmd))
                    return False

    return True

def sys_info(test_ctrl):
    if test_ctrl.mtp._fpga_ver["fpga 0"] is None \
    or test_ctrl.mtp._fpga_ver["fpga 1"] is None \
    or test_ctrl.mtp._fpga_dat["fpga 0"] is None \
    or test_ctrl.mtp._fpga_dat["fpga 1"] is None:
        if not fpga_init(test_ctrl):
            if not silently:
                test_ctrl.cli_log_err("Failed to read FPGA versions", level=0)

    return (test_ctrl.mtp._fpga_ver, test_ctrl.mtp._fpga_dat)

def fpgautil_cmd(test_ctrl, cmd, pass_sig_list=[], fail_sig_list=[], timeout=60):
    fail_sig_list_ = ["ERROR", "fpgautil:", "Invalid Arg", "Exiting "] + fail_sig_list # need new variable since this function call is shared across threads
    if not test_ctrl.mtp.exec_cmd(cmd, pass_sig_list=pass_sig_list, fail_sig_list=fail_sig_list_, timeout=timeout):
        return False
    return True
