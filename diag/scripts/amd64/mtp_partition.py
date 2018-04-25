#!/usr/bin/env python

import pexpect
import re
import sys

#child = pexpect.spawn("fdisk -l /dev/mmcblk0")
#child.expect(pexpect.EOF)
#print child.before
#child.close()
print "=========\n"
child = pexpect.spawn("fdisk /dev/mmcblk0")
child.logfile_read = sys.stdout
child.expect("Command \(m for help\):")
child.sendline("m")
child.expect("Command \(m for help\):")
child.sendline("F")
child.expect("Command \(m for help\):")

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

print "==================="
start_sector = int(m.group(1))
end_sector = int(m.group(2))
print start_sector, end_sector
if end_sector - start_sector < 2048*1000:
    print "Not enough space!"
    child.sendline("q")
    child.expect(pexpect.EOF)
    sys.exit()
print "==================="

child.sendline("n")
child.expect("Select \(default p\): ")

child.sendline("p")
child.expect("Partition number \(3,4, default 3\): ")

# Partition number: use default
child.sendline()
child.expect(": ")

# Start sector
child.sendline(str(start_sector+2048))
child.expect(": ")

# End sector - use default
child.sendline()
child.expect(": ")

# Write partition
child.sendline("w")
child.expect(": ")

child.sendline("q")
child.expect(pexpect.EOF)

print "=== Partition Created: Reboot needed ==="
