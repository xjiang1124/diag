#!/bin/bash


#For and Naples25SWM.  set the SBMUS to the NIC (Not the ALOM)
mtp_adapter_set_nic_smb() {
    slot=$1
    CPLD25swm="0x1b"
    turn_on_hub.sh $1
    cpld_id=$(i2cget -y 0 0x4b 0x80)
    if [ $? -eq 0 ] && [[ $cpld_id -eq $CPLD25swm ]] #If we get a valid return code, an alom card is there that we need to power up
    then
        #set SMBUS master to nic
        reg1=$(i2cget -y 0 0x4b 0x01)
        if [[ $(($reg1 & 0x04)) -ne 0x04  ]]
        then
            reg1=$(( $reg1 | 0x04))
	        i2cset -y 0 0x4b 0x1 $reg1
        fi
    fi
}

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

        for i in {1..10}
        do
            mtp_adapter_set_nic_smb $i   #Enable Nic SMBUS master on naples25swm
        done
    
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

    for slot in $slot_list
    do
       mtp_adapter_set_nic_smb $slot   #Enable naples25swm SMBUS master
    done
    
    #control_slot $1 $2
fi
