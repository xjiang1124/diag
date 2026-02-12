#!/bin/bash

matera_P12V_addr="0x174"
matera_P3V3_addr="0x178"
matera_perst_addr="0x17c"


declare -a slotI2Cmap=(
[1]=3
[2]=4
[3]=5
[4]=6
[5]=7
[6]=8
[7]=9
[8]=10
[9]=11
[10]=12
)


#For cards in the MTP that use an adapter to operate in the MTP test chassis.
#OCP cards for example need an adapter card.
#The adapter card controls the power on/off for the nic plugged into it.
card_adapter_enable_power() {
    slot=$1
    ocpAdapterID="0x1a"
    cpld_id=$(i2cget -y ${slotI2Cmap[$slot]} 0x4b 0x80 2> /dev/null)
    if [ $? -eq 0 ] && [[ $cpld_id -eq $ocpAdapterID ]] 
    then
        #power it up via CPLD reg 0x40 (BIT0=AUX_PWR_EN  BIT1=MAIN_PWR_EN)
        register40=$(i2cget -y ${slotI2Cmap[$slot]} 0x4b 0x40)
        if [[ $MTP_TYPE == "MTP_MATERA" ]]
        then
            register40=$(( $register40 | 0x1 ))
        else
            register40=$(( $register40 | 0x1 )) 
        fi
        i2cset -y ${slotI2Cmap[$slot]} 0x4b 0x40 $register40
        sleep 0.5
        adapter_card_check_nic_power_good $slot
        if [[ $MTP_TYPE == "MTP_MATERA" ]]
        then
            register40=$(( $register40 | 0x2 ))
        else 
            register40=$(( $register40 | 0x2 )) 
        fi
        i2cset -y ${slotI2Cmap[$slot]} 0x4b 0x40 $register40
        sleep 0.5
        adapter_card_check_nic_power_good $slot

        #cpldreg00=$(i2cget -y ${slotI2Cmap[$slot]} 0x4a 0x00)
        ##apply this to CPLD Rev 2.0 or higher
        #if [[ $cpldreg00 -gt 1 ]]
        #then
        #    cpldreg01=$(i2cget -y ${slotI2Cmap[$slot]} 0x4a 0x01)
        #    cpldreg01=$(( $cpldreg01 & 0xE7 ))
        #    cpldreg01=$(( $cpldreg01 | 0x08 ))
        #    i2cset -y ${slotI2Cmap[$slot]} 0x4a 0x01 $cpldreg01
        #fi
    fi

}

adapter_card_check_nic_power_good() {
    slot=$1
    regTemp=$(i2cget -y ${slotI2Cmap[$slot]} 0x4b 0x40)
    bit3=$(( $regTemp & 0x08 ))
    if [ $bit3 -eq 0 ] 
    then
        echo "ERROR: Slot-$slot Adapater CPLD is not showing NIC_POWER_GOOD (BIT3) after power enable.  Reg 0x40=$regTemp"
    fi
}


# Enable Elba card JTAG
elba_enable_jtag() {
    slot=$1

    #echo "slot=$slot"
    #echo "i2cslot=${slotI2Cmap[$slot]}"
    reg1=$(i2cget -y ${slotI2Cmap[$slot]} 0x4a 0x22)
    if [ $? -ne 0 ]
    then
        echo "Empty slot $slot"
        return
    fi

    reg1=$(( $reg1 & 0xFC ))
    i2cset -y ${slotI2Cmap[$slot]} 0x4a 0x22 $reg1
}

# Enable NIC MTP Rev3 mode
enable_nic_mtp_r3() {
    slot=$1
    echo "uart_id is $uart_id"

    reg1=$(i2cget -y ${slotI2Cmap[$slot]} 0x4a 0x21)
    #echo $reg1
    if [ $? -ne 0 ]
    then
        echo "Empty slot $slot"
        return
    fi

    board_type=$(i2cget -y ${slotI2Cmap[$slot]} 0x4a 0x80)
    if [[ "$board_type" -ge 0x62 ]]
    then
        data=$(i2cget -y $(($slot + 2)) 0x4a 0x21)
        data=$(( $data & 0xF8 ))
        data=$(( $data | $uart_id ))
        i2cset -y ${slotI2Cmap[$slot]} 0x4a 0x21 $data
    else
        reg1=$(( $reg1 | 0x25 ))
        reg1=$(( $reg1 & 0xBF ))
        i2cset -y ${slotI2Cmap[$slot]} 0x4a 0x21 $reg1
    fi
}

