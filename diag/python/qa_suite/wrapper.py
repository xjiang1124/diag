#!/usr/bin/env python

import pexpect
import sys
import re
import time

sys.path.append("../lib")
import common

import nic_test
from nic_con import nic_con

slot_list = ["1","2","3","4","5","6","7","8","9","10"]

class wrapper:
    def __init__(self):
        self.name = "nic prbs test"

    def nic_prbs_test(self, nic_list=[]):

        try:
            for slot in nic_list:
                prbs = pexpect.spawn('ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@10.1.1.{}'.format(int(slot) + 100))
                prbs.logfile = sys.stdout
                prbs.expect ('password:', timeout=1)
                prbs.sendline("pen123\r")
                prbs.expect('#', timeout=5)
                prbs.sendline("cd /data/nic_util\r")
                prbs.sendline("./asicutil -prbs -mode pcie\r")
                prbs.sendline("\r")
                prbs.expect("PRBS PASSED", timeout=300)
                prbs.close

        except pexpect.TIMEOUT:
            print "PRBS test time out on slot {}".format(slot)
            return 1

        return 0

    def nic_jtags_test(self, nic_list=[]):

        try:
            for slot in nic_list:
                jtag = pexpect.spawn('bash')
                jtag.expect('$', timeout=5)
                jtag.logfile = sys.stdout
                jtag.sendline("cd ~/diag/scripts/asic\r")
                jtag.sendline("tclsh set_avs.tcl -arm_vdd arm -slot {}\r".format(slot))
                jtag.expect("SET AVS PASSED", timeout=200)
                time.sleep(5)
                print "JTAG test passed on slot {}".format(slot)
                jtag.close

        except pexpect.TIMEOUT:
            print "JTAG test time out on slot {}".format(slot)
            return 1

        return 0

if __name__=="__main__":
    test = nic_test.nic_test()
    console = nic_con()
    wrapper_test = wrapper()

    test.ena_dis_uboot_pcie(slot_list, False)    

    ret = test.setup_env_multi_top(slot_list, True, 30, False, True, False)    
    if ret[0] != 0:
        print "=== setup mgmt failed"
    else:
        print "=== setup mgmte was successful"

    ret = test.setup_env_multi_top(slot_list, True, 30, False, True, True)    
    if ret[0] != 0:
        print "=== setup mgmt aapl failed"
    else:
        print "=== setup mgmte aapl was successful"

    ret = wrapper_test.nic_prbs_test(slot_list)
    if ret != 0:
        print "== nic prbs test failed"
    else:
        print "== nic prbs tests passed"

    ret = wrapper_test.nic_jtags_test(slot_list)
    if ret != 0:
        print "== jtag test failed"
    else:
        print "== jtag tests passed"
    sys.exit()


