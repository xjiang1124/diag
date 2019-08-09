#!/bin/bash

echo $CARD_TYPE

SERVER_IP=localhost
PORT=9000

sbus_list="34 35 36 37 38 39 40 41"
for sbus in $sbus_list
do
    echo "$SERVER_IP:$PORT $sbus"
    aapl serdes-init -server $SERVER_IP -port $PORT -addr $sbus -reset 
    #sleep 0.5
done

echo "AAPL ETH SERDES RESET DONE"
