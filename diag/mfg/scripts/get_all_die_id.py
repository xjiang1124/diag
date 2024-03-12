#!/usr/bin/python

import csv
import os, fnmatch
import tarfile
import shutil
import subprocess
import sys
#import xlwt

def find_file(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    if result == []:
        print("Can not find file!", pattern, path)
    return result

def find_dir(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            if fnmatch.fnmatch(dir_name, pattern):
                result.append(os.path.join(root, dir_name))
    if result == []:
        print("Can not find file!", pattern, path)

    return result

def find_first_dir(path):
    result = []
    for root, dirs, files in os.walk(path):
        #print path, root, dirs
        for dir_name in dirs:
            result.append(os.path.join(root, dir_name))

    if result == []:
        print("Can not find file!", path)

    return result

def untar(fname):
    if (fname.endswith("tar.gz")):
        tar = tarfile.open(fname, "r:gz")
        tar.extractall()
        tar.close()
    elif (fname.endswith("tar")):
        tar = tarfile.open(fname, "r:")
        tar.extractall()
        tar.close()

def get_dieId_sn(line):
    line_arr = line.split()
    ret = line_arr[len(line_arr)-1]
    return ret

def parse_asic_file(sn, file):
    dieId = "000000"
    for line in open(file):
        if (sn in line and "CAPRI ASIC_DIE_ID" in line and "cap_l1_screen_board" in line):
            dieId = get_dieId_sn(line)

    return dieId

#sn_list = ['FLM18510002']
log_root = "/mfg_log/"
log_root = "/home/xguo2/workspace/psdiag1/diag/mfg/scripts/mfg_log/"
card_list = ['NAPLES100/', 'NAPLES25/', 'VOMERO/']
card_list = ['NAPLES25/', 'VOMERO/']
stage = "P2C/"

cwd_top = os.getcwd()
try:
    shutil.rmtree(cwd_top+'/test_logs')
except os.error:
    print("no test_logs folder, will be created")

#print "Parsing error logs"
record_dict = dict()
for card in card_list:
    path = log_root+card+stage

    try:
        sn_list = os.listdir(path)
    except:
        continue

    new_record = dict()
    for sn in sn_list:
        dir_name = path+sn
        files_found = find_file('*gz', dir_name)
        #print files_found
        
        for file_fullname in files_found:
            dir_name1 = os.path.dirname(file_fullname)
            file_name = os.path.basename(file_fullname)
            print(file_fullname)
        
            tgt_dir = cwd_top+"/test_logs"
            if not os.path.exists(tgt_dir):
                os.mkdir(tgt_dir)
            os.chdir(cwd_top+"/test_logs")
        
            untar(file_fullname)

            cmd = 'grep -r -e '+sn+' -e "CAPRI ASIC_DIE_ID" * | grep cap_l1_screen_board | grep ASIC_DIE_ID > temp.log'
            os.system(cmd)

            tgt_msg = parse_asic_file(sn, "./temp.log")
            if tgt_msg != '000000':
                new_record[sn] = tgt_msg
                print(card[:-1], sn, tgt_msg)
            os.system("rm -rf "+cwd_top+"/test_logs/*")
        
            #print cwd_top
            os.chdir(cwd_top)
    
    record_dict[card[:-1]] = new_record

os.chdir(cwd_top)

# Output
f= open("die_id.log","w+")
f1= open("card_sn_die_id.log","w+")
fmt_str = "{:15}{:15}{:50}"
for card, sn_die_dict in record_dict.items():
    for sn, dieId in sn_die_dict.items():
        out_str = fmt_str.format(card, sn, dieId)
        #print out_str
        f1.write(out_str+'\n')
        f.write(dieId+'\n')
f.close()
f1.close()
