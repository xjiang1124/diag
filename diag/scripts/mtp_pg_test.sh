#!/bin/bash

cpldutil -cpld-wr -addr=0x12 -data=0xff > /dev/null 2>&1
cpldutil -cpld-wr -addr=0x13 -data=0xff > /dev/null 2>&1
sleep 0.5
cpldutil -cpld-wr -addr=0x10 -data=0xff > /dev/null 2>&1
cpldutil -cpld-wr -addr=0x11 -data=0xff > /dev/null 2>&1
sleep 0.5
value0_3v3=$(cpldutil -cpld-rd -addr=0x20 | awk '/data/{sub(/.*data/, ""); print}')
value1_3v3=$(cpldutil -cpld-rd -addr=0x21 | awk '/data/{sub(/.*data/, ""); print}')
value0_12v=$(cpldutil -cpld-rd -addr=0x22 | awk '/data/{sub(/.*data/, ""); print}')
value1_12v=$(cpldutil -cpld-rd -addr=0x20 | awk '/data/{sub(/.*data/, ""); print}')
if [[ $value0_12v -ne 0 ]] && [[ $value1_12v -ne 0 ]];then
    echo "failed to turn off 12 v" $((value0_12v))  $((value1_12v))
    exit 1
fi
if [[ $value0_3v3 -ne 0 ]] && [[ $value1_3v3 -ne 0 ]];then
    echo "failed to turn off 3.3 v" $((value0_3v3))  $((value1_3v3))
    exit 1
fi

mask=0x0001
pwr=0xff
fail=0
for slot in {1..10}
do
    if [[ $slot -lt 9 ]];then
        pwr=$(($pwr & ((~$((0x1 << $(($slot-1))))))))
        cpldutil -cpld-wr -addr=0x12 -data=$pwr > /dev/null 2>&1
        sleep 0.5
        cpldutil -cpld-wr -addr=0x10 -data=$pwr > /dev/null 2>&1
    else
        pwr=$(($pwr & ((~$((0x1 << $(($slot-9))))))))
        cpldutil -cpld-wr -addr=0x13 -data=$pwr > /dev/null 2>&1
        sleep 0.5
        cpldutil -cpld-wr -addr=0x11 -data=$pwr > /dev/null 2>&1
    fi
    value0_3v3=$(cpldutil -cpld-rd -addr=0x20 | awk '/data/{sub(/.*data/, ""); print}')
    value1_3v3=$(cpldutil -cpld-rd -addr=0x21 | awk '/data/{sub(/.*data/, ""); print}')
    value=$(($(($value1_3v3 << 8)) | $value0_3v3))
    if [[ $(($((value)) & $mask)) -eq 0 ]];then
        echo "failed to run on 3.3v over " $slot $((value))
        fail=$(($fail+1))
    fi

    value0_12v=$(cpldutil -cpld-rd -addr=0x22 | awk '/data/{sub(/.*data/, ""); print}')
    value1_12v=$(cpldutil -cpld-rd -addr=0x23 | awk '/data/{sub(/.*data/, ""); print}')
    value=$(($(($value1_12v << 8)) | $value0_12v))
    if [[ $(($value & $mask)) -eq 0 ]];then
        echo "failed to run on 12v over " $slot $((value))
        fail=$(($fail+1))
    fi
    mask=$(( $mask << 1 ))
done

echo ""
if [[ $fail -eq 0 ]];then
    echo "MTP PASSED power good test"
else
    echo "MTP FAILED power good test for $fail incidents" 
fi
echo ""
exit 0
