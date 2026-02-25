# !/bin/bash

# Based on https://amd.atlassian.net/wiki/spaces/HD/pages/1159227876/Diagnostic+Manufactory+Release

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <card name> <release version>"
    exit 1
fi

# Covert to upper case
product=$(echo "$1" | tr '[:lower:]' '[:upper:]')

case "$product" in
    GELSO)
        major=2
        minor=0
        ;;
    SARACENO)
        major=2
        minor=1
        ;;
    MORTARO)
        major=2
        minor=2
        ;;
    *)
        echo "Invalid product name: $product, expect MORTARO/SARACENO"
        exit 1
        ;;
esac

if [[ "$2" =~ ^[0-9]{3}$ ]]; then
    release=$2
else
    echo "Invalid release version $2, expect 3 digits"
    exit 1
fi

version="$product-$major.$minor.$release"
echo "Generate mfg script version $version for $product"

BUILD_DIR=$(pwd)
TOP_DIR=$(dirname $BUILD_DIR)
IMG_DIR=$BUILD_DIR/images/
REL_IMG_DIR="/vol/hw/diag/mfg_release/$product"

# Copy mfg code base and release images.
TEMP_DIR=$BUILD_DIR/temp/
TARGET_DIR=$TEMP_DIR/$version
mkdir -p $TARGET_DIR
cp -r $TOP_DIR/diag/mfg $TARGET_DIR
mkdir -p $TARGET_DIR/mfg/release

case "$product" in
    GELSO|SARACENO|MORTARO)
        # Copy diag image and update config file
        cp $IMG_DIR/image_amd64_vulcano.tar $TARGET_DIR/mfg/release/image_amd64_vulcano.tar
        touch $TARGET_DIR/mfg/release/image_arm64_vulcano.tar
        cd $TARGET_DIR
        sed -i 's|MTP_AMD64_IMAGE = ".*\.tar"|MTP_AMD64_IMAGE = "image_amd64_vulcano.tar"|' mfg/lib/libmfg_cfg.py
        sed -i 's|MTP_ARM64_IMAGE = ".*\.tar"|MTP_ARM64_IMAGE = "image_arm64_vulcano.tar"|' mfg/lib/libmfg_cfg.py
        # Set power on delay to 30 seconds for Saraceno/Mortaro
        sed -i 's|NIC_POWER_ON_DELAY = 80|NIC_POWER_ON_DELAY = 30|' mfg/lib/libdefs.py
        # Copy other required release files defined in libmfg_cfg.py
        cp -r $REL_IMG_DIR/* $TARGET_DIR/mfg/release/
        ;;
    *)
        echo "Invalid product name: $product, expect MORTARO/SARACENO"
        exit 1
        ;;
esac

# Now packaging
cd $TEMP_DIR
tar czf $IMG_DIR/${version}.tar $version
echo "--------------------"
echo "Cleaning up."
rm -rf $TARGET_DIR
echo "Clean up -- Done"
