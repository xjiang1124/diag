#!/bin/bash
set_vmarg_taormina()
{
    /fs/nos/home_diag/diag/util/devmgr -dev P0V8AVDD_GB_A -margin -pct=$1
    /fs/nos/home_diag/diag/util/devmgr -dev P0V8AVDD_GB_B -margin -pct=$1
    /fs/nos/home_diag/diag/util/devmgr -dev P0V8RT_B -margin -pct=$1
    /fs/nos/home_diag/diag/util/devmgr -dev P0V8RT_A -margin -pct=$1
    /fs/nos/home_diag/diag/util/devmgr -dev TDNT_P0V8_AVDD -margin -pct=$1
    return
}


set_vmarg_taormina3v3S()
{
    /fs/nos/home_diag/diag/util/devmgr -dev p3v3s -margin -pct=$1
    #/fs/nos/home_diag/diag/util/devmgr -dev p3v3  -margin -pct=$1
    return
}

set_vmarg_taormina3v3()
{
    /fs/nos/home_diag/diag/util/devmgr -dev p3v3  -margin -pct=$1
    return
}


if [ "$1" == "normal" ]
then
    percent=0
    set_vmarg_taormina $percent
    set_vmarg_taormina3v3 $percent
    set_vmarg_taormina3v3S $percent
    sleep 1
    /fs/nos/home_diag/diag/util/switch show power    
    exit 0
elif [ "$1"  == "low" ]
then
    declare -a pct_list=(0)
    declare -a pct_list3V3S=(0)
    declare -a pct_list3V3=(0)
elif [ "$1" == "high" ]
then
    declare -a pct_list=(1 2)
    declare -a pct_list3V3S=(1 2 3)
    declare -a pct_list3V3=(1 2 3 4 5 6)
    declare -a pct_list3V3_vrefprogrammed=(0)
else
    echo "Invalid parameter"
    exit 1
fi

for percent in ${pct_list[@]}
do
    echo "=== Setting Vmarg for taormina to $percent% ==="
    set_vmarg_taormina $percent
    echo "=== Vmarg is at $percent% ==="
done


reg1=$(fpgautil i2c 0 1 8 w 0xd4 r 2 | grep RD | cut -c 5-8)
if [[ $reg1 -gt 0x01 ]]
then
    for percent in ${pct_list3V3_vrefprogrammed[@]}
    do
        echo "=== Setting Vmarg for taormina P3V3 to $percent% ==="
        set_vmarg_taormina3v3 $percent
        echo "=== Vmarg is at $percent% ==="
    done
else
    for percent in ${pct_list3V3[@]}
    do
        echo "=== Setting Vmarg for taormina P3V3 to $percent% ==="
        set_vmarg_taormina3v3 $percent
        echo "=== Vmarg is at $percent% ==="
    done
fi

for percent in ${pct_list3V3S[@]}
do
    echo "=== Setting Vmarg for taormina P3V3S to $percent% ==="
    set_vmarg_taormina3v3S $percent
    echo "=== Vmarg is at $percent% ==="
done


sleep 1
/fs/nos/home_diag/diag/util/switch show power
exit 0