# Set bit between proto mode or production mode
set_prod_mode() {
    slot=$1
    if [[ $prod_mode == "0" ]]
    then
        # mode = prototype
        reg20=$(i2cget -y ${slotI2Cmap[$slot]} 0x4a 0x20)
        reg20=$(( $reg20 & 0xFE )) # set bit0 = 0
        i2cset -y ${slotI2Cmap[$slot]} 0x4a 0x20 $reg20
        echo "Proto mode set"
    fi
}

control_slot_matera() {
    wValue=$pc
    if [[ $wValue -eq 0 ]]
    then
        return 0
    fi

    printf "Setting power control to $on_off with 0x%x\n" $wValue

    v12=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $matera_P12V_addr | awk '{print $4}')
    v3v3=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $matera_P3V3_addr | awk '{print $4}')
    perst=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $matera_perst_addr | awk '{print $4}')

    if [[ $on_off == "off" ]]
    then
        wValue=$(( ~$wValue ))
        wValue=$(( $wValue & 0x3ff ))
        fpgautil w32 $matera_perst_addr $(( $perst & $wValue ))
        sleep 0.2
        fpgautil w32 $matera_P12V_addr $(( $v12 & $wValue ))
        sleep 0.2
        fpgautil w32 $matera_P3V3_addr $(( $v3v3 & $wValue ))
        sleep 0.2
    else
        fpgautil w32 $matera_P3V3_addr $(( $v3v3 | $wValue ))
        sleep 2
        for slot in $slot_list
        do
            enable_nic_mtp_r3 $slot
            elba_enable_jtag $slot
            set_prod_mode $slot $prod_mode
        done
        fpgautil w32 $matera_P12V_addr $(( $v12 | $wValue ))
        fpgautil w32 $matera_perst_addr  $(( $perst | $wValue ))
        for slot in $slot_list
        do
            card_adapter_enable_power $slot
        done
    fi
    sleep 0.2
    fpgautil r32 $matera_P12V_addr
    fpgautil r32 $matera_P3V3_addr
    fpgautil r32 $matera_perst_addr
}

control_all() {
    if [[ "$1" == "on" ]]
    then
        echo "Turning on all slots"
        fpgautil w32 $matera_P3V3_addr 0x3ff
        sleep 2
        for i in {1..10}
        do
            enable_nic_mtp_r3 $i
            set_prod_mode $slot $prod_mode
            elba_enable_jtag $i
        done
        fpgautil w32 $matera_P12V_addr 0x3ff
        sleep 0.2
        fpgautil w32 $matera_perst_addr 0x3ff
        sleep 0.2
        for i in {1..10}
        do
            card_adapter_enable_power $i
        done



        echo "All slots turned on"
    
    else
        echo "Turning off all slots"
        fpgautil w32 $matera_P3V3_addr 0x0
        fpgautil w32 $matera_P12V_addr 0x0
        fpgautil w32 $matera_perst_addr 0x0
        echo "All slots turned off"
    fi

    fpgautil r32 $matera_P12V_addr
    fpgautil r32 $matera_P3V3_addr
    fpgautil r32 $matera_perst_addr
}

