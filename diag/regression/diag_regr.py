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

#=========================================================
# To load yaml file in order
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

#=========================================================
# create output folder
def create_folder(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

#=========================================================
# Initialization
pp = pprint.PrettyPrinter()
input_path = './config/'

#=========================================================
# yaml parser
config_file = "cards.yaml"
with open(config_file) as stream:
    try:
        #config_dict = yaml.load(stream)
        config_dict = ordered_load(stream, yaml.SafeLoader)
    except yaml.YAMLError as exc:
        print exc
        sys.exit()

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
            card_dict = ordered_load(stream, yaml.SafeLoader)
        except yaml.YAMLError as exc:
            print exc
            sys.exit()
        cards_dict.update(card_dict)

slot_dict = OrderedDict()
for card, slots in config_dict.items():
    slotArr = slots.split()
    for slot in slotArr:
        slot_dict[slot] = card

cardNm = "NIC1"
mfgMode = "P2C"
regrDict = card_dict["NAPLES"][mfgMode]

def parseRegrDict(cardNm, regrDict):
    diagBinPath = "/home/xguo2/workspace/psdiag/diag/app/bin/x86/"
    diagInfraPath = "/home/xguo2/workspace/psdiag/diag/infra/dshell/"
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


#runRegr(cmdList)

print "====", "Regression Done", "====\n"
