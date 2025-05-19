import threading
import traceback
import time
from libdefs import MTP_Const
from libdefs import MTP_TYPE

"""
    This module has the following decorators for use

    @parallelize.sequential_nic_test                Run each slot sequentially on all MTP types
    @parallelize.parallel_nic_using_console         Run each slot sequentially on Rev01-Rev04 MTP & Turbo MTP. Run in parallel on Matera MTP.
    @parallelize.parallel_nic_using_ssh             Run each slot in parallel on all MTP types
    @parallelize.parallel_nic_using_nic_test        Run entire nic_list semi-sequential on Rev01-Rev04 MTP & Turbo MTP. Run fully parallel on Matera MTP.
    @parallelize.parallel_nic_using_j2c             Run each slot sequentially on Rev01-Rev04 MTP. Odd slots together and even slots together on Turbo. Fully parallel on Matera.
    @parallelize.parallel_nic_using_smbus           Same as "using_console".
"""


def sanitize_input(func, mtp_mgmt_ctrl, nic_list):
    if isinstance(nic_list, list):
        return nic_list
    elif isinstance(nic_list, int):
        slot = nic_list
        if 0 <= slot <= 9:
            return [slot]
        else:
            mtp_mgmt_ctrl.cli_log_err("Out-of-bound slot {} passed to {:s}".format(repr(nic_list), func), level=0)
            return []
    else:
        mtp_mgmt_ctrl.cli_log_err("Incorrect input {} when nic_list is needed for function {:s}".format(repr(nic_list),func), level=0)
        return []

def map_rslt_to_slot(rslt_list):
    # rslt_list as e.g. [True, True, False, False, True, True, True, True, True, True]
    # return fail_nic_list as e.g. [3,4]
    fail_nic_list = list()
    for idx, slot_rslt in enumerate(rslt_list):
        if not slot_rslt:
            fail_nic_list.append(idx)
    return fail_nic_list

def category_rslt_to_slot(rslt_list):
    # rslt_list as e.g. [99, 0, 1, 0, 99, 99, 1, -1, 0, 99]
    # return {-1:[7], 0:[2,3,8], 1:[2,6], 99:[0,4,5,9]}
    rs_nic_dict = {}
    for idx, slot_rslt in enumerate(rslt_list):
        if slot_rslt not in rs_nic_dict:
            rs_nic_dict[slot_rslt] = []
        rs_nic_dict[slot_rslt].append(idx)
    return rs_nic_dict

def sequential_nic_test(func):
    def single_slot_func(func, mtp_mgmt_ctrl, slot, test_rslt_list, *args, **kwargs):
        try:
            ###### RUN THE TEST #####
            ret = func(mtp_mgmt_ctrl, slot, *args, **kwargs)
            #########################
            if ret:
                test_rslt_list[slot] = True
            else:
                test_rslt_list[slot] = False
        except Exception:
            test_rslt_list[slot] = False
            err_msg = traceback.format_exc()
            mtp_mgmt_ctrl.cli_log_slot_err(slot, err_msg)

    def start_end(mtp_mgmt_ctrl, nic_list, *test_args, **test_kwargs):
        nic_list = sanitize_input(func, mtp_mgmt_ctrl, nic_list)
        test_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
        for slot in nic_list:
            single_slot_func(func, mtp_mgmt_ctrl, slot, test_rslt_list, *test_args, **test_kwargs)
        return map_rslt_to_slot(test_rslt_list)

    return start_end

def sequential_nic_test_category(func):
    def single_slot_category_func(func, mtp_mgmt_ctrl, slot, test_rslt_list, *args, **kwargs):
        try:
            ###### RUN THE TEST #####
            ret = func(mtp_mgmt_ctrl, slot, *args, **kwargs)
            #########################
            test_rslt_list[slot] = ret
        except Exception:
            test_rslt_list[slot] = -1
            err_msg = traceback.format_exc()
            mtp_mgmt_ctrl.cli_log_slot_err(slot, err_msg)

    def start_end(mtp_mgmt_ctrl, nic_list, *test_args, **test_kwargs):
        nic_list = sanitize_input(func, mtp_mgmt_ctrl, nic_list)
        test_rslt_list = [99] * MTP_Const.MTP_SLOT_NUM
        for slot in nic_list:
            single_slot_category_func(func, mtp_mgmt_ctrl, slot, test_rslt_list, *test_args, **test_kwargs)
        return category_rslt_to_slot(test_rslt_list)

    return start_end

