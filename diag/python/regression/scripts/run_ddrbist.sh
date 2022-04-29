# !/bin/bash

# Set up environment
echo "------------------------------------"
echo "Preparing diag environment"
source /data/nic_arm/nic_setup_env.sh
source /etc/profile

echo "checking uboot permission"
fwenv -n gold | grep "run_ddrbist_ok=1"
if [ $? = 1 ];then
    echo "uboot setting is not allowing to run automated ddr bist"
    exit 0
fi

if [[ ! -f /data/ddrbist_run_valid ]]; then
    echo "no valid flag is set to run ddr bist! exit ..."
    exit 0
fi

echo "found the flash to run ddr bist"
rm /data/ddrbist_run_valid
echo "RUNNING" > /data/ddrbist_status
/data/nic_util/run_ddrbist_arm.sh
echo "FINISHED" > /data/ddrbist_status
