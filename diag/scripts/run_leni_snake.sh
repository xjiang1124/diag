#!/bin/bash

slot=$1
corner=$2

if [[ $slot == 1 ]]
then
    ln -s /home/diag/xin/nic/ /home/diag/xin/nic1/
else
    rm -r /home/diag/xin/nic${slot}/
    cp -r /home/diag/xin/nic/ /home/diag/xin/nic${slot}/
fi

# Define an array
FF_vmarg_list=("FF_0" "FF_1" "FF_2" "FF_3" "FF_4" "FF_5" "FF_6" "FF_7" "FF_8" "FF_9" "FF_10" "FF_11" "FF_12" "FF_13" "FF_14")
TT_vmarg_list=("TT_0" "TT_1" "TT_2" "TT_3" "TT_4" "TT_5" "TT_6" "TT_7" "TT_8" "TT_9" "TT_10" "TT_11" "TT_12" "TT_13" "TT_14")
SS_vmarg_list=("SS_0" "SS_1" "SS_2" "SS_3" "SS_4" "SS_5" "SS_6" "SS_7" "SS_8" "SS_9" "SS_10" "SS_11" "SS_12" "SS_13" "SS_14")

FF_vmarg_list=("FF_1" "FF_2" "FF_3" "FF_4" "FF_5" "FF_6" "FF_7" "FF_8" "FF_9" "FF_10" "FF_11" "FF_12" "FF_13" "FF_14" "FF_15" "FF_16" "FF_17" "FF_18")
TT_vmarg_list=("TT_1" "TT_2" "TT_3" "TT_4" "TT_5" "TT_6" "TT_7" "TT_8" "TT_9" "TT_10" "TT_11" "TT_12" "TT_13" "TT_14" "TT_15" "TT_16" "TT_17" "TT_18")
SS_vmarg_list=("SS_1" "SS_2" "SS_3" "SS_4" "SS_5" "SS_6" "SS_7" "SS_8" "SS_9" "SS_10" "SS_11" "SS_12" "SS_13" "SS_14" "SS_15" "SS_16" "SS_17" "SS_18")


if [[ $corner == "FF" ]]
then
    vmarg_list=("${FF_vmarg_list[@]}")
elif [[ $corner == "TT" ]]
then
    vmarg_list=("${TT_vmarg_list[@]}")
else
    vmarg_list=("${SS_vmarg_list[@]}")
fi

# Iterate over the array
for vmarg in "${vmarg_list[@]}"; do
    time_stamp=$(date "+%m%d%y_%H%M%S")
    #./nic_test_v2_working.py nic_snake_mtp -slot ${slot} -ite 1 -timeout 3600 -dura 900 -snake_type esam_pktgen_pcie_mtp_sor -card_type LENI -vmarg ${vmarg} | tee slot_${slot}_${vmarg}_snake.log
    #./nic_test_v2_yanmin.py nic_snake_mtp -slot ${slot} -ite 1 -timeout 3600 -dura 900 -snake_type esam_pktgen_ddr_arm_sor -card_type LENI -vmarg ${vmarg} | tee slot_${slot}_${vmarg}_snake.log
    #./nic_test_v2.py nic_snake_mtp -slot $slot -ite 1 -timeout 3600 -dura 900 -snake_type esam_pktgen_ddr_arm_sor   -card_type LENI -vmarg ${vmarg} | tee snake_slot${slot}_${vmarg}.log
    #./nic_test_v2.py nic_snake_mtp -slot $slot -ite 1 -timeout 3600 -dura 900 -snake_type esam_pktgen_max_power_sor -card_type LENI -vmarg ${vmarg} | tee snake_slot${slot}_${vmarg}.log
    #./nic_test_v2_pcie.py nic_snake_mtp -slot $slot -ite 1 -timeout 3600 -dura 900 -snake_type esam_pktgen_max_power_sor -card_type LENI -vmarg ${vmarg} | tee snake_slot${slot}_${vmarg}.log
    #./nic_test_v2_yanmin_2_lt.py nic_snake_mtp -slot $slot -ite 1 -timeout 3600 -dura 900 -snake_type esam_pktgen_max_power_sor -card_type LENI -vmarg ${vmarg} | tee snake_slot${slot}_${vmarg}.log
    ./nic_test_v2_yanmin_2.py nic_snake_mtp    -slot $slot -ite 1 -timeout 3600 -dura 900 -snake_type esam_pktgen_max_power_sor -card_type LENI -vmarg ${vmarg} | tee snake_slot${slot}_${vmarg}.log
done

