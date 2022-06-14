#!/bin/bash
#nzaim

##########
# Change logfile name to follow Aruba format
# - input: the original logfile
# - aruba-logfile.sh extracts the log into temp folder, changes the names of all files, and recompresses to a new tarball
# - output: logfile with new name stored to destination folder
##########

if [[ -z $1 ]]; then
	echo "Usage: ./aruba-log.sh /full/path/to/logfile.tar.gz"
	exit -1
fi

######################################

PENSANDO_LOG_FILE=$1				#/mfg_log/x/x/x/DL2_xx.tar.gz
PENSANDO_LOG_PATH=${PENSANDO_LOG_FILE%.tar.gz}	#/mfg_log/x/x/x/DL2_xx
PENSANDO_LOG_FOLDER=${PENSANDO_LOG_PATH##*/}	#DL2_xx
DESTINATION_FOLDER="/home/prod/Taormina/"
TEMP_FOLDER="/tmp"

######################################


mkdir -p ${TEMP_FOLDER}
tar xzf $1 -C ${TEMP_FOLDER}

if [[ ! -f ${TEMP_FOLDER}/${PENSANDO_LOG_FOLDER}/mtp_test.log ]]; then
	echo "ERROR empty log archive"
	exit -1
fi

SN=$(grep "DIAG_REGRESSION_TEST_" ${TEMP_FOLDER}/${PENSANDO_LOG_FOLDER}/mtp_test.log | awk -F" " '{print $(NF-1)}')
YYMMDD=$(echo $PENSANDO_LOG_FOLDER | cut -d "_" -f3)
hhmmss=$(echo $PENSANDO_LOG_FOLDER | cut -d "_" -f4)
RESULT=$(grep "DIAG_REGRESSION_TEST_" ${TEMP_FOLDER}/${PENSANDO_LOG_FOLDER}/mtp_test.log | awk -F"_" '{print $NF}')
TESTSTAGE=$(echo $PENSANDO_LOG_FOLDER | cut -d"_" -f1)

aruba_file_suffix="${SN}_${YYMMDD}_${hhmmss}_${RESULT}"
aruba_log=${aruba_file_suffix}_${TESTSTAGE}
mkdir ${TEMP_FOLDER}/${aruba_log}

for f in $(ls ${TEMP_FOLDER}/${PENSANDO_LOG_FOLDER}); do
	mv ${TEMP_FOLDER}/${PENSANDO_LOG_FOLDER}/$f ${TEMP_FOLDER}/${aruba_log}/${aruba_file_suffix}_$f
done

cd ${TEMP_FOLDER}
tar czf ${aruba_log}.tar.gz ${aruba_log}/
mv ${TEMP_FOLDER}/${aruba_log}.tar.gz ${DESTINATION_FOLDER}/${TESTSTAGE}/${aruba_log}.tar.gz

rm -rf ${TEMP_FOLDER}/${aruba_log}
rm -rf ${TEMP_FOLDER}/${PENSANDO_LOG_FOLDER}

if [[ -e ${DESTINATION_FOLDER}/${TESTSTAGE}/${aruba_log}.tar.gz ]]; then
	echo -e "TEST LOG $1 \nSAVED TO ${DESTINATION_FOLDER}/${TESTSTAGE}/${aruba_log}.tar.gz"
else
	echo -e "ERROR IN SAVING LOG TO ${DESTINATION_FOLDER}/${TESTSTAGE}/${aruba_log}.tar.gz"
fi
