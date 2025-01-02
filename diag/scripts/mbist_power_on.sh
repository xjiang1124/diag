# !/bin/bash

slot=$1

echo "MBIST Power on init"

turn_on_slot.sh off $slot

sleep 3; turn_on_slot_3v3.sh on $slot
data=$(i2cget -y $(($slot + 2)) 0x4a 0x11)
data=$(( $data & 0xF0 ))
i2cset -y $((slot+2)) 0x4a 0x11 $data
#i2cset -y $((slot+2)) 0x4a 0x20 0
inventory -sts -slot $slot

sleep 1;
turn_on_slot_12v.sh on $slot
sleep 5;
turn_on_slot_12v.sh off $slot
sleep 10;
turn_on_slot_12v.sh on $slot

 sleep 10; turn_on_slot.sh on $slot

 sleep 3; turn_on_slot.sh off $slot
 sleep 10; turn_on_slot.sh on $slot

inventory -sts -slot $slot
i2cdump -y $((slot+2)) 0x4a

