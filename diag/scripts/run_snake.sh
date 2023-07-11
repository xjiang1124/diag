#!/bin/bash
slot_list=$1

#==============
# config
ite=10

vmarg="normal"
vmarg="high"

stop_on_error=0

#==============

for idx in $(seq 1 1 $ite)
do
    echo "=== Ite: $idx ==="
    #stdbuf -i0 -o0 -e0 python ./nic_test.py -snake -slot_list $slot_list -mode hod -int_lpbk -dura 3 -snake_num 4 -wtime 600 -vmarg $vmarg | tee snake_ite.log
    stdbuf -i0 -o0 -e0 python ./nic_test.py -snake -slot_list $slot_list -mode nod_525 -int_lpbk -dura 120 -snake_num 6 -wtime 300 -vmarg $vmarg | tee snake_ite.log
    sync
 
    IFS=',' read -r -a slot_list1 <<< "$slot_list"

    for slot in "${slot_list1[@]}"
    do
        echo "=== Checking result: $slot ==="

        num_slot=${#slot_list1[@]}
        slot_info=$(grep -a -A${num_slot} "TEST RESULT: SNAKE" snake_ite.log | grep "Slot ${slot} ")
        echo $slot_info
 
        num_pass=$(echo $slot_info | grep PASS | wc | awk -F " " '{print $1}')
        if [[ $num_pass -ne 1 ]]
        then
            tclsh ~/diag/scripts/asic/read_ecc_reg.tcl $slot
            if [[ $stop_on_error -ne 0 ]]
            then
                exit 0
            fi
        fi

    done
 
    #num_pass=$(cat snake_ite.log | grep -a -E "Slot.*[PASS|FAIL].*" | grep PASS | wc | awk -F " " '{print $1}')
    #if [[ $num_pass -ne 1 ]]
    #then
    #    tclsh ~/diag/scripts/asic/read_ecc_reg.tcl $slot
    #    exit 0
    #fi

    #num_fail=$(cat snake_ite.log | grep -a -E "Slot.*[PASS|FAIL].*" | grep FAIL | wc | awk -F " " '{print $1}')
    #if [[ $num_fail -ne 0 ]]
    #then
    #    tclsh ~/diag/scripts/asic/read_ecc_reg.tcl $slot
    #    exit 0
    #fi

done
