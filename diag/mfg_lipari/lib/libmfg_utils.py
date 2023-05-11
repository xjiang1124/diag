import getpass
import smtplib
import sys
import datetime
import re
import yaml as yaml
import os
import time
import pexpect
import glob
import select
if sys.version_info.major == 3: #python3
    import http.client as httplib
else:
    import httplib

from libdefs import MTP_Const
from libdefs import UUT_Type
from libdefs import FF_Stage
from libdefs import FPN_FF_Stage
from libdefs import MTP_DIAG_Path
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import MFG_DIAG_CMDS
from libdefs import NIC_IP_Address
from libmfg_cfg import *
from libsku_utils import *

def get_linux_prompt_list():
    DIAG_OS_PROMPT_LIST = ["$", "#", ">"]
    return DIAG_OS_PROMPT_LIST

def get_ssh_option():
    DIAG_SSH_OPTIONS = " -q -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"
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
    fp.flush()

    cli_inf(info)


def cli_log_err(fp, err):
    msg = "## [" + get_timestamp() + "] ERR: " + err
    fp.write(msg + "\n")
    fp.flush()

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
    # return 10.1.1.(100+slot)
    return "10.1.1.{:d}".format(100+slot+1)


# remove the special character mixed with output:
# eg: SMP Tue Ma^@r 19 11:14:41 PT 2019
def special_char_removal(buf):
    return re.sub(r"[\x00-\x09,\x0B-\x0C,\x0E-\x1F]", "", buf)


def part_number_match(pn, regex):
    return re.match(regex, pn) is not None

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

def mac_address_add_separator(addr, separator="-"):
    """
        input = 00aecd123456
        output = 00-ae-cd-12-34-56
    """
    return separator.join([addr[i:i+2] for i in range(0,len(addr),2)])

def mac_address_remove_separator(addr):
    """ 
        input = 00-ae-cd-12-34-56
        output = 00aecd123456
    """
    return "".join([addr[i] for i in range(0,len(addr)) if (i+1) % 3 != 0])

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

def mac_address_in_range(mac_addr, range_start, range_end):
    """
        return True if MAC address falls between start-end range
        return False if not, or either of 3 inputs is bad MAC
    """
    addr_list = [mac_addr, range_start, range_end]
    for idx in [0,1,2]:
        addr = addr_list[idx]
        if not isinstance(addr, int):
            if isinstance(addr, str):

                # LENGTH CHECK
                if len(addr) < 12:
                    cli_err("Missing characters in MAC address {:s}".format(addr))
                    return False
                elif len(addr) == 17:
                    addr = str(mac_address_remove_separator(addr))
                elif len(addr) >= 12:
                    cli_err("Extra characters in MAC address {:s}".format(addr))
                    return False

                addr = int(addr, 16)
            else:
                cli_err("Badly formed MAC address {}".format(addr))
                return False
        addr_list[idx] = addr #updated

    mac_addr = addr_list[0]
    range_start = addr_list[1]
    range_end = addr_list[2]

    if range_start <= mac_addr <= range_end:
        return True
    else:
        return False

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
        tmp = input("Confirm " + msg + "? (Y/N) [Y]:")
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
        tmp = input("Operator Confirm " + msg + ":")


def sw_pn_scan():
    tmp = input("Scan the Software PN: ")
    return tmp;


def single_select_menu(title, opt_list):
    menu = "+-" + "-"*len(title) + "-+\n"
    menu += "| " + title + " |\n"
    menu += "+-" + "-"*len(title) + "-+\n"
    menu += "Options:\n"
    for idx in range(len(opt_list)):
        menu += "    * " + opt_list[idx] + "\n"
    menu += "Scan the UUT ID Bar Code: "

    # validate input loop
    while True:
        scan_input = input(menu).replace(' ', '')
        if scan_input == "STOP":
            return None
        elif scan_input in opt_list:
            break
        else:
            cli_err("Invalid UUT ID: {:s}".format(scan_input))
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
        menu += "Scan the UUT ID Bar Code: [{:s} Selected]".format(", ".join(sub_list))

        # validate input loop
        scan_input = input(menu).replace(' ','')
        if scan_input == "STOP":
            return sub_list
        elif scan_input in menu_list:
            sub_list.append(scan_input)
            menu_list.remove(scan_input)
        else:
            cli_err("Invalid UUT ID: {:s}".format(scan_input))


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

def expect_spawn(cmd, logfile, timeout=MTP_Const.MTP_NETCOPY_DELAY):
    return pexpect.spawn(cmd, logfile=logfile, timeout=timeout, encoding='ascii', codec_errors='ignore')

def expect_clear_buffer(handle):
    buff = None
    try:
        buff = handle.read_nonblocking(16384, timeout = 1)
    except pexpect.exceptions.TIMEOUT as toe:
        pass
    except pexpect.exceptions.EOF:
        pass

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

def host_shell_cmd(test_ctrl, cmd, timeout=None, logfile=None):
    # host session doesnt have defined prompt, just wait for EOF. Thats why each command needs new session
    if timeout is None:
        timeout = MTP_Const.OS_CMD_DELAY
    if logfile is None:
        logfile = test_ctrl._diag_filep

    logfile.write("\n[{:s}] HOST: # {:s}\n".format(get_timestamp(), cmd)) # log the command otherwise pexpect eats it up
    session = expect_spawn(cmd, logfile=logfile, timeout=timeout)
    session.setecho(False)
    idx = mfg_expect_new(session, [pexpect.EOF], timeout=timeout)
    cmd_buf = session.before
    session.close()
    if idx < 0:
        return None
    else:
        return cmd_buf

