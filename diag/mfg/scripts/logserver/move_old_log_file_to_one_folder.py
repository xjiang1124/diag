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
    listofhistoryfolder = list()

    for eachjsonfile in listofJson:
        pr['modules'].debug_print("FILE: {}".format(eachjsonfile))
        eachjsondict = pr['modules'].readjsonfile(eachjsonfile)
        jsonfiledata[eachjsonfile] = eachjsondict

        thishistoryfolder = getcurrentlyhistoryfolder(eachjsondict)
        if thishistoryfolder:
            if not thishistoryfolder in listofhistoryfolder:
                listofhistoryfolder.append(thishistoryfolder) 

    pr['modules'].print_anyinformation(jsonfiledata)
    pr['modules'].print_anyinformation(listofhistoryfolder)


    for eachjsonfolder in listofhistoryfolder:
        print(eachjsonfolder)
        BackupAlloldfolder = "{}/BACKUP".format(eachjsonfolder)
        pr['modules'].createdirinserver(BackupAlloldfolder)
        listofJsonfromfolder = pr['modules'].getallfolder(eachjsonfolder,level=2)
        pr['modules'].print_anyinformation(listofJsonfromfolder) 
        listofJsonfromfolder.remove(eachjsonfolder)
        
        pr['modules'].debug_print("BACK UP FOLDER: {}".format(BackupAlloldfolder))
        if BackupAlloldfolder in listofJsonfromfolder:
            listofJsonfromfolder.remove(BackupAlloldfolder)
        pr['modules'].print_anyinformation(listofJsonfromfolder)
        #sys.exit()
        for eachdir in listofJsonfromfolder:
            eachdir = "{}/".format(eachdir)
            pr['modules'].rsync_and_delete_by_os_system_at_locate(eachdir,BackupAlloldfolder)

        #sys.exit()

    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None

def getcurrentlyhistoryfolder(eachjsondict):
    if 'DIR' in eachjsondict:
        if 'historypath' in eachjsondict['DIR']:
            return eachjsondict['DIR']['historypath']

    return None
if __name__ == "__main__":
    sys.exit(main())