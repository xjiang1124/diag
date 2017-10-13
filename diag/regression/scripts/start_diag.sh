# !/bin/bash

if [[ $# -eq 0 ]]
then
    arch=x86_64
else
    if [[ $1 == "arm" || $1 == "arm64" ]]
    then
        arch=arm
    else
        arch=x86_64
    fi
fi

echo "===================================="
echo "Setting up diag $arch"

# Extract files
echo "-------------------"
echo "Extracting files"
rm -rf diag/
tar xzf image_$arch.tar
mv x86_64/ diag/
echo "Extracting files -- Done"

# Set up environment
echo "-------------------"
echo "Preparing diag environment"
DIAG_DIR=$(pwd)/diag

# Prepare all paths
cat $DIAG_DIR/regression/scripts/dft_profile > temp_profile
echo "" >> temp_profile
echo "# Diag set up" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/regression" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/dshell" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/scripts" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/tools" >> temp_profile

if [[ $arch == "arm" ]]
then
    source $DIAG_DIR/scripts/pre_dsp_nic1
else
    source $DIAG_DIR/scripts/pre_dsp_host
    echo "source $DIAG_DIR/scripts/pre_dsp_host" >> temp_profile
fi

cp temp_profile ~/.bash_profile
source ~/.bash_profile

# Start redis if it is not running
redisFlag=$($DIAG_DIR/tools/redis-cli get DIAG_UP)
if [[ $redisFlag != "1" ]]
then
    $DIAG_DIR/tools/redis-server --daemonize yes
    echo "Diag engine turned on"
    redis-cli -h $REDIS_IP set DIAG_UP 1
fi
echo "redisFlag $redisFlag"

echo "Preparing diag environment -- Done"

echo "-------------------"
echo "Set up diag $arch -- Done"
echo "===================================="

