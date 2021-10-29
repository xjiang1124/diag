#!/usr/bin/python3

import shutil
import json
import sys
import glob
import os
import re
import mpu.io
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font
from openpyxl.cell import Cell
import timeit
from datetime import datetime
from datetime import timedelta
import pandas as pd
import math
import numpy
from os import listdir
import time
from logdef import KEY_WORD
import modules

now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d_%H%M%S")
print("date and time:",date_time)

#TEST on KEY_WORD
#print(KEY_WORD.NIC_DIAG_TEST_RSLT_RE)

def main():

    start=datetime.now()
    pr = dict()
    pr['modules'] = modules.modules()

    yamlfile = '/home/mfg/taormina_PP/diag/mfg/config/taormina_sn_pcbasn_cfg.yaml'
    #yamlfile2 = '/home/mfg/taormina_DL3/diag/mfg/config/taormina_sn_pcbasn_cfg3.yaml'

    #sn_pcbasn_yamldict = pr['modules'].readyamltodict(yamlfile)

    #pr['modules'].wirtedicttoyaml(sn_pcbasn_yamldict, yamlfile2)

    #pr['modules'].print_anyinformation(sn_pcbasn_yamldict)

    #sn_pcbasn_yamldict2 = pr['modules'].readyamltodict(yamlfile2)

    #pr['modules'].print_anyinformation(sn_pcbasn_yamldict2)

    #sys.exit()

    pathofsn = '/samba/public/SN'
    listoffiles = pr['modules'].getallfilebyfolder(pathofsn,keyword='xlsx')
    listoffiles.sort()

    #pr['modules'].print_anyinformation(listoffiles)
    SNvsPCBA = dict()

    for eachfile in listoffiles:
        pr['modules'].readSNxlsxfile(eachfile,SNvsPCBA)

    #pr['modules'].print_anyinformation(SNvsPCBA)

    SNlist = list()

    for SN in SNvsPCBA:
        somedict = dict()
        somedict['SN'] = SN
        somedict['PCBA_SN'] = SNvsPCBA[SN]
        SNlist.append(somedict)

    #pr['modules'].print_anyinformation(SNlist)
    pr['modules'].wirtedicttoyaml(SNlist, yamlfile)
    sn_pcbasn_yamldict2 = pr['modules'].readyamltodict(yamlfile)
    pr['modules'].print_anyinformation(sn_pcbasn_yamldict2)

    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None


if __name__ == "__main__":
    sys.exit(main())