control_slot_panarea() {
    if [[ $on_off == "off" ]]
    then
        for slot_one_based in $slot_list
        do
            slot_zero_based=$(( $slot_one_based - 1 ))
            slot_ctrl_reg_addr=$((0x180 + (slot_zero_based * 4)))
            printf "Setting power control to $on_off at addr 0x%08x\n" $slot_ctrl_reg_addr
            wValue=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr | awk '{print $4}')
            # PERST
            wValue=$(( $wValue & 0xFFFFFFFB ))
            sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
            sleep 0.2
            # 12V
            wValue=$(( $wValue & 0xFFFFFFF9 ))
            sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
            sleep 0.2
            # 3V3
            wValue=$(( $wValue & 0xFFFFFFF8 ))
            sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
            sleep 0.2
        done
    elif [[ $on_off == "on" ]]
    then
        for slot_one_based in $slot_list
        do
            slot_zero_based=$(( $slot_one_based - 1 ))
            slot_ctrl_reg_addr=$((0x180 + (slot_zero_based * 4)))
            printf "Setting power control to $on_off at addr 0x%08x\n" $slot_ctrl_reg_addr
            # 3V3
            wValue=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr | awk '{print $4}')
            wValue=$(( $wValue | 0x1 ))
            sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
            # 12V
            wValue=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr | awk '{print $4}')
            wValue=$(( $wValue | 0x3 ))
            sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
            # PERST
            wValue=$(( $wValue | 0x7 ))
            sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
            
            #The OCP Adapter CPLD needs a split second to show up on the i2c bus
            sleep 1
            card_adapter_enable_power $slot_one_based
        done
    fi
    # display
    sleep 0.2
    for slot_one_based in $slot_list
    do
        slot_zero_based=$(( $slot_one_based - 1 ))
        slot_ctrl_reg_addr=$((0x180 + (slot_zero_based * 4)))
        sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr
    done
    if [[ $on_off == "on" ]]
    then
        # wait for bootup message to be print first so it won't mix with our command output
        sleep 3
        for slot_one_based in $slot_list
        do
            #mute backend log on console
            sucutil exec -s $slot_one_based -c "log backend log_backend_uart disable"
        done
    fi
}

control_slot_ponza() {
    if [[ $on_off == "off" ]]
    then
        for slot_one_based in $slot_list
        do
            slot_zero_based=$(( $slot_one_based - 1 ))
            slot_ctrl_reg_addr=$((0x180 + (slot_zero_based * 4)))
            printf "Setting power control to $on_off at addr 0x%08x\n" $slot_ctrl_reg_addr
            wValue=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr | awk '{print $4}')
            wValue=$(( $wValue & 0xFFFFFFF0 ))
            sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
            sleep 0.2
        done
    elif [[ $on_off == "on" ]]
    then
        for slot_one_based in $slot_list
        do
            slot_zero_based=$(( $slot_one_based - 1 ))
            slot_ctrl_reg_addr=$((0x180 + (slot_zero_based * 4)))
            # read NIC present bit
            rValue=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr | awk '{print $4}')
            nic_present=$((rValue & 0x200))
            if [[ "$nic_present" -eq 0 ]]
            then
                printf "Card present, setting power control to $on_off at addr 0x%08x\n" $slot_ctrl_reg_addr
                # 12V
                wValue=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr | awk '{print $4}')
                wValue=$(( $wValue | 0x2 ))
                sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
                # 54V
                wValue=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr | awk '{print $4}')
                wValue=$(( $wValue | 0xa ))
                sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
                sleep 1
                # PERST
                wValue=$(( $wValue | 0xe ))
                sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
            else
                on_off="off"
                printf "Card not present, setting power control to $on_off at addr 0x%08x\n" $slot_ctrl_reg_addr
                wValue=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr | awk '{print $4}')
                wValue=$(( $wValue & 0xFFFFFFF0 ))
                sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil w32 $slot_ctrl_reg_addr $wValue
                sleep 0.2
            fi
        done
    fi
    # display
    sleep 0.2
    for slot_one_based in $slot_list
    do
        slot_zero_based=$(( $slot_one_based - 1 ))
        slot_ctrl_reg_addr=$((0x180 + (slot_zero_based * 4)))
        sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr
    done
    if [[ $on_off == "on" ]]
    then
        # wait for bootup message to be print first so it won't mix with our command output
        sleep 3
        for slot_one_based in $slot_list
        do
            #mute backend log on console
            sucutil exec -s $slot_one_based -c "log backend log_backend_uart disable"
        done
    fi
}

