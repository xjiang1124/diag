#!/bin/bash

./xo3dcpld -smiwr 0x16 0x3 0x06
sleep 1
./xo3dcpld -smiwr 0x12 0x3 0x18
sleep 1
./xo3dcpld -smiwr 0x10 0x3 0x18
sleep 1
p0=$(./xo3dcpld -smird 0x11 0x3)
sleep 1
p1=$(./xo3dcpld -smird 0x11 0x3)
echo $p0 $p1

if [[ $(( p0 & 0xff00 )) == 0 ]]; then
    echo $p0 
    echo "MVL STUB TEST FAILED -- no packet received"
    exit 1
fi

if [[ $(( $p0 & 0xff )) -lt $(( $p1 & 0xff )) ]]; then
    echo "MVL STUB TEST FAILED -- packets with errors"
    exit 1
fi

if [[ $(( $p0 & 0xff )) -eq 0xff ]]; then
    echo "MVL STUB TEST FAILED -- max errors reached"
    exit 1
fi

./xo3dcpld -smiwr 0x10 0x3 0x0
./xo3dcpld -smiwr 0x12 0x3 0x0
./xo3dcpld -smiwr 0x16 0x3 0x0

echo "MVL STUB TEST PASSED"
   
