# !/bin/bash

# Default values
MODE="nod"
OFFLOAD=0
ESEC_EN=0
INT_LPBK=0

iter=1
slot=""

usage () {
    echo "=========================="
    echo "./${0##*/} -slot <> -mode <> -lpbk <> -offload <> -esec <> -ite <>"
    echo "slot:    Slot number"
    echo "mode:    Mode hod/hod_1100/nod/nod_525"
    echo "lpbk:    0: external loopback; 1 internal loopback; default: 0"
    echo "offload: 0: offload diabled; 1: offload PCIe/ETH PRBS, TCAM, efuse tests to ARM; default: 1"
    echo "esec:    0: esecure test disabled; 1: esecure test enabled; default: 1"
    echo "ite:     Number of iterations"
    echo "=========================="
}

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"
case $key in
    #-------------
    -slot|--slot)
    slot=${2^^}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -mode|--mode)
    MODE=${2,,}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -lpbk|--int_lpbk)
    INT_LPBK="${2}"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -offload|--offload)
    OFFLOAD=${2}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -esec|--esec_en)
    ESEC_EN=${2}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -ite)
    iter=${2}
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

echo "slot: $slot"

if [[ $slot -lt 1 ]] || [[ $slot -gt 10 ]]
then
    echo "Invalid slot number: $slot    Expected [1,10]"
    usage
    exit
fi

echo "slot: $slot; MODE: $MODE; INT_LPBK: $INT_LPBK; OFFLOAD: $OFFLOAD; ESEC_EN: $ESEC_EN; ite: $iter"


for (( i=0; $i<$iter; i++ ))
do
    echo "==== Iteration #$i (slot $slot) ===="

    #echo ""
    #echo "#### Programming QSPI Flash #0 (iteration $i) ... ####"
    #date
    #cd /home/diag/tmp

    #rm fileRandom256MB.img
    #dd if=/dev/urandom of=fileRandom256MB.img bs=256M count=1
    #./fpgautil flash $(($slot-1)) 0 program allflash fileRandom256MB.img

    #echo "#### Programming QSPI Flash #1 (iteration #i) ... ####"
    #rm fileRandom256MB.img
    #dd if=/dev/urandom of=fileRandom256MB.img bs=256M count=1
    #./fpgautil flash $(($slot-1)) 1 program allflash fileRandom256MB.img

    #echo "#### END of Programming QSPI Flash (iteration $i) ####"
    #exit 0

    echo ""
    echo "#### pwr cycle slot $slot (iteration $i) ... ####"
    date
    echo "  turn off slot $slot..."
    turn_on_slot.sh off $slot
    echo "  wait 10 seconds..."
    sleep 10
    echo "  turn on slot $slot..."
    turn_on_slot.sh on $slot 0 0
    echo "  wait 10 seconds..."
    sleep 10

    reset_code=$(i2cget -y $(($slot+2)) 0x4a 0x30)
    sleep 1
    fault_code=$(i2cget -y $(($slot+2)) 0x4a 0x32)
    sleep 1
    dpu_stat0=$(i2cget -y $(($slot+2)) 0x4a 0x14)

    echo "  CPLD reset_code reg (0x30): $reset_code"
    if [[ $reset_code != "0x00" ]]
    then
        echo "    ERROR: CPLD reset_code is not zero! Stop L1_Tests."
        exit 1
    fi

    echo "  CPLD fault_code reg (0x32): $fault_code"
    if [[ $fault_code != "0x00" ]]
    then
        echo "    Warning: CPLD fault_code is not zero!"
    fi

    echo "  CPLD DPU_STAT0 reg (0x14): $dpu_stat0"
    if [[ $dpu_stat0 != "0x07" ]]
    then
        echo "    ERROR: CPLD DPU_STAT0 is not 0x07! Stop L1_Tests."
        exit 1
    fi
    echo "#### END of pwr cycle slot $slot (iteration $i) ####"

    echo ""
    echo "#### RUN L1 TESTS (iteration $i) ... ####"
    date

    verStr=$(version)
    IFS=$'\n' read -rd '' -a verArray <<<"$verStr"
    echo ""
    echo "version:"
    for (( j=0; $j<3; j++ ))
    do
        echo ${verArray[$j]}
    done

    snMsg=$(eeutil -uut=UUT_$slot -disp -field=SN)
    echo ""
    echo $snMsg

    cd /home/diag/diag/scripts/asic
    run_l1_cmd="./run_l1.sh -sn \"slot$slot\" -slot $slot -m $MODE -o $OFFLOAD -e $ESEC_EN -i $INT_LPBK -ite $iter"
    echo ""
    echo $run_l1_cmd
    eval $run_l1_cmd

    echo "#### END of L1 TESTS (iteration $i) ####"
    echo ""
done
date
echo "== THE END of The World!!! (slot $slot) =="

