#!/bin/bash

control_slot() {
    v12_addr="0x10"
    v3v3_addr="0x12"
    perst_addr="0x16"
    
    if [[ $low_high == "high" ]]
    then
        v12_addr=$(( $v12_addr + 1 ))
        v3v3_addr=$(( $v3v3_addr + 1 ))
        perst_addr=$(( $perst_addr + 1 ))
        wValue=$pc_high
    else
        wValue=$pc_low
    fi
    if [[ $wValue -eq 0 ]]
    then
        return 0
    fi

    printf "Setting $low_high power control to $on_off with 0x%x\n" $wValue
    
    cpldutil -cpld-rd -addr=$v12_addr
    v12=$?
    
    cpldutil -cpld-rd -addr=$v3v3_addr
    v3v3=$?
    
    cpldutil -cpld-rd -addr=$perst_addr
    perst=$?
    
    #printf "0x%x\n" $v12_addr
    #printf "0x%x\n" $v3v3_addr
    #printf "0x%x\n" $perst_addr
    
    if [[ $on_off == "on" ]]
    then
        wValue=$(( ~$wValue ))
        wValue=$(( $wValue & 0xff ))
        v12=$(( $v12 & $wValue ))
        v3v3=$(( $v3v3 & $wValue ))
        perst=$(( $perst & $wValue ))
    
        cpldutil -cpld-wr -addr=$v3v3_addr -data=$v3v3
        sleep 0.2
        cpldutil -cpld-wr -addr=$v12_addr -data=$v12
        sleep 0.2
        cpldutil -cpld-wr -addr=$perst_addr -data=$perst
        sleep 0.2
    
    else
        v12=$(( $v12 | $wValue ))
        v3v3=$(( $v3v3 | $wValue ))
        perst=$(( $perst | $wValue ))
    
        cpldutil -cpld-wr -addr=$perst_addr -data=$perst
        sleep 0.2
        cpldutil -cpld-wr -addr=$v12_addr -data=$v12
        sleep 0.2
        cpldutil -cpld-wr -addr=$v3v3_addr -data=$v3v3
        sleep 0.2
    fi
    
    cpldutil -cpld-rd -addr=$v12_addr
    cpldutil -cpld-rd -addr=$v3v3_addr
    cpldutil -cpld-rd -addr=$perst_addr
}

control_all() {
    if [[ "$1" == "on" ]]
    then
        echo "Turning on all slots"
        cpldutil -cpld-wr -addr=0x12 -data=0
        cpldutil -cpld-wr -addr=0x13 -data=0
        sleep 0.5
        cpldutil -cpld-wr -addr=0x10 -data=0
        cpldutil -cpld-wr -addr=0x11 -data=0
        sleep 0.5
        cpldutil -cpld-wr -addr=0x16 -data=0
        cpldutil -cpld-wr -addr=0x17 -data=0
        sleep 0.5
    
        echo "All slots turned on"
    
    else
        echo "Turning off all slots"
        cpldutil -cpld-wr -addr=0x16 -data=0xff
        cpldutil -cpld-wr -addr=0x17 -data=0xff
        sleep 0.5
        cpldutil -cpld-wr -addr=0x10 -data=0xff
        cpldutil -cpld-wr -addr=0x11 -data=0xff
        sleep 0.5
        cpldutil -cpld-wr -addr=0x12 -data=0xff
        cpldutil -cpld-wr -addr=0x13 -data=0xff
        sleep 0.5
    
        echo "All slots turned off"
    fi

    cpldutil -cpld-rd -addr=0x10
    cpldutil -cpld-rd -addr=0x11
    cpldutil -cpld-rd -addr=0x12
    cpldutil -cpld-rd -addr=0x13
    cpldutil -cpld-rd -addr=0x16
    cpldutil -cpld-rd -addr=0x17

}

usage() {
    echo "========================="
    echo "turn_on_slot_multi.sh Usage"
    echo "========================="
    echo "Turn on specific slot"
    echo "turn_on_slot_multi.sh on <slot_list>"

    echo "-------------------------"
    echo "Turn off_specific slot"
    echo "turn_on_slot_multi.sh off <slot_list>"
}

if [[ $1 == "show" ]]
then
    cpldutil -cpld-rd -addr=0x10
    cpldutil -cpld-rd -addr=0x11
    cpldutil -cpld-rd -addr=0x12
    cpldutil -cpld-rd -addr=0x13
    cpldutil -cpld-rd -addr=0x16
    cpldutil -cpld-rd -addr=0x17
    exit
fi

if [[ $# -ne 2 ]] 
then
    usage
    exit
fi

slot_list=$(echo $2 | tr "," "\n")
pc_low=0
pc_high=0
on_off=$1

for slot in $slot_list
do
    slot=$(( $slot - 1 ))
    if [[ $slot -ge 8 ]]
    then
        slot=$(( $slot - 8 ))
        bitPos=$(( 1 << $slot ))
        pc_high=$(( $pc_high | $bitPos ))
    else
        bitPos=$(( 1 << $slot ))
        pc_low=$(( $pc_low | $bitPos ))
    fi
done
#printf "pc_low: 0x%x\n" $pc_low
#printf "pc_high: 0x%x\n" $pc_high

declare -a low_high_list=("low" "high")
for low_high in "${low_high_list[@]}"
do
    control_slot
done
