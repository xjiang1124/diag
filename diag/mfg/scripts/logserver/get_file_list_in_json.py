#!/usr/bin/python3

import shutil
import json
import sys
import glob
import os
import re
from datetime import datetime

now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d_%H%M%S")
print("date and time:",date_time)

#TEST on KEY_WORD
#print(KEY_WORD.NIC_DIAG_TEST_RSLT_RE)

def main():

    start=datetime.now()
    ARGV = dict()
    check_argv(ARGV)
    #print(json.dumps(ARGV, indent = 4 ))

    if 'dir' in ARGV:

        filedict = dict()
        cwd = ARGV['dir']
        start2=datetime.now()
        listofJson = getallfileinfolderbyoswalk(cwd)
        timedifferentfromstart(start2)
        print("How many files in DIR[{}]? {}".format(cwd,len(listofJson)))
        start3=datetime.now()
        listofJson = getallfilebyfolder(cwd)
        timedifferentfromstart(start3)
        print("How many files in DIR[{}]? {}".format(cwd,len(listofJson)))

    else:
        print("Missing [dir] input!")

    
    timedifferentfromstart(start)
    return None

def timedifferentfromstart(start):
    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))   

    return difftime

def check_argv(ARGV):
    #print(sys.argv)

    for argvitem in sys.argv:
        #print(argvitem)
        matchcheck = re.findall(r"(.*)=(.*)", argvitem)
        if matchcheck:
            #print(matchcheck)
            ARGV[matchcheck[0][0]] = matchcheck[0][1]

    return None

def getallfileinfolderbyoswalk(rootdir,keyword=None,level=None):
    listOfFiles = list()
    for (dirpath, dirnames, filenames) in os.walk(rootdir):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames]

    listOfFiles.sort()

    #print(json.dumps(listOfFiles, indent = 4 ))

    return listOfFiles

def getallfilebyfolder(rootdir,keyword=None,level=None):

    listofdirs = getallfolder(rootdir,keyword=keyword,level=level)

    listoffiles = list()

    for eachdir in listofdirs:
        somelists = glob.glob(eachdir + '/*')
        for something in somelists:
            if os.path.isfile(something):  
                basename = os.path.basename(something)
                if keyword:
                    if not keyword.upper() in basename.upper():
                        continue
                if not something in listoffiles:
                    listoffiles.append(something)

    listoffiles.sort()

    #print(json.dumps(listoffiles, indent = 4))

    return listoffiles

def getallfolder(rootdir,keyword=None,level=None):

    listofdirs = list()

    listofdirs.append(rootdir)

    stillhavedir = True

    count = 1
    #print(level)

    while stillhavedir:
        
        if level:
            #print(json.dumps(listofdirs, indent = 4))
            if count >= level:
                break
        stillhavedir = False
        resultlist = list()         

        for checkdir in listofdirs:
            somelists = glob.glob(checkdir + '/*')
            #print("COUNT: {} DIR: {} STILLHAVE: {}".format(count,checkdir,stillhavedir))
            for something in somelists:
                if os.path.isdir(something):
                    if not something in listofdirs:
                        stillhavedir = True
                        resultlist.append(something)
        #print("COUNT: {} TOTAL resultlist: {} STILLHAVE: {}".format(count,len(resultlist), stillhavedir))
        for eachdir in resultlist:
            if not eachdir in listofdirs:
                listofdirs.append(eachdir)

        #print("COUNT: {} TOTAL listofdirs: {} STILLHAVE: {}".format(count,len(listofdirs), stillhavedir))
        count += 1

    #print("LEVEL: {}".format(level))

    return listofdirs

if __name__ == "__main__":
    sys.exit(main())