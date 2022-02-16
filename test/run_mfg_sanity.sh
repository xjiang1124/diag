#!/bin/bash

#set -x

echo "Installing dependencies..."
sudo apt-get install -y python3
sudo apt-get install -y python3-pip
sudo apt-get install -y iputils-ping
sudo apt-get install -y vim

sudo pip3 install -r /psdiag/test/infra/requirements.txt

echo "Generating MTP-CFGYML file..."
python3 /psdiag/test/infra/launch.py --cfg-folder /psdiag/diag/mfg/config --image-manifest /psdiag/test/manifests/latest.json --diag-images /psdiag/build/images --asic-images /psdiag/releases $@
ret=$?

if [[ "$ret" != "0" ]];
then
    echo "Launch script failed - ABORT"
    exit 249
fi

source /psdiag/env.sh

echo "MTP_ID=${MTP_ID}"
echo "MTP_CFG_YML=${MTP_CFG_YML}"
echo "DIAG_AMD64_IMAGE_PATH=${DIAG_AMD64_IMAGE_PATH}"
echo "DIAG_ARM64_IMAGE_PATH=${DIAG_ARM64_IMAGE_PATH}"
echo "DIAG_VERSION=${DIAG_VERSION}"
echo "DIAG_IMAGE_FOLDER=${DIAG_IMAGE_FOLDER}"
echo "ASIC_IMAGE_FOLDER=${ASIC_IMAGE_FOLDER}"

if [[ -f "${MTP_CFG_YML}" ]];
then
    cat ${MTP_CFG_YML}
else
    echo "Missing ${MTP_CFG_YML} - ABORT"
    exit 249
fi

echo "Diag Tools"
ls -ltr ${DIAG_IMAGE_FOLDER}

echo "ASIC Libraries "
ls -ltr ${ASIC_IMAGE_FOLDER}

echo ""
echo "Install python tool-set from /psdiag/tools/python_packets/amd64/lib"
echo ""

mkdir -p ${HOME}/.local
cp -r /psdiag/tools/python_packets/amd64/lib ${HOME}/.local/
export PYTHONPATH=$PYTHONPATH:/psdiag/diag/mfg:/psdiag/diag/mfg/lib

cd /psdiag/diag/mfg
echo ""
echo "Launching qa_regression_test.py"
echo ""

set -x
python /psdiag/diag/mfg/qa_regression_test.py --mtpcfg ${MTP_CFG_YML} --iteration 1 --mtpid ${MTP_ID} --logdir /psdiag/log
ret=$?

cd /psdiag
tar -zcvf diag_detailed_log.tgz log

exit $ret
