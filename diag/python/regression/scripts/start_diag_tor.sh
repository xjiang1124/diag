# !/bin/sh

# Set up environment
echo "-------------------"
echo "Preparing diag environment"
#mkdir -p /home/diag/
rm -r /home/diag
DIAG_HOME=/home/diag
DIAG_DIR=/home/diag/diag
ln -sf /fs/nos/home_diag $DIAG_HOME

mkdir -p $DIAG_DIR/log/

# Prepare all paths
cp $DIAG_DIR/python/regression/scripts/profile_tor /home/root/.profile
source /home/root/.profile

rmmod ftdi_sio

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

tar xf $DIAG_HOME/diag/scripts/taormina/tcl8.6_install.tar -C /
cp $DIAG_HOME/diag/scripts/taormina/readline/x86_64-linux-gnu/* /usr/lib/x86_64-linux-gnu/
mkdir -p /usr/lib/tcltk/x86_64-linux-gnu
cp -r $DIAG_HOME/diag/scripts/taormina/readline/tcltk/x86_64-linux-gnu/* /usr/lib/tcltk/x86_64-linux-gnu/

#==================================
source $DIAG_DIR/python/infra/config/scripts/pre_dsp_tor

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

echo "Setting up fan controllers"
/fs/nos/home_diag/diag/util/devmgr -dev=fan_1 -faninit
/fs/nos/home_diag/diag/util/devmgr -dev=fan_2 -faninit

echo "Setting tmp451 to extended mode"
/fs/nos/home_diag/diag/util/fpgautil i2c 2 1 0x4c w 0x09 0x4

echo "-------------------"
echo "Set up diag $arch -- Done"
echo "===================================="

