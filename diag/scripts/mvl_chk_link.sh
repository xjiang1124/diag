#!/bin/bash

p0=$(./xo3dcpld -smird 0x11 0x3)
p1=$(./xo3dcpld -smird 0x11 0xC)
p2=$(./xo3dcpld -smird 0x11 0xD)
echo $p0 $p1 $p2

if [[ $(( p0 & 0x0400 )) -eq 0 ]]; then
    echo "MVL RJ45 port link is down"
else
    echo "MVL RJ45 port link is up"
fi

if [[ $(( p1 & 0x0400 )) -eq 0 ]]; then
    echo "MVL ELBA port link is down"
else
    echo "MVL ELBA port link is up"
fi

if [[ $(( p2 & 0x0400 )) -eq 0 ]]; then
    echo "MVL MTP port link is down"
else
    echo "MVL MTP port link is up"
fi

