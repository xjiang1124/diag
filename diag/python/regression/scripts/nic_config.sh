cpld_id="$(cpld -r 0x80)"
echo "P0: cpld_id $cpld_id"
cpld_id="${cpld_id}"
echo "P1: cpld_id $cpld_id"

if [[ $cpld_id == "0x12" ]]
then
    type="NAPLES100"
elif [[ $cpld_id == "0x13" ]]
then
    type="NAPLES25"
fi

echo "$type Detected!"
echo "export CARD_TYPE=\"$type\"" >> /etc/profile

echo "RTC Resetted"
cpld -w 0x2F 0x2C

echo "Hello"
