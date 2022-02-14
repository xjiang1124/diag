# !/bin/bash

if [[ $# -ne 3 ]]
then
    echo "Invalid number of argements"
    exit 0
fi

phy=$1
addr=$2
val=$3
bus=0
i2c_addr=0x4b

ctrl_low=$(( ( $phy << 3 ) | 5 ))
ctrl_low_hex=$( printf "%x" $ctrl_low )

val_low=$(( val & 0xFF ))
val_high=$(( (val >> 8) & 0xFF ))

i2cset -y $bus $i2c_addr 0x8 $val_low
i2cset -y $bus $i2c_addr 0x9 $val_high

i2cset -y $bus $i2c_addr 0x7 $addr
i2cset -y $bus $i2c_addr 0x6 $ctrl_low

sleep 0.1
i2cset -y $bus $i2c_addr 0x6 0
sleep 0.1

rd_low="$(i2cget -y $bus 0x4b 0x8)"
rd_high="$(i2cget -y $bus 0x4b 0x9)"

echo "High: $rd_high; Low: $rd_low"
