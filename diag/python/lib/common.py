#!/usr/bin/env python

import datetime
import errno
import os
import pexpect
import sys
import time
import yaml
from collections import OrderedDict
import threading


PY3 = (sys.version_info[0] >= 3)
encoding = "utf-8" if PY3 else None

#=========================================================
# To load yaml file in order
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

def load_yaml(filename):
    with open(filename) as stream:
        try:
            #config_dict = yaml.load(stream)
            config = ordered_load(stream, yaml.SafeLoader)
        except yaml.YAMLError as exc:
            print(exc)
    return config

#=========================================================
# create output folder
def create_folder(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

#=========================================================
# Constant class
class Const():
    def __init__(self):
        self.BASH_PROMPP = "\$ "
        self.PWD_PROMPT = ": "
        self.SUDO_PW = "lab123"
        self.RET_VAL = "echo $?"
        self.EXI = "exit"
        self.DIAG_USR = "diag"
        self.DIAG_PW = "lab123"
        self.EOF = pexpect.EOF

# Constant
def constant(f):
    def fset(self, value):
        raise TypeError
    def fget(self):
        return f()
    return property(fget, fset)

class _Const(object):
    @constant
    def BASH_PROMPT():
        return "\$ "
    def PWD_PROMPT():
        return ": "
    def SUDO_PWD():
        return "lab123"
    def RET_VAL():
        return "echo $?"
    def EXIT():
        return "exit"
    def EOF():
        return pexpect.EOF

CONST = _Const()

pwd_prompt = "password: "
bash_prompt = "\$"
#bash_prompt = r"$ "
sudo_pwd = "lab123"

#=============================
# Pexpect functions
def runcmd(cmd, timeout=30, sudo=False):
    if sudo == True:
        cmd = "sudo "+cmd
        expstr = [CONST.PWD_PROMPT, CONST.EOF]
    else:
        expstr = CONST.EOF

    try:
        session = pexpect.spawn(cmd, timeout=timeout, encoding=encoding, codec_errors='ignore')
        session.logfile_read = sys.stdout
        i = session.expect(expstr, timeout=timeout)
        if sudo == True:
            if i == 0:
                session.sendline(CONST.SUDO_PWD)
                session.expect(pexpect.EOF, timeout=timeout)
    except pexpect.TIMEOUT:
        print("=== TIMEOUT:", cmd, "===")
        return -1
    return 0

#=============================
# Run command with provided session and get return value
def run_cmd(cmd, timeout=30, sudo=False):
    if sudo == True:
        cmd = "sudo "+cmd
    expstr = [pwd_prompt, bash_prompt]
    try:
        session = pexpect.spawn(cmd, encoding=encoding, codec_errors='ignore')
        session.logfile_read = sys.stdout
        session.timeout = timeout
        i = session.expect(expstr)

        if i == 0:
            session.sendline(sudo_pwd)
            session.expect(pexpect.EOF)
        return 0

    except pexpect.TIMEOUT:
        print("=== TIMEOUT:", cmd, "===")
        session.close()
        return -2

#=============================
# Run command with provided session and get return value
def bash_cmd(cmd, timeout=30, sudo=False):
    if sudo == True:
        cmd = "sudo "+cmd
    expstr = [pwd_prompt, bash_prompt]
    try:
        session = pexpect.spawn("bash", encoding=encoding, codec_errors='ignore')
        session.expect(bash_prompt)
        session.logfile_read = sys.stdout
        session.timeout = timeout

        session.sendline(cmd)
        i = session.expect(expstr)
        if i == 0:
            session.sendline(sudo_pwd)
            session.expect(bash_prompt)
        session.sendline("echo $?")
        session.expect(bash_prompt)
        if session.before == "0":
            retval = 0
        else:
            retval = -1
        session.sendline("exit")
        session.expect(pexpect.EOF)
        session.close()
        return retval

    except pexpect.TIMEOUT:
        print("=== TIMEOUT:", cmd, "===")
        session.close()
        return -2




    #=============================
# Run command with provided session 
def session_cmd_no_rc(session, cmd, timeout=30, sudo=False, ending=bash_prompt):
    session.timeout = timeout
    expstr = [pwd_prompt, ending]
    if sudo == True:
        cmd = "sudo "+cmd
        expstr = ["password for diag: "] + expstr
    try:
        session.sendline(cmd)
        time.sleep(0.05)
        i = session.expect(expstr)
        #print session.before
        if i < (len(expstr) - 1):
            session.sendline(sudo_pwd)
            time.sleep(0.1)
            session.expect(bash_prompt)
            return 0

    except pexpect.TIMEOUT:
        print("=== TIMEOUT:", cmd, "===")
        # Send CTRL+C
        session.send(chr(3))
        time.sleep(0.05)
        session.expect(bash_prompt)
        return -2

##=============================
# Run command with provided session and get return value
def session_cmd(session, cmd, timeout=30, sudo=False, ending=bash_prompt):
    session.timeout = timeout
    if type(ending) is str:
        expstr = [pwd_prompt, ending]
    elif type(ending) is list:
        expstr = [pwd_prompt] + ending
    else:
        expstr = [pwd_prompt, ending]

    if sudo == True:
        cmd = "sudo "+cmd
        expstr = expstr + ["password for diag: "]
    try:
        session.sendline(cmd)
        time.sleep(0.05)
        i = session.expect(expstr)
        #print session.before
        if i == (len(expstr) - 1) and sudo == True:
            session.sendline(sudo_pwd)
            time.sleep(0.1)
            session.expect(bash_prompt)
            #print session.before
        #session.sendline("echo $?")
        #time.sleep(0.05)
        #session.expect(bash_prompt)
        #if session.before == "0":
        #    return i
        #else:
        #    return -1
        return i

    except pexpect.TIMEOUT:
        print("=== TIMEOUT:", cmd, "===")
        # Send CTRL+C
        session.send(chr(3))
        time.sleep(0.05)
        session.expect(bash_prompt)
        return -2

#=============================
# Run command with provided session and get return value, return with output
def session_cmd_w_ot(session, cmd, timeout=30, sudo=False, ending=bash_prompt):
    session.timeout = timeout
    expstr = [pwd_prompt, ending]
    output = ""
    if sudo == True:
        cmd = "sudo "+cmd
        expstr = expstr + ["password for diag: "] 
    try:
        session.sendline(cmd)
        time.sleep(0.05)
        i = session.expect(expstr)
        output = session.before
        #print session.before
        if i ==len(expstr) and sudo == True:
            session.sendline(sudo_pwd)
            time.sleep(0.1)
            j = session.expect(bash_prompt)
        return [0, output]

    except pexpect.TIMEOUT:
        print("=== TIMEOUT:", cmd, "===")
        # Send CTRL+C
        session.send(chr(3))
        time.sleep(0.05)
        session.expect(bash_prompt)
        return [-2, output]

#=============================
# Run command with provided session and get return value
def session_cmd_pass(session, cmd, pass_sign="", timeout=30, ending=bash_prompt, sudo=False):
    session.timeout = timeout
    expstr = [pwd_prompt, ending]
    if sudo == True:
        cmd = "sudo "+cmd
        expstr = ["password for diag: "] + expstr
    try:
        session.sendline(cmd)
        time.sleep(0.05)
        i = session.expect(expstr)
        #print session.before
        if i < (len(expstr) - 1):
            session.sendline(sudo_pwd)
            time.sleep(0.1)
            session.expect(bash_prompt)
            #print session.before
        if pass_sign in session.before:
            return 0
        else:
            return -1
    except pexpect.TIMEOUT:
        print("=== TIMEOUT:", cmd, "===")
        # Send CTRL+C
        session.send(chr(3))
        time.sleep(0.05)
        session.expect(bash_prompt)
        return -2

#=============================
# Run command with provided session and get return value
def session_cmd_pass_multi(session, cmd, pass_sign_list=["NO PASS SIGN"], timeout=30, ending=bash_prompt, sudo=False):
    session.timeout = timeout
    expstr = [pwd_prompt, ending]
    if sudo == True:
        cmd = "sudo "+cmd
        expstr = ["password for diag: "] + expstr
    try:
        session.sendline(cmd)
        time.sleep(0.05)
        i = session.expect(expstr)
        #print session.before
        if i < (len(expstr) - 1):
            session.sendline(sudo_pwd)
            time.sleep(0.1)
            session.expect(bash_prompt)
            #print session.before
        
        for pass_sign in pass_sign_list:
            if pass_sign in session.before:
                return 0
        return -1

    except pexpect.TIMEOUT:
        print("=== TIMEOUT:", cmd, "===")
        # Send CTRL+C
        session.send(chr(3))
        time.sleep(0.05)
        session.expect(bash_prompt)
        return -2

#=============================
def session_cmd_exp_multi(session, cmd, exp_list=["NO PASS SIGN"], timeout=30, ending=bash_prompt):
    session.timeout = timeout
    try:
        session.sendline(cmd)
        i = session.expect(exp_list)
        return i

    except pexpect.TIMEOUT:
        print("=== TIMEOUT: ", cmd, " ===")
        return -1

#=============================
# Start bash session
def session_start(timeout=30):
    print("Encoding:", encoding)
    try:
        session = pexpect.spawn("bash", timeout=timeout, ignore_sighup=False, encoding=encoding, codec_errors='ignore')
        #session = pexpect.spawn("bash", timeout=timeout, ignore_sighup=False)
        session.logfile_read = sys.stdout
        session.expect(bash_prompt) 
        return session
    except pexpect.TIMEOUT:
        print("=== Faled to spawn bash session ===")
        return None

#=============================
# Run bash command and get return value
def session_stop(session, timeout=30):
    session.timeout = timeout
    try:
        session.sendline("exit")
        session.expect(pexpect.EOF) 
        return 0
    except pexpect.TIMEOUT:
        print("=== Faled to stop bash session ===")
        return -1

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

#=============================
# untar
def untar(fname):
    if (fname.endswith("tar.gz")):
        tar = tarfile.open(fname, "r:gz")
        tar.extractall()
        tar.close()
    elif (fname.endswith("tar")):
        tar = tarfile.open(fname, "r:")
        tar.extractall()
        tar.close()

#=============================
def find_file(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    if result == []:
        print("Can not find file!", pattern, path)
    return result

#=============================
def find_dir(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            if fnmatch.fnmatch(dir_name, pattern):
                result.append(os.path.join(root, dir_name))
    if result == []:
        print("Can not find file!", pattern, path)

    return result

#=============================
def find_first_dir(path):
    result = []
    for root, dirs, files in os.walk(path):
        #print path, root, dirs
        for dir_name in dirs:
            result.append(os.path.join(root, dir_name))

    if result == []:
        print("Can not find file!", path)

    return result

#====================
def split_into_threads(func):
    def single_thread_func(func, slot, thread_rslt_list, *test_args, **test_kwargs):
        try:
            ret = func(slot, *test_args, **test_kwargs)
            if ret != 0:
                thread_rslt_list[int(slot) - 1] = False
        except Exception:
            thread_rslt_list[int(slot) - 1] = False

    def wrapper(nic_list, *test_args, **test_kwargs):
        nic_thread_list = list()
        fail_nic_list = list()
        thread_rslt_list = [True] * 10
        for slot in nic_list:
            thread_args = tuple([func, slot, thread_rslt_list]) + test_args
            nic_thread = threading.Thread(
                target = single_thread_func,
                args = thread_args,
                kwargs = test_kwargs
            )
            nic_thread.daemon = True
            nic_thread.start()
            nic_thread_list.append(nic_thread)
            time.sleep(1)

        # monitor all the thread
        while True:
            if len(nic_thread_list) == 0:
                break
            for nic_thread in nic_thread_list[:]:
                if not nic_thread.is_alive():
                    nic_thread.join()
                    nic_thread_list.remove(nic_thread)
            time.sleep(1)
        for idx, slot_rslt in enumerate(thread_rslt_list):
            if not slot_rslt:
                fail_nic_list.append(idx + 1)
        return fail_nic_list

    return wrapper

#=============================
# ssh
def ssh_login(session, ip, usr, passwd):
    ret = 0
    try:
        session.sendline("ssh "+usr+ "@"+ip)
        session.expect("password:")
        session.sendline(passwd)
        session.expect("\$")
    except pexpect.TIMEOUT:
        print("Failed to ssh to " + ip)
        ret = -1

    return ret

#=============================
def ssh_exit(session):
    ret = 0
    try:
        session.sendline("exit")
        session.expect("\$")
    except pexpect.TIMEOUT:
        print("Failed to exit ssh")
        ret = -1

    return ret

#=============================
def switch_to_sudo(session, sudo_passwd, ending=bash_prompt, timeout=30):
    ret = 0

    session.timeout = timeout
    if type(ending) is str:
        expstr = [pwd_prompt, ending]
    elif type(ending) is list:
        expstr = [pwd_prompt] + ending
    else:
        expstr = [pwd_prompt, ending]

    expstr = ["password for diag: "] + expstr
    try:
        session.sendline("sudo su")
        i = session.expect(expstr)
        if i == 0:
            session.sendline(sudo_passwd)
            session.expect(expstr)

    except pexpect.TIMEOUT:
        print("=== TIMEOUT: sudo su ===")
        ret = -1

    return ret


