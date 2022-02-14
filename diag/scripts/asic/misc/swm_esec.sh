# !/bin/bash

#declare -a arr=(1 3 5 6 7 9)
declare -a arr=(1 3 6 9)

turn_on_slot.sh off all

for slot in "${arr[@]}"
do
    echo "=== Slot: $slot ==="
    turn_on_slot.sh on $slot
    ./esec_ctrl.py -img_prog -slot $slot
    ./esec_ctrl.py -esec_prog -slot $slot -sn 5UPYWW010$slot -pn "P26967-B21" -mac 00:AE:CD:00:00:00 -brd_name NAPLES25SWM -mtp MTP100
    turn_on_slot.sh off $slot
done
