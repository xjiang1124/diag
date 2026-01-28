# !/bin/bash

if [[ $CARD_TYPE == "TAORMINA" ]]
then
    if [ "x$1" == "x0" ] ; then
        #./setConsole.bash
        i2cset -y -a 3 1 1 2
        i2cset -y 3 0x4a 0x22 0xA0
        i2cset -y 3 0x4a 0x21 0x61
        picocom -b 115200 -f h /dev/ttyS2
    elif [ "x$1" == "x1" ] ; then
        #./setConsole.bash
        i2cset -y -a 3 1 1 3
        i2cset -y 3 0x4a 0x22 0xA0
        i2cset -y 3 0x4a 0x21 0x61
        picocom -b 115200 -f h /dev/ttyS3
    fi
elif [[ $CARD_TYPE == "MTP_MATERA" ]]
then
    slot=$1
    uart_id=0
    if [ $# -eq 2 ]
    then
        uart_id=$(($2 & 0x7))
        echo "uart_id=$uart_id"
    fi
    echo "UART connected to slot $1"
    if [[ $CARD_TYPE == "MTP_MATERA" ]]
    then
        board_type=$(i2cget -y $(($slot + 2)) 0x4a 0x80)
        if [[ "$board_type" -ge 0x62 ]]
        then
            data=$(i2cget -y $(($slot + 2)) 0x4a 0x21)
            data=$(( $data & 0xF8 ))
            data=$(( $data | $uart_id ))
            i2cset -y $(($slot + 2)) 0x4a 0x21 $data
        fi
    fi
    taskset -c $slot fpga_uart $((slot - 1))
elif [[ $CARD_TYPE == "MTP_PANAREA" ]]
then
    slot=$1
    if [ $# -eq 1 ]
    then
        if [ -e "/dev/SUCUART$slot" ]
        then
            picocom -b 115200 -f h "/dev/SUCUART$slot"
        else
            picocom -b 115200 "/dev/ttySuC$((slot - 1))"
        fi
    elif [ $# -eq 2 ]
    then
        uart_id=$(($2 & 0x3))
        echo "uart_id=$uart_id"
        if [[ $uart_id -eq 0 ]]
        then
            term="/dev/SUCUART$slot"
            picocom -b 115200 -f h $term
        elif [[ $uart_id -eq 1 ]]
        then
            term="/dev/ttySuC$((slot - 1))"
            picocom -b 115200 $term
        elif [[ $uart_id -eq 2 ]]
        then
            term="/dev/ttyVul$((slot - 1))"
            picocom -b 115200 $term
        fi
    fi
else
    cpldutil -cpld-wr -addr=0x18 -data=0
    cpldutil -cpld-wr -addr=0x18 -data=$1
    
    picocom -b 115200 -f h /dev/ttyS1
fi
