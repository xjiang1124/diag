# !/bin/bash
ftdi_addr=("0" "0x1021" "0x1022" "0x1031" "0x1032" "0x1041" "0x1042" "0x1051" "0x1052" "0x1081" "0x1082")

res=$(smbutil -uut=uut_$1 -dev=CPLD -rd -addr=0x80)
IFS=';'
read -ra reg <<< "$res"
IFS='='
read -ra data <<< "${reg[1]}"
if [ $1 -eq 10 ]
then
    portnum=0xa
else
    portnum=$1
fi

if [[ $MTP_TYPE == "MTP_ELBA" ]] 
then
    printf "====== jtag_cpurd_v2 ======\n"
    #jtag_cpurd_v2 rst 0xa $portnum
    #jtag_cpurd_v2 ena 0xa $portnum
    #jtag_cpurd_v2 rd  0xa $portnum 0x307c0000 2
elif [[ $MTP_TYPE == "MTP_TURBO_ELBA" ]] 
then
    printf "====== jtag_cpurd_v2 turbo ======\n"
    #jtag_cpurd_v2 rst ${ftdi_addr[$portnum]} 1
    #jtag_cpurd_v2 ena ${ftdi_addr[$portnum]} 1
    #jtag_cpurd_v2 rd  ${ftdi_addr[$portnum]} 1 0x307c0000 2
else
    printf "====== jtag_cpurd_debug ======\n"
    jtag_cpurd_debug rst 0xa $portnum 
    jtag_cpurd_debug ena 0xa $portnum
    jtag_cpurd_debug rd  0xa $portnum 0x6a000000 2
fi

printf "\n====== lsusb ======\n"
lsusb

printf "\n====== ls -l /dev/bus/usb/001 ======\n"
ls -l /dev/bus/usb/001


