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

    yamlfile = '/samba/public/NAPLES25SWMDELLSNtoyaml/new_fru_cfg.yaml'
    #yamlfile2 = '/home/mfg/taormina_DL3/diag/mfg/config/taormina_sn_pcbasn_cfg3.yaml'
    print("yamlfile: {}".format(yamlfile))
    mac_yamldict = pr['modules'].readyamltodict(yamlfile)

    #pr['modules'].wirtedicttoyaml(sn_pcbasn_yamldict, yamlfile2)

    #pr['modules'].print_anyinformation(mac_yamldict)

    OLD_PN = ''
    PN = ''
    TYPE = ''
    for eachdata in mac_yamldict:
        #pr['modules'].print_anyinformation(eachdata)
        #pr['modules'].print_anyinformation(mac_yamldict[eachdata])
        if not len(OLD_PN):
            OLD_PN = mac_yamldict[eachdata]['OLD_PN']
        else:
            if OLD_PN != mac_yamldict[eachdata]['OLD_PN']:
                print("{} OLD_PN: {} vs {}".format(eachdata, OLD_PN, mac_yamldict[eachdata]['OLD_PN']))
                sys.exit()
        if not len(PN):
            PN = mac_yamldict[eachdata]['PN']
        else:
            if PN != mac_yamldict[eachdata]['PN']:
                print("{} PN: {} vs {}".format(eachdata, PN, mac_yamldict[eachdata]['PN']))
                sys.exit()
        if not len(TYPE):
            TYPE = mac_yamldict[eachdata]['TYPE']
        else:
            if TYPE != mac_yamldict[eachdata]['TYPE']:
                print("{} TYPE: {} vs {}".format(eachdata, TYPE, mac_yamldict[eachdata]['TYPE']))
                sys.exit()            
        #sys.exit()
    #sn_pcbasn_yamldict2 = pr['modules'].readyamltodict(yamlfile2)

    #pr['modules'].print_anyinformation(sn_pcbasn_yamldict2)

    print("OLD_PN: {} vs PN: {} vs TYPE: {}".format(OLD_PN,PN,TYPE))

    #sys.exit()

    pathofmac = os.path.dirname(yamlfile)
    listoffiles = pr['modules'].getallfilebyfolder(pathofmac,keyword='xlsx')
    listoffiles.sort()

    pr['modules'].print_anyinformation(listoffiles)
    MACvsOLDSNvsNEWSN = dict()

    #sys.exit()

    for eachfile in listoffiles:
        pr['modules'].readMACvsOLDSNvsNEWSNxlsfile(eachfile,MACvsOLDSNvsNEWSN)

    pr['modules'].print_anyinformation(MACvsOLDSNvsNEWSN)

    #sys.exit()

    for MAC in MACvsOLDSNvsNEWSN:
        if not MAC in mac_yamldict:
            mac_yamldict[MAC] = dict()
            mac_yamldict[MAC]['OLD_PN'] = OLD_PN
            mac_yamldict[MAC]['PN'] = PN
            mac_yamldict[MAC]['TYPE'] = TYPE
            mac_yamldict[MAC]['OLD_SN'] = MACvsOLDSNvsNEWSN[MAC]["OldSN"]
            mac_yamldict[MAC]['SN'] = MACvsOLDSNvsNEWSN[MAC]["NewSN"]

    #pr['modules'].print_anyinformation(SNlist)
    pr['modules'].wirtedicttoyaml(mac_yamldict, yamlfile)
    mac_yamldict2 = pr['modules'].readyamltodict(yamlfile)
    pr['modules'].print_anyinformation(mac_yamldict2)

    print("Total MAC: {}".format(len(mac_yamldict.keys())))

    for MAC in mac_yamldict:
        SN = mac_yamldict[MAC]['SN']
        OLDSN = mac_yamldict[MAC]['OLD_SN']
        for MAC2 in mac_yamldict:
            if MAC != MAC2:
                if SN == mac_yamldict[MAC2]['SN']:
                    print("Find same SN issue on 2 MAC: MAC1: {} SN {} equal to MAC2: {} SN: {}".format(MAC,SN,MAC2,mac_yamldict[MAC2]['SN']))
                    sys.exit()
                if OLDSN == mac_yamldict[MAC2]['OLD_SN']:
                    print("Find same OLDSN issue on 2 MAC: MAC1: {} OLDSN {} equal to MAC2: {} OLDSN: {}".format(MAC,OLDSN,MAC2,mac_yamldict[MAC2]['OLD_SN']))
                    sys.exit()
    print("Did not have Same SN or OLD SN issue on different MAC!")

    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None


if __name__ == "__main__":
    sys.exit(main())