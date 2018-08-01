# !/bin/bash

# Set quit on error
set -e

if [[ $# -eq 0 ]]
then
    arch=amd64
else
    if [[ $1 == "arm" || $1 == "arm64" ]]
    then
        arch=arm64
    else
        arch=amd64
    fi
fi

echo "============================================"
echo "Start packaging Diag environment for $arch"

BUILD_DIR=$(pwd)
TOP_DIR=$(dirname $BUILD_DIR)

TEMP_DIR=$BUILD_DIR/temp/$arch/diag/
IMG_DIR=$BUILD_DIR/images/

# In case images/ folder is not created yet for new repo
mkdir -p images/

# Prepare all folders
mkdir -p $TEMP_DIR
mkdir -p $TEMP_DIR/dsp
mkdir -p $TEMP_DIR/util
mkdir -p $TEMP_DIR/dshell
mkdir -p $TEMP_DIR/config
mkdir -p $TEMP_DIR/config/redis/
mkdir -p $TEMP_DIR/scripts
mkdir -p $TEMP_DIR/regression
mkdir -p $TEMP_DIR/tools

# Prepare files
cd $TOP_DIR/diag/python/infra/config/
./parseYaml.py

# Copy all the files needed
echo "--------------------"
echo "Copying all files"
cd $BUILD_DIR
cp -r $TOP_DIR/diag/app/bin/linux_$arch/diagmgr $TEMP_DIR/
cp -r $TOP_DIR/diag/app/bin/linux_$arch/dsp/ $TEMP_DIR/
cp -r $TOP_DIR/diag/app/bin/linux_$arch/util/ $TEMP_DIR/
[ "$(ls -A $TOP_DIR/diag/app/bin/linux_$arch/cbin)" ] && cp -r $TOP_DIR/diag/app/bin/linux_$arch/cbin/* $TEMP_DIR/util/
cp -r -L $TOP_DIR/diag/scripts/$arch/* $TEMP_DIR/scripts
cp $TOP_DIR/diag/scripts/*sh $TEMP_DIR/scripts/
cp $TOP_DIR/diag/scripts/version* $TEMP_DIR/scripts/

cp -r $TOP_DIR/diag/python/ $TEMP_DIR/
cp -r $TOP_DIR/diag/python/regression/scripts/start_diag.sh $TEMP_DIR/..

cp -r $TOP_DIR/tools/bin/$arch/* $TEMP_DIR/tools/

# Version
git log --name-status HEAD^..HEAD > $TEMP_DIR/scripts/version.txt
git status >> $TEMP_DIR/scripts/version.txt

# ARM specified files

echo "Copying all files -- Done"

# Prepare image
echo "--------------------"
echo "Preparing image"
cd $BUILD_DIR/temp/$arch
tar czf $IMG_DIR/image_$arch.tar *

echo "Preparing image -- Done"

echo "--------------------"
echo "Cleaning up"
rm -rf $BUILD_DIR/temp/$arch
echo "Clean up -- Done"

echo "--------------------"
echo "Done packaging $arch"
echo "============================================"
