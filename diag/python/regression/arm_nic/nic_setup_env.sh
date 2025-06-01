source /data/nic_arm/nic_config.sh $@

source /etc/profile

cpld_id="$(/data/nic_util/xo3dcpld -r 0x80)"
if [[ $cpld_id == "0x0" ]]
then
    echo "Try Capri CPLD"
	cpld_id="$(/data/nic_util/cpld -r 0x80)"
elif [[ $cpld_id == "0x60" || $cpld_id == "0x61" || $cpld_id == "0x84" ]]
then
    echo "Giglio CPLD"
else
    echo "Elba CPLD"
fi
cpld_id="$(($cpld_id))"
echo "cpld id: $cpld_id"

if [[ $cpld_id -eq 96 || $cpld_id -eq 97 || $cpld_id -eq 132 ]]
then
    export ASIC_LIB_BUNDLE=/data/nic_arm/giglio
elif [[ $cpld_id -ge 64 ]]
then
    export ASIC_LIB_BUNDLE=/data/nic_arm/elba
else
    export ASIC_LIB_BUNDLE=/data/nic_arm/capri
fi

rm -rf /data/nic_arm/nic
ln -sf $ASIC_LIB_BUNDLE /data/nic_arm/nic

export ASIC_LIB=$ASIC_LIB_BUNDLE/asic_lib
export ASIC_SRC=$ASIC_LIB_BUNDLE//asic_src
export ASIC_GEN=$ASIC_LIB_BUNDLE//asic_src
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ASIC_LIB:$ASIC_LIB_BUNDLE/depend_libs/nic/hal/third-party/judy/aarch64/lib/:$ASIC_LIB_BUNDLE/depend_libs/tool/toolchain/asic_third_party/lib/:$ASIC_LIB_BUNDLE/depend_libs/nic/hal/third-party/zmq/aarch64/:$ASIC_LIB_BUNDLE/depend_libs/nic/hal/third-party/sknobs/aarch64/lib/:/platform/lib/

mkdir -p $ASIC_SRC/ip/cosim/library/
cp $ASIC_LIB_BUNDLE/../init.tcl $ASIC_SRC/ip/cosim/library/
#cp $ASIC_LIB/diag_s.exe $ASIC_SRC/ip/cosim/tclsh/diag.exe

if [[ $CARD_TYPE == "FORIO" ]]
then
    /data/nic_util/gb_25nrz_cfg
fi

