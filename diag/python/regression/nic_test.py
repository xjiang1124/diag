#!/usr/bin/env python

import argparse
import pexpect
import re
import sys
import time
from collections import OrderedDict

sys.path.append("../lib")
import common
from nic_con import nic_con

class nic_test:
    def __init__(self):
        self.name = "nic_snake"
        self.baud_rate_org = 115200
        self.baud_rate = 4800
        self.num_retry = 10
        self.nic_con = nic_con()

    def setup_env(self, slot=0, mgmt=False, timeout=30, first_pwr_on=False):
        print "=== Starting snake on slot {} ===".format(slot)


        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        # Change baud rate to 4800
        ret = self.nic_con.change_rate_pw(self.baud_rate_org, self.baud_rate, slot)
        if ret != 0:
            print "Failed to change baud rate"
            return -1

        session = common.session_start()
        session.timeout = timeout
        self.nic_con.uart_session_start(session, self.baud_rate)
        self.nic_con.uart_session_cmd(session, "")
        self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data")
        self.nic_con.uart_session_cmd(session, "source /data/nic_arm/nic_setup_env.sh")
        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -w 1 0xe")
        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -r 1")
        self.nic_con.uart_session_cmd(session, "cd /data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
        self.nic_con.uart_session_stop(session)
        common.session_stop(session)

        if mgmt == True:
            ret = self.nic_con.get_mgmt_rdy(self.baud_rate, slot, first_pwr_on)

        print "=== Snake on slot {} env setup done ===".format(slot)

        return ret

    def pwr_cycle_test(self, slot=0, iteration=1):
        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        for i in range(iteration):
            print "=== Ite {} ===".format(i)
            ret = self.setup_env(slot, True, 30, True)
            if ret != 0:
                print "=== Power cycle test failed at ite {} ===".format(i)
                break

        if ret == 0:
            print "=== Power cycle test passed {} iterations ===".format(iteration)
        return ret

    def test_start(self, slot=0, test_type="snake", mode="hbm", timeout=30, vmarg=0):
        print "=== Starting snake on slot {} ===".format(slot)

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        if test_type == "snake" and mode == "hbm":
            test_cmd = "./diag.exe snake.h.a.tcl 2>&1 > snake_hbm.log &"
        elif test_type == "snake" and mode == "pcie":
            test_cmd = "./diag.exe snake.p.a.tcl 2>&1 > snake_pcie.log &"
        elif test_type == "prbs" and mode == "eth":
            test_cmd = "./diag.exe prbs.e.a.tcl 2>&1 > prbs_eth.log &"
        elif test_type == "prbs" and mode == "pcie":
            test_cmd = "./diag.exe prbs.p.a.tcl 2>&1 > prbs_pcie.log &"
        else:
            print "Invalid test_type {} and mdoe {}".format(test_type, mode)
            sys.exit(0)

        self.nic_con.change_rate_pw(self.baud_rate_org, self.baud_rate, slot)

        session = common.session_start()
        session.timeout = timeout
        self.nic_con.uart_session_start(session, self.baud_rate)
        self.nic_con.uart_session_cmd(session, "")
        self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data")
        self.nic_con.uart_session_cmd(session, "source /data/nic_arm/nic_setup_env.sh")
        if vmarg > 0:
            self.nic_con.uart_session_cmd(session, "/data/nic_arm/vmarg.sh high")
        elif vmarg < 0:
            self.nic_con.uart_session_cmd(session, "/data/nic_arm/vmarg.sh low")
        else:
            pass
        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -w 1 0xe")
        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -w 1 0xe")
        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -r 1")
        self.nic_con.uart_session_cmd(session, "cd /data/nic_arm/nic/asic_src/ip/cosim/tclsh/")

        session.sendline(test_cmd)
        session.sendline("\r")

        self.nic_con.uart_session_stop(session)

        common.session_stop(session)

        print "=== Snake on slot {} started ===".format(slot)

        return ret

    def test_check(self, slot=0, test_type="snake", mode="hbm", timeout=30):
        print "=== Checing snake result on slot {} ===".format(slot)
        session = common.session_start()

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        if test_type == "snake":
            exp_err_cnt = 3
            if mode == "hbm":
                log_name = "snake_hbm.log"
            else:
                log_name = "snake_pcie.log"
        else:
            exp_err_cnt = 0
            if mode == "eth":
                log_name = "prbs_eth.log"
            else:
                log_name = "prbs_pcie.log"

        session.timeout = timeout
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(1)

        self.nic_con.uart_session_start(session, self.baud_rate)

        check_cmd = "/data/nic_arm/check_snake.sh {} {}".format(log_name, exp_err_cnt)
        ret = self.nic_con.uart_session_cmd_sig(session, check_cmd, 3600, "\#", ["TEST Passed", "TEST Failed", "TEST Not Done"])
        print "ret:", ret
        self.nic_con.uart_session_stop(session)

        common.session_stop(session)

        print "=== Checing snake result on slot {} Done ===".format(slot)
        return ret

    def nic_test(self, nic_list=[], test_type="snake", mode="hbm", wait_time=180, vmargin=0):
        print "=== NIC Snake {} ===".format(mode)
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        test_result = OrderedDict()
        # Start snake
        for slot in nic_list:
            self.test_start(int(slot), test_type, mode, vmarg=vmargin)
            test_result[slot] = "No Result"

        print "Wait for {}s before checking result".format(wait_time)
        time.sleep(wait_time)

        done_count = 0
        for retry_idx in range(self.num_retry):
            print "Checking result:", retry_idx
            for slot in nic_list:
                if test_result[slot] != "No Result":
                    continue

                test_sts = self.test_check(int(slot), test_type, mode)
                if test_sts == 0:
                    print "=== Snake Result at Slot {}: Passed".format(slot)
                    test_result[slot] = "PASS"
                    done_count = done_count + 1
                if test_sts == 1:
                    print "=== Snake Result at Slot {}: Failed".format(slot)
                    test_result[slot] = "FAIL"
                    done_count = done_count + 1

            if done_count == len(nic_list):
                break
            time.sleep(30)

        # Print result
        print "\n====== TEST RESULT: {:<5} {:<5} ======".format(test_type.upper(), mode.upper())
        result_fmt = "Slot {:<2}: {:<5}"
        for slot, sts in test_result.items():
            print result_fmt.format(slot, sts)
        print "======================================"



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()

    group.add_argument("-snake_start", "--snake_start", help="Start snake", action='store_true')
    group.add_argument("-snake_check", "--snake_check", help="Check snake result", action='store_true')
    group.add_argument("-snake", "--snake", help="Run nic snake on multile nics", action='store_true')

    group.add_argument("-prbs_start", "--prbs_start", help="Start prbs", action='store_true')
    group.add_argument("-prbs_check", "--prbs_check", help="Check prbs result", action='store_true')
    group.add_argument("-prbs", "--prbs", help="Run nic prbs on multile nics", action='store_true')

    group.add_argument("-setup", "--setup", help="Set up nic env", action='store_true')
    group.add_argument("-pct", "--pwr_cycle_test", help="Power cycle test", action='store_true')

    parser.add_argument("-slot", "--slot", help="NIC slot number", type=int, default=0)
    parser.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser.add_argument("-wtime", "--wait_time", help="Wait time", type=int, default=300)
    parser.add_argument("-mgmt", "--mgmt", help="Set up management port", action='store_true')
    parser.add_argument("-mode", "--mode", help="Test mode: pcie/hbm; prbs: pcie/eth", type=str, default="hbm")
    parser.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=int, default=0)
    parser.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    parser.add_argument("-ite", "--iteration", help="Number of power cycle test iterations", type=int, default=1)

    args = parser.parse_args()

    test = nic_test()
    if args.snake_start == True:
        test.test_start(args.slot, "snake", args.mode, args.baud_rate)
        sys.exit()

    if args.snake_check == True:
        test.snake_check(args.slot, "snake", args.mode)
        sys.exit()

    if args.snake == True:
        slot_list = args.slot_list.split(',')
        test.nic_test(slot_list, "snake", args.mode, args.wait_time, vmargin=args.vmarg)
        sys.exit()

    if args.prbs_start == True:
        test.test_start(args.slot, "prbs", args.mode, args.baud_rate)
        sys.exit()

    if args.prbs_check == True:
        test.prbs_check(args.slot, "prbs", args.mode)
        sys.exit()

    if args.prbs == True:
        slot_list = args.slot_list.split(',')
        test.nic_test(slot_list, "prbs", args.mode, args.wait_time, vmargin=args.vmarg)
        sys.exit()

    if args.setup == True:
        test.setup_env(args.slot, args.mgmt, 30, args.first_pwr_on)
        sys.exit()

    if args.pwr_cycle_test == True:
        test.pwr_cycle_test(args.slot, args.iteration)
        sys.exit()

