#!/usr/bin/env python

import argparse
import pexpect
import re
import sys
import time
from collections import OrderedDict
from time import sleep

import datetime

sys.path.append("../lib")
import common
from nic_con import nic_con

class nic_test:
    def __init__(self):
        self.name = "nic_snake"
        self.baud_rate = 115200
        self.num_retry = 30
        self.nic_con = nic_con()

    def setup_env(self, slot=0, mgmt=False, timeout=30, first_pwr_on=False, pwr_cycle=True, aapl=False):
        print "=== Starting setup env on slot {} ===".format(slot)

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        if pwr_cycle == True:
            ret = self.nic_con.power_cycle_uart(self.baud_rate, slot)
            if ret != 0:
                print "Failed to change baud rate"
                return -1

        self.nic_con.switch_console(int(slot))

        session = common.session_start()
        session.timeout = timeout
        self.nic_con.uart_session_start(session, self.baud_rate)
        self.nic_con.uart_session_cmd(session, "")
        self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data")
        self.nic_con.uart_session_cmd(session, "source /data/nic_arm/nic_setup_env.sh", 120)
        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -w 1 0xe")
        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -r 1")
        self.nic_con.uart_session_cmd(session, "cd /data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
        self.nic_con.uart_session_cmd(session, "export PCIE_ENABLED_PORTS=0")
        self.nic_con.uart_session_stop(session)
        common.session_stop(session)

        if aapl == True:
            ret = self.aapl_setup(self.baud_rate, slot)
            if ret != 0:
                return ret

        if mgmt == True:
            ret = self.nic_con.get_mgmt_rdy(self.baud_rate, slot, first_pwr_on)

        print "=== Setup env on slot {} env setup done ===".format(slot)

        return ret

    def setup_env_multi_top(self, nic_list=[], mgmt=False, timeout=30, first_pwr_on=False, pwr_cycle=True, aapl=False):
        numRetry = 1
        nic_list_remain = nic_list[:]
        for retry in range(numRetry):
            print "Setting up #{}".format(retry)
            ret, nic_list_remain = self.setup_env_multi_2(nic_list_remain, mgmt, timeout, first_pwr_on, pwr_cycle, aapl)
            if ret == 0:
                break
        if ret != 0:
            print "=== Setup env top failed!", ",".join(nic_list_remain)
        else:
            print "=== Setup env top done ==="

        return ret

    def setup_env_multi_1(self, nic_list=[], mgmt=False, timeout=30, first_pwr_on=False, pwr_cycle=True, aapl=False):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        nic_list_remain = nic_list[:]
        slot_list = ",".join(nic_list)
        print "slot_list:", slot_list

        if pwr_cycle == True:
            self.nic_con.power_cycle_multi(self.baud_rate, slot_list)

        for slot in nic_list:
            ret = self.setup_env(int(slot), False, 30, False, False, False)

        for slot in nic_list:
            skip = False
            ret1 = 0

            if aapl == True:
                ret1 = self.aapl_setup(self.baud_rate, int(slot), skip)
                ret = ret + ret1

            # if failed, go to the next one
            if ret1 != 0:
                continue

            if mgmt == True:
                self.nic_con.switch_console(slot)
                ret1 = ret1 + self.nic_con.get_mgmt_rdy(self.baud_rate, int(slot), first_pwr_on)
                ret = ret + ret1

            if ret1 == 0:
                nic_list_remain.remove(slot)

        if ret != 0:
            print "===  setup_env_multi {} failed; failed slot:", ",".join(nic_list_remain)
        else:
            print "===  setup_env_multi Passed ==="

        return ret, nic_list_remain

    def setup_env_multi_2(self, nic_list=[], mgmt=False, timeout=30, first_pwr_on=False, pwr_cycle=True, aapl=False):
        ret_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        nic_list_remain = nic_list[:]
        slot_list = ",".join(nic_list)
        print "slot_list:", slot_list

        if pwr_cycle == True:
            self.nic_con.power_cycle_multi(self.baud_rate, slot_list)

        for slot in nic_list:
            ret = self.setup_env(int(slot), False, 30, False, False, False)

        if mgmt == True:
            for slot in nic_list:
                self.nic_con.switch_console(slot)
                set = self.nic_con.enable_mnic(self.baud_rate, int(slot), first_pwr_on)
        elif aapl == True and mgmt == False:
            for slot in nic_list:
                self.nic_con.switch_console(slot)

                session = common.session_start()
                self.nic_con.uart_session_start(session)

                self.nic_con.uart_session_cmd(session, "sysinit.sh classic hw diag")

                self.nic_con.uart_session_stop(session)
                common.session_stop(session)

        if mgmt == True or aapl == True:
                self.nic_con.switch_console(slot)
                session = common.session_start()
                self.nic_con.uart_session_start(session)

                print "Sleep 30 sec"
                time.sleep(30)

                # Disable link manager
                self.nic_con.uart_session_cmd(session, "halctl debug port --port 1 --admin-state down")
                self.nic_con.uart_session_cmd(session, "halctl debug port --port 5 --admin-state down")
                self.nic_con.uart_session_cmd(session, "halctl show port status")
                sleep(0.5)

                self.nic_con.uart_session_stop(session)
                common.session_stop(session)

        if aapl == True:
            for slot in nic_list:
                ret = self.aapl_setup(self.baud_rate, int(slot), True)
                if ret != 0:
                    ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret

        if mgmt == True:
            for slot in nic_list:
                ret = self.nic_con.get_mgmt_rdy(self.baud_rate, int(slot), first_pwr_on, True)
                if ret != 0:
                    ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret

        for slot in nic_list:
            if ret_list[int(slot)-1] == 0:
                nic_list_remain.remove(slot)
            ret = ret + ret_list[int(slot)-1]

        if ret != 0:
            print "===  setup_env_multi {} failed; failed slot:", ",".join(nic_list_remain)
        else:
            print "===  setup_env_multi Passed ==="

        return ret, nic_list_remain

    def setup_env_multi(self, nic_list=[], mgmt=False, timeout=30, first_pwr_on=False, pwr_cycle=True, aapl=False):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        nic_list_remain = nic_list[:]
        slot_list = ",".join(nic_list)
        print "slot_list:", slot_list

        if pwr_cycle == True:
            self.nic_con.power_cycle_multi(self.baud_rate, slot_list)

        for slot in nic_list:
            ret = self.setup_env(int(slot), False, 30, False, False, False)

        if mgmt == True:
            for slot in nic_list:
                self.nic_con.switch_console(slot)
                set = self.nic_con.enable_mnic(self.baud_rate, int(slot), first_pwr_on)

        if mgmt == False and aapl == True:
            for slot in nic_list:
                self.nic_con.switch_console(slot)

                session = common.session_start()
                self.nic_con.uart_session_start(session, self.baud_rate)
                self.nic_con.uart_session_cmd(session, "sysinit.sh classic hw diag")
                self.nic_con.uart_session_stop(session)

                common.session_stop(session)

        if mgmt == True or aapl == True:
            time.sleep(60)

        if mgmt == True:
            for slot in nic_list:
                ret = self.nic_con.get_mgmt_rdy(self.baud_rate, int(slot), first_pwr_on, True)
                if ret != 0:
                    return

        if aapl == True:
            for slot in nic_list:
                ret1 = self.aapl_setup(self.baud_rate, int(slot), True)
                if ret1 != 0:
                    ret = ret + ret1
                else:
                    nic_list_remain.remove(slot)

        if ret != 0:
            print "===  setup_env_multi {} failed; failed slot:", ",".join(nic_list_remain)
        else:
            print "===  setup_env_multi Passed ==="

        return ret

    def aapl_setup(self, rate, slot=0, skip=False):
        numRetry = 3
        ret = -1
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            return -1

        self.nic_con.switch_console(slot)

        session = common.session_start()
        self.nic_con.uart_session_start(session)

        if skip == False:
            self.nic_con.uart_session_cmd(session, "sysinit.sh classic hw diag")
            print "Sleep 30 sec"
            time.sleep(30)

            # Disable link manager
            self.nic_con.uart_session_cmd(session, "halctl debug port --port 1 --admin-state down")
            self.nic_con.uart_session_cmd(session, "halctl debug port --port 5 --admin-state down")
            self.nic_con.uart_session_cmd(session, "halctl show port status")
            sleep(0.5)

        self.nic_con.uart_session_cmd(session, "halctl debug port aacs-server-start --server-port 9000")
        sleep(2)
        for i in range(numRetry):
            try:
                # PRBS init
                self.nic_con.uart_session_cmd(session, "/data/nic_arm/aapl/aapl_prbs_reset.sh")
                time.sleep(1)

                session.sendline("/data/nic_arm/aapl/aapl_prbs_init.sh")
                session.expect("\#")
                if "ERROR" in session.before or "WARNING" in session.before:
                    continue
                else:
                    ret = 0
                    break

            except pexpect.TIMEOUT:
                print "=== TIMEOUT: Failed to set up AAPL ==="
                break;
            
        self.nic_con.uart_session_stop(session)
        common.session_stop(session)

        if ret == 0:
            print "=== AAPL setup done; slot {}===".format(slot)
        else:
            print "=== AAPL setup failed; slot {} ===".format(slot)

        return ret

    def pwr_cycle_test(self, slot=0, iteration=1):
        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        for i in range(iteration):
            print "=== Ite {} ===".format(i)
            ret = self.setup_env(slot, True, 32, True)
            if ret != 0:
                print "=== Power cycle test failed at ite {} ===".format(i)
                break

        if ret == 0:
            print "=== Power cycle test passed {} iterations ===".format(iteration)
        return ret

    def test_start(self, slot=0, test_type="snake", mode="hbm", timeout=30, vmarg=0, pc="on"):
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
            test_cmd = "sh ./nic_prbs.sh 2>&1 > prbs_eth.log &"
        elif test_type == "prbs" and mode == "pcie":
            test_cmd = "./diag.exe prbs.p.a.tcl 2>&1 > prbs_pcie.log &"
        else:
            print "Invalid test_type {} and mdoe {}".format(test_type, mode)
            sys.exit(0)

        if pc == "on":
            self.nic_con.power_cycle_uart(self.baud_rate, slot)

        session = common.session_start()
        try:
            session.timeout = timeout
            self.nic_con.uart_session_start_slot(session, self.baud_rate, slot)
            self.nic_con.uart_session_cmd(session, "")
            self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data")
            self.nic_con.uart_session_cmd(session, "source /data/nic_arm/nic_setup_env.sh", 120)
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

            print "=== Snake on slot {} started ===".format(slot)
        except:
            try: 
                self.nic_con.uart_session_stop(session)
            except:
                pass
            print "=== Snake on slot {} FAILED to start! ===".format(slot)
            ret = -1

        common.session_stop(session)
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
        ret = self.nic_con.uart_session_cmd_sig(session, check_cmd, 15, "\#", ["TEST Passed", "TEST Failed", "TEST Not Done"], False)
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

        slot_list = ",".join(nic_list)
        print "slot_list:", slot_list
        self.nic_con.power_cycle_multi(self.baud_rate, slot_list)

        test_result = OrderedDict()
        # Start snake
        for slot in nic_list:
            ret = self.test_start(int(slot), test_type, mode, vmarg=vmargin, pc="off")
            if ret != 0:
                test_result[slot] = "FAIL"
            else:
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
            time.sleep(20)

        # Print result
        print "\n====== TEST RESULT: {:<5} {:<5} ======".format(test_type.upper(), mode.upper())
        result_fmt = "Slot {:<2}: {:<5}"
        for slot, sts in test_result.items():
            print result_fmt.format(slot, sts)
        print "======================================"

    def ena_dis_uboot_pcie(self, nic_list=[], enable=True):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        slot_list = ",".join(nic_list)
        print "slot_list:", slot_list

        for slot in nic_list:
            if enable == True:
                ret = self.nic_con.enable_pcie_uboot(int(slot))
            else:
                ret = self.nic_con.disable_pcie_uboot(int(slot))

            if ret != 0:
                print "=== Failed to change uboot PCIe setting at slot {} ===".format(slot)

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
    group.add_argument("-setup_multi", "--setup_multi", help="Set up nic env multi", action='store_true')

    group.add_argument("-pct", "--pwr_cycle_test", help="Power cycle test", action='store_true')

    group.add_argument("-ena_uboot_pcie", 
                       "--ena_uboot_pcie", 
                       help="Enable uboot PCIe for mutiple cards", 
                       action='store_true')
    group.add_argument("-dis_uboot_pcie", 
                       "--dis_uboot_pcie", 
                       help="Disable uboot PCIe for mutiple cards", 
                       action='store_true')

    parser.add_argument("-slot", "--slot", help="NIC slot number", type=int, default=0)
    parser.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser.add_argument("-wtime", "--wait_time", help="Wait time", type=int, default=300)
    parser.add_argument("-mgmt", "--mgmt", help="Set up management port", action='store_true')
    parser.add_argument("-mode", "--mode", help="Test mode: pcie/hbm; prbs: pcie/eth", type=str, default="hbm")
    parser.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=int, default=0)
    parser.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    parser.add_argument("-ite", "--iteration", help="Number of power cycle test iterations", type=int, default=1)
    parser.add_argument("-no_pc", "--no_pwr_cycle", help="Power cycle", action='store_false')
    parser.add_argument("-aapl", "--aapl", help="Setup AAPL", action='store_true')

    args = parser.parse_args()

    test = nic_test()
    if args.snake_start == True:
        test.test_start(args.slot, "snake", args.mode)
        sys.exit()

    if args.snake_check == True:
        test.snake_check(args.slot, "snake", args.mode)
        sys.exit()

    if args.snake == True:
        slot_list = args.slot_list.split(',')
        test.nic_test(slot_list, "snake", args.mode, args.wait_time, vmargin=args.vmarg)
        sys.exit()

    if args.prbs_start == True:
        test.test_start(args.slot, "prbs", args.mode)
        sys.exit()

    if args.prbs_check == True:
        test.test_check(args.slot, "prbs", args.mode)
        sys.exit()

    if args.prbs == True:
        slot_list = args.slot_list.split(',')
        test.nic_test(slot_list, "prbs", args.mode, args.wait_time, vmargin=args.vmarg)
        sys.exit()

    if args.setup == True:
        test.setup_env(args.slot, args.mgmt, 30, args.first_pwr_on, args.no_pwr_cycle, args.aapl)
        sys.exit()

    if args.setup_multi == True:
        slot_list = args.slot_list.split(',')
        test.setup_env_multi_top(slot_list, args.mgmt, 30, args.first_pwr_on, args.no_pwr_cycle, args.aapl)
        sys.exit()

    if args.pwr_cycle_test == True:
        test.pwr_cycle_test(args.slot, args.iteration)
        sys.exit()

    if args.ena_uboot_pcie == True or args.dis_uboot_pcie == True:
        slot_list = args.slot_list.split(',')

        if args.ena_uboot_pcie == True:
            ena_dis = True
        else:
            ena_dis = False
        test.ena_dis_uboot_pcie(slot_list, ena_dis)
        sys.exit()

