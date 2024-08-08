#!/bin/bash

TEST_DIR=/home/diag/snake_test/
SLOT=$1
#ITE=$2
echo $SLOT
cd $TEST_DIR/nic
export ASIC_LIB_BUNDLE=`pwd`
export ASIC_SRC=$ASIC_LIB_BUNDLE/asic_src
export ASIC_GEN=$ASIC_LIB_BUNDLE/asic_src
export ASIC_LIB=$ASIC_LIB_BUNDLE/asic_lib
cd $ASIC_LIB_BUNDLE/asic_lib
source source_env_path
export LD_LIBRARY_PATH=$ASIC_LIB_BUNDLE/depend_libs/mtp_hack:$LD_LIBRARY_PATH
cd $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
rm -f *
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libJudy.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libgmpxx.so.4 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libcrypto.so.10 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpcap.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpython2.7.so.1.0 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
cd /home/diag/diag/scripts/asic

#time_stamp=$(date "+%m%d%y_%H%M%S")

#fn="sal_snake_${time_stamp}.log"
#echo $fn

#for idx in $(seq 1 1 $ITE)
#do
#    echo "Snake Iteration $idx"
    turn_on_slot.sh off $SLOT
    turn_on_slot.sh on $SLOT
    sleep 10
    turn_on_slot.sh on $SLOT
    sleep 1
    jtag_accpcie_salina clr $SLOT
    sleep 3
    stdbuf -i0 -o0 -e0 tclsh sal_snake.tcl $SLOT
    #script -f $ASIC_SRC/ip/cosim/tclsh/$fn -c "tclsh sal_snake.tcl $SLOT"
    #sync
    #num_fail=$(cat $ASIC_SRC/ip/cosim/tclsh/$fn | grep "SNAKE TEST FAILED" | wc | awk -F " " '{print $1}')
    #if [[ $num_fail -ne 0 ]]
    #then
    #    echo "Snake Iteration $idx failed"
        #exit 0
    #fi

#done

