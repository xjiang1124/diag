#!/bin/bash
set -x 

DATE=`date +%d-%m-%y` 
now=$(date +"%b%d-%Y-%H%M%S")
#_mydir="`pwd`"
_mydir="/home/diag/logserver"
echo "My Currently Dir ($DATE): $_mydir"

SCRIPTLOG=$_mydir/LOG/upload_report_log_$now.log
exec > >(tee -i $SCRIPTLOG)
exec 2>&1

echo "Log Location should be: [ $SCRIPTLOG ]"
echo "My Currently Dir ($DATE): $_mydir"

#exit 0

rsync -r -a -v --delete --include="*.xlsx" --exclude="*LastFail*" -e ssh mfg@logserver01:/samba/public/REPORT/  /testreport/

rsync -r -a -v -e "ssh winson@192.168.100.2" /testreport/ ":/cygdrive/g/Shared\ drives/TestStatus/"