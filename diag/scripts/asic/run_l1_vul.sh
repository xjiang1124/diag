#!/bin/bash

# Default values
INT_LPBK=0
VMARG="normal"
ESEC_EN=1
SIMPLIFY=0
ITE=1
JOO=1
MODE="hod"
PCT=0
#PRBSLT=1

usage () {
    echo "=========================="
    echo "./run_l1.sh -sn <> -slot <> -joo <> -m <> -i <> -v <> -o <> -e <> -s <> -ite <>"
    echo "sn:   SN"
    echo "slot: Slot number"
    echo "joo:  J2C or OW; J2C; 1: OW: 0; default: 1"
    echo "m:    Mode"
    echo "i:    0: external loopback; 1 internal loopback; default: 0"
    echo "v:    Voltage margin: normal/low/high; default: normal"
    echo "e:    0: esecure test disabled; 1: esecure test enabled; default: 1"
    echo "s:    0: simplified test disabled; 1: simlified test enabled; default: 0"
    echo "ite:  Number of iterations"
    echo "=========================="
}


POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"
case $key in
    #-------------
    -sn|--sn)
    SN=${2^^}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -slot|--slot)
    SLOT=${2^^}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -joo|--joo)
    JOO=${2^^}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -m|--mode)
    MODE=${2,,}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -i|--int_lpbk)
    INT_LPBK="${2}"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -v|--vmarg)
    VMARG=${2,,:-normal}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -e|--esec_en)
    ESEC_EN=${2}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -s|--simplify)
    SIMPLIFY=${2}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -ite)
    ITE=${2}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -h)
    usage
    exit 0
    ;;
    #-------------
    *)    # unknown option
    usage
    exit 0
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

echo "sn: $SN; slot: $SLOT; INT_LPBK: $INT_LPBK; VMARG: $VMARG; ESEC_EN: $ESEC_EN; SIMPLIfY: $SIMPLIFY; JOO: $JOO"
if [[ $VMARG == "normal" ]]
then
    PCT=0
fi
echo "vmarg: $VMARG; pct: $PCT"

time_stamp=$(date "+%m%d%y_%H%M%S")
fn="l1_screen_board_${SN}_${time_stamp}.log"
if [[ $JOO == "0" ]]; then
    fn="l1_ow_screen_board_${SN}_${time_stamp}.log"
fi
echo $fn

for (( idx=0; idx<$ITE; idx++ ))
do
    echo "L1 Iteration $idx"
    echo "jtag_accpcie_vulcano clr $SLOT"
    jtag_accpcie_vulcano clr $SLOT

    echo "script -f $ASIC_SRC/ip/cosim/tclsh/$fn -c \"tclsh l1_test_vul.tcl $SN $SLOT $INT_LPBK $VMARG $ESEC_EN 0 $PCT $JOO 1\""
    script -f $ASIC_SRC/ip/cosim/tclsh/$fn -c "tclsh l1_test_vul.tcl $SN $SLOT $INT_LPBK $VMARG $ESEC_EN 0 $PCT $JOO 1"
    ret=$?
    sync
    num_fail=$(cat $ASIC_SRC/ip/cosim/tclsh/$fn | grep "L1 SCREENING FAILED" | wc | awk -F " " '{print $1}')
    if [[ $num_fail -ne 0 ]]
    then
        echo "L1 Iteration $idx failed"
        ret=-1
    fi

done

exit $ret