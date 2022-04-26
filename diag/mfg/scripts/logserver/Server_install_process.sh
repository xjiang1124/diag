#!/bin/bash
set -x 



DATE=`date +%d-%m-%y` 
now=$(date +"%b%d-%Y-%H%M%S")
_mydir="`pwd`"
#_mydir="/home/mfg/logserver"
echo "My Currently Dir ($DATE): $_mydir"

SCRIPTLOG=$_mydir/LOG/log_$now.log
exec > >(tee -i $SCRIPTLOG)
exec 2>&1

echo "Log Location should be: [ $SCRIPTLOG ]"
echo "My Currently Dir ($DATE): $_mydir"

#exit 0

# Exit if /tmp/lock.file exists
[ -f /tmp/server_install_process.file ] && exit

# Create lock file, sleep 1 sec and verify lock
echo $$ > /tmp/server_install_process.file
sleep 1
[ "x$(cat /tmp/server_install_process.file)" == "x"$$ ] || exit

SWNames=(
net-tools
python
curl
)

installModule()
{
echo "install SW: $1"
apt install $1 
}

START=$(date +%s);

echo Script: server_install_process.sh

for name in "${SWNames[@]}";
do 
        runReportModule $name $_mydir
done

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'

# Remove lock file
rm /tmp/server_install_process.file