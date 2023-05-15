import time
import os
import sys
import re
import threading
import traceback
from datetime import datetime
from libdefs import MTP_Const
from libmfg_cfg import *
from libmtp_db import mtp_db
import libmfg_utils

def load_mtp_cfg():
    mtp_chassis_cfg_file_list = list()
    if not GLB_CFG_MFG_TEST_MODE:
        mtp_chassis_cfg_file_list.append(os.path.abspath("config/qa_mtp_chassis_cfg.yaml"))
    mtp_cfg_db = mtp_db(mtp_chassis_cfg_file_list)
    return mtp_cfg_db

def mtpid_list_select(mtp_cfg_db, preselect=[]):
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    if preselect:
        sub_mtpid_list = list()
        for mtpid in preselect:
            if mtpid not in mtpid_list:
                cli_err("Invalid UUT ID: {:s}".format(mtpid))
            else:
                sub_mtpid_list.append(mtpid)
    else:
        sub_mtpid_list = multiple_select_menu("Select UUT Chassis", mtpid_list)
    return sub_mtpid_list

"""
    Run a function in parallel on multiple slots.


    Define the function as:
        @libtest_utils.parallel_threaded_test_section
        def function_name(test_ctrl, slot, ...):

    First two arguments MUST match exactly. Return value must be True/False.


    Call the function as:
        ret = function_name(test_ctrl, nic_list, ...)

"""
def parallel_threaded_test_section(func):

    def threaded_func(func, test_ctrl, slot, thread_rslt_list, *args, **kwargs):
        try:
            ###### RUN THE TEST #####
            ret = func(test_ctrl, slot, *args, **kwargs)
            #########################
            if ret:
                thread_rslt_list[slot] = True
            else:
                thread_rslt_list[slot] = False
        except Exception:
            thread_rslt_list[slot] = False
            err_msg = traceback.format_exc()
            test_ctrl.mtp_dump_nic_err_msg(slot, err_msg)

    def map_rslt_to_slot(thread_rslt_list):
        fail_nic_list = list()
        for idx, slot_rslt in enumerate(thread_rslt_list):
            if not slot_rslt:
                fail_nic_list.append(idx)
        return fail_nic_list

    def start_end(test_ctrl, nic_list=None, *test_args, **test_kwargs):
        nic_thread_list = list()
        thread_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM

        for slot in nic_list:
            thread_args = tuple([func, test_ctrl, slot, thread_rslt_list]) + test_args
            nic_thread = threading.Thread(
                target = threaded_func,
                args = thread_args,
                kwargs = test_kwargs
            )
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)
            time.sleep(1)

        # monitor all the thread
        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(1)

        return map_rslt_to_slot(thread_rslt_list)

    return start_end

"""
    Wrapper inside wrapper
    Run parallel test on ALL slots
    Return combined result: FAIL if any one slot failed
    This will NOT track which slot failed

    Define the function as:
        @libtest_utils.parallel_combined_test
        def function_name(test_ctrl, slot, ...):

    First two arguments MUST match exactly. Return value must be True/False.


    Call the function as:
        ret = function_name(test_ctrl, ...)
"""
def parallel_combined_test(func):
    @parallel_threaded_test_section
    def single_start_end(test_ctrl, slot, *args, **kwargs):
        return func(test_ctrl, slot, *args, **kwargs)

    def start_end(test_ctrl, *args, **kwargs):
        fail_nic_list = single_start_end(test_ctrl, range(test_ctrl.mtp._slots), *args, **kwargs)
        if fail_nic_list:
            return False
        return True

    return start_end
