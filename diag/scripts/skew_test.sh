# !/bin/bash

declare -a slot_list=(1 2 3 6 7 9)
declare -a card_no_list=("No41" "No42" "No43" "No46" "NO47" "No49")
core_freq=1100
arm_freq=3000

core_volt=760
arm_volt=858

volt_mode="hod"
chamber_temp="0_temp_ctrl_30"

card_config="core_freq_${core_freq}_arm_freq_${arm_freq}_core_volt_${core_volt}_arm_volt_${arm_volt}_chamber_${chamber_temp}"
echo $card_config

for idx in "${!slot_list[@]}"
do
    slot=${slot_list[$idx]}
    card_no=${card_no_list[$idx]}

    echo "=== Slot: $slot ==="
    log_file="hbm_pktgen_pcie_lb_100g_${card_no}_${card_config}.log"
    /home/diag/diag/python/regression/nic_test.py -skew -slot_list $slot -fan_ctrl -tgt_die_temp 30 | tee $log_file
done
