#!/bin/bash

str=$(mmc extcsd read /dev/mmcblk0 | grep -A 1 "MAX_ENH_SIZE_MULT")
i=0
for substr in $str
do
    if [[ $i == "1" ]]; then
        size=$((substr))
        break
    elif [[ $substr == "i.e." ]]; then
        i=1
    fi
done

set -x
mmc enh_area set -y 0 $size /dev/mmcblk0
#mmc enh_area set -n 0 $size /dev/mmcblk0
