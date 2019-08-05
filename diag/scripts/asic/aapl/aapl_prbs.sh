#!/bin/bash
echo $CARD_TYPE

function do_prbs() {
SERVER_IP=localhost
PORT=9000
duration=2

sbus_list="2 4 6 8 10 12 14 16 18 20 22 24 26 28 30 32"
#sbus_list="2 18"
for sbus in $sbus_list
do
    echo "=== $SERVER_IP:$PORT $sbus ==="
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
}

do_prbs | tee aapl.log
