#!/bin/bash
slot=($1)

declare -a addr=(0x00000000 \
                 0x00010000 \
                 0x00020000 \
                 0x00030000 \
                 0x00040000 \
                 0x00050000 \
                 0x00060000 \
                 0x00070000 \
                 0x00080000 \
                 0x00090000 \
                 0x000a0000 \
                 0x000b0000 \
                 0x000c0000 \
                 0x000d0000 \
                 0x000e0000 \
                 0x000f0000)

turn_on_slot.sh off $slot
sleep 3
turn_on_slot.sh on $slot 0 0
sleep 3

for i in ${!addr[*]}
do
    echo "Erasing address  ${addr[$i]}"
    fpgautil flash $slot 1 sectorerase ${addr[$i]}
    if [ $? != 0 ]
    then
    echo "Erasing address  ${addr[$i]} FAILED"
    exit 1
    fi 
done    

