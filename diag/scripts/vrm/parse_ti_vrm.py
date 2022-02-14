#!/usr/bin/env python

import argparse
from bs4 import BeautifulSoup
import subprocess
import xmltodict
import xml.etree.ElementTree


parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.RawTextHelpFormatter)
#group = parser.add_mutually_exclusive_group()
parser.add_argument("-cf", "--csvfile", help="csv file of VRM image", type=str, default='')
parser.add_argument("-xf", "--xmlfile", help="xml file of VRM image", type=str, default='')
parser.add_argument("-of", "--outfile", help="Output VRM image name", type=str, default='naples_53659.img')

args = parser.parse_args()

xmlfile = args.xmlfile
csvfile = args.csvfile
outfile = args.outfile

subprocess.call("./create_image.sh "+csvfile, shell=True)

# Write field
prog_table = ['MFR_REVISION']
veri_table = ['MFR_SERIAL']

fmt_str = "{},{},{}\n"
fmt_num_byte = '{:02d}'

with open(xmlfile) as fd:
    doc = xmltodict.parse(fd.read())

param = doc[u'ProjectData'][u'Devices'][u'Device'][u'Parameters'][u'Parameter']

prog_out = []
veri_out = []
for item in param:
    # Check prog list
    for cmd in prog_table:
        if item['ID'] == cmd:
            cmdCode = hex(int(item['Code']))
            cmdType = item['ValueEncoded']['@xsi:type']
            cmdVal = item['ValueEncoded']['@Hex']
            cmdValBlk = cmdVal[:2]+fmt_num_byte.format((len(cmdVal)-2)/2)+cmdVal[2:]

            if cmdType == "PMBusBlock":
                writeCmd = 'BlockWrite'
                readCmd = 'BlockRead'
            writeStr = fmt_str.format(writeCmd, cmdCode, cmdValBlk)
            readStr = fmt_str.format(readCmd, cmdCode, cmdValBlk)
            #print writeStr
            #print readStr
            prog_out.append(writeStr)
            prog_out.append(readStr)


    # Check prog list
    for cmd in veri_table:
        if item['ID'] == cmd:
            cmdCode = hex(int(item['Code']))
            cmdType = item['ValueEncoded']['@xsi:type']
            cmdVal = item['ValueEncoded']['@Hex']
            cmdValBlk = cmdVal[:2]+fmt_num_byte.format((len(cmdVal)-2)/2)+cmdVal[2:]
            print cmdValBlk

            if cmdType == "PMBusBlock":
                readCmd = 'BlockRead'
            readStr = fmt_str.format(readCmd, cmdCode, cmdValBlk)
            veri_out.append(readStr)



with open('naples_53659_pre.img') as f:
    lines = f.readlines()

img = open(outfile, 'w')

for line in lines:
    if 'SendByte,0x11' in line:
        for outStr in prog_out:
            img.write(outStr)
    img.write(line)

for outStr in veri_out:
    img.write(outStr)

img.close()
