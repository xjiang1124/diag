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
    -cm|--cm)
    CM=${2^^}
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

echo "=== SN:        ${SN} ==="

mkdir -p "mfg_log/"
mkdir -p "test_logs/"

cwd=$(pwd)
cwd=$cwd"/mfg_log/"

fetch_output=$(python3 ./mfg.py -fetch -stage dl -cm $CM -logroot $cwd -sn_list $SN)

while IFS=';' read -ra out_list
do
    for i in "${out_list[@]}"
    do
        echo $i
        if [[ $i == *"=== Card Type"* ]]; then
            CARD_TYPE=$(echo $i | awk -F " " '{print $4}')
        fi
    done
done <<< "${fetch_output}"

python3 ./failure_anal.py -stage dl -card_type $CARD_TYPE -parse -pmode die_id_dl -sn $SN -cl -logroot $cwd
