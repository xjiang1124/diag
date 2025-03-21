#!/usr/bin/env python

import argparse
import pexpect
import os
import re
import sys
import time
import subprocess
import datetime
from time import sleep

sys.path.append("../lib")
import common

class nic_con:
    def __init__(self):
        self.usr = "root"
        self.pwd = "pen123"
        self.fmt_con_cmd = "con_connect.sh {}"
        self.fmt_change_rate = "stty speed {}"

    def get_connect_cmd(self, slot, *args, **kwargs):
        cmd = self.fmt_con_cmd.format(slot)
        if self.get_asic_type(slot) == "SALINA":
            uart_id = str(kwargs.get("uart_id", "1")) # override from function call, or default to N1
            cmd += " " + str(uart_id)
        return cmd

    def set_cpld_uart_bits(self, session, slot, *args, **kwargs):
        """
            Elba/Capri:
                0x35 = uart to MTP
            Salina:
                0x00 = a35 uart
                0x01 = n1 uart
        """
        if self.get_asic_type(slot) == "SALINA":
            uart_id = str(kwargs.get("uart_id", "0x01")) # override from function call, or default to N1
            cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x21 -data={}".format(slot, uart_id)
        else:
            cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x21 -data=0x35".format(slot)
        common.session_cmd(session, cmd)

    def uart_session_start_login(self, session, slot, timeout=15):
        ret = 0
        cmd = self.get_connect_cmd(slot)
        expstr = ["Login incorrect", "$\# ", "capri login:", "-gold login", "elba-haps login:", "salina-gold login:", "Press g to continue", "elba login:", "resetting ..."]
        session.sendline(cmd)
        if self.get_asic_type(slot) == "SALINA":
            timeout=30
        for ite in range(3):
            print("ite: ", ite)
            #timeout = 15

            try:
                #session.expect("Terminal ready")
                print("sending r")
                session.send("\r")

                i = session.expect(expstr, timeout)
                if i == 0:
                    # press another enter and wait for prompt again
                    continue
                elif i == 1:
                    # already logged in
                    pass
                elif i != len(expstr)-1:
                    session.sendline(self.usr)
                    session.expect("assword:")
                    session.sendline(self.pwd)
                    session.expect("\#")
                else:
                    return -1
                ret = 0
                break
            except pexpect.TIMEOUT:
                if ite != 0:
                    print("=== TIMEOUT: Can not connect to NIC on UART!")
                ret = -1
            #time.sleep(15)
        currentTime = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
        session.sendline("date -s " + currentTime)
        i = session.expect(["#", pexpect.TIMEOUT, pexpect.EOF], timeout)
        if i != 0:
            ret = -1
        session.sendline(r'PS1="[$(date +%Y-%m-%d_)\\t] \u# "')
        i = session.expect(["#", pexpect.TIMEOUT, pexpect.EOF], timeout) # expect the # in my send command
        i = session.expect(["#", pexpect.TIMEOUT, pexpect.EOF], timeout)
        if i != 0:
            ret = -1

        return ret

    def uart_session_start(self, session, slot, numRetry=10, uart_id=1):
        ret = 0
        cmd = self.get_connect_cmd(slot, uart_id=uart_id)
        expstr = ["capri login:", "-gold login", "elba-haps login:", "salina-gold login:", "Press g to continue", "elba login:", "\#", "uart:~\$"]
        session.sendline(cmd)
        for ite in range(numRetry):
            print("ite: ", ite)
            timeout = 1

            try:
                #session.expect("Terminal ready")
                print("sending r")
                session.send("\r")

                i = session.expect(expstr, timeout)
                if i != len(expstr)-1 and i != len(expstr)-2:
                    session.sendline(self.usr)
                    session.expect("assword:")
                    session.sendline(self.pwd)
                    session.expect("\#")
                ret = 0
                break
            except pexpect.TIMEOUT:
                if ite != 0:
                    print("=== TIMEOUT: Can not connect to NIC on UART!")
                ret = -1

        if uart_id == 1:
            # not applicable to non-salina & zephyr
            currentTime = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
            session.sendline("date -s " + currentTime)
            i = session.expect(["#", pexpect.TIMEOUT, pexpect.EOF], timeout)
            if i != 0:
                ret = -1
            session.sendline(r'PS1="[$(date +%Y-%m-%d_)\\t] \u# "')
            i = session.expect(["#", pexpect.TIMEOUT, pexpect.EOF], timeout) # expect the # in my send command
            i = session.expect(["#", pexpect.TIMEOUT, pexpect.EOF], timeout)
            if i != 0:
                ret = -1
        return ret

    def uart_session_start_slot(self, session, slot=0):
        ret = 0
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            return -1

        #cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        #common.session_cmd(session, cmd) 

        cmd = self.get_connect_cmd(slot)
        expstr = ["capri login:", "\#"]
        try:
            session.sendline(cmd)
            #session.expect("Terminal ready")
            session.send("\r")
            i = session.expect(expstr, 15)
            if i == 0:
                session.sendline(self.usr)
                session.expect("assword:")
                session.sendline(self.pwd)
                session.expect("\#")
        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Can not connect to NIC on UART!")
            return -1

        currentTime = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
        session.sendline("date -s " + currentTime)
        i = session.expect(["#", pexpect.TIMEOUT, pexpect.EOF], 15)
        if i != 0:
            return -1
        session.sendline(r'PS1="[$(date +%Y-%m-%d_)\\t] \u# "')
        i = session.expect(["#", pexpect.TIMEOUT, pexpect.EOF], 15) # expect the # in my send command
        i = session.expect(["#", pexpect.TIMEOUT, pexpect.EOF], 15)
        if i != 0:
            return -1
        return 0

    def uart_session_stop(self, session):
        session.timeout = 15
        try:
            session.sendcontrol('a')
            session.sendcontrol('x')
            session.expect("\$")
            return 0
        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Faled to stop UART session ===")
            return -1

    def uart_session_cmd_sig(self, session, cmd, timeout=30, ending="\#", sig=["PASS", "FAIL"], verbose=True):
        temp = session.timeout
        session.timeout = timeout
        ret = -1
        try:
            session.sendline(cmd)
            i = session.expect(sig)
            ret = i

        except:
            if verbose == True:
                print("=== TIMEOUT:", cmd, "===")
            try:
                session.send(chr(3))
                time.sleep(0.05)
                session.expect(ending)
            except:
                print("Failed to recover console!")
            ret = -1
        session.timeout = temp
        return ret

    def uart_session_cmd(self, session, cmd, timeout=30, ending="\#"):
        temp = session.timeout
        session.timeout = timeout
        ret = 0
        try:
            session.sendline(cmd)
            ret = session.expect(ending)
        except:
            print("=== TIMEOUT:", cmd, "===")
            session.send(chr(3))
            time.sleep(0.05)
            #session.expect(ending)
            ret = -1
        session.timeout = temp
        return ret

    def uart_session_cmd_w_ot(self, session, cmd, timeout=30, ending="\#"):
        temp = session.timeout
        session.timeout = timeout
        ret = 0
        try:
            session.sendline(cmd)
            session.expect(ending)
        except:
            print("=== TIMEOUT:", cmd, "===")
            session.send(chr(3))
            time.sleep(0.05)
            session.expect(ending)
            ret = -1
        session.timeout = temp
        return[ret, session.before]

    def uart_session_cmd_list(self, session, cmd_list=[], timeout=30, ending="\#"):
        for cmd in cmd_list:
            ret = self.uart_session_cmd(session, cmd, timeout, ending)
            if ret == -1:
                return ret
        return 0

    #================================================== 
    #
    # Function wait till NIC boots up to prompt,
    #   then log in with password
    # 1. Assume that session is on console already
    # 2. Assume card is just power cycled
    # 
    #================================================== 
    def uart_session_wait_for_login(self, session, timeout=15):
        expstr = ["capri login:", "-gold login", "elba-haps login:", "salina-gold login:", "Press g to continue", "elba login:", "resetting ..."]

        for ite in range(3):
            print("ite: ", ite)
            #timeout = 15

            try:
                #session.expect("Terminal ready")
                print("sending r")
                session.send("\r")

                i = session.expect(expstr, timeout)
                if i != len(expstr)-1:
                    session.sendline(self.usr)
                    session.expect("assword:")
                    session.sendline(self.pwd)
                    session.expect("\#")
                else:
                    return -1
                ret = 0
                break
            except pexpect.TIMEOUT:
                print("=== Card not ready in ite {} ===".format(ite))
                ret = -1

        if ret != 0:
            print("=== TIMEOUT: Can not connect to NIC on UART!")

        return ret

    #================================================== 
    #
    # Function uses "systeset" command to reboot, 
    #   then enter uboot with CTRL+c
    # 1. Assume that session is on console already
    # 2. Assume card has logged in already
    # 
    #================================================== 
    def uart_session_enter_uboot_sysreset(self, session):
        expstr = ["Capri# ", "DSC# "]
        ret = -1

        cmd = "sysreset.sh\r"
        session.sendline(cmd)
        time.sleep(1)
        for i in range(60):
            session.timeout = 1
            try:
                print("C+C", i)
                session.send(chr(3))
                session.expect(expstr)
                ret = 0
                break
            except pexpect.TIMEOUT:
                print("Retry:", i)
                ret = -1

        if ret == -1:
            print("=== Failed to enter uboot ===")

        # When sending to manay C+C, there are multiple pending DSC# prompt.
        # Following section is to clear the pending prompt to avoid mismatch
        for i in range(20):
            try:
                session.timeout = 1
                session.expect(expstr)
            except pexpect.TIMEOUT:
                print("No more expect")
                break

        return ret

    def uart_session_connect(self, session, slot, timeout=15, uart_id="1"):
        ret = 0
        cmd = self.get_connect_cmd(slot, uart_id=uart_id)
        expstr = "tx/rx buffer cleared"
        try:
            session.sendline(cmd)
            sleep(1) # needs delay otherwise fpga_uart will throw UART_ERROR2, and drop some characters from the next command
            session.expect(expstr, timeout)
        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Failed to connect console")
            ret = -1
        return ret

    def power_cycle_uart(self, slot=0):
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            sys.exit(0)

        numRetry = 3

        session = common.session_start()
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(1)

        for i in range(numRetry):
            cmd = "turn_on_slot.sh off {}".format(slot)
            common.session_cmd(session, cmd)
            cmd = "turn_on_slot.sh on {}".format(slot)
            common.session_cmd(session, cmd)

            # Wait for nic to boot
            time.sleep(90)

            print("=== Start Uart Session {} ===".format(i))
            ret = self.uart_session_start(session, slot)
            if ret == 0:
                break
            self.uart_session_stop(session)

        self.uart_session_stop(session)
        common.session_stop(session)
        return ret


    def power_cycle_multi(self, slot_list="", wtime=30, swm_lp=False, uart_id=0, proto_mode_dis=1):
        ret = 0
        session = common.session_start()

        cmd = "turn_on_slot.sh off {}".format(slot_list)
        common.session_cmd(session, cmd)
        time.sleep(3)
        cmd = "turn_on_slot.sh on {} {} {}".format(slot_list, uart_id, proto_mode_dis)
        if swm_lp == True:
            cmd = "".join((cmd, " 1"))
        common.session_cmd(session, cmd)

        # Wait for nic to boot
        print("Wait", wtime, "after power cycle")
        time.sleep(wtime)

        common.session_stop(session)
        return ret

    def power_cycle_multi_via_3v3(self, slot_list="", wtime=30, swm_lp=False):
        ret = 0
        session = common.session_start()

        cmd = "turn_on_slot.sh off {}".format(slot_list)
        common.session_cmd(session, cmd)
        time.sleep(1)
        cmd = "turn_on_slot_3v3.sh on {}".format(slot_list)
        common.session_cmd(session, cmd)

        cmd = "turn_on_slot.sh on {}".format(slot_list)
        if swm_lp == True:
            cmd = "".join((cmd, " 1"))
        common.session_cmd(session, cmd)

        # Wait for nic to boot
        print("Wait", wtime, "after power cycle")
        time.sleep(wtime)

        common.session_stop(session)
        return ret

    def power_cycle_12v_multi(self, slot_list="", wtime=30, swm_lp=False):
        ret = 0
        session = common.session_start()

        cmd = "turn_on_slot_12v.sh off {}".format(slot_list)
        common.session_cmd(session, cmd)
        time.sleep(1)
        cmd = "turn_on_slot_12v.sh on {}".format(slot_list)
        if swm_lp == True:
            cmd = "".join((cmd, " 1"))
        common.session_cmd(session, cmd)

        # Wait for nic to boot
        print("Wait", wtime, "after power cycle")
        time.sleep(wtime)

        common.session_stop(session)
        return ret

    def nic_warm_reset(self, session, slot):
        print("Asserting warm reset...")
        if self.get_asic_type(slot) == "SALINA":
            cmd = "i2cset -yr {} 0x4a 0x10 0x3a".format(slot+2)
            common.session_cmd(session, cmd)
            cmd = "i2cset -yr {} 0x4a 0x10 0xba".format(slot+2)
            common.session_cmd(session, cmd)
        else:
            cmd = "i2cset -yr {} 0x4a 0x10 0xbe".format(slot+2)
            common.session_cmd(session, cmd)
            cmd = "i2cset -yr {} 0x4a 0x10 0x3e".format(slot+2)
            common.session_cmd(session, cmd)

    def nic_power_cycle(self, session, slot=0):
        print("Powercycling...")
        cmd = "turn_on_slot.sh off {}".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(3)
        cmd = "turn_on_slot.sh on {}".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(3)
        print("Powercycling done")

    def enter_uboot(self, session, slot=0, timeout=30, uboot_delay=60, num_retry=3, uart_id=1, warm_reset=False):
        expstr = ["Capri# ", "DSC# "]
        ret = -1
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            sys.exit(0)

        session.timeout = timeout
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(1)
        for retry in range(num_retry):
            print("Attempt {} of {} to enter uboot".format(retry, num_retry))
            if warm_reset:
                self.nic_warm_reset(session, slot)
            else:
                print("Powercycling...")
                cmd = "turn_on_slot.sh off {}".format(slot)
                common.session_cmd(session, cmd)
                time.sleep(5)
                cmd = "turn_on_slot.sh on {}".format(slot)
                common.session_cmd(session, cmd)

            self.set_cpld_uart_bits(session, slot, uart_id=uart_id)

            #time.sleep(2)
            cmd = self.get_connect_cmd(slot, uart_id=uart_id)
            session.sendline(cmd)
            session.expect(["Terminal ready", "buffer cleared"])
            time.sleep(1) # extra time to ctrl-c doesn't get captured by fpga_uart
            session.sendline("") # extra <enter> needed so that the next ctrl-c doesn't kill con_connect.sh if its too fast

            for i in range(uboot_delay):
                session.timeout = 0.5
                try:
                    print("C+C", i)
                    session.send(chr(3))
                    session.expect(expstr)
                    #time.sleep(1)
                    ret = 0
                    break
                except pexpect.TIMEOUT:
                    print("timeout:", i)
                    ret = -1
            self.uart_session_stop(session)
            if ret == 0:
                break

        if ret == -1:
            print("=== Failed to enter uboot ===")
        return ret

    def salina_power_cycle(self, session, slot=0, warm_reset=False, pc=True, v12_reset=False):
        if pc:
            if warm_reset:
                self.nic_warm_reset(session, slot)
            elif v12_reset:
                print("Powercycling 12V...")
                cmd = "turn_on_slot_12v.sh off {}".format(slot)
                common.session_cmd(session, cmd)
                time.sleep(5)
                cmd = "turn_on_slot_12v.sh on {}".format(slot)
                common.session_cmd(session, cmd)
            else:
                print("Powercycling...")
                cmd = "turn_on_slot.sh off {}".format(slot)
                common.session_cmd(session, cmd)
                time.sleep(3)
                cmd = "turn_on_slot.sh on {}".format(slot)
                common.session_cmd(session, cmd)

    def enter_uboot_salina(self, session, slot=0, timeout=30, uboot_delay=60, uart_id=1, expect_sig=[], warm_reset=False, pc=True, v12_reset=False):
        expstr = ["DSC# "]
        ret = 0
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            sys.exit(0)

        session.timeout = timeout

        uart_session = common.session_start()
        uart_session.timeout = timeout
        # Start console first
        cmd = self.get_connect_cmd(slot, uart_id=uart_id)
        uart_session.sendline(cmd)
        uart_session.expect(["Terminal ready", "buffer cleared"])

        self.salina_power_cycle(session, slot, warm_reset, pc, v12_reset)

        self.set_cpld_uart_bits(session, slot, uart_id=uart_id)
        #time.sleep(1) # extra time to ctrl-c doesn't get captured by fpga_uart
        #session.sendline("") # extra <enter> needed so that the next ctrl-c doesn't kill con_connect.sh if its too fast

        try:
            uart_session.expect(expect_sig)
        except pexpect.TIMEOUT:
            print("==== Failed: did not reach uboot shell")
            self.uart_session_stop(uart_session)
            common.session_stop(uart_session)
            return -1
        if expect_sig == "Autoboot ":
            for i in range(uboot_delay):
                uart_session.timeout = 0.5
                try:
                    print("C+C")
                    uart_session.send(chr(3))
                    idx = uart_session.expect(expstr)
                    #time.sleep(1)
                    ret = 0
                    if idx == 0:
                        break
                except pexpect.TIMEOUT:
                    print("timeout:", i)
                    ret = -1

        self.uart_session_stop(uart_session)
        common.session_stop(uart_session)

        if ret == -1:
            print("=== Failed to enter uboot ===")
        return ret

    def enter_uboot_by_sysreset_after_pwr_cycle(self, session, slot=0, timeout=30):
        expstr = ["Capri# ", "DSC# "]
        ret = -1
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            sys.exit(0)

        session.timeout = timeout
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(1)

        self.uart_session_start(session, slot)
        cmd = "sysreset.sh\r"
        session.sendline(cmd)
        time.sleep(1)
        for i in range(60):
            session.timeout = 0.5
            try:
                print("C+C", i)
                session.send(chr(3))
                session.expect(expstr)
                ret = 0
                break
            except pexpect.TIMEOUT:
                print("timeout:", i)
                ret = -1
        self.uart_session_stop(session)

        if ret == -1:
            print("=== Failed to enter uboot ===")
        return ret

    def enter_uboot_by_sysreset_after_pwr_cycle_v2(self, session, timeout=30):
        expstr = ["Capri# ", "DSC# "]
        ret = -1

        self.uart_session_start(session, slot)
        cmd = "sysreset.sh\r"
        session.sendline(cmd)
        time.sleep(1)
        for i in range(60):
            session.timeout = 0.5
            try:
                print("C+C", i)
                session.send(chr(3))
                session.expect(expstr)
                ret = 0
                break
            except pexpect.TIMEOUT:
                print("timeout:", i)
                ret = -1
        self.uart_session_stop(session)

        if ret == -1:
            print("=== Failed to enter uboot ===")
        return ret

    def enter_uboot_by_sysreset(self, session, slot=0, timeout=30):
        expstr = ["Capri# ", "DSC# "]
        ret = -1
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            sys.exit(0)

        session.timeout = timeout
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(1)
        for retry in range(3):
            cmd = "turn_on_slot.sh off {}".format(slot)
            common.session_cmd(session, cmd) 
            cmd = "turn_on_slot.sh on {}".format(slot)
            common.session_cmd(session, cmd) 
            self.set_cpld_uart_bits(session, slot)
            print("turn on slot, wait for 30 seconds\n")
            sys.stdout.flush()
            time.sleep(30)

            uartsession = common.session_start()
            uartsession.timeout = timeout
            self.uart_session_start(uartsession, slot)
            cmd = "sysreset.sh\r"
            uartsession.sendline(cmd)
            time.sleep(1)
            print("Trying break into uboot {}".format(retry))
            for i in range(60):
                uartsession.timeout = 0.5
                try:
                    print("C+C", i)
                    uartsession.send(chr(3))
                    uartsession.expect(expstr)
                    ret = 0
                    break
                except pexpect.TIMEOUT:
                    print("timeout:", i)
                    ret = -1
            self.uart_session_stop(uartsession)
            if ret == 0:
                break

        if ret == -1:
            print("=== Failed to enter uboot ===")
        return ret

    def enter_uboot_esec(self, session, slot=0, timeout=30):
        expstr = ["Capri# ", "DSC# "]
        ret = -1
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            sys.exit(0)

        numRetry = 3

        session.timeout = timeout
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd) 
        time.sleep(1)

        asic_type = self.get_asic_type(slot)
        for retry in range(numRetry):
            print("Trying enter uboot {}".format(retry))
            if (asic_type == "ELBA_FPGA"):
                cmd = "smbutil -uut=uut_{} -dev=cpld -rd -addr=0x21".format(slot)
                common.session_cmd(session, cmd)
                match = re.search(r'data=(0x[a-fA-F0-9]+)', session.before)
                if match:
                    cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x21 -data={}".format(slot, hex(int(match.group(1), 16) | 0x10))
                    common.session_cmd(session, cmd)
                else:
                    print("Failed to read CPLD addr=0x21")
                    continue

                cmd = "smbutil -uut=uut_{} -dev=cpld -rd -addr=0x20".format(slot)
                common.session_cmd(session, cmd)
                match = re.search(r'data=(0x[a-fA-F0-9]+)', session.before)
                if match:
                    cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x20 -data={}".format(slot, hex(int(match.group(1), 16) | 0x6))
                    common.session_cmd(session, cmd)
                else:
                    print("Failed to read CPLD addr=0x21")
                    continue

                cmd = "smbutil -uut=uut_{} -dev=cpld -rd -addr=0x51".format(slot)
                common.session_cmd(session, cmd)
                match = re.search(r'data=(0x[a-fA-F0-9]+)', session.before)
                if match:
                    data = int(match.group(1), 16)
                    cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x51 -data={}".format(slot, data | 0x10)
                    common.session_cmd(session, cmd)
                    cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x51 -data={}".format(slot, data & (~0x10))
                    common.session_cmd(session, cmd)
                else:
                    print("Failed to read CPLD addr=0x21")
                    continue
            else:
                cmd = "turn_on_slot.sh off {}".format(slot)
                common.session_cmd(session, cmd)
                cmd = "turn_on_hub.sh {}".format(slot)
                common.session_cmd(session, cmd)
                cmd = "turn_on_slot_3v3.sh on {}".format(slot)
                common.session_cmd(session, cmd)
                self.set_cpld_uart_bits(session, slot)
                cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x20 -data=0x7".format(slot)
                common.session_cmd(session, cmd)

                cmd = "turn_on_slot.sh on {}".format(slot)
                common.session_cmd(session, cmd)

            print("Wait for 60 seconds before entering uboot")
            sleep(60)

            self.uart_session_start(session, slot)
            cmd = "sysreset.sh\r"
            session.sendline(cmd)
            time.sleep(1)
            for i in range(60):
                session.timeout = 0.5
                try:
                    print("C+C", i)
                    session.send(chr(3))
                    session.expect(expstr)
                    ret = 0
                    break
                except pexpect.TIMEOUT:
                    print("timeout:", i)
                    ret = -1
            self.uart_session_stop(session)
            if ret == 0:
                break

        if ret == -1:
            print("=== Failed to enter uboot ===")
        return ret

    def enter_uboot_after_reset(self, session, slot=0, timeout=30,):
        ret = -1
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            sys.exit(0)

        session.timeout = timeout

        for i in range(60):
            session.timeout = 0.3
            try:
                print("C+C", i)
                session.send(chr(3))
                session.expect("Capri# ")
                #time.sleep(1)
                ret = 0
                break
            except pexpect.TIMEOUT:
                print("timeout:", i)
                ret = -1

        return ret

    def boot_goldfw_uboot(self, slot=0, timeout=30):
        session = common.session_start()
        ret = self.enter_uboot(session, slot, timeout)
        if ret != 0:
            print("Failed to enter uboot")
            common.session_stop(session)
            return ret

        #ret = self.uart_session_start(session, slot)
        #if ret != 0:
        #    print("Failed to start uart session")
        #    common.session_stop(session)
        #    return ret

        ret = self.conn_uboot(session, slot)
        if ret != 0:
            print("Failed to connect uboot")
            common.session_stop(session)
            return ret

        session.sendline("boot goldfw")
        time.sleep(3)
        self.uart_session_stop(session)
        common.session_stop(session)
        return 0

        #self.uart_session_cmd(session, "mkdir -p /data/elba ; mount /dev/mmcblk0p10 /data; mkdir -p /data/elba; cd /data/elba")

        ## Calculate IP
        #ip_int = 100+int(slot)
        #ip = "10.1.1."+str(ip_int)
        #self.uart_session.cmd(session, "ifconfig oob_mnic0 "+ip+" netmask 255.255.255.0")
        #self.uart_session_stop(session)

    def conn_uboot(self, session, slot, uart_id=1):
        #exprStr = "Capri# "
        expstr = ["Capri# ", "DSC# "]
        session.timeout = 15
        ret = 0
        try:
            cmd = self.get_connect_cmd(slot, uart_id=uart_id)
            session.sendline(cmd)
            session.expect(["Terminal ready", "buffer cleared"])
            session.sendline("\r")
            session.expect(expstr)
        except pexpect.TIMEOUT:
            print("Failed to connet uboot")
            self.uart_session_stop(session)
            ret = -1
        return ret

    def mtest_uboot(self, slot=0):
        err = 0
        numRetry = 3
        session = common.session_start()
        ret = self.enter_uboot(session, slot)
        if ret == -1:
            print("=== Failed to change uboot board rate! ===")
            print("=== MTEST FAILED ===")
            return ret

        exprStr = "Capri# "
        mtest_cmd = "mtest {} {} 0xaaaaaaaa 1"
        session.timeout = 30
        try:
            cmd = self.fmt_con_cmd.format(slot)
            #session.sendline(cmd)
            #session.expect("Terminal ready")
            #time.sleep(1)
            session.send("\r")
            session.expect(exprStr)

            session.sendline("bdinfo")
            session.expect(exprStr)

            start = "0xC0000000"
            if "start    = 0x140000000" in session.before:
                print("=== 4G HBM detected ===")
                end = "0x17fffffff"
                timeout = 60
            elif "start    = 0x240000000" in session.before:
                print("=== 8G HBM detected ===")
                end = "0x27fffffff"
                timeout = 150

            session.timeout = 30
            cmd = mtest_cmd.format("0x80000000", "0xBE9FFFFF")
            session.sendline(cmd)
            session.expect(exprStr)
            if "with 0 errors" in session.before:
                print("=== MTEST PASSED LOW 1G ===")
            else:
                print("=== MTEST FAILED LOW 1G ===")
                err = err + 1

            session.timeout = timeout
            cmd = mtest_cmd.format(start, end)
            session.sendline(cmd)
            session.expect(exprStr)
            if "with 0 errors" in session.before:
                print("=== MTEST PASSED HIGH 3G ===")
            else:
                print("=== MTEST FAILED HIGH 3G ===")
                err = err + 1

        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Faled to perform uboot mtest ===")
            err = -1

        if err == 0:
            print("=== MTEST PASSED ===")
        else:
            print("=== MTEST FAILED ===")

        self.uart_session_stop(session)
        common.session_stop(session)

    def get_card_type(self, slot):
        uut = "UUT_"+str(slot)
        card_type = os.environ[uut]
        if not card_type:
            return "UNKNOWN"
        return card_type

    def get_asic_type(self, slot):
        # Get AISC type
        uut = "UUT_"+str(slot)
        card_type = os.environ[uut]
        if card_type == "ORTANO"  or \
           card_type == "ORTANO2" or \
           card_type == "ORTANO2A" or \
           card_type == "ORTANO2AC" or \
           card_type == "ORTANO2I" or \
           card_type == "ORTANO2S" or \
           card_type == "BIODONA":
            asic_type = "ELBA_CPLD"
        elif card_type == "LACONA"       or \
             card_type == "LACONADELL"   or \
             card_type == "LACONA32"     or \
             card_type == "LACONA32DELL" or \
             card_type == "POMONTE"      or \
             card_type == "POMONTEDELL":
            asic_type = "ELBA_FPGA"
        elif card_type == "GINESTRA_D4"  or \
             card_type == "GINESTRA_D5":
            asic_type = "GIGLIO_CPLD"
        elif card_type == "MALFA" or \
             card_type == "LENI" or \
             card_type == "LENI48G" or \
             card_type == "LINGUA" or \
             card_type == "POLLARA":
            asic_type = "SALINA"
        else:
            asic_type = "CAPRI"
        print(("asic_type:", asic_type))
        return asic_type

    def enable_mnic(self, slot=0, first_pwr_on=False, session_uart=None):
        fmt_dummy_fru_json = """
{{
    "manufacturing-date": "1616630400",
    "manufacturer": "Pensando",
    "product-name": "DSC2-200 2x200GbE Dual QSFP56",
    "serial-number": "FLM20000001",
    "part-number": "{}",
    "frufileid": "02\/19\/21",
    "board-id": "6",
    "engineering-change-level": "0",
    "num-mac-address": "24",
    "mac-address": "00:ae:{:02}:f6:00:28",
    "board-assembly-area": "{}"
}}

        """
        #fmt_dummy_fru_json = '"mac-address": "00:11:22:33:{:02}:00"'
        ret = 0
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            return -1

        asic_type = self.get_asic_type(slot)
        if asic_type == "ELBA_CPLD":
            dummy_fru_json = fmt_dummy_fru_json.format("DSC2-2Q200-32R32F64P-R", slot, "68-0015-02 01")
        elif asic_type == "GIGLIO_CPLD":
            dummy_fru_json = fmt_dummy_fru_json.format("DSC2A-2Q200-32S32F64P-R", slot, "68-0075-01")
        elif asic_type == "SALINA":
            pass
        else:
            dummy_fru_json = fmt_dummy_fru_json.format("0PCFPCA00", slot, "68-0015-02 01")

        if session_uart == None:
            session = common.session_start()
            self.uart_session_start(session, slot)
        else:
            session = session_uart
        session.timeout = 60

        cmd_pre = "ulimit -c unlimited"
        cmd_mac = "echo \'00:11:22:33:{:02}:00\' > /sysconfig/config0/sysuuid"
        cmd_mac = cmd_mac.format(slot)
        #print "MAC:", cmd_mac
        try:
            if first_pwr_on == True:
                if asic_type == "CAPRI":
                    self.uart_session_cmd(session, "cd /nic/conf/")
                    self.uart_session_cmd(session, "cp catalog_hw_68-0003.json catalog_hw_")
                    self.uart_session_cmd(session, cmd_mac)
                elif asic_type == "ELBA_CPLD" or asic_type == "ELAB_FPGA":
                    session.send("cat > /tmp/fru.json")
                    session.send("\r")
                    session.send(dummy_fru_json)
                    session.send(chr(3))
                    session.expect("#")
                else:
                    pass

            if asic_type == "GIGLIO_CPLD":
                cmd = "sed -i 's/\"port_num\" : \"8\", \"mac_id\" : \"1\"/\"port_num\" : \"8\", \"mac_id\" : \"2\"/' /nic/conf/catalog_hw_board_id_0x03610001.json"
                self.uart_session_cmd(session, cmd)
                cmd = "sed -i 's/\"port_num\" : \"9\", \"mac_id\" : \"2\"/\"port_num\" : \"9\", \"mac_id\" : \"1\"/' /nic/conf/catalog_hw_board_id_0x03610001.json"
                self.uart_session_cmd(session, cmd)

            if asic_type == "SALINA":
                self.uart_session_cmd(session, cmd_pre)
                print("wait 30 s for mgmt port to be ready")
                time.sleep(30)
                #self.uart_session_cmd(session, "dpctl debug update pipeline pin-lif --lif 65 --uplink 8", 30)
            session.sendline("ifconfig -a")
            session.expect("\#")
            temp = session.after
            if 'oob_mnic0' in session.before:
                print('oob_mnic0 enabled')
            else:
                self.uart_session_cmd(session, cmd_pre)
                self.uart_session_cmd(session, "sysinit.sh classic hw diag", 15)

        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Faled to enable management port ===")
            ret = -1

        if session_uart == None:
            self.uart_session_stop(session)
            common.session_stop(session)
        return ret

    def run_mes_mtp_reset_commands(self, session):
        self.uart_session_cmd(session, "diag_test ps48_reg_op -d serdes -o 24 -w --mask 0x1 -v 1")
        self.uart_session_cmd(session, "diag_test ps48_reg_op -d mes -o 0xA68 -w --mask 0x1 -v 0x0")
        self.uart_session_cmd(session, "diag_test ps48_reg_op -d serdes -o 24 -w --mask 0x1 -v 0")
        self.uart_session_cmd(session, "diag_test ps48_reg_op -d serdes -o 72 -r")
        self.uart_session_cmd(session, "diag_test ps48_reg_op -d mes -o 0xA68 -w --mask 0x1 -v 0x1")

    def mes_mtp_reset(self, slot, session_uart=None):
        if session_uart == None:
            session = common.session_start()
            self.uart_session_start(session, slot)
        else:
            session = session_uart

        session.timeout = 30
        self.run_mes_mtp_reset_commands(session)
        if session_uart == None:
            self.uart_session_stop(session)
            common.session_stop(session)

    def config_mnic(self, slot=0, uefi=False, dis_net_port=False, session_uart=None):
        ret = 0
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            return -1

        if session_uart == None:
            session = common.session_start()
            self.uart_session_start(session, slot)
        else:
            session = session_uart

        session.timeout = 30

        try:
            session.sendline("ifconfig -a")
            session.expect("\#")
            temp = session.after
            if 'oob_mnic0' in session.before:
                asic_type = self.get_asic_type(slot)
                # only works for Elba FPGA cards with PS48
                if asic_type == "ELBA_FPGA":
                    self.run_mes_mtp_reset_commands(session)
                elif asic_type == "SALINA":
                    pass
                else:
                    self.uart_session_cmd(session, "ifconfig oob_mnic0 down")
                    time.sleep(0.5)
                    print('oob_mnic0 enabled')
                    self.uart_session_cmd(session, "ifconfig oob_mnic0 up")
                    self.uart_session_cmd(session, "halctl debug port --port Eth1/3 --admin-state up")
                    if dis_net_port == True:
                        self.uart_session_cmd(session, "/data/nic_util/xo3dcpld -smiwr 0 0x3 0x1940")
                self.uart_session_cmd(session, "ifconfig oob_mnic0 10.1.1.{} netmask 255.255.255.0 up".format(slot+100))
                self.uart_session_cmd(session, "ifconfig")
            else:
                print('oob_mnic0 NOT enabled!')
                ret = 1

        except pexpect.TIMEOUT:
            if session_uart == None:
                self.uart_session_stop(session)
            print("=== TIMEOUT: Faled to config management port ===")
            ret = -1

        if session_uart == None:
            self.uart_session_stop(session)
            common.session_stop(session)
        return ret

    def turn_off_sgmii(self, slot=0):
        cmd = "swm_dis_sgmii.sh {}".format(slot)

        session = common.session_start()
        common.session_cmd(session, cmd)
        common.session_stop(session)

    def ping_check(self, slot=0):
        ret = 0
        session = common.session_start()
        self.uart_session_start(session, slot)

        try:
            ret, output = self.uart_session_cmd_w_ot(session, "ping 10.1.1.100 -c 10 -s 64", 60)
            if ret == 0:
                if " 0% packet loss" not in output:
                    print("Ping check failed!")
                    ret = -2
        except:
            self.uart_session_stop(session)
            print("=== TIMEOUT: Failed to ping host ===")
            ret = -1

        self.uart_session_stop(session)
        common.session_stop(session)
        return ret

    def ping_check_mtp(self, slot=0, session_bash=None):
        ret = 0
        if session_bash == None:
            session = common.session_start()
        else:
            session = session_bash

        try:
            cmd = "ping 10.1.1.{} -c 3 -s 64".format(100+slot)
            ret = common.session_cmd(session, cmd, 60)
            cmd = "ping 10.1.1.{} -c 5 -s 64".format(100+slot)
            ret, output = common.session_cmd_w_ot(session, cmd, 60)
            if ret == 0:
                if " 0% packet loss" not in output:
                    print("Ping check failed!")
                    ret = -2
        except:
            print("=== TIMEOUT: Failed to ping slot {} ===".format(slot))
            ret = -1

        if session_bash == None:
            common.session_stop(session)
        return ret

    def fix_elba_bx(self, slot=0, session_uart=None):
        ret = 0
        if session_uart == None:
            self.switch_console(slot)
            session = common.session_start()
        else:
            session = session_uart
        session.timeout = 30
        try:
            if session_uart == None:
                self.uart_session_start(session, slot)
            self.uart_session_cmd(session, "fwupdate --init-emmc")
            ret, output = self.uart_session_cmd_w_ot(session, "fwupdate -l")
            # Only do it with one version of diagfw
            if "1.15.8-C-3" in output or "1.5.0-EXP" in output:
                self.uart_session_cmd(session, "halctl debug port aacs-server-start --server-port 9000")
                self.uart_session_cmd(session, "export SERDES_DUT_IP=localhost:9000")
                self.uart_session_cmd(session, "export SERDES_SBUS_RINGS=4")
                self.uart_session_cmd(session, "aapl serdes -mem-rd lsb 0x835 -a 3:5")
                self.uart_session_cmd(session, "aapl serdes -int 0xe 0x100 -a 3:5")
                self.uart_session_cmd(session, "aapl serdes -int 0xe 0x100 -a 3:5")
                self.uart_session_cmd(session, "aapl serdes -int 0xe 0x100 -a 3:5")
                self.uart_session_cmd(session, "aapl serdes -int 0xe 0x100 -a 3:5")
                self.uart_session_cmd(session, "aapl serdes -int 0xe 0x100 -a 3:5")
                self.uart_session_cmd(session, "halctl debug port aacs-server-stop")
                self.uart_session_stop(session)

        except pexpect.TIMEOUT:
            if session_uart == None:
                self.uart_session_stop(session)
            print("=== TIMEOUT: Faled to fix elb bx ===")
            ret = -1

        if session_uart == None:
            self.uart_session_stop(session)
            common.session_stop(session)
        return ret

    def sal_wait_for_uplink_ready(self, slot=0, session_uart=None):
        ret = -1
        if session_uart == None:
            session = common.session_start()
            self.uart_session_start(session, slot)
        else:
            session = session_uart

        try:
            self.uart_session_cmd(session, "pdsctl show port status", 360)
            match = re.search(r'Eth1\/1\s+.*UP\/', session.before)
            if match:
                ret = 0
            else:
                print("=== Uplink port is not ready ===")
        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Failed to wait for uplink ready ===")

        if session_uart == None:
            self.uart_session_stop(session)
            common.session_stop(session)
        return ret

    def get_mgmt_rdy(self, slot=0, first_pwr_on=False, skip_enable=False, asic_type="elba", uefi=False, dis_net_port=False, session_bash=None, session_uart=None):
        numRetry = 6
        ret = 0
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            return -1

        if session_bash == None:
            self.switch_console(slot)

        if skip_enable == False:
            ret = self.enable_mnic(slot, first_pwr_on, session_uart)
            if ret != 0:
                print("=== FAIL to enable management port! ===")
                return ret

        for i in range(numRetry):
            ret = self.config_mnic(slot, uefi, dis_net_port, session_uart)
            if ret == -1:
                print("=== FAIL to enable management port! ===")
                return ret
            elif ret == 0:
                break

            time.sleep(10)

        if ret != 0:
            print("=== FAIL to enable management port! Max retry reached!")
            return -1
        else:
            print("=== Management port is ready ===")
        # for FW rev 1.68-G-9 or later, need to wait 10s before ping check
        asic_type = self.get_asic_type(slot)
        if asic_type == "GIGLIO_CPLD":
            print("sleep 10")
            time.sleep(10)
        if asic_type == "SALINA":
            ret = self.sal_wait_for_uplink_ready(slot, session_uart)
            if ret != 0:
                print("=== FAIL to wait for uplink ready! ===")
                return ret
        ret = self.ping_check_mtp(slot, session_bash)
        print(("ret:", ret))

        # if ping test fails, apply WA for Elba
        mtpType = os.environ['MTP_TYPE']
        if ret == -2 and mtpType == "MTP_ELBA" and first_pwr_on == True: 
            self.fix_elba_bx(slot, session_uart)
            ret = self.ping_check_mtp(slot, session_bash)

        # if ping test fails, retry the MTP port reset
        asic_type = self.get_asic_type(slot)
        if ret != 0 and asic_type == "ELBA_FPGA":
            for i in range(numRetry):
                self.mes_mtp_reset(slot, session_uart)
                ret = self.ping_check_mtp(slot, session_bash)
                if ret == 0:
                    break

        return ret

    def switch_fw(self, slot=0):
        ret = 0
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            return -1

        session = common.session_start()
        self.uart_session_start(session, slot)
        session.timeout = 60

        cmd = "fwupdate -r"
        try:
            session.sendline(cmd)
            session.expect("\#")
            temp = session.after
            if 'mainfwa' in session.before:
                print('current fw is mainfwa, switching to mainfwb')
                cmd = "fwupdate -s mainfwb"
            else:
                print('current fw is mainfwb, switching to mainfwa')
                cmd = "fwupdate -s mainfwa"

        except pexpect.TIMEOUT:
            self.uart_session_stop(session)
            print("=== TIMEOUT: Faled to get fw ===")
            ret = -1

        try:
            session.sendline(cmd)
            session.expect("\#")

        except pexpect.TIMEOUT:
            self.uart_session_stop(session)
            print("=== TIMEOUT: Faled to switch fw ===")
            ret = -1

        try:
            session.sendline("reboot")
            session.expect("\#")

        except pexpect.TIMEOUT:
            self.uart_session_stop(session)
            print("=== TIMEOUT: Faled to reboot after switching fw ===")
            ret = -1

        self.uart_session_stop(session)
        common.session_stop(session)
        return ret

    def config_ddr(self, slot, hardcode, speed):
        expstr = ["Capri# ", "DSC# "]
        ret = 0
        session = common.session_start()
        ret = self.enter_uboot(session, slot)
        if ret != 0:
            print("Failed to enter uboot")
            return ret
        ret = self.conn_uboot(session, slot)
        if ret != 0:
            print("Failed to connect uboot")
            return ret

        if hardcode == True:
            self.uart_session_cmd(session, "env set ddr_use_hardcoded_training 1", 30, expstr)
        else:
            self.uart_session_cmd(session, "env set ddr_use_hardcoded_training 0", 30, expstr)

        if speed == 2400:
            self.uart_session_cmd(session, "env set ddr_freq 2400", 30, expstr)
        else:
            self.uart_session_cmd(session, "env set ddr_freq 3200", 30, expstr)
        self.uart_session_cmd(session, "saveenv", 30, expstr)
        self.uart_session_cmd(session, "saveenv", 30, expstr)
        self.uart_session_stop(session)
        common.session_stop(session)
        return ret

    def disable_pcie_uboot(self, slot):
        expstr = ["Capri# ", "DSC# "]
        ret = 0
        session = common.session_start()
        ret = self.enter_uboot_by_sysreset_after_pwr_cycle(session, slot)
        if ret != 0:
            print("Failed to enter uboot")
            common.session_stop(session)
            return ret
        ret = self.conn_uboot(session, slot)
        if ret != 0:
            print("Failed to connect uboot")
            common.session_stop(session)
            return ret

        pcie_config_cmds = ["setenv pcie_poll_disable 1", "saveenv", "saveenv"]
        ret = self.uart_session_cmd_list(session, pcie_config_cmds, 30, expstr)
        self.uart_session_stop(session)
        common.session_stop(session)
        if ret == -1:
            print("Failed to set pcie_poll_disable")
        return ret

    def enable_pcie_uboot(self, slot):
        expstr = ["Capri# ", "DSC# "]
        ret = 0
        session = common.session_start()
        ret = self.enter_uboot_by_sysreset_after_pwr_cycle(session, slot)
        if ret != 0:
            print("Failed to enter uboot")
            common.session_stop(session)
            return ret
        ret = self.conn_uboot(session, slot)
        if ret != 0:
            print("Failed to connect uboot")
            common.session_stop(session)
            return ret

        pcie_config_cmds = ["setenv pcie_poll_disable", "saveenv", "saveenv"]
        ret = self.uart_session_cmd_list(session, pcie_config_cmds, 30, expstr)
        self.uart_session_stop(session)
        common.session_stop(session)
        if ret == -1:
            print("Failed to set pcie_poll_disable")
        return ret

    def config_cpld_qspi_wp(self, session, enable):
        expstr = ["Capri# ", "DSC# "]
        ret = 0
        try:
            if enable == True:
                cmd = "cpldwr 0x12 0x4"
                rd_value = 0x0
                str = "enable"
            else:
                cmd = "cpldwr 0x12 0"
                rd_value = 0x80
                str = "disable"
            session.sendline(cmd)
            session.expect(expstr)
            cmd = "cpldrd 0x1"
            session.sendline(cmd)
            session.expect(expstr)

            # Remove empty lines: happened on Matera MTP
            before = [s for s in session.before.splitlines() if s]

            #if int(session.before.splitlines()[1], 16) & 0x80 != rd_value:
            if int(before[1], 16) & 0x80 != rd_value:
                print("unexpected status after", str, "WP")
                ret = -1
        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Failed to", str, "WP ===")
            ret = -1
        if ret != 0:
            print("Failed to", str, "WP on CPLD")
        return ret

    def config_esec_qspi_wp(self, session, enable):
        expstr = ["Capri# ", "DSC# "]
        ret = 0
        try:
            if enable == True:
                cmd = "hwprot wrdis bot 0x10000"
                str = "enable"
            else:
                cmd = "hwprot wren bot 0"
                str = "disable"
            session.sendline(cmd)
            session.expect(expstr)
        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Failed to", str, "WP ===")
            ret = -1
        if ret != 0:
            print("Failed to", str, "WP in uboot")
        return ret

    def check_esec_qspi_wp(self, session, enable):
        expstr = ["Capri# ", "DSC# "]
        ret = 0
        try:
            if enable == True:
                exp_output = "SR write-disabled, W# asserted (SR locked), BP bot 0x10000"
                str = "enable"
            else:
                exp_output = "SR write-enabled, W# deasserted (SR unlocked), BP bot none"
                str = "disable"
            session.sendline("hwprot")
            session.expect(expstr)
            if exp_output not in session.before:
                print("unexpected status after", str, "WP")
                ret = -1
        except pexpect.TIMEOUT:
            print("=== TIMEOUT: Failed to", str, "WP ===")
            ret = -1
        if ret != 0:
            print("Failed to", str, "WP in uboot")
        return ret

    def file_compare(self, fn1, fn2):
        ret = 0
        try:
            with open(fn1, "r") as f1:
                f1_lines = f1.readlines()
            with open(fn2, "r") as f2:
                f2_lines = f2.readlines()
            for i in range(len(f1_lines)):
                if f1_lines[i] != f2_lines[i]:
                    print("line " + str(i) + " not match, " + fn1 + ": " + f1_lines[i] + ", " + fn2 + ": " + f2_lines[i])
                    ret = 1
                    break
        except (IOError, OSError) as e:
            print(e)
            ret = 1
        return ret

    def qspi_wp_program_test(self, enable, j2c_session, start_addr):
        ret = -1
        common.session_cmd(j2c_session, "rm -f /home/diag/save.txt", 30, False, "tclsh]")
        common.session_cmd(j2c_session, "rm -f /home/diag/after_prog.txt", 30, False, "tclsh]")
        common.session_cmd(j2c_session, "rm -f /home/diag/after_prog_wo_addr.txt", 30, False, "tclsh]")
        common.session_cmd(j2c_session, "rm -f /home/diag/random.hex", 30, False, "tclsh]")
        # save
        common.session_cmd(j2c_session, "elb_dump_qspi OTHER {} 0x10000 /home/diag/save.txt".format(start_addr), 300, False, "tclsh]")
        #common.session_cmd(j2c_session, "exec awk {print $2} /home/diag/save.txt > /home/diag/restore.txt", 300, False, "tclsh]")
        # program random
        common.session_cmd(j2c_session, "head -c 64k /dev/urandom > /home/diag/random.txt", 30, False, "tclsh]")
        common.session_cmd(j2c_session, "bin2hex /home/diag/random.txt > /home/diag/random.hex", 30, False, "tclsh]")
        common.session_cmd(j2c_session, "elb_prog_qspi /home/diag/random.hex {}".format(start_addr), 300, False, "tclsh]")
        # dump after program
        common.session_cmd(j2c_session, "elb_dump_qspi OTHER {} 0x10000 /home/diag/after_prog.txt".format(start_addr), 300, False, "tclsh]")
        common.session_cmd(j2c_session, "exec awk {{print $2}} /home/diag/after_prog.txt > /home/diag/after_prog_wo_addr.txt", 300, False, "tclsh]")
        if enable == True:
            # compare with saved
            if self.file_compare("/home/diag/after_prog.txt", "/home/diag/save.txt") == 0:
                ret = 0
            else:
                common.session_cmd(j2c_session, "exit", 10)
                common.session_stop(j2c_session)
                ret = -1
        else:
            # compare with programmed
            if self.file_compare("/home/diag/after_prog_wo_addr.txt", "/home/diag/random.hex") == 0:
                ret = 0
            else:
                common.session_cmd(j2c_session, "exit", 10)
                common.session_stop(j2c_session)
                ret = -1
        return ret

    def qspi_wp_erase_test(self, enable, j2c_session, start_addr):
        ret = -1

        common.session_cmd(j2c_session, "rm -f /home/diag/after_erase.txt", 30, False, "tclsh]")
        common.session_cmd(j2c_session, "rm -f /home/diag/expected_after_erase.txt", 30, False, "tclsh]")
        # erase
        common.session_cmd(j2c_session, "elb_erase_qspi 0x10000 {}".format(start_addr), 100, False, "tclsh]")
        # dump after erase
        common.session_cmd(j2c_session, "elb_dump_qspi OTHER {} 0x10000 /home/diag/after_erase.txt".format(start_addr), 300, False, "tclsh]")
        if enable == True:
            # compare with saved
            if self.file_compare("/home/diag/after_erase.txt", "/home/diag/save.txt") == 0:
                ret = 0
            else:
                common.session_cmd(j2c_session, "exit", 10)
                common.session_stop(j2c_session)
                ret = -1
        else:
            # should be erased
            common.session_cmd(j2c_session, "exec awk {$2=\"FFFFFFFF\"} /home/diag/save.txt > /home/diag/expected_after_erase.txt", 30, False, "tclsh]")
            if self.file_compare("/home/diag/after_erase.txt", "/home/diag/expected_after_erase.txt") == 0:
                ret = 0
            else:
                common.session_cmd(j2c_session, "exit", 10)
                common.session_stop(j2c_session)
                ret = -1
        return ret

    def verify_esec_qspi_wp(self, slot, enable):
        ret = -1
        if enable == True:
            str = "enable"
        else:
            str = "disable"

        j2c_session = common.session_start()
        common.session_cmd(j2c_session, "cd /home/diag/diag/asic/asic_src/ip/cosim/tclsh")

        # TCL command
        common.session_cmd(j2c_session, "tclsh", 40, False, ending=["%", "tclsh]"])
        common.session_cmd(j2c_session, "source .tclrc.diag.elb", 40, False, "tclsh]")

        common.session_cmd(j2c_session, "set slot {}".format(slot), 30, False, "tclsh]")
        common.session_cmd(j2c_session, "set port [mtp_get_j2c_port $slot]", 30, False, "tclsh]")
        common.session_cmd(j2c_session, "set slot1 [mtp_get_j2c_slot $slot]", 30, False, "tclsh]")
        common.session_cmd(j2c_session, "diag_close_j2c_if $port $slot1", 30, False, "tclsh]")
        common.session_cmd(j2c_session, "diag_open_j2c_if $port $slot1", 30, False, "tclsh]")
        common.session_cmd(j2c_session, "_msrd", 30, False, "tclsh]")
        if "0x00000001" not in j2c_session.before:
            print("ERROR: j2c failure")
            common.session_cmd(j2c_session, "exit", 10)
            common.session_stop(j2c_session)
            return -1

        # only the bottom 64k is protected by WP
        ret = self.qspi_wp_program_test(enable, j2c_session, "0x70000000")
        if ret != 0:
            return ret
        ret = self.qspi_wp_erase_test(enable, j2c_session, "0x70000000")
        if ret != 0:
            return ret
        # negative test: 64k from 0x70010000 is not affected by WP
        ret = self.qspi_wp_program_test(False, j2c_session, "0x70010000")
        if ret != 0:
            return ret
        ret = self.qspi_wp_erase_test(False, j2c_session, "0x70010000")
        if ret != 0:
            return ret
        # negative test: 64k from 0x7fff0000 is not affected by WP
        ret = self.qspi_wp_program_test(False, j2c_session, "0x7fff0000")
        if ret != 0:
            return ret
        ret = self.qspi_wp_erase_test(False, j2c_session, "0x7fff0000")
        if ret != 0:
            return ret

        common.session_cmd(j2c_session, "exit", 10)
        common.session_stop(j2c_session)
        return ret


    # enable = True:  enable WP
    # enable = False: disable WP
    def ena_dis_esec_wp(self, slot, enable):
        ret = 0
        session = common.session_start()
        ret = self.enter_uboot_by_sysreset_after_pwr_cycle(session, slot)
        if ret != 0:
            print("Failed to enter uboot")
            common.session_stop(session)
            return ret
        self.uart_session_start(session, slot)
        # deassert CPLD WP# to make sure SR is not in locked state
        ret = self.config_cpld_qspi_wp(session, False)
        if ret != 0:
            self.uart_session_stop(session)
            common.session_stop(session)
            return ret
        # change hwprot setting
        ret = self.config_esec_qspi_wp(session, enable)
        if ret != 0:
            self.uart_session_stop(session)
            common.session_stop(session)
            return ret
        # put CPLD WP# to the requested state
        ret = self.config_cpld_qspi_wp(session, enable)
        if ret != 0:
            self.uart_session_stop(session)
            common.session_stop(session)
            return ret
        # read/verify hwprot setting
        ret = self.check_esec_qspi_wp(session, enable)
        if ret != 0:
            self.uart_session_stop(session)
            common.session_stop(session)
            return ret
        self.uart_session_stop(session)
        common.session_stop(session)
        if ret == 0:
            if enable == True:
                print("Succeeded to set QSPI WP enable for slot", slot)
            else:
                print("Succeeded to set QSPI WP disable for slot", slot)
        return ret

    def setup_uboot_env(self, slot):
        expstr = ["Capri# ", "DSC# "]
        ret = 0
        session = common.session_start()
        ret = self.enter_uboot_by_sysreset(session, slot)
        if ret != 0:
            print("Failed to enter uboot")
            return ret
        ret = self.conn_uboot(session, slot)
        if ret != 0:
            print("Failed to connect uboot")
            return ret

        self.uart_session_cmd(session, "setenv mem_dp_tot_size 26G", 30, expstr)
        self.uart_session_cmd(session, "setenv mem_bypass_size 0", 30, expstr)
        self.uart_session_cmd(session, "setenv mem_dp_tot_size 26G", 30, expstr)
        self.uart_session_cmd(session, "setenv bootargs isolcpus=2,3,6,7,10,11,14,15 nohz_full=2,3,6,7,10,11,14,15 rcu_nocbs=2,3,6,7,10,11,14,15 rcu_nocb_poll irqaffinity=0-1 console=ttyS0,115200n8", 30, expstr)
        self.uart_session_cmd(session, "saveenv", 30, expstr)
        self.uart_session_cmd(session, "saveenv", 30, expstr)
        self.uart_session_stop(session)
        common.session_stop(session)
        return ret

    def switch_console(self, slot=1):
        if int(slot) > 10:
            print("Invalide slot {}!".format(slot))
            return -1

        session = common.session_start()
        cmd = "cpldutil -cpld-wr -addr=0x18 -data=0"
        common.session_cmd(session, cmd)
        sleep(0.5)
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        sleep(0.5)
        common.session_cmd(session, cmd)
        common.session_stop(session)
        return 0

    def tcl_env_setup(self, session, slot, tcl_path='/home/diag/diag/asic'):
        print("tcl_path:", tcl_path)
        print("=== TCL ENV setup ===")
        common.session_cmd(session, "export ASIC_LIB_BUNDLE="+tcl_path)
        common.session_cmd(session, "export ASIC_SRC=$ASIC_LIB_BUNDLE/asic_src")
        common.session_cmd(session, "export ASIC_LIB=$ASIC_LIB_BUNDLE/asic_lib")
        common.session_cmd(session, "export ASIC_GEN=$ASIC_SRC")
        common.session_cmd(session, "cd $ASIC_LIB_BUNDLE/asic_lib")
        common.session_cmd(session, "source source_env_path")
        common.session_cmd(session, "export LD_LIBRARY_PATH=$ASIC_LIB_BUNDLE/depend_libs/mtp_hack:$LD_LIBRARY_PATH")
        common.session_cmd(session, "cd $ASIC_LIB_BUNDLE/depend_libs/mtp_hack")
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
        if self.get_asic_type(slot) == "SALINA":
            cmd = "fpgautil spimode {} off".format(slot)
            common.session_cmd(session, cmd)
            cmd = "jtag_accpcie_salina clr {}".format(slot)
            common.session_cmd(session, cmd)

    def read_cpld_reg(self, reg_addr, read_data, slot=1):
        ret = 0
        if int(slot) > 10:
            print("Invalide slot {}!".format(slot))
            return -1

        session = common.session_start()
        cmd = "i2cget -y {} 0x4f {}".format(int(slot)+2, int(reg_addr))
        common.session_cmd(session, cmd)
        match = re.findall(r"(0x[0-9a-fA-F]+)", session.before)
        if len(match) > 1:
            read_data[0] = match[1]
        else:
            print("Failed to read cpld reg {}".format(int(reg_addr)))
            ret = -1
        common.session_stop(session)
        return ret

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()

    group.add_argument("-mgmt", "--ena_mgmt_port", help="Enable managment port", action='store_true')
    group.add_argument("-mtest", "--mtest", help="Change baud rate", action='store_true')
    group.add_argument("-dis_pcie", "--dis_pcie", help="Disable PCIe", action='store_true')
    group.add_argument("-ena_pcie", "--ena_pcie", help="Enable PCIe", action='store_true')
    group.add_argument("-config_ddr", "--config_ddr", help="configure DDR", action='store_true')

    parser.add_argument("-br", "--baud_rate", help="Original baud rate", type=int, default=115200)
    parser.add_argument("-slot", "--slot", help="NIC slot number", type=int, default=0)
    parser.add_argument("-ping", "--ping", help="Ping test before enable management port", action='store_true')
    parser.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    parser.add_argument("-hardcode", "--hardcode", help="DDR hardcode setting", action='store_true')
    parser.add_argument("-ddr_speed", "--ddr_speed", help="DDR speed", type=int, default=3200)
    args = parser.parse_args()
    
    con = nic_con()

    if args.ena_mgmt_port == True:
        con.get_mgmt_rdy(args.slot, args.first_pwr_on)
        sys.exit()

    if args.mtest == True:
        con.mtest_uboot(args.slot)
        sys.exit()

    if args.dis_pcie == True:
        con.disable_pcie_uboot(args.slot)
        sys.exit()

    if args.ena_pcie == True:
        con.enable_pcie_uboot(args.slot)
        sys.exit()

    if args.config_ddr == True:
        con.config_ddr(args.slot, args.hardcode, args.ddr_speed)
        sys.exit()
