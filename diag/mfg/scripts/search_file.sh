#!/bin/bash

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"
case $key in
    #-------------
    -mode|--mode)
    MODE=${2^^}
    shift # past argument
    shift # past value
    ;;
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

if [[ $VERB == TRUE ]]
then
    echo "MODE:        ${MODE}"
    echo "FN:          ${FN}"
fi

if [[ $MODE == "L1" ]]
then
    grep "ERROR ::" $FN
fi

if [[ $MODE == "L1_ESEC" ]]
then
    output1=$(grep -A10 "ERROR :: cap_eval_pac_score_all" $FN)
    output2=$(grep "ERROR ::" $FN | grep "cap_puf_dppm_chk: Puf allowed")

    while IFS=';' read -ra out_list
    do
        for i in "${out_list[@]}"
        do
            echo $i
        done
    done <<< "${output1}"

    grep "ERROR ::" $FN | grep "cap_puf_dppm_chk: Puf allowed"
fi
