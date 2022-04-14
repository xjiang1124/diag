#!/usr/bin/env python

from pyroute2 import netns
from telnetlib import Telnet
import signal
import datetime
import sys
import os
import socket

timeout = 1200
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
#commandList.append('exit \n')

# Output File Location
f = open('/tmp/bcm_cmd_output', 'w')

tn.write('\n')
data = tn.read_until('BCM.0>')
if data:
    f.write(data)
    # Loop over the commandList
    # Collecting data till the next BCM.0 prompt
    for i in commandList:
        tn.write(i)
        data = tn.read_until('BCM.0>')
        f.write(data)
#else:
#    tn.close()
#
#tn.write('exit \n')
#tn.get_socket().shutdown(socket.SHUT_WR)
tn.write('\n')
tn.close
timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
f.write('\n')
f.write(timestamp)
f.close()
os.system("cat /tmp/bcm_cmd_output")

