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

class nic_test_v2:
    def __init__(self):
        self.name = "nic_snake"
        self.baud_rate = 115200
        self.fmt_con_cmd = "con_connect.sh {}"
        self.nic_con = nic_con()
        self.nic_test = nic_test()
        self.encoding = common.encoding

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
                cmd = self.nic_con.get_connect_cmd(slot)
                uart_session.sendline(cmd)

                #uart_session = common.session_start()
                #cmd = self.nic_con.get_connect_cmd(slot)
                #uart_session.sendline(cmd)

                print("=== Slot:", slot, "===")
                self.nic_con.power_cycle_multi_via_3v3(slot, wtime=0, swm_lp=False)

                self.nic_con.uart_session_stop(uart_session)
                ret = self.nic_con.uart_session_start_login(uart_session, slot)

                #common.session_stop(uart_session)

                if ret != 0:
                    return -1
                self.nic_con.uart_session_stop(uart_session)
                #common.session_stop(uart_session)

                ## Winbond prog test
                #uart_session = common.session_start()
                ##ret = self.nic_con.uart_session_start(uart_session)
                #try:
                #    cmd = self.nic_con.get_connect_cmd(slot)
                #    uart_session.sendline(cmd)
                #    cmd = 'fwupdate -p /data/naples_gold_elba.tar -i all; sleep 10; echo "DIAGFW PROG DONE"'
                #    cmd = 'date;sleep 10; date; echo "DIAGFW PROG DONE"'
                #    cmd = "source /data/run_prog.sh"
                #    uart_session.timeout=1800
                #    uart_session.sendline(cmd)
                #    uart_session.expect("DIAGFW PROG DONE")
                #    #uart_session.expect("\#")
                #except pexpect.TIMEOUT:
                #    print "DIAGFW PROG FAILED!"
                #    sys.exit(0)
                #continue


                #ret = self.nic_con.uart_session_cmd(uart_session, cmd, 1800, "DIAGFW PROG DONE")
                #if ret != 0:
                #    return -1

                #self.nic_con.uart_session_stop(uart_session)
                #common.session_stop(uart_session)
                #continue

                # Setup ENV
                ret = self.nic_test.setup_env(int(slot), False, 30, args.first_pwr_on, False, False)
                if ret != 0:
                    return -1

                if args.fast == True:
                    common.session_stop(uart_session)
                    continue

                self.nic_con.get_mgmt_rdy(int(slot), args.first_pwr_on)
                if ret != 0:
                    return -1

                ret = self.nic_con.uart_session_start(uart_session, slot)
                if ret != 0:
                    return -1
                
                ret = self.nic_con.uart_session_cmd(uart_session, "sleep 15; ls", 30)
                if ret != 0:
                    return -1

                self.nic_con.uart_session_stop(uart_session)
                common.session_stop(uart_session)

                self.nic_con.get_mgmt_rdy(int(slot), args.first_pwr_on)
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
                cmd = self.nic_con.get_connect_cmd(slot)
                session.sendline(cmd)

                #session = common.session_start()

                print("=== Slot:", slot, "===")
                self.nic_con.power_cycle_multi(slot, wtime=0, swm_lp=False)

                ret = self.nic_con.uart_session_start_login(session, slot)
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

                ret = self.nic_con.uart_session_start(session, slot)
                if ret != 0:
                    return False
                try:
                    cmd_str = 'echo \"fwupdate -p /update/{} -i all; sleep 10; echo \"DIAGFW PROG DONE\" \" > /update/run_prog.sh'
                    cmd = cmd_str.format(args.img_fn)
                    self.nic_con.uart_session_cmd(session, cmd)
                    session.timeout=1800
                    session.sendline("source /update/run_prog.sh")
                    session.expect("DIAGFW PROG DONE")
                    #self.nic_con.uart_session_cmd(session, "fwupdate -s diagfw")
                    self.nic_con.uart_session_cmd(session, "pwd")
                except pexpect.TIMEOUT:
                    print ("DIAGFW PROG FAILED!")
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
                ret = self.nic_con.enter_uboot(session, slot)
                if ret == -1:
                    print ("=== Failed to change uboot board rate! Slot: {} ===".format(slot))
                    common.session_stop(session)
                    continue

                ret = self.nic_con.uart_session_start(session, slot)
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
        session=pexpect.spawn(cmd, encoding=self.encoding, codec_errors='ignore')
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
        session=pexpect.spawn(cmd, encoding=self.encoding, codec_errors='ignore')
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
            #cmd = self.nic_con.get_connect_cmd(slot)
            #session.sendline(cmd)

            # Copy image file to NIC
            cmd_str = "scp_s.sh ./{} {} /data/"
            cmd = cmd_str.format(args.img_fn, slot)
            ret = common.session_cmd(session, cmd)
            if ret != 0:
                print("P000")
                #return False

            ret = self.nic_con.uart_session_start(session, slot)
            if ret != 0:
                return False
            try:
                cmd_str = 'mount /dev/mmcblk0p10 /data; cd /data/; sync; flash_erase /dev/mtd0 0x69F0000 64; dd if={} of=/dev/mtd0 bs=64k seek=1695'
                cmd = cmd_str.format(args.img_fn)
                self.nic_con.uart_session_cmd(session, cmd, 60)
                self.nic_con.uart_session_cmd(session, "pwd")
            except pexpect.TIMEOUT:
                print ("UBOOT PROG FAILED!")
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
                ret = self.nic_con.uart_session_start(session, slot)
                if ret != 0:
                    return False

                # Copy image file to NIC
                try:
                    # clear interrupts before test
                    self.nic_con.uart_session_cmd(session, "halctl clear interrupts")
                    time.sleep(10)
                    # ECC check before test
                    self.nic_con.uart_session_cmd(session, "halctl show interrupts | grep -i mcc")
                    if 'int_mcc_ecc' in session.before or 'int_mcc_controller' in session.before:
                        print("New interrupts before stress test")
                        return False
                    cmd = "/data/nic_util/stressapptest_arm -M 20000 -s 60 -m 16 -l /data/nic_util/stressapptest.log"
                    ret = common.session_cmd(session, cmd, timeout=120, ending="Status: PASS - please verify no corrected errors")
                    if ret < 0:
                        print("P000", ret)
                        return False
                    time.sleep(3)
                    # ECC check
                    self.nic_con.uart_session_cmd(session, "halctl show interrupts | grep -i mcc")
                    if 'int_mcc_ecc' in session.before or 'int_mcc_controller' in session.before:
                        print("Failed ECC check")
                        return False
                except pexpect.TIMEOUT:
                    return False

                self.nic_con.uart_session_stop(session)
                common.session_stop(session)


    def parse_number_string(input_string):
        # Split the input string by commas to separate out individual elements
        elements = input_string.split(',')
        # This will hold all the numbers once they are parsed and expanded
        full_range = []
        
        # Loop through each element
        for element in elements:
            # Check if the element contains a dash, indicating a range
            if '-' in element:
                # Split the range into its start and end
                start, end = element.split('-')
                # Use range to generate all numbers from start to end (inclusive)
                full_range.extend(range(int(start), int(end) + 1))
            else:
                # If no dash, it's a single number, so just add it to the list
                full_range.append(int(element))
        
        return full_range

    def pcie_prbs(self, args):
        print("tcl_path:", args.tcl_path)

        session = common.session_start()
        # set spimode to be off
        cmd = "fpgautil spimode {} off".format(args.slot)
        common.session_cmd(session, cmd)

        cmd = "jtag_accpcie_salina clr {}".format(args.slot)
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
        if sal_con.enter_a35_zephyr(int(args.slot), session, warm_reset=False):
            print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
            ret = -1
            return ret
        print("Done with Zephyr boot up, now start tcl")

        # TCL command
        cmd = "tclsh ~/diag/scripts/asic/sal_pcie_prbs.tcl {} {} {} {}".format(args.slot, args.card_type, args.vmarg, args.dura)
        if args.card_type == "LENI" or args.card_type == "LENI48G":
            cmd = "tclsh ~/diag/scripts/asic/sal_pcie_prbs.leni.tcl"
            cmd += " {}".format(args.slot)
            cmd += " {}".format("LENI")
            cmd += " {}".format(args.vmarg)
            cmd += " {}".format(args.dura)
            cmd += " {}".format(args.mtp_clk)
        elif args.card_type == "POLLARA" or args.card_type == "LINGUA":
            cmd = "tclsh ~/diag/scripts/asic/sal_pcie_prbs.pollara.tcl"
            cmd += " {}".format(args.slot)
            cmd += " {}".format("LENI")
            cmd += " {}".format(args.vmarg)
            cmd += " {}".format(args.dura)
            cmd += " {}".format(args.mtp_clk)
        else:
            print(args.card_type, "not supported!")
            common.session_stop(session)
            return 0

        common.session_cmd(session, cmd, ending="PRBS TEST DONE", timeout=args.timeout)
        idx = session.expect(["PRBS test PASSED", "PRBS test FAILED", pexpect.TIMEOUT, "j2c : read req error", "min <= max", "sync failed"], args.timeout)

        if idx >= 1:
            print("ERROR :: PRBS test has failed!")
            ret = -1

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
            print ("Faied to dump pcie trace")
            return -1
        self.nic_con.uart_session_stop(uart_session)
        common.session_stop(uart_session)

        return 0

    def sal_pcie_prbs_v2(self, args):
        print("tcl_path:", args.tcl_path)

        session = common.session_start()
        # set spimode to be off
        cmd = "fpgautil spimode {} off".format(args.slot)
        common.session_cmd(session, cmd)

        cmd = "jtag_accpcie_salina clr {}".format(args.slot)
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
        if sal_con.enter_a35_zephyr(int(args.slot), session, warm_reset=False):
            print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
            ret = -1
            return ret
        print("Done with Zephyr boot up, now start tcl")

        # TCL command
        if args.card_type == "LENI" or args.card_type == "LENI48G":
            cmd = "tclsh ~/diag/scripts/asic/sal_pcie_prbs.leni.tcl {} {} {} {} {}".format(args.slot, "LENI", args.vmarg, args.dura, args.mtp_clk)
        elif args.card_type == "POLLARA" or args.card_type == "LINGUA":
            cmd = "tclsh ~/diag/scripts/asic/sal_pcie_prbs.pollara_v2.tcl -slot {} -card_type {} -vmarg {} -dura {} -mtp_clk {} -aw_txfir_ow {}".format(args.slot, "LENI", args.vmarg, args.dura, args.mtp_clk, args.aw_txfir_ow)
        else:
            print(args.card_type, "not supported!")
            common.session_stop(session)
            return 0

        common.session_cmd(session, cmd, ending="PRBS TEST DONE", timeout=args.timeout)
        idx = session.expect(["PRBS test PASSED", "PRBS test FAILED", pexpect.TIMEOUT, "j2c : read req error", "min <= max", "sync failed"], args.timeout)

        if idx >= 1:
            print("ERROR :: PRBS test has failed!")
            ret = -1

        common.session_stop(session)

        print("Dumping PCIe trace")
        uart_session = common.session_start()
        ret = self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=0)
        #ret = self.nic_con.uart_session_start(uart_session, args.slot, uart_id=0)
        if ret != 0:
            return ret
        try:
            self.nic_con.uart_session_cmd(uart_session, "pcieawd showparams", ending="uart:~\$")
            self.nic_con.uart_session_cmd(uart_session, "pcieawd showlog", ending="uart:~\$")
        except pexpect.TIMEOUT:
            print ("Faied to dump pcie trace")
            return -1
        self.nic_con.uart_session_stop(uart_session)
        common.session_stop(uart_session)

        return 0

    def nic_snake_mtp(self, args):
        ret = 0
        print("tcl_path:", args.tcl_path)

        session = common.session_start()
        # set spimode to be off
        #cmd = "fpgautil spimode {} off".format(args.slot)
        #common.session_cmd(session, cmd)
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

        if args.card_type == "POLLARA" or args.card_type == "LINGUA":
            if args.arm_freq == "default":
                if sal_con.enter_a35_zephyr(int(args.slot), session, warm_reset=False):
                    print("===== FAILED: slot {} couldn't boot Zephyr".format(args.slot))
                    ret = -1
                    return ret

            else:
                # Change the freq (includes warm reset), then boot to zephyr cleanly
                if sal_con.enter_a35_uboot(int(args.slot), session, warm_reset=False):
                    print("===== FAILED: slot {} couldn't boot Zephyr".format(args.slot))
                    ret = -1
                    return ret

                cmd = "tclsh ~/diag/scripts/asic/sal_arm_freq.tcl -slot {} -arm_freq {}".format(args.slot, args.arm_freq)
                common.session_cmd(session, cmd, timeout=60)

                if sal_con.enter_a35_zephyr(int(args.slot), session, warm_reset=True):
                    print("===== FAILED: slot {} couldn't boot Zephyr".format(args.slot))
                    ret = -1
                    return ret
