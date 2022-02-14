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
#declare -a slot_list=("1" "2" "3" "4" "5" "6" "7" "8" "9" "10")
declare -a slot_list=("1" "2" "3" "4" "5" "6" "8" "9" "10")
declare -a slot_list=("10")

declare -a core_freq_list=("833" "1100" "417" "208")
declare -a arm_freq_list=("2000" "2200" "1600" "1100")

declare -a core_freq_list=("833" "1100")
declare -a arm_freq_list=("2000" "2200")

declare -a core_freq_list=("1100")
declare -a arm_freq_list=("2200")

#declare -a skew_list=("SS-2.70" "SS-2.61" "SS-0.84" "TT-0.52" "TT-0.13" "FF1.11" "FF1.29" "FF1.50" "FF1.57" "FF1.71")
declare -a skew_list=("SS-2.70" "SS-2.61" "SS-0.84" "TT-0.52" "TT-0.13" "FF1.11" "FF1.50" "FF1.57" "FF1.71")
declare -a skew_list=("FF1.71")

declare -a temp_list=("90" "125")
#declare -a temp_list=("90")
declare -a temp_list=("115")

DIAG_ROOT=/home/diag/
ASIC_LIB=$DIAG_ROOT/diag/asic/asic_lib
ASIC_SRC=/$DIAG_ROOT/diag/asic//asic_src
ASIC_GEN=$DIAG_ROOT/diag/asic//asic_src
ASIC_LIB_BUNDLE=$DIAG_ROOT/diag/asic/

duration=600
diag_dir=$DIAG_ROOT

FAN=80
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

    for TEMP in "${temp_list[@]}"
    do
        # Adjust init fan speed for different temp level to allow more time to stablization
        if [ $TEMP == "90" ]
        then
            FAN=70
        else
            FAN=80
        fi
        echo "Setting Fan speed at $FAN"
        devmgr -dev=fan -speed -pct=$FAN
        sleep 3
        devmgr -dev=fan -status

        for freq_idx in "${!core_freq_list[@]}"
        do
            turn_on_slot.sh off all
            turn_on_slot.sh on all

            echo "=== TEMP $TEMP ==="
            CORE_FREQ=${core_freq_list[$freq_idx]}
            ARM_FREQ=${arm_freq_list[$freq_idx]}

            echo "=== Core Freq $CORE_FREQ : ARM Freq $ARM_FREQ ==="
            for slot_idx in "${!slot_list[@]}"
            do
                SLOT=${slot_list[$slot_idx]}
                SKEW=${skew_list[$slot_idx]}

                echo "=== Slot $SLOT ==="

                fn=slot$SLOT.$SKEW.CORE_FREQ$CORE_FREQ.TEMP$TEMP.FAN$FAN_NAME
                echo "fn: $fn"
                tclsh ./set_avs.tcl -sn $fn -slot $SLOT -arm_vdd vdd -freq $CORE_FREQ -use_pmro 0

                fn=slot$SLOT.$SKEW.ARM_FREQ$ARM_FREQ.TEMP$TEMP.FAN$FAN_NAME
                echo "fn: $fn"
                tclsh ./set_avs.tcl -sn $fn -slot $SLOT -arm_vdd arm -freq $ARM_FREQ -use_pmro 0

                fn=slot$SLOT.$SKEW.CORE_FREQ$CORE_FREQ.ARM_FREQ$ARM_FREQ.TEMP$TEMP.FAN$FAN_NAME
                echo "fn: $fn"

                #tclsh disp_volt_temp.tcl -sn $fn -slot $SLOT
                tclsh cap_snake.tcl -sn $fn -slot $SLOT -duration $duration -diag_dir $diag_dir -core_freq $CORE_FREQ -fan_ctrl 1 -tgt_temp $TEMP -mac_lb 0
                #tclsh cap_snake.tcl -sn $fn -slot $SLOT -duration $duration -mode pcie_lb -diag_dir $diag_dir -core_freq $FREQ
                #tclsh l1_test.new.tcl -sn $fn -slot $SLOT -freq $FREQ
            done
        done
    done
done
