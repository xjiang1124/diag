import sys, os, re, time
from datetime import datetime

sys.path.append(os.path.relpath("../../lib"))
import libtest_config

param_cfg = libtest_config.parse_config("lib/tests/tor_os/parameters.yaml")
file_store_path = "/home/admin/"

def os_init(test_ctrl):
    """
        SONiC Software Version: SONiC.master.0-dirty-20230314.045729    <-- _os_name
        Distribution: Debian 11.6
        Kernel: 5.10.0-12-2-amd64                                       <-- _os_ver
        Build commit: 7018aa4ac
        Build date: Tue Mar 14 05:42:19 UTC 2023                        <-- _os_dat
        Built by: vm@lipari3
    """
    cmd = "show version"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    match = re.findall("Build date *: *(.*)", cmd_buf)
    if match:
        # check if timestamp is valid
        try:
            dt = datetime.strptime(match[0].strip(), "%a %b %d %H:%M:%S %Z %Y")
            test_ctrl.mtp._os_dat = dt.strftime("%m-%d-%Y")
        except ValueError:
            test_ctrl.cli_log_err("Invalid OS build date", level=0)
            test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(cmd_buf)))
            test_ctrl.log_mtp_file("SCRIPTDEBUG>> match: {} \nSCRIPTDEBUG<<".format(str(match[0])))
            return False

    match = re.findall("Kernel *: *(.*)", cmd_buf)
    if match:
        test_ctrl.mtp._os_ver = match[0].strip()
    else:
        test_ctrl.cli_log_err("Unable to read OS version", level=0)
        test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(cmd_buf)))
        return False

    match = re.findall("SONiC Software Version *: *(.*)", cmd_buf)
    if match:
        test_ctrl.mtp._os_name = match[0].strip()
    else:
        test_ctrl.cli_log_err("Unable to read OS version name", level=0)
        test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(cmd_buf)))
        return False

    cmd = "sonic-installer list"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
        return False

    return True

def os_verify(test_ctrl, test_config, silently=False):
    exp_ver = test_config["os_ver"]
    exp_dat = test_config["os_dat"]
    if not os_init(test_ctrl):
        if not silently:
            test_ctrl.cli_log_err("Failed to read SONiC version", level=0)
        return False

    got_dat = test_ctrl.mtp._os_dat
    if got_dat != exp_dat:
        if not silently:
            test_ctrl.cli_log_err("Incorrect OS build date: {:s}, expected {:s}".format(got_dat, exp_dat), level=0)
        return False

    got_ver = test_ctrl.mtp._os_ver
    if got_ver != exp_ver:
        if not silently:
            test_ctrl.cli_log_err("Incorrect OS version: {:s}, expected {:s}".format(got_ver, exp_ver), level=0)
        return False

    return True

def os_prog(test_ctrl, test_config):
    """
        sonic-installer install sonic.bin -y
        sonic-installer verify-next-image
        sonic-installer cleanup -y
        sonic-installer list
    """
    if not param_cfg["FORCE_UPDATE_OS"] and os_verify(test_ctrl, test_config, silently=True):
        test_ctrl.cli_log_inf("OS already up-to-date", level=0)
        return True

    os_img_file = test_config["os_img"]
    test_ctrl.cli_log_inf("Downloading OS image")
    if not test_ctrl.mtp.copy_file_to_mtp("release/"+os_img_file, file_store_path):
        return False

    test_ctrl.cli_log_inf("Programming OS image", level=0)
    cmd = "sonic-installer install {:s}/{:s} -y".format(file_store_path, os.path.basename(os_img_file))
    if not test_ctrl.mtp.exec_cmd(cmd, pass_sig_list=["Installed"], timeout=param_cfg["OS_PROG_DELAY"]):
        test_ctrl.cli_log_err("{:s} failed".format(cmd), level=0)
        return False

    cmd = "sonic-installer verify-next-image"
    if not test_ctrl.mtp.exec_cmd(cmd, pass_sig_list=["Image successfully verified"], timeout=param_cfg["OS_PROG_DELAY"]):
        test_ctrl.cli_log_err("New OS image verification failed".format(cmd), level=0)
        return False

    cmd = "sonic-installer cleanup -y"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} failed".format(cmd), level=0)
        return False

    cmd = "sonic-installer list"
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("{:s} failed".format(cmd), level=0)
        return False

    return True

def sys_info(test_ctrl):
    if test_ctrl.mtp._os_name is None \
    or test_ctrl.mtp._os_ver is None \
    or test_ctrl.mtp._os_dat is None: 
        if not os_init(test_ctrl):
            if not silently:
                test_ctrl.cli_log_err("Failed to read SONiC version", level=0)

    return (test_ctrl.mtp._os_ver, test_ctrl.mtp._os_dat, test_ctrl.mtp._os_name)

def erase_ssd(test_ctrl):
    """
        Delete ONIE and SONiC partition table
    """
    handle = test_ctrl.mtp._mgmt_handle

    handle.sendline("fdisk /dev/nvme0n1")
    handle.expect([": "])
    handle.sendline("d")
    handle.expect([": "])
    handle.sendline("3")
    handle.expect([": "])
    handle.sendline("d")
    handle.expect([": "])
    handle.sendline("2")
    handle.expect([": "])
    handle.sendline("d")
    handle.expect([": "])
    handle.sendline("w")
    handle.expect([test_ctrl.mtp._mgmt_prompt], timeout=10)
    time.sleep(2)
    return True