#            if sal_con.enter_a35_zephyr(int(args.slot), session, v12_reset=args.v12_reset):
#                print("===== FAILED: slot {} couldn't boot Zephyr".format(args.slot))
#                ret = -1
#                return ret
        else:
            if args.snake_type == "esam_pktgen_llc_sor" or \
               args.snake_type == "esam_pktgen_ddr_burst_400G_no_mac" or \
               args.snake_type == "esam_pktgen_ddr_burst":
                print("ARM not booted")
            else:
                if sal_con.enter_n1_linux(int(args.slot), session, warm_reset=False, new_memory_layout=args.new_memory_layout):
                    print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
                    ret = -1
                    return ret

        cmd = "jtag_accpcie_salina clr {}".format(args.slot)
        common.session_cmd(session, cmd)

        # Disable WDT
        cmd = "i2cset -y {} 0x4f 0x1 0".format(int(args.slot)+2)
        common.session_cmd(session, cmd)
        cmd = "i2cget -y {} 0x4f 0x1".format(int(args.slot)+2)
        common.session_cmd(session, cmd)

        print("Start Vmarge")
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

        cmd = "i2cget -y {} 0x4f 0x1".format(int(args.slot)+2)
        common.session_cmd(session, cmd)

        print("Start tcl")
        # TCL command
        if args.card_type == "LENI" or args.card_type == "LENI48G":
            if args.snake_type == "esam_pktgen_llc_sor" or \
               args.snake_type == "esam_pktgen_ddr_burst_400G_no_mac" or \
               args.snake_type == "esam_pktgen_ddr_burst":
                new_vmarg = args.vmarg
            else:
                new_vmarg = "none"
            cmd = "tclsh ~/diag/scripts/asic/sal_snake.leni.tcl"
            cmd += " " + str(args.slot)
            cmd += " " + str(args.snake_type)
            cmd += " " + str(args.dura)
            cmd += " " + str(args.card_type)
            cmd += " " + str(new_vmarg)
            cmd += " " + str(args.int_lpbk)
            cmd += " " + str(args.mtp_clk)
        elif args.card_type == "POLLARA" or args.card_type == "LINGUA":
            cmd = "tclsh ~/diag/scripts/asic/sal_snake.pollara.tcl"
            cmd += " " + str(args.slot)
            cmd += " " + str(args.snake_type)
            cmd += " " + str(args.dura)
            cmd += " " + str(args.card_type)
            cmd += " " + str(args.vmarg)
            cmd += " " + str(args.int_lpbk)
            cmd += " " + str(args.ite)
            cmd += " " + str(args.mtp_clk)
            cmd += " " + str(args.lpmode)
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
        if args.snake_type != "esam_pktgen_llc_sor" and \
           args.snake_type != "esam_pktgen_ddr_burst_400G_no_mac" and \
           args.snake_type != "esam_pktgen_ddr_burst":
            uart_session = common.session_start()
            self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=0)
            if 0 != sal_con.exp_cmd(uart_session, "", pass_sig_list=["uart:~\$"], timeout=5)[0]:
                print("===== FAILED: slot {} A35 console is not responsive".format(args.slot))
                return -1
            self.nic_con.uart_session_stop(uart_session)
            if args.card_type != "POLLARA" and args.card_type != "LINGUA":
                uart_session = common.session_start()
                self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=1)
                if 0 != sal_con.exp_cmd(uart_session, "", pass_sig_list=["\#"], timeout=5)[0]:
                    print("===== FAILED: slot {} N1 console is not responsive".format(args.slot))
                    return -1
                self.nic_con.uart_session_stop(uart_session)
                common.session_stop(uart_session)
        return ret

    def nic_snake(self, slot, ite, mode, dura, vmarg, int_lpbk, verbose, snake_num, timeout):
        for idx in range(ite):
            print("=== Ite", idx, "===")
            sts = "NO RESULT"
            ret = self.setup_env(slot, False, False, True, "elba", False, False, 2, "0")
            if ret == 0:
                int_lpbk_str = ""
                if int_lpbk == True:
                    int_lpbk_str = "-int_lpbk"
                verbose_str = ""
                if verbose == True:
                    verbose_str = "-verbose"

                session = common.session_start()
                ret = self.nic_con.uart_session_start(session, slot)
                if ret == 0:
                    vmarg = vmarg.replace('_', ' ')
                    try:
                        self.nic_con.uart_session_cmd(session, "/data/nic_arm/vmarg.sh {}".format(vmarg))
                        cmd = ("date; "
                                "/data/nic_util/asicutil -snake "
                                "-mode {} -dura {} {} {} -snake_num {}; "
                                "date").format(mode, dura, verbose_str, int_lpbk_str, snake_num)
                        sig = ["SNAKE TEST PASSED", "SNAKE TEST FAILED"]
                        ret = self.nic_con.uart_session_cmd_sig(session, cmd, timeout, "\#", sig, verbose)
                        if ret == 0:
                            print ("=== snake Result at Slot {}: Passed".format(slot))
                            sts = "PASS"
                        elif ret == 1:
                            print ("=== snake Result at Slot {}: Failed".format(slot))
                            sts = "FAIL"
                    except pexpect.TIMEOUT:
                        ret = -1
                self.nic_con.uart_session_stop(session)
                common.session_stop(session)
            # Print result
            print("\n====== TEST RESULT: SNAKE {:<5} ======".format(mode.upper()))
            print ("Slot {:<2}: {:<5}".format(slot, sts))
            print("======================================")
        return ret

    def nic_snake_parallel(self, args):
        print(args)
        # run nic_snake in parallel
        slot_list = args.slot_list.split(',')
        test_args = (args.ite, args.mode, args.dura, args.vmarg, args.int_lpbk, args.verbose, args.snake_num, args.timeout)
        test_kwargs = {}
        fail_nic_list = self.split_into_threads(self.nic_snake, slot_list, *test_args, **test_kwargs)
        print ("Failed NIC list:", fail_nic_list)

    def nic_snake_single(self, args):
        print(args)
        ret = self.nic_snake(args.slot, args.ite, args.mode, args.dura, args.vmarg, args.int_lpbk, args.verbose, args.snake_num, args.timeout)
        return ret

    def nic_pcie_prbs(self, slot, mode, dura, lpbk, poly, vmarg, timeout):
        print ("=== ARM {} PRBS {} {} {}".format(mode, dura, lpbk, vmarg))
        sts = "NO RESULT"
        ret = self.setup_env(slot, False, False, True, "elba", False, False, 2, "")
        if ret == 0:
            print ("=== Starting NIC arm {} prbs {} {} on slot {} ===".format(mode, dura, lpbk, slot))
            vmarg = vmarg.replace('_', ' ')
            session = common.session_start()
            ret = self.nic_con.uart_session_start(session, slot)
            if ret == 0:
                try:
                    self.nic_con.uart_session_cmd(session, "/data/nic_arm/vmarg.sh {}".format(vmarg))
                    cmd = ("date; "
                            "/data/nic_arm/nic/asic_src/ip/cosim/tclsh/nic_prbs.sh {} {} {} {};"
                            "date").format(mode, dura, lpbk, poly)
                    sig = ["PCIE PRBS PASSED", "FAILED"]
                    ret = self.nic_con.uart_session_cmd_sig(session, cmd, timeout, "\#", sig, False)
                    if ret == 0:
                        print ("=== Result at Slot {}: Passed".format(slot))
                        sts = "PASSED"
                    elif ret == 1:
                        print ("=== Result at Slot {}: Failed".format(slot))
                        sts = "FAILED"
                except pexpect.TIMEOUT:
                    ret = -1
            self.nic_con.uart_session_stop(session)
            common.session_stop(session)

        # Print result
        print ("\n====== NIC ARM {} PRBS TEST RESULT: ======".format(mode))
        print ("Slot {:<2}: {:<5}".format(slot, sts))
        print ("======================================")
        return ret

    def nic_pcie_prbs_parallel(self, args):
        print(args)
        slot_list = args.slot_list.split(',')
        test_args = (args.mode, args.dura, args.lpbk, args.poly, args.vmarg, args.timeout)
        test_kwargs = {}
        fail_nic_list = self.split_into_threads(self.nic_pcie_prbs, slot_list, *test_args, **test_kwargs)
        print ("Failed NIC list:", fail_nic_list)

    def nic_pcie_prbs_single(self, args):
        print(args)
        ret = self.nic_pcie_prbs(args.slot, args.mode, args.dura, args.lpbk, args.poly, args.vmarg, args.timeout)
        return ret

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

                #self.nic_con.switch_console(slot)
                session = common.session_start()
                # with con_connect.sh, the first iteration always times out
                ret = self.nic_con.uart_session_start(session, slot, numRetry=2)
                if ret != 0:
                    self.nic_con.uart_session_stop(session)
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

    def split_into_threads(self, func, nic_list, *test_args, **test_kwargs):
        def single_thread_func(func, slot, thread_rslt_list, *test_args, **test_kwargs):
            try:
                ret = func(slot, *test_args, **test_kwargs)
                if ret != 0:
                    thread_rslt_list[int(slot) - 1] = False
            except Exception:
                thread_rslt_list[int(slot) - 1] = False

        nic_thread_list = list()
        fail_nic_list = list()
        thread_rslt_list = [True] * 10
        for slot in nic_list:
            thread_args = tuple([func, slot, thread_rslt_list]) + test_args
            nic_thread = threading.Thread(
                target = single_thread_func,
                args = thread_args,
                kwargs = test_kwargs
            )
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)
            time.sleep(1)

        # monitor all the thread
        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(1)
        for idx, slot_rslt in enumerate(thread_rslt_list):
            if not slot_rslt:
                fail_nic_list.append(idx + 1)
        return fail_nic_list

    def setup_env_parallel(self, args):
        print(args)
        # run setup_env_single in parallel
        slot_list = args.slot_list.split(',')
        test_args = ()
        test_kwargs = {"mgmt": args.mgmt, "first_pwr_on": args.first_pwr_on, "pwr_cycle": not args.no_pwr_cycle, "asic_type": args.asic_type, "uefi": args.uefi, "dis_net_port": args.dis_net_port, "numRetry": 1, "do_untar": ""}
        fail_nic_list = self.split_into_threads(self.setup_env, slot_list, *test_args, **test_kwargs)
        print ("Failed NIC list:", fail_nic_list)

    def setup_env_single(self, args):
        print(args)
        if args.asic_type == "elba":
            ret = self.setup_env(args.slot, args.mgmt, args.first_pwr_on, not args.no_pwr_cycle, args.asic_type, args.uefi, args.dis_net_port, 1, "")
        elif args.asic_type == "salina":
            ret = self.setup_env_salina(args.slot, args.mgmt, args.first_pwr_on, not args.no_pwr_cycle, args.asic_type, args.uefi, args.dis_net_port, 1, "")
        else:
            ret = -1
            printf("asic type is not supported")
        return ret

    # setup_env for single slot elba
    def setup_env(self, slot, mgmt=False, first_pwr_on=False, pwr_cycle=True, asic_type="elba", uefi=False, dis_net_port=False, numRetry=1, do_untar=""):
        for retry in range(numRetry):
            print("Setting up #{}".format(retry))
            print("slot", slot)
            print("timestamp", datetime.datetime.now().time())
            try:
                session_uart = common.session_start()
                session_uart.timeout = 30
                ret = self.nic_con.uart_session_connect(session_uart, slot)
                if ret != 0:
                    self.nic_con.uart_session_stop(session_uart)
                    common.session_stop(session_uart)
                    continue
                if pwr_cycle == True:
                    session_bash = common.session_start()
                    session_bash.timeout = 30
                    cmd = "turn_on_slot.sh off {}".format(slot)
                    common.session_cmd(session_bash, cmd, 60)
                    time.sleep(1)
                    cmd = "turn_on_slot.sh on {}".format(slot)
                    common.session_cmd(session_bash, cmd, 60)

                ret = self.nic_con.uart_session_wait_for_login(session_uart)
                if ret != 0:
                    self.nic_con.uart_session_stop(session_uart)
                    common.session_stop(session_uart)
                    common.session_stop(session_bash)
                    continue
                print("=== Starting setup env on slot {} ===".format(slot))
                # get_mtp_rev() not work on Matera, hard code for now
                #mtp_rev = self.nic_test.get_mtp_rev()
                mtp_rev = "REV_04"
                print("MTP_REV: ", mtp_rev)
                self.nic_con.uart_session_cmd(session_uart, "fsck -y /dev/mmcblk0p10")
                self.nic_con.uart_session_cmd(session_uart, "mount /dev/mmcblk0p10 /data")
                self.nic_con.uart_session_cmd(session_uart, "source /data/nic_arm/nic_setup_env.sh " + do_untar, 120)
                self.nic_con.uart_session_cmd(session_uart, "source /etc/profile", 10)
                self.nic_con.uart_session_cmd(session_uart, "/data/nic_util/xo3dcpld -w 1 0x0")
                self.nic_con.uart_session_cmd(session_uart, "/data/nic_util/xo3dcpld -r 1")
                self.nic_con.uart_session_cmd(session_uart, "cd /data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
                self.nic_con.uart_session_cmd(session_uart, "export PCIE_ENABLED_PORTS=0")
                self.nic_con.uart_session_cmd(session_uart, "export MTP_REV="+mtp_rev)
                # if this file exists, it means the card is not rebooted
                self.nic_con.uart_session_cmd(session_uart, "touch /root/reboot_check")

                if mgmt == True:
                    ret = self.nic_con.enable_mnic(int(slot), first_pwr_on, session_uart)
                    print("Sleep 30 sec")
                    time.sleep(30)
                    # Disable link manager
                    # Not Pretty..depedning on the f/w version running the command to bring a port to the down state may be different
                    #time.sleep(5)
                    self.nic_con.uart_session_cmd(session_uart, "halctl debug port --port 1 --admin-state down")
                    self.nic_con.uart_session_cmd(session_uart, "halctl debug port --port 5 --admin-state down")
                    if asic_type == "ELBA":
                        self.nic_con.uart_session_cmd(session_uart, "halctl debug port --admin-state down")
                    #self.nic_con.uart_session_cmd(session_uart, "halctl debug port --port eth1/1 --admin-state down")
                    #self.nic_con.uart_session_cmd(session_uart, "halctl debug port --port eth1/2 --admin-state down")
                    self.nic_con.uart_session_cmd(session_uart, "halctl show port status")
                    if dis_net_port == True:
                        self.nic_con.uart_session_cmd(session_uart, "/data/nic_util/xo3dcpld -smiwr 0 0x3 0x1940")
                        self.nic_con.uart_session_cmd(session_uart, "/data/nic_util/xo3dcpld -smird 0 0x3")
                    sleep(0.5)
                    ret = self.nic_con.get_mgmt_rdy(int(slot), first_pwr_on, True, asic_type, uefi, dis_net_port, session_bash, session_uart)

                self.nic_con.uart_session_stop(session_uart)
                common.session_stop(session_uart)
                common.session_stop(session_bash)

            except pexpect.TIMEOUT:
                print("=== TIMEOUT: Failed to set up env single slot {} ===".format(slot))
                ret = -1

            if ret == 0:
                break

        if ret != 0:
            print("=== Setup env single slot failed! failed slot:", slot)
        else:
            print("=== Setup env single slot done #", retry, "===")
        print("timestamp", datetime.datetime.now().time())
        return ret

    # setup_env for single slot salina
    def setup_env_salina(self, slot, mgmt=False, first_pwr_on=False, pwr_cycle=True, asic_type="salina", uefi=False, dis_net_port=False, numRetry=1, do_untar=""):
        for retry in range(numRetry):
            print("Setting up #{}".format(retry))
            print("slot", slot)
            print("timestamp", datetime.datetime.now().time())
            try:
                ret = 0
                card_type = self.nic_con.get_card_type(slot)

                if card_type != "LENI" and card_type != "LENI48G" and card_type != "MALFA":
                    print("======setup_env on slot {} is not supported for non LENI/LENI48 card======".format(slot))
                    break              
                session_bash = common.session_start()
                session_bash.timeout = 90
                if pwr_cycle == True:
                    if sal_con.enter_n1_linux(int(slot), session_bash, warm_reset=False):
                        print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
                        common.session_stop(session_bash)
                        continue
                session_uart = common.session_start()
                session_uart.timeout = 60
                ret = self.nic_con.uart_session_start(session_uart, slot)
                if ret != 0:
                    self.nic_con.uart_session_stop(session_uart)
                    common.session_stop(session_uart)
                    continue
                print("=== Starting setup env on slot {} ===".format(slot))
                # get_mtp_rev() not work on Matera, hard code for now
                #mtp_rev = self.nic_test.get_mtp_rev()
                mtp_rev = "REV_04"
                print("MTP_REV: ", mtp_rev)
                self.nic_con.uart_session_cmd(session_uart, "fsck -y /dev/mmcblk0p10")
                self.nic_con.uart_session_cmd(session_uart, "mount /dev/mmcblk0p10 /data")
                self.nic_con.uart_session_cmd(session_uart, "source /data/nic_arm/nic_salina_setup_env.sh " + do_untar, 120)
                self.nic_con.uart_session_cmd(session_uart, "export MTP_REV="+mtp_rev)
                # if this file exists, it means the card is not rebooted
                self.nic_con.uart_session_cmd(session_uart, "touch /root/reboot_check")

                if mgmt == True:
                    ret = self.nic_con.enable_mnic(int(slot), first_pwr_on, session_uart)
                    print("Sleep 10 sec for link to be up")
                    time.sleep(10)
                    self.nic_con.uart_session_cmd(session_uart, "pdsctl show port status")
                    ret = self.nic_con.get_mgmt_rdy(int(slot), first_pwr_on, True, asic_type, uefi, dis_net_port, session_bash, session_uart)

                self.nic_con.uart_session_stop(session_uart)
                common.session_stop(session_uart)
                common.session_stop(session_bash)

            except pexpect.TIMEOUT:
                print("=== TIMEOUT: Failed to set up env single slot {} ===".format(slot))
                ret = -1

            if ret == 0:
                break

        if ret != 0:
            print("=== Setup env single slot failed! failed slot:", slot)
        else:
            print("=== Setup env single slot done #", retry, "===")
        print("timestamp", datetime.datetime.now().time())
        return ret

    def setup_multi(self, args):
        print(args)

        slot_list = args.slot_list.split(',')
        [ret, pass_list, fail_list] = self.nic_test.setup_env_multi_top(nic_list=slot_list, timeout=0, mgmt=args.mgmt, first_pwr_on=args.first_pwr_on, pwr_cycle=not args.no_pwr_cycle, asic_type=args.asic_type, uefi=args.uefi, dis_net_port=args.dis_net_port, env=args.skip_env)

    def setup_multi_w_console(self, args):
        print(args)
    
        if args.slot_list == "":
            print ("Invalide input slot_list:", slot_list)
    
        slot_list = args.slot_list.split(',')

        for ite in range(args.iteration):
            print("=== Ite:", ite, "===")
            for slot1 in slot_list:
                slot = int(slot1)

                #self.nic_con.switch_console(slot)
                #session = common.session_start()
                #cmd = self.nic_con.get_connect_cmd(slot)
                #session.sendline(cmd)

                session = common.session_start()

                print("=== Slot:", slot, "===")
                self.nic_con.power_cycle_multi(slot, wtime=0, swm_lp=False)

                ret = self.nic_con.uart_session_start_login(session, slot)
                if ret != 0:
                    self.nic_con.uart_session_stop(session)
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
                    self.nic_con.uart_session_stop(session)
                    return False

                #self.nic_con.uart_session_stop(session)
                common.session_stop(session)
                print("=== Slot:", slot, "Passed ===")

    def qspi_prog_salina(self, slot, qspi_image_path):
        session = common.session_start()
        if not qspi_image_path:
            print("===== FAILED: Please provide a qspi image path")
            return -1
        if not os.path.exists(os.path.join(qspi_image_path, "qspi_prog.sh")):
            print("===== FAILED: Unable to locate qspi_prog.sh in {} directory".format(qspi_image_path))
            return -1
        self.nic_con.power_cycle_multi(str(slot), wtime=1, proto_mode_dis=0)
        cur_dir = os.getcwd()
        common.session_cmd(session, "cd {}".format(qspi_image_path))
        common.session_cmd(session, "./qspi_prog.sh {}".format(slot))
        common.session_cmd(session, "cd {}".format(cur_dir))
        common.session_stop(session)
        return 0

    def qspi_test_pollara(self, slot):
        ret = 0

        uart_session = common.session_start()
        if sal_con.enter_a35_zephyr(slot, uart_session):
            print("===== FAILED: slot {} couldn't boot zephyr".format(slot))
            ret = -1

        if self.nic_con.uart_session_connect(uart_session, slot, uart_id=0):
            print("===== FAILED: couldn't open uart")
            ret = -1
        if self.nic_con.uart_session_cmd(uart_session, "", ending="- T R", timeout=1):
            print("===== FAILED: no pcie messages - wrong image")
            ret = -1
        else:
            print("================\nFinal Zephyr UART checking has passed\n================")

        self.nic_con.uart_session_stop(uart_session)
        common.session_stop(uart_session)
        return ret

    def prog_dpu_fru(self, args):
        import fru
        ret = 0
        slot=args.slot
    
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            return -1

        self.nic_con.power_cycle_multi(str(slot), wtime=1, proto_mode_dis=0)

        # Now boot zephyr and program dpu fru
        print("====== PROGRAMMING DPU FRU")
        if fru.program_dpu_fru(slot):
            print("====== ERRORS encountered programming DPU FRU")
            ret = -1

        # Now check from uboot
        print("====== VERIFYING PROGRAMMED DPU FRU")
        if fru.verify_dpu_fru(slot):
            print("====== ERRORS encountered verifying DPU FRU")
            ret = -1

        # Program 2nd PCIE fru as well
        if self.nic_con.get_card_type(slot) != "MALFA":
            if args.skip_fru2 == True:
                print("VERIFYING 2nd PCIE FRU - Skipped")
            else:
                print("====== PROGRAMMING 2nd PCIE FRU")
                if fru.program_2nd_pcie_fru(slot):
                    print("====== ERRORS encountered programming 2nd PCIE FRU")
                    ret = -1
                print("====== VERIFYING PROGRAMMED 2nd PCIE FRU")
                if fru.verify_2nd_pcie_fru(slot):
                    print("====== ERRORS encountered verifying 2nd PCIE FRU")
                    ret = -1

        if ret == 0:
            print("DPU_FRU updated successfully")
        else:
            print("DPU_FRU update unsuccessful")

        return ret

    def verify_dpu_fru(self, args):
        import fru
        ret = 0
        slot=args.slot

        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            return -1

        self.nic_con.power_cycle_multi(str(slot), wtime=1, proto_mode_dis=0)

        print("====== VERIFYING PROGRAMMED DPU FRU")
        if fru.verify_dpu_fru(slot):
            print("====== ERRORS encountered verifying DPU FRU")
            ret = -1

        if self.nic_con.get_card_type(slot) != "MALFA":
            if args.skip_fru2 == True:
                print("PROGRAMMING 2nd PCIE FRU - Skipped")
            else:
                print("====== VERIFYING PROGRAMMED 2nd PCIE FRU")
                if fru.verify_2nd_pcie_fru(slot):
                    print("====== ERRORS encountered verifying 2nd PCIE FRU")
                    ret = -1

        if ret == 0:
            print("DPU_FRU checked and verified")
        else:
            print("DPU_FRU failed verification")

        return ret

    def mask_vrm_smbalert(self, args):
        import vrm
        ret = 0
        slot=args.slot
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            return -1
        if (slot):
            if vrm.mask_smbalert(slot) != 0:
                print("====== ERRORS encountered during fix_sal_vrm")
                ret = -1
        if ret == 0:
            print("VRM mask applied successfully")
        else:
            print("VRM mask unsuccessful")
        return ret
   
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

            ret = self.nic_con.uart_session_start(session, slot)
            if ret != 0:
                self.nic_con.uart_session_stop(session)
                common.session_stop(session)
                continue

            if args.send_only:
                session.sendline(args.nic_cmd)
                time.sleep(3)
            else:
                ret = self.nic_con.uart_session_cmd(session, args.nic_cmd, args.timeout)

            self.nic_con.uart_session_stop(session)
            common.session_stop(session)

    def en_dis_esec_wp_single(self, args):
        print(args)
        enable = True
        slot = args.slot

        if args.en_dis == "enable":
            enable = True
        else:
            enable = False

        try:
            session_bash = common.session_start()
            session_bash.timeout = 30

            # Start console first to get all output
            session_uart = common.session_start()
            session_uart.timeout = 60

            ret = self.nic_con.uart_session_connect(session_uart, slot)
            if ret != 0:
                self.nic_con.uart_session_stop(session_uart)
                common.session_stop(session_uart)
                return ret

            # Power cycle NIC
            cmd = "turn_on_slot.sh off {}".format(slot)
            common.session_cmd(session_bash, cmd, 60)
            time.sleep(1)
            cmd = "turn_on_slot.sh on {}".format(slot)
            common.session_cmd(session_bash, cmd, 60)
            common.session_stop(session_bash)

            ret = self.nic_con.uart_session_wait_for_login(session_uart)
            if ret != 0:
                self.nic_con.uart_session_stop(session_uart)
                common.session_stop(session_uart)
                return ret

            ret = self.nic_con.uart_session_enter_uboot_sysreset(session_uart)
            if ret != 0:
                self.nic_con.uart_session_stop(session_uart)
                common.session_stop(session_uart)
                return ret

            #========================================
            # Enable/Disable ESEC QSPI WP
            # deassert CPLD WP# to make sure SR is not in locked state
            ret = self.nic_con.config_cpld_qspi_wp(session_uart, False)
            if ret != 0:
                self.nic_con.uart_session_stop(session_uart)
                common.session_stop(session_uart)
                return ret

            # change hwprot setting
            ret = self.nic_con.config_esec_qspi_wp(session_uart, enable)
            if ret != 0:
                self.nic_con.uart_session_stop(session_uart)
                common.session_stop(session_uart)
                return ret

            # put CPLD WP# to the requested state
            ret = self.nic_con.config_cpld_qspi_wp(session_uart, enable)
            if ret != 0:
                self.nic_con.uart_session_stop(session_uart)
                common.session_stop(session_uart)
                return ret

            # read/verify hwprot setting
            ret = self.nic_con.check_esec_qspi_wp(session_uart, enable)
            if ret != 0:
                self.nic_con.uart_session_stop(session_uart)
                common.session_stop(session_uart)
                return ret

        except pexpect.TIMEOUT:
            ret = -1

        self.nic_con.uart_session_stop(session_uart)
        common.session_stop(session_uart)

        return ret

    def sal_misc_eqbk_ctrl(self, args):
        ret = 0
        session = common.session_start()

        if sal_con.enter_a35_uboot(int(args.slot), session, warm_reset=False):
            print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
            ret = -1
            return ret

        #ret = self.nic_con.uart_session_start(session, args.slot)
        ret = self.nic_con.uart_session_connect(session, args.slot, uart_id=0)
        if ret != 0:
            return ret
        try:
            if args.enable == True:
                self.nic_con.uart_session_cmd(session, "setenv pcieawd_eqbk_en 1")
            else:
                self.nic_con.uart_session_cmd(session, "setenv delete pcieawd_eqbk_en")
            self.nic_con.uart_session_cmd(session, "saveenv")
        except pexpect.TIMEOUT:
            print ("Failed to set eqbk")
            ret = -1

        self.nic_con.uart_session_stop(session)
        common.session_stop(session)
        print("Done setting EQBK")

        return 0

    def sal_misc_a35_cmds(self, args):
        ret = 0
        session = common.session_start()

        #ret = self.nic_con.uart_session_start(session, args.slot)
        ret = self.nic_con.uart_session_connect(session, args.slot, uart_id=0)
        if ret != 0:
            return ret

        session.send(chr(3))
        session.expect("uart:~\$")
        try:
            cmd_list = args.all_cmds.split("#")
            for cmd in cmd_list:
                self.nic_con.uart_session_cmd(session, cmd, ending="uart:~\$")

        except pexpect.TIMEOUT:
            print ("Failed to run A35 commands")
            ret = -1

        self.nic_con.uart_session_stop(session)
        common.session_stop(session)
        return 0

    def sal_misc_pcieawd_env_ctrl(self, args):
        ret = 0
        session = common.session_start()

        if sal_con.enter_a35_uboot(int(args.slot), session, warm_reset=False):
            print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
            ret = -1
            return ret

        #ret = self.nic_con.uart_session_start(session, args.slot)
        ret = self.nic_con.uart_session_connect(session, args.slot, uart_id=0)
        if ret != 0:
            return ret
        try:
            if args.erase:
                self.nic_con.uart_session_cmd(session, "env erase")
            else:
                if args.eqbk_en is not None:
                    self.nic_con.uart_session_cmd(session, "setenv pcieawd_eqbk_en {}".format(args.eqbk_en))
                if args.cmn_kp is not None:
                    self.nic_con.uart_session_cmd(session, "setenv pcieawd_cmn_kp {}".format(args.cmn_kp))
                if args.cmn_ki is not None:
                    self.nic_con.uart_session_cmd(session, "setenv pcieawd_cmn_ki {}".format(args.cmn_ki))
                if args.tx_prop_adj is not None:
                    self.nic_con.uart_session_cmd(session, "setenv pcieawd_tx_prop_adj {}".format(args.tx_prop_adj))
                if args.rx_prop_adj is not None:
                    self.nic_con.uart_session_cmd(session, "setenv pcieawd_rx_prop_adj {}".format(args.rx_prop_adj))
                if args.tx_mag is not None:
                    self.nic_con.uart_session_cmd(session, "setenv pcieawd_tx_change_mag {}".format(args.tx_mag))
                if args.rx_mag is not None:
                    self.nic_con.uart_session_cmd(session, "setenv pcieawd_rx_change_mag {}".format(args.rx_mag))
                if args.rx_rate_nt is not None:
                    self.nic_con.uart_session_cmd(session, "setenv pcieawd_rx_rate_nt {}".format(args.rx_rate_nt))
                if args.txfirgen5 is not None:
                    self.nic_con.uart_session_cmd(session, "setenv pcieawd_txfirgen5 {}".format(args.txfirgen5))
                if args.all_params is not None:
                    self.nic_con.uart_session_cmd(session, "env erase")
                    param_list = args.all_params.split("#")
                    for param in param_list:
                        name = param.split(":")[0]
                        value = param.split(":")[1]
                        self.nic_con.uart_session_cmd(session, "setenv {} {}".format(name, value))

                self.nic_con.uart_session_cmd(session, "saveenv")
                self.nic_con.uart_session_cmd(session, "env print")
        except pexpect.TIMEOUT:
            print ("Failed to set pcieawd env")
            ret = -1

        self.nic_con.uart_session_stop(session)
        common.session_stop(session)
        print("Done setting pcieawd env")

        session = common.session_start()
        if sal_con.enter_a35_zephyr(int(args.slot), session, warm_reset=False):
            print("===== FAILED: slot {} couldn't boot zephyr".format(args.slot))
            ret = -1
        nc = nic_con()
        nc.uart_session_connect(session, args.slot, uart_id=0)
        nc.uart_session_cmd(session, "pcieawd showparams", ending="uart:~\$")
        nc.uart_session_stop(session)
        return 0

    def google_stress_test(self, args):
        ret = 0
        card_type = self.nic_con.get_card_type(args.slot)
        if card_type == "POLLARA" or card_type == "LINGUA":
            print("===== FAILED: This test not applicable to Pollara or Lingua")
            return -1

        session = common.session_start()
        if sal_con.enter_a35_uboot(int(args.slot), session, warm_reset=False):
            print("===== FAILED: slot {} couldn't boot Zephyr".format(args.slot))
            return -1
        # set vmarg before booting N1, otherwise the card reboots with reason "DPU internal reset GPIO8"
        print("Start Vmarge")
        print("tcl_path:", args.tcl_path)
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
        cmd = "fpgautil spimode {} off".format(args.slot)
        common.session_cmd(session, cmd)
        cmd = "jtag_accpcie_salina clr {}".format(args.slot)
        common.session_cmd(session, cmd)
        print("\nDisable WDT since vmarg will occupy i2c bus")
        cmd = "i2cset -y {} 0x4A 0x1 0x0".format(int(args.slot) + 2)
        common.session_cmd(session, cmd)
        cmd = "tclsh ~/diag/scripts/asic/leni_vmarg.tcl {} {} {}".format(args.slot, card_type, args.vmarg)
        common.session_cmd(session, cmd, 360, False, "vmarg set")

        if sal_con.enter_n1_linux(int(args.slot), session, new_memory_layout=args.new_memory_layout, warm_reset=True):
            print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
            return -1

        print("Start test on N1")
        uart_session = common.session_start()
        ret = self.nic_con.uart_session_start(uart_session, args.slot)
        if ret != 0:
            return ret
        # # clear interrupts before test
        # for i in range(10):
        #     self.nic_con.uart_session_cmd(uart_session, "pdsctl clear interrupts", 1)
        #     if "Interrupts cleared" in uart_session.before:
        #         ret = 0
        #         break
        #     else:
        #         ret = -1
        #         time.sleep(1)
        # if ret != 0:
        #     return ret
        # time.sleep(10)
        # # ECC check before test
        # if self.nic_con.uart_session_cmd(uart_session, "pdsctl show interrupts | grep -i mcc") != 0:
        #     ret = -1
        # if 'int_mcc_ecc' in uart_session.before or 'int_mcc_controller' in uart_session.before:
        #     print("===== FAILED: New interrupts before stress test")
        #     ret = -1
        self.nic_con.uart_session_cmd(uart_session, "mem=$(cat /proc/meminfo | grep MemFree | awk \'{print $2}\');mem=$(expr $mem / 100000);mem=$(expr $mem \* 80);echo $mem")
        cmd = "stressapptest_arm -M $mem -m {} -s {}".format(args.threads, args.dura)
        cmd_timeout = 60 + args.dura # buffer of a minute for any error dumps
        pass_sig = "Status: PASS"
        cmdret, output = self.nic_con.uart_session_cmd_w_ot(uart_session, cmd, cmd_timeout)
        if cmdret != 0:
            print("Command {} failed".format(cmd))
            ret = -1
        if pass_sig not in output:
            print("===== FAILED: missing passing signature")
            ret = -1
            time.sleep(3)
        # # ECC check after test
        # if self.nic_con.uart_session_cmd(uart_session, "pdsctl show interrupts | grep -i mcc") != 0:
        #     ret = -1
        # if 'int_mcc_ecc' in uart_session.before or 'int_mcc_controller' in uart_session.before:
        #     print("===== FAILED: Failed ECC check")
        #     ret = -1

        self.nic_con.uart_session_stop(uart_session)
        common.session_stop(uart_session)

        if ret != 0:
            cmd = "tclsh ~/diag/scripts/asic/get_nic_sts.tcl x {} 1".format(args.slot)
            common.session_cmd(session, cmd, 360, False, "Getting ASIC status - Done")
        else:
            # check ECC from tcl too
            cmd = "tclsh ~/diag/scripts/asic/get_nic_sts.tcl x {} 0 1".format(args.slot)
            common.session_cmd(session, cmd, 360, False, "Getting ASIC ECC status - Done")
            match = re.search(r'ECC happened', session.before)
            if match:
                print("ECC check FAILED for GOOGLE STRESS TEST")
                ret = -1

        common.session_cmd(session, "inventory -sts -slot {}".format(args.slot))
        common.session_stop(session)
        # check uart console
        if ret == 0:
            uart_session = common.session_start()
            self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=1)
            if 0 != sal_con.exp_cmd(uart_session, "", pass_sig_list=["\#"], timeout=5)[0]:
                print("===== FAILED: slot {} N1 console is not responsive".format(args.slot))
                return -1
            self.nic_con.uart_session_stop(uart_session)
            common.session_stop(uart_session)
            print("GOOGLE STRESS TEST PASSED")
        return ret

    def sal_edma_test(self, args):
        ret = 0
        card_type = self.nic_con.get_card_type(args.slot)
        if card_type == "POLLARA" or card_type == "LINGUA":
            print("===== FAILED: This test not applicable to Pollara or Lingua")
            return -1

        session = common.session_start()
        if sal_con.enter_a35_uboot(int(args.slot), session, warm_reset=False):
            print("===== FAILED: slot {} couldn't boot Zephyr".format(args.slot))
            return -1
        # set vmarg before booting N1, otherwise the card reboots with reason "DPU internal reset GPIO8"
        print("Start Vmarge")
        print("tcl_path:", args.tcl_path)
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
        cmd = "fpgautil spimode {} off".format(args.slot)
        common.session_cmd(session, cmd)
        cmd = "jtag_accpcie_salina clr {}".format(args.slot)
        common.session_cmd(session, cmd)
        print("\nDisable WDT since vmarg will occupy i2c bus")
        cmd = "i2cset -y {} 0x4A 0x1 0x0".format(int(args.slot) + 2)
        common.session_cmd(session, cmd)
        cmd = "tclsh ~/diag/scripts/asic/leni_vmarg.tcl {} {} {}".format(args.slot, card_type, args.vmarg)
        common.session_cmd(session, cmd, 360, False, "vmarg set")

        if sal_con.enter_n1_linux(int(args.slot), session, new_memory_layout=args.new_memory_layout):
            print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
            return -1

        print("Start test on N1")
        uart_session = common.session_start()
        ret = self.nic_con.uart_session_start(uart_session, args.slot)
        if ret != 0:
            return ret

        # clear interrupts before test
        for i in range(10):
            self.nic_con.uart_session_cmd(uart_session, "pdsctl clear interrupts", 1)
            if "Interrupts cleared" in uart_session.before:
                ret = 0
                break
            else:
                ret = -1
                time.sleep(1)
        if ret != 0:
            return ret
        time.sleep(10)
        # ECC check before test
        if self.nic_con.uart_session_cmd(uart_session, "pdsctl show interrupts | grep -i mcc") != 0:
            ret = -1
        if 'int_mcc_ecc' in uart_session.before or 'int_mcc_controller' in uart_session.before:
            print("New interrupts before EDMA test")
            ret = -1
        else:
            cmd = "eth_dbgtool ddr_stress 65 100 0 0 0 0 3 100 wrcnt 500 1 3 &"
            if self.nic_con.uart_session_cmd(uart_session, cmd, timeout=30, ending="wr_dst_sz ") != 0:
                ret = -1
            start_time = time.time()
            while True:
                if time.time() - start_time > args.dura:
                    break
                if self.nic_con.uart_session_cmd(uart_session, "pdsctl show interrupts | grep -i mcc") != 0:
                    ret = -1
                if 'int_mcc_ecc' in uart_session.before or 'int_mcc_controller' in uart_session.before:
                    print("EDMA test FAILED ECC check")
                    ret = -1
                    break
                time.sleep(10)
            self.nic_con.uart_session_cmd(uart_session, "killall eth_dbgtool")
            self.nic_con.uart_session_cmd(uart_session, "\r")

        self.nic_con.uart_session_stop(uart_session)
        common.session_stop(uart_session)

        if ret != 0:
            cmd = "tclsh ~/diag/scripts/asic/get_nic_sts.tcl x {} 1".format(args.slot)
            common.session_cmd(session, cmd, 360, False, "Getting ASIC status - Done")
        else:
            # check ECC from tcl too
            cmd = "tclsh ~/diag/scripts/asic/get_nic_sts.tcl x {} 0 1".format(args.slot)
            common.session_cmd(session, cmd, 360, False, "Getting ASIC ECC status - Done")
            match = re.search(r'ECC happened', session.before)
            if match:
                print("ECC check FAILED for EDMA TEST")
                ret = -1
        common.session_cmd(session, "inventory -sts -slot {}".format(args.slot))
        common.session_stop(session)
        # check uart console
        if ret == 0:
            uart_session = common.session_start()
            self.nic_con.uart_session_connect(uart_session, args.slot, uart_id=1)
            if 0 != sal_con.exp_cmd(uart_session, "", pass_sig_list=["\#"], timeout=5)[0]:
                print("===== FAILED: slot {} N1 console is not responsive".format(args.slot))
                return -1
            self.nic_con.uart_session_stop(uart_session)
            common.session_stop(uart_session)
            print("EDMA test PASSED")
        return ret

    def read_qsfp_from_arm(self, args):
        ret = 0
        session = common.session_start()
        if sal_con.enter_a35_zephyr(int(args.slot), session, warm_reset=False):
            print("===== FAILED: slot {} couldn't boot Zephyr".format(args.slot))
            ret = -1
            return ret

        print("Start Vmarge")
        print("tcl_path:", args.tcl_path)
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
        cmd = "fpgautil spimode {} off".format(args.slot)
        common.session_cmd(session, cmd)
        cmd = "jtag_accpcie_salina clr {}".format(args.slot)
        common.session_cmd(session, cmd)
        print("\nDisable WDT since vmarg will occupy i2c bus")
        cmd = "i2cset -y {} 0x4A 0x1 0x0".format(int(args.slot) + 2)
        common.session_cmd(session, cmd)
        cmd = "tclsh ~/diag/scripts/asic/leni_vmarg.tcl {} x {}".format(args.slot, args.vmarg)
        common.session_cmd(session, cmd, 360, False, "vmarg set")

        print("Start test on Zephyr")
        card_type = self.nic_con.get_card_type(args.slot)
        if card_type == "POLLARA" or card_type == "LINGUA":
            ports = ("0")
        else:
            ports = ("0", "1")

        for port in ports:
            cmd = "i2cset -y {} 0x4A 0x2 0x3c".format(int(args.slot) + 2)
            common.session_cmd(session, cmd)
            cmd = "i2cget -y {} 0x4a 0x2".format(int(args.slot) + 2)
            cmdret, output = common.session_cmd_w_ot(session, cmd)
            uart_session = common.session_start()
            ret = self.nic_con.uart_session_start(uart_session, args.slot, uart_id=0)
            if ret != 0:
                print("=== FAILED to connect")
                return ret
            for eeprom_address in (
                "0x80",
                "0x90",
                "0xa0",
                "0xb0",
                "0xc0",
                "0xd0",
                "0xe0",
                "0xf0"):
                cmd = "i2c read cpld-i2c@{} 0x50 {}".format(port, eeprom_address)
                cmdret, output = self.nic_con.uart_session_cmd_w_ot(uart_session, cmd, ending="uart:~\$")
                if "Failed to read" in output:
                    print("=== Command {} failed".format(cmd))
                    ret = -1
        self.nic_con.uart_session_stop(uart_session)
        common.session_stop(uart_session)
        common.session_stop(session)

        if ret == 0:
            print("QSFP READ TEST PASSED")
        else:
            print("QSFP READ TEST FAILED")
        return ret

    def sal_pc_test(self, args):
        print(args)
        ret = 0
    
        for ite in range(args.iteration):
            print("=== Ite:", ite, "===")
    
            uart_session = common.session_start()
            if sal_con.enter_a35_zephyr(args.slot, uart_session, warm_reset=args.warm, v12_reset=args.v12, awd_showparms=False):
                print("===== FAILED: slot {} couldn't boot zephyr".format(slot))
                ret = -1
                break

        return ret

    def sal_emmc_test(self, args):
        ret = 0
        card_type = self.nic_con.get_card_type(args.slot)
        if card_type == "POLLARA" or card_type == "LINGUA":
            print("===== FAILED: This test is not applicable to Pollara or Lingua")
            return -1

        for ite in range(args.iteration):
            print("=== Ite:", ite, "===")
            session = common.session_start()
            if sal_con.enter_n1_linux(int(args.slot), session, warm_reset=False, new_memory_layout=args.new_memory_layout):
                print("===== FAILED: slot {} couldn't boot Linux".format(args.slot))
                ret = -1
                return ret

            uart_session = common.session_start()
            uart_session.timeout = 60
            ret = self.nic_con.uart_session_start(uart_session, args.slot)
            if ret != 0:
                return ret

            print("Start test on N1")

            self.nic_con.uart_session_cmd(uart_session, "fdisk -l", 10)
            if not 'Data Filesystem' in uart_session.before:
                print("Failed EMMC TEST:  EMMC is not formated.  Do not see Partition 10 -> Data Filesystem")
                return False

            self.nic_con.uart_session_cmd(uart_session, "cat /sys/kernel/debug/mmc0/ios", 12)
            if not 'mmc HS200' in uart_session.before:
                print("EMMC Test Failed.  Expecting EMMC to be in HS200 mode")
                return False
            
            self.nic_con.uart_session_cmd(uart_session, "mount /dev/mmcblk0p10 /data;cd /data;pwd", 12)
            self.nic_con.uart_session_cmd(uart_session, "mem=$(cat /proc/meminfo | grep MemFree | awk \'{print $2}\');mem=$(expr $mem / 100000);mem=$(expr $mem \* 80);echo $mem")
            cmd = "/data/nic_util/stressapptest_arm -M $mem -s {} -m 8 -f file.1 -f file.2".format(args.dura)
            cmd_timeout = 60 + args.dura
            pass_sig = "Status: PASS"
            cmdret, output = self.nic_con.uart_session_cmd_w_ot(uart_session, cmd, cmd_timeout)
            if cmdret != 0:
                print("Command {} failed".format(cmd))
                return False
            if pass_sig not in output:
                print("===== FAILED: stressapptest_arm")
                return False


            self.nic_con.uart_session_cmd(uart_session, "dmesg | grep -i \"SDHCI REGISTER DUMP\" > test.txt;", 12)
            self.nic_con.uart_session_cmd(uart_session, "cat test.txt", 12)
            if 'REGISTER' in uart_session.before:
                print("EMMC Test Failed with demsg I/O Error!!")
                return False
            self.nic_con.uart_session_cmd(uart_session, "dmesg | grep -i \"O error\" > test.txt;", 12)
            self.nic_con.uart_session_cmd(uart_session, "cat test.txt", 12)
            if 'error' in uart_session.before:
                print("EMMC Test Failed with demsg I/O Error!!")
                return False
            self.nic_con.uart_session_cmd(uart_session, "dmesg | grep -i mmc | grep -i error > test.txt", 12)
            self.nic_con.uart_session_cmd(uart_session, "cat test.txt", 12)
            if 'error' in uart_session.before:
                print("EMMC Test Failed with demsg MMC Error!!")
                return False
            print("Test Ite:", ite, " PASSED")
            self.nic_con.uart_session_stop(uart_session)
            common.session_stop(uart_session)

    def sal_pc_test_j2c(self, args):
        ret = 0
        card_type = self.nic_con.get_card_type(args.slot)


        for ite in range(args.iteration):
            print("=== Ite:", ite, "===")

            session = common.session_start()
            common.session_cmd(session, "mbist_power_on.sh "+str(args.slot), timeout=90)

            print("tcl_path:", args.tcl_path)
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
            cmd = "fpgautil spimode {} off".format(args.slot)
            common.session_cmd(session, cmd)
            cmd = "jtag_accpcie_salina clr {}".format(args.slot)
            common.session_cmd(session, cmd)

            use_j2c = 1         if args.j2c             else 0
            use_gpio3 = 1       if args.gpio3           else 0
            use_pwr_ok_rst = 1  if args.pwr_ok_rst      else 0
            stop_on_error = 1   if args.stop_on_error   else 0

            cmd = "tclsh ~/diag/scripts/asic/sal_check_j2c.tcl -slot {} -ite {} -use_j2c {} -use_gpio3 {} -use_pwr_ok_rst {} -stop_on_error {}".format(args.slot, args.tcl_ite, use_j2c, use_gpio3, use_pwr_ok_rst, stop_on_error)
            timeout = 120+6*args.tcl_ite
            ret = common.session_cmd_pass(session, cmd, pass_sign="PC_TEST_J2C PASSED", timeout=timeout)

            common.session_cmd(session, "inventory -sts -slot {}".format(args.slot))
            common.session_cmd(session, "i2cdump -y {} 0x4a".format(args.slot+2))
            common.session_cmd(session, "i2cset -y {} 0x4a 0x1 0".format(args.slot+2))

            if ret != 0:
                print("PC_TEST_J2C has failed!", ite, ret)
                if args.stop_on_error:
                    print("Stoping scripti")
                    break
            else:
                print("PC_TEST_J2C has passed!", ite)

            common.session_stop(session)
        return ret

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
    parser_pc_test.add_argument("-fast", "--fast", help="Fast test", action='store_true')
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

    # NIC snake test for single slot
    parser_nic_snake_single = subparsers.add_parser('nic_snake_single', help='NIC snake test for single slot', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_nic_snake_single.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_nic_snake_single.add_argument("-ite", "--ite", help="Number of iteration", type=int, default=1)
    parser_nic_snake_single.add_argument("-mode", "--mode", help="snake mode", type=str, default="hod")
    parser_nic_snake_single.add_argument("-timeout", "--timeout", help="nic session cmd time out seconds", type=int, default=600)
    parser_nic_snake_single.add_argument("-dura", "--dura", help="test duration in seconds", type=int, default=3)
    parser_nic_snake_single.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=str, default='normal')
    parser_nic_snake_single.add_argument("-verbose", "--verbose", help="verbose level", action='store_true')
    parser_nic_snake_single.add_argument("-int_lpbk", "--int_lpbk", help="internal loopback", action='store_true')
    parser_nic_snake_single.add_argument("-snake_num", "--snake_num", help="snake test number (4: EDMA+regular; 6: regular)", type=int, default=6)

    parser_nic_snake_single.set_defaults(func=test.nic_snake_single)

    # NIC snake test in parallel
    parser_nic_snake_parallel = subparsers.add_parser('nic_snake_parallel', help='NIC snake test in parallel', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_nic_snake_parallel.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_nic_snake_parallel.add_argument("-ite", "--ite", help="Number of iteration", type=int, default=1)
    parser_nic_snake_parallel.add_argument("-mode", "--mode", help="snake mode", type=str, default="hod")
    parser_nic_snake_parallel.add_argument("-timeout", "--timeout", help="nic session cmd time out seconds", type=int, default=300)
    parser_nic_snake_parallel.add_argument("-dura", "--dura", help="test duration in seconds", type=int, default=3)
    parser_nic_snake_parallel.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=str, default='normal')
    parser_nic_snake_parallel.add_argument("-verbose", "--verbose", help="verbose level", action='store_true')
    parser_nic_snake_parallel.add_argument("-int_lpbk", "--int_lpbk", help="internal loopback", action='store_true')
    parser_nic_snake_parallel.add_argument("-snake_num", "--snake_num", help="snake test number (4: EDMA+regular; 6: regular)", type=int, default=6)

    parser_nic_snake_parallel.set_defaults(func=test.nic_snake_parallel)

    # NIC pcie prbs test for single slot
    parser_nic_pcic_prbs_single = subparsers.add_parser('nic_pcie_prbs_single', help='NIC PCIE prbs test for single slot', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_nic_pcic_prbs_single.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_nic_pcic_prbs_single.add_argument("-timeout", "--timeout", help="nic session cmd time out seconds", type=int, default=300)
    parser_nic_pcic_prbs_single.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=str, default='normal')
    parser_nic_pcic_prbs_single.add_argument("-lpbk", "--lpbk", help="Loop Back Level", type=int, default=0)
    parser_nic_pcic_prbs_single.add_argument("-dura", "--dura", help="Duration", type=int, default=60)
    parser_nic_pcic_prbs_single.add_argument("-poly", "--poly", help="Polynomial", type=str, default="PRBS31")
    parser_nic_pcic_prbs_single.add_argument("-mode", "--mode", help="PRBS Type", type=str, default="PCIE")

    parser_nic_pcic_prbs_single.set_defaults(func=test.nic_pcie_prbs_single)

    # NIC pcie prbs test in parallel
    parser_nic_pcic_prbs_parallel = subparsers.add_parser('nic_pcie_prbs_parallel', help='NIC PCIE prbs test in parallel', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_nic_pcic_prbs_parallel.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_nic_pcic_prbs_parallel.add_argument("-timeout", "--timeout", help="nic session cmd time out seconds", type=int, default=300)
    parser_nic_pcic_prbs_parallel.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=str, default='normal')
    parser_nic_pcic_prbs_parallel.add_argument("-lpbk", "--lpbk", help="Loop Back Level", type=int, default=0)
    parser_nic_pcic_prbs_parallel.add_argument("-dura", "--dura", help="Duration", type=int, default=60)
    parser_nic_pcic_prbs_parallel.add_argument("-poly", "--poly", help="Polynomial", type=str, default="PRBS31")
    parser_nic_pcic_prbs_parallel.add_argument("-mode", "--mode", help="PRBS Type", type=str, default="PCIE")

    parser_nic_pcic_prbs_parallel.set_defaults(func=test.nic_pcie_prbs_parallel)

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
    parser_setup_multi_w_console.add_argument("-ite", "--iteration", help="Number of iteration", type=int, default=1)

    parser_setup_multi_w_console.set_defaults(func=test.setup_multi_w_console)

    # setup multi
    parser_setup_multi = subparsers.add_parser('setup_multi', help='Set up multiple cards', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_setup_multi.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_setup_multi.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    parser_setup_multi.add_argument("-mgmt", "--mgmt", help="Set up management port", action='store_true')
    parser_setup_multi.add_argument("-no_pc", "--no_pwr_cycle", help="Power cycle", action='store_true')
    parser_setup_multi.add_argument("-asic_type", "--asic_type", help="ASIC type: capri/elba", type=str, default="elba")
    parser_setup_multi.add_argument("-uefi", "--uefi", help="UEFI mode", action='store_true')
    parser_setup_multi.add_argument("-dis_net_port", "--dis_net_port", help="Disable RJ45 Network port", action='store_true')
    parser_setup_multi.add_argument("-skip_env", "--skip_env", help="Set up env", action='store_false')
    parser_setup_multi.add_argument("-edma", "--edma", help="EDMA setup", action='store_true')

    parser_setup_multi.set_defaults(func=test.setup_multi)

    # setup env for single slot
    parser_setup_single = subparsers.add_parser('setup_single', help='Set up for single slot', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_setup_single.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_setup_single.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    parser_setup_single.add_argument("-mgmt", "--mgmt", help="Set up management port", action='store_true')
    parser_setup_single.add_argument("-no_pc", "--no_pwr_cycle", help="Power cycle", action='store_true')
    parser_setup_single.add_argument("-asic_type", "--asic_type", help="ASIC type: capri/elba", type=str, default="elba")
    parser_setup_single.add_argument("-uefi", "--uefi", help="UEFI mode", action='store_true')
    parser_setup_single.add_argument("-dis_net_port", "--dis_net_port", help="Disable RJ45 Network port", action='store_true')
    parser_setup_single.add_argument("-edma", "--edma", help="EDMA setup", action='store_true')

    parser_setup_single.set_defaults(func=test.setup_env_single)

    # setup env parallel
    parser_setup_parallel = subparsers.add_parser('setup_parallel', help='Set up multiple cards in parallel', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_setup_parallel.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_setup_parallel.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    parser_setup_parallel.add_argument("-mgmt", "--mgmt", help="Set up management port", action='store_true')
    parser_setup_parallel.add_argument("-no_pc", "--no_pwr_cycle", help="Power cycle", action='store_true')
    parser_setup_parallel.add_argument("-asic_type", "--asic_type", help="ASIC type: capri/elba", type=str, default="elba")
    parser_setup_parallel.add_argument("-uefi", "--uefi", help="UEFI mode", action='store_true')
    parser_setup_parallel.add_argument("-dis_net_port", "--dis_net_port", help="Disable RJ45 Network port", action='store_true')
    parser_setup_parallel.add_argument("-edma", "--edma", help="EDMA setup", action='store_true')

    parser_setup_parallel.set_defaults(func=test.setup_env_parallel)

    # Multi nic cmd
    parser_multi_nic_cmds = subparsers.add_parser('multi_nic_cmds', help='Run commands on each nic console', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_multi_nic_cmds.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser_multi_nic_cmds.add_argument("-nic_cmd", "--nic_cmd", help="nic command", type=str, default="")
    parser_multi_nic_cmds.add_argument("-timeout", "--timeout", help="timeout", type=int, default=30)
    parser_multi_nic_cmds.add_argument("-sd_only", "--send_only", help="Only send command and do not wait for it finish", action='store_true')

    parser_multi_nic_cmds.set_defaults(func=test.multi_nic_cmds)

    # Enable/Disable WP single
    parser_setup_single = subparsers.add_parser('en_dis_esec_wp_single', help='Set up for single slot', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_setup_single.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_setup_single.add_argument("-en_dis", "--en_dis", help="Enable/Disable", type=str, default="enable")

    parser_setup_single.set_defaults(func=test.en_dis_esec_wp_single)

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
    parser_nic_snake_mtp.add_argument("-ite", "--ite", help="Iteration of start and stop snake (Debug only)", type=int, default=1)
    parser_nic_snake_mtp.add_argument("-mtp_clk", "--mtp_clk", help="Whether to use MTP PCIe refclk; 0: Disable; 1: use MTP clk", type=int, default=0)
    parser_nic_snake_mtp.add_argument("-low_power_mode", "--lpmode", help="Turn off unused blocks (Pollara only)", type=int, default=0)
    parser_nic_snake_mtp.add_argument("-arm_freq", "--arm_freq", help="Change ARM frequency (Pollara only)", type=str, default="default")
    parser_nic_snake_mtp.add_argument("-v12_reset", '--v12_reset', action='store_true', help='Power cycle 12v')
    parser_nic_snake_mtp.add_argument("-new_memory_layout", "--new_memory_layout", "-nm", help="following new Leni memory layout after Jan 15", action='store_true', default=False)
    parser_nic_snake_mtp.set_defaults(func=test.nic_snake_mtp)

    # NIC PCIE PRBS test from mtp
    parser_nic_port_up = subparsers.add_parser('pcie_prbs', help='pcie_prbs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_nic_port_up.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_nic_port_up.add_argument("-tcl_path", "--tcl_path", help="TCL nic folder path", type=str, default='/home/diag/diag/asic/')
    parser_nic_port_up.add_argument("-card_type", "--card_type", help="Card type", type=str, default='LENI')
    parser_nic_port_up.add_argument("-vmarg", "--vmarg", help="vmarg", type=str, default='normal')
    parser_nic_port_up.add_argument("-dura", "--dura", help="Duration", type=str, default="30")
    parser_nic_port_up.add_argument("-mtp_clk", "--mtp_clk", help="Whether to use MTP PCIe refclk; 0: Disable; 1: use MTP clk", type=int, default=0)
    parser_nic_port_up.add_argument("-timeout", "--timeout", help="nic session cmd time out seconds", type=int, default=300)
    parser_nic_port_up.add_argument("-v12_reset", '--v12_reset', action='store_true', help='Power cycle 12v')
    parser_nic_port_up.set_defaults(func=test.pcie_prbs)

    # Program FRUs
    parser_prog_dpu_fru = subparsers.add_parser('prog_dpu_fru', help='Program Salina DPU FRU', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_prog_dpu_fru.add_argument("-slot", "--slot", help="NIC slot", type=int, default="")
    parser_prog_dpu_fru.add_argument("-skip_fru2", '--skip_fru2', action='store_true', help='Skip 2nd host FRU')
    parser_prog_dpu_fru.set_defaults(func=test.prog_dpu_fru)

    parser_verif_dpu_fru = subparsers.add_parser('verify_dpu_fru', help='Verify programmed Salina DPU FRU', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_verif_dpu_fru.add_argument("-slot", "--slot", help="NIC slot", type=int, default="")
    parser_verif_dpu_fru.add_argument("-skip_fru2", '--skip_fru2', action='store_true', help='Skip 2nd host FRU')
    parser_verif_dpu_fru.set_defaults(func=test.verify_dpu_fru)

    # Salina VRM fix
    parser_fix_sal_vrm = subparsers.add_parser('fix_sal_vrm', help='Program Salina VRM with alert masking', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_fix_sal_vrm.add_argument("-slot", "--slot", help="NIC slot", type=int, default="")
    parser_fix_sal_vrm.set_defaults(func=test.mask_vrm_smbalert)

    # Google stress test
    parser_mem_test = subparsers.add_parser('mem_test', help='Memory test using google stress test', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_mem_test.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_mem_test.add_argument("-tcl_path", "--tcl_path", help="TCL nic folder path", type=str, default='/home/diag/diag/asic/')
    parser_mem_test.add_argument("-vmarg", "--vmarg", help="vmarg", type=str, default='normal')
    parser_mem_test.add_argument("-dura", "--dura", help="number of seconds to run", type=int, default=60)
    parser_mem_test.add_argument("-threads", "--threads", help="number of memory copy threads to run", type=int, default=16)
    parser_mem_test.add_argument("-new_memory_layout", "--new_memory_layout", "-nm", help="following new Leni memory layout after Jan 15", action='store_true', default=False)
    parser_mem_test.set_defaults(func=test.google_stress_test)

    # EDMA test
    parser_edma_test = subparsers.add_parser('edma_test', help='EDMA test', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_edma_test.add_argument("-slot", "--slot", help="NIC slot", type=str, default="")
    parser_edma_test.add_argument("-tcl_path", "--tcl_path", help="TCL nic folder path", type=str, default='/home/diag/diag/asic/')
    parser_edma_test.add_argument("-vmarg", "--vmarg", help="vmarg", type=str, default='normal')
    parser_edma_test.add_argument("-dura", "--dura", help="number of seconds to run", type=int, default=60)
    parser_edma_test.add_argument("-new_memory_layout", "--new_memory_layout", "-nm", help="following new Leni memory layout after Jan 15", action='store_true', default=False)
    parser_edma_test.set_defaults(func=test.sal_edma_test)

    # SPI-to-CPLD test from ARM
    parser_spi_cpld_test = subparsers.add_parser('test_spi', help='Test SPI-to-CPLD from ARM on QSFP loopbacks', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_spi_cpld_test.add_argument("-slot", "--slot", help="NIC slot", type=int, default="")
    parser_spi_cpld_test.add_argument("-tcl_path", "--tcl_path", help="TCL nic folder path", type=str, default='/home/diag/diag/asic/')
    parser_spi_cpld_test.add_argument("-vmarg", "--vmarg", help="vmarg", type=str, default='normal')
    parser_spi_cpld_test.set_defaults(func=test.read_qsfp_from_arm)

    #=====================================================
    # Salina misc commands
    sal_misc_parser = subparsers.add_parser('salina', help='Salina misc commands', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    sal_misc_subp = sal_misc_parser.add_subparsers(title="Salina misc commands", dest="sal_misc_subp", description="Salina misc commands", help='Salina misc commands description')

    #---------------------------------------
    # Salina misc sub commands
    parser_eqbk = sal_misc_subp.add_parser('eqbk', help='EQBK Enable/Disalbe', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_eqbk.add_argument("-slot", "--slot", help="NIC slot", type=int, default="")
    group_eqbk = parser_eqbk.add_mutually_exclusive_group(required=True)
    group_eqbk.add_argument("-enable", '--enable', action='store_true', help='Enabled')
    group_eqbk.add_argument("-disable", '--disable', action='store_true', help='Disabled')
    parser_eqbk.set_defaults(func=test.sal_misc_eqbk_ctrl)

    parser_misc_a35_cmds = sal_misc_subp.add_parser('a35_cmds', help='A35 commands', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_misc_a35_cmds.add_argument("-slot", "--slot", help="NIC slot", type=int, default="")
    parser_misc_a35_cmds.add_argument("-all_cmds", '--all_cmds', help='all parameters in one; format: cmd1#cmd2', type=str, default=None)
    parser_misc_a35_cmds.set_defaults(func=test.sal_misc_a35_cmds)

    parser_pcieawd_env = sal_misc_subp.add_parser('pcieawd_env', help='pcieawd setenv', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_pcieawd_env.add_argument("-slot", "--slot", help="NIC slot", type=int, default="")
    parser_pcieawd_env.add_argument("-erase", '--erase', action='store_true', help='Erase env')
    parser_pcieawd_env.add_argument("-eqbk_en", '--eqbk_en', help='pcieawd_eqbk_en', type=str, default=None)
    parser_pcieawd_env.add_argument("-cmn_kp", '--cmn_kp', help='pcieawd_cmn_kp', type=str, default=None)
    parser_pcieawd_env.add_argument("-cmn_ki", '--cmn_ki', help='pcieawd_cmn_ki', type=str, default=None)
    parser_pcieawd_env.add_argument("-tx_prop_adj", '--tx_prop_adj', help='pcieawd_tx_prop_adj', type=str, default=None)
    parser_pcieawd_env.add_argument("-rx_prop_adj", '--rx_prop_adj', help='pcieawd_rx_prop_adj', type=str, default=None)
    parser_pcieawd_env.add_argument("-tx_mag", '--tx_mag', help='pcieawd_tx_change_mag', type=str, default=None)
    parser_pcieawd_env.add_argument("-rx_mag", '--rx_mag', help='pcieawd_rx_change_mag', type=str, default=None)
    parser_pcieawd_env.add_argument("-rx_rate_nt", '--rx_rate_nt', help='pcieawd_rx_rate_nt', type=str, default=None)
    parser_pcieawd_env.add_argument("-txfirgen5", '--txfirgen5', help='pcieawd_txfirgen5', type=str, default=None)
    parser_pcieawd_env.add_argument("-all_params", '--all_params', help='all parameters in one; format: param1:value1#param2:value2', type=str, default=None)
    parser_pcieawd_env.set_defaults(func=test.sal_misc_pcieawd_env_ctrl)

    # salina power cycle test
    parser_sal_pc = sal_misc_subp.add_parser('pc_test', help='Power cycle test', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_sal_pc.add_argument("-slot", "--slot", help="NIC slot", type=int, default=1)
    parser_sal_pc.add_argument("-ite", "--iteration", help="Number of iteration", type=int, default=1)
    group_sal_pc = parser_sal_pc.add_mutually_exclusive_group(required=False)
    group_sal_pc.add_argument("-v12", '--v12', action='store_true', help='12V power cycle')
    group_sal_pc.add_argument("-warm", '--warm', action='store_true', help='Warm reset')
    parser_sal_pc.set_defaults(func=test.sal_pc_test)

    # salina emmc test
    parser_sal_emmc = sal_misc_subp.add_parser('emmc_test', help='power cycle EMMC test', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_sal_emmc.add_argument("-slot", "--slot", help="NIC slot", type=int, default=1)
    parser_sal_emmc.add_argument("-dura", "--dura", help="number of seconds to run", type=int, default=60)
    parser_sal_emmc.add_argument("-ite", "--iteration", help="Number of iteration", type=int, default=1)
    group_sal_emmc = parser_sal_emmc.add_mutually_exclusive_group(required=False)
    group_sal_emmc.add_argument("-v12", '--v12', action='store_true', help='12V power cycle')
    group_sal_emmc.add_argument("-warm", '--warm', action='store_true', help='Warm reset')
    group_sal_emmc.add_argument("-new_memory_layout", "--new_memory_layout", "-nm", help="following new Leni memory layout after Jan 15", action='store_true', default=False)
    parser_sal_emmc.set_defaults(func=test.sal_emmc_test)

    # salina power cycle test
    parser_sal_pc_j2c = sal_misc_subp.add_parser('pc_test_j2c', help='Power cycle test, check with J2C', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_sal_pc_j2c.add_argument("-tcl_path", "--tcl_path", help="TCL nic folder path", type=str, default='/home/diag/diag/asic/')
    parser_sal_pc_j2c.add_argument("-slot", "--slot", help="NIC slot", type=int, default=1)
    parser_sal_pc_j2c.add_argument("-ite", "--iteration", help="Number of iteration", type=int, default=1)
    parser_sal_pc_j2c.add_argument("-tcl_ite", "--tcl_ite", help="Number of iteration in TCL file", type=int, default=10)
    parser_sal_pc_j2c.add_argument("-gpio3", '--gpio3', action='store_true', help='Use GPIO3 reset')
    parser_sal_pc_j2c.add_argument("-pwr_ok_rst", '--pwr_ok_rst', action='store_true', help='Toggle CPLD Power OK')
    parser_sal_pc_j2c.add_argument("-j2c", '--j2c', action='store_true', help='Use j2c to check; Otherwise use OW')
    parser_sal_pc_j2c.add_argument("-soe", '--stop_on_error', action='store_true', help='Stop the script on the first error')
    parser_sal_pc_j2c.set_defaults(func=test.sal_pc_test_j2c)

    # NIC PCIE PRBS test from mtp
    parser_sal_pcie_prbs = sal_misc_subp.add_parser('pcie_prbs', help='pcie_prbs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser_sal_pcie_prbs.add_argument("-slot",          "--slot",       help="NIC slot", type=str, default="")
    parser_sal_pcie_prbs.add_argument("-tcl_path",      "--tcl_path",   help="TCL nic folder path", type=str, default='/home/diag/diag/asic/')
    parser_sal_pcie_prbs.add_argument("-card_type",     "--card_type",  help="Card type", type=str, default='LENI')
    parser_sal_pcie_prbs.add_argument("-vmarg",         "--vmarg",      help="vmarg", type=str, default='normal')
    parser_sal_pcie_prbs.add_argument("-dura",          "--dura",       help="Duration", type=str, default="30")
    parser_sal_pcie_prbs.add_argument("-mtp_clk",       "--mtp_clk",    help="Whether to use MTP PCIe refclk; 0: Disable; 1: use MTP clk", type=int, default=0)
    parser_sal_pcie_prbs.add_argument("-aw_txfir_ow",   "--aw_txfir_ow", help="TX FIR overwrite", type=int, default=100)
    parser_sal_pcie_prbs.add_argument("-timeout",       "--timeout",    help="nic session cmd time out seconds", type=int, default=300)
    parser_sal_pcie_prbs.add_argument("-v12_reset",     '--v12_reset',  help='Power cycle 12v', action='store_true' )
    parser_sal_pcie_prbs.set_defaults(func=test.sal_pcie_prbs_v2)

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)
        #parser.exit(status=1, message=parser.print_help())

    sys.exit(args.func(args))

