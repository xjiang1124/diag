import pexpect
import time
import os
import sys
import re
import libmfg_utils
import traceback
from libdefs import MTP_Const

def collect_err_msg(mtp_mgmt_ctrl, vmarg=None):
    try:
        collect_diag_err_msg(mtp_mgmt_ctrl)
        collect_dsp_err_msg(mtp_mgmt_ctrl, vmarg) # for 2C only
        collect_nic_err_msg(mtp_mgmt_ctrl, 0)
        collect_nic_err_msg(mtp_mgmt_ctrl, 1)

        print(mtp_mgmt_ctrl.get_err_msg())
    except:
        err_msg = traceback.format_exc()
        mtp_mgmt_ctrl.cli_log_err(err_msg)
        return False
    return True

def collect_diag_err_msg(mtp_mgmt_ctrl):
    buf = read_entire_logfile(mtp_mgmt_ctrl, "mtp_diag.log")
    err_msg_list = cleanup(re.findall(r"(\[ERROR\] .*)", buf))
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
