#!/bin/bash

if [[ $MTP_TYPE != "MTP_MATERA" ]]; then
    killall picocom
    exit 0

elif [[ $MTP_TYPE == "MTP_MATERA" ]]; then
    SLOT=$(expr $1 - 1)
    pid=$(ps aux | grep "fpga_uart $SLOT" | grep -v "grep" | head -n1 | awk '{print $2}')
    if [[ ! -z $pid ]]; then
        kill -9 $pid
        echo "Killed uart to slot $1. Use 'reset' command to fix terminal screen."
    fi
    sudo rm /dev/shm/uart${SLOT}
fi

exit 0