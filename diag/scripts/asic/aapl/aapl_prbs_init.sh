echo $CARD_TYPE

SERVER_IP=localhost
PORT=9000

sbus_list="2 4 6 8 10 12 14 16 18 20 22 24 26 28 30 32"
#sbus_list="2 18"
#sbus_list="4 6 8 10 12 14 16 20 22 24 26 28 30 32"

for sbus in $sbus_list
do
    echo "$SERVER_IP:$PORT $sbus"
    aapl  serdes-init -server $SERVER_IP -port $PORT -addr $sbus -firm /data/nic_arm/aapl/serdes.0x1094_2347.rom
    #sleep 0.5
    aapl  serdes-init -server $SERVER_IP -port $PORT -addr $sbus -div 160 -width 40 -elb -disable-signal-ok
done
