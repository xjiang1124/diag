#!/usr/bin/env python

from pyroute2 import netns
from telnetlib import Telnet
import signal
import datetime
import sys
import os

timeout = 1000 
netns.setns('swns')

# create a script-wide timeout event


def script_timeout_event(signum, frame):
    raise Exception('Script exceeded timeout.')


signal.signal(signal.SIGALRM, script_timeout_event)
signal.alarm(timeout)

# create the telnet connection
tn = Telnet('127.0.0.1', '1943', timeout)

# Add commands in the list.
# Format : 'command  

commandList = []

# For taking command line arguments
# Format : sudo python collect_bcm_l1_port_info.py command
sys.argv = [i+' \n' for i in sys.argv]
if len(sys.argv) > 1:
    commandList = commandList + sys.argv[1:]

# Output File Location
f = open('/tmp/bcm_cmd_output', 'w')

# HPE BCM Shell has prompt BCM.0> immediately once login
# no need to write a '\n'. Instead, need to read to consume the first 'BCM.0>'
# but diag BCM Shell need to write "\n" to reach prompt 'BCM.0>'
# further, if last time connection tn time out,
# the telnet session would not be released and thus blocks new connect request
tn.write('\n')
data = tn.read_until('BCM.0>')
#if data:
#    f.write(data)
#    tn.write('\n')
    # Loop over the commandList
    # Collecting data till the next BCM.0 prompt
for i in commandList:
    print(i)
    tn.write(i)
    data = tn.read_until('BCM.0>')
    if data:
        f.write(data)
#else:
#    tn.close()

#tn.write('exit \n')
tn.write('\n')
tn.close
timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
f.write('\n')
f.write(timestamp)
f.write('\n')
f.close()
os.system("cat /tmp/bcm_cmd_output")

