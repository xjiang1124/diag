import getpass
import smtplib
import httplib
import sys
import datetime
import re
import os
import time
import pexpect
import glob
import threading
import subprocess

# mfg servers
try:
    import oyaml as yaml
# lab servers
except ImportError:
    import yaml

from libdefs import MTP_Const
from libdefs import FF_Stage
from libdefs import FPN_FF_Stage
from libdefs import MTP_DIAG_Path
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import Factory
from libdefs import MFG_DIAG_CMDS
from libdefs import Swm_Test_Mode
from libdefs import NIC_Status
from libdefs import FLEX_TWO_WAY_COMM
from libmfg_cfg import *
from libsku_utils import *

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


def get_fru_date():
    # return format mmddyy
    return datetime.datetime.now().strftime("%m%d%y")


def get_nic_ip_addr(slot):
    # return 10.1.1.(100+slot)
    return "10.1.1.{:d}".format(100+slot+1)


# remove the special character mixed with output:
# eg: SMP Tue Ma^@r 19 11:14:41 PT 2019
def special_char_removal(buf):
    return re.sub(r"[\x00-\x09\x0B-\x0C\x0E-\x1F]", "", buf)

def extract_sn_from_dell_ppid(tmp):
    """ 
    The Board Serial Number is formed by concatenating the following PPID fields: 
    Country of Origin, MFG ID, Date Code and Serial Number. 
    For information on the fields in the PPID label, reference DP/N ENG0014180.
    
        US-01234D-54321-25A-0123-A00
        A -   B  -  C  - D - E  - F
        SN = A+C+D+E
    """
    sn = tmp[0:2] + tmp[8:13] + tmp[13:16] + tmp[16:20]
    return serial_number_validate(sn)

def extract_pn_from_dell_ppid(tmp):
    """ 
    Derived from PPDI field P/N + Rev
    
        US-01234D-54321-25A-0123-A00
        A -   B  -  C  - D - E  - F
        PN = B+F
    """
    pn = tmp[2:8] + tmp[20:23]
    return part_number_validate(pn)

def dell_ppid_validate(tmp):
    # No Dashes in Barcode read
    tmp = tmp.replace("-","")
    if re.match(DELL_PPID_FMT, tmp) and len(tmp) <= 23 and len(tmp) >= 22:
        return tmp
    else:
        return None

def serial_number_validate(buf, exact_match=True):
    """
        This is a "LOOSE" validation compared to libnic_ctrl::nic_fru_validate_sn().
        Check that the 'buf' containing serial number matches *ANY* of the rules.
        If exact_match=True, 'buf' must contain whole serial number and nothing else.
    """
    all_sn_regexes = [p[s] for p in SN_FORMAT_TABLE.values() for s in p] # flatten dict

    for sn_regex in all_sn_regexes:
        if exact_match:
            match = re.match(sn_regex, buf)
            if match:
                if match.group(0) == buf:
                    # check no truncation happened during regex match
                    return buf
                else:
                    return None
        else:
            disp_field = "Serial Number"
            sn_disp_regex = r"%s +(%s)" % (disp_field, sn_regex)
            match = re.findall(sn_disp_regex, buf)
            if match:
                return match[0]

    return None

def mac_address_validate(tmp):
    if re.match(PEN_MAC_NO_DASHES_FMT, tmp) and (len(tmp) == 12):
        return tmp
    else:
        return None


def part_number_validate(tmp):
    match, _ = part_number_lookup(tmp)
    if match is None:
        return None

    if match == tmp:
        # check no truncation happened during regex match
        return tmp
    else:
        return None

def part_number_lookup(pn):
    all_pn_regexes = [x for y in PN_FORMAT_TABLE.values() for x in y] # flatten list

    for pn_regex in all_pn_regexes:
        match = re.match(pn_regex, pn)
        if match:
            return match.group(0), pn_regex

    return None, None

def part_number_match(pn, regex):
    return re.match(regex, pn) is not None

def get_nic_type_by_part_number(pn):
    for nic_type, pn_regex_arr in PN_FORMAT_TABLE.items():
        for pn_regex in pn_regex_arr:
            if re.match(pn_regex, pn):
                return nic_type

    return None

def mac_address_format(tmp):
    return "-".join(re.findall("..", tmp))

def flatten_list_of_lists(list_of_lists):
    from itertools import chain
    return list(chain(*list_of_lists))

def list_subtract(a, b):
    """ set(A) - set(B) but keep the ordering """
    return list(x for x in a if x not in b)

def list_intersection(a, b):
    """ set(A).intersection(set(B)) but keep the ordering """
    return list(x for x in a if x in b)

def list_union(a, b):
    """ set(A).union(set(B)) but keep the ordering """
    return list_intersection(a,b) + list_subtract(a,b) + list_subtract(b,a)

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

def network_md5_compare(ip_addr, userid, passwd, local_file, remote_file):
    """
    calculate local file and remote file md5sum, compare each other.
    parameter local_file can be absolute or relative path;
    parameter remote_file must pass in with absolute path;
    return True if match
    return False if mismatch
    """

    # calculate the local file md5sum value
    cmd = ["md5sum", local_file]
    try:
        cmdoutput = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as Err:
        cli_err("Execute command {:s} failed".format(" ".join(cmd)))
        cli_err("Get output: {:s}".format(Err.output))
        cli_err("Get returncode: {:s}".format(str(Err.returncode)))
        return False
    local_md5sum = cmdoutput.split()[0]

    # calculate remote file ms5sum
    cmd = get_ssh_connect_cmd(userid, ip_addr)
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
    if not match:
        cli_err("Execute command {:s} on {:s} failed".format(cmd, ip_addr))
        return False
    remote_md5sum = match.group(1)

    # md5sum compare
    if remote_md5sum == local_md5sum:
        return True
    else:
        cli_err("File md5sum mismatch")
        return False

def need_mtp_file_update(mtp_ip_addr, mtp_usrid, mtp_passwd, local_filename=None, filename_on_mtp=None):
    """
    check if the file on MTP need copy/update by compare file md5sum with local source file
    return True if copy needed, namely md5sum mismath
    return False if copy not needed, namly md5sum match
    """

    if local_filename is None or filename_on_mtp is None:
        return True

    if not network_md5_compare(mtp_ip_addr, mtp_usrid, mtp_passwd, local_filename, filename_on_mtp):
        return True
    return False

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
    cmd = get_ssh_connect_cmd(userid, ip_addr)
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
    cmd = get_ssh_connect_cmd(userid, ip_addr)
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


def mtp_init_test_script(mtp_mgmt_ctrl, mtp_script_dir, mtp_script_pkg, logfile_dir=None, extra_script=None):
    shared_script_dir = os.path.dirname(mtp_script_dir)
    mtp_script_dir = os.path.dirname(mtp_script_dir) + ".{:s}/".format(mtp_mgmt_ctrl._id)
    # remove previous copy to this MTP
    cmd = "rm -rf {:s}".format(mtp_script_dir)
    os.system(cmd)
    # make new staging folder for copy
    cmd = "cp -r {:s} {:s}".format(shared_script_dir, mtp_script_dir)
    os.system(cmd)
    os.system("sync")
    if extra_script:
        cmd = "cp {:s} {:s}".format(extra_script, mtp_script_dir)
        os.system(cmd)
    cmd = "cp -r lib/ config/ {:s}".format(mtp_script_dir)
    os.system(cmd)
    if logfile_dir:
        cmd = "cp {:s}/*.log {:s}".format(logfile_dir, mtp_script_dir)
        os.system(cmd)
        if FF_Stage.FF_DL in logfile_dir or FF_Stage.FF_SWI in logfile_dir:
            cmd = "cp {:s}/{:s} {:s}".format(logfile_dir, MTP_DIAG_Logfile.SCAN_BARCODE_FILE, mtp_script_dir)
            os.system(cmd)
    cmd = "tar czf {:s} {:s}".format(mtp_script_pkg, mtp_script_dir)
    os.system(cmd)
    # remove the lib config for the next run
    if extra_script:
        cmd = "rm -f {:s}/{:s}".format(mtp_script_dir, os.path.basename(extra_script))
        os.system(cmd)
    os.system("sync")

    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
    # download the test script pkg
    if not network_copy_file(ipaddr, userid, passwd, mtp_script_pkg, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH):
        mtp_mgmt_ctrl.cli_log_err("Copy Test script failed... Abort")
        return False
    # remove the stale test script
    cmd = "rm -rf {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"/"+shared_script_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False
    # unpack the test script pkg
    cmd = "tar zxf {:s} -C {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"/"+mtp_script_pkg, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False
    # move test script folder to common folder
    cmd = "mv {:s} {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"/"+mtp_script_dir, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"/"+shared_script_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False
    # remove the test script pkg
    cmd = "rm -f {:s}".format(MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH+"/"+mtp_script_pkg)
    os.system(cmd)
    # remove the MTP-specific test script folder
    cmd = "rm -rf {:s}".format(mtp_script_dir)
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


def mtpid_list_poweroff(mtp_mgmt_ctrl_list, safely=True):
    if safely:
        for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
            mtp_mgmt_ctrl.mtp_mgmt_poweroff()
            mtp_mgmt_ctrl.cli_log_inf("Power off OS, Wait {:d} seconds to power off APC".format(MTP_Const.MTP_OS_SHUTDOWN_DELAY), level=0)
        count_down(MTP_Const.MTP_OS_SHUTDOWN_DELAY)
    for mtp_mgmt_ctrl in mtp_mgmt_ctrl_list:
        mtp_mgmt_ctrl.mtp_apc_pwr_off()
        mtp_mgmt_ctrl.cli_log_inf("Power off APC, Wait {:d} seconds for APC shutdown".format(MTP_Const.MTP_POWER_CYCLE_DELAY), level=0)
    count_down(MTP_Const.MTP_POWER_CYCLE_DELAY)


