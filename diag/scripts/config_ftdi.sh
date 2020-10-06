#!/bin/bash

rmmod ftdi_sio

bus=$(lsusb | grep "Future Technology"|  awk -F " " '{print $2}')
dev=$(lsusb | grep "Future Technology"|  awk -F " " '{print $4}')

dev=${dev%?}

echo "Found FTDI at bus $bus; dev $dev"

chmod ugo+rw /dev/bus/usb/$bus/$dev
