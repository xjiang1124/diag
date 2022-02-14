#!/bin/bash
for i in `seq 1 $1`;
do
    echo "Iteration #$i"
    mtptest -pcs -index=4
done
