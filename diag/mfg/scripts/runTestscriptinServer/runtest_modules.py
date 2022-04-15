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
import mysql_db
import json

today = date.today()
# dd/mm/YY
todayday = today.strftime("%Y/%m/%d")
print("todayday =", todayday)

from datetime import datetime

MTPslot = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]


class Logger(object):
    def __init__(self,logfile):
        self.terminal = sys.stdout
        self.log = open(logfile, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  

class db_modules(object):
	def __init__(self,logmodule=None,username=None, password=None):
		start=datetime.now()
		self.username = 'prodmgr'
		self.password = 'mgruser2wsx$RFV'
		if username:
			self.username = username

		if password:
			self.password = password
		
		self.db = None
		self.logmodule = None
		if logmodule:
			self.logmodule = logmodule

		self.perpare_status_table()
		self.perpare_product_info_table()
		self.perpare_test_info_table()

		difftime = datetime.now()-start

		self.wirtetoscript('db_modulesDone Time: {}'.format(difftime))

	def wirtetoscript(self,message):
		message = str(message)
		if self.logmodule:
			self.logmodule.WriteLine(message)
		else:
			print(message)
		return None

	def push_result_to_history(self,mtp):
		
		cmd1 = "Call copyResultToHistory(\"{}\",@spResult);".format(mtp)
		cmd2 = "select @spResult as result;"

		self.wirtetoscript("push_result_to_history")

		if not self.db:
			self.open_database()

		self.db.execute_cmd(cmd1)
		
		returnlist = self.db.read_cmd(cmd2)

		self.wirtetoscript(returnlist)

		self.close_database()		
		


	def perpare_test_info_table(self):

		if 'test_info' in self.show_table_to_mfg_database():
			status_info = self.get_data_on_table_from_mfg_database('test_info',returntype='list')
			self.test_info1 = self.convert_list_to_dict(status_info,['test_type','exec_script'])
			self.test_info2 = self.convert_list_to_dict(status_info,['name_dis','exec_script'])
			self.test_info_col = self.convert_list_to_dict(status_info,['test_type','info_col'])
			self.test_info_dict = self.get_data_on_table_from_mfg_database('test_info')

		return None

	def Get_test_exec_script(self,number,familynumber):
		self.wirtetoscript("Get_test_exec_script: {}".format(number))
		print(self.test_info1)
		test_exec_script_cmd = None
		if number in self.test_info1:

			test_exec_script_cmd = self.test_info1[number]
			if self.product_dict[familynumber][self.test_info_col[number]]:
				if len(self.product_dict[familynumber][self.test_info_col[number]]):
					test_exec_script_cmd = "{} {}".format(test_exec_script_cmd,self.product_dict[familynumber][self.test_info_col[number]])

		return test_exec_script_cmd

	def perpare_product_info_table(self):

		if 'product_info' in self.show_table_to_mfg_database():
			status_info = self.get_data_on_table_from_mfg_database('product_info',returntype='list')
			self.product_info1 = self.convert_list_to_dict(status_info,['id','script_path'])
			self.product_info2 = self.convert_list_to_dict(status_info,['name_dis','id'])
			self.product_dict = self.get_data_on_table_from_mfg_database('product_info')

		return None

	def Get_test_exec_script_path(self,number):
		self.wirtetoscript("Get_test_exec_script_path: {}".format(number))
		if number in self.product_info1:
			return self.product_info1[number]
		return None

	def perpare_status_table(self):

		if 'status_info' in self.show_table_to_mfg_database():
			status_info = self.get_data_on_table_from_mfg_database('status_info',returntype='list')
			self.status_info1 = self.convert_list_to_dict(status_info,['status','status_name'])
			self.status_info2 = self.convert_list_to_dict(status_info,['status_name','status'])

		return None

	def Get_status_in_number(self,keyword):
		keyword = keyword.upper()
		self.wirtetoscript("Get_status_in_number: {}".format(keyword))
		if keyword in self.status_info2:
			return self.status_info2[keyword]
		return None

	def Get_status_in_keyword(self,number):
		self.wirtetoscript("Get_status_in_keyword: {}".format(number))
		if number in self.status_info1:
			return self.status_info1[number]
		return None

	def get_mtp_startTestlist_from_mfg_database(self):

	    fields = self.check_table_to_mfg_database('mtp_status')
	    checklist = dict()
	    checklist['mtp_status'] = self.Get_status_in_number("STARTTEST")

	    infoindict = self.get_data_from_mfg_database('mtp_status',fields,checklist)
	    
	    returnlist = list()
	    for eachMTP in infoindict:
	    	returnlist.append(eachMTP)

	    return returnlist

	def update_one_nic_sn_on_mtp_status(self,mtp,nic_slot,sn):
		self.wirtetoscript("update_one_nic_sn_on_mtp_status<{}>: {}".format(sn,mtp))
		updatedict = dict()
		updatedict['nic_sn'] = sn
		referdict = dict()
		referdict['mtp_id'] = mtp
		referdict['nic_slot'] = nic_slot
		if not self.check_one_nic_sn_on_mtp_by_keyword(mtp,nic_slot,sn):
			self.wirtetoscript("update_one_nic_sn_on_mtp_status<{}> not match, Need to update database: {}".format(sn,mtp))
			self.update_data_to_mfg_database(updatedict,'nic_status',referdict)

			if self.check_one_nic_sn_on_mtp_by_keyword(mtp,nic_slot,sn):
				self.wirtetoscript("update_one_nic_sn_on_mtp_status<{}> update database success: {}".format(sn,mtp))
				return True
			else:
				self.wirtetoscript("update_one_nic_sn_on_mtp_status<{}> update database False: {}".format(sn,mtp))
				return False
		else:
			self.wirtetoscript("update_one_nic_sn_on_mtp_status<{}> match, don't Need to update database: {}".format(sn,mtp))
			return True

	def check_one_nic_sn_on_mtp_by_keyword(self,mtp,nic_slot,sn):
		if sn:
			mtpinfo = self.get_one_nic_status_on_mtp_from_mfg_database(mtp,nic_slot)
			if sn == mtpinfo['nic_sn']:
				self.wirtetoscript("check_one_nic_sn_on_mtp_by_keyword <{}> {} | {}: True".format(sn,mtp,nic_slot))
				return True
			else:
				self.wirtetoscript("check_one_nic_sn_on_mtp_by_keyword <{}> {} | {}: False".format(sn,mtp,nic_slot))
				return False
		else:
			return None

	def update_one_nic_status_on_mtp_status(self,mtp,nic_slot,keyword):
		self.wirtetoscript("update_one_nic_status_on_mtp_status <{}>: {} SLOT: {}".format(keyword,mtp,nic_slot))
		updatedict = dict()
		updatedict['nic_status'] = self.Get_status_in_number(keyword)
		referdict = dict()
		referdict['mtp_id'] = mtp
		referdict['nic_slot'] = nic_slot
		if not self.check_one_nic_status_on_mtp_by_keyword(mtp,nic_slot,keyword):
			self.wirtetoscript("update_one_nic_status_on_mtp_status<{}> not match, Need to update database: {}".format(keyword,mtp))
			self.update_data_to_mfg_database(updatedict,'nic_status',referdict)

			if self.check_one_nic_status_on_mtp_by_keyword(mtp,nic_slot,keyword):
				self.wirtetoscript("update_one_nic_status_on_mtp_status<{}> update database success: {}".format(keyword,mtp))
				return True
			else:
				self.wirtetoscript("update_one_nic_status_on_mtp_status<{}> update database False: {}".format(keyword,mtp))
				return False
		else:
			self.wirtetoscript("update_one_nic_status_on_mtp_status<{}> match, don't Need to update database: {}".format(keyword,mtp))
			return True

	def check_one_nic_status_on_mtp_by_keyword(self,mtp,nic_slot,keyword):
		checknumber = self.Get_status_in_number(keyword)
		if checknumber:
			mtpinfo = self.get_one_nic_status_on_mtp_from_mfg_database(mtp,nic_slot)
			if checknumber == mtpinfo['nic_status']:
				self.wirtetoscript("cheeck_one_nic_status_on_mtp_by_keyword <{}> {} | {}: True".format(keyword,mtp,nic_slot))
				return True
			else:
				self.wirtetoscript("cheeck_one_nic_status_on_mtp_by_keyword <{}> {} | {}: False".format(keyword,mtp,nic_slot))
				return False
		else:
			return None

	def get_one_nic_status_on_mtp_from_mfg_database(self,mtp,nic_slot):

	    fields = self.check_table_to_mfg_database('nic_status')
	    checklist = dict()
	    checklist['mtp_id'] = mtp
	    checklist['nic_slot'] = nic_slot

	    infoindict = self.get_data_from_mfg_database('nic_status',fields,checklist,returntype='list')
	    self.wirtetoscript(infoindict)
	    if infoindict:
	    	return infoindict[0]

	    return None

	def update_MTP_end_time(self,mtp):
		self.wirtetoscript("update_MTP_end_time<{}>".format(mtp))
		date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		updatedict = dict()
		updatedict['end_time'] = date
		referdict = dict()
		referdict['mtp_id'] = mtp
		self.update_data_to_mfg_database(updatedict,'mtp_status',referdict)

		return None

	def update_MTP_start_time(self,mtp):
		self.wirtetoscript("update_MTP_start_time<{}>".format(mtp))
		date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		updatedict = dict()
		updatedict['start_time'] = date
		referdict = dict()
		referdict['mtp_id'] = mtp
		self.update_data_to_mfg_database(updatedict,'mtp_status',referdict)

		return None

	def update_MTP_log_file(self,mtp,logfile):
		self.wirtetoscript("update_MTP_log_file<{}>: {}".format(mtp,logfile))
		updatedict = dict()
		updatedict['log_file'] = logfile
		referdict = dict()
		referdict['mtp_id'] = mtp
		self.update_data_to_mfg_database(updatedict,'mtp_status',referdict)

		return None

	def update_MTP_status(self,mtp,keyword):
		self.wirtetoscript("update_MTP_status_to_<{}>: {}".format(keyword,mtp))
		updatedict = dict()
		updatedict['mtp_status'] = self.Get_status_in_number(keyword)
		referdict = dict()
		referdict['mtp_id'] = mtp
		if not self.cheeck_mtp_status_by_keyword(mtp,keyword):
			self.wirtetoscript("update_MTP_status_to_<{}> Need Update: {}".format(keyword,mtp))
			self.update_data_to_mfg_database(updatedict,'mtp_status',referdict)

			if self.cheeck_mtp_status_by_keyword(mtp,keyword):
				self.wirtetoscript("update_MTP_status_to_<{}> Updates: {}".format(keyword,mtp))
				return True
			else:
				self.wirtetoscript("update_MTP_status_to_<{}> update Failed: {}".format(keyword,mtp))
				return False
		else:
			self.wirtetoscript("update_MTP_status_to_<{}> up to date: {}".format(keyword,mtp))
			return True

	def check_MTPSTOP_status(self,mtp,keyword='MTPSTOP'):
		self.wirtetoscript("check_MTPSTOP_status <{}>: {}".format(keyword,mtp))
		if self.cheeck_mtp_status_by_keyword(mtp,keyword):
			self.wirtetoscript("check_MTPSTOP_status <{}> get it: {}".format(keyword,mtp))
			return True
		else:
			self.wirtetoscript("check_MTPSTOP_status <{}> don't have it: {}".format(keyword,mtp))
			return False


	def cheeck_mtp_status_by_keyword(self,mtp,keyword):
		checknumber = self.Get_status_in_number(keyword)
		if checknumber:
			mtpinfo = self.get_one_mtp_status_from_mfg_database(mtp)
			if checknumber == mtpinfo['mtp_status']:
				return True
			else:
				return False
		else:
			return None

	def get_one_mtp_status_from_mfg_database(self,mtp):

	    fields = self.check_table_to_mfg_database('mtp_status')
	    checklist = dict()
	    checklist['mtp_id'] = mtp

	    infoindict = self.get_data_from_mfg_database('mtp_status',fields,checklist)
	    if mtp in infoindict:
	    	return infoindict[mtp]

	    return None

	def get_data_on_table_from_mfg_database(self,table,checklist=None,returntype='dict'):

	    fields = self.check_table_to_mfg_database(table)
	    infoindict = self.get_data_from_mfg_database(table,fields,checklist=checklist,returntype=returntype)
	    self.wirtetoscript(infoindict)

	    return infoindict

	def check_table_to_mfg_database(self,table):

		self.wirtetoscript("check_table_to_mfg_database: {}".format(table))

		if not self.db:
			 self.open_database()

		returnlist = self.db.check_table(table)

		self.wirtetoscript(returnlist)

		self.close_database()

		return returnlist

	def show_table_to_mfg_database(self):

		self.wirtetoscript("show_table_to_mfg_database")

		if not self.db:
			self.open_database()

		returnlist = self.db.show_table()

		self.wirtetoscript(returnlist)

		self.close_database()

		return returnlist

	def convert_list_to_dict(self,listdata,fields):
		self.wirtetoscript("convert_list_to_dict")
		if len(fields) == 2:
			returndata = dict()
			for eachdata in listdata:
				returndata[eachdata[fields[0]]] = eachdata[fields[1]]
			self.wirtetoscript(returndata)
			return returndata
		else:
			return None

	def get_data_from_mfg_database(self,table,fields, checklist=None, returntype='dict'):
	    if not self.db:
	        self.open_database()

	    insertlist = list()
	    insertsprint = fields[0]
	    insertlist.append(fields[0])    
	    for name in fields[1:]:
	        print(name)
	        insertsprint = insertsprint + "," + name 
	        insertlist.append(name)
	    
	    query = "SELECT " + insertsprint + " FROM " + table
	    values = list()
	    if checklist:
	    	checkliststr = list()
	    	for eackkey in checklist:
	    		if not eackkey in fields:
	    			self.wirtetoscript("ERROR: Key <{}> is not in Feild <{}>".format(eackkey, fields))
	    			return None
	    		checkstr = "{} = %s".format(eackkey)
	    		values.append(checklist[eackkey])
	    		checkliststr.append(checkstr)

	    	query = "{} WHERE {}".format(query,checkliststr[0])
	    	for eachstr in checkliststr[1:]:
	    		query = "{} AND {}".format(query,eachstr)

	    
	    self.wirtetoscript(query)
	    fields = insertlist
	    returndata = None

	    if returntype == 'dict':
		    returndata = dict()

		    if self.db.select_ret_dict(query, values, fields, returndata):
		        self.wirtetoscript("ERROR:  Query failed {0}, {1}".format(query, insertdata[checklist[0]]))
		        sys.exit()
		        return -1

		    self.wirtetoscript(returndata)

	    elif returntype == 'list':
		    returndata = list()
		    if self.db.select_ret_list(query, values, fields, returndata):
		        self.wirtetoscript("ERROR:  Query failed {0}, {1}".format(query, insertdata[checklist[0]]))
		        sys.exit()
		        return -1

		    self.wirtetoscript(returndata)

	    self.close_database()

	    return returndata


	def update_data_to_mfg_database(self, insertdata,table,checklist):
		fields = self.check_table_to_mfg_database(table)

		if not self.db:
			self.open_database()
		stat = 0

		date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		insertsprint = ""
		insertlist = list()
		firstone = 1
		for name in insertdata:
			print(name)
			if insertdata[name]:
				if firstone:
					insertsprint = insertsprint + name + " = \"" + str(insertdata[name]) + "\""
					firstone = 0
				else:
					insertsprint = insertsprint + " , " + name + " = \"" + str(insertdata[name]) + "\""
				insertlist.append(insertdata[name])

		insert_cert_cmd = "UPDATE " + table + " SET " + insertsprint
		
		checkliststr = list()
		for eackkey in checklist:
			if not eackkey in fields:
				self.wirtetoscript("ERROR: Key <{}> is not in Feild <{}>".format(eackkey, fields))
				return None
			checkstr = "{} = \"{}\"".format(eackkey,checklist[eackkey])
			checkliststr.append(checkstr)

		insert_cert_cmd = "{} WHERE {}".format(insert_cert_cmd,checkliststr[0])
		for eachstr in checkliststr[1:]:
			insert_cert_cmd = "{} AND {}".format(insert_cert_cmd,eachstr)

		self.wirtetoscript(insert_cert_cmd)

		if self.db.update_data(insert_cert_cmd):
			self.wirtetoscript("Error:  update failed: <{0}>".format(
			insert_cert_cmd))
			stat = -1

		self.close_database()
		return stat

	def open_database(self):
	    """ Open database."""
	    db = mysql_db.mysql_db()

	    if db.connect(username=self.username, pw=self.password):
	        self.wirtetoscript("Error:  Failed to connect to db.")
	        return -1
	    else:
	        self.wirtetoscript("Database opened: {0}".format(db.database))

	    self.db = db

	    return None

	def close_database(self):
	    """ Close database."""
	    if self.db:
	        self.db.disconnect()
	        self.db = None
	    return 0

class modules(object):
	def __init__(self, status,screenlogDir,TestUUT,testprogramDir,runtestCmd,family=None):
		self.debug = True
		now = datetime.now() # current date and time
		date_time = now.strftime("%Y%m%d_%H%M%S")
		print("date and time:",date_time)
		screenlog = "{}/{}_{}.log".format(screenlogDir,TestUUT,date_time)
		basescreenlog = "{}_{}.log".format(TestUUT,date_time)
		pexpectlog = screenlog
		self.tclshexp = "{}_%$%".format(TestUUT)
		self.status = status
		self.family = family
		self.markfalse = False
		self.mtpstop = False
		self.logfile = screenlog
		self.baselogfile = basescreenlog
		self.pexpectlog = pexpectlog
		self.testuut = TestUUT
		self.testdir = testprogramDir
		if not './' == runtestCmd[:2]:
			runtestCmd = './' + runtestCmd
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

	def update_status_in_database(self,pr,Testuut):
		start=datetime.now()
		if self.status["MTP"]["status"]:
			pr['db'].update_MTP_status(Testuut,self.status["MTP"]["status"])
	
		for eachslot in self.status["NIC"]:
			if self.status["NIC"][eachslot]["SN"]:
				pr['db'].update_one_nic_sn_on_mtp_status(Testuut,eachslot,self.status["NIC"][eachslot]["SN"])
			if self.status["NIC"][eachslot]["status"]:
				pr['db'].update_one_nic_status_on_mtp_status(Testuut,eachslot,self.status["NIC"][eachslot]["status"])

		difftime = datetime.now()-start
		self.writelineinscriptlog("update_status_in_database: {} seconds".format(difftime.total_seconds()))

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
		#{'IDLE': 0, 'STARTTEST': 1, 'TESTING': 2, 'PASS': 3, 'FAIL': 4, 'MTPDONE': 5}

	def update_testing_in_MTP(self):
		self.status["MTP"]["name"] = self.testuut
		self.status["MTP"]["status"] = "TESTING"

	def update_failure_in_MTP(self):
		self.status["MTP"]["result"] = "FAIL"
		self.status["MTP"]["status"] = "FAIL"

	def update_complete_in_MTP(self):
		self.status["MTP"]["result"] = "MTPDONE"
		self.status["MTP"]["status"] = "MTPDONE"

	def update_STOP_in_MTP(self):
		self.status["MTP"]["result"] = "MTPSTOP"
		self.status["MTP"]["status"] = "MTPSTOP"
		self.mtpstop = True

	def update_STOPDONE_in_MTP(self):
		self.status["MTP"]["result"] = "MTPSTOPDONE"
		self.status["MTP"]["status"] = "MTPSTOPDONE"
		self.mtpstop = True

	def update_STOP_in_AllNic(self):
		for eachslot in MTPslot:
			if self.status["NIC"][eachslot]["SN"]:
				self.status["NIC"][eachslot]["status"] = "MTPSTOP"

	def check_all_NIC_STATUS_is_not_TESTING_in_AllNic(self):
		for eachslot in MTPslot:
			if self.status["NIC"][eachslot]["SN"]:
				if self.status["NIC"][eachslot]["status"] == "TESTING":
					self.status["NIC"][eachslot]["status"] = "MTPSTOP"

	def check_screenlog(self):
		return self.baselogfile

	def update_test_result(self,testresult):
		self.status['RESULT'] = testresult
		return None

	def update_each_nic_result(self,eachslot,eachtype,eachsn,eachresult):
		self.status["NIC"][eachslot]["result"] = eachresult
		self.status["NIC"][eachslot]["status"] = eachresult.upper()
		self.status["NIC"][eachslot]["TYPE"] = eachtype
		self.status["NIC"][eachslot]["SN"] = eachsn

	def update_each_nic_in_test(self,eachslot,eachsn):
		self.status["NIC"][eachslot]["status"] = "TESTING"
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
			self.child.logfile.write(eachmessage)
		return None

	def startRunchannel(self):

		return self.startRunchannel_bash()

		#return self.startRunchannel_sshtoMFlex()

	def startRunchannel_sshtoMFlex(self):
	    self.child = pexpect.spawn ('ssh mfg@192.168.1.112', encoding='utf-8')
	    self.child.logfile = log_modules.Logger(self.pexpectlog)
	    time.sleep(1)
	    self.child.sendline('export TERM=xterm-256color')
	    time.sleep(1)
	    self.child.sendline('source ~/.profile')
	    time.sleep(1)
	    self.child.sendline('export PS1="' + self.tclshexp + ' "')
	    time.sleep(1)

	def startRunchannel3_sshtoLocalhost(self):
	    self.child = pexpect.spawn ('ssh mfg@localhost', encoding='utf-8')
	    self.child.logfile = log_modules.Logger(self.pexpectlog)
	    time.sleep(1)
	    self.child.sendline('export TERM=xterm-256color')
	    time.sleep(1)
	    self.child.sendline('source ~/.profile')
	    time.sleep(1)
	    self.child.sendline('export PS1="' + self.tclshexp + ' "')
	    time.sleep(1)

	def startRunchannel_bash(self):
	    self.child = pexpect.spawn ('bash', encoding='utf-8')
	    self.child.logfile = log_modules.Logger(self.pexpectlog)
	    time.sleep(1)
	    self.child.sendline('export TERM=xterm-256color')
	    time.sleep(1)
	    self.child.sendline('source ~/.profile')
	    time.sleep(1)
	    self.child.sendline('export PS1="' + self.tclshexp + ' "')
	    time.sleep(1)


	def startRunchannel_tclsh(self):
	    self.child = pexpect.spawn ('tclsh', encoding='utf-8')
	    self.child.logfile = log_modules.Logger(self.pexpectlog)
	    time.sleep(1)
	    self.child.sendline('export TERM=xterm-256color')
	    time.sleep(1)
	    self.child.sendline('source ~/.profile')
	    time.sleep(1)
	    self.child.sendline("global tcl_prompt1 tcl_prompt2")
	    time.sleep(1)
	    self.child.sendline('set tcl_prompt1 {puts -nonewline "' + self.tclshexp + ' "}')
	    time.sleep(1)
	    self.child.sendline('set tcl_prompt2 {}')
	    time.sleep(1)

	def SetupTestEnv(self):

		output1 = self.send_command_wait_for_output('printenv')
		output1 = self.send_command_wait_for_output('whoami')
		output1 = self.send_command_wait_for_output('pwd')
		output1 = self.send_command_wait_for_output("cd {}".format(self.testdir))
		self.writelineinscriptlog(output1)
		output1 = self.send_command_wait_for_output('pwd')
		self.writelineinscriptlog(output1)
		if not self.testdir in output1:
			message = "\n\[1;91mERR: {} is not exist\[0m\n".format(self.testdir)

			self.writelineinscriptlog(message)
			self.addspecialMessage(message)
			self.child.logfile.write(message)
			self.markfalse = True

			return False
		self.send_command_wait_for_output('sync')

		output1 = self.send_command_wait_for_output(self.runtestCmd,exp_list=["Scan the MTP ID Bar Code","Confirm to continue?"])

		self.writelineinscriptlog(output1)
		if not self.testuut in output1:
			message = "\n\[1;91mERR: {} is not in Test config\[0m\n".format(self.testuut)
			#cmd = "echo {}".format(message)
			self.addspecialMessage(message)
			self.markfalse = True
			self.child.logfile.write(message)
			self.child.send(chr(3))
			return False

		output1 = self.send_command_wait_for_output(self.testuut,exp_list=["Selected"])
		self.writelineinscriptlog(output1)

		return True

	def STOPTest(self):
		self.child.send(chr(3))
		Timeoutcount = 10
		for x in range(5):
			self.index = self.runtest_expect([self.tclshexp], timeout=Timeoutcount)
			if self.index == 0:
				break
			self.child.send(chr(3))
		return None

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

		return True	

	def checkoutputstatus(self,theend=False):
		start=datetime.now()
		resultindict = dict()
		for keystatus in RUN_KEY.checkstatus:
			if not theend:
				if keystatus == "FIND_MTP_FAIL":
					continue
			sub_match = re.findall(RUN_KEY.checkstatus[keystatus].format(self.testuut), self.output)
			if sub_match:
				print("keystatus: {}".format(keystatus))
				print(sub_match)
				resultindict[keystatus] = sub_match

		difftime = datetime.now()-start
		print('Done Time: ', difftime)
		self.writelineinscriptlog("checkoutputstatus: {} seconds".format(difftime.total_seconds()))
		return resultindict

	def send_command_wait_for_output(self, command, exp_list=None, timeout=None):
		self.clear_buffer()
		_exp_list = list()
		_exp_list.append(self.tclshexp)
		if exp_list:
			_exp_list = _exp_list[:] + exp_list[:]

		self.child.sendline(command)

		index = self.runtest_expect(_exp_list, timeout=timeout)
		return_output = ""
		if index >= 0:
			return_output = str(self.child.before) + str(self.child.after) + str(self.child.buffer)

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
		except pexpect.exceptions.TIMEOUT as toe:
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