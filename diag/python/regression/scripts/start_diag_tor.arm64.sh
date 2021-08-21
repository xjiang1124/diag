# !/bin/bash
arch=arm64

#killall hal

# Set up environment
echo "-------------------"
echo "Preparing diag environment"
DIAG_DIR=/home/diag/diag

#mkdir -p $DIAG_DIR/log/
mkdir -p /data/nic_arm/log/
mkdir -p $DIAG_DIR
cd $DIAG_DIR
ln -s /data/nic_arm/log/

source /etc/profile

if [[ $# -eq 1 ]]
then
    slot=$1
else
    slot_val="$(cpldapp -r 0xA)"
    slot=$((slot_val & 0x7F))
fi
nic_name_pre="CARD_NAME=NIC"
nic_name="$nic_name_pre$slot"
echo "nic_name: $nic_name"
echo "export $nic_name" >> /etc/profile

source /etc/profile
sh /data/nic_arm/rtc_sanity.sh

echo "Preparing diag environment -- Done"

num="$(ps -elf | grep diagmgr | wc | awk -F " " '{print $1}')"
echo "num $num"
if [[ $num -le 1 ]]
then
    echo "Launching diagmgr"
    diagmgr &
fi


echo "-------------------"
echo "Set up diag $arch -- Done"
echo "===================================="

