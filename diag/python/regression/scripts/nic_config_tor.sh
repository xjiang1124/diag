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

CORECLK417MHZ=0
CORECLK833MHZ=0
cpld_id="$(cpldapp -r 0x80)"

cpld_id="${cpld_id}"
if [[ $cpld_id == "0x80" ]]
then
    type="TAORMINA"
else
    type="UNKNOWN"
fi

echo "$type Detected!"
echo "export CARD_TYPE=\"$type\"" >> /etc/profile
echo "export CARD_ENV=\"ARM\"" >> /etc/profile
export CARD_TYPE=$type
export CARD_ENV="ARM"

ASIC_LIB_BUNDLE="/data/nic_arm/nic"
ASIC_SRC=$ASIC_LIB_BUNDLE/asic_src
ASIC_LIB=$ASIC_LIB_BUNDLE/asic_lib
ASIC_GEN=$ASIC_SRC

echo "export ASIC_LIB_BUNDLE=/data/nic_arm/nic" >> /etc/profile
echo "export ASIC_SRC=\$ASIC_LIB_BUNDLE/asic_src" >> /etc/profile
echo "export ASIC_LIB=\$ASIC_LIB_BUNDLE/asic_lib" >> /etc/profile
echo "export ASIC_GEN=\$ASIC_SRC" >> /etc/profile
echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ASIC_LIB:$ASIC_LIB_BUNDLE/depend_libs/nic/hal/third-party/judy/aarch64/lib/:$ASIC_LIB_BUNDLE/depend_libs/tool/toolchain/asic_third_party/lib/:$ASIC_LIB_BUNDLE/depend_libs/nic/hal/third-party/zmq/aarch64/:$ASIC_LIB_BUNDLE/depend_libs/nic/hal/third-party/sknobs/aarch64/lib/:/platform/lib/" >> /etc/profile

echo "nic_config done"

