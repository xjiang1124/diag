# !/bin/bash
arch=arm64


# Set up environment
echo "-------------------"
echo "Preparing diag environment"
DIAG_DIR=/home/diag/diag
mkdir -p $DIAG_DIR/diag/log/


if [[ -f /etc/profile.bak ]]
then
    echo "Skip back up profile"
else
    cp /etc/profile /etc/profile.bak
fi
cat /etc/profile.bak $DIAG_DIR/python/regression/scripts/dft_profile_nic > /etc/profile
source /etc/profile

if [[ $# -eq 1 ]]
then
    slot=$1
else
    slot_val="$(cpld -r 0xA)"
    slot=$((slot_val & 0x7F))
fi
nic_name_pre="CARD_NAME=NIC"
nic_name="$nic_name_pre$slot"
echo "nic_name: $nic_name"
echo "export $nic_name" >> /etc/profile

source /etc/profile
sh $DIAG_DIR/python/regression/scripts/nic_config.sh

echo "Preparing diag environment -- Done"

source /etc/profile

num="$(ps -elf | grep diagmgr | wc | awk -F " " '{print $1}')"
echo "num $num"
if [[ $num -eq 1 ]]
then
    echo "Launching diagmgr"
    diagmgr &
fi


echo "-------------------"
echo "Set up diag $arch -- Done"
echo "===================================="

