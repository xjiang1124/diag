#!/bin/bash
for i in `seq 1 $1`;
do
    echo "Iteration #$1"
    pcieswutil -uut=UUT_1 -dev=PEX -mtest -dura=30
done
