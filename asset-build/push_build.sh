#!/bin/bash

set -x

if [ -z $RELEASE ]
then
    echo "RELEASE not set, return"
    exit 0
fi

set +x
echo "**************************************************"
echo " 1/3 Unpack mfg script"
echo "**************************************************"
set -x

mkdir -p /release/unpack/
tar xzf /psdiag/jobd/jobd.tar.gz -C /release/unpack/ --strip-components=1
cp -r /release/unpack /release/${ASIC}_${RELEASE}
rm -r /release/unpack


set +x
echo "**************************************************"
echo " 2/3 Rename diag images"
echo "**************************************************"
set -x

# only rename and do not change anything else, to keep trustability of test results
cd /release/${ASIC}_${RELEASE}
sed -i "s/MTP_ARM64_IMAGE = \".*\.tar\"/MTP_ARM64_IMAGE = \"image_arm64_${ASIC}_${RELEASE}\.tar\"/g" mfg/lib/libmfg_cfg.py
sed -i "s/MTP_AMD64_IMAGE = \".*\.tar\"/MTP_AMD64_IMAGE = \"image_amd64_${ASIC}_${RELEASE}\.tar\"/g" mfg/lib/libmfg_cfg.py
rsync -at --chmod=644 /psdiag/build/images/image_amd64_${ASIC}.tar /release/${ASIC}_${RELEASE}/mfg/release/image_amd64_${ASIC}_${RELEASE}.tar
rsync -at --chmod=644 /psdiag/build/images/image_arm64_${ASIC}.tar /release/${ASIC}_${RELEASE}/mfg/release/image_arm64_${ASIC}_${RELEASE}.tar


set +x
echo "**************************************************"
echo " 3/3 Repack mfg script"
echo "**************************************************"
set -x

echo "Collect image versions"
amd64img=/psdiag/build/images/image_amd64_${ASIC}.tar
arm64img=/psdiag/build/images/image_arm64_${ASIC}.tar
tar xfO ${amd64img} diag/scripts/version.txt | head > /release/${ASIC}_${RELEASE}/DIAG_VERSION
tar xfO ${arm64img} nic.tar.gz | tar xzO nic/fake_root_target/nic/asic_src/ip/cosim/tclsh/.git_rev.tcl > /release/${ASIC}_${RELEASE}/ASIC_VERSION

echo "Collect release targets"
grep ${ASIC} /psdiag/test/jobs.cfg | grep -v "#" | awk -F"\t" '{$(NF-1)=$(NF-2)=""; OFS="\t"; $1=$1; print}' > /release/${ASIC}_${RELEASE}/TARGETS

echo "Collect release changelist"
cp /psdiag/CHANGES.md /release/${ASIC}_${RELEASE}/CHANGES.md
if [[ $(wc -l /release/${ASIC}_${RELEASE}/CHANGES.md) < 1 ]]; then
    echo "CHANGES.md looks empty. Aborting release"
    exit -1
fi
/psdiag/asset-build/generate_diff.sh > /release/${ASIC}_${RELEASE}/GITLOG

ls -l /release/*
cd /release; asset-push --remote-name ${ASIC}_${RELEASE}.tar.gz builds hourly-diag ${RELEASE} ${ASIC}_${RELEASE}

set +x
echo
echo "---------------------"
echo "${RELEASE} RELEASE NOTES"
echo "---------------------"
echo
echo "DIAG VERSION"
echo "============"
cat /release/${ASIC}_${RELEASE}/DIAG_VERSION
echo
echo "ASIC VERSION"
echo "============"
cat /release/${ASIC}_${RELEASE}/ASIC_VERSION
echo
echo "TARGETS"
echo "======="
cat /release/${ASIC}_${RELEASE}/TARGETS
echo
echo "CHANGES"
echo "======="
cat /release/${ASIC}_${RELEASE}/CHANGES.md
cat /release/${ASIC}_${RELEASE}/GITLOG
echo
echo "Release available at /vol/builds/hourly-diag/${RELEASE}"
