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

cpld -w 0x1 0x2   #Capri Bleed Enable

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
elif [[ $cpld_id == "0x1e" ]]
then
    type="VOMERO2"
elif [[ $cpld_id == "0x17" ]]
then
    type="NAPLES25SWM"
elif [[ $cpld_id == "0x19" ]]
then
    type="NAPLES25OCP"
elif [[ $cpld_id == "0x1c" ]]
then
    type="NAPLES100IBM"
elif [[ $cpld_id == "0x1e" ]]
then
    type="VOMERO2"
elif [[ $cpld_id == "0x1f" ]]
then
    type="NAPLES100HPE"
elif [[ $cpld_id == "0x40" ]]
then
    type="BIODONA_D4"
elif [[ $cpld_id == "0x41" ]]
then
    type="BIODONA_D5"
fi

echo "$type Detected!"
echo "export CARD_TYPE=\"$type\"" >> /etc/profile
export CARD_TYPE=$type
export CARD_ENV="ARM"


echo "nic_config done"