def mtp_common_setup(mtp_mgmt_ctrl, mtp_capability, fan_spd=MTP_Const.MFG_EDVT_NORM_FAN_SPD, stage=None, skip_nic_pn_init=False):
    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP chassis", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected\n", level=0)

    # diag environment pre init
    if not mtp_mgmt_ctrl.mtp_diag_pre_init():
        mtp_mgmt_ctrl.cli_log_err("Unable to pre-init diag environment", level=0)
        #mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False

    # diag environment post init
    if not mtp_mgmt_ctrl.mtp_diag_post_init(mtp_capability, stage):
        mtp_mgmt_ctrl.cli_log_err("Unable to post-init diag environment", level=0)
        #mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False

    # PSU/FAN absent, powerdown MTP
    if not mtp_mgmt_ctrl.mtp_hw_init(fan_spd, stage):
        mtp_mgmt_ctrl.cli_log_err("MTP HW Init Fail", level=0)
        #mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False

    # get the mtp system info
    if not mtp_mgmt_ctrl.mtp_sys_info_disp():
        mtp_mgmt_ctrl.cli_log_err("Unable to retrieve MTP system info", level=0)
        #mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False

    # init all the nic.
    if not mtp_mgmt_ctrl.mtp_nic_init(stage, skip_nic_pn_init=skip_nic_pn_init):
        mtp_mgmt_ctrl.cli_log_err("Initialize NIC type, present failed", level=0)
        #mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False
    return True


def mtp_common_setup2(mtp_mgmt_ctrl, mtp_capability, fan_spd=MTP_Const.MFG_EDVT_NORM_FAN_SPD, stage=None):
    mtp_mgmt_ctrl.cli_log_inf("Try to connect MTP chassis", level=0)
    if not mtp_mgmt_ctrl.mtp_mgmt_connect():
        mtp_mgmt_ctrl.cli_log_err("Unable to connect MTP chassis", level=0)
        return False
    mtp_mgmt_ctrl.cli_log_inf("MTP chassis connected\n", level=0)

    # diag environment pre init
    if not mtp_mgmt_ctrl.mtp_diag_pre_init():
        mtp_mgmt_ctrl.cli_log_err("Unable to pre-init diag environment", level=0)
        #mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False

    # diag environment post init
    if not mtp_mgmt_ctrl.mtp_diag_post_init(mtp_capability, stage):
        mtp_mgmt_ctrl.cli_log_err("Unable to post-init diag environment", level=0)
        #mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False

    # get the mtp system info
    if not mtp_mgmt_ctrl.mtp_sys_info_disp():
        mtp_mgmt_ctrl.cli_log_err("Unable to retrieve MTP system info", level=0)
        #mtp_mgmt_ctrl.mtp_chassis_shutdown()
        return False
    mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    # PSU/FAN absent, powerdown MTP
    if not mtp_mgmt_ctrl.mtp_hw_init(fan_spd, stage):
        mtp_mgmt_ctrl.cli_log_err("MTP HW Init Fail", level=0)
        #mtp_mgmt_ctrl.mtp_chassis_shutdown()
        #sys.exit()
        return False

    mtp_mgmt_ctrl.cli_log_inf("MTP Inlet temp = {:2.2f}".format(mtp_mgmt_ctrl.mtp_get_inlet_temp(None, None)))
    #sys.exit()
    # init all the nic.
    # if not mtp_mgmt_ctrl.mtp_nic_init():
    #     mtp_mgmt_ctrl.cli_log_err("Initialize NIC type, present failed", level=0)
    #     #mtp_mgmt_ctrl.mtp_chassis_shutdown()
    #     return False

    return True

def mtp_update_firmware(mtp_mgmt_ctrl, image_list, image_on_mtp):
    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    mtp_ip_addr = mtp_mgmt_cfg[0]
    mtp_usrid = mtp_mgmt_cfg[1]
    mtp_passwd = mtp_mgmt_cfg[2]
    image_dir = "/home/diag/"

    done_list = []
    image_list_unique = list(set(image_list))
    image_list_unique.sort()
    for image in image_list_unique:
        if image == "":
            continue
        image_rel_path = "release/{:s}".format(image)
        if not file_exist(image_rel_path):
            mtp_mgmt_ctrl.cli_log_err("Firmware image {:s} doesn't exist... Abort".format(image_rel_path), level=0)
            return False
        if image not in image_on_mtp and image not in done_list:
            mtp_mgmt_ctrl.cli_log_inf("Copy Firmware image {:s}".format(image), level=0)
            if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, image_rel_path, image_dir):
                mtp_mgmt_ctrl.cli_log_err("Copy Firmware image {:s} failed... Abort".format(image), level=0)
                return False
            mtp_mgmt_ctrl.cli_log_inf("Copy Firmware image {:s} complete".format(image), level=0)
            done_list.append(image)
        elif image in image_on_mtp and image not in done_list:
            if need_mtp_file_update(mtp_ip_addr, mtp_usrid, mtp_passwd, image_rel_path, image_dir + os.path.basename(image_rel_path)):
                mtp_mgmt_ctrl.cli_log_inf("Copy and overwrite existing md5sum not match firmware image {:s}".format(image), level=0)
                if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, image_rel_path, image_dir):
                    mtp_mgmt_ctrl.cli_log_err("Overwrite Firmware image {:s} failed... Abort".format(image), level=0)
                    return False
                mtp_mgmt_ctrl.cli_log_inf("Overwrite Firmware image {:s} complete".format(image), level=0)
                done_list.append(image)
            else:
                mtp_mgmt_ctrl.cli_log_inf("Firmware image {:s} on MTP is up-to-date".format(image), level=0)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Firmware image {:s} on MTP is up-to-date".format(image), level=0)

    return True

def mtp_update_asic_image(mtp_mgmt_ctrl, mtp_image, nic_image, image_on_mtp, force_update=False):
    mtp_mgmt_ctrl.cli_log_inf("Looking for {:s}".format(mtp_image), level=0)
    mtp_mgmt_ctrl.cli_log_inf("Looking for {:s}".format(nic_image), level=0)

    if os.path.isabs(mtp_image):
        mtp_image_file = mtp_image
    else:
        mtp_image_file = "release/{:s}".format(mtp_image)

    if not file_exist(mtp_image_file):
        mtp_mgmt_ctrl.cli_log_err("ASIC image {:s} doesn't exist... Abort".format(mtp_image_file), level=0)
        return False

    if os.path.isabs(nic_image):
        nic_image_file = nic_image
    else:
        nic_image_file = "release/{:s}".format(nic_image)

    if not file_exist(nic_image_file):
        mtp_mgmt_ctrl.cli_log_err("ASIC image {:s} doesn't exist... Abort".format(nic_image_file), level=0)
        return False

    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    mtp_ip_addr = mtp_mgmt_cfg[0]
    mtp_usrid = mtp_mgmt_cfg[1]
    mtp_passwd = mtp_mgmt_cfg[2]
    remote_dir = "/home/diag/"

    if not force_update and mtp_image in image_on_mtp and nic_image in image_on_mtp:
        if not need_mtp_file_update(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir + os.path.basename(mtp_image)) and \
            not need_mtp_file_update(mtp_ip_addr, mtp_usrid, mtp_passwd, nic_image_file, remote_dir + os.path.basename(nic_image)):
            mtp_mgmt_ctrl.cli_log_inf("ASIC images on MTP is up-to-date", level=0)
            return True

    # cleanup the stale asic images
    cmd = "rm -f /home/diag/" + mtp_image
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    mtp_mgmt_ctrl.cli_log_inf("Copy ASIC image: {:s}".format(mtp_image_file), level=0)
    if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir):
        mtp_mgmt_ctrl.cli_log_err("Copy MTP ASIC image failed... Abort", level=0)
        return False

    mtp_mgmt_ctrl.cli_log_inf("Copy ASIC image: {:s}".format(nic_image_file), level=0)
    if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, nic_image_file, remote_dir):
        mtp_mgmt_ctrl.cli_log_err("Copy NIC ASIC image failed... Abort", level=0)
        return False
    return True

def mtp_update_diag_image(mtp_mgmt_ctrl, mtp_image, nic_image, image_on_mtp, force_update=False):
    mtp_mgmt_ctrl.cli_log_inf("Looking for {:s}".format(mtp_image), level=0)
    mtp_mgmt_ctrl.cli_log_inf("Looking for {:s}".format(nic_image), level=0)

    if "amd64" not in mtp_image:
        mtp_mgmt_ctrl.cli_log_err("Wrong MTP image: {:s}".format(mtp_image), level=0)
        return False
    if "arm64" not in nic_image:
        mtp_mgmt_ctrl.cli_log_err("Wrong NIC image: {:s}".format(nic_image), level=0)
        return False

    if os.path.isabs(mtp_image):
        mtp_image_file = mtp_image
    else:
        mtp_image_file = "release/{:s}".format(mtp_image)
    if not file_exist(mtp_image_file):
        mtp_mgmt_ctrl.cli_log_err("MTP Diag image {:s} doesn't exist... Abort".format(mtp_image_file), level=0)
        return False

    if os.path.isabs(nic_image):
        nic_image_file = nic_image
    else:
        nic_image_file = "release/{:s}".format(nic_image)
    if not file_exist(nic_image_file):
        mtp_mgmt_ctrl.cli_log_err("NIC Diag image {:s} doesn't exist... Abort".format(nic_image_file), level=0)
        return False

    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    mtp_ip_addr = mtp_mgmt_cfg[0]
    mtp_usrid = mtp_mgmt_cfg[1]
    mtp_passwd = mtp_mgmt_cfg[2]
    remote_dir = "/home/diag/"

    if not force_update and mtp_image in image_on_mtp and nic_image in image_on_mtp:
        if not need_mtp_file_update(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir + os.path.basename(mtp_image)) and \
            not need_mtp_file_update(mtp_ip_addr, mtp_usrid, mtp_passwd, nic_image_file, remote_dir + os.path.basename(nic_image)):
            mtp_mgmt_ctrl.cli_log_inf("Diag images on MTP is up-to-date", level=0)
            return True

    # cleanup the stale diag images
    cmd = "rm -f /home/diag/image_a*.tar"
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

    # copy activity
    mtp_mgmt_ctrl.cli_log_inf("Copy MTP Chassis image: {:s}".format(mtp_image_file), level=0)
    if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir):
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

    if "penctl.linux" not in mtp_image:
        mtp_mgmt_ctrl.cli_log_err("Wrong FST Penctl image: {:s}".format(mtp_image), level=0)
        return False
    if "penctl.token" not in nic_image:
        mtp_mgmt_ctrl.cli_log_err("Wrong FST Penctl TOKEN image: {:s}".format(nic_image), level=0)
        return False

    if os.path.isabs(mtp_image):
        mtp_image_file = mtp_image
    else:
        mtp_image_file = "release/{:s}".format(mtp_image)
    if not file_exist(mtp_image_file):
        mtp_mgmt_ctrl.cli_log_err("MTP Penctl image {:s} doesn't exist... Abort".format(mtp_image_file), level=0)
        return False

    if os.path.isabs(nic_image):
        nic_image_file = nic_image
    else:
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

    if mtp_image in image_on_mtp and nic_image in image_on_mtp:
        if not need_mtp_file_update(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir + os.path.basename(mtp_image)) and \
            not need_mtp_file_update(mtp_ip_addr, mtp_usrid, mtp_passwd, nic_image_file, remote_dir + os.path.basename(nic_image)):
            mtp_mgmt_ctrl.cli_log_inf("Diag images on MTP is up-to-date", level=0)
            return True

    # cleanup the stale diag images
    cmd = "rm -f /home/diag/image_a*.tar"
    mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd)

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

