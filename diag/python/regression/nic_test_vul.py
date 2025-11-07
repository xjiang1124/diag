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
from vul_con import vul_con
from nic_con import nic_con

#from nic_test import nic_test

class nic_test_vul:
    def __init__(self):
        self.name = "nic_test_vul"
        self.vul_con = vul_con()
        self.nic_con = nic_con()
        #self.nic_test = nic_test()
        self.encoding = common.encoding

    def suc_dev_test_common(self, cmd, pass_sig, args):
        ret = 0
        try:
            uart_session = common.session_start()
            self.vul_con.usb_uart_session_connect(uart_session, args.slot, uart_id=0)
            cmdret, output = self.nic_con.uart_session_cmd_w_ot(uart_session, cmd, ending="uart:~\$", timeout=30)
            if cmdret != 0:
                print("Command {} failed".format(cmd))
                ret = -1
            if pass_sig not in output:
                print("===== FAILED: missing passing signature")
                ret = -1
            self.nic_con.uart_session_stop(uart_session)
            common.session_stop(uart_session)
        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Failed to run cmd on slot {} ===".format(args.slot))
            ret = -1
        if ret == 0 :
            print ("=== test result at Slot {}: Passed".format(args.slot))
        else:
            print ("=== test result at Slot {}: Failed".format(args.slot))

        return ret

    def suc_i2c_dev1_test(self, args):
        cmd = "command to be added"
        pass_sig = "PASS"
        return self.suc_dev_test_common(cmd, pass_sig, args)

    def nic_snake_mtp(self, args):
        ret = 0
        print("tcl_path:", args.tcl_path)

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

        # if args.snake_type == "esam_pktgen_llc_sor" or \
        #     args.snake_type == "esam_pktgen_ddr_burst_400G_no_mac" or \
        #     args.snake_type == "esam_pktgen_ddr_burst":
        #     print("ARM not booted")
        # else:
        #     if sal_con.enter_n1_linux(int(args.slot), session, warm_reset=False):
        #         print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
        #         ret = -1
        #         return ret

        # cmd = "jtag_accpcie_vulcano clr {}".format(args.slot)
        # common.session_cmd(session, cmd)

        # Disable WDT
        # cmd = "i2cset -y {} 0x4f 0x1 0".format(int(args.slot)+2)
        # common.session_cmd(session, cmd)
        # cmd = "i2cget -y {} 0x4f 0x1".format(int(args.slot)+2)
        # common.session_cmd(session, cmd)

        print("Start Vmarg")
        # if args.card_type == "LENI" or args.card_type == "LENI48G":
        #     cmd = "tclsh ~/diag/scripts/asic/leni_vmarg.tcl {} {} {}".format(args.slot, args.card_type, args.vmarg)
        #     common.session_cmd(session, cmd, 360, False, "vmarg set")

        # Start CPU Burn on N1
        if args.snake_type == "esam_pktgen_max_power_pcie_sor" or args.snake_type == "esam_pktgen_max_power_sor":
            print("Start CPU BURN on N1")
            # uart_session = common.session_start()
            # ret = self.nic_con.uart_session_start(uart_session, args.slot)
            # if ret != 0:
            #     return ret
            # try:
            #     self.nic_con.uart_session_cmd(uart_session, "/nic/bin/cpuburn_16 &")
            # except pexpect.TIMEOUT:
            #     print ("failed to run cpuburn")
            #     return -1
            # self.nic_con.uart_session_stop(uart_session)
            # common.session_stop(uart_session)
            print("Done with starting CPU BURN on N1")

        # cmd = "i2cget -y {} 0x4f 0x1".format(int(args.slot)+2)
        # common.session_cmd(session, cmd)

        print("Start tcl")
        # TCL command
        if args.card_type == "GELSOP":
            cmd = "tclsh ~/diag/scripts/asic/vul_snake.tcl"
            cmd += " " + str(args.slot)
            cmd += " " + str(args.snake_type)
            cmd += " " + str(args.dura)
            cmd += " " + str(args.card_type)
            cmd += " " + str(args.vmarg)
            cmd += " " + str(args.int_lpbk)
            cmd += " " + str(args.mtp_clk)
        else:
            print(args.card_type, "not supported!")
            common.session_stop(session)
            return 0

        common.session_cmd(session, cmd, 360, False, "pcie done")
        idx = session.expect(["SNAKE TEST PASSED", "SNAKE TEST FAILED", pexpect.TIMEOUT, "j2c : read req error", "min <= max", "sync failed"], args.timeout)

        if idx >= 1:
            print("ERROR :: Snake test has failed!")
            if idx == 2:
                print("\n==== TIMEOUT after command {}".format(cmd))
            elif idx == 3:
                print("\n==== J2C access failure")
            ret = -1
        common.session_cmd(session, chr(3))
        common.session_cmd(session, "inventory -sts -slot {}".format(args.slot))
        common.session_stop(session)
        # check uart console
        # if args.snake_type != "esam_pktgen_llc_sor" and \
        #    args.snake_type != "esam_pktgen_ddr_burst_400G_no_mac" and \
        #    args.snake_type != "esam_pktgen_ddr_burst":
        #     uart_session = common.session_start()
        #     self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=0)
        #     if 0 != sal_con.exp_cmd(uart_session, "", pass_sig_list=["uart:~\$"], timeout=5)[0]:
        #         print("===== FAILED: slot {} A35 console is not responsive".format(args.slot))
        #         return -1
        #     self.nic_con.uart_session_stop(uart_session)
        #     if args.card_type != "POLLARA":
        #         uart_session = common.session_start()
        #         self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=1)
        #         if 0 != sal_con.exp_cmd(uart_session, "", pass_sig_list=["\#"], timeout=5)[0]:
        #             print("===== FAILED: slot {} N1 console is not responsive".format(args.slot))
        #             return -1
        #         self.nic_con.uart_session_stop(uart_session)
        #         common.session_stop(uart_session)
        return ret

