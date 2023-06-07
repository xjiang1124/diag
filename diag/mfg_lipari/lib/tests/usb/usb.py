import sys, os, re

sys.path.append(os.path.relpath("../../lib"))
import libtest_config

param_cfg = libtest_config.parse_config("lib/tests/usb/parameters.yaml")
onie_partition = "/dev/sda1"

def detect_usb(test_ctrl, silently=False):
    cmd = "fdisk -l" # just for info
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=10):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd))
        return False

    cmd = "lsusb"
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=10):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd))
        return False

    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    devices = re.findall("Bus .* Device .*: .*", cmd_buf)
    if len(devices) > 2:
        # 2 devices always show up as the root hub.
        return True
    else:
        if not silently:
            test_ctrl.cli_log_err("USB drive not detected", level=0)
        return False


def mount_usb(test_ctrl):
    cmd = "mkdir -p /mnt/usb/"
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=10):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd))
        return False

    cmd = "mount {:s} /mnt/usb".format(onie_partition)
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=10):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd))
        return False

    cmd = "ls /mnt/usb"
    if not test_ctrl.mtp.exec_cmd(cmd, timeout=10):
        test_ctrl.cli_log_err("{:s} command failed".format(cmd))
        return False

    return True


def unmount_usb(test_ctrl):
    cmd = "umount /mnt/usb"
    if not test_ctrl.mtp.exec_cmd(cmd, fail_sig_list=["target is busy"], timeout=10):
        test_ctrl.cli_log_err("Failed to unmount USB drive".format(cmd))
        return False

    return True