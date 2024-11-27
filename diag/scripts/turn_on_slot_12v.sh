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

#For Naples25OCP and Naples25SWM.  They need an additional power up through the CPLD.
power_on_naples25_swm_ocp() {
    slot=$1
    CPLD25swm="0x1b"
    CPLD25ocp="0x1a"
    #turn_on_hub.sh $1
    cpld_id=$(i2cget -y 0 0x4b 0x80)
    if [ $? -eq 0 ] && [[ $cpld_id -eq $CPLD25swm ]] #If we get a valid return code, an alom card is there that we need to power up
    then
        # Disable SGMII port on adaptor board
        swm_dis_sgmii.sh $slot 

        #power it up ASIC via CPLD
        reg1=$(i2cget -y 0 0x4b 0x01)

        reg1=$(( $reg1 & 0x18 )) 
        if [[ $reg1 -eq 0x18 ]]
        then
            echo "Already powered up"
        else
            i2cset -y 0 0x4b 0x1 0x14 #enable alom pwr (5V upconverted to 12V to card)
            #sleep 0.2
            if [[ $swm_lp_mode -ne 1 ]]
            then
                #enable high power mode on SWM CPLD
                reg1=$(i2cget -y 0 0x4a 0x21)
                reg1=$(( $reg1 | 0x6 ))
                i2cset -y 0 0x4a 0x21 $reg1
                #sleep 0.2
                i2cset -y 0 0x4b 0x1 0x1C #enable alom + 12V PCIE Edge power
                echo "Power on done (12V PCIe)"
            else
                echo "Power on done (Alom Power)"
            fi
        fi
    fi

    if [ $? -eq 0 ] && [[ $cpld_id -eq $CPLD25ocp ]] 
    then
        #power it up via CPLD reg 0x40 (BIT0=AUX_PWR_EN  BIT1=MAIN_PWR_EN)
        #reg1=$(i2cget -y 0 0x4b 0x40 2> /dev/null )
        reg1=$(i2cget -y 0 0x4b 0x40)
        reg1=$(( $reg1 | 0x1 ))
        i2cset -y 0 0x4b 0x40 $reg1
        #sleep 0.5
        reg1=$(( $reg1 | 0x3 ))
        i2cset -y 0 0x4b 0x40 $reg1
    fi

}

# Enable Elba card JTAG
elba_enable_jtag() {
    slot=$1

    if [[ $MTP_TYPE == "MTP_MATERA" ]]
    then
        reg1=$(i2cget -y ${slotI2Cmap[$slot]} 0x4a 0x22)
        if [ $? -ne 0 ]
        then
            echo "Empty slot $slot"
            return
        fi

        reg1=$(( $reg1 & 0xFC ))
        i2cset -y ${slotI2Cmap[$slot]} 0x4a 0x22 $reg1
    elif [[ $mtp_id == "0x42" || $mtp_id == "0x4d" ]]
    then
        reg=$(smbutil -uut=uut_$slot -dev=CPLD -rd -addr=0x22)
        reg=$(expr match "$reg" '.*data=\(0x[0-9|a-f|A-F]*\)')
        if [[ $reg = "" ]]
        then
            echo "Skip turn on Elba MTP JTAG $slot"
            return
        fi

        reg=$(( $reg & 0xfc ))
        smbutil -uut=uut_$slot -dev=CPLD -wr -addr=0x22 -data=$reg
    fi
}

elba_delay() {
    if [[ $mtp_id == "0x42" || $mtp_id == "0x4d" ]]
    then
        echo "Elba delay enabled"
        #sleep 1
    fi
}

