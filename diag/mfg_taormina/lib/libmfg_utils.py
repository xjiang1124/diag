import getpass
import smtplib
import httplib
import sys
import datetime
import re
import yaml as yaml
import os
import time
import pexpect
import glob
import select

from libdefs import MTP_Const
from libdefs import UUT_Type
from libdefs import FF_Stage
from libdefs import FPN_FF_Stage
from libdefs import MTP_DIAG_Path
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import FLX_Factory
from libdefs import MFG_DIAG_CMDS
from libdefs import Swm_Test_Mode
from libdefs import NIC_IP_Address
from libmfg_cfg import *

def get_linux_prompt_list():
    return DIAG_OS_PROMPT_LIST

def get_ssh_option():
    return DIAG_SSH_OPTIONS

def get_ssh_connect_cmd(userid, ipaddr):
    ssh_cmd = " ".join(["ssh -l", userid, ipaddr]) + get_ssh_option()
    return ssh_cmd

def cli_out(info):
    print("## ATT: " + info)


def cli_inf(info):
    print("## [" + get_timestamp() + "] INF: " + info)


def cli_dbg(info):
    print("## DBG: " + info)


def cli_err(err):
    print("\033[1;91m" + "## [" + get_timestamp() + "] ERR: " + err + "\033[0m")


def cli_log_inf(fp, info):
    msg = "## [" + get_timestamp() + "] LOG: " + info
    fp.write(msg + "\n")

    cli_inf(info)


def cli_log_err(fp, err):
    msg = "## [" + get_timestamp() + "] ERR: " + err
    fp.write(msg + "\n")

    cli_err(err)


def cli_log_rslt(title, pass_list, fail_list, fp):
    desc = "################ {:s} ################".format(title)
    pre_post = "#" * len(desc)

    print("\033[1;7m")
    print(pre_post)
    print(desc)
    print(pre_post + "\033[0m")

    if len(pass_list) != 0:
        print("\033[1;92m")
        for item in pass_list:
            cli_log_inf(fp, item)

    if len(fail_list) != 0:
        print("\033[1;91m")
        for item in fail_list:
            cli_log_err(fp, item)
    print("\033[0m")


def diag_skip_cmd(dsp, test=None):
    cmd = " -d " + dsp
    if test:
        cmd += " -t " + test
    return cmd


def diag_param_cmd(param_list):
    # CARD, DSP, TEST, Param_list
    card = param_list[0]
    dsp = param_list[1]
    test = param_list[2]
    param = param_list[3]

    cmd = " -c {:s} -d {:s} -t {:s} -p '{:s}'".format(card, dsp, test, param)
    return cmd


def diag_seq_run_cmd(card_name, dsp, test, param):
    cmd = MFG_DIAG_CMDS.MTP_DIAG_RUN_FMT.format(card_name)
    cmd += " -d {:s}".format(dsp)
    if test:
        cmd += " -t {:s}".format(test)
    if param != '""':
        cmd += " -p {:s}".format(param)
    return cmd


def diag_para_run_cmd(card_name, dsp, test, param):
    cmd = MFG_DIAG_CMDS.MTP_DIAG_RUN_FMT.format(card_name)
    cmd += " -d {:s}".format(dsp)
    if test:
        cmd += " -t {:s}".format(test)
    if param != '""':
        cmd += " -p {:s}".format(param)
    return cmd


def diag_seq_errcode_cmd(card_name, dsp):
    cmd = MFG_DIAG_CMDS.MTP_DIAG_RSLT_FMT.format(card_name)
    cmd += " -d {:s}".format(dsp)
    return cmd


def diag_para_errcode_cmd(card_name, dsp):
    cmd = MFG_DIAG_CMDS.MTP_DIAG_RSLT_FMT.format(card_name)
    cmd += " -d {:s}".format(dsp)
    return cmd


def count_down(seconds):
    secs = seconds
    while secs:
        sys.stdout.write("Time left: {:03d} seconds....\r".format(secs))
        sys.stdout.flush()
        time.sleep(1)
        secs -= 1

def count_down_by_time(seconds):
    start=datetime.datetime.now()
    while True:
        difftime = datetime.datetime.now()-start
        totalseconds = difftime.total_seconds()
        if totalseconds > seconds:
            break
        sys.stdout.write("Time left: {:03d} seconds....\r".format(int(seconds - totalseconds)))
        sys.stdout.flush()
        #time.sleep(1)
        #secs -= 1

def file_exist(file_path):
    return os.path.isfile(file_path)


def fan_key(slot, base = 1):
    return "FAN-{:d}".format(slot + base)


def psu_key(slot, base = 1):
    return "PSU-{:d}".format(slot + base)


def nic_key(slot, base = 1):
    return "NIC-{:02d}".format(slot + base)


def mtp_key(mtp, base = 1):
    return "MTP-{:03d}".format(mtp + base)


def id_str(srv = None, mtp = None, nic = None, base = 1):
    tmp_str = ""
    if srv is not None:
        tmp_str += "[{:s}]: ".format(srv)
    if mtp is not None:
        tmp_str += "[{:s}]: ".format(mtp)
    if nic is not None:
        tmp_str += "[{:s}]: ".format(nic_key(nic, base))
        
    return tmp_str

def id_final_str(srv = None, mtp = None):
    tmp_str = ""
    if srv is not None:
        tmp_str += "[{:s}]: ".format(srv)
    if mtp is not None:
        tmp_str += "[{:s}]: ".format(mtp)

    return tmp_str

def sys_exit(err):
    sys.exit("\033[1;91m" + "## ERR: " + err + "\033[0m")

def get_passmark_timestamp():
    # 20180807225440
    tmp = str(timestamp_snapshot())
    tmp = tmp.replace(' ', '')
    tmp = tmp.replace(':', '')
    tmp = tmp.replace('-', '')
    return tmp

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


def get_fru_date():
    # return format mmddyy
    return datetime.datetime.now().strftime("%m%d%y")


def get_nic_ip_addr(slot, nic_type=""):
    if nic_type == NIC_Type.TAORMINA:
        return NIC_IP_Address.MGMT_IP[slot]

    # return 10.1.1.(100+slot)
    return "10.1.1.{:d}".format(100+slot+1)


# remove the special character mixed with output:
# eg: SMP Tue Ma^@r 19 11:14:41 PT 2019
def special_char_removal(buf):
    return re.sub(r"[\x00-\x09,\x0B-\x0C,\x0E-\x1F]", "", buf)


def serial_number_validate(tmp):
    if re.match(NAPLES_SN_FMT, tmp) and (len(tmp) == 11):
        return tmp
    elif re.match(HP_SN_FMT, tmp) and (len(tmp) == 10):
        return tmp
    elif re.match(TOR_SN_FMT, tmp) and (len(tmp) == 11 or len(tmp) == 10):
        return tmp
    else:
        return None


def mac_address_validate(tmp):
    if re.match(NAPLES_MAC_FMT, tmp) and (len(tmp) == 12):
        return tmp
    elif re.match(TOR_MAC_FMT, tmp):
        return tmp
    else:
        return None


def part_number_validate(tmp):
    if re.match(NAPLES_PN_FMT, tmp) and (len(tmp) == 13 or len(tmp) == 12):
        return tmp
    if re.match(HP_PN_FMT, tmp) and (len(tmp) == 10):
        return tmp
    if re.match(TOR_PN_FMT, tmp):
        return tmp
    else:
        return None

def edc_validate(tmp):
    if re.match(ARUBA_EDC_FMT, tmp):
        return tmp
    else:
        return None

