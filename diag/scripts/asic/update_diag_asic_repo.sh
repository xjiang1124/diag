# !/bin/bash

# ASIC repo need to be pulled and compiled before running this script

DIAG_REPO="/vol/hw/diag/diag_repo/asic/amd64"
ASIC_REPO="/home/xguo2/workspace/asic/"
ASIC_GEN="/vol/dump/xguo2/workspace/asic"

cd $DIAG_REPO
cp -rf $ASIC_GEN/ip/cosim/diag/nic/* .

cd $ASIC_REPO
gitVer=$(git log --name-status HEAD^..HEAD > $DIAG_REPO/asic_version.txt.temp)
echo -e "\n-----------------\n" >> $DIAG_REPO/asic_version.txt.temp
mv $DIAG_REPO/asic_version.txt $DIAG_REPO/asic_version.txt.temp1
cat $DIAG_REPO/asic_version.txt.temp $DIAG_REPO/asic_version.txt.temp > $DIAG_REPO/asic_version.txt
cat $DIAG_REPO/asic_version.txt