def fail_all_slots(mtp_mgmt_ctrl):
    """
     Call this function when failing a script BEFORE any dsp test results have come.
     e.g. whole MTP fails: report as all cards failed
     e.g. connection problem: report as all cards failed
    """
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
    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Init new connection for failed NIC")
    ret = mtp_mgmt_ctrl.mtp_nic_para_session_init(slot_list=[slot], fpo=False)
    if not ret:
        mtp_mgmt_ctrl.cli_log_err("Init NIC Connection Failed", level = 0)
    mtp_mgmt_ctrl._nic_ctrl_list[slot].mtp_exec_cmd("######## {:s} ########".format("START post fail debug"))
    powered_on = mtp_mgmt_ctrl.mtp_mgmt_check_nic_pwr_status(slot)
    if not powered_on:
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "NIC not powered on")
        mtp_mgmt_ctrl.mtp_mgmt_set_nic_avs_post(slot)
    else:
        
        mtp_mgmt_ctrl.mtp_nic_console_lock()
        mtp_mgmt_ctrl.mtp_nic_boot_info_init(slot)
        mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_check_rebooted()
        mtp_mgmt_ctrl.mtp_nic_port_counters(slot) # if mtp_mgmt_ctrl._nic_ctrl_list[slot]._nic_status == NIC_Status.NIC_STA_MGMT_FAIL
        mtp_mgmt_ctrl.mtp_nic_console_unlock()

        mtp_mgmt_ctrl.mtp_mgmt_set_nic_avs_post(slot)

        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) in ELBA_NIC_TYPE_LIST:
            mtp_mgmt_ctrl.mtp_single_j2c_lock()
            mtp_mgmt_ctrl.mtp_nic_disp_ecc(slot) # needed separately in case j2c is unavailable
            mtp_mgmt_ctrl.mtp_nic_read_temp(slot)
            if mtp_mgmt_ctrl.mtp_nic_failed_boot(slot):
                mtp_mgmt_ctrl.mtp_nic_l1_health_check(slot) # for a CONSOLE_BOOT failure ONLY: do a mini L1
            mtp_mgmt_ctrl.mtp_single_j2c_unlock()
    

    # in case nic hung up the bus:
    mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
    mtp_mgmt_ctrl.mtp_reset_hub(slot)
    mtp_mgmt_ctrl._nic_ctrl_list[slot].mtp_exec_cmd("######## {:s} ########".format("END post fail debug"))
    mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_clear_fa()

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

def flx_soap_save_uut_result_xml(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, factory, mac=None, pn=None):
    test_xml = ""
    if mac:
        test_xml += FLX_SAVE_UUT_MAC_RSLT_FMT.format(mac)
    if pn:
        test_xml += FLX_SAVE_UUT_PN_RSLT_FMT.format(pn)
    for test, test_rslt, err_dsc, err_code in zip(test_list, test_rslt_list, err_dsc_list, err_code_list):
        # (test, status, value, description, failure code)
        value = ""
        test_xml += FLX_SAVE_UUT_TEST_RSLT_FMT.format(test, test_rslt, value, err_dsc, err_code)

    extra_info_xml = ""
    if mtp_psu_sn_list or nic_loopback_sn_list:
        for psu, psu_sn in zip(mtp_psu_sn_list.keys(), mtp_psu_sn_list.values()):
            extra_info_xml += "PSU_{:s}=\"{:s}\" ".format(psu, psu_sn)

        for lpbk, lpbk_sn in zip(nic_loopback_sn_list.keys(), nic_loopback_sn_list.values()):
            extra_info_xml += "LOOPBACK_PORT{:s}=\"{:s}\" ".format(lpbk, lpbk_sn)

        extra_info_xml = FLX_SAVE_UUT_RSLT_ENTRY_EXTRA_FMT.format(extra_info_xml)

    #(stage, SN, start_ts, duration, stop_ts, result)

    # factory = flx_sn_to_factory(sn)
    # if not factory:
    #     print("Unable to locate flex factory based on sn: {:s}".format(sn))
    #     return None

    if factory == Factory.FSP or factory == Factory.P1:
        ff_pn = flx_stage_to_penang(stage)
        return FLX_PENANG_SAVE_UUT_RSLT_XML_HEAD + \
               FLX_PENANG_SAVE_UUT_RSLT_ENTRY_FMT.format(ff_pn,sn,str(start_ts),str(duration),str(stop_ts),rslt,nic_type,duration,rslt) + \
               extra_info_xml + \
               FLX_SAVE_UUT_RSLT_ENTRY_2_FMT + \
               test_xml + \
               FLX_SAVE_UUT_RSLT_ENTRY_END + \
               FLX_SAVE_UUT_RSLT_XML_TAIL
    elif factory == Factory.MILPITAS:
        return FLX_SAVE_UUT_RSLT_XML_HEAD + \
               FLX_SAVE_UUT_RSLT_ENTRY_FMT.format(stage,sn,str(start_ts),str(duration),str(stop_ts),rslt,nic_type,duration,rslt) + \
               extra_info_xml + \
               FLX_SAVE_UUT_RSLT_ENTRY_2_FMT + \
               test_xml + \
               FLX_SAVE_UUT_RSLT_ENTRY_END + \
               FLX_SAVE_UUT_RSLT_XML_TAIL


def flx_soap_get_uut_info_xml(stage, sn, factory):
    # factory = flx_sn_to_factory(sn)
    # if not factory:
    #     print("Unable to locate flex factory based on sn: {:s}".format(sn))
    #     return None

    if factory == Factory.FSP or factory == Factory.P1:
        ff_pn = flx_stage_to_penang(stage)
        return FLX_PENANG_GET_UUT_INFO_XML_HEAD + \
               FLX_PENANG_GET_UUT_INFO_ENTRY_FMT.format(sn, ff_pn) + \
               FLX_GET_UUT_INFO_XML_TAIL
    if factory == Factory.MILPITAS:
        return FLX_GET_UUT_INFO_XML_HEAD + \
               FLX_GET_UUT_INFO_ENTRY_FMT.format(sn, stage) + \
               FLX_GET_UUT_INFO_XML_TAIL


def flx_sn_to_factory(sn):
    if not sn:
        return None

    for factory_location in SN_FORMAT_TABLE.keys():
        if factory_location == Factory.LAB:
            # skip, dont use lab SN to match
            continue

        for sn_regex in SN_FORMAT_TABLE[factory_location].values():
            if re.match(sn_regex, sn):
                return factory_location

    return None

def FindDellSN(sn):
    dell_cards = [
        PART_NUMBERS_MATCH.LACONA32DELL_PN_FMT,
        PART_NUMBERS_MATCH.POMONTEDELL_PN_FMT
        ]

    for factory_location in SN_FORMAT_TABLE.keys():
        for pn_regex in SN_FORMAT_TABLE[factory_location]:
            if pn_regex in dell_cards:
                sn_regex = SN_FORMAT_TABLE[factory_location][pn_regex]
                if re.match(sn_regex, sn):
                    return True
    return False

def flx_stage_to_penang(stage):
    if stage == FF_Stage.FF_DL:
        return FPN_FF_Stage.FF_DL
    elif stage == FF_Stage.FF_CFG:
        return FPN_FF_Stage.FF_CFG
    elif stage == FF_Stage.FF_P2C:
        return FPN_FF_Stage.FF_P2C
    elif stage == FF_Stage.FF_4C_H:
        return FPN_FF_Stage.FF_4C_H
    elif stage == FF_Stage.FF_4C_L:
        return FPN_FF_Stage.FF_4C_L
    elif stage == FF_Stage.FF_2C_H:
        return FPN_FF_Stage.FF_2C_H
    elif stage == FF_Stage.FF_2C_L:
        return FPN_FF_Stage.FF_2C_L
    elif stage == FF_Stage.FF_SWI:
        return FPN_FF_Stage.FF_SWI
    elif stage == FF_Stage.FF_FST:
        return FPN_FF_Stage.FF_FST
    else:
        print("Unknown Flex Flow Stage: {:s}".format(stage))
        return None

def soap_post_report(xml, factory=Factory.FSP):
    try:
        webserverip = Factory_network_config[factory]["Flexflow"]
        if factory == Factory.FSP or factory == Factory.P1:
            webservice = httplib.HTTP(webserverip)
            webservice.putrequest("POST", FLX_PENANG_API_URL)
            webservice.putheader("Content-Type", "text/xml")
            webservice.putheader("SOAPAction", FLX_PENANG_SAVE_UUT_RSLT_SOAP)
        else:
            webservice = httplib.HTTP(webserverip)
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
            print(resp)
            print("################## SAVE UUT RSLT #######################")
            return "500"
    except:
        print("Error occur when post report to webserver")
        return "999"

def soap_get_uut_info(xml, factory=Factory.FSP):
    try:
        webserverip = Factory_network_config[factory]["Flexflow"]
        if factory == Factory.FSP or factory == Factory.P1:
            webservice = httplib.HTTP(webserverip)
            webservice.putrequest("POST", FLX_PENANG_API_URL)
            webservice.putheader("Content-Type", "text/xml")
            webservice.putheader("SOAPAction", FLX_PENANG_GET_UUT_INFO_SOAP)
        else:
            webservice = httplib.HTTP(webserverip)
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
            print(resp)
            print("################## GET UUT INF #######################")
            return "500"
    except:
        print("Unable to connect to webserver")
        return "500"

