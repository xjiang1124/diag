# !/bin/bash

# ASIC repo need to be pulled and compiled before running this script

ASIC_TYPE=$1
ARCH=$2

ASIC_TYPE=${ASIC_TYPE,,}
ARCH=${ARCH,,}

ASIC_REPO="/home/$USER/workspace/asic/"
ASIC_TMP="/home/$USER/workspace/temp/"

#DIAG_REPO_TOP="/vol/hw/diag/diag_repo/asic.2020.02.10/"
DIAG_REPO_TOP="/vol/hw/diag/diag_repo/asic/"
DIAG_REPO_TOP="/vol/hw/diag/diag_repo/asic.2021.03.30/"

if [[ $ASIC_TYPE == "capri" ]]
then
    if [[ $ARCH == "amd64" ]]
    then
        DIAG_REPO="$DIAG_REPO_TOP/$ASIC_TYPE/$ARCH/"
        #ASIC_GEN="/vol/dump/$USER/workspace/asic/ip/cosim/diag/nic/"
        ASIC_IMG="/vol/dump/$USER/workspace/capri_amd64/ip/cosim/diag/nic.tar.gz"
        ASIC_TMP_NIC=$ASIC_TMP/nic
    else
        #DIAG_REPO="/vol/hw/diag/diag_repo/asic/capri/arm64"
        DIAG_REPO="$DIAG_REPO_TOP/$ASIC_TYPE/$ARCH/"
        #ASIC_GEN="/vol/dump/$USER/workspace/asic/ip/cosim/diag/nic/fake_root_target/nic/"
        ASIC_IMG="/vol/dump/$USER/workspace/capri_arm64/ip/cosim/diag/nic.tar.gz"
        ASIC_TMP_NIC=$ASIC_TMP/nic/fake_root_target/nic/
    fi
else
    if [[ $ARCH == "amd64" ]]
    then
        DIAG_REPO="$DIAG_REPO_TOP/$ASIC_TYPE/$ARCH/"
        #DIAG_REPO="/vol/hw/diag/diag_repo/asic/elba/amd64/"
        #ASIC_GEN="/vol/dump/$USER/workspace/asic/ip/cosim/diag/nic/"
        ASIC_IMG="/vol/dump/$USER/workspace/elba_amd64/ip/cosim/diag_elb/nic.tar.gz"
        ASIC_TMP_NIC=$ASIC_TMP/nic
    else
        DIAG_REPO="$DIAG_REPO_TOP/$ASIC_TYPE/$ARCH/"
        #DIAG_REPO="/vol/hw/diag/diag_repo/asic/elba/arm64"
        #ASIC_GEN="/vol/dump/$USER/workspace/asic/ip/cosim/diag/nic/fake_root_target/nic/"
        ASIC_IMG="/vol/dump/$USER/workspace/elba_arm64/ip/cosim/diag_elb/nic.tar.gz"
        ASIC_TMP_NIC=$ASIC_TMP/nic/fake_root_target/nic/
    fi
fi

mkdir -p $DIAG_REPO

echo "DIAG_REPO: $DIAG_REPO"
echo "ASIC_IMG: $ASIC_IMG"

rm -rf $ASIC_TMP/nic
cd $ASIC_TMP
tar xf $ASIC_IMG

cd $DIAG_REPO
cp -r $ASIC_TMP_NIC/* .

cd $ASIC_REPO
gitVer=$(git log --name-status HEAD^..HEAD 2>&1 | head -n 6 > $DIAG_REPO/asic_version.txt)

rm -rf $ASIC_TMP/nic
