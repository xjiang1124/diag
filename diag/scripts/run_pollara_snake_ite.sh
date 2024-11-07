#!/bin/bash

slot=$1
vmarg=$2
num_ite=$3
stop_on_err=$4
mtp_clk=$5

nic_log=nic_port_up_slot${slot}.log
snake_type="esam_pktgen_pollara_max_power_pcie_arm"

if [[ $stop_on_err == "1" ]]
then
    echo "Stop on error enabled"
else
    echo "Free run mode enabled"
fi

for ite in $(seq 1 $num_ite)
do
    echo "===== Ite: $ite ====="
    ./nic_test_v2.py nic_snake_mtp  -slot $slot  -tcl_path "/home/diag/xin/nic${slot}/"  -timeout 3600 -dura 300 -snake_type  $snake_type -card_type POLLARA -vmarg ${vmarg} -mtp_clk ${mtp_clk} | tee $nic_log
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
