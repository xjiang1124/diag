#!/bin/bash
slot=($1)

declare -a addr=(0x00020000 \
                 0x00030000)

declare -a image=(/home/diag/diag/python/esec/images/binaries/sal_softrom_43.img \
                  /home/diag/diag/python/esec/images/binaries/sal_softrom_43.img)

turn_on_slot.sh off $slot
sleep 3
turn_on_slot.sh on $slot 0 0
sleep 3

for i in ${!addr[*]}
do
    echo "Programming softROM  ${addr[$i]} ${image[$i]}"
    fpgautil flash $slot 1 writefile ${addr[$i]} ${image[$i]}
    if [ $? != 0 ]
    then
    echo "IMG PROG FAILED"
    exit 1
    fi 
    echo "IMG PROG PASSED"
done    
