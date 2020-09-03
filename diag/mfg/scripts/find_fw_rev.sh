#!/bin/bash

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
    -card_type|--card_type)
    CARD_TYPE=${2^^}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -verb|--verb)
    VERB=TRUE
    shift # past argument
    ;;

    #-------------
    --default)
    DEFAULT=YES
    shift # past argument
    ;;
    #-------------
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

echo "=== CARD_TYPE: ${CARD_TYPE} ==="
echo "=== SN:        ${SN} ==="

mkdir -p "mfg_log/"
mkdir -p "test_logs/"

cwd=$(pwd)
cwd=$cwd"/mfg_log/"

python3 ./mfg.py -fetch -card_type $CARD_TYPE -stage swi -cm pen -logroot $cwd -sn_list $SN
python3 ./failure_anal.py -stage swi -card_type $CARD_TYPE -parse -pmode fw_rev -sn $SN -cl -logroot $cwd
