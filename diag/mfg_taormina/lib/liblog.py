import pexpect
import time
import os
import sys
import re
import libmfg_utils
import traceback
from libdefs import MTP_Const

def collect_err_msg(mtp_mgmt_ctrl, subtest, vmarg=None):
    try:
        collect_test_err_msg(mtp_mgmt_ctrl, subtest)
        collect_diag_err_msg(mtp_mgmt_ctrl, subtest)
        collect_dsp_err_msg(mtp_mgmt_ctrl, vmarg) # for 2C only
        collect_nic_err_msg(mtp_mgmt_ctrl, 0)
        collect_nic_err_msg(mtp_mgmt_ctrl, 1)
    except:
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.cli_log_err(err_msg)
        return False
    return True

def collect_test_err_msg(mtp_mgmt_ctrl, subtest):
    buf_all = read_entire_logfile(mtp_mgmt_ctrl, "mtp_test.log")

    if subtest:
        # Collect all error messages within the subtest section
        buf = _strip_logfile_to_subtest(buf_all, " " + subtest)
        if not buf:
            buf = buf_all
    else:
        buf = buf_all

    err_msg_list = cleanup(re.findall(r"(ERR: .*)", buf))
    mtp_mgmt_ctrl.set_err_msg(err_msg_list)
    return True

def collect_diag_err_msg(mtp_mgmt_ctrl, subtest):
    buf_all = read_entire_logfile(mtp_mgmt_ctrl, "mtp_diag.log")

    if not subtest:
        # If no subtest is specified, collect any errors listed
        # in diag file
        err_msg_list = cleanup(re.findall(r"(\[ERROR\] .*)", buf_all))
    else:
        # Collect all error messages within the subtest section
        buf = _strip_logfile_to_subtest(buf_all, "# " + subtest)
        if not buf:
            # If subtest section is not listed in diag file,
            # do not collect anything
            buf = ''
        else:
            if subtest in ['OS_BOOT']:
                # OS_BOOT: Strip off bootup output
                buf_lstrip_list = _strip_log_output(buf, "10000#")
                buf = "\n".join(buf_lstrip_list)

        err_msg_list = buf.split("\r\n")

    mtp_mgmt_ctrl.set_err_msg(err_msg_list)
    return True

def collect_dsp_err_msg(mtp_mgmt_ctrl, vmarg):
    # read diag_logs/log_*.txt
    if vmarg == MTP_Const.MFG_EDVT_LOW_VOLT:
        diag_sub_dir = "lv_diag_logs/"
    elif vmarg == MTP_Const.MFG_EDVT_HIGH_VOLT:
        diag_sub_dir = "hv_diag_logs/"
    else:
        return True

    for dsp in ("BCM", "SWITCH", "I2C", "QSFP"):
        buf = read_entire_logfile(mtp_mgmt_ctrl, "{:s}/log_{:s}.txt".format(diag_sub_dir, dsp))
        err_msg_list = cleanup(re.findall(r"(\[ERROR\] .*)", buf))
        mtp_mgmt_ctrl.set_err_msg(err_msg_list)
    return True

def collect_nic_err_msg(mtp_mgmt_ctrl, slot):
    key = libmfg_utils.nic_key(slot)
    buf = read_entire_logfile(mtp_mgmt_ctrl, "mtp_test.log")
    err_msg_list = cleanup(re.findall("ERR: *\[UUT-.+\] *\[({:s})\]:(.*)".format(key), buf))
    err_msg_list = [nic_key + " " + nic_err_msg for nic_key, nic_err_msg in err_msg_list] # turn two collected fields into one
    mtp_mgmt_ctrl.set_err_msg(err_msg_list)
    return True

def read_entire_logfile(mtp_mgmt_ctrl, filename):
    # filename should be relative path from log folder root
    buf = None
    tlf = mtp_mgmt_ctrl._test_log_folder
    with open(os.path.join(tlf, filename), "rb") as fh:
        buf = fh.read().decode('ascii', errors='ignore')
    return buf

def cleanup(err_msg_list):
     return list(map(unicode.strip, err_msg_list)) # cleanup newlines


def _strip_logfile_to_subtest(buf, subtest):
    # Take logfile buffer and lstrip it down to beginning of subtest
    buf_lstrip_list = _strip_log_output(buf, subtest)

    # Reverse the lstripped buffer and lstrip it up to end of subtest
    buf_lstrip_list.reverse()
    buf_rstrip_list = _strip_log_output("\n".join(buf_lstrip_list), subtest)

    # Reverse the stripped buffer one more time and return it back as a string
    buf_rstrip_list.reverse()
    return "\n".join(buf_rstrip_list)


def _strip_log_output(output, strip_to):
    # Take logfile buffer and lstrip it down to a specified place
    skip = True
    buf_lstrip_list = []
    for line in output.split("\n"):
        if skip:
            if re.search(strip_to, line):
                skip = False
            else:
                continue
        buf_lstrip_list.append(line)

    return buf_lstrip_list
