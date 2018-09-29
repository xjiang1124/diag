#!/usr/bin/env python

import pexpect
import re
import sys
import time

child = pexpect.spawn("bash")
child.logfile_read = sys.stdout
child.expect("\$ ")
child.sendline("sudo chmod ugo+rw /dev/i2c-8")
i = child.expect(["diag: ", "\$ "])
if i == 0:
    child.sendline("lab123")
    child.expect("\$ ")

child.sendline("sudo chmod ugo+rw /dev/i2c-0")
i = child.expect(["diag: ", "\$ "])
if i == 0:
    child.sendline("lab123")
    child.expect("\$ ")

child.sendline("sudo rmmod ftdi_sio")
child.expect("\$ ")

child.sendline("sudo chmod ugo+rw /dev/bus/usb/001/001")
child.expect("\$ ")

child.sendline("sudo chmod ugo+rw /dev/bus/usb/001/002")
child.expect("\$ ")

time.sleep(30)

# Enable fan controller
#child.sendline("spi_acc reg 0xe 0x10")
child.sendline("cpldutil -cpld-wr -addr=0xe -data=0x10")
child.expect("\$ ")
child.sendline("cpldutil -cpld-wr -addr=0x2 -data=0x00")
child.expect("\$ ")

child.sendline("devmgr -dev=fan -faninit")
child.expect("\$ ")
child.sendline("devmgr -dev=fan -speed -pct=40")
child.expect("\$ ")

child.close()

print "envinit Done"

