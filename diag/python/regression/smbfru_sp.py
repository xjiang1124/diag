#!/usr/bin/env python

import argparse
import datetime
import math
import pexpect
import os
import re
import sys

from collections import OrderedDict
from time import sleep

import datetime

sys.path.append("../lib")
import common
from nic_con import nic_con

class smbfru_wp:
    def __init__(self):
        self.name = "smb fru wp"
        self.nic_con = nic_con()

    def check_fru_wp(self, slot=0):
        if slot == 0 or slot > 10:
            print "Invalid slot number:", slot
            sys.exit(0)
        print "=== Starting smb fru wp test on slot {} ===".format(slot)
        ret = 0

        session = common.session_start()
        session.timeout = 400
        try:
            cmd = "eeutil -uut=uut_{} -disp -field=pn".format(slot)
            common.session_cmd_no_rc(session, cmd)
            pn_output = str(session.before)
            pn_output = pn_output.split()
            orig_pn = pn_output[-4] + " " + pn_output[-3]
            cmd = "eeutil -uut=uut_{} -disp -field=mac".format(slot)
            common.session_cmd_no_rc(session, cmd)
            mac_output = str(session.before)
            mac_output = mac_output.split()
            orig_mac = mac_output[-3]
            orig_mac = re.sub('-', '' , orig_mac)
            prog_mac = re.sub('00', 'FF', orig_mac)
            cmd = "eeutil -uut=uut_{} -update -pn={} -mac={}".format(slot, orig_pn, prog_mac)
            common.session_cmd_no_rc(session, cmd)
            cmd = "eeutil -uut=uut_{} -disp -field=mac".format(slot)
            common.session_cmd_no_rc(session, cmd)
            mac_output = str(session.before)
            mac_output = mac_output.split()
            read_mac = mac_output[-3]
            read_mac = re.sub('-', '' , read_mac)
            print "original pn", orig_pn,  "original mac", orig_mac, "read mac", read_mac, "\n"

            if read_mac != orig_mac:
                common.session_stop(session)
                ret = -1

        except:
            print "=== check smb fru wp TIMEOUT on slot {} ===".format(slot)
            common.session_stop(session)
            ret = -1

        common.session_stop(session)
        return ret

    def smb_fru_wp(self, slot_list=[]):
        print "=== smb fru wp test"
        if len(slot_list) == 0:
            print "No nic specified -- Exit"
            sys.exit(0)

        print "slot:", slot_list
        nic_list = ",".join(slot_list)

        # initialize all slots to FAIL as default
        test_result = OrderedDict()
        for slot in slot_list:
            test_result[slot] = "FAILED"

        # Start smb fru wp test 
        session = common.session_start()
        session.timeout = 300
        cmd = "turn_on_slot.sh off {}".format(nic_list)
        common.session_cmd_no_rc(session, cmd)
        sleep(2)
        cmd = "turn_on_slot_3v3.sh on {}".format(nic_list)
        common.session_cmd_no_rc(session, cmd)
        sleep(1)
        common.session_stop(session)

        for slot in slot_list:
            ret = self.check_fru_wp(int(slot))
            if ret == 0:
                test_result[slot] = "PASSED"
                print "=== Result at Slot {}: Passed".format(slot)
            else:
                print "=== Result at Slot {}: Failed".format(slot)

        print "\n====== SMB FRU WP TEST RESULT SUMMERY: ======"
        result_fmt = "Slot {:<2}: {:<5}"
        for slot, sts in test_result.items():
            print result_fmt.format(slot, sts)
        print "======================================"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="smb FRU Protect", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-slot_list", "--slot_list", help="slot(s) to test", type=str, default="")
    args = parser.parse_args()

    test = smbfru_wp()
    slot_list = args.slot_list.split(',')
    test.smb_fru_wp(slot_list)
    sys.exit()

