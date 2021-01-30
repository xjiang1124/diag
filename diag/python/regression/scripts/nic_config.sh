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

cpld_id="$(xo3dcpld -r 0x80)"
if [[ $cpld_id == "0x0" ]]
then
    echo "Capri CPLD"
    cpld_id="$(cpld -r 0x80)"
else
    echo "Elba CPLD"
fi

echo "P0: cpld_id $cpld_id"
cpld_id="${cpld_id}"
echo "P1: cpld_id $cpld_id"

cpld -w 0x1 0x2   #Capri Bleed Enable

if [[ $cpld_id == "0x12" ]]
then
    type="NAPLES100"
elif [[ $cpld_id == "0x13" ]]
then
    type="NAPLES25"
elif [[ $cpld_id == "0x14" ]]
then
    type="FORIO"
elif [[ $cpld_id == "0x15" ]]
then
    type="VOMERO"
elif [[ $cpld_id == "0x1e" ]]
then
    type="VOMERO2"
elif [[ $cpld_id == "0x17" ]]
then
    type="NAPLES25SWM"
    CORECLK417MHZ=1
elif [[ $cpld_id == "0x19" ]]
then
    type="NAPLES25OCP"
    CORECLK417MHZ=1
elif [[ $cpld_id == "0x1c" ]]
then
    type="NAPLES100IBM"
elif [[ $cpld_id == "0x1e" ]]
then
    type="VOMERO2"
elif [[ $cpld_id == "0x1f" ]]
then
    type="NAPLES100HPE"
elif [[ $cpld_id == "0x20" ]]
then
    type="NAPLES25SWMDELL"
    CORECLK417MHZ=1
elif [[ $cpld_id == "0x40" ]]
then
    type="BIODONA_D4"
elif [[ $cpld_id == "0x41" ]]
then
    type="BIODONA_D5"
elif [[ $cpld_id == "0x43" ]]
then
    type="ORTANO"
elif [[ $cpld_id == "0x44" ]]
then
    type="ORTANO2"
fi

echo "$type Detected!"
echo "export CARD_TYPE=\"$type\"" >> /etc/profile
export CARD_TYPE=$type
export CARD_ENV="ARM"

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



echo "nic_config done"