if __name__ == "__main__":
    test = nic_test_vul()

    parser = argparse.ArgumentParser(description="Diagnostic Test for Vulcano", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    subparsers = parser.add_subparsers(title="subcommands list", dest="suite", description="'%(prog)s {subcommand} --help' for detail usage of specified subcommand", help='sub-command description')

    # i2c dev test
    parser_i2c_test = subparsers.add_parser('suc_i2c_dev1_test', help='i2c dev1 test', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_i2c_test.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_i2c_test.set_defaults(func=test.suc_i2c_dev1_test)

    # NIC snake test from mtp
    parser_nic_snake_mtp = subparsers.add_parser('nic_snake_mtp', help='NIC snake test from mtp', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_nic_snake_mtp.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_nic_snake_mtp.add_argument("-tcl_path", "--tcl_path", help="TCL nic folder path", type=str, default='/home/diag/diag/asic/')
    parser_nic_snake_mtp.add_argument("-dura", "--dura", help="test duration in seconds", type=int, default=3)
    parser_nic_snake_mtp.add_argument("-snake_type", "--snake_type", help="Snake type", type=str, default='esam_pktgen_llc_no_mac_sor')
    parser_nic_snake_mtp.add_argument("-card_type", "--card_type", help="Card type", type=str, default='LENI')
    parser_nic_snake_mtp.add_argument("-vmarg", "--vmarg", help="vmarg", type=str, default='normal')
    parser_nic_snake_mtp.add_argument("-timeout", "--timeout", help="nic session cmd time out seconds", type=int, default=1800)
    parser_nic_snake_mtp.add_argument("-int_lpbk", "--int_lpbk", help="Internal loopback (1 or 0)", type=int, default=0)
    parser_nic_snake_mtp.add_argument("-mtp_clk", "--mtp_clk", help="Whether to use MTP PCIe refclk; 0: Disable; 1: use MTP clk", type=int, default=0)
    parser_nic_snake_mtp.add_argument("-v12_reset", '--v12_reset', action='store_true', help='Power cycle 12v')
    parser_nic_snake_mtp.set_defaults(func=test.nic_snake_mtp)

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)
        #parser.exit(status=1, message=parser.print_help())

    sys.exit(args.func(args))

