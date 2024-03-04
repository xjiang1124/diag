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
from libdefs import Voltage_Margin
from libmfg_cfg import *
from libsku_utils import *
import image_control
import test_utils

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


def cli_wrn(err):
    print("\033[0;33m" + "## [" + get_timestamp() + "] WRN: " + err + "\033[0m")


def cli_log_inf(fp, info):
    msg = "## [" + get_timestamp() + "] LOG: " + info
    fp.write(msg + "\n")

    cli_inf(info)


def cli_log_err(fp, err):
    msg = "## [" + get_timestamp() + "] ERR: " + err
    fp.write(msg + "\n")

    cli_err(err)


def cli_log_wrn(fp, wrn):
    msg = "## [" + get_timestamp() + "] WRN: " + wrn
    fp.write(msg + "\n")

    cli_wrn(wrn)


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

def rot_cable_serial_number_validate(tmp):
    return re.match(r'^ROT-\d{5}$', tmp)

def part_number_match_rot_require_list(pn):

    rc = False
    for pattern in ROT_CABLE_REQUIRED_FOR_FST_PN_LIST:
        if re.match(pattern, pn):
            rc = True
            break
    return rc

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

def save_cfg_to_yaml(d, output_file):
    with open(output_file, "w+") as o:
        yaml.safe_dump(d, o)

    # read back to validate
    with open(output_file, "r") as i:
        e = yaml.safe_load(i)
        if d != e:
            return False
    return True

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
        cli_wrn("File md5sum mismatch")
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
    match = re.search(r"([0-9a-fA-F]{32}) +.*", str(session.before))
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

    if "*" not in remote_file: #skip md5sum checksum for wildcard/multifile copies
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
                cli_err("File {:s} md5sum mismatch".format(local_file))
                return False
        else:
            cli_err("Execute command {:s} on {:s} failed".format(cmd, ip_addr))
            return False

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
    return True


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
    return True


def mtp_get_sw_image_list(mtp_mgmt_ctrl, stage):
    image_list = list()
    nic_prsnt_list = mtp_mgmt_ctrl.mtp_get_nic_prsnt_list()
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if not nic_prsnt_list[slot]:
            continue
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        images_for_nic_type = image_control.get_all_images_for_stage(mtp_mgmt_ctrl, nic_type, stage)
        if images_for_nic_type is None:
            return None
        image_list += images_for_nic_type.values()

    image_list.append(NIC_IMAGES.uboot_img["INSTALLER"])
    return image_list

def rgx_extract_commit_date(buf):
    match = re.findall(r"Date: +(.*20\d{2})", buf)
    if match:
        return match[0]
    else:
        return None

def read_amd64_img_version(mtp_mgmt_ctrl, diag_img_tarball):
    cmd = "tar xfO {:s} diag/scripts/version.txt | head".format(diag_img_tarball)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Command {:s} failed".format(cmd), level=0)
        return None
    return rgx_extract_commit_date(mtp_mgmt_ctrl.mtp_get_cmd_buf())

def read_asiclib_version(mtp_mgmt_ctrl, diag_img_tarball):
    cmd = "tar xfO {:s} nic.tar.gz | tar xzO nic/asic_src/ip/cosim/tclsh/.git_rev.tcl | head".format(diag_img_tarball)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Command {:s} failed".format(cmd), level=0)
        return None
    return rgx_extract_commit_date(mtp_mgmt_ctrl.mtp_get_cmd_buf())

def running_diag_img_match(mtp_mgmt_ctrl, new_mtp_image):
    # wrong diag binaries
    mtp_mgmt_ctrl.mtp_init_diag_img_version()
    cur_version = mtp_mgmt_ctrl.mtp_get_sw_version()
    new_version = read_amd64_img_version(mtp_mgmt_ctrl, new_mtp_image)
    if new_version != cur_version:
        return False

    # or wrong asiclib
    mtp_mgmt_ctrl.mtp_init_diag_asiclib_version()
    cur_version = mtp_mgmt_ctrl.mtp_get_asic_version()
    new_version = read_asiclib_version(mtp_mgmt_ctrl, new_mtp_image)
    if new_version != cur_version:
        return False

    return True

def mtp_update_firmware(mtp_mgmt_ctrl, image_list):
    if not image_list:
        mtp_mgmt_ctrl.cli_log_err("Copy Firmware images failed... Abort", level=0)
        return False

    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    mtp_ip_addr = mtp_mgmt_cfg[0]
    mtp_usrid = mtp_mgmt_cfg[1]
    mtp_passwd = mtp_mgmt_cfg[2]
    image_dir = "/home/diag/"

    done_list = []
    image_list_unique = list(set(image_list))
    image_list_unique.sort()
    image_on_mtp = mtp_mgmt_ctrl.mtp_diag_get_img_files()
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

def mtp_update_diag_image(mtp_mgmt_ctrl, mtp_image=MFG_IMAGE_FILES.MTP_AMD64_IMAGE, nic_image=MFG_IMAGE_FILES.MTP_ARM64_IMAGE, force_update=False):
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
    image_on_mtp = mtp_mgmt_ctrl.mtp_diag_get_img_files()

    ### Update logic
    update_needed = False
    if force_update:
        update_needed = True

    # check for file present
    elif mtp_image not in image_on_mtp or nic_image not in image_on_mtp:
        mtp_mgmt_ctrl.cli_log_inf("Image files not present...updating", level=0)
        update_needed = True

    # compare checksum
    elif need_mtp_file_update(mtp_ip_addr, mtp_usrid, mtp_passwd, mtp_image_file, remote_dir + os.path.basename(mtp_image)) \
      or need_mtp_file_update(mtp_ip_addr, mtp_usrid, mtp_passwd, nic_image_file, remote_dir + os.path.basename(nic_image)):
        mtp_mgmt_ctrl.cli_log_inf("Older tarball on MTP...updating", level=0)
        update_needed = True

    # check previously loaded version on MTP
    elif not running_diag_img_match(mtp_mgmt_ctrl, mtp_image):
        mtp_mgmt_ctrl.cli_log_inf("Loaded diag image doesn't match...updating", level=0)
        update_needed = True

    if not update_needed:
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

