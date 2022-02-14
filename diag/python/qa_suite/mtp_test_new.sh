#!/bin/bash
# Use this command to turn on all UUT 12v
# Need this to show PSU DC ok is good

declare -i test_failed=1
declare -i psu_result=0
time=$(date +"%I%M%S")
day=$(date +"%m%d")
tempfile="./temp_test.log"
logfile=$HOME/mtp_test$day$time.log

function FAIL ()
{
   echo "==============================================="
   echo " Test FAILED. Check log file for details       "
   echo "==============================================="
   cat $tempfile >> $logfile
}

$HOME/diag/scripts/turn_on_slot.sh off all
$HOME/diag/scripts/turn_on_slot.sh on all
cd $HOME
#./start_diag.sh
#source .bash_profile

version > $logfile
devmgr -dev=fan -speed -pct=40 >> $logfile

#turn_on_uut.sh 1 0

sensors >> logfile
i2cdetect -y -r 0 >> $logfile

mtptest -fan  > $tempfile
while IFS= read -r line
do
    if [[ $line =~ .*"TEST PASSED".* ]] 
    then
        echo " FAN test passed"
        test_failed=0
    fi
done < $tempfile

if [[ $test_failed -eq 1 ]]
    then
    echo " FAN test failed!!!" 
    FAIL      
    exit 1
fi

cat $tempfile >> $logfile

test_failed=1
mtptest -fanspd > $tempfile
while IFS= read -r line
do
    if [[ $line =~ .*"TEST PASSED".* ]] 
    then
        echo " FAN speed test passed"
        test_failed=0
    fi
done < $tempfile

if [[ $test_failed -eq 1 ]]
    then
    echo " FAN speed test failed!!!" 
    FAIL      
    cat $tempfile >> $logfile
    exit 1
fi
cat $tempfile >> $logfile

devmgr -dev=fan -speed -pct=40 >> $logfile

test_failed=1
mtptest -fantmp > $tempfile
while IFS= read -r line
do
    if [[ $line =~ .*"TEST PASSED".* ]] 
    then
        echo " FAN temperature sensor test passed"
        test_failed=0
    fi
done < $tempfile

if [[ $test_failed -eq 1 ]]
    then
    echo " FAN temperature sensor test failed!!!" 
    FAIL      
    exit 1
fi
cat $tempfile >> $logfile

: <<'END'
mtptest -psu > $tempfile
while IFS= read -r line
do
    if [[ $line =~ .*"PSU_1 TEST PASSED".* ]] 
    then
        echo " PSU_1 sensor test passed"
        if [[ $psu_result -eq 2 ]] 
        then 
            psu_result=3
        else
            psu_result=1
        fi
    fi
    if [[ $line =~ .*"PSU_2 TEST PASSED".* ]] 
    then
        echo " PSU_1 sensor test passed"
        if [[ $psu_result -eq 1 ]] 
        then 
            psu_result=3
        else
            psu_result=2
        fi
    fi
done < $tempfile

if [[ $psu_result -ne 3 ]]
then
    if [[ $psu_result -eq 1 ]]
    then
        echo " PSU_2 test failed!!!" 
    elif [[ $psu_result -eq 2 ]]
    then
        echo " PSU_1 test failed!!!" 
    else
        echo " BOTH PSU test failed!!!" 
    fi
    FAIL      
    exit 1
fi
cat $tempfile >> $logfile
END

test_failed=1
mtptest -vrm > $tempfile
while IFS= read -r line
do
    if [[ $line =~ .*"TEST PASSED".* ]] 
    then
        echo " VRM test passed"
        test_failed=0
    fi
done < $tempfile

if [[ $test_failed -eq 1 ]]
    then
    echo " VRM test failed!!!" 
    FAIL      
    exit 1
fi
cat $tempfile >> $logfile

declare -i mvl_result=0
mtptest -mvl > $tempfile
while IFS= read -r line
do
    if [[ $line =~ .*"0 TEST PASSED".* ]] 
    then
        echo " Marvell switch 0 test passed"
        if [[ mvl_result -eq 2 ]] 
        then 
            mvl_result=3
        else
            mvl_result=1
        fi
    fi
    if [[ $line =~ .*"1 TEST PASSED".* ]] 
    then
        echo " Marvell switch 1 test passed"
        if [[ mvl_result -eq 1 ]] 
        then 
            mvl_result=3
        else
            mvl_result=2
        fi
    fi
done < $tempfile

if [[ $mvl_result -ne 3 ]]
    then
        if [[ mvl_result -eq 1 ]]
        then
            echo " Marvell switch 1 test failed!!!" 
        elif [[ mvl_result -eq 2 ]]
        then
            echo " Marvell switch 0 test failed!!!" 
        else
            echo " Both Marvell switch test failed!!!" 
        fi
    FAIL      
    exit 1
fi
cat $tempfile >> $logfile

mtptest -wdt > $tempfile
while IFS= read -r line
do
    if [[ $line =~ .*"TEST PASSED".* ]] 
    then
        echo " Watchdog test passed"
        test_failed=0
    fi
done < $tempfile

if [[ $test_failed -eq 1 ]]
    then
    echo " Watchdo test failed!!!" 
    FAIL      
    exit 1
fi
cat $tempfile >> $logfile

declare -i count=0
mtptest -present > $tempfile
while IFS= read -r line
do
    if [[ $line =~ .*"Fan 0 is present".* ]] 
    then
        echo " Fan 0 is present"
        count=$[count+1]
    fi
    if [[ $line =~ .*"Fan 1 is present".* ]] 
    then
        echo " Fan 1 is present"
        count=$[count+1]
    fi
    if [[ $line =~ .*"Fan 2 is present".* ]] 
    then
        echo " Fan 2 is present"
        count=$[count+1]
    fi
    if [[ $line =~ .*"PSU 0 is present".* ]] 
    then
        echo " PSU 0 is present"
        count=$[count+1]
    fi
    if [[ $line =~ .*"PSU 1 is present".* ]] 
    then
        echo " PSU 1 is present"
        count=$[count+1]
    fi
done < $tempfile
if [[ $count -ne 5 ]] 
then 
   echo " Not all devices are present!!!"
   FAIL
   exit 1
fi
echo " All devices are present"
cat $tempfile >> $logfile

count=0
inventory -present > $tempfile
while IFS= read -r line
do
    if [[ $line =~ .*"NAPLES100".* ]] 
    then
        count=$[count+1]
    fi
done < $tempfile
if [[ $count -eq 9 ]]
then 
    echo "Not ALL ($count) NIC cards present!!!"
    FAIL
    exit 1
fi
echo " All NIC cards are present"
cat $tempfile >> $logfile

python wrapper.py

sensors >> $logfile
echo "===================================================="
echo " ALL Tests PASSED. Check log file for details       "
echo "===================================================="

