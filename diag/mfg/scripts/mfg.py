#!/usr/bin/python3

from datetime import datetime
import argparse
import errno
import os
from os import listdir
from os.path import isfile, join
import re
import shutil
import subprocess
import sys
import shlex

#=============================
# mkdir -p
def mkdir_p(path):
    try:
        os.makedirs(path)
    # Python 2.5
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            print("mkdir_p failed")
            raise

def run_bash_cmd(cmd):
    cmd_list = shlex.split(cmd)
    result = subprocess.check_output(cmd_list)
    result_str = result.decode("utf-8")
    return result_str

class mfg:
    def __init__(self):
        self.cm_server = dict()
        self.cm_server["FML"] = "192.168.1.112"
        self.cm_server["FPN"] = "192.168.2.22"
        self.cm_server["FSN"] = "192.168.3.2"
        self.cm_server["PEN"] = "hw-mftg-data"
        self.user = "mfg"
        self.pwd  = "pensando"
        self.remote_path = "/mfg_log/"

    def fetch_remote(self, cm, card_type, stage, sn_list, logroot, tt_c):
        remote_ip = mfg.cm_server[cm]

        corner_4C = ['4C-H', '4C-L']
        for sn in sn_list:
            remote_path = ""
            # In case of no card_type specified, find it first
            if card_type == "":
                cmd = "sshpass -p 'pensando' ssh mfg@"+remote_ip+" find /mfg_log/ -name "+sn
                path_list = run_bash_cmd(cmd).split("\n")
                for path in path_list:
                    if stage == "4C":
                        print("Please specify card_type")
                        return
                    if stage in path:
                        card_type = path.split("/")[2]
                        sn1 = path.split("/")[4]
                        print("=== Card Type:", card_type, "===")
                        path1 = path.split("/")[:-1]
                        remote_path = '/'.join(path1)
                        print(remote_path)
                        break
            else:
                remote_path = self.remote_path+card_type+'/'+stage
            logroot1 = logroot+card_type+'/'+stage
            if stage == "4C":
                for corner in corner_4C:
                    remote_path1 = remote_path+'/'+corner+'/'+sn+'/'
                    logroot2 = logroot1+'/'+corner+'/'+sn+'/'
                    mkdir_p(logroot2)

                    cmd = "sshpass -p 'pensando' rsync -r mfg@"+remote_ip+":"+remote_path1+"* "+logroot2
                    print(cmd)
                    try:
                        subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')
                    except:
                        continue
                    subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')

            else:
                remote_path = remote_path+'/'+sn+'/'
                logroot1 = logroot1+'/'+sn+'/'
                #pathlib.Path(logroot).mkdir(parents=True, exist_ok=True)
                print(logroot1)
                mkdir_p(logroot1)

                cmd = "sshpass -p 'pensando' rsync -r mfg@"+remote_ip+":"+remote_path+"* "+logroot1
                #print(cmd)
                try:
                    subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')
                except:
                    continue

                test_time = tt_c
                if test_time == "all":
                    continue

                # Get timestamp of directory
                # Get first/last/all of the logs
                r = re.compile(r'.*MTP-[\d]+_([\d]+)-([\d]+)-([\d]+)_([\d]+)-([\d]+)-([\d]+).tar.gz')

                cur_pwd = os.getcwd()
                #print("cur_pwd:", cur_pwd)
                os.chdir(logroot1)

                print("Test time condition:", test_time)
                all_files = [f for f in listdir('.') if isfile(join('.', f))]
                find_file=""
                for log_file in all_files:
                    print(log_file)
                    m = r.match(log_file)
                    if m:
                        dtime = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)))
                        if find_file == "":
                            find_file = log_file
                            find_dtime = dtime
                        else:
                            if test_time == "first":
                                if dtime < find_dtime:
                                    find_dtime = dtime
                                    find_file = log_file
                            else:
                                if dtime > find_dtime:
                                    find_dtime = dtime
                                    find_file = log_file

                print(find_dtime)
                print(find_file)
                for log_file in all_files:
                    if log_file != find_file:
                        os.remove(log_file)
                os.chdir(cur_pwd)

    def fetch_remote_file(self, cm, card_type, stage, filename, fmode, logroot, tt_c):
        print("Using SN in file", filename)
        with open(filename) as f:
            sn_list = f.readlines()
        sn_list = [x.strip() for x in sn_list]
        print(sn_list)
        stage1 = stage
        card_type1 = card_type
        sn_list1 = []

        for sn in sn_list:
            sn = " ".join(sn.split())
            if fmode == "SN":
                sn_list1 = [sn]
            elif fmode == "SN_STAGE":
                sn1 = sn.split(" ")[0]
                stage1 = sn.split(" ")[1]
                print("===", sn1, stage1)
                if "4C" in stage1:
                    stage1 = "4C"
                sn_list1 = [sn1]
            elif fmode == "SN_TYPE_STAGE":
                sn1 = sn.split(" ")[0]
                card_type1 = sn.split(" ")[1]
                stage1 = sn.split(" ")[2]
                print("===", sn1, stage1)
                if "4C" in stage1:
                    stage1 = "4C"
                sn_list1 = [sn1]
            else:
                print("Invalid FMODE:", fmode)
                return

            mfg.fetch_remote(cm, card_type1, stage1, sn_list1, args.logroot, tt_c)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    group = parser.add_mutually_exclusive_group()

    parser.add_argument("-fetch", "--fetch", help="Fetch log file", action='store_true')

    group.add_argument("-cm", "--cm", help="CM site: FML/FPN/FSN/PEN", type=str, default="PEN")
    parser.add_argument("-sn", "--sn", help="Serial Number", type=str, default="")
    parser.add_argument("-fn", "--filename", help="File nmae with Serial Number", type=str, default="")
    parser.add_argument("-fmode", "--file_mode", help="File mode: SN only/SN_STAGE", type=str, default="SN")
    parser.add_argument("-sn_list", "--sn_list", help="Serial Number list", type=str, default="")
    parser.add_argument("-card_type", "--card_type", help="Serial ", type=str, default="")
    parser.add_argument("-stage", "--stage", help="Manufacture stage: DL/P2C/4C/SWI/FST", type=str, default="")
    parser.add_argument("-logroot", "--logroot", help="Path to log root folder", type=str, default="/home/xguo2/workspace/manufacture/mfg_log/")
    parser.add_argument("-tt_c", "--test_time_condition", help="Test time condition", type=str, default="all")

    args = parser.parse_args()
    
    mfg = mfg()

    stage = args.stage.upper()
    card_type = args.card_type.upper()
    cm = args.cm.upper()
    filename = args.filename
    fmode = args.file_mode.upper()

    logroot = args.logroot
    logroot = logroot+"/"

    sn_list1 = args.sn_list.upper()
    sn_list = sn_list1.split(',')
 
    tt_c = args.test_time_condition.lower()

    try:
        srv_ip = mfg.cm_server[cm]
        print(srv_ip)
    except KeyError:
        print("Invalid CM:", cm)
        sys.exit()
   
    #if filename != "":
    #    print("Using SN in file", filename)
    #    with open(filename) as f:
    #        sn_list = f.readlines()
    #    sn_list = [x.strip() for x in sn_list]
    #    print(sn_list)

    if args.fetch == True:
        if filename == "":
            mfg.fetch_remote(cm, card_type, stage, sn_list, logroot, tt_c)
            sys.exit()
        else:
            mfg.fetch_remote_file(cm, card_type, stage, filename, fmode, logroot, tt_c)
            sys.exit()

