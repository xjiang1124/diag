import getpass
import sys
import datetime
import re
import yaml
import os
import time


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


def count_down(seconds):
    secs = seconds
    while secs:
        sys.stdout.write("Time left: {:03d} seconds....\r".format(secs))
        sys.stdout.flush()
        time.sleep(1)
        secs -= 1


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
    tmp = str(datetime.datetime.now())[:19]
    tmp = tmp.replace(' ', '_')
    tmp = tmp.replace(':', '-')
    return tmp


def serial_number_validate(tmp):
    # please check the label specification
    # FL[M,Z,G][Year, like 18, 19, 20][Week: 00-52][4 hex sequential digits]
    if re.match("FL[M,Z,G]\d{2}[0-5]{1}\d{1}[0-9A-F]{4}", tmp) and (len(tmp) == 11):
        return tmp
    else:
        return None


def mac_address_validate(tmp):
    if re.match("00AECD[A-F0-9]+$", tmp) and (len(tmp) == 12):
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
