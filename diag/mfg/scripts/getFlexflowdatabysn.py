#!/usr/bin/env python

import sys
import os
import time
import pexpect
import threading
import argparse
import re
from datetime import datetime
import json

sys.path.append(os.path.relpath("../lib"))
import libmfg_utils
from libdefs import NIC_Type
from libdefs import MTP_Const
from libdefs import FF_Stage
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import MTP_DIAG_Path
from libdefs import MFG_DIAG_CMDS
from libdefs import NIC_Vendor
from libmfg_cfg import GLB_CFG_MFG_TEST_MODE
from libmfg_cfg import MFG_IMAGE_FILES
from libmfg_cfg import NIC_IMAGES
from libmfg_cfg import MTP_REV02_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import MTP_REV03_CAPABLE_NIC_TYPE_LIST
from libmfg_cfg import PSLC_MODE_TYPE_LIST
from libmfg_cfg import ELBA_NIC_TYPE_LIST
from libmfg_cfg import FPGA_TYPE_LIST
from libmfg_cfg import PART_NUMBERS_MATCH
from libmtp_db import mtp_db
from libmtp_ctrl import mtp_ctrl
from libdefs import Swm_Test_Mode
from libmfg_cfg import *

def main():

    start=datetime.now()

    ARGV = dict()
    checkargv(ARGV)

    if 'test' in ARGV:

        resp = libmfg_utils.flx_web_srv_get_uut_info(ARGV["sn"],ARGV['test'])

        #print(resp)

        #print("################## GET UUT INF #######################")
        resp = resp.replace(':\n',': ')
        resp = resp.replace('&gt;', ' ')
        #print resp
        match = re.findall(r"Unit Current State:\s+(\w.*\w)",resp)
        #print(match)
        if match:
            print("CURRENT STATUS: {}".format(match[0]))
        else:
            print("CURRENT STATUS: NONE")
            print(resp)

    else:        

        resp = libmfg_utils.flx_web_srv_get_uut_info(ARGV["sn"])

        #print(resp)

        #print("################## GET UUT INF #######################")
        resp = resp.replace(':\n',': ')
        resp = resp.replace('&gt;', ' ')
        #print resp
        match = re.findall(r"Unit Current State:\s+(\w.*\w)",resp)
        #print(match)
        if match:
            print("CURRENT STATUS: {}".format(match[0]))
        #print("################## GET UUT INF #######################")
        #return "500"
        else:
            resp = libmfg_utils.flx_web_srv_get_uut_info(ARGV["sn"],stage="P2C")
            resp = resp.replace(':\n',': ')
            resp = resp.replace('&gt;', ' ')
            #print resp
            match = re.findall(r"Unit Current State:\s+(\w.*\w)",resp)
            #print(match)
            if match:
                print("CURRENT STATUS: {}".format(match[0]))
            else:
                print("CURRENT STATUS: NONE")
                print(resp)

    difftime = datetime.now()-start
    #print('Done Time: ', difftime)       
    #print("How many seconds use?: {} seconds".format(difftime.total_seconds()))  

    return


def checkargv(ARGV):
    #print(sys.argv)

    for argvitem in sys.argv:
        #print(argvitem)
        matchcheck = re.findall(r"(.*)=(.*)", argvitem)
        if matchcheck:
            #print(matchcheck)
            ARGV[matchcheck[0][0]] = matchcheck[0][1]

    #print(json.dumps(ARGV, indent = 4 ))

    #sys.exit()

    return None

if __name__ == "__main__":
    main()

