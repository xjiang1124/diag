#!/usr/bin/env python

from pyroute2 import netns
from telnetlib import Telnet
import signal
import datetime
import sys
import os
import fileinput

timeout = 1000
netns.setns('swns')

# create a script-wide timeout event


def script_timeout_event(signum, frame):
    raise Exception('Script exceeded timeout.')


signal.signal(signal.SIGALRM, script_timeout_event)
signal.alarm(timeout)

# check if "switchd" is running, if so, stop it and launch diag bcm shell
ret = os.system('ps -x | grep -v grep | grep switchd > /dev/null')
if (ret == 0):
    ans = raw_input("WARNING: switchd is running, going to stop it. Are you sure? (y/n) ")
    if (ans != 'y' and ans != 'Y'):
        exit()
    ret = os.system('systemctl stop switchd > /dev/null')
    if (ret != 0):
        print("Failed to stop switchd: rv = %d\n" % (ret))
        exit()
    os.system('/sbin/ip netns exec swns /usr/bin/netserve -d 1943 /fs/nos/eeupdate/bcm.user > /dev/null')

# check if diag bcm shell is running upon swns
ret = os.system('netstat -plunt | grep netserve | grep 1943 > /dev/null')
#print("return code of 'netstat -plunt': %d" % (ret))
if (ret != 0):
    print("ERROR: failed to start Diag BCM Shell!!!")
    print("       Please contact Diag engineer for debugging.")
    exit()

# create the telnet connection
tn = Telnet('127.0.0.1', '1943', timeout)
tn.write('\n')
data = tn.read_until('BCM.0>')

#tn.write('ps\n')
print("Initializing Trident3...")
tn.write('init all\n')
data = tn.read_until('BCM.0>')
if data:
    log = open('./start_diag_bcm_shell.log', 'w')
    log.write(data)

print("Initializing Gearbox...")
tn.write('gb_init\n')
data = tn.read_until('BCM.0>')
if data:
    log = open('./start_diag_bcm_shell.log', 'a')
    log.write(data)

print("Initializing Retimer...")
tn.write('rt_init\n')
data = tn.read_until('BCM.0>')
if data:
    log = open('./start_diag_bcm_shell.log', 'a')
    log.write(data)

#tn.write('exit \n')
tn.write('\n')
tn.close
timestamp = 'Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
log.write('\n')
log.write(timestamp)
log.write('\n')
log.close()
print("Completed start_diag_bcm_shell.py, please check logs in ./start_diag_bcm_shell.log")
