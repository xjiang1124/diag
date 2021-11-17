#!/bin/bash

set_vmarg_elba()
{
    /data/nic_util/devmgr -dev=ELB0_ARM -margin -pct=$1
    /data/nic_util/devmgr -dev=ELB0_CORE -margin -pct=$1
    /data/nic_util/devmgr -dev=VDDQ_DDR -margin -pct=$1
    /data/nic_util/devmgr -dev=VDD_DDR -margin -pct=$1
    return
}


set_vmarg_ddr()
{
    /data/nic_util/devmgr -dev=ELB0_ARM -margin -pct=$1
    /data/nic_util/devmgr -dev=ELB0_CORE -margin -pct=$1
    /data/nic_util/devmgr -dev=VDDQ_DDR -margin -pct=$1
    /data/nic_util/devmgr -dev=VDD_DDR -margin -pct=$1
    return
}

if [ "$1" == "normal" ]
then
    percent=0
    set_vmarg_elba $percent
    set_vmarg_ddr $percent
elif [ "$1"  == "low" ]
then
    declare -a pct_list=(-1 -2)
    declare -a ddr_pct_list=(-1 -2)
elif [ "$1" == "high" ]
then
    declare -a pct_list=(1 2)
    declare -a ddr_pct_list=(1 2)
else
    echo "Invalid parameter"
    exit 0
fi

for percent in ${pct_list[@]}
do
    echo "=== Setting Vmarg for elba to $percent% ==="
    set_vmarg_elba $percent
    echo "=== Vmarg is at $percent% ==="
done

for percent in ${ddr_pct_list[@]}
do
    echo "=== Setting Vmarg for elba DDR to $percent% ==="
    set_vmarg_ddr $percent
    echo "=== Vmarg is at $percent% ==="
done

