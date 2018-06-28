#!/bin/bash
for i in `seq 1 10`;
do
    echo "Testing UUT_$i"
    turn_on_uut.sh $i 0
    pcieswutil -uut=UUT_$i -dev=PEX -mtest -dura=30
done



