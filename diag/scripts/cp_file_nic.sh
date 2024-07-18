#!/bin/bash

fn=$1
slot_list=$2
path=$3

echo "fn: $fn; slot_list: $slot_list; path: $path"

delimiter=","

IFS="$delimiter" read -ra array <<< "$slot_list"

# Printing each element of the array
for element in "${array[@]}"; do
    echo "scp_s.sh $fn $element $path"
    scp_s.sh $fn $element $path
done
