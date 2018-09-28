# !/bin/bash

DIAG_ROOT="/home/diag/diag/"
declare -a arr=( 
    "/home/diag/diag/log/*txt"  
    "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/*log" 
    )

for i in "${arr[@]}"
do
    #echo "$i"
    cmd="rm "$i
    echo $cmd
    eval "$cmd"
done



