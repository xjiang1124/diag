#!/bin/bash

#set -x

export PSDIAG_ROOT=/psdiag

echo "Installing dependencies..."
sudo apt-get install -y python3
sudo apt-get install -y python3-pip
sudo apt-get install -y iputils-ping
sudo apt-get install -y vim
sudo apt-get install -y telnet

sudo pip3 install -r ${PSDIAG_ROOT}/test/infra/requirements.txt

if [[ -f /warmd.json ]] ;
then
    cat /warmd.json
    mkdir -p ${PSDIAG_ROOT}/log
    cp /warmd.json ${PSDIAG_ROOT}/log
fi

echo "Generating MTP-CFGYML file and test-arguments..."
python3 ${PSDIAG_ROOT}/test/infra/launch.py \
    --cfg-folder ${PSDIAG_ROOT}/diag/mfg/config \
    --image-manifest ${PSDIAG_ROOT}/test/manifests/latest.json \
    --diag-images ${PSDIAG_ROOT}/build/images \
    --asic-images ${PSDIAG_ROOT}/releases $@
ret=$?

if [[ "$ret" != "0" ]];
then
    echo "Launch script failed - ABORT"
    cd ${PSDIAG_ROOT}
    tar -zcvf diag_detailed_log.tgz log
    exit 249
fi

if [[ -f ${PSDIAG_ROOT}/env.sh ]];
then
    echo "Contents of ${PSDIAG_ROOT}/env.sh:"
    cat ${PSDIAG_ROOT}/env.sh
    source ${PSDIAG_ROOT}/env.sh
else
    echo "Missing ${PSDIAG_ROOT}/env.sh - ABORT"
    cd ${PSDIAG_ROOT}
    tar -zcvf diag_detailed_log.tgz log
    exit 249
fi

if [[ -f "${MTP_CFG_YML}" ]];
then
    cat ${MTP_CFG_YML}
else
    echo "Missing ${MTP_CFG_YML} - ABORT"
    cd ${PSDIAG_ROOT}
    tar -zcvf diag_detailed_log.tgz log
    exit 249
fi

echo ""
echo "Install python tool-set from ${PSDIAG_ROOT}/tools/python_packets/amd64/lib"
echo ""

mkdir -p ${HOME}/.local
cp -r ${PSDIAG_ROOT}/tools/python_packets/amd64/lib ${HOME}/.local/
export PYTHONPATH=$PYTHONPATH:${PSDIAG_ROOT}/diag/mfg:${PSDIAG_ROOT}/diag/mfg/lib
cd ${PSDIAG_ROOT}/diag/mfg

echo ""
echo "Mfg script release step: rename diag images with release name"
echo ""
AMD64_DIAG_IMAGE=$(basename -s .tar ${DIAG_AMD64_IMAGE_PATH})
ARM64_DIAG_IMAGE=$(basename -s .tar ${DIAG_ARM64_IMAGE_PATH})
sed -i "s/MTP_ARM64_IMAGE = \".*\.tar\"/MTP_ARM64_IMAGE = \"${ARM64_DIAG_IMAGE}.tar\"/g" ${PSDIAG_ROOT}/diag/mfg/lib/libmfg_cfg.py
sed -i "s/MTP_AMD64_IMAGE = \".*\.tar\"/MTP_AMD64_IMAGE = \"${AMD64_DIAG_IMAGE}.tar\"/g" ${PSDIAG_ROOT}/diag/mfg/lib/libmfg_cfg.py

if [[ "${JOB_TYPE}" == "MFG_DIAG" ]];
then
    echo "Diag Tools"
    ls -ltr ${DIAG_IMAGE_FOLDER}

    echo "ASIC Libraries "
    ls -ltr ${ASIC_IMAGE_FOLDER}

    echo ""
    echo "Launching qa_regression_test.py"
    echo ""

    set -x
    python ${PSDIAG_ROOT}/diag/mfg/qa_regression_test.py ${TEST_ARGS} --logdir ${PSDIAG_ROOT}/log
    ret=$?
fi

if [[ "${JOB_TYPE}" == "FST" ]];
then
    echo ""
    echo "Launching mfg_fst_test.py"
    echo ""

    set -x
    python ${PSDIAG_ROOT}/diag/mfg/mfg_fst_test.py ${TEST_ARGS} --card_type ${CARD_TYPE} --logdir ${PSDIAG_ROOT}/log
    ret=$?
fi

cd ${PSDIAG_ROOT}
tar -zcvf diag_detailed_log.tgz log

exit $ret
