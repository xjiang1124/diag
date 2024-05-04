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
mkdir -p ${HOME}/.local

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
    --diag-images ${PSDIAG_ROOT}/build/images $@
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

NIC_BARCODE_FILE=${PSDIAG_ROOT}/nic_barcode_scan
if [[ -f ${NIC_BARCODE_FILE} ]];
then
    echo ""
    echo "Contents of ${NIC_BARCODE_FILE}"
    cat ${NIC_BARCODE_FILE}
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
asic=$ASIC

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

if [[ -f "${PSDIAG_ROOT}/fw.tar" ]];
then
    ls -lt ${PSDIAG_ROOT}/fw.tar
else
    echo "Missing ${PSDIAG_ROOT}/fw.tar - ABORT"
    cd ${PSDIAG_ROOT}
    tar -zcvf diag_detailed_log.tgz log
    exit 249
fi
tar xf ${PSDIAG_ROOT}/fw.tar -C ${PSDIAG_ROOT}/${mfg_script_dir}/mfg/
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
echo "Diag Tools"
ls -ltr ${DIAG_IMAGE_FOLDER}

if [[ "${JOB_TYPE}" != "ScanDL" && "${JOB_TYPE}" != "FST" ]];
then
    echo "**************************************************"
    echo " Launching ScanDL to restore card before test"
    echo "**************************************************"

    set -x
    # need to pass --iteration=1 to unset any iteration arg passed in TEST_ARGS
    python3 ./mfg_test.py sdl ${TEST_ARGS} --iteration=1 --logdir ${PSDIAG_ROOT}/log < ${NIC_BARCODE_FILE}
    ret=$?
else
    ret=0
fi

if [[ $ret == 0 && "${JOB_TYPE}" == "DL" ]];
then
    echo "**************************************************"
    echo " Launching mfg_test.py dl"
    echo "**************************************************"

    set -x
    python3 ./mfg_test.py dl ${TEST_ARGS} --logdir ${PSDIAG_ROOT}/log < ${NIC_BARCODE_FILE}
    ret=$?
fi

if [[ "${JOB_TYPE}" == "ScanDL" ]];
then
    echo "**************************************************"
    echo " Launching mfg_test.py sdl"
    echo "**************************************************"

    set -x
    python3 ./mfg_test.py sdl ${TEST_ARGS} --logdir ${PSDIAG_ROOT}/log < ${NIC_BARCODE_FILE}
    ret=$?
fi

if [[ $ret == 0 && "${JOB_TYPE}" == "P2C" ]];
then
    echo "**************************************************"
    echo " Launching mfg_test.py p2c"
    echo "**************************************************"

    set -x
    python3 ./mfg_test.py p2c ${TEST_ARGS} --logdir ${PSDIAG_ROOT}/log
    ret=$?
fi

if [[ $ret == 0 && "${JOB_TYPE}" == "4C" ]];
then
    echo "**************************************************"
    echo " Launching mfg_test.py 4c --low_temp"
    echo "**************************************************"

    set -x
    echo "STOP" > /tmp/4c_input
    python3 ./mfg_test.py 4c ${TEST_ARGS} --low_temp --logdir ${PSDIAG_ROOT}/log < /tmp/4c_input
    ret=$?
fi

if [[ $ret == 0 && "${JOB_TYPE}" == "SWI" ]];
then
    echo "**************************************************"
    echo " Launching mfg_test.py swi"
    echo "**************************************************"

    set -x
    python3 ./mfg_test.py swi ${TEST_ARGS} --logdir ${PSDIAG_ROOT}/log < ${NIC_BARCODE_FILE}
    ret1=$?
    if [[ "${NIC_TYPE}" == "ortano-adi-ibm" ]]; then # convert back the cpld
        python3 ./mfg_test.py cnic ${TEST_ARGS} --logdir ${PSDIAG_ROOT}/log < ${NIC_BARCODE_FILE}
        ret2=$?
    else ret2=0
    fi
    (( ret = ret1 || ret2 )) # both step should pass
fi

if [[ "${JOB_TYPE}" == "FST" ]];
then
    echo "**************************************************"
    echo " Launching mfg_test.py fst"
    echo "**************************************************"

    set -x
    python3 ./mfg_test.py fst ${TEST_ARGS} --card_type ${CARD_TYPE} --logdir ${PSDIAG_ROOT}/log < ${NIC_BARCODE_FILE}
    ret=$?
fi

if [[ $ret == 0 && "${JOB_TYPE}" == "ORT" ]];
then
    echo "**************************************************"
    echo " Launching mfg_ort_test.py for two loops"
    echo "**************************************************"

    set -x
    python3 ./mfg_test.py ort ${TEST_ARGS} --logdir ${PSDIAG_ROOT}/log
    ret=$?
fi

if [[ $ret == 0 && "${JOB_TYPE}" == "RDT" ]];
then
    echo "**************************************************"
    echo " Launching mfg_rdt_test.py for two loops"
    echo "**************************************************"

    set -x
    python3 ./mfg_test.py rdt ${TEST_ARGS} --logdir ${PSDIAG_ROOT}/log
    ret=$?
fi

cd ${PSDIAG_ROOT}
tar -zcvf diag_detailed_log.tgz log

exit $ret