def ip_address_validate(tmp):
    if re.match(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', tmp):
        return True
    else:
        return False


def mac_address_format(tmp, delimiter="-"):
    return delimiter.join(re.findall("..", tmp))


def hpe_date_format(tmp):
    timestamp_format = "%Y-%m-%d_%H-%M-%S"
    hpe_format = "%m/%d/%Y %H:%M:%S"
    return datetime.datetime.strptime(tmp,timestamp_format).strftime(hpe_format)

def mac_address_offset(base, addend):
    """ input base MAC as string and return string """
    base_mac = int(base, 16)
    sum_mac = base_mac + addend
    return "{0:0{1}X}".format(sum_mac,12) #zero padding


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


def action_confirm(msg, action):
    tmp = ""
    while (tmp != action):
        tmp = raw_input("Operator Confirm " + msg + ":")


def sw_pn_scan():
    tmp = raw_input("Scan the Software PN: ")
    return tmp;


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
        if scan_input == "STOP":
            return None
        elif scan_input in opt_list:
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


def load_cfg_from_yaml_file_list(yaml_file_list):
    yaml_merge_content = ""
    for yaml_file in yaml_file_list:
        if not os.path.exists(yaml_file):
            sys_exit("Yaml config file: " + yaml_file + " doesn't exist")

        with open(yaml_file, "r") as f:
            yaml_merge_content += f.read()

    cfg = yaml.safe_load(yaml_merge_content)

    if not cfg:
        sys_exit("Load yaml config files failed")

    if len(cfg) == 0:
        sys_exit("No content in yaml config files")

    return cfg

def expand_range_of_numbers(data, range_min=1, range_max=10, dev=None):
    '''
    Expands a string "1-3,5,7" as list of integers [1,2,3,5,7]
    Can provide a min and max possible value.
    '''
    expanded = []
    try:
        if not data:
            return expanded
        if isinstance(data, int):
            #single element that yaml parser read as integer.
            expanded.append(data)
        else:
            for yaml_field in data.split(","):
                if "-" not in yaml_field:
                    #individual integer
                    expanded.append(int(yaml_field))
                else:
                    #range of integers: expand them
                    start,end = map(int, yaml_field.split("-"))
                    if start < end:
                        expanded = expanded + range(start,end+1)
                    else:
                        sys_exit("{:s} Invalid slot range '{:s}-{:s}' in config file".format(dev, start, end))

        #remove duplicates
        expanded = list(set(expanded))
        #range check
        if not all(x >= range_min and x <= range_max for x in expanded):
            sys_exit("{:s} Invalid slot in config file: must be between {:s}-{:s}".format(dev, range_min, range_max))

    except ValueError as e:
        #not a number
        sys_exit(dev+" Invalid slot "+str(e.message.split(":")[-1])+" in config file")

    return expanded


def load_cfg_from_yaml(yaml_file):
    if not os.path.exists(yaml_file):
        sys_exit("Yaml config file: " + yaml_file + " doesn't exist")

    with open(yaml_file, "r") as f:
        cfg = yaml.safe_load(f)

    if not cfg:
        sys_exit("Load yaml config files failed")

    if len(cfg) == 0:
        sys_exit("No content in yaml config files")

    return cfg

def handle_uut_id_scan(usr_input, uut_scan_rslt, valid_uut_list):
    if usr_input in uut_scan_rslt.keys():
        cli_err("UUT ID Barcode: {:s} is double scanned, please restart the scan process\n".format(usr_input))
        return None
    if usr_input in valid_uut_list:
        return usr_input
    elif len(valid_uut_list) == 0:
        return usr_input
    elif usr_input not in valid_uut_list:
        cli_err("UUT ID Barcode: {:s} not found in config".format(usr_input))
        return None
    else:
        return None

def handle_scan(scan_item_str, usr_input, scanned_list):
    scan_item_to_validation_func = {
        "Serial Number": serial_number_validate,
        "MAC Address": mac_address_validate,
        "Part Number": part_number_validate,
        "Engineering Date Code": edc_validate
    }
    validation_func = scan_item_to_validation_func.get(scan_item_str)
    if validation_func(usr_input):
        if usr_input not in scanned_list:
            return True
        elif usr_input in scanned_list and (scan_item_str == "Part Number" or scan_item_str == "Engineering Date Code"): #pn/edc is not unique
            return True
        else:
            cli_err("UUT {:s}: {:s} is double scanned, please restart the scan process".format(scan_item_str, usr_input))
            return False
    elif usr_input == "KEEP":
        return True
    else:
        cli_err("Invalid UUT {:s}: {:s} detected, please restart the scan process".format(scan_item_str, usr_input))
        return False

def uut_barcode_scan(valid_uut_list=[]):
    uut_scan_rslt = dict()
    already_scanned_list  = list()
    while True:
        # STEP 1: Scan UUT-XXX
        uut_id = None
        usr_prompt = "Please scan UUT ID barcode: "
        raw_scan = raw_input(usr_prompt)

        if re.match("UUT\-[0-9]{3}", raw_scan):
            uut_id = handle_uut_id_scan(raw_scan, uut_scan_rslt, valid_uut_list)
        elif raw_scan == "STOP":
            break
        if uut_id is None:
            cli_err("Invalid UUT ID: {:s}".format(raw_scan))
            continue

        uut_scan_rslt[uut_id] = dict()
        usr_prompt_prefix = id_str(mtp = uut_id)

        # STEPS 2-4: Scan SN, MAC, PN
        for scan_item in ["Serial Number", "MAC Address", "Part Number", "Engineering Date Code"]:
            while True:
                usr_prompt = usr_prompt_prefix + "Please scan {:s} {:s} barcode: ".format(uut_id, scan_item)
                raw_scan = raw_input(usr_prompt)
                if handle_scan(scan_item, raw_scan, already_scanned_list):
                    uut_scan_rslt[uut_id][scan_item] = raw_scan
                    already_scanned_list.append(raw_scan)
                    break
                else:
                    continue

        # remove ':' in entered MAC address
        if re.match(TOR_MAC_QR_FMT, uut_scan_rslt[uut_id]["MAC Address"]):
            uut_scan_rslt[uut_id]["MAC Address"] = uut_scan_rslt[uut_id]["MAC Address"].replace(":","")

        # make the result neat, change key names
        uut_scan_rslt[uut_id]["UUT_VALID"] = True
        uut_scan_rslt[uut_id]["UUT_ID"]  = uut_id
        uut_scan_rslt[uut_id]["UUT_TS"]  = get_timestamp()
        uut_scan_rslt[uut_id]["UUT_SN"]  = uut_scan_rslt[uut_id].pop("Serial Number")
        uut_scan_rslt[uut_id]["UUT_MAC"] = uut_scan_rslt[uut_id].pop("MAC Address")
        uut_scan_rslt[uut_id]["UUT_PN"]  = uut_scan_rslt[uut_id].pop("Part Number")
        uut_scan_rslt[uut_id]["UUT_EDC"] = uut_scan_rslt[uut_id].pop("Engineering Date Code")

    return uut_scan_rslt

def gen_barcode_config_file(file_p, scan_rslt):
    for key in scan_rslt.keys():
        config_lines = [str(scan_rslt[key]["UUT_ID"]) + ":"]
        tmp = "    ID: " +  scan_rslt[key]["UUT_ID"]
        config_lines.append(tmp)
        tmp = "    TS: " +  scan_rslt[key]["UUT_TS"]
        config_lines.append(tmp)
        if scan_rslt[key]["UUT_VALID"]:
            tmp = "    VALID: \"Yes\""
            config_lines.append(tmp)
            tmp = "    SN: \"" + scan_rslt[key]["UUT_SN"] + "\""
            config_lines.append(tmp)
            tmp = "    MAC: \"" + scan_rslt[key]["UUT_MAC"] + "\""
            config_lines.append(tmp)
            tmp = "    EDC: \"" + scan_rslt[key]["UUT_EDC"] + "\""
            config_lines.append(tmp)
            tmp = "    PN: \"" + scan_rslt[key]["UUT_PN"] + "\""
            config_lines.append(tmp)
        else:
            tmp = "    VALID: \"No\""
            config_lines.append(tmp)

        for line in config_lines:
            file_p.write(line + "\n")

def mfg_expect_new(session, exp_list, timeout=None):
    _exp_list = exp_list[:] + [pexpect.TIMEOUT]
    _timeout = timeout
    if _timeout != None:
        idx = session.expect_exact(_exp_list, timeout = _timeout)
    else:
        idx = session.expect_exact(_exp_list)

    if idx >= len(exp_list):
        return -1
    else:
        return idx

def mfg_expect(session, exp_list, timeout=None):
    _exp_list = exp_list[:] + [pexpect.TIMEOUT, pexpect.EOF]
    _timeout = timeout
    if _timeout != None:
        idx = session.expect_exact(_exp_list, timeout = _timeout)
    else:
        idx = session.expect_exact(_exp_list)

    if idx >= len(exp_list):
        return -1
    else:
        return idx


def mfg_expect_re(session, exp_list, timeout=None):
    _exp_list = exp_list[:] + [pexpect.TIMEOUT, pexpect.EOF]
    _timeout = timeout
    if _timeout != None:
        idx = session.expect(_exp_list, timeout = _timeout)
    else:
        idx = session.expect(_exp_list)

    if idx >= len(exp_list):
        return -1
    else:
        return idx

def expect_sendline(handle, cmd, timeout=None):
    # send something to a session that doesnt have defined prompt, just wait for EOF
    handle.sendline(cmd)
    idx = mfg_expect_new(handle, [pexpect.EOF], timeout=timeout)
    if idx < 0:
        return False
    return True

def host_shell_cmd(mtp_mgmt_ctrl, cmd, timeout=None):
    # host session doesnt have defined prompt, just wait for EOF. Thats why each command needs new session
    if timeout is None:
        timeout = MTP_Const.OS_CMD_DELAY
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("### HOST CMD: ### {:s}".format(cmd)) # log the command otherwise pexpect eats it up
    session = pexpect.spawn(cmd, timeout=timeout, logfile=mtp_mgmt_ctrl._diag_filep)
    session.setecho(False)
    idx = mfg_expect_new(session, [pexpect.EOF], timeout=timeout)
    cmd_buf = session.before
    session.close()
    if idx < 0:
        return None
    else:
        return cmd_buf

def get_userid(proj):
    if proj == "t":
        return "root"
    else:
        return "diag"

def network_copy_file(ip_addr, userid, passwd, local_file, remote_dir, logfilep=""):
    temp_remote_dir = "/home/{:s}/".format(userid) #first, scp to a directory where we have permissions

    if logfilep == "":
        logfilep = open("/tmp/{:s}_nc".format(ip_addr), "w+")
    cmd = "md5sum " + local_file
    session = pexpect.spawn(cmd, logfile=logfilep)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.OS_CMD_DELAY)
    match = re.search(r"([0-9a-fA-F]+) +.*", str(session.before))
    session.close()
    if match:
        local_md5sum = match.group(1)
    else:
        cli_err("Execute command {:s} failed".format(cmd))
        return False

    session = pexpect.spawn("scp {:s} {:s} {:s}@{:s}:{:s}".format(get_ssh_option(), local_file, userid, ip_addr, temp_remote_dir), logfile=logfilep)
    session.expect_exact("ssword:")
    session.sendline(passwd)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.MTP_NETCOPY_DELAY)

    # verify the file md5sum
    cmd = get_ssh_connect_cmd(userid, ip_addr)
    session = pexpect.spawn(cmd, logfile=logfilep)
    session.setecho(False)
    session.expect_exact("assword:")
    session.sendline(passwd)
    session.expect_exact(get_linux_prompt_list())

    cmd = "sudo mv {:s}/{:s} {:s}".format(temp_remote_dir, os.path.basename(local_file), remote_dir)
    session.sendline(cmd)
    session.expect_exact(get_linux_prompt_list(), timeout=MTP_Const.OS_SYNC_DELAY)

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
            cli_err("File md5sum mismatch copying to UUT")
            return False
    else:
        cli_err("Execute command {:s} on {:s} failed".format(cmd, ip_addr))
        return False


