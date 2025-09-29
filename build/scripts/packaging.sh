# !/bin/bash

# Set quit on error
set -e

if [[ $# -eq 0 ]]
then
    arch=amd64
    asic=all
else
    if [[ $1 == "arm64" ]]
    then
        arch=arm64
    elif [[ $1 == "arm" ]]
    then
        arch=arm
    else
        arch=amd64
    fi
fi

## parse asic types
IFS=',' read -r -a asicArr <<< "$2"
declare -a asic_list
for item in ${asicArr[@]}
do
    if [[ $item == "elba" ]] || \
       [[ $item == "capri" ]] || \
       [[ $item == "giglio" ]] || \
       [[ $item == "salina" ]] || \
       [[ $item == "vulcano" ]]
    then
        asic_list+=($item)
    fi
done
if [[ ${#asic_list[@]} == 0 ]]
then
    asic_list=("giglio" "elba" "capri" "salina" "vulcano")
fi

for asic in ${asic_list[@]}
do
    echo "asic: $asic"
done

# if asiclib is not specified in make command, default is "stable", we use the stable nic.tar.gz in /vol/hw, for mfg release
# if asiclib=latest in make command, we use the latest build nic.tar.gz in /vol/builds/hourly-asic/
asiclib="stable"
if [[ $# -eq 3 ]]
then
    asiclib=$3
fi


echo "============================================"
echo "Start packaging Diag environment for $arch"

BUILD_DIR=$(pwd)
TOP_DIR=$(dirname $BUILD_DIR)

for asic in ${asic_list[@]}
do

    ## initialize defaults for j2cdriver
    if [[ $asic == "giglio" ]]
    then
        declare -a j2cd_list=("ftdi" "fpga")
    elif [[ $asic == "elba" ]]
    then
        declare -a j2cd_list=("ftdi" "lipari" "fpga")
    elif [[ $asic == "salina" || $asic == "vulcano" ]]
    then
        declare -a j2cd_list=("fpga")
    else
        declare -a j2cd_list=("ftdi")
    fi

    TEMP_DIR_TOP=$BUILD_DIR/temp_$asic/$arch/
    TEMP_DIR=$TEMP_DIR_TOP/diag/
    NIC_UTIL_DIR=$TEMP_DIR_TOP/nic_util/
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
    if [[ $arch != "arm" ]]
    then    
        cp -r -L $TOP_DIR/diag/scripts/$arch/* $TEMP_DIR/scripts
    fi
    cp -r $TOP_DIR/diag/scripts/* $TEMP_DIR/scripts/
    cp $TOP_DIR/diag/scripts/version* $TEMP_DIR/scripts/
    cp -r $TOP_DIR/diag/scripts/asic/ $TEMP_DIR/scripts/
    
    cp -r $TOP_DIR/diag/python/ $TEMP_DIR/
    
    if [[ $arch != "arm" ]]
    then    

        cp -r $TOP_DIR/tools/bin/$arch/* $TEMP_DIR/tools/
        cp -r $TOP_DIR/diag/util/bin/$arch/* $TEMP_DIR/util/
    fi

    if [[ $arch == "amd64" ]]
    then
        cp $TOP_DIR/diag/python/regression/scripts/start_diag.sh $TEMP_DIR/..
        if [[ $asic == "giglio" ]]
        then
            sed -i 's/ASIC_DIR_SUB_TOP=\$ASIC_DIR_TOP\/elba/ASIC_DIR_SUB_TOP=$ASIC_DIR_TOP\/giglio/' $TEMP_DIR/../start_diag.sh
            echo "export ASIC_TYPE=GIGLIO" >> $TEMP_DIR/python/regression/scripts/dft_profile_mtp
        fi
        if [[ $asic == "elba" ]]
        then
            echo "export ASIC_TYPE=ELBA" >> $TEMP_DIR/python/regression/scripts/dft_profile_mtp
        fi
        if [[ $asic == "salina" ]]
        then
            echo "export ASIC_TYPE=SALINA" >> $TEMP_DIR/python/regression/scripts/dft_profile_mtp
        fi
        if [[ $asic == "vulcano" ]]
        then
            echo "export ASIC_TYPE=VULCANO" >> $TEMP_DIR/python/regression/scripts/dft_profile_mtp
        fi
        if [[ $asic == "capri" ]]
        then
            echo "export ASIC_TYPE=CAPRI" >> $TEMP_DIR/python/regression/scripts/dft_profile_mtp
        fi
        cp $TOP_DIR/diag/app/pkg/linux_$arch/clib/libacc_mtp.so $TEMP_DIR/tools/.
        cp $TOP_DIR/diag/app/pkg/linux_$arch/clib/libacc_turbo.so $TEMP_DIR/tools/.
        cp $TOP_DIR/diag/python/regression/scripts/start_diag_tor.sh $TEMP_DIR/..
        cp -r $TOP_DIR/tools/pki/ $TEMP_DIR/tools/
        cp -r $TOP_DIR/tools/barco/ $TEMP_DIR/tools/
        # Copy this for Taormina.  Need it in amd64 pkgt. Bringup doesn't pull in the arm64 pkg.  
        cp $TOP_DIR/tools/bin/arm64/stressapptest_arm           $TEMP_DIR/tools/
    elif [[ $arch == "arm" ]]
    then
        # nothing right now     
        echo "Nothing to do for arm32 right now"    
    else
        cp $TOP_DIR/diag/python/regression/scripts/start_diag.arm64.sh $TEMP_DIR/..
        cp $TOP_DIR/tools/bin/arm64/mmc.latest           $TEMP_DIR/tools/
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
        mkdir -p $NIC_UTIL_DIR/sw/
    
        cp $TOP_DIR/diag/app/bin/linux_arm64/cbin/cpld          $NIC_UTIL_DIR
        cp $TOP_DIR/diag/app/bin/linux_arm64/cbin/xo3dcpld      $NIC_UTIL_DIR
        cp $TOP_DIR/diag/app/bin/linux_arm64/cbin/artix7fpga    $NIC_UTIL_DIR
        cp $TOP_DIR/tools/bin/arm64/stressapptest_arm           $NIC_UTIL_DIR
        cp $TOP_DIR/tools/bin/arm64/fio                         $NIC_UTIL_DIR
        cp $TOP_DIR/tools/bin/arm64/elba-chk-secboot-rdy.sh     $NIC_UTIL_DIR
        cp $TOP_DIR/diag/app/bin/linux_arm64/util/devmgr        $NIC_UTIL_DIR
        cp $TOP_DIR/diag/app/bin/linux_arm64/util/devmgr_v2     $NIC_UTIL_DIR
        cp $TOP_DIR/diag/app/bin/linux_arm64/util/eeutil        $NIC_UTIL_DIR
        cp $TOP_DIR/diag/app/bin/linux_arm64/util/smbutil       $NIC_UTIL_DIR
        cp $TOP_DIR/diag/app/bin/linux_arm64/util/rtcutil       $NIC_UTIL_DIR
        cp $TOP_DIR/diag/app/bin/linux_arm64/util/emmcutil      $NIC_UTIL_DIR
        cp $TOP_DIR/diag/app/bin/linux_arm64/util/asicutil      $NIC_UTIL_DIR
        cp $TOP_DIR/diag/python/regression/update_mac.py        $NIC_UTIL_DIR
        cp $TOP_DIR/diag/python/regression/scripts/run_ddrbist.sh     $NIC_UTIL_DIR
        cp $TOP_DIR/diag/python/regression/scripts/run_ddrbist_arm.sh $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/clear_nic_config.sh            $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/fix_o2_vrm.sh                  $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/fix_o2_vrm_oc.sh               $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/mvl_acc.sh                     $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/mvl_stub.sh                    $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/mvl_link.sh                    $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/mvl_acc_capri.sh               $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/mvl_stub_capri.sh              $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/mvl_link_capri.sh              $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/mvl_chk_link.sh                $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/run_edma.sh                    $NIC_UTIL_DIR
        cp $TOP_DIR/diag/scripts/xcvr_phy_intf.sh               $NIC_UTIL_DIR
        cp $TOP_DIR/tools/bin/arm64/gb_25nrz_cfg                $NIC_UTIL_DIR
        cp $TOP_DIR/tools/edma/edma_test.tar.gz                 $NIC_UTIL_DIR
        cp $TEMP_DIR/scripts/version.txt                        $NIC_UTIL_DIR
        cp $TEMP_DIR/scripts/pre_ltc3888                        $NIC_UTIL_DIR
        cp $TEMP_DIR/scripts/pre_ltc3888_1                      $NIC_UTIL_DIR
        cp $TEMP_DIR/scripts/ltc3888.txt                        $NIC_UTIL_DIR
        cp $TEMP_DIR/scripts/ltc3888_1.txt                      $NIC_UTIL_DIR
    
        cp $TOP_DIR/diag/scripts/sw/*                           $NIC_UTIL_DIR/sw/
        cp $TOP_DIR/tools/bin/arm64/mmc.latest                  $NIC_UTIL_DIR/
    
        cd $NIC_UTIL_DIR
        tar czf $IMG_DIR/nic_util.tar -C $TEMP_DIR_TOP nic_util/
    
        echo "NIC Utilities Done"
    fi
    
    # Prepare ASIC files
    echo "--------------------"
    echo "Preparing ASIC files"

    echo "--------------------"
    echo "Processing $asic"

    DIAG_ASIC_PATH=$TOP_DIR/asic_repo/$asic/$arch
    #SNAKE_CFG_PATH=/vol/hw/diag/diag_repo/snake_configs/
    #ASIC_REPO_PATH=/vol/hw/diag/diag_repo/asic/$asic/$arch
    #ASIC_REPO_PATH=/vol/hw/diag/diag_repo/asic.2021.11.17/$asic/$arch
    
    if [[ $arch == "amd64" ]]
    then
        DIAG_ASIC_IMG_PATH=$TEMP_DIR/asic_all/$asic/
    
        #mkdir -p $DIAG_ASIC_PATH
        mkdir -p $DIAG_ASIC_IMG_PATH
    
        #echo "Update ASIC lib"
        #rsync -r $ASIC_REPO_PATH/* $DIAG_ASIC_PATH/
        
        #echo "Copy ASIC lib to $arch image"
        #rsync -r $DIAG_ASIC_PATH/ $DIAG_ASIC_IMG_PATH/
    
        #echo "Copy snake CFG to $arch image"
        #rsync -r $SNAKE_CFG_PATH/ $TEMP_DIR/
        if [[ $asiclib == "stable" ]]
        then
            echo "Copying stable ASIC lib for $asic"
            for j2cd in ${j2cd_list[@]}
            do
                ASIC_IMG="/vol/hw/diag/diag_repo/asic_lib_rel_stable/nic_${arch}_${asic}_${j2cd}.tar.gz"
                cp $ASIC_IMG $TEMP_DIR_TOP/
            done
        fi
        if [[ $asiclib == "latest" ]]
        then
            echo "Copying latest ASIC libs for $asic"
            for j2cd in ${j2cd_list[@]}
            do
                ASIC_IMG="/vol/hw/diag/diag_images/asicimg_latest/nic_${arch}_${asic}_${j2cd}.tar.gz"
                cp $ASIC_IMG $TEMP_DIR_TOP/
            done
        fi
    fi
    
    if [[ $arch == "arm64" ]]
    then
        DIAG_ASIC_IMG_PATH=$TEMP_DIR_TOP/nic_arm/
        ARM_ASIC_PATH=$DIAG_ASIC_IMG_PATH/$asic/
       
        mkdir -p $ARM_ASIC_PATH
        #mkdir -p $DIAG_ASIC_PATH
    
        #echo "Update ASIC lib"
        #rsync -r $ASIC_REPO_PATH/* $DIAG_ASIC_PATH/
    
        #echo "Copy ASIC lib to $arch image"
        #rsync -r $DIAG_ASIC_PATH/* $ARM_ASIC_PATH/
        if [[ $asiclib == "stable" ]]
        then
            echo "Copying stable ASIC lib for $asic"
            ASIC_IMG="/vol/hw/diag/diag_repo/asic_lib_rel_stable/nic_${arch}_${asic}.tar.gz"
            cp $ASIC_IMG $TEMP_DIR_TOP/nic.tar.gz
        fi
        if [[ $asiclib == "latest" ]]
        then
            echo "Copying latest ASIC lib for $asic"
            ASIC_IMG="/vol/hw/diag/diag_images/asicimg_latest/nic_${arch}_${asic}.tar.gz"
            cp $ASIC_IMG $TEMP_DIR_TOP/nic.tar.gz
        fi
        #echo "Copy snake CFG to $arch image"
        #cp -r $SNAKE_CFG_PATH/* $DIAG_ASIC_IMG_PATH
    
        echo "Copy aapl $arch image"
        cp -r $TOP_DIR/diag/scripts/asic/aapl/ $DIAG_ASIC_IMG_PATH
    
        #cp $ARM_ASIC_PATH/asic_lib/diag.exe $ARM_ASIC_PATH/asic_src/ip/cosim/tclsh/
        cp $TOP_DIR/diag/python/regression/arm_nic/* $DIAG_ASIC_IMG_PATH/
        cp $TOP_DIR/diag/python/regression/scripts/dft_profile_nic $DIAG_ASIC_IMG_PATH/
        cp $TOP_DIR/diag/python/regression/scripts/nic_config.sh $DIAG_ASIC_IMG_PATH/
        cp $TOP_DIR/diag/python/regression/scripts/rtc_sanity.sh $DIAG_ASIC_IMG_PATH/
        cp $TOP_DIR/diag/scripts/vmarg.sh $DIAG_ASIC_IMG_PATH/
        cp $TOP_DIR/diag/scripts/asic/snake.h.a.tcl $DIAG_ASIC_IMG_PATH
        cp $TOP_DIR/diag/scripts/asic/snake.p.a.tcl $DIAG_ASIC_IMG_PATH
        cp $TOP_DIR/diag/scripts/asic/prbs.e.a.tcl $DIAG_ASIC_IMG_PATH
        cp $TOP_DIR/diag/scripts/asic/prbs.p.a.tcl $DIAG_ASIC_IMG_PATH
        cp $TOP_DIR/diag/scripts/asic/prbs.e.a.forio.tcl $DIAG_ASIC_IMG_PATH
        cp $TOP_DIR/diag/scripts/asic/snake_all.tcl $DIAG_ASIC_IMG_PATH
        cp $TOP_DIR/diag/scripts/asic/elb_efuse_prog.tcl $DIAG_ASIC_IMG_PATH/
        cp $TOP_DIR/diag/scripts/asic/gig_efuse_prog.tcl $DIAG_ASIC_IMG_PATH/
        cp $TOP_DIR/diag/scripts/asic/elb_arm*tcl $DIAG_ASIC_IMG_PATH
        cp $TOP_DIR/diag/scripts/asic/nic_prbs.sh $DIAG_ASIC_IMG_PATH
    fi

    #if [[ $arch == "arm64" ]]
    #then
    #    echo "Generate nic_arm.tar"
    #    cd $TEMP_DIR_TOP; tar czf $IMG_DIR/nic_arm_$asic.tar nic_arm/ 
    #fi
    
    echo "ASIC file -- Done"
    
    # Prepare image
    echo "--------------------"
    echo "Preparing image"
    cd $TEMP_DIR_TOP
    tar czf $IMG_DIR/image_${arch}_${asic}.tar *
    
    echo "--------------------"
    echo "Done packaging $arch; asic $asic"

    echo "============================================"   
done

for asic in ${asic_list[@]}
do

    echo "Preparing image -- Done"
    
    echo "--------------------"
    echo "Cleaning up"
    rm -rf $BUILD_DIR/temp_$asic/$arch
    echo "Clean up -- Done"
done
