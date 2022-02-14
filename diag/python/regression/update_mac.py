# !/usr/bin/python

import os
from os import walk
import re
import shutil
import subprocess
import sys

src_path = '/platform/etc/nicmgrd/'
input_path = '/mnt'

src_files = os.listdir(src_path)
r = re.compile('.*json$')
src_files = filter(r.match, src_files)

for file_name in src_files:
    full_file_name = os.path.join(src_path, file_name)
    if (os.path.isfile(full_file_name)):
          shutil.copy(full_file_name, input_path)

#subprocess.Popen(["cp", "/platform/etc/nicmgrd/*json", input_path], stdout=subprocess.PIPE).communicate()[0]

filenames = [f for f in os.listdir(input_path) if os.path.isfile(f)]
print filenames

output = subprocess.Popen(["./eeutil", "-disp", "-field=mac"], stdout=subprocess.PIPE).communicate()[0]
print output

r = re.compile('.*([0-9,a-f][0-9,a-f])-([0-9,a-f][0-9,a-f])-([0-9,a-f][0-9,a-f])-([0-9,a-f][0-9,a-f])-([0-9,a-f][0-9,a-f])-([0-9,a-f][0-9,a-f]).*')
m = r.match(output)
if m:
    mac_str = m.group(1)+m.group(2)+m.group(3)+m.group(4)+m.group(5)+m.group(6)
    print mac_str
else:
    print "Can not fine mac from FRU"
    sys.exit(0)

mac_int = int(mac_str, 16)
empty_mac = "000000000000"
tgt_mac_list_temp = []
for i in range(5):
    mac_str = '{:02x}'.format(mac_int)
    tgt_mac = empty_mac[0:12-len(mac_str)]+mac_str
    tgt_mac_list_temp.append(tgt_mac)
    mac_int = mac_int+1

tgt_mac_list = []
for i in range(5):
    tgt_mac_temp = tgt_mac_list_temp[i]
    tgt_mac = tgt_mac_temp[0:2]+":"+tgt_mac_temp[2:4]+":"+tgt_mac_temp[4:6]+":"+tgt_mac_temp[6:8]+":"+tgt_mac_temp[8:10]+":"+tgt_mac_temp[10:]
    tgt_mac_list.append(tgt_mac)
print tgt_mac_list

r = re.compile('.*json$')
files_json = filter(r.match, filenames)
org_mac = ["00:02:00:00:01:01", "00:02:00:00:01:02", "00:02:00:00:01:03", "00:02:00:00:01:04", "00:02:00:00:01:05"]
for filename in files_json:
    print "Processing", filename
    with open(filename) as f:
        s = f.read()

    for i in range(len(org_mac)):
        if org_mac[i] in s:
            s = s.replace(org_mac[i], tgt_mac_list[i])

    with open(filename, 'w') as f:
        f.write(s)
            
subprocess.Popen(["sync"], stdout=subprocess.PIPE).communicate()[0]


