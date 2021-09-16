#!/bin/bash
set -x 

DATE=`date +%d-%m-%y` 
now=$(date +"%b%d-%Y-%H%M%S")
#_mydir="`pwd`"
_mydir="/home/diag/logserver"
echo "My Currently Dir ($DATE): $_mydir"

SCRIPTLOG=$_mydir/LOG/log_$DATE.log
exec > >(tee -i $SCRIPTLOG)
exec 2>&1

echo "My Currently Dir ($DATE): $_mydir"
echo "NOW: $now"

echo "Log Location should be: [ $SCRIPTLOG ]"
echo "My Currently Dir ($DATE): $_mydir"

cd /home/diag/hw
pwd
ls -altr
cd $_mydir
pwd
python3 $_mydir/copy_diag_image_by_date.py

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'