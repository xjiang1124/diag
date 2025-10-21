#!/bin/bash

### Parses MBIST logfile and summarizes which memories failed

usage () {
    echo "==============================="
    echo "./mbist_err_parse.sh <logfile>"
    echo "==============================="
}

LOGFILE=$1
if [[ $LOGFILE == "" ]]; then
    usage
    exit 1
fi

sep_line=$(grep "Running diagnostics" -n $LOGFILE -a | cut -d':' -f1) # line number that separates test portion 1 vs 2
echo "Summarizing MBIST failures from $LOGFILE"
line_nums=""
for errline in $(grep "Failed TDO check" -an $LOGFILE | awk '{print $(NF-1)}'); do
    grep -an "Failed TDO check.*$errline" -A50 $LOGFILE | grep -a $errline -m2
done

