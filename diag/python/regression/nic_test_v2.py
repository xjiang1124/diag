#!/usr/bin/env python

import argparse
import datetime
import copy
import math
import pexpect
import os
import re
import sys
import time
from collections import OrderedDict
from time import sleep

import datetime

sys.path.append("../lib")
import common
from nic_con import nic_con
from nic_test import nic_test

class nic_test_v2:
    def __init__(self):
        self.name = "nic_snake"
        self.baud_rate = 115200
        self.fmt_con_cmd = "picocom -q -b {} -f h /dev/ttyS1"
        self.nic_con = nic_con()
        self.nic_test = nic_test()

    def pc_test(self, args):
        print(args)
    
        if args.slot_list == "":
            print ("Invalide input slot_list:", slot_list)
    
        slot_list = args.slot_list.split(',')
        for ite in range(args.iteration):
            print("=== Ite:", ite, "===")
            for slot in slot_list:
                self.nic_con.switch_console(slot)
                uart_session = common.session_start()
                cmd = self.fmt_con_cmd.format(self.baud_rate)
                uart_session.sendline(cmd)

                uart_session = common.session_start()
                #cmd = self.fmt_con_cmd.format(self.baud_rate)
                #uart_session.sendline(cmd)

                print("=== Slot:", slot, "===")
                self.nic_con.power_cycle_multi(self.baud_rate, slot, wtime=0, swm_lp=False)

                ret = self.nic_con.uart_session_start_login(uart_session, self.baud_rate)
                #self.nic_con.uart_session_stop(uart_session)
                #common.session_stop(uart_session)

                if ret != 0:
                    return -1
                self.nic_con.uart_session_stop(uart_session)
                common.session_stop(uart_session)

                # Winbond prog test
                uart_session = common.session_start()
                #ret = self.nic_con.uart_session_start(uart_session, self.baud_rate)
                try:
                    cmd = self.fmt_con_cmd.format(self.baud_rate)
                    uart_session.sendline(cmd)
                    cmd = 'fwupdate -p /data/naples_gold_elba.tar -i all; sleep 10; echo "DIAGFW PROG DONE"'
                    cmd = 'date;sleep 10; date; echo "DIAGFW PROG DONE"'
                    cmd = "source /data/run_prog.sh"
                    uart_session.timeout=1800
                    uart_session.sendline(cmd)
                    uart_session.expect("DIAGFW PROG DONE")
                    #uart_session.expect("\#")
                except pexpect.TIMEOUT:
                    print "DIAGFW PROG FAILED!"
                    sys.exit(0)
                continue


                ret = self.nic_con.uart_session_cmd(uart_session, cmd, 1800, "DIAGFW PROG DONE")
                if ret != 0:
                    return -1

                self.nic_con.uart_session_stop(uart_session)
                common.session_stop(uart_session)
                continue

                # Setup ENV
                ret = self.nic_test.setup_env(int(slot), False, 30, args.first_pwr_on, False, False)
                if ret != 0:
                    return -1

                self.nic_con.get_mgmt_rdy(self.baud_rate, int(slot), args.first_pwr_on)
                if ret != 0:
                    return -1

                ret = self.nic_con.uart_session_start(uart_session, self.baud_rate)
                if ret != 0:
                    return -1
                
                ret = self.nic_con.uart_session_cmd(uart_session, "sleep 15; ls", 30)
                if ret != 0:
                    return -1

                self.nic_con.uart_session_stop(uart_session)
                common.session_stop(uart_session)

                self.nic_con.get_mgmt_rdy(self.baud_rate, int(slot), args.first_pwr_on)
                if ret != 0:
                    return -1

        return True

    def fw_update(self, args):
        print(args)
    
        if args.slot_list == "":
            print ("Invalide input slot_list:", slot_list)
    
        slot_list = args.slot_list.split(',')

        for ite in range(args.iteration):
            print("=== Ite:", ite, "===")
            for slot1 in slot_list:
                slot = int(slot1)

                self.nic_con.switch_console(slot)
                session = common.session_start()
                cmd = self.fmt_con_cmd.format(self.baud_rate)
                session.sendline(cmd)

                #session = common.session_start()

                print("=== Slot:", slot, "===")
                self.nic_con.power_cycle_multi(self.baud_rate, slot, wtime=0, swm_lp=False)

                ret = self.nic_con.uart_session_start_login(session, self.baud_rate)
                if ret != 0:
                    return False
                self.nic_con.uart_session_stop(session)

                ret = self.nic_con.enable_mnic(slot=slot, first_pwr_on=args.first_pwr_on)
                if ret != 0:
                    return False

                for i in range(3):
                    ret = self.nic_con.config_mnic(slot=slot)
                    if ret == 0:
                        break
                if ret != 0:
                    return False


                # Copy image file to NIC
                cmd_str = "scp_s.sh ./{} {} /update"
                cmd = cmd_str.format(args.img_fn, slot)
                ret = common.session_cmd(session, cmd)
                if ret != 0:
                    print("P000")
                    #return False

                ret = self.nic_con.uart_session_start(session)
                if ret != 0:
                    return False
                try:
                    cmd_str = 'echo \"fwupdate -p /update/{} -i all; sleep 10; echo \"DIAGFW PROG DONE\" \" > /update/run_prog.sh'
                    cmd = cmd_str.format(args.img_fn)
                    self.nic_con.uart_session_cmd(session, cmd)
                    session.timeout=1800
                    session.sendline("source /update/run_prog.sh")
                    session.expect("DIAGFW PROG DONE")
                    self.nic_con.uart_session_cmd(session, "fwupdate -s goldfw")
                    self.nic_con.uart_session_cmd(session, "pwd")
                except pexpect.TIMEOUT:
                    print "DIAGFW PROG FAILED!"
                    return False

                self.nic_con.uart_session_stop(session)
                common.session_stop(session)

    def ddrmargin(self, args):
        print(args)
    
        if args.slot_list == "":
            print ("Invalide input slot_list:", slot_list)
    
        slot_list = args.slot_list.split(',')

        for slot_s in slot_list:
            print("=== Slot {} ===".format(slot_s))

            # Mode
            mode = args.mode.upper()
            if mode == "ALL":
                mode_list = ["findrdvalid", "findwrvalid"]
            elif mode == "RD":
                mode_list = ["findrdvalid"]
            elif mode == "WR":
                mode_list = ["findwrvalid"]

            # Calculate timeout
            sliceMap = int(args.slice_map, 16)
            cnt = 0
            for i in range(8):
                temp = sliceMap & 1
                if temp == 1:
                    cnt = cnt + 1
                sliceMap = sliceMap >> 1
            timeout = 60*40*cnt
            print(cnt, "sliceBits detected; timeout set to", timeout)

            slot = int(slot_s)

            self.nic_con.switch_console(slot)

            for mode in mode_list:
                session = common.session_start()
                ret = self.nic_con.enter_uboot(session, slot, self.baud_rate)
                if ret == -1:
                    print "=== Failed to change uboot board rate! Slot: {} ===".format(slot)
                    common.session_stop(session)
                    continue

                ret = self.nic_con.uart_session_start(session)
                if ret != 0:
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    continue

                self.nic_con.uart_session_cmd(session, "ddrmargin init", 10)
                self.nic_con.uart_session_cmd(session, "ddrmargin set byte_mode {}".format(args.byte_mode), 10)
                self.nic_con.uart_session_cmd(session, "ddrmargin set FreqMHz   {}".format(args.freq), 10)
                self.nic_con.uart_session_cmd(session, "ddrmargin set SliceMap  {}".format(args.slice_map), 10)
                self.nic_con.uart_session_cmd(session, "ddrmargin set gBitMap   {}".format(args.bit_map), 10)
                self.nic_con.uart_session_cmd(session, "ddrmargin show", 10)
                self.nic_con.uart_session_cmd(session, "ddrmargin               {}".format(mode), timeout, "to reboot")

                self.nic_con.uart_session_stop(session)
                common.session_stop(session)


    def chamber_get_temp(self, ip):
        cmd = "telnet {} 5025".format(ip)
        print(cmd)
        session=pexpect.spawn(cmd)
        session.logfile = sys.stdout
        session.expect(r"\]")

        session.sendline(":SOURCE:CLOOP1:PVALUE?")
        session.expect(r"\d+\.\d+")

        session.sendcontrol("]")
        session.expect(r"telnet>")

        session.sendline("q")

    def chamber_set_temp(self, ip, temp):
        cmd = "telnet {} 5025".format(ip)
        print(cmd)
        session=pexpect.spawn(cmd)
        session.logfile = sys.stdout
        session.expect(r"\]")

        session.send(":SOURCE:CLOOP1:SPOINT {}\r".format(temp))
        session.send(":SOURCE:CLOOP1:SPOINT?\r")
        session.expect(r"\d+\.\d+")

        session.sendcontrol("]")
        session.expect(r"telnet>")

        session.sendline("q")

    def chamber_ctrl(self, args):
        print(args)

        if args.show == True:
            self.chamber_get_temp(args.ip)
            return

        if args.set == True:
            self.chamber_set_temp(args.ip, args.temp)
            return

    def uboot_update(self, args):
        print(args)
    
        if args.slot_list == "":
            print ("Invalide input slot_list:", slot_list)
    
        slot_list = args.slot_list.split(',')

        if args.skip_init == True:
            nic_list_pass = slot_list
        else:
            [ret, nic_list_pass, nic_list_fail] = self.nic_test.setup_env_multi_top(nic_list=slot_list, mgmt=True, asic_type="elba", first_pwr_on=args.first_pwr_on)

        for slot1 in nic_list_pass:
            slot = int(slot1)

            self.nic_con.switch_console(slot)
            session = common.session_start()
            #cmd = self.fmt_con_cmd.format(self.baud_rate)
            #session.sendline(cmd)

            # Copy image file to NIC
            cmd_str = "scp_s.sh ./{} {} /data/"
            cmd = cmd_str.format(args.img_fn, slot)
            ret = common.session_cmd(session, cmd)
            if ret != 0:
                print("P000")
                #return False

            ret = self.nic_con.uart_session_start(session)
            if ret != 0:
                return False
            try:
                cmd_str = 'mount /dev/mmcblk0p10 /data; cd /data/; sync; flash_erase /dev/mtd0 0x69F0000 64; dd if={} of=/dev/mtd0 bs=64k seek=1695'
                cmd = cmd_str.format(args.img_fn)
                self.nic_con.uart_session_cmd(session, cmd, 60)
                self.nic_con.uart_session_cmd(session, "pwd")
            except pexpect.TIMEOUT:
                print "UBOOT PROG FAILED!"
                return False

            self.nic_con.uart_session_stop(session)
            common.session_stop(session)

    def ddr_stress(self, args):
        print(args)
    
        if args.slot_list == "":
            print ("Invalide input slot_list:", slot_list)
    
        slot_list = args.slot_list.split(',')

        for idx in range(args.ite):
            print("=== Ite", idx, "===")

            [ret, nic_list_pass, nic_list_fail] = self.nic_test.setup_env_multi_top(nic_list=slot_list, mgmt=False, asic_type="elba", first_pwr_on=args.first_pwr_on)

            for slot1 in nic_list_pass:
                slot = int(slot1)

                self.nic_con.switch_console(slot)
                session = common.session_start()
                ret = self.nic_con.uart_session_start(session)
                if ret != 0:
                    return False

                # Copy image file to NIC
                try:
                    cmd = "/data/nic_util/stressapptest_arm -M 20000 -s 60 -m 16 -l /data/nic_util/stressapptest.log"
                    ret = common.session_cmd(session, cmd, timeout=120, ending="Status: PASS - please verify no corrected errors")
                    if ret < 0:
                        print("P000", ret)
                        return False
                except pexpect.TIMEOUT:
                    return False

                self.nic_con.uart_session_stop(session)
                common.session_stop(session)

    def check_edma_ready(self, args):
        slot_list = args.slot_list.split(',')
        num_retry = 16
        slot_list_remain = copy.deepcopy(slot_list)
        slot_list_pass = []

        for idx in range(num_retry):
            print('------------------')
            print('EDMA checking #{}'.format(idx))
            print('------------------')

            for slot1 in slot_list:

                if slot1 in slot_list_pass:
                    continue

                slot = int(slot1)

                self.nic_con.switch_console(slot)
                session = common.session_start()
                ret = self.nic_con.uart_session_start(session, numRetry=1)
                if ret != 0:
                    common.session_stop(session)
                    continue

                try:
                    cmd = "ls /nic/conf/gen/mpu_prog_info.json"
                    [ret, output] = self.nic_con.uart_session_cmd_w_ot(session, cmd, timeout=10)
                except pexpect.TIMEOUT:
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    continue

                if 'No such file or directory' in output:
                    print('Json file not present')
                else:
                    print('Json file present')
                    slot_list_remain.remove(slot1)
                    slot_list_pass.append(slot1)

                self.nic_con.uart_session_stop(session)
                common.session_stop(session)

            if len(slot_list_remain) == 0:
                break

            print('Wait for 15 sec before next checking')
            time.sleep(15)

        print("EDMA checking: PASS list:", slot_list_pass)
        print("EDMA checking: FAIL list:", slot_list_remain)
        print('EDMA Checking Done')

    def setup_multi(self, args):
        print(args)

        slot_list = args.slot_list.split(',')
        [ret, pass_list, fail_list] = self.nic_test.setup_env_multi_top(nic_list=slot_list, timeout=30, mgmt=args.mgmt, first_pwr_on=args.first_pwr_on, pwr_cycle=args.no_pc, asic_type=args.asic_type, uefi=args.uefi, dis_net_port=args.dis_net_port, env=args.skip_env)

    def setup_multi_w_console(self, args):
        print(args)
    
        if args.slot_list == "":
            print ("Invalide input slot_list:", slot_list)
    
        slot_list = args.slot_list.split(',')

        for ite in range(args.iteration):
            print("=== Ite:", ite, "===")
            for slot1 in slot_list:
                slot = int(slot1)

                self.nic_con.switch_console(slot)
                session = common.session_start()
                cmd = self.fmt_con_cmd.format(self.baud_rate)
                session.sendline(cmd)

                #session = common.session_start()

                print("=== Slot:", slot, "===")
                self.nic_con.power_cycle_multi(self.baud_rate, slot, wtime=0, swm_lp=False)

                ret = self.nic_con.uart_session_start_login(session, self.baud_rate)
                if ret != 0:
                    return False
                self.nic_con.uart_session_stop(session)

                ret = self.nic_con.enable_mnic(slot=slot, first_pwr_on=args.first_pwr_on)
                if ret != 0:
                    return False

                for i in range(3):
                    ret = self.nic_con.config_mnic(slot=slot)
                    if ret == 0:
                        break
                if ret != 0:
                    return False

                self.nic_con.uart_session_stop(session)
                common.session_stop(session)

    def multi_nic_cmds(self, args):
        print(args)
    
        if args.slot_list == "":
            print ("Invalide input slot_list:", slot_list)
    
        slot_list = args.slot_list.split(',')
        for slot1 in slot_list:
            slot = int(slot1)
            print("=== Slot {} ===".format(slot))

            self.nic_con.switch_console(slot)
            session = common.session_start()

            ret = self.nic_con.uart_session_start(session, self.baud_rate)
            if ret != 0:
                continue

            if args.send_only:
                session.sendline(args.nic_cmd)
                time.sleep(3)
            else:
                ret = self.nic_con.uart_session_cmd(session, args.nic_cmd, args.timeout)

            self.nic_con.uart_session_stop(session)
            common.session_stop(session)

