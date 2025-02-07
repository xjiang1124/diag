#!/bin/bash
slot=($1)

turn_on_slot.sh off $slot
sleep 3
turn_on_slot.sh on $slot 0 0
sleep 3

fpgautil flash $slot 1 sectorerase all
if [ $? != 0 ]
then
    echo "Erasing QSPI of slot $slot FAILED"
    exit 1
fi

