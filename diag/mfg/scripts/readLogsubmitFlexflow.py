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

def main():

    start=datetime.now()

    ARGV = dict()
    checkargv(ARGV)

    test_log_file = ARGV["file"]

    with open(test_log_file, 'r') as fp:
        buf = fp.read()

    #print(buf)

    mtp_id = findMTPbylog(buf)
    mfg_dl_start_ts, mfg_dl_stop_ts = findtotaltesttime(buf)

    libmfg_utils.mfg_report(mtp_id, mfg_dl_start_ts, mfg_dl_stop_ts, test_log_file, ARGV["test"])

    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))  

    return

def findtotaltesttime(buf):
    #print(f)
    match = re.findall(r"\[(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\]", buf) 

    #print(match)

    if match:
        #print(match[0])

        #print(match[-1])

        starttime = "{}_{}".format(match[0][0], match[0][1])
        endtime = "{}_{}".format(match[-1][0], match[-1][1])
        if starttime > endtime:
            print(match)
            #print(len(match))
            #sys.exit()
            for x in range(len(match)):
                starttime = "{}_{}".format(match[x][0], match[x][1])
                if endtime > starttime:
                    break
        startdatetime_object = datetime.strptime(starttime, '%Y-%m-%d_%H-%M-%S')
        enddatetime_object = datetime.strptime(endtime, '%Y-%m-%d_%H-%M-%S')

        return startdatetime_object, enddatetime_object

    return None, None

def findMTPbylog(buf):
    match = re.findall(r"##\s\[.*\]\sLOG:\s\[(\w+\-\d+)\]:", buf)
    #print(match)
    if match:
        return match[0]

    return None

def checkargv(ARGV):
    print(sys.argv)

    for argvitem in sys.argv:
        #print(argvitem)
        matchcheck = re.findall(r"(.*)=(.*)", argvitem)
        if matchcheck:
            #print(matchcheck)
            ARGV[matchcheck[0][0]] = matchcheck[0][1]

    print(json.dumps(ARGV, indent = 4 ))

    #sys.exit()

    return None

if __name__ == "__main__":
    main()

