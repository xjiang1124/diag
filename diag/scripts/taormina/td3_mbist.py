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

# check if diag bcm shell is running upon swns
ret = os.system('netstat -plunt | grep netserve | grep 1943 > /dev/null')
#print("return code of 'netstat -plunt': %d" % (ret))
if (ret != 0):
    print("ERROR: Diag BCM Shell is not running!!!")
    print("       Please launch Diag BCM Shell and init TD3/GB/RT first.")
    exit()

# create the telnet connection
tn = Telnet('127.0.0.1', '1943', timeout)
tn.write('\n')
data = tn.read_until('BCM.0>')

tn.write('ps\n')
#tn.write('TestRun 147\n')
data = tn.read_until('BCM.0>')
if data:
    # Output File Location
    f = open('/tmp/bcm_cmd_output', 'w')
    f.write(data)

#tn.write('exit \n')
tn.write('\n')
tn.close
timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
f.write('\n')
f.write(timestamp)
f.write('\n')
f.close()
os.system("cat /tmp/bcm_cmd_output")

