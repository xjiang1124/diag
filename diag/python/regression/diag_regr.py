#!/usr/bin/env python

import os
from os import walk
import errno
import sys
import re
import yaml
import pickle
import pprint
import redis
from collections import OrderedDict
#from subprocess import call

from pebble import ProcessPool
from concurrent.futures import TimeoutError

sys.path.append("../lib")
import common
#=========================================================
# Initialization
pp = pprint.PrettyPrinter()
input_path = './config/'

#=========================================================
# yaml parser
config_file = "cards.yaml"
config_dict = common.load_yaml(config_file)

for (dirpath, dirnames, filenames) in walk(input_path):
    print filenames

# Exclude unnecessory file like .swp
r = re.compile('.*yaml$')
filenames_needed = filter(r.match, filenames)

card_dict = OrderedDict()
cards_dict = OrderedDict()
for filename in filenames_needed:
    with open(input_path+filename) as stream:
        try:
            card_dict = common.ordered_load(stream, yaml.SafeLoader)
        except yaml.YAMLError as exc:
            print exc
            sys.exit()
        cards_dict.update(card_dict)

slot_dict = OrderedDict()
for card, slots in config_dict.items():
    slotArr = slots.split()
    for slot in slotArr:
        slot_dict[slot] = card

#diagBinPath = "/home/xguo2/workspace/psdiag/diag/app/bin/x86_64/"
#diagInfraPath = "/home/xguo2/workspace/psdiag/diag/infra/dshell/"
diagBinPath = "/home/mtp/diag/"
diagInfraPath = "/home/mtp/diag/dshell/"

cardNm = "NIC1"
mfgMode = "P2C"
regrDict = cards_dict["NAPLES"][mfgMode]

def parseRegrDict(cardNm, regrDict):
    diagCmd = diagInfraPath + "diag"

    #=============================
    # Parse test confiuration into a list of commands
    cmdList = []
    
    #=============================
    # Initlization section
    initDict = regrDict["INIT"]
    for initName, initCmd in initDict.items():
        if initCmd != None:
            cmd = initCmd.replace(":", " ")
            cmd = diagBinPath + cmd
            cmdList.append(cmd)
    
    #=============================
    # Sequential section --- Parameter
    if regrDict["UUT_SEQ"]["PARAM"] != None:
        paramList = regrDict["UUT_SEQ"]["PARAM"].split()
        for paramItem in paramList:
            cmd = ""
            param = paramItem.split(":")
            if len(param) != 4:
                print "Invalide parameter setting:", paramItem
                continue
            cmd = diagCmd
            cmd = cmd + " -param"
            cmd = cmd + " -c " + cardNm
            cmd = cmd + " -d " + param[0]
            cmd = cmd + " -t " + param[1]
            cmd = cmd + " -p " + param[2]+"="+param[3]
            cmdList.append(cmd) 
            
            # add show param command
            cmd = diagCmd
            cmd = cmd + " -sparam"
            cmd = cmd + " -c "+cardNm + " -d " + param[0] + " -t " + param[1]
            cmdList.append(cmd) 
    
    #=============================
    # Sequential section --- skip
    if regrDict["UUT_SEQ"]["SKIP"] != None:
        skipList = regrDict["UUT_SEQ"]["SKIP"].split() 
        for skipItem in skipList:
            cmd = ""
            cmd = cmd + diagCmd
            skip = skipItem.split()
            cmd = cmd + " -skip"
            cmd = cmd + " -c " + cardNm
            cmd = cmd + " -d " + skip[0]
            if len(skip) > 1:
                cmd = cmd + " -t "+skip[1]
            cmdList.append(cmd)
    
        # add show param command
        cmd = diagCmd
        cmd = cmd + " -sskip"
        cmd = cmd + " -c "+cardNm
        cmdList.append(cmd) 
    
    #=============================
    # Sequential section --- test
    if regrDict["UUT_SEQ"]["TEST"] != None:
        testList = regrDict["UUT_SEQ"]["TEST"].split() 
        for testItem in testList:
            cmd = diagCmd
            test = testItem.split()
            cmd = cmd + " -r"
            cmd = cmd + " -c " + cardNm
            if test[0] == "ALL":
                cmdList.append(cmd)
                continue
            cmd = cmd + " -d "+test[0]
            if len(test) == 1:
                continue
            if test[1] != "ALL":
                cmd = cmd + " -t "+test[1]
            cmdList.append(cmd)

    #=============================
    # Show history
    cmd = diagCmd
    cmd = cmd + " -shist" + " -c " + cardNm
    cmdList.append(cmd)

    return cmdList

cmdList1 = parseRegrDict("NIC1", regrDict)
cmdList2 = parseRegrDict("NIC2", regrDict)

def runRegr(cmdList):
    for cmd in cmdList:
        print cmd
        os.system(cmd)


def task_done(future):
    try:
        future.result()  # blocks until results are ready
    except TimeoutError as error:
        print("Function took longer than %d seconds" % error.args[1])
    except Exception as error:
        print("Function raised %s" % error)
        print(error.traceback)  # traceback of the function

with ProcessPool(max_workers=20, max_tasks=6) as pool:
    future = pool.schedule(runRegr, args=[cmdList1])
    future.add_done_callback(task_done)
    future = pool.schedule(runRegr, args=[cmdList2])
    future.add_done_callback(task_done)

print "====", "Regression Done", "====\n"
