#!/bin/bash

slot=$1
testname=$2

leni48g_core_shmoo=(\
650 \
665 \
680 \
695 \
710 \
# 710 \
# 710 \
725 \
740 \
755 \
770 \
)
leni48g_arm_shmoo=(\
825 \
845 \
865 \
885 \
# 885 \
910 \
935 \
# 935 \
985 \
1010 \
1035 \
)
pollara_core_shmoo=(\
650 \
665 \
680 \
695 \
710 \
725 \
740 \
750 \
755 \
770 \
785 \
800 \
)
pollara_arm_shmoo=${pollara_core_shmoo[@]}

#    SN  ~SKEW~ARM~CORE~ TYPE
skew_selection=( \
FPK24410007~SS~740~985~LENI48G \
FPK24410008~SS~740~985~LENI48G \
FPK24410009~SS~740~985~LENI48G \
FPK2441000A~SS~740~985~LENI48G \
FPK2441000B~SS~740~985~LENI48G \
FPK24410001~TT~710~935~LENI48G \
FPK24410002~TT~710~935~LENI48G \
FPK24410003~TT~710~935~LENI48G \
FPK24410004~TT~710~935~LENI48G \
FPK24410005~TT~710~935~LENI48G \
FPK2441000C~FF~710~885~LENI48G \
FPK2441000D~FF~710~885~LENI48G \
FPK2441000E~FF~710~885~LENI48G \
FPK2441000F~FF~710~885~LENI48G \
FPK24410010~FF~710~885~LENI48G \
FPL24390013~SS~740~985~POLLARA \
FPL2439001B~SS~740~985~POLLARA \
FPL24390022~SS~740~985~POLLARA \
FPL24390044~SS~740~985~POLLARA \
FPL24390010~SS~740~985~POLLARA \
FPL2439006D~TT~725~935~POLLARA \
FPL2439009C~TT~725~935~POLLARA \
FPL2439008E~TT~710~935~POLLARA \
FPL2439004A~TT~710~935~POLLARA \
FPL24390004~TT~710~935~POLLARA \
FPL24390049~FF~710~885~POLLARA \
FPL24390018~FF~710~910~POLLARA \
FPL2439009D~FF~710~910~POLLARA \
FPL2439007E~FF~710~885~POLLARA \
FPL24390054~FF~710~885~POLLARA \
)

runsnaketest() {
    LOGFILE=$1
    slot=$2
    card_type=$3
    coreV=$4
    armV=$5

    if [[ ${card_type} == "POLLARA" ]]; then lpmode=1; else lpmode=0; fi
    if [[ ${card_type} == "POLLARA" ]]; then arm_freq="1500"; else arm_freq="default"; fi
    if [[ ${card_type} == "POLLARA" ]]; then snake_type=esam_pktgen_pollara_max_power_pcie_arm; else snake_type=esam_pktgen_max_power_pcie_sor; fi
    if [[ ${card_type} == "POLLARA" ]]; then devmgr_v2 fanctrl --pct 40; else devmgr_v2 fanctrl --pct 60; fi

    cd ~/diag/python/regression
    devmgr_v2 status | tee $LOGFILE
    fpgautil show fan | tee -a $LOGFILE
    python3 ./nic_test_v2.py nic_snake_mtp \
        -slot $slot \
        -tcl_path "/home/diag/nabeel/nic${slot}/" \
        -timeout 3600 \
        -dura 900 \
        -snake_type $snake_type \
        -vmarg none \
        -card_type ${card_type} \
        -vmargCORE ${coreV} \
        -vmargARM ${armV} \
        --lpmode ${lpmode} \
        --arm_freq ${arm_freq} \
        | tee -a $LOGFILE
    ret=$?
    if [[ $ret != 0 ]]; then echo "=== ERROR :: Test loop did not exit successfully" | tee -a $LOGFILE; fi
    grep "STAGE 2 BOOT" $LOGFILE
    ret=$?
    if [[ $ret != 0 ]]; then echo "=== ERROR :: Test loop did not initialize correctly" | tee -a $LOGFILE; fi
    tail $LOGFILE | grep " Can not connect to NIC on UART"
    ret=$?
    if [[ $ret == 0 ]]; then echo "=== ERROR :: card hung" | tee -a $LOGFILE; cd ~/diag/scripts/asic; tclsh get_nic_sts.tcl X $slot 1 | tee -a $LOGFILE; fi
}