def mtp_update_fst_image(mtp_mgmt_ctrl, mtp_image=MFG_IMAGE_FILES.penctl_img, nic_image=MFG_IMAGE_FILES.penctl_token_img):
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

    image_on_mtp = mtp_mgmt_ctrl.mtp_diag_get_img_files()
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

def load_barcode_sn_pn(mtp_mgmt_ctrl, slot):
    if mtp_mgmt_ctrl.barcode_scans == {}:
        return False
    mtp_id = mtp_mgmt_ctrl._id
    key = nic_key(slot)
    if key not in mtp_mgmt_ctrl.barcode_scans.keys():
        return False
    if not mtp_mgmt_ctrl.barcode_scans[key]["VALID"]:
        return False
    sn = mtp_mgmt_ctrl.barcode_scans[key]["SN"]
    pn = mtp_mgmt_ctrl.barcode_scans[key]["PN"]
    nic_type = get_nic_type_by_part_number(pn)
    mtp_mgmt_ctrl.mtp_set_nic_sn(slot, sn)
    mtp_mgmt_ctrl.mtp_set_nic_type(slot, nic_type)
    return True

def fail_all_slots(mtp_mgmt_ctrl):
    """
     Call this function when failing a script BEFORE any dsp test results have come.
     e.g. whole MTP fails: report as all cards failed
     e.g. connection problem: report as all cards failed
    """
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if not mtp_mgmt_ctrl._nic_prsnt_list[slot]:
            # may not have initialized prsnt_list yet. But this stage may have SCAN. 
            # So try to load SN and NIC_TYPE from the scans.
            # Otherwise, skip this slot
            if not load_barcode_sn_pn(mtp_mgmt_ctrl, slot):
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
    mtp_mgmt_ctrl.log_nic_file(slot, "######## {:s} ########".format("START post fail debug"))
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

        if mtp_mgmt_ctrl.mtp_get_nic_type(slot) in ELBA_NIC_TYPE_LIST or mtp_mgmt_ctrl.mtp_get_nic_type(slot) in GIGLIO_NIC_TYPE_LIST:
            mtp_mgmt_ctrl.mtp_single_j2c_lock()
            mtp_mgmt_ctrl.mtp_nic_read_temp(slot)
            if mtp_mgmt_ctrl.mtp_nic_failed_boot(slot):
                mtp_mgmt_ctrl.mtp_nic_l1_health_check(slot) # for a CONSOLE_BOOT failure ONLY: do a mini L1
            mtp_mgmt_ctrl.mtp_single_j2c_unlock()
    

    # in case nic hung up the bus:
    mtp_mgmt_ctrl.mtp_power_off_single_nic(slot)
    mtp_mgmt_ctrl.mtp_reset_hub(slot)
    mtp_mgmt_ctrl.log_nic_file(slot, "######## {:s} ########".format("END post fail debug"))
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

def flx_soap_save_uut_result_xml(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, ocp_adap_sn, mfg_script_ver, factory, mac=None, pn=None, rot_sn=None):
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
    if stage == FF_Stage.FF_FST and rot_sn:
        extra_info_xml += "FST_ROT_SN=\"{:s}\" ".format(rot_sn)

    if mtp_psu_sn_list or nic_loopback_sn_list or ocp_adap_sn:
        for psu, psu_sn in zip(mtp_psu_sn_list.keys(), mtp_psu_sn_list.values()):
            extra_info_xml += "PSU_{:s}=\"{:s}\" ".format(psu, psu_sn)

        for lpbk, lpbk_sn in zip(nic_loopback_sn_list.keys(), nic_loopback_sn_list.values()):
            extra_info_xml += "LOOPBACK_PORT{:s}=\"{:s}\" ".format(lpbk, lpbk_sn)

        extra_info_xml += "OCP_ADAPTER=\"{:s}\" ".format(ocp_adap_sn)

        extra_info_xml += "MFG_SCRIPT_VER=\"{:s}\" ".format(mfg_script_ver)

    if extra_info_xml:
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
    elif stage == FF_Stage.FF_ORT:
        return FPN_FF_Stage.FF_ORT
    elif stage == FF_Stage.FF_RDT:
        return FPN_FF_Stage.FF_RDT
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
    except Exception as Err:
        cli_dbg(Err)
        cli_dbg("Exception occur when send HTTP POST request to webserver, please check server avaiblity")
        return 88888888
    else:
        statuscode, reason, msg = webservice.getreply()
        cli_dbg("HTTP POST response, status code: {:s},  status reason: {:s}, status message: {:s}".format(str(statuscode), reason, msg))
        if not str(statuscode).startswith('2'):
            cli_dbg("HTTP POST request NOT successful, return HTTP statuscode")
            return int(statuscode)
        resp = webservice.getfile().read()
        match = re.findall(FLX_SAVE_UUT_RSLT_CODE_RE, resp)
        cli_inf("HTTP POST request successful")
        if match:
            cli_inf("GOT FLX_SAVE_UUT_RSLT_CODE {:s} From HTTP POST Response, Return it".format(match[0]))
            return match[0]
        else:
            cli_dbg("Failed to parse FLX_SAVE_UUT_RSLT_CODE From HTTP POST Response, display the response as following:")
            cli_dbg("################## SAVE UUT RSLT #######################")
            cli_dbg(resp)
            cli_dbg("################## SAVE UUT RSLT #######################")
            return 58888888
    finally:
        webservice.close()


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
    except Exception as Err:
        cli_dbg(Err)
        cli_dbg("Exception occur when send HTTP POST request to webserver, please check server avaiblity")
        return 88888888
    else:
        statuscode, reason, msg = webservice.getreply()
        cli_dbg("HTTP POST response, status code: {:s},  status reason: {:s}, status message: {:s}".format(str(statuscode), reason, msg))
        if not str(statuscode).startswith('2'):
            cli_dbg("HTTP POST request NOT successful, return HTTP statuscode")
            return int(statuscode)
        resp = webservice.getfile().read()
        match = re.findall(FLX_GET_UUT_INFO_CODE_RE, resp)
        cli_inf("HTTP POST request successful")
        if match:
            cli_inf("GOT FLX_GET_UUT_INFO_CODE {:s} From HTTP POST Response, Return it".format(match[0]))
            return match[0]
        else:
            cli_dbg("Failed to parse FLX_GET_UUT_INFO_CODE From HTTP POST Response, display the response as following:")
            cli_dbg("################## GET UUT INFO RSLT #######################")
            cli_dbg(resp)
            cli_dbg("################## GET UUT INFO RSLT #######################")
            return 58888888
    finally:
        webservice.close()

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
    except Exception as Err:
        cli_dbg(Err)
        cli_dbg("Exception occur when send HTTP POST request to webserver, please check server avaiblity")
        return "88888888"
    else:
        statuscode, reason, msg = webservice.getreply()
        cli_dbg("HTTP POST response, status code: {:s},  status reason: {:s}, status message: {:s}".format(str(statuscode), reason, msg))
        if not str(statuscode).startswith('2'):
            cli_dbg("HTTP POST request NOT successful, return HTTP statuscode")
            return int(statuscode)
        resp = webservice.getfile().read()
        cli_inf("HTTP POST request successful")
        return resp
    finally:
        webservice.close()

