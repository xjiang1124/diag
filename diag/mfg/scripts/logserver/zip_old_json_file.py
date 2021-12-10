#!/usr/bin/python3

import shutil
import json
import sys
import glob
import os
import re
import mpu.io
from datetime import datetime

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

    cwd = os.getcwd()
    
    listofJson = pr['modules'].getallfilebyfolder(cwd, keyword="input.json")

    #pr['modules'].print_anyinformation(listofJson)

    jsonfiledata = dict()
    listofcurrentusingdatabase = list()
    listofdatabasefolder = list()

    for eachjsonfile in listofJson:
        pr['modules'].debug_print("FILE: {}".format(eachjsonfile))
        eachjsondict = pr['modules'].readjsonfile(eachjsonfile)
        jsonfiledata[eachjsonfile] = eachjsondict
        thisdatabaselist = getcurrentlydatabase(eachjsondict)
        if len(thisdatabaselist):
            for thisdatabase in thisdatabaselist:
                if not thisdatabase in listofcurrentusingdatabase:
                    listofcurrentusingdatabase.append(thisdatabase)
                datebasedir = os.path.dirname(thisdatabase)
                if not datebasedir in listofdatabasefolder:
                    listofdatabasefolder.append(datebasedir)

        thisdatabasefolder = getcurrentlydatabasefolder(eachjsondict)
        if thisdatabasefolder:
            if not thisdatabasefolder in listofdatabasefolder:
                listofdatabasefolder.append(thisdatabasefolder) 

    pr['modules'].print_anyinformation(jsonfiledata)
    pr['modules'].print_anyinformation(listofcurrentusingdatabase)
    pr['modules'].print_anyinformation(listofdatabasefolder)
    #sys.exit()

    for eachjsonfolder in listofdatabasefolder:
        print(eachjsonfolder)
        listofJsonfromfolder = pr['modules'].getallfilebyfolder(eachjsonfolder, keyword=".json")
        filterlist = list()
        for eachfile in listofJsonfromfolder:
            if eachfile[-4:] == 'json':
                if not eachfile in listofcurrentusingdatabase:
                    filterlist.append(eachfile)
        pr['modules'].print_anyinformation(filterlist)
        for eachgotozipfile in filterlist:
            pr['modules'].gzip_to_file(eachgotozipfile)

    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None

def getcurrentlydatabase(eachjsondict):
    listfordatabase = list()
    if 'FILE' in eachjsondict:
        for filename in eachjsondict['FILE']:
            listfordatabase.append(eachjsondict['FILE'][filename])

    return listfordatabase

def getcurrentlydatabasefolder(eachjsondict):
    if 'DIR' in eachjsondict:
        if 'TEMPDATABASE' in eachjsondict['DIR']:
            return eachjsondict['DIR']['TEMPDATABASE']

    return None
if __name__ == "__main__":
    sys.exit(main())