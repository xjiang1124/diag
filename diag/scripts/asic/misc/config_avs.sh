# !/bin/bash

declare -a arr=(1 3 5 6 7 9)
declare -a arr=(1 3 6 7 9)
declare -a arr=(9)
#declare -a arr=(1)

for slot in "${arr[@]}"
do
    echo "=== Slot: $slot ==="
    turn_on_slot.sh on $slot
    tclsh ./set_avs.tcl -sn slot$slot -slot $slot -arm_vdd vdd -core_freq 417 -arm_freq 1600
    tclsh ./set_avs.tcl -sn slot$slot -slot $slot -arm_vdd arm -core_freq 417 -arm_freq 1600
    turn_on_slot.sh off $slot
done
