#!/usr/bin/env bash
set -x 

DATE=`date +%d-%m-%y` 
now=$(date +"%b%d-%Y-%H%M%S")
#_mydir="`pwd`"
_mydir="/home/mfg/runTestscriptinServer"
echo "My Currently Dir ($DATE): $_mydir"

SCRIPTLOGDIR=$_mydir/LOOGLOG/$DATE
SCRIPTLOG=$_mydir/LOOGLOG/$DATE/LOOPTEST_log_$now.log
mkdir -p $SCRIPTLOGDIR
exec > >(tee -i $SCRIPTLOG)
exec 2>&1

START=$(date +%s);

echo "Log Location should be: [ $SCRIPTLOG ]"
echo "My Currently Dir ($DATE): $_mydir"

while true
do
	
	cd $_mydir
	python3 $_mydir/Loop_Test.py
	echo "Wait for 30 minutes"
	sleep 30m

done

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'