#!/bin/bash

# setup libary path
if [[ -f "/nic/tools/setup_env_hw.sh" ]]; then
. /nic/tools/setup_env_hw.sh
fi

ret=0

if [[ -z "${dbgtool}" ]]; then
    dbgtool="eth_dbgtool"
    which eth_dbgtool 2> /dev/null
    if [[ $? -ne 0 ]]; then
        echo "Test binary not found in path" | tee -a $logfile
        exit $ret
    fi
else
    if [[ ! -f $dbgtool ]]; then
        echo "Test binary not found" | tee -a $logfile
        exit $ret
    fi
fi

INTERRUPTS=(
    "mc.mc[0].mcc0.int_mcc_controller"
    "mc.mc[0].mcc0.int_mcc_ecc_dataout_corrected_0"
    "mc.mc[0].mcc0.int_mcc_ecc_dataout_corrected_1"
    "mc.mc[0].mcc0.int_mcc_ecc_dataout_uncorrected_0"
    "mc.mc[0].mcc0.int_mcc_ecc_dataout_uncorrected_1"
    "mc.mc[0].mcc1.int_mcc_controller"
    "mc.mc[0].mcc1.int_mcc_ecc_dataout_corrected_0"
    "mc.mc[0].mcc1.int_mcc_ecc_dataout_corrected_1"
    "mc.mc[0].mcc1.int_mcc_ecc_dataout_uncorrected_0"
    "mc.mc[0].mcc1.int_mcc_ecc_dataout_uncorrected_1"
    "mc.mc[1].mcc0.int_mcc_controller"
    "mc.mc[1].mcc0.int_mcc_ecc_dataout_corrected_0"
    "mc.mc[1].mcc0.int_mcc_ecc_dataout_corrected_1"
    "mc.mc[1].mcc0.int_mcc_ecc_dataout_uncorrected_0"
    "mc.mc[1].mcc0.int_mcc_ecc_dataout_uncorrected_1"
    "mc.mc[1].mcc1.int_mcc_controller"
    "mc.mc[1].mcc1.int_mcc_ecc_dataout_corrected_0"
    "mc.mc[1].mcc1.int_mcc_ecc_dataout_corrected_1"
    "mc.mc[1].mcc1.int_mcc_ecc_dataout_uncorrected_0"
    "mc.mc[1].mcc1.int_mcc_ecc_dataout_uncorrected_1"
)

clitool="pdsctl"
which $clitool 2> /dev/null
if [[ $? -ne 0 ]]; then
    clitool="halctl"
    which $clitool 2> /dev/null
    if [[ $? -ne 0 ]]; then
        echo "Did not find pdsctl or halctl" | tee -a $logfile
        exit $ret
    fi
fi

check_interrupts() {
    $clitool show interrupts | grep -v INFO >> $logfile
    for intr in ${INTERRUPTS[@]}; do
        if grep -w -F $intr $logfile > /dev/null; then
            return 1
        fi
    done
    return 0
}

on_int() {
    ret=2
    exit $ret
}

on_exit() {
    if [[ $ret -eq 1 ]]; then
        echo "Test FAILED" | tee -a $logfile
    elif [[ $ret -eq 2 ]]; then
        echo "Test ABORTED" | tee -a $logfile
    else
        echo "Test PASSED" | tee -a $logfile
    fi
    echo "Please save the log file ddr_test.log & reboot the card."
}

trap on_exit EXIT
trap on_int INT

logfile="./ddr_test.log"
rm -f $logfile

# log all output to a file
echo "===> Before Test" | tee -a $logfile

num_hugepages=`cat /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages`
if [[ "$num_hugepages" -eq "0" ]]; then
    echo "Creating hugepages ..."
    echo "1024" > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
fi

fwname=`fwupdate -r`
loader_db="/nic/conf/gen/mpu_prog_info.json"
if [[ $fwname == "diagfw" && ! -f $loader_db ]]; then
    echo "Doing sysinit ..."
    sysinit.sh classic hw
fi

if [[ ! -f $loader_db ]]; then
    echo "Waiting upto 180 seconds for $loader_db to get generated!"
    wait=0
    while [[ $wait -lt 180 && ! -f $loader_db ]]
    do
        sleep 2
        wait=$(($wait + 2))
    done
fi

if [[ ! -f $loader_db ]]; then
    ret=1
    echo "Timeout waiting for $loader_db to get generated!" | tee -a $logfile
    exit $ret
fi

# clear old interrupts before starting test
$clitool clear interrupts | tee -a $logfile

# wait more than one interrupt polling period to catch any new/sticky interrupts
echo "Waiting 10 seconds for interrupt scan ..."
sleep 10
check_interrupts $logfile
if [[ $? -ne 0 ]]; then
    ret=1
    echo "There are error interrupts. Reboot the card & retry the test." | tee -a $logfile
    exit $ret
else
    echo "There are no error interrupts."
fi

echo "===> Starting Test" | tee -a $logfile
start=`date "+%s"`

# eth_dbgtool ddr_stress <lif> <wrcnt> <wrpad> <rdcnt> <rdpad> <freeze> <pattern> [<delay> [<axis> <bound> <step>]]
$dbgtool ddr_stress 65 45 0 45 ${rdpad_min:=0} 0 0 ${duration:=5} wrpad ${wrpad_max:=200} ${wrpad_step:=10}
test_results=$?

end=`date "+%s"`
runtime=$((end-start))
echo "Test Runtime: "$runtime"s" >> $logfile

echo "===> After Test" | tee -a $logfile
# check for any new error interrupts
check_interrupts $logfile
if [[ $? -ne 0 ]]; then
    ret=1
    echo "There are new error interrupts. Please check ddr_test.log." | tee -a $logfile
    exit $ret
fi

if [[ $test_results -ne 0 ]]; then
    ret=1
    exit $ret
fi

exit $ret
