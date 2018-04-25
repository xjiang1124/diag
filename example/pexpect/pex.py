#!/usr/bin/env python
from __future__ import print_function
import pexpect
import sys
from time import sleep

bash = pexpect.spawn('/bin/bash')
bash.logfile = sys.stdout
bash.expect_exact("$ ")
#print(bash.before)
bash.sendline("ls")
bash.expect_exact("$ ")
#print(bash.before)
bash.sendline("ls -l")
bash.expect_exact("$ ")

