import pexpect
import time
import os
import sys
import re
import threading
from datetime import datetime

PRINT_TEST_HISTORY = 'PRINT_HISTORY'
CLEAR_TEST_HISTORY = 'CLEAR_HISTORY'

# executed a single time for every testcase, upon initalization with @...
# keep track of metadata higher than test-level
def single_slot_test(dsp, test):
  test_result_list = dict()

  # executed a single time for every testcase, upon initalization with @...
  # keep track of test-specific metadata
  def middle_wrapper(func):
    slots_done = list()

    # executed at every call
    def start_end(mtp_mgmt_ctrl, slot=None, operation="", *args, **kwargs):

      if slot is None and operation != "":
        if mtp_mgmt_ctrl._id not in test_result_list.keys():
          return list()

        if operation == PRINT_TEST_HISTORY:
          print("Getting history of {:s}".format(test))
          return test_result_list[mtp_mgmt_ctrl._id]

        if operation == CLEAR_TEST_HISTORY:
          print("Clearing history of {:s}".format(test))
          test_result_list[mtp_mgmt_ctrl._id] = list()
          return list()

      #else:
      start_ts = mtp_mgmt_ctrl.log_slot_test_start(slot, test)
      ret = func(mtp_mgmt_ctrl, slot, *args, **kwargs)
      duration = mtp_mgmt_ctrl.log_slot_test_stop(slot, test, start_ts)

      slots_done.append(slot)
      if mtp_mgmt_ctrl._id not in test_result_list.keys():
        test_result_list[mtp_mgmt_ctrl._id] = list()
      test_result_list[mtp_mgmt_ctrl._id].append((slot,dsp,test,ret,str(duration)))

      return ret

    return start_end

  return middle_wrapper

# executed a single time for every testcase, upon initalization with @...
# keep track of metadata higher than test-level
def single_uut_test(dsp, test):
  test_result_list = dict()

  # executed a single time for every testcase, upon initalization with @...
  # keep track of test-specific metadata
  def middle_wrapper(func):
    example_metadata_list = list()

    # executed at every call
    def start_end(mtp_mgmt_ctrl, operation="", *args, **kwargs):

      if operation != "":
        if mtp_mgmt_ctrl._id not in test_result_list.keys():
          return list()

        if operation == PRINT_TEST_HISTORY:
          print("Getting history of {:s}".format(test))
          return test_result_list[mtp_mgmt_ctrl._id]

        if operation == CLEAR_TEST_HISTORY:
          print("Clearing history of {:s}".format(test))
          test_result_list[mtp_mgmt_ctrl._id] = list()
          return list()

      #else:
      start_ts = mtp_mgmt_ctrl.log_test_start(test)
      ret = func(mtp_mgmt_ctrl, *args, **kwargs)
      duration = mtp_mgmt_ctrl.log_test_stop(test, start_ts)

      if mtp_mgmt_ctrl._id not in test_result_list.keys():
        test_result_list[mtp_mgmt_ctrl._id] = list()
      test_result_list[mtp_mgmt_ctrl._id].append((dsp,test,ret,str(duration)))

      return ret

    return start_end

  return middle_wrapper