#!/bin/bash

slot=$1
vmarg=$2
num_ite=$3

for ite in $(seq 1 $num_ite)
do
    echo "===== Ite: $ite ====="
    ./nic_test_debug.py nic_port_up -slot $slot -tcl_path "/home/diag/xin/nic/" -card_type LENI -vmarg $vmarg
done
