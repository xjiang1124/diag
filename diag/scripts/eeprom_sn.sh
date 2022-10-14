#!/bin/bash

#script for finding the serial number of QSFP EEPROM 
#takes input of i2c bus; output EEPROM serial number

userBus="f"
userInput="f"

ADDR="0x50"

serial() {
    bus=$1
    #SN addresses:0xc4 - 0xd1
    #SN address SFP: 0x44 - 0x53
    snaddr="0xc4"

    dtype=$(detect $bus)
    if [[ $dtype == "SFP" ]]
    then
        snaddr="0x44"
    fi

    incr=14
    SN=""

    testVar=$(i2cget -y $bus $ADDR $snaddr 2>/dev/null)
    if [[ $testVar ]]
    then
        while [[ incr -ne 0 ]]
        do
            hex=$(i2cget -y $bus $ADDR $snaddr 2>/dev/null)
            hex=${hex:2:3}
            SN="$SN\x$hex"

            snaddr=$(( $snaddr + 1 ))
            snaddr=$(printf '0x%x' $snaddr)
            incr=$(( incr - 1 ))
        done

        testVar=${SN//"\xff"}
        if [[ $testVar ]]
        then
            echo -e "Bus $bus: SN $SN"
        else
            echo "No serial number / EEPROM found"
        fi
    else
        echo "QSFP / SFP not detected on bus $bus"
    fi
}

detect() {
    bus=$1
    busCheck=$(checkBus $1)
    if [[ $busCheck == "Present" ]]
    then
        typeAddr="0x00"
        typeVal=$(i2cget -y $bus $ADDR $typeAddr 2>/dev/null)
        typeVal=${typeVal:2:3}
        if [[ $typeVal ]]
        then
            if [[ $typeVal == "03" ]]
            then
                echo "SFP"
            elif [[ $typeVal == "11" ]]
            then
                echo "QSFP"
            else
                echo "Unknown device on bus $bus."
            fi
        else
            echo "Bus $bus: no device found."
        fi
    else
        echo $busCheck
    fi
}

checkBus() {
    bus=$1
    busPresent=$(i2cdetect -F $bus 2>/dev/null)
    if [[ busPresent ]]
    then
        echo "Present"
    else
        echo "I2Cbus $bus not installed"
    fi
}

main() {
    bus=$1
    testBus=$(checkBus $bus)
    if [[ $testBus == "Present" ]]
    then
        serial $bus
    fi
}

usage() {
    echo "eeprom_sn.sh Usage:"
    echo "eeprom_sn.sh -h: help"
    echo "======================"
    echo "eeprom_sn.sh -s [returns serial number of EEPROM on bus 1 and 2]"
    echo "eeprom_sn.sh -d [detects prescence and type of EEPROM on bus 1 and 2]"
    echo "======================"
    echo "eeprom_sn.sh [-s/-d] -b <bus> [specifies bush]"
 }

if [[ $# -eq 0 ]]
then
    echo "help: $0 -h"
    exit
fi

while [[ $# -gt 0 ]]
do
key="$1"
case $key in
    #-------------
    -h) #help
    usage
    exit
    ;;
    #-------------
    -b) #check bus (individual)
    userBus=$2
    break
    ;;
    #-------------
    -d) #detect EEPROM type (both buses)
    userInput="d"
    shift
    ;;
    #-------------
    -s) #return serial number
    userInput="s"
    shift
    ;;
    #-------------
    *) #invalid input
    echo "Invalid input"
    echo "help: $0 -h"
    exit
    ;;
esac
done

if [[ $userBus == "f" ]]
then
    if [[ $userInput == "s" ]]
    then
        main 1
        main 2
        exit
    elif [[ $userInput == "d" ]]
    then
        detect 1
        detect 2
        exit
    fi
else
    if [[ $userInput == "s" ]]
    then
        main $userBus
        exit
    elif [[ $userInput == "d" ]]
    then
        detect $userBus
        exit
    fi
fi
