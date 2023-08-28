#!/usr/bin/env python

import argparse
import datetime
import math
import pexpect
import os
import re
import sys

from collections import OrderedDict
from time import sleep

import datetime

sys.path.append("../lib")
import common
from nic_con import nic_con
from nic_test import nic_test

class arm_prbs:
    def __init__(self):
        self.name = "NIC PCIE"
        self.baud_rate = 115200
        self.nic_con = nic_con()
        self.nic_test = nic_test()

    def test_start(self, slot=0, vmarg='normal', lpbk=0, dura=60, poly="PRBS31", mode="PCIE"):
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)
        ret = 0
        print "=== Starting NIC arm {} prbs {} {} on slot {} ===".format(mode, dura, lpbk, slot)

        session = common.session_start()
        try:
            session.timeout = 30
            self.nic_con.uart_session_start_slot(session, self.baud_rate, slot)
            vmarg = vmarg.replace('_', ' ')
            self.nic_con.uart_session_cmd(session, "/data/nic_arm/vmarg.sh {}".format(vmarg))
            self.nic_con.uart_session_cmd(session, "/data/nic_arm/nic/asic_src/ip/cosim/tclsh/nic_prbs.sh {} {} {} &".format(mode, dura, lpbk))
            self.nic_con.uart_session_stop(session)

            print "=== NIC arm {} prbs on slot {} started ===".format(mode, slot)
        except:
            self.nic_con.uart_session_stop(session)
            print "=== NIC arm {} prbs on slot {} FAILED to start! ===".format(mode, slot)
            common.session_stop(session)
            ret = -1

        common.session_stop(session)
        return ret

    def test_check(self, slot=0, mode="PCIE", timeout=30):
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)
        ret = 0
        print "=== ARM {} prbs Checking result on slot {} ===".format(mode, slot)

        self.nic_con.switch_console(slot)
        session = common.session_start()
        ret = self.nic_con.uart_session_start(session)
        if ret != 0:
            self.nic_con.uart_session_stop(session)
            common.session_stop(session)
            return -1
 
        ret = self.nic_con.uart_session_cmd(session, "sync")
        if os.environ['ASIC_TYPE'] == "GIGLIO":
            asic_name = "giglio"
        else:
            asic_name = "elba"
        if mode == "PCIE":
            cmd = "tail -5 /data/nic_arm/nic/asic_src/ip/cosim/tclsh/{}_PRBS_PCIE.log".format(asic_name)
            ret = self.nic_con.uart_session_cmd_sig(session, cmd, 5, "\#", ["PCIE PRBS PASSED", "FAILED"], False)
        elif mode == "ETH":
            cmd = "tail -5 /data/nic_arm/nic/asic_src/ip/cosim/tclsh/{}_PRBS_MX.log".format(asic_name)
            ret = self.nic_con.uart_session_cmd_sig(session, cmd, 5, "\#", ["MX PRBS PASSED", "FAILED"], False)
        else:
            print "Invalid test type for checking result!!!"
            return -1

        if ret == 0:
            print "ARM {} PRBS TEST PASSED".format(mode)
            print "ARM {} PRBS TEST PASSED".format(mode)
        elif ret == 1:
            print "ARM {} PRBS TEST FAILED".format(mode)
        else:
            print "ARM {} PRBS NO RESULT in log file or no log file found".format(mode)

        self.nic_con.uart_session_stop(session)
        common.session_stop(session)

        print "check_result:"
        print "=== ARM {} PRBS Checking result on slot {} Done ===".format(mode, slot)
        return ret

    def arm_prbs(self, slot_list=[], wait_time=300, vmargin='normal', lpbk=0, dura=60, poly="PRBS31", mode="PCIE", no_pwr_cycle=False):
        print "=== ARM {} PRBS {} {} {}".format(mode, dura, lpbk, vmargin)
        if len(slot_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        print "slot:", slot_list
        nic_list_remain = slot_list[:]
        nic_failed_setup = slot_list[:]
        nic_passed_setup = slot_list[:]
        ret, nic_passed_setup, nic_failed_setup = self.nic_test.setup_env_multi_top(slot_list, False, 30, False, no_pwr_cycle, False, False, "elba", False, False)

        # initialize all slots to FAIL
        test_result = OrderedDict()
        for slot in slot_list:
            test_result[slot] = "FAIL"

        # not testing on failed setup slots
        for slot in nic_failed_setup:
            nic_list_remain.remove(slot)

        # Start L1 
        for slot in nic_list_remain:
            ret = self.test_start(int(slot), vmargin, lpbk, dura, poly, mode)
            if ret == 0:
                test_result[slot] = "NO RESULT"

        print "Wait for {}s before checking result".format(wait_time)
        sleep(wait_time)

        print "Checking result:"
        for slot in slot_list:
            if test_result[slot] != "NO RESULT":
                continue

            test_sts = self.test_check(int(slot), mode)
            if test_sts == 0:
                print "=== Result at Slot {}: Passed".format(slot)
                test_result[slot] = "PASSED"
            if test_sts == 1:
                print "=== Result at Slot {}: Failed".format(slot)
                test_result[slot] = "FAILED"

        # Print result
        print "\n====== NIC ARM {} PRBS TEST RESULT: ======".format(mode)
        result_fmt = "Slot {:<2}: {:<5}"
        for slot, sts in test_result.items():
            print result_fmt.format(slot, sts)
        print "======================================"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARM PRBS Interface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-test_start", "--prbs_start", help="Start arm pcie test", action='store_true')
    group.add_argument("-test_check", "--prbs_check", help="Check arm pcie result", action='store_true')
    group.add_argument("-arm_prbs", "--arm_prbs", help="Run ARM PRBS", action='store_true')

    parser.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser.add_argument("-wtime", "--wait_time", help="Wait time", type=int, default=300)
    parser.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=str, default='normal')
    parser.add_argument("-no_pc", "--no_pwr_cycle", help="Test with Power Cycle", action='store_false')

    parser.add_argument("-lpbk", "--lpbk", help="Loop Back Level", type=int, default=0)
    parser.add_argument("-dura", "--dura", help="Duration", type=int, default=60)
    parser.add_argument("-poly", "--poly", help="Polynomial", type=str, default="PRBS31")
    parser.add_argument("-mode", "--mode", help="PRBS Type", type=str, default="PCIE")

    args = parser.parse_args()

    test = arm_prbs()
    slot_list = args.slot_list.split(',')
    if args.prbs_start == True:
        for slot in args.slot_list:
            test.test_start(int(slot), args.vmarg, args.lpbk, args.dura, args.poly, args.mode)
        sys.exit()

    if args.prbs_check == True:
        for slot in args.slot_list:
            test.test_check(int(slot), args.mode)
        sys.exit()

    if args.arm_prbs == True:
        test.arm_prbs(slot_list, args.wait_time, args.vmarg, args.lpbk, args.dura, args.poly, args.mode, args.no_pwr_cycle)
        sys.exit()
