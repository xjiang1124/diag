NIC_ARM_DIR=/data/nic_arm/

if [[ -f /etc/profile.bak ]]
then
    echo "Skip back up profile"
else
    cp /etc/profile /etc/profile.bak
fi
cat /etc/profile.bak $NIC_ARM_DIR/dft_profile_nic > /etc/profile
source /etc/profile


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
elif [[ $cpld_id == "0x15" ]]
then
    type="VOMERO"
fi

echo "$type Detected!"
echo "export CARD_TYPE=\"$type\"" >> /etc/profile
export CARD_TYPE=$type
export CARD_ENV="ARM"


echo "nic_config done"
