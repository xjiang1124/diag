#!/bin/bash

#set -x

DIAG_JOB=$1
shift

export PSDIAG_ROOT=/psdiag

echo "**************************************************"
echo "Installing dependencies..."
echo "**************************************************"
sudo apt install -y sshpass

# sudo pip3 install -r ${PSDIAG_ROOT}/test/infra/requirements.txt
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

MTP_BARCODE_FILE=${PSDIAG_ROOT}/mtp_barcode_scan
if [[ -f ${MTP_BARCODE_FILE} ]];
then
    echo ""
    echo "Contents of ${MTP_BARCODE_FILE}"
    cat ${MTP_BARCODE_FILE}
fi

NIC_BARCODE_FILE=${PSDIAG_ROOT}/nic_barcode_scan
if [[ -f ${NIC_BARCODE_FILE} ]];
then
    echo ""
    echo "Contents of ${NIC_BARCODE_FILE}"
    cat ${NIC_BARCODE_FILE}
fi

PARSER_SN_FILE=${PSDIAG_ROOT}/parser_sn.txt
if [[ -f ${PARSER_SN_FILE} ]];
then
    echo ""
    echo "Contents of ${PARSER_SN_FILE}"
    cat ${PARSER_SN_FILE}
else
    echo "Missing ${PARSER_SN_FILE}"
fi
sudo mkdir -p /mfg_log
sudo mkdir -p /tmp/mfg_log

echo "**************************************************"
echo " Install python tool-set from ${PSDIAG_ROOT}/tools/python_packets/amd64/lib"
echo "**************************************************"
mkdir -p ${HOME}/.local
cp -r ${PSDIAG_ROOT}/tools/python_packets/amd64/lib ${HOME}/.local/

MTPIP=$(grep "IP:" ${MTP_CFG_YML} | awk -F": " '{print $NF}')
SLOT=$(grep "NIC-" ${NIC_BARCODE_FILE} | head -n1 | awk -F"-0" '{print $NF}')  ##TODO: better way to get single digit slot
LOGFILE=${PSDIAG_ROOT}/log/test.log
echo $(date) > $LOGFILE
echo "**************************************************"
echo " Update MTP diag image "
echo "**************************************************"
SSH_OPTIONS=( -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30' )
rsync --rsh="/usr/bin/sshpass -p lab123 ssh -o StrictHostKeyChecking=no -l diag" -aPtv ${PSDIAG_ROOT}/build/images/image_amd64_${ASIC}.tar diag@$MTPIP:~
sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP "set +x; tar xf ~/image_amd64_${ASIC}.tar; /home/diag/start_diag.sh"
ret=$?
echo "RETURN CODE= $ret"

if [[ $ret == 0 ]]; then
    echo "**************************************************"
    echo " Running test "
    echo "**************************************************"

    sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
    source ~/.bash_profile; set -x; \
    turn_on_slot.sh off $SLOT; \
    sleep 3; turn_on_slot.sh on $SLOT; \
    fpgautil spimode $SLOT off; \
    jtag_accpcie_salina clr $SLOT; \
    " | tee -a $LOGFILE

    case $(echo ${DIAG_JOB}_${NIC_TYPE}) in
        ##TODO: commands not printing on screen, only outputs
        l1_leni)
            echo "Running l1 leni" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/scripts/asic; \
            tclsh l1_test.tcl slot$SLOT $SLOT hod 0 normal 0 0 0 0 0 1 1 0 1; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        l1_pollara)
            echo "Running l1 pollara" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/scripts/asic; \
            tclsh l1_test.tcl slot$SLOT $SLOT hod 0 normal 0 0 0 0 0 0 1 0 1; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        mbist_leni)
            echo "Running mbist leni" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/scripts/asic; \
            tclsh jtag_screen.tcl -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        mbist_pollara)
            echo "Running mbist pollara" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/scripts/asic; \
            tclsh jtag_screen.tcl -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        pcieprbs_leni)
            echo "Running PCIE PRBS leni" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py pcie_prbs -card_type LENI -dura 60 -tcl_path /home/diag/diag/asic/ -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        pcieprbs_pollara)
            echo "Running PCIE PRBS pollara" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py pcie_prbs -card_type POLLARA -dura 60 -tcl_path /home/diag/diag/asic/ -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        ddrsnake_leni)
            echo "Running snake leni" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py nic_snake_mtp -snake_type esam_pktgen_ddr_burst_400G_no_mac -timeout 3600 -dura 900 -tcl_path /home/diag/diag/asic/ -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        snake_leni)
            echo "Running snake leni" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py nic_snake_mtp -snake_type esam_pktgen_max_power_pcie_sor -card_type LENI -timeout 3600 -dura 900 -tcl_path /home/diag/diag/asic/ -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        snake_pollara)
            echo "Running snake pollara" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py nic_snake_mtp -snake_type esam_pktgen_pollara_max_power_pcie_arm -card_type POLLARA -timeout 3600 -dura 900 -tcl_path /home/diag/diag/asic/ --lpmode 1 -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        googlestress_leni)
            echo "Running google stress test leni" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py mem_test -tcl_path /home/diag/diag/asic/ -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        qsfp_leni)
            echo "Running QSFP leni" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py test_spi -tcl_path /home/diag/diag/asic/ -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        qsfp_pollara)
            echo "Running QSFP test pollara" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py test_spi -tcl_path /home/diag/diag/asic/ -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        dpufru_leni)
            echo "Running PROG DPU FRU leni" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py prog_dpu_fru -skip_fru2 -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        dpufru_pollara)
            echo "Running PROG DPU FRU pollara" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py prog_dpu_fru -skip_fru2 -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        i2caccess_leni)
            echo "Running I2C TEST leni" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/python/regression; \
            python3 ./nic_test_v2.py prog_dpu_fru -skip_fru2 -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;
        i2caccess_pollara)
            echo "Running I2C TEST pollara" | tee -a $LOGFILE
            echo "**************************************************"
            sshpass -p lab123 ssh ${SSH_OPTIONS[@]} diag@$MTPIP " \
            source ~/.bash_profile; set -x; \
            cd /home/diag/diag/scripts/asic; \
            tclsh sal_i2c_access.tcl -slot $SLOT; \
            ret=\$?; if [[ \$ret == 0 ]]; then echo jobd-passed; fi \
            " | tee -a $LOGFILE
            grep "jobd-passed" $LOGFILE
            ret=$?
            echo "RETURN CODE= $ret"
            ;;

        *)
            echo "Unknown test name ${DIAG_JOB} or card ${NIC_TYPE}" | tee -a $LOGFILE
            ret=-1
            ;;
    esac
fi

cd ${PSDIAG_ROOT}
tar -zcvf diag_detailed_log.tgz log
exit $ret
