#!/bin/bash

#POSITIONAL=()
#while [[ $# -gt 0 ]]
#do
#key="$1"
#
#case $key in
#    #-------------
#    -slot|--slot)
#    SLOT="$2"
#    shift # past argument
#    shift # past value
#    ;;
#    #-------------
#    --default)
#    DEFAULT=YES
#    shift # past argument
#    ;;
#    #-------------
#    *)    # unknown option
#    POSITIONAL+=("$1") # save it in an array for later
#    shift # past argument
#    echo "Invalid input $0 $1 $2"
#    exit
#    ;;
#esac
#done
#set -- "${POSITIONAL[@]}" # restore positional parameters

SLOT=$1
echo "SLOT:        ${SLOT}"

turn_on_hub.sh $SLOT
smbutil -uut=uut_$SLOT -dev=cpld -rd -addr=0x21
smbutil -uut=uut_$SLOT -dev=cpld -wr -addr=0x21 -data=0xe
smbutil -uut=uut_$SLOT -dev=cpld -rd -addr=0x21
i2cutil -uut=uut_$SLOT -dev=i2cspi -erase -addr=0

OUTPUT="$(i2cutil -uut=uut_$SLOT -dev=i2cspi -addr=0x00 -wrpage)"
echo $OUTPUT
if [[ $OUTPUT == *"Read back verification passed"* ]]
then
    echo "I2CSPI TEST PASSED"
    echo "I2CSPI TEST PASSED"
else
    echo "I2CSPI TEST FAILED"
    echo "I2CSPI TEST FAILED"
fi
