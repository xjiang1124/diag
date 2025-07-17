#!/bin/bash

if [[ $MTP_TYPE != "MTP_MATERA" && $MTP_TYPE != "MTP_PANAREA" ]]; then
    killall picocom
    exit 0

elif [[ $MTP_TYPE == "MTP_MATERA" || $MTP_TYPE == "MTP_PANAREA" ]]; then
    SLOT=$(expr $1 - 1)
    sudo fuser -k /dev/shm/uart${SLOT} >> /dev/null
    sudo rm /dev/shm/uart${SLOT}
    echo "Killed uart to slot $1. Use 'reset' command to fix terminal screen."
fi

exit 0
