#!/bin/bash

for type in IO JTAG
do
    for((n = 0x10; n <= 0x15; n++))
    {
        cpldutil -type=$type -phy=$n -mvl-wr -addr=0x1 -data=0x003e
        cpldutil -type=$type -phy=$n -mvl-wr -addr=0x4 -data=0x77 
    }
done

cpldutil -type=JTAG -phy=0x19 -mvl-wr -addr=0x1 -data=0x003e
cpldutil -type=JTAG -phy=0x19 -mvl-wr -addr=0x4 -data=0x77

exit 0
