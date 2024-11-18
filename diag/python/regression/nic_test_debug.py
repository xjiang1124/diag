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
import threading
from collections import OrderedDict
from time import sleep

import datetime

sys.path.append("../lib")
import common
import sal_con
from nic_con import nic_con
from nic_test import nic_test

class nic_test_debug:
    def __init__(self):
        self.name = "nic_snake"
        self.baud_rate = 115200
        self.fmt_con_cmd = "con_connect.sh {}"
        self.nic_con = nic_con()
        self.nic_test = nic_test()
        self.encoding = common.encoding

    def nic_port_up(self, args):
        print("tcl_path:", args.tcl_path)

        session = common.session_start()
        # set spimode to be off
        cmd = "fpgautil spimode {} off".format(args.slot)
        common.session_cmd(session, cmd)
        print("=== TCL ENV setup ===")
        tcl_path = args.tcl_path
        common.session_cmd(session, "export ASIC_LIB_BUNDLE="+tcl_path)
        common.session_cmd(session, "export ASIC_SRC=$ASIC_LIB_BUNDLE/asic_src")
        common.session_cmd(session, "export ASIC_LIB=$ASIC_LIB_BUNDLE/asic_lib")
        common.session_cmd(session, "export ASIC_GEN=$ASIC_SRC")
        common.session_cmd(session, "cd $ASIC_LIB_BUNDLE/asic_lib")
        common.session_cmd(session, "source source_env_path")
        common.session_cmd(session, "export LD_LIBRARY_PATH=$ASIC_LIB_BUNDLE/depend_libs/mtp_hack:$LD_LIBRARY_PATH")
        common.session_cmd(session, "cd $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        #common.session_cmd(session, "rm -f *")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libJudy.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libgmpxx.so.4 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libcrypto.so.10 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpcap.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpython2.7.so.1.0 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")

        time.sleep(3)
        if args.card_type == "LENI" or args.card_type == "LENI48G":
            #if sal_con.enter_n1_linux(int(args.slot), session, warm_reset=False):
            if sal_con.enter_a35_zephyr(int(args.slot), session, warm_reset=False):
                print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
                ret = -1
                return ret
        elif args.card_type == "POLLARA":
            if sal_con.enter_a35_zephyr(int(args.slot), session, warm_reset=False):
                print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
                ret = -1
                return ret
        else:
            print(args.card_type, "not supported!")
            common.session_stop(session)
            return 0

        cmd = "jtag_accpcie_salina clr {}".format(args.slot)
        common.session_cmd(session, cmd)

        print("Done with Zephyr boot up, now start tcl")
        # TCL command
        if args.card_type == "LENI" or args.card_type == "LENI48G":
            cmd = "tclsh ~/diag/scripts/asic/sal_port_up.leni.tcl {} {} {} {}".format(args.slot, args.card_type, args.vmarg, args.inf)
        elif args.card_type == "POLLARA":
            cmd = "tclsh ~/diag/scripts/asic/sal_port_up.pollara.tcl {} {} {} {}".format(args.slot, args.card_type, args.vmarg, args.inf)
        else:
            print(args.card_type, "not supported!")
            common.session_stop(session)
            return 0

        common.session_cmd(session, cmd, ending="NAKE TEST DONE", timeout=args.timeout)
        common.session_stop(session)

        if args.inf == "pcie" or args.inf == "all":
            print("Dumping PCIe trace")
            uart_session = common.session_start()
            ret = self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=0)
            #ret = self.nic_con.uart_session_start(uart_session, args.slot, uart_id=0)
            if ret != 0:
                return ret
            try:
                self.nic_con.uart_session_cmd(uart_session, "pcieawd showlog", ending="uart:~\$")
            except pexpect.TIMEOUT:
                print ("Faied to dump pcie trace")
                return -1
            self.nic_con.uart_session_stop(uart_session)
            common.session_stop(uart_session)

        return 0

    def nic_stress_reset(self, args):
        ret = 0
        print("tcl_path:", args.tcl_path)

        session = common.session_start()
        # set spimode to be off
        cmd = "fpgautil spimode {} off".format(args.slot)
        common.session_cmd(session, cmd)

        if args.card_type == "POLLARA":
            if sal_con.enter_a35_zephyr(int(args.slot), session, warm_reset=False):
                print("===== FAILED: slot {} couldn't boot Zephyr".format(args.slot))
                ret = -1
                return ret
        else:
            if args.snake_type == "esam_pktgen_llc_sor" or \
               args.snake_type == "esam_pktgen_ddr_burst_400G_no_mac" or \
               args.snake_type == "esam_pktgen_ddr_burst":
                print("ARM not booted")
            else:
                if sal_con.enter_n1_linux(int(args.slot), session, warm_reset=False):
                    print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
                    ret = -1
                    return ret
        common.session_stop(session)

        for ite in range(args.ite):
            print("=== Iteration {} ===".format(ite))
            session = common.session_start()
            print("=== TCL ENV setup ===")
            tcl_path = args.tcl_path
            common.session_cmd(session, "export ASIC_LIB_BUNDLE="+tcl_path)
            common.session_cmd(session, "export ASIC_SRC=$ASIC_LIB_BUNDLE/asic_src")
            common.session_cmd(session, "export ASIC_LIB=$ASIC_LIB_BUNDLE/asic_lib")
            common.session_cmd(session, "export ASIC_GEN=$ASIC_SRC")
            common.session_cmd(session, "cd $ASIC_LIB_BUNDLE/asic_lib")
            common.session_cmd(session, "source source_env_path")
            common.session_cmd(session, "export LD_LIBRARY_PATH=$ASIC_LIB_BUNDLE/depend_libs/mtp_hack:$LD_LIBRARY_PATH")
            common.session_cmd(session, "cd $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
            #common.session_cmd(session, "rm -f *")
            common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libJudy.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
            common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
            common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libgmpxx.so.4 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
            common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libcrypto.so.10 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
            common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpcap.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
            common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpython2.7.so.1.0 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
            common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libzmq.so.5 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
            common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libsodium.so.23 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
            common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpgm-5.2.so.0 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")

            time.sleep(3)
            cmd = "jtag_accpcie_salina clr {}".format(args.slot)
            common.session_cmd(session, cmd)

            print("Start Vmarg")
            if args.card_type == "LENI" or args.card_type == "LENI48G":
                cmd = "tclsh ~/diag/scripts/asic/leni_vmarg.tcl {} {} {}".format(args.slot, args.card_type, args.vmarg)
                common.session_cmd(session, cmd, 360, False, "vmarg set")

            # Start CPU Burn on N1
            if args.snake_type == "esam_pktgen_max_power_pcie_sor" or args.snake_type == "esam_pktgen_max_power_sor":
                print("Start CPU BURN on N1")
                uart_session = common.session_start()
                ret = self.nic_con.uart_session_start(uart_session, args.slot)
                if ret != 0:
                    return ret
                try:
                    self.nic_con.uart_session_cmd(uart_session, "/nic/bin/cpuburn_16 &")
                except pexpect.TIMEOUT:
                    print ("failed to run cpuburn")
                    return -1
                self.nic_con.uart_session_stop(uart_session)
                common.session_stop(uart_session)
                print("Done with starting CPU BURN on N1")

            print("Start tcl")
            # TCL command
            if args.card_type == "LENI" or args.card_type == "LENI48G":
                if args.snake_type == "esam_pktgen_llc_sor" or \
                args.snake_type == "esam_pktgen_ddr_burst_400G_no_mac" or \
                args.snake_type == "esam_pktgen_ddr_burst":
                    new_vmarg = args.vmarg
                else:
                    new_vmarg = "none"
                cmd = "tclsh ~/diag/scripts/asic/sal_snake.leni.tcl {} {} {} {} {} {}".format(args.slot, args.snake_type, args.dura, args.card_type, new_vmarg, args.int_lpbk)
            elif args.card_type == "POLLARA":
                cmd = "tclsh ~/diag/scripts/asic/sal_snake.pollara.yanmin.tcl {} {} {} {} {} {} 1 0".format(args.slot, args.snake_type, args.dura, args.card_type, args.vmarg, args.int_lpbk)
            else:
                print(args.card_type, "not supported!")
                common.session_stop(session)
                return 0

            # wait for snake traffic to run for 90 seconds
            common.session_cmd(session, cmd, args.timeout, False, "90 second passed")

            # check uart console
            if args.snake_type != "esam_pktgen_llc_sor" and \
               args.snake_type != "esam_pktgen_ddr_burst_400G_no_mac" and \
               args.snake_type != "esam_pktgen_ddr_burst":
                uart_session = common.session_start()
                self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=0)
                if 0 != sal_con.exp_cmd(uart_session, "", pass_sig_list=["uart:~\$"], timeout=5):
                    print("===== FAILED: slot {} A35 console is not responsive".format(args.slot))
                    return -1
                self.nic_con.uart_session_stop(uart_session)
                if args.card_type != "POLLARA":
                    uart_session = common.session_start()
                    self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=1)
                    if 0 != sal_con.exp_cmd(uart_session, "", pass_sig_list=["\#"], timeout=5):
                        print("===== FAILED: slot {} N1 console is not responsive".format(args.slot))
                        return -1
                    self.nic_con.uart_session_stop(uart_session)
                    common.session_stop(uart_session)

            # do warm reset
            uart_session = common.session_start()
            self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=0)
            if 0 != sal_con.exp_cmd(uart_session, "kernel reboot warm", pass_sig_list=["uart:~\$"], timeout=10):
                print("===== FAILED: slot {} warm reboot failed".format(args.slot))
                return -1
            self.nic_con.uart_session_stop(uart_session)

            # kill j2c
            common.session_cmd(session, chr(3))
            common.session_cmd(session, "inventory -sts -slot {}".format(args.slot))
            common.session_stop(session)

        return ret

