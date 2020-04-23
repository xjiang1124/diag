# !/bin/bash

if [[ $# -ne 1 ]]
then
    echo "Invalid number of argument"
    exit 0
fi

uut=$1
turn_on_hub.sh $1

uut_type=$(env|grep UUT_$uut)
if [[ $uut_type != *"NAPLES25SWM"* ]]
then
    echo "Not a SWM, no need to turn off SGMII"
fi

phy=0x10
# Read status
adaptor_mdio_rd.sh $phy 0
# Disable port -- seems not working
adaptor_mdio_wr.sh $phy 4 0x7C
# Force link down
adaptor_mdio_wr.sh $phy 1 0x13
# Read status
adaptor_mdio_rd.sh $phy 0

echo "SGMII on SWM adaptor card is disabled"

