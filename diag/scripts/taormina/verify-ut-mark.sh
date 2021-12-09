#!/bin/bash
# (c) Copyright 2021 Hewlett Packard Enterprise Development LP
#
# Confidential computer software. Valid license from Hewlett Packard
# Enterprise required for possession, use or copying.
#
# Consistent with FAR 12.211 and 12.212, Commercial Computer Software,
# Computer Software Documentation, and Technical Data for Commercial Items
# are licensed to the U.S. Government under vendor's standard commercial
# license.

# This script provides a means for manufacturing to verify the Unsupported
# Transceiver (UT) mark for Taormina.
# If the UT Mark is set, the card has been marked for UT usage.
# If the UT Mark is clear, the card has not been marked for UT usage.
#
# This tool is intended for internal use only.

# Taormina usage:
# verify-ut-mark.sh

set -o pipefail

# sig is 32 bytes followed by salt of 32 bytes.
eeprom_sig_salt_sz=0x40

default_seed=1A38CCE259CB034

# setup scratch pad
tmp_dir=`mktemp -d`
sync

# need prod name to determine if system is Taormina or not
prod_name=$(platform-info system-product-name)
if [ $? -ne 0 ]; then
  echo "verify-ut-mark: Failure: Could not read product name."
  rm -rf $tmp_dir
  exit 1
fi

# need part number to select appropriate dir for i2cexec.
part_num=$(fruread --chassis 1 --part_nr | cut -d "'" -f 2)
if [ $? -ne 0 ]; then
  echo "verify-ut-mark: Failure: Could not read part number."
  rm -rf $tmp_dir
  exit 1
fi

# retrieve the serial # and setup the i2cexec params based on the product.
if [ "$prod_name" = "10000" ]; then
  fruread --chassis 1 --serial_nr | cut -d "'" -f 2 | tr -d '\n' > $tmp_dir/serial_num
  if [ $? -ne 0 ]; then
    echo "verify-ut-mark: Failure: Could not read fru data."
    rm -rf $tmp_dir
    exit 1
  fi
  i2cexec_params="-y /etc/openswitch/platform/HPE/10000/$part_num base fru_eeprom_ul"
  eeprom_sig_salt_offset=0xA04
else
  echo "verify-ut-mark: Failure: Bad product name: $prod_name"
  rm -rf $tmp_dir
  exit 1
fi

echo "verify-ut-mark: product name : $prod_name"
echo "verify-ut-mark: part #       : $part_num"
echo "verify-ut-mark: serial #     : $(cat $tmp_dir/serial_num)"

# setup the secret, serial #, and salt as inputs to create the digest ("signature").
echo $default_seed | tr -d '\n' > $tmp_dir/default_seed

# read the mark from eeprom
i2cexec $i2cexec_params R@$eeprom_sig_salt_offset $eeprom_sig_salt_sz > $tmp_dir/read_data
if [ $? -ne 0 ]; then
  echo "verify-ut-mark: Failure: Could not read eeprom data."
  rm -rf $tmp_dir
  exit 1
fi

# convert to binary in preparation for computing digest.
cat $tmp_dir/read_data | sed -r 's/.{16}$//' | tr -s ' ' | tr -d '\n' > $tmp_dir/mark.txt
xxd -r -p $tmp_dir/mark.txt > $tmp_dir/mark
if [ $? -ne 0 ]; then
  echo "verify-ut-mark: Failure: Could not transform mark."
  rm -rf $tmp_dir
  exit 1
fi

# retrieve digest to verify from mark.
dd if=$tmp_dir/mark of=$tmp_dir/dgst_to_verify bs=32 count=1 &>/dev/null
if [ $? -ne 0 ]; then
  echo "verify-ut-mark: Failure: Could not retrieve digest to verify."
  rm -rf $tmp_dir
  exit 1
fi

# retrieve salt from mark for computing digest.
dd if=$tmp_dir/mark of=$tmp_dir/random_num bs=32 count=1 skip=1 &>/dev/null
if [ $? -ne 0 ]; then
  echo "verify-ut-mark: Failure: Could not retrieve salt for digest."
  rm -rf $tmp_dir
  exit 1
fi

# compute digest
cat $tmp_dir/default_seed $tmp_dir/serial_num $tmp_dir/random_num \
  | openssl dgst -sha256 -binary -out $tmp_dir/dgst
if [ $? -ne 0 ]; then
  echo "verify-ut-mark: Failure: Could not compute digest."
  rm -rf $tmp_dir
  exit 1
fi

# compare.
cmp -s $tmp_dir/dgst $tmp_dir/dgst_to_verify
if [ $? -ne 0 ]; then
  echo "verify-ut-mark: UT mark is set."
  rm -rf $tmp_dir
  exit 1
fi

echo "verify-ut-mark: UT mark is clear."

# remove the scratch pad
rm -rf $tmp_dir
