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
    #output2=$(grep "ERROR ::" $FN | grep "cap_puf_dppm_chk: Puf allowed")

    while IFS=';' read -ra out_list
    do
        for i in "${out_list[@]}"
        do
            echo $i
        done
    done <<< "${output1}"

    grep "ERROR ::" $FN | grep -e "cap_puf_dppm_chk:"
fi

if [[ $MODE == "L1_HBM" ]]
then
    output=$(grep -e "ERROR ::" -e "ERROR_CHANNEL_FAILURES_EXIST" -e "RROR_CTC_WRITE_READ_COMPARE_FAILURE" -e "UNKNOWN_ERROR_CODE" $FN)

    while IFS=';' read -ra out_list
    do
        for i in "${out_list[@]}"
        do
            echo $i
        done
    done <<< "${output}"
fi

if [[ $MODE == "SNAKE" ]]
then
    grep -e "ERROR ::" $FN | grep -v "cap0.ms.em.int_groups.intreg: axi_interrupt" | grep -v "Unexpected int set: cap0.ms.em" | grep -v "interrupt-non-zero for reg:MS_M_AM_STS" | grep -v "interrupt-non-zero for reg:AR_M_AM_STS" | grep -v "PRP2() error_count non-zero" | grep -v "stall_timeout_error"
fi

if [[ $MODE == "AVS" ]]
then
    #grep -a -A100 -e "tclsh8.6 set_avs.tcl" $FN | grep ""FAILED: could not set gval 0x6a000000" | sort -t: -u -k1,1
    grep -a -A300 -e "tclsh8.6 set_avs.tcl" $FN | grep "FAILED: could not set gval 0x6a000000" | sort -t: -u -k1,1
fi

