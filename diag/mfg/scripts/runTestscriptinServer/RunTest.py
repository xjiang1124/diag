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
import script_logging
import modules
from logdef import KEY_WORD
from logdef import RUN_KEY

now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d_%H%M%S")
from datetime import date
today = date.today()
todayday = today.strftime("%Y-%m-%d")
print("date and time:",date_time)

print(os.environ)

def main():

    start=datetime.now()

    #For Test only
    testprogramDir = "/home/winson/winson/worksapce/TAA/Production/psdiag/diag/mfg"
    runtestCmd = "./mfg_swi_test.py"
    screenlogDir = "/home/winson/winson/tmp/screenLog"
    logDir = "/home/winson/winson/tmp/log/"
    jsonrecordlogDir = "/home/winson/winson/tmp/json_log/"
    TestUUTlist = ["MTP-002","MTP-301","MTP-302","MTP-303"]
    ######

    """ main routine."""
    scriptname = os.path.basename(__file__)
    print("Starting {0}...".format(scriptname))
    pr = dict()
    pr['modules'] = modules.modules()

    temp_db = runtest_modules.db_modules()
    log_info = temp_db.get_data_on_table_from_mfg_database('log_info',returntype='list')
    log_info2 = temp_db.convert_list_to_dict(log_info,['name','path'])
    pr['modules'].print_anyinformation(log_info2)
    temp_db = None
    pr['loginfo'] = log_info2

    prefix = scriptname.replace('.py', '')
    if 'scriptLog' in pr['loginfo']:
        ldir = pr['loginfo']['scriptLog'] + '/' + prefix + '/' + todayday
        logDir = pr['loginfo']['scriptLog']
        screenlogDir = pr['loginfo']['log'] 
    else:
        ldir = logDir + '/' + prefix + '/' + todayday

    pr['ldir'] = ldir
    log = script_logging.Script_logging(
        log_dir=ldir, log_prefix=prefix, log_suffix='.log')
    if log.Open():
        print("Error: log failed to open, {0}".format(log.fullname))
        return -1
    if 'scriptLog' in pr['loginfo']:
        pr['modules'] = modules.modules(logmodule=log)
    
    pr['script'] = prefix
    pr['log'] = log
    pr['status'] = dict()
    pr['db'] = runtest_modules.db_modules(logmodule=log)
    pr['mtp_info'] = pr['db'].get_data_on_table_from_mfg_database('mtp_info')
    #pr['modules'].print_anyinformation(pr['mtp_info'])

    TestUUTlist = pr['db'].get_mtp_startTestlist_from_mfg_database()
    if len(TestUUTlist) > 10:
        TestUUTlist = TestUUTlist[:10]
    thread_list = list()
    loginfo_dict = dict()
    for TestUUT in TestUUTlist:
        start5=datetime.now()
        log.WriteLine("TEST UUT: {}".format(TestUUT))
        UUTinfo = pr['db'].get_one_mtp_status_from_mfg_database(TestUUT)
        pr['modules'].print_anyinformation(UUTinfo)
        scriptbasepath = pr['loginfo']['scriptPath']
        product_scriptpath = pr['db'].Get_test_exec_script_path(UUTinfo['product_id'])
        runtestCmd = pr['db'].Get_test_exec_script(UUTinfo['test_type'],UUTinfo['product_id'])
        eachtestprogramDir = scriptbasepath + product_scriptpath
        log.WriteLine("eachtestprogramDir: {}".format(eachtestprogramDir))
        log.WriteLine("runtestCmd: {}".format(runtestCmd))
        difftime = datetime.now()-start5
        log.WriteLine('Get information Time: {}'.format(difftime))

        loginfo_dict[TestUUT] = dict()
        pr['status'][TestUUT] = dict()

        thread = threading.Thread(target = runningtest, args = (pr,
                                                                TestUUT,
                                                                eachtestprogramDir,
                                                                screenlogDir,
                                                                runtestCmd,
                                                                loginfo_dict[TestUUT])
                                    )
        thread.daemon = True
        thread.start()
        thread_list.append(thread)
        time.sleep(2)

        #break

    # monitor all the thread
    while True:
        if len(thread_list) == 0:
            break
        for thread in thread_list[:]:
            if not thread.is_alive():
                thread.join()
                thread_list.remove(thread)
        time.sleep(5)    

    pr['log'].WriteLine(str(pr))
    difftime = datetime.now()-start
    pr['log'].WriteLine("Done Time: {}".format(difftime))  
    pr['log'].WriteLine("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None

def runningtest(mainpr,TestUUT,testprogramDir,screenlogDir,runtestCmd,returnlog):
    wirtelogbyeachUUT(mainpr,TestUUT,"Start runningtest")
    UUTinfo = mainpr['db'].get_one_mtp_status_from_mfg_database(TestUUT)
    mtp_info = dict()
    mtp_info['mtp_id'] = TestUUT

    pr = dict()
    scriptname = os.path.basename(__file__)
    prefix = scriptname.replace('.py', '')
    if 'scriptLog' in mainpr['loginfo']:
        ldir = mainpr['loginfo']['scriptLog'] + '/' + prefix + '/' + todayday + '/' + TestUUT
        logDir = mainpr['loginfo']['scriptLog']
        screenlogDir = mainpr['loginfo']['log'] 
    else:
        ldir = logDir + '/' + prefix + '/' + todayday
    log = script_logging.Script_logging(
        log_dir=ldir, log_prefix=prefix, log_suffix='.log')
    if log.Open():
        print("Error: log failed to open, {0}".format(log.fullname))
        return -1
    
    pr['modules'] = modules.modules(logmodule=log)
    
    pr['script'] = prefix
    pr['log'] = log
    pr['status'] = dict()
    pr['db'] = runtest_modules.db_modules(logmodule=log)

    runtest = runtest_modules.modules(mainpr['status'][TestUUT],screenlogDir,TestUUT,testprogramDir,runtestCmd)
    pr['db'].update_MTP_log_file(TestUUT,runtest.check_screenlog())
    runtest.updatescriptlogmodule(pr['log'])
    wirtelogbyeachUUT(pr,TestUUT,runtest.check_screenlog())
    runtest.startRunchannel()

    if not runtest.SetupTestEnv():
        wirtelogbyeachUUT(pr,TestUUT,"Cannot find  [{}] in test config".format(TestUUT))
        wirtelogbyeachUUT(pr,TestUUT,"Test folder  [{}]".format(testprogramDir))
        wirtelogbyeachUUT(pr,TestUUT,"Test program [{}]".format(runtestCmd))
        runtest.update_failure_in_MTP()
        runtest.update_status_in_database(pr,TestUUT)
    else:      
        runtest.StartTest()
        time.sleep(2)
        runtest.update_testing_in_MTP()
        runtest.update_status_in_database(pr,TestUUT)
        while runtest.MonitorTest2():
            if pr['db'].check_MTPSTOP_status(TestUUT):
                runtest.update_STOP_in_MTP()
                runtest.update_STOP_in_AllNic()
                runtest.STOPTest()
                break
            runtest.TakecardLastlinetoprovideresponce()
            checkresult = runtest.checkoutputstatus()
            runtest.updateresultstatusbycheckpointdata(checkresult)
            runtest.update_status_in_database(pr,TestUUT)

    if not runtest.mtpstop:
        checkresult = runtest.checkoutputstatus(theend=True)
        runtest.updateresultstatusbycheckpointdata(checkresult,TESTEND=True)
        runtest.check_all_NIC_STATUS_is_not_TESTING_in_AllNic()
    else:
        runtest.update_STOPDONE_in_MTP()
    if runtest.markfalse:
        runtest.update_failure_in_MTP()
    runtest.update_status_in_database(pr,TestUUT)

    runtest.ShowspecialMessageinconsoleOutput()

    #returnlog['output'] =runtest.output
    runtest.endchannel()

    pr['db'].update_MTP_end_time(TestUUT)

    pr['db'].push_result_to_history(TestUUT)

    return True   

def wirtelogbyeachUUT(pr,TestUUT,message):
    firstmessage = "[{}] {}".format(TestUUT,message)
    pr['log'].WriteLine(firstmessage)
    return None








if __name__ == "__main__":
    sys.exit(main())