#!/bin/bash

slot=$1
vmarg=$2
num_ite=$3
stop_on_err=$4
mtp_clk=$5

if [[ $stop_on_err == "1" ]]
then
    echo "Stop on error enabled"
else
    echo "Free run mode enabled"
fi

echo "mtp_clk $mtp_clk"

card_type_v="UUT_${slot}"
card_type=${!card_type_v}
echo "card_type $card_type"

sn=$(inventory -present | grep "UUT_${slot} " | sed 's/\s*]/]/g' | awk -F " " '{print $6}')
echo "sn: $sn"

nic_log=/home/diag/xin/pcie_prbs_slot${slot}_${sn}_${vmarg}.log

echo "pcie_prbs_slot${slot}_${sn}_${vmarg}"  | tee $nic_log


cd ~/diag/scripts/asic/

for ite in $(seq 1 $num_ite)
do

    echo "===== Ite: $ite =====" | tee -a $nic_log
    turn_on_slot.sh off $slot
    sleep 5
    turn_on_slot.sh on $slot
    sleep 15

    #tclsh /home/diag/xin/sal_pcie_aw_ber_collect.pollara_v2.tcl -slot $slot -card_type $card_type -dura 600 -aw_txfir_ow 9 -cap_ffe 0| tee -a $nic_log
    tclsh sal_pcie_prbs.pollara_v2.tcl -slot $slot -card_type $card_type -dura 60 | tee -a $nic_log
    inventory -sts -slot $slot | tee -a $nic_log

    if [[ $stop_on_err == "1" ]]
    then
        num_err=$(grep -a "ERROR :" $nic_log | wc | awk -F " " '{print $1}')
        if [[ $num_err -ne 0 ]]
        then
            echo "Error has happened, exiting"
            exit -1
        else
            echo "No Error happened, continue"
        fi
    fi
done
