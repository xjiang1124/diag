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

class qaSuite:
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

    def setup(self, pf, modeStr):
        try:
            self.pfconfig = self.csconfig[pf]
        except KeyError:
            print "Can not retrieve platform information!"
            sys.exit()
        self.pf = pf
        self.ip = self.pfconfig["IP"]

        modes = modeStr.split()
        if len(modes) == 0:
            print "Mode field can not be empty!"
            sys.exit()
        self.modes = modes

    def fullpwrcycle(self):
        # Test whether system is alive
        # if alive, issue "sudo shutdown"
        session = common.session_start()
        ret = common.session_cmd(session, "ssh diag@"+self.ip, timeout=10)
        if ret != -2:
            common.session_cmd(session, "poweroff", sudo=True, timeout=10)
            time.sleep(180)
        else:
            print "=== MTP is not responding ==="
        session.close()
        self.pwrcycle()

    def pwrcycle(self):
        self.pwr.pwraction(self.pf, "off")
        time.sleep(60)
        self.pwr.pwraction(self.pf, "on")

    def wait4rdySsh(self, ite=20, intv=30):
        ip = self.pfconfig["IP"]
        #ip = "192.168.70.73"
        cmd = "ssh diag@"+ip
        for i in range(10):
            print "--- SSH attemp #"+str(i+1)+" ---"
            try:
                session = pexpect.spawn(cmd)
                session.timeout=10
                #session.logfile_read = sys.stdout
                session.expect("password: ")
                session.close()
                print self.pf, "is ready"
                return 0
                break
            except pexpect.TIMEOUT:
                print "--- SSH attemp #"+str(i+1)+" failed ---"
            except pexpect.EOF:
                continue
            time.sleep(intv)
        print "--- "+self.pf+" failed boot! ---"
        return -1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("-p", "--platform", help="Platform, e.g. MTP001", type=str, default='')
    parser.add_argument("-m", "--mode", help="Platform, e.g. P2C", type=str, default='')
    parser.add_argument("-i", "--ite", help="Number of interation", type=int, default=9999)
    parser.add_argument("-pc", "--pwrcycle", help="Power cycle enable", type=bool, default=True)
    parser.add_argument("-stop", "--stoponerror", help="Stop on error", type=bool, default=True)
    args = parser.parse_args()
    
    qa = qaSuite()
    qa.setup(args.platform, args.mode)
    
    for idx in range(args.ite):
        print "========== Iteration", idx+1, "=========="
        if args.pwrcycle == True:
            #qa.pwrcycle()
            qa.fullpwrcycle()
            ret = qa.wait4rdySsh()
            if ret != 0 and args.stoponerror == True:
                print "=== Stopped on error at ite "+str(idx+1)+" ==="
                break;
        session = common.session_start()
        ret = common.session_cmd(session, "ssh diag@"+qa.ip, timeout=30, ending="\$ ")
        common.session_cmd(session, "cd /home/diag/xin/qa_suite/", sudo=False)
        #common.session_cmd(session, "/home/diag/xin/envinit.py", sudo=False, ending="envinit Done")
        common.session_cmd(session, "/home/diag/xin/qa_suite/mtp_qa_suite.py -m="+args.mode, ending="=== MTP Regression Done ===")

        common.session_cmd(session, "exit")
        common.session_stop(session)
    
        print "========== Iteration", idx+1, "Done =========="
    
    print "=== QA_SUITE Done ==="