runMBIST() {
    LOGFILE=$1
    slot=$2
    card_type=$3
    coreV=$4
    armV=$5

    if [[ ${card_type} == "POLLARA" ]]; then devmgr_v2 fanctrl --pct 40; else devmgr_v2 fanctrl --pct 60; fi

    cd ~/diag/scripts/asic
    devmgr_v2 status | tee $LOGFILE
    fpgautil show fan | tee -a $LOGFILE
    turn_on_slot.sh off $slot | tee -a $LOGFILE
    sleep 3; turn_on_slot_3v3.sh on $slot | tee -a $LOGFILE
    data=$(i2cget -y $(($slot + 2)) 0x4a 0x11)
    data=$(( $data & 0xFA ))
    data=$(( $data | 0x0A ))
    i2cset -y $((slot+2)) 0x4a 0x11 $data
    inventory -sts -slot $slot | tee -a $LOGFILE
    turn_on_slot_12v.sh on $slot | tee -a $LOGFILE
    tclsh jtag_screen.tcl \
        -slot $slot \
        -tcl_path "/home/diag/nabeel/nic${slot}/" \
        -test_list "DIAG_MBIST" \
        -vmarg "none" \
        -vmarg_core ${coreV} \
        -vmarg_arm ${armV} \
        | tee -a $LOGFILE
    ret=$?
    if [[ $ret != 0 ]]; then echo "=== ERROR :: Test loop did not exit successfully" | tee -a $LOGFILE; fi
    inventory -sts -slot $slot | tee -a $LOGFILE
}

slotsn=$(inventory -present | grep "UUT_${slot} " | sed 's/\s*]/]/g' | awk -F " " '{print $6}')
for card in "${skew_selection[@]}"; do
    sn=$(echo $card | cut -d"~" -f1)
    skew=$(echo $card | cut -d"~" -f2)
    core_fused=$(echo $card | cut -d"~" -f3)
    arm_fused=$(echo $card | cut -d"~" -f4)
    card_type=$(echo $card | cut -d"~" -f5)

    if [[ ${slotsn} != $sn ]]; then continue; fi #find the correct settings for this card

    if [[ ${card_type} == "POLLARA" ]]; then
        shmoo_core="${pollara_core_shmoo[@]}"
        shmoo_arm="${pollara_arm_shmoo[@]}"
    elif [[ ${card_type} == "LENI48G" ]]; then
        shmoo_core="${leni48g_core_shmoo[@]}"
        shmoo_arm="${leni48g_arm_shmoo[@]}"
    fi

    ## FIRST LOOP: fix core to fused, shmoo over arm
    for armV in ${shmoo_arm[*]}; do
        coreV=${core_fused}
        if [[ ${card_type} == "POLLARA" ]]; then coreV=$armV; fi
        LOGFILE=/home/diag/nabeel/skewc/${testname}_${card_type}_${sn}_slot${slot}_${skew}_CORE${coreV}_ARM${armV}.log
        echo $LOGFILE
        runMBIST $LOGFILE $slot $card_type $coreV $armV
    done

    ## SECOND LOOP: fix arm to fused, shmoo over core
    #skip pollara
    for coreV in ${shmoo_core[*]}; do
        if [[ ${card_type} == "POLLARA" ]]; then break; fi
        armV=${arm_fused}
        LOGFILE=/home/diag/nabeel/skewc/${testname}_${card_type}_${sn}_slot${slot}_${skew}_CORE${coreV}_ARM${armV}.log
        runMBIST $LOGFILE $slot $card_type $coreV $armV
    done
    break # dont continue search
done
