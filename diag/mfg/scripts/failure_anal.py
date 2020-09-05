#!/usr/bin/python

import csv
import errno
import os, fnmatch
import tarfile
import shutil
import subprocess
import sys
import shlex
import subprocess
#import xlwt
import pandas as pd
import xlrd
import numpy
import argparse
import re
import collections
from pathlib import Path
import shlex

try:
    import cPickle as pickle
except ImportError:  # python 3.x
    import pickle

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

def run_bash_cmd(cmd):
    cmd_list = shlex.split(cmd)
    result = subprocess.check_output(cmd_list)
    result_str = result.decode("utf-8")
    return result_str

def rm_cmd(path):
    fmt_cmd = "rm -rf {}" 
    cmd = fmt_cmd.format(path)
    ret = run_bash_cmd(cmd)
    print(ret)

def get_dieId_sn(line):
    line_arr = line.split()
    ret = line_arr[len(line_arr)-1]
    return ret

def get_err_code(err_info):
    if "HV_" in err_info and "LV_" in err_info:
        volt_lvl = "HV_LV"
    elif "HV_" in err_info:
        volt_lvl = "HV"
    elif "LV_" in err_info:
        volt_lvl = "LV"
    else:
        volt_lvl = ""

    if "booted from goldfw" in err_info:
        err_code = "BOOT_GOLDFW"
    elif "Retrieve NIC FRU failed" in err_info:
        err_code = "RD_FRU"
    elif "AVS_SET FAILED" in err_info:
        err_code = "AVS"
    elif "Init NIC boot info failed" in err_info:
        err_code = "NIC_BOOT_FAIL"
    elif "Program NIC FRU failed" in err_info:
        err_code = "PROG_NIC_FRU"
    elif "Bad Component" in err_info:
        err_code = "COMP_DEFECT"
    elif "Program Wrong" in err_info:
        err_code = "PROG_WRONG"
    elif "Knockoff" in err_info:
        err_code = "COMP_KNOCKOFF"
    elif "Component Loose" in err_info:
        err_code = "COMP_LOOSE"
    elif "Component Damaged" in err_info:
        err_code = "COMP_DEFECT"
    elif "Component Misaligned" in err_info:
        err_code = "COMP_MISALIGN"
    elif "Component Electrical Failure" in err_info:
        err_code = "COMP_ELEC"
    elif "Component Missing" in err_info:
        err_code = "COMP_MISS"
    elif "Component Height" in err_info:
        err_code= "COMP_HEIGHT"
    elif "Comp_Marginal_Value" in err_info:
        err_code = "COMP_MARGINAL"
    elif "Component Wrong" in err_info:
        err_code = "COMP_WRONG"
    elif "Component Burnt" in err_info:
        err_code = "COMP_BURNT"
    elif "Wrong Orientation" in err_info:
        err_code = "WRONG_ORNT"
    elif "NDF" in err_info:
        err_code = "NDF"
    elif "L1" in err_info:
        err_code = "L1"
        if "hbm_test" in err_info:
            err_code = err_code + "_HBM"
        elif "esec_l1_test" in err_info:
            err_code = err_code + "_ESEC"
        elif "Cmd failed" in err_info:
            err_code = err_code + "_CMD"
        else:
            print(err_info)
    elif "ETH_PRBS" in err_info:
        err_code = "ETH_PRBS"
    elif "PCIE_PRBS" in err_info:
        err_code = "PCIE_PRBS"
    elif "SNAKE_PCIE" in err_info:
        err_code = "SNAKE_PCIE"
    elif "SNAKE_HBM" in err_info:
        err_code = "SNAKE_HBM"
    elif "MVL STUB FAIL" in err_info:
        err_code = "MVL"
    elif "RTC FAIL" in err_info:
        err_code = "RTC"
    elif "ERROR: MTP ADAPTER SCAN CHAIN" in err_info:
        err_code = "ADPT_SCAN_CHAIN"
    elif "Contamination" in err_info:
        err_code = "CONTAMINATION"
    elif "Solder" in err_info:
        err_code = "SOLDER"
    elif "Init NIC EMMC" in err_info:
        err_code = "INIT_NIC_EMMC"
    elif "Flex Pad Lifted" in err_info:
        err_code = "FLEX_PAD"
    elif "PRE_CHECK NIC_JTAG FAIL" in err_info:
        err_code = "NIC_JTAG"
    elif "PRE_CHECK NIC_ALOM_CABLE FAIL" in err_info:
        err_code = "ALOM_CABLE"
    elif "Copy NIC Diag Image failed" in err_info:
        err_code = "COPY_NIC_IMAGE_FAIL"
    elif "Program NIC Secure Key failed" in err_info:
        err_code = "KEY_PROG_FAIL"
    elif "Pre init key programming failed" in err_info:
        err_code = "PRE_KEY_PROG_FAIL"

    # ICT error code
    elif "Test Point" in err_info:
        err_code = "TEST_POINT"
    elif "Shorted Continuity" in err_info:
        err_code = "SHORT_CONTINUITY"
    elif "Lifted Lead" in err_info:
        err_code = "LIFT_LEAD"
    elif "Component Reversed" in err_info:
        err_code = "COMP_REV"
    elif "Extra Part" in err_info:
        err_code = "EXTRA_PART"
    elif "Bad Rework" in err_info:
        err_code = "BAD_REWORK"
    elif "Gold finger Damaged" in err_info:
        err_code = "GOLD_FNGR_DMG"
    else:
        err_code = "UNKNOWN"
        print("Unknown error code!")
        print(err_info)

    err_code = err_code+","+volt_lvl
    return err_code