def flx_web_srv_post_uut_report(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, ocp_adap_sn, mfg_script_ver, factory, mac=None, pn=None,  rot_sn=None):
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

    xml = flx_soap_save_uut_result_xml(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, ocp_adap_sn, mfg_script_ver, factory, mac, pn, rot_sn)
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

def flx_web_srv_post_uut_status(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, ocp_adap_sn, mfg_script_ver, factory, mac=None, pn=None, rot_sn=None):
    if factory is None or factory == Factory.UNKNOWN:
        factory = flx_sn_to_factory(sn)

    if not factory:
        print("Unable to locate flex factory based on sn: {:s}".format(sn))
        return -3

    xml = flx_soap_save_uut_result_xml(stage, nic_type, sn, rslt, start_ts, stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, ocp_adap_sn, mfg_script_ver, factory, mac, pn, rot_sn)
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


def mfg_report(mtp_mgmt_ctrl, mtp_id, mtp_start_ts, mtp_stop_ts, buf, stage, mtp_test_summary=[]):
    import testlog
    mtp_cli_id_str = id_str(mtp = mtp_id)
    duration = mtp_stop_ts - mtp_start_ts

    # Factory detected related error, don't post any report
    factory =  mtp_mgmt_ctrl.get_mtp_factory_location()
    if factory is None or factory == Factory.UNKNOWN:
        cli_inf(mtp_cli_id_str + "MTP Setup fails and not able to detect factory so no report will be generated")
        return

    cli_inf(mtp_cli_id_str + "Start posting test report")
    if MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL in buf:
        nic_fail_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_RSLT_RE.format(MTP_DIAG_Report.NIC_DIAG_REGRESSION_FAIL)
        match = re.findall(nic_fail_reg_exp, buf)
        for slot, sn_type, sn in match:
            mtp_psu_sn_list = dict()
            nic_loopback_sn_list = dict()
            ocp_adap_sn = ""
            mfg_script_ver = mtp_mgmt_ctrl._script_ver
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

                # save serial number of OCP adapter
                if mtp_mgmt_ctrl.mtp_get_nic_type(int(slot)-1) == NIC_Type.NAPLES25OCP:
                    riser_sn = mtp_mgmt_ctrl.mtp_get_nic_ocp_adapter_sn(int(slot)-1)
                    if riser_sn:
                        ocp_adap_sn = riser_sn

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

            rot_sn = None
            if stage == FF_Stage.FF_FST:
                nic_rot_sn_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_ROT_SN_BY_FRU_RE.format(sn)
                matchsnfor_rot_sn = re.findall(nic_rot_sn_reg_exp, buf)
                if matchsnfor_rot_sn:
                    rot_sn=matchsnfor_rot_sn[-1][0]

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
                block_retest |= testlog.is_retest_blocked(test, stage)


            if FLEX_SHOP_FLOOR_CONTROL:
                if sn is not None and str(sn).upper() != "UNKNOWN" and str(sn).upper() != "NONE" and len(str(sn)) > 6:
                    post_cnt = 0
                    retry = FLEX_TWO_WAY_COMM.POST_RETRY
                    time.sleep(1)
                    while True:
                        rs = flx_web_srv_post_uut_status(stage, sn_type, sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, ocp_adap_sn, mfg_script_ver, factory, mac, pn, rot_sn)
                        if rs == 0:
                            cli_inf(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver complete".format((post_cnt + 1), sn))
                            break
                        else:
                            if rs in FLEX_ERR_CODE_MAP.err_code:
                                cli_err(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver failed. [Database Server Access Error: error code ({:s}) --> {:s}]".format((post_cnt + 1), sn, str(rs), FLEX_ERR_CODE_MAP.err_code[rs]))
                            elif rs in httplib.responses:
                                cli_err(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver failed. [HTTP Response ERROR: error code ({:s}) --> {:s}]".format((post_cnt + 1), sn, str(rs)), httplib.responses[rs])
                            elif rs == 88888888:
                                cli_err(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver failed. [Sending HTTP Request Error: error code ({:s}) --> Please check server avaiblity and network connectivity]".format((post_cnt + 1), sn, str(rs)))
                            elif rs == 58888888:
                                cli_err(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver failed. [Parse Xml data Error: error code ({:s}) --> did not find xml tag <GetUnitInfoResult> or <SaveResultResult> in xml data]".format((post_cnt + 1), sn, str(rs)))
                            else:
                                cli_err(mtp_cli_id_str + "{:d}th: Post [{:s}] result to webserver failed. [ERROR: Unknown error code -->({:s})]".format((post_cnt + 1), sn, str(rs)))
                            if rs != 9999:
                                post_cnt = retry
                            if post_cnt >= retry:
                                break
                        post_cnt += 1
                        time.sleep(3)

            else:
                ret = flx_web_srv_post_uut_report(stage, sn_type, sn, "FAIL", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, ocp_adap_sn, mfg_script_ver, factory, mac, pn, rot_sn)
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
            ocp_adap_sn = ""
            mfg_script_ver = mtp_mgmt_ctrl._script_ver
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

                # save serial number of OCP adapter
                if mtp_mgmt_ctrl.mtp_get_nic_type(int(slot)-1) == NIC_Type.NAPLES25OCP:
                    riser_sn = mtp_mgmt_ctrl.mtp_get_nic_ocp_adapter_sn(int(slot)-1)
                    if riser_sn:
                        ocp_adap_sn = riser_sn

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

            rot_sn = None
            if stage == FF_Stage.FF_FST:
                nic_rot_sn_reg_exp = MTP_DIAG_Report.NIC_DIAG_REGRESSION_ROT_SN_BY_FRU_RE.format(sn)
                matchsnfor_rot_sn = re.findall(nic_rot_sn_reg_exp, buf)
                if matchsnfor_rot_sn:
                    rot_sn=matchsnfor_rot_sn[-1][0]

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
                if sn is not None and str(sn).upper() != "UNKNOWN" and str(sn).upper() != "NONE" and len(str(sn)) > 6:
                    post_cnt = 0
                    retry = FLEX_TWO_WAY_COMM.POST_RETRY
                    time.sleep(1)
                    while True:
                        rs = flx_web_srv_post_uut_status(stage, sn_type, sn, "PASS", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, ocp_adap_sn, mfg_script_ver, factory, mac, pn, rot_sn)
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
                ret = flx_web_srv_post_uut_report(stage, sn_type, sn, "PASS", mtp_start_ts, mtp_stop_ts, duration, test_list, test_rslt_list, err_dsc_list, err_code_list, mtp_psu_sn_list, nic_loopback_sn_list, ocp_adap_sn, mfg_script_ver, factory, mac, pn, rot_sn)
                if not ret:
                    cli_err(mtp_cli_id_str + "Post [{:s}] result to webserver failed".format(sn))
                else:
                    cli_inf(mtp_cli_id_str + "Post [{:s}] result to webserver complete".format(sn))


def mfg_summary_disp(stage, summary_dict, mtp_fail_list):
    final_result = True
    cli_inf("##########  MFG {:s} Test Summary  ##########".format(stage))
    for mtp_id in summary_dict.keys():
        cli_inf("---------- {:s} Report: ----------".format(mtp_id))
        if len(summary_dict[mtp_id]) == 0:
            # test didnt finish properly
            final_result = False
            continue
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
    final_result = True
    for mtp_id in summary_dict.keys():
        for slot, sn, nic_type, rc, retest in summary_dict[mtp_id]:
            if rc:
                cli_inf("{:s} {:s} {:s} PASS".format(slot, sn, nic_type))
            else:
                final_result = False
                cli_err("{:s} {:s} {:s} FAIL".format(slot, sn, nic_type))
    cli_inf("--------- Report End --------\n")
    for mtp_id in mtp_fail_list:
        cli_err("-------- {:s} Test Aborted -------\n".format(mtp_id))
        final_result = False
    return final_result

def mfg_summary_srn_disp(stage, summary_dict, mtp_fail_list, mtp_sn):
    cli_inf("##########  MFG {:s} Test Summary  ##########".format(stage))
    result = True
    for mtp_id in summary_dict.keys():
        cli_inf("---------- {:s} Report: ----------".format(mtp_id))
        if len(mtp_fail_list) > 0:
            cli_err("[{:s}] {:s} FAIL".format(mtp_id, mtp_sn))
        else:
            #one fail all fail
            for slot, sn, nic_type, rc, retest in summary_dict[mtp_id]:
                nic_cli_id_str = id_str(mtp=mtp_id, nic=int(slot), base=0)
                if not rc:
                    result = False
                    
        if result:
            cli_inf("[{:s}] {:s} PASS".format(mtp_id, mtp_sn))
        else:
            cli_err("[{:s}] {:s} FAIL".format(mtp_id, mtp_sn))
        cli_inf("--------- {:s} Report End --------\n".format(mtp_id))

def mtp_common_setup(*args, **kwargs):
    # for backward compatability
    return test_utils.mtp_common_setup(*args, **kwargs)

def mtp_common_setup_fpo(*args, **kwargs):
    # for backward compatability
    return test_utils.mtp_common_setup_fpo(*args, **kwargs)

def mtp_setup(mtp_mgmt_ctrl, setup_rslt_list):
    setup_rslt_list[mtp_mgmt_ctrl._id] = mtp_common_setup(mtp_mgmt_ctrl)

def display_failures(mtp_mgmt_ctrl, nic_list, loopback_fail_list, fail_nic_list, length):
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
    mtp_id = mtp_mgmt_ctrl._id

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
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot not in nic_list or slot in fail_nic_list:
            pre += "    "
        elif loopback_fail_list[slot] > 0:
            pre += "X   "
        else:
            pre += "o   "
    pre += "  |"
    print(pre)

    # Port 2 row
    pre="|     "
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot not in nic_list or slot in fail_nic_list:
            pre += "    "
        elif loopback_fail_list[slot+length] > 0:
            pre += "X   "
        else:
            pre += "o   "
    pre += "  |"
    print(pre)

    print(vertical_border)

    pre="|    "
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        pre+= "{:>2s}  ".format(str(slot+1))
    pre += "   |"
    print(pre)

    print(vertical_border)
    print(mtp_name_bot)
    print(horizontal_border)



    for slot in nic_list:
        if loopback_fail_list[slot]:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "QSFP Module 1 is missing")
        if loopback_fail_list[slot+length]:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "QSFP Module 2 is missing")

    return

def display_rj45_failures(mtp_mgmt_ctrl, nic_list, loopback_fail_list, fail_nic_list):
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
    mtp_id = mtp_mgmt_ctrl._id
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
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if slot not in nic_list or slot in fail_nic_list:
            pre += "    "
        elif loopback_fail_list[slot] > 0:
            pre += "X   "
        else:
            pre += "o   "
    pre += "  |"
    print(pre)

    # Port 2 row, for naples100 only
    pre="|     "
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        if (
            slot not in nic_list
            or slot in fail_nic_list
            or mtp_mgmt_ctrl.mtp_get_nic_type(slot) in ELBA_NIC_TYPE_LIST
            or mtp_mgmt_ctrl.mtp_get_nic_type(slot) in GIGLIO_NIC_TYPE_LIST
            or mtp_mgmt_ctrl.mtp_get_nic_type(slot) not in TWO_OOB_MGMT_PORT_TYPE_LIST
            ):
            pre += "    "
        elif loopback_fail_list[slot] > 0 and mtp_mgmt_ctrl.mtp_get_nic_type(slot) in TWO_OOB_MGMT_PORT_TYPE_LIST:
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
    for slot in range(MTP_Const.MTP_SLOT_NUM):
        pre+= "{:>2s}  ".format(str(slot+1))
    pre += "   |"
    print(pre)

    print(vertical_border)
    print(mtp_name_bot)
    print(horizontal_border)



    for slot in nic_list:
        if loopback_fail_list[slot]:
            mtp_mgmt_ctrl.cli_log_slot_err(slot, "RJ45 module is missing")

    return
    

def loopback_sanity_check(mtp_mgmt_ctrl, nic_list):
    max_retries_per_slot = 3
    length = MTP_Const.MTP_SLOT_NUM
    loopback_fail_list = [0, 0] * length
    cur_fail_list = [0, 0] * length
    fail_nic_list = list()
    start_ts = timestamp_snapshot()
    while True:
        failure_detected = False
        for slot in nic_list:
            if slot not in fail_nic_list:
                cur_fail_list[slot] = 0
                cur_fail_list[slot+length] = 0
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type in ELBA_NIC_TYPE_LIST:
                    read_data = [0]
                    rc = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_read_cpld_via_smbus(reg_addr=0x40, read_data=read_data)
                    if not rc:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read CPLD")
                        if slot not in fail_nic_list:
                            fail_nic_list.append(slot)
                        continue

                    ### QSFP/SFP PORT 1
                    if read_data[0] & 0x01 == 0:
                        # not present, retry 3x
                        if loopback_fail_list[slot] == max_retries_per_slot:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            continue
                        else:
                            cur_fail_list[slot] = 1
                            loopback_fail_list[slot] += 1
                            failure_detected = True
                    else:
                        # log the transceiver serial number. retry 3x if unable to read.
                        if not mtp_mgmt_ctrl.mtp_nic_read_transceiver_sn(slot, "1"):
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read loopback EEPROM")
                            if loopback_fail_list[slot] == max_retries_per_slot:
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                continue
                            else:
                                cur_fail_list[slot] = 1
                                loopback_fail_list[slot] += 1
                                failure_detected = True

                    ### QSFP/SFP PORT 2
                    if read_data[0] & 0x02 == 0:
                        # not present, retry 3x
                        if loopback_fail_list[slot+length] == max_retries_per_slot:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            continue
                        else:
                            cur_fail_list[slot+length] = 1
                            loopback_fail_list[slot+length] += 1
                            failure_detected = True
                    else:
                        # log the transceiver serial number. retry 3x if unable to read.
                        if not mtp_mgmt_ctrl.mtp_nic_read_transceiver_sn(slot, "2"):
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read loopback EEPROM")
                            if loopback_fail_list[slot+length] == max_retries_per_slot:
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                continue
                            else:
                                cur_fail_list[slot+length] = 1
                                loopback_fail_list[slot+length] += 1
                                failure_detected = True

                elif nic_type in GIGLIO_NIC_TYPE_LIST:
                    read_data = [0]
                    rc = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_read_cpld_via_smbus(reg_addr=0x40, read_data=read_data)
                    if not rc:
                        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read CPLD")
                        if slot not in fail_nic_list:
                            fail_nic_list.append(slot)
                        continue

                    ### QSFP/SFP PORT 1
                    if read_data[0] & 0x01 == 0:
                        # not present, retry 3x
                        if loopback_fail_list[slot] == max_retries_per_slot:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            continue
                        else:
                            cur_fail_list[slot] = 1
                            loopback_fail_list[slot] += 1
                            failure_detected = True
                    else:
                        # log the transceiver serial number. retry 3x if unable to read.
                        if not mtp_mgmt_ctrl.mtp_nic_read_transceiver_sn(slot, "0"):
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read loopback EEPROM")
                            if loopback_fail_list[slot] == max_retries_per_slot:
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                continue
                            else:
                                cur_fail_list[slot] = 1
                                loopback_fail_list[slot] += 1
                                failure_detected = True

                    ### QSFP/SFP PORT 2
                    if read_data[0] & 0x02 == 0:
                        # not present, retry 3x
                        if loopback_fail_list[slot+length] == max_retries_per_slot:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            continue
                        else:
                            cur_fail_list[slot+length] = 1
                            loopback_fail_list[slot+length] += 1
                            failure_detected = True
                    else:
                        # log the transceiver serial number. retry 3x if unable to read.
                        if not mtp_mgmt_ctrl.mtp_nic_read_transceiver_sn(slot, "1"):
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read loopback EEPROM")
                            if loopback_fail_list[slot+length] == max_retries_per_slot:
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                continue
                            else:
                                cur_fail_list[slot+length] = 1
                                loopback_fail_list[slot+length] += 1
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
                        read_data = [0]

                    if read_data[0] & expected_val != expected_val:
                        if loopback_fail_list[slot] == max_retries_per_slot:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            continue
                        else:
                            cur_fail_list[slot] = 1
                            loopback_fail_list[slot] += 1
                            failure_detected = True
                    else:
                        # log the transceiver serial number. retry 3x if unable to read.
                        if not mtp_mgmt_ctrl.mtp_nic_read_transceiver_sn(slot, "0"):
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read loopback EEPROM")
                            if loopback_fail_list[slot] == max_retries_per_slot:
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                continue
                            else:
                                cur_fail_list[slot] = 1
                                loopback_fail_list[slot] += 1
                                failure_detected = True

                    # QSFP/SFP port 2
                    read_data = [0]
                    rc = mtp_mgmt_ctrl._nic_ctrl_list[slot].nic_console_read_i2c(1, 0x50, 0, read_data)
                    if not rc:
                        read_data = [0]

                    if read_data[0] & expected_val != expected_val:
                        if loopback_fail_list[slot+length] == max_retries_per_slot:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            continue
                        else:
                            cur_fail_list[slot+length] = 1
                            loopback_fail_list[slot+length] += 1
                            failure_detected = True
                    else:
                        # log the transceiver serial number. retry 3x if unable to read.
                        if not mtp_mgmt_ctrl.mtp_nic_read_transceiver_sn(slot, "1"):
                            mtp_mgmt_ctrl.cli_log_slot_err(slot, "Unable to read loopback EEPROM")
                            if loopback_fail_list[slot+length] == max_retries_per_slot:
                                if slot not in fail_nic_list:
                                    fail_nic_list.append(slot)
                                continue
                            else:
                                cur_fail_list[slot+length] = 1
                                loopback_fail_list[slot+length] += 1
                                failure_detected = True

        display_failures(mtp_mgmt_ctrl, nic_list, cur_fail_list, fail_nic_list, length)

        if not failure_detected:
            break

        # while True:
        raw_input("Please re-insert the modules above then press any key to continue.\nWARNING: do not power off the MTP yet. ")

        mtp_mgmt_ctrl.cli_log_inf("Re-running sanity check...", level=0)

    stop_ts = timestamp_snapshot()
    duration = str(stop_ts - start_ts)

    fail_rslt_list = list()
    mtp_id = mtp_mgmt_ctrl._id
    for slot in fail_nic_list:
        nic_cli_id_str = id_str(mtp=mtp_id, nic=slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        fail_rslt_list.append(nic_cli_id_str + "Sanity check failed {:d} attempts".format(max_retries_per_slot))
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, "SANITY_CHECK", "QSFP", "FAILED", duration))
    cli_log_rslt("{:s} Eth Sanity Check complete".format(mtp_id), [], fail_rslt_list, mtp_mgmt_ctrl._filep)

    return fail_nic_list

def rj45_sanity_check(mtp_mgmt_ctrl, nic_list):
    max_retries_per_slot = 3

    length = MTP_Const.MTP_SLOT_NUM
    loopback_fail_list = [0] * length
    cur_fail_list = [0] * length
    fail_nic_list = list()

    start_ts = timestamp_snapshot()

    while True:
        failure_detected = False
        for slot in nic_list:
            if slot not in fail_nic_list:
                cur_fail_list[slot] = 0
                nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
                if nic_type in [NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4]:
                    continue
                if nic_type in ELBA_NIC_TYPE_LIST and nic_type in FPGA_TYPE_LIST:
                    ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_phy_xcvr_link_test(slot)
                elif nic_type in ELBA_NIC_TYPE_LIST:
                    ret, err_msg_list = mtp_mgmt_ctrl.mtp_nic_mvl_link_test(slot)

                if nic_type in ELBA_NIC_TYPE_LIST:
                    if ret != "SUCCESS":
                        if loopback_fail_list[slot] == max_retries_per_slot:
                            if slot not in fail_nic_list:
                                fail_nic_list.append(slot)
                            continue
                        else:
                            cur_fail_list[slot] = 1
                            loopback_fail_list[slot] += 1
                            failure_detected = True

        display_rj45_failures(mtp_mgmt_ctrl, nic_list, cur_fail_list, fail_nic_list)

        if not failure_detected:
            break

        raw_input("Please re-insert the RJ45 modules above then press any key to continue.\nWARNING: do not power off the MTP yet. ")

        mtp_mgmt_ctrl.cli_log_inf("Re-running sanity check...", level=0)

    stop_ts = timestamp_snapshot()
    duration = str(stop_ts - start_ts)

    fail_rslt_list = list()
    mtp_id = mtp_mgmt_ctrl._id
    for slot in fail_nic_list:
        nic_cli_id_str = id_str(mtp=mtp_id, nic=slot)
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
        fail_rslt_list.append(nic_cli_id_str + "Sanity check failed {:d} attempts".format(max_retries_per_slot))
        mtp_mgmt_ctrl.cli_log_slot_err_lock(slot, MTP_DIAG_Report.NIC_DIAG_TEST_FAIL.format(sn, "SANITY_CHECK", "RJ45", "FAILED", duration))
    cli_log_rslt("{:s} RJ45 Sanity Check complete".format(mtp_id), [], fail_rslt_list, mtp_mgmt_ctrl._filep)

    return fail_nic_list

def sanity_check_setup(mtp_mgmt_ctrl, nic_list):
    cli_log_rslt("Begin Sanity Check .. Please monitor until complete", [], [], mtp_mgmt_ctrl._filep)

    fail_nic_list = list()
    para_nic_list = list()       # needs para_init
    mgmt_nic_list = list()  # needs para_mgmt_init
    for slot in nic_list:
        nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
        if nic_type in FPGA_TYPE_LIST:
            mgmt_nic_list.append(slot)
        else:
            para_nic_list.append(slot)

    # for all cards:
    if para_nic_list:
        if not mtp_mgmt_ctrl.mtp_nic_para_init(para_nic_list):
            for slot in para_nic_list:
                if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)

    # for lacona/pomonte:
    if mgmt_nic_list:
        if not mtp_mgmt_ctrl.mtp_nic_mgmt_para_init(mgmt_nic_list, False):
            for slot in mgmt_nic_list:
                if not mtp_mgmt_ctrl.mtp_check_nic_status(slot):
                    if slot not in fail_nic_list:
                        fail_nic_list.append(slot)

    return fail_nic_list

def mtp_power_log_start(mtp_mgmt_ctrl):
    mtp_mgmt_ctrl.cli_log_inf("Start logging MTP syslog\n", level=0)
    mtp_syslog_handle = mtp_mgmt_ctrl.mtp_session_create()
    mtp_syslog_handle.sendline("while [ 1 ]; do devmgr -status; sleep 60; done > /home/diag/mtp_regression/mtp_sts.log")

    return mtp_syslog_handle

def mtp_power_log_end(mtp_mgmt_ctrl, mtp_syslog_handle):
    mtp_mgmt_ctrl.cli_log_inf("End logging MTP syslog", level=0)
    mtp_syslog_handle.send('\x03')
    mtp_syslog_handle.close()

@test_utils.semi_parallel_test_section
def flx_web_srv_two_way_comm_precheck_uut(mtp_mgmt_ctrl, slot, stage, sn=None, retry = 0):
    if sn is None:
        sn = mtp_mgmt_ctrl.mtp_get_nic_sn(slot)
    if sn is None or str(sn).upper() == "UNKNOWN" or str(sn).upper() == "NONE" or len(str(sn)) <= 6:
        mtp_mgmt_ctrl.cli_log_slot_err(slot, "Bad SN for area check: '{:s}'".format(str(sn)))
        return False
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
                return False
        post_cnt += 1
        time.sleep(3)

    return True

def get_fst_nic_ssh_cmd(ip, username, passwd):
    ssh_cmd_fmt = "/home/diag/mtp_fst_script/sshpass -p {} ssh -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30' -o 'LogLevel=ERROR' {}@{}"
    ssh_cmd = ssh_cmd_fmt.format(passwd, username, ip)
    return ssh_cmd

def get_fst_nic_ssh_cmd_penctl(ip, username):
    ssh_cmd_fmt = "ssh -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30' -o 'LogLevel=ERROR' -i  ~/.ssh/id_rsa {}@{}"
    ssh_cmd = ssh_cmd_fmt.format(username, ip)
    return ssh_cmd

"""
+--------+----------------+-----------------+------------+------------------+
| Stage  | Low Threshold  | High Threshold  | Fan Speed  | Voltage Margins  |
+--------+----------------+-----------------+------------+------------------+
| P2C    | None           | None            | NORM       | normal           |
| CI/CD  | None           | None            | NORM       | high, low        |
| 2C_L   | LOW            | None            | LOW        | high, low        |
| 2C_H   | None           | HIGH            | HIGH       | low, high        |
| 4C_H   | None           | HIGH            | HIGH       | low, high        |
| 4C_L   | LOW            | None            | LOW        | high, low        |
| ORT    | None           | None            | HIGH       | normal           |
+--------+----------------+-----------------+------------+------------------+
"""

def pick_temperature_thresholds(stage):
    if stage == FF_Stage.FF_P2C:
        low_temp_threshold = None
        high_temp_threshold = None

    elif stage == FF_Stage.FF_2C_L:
        low_temp_threshold = MTP_Const.MFG_EDVT_LOW_TEMP
        high_temp_threshold = None

        if not GLB_CFG_MFG_TEST_MODE:
            low_temp_threshold = MTP_Const.MFG_MODEL_EDVT_LOW_TEMP

    elif stage == FF_Stage.FF_4C_L:
        low_temp_threshold = MTP_Const.MFG_EDVT_LOW_TEMP
        high_temp_threshold = None

        if not GLB_CFG_MFG_TEST_MODE:
            low_temp_threshold = MTP_Const.MFG_MODEL_EDVT_LOW_TEMP

    elif stage == FF_Stage.FF_2C_H:
        low_temp_threshold = None
        high_temp_threshold = MTP_Const.MFG_EDVT_HIGH_TEMP

        if not GLB_CFG_MFG_TEST_MODE:
            high_temp_threshold = MTP_Const.MFG_MODEL_EDVT_HIGH_TEMP

    elif stage == FF_Stage.FF_4C_H:
        low_temp_threshold = None
        high_temp_threshold = MTP_Const.MFG_EDVT_HIGH_TEMP

        if not GLB_CFG_MFG_TEST_MODE:
            high_temp_threshold = MTP_Const.MFG_MODEL_EDVT_HIGH_TEMP

    else:
        low_temp_threshold = None
        high_temp_threshold = None

    return low_temp_threshold, high_temp_threshold

def pick_fan_speed(stage):
    if stage == FF_Stage.FF_P2C:
        fanspd = MTP_Const.MFG_EDVT_NORM_FAN_SPD

    elif stage == FF_Stage.FF_2C_L:
        fanspd = MTP_Const.MFG_EDVT_LOW_FAN_SPD

        if not GLB_CFG_MFG_TEST_MODE:
            fanspd = MTP_Const.MFG_MODEL_EDVT_LOW_FAN_SPD

    elif stage == FF_Stage.FF_4C_L:
        fanspd = MTP_Const.MFG_EDVT_LOW_FAN_SPD

        if not GLB_CFG_MFG_TEST_MODE:
            fanspd = MTP_Const.MFG_MODEL_EDVT_LOW_FAN_SPD

    elif stage == FF_Stage.FF_2C_H:
        fanspd = MTP_Const.MFG_EDVT_HIGH_FAN_SPD

        if not GLB_CFG_MFG_TEST_MODE:
            fanspd = MTP_Const.MFG_MODEL_EDVT_HIGH_FAN_SPD

    elif stage == FF_Stage.FF_4C_H:
        fanspd = MTP_Const.MFG_EDVT_HIGH_FAN_SPD

        if not GLB_CFG_MFG_TEST_MODE:
            fanspd = MTP_Const.MFG_MODEL_EDVT_HIGH_FAN_SPD

    elif stage == FF_Stage.FF_ORT:
        fanspd = MTP_Const.MFG_EDVT_HIGH_FAN_SPD

    elif stage == FF_Stage.FF_RDT:
        fanspd = MTP_Const.MFG_EDVT_HIGH_FAN_SPD

    else:
        fanspd = MTP_Const.MFG_EDVT_NORM_FAN_SPD

    return fanspd

def pick_voltage_margin(stage):
    if stage == FF_Stage.FF_P2C:
        vmarg_list = [Voltage_Margin.normal]

    elif stage == FF_Stage.QA:
        vmarg_list = [Voltage_Margin.high, Voltage_Margin.low]

    elif stage == FF_Stage.FF_2C_L:
        vmarg_list = [Voltage_Margin.high]

    elif stage == FF_Stage.FF_2C_H:
        vmarg_list = [Voltage_Margin.low]

    elif stage == FF_Stage.FF_4C_L:
        vmarg_list = [Voltage_Margin.high, Voltage_Margin.low]

    elif stage == FF_Stage.FF_4C_H:
        vmarg_list = [Voltage_Margin.low, Voltage_Margin.high]

    elif stage == FF_Stage.FF_ORT:
        vmarg_list = [Voltage_Margin.normal]

    elif stage == FF_Stage.FF_RDT:
        vmarg_list = [Voltage_Margin.normal]

    else:
        vmarg_list = [Voltage_Margin.normal]

    return vmarg_list

def pick_voltage_margin_percentage(part_number=None):

    partnumber = part_number if part_number else "DEFAULT"
    no_rev_partnumber =  "-".join(partnumber.split("-")[0:2])
    if partnumber != "DEFAULT" and partnumber == no_rev_partnumber:
        no_rev_partnumber = partnumber[0:6]
    vmarg_percentage = VMARG_PERCENTAGE.get(no_rev_partnumber, "")
    if not vmarg_percentage:
        result = vmarg_percentage
    if vmarg_percentage:
        # Normal MFG value
        result = vmarg_percentage[0]
        # EDVT valuse
        if RUNNING_EDVT:
            result = vmarg_percentage[1]

    return result

def get_mode_param(mtp_mgmt_ctrl, slot, test):
    """
    For NIC_ASIC L1 test parameter.
    """
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    if nic_type == NIC_Type.ORTANO2 and test in ("L1", "SEC_PROG_VERIFY"):
        if mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
            mode = "hod"
        else:
            mode = "hod_1100"
    elif nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADICR) and test in ("L1", "SEC_PROG_VERIFY"):
        mode = "hod"
    elif nic_type in (NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICRMSFT) and test in ("L1", "SEC_PROG_VERIFY"):
        mode = "hod_1100"
    elif nic_type == NIC_Type.ORTANO2INTERP:
        mode = "hod"
    elif nic_type == NIC_Type.ORTANO2SOLO:
        mode = "hod"
    elif nic_type == NIC_Type.ORTANO2SOLOORCTHS:
        mode = "hod"
    elif nic_type == NIC_Type.ORTANO2SOLOMSFT:
        mode = "hod_1100"
    elif nic_type == NIC_Type.ORTANO2SOLOS4:
        mode = "hod_1100"
    elif nic_type == NIC_Type.ORTANO2ADICRS4:
        mode = "hod_1100"
    elif nic_type == NIC_Type.POMONTEDELL:
        mode = "nod"
    elif nic_type == NIC_Type.LACONA32DELL or nic_type == NIC_Type.LACONA32:
        mode = "nod_550"
    elif nic_type in CAPRI_NIC_TYPE_LIST:
        mode = "hod"
    elif nic_type in GIGLIO_NIC_TYPE_LIST:
        mode = "hod_1100"
    else:
        mode = ""

    return mode

