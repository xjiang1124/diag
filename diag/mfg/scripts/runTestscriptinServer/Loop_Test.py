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

    #######################################################
    #For Test only
    testprogramDir = "/home/winson/winson/worksapce/TAA/Production/psdiag/diag/mfg"
    runtestCmd = "./mfg_swi_test.py"
    screenlogDir = "/home/winson/winson/tmp/screenLog"
    logDir = "/home/winson/winson/tmp/log/"
    jsonrecordlogDir = "/home/winson/winson/tmp/json_log/"
    TestUUTlist = ["MTP-113","MTP-210","MTP-212","MTP-213","MTP-221","MTP-222"]
    #TestUUTlist = ["MTP-113"]
    #######################################################

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

    thread_list = list()
    loginfo_dict = dict()
    MTPslot = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]
    for TestUUT in TestUUTlist:
        if not pr['db'].cheeck_mtp_status_by_keyword(TestUUT,'TESTING'):
            time.sleep(60)
            pr['log'].WriteLine("MTP: {} | IT is not in TESTING!".format(TestUUT))
            pr['db'].update_MTP_status(TestUUT,'STARTTEST')
            pr['db'].update_MTP_start_time(TestUUT)
            for nic_slot in MTPslot:
                pr['db'].update_one_nic_status_on_mtp_status(TestUUT,nic_slot,'MTPDONE')
        
    pr['log'].WriteLine(str(pr))
    difftime = datetime.now()-start
    pr['log'].WriteLine("Done Time: {}".format(difftime))  
    pr['log'].WriteLine("How many seconds use?: {} seconds".format(difftime.total_seconds()))       
    return None

def wirtelogbyeachUUT(pr,TestUUT,message):
    firstmessage = "[{}] {}".format(TestUUT,message)
    pr['log'].WriteLine(firstmessage)
    return None

if __name__ == "__main__":
    sys.exit(main())