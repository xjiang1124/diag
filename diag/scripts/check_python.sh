#!/usr/bin/bash

if test -d "/usr/local/lib/python2.7/dist-packages/cryptography-2.2.2.dist-info"; then
    echo "MTP is read for SWI"
    exit 0
fi
echo "MTP is NOT read for SWI"
exit 1