if __name__ == "__main__":

    test = nic_test_debug()
    parser = argparse.ArgumentParser(description="Diagnostic Test Debug", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    subparsers = parser.add_subparsers(title="subcommands list", dest="suite", description="'%(prog)s {subcommand} --help' for detail usage of specified subcommand", help='sub-command description')

    # NIC snake test from mtp
    parser_nic_port_up = subparsers.add_parser('nic_port_up', help='NIC port up', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_nic_port_up.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_nic_port_up.add_argument("-tcl_path", "--tcl_path", help="TCL nic folder path", type=str, default='/home/diag/xin/nic')
    parser_nic_port_up.add_argument("-card_type", "--card_type", help="Card type", type=str, default='LENI')
    parser_nic_port_up.add_argument("-vmarg", "--vmarg", help="vmarg", type=str, default='normal')
    parser_nic_port_up.add_argument("-inf", "--inf", help="inf", type=str, default='pcie')
    parser_nic_port_up.add_argument("-timeout", "--timeout", help="nic session cmd time out seconds", type=int, default=300)
    parser_nic_port_up.set_defaults(func=test.nic_port_up)

    # NIC warm reboot during snake
    parser_nic_stress_reset = subparsers.add_parser('nic_stress_reset', help='NIC warm reboot during snake', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_nic_stress_reset.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_nic_stress_reset.add_argument("-tcl_path", "--tcl_path", help="TCL nic folder path", type=str, default='/home/diag/xin/nic')
    parser_nic_stress_reset.add_argument("-dura", "--dura", help="test duration in seconds", type=int, default=3)
    parser_nic_stress_reset.add_argument("-card_type", "--card_type", help="Card type", type=str, default='LENI')
    parser_nic_stress_reset.add_argument("-vmarg", "--vmarg", help="vmarg", type=str, default='normal')
    #parser_nic_stress_reset.add_argument("-inf", "--inf", help="inf", type=str, default='pcie')
    parser_nic_stress_reset.add_argument("-snake_type", "--snake_type", help="Snake type", type=str, default='esam_pktgen_llc_no_mac_sor')
    parser_nic_stress_reset.add_argument("-timeout", "--timeout", help="nic session cmd time out seconds", type=int, default=300)
    parser_nic_stress_reset.add_argument("-int_lpbk", "--int_lpbk", help="Internal loopback (1 or 0)", type=int, default=0)
    parser_nic_stress_reset.add_argument("-ite", "--ite", help="Iteration of start and stop snake", type=int, default=1)
    parser_nic_stress_reset.set_defaults(func=test.nic_stress_reset)

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)
        #parser.exit(status=1, message=parser.print_help())

    sys.exit(not args.func(args))

