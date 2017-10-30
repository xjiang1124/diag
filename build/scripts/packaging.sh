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

TEMP_DIR=$BUILD_DIR/temp/$arch
IMG_DIR=$BUILD_DIR/images/

# Prepare all folders
mkdir -p temp/$arch
mkdir -p temp/$arch/dsp
mkdir -p temp/$arch/util
mkdir -p temp/$arch/dshell
mkdir -p temp/$arch/config
mkdir -p temp/$arch/config/redis/
mkdir -p temp/$arch/scripts
mkdir -p temp/$arch/regression
mkdir -p temp/$arch/tools

mkdir -p images/

# Prepare files
cd $TOP_DIR/diag/infra/config/
./parseYaml.py

# Copy all the files needed
echo "--------------------"
echo "Copying all files"
cd $BUILD_DIR
cp -r $TOP_DIR/diag/app/bin/linux_$arch/dsp/ $TEMP_DIR/
cp -r $TOP_DIR/diag/app/bin/linux_$arch/util/ $TEMP_DIR/

cp -r $TOP_DIR/diag/infra/dshell/ $TEMP_DIR/
cp -r $TOP_DIR/diag/infra/config/OUTPUT/*redis $TEMP_DIR/config/redis/
cp -r $TOP_DIR/diag/infra/config/scripts/* $TEMP_DIR/scripts/

cp -r $TOP_DIR/diag/regression/ $TEMP_DIR/

cp -r $TOP_DIR/tools/bin/$arch/* $TEMP_DIR/tools/
echo "Copying all files -- Done"

# Prepare image
echo "--------------------"
echo "Preparing image"
cd $BUILD_DIR/temp
tar czf $IMG_DIR/image_$arch.tar $arch/

echo "Preparing image -- Done"

echo "--------------------"
echo "Cleaning up"
rm -rf $TEMP_DIR
echo "Clean up -- Done"

echo "--------------------"
echo "Done packaging $arch"
echo "============================================"
