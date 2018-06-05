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
            dumpfile = "iocpld.dump"
            cmd = "cpldutil -inst=1 -cpld-flash-rd -output="+dumpfile
            diffcmd = "diff "+filename+" "+dumpfile
            session = common.session_start()
            common.session_cmd(session, "ssh diag@"+self.ip, timeout=10)
            common.session_cmd(session, cmd, timeout=60)

            # Check whether two files are the same
            session.sendline(diffcmd)
            session.expect("\$ ")
            if ("diff:" in session.before) or ("differ" in session.before):
                print "=== Verify FAILED! ==="
                ret = False
            else:
                print "=== Verify PASSED! ==="
                ret = True

            print "=== CPLD version ==="
            cmd = "cpldutil -inst=1 -cpld-rd -addr=0"
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
    parser.add_argument("-tp", "--type", help="Type, e.g. IOCPLD", type=str, default='')
    parser.add_argument("-fn", "--filename", help="Filename", type=str, default='')
    parser.add_argument("-full", "--full", help="Full upgrade process", action='store_true')
    parser.add_argument("-v", "--verify", help="Verify content against file", action='store_true')
    parser.add_argument("-emac", "--mac", help="EEPROM MAC address", type=str, default="")
    parser.add_argument("-esn", "--sn", help="EEPROM serial number", type=str, default="")
    args = parser.parse_args()
    
    filename = args.filename
    mtp = mtpUpgrade()
    mtp.setup(args.platform)

    print "p:", args.platform, "tp:", args.type, "f:", args.filename
    if args.type == "IOCPLD":
        if args.full == True:
            ## Get platform ready
            ret = mtp.mtprdy(False)
            if ret != 0:
                sys.exit()
        
            mtp.mtpinit()
            mtp.copy_file(filename)
            mtp.upgrade(args.type, filename)
            mtp.mtprdy(True)
            mtp.mtpinit()
            ret = mtp.verify(args.type, filename)
            if ret == True:
                print filename+" matches after upgrade"
            else:
                print filename+" does not match after upgrade!"
    
        if args.verify == True:
            mtp.verify(args.type, filename)


    if args.type == "FRU":
        mtp.upgradeEep(args.mac, args.sn)
