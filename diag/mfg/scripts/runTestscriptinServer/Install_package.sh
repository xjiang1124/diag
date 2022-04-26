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

InstallPythonModule()
{
echo
echo "Install Module From Config File: $1"
python -m pip install $1
python3 -m pip install $1
#sudo -u mfg -- bash -c "python -m pip install $1"
#sudo -u mfg -- bash -c "python3 -m pip install $1"
}

whoami

apt-get update -y
apt-get upgrade -y
apt-get install -y python2
apt-get install -y python3
apt-get install -y python2-dev
apt-get install -y python3-dev
apt-get install -y python2-pip
apt-get install -y python3-pip
apt-get install -y libgpgme-dev
apt-get install -y python2-gpg
apt-get install -y python3-gpg

python get-pip.py

python -m pip install --upgrade pip setuptools wheel
python3 -m pip install --upgrade pip setuptools wheel

#apt-get install -y mysql-connector-python

python -m pip uninstall mysql-connector -y
python3 -m pip uninstall mysql-connector -y
python -m pip uninstall mysql-connector-python -y
python3 -m pip uninstall mysql-connector-python -y

PackageNames=(
cffi
cmdline
cryptography
docutils
ecdsa
enum34
futures
mpu
mysql-connector-python
numpy
openpyxl
oyaml
pandas
pexpect
protobuf
ptyprocess
pycparser
PyYAML
six
statistics
unidecode
)

for name in "${PackageNames[@]}";
do 
        InstallPythonModule $name
done

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'