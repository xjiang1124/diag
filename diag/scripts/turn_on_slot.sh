#!/bin/bash

control_slot() {
    v12_addr="0x10"
    v3v3_addr="0x12"
    perst_addr="0x16"
    
    bitPos=$(( $2 - 1 ))
    
    if [[ $2 -ge 9 ]]
    then
        v12_addr=$(( $v12_addr + 1 ))
        v3v3_addr=$(( $v3v3_addr + 1 ))
        perst_addr=$(( $perst_addr + 1 ))
        bitPos=$(( $bitPos - 8 ))
    fi
    
    cpldutil -cpld-rd -addr=$v12_addr
    v12=$?
    
    cpldutil -cpld-rd -addr=$v3v3_addr
    v3v3=$?
    
    cpldutil -cpld-rd -addr=$perst_addr
    perst=$?
    
    bitPos=$(( 1 << $bitPos ))
    
    #printf "0x%x\n" $v12_addr
    #printf "0x%x\n" $v3v3_addr
    #printf "0x%x\n" $perst_addr
    
    if [[ "$1" == "on" ]]
    then
        echo "Turning on slot $2"
        bitPos=$(( ~$bitPos ))
        bitPos=$(( $bitPos & 0xff ))
        v12=$(( $v12 & $bitPos ))
        v3v3=$(( $v3v3 & $bitPos ))
        perst=$(( $perst & $bitPos ))
    
        cpldutil -cpld-wr -addr=$v3v3_addr -data=$v3v3
        sleep 1
        cpldutil -cpld-wr -addr=$v12_addr -data=$v12
        sleep 1
        cpldutil -cpld-wr -addr=$perst_addr -data=$perst
        sleep 1
    
        echo "slot $2 turned on"
    
    else
        echo "Turn off slot $2"
        v12=$(( $v12 | $bitPos ))
        v3v3=$(( $v3v3 | $bitPos ))
        perst=$(( $perst | $bitPos ))
    
        cpldutil -cpld-wr -addr=$perst_addr -data=$perst
        sleep 1
        cpldutil -cpld-wr -addr=$v12_addr -data=$v12
        sleep 1
        cpldutil -cpld-wr -addr=$v3v3_addr -data=$v3v3
        sleep 1
    
        echo "slot $2 turned off"
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
        sleep 1
        cpldutil -cpld-wr -addr=0x10 -data=0
        cpldutil -cpld-wr -addr=0x11 -data=0
        sleep 1
        cpldutil -cpld-wr -addr=0x16 -data=0
        cpldutil -cpld-wr -addr=0x17 -data=0
        sleep 1
    
        echo "All slots turned on"
    
    else
        echo "Turning off all slots"
        cpldutil -cpld-wr -addr=0x16 -data=0xff
        cpldutil -cpld-wr -addr=0x17 -data=0xff
        sleep 1
        cpldutil -cpld-wr -addr=0x10 -data=0xff
        cpldutil -cpld-wr -addr=0x11 -data=0xff
        sleep 1
        cpldutil -cpld-wr -addr=0x12 -data=0xff
        cpldutil -cpld-wr -addr=0x13 -data=0xff
        sleep 1
    
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
    echo "Turn_on_slot.sh Usage"
    echo "========================="
    echo "Turn on specific slot"
    echo "turn_on_slot.sh on <slot_id>"

    echo "-------------------------"
    echo "Turn off_specific slot"
    echo "turn_on_slot.sh off <slot_id>"

    echo "-------------------------"
    echo "Turn on all slots"
    echo "turn_on_slot.sh on all"

    echo "-------------------------"
    echo "Turn off all slots"
    echo "turn_on_slot.sh off all"
    echo "========================="
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

if [[ $2 == "all" ]]
then
    control_all $1
else
    control_slot $1 $2
fi