def parse_yield_file(filename, prefix, log_root, cm, stage_list, first_yield, fetch, verbose):
    if "SWM" in filename:
        card_type = "NAPLES25SWM"
    elif "100" in filename:
        card_type = "NAPLES100"
    else:
        card_type = "UNKNOWN"
    
    xls = pd.ExcelFile(filename)
    sheet = xls.parse('RCCA')
    wk_list = sheet['WW']
    fail_dsrp_list = sheet['Failure Description']
    stage_list = sheet['Impacted Station ']
    sn_list = sheet['Serial No']
    location_list = sheet['Location ']
    root_cause_list = sheet['Root Cause ']
    action_list = sheet['ACTION']

    f_dl  = open(prefix+"_"+card_type.lower()+"_dl.txt","w+")
    f_4c  = open(prefix+"_"+card_type.lower()+"_4c.txt","w+")
    f_p2c = open(prefix+"_"+card_type.lower()+"_p2c.txt","w+")
    f_swi = open(prefix+"_"+card_type.lower()+"_swi.txt","w+")
    f_fst = open(prefix+"_"+card_type.lower()+"_fst.txt","w+")

    stage_new_list = []
    record_dict = dict()
    ict_sn_dict = dict()
    dl_sn_dict  = dict()
    p2c_sn_dict = dict()
    h4c_sn_dict = dict()
    l4c_sn_dict = dict()
    swi_sn_dict = dict()
    fst_sn_dict = dict()

    for idx, sn in sn_list.items():
        stage_new_list.append("NA")
        if pd.isna(sn) == True or pd.isna(fail_dsrp_list[idx]) == True:
            break

        # Temp solution: Penang yield report has extra records of old data
        if idx < 1640:
            continue

        stage = "NA"
        fail_dsrp = fail_dsrp_list[idx]
        wk = wk_list[idx]
        if "DOWNLOAD" in stage_list[idx]:
            stage = "DL"
        elif "P2C" in stage_list[idx]:
            stage = "P2C"
        #elif "5C" in stage_list[idx]:
        #    stage = "4C"
        elif "4C-H" in stage_list[idx]:
            stage = "4C-H"
        elif "4C-L" in stage_list[idx]:
            stage = "4C-L"
        elif "SWI" in stage_list[idx]:
            stage = "SWI"
        elif "FST" in stage_list[idx]:
            stage = "FST"
        elif "ICT" in stage_list[idx]:
            stage = "ICT"
        else:
            #print("Skip stage", idx, stage_list[idx])
            continue

        stage_new_list[idx] = stage

        if "Diagnostic Software Problem" in fail_dsrp:
            if stage == "DL":
                f_dl.write(sn+'\n')
            if stage == "P2C":
                f_p2c.write(sn+'\n')
            if stage == "4C-L":
                f_4c.write(sn+'\n')
            if stage == "4C-H":
                f_4c.write(sn+'\n')
            if stage == "SWI":
                f_swi.write(sn+'\n')
            if stage == "FST":
                f_fst.write(sn+'\n')
        else:
            err_info_dict = dict()
            stage_err_info_dict = dict()
            err_info_dict["ERR_INFO"] = fail_dsrp_list[idx]
            err_info_dict["ERR_CODE"] = get_err_code(fail_dsrp_list[idx])
            stage_err_info_dict[stage+"_GENERAL"] = err_info_dict

            if stage == "ICT":
                ict_sn_dict[sn] = stage_err_info_dict
            if stage == "DL":
                dl_sn_dict[sn] = stage_err_info_dict
            if stage == "P2C":
                p2c_sn_dict[sn] = stage_err_info_dict
            if stage == "4C-L":
                l4c_sn_dict[sn] = stage_err_info_dict
            if stage == "4C-H":
                h4c_sn_dict[sn] = stage_err_info_dict
            if stage == "SWI":
                swi_sn_dict[sn] = stage_err_info_dict
            if stage == "FST":
                fst_sn_dict[sn] = stage_err_info_dict

            err_info_dict["LOCATION"] = location_list[idx]
            err_info_dict["ROOT CAUSE"] = root_cause_list[idx]
            err_info_dict["ACTION"] = action_list[idx]

    record_dict["ICT"]  = ict_sn_dict
    record_dict["DL"]   = dl_sn_dict
    record_dict["P2C"]  = p2c_sn_dict
    record_dict["4C-H"] = h4c_sn_dict
    record_dict["4C-L"] = l4c_sn_dict
    record_dict["SWI"]  = swi_sn_dict
    record_dict["FST"]  = fst_sn_dict

    f_dl.close()
    f_p2c.close()
    f_4c.close()
    f_swi.close()
    f_fst.close()

    if args.fetch == True:
        sys.exit(0)
   
    cwd_top = os.getcwd()
    try:
        shutil.rmtree(cwd_top+'/test_logs')
    except os.error:
        print("no test_logs folder, will be created")

    #stage_tgt_list = ["DL"]
    stage_tgt_list = args.stage_list.upper().split(",")

    record_diag_dict = dict()
    for stage_tgt in stage_tgt_list:

        stage_sn_dict = dict()
        for idx, sn in sn_list.items():

            # Temp solution: Penang yield report has extra records of old data
            if idx < 1640:
                continue

            if pd.isna(sn) == True or pd.isna(fail_dsrp_list[idx]) == True:
                break

            if stage_new_list[idx] != stage_tgt:
                continue

            if "Diagnostic Software Problem" not in fail_dsrp_list[idx]:
                continue

            if "4C" in stage_tgt:
                path = log_root+card_type+"/4C/"+stage_tgt+"/"
            else:
                path = log_root+card_type+"/"+stage_tgt+"/"
            #print(path)

            dir_name = path+sn
            #print(dir_name)
            files_found = find_file('*gz', dir_name)

            if files_found == []:
                print(sn, "No log file found")
                err_info_dict = dict()
                stage_err_info_dict = dict()
                err_info_dict["ERR_INFO"] = "LOG_NOT_FOUND"
                err_info_dict["ERR_CODE"] = "LOG_NOT_FOUND"
                stage_err_info_dict[stage+"_GENERAL"] = err_info_dict
                stage_sn_dict[sn] = stage_err_info_dict

                err_info_dict["LOCATION"] = location_list[idx]
                err_info_dict["ROOT CAUSE"] = root_cause_list[idx]
                err_info_dict["ACTION"] = action_list[idx]
                continue

            if args.first_yield == True:
                log_time_list = []
                for idx, file_fullname in enumerate(files_found):
                    dir_name1 = os.path.dirname(file_fullname)
                    file_name = os.path.basename(file_fullname)

                    m = re.compile("^([\D\d]+)_(MTP[S]*-\d+)_(\d\d\d\d)-(\d\d)-(\d\d)_(\d\d)-(\d\d)-(\d\d).*")
                    result = m.match(file_name)

                    log_file_dict = dict()
                    log_file_dict["STAGE"]  = result.group(1)
                    log_file_dict["MTP_NO"] = result.group(2)
                    log_file_dict["YEAR"]   = result.group(3)
                    log_file_dict["MONTH"]  = result.group(4)
                    log_file_dict["DAY"]    = result.group(5)
                    log_file_dict["HOUR"]   = result.group(6)
                    log_file_dict["MIN"]    = result.group(7)
                    log_file_dict["SEC"]    = result.group(8)
                    log_time = "{}-{}-{}-{}-{}".format(log_file_dict["YEAR"], log_file_dict["MONTH"],log_file_dict["DAY"],log_file_dict["HOUR"], log_file_dict["MIN"])
                    log_time_list.append(log_time)
                first_log_time="9999-99-99-99-99"
                first_log_time_idx=0
                for i in range(len(log_time_list)):
                    if log_time_list[i] < first_log_time:
                        first_log_time = log_time_list[i]
                        first_log_time_idx = i

                files_found = [files_found[first_log_time_idx]]

            stage_err_info_dict = dict()

            for file_fullname in files_found:
                dir_name1 = os.path.dirname(file_fullname)
                file_name = os.path.basename(file_fullname)
                #print(file_fullname)
            
                tgt_dir = cwd_top+"/test_logs"
                if not os.path.exists(tgt_dir):
                    os.mkdir(tgt_dir)
                os.chdir(cwd_top+"/test_logs")
            
                untar(file_fullname)

                #print(file_name)
                m = re.compile("^([\D\d]+)_(MTP[S]*-\d+)_(\d\d\d\d)-(\d\d)-(\d\d)_(\d\d)-(\d\d)-(\d\d).*")
                result = m.match(file_name)

                log_file_dict = dict()
                log_file_dict["STAGE"]  = result.group(1)
                log_file_dict["MTP_ID"] = result.group(2)
                log_file_dict["YEAR"]   = result.group(3)
                log_file_dict["MONTH"]  = result.group(4)
                log_file_dict["DAY"]    = result.group(5)
                log_file_dict["HOUR"]   = result.group(6)
                log_file_dict["MIN"]    = result.group(7)
                log_file_dict["SEC"]    = result.group(8)
            
                dir_name = file_name.split(".")[0]

                os.chdir(cwd_top+"/test_logs/"+dir_name)

                if stage_tgt == "DL":
                    test_stage_log = "test_dl.log"
                elif stage_tgt == "SWI":
                    test_stage_log = "test_swi.log"
                else:
                    test_stage_log = "mtp_test.log"

                #print(test_stage_log)

                nic_info = dict()
                err_info_dict = dict()
                err_info = ""
                # find slot number
                fmt_pattern_fail = "^.*{}.*NIC_DIAG_REGRESSION_TEST_FAIL.*"
                fmt_pattern_pass = "^.*{}.*NIC_DIAG_REGRESSION_TEST_PASS.*"
                pattern_fail = fmt_pattern_fail.format(sn)
                pattern_pass = fmt_pattern_pass.format(sn)
                pass_flag = False
                for line in open(test_stage_log, 'r'):

                    # Somehow we do have first log as pass
                    if re.search(pattern_pass, line):
                        print(sn, "Passed!")
                        pass_flag = True
                        break

                    if re.search(pattern_fail, line):
                        m = re.compile("^.*(NIC-[\d]+) ([\D\d]+) ([\D\d]+) .*")
                        result = m.match(line)
                        if m:
                            nic_info["SLOT"]      = result.group(1)
                            nic_info["CARD_TYPE"] = result.group(2)
                            nic_info["SN"]        = result.group(3)
                            break

                if pass_flag == False:
                    err_info = err_info + line

                    # Find top level failure info
                    for line in open(test_stage_log, 'r'):
                        if re.search("^.*ERR.*"+nic_info["SLOT"]+".*", line):
                            err_info = err_info + line

                    err_info_dict["ERR_INFO"] = err_info

                    err_code = get_err_code(err_info)
                    err_info_dict["ERR_CODE"] = err_code
                    err_info_dict["TEST_INFO"] = log_file_dict
                else:
                    err_info_dict["ERR_INFO"] = err_info
                    err_info_dict["ERR_CODE"] = "PASS"
                    err_info_dict["TEST_INFO"] = log_file_dict

                err_info_dict["LOCATION"] = location_list[idx]
                err_info_dict["ROOT CAUSE"] = root_cause_list[idx]
                err_info_dict["ACTION"] = action_list[idx]

                stage_err_info_dict[dir_name] = err_info_dict

                #os.system("rm -rf ./*")

                os.chdir(cwd_top)

            stage_sn_dict[sn] = stage_err_info_dict

        record_diag_dict[stage_tgt] = stage_sn_dict
    
    os.chdir(cwd_top)


    print("=== {} ===".format(card_type))
    for stage_tgt in stage_tgt_list:
        print("=== {} ===".format(stage_tgt))
        for stage, sn_dict in record_diag_dict.items():
            if stage != stage_tgt:
                continue
            for sn, test_info_dict in sn_dict.items():
                print("==============================================")
                print("--- {} ---".format(sn))
                for test_info,err_info_dict in test_info_dict.items():
                    print("--- {} ---".format(test_info))
                    print("ERROR CODE:", err_info_dict["ERR_CODE"])
                    if verbose == True:
                        print(err_info_dict["ERR_INFO"])
        for stage, sn_dict in record_dict.items():
            if stage != stage_tgt:
                continue
            for sn, test_info_dict in sn_dict.items():
                print("==============================================")
                print("--- {} ---".format(sn))
                for test_info,err_info_dict in test_info_dict.items():
                    print("--- {} ---".format(test_info))
                    print("ERROR CODE:", err_info_dict["ERR_CODE"])
                    if verbose == True:
                        print(err_info_dict["ERR_INFO"])

    # Output to csv file
    # stage - date - MTP_ID - SN - err_code

    fmt_anal_file = "anal_{}_{}{}.csv"
    fmt_anal_output = "{},{},{},{},{},{},{},{},{}\n"
    fmt_date = "{}-{}-{}"

    anal_file = fmt_anal_file.format(card_type, prefix, "_".join(stage_tgt_list))
    f = open(anal_file, "w+") 
    anal_output = fmt_anal_output.format("STAGE", "DATE", "MTP_ID", "SN", "ERR_CODE", "CORNER", "LOCATION", "ROOT CAUSE", "ACTION")
    f.write(anal_output)
    for stage_tgt in stage_tgt_list:
        print("=== {} ===".format(stage_tgt))
        for stage, sn_dict in record_diag_dict.items():
            if stage != stage_tgt:
                continue
            for sn, test_info_dict in sn_dict.items():
                #print(sn)
                for test_info,err_info_dict in test_info_dict.items():
                    location = err_info_dict["LOCATION"]
                    root_cause = err_info_dict["ROOT CAUSE"]
                    action = err_info_dict["ACTION"]
                    action = action.replace(",", ";")

                    err_code = err_info_dict["ERR_CODE"]
                    try:
                        corner = err_code.split(',')[1]
                    except:
                        corner = "NA"
                    if corner == "":
                        corner = "NA"
                    err_code = err_code.split(',')[0]

                    if err_code == "LOG_NOT_FOUND":
                        mtp_id = "NA"
                        date = "NA"
                    else:
                        log_info_dict = err_info_dict["TEST_INFO"]
                        mtp_id = log_info_dict["MTP_ID"]
                        year = log_info_dict["YEAR"]
                        mon = log_info_dict["MONTH"]
                        day = log_info_dict["DAY"]
                        date = fmt_date.format(year, mon, day)
                    anal_output = fmt_anal_output.format(stage, date, mtp_id, sn, err_code, corner, location, root_cause, action)
                    f.write(anal_output)

        for stage, sn_dict in record_dict.items():
            if stage != stage_tgt:
                continue
            for sn, test_info_dict in sn_dict.items():
                for test_info,err_info_dict in test_info_dict.items():
                    location = err_info_dict["LOCATION"]
                    root_cause = err_info_dict["ROOT CAUSE"]
                    action = err_info_dict["ACTION"]
                    action = action.replace(",", ";")

                    err_code = err_info_dict["ERR_CODE"]
                    try:
                        corner = err_code.split(',')[1]
                    except:
                        corner = "NA"
                    if corner == "":
                        corner = "NA"
                    err_code = err_code.split(',')[0]

                    date = "NA"
                    mtp_id = "NA"
                    anal_output = fmt_anal_output.format(stage, date, mtp_id, sn, err_code, corner, location, root_cause, action)
                    f.write(anal_output)
    f.close()

    #with open('data.p', 'wb') as fp:
    #    pickle.dump(data, fp, protocol=pickle.HIGHEST_PROTOCOL)

    # Statistic analysis

    total_tested = dict()
    #WK32 NAPLES25SWM
    #total_tested["DL"]   = 276.0
    #total_tested["P2C"]  = 271.0
    #total_tested["4C-H"] = 1031.0
    #total_tested["4C-L"] = 273.0
    #total_tested["SWI"]  = 905.0
    #total_tested["FST"]  = 944.0

    #WK33 NAPLES25SWM
    #total_tested["DL"]   = 276.0
    #total_tested["P2C"]  = 964.0
    #total_tested["4C-H"] = 1031.0
    #total_tested["4C-L"] = 273.0
    #total_tested["SWI"]  = 905.0
    #total_tested["FST"]  = 944.0

    #WK34 NAPLES25SWM
    #total_tested["ICT"]  = 276.0
    total_tested["DL"]   = 77.0
    total_tested["P2C"]  = 114.0
    #total_tested["4C-H"] = 1031.0
    #total_tested["4C-L"] = 273.0
    total_tested["SWI"]  = 557.0
    #total_tested["FST"]  = 944.0

    #WK32 NAPLES100
    #total_tested["DL"]   = 276.0
    #total_tested["P2C"]  = 271.0
    #total_tested["4C-H"] = 253.0
    #total_tested["4C-L"] = 237.0
    #total_tested["SWI"]  = 206.0
    #total_tested["FST"]  = 204.0

    #WK33 NAPLES100
    #total_tested["DL"]   = 276.0
    #total_tested["P2C"]  = 271.0
    #total_tested["4C-H"] = 253.0
    #total_tested["4C-L"] = 237.0
    #total_tested["SWI"]  = 135.0
    #total_tested["FST"]  = 204.0

    stat_dict = dict()
    stat_pct_dict = dict()

    for stage_tgt in stage_tgt_list:
        print("=== {} ===".format(stage_tgt))
        stage_stat_dict = dict()
        stage_stat_dict["TOTAL"] = 0
        for stage, sn_dict in record_diag_dict.items():
            if stage != stage_tgt:
                continue
            for sn, test_info_dict in sn_dict.items():
                for test_info,err_info_dict in test_info_dict.items():
                    err_code = err_info_dict["ERR_CODE"]
                    err_code = err_code.split(",")[0]
                    stage_stat_dict["TOTAL"] = stage_stat_dict["TOTAL"] + 1
                    try:
                        stage_stat_dict[err_code] = stage_stat_dict[err_code] + 1
                    except:
                        stage_stat_dict[err_code] = 1

        for stage, sn_dict in record_dict.items():
            if stage != stage_tgt:
                continue
            for sn, test_info_dict in sn_dict.items():
                for test_info,err_info_dict in test_info_dict.items():
                    err_code = err_info_dict["ERR_CODE"]
                    stage_stat_dict["TOTAL"] = stage_stat_dict["TOTAL"] + 1
                    try:
                        stage_stat_dict[err_code] = stage_stat_dict[err_code] + 1
                    except:
                        stage_stat_dict[err_code] = 2
            
            sorted_x = sorted(stage_stat_dict.items(), key=lambda kv: kv[1], reverse=True)
            sorted_dict = collections.OrderedDict(sorted_x)

            stage_stat_pct_dict = collections.OrderedDict()
            for err_code, value in sorted_dict.items():
                print(err_code, value)
                stage_stat_pct_dict[err_code] = '{:.1%}'.format(sorted_dict[err_code]/total_tested[stage])

            stat_dict[stage] = sorted_dict
            stat_pct_dict[stage] = stage_stat_pct_dict


    # Output
    fmt_stat_file = "stat_{}_{}{}.csv"
    fmt_stat_output = "{},{},{}\n"

    stat_file = fmt_stat_file.format(card_type, prefix, "_".join(stage_tgt_list))
    f = open(stat_file, "w+") 
    for stage, err_dict in stat_dict.items():
        f.write(stage+"\n")
        for err_code, num in err_dict.items():
            new_err_code = err_code.replace(",", "")
            stat_output = fmt_stat_output.format(new_err_code, num, stat_pct_dict[stage][err_code])
            f.write(stat_output)
        f.write("\n")
        
    f.close()

