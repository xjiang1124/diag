# !/bin/bash

if [ "$1"  == "low" ]
then
    percent=-5
elif [ "$1" == "high" ]
then
    percent=5
else
    percent=0
fi

for dev in CAP0_CORE_DVDD CAP0_ARM CAP0_3V3 CAP0_HBM CAP0_CORE_AVDD
do
    devmgr -dev=$dev -margin -pct=$percent
done

