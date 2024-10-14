#!/bin/bash

slot=$1
vmarg=$2
num_ite=$3
stop_on_err=$4
inf=$5

nic_log=nic_port_up_slot${slot}.log

if [[ $stop_on_err == "1" ]]
then
    echo "Stop on error enabled"
else
    echo "Free run mode enabled"
fi

for ite in $(seq 1 $num_ite)
do

    echo "===== Ite: $ite ====="
    python3 ./nic_test_debug.py nic_port_up -slot $slot -tcl_path "/home/diag/xin/nic${slot}/" -card_type LENI -vmarg $vmarg -inf $inf -timeout 900| tee $nic_log
    sync

    inventory -sts -slot $slot

    if [[ $stop_on_err == "1" ]]
    then
        num_err=$(grep "ERROR :" $nic_log | wc | awk -F " " '{print $1}')
        if [[ $num_err -ne 0 ]]
        then
            echo "Error has happened, exiting"
            exit -1
        else
            echo "No Error happened, continue"
        fi
    fi
done
