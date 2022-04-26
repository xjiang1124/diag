# !/bin/bash

# Set up environment
echo "--------------------------"
echo "start running ddr bist"

if [[ ! -f /data/current_chan ]]; then
    echo "no current channel is specified, exit"
    exit 0
fi

fwenv -n gold
chan=$(cat /data/current_chan)
rm /data/current_chan
bist_parm=$(cat /data/ddrbist_config.txt)
echo "testing channel "$chan
vmarg=$(cat /data/ddrbist_vmarg.txt)
echo "testing channel "$chan $vmarg $bist_parm
/data/nic_arm/vmarg.sh $vmarg
cd /data/nic_arm/nic/asic_src/ip/cosim/tclsh
if [[ $chan -eq 0 ]];then
    echo "testing channel 0"
    ./diag.exe ../elba/elb_arm_ddr_bist.tcl $bist_parm 0 1 1
elif [[ $chan -eq 1 ]]; then
    echo "testing channel 1"
    ./diag.exe ../elba/elb_arm_ddr_bist.tcl $bist_parm 0 0 0
else
    echo "invalid channel number"
fi

if [[ -f /data/next_chan ]]; then
    chan=$(cat /data/next_chan)
    mv /data/next_chan /data/current_chan
    touch /data/ddrbist_run_valid
    fwenv -n gold -s noc_llc_pin $chan
    fwenv -n gold
    sysreset.sh
    # in case sysreset not kicked in fast enough
    sleep 1
fi

rm /data/ddrbist_config.txt
rm /data/ddrbist_vmarg.txt
rm /data/pensando_pre_init.sh
fwenv -n gold -E
fwenv -n gold
echo "DDR BIST FINISHED"
