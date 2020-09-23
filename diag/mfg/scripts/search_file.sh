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
    -raw|--raw)
    RAW=TRUE
    shift # past argument
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

if [[ $FN == "" ]]
then
    echo "EORROR:: filename is empty"
    exit 0
fi

if [[ $VERB == TRUE ]]
then
    echo "MODE:        ${MODE}"
    echo "FN:          ${FN}"

elif [[ $MODE == "L1" ]]
then
    grep "ERROR ::" $FN

elif [[ $MODE == "L1_ESEC" ]]
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

    grep "ERROR ::" $FN | grep -e "cap_puf_dppm_chk:" -e "cap_esec_chk_boot_step :: expected_val:0x20 got_val" | sort -t: -u -k1,1

elif [[ $MODE == "L1_HBM" ]]
then
    output=$(grep -e "ERROR ::" -e "ERROR_CHANNEL_FAILURES_EXIST" -e "RROR_CTC_WRITE_READ_COMPARE_FAILURE" -e "UNKNOWN_ERROR_CODE" $FN)

    while IFS=';' read -ra out_list
    do
        for i in "${out_list[@]}"
        do
            echo $i
        done
    done <<< "${output}"

elif [[ $MODE == "SNAKE" ]]
then
    grep -e "ERROR ::" $FN | grep -v "cap0.ms.em.int_groups.intreg: axi_interrupt" | grep -v "Unexpected int set: cap0.ms.em" | grep -v "interrupt-non-zero for reg:MS_M_AM_STS" | grep -v "interrupt-non-zero for reg:AR_M_AM_STS" | grep -v "PRP2() error_count non-zero" | grep -v "stall_timeout_error"

elif [[ $MODE == "AVS" ]]
then
    #grep -a -A100 -e "tclsh8.6 set_avs.tcl" $FN | grep ""FAILED: could not set gval 0x6a000000" | sort -t: -u -k1,1
    grep -a -A300 -e "tclsh8.6 set_avs.tcl" $FN | grep "FAILED: could not set gval 0x6a000000" | sort -t: -u -k1,1

elif [[ $MODE == "ETH_PRBS" ]]
then
    grep "ERROR" $FN

elif [[ $MODE == "FW_REV" ]]
then
    echo "========================================"

    if [[ $RAW == TRUE ]]
    then
        grep -a  "cpld -prog" $FN
        grep -a -A130 "fwupdate -l" $FN
        exit 0
    fi

    echo "boot0"
    grep -a -A130 "fwupdate -l" $FN | grep -A12 "boot0" | grep "software_version"
    grep -a -A130 "fwupdate -l" $FN | grep -A12 "boot0" | grep "software_pipeline"

    echo "========================================"
    echo "mainfwa"
    echo "system_image"
    grep -a -A130 "fwupdate -l" $FN | grep -A32 "mainfwa" | grep -A10 "system_image" | grep -e "software_version" -e "software_pipeline"
    echo "kernel_fit"
    grep -a -A130 "fwupdate -l" $FN | grep -A32 "mainfwa" | grep -A10 "kernel_fit" | grep -e "software_version" -e "software_pipeline"
    echo "uboot"
    grep -a -A130 "fwupdate -l" $FN | grep -A32 "mainfwa" | grep -A10 "uboot" | grep -e "software_version" -e "software_pipeline"

    echo "========================================"
    echo "mainfwb"
    echo "system_image"
    grep -a -A130 "fwupdate -l" $FN | grep -A32 "mainfwb" | grep -A10 "system_image" | grep -e "software_version" -e "software_pipeline"
    echo "kernel_fit"
    grep -a -A130 "fwupdate -l" $FN | grep -A32 "mainfwb" | grep -A10 "kernel_fit" | grep -e "software_version" -e "software_pipeline"
    echo "uboot"
    grep -a -A130 "fwupdate -l" $FN | grep -A32 "mainfwb" | grep -A10 "uboot" | grep -e "software_version" -e "software_pipeline"

    echo "========================================"
    echo "goldfw"
    echo "kernel_fit"
    grep -a -A130 "fwupdate -l" $FN | grep -A24 "goldfw" | grep -A10 "kernel_fit" | grep "software_version"
    echo "uboot"
    grep -a -A130 "fwupdate -l" $FN | grep -A24 "goldfw" | grep -A10 "uboot" | grep "software_version"

    echo "========================================"
    echo "cpld"
    grep -a -A130 "fwupdate -l" $FN | grep -A12 "cpld" | grep "version"

    echo "========================================"

elif [[ $MODE == "PCIE_LINK" ]]
then
    grep -a -A5 "failed" $FN

elif [[ $MODE == "PCIE_LINK" ]]
then
    #grep -a -A100 -e "tclsh8.6 set_avs.tcl" $FN | grep ""FAILED: could not set gval 0x6a000000" | sort -t: -u -k1,1
    grep -a -A300 -e "tclsh8.6 set_avs.tcl" $FN | grep "FAILED: could not set gval 0x6a000000" | sort -t: -u -k1,1


else
    echo "Unsupported error code SEARCH!" $MODE
fi


