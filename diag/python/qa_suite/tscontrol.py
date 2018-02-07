#!/usr/bin/env python

import pexpect
import re
import sys


def start_telnet(ip, usr, pwd):
    telnet_cmd = "telnet "+ip
    child = pexpect.spawn(telnet_cmd)
    child.logfile_read = sys.stdout
    child.expect("login: ")
    child.sendline(usr)
    child.expect("Password: ")
    child.sendline(pwd)
    child.expect("\# ")
    return child

def quit_telnet(child):
    child.sendline("exit")
    child.expect(pexpect.EOF)

def clear_line(child, line):
    child.sendline("config")
    child.expect(">>")
    cmd = "clear line "+str(line)
    child.sendline(cmd)
    child.expect(">>")
    child.sendline("exit")
    child.expect("\# ")
    
def change_speed(child, line, speed):
    child.sendline("config")
    child.expect(">>")
    cmd = "configure line "+str(line)+" speed "+str(speed)
    child.sendline(cmd)
    child.expect(">>")
    child.sendline("exit")
    child.expect("\# ")

if __name__ == "__main__":
    ip = "192.168.65.227"
    usr = "root"
    pwd = "tslinux"
    session = start_telnet(ip, usr, pwd)
    clear_line(session, 10)
    change_speed(session, 10, 9600)
    quit_telnet(session)

