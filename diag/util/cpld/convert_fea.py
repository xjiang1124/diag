#!/usr/bin/env python
import sys
from array import *

bin_array = array('B')
filename = sys.argv[1]
cfgfile = filename[:filename.find('.')] + "_fea.bin"

with open (filename) as f:
    lines = f.readlines()
    begin = lines.index('DATA:\r\n')
    end = begin + 2
    for j in range(begin + 1, end):
        s = lines[j]
        for i in range(16):
            bin_array.append(int((s[i*8 : (i+1)*8]), 2))
f = file(cfgfile, 'wb')
bin_array.tofile(f)
f.close()

