#!/bin/bash

set_vmarg_lacona()
{
    if [[ $1 == "arm" ]]
    then
        vrail="ELB0_ARM"
    else
        vrail="ELB0_CORE"
    fi

    vout=$(/data/nic_util/devmgr -status | grep $vrail | sed "s/[ +]\]//g" | awk -F " " '{print $6}')
    voutmv=$(awk "BEGIN {print $vout*1000*(100+$2)/100}")
    voutmv=$(printf '%.0f' $voutmv)

    echo "Calculated vout: $voutmv"
    if [[ "$voutmv" -lt 700 ]]
    then
        voutmv=700
        echo "Setting to minimal vout: $voutmv"
    fi
    /data/nic_util/devmgr -dev=$vrail -margin -mgmode=mv -vout=$voutmv
}

set_vmarg()
{
    echo $CARD_TYPE
    if [[ $CARD_TYPE == "ORTANO" || $CARD_TYPE == "ORTANO2" || $CARD_TYPE == "ORTANO2A" ]]
    then
        if [[ "$1" -lt 3 && "$1" -ge -2 ]] 
        then
            /data/nic_util/devmgr -dev=ELB0_ARM -margin -pct=$1
            /data/nic_util/devmgr -dev=ELB0_CORE -margin -pct=$1
            if [[ $CARD_TYPE == "ORTANO" || $CARD_TYPE == "ORTANO2" ]]
            then
                /data/nic_util/devmgr -dev=VDDQ_DDR -margin -pct=$1
                /data/nic_util/devmgr -dev=VDD_DDR -margin -pct=$1
            fi
            return
        fi
        echo "Skipping $1%"
    elif [[ $CARD_TYPE == "LACONA32"        || \
            $CARD_TYPE == "LACONA32DELL"    || \
            $CARD_TYPE == "POMONTE"         || \
            $CARD_TYPE == "POMONTEDELL"     ]]
    then
        if [[ "$1" -eq 0 ]]
        then
            echo "Do nothing"
            return
        elif [[ "$1" -lt 3 && "$1" -ge -2 ]] 
        then
            #/data/nic_util/devmgr -dev=ELB0_ARM -margin -pct=$1
            /data/nic_util/devmgr -dev=VDDQ_DDR -margin -pct=$1
            set_vmarg_lacona arm $1
            set_vmarg_lacona core $1
            return
        fi
        echo "Skipping $1%"
    else
        for dev in CAP0_ARM CAP0_CORE_DVDD CAP0_HBM CAP0_CORE_AVDD
        do
            /data/nic_util/devmgr -dev=$dev -margin -pct=$1
        done
    fi
    return
}

if [ "$1" == "normal" ]
then
    percent=0
    set_vmarg $percent
elif [ "$1"  == "low" ]
then
    declare -a pct_list=(-1 -2 -3 -4 -5)
    if [[ $ASIC_TYPE == "ELBA" ]]
    then
        declare -a pct_list=(-1 -2)
    fi
elif [ "$1" == "high" ]
then
    declare -a pct_list=(1 2 3 4 5)
    if [[ $ASIC_TYPE == "ELBA" ]]
    then
        declare -a pct_list=(1 2)
    fi
else
    echo "Invalid parameter"
    exit 0
fi

for percent in ${pct_list[@]}
do
    echo "=== Setting Vmarg to $percent% ==="
    set_vmarg $percent
    echo "=== Vmarg is at $percent% ==="
done

