#!/bin/bash
slot=($1)

declare -a addr=( \
                 0x08000000 \
                 0x09e00000 \
                 0x00140000 \
                )
declare -a partition=( \
                 zephyr_mainfwa.img \
                 zephyr_mainfwb.img \
                 zephyr_goldfw.img \
                )

turn_on_slot.sh off $slot
sleep 10
turn_on_slot.sh on $slot 0 0
sleep 3

for i in ${!addr[*]}
do
    fpgautil flash $slot 1 generatefile ${addr[$i]} 0x01e00000 slot${slot}_${partition[$i]}
    if [ $? != 0 ]
    then
	echo "Saving content from address ${addr[$i]} FAILED"
    exit 1
    fi 
done
for i in ${!addr[*]}
do
    fpgautil flash $slot 1 sectorerase ${addr[$i]}
    if [ $? != 0 ]
    then
	echo "Erasing address ${addr[$i]} FAILED"
    exit 1
    fi 
done    

echo "QSPI ERASE PASSED"
