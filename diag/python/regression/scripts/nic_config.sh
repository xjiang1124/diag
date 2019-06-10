PATH=$PATH:/data/nic_util/
PATH=$PATH:/data/nic_arm/

cpld_id="$(cpld -r 0x80)"
echo "P0: cpld_id $cpld_id"
cpld_id="${cpld_id}"
echo "P1: cpld_id $cpld_id"

cpld -w 0x1 0x6

if [[ $cpld_id == "0x12" ]]
then
    type="NAPLES100"
elif [[ $cpld_id == "0x13" ]]
then
    type="NAPLES25"
elif [[ $cpld_id == "0x14" ]]
then
    type="FORIO"
fi

echo "$type Detected!"
echo "export CARD_TYPE=\"$type\"" >> /etc/profile
export CARD_TYPE=$type
export CARD_ENV="ARM"

sh /data/nic_arm/rtc_sanity.sh

echo "nic_config done"
