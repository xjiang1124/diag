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

class nic_test:
    def __init__(self):
        self.name = "nic_snake"
        self.baud_rate = 115200
        self.num_retry = 3
        self.nic_con = nic_con()

    def switch_fw(self, slot=0):
        self.nic_con.switch_fw(self.baud_rate, slot);

    def get_mtp_rev(self):
        file1 = open("/home/diag/mtp_rev","r")
        mtp_rev = file1.readlines()
        file1.close()
        return mtp_rev[0][:-1]

    def setup_env(self, slot=0, mgmt=False, timeout=30, first_pwr_on=False, pwr_cycle=True, aapl=False):
        print "=== Starting setup env on slot {} ===".format(slot)

        mtp_rev = self.get_mtp_rev()
        print("MTP_REV: ", mtp_rev)

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        try:
            if pwr_cycle == True:
                ret = self.nic_con.power_cycle_uart(self.baud_rate, slot)
                if ret != 0:
                    print "Failed to change baud rate"
                    return -1

            self.nic_con.switch_console(int(slot))

            session = common.session_start()
            session.timeout = timeout
            cmd = "turn_on_hub.sh {}".format(slot)
            common.session_cmd_no_rc(session, cmd)
            sleep(0.5)
            cmd = "smbutil -uut=uut_{} -dev=cpld -rd -addr=0x80".format(slot)
            common.session_cmd_no_rc(session, cmd)
            cpldID = re.findall(r"data=(0x[0-9a-fA-F]+)", session.before)
            if cpldID == []:
                print("Failed to find CPLD ID! Read back", session.before)
                common.session_stop(session)
                return -1
            cpldIDs = cpldID[0].upper()

            mtpType = os.environ['MTP_TYPE']

            cmd = "smbutil -uut=uut_{} -dev=cpld_adap -rd -addr=0x80".format(slot)
            common.session_cmd_no_rc(session, cmd)
            match = re.findall(r"Failed", session.before)
            if match:
                sleepTime=3.0
            else:
                sleepTime=6.0

            ret = self.nic_con.uart_session_start(session, self.baud_rate)
            if ret == 0:
                self.nic_con.uart_session_cmd(session, "fsck -y /dev/mmcblk0p10")
                self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data")

                #self.nic_con.uart_session_cmd(session, "cd /data")
                #self.nic_con.uart_session_cmd(session, "cat read_iemode_cmds | capview | grep data")
                #self.nic_con.uart_session_cmd(session, "python ./ie_mode.py")
                #self.nic_con.uart_session_cmd(session, "cat read_iemode_cmds | capview | grep data")
                #self.nic_con.uart_session_cmd(session, "cat read_ddl.txt | capview | grep data")
                #self.nic_con.uart_session_cmd(session, "cat write_ddl.txt | capview")
                #self.nic_con.uart_session_cmd(session, "cat read_ddl.txt | capview | grep data")

                self.nic_con.uart_session_cmd(session, "source /data/nic_arm/nic_setup_env.sh", 120)
                self.nic_con.uart_session_cmd(session, "source /etc/profile", 10)
                #if cpldID[0] == "0x43" or \
                #   cpldID[0] == "0x44" or \
                #   cpldID[0] == "0x45" or \
                #   cpldID[0] == "0x46" or \
                #   cpldID[0] == "0x47" or \
                #   cpldID[0] == "0x49" or \
                #   cpldID[0] == "0x4A":
                if mtpType == "MTP_ELBA" or mtpType == "MTP_TURBO_ELBA":
                    self.nic_con.uart_session_cmd(session, "/data/nic_util/xo3dcpld -w 1 0x0")
                    self.nic_con.uart_session_cmd(session, "/data/nic_util/xo3dcpld -r 1")

                    ## FIXME: Temp hack before new QSPI kick in
                    #if first_pwr_on == True:
                    #    print("Temp FIX: catalog hack!")
                    #    self.nic_con.uart_session_cmd(session, "/data/nic_util/sw/sw_init.sh", 30)
                else:
                    self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -w 1 0xe")
                    self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -r 1")
                self.nic_con.uart_session_cmd(session, "cd /data/nic_arm/nic/asic_src/ip/cosim/tclsh/")
                self.nic_con.uart_session_cmd(session, "export PCIE_ENABLED_PORTS=0")
                self.nic_con.uart_session_cmd(session, "export MTP_REV="+mtp_rev)
                # if this file exists, it means the card is not rebooted
                self.nic_con.uart_session_cmd(session, "touch /root/reboot_check")

                try:
                    if cpldIDs == "0x17" or cpldIDs == "0x19":
                        self.nic_con.turn_off_sgmii(int(slot))
    
                        # enable ports
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -mdiowr 0x4 0x10 0x7f")
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -mdiowr 0x4 0x11 0x7f")
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -mdiowr 0x4 0x13 0x7f")
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -mdiowr 0x4 0x15 0x7f")
                        # power up PHY ports
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -smiwr 0x0 0x3 0x1140")
                        # power up serdes ports
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -smiwr 0x0 0xC 0x1140")
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/cpld -smiwr 0x0 0xD 0x1140")
    
                        self.nic_con.uart_session_cmd(session, "/platform/bin/cpldmon &")
                        sleep(sleepTime)
                        self.nic_con.uart_session_cmd(session, "kill -9 $(pidof cpldmon)")
                except:
                    print("Failed to turn off sgmii")
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    return -1
            else:
                self.nic_con.uart_session_stop(session)
                common.session_stop(session)
                return -1

            self.nic_con.uart_session_stop(session)
            common.session_stop(session)

            if aapl == True:
                ret = self.aapl_setup(self.baud_rate, slot)
                if ret != 0:
                    return ret

            if mgmt == True:
                ret = self.nic_con.get_mgmt_rdy(self.baud_rate, slot, first_pwr_on)

            print "=== Setup env on slot {} env setup done ===".format(slot)

        except pexpect.TIMEOUT:
            print "=== TIMEOUT: Failed to set up env slot {} ===".format(slot)
            ret = -1

        return ret

    def setup_env_multi_top(self, nic_list=[], mgmt=False, timeout=60, first_pwr_on=False, pwr_cycle=True, aapl=False, swm_lp=False, asic_type="capri", uefi=False, dis_net_port=False):
        numRetry = 2
        nic_list_remain = nic_list[:]
        timeout = 60
        for retry in range(numRetry):
            print "Setting up #{}".format(retry)
            print "slot_list", nic_list_remain
            print "timestamp", datetime.datetime.now().time()
            ret, nic_list_remain = self.setup_env_multi(nic_list_remain, mgmt, timeout, first_pwr_on, pwr_cycle, aapl, swm_lp, asic_type, uefi, dis_net_port)
            timeout += retry*10
            if ret == 0:
                break

        if ret != 0:
            print "=== Setup env top failed!", ",".join(nic_list_remain)
        else:
            print "=== Setup env top done #", retry, "==="

        print "timestamp", datetime.datetime.now().time()
        return ret, nic_list_remain

    def setup_env_multi_mainfw(self, nic_list=[], mgmt=False, timeout=30, first_pwr_on=False, pwr_cycle=True, dis_net_port=False):
        ret_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        nic_list_remain = nic_list[:]
        slot_list = ",".join(nic_list)

        if pwr_cycle == True:
            self.nic_con.power_cycle_multi(self.baud_rate, slot_list, 60)

        if mgmt == True:
            for slot in nic_list:
                self.nic_con.switch_console(slot)
                ret = self.nic_con.enable_mnic(self.baud_rate, int(slot), first_pwr_on)
                ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret
            if ret != 0:
                ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret

            for slot in nic_list:
                if ret_list[int(slot)-1] != 0:
                    nic_list.remove(slot)

        if mgmt == True:
            for slot in nic_list:
                if ret_list[int(slot)-1] != 0:
                    continue
                ret = self.nic_con.get_mgmt_rdy(self.baud_rate, int(slot), first_pwr_on, True, dis_net_port)
                if ret != 0:
                    ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret

        for slot_ret in ret_list:
            ret = ret + slot_ret

        if ret != 0:
            print "===  setup_env_multi {} failed; failed slot:", ",".join(nic_list_remain)
        else:
            print "===  setup_env_multi Passed ==="

        print "timestamp", datetime.datetime.now().time()
        return ret, nic_list_remain


    def setup_env_multi(self, nic_list=[], mgmt=False, timeout=30, first_pwr_on=False, pwr_cycle=True, aapl=False, swm_lp=False, asic_type="capri", uefi=False, dis_net_port=False):
        ret_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        nic_list_remain = nic_list[:]
        slot_list = ",".join(nic_list)

        if pwr_cycle == True:
            self.nic_con.power_cycle_multi(self.baud_rate, slot_list, timeout, swm_lp)

        for slot in nic_list:
            ret = self.setup_env(int(slot), False, timeout, False, False, False)
            ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret

        for slot in nic_list:
            if ret_list[int(slot)-1] != 0:
                nic_list.remove(slot)

        if mgmt == True:
            for slot in nic_list:
                self.nic_con.switch_console(slot)
                ret = self.nic_con.enable_mnic(self.baud_rate, int(slot), first_pwr_on)
                ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret

            for slot in nic_list:
                if ret_list[int(slot)-1] != 0:
                    nic_list.remove(slot)

        elif aapl == True and mgmt == False:
            for slot in nic_list:
                self.nic_con.switch_console(slot)

                session = common.session_start()
                ret = self.nic_con.uart_session_start(session)
                if ret != 0:
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    return -1

                self.nic_con.uart_session_cmd(session, "sysinit.sh classic hw diag")

                self.nic_con.uart_session_stop(session)
                common.session_stop(session)

        if mgmt == True or aapl == True:
            if len(nic_list) != 0:
                 print "Sleep 30 sec"
                 time.sleep(30)
            
        if aapl == True:
            for slot in nic_list:
                ret = self.aapl_setup(self.baud_rate, int(slot), True)
                if ret != 0:
                    ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret

        if mgmt == True:
            time.sleep(5)
            for slot in nic_list:
                if ret_list[int(slot)-1] != 0:
                    continue

                self.nic_con.switch_console(slot)
                session = common.session_start()
                ret = self.nic_con.uart_session_start(session)
                if ret != 0:
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret
                    continue

                # Disable link manager
                # Not Pretty..depedning on the f/w version running the command to bring a port to the down state may be different
                try:
                    self.nic_con.uart_session_cmd(session, "halctl debug port --port 1 --admin-state down")
                    self.nic_con.uart_session_cmd(session, "halctl debug port --port 5 --admin-state down")
                    if asic_type == "ELBA":
                        self.nic_con.uart_session_cmd(session, "halctl debug port --admin-state down")
                    #self.nic_con.uart_session_cmd(session, "halctl debug port --port eth1/1 --admin-state down")
                    #self.nic_con.uart_session_cmd(session, "halctl debug port --port eth1/2 --admin-state down")
                    self.nic_con.uart_session_cmd(session, "halctl show port status")
                    if dis_net_port == True:
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/xo3dcpld -smiwr 0 0x3 0x1940")
                        self.nic_con.uart_session_cmd(session, "/data/nic_util/xo3dcpld -smird 0 0x3")
                except:
                    self.nic_con.uart_session_stop(session)
                    common.session_stop(session)
                    ret = -1
                    ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret
                    continue
                
                sleep(0.5)
                self.nic_con.uart_session_stop(session)
                common.session_stop(session)

        if mgmt == True:
            for slot in nic_list:
                if ret_list[int(slot)-1] != 0:
                    continue
                ret = self.nic_con.get_mgmt_rdy(self.baud_rate, int(slot), first_pwr_on, True, asic_type, uefi, dis_net_port)
                if ret != 0:
                    ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret
        for slot in nic_list:
            if ret_list[int(slot)-1] == 0:
                nic_list_remain.remove(slot)

        for slot_ret in ret_list:
            ret = ret + slot_ret

        if ret != 0:
            print "===  setup_env_multi {} failed; failed slot:", ",".join(nic_list_remain)
        else:
            print "===  setup_env_multi Passed ==="

        print "timestamp", datetime.datetime.now().time()
        return ret, nic_list_remain

    def setup_env_multi_goldfw(self, nic_list=[], mgmt=False, timeout=30):
        ret_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        nic_list_remain = nic_list[:]
        slot_list = ",".join(nic_list)

        for slot in nic_list:
            ret = self.nic_con.boot_goldfw_uboot(int(slot))
            #print("ret", ret)
            ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret

        for slot in nic_list:
            if ret_list[int(slot)-1] != 0:
                nic_list.remove(slot)

        if mgmt == True:
            print("sleep 30 sec for goldfw being ready")
            time.sleep(30)
            session = common.session_start()
            for slot in nic_list:
                self.nic_con.switch_console(slot)
                ret = self.nic_con.uart_session_start(session)
                if ret != 0:
                    print("Failed to start uart!")
                    self.nic_con.uart_session_stop(session)
                    ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret
                    continue

                self.nic_con.uart_session_cmd(session, "mkdir -p /data/elba ; mount /dev/mmcblk0p10 /data; mkdir -p /data/elba; cd /data/elba")
                # Calculate IP
                ip_int = 100+int(slot)
                ip = "10.1.1."+str(ip_int)

                for i in range(10):
        	    session.sendline("ifconfig -a")
        	    session.expect("\#")
        	    temp = session.after
        	    if 'oob_mnic0' in session.before:
        	        print 'oob_mnic0 ready'
                        break
                    else:
                        print("Wait for 5 seconds for mnic0 being ready")
                        time.sleep(5)

                self.nic_con.uart_session_cmd(session, "ifconfig oob_mnic0 "+ip+" netmask 255.255.255.0")
                self.nic_con.uart_session_stop(session)
                ret_list[int(slot)-1] = ret_list[int(slot)-1] + ret
            common.session_stop(session)

            for slot in nic_list:
                if ret_list[int(slot)-1] != 0:
                    nic_list.remove(slot)

        for slot_ret in ret_list:
            ret = ret + slot_ret

        if ret != 0:
            print "===  setup_env_multi {} failed; failed slot:", ",".join(nic_list_remain)
        else:
            print "===  setup_env_multi Passed ==="

        print "timestamp", datetime.datetime.now().time()
        return ret, nic_list_remain

    def aapl_setup(self, rate, slot=0, skip=False):
        numRetry = 3
        ret = -1
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            return -1

        self.nic_con.switch_console(slot)

        session = common.session_start()
        ret = self.nic_con.uart_session_start(session)
        if ret != 0:
            print "=== AAPL setup failed; slot {} ===".format(slot)
            self.nic_con.uart_session_stop(session)
            common.session_stop(session)
            return ret

        if skip == False:
            self.nic_con.uart_session_cmd(session, "sysinit.sh classic hw diag")
            print "Sleep 30 sec"
            time.sleep(30)

            # Disable link manager
            # Not Pretty..depedning on the f/w version running the command to bring a port to the down state may be different
            try:
                self.nic_con.uart_session_cmd(session, "halctl debug port --port 1 --admin-state down")
                self.nic_con.uart_session_cmd(session, "halctl debug port --port 5 --admin-state down")
                #self.nic_con.uart_session_cmd(session, "halctl debug port --port eth1/1 --admin-state down")
                #self.nic_con.uart_session_cmd(session, "halctl debug port --port eth1/2 --admin-state down")
                sleep(0.5)
            except:
                 self.nic_con.uart_session_stop(session)
                 common.session_stop(session)
                 return -1


        self.nic_con.uart_session_cmd(session, "halctl debug port aacs-server-start --server-port 9000")
        sleep(2)
        for i in range(numRetry):
            try:
                # PRBS init
                session.sendline("/data/nic_arm/aapl/aapl_prbs_all.sh PCIE RESET")
                session.expect("AAPL OP DONE")
                time.sleep(5)

                session.sendline("/data/nic_arm/aapl/aapl_prbs_all.sh PCIE INIT")
                session.expect("AAPL OP DONE")
                if "ERROR" in session.before or "WARNING" in session.before:
                    ret = -1
                    continue
                else:
                    ret = 0
                    break

            except pexpect.TIMEOUT:
                print "=== TIMEOUT: Failed to set up AAPL ==="
                ret = -1
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
            ret = self.setup_env(slot, False, 30)
            if ret != 0:
                print "=== Power cycle test failed at ite {} ===".format(i)
                break

        if ret == 0:
            print "=== Power cycle test passed {} iterations ===".format(iteration)
        return ret

    def pwr_cycle_test_multi(self, nic_list=[], iteration=1, pc_mode="board"):
        ret = 0

        if pc_mode != "board":
            nic_list_str = ",".join(nic_list)
            self.nic_con.power_cycle_multi(self.baud_rate, nic_list_str, 60)

        for i in range(iteration):
            print "=== Ite {} ===".format(i)
            if pc_mode == "board":
                ret, _ = self.setup_env_multi(nic_list, False, 60)
            else:
                ret, _ = self.setup_env_multi(nic_list, False, 60, pwr_cycle=False)

            if ret != 0:
                print "=== Power cycle test failed at ite {} ===".format(i)
                break

            if pc_mode != "board":
                print("=== sysreset ===")
                session = common.session_start()
                self.nic_con.uart_session_start(session)
                self.nic_con.uart_session_cmd(session, "ls -l")
                self.nic_con.uart_session_cmd(session, "sysreset.sh", ending=["Restarting system", "Boot0"])
                self.nic_con.uart_session_stop(session)
                session = common.session_stop(session)
                time.sleep(10)

        if ret == 0:
            print "=== Power cycle test passed {} iterations ===".format(iteration)
        return ret

    def test_start(self, slot=0, test_type="snake", mode="hbm", timeout=30, vmarg=0, pc="off", dura=120, in_lpbk=False, snake_num=6):
        print "=== Starting {} on slot {} ===".format(test_type, slot)

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        int_lpbk_str = ""
        if in_lpbk == True:
            int_lpbk_str = "-int_lpbk"

        if test_type == "snake" and mode == "hbm":
            test_cmd = "/data/nic_util/asicutil -snake -mode hbm_lb 2>&1 >  /data/nic_util/asicutil_hbm.log &"
        elif test_type == "snake" and mode == "pcie":
            test_cmd = "/data/nic_util/asicutil -snake -mode pcie_lb 2>&1 > /data/nic_util/asicutil_pcie.log &"
        elif (test_type == "snake" and ("nod" in mode)) or (test_type == "snake" and ("hod" in mode) ):
            test_cmd = "/data/nic_util/asicutil -snake -mode {} -dura {} {} -snake_num {} 2>&1 > /data/nic_util/asicutil_elba.log &".format(mode, dura, int_lpbk_str, snake_num)
            print("test_cmd", test_cmd)
        elif test_type == "prbs" and mode == "eth":
            test_cmd = "/data/nic_util/asicutil -prbs -mode ETH -dura {} {} 2>&1 > /data/nic_util/asicutil_elba_prbs_eth.log &".format(dura, int_lpbk_str)
            print("test_cmd", test_cmd)
        else:
            print "Invalid test_type {} and mode {}".format(test_type, mode)
            sys.exit(0)

        if pc == "on":
            self.nic_con.power_cycle_uart(self.baud_rate, slot)

        session = common.session_start()
        try:
            session.timeout = timeout
            self.nic_con.uart_session_start_slot(session, self.baud_rate, slot)
            if vmarg > 0:
                self.nic_con.uart_session_cmd(session, "/data/nic_arm/vmarg.sh high")
            elif vmarg < 0:
                self.nic_con.uart_session_cmd(session, "/data/nic_arm/vmarg.sh low")
            else:
                pass

            session.sendline(test_cmd)
            session.sendline("\r")

            self.nic_con.uart_session_stop(session)

            print "=== {} on slot {} started ===".format(test_type, slot)
        except:
            self.nic_con.uart_session_stop(session)
            print "=== {} on slot {} FAILED to start! ===".format(test_type, slot)
            common.session_stop(session)
            ret = -1

        common.session_stop(session)
        return ret

    def test_check(self, slot=0, test_type="snake", mode="hbm", timeout=30):
        print "=== Checking {} result on slot {} ===".format(test_type, slot)

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        self.nic_con.switch_console(slot)
        session = common.session_start()
        ret = self.nic_con.uart_session_start(session)
        if ret != 0:
            self.nic_con.uart_session_stop(session)
            common.session_stop(session)
            return -1

        if test_type == "snake":
            if mode == "hbm":
                 test_mode= "hbm_lb"
            else:
                 test_mode= "pcie_lb"

        if test_type == "prbs" and mode == "eth":
            cmd = "/data/nic_util/asicutil -prbs_chk"
        else:
            cmd = "/data/nic_util/asicutil -snake_chk"

        if test_type == "snake":
            session.sendline("tail -5 /data/nic_arm/nic/asic_src/ip/cosim/tclsh/snake_elba.log")

        ret = self.nic_con.uart_session_cmd_sig(session, cmd, 15, "\#", ["SUCCESS", "FAIL", "RUNNING"], False)
        self.nic_con.uart_session_cmd(session, "sync", 15)
        self.nic_con.uart_session_stop(session)

        common.session_stop(session)

        print "check_result:", ret
        print "=== Checing {} result on slot {} Done ===".format(test_type, slot)
        return ret

    def test_check_ddr(self, slot=0):
        print "=== Checking {} on slot {} ===".format("DDR setting", slot)

        ret = 0
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)

        self.nic_con.switch_console(slot)
        session = common.session_start()
        ret = self.nic_con.uart_session_start(session)
        if ret != 0:
            self.nic_con.uart_session_stop(session)
            common.session_stop(session)
            return -1

        try:
            self.nic_con.uart_session_cmd(session, "cd /data/nic_arm/nic/asic_src/ip/cosim/tclsh")
            self.nic_con.uart_session_cmd(session, "./diag.exe ../elba/elb_arm_check_ddr.tcl")
        except:
            print("Failed to retrieve DDR info")

        self.nic_con.uart_session_stop(session)

        common.session_stop(session)

        print "=== Checking {} on slot {} Done ===".format("DDR setting", slot)
        return ret

    def mtp_sts(self, wait_time, interval=15):
        session = common.session_start()
        print("=== Displaying MTP status ===", wait_time)
        for time_e in range(0, wait_time, interval):
            print("=== time", time_e, "===")
            common.session_cmd(session, "devmgr -status")
            time.sleep(interval)
            

    def nic_test(self, nic_list=[], test_type="snake", mode="hbm", wait_time=180, vmargin=0, duration=120, int_lpbk=False, snake_num=6, disp_si=False):
        print "=== NIC {} {} ===".format(test_type, mode)
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        #slot_list = ",".join(nic_list)
        print "slot_list:", slot_list
        #self.nic_con.power_cycle_multi(self.baud_rate, slot_list)
        self.setup_env_multi_top(slot_list, False, 30, False, True, False)

        test_result = OrderedDict()
        # Start snake
        for slot in nic_list:
            ret = self.test_start(int(slot), test_type, mode, vmarg=vmargin, pc="off", dura=duration, in_lpbk=int_lpbk, snake_num=snake_num)
            if ret != 0:
                test_result[slot] = "FAIL"
            else:
                test_result[slot] = "NO RESULT"

        print "Wait for {}s before checking result".format(wait_time)
        self.mtp_sts(wait_time)

        done_count = 0
        for retry_idx in range(self.num_retry):
            print "Checking result:", retry_idx
            for slot in nic_list:
                if test_result[slot] != "NO RESULT":
                    continue

                test_sts = self.test_check(int(slot), test_type, mode)
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

        if disp_si == True:
            for slot in nic_list:
                print("======================================")
                print("Checking DDR setting")
                print("======================================")
                ret = self.test_check_ddr(int(slot))

        # Print result
        print "\n====== TEST RESULT: {:<5} {:<5} ======".format(test_type.upper(), mode.upper())
        result_fmt = "Slot {:<2}: {:<5}"
        for slot, sts in test_result.items():
            print result_fmt.format(slot, sts)
        print "======================================"

    def disp_ecc(self, nic_list=[]):
        print("=== Collect ECC info ===")
        slot_list = ",".join(nic_list)
        print("slot_list:", slot_list)

        session = common.session_start()
        try:
            ret, output = common.session_cmd_w_ot(session, "tclsh /home/diag/diag/scripts/asic/read_ecc_reg.tcl "+slot_list, 60, ending="ECC COLLECTION DONE")
            p = re.compile(r'.*ECC COLLECTION RESULT (.*) Done.*', re.DOTALL)
            m = p.match(output)
            if m:
                rets = m.group(1)
            else:
                print("Failed to retrief ECC result!")
                return
            print(rets)
        except pexpect.TIMEOUT:
            print("Failed to connect ECC info")
        common.session_stop(session)

    def ena_dis_uboot_pcie(self, nic_list=[], enable=True):
        ret_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        nic_list_remain = nic_list[:]

        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        for retry in range(self.num_retry):
            print "Trying break into uboot {}".format(retry)
            for slot in nic_list_remain:
                self.nic_con.power_cycle_multi(self.baud_rate, int(slot), 0)
            print "Wait for 60 seconds before entering uboot"
            sleep(60)
            for slot in nic_list_remain:
                if enable == True:
                    ret = self.nic_con.enable_pcie_uboot(int(slot))
                else:
                    ret = self.nic_con.disable_pcie_uboot(int(slot))
                ret_list[int(slot)-1] = ret

            for slot in nic_list_remain:
                if ret_list[int(slot)-1] == 0:
                    nic_list.remove(slot)

            print "remaining slots: ", ",".join(nic_list)
            nic_list_remain = nic_list[:]

            if len(nic_list) == 0:
                break

        if len(nic_list) != 0:
            print "=== ena_dis_uboot_pcie failed; failed slots: ", ",".join(nic_list)
        else:
            print "=== ena_dis_uboot_pcie passed ==="
        print "=== ena_dis_uboot_pcie done #", retry, "==="


    def ena_dis_esec_wp(self, nic_list=[], enable=True):
        ret_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        nic_list_remain = nic_list[:]

        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        for retry in range(self.num_retry):
            print "Trying break into uboot {}".format(retry)
            for slot in nic_list_remain:
                self.nic_con.power_cycle_multi(self.baud_rate, int(slot), 0)
            print "Wait for 60 seconds before entering uboot"
            sleep(60)
            for slot in nic_list_remain:
                ret = self.nic_con.ena_dis_esec_wp(int(slot), enable)
                ret_list[int(slot)-1] = ret

            for slot in nic_list_remain:
                if ret_list[int(slot)-1] == 0:
                    nic_list.remove(slot)

            print "remaining slots: ", ",".join(nic_list)
            nic_list_remain = nic_list[:]

            if len(nic_list) == 0:
                break

        if len(nic_list) != 0:
            print "=== ena_dis_esec_wp failed; failed slots: ", ",".join(nic_list)
        else:
            print "=== ena_dis_esec_wp passed ==="
        print "=== ena_dis_esec_wp done #", retry, "==="

    def vrd_fault_line(self, nic_list=[]):
        ret_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        print "slot_list:", slot_list
        self.setup_env_multi_top(slot_list, False, 30, False, True, False)

        for slot in nic_list:
            session = common.session_start()
            ret = self.nic_con.uart_session_start(session)
            if ret != 0:
                print("Connecting to console failed!")
            else:
                session.sendline("/data/nic_util/devmgr -dev=ELB0_ARM -vrFault")
                time.sleep(3)
                self.nic_con.uart_session_stop(session)
            # on MTP, smb read register 0x50 bit 2
            cmd = "smbutil -uut=uut_{} -dev=cpld -rd -addr=0x50".format(slot)
            common.session_cmd(session, cmd)
            match = re.search(r'data=(0x[a-fA-F0-9]+)', session.before)
            if match:
                if int(match.group(1), 16) & 0x4 == 0x4:
                    ret_list[int(slot)-1] = 1
            else:
                print "Failed to read CPLD addr=0x50 for slot {}".format(slot)

        for slot in nic_list:
            if ret_list[int(slot)-1] == 1:
                nic_list.remove(slot)

        if len(nic_list) != 0:
            print "=== vrd_fault_line failed; failed slots: ", ",".join(nic_list)
        else:
            print "=== vrd_fault_line passed ==="
        print "=== vrd_fault_line done ==="

    def therm_alert_line(self, nic_list=[]):
        ret_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        print "slot_list:", slot_list

        for slot in nic_list:
            intr_set = 0
            intr_cleared = 0
            session = common.session_start()
            ret = self.nic_con.uart_session_start(session)
            if ret != 0:
                print("Connecting to console failed!")
            else:
                # trigger the therm alert
                self.nic_con.uart_session_cmd(session, "/data/nic_util/devmgr -dev=TSENSOR -thermAlert")
                # enable the temp warning interrupt
                self.nic_con.uart_session_cmd(session, "/data/nic_util/xo3dcpld -w 0x3 0x20")
                # read the status of the temp warning interrupt to make sure it's set
                for retry in range(10):
                    self.nic_con.uart_session_cmd(session, "/data/nic_util/xo3dcpld -r 4")
                    match = re.search(r'(0x[a-fA-F0-9]+)', session.before)
                    if match:
                        if int(match.group(1), 16) & 0x20 == 0x20:
                            intr_set = 1
                            break
                    else:
                        print "Failed to read CPLD addr=0x4 for slot {}".format(slot)
                    time.sleep(1)
                # restore the temp limit
                self.nic_con.uart_session_cmd(session, "/data/nic_util/devmgr -dev=TSENSOR -restoreLimit")
                # enable the temp warning interrupt
                self.nic_con.uart_session_cmd(session, "/data/nic_util/xo3dcpld -w 0x3 0x20")
                # read the status of the temp warning interrupt to make sure it's cleared
                for retry in range(10):
                    self.nic_con.uart_session_cmd(session, "/data/nic_util/xo3dcpld -r 4")
                    match = re.search(r'(0x[a-fA-F0-9]+)', session.before)
                    if match:
                        if int(match.group(1), 16) & 0x20 == 0x0:
                            intr_cleared = 1
                            break
                    else:
                        print "Failed to read CPLD addr=0x4 for slot {}".format(slot)
                    time.sleep(1)
                # disable the temp waring interrupt
                self.nic_con.uart_session_cmd(session, "/data/nic_util/xo3dcpld -w 0x3 0x0")
                self.nic_con.uart_session_stop(session)
                if intr_set == 1 and intr_cleared == 1:
                    ret_list[int(slot)-1] = 1

        for slot in nic_list:
            if ret_list[int(slot)-1] == 1:
                nic_list.remove(slot)

        if len(nic_list) != 0:
            print "=== therm_alert_line failed; failed slots: ", ",".join(nic_list)
        else:
            print "=== therm_alert_line passed ==="
        print "=== therm_alert_line done ==="

    def therm_trip_line(self, nic_list=[]):
        ret_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        print "slot_list:", slot_list
        self.setup_env_multi_top(slot_list, False, 30, False, True, False)

        for slot in nic_list:
            session = common.session_start()
            ret = self.nic_con.uart_session_start(session)
            if ret != 0:
                print("Connecting to console failed!")
            else:
                session.sendline("/data/nic_util/devmgr -dev=TSENSOR -thermTrip")
                time.sleep(3)
                self.nic_con.uart_session_stop(session)
            # on MTP, smb read register 0x50 bit 3
            cmd = "smbutil -uut=uut_{} -dev=cpld -rd -addr=0x50".format(slot)
            common.session_cmd(session, cmd)
            match = re.search(r'data=(0x[a-fA-F0-9]+)', session.before)
            if match:
                if int(match.group(1), 16) & 0x8 == 0x8:
                    ret_list[int(slot)-1] = 1
            else:
                print "Failed to read CPLD addr=0x50 for slot {}".format(slot)

        for slot in nic_list:
            if ret_list[int(slot)-1] == 1:
                nic_list.remove(slot)

        if len(nic_list) != 0:
            print "=== therm_trip_line failed; failed slots: ", ",".join(nic_list)
        else:
            print "=== therm_trip_line passed ==="
        print "=== therm_trip_line done ==="

    def config_ddr(self, nic_list=[], hardcode=False, speed=3200):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        slot_list = ",".join(nic_list)
        print "slot_list:", slot_list

        for slot in nic_list:
            ret = self.nic_con.config_ddr(int(slot), hardcode, speed)

            if ret != 0:
                print "=== Failed to change uboot PCIe setting at slot {} ===".format(slot)

    def setup_uboot_env(self, nic_list=[]):
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        slot_list = ",".join(nic_list)
        print "slot_list:", slot_list

        for slot in nic_list:
            ret = self.nic_con.setup_uboot_env(int(slot))

            if ret != 0:
                print "=== Failed to setup uboot env at slot {} ===".format(slot)

    def nic_test1(self, nic_list=[], test_type="snake", mode="hbm", wait_time=180, vmargin=0):
        print "=== NIC {} {} ===".format(test_type, mode)
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        # Initialization
        test_result = OrderedDict()
        for slot in nic_list:
            test_result[slot] = "NO RESULT"

        ret, nic_test_remain = self.setup_env_multi_top(nic_list, False, 30, False, True, False)

        for slot in nic_list_remain:
            test_result[slot] = "FAIL"
            nic_list.remove(slot)

        print "NIC list after init:", nic_list

        # Start snake
        for slot in nic_list:
            ret = self.test_start(int(slot), test_type, mode, vmarg=vmargin, pc="off")
            if ret != 0:
                test_result[slot] = "FAIL"
                nic_list.remove(slot)

        print "NIC list after test start:", nic_list

        print "Wait for {}s before checking result".format(wait_time)
        time.sleep(wait_time)

        done_count = 0
        for retry_idx in range(self.num_retry):
            print "Checking result:", retry_idx
            for slot in nic_list:
                if test_result[slot] != "NO RESULT":
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


    def timeout_test(self, timeout):
        session = common.session_start()
        common.session_cmd(session, "ping hw-srv1", timeout)
        common.session_stop(session)

    def set_mtp_fan_speed(self, fan_speed):
        mtp_session = common.session_start()
        fan_cmd_fmt = "devmgr -dev=fan -speed -pct={}"
        common.session_cmd(mtp_session, fan_cmd_fmt.format(fan_speed))
        time.sleep(3)
        common.session_cmd(mtp_session, "devmgr -dev=fan -status")

        common.session_stop(mtp_session)

    def die_temp_ctrl(self, tgt_die_temp, init_speed, buf):
        # Fan control session
        fan_cmd_fmt = "devmgr -dev=fan -speed -pct={}"

        fan_speed = init_speed
        print("tgt_die_temp:", tgt_die_temp, "init_speed:", init_speed)

        mtp_session = common.session_start()
        common.session_cmd(mtp_session, "devmgr -dev=fan -status")

        #p = re.compile(r'.*elb_get_temp :: temp:([\d]+\.[\d]+).*', re.DOTALL)
        p = re.compile(r'.*TEMP:[\d]+\.[\d]+/[\d]+\.[\d]+/([\d]+\.[\d]+).*', re.DOTALL)

        m = p.match(buf)
        if m:
            cur_temp = m.group(1)

            temp_diff = tgt_die_temp - float(cur_temp)
            temp_diff = math.copysign(1, temp_diff) * (min(abs(temp_diff), 10))

            fan_speed = fan_speed - temp_diff
            fan_speed = max(fan_speed, 40)
            fan_speed = min(fan_speed, 100)
            fan_speed = int(fan_speed)

            print("Die Temp:", cur_temp, "tgt_temp:", tgt_die_temp, "fan_speed:", fan_speed)
            common.session_cmd(mtp_session, fan_cmd_fmt.format(fan_speed))
            time.sleep(3)
            common.session_cmd(mtp_session, "devmgr -dev=fan -status")
        else:
            print("Failed to retried die temp")

        common.session_stop(mtp_session)
        return fan_speed

    def skew_test(self, nic_list=[], fan_ctrl=False, tgt_die_temp=80):
        print "=== NIC Skew Test ==="
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        slot_list = ",".join(nic_list)
        print("slot_list:", slot_list)
