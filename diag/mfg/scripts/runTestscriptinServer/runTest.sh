#!/bin/bash
set -x 

DATE=`date +%d-%m-%y` 
now=$(date +"%b%d-%Y-%H%M%S")
#_mydir="`pwd`"
_mydir="/home/mfg/runTestscriptinServer"
echo "My Currently Dir ($DATE): $_mydir"

SCRIPTLOGDIR=$_mydir/LOG/$DATE
SCRIPTLOG=$_mydir/LOG/$DATE/log_$now.log
mkdir -p $SCRIPTLOGDIR
exec > >(tee -i $SCRIPTLOG)
exec 2>&1

echo "Log Location should be: [ $SCRIPTLOG ]"
echo "My Currently Dir ($DATE): $_mydir"

cd $_mydir
python3 $_mydir/RunTest.py

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'