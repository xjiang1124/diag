#!/bin/bash

set -x

if [ -z $RELEASE ]
then
    echo "RELEASE not set, return"
    exit 0
fi

ls -l /psdiag/build/images/*

mkdir -p /releases/images
mkdir -p /releases/diag/mfg
mkdir -p /releases/diag/mfg/mtp_regression
mkdir -p /releases/diag/mfg/lib
mkdir -p /releases/diag/mfg/config

cp /psdiag/build/images/* /releases/images/
cp /psdiag/diag/mfg/qa_regression_test.py /releases/diag/mfg
cp /psdiag/diag/mfg/mtp_regression/*.py /releases/diag/mfg/mtp_regression/
cp /psdiag/diag/mfg/lib/*.py /releases/diag/mfg/lib/
cp /psdiag/diag/mfg/config/*.yaml /releases/diag/mfg/config/
cd /; asset-push --remote-name releases.tar.gz builds hourly-diag ${RELEASE} releases

