# !/bin/bash

# Set up environment
echo "-----------------------------"
echo "checking uboot permission"
permit=$(fwenv -n gold)
if [[ ${permit} != *"run_ddrbist_ok=1"* ]];then
    echo "uboot setting is not allowing to run automated ddr bist"
    exit 0
fi
echo "Preparing diag environment"
mount /dev/mmcblk0p10 /data
source /data/nic_arm/nic_setup_env.sh
source /etc/profile

if [[ ! -f /data/ddrbist_run_valid ]]; then
    echo "no valid flag is set to run ddr bist! exit ..."
    exit 0
fi

echo "found the flag to run ddr bist"
rm /data/ddrbist_run_valid
run_ddrbist_arm.sh
