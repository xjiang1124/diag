if [ -z $RELEASE ]
then
    echo "RELEASE not set, return"
    exit 0
fi
set -x
ls -l /psdiag/fw.tar
cd /; asset-push --remote-name fw_${RELEASE}.tar.gz builds hourly-diag ${RELEASE} /psdiag/fw.tar