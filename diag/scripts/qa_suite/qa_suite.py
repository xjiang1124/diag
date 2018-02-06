#!/usr/bin/env python

import pexpect
import re
import sys

mtp_ip = "192.168.69.238"
ssh_cmd = "ssh diag@"+mtp_ip
bash_prompt = "\$ "

child = pexpect.spawn(ssh_cmd)
child.logfile_read = sys.stdout

# With or without password
i = child.expect(["password:", bash_prompt])
if i==0:
    child.sendline("lab123")
    child.expect(bash_prompt)

child.sendline("ls -l")
child.expect(bash_prompt)

child.sendline("exit")
child.expect(pexpect.EOF)
sys.exit()

# Parse free space info
re_pattern = "^(\d+)\s+(\d+)\s+(\d+).*"
re_p = re.compile(re_pattern)
buf = child.before
buflist = buf.splitlines()

for line in buflist:
    #print line
    m = re_p.match(line)
    if m:
        break
    else:
        if buflist.index(line) == len(buflist)-1:
            print "Can not find disk info! quit!"
            sys.exit()
child.expect(pexpect.EOF)

print "=== Partition Created: Reboot needed ==="
