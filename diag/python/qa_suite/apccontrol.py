#!/usr/bin/env python

import pexpect
import re
import sys
import time

sys.path.append("../lib")
import common

class apcControl:
    def __init__(self):
        filename="config/apcinfo.yaml"
        self.tsconfig = common.load_yaml(filename)
        self.ip = ""
        self.usr = ""
        self.pwd = ""

    def start_session(self):
        cmd = "ssh "+self.usr+"@"+self.ip
        child = pexpect.spawn(cmd)
        child.logfile_read = sys.stdout
        child.expect("password: ")
        child.sendline(self.pwd)
        child.expect("\# ")
        return child
    
    def quit_session(self, child):
        child.sendline("exit")
        child.expect(pexpect.EOF)
    
    def turn_port_on(self, child, port):
        cmd = "power outlets "+str(port)+" on"
        child.sendline(cmd)
        child.expect("\[y\/n\] ")
        child.sendline("y")
        child.expect("\# ")
        cmd = "show outlets "+str(port)
        child.sendline(cmd)
        child.expect("\# ")
     
    def turn_port_off(self, child, port):
        cmd = "power outlets "+str(port)+" off"
        child.sendline(cmd)
        child.expect("\[y\/n\] ")
        child.sendline("y")
        child.expect("\# ")
        cmd = "show outlets "+str(port)
        child.sendline(cmd)
        child.expect("\# ")
  
    def turn_off(self, apc, *ports):
        try:
            tsinfo = self.tsconfig[apc]
        except KeyError:
            print "Invalide APC name:", apc
            return
        else:
            self.ip = tsinfo["IP"]
            self.usr = tsinfo["USR"]
            self.pwd = tsinfo["PASSWD"]

        session = self.start_session()
        for port in ports:
            self.turn_port_off(session, port)
        self.quit_session(session)

    def turn_on(self, apc, *ports):
        try:
            tsinfo = self.tsconfig[apc]
        except KeyError:
            print "Invalide APC name:", apc
            return
        else:
            self.ip = tsinfo["IP"]
            self.usr = tsinfo["USR"]
            self.pwd = tsinfo["PASSWD"]

        session = self.start_session()
        for port in ports:
            self.turn_port_on(session, port)
            #time.sleep(5)
            
        self.quit_session(session)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-on", "--on", action="store_true", help="Turn on APC port")
    group.add_argument("-off", "--off", action="store_true", help="Turn off APC port")
    parser.add_argument("-p", "--port", type=int, help="APC port number", default=0)
    args = parser.parse_args()

    apc = apcControl()
    if args.on == True:
        apc.turn_on("pen-hwlab-apc-01", args.port)
        sys.exit()

    if args.off == True:
        apc.turn_off("pen-hwlab-apc-01", args.port)
        sys.exit()

    print "Invalid parameter"

