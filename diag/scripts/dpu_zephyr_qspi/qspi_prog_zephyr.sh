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
    image=$(echo slot${slot}_${partition[$i]})
    fpgautil flash $slot 1 writefile ${addr[$i]} $image 
    if [ $? != 0 ]
    then
        echo "Programming image to address ${addr[$i]} FAILED"
    exit 1
    fi 
done

echo "QSPI PROG PASSED"

