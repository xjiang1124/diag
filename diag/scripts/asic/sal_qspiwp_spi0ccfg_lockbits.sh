#!/bin/bash

# param 1: slot
# param 2: value at 0x403; use 0x01 to set QSPI_WP and SPI0_CCFG_DISABLE; esecure; 0x00 to clear

fn=cpldreg25_ufm2_slot$1.bin
echo "QSPI_WP and SPI0_CCFG_DISABLE --> Slot-$1 0x403=$2"
fpgautil cpld $1 generate ufm2 $fn
printf "$(printf '\\x%02X' $2)" | dd of=$fn bs=1 seek=1027 count=1 conv=notrunc &> /dev/null
fpgautil cpld $1 program ufm2 $fn
ret=$?
if [[ $ret != 0 ]]
then
    echo "Programming failed. Dumping UFM2 to compare"
    fpgautil cpld $1 generate $fn $fn.compare
    od -tx1 -v $fn > $fn.hex
    od -tx1 -v $fn.compare > $fn.compare.hex
    diff $fn.hex $fn.compare.hex
else
    printf "\n\n----------------------------------------\n"
    echo "Programming Passed, dump for double check"
    fpgautil cpld $1 generate ufm2 $fn
    hexdump $fn
fi
rm $fn