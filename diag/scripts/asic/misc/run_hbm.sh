# !/bin/bash

#set -e
declare -a slot_list=("1" "2" "3" "4" "5" "6" "7" "9" "10")
#declare -a slot_list=("1")

declare -a hbm_freq_list=("1600" "2000")
#declare -a hbm_freq_list=("1600")

declare -a skew_list=("SS-2.70" "SS-2.61" "SS-0.84" "TT-0.52" "TT-0.13" "FF1.11" "HBM8G" "FF1.57" "FF1.71")
#declare -a skew_list=("SS-2.70")

declare -a temp_list=("90" "105")
#declare -a temp_list=("90")

DIAG_ROOT=/home/diag/
ASIC_LIB=$DIAG_ROOT/diag/asic/asic_lib
ASIC_SRC=/$DIAG_ROOT/diag/asic//asic_src
ASIC_GEN=$DIAG_ROOT/diag/asic//asic_src
ASIC_LIB_BUNDLE=$DIAG_ROOT/diag/asic/

diag_dir=$DIAG_ROOT

FAN=80

for TEMP in "${temp_list[@]}"
do
    echo "Setting Fan speed at $FAN"
    devmgr -dev=fan -speed -pct=$FAN
    sleep 3
    devmgr -dev=fan -status

    turn_on_slot.sh off all
    turn_on_slot.sh on all

    echo "=== TEMP $TEMP ==="

    for freq_idx in "${!hbm_freq_list[@]}"
    do

        CORE_FREQ=1100
        HBM_FREQ=${hbm_freq_list[$freq_idx]}

        echo "=== Core Freq $CORE_FREQ : ARM Freq $ARM_FREQ ==="
        for slot_idx in "${!slot_list[@]}"
        do
            SLOT=${slot_list[$slot_idx]}
            SKEW=${skew_list[$slot_idx]}

            echo "=== Slot $SLOT ==="

            fn=slot$SLOT.$SKEW.CORE_FREQ$CORE_FREQ.HBM_FREQ$HBM_FREQ.TEMP$TEMP
            echo "fn: $fn"
            tclsh ./run_hbm.tcl $fn $SLOT $HBM_FREQ $TEMP 128
        done
    done
done
