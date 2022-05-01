#!/bin/bash

# Default values
INT_LPBK=0
VMARG="normal"
OFFLOAD=1
ESEC_EN=1
SIMPLIFY=0
HC=1
DDR=1

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
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

echo "sn: $SN; slot: $SLOT; MODE: $MODE; INT_LPBK: $INT_LPBK; VMARG: $VMARG; OFFLOAD: $OFFLOAD; ESEC_EN: $ESEC_EN; SIMPLIfY: $SIMPLIFY; HC: $HC; DDR: $DDR"


time_stamp=$(date "+%m%d%y_%H%M%S")

fn="l1_screen_board_${SN}_${time_stamp}.log"
echo $fn

script -f $ASIC_SRC/ip/cosim/tclsh/$fn -c "tclsh l1_test.tcl $SN $SLOT $MODE $INT_LPBK $VMARG 0 $OFFLOAD $ESEC_EN $SIMPLIFY $HC $DDR 0"

