#!/bin/bash

# Default values
INT_LPBK=0
VMARG="normal"
OFFLOAD=1
ESEC_EN=1
SIMPLIFY=0
HC=0
DDR=1
ITE=1
JOO=1
MODE="hod"
PCT=0
PRBSLT=1
PROTO=1

usage () {
    echo "=========================="
    echo "./run_l1.sh -sn <> -slot <> -joo <> -m <> -i <> -v <> -o <> -e <> -s <> -hc <> -ddr <> -ite <> -lt <>"
    echo "sn:   SN"
    echo "slot: Slot number"
    echo "joo:  J2C or OW; J2C; 1: OW: 0; default: 1"
    echo "m:    Mode hod/hod_1100/nod/nod_525"
    echo "i:    0: external loopback; 1 internal loopback; default: 0"
    echo "v:    Voltage margin: normal/low/high; default: normal"
    echo "o:    0: offload diabled; 1: offload PCIe/ETH PRBS, TCAM, efuse tests to ARM; default: 1"
    echo "e:    0: esecure test disabled; 1: esecure test enabled; default: 1"
    echo "s:    0: simplified test disabled; 1: simlified test enabled; default: 0"
    echo "hc:   0: Soft training; 1: hardcoded DDR training; default: 0"
    echo "ddr:  0: DDR test skipped; 1: DDR test enabled"
    echo "ite:  Number of iterations"
    echo "lt:   (salina only) 0: PRBS link training off; 1: PRBS link training on"
    echo "p:    (salina only) 0: dont apply protomode; 1: test in protomode; default:1"
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
    -o|--offload)
    OFFLOAD=${2}
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
    -hc)
    HC=${2}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -ddr)
    DDR=${2}
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
    -lt)
    PRBSLT=${2}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -p)
    PROTO=${2}
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

echo "sn: $SN; slot: $SLOT; MODE: $MODE; INT_LPBK: $INT_LPBK; VMARG: $VMARG; OFFLOAD: $OFFLOAD; ESEC_EN: $ESEC_EN; SIMPLIfY: $SIMPLIFY; HC: $HC; DDR: $DDR; JOO: $JOO; LT: $PRBSLT; P: $PROTO"
VMARG_PCT=$VMARG
if [[ $VMARG == "normal" ]] 
then
    PCT=0
else
    if [[ $ASIC_TYPE == "GIGLIO" ]]
    then
        VMARG=$(echo $VMARG_PCT | cut -d "_" -f 1)
        PCT=$(echo $VMARG_PCT | cut -s -d "_" -f 2)
    fi
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
    echo "jtag_accpcie_salina clr $SLOT"
    jtag_accpcie_salina clr $SLOT

    echo "script -f $ASIC_SRC/ip/cosim/tclsh/$fn -c \"tclsh l1_test.tcl $SN $SLOT $MODE $INT_LPBK $VMARG 0 $OFFLOAD $ESEC_EN $SIMPLIFY $HC $DDR 0 $PCT $JOO $PRBSLT $PROTO \""
    script -f $ASIC_SRC/ip/cosim/tclsh/$fn -c "tclsh l1_test.tcl $SN $SLOT $MODE $INT_LPBK $VMARG 0 $OFFLOAD $ESEC_EN $SIMPLIFY $HC $DDR 0 $PCT $JOO $PRBSLT $PROTO"
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