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
import threading
from collections import OrderedDict
from time import sleep

import datetime

sys.path.append("../lib")
import common
from nic_con import nic_con
from nic_test import nic_test
from nic_test_v2 import nic_test_v2

class ddr_test:
    def __init__(self):
        self.name = "ddr_test"
        self.baud_rate = 115200
        self.num_retry = 3
        self.nic_con = nic_con()
        self.nic_test = nic_test()
        self.nic_test_v2 = nic_test_v2()

    def two_step_edma(self, nic_list=[], num_ite=1, num_edma=5, tcl_path="/home/diag/diag/asic/", script_path="/home/diag/diag/scripts/asic/", start_tcl="start.tcl", stop_tcl="stop.tcl", pc_mode="board"):
        print "=== NIC DDR Test ==="
        print("num_ite:", num_ite)
        print("num_edma:", num_edma)
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
                        self.nic_con.power_cycle_multi(slot, 0)

                    #ret = self.nic_con.uart_session_start(con_session, slot)
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
                        common.session_cmd(j2c_session, "source .tclrc.diag.gig", 40, False, "tclsh]")

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
                    sys.exit(0)
                time.sleep(1)
                self.nic_con.uart_session_stop(con_session)

                print("Sleep 60 sec")
                time.sleep(60)
                ret = self.nic_con.uart_session_start(con_session, slot)
                if ret != 0:
                    print("Connecting to console failed!")
                else:
                    self.nic_con.uart_session_cmd(con_session, "export CARD_TYPE=GINESTRA_D5", 10)
                    #self.nic_con.uart_session_cmd(con_session, "cp /data/fru.json /tmp", 10)
                    #self.nic_con.uart_session_cmd(con_session, "cp /data/ddr_test.sh /nic/bin/", 10)
                    #self.nic_con.uart_session_cmd(con_session, "sysinit.sh classic hw diag", 10)
                    #self.nic_con.uart_session_cmd(con_session, "/data/nic_util/devmgr -status", 20)
                    print("num_edma:", num_edma)
                    for edma_ite in range(num_edma):
                        print("=== edma_ite:", edma_ite, "===")
                        self.nic_con.uart_session_cmd(con_session, "/nic/bin/ddr_test.sh", 270)
                        if 'Test FAILED' in con_session.before or 'TIMEOUT:' in con_session.before:
                            #self.nic_con.uart_session_stop(session)
                            #common.session_stop(session)
                            #return
                            print("Failed in ite:", edma_ite)
                            continue

                    #self.nic_con.uart_session_cmd(con_session, "/data/nic_util/devmgr -status", 20)

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
                        self.nic_con.power_cycle_multi(slot, 0)
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
                    sys.exit(0)
                time.sleep(1)
                self.nic_con.uart_session_stop(con_session)

                print("Sleep 60 sec")
                time.sleep(60)
                ret = self.nic_con.uart_session_start(con_session, slot)
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

    def edma(self, nic_list=[], num_ite=1, num_edma=20, vmarg="normal"):
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
                    self.nic_con.power_cycle_multi(slot, 30)

                    self.nic_con.switch_console(int(slot))
                    ret = self.nic_con.uart_session_start(session, slot)
                    if ret != 0:
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        continue
                    #self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data")
                    #self.nic_con.uart_session_cmd(session, "cp /data/fru.json /tmp/")
                    #self.nic_con.uart_session_cmd(session, "sysinit.sh classic hw diag")
                    #time.sleep(180)
                    self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data")
                    #self.nic_con.uart_session_cmd(session, "source /data/nic_arm/nic_setup_env.sh")
                    self.nic_con.uart_session_cmd(session, "export CARD_TYPE=GINESTRA_D5", 10)
                    vmarg = vmarg.replace('_', ' ')
                    self.nic_con.uart_session_cmd(session, "/data/nic_arm/vmarg.sh {}".format(vmarg))
                    print("num_edma:", num_edma)
                    for edma_ite in range(num_edma):
                        print("=== edma_ite:", edma_ite, "===")
                        #self.nic_con.uart_session_cmd(session, "export CARD_TYPE=ORTANO2", 10)
                        self.nic_con.uart_session_cmd(session, "/nic/bin/ddr_test.sh", 270)
                        if 'Test FAILED' in session.before or 'TIMEOUT:' in session.before:
                            #self.nic_con.uart_session_stop(session)
                            #common.session_stop(session)
                            #return
                            print("Failed in ite:", edma_ite)
                            continue
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/devmgr -status", 20)

                    self.nic_con.uart_session_stop(session)

                    #common.session_cmd(session, "cd ~/diag/scripts/asic/; tclsh get_nic_sts.tcl "+slot, 120)
                    common.session_stop(session)

                except pexpect.TIMEOUT:
                    print(slot, "DDR test failed")
                    common.session_stop(j2c_session)
                    return

    def nic_edma_and_stress(self, slot, num_edma, num_stress, vmarg):
        try:
            session = common.session_start()
            session.sendline("ssh_s.sh {}".format(slot))
            session.expect("\#")
            session.sendline("/data/nic_util/eeutil -disp -field sn")
            session.expect("\#")
            vmarg = vmarg.replace('_', ' ')
            session.sendline("/data/nic_arm/vmarg.sh {}".format(vmarg))
            session.expect("\#")
            print("num_edma:", num_edma)
            edma_fail = 0
            for edma_ite in range(num_edma):
                print("=== edma_ite:", edma_ite, "===")
                session.timeout = 270
                session.sendline("/nic/bin/ddr_test.sh")
                session.expect("\#")
                if 'Test FAILED' in session.before or 'TIMEOUT:' in session.before:
                    #self.nic_con.uart_session_stop(session)
                    #common.session_stop(session)
                    #return
                    print("Failed in ite:", edma_ite)
                    edma_fail = 1
                    break
            if edma_fail == 1:
                session.sendline("exit")
                session.expect("\$")
                common.session_cmd(session, "cd ~/diag/scripts/asic/; tclsh get_nic_sts.tcl slot_{} {} 0".format(slot, slot), 120)
                common.session_stop(session)
                #continue
                return
            else:
                session.sendline("/data/nic_util/devmgr -status")
                session.expect("\#")
            print("num_stress:", num_stress)
            stress_fail = 0
            for stress_ite in range(num_stress):
                print("=== stress_ite:", stress_ite, "===")
                # clear interrupts before test
                session.sendline("halctl clear interrupts")
                session.expect("\#")
                time.sleep(10)
                # ECC check before test
                session.sendline("halctl show interrupts | grep -i mcc")
                session.expect("\#")
                if 'int_mcc_ecc' in session.before or 'int_mcc_controller' in session.before:
                    print("New interrupts before stress test, failed in ite:", stress_ite)
                    stress_fail = 1
                    break
                #raw_input("Press Enter to continue...")
                session.timeout = 360
                session.sendline("/data/nic_util/stressapptest_arm -m 16 -i 16 -C 16 -M 20000 -s 60")
                session.expect("\#")
                if 'Status: PASS' not in session.before:
                    #self.nic_con.uart_session_stop(session)
                    #common.session_stop(session)
                    #return
                    print("Failed in ite:", stress_ite)
                    stress_fail = 1
                    #break
                time.sleep(3)
                # ECC check
                session.sendline("halctl show interrupts | grep -i mcc")
                session.expect("\#")
                if 'int_mcc_ecc' in session.before or 'int_mcc_controller' in session.before:
                    print("Failed in ite:", stress_ite)
                    stress_fail = 1
                    break
            if stress_fail == 1:
                session.sendline("exit")
                session.expect("\$")
                common.session_cmd(session, "cd ~/diag/scripts/asic/; tclsh get_nic_sts.tcl slot_{} {} 0".format(slot, slot), 120)
                common.session_stop(session)
                #continue
                return
            else:
                session.sendline("/data/nic_util/devmgr -status")
                session.expect("\#")

            #common.session_cmd(session, "cd ~/diag/scripts/asic/; tclsh get_nic_sts.tcl slot_{} {}".format(slot, slot), 120)
            session.sendline("exit")
            session.expect("\$")
            common.session_stop(session)

        except pexpect.TIMEOUT:
            print(slot, "DDR test failed")
            common.session_stop(session)
            return

    def edma_and_stress_parallel(self, nic_list=[], num_ite=1, num_edma=20, num_stress=20, vmarg="normal"):
        nic_thread_list = list()
        for ite in range(num_ite):
            print("=== Ite:", ite, "===")
            slot_list = ",".join(nic_list)
            print("slot_list:", slot_list)

            for slot in nic_list:
                nic_thread = threading.Thread(target = self.nic_edma_and_stress, args = (slot, num_edma, num_stress, vmarg))
                nic_thread.start()
                nic_thread_list.append(nic_thread)

            while True:
                if len(nic_thread_list) == 0:
                    break
                for nic_thread in nic_thread_list[:]:
                    if not nic_thread.is_alive():
                        ret = nic_thread.join()
                        nic_thread_list.remove(nic_thread)
                time.sleep(1)

    def set_temp_for_ddr(self, ip, temp):
        self.nic_test_v2.chamber_set_temp(ip, temp)
        self.nic_test.set_mtp_fan_speed(100)
        self.nic_test.mtp_sts(1200, 60)
        self.nic_test_v2.chamber_get_temp(ip)

    def chamber_test_init(self, nic_list=[]):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)
        #print("=====set chamber 20C=====")
        #self.set_temp_for_ddr('10.9.6.249', 20)
        print("=====power cycle=====")
        # power cycle
        self.nic_test.setup_env_multi_top(nic_list, True, 30, False, True, False)

    def chamber_test_snake(self, nic_list=[], num_ite=10):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)
        for ite in range(num_ite):
            #print("=====set chamber 20C=====")
            #self.set_temp_for_ddr('10.9.6.249', 20)
            print("=====power cycle=====")
            self.nic_test.setup_env_multi_top(nic_list, False, 30, False, True, False, 1, do_untar="0")
            #print("=====set chamber 45C=====")
            #self.set_temp_for_ddr('10.9.6.249', 45)
            print("=====run snake=====")
            test_result = OrderedDict()
            wait_time = 600
            num_retry = 10
            test_type = "snake"
            mode = "hod_1100"
            # Start snake
            for slot in nic_list:
                ret = self.nic_test.test_start(int(slot), test_type, mode, 30, "normal", "off", 120, True, 6)
                if ret != 0:
                    test_result[slot] = "FAIL"
                else:
                    test_result[slot] = "NO RESULT"

            print "Wait for {}s before checking result".format(wait_time)
            self.nic_test.mtp_sts(wait_time)

            done_count = 0
            for retry_idx in range(num_retry):
                print "Checking result:", retry_idx
                for slot in nic_list:
                    if test_result[slot] != "NO RESULT":
                        continue

                    test_sts = self.nic_test.test_check(int(slot), test_type, mode)
                    if test_sts == 0:
                        print "=== {} Result at Slot {}: Passed".format(test_type, slot)
                        test_result[slot] = "PASS"
                        done_count = done_count + 1
                    if test_sts == 1:
                        print "=== {} Result at Slot {}: Failed".format(test_type, slot)
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


    def chamber_test(self, nic_list=[], num_ite=1, num_edma=20, num_stress=20, vmarg="normal"):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)
        self.chamber_test_init(nic_list)
        print("=====run edma and stress=====")
        #self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "normal")
        #self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "high")
        #self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "low")
        #print("=====set chamber 25C=====")
        #self.set_temp_for_ddr('10.9.6.249', 25)
        #print("=====run edma and stress=====")
        #self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "normal")
        #self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "high")
        #self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "low")
        #print("=====set chamber 45C=====")
        #self.set_temp_for_ddr('10.9.6.249', 45)
        #print("=====run edma and stress=====")
        self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, vmarg)
        #self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "high")
        #self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "low")

        # print("=====set chamber 50C=====")
        # self.set_temp_for_ddr('10.9.6.249', 50)
        # print("=====power cycle=====")
        # # power cycle
        # self.nic_con.power_cycle_multi(slot_list, 30)
        # print("=====run edma and stress=====")
        # self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "normal")
        # self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "high")
        # self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "low")
        # print("=====set chamber 25C=====")
        # self.edma_and_stress_parallel('10.9.6.249', 25)
        # print("=====run edma and stress=====")
        # self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "normal")
        # self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "high")
        # self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "low")
        # print("=====set chamber 0C=====")
        # self.set_temp_for_ddr('10.9.6.249', 0)
        # print("=====run edma and stress=====")
        # self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "normal")
        # self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "high")
        # self.edma_and_stress_parallel(nic_list, num_ite, num_edma, num_stress, "low")


    def stress(self, nic_list=[], num_ite=1, num_stress=20, vmarg="normal"):
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
                    self.nic_con.power_cycle_multi(slot, 30)
                except pexpect.TIMEOUT:
                    print(slot, "DDR test failed during slot power on")
                    common.session_stop(j2c_session)
                    return

            for slot in nic_list:
                try:
                    self.nic_con.switch_console(int(slot))
                    ret = self.nic_con.uart_session_start(session, slot)
                    if ret != 0:
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        #sys.exit(0)
                        print("Failed to connect console")
                        continue
                    print("STARTING TEST ON SLOT:", slot)
                    print("STARTING TEST ON SLOT:", slot)
                    self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data;cd /data")
                    self.nic_con.uart_session_cmd(session, "export CARD_TYPE=ORTANO2AC", 10)
                    self.nic_con.uart_session_cmd(session, "export ASIC_TYPE=ELBA", 10)
                    self.nic_con.uart_session_cmd(session, "rm /data/stressapptest_arm.log")
                    self.nic_con.uart_session_cmd(session, "/data/nic_util/stressapptest_arm -m 12 -M 22000 -s 900 -l stressapptest_arm.log & pwd", 360)
                    time.sleep(3)
                    self.nic_con.uart_session_stop(session)

                    #common.session_cmd(session, "cd ~/diag/scripts/asic/; tclsh get_nic_sts.tcl "+slot, 120)
                    

                except pexpect.TIMEOUT:
                    print(slot, "DDR test failed")
                    common.session_stop(session)
                    return

            print("Sleep 100-1")
            time.sleep(100)
            print("Sleep 100-2")
            time.sleep(100)
            print("Sleep 100-3")
            time.sleep(100)
            print("Sleep 100-4")
            time.sleep(100)
            print("Sleep 100-5")
            time.sleep(100)
            print("Sleep 100-6")
            time.sleep(100)
            print("Sleep 100-7")
            time.sleep(100)
            print("Sleep 100-8")
            time.sleep(100)
            print("Sleep 100-9")
            time.sleep(100)
            time.sleep(25)
            for slot in nic_list:
                try:
                    self.nic_con.switch_console(int(slot))
                    ret = self.nic_con.uart_session_start(session, slot)
                    if ret != 0:
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        #sys.exit(0)
                        print("Failed to connect console")
                        continue
                    self.nic_con.uart_session_cmd(session, "pwd")
                    print("CHECKING RESULTS ON SLOT:", slot)
                    print("CHECKING RESULTS ON SLOT:", slot)
                    self.nic_con.uart_session_cmd(session, "cat stressapptest_arm.log", 15)
                    if 'Status: PASS' not in session.before:
                        print("Failed google stressapptest on slot:", slot)
                    self.nic_con.uart_session_cmd(session, "/data/nic_util/asicutil -checkecc", 15)
                    if 'ECC Check PASSED' not in session.before:
                        print("Failed google stressapptest ecc check on slot:", slot)

                    self.nic_con.uart_session_stop(session)
                    time.sleep(1)


                except pexpect.TIMEOUT:
                    print(slot, "DDR test check failed")
                    common.session_stop(session)
                    return

            common.session_stop(session)


    def liparielbastress(self, nic_list=[], num_ite=1, num_stress=20, vmarg="normal"):
        if len(nic_list) == 0:
            print "No ELBA specified -- Exit"
            sys.exit(0)

        for ite in range(num_ite):
            print("=== Ite:", ite, "===")
            slot_list = ",".join(nic_list)
            print("slot_list:", slot_list)

            for slot in nic_list:
               try:
                   session = common.session_start()
                   #common.session_cmd(session, "killall picocom", 20)
                   common.session_cmd(session, "cd /home/admin/tmp/eeupdate", 2)
                   slotnumber = int(slot) - 1
                   cmd = "./td.bash e{} off".format(slotnumber)
                   common.session_cmd(session, cmd, 2)
                   time.sleep(5)
                   cmd = "./td.bash e{} on".format(slotnumber)
                   common.session_cmd(session, cmd, 2)
                   time.sleep(5)
                   common.session_cmd(session, "cd -", 2)
            #        self.nic_con.power_cycle_multi(slot, 30)
               except pexpect.TIMEOUT:
                   print(slot, "DDR test failed during slot power on")
                   common.session_stop(session)
                   return

            for slot in nic_list:
                try:
                    #session = common.session_start()
                    #self.nic_con.switch_console(int(slot))
                    ret = self.nic_con.uart_session_start(session, slot)
                    if ret != 0:
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        #sys.exit(0)
                        print("Failed to connect console")
                        return
                    print("STARTING TEST ON SLOT:", slot)
                    print("STARTING TEST ON SLOT:", slot)
                    self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data;cd /data")
                    self.nic_con.uart_session_cmd(session, "export CARD_TYPE=LIPARIELBA", 10)
                    self.nic_con.uart_session_cmd(session, "export ASIC_TYPE=ELBA", 10)
                    self.nic_con.uart_session_cmd(session, "rm /data/stressapptest_arm.log")
                    self.nic_con.uart_session_cmd(session, "./devmgr -margin -dev VDDQ_DDR -pct -3")
                    self.nic_con.uart_session_cmd(session, "./devmgr -margin -dev VDD_DDR -pct -3")
                    self.nic_con.uart_session_cmd(session, "/data/stressapptest_arm -m 12 -M 22000 -s 900 -l stressapptest_arm.log & pwd", 360)
                    time.sleep(3)
                    self.nic_con.uart_session_stop(session)

                    #common.session_cmd(session, "cd ~/diag/scripts/asic/; tclsh get_nic_sts.tcl "+slot, 120)


                except pexpect.TIMEOUT:
                    print(slot, "DDR test failed")
                    common.session_stop(session)
                    return

            for x in range(0, 10):
                print("Sleep 100-", x)
                time.sleep(100)
            print("Sleeping while test completes")
            time.sleep(45)

            for slot in nic_list:
                try:
                    self.nic_con.switch_console(int(slot))
                    ret = self.nic_con.uart_session_start(session, slot)
                    if ret != 0:
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        #sys.exit(0)
                        print("Failed to connect console on slot", slot)
                        return
                    self.nic_con.uart_session_cmd(session, "pwd")
                    print("CHECKING RESULTS ON SLOT:", slot)
                    print("CHECKING RESULTS ON SLOT:", slot)
                    self.nic_con.uart_session_cmd(session, "cat stressapptest_arm.log", 15)
                    if 'Status: PASS' not in session.before:
                        print("Failed google stressapptest on slot:", slot)
                        common.session_stop(session)
                        return
                    self.nic_con.uart_session_cmd(session, "/data/asicutil -checkecc", 15)
                    if 'ECC Check PASSED' not in session.before:
                        print("Failed google stressapptest ecc check on slot:", slot)
                        common.session_stop(session)
                        return

                    self.nic_con.uart_session_cmd(session, "./devmgr -margin -dev VDDQ_DDR -pct 0")
                    self.nic_con.uart_session_cmd(session, "./devmgr -margin -dev VDD_DDR -pct 0")
                    self.nic_con.uart_session_stop(session)
                    time.sleep(1)


                except pexpect.TIMEOUT:
                    print(slot, "DDR test check failed")
                    common.session_stop(session)
                    return

            common.session_stop(session)


    def qspi_edma_corruption(self, nic_list=[], num_ite=1, num_edma=20):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        for ite in range(num_ite):
            print("=== Ite:", ite, "===")
            slot_list = ",".join(nic_list)
            print("slot_list:", slot_list)

            slot_list = ",".join(nic_list)
            self.nic_con.power_cycle_multi(slot_list, 60)

            for slot in nic_list:
                try:
                    self.nic_con.switch_console(int(slot))
                    session = common.session_start()
                    common.session_cmd(session, "killall picocom", 20)
                    ret = self.nic_con.uart_session_start(session, slot)
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
                    ret = self.nic_con.uart_session_start(session, slot)
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
                    ret = self.nic_con.uart_session_start(session, slot)
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
                    ret = self.nic_con.uart_session_start(session, slot)
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
                    ret = self.nic_con.uart_session_start(session, slot)
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
                    ret = self.nic_con.uart_session_start(session, slot)
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
    group.add_argument("-stress", "--stress", help="Stress test", action='store_true')
    group.add_argument("-liparielbastress", "--liparielbastress", help="Stress test", action='store_true')
    group.add_argument("-qspi_crpt", "--qspi_crpt", help="test", action='store_true')
    group.add_argument("-qspi_s_crpt", "--qspi_s_crpt", help="test", action='store_true')
    group.add_argument("-chamber_temp", "--chamber_temp", help="chamber_temp_control", action='store_true')
    group.add_argument("-stress_reset", "--stress_reset", help="stress/sysreset test", action='store_true')
    group.add_argument("-chamber_test", "--chamber_test", help="test", action='store_true')
    group.add_argument("-chamber_test_snake", "--chamber_test_snake", help="test", action='store_true')
    group.add_argument("-chamber_test_init", "--chamber_test_init", help="test", action='store_true')

    parser.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser.add_argument("-num_ite", "--num_ite", help="Number of iterations", type=int, default=1)
    parser.add_argument("-num_edma", "--num_edma", help="Number of edma iterations", type=int, default=1)
    parser.add_argument("-num_stress", "--num_stress", help="Number of stress iterations", type=int, default=1)
    parser.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=str, default="normal")

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
        test.two_step_edma(slot_list, args.num_ite, args.num_edma, args.tcl_dir, args.script_dir, args.start_tcl, args.stop_tcl, args.pc_mode)
        sys.exit()

    if args.two_step_snake == True:
        slot_list = args.slot_list.split(',')
        test.two_step_snake(slot_list, args.num_ite, args.tcl_dir, args.script_dir, args.start_tcl, args.stop_tcl, args.pc_mode)
        sys.exit()

    if args.edma == True:
        slot_list = args.slot_list.split(',')
        test.edma(slot_list, args.num_ite, args.num_edma, args.vmarg)
        sys.exit()

    if args.stress == True:
        slot_list = args.slot_list.split(',')
        test.stress(slot_list, args.num_ite, args.num_stress, args.vmarg)
        sys.exit()

    if args.liparielbastress == True:
        slot_list = args.slot_list.split(',')
        test.liparielbastress(slot_list, args.num_ite, args.num_stress, args.vmarg)
        sys.exit()

    if args.chamber_test == True:
        slot_list = args.slot_list.split(',')
        test.chamber_test(slot_list, args.num_ite, args.num_edma, args.num_stress, args.vmarg)
        sys.exit()

    if args.chamber_test_snake == True:
        slot_list = args.slot_list.split(',')
        test.chamber_test_snake(slot_list, args.num_ite)
        sys.exit()

    if args.chamber_test_init == True:
        slot_list = args.slot_list.split(',')
        test.chamber_test_init(slot_list)
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
