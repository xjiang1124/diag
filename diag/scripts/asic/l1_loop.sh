# !/bin/bash

if [[ $# -ne 2 ]]
then
    echo "./l1_loop.sh <slot> <iteration#>"
    exit
fi

slot=$1
iter=$2

for (( i=0; $i<$iter; i++ ))
do
    echo "==== Iteration #$i (slot $slot) ===="

    #echo ""
    #echo "#### Programming QSPI Flash #0 (iteration $i) ... ####"
    #date
    #cd /home/diag/tmp

    #rm fileRandom256MB.img
    #dd if=/dev/urandom of=fileRandom256MB.img bs=256M count=1
    #./fpgautil flash $(($slot-1)) 0 program allflash fileRandom256MB.img

    #echo "#### Programming QSPI Flash #1 (iteration #i) ... ####"
    #rm fileRandom256MB.img
    #dd if=/dev/urandom of=fileRandom256MB.img bs=256M count=1
    #./fpgautil flash $(($slot-1)) 1 program allflash fileRandom256MB.img

    #echo "#### END of Programming QSPI Flash (iteration $i) ####"
    #exit 0

    echo ""
    echo "#### pwr cycle slot $slot (iteration $i) ... ####"
    date
    echo "  turn off slot $slot..."
    turn_on_slot.sh off $slot
    echo "  wait 1 seconds..."
    sleep 1 
    echo "  turn on slot $slot..."
    turn_on_slot.sh on $slot
    echo "  wait 3 seconds..."
    sleep 3
    echo "  turn on slot $slot one more time..."
    turn_on_slot.sh on $slot
    sleep 3

    reset_code=$(i2cget -y $(($slot+2)) 0x4a 0x30)
    sleep 1
    fault_code=$(i2cget -y $(($slot+2)) 0x4a 0x32)
    sleep 1
    dpu_stat0=$(i2cget -y $(($slot+2)) 0x4a 0x14)

    echo "  CPLD reset_code reg (0x30): $reset_code"
    if [[ $reset_code != "0x00" ]]
    then
        echo "    Warning: CPLD reset_code is not zero!"
    fi

    echo "  CPLD fault_code reg (0x32): $fault_code"
    if [[ $fault_code != "0x00" ]]
    then
        echo "    Warning: CPLD fault_code is not zero!"
    fi

    echo "  CPLD DPU_STAT0 reg (0x14): $dpu_stat0"
    if [[ $dpu_stat0 != "0x07" ]]
    then
        echo "    Warning: CPLD DPU_STAT0 is not 0x07!"
    fi
    echo "#### END of pwr cycle slot $slot (iteration $i) ####"

    echo ""
    echo "#### RUN L1 TESTS (iteration $i) ... ####"
    date

    echo "jtag_accpcie_salina clr $slot"
    jtag_accpcie_salina clr $slot
    sleep 1

    cd /home/diag/diag/scripts/asic
    run_l1.sh -sn "slot$slot" -slot $slot -o 0 -e 0 -ite 1
    echo "#### END of L1 TESTS (iteration $i) ####"
    echo ""
done
date
echo "== THE END of The World!!! (slot $slot) =="

