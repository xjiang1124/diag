#!/bin/bash
for i in `seq 1 10`;
do
    echo "Testing UUT_$i"
    turn_on_uut.sh $i 0
    mtptest -pcs -index=$((i-1))
done
