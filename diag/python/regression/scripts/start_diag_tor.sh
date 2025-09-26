# !/bin/sh

# Set up environment
echo "-------------------"
echo "Preparing diag environment"
Lipari=$(cat /proc/cpuinfo | grep AuthenticAMD | wc -l)
if [[ $Lipari == "0" ]]
then
    echo "TAORMINA"
else
    echo "LIPARI"
fi
#mkdir -p /home/diag/
rm -r /home/diag
DIAG_HOME=/home/diag
DIAG_DIR=/home/diag/diag
ln -sf /fs/nos/home_diag $DIAG_HOME

echo "Untar ASIC lib"
asic_type=$(grep "ASIC_TYPE" $DIAG_DIR/python/regression/scripts/dft_profile_mtp | cut -d "=" -f 2)
asic=$(echo $asic_type | awk '{print tolower($0)}')
echo "ASIC: $asic"
if [[ $Lipari == "0" ]]
then
    ASIC_IMG=$DIAG_HOME/nic_amd64_${asic}_ftdi.tar.gz
else
    ASIC_IMG=$DIAG_HOME/nic_amd64_${asic}_lipari.tar.gz
fi
chmod -R 755 $DIAG_DIR/asic_all/$asic/
rm -rf  $DIAG_DIR/asic_all/$asic/*
tar xzf $ASIC_IMG -C $DIAG_DIR/asic_all/$asic/
cp -r $DIAG_DIR/asic_all/$asic/nic/* $DIAG_DIR/asic_all/$asic/
cp $DIAG_DIR/asic_all/$asic/asic_src/ip/cosim/tclsh/.git_rev.tcl $DIAG_DIR/asic_all/$asic/asic_version.txt
rm -rf $DIAG_DIR/asic_all/$asic/nic
sync;sync;sync

mkdir -p $DIAG_DIR/log/
rmmod ftdi_sio

# Prepare all paths
cp $DIAG_DIR/python/regression/scripts/profile_tor /home/root/.profile
source /home/root/.profile


#==================================
# Tcl configuration
ln -sf $DIAG_HOME/diag/asic_all/elba $DIAG_HOME/diag/asic

cp $DIAG_HOME/diag/scripts/taormina/tclsh8.6 $ASIC_SRC/ip/cosim/tclsh
cp $DIAG_HOME/diag/scripts/taormina/tclsh8.6 $ASIC_SRC/ip/cosim/tclsh/tclsh
cp $DIAG_DIR/scripts/asic/tclrc.diag.elb.taor.nointv $ASIC_SRC/ip/cosim/tclsh/.tclrc.diag.elb.taor.nointv

mkdir -p $DIAG_HOME/diag/asic/lib/
cp -r $DIAG_HOME/diag/scripts/taormina/tcl8.6 $DIAG_HOME/diag/asic/lib/

mkdir -p /usr/lib/x86_64-linux-gnu/
#cp $DIAG_HOME/diag/scripts/taormina/tcl8.6/libtclreadline.so /usr/lib/x86_64-linux-gnu/

mkdir -p $DIAG_DIR/asic/asic_src/tcl8.6.8/library/
cp $DIAG_DIR/asic/lib/tcl8.6/clock.tcl $DIAG_DIR/asic/asic_src/tcl8.6.8/library/
#cp $DIAG_DIR/asic/lib/tcl8.6/* $ASIC_SRC/ip/cosim/tclsh/

if [[ $Lipari == "0" ]]
then
    mkdir $DIAG_HOME/dssman
    tar xf $DIAG_HOME/diag/scripts/taormina/dssman56vlans.tar.gz -C $DIAG_HOME
fi
tar xf $DIAG_HOME/diag/scripts/taormina/tcl8.6_install.tar -C /
if [[ $Lipari != "0" ]]
then
    sed -i 's/.*package require -exact Tcl 8.6.8*/#package require -exact Tcl 8.6.8/' /usr/share/tcltk/tcl8.6/init.tcl
