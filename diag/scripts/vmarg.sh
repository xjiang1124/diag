# !/bin/bash

if [ "$1" == "normal" ]
then
    percent=0
    for dev in CAP0_CORE_DVDD CAP0_ARM CAP0_HBM CAP0_CORE_AVDD
    do
        devmgr -dev=$dev -margin -pct=$percent
    done
else
    if [ "$1"  == "low" ]
    then
        percent3=-3
        percent4=-4
        percent5=-5
	for percent in $percent3 $percent4 $percent5
	do
	    for dev in CAP0_CORE_DVDD CAP0_ARM CAP0_HBM CAP0_CORE_AVDD
            do
                devmgr -dev=$dev -margin -pct=$percent
            done
	done
    elif [ "$1" == "high" ]
    then
        percent3=3
        percent4=4
        percent5=5
	for percent in $percent3 $percent4 $percent5
        do
            for dev in CAP0_CORE_DVDD CAP0_ARM CAP0_HBM CAP0_CORE_AVDD
            do
                devmgr -dev=$dev -margin -pct=$percent
            done
        done
    else
        echo "Invalid parameter"
    fi
fi

