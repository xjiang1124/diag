#!/bin/bash

echo $CARD_TYPE
if [[ $CARD_TYPE == "FORIO" ]] 
then
    ./diag.exe prbs.e.a.forio.tcl
elif [[ $CARD_TYPE == "ORTANO"      || \
        $CARD_TYPE == "ORTANO2"     || \
        $CARD_TYPE == "LACONA32"    || \
        $CARD_TYPE == "LACONA32DELL"|| \
        $CARD_TYPE == "POMONTE"     || \
        $CARD_TYPE == "POMONTEDELL" ]] 
then
    killall hal
    cd /data/nic_arm/elba/asic_src/ip/cosim/tclsh
    if [[ $1 == "PCIE" ]]
    then
        ./diag.exe ../elba/elb_arm_pcie_prbs.tcl $2
    elif [[ $1 == "ETH" ]] 
    then
        ./diag.exe ../elba/elb_arm_mx_prbs.tcl $2 0
    else
	echo "INVALID MODE" $1
    fi
else
    ./diag.exe prbs.e.a.tcl
fi
