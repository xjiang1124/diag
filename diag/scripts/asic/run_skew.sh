# !/bin/bash
if [ "$#" -ne 2 ]; then
    echo "Wrong nubmer of input expected 3, get $#"
    echo "run_skew.sh <ite> <fan_ctrl>"
    echo "Ite: Number of iterations"
    echo "Fan_ctrl: 0: fan control disable; 1: internal control"
    exit
fi

ite=$1
FAN_CTRL=$2

#set -e
declare -a slot_list=("1" "2" "3" "4" "5" "6" "8" "9" "10")
declare -a slot_list=("9" "10")

#declare -a freq_list=("833" "900" "967" "1033" "1100")
declare -a freq_list=("833" "1100")
declare -a freq_list=("1100")

declare -a skew_list=("SS-2.25" "SS-2.00" "SS-1.75" "TT-0.24" "TT-0.15" "TT0.04" "FF1.56" "FF1.59" "FF1.48")
declare -a skew_list=("FF1.59" "FF1.48")

declare -a temp_list=("90")

DIAG_ROOT=/home/diag/
ASIC_LIB=$DIAG_ROOT/diag/asic/asic_lib
ASIC_SRC=/$DIAG_ROOT/diag/asic//asic_src
ASIC_GEN=$DIAG_ROOT/diag/asic//asic_src
ASIC_LIB_BUNDLE=$DIAG_ROOT/diag/asic/

duration=600
diag_dir=$DIAG_ROOT

FAN=100
if [ $FAN_CTRL -eq 1 ]
then
    FAN_NAME="_CTRL"
else
    FAN_NAME=100
fi
echo "Setting Fan speed at $FAN"
devmgr -dev=fan -speed -pct=$FAN
sleep 3
devmgr -dev=fan -status

for i in `seq 1 $ite`;
do
    echo "=== Ite $i ==="
    turn_on_slot.sh off all
    turn_on_slot.sh on all

    for TEMP in "${temp_list[@]}"
    do
        for freq_idx in "${!freq_list[@]}"
        do
            echo "=== TEMP $TEMP ==="
            FREQ=${freq_list[$freq_idx]}

            echo "=== Freq $FREQ ==="
            for slot_idx in "${!slot_list[@]}"
            do
                SLOT=${slot_list[$slot_idx]}
                SKEW=${skew_list[$slot_idx]}

                echo "=== Slot $SLOT ==="
                date_c=`date`
                echo "=== date $date_c ==="
                cd $DIAG_ROOT/diag/scripts/asic
                fn=slot$SLOT.$SKEW.VOLT_800.FREQ$FREQ.TEMP$TEMP.FAN$FAN_NAME
                echo "fn: $fn"
                tclsh ./set_avs.tcl -sn $fn -slot $SLOT -arm_vdd vdd -freq $FREQ -use_pmro 1

                #tclsh disp_volt_temp.tcl -sn $fn -slot $SLOT
                #tclsh cap_snake.tcl -sn $fn -slot $SLOT -duration $duration -diag_dir $diag_dir -core_freq $FREQ -fan_ctrl 1 -tgt_temp $TEMP -mac_lb 0
                #tclsh cap_snake.tcl -sn $fn -slot $SLOT -duration $duration -mode pcie_lb -diag_dir $diag_dir -core_freq $FREQ
                #tclsh l1_test.new.tcl -sn $fn -slot $SLOT -freq $FREQ
            done
        done
    done
done
