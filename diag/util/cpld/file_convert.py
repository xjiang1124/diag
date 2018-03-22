#!/usr/bin/env python
import sys
from array import *

bin_array = array('B')
#filename = "MTP_IO_BB_impl1.jed"
filename = sys.argv[1]

max_row = 2175

with open (filename) as f:
    lines = f.readlines()
    begin = lines.index('L000000\r\n')
    end = lines.index('*\r\n')
    #for j in range(begin + 1, end):
    for j in range(begin + 1,begin + max_row + 1):
        if j < end:
            s = lines[j]
            for i in range(16):
                #print s[i*8 : (i+1)*8]
                bin_array.append(int((s[i*8 : (i+1)*8]), 2))
        else:
            for i in range(16):
                bin_array.append(0)


#f = file('binary', 'wb')
f = file(sys.argv[2], 'wb')
bin_array.tofile(f)
f.close()