usage() {
    echo "========================="
    echo "Turn_on_slot.sh Usage"
    echo "========================="
    echo "Turn on specific slot"
    echo "turn_on_slot.sh on <slot_id> <uart_id> <prod_mode>"

    echo "-------------------------"
    echo "Turn off_specific slot"
    echo "turn_on_slot.sh off <slot_id>"

    echo "-------------------------"
    echo "Turn on all slots"
    echo "turn_on_slot.sh on all <uart_id> <prod_mode>"

    echo "-------------------------"
    echo "Turn off all slots"
    echo "turn_on_slot.sh off all"
    echo "========================="
}

if [[ $1 == "show" ]]
then
    if [[ $MTP_TYPE == "MTP_MATERA" ]]
    then
        fpgautil r32 $matera_P12V_addr
        fpgautil r32 $matera_P3V3_addr
        fpgautil r32 $matera_perst_addr
    elif [[ $MTP_TYPE == "MTP_PANAREA" || $MTP_TYPE == "MTP_PONZA" ]]
    then
        if [[ $MTP_TYPE == "MTP_PANAREA" ]]
        then
            slot_list="1 2 3 4 5 6 7 8 9 10"
        elif [[ $MTP_TYPE == "MTP_PONZA" ]]
        then
            slot_list="1 2 3 4 5 6"
        else
            slot_list=""
        fi
        for slot_one_based in $slot_list
        do
            slot_zero_based=$(( $slot_one_based - 1 ))
            slot_ctrl_reg_addr=$((0x180 + (slot_zero_based * 4)))
            sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $slot_ctrl_reg_addr
        done
    else
        cpldutil -cpld-rd -addr=0x10
        cpldutil -cpld-rd -addr=0x11
        cpldutil -cpld-rd -addr=0x12
        cpldutil -cpld-rd -addr=0x13
        cpldutil -cpld-rd -addr=0x16
        cpldutil -cpld-rd -addr=0x17
    fi
    exit
fi

if [[ $# -lt 2 ]] && [[ $# -lt 3 ]] && [[ $# -lt 4 ]]
then
    usage
    exit
fi

uart_id=0
if [ $# -ge 3 ]
then
    uart_id=$(($3 & 0x7))
fi
if [ $# -ge 4 ]
then
    prod_mode=$4
fi

if [[ $2 == "all" ]]
then
    on_off=$1
    if [[ $MTP_TYPE == "MTP_MATERA" ]]
    then
        (flock -x -w 50 99 || { echo "ERROR: Failed to acquire lock within 50 seconds"; exit 1;}; control_all $on_off;
        ) 99>/home/diag/turn_on_slot.lock
    elif [[ $MTP_TYPE == "MTP_PANAREA" ]]
    then
        slot_list="1 2 3 4 5 6 7 8 9 10"
        control_slot_panarea
    elif [[ $MTP_TYPE == "MTP_PONZA" ]]
    then
        slot_list="1 2 3 4 5 6"
        control_slot_ponza
    fi
else
    slot_list=$(echo $2 | tr "," "\n")
	pc_low=0
	pc_high=0
	pc=0
	on_off=$1

    if [[ $MTP_TYPE == "MTP_MATERA" ]]
    then
        for slot in $slot_list
        do
            slot=$(( $slot - 1 ))
            bitPos=$(( 1 << $slot ))
            pc=$(( $pc | $bitPos ))
        done
        #printf "pc: 0x%x\n" $pc
    else
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
    fi

    if [[ $MTP_TYPE == "MTP_MATERA" ]]
    then
        (flock -x -w 50 99 || { echo "ERROR: Failed to acquire lock within 50 seconds"; exit 1;}; control_slot_matera;
        ) 99>/home/diag/turn_on_slot.lock
    elif [[ $MTP_TYPE == "MTP_PANAREA" ]]
    then
        control_slot_panarea
    elif [[ $MTP_TYPE == "MTP_PONZA" ]]
    then
        control_slot_ponza
    else
        declare -a low_high_list=("low" "high")
        for low_high in "${low_high_list[@]}"
        do
            echo "remove"
            #control_slot
        done
    fi

    if [[ $on_off == "off" ]]
    then
        exit 0
    fi
    
    #control_slot $1 $2
fi
