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
        common.session_cmd(session, "rm -f *")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libJudy.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libgmpxx.so.4 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libcrypto.so.10 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpcap.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
        common.session_cmd(session, "ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpython2.7.so.1.0 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")

        time.sleep(3)
        if sal_con.enter_a35_zephyr(int(args.slot), session, warm_reset=False):
            print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
            ret = -1
            return ret

        cmd = "jtag_accpcie_salina clr {}".format(args.slot)
        common.session_cmd(session, cmd)

        print("Done with Zephyr boot up, now start tcl")
        # TCL command
        if args.card_type == "LENI" or args.card_type == "LENI48G":
            cmd = "tclsh ~/diag/scripts/asic/sal_port_up.leni.tcl {} {} {}".format(args.slot, args.card_type, args.vmarg)
        elif args.card_type == "POLLARA":
            cmd = "tclsh ~/diag/scripts/asic/sal_port_up.pollara.tcl {} {} {}".format(args.slot, args.card_type, args.vmarg)
        else:
            print(args.card_type, "not supported!")
            common.session_stop(session)
            return 0

        common.session_cmd(session, cmd, ending="NAKE TEST DONE", timeout=args.timeout)
        common.session_stop(session)

        print("Dumping PCIe trace")
        uart_session = common.session_start()
        ret = self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=0)
        #ret = self.nic_con.uart_session_start(uart_session, args.slot, uart_id=0)
        if ret != 0:
            return ret
        try:
            self.nic_con.uart_session_cmd(uart_session, "pcieawd showlog", ending="uart:~\$")
        except pexpect.TIMEOUT:
            print ("failed to run cpuburn")
            return -1
        self.nic_con.uart_session_stop(uart_session)
        common.session_stop(uart_session)
        print("Done with Zephyr boot up.")

        return 0

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
    parser_nic_port_up.add_argument("-timeout", "--timeout", help="nic session cmd time out seconds", type=int, default=300)
    parser_nic_port_up.set_defaults(func=test.nic_port_up)

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)
        #parser.exit(status=1, message=parser.print_help())

    sys.exit(not args.func(args))

