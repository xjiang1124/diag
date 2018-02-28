#!/usr/bin/env python

import pexpect
import re
import sys

child = pexpect.spawn("bash")
child.logfile_read = sys.stdout
child.expect("\$ ")
child.sendline("sudo chmod ugo+rw /dev/i2c-8")
i = child.expect([": ", "\$ "])
if i == 0:
    child.sendline("lab123")
    child.expect("\$ ")

child.sendline("sudo chmod ugo+rw /dev/i2c-0")
i = child.expect([": ", "\$ "])
if i == 0:
    child.sendline("lab123")
    child.expect("\$ ")

child.sendline("sudo rmmod ftdi_sio")
child.expect("\$ ")

child.sendline("exit")
child.expect(pexpect.EOF)