def soap_get_uut_resp(xml, factory=Factory.FSP):
    try:
        webserverip = Factory_network_config[factory]["Flexflow"]
        if factory == Factory.FSP or factory == Factory.P1:
            webservice = httplib.HTTP(webserverip)
            webservice.putrequest("POST", FLX_PENANG_API_URL)
            webservice.putheader("Content-Type", "text/xml")
            webservice.putheader("SOAPAction", FLX_PENANG_GET_UUT_INFO_SOAP)
        else:
            webservice = httplib.HTTP(webserverip)
            webservice.putrequest("POST", FLX_API_URL)
            webservice.putheader("Content-Type", "text/xml")
            webservice.putheader("SOAPAction", FLX_GET_UUT_INFO_SOAP)

        webservice.putheader("Content-length", "%d" % len(xml))
        webservice.endheaders()

        webservice.send(xml)

        statuscode, statusmessage, header = webservice.getreply()
        resp = webservice.getfile().read()
        
        return resp
    except:
        print("Unable to connect to webserver")
        return "500"

def flx_web_srv_post_uut_report(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, factory, mac=None, pn=None):
    if factory is None or factory == Factory.UNKNOWN:
        factory = flx_sn_to_factory(sn)

    if not factory:
        print("Unable to locate flex factory based on sn: {:s}".format(sn))
        return False

    xml = flx_soap_get_uut_info_xml(stage, sn, factory)
    if not xml:
        return False

    ret = soap_get_uut_info(xml, factory)
    if int(ret) != 0:
        return False

    xml = flx_soap_save_uut_result_xml(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, factory, mac, pn)
    if not xml:
        return False

    retry = 0
    while retry < 3:
        ret = soap_post_report(xml, factory)
        if int(ret) != 0:
            print("{:d}th post uut report failed.".format((retry + 1)))
            retry += 1
            time.sleep(2)
        else:
            break
    if int(ret) != 0:
        return False

    return True

def flx_web_srv_precheck_uut_status(sn, factory, stage=None):
    if factory is None or factory == Factory.UNKNOWN:
        factory = flx_sn_to_factory(sn)

    if not factory:
        print("Unable to locate flex factory based on sn: {:s}".format(sn))
        return -3

    xml = flx_soap_get_uut_info_xml(stage, sn, factory)
    if not xml:
        return -2

    ret = soap_get_uut_info(xml, factory)
    return int(ret)

def flx_web_srv_post_uut_status(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, factory, mac=None, pn=None):
    if factory is None or factory == Factory.UNKNOWN:
        factory = flx_sn_to_factory(sn)

    if not factory:
        print("Unable to locate flex factory based on sn: {:s}".format(sn))
        return -3

    xml = flx_soap_save_uut_result_xml(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, factory, mac, pn)
    if not xml:
        return -2

    retry = 0
    while retry < 3:
        ret = soap_post_report(xml, factory)
        if int(ret) != 0:
            print("{:d}th post uut status failed.".format((retry + 1)))
            retry += 1
            time.sleep(2)
        else:
            break

    return int(ret)


def flx_web_srv_get_uut_info(sn, stage=None):
    factory = flx_sn_to_factory(sn)
    if not factory:
        print("Unable to locate flex factory based on sn: {:s}".format(sn))
        return False
    if not stage:
        stage = FF_Stage.FF_DL

    xml = flx_soap_get_uut_info_xml(stage, sn, factory)
    if not xml:
        return False

    resp = soap_get_uut_resp(xml, factory)
    #print(resp)
    return resp


