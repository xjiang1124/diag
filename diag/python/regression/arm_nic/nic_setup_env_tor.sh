source /data/nic_arm/nic_config.sh

cpld_id="$(cpldapp -r 0x80)"
cpld_id="$(($cpld_id))"
echo "cpld id: $cpld_id"

export ASIC_LIB_BUNDLE=/data/nic_arm/elba

rm -rf /data/nic_arm/nic
ln -sf $ASIC_LIB_BUNDLE /data/nic_arm/nic

export ASIC_LIB=$ASIC_LIB_BUNDLE/asic_lib
export ASIC_SRC=$ASIC_LIB_BUNDLE//asic_src
export ASIC_GEN=$ASIC_LIB_BUNDLE//asic_src
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ASIC_LIB:$ASIC_LIB_BUNDLE/depend_libs/nic/hal/third-party/judy/aarch64/lib/:$ASIC_LIB_BUNDLE/depend_libs/tool/toolchain/asic_third_party/lib/:$ASIC_LIB_BUNDLE/depend_libs/nic/hal/third-party/zmq/aarch64/:$ASIC_LIB_BUNDLE/depend_libs/nic/hal/third-party/sknobs/aarch64/lib/:/platform/lib/

mkdir -p $ASIC_SRC/ip/cosim/library/
cp $ASIC_LIB_BUNDLE/../init.tcl $ASIC_SRC/ip/cosim/library/
#cp $ASIC_LIB/diag_s.exe $ASIC_SRC/ip/cosim/tclsh/diag.exe

