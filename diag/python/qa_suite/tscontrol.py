#!/usr/bin/env python

import argparse
import pexpect
import re
import sys
import time

sys.path.append("../lib")
import common
from common import Const

prompt_login = "MTP login: "
prompt_pwd = "Password: "
prompt_bash = "diag@MTP:~\$ "

class tsControlBase(Const):
    def __init__(self):
        filename="config/tsinfo.yaml"
        self.tsconfig = common.load_yaml(filename)
        filename = "config/chassis_info.yaml"
        self.csconfig = common.load_yaml(filename)

        self.tsName = ""
        self.tsIp = ""
        self.tsUsr = ""
        self.tsPwd = ""
        self.tsPort = ""
        self.tsModel = ""

        Const.__init__(self)

    def telnet_start(self, timeout=30):
        #expstr = [prompt_login, prompt_pwd, prompt_bash]
        expstr = [prompt_login, prompt_pwd, "\$ "]
        session = common.session_start()
        try:
            cmd = "telnet "+self.tsIp+" "+str(self.tsPort)
            session.sendline(cmd)
            session.expect("'\.")
            session.send("\r")
            i = session.expect(expstr, timeout)
            if i == 0:
                session.sendline(self.DIAG_USR)
                session.expect(prompt_pwd)
                session.sendline("lab123")
                session.expect(prompt_bash)
            elif i == 2:
                # Need second expect to deal with double \$ case
                session.expect("\$ ")
                pass
            else:
                print "Wrong prompt", i
        except pexpect.TIMEOUT:
            print "Failed to log in to telnet"
            sys.exit()

        #print "Telnet session established"
        return session

    def telnet_stop(self, session):
        session.sendcontrol(']')
        session.expect("telnet> ")
        session.sendline('q')
        session.expect("\$ ")
        common.session_stop(session)

    def findIp(self, pf):
        self.setup(pf)

        session = self.telnet_start(self.tsPort)
        session.sendline("ifconfig")
        session.expect("\$ ")

        # Find IP
        buf = session.before
        buf = repr(buf).replace("\\r\\n", " ").replace("\'", "")
        # There is another one for local host
        buf = buf.replace("inet addr:127.0.0.1", "iinneett addr:127.0.0.1")
        pat = re.compile(r"^.*inet addr:(\d+\.\d+\.\d+\.\d+).*") 
        m = pat.match(buf)
        if m:
            result = m.group(1)
        else:
            result = "ip_not_found"

        self.telnet_stop(session)
        return result

    def setup(self, pf):
        try:
            self.tsName = self.csconfig[pf]["TS"]
            ts = self.tsconfig[self.tsName]
        except KeyError:
            print "Wrong TS name:", tsName
            sys.exit()
        self.tsIp = ts["IP"]
        self.tsUsr = ts["USR"]
        self.tsPwd = ts["PASSWD"]
        self.tsPort = self.csconfig[pf]["TS_PORT"]
        self.tsModel = ts["MODEL"]

    def wait4rdyTel(self, pf, timeout=300):
        self.setup(pf)
        expstr = "MTP login:"
        session = common.session_start()
        try:
            cmd = "telnet "+self.tsIp+" "+str(self.tsPort)
            session.sendline(cmd)
            session.expect(expstr, timeout)
            self.telnet_stop(session)
        except pexpect.TIMEOUT:
            print "Failed to wait for system ready from telnet!"
            return -1
        return 0

class ts3000Control(tsControlBase):
    def __init__(self):
        tsControlBase.__init__(self)

    def telnet_ts_start(self, ip, usr, pwd):
        telnet_cmd = "telnet "+ip
        child = pexpect.spawn(telnet_cmd)
        child.logfile_read = sys.stdout
        child.expect("login: ")
        child.sendline(usr)
        child.expect("Password: ")
        child.sendline(pwd)
        child.expect("\# ")
        return child
    
    def telnet_ts_quit(self, child):
        child.sendline("exit")
        child.expect(pexpect.EOF)
    
    def clear_line(self, session, line):
        session = self.telnet_ts_start(self.ip, self.usr, self.pwd)
        session.sendline("config")
        session.expect(">>")
        cmd = "clear line "+str(line)
        session.sendline(cmd)
        session.expect(">>")
        session.sendline("exit")
        session.expect("\# ")
        
    def change_speed(self, child, line, speed):
        child.sendline("config")
        child.expect(">>")
        cmd = "configure line "+str(line)+" speed "+str(speed)
        child.sendline(cmd)
        child.expect(">>")
        child.sendline("exit")
        child.expect("\# ")

class tsControl(tsControlBase):
    def __init(self):
        tsControlBase.__init__(self)

    def findIp(self, pf):
        self.setup(pf)
        if self.tsModel == "TS3000":
            tscontrol = ts3000Control()
        else:
            ip = "ip_not_found"
            return ip
        ip = tscontrol.findIp(pf)
        return ip



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Console control", formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("-pf", "--platform", help="Platform, e.g. MTP001", type=str, default='')
    group.add_argument("-ip", "--ip", help="Find IP address", action='store_true')
    group.add_argument("-cl", "--cl", help="Clear line", action='store_true')
    args = parser.parse_args()

    pf = args.platform.upper()

    tscontrol = tsControl()
    if args.ip == True:
        ip = tscontrol.findIp(pf)
        print "ip:", ip
        sys.exit()

    print "Invalid Parameter"

