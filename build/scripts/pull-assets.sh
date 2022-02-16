#!/bin/bash

set -e
#set -x

MINIO_DIR=/psdiag/build/minio

if cmp ${MINIO_DIR}/VERSIONS ${MINIO_DIR}/.VERSIONS.orig
then
    echo "${MINIO_DIR}/VERSIONS same as current. Skipping pull-assets."
    exit 0
fi

echo "Deleting any stale files"
for fname in $(find ${MINIO_DIR}/ -name '*.txt') 
do
  while IFS='' read -r f || [[ -n "$f" ]]; do
    # We use this expresion to remove any trailing "/*"
    # so that /output/*
    # becomes /output
    rm -rf $(echo "$f" | sed -e 's/\/\*\s*$//')
  done < $fname
done

echo "pulling assets"
for fname in $(find ${MINIO_DIR} -name '*.txt') 
do
  name=$(basename $fname .txt)
  version=$(grep "${name}" ${MINIO_DIR}/VERSIONS | awk '{ print $2 }')
  echo asset-pull ${name} ${version}
  asset-pull --bucket hw-repository --asset-name releases.tar.gz ${name} ${version} /dev/stdout | tar xz --owner=`id -u` --group=`id -g`
  echo
done
cp ${MINIO_DIR}/VERSIONS ${MINIO_DIR}/.VERSIONS.orig
