#!/bin/bash
set -x 

DATE=`date +%d-%m-%y` 
now=$(date +"%b%d-%Y-%H%M%S")
#_mydir="`pwd`"
_mydir="/home/mfg/winson"
echo "My Currently Dir ($DATE): $_mydir"

SCRIPTLOG=$_mydir/LOG/log_$DATE.log
exec > >(tee -a $SCRIPTLOG)
exec 2>&1

echo "Log Location should be: [ $SCRIPTLOG ]"
echo "My Currently Dir ($DATE): $_mydir"

date

free -h

date

w

date

#ps -eo pmem,pcpu,rss,vsize,args | sort -k 1 -n -r | less

#date

pstree -p

date

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'