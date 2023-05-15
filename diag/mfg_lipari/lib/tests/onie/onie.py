import sys, os, re, time

sys.path.append(os.path.relpath("../../lib"))
import libtest_config
import libmfg_utils

param_cfg = libtest_config.parse_config("lib/tests/onie/parameters.yaml")
file_store_path = "/"
ONIE_USERNAME = "root"
ONIE_PASSWORD = ""


def onie_init(test_ctrl, silently=False):
    """
        ONIE:/ # uname -r                       <-- _onie_ver

        ONIE:/ # cat /etc/os*
        VERSION="master-02240905.0.1-dirty"     <-- _onie_dat 

    """

    @retry_console_cmd
    def onie_ver_cmd(test_ctrl):
        cmd = "uname -r"
        if not test_ctrl.mtp.exec_cmd(cmd, timeout=1):
            test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
            return False
        cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf().strip()
        if not cmd_buf:
            return False
        match = re.findall(r"([\d\w\.]+-onie\+?)", cmd_buf)
        if match:
            test_ctrl.mtp._onie_ver = match[0]
            return True
        else:
            return False

    if not onie_ver_cmd(test_ctrl):
        if not silently:
            test_ctrl.cli_log_err("Couldn't find ONIE version", level=0)
        return False


    @retry_console_cmd
    def onie_dat_cmd(test_ctrl):
        cmd = "cat /etc/os*"
        if not test_ctrl.mtp.exec_cmd(cmd, timeout=1):
            test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
            return False
        cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf().strip()
        if not cmd_buf:
            return False
        match = re.findall(r"VERSION=\".*-(\d+)\..*\"", cmd_buf)
        if match:
            test_ctrl.mtp._onie_dat = match[0].strip()
            return True
        else:
            return False

    if not onie_dat_cmd(test_ctrl):
        if not silently:
            test_ctrl.cli_log_err("Couldn't find ONIE build date", level=0)
        return False

    return True


def onie_verify(test_ctrl, test_config, silently=False):
    exp_ver = test_config["onie_ver"]
    exp_dat = test_config["onie_dat"]
    if not onie_init(test_ctrl, silently):
        return False

    got_dat = test_ctrl.mtp._onie_dat
    if got_dat != exp_dat:
        if not silently:
            test_ctrl.cli_log_err("Incorrect ONIE build date: {:s}, expected {:s}".format(got_dat, exp_dat), level=0)
        return False

    got_ver = test_ctrl.mtp._onie_ver
    if got_ver != exp_ver:
        if not silently:
            test_ctrl.cli_log_err("Incorrect ONIE version: {:s}, expected {:s}".format(got_ver, exp_ver), level=0)
        return False

    return True


def onie_prog(test_ctrl, test_config):
    if not param_cfg["FORCE_UPDATE_ONIE"] and onie_verify(test_ctrl, test_config, silently=True):
        test_ctrl.cli_log_inf("ONIE already up-to-date", level=0)
        return True

    onie_img_file = test_config["onie_img"]
    test_ctrl.cli_log_inf("Downloading ONIE image")

    old_cfg = set_onie_credentials(test_ctrl)    
    if not test_ctrl.mtp.copy_file_to_mtp("release/"+onie_img_file, file_store_path, nopasswd=True):
        return False
    unset_onie_credentials(test_ctrl, old_cfg)

    test_ctrl.cli_log_inf("Programming ONIE image", level=0)
    cmd = "onie-self-update -v {:s}/{:s}".format(file_store_path, os.path.basename(onie_img_file))
    test_ctrl.mtp._mgmt_handle.sendline(cmd)
    libmfg_utils.mfg_expect(test_ctrl.mtp._mgmt_handle, ["The system is going down"], timeout=param_cfg["ONIE_PROG_DELAY"])
    return True


def set_onie_credentials(test_ctrl):
    old_cfg = test_ctrl.mtp._mgmt_cfg
    test_ctrl.mtp._mgmt_cfg = ["", ONIE_USERNAME, ONIE_PASSWORD]

    @retry_console_cmd
    def read_onie_ip(test_ctrl):
        if not test_ctrl.mtp.tor_get_ip():
            return False
        else:
            return True
    if not read_onie_ip(test_ctrl):
        test_ctrl.cli_log_err("Failed to get IP in ONIE", level=0)

    return old_cfg


def unset_onie_credentials(test_ctrl, old_cfg):
    test_ctrl.mtp._mgmt_cfg = old_cfg


def set_onie_rescue_mode(test_ctrl):
    if get_onie_boot_mode(test_ctrl):
        return True

    test_ctrl.cli_log_inf("Setting ONIE Rescue Mode", level=0)

    @retry_console_cmd
    def onie_rescue_cmd(test_ctrl):
        if not test_ctrl.mtp.exec_cmd("onie-boot-mode -o rescue", timeout=60):
            return False
        if not test_ctrl.mtp.exec_cmd("sync"):
            return False
        else:
            return True
    if not onie_rescue_cmd(test_ctrl):
        test_ctrl.cli_log_err("Failed to set ONIE Rescue mode", level=0)
        return False

    return True


def get_onie_boot_mode(test_ctrl):
    if not test_ctrl.mtp.exec_cmd("onie-boot-mode", pass_sig_list=["Default boot"], timeout=1):
        return False
    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    if "ONIE mode: rescue" in cmd_buf:
        return True
    else:
        return False


def install_sonic_from_onie(test_ctrl):
    scp_failed = False
    os_img_file = test_ctrl.image["os_img"]
    test_ctrl.cli_log_inf("Downloading SONiC image", level=0)
    old_cfg = set_onie_credentials(test_ctrl)
    if not test_ctrl.mtp.copy_file_to_mtp("release/"+os_img_file, file_store_path, nopasswd=True):
        scp_failed = True
    unset_onie_credentials(test_ctrl, old_cfg)

    test_ctrl.cli_log_inf("Installing SONiC", level=0)
    if scp_failed:
        cmd = "onie-nos-install tftp://192.168.66.79/lipari/sonic-broadcom_56993_brcm_patch.bin"
    else:
        cmd = "onie-nos-install {:s}/{:s}".format(file_store_path, os.path.basename(os_img_file))
    test_ctrl.mtp._mgmt_handle.sendline(cmd)
    idx = libmfg_utils.mfg_expect(test_ctrl.mtp._mgmt_handle, ["Failure", "ERROR"], timeout=5)
    if idx > 0:
        test_ctrl.cli_log_err("SONiC installation failed", level=0)
        return False
    if scp_failed:
        libmfg_utils.count_down(20*60) # 9-20min of no output (during tftp), then auto-reboot
    else:
        time.sleep(5) # auto-reboot and check for bootup messages
    return True


def retry_console_cmd(func):
    def start_end(test_ctrl, *args, **kwargs):
        retries = 5
        while retries >= 0:
            if retries == 0:
                test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(test_ctrl.mtp.mtp_get_cmd_buf())))
                return False
            retries -= 1

            if not func(test_ctrl, *args, **kwargs):
                time.sleep(5)
                continue
            else:
                return True
    return start_end