def get_mfg_log_list(card_type, sn, stage):
    if sn == "":
        print("SN can not be empty!")
        return

    if "4C" in stage:
        if "H" in stage:
            stage = "4C-H"
        else:
            stage = "4C-L"
        path = log_root+card_type+"/4C/"+stage+"/"
    else:
        path = log_root+card_type+"/"+stage+"/"

    #print(path)

    dir_name = path+sn
    #print(dir_name)
    files_found = find_file('*gz', dir_name)

    if files_found == []:
        print(sn, "No log file found")
        return

    print("Following logs are located")
    for file_fullname in files_found:
        file_name = os.path.basename(file_fullname)
        print(file_name.split(".")[0])
    return

def parse_log_file_top(log_root, parse_mode, card_type, stage, sn, tgt_log, verbose, cleanup, save, save_path):
    cwd_top = os.getcwd()
    #try:
    #    shutil.rmtree(cwd_top+'/test_logs')
    #except os.error:
    #    print("no test_logs folder, will be created")

    record_diag_dict = dict()
    if "4C" in stage:
        if "H" in stage:
            stage = "4C-H"
        else:
            stage = "4C-L"
        path = log_root+card_type+"/4C/"+stage+"/"
    else:
        path = log_root+card_type+"/"+stage+"/"
    #print(path)

    dir_name = path+sn
    #print(dir_name)
    files_found = find_file('*gz', dir_name)

    if files_found == []:
        print(sn, "No log file found")
        return

    if parse_mode != "SPEC":
        log_time_list = []
        for idx, file_fullname in enumerate(files_found):
            dir_name1 = os.path.dirname(file_fullname)
            file_name = os.path.basename(file_fullname)

            m = re.compile("^([\D\d]+)_(MTP[S]*-\d+)_(\d\d\d\d)-(\d\d)-(\d\d)_(\d\d)-(\d\d)-(\d\d).*")
            result = m.match(file_name)

            log_file_dict = dict()
            log_file_dict["STAGE"]  = result.group(1)
            log_file_dict["MTP_NO"] = result.group(2)
            log_file_dict["YEAR"]   = result.group(3)
            log_file_dict["MONTH"]  = result.group(4)
            log_file_dict["DAY"]    = result.group(5)
            log_file_dict["HOUR"]   = result.group(6)
            log_file_dict["MIN"]    = result.group(7)
            log_file_dict["SEC"]    = result.group(8)
            log_time = "{}-{}-{}-{}-{}".format(log_file_dict["YEAR"], log_file_dict["MONTH"],log_file_dict["DAY"],log_file_dict["HOUR"], log_file_dict["MIN"])
            log_time_list.append(log_time)
        if parse_mode == "FIRST":
            tgt_log_time="9999-99-99-99-99"
            tgt_log_time_idx=0
            for i in range(len(log_time_list)):
                if log_time_list[i] < tgt_log_time:
                    tgt_log_time = log_time_list[i]
                    tgt_log_time_idx = i
        else:
            tgt_log_time="0000-00-00-00-00"
            tgt_log_time_idx=0
            for i in range(len(log_time_list)):
                if log_time_list[i] > tgt_log_time:
                    tgt_log_time = log_time_list[i]
                    tgt_log_time_idx = i
        files_found = [files_found[tgt_log_time_idx]]

    # Specified log location
    else:
        files_found = find_file(tgt_log+'.tar.gz', dir_name)

        if files_found == []:
            print(sn, "No log file found")
            sys.exit(0)
        if len(files_found) != 1:
            print("ERROR: more than one target log found!")
            sys.exit(0)

    print(files_found)
    if parse_mode == "FW_REV":
        parse_fw_rev(files_found[0], sn, verbose, cleanup)
    else:
        parse_log_file(files_found[0], sn, stage, verbose, cleanup, save, save_path)

