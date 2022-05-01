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

class arm_ddrbist:
    def __init__(self):
        self.name = "arm ddrbist"
        self.baud_rate = 115200
        self.nic_con = nic_con()

    def setup_env(self, slot=0, ddr_freq=3200, addrspace=34, dualrank=0, ddr5=0, ctrl_pi_bitmask=0xC, timeout=300):
        print "=== Starting setup env on slot {} ===".format(slot)

        try:
            self.nic_con.switch_console(int(slot))
            session = common.session_start()
            session.timeout = timeout
            cmd = "turn_on_hub.sh {}".format(slot)
            common.session_cmd_no_rc(session, cmd)
            sleep(0.5)

            ret = self.nic_con.uart_session_start(session, self.baud_rate)
            if ret == 0:
                self.nic_con.uart_session_cmd(session, "source /data/nic_arm/nic_setup_env.sh", 120)
                self.nic_con.uart_session_cmd(session, "source /etc/profile", 10)
                self.nic_con.uart_session_cmd(session, "echo \'{} {} {} {} {}\' > /data/ddrbist_config.txt".format(ddr_freq, addrspace, dualrank, ddr5, ctrl_pi_bitmask))
            else:
                self.nic_con.uart_session_stop(session)
                common.session_stop(session)
                return -1

            self.nic_con.uart_session_stop(session)
            common.session_stop(session)

            print "=== Setup env on slot {} env setup done ===".format(slot)

        except pexpect.TIMEOUT:
            print "=== TIMEOUT: Failed to set up env slot {} ===".format(slot)
            ret = -1

        return ret

    def setup_env_multi(self, nic_list=[], ddr_freq=3200, addrspace=34, dualrank=0, ddr5=0, ctrl_pi_bitmask=0xC):
        ret_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        nic_list_remain = nic_list[:]
        slot_list = ",".join(nic_list)

        self.nic_con.power_cycle_multi(self.baud_rate, slot_list)

        for slot in nic_list:
            ret = self.setup_env(int(slot), ddr_freq, addrspace, dualrank, ddr5, ctrl_pi_bitmask)
            ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret

        for slot in nic_list:
            if ret_list[int(slot)-1] == 0:
                nic_list_remain.remove(slot)

        print "timestamp", datetime.datetime.now().time()
        return ret, nic_list_remain

    def test_start(self, slot=0, vmarg='normal'):
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)
        print "=== Starting ddr bist on slot {} ===".format(slot)
        ret = 0

        self.nic_con.switch_console(int(slot))
        session = common.session_start()
        session.timeout = 400
        cmd = "turn_on_hub.sh {}".format(slot)
        common.session_cmd_no_rc(session, cmd)

        try:
            ret = self.nic_con.uart_session_start(session, self.baud_rate)
            if ret != 0:
                print "==failed to start uart session=="
                self.nic_con.uart_session_stop(session)
                common.session_stop(session)
                return -1
            self.nic_con.uart_session_cmd(session, "echo \'{}\' > /data/ddrbist_vmarg.txt".format(vmarg))
            self.nic_con.uart_session_cmd(session, "touch /data/ddrbist_run_valid")
            self.nic_con.uart_session_cmd(session, "echo \'0\' > /data/current_chan")
            self.nic_con.uart_session_cmd(session, "echo \'1\' > /data/next_chan")
            self.nic_con.uart_session_cmd(session, "fwenv -n gold -E")
            self.nic_con.uart_session_cmd(session, "fwenv -n gold -s noc_llc_pin 0")
            self.nic_con.uart_session_cmd(session, "fwenv -n gold -s run_ddrbist_ok 1")
            self.nic_con.uart_session_cmd(session, "cp /data/nic_util/run_ddrbist.sh /data/pensando_pre_init.sh")
            self.nic_con.uart_session_cmd(session, "sysreset.sh")
            self.nic_con.uart_session_stop(session)

            print "=== DDR BIST on slot {} started ===".format(slot)
        except:
            self.nic_con.uart_session_stop(session)
            print "=== DDR BIST on slot {} FAILED to start! ===".format(slot)
            common.session_stop(session)
            ret = -1

        common.session_stop(session)
        return ret

    def test_check(self, slot=0, timeout=30):
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)
        print "=== DDR BIST Checking result on slot {} ===".format(slot)
        ret = 0
        rc = 0

        self.nic_con.switch_console(slot)
        session = common.session_start()
        ret = self.nic_con.uart_session_start(session, self.baud_rate)
        if ret != 0:
            self.nic_con.uart_session_stop(session)
            common.session_stop(session)
            return -1

        cmd = "cat /data/ddrbist_status"
        ret = self.nic_con.uart_session_cmd_sig(session, cmd, 15, "\#", ["FINISHED", "RUNNING"], False)
        if ret != 0:
            rc = 3
            return rc
        
        session.sendline("rm /data/ddrbist_status")
        cmd = "tail -5 /data/nic_arm/nic/asic_src/ip/cosim/tclsh/arm_ddr_bist_1.log"
        ret = self.nic_con.uart_session_cmd_sig(session, cmd, 15, "\#", ["DDR BIST PASSED", "FAILED"], False)
        if ret == 1:
            print "DDR BIST failed channel 0"
            rc = 1
 
        self.nic_con.uart_session_cmd(session, "sync")
        cmd = "tail -5 /data/nic_arm/nic/asic_src/ip/cosim/tclsh/arm_ddr_bist_0.log"
        ret = self.nic_con.uart_session_cmd_sig(session, cmd, 15, "\#", ["DDR BIST PASSED", "FAILED"], False)
        if ret == 1:
            print "DDR BIST failed channel 1"
            rc = rc + 1

        self.nic_con.uart_session_stop(session)
        common.session_stop(session)

        print "check_result:", rc
        print "=== DDR BIST Checing result on slot {} Done ===".format(slot)
        return rc

    def arm_ddrbist(self, slot_list=[], wait_time=300, vmargin='normal', ddr_freq=3200, addrspace=34, dualrank=0, ddr5=0, ctrl_pi_bitmask=0xC):
        print "=== NIC DDR bist"
        if len(slot_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        print "slot:", slot_list
        nic_list_remain = slot_list[:]
        ret, nic_failed_setup = self.setup_env_multi(slot_list, ddr_freq, addrspace, dualrank, ddr5, ctrl_pi_bitmask)

        # initialize all slots to FAIL as default
        test_result = OrderedDict()
        for slot in slot_list:
            test_result[slot] = "FAIL"

        # not testing on filed setup slots
        for slot in nic_failed_setup:
            nic_list_remain.remove(slot)

        # Start DDR bist 
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
        print "\n====== DDR BIST TEST RESULT: ======"
        result_fmt = "Slot {:<2}: {:<5}"
        for slot, sts in test_result.items():
            print result_fmt.format(slot, sts)
        print "======================================"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DDR bist inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-test_start", "--ddr_start", help="Start DDR bist", action='store_true')
    group.add_argument("-test_check", "--ddr_check", help="Check DDR bist result", action='store_true')
    group.add_argument("-arm_ddrbist", "--arm_ddrbist", help="Run DDR bist on multile nics", action='store_true')

    parser.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser.add_argument("-wtime", "--wait_time", help="Wait time", type=int, default=300)
    parser.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=str, default='normal')

    parser.add_argument("-ddr_freq", "--ddr_freq", help="DDR frequency", type=int, default=3200)
    parser.add_argument("-addrspace", "--addrspace", help="DDR size", type=int, default=34)
    parser.add_argument("-dualrank", "--dualrank", help="rank type", type=int, default=0)
    parser.add_argument("-ddr5", "--ddr5", help="DDR type", type=int, default=0)
    parser.add_argument("-ctrl_pi_bitmask", "--ctrl_pi_bitmask", help="bit mask", type=int, default=0xC)

    args = parser.parse_args()

    test = arm_ddrbist()
    slot_list = args.slot_list.split(',')
    if args.ddr_start == True:
        for slot in args.slot_list:
            test.test_start(int(slot), args.wait_time, args.vmarg)
        sys.exit()

    if args.ddr_check == True:
        for slot in args.slot_list:
            test.test_check(int(slot))
        sys.exit()

    if args.arm_ddrbist == True:
        test.arm_ddrbist(slot_list, args.wait_time, args.vmarg, args.ddr_freq, args.addrspace, args.dualrank, args.ddr5, args.ctrl_pi_bitmask)
        sys.exit()
