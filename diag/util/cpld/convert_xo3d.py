#!/usr/bin/env python
import sys
from array import *

bin_array = array('B')
ufm_array = array('B')
image_number = sys.argv[1]
filename = sys.argv[2]
cfgfile = sys.argv[3] + "_cfg" + sys.argv[1] + ".bin"
ufmfile = sys.argv[3] + "_ufm" + sys.argv[1] + ".bin"
total_page = 0

with open (filename) as f:
    lines = f.readlines()
    begin = lines.index('L0000000\r\n')
    second = lines.index('NOTE EBR_INIT DATA*\r\n')
    third = lines.index('NOTE END CONFIG DATA*\r\n')
    if image_number == "0":
        end = lines.index('NOTE USER MEMORY DATA UFM0*\r\n')
    else:
        end = lines.index('NOTE USER MEMORY DATA UFM1*\r\n')
    ufm_end = lines.index('NOTE User Electronic Signature Data*\r\n')
    for j in range(begin + 1, second -1):
        s = lines[j]
        total_page = total_page + 1
        for i in range(16):
            bin_array.append(int((s[i*8 : (i+1)*8]), 2))
    for j in range(second + 2, third - 1):
        s = lines[j]
        total_page = total_page + 1
        for i in range(16):
            bin_array.append(int((s[i*8 : (i+1)*8]), 2))
    for j in range(third + 2, end - 1):
        s = lines[j]
        total_page = total_page + 1
        if total_page > 12541:
            break;
        for i in range(16):
            bin_array.append(int((s[i*8 : (i+1)*8]), 2))
    for j in range(end + 2, ufm_end - 2):
        s = lines[j]
        for i in range(16):
            ufm_array.append(int((s[i*8 : (i+1)*8]), 2))
f = file(cfgfile, 'wb')
bin_array.tofile(f)
f.close()
f = file(ufmfile, 'wb')
ufm_array.tofile(f)
f.close()