def get_mtp_logfile(mtp_mgmt_ctrl, log_dir, mtp_id, mtp_test_summary, stage, vmarg=[]):
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
        test_log_file = "{:s}mtp_test.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
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
    elif stage == FF_Stage.FF_2C_H or stage == FF_Stage.FF_2C_L:
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
        local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
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
    elif stage == FF_Stage.FF_SRN:
        # log subdir
        sub_dir = MTP_DIAG_Logfile.MFG_SRN_LOG_DIR.format(mtp_id, log_timestamp)
        # log pkg filename
        log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_SRN_LOG_PKG_FILE.format(mtp_id, log_timestamp)
        # onboard log files
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_SRN_TEST_LOG_FILES
        # test summary logfile
        test_log_file = "{:s}mtp_test.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
    elif stage == FF_Stage.FF_ORT:
        # log subdir
        sub_dir = MTP_DIAG_Logfile.MFG_ORT_LOG_DIR.format(mtp_id, log_timestamp)
        # log pkg filename
        log_pkg_file = log_dir + MTP_DIAG_Logfile.MFG_ORT_LOG_PKG_FILE.format(mtp_id, log_timestamp)
        # onboard log files
        test_onboard_log_files = MTP_DIAG_Logfile.ONBOARD_TEST_LOG_FILES
        # test summary logfile
        test_log_file = "{:s}mtp_test.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_mtp_test.log".format(mtp_id)
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
    elif stage == FF_Stage.FF_P2C or stage == FF_Stage.FF_SRN or stage == FF_Stage.FF_ORT:
        if not vmarg:
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
        else:
            for vmag in vmarg:
                if vmag.lower() == "high":
                    diag_log_dir = log_dir + "hv_diag_logs/"
                    asic_log_dir = log_dir + "hv_asic_logs/"
                    nic_log_dir = log_dir + "hv_nic_logs/"
                elif vmag.lower() == "low":
                    diag_log_dir = log_dir + "lv_diag_logs/"
                    asic_log_dir = log_dir + "lv_asic_logs/"
                    nic_log_dir = log_dir + "lv_nic_logs/"
                else:
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

    elif stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L or stage == FF_Stage.FF_2C_H or stage == FF_Stage.FF_2C_L:
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
        if vmarg and "normal" in vmarg:
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

    if len(fail_match + pass_match) == 0:
        # no cards tested, save log to UNKNOWN folder
        fail_match = [(0, NIC_Type.UNKNOWN, NIC_Type.UNKNOWN)]

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
        elif stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_4C_LOG_DIR_FMT.format(nic_type, stage, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_4C_LOG_DIR_FMT.format(nic_type, stage, sn)
        elif stage == FF_Stage.FF_2C_H or stage == FF_Stage.FF_2C_L:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_2C_LOG_DIR_FMT.format(nic_type, stage, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_2C_LOG_DIR_FMT.format(nic_type, stage, sn)
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
        elif stage == FF_Stage.FF_SRN:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_SRN_LOG_DIR_FMT.format(nic_type, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_SRN_LOG_DIR_FMT.format(nic_type, sn)
        elif stage == FF_Stage.FF_ORT:
            if GLB_CFG_MFG_TEST_MODE:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_ORT_LOG_DIR_FMT.format(nic_type, sn)
            else:
                mfg_log_dir = MTP_DIAG_Logfile.DIAG_MFG_MODEL_ORT_LOG_DIR_FMT.format(nic_type, sn)
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
                if stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L or stage == FF_Stage.FF_2C_H or stage == FF_Stage.FF_2C_L:
                    # since 4C directory is organized as /mfg_log/type/4C/4C-H/...
                    os.system("chmod 777 {:s}".format(mfg_log_dir+"/../.."))
            else:
                # chdir from mfg_log/type/stage/sn --> mfg_log/MERGE/type/stage/sn
                mfg_log_dir = mfg_log_dir.replace(nic_type, "MERGE/"+nic_type)
                os.system(MFG_DIAG_CMDS.MFG_MK_DIR_777_FMT.format(mfg_log_dir))
                os.system("chmod 777 {:s}".format(mfg_log_dir+"/.."))
                if stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L or stage == FF_Stage.FF_2C_H or stage == FF_Stage.FF_2C_L:
                    os.system("chmod 777 {:s}".format(mfg_log_dir+"/../.."))

        # copy the onboard logs only once
        if log_hard_copy_flag:
            qa_log_pkg_file = mfg_log_dir + os.path.basename(log_pkg_file)
            if not network_get_file(ipaddr, userid, passwd, qa_log_pkg_file, log_pkg_file):
                mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file to {:}".format(qa_log_pkg_file), level=0)
                continue

            mtp_mgmt_ctrl.cli_log_inf("[{:s}] Collecting log file {:s}".format(sn, qa_log_pkg_file))

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

    retest_block_default = False

    if stage != FF_Stage.FF_SRN:
        for slot in skip_match:
            mtp_test_summary.append([slot, "SKIPPED", "SLOT", True, retest_block_default])

        for slot, nic_type, sn in fail_match:
            mtp_test_summary.append([slot, sn, nic_type, False, retest_block_default])

        for slot, nic_type, sn in pass_match:
            mtp_test_summary.append([slot, sn, nic_type, True, retest_block_default])

    else:
        ret = True
        first_rcd = True
        for slot, nic_type, sn in fail_match:
            if first_rcd:
                mtp_test_summary.append([slot, sn, nic_type, False, retest_block_default])
                first_rcd = False
                ret = False
        if ret:
            for slot, nic_type, sn in pass_match:
                if first_rcd:
                    mtp_test_summary.append([slot, sn, nic_type, True, retest_block_default])

    # clear the onboard logs
    logfile_list.append(log_pkg_file)
    logfile_list.append(log_dir+sub_dir)
    #cmd = "rm -rf {:s}".format(" ".join(logfile_list))
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

    mtp_mgmt_ctrl.cli_log_inf("Collecting {:s} log files complete".format(stage), level=0)

    return local_test_log_file


def mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts, mtp_stop_ts, test_log_file, stage, mtp_test_summary=[]):
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

    factory =  mtp_mgmt_ctrl.get_mtp_factory_location()
    cli_inf(mtp_cli_id_str + "Start posting test report")
    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL in buf:
        nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
        match = re.findall(nic_fail_reg_exp, buf)
        for slot, sn_type, sn in match:
            mtp_psu_sn_list = dict()
            nic_loopback_sn_list = dict()
            test_list = list()
            test_rslt_list = list()
            err_dsc_list = list()
            err_code_list = list()
            nic_cli_id_str = id_str(mtp=mtp_id, nic=int(slot), base=0)

            # FST will give syntax error since nic_ctrl is not initialized
            if stage != FF_Stage.FF_FST:
                # save infra serial numbers
                if len(mtp_mgmt_ctrl._psu_sn.keys()) > 0:
                    mtp_psu_sn_list = mtp_mgmt_ctrl._psu_sn

                # loopback SNs are read in P2C only for elba. P2C, 2C-L, 2C-H for capri
                if stage == FF_Stage.FF_P2C or (mtp_mgmt_ctrl._nic_ctrl_list[int(slot)-1]._asic_type == "capri" and stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H)):
                    if len(mtp_mgmt_ctrl._nic_ctrl_list[int(slot)-1]._loopback_sn.keys()) > 0:
                        nic_loopback_sn_list = mtp_mgmt_ctrl._nic_ctrl_list[int(slot)-1]._loopback_sn

            # find all test status
            nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
            sub_match = re.findall(nic_test_rslt_reg_exp, buf)
            for dsp, test, result in sub_match:
                test_list.append("{:s}-{:s}".format(dsp, test))
                test_rslt_list.append(result)
                err_dsc_list.append(nic_cli_id_str)
                err_code_list.append(result)
            # for failure case, there should be a test that failed.
            if len(sub_match) == 0 or "FAIL" not in test_rslt_list:
                test_list.append(MTP_DIAG_Report.NIC_UNKNOWN_FAILURE_CODE)
                test_rslt_list.append("FAIL")
                err_dsc_list.append(nic_cli_id_str)
                err_code_list.append("FAIL")

            mac=None 
            pn=None
            nic_mac_pc_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_MAC_PN_BY_FRU_RE.format(sn)
            matchsnformacpn = re.findall(nic_mac_pc_reg_exp, buf)
            if matchsnformacpn:
                mac=matchsnformacpn[-1][0]
                pn=matchsnformacpn[-1][1]

            if FindDellSN(sn):
                nic_pn_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_PN_BY_FRU_RE.format(sn)
                matchsn = re.findall(nic_pn_reg_exp, buf)
                if matchsn:
                    sn = sn[:2] + matchsn[-1][:6] + sn[2:] + matchsn[-1][6:]
                else:
                    nic_pn_reg_exp2 = MTP_DIAG_Report.NIC_DIAG_REGRESSION_PN_BY_FRU2_RE.format(sn)
                    matchsn2 = re.findall(nic_pn_reg_exp2, buf)
                    if matchsn2:
                        sn = sn[:2] + matchsn2[-1][:6] + sn[2:] + matchsn2[-1][6:]

            block_retest = False
            for test in test_list:
                block_retest |= is_retest_blocked(test, stage)


            if FLEX_SHOP_FLOOR_CONTROL:
                post_cnt = 0
                retry = FLEX_TWO_WAY_COMM.POST_RETRY
                time.sleep(1)
                while True:
                    rs = flx_web_srv_post_uut_status(stage, sn_type, sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, factory, mac, pn)
                    if rs == 0:
                        cli_inf(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver complete".format((post_cnt + 1), sn))
                        break
                    else:
                        if rs in FLEX_ERR_CODE_MAP.err_code:
                            cli_err(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver failed. [{:s}:{:s}]".format((post_cnt + 1), sn, str(rs), FLEX_ERR_CODE_MAP.err_code[rs]))
                        else:
                            cli_err(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver failed. [ERROR: Unknown error code -->({:s})]".format((post_cnt + 1), sn, str(rs)))
                        if rs != 9999:
                            post_cnt = retry
                        if post_cnt >= retry:
                            break
                    post_cnt += 1
                    time.sleep(3)

            else:
                ret = flx_web_srv_post_uut_report(stage, sn_type, sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, factory, mac, pn)
                if not ret:
                    cli_err(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
                else:
                    cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))
                    if block_retest:
                        cli_inf(mtp_cli_id_str + "[{:s}] {:s}".format(sn, MTP_DIAG_Report.NIC_RETEST_BLOCKED_MSG))


    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS in buf:
        nic_pass_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_PASS)
        match = re.findall(nic_pass_reg_exp, buf)
        for slot, sn_type, sn in match:
            mtp_psu_sn_list = dict()
            nic_loopback_sn_list = dict()
            test_list = list()
            test_rslt_list = list()
            err_dsc_list = list()
            err_code_list = list()
            nic_cli_id_str = id_str(mtp=mtp_id, nic=int(slot), base=0)

            # FST will give syntax error since nic_ctrl is not initialized
            if stage != FF_Stage.FF_FST:
                # save infra serial numbers
                if len(mtp_mgmt_ctrl._psu_sn.keys()) > 0:
                    mtp_psu_sn_list = mtp_mgmt_ctrl._psu_sn

                # loopback SNs are read in P2C only for elba. P2C, 2C-L, 2C-H for capri
                if stage == FF_Stage.FF_P2C or (mtp_mgmt_ctrl._nic_ctrl_list[int(slot)-1]._asic_type == "capri" and stage in (FF_Stage.FF_2C_L, FF_Stage.FF_2C_H)):
                    if len(mtp_mgmt_ctrl._nic_ctrl_list[int(slot)-1]._loopback_sn.keys()) > 0:
                        nic_loopback_sn_list = mtp_mgmt_ctrl._nic_ctrl_list[int(slot)-1]._loopback_sn

            # find all test status
            nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
            sub_match = re.findall(nic_test_rslt_reg_exp, buf)
            for dsp, test, result in sub_match:
                test_list.append("{:s}-{:s}".format(dsp, test))
                test_rslt_list.append(result)
                err_dsc_list.append(nic_cli_id_str)
                err_code_list.append(result)

            mac=None 
            pn=None
            nic_mac_pc_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_MAC_PN_BY_FRU_RE.format(sn)
            matchsnformacpn = re.findall(nic_mac_pc_reg_exp, buf)
            if matchsnformacpn:
                mac=matchsnformacpn[0][0]
                pn=matchsnformacpn[0][1]

            if FindDellSN(sn):
                nic_pn_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_PN_BY_FRU_RE.format(sn)
                matchsn = re.findall(nic_pn_reg_exp, buf)
                if matchsn:
                    sn = sn[:2] + matchsn[0][:6] + sn[2:] + matchsn[0][6:]
                else:
                    nic_pn_reg_exp2 = MTP_DIAG_Report.NIC_DIAG_REGRESSION_PN_BY_FRU2_RE.format(sn)
                    matchsn2 = re.findall(nic_pn_reg_exp2, buf)
                    if matchsn2:
                        sn = sn[:2] + matchsn2[0][:6] + sn[2:] + matchsn2[0][6:]
            if FLEX_SHOP_FLOOR_CONTROL:
                post_cnt = 0
                retry = FLEX_TWO_WAY_COMM.POST_RETRY
                time.sleep(1)
                while True:
                    rs = flx_web_srv_post_uut_status(stage, sn_type, sn, "PASS", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, factory, mac, pn)
                    if rs == 0:
                        cli_inf(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver complete".format((post_cnt + 1), sn))
                        break
                    else:
                        if rs in FLEX_ERR_CODE_MAP.err_code:
                            cli_err(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver failed. [{:s}:{:s}]".format((post_cnt + 1), sn, str(rs), FLEX_ERR_CODE_MAP.err_code[rs]))
                        else:
                            cli_err(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver failed. [ERROR: Unknown error code -->({:s})]".format((post_cnt + 1), sn, str(rs)))
                        if rs != 9999:
                            post_cnt = retry
                        if post_cnt >= retry:
                            break
                    post_cnt += 1
                    time.sleep(3)

                #change from display PASS --> FAIL (it fail when post result to flex flow)
                if rs != 0:
                    for idx in range(len(mtp_test_summary)):
                        # locate this SN's record
                        if mtp_test_summary[idx][1] == sn:
                            # force to set fail record
                            mtp_test_summary[idx][3] = False

            else:
                ret = flx_web_srv_post_uut_report(stage, sn_type, sn, "PASS", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, factory, mac, pn)
                if not ret:
                    cli_err(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
                else:
                    cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))


def mfg_summary_disp(stage, summary_dict, mtp_fail_list):
    final_result = True
    cli_inf("##########  MFG {:s} Test Summary  ##########".format(stage))
    for mtp_id in summary_dict.keys():
        cli_inf("---------- {:s} Report: ----------".format(mtp_id))
        for slot, sn, nic_type, rc, retest_blocked in summary_dict[mtp_id]:
            nic_cli_id_str = id_str(mtp=mtp_id, nic=int(slot), base=0)
            if rc:
                cli_inf("{:s} {:s} {:s} FINAL RESULT PASS".format(nic_cli_id_str, nic_type, sn))
            else:
                final_result = False
                if not retest_blocked:
                    cli_err("{:s} {:s} {:s} FINAL RESULT FAIL".format(nic_cli_id_str, nic_type, sn))
                else:
                    cli_err("{:s} {:s} {:s} FINAL RESULT FAIL {:s}".format(nic_cli_id_str, nic_type, sn, MTP_DIAG_Report.NIC_RETEST_BLOCKED_MSG))
        cli_inf("--------- {:s} Report End --------\n".format(mtp_id))
    for mtp_id in mtp_fail_list:
        cli_err("-------- {:s} Test Aborted -------\n".format(mtp_id))
        final_result = False
    return final_result

def mfg_mtp_summary_disp(stage, summary_dict, mtp_fail_list):
    """
     Same as mfg_summary_disp, but lists by MTP instead of NIC.
     Meant to be used for MTP-only scripts (like convert) or future projects.
    """
    cli_inf("##########  MFG {:s} Test Summary  ##########".format(stage))
    cli_inf("---------- Report: ----------")
    # summary_dict[MTP_ID] = [MTP_ID, SN, MTP_TYPE, PASS/FAIL]  ### MTP_ID stored twice because reusing same func as nic (mtp_id in place of slot)
    for mtp_id in summary_dict.keys():
        for slot, sn, nic_type, rc, retest in summary_dict[mtp_id]:
            if rc:
                cli_inf("{:s} {:s} {:s} PASS".format(slot, sn, nic_type))
            else:
                cli_err("{:s} {:s} {:s} FAIL".format(slot, sn, nic_type))
    cli_inf("--------- Report End --------\n")
    for mtp_id in mtp_fail_list:
        cli_err("-------- {:s} Test Aborted -------\n".format(mtp_id))

def mfg_summary_srn_disp(stage, summary_dict, mtp_fail_list, mtp_sn):
    cli_inf("##########  MFG {:s} Test Summary  ##########".format(stage))
    result = True
    for mtp_id in summary_dict.keys():
        cli_inf("---------- {:s} Report: ----------".format(mtp_id))
        if len(mtp_fail_list) > 0:
            cli_err("[{:s}] {:s} FAIL".format(mtp_id, mtp_sn))
        else:
            #one fail all fail
            for slot, sn, nic_type, rc in summary_dict[mtp_id]:
                nic_cli_id_str = id_str(mtp=mtp_id, nic=int(slot), base=0)
                if not rc:
                    result = False
                    
        if result:
            cli_inf("[{:s}] {:s} PASS".format(mtp_id, mtp_sn))
        else:
            cli_err("[{:s}] {:s} FAIL".format(mtp_id, mtp_sn))
        cli_inf("--------- {:s} Report End --------\n".format(mtp_id))

def display_failures(loopback_fail_list, fail_nic_list, mtpid_list, mtp_mgmt_ctrl_list, length):
    """
    -------------------------------------------------
    | MTP-XXX                                       |
    |                                               |
    |     o       o       o       X   o       o     |
    |     o       o       o       X   o       X     |
    |                                               |
    |     1   2   3   4   5   6   7   8   9  10     |
    |                                               |
    |                                       MTP-XXX |
    -------------------------------------------------

    [MTP-XXX]: [NIC-07]: QSFP port 1
    [MTP-XXX]: [NIC-07]: QSFP port 2
    [MTP-XXX]: [NIC-10]: QSFP port 2

    'o' = loopback present
    'X' = loopback missing
    ' ' = empty/failed slot

    """
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        width = 49
        horizontal_border = "-{:s}-".format("-"*47)
        vertical_border = "| {:s} |".format(" "*45)
        mtp_name_top = "| {:<45s} |".format(mtp_id)
        mtp_name_bot = "| {:>45s} |".format(mtp_id)

        print(horizontal_border)
        print(mtp_name_top)
        print(vertical_border)

        # Port 1 row
        pre="|     "
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot] or slot in fail_nic_list[mtp_id]:
                pre += "    "
            elif loopback_fail_list[mtp_id][slot] > 0:
                pre += "X   "
            else:
                pre += "o   "
        pre += "  |"
        print(pre)

        # Port 2 row
        pre="|     "
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot] or slot in fail_nic_list[mtp_id]:
                pre += "    "
            elif loopback_fail_list[mtp_id][slot+length] > 0:
                pre += "X   "
            else:
                pre += "o   "
        pre += "  |"
        print(pre)

        print(vertical_border)

        pre="|    "
        for slot in range(len(nic_prsnt_list)):
            pre+= "{:>2s}  ".format(str(slot+1))
        pre += "   |"
        print(pre)

        print(vertical_border)
        print(mtp_name_bot)
        print(horizontal_border)



    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(len(nic_prsnt_list)):
            if nic_prsnt_list[slot] and loopback_fail_list[mtp_id][slot]:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "QSFP Module 1 is missing")
            if nic_prsnt_list[slot] and loopback_fail_list[mtp_id][slot+length]:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "QSFP Module 2 is missing")

    return

