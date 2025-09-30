#!/bin/bash

# param 1: slot
# param 2: value at 0x400; use 0xbd to enable esecure; program other value to disable
# param 3: value at 0x401; use 0xbd to enable hw lock; program other value to disable
fn=ufm2_slot$1.bin
echo "Esecure HW Lock Bits --> Slot-$1 0x400=$2 0x401=$3"
fpgautil cpld $1 generate ufm2 $fn
printf "$(printf '\\x%02X' $2)" | dd of=$fn bs=1 seek=1024 count=1 conv=notrunc &> /dev/null
printf "$(printf '\\x%02X' $3)" | dd of=$fn bs=1 seek=1025 count=1 conv=notrunc &> /dev/null
fpgautil cpld $1 program ufm2 $fn
ret=$?
if [[ $ret != 0 ]]
then
    echo "Programming failed. Dumping UFM2 to compare"
    fpgautil cpld $1 generate ufm2 $fn.compare
    od -tx1 -v $fn > $fn.hex
    od -tx1 -v $fn.compare > $fn.compare.hex
    diff $fn.hex $fn.compare.hex
fi
