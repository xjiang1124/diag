#!/bin/bash

p0=$(./cpld -smird 0 0x3)
p1=$(( $p0 & 0xCFBF ))
p1=$(( $p1 | 0x2000 ))
./cpld -smiwr 0 0x3 $p1
p2=$(./cpld -smird 0 0x3)
sleep 10
p3=$(./cpld -smird 0x11 0x3)
printf "0x%x 0x%x 0x%x 0x%x\n" $p0 $p1 $p2 $p3

if [[ $(( $p3 & 0x0400 )) -eq 0 ]]; then
    echo "MVL RJ45 port 1 link is down"
else
    echo "MVL RJ45 port 1 link is up"
fi
./cpld -smiwr 0 0x3 $p0

if [[ $1 == "2" ]]; then
    p0=$(./cpld -smird 0 0x4)
    p1=$(( $p0 & 0xCFBF ))
    p1=$(( $p1 | 0x2000 ))
    ./cpld -smiwr 0 0x4 $p1
    p2=$(./cpld -smird 0 0x4)
    sleep 10
    p3=$(./cpld -smird 0x11 0x4)
    printf "0x%x 0x%x 0x%x 0x%x\n" $p0 $p1 $p2 $p3

    if [[ $(( $p3 & 0x0400 )) -eq 0 ]]; then
        echo "MVL RJ45 port 2 link is down"
    else
        echo "MVL RJ45 port 2 link is up"
    fi
./cpld -smiwr 0 0x4 $p0
fi
