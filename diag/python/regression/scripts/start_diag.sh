# !/bin/bash

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

# Set up environment
echo "-------------------"
echo "Preparing diag environment"
DIAG_DIR=/home/diag/diag

# Prepare all paths
cat $DIAG_DIR/python/regression/scripts/dft_profile > temp_profile
echo "" >> temp_profile
echo "# Diag set up" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/util/" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/dsp/" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/python/regression" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/python/infra" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/python/qa_suite" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/scripts" >> temp_profile
echo "PATH=\$PATH:$DIAG_DIR/tools" >> temp_profile

if [[ $arch == "arm64" ]]
then
    source $DIAG_DIR/python/infra/config/scripts/pre_dsp_nic1
else
    source $DIAG_DIR/python/infra/config/scripts/pre_dsp_mtp
    echo "source $DIAG_DIR/python/infra/config/scripts/pre_dsp_mtp" >> temp_profile
fi

cp temp_profile ~/.bash_profile
source ~/.bash_profile

if [[ $arch == "amd64" ]]
then
    envinit.py

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
    
    # Load all the redis keys
    cat $DIAG_DIR/python/infra/config/OUTPUT/* | $DIAG_DIR/tools/redis-cli -h $REDIS_IP &>/dev/null
    echo "Redis keys loaded"
fi

#echo "redisFlag $redisFlag"

echo "Preparing diag environment -- Done"

echo "-------------------"
echo "Set up diag $arch -- Done"
echo "===================================="

