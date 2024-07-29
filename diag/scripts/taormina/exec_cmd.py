#!/usr/bin/env python

import argparse
import pexpect
import sys
import os
import io
import subprocess

class exec_commands:


    def run(self, args):
        print(args)

        try:
            PY3 = (sys.version_info[0] >= 3)
            encoding = "utf-8" if PY3 else None
            session=pexpect.spawn("bash", encoding=encoding, codec_errors='ignore')
            session.logfile_read = sys.stdout
            session.timeout=10
                
            index = session.expect("10000:")

            # initial setup
            if args.port == 0:
                session.sendline("i2cset -y -a 3 1 1 2")
            elif args.port == 1: 
                session.sendline("i2cset -y -a 3 1 1 3")
            else:
                raise ValueError("Invalid port number: {}".format(args.port))
            
            session.expect("10000:")
            session.sendline("i2cset -y 3 0x4a 0x22 0xA0")
            session.expect("10000:")
            session.sendline("i2cset -y 3 0x4a 0x21 0x61")
            session.expect("10000:")
            session.sendline("fpgautil w32 0 0x7020 0x80000000")
            session.expect("10000:")
            session.sendline("fpgautil w32 0 0x7024 0x80000000")
            session.expect("10000:")
            
            # save command file
            if args.file_path != "": 
                if os.path.exists(args.file_path):
                    with open(args.file_path, 'r') as file:
                        lines = file.readlines()
                        content_array = [line.strip() for line in lines]
                else:
                    print("File does not exist.")


            # connect to elba
            session.sendline("cd /fs/nos/home_diag/fpga_uart")
            session.expect("10000:/fs/nos/home_diag/fpga_uart#")
            session.sendline("./fpga_uart {}".format(args.port))
            session.expect("uart console") 
            session.sendline("")
            session.expect("#")
            
            # run single line command
            if args.command != "":
                session.sendline(args.command)
                session.expect_exact("#", timeout=30)

            # run command file
            if args.file_path != "":           
                for line in content_array:
                    session.sendline(line)
                    session.expect_exact("#", timeout=30)

            # disconnect elba
            session.sendline("")
            session.expect("#")
            #session.send("\x01")
            #session.send("\x18")
            
        except pexpect.TIMEOUT:
            print("Timeout exceeded while running command.")
        except pexpect.EOF:
            print("End of file reached while running command.")
        except Exception as e:
            print("Error while running command: {}".format(e))


if __name__ == "__main__":

    exec_cmd = exec_commands()

    parser = argparse.ArgumentParser(description="A script to run specified commands on Taormina elba")

    parser.add_argument('-cmd', '--command', type=str, default='', help='Specify a command line to execute on Taormina elba')
    parser.add_argument('-file', '--file_path', type=str, default='', help='Specify a filepath containing a list of commands to execute on elba')
    parser.add_argument('-p', '--port', type=int, default=0, help='Specify the elba port number to connect to')
    parser.set_defaults(func=exec_cmd.run)

    try:
        args = parser.parse_args()
    except Exception as e:
        print("Error: {}".format(e))
        parser.print_help()
        sys.exit(1)

    sys.exit(not args.func(args))
