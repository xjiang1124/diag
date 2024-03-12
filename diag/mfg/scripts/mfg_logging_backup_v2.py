#!/usr/bin/env python

import sys
import os
import time
import pexpect
import argparse
import re
import random
import subprocess
from datetime import datetime
import json

sys.path.append(os.path.relpath("/home/mfg/lib"))
#sys.path.append(os.path.relpath("lib"))
import liblog_utils
from liblog_cfg import *
from libpro_srv_db import pro_srv_db


def main():
    parser = argparse.ArgumentParser(description="Manufacture Logging File Backup Utility", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--email", help="email address the report will send to")
    email_to = None

    args = parser.parse_args()
    if args.email:
        email_to = args.email

    

    # get the absolute file path
    product_server_cfg_file = os.path.abspath("/home/mfg/config/pensando_pro_srv_cfg.yaml")
    #product_server_cfg_file = os.path.abspath("config/pensando_pro_srv_cfg.yaml")
    # load the product server config
    pro_srv_cfg_db = pro_srv_db(pro_srv_cfg_file = product_server_cfg_file)
    pro_srv_list = list(pro_srv_cfg_db.get_pro_srv_id_list())

    for pro_srv_id in pro_srv_list:
        start=datetime.now()
        pro_srv_mgmt_cfg = pro_srv_cfg_db.get_pro_srv_mgmt(pro_srv_id)
        pro_srv_logpath = pro_srv_cfg_db.get_pro_srv_logpath(pro_srv_id)

        srv_ipaddr = pro_srv_mgmt_cfg[0]
        srv_username = pro_srv_mgmt_cfg[1]
        srv_passwd = pro_srv_mgmt_cfg[2]
        
        ping_cmd = "ping {:s} -c 4".format(srv_ipaddr)

        output = subprocess.getstatusoutput(ping_cmd)

        findmatch = re.findall(r"\s(\d+)% packet loss",output[1])

        if findmatch:
            if findmatch[0] == '100':
                if email_to:
                    liblog_utils.email_report(email_to, pro_srv_id + ": Backup logging files failure", "PING TEST FAILURE\n{}".format(output[1]))
                continue

        ssh_cmd = "'ssh {:s}'".format(DIAG_SSH_OPTIONS) + " " + srv_username + "@" + srv_ipaddr 
        logserver_dir = "/mfg_log/"
        rsync_cmd = "rsync -u -t -r -a -v --dry-run -e " + ssh_cmd + ":" + pro_srv_logpath + " " + logserver_dir
        session = pexpect.spawn(rsync_cmd, encoding='utf-8')
        try:
            session.expect_exact("assword:")
        except pexpect.TIMEOUT:
            liblog_utils.email_report(email_to, pro_srv_id + ": Backup logging files failure", "RSYNC CMD: {}\n\n{}".format(rsync_cmd,session))
            continue

        session.sendline(srv_passwd)
        session.expect_exact(pexpect.EOF, timeout=None)

        output2 = session.before
        output2 = output2.replace('\r','\n')
        emailBody = output2
        workondata = dict()

        filecount = workingonfilelist(output2,workondata)

        #print(json.dumps(workondata, indent = 4))
        #print(output2)
        print("FILE COUNT: {}".format(filecount))
        print("FILE COUNT After process: {}".format(len(list(workondata.keys()))))
        emailBody = "FILE COUNT After process: {}\n{}".format(len(list(workondata.keys())),emailBody)
        emailBody = "FILE COUNT: {} \n{}".format(filecount,emailBody)
        #gettransfersize(output2)
        #sys.exit()
        if filecount:
            listofeachtransfer = list()
            for eachfile in workondata:
                dictofdata = dict()
                output30 = workonrsynceachfile(eachfile, workondata[eachfile], ssh_cmd, pro_srv_logpath, logserver_dir,srv_passwd,dictofdata)
                listofeachtransfer.append(dictofdata)
                emailBody += output30
                #if len(listofeachtransfer) > 10:
                    #break

            #sys.exit()
            listofreceived = list()
            listofspent = list()
            for eachoutput in listofeachtransfer:
                listofreceived.append(eachoutput['received'])
                listofspent.append(eachoutput['spent'])
            difftime = datetime.now()-start
            from statistics import mean
            processtime = ("{} Use {} | Received: {} MB | Ave. speed: {} MB/s | Max. speed {} MB/s\n".format(pro_srv_id,difftime,sum(listofreceived),round(mean(listofspent),2), max(listofspent)))
        else:
            difftime = datetime.now()-start
            processtime = ("{} Use {} \n".format(pro_srv_id,difftime))

        if email_to:
            liblog_utils.email_report(email_to, pro_srv_id + ": Backup logging files complete", processtime + emailBody)

        #break

    return None

def workonrsynceachfile(eachfile,eachdata, ssh_cmd, pro_srv_logpath, logserver_dir,srv_passwd,dictofdata):
    print(eachfile)
    print(eachdata)
    print(ssh_cmd)
    print(pro_srv_logpath)
    print(logserver_dir)
    rsync_cmd = "rsync -H -t -r -v -e " + ssh_cmd + ":" + pro_srv_logpath + eachdata[0] + " " + logserver_dir + eachdata[0]
    print(rsync_cmd)
    dir_path = os.path.dirname(eachdata[0])
    print(dir_path)
    createdirinserver(logserver_dir + dir_path)
    #sys.exit()
    output3 = run_rsync_cmd(rsync_cmd,srv_passwd)
    print(output3)
    gettransfersize(output3,dictofdata)

    if len(eachdata) > 1:
        for eachfile in eachdata[1:]:
            dir_path_locate = os.path.dirname(eachfile)
            createdirinserver(logserver_dir + dir_path_locate)
            rsync_cmd_locate = "rsync " + logserver_dir + eachdata[0] + " " + logserver_dir + dir_path_locate
            print(rsync_cmd_locate)
            run_rsync_cmd_locate(rsync_cmd_locate)
    #sys.exit()

    return rsync_cmd + "\n" + output3

def run_rsync_cmd_locate(rsync_cmd):
    session3 = pexpect.spawn(rsync_cmd, encoding='utf-8')
    session3.expect_exact(pexpect.EOF, timeout=None)

    output3 = session3.before
    print(output3)
    return output3

def run_rsync_cmd(rsync_cmd,srv_passwd):
    session2 = pexpect.spawn(rsync_cmd, encoding='utf-8')
    try:
        session2.expect_exact("assword:")
    except pexpect.TIMEOUT:
        pass

    session2.sendline(srv_passwd)
    session2.expect_exact(pexpect.EOF, timeout=None)

    output2 = session2.before
    return output2

def createdirinserver(createdir):
    mode = 0o777
    if not os.path.isdir(createdir):
        #os.mkdir(createdir, mode)
        os.makedirs(createdir)
        print("Directory '% s' created" % createdir)

    return None

def gettransfersize(outputinformation,dictofdata):
    match = re.findall(r"sent\s+(\d.*\d)\s+bytes\s+received\s+(\d.*\d)\s+bytes\s+(\d.*\d)\s+bytes\/sec",outputinformation)
    if match:
        #print(match[0])
        dictofdata['sent'] = round(float(match[0][0].replace(',',''))/1048576,2)
        dictofdata['received'] = round(float(match[0][1].replace(',',''))/1048576,2)
        dictofdata['spent'] = round(float(match[0][2].replace(',',''))/1048576,2)

    return None

def workingonfilelist(information,workondata):
    listofinformation = information.split("\n")
    Needtoworkonline = list()
    for eachline in listofinformation:
        if re.findall(r".*\/.*\w\.\w",eachline):
            Needtoworkonline.append(eachline)

    #print(Needtoworkonline)
    #workondata = dict()
    for eachlineagain in Needtoworkonline:
        if '=>' in eachlineagain:
            eachitems = eachlineagain.split()
            eachlineagain = eachitems[0]
        listofeachline = eachlineagain.split('/')
        workfile = listofeachline[-1]
        if not workfile in workondata:
            workondata[workfile] = list()
        if not eachlineagain in workondata[workfile]:
            workondata[workfile].append(eachlineagain)

    #print(json.dumps(workondata, indent = 4))
    #print("FILE COUNT: {}".format(len(Needtoworkonline)))
    #print("FILE COUNT After process: {}".format(len(workondata.keys())))
    filecount = len(Needtoworkonline)
    return filecount

if __name__ == "__main__":
    main()