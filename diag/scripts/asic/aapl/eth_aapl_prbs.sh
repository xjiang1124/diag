#!/bin/bash

if [ $# -ge 1 ]
then
    POLY=$1
else
    POLY="PRBS31"
fi

if [ $# -ge 2 ]
then
    DURATION=$2
else
    DURATION=60
fi

echo "POLY: $POLY; DURA: $DURATION"

echo $CARD_TYPE
card_type=$CARD_TYPE

function do_prbs() {
    SERVER_IP=localhost
    PORT=9000
    $DURATION=60
    
    #sbus_list_naples100="34 35 36 37 38 39 40 41"
    declare -a sbus_list_naples100=("34" "35" "36" "37" "38" "39" "40" "41")
    declare -a atten_list_naples100=("0" "0" "0" "0" "0" "0" "0" "0")
    declare -a pre_list_naples100=("2" "2" "2" "2" "2" "2" "2" "2")
    declare -a post_list_naples100=("12" "12" "12" "12" "12" "12" "12" "12")

    if [ $card_type = "NAPLES100" ]
    then
        sbus_list=("${sbus_list_naples100[@]}") 
        atten_list=("${atten_list_naples100[@]}") 
        pre_list=("${pre_list_naples100[@]}") 
        post_list=("${post_list_naples100[@]}") 
    fi

    for idx in "${!sbus_list[@]}"
    do
        sbus=${sbus_list[$idx]}
        atten=${atten_list[$idx]}
        pre=${pre_list[$idx]}
        post=${post_list[$idx]}

        echo "=== $SERVER_IP:$PORT sbus $sbus atten $atten pre $pre post $post ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -atten 0 -pre $pre -post $post
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
    
    sleep $DURATION
    
    #for sbus in $sbus_list
    for sbus in ${sbus_list[@]}
    do
        echo "=== $SERVER_IP:$PORT $sbus ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -ber -ber-dwell 1
    done

    echo "AAPL PRBS DONE"
}

#do_prbs | tee /data/nic_arm/aapl/aapl.log
do_prbs
