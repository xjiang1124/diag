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
    taskset -c $slot fpga_uart $((slot - 1))
else
    cpldutil -cpld-wr -addr=0x18 -data=0
    cpldutil -cpld-wr -addr=0x18 -data=$1
    
    picocom -b 115200 -f h /dev/ttyS1
fi
