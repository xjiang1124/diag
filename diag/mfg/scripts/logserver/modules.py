#!/usr/bin/python3

import warnings
import openpyxl
import os
import sys
import time
import glob
import os.path
from os import path
import datetime
import re
import json
import mpu.io
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import timeit
from datetime import datetime
import dateutil.relativedelta
from statistics import mean 
import statistics
import pandas as pd
#import mysql_202009_db
import math
import csv
import operator
from collections import OrderedDict
#import opsfs_mail
#import modules
import socket
#import script_logging
import gzip
import shutil
import yaml

from datetime import date

today = date.today()
# dd/mm/YY
todayday = today.strftime("%Y/%m/%d")
print("todayday =", todayday)

from datetime import datetime

now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d_%H%M%S")
print("date and time:",date_time)
defecttmpfolder = "/logs/arubadashbroad"

class modules(object):
	def __init__(self, logfile=None):
		self.debug = True
		self.logfile = None
		if logfile:
			self.logfile = logfile
		self.debug_print("Start modules...")


	def readjsonfile(self,jsonfile):
		start=datetime.now()
		outputdict = dict()

		if os.path.exists(jsonfile):
			outputdict = mpu.io.read(jsonfile)

		difftime = datetime.now()-start
		self.debug_print("readjsonfile: {} use {} seconds".format(jsonfile,difftime.total_seconds()))

		return outputdict

	def readyamltodict(self, yamlfile):
		with open(yamlfile) as file:
		    # The FullLoader parameter handles the conversion from YAML
		    # scalar values to Python the dictionary format
		    yamldict = yaml.load(file, Loader=yaml.FullLoader)

		    #self.print_anyinformation(yamldict)

		return yamldict

	def wirtedicttoyaml(self, yamldict, yamlfile):
		with open(yamlfile, 'w') as file:
		    documents = yaml.dump(yamldict, file)

		    #self.print_anyinformation(documents)
		return None

	def checkDirectoryexist(self, checkDir):
	    for DirName in checkDir.keys():
	        #print(DirName)
	        #print(checkDir[DirName])
	        #print(os.path.isdir(checkDir[DirName]))
	        if "testlogpath" in DirName:
	            continue
	        self.createdirinserver(checkDir[DirName])

	    return None

	def createdirinserver(self, createdir):
	    mode = 0o777
	    if not os.path.isdir(createdir):
	        #os.mkdir(createdir, mode)
	        os.makedirs(createdir, exist_ok=True)
	        self.debug_print("Directory '% s' created" % createdir)

	    return None


	def getallfilebyfolder(self,rootdir,keyword=None,level=None):

	    listofdirs = self.getallfolder(rootdir,keyword=keyword,level=level)

	    listoffiles = list()

	    for eachdir in listofdirs:
	        somelists = glob.glob(eachdir + '/*')
	        for something in somelists:
	            if os.path.isfile(something):  
	                basename = os.path.basename(something)
	                if keyword:
	                    if not keyword.upper() in basename.upper():
	                        continue
	                if not something in listoffiles:
	                    listoffiles.append(something)

	    listoffiles.sort()

	    #print(json.dumps(listoffiles, indent = 4))

	    return listoffiles

	def getallfolder(self,rootdir,keyword=None,level=None):

	    listofdirs = list()

	    listofdirs.append(rootdir)

	    stillhavedir = True

	    count = 1
	    #print(level)

	    while stillhavedir:
	        
	        if level:
	            #print(json.dumps(listofdirs, indent = 4))
	            if count >= level:
	                break
	        stillhavedir = False
	        resultlist = list()         

	        for checkdir in listofdirs:
	            somelists = glob.glob(checkdir + '/*')
	            #print("COUNT: {} DIR: {} STILLHAVE: {}".format(count,checkdir,stillhavedir))
	            for something in somelists:
	                if os.path.isdir(something):
	                    if not something in listofdirs:
	                        stillhavedir = True
	                        resultlist.append(something)
	        #print("COUNT: {} TOTAL resultlist: {} STILLHAVE: {}".format(count,len(resultlist), stillhavedir))
	        for eachdir in resultlist:
	            if not eachdir in listofdirs:
	                listofdirs.append(eachdir)

	        #print("COUNT: {} TOTAL listofdirs: {} STILLHAVE: {}".format(count,len(listofdirs), stillhavedir))
	        count += 1

	    #print("LEVEL: {}".format(level))

	    return listofdirs

	def fixcolumnssize(self,ws):
		dims = {}
		for row in ws.rows:
			for cell in row:
				if cell.value:
					dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), len(str(cell.value))))  
		for col, value in dims.items():
			usevalue = value
			if value > 100:
				usevalue = 100
			ws.column_dimensions[col].width = usevalue + 2

		ws.auto_filter.ref = ws.dimensions
		return None

	def highlightinyellownumber(self,ws):
		from openpyxl.styles import Color, PatternFill, Font, Border
		maxRow = ws.max_row
		maxCol = ws.max_column
		#print('highlightinyellow: ' + keyword + ' ' + str(maxRow) + ' ' + str(maxCol))
		for rowNum in range(1, maxRow + 1):
			fillcolor = 0
			for colNum in range(1, maxCol + 1):
				#print(str(rowNum) + ' ' + str(colNum) + ' ' + str(ws.cell(row=rowNum, column=colNum).value))
				if str(ws.cell(row=rowNum, column=colNum).value).isnumeric():
					if int(ws.cell(row=rowNum, column=colNum).value) > 0:
						if colNum < 3:
							continue
						ws.cell(row=rowNum, column=colNum).fill = PatternFill(start_color='FFEE08', end_color='FFEE08', fill_type = 'solid')
		return 0

	def readSNxlsxfile(self,xlsxfile,SNvsPCBA):
		from openpyxl import load_workbook
		self.debug_print("FILE: {}".format(xlsxfile))
		wb_sn = load_workbook(filename = xlsxfile)
		for tabname in wb_sn.sheetnames:
			self.debug_print("tabname: {}".format(tabname))
			eachsheet = wb_sn[tabname]
			SNraw, SNcolunm = self.findposition(eachsheet,'SN')
			PCBAsnraw, PCBAsncolunm = self.findposition(eachsheet,'PCBA_SN')

			self.debug_print("SN: Raw {} Colunm {} | PCBA_SN: Raw {} Colunm {}".format(SNraw, SNcolunm, PCBAsnraw, PCBAsncolunm))

			if SNraw and PCBAsnraw:
				colunm = eachsheet['A']
				for countnumberinrow in range(2,len(colunm)+1):
					SN = str(eachsheet.cell(row=countnumberinrow, column=SNcolunm).value)
					PCBA_SN = str(eachsheet.cell(row=countnumberinrow, column=PCBAsncolunm).value)
					self.debug_print("SN: {} | PCBA_SN: {}".format(SN, PCBA_SN))
					SNvsPCBA[SN] = PCBA_SN		

		return None

	def findposition(self,sheet,keyword):

		colunm = sheet[1]
		raw = sheet['A']

		for rawnumber in range(1,len(raw)+1):
			for colunmnumber in range(1,len(colunm)+1):
				if keyword == sheet.cell(row=rawnumber, column=colunmnumber).value:
					return rawnumber, colunmnumber
		return None, None

	def gzip_to_file(self, sourcefile):

		self.debug_print("Current {} FileSize : {}".format(sourcefile,os.path.getsize(sourcefile)))
		returnfile = "{}.gz".format(sourcefile)
		with open(sourcefile, 'rb') as f_in:               	# open original file for reading
			with gzip.open(returnfile, 'wb') as f_out: 		# open gz file for writing
				shutil.copyfileobj(f_in, f_out)           	# write/copy text file into gz file

		if os.path.exists(returnfile):
			self.debug_print("ZIPFILE {} FileSize : {}".format(returnfile,os.path.getsize(returnfile)))
			if os.path.exists(sourcefile):
				self.debug_print("Process to remove FILE : {}".format(sourcefile))
				os.remove(sourcefile)
			else:
				self.debug_print("The file {} does not exist".format(sourcefile))

		return returnfile

	def debug_print(self,msg):
		if self.debug:
			
			if self.logfile:
				self.logfile.WriteLine(str(msg))
			else:
				print(msg)
		return None

	def check_is_module_class(self,inputdata):
		m = re.findall(r'\'(.*)\'', str(type(inputdata)))
		if m:
			#print(m)
			mlist = m[0].lower().split('.')
			#print(mlist)
			#print(len(mlist))
			if len(mlist) == 2:
				if mlist[0] == mlist[1]:
					return True
		if 'object at' in str(inputdata):
			return True

		return False

	def print_anyinformation(self,inputdata):
		countlevel=0
		self.debug_print("")
		specenumber = "\t"
		if countlevel:
			for n in range(countlevel):
				specenumber += "\t"
		if isinstance(inputdata, dict):
			self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <DICT>".format(countlevel,specenumber,inputdata,type(inputdata)))
			self.print_dict(inputdata,countlevel+1)
		elif isinstance(inputdata, list):
			self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <LIST>".format(countlevel,specenumber,inputdata,type(inputdata)))
			self.print_list(inputdata,countlevel+1)
		elif self.check_is_module_class(inputdata):
			self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <CLASS>".format(countlevel,specenumber,inputdata,type(inputdata)))
			self.print_dict(inputdata.__dict__,countlevel+1)				
		else:
			self.debug_print("[{}]{}\t{}\t<TYPE:{}>".format(countlevel,specenumber,inputdata,type(inputdata)))		

	def print_dict(self,dictdata,countlevel=0):
		specenumber = "\t"
		if countlevel:
			countlevelspacenumber = countlevel
			if countlevel > 5:
				countlevelspacenumber = 5
			for n in range(countlevelspacenumber):
				specenumber += "\t"

		for x, y in dictdata.items():
			if countlevel > 100:
				self.debug_print("[{}]{}{}\t=\t{}\t<TYPE:{}>".format(countlevel,specenumber,x,y,type(y)))
				return None
			if isinstance(y, dict):
				self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <DICT>".format(countlevel,specenumber,x,type(x)))
				self.print_dict(y,countlevel+1)
			elif isinstance(y, list):
				self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <LIST>".format(countlevel,specenumber,x,type(x)))
				self.print_list(y,countlevel+1)
			elif self.check_is_module_class(y):
				self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <CLASS>".format(countlevel,specenumber,x,type(x)))
				self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <CLASS>".format(countlevel,specenumber,y,type(y)))
				self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <CLASS>".format(countlevel,specenumber,y.__class__,type(y.__class__)))
				self.print_dict(y.__dict__,countlevel+1)				
			else:
				self.debug_print("[{}]{}{}\t=\t{}\t<TYPE:{}>".format(countlevel,specenumber,x,y,type(y)))
		return None

	def print_list(self,listdata,countlevel=0):
		specenumber = "\t"
		if countlevel:
			countlevelspacenumber = countlevel
			if countlevel > 5:
				countlevelspacenumber = 5
			for n in range(countlevelspacenumber):
				specenumber += "\t"

		for x in listdata:
			if countlevel > 100:
				self.debug_print("[{}]{}{}\t<TYPE:{}>".format(countlevel,specenumber,x,type(x)))
				return None
			if isinstance(x, list):
				self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <LIST>".format(countlevel,specenumber,x,type(x)))
				self.print_list(x,countlevel+1)
			elif isinstance(x, dict):
				self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <DICT>".format(countlevel,specenumber,x,type(x)))
				self.print_dict(x,countlevel+1)
			elif self.check_is_module_class(x):
				self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <CLASS>".format(countlevel,specenumber,x,type(x)))
				self.debug_print("[{}]{}\"{}\"\t<TYPE:{}> : <CLASS>".format(countlevel,specenumber,x.__class__,type(x.__class__)))
				self.print_dict(x.__dict__,countlevel+1)
			else:
				self.debug_print("[{}]{}{}\t<TYPE:{}>".format(countlevel,specenumber,x,type(x)))

	def print_json(self,printoutput):

		self.debug_print(json.dumps(printoutput, indent = 4))
		return None

	def print_json_str_only(self,printoutput):
		for eachkey in printoutput:
			recordline = '[{}] : {} ({})'.format(eachkey,printoutput[eachkey],type(printoutput[eachkey]))
			self.debug_print(recordline)
		return None	

	def return_json(self,printoutput):
		return json.dumps(printoutput, indent = 4)

	def getbasename(self,path):
		return os.path.basename(path)

	def checkfilelistkeywork(self,filelist,keyword=None):
		newfilelist = list()
		for eachfile in filelist:
			basename = os.path.basename(eachfile)
			if keyword:
				if not keyword.upper() in basename.upper():
					continue
				if not eachfile in newfilelist:
					newfilelist.append(eachfile)
		newfilelist.sort()
		self.filelist = newfilelist

		self.debug_print(json.dumps(self.filelist, indent = 4))

		return newfilelist		

	def checkandcreatedit(self,pathdir):
		from pathlib import Path
		Path(pathdir).mkdir(parents=True, exist_ok=True)

	def _removeNonAscii(self,s): return "".join(i for i in s if ord(i)<128)

	def _keepnumberandsomestamps(self,s): return "".join(i for i in s if ord(i)<65)

	def _removespace(self,s): return "".join(i for i in s if ord(i)!=32)

	def _removeenter(self,s): return "".join(i for i in s if ord(i)!=12)

	def _onlykeepword(self,s): return "".join(i for i in s if (ord(i)>=48 and ord(i)<=57) or (ord(i)>=97 and ord(i)<=122) or (ord(i)>=65 and ord(i)<=90) or ord(i)==32 or ord(i)==45)

	def _remove47(self,s): return "".join(i for i in s if ord(i)!=47 and ord(i)!=43 and ord(i)!=58 and ord(i)!=33)