import sys, os

sys.path.append(os.path.relpath("../../lib"))
import libtest_config

param_cfg = libtest_config.parse_config("lib/tests/diag/parameters.yaml")


### DIAG_INIT ###
def tor_diag_init(test_ctrl):
    if not copy_diag_img(test_ctrl):
        return False

    if not diag_env_init(test_ctrl):
        return False

    return True


def copy_diag_img(test_ctrl):
    amd64_img = test_ctrl.image["amd64_img"]
    src = "release/" + os.path.basename(amd64_img)
    copy_dst = "/home/admin/" + os.path.basename(amd64_img)
    untar_dst = "/home/admin/"

    if check_diag_img(test_ctrl, ["/home/admin/eeupdate/"]):
        test_ctrl.cli_log_inf("Diag images up-to-date", level=0)
        return True

    test_ctrl.cli_log_inf("Downloading diag images", level=0)
    if not test_ctrl.mtp.copy_file_to_mtp(src, os.path.dirname(copy_dst)):
        test_ctrl.cli_log_err("Failed to download diag image", level=0)
        return False

    cmd = "tar xf {:s} -C {:s}".format(copy_dst, untar_dst)
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("Failed to extract diag image", level=0)
        return False

    cmd = "ls {:s}".format(untar_dst)
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("Failed to extract diag image", level=0)
        return False

    cmd = "ls {:s}".format(untar_dst+os.path.basename(copy_dst))
    if not test_ctrl.mtp.exec_cmd(cmd):
        test_ctrl.cli_log_err("Failed to extract diag image", level=0)
        return False

    return True


def check_diag_img(test_ctrl, filename_list):
    for filename in filename_list:
        cmd = "ls {:s}".format(filename)
        if not test_ctrl.mtp.exec_cmd(cmd):
            test_ctrl.cli_log_err("{:s} command failed", level=0)
            return False

        cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
        if not cmd_buf:
            return False

        if "No such file" in cmd_buf:
            return False

    return True


def diag_env_init(test_ctrl, slot=None):
    cmd = "source /home/admin/eeupdate/header.bash"

    if slot is None:
        if not test_ctrl.mtp.exec_cmd(cmd):
            test_ctrl.cli_log_err("{:s} command failed".format(cmd), level=0)
            return False
    else:
        if not test_ctrl.mtp.nic_mtp_exec_cmd(slot, cmd):
            test_ctrl.cli_log_slot_err(slot, "{:s} command failed".format(cmd), level=0)
            return False

    return True