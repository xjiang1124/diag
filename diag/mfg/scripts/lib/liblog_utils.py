import getpass
import smtplib
import sys
import datetime
import re
import oyaml as yaml
import os
import time
import pexpect
from liblog_cfg import * 

def get_ssh_option():
    return DIAG_SSH_OPTIONS


def sys_exit(err):
    sys.exit("\033[1;91m" + "## ERR: " + err + "\033[0m")


def get_timestamp():
    # 2018-08-07 22:54:40.484198
    tmp = str(timestamp_snapshot())
    tmp = tmp.replace(' ', '_')
    tmp = tmp.replace(':', '-')
    return tmp


def timestamp_snapshot():
    return datetime.datetime.now().replace(microsecond=0)


def get_date():
    return str(datetime.datetime.now().date())


def get_password(srv_id, srv_ip, userid):
    while True:
        while True:
            passwd = getpass.getpass("Password for " + userid + "@" + srv_id + "(" + srv_ip + "): ")
            if passwd != "":
                break
        confirm = getpass.getpass("Confirm your password: ")
        if passwd == confirm:
            return passwd
        else:
            print("password mismatch, please retry...")
            continue


def double_confirm(msg):
    tmp = ""

    while (tmp != "Y") and (tmp != "N"):
        tmp = raw_input("Confirm " + msg + "? (Y/N) [Y]:")
        # default is yes
        if tmp == "":
            tmp = "Y"

        tmp = str.upper(tmp)
        if tmp == "Y":
            return True
        elif tmp == "N":
            return False
        else:
            continue


def single_select_menu(title, opt_list):
    menu = "+-" + "-"*len(title) + "-+\n"
    menu += "| " + title + " |\n"
    menu += "+-" + "-"*len(title) + "-+\n"
    menu += "Options:\n"
    for idx in range(len(opt_list)):
        menu += "    * " + opt_list[idx] + "\n"
    menu += "Scan the MTP ID Bar Code: "

    # validate input loop
    while True:
        scan_input = raw_input(menu).replace(' ', '')
        if scan_input in opt_list:
            break
        else:
            cli_err("Invalid MTP ID: {:s}".format(scan_input))
            continue

    return scan_input


def multiple_select_menu(title, opt_list):
    sub_list = list()
    menu_list = list(opt_list)

    # select menu
    while True:
        opt_num = len(menu_list)
        menu = "+-" + "-"*len(title) + "-+\n"
        menu += "| " + title + " |\n"
        menu += "+-" + "-"*len(title) + "-+\n"
        menu += "Options:\n"
        for idx in range(opt_num):
            menu += "    * " + menu_list[idx] + "\n"
        menu += "Scan the MTP ID Bar Code: [{:s} Selected]".format(", ".join(sub_list))

        # validate input loop
        scan_input = raw_input(menu).replace(' ','')
        if scan_input == "STOP":
            return sub_list
        elif scan_input in menu_list:
            sub_list.append(scan_input)
            menu_list.remove(scan_input)
        else:
            cli_err("Invalid MTP ID: {:s}".format(scan_input))


def load_cfg_from_yaml(yaml_file):
    if not os.path.exists(yaml_file):
        sys_exit("Yaml config file: " + yaml_file + " doesn't exist")

    with open(yaml_file, "r") as f:
        cfg = yaml.load(f)

    if not cfg:
        sys_exit("Load yaml config file: " + yaml_file + " failed")

    if len(cfg) == 0:
        sys_exit("No content in yaml config file: " + yaml_file)

    return cfg


def network_copy_file(ip_addr, userid, passwd, local_file, remote_dir):
    cmd = "md5sum " + local_file
    session = pexpect.spawn(cmd)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.OS_CMD_DELAY)
    match = re.search(r"([0-9a-fA-F]+) +.*", str(session.before))
    session.close()
    if match:
        local_md5sum = match.group(1)
    else:
        cli_err("Execute command {:s} failed".format(cmd))
        return False

    session = pexpect.spawn("scp {:s} {:s} {:s}@{:s}:{:s}".format(get_ssh_option(), local_file, userid, ip_addr, remote_dir))
    session.expect_exact("ssword:")
    session.sendline(passwd)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.MTP_NETCOPY_DELAY)

    # verify the file md5sum
    cmd = " ".join(["ssh -l", userid, ip_addr]) + get_ssh_option()
    session = pexpect.spawn(cmd)
    session.setecho(False)
    session.expect_exact("assword:")
    session.sendline(passwd)
    session.expect_exact(get_linux_prompt_list())

    cmd = "sync"
    session.sendline(cmd)
    session.expect_exact(get_linux_prompt_list(), timeout=MTP_Const.OS_SYNC_DELAY)

    cmd = "md5sum " + remote_dir + os.path.basename(local_file)
    session.sendline(cmd)
    session.expect_exact(get_linux_prompt_list(), timeout=MTP_Const.OS_CMD_DELAY)
    match = re.search(r"([0-9a-fA-F]+) +.*", str(session.before))
    session.close()
    # md5sum match
    if match:
        if match.group(1) == local_md5sum:
            return True
        else:
            cli_err("File md5sum mismatch")
            return False
    else:
        cli_err("Execute command {:s} on {:s} failed".format(cmd, ip_addr))
        return False


