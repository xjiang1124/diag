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


# Exit if /tmp/lock.file exists
[ -f /tmp/runuploadReport_truelock.file ] && exit

# Create lock file, sleep 1 sec and verify lock
echo $$ > /tmp/runuploadReport_truelock.file
sleep 1
[ "x$(cat /tmp/runuploadReport_truelock.file)" == "x"$$ ] || exit

#exit 0

rsync -r -a -v --delete --include="*.xlsx" --exclude="*LastFail*" --exclude="*LOG_COPY*" -e ssh mfg@logserver01:/samba/public/REPORT/  /testreport/

#rsync -r -a -v --delete -e ssh mfg@logserver01:/samba/public/REPORT/ORTANO2_EMMC/  /testreport/ORTANO2_EMMC/

rsync -r -a -v -e "ssh winson@192.168.100.2" /testreport/ ":/cygdrive/g/Shared\ drives/TestStatus/"

#rsync -r -a -v --delete -e "ssh winson@192.168.100.2" /testreport/ORTANO2_EMMC/ ":/cygdrive/g/Shared\ drives/TestStatus/ORTANO2_EMMC/"

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'

# Remove lock file
rm /tmp/runuploadReport_truelock.file