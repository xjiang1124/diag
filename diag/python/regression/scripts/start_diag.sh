# !/bin/bash

if [[ $# -eq 0 ]]
then
    arch=amd64
else
    if [[ $1 == "arm" || $1 == "arm64" ]]
    then
        arch=arm64
        slot=$2
    else
        arch=amd64
        if [[ $1 == "skip_untar" ]]
        then
            skip_untar=1
        fi
    fi
fi

# Set up environment
echo "-------------------"
echo "Checking if FPGA is present"
num_fpga=$(lspci | grep "Pensando Systems" | wc | awk -F " " '{print $1}')
echo "num_fpga: $num_fpga"
FPGA_PRST="YES"
if [[ $num_fpga -ne 0 ]]
then
    echo "FPGA found"
    setpci -s 1:0.0 command.l=0x100006
else
    echo "Legacy MTP found"
    FPGA_PRST="NO"
fi

echo "-------------------"
echo "Preparing diag environment"
DIAG_DIR=/home/diag/diag

asic_type=$(grep "ASIC_TYPE" $DIAG_DIR/python/regression/scripts/dft_profile_mtp | cut -d "=" -f 2)
asic=$(echo $asic_type | awk '{print tolower($0)}')
echo "ASIC: $asic"

if [[ $FPGA_PRST == "YES" ]]
then
    ASIC_IMG=/home/diag/nic_amd64_${asic}_fpga.tar.gz
else
    ASIC_IMG=/home/diag/nic_amd64_${asic}_ftdi.tar.gz
fi

if [[ -n $skip_untar ]]
then
    echo "Using existing ASIC lib"
else
    if [[ $asic != "vulcano" ]]
    then
        echo "Untar ASIC lib"
        chmod -R 755 $DIAG_DIR/asic_all/$asic/
        rm -rf  $DIAG_DIR/asic_all/$asic/*
        tar xzf $ASIC_IMG -C $DIAG_DIR/asic_all/$asic/
        cp -r $DIAG_DIR/asic_all/$asic/nic/* $DIAG_DIR/asic_all/$asic/
        cp $DIAG_DIR/asic_all/$asic/asic_src/ip/cosim/tclsh/.git_rev.tcl $DIAG_DIR/asic_all/$asic/asic_version.txt
        rm -rf $DIAG_DIR/asic_all/$asic/nic
    fi
fi

mkdir -p $DIAG_DIR/log/

if [ -f "$DIAG_DIR/log/board_env.txt" ]; then
    echo "board_env.txt exist, removing it"
    rm $DIAG_DIR/log/board_env.txt
fi

# Prepare all paths
if [[ $arch == "amd64" ]]
then
    cat $DIAG_DIR/python/regression/scripts/dft_profile_mtp > temp_profile
    if [[ $FPGA_PRST == "YES" ]]
    then
        if [[ $asic == "salina" ]]
        then
            export MTP_TYPE=MTP_MATERA
            export CARD_TYPE=MTP_MATERA
        else
            export MTP_TYPE=MTP_PANAREA
            export CARD_TYPE=MTP_PANAREA
        fi
        export UUT_1="UUT_NONE"
        export UUT_2="UUT_NONE"
        export UUT_3="UUT_NONE"
        export UUT_4="UUT_NONE"
        export UUT_5="UUT_NONE"
        export UUT_6="UUT_NONE"
        export UUT_7="UUT_NONE"
        export UUT_8="UUT_NONE"
        export UUT_9="UUT_NONE"
        export UUT_10="UUT_NONE"
        export PATH=$PATH:$DIAG_DIR/util
        cp /home/diag/diag/python/regression/scripts/dft_bashrc /etc/skel/.bashrc
        cp /home/diag/diag/python/regression/scripts/dft_bashrc /home/diag/.bashrc
        cp /home/diag/diag/python/regression/scripts/dft_bashrc /etc/bash.bashrc
        if [[ $asic == "salina" ]]
        then
            /home/diag/diag/python/regression/envinit_matera.py
        else
            /home/diag/diag/python/regression/envinit_panarea.py
        fi
    else 
        /home/diag/diag/python/regression/envinit.py
    fi
    /home/diag/diag/scripts/turn_on_slot.sh on all
    /home/diag/diag/util/inventory -env
    cat $DIAG_DIR/log/board_env.txt >> temp_profile
    echo "export DIAG_HOME=/home/diag/" >> temp_profile
    for i in $(seq 1 10);
    do
        UUT_TYPE=$(cat $DIAG_DIR/log/board_env.txt | grep "UUT_$i=" | cut -d "\"" -f 2)
        if [[ $UUT_TYPE == "UUT_NONE" ]]
        then
            echo "Turning off empty slot $i"
            /home/diag/diag/scripts/turn_on_slot.sh off $i
        fi
    done
else
    cat $DIAG_DIR/python/regression/scripts/dft_profile_nic > temp_profile
fi

echo "-------------------"

echo "" >> temp_profile
echo "# Diag set up" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/util/" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/dsp/" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/python/regression" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/python/infra" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/python/infra/dshell" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/python/qa_suite" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/scripts" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/scripts/asic" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/tools" >> temp_profile

if [[ $FPGA_PRST == "YES" ]]
then
    mtp_id_str=$(sudo -SE <<< "lab123" /home/diag/diag/util/fpgautil r32 0 0)
    mtp_id_str1=$(echo "$mtp_id_str" | cut -b 15-20)
    mtp_id="${mtp_id_str1:0:6}"
    echo "mtp_id_str: $mtp_id_str; mtp_id_str1: $mtp_id_str1; mtp_id: $mtp_id"
    echo "setting fan PWM to 40%"
    /home/diag/diag/util/fanutil 0 pwm 40 all
    
else
    mtp_id_str=$(/home/diag/diag/util/cpldutil -cpld-rd -addr=0x80)
    mtp_id_str1=($mtp_id_str)
    mtp_id=${mtp_id_str1[-1]}
    #echo "mtp_id: $mtp_id"
fi

#==================================
ASIC_DIR_TOP=$DIAG_DIR/asic_all

ftdicnt=$(awk '{for (I=1;I<NF;I++) if ($I == "FTDI_DEVICE_COUNT") print$(I+1)}' temp_profile)
#echo "ftdicnt: $ftdicnt"

MEM_SIZE=$(awk 'NR==1 {if (length($2) == 7) print ($2 ~ /^[78]/) ? "8G" : "4G" }' /proc/meminfo)
echo "export MEM_SIZE="$MEM_SIZE >> temp_profile

if [[ $mtp_id == "0x42" || $mtp_id == "0x4d" ]]
then
    if [[ $ftdicnt -eq 1 ]]; then
        echo "ELBA MTP"
        echo "export MTP_TYPE=MTP_ELBA" >> temp_profile
    else
        echo "TURBO ELBA MTP"
        echo "export MTP_TYPE=MTP_TURBO_ELBA" >> temp_profile
    fi
    ASIC_DIR_SUB_TOP=$ASIC_DIR_TOP/elba
elif [[ $mtp_id == "0x2" ]]
then
    echo "CAPRI MTP"
    echo "export MTP_TYPE=MTP_CAPRI" >> temp_profile
    ASIC_DIR_SUB_TOP=$ASIC_DIR_TOP/capri
elif [[ $mtp_id == "0x000b" ]]
then
    echo "Matera  MTP"
    echo "export MTP_TYPE=MTP_MATERA" >> temp_profile
    ASIC_DIR_SUB_TOP=$ASIC_DIR_TOP/${asic_type,,}
elif [[ $mtp_id == "0x000c" ]]
then
    echo "Panarea  MTP"
    echo "export MTP_TYPE=MTP_PANAREA" >> temp_profile
    ASIC_DIR_SUB_TOP=$ASIC_DIR_TOP/${asic_type,,}
else
    echo "Default MTP to Capri"
    echo "export MTP_TYPE=MTP_CAPRI" >> temp_profile
    ASIC_DIR_SUB_TOP=$ASIC_DIR_TOP/capri
fi

ASIC_LIB_BUNDLE=$DIAG_DIR/asic
rm -rf $ASIC_LIB_BUNDLE
ln -sf $ASIC_DIR_SUB_TOP $ASIC_LIB_BUNDLE

echo "Set up ASIC environment"
echo "export ASIC_LIB_BUNDLE=$ASIC_LIB_BUNDLE" >> temp_profile
echo "export ASIC_SRC=\$ASIC_LIB_BUNDLE/asic_src" >> temp_profile
echo "export ASIC_LIB=\$ASIC_LIB_BUNDLE/asic_lib" >> temp_profile
echo "export ASIC_GEN=\$ASIC_SRC" >> temp_profile
echo "source \$ASIC_LIB/source_env_path" >> temp_profile

#==================================
if [[ $mtp_id == "0x000b" ]]
then
    echo "export CARD_TYPE=MTP_MATERA" >> temp_profile
    echo "export REDIS_IP=127.0.0.1" >> temp_profile
    export REDIS_IP="127.0.0.1"
elif [[ $mtp_id == "0x000c" ]]
then
    echo "export CARD_TYPE=MTP_PANAREA" >> temp_profile
    echo "export REDIS_IP=127.0.0.1" >> temp_profile
    export REDIS_IP="127.0.0.1"
else
    source $DIAG_DIR/python/infra/config/scripts/pre_dsp_mtp
    echo "source $DIAG_DIR/python/infra/config/scripts/pre_dsp_mtp" >> temp_profile
fi


cp temp_profile ~/.bash_profile
source ~/.bash_profile
if [[ $mtp_id == "0x42" || $mtp_id == "0x4d" || $mtp_id == "0x000b" || $mtp_id == "0x000c" ]]
then
    hack_asic_elba.sh
else
    hack_asic.sh
fi
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

# ESEC images
cp -r $DIAG_DIR/python/esec/images/ $ASIC_SRC/ip/cosim/tclsh/

# Duplicate 5 asic DSPs
cp $DIAG_DIR/dsp/asic $DIAG_DIR/dsp/asic1
cp $DIAG_DIR/dsp/asic $DIAG_DIR/dsp/asic2
cp $DIAG_DIR/dsp/asic $DIAG_DIR/dsp/asic3
cp $DIAG_DIR/dsp/asic $DIAG_DIR/dsp/asic4
cp $DIAG_DIR/dsp/asic $DIAG_DIR/dsp/asic5

env | grep MTP_REV | awk -F "=" '{print $2}' > /home/diag/mtp_rev

#echo "redisFlag $redisFlag"

echo "Preparing diag environment -- Done"

echo "-------------------"
echo "Set up diag $arch -- Done"
echo "===================================="

