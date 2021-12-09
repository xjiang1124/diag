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

# This script provides a means for manufacturing to clear the Unsupported
# Transceiver (UT) mark for Taormina.  To "clear" this mark is to program the
# Unsupported Transceiver Signature and salt onto the unlocked chassis eeprom
# for Taormina.
#
# This tool is intended for manufacturing and internal use only.

# Taormina usage:
# clear-ut-mark.sh


# sig is 32 bytes followed by salt of 32 bytes.
eeprom_sig_salt_sz=0x40

default_seed=1A38CCE259CB034

# setup scratch pad
tmp_dir=`mktemp -d`
sync

# need prod name to determine if system is Taormina or not.
prod_name=$(platform-info system-product-name)
# need part number to select appropriate dir for i2cexec.
part_num=$(fruread --chassis 1 --part_nr | cut -d "'" -f 2)

# retrieve the serial # and setup the i2cexec params based on the product.
if [ "$prod_name" = "10000" ]; then
  fruread --chassis 1 --serial_nr | cut -d "'" -f 2 | tr -d '\n' > $tmp_dir/serial_num
  i2cexec_params="-y /etc/openswitch/platform/HPE/10000/$part_num base fru_eeprom_ul"
  eeprom_sig_salt_offset=0xA04
else
  echo "clear-ut-mark: bad product name: $prod_name"
  rm -rf $tmp_dir
  exit 1
fi

echo "clear-ut-mark: product name : $prod_name"
echo "clear-ut-mark: part #       : $part_num"
echo "clear-ut-mark: serial #     : $(cat $tmp_dir/serial_num)"

# setup the secret, serial #, and salt as inputs to create the digest ("signature").
echo $default_seed | tr -d '\n' > $tmp_dir/default_seed
openssl rand -out $tmp_dir/random_num 32
if [ $? -ne 0 ]; then
  echo "clear-ut-mark: could not generate random #."
  rm -rf $tmp_dir
  exit 1
fi

# create the signature.
cat $tmp_dir/default_seed $tmp_dir/serial_num $tmp_dir/random_num \
  | openssl dgst -sha256 -binary -out $tmp_dir/dgst
if [ $? -ne 0 ]; then
  echo "clear-ut-mark: could not create signature."
  rm -rf $tmp_dir
  exit 1
fi

# prepare signature and salt for use with i2cexec tool and create the mark for the eeprom. which
# includes the signature+salt (64 bytes)
cat $tmp_dir/dgst $tmp_dir/random_num > $tmp_dir/mark
eeprom_data=$(hexdump -C $tmp_dir/mark | sed -r 's/.{8}//' | sed -r 's/.{20}$//' \
  | tr -s ' ' | tr -d '\n' | sed -r 's/ / 0x/g')

# write the data to the unlocked eeprom.
i2cexec $i2cexec_params W@$eeprom_sig_salt_offset $eeprom_data > $tmp_dir/write_data
if [ $? -ne 0 ]; then
  echo "clear-ut-mark: could not write eeprom data."
  rm -rf $tmp_dir
  exit 1
fi

# read the data to confirm.
i2cexec $i2cexec_params R@$eeprom_sig_salt_offset $eeprom_sig_salt_sz > $tmp_dir/read_data
if [ $? -ne 0 ]; then
  echo "clear-ut-mark: could not read eeprom data."
  rm -rf $tmp_dir
  exit 1
fi

# check that the write data and read data match.
cmp -s $tmp_dir/write_data $tmp_dir/read_data
if [ $? -ne 0 ]; then
  echo "clear-ut-mark: data read back does not match data written."
  rm -rf $tmp_dir
  exit 1
fi

# remove the scratch pad
rm -rf $tmp_dir
