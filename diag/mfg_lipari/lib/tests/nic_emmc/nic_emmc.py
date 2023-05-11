import sys, os

sys.path.append(os.path.relpath("../../lib"))
import libtest_config
import libtest_utils

param_cfg = libtest_config.parse_config("lib/tests/nic_emmc/parameters.yaml")

EMMC_FORMAT_SCRIPT = "/home/admin/diag/scripts/emmc_format.sh"
BKOPS_SCRIPT = "/home/admin/diag/scripts/mmc.latest"
PSLC_PARTITION_OK_SIG = "setting OTP PARTITION_SETTING_COMPLETED!"
PSLC_PARTITION1_OK_SIG = "Device is already partitioned"
HWRESET_PASS_SIG = "H/W reset function [RST_N_FUNCTION]: 0x01"
HWRESET_FAIL_SIG = "H/W reset function [RST_N_FUNCTION]: 0x00"
BKOPS_PASS_SIG = "Enable background operations handshake [BKOPS_EN]: 0x02"
BKOPS_FAIL_SIG = "Enable background operations handshake [BKOPS_EN]: 0x00"

@libtest_utils.parallel_combined_test
def format_emmc(test_ctrl, slot):
    if not verify_pslc(test_ctrl, slot):
        return False

    # copy script to detect the emmc part size
    if not test_ctrl.nic[slot].copy_file_to_nic(EMMC_FORMAT_SCRIPT):
        test_ctrl.cli_log_slot_err(slot, "Could not copy emmc_format.sh")
        return False

    # Run command twice: first time does it, 2nd time says 'already partitioned'
    if not set_pslc(test_ctrl, slot):
        test_ctrl.cli_log_slot_err(slot, "Could not complete partition command")
        return False
    if not set_pslc(test_ctrl, slot): 
        test_ctrl.cli_log_slot_err(slot, "Partition table was not updated")
        return False
    test_ctrl.cli_log_slot_inf(slot, "Partition table updated")

    # verify
    if not verify_pslc(test_ctrl, slot):
        return False

    return True


def verify_pslc(test_ctrl, slot):
    cmd = "fdisk -l"
    test_ctrl.nic[slot].nic_exec_ssh_cmds(cmd)
    return True


def set_pslc(test_ctrl, slot):
    cmd = "sh /emmc_format.sh"
    if not test_ctrl.nic[slot].nic_exec_ssh_cmds(cmd):
        return False

    cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if not cmd_buf:
        return False
    if PSLC_PARTITION1_OK_SIG in cmd_buf:
        return True
    elif PSLC_PARTITION_OK_SIG in cmd_buf:
        return True
    else:
        return False


def read_emmc_id(test_ctrl, slot):
    cmd = "cat /sys/block/mmcblk0/device/manfid"
    if not test_ctrl.nic[slot].nic_exec_ssh_cmds(cmd):
        test_ctrl.cli_log_slot_err(slot, "Reading emmc id failed")
        return False
    cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if not cmd_buf:
        return False
    id_match = re.search("0x([0-9A-Za-z]+)", cmd_buf)
    if not id_match:
        test_ctrl.cli_log_slot_err(slot, "Failed to parse emmc manufacturer id")
        return False
    test_ctrl.nic[slot]._emmc_mfr_id = id_match.group(1)

    # also find mfr id dumped by kernel
    cmd = "dmesg | grep mmc"
    if not test_ctrl.nic[slot].nic_exec_ssh_cmds(cmd):
        test_ctrl.cli_log_slot_err(slot, "Dumping emmc logs failed")
        return False

    return True


@libtest_utils.parallel_combined_test
def enable_emmc_bkops(test_ctrl, slot):
    if not test_ctrl.nic[slot].copy_file_to_nic(BKOPS_SCRIPT):
        test_ctrl.cli_log_slot_err(slot, "Could not copy emmc util")
        return False
    if not verify_bkops(test_ctrl, slot):
        if not enable_bkops(test_ctrl, slot): 
            test_ctrl.cli_log_slot_err(slot, "Failed to enable eMMC bkops")
            return False
        if not verify_bkops(test_ctrl, slot):
            test_ctrl.cli_log_slot_err(slot, "Incorrect eMMC bkops value reflected")
            return False
    return True

@libtest_utils.parallel_combined_test
def set_emmc_hwreset(test_ctrl, slot):
    if not verify_hwreset(test_ctrl, slot):
        if not set_hwreset(test_ctrl, slot): 
            test_ctrl.cli_log_slot_err(slot, "Failed to enable eMMC hwreset setting")
            return False
        if not verify_hwreset(test_ctrl, slot):
            test_ctrl.cli_log_slot_err(slot, "Incorrect eMMC hwreset setting reflected")
            return False
    return True


