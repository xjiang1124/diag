#!/usr/bin/python3

import warnings
import os
import sys
import time
import glob
import os.path
from os import path
import datetime
from datetime import datetime
from datetime import date
import pexpect

today = date.today()
# dd/mm/YY
todayday = today.strftime("%Y/%m/%d")
print("todayday =", todayday)

from datetime import datetime

now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d_%H%M%S")
print("date and time:",date_time)

class Logger(object):
	#"Lumberjack class - duplicates sys.stdout to a log file and it's okay"
	#source: https://stackoverflow.com/q/616645
	def __init__(self, filename, mode="a", buff=0):
		self.stdout = sys.stdout
		print("filename: {}".format(filename))
		self.file = open(filename, mode)
		#sys.stdout = self

	def __del__(self):
		self.close()

	def __enter__(self):
		pass

	def __exit__(self, *args):
		self.close()

	def write(self, message):
		#self.stdout.write(message)
		#self.file.write(self._remove_esc(self._removeNonAscii(message)))
		self.file.write(self._removeNonAscii(message))

	def flush(self):
		self.stdout.flush()
		self.file.flush()
		os.fsync(self.file.fileno())

	def close(self):
		if self.stdout != None:
			sys.stdout = self.stdout
			self.stdout = None

		if self.file != None:
			self.file.close()
			self.file = None

	def _removeNonAscii(self,s): return "".join(i for i in s if ord(i)<128)

	def _keepnumberandsomestamps(self,s): return "".join(i for i in s if ord(i)<65)

	def _remove_esc(self,s): return "".join(i for i in s if ord(i)!=27)

	def _removespace(self,s): return "".join(i for i in s if ord(i)!=32)

	def _removeenter(self,s): return "".join(i for i in s if ord(i)!=12)

	def _onlykeepword(self,s): return "".join(i for i in s if (ord(i)>=48 and ord(i)<=57) or (ord(i)>=97 and ord(i)<=122) or (ord(i)>=65 and ord(i)<=90) or ord(i)==32 or ord(i)==45)

	def _remove47(self,s): return "".join(i for i in s if ord(i)!=47 and ord(i)!=43 and ord(i)!=58 and ord(i)!=33)