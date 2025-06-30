#!/bin/bash
slot=($1)

declare -a addr=(0x00040000 \
                 0x00060000 \
                 0x00080000 \
                 0x000A0000 \
                 0x00010000)

declare -a image=(/home/diag/diag/python/esec/images/binaries/sal_pentrustfw_43.img \
                  /home/diag/diag/python/esec/images/binaries/sal_pentrustfw_43.img \
                  /home/diag/diag/python/esec/images/binaries/sal_boot_nonsec_43.img \
                  /home/diag/diag/python/esec/images/binaries/sal_boot_nonsec_43.img \
                  /home/diag/diag/python/esec/images/binaries/esecure_fw_ptr.bin)

turn_on_slot.sh off $slot
sleep 3
turn_on_slot.sh on $slot 0 0
sleep 3

for i in ${!addr[*]}
do
    echo "Programming dice img ${addr[$i]} ${image[$i]}"
    fpgautil flash $slot 1 writefile ${addr[$i]} ${image[$i]}
    if [ $? != 0 ]
    then
    echo "DICE IMG PROG FAILED"
    exit 1
    fi 
    echo "DICE IMG PROG PASSED"
done    
