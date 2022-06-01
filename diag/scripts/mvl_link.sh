#!/bin/bash

p0=$(./xo3dcpld -smird 0 0x3)
p1=$(( $p0 & 0xCFBF ))
p1=$(( $p1 | 0x2000 ))
./xo3dcpld -smiwr 0 0x3 $p1
p2=$(./xo3dcpld -smird 0 0x3)
sleep 10
p3=$(./xo3dcpld -smird 0x11 0x3)
printf "0x%x 0x%x 0x%x 0x%x\n" $p0 $p1 $p2 $p3

if [[ $(( $p3 & 0x0400 )) -eq 0 ]]; then
    echo "MVL RJ45 port link is down"
    echo "MVL RJ45 port link is down"
else
    echo "MVL RJ45 port link is up"
    echo "MVL RJ45 port link is up"
fi
./xo3dcpld -smiwr 0 0x3 $p0
