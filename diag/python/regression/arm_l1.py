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

class arm_l1:
    def __init__(self):
        self.name = "NIC arm L1"
        self.baud_rate = 115200
        self.nic_con = nic_con()
        self.nic_test = nic_test()

    def test_start(self, slot=0, vmarg='normal', sn='SN00000000', mode='hod'):
        print "=== Starting NIC arm L1 on slot {} ===".format(slot)

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        session = common.session_start()
        try:
            session.timeout = 30
            self.nic_con.uart_session_start_slot(session, self.baud_rate, slot)
            self.nic_con.uart_session_cmd(session, "/data/nic_arm/vmarg.sh {}".format(vmarg))
            self.nic_con.uart_session_cmd(session, "cd /data/nic_arm/nic/asic_src/ip/cosim/tclsh")
            self.nic_con.uart_session_cmd(session, "./diag.exe ../elba/elb_arm_l1.tcl {} {} 1 &".format(sn, mode))
            self.nic_con.uart_session_stop(session)

            print "=== NIC arm L1 on slot {} started ===".format(slot)
        except:
            self.nic_con.uart_session_stop(session)
            print "=== NIC arm L1 on slot {} FAILED to start! ===".format(slot)
            common.session_stop(session)
            ret = -1

        common.session_stop(session)
        return ret

    def test_check(self, slot=0, timeout=30):
        print "=== ARM L1 Checking result on slot {} ===".format(slot)

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        self.nic_con.switch_console(slot)
        session = common.session_start()
        ret = self.nic_con.uart_session_start(session)
        if ret != 0:
            self.nic_con.uart_session_stop(session)
            common.session_stop(session)
            return -1
 
        cmd = "tail -5 /data/nic_arm/nic/asic_src/ip/cosim/tclsh/elba_arm_l1_test.log"
        ret = self.nic_con.uart_session_cmd_sig(session, cmd, 5, "\#", ["ARM L1 TESTS PASSED", "FAILED"], False)
        if ret == 0:
            print "ARM L1 TESTS PASSED"
        elif ret == 1:
            print "ARM L1 TESTS FAILED"
        else:
            print "ARM L1 NO RESULT in log file or no log file found"

        self.nic_con.uart_session_stop(session)
        common.session_stop(session)

        print "check_result:"
        print "=== ARM L1 Checking result on slot {} Done ===".format(slot)
        return ret

    def arm_l1(self, slot_list=[], wait_time=300, vmargin='normal', sn="SN00000000", mode="hod", no_pwr_cycle=False):
        print "=== ARM L1"
        if len(slot_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        print "slot:", slot_list
        nic_list_remain = slot_list[:]
        nic_failed_setup = slot_list[:]
        #ret, nic_list_remain = self.setup_env_multi(slot_list, no_pwr_cycle)
        ret, nic_failed_setup = self.nic_test.setup_env_multi_top(slot_list, False, 30, False, no_pwr_cycle, False, False, "elba", False, False)

        # initialize all slots to FAIL
        test_result = OrderedDict()
        for slot in slot_list:
            test_result[slot] = "FAIL"

        # not testing on failed setup slots
        for slot in nic_failed_setup:
            nic_list_remain.remove(slot)

        # Start L1 
        for slot in nic_list_remain:
            ret = self.test_start(int(slot), vmargin)
            if ret == 0:
                test_result[slot] = "NO RESULT"

        print "Wait for {}s before checking result".format(wait_time)
        sleep(wait_time)

        print "Checking result:"
        for slot in slot_list:
            if test_result[slot] != "NO RESULT":
                continue

            test_sts = self.test_check(int(slot))
            if test_sts == 0:
                print "=== Result at Slot {}: Passed".format(slot)
                test_result[slot] = "PASSED"
            if test_sts == 1:
                print "=== Result at Slot {}: Failed".format(slot)
                test_result[slot] = "FAILED"

        # Print result
        print "\n====== NIC ARM L1 TEST RESULT: ======"
        result_fmt = "Slot {:<2}: {:<5}"
        for slot, sts in test_result.items():
            print result_fmt.format(slot, sts)
        print "======================================"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARM L1 Interface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-test_start", "--l1_start", help="Start arm l1 test", action='store_true')
    group.add_argument("-test_check", "--l1_check", help="Check arm l1 result", action='store_true')
    group.add_argument("-arm_l1", "--arm_l1", help="Run ARM L1", action='store_true')

    parser.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser.add_argument("-wtime", "--wait_time", help="Wait time", type=int, default=300)
    parser.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=str, default='normal')
    parser.add_argument("-no_pc", "--no_pwr_cycle", help="Test with Power Cycle", action='store_false')

    parser.add_argument("-sn", "--sn", help="Serian Number", type=str, default="SN00000000")
    parser.add_argument("-mod", "--mod", help="L1 mode", type=str, default="hod")

    args = parser.parse_args()

    test = arm_l1()
    slot_list = args.slot_list.split(',')
    if args.l1_start == True:
        test.test_start(slot_list, args.wait_time, args.vmarg)
        sys.exit()

    if args.l1_check == True:
        test.test_check(args.slot)
        sys.exit()

    if args.arm_l1 == True:
        test.arm_l1(slot_list, args.wait_time, args.vmarg, args.sn, args.mod, args.no_pwr_cycle)
        sys.exit()
