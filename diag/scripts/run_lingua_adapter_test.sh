#!/bin/bash

rc=0
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
if [[ $cTyp != "LINGUA" ]];
then
    echo "$uut=$cTyp"
    echo "${0##*/} is only applicable to Lingua cards."
    echo $usage
    exit
fi

##########################################################
#Scan Chain Request (MTP Adapter requesting from OCP card)
##########################################################
i2cset -y $(($slot+2)) 0x4b 0x43 1
echo "Initiate scan chain from ocp adapter to ocp card"
ScanChain=$(i2cget -y $(($slot+2)) 0x4b 0x44)
if [[ "$ScanChain" -ne 0x77 ]]
then
    echo "ERROR: Slot-$slot OCP Adapter scan chain.  Adapter reg 0x4B.  Expect 0x77.  Read=$ScanChain"
    rc=1
fi
echo "Scan Chain value=$ScanChain"


###################################################
# BIF TEST.  SEND BIF FROM ADAPTER TO OCP CARD
###################################################
declare -a bifValue=(0x01 0x02 0x04)
for i in ${!bifValue[*]}
do
    turn_on_slot.sh off $slot
    matera_P3V3_addr="0x178"
    v3v3=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $matera_P3V3_addr | awk '{print $4}')
    bitPos=$(( 1 << $(( $slot - 1 )) ))
    printf "Setting BitPos=0x%.04x   v3v3=0x%.08x   final write=0x%.08x\n" $bitPos $v3v3 $(( $v3v3 | $bitPos ))
    printf "Testing BIF Value 0x%.02x\n"  ${bifValue[$i]}
    fpgautil w32 $matera_P3V3_addr $(( $v3v3 | $bitPos ))
    sleep 1
    i2cset -y $(($slot+2)) 0x4b 0x41 ${bifValue[$i]}
    i2cset -y $(($slot+2)) 0x4b 0x40 0x1
    bif=$(( $(i2cget -y $(($slot+2)) 0x4a 0xc1) & 0x70 ))
    bif=$(( $bif>>4 ))
    if [[ ${bifValue[$i]} -ne $bif ]]
    then
        echo "ERROR: BIF VALUE:  bif sent=${bifValue[$i]}   bif read=$bif"
        rc=1
    fi    
done
turn_on_slot.sh on $slot




if [[ $rc -eq 0x00 ]]
then
    echo "Adapter Test PASSED"
else
    echo "Adapter Test FAILED"
fi
