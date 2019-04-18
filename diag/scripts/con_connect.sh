# !/bin/bash

cpldutil -cpld-wr -addr=0x18 -data=0
cpldutil -cpld-wr -addr=0x18 -data=$1

picocom -b 4800 -f h /dev/ttyS1

