#!/usr/bin/env python

import argparse
import datetime
import math
import pexpect
import os
import random
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
                    self.nic_con.switch_console(int(slot))
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

                    ret = common.session_cmd(j2c_session, "source "+script_path+"/"+start_tcl, 120, False, ["tclsh]", "j2c : read req error", "j2c : write req error"])
                    if ret != 1:
                        common.session_cmd(j2c_session, chr(3))
                        common.session_cmd(j2c_session, "inventory -sts -slot "+str(slot), 30)
                        common.session_stop(j2c_session)

                        self.nic_con.uart_session_stop(con_session)
                        common.session_stop(con_session)
                        print("=== J2C failure happened! EXITING ===")
                        continue

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
                    print("Connecting to console failed!")
                else:
                    self.nic_con.uart_session_cmd(con_session, "export CARD_TYPE=ORTANO2A", 10)
                    self.nic_con.uart_session_cmd(con_session, "/data/nic_util/devmgr -status", 20)

                    self.nic_con.uart_session_cmd(con_session, "/nic/bin/ddr_test.sh", 70)

                    self.nic_con.uart_session_cmd(con_session, "/data/nic_util/devmgr -status", 20)

                self.nic_con.uart_session_stop(con_session)

                common.session_cmd(j2c_session, "source "+script_path+"/"+stop_tcl, 10, False, "tclsh]")
                common.session_cmd(j2c_session, "exit", 10)

                common.session_stop(j2c_session)
                common.session_stop(con_session)

    def two_step_snake(self, nic_list=[], num_ite=1, tcl_path="/home/diag/diag/asic/", script_path="/home/diag/diag/scripts/asic/", start_tcl="start.tcl", stop_tcl="stop.tcl", pc_mode="board"):
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

                    ret = common.session_cmd(j2c_session, "source "+script_path+"/"+start_tcl, 240, False, ["tclsh]", "j2c : read req error", "j2c : write req error"])
                    if ret != 1:
                        common.session_cmd(j2c_session, chr(3))
                        common.session_cmd(j2c_session, "inventory -sts -slot "+str(slot), 30)
                        common.session_stop(j2c_session)

                        self.nic_con.uart_session_stop(con_session)
                        common.session_stop(con_session)
                        print("=== J2C failure happened! EXITING ===")
                        continue

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

                print("Sleep 60 sec")
                time.sleep(60)
                ret = self.nic_con.uart_session_start(con_session)
                if ret != 0:
                    print("Connecting to console failed!")
                else:
                    self.nic_con.uart_session_cmd(con_session, "mount /dev/mmcblk0p10 /data/", 30)
                    self.nic_con.uart_session_cmd(con_session, "source /data/nic_arm/nic_setup_env.sh", 30)
                    self.nic_con.uart_session_cmd(con_session, "source /etc/profile", 30)
                    self.nic_con.uart_session_cmd(con_session, "/data/nic_util/devmgr -status", 20)

                    ret = self.nic_con.uart_session_cmd_sig(con_session, "/data/nic_util/asicutil -snake -mode hod -dura 3 -verbose -int_lpbk -snake_num 6", 300, "\#", ["SNAKE TEST PASSED", "SNAKE TEST FAILED"])

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

                    self.nic_con.switch_console(int(slot))
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


    def qspi_edma_corruption(self, nic_list=[], num_ite=1, num_edma=20):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        for ite in range(num_ite):
            print("=== Ite:", ite, "===")
            slot_list = ",".join(nic_list)
            print("slot_list:", slot_list)

            slot_list = ",".join(nic_list)
            self.nic_con.power_cycle_multi(self.baud_rate, slot_list, 60)

            for slot in nic_list:
                try:
                    self.nic_con.switch_console(int(slot))
                    session = common.session_start()
                    common.session_cmd(session, "killall picocom", 20)
                    ret = self.nic_con.uart_session_start(session, self.baud_rate)
                    if ret != 0:
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        continue

                    # Check if diagfw is active
                    [ret, ot] = self.nic_con.uart_session_cmd_w_ot(session, "fwupdate -r")
                    if "diagfw" not in ot:
                        print "=== FAILURE happened: slot {} failed to boot into diagfw".format(slot)
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        return

                    self.nic_con.uart_session_stop(session)

                    common.session_stop(session)

                except pexpect.TIMEOUT:
                    print(slot, "diagfw checking failed!")
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    return

            print("{} passed diagfw checking".format(slot_list))

            # start edma test
            for slot in nic_list:
                try:
                    self.nic_con.switch_console(int(slot))
                    session = common.session_start()
                    common.session_cmd(session, "killall picocom", 20)
                    ret = self.nic_con.uart_session_start(session, self.baud_rate)
                    if ret != 0:
                        print("Failed to connect UART of slot", slot)
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        return

                    self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data/", 30)
                    session.sendline("/data/run_edma_ite.sh 100")
                    time.sleep(5)
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)

                except pexpect.TIMEOUT:
                    print(slot, "Running EDMA failed!")
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    return

            sleep_in_sec = random.randrange(240, 300)
            print("Sleep for", sleep_in_sec, "sec")
            time.sleep(sleep_in_sec)

    def qspi_snake_corruption(self, nic_list=[], num_ite=1):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        for ite in range(num_ite):
            print("=== Ite:", ite, "===")
            slot_list = ",".join(nic_list)
            print("slot_list:", slot_list)

            slot_list = ",".join(nic_list)
            session = common.session_start()
            common.session_cmd(session, "./nic_test.py -setup_multi -slot_list {}".format(slot_list), timeout=300, ending="Setup env top done")
            common.session_stop(session)

            for slot in nic_list:
                try:
                    self.nic_con.switch_console(int(slot))
                    session = common.session_start()
                    common.session_cmd(session, "killall picocom", 20)
                    ret = self.nic_con.uart_session_start(session, self.baud_rate)
                    if ret != 0:
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        continue

                    # Check if diagfw is active
                    [ret, ot] = self.nic_con.uart_session_cmd_w_ot(session, "fwupdate -r")
                    if "diagfw" not in ot:
                        print "=== FAILURE happened: slot {} failed to boot into diagfw".format(slot)
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        return

                    self.nic_con.uart_session_stop(session)

                    common.session_stop(session)

                except pexpect.TIMEOUT:
                    print(slot, "diagfw checking failed!")
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    return

            print("{} passed diagfw checking".format(slot_list))

            # start edma test
            for slot in nic_list:
                try:
                    self.nic_con.switch_console(int(slot))
                    session = common.session_start()
                    common.session_cmd(session, "killall picocom", 20)
                    ret = self.nic_con.uart_session_start(session, self.baud_rate)
                    if ret != 0:
                        print("Failed to connect UART of slot", slot)
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        return

                    session.sendline("/data/nic_util/asicutil -snake -mode hod -dura 3 -int_lpbk -snake_num 4")
                    time.sleep(5)
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)

                except pexpect.TIMEOUT:
                    print(slot, "Running EDMA failed!")
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    return

            sleep_in_sec = random.randrange(240, 540)
            print("Sleep for", sleep_in_sec, "sec")
            time.sleep(sleep_in_sec)

    def stress_reset(self, nic_list=[], num_ite=1):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        for ite in range(num_ite):
            print("=== Ite:", ite, "===")
            slot_list = ",".join(nic_list)
            print("slot_list:", slot_list)

            slot_list = ",".join(nic_list)
            session = common.session_start()
            common.session_cmd(session, "cd ~/diag/python/regression/")
            common.session_cmd(session, "nic_test.py -snake -slot_list={} -wtime=3600 -snake_num=6 -dura=3600 -mode=hod_1100 -int_lpbk".format(slot_list), 600, ending="before checking result")
            print("=== Snake started: wait for 300 sec ===")
            time.sleep(300)

            session.sendline(chr(3))
            # sysreset all slots
            for slot in nic_list:
                try:
                    self.nic_con.switch_console(int(slot))
                    common.session_cmd(session, "killall picocom")
                    ret = self.nic_con.uart_session_start(session, self.baud_rate)
                    if ret != 0:
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        continue

                    session.sendline("sysreset.sh")
                    time.sleep(2)

                    self.nic_con.uart_session_stop(session)

                except pexpect.TIMEOUT:
                    print(slot, "diagfw checking failed!")
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    return

            # Check if cards are alive
            time.sleep(60)
            for slot in nic_list:
                try:
                    self.nic_con.switch_console(int(slot))
                    ret = self.nic_con.uart_session_start(session, self.baud_rate)
                    if ret != 0:
                        print("Failed to connect UART of slot", slot)
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        return

                    ret = self.nic_con.uart_session_cmd(session, "pwd")
                    self.nic_con.uart_session_stop(session)
                    if ret != 0:
                        print("=== slot {} failed to boot! ===".format(slot))
                        return
                    print("slot {} booted successfully".format(slot))

                except pexpect.TIMEOUT:
                    print(slot, "Running EDMA failed!")
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    return

    def chamber_temp_ctrl(self, low_temp, high_temp, interval, num_ite):
        cur_temp_corner = "LOW"
        chamber_ip = "192.168.70.216"
        session = common.session_start()
        common.session_cmd(session, "cd $ASIC_SRC/ip/cosim/tclsh")
        ret = common.session_cmd(session, "tclsh", 40, False, ending=["%", "tclsh]"])
        if ret == 1:
            common.session_cmd(session, "source .tclrc.diag.elb", 40, False, "tclsh]")
        common.session_cmd(session, "source ../capri/chamber_utils.tcl", 40, False, "tclsh]")
    
        for ite in range(num_ite):
            print("=== Ite: {} ===".format(ite))
            print("Current corner:", cur_temp_corner)
            for temp_loop in range(interval):
                print("=== temp_loop: {} ===".format(temp_loop))
                common.session_cmd(session, "set cur_temp [check_temp 192.168.70.216]", 40, False, ending="tclsh]")
                common.session_cmd(session, "puts \"cur_temp: $cur_temp\"", 40, False, ending="tclsh]")
                common.session_cmd(session, "exec devmgr -dev=fan -status", 40, False, ending="tclsh]")
                time.sleep(60)
            if cur_temp_corner == "LOW":
                cmd = "set_temp {} {}".format(chamber_ip, high_temp)
                ret = common.session_cmd(session, cmd, 40, False, ending="tclsh]")
                cur_temp_corner = "HIGH"
            else:
                cmd = "set_temp {} {}".format(chamber_ip, low_temp)
                ret = common.session_cmd(session, cmd, 40, False, ending="tclsh]")
                cur_temp_corner = "LOW"
        common.session_cmd(session, "exit")
        common.session_stop(session)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-two_step_edma", "--two_step_edma", help="Two step EDMA test", action='store_true')
    group.add_argument("-two_step_snake", "--two_step_snake", help="Two step Snake test", action='store_true')
    group.add_argument("-edma", "--edma", help="EDMA test", action='store_true')
    group.add_argument("-qspi_crpt", "--qspi_crpt", help="test", action='store_true')
    group.add_argument("-qspi_s_crpt", "--qspi_s_crpt", help="test", action='store_true')
    group.add_argument("-chamber_temp", "--chamber_temp", help="chamber_temp_control", action='store_true')
    group.add_argument("-stress_reset", "--stress_reset", help="stress/sysreset test", action='store_true')

    parser.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser.add_argument("-num_ite", "--num_ite", help="Number of iterations", type=int, default=1)
    parser.add_argument("-num_edma", "--num_edma", help="Number of edma iterations", type=int, default=1)

    parser.add_argument("-pc_mode", "--pc_mode", help="Power cycle mode; board: whole board PC; gpio3: GPIO3 PC", type=str, default="board")
    parser.add_argument("-tcl_dir", "--tcl_dir", help="TCL directory", type=str, default="/home/diag/diag/asic/")
    parser.add_argument("-script_dir", "--script_dir", help="script directory", type=str, default="/home/diag/diag/scripts/asic/")
    parser.add_argument("-start_tcl", "--start_tcl", help="Start tcl file", type=str, default="start.tcl")
    parser.add_argument("-stop_tcl", "--stop_tcl", help="Stop tcl file", type=str, default="stop.tcl")

    parser.add_argument("-low_temp", "--low_temp", help="Chamber temp low", type=int, default=25)
    parser.add_argument("-high_temp", "--high_temp", help="Chamber temp high", type=int, default=25)
    parser.add_argument("-interval", "--interval", help="Chamber temp control interval in minutes", type=int, default=60)

    try:
        args = parser.parse_args()
    except:
        #parser.print_help()
        sys.exit(0)

    test = ddr_test()

    if args.two_step_edma == True:
        slot_list = args.slot_list.split(',')
        test.two_step_edma(slot_list, args.num_ite, args.tcl_dir, args.script_dir, args.start_tcl, args.stop_tcl, args.pc_mode)
        sys.exit()

    if args.two_step_snake == True:
        slot_list = args.slot_list.split(',')
        test.two_step_snake(slot_list, args.num_ite, args.tcl_dir, args.script_dir, args.start_tcl, args.stop_tcl, args.pc_mode)
        sys.exit()

    if args.edma == True:
        slot_list = args.slot_list.split(',')
        test.edma(slot_list, args.num_ite, args.num_edma)
        sys.exit()

    if args.qspi_crpt == True:
        slot_list = args.slot_list.split(',')
        test.qspi_edma_corruption(slot_list, args.num_ite, args.num_edma)
        sys.exit()

    if args.qspi_s_crpt == True:
        slot_list = args.slot_list.split(',')
        test.qspi_snake_corruption(slot_list, args.num_ite)
        sys.exit()

    if args.stress_reset == True:
        slot_list = args.slot_list.split(',')
        test.stress_reset(slot_list, args.num_ite)
        sys.exit()

    if args.chamber_temp == True:
        test.chamber_temp_ctrl(args.low_temp, args.high_temp, args.interval, args.num_ite)
        sys.exit()

    parser.print_help()