# Enable NIC MTP Rev3 mode
enable_nic_mtp_r3() {
    slot=$1

    if [[ $MTP_TYPE == "MTP_MATERA" ]]
    then
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
    else
        sleep 1

        reg1=$(smbutil -uut=uut_$slot -dev=CPLD -rd -addr=0x21)
        echo $reg1
        reg1=$(expr match "$reg1" '.*data=\(0x[0-9|a-f|A-F]*\)')
        if [[ $reg1 = "" ]]
        then
            echo "Empty slot $slot"
            return
        fi

        mtp_rev=$(echo $MTP_REV | awk -F"_" '{print $2}')
        echo "Rev: $mtp_rev"
        if [[ "$mtp_rev" -lt 3 ]]
        then
            echo "MTP Rev 2 detected, clear bit 0"
            reg1=$(( $reg1 & 0xFE ))
        else
            echo "MTP Rev $mtp_rev detected, set bit 0"
            reg1=$(( $reg1 | 0x1 ))
        fi
        reg1=$(( $reg1 | 0x25 ))
        reg1=$(( $reg1 & 0xBF ))
        smbutil -uut=uut_$slot -dev=CPLD -wr -addr=0x21 -data=$reg1
    fi
}

reset_hub() {
    echo "Reset hub"
    cpldutil -cpld-wr -addr=0x2 -data=0xf
    #sleep 0.2
    cpldutil -cpld-rd -addr=0x2
    cpldutil -cpld-wr -addr=0x2 -data=0x0
    #sleep 0.2
    cpldutil -cpld-rd -addr=0x2
    echo "Reset hub done"
}

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
        perst=$(( $perst & $wValue ))
    
        cpldutil -cpld-wr -addr=$v12_addr -data=$v12
        #sleep 0.2
        cpldutil -cpld-wr -addr=$perst_addr -data=$perst
 
        elba_delay
    else
        v12=$(( $v12 | $wValue ))
        perst=$(( $perst | $wValue ))
    
        cpldutil -cpld-wr -addr=$perst_addr -data=$perst
        sleep 0.2
        cpldutil -cpld-wr -addr=$v12_addr -data=$v12
        sleep 0.2
    fi
    
    cpldutil -cpld-rd -addr=$v12_addr
    cpldutil -cpld-rd -addr=$v3v3_addr
    cpldutil -cpld-rd -addr=$perst_addr
}

control_slot_matera() {
    wValue=$pc
    if [[ $wValue -eq 0 ]]
    then
        return 0
    fi

    printf "Setting power control to $on_off with 0x%x\n" $wValue

    v12=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $matera_P12V_addr | awk '{print $4}')
    perst=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 $matera_perst_addr | awk '{print $4}')

    if [[ $on_off == "off" ]]
    then
        wValue=$(( ~$wValue ))
        wValue=$(( $wValue & 0x3ff ))
        fpgautil w32 $matera_perst_addr $(( $perst & $wValue ))
        sleep 0.2
        fpgautil w32 $matera_P12V_addr $(( $v12 & $wValue ))
        sleep 0.2
    else
        fpgautil w32 $matera_P12V_addr $(( $v12 | $wValue ))
        fpgautil w32 $matera_perst_addr  $(( $perst | $wValue ))
    fi
    fpgautil r32 $matera_P12V_addr
    fpgautil r32 $matera_perst_addr
}