def network_get_file_old(ip_addr, userid, passwd, local_file, remote_file, logfilep=""):
    if logfilep == "":
        logfilep = open("/tmp/{:s}_ng".format(ip_addr), "w+")
    session = pexpect.spawn("scp {:s} {:s}@{:s}:{:s} {:s}".format(get_ssh_option(), userid, ip_addr, remote_file, local_file), logfile=logfilep)
    session.expect_exact("ssword:")
    session.sendline(passwd)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.MTP_NETCOPY_DELAY)

    cmd = "sync"
    session = pexpect.spawn(cmd, logfile=logfilep)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.OS_SYNC_DELAY)

    cmd = "md5sum " + local_file
    session = pexpect.spawn(cmd, logfile=logfilep)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.OS_CMD_DELAY)
    match = re.search(r"([0-9a-fA-F]+) +.*", str(session.before))
    session.close()
    if match:
        local_md5sum = match.group(1)
    else:
        cli_err("Execute command {:s} failed".format(cmd))
        return False

    # verify the file md5sum
    cmd = get_ssh_connect_cmd(userid, ip_addr)
    session = pexpect.spawn(cmd)
    session.setecho(False)
    session.expect_exact("assword:")
    session.sendline(passwd)
    session.expect_exact(get_linux_prompt_list())

    if "*" not in remote_file: #skip md5sum checksum for wildcard/multifile copies
        # need sudo with new CXOS
        cmd = "sudo md5sum " + remote_file
        session.sendline(cmd)
        session.expect_exact(get_linux_prompt_list(), timeout=MTP_Const.OS_CMD_DELAY)
        match = re.search(r"([0-9a-fA-F]+) +.*", str(session.before))
        session.close()
        # md5sum match
        if match:
            if match.group(1) == local_md5sum:
                return True
            else:
                cli_err("File {:s} md5sum mismatch".format(local_file))
                return False
        else:
            cli_err("Execute command {:s} on {:s} failed".format(cmd, ip_addr))
            return False

    return True

def network_get_file(mtp_mgmt_ctrl, local_file, remote_file):
    """ scp userid@UUT:remote_file local_file """

    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    if not mtp_mgmt_cfg:
        mtp_mgmt_ctrl.cli_log_err("Lost IP - cant connect to UUT", level=0)
        return False
    ip_addr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]

    session = pexpect.spawn("scp {:s} {:s}@{:s}:{:s} {:s}".format(get_ssh_option(), userid, ip_addr, remote_file, local_file), logfile=mtp_mgmt_ctrl._diag_filep)
    session.setecho(False)
    if mfg_expect(session, ["ssword:"]) < 0:
        mtp_mgmt_ctrl.cli_log_err("File copy: could not get password prompt")
        return False
    if not expect_sendline(session, passwd, timeout=MTP_Const.MTP_NETCOPY_DELAY):
        mtp_mgmt_ctrl.cli_log_err("File copy {:s} failed".format(remote_file))
        return False
    session.close()

    cmd = "sync"
    cmd_buf = host_shell_cmd(mtp_mgmt_ctrl, cmd)
    if cmd_buf is None:
        mtp_mgmt_ctrl.cli_log_err("Command {:s} failed".format(cmd))
        return False

    cmd = "md5sum " + local_file
    cmd_buf = host_shell_cmd(mtp_mgmt_ctrl, cmd, timeout=10)
    if cmd_buf is None:
        mtp_mgmt_ctrl.cli_log_err("Command {:s} failed".format(cmd))
        return False
    match = re.search(r"([0-9a-fA-F]+) +.*", str(cmd_buf))
    session.close()
    if match:
        local_md5sum = match.group(1)
    else:
        mtp_mgmt_ctrl.cli_log_err("Execute command {:s} failed".format(cmd))
        return False

    if "*" not in remote_file: #skip md5sum checksum for wildcard/multifile copies
        cmd = "md5sum " + remote_file
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        cmd_buf = mtp_mgmt_ctrl.mtp_get_cmd_buf()
        if not cmd_buf:
            mtp_mgmt_ctrl.cli_log_err("No result from command {:s}".format(cmd))
            return False
        match = re.search(r"([0-9a-fA-F]+) +.*", str(cmd_buf))
        if match:
            if match.group(1) == local_md5sum:
                return True
            else:
                mtp_mgmt_ctrl.cli_log_err("File {:s} md5sum mismatch".format(local_file))
                return False
        else:
            mtp_mgmt_ctrl.cli_log_err("Execute command {:s} on {:s} failed".format(cmd, ip_addr))
            return False

    return True

def console_copy_file(mtp_mgmt_ctrl, ip_addr, local_dir, remote_file):
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("ping -c 4 {:s}".format(ip_addr), timeout=MTP_Const.TOR_SVOS_CMD_DELAY)

    final_file_name = local_dir+os.path.basename(remote_file)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("rm {:s}".format(final_file_name), timeout=MTP_Const.TOR_SVOS_CMD_DELAY)
    Downloadsuccess = False
    for x in range(3):
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd("tftp -g -r {:s} {:s} -b 65000".format(remote_file, ip_addr), sig_list=["100%"], timeout=MTP_Const.TOR_TFTP_DELAY):
            mtp_mgmt_ctrl.cli_log_err("Failed to copy file {:s}, try Again!".format(os.path.basename(remote_file)))
        else:
            Downloadsuccess = True
        if Downloadsuccess:
                    break
    if not Downloadsuccess:
        mtp_mgmt_ctrl.cli_log_err("Failed to copy file {:s}".format(os.path.basename(remote_file)))
        return False        
    cmd = "cp {:s} {:s}".format(os.path.basename(remote_file), final_file_name)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
        mtp_mgmt_ctrl.cli_log_err("{:s} failed".format(cmd))
        return False

    cmd = "sync"
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd, timeout=MTP_Const.OS_SYNC_DELAY):
        mtp_mgmt_ctrl.cli_log_err("{:s} failed".format(cmd))
        return False

    return True

