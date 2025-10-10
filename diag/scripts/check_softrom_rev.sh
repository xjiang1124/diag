#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <slot> <softrom_rev>"
    echo "Example: $0 3 43"
    exit 1
fi

slot=$1
softrom_rev=$2

check_rev() {
    softrom_idx=$1

    if [[ $softrom_idx == "0" ]]
    then
        offset=0x20000
    else
        offset=0x30000
    fi

    fn=softrom_dump_${softrom_idx}_slot${slot}.bin
    fpgautil flash $slot 1 generatefile 0x20000 0x10000 $fn
    nic_crc=$(md5sum $fn | awk -F " " '{print $1}')
    #echo "Check sum: $nic_crc"

    echo "--------------------------------------"
    echo "=== Checking SoftROM copy #$softrom_idx at offset $offset"
    file="sal_softrom_${softrom_rev}.img"

    # Check if file exists
    if [ ! -f "$file" ]; then
        echo "Skipping '$file' (not a file)"
        return
    fi

    echo "Checking '$file'..."
    file_crc=$(md5sum $file | awk -F " " '{print $1}')
    #echo "file_crc: $file_crc"

    if [[ $nic_crc == $file_crc ]]
    then
        echo "=== SoftROM copy #$softrom_idx matching to $file"
        return
    fi


    echo "=== SoftROM copy #$softrom_idx NO matching found!!!: file_crc: $file_crc; nic_crc: $nic_crc"
    return

}

# Prepare softrom binary files by padding
cp ~/diag/python/esec/images/binaries/sal_softrom*img .
# Iterate over files matching the pattern
file="sal_softrom_${softrom_rev}.img"

# Check if file exists
if [ ! -f "$file" ]; then
    echo "Skipping '$file' (not a file)"
    exit -1
fi

echo "Processing '$file'..."
./pad_bin_hex.sh "$file" "0x10000"


check_rev 0
check_rev 1