def network_get_file(ip_addr, userid, passwd, local_file, remote_file):
    session = pexpect.spawn("scp {:s} {:s}@{:s}:{:s} {:s}".format(get_ssh_option(), userid, ip_addr, remote_file, local_file))
    session.expect_exact("ssword:")
    session.sendline(passwd)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.MTP_NETCOPY_DELAY)

    cmd = "sync"
    session = pexpect.spawn(cmd)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.OS_SYNC_DELAY)

    cmd = "md5sum " + local_file 
    session = pexpect.spawn(cmd)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.OS_CMD_DELAY)
    match = re.search(r"([0-9a-fA-F]+) +.*", str(session.before))
    session.close()
    if match:
        local_md5sum = match.group(1)
    else:
        cli_err("Execute command {:s} failed".format(cmd))
        return False

    # verify the file md5sum
    cmd = " ".join(["ssh -l", userid, ip_addr]) + get_ssh_option()
    session = pexpect.spawn(cmd)
    session.setecho(False)
    session.expect_exact("assword:")
    session.sendline(passwd)
    session.expect_exact(get_linux_prompt_list())

    cmd = "md5sum " + remote_file
    session.sendline(cmd)
    session.expect_exact(get_linux_prompt_list(), timeout=MTP_Const.OS_CMD_DELAY)
    match = re.search(r"([0-9a-fA-F]+) +.*", str(session.before))
    session.close()
    # md5sum match
    if match:
        if match.group(1) == local_md5sum:
            return True
        else:
            cli_err("File md5sum mismatch")
            return False
    else:
        cli_err("Execute command {:s} on {:s} failed".format(cmd, ip_addr))
        return False

def print_testcounts(testcounts):
    ret = ""
    for card_type in testcounts:
        for test_type in testcounts[card_type]:
            passed = testcounts[card_type][test_type]["PASS"]
            failed = testcounts[card_type][test_type]["FAIL"]
            skipped = testcounts[card_type][test_type]["SKIP"]
            total = testcounts[card_type][test_type]["TOTAL"]
            ret += "{:d}/{:d} {:s} passed {:s}".format(passed,total,card_type,test_type)
            if failed:
                ret += ", {:d} failed\n".format(failed)
            else:
                ret += "\n"
    return ret

def get_tail_logfile(test_type, filepath, logpath):
    import subprocess
    cmd_log_list = subprocess.Popen(("tar", "-tvzf", logpath+filepath), 
            stdout = subprocess.PIPE)
    summary_file = subprocess.check_output(("grep test | awk '{print $NF}'"),
            stdin = cmd_log_list.stdout, shell=True)
    summary_file = summary_file.strip()
    cmd = subprocess.Popen(("tar", "-xOvzf", logpath+filepath, "{:s}".format(summary_file)),
            stdout = subprocess.PIPE)
    res = subprocess.check_output(('grep','NIC_DIAG_REGRESSION_TEST'), 
            stdin = cmd.stdout)
    return res

def get_log_summary(session_before, logpath):
    summary = ""
    logs_done = set()
    testcounts = dict()
    for line in session_before.split("\n"):
        if line.strip().endswith(".tar.gz"):
