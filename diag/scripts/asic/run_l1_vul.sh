#!/bin/bash

# Default values
INT_LPBK=1
VMARG="normal"
ESEC_EN=1
ITE=1
PCT=0
REPORT_MODE=0
SKIP_SERDES=0
TCL_PATH=""

usage () {
    echo "=========================="
    echo "./run_l1.sh -sn <> -slot <> -i <> -v <> -e <> -t <> -r <> -k <> -ite <>"
    echo "sn:   SN"
    echo "slot: Slot number"
    echo "i:    0: external loopback; 1 internal loopback; default: 0"
    echo "v:    Voltage margin: nom/low/high; default: nom"
    echo "e:    0: esecure test disabled; 1: esecure test enabled; default: 1"
    echo "t:    Tcl_path"
    echo "r:    skip_l1_report_mode: 0 or 1"
    echo "k:    skip_serdes_tests: 0 or 1"
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
    -i|--int_lpbk)
    INT_LPBK="${2}"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -v|--vmarg)
    VMARG=${2,,:-nom}
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
    -t|--tcl_path)
    TCL_PATH=${2}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -r|--report_mode)
    REPORT_MODE=${2}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -k|--skip_serdes)
    SKIP_SERDES=${2}
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

echo "sn: $SN; slot: $SLOT; INT_LPBK: $INT_LPBK; VMARG: $VMARG; ESEC_EN: $ESEC_EN; REPORT_MODE: $REPORT_MODE; SKIP_SERDES: $SKIP_SERDES; TCL_PATH: $TCL_PATH"
if [[ $VMARG == "nom" ]]
then
    PCT=0
fi
#echo "vmarg: $VMARG; pct: $PCT"

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

    echo "script -f $ASIC_SRC/ip/cosim/tclsh/$fn -c \"tclsh l1_test_vul.tcl $SN $SLOT $INT_LPBK $VMARG $ESEC_EN 1 $PCT $REPORT_MODE $SKIP_SERDES $TCL_PATH\""
    script -f $ASIC_SRC/ip/cosim/tclsh/$fn -c "tclsh l1_test_vul.tcl $SN $SLOT $INT_LPBK $VMARG $ESEC_EN 1 $PCT $REPORT_MODE $SKIP_SERDES $TCL_PATH"
    ret=$?
    sync
    num_fail=$(cat $ASIC_SRC/ip/cosim/tclsh/$fn | grep "L1_SCREEN FAILED" | wc | awk -F " " '{print $1}')
    if [[ $num_fail -ne 0 ]]
    then
        echo "L1 TEST FAILED"
        ret=-1
    else
        echo "L1 TEST PASSED"
        ret=0
    fi

done

exit $ret