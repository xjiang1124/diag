#!/bin/bash

control_slot() {
    v3v3_addr="0x12"
    
    if [[ $low_high == "high" ]]
    then
        v3v3_addr=$(( $v3v3_addr + 1 ))
        wValue=$pc_high
    else
        wValue=$pc_low
    fi
    if [[ $wValue -eq 0 ]]
    then
        return 0
    fi

    printf "Setting $low_high power control to $on_off with 0x%x\n" $wValue

    cpldutil -cpld-rd -addr=$v3v3_addr
    v3v3=$?

    if [[ $on_off == "on" ]]
    then
        wValue=$(( ~$wValue ))
        wValue=$(( $wValue & 0xff ))
        v3v3=$(( $v3v3 & $wValue ))
    
        cpldutil -cpld-wr -addr=$v3v3_addr -data=$v3v3
        sleep 0.2
    
    else
        v3v3=$(( $v3v3 | $wValue ))
        cpldutil -cpld-wr -addr=$v3v3_addr -data=$v3v3
        sleep 0.2
    fi
    
    cpldutil -cpld-rd -addr=$v3v3_addr

}

control_all() {
    if [[ "$1" == "on" ]]
    then
        echo "Turning on all slots"
        cpldutil -cpld-wr -addr=0x12 -data=0
        cpldutil -cpld-wr -addr=0x13 -data=0
        sleep 0.5
    
    else
        echo "Turning off all slots"
        cpldutil -cpld-wr -addr=0x12 -data=0xff
        cpldutil -cpld-wr -addr=0x13 -data=0xff
        sleep 0.5
    
        echo "All slots turned off"
    fi

    cpldutil -cpld-rd -addr=0x12
    cpldutil -cpld-rd -addr=0x13
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

    if [[ $on_off == "off" ]]
    then
        exit 0
    fi

    
    #control_slot $1 $2
fi
