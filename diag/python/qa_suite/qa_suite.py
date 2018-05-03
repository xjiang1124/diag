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
            time.sleep(60)
        else:
            print "=== MTP is not responding ==="
        common.session_stop(session)
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
                session.logfile_read = sys.stdout
                prmt = ["password: ", "\$ "]
                #print "prmt:", prmt
                session.expect(prmt)
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

def check_error(filename, num_test=0):
    with open(filename) as f:
        contents = f.read()
        count_pass = contents.count("TEST PASSED")
        count_fail = contents.count("TEST FAILED")

        if count_fail != 0:
            print "Found test failure!", count_fail
            return -1

        if count_pass != num_test:
            print "Number of pass does not match expected", "passed:", count_pass, ", expected:", num_test
            return -1

        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.RawTextHelpFormatter)
    #group = parser.add_mutually_exclusive_group()
    parser.add_argument("-p", "--platform", help="Platform, e.g. MTP001", type=str, default='')
    parser.add_argument("-m", "--mode", help="Platform, e.g. P2C", type=str, default='')
    parser.add_argument("-i", "--ite", help="Number of interation", type=int, default=9999)
    parser.add_argument("-pc", "--pwrcycle", help="Power cycle enable", action='store_true')
    parser.add_argument("-stop", "--stoponerror", help="Stop on error", action='store_true')
    args = parser.parse_args()
    
    qa = qaSuite()
    qa.setup(args.platform, args.mode)
    
    print "pc:", args.pwrcycle, "ite:", args.ite, "stop:", args.stoponerror
    for idx in range(args.ite):

        idx_str = str(idx+1)
        print "========== Iteration", idx_str, "Started =========="
        if args.pwrcycle == True:
            #qa.pwrcycle()
            qa.fullpwrcycle()
            ret = qa.wait4rdySsh()
            if ret != 0 and args.stoponerror == True:
                print "=== Stopped on error at ite "+idx_str+" ==="
                break;

        session = common.session_start()
        # Start logging
        filename = args.platform+"_temp.log"
        common.session_cmd(session, "script -f "+filename)
           
        ret = common.session_cmd(session, "ssh diag@"+qa.ip)
        common.session_cmd(session, "cd /home/diag/diag/python/qa_suite/")
        #common.session_cmd(session, "/home/diag/xin/envinit.py", sudo=False, ending="envinit Done")
        common.session_cmd(session, "./mtp_qa_suite.py -m="+args.mode, timeout=5000, ending="=== MTP Regression Done ===")

        common.session_cmd(session, "exit")

        # Quit script command
        common.session_cmd(session, "exit")

        common.session_stop(session)
 
        #==================================
        # Post process
        # Check MTP errors
        if args.mode == "MTP_QK":
            print "Checking test result"
            ret = check_error(filename, 8)
            if ret != 0:
                print "=== MTP TEST FAILED! ==="
                if args.stoponerror == True:
                    print "=== Stopped on error at ite "+idx_str+" ==="
                    break
            else:
                print "=== MTP TEST PASSED! ==="
   
        print "========== Iteration", idx_str, "Done =========="
   
    print "=== QA_SUITE Done ==="