def network_copy_file2(mtp_mgmt_ctrl, local_file, remote_dir):
    ip_addr = mtp_mgmt_ctrl._mgmt_cfg[0]
    userid = mtp_mgmt_ctrl._mgmt_cfg[1]
    passwd = mtp_mgmt_ctrl._mgmt_cfg[2]
    logfilep = mtp_mgmt_ctrl._diag_filep
    temp_remote_dir = "/home/{:s}/".format(userid) #first, scp to a directory where we have permissions

    if logfilep == "":
        logfilep = open("/tmp/{:s}_nc".format(ip_addr), "w+")
    cmd = "md5sum " + local_file
    session = pexpect.spawn(cmd, logfile=logfilep)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.OS_CMD_DELAY)
    match = re.search(r"([0-9a-fA-F]+) +.*", str(session.before))
    session.close()
    if match:
        local_md5sum = match.group(1)
    else:
        cli_err("Execute command {:s} failed".format(cmd))
        return False

    session = pexpect.spawn("scp {:s} {:s} {:s}@{:s}:{:s}".format(get_ssh_option(), local_file, userid, ip_addr, temp_remote_dir), logfile=logfilep)
    session.expect_exact("ssword:")
    session.sendline(passwd)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.MTP_NETCOPY_DELAY)

    # verify the file md5sum
    cmd = "sudo mv {:s}/{:s} {:s}".format(temp_remote_dir, os.path.basename(local_file), remote_dir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    cmd = "sync"
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    cmd = "md5sum " + remote_dir + os.path.basename(local_file)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
    cmd_buf = mtp_mgmt_ctrl.mtp_get_cmd_buf()
    if not cmd_buf:
        cli_err("No result from command {:s}".format(cmd))
        return False
    match = re.search(r"([0-9a-fA-F]+) +.*", str(cmd_buf))

    # md5sum match
    if match:
        if match.group(1) == local_md5sum:
            return True
        else:
            cli_err("File md5sum mismatch copying to UUT")
            return False
    else:
        cli_err("Execute command {:s} on {:s} failed".format(cmd, ip_addr))
        return False

def mtp_clear_console(mtp_mgmt_ctrl):
    if mtp_mgmt_ctrl._ts_cfg:
        if mtp_mgmt_ctrl._use_usb_console:
            mtp_mgmt_ctrl.cli_log_inf("Clearing USB console line")
            ts_cfg = mtp_mgmt_ctrl._usb_ts_cfg
        else:
            mtp_mgmt_ctrl.cli_log_inf("Clearing console line")
            ts_cfg = mtp_mgmt_ctrl._ts_cfg
        ts_ip = ts_cfg[0]
        ts_port = ts_cfg[1]
        ts_user = ts_cfg[2]
        ts_pass = ts_cfg[3]
        telnet_cmd = mtp_mgmt_ctrl.mtp_get_telnet_command()
        telnet_cmd = telnet_cmd[:-4] #remove port
        session = pexpect.spawn(telnet_cmd, logfile=mtp_mgmt_ctrl._diag_filep)
        prompt_list = ["ogin:","assword:", "]>", ">", "#"]
        while True:
            idx = mfg_expect(session, prompt_list)
            if idx < 0:
                mtp_mgmt_ctrl.cli_log_err("Terminal server is unavailable", level=0)
                return False
            elif idx == 0:
                session.sendline(ts_user)
            elif idx == 1:
                session.setecho(False)
                session.waitnoecho()
                session.sendline(ts_pass)
                # session.setecho(True)
            elif idx == 2:
                 session.sendline("set deviceport port {:s} reset".format(ts_port))
                 session.sendline()
                 session.expect("Device Port settings successfully updated.")
                 session.sendline("logout")
                 session.sendline()
                 break
            elif idx == 3:
                session.sendline("en")
            elif idx == 4:
                session.sendline("clear line {:s}".format(ts_port))
                session.sendline()
                session.sendline()
                session.expect("OK")
                session.sendline("clear line {:s}".format(ts_port))
                session.sendline()
                session.sendline()
                session.expect("OK")
                break
        session.close()
        return True

def mtp_init_test_script(mtp_mgmt_ctrl, mtp_script_dir, mtp_script_pkg, logfile_dir="/dev/null", extra_script=None):
    if mtp_mgmt_ctrl._uut_type == UUT_Type.TOR:
        # need this path on fresh-power on
        cmd = "export PYTHONPATH=/fs/nos/home_diag/python_files/lib/python2.7/site-packages/"
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("{:s} failed".format(cmd))
            return False

    onboard_home_dir = mtp_mgmt_ctrl.get_homedir()
    cmd = "cd {:s}".format(onboard_home_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("{:s} failed".format(cmd))
        return False
        
    if extra_script:
        cmd = "cp {:s} {:s}".format(extra_script, mtp_script_dir)
        os.system(cmd)
    cmd = "cp -r lib/ config/ {:s}".format(mtp_script_dir)
    os.system(cmd)
    cmd = "cp -r {:s}/*.log {:s}".format(logfile_dir, mtp_script_dir)
    os.system(cmd)
    cmd = "tar czf {:s} {:s}".format(mtp_script_pkg, mtp_script_dir)
    os.system(cmd)
    # remove the lib config for the next run
    if extra_script:
        cmd = "rm -f {:s}/{:s}".format(mtp_script_dir, os.path.basename(extra_script))
        os.system(cmd)
    cmd = "rm -rf {:s}/lib {:s}/config {:s}/".format(mtp_script_dir, mtp_script_dir, logfile_dir)
    os.system(cmd)

    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
    # download the test script pkg
    if not network_copy_file(ipaddr, userid, passwd, mtp_script_pkg, onboard_home_dir, mtp_mgmt_ctrl._diag_filep):
        mtp_mgmt_ctrl.cli_log_err("Copy Test script failed... Abort")
        return False
    # remove the stale test script
    cmd = "rm -rf {:s}".format(onboard_home_dir+"/"+mtp_script_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False
    # unpack the test script pkg
    cmd = "tar zxf {:s} -C {:s}".format(onboard_home_dir+"/"+mtp_script_pkg, onboard_home_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False
    # remove the test script pkg
    cmd = "rm -f {:s}".format(onboard_home_dir+"/"+mtp_script_pkg)
    os.system(cmd)
    return True


def mtpid_list_select(mtp_cfg_db, preselect=[]):
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
    if preselect:
        sub_mtpid_list = list()
        for mtpid in preselect:
            if mtpid not in mtpid_list:
                cli_err("Invalid MTP ID: {:s}".format(mtpid))
            else:
                sub_mtpid_list.append(mtpid)
    else:
        sub_mtpid_list = multiple_select_menu("Select MTP Chassis", mtpid_list)
    return sub_mtpid_list


def mtpid_list_poweron(mtp_mgmt_ctrl_list):
    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.mtp_apc_pwr_on()
        mtp_mgmt_ctrl.cli_log_inf("Power on APC, Wait {:d} seconds for system coming up".format(MTP_Const.MTP_POWER_ON_DELAY), level=0)
    count_down(MTP_Const.MTP_POWER_ON_DELAY)


def mtpid_list_poweroff(mtp_mgmt_ctrl_list):
    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.mtp_mgmt_poweroff()
        mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
    count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.mtp_apc_pwr_off()
        mtp_mgmt_ctrl.cli_log_inf("Power off APC, Wait {:d} seconds for APC shutdown".format(MTP_Const.MTP_POWER_CYCLE_DELAY), level=0)
    count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)

def tor_uut_list_poweroff(mtp_mgmt_ctrl_list):
    # for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
    #     mtp_mgmt_ctrl.mtp_mgmt_poweroff()
    #     mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
    # count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.mtp_apc_pwr_off()
        mtp_mgmt_ctrl.cli_log_inf("Power off APC, Wait {:d} seconds for APC shutdown".format(MTP_Const.MTP_POWER_CYCLE_DELAY), level=0)
    count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)

def mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, fan_spd=MTP_Const.MFG_EDVT_NORM_FAN_SPD, stage=None):
    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP chassis", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected\n", level=0)

    # diag environment pre init
    if not mtp_mgmt_ctrl.mtp_diag_pre_init("/dev/null"):
        mtp_mgmt_ctrl.cli_log_err("Unable to pre-init diag environment", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False

    # diag environment post init
    if not mtp_mgmt_ctrl.mtp_diag_post_init(mtp_capability, stage):
        mtp_mgmt_ctrl.cli_log_err("Unable to post-init diag environment", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False

    # get the mtp system info
    if not mtp_mgmt_ctrl.mtp_sys_info_disp():
        mtp_mgmt_ctrl.cli_log_err("Unable to retrieve MTP system info", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False

    # PSU/FAN absent, powerdown MTP
    if not mtp_mgmt_ctrl.mtp_hw_init(fan_spd):
        mtp_mgmt_ctrl.cli_log_err("MTP HW Init Fail", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False

    # init all the nic.
    if not mtp_mgmt_ctrl.mtp_nic_init():
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC type, present failed", level=0)
        mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False
    return True


def mtp_update_firmware(mtp_mgmt_ctrl, image_list, image_on_mtp):
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    mtp_ip_addr = mtp_mgmt_cfg[0]
    mtp_usrid = mtp_mgmt_cfg[1]
    mtp_passwd = mtp_mgmt_cfg[2]
    image_dir = "/home/diag/"

    done_list = []
    for image in image_list:
        if image == "":
            continue
        if image not in image_on_mtp and image not in done_list:
            image_rel_path = "release/{:s}".format(image)
            if not file_exist(image_rel_path):
                mtp_mgmt_ctrl.cli_log_err("Firmware image {:s} doesn't exist... Abort".format(image_rel_path), level=0)
                return False

            mtp_mgmt_ctrl.cli_log_inf("Copy Firmware image {:s}".format(image), level=0)
            if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, image_rel_path, image_dir):
                mtp_mgmt_ctrl.cli_log_err("Copy Firmware image {:s} failed... Abort".format(image), level=0)
                return False
            mtp_mgmt_ctrl.cli_log_inf("Copy Firmware image {:s} complete".format(image), level=0)
            done_list.append(image)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Firmware image {:s} on MTP is up-to-date".format(image), level=0)

    return True


def mtp_update_diag_image(mtp_mgmt_ctrl, mtp_image, nic_image, image_on_mtp, homedir="/home/diag/", force_update=False):
    if not force_update and mtp_image in image_on_mtp and nic_image in image_on_mtp:
        mtp_mgmt_ctrl.cli_log_inf("Diag images on MTP is up-to-date", level=0)
        return True

    # cleanup the stale diag images
    cmd = "rm -f {:s}image_a*.tar".format(homedir)
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    if "amd64" not in mtp_image:
        mtp_mgmt_ctrl.cli_log_err("Wrong MTP image: {:s}".format(mtp_image), level=0)
        return False
    if "arm64" not in nic_image:
        mtp_mgmt_ctrl.cli_log_err("Wrong NIC image: {:s}".format(nic_image), level=0)
        return False

    mtp_image_file = "release/{:s}".format(mtp_image)
    if not file_exist(mtp_image_file):
        mtp_mgmt_ctrl.cli_log_err("MTP Diag image {:s} doesn't exist... Abort".format(mtp_image_file), level=0)
        return False
    nic_image_file = "release/{:s}".format(nic_image)
    if not file_exist(nic_image_file):
        mtp_mgmt_ctrl.cli_log_err("NIC Diag image {:s} doesn't exist... Abort".format(nic_image_file), level=0)
        return False

    mtp_mgmt_ctrl.cli_log_inf("Copy MTP Chassis image: {:s}".format(mtp_image_file), level=0)
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    mtp_ip_addr = mtp_mgmt_cfg[0]
    mtp_usrid = mtp_mgmt_cfg[1]
    mtp_passwd = mtp_mgmt_cfg[2]
    remote_dir = homedir
    logfilep = mtp_mgmt_ctrl._diag_filep

    if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir, logfilep=logfilep):
        mtp_mgmt_ctrl.cli_log_err("Copy MTP Chassis image failed... Abort", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("Update MTP Chassis image: {:s}".format(os.path.basename(mtp_image_file)), level=0)
    if not mtp_mgmt_ctrl.mtp_update_mtp_diag_image(remote_dir + os.path.basename(mtp_image_file)):
        mtp_mgmt_ctrl.cli_log_err("Update MTP Chassis image failed... Abort", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("Update MTP Chassis image complete\n", level=0)

    mtp_mgmt_ctrl.cli_log_inf("Copy NIC Diag image: {:s}".format(nic_image_file), level=0)
    if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, nic_image_file, remote_dir):
        mtp_mgmt_ctrl.cli_log_err("Copy NIC Diag image failed... Abort", level=0)
        return False

    mtp_mgmt_ctrl.cli_log_inf("Update NIC Diag image: {:s}".format(os.path.basename(nic_image_file)), level=0)
    if not mtp_mgmt_ctrl.mtp_update_nic_diag_image(remote_dir + os.path.basename(nic_image_file)):
        mtp_mgmt_ctrl.cli_log_err("Update NIC Diag image failed... Abort", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("Update NIC Diag image complete\n", level=0)

    return True

def mtp_update_fst_image(mtp_mgmt_ctrl, mtp_image, nic_image, image_on_mtp):
    if mtp_image in image_on_mtp and nic_image in image_on_mtp:
        mtp_mgmt_ctrl.cli_log_inf("Diag images on MTP is up-to-date", level=0)
        return True

    # cleanup the stale diag images
    cmd = "rm -f /home/diag/image_a*.tar"
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    if "penctl.linux" not in mtp_image:
        mtp_mgmt_ctrl.cli_log_err("Wrong FST Penctl image: {:s}".format(mtp_image), level=0)
        return False
    if "penctl.token" not in nic_image:
        mtp_mgmt_ctrl.cli_log_err("Wrong FST Penctl TOKEN image: {:s}".format(nic_image), level=0)
        return False

    mtp_image_file = "release/{:s}".format(mtp_image)
    if not file_exist(mtp_image_file):
        mtp_mgmt_ctrl.cli_log_err("MTP Penctl image {:s} doesn't exist... Abort".format(mtp_image_file), level=0)
        return False
    nic_image_file = "release/{:s}".format(nic_image)
    if not file_exist(nic_image_file):
        mtp_mgmt_ctrl.cli_log_err("NIC Penctl_TOKEN image {:s} doesn't exist... Abort".format(nic_image_file), level=0)
        return False

    mtp_mgmt_ctrl.cli_log_inf("Copy FST Penctl image: {:s}".format(mtp_image_file), level=0)
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    mtp_ip_addr = mtp_mgmt_cfg[0]
    mtp_usrid = mtp_mgmt_cfg[1]
    mtp_passwd = mtp_mgmt_cfg[2]
    remote_dir = "/home/diag/"

    if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir):
        mtp_mgmt_ctrl.cli_log_err("Copy FST Penctl image failed... Abort", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("Update FST Penctl image: {:s}".format(os.path.basename(mtp_image_file)), level=0)
    if not mtp_mgmt_ctrl.mtp_update_mtp_diag_image(remote_dir + os.path.basename(mtp_image_file)):
        mtp_mgmt_ctrl.cli_log_err("Update FST Penctl image failed... Abort", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("Update FST Penctl image complete\n", level=0)

    mtp_mgmt_ctrl.cli_log_inf("Copy FST Penctl TOKEN image: {:s}".format(nic_image_file), level=0)
    if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, nic_image_file, remote_dir):
        mtp_mgmt_ctrl.cli_log_err("Copy FST Penctl TOKEN image failed... Abort", level=0)
        return False

    mtp_mgmt_ctrl.cli_log_inf("Update FST Penctl TOKEN image: {:s}".format(os.path.basename(nic_image_file)), level=0)
    if not mtp_mgmt_ctrl.mtp_update_nic_diag_image(remote_dir + os.path.basename(nic_image_file)):
        mtp_mgmt_ctrl.cli_log_err("Update FST Penctl TOKEN image failed... Abort", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("Update FST PENCTL image complete\n", level=0)

    return True

def mtp_update_packages(mtp_mgmt_ctrl, packages_src_dir, packages_dst_dir):
    cmd = "mkdir -p {:s}".format(packages_dst_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("{:s} failed".format(cmd))
        return False

    cmd = "ls " + packages_src_dir
    session = pexpect.spawn(cmd, logfile=mtp_mgmt_ctrl._diag_filep)
    session.expect_exact(pexpect.EOF, timeout=MTP_Const.OS_CMD_DELAY)
    if "No such file" in session.before:
        session.close()
        mtp_mgmt_ctrl.cli_log_err("Packages missing from release folder", level=0)
        return False
    packages_list = session.before.split()
    session.close()

    onboard_packages = mtp_mgmt_ctrl.mtp_diag_get_img_files(packages_dst_dir)

    for package in packages_list:
        # skip doing rm -rf on packages folder
        if package in onboard_packages:
            mtp_mgmt_ctrl.cli_log_inf("{:s} package already exists".format(package))
            continue
        if not network_copy_file2(mtp_mgmt_ctrl, packages_src_dir+package, packages_dst_dir):
            mtp_mgmt_ctrl.cli_log_err("Copy python packages failed", level=0)
            return False
        cmd = "cd {:s}".format(packages_dst_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("{:s} failed".format(cmd))
            return False
        cmd = "tar -xf {:s} -C {:s}".format(package, packages_dst_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("{:s} failed".format(cmd))
            return False
        mtp_mgmt_ctrl.cli_log_inf("Installed package {:s}".format(package))

    return True

def fail_all_slots(mtp_mgmt_ctrl):
    """
     Call this function when failing a script BEFORE any dsp test results have come.
     e.g. whole MTP fails: report as all cards failed
     e.g. connection problem: report as all cards failed
    """
    if mtp_mgmt_ctrl._uut_type == UUT_Type.TOR:
        # single slot
        slot = 0
        key = nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
        return

    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if not mtp_mgmt_ctrl._nic_prsnt_list[slot]:
            continue
        key = nic_key(slot)
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)
        card_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if card_type == NIC_Type.NAPLES25SWM and mtp_mgmt_ctrl.mtp_get_swmtestmode(slot) == Swm_Test_Mode.ALOM:
            alom_sn = mtp_mgmt_ctrl.mtp_get_nic_alom_sn(slot)
            mtp_mgmt_ctrl.cli_log_inf("{:s} {:s} {:s} {:s}".format(key, nic_type, alom_sn, MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL), level=0)

def post_fail_steps(mtp_mgmt_ctrl, slot):
    # first, exit out of nic ssh if pexpect handle is there
    mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_exec_cmds(list(), timeout=1)

    mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
    mtp_mgmt_ctrl.mtp_mgmt_check_cpld_debug_bits(slot)
    mtp_mgmt_ctrl.mtp_mgmt_set_nic_avs_post(slot)
    mtp_mgmt_ctrl.mtp_nic_check_diag_boot(slot)

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

def flx_soap_save_uut_result_xml(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list):
    test_xml = ""
    for test, test_rslt, err_dsc, err_code in zip(test_list, test_rslt_list, err_dsc_list, err_code_list):
        # (test, status, value, description, failure code)
        value = ""
        test_xml += FLX_SAVE_UUT_TEST_RSLT_FMT.format(test, test_rslt, value, err_dsc, err_code)

    #(stage, SN, start_ts, duration, stop_ts, result)

    factory = flx_sn_to_factory(sn)
    if not factory:
        print("Unable to locate flex factory based on sn: {:s}".format(sn))
        return None

    if factory == FLX_Factory.PENANG:
        ff_pn = flx_stage_to_penang(stage)
        return FLX_PENANG_SAVE_UUT_RSLT_XML_HEAD + \
               FLX_PENANG_SAVE_UUT_RSLT_ENTRY_FMT.format(ff_pn,sn,str(start_ts),str(duration),str(stop_ts),rslt,nic_type,duration,rslt) + \
               test_xml + \
               FLX_SAVE_UUT_RSLT_ENTRY_END + \
               FLX_SAVE_UUT_RSLT_XML_TAIL
    else:
        return FLX_SAVE_UUT_RSLT_XML_HEAD + \
               FLX_SAVE_UUT_RSLT_ENTRY_FMT.format(stage,sn,str(start_ts),str(duration),str(stop_ts),rslt,nic_type,duration,rslt) + \
               test_xml + \
               FLX_SAVE_UUT_RSLT_ENTRY_END + \
               FLX_SAVE_UUT_RSLT_XML_TAIL


def flx_soap_get_uut_info_xml(stage, sn):
    factory = flx_sn_to_factory(sn)
    if not factory:
        print("Unable to locate flex factory based on sn: {:s}".format(sn))
        return None

    if factory == FLX_Factory.PENANG:
        ff_pn = flx_stage_to_penang(stage)
        return FLX_PENANG_GET_UUT_INFO_XML_HEAD + \
               FLX_PENANG_GET_UUT_INFO_ENTRY_FMT.format(sn, ff_pn) + \
               FLX_GET_UUT_INFO_XML_TAIL
    else:
        return FLX_GET_UUT_INFO_XML_HEAD + \
               FLX_GET_UUT_INFO_ENTRY_FMT.format(sn, stage) + \
               FLX_GET_UUT_INFO_XML_TAIL


def flx_sn_to_factory(sn):
    if re.match(FLX_PENANG_BUILD_SN_FMT, sn):
        return FLX_Factory.PENANG
    elif re.match(FLX_MILPITAS_BUILD_SN_FMT, sn):
        return FLX_Factory.MILPITAS
    else:
        return None


def flx_stage_to_penang(stage):
    if stage == FF_Stage.FF_DL:
        return FPN_FF_Stage.FF_DL
    elif stage == FF_Stage.FF_CFG:
        return FPN_FF_Stage.FF_CFG
    elif stage == FF_Stage.FF_P2C:
        return FPN_FF_Stage.FF_P2C
    elif stage == FF_Stage.FF_2C:
        return FPN_FF_Stage.FF_2C
    elif stage == FF_Stage.FF_4C_H:
        return FPN_FF_Stage.FF_4C_H
    elif stage == FF_Stage.FF_4C_L:
        return FPN_FF_Stage.FF_4C_L
    elif stage == FF_Stage.FF_SWI:
        return FPN_FF_Stage.FF_SWI
    elif stage == FF_Stage.FF_FST:
        return FPN_FF_Stage.FF_FST
    else:
        print("Unknown Flex Flow Stage: {:s}".format(stage))
        return None

def soap_post_report(xml, factory=FLX_Factory.PENANG):
    if factory == FLX_Factory.PENANG:
        webservice = httplib.HTTP(FLX_PENANG_WEBSERVER)
        webservice.putrequest("POST", FLX_PENANG_API_URL)
        webservice.putheader("Content-Type", "text/xml")
        webservice.putheader("SOAPAction", FLX_PENANG_SAVE_UUT_RSLT_SOAP)
    else:
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


def soap_get_uut_info(xml, factory=FLX_Factory.PENANG):
    if factory == FLX_Factory.PENANG:
        webservice = httplib.HTTP(FLX_PENANG_WEBSERVER)
        webservice.putrequest("POST", FLX_PENANG_API_URL)
        webservice.putheader("Content-Type", "text/xml")
        webservice.putheader("SOAPAction", FLX_PENANG_GET_UUT_INFO_SOAP)
    else:
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


def flx_web_srv_post_uut_report(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list):
    factory = flx_sn_to_factory(sn)
    if not factory:
        print("Unable to locate flex factory based on sn: {:s}".format(sn))
        return False

    xml = flx_soap_get_uut_info_xml(stage, sn)
    if not xml:
        return False

    ret = soap_get_uut_info(xml, factory)
    if int(ret) != 0:
        return False

    xml = flx_soap_save_uut_result_xml(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list)
    if not xml:
        return False

    ret = soap_post_report(xml, factory)
    if int(ret) != 0:
        return False

    return True


def get_mtp_logfile(mtp_mgmt_ctrl, log_dir, mtp_id, mtp_test_summary, stage):
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]

    mtp_mgmt_ctrl.cli_log_inf("Collecting {:s} log files started".format(stage), level=0)

    log_timestamp = get_timestamp()
    if stage == FF_Stage.FF_DL:
        # log subdir
        sub_dir = MTP_DIAG_Logfile.MFG_DL_LOG_DIR.format(mtp_id, log_timestamp)
        # log pkg filename
        log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_DL_LOG_PKG_FILE.format(mtp_id, log_timestamp)
        # onboard log files
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_DL_LOG_FILES
        # test summary logfile
        test_log_file = "{:s}mtp_test.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
    elif stage == FF_Stage.FF_CFG:
        # log subdir
        sub_dir = MTP_DIAG_Logfile.MFG_CFG_LOG_DIR.format(mtp_id, log_timestamp)
        # log pkg filename
        log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_CFG_LOG_PKG_FILE.format(mtp_id, log_timestamp)
        # onboard log files
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_CFG_LOG_FILES
        # test summary logfile
        test_log_file = "{:s}test_cfg.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_test_cfg.log".format(mtp_id)
    elif stage == FF_Stage.FF_P2C:
        # log subdir
        sub_dir = MTP_DIAG_Logfile.MFG_P2C_LOG_DIR.format(mtp_id, log_timestamp)
        # log pkg filename
        log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_P2C_LOG_PKG_FILE.format(mtp_id, log_timestamp)
        # onboard log files
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES
        # test summary logfile
        test_log_file = "{:s}mtp_test.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
    elif stage == FF_Stage.FF_2C_HV or stage == FF_Stage.FF_2C_LV:
        # log subdir
        sub_dir = MTP_DIAG_Logfile.MFG_2C_LOG_DIR.format(stage, mtp_id, log_timestamp)
        # log pkg filename
        log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_2C_LOG_PKG_FILE.format(stage, mtp_id, log_timestamp)
        # onboard log files
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES
        # test summary logfile
        test_log_file = "{:s}mtp_test.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
    elif stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L:
        # log subdir
        sub_dir = MTP_DIAG_Logfile.MFG_4C_LOG_DIR.format(stage, mtp_id, log_timestamp)
        # log pkg filename
        log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_4C_LOG_PKG_FILE.format(stage, mtp_id, log_timestamp)
        # onboard log files
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES
        # test summary logfile
        test_log_file = "{:s}mtp_test.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
    elif stage == FF_Stage.FF_SWI:
        # log subdir
        sub_dir = MTP_DIAG_Logfile.MFG_SWI_LOG_DIR.format(mtp_id, log_timestamp)
        # log pkg filename
        log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_SWI_LOG_PKG_FILE.format(mtp_id, log_timestamp)
        # onboard log files
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_SWI_LOG_FILES
        # test summary logfile
        test_log_file = "{:s}mtp_test.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_mtp_testlog".format(mtp_id)
        # copy csp files from MTP to Server
        test_onboard_csp_log_files = MTP_DIAG_Logfile.ONBOARD_CSP_LOG_FILES
    elif stage == FF_Stage.FF_FST:
        # log subdir
        sub_dir = MTP_DIAG_Logfile.MFG_FST_LOG_DIR.format(mtp_id, log_timestamp)
        # log pkg filename
        log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_FST_LOG_PKG_FILE.format(mtp_id, log_timestamp)
        # onboard log files
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_FST_LOG_FILES
        # test summary logfile
        test_log_file = "{:s}test_fst.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_test_fst.log".format(mtp_id)
    else:
        mtp_mgmt_ctrl.cli_log_err("Unknown FF Stage: {:s}".format(stage), level=0)
        return None

    # local dir to temporarily store test summary
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format("log/")
    err = os.system(cmd)
    if err:
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s}".format(cmd), level=0)
        return None
    # temporary dir for log files on MTP
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir+sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None
    # move onboard log files
    cmd = "mv {:s} {:s}".format(test_onboard_log_files, log_dir+sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

    # for DL/P2C/4C test, extra logfiles are needed
    if stage == FF_Stage.FF_DL:
        asic_log_dir = log_dir + "asic_logs/"
        cmd = "mv {:s} {:s}".format(asic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
    elif stage == FF_Stage.FF_P2C:
        diag_log_dir = log_dir + "diag_logs/"
        asic_log_dir = log_dir + "asic_logs/"
        nic_log_dir = log_dir + "nic_logs/"
        # move the extra logfile
        cmd = "mv {:s} {:s}".format(diag_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(asic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(nic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
    elif stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L or stage == FF_Stage.FF_2C_LV or stage == FF_Stage.FF_2C_HV:
        hv_diag_log_dir = log_dir + "hv_diag_logs/"
        hv_asic_log_dir = log_dir + "hv_asic_logs/"
        hv_nic_log_dir = log_dir + "hv_nic_logs/"
        lv_diag_log_dir = log_dir + "lv_diag_logs/"
        lv_asic_log_dir = log_dir + "lv_asic_logs/"
        lv_nic_log_dir = log_dir + "lv_nic_logs/"
        # move the extra logfile
        cmd = "mv {:s} {:s}".format(hv_diag_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(hv_asic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(hv_nic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        # move the extra logfile
        cmd = "mv {:s} {:s}".format(lv_diag_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(lv_asic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
        cmd = "mv {:s} {:s}".format(lv_nic_log_dir, log_dir+sub_dir)
        if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
            mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
            return None
    # for SWI/FST, no extra logfiles
    else:
        pass

    logfile_list = list()
    # pkg the onboard logs
    cmd = MFG_DIAG_CMDS.MFG_LOG_PKG_FMT.format(log_pkg_file, log_dir, sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

    if not network_get_file(ipaddr, userid, passwd, local_test_log_file, test_log_file):
        mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test summary file {:}".format(test_log_file), level=0)
        return None

    # analyze test summary logfile
    try:
        with open(local_test_log_file, 'r') as fp:
            buf = fp.read()
    except:
        mtp_mgmt_ctrl.cli_log_err("Unable to open MTP test summary file {:}".format(test_log_file), level=0)
        return None

    nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
    nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
    nic_skip_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_SKIP_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_SKIP)
    fail_match = re.findall(nic_fail_reg_exp, buf)
    pass_match = re.findall(nic_pass_reg_exp, buf)
    skip_match = re.findall(nic_skip_reg_exp, buf)

    log_hard_copy_flag = True
    log_relative_link = None
    temp_nic_type = None
    csp_log_dir = None

    for slot, nic_type, sn in fail_match + pass_match:
        # report doesn't have valid serial number
        if nic_type:
            temp_nic_type = nic_type
        if sn == "None":
            sn = NIC_Type.UNKNOWN
        if stage == FF_Stage.FF_DL:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_DL_LOG_DIR_FMT.format(nic_type, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_DL_LOG_DIR_FMT.format(nic_type, sn)
        if stage == FF_Stage.FF_CFG:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_CFG_LOG_DIR_FMT.format(nic_type, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_CFG_LOG_DIR_FMT.format(nic_type, sn)
        elif stage == FF_Stage.FF_P2C:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_P2C_LOG_DIR_FMT.format(nic_type, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_P2C_LOG_DIR_FMT.format(nic_type, sn)
        elif stage == FF_Stage.FF_2C_HV or stage == FF_Stage.FF_2C_LV:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_2C_LOG_DIR_FMT.format(nic_type, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_2C_LOG_DIR_FMT.format(nic_type, sn)
        elif stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_4C_LOG_DIR_FMT.format(nic_type, stage, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_4C_LOG_DIR_FMT.format(nic_type, stage, sn)
        elif stage == FF_Stage.FF_SWI:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_SWI_LOG_DIR_FMT.format(nic_type, sn)
                csp_log_dir = MTP_DIAG_Logfile.DIAG_MFG_CSP_LOG_DIR_FMT.format(nic_type)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_SWI_LOG_DIR_FMT.format(nic_type, sn)
                csp_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_CSP_LOG_DIR_FMT.format(nic_type)
        elif stage == FF_Stage.FF_FST:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_FST_LOG_DIR_FMT.format(nic_type, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_FST_LOG_DIR_FMT.format(nic_type, sn)
        else:
            pass

        if GLB_CFG_MFG_TEST_MODE:
            cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir)
            os.system(cmd)
        else:
            err_code = os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(mfg_log_dir))
            if not err_code:
                # try to change permission of the stage if this is first time created
                # this will fail if someone else created them...ask them to chmod 777
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))
                if stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L:
                    # since 4C directory is organized as /mfg_log/type/4C/4C-H/...
                    os.system("chmod 777 {:s}".format(mfg_log_dir+"/../.."))
            else:
                # chdir from mfg_log/type/stage/sn --> mfg_log/MERGE/type/stage/sn
                mfg_log_dir = mfg_log_dir.replace(nic_type, "MERGE/"+nic_type)
                os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(mfg_log_dir))
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))
                if stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L:
                    os.system("chmod 777 {:s}".format(mfg_log_dir+"/../.."))

        # copy the onboard logs only once
        if log_hard_copy_flag:
            qa_log_pkg_file = mfg_log_dir + os.path.basename(log_pkg_file)
            if not network_get_file(ipaddr, userid, passwd, qa_log_pkg_file, log_pkg_file):
                mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file to {:}".format(qa_log_pkg_file), level=0)
                continue

            mtp_mgmt_ctrl.cli_log_inf("[{:s}] Collecting log file {:s}".format(sn, qa_log_pkg_file))
            os.system("./aruba-log.sh {:s}".format(qa_log_pkg_file))

            # It is fine to do hard copy
            #log_hard_copy_flag = False
            # relative link is ../sn/log_pkg_file
            log_relative_link = "../{:s}/{:s}".format(sn, os.path.basename(log_pkg_file))
        # create hard link
        else:
            mtp_mgmt_ctrl.cli_log_inf("[{:s}] Create link log file {:s}".format(sn, mfg_log_dir+os.path.basename(log_pkg_file)))
            chdir_cmd = "cd {:s}".format(mfg_log_dir)
            ln_cmd = MFG_DIAG_CMDS.MFG_LOG_LINK_FMT.format(log_relative_link, os.path.basename(log_pkg_file))
            cmd = "{:s} && {:s}".format(chdir_cmd, ln_cmd)
            os.system(cmd)
        
    if stage == FF_Stage.FF_SWI:
        # csp log files    
        cmd = "ls --color=never /home/diag/diag/asic/asic_src/ip/cosim/tclsh/csp*"
     
        mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)
        listoffileoutput = mtp_mgmt_ctrl.mtp_get_cmd_buf()
        listoffile = listoffileoutput.split()
        
        listcspfiletoupload = list()
        for cspfile in listoffile:
            if 'txt' in cspfile:
                listcspfiletoupload.append(cspfile)
        for cspfilepath in listcspfiletoupload:
            if not csp_log_dir:
                mtp_mgmt_ctrl.cli_log_err("Unable to copy CSP log file", level=0)
                break
            if GLB_CFG_MFG_TEST_MODE:
                cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(csp_log_dir)
                os.system(cmd)
            else:
                err_code = os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(csp_log_dir))
                if not err_code:
                    os.system("chmod 777 {:s}".format(csp_log_dir+"/.."))
                else:
                    csp_log_dir = csp_log_dir.replace("CSP_REC", "MERGE/CSP_REC")
                    os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(csp_log_dir))
                    os.system("chmod 777 {:s}".format(csp_log_dir+"/.."))
            csp_log_file = csp_log_dir + os.path.basename(cspfilepath)
            if not network_get_file(ipaddr, userid, passwd, csp_log_file, cspfilepath):
                mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file {:}".format(csp_log_file), level=0)
                continue
            mtp_mgmt_ctrl.cli_log_inf("Collecting csp log file {:s}".format(csp_log_file))

    for slot in skip_match:
        mtp_test_summary.append((slot, "SKIPPED", "SLOT", True))

    for slot, nic_type, sn in fail_match:
        mtp_test_summary.append((slot, sn, nic_type, False))

    for slot, nic_type, sn in pass_match:
        mtp_test_summary.append((slot, sn, nic_type, True))

    # clear the onboard logs
    logfile_list.append(log_pkg_file)
    logfile_list.append(log_dir+sub_dir)
    #cmd = "rm -rf {:s}".format(" ".join(logfile_list))
    # if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
    #     mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
    #     return None

    mtp_mgmt_ctrl.cli_log_inf("Collecting {:s} log files complete".format(stage), level=0)

    return local_test_log_file


def mfg_report(mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, stage):
    mtp_cli_id_str = id_str(mtp = mtp_id)
    duration = mtp_stop_ts - mtp_start_ts

    with open(test_log_file, 'r') as fp:
        buf = fp.read()

    # MTP related error, don't post any report
    if MTP_DIAG_Report.MTP_DIAG_REGRESSION_FAIL in buf:
        cli_inf(mtp_cli_id_str + "MTP Setup fails, no report will be generated")
        cmd = "cp {:s} {:s}.bak".format(test_log_file, test_log_file)
        os.system(cmd)
        return

    cli_inf(mtp_cli_id_str + "Start posting test report")
    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL in buf:
        nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
        match = re.findall(nic_fail_reg_exp, buf)
        for slot, sn_type, sn in match:
            test_list = list()
            test_rslt_list = list()
            err_dsc_list = list()
            err_code_list = list()
            nic_cli_id_str = id_str(mtp=mtp_id, nic=int(slot), base=0)
            # find all test status
            nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
            sub_match = re.findall(nic_test_rslt_reg_exp, buf)
            for dsp, test, result in sub_match:
                test_list.append("{:s}-{:s}".format(dsp, test))
                test_rslt_list.append(result)
                err_dsc_list.append(nic_cli_id_str)
                err_code_list.append(result)
            ret = flx_web_srv_post_uut_report(stage, sn_type, sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list)
            if not ret:
                cli_err(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
            else:
                cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))

    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS in buf:
        nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
        match = re.findall(nic_pass_reg_exp, buf)
        for slot, sn_type, sn in match:
            test_list = list()
            test_rslt_list = list()
            err_dsc_list = list()
            err_code_list = list()
            nic_cli_id_str = id_str(mtp=mtp_id, nic=int(slot), base=0)
            # find all test status
            nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
            sub_match = re.findall(nic_test_rslt_reg_exp, buf)
            for dsp, test, result in sub_match:
                test_list.append("{:s}-{:s}".format(dsp, test))
                test_rslt_list.append(result)
                err_dsc_list.append(nic_cli_id_str)
                err_code_list.append(result)
            ret = flx_web_srv_post_uut_report(stage, sn_type, sn, "PASS", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list)
            if not ret:
                cli_err(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
            else:
                cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))


def mfg_summary_disp(stage, summary_dict, mtp_fail_list):
    # for 2C, coalesce HV and LV results into one result
    sn_result_dict = dict()
    sn_done = list()
    for mtp_id in summary_dict.keys():
        for slot, sn, nic_type, rc in summary_dict[mtp_id]:
            # new sn
            if sn not in sn_result_dict.keys():
                sn_result_dict[sn] = rc
            # double entry sn
            else:
                sn_result_dict[sn] &= rc

    cli_inf("##########  MFG {:s} Test Summary  ##########".format(stage))
    for mtp_id in summary_dict.keys():
        cli_inf("---------- {:s} Report: ----------".format(mtp_id))
        for slot, sn, nic_type, rc in summary_dict[mtp_id]:
            nic_cli_id_str = id_final_str(mtp=mtp_id)
            # ignore file rc, use computed rc
            if sn in sn_done:
                continue
            rc = sn_result_dict[sn]
            sn_done.append(sn)
            if rc:
                cli_inf("{:s} {:s} {:s} PASS".format(nic_cli_id_str, sn, nic_type))
            else:
                cli_err("{:s} {:s} {:s} FAIL".format(nic_cli_id_str, sn, nic_type))
        cli_inf("--------- {:s} Report End --------\n".format(mtp_id))
    for mtp_id in mtp_fail_list:
        cli_err("-------- {:s} Test Aborted -------\n".format(mtp_id))

def open_logfiles(mtp_mgmt_ctrl, run_from_mtp=True, stage=FF_Stage.FF_P2C):
    if run_from_mtp:
        # Running python/pexpect on the MTP
        # Fixed directory name, always cleaned up before starting
        logfile_path = os.getcwd()
        MODIFIER = "a+"
    else:
        # Running python/pexpect outside MTP
        # Directory name contains timestamp and MTP id
        log_dir = "log/"
        log_timestamp = get_timestamp()
        mtp_id = mtp_mgmt_ctrl._id
        if stage == FF_Stage.FF_DL:
            log_sub_dir = MTP_DIAG_Logfile.MFG_DL_LOG_DIR.format(mtp_id, log_timestamp)
        elif stage == FF_Stage.FF_P2C:
            log_sub_dir = MTP_DIAG_Logfile.MFG_P2C_LOG_DIR.format(mtp_id, log_timestamp)
        elif stage == FF_Stage.FF_2C_HV or stage == FF_Stage.FF_2C_LV:
            log_sub_dir = MTP_DIAG_Logfile.MFG_2C_LOG_DIR.format(stage, mtp_id, log_timestamp)
        elif stage == FF_Stage.FF_4C_L or stage == FF_Stage.FF_4C_H:
            log_sub_dir = MTP_DIAG_Logfile.MFG_4C_LOG_DIR.format("4C", mtp_id, log_timestamp)
        elif stage == FF_Stage.FF_SWI:
            log_sub_dir = MTP_DIAG_Logfile.MFG_SWI_LOG_DIR.format(mtp_id, log_timestamp)
        elif stage == FF_Stage.FF_FST:
            log_sub_dir = MTP_DIAG_Logfile.MFG_FST_LOG_DIR.format(mtp_id, log_timestamp)
        else:
            print("Unknown stage!")
            return []
        os.system(MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir + log_sub_dir))

        logfile_path = log_dir + log_sub_dir
        MODIFIER = "w+"

    open_file_track_list = list()

    mtp_test_log_file = logfile_path + "/mtp_test.log"
    mtp_diag_log_file = logfile_path + "/mtp_diag.log"
    mtp_diag_cmd_log_file = logfile_path + "/mtp_diag_cmd.log"
    mtp_diagmgr_log_file = logfile_path + "/mtp_diagmgr.log"
    mtp_console_log_file = logfile_path + "/mtp_console.log"
    mtp_console_cmd_file = logfile_path + "/mtp_console_cmd.log"
    mtp_test_log_filep = open(mtp_test_log_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_test_log_filep)
    mtp_diag_log_filep = open(mtp_diag_log_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_diag_log_filep)
    mtp_diag_cmd_log_filep = open(mtp_diag_cmd_log_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_diag_cmd_log_filep)
    mtp_console_log_filep = open(mtp_console_log_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_console_log_filep)
    mtp_console_cmd_filep = open(mtp_console_cmd_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_console_cmd_filep)
    mtp_diagmgr_log_filep = open(mtp_diagmgr_log_file, MODIFIER, buffering=0)

    diag_nic_log_filep_list = list()
    for slot in range(mtp_mgmt_ctrl._slots):
        key = nic_key(slot)
        diag_nic_log_file = logfile_path + "/mtp_{:s}_diag.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, MODIFIER, buffering=0)
        open_file_track_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl._filep = mtp_test_log_filep
    mtp_mgmt_ctrl._diag_filep = mtp_diag_log_filep
    mtp_mgmt_ctrl._console_filep = mtp_console_log_filep
    mtp_mgmt_ctrl._console_cmd_filep = mtp_console_cmd_filep
    mtp_mgmt_ctrl._diag_cmd_filep = mtp_diag_cmd_log_filep
    mtp_mgmt_ctrl._diag_nic_filep_list = diag_nic_log_filep_list[:]

    return logfile_path, open_file_track_list

def aruba_gui_clear_buffer():
    while True:
        i,o,e = select.select([sys.stdin],[],[],2)
        if i:
            print("this is catch:", sys.stdin.readline())
        else:
            break

def aruba_gui_clear_buffer2():
    # Catch any previously entered User input especially from the GUI before
    # prompting the User to press any key to continue.
    while True:
        rlist, wlist, xlist = select.select([sys.stdin], [], [], 2)
        if rlist:
            print("Catching previously entered input:", sys.stdin.readline())
        else:
            break

