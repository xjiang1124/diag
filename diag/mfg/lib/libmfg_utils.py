import getpass
import smtplib
import httplib
import sys
import datetime
import re
import oyaml as yaml
import os
import time
import pexpect
import glob

from libdefs import MTP_Const
from libdefs import FF_Stage
from libdefs import FPN_FF_Stage
from libdefs import MTP_DIAG_Path
from libdefs import MTP_DIAG_Logfile
from libdefs import MTP_DIAG_Report
from libdefs import FLX_Factory
from libdefs import MFG_DIAG_CMDS
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
    return re.sub(r"[\x00-\x09,\x0B-\x0C,\x0E-\x1F]", "", buf)


def serial_number_validate(tmp):
    if re.match(NAPLES_SN_FMT, tmp) and (len(tmp) == 11):
        return tmp
    elif re.match(HP_SN_FMT, tmp) and (len(tmp) == 10):
        return tmp
    else:
        return None


def mac_address_validate(tmp):
    if re.match(NAPLES_MAC_FMT, tmp) and (len(tmp) == 12):
        return tmp
    else:
        return None


def part_number_validate(tmp):
    if re.match(NAPLES_PN_FMT, tmp) and (len(tmp) == 13 or len(tmp) == 12):
        return tmp
    if re.match(HP_PN_FMT, tmp) and (len(tmp) == 10):
        return tmp
    else:
        return None


def mac_address_format(tmp):
    return "-".join(re.findall("..", tmp))


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


