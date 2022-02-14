#!/usr/bin/python3

import shutil
import json
import sys
import glob
import os
import re
import mpu.io
from datetime import datetime
import time

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
    onlylistofdatabasefolder = list()

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
            if not thisdatabasefolder in onlylistofdatabasefolder:
                onlylistofdatabasefolder.append(thisdatabasefolder) 

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

    for eachjsonfolder in onlylistofdatabasefolder:
        print(eachjsonfolder)
        listofJsonfromfolder = pr['modules'].getallfilebyfolder(eachjsonfolder, keyword=".gz")
        filterlist = list()
        for eachfile in listofJsonfromfolder:
            if eachfile[-2:] == 'gz':
                if not eachfile in listofcurrentusingdatabase:
                    filterlist.append(eachfile)
                #print(eachfile)
                #print("Last modified: %s" % time.ctime(os.path.getmtime(eachfile)))
                #print("Created: %s" % time.ctime(os.path.getctime(eachfile)))
                #print(os.path.getctime(eachfile))
                #print(cal_total_Time_from_create(eachfile))
                if convertSecondtodays(cal_total_Time_from_create(eachfile)) > 7:
                    os.remove(eachfile)
                #sys.exit()
        #pr['modules'].print_anyinformation(filterlist)
        #for eachgotozipfile in filterlist:
            #pr['modules'].gzip_to_file(eachgotozipfile)


    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None

def cal_total_Time_from_create(eachfile):

    startdatetime_object = datetime.fromtimestamp(os.path.getctime(eachfile))
    enddatetime_object = datetime.now()
    difftime = enddatetime_object-startdatetime_object
    returninseconds = int(float("{}".format(difftime.total_seconds())))

    return returninseconds

def convertSecondtodays(getsecond):
    seconds_in_day = 60 * 60 * 24
    seconds_in_hour = 60 * 60
    seconds_in_minute = 60

    days = getsecond // seconds_in_day
    hours = (getsecond - (days * seconds_in_day)) // seconds_in_hour
    minutes = (getsecond - (days * seconds_in_day) - (hours * seconds_in_hour)) // seconds_in_minute

    print(days, hours, minutes)

    return days

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