def split_into_threads(func, mtp_mgmt_ctrl, nic_list, nic_as_list, *test_args, **test_kwargs):
    def single_thread_func(func, mtp_mgmt_ctrl, slot, thread_rslt_list, nic_as_list, *test_args, **test_kwargs):
        try:
            if nic_as_list:
                # send a single slot encased in a list []
                ret_list = func(mtp_mgmt_ctrl, [slot], *test_args, **test_kwargs)
                if slot in ret_list:
                    thread_rslt_list[slot] = False
            else:
                ret = func(mtp_mgmt_ctrl, slot, *test_args, **test_kwargs)
                if not ret:
                    thread_rslt_list[slot] = False
        except Exception:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Caught exception in single_thread_func")
            mtp_mgmt_ctrl.cli_log_slot_err(slot, traceback.format_exc())
            thread_rslt_list[slot] = False

    nic_thread_list = list()
    thread_rslt_list = [True] * MTP_Const.MTP_SLOT_NUM
    for slot in nic_list:
        thread_args = tuple([func, mtp_mgmt_ctrl, slot, thread_rslt_list, nic_as_list]) + test_args
        nic_thread = threading.Thread(
            target = single_thread_func,
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

def parallel_nic_using_ssh(func):
    """ Spawn threads for each slot, on all old and new MTP """
    def run_in_parallel(mtp_mgmt_ctrl, nic_list, *test_args, **test_kwargs):
        nic_list = sanitize_input(func, mtp_mgmt_ctrl, nic_list)
        fail_nic_list = split_into_threads(func, mtp_mgmt_ctrl, nic_list, False, *test_args, **test_kwargs)
        return fail_nic_list

    return run_in_parallel

def parallel_nic_using_console(func):
    """ Spawn threads for each slot on MTP with FPGA-based console access but keep sequential for old MTP """
    def pick_parallelism(mtp_mgmt_ctrl, nic_list, *test_args, **test_kwargs):
        nic_list = sanitize_input(func, mtp_mgmt_ctrl, nic_list)
        if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.MATERA:
            # run parallel
            fail_nic_list = split_into_threads(func, mtp_mgmt_ctrl, nic_list, False, *test_args, **test_kwargs)
        else:
            # run sequential
            fail_nic_list = list()
            for slot in nic_list:
                ret = func(mtp_mgmt_ctrl, slot, *test_args, **test_kwargs)
                if not ret:
                    fail_nic_list.append(slot)
        return fail_nic_list

    return pick_parallelism

def parallel_nic_using_nic_test(func):
    """ Spawn threads for each slot on new MTP with FPGA-based console access but keep semi-parallel for old MTP """
    def pick_parallelism(mtp_mgmt_ctrl, nic_list, *test_args, **test_kwargs):
        nic_list = sanitize_input(func, mtp_mgmt_ctrl, nic_list)
        if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.MATERA:
            # run true parallel
            fail_nic_list = split_into_threads(func, mtp_mgmt_ctrl, nic_list, True, *test_args, **test_kwargs)
        else:
            # run semi-parallel
            fail_nic_list = func(mtp_mgmt_ctrl, nic_list, *test_args, **test_kwargs)
        return fail_nic_list

    return pick_parallelism

def parallel_nic_using_smbus(func):
    """ For tests limited by the shared smbus. FPGA allows parallel access, but not recommended on old MTP """
    return parallel_nic_using_console(func)

def parallel_nic_using_j2c(func):
    """ Spawn threads for each slot on new MTP, odd/even slots for Tubro, and sequential for non-Turbo MTP """
    def pick_parallelism(mtp_mgmt_ctrl, nic_list, *test_args, **test_kwargs):
        nic_list = sanitize_input(func, mtp_mgmt_ctrl, nic_list)
        if mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.MATERA:
            # run parallel
            fail_nic_list = split_into_threads(func, mtp_mgmt_ctrl, nic_list, False, *test_args, **test_kwargs)
        elif mtp_mgmt_ctrl.mtp_get_mtp_type() == MTP_TYPE.TURBO_ELBA:
            # run odd slots together and even slots together
            top_nic_list = [x for x in nic_list if x in [0,2,4,6,8]] # odd slots
            bot_nic_list = [x for x in nic_list if x in [1,3,5,7,9]] # even slots
            top_fail_list = split_into_threads(func, mtp_mgmt_ctrl, top_nic_list, False, *test_args, **test_kwargs)
            bot_fail_list = split_into_threads(func, mtp_mgmt_ctrl, bot_nic_list, False, *test_args, **test_kwargs)
            fail_nic_list = top_fail_list + bot_fail_list
        else:
            # run sequential
            fail_nic_list = list()
            for slot in nic_list:
                ret = func(mtp_mgmt_ctrl, slot, *test_args, **test_kwargs)
                if not ret:
                    fail_nic_list.append(slot)
        return fail_nic_list

    return pick_parallelism