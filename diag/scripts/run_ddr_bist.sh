#!/bin/bash
slot=$1
ddr_freq=$2
vmarg=$3
mode=$4
#vdd_margin_pct=$4
#arm_margin_pct=$5
#margin_pct=$6
ite=$5
if [[ $vmarg == "normal" ]]
then
    vdd_margin_pct=0
    arm_margin_pct=0
    margin_pct=0
elif [[ $vmarg == "high" ]]
then
    vdd_margin_pct=3
    arm_margin_pct=3
    margin_pct=3
elif [[ $vmarg == "low" ]]
then
    vdd_margin_pct=3
    arm_margin_pct=3
    margin_pct=3
fi
for (( idx=0; idx<$ite; idx++ ))
do
    echo "DDR BIST Iteration $idx"
    cd /home/diag/diag/scripts/asic/
    set -x
    stdbuf -i0 -o0 -e0 tclsh gig_ddr_bist.tcl -sn "slot$slot" -slot $slot -ddr_freq $ddr_freq -vmarg $vmarg -mode $mode -vdd_margin_pct $vdd_margin_pct -arm_margin_pct $arm_margin_pct -margin_pct $margin_pct | tee ddr_bist.log
    set +x
    sync
    num_fail=$(cat ddr_bist.log | grep "DDR BIST FAILED" | wc | awk -F " " '{print $1}')
    if [[ $num_fail -ne 0 ]]
    then
        echo "DDR BIST Iteration $idx failed, exiting"
        #exit 0
    fi
done
