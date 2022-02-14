# !/bin/bash

declare -a slot_list=(1 2 3 4 5 6 7 8 9 10)

for slot in "${slot_list[@]}"
do
    echo "=== Slot: $slot ==="
    ip=$(expr 100 + $slot)
    ping -c 4 10.1.1.$ip
done

