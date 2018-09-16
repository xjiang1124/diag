#!/bin/bash

cpldutil -cpld-rd -addr=0x10
v12=$?
#v12=`printf "0x%x\n" $?`

cpldutil -cpld-rd -addr=0x12
v3v3=$?
#v3v3=`printf "0x%x\n" $?`

cpldutil -cpld-rd -addr=0x16
perst=$?
#perst=`printf "0x%x\n" $?`

bitPos=$(( $2 - 1 ))
bitPos=$(( 1 << $bitPos ))

if [[ "$1" == "on" ]]
then
    echo "Turning on slot $2"
    bitPos=$(( ~$bitPos ))
    bitPos=$(( $bitPos & 0xff ))
    echo "bitPos:"
    printf "0x%x\n" $bitPos
    printf "0x%x\n" $v12
    v12=$(( $v12 & $bitPos ))
    v3v3=$(( $v3v3 & $bitPos ))
    perst=$(( $perst & $bitPos ))

    cpldutil -cpld-wr -addr=0x12 -data=$v3v3
    sleep 1
    cpldutil -cpld-wr -addr=0x10 -data=$v12
    sleep 1
    cpldutil -cpld-wr -addr=0x16 -data=$perst
    sleep 1

    echo "slot $2 turned on"

else
    echo "Turn off slot $2"
    v12=$(( $v12 | $bitPos ))
    v3v3=$(( $v3v3 | $bitPos ))
    perst=$(( $perst | $bitPos ))

    cpldutil -cpld-wr -addr=0x16 -data=$perst
    sleep 1
    cpldutil -cpld-wr -addr=0x10 -data=$v3v3
    sleep 1
    cpldutil -cpld-wr -addr=0x12 -data=$v12
    sleep 1

    echo "slot $2 turned off"
fi

exit

# Turn on all 12v
echo "Turn on all 12v"
cpldutil -cpld-wr -addr=0x10 -data=0x0
cpldutil -cpld-wr -addr=0x11 -data=0x0
sleep 3
# Disable all PERST
echo "Disable all PERST"
cpldutil -cpld-wr -addr=0x16 -data=0x0
cpldutil -cpld-wr -addr=0x17 -data=0x0
sleep 3

