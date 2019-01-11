# !/bin/bash
if [ "$#" -ne 3 ]; then
    echo "Wrong nubmer of input expected 3, get $#"
    echo "run_skew.sh <ite> <Temp> <fan_ctrl>"
    echo "Ite: Number of iterations"
    echo "Temp: Chamber temp"
    echo "Fan_ctrl: 0: fan control disable; 1: fan control enabled"
    exit
fi

ite=$1
TEMP=$2
FAN_CTRL=$3

#set -e
declare -a slot_list=("1" "2" "3" "4" "5" "6" "7" "8" "9")
#declare -a slot_list=("1")

declare -a freq_list=("833" "900" "967" "1033" "1100")
#declare -a freq_list=("1100")

declare -a fan_spd_list=("40" "50" "60" "70" "80")

declare -a skew_list=("SS-2.25" "SS-2.00" "SS-1.75" "TT-0.24" "TT-0.15" "TT0.04" "FF1.48" "FF1.56" "FF1.59")

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
    #set +e
    turn_on_slot.sh off all
    turn_on_slot.sh on all
    #set -e
    for freq_idx in "${!freq_list[@]}"
    do
        FREQ=${freq_list[$freq_idx]}

        if [ $FAN_CTRL -eq 1 ]
        then
            FAN=${fan_spd_list[$freq_idx]}
        else
            FAN=100
        fi
        echo "Setting Fan speed at $FAN"
        devmgr -dev=fan -speed -pct=$FAN
        sleep 3
        devmgr -dev=fan -status

        echo "=== Freq $FREQ ==="
        for slot_idx in "${!slot_list[@]}"
        do
            SLOT=${slot_list[$slot_idx]}
            SKEW=${skew_list[$slot_idx]}

            echo "=== Slot $SLOT ==="
            date_c=`date`
            echo "=== date $date_c ==="
            cd $DIAG_ROOT/diag/scripts/asic
            fn=slot$SLOT.$SKEW.FREQ$FREQ.TEMP$TEMP.FAN$FAN
            echo "fn: $fn"
            tclsh ./set_avs.tcl -sn $fn -slot $SLOT -arm_vdd vdd -freq $FREQ
            tclsh disp_volt_temp.tcl -sn $fn -slot $SLOT
            tclsh cap_snake.tcl -sn $fn -slot $SLOT -duration $duration -diag_dir $diag_dir -core_freq $FREQ
            tclsh cap_snake.tcl -sn $fn -slot $SLOT -duration $duration -mode pcie_lb -diag_dir $diag_dir -core_freq $FREQ
            tclsh l1_test.new.tcl -sn $fn -slot $SLOT -freq $FREQ
        done
    done
done
