do_untar=1
if [[ $# -ne 0 ]]
then
    if [[ $1 == "0" ]]
    then
        do_untar=0
    fi
fi

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
if [[ $cpld_id == "0x0" ]]
then
    cpld_id="$(cpld -r 0x80)"
fi

echo "P0: cpld_id $cpld_id"
cpld_id="${cpld_id}"
echo "P1: cpld_id $cpld_id"

cpld -w 0x1 0x2   #Capri Bleed Enable

if [[ $cpld_id == "0x12" ]]
then
    type="NAPLES100"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x13" ]]
then
    type="NAPLES25"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x14" ]]
then
    type="FORIO"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x15" ]]
then
    type="VOMERO"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x1e" ]]
then
    type="VOMERO2"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x17" ]]
then
    type="NAPLES25SWM"
    CORECLK417MHZ=1
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x19" ]]
then
    type="NAPLES25OCP"
    CORECLK417MHZ=1
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x1c" ]]
then
    type="NAPLES100IBM"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x1e" ]]
then
    type="VOMERO2"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x1f" ]]
then
    type="NAPLES100HPE"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x22" ]]
then
    type="NAPLES100DELL"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x20" ]]
then
    type="NAPLES25SWMDELL"
    CORECLK417MHZ=1
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x21" ]]
then
    type="NAPLES25SWM833"
    CORECLK833MHZ=1
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x40" ]]
then
    type="BIODONA_D4"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x41" ]]
then
    type="BIODONA_D5"
    asic_type="CAPRI"
    echo "Capri CPLD"
elif [[ $cpld_id == "0x43" ]]
then
    type="ORTANO"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x44" ]]
then
    type="ORTANO2"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x45" ]]
then
    type="LACONADELL"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x46" ]]
then
    type="LACONA"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x47" ]]
then
    type="POMONTEDELL"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x48" ]]
then
    type="POMONTE"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x49" ]]
then
    type="LACONA32DELL"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x4a" ]]
then
    type="LACONA32"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x4b" ]]
then
    type="ORTANO2A"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x4c" ]]
then
    itp_type="$(xo3dcpld -r 0x93)"
    type="ORTANO2I"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x4e" ]]
then
    itp_type="$(xo3dcpld -r 0x99)"
    type="ORTANO2S"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x50" ]]
then
    type="ORTANO2AC"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x60" ]]
then
    type="GINESTRA_D4"
    asic_type="GIGLIO"
    echo "Giglio CPLD"
elif [[ $cpld_id == "0x61" ]]
then
    type="GINESTRA_D5"
    asic_type="GIGLIO"
    echo "Giglio CPLD"
elif [[ $cpld_id == "0x62" ]]
then
    type="MALFA"
    asic_type="SALINA"
    echo "Salina CPLD"
elif [[ $cpld_id == "0x64" ]]
then
    type="LENI"
    asic_type="SALINA"
    echo "Salina CPLD"
elif [[ $cpld_id == "0x65" ]]
then
    type="POLLARA"
    asic_type="SALINA"
    echo "Salina CPLD"
elif [[ $cpld_id == "0x66" ]]
then
    type="LENI48G"
    asic_type="SALINA"
    echo "Salina CPLD"
elif [[ $cpld_id == "0x67" ]]
then
    type="LINGUA"
    asic_type="SALINA"
    echo "Salina CPLD"
elif [[ $cpld_id == "0x81" ]]
then
    type="LIPARI"
    asic_type="ELBA"
    echo "Elba CPLD"
elif [[ $cpld_id == "0x82" ]]
then
    type="MTFUJI"
    asic_type="ELBA"
    echo "Elba CPLD"
else
    type="UNKNOW"
    asic_type="UNKNOW"
    echo "Unknown CPLD"
fi

echo "$type Detected!"
echo "export CARD_TYPE=\"$type\"" >> /etc/profile
echo "export ITP_TYPE=\"$itp_type\"" >> /etc/profile
echo "export ASIC_TYPE=\"$asic_type\"" >> /etc/profile
echo "export CARD_ENV=\"ARM\"" >> /etc/profile
export CARD_TYPE=$type
export ITP_TYPE=$itp_type
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

#This piece of code is a bit odd.. it cannot be indented so need to run it outside an if statement
#DO NOT INDENT CODE IN THE IF STATEMENT
#DO NOT INDENT CODE IN THE IF STATEMENT
if [[ $CORECLK417MHZ -eq 1 ]]
then

echo "Setting Core Clock to 417Mhz"
/platform/bin/capview << EOF
secure on
fset ms_cfg_clk__S pll_select_core=0x5
EOF

fi

if [[ $CORECLK833MHZ -eq 1 ]]
then

echo "Setting Core Clock to 833Mhz"
/platform/bin/capview << EOF
secure on
fset ms_cfg_clk__S pll_select_core=0x0
EOF

fi

if [[ $type == "ORTANO2A" ]]
then
    echo "i2cset -f -y 0 0x4c 0x19 0x7d"
    i2cset -f -y 0 0x4c 0x19 0x7d
    reg12=$(/data/nic_util/xo3dcpld -r 0x12)
    reg12=$(( $reg12 | 0x40 ))
    /data/nic_util/xo3dcpld -w 0x12 $reg12 
fi

# WA for the logic SW added for NCSI where it doesn’t send unicast packets until BMC MAC is registered
cd /nic/conf/
find . -name "catalog*.json" | xargs sed -i 's/"num_local_passthru_channel": 1/"num_local_passthru_channel": 0/g'

cd /data/nic_util/
tar xf edma_test.tar.gz
echo "EDMA setup done"
if [[ $do_untar == "1" ]]
then
    if [[ $asic_type != "UNKNOW" ]]
    then
        if [[ $asic_type == "ELBA" ]]
        then
            ARM_ASIC_PATH=$NIC_ARM_DIR/elba
        elif [[ $asic_type == "GIGLIO" ]]
        then
            ARM_ASIC_PATH=$NIC_ARM_DIR/giglio
        elif [[ $asic_type == "SALINA" ]]
        then
            ARM_ASIC_PATH=$NIC_ARM_DIR/salina
        else
            ARM_ASIC_PATH=$NIC_ARM_DIR/capri
        fi
        echo "Copy scripts to nic_arm"
        ASIC_IMG=/data/nic.tar.gz
        tar xf $ASIC_IMG -C /data
        sync;sync;sync
        cp -r /data/nic/fake_root_target/nic/* $ARM_ASIC_PATH
        cp -r /data/nic/fake_root_target/nic/asic_src/ip/cosim/tclsh/.git_rev.tcl $ARM_ASIC_PATH/asic_version.txt
        rm -rf /data/nic/
        sync;sync;sync
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
        sync;sync;sync
    fi
else
    echo "Using existing ASIC lib"
fi


echo "nic_config done"

