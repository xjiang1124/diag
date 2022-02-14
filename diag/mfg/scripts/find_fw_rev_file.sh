#!/bin/bash

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"
case $key in
    #-------------
    -fn|--fn)
    FN=$2
    shift # past argument
    shift # past value
    ;;
    #-------------
    -verb|--verb)
    VERB=TRUE
    shift # past argument
    ;;
    #-------------
    -raw|--raw)
    RAW=TRUE
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

sn_list=()
echo "=== FN:        ${FN} ==="
while IFS= read -r line; do
    sn=$(echo $line|tr -d '\n')
    sn_list+=($sn)
done < $FN

for sn in "${sn_list[@]}"
do
    echo $sn
    ./find_fw_rev.sh -sn $sn
done
