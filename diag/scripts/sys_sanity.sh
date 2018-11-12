# !/bin/bash

printf "====== jtag_cpurd_debug ======\n"
if [ $1 -eq 10 ]
then
    jtag_cpurd_debug rst 0xa 0xa
    jtag_cpurd_debug ena 0xa 0xa
    jtag_cpurd_debug rd  0xa 0xa 0x6a000000 2
else
    jtag_cpurd_debug rst 0xa $1
    jtag_cpurd_debug ena 0xa $1
    jtag_cpurd_debug rd  0xa $1 0x6a000000 2
fi

printf "\n====== lsusb ======\n"
lsusb

printf "\n====== ls -l /dev/bus/usb/001 ======\n"
ls -l /dev/bus/usb/001


