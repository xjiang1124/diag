#!/bin/bash

#set -x

export PSDIAG_ROOT=/psdiag

echo "**************************************************"
echo "Installing dependencies..."
echo "**************************************************"
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
echo "**************************************************"
echo " Generating MTP-CFGYML file and test-arguments..."
echo "**************************************************"
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

echo "**************************************************"
echo " Install python tool-set from ${PSDIAG_ROOT}/tools/python_packets/amd64/lib"
echo "**************************************************"
mkdir -p ${HOME}/.local
cp -r ${PSDIAG_ROOT}/tools/python_packets/amd64/lib ${HOME}/.local/


echo "**************************************************"
echo " Unpack mfg script"
echo "**************************************************"
cd ${PSDIAG_ROOT}
mfg_script_dir=jobd
asic=$(basename ${ASIC_IMAGE_FOLDER})

if [[ -f "${PSDIAG_ROOT}/${mfg_script_dir}/${mfg_script_dir}.tar.gz" ]];
then
    ls -lt ${PSDIAG_ROOT}/${mfg_script_dir}/${mfg_script_dir}.tar.gz
else
    echo "Missing ${PSDIAG_ROOT}/${mfg_script_dir}/${mfg_script_dir}.tar.gz - ABORT"
    cd ${PSDIAG_ROOT}
    tar -zcvf diag_detailed_log.tgz log
    exit 249
fi
tar xzf ${PSDIAG_ROOT}/${mfg_script_dir}/${mfg_script_dir}.tar.gz -C ${PSDIAG_ROOT}
sync

if [[ -f "${PSDIAG_ROOT}/${mfg_script_dir}/fw.tar.gz" ]];
then
    ls -lt ${PSDIAG_ROOT}/${mfg_script_dir}/fw.tar.gz
else
    echo "Missing ${PSDIAG_ROOT}/${mfg_script_dir}/fw.tar.gz - ABORT"
    cd ${PSDIAG_ROOT}
    tar -zcvf diag_detailed_log.tgz log
    exit 249
fi
tar xzf ${PSDIAG_ROOT}/${mfg_script_dir}/fw.tar.gz -C ${PSDIAG_ROOT}/${mfg_script_dir}/mfg/
sync

cp ${PSDIAG_ROOT}/build/images/image_amd64_${asic}.tar ${PSDIAG_ROOT}/${mfg_script_dir}/mfg/release/image_amd64_${asic}_${mfg_script_dir}.tar
cp ${PSDIAG_ROOT}/build/images/image_arm64_${asic}.tar ${PSDIAG_ROOT}/${mfg_script_dir}/mfg/release/image_arm64_${asic}_${mfg_script_dir}.tar
cp ${MTP_CFG_YML} ${PSDIAG_ROOT}/${mfg_script_dir}/mfg/config/
sync

ls ${PSDIAG_ROOT}/${mfg_script_dir}/ -lt
ls ${PSDIAG_ROOT}/${mfg_script_dir}/mfg/config/ -lt
ls ${PSDIAG_ROOT}/${mfg_script_dir}/mfg/release/ -lt
echo "**************************************************"
echo " Unpacking complete"
echo "**************************************************"


cd ${PSDIAG_ROOT}/${mfg_script_dir}/mfg

if [[ "${JOB_TYPE}" == "DL" ]];
then
    echo "Diag Tools"
    ls -ltr ${DIAG_IMAGE_FOLDER}

    echo "ASIC Libraries "
    ls -ltr ${ASIC_IMAGE_FOLDER}

    echo "**************************************************"
    echo " Launching mfg_dl_test.py"
    echo "**************************************************"

    set -x
    python ./mfg_dl_test.py ${TEST_ARGS} --logdir ${PSDIAG_ROOT}/log
    ret=$?
fi

if [[ "${JOB_TYPE}" == "P2C" ]];
then
    echo "Diag Tools"
    ls -ltr ${DIAG_IMAGE_FOLDER}

    echo "ASIC Libraries "
    ls -ltr ${ASIC_IMAGE_FOLDER}

    echo "**************************************************"
    echo " Launching mfg_p2c_test.py"
    echo "**************************************************"

    set -x
    python ./mfg_p2c_test.py ${TEST_ARGS} --logdir ${PSDIAG_ROOT}/log
    ret=$?
fi

if [[ "${JOB_TYPE}" == "4C" ]];
then
    echo "Diag Tools"
    ls -ltr ${DIAG_IMAGE_FOLDER}

    echo "ASIC Libraries "
    ls -ltr ${ASIC_IMAGE_FOLDER}

    echo "**************************************************"
    echo " Launching mfg_4c_test.py --low-temp"
    echo "**************************************************"

    set -x
    echo "STOP" > /tmp/4c_input
    python ./mfg_4c_test.py ${TEST_ARGS} --low-temp --logdir ${PSDIAG_ROOT}/log < /tmp/4c_input
    ret=$?
fi

if [[ "${JOB_TYPE}" == "FST" ]];
then
    echo "**************************************************"
    echo " Launching mfg_fst_test.py"
    echo "**************************************************"

    set -x
    python ./mfg_fst_test.py ${TEST_ARGS} --card_type ${CARD_TYPE} --logdir ${PSDIAG_ROOT}/log
    ret=$?
fi

cd ${PSDIAG_ROOT}
tar -zcvf diag_detailed_log.tgz log

exit $ret