def parse_log_file(file_fullname, sn, stage, verbose, cleanup, save, save_path):
    cwd_top = os.getcwd()
    dir_name1 = os.path.dirname(file_fullname)
    file_name = os.path.basename(file_fullname)
    
    tgt_dir = cwd_top+"/test_logs"
    if not os.path.exists(tgt_dir):
        os.mkdir(tgt_dir)
    os.chdir(cwd_top+"/test_logs")
    
    untar(file_fullname)
    
    dir_name = file_name.split(".")[0]

    card_log_path = cwd_top+"/test_logs/"+dir_name
    os.chdir(card_log_path)

    if stage == "DL":
        test_stage_log = "test_dl.log"
    elif stage == "SWI":
        test_stage_log = "test_swi.log"
    else:
        test_stage_log = "mtp_test.log"

    # find slot number
    fmt_pattern_fail = "^.*{}.*NIC_DIAG_REGRESSION_TEST_FAIL.*"
    fmt_pattern_pass = "^.*{}.*NIC_DIAG_REGRESSION_TEST_PASS.*"
    pattern_fail = fmt_pattern_fail.format(sn)
    pattern_pass = fmt_pattern_pass.format(sn)
    pass_flag = False
    nic_info = dict()
    err_info_dict = dict()
    err_info = ""
    err_info_s = ""
    err_info_a = ""
    for line in open(test_stage_log, 'r'):

        # Somehow we do have first log as pass
        if re.search(pattern_pass, line):
            print(sn, "Passed!")
            pass_flag = True
            os.chdir(cwd_top)
            return

        if re.search(pattern_fail, line):
            m = re.compile("^.*(NIC-[\d]+) ([\D\d]+) ([\D\d]+) .*")
            result = m.match(line)
            if m:
                nic_info["SLOT"]      = result.group(1)
                nic_info["CARD_TYPE"] = result.group(2)
                nic_info["SN"]        = result.group(3)
                break

    expErrList = [
        "cap0.ms.em.int_groups.intreg: axi_interrupt : 1 EN 1 hier_enabled 1",
        "Unexpected int set: cap0.ms.em",
        "interrupt-non-zero for reg:MS_M_AM_STS:",
        "interrupt-non-zero for reg:AR_M_AM_STS",
        "PRP2() error_count non-zero",
        "stall_timeout_error"]

    if pass_flag == False:
        err_info_s = err_info_s + line
        err_info_a = err_info_a + line

        # Get summary first
        pattern = "^.*ERR.*"+nic_info["SLOT"]+".*FAIL.*"
        # Find top level failure info
        for line in open(test_stage_log, 'r'):
            if re.search(pattern, line):

                # There are some expected Errors in snake test
                expFound = False
                for expErr in expErrList:
                    if expErr in line:
                        expFound = True
                if expFound == True:
                    continue

                err_info_s = err_info_s + line

        # Get all errors
        pattern = "^.*ERR.*"+nic_info["SLOT"]+".*"
        for line in open(test_stage_log, 'r'):
            if re.search(pattern, line):

                # There are some expected Errors in snake test
                expFound = False
                for expErr in expErrList:
                    if expErr in line:
                        expFound = True
                if expFound == True:
                    continue
                err_info_a = err_info_a + line

        if "Init NIC boot info failed" in err_info_a:
            err_info = err_info_a
        else:
            if verbose == False:
                err_info = err_info_s
            else:
                err_info = err_inf_a
    
        err_info_dict["ERR_INFO"] = err_info

        err_code = get_err_code(err_info)
        err_info_dict["ERR_CODE"] = err_code
    else:
        err_info_dict["ERR_INFO"] = err_info
        err_info_dict["ERR_CODE"] = "PASS"
        sys.exit(1)

    print(err_info)
    print(err_code)

    if "4C" in stage:
        if "HV" in err_code:
            prefix = "hv_"
        elif "LV" in err_code:
            prefix = "lv_"
        else:
            print("No corner detected!")
            return
    else:
        prefix = "./"

    if "L1" in err_code:
        logfile_path = prefix+"asic_logs/"
        logfile_pattern = "cap_l1*"+sn+"*log"
    elif "SNAKE_PCIE" in err_code:
        logfile_path = prefix+"asic_logs/"
        logfile_pattern = sn+"_snake_pcie.log"
    elif "AVS" in err_code:
        logfile_path = "./"
        logfile_pattern = "diag_"+nic_info["SLOT"]+"_dl.log"
    elif "ETH_PRBS" in err_code:
        logfile_path = "nic_logs/AAPL-"+nic_info["SLOT"]
        logfile_pattern = "log_NIC_ASIC.txt"
    elif "NIC_BOOT_FAIL" in err_code:
        logfile_path = "./"
        logfile_pattern = "diag_"+nic_info["SLOT"]+"*log"
    else:
        print("Unsupported error code!")
        return

    if verbose == True:
        print(logfile_path, logfile_pattern)
    log_filename = ""
    #for path in Path('./').rglob("cap_l1*"+sn+"*log"):
    for path in Path(logfile_path).rglob(logfile_pattern):
        log_filename = str(path.parent)+'/'+str(path.name)

    if verbose == True:
        print("log_filename:", log_filename)

    fmt_cmd = cwd_top+"/search_file.sh -mode {} -fn {}" 
    # L1 ESEC
    if "L1_ESEC" in err_code:
        cmd = fmt_cmd.format("L1_ESEC", log_filename)
    elif "L1_HBM" in err_code:
        cmd = fmt_cmd.format("L1_HBM", log_filename)
    elif "L1" in err_code:
        cmd = fmt_cmd.format("L1", log_filename)
    elif "SNAKE" in err_code:
        cmd = fmt_cmd.format("SNAKE", log_filename)
    elif "AVS" in err_code:
        cmd = fmt_cmd.format("AVS", log_filename)
    elif "ETH_PRBS" in err_code:
        cmd = fmt_cmd.format("ETH_PRBS", log_filename)
    else:
        err_code = err_code.split(",")[0]
        cmd = fmt_cmd.format(err_code, log_filename)

    ret_str = run_bash_cmd(cmd)
    if ret_str == "":
        ret_str = "No error found. Please check manually"

    print(ret_str)

    if save == True:
        save_path = save_path+"/"+sn
        mkdir_p(save_path)
        fmt_cmd = "cp -r {} {}/"
        cmd = fmt_cmd.format(card_log_path, save_path)
        print(cmd)
        ret = run_bash_cmd(cmd)
        print(ret)

    os.chdir(cwd_top)

    if cleanup == True:
        rm_cmd(card_log_path)

