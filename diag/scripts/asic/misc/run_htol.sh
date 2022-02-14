# !/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Wrong nubmer of input expected 2, get $#"
    exit
fi

ite=$1

#set -e
declare -a slot_list=("1" "2" "3" "4" "5" "6" "7" "9")

DIAG_ROOT=/home/diag/
ASIC_LIB=$DIAG_ROOT/diag/asic/asic_lib
ASIC_SRC=/$DIAG_ROOT/diag/asic//asic_src
ASIC_GEN=$DIAG_ROOT/diag/asic//asic_src
ASIC_LIB_BUNDLE=$DIAG_ROOT/diag/asic/

duration=600
diag_dir=$DIAG_ROOT

for i in `seq 1 $ite`;
do
    echo "=== Ite $i ==="
    turn_on_slot.sh off all
    turn_on_slot.sh on all
    for SLOT in "${slot_list[@]}"
    do
        echo "=== Slot $SLOT ==="
        date_c=`date`
        echo "=== $date_c ==="
        cd $DIAG_ROOT/diag/scripts/asic
        fn=slot$SLOT
        tclsh cap_snake.tcl -sn $fn -slot $SLOT -duration $duration -diag_dir $diag_dir
        tclsh cap_snake.tcl -sn $fn -slot $SLOT -duration 600 -mode pcie_lb -diag_dir $diag_dir
        tclsh l1_test.tcl $fn $SLOT
    done
done
