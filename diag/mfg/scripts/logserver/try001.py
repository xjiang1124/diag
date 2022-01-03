#!/usr/bin/python3

import re
from logdef import KEY_WORD
import time
from datetime import datetime

x = '''
## [2021-07-21_17-39-27] LOG: [UUT-004]: Power off APC
## [2021-07-21_17-40-01] LOG: [UUT-004]: Power on APC
## [2021-07-21_17-40-33] LOG: [UUT-004]:     Get the "Looking for SvOS" begin Console message
## [2021-07-21_17-41-27] LOG: [UUT-004]: UUT Chassis is connected
## [2021-07-21_17-41-28] LOG: [UUT-004]: Firmware Download Process Started
## [2021-07-21_17-41-28] LOG: [UUT-004]: FSJ21280038 DIAG TEST (DL2, SVOS_BOOT) STARTED
'''

print(x)

match = re.findall(KEY_WORD.FINDDATEANDTIME, x) 

print(match)

print(match[0])

print(match[-1])

starttime = "{}_{}".format(match[0][0], match[0][1])
endtime = "{}_{}".format(match[-1][0], match[1][1])
startdatetime_object = datetime.strptime(starttime, '%Y-%m-%d_%H-%M-%S')
enddatetime_object = datetime.strptime(endtime, '%Y-%m-%d_%H-%M-%S')

print(type(startdatetime_object))
print(startdatetime_object)  # printed in default format

print(type(enddatetime_object))
print(enddatetime_object)  # printed in default format

difftime = enddatetime_object-startdatetime_object
print('Done Time: ', difftime)       
print("How many seconds use?: {} seconds".format(difftime.total_seconds())) 