def parse_fw_rev(file_fullname, sn, verbose, cleanup):
    cwd_top = os.getcwd()
    dir_name1 = os.path.dirname(file_fullname)
    file_name = os.path.basename(file_fullname)
    
    tgt_dir = cwd_top+"/test_logs"
    if not os.path.exists(tgt_dir):
        os.mkdir(tgt_dir)
    os.chdir(cwd_top+"/test_logs")
    
    untar(file_fullname)
    
    dir_name = file_name.split(".")[0]

    card_log_path = cwd_top+"/test_logs/"+dir_name
    os.chdir(card_log_path)

    test_stage_log = "test_swi.log"

    # find slot number
    fmt_pattern_pass = "^.*{}.*NIC_DIAG_REGRESSION_TEST_PASS.*"
    pattern_pass = fmt_pattern_pass.format(sn)
    nic_info = dict()
    err_info_dict = dict()
    err_info = ""

    found_flag = False
    for line in open(test_stage_log, 'r'):
        if re.search(pattern_pass, line):
            m = re.compile("^.*(NIC-[\d]+) ([\D\d]+) ([\D\d]+) .*")
            result = m.match(line)
            if m:
                nic_info["SLOT"]      = result.group(1)
                nic_info["CARD_TYPE"] = result.group(2)
                nic_info["SN"]        = result.group(3)
                found_flag = True
                break

    if found_flag == False:
        print("Unable to find record:", sn)
        return
    logfile_path = "./"
    logfile_pattern = "diag_"+nic_info["SLOT"]+"_swi.log"

    if verbose == True:
        print(logfile_path, logfile_pattern)
    log_filename = ""
    for path in Path(logfile_path).rglob(logfile_pattern):
        log_filename = str(path.parent)+'/'+str(path.name)

    if verbose == True:
        print("log_filename:", log_filename)

    fmt_cmd = cwd_top+"/search_file.sh -mode {} -fn {}" 
    cmd = fmt_cmd.format("FW_REV", log_filename)

    ret_str = run_bash_cmd(cmd)
    if ret_str == "":
        ret_str = "No error found. Please check manually"
    print(ret_str)

    os.chdir(cwd_top)

    if cleanup == True:
        rm_cmd(card_log_path)

