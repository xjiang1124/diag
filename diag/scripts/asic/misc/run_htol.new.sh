# !/bin/bash
if [ "$#" -ne 2 ]; then
    echo "Wrong nubmer of input expected 2, get $#"
    exit
fi

ite=$1
TEMP=$2

#set -e
declare -a slot_list=("1" "2" "3" "4" "5" "6" "7" "9")

declare -a freq_list=("833" "900" "967" "1033" "1100")
#declare -a freq_list=("1100")

DIAG_ROOT=/home/diag/
ASIC_LIB=$DIAG_ROOT/diag/asic/asic_lib
ASIC_SRC=/$DIAG_ROOT/diag/asic//asic_src
ASIC_GEN=$DIAG_ROOT/diag/asic//asic_src
ASIC_LIB_BUNDLE=$DIAG_ROOT/diag/asic/

duration=600
diag_dir=$DIAG_ROOT
FAN=100

for i in `seq 1 $ite`;
do
    echo "=== Ite $i ==="
    #set +e
    turn_on_slot.sh off all
    turn_on_slot.sh on all
    #set -e
    for FREQ in "${freq_list[@]}"
    do
        echo "=== Freq $FREQ ==="
        for SLOT in "${slot_list[@]}"
        do
            case $SLOT in
                "1")
                    SKEW="SS-2.25"
                    ;;
                "2")
                    SKEW="SS-2.00"
                    ;;
                "3")
                    SKEW="SS-1.75"
                    ;;
                "4")
                    SKEW="TT-0.24"
                    ;;
                "5")
                    SKEW="TT-0.15"
                    ;;
                "6")
                    SKEW="TT0.04"
                    ;;
                "7")
                    SKEW="FF1.48"
                    ;;
                "8")
                    SKEW="FF1.56"
                    ;;
                "9")
                    SKEW="FF1.59"
                    ;;
                *)
                    echo "invalid input", $1
                    exit
            esac


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
            #tclsh l1_test.tcl $fn $SLOT
            tclsh l1_test.new.tcl -sn $fn -slot $SLOT -freq $FREQ
        done
    done
done
