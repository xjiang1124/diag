#!/usr/bin/env python

import argparse
import pexpect
import sys
import time
import os

sys.path.append("../lib")
import common

class ts_control:
    def __init__(self):
        self.usr = "admin"
        self.passwd = "N0isystem$"
        self.encoding = common.encoding
        self.type = "Type I"

    def connect(self, ip, passwd):
        try:
            session=pexpect.spawn("bash", encoding=self.encoding, codec_errors='ignore')
            session.logfile_read = sys.stdout
            session.timeout=10
            
            session.sendline("telnet " + ip)
            idx = session.expect(["Password: ", "Username: "])

            if idx == 0:
                self.type = "Type I"
                session.sendline(passwd)
                session.expect(r".*#$")
            else:
                self.type = "Type II"
                session.sendline(self.usr)
                session.expect("Password: ")
                session.sendline(self.passwd)
                session.expect("Router>")
                session.sendline("enable")
                session.expect("Password: ")
                session.sendline(self.passwd)
                session.expect("Router#")
            return 0, session

        except pexpect.TIMEOUT:
            print("Timeout exceeded during connection.")
        except pexpect.EOF:
            print("End of file reached during connection.")
        except Exception as e:
            print("Error during connection: {}".format(e))

        return -1, None

    # clear current line in console
    def clearline(self, args):
        print(args)
        if args.retry < 1:
            print("Number of retry is less than 1")
            return

        status, session = self.connect(args.ip, args.passwd)

        if status == -1:
            return

        try:
            for i in range(args.retry):
                session.sendline("clear line {}".format(args.port))
                index = session.expect("\[confirm\]")
                session.sendline("")
                session.expect(" \[OK\]")
                session.sendline("")
                session.expect(r".*#$")

        except pexpect.TIMEOUT:
            print("Timeout exceeded while clearing lines.")
        except pexpect.EOF:
            print("End of file reached while clearing lines.")
        except Exception as e:
            print("Error while clearing lines: {}".format(e))

    def connect_ts_port(self, session, ip, port, exp_str):
        ret = 0
        try:
            session.sendline("telnet " + ip + " " + port)
            session.expect("Escape character is")
            time.sleep(1)
            #session.sendline('')
            session.sendline('help')
            #session.expect("uart:")
            session.expect(exp_str)
        except pexpect.TIMEOUT:
            print("telnet connect failed")
            ret = -1
        return ret

    def disconnect_ts_port(self, session, exp_str):
        ret = 0
        try:
            session.sendline(chr(29))
            session.expect("telnet>")
            session.sendline("q")
            session.expect(exp_str)
        except pexpect.TIMEOUT:
            print("telnet disconnect failed")
            ret = -1
        return ret

if __name__ == "__main__":

    ts_ctrl = ts_control()

    parser = argparse.ArgumentParser(description="A script to clear lines in a telnet session")

    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    subparser = parser.add_subparsers(dest='command', help='Subcommands')

    # 'clearline' subcommand
    parser_clearline = subparser.add_parser('clearline', help='Clear the current line in the console')

    parser_clearline.add_argument('-ip', '--ip', default='10.9.6.192', help='Console server IP address')
    parser_clearline.add_argument('-passwd', '--passwd', default='N0isystem$', help='Password of console server')
    parser_clearline.add_argument('-p', '--port', type=str,  default="1",  help='Port number to clear')
    parser_clearline.add_argument('-r', '--retry', type=int, default=3, help='Number of times to clear the line')
    parser_clearline.set_defaults(func=ts_ctrl.clearline)

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)

    sys.exit(not args.func(args))
