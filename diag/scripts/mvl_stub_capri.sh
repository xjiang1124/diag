#!/bin/bash

if [[ $1 == "0" ]]; then
    echo "setting up internal loopback"
    ./cpld -smiwr 0x16 0x3 0x0
    sleep 1
    ./cpld -smiwr 0x00 0x03 0x4000
    sleep 1
    if [[ $2 == "2" ]]; then
        echo "setting up internal loopback on second port"
        ./cpld -smiwr 0x16 0x4 0x0
        sleep 1
        ./cpld -smiwr 0x00 0x04 0x4000
        sleep 1
    fi
fi

./cpld -smiwr 0x16 0x3 0x06
sleep 1
./cpld -smiwr 0x12 0x3 0x18
sleep 1
./cpld -smiwr 0x10 0x3 0x18
sleep 1
p0=$(./cpld -smird 0x11 0x3)
sleep 1
p1=$(./cpld -smird 0x11 0x3)
echo $p0 $p1

if [[ $(( p0 & 0xff00 )) -eq 0 ]]; then
    echo $p0 
    echo "MVL STUB TEST FAILED on port 1 -- no packet received"
    exit 1
fi

if [[ $(( p1 & 0xff00 )) -ne 0xff00 ]]; then
    echo $p0 
    echo "MVL STUB TEST FAILED on port 1 -- packet count not expected"
    exit 1
fi

if [[ $(( $p0 & 0xff )) -lt $(( $p1 & 0xff )) ]]; then
    echo "MVL STUB TEST FAILED on port 1 -- packets with errors"
    exit 1
fi

if [[ $(( $p0 & 0xff )) -eq 0xff ]]; then
    echo "MVL STUB TEST FAILED on port 1 -- max errors reached"
    exit 1
fi

if [[ $2 == "2" ]]; then
    ./cpld -smiwr 0x16 0x4 0x06
    sleep 1
    ./cpld -smiwr 0x12 0x4 0x18
    sleep 1
    ./cpld -smiwr 0x10 0x4 0x18
    sleep 1
    p0=$(./cpld -smird 0x11 0x4)
    sleep 1
    p1=$(./cpld -smird 0x11 0x4)
    echo $p0 $p1

    if [[ $(( p0 & 0xff00 )) -eq 0 ]]; then
        echo $p0 
        echo "MVL STUB TEST FAILED on port 2 -- no packet received"
        exit 1
    fi

    if [[ $(( p1 & 0xff00 )) -ne 0xff00 ]]; then
        echo $p0 
        echo "MVL STUB TEST FAILED on port 2 -- packet count not expected"
        exit 1
    fi

    if [[ $(( $p0 & 0xff )) -lt $(( $p1 & 0xff )) ]]; then
        echo "MVL STUB TEST FAILED on port 2 -- packets with errors"
        exit 1
    fi

    if [[ $(( $p0 & 0xff )) -eq 0xff ]]; then
        echo "MVL STUB TEST FAILED on port 2 -- max errors reached"
        exit 1
    fi
fi

./cpld -smiwr 0x10 0x3 0x0
./cpld -smiwr 0x12 0x3 0x0
./cpld -smiwr 0x16 0x3 0x0
./cpld -smiwr 0x10 0x4 0x0
./cpld -smiwr 0x12 0x4 0x0
./cpld -smiwr 0x16 0x4 0x0

if [[ $1 == "0" ]]; then
    ./cpld -smiwr 0x16 0x03 0x00
    ./cpld -smiwr 0x00 0x03 0x00
    ./cpld -smiwr 0x16 0x04 0x00
    ./cpld -smiwr 0x00 0x04 0x00
fi

echo "MVL STUB TEST PASSED"
   
