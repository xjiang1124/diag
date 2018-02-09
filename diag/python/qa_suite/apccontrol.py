#!/usr/bin/env python

import pexpect
import re
import sys

sys.path.append("../lib")
import common

def start_session(ip, usr, pwd):
    cmd = "ssh "+usr+"@"+ip
    child = pexpect.spawn(cmd)
    child.logfile_read = sys.stdout
    child.expect("password: ")
    child.sendline(pwd)
    child.expect("\# ")
    return child

def quit_session(child):
    child.sendline("exit")
    child.expect(pexpect.EOF)

def turn_port_on(child, port):
    cmd = "power outlets "+str(port)+" on"
    child.sendline(cmd)
    child.expect("\[y\/n\] ")
    child.sendline("y")
    child.expect("\# ")
    cmd = "show outlets "+str(port)
    child.sendline(cmd)
    child.expect("\# ")
 
def turn_port_off(child, port):
    cmd = "power outlets "+str(port)+" off"
    child.sendline(cmd)
    child.expect("\[y\/n\] ")
    child.sendline("y")
    child.expect("\# ")
    cmd = "show outlets "+str(port)
    child.sendline(cmd)
    child.expect("\# ")
  
if __name__ == "__main__":

    filename="config/apcinfo.yaml"
    tsconfig = common.load_yaml(filename)

    tsinfo = tsconfig["pen-hwlab-apc-01"]
    ip = tsinfo["IP"]
    usr = tsinfo["USR"]
    pwd = tsinfo["PASSWD"]

    #ip = "192.168.65.227"
    #usr = "root"
    #pwd = "tslinux"
    session = start_session(ip, usr, pwd)
    turn_port_on(session, 11)
    turn_port_off(session, 11)
    quit_session(session)

