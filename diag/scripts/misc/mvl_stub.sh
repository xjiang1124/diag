# !/bin/bash

declare -a arr=(1 2 3 4 5)

for slot in "${arr[@]}"
do
    echo "=== Slot: $slot ==="
    diag -r -d mvl -t stub -p "ite=10"  -c nic$slot
done

diag -shist | grep -e NIC -e STUB