control_all() {
    if [[ "$1" == "on" ]]
    then
        echo "Turning on all slots"
        if [[ $MTP_TYPE == "MTP_MATERA" ]]
        then
            fpgautil w32 $matera_P12V_addr 0x3ff
            sleep 0.2
            fpgautil w32 $matera_perst_addr 0x3ff
            sleep 0.2
        else
            cpldutil -cpld-wr -addr=0x10 -data=0
            cpldutil -cpld-wr -addr=0x11 -data=0
            #sleep 0.5
            cpldutil -cpld-wr -addr=0x16 -data=0
            cpldutil -cpld-wr -addr=0x17 -data=0
            #sleep 0.5

            elba_delay
        fi

        for i in {1..10}
        do
            if [[ $MTP_TYPE != "MTP_MATERA" ]]
            then
                reset_hub
                turn_on_hub.sh $i
                power_on_naples25_swm_ocp $i   #these adapters need an additional power on via the MTP Adapter
            fi
            enable_nic_mtp_r3 $i
            elba_enable_jtag $i
        done

        echo "All slots turned on"
    
    else
        echo "Turning off all slots"
        if [[ $MTP_TYPE == "MTP_MATERA" ]]
        then
            fpgautil w32 $matera_P12V_addr 0x0
            fpgautil w32 $matera_perst_addr 0x0
        else
            cpldutil -cpld-wr -addr=0x16 -data=0xff
            cpldutil -cpld-wr -addr=0x17 -data=0xff
            #sleep 0.5
            cpldutil -cpld-wr -addr=0x10 -data=0xff
            cpldutil -cpld-wr -addr=0x11 -data=0xff
            #sleep 0.5
        fi
    
        echo "All slots turned off"
    fi

    if [[ $MTP_TYPE == "MTP_MATERA" ]]
    then
        fpgautil r32 $matera_P12V_addr
        fpgautil r32 $matera_perst_addr
    else
        cpldutil -cpld-rd -addr=0x10
        cpldutil -cpld-rd -addr=0x11
        cpldutil -cpld-rd -addr=0x12
        cpldutil -cpld-rd -addr=0x13
        cpldutil -cpld-rd -addr=0x16
        cpldutil -cpld-rd -addr=0x17
    fi
}

usage() {
    echo "========================="
    echo "Turn_on_slot_12v.sh Usage"
    echo "========================="
    echo "Turn 12v on specific slot"
    echo "turn_on_slot.sh on <slot_id> <uart_id> <prod_mode>"

    echo "-------------------------"
    echo "Turn 12v off specific slot"
    echo "turn_on_slot_12v.sh off <slot_id>"

    echo "-------------------------"
    echo "Turn 12v on all slots"
    echo "turn_on_slot.sh on all <uart_id> <prod_mode>"

    echo "-------------------------"
    echo "Turn 12v off all slots"
    echo "turn_on_slot_12v.sh off all"
    echo "========================="
}

if [[ $1 == "show" ]]
then
    if [[ $MTP_TYPE == "MTP_MATERA" ]]
    then
        fpgautil r32 $matera_P12V_addr
        fpgautil r32 $matera_P3V3_addr
        fpgautil r32 $matera_perst_addr
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

if [[ $MTP_TYPE != "MTP_MATERA" ]]
then
    swm_lp_mode=0
    if [[ $# -eq 3 ]]
    then
        echo "3rd arg = $3"
        swm_lp_mode=$3
        echo "swm_lp_mode = $swm_lp_mode"
    fi
else
    uart_id=0
    if [ $# -ge 3 ]
    then
        uart_id=$(($3 & 0x7))
    fi
    if [ $# -ge 4 ]
    then
        prod_mode=$4
    fi
fi

if [[ $MTP_TYPE != "MTP_MATERA" ]]
then
    mtp_id_str=$(/home/diag/diag/util/cpldutil -cpld-rd -addr=0x80)
    mtp_id_str1=($mtp_id_str)
    mtp_id=${mtp_id_str1[-1]}
fi

if [[ $2 == "all" ]]
then
    on_off=$1
    (flock -x -w 50 99 || exit 1; control_all $on_off;
    ) 99>/home/diag/turn_on_slot.lock
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
        (flock -x -w 50 99 || exit 1; control_slot_matera;
        ) 99>/home/diag/turn_on_slot.lock
    else
        declare -a low_high_list=("low" "high")
        for low_high in "${low_high_list[@]}"
        do
            control_slot
        done
    fi

    if [[ $on_off == "off" ]]
    then
        exit 0
    fi

    for slot in $slot_list
    do
        if [[ $MTP_TYPE != "MTP_MATERA" ]]
        then
            reset_hub
            turn_on_hub.sh $slot
            power_on_naples25_swm_ocp $slot   #these adapters need an additional power on via the MTP ADAPTER
            enable_nic_mtp_r3 $slot
            elba_enable_jtag $slot
        fi
    done

    
    #control_slot $1 $2
fi
