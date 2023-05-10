import sys, os, re

sys.path.append(os.path.relpath("../../lib"))
import libtest_config

param_cfg = libtest_config.parse_config("lib/tests/bios/parameters.yaml")
file_store_path = "/home/admin/"

def bios_init(test_ctrl):
    cmd = "dmidecode -s bios-version"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed", level=0)
        return False

    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    match = re.findall("\d+\.\d+", cmd_buf)
    if match:
        test_ctrl.mtp._bios_ver = match[0]
    else:
        test_ctrl.cli_log_err("Failed to read BIOS version", level=0)
        return False

    cmd = "dmidecode -s bios-release-date"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed", level=0)
        return False

    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    match = re.findall("\d{2}/\d{2}/\d{4}", cmd_buf)
    if match:
        test_ctrl.mtp._bios_dat = match[0]
    else:
        test_ctrl.cli_log_err("Failed to read BIOS timestamp", level=0)
        return False

    return True

def bios_verify(test_ctrl, test_config, silently=False):
    exp_ver = test_config["bios_ver"]
    exp_dat = test_config["bios_dat"]

    if not bios_init(test_ctrl):
        if not silently:
            test_ctrl.cli_log_err("Failed to read BIOS version")
        return False

    got_ver = test_ctrl.mtp._bios_ver
    if got_ver != exp_ver:
        if not silently:
            test_ctrl.cli_log_err("Incorrect BIOS version: {:s}, expected {:s}".format(got_ver, exp_ver), level=0)
        return False

    got_dat = test_ctrl.mtp._bios_dat
    if got_dat != exp_dat:
        if not silently:
            test_ctrl.cli_log_err("Incorrect BIOS timestamp: {:s}, expected {:s}".format(got_dat, exp_dat), level=0)
        return False

    return True

def bios_prog(test_ctrl, test_config):
    if not param_cfg["FORCE_UPDATE_BIOS"] and bios_verify(test_ctrl, test_config, silently=True):
        test_ctrl.cli_log_inf("BIOS already up-to-date", level=0)
        return True

    bios_img_file = test_config["bios_img"]
    test_ctrl.cli_log_inf("Downloading BIOS image")    
    if not test_ctrl.mtp.copy_file_to_mtp("release/"+bios_img_file, file_store_path):
        return False

    test_ctrl.cli_log_inf("Programming BIOS image", level=0)
    cmd = "/home/admin/eeupdate/h2offt -ALL {:s}/{:s} -N".format(file_store_path, os.path.basename(bios_img_file))
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=param_cfg["BIOS_PROG_DELAY"]):
        test_ctrl.cli_log_err("Failed to program BIOS image", level=0)
        return False

    return True
