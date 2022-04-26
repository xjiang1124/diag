#!/usr/bin/env bash
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

START=$(date +%s);

echo "Log Location should be: [ $SCRIPTLOG ]"
echo "My Currently Dir ($DATE): $_mydir"

#- Ensure User Environment Set -#
. ${HOME}/.profile

whoami

printenv

export PATH=$PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/usr/sbin:/sbin:/usr/bin:/bin

printenv

su - mfg -c printenv

#su - mfg -c sync

#cd $_mydir

#su - mfg -c sync

#su - mfg -c pwd

#su - mfg -c cd $_mydir | $_mydir/RunTest.py

#sleep 10m

sudo -u mfg -- bash -c "cd $_mydir; $_mydir/RunTest.py"

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'