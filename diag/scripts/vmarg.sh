# !/bin/bash

set_vmarg()
{
    echo $CARD_TYPE
    if [[ $CARD_TYPE == "ORTANO" ]]
    then
        for dev in ELB0_CORE ELB0_ARM VDD_DDR VDDQ_DDR
        do
            /data/nic_util/devmgr -dev=$dev -margin -pct=$1
        done
    else
        for dev in CAP0_ARM CAP0_CORE_DVDD CAP0_HBM CAP0_CORE_AVDD
        do
            /data/nic_util/devmgr -dev=$dev -margin -pct=$1
        done
    fi
}

if [ "$1" == "normal" ]
then
    percent=0
    set_vmarg $percent
else
    if [ "$1"  == "low" ]
    then
        percent1=-1
        percent2=-2
        percent3=-3
        percent4=-4
        percent5=-5
	for percent in $percent3 $percent4 $percent5
	do
            set_vmarg $percent
	done
    elif [ "$1" == "high" ]
    then
        percent1=1
        percent2=2
        percent3=3
        percent4=4
        percent5=5
	for percent in $percent1 $percent2 $percent3 $percent4 $percent5
        do
            echo "=== Vmarg is at $percent% ==="
            set_vmarg $percent
        done
    else
        echo "Invalid parameter"
    fi
fi

