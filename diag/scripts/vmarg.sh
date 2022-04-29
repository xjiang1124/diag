#!/bin/bash
declare -A ortano_high=([elb0_arm]=2 [elb0_core]=2 [vdd_ddr]=2 [vddq_ddr]=2)
declare -A ortano_low=([elb0_arm]=-2 [elb0_core]=-2 [vdd_ddr]=-2 [vddq_ddr]=-2)
declare -A ortano_normal=([elb0_arm]=0 [elb0_core]=0 [vdd_ddr]=0 [vddq_ddr]=0)
ortano_vmarg=(ortano_normal ortano_low ortano_high)
declare -A ortanoA_high=([elb0_arm]=2 [elb0_core]=2)
declare -A ortanoA_low=([elb0_arm]=-2 [elb0_core]=-2)
declare -A ortanoA_normal=([elb0_arm]=0 [elb0_core]=0)
ortanoA_vmarg=(ortanoA_normal ortanoA_low ortanoA_high)

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
        if [[ "$1" == "high" ]]
        then
            index=2
        elif [[ "$1" == "low" ]]
        then
            index=1
        elif [[ "$1" == "normal" ]]
        then
            index=0
        fi
        if [[ $CARD_TYPE == "ORTANO2A" ]]
        then
            tmp=(${ortanoA_vmarg[$index]})
        else
            tmp=(${ortano_vmarg[$index]})
        fi
        declare -n tgt_vmarg="$tmp"
        for i in "${!tgt_vmarg[@]}"
        do
            /data/nic_util/devmgr -dev=$i -margin -pct=${tgt_vmarg[$i]}
        done
    elif [[ $CARD_TYPE == "LACONA32"        || \
            $CARD_TYPE == "LACONA32DELL"    || \
            $CARD_TYPE == "POMONTE"         || \
            $CARD_TYPE == "POMONTEDELL"     ]]
    then
        if [[ "$1" -eq "normal" ]]
        then
            echo "Do nothing"
            return
        elif [[ "$1" == "low" ]]
        then
            #/data/nic_util/devmgr -dev=ELB0_ARM -margin -pct=$1
            /data/nic_util/devmgr -dev=VDDQ_DDR -margin -pct=-2
            set_vmarg_lacona arm -2 
            set_vmarg_lacona core -2
            return
        elif [[ "$1" == "high" ]]
        then
            /data/nic_util/devmgr -dev=VDDQ_DDR -margin -pct=2
            set_vmarg_lacona arm 2 
            set_vmarg_lacona core 2
        fi
    else
        if [[ "$1" -eq "normal" ]]
        then
            vmarg=0
        elif [[ "$1" -eq "low" ]]
        then
            vmarg=-5
        elif [[ "$1" -eq "high" ]]
        then
            vmarg=5
        fi
        for dev in CAP0_ARM CAP0_CORE_DVDD CAP0_HBM CAP0_CORE_AVDD
        do
            /data/nic_util/devmgr -dev=$dev -margin -pct=$vmarg
        done
    fi
    return
}

echo "=== Setting Vmarg to $1 ==="
set_vmarg $1
echo "=== Vmarg is at $1 ==="

