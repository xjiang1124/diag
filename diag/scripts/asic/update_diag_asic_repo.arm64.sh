# !/bin/bash

# ASIC repo need to be pulled and compiled before running this script

DIAG_REPO="/vol/hw/diag/diag_repo/asic/arm64"
ASIC_REPO="/home/xguo2/workspace/asic/"
ASIC_GEN="/vol/dump/xguo2/workspace/asic_arm64"

cd $DIAG_REPO
rsync -rd $ASIC_GEN/ip/cosim/diag/nic/fake_root_target/nic/asic_lib/ asic_lib/
rsync -rd $ASIC_GEN/ip/cosim/diag/nic/fake_root_target/nic/asic_src/ asic_src/
rsync -rd $ASIC_GEN/ip/cosim/diag/nic/fake_root_target/nic/depend_libs/ depend_libs/
rsync -rd $ASIC_GEN/ip/cosim/diag/nic/fake_root_target/nic/lib/ lib/

cd $ASIC_REPO
gitVer=$(git log --name-status HEAD^..HEAD 2>&1 | head -n 6 > $DIAG_REPO/asic_version.txt.temp)
echo -e "\n-----------------\n" >> $DIAG_REPO/asic_version.txt.temp
mv $DIAG_REPO/asic_version.txt $DIAG_REPO/asic_version.txt.temp1
cat $DIAG_REPO/asic_version.txt.temp $DIAG_REPO/asic_version.txt.temp1 > $DIAG_REPO/asic_version.txt
cat $DIAG_REPO/asic_version.txt