def cleanup_all():
    cwd_top = cwd_top = os.getcwd()
    path = cwd_top + "/test_logs/"
    rm_cmd(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    group = parser.add_mutually_exclusive_group()

    parser.add_argument("-fetch", "--fetch", help="Fetch log file", action='store_true')
    parser.add_argument("-fy", "--first_yield", help="Parse first fail", action='store_true')
    parser.add_argument("-verbose", "--verbose", help="Print all output", action='store_true')
    parser.add_argument("-list", "--list", help="List all test logs under specific sn", action='store_true')
    parser.add_argument("-parse", "--parse", help="Parse error of specific sn", action='store_true')
    parser.add_argument("-cl", "--cl", help="Delete logs after processing", action='store_true')
    parser.add_argument("-cl_all", "--cl_all", help="Delete logs after processing", action='store_true')
    parser.add_argument("-sv", "--save", help="Save log to target location", action='store_true')

    group.add_argument("-cm", "--cm", help="CM site: FML/FPN", type=str, default="FPN")
    parser.add_argument("-fn", "--filename", help="File name of yield report", type=str, default="")
    parser.add_argument("-sl", "--stage_list", help="Stage list; e.g. 'DL,P2C'", type=str, default="")
    parser.add_argument("-prefix", "--prefix", help="prefix", type=str, default="")
    parser.add_argument("-logroot", "--logroot", help="Path to log root folder", type=str, default="/home/xguo2/workspace/manufacture/mfg_log/")

    # Log parser
    parser.add_argument("-pmode", "--parse_mode", help="Parse mode", type=str, default="list")
    parser.add_argument("-sn", "--sn", help="Serial Number", type=str, default="")
    parser.add_argument("-card_type", "--card_type", help="Card_type", type=str, default="")
    parser.add_argument("-stage", "--stage", help="Stage", type=str, default="")
    parser.add_argument("-tgt_log", "--tgt_log", help="Target log", type=str, default="")
    parser.add_argument("-sv_path", "--save_path", help="Path to save log", type=str, default="/vol/hw/diag/asic_log")

    args = parser.parse_args()

    filename = args.filename
    prefix = args.prefix
    log_root = args.logroot
    verbose = args.verbose

    sn = args.sn.upper()
    stage = args.stage.upper()
    card_type = args.card_type.upper()
    tgt_log = args.tgt_log
    parse_mode = args.parse_mode.upper()
    cl = args.cl
    cl_all = args.cl_all

    if cl_all == True:
        cleanup_all()
        sys.exit(0)

    if filename != "":
        parse_yield_file(filename, prefix, log_root, args.cm, args.stage_list, args.first_yield, args.fetch, verbose)
        sys.exit(0)

    if args.parse == True:
        if parse_mode == "LIST":
            get_mfg_log_list(card_type, sn, stage)
            sys.exit(0)
        parse_log_file_top(log_root, parse_mode, card_type, stage, sn, tgt_log, verbose, cl, args.save, args.save_path)
