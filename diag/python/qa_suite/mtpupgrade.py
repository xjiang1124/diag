#!/usr/bin/env python

import argparse
import pexpect
import re
import sys
import filecmp
import time

import apccontrol
from mtpcontrol import mtpControl
from pwrcontrol import pwrControl
import tscontrol

sys.path.append("../lib")
import common

class mtpUpgrade(mtpControl):
    def __init__(self):
        mtpControl.__init__(self)

    def copy_file(self, filename):
        cmd = "scp "+filename+" diag@"+self.ip+":"
        session = common.session_start()
        ret = common.session_cmd(session, cmd, timeout=10)
        common.session_stop(session)

    def upgrade(self, upgtype, filename):
        if upgtype == "IOCPLD":
            cmd = "cpldutil -inst=1 -cpld-flash-prog -input=./"+filename
        elif upgtype == "JTAGCPLD":
            cmd = "cpldutil -inst=0 -cpld-flash-prog -input=./"+filename
        else:
            print "Wrong upgrade type:", uptype
            return -1
        session = common.session_start()
        common.session_cmd(session, "ssh diag@"+self.ip, timeout=10)
        common.session_cmd(session, cmd, timeout=60)
        common.session_cmd(session, "exit")
        common.session_stop(session)
        return 0

    def verify(self, upgtype, filename):
        ret = False
        if upgtype == "IOCPLD":
            inst = 1
            regAddr = 0
        elif upgtype == "JTAGCPLD":
            inst = 0
            regAddr = 0x19
        else:
            print "Unsupported type:", upgtype
            print "=== Verify FAILED! ==="
            return -1

        dumpfile = "verify.dump"
        cmd = "cpldutil -inst="+str(inst)+" -cpld-flash-rd -output="+dumpfile
        diffcmd = "diff "+filename+" "+dumpfile
        session = common.session_start()
        common.session_cmd(session, "ssh diag@"+self.ip, timeout=10)
        common.session_cmd(session, cmd, timeout=60)

        # Check whether two files are the same
        session.sendline(diffcmd)
        session.expect("\$ ")
        if ("diff:" in session.before) or ("differ" in session.before):
            print "=== Verify FAILED! ==="
            ret = -1
        else:
            print "=== Verify PASSED! ==="
            ret = 0

        print "=== CPLD version ==="
        cmd = "cpldutil -inst=1 -cpld-rd -addr="+str(regAddr)
        common.session_cmd(session, cmd)

        common.session_cmd(session, "exit")
        common.session_stop(session)

        return ret

    def upgradeEep(self, mac, sn):
        cmd = "eeutil -update -dev=FRU -sn="+sn+" -mac="+mac
        cmdDisp = "eeutil -show -dev=FRU"
        session = common.session_start()
        common.session_cmd(session, "ssh diag@"+self.ip, timeout=10)
        common.session_cmd(session, cmd, timeout=60)
        common.session_cmd(session, cmdDisp, timeout=60)
        common.session_cmd(session, "exit")
        common.session_stop(session)
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface\ne.g. ./mtpupgrade.py -pf=MTP001 -tp=IOCPLD -fn=./NIC_MTP_IO.bin -full", formatter_class=argparse.RawTextHelpFormatter)
    #group = parser.add_mutually_exclusive_group()
    parser.add_argument("-pf", "--platform", help="Platform, e.g. MTP001", type=str, default='')
    parser.add_argument("-tp", "--type", help="Supported types:  IOCPLD/JTAGCPLD/FRU", type=str, default='')
    parser.add_argument("-fn", "--filename", help="Filename", type=str, default='')
    parser.add_argument("-full", "--full", help="Full upgrade process including power cycle and verify", action='store_true')
    parser.add_argument("-v", "--verify", help="Verify content against file", action='store_true')
    parser.add_argument("-emac", "--mac", help="EEPROM MAC address", type=str, default="")
    parser.add_argument("-esn", "--sn", help="EEPROM serial number", type=str, default="")
    args = parser.parse_args()
    
    filename = args.filename
    pf = args.platform.upper()
    pf_type = args.type.upper()
    mtp = mtpUpgrade()
    mtp.setup(pf)

    #print "p:", args.platform, "tp:", pf_type, "f:", args.filename
    if pf_type == "IOCPLD" or pf_type == "JTAGCPLD":
        if args.full == True:
            ## Get platform ready
            ret = mtp.mtprdy(False, False)
            if ret != 0:
                sys.exit()
        
            mtp.mtpinit()
            mtp.copy_file(filename)
            mtp.upgrade(pf_type, filename)
            mtp.mtprdy(True, False)
            mtp.mtpinit()
            ret = mtp.verify(pf_type, filename)
            if ret == 0:
                print filename+" matches after upgrade"
            else:
                print filename+" does not match after upgrade!"
    
        if args.verify == True:
            mtp.verify(pf_type, filename)


    if pf_type == "FRU":
        mtp.upgradeEep(args.mac, args.sn)
