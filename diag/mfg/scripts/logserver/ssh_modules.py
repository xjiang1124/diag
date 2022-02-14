#!/usr/bin/python3

import warnings
import openpyxl
import os
import sys
import time
from pexpect import pxssh
import getpass
import re

class ssh_modules(object):
	def __init__(self, hostname, logfile=None):
		self.debug = True
		self.logfile = None
		if logfile:
			self.logfile = logfile
		self.debug_print("Start ssh_modules...")
		self._username = "mfg"
		self._passwd = "pensando"
		self._hostname = hostname

	def ssh_login(self):
		try:
		    self.ssh_connection = pxssh.pxssh()
		    self.ssh_connection.login(self._hostname, self._username, self._passwd)
		    # s.sendline('uptime')   # run a command
		    # s.prompt()             # match the prompt
		    # print(s.before)        # print everything before the prompt.
		    # s.sendline('ls -l')
		    # s.prompt()
		    # print(s.before)
		    # s.sendline('df')
		    # s.prompt()
		    # print(s.before)
		    # s.logout()
		    return True
		except pxssh.ExceptionPxssh as e:
		    print("pxssh failed on login.")
		    print(e)
		    return False

	def ssh_logout(self):
		try:
			self.ssh_connection.logout()
			return True
		except pxssh.ExceptionPxssh as e:
		    print("pxssh failed on login.")
		    print(e)
		    return False

	def getuptimeinfo(self):
	    self.ssh_connection.sendline('uptime')   # run a command
	    self.ssh_connection.prompt()             # match the prompt
	    print(str(self.ssh_connection.before, "utf-8"))      # print everything before the prompt.

	def getflowflex(self,sn):
		cmd = 'cd /home/mfg/winson/mfg/scripts/'
		self.ssh_connection.sendline(cmd)
		self.ssh_connection.prompt() 
		cmd = "python getFlexflowdatabysn.py sn={}".format(sn)
		self.ssh_connection.sendline(cmd)
		self.ssh_connection.prompt() 
		resp = str(self.ssh_connection.before, "utf-8")
		print(resp)
		match = re.findall(r"CURRENT STATUS:\s+(\w.*\w)",resp)
		#print(match)
		if match:
			return match[0]

		return None



	def debug_print(self,msg):
		if self.debug:
			
			if self.logfile:
				self.logfile.WriteLine(str(msg))
			else:
				print(msg)
		return None