#!/usr/bin/env python

""" Copyright (c) 2017 Barco Silex. All Rights reserved """

import sys, os
from oscrypto import asymmetric
from certbuilder import CertificateBuilder, pem_armor_certificate
from asn1crypto.keys import *
from asn1crypto.core import *
from asn1crypto import util

script_path = os.path.abspath(os.path.dirname(__file__))

privEK = '3CA6EDC0DBD20F3C33A2468A5A485359FD3DAC42EBCC86540685BD0BE2E3AA46E59B038F7390DEF2FB9D066F428015E3'
pubEK  = '6da4c7ee1f9776bc0958a6b6f5d11fee30a5f9296786a2e205e74eeae53397e11221f7592c9d51c0d2ee85f37a2a553f' \
         'e71ac47a73addfeba80260a5ebc0100a8600ff53900983d1f08ad1fb066c7f908be01697109f01e469f504c40aa43b96'

private_key = PrivateKeyInfo({
    'version' : 0,
    'private_key_algorithm': PrivateKeyAlgorithm({
        'algorithm': u'ec',
        'parameters': ECDomainParameters(
            name=u'named',
            value=u'secp384r1'
        )
    }),
    'private_key': ECPrivateKey({
        'version' : 1,
        'private_key' : int(privEK, 16)
    })
})

public_key = PublicKeyInfo({
    'algorithm': PublicKeyAlgorithm({
        'algorithm': u'ec',
        'parameters': ECDomainParameters(
            name=u'named',
            value=u'secp384r1'
        )
    }),
    'public_key': pubEK.decode('hex')
})

builder = CertificateBuilder(
    {
        u'country_name': u'BE',
        u'locality_name': u'Ottignies-Louvain-la-neuve',
        u'organization_name': u'Barco-Silex',
    },
    public_key
)

#HACK: In real use certificate would not be self signed.
builder.self_signed = True
builder.hash_algo = u'sha512'
certificate = builder.build(private_key)

cert_file = script_path + '/workdir/chipcert.der'
print('Writing DER encoded certificate to {0}'.format(cert_file))
with open(cert_file, 'wb') as f:
    f.write(certificate.dump())
    print('HACK: truncating CHIPCERT file to 1412 bytes as hardcoded in utils.py')
    f.truncate(1412)
