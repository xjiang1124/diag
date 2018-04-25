#!/bin/bash

(IFS='
'
for x in `find /sys/devices/ -name temp`
do 
    zone=`echo $x | awk -F "/" '{print $6}'`
    zone=`echo $zone | awk -F "_" '{print $2}'`
    cpu_temp=$(< $x)
    cpu_temp=$(($cpu_temp/1000))
    echo $zone $cpu_temp°C
done)

