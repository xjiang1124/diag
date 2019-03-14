#!/usr/bin/env python

import argparse
import pexpect
import re
import sys
import time

sys.path.append("../lib")
import common
from nic_con import nic_con

class nic_test:
    def __init__(self):
        self.name = "nic_snake"
        self.baud_rate_org = 115200
        self.baud_rate = 9600
        self.num_retry = 10
        self.nic_con = nic_con()

    def setup_env(self, slot=0, mgmt=False, timeout=30):
        print "=== Starting snake on slot {} ===".format(slot)

        session = common.session_start()

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        session.timeout = timeout
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(1)
        cmd = "turn_on_slot.sh off {}".format(slot)
        common.session_cmd(session, cmd) 
        cmd = "turn_on_slot.sh on {}".format(slot)
        common.session_cmd(session, cmd) 

        # Wait for nic to boot
        time.sleep(15)

        # Change baud rate to 9600
        self.nic_con.change_rate(self.baud_rate_org, self.baud_rate, slot)

        self.nic_con.uart_session_start(session, self.baud_rate)
        self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data")
        self.nic_con.uart_session_cmd(session, "source /data/nic_arm/nic_setup_env.sh")
        self.nic_con.uart_session_stop(session)
        common.session_stop(session)

        if mgmt == True:
            self.nic_con.get_mgmt_rdy(self.baud_rate, slot)

        print "=== Snake on slot {} env setup done ===".format(slot)

        return ret

    def snake_start(self, slot=0, mode="hbm", timeout=30):
        print "=== Starting snake on slot {} ===".format(slot)

        session = common.session_start()

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        session.timeout = timeout
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(1)
        cmd = "turn_on_slot.sh off {}".format(slot)
        common.session_cmd(session, cmd) 
        cmd = "turn_on_slot.sh on {}".format(slot)
        common.session_cmd(session, cmd) 

        # Wait for nic to boot
        time.sleep(15)

        # Change baud rate to 9600
        self.nic_con.change_rate(self.baud_rate_org, self.baud_rate, slot)

        self.nic_con.uart_session_start(session, self.baud_rate)
        self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data")
        self.nic_con.uart_session_cmd(session, "source /data/nic_arm/nic_setup_env.sh")
        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -w 1 0xe")
        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -r 1")
        self.nic_con.uart_session_cmd(session, "cd /data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
        #session.sendline("./diag.exe cap_snake.arm.test.tcl 2>&1 > snake.log &")
        if mode == "hbm":
            print "--- hbm ---"
            session.sendline("./diag.exe snake.h.a.tcl 2>&1 > snake.log &")
        else:
            print "--- pcie ---"
            #session.sendline("./diag.exe cap_snake.pcie.arm.tcl 2>&1 > snake.log &")
            session.sendline("./diag.exe snake.p.a.tcl 2>&1 > snake.log &")

        session.sendline("\r")
        self.nic_con.uart_session_stop(session)

        common.session_stop(session)

        print "=== Snake on slot {} started ===".format(slot)

        return ret

    def snake_check(self, slot=0, timeout=30):
        print "=== Checing snake result on slot {} ===".format(slot)
        session = common.session_start()

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        session.timeout = timeout
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(1)

        self.nic_con.uart_session_start(session, self.baud_rate)
        ret = self.nic_con.uart_session_cmd_sig(session, "/data/nic_arm/check_snake.sh", 3600, "\#", ["Snake Passed", "Snake Failed", "Test Not Done"])
        print "ret:", ret
        self.nic_con.uart_session_stop(session)

        common.session_stop(session)

        print "=== Checing snake result on slot {} Done ===".format(slot)
        return ret

    def nic_snake(self, nic_list=[], mode="hbm", wait_time=180):
        print "=== NIC Snake {} ===".format(mode)
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        # Start snake
        for slot in nic_list:
            self.snake_start(int(slot), mode)

        print "Wait for {}s before checking result".format(wait_time)
        time.sleep(wait_time)

        for retry_idx in range(self.num_retry):
            print "Checking result:", retry_idx
            for slot in nic_list:
                test_sts = self.snake_check(int(slot))
                if test_sts == 0 or test_sts == 1:
                    nic_list.remove(slot)
                if test_sts == 0:
                    print "=== Snake Result at Slot {}: Passed".format(slot)
                if test_sts == 1:
                    print "=== Snake Result at Slot {}: Failed".format(slot)
            if len(nic_list) == 0:
                break
            time.sleep(30)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()

    group.add_argument("-snake_start", "--snake_start", help="Start snake", action='store_true')
    group.add_argument("-snake_check", "--snake_check", help="Check snake result", action='store_true')
    group.add_argument("-snake", "--snake", help="Run nic snake on multile nics", action='store_true')
    group.add_argument("-setup", "--setup", help="Set up nic env", action='store_true')

    parser.add_argument("-slot", "--slot", help="NIC slot number", type=int, default=0)
    parser.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser.add_argument("-wtime", "--wait_time", help="Wait time", type=int, default=300)
    parser.add_argument("-mgmt", "--mgmt", help="Set up management port", action='store_true')
    parser.add_argument("-mode", "--mode", help="Test mode: snake: pcie/hbm; prbs: pcie/eth", type=str, default="hbm")

    args = parser.parse_args()

    test = nic_test()
    if args.snake_start == True:
        test.snake_start(args.slot, args.mode)
        sys.exit()

    if args.snake_check == True:
        test.snake_check(args.slot)
        sys.exit()

    if args.snake == True:
        slot_list = args.slot_list.split(',')
        test.nic_snake(slot_list, args.mode, args.wait_time)
        sys.exit()

    if args.setup == True:
        test.setup_env(args.slot, args.mgmt)
        sys.exit()

