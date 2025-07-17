#!/usr/bin/env python
#
import pexpect
import re
import sys
import time

PY3 = (sys.version_info[0] >= 3)
encoding = "utf-8" if PY3 else None

child = pexpect.spawn("bash", encoding=encoding, codec_errors='ignore')
child.logfile_read = sys.stdout
child.expect("\$ ")

child.sendline("sudo /home/diag/diag/tools/devmem 0xfed08010 w 0x80")
child.expect("\$ ")

child.sendline("sudo ifconfig enp3s0f1 10.1.1.100 netmask 255.255.255.0")
child.expect("\$ ")

child.close()

print("envinit Done")

