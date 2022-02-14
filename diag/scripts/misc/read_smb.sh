# !/bin/bash

num_ite=$1
intv=$2

i2caddr=0x76

for i in `seq 1 $num_ite`;
do

    reg16=$(i2cget -y 0 0x76 0x16)
    reg17=$(i2cget -y 0 0x76 0x17)
    reg18=$(i2cget -y 0 0x76 0x18)
    reg19=$(i2cget -y 0 0x76 0x19)
    reg1A=$(i2cget -y 0 0x76 0x1A)

    echo "reg16: $reg16; reg17: $reg17; reg18: $reg18; reg19: $reg19; reg1A: $reg1A"
    if [[ $reg16 != "0x16" ]] || [[ $reg17 != "0x17" ]] || [[ $reg18 != "0x18" ]] || [[ $reg19 != "0x19" ]] || [[ $reg1A != "0x1a" ]]
    then
        break
    fi
    date
    sleep $intv
done
