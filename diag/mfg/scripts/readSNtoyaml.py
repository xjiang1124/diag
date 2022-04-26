#!/usr/bin/python3

import shutil
import sys
import glob
import os
import re
from openpyxl import Workbook
import timeit
from datetime import datetime
from datetime import timedelta
import pandas as pd
import math
import numpy
from os import listdir
import time
import modules

now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d_%H%M%S")
print("date and time:",date_time)

def main():

    start=datetime.now()
    ARGV = dict()
    checkconfigfile(ARGV)
    pr = dict()
    pr['modules'] = modules.modules()

    yamlfile = '../config/taormina_sn_pcbasn_cfg.yaml'

    pathofsn = ARGV["DIR"]
    listoffiles = pr['modules'].getallfilebyfolder(pathofsn,keyword='xlsx')
    listoffiles.sort()

    SNvsPCBA = dict()

    for eachfile in listoffiles:
        try:
            pr['modules'].readSNxlsxfile(eachfile,SNvsPCBA)
        except:
            print("This File have issue: {}!".format(eachfile))

    SNlist = list()

    for SN in SNvsPCBA:
        somedict = dict()
        somedict['SN'] = SN
        somedict['PCBA_SN'] = SNvsPCBA[SN]
        SNlist.append(somedict)

    print(yamlfile)
    pr['modules'].wirtedicttoyaml(SNlist, yamlfile)

    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None

def checkconfigfile(ARGV):

    for argvitem in sys.argv:
        matchcheck = re.findall(r"(.*)=(.*)", argvitem)
        if matchcheck:
            ARGV[matchcheck[0][0]] = matchcheck[0][1]

    return None
if __name__ == "__main__":
    sys.exit(main())