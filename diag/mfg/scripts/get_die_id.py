#!/usr/bin/python

import csv
import os, fnmatch
import tarfile
import shutil
import xlwt

def find_file(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    if result == []:
        print "Can not find file!", pattern, path
    return result

def find_dir(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            if fnmatch.fnmatch(dir_name, pattern):
                result.append(os.path.join(root, dir_name))
    if result == []:
        print "Can not find file!", pattern, path

    return result

def find_first_dir(path):
    result = []
    for root, dirs, files in os.walk(path):
        #print path, root, dirs
        for dir_name in dirs:
            result.append(os.path.join(root, dir_name))

    if result == []:
        print "Can not find file!", path

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

def parse_asic_file(file_list):

    l1_msg = []
    l1_found = 0
    l1_pass = 0

    die_id_num_lines = 16

    file_list.sort()
    for asic_log in file_list:
        if "l1_screen" in asic_log:
            l1_found = 1
            count_down = 0
            l1_msg.append("=== Die ID ===\n")
            for line in open(asic_log):
                if ("CAPRI ASIC_DIE_ID" in line):
                    count_down = die_id_num_lines
                if count_down != 0:
                    count_down = count_down - 1
                    l1_msg.append(line)
                    #print line

    return l1_msg

#with open('testfile.csv', newline='') as csvfile:
with open('flex_p2_chamber_failure.csv', 'rb') as csvfile:
    data = list(csv.reader(csvfile))

sn_list=[]
for i,row in enumerate(data):
    #print row[2], row[6], row[7], row[8], row[9]
    if (row[2] !='') and ("FLM" in row[2]):
        sn_list.append(row[2])

# Missing SN from "61"
sn_list = [
    "FLM18510012",
    "FLM1851001E",
    "FLM18510044",
    "FLM18510076",
    "FLM18510087",
    "FLM1851008F",
    "FLM185100DB",
    "FLM185100E1"
    ]
#sn_list = [
#    "FLM185100DB",
#    "FLM185100E1"
#    ]


#sn_list = ['FLM18510002']
log_root = "/mfg_log/"
card = 'NAPLES100/'
stage = "4C/"
corners = ['HTLV', 'HTHV', 'LTLV', 'LTHV']
corners = ['HTLV']

cwd_top = os.getcwd()
try:
    shutil.rmtree(cwd_top+'/test_logs')
except os.error:
    print "no test_logs folder"

sn_dict = dict()
print "Parsing error logs"
for sn in sn_list:
    pattern = '*'+sn+'*'
    corner_dict = dict()
    print sn
    for corner in corners:
        path = log_root+card+stage+corner
        dirs_found = find_dir(pattern, path)
        #print path, dirs_found
   
        err_msg = []
        for dir_name in dirs_found:
            files_found = find_file('*gz', dir_name)
            #print files_found
        
            for file_fullname in files_found:
                dir_name1 = os.path.dirname(file_fullname)
                file_name = os.path.basename(file_fullname)
                #print file_fullname
        
                tgt_dir = cwd_top+"/test_logs"
                if not os.path.exists(tgt_dir):
                    os.mkdir(tgt_dir)
                os.chdir(cwd_top+"/test_logs")
        
                untar(file_fullname)
        
                cwd_log = os.getcwd()
                corner_dirs = find_dir(corner+"*", cwd_log)
                for corner_dir in corner_dirs:
                    tgt_files = find_file(pattern, corner_dir)
                    #print tgt_files
                    err_msg.append(os.path.basename(corner_dir)+'\n') 
                    tgt_msg = parse_asic_file(tgt_files)
                    err_msg = err_msg + tgt_msg
       
                    shutil.rmtree(corner_dir)
                #print cwd_top
                os.chdir(cwd_top)

        corner_dict[corner] = err_msg 
    sn_dict[sn] = corner_dict

# Output
print "Printing error report"
for sn, corner_dict in sn_dict.iteritems():
    print "====================="
    print sn
    for corner, msg_list in corner_dict.iteritems():
        print "-------------"
        print corner
        for msg in msg_list:
            print msg
    print " "

