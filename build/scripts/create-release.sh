#!/bin/bash

cat <<EOF
This will promote the selected hourly-build to stable status.

Please do not run this script unless you know what you're doing.

If you really wanted to run it, pass UPLOAD=1 to this command's environment.

Usage: UPLOAD=1 /psdiag/build/scripts/create-release.sh <hourly-label>

EOF

if [ "x$UPLOAD" = "x" ]
then
  echo "Not doing it"
  exit 1
fi

if [[ $# -eq 0 ]]
then
  exit 1
fi

VERSION=$1

echo "Promoting ${VERSION} as stable build"

curl http://fs2.pensando.io/builds/hourly-diag/1.0-1/releases.tar.gz --output releases.tar.gz
asset-push  -ac assets-colo.pensando.io:9000 hw-repository diag ${VERSION} releases.tar.gz
ret=$?
rm -f releases.tar.gz
exit $?
