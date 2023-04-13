import sys, os, re
import time

sys.path.append(os.path.relpath("../../lib"))
import libtest_config
import libtest_utils
import libmfg_utils

param_cfg = libtest_config.parse_config("lib/tests/cpld/parameters.yaml")
fpgautil_path = "/home/admin/eeupdate/"
file_store_path = "/home/admin/"


def cpld_init(test_ctrl):
    if not cpu_cpld_init(test_ctrl):
        return False

    if not nic_cpld_init(test_ctrl):
        return False

    if not nic_fea_cpld_init(test_ctrl):
        return False

    return True


def cpu_cpld_init(test_ctrl):
    if test_ctrl.mtp._cpld_ver is None:
        test_ctrl.mtp._cpld_ver = dict()

    cmd = "{:s}fpgautil cpld cpu uc".format(fpgautil_path)
    if not fpgautil_cmd(test_ctrl, cmd, timeout=100):
        test_ctrl.cli_log_err("{:s} failed".format(cmd))
        return False

    cmd_buf = test_ctrl.mtp.mtp_get_cmd_buf()
    uc_match = re.search("= ?(0x[A-Fa-f0-9]{4}([A-Fa-f0-9]{4}))", cmd_buf)
    if uc_match:
        test_ctrl.mtp._cpld_ver["cpu"] = uc_match.group(2)
    else:
        test_ctrl.cli_log_err("Failed to read CPU CPLD version", level=0)
        test_ctrl.log_mtp_file("SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(cmd_buf)))
        return False
    return True


@libtest_utils.parallel_combined_test
def nic_cpld_init(test_ctrl, slot):
    if test_ctrl.mtp._cpld_ver is None:
        test_ctrl.mtp._cpld_ver = dict()

    device = "elba {:d}".format(slot)

    cmd = "{:s}fpgautil elba {:d} cpld uc".format(fpgautil_path, slot)
    if not fpgautil_cmd_para(test_ctrl, slot, cmd, timeout=100):
        test_ctrl.cli_log_slot_err(slot, "{:s} failed".format(cmd))
        return False

    cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    uc_match = re.search("= ?(0x[A-Fa-f0-9]{4}([A-Fa-f0-9]{4}))", cmd_buf)
    if uc_match:
        test_ctrl.mtp._cpld_ver[device] = uc_match.group(2)
    else:
        test_ctrl.cli_log_slot_err(slot, "Failed to read {:s} CPLD version".format(device))
        test_ctrl.log_nic_file(slot, "SCRIPTDEBUG>> cmdbuf: {} \nSCRIPTDEBUG<<".format(repr(cmd_buf)))
        return False

    return True


@libtest_utils.parallel_combined_test
def nic_fea_cpld_init(test_ctrl, slot):
    if test_ctrl.mtp._fea_cpld_ver is None:
        test_ctrl.mtp._fea_cpld_ver = dict()

    device = "elba {:d}".format(slot)

    # dump programmed
    cmd = "{:s}fpgautil elba {:d} cpld featurerow".format(fpgautil_path, slot)
    dumprowdatasuccess = False
    for x in range(3):
        if not fpgautil_cmd_para(test_ctrl, slot, cmd, timeout=param_cfg["VERIFY_FEATURE_ROW_DELAY"]):
            test_ctrl.cli_log_slot_err(slot, "Dumping Elba {:d} CPLD feature row failed".format(slot))
            time.sleep(5)
            #return False
        else:
            fea_nic_dump = test_ctrl.nic[slot].nic_get_cmd_buf()
            fea_nic_regex = r" ([0-9 ]*) "
            fea_nic_match = re.search(fea_nic_regex,fea_nic_dump)

            if fea_nic_match:
                dumprowdatasuccess = True
                break
            else:
                time.sleep(5)
    if not dumprowdatasuccess:
        return False
    fea_nic_dump = test_ctrl.nic[slot].nic_get_cmd_buf()
    fea_nic_regex = r" ([0-9 ]*) "
    fea_nic_match = re.search(fea_nic_regex,fea_nic_dump)

    if fea_nic_match:
        test_ctrl.mtp._fea_cpld_ver[device] = fea_nic_match.group(1)
    else:
        test_ctrl.cli_log_slot_err(slot, "Unable to dump feature row.")
        return False

    return True


def cpld_verify(test_ctrl, test_config, silently=False):
    if not cpu_cpld_verify(test_ctrl, test_config, silently):
        return False

    if not nic_cpld_verify(test_ctrl, test_config, silently):
        return False

    if not nic_fea_cpld_verify(test_ctrl, test_config, silently):
        return False

    return True

def cpu_cpld_verify(test_ctrl, test_config, silently):
    if not cpu_cpld_init(test_ctrl):
        return False

    exp_ver = test_config["cpu_cpld_ver"]
    got_ver = test_ctrl.mtp._cpld_ver["cpu"]
    if got_ver != exp_ver:
        if not silently:
            test_ctrl.cli_log_err("Incorrect CPU CPLD version: {:s}, expect: {:s}".format(got_ver, exp_ver), level=0)
        return False

    return True

def nic_cpld_verify(test_ctrl, test_config, silently=False):
    if not nic_cpld_init(test_ctrl):
        return False

    for slot in range(test_ctrl.mtp._slots):
        device = "elba {:d}".format(slot)
        exp_ver = test_config["nic_cpld_ver"]
        got_ver = test_ctrl.mtp._cpld_ver[device]
        if got_ver != exp_ver:
            if not silently:
                test_ctrl.cli_log_slot_err(slot, "Incorrect {:s} CPLD version: {:s}, expect: {:s}".format(device, got_ver, exp_ver))
            return False

    return True


def nic_fea_cpld_verify(test_ctrl, test_config, silently=False):
    if not nic_fea_cpld_init(test_ctrl):
        return False

    cpld_img_file = test_config["nic_fea_cpld_img"]
    test_ctrl.cli_log_inf("Downloading CPLD feature row image")
    if not test_ctrl.mtp.copy_file_to_mtp("release/"+cpld_img_file, file_store_path):
        # test_ctrl.cli_log_err("Unable to get {:s}".format(cpld_img_file), level=0)
        return False

    for slot in range(test_ctrl.mtp._slots):
        device = "elba {:d}".format(slot)
        if test_ctrl.mtp._fea_cpld_ver[device] != test_config["nic_fea_cpld_ver"]:
            cmd = "{:s}fpgautil elba {:d} cpld verify fea {:s}/{:s}".format(fpgautil_path, slot, file_store_path, os.path.basename(cpld_img_file))
            if not fpgautil_cmd_para(test_ctrl, slot, cmd, pass_sig_list=["Verification passed"], timeout=param_cfg["VERIFY_FEATURE_ROW_DELAY"]):
                return False

    return True


def cpu_cpld_prog(test_ctrl, test_config):
    """
        fpgautil cpld cpu program cfg0 ccpld_img.bin
        fpgautil cpld cpu verify cfg0 ccpld_img.bin
        fpgautil cpld cpu program cfg1 ccpld_img.bin
        fpgautil cpld cpu verify cfg1 ccpld_img.bin
    """

    if not param_cfg["FORCE_UPDATE_CPU_CPLD"] and cpu_cpld_verify(test_ctrl, test_config, silently=True):
        test_ctrl.cli_log_inf("CPU CPLD already up-to-date", level=0)
        return True

    cpld_img_file = test_config["cpu_cpld_img"]

    test_ctrl.cli_log_inf("Downloading CPLD image")
    if not test_ctrl.mtp.copy_file_to_mtp("release/"+cpld_img_file, file_store_path):
        # test_ctrl.cli_log_err("Unable to get {:s}".format(cpld_img_file), level=0)
        return False

    for partition in ("cfg0", "cfg1"):
        test_ctrl.cli_log_inf("Programming CPU CPLD {:s} partition".format(partition))
        cmd = "{:s}fpgautil cpld cpu program {:s} {:s}/{:s}".format(fpgautil_path, partition, file_store_path, os.path.basename(cpld_img_file))
        if not fpgautil_cmd(test_ctrl, cmd, pass_sig_list=["Programming passed"], timeout=param_cfg["CPLD_PROG_DELAY"]):
            test_ctrl.cli_log_err("Programming CPU CPLD failed".format(cmd))
            return False

        test_ctrl.cli_log_inf("Verifying programmed CPU CPLD")
        cmd = "{:s}fpgautil cpld cpu verify {:s} {:s}/{:s}".format(fpgautil_path, partition, file_store_path, os.path.basename(cpld_img_file))
        if not fpgautil_cmd(test_ctrl, cmd, pass_sig_list=["Verification"], timeout=param_cfg["CPLD_PROG_DELAY"]):
            test_ctrl.cli_log_err("Verifying programmed CPU CPLD failed".format(cmd))
            return False

    return True


def nic_cpld_prog(test_ctrl, test_config):
    """
        fpgautil elba <0-7> cpld program cfg0 ecpld_img.bin
        fpgautil elba <0-7> cpld verify cfg0 ecpld_img.bin
        fpgautil elba <0-7> cpld program cfg1 ecpld_img.bin
        fpgautil elba <0-7> cpld verify cfg1 ecpld_img.bin
    """
    if not param_cfg["FORCE_UPDATE_NIC_CPLD"] and nic_cpld_verify(test_ctrl, test_config, silently=True):
        test_ctrl.cli_log_inf("Elba CPLDs already up-to-date", level=0)
        return True

    cpld_img_file = test_config["nic_cpld_img"]

    test_ctrl.cli_log_inf("Downloading CPLD image")
    if not test_ctrl.mtp.copy_file_to_mtp("release/"+cpld_img_file, file_store_path):
        # test_ctrl.cli_log_err("Unable to get {:s}".format(cpld_img_file), level=0)
        return False

    nic_list = list(range(test_ctrl.mtp._slots))
    ret = True
    cfg0_fail_nic_list = single_nic_cpld_prog(test_ctrl, nic_list, cpld_img_file, "cfg0")
    for slot in cfg0_fail_nic_list:
        ret &= False
        if slot in nic_list:
            nic_list.remove(0)

    cfg1_fail_nic_list = single_nic_cpld_prog(test_ctrl, nic_list, cpld_img_file, "cfg1")
    for slot in cfg1_fail_nic_list:
        ret &= False

    return ret


def nic_fea_cpld_prog(test_ctrl, test_config):
    """
        fpgautil elba <0-7> cpld program fea Lipari_ecpld_impl1.fea
        fpgautil elba <0-7> cpld verify fea Lipari_ecpld_impl1.fea
    """
    
    if not param_cfg["FORCE_UPDATE_NIC_FEA"] and nic_fea_cpld_verify(test_ctrl, test_config, silently=True):
        test_ctrl.cli_log_inf("Elba CPLD feature rows up-to-date", level=0)
        return True

    cpld_img_file = test_config["nic_fea_cpld_img"]

    test_ctrl.cli_log_inf("Downloading CPLD feature row image")
    if not test_ctrl.mtp.copy_file_to_mtp("release/"+cpld_img_file, file_store_path):
        # test_ctrl.cli_log_err("Unable to get {:s}".format(cpld_img_file), level=0)
        return False

    if not single_nic_fea_cpld_prog(test_ctrl, cpld_img_file):
        return False
    return True


@libtest_utils.parallel_threaded_test_section
def single_nic_cpld_prog(test_ctrl, slot, cpld_img_file, partition):
    test_ctrl.cli_log_slot_inf(slot, "Programming Elba{:d} CPLD {:s} partition".format(slot, partition))

    cmd = "{:s}fpgautil elba {:d} cpld program {:s} {:s}/{:s}".format(fpgautil_path, slot, partition, file_store_path, os.path.basename(cpld_img_file))
    if not fpgautil_cmd_para(test_ctrl, slot, cmd, timeout=param_cfg["CPLD_PROG_DELAY"]):
        test_ctrl.cli_log_slot_err(slot, "{:s} failed".format(cmd))
        return False

    cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if "Programming passed" not in cmd_buf:
        test_ctrl.cli_log_err("Programming Elba{:d} CPLD failed".format(slot))
        return False

    test_ctrl.cli_log_slot_inf(slot, "Verifying programmed Elba{:d} CPLD {:s}".format(slot, partition))
    cmd = "{:s}fpgautil elba {:d} cpld verify {:s} {:s}/{:s}".format(fpgautil_path, slot, partition, file_store_path, os.path.basename(cpld_img_file))
    if not fpgautil_cmd_para(test_ctrl, slot, cmd, timeout=param_cfg["CPLD_PROG_DELAY"]):
        test_ctrl.cli_log_slot_err(slot, "{:s} failed".format(cmd))
        return False

    cmd_buf = test_ctrl.nic[slot].nic_get_cmd_buf()
    if "Verification passed" not in cmd_buf:
        test_ctrl.cli_log_err("Programming Elba{:d} CPLD failed".format(slot))
        return False

    return True


@libtest_utils.parallel_combined_test
def single_nic_fea_cpld_prog(test_ctrl, slot, cpld_img_file):
    test_ctrl.cli_log_slot_inf(slot, "Programming CPLD feature row image")
    cmd = "{:s}fpgautil elba {:d} cpld program fea {:s}/{:s}".format(fpgautil_path, slot, file_store_path, os.path.basename(cpld_img_file))
    if not fpgautil_cmd_para(test_ctrl, slot, cmd, pass_sig_list=["Programming passed"], timeout=param_cfg["CPLD_PROG_DELAY"]):
        test_ctrl.cli_log_err("Programming Elba{:d} CPLD feature row failed".format(slot))
        return False

    test_ctrl.cli_log_slot_inf(slot, "Verifying CPLD feature row image")
    cmd = "{:s}fpgautil elba {:d} cpld verify fea {:s}/{:s}".format(fpgautil_path, slot, file_store_path, os.path.basename(cpld_img_file))
    if not fpgautil_cmd_para(test_ctrl, slot, cmd, pass_sig_list=["Verification passed"], timeout=param_cfg["CPLD_PROG_DELAY"]):
        test_ctrl.cli_log_err("Verifying Elba{:d} CPLD feature row failed".format(slot))
        return False
    return True


def cpld_refresh(test_ctrl):
    # refresh cpu cpld last, where we lose connection
    nic_list = range(test_ctrl.mtp._slots)
    if not nic_cpld_refresh(test_ctrl):
        return False

    test_ctrl.cli_log_inf("Refreshing CPU CPLD", level=0)
    test_ctrl.mtp._mgmt_handle.sendline("{:s}fpgautil cpld cpu refresh".format(fpgautil_path))
    time.sleep(3)
    idx = libmfg_utils.mfg_expect(test_ctrl.mtp._mgmt_handle, ["Timeout", "not responding."])
    while idx > 0:
        idx = libmfg_utils.mfg_expect(test_ctrl.mtp._mgmt_handle, ["Timeout", "not responding."])

    return True


@libtest_utils.parallel_combined_test
def nic_cpld_refresh(test_ctrl, slot):
    test_ctrl.cli_log_slot_inf(slot, "Refreshing Elba CPLD")
    test_ctrl.nic[slot]._nic_handle.sendline("{:s}fpgautil elba {:d} cpld refresh".format(fpgautil_path, slot))
    time.sleep(3)
    idx = libmfg_utils.mfg_expect(test_ctrl.nic[slot]._nic_handle, ["Refresh performed"])
    while idx > 0:
        idx = libmfg_utils.mfg_expect(test_ctrl.nic[slot]._nic_handle, ["Refresh performed"])

    return True


def fpgautil_cmd(test_ctrl, cmd, pass_sig_list=[], fail_sig_list=[], timeout=60):
    fail_sig_list_ = ["ERROR", "fpgautil:", "Invalid Arg", "Exiting "] + fail_sig_list # need new variable since this function call is shared across threads
    if not test_ctrl.mtp.exec_cmd(cmd, pass_sig_list=pass_sig_list, fail_sig_list=fail_sig_list_, timeout=timeout):
        return False
    return True


def fpgautil_cmd_para(test_ctrl, slot, cmd, pass_sig_list=[], fail_sig_list=[], timeout=60):
    fail_sig_list_ = ["ERROR", "fpgautil:", "Invalid Arg", "Exiting "] + fail_sig_list # need new variable since this function call is shared across threads
    if not test_ctrl.mtp.nic_mtp_exec_cmd(slot, cmd, pass_sig_list=pass_sig_list, fail_sig_list=fail_sig_list_, timeout=timeout):
        return False
    return True