fi
cp $DIAG_HOME/diag/scripts/taormina/readline/x86_64-linux-gnu/* /usr/lib/x86_64-linux-gnu/
mkdir -p /usr/lib/tcltk/x86_64-linux-gnu
cp -r $DIAG_HOME/diag/scripts/taormina/readline/tcltk/x86_64-linux-gnu/* /usr/lib/tcltk/x86_64-linux-gnu/

#==================================
source $DIAG_DIR/python/infra/config/scripts/pre_dsp_tor

ASIC_DIR_TOP=$DIAG_DIR/asic_all
ASIC_DIR_SUB_TOP=$ASIC_DIR_TOP/elba

ASIC_LIB_BUNDLE=$DIAG_DIR/asic
rm -rf $ASIC_LIB_BUNDLE
ln -sf $ASIC_DIR_SUB_TOP $ASIC_LIB_BUNDLE


echo "Set up ASIC environment"
echo "export ASIC_LIB_BUNDLE=$ASIC_LIB_BUNDLE" >> temp_profile
echo "export ASIC_SRC=\$ASIC_LIB_BUNDLE/asic_src" >> temp_profile
echo "export ASIC_LIB=\$ASIC_LIB_BUNDLE/asic_lib" >> temp_profile
echo "export ASIC_GEN=\$ASIC_SRC" >> temp_profile
echo "source \$ASIC_LIB/source_env_path" >> temp_profile

hack_asic_elba.sh

mkdir -p $ASIC_SRC/ip/cosim/tclsh/images/

# Start redis if it is not running
redisFlag=$($DIAG_DIR/tools/redis-cli get DIAG_UP)
if [[ $redisFlag != "1" ]]
then
    $DIAG_DIR/tools/redis-server --daemonize yes
    # Wait for 1s for redis-server to get ready
    sleep 5s
    echo "Turning on diag engine"
    $DIAG_DIR/tools/redis-cli CONFIG SET protected-mode no
    $DIAG_DIR/tools/redis-cli -h $REDIS_IP set DIAG_UP 1
    echo "Diag engine turned on"
fi

# Flush all previous residues
$DIAG_DIR/tools/redis-cli -h $REDIS_IP FLUSHALL

# Load all the redis keys
cat $DIAG_DIR/python/infra/config/OUTPUT/* | $DIAG_DIR/tools/redis-cli -h $REDIS_IP &>/dev/null
echo "Redis keys loaded"

env | grep MTP_REV | awk -F "=" '{print $2}' > /home/diag/mtp_rev

# Duplicate 5 asic DSPs
cp $DIAG_DIR/dsp/asic $DIAG_DIR/dsp/asic1
cp $DIAG_DIR/dsp/asic $DIAG_DIR/dsp/asic2
cp $DIAG_DIR/dsp/asic $DIAG_DIR/dsp/asic3
cp $DIAG_DIR/dsp/asic $DIAG_DIR/dsp/asic4
cp $DIAG_DIR/dsp/asic $DIAG_DIR/dsp/asic5

echo "Preparing diag environment -- Done"
if [[ $Lipari == "0" ]]
then
    echo "Setting CXOS to no reboot and disble CXOS holding Elba consoles"
    ovs-appctl -t hpe-cardd park_chassis 1
    systemctl stop dsm-uart-log.path
    systemctl stop dsm-uart-log

    echo "Stopping netagent services"
    systemctl stop netagent.path
    systemctl stop netagent.service

    echo "Setting tmp451 to extended mode"
    /fs/nos/home_diag/diag/util/fpgautil i2c 2 1 0x4c w 0x09 0x4

    echo "Disabling Elba JTAG to external header"
    /fs/nos/home_diag/diag/util/fpgautil i2c 2 2 0x4a w 0x22 0xA0
    /fs/nos/home_diag/diag/util/fpgautil i2c 2 2 0x4a w 0x21 0x61
    /fs/nos/home_diag/diag/util/fpgautil i2c 2 3 0x4a w 0x22 0xA0
    /fs/nos/home_diag/diag/util/fpgautil i2c 2 3 0x4a w 0x21 0x61

    echo "Killing cxos monitoring processes"
    declare -a arr=("pmd" "hhmd" "tempd" "vrfmgrd" "fand" "powerd")
    for i in "${arr[@]}"
    do
        ps -A | grep $i > /dev/null
        if [ $? -eq 0 ]
        then
	        killall $i
        fi
    done

    echo "Stopping X86 and Elba Watchdog Timers"
    /fs/nos/home_diag/diag/util/fpgautil w32 1 0x500 0xD100FFFF
    /fs/nos/home_diag/diag/util/fpgautil w32 1 0x508 0xD100FFFF
    /fs/nos/home_diag/diag/util/fpgautil w32 1 0x510 0xD100FFFF

    echo "-------------------"
    echo "Set up diag $arch -- Done"
    echo "===================================="

    echo "Setting up fan controllers *"
    /fs/nos/home_diag/diag/util/fpgautil i2c 0 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 1 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 2 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 3 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 4 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 5 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 6 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 7 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 8 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 9 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 10 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 11 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 12 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 13 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 14 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 15 reset
    /fs/nos/home_diag/diag/util/fpgautil i2c 16 reset

    /fs/nos/home_diag/diag/util/devmgr -dev=fan_1 -faninit
    /fs/nos/home_diag/diag/util/devmgr -dev=fan_2 -faninit

    /fs/nos/home_diag/diag/util/fanutil 0 pwm 55 all
    /fs/nos/home_diag/diag/util/fanutil 1 pwm 55 all
    sleep 1
    /fs/nos/home_diag/diag/util/fanutil 0 pwm 60 all
    /fs/nos/home_diag/diag/util/fanutil 1 pwm 60 all
    sleep 1
    /fs/nos/home_diag/diag/util/fanutil 0 pwm 65 all
    /fs/nos/home_diag/diag/util/fanutil 1 pwm 65 all
    sleep 1
    /fs/nos/home_diag/diag/util/fanutil 0 pwm 70 all
    /fs/nos/home_diag/diag/util/fanutil 1 pwm 70 all
    sleep 1
    /fs/nos/home_diag/diag/util/fanutil 0 pwm 75 all
    /fs/nos/home_diag/diag/util/fanutil 1 pwm 75 all
else
    echo "Lipari startup code goes here (fan rpm, i2c reset, etc)"
fi


