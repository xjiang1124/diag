#!/usr/bin/python3

import json
import sys
import os
import re
from datetime import datetime
import pexpect
import runtest_modules
import log_modules
import threading
import time
#import mysql_db
import script_logging
import modules

now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d_%H%M%S")
print("date and time:",date_time)

testprogramDir = "/home/winson/winson/worksapce/taormina/psdiag/diag/mfg"

#runtestCmd = "./mfg_p2c_test.py"

#runtestCmd = "./mfg_p2c_test.py"

runtestCmdlist = ["./mfg_p2c_test.py"]

screenlogDir = "/home/winson/winson/tmp/screenLog"

logDir = "/home/winson/winson/tmp/log/"

TestUUTlist = ["UUT-132"]

Loopcountsetup = 50

def main():

    start=datetime.now()
    """ main routine."""
    scriptname = os.path.basename(__file__)
    print("Starting {0}...".format(scriptname))

    prefix = scriptname.replace('.py', '')
    ldir = logDir + prefix
    log = script_logging.Script_logging(
        log_dir=ldir, log_prefix=prefix, log_suffix='.log')
    if log.Open():
        print("Error: log failed to open, {0}".format(log.fullname))
        return -1

    pr = dict()
    pr['script'] = prefix
    pr['log'] = log
    pr['status'] = dict()
    pr['modules'] = modules.modules()

    for x in range(Loopcountsetup):
        print("TEST#{} of {}".format(x+1,Loopcountsetup))  
        for runtestCmd in runtestCmdlist:
            thread_list = list()
            loginfo_dict = dict()
            for TestUUT in TestUUTlist:
                loginfo_dict[TestUUT] = dict()
                pr['status'][TestUUT] = dict()
                thread = threading.Thread(target = runningtest, args = (pr,
                                                                        screenlogDir,
                                                                        TestUUT,
                                                                        testprogramDir,
                                                                        runtestCmd,
                                                                        loginfo_dict[TestUUT])
                                            )
                thread.daemon = True
                thread.start()
                thread_list.append(thread)
                time.sleep(2)

            # monitor all the thread
            while True:
                if len(thread_list) == 0:
                    break
                for thread in thread_list[:]:
                    if not thread.is_alive():
                        thread.join()
                        thread_list.remove(thread)
                time.sleep(5)    

            for TestUUT in loginfo_dict:
                print("TestUUT: {} in Loop {}".format(TestUUT,x+1))
                #print(loginfo_dict[TestUUT]['output'])
    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None

def runningtest(pr,screenlogDir,TestUUT,testprogramDir,runtestCmd,returnlog):
    runtest = runtest_modules.modules(pr['status'][TestUUT],screenlogDir,TestUUT,testprogramDir,runtestCmd)
    
    runtest.startRunchannel()
    #sys.stdout = log_modules.Logger(runtest.pexpectlog)
    runtest.SetupTestEnv()
    runtest.StartTest()
    runtest.MonitorTest()
    returnlog['output'] =runtest.output
    runtest.endchannel()    

if __name__ == "__main__":
    sys.exit(main())