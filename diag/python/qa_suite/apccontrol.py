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

    def turn_off(self, apcName, *ports):
        try:
            tsinfo = self.tsconfig[apcName]
        except KeyError:
            print "Invalide APC name:", apc
            return

        model = tsinfo["MODEL"]
        if model == "RARITAN":
            apc = apcControlRar()
        elif model == "SCHNEIDER":
            apc = apcControlSch()
        else:
            print "invalid APC model:", model
            return

        apc.turn_off(apcName, ports)

    def turn_on(self, apcName, *ports):
        try:
            tsinfo = self.tsconfig[apcName]
        except KeyError:
            print "Invalide APC name:", apcName
            return

        model = tsinfo["MODEL"]
        if model == "RARITAN":
            apc = apcControlRar()
        elif model == "SCHNEIDER":
            apc = apcControlSch()
        else:
            print "invalid APC model:", model
            return

        apc.turn_on(apcName, ports)


class apcControlRar:
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
    
    def turn_port_on(self, child, ports):
        aports = ports[0]
        cmd = "power outlets "+aports+" on"
        child.sendline(cmd)
        child.expect("\[y\/n\] ")
        child.sendline("y")
        child.expect("\# ")
        cmd = "show outlets "+aports
        child.sendline(cmd)
        child.expect("\# ")
     
    def turn_port_off(self, child, ports):
        aports = ports[0]
        cmd = "power outlets "+aports+" off"
        child.sendline(cmd)
        child.expect("\[y\/n\] ")
        child.sendline("y")
        child.expect("\# ")
        cmd = "show outlets "+aports
        child.sendline(cmd)
        child.expect("\# ")
  
    def turn_off(self, apcName, ports):
        try:
            tsinfo = self.tsconfig[apcName]
        except KeyError:
            print "Invalide APC name:", apcName
            return
        else:
            self.ip = tsinfo["IP"]
            self.usr = tsinfo["USR"]
            self.pwd = tsinfo["PASSWD"]

        session = self.start_session()
        for port in ports:
            self.turn_port_off(session, port)
        self.quit_session(session)

    def turn_on(self, apcName, *ports):
        try:
            tsinfo = self.tsconfig[apcName]
        except KeyError:
            print "Invalide APC name:", apcName
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

#=============================
#
# Schneider APC control
#
#=============================
class apcControlSch:
    def __init__(self):
        filename="config/apcinfo.yaml"
        self.tsconfig = common.load_yaml(filename)
        self.ip = ""
        self.usr = ""
        self.pwd = ""

    def start_session(self):
        cmd = "telnet "+self.ip
        child = pexpect.spawn(cmd)
        child.logfile_read = sys.stdout

        usrpmt = "User Name : "
        pwdpmt = "Password  : "
        apcpmt = "apc>"
        pmt = [usrpmt, pwdpmt, apcpmt]
        maxwait = 10
        trycount = 0
        
        child = pexpect.spawn(cmd)
        child.logfile_read = sys.stdout
        while True:
            #print "Log in No.", trycount
            i = child.expect(pmt)
            if i == 0:
                child.send(self.usr+"\r")
            elif i == 1:
                child.send(self.pwd+"\r")
            else:
                break
            trycount = trycount + 1
            if trycount >= maxwait:
                print "Max try reached, quit session", trycount
                child.close()
                sys.exit()

        return child
    
    def quit_session(self, child):
        child.sendline("exit")
        child.expect(pexpect.EOF)
    
    def turn_port_on(self, child, ports):
        aports = ports[0]
        cmd = "olon "+aports
        child.sendline(cmd)
        child.expect("apc>")
        cmd = "olstatus "+aports
        child.sendline(cmd)
        child.expect("apc>")
     
    def turn_port_off(self, child, ports):
        aports = ports[0]
        cmd = "oloff "+aports
        child.sendline(cmd)
        child.expect("apc>")
        cmd = "olstatus "+aports
        child.sendline(cmd)
        child.expect("apc>")
  
    def turn_off(self, apc, ports):
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
        self.turn_port_off(session, ports)
        self.quit_session(session)

    def turn_on(self, apc, ports):
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
        self.turn_port_on(session, ports)
        self.quit_session(session)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-on",  "--on", action="store_true", help="Turn on APC port")
    group.add_argument("-off", "--off", action="store_true", help="Turn off APC port")
    parser.add_argument("-p",  "--port", type=str, help="APC port number", default="99")
    parser.add_argument("-apc", "--apc", type=str, help="APC Name", default="")
    args = parser.parse_args()

    if args.apc == "":
        print "Please give APC name!"
        sys.exit()

    apcCtrl = apcControl()
    if args.on == True:
        apcCtrl.turn_on(args.apc, args.port)
        sys.exit()

    if args.off == True:
        apcCtrl.turn_off(args.apc, args.port)
        sys.exit()

    print "Invalid parameter"