def display_rj45_failures(loopback_fail_list, fail_nic_list, mtpid_list, mtp_mgmt_ctrl_list):
    """
    -------------------------------------------------
    | MTP-XXX                                       |
    |                                               |
    |                     o       X                 |
    |     o       o       o       X   o       X     |
    |                                               |
    |     1   2   3   4   5   6   7   8   9  10     |
    |                                               |
    |                                       MTP-XXX |
    -------------------------------------------------

    [MTP-XXX]: [NIC-07]: RJ45 port 1
    [MTP-XXX]: [NIC-07]: RJ45 port 2
    [MTP-XXX]: [NIC-10]: RJ45 port 1

    'o' = loopback present
    'X' = loopback missing
    ' ' = empty/failed slot

    """
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

        width = 49
        horizontal_border = "-{:s}-".format("-"*47)
        vertical_border = "| {:s} |".format(" "*45)
        mtp_name_top = "| {:<45s} |".format(mtp_id)
        mtp_name_bot = "| {:>45s} |".format(mtp_id)

        print(horizontal_border)
        print(mtp_name_top)
        print(vertical_border)

        # Port 1 row
        pre="|     "
        for slot in range(len(nic_prsnt_list)):
            if not nic_prsnt_list[slot] or slot in fail_nic_list[mtp_id]:
                pre += "    "
            elif loopback_fail_list[mtp_id][slot] > 0:
                pre += "X   "
            else:
                pre += "o   "
        pre += "  |"
        print(pre)

        # Port 2 row, for naples100 only
        pre="|     "
        for slot in range(len(nic_prsnt_list)):
            if (
                not nic_prsnt_list[slot]
                or slot in fail_nic_list[mtp_id]
                or mtp_mgmt_ctrl.mtp_get_nic_type(slot) in ELBA_NIC_TYPE_LIST
                or mtp_mgmt_ctrl.mtp_get_nic_type(slot) not in TWO_OOB_MGMT_PORT_TYPE_LIST
                ):
                pre += "    "
            elif loopback_fail_list[mtp_id][slot] > 0 and mtp_mgmt_ctrl.mtp_get_nic_type(slot) in TWO_OOB_MGMT_PORT_TYPE_LIST:
                pre += "X   "
            elif mtp_mgmt_ctrl.mtp_get_nic_type(slot) in TWO_OOB_MGMT_PORT_TYPE_LIST:
                pre += "o   "
            else:
                pre += "    "
        pre += "  |"
        print(pre)

        print(vertical_border)

        # Slots row
        pre="|    "
        for slot in range(len(nic_prsnt_list)):
            pre+= "{:>2s}  ".format(str(slot+1))
        pre += "   |"
        print(pre)

        print(vertical_border)
        print(mtp_name_bot)
        print(horizontal_border)



    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(len(nic_prsnt_list)):
            if nic_prsnt_list[slot] and loopback_fail_list[mtp_id][slot]:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "RJ45 module is missing")

    return
    

def loopback_sanity_check(mtpid_list, mtp_mgmt_ctrl_list, fail_nic_list):
    max_retries_per_slot = 3

    loopback_fail_list = dict()
    cur_fail_list = dict()
    length = MTP_Const.MTP_SLOT_NUM
    for mtp_id in mtpid_list:
        loopback_fail_list[mtp_id] = [0, 0] * length
        cur_fail_list[mtp_id] = [0, 0] * length

    skip_check_list = dict() # dont test slots that have already failed before sanity
    for mtp_id in mtpid_list:
        skip_check_list[mtp_id] = fail_nic_list[mtp_id][:]

    start_ts = timestamp_snapshot()

    while True:
        failure_detected = False
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
            
            nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
            for slot in range(len(nic_prsnt_list)):
                if nic_prsnt_list[slot] and slot not in fail_nic_list[mtp_id]:
                    cur_fail_list[mtp_id][slot] = 0
                    cur_fail_list[mtp_id][slot+length] = 0
                    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                    if nic_type in ELBA_NIC_TYPE_LIST:
                        read_data = [0]
                        rc = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_read_cpld_via_smbus(reg_addr=0x40, read_data=read_data)
                        if not rc:
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read CPLD")
                            if slot not in fail_nic_list[mtp_id]:
                                fail_nic_list[mtp_id].append(slot)
                            continue

                        ### QSFP/SFP PORT 1
                        if read_data[0] & 0x01 == 0:
                            # not present, retry 3x
                            if loopback_fail_list[mtp_id][slot] == max_retries_per_slot:
                                if slot not in fail_nic_list[mtp_id]:
                                    fail_nic_list[mtp_id].append(slot)
                                continue
                            else:
                                cur_fail_list[mtp_id][slot] = 1
                                loopback_fail_list[mtp_id][slot] += 1
                                failure_detected = True
                        else:
                            # log the transceiver serial number. retry 3x if unable to read.
                            if not mtp_mgmt_ctrl.mtp_nic_read_transceiver_sn(slot, "1"):
                                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read loopback EEPROM")
                                if loopback_fail_list[mtp_id][slot] == max_retries_per_slot:
                                    if slot not in fail_nic_list[mtp_id]:
                                        fail_nic_list[mtp_id].append(slot)
                                    continue
                                else:
                                    cur_fail_list[mtp_id][slot] = 1
                                    loopback_fail_list[mtp_id][slot] += 1
                                    failure_detected = True

                        ### QSFP/SFP PORT 2
                        if read_data[0] & 0x02 == 0:
                            # not present, retry 3x
                            if loopback_fail_list[mtp_id][slot+length] == max_retries_per_slot:
                                if slot not in fail_nic_list[mtp_id]:
                                    fail_nic_list[mtp_id].append(slot)
                                continue
                            else:
                                cur_fail_list[mtp_id][slot+length] = 1
                                loopback_fail_list[mtp_id][slot+length] += 1
                                failure_detected = True
                        else:
                            # log the transceiver serial number. retry 3x if unable to read.
                            if not mtp_mgmt_ctrl.mtp_nic_read_transceiver_sn(slot, "2"):
                                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read loopback EEPROM")
                                if loopback_fail_list[mtp_id][slot+length] == max_retries_per_slot:
                                    if slot not in fail_nic_list[mtp_id]:
                                        fail_nic_list[mtp_id].append(slot)
                                    continue
                                else:
                                    cur_fail_list[mtp_id][slot+length] = 1
                                    loopback_fail_list[mtp_id][slot+length] += 1
                                    failure_detected = True

                    elif nic_type in CAPRI_NIC_TYPE_LIST:
                        # QSFP/SFP port 1
                        read_data = [0]
                        expected_val = 0x3
                        if nic_type in (NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL):
                            expected_val = 0x11
                        else:
                            expected_val = 0x3

                        rc = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_read_i2c(0, 0x50, 0, read_data)
                        if not rc:
                            mtp_mgmt_ctrl.mtp_get_nic_err_msg(slot)
                            mtp_mgmt_ctrl.mtp_dump_nic_err_msg(slot)
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read port 1 loopback over i2c")
                            if slot not in fail_nic_list[mtp_id]:
                                fail_nic_list[mtp_id].append(slot)
                            continue

                        if read_data[0] & expected_val != expected_val:
                            if loopback_fail_list[mtp_id][slot] == max_retries_per_slot:
                                if slot not in fail_nic_list[mtp_id]:
                                    fail_nic_list[mtp_id].append(slot)
                                continue
                            else:
                                cur_fail_list[mtp_id][slot] = 1
                                loopback_fail_list[mtp_id][slot] += 1
                                failure_detected = True
                        else:
                            # log the transceiver serial number. retry 3x if unable to read.
                            if not mtp_mgmt_ctrl.mtp_nic_read_transceiver_sn(slot, "0"):
                                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read loopback EEPROM")
                                if loopback_fail_list[mtp_id][slot] == max_retries_per_slot:
                                    if slot not in fail_nic_list[mtp_id]:
                                        fail_nic_list[mtp_id].append(slot)
                                    continue
                                else:
                                    cur_fail_list[mtp_id][slot] = 1
                                    loopback_fail_list[mtp_id][slot] += 1
                                    failure_detected = True

                        # QSFP/SFP port 2
                        read_data = [0]
                        rc = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_read_i2c(1, 0x50, 0, read_data)
                        if not rc:
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read port 2 loopback over i2c")
                            if slot not in fail_nic_list[mtp_id]:
                                fail_nic_list[mtp_id].append(slot)
                            continue

                        if read_data[0] & expected_val != expected_val:
                            if loopback_fail_list[mtp_id][slot+length] == max_retries_per_slot:
                                if slot not in fail_nic_list[mtp_id]:
                                    fail_nic_list[mtp_id].append(slot)
                                continue
                            else:
                                cur_fail_list[mtp_id][slot+length] = 1
                                loopback_fail_list[mtp_id][slot+length] += 1
                                failure_detected = True
                        else:
                            # log the transceiver serial number. retry 3x if unable to read.
                            if not mtp_mgmt_ctrl.mtp_nic_read_transceiver_sn(slot, "1"):
                                mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read loopback EEPROM")
                                if loopback_fail_list[mtp_id][slot+length] == max_retries_per_slot:
                                    if slot not in fail_nic_list[mtp_id]:
                                        fail_nic_list[mtp_id].append(slot)
                                    continue
                                else:
                                    cur_fail_list[mtp_id][slot+length] = 1
                                    loopback_fail_list[mtp_id][slot+length] += 1
                                    failure_detected = True

        display_failures(cur_fail_list, fail_nic_list, mtpid_list, mtp_mgmt_ctrl_list, length)

        if not failure_detected:
            break

        # while True:
        raw_input("Please re-insert the modules above then press any key to continue.\nWARNING: do not power off the MTP yet. ")

        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
            mtp_mgmt_ctrl.cli_log_inf("Re-running sanity check...", level=0)

    stop_ts = timestamp_snapshot()
    duration = str(stop_ts - start_ts)

    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        fail_rslt_list = list()
        for slot in fail_nic_list[mtp_id]:
            if slot in skip_check_list[mtp_id]:
                continue
            nic_cli_id_str = id_str(mtp=mtp_id, nic=slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            fail_rslt_list.append(nic_cli_id_str + "Sanity check failed {:d} attempts".format(max_retries_per_slot))
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, "SANITY_CHECK", "QSFP", "FAILED", duration))
        cli_log_rslt("{:s} Eth Sanity Check complete".format(mtp_id), [], fail_rslt_list, mtp_mgmt_ctrl._filep)

    return fail_nic_list