def mtp_init_test_script(mtp_mgmt_ctrl, mtp_script_dir, mtp_script_pkg, extra_script=None):
    if extra_script:
        cmd = "cp {:s} {:s}".format(extra_script, mtp_script_dir)
        os.system(cmd)
    cmd = "cp -r lib/ config/ {:s}".format(mtp_script_dir)
    os.system(cmd)
    cmd = "tar czf {:s} {:s}".format(mtp_script_pkg, mtp_script_dir)
    os.system(cmd)
    # remove the lib config for the next run
    if extra_script:
        cmd = "rm -f {:s}/{:s}".format(mtp_script_dir, os.path.basename(extra_script))
        os.system(cmd)
    cmd = "rm -rf {:s}/lib {:s}/config".format(mtp_script_dir, mtp_script_dir)
    os.system(cmd)

    mtp_mgmt_cfg = mtp_mgmt_ctrl.get_mgmt_cfg()
    ipaddr = mtp_mgmt_cfg[0]
    userid = mtp_mgmt_cfg[1]
    passwd = mtp_mgmt_cfg[2]
    # download the test script pkg
    if not network_copy_file(ipaddr, userid, passwd, mtp_script_pkg, MTP_DIAG_Path.ONBOARD_MTP_DIAG_PATH):
        mtp_mgmt_ctrl.cli_log_err("Copy Test script failed... Abort")
        return False
    # remove the stale test script
    cmd = "rm -rf {:s}".format(mtp_script_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False
    # unpack the test script pkg
    cmd = "tar zxf {:s}".format(mtp_script_pkg)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute {:s} on MTP Chassis".format(cmd), level=0)
        return False
    # remove the test script pkg
    cmd = "rm -f {:s}".format(mtp_script_pkg)
    os.system(cmd)
    return True


def mtpid_list_select(mtp_cfg_db):
    mtpid_list = list(mtp_cfg_db.get_mtpid_list())
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

    for image in image_list:
        if image not in image_on_mtp:
            image_rel_path = "release/{:s}".format(image)
            if not file_exist(image_rel_path):
                mtp_mgmt_ctrl.cli_log_err("Firmware image {:s} doesn't exist... Abort".format(image_rel_path), level=0)
                return False

            mtp_mgmt_ctrl.cli_log_inf("Copy Firmware image {:s}".format(image), level=0)
            if not network_copy_file(mtp_ip_addr, mtp_usrid, mtp_passwd, image_rel_path, image_dir):
                mtp_mgmt_ctrl.cli_log_err("Copy Firmware image {:s} failed... Abort".format(image), level=0)
                return False
            mtp_mgmt_ctrl.cli_log_inf("Copy Firmware image {:s} complete".format(image), level=0)
        else:
            mtp_mgmt_ctrl.cli_log_inf("Firmware image {:s} on MTP is up-to-date".format(image), level=0)

    return True


def mtp_update_diag_image(mtp_mgmt_ctrl, mtp_image, nic_image, image_on_mtp):
    if mtp_image in image_on_mtp and nic_image in image_on_mtp:
        mtp_mgmt_ctrl.cli_log_inf("Diag images on MTP is up-to-date", level=0)
        return True

    # cleanup the stale diag images
    cmd = "rm -f /home/diag/image_a*.tar"
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
    remote_dir = "/home/diag/"

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
        test_log_file = "{:s}test_dl.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_test_dl.log".format(mtp_id)
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
        test_log_file = "{:s}test_swi.log".format(log_dir+sub_dir)
        # local copy of summary logfile
        local_test_log_file = "log/{:s}_test_swi.log".format(mtp_id)
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

    # temperary dir for log files
    cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(log_dir+sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None
    # move onboard log files
    cmd = "mv {:s} {:s}".format(test_onboard_log_files, log_dir+sub_dir)
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

    # for P2C/4C test, extra logfiles are needed
    if stage == FF_Stage.FF_P2C:
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
    elif stage == FF_Stage.FF_4C_H or stage == FF_Stage.FF_4C_L:
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
    # for DL/SWI/FST, no extra logfiles
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
    upload_csp = False
    csp_log_dir = None
    for slot, nic_type, sn in fail_match + pass_match:
        # report doesn't have valid serial number
        if nic_type:
            temp_nic_type = nic_type
        if sn == "None":
            continue
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
        elif stage == FF_Stage.FF_SWI:
            upload_csp = True
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

        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(mfg_log_dir)
        os.system(cmd)
        cmd = MFG_DIAG_CMDS.MFG_MK_DIR_FMT.format(csp_log_dir)
        os.system(cmd)
        # copy the onboard logs only once
        if log_hard_copy_flag:
            qa_log_pkg_file = mfg_log_dir + os.path.basename(log_pkg_file)
            mtp_mgmt_ctrl.cli_log_inf("[{:s}] Collecting log file {:s}".format(sn, qa_log_pkg_file))
            if not network_get_file(ipaddr, userid, passwd, qa_log_pkg_file, log_pkg_file):
                mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file {:}".format(log_pkg_file), level=0)
                continue

            # It is fine to do hard copy
            #log_hard_copy_flag = False
            # relative link is ../sn/log_pkg_file
            log_relative_link = "../{:s}/{:s}".format(sn, os.path.basename(log_pkg_file))
        # create hard link
        else:
            mtp_mgmt_ctrl.cli_log_inf("[{:s}] Create link log file {:s}".format(sn, log_relative_link))
            chdir_cmd = "cd {:s}".format(mfg_log_dir)
            ln_cmd = MFG_DIAG_CMDS.MFG_LOG_LINK_FMT.format(log_relative_link, os.path.basename(log_pkg_file))
            cmd = "{:s} && {:s}".format(chdir_cmd, ln_cmd)
            os.system(cmd)
        
    if upload_csp:
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
            mtp_mgmt_ctrl.cli_log_inf("Collecting csp log file {:s}".format(os.path.basename(cspfilepath)))
            csp_log_file = csp_log_dir + os.path.basename(cspfilepath)
            if not network_get_file(ipaddr, userid, passwd, csp_log_file, cspfilepath):
                mtp_mgmt_ctrl.cli_log_err("Unable to copy MTP test log file {:}".format(cspfilepath), level=0)
                continue

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
    if not mtp_mgmt_ctrl.mtp_mgmt_exec_cmd(cmd):
        mtp_mgmt_ctrl.cli_log_err("Unable to execute command {:s} on MTP".format(cmd), level=0)
        return None

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
    cli_inf("##########  MFG {:s} Test Summary  ##########".format(stage))
    for mtp_id in summary_dict.keys():
        cli_inf("---------- {:s} Report: ----------".format(mtp_id))
        for slot, sn, nic_type, rc in summary_dict[mtp_id]:
            nic_cli_id_str = id_str(mtp=mtp_id, nic=int(slot), base=0)
            if rc:
                cli_inf("{:s} {:s} {:s} PASS".format(nic_cli_id_str, sn, nic_type))
            else:
                cli_err("{:s} {:s} {:s} FAIL".format(nic_cli_id_str, sn, nic_type))
        cli_inf("--------- {:s} Report End --------\n".format(mtp_id))
    for mtp_id in mtp_fail_list:
        cli_err("-------- {:s} Test Aborted -------\n".format(mtp_id))
