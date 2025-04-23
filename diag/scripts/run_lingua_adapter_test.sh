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
#CHECK PRESNTB[3:0]_L
#On the MTP PRESENTB[3] IS HOOKED TO CLK AND TOGGLES
#So PRESENTB[3] IS MASKED OUT FOR CHECKING
##########################################################
echo "Check PRESNTB[3:0]_L on Adapter"
register42=$(i2cget -y $(($slot+2)) 0x4b 0x42)
register42=$(( $register42 & 0x07 ))
if [[ "$register42" -ne 0x07 ]]
then
    printf "ERROR: Slot-$slot OCP Adapter PRSNT[3:0] test failed.  Adapter reg 0x42.  Expect 0x07.  Read=0x%.02x\n" $register42
    rc=1
fi

##########################################################
#CHECK SLOT ID FROM ADAPTER TO LINGUA
##########################################################
declare -a slotid=(0x01 0x02 0x03 0x00)
for i in ${!slotid[*]}
do
    printf "Test Slot ID on Lingua:  Slot ID=0x%.02x\n"  ${slotid[$i]}
    #set slotID on register 0x40 on adapter
    register40=$(i2cget -y $(($slot+2)) 0x4b 0x40)
    value=$(( ${slotid[$i]} << ((6)) ))
    value=$(( $register40 | $value ))
    i2cset -y $(($slot+2)) 0x4b 0x40 $value

    #read slot ID on register 0xA on Lingua
    registerA=$(i2cget -y $(($slot+2)) 0x4a 0xA)
    registerA=$(( $registerA & 0x03 ))
    if [[ $registerA -ne ${slotid[$i]} ]] 
    then
        printf "ERROR: SLOT ID CHECK FAILED.  ADAPTER REGISTER 0x40=0x%.02x.  LINGUA CPLD REG 0x0A=0x%.02x\n" $register40 $registerA
        rc=1
    fi 

    #set back to default state
    i2cset -y $(($slot+2)) 0x4b 0x40 $register40
done

##########################################################
#Scan Chain Request (MTP Adapter requesting from OCP card)
##########################################################
echo "Performing Scan Chain test"
echo "Initiate scan chain from ocp adapter to ocp card"
i2cset -y $(($slot+2)) 0x4b 0x43 1
ScanChain=$(i2cget -y $(($slot+2)) 0x4b 0x44)
if [[ "$ScanChain" -ne 0x77 ]]
then
    printf "ERROR: Slot-$slot OCP Adapter scan chain.  Adapter reg 0x44.  Expect 0x77.  Read=0x%.02x\n" $ScanChain
    rc=1
fi
printf "Scan Chain value=%.02x\n" $ScanChain


###################################################
# BIF TEST.  SEND BIF FROM ADAPTER TO OCP CARD
###################################################
echo "Performing BIF test"
declare -a bifValue=(0x01 0x02 0x04)
for i in ${!bifValue[*]}
do
    turn_on_slot.sh off $slot
    sleep 1
    matera_P12V_addr="0x174"
    matera_P3V3_addr="0x178"
    p3v3=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $matera_P3V3_addr | awk '{print $4}')
    p12v=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $matera_P3V3_addr | awk '{print $4}')
    bitPos=$(( 1 << $(( $slot - 1 )) ))
    printf "Setting 3.3V and 12V enable\n"
    fpgautil w32 $matera_P3V3_addr $(( $p3v3 | $bitPos ))
    fpgautil w32 $matera_P12V_addr $(( $p12v | $bitPos ))
    sleep 2
    printf "Testing BIF Value 0x%.02x\n"  ${bifValue[$i]}
    i2cset -y $(($slot+2)) 0x4b 0x41 ${bifValue[$i]}
    i2cset -y $(($slot+2)) 0x4b 0x40 0x1
    sleep 0.2
    i2cset -y $(($slot+2)) 0x4b 0x40 0x3
    sleep 2
    bif=$(( $(i2cget -y $(($slot+2)) 0x4a 0xc1) & 0x70 ))
    bif=$(( $bif>>4 ))
    if [[ ${bifValue[$i]} -ne $bif ]]
    then
        printf "ERROR: BIF VALUE:  bif sent=0x%.02x   bif read=0x%.02x\n" ${bifValue[$i]} $bif
        rc=1
    fi    
done
turn_on_slot.sh off $slot
turn_on_slot.sh on $slot


############################################################
# BMC RESET TEST.  TOGGLE MAIN POWER WITH AUX POWER ENABLED
############################################################
printf "Testing BMC Power Cycle Method\n"
register40=$(i2cget -y $(($slot+2)) 0x4b 0x40)
register40=$(( $register40 & 0xFD ))
printf "Disabling MAIN Power\n"
i2cset -y $(($slot+2)) 0x4b 0x40 $register40
sleep 5 
register40=$(( $register40 | 0x2 ))
printf "Enabling MAIN Power\n"
i2cset -y $(($slot+2)) 0x4b 0x40 $register40
sleep 2
#### Check Register 0x30 on Lingua CPLD for any failures
register30=$(i2cget -y $(($slot+2)) 0x4a 0x30)
if [[ $register30 -eq 0x0b ]] 
then
    printf "ERROR: SIMULATED BMC POWER CYCLE.  LINGUA CPLD REGISTER 0x30 IS 0x0B.  REG 0x30=0x%.02x" $register30
    rc=1
fi

if [[ $rc -eq 0x00 ]]
then
    echo "Adapter Test PASSED"
else
    echo "Adapter Test FAILED"
fi
