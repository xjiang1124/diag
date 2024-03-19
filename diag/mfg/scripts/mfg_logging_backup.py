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

sys.path.append(os.path.relpath("/home/mfg/lib"))
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

    start=datetime.now()

    # get the absolute file path
    product_server_cfg_file = os.path.abspath("/home/mfg/config/pensando_pro_srv_cfg.yaml")

    # load the product server config
    pro_srv_cfg_db = pro_srv_db(pro_srv_cfg_file = product_server_cfg_file)
    pro_srv_list = list(pro_srv_cfg_db.get_pro_srv_id_list())

    for pro_srv_id in pro_srv_list:
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
        rsync_cmd = "rsync -H -t -r -v -e " + ssh_cmd + ":" + pro_srv_logpath + " " + "/mfg_log/"
        session = pexpect.spawn(rsync_cmd, encoding='utf-8')
        try:
            session.expect_exact("assword:")
        except pexpect.TIMEOUT:
            liblog_utils.email_report(email_to, pro_srv_id + ": Backup logging files failure", "RSYNC CMD: {}\n\n{}".format(rsync_cmd,session))
            continue

        session.sendline(srv_passwd)
        session.expect_exact(pexpect.EOF, timeout=None)

        output = session.before

        outputdict = gettransfersize(output)

        difftime = datetime.now()-start
        processtime = ("{} Use {} \n".format(pro_srv_id,difftime))
        if outputdict:
            processtime = ("{} Use {} | Received: {} MB | speed: {} MB/s\n".format(pro_srv_id,difftime,outputdict['received'],outputdict['spent']))
        if email_to:
            liblog_utils.email_report(email_to, pro_srv_id + ": Backup logging files complete", processtime + output)
        try:
            if ".tar.gz" in session.before:
                liblog_utils.email_report(email_to, pro_srv_id + ": New logs summary", liblog_utils.get_log_summary(session.before, pro_srv_logpath))
        except:
            pass

        #break

def gettransfersize(outputinformation):
    match = re.findall(r"sent\s+(\d.*\d)\s+bytes\s+received\s+(\d.*\d)\s+bytes\s+(\d.*\d)\s+bytes\/sec",outputinformation)
    outputdict = dict()
    outputdict['sent'] = 0
    outputdict['received'] = 0
    outputdict['spent'] = 0
    if match:
        #print(match[0])
        outputdict['sent'] = round(float(match[0][0].replace(',',''))/1048576,2)
        outputdict['received'] = round(float(match[0][1].replace(',',''))/1048576,2)
        outputdict['spent'] = round(float(match[0][2].replace(',',''))/1048576,2)
        #print(outputdict)
        return outputdict

    return None

if __name__ == "__main__":
    main()