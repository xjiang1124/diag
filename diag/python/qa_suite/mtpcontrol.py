#!/usr/bin/env python

import argparse
import pexpect
import re
import sys
import time

import tscontrol
import apccontrol
sys.path.append("../lib")
import common
from pwrcontrol import pwrControl

class mtpControl:
    def __init__(self):
        # Retrieve platform info
        filename = "config/chassis_info.yaml"
        self.csconfig = common.load_yaml(filename)

        self.pf = ""
        self.pfconfig = dict()
        
        # Prepare for log file name, based on date, time and iteration
        filename = "config/sys_info.yaml"
        self.sysconfig = common.load_yaml(filename)
        self.log_loc = self.sysconfig["LOG_LOC"]

        self.pwr = pwrControl()

    def setup(self, pf):
        try:
            self.pfconfig = self.csconfig[pf]
        except KeyError:
            print "Can not retrieve platform information!"
            sys.exit()
        self.pf = pf
        self.ip = self.pfconfig["IP"]

    def fullpwrcycle(self):
        # Test whether system is alive
        # if alive, issue "sudo shutdown"
        session = common.session_start()
        ret = common.session_cmd(session, "ssh diag@"+self.ip, timeout=10)
        if ret != -2:
            common.session_cmd(session, "poweroff", sudo=True, timeout=10)
            time.sleep(60)
        else:
            print "=== MTP is not responding ==="
        common.session_stop(session)
        self.pwrcycle()

    def pwrcycle(self):
        self.pwr.pwraction(self.pf, "off")
        time.sleep(60)
        self.pwr.pwraction(self.pf, "on")

    def pwron(self):
        self.pwr.pwraction(self.pf, "on")

    def pwroff(self):
        # Test whether system is alive
        # if alive, issue "sudo shutdown"
        session = common.session_start()
        ret = common.session_cmd(session, "ssh diag@"+self.ip, timeout=10)
        if ret != -2:
            common.session_cmd(session, "poweroff", sudo=True, timeout=10)
            time.sleep(60)
        else:
            print "=== MTP is not responding ==="
        common.session_stop(session)
        self.pwr.pwraction(self.pf, "off")

    def wait4rdySsh(self, ite=20, intv=30):
        ip = self.pfconfig["IP"]
        #ip = "192.168.70.73"
        cmd = "ssh diag@"+ip
        for i in range(10):
            print "--- SSH attemp #"+str(i+1)+" ---"
            try:
                session = pexpect.spawn(cmd)
                session.timeout=10
                session.logfile_read = sys.stdout
                prmt = ["password: ", "\$ "]
                #print "prmt:", prmt
                session.expect(prmt)
                session.close()
                print "\n", "===", self.pf, "is ready ==="
                return 0
                break
            except pexpect.TIMEOUT:
                print "--- SSH attemp #"+str(i+1)+" failed ---"
            except pexpect.EOF:
                continue
            time.sleep(intv)
        print "--- "+self.pf+" failed boot! ---"
        return -1

    # Use ssh to check whether MTP is alive
    def sshCheck(self):
        session = common.session_start()
        ret = common.session_cmd(session, "ssh diag@"+self.ip, timeout=10)
        if ret != -2:
            ret = common.session_cmd(session, "exit", timeout=10)
            retVal = 0
        else:
            print "=== MTP is not responding ==="
            retVal = -1
        common.session_stop(session)
        return retVal

    def mtprdy(self, pwr):
        if pwr == True:
            self.fullpwrcycle()
            ret = self.wait4rdySsh()
            return ret

        # No mandatory power cycle
        ret = self.sshCheck()
        if ret == 0:
            return ret

        self.fullpwrcycle()
        ret = self.wait4rdySsh()
        return ret

    def mtpinit(self):
        session = common.session_start()
        common.session_cmd(session, "ssh diag@"+self.ip)
        common.session_cmd(session, "./start_diag.sh", timeout=120, ending="Set up diag amd64 -- Done")
        common.session_cmd(session, "exit")
        common.session_stop(session)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.RawTextHelpFormatter)
    #group = parser.add_mutually_exclusive_group()
    parser.add_argument("-pf", "--platform", help="Platform, e.g. MTP001", type=str, default='')
    parser.add_argument("-pc", "--pwrcycle", help="Power cycle enable", action='store_true')
    parser.add_argument("-rdy", "--ready", help="Get platform ready", action='store_true')
    parser.add_argument("-off", "--off", help="Power off", action='store_true')
    args = parser.parse_args()
    
    mtp = mtpControl()
    mtp.setup(args.platform)

    if args.ready == True:
        mtp.mtprdy(args.pwrcycle)
        sys.exit()

    if args.pwrcycle == True:
        mtp.mtprdy(True)
        sys.exit()

    if args.off == True:
        mtp.pwroff()
