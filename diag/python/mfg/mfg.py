#!/usr/bin/env python

import argparse
import errno
import os
#import pathlib
#import pexpect
import re
import subprocess
import sys

sys.path.append("../lib")
import common

class mfg:
    def __init__(self):
        self.cm_server = dict()
        self.cm_server["FML"] = "192.168.1.112"
        self.cm_server["FPN"] = "192.168.2.22"
        self.cm_server["FSN"] = "192.168.3.11"
        self.cm_server["PEN"] = "hw-mftg-data"
        self.user = "mfg"
        self.pwd  = "pensando"
        self.remote_path = "/mfg_log/"
        self.local_path = "/home/adieckman/workspace/manufacture/mfg_log/"
        #self.local_path = "/vol/hw/diag/Naples25_2nd_Source_Qual_Build/mfg_log/"
        self.log_path = "/home/adieckman/workspace/manufacture/test_log/"

    def fetch_remote(self, cm, card_type, stage, sn_list):
        remote_ip = mfg.cm_server[cm]

        corner_4C = ['4C-H', '4C-L']
        for sn in sn_list:
            remote_path = self.remote_path+card_type+'/'+stage
            local_path = self.local_path+card_type+'/'+stage
            if stage == "4C":
                for corner in corner_4C:
                    remote_path1 = remote_path+'/'+corner+'/'+sn+'/'
                    local_path1 = local_path+'/'+corner+'/'+sn+'/'
                    common.mkdir_p(local_path1)

                    cmd = "sshpass -p 'pensando' rsync -r mfg@"+remote_ip+":"+remote_path1+"* "+local_path1
                    print(cmd)
                    try:
                        subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')
                    except:
                        continue
                    subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')

            else:
                remote_path = remote_path+'/'+sn+'/'
                local_path = local_path+'/'+sn+'/'
                #pathlib.Path(local_path).mkdir(parents=True, exist_ok=True)
                common.mkdir_p(local_path)

                cmd = "sshpass -p 'pensando' rsync -r mfg@"+remote_ip+":"+remote_path+"* "+local_path
                print(cmd)
                try:
                    subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')
                except:
                    continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    group = parser.add_mutually_exclusive_group()

    parser.add_argument("-fetch", "--fetch", help="Fetch log file", action='store_true')

    group.add_argument("-cm", "--cm", help="CM site: FML/FPN", type=str, default="FPN")
    parser.add_argument("-sn", "--sn", help="Serial Number", type=str, default="")
    parser.add_argument("-sn_list", "--sn_list", help="Serial Number list", type=str, default="")
    parser.add_argument("-card_type", "--card_type", help="Serial ", type=str, default="NAPLES100")
    parser.add_argument("-stage", "--stage", help="P2C", type=str, default="NAPLES100")

    args = parser.parse_args()
    
    mfg = mfg()

    cm = args.cm.upper()
    sn_list1 = args.sn_list.upper()
    sn_list = sn_list1.split(',')
    
    stage = args.stage.upper()
    card_type = args.card_type.upper()

    try:
        srv_ip = mfg.cm_server[cm]
        print(srv_ip)
    except KeyError:
        print("Invalid CM:", cm)
        sys.exit()


    if args.fetch == True:
        mfg.fetch_remote(cm, card_type, stage, sn_list)
        sys.exit()