if __name__ == "__main__":

    test = nic_test_v2()

    parser = argparse.ArgumentParser(description="Diagnostic Test V2", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    subparsers = parser.add_subparsers(title="subcommands list", dest="suite", description="'%(prog)s {subcommand} --help' for detail usage of specified subcommand", help='sub-command description')

    #aliases only support in python2.7
    parser_pc_test = subparsers.add_parser('pc_test', help='Power cycle test', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_pc_test.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_pc_test.add_argument("-ite", "--iteration", help="Number of iterations", type=int, required=False, default=1)
    parser_pc_test.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    #parser_pc_test.add_argument("-fg", "--foreground", help="Run test in foreground", action='store_true')
    parser_pc_test.set_defaults(func=test.pc_test)

    # FW update
    parser_fw_update = subparsers.add_parser('fw_update', help='Diagfw update', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_fw_update.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_fw_update.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    parser_fw_update.add_argument("-fn", "--img_fn", help="Image file name", type=str, default='UNKNOWN')
    parser_fw_update.add_argument("-ite", "--iteration", help="Number of iterations", type=int, required=False, default=1)

    parser_fw_update.set_defaults(func=test.fw_update)

    # Uboot update
    parser_fw_update = subparsers.add_parser('uboot_update', help='Uboot update', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_fw_update.add_argument("-slot_list", "--slot_list", help="NIC slot list; defaut", type=str, default="")
    parser_fw_update.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    parser_fw_update.add_argument("-skip_init", "--skip_init", help="Skip mgmt port intialiaztion", action='store_true')
    parser_fw_update.add_argument("-fn", "--img_fn", help="Image file name; defaut", type=str, default='UNKNOWN')

    parser_fw_update.set_defaults(func=test.uboot_update)

    # DDR stress
    parser_fw_update = subparsers.add_parser('ddr_stress', help='DDR stressapptest', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_fw_update.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_fw_update.add_argument("-ite", "--ite", help="Number of iteration", type=int, default=1)
    parser_fw_update.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')

    parser_fw_update.set_defaults(func=test.ddr_stress)

    # Chamber temp show/set
    parser_fw_update = subparsers.add_parser('chamber_ctrl', help='Chamber temperature control', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_fw_update.add_argument("-show", "--show", help="Show temp", action='store_true')
    parser_fw_update.add_argument("-set", "--set", help="Set temp", action='store_true')
    parser_fw_update.add_argument("-ip", "--ip", help="IP address", type=str, default='10.9.6.249')
    parser_fw_update.add_argument("-temp", "--temp", help="Target temp", type=str, default='25')

    parser_fw_update.set_defaults(func=test.chamber_ctrl)

    # PDU control
    parser_fw_update = subparsers.add_parser('pdu_ctrl', help='PDU control', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_fw_update.add_argument("-show", "--show", help="Show temp", action='store_true')
    parser_fw_update.add_argument("-set", "--set", help="Set temp", action='store_true')
    parser_fw_update.add_argument("-ip", "--ip", help="IP address", type=str, default='10.9.6.249')
    parser_fw_update.add_argument("-temp", "--temp", help="Target temp", type=str, default='25')

    parser_fw_update.set_defaults(func=test.chamber_ctrl)

    # DDR Margin
    parser_fw_update = subparsers.add_parser('ddrmargin', help='DDR eye measurement', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_fw_update.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_fw_update.add_argument("-freq", "--freq", help="DDR frequency", type=str, default="3200")
    parser_fw_update.add_argument("-byte_mode", "--byte_mode", help="Byte/bite mode", type=str, default="0")
    parser_fw_update.add_argument("-slice_map", "--slice_map", help="Slice bite map", type=str, default="0xFF")
    parser_fw_update.add_argument("-bit_map", "--bit_map", help="DDR chip DQ bit map", type=str, default="0xFF")
    parser_fw_update.add_argument("-mode", "--mode", help="RD/WR/All margin", type=str, default="all")
    #parser_fw_update.add_argument("", "", help="", type=str, default="")

    parser_fw_update.set_defaults(func=test.ddrmargin)

    # Check EDMA readiness
    parser_check_edma = subparsers.add_parser('check_edma', help='Check EDMA readiness', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_check_edma.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")

    parser_check_edma.set_defaults(func=test.check_edma_ready)

    # setup multi with console output
    parser_setup_multi_w_console = subparsers.add_parser('setup_multi_w_console', help='Set up multiple cards', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_setup_multi_w_console.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_setup_multi_w_console.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')

    parser_setup_multi_w_console.set_defaults(func=test.setup_multi_w_console)

    # setup multi
    parser_setup_multi = subparsers.add_parser('setup_multi', help='Set up multiple cards', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_setup_multi.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_setup_multi.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    parser_setup_multi.add_argument("-mgmt", "--mgmt", help="Set up management port", action='store_true')
    parser_setup_multi.add_argument("-no_pc", "--no_pwr_cycle", help="Power cycle", action='store_false')
    parser_setup_multi.add_argument("-asic_type", "--asic_type", help="ASIC type: capri/elba", type=str, default="elba")
    parser_setup_multi.add_argument("-uefi", "--uefi", help="UEFI mode", action='store_true')
    parser_setup_multi.add_argument("-dis_net_port", "--dis_net_port", help="Disable RJ45 Network port", action='store_true')
    parser_setup_multi.add_argument("-skip_env", "--skip_env", help="Set up env", action='store_false')
    parser_setup_multi.add_argument("-edma", "--edma", help="EDMA setup", action='store_true')

    parser_setup_multi.set_defaults(func=test.setup_multi)

    # Multi nic cmd
    parser_multi_nic_cmds = subparsers.add_parser('multi_nic_cmds', help='Run commands on each nic console', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_multi_nic_cmds.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_multi_nic_cmds.add_argument("-nic_cmd", "--nic_cmd", help="nic command", type=str, default="")
    parser_multi_nic_cmds.add_argument("-timeout", "--timeout", help="timeout", type=int, default=30)
    parser_multi_nic_cmds.add_argument("-sd_only", "--send_only", help="Only send command and do not wait for it finish", action='store_true')

    parser_multi_nic_cmds.set_defaults(func=test.multi_nic_cmds)

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)
        #parser.exit(status=1, message=parser.print_help())

    sys.exit(not args.func(args))

