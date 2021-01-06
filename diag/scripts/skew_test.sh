# !/bin/bash

declare -a slot_list=(1 2 3 4 5 6 7 8 9)
declare -a card_no_list=("Ortano_No33" "Ortano_No32" "Ortano_No31" "Ortano_No34" "Ortano_No35" "Ortano_No36" "Ortano_No38" "Ortano_No37" "Ortano_No39")

declare -a slot_list=(1 2 3 4 5 7 8)
declare -a card_no_list=("Ortano_No33" "Ortano_No32" "Ortano_No31" "Ortano_No34" "Ortano_No35" "Ortano_No38" "Ortano_No37")

declare -a slot_list=(4 5 7 8)
declare -a card_no_list=("Ortano_No34" "Ortano_No35" "Ortano_No38" "Ortano_No37")

core_freq=833
arm_freq=2000

core_volt=665
arm_volt=689

volt_mode="nod"
tgt_die_temp="NONE"
chamber_temp="0_temp_ctrl_$tgt_die_temp"

card_config="core_freq_${core_freq}_arm_freq_${arm_freq}_core_volt_${core_volt}_arm_volt_${arm_volt}_chamber_${chamber_temp}"
echo $card_config

for idx in "${!slot_list[@]}"
do
    slot=${slot_list[$idx]}
    card_no=${card_no_list[$idx]}

    echo "=== Slot: $slot ==="
    log_file="hbm_pktgen_pcie_lb_100g_${card_no}_${card_config}.log"
    devmgr -dev=fan -speed -pct=100
    #/home/diag/diag/python/regression/nic_test.py -skew -slot_list $slot -fan_ctrl -tgt_die_temp $tgt_die_temp | tee $log_file
    /home/diag/diag/python/regression/nic_test.py -skew -slot_list $slot | tee $log_file
done

