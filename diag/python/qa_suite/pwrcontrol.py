#!/usr/bin/env python

import pexpect
import re
import sys

sys.path.append("../lib")
import common
from apccontrol import apcControl

class pwrControl:
    def __init__(self):
        filename = "config/chassis_info.yaml"
        self.csconfig = common.load_yaml(filename)
        self.apccontrol = apcControl()

    def pwraction(self, csname, action):
        if action != "on" and action != "off":
            print "Unsupported action:", action
            return

        try:
            csinfo = self.csconfig[csname]
        except KeyError:
            print "Chassis name not found:", csname
            return

        # find APC info 1 by 1 in case there are more than one APCs
        apc_pattern = "^APC_(\d+)_NAME.*"
        re_p = re.compile(apc_pattern)
        for key in csinfo.keys():
            m = re_p.match(key)
            if m:
                apcidx = m.group(1)
                apcname = csinfo[key]
                apcport = csinfo["APC_"+apcidx+"_PORT"]
                if apcname == None or apcport == None:
                    continue
                if action == "on":
                    self.apccontrol.turn_on(apcname, apcport)
                else:
                    self.apccontrol.turn_off(apcname, apcport)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-on", "--on", action="store_true", help="Turn on APC port")
    group.add_argument("-off", "--off", action="store_true", help="Turn off APC port")
    parser.add_argument("-p", "--port", type=int, help="APC port number", default=0)
    args = parser.parse_args()

    pwr = pwrControl()
    pwr.pwraction("MTP001", "on")
