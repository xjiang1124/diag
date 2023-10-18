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

if [[ $asic_type != "UNKNOW" ]]
then
    if [[ $asic_type == "ELBA" ]]
    then
        ARM_ASIC_PATH=$NIC_ARM_DIR/elba
    elif [[ $asic_type == "GIGLIO" ]]
    then
        ARM_ASIC_PATH=$NIC_ARM_DIR/giglio
    else
        ARM_ASIC_PATH=$NIC_ARM_DIR/capri
    fi
    echo "Copy scripts to nic_arm"
    ASIC_IMG=/data/nic.tar.gz
    tar xf $ASIC_IMG -C /data
    cp -r /data/nic/fake_root_target/nic/* $ARM_ASIC_PATH
    cp -r /data/nic/fake_root_target/nic/asic_src/ip/cosim/tclsh/.git_rev.tcl $ARM_ASIC_PATH/asic_version.txt
    rm -rf /data/nic/
    cp $ARM_ASIC_PATH/asic_lib/diag_s.exe $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/diag.exe
    cp $NIC_ARM_DIR/snake.h.a.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $NIC_ARM_DIR/snake.p.a.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $NIC_ARM_DIR/prbs.e.a.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $NIC_ARM_DIR/prbs.p.a.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $NIC_ARM_DIR/prbs.e.a.forio.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $NIC_ARM_DIR/snake_all.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $NIC_ARM_DIR/elb_efuse_prog.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $NIC_ARM_DIR/gig_efuse_prog.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $NIC_ARM_DIR/elb_arm*tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $NIC_ARM_DIR/nic_prbs.sh $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
fi
echo "nic_config done"