#    for line in session_before.split("\n"):
#        if line.strip().endswith(".tar.gz"):
            if os.path.basename(line.strip()) in logs_done:
                #this SN already part of previously printed log archive
                continue
            logs_done.add(os.path.basename(line.strip()))
            summary += "\n\n" + logpath + line.strip()
            summary += "\n" + "="*len(logpath+line.strip()) + "\n"
            
            #test_type = os.path.basename(line.strip())[:3]
            card_type = line.strip().split("/")[0]
            test_type = line.strip().split("/")[1]
            if not card_type in testcounts:
                testcounts[card_type] = dict()
                testcounts[card_type][test_type] = {"PASS":0,"FAIL":0,"SKIP":0,"TOTAL":0}
            if not test_type in testcounts[card_type]:
                testcounts[card_type][test_type] = {"PASS":0,"FAIL":0,"SKIP":0,"TOTAL":0}
            
            res = get_tail_logfile(test_type, line.strip(), logpath)
            summary += res
            # Count:
            testcounts[card_type][test_type]["TOTAL"] += len(re.findall("TEST",res))
            testcounts[card_type][test_type]["PASS"] += len(re.findall("PASS",res))
            testcounts[card_type][test_type]["FAIL"] += len(re.findall("FAIL",res))
            testcounts[card_type][test_type]["SKIP"] += len(re.findall("SKIP",res))
    print(summary)

    return "\nIn these logs:\n"+print_testcounts(testcounts)+"\n\n"+summary

def email_report(email_to, title, body = None):
    if not email_to:
        return

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(DIAG_NIGHTLY_REPORT_ACCOUNT, DIAG_NIGHTLY_REPORT_PASSWD)

    msg = "Subject: {:s}\n\n".format(title)
    if body:
        msg += "{:s}".format(body)
    server.sendmail(DIAG_NIGHTLY_REPORT_ACCOUNT, email_to, msg) 
    server.quit()

###################################################################################

def flx_soap_save_uut_result_xml(stage, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list):
    test_xml = ""
    for test, test_rslt, err_dsc, err_code in zip(test_list, test_rslt_list, err_dsc_list, err_code_list):
        # (test, status, value, description, failure code)
        value = ""
        test_xml += FLX_SAVE_UUT_TEST_RSLT_FMT.format(test, test_rslt, value, err_dsc, err_code) 

    #(stage, SN, start_ts, duration, stop_ts, result)
    save_uut_rslt_entry = FLX_SAVE_UUT_RSLT_ENTRY_FMT.format(stage, sn, str(start_ts), str(duration), str(stop_ts), rslt, duration, rslt)

    return FLX_SAVE_UUT_RSLT_XML_HEAD + \
           save_uut_rslt_entry + \
           test_xml + \
           FLX_SAVE_UUT_RSLT_ENTRY_END + \
           FLX_SAVE_UUT_RSLT_XML_TAIL


def flx_soap_get_uut_info_xml(stage, sn):
    get_uut_info_entry = FLX_GET_UUT_INFO_ENTRY_FMT.format(sn, stage) 
    return FLX_GET_UUT_INFO_XML_HEAD + \
           get_uut_info_entry + \
           FLX_GET_UUT_INFO_XML_TAIL


def soap_post_report(xml):
    webservice = httplib.HTTP(FLX_WEBSERVER)
    webservice.putrequest("POST", FLX_API_URL)
    webservice.putheader("Content-Type", "text/xml")
    webservice.putheader("SOAPAction", FLX_SAVE_UUT_RSLT_SOAP)
    webservice.putheader("Content-length", "%d" % len(xml))
    webservice.endheaders()

    webservice.send(xml)

    statuscode, statusmessage, header = webservice.getreply()
    resp = webservice.getfile().read()
    match = re.findall(FLX_SAVE_UUT_RSLT_CODE_RE, resp)
    if match:
        return match[0]
    else:
        print("################## SAVE UUT RSLT #######################")
        print resp
        print("################## SAVE UUT RSLT #######################")
        return "500"


def soap_get_uut_info(xml):
    webservice = httplib.HTTP(FLX_WEBSERVER)
    webservice.putrequest("POST", FLX_API_URL)
    webservice.putheader("Content-Type", "text/xml")
    webservice.putheader("SOAPAction", FLX_GET_UUT_INFO_SOAP)
    webservice.putheader("Content-length", "%d" % len(xml))
    webservice.endheaders()

    webservice.send(xml)

    statuscode, statusmessage, header = webservice.getreply()
    resp = webservice.getfile().read()
    match = re.findall(FLX_GET_UUT_INFO_CODE_RE, resp)
    if match:
        return match[0]
    else:
        print("################## GET UUT INF #######################")
        print resp
        print("################## GET UUT INF #######################")
        return "500"


def flx_web_srv_post_uut_report(stage, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list):
    xml = flx_soap_get_uut_info_xml(stage, sn)
    ret = soap_get_uut_info(xml) 
    if int(ret) != 0:
        return False

    xml = flx_soap_save_uut_result_xml(stage, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list)
    ret = soap_post_report(xml)
    if int(ret) != 0:
        return False

    return True
