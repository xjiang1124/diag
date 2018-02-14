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
    import argparse
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-on", "--on", action="store_true", help="Turn on APC port")
    group.add_argument("-off", "--off", action="store_true", help="Turn off APC port")
    parser.add_argument("-p", "--port", type=int, help="APC port number", default=0)
    args = parser.parse_args()

    filename="config/apcinfo.yaml"
    tsconfig = common.load_yaml(filename)

    tsinfo = tsconfig["pen-hwlab-apc-01"]
    ip = tsinfo["IP"]
    usr = tsinfo["USR"]
    pwd = tsinfo["PASSWD"]

    if args.port == 0:
        print "Invalid port number:", args.port
        sys.exit()

    if args.on == True:
        session = start_session(ip, usr, pwd)
        turn_port_on(session, args.port)
        quit_session(session)

    if args.off == True:
        session = start_session(ip, usr, pwd)
        turn_port_off(session, args.port)
        quit_session(session)

