#!/usr/bin/env python

import argparse
import pexpect
import re
import sys
import subprocess
import time

sys.path.append("../lib")
import common

parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-pf", "--platform", help="Platform, e.g. MTP001", type=str, default='')
args = parser.parse_args()

pf = args.platform.upper()

# Retrieve platform info
filename = "config/chassis_info.yaml"
csconfig = common.load_yaml(filename)

try:
    pfconfig = csconfig[pf]
except KeyError:
    print "Wrong platform", pf
    sys.exit()

filename = "~/diag/python/regression/scripts/dft_profile"
f = open(filename, "a")

for i in range(10):
    idx = str(i+1)
    uut = pfconfig["SLOT_"+idx.upper()]
    if uut != None:
        f.write('UUT_'+'"'+idx=uut+'"')

f.close()
