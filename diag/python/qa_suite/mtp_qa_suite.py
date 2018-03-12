#!/usr/bin/env python

import pexpect
import re
import sys
import time

sys.path.append("/home/diag/xin/lib")
import common

class mtptest:
    def __init__(self, mode):
        filename = "config/mtp_test_config.yaml"
        self.mtpconfig = common.load_yaml(filename)
        if mode == "MTP_QK":
            self.mtp_pre = self.mtpconfig["MTP_QK_PRE"]
            self.mtp = self.mtpconfig["MTP_QK"]
        else:
            print "Invalid MTP mode:", mode
            sys.exit(-1)

    def runpre(self, mode):
        session = common.session_start()
        #common.session_cmd(session, "/home/diag/xin/envinit.py", ending="envinit Done")
        #common.session_cmd(session, "i2cdetect -y -r 0")
        for key, pre in self.mtp_pre.items():
            cmd = pre["CMD"]
            su = pre["SUDO"]
            end = pre["ENDING"]
            tout = pre["TIMEOUT"]
            #if su == None:
            #    su = False
            #if end == None:
            #    end = "\$ "
            #if tout == None:
            #    tout = 30
            print "yyy cmd:", cmd, "sudo:", su, "; timeout:", tout
            common.session_cmd(session, cmd, tout, su, end)
        common.session_stop(session)
        time.sleep(3)

    def runtest(self, mode):
        try:
            test_config = self.mtpconfig[mode]
        except KeyError:
            print "Invalid test mode:", mode
            sys.exit(-1)

        session = common.session_start()
        for key, test in test_config.items():
            cmd = test["CMD"]
            sudo = test["SUDO"]
            ending = test["ENDING"]
            tout = test["TIMEOUT"]
            if ending == None:
                ending = "\$ "
            common.session_cmd(session, cmd, tout, sudo, ending)

        common.session_stop(session)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("-m", "--mode", type=str, help="Test mode", default="")
    args = parser.parse_args()

    if args.mode == "MTP_QK":
        mtp = mtptest("MTP_QK")
        mtp.runtest("MTP_QK_PRE")
        mtp.runtest("MTP_QK")

    print "=== MTP Regression Done ==="
