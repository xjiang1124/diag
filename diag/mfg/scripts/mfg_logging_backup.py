#!/usr/bin/env python

import sys
import os
import time
import pexpect
import argparse
import re
import random
import commands

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

        output = commands.getstatusoutput(ping_cmd)

        findmatch = re.findall(r"\s(\d+)% packet loss",output[1])

        if findmatch:
            if findmatch[0] == '100':
                if email_to:
                    liblog_utils.email_report(email_to, pro_srv_id + ": Backup logging files failure", "PING TEST FAILURE\n{}".format(output[1]))
                continue

        ssh_cmd = "'ssh {:s}'".format(DIAG_SSH_OPTIONS) + " " + srv_username + "@" + srv_ipaddr 
        rsync_cmd = "rsync -H -t -r -v -e " + ssh_cmd + ":" + pro_srv_logpath + " " + "/mfg_log/"
        session = pexpect.spawn(rsync_cmd)
        try:
            session.expect_exact("assword:")
        except pexpect.TIMEOUT:
            liblog_utils.email_report(email_to, pro_srv_id + ": Backup logging files failure", "RSYNC CMD: {}\n\n{}".format(rsync_cmd,session))
            continue

        session.sendline(srv_passwd)
        session.expect_exact(pexpect.EOF, timeout=None)
        if email_to:
            liblog_utils.email_report(email_to, pro_srv_id + ": Backup logging files complete", session.before)
        try:
            if ".tar.gz" in session.before:
                liblog_utils.email_report(email_to, pro_srv_id + ": New logs summary", liblog_utils.get_log_summary(session.before, pro_srv_logpath))
        except:
            pass


if __name__ == "__main__":
    main()