#        self.nic_con.power_cycle_multi(self.baud_rate, slot_list, 1)

        print("fan_ctrl:", fan_ctrl, "tgt_die_temp:", tgt_die_temp)
        if fan_ctrl == False:
            fan_speed = 100
        else:
            fan_speed = 60
        self.set_mtp_fan_speed(fan_speed)

        session = common.session_start()

        #for slot in nic_list:
        #    cmd = "turn_on_hub.sh {}; i2cset -y 0 0x4a 0x21 0x15".format(slot)
        #    common.session_cmd(session, cmd)
#        print("Wait 60 sec for cards booting up")
#        time.sleep(60)

        card_info_dict = dict()
        card_info_dict['1'] = "SLOT01"
        card_info_dict['2'] = "SLOT02"
        card_info_dict['3'] = "SLOT03"
        card_info_dict['4'] = "SLOT04"
        card_info_dict['5'] = "SLOT05"
        card_info_dict['6'] = "SLOT06"
        card_info_dict['7'] = "SLOT07"
        card_info_dict['8'] = "SLOT08"
        card_info_dict['9'] = "SLOT09"

        # Manul change here
        core_freq = 1033
        arm_freq = 3000
        core_volt = "xxx"
        arm_volt = "xxx"
        volt_mode = "hod"
        chamber_temp = "0_temp_ctrl_{}".format(tgt_die_temp)

        test_result = OrderedDict()
        # Start snake
        for slot in nic_list:
            card_no = card_info_dict[slot]

            self.nic_con.switch_console(slot)

            try:
                ret = self.nic_con.uart_session_start(session)
                if ret != 0:
                    print("Faied to enter uart session")
