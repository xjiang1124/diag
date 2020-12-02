# !/bin/bash

printf "====== jtag_cpurd_debug ======\n"
mtp_id_cmd=$(cpldutil -cpld-rd -addr=0x80)
mtp_id_str=($mtp_id_cmd)
mtp_id=${mtp_id_str[-1]}
if [ $1 -eq 10 ]
then
    portnum=0xa
else
    portnum=$1
fi

if [ $mtp_id == "0x42" ]
then
    jtag_cpurd_v2 rst 0xa $portnum
    jtag_cpurd_v2 ena 0xa $portnum
    jtag_cpurd_v2 rd  0xa $portnum 0x307c0000 2
else
    jtag_cpurd_debug rst 0xa $portnum 
    jtag_cpurd_debug ena 0xa $portnum
    jtag_cpurd_debug rd  0xa $portnum 0x6a000000 2
fi

printf "\n====== lsusb ======\n"
lsusb

printf "\n====== ls -l /dev/bus/usb/001 ======\n"
ls -l /dev/bus/usb/001


