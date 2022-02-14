# !/bin/bash

declare -a arr=(1 3 5 6 7 9)
# Done
#declare -a arr=(1 3 6 9)

declare -a arr=(5 7)

turn_on_slot.sh off all

for slot in "${arr[@]}"
do
    echo "=== Slot: $slot ==="
    turn_on_slot.sh on $slot
    tclsh ./l1_test.tcl slot$slot $slot 0 normal 0 0 1
    turn_on_slot.sh off $slot
done
