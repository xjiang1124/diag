#!/bin/bash
set -x 

_mydir="`pwd`"
echo "My Currently Dir: $_mydir"

SCRIPTLOG=$_mydir/LOG/myfirstlog.log
exec > >(tee -i $SCRIPTLOG)
exec 2>&1

echo "Log Location should be: [ $SCRIPTLOG ]"

configNames=(
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
TAORMINA_P2_2_input.json
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
python3 $2/process_log.py $1 rerun=4C
}

START=$(date +%s);

echo Script: runReport.sh



for name in "${configNames[@]}";
do 
        runReportModule $name $_mydir
done

cd $_mydir
python3 $_mydir/zip_old_json_file.py

cd $_mydir
python3 $_mydir/move_old_log_file_to_one_folder.py

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'