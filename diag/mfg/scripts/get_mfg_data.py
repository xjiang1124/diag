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
    summary_msg = []
    asic_pass = 1

    pcie_prbs_msg = []
    pcie_prbs_found = 0
    pcie_prbs_pass = 0

    eth_prbs_msg = []
    eth_prbs_found = 0
    eth_prbs_pass = 0

    l1_msg = []
    l1_found = 0
    l1_pass = 0

    file_list.sort()
    for asic_log in file_list:

        #print asic_log
        if "pcie_prbs" in asic_log:
            pcie_prbs_found = 1
            pass_count = 0
            sign_count = 0
            pcie_prbs_msg.append("=== PCIE PRBS Details ===\n")
            for line in open(asic_log):
                if (
                    "ERROR" in line or 
                    "error \"Operation timed out\"" in line or 
                    "ssi_check_timeout" in line
                   ):
                    pcie_prbs_msg.append(line)
                if "MSG :: pen_aapl_prbs_check :: sbus_addr" in line:
                    sign_count = sign_count + 1
                    if "passed" in line:
                        pass_count = pass_count + 1
            if pass_count == 16:
                summary_msg.append("=== PCIE PRBS Passed ===\n")
                pcie_prbs_pass = 1
            else:
                summary_msg.append("=== PCIE PRBS Failed ===\n")
            if sign_count != 16:
                summary_msg.append("=== PCIE PRBS Did Not Finish ===\n")
    
        if "eth_prbs" in asic_log:
            eth_prbs_found = 1
            pass_count = 0
            sign_count = 0
            eth_prbs_msg.append("=== ETH PRBS Details ===\n")
            for line in open(asic_log):
                if (
                    "ERROR" in line or 
                    "Operation timed out" in line or 
                    "ssi_check_timeout" in line
                   ):
                    eth_prbs_msg.append(line)
                if "MSG :: pen_aapl_prbs_check :: sbus_addr" in line:
                    sign_count = sign_count + 1
                    if "passed" in line:
                        pass_count = pass_count + 1
                        #print line+"\n"
    
            # 10G and 25G
            if pass_count == 16:
                summary_msg.append("=== ETH PRBS Passed ===\n")
                eth_prbs_pass = 1
            else:
                summary_msg.append("=== ETH PRBS Failed ===\n")
            if sign_count != 16:
                summary_msg.append("=== ETH PRBS Did Not Finish {} ===\n".format(sign_count))
    
        if "l1_screen" in asic_log:
            l1_found = 1
            l1_msg.append("=== L1 Details ===\n")
            for line in open(asic_log):
                if (
                    "ERROR" in line or 
                    "operation timed out" in line or 
                    "ssi_check_timeout" in line or
                    "L1_SCREEN" in line or 
                    "#FAIL#" in line or
                    "domain error: argument not in valid range" in line
                    ):
                    #print tgt_files
                    #print line
                    l1_msg.append(line)
                if "L1_SCREEN PASSED" in line:
                    l1_pass = 1
                    summary_msg.append("=== L1 Passed ===\n")
                if "L1_SCREEN FAILED" in line:
                    summary_msg.append("=== L1 Failed ===\n")

        if os.stat(asic_log).st_size == 0:
            summary_msg.append("=== "+asic_log+" has 0 size ===")

    if "L1_SCREEN" not in ''.join(l1_msg):
        summary_msg.append("=== L1 Did Not Finish ===\n")

    if pcie_prbs_found == 0:
        summary_msg.append("=== PCIE PRBS log not found ===\n")
    if eth_prbs_found == 0:
        summary_msg.append("=== ETH PRBS log not found ===\n")
    if l1_found == 0:
        summary_msg.append("=== L1 log not found ===\n")

    tgt_msg = summary_msg
    if pcie_prbs_pass == 0:
        asic_pass = 0
        tgt_msg.append("---------------------------------\n")
        tgt_msg = tgt_msg + pcie_prbs_msg
    if eth_prbs_pass == 0:
        asic_pass = 0
        tgt_msg.append("---------------------------------\n")
        tgt_msg = tgt_msg + eth_prbs_msg
    if l1_pass == 0:
        asic_pass = 0
        tgt_msg.append("---------------------------------\n")
        tgt_msg = tgt_msg + l1_msg

    return tgt_msg, asic_pass

def parse_mtp_file(file_list):
    tgt_msg = []

    mtp_msg = []
    mtp_log_found = 0

    for asic_log in file_list:
        mtp_log_found = 1
        mtp_msg.append("=== MTP Log Details ===\n")
        for line in open(asic_log):
            if (
                "error \"Operation timed out\"" in line or 
                "procedure \"ssi_check_timeout\"" in line or
                "procedure \"ssi_rx\"" in line or
                "procedure \"ssi_cpld_write\" line" in line or
                "procedure \"ssi_cpld_read\" line" in line or
                "procedure \"cap_jtag_chip_rst\"" in line or
                "\"cap_power_cycle_chk" in line or
                "\"cap_esec_chamber_loop" in line or
                "domain error: argument not in valid range" in line
                ):
                mtp_msg.append(line)

        tgt_msg.append("---------------------------------\n")
        tgt_msg = tgt_msg + mtp_msg

    return tgt_msg

#with open('testfile.csv', newline='') as csvfile:
with open('flex_p2_chamber_failure.csv', 'rb') as csvfile:
    data = list(csv.reader(csvfile))

sn_list=[]
for i,row in enumerate(data):
    #print row[2], row[6], row[7], row[8], row[9]
    if (row[2] !='') and ("FLM" in row[2]):
        sn_list.append(row[2])

sn_list = ['FLM18510002']
log_root = "/mfg_log/"
card = 'NAPLES100/'
stage = "4C/"
corners = ['HTLV', 'HTHV', 'LTLV', 'LTHV']
#corners = ['LTLV']

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
                    tgt_msg, asic_pass = parse_asic_file(tgt_files)
                    err_msg = err_msg + tgt_msg

                    if asic_pass != 1:
                        tgt_files = find_file("mtp_diag.log", corner_dir)
                        tgt_msg = parse_mtp_file(tgt_files)
                        err_msg = err_msg + tgt_msg
       
                    #shutil.rmtree(corner_dir)
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

# Write to csv file
print "Write to spreadsheet"
book = xlwt.Workbook()

algn1 = xlwt.Alignment()
algn1.wrap = 1
style1 = xlwt.XFStyle()
style1.alignment = algn1

sh = book.add_sheet("Error Report")
sh.write(0, 0, "SN")
sh.write(0, 1, "HTLV")
sh.write(0, 2, "HTHV")
sh.write(0, 3, "LTLV")
sh.write(0, 4, "LTHV")

row_idx = 1
for sn, corner_dict in sn_dict.iteritems():
    sh.write(row_idx, 0, sn)
    for corner_idx in range(len(corners)):
        msg_list = corner_dict[corners[corner_idx]]
        output=''.join(msg_list)
        #print output
        if output == '':
            output = "Not Tested"
        sh.write(row_idx, corner_idx+1, output, style1) 
    row_idx = row_idx + 1

    book.save("error_report.xls")




