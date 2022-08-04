#!/bin/bash

value0=$(cpldutil -cpld-rd -addr=0x20 | awk '/data/{sub(/.*data/, ""); print}')
value1=$(cpldutil -cpld-rd -addr=0x21 | awk '/data/{sub(/.*data/, ""); print}')
value_3v3=$(($(($value1 << 8)) | $value0))
value0=$(cpldutil -cpld-rd -addr=0x22 | awk '/data/{sub(/.*data/, ""); print}')
value1=$(cpldutil -cpld-rd -addr=0x20 | awk '/data/{sub(/.*data/, ""); print}')
value_12v=$(($(($value1 << 8)) | $value0))

mask=0x0001
echo "3.3v status slot -- 1  2  3  4  5  6  7  8  9  10"
status="" 
for slot in {1..10}
do
    if [[ $(($value_3v3 & $mask)) -eq 0 ]];then
        status=$status"xx "
    else
        status=$status"ok "
    fi
    mask=$(( $mask << 1 ))
done
echo "                    "$status
echo ""
echo "12v status slot -- 1  2  3  4  5  6  7  8  9  10"
status="" 
mask=0x0001
for slot in {1..10}
do
    if [[ $(($value_12v & $mask)) -eq 0 ]];then
        status=$status"xx "
    else
        status=$status"ok "
    fi
    mask=$(( $mask << 1 ))
done
echo "                   "$status
echo ""

exit 0
