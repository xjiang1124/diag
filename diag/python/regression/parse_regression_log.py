#!/usr/bin/python

import argparse
import os, fnmatch
import tarfile
import shutil

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

def parse_asic_file1(file_list):
    summary_msg = []

    pcie_prbs_found = 0
    pcie_prbs_pass = 0

    eth_prbs_found = 0
    eth_prbs_pass = 0

    l1_found = 0
    l1_pass = 0

    file_list.sort()
    for asic_log in file_list:

        #print asic_log
        if "pcie_prbs" in asic_log:
            pcie_prbs_found = 1
            pass_count = 0
            sign_count = 0
            for line in open(asic_log):
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
            for line in open(asic_log):
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
            for line in open(asic_log):
                if "L1_SCREEN PASSED" in line:
                    l1_pass = 1
                    summary_msg.append("=== L1 Passed ===\n")
                if "L1_SCREEN FAILED" in line:
                    summary_msg.append("=== L1 Failed ===\n")

        if os.stat(asic_log).st_size == 0:
            summary_msg.append("=== "+os.path.basename(asic_log)+" has 0 size ===\n")

    if ("L1 Passed" not in ''.join(summary_msg)) and ("L1 Failed" not in ''.join(summary_msg)):
        summary_msg.append("=== L1 Did Not Finish ===\n")

    if pcie_prbs_found == 0:
        summary_msg.append("=== PCIE PRBS log not found ===\n")
    if eth_prbs_found == 0:
        summary_msg.append("=== ETH PRBS log not found ===\n")
    if l1_found == 0:
        summary_msg.append("=== L1 log not found ===\n")

    tgt_msg = summary_msg

    return tgt_msg, pcie_prbs_pass, eth_prbs_pass, l1_pass

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
            summary_msg.append("=== "+os.path.basename(asic_log)+" has 0 size ===\n")

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

def parse_dsp_log(file_list, sn, pcie_prbs, eth_prbs, l1):
    tgt_msg = []

    dsp_msg = []
    dsp_log_found = 0
    parse_en = 0
    jtag_found = 0

    sig_pcie_start = ["PCIE_PRBS"]
    sig_eth_start = ["ETH_PRBS"]
    sig_l1_start = ["L1"]
    sig_start = []
    if pcie_prbs == 0:
        sig_start = sig_start + sig_pcie_start
    if eth_prbs == 0:
        sig_start = sig_start + sig_eth_start
    if l1 == 0:
        sig_start = sig_start + sig_l1_start


    sig_common = ["ERROR ::"]
    sig_l1 = ["L1_SCREEN", "#FAIL#", "domain error: argument not in valid range"]
    sig_timeout = [
                    "error \"Operation timed out\"", 
                    "procedure \"ssi_check_timeout\"",
                    "procedure \"ssi_rx\"",
                    "procedure \"ssi_cpld_write\" line",
                    "procedure \"ssi_cpld_read\" line",
                    "procedure \"cap_jtag_chip_rst\"",
                    "\"cap_power_cycle_chk",
                    "\"cap_esec_chamber_loop",
                    "domain error: argument not in valid range",
                  ]
    sig_jtag = [ "max retry reached!",
                 "Failure. Frame was corrupted",
                 "Corrupted data:"
               ] 

    sig_all = sig_common + sig_l1 + sig_timeout

    sig_ignore = ["IN_ETH_ERROR", "IN_TDMA_ERROR", "OUT_ETH_ERROR", "OUT_TDMA_ERROR"]

    #print "parse_dsp_log", file_list, sn
    for dsp_log in file_list:
        dsp_log_found = 1
        dsp_msg.append("=== ASIC log Details: "+sn+" ===\n")
        index = 0
        with open(dsp_log, 'r+') as f:
            for line in f:
                index = index + 1
                if "TEST STARTED" in line:
                    for sig in sig_start:
                        if sig in line:
                            f.next()
                            line_next = f.next()
                            line_nnext = f.next()
                            if sn in line_next or sn in line_nnext:
                                parse_en = 1
                                dsp_msg.append(line)

                if "TEST DONE" in line:
                    parse_en = 0

                if parse_en == 1:
                    for sig in sig_all:
                        if sig in line:
                            dsp_msg.append(line)
                    if "max retry reached!" in line:
                        if jtag_found == 0:
                            dsp_msg.append(line)
                            f.next()
                            dsp_msg.append(f.next())
                            dsp_msg.append(f.next())
                            f.next()
                            jtag_found = 1
                    else:
                        jtag_found = 0


        dsp_msg.append("---------------------------------\n")

    return dsp_msg

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
                "domain error: argument not in valid range" in line or
                "Failure. Frame was corrupted" in line
                ):
                mtp_msg.append(line)

        tgt_msg.append("---------------------------------\n")
        tgt_msg = tgt_msg + mtp_msg

    return tgt_msg

parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
group = parser.add_mutually_exclusive_group()
parser.add_argument("-sn", "--sn", help="Serial number", type=str, default="")
parser.add_argument("-log", "--log_file", help="Log file name", type=str, default="")
args = parser.parse_args()

sn = args.sn
file_fullname = args.log_file

#sn = "FLM185100DB"
#file_fullname = "/vol/hw/diag/diag_qa/regression_log/2019-02-23/LTHV_MTP-010_2019-02-23_10-15-03_mtp_regression.4.tar.gz"

cwd_top = os.getcwd()
try:
    shutil.rmtree(cwd_top+'/test_logs')
except os.error:
    print "no test_logs folder"

cwd_log = cwd_top+"/test_logs"
if not os.path.exists(cwd_log):
    os.mkdir(cwd_log)
os.chdir(cwd_log)
 
print "Parsing error logs"

dir_name1 = os.path.dirname(file_fullname)
file_name = os.path.basename(file_fullname)
#print file_fullname

tgt_dir = cwd_top+"/test_logs/"+sn+"/"
if not os.path.exists(tgt_dir):
    os.mkdir(tgt_dir)
os.chdir(tgt_dir)

untar(file_fullname)

cwd_log = os.getcwd()
corner_dirs = find_dir("*MTP*", cwd_log)
err_msg = []
for corner_dir in corner_dirs:
    pattern = "*"+sn+"*"
    tgt_files = find_file(pattern, corner_dir)
    #print tgt_files
    err_msg.append(os.path.basename(corner_dir)+'\n') 
    tgt_msg, pcie_prbs_pass, eth_prbs_pass, l1_pass = parse_asic_file1(tgt_files)
    err_msg = err_msg + tgt_msg

    if pcie_prbs_pass == 0 or eth_prbs_pass == 0 or l1_pass == 0:
        log_files = find_file("log_ASIC.txt", corner_dir)
        dsp_msg = parse_dsp_log(log_files, sn, pcie_prbs_pass, eth_prbs_pass, l1_pass)
        err_msg = err_msg + dsp_msg
os.chdir(cwd_top)

# Output
print "Printing error report"
for msg in err_msg:
    print msg




