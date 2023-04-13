import sys, os
import time
from collections import OrderedDict

sys.path.append(os.path.relpath("../../lib"))
import libtest_config
import libtest_utils

param_cfg = libtest_config.parse_config("lib/tests/nic_qspi/parameters.yaml")
fpgautil_path = "/home/admin/eeupdate/"
file_store_path = "/home/admin/"


def nic_qspi_prog(test_ctrl, test_config):
    """
        fpgautil elba <0-7> flash program boot0 boot0.img
        fpgautil elba <0-7> flash program golduboot ubootg.img
        fpgautil elba <0-7> flash program goldfw ubootg.img
    """
    img_location = OrderedDict({
        "uboot0":   test_config["boot0_img"],
        "golduboot":test_config["ubootg_img"],
        "goldfw":   test_config["goldfw_img"],
        "uboota":   test_config["uboota_img"]
    })

    for article in img_location.keys():
        qspi_img = img_location[article]
        test_ctrl.cli_log_inf("Downloading QSPI {:s} image".format(article))
        if not test_ctrl.mtp.copy_file_to_mtp("release/"+qspi_img, file_store_path):
            return False

    if not param_cfg["FORCE_UPDATE_QSPI"] and single_nic_qspi_verify(test_ctrl, img_location, silently=True):
        test_ctrl.cli_log_inf("Elba QSPI already up-to-date", level=0)
        return True

    if not single_nic_qspi_prog(test_ctrl, img_location):
        return False

    return True


def nic_qspi_verify(test_ctrl, test_config):
    img_location = OrderedDict({
        "uboot0":   test_config["boot0_img"],
        "golduboot":test_config["ubootg_img"],
        "goldfw":   test_config["goldfw_img"],
        "uboota":   test_config["uboota_img"]
    })

    if not single_nic_qspi_verify(test_ctrl, img_location, silently=False):
        return False
    return True


@libtest_utils.parallel_combined_test
def single_nic_qspi_prog(test_ctrl, slot, article_img_dict):
    for article in article_img_dict.keys():
        test_ctrl.cli_log_slot_inf(slot, "Programming Elba{:d} {:s}".format(slot, article))

        cmd = "{:s}fpgautil elba {:d} flash program {:s} {:s}/{:s}".format(fpgautil_path, slot, article, file_store_path, os.path.basename(article_img_dict[article]))
        if not fpgautil_cmd_para(test_ctrl, slot, cmd, timeout=param_cfg["QSPI_PROG_DELAY"]):
            test_ctrl.cli_log_slot_err(slot, "{:s} failed".format(cmd))
            return False

        cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
        if "Flashing Partition {:s} passed".format(article) not in cmd_buf:
            test_ctrl.cli_log_err("Programming Elba{:d} {:s} failed".format(slot, article))
            return False

        cmd = "{:s}fpgautil elba {:d} flash verify {:s} {:s}/{:s}".format(fpgautil_path, slot, article, file_store_path, os.path.basename(article_img_dict[article]))
        if not fpgautil_cmd_para(test_ctrl, slot, cmd, timeout=param_cfg["QSPI_PROG_DELAY"]):
            test_ctrl.cli_log_slot_err(slot, "{:s} failed".format(cmd))
            return False

        cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
        if "Verification passed" not in cmd_buf:
            test_ctrl.cli_log_err("Verifying Elba{:d} {:s} failed".format(slot, article))
            return False

    return True


@libtest_utils.parallel_combined_test
def single_nic_qspi_verify(test_ctrl, slot, article_img_dict, silently=False):
    for article in article_img_dict.keys():
        cmd = "{:s}fpgautil elba {:d} flash verify {:s} {:s}/{:s}".format(fpgautil_path, slot, article, file_store_path, os.path.basename(article_img_dict[article]))
        if not fpgautil_cmd_para(test_ctrl, slot, cmd, timeout=param_cfg["QSPI_PROG_DELAY"]):
            test_ctrl.cli_log_slot_err(slot, "{:s} failed".format(cmd))
            test_ctrl.log_nic_file(slot, "SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(test_ctrl.nic[slot].nic_get_cmd_buf()))
            return False

        cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
        if "Verification passed" not in cmd_buf:
            if not silently:
                test_ctrl.cli_log_slot_err(slot, "Verifying Elba{:d} {:s} failed".format(slot, article))
            return False

    return True


def fpgautil_cmd_para(test_ctrl, slot, cmd, pass_sig_list=[], fail_sig_list=[], timeout=60):
    fail_sig_list_ = ["fpgautil:", "Invalid Arg", "Exiting "] + fail_sig_list # need new variable since this function call is shared across threads
    if not test_ctrl.mtp.nic_mtp_exec_cmd(slot, cmd, pass_sig_list=pass_sig_list, fail_sig_list=fail_sig_list_, timeout=timeout):
        return False
    return True