def set_hwreset(test_ctrl, slot):
    """
    # mmc hwreset enable /dev/mmcblk0
    # mmc extcsd read /dev/mmcblk0|grep -i reset
    H/W reset function [RST_N_FUNCTION]: 0x01
    """
    cmd = "mmc hwreset enable /dev/mmcblk0"
    if not test_ctrl.nic[slot].nic_exec_ssh_cmds(cmd, timeout=10):
        return False
    return True

def verify_hwreset(test_ctrl, slot):
    cmd = "mmc extcsd read /dev/mmcblk0 | grep -i reset"
    test_ctrl.nic[slot].nic_exec_ssh_cmds(cmd)
    cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if not cmd_buf:
        return False
    if HWRESET_PASS_SIG in cmd_buf:
        return True
    elif HWRESET_FAIL_SIG in cmd_buf:
        return False
    else:
        return False

def enable_bkops(test_ctrl, slot):
    """
    -------------------------
    ENABLE BKOPS INSTRUCTIONS
    -------------------------
    Enable auto background mmc ops.  SEE warning below.
    # /data/nic_util/mmc.latest bkops_en auto /dev/mmcblk0

    Example:

    BEFORE:
    # mmc extcsd read /dev/mmcblk0|grep -i ops
    Background operations support [BKOPS_SUPPORT: 0x01]
    Background operations status [BKOPS_STATUS: 0x00]
    Enable background operations handshake [BKOPS_EN]: 0x00    <==== OFF

    AFTER:
    # mmc extcsd read /dev/mmcblk0|grep -i ops
    Background operations support [BKOPS_SUPPORT: 0x01]
    Background operations status [BKOPS_STATUS: 0x00]
    Enable background operations handshake [BKOPS_EN]: 0x02    <==== AUTO

    WARNING DO NOT SET MANUAL, this is a OTP setting and can't be undone

    # /data/nic_util/mmc.latest bkops --help
    Usage:
            mmc.latest bkops_en <auto|manual> <device>
                    Enable the eMMC BKOPS feature on <device>.
                    The auto (AUTO_EN) setting is only supported on eMMC 5.0 or newer.
                    Setting auto won't have any effect if manual is set.
                    NOTE!  Setting manual (MANUAL_EN) is one-time programmable (unreversible) change.
    """
    nic_cmd_list = list()
    nic_cmd_list.append("/mmc.latest bkops_en auto /dev/mmcblk0")
    if not test_ctrl.nic[slot].nic_exec_ssh_cmds(nic_cmd_list, timeout=10):
        return False
    return True

def verify_bkops(test_ctrl, slot):
    nic_cmd_list = list()
    nic_cmd_list.append("mmc extcsd read /dev/mmcblk0 | grep -i ops")
    test_ctrl.nic[slot].nic_exec_ssh_cmds(nic_cmd_list)
    cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if not cmd_buf:
        return False
    if BKOPS_PASS_SIG in cmd_buf:
        return True
    elif BKOPS_FAIL_SIG in cmd_buf:
        return False
    else:
        return False

def nic_init_emmc(test_ctrl, slot, init=False):
    nic_cmd_list = list()
    if init:
        if not read_emmc_id(test_ctrl, slot):
            return False

        nic_cmd = MFG_DIAG_CMDS.NIC_CHECK_EMMC_FMT
        emmc_check_sig = MFG_DIAG_SIG.NIC_EMMC_CHECK_OK_SIG
        emmc_check_buf = test_ctrl.nic[slot].nic_exec_ssh_cmds(nic_cmd)
        if emmc_check_buf:
            if emmc_check_sig in emmc_check_buf:
                pass
            else:
                test_ctrl.cli_log_slot_err(slot, "pSLC mode setting not found")
                if not SKIP_EMMC_PSLC_CHECK:
                    return False
        else:
            return False
    if init:
        nic_cmd = MFG_DIAG_CMDS.NIC_EMMC_INIT_FMT
        nic_cmd_list.append(nic_cmd)
    nic_cmd = MFG_DIAG_CMDS.NIC_FSCK_EMMC_FMT
    nic_cmd_list.append(nic_cmd)
    nic_cmd = MFG_DIAG_CMDS.NIC_MOUNT_EMMC_FMT
    nic_cmd_list.append(nic_cmd)
    nic_cmd_list.append(MFG_DIAG_CMDS.NIC_PARTITION_DISP_FMT)
    if not test_ctrl.nic[slot].nic_exec_ssh_cmds(nic_cmd_list, timeout=MTP_Const.OS_CMD_DELAY):
        return False

    # check if mount is ok
    nic_cmd = MFG_DIAG_CMDS.NIC_MOUNT_DISP_FMT
    mount_sig = MFG_DIAG_SIG.NIC_MOUNT_OK_SIG
    mount_buf = test_ctrl.nic[slot].nic_exec_ssh_cmds(nic_cmd)
    if mount_buf:
        if mount_sig in mount_buf:
            return True
        else:
            return False
    else:
        return False
