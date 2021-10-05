#!/bin/bash

if lsmod | grep "ftdi_sio" &> /dev/null; then
    rmmod ftdi_sio
fi
if lsmod | grep "usbserial" &> /dev/null; then
    rmmod usbserial
fi

lsusb | while read line; do if [[ $line == *"Future"* ]]; then IFS=' ' read -ra dev <<< $line;echo "Found FTDI at bus ${dev[1]} dev ${dev[3]:0:3}";chmod ugo+rw /dev/bus/usb/${dev[1]}/${dev[3]:0:3};cnt=$((cnt+1));fi; done;
cnt=$(lsusb | grep -o "Future" | wc -l)
echo "# FTDI DEVICE COUNT" $cnt >> temp_profile

if [ -f "/home/diag/diag/tools/libacc.so" ]; then
    rm /home/diag/diag/tools/libacc.so
fi

if [[ $cnt -eq 1 ]]; then
    echo "Non-Turbo MTP found"
    ln -s /home/diag/diag/tools/libacc_mtp.so /home/diag/diag/tools/libacc.so
else 
    echo "Turbo MTP found"
    ln -s /home/diag/diag/tools/libacc_turbo.so /home/diag/diag/tools/libacc.so
fi
