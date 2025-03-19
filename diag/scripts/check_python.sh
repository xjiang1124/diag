#!/usr/bin/bash

need_update=0
if test -d "/usr/local/lib/python2.7/dist-packages/cryptography-2.2.2.dist-info"; then
    echo "MTP has right cryptography package installed"
else
    need_update=1
fi

if test -d "/usr/local/lib/python2.7/dist-packages/asn1crypto"; then
    echo "MTP has asn1crypto package installed"
else
    need_update=1
fi

if [ $need_update -eq 0 ]; then
    echo "MTP is ready for SWI"
    exit 0
else
    echo "MTP is NOT ready for SWI"
    exit 1
fi
