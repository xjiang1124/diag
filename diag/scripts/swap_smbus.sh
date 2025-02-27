#!/bin/bash

usage="Usage: ${0##*/} <slot_num>"
if [ $# -ne 1 ]
then
    echo $usage
    exit
fi

slot=$1
if [[ $slot -lt 1 || $slot -gt 10 ]];
then
    echo "Invalid slot number. Expected [1,10], entered $slot"
    echo $usage
    exit
fi

uut="UUT_$slot"
cTyp=${!uut}
if [[ -z $cTyp ]];
then
    echo "Env var $uut not defined"
fi
if [[ $cTyp != "MALFA" && $cTyp != "LENI" && $cTyp != "LENI48G" && $cTyp != "POLLARA" $cTyp != "LINGUA" ]];
then
    echo "$uut=$cTyp"
    echo "${0##*/} is only applicable to Salina cards."
    echo $usage
    exit
fi

echo "Warning: smbus is going to swap to NIC side"
echo "         uut power cycle is required to recover!!!"

curVal=$(i2cget -y $(($slot+2)) 0x4a 0x1F)
curVal=$(( curVal | (1 << 2 )))
i2cset -y $(($slot+2)) 0x4a 0x1F $curVal
echo "smbus has been swapped to NIC"

