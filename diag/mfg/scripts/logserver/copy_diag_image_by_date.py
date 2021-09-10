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
    today = now.strftime("%Y.%m.%d")
    pr = dict()
    pr['modules'] = modules.modules()

    currentcwd = os.getcwd()

    pr['modules'].debug_print(currentcwd)

    pr['config'] = pr['modules'].readjsonfile('{}/diag_image.json'.format(currentcwd))
    DATA = pr['modules'].readjsonfile(pr['config']["FILE"]["datebasesjsonfile"])
    pr['modules'].print_anyinformation(pr)
    pr['modules'].checkDirectoryexist(pr['config']["DIR"])
    diagimagecwd = pr['config']["DIR"]["imagedir"]
    
    listofdiag = pr['modules'].getallfilebyfolder(diagimagecwd, keyword=".tar")

    pr['modules'].print_anyinformation(listofdiag)

    for eachdiagimage in listofdiag:
        md5sumoffile = pr['modules'].getmd5sumoffile(eachdiagimage)
        pr['modules'].debug_print("FILE: {} ==> MD5SUM: {}".format(eachdiagimage,md5sumoffile))
        filename = os.path.basename(eachdiagimage)
        pr['modules'].debug_print("OLD FILE: {}".format(filename))
        filearraybyname = filename.split('.')
        newfilename = "{}_{}.{}".format(filearraybyname[0],today,filearraybyname[1])
        pr['modules'].debug_print("NEW FILE: {}".format(newfilename))
        newpath = "{}/{}".format(pr['config']["DIR"]["local_dir"],today)
        pr['modules'].createdirinserver(newpath)
        newpathwithfile = "{}/{}".format(newpath,newfilename)
        if not today in DATA:
            DATA[today] = dict()
        if not filename in DATA[today]:
            DATA[today][filename] = dict()
        DATA[today][filename]["origin"] = eachdiagimage
        DATA[today][filename]["newfilename"] = newfilename
        DATA[today][filename]["newfilepath"] = newpathwithfile
        DATA[today][filename]["md5sum"] = md5sumoffile
        DATA[today][filename]["size_in_MB"] = pr['modules'].get_file_size(eachdiagimage)
        DATA[today][filename]["createdate"] = pr['modules'].findfilecreatedate(eachdiagimage)
        pr['modules'].copy_file(eachdiagimage,newpathwithfile)

    pr['modules'].print_anyinformation(DATA)
    pr['modules'].wirtejsonfile(pr['config']["FILE"]["datebasesjsonfile"],DATA)

    difftime = datetime.now()-start
    pr['modules'].debug_print('Done Time: {}'.format(difftime))       
    pr['modules'].debug_print("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None

def getcurrentlydatabase(eachjsondict):
    if 'FILE' in eachjsondict:
        if 'datebasesjsonfile' in eachjsondict['FILE']:
            return eachjsondict['FILE']['datebasesjsonfile']

    return None

def getcurrentlydatabasefolder(eachjsondict):
    if 'DIR' in eachjsondict:
        if 'TEMPDATABASE' in eachjsondict['DIR']:
            return eachjsondict['DIR']['TEMPDATABASE']

    return None
if __name__ == "__main__":
    sys.exit(main())