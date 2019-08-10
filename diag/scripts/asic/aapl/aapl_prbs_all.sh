#!/bin/bash

if [ $# -ge 1 ]
then
    INF=$1
    INF=${INF^^}
else
    INF="PCIE"
fi

if [ $# -ge 2 ]
then
    STAGE=$2
    STAGE=${STAGE^^}
else
    STAGE="PRBS"
fi

if [ $# -ge 3 ]
then
    POLY=$3
    POLY=${POLY^^}
else
    POLY="PRBS31"
fi

if [ $# -ge 4 ]
then
    DURATION=$4
else
    DURATION=60
fi

echo "INF: $INF; STAGE: $STAGE; POLY: $POLY; DURA: $DURATION"

echo $CARD_TYPE
card_type=$CARD_TYPE

SERVER_IP=localhost
PORT=9000

function get_card_config() {
    # Naples100
    declare -a sbus_list_naples100_eth=("34" "35" "36" "37" "38" "39" "40" "41")
    declare -a atten_list_naples100_eth=("0" "0" "0" "0" "0" "0" "0" "0")
    declare -a pre_list_naples100_eth=("2" "2" "2" "2" "2" "2" "2" "2")
    declare -a post_list_naples100_eth=("12" "12" "12" "12" "12" "12" "12" "12")

    declare -a sbus_list_naples100_pcie=("2" "4" "6" "8" "10" "12" "14" "16" "18" "20" "22" "24" "26" "28" "30" "32")

    if [ $card_type = "NAPLES100" ]
    then
        if [ $INF = "ETH" ]
        then
            sbus_list=("${sbus_list_naples100_eth[@]}") 
            atten_list=("${atten_list_naples100_eth[@]}") 
            pre_list=("${pre_list_naples100_eth[@]}") 
            post_list=("${post_list_naples100_eth[@]}") 
        elif [ $INF = "PCIE" ]
        then
            sbus_list=("${sbus_list_naples100_pcie[@]}") 
        else
            echo "xxx"
        fi
    fi

    if [ $INF = "ETH" ]
    then
        rom_file="/data/nic_arm/aapl/serdes.0x1087_244D.rom"
        div="165"
        width="40"
    elif [ $INF = "PCIE" ]
    then
        rom_file="/data/nic_arm/aapl/serdes.0x1094_2347.rom"
        div="160"
        width="40"
    else
        echo "Wrong INF $INF"
        exit 1
    fi
}

function do_reset() {
    for sbus in ${sbus_list[@]}
    do
        echo "Resetting sbus $sbus; $SERVER_IP:$PORT"
        aapl serdes-init -server $SERVER_IP -port $PORT -addr $sbus -reset 
    done
    echo "AAPL ETH SERDES RESET DONE"
}

function do_init() {
    for sbus in ${sbus_list[@]}
    do
        echo "Initializing sbus $sbus; $SERVER_IP:$PORT"
        aapl  serdes-init -server $SERVER_IP -port $PORT -addr $sbus -div $div -width $width -elb -disable-signal-ok -firm $rom_file
    done
    echo "AAPL ETH SERDES INIT DONE"
}

function do_prbs() {
    for idx in "${!sbus_list[@]}"
    do
        sbus=${sbus_list[$idx]}
        atten=${atten_list[$idx]}
        pre=${pre_list[$idx]}
        post=${post_list[$idx]}

        echo "=== $SERVER_IP:$PORT sbus $sbus atten $atten pre $pre post $post ==="
        if [ $INF = "ETH" ]
        then
            aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -atten 0 -pre $pre -post $post
        fi

        aapl dfe -server $SERVER_IP -port $PORT -addr $sbus -pcal-tune
        aapl dfe -server $SERVER_IP -port $PORT -addr $sbus -start-adaptive
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -display
    done
    
    for sbus in ${sbus_list[@]}
    do
        echo "=== $SERVER_IP:$PORT $sbus ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -tx-data-sel $POLY -rx-mode $POLY
    done
    
    
    #for sbus in $sbus_list
    for sbus in ${sbus_list[@]}
    do
        echo "=== $SERVER_IP:$PORT $sbus ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -error-reset
    done
    
    echo "Sleep $DURATION sec"
    sleep $DURATION
    
    #for sbus in $sbus_list
    for sbus in ${sbus_list[@]}
    do
        echo "=== $SERVER_IP:$PORT $sbus ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -ber -ber-dwell 1
    done

    echo "AAPL PRBS DONE"
}

get_card_config

if [ $STAGE = "RESET" ]
then
    do_reset
elif [ $STAGE = "INIT" ]
then
    do_init
elif [ $STAGE = "PRBS" ]
then
    do_prbs | tee /data/nic_arm/aapl/aapl.log
else
    echo "Invalid stage $STAGE"
fi

