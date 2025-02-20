#!/bin/bash

# param 1: slot
# param 2: value at 0x400; use 0xbd to enable esecure; program other value to disable
# param 3: value at 0x401; use 0xbd to enable hw lock; program other value to disable
echo "Esecure HW Lock Bits --> Slot-$1 0x400=$2 0x401=$3"
fpgautil cpld $1 generate ufm2 ufm2.bin
printf "$(printf '\\x%02X' $2)" | dd of=ufm2.bin bs=1 seek=1024 count=1 conv=notrunc &> /dev/null
printf "$(printf '\\x%02X' $3)" | dd of=ufm2.bin bs=1 seek=1025 count=1 conv=notrunc &> /dev/null
fpgautil cpld $1 program ufm2 ufm2.bin
