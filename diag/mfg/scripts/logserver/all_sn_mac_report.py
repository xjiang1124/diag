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
from openpyxl.styles import numbers
from openpyxl.chart import BarChart, Reference, Series, LineChart
from openpyxl.chart.label import DataLabelList
from datetime import datetime

import modules

now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d_%H%M%S")
print("date and time:",date_time)

reportpath = "/samba/public/REPORT/SNMAC/"
MTPslot = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]

def main():

    start=datetime.now()
    pr = dict()
    pr['modules'] = modules.modules()
    pr['modules'].createdirinserver(reportpath)
    cwd = os.getcwd()
    
    listofJson = pr['modules'].getallfilebyfolder(cwd, keyword="input.json")

    #pr['modules'].print_anyinformation(listofJson)

    jsonfiledata = dict()
    listofcurrentusingdatabase = list()

    for eachjsonfile in listofJson:
        pr['modules'].debug_print("FILE: {}".format(eachjsonfile))
        eachjsondict = pr['modules'].readjsonfile(eachjsonfile)
        jsonfiledata[eachjsonfile] = eachjsondict
        thisdatabasefile = getcurrentlymtpdatabasejsonfile(eachjsondict)
        if thisdatabasefile:
            if not thisdatabasefile in listofcurrentusingdatabase:
                listofcurrentusingdatabase.append(thisdatabasefile)

    pr['modules'].print_anyinformation(jsonfiledata)
    pr['modules'].print_anyinformation(listofcurrentusingdatabase)
    #sys.exit()

    if len(listofcurrentusingdatabase) != 1:
        print("ERROR! Have {} file for MTP DATABASE, it is not correct!".format(len(listofcurrentusingdatabase)))
        sys.exit()

    SNMACDATA = pr['modules'].readjsonfile(listofcurrentusingdatabase[0])
    #pr['modules'].print_anyinformation(MTPDATA)

    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None



def getcurrentlymtpdatabasejsonfile(eachjsondict):
    if 'FILE' in eachjsondict:
        if 'snandmacjsonfile' in eachjsondict['FILE']:
            return eachjsondict['FILE']["snandmacjsonfile"]

    return None

if __name__ == "__main__":
    sys.exit(main())