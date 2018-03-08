#!/usr/bin/env python

import argparse
import pexpect
import re
import sys

import tscontrol
import apccontrol
sys.path.append("../lib")
import common

parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.RawTextHelpFormatter)
group = parser.add_mutually_exclusive_group()
parser.add_argument("-p", "--platform", help="Platform, e.g. MTP001", type=str, default='')
parser.add_argument("-m", "--mode", help="Platform, e.g. P2C", type=str, default='')
args = parser.parse_args()

# Retrieve platform info
filename = "config/chassis_info.yaml"
chassis_config = common.load_yaml(filename)
pltf_info = chassis_config[args.platform]
if not pltf_info:
    print "Can not retrieve platform information!")
    sys.exit()

modes = args.mode.split()
if len(modes) == 0:
    print "Mode field can not be empty!"
    sys.exit()

# Prepare for log file name, based on date, time and iteration
filename = "config/sys_info.yaml"
sys_config = common.load_yaml(filename)
log_loc = sys_config["LOG_LOC"]

print "===  ==="
