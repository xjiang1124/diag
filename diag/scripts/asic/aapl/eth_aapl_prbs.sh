#!/bin/bash
echo $CARD_TYPE

function do_prbs() {
    SERVER_IP=localhost
    PORT=9000
    duration=2
    
    sbus_list="34 35 36 37 38 39 40 41"
    #sbus_list="2 18"
    for sbus in $sbus_list
    do
        echo "=== $SERVER_IP:$PORT $sbus ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -atten 0 -pre 2 -post 12
        aapl dfe -server $SERVER_IP -port $PORT -addr $sbus -pcal-tune
        aapl dfe -server $SERVER_IP -port $PORT -addr $sbus -start-adaptive
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -display
    done
    
    for sbus in $sbus_list
    do
        echo "=== $SERVER_IP:$PORT $sbus ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -tx-data-sel PRBS31 -rx-mode PRBS31
    done
    
    
    for sbus in $sbus_list
    do
        echo "=== $SERVER_IP:$PORT $sbus ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -error-reset
    done
    
    sleep $duration
    
    for sbus in $sbus_list
    do
        echo "=== $SERVER_IP:$PORT $sbus ==="
        sleep $duration
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -ber -ber-dwell 1
    done

    echo "AAPL PRBS DONE"
}

do_prbs | tee /data/nic_arm/aapl/aapl.log
