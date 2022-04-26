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
import mysql_db
import script_logging
import modules
from logdef import KEY_WORD
from logdef import RUN_KEY

now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d_%H%M%S")
print("date and time:",date_time)

testprogramDir = "/home/winson/winson/worksapce/Ortano/testing/ortano_pilot_v1.41-rc2/mfg"

#runtestCmd = "./mfg_p2c_test.py"

#runtestCmd = "./mfg_swi_test.py"

screenlogDir = "/home/winson/winson/tmp/screenLog"

logDir = "/home/winson/winson/tmp/log/"

jsonrecordlogDir = "/home/winson/winson/tmp/json_log/"

#runtestCmdlist = ["./mfg_dl_test.py","./mfg_p2c_test.py","./mfg_4c_test.py --low-temp","./mfg_4c_test.py --high-temp","./mfg_swi_test.py"]

runtestCmdlist = ["./mfg_p2c_test.py"]

TestUUTlist = ["MTP-061","MTP-063"]
#TestUUTlist = ["MTP-208","MTP-207"]
Loopcountsetup = 1


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
    open_database(pr)

    #get_mtp_status_from_mfg_database(pr)
    #pr['modules'].print_anyinformation(RUN_KEY.checkstatus)
    #sys.exit()

    for x in range(Loopcountsetup):
        print("TEST#{} of {}".format(x+1,Loopcountsetup))  
        for runtestCmd in runtestCmdlist:
            thread_list = list()
            loginfo_dict = dict()
            for TestUUT in TestUUTlist:
                loginfo_dict[TestUUT] = dict()
                pr['status'][TestUUT] = dict()
                thread = threading.Thread(target = runningtest, args = (pr,
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

    # for TestUUT in loginfo_dict:
    #     print("TestUUT: {}".format(TestUUT))
    #     print(loginfo_dict[TestUUT]['output'])
    close_database(pr)
    pr['log'].WriteLine(str(pr))
    pr['log'].WriteLine(json.dumps(pr["status"], indent = 4))
    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None

def runningtest(pr,TestUUT,testprogramDir,runtestCmd,returnlog):
    wirtelogbyeachUUT(pr,TestUUT,"Start runningtest")
    runtest = runtest_modules.modules(pr['status'][TestUUT],screenlogDir,TestUUT,testprogramDir,runtestCmd)
    runtest.updatescriptlogmodule(pr['log'])
    wirtelogbyeachUUT(pr,TestUUT,runtest.check_screenlog())
    runtest.startRunchannel()
    #sys.stdout = log_modules.Logger(runtest.pexpectlog)
    if not runtest.SetupTestEnv():
        wirtelogbyeachUUT(pr,TestUUT,"Cannot find  [{}] in test config".format(TestUUT))
        wirtelogbyeachUUT(pr,TestUUT,"Test folder  [{}]".format(testprogramDir))
        wirtelogbyeachUUT(pr,TestUUT,"Test program [{}]".format(runtestCmd))
        runtest.update_failure_in_MTP()
        #return False
    runtest.StartTest()
    time.sleep(5)
    #runtest.StartTest()
    runtest.update_testing_in_MTP()
    while runtest.MonitorTest2():
        #print(runtest.output)
        #print(runtest.index)
        runtest.TakecardLastlinetoprovideresponce()
        checkresult = runtest.checkoutputstatus()
        #pr['modules'].print_anyinformation(checkresult)
        runtest.updateresultstatusbycheckpointdata(checkresult)
        #pr['modules'].print_anyinformation(runtest.status)

    
    checkresult = runtest.checkoutputstatus()
    #pr['modules'].print_anyinformation(checkresult)
    runtest.updateresultstatusbycheckpointdata(checkresult,TESTEND=True)
    if runtest.markfalse:
        runtest.update_failure_in_MTP()
    #pr['modules'].print_anyinformation(runtest.status)

    runtest.ShowspecialMessageinconsoleOutput()
    
    #runtest.update_test_result('PASS')
    returnlog['output'] =runtest.output
    runtest.endchannel()
    return True   

def wirtelogbyeachUUT(pr,TestUUT,message):
    firstmessage = "[{}] {}".format(TestUUT,message)
    pr['log'].WriteLine(firstmessage)
    return None

def get_mtp_status_from_mfg_database(pr):

    fields = ['mtp_id','mtp_status']
    infoindict = get_data_from_mfg_database(pr,'mtp_status',fields)

    print(json.dumps(infoindict, indent = 4))

    return infoindict


def get_data_from_mfg_database(pr,table,fields):
    if not 'db' in pr:
        open_database(pr)

    insertlist = list()
    insertsprint = fields[0]
    insertlist.append(fields[0])    
    for name in fields[1:]:
        print(name)
        insertsprint = insertsprint + "," + name 
        insertlist.append(name)
    
    query = "SELECT " + insertsprint + " FROM " + table
    values = list()

    fields = insertlist
    returndict = dict()

    if pr['db'].select_ret_dict(query, values, fields, returndict):
        print("ERROR:  Query failed {0}, {1}".format(query, insertdata[checklist[0]]))
        sys.exit()
        return -1

    print(json.dumps(returndict, indent = 4))

    return returndict

def open_database(pr):
    """ Open database."""
    db = mysql_db.mysql_db()

    if db.connect(username='prodmgr', pw='mgruser2wsx$RFV'):
        print("Error:  Failed to connect to db.")
        return -1
    else:
        print("Database opened: {0}".format(db.database))
        pr['log'].WriteLine("Database opened: {0}".format(db.database))

    pr['db'] = db
    return 0

def close_database(pr):
    """ Close database."""
    if 'db' in pr:
        pr['db'].disconnect()
        del pr['db']
    return 0

if __name__ == "__main__":
    sys.exit(main())