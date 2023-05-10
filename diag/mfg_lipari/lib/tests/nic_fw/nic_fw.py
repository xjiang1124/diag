import sys, os, re

sys.path.append(os.path.relpath("../../lib"))
import libtest_config
import libtest_utils

param_cfg = libtest_config.parse_config("lib/tests/nic_fw/parameters.yaml")


@libtest_utils.parallel_combined_test
def set_goldfw_boot(test_ctrl, slot, *args, **kwargs):
    cmd_list = ["fwupdate -s goldfw", "fwupdate -S"]
    if not test_ctrl.nic[slot].nic_exec_console_cmds(cmd_list):
        return False
    nic_cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if not nic_cmd_buf:
        test_ctrl.cli_log_slot_err(slot, "Failed to check startup image")
        return False
    if "goldfw" in nic_cmd_buf:
        return True


@libtest_utils.parallel_combined_test
def verify_goldfw_boot(test_ctrl, slot, *args, **kwargs):
    cmd_list = ["fwupdate -r"]
    if not test_ctrl.nic[slot].nic_exec_console_cmds(cmd_list):
        return False
    nic_cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if not nic_cmd_buf:
        return False
    if "goldfw" in nic_cmd_buf:
        return True
    else:
        test_ctrl.cli_log_slot_err(slot, "Booted from {:s}".format(nic_cmd_buf))
        return False


@libtest_utils.parallel_combined_test
def set_mainfwa_boot(test_ctrl, slot, *args, **kwargs):
    cmd_list = ["fwupdate -s mainfwa", "fwupdate -S"]
    if not test_ctrl.nic[slot].nic_exec_console_cmds(cmd_list):
        return False
    nic_cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if not nic_cmd_buf:
        test_ctrl.cli_log_slot_err(slot, "Failed to check startup image")
        return False
    if "mainfwa" in nic_cmd_buf:
        return True


@libtest_utils.parallel_combined_test
def verify_mainfwa_boot(test_ctrl, slot, *args, **kwargs):
    cmd_list = ["fwupdate -r"]
    if not test_ctrl.nic[slot].nic_exec_console_cmds(cmd_list):
        return False
    nic_cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if not nic_cmd_buf:
        return False
    if "mainfwa" in nic_cmd_buf:
        return True
    else:
        test_ctrl.cli_log_slot_err(slot, "Booted from {:s}".format(nic_cmd_buf))
        return False