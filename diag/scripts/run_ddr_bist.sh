#!/bin/bash
slot=$1
vmarg=$2
ite=$3
for (( idx=0; idx<$ite; idx++ ))
do
    echo "DDR BIST Iteration $idx"
    cd /home/diag/diag/scripts/asic/
    set -x
    stdbuf -i0 -o0 -e0 tclsh gig_ddr_bist.tcl -sn "slot$slot" -slot $slot -vmarg $vmarg | tee ddr_bist.log
    set +x
    sync
    num_fail=$(cat ddr_bist.log | grep "DDR BIST FAILED" | wc | awk -F " " '{print $1}')
    if [[ $num_fail -ne 0 ]]
    then
        echo "DDR BIST Iteration $idx failed, exiting"
        #exit 0
    fi
done
