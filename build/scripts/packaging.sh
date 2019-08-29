# !/bin/bash

# Set quit on error
set -e

if [[ $# -eq 0 ]]
then
    arch=amd64
else
    if [[ $1 == "arm" || $1 == "arm64" ]]
    then
        arch=arm64
    else
        arch=amd64
    fi
fi

echo "============================================"
echo "Start packaging Diag environment for $arch"

BUILD_DIR=$(pwd)
TOP_DIR=$(dirname $BUILD_DIR)

TEMP_DIR=$BUILD_DIR/temp/$arch/diag/
NIC_UTIL_DIR=$BUILD_DIR/temp/$arch/nic_util/
IMG_DIR=$BUILD_DIR/images/

# In case images/ folder is not created yet for new repo
mkdir -p images/

# Prepare all folders
mkdir -p $TEMP_DIR
mkdir -p $TEMP_DIR/dsp
mkdir -p $TEMP_DIR/util
mkdir -p $TEMP_DIR/dshell
mkdir -p $TEMP_DIR/config
mkdir -p $TEMP_DIR/config/redis/
mkdir -p $TEMP_DIR/scripts
mkdir -p $TEMP_DIR/regression
mkdir -p $TEMP_DIR/tools

# Prepare files
cd $TOP_DIR/diag/python/infra/config/
./parseYaml.py

# Copy all the files needed
echo "--------------------"
echo "Copying diag files"
cd $BUILD_DIR
cp -r $TOP_DIR/diag/app/bin/linux_$arch/diagmgr $TEMP_DIR/
cp -r $TOP_DIR/diag/app/bin/linux_$arch/dsp/ $TEMP_DIR/
cp -r $TOP_DIR/diag/app/bin/linux_$arch/util/ $TEMP_DIR/
[ "$(ls -A $TOP_DIR/diag/app/bin/linux_$arch/cbin)" ] && cp -r $TOP_DIR/diag/app/bin/linux_$arch/cbin/* $TEMP_DIR/util/
cp -r -L $TOP_DIR/diag/scripts/$arch/* $TEMP_DIR/scripts
cp -r $TOP_DIR/diag/scripts/* $TEMP_DIR/scripts/
cp $TOP_DIR/diag/scripts/version* $TEMP_DIR/scripts/
cp -r $TOP_DIR/diag/scripts/asic/ $TEMP_DIR/scripts/

cp -r $TOP_DIR/diag/python/ $TEMP_DIR/

cp -r $TOP_DIR/tools/bin/$arch/* $TEMP_DIR/tools/
cp -r $TOP_DIR/diag/util/bin/$arch/* $TEMP_DIR/util/

if [[ $arch == "amd64" ]]
then
    cp $TOP_DIR/diag/python/regression/scripts/start_diag.sh $TEMP_DIR/..
    cp -r $TOP_DIR/tools/pki/ $TEMP_DIR/tools/
    cp -r $TOP_DIR/tools/barco/ $TEMP_DIR/tools/
else
    cp $TOP_DIR/diag/python/regression/scripts/start_diag.arm64.sh $TEMP_DIR/..
fi
# Version
git log --name-status HEAD^..HEAD > $TEMP_DIR/scripts/version.txt
git status >> $TEMP_DIR/scripts/version.txt

echo "Copying diag files -- Done"

# NIC utilities
if [[ $arch == "arm64" ]]
then
    echo "--------------------"
    echo "Preparing NIC utilities"

    mkdir -p $NIC_UTIL_DIR

    cp $TOP_DIR/diag/app/bin/linux_arm64/cbin/cpld      $NIC_UTIL_DIR
    cp $TOP_DIR/diag/app/bin/linux_arm64/util/devmgr    $NIC_UTIL_DIR
    cp $TOP_DIR/diag/app/bin/linux_arm64/util/eeutil    $NIC_UTIL_DIR
    cp $TOP_DIR/diag/app/bin/linux_arm64/util/smbutil   $NIC_UTIL_DIR
    cp $TOP_DIR/diag/app/bin/linux_arm64/util/rtcutil   $NIC_UTIL_DIR
    cp $TOP_DIR/diag/app/bin/linux_arm64/util/emmc      $NIC_UTIL_DIR
    cp $TOP_DIR/diag/app/bin/linux_arm64/util/asicutil  $NIC_UTIL_DIR
    cp $TOP_DIR/tools/bin/arm64/gb_25nrz_cfg            $NIC_UTIL_DIR
    cp $TOP_DIR/diag/python/regression/update_mac.py    $NIC_UTIL_DIR
    cp $TEMP_DIR/scripts/version.txt                    $NIC_UTIL_DIR

    cd $NIC_UTIL_DIR
    tar czf $IMG_DIR/nic_util.tar -C $BUILD_DIR/temp/$arch/ nic_util/

    echo "NIC Utilities Done"
fi



# Prepare ASIC files
echo "--------------------"
echo "Preparing ASIC files"
DIAG_ASIC_PATH=$TOP_DIR/asic_repo/$arch
SNAKE_CFG_PATH=/vol/hw/diag/diag_repo/snake_configs/
ASIC_REPO_PATH=/vol/hw/diag/diag_repo/asic/$arch

if [[ $arch == "amd64" ]]
then
    DIAG_ASIC_IMG_PATH=$TEMP_DIR/asic

    mkdir -p $DIAG_ASIC_PATH
    mkdir -p $DIAG_ASIC_IMG_PATH
    mkdir -p $DIAG_ASIC_IMG_PATH

    echo "Update ASIC lib"
    rsync -r $ASIC_REPO_PATH/* $DIAG_ASIC_PATH/
    
    echo "Copy ASIC lib to $arch image"
    rsync -r $DIAG_ASIC_PATH/ $DIAG_ASIC_IMG_PATH/

    echo "Copy snake CFG to $arch image"
    rsync -r $SNAKE_CFG_PATH/ $TEMP_DIR/

fi

if [[ $arch == "arm64" ]]
then
    DIAG_ASIC_IMG_PATH=$BUILD_DIR/temp/$arch/nic_arm
    ARM_ASIC_PATH=$DIAG_ASIC_IMG_PATH/nic
   
    mkdir -p $ARM_ASIC_PATH
    mkdir -p $DIAG_ASIC_PATH

    echo "Update ASIC lib"
    rsync -r $ASIC_REPO_PATH/* $DIAG_ASIC_PATH/

    echo "Copy ASIC lib to $arch image"
    cp -r $DIAG_ASIC_PATH/* $ARM_ASIC_PATH/

    echo "Copy snake CFG to $arch image"
    cp -r $SNAKE_CFG_PATH/* $DIAG_ASIC_IMG_PATH

    echo "Copy aapl $arch image"
    cp -r $TOP_DIR/diag/scripts/asic/aapl/ $DIAG_ASIC_IMG_PATH

    cp $ARM_ASIC_PATH/asic_lib/diag.exe $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $TOP_DIR/diag/python/regression/arm_nic/* $DIAG_ASIC_IMG_PATH/
    cp $TOP_DIR/diag/python/regression/scripts/dft_profile_nic $DIAG_ASIC_IMG_PATH/
    cp $TOP_DIR/diag/python/regression/scripts/nic_config.sh $DIAG_ASIC_IMG_PATH/
    cp $TOP_DIR/diag/python/regression/scripts/rtc_sanity.sh $DIAG_ASIC_IMG_PATH/
    cp $TOP_DIR/diag/scripts/vmarg.sh $DIAG_ASIC_IMG_PATH/
    cp $TOP_DIR/diag/scripts/asic/snake.h.a.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $TOP_DIR/diag/scripts/asic/snake.p.a.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $TOP_DIR/diag/scripts/asic/prbs.e.a.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $TOP_DIR/diag/scripts/asic/prbs.p.a.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $TOP_DIR/diag/scripts/asic/prbs.e.a.forio.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $TOP_DIR/diag/scripts/asic/snake_all.tcl $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
    cp $TOP_DIR/diag/scripts/asic/nic_prbs.sh $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/

    tar czf $IMG_DIR/nic_arm.tar -C $BUILD_DIR/temp/$arch/ nic_arm/
fi

echo "ASIC file -- Done"

# Prepare image
echo "--------------------"
echo "Preparing image"
cd $BUILD_DIR/temp/$arch
tar czf $IMG_DIR/image_$arch.tar *

echo "Preparing image -- Done"

echo "--------------------"
echo "Cleaning up"
rm -rf $BUILD_DIR/temp/$arch
echo "Clean up -- Done"

echo "--------------------"
echo "Done packaging $arch"
echo "============================================"
