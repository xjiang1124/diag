# !/bin/bash

#set -e
#declare -a slot_list=("1" "2" "3" "8" "9")
#declare -a card_no_list=("OT31" "OT32" "OT33" "OT38" "OT39")

declare -a slot_list=("2" "4")
declare -a sn_list=("USFLUPK19G0034" "USFLUPK19G0022")

# 0: external loopback; 1: internal loopback
int_lpbk=1

turn_on_slot.sh off all

for slot_idx in "${!slot_list[@]}"
do
    SLOT=${slot_list[$slot_idx]}
    SN=${sn_list[$slot_idx]}

    mode="nod_550"
    int_lpbk=0
    offload=1
    esecEn=1

    turn_on_slot.sh on $SLOT

    echo "=== Slot $SLOT ==="
    #l1_test.sh $CARD_NO $SLOT 0 normal 0 0 1
    #tclsh ./l1_test.tcl $CARD_NO $SLOT $int_lpbk normal 0 0 1
    stdbuf_tclsh.sh /home/diag/diag/scripts/asic/l1_test.tcl $SN $SLOT $mode $int_lpbk normal 0 $offload $esecEn
    inventory -sts -slot $SLOT

    turn_on_slot.sh off $SLOT
done

