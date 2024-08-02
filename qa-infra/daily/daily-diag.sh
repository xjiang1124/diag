#!/bin/sh

ls psdiag/build/images/ -la

if [ -z $RELEASE ]
then
    echo "RELEASE not set, aborting. Run this script from JobD releases page."
    exit 0
fi

rsync -aPtv /psdiag/build/images/*.tar /vol/hw/diag/diag_images/daily/ --exclude='.*'
chmod +r /vol/hw/diag/diag_images/daily/*.tar