#                self.nic_con.uart_session_cmd(session, "mount /dev/mmcblk0p10 /data")
#                self.nic_con.uart_session_cmd(session, "export CARD_TYPE=ORTANO2")
                self.nic_con.uart_session_cmd(session, "/data/devmgr -status")

                self.nic_con.uart_session_cmd(session, "/data/smbutil -dev=ELB0_CORE -addr=0x0 -mode b -wr -data=0xFF")
                self.nic_con.uart_session_cmd(session, "/data/smbutil -dev=ELB0_CORE -addr=0x0 -mode b -rd")

                self.nic_con.uart_session_cmd(session, "/data/smbutil -dev=ELB0_CORE -addr=0x4f -mode w -wr -data=0x8C")
                self.nic_con.uart_session_cmd(session, "/data/smbutil -dev=ELB0_CORE -addr=0x51 -mode w -wr -data=0x87")

                self.nic_con.uart_session_cmd(session, "/data/smbutil -dev=ELB0_CORE -addr=0x4f -mode w -rd")
                self.nic_con.uart_session_cmd(session, "/data/smbutil -dev=ELB0_CORE -addr=0x51 -mode w -rd")

                self.set_mtp_fan_speed(60)
#
#                self.nic_con.uart_session_cmd(session, "cd /data/nic_arm/nic")
#                self.nic_con.uart_session_cmd(session, "export ASIC_LIB_BUNDLE=`pwd`")
#                self.nic_con.uart_session_cmd(session, "export ASIC_SRC=$ASIC_LIB_BUNDLE/asic_src")
#                self.nic_con.uart_session_cmd(session, "source $ASIC_LIB_BUNDLE/asic_lib/source_env_path")
                self.nic_con.uart_session_cmd(session, "cd $ASIC_SRC/ip/cosim/tclsh")

                # TCL commands
                self.nic_con.uart_session_cmd(session, "$ASIC_LIB_BUNDLE/asic_lib/diag.exe", 60, "%")
                self.nic_con.uart_session_cmd(session, "source .tclrc.diag.elb.arm", 60, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set ::env(CARD_ENV) ARM", 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set ::env(CARD_TYPE) ORTANO", 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set ::env(MTP_REV) REV_4", 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "elb_appl_set_srds_int_timeout  5000", 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "sleep 1", 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set die_temp [elb_get_temp]", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set core_freq [get_freq]", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set arm_freq [elb_top_sbus_get_cpu_freq  0 0]", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, 'plog_msg "die_temp $die_temp; core_freq $core_freq; arm_freq $arm_freq"', 30, "tclsh]")

                self.nic_con.uart_session_cmd(session, "set core_freq {}.0".format(core_freq), 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set arm_freq {}".format(arm_freq), 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set core_volt {}".format(core_volt), 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set arm_volt {}".format(arm_volt), 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set volt_mode {}".format(volt_mode), 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set core_freq1 [elb_core_freq_for_mode $volt_mode]", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set stg_freq  [elb_stg_freq_for_mode $volt_mode]", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set eth_freq  900", 10, "tclsh]")
                self.nic_con.uart_session_cmd(session, "elb_set_freq $core_freq1", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "elb_soc_stg_pll_init 0 0 $stg_freq", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "elb_mm_eth_pll_init  0 0 $eth_freq", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "elb_top_sbus_cpu_${arm_freq} 0 0", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "get_freq", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "elb_top_sbus_get_cpu_freq  0 0", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set card_no {}".format(card_info_dict[slot]), 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set chamber_temp {}".format(chamber_temp), 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set card_config core_freq_${core_freq}_arm_freq_${arm_freq}_core_volt_${core_volt}_arm_volt_${arm_volt}_chamber_${chamber_temp}", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "puts $card_config", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "set duration 120", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "plog_start hbm_pktgen_pcie_lb_100g_${card_no}_${card_config}.log", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "plog_file_to_flag_set 3", 30, "tclsh]")
                #self.nic_con.uart_session_cmd(session, "elb_snake_test_mtp 6 4096 0 1 {}.0 1 $duration".format(core_freq), 30, "parseKnobFile")
                if fan_ctrl == False:
                    self.nic_con.uart_session_cmd(session, "elb_snake_test_mtp 6 4096 1 1 {}.0 1 $duration".format(core_freq), 2400, "SNAKE DONE")
                else:
                    cmd = "elb_snake_test_mtp 6 4096 1 1 {}.0 1 $duration".format(core_freq)
                    expstr = ["SNAKE DONE", "Done Pulling"]
                    timeout = 1200
                    session.sendline(cmd)

                    while True:
                        i = session.expect(expstr, timeout)
                        print("=== i:", i)
                        if i == 0:
                            break
                        else:
                            timeout = 900
                            i = session.expect(expstr, timeout)
                            print("==== FOUND PULL ====")
                            #common.session_cmd(mtp_session, "devmgr -dev=fan -status")
                            #m = p.match(session.before)
                            #if m:
                            #    temp = m.group(1)
                            #    print("Die Temp:", temp)
                            #else:
                            #    print("Failed to retried die temp")
                            if i == 1:
                                fan_speed = self.die_temp_ctrl(tgt_die_temp, fan_speed, session.before)
                            session.send("temp ")

                self.nic_con.uart_session_cmd(session, "puts 'xxx'", 300, "tclsh]")
                self.nic_con.uart_session_cmd(session, "plog_stop", 30, "tclsh]")
                self.nic_con.uart_session_cmd(session, "exit", 120)
                self.nic_con.uart_session_cmd(session, "sync", 30)
                self.nic_con.uart_session_cmd(session, "sync", 30)

                self.nic_con.uart_session_stop(session)
                test_result[slot] = "PASS"
            except pexpect.TIMEOUT:
                print(slot, "skew test failed")
                test_result[slot] = "FAIL"
                self.nic_con.uart_session_stop(session)

        #common.session_stop(mtp_session)
        common.session_stop(session)

        result_fmt = "Slot {:<2}: {:<5}"
        print "\n====== TEST RESULT: {:<5} {:<5} ======".format("SLOT", "RESULT")
        for slot, result in test_result.items():
            print result_fmt.format(slot, result)

    def skew_test_exit(self, nic_list=[]):

        slot_list = ",".join(nic_list)

        session = common.session_start()
        cmd = self.nic_con.fmt_con_cmd.format(self.baud_rate)
        session.sendline(cmd)

        # Quite tcl shell
        for slot in nic_list:
            self.nic_con.switch_console(slot)
            try:
                ret = self.nic_con.uart_session_cmd(session, "puts 'xxx'", 3, "%")
                if ret != 0:
                    print("Slot", slot, "Still running")
                    continue
                self.nic_con.uart_session_cmd(session, "plog_stop", 30, "%")
                self.nic_con.uart_session_cmd(session, "exit", 120)
                self.nic_con.uart_session_cmd(session, "sync", 30)
                self.nic_con.uart_session_cmd(session, "sync", 30)

            except pexpect.TIMEOUT:
                print("Slot", slot, "TIMEOUT")

        self.nic_con.uart_session_stop(session)
        common.session_stop(session)

    def emmc_test(self, nic_list=[], num_ite=1):
        print "=== NIC eMMC Test ==="
        if len(nic_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        fan_speed = 50
        self.set_mtp_fan_speed(fan_speed)

        for ite in range(num_ite):
            print("=== Ite:", ite, "===")
            slot_list = ",".join(nic_list)
            print("slot_list:", slot_list)
            self.nic_con.power_cycle_multi(self.baud_rate, slot_list, 1)

            session = common.session_start()

            #for slot in nic_list:
            #    cmd = "turn_on_hub.sh {}; i2cset -y 0 0x4a 0x21 0x15".format(slot)
            #    common.session_cmd(session, cmd)
            print("Wait 60 sec for cards booting up")
            time.sleep(60)

            core_volt=750
            arm_volt=860
            core_freq = 833
            arm_freq = 2000
            volt_mode = "nod"

            for slot in nic_list:
                common.session_cmd(session, "cd $ASIC_SRC/ip/cosim/tclsh")

                # TCL command
                common.session_cmd(session, "tclsh", 20, False, "%")
                common.session_cmd(session, "source .tclrc.diag.elb", 60, False, "tclsh]")

                try:
                    common.session_cmd(session, "diag_open_j2c_if 10 "+slot, 10, False, "tclsh]")
                    common.session_cmd(session, "elb_get_vout arm", 30, False, "tclsh]")
                    common.session_cmd(session, "elb_get_vout vdd", 30, False, "tclsh]")
                    common.session_cmd(session, "elb_appl_set_srds_int_timeout  5000", 10, False, "tclsh]")
                    common.session_cmd(session, "sleep 1", 10, False, "tclsh]")
                    common.session_cmd(session, "set die_temp [elb_get_temp]", 30, False, "tclsh]")
                    common.session_cmd(session, "set core_freq [get_freq]", 30, False, "tclsh]")
                    common.session_cmd(session, "set arm_freq [elb_top_sbus_get_cpu_freq  0 0]", 30, False, "tclsh]")
                    common.session_cmd(session, 'plog_msg "die_temp $die_temp; core_freq $core_freq; arm_freq $arm_freq"', 30, False, "tclsh]")

                    common.session_cmd(session, "set core_freq {}.0".format(core_freq), 10, False, "tclsh]")
                    common.session_cmd(session, "set arm_freq {}".format(arm_freq), 10, False, "tclsh]")
                    common.session_cmd(session, "set core_volt {}".format(core_volt), 10, False, "tclsh]")
                    common.session_cmd(session, "set arm_volt {}".format(arm_volt), 10, False, "tclsh]")
                    common.session_cmd(session, "set volt_mode {}".format(volt_mode), 10, False, "tclsh]")
                    common.session_cmd(session, "set core_freq1 [elb_core_freq_for_mode $volt_mode]", 30, False, "tclsh]")
                    common.session_cmd(session, "set stg_freq  [elb_stg_freq_for_mode $volt_mode]", 30, False, "tclsh]")
                    common.session_cmd(session, "set eth_freq  900", 10, False, "tclsh]")
                    common.session_cmd(session, "elb_set_freq $core_freq1", 30, False, "tclsh]")
                    common.session_cmd(session, "elb_soc_stg_pll_init 0 0 $stg_freq", 30, False, "tclsh]")
                    common.session_cmd(session, "elb_mm_eth_pll_init  0 0 $eth_freq", 30, False, "tclsh]")
                    common.session_cmd(session, "elb_top_sbus_cpu_${arm_freq} 0 0", 120, False, "tclsh]")
                    common.session_cmd(session, "get_freq", 30, False, "tclsh]")
                    common.session_cmd(session, "elb_top_sbus_get_cpu_freq  0 0", 60, False, "tclsh]")
                    common.session_cmd(session, "diag_close_j2c_if 10 "+slot, 10, False, "tclsh]")
                    common.session_cmd(session, "exit", 11)

                except pexpect.TIMEOUT:
                    print(slot, "eMMC test failed")
                    common.session_stop(session)
                    return
            common.session_stop(session)


            print("Wait for 10 sec after freq change")
            time.sleep(10)

            session = common.session_start()
            for slot in nic_list:
                self.nic_con.switch_console(slot)
                try:
                    ret = self.nic_con.uart_session_start(session)
                    if ret != 0:
                        print("Faied to enter uart session")

                    session.sendline("mkdir -p /data/elba ; mount /dev/mmcblk0p10 /data; mkdir -p /data/elba; cd /data/elba")
                    session.expect("\#")
                    if "superblock" in session.before:
                        print("Super Block is bad!")
                        self.nic_con.uart_session_stop(session)
                        common.session_stop(session)
                        return

                    self.nic_con.uart_session_cmd(session, "sync")
                    self.nic_con.uart_session_stop(session)
                except pexpect.TIMEOUT:
                    print(slot, "NIC console timeout")
                    self.nic_con.session_stop(session)
                    return

            common.session_stop(session)

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
    group.add_argument("-pct_multi", "--pwr_cycle_test_multi", help="Power cycle test on multiple slots", action='store_true')

    group.add_argument("-ena_uboot_pcie", 
                       "--ena_uboot_pcie", 
                       help="Enable uboot PCIe for mutiple cards", 
                       action='store_true')
    group.add_argument("-dis_uboot_pcie", 
                       "--dis_uboot_pcie", 
                       help="Disable uboot PCIe for mutiple cards", 
                       action='store_true')
    group.add_argument("-ena_esec_wp",
                       "--ena_esec_wp",
                       help="Enable QSPI WP for mutiple cards",
                       action='store_true')
    group.add_argument("-dis_esec_wp",
                       "--dis_esec_wp",
                       help="Disable QSPI WP for mutiple cards",
                       action='store_true')
    group.add_argument("-setup_uboot_env", 
                       "--setup_uboot_env", 
                       help="Setup uboot evn variable for mutiple cards", 
                       action='store_true')
    group.add_argument("-test_t", "--test_timeout", help="Test timeout", action='store_true')
    group.add_argument("-skew", "--skew", help="Run nic skew test on multile nics", action='store_true')
    group.add_argument("-skew_exit", "--skew_exit", help="End nic skew test on multile nics", action='store_true')
    group.add_argument("-emmc", "--emmc", help="Run nic emmc test on multile nics", action='store_true')
    group.add_argument("-fix_bx", "--fix_bx", help="UART cpl file", action='store_true')
    group.add_argument("-config_ddr", "--config_ddr", help="configure DDR", action='store_true')
    group.add_argument("-disp_ecc", "--disp_ecc", help="Display ECC syndrom", action='store_true')
    group.add_argument("-vrd_fault_line", "--vrd_fault_line", help="Test VRD_FAULT line", action='store_true')
    group.add_argument("-therm_alert_line", "--therm_alert_line", help="Test Temp Sensor Alert line", action='store_true')
    group.add_argument("-therm_trip_line", "--therm_trip_line", help="Test Temp Sensor Trip line", action='store_true')

    parser.add_argument("-slot", "--slot", help="NIC slot number", type=int, default=0)
    parser.add_argument("-slot_list", "--slot_list", help="NIC slot list", type=str, default="")
    parser.add_argument("-wtime", "--wait_time", help="Wait time", type=int, default=180)
    parser.add_argument("-mgmt", "--mgmt", help="Set up management port", action='store_true')
    parser.add_argument("-mode", "--mode", help="Test mode: pcie/hbm; prbs: pcie/eth", type=str, default="hbm")
    parser.add_argument("-vmarg", "--vmarg", help="Voltage Margin", type=int, default=0)
    parser.add_argument("-int_lpbk", "--int_lpbk", help="Internal loopback", action='store_true')
    parser.add_argument("-dura", "--dura", help="Duration", type=int, default=120)
    parser.add_argument("-snake_num", "--snake_num", help="Snake number 4/6", type=int, default=6)
    parser.add_argument("-fpo", "--first_pwr_on", help="First time power on", action='store_true')
    parser.add_argument("-ite", "--iteration", help="Number of power cycle test iterations", type=int, default=1)
    parser.add_argument("-no_pc", "--no_pwr_cycle", help="Power cycle", action='store_false')
    parser.add_argument("-swm_lp", "--swm_lp", help="Power Up SWM in Low Power Mode", action='store_true')
    parser.add_argument("-aapl", "--aapl", help="Setup AAPL", action='store_true')
    parser.add_argument("-mainfw", "--mainfw", help="Setup for mainfw", action='store_true')
    parser.add_argument("-goldfw", "--goldfw", help="Setup for goldfw", action='store_true')
    parser.add_argument("-switch_fw", "--switch-fw", help="Switch FW on Naples", action='store_true')
    parser.add_argument("-asic_type", "--asic_type", help="ASIC type: capri/elba", type=str, default="capri")
    parser.add_argument("-uefi", "--uefi", help="UEFI mode", action='store_true')
    parser.add_argument("-num_ite", "--num_ite", help="Number of iterations", type=int, default=1)
    parser.add_argument("-dis_net_port", "--dis_net_port", help="Disable RJ45 Network port", action='store_true')
    parser.add_argument("-disp_si", "--disp_si", help="Display ECC info", action='store_true')
    parser.add_argument("-hardcode", "--hardcode", help="DDR hardcode setting", action='store_true')
    parser.add_argument("-ddr_speed", "--ddr_speed", help="DDR speed", type=int, default=3200)
    parser.add_argument("-pc_mode", "--pc_mode", help="Power cycle mode; board: whole board PC; gpio3: GPIO3 PC", type=str, default="board")

    # Skew test parameters
    parser.add_argument("-fan_ctrl", "--fan_ctrl", help="Enable fan control", action='store_true')
    parser.add_argument("-tgt_die_temp", "--tgt_die_temp", help="Target Die temperature", type=int, default=80)

    args = parser.parse_args()

    test = nic_test()
    if args.snake_start == True:
        test.test_start(args.slot, "snake", args.mode)
        sys.exit()

    if args.snake_check == True:
        test.test_check(args.slot, "snake", args.mode)
        sys.exit()

    if args.snake == True:
        slot_list = args.slot_list.split(',')
        test.nic_test(slot_list, "snake", args.mode, args.wait_time, vmargin=args.vmarg, duration=args.dura, int_lpbk=args.int_lpbk, snake_num=args.snake_num, disp_si=args.disp_si)
        sys.exit()

    if args.prbs == True and args.asic_type == "elba":
        slot_list = args.slot_list.split(',')
        test.nic_test(slot_list, "prbs", args.mode, args.wait_time, vmargin=args.vmarg, duration=args.dura, int_lpbk=args.int_lpbk)
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
        if args.mainfw == True:
            test.setup_env_multi_mainfw(slot_list, args.mgmt, 30, args.first_pwr_on, args.no_pwr_cycle, args.dis_net_port)
        elif args.goldfw == True:
            test.setup_env_multi_goldfw(slot_list, args.mgmt, 30)
        else: 
            test.setup_env_multi_top(slot_list, args.mgmt, 30, args.first_pwr_on, args.no_pwr_cycle, args.aapl, args.swm_lp, args.asic_type, args.uefi, args.dis_net_port)
        sys.exit()

    if args.pwr_cycle_test == True:
        test.pwr_cycle_test(args.slot, args.iteration)
        sys.exit()

    if args.pwr_cycle_test_multi == True:
        slot_list = args.slot_list.split(',')
        test.pwr_cycle_test_multi(slot_list, args.iteration, args.pc_mode)
        sys.exit()

    if args.ena_uboot_pcie == True or args.dis_uboot_pcie == True:
        slot_list = args.slot_list.split(',')

        if args.ena_uboot_pcie == True:
            ena_dis = True
        else:
            ena_dis = False
        test.ena_dis_uboot_pcie(slot_list, ena_dis)
        sys.exit()

    if args.ena_esec_wp == True or args.dis_esec_wp == True:
        slot_list = args.slot_list.split(',')

        if args.ena_esec_wp == True:
            ena_dis = True
        else:
            ena_dis = False
        test.ena_dis_esec_wp(slot_list, ena_dis)
        sys.exit()

    if args.config_ddr == True:
        slot_list = args.slot_list.split(',')
        test.config_ddr(slot_list, args.hardcode, args.ddr_speed)
        sys.exit()

    if args.disp_ecc == True:
        slot_list = args.slot_list.split(',')
        test.disp_ecc(slot_list)
        sys.exit()

    if args.vrd_fault_line == True:
        slot_list = args.slot_list.split(',')
        test.vrd_fault_line(slot_list)
        sys.exit()

    if args.therm_alert_line == True:
        slot_list = args.slot_list.split(',')
        test.therm_alert_line(slot_list)
        sys.exit()

    if args.therm_trip_line == True:
        slot_list = args.slot_list.split(',')
        test.therm_trip_line(slot_list)
        sys.exit()

    if args.setup_uboot_env == True:
        slot_list = args.slot_list.split(',')

        test.setup_uboot_env(slot_list)
        sys.exit()

    if args.test_timeout == True:
        test.timeout_test(args.wait_time)

    if args.switch_fw == True:
        test.switch_fw(args.slot)
        sys.exit()

    if args.skew == True:
        slot_list = args.slot_list.split(',')
        test.skew_test(slot_list, args.fan_ctrl, args.tgt_die_temp)
        sys.exit()

    if args.skew_exit == True:
        slot_list = args.slot_list.split(',')
        test.skew_test_exit(slot_list)
        sys.exit()

    if args.emmc == True:
        slot_list = args.slot_list.split(',')
        test.ddr_test(slot_list, args.num_ite)
        sys.exit()

    if args.fix_bx == True:
        test.nic_con.fix_elba_bx_1(115200, args.slot)
        sys.exit()

