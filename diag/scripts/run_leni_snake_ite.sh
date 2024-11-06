#!/bin/bash

slot=$1
vmarg=$2
num_ite=$3
stop_on_err=$4
mtp_clk=$5

nic_log=nic_snake_slot${slot}.log
snake_type="esam_pktgen_max_power_pcie_sor"

if [[ $stop_on_err == "1" ]]
then
    echo "Stop on error enabled"
else
    echo "Free run mode enabled"
fi

for ite in $(seq 1 $num_ite)
do

    echo "===== Ite: $ite ====="
    #python3 ./nic_test_debug.py nic_port_up -slot $slot -tcl_path "/home/diag/xin/nic${slot}/" -card_type LENI -vmarg $vmarg -inf $inf -timeout 900| tee $nic_log
    ./nic_test_v2.py nic_snake_mtp  -slot $slot  -tcl_path "/home/diag/xin/nic${slot}/"  -timeout 3600 -dura 300 -snake_type  $snake_type -card_type LENI -vmarg ${vmarg} -mtp_clk ${mtp_clk} | tee $nic_log

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
