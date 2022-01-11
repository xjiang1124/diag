#!/bin/bash
set -x 



DATE=`date +%d-%m-%y` 
now=$(date +"%b%d-%Y-%H%M%S")
#_mydir="`pwd`"
_mydir="/home/mfg/logserver"
echo "My Currently Dir ($DATE): $_mydir"

SCRIPTLOG=$_mydir/LOG/log_$now.log
exec > >(tee -i $SCRIPTLOG)
exec 2>&1

echo "Log Location should be: [ $SCRIPTLOG ]"
echo "My Currently Dir ($DATE): $_mydir"

#exit 0

# Exit if /tmp/lock.file exists
[ -f /tmp/runReport_special.file ] && exit

# Create lock file, sleep 1 sec and verify lock
echo $$ > /tmp/runReport_special.file
sleep 1
[ "x$(cat /tmp/runReport_special.file)" == "x"$$ ] || exit

configNames=(
NAPLES100DELL_input.json
POMONTE_test_input.json
ORTANO2_input.json
NAPLES25_input.json
NAPLES25SWM_input.json
NAPLES25SWM833_input.json
NAPLES25SWMDELL_input.json
NAPLES100_input.json
NAPLES100HPE_input.json
NAPLES100IBM_input.json
NAPLES25OCP_input.json
TAORMINA_PP_input.json
FLEX_LACONA32DELL_P1B_input.json
LACONA32DELL_input.json
LACONA32_input.json
POMONTEDELL_test_input.json
)

runReportModule()
{
echo
echo "Run Report Config File: $1"
cd /mnt/hw-mftg-data
pwd
ls -altr
cd $2
pwd
echo "Run Report Config File: $1"
python3 $2/process_log.py $1 
}

START=$(date +%s);

echo Script: runReport_special.sh

#ORTANO2_EDMA_1

#Unknown_EDMA_3200
#ORTANO2_EDMA_3200
#ORTANO2_EDMA_3200_loop

#ORTANO2_EDMA_3200_lv6

#ORTANO2_EDMA_3200_lv5

#ORTANO2_EDMA_3200_lv4

#ORTANO2_EDMA_3200_1M

#ORTANO2_EDMA_3200_1M_3-75

#ORTANO2_EDMA_3200_1M_hv3

#ORTANO2_EDMA_3200_1M_hv5-251

#ORTANO2_EDMA_3200_1M_lv3-75_round2

#ORTANO2_EDMA_3200_1M_lv3-75_round3

#ORTANO2_EDMA_3200_1M_lv6_round2

#ORTANO2_EDMA_3200_1M_lv3-75_round4

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_1M_lv3-75_round4_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_1M_lv6_round2_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_1M_lv3-75_round3_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_1M_lv3-75_round2_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_1M_hv5-25_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_1M_hv3_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_1M_3-75_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_1M_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_lv4_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_lv5_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_lv12_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_lv9_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_lv6_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_2800_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_loop_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_loop_w_pwrcycle_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_loop_input.json specreport3=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_3200_input.json specreport2=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_EDMA_1_input.json specreport2=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_SNAKE2_2_input.json specreport=1 skiplock=1

cd $_mydir
python3 $_mydir/process_log.py ORTANO2_SNAKE_input.json specreport=1 skiplock=1

# for name in "${configNames[@]}";
# do 
#         runReportModule $name $_mydir
# done



# cd $_mydir
# python3 $_mydir/all_mtp_report.py

# cd $_mydir
# python3 $_mydir/zip_old_json_file.py

# cd $_mydir
# python3 $_mydir/move_old_log_file_to_one_folder.py

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'

# Remove lock file
rm /tmp/runReport_special.file