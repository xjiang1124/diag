SLOT=$1
ITE=$2
for (( idx=0; idx<$ITE; idx++ ))
do
    echo "JTAG Iteration $idx"
    turn_on_slot.sh off $SLOT && sleep 10 && turn_on_slot.sh on $SLOT 0 && sleep 10
    echo "jtag_accpcie_salina clr $SLOT"
    jtag_accpcie_salina clr $SLOT

    SN=$(inventory -present | grep UUT_$SLOT | awk '{print $NF}')
    time_stamp=$(date "+%m%d%y_%H%M%S")
    fn="jtag_screen_${SN}_${time_stamp}.log"

    echo "script -f $ASIC_SRC/ip/cosim/tclsh/$fn -c \"tclsh jtag_screen.tcl $SLOT 1\""
    script -f $ASIC_SRC/ip/cosim/tclsh/$fn -c "tclsh /home/diag/diag/scripts/asic/jtag_screen.tcl $SLOT 1"
    sync
done
