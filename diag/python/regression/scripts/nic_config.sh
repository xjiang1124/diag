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

sh /home/diag/diag/python/regression/scripts/rtc_sanity.sh

echo "Hello"
