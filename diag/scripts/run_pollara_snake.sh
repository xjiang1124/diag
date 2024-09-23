#!/bin/bash

if [[ $1 == "-h" || $1 == "-help" || $# -ne 5 ]]
then
    echo "Usage: ./$(basename $0) <slot> <corner_index> <nic_path> <snake_type> <duration>"
    exit
fi

slot=$1
corner=$2
tcl_path=$(realpath -sm $3)
snake_name=$4
dura=$5

if [[ $slot == 1 ]]
then
    ln -s $tcl_path ${tcl_path}${slot}
else
    rm -fr ${tcl_path}${slot}
    cp -r $tcl_path ${tcl_path}${slot}
fi
tcl_path=${tcl_path}${slot}
echo "run_pollara_snake.sh :: tcl_path: $tcl_path"

# Define an array
FF_vmarg_list=("FF_1" "FF_2" "FF_3" "FF_4" "FF_5" "FF_6" "FF_7" "FF_8" "FF_9")
TT_vmarg_list=("TT_1" "TT_2" "TT_3" "TT_4" "TT_5" "TT_6" "TT_7" "TT_8" "TT_9")
SS_vmarg_list=("SS_1" "SS_2" "SS_3" "SS_4" "SS_5" "SS_6" "SS_7" "SS_8" "SS_9")

if [[ $corner == "FF" ]]
then
    vmarg_list=("${FF_vmarg_list[@]}")
elif [[ $corner == "TT" ]]
then
    vmarg_list=("${TT_vmarg_list[@]}")
elif [[ $corner == "SS" ]]
then
    vmarg_list=("${SS_vmarg_list[@]}")
else
    vmarg_list=("normal")
fi

# Iterate over the array
for vmarg in "${vmarg_list[@]}"; do
    time_stamp=$(date "+%m%d%y_%H%M%S")
    ./nic_test_v2.py nic_snake_mtp -slot $slot -tcl_path $tcl_path -timeout 3600 -dura $dura -snake_type $snake_name -card_type POLLARA -vmarg ${vmarg} | tee snake_slot${slot}_${vmarg}.log
done

