#!/usr/bin/env python

import argparse
import datetime
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

class ddr_test:
    def __init__(self):
        self.name = "ddr_test"
        self.baud_rate = 115200
        self.num_retry = 3
        self.nic_con = nic_con()
        self.nct_test = nic_test()

    def two_step_edma(self, nic_list=[], num_ite=1, tcl_path="/home/diag/diag/asic/", script_path="/home/diag/diag/scripts/asic/", start_tcl="start.tcl", stop_tcl="stop.tcl", pc_mode="board"):
        print "=== NIC DDR Test ==="
        print("tcl_path:", tcl_path)
        print("script_path:", script_path)
        print("start_tcl:", start_tcl)
        print("stop_tcl:", stop_tcl)
        print("pc_mode:", pc_mode)

        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        for ite in range(num_ite):
            print("=== Ite:", ite, "===")
            slot_list = ",".join(nic_list)
            print("slot_list:", slot_list)

            for slot in nic_list:
                try:
                    con_session = common.session_start()

                    common.session_cmd(con_session, "killall picocom", 20)

                    if pc_mode == "board":
                        self.nic_con.power_cycle_multi(self.baud_rate, slot, 0)
                    #ret = self.nic_con.uart_session_start(con_session)
                    con_session.sendline("picocom -q -b 115200 -f h /dev/ttyS1")

                    #self.nic_con.uart_session_stop(con_session)

                    #if ret != 0:
                    #    print("Fail to connect uboot")
                    #    return

                    j2c_session = common.session_start()

                    # Helen's procedure
                    print("=== TCL ENV setup ===")
                    common.session_cmd(j2c_session, "export ASIC_LIB_BUNDLE="+tcl_path)
                    common.session_cmd(j2c_session, "export ASIC_SRC=$ASIC_LIB_BUNDLE/asic_src")
                    common.session_cmd(j2c_session, "export ASIC_LIB=$ASIC_LIB_BUNDLE/asic_lib")
                    common.session_cmd(j2c_session, "export ASIC_GEN=$ASIC_SRC")
                    common.session_cmd(j2c_session, "export LD_LIBRARY_PATH=$ASIC_LIB_BUNDLE/depend_libs/tool/lib64:$ASIC_LIB_BUNDLE/depend_libs/mtp_hack:$ASIC_LIB_BUNDLE/asic_lib:$ASIC_LIB_BUNDLE/depend_libs/usr/local/lib")
                    common.session_cmd(j2c_session, "env | grep -e ASIC -e LD")

                    common.session_cmd(j2c_session, "cd $ASIC_SRC/ip/cosim/tclsh")
                    common.session_cmd(j2c_session, "cd $ASIC_LIB_BUNDLE/asic_lib")
                    common.session_cmd(j2c_session, "source source_env_path")
                    common.session_cmd(j2c_session, "mkdir -p $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
                    common.session_cmd(j2c_session, "export LD_LIBRARY_PATH=$ASIC_LIB_BUNDLE/depend_libs/mtp_hack:$LD_LIBRARY_PATH")
                    common.session_cmd(j2c_session, "ln -sf $ASIC_LIB_BUNDLE/depend_libs/lib64/libJudy.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
                    common.session_cmd(j2c_session, "ln -sf $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
                    common.session_cmd(j2c_session, "ln -sf $ASIC_LIB_BUNDLE/depend_libs/lib64/libgmpxx.so.4 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
                    common.session_cmd(j2c_session, "ln -sf $ASIC_LIB_BUNDLE/depend_libs/lib64/libcrypto.so.10 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
                    common.session_cmd(j2c_session, "ln -sf $ASIC_LIB_BUNDLE/depend_libs/lib64/libpcap.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
                    #common.session_cmd(j2c_session, "")

                    common.session_cmd(j2c_session, "cd $ASIC_SRC/ip/cosim/tclsh")

                    # TCL command
                    ret = common.session_cmd(j2c_session, "tclsh", 40, False, ending=["%", "tclsh]"])
                    if ret == 1:
                        common.session_cmd(j2c_session, "source .tclrc.diag.elb", 40, False, "tclsh]")

                    common.session_cmd(j2c_session, "set slot {}".format(slot), 30, False, "tclsh]")
                    common.session_cmd(j2c_session, "set port [mtp_get_j2c_port $slot]", 30, False, "tclsh]")
                    common.session_cmd(j2c_session, "set slot1 [mtp_get_j2c_slot $slot]", 30, False, "tclsh]")
                    common.session_cmd(j2c_session, "diag_close_j2c_if $port $slot1", 30, False, "tclsh]")
                    common.session_cmd(j2c_session, "diag_open_j2c_if $port $slot1", 30, False, "tclsh]")
                    common.session_cmd(j2c_session, "_msrd", 30, False, "tclsh]")

                    if pc_mode == "gpio3":
                        common.session_cmd(j2c_session, "elb_power_cycle_thro_gpio3 $port $slot1", 30, False, "tclsh]")

                    common.session_cmd(j2c_session, "source "+script_path+"/"+start_tcl, 120, False, "tclsh]")

                except pexpect.TIMEOUT:
                    print(slot, "DDR test failed")
                    common.session_stop(j2c_session)
                    return

                ret = self.nic_con.uart_session_cmd(con_session, "g", 10, ending=["Loading Environment from Flash", "Resetting CPU"])

                print("ret:", ret)
                if ret != 0:
                    print("=== Booting to alt FW!!! EXIT ===")
                    self.nic_con.uart_session_stop(con_session)
                    common.session_stop(con_session)

                    common.session_cmd(j2c_session, "exit", 10)
                    common.session_stop(j2c_session)
                    continue
                time.sleep(1)
                self.nic_con.uart_session_stop(con_session)

                print("Sleep 30 sec")
                time.sleep(30)
                ret = self.nic_con.uart_session_start(con_session)
                if ret != 0:
                    self.nic_con.uart_session_stop(con_session)
                    return

                self.nic_con.uart_session_cmd(con_session, "export CARD_TYPE=ORTANO2", 10)
                self.nic_con.uart_session_cmd(con_session, "/data/nic_util/devmgr -status", 20)

                self.nic_con.uart_session_cmd(con_session, "/nic/bin/ddr_test.sh", 70)

                self.nic_con.uart_session_cmd(con_session, "/data/nic_util/devmgr -status", 20)
                self.nic_con.uart_session_stop(con_session)

                common.session_cmd(j2c_session, "source "+script_path+"/"+stop_tcl, 10, False, "tclsh]")
                common.session_cmd(j2c_session, "exit", 10)

                common.session_stop(j2c_session)
                common.session_stop(con_session)

    def edma(self, nic_list=[], num_ite=1, num_edma=20):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        for ite in range(num_ite):
            print("=== Ite:", ite, "===")
            slot_list = ",".join(nic_list)
            print("slot_list:", slot_list)

            for slot in nic_list:
                try:
                    session = common.session_start()
                    common.session_cmd(session, "killall picocom", 20)
                    self.nic_con.power_cycle_multi(self.baud_rate, slot, 30)
                    ret = self.nic_con.uart_session_start(session, self.baud_rate)
                    if ret != 0:
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        continue
                    
                    for edma_ite in range(num_edma):
                        self.nic_con.uart_session_cmd(session, "export CARD_TYPE=ORTANO2", 10)
                        self.nic_con.uart_session_cmd(session, "/nic/bin/ddr_test.sh", 70)
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/devmgr -status", 20)

                    self.nic_con.uart_session_stop(session)

                    common.session_cmd(session, "cd ~/diag/scripts/asic/; tclsh get_nic_sts.tcl "+slot, 120)
                    common.session_stop(session)

                except pexpect.TIMEOUT:
                    print(slot, "DDR test failed")
                    common.session_stop(j2c_session)
                    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-two_step_edma", "--two_step_edma", help="Two step EDMA test", action='store_true')
    group.add_argument("-edma", "--edma", help="EDMA test", action='store_true')

    parser.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser.add_argument("-num_ite", "--num_ite", help="Number of iterations", type=int, default=1)
    parser.add_argument("-num_edma", "--num_edma", help="Number of edma iterations", type=int, default=1)

    parser.add_argument("-pc_mode", "--pc_mode", help="Power cycle mode; board: whole board PC; gpio3: GPIO3 PC", type=str, default="board")
    parser.add_argument("-tcl_dir", "--tcl_dir", help="TCL directory", type=str, default="/home/diag/diag/asic/")
    parser.add_argument("-script_dir", "--script_dir", help="script directory", type=str, default="/home/diag/diag/scripts/asic/")
    parser.add_argument("-start_tcl", "--start_tcl", help="Start tcl file", type=str, default="start.tcl")
    parser.add_argument("-stop_tcl", "--stop_tcl", help="Stop tcl file", type=str, default="stop.tcl")

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    test = ddr_test()

    if args.two_step_edma == True:
        slot_list = args.slot_list.split(',')
        test.two_step_edma(slot_list, args.num_ite, args.tcl_dir, args.script_dir, args.start_tcl, args.stop_tcl, args.pc_mode)
        sys.exit()

    if args.edma == True:
        slot_list = args.slot_list.split(',')
        test.edma(slot_list, args.num_ite, args.num_edma)
        sys.exit()

    parser.print_help()
