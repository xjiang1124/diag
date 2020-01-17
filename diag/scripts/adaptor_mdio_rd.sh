# !/bin/bash

if [[ $# -ne 2 ]]
then
    echo "Invalid number of argements"
    exit 0
fi

phy=$1
addr=$2

bus=0
i2c_addr=0x4b

ctrl_low=$(( ( $phy << 3 ) | 3 ))
ctrl_low_hex=$( printf "%x" $ctrl_low )

# Show port status
i2cset -y $bus $i2c_addr 0x7 $addr
i2cset -y $bus $i2c_addr 0x6 $ctrl_low
sleep 0.1
i2cset -y $bus $i2c_addr 0x6 0
sleep 0.1

rd_low="$(i2cget -y $bus 0x4b 0x8)"
rd_high="$(i2cget -y $bus 0x4b 0x9)"

echo "High: $rd_high; Low: $rd_low"
