#!/bin/bash

slot=$1
corner=$2

# Define an array
FF_vmarg_list=("FF_0" "FF_1" "FF_2" "FF_3" "FF_4" "FF_5" "FF_6" "FF_7" "FF_8" "FF_9" "FF_10" "FF_11" "FF_12" "FF_13" "FF_14")
TT_vmarg_list=("TT_0" "TT_1" "TT_2" "TT_3" "TT_4" "TT_5" "TT_6" "TT_7" "TT_8" "TT_9" "TT_10" "TT_11" "TT_12" "TT_13" "TT_14")
SS_vmarg_list=("SS_0" "SS_1" "SS_2" "SS_3" "SS_4" "SS_5" "SS_6" "SS_7" "SS_8" "SS_9" "SS_10" "SS_11" "SS_12" "SS_13" "SS_14")

FF_vmarg_list=("FF_1" "FF_2" "FF_3" "FF_4" "FF_5" "FF_6" "FF_7" "FF_8" "FF_9" "FF_10" "FF_11" "FF_12" "FF_13" "FF_14" "FF_15" "FF_16" "FF_17" "FF_18")
TT_vmarg_list=("TT_1" "TT_2" "TT_3" "TT_4" "TT_5" "TT_6" "TT_7" "TT_8" "TT_9" "TT_10" "TT_11" "TT_12" "TT_13" "TT_14" "TT_15" "TT_16" "TT_17" "TT_18")
SS_vmarg_list=("SS_1" "SS_2" "SS_3" "SS_4" "SS_5" "SS_6" "SS_7" "SS_8" "SS_9" "SS_10" "SS_11" "SS_12" "SS_13" "SS_14" "SS_15" "SS_16" "SS_17" "SS_18")

FF_vmarg_list=("FF_101" "FF_104" "FF_107" "FF_110" "FF_113" "FF_116")
TT_vmarg_list=("TT_101" "TT_104" "TT_107" "TT_110" "TT_113" "TT_116")
SS_vmarg_list=("SS_101" "SS_104" "SS_107" "SS_110" "SS_113" "SS_116")


if [[ $corner == "FF" ]]
then
    vmarg_list=("${FF_vmarg_list[@]}")
elif [[ $corner == "TT" ]]
then
    vmarg_list=("${TT_vmarg_list[@]}")
else
    vmarg_list=("${SS_vmarg_list[@]}")
fi

cd /home/diag/diag/scripts/asic/
# Iterate over the array
for vmarg in "${vmarg_list[@]}"; do
    time_stamp=$(date "+%m%d%y_%H%M%S")
    tclsh ./jtag_screen.tcl  -slot $slot -DIAG_DIR "/home/diag/xin/nic/" -vmarg ${vmarg} | tee mbist_slot${slot}_${vmarg}.log
done

