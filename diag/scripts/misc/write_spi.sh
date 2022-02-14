# !/bin/bash

intv=$1
echo "Write smbus in every $intv sec"

while true;
do
    date
    /data/nic_util/cpld -w 0x16 0x16
    /data/nic_util/cpld -w 0x17 0x17
    /data/nic_util/cpld -w 0x18 0x18
    /data/nic_util/cpld -w 0x19 0x19
    /data/nic_util/cpld -w 0x1A 0x1A

    /data/nic_util/cpld -r 0x16
    /data/nic_util/cpld -r 0x17
    /data/nic_util/cpld -r 0x18
    /data/nic_util/cpld -r 0x19
    /data/nic_util/cpld -r 0x1A

    sleep $intv
done
