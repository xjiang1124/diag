#!/bin/bash

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

usage() {
    echo ""
    echo "========================="
    echo "con_switch.sh Usage"
    echo "========================="
    echo "Toggle slot's uart from A35 to N1, or N1 to A35"
    echo "con_switch.sh <slot>"

    echo "-------------------------"
    echo "Set slot's uart to A35"
    echo "con_switch.sh <slot> 0"
    echo "or"
    echo "con_switch.sh <slot> A35"

    echo "-------------------------"
    echo "Set slot's uart to N1"
    echo "con_switch.sh <slot> 1"
    echo "or"
    echo "con_switch.sh <slot> N1"
    echo "========================="
}

validate_present() {
    reg1=$(i2cget -y ${slotI2Cmap[$slot]} 0x4a 0x21)
    if [ $? -ne 0 ]; then
        echo "Empty slot $slot"
        return -2
    fi
}

validate_card_type() {
    MALFA=0x62
    LENI=0x64
    POLLARA=0x65
    LINGUA=0x67

    reg1=$(i2cget -y ${slotI2Cmap[$slot]} 0x4a 0x80)
    if [[ "$reg1" -lt "$MALFA" ]]; then
        echo "Wrong card type"
        return -3
    fi
}

parse_uart_sel() {
    if [[ -z $1 ]]; then
        uart_sel="toggle"
    elif [[ $1 == "0" || $1 == "A35" ]]; then
        uart_sel="A35"
    elif [[ $1 == "1" || $1 == "N1" ]]; then
        uart_sel="N1"
    else
        usage
    fi
    echo $uart_sel
}

select_uart() {
    UART0_SEL=0x00 # A35
    UART1_SEL=0x01 # N1
    slot=$1

    if [[ $2 == "toggle" ]]; then
        cur_sel=$(i2cget -y ${slotI2Cmap[$slot]} 0x4a 0x21)
        cur_sel=$(( $cur_sel & 0x7 ))
        if (( $cur_sel == $UART0_SEL )); then
            i2cset -yr ${slotI2Cmap[$slot]} 0x4a 0x21 ${UART1_SEL}
            if [[ $? == 0 ]]; then echo "Console set to N1 uart"; fi
        elif (( $cur_sel == $UART1_SEL )); then
            i2cset -yr ${slotI2Cmap[$slot]} 0x4a 0x21 ${UART0_SEL}
            if [[ $? == 0 ]]; then echo "Console set to A35 uart"; fi
        fi
    elif [[ $2 == "A35" ]]; then
        i2cset -yr ${slotI2Cmap[$slot]} 0x4a 0x21 ${UART0_SEL}
        if [[ $? == 0 ]]; then echo "Console set to A35 uart"; fi
    elif [[ $2 == "N1" ]]; then
        i2cset -yr ${slotI2Cmap[$slot]} 0x4a 0x21 ${UART1_SEL}
        if [[ $? == 0 ]]; then echo "Console set to N1 uart"; fi
    fi
}

if [ $# -lt 1 ]; then
    usage
    exit
fi
if [[ $MTP_TYPE != "MTP_MATERA" && $MTP_TYPE != "MTP_PANAREA" ]]; then
    exit 0
fi
slot=$1
SLOT_0_BASED=$(expr $slot - 1)
uart_sel=$(parse_uart_sel $2)

validate_present $slot
if [ $? -ne 0 ]; then exit -1; fi
validate_card_type
if [ $? -ne 0 ]; then exit -2; fi
select_uart $slot $uart_sel
if [ $? -ne 0 ]; then exit -3; fi
