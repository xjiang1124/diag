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
import log_modules
from logdef import KEY_WORD
from logdef import RUN_KEY
import re

today = date.today()
# dd/mm/YY
todayday = today.strftime("%Y/%m/%d")
print("todayday =", todayday)

from datetime import datetime

MTPslot = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]

#screenlogDir = "/home/winson/winson/tmp/screenLog"

class Logger(object):
    def __init__(self,logfile):
        self.terminal = sys.stdout
        self.log = open(logfile, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  

class modules(object):
	def __init__(self, status,screenlogDir,TestUUT,testprogramDir,runtestCmd,family=None):
		self.debug = True
		now = datetime.now() # current date and time
		date_time = now.strftime("%Y%m%d_%H%M%S")
		print("date and time:",date_time)
		screenlog = "{}/{}_{}.log".format(screenlogDir,TestUUT,date_time)
		pexpectlog = "{}/pexpect_{}_{}.log".format(screenlogDir,TestUUT,date_time)
		self.tclshexp = "{}_%$%".format(TestUUT)
		self.status = status
		self.family = family
		self.markfalse = False
		self.logfile = screenlog
		self.pexpectlog = pexpectlog
		self.testuut = TestUUT
		self.testdir = testprogramDir
		self.runtestCmd = runtestCmd
		self.specialMessage = list()
		self.output = ""
		self.index = None
		self.scriptlogmodule = None
		self.define_status()

	def updatescriptlogmodule(self,logmodule):
		self.scriptlogmodule = logmodule

	def writelineinscriptlog(self,message):
		firstmessage = "[{}] {}".format(self.testuut,message)
		if self.scriptlogmodule:
			self.scriptlogmodule.WriteLine(firstmessage)
		else:
			print(firstmessage)
		return None

	def define_status(self):
		self.status["MTP"] = dict()
		self.status["MTP"]["name"] = None
		self.status["MTP"]["result"] = None
		self.status["MTP"]["status"] = None
		self.status["NIC"] = dict()
		for eachslot in MTPslot:
			self.status["NIC"][eachslot] = dict()
			self.status["NIC"][eachslot]["SN"] = None
			self.status["NIC"][eachslot]["PN"] = None
			self.status["NIC"][eachslot]["TYPE"] = None
			self.status["NIC"][eachslot]["result"] = None
			self.status["NIC"][eachslot]["status"] = None

	def update_testing_in_MTP(self):
		self.status["MTP"]["name"] = self.testuut
		self.status["MTP"]["status"] = "testing"

	def update_failure_in_MTP(self):
		self.status["MTP"]["result"] = "FAIL"
		self.status["MTP"]["status"] = "done"

	def update_complete_in_MTP(self):
		self.status["MTP"]["result"] = "COMPLETE"
		self.status["MTP"]["status"] = "done"

	def check_screenlog(self):
		return self.logfile

	def update_test_result(self,testresult):
		self.status['RESULT'] = testresult
		return None

	def update_each_nic_result(self,eachslot,eachtype,eachsn,eachresult):
		self.status["NIC"][eachslot]["result"] = eachresult
		self.status["NIC"][eachslot]["status"] = "done"
		self.status["NIC"][eachslot]["TYPE"] = eachtype
		self.status["NIC"][eachslot]["SN"] = eachsn

	def update_each_nic_in_test(self,eachslot,eachsn):
		self.status["NIC"][eachslot]["status"] = "testing"
		self.status["NIC"][eachslot]["SN"] = eachsn

	def update_each_nic_pn(self,eachslot,eachpn):
		self.status["NIC"][eachslot]["PN"] = eachpn

	def updateresultstatusbycheckpointdata(self,checkpointdata,TESTEND=False):
		start=datetime.now()
		if "FIND_MTP_RE" in checkpointdata:
			if "REPORT" in checkpointdata["FIND_MTP_RE"][0].upper():
				self.update_complete_in_MTP()
			else:
				self.update_failure_in_MTP()

		if "FIND_NIC_RE" in checkpointdata:
			for eachdata in checkpointdata["FIND_NIC_RE"]:
				self.update_each_nic_result(eachdata[0],eachdata[1],eachdata[2],eachdata[3])
		elif "FIND_NIC_SN" in checkpointdata:
			for eachdata in checkpointdata["FIND_NIC_SN"]:
				self.update_each_nic_in_test(eachdata[0],eachdata[1])

		if "FIND_NIC_PN" in checkpointdata:
			for eachdata in checkpointdata["FIND_NIC_PN"]:
				self.update_each_nic_pn(eachdata[0],eachdata[1])

		if "FIND_MTP_FAIL" in checkpointdata:
			self.update_failure_in_MTP()

		if TESTEND:
			if not "FIND_MTP_RE" in checkpointdata:
				self.update_failure_in_MTP()
		
		difftime = datetime.now()-start
		print('Done Time: ', difftime)
		self.writelineinscriptlog("updateresultstatusbycheckpointdata: {} seconds".format(difftime.total_seconds()))
		return None

	def TakecardLastlinetoprovideresponce(self):
		start=datetime.now()

		if len(self.output):

			outputlist = self.output.replace('\r','\n').split('\n')
			print(outputlist[-1])
			for keystatus in RUN_KEY.checkresponcestatus:
				sub_match = re.findall(RUN_KEY.checkresponcestatus[keystatus], outputlist[-1])
				if sub_match:
					return self.sendresponcefunction(keystatus)

		difftime = datetime.now()-start
		print('Done Time: ', difftime)
		self.writelineinscriptlog("TakecardLastlinetoprovideresponce: {} seconds".format(difftime.total_seconds()))
		return None
	
	def sendresponcefunction(self, keystatus):
		if keystatus.startswith("FINDSTOP"):
			self.child.sendline('STOP')
		elif keystatus == "NEEDINPUTSWPN":
			if self.family:
				if self.family == 'ORTANO':
					self.child.sendline('90-0009-0004')
				elif self.family == 'ORTANO2ADI':
					self.child.sendline('90-0009-0005')

			else:
				self.child.sendline('90-0009-0005')
		elif keystatus.startswith("FINDSENDENTER"):
			self.child.sendline('')
		return None

	def addspecialMessage(self,message):
		self.specialMessage.append(message)
		return None

	def ShowspecialMessageinconsoleOutput(self):
		for eachmessage in self.specialMessage:
			self.send_command_wait_for_output(eachmessage)
		return None

	def startRunchannel(self):
	    self.child = pexpect.spawn ('ssh mfg@192.168.3.2', encoding='utf-8')
	    self.child.logfile = log_modules.Logger(self.pexpectlog)
	    #time.sleep(2)
	    #self.child.sendline("yes")
	    #time.sleep(2)
	    #self.child.sendline("pensando")
	    # self.child.sendline("global tcl_prompt1 tcl_prompt2")
	    time.sleep(30)
	    self.child.sendline('export PS1="' + self.tclshexp + ' "')
	    # time.sleep(1)
	    # self.child.sendline('set tcl_prompt2 {}')
	    time.sleep(1)

	def SetupTestEnv(self):

		output1 = self.send_command_wait_for_output("cd {}".format(self.testdir))
		print(output1)
		output1 = self.send_command_wait_for_output('pwd')
		print(output1)
		output1 = self.send_command_wait_for_output(self.runtestCmd,exp_list=["Scan the MTP ID Bar Code"])
		print(output1)
		if not self.testuut in output1:
			message = "\"\[{}\] is not in Test config\"".format(self.testuut)
			cmd = "echo {}".format(message)
			self.addspecialMessage(cmd)
			self.markfalse = True
			return False

		output1 = self.send_command_wait_for_output(self.testuut,exp_list=["Selected"])
		print(output1)

		return True

	def StartTest(self):
		self.clear_buffer()
		self.child.sendline('STOP')

	def MonitorTest(self):
		Timeoutcount = 5
		while True:
			self.index = self.runtest_expect([self.tclshexp], timeout=Timeoutcount)
			if self.index > -1:
				output_temp = str(self.child.before) + str(self.child.after) + str(self.child.buffer)
			else:
				output_temp = str(self.child.before)
			self.clear_buffer2()
			self.output += output_temp
			if len(output_temp)>0:
				print(output_temp)
			if self.index == 0:
				break

		print(self.output)
		print(self.index)
		self.writelineinscriptlog('TEST END')

		return None	

	def MonitorTest2(self):
		Timeoutcount = 60
		
		self.index = self.runtest_expect([self.tclshexp], timeout=Timeoutcount)
		if self.index > -1:
			output_temp = str(self.child.before) + str(self.child.after) + str(self.child.buffer)
		else:
			output_temp = str(self.child.before)
		self.clear_buffer2()
		self.output += output_temp
		if len(output_temp)>0:
			print(output_temp)
		if self.index == 0:
			return False

		#print(self.output)
		#print(index)
		#print('TEST END')

		return True	

	def checkoutputstatus(self):
		start=datetime.now()
		resultindict = dict()
		for keystatus in RUN_KEY.checkstatus:
			sub_match = re.findall(RUN_KEY.checkstatus[keystatus].format(self.testuut), self.output)
			if sub_match:
				#print(x)
				print("keystatus: {}".format(keystatus))
				print(sub_match)
				resultindict[keystatus] = sub_match

		difftime = datetime.now()-start
		print('Done Time: ', difftime)
		self.writelineinscriptlog("checkoutputstatus: {} seconds".format(difftime.total_seconds()))
		return resultindict

	def send_command_wait_for_output(self, command, exp_list=None, timeout=None):
		self.clear_buffer()
		print(exp_list)
		_exp_list = list()
		_exp_list.append(self.tclshexp)
		if exp_list:
			_exp_list = _exp_list[:] + exp_list[:]

		self.child.sendline(command)

		index = self.runtest_expect(_exp_list, timeout=timeout)
		return_output = ""
		if index >= 0:
			return_output = str(self.child.before) + str(self.child.after) + str(self.child.buffer)

		#print(self.child)
		return return_output


	def runtest_expect(self, exp_list, timeout=None):
	    _exp_list = exp_list[:] + [pexpect.TIMEOUT]
	    _timeout = timeout
	    if _timeout != None:
	        idx = self.child.expect_exact(_exp_list, timeout = _timeout)
	    else:
	        idx = self.child.expect_exact(_exp_list)

	    if idx >= len(exp_list):
	        return -1
	    else:
	        return idx

	def clear_buffer(self):
		self.child.buffer = ''
		buff = None
		try:
			buff = self.child.read_nonblocking(16384, timeout = 1)
			#print("clear_buffer(): read_nonblocking: ***{}***".format(buff))
		except pexpect.exceptions.TIMEOUT as toe:
			#print("clear_buffer(): TIMEOUT, buff: ***{}***".format(buff))
			pass
		except pexpect.exceptions.EOF:
			pass

	def clear_buffer2(self):
		self.child.buffer = ''

	def endchannel(self):
		self.child.sendline('exit')
		self.child = None
		return None

	def _removeNonAscii(self,s): return "".join(i for i in s if ord(i)<128)

	def _keepnumberandsomestamps(self,s): return "".join(i for i in s if ord(i)<65)

	def _removespace(self,s): return "".join(i for i in s if ord(i)!=32)

	def _removeenter(self,s): return "".join(i for i in s if ord(i)!=12)

	def _onlykeepword(self,s): return "".join(i for i in s if (ord(i)>=48 and ord(i)<=57) or (ord(i)>=97 and ord(i)<=122) or (ord(i)>=65 and ord(i)<=90) or ord(i)==32 or ord(i)==45)

	def _remove47(self,s): return "".join(i for i in s if ord(i)!=47 and ord(i)!=43 and ord(i)!=58 and ord(i)!=33)