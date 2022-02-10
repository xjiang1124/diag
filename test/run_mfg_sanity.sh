#!/bin/bash

#set -x

echo "Installing dependencies..."
apt-get install -y python3
apt-get install -y python3-pip
apt-get install -y iputils-ping
apt-get install -y vim

pip3 install -r /psdiag/test/infra/requirements.txt

echo "Running MFG-DIAG on reserved MTP"
echo ""
cat /warmd.json

echo "Generating MTP-CFGYML file..."
python3 /psdiag/test/infra/launch.py --logdir /psdiag/log --cfg-folder /psdiag/diag/mfg/config $@
ret=$?

source /psdiag/env.sh

echo "MTP_ID=${MTP_ID}"
echo "MTP_CFG_YML=${MTP_CFG_YML}"
echo "DIAG_AMD64_IMAGE_PATH=${DIAG_AMD64_IMAGE_PATH}"
echo "DIAG_ARM64_IMAGE_PATH=${DIAG_ARM64_IMAGE_PATH}"
echo "DIAG_VERSION=${DIAG_VERSION}"
echo "DIAG_IMAGE_FOLDER=${DIAG_IMAGE_FOLDER}"
cat ${MTP_CFG_YML}


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
