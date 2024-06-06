#!/usr/bin/env python

import argparse
import pexpect
import sys
import os

class ts_control:

    def connect(self, ip, pwd):
        try:
            PY3 = (sys.version_info[0] >= 3)
            encoding = "utf-8" if PY3 else None
            session=pexpect.spawn("bash", encoding=encoding, codec_errors='ignore')
            session.logfile_read = sys.stdout
            session.timeout=10
            
            session.sendline("telnet " + ip)
            session.expect("Password: ")

            session.sendline(pwd)
            session.expect(r".*#$")

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

        status, session = self.connect(args.ip, args.pwd)

        if status == -1:
            return

        try:
            for i in range(args.retry):
                session.sendline("clear line {}".format(args.line_num))
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


if __name__ == "__main__":

    ts_ctrl = ts_control()

    parser = argparse.ArgumentParser(description="A script to clear lines in a telnet session")

    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    subparser = parser.add_subparsers(dest='command', help='Subcommands')

    # 'clearline' subcommand
    parser_clearline = subparser.add_parser('clearline', help='Clear the current line in the console')

    parser_clearline.add_argument('-ip', '--ip', default='10.9.6.192', help='Console server IP address')
    parser_clearline.add_argument('-pwd', '--pwd', default='N0isystem$', help='Password of console server')
    parser_clearline.add_argument('-l', '--line_num', type=int,  default=1,  help='Line number to clear')
    parser_clearline.add_argument('-r', '--retry', type=int, default=2, help='Number of times to clear the line')
    parser_clearline.set_defaults(func=ts_ctrl.clearline)


    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(1)

    sys.exit(not args.func(args))