def rj45_sanity_check(mtpid_list, mtp_mgmt_ctrl_list, fail_nic_list):
    max_retries_per_slot = 3

    loopback_fail_list = dict()
    cur_fail_list = dict()
    length = MTP_Const.MTP_SLOT_NUM
    for mtp_id in mtpid_list:
        loopback_fail_list[mtp_id] = [0] * length
        cur_fail_list[mtp_id] = [0] * length

    skip_check_list = dict() # dont test slots that have already failed before sanity
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        skip_check_list[mtp_id] = fail_nic_list[mtp_id][:]
        # Skip RJ45 check for slots populated with NIC_Type.ORTANO2SOLO or NIC_Type.ORTANO2ADICR
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if nic_prsnt_list[slot] and slot not in fail_nic_list[mtp_id]:
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type in [NIC_Type.ORTANO2SOLO or NIC_Type.ORTANO2ADICR]:
                    mtp_mgmt_ctrl.cli_log_slot_inf(slot, "Skip RJ45 Sanity Check For This Slot")
                    skip_check_list[mtp_id].append(slot)

    start_ts = timestamp_snapshot()

    while True:
        failure_detected = False
        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
            
            nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()

            for slot in range(len(nic_prsnt_list)):
                if nic_prsnt_list[slot] and slot not in fail_nic_list[mtp_id]:
                    cur_fail_list[mtp_id][slot] = 0
                    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                    if nic_type in [NIC_Type.ORTANO2SOLO or NIC_Type.ORTANO2ADICR]:
                        continue
                    if nic_type in ELBA_NIC_TYPE_LIST and nic_type in FPGA_TYPE_LIST:
                        ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_phy_xcvr_link_test(slot)
                    elif nic_type in ELBA_NIC_TYPE_LIST:
                        ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_mvl_link_test(slot)

                    if nic_type in ELBA_NIC_TYPE_LIST:
                        if ret != "SUCCESS":
                            if loopback_fail_list[mtp_id][slot] == max_retries_per_slot:
                                if slot not in fail_nic_list[mtp_id]:
                                    fail_nic_list[mtp_id].append(slot)
                                continue
                            else:
                                cur_fail_list[mtp_id][slot] = 1
                                loopback_fail_list[mtp_id][slot] += 1
                                failure_detected = True

        display_rj45_failures(cur_fail_list, fail_nic_list, mtpid_list, mtp_mgmt_ctrl_list)

        if not failure_detected:
            break

        raw_input("Please re-insert the RJ45 modules above then press any key to continue.\nWARNING: do not power off the MTP yet. ")

        for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
            mtp_mgmt_ctrl.cli_log_inf("Re-running sanity check...", level=0)

    stop_ts = timestamp_snapshot()
    duration = str(stop_ts - start_ts)

    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        fail_rslt_list = list()
        for slot in fail_nic_list[mtp_id]:
            if slot in skip_check_list[mtp_id]:
                continue
            nic_cli_id_str = id_str(mtp=mtp_id, nic=slot)
            sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
            fail_rslt_list.append(nic_cli_id_str + "Sanity check failed {:d} attempts".format(max_retries_per_slot))
            mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, "SANITY_CHECK", "RJ45", "FAILED", duration))
        cli_log_rslt("{:s} RJ45 Sanity Check complete".format(mtp_id), [], fail_rslt_list, mtp_mgmt_ctrl._filep)

    return fail_nic_list

def mtp_setup(mtp_mgmt_ctrl, mtp_capability, setup_rslt_list):
    setup_rslt_list[mtp_mgmt_ctrl._id] = mtp_common_setup(mtp_mgmt_ctrl, mtp_capability)

def sanity_check(mtp_cfg_db, mtpid_list, mtp_mgmt_ctrl_list, mtpid_fail_list, fail_nic_list, skip_test):
    if "SANITY_CHECK" in skip_test:
        return fail_nic_list

    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        # find any slots to skip
        mtp_slots_to_skip = mtp_cfg_db.get_mtp_slots_to_skip(mtp_id)
        mtp_mgmt_ctrl._slots_to_skip = mtp_slots_to_skip

        # find the mtp capability
        mtp_capability = mtp_cfg_db.get_mtp_capability(mtp_id)

    cli_log_rslt("Begin Sanity Check .. Please monitor until complete", [], [], mtp_mgmt_ctrl._filep)


    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        nic_list = list()       # needs para_init
        mgmt_nic_list = list()  # needs para_mgmt_init
        nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
        for slot in range(MTP_Const.MTP_SLOT_NUM):
            if nic_prsnt_list[slot] and slot not in fail_nic_list[mtp_id]:
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type in ELBA_NIC_TYPE_LIST and nic_type in FPGA_TYPE_LIST:
                    mgmt_nic_list.append(slot)
                else:
                    nic_list.append(slot)

        # for all cards:
        if nic_list:
            if not mtp_mgmt_ctrl.mtp_nic_para_init(nic_list):
                for slot in nic_list:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        if slot not in fail_nic_list[mtp_id]:
                            fail_nic_list[mtp_id].append(slot)

        # for lacona/pomonte:
        if mgmt_nic_list:
            if not mtp_mgmt_ctrl.mtp_nic_mgmt_para_init(mgmt_nic_list, False):
                for slot in mgmt_nic_list:
                    if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                        if slot not in fail_nic_list[mtp_id]:
                            fail_nic_list[mtp_id].append(slot)

    if "QSFP" not in skip_test:
        loopback_sanity_check(mtpid_list, mtp_mgmt_ctrl_list, fail_nic_list)
    if "RJ45" not in skip_test:
        rj45_sanity_check(mtpid_list, mtp_mgmt_ctrl_list, fail_nic_list)

    # if all slots in an MTP fail, assert stop on failure here
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        if len(fail_nic_list[mtp_id]) == mtp_mgmt_ctrl._slots:
            mtp_mgmt_ctrl.mtp_diag_fail_report("MTP completely failed Sanity Check. Test abort..")
            mtpid_list.remove(mtp_id)
            mtp_mgmt_ctrl_list.remove(mtp_mgmt_ctrl)
            mtpid_fail_list.append(mtp_id)

    # close NIC ssh sessions
    for mtp_id, mtp_mgmt_ctrl in zip(mtpid_list, mtp_mgmt_ctrl_list):
        mtp_mgmt_ctrl.mtp_nic_para_session_end()

    return fail_nic_list

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
        elif stage == FF_Stage.FF_4C_L or stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_2C_L or stage == FF_Stage.FF_2C_H:
            log_sub_dir = MTP_DIAG_Logfile.MFG_4C_LOG_DIR.format("4C", mtp_id, log_timestamp)
        elif stage == FF_Stage.FF_SWI:
            log_sub_dir = MTP_DIAG_Logfile.MFG_SWI_LOG_DIR.format(mtp_id, log_timestamp)
        elif stage == FF_Stage.FF_FST:
            log_sub_dir = MTP_DIAG_Logfile.MFG_FST_LOG_DIR.format(mtp_id, log_timestamp)
        elif stage == FF_Stage.FF_SRN:
            log_sub_dir = MTP_DIAG_Logfile.MFG_SRN_LOG_DIR.format(mtp_id, log_timestamp)
        elif stage == FF_Stage.FF_ORT:
            log_sub_dir = MTP_DIAG_Logfile.MFG_ORT_LOG_DIR.format(mtp_id, log_timestamp)
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
    if run_from_mtp:
        mtp_diagmgr_log_file = logfile_path + "/mtp_diagmgr.log"
    else:
        mtp_diagmgr_log_file = "/tmp/mtp_diagmgr.log"
    mtp_test_log_filep = open(mtp_test_log_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_test_log_filep)
    mtp_diag_log_filep = open(mtp_diag_log_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_diag_log_filep)
    mtp_diag_cmd_log_filep = open(mtp_diag_cmd_log_file, MODIFIER, buffering=0)
    open_file_track_list.append(mtp_diag_cmd_log_filep)

    diag_nic_log_filep_list = list()
    for slot in range(mtp_mgmt_ctrl._slots):
        key = nic_key(slot)
        diag_nic_log_file = logfile_path + "/mtp_{:s}_diag.log".format(key)
        diag_nic_log_filep = open(diag_nic_log_file, MODIFIER, buffering=0)
        open_file_track_list.append(diag_nic_log_filep)
        diag_nic_log_filep_list.append(diag_nic_log_filep)

    mtp_mgmt_ctrl._filep = mtp_test_log_filep
    mtp_mgmt_ctrl._diag_filep = mtp_diag_log_filep
    mtp_mgmt_ctrl._diag_cmd_filep = mtp_diag_cmd_log_filep
    mtp_mgmt_ctrl._diag_nic_filep_list = diag_nic_log_filep_list[:]
    mtp_mgmt_ctrl._diagmgr_logfile = mtp_diagmgr_log_file

    return logfile_path, open_file_track_list

