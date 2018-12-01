cpld_id="$(cpld -r 0x80)"
cpld_id="${cpld_id}"

if [[ $cpld_id == "0x12" ]]
then
    type="NAPLES100"
fi
echo "$type Detected!"
echo "export CARD_TYPE=\"$type\"" >> /etc/profile

echo "Hello"