def mtp_power_log_start(mtp_mgmt_ctrl):
    mtp_mgmt_ctrl.cli_log_inf("Start logging MTP syslog\n", level=0)
    mtp_syslog_handle = mtp_mgmt_ctrl.mtp_session_create()
    mtp_syslog_handle.sendline("while [ 1 ]; do devmgr -status; sleep 60; done > /home/diag/mtp_regression/mtp_sts.log")

    return mtp_syslog_handle

def mtp_power_log_end(mtp_mgmt_ctrl, mtp_syslog_handle):
    mtp_mgmt_ctrl.cli_log_inf("End logging MTP syslog", level=0)
    mtp_syslog_handle.send('\x03')
    mtp_syslog_handle.close()

def single_mtp_barcode_scan(mtp_id, mtp_mgmt_ctrl, logfile_dir, swmtestmode=Swm_Test_Mode.SW_DETECT):
    mtp_mgmt_ctrl.cli_log_inf("Start the Barcode Scan Process", level=0)

    while True:
        scan_rslt = mtp_mgmt_ctrl.mtp_barcode_scan(False, swmtestmode)
        if scan_rslt:
            break;
        mtp_mgmt_ctrl.cli_log_inf("Restart the Barcode Scan Process", level=0)

    pass_rslt_list = list()
    fail_rslt_list = list()
    # print scan summary
    for slot in range(mtp_mgmt_ctrl._slots):
        key = nic_key(slot)
        nic_cli_id_str = id_str(mtp = mtp_id, nic = slot)
        if scan_rslt[key]["VALID"]:
            sn = scan_rslt[key]["SN"]
            pn = scan_rslt[key]["PN"]
            mac_ui = mac_address_format(scan_rslt[key]["MAC"])
            if pn == '000000-000' or swmtestmode == Swm_Test_Mode.ALOM:
                alom_sn = scan_rslt[key]["SN_ALOM"]
                alom_pn = scan_rslt[key]["PN_ALOM"]
                if swmtestmode == Swm_Test_Mode.ALOM:
                    pass_rslt_list.append(nic_cli_id_str + "SN_ALOM = " + alom_sn + " PN_ALOM = " + alom_pn)
                else:
                    pass_rslt_list.append(nic_cli_id_str + "SN = " + sn + "; MAC = " + mac_ui + "; PN = " + pn + "; SN_ALOM = " + alom_sn + "; PN_ALOM = " + alom_pn)
            else:
                pass_rslt_list.append(nic_cli_id_str + "SN = " + sn + "; MAC = " + mac_ui + "; PN = " + pn)
        else:
            fail_rslt_list.append(nic_cli_id_str + "NIC Absent")
    cli_log_rslt("Barcode Scan Summary", pass_rslt_list, fail_rslt_list, mtp_mgmt_ctrl._filep)

    scan_cfg_file = logfile_dir + MTP_DIAG_Logfile.SCAN_BARCODE_FILE
    scan_cfg_filep = open(scan_cfg_file, "w+")
    mtp_mgmt_ctrl.gen_barcode_config_file(scan_cfg_filep, scan_rslt)
    scan_cfg_filep.close()

def is_retest_blocked(test, stage):
    test = test.split("-")
    test = test[len(test)-1]
    if test in [
                "NIC_POWER",
                "SNAKE_ELBA",
                "L1",
                "EMMC",
                "DDR_STRESS",
                "I2C",
                "RTC",
                "EDMA"
                ]:
        return True
    elif test in ["ETH_PRBS"] and stage in (FF_Stage.FF_4C_L, FF_Stage.FF_4C_H, FF_Stage.FF_2C_H, FF_Stage.FF_2C_L):
        return True 
    else:
        return False

def assign_nic_retest_flag(test_log_file, mtp_test_summary, stage):
    """
        1. Open mtp_test.log to search for "<SN> NIC_DIAG_REGRESSION_TEST_FAIL" (usually at the end)
        2. For those SN's failing, search for which test they failed "<SN> DIAG TEST <DSP> <TEST> <RESULT> "
    """
    with open(test_log_file, 'r') as fp:
        buf = fp.read()

    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL in buf:
        nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
        match = re.findall(nic_fail_reg_exp, buf)
        for slot, sn_type, sn in match:
            test_list = list()
            test_rslt_list = list()
            err_dsc_list = list()
            nic_cli_id_str = id_str(nic=int(slot), base=0)
            # find all test status
            nic_test_rslt_reg_exp = MTP_DIAG_Report.NIC_DIAG_TEST_RSLT_RE.format(slot, sn)
            sub_match = re.findall(nic_test_rslt_reg_exp, buf)
            for dsp, test, result in sub_match:
                # EXCLUDE PASSING TESTS
                if result == "PASS":
                    continue

                test_list.append("{:s}-{:s}".format(dsp, test))
                test_rslt_list.append(result)
                err_dsc_list.append(nic_cli_id_str)

            mac=None 
            pn=None
            nic_mac_pc_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_MAC_PN_BY_FRU_RE.format(sn)
            matchsnformacpn = re.findall(nic_mac_pc_reg_exp, buf)
            if matchsnformacpn:
                mac=matchsnformacpn[0][0]
                pn=matchsnformacpn[0][1]

            if FindDellSN(sn):
                nic_pn_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_PN_BY_FRU_RE.format(sn)
                matchsn = re.findall(nic_pn_reg_exp, buf)
                if matchsn:
                    sn = sn[:2] + matchsn[0][:6] + sn[2:] + matchsn[0][6:]
                else:
                    nic_pn_reg_exp2 = MTP_DIAG_Report.NIC_DIAG_REGRESSION_PN_BY_FRU2_RE.format(sn)
                    matchsn2 = re.findall(nic_pn_reg_exp2, buf)
                    if matchsn2:
                        sn = sn[:2] + matchsn2[0][:6] + sn[2:] + matchsn2[0][6:]

            block_retest = False
            for test in test_list:
                block_retest |= is_retest_blocked(test, stage)

            # replace the 5th field in matrix
            if block_retest:
                for idx in range(len(mtp_test_summary)):
                    # locate this SN's record
                    if mtp_test_summary[idx][1] == sn:
                        # block it
                        mtp_test_summary[idx][4] = True

def flx_web_srv_two_way_comm_precheck_uut(mtp_mgmt_ctrl, fail_nic_list, sn, stage, slot, retry = 0):
    post_cnt = 0
    time.sleep(1)
    while True:
        factory = mtp_mgmt_ctrl.get_mtp_factory_location()
        flex_rs = flx_web_srv_precheck_uut_status(sn, factory, stage)
        if flex_rs == 0:
            mtp_mgmt_ctrl.cli_log_slot_inf(slot, "{:d}th: Pre-Post [{:s}] result to webserver complete".format((post_cnt + 1), sn))
            break
        else:
            if flex_rs in FLEX_ERR_CODE_MAP.err_code:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "{:d}th: Pre-Post [{:s}] result to webserver failed. [{:s}:{:s}]".format((post_cnt + 1), sn, str(flex_rs), FLEX_ERR_CODE_MAP.err_code[flex_rs]))
            else:
                mtp_mgmt_ctrl.cli_log_slot_err(slot, "{:d}th: Pre-Post [{:s}] result to webserver failed. [ERROR: Unknown error code -->({:s})]".format((post_cnt + 1), sn, str(flex_rs)))
            if flex_rs != 9999 or retry == post_cnt:
                if slot not in fail_nic_list:
                    fail_nic_list.append(slot)
                break
        post_cnt += 1
        time.sleep(3)

    return fail_nic_list

def get_fst_nic_ssh_cmd(ip, username, passwd):
    ssh_cmd_fmt = "/home/diag/mtp_fst_script/sshpass -p {} ssh -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30' -o 'LogLevel=ERROR' {}@{}"
    ssh_cmd = ssh_cmd_fmt.format(passwd, username, ip)
    return ssh_cmd

def get_fst_nic_ssh_cmd_penctl(ip, username):
    ssh_cmd_fmt = "ssh -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30' -o 'LogLevel=ERROR' -i  ~/.ssh/id_rsa {}@{}"
    ssh_cmd = ssh_cmd_fmt.format(username, ip)
    return ssh_cmd

