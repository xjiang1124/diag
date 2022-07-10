#!/usr/bin/python

# The "cryptography" library must be installed:
# sudo pip install cryptography
#
# Set PYTHONPATH to pki/src/manufacturing/svc/api/generated/python

"""
This module is a sample gRPC client for the svc server.
The svc server is used to issue certificates to NAPLES cards at manufacturing time.
This code will eventually be imported in MTP software to integrate with manufacturing flow.
"""

import argparse
import binascii
import struct
import os.path
import StringIO
from datetime import datetime
import grpc
import random

import cryptography.x509
from cryptography import utils
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

import certificates_pb2
import certificates_pb2_grpc
import keys_pb2
import keys_pb2_grpc
import random_pb2
import random_pb2_grpc


def parse_args():
    """ Parse command-line arguments """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-k",
        "--client-key",
        required=True,
        help="path to the file containing the client key")
    parser.add_argument(
        "-c",
        "--client-cert",
        required=True,
        help="path to the file containing the client certificates")
    parser.add_argument(
        "-t",
        "--trust-roots",
        required=True,
        help="path to the file containing the trust bundle to verify server certificate")
    parser.add_argument(
        "-b",
        "--backend-url",
        required=True,
        help="comma-separated list of backend URLs")
    parser.add_argument(
        "-s",
        "--store-dir",
        required=False,
        help="directory where to store crypto  material")
    parser.add_argument(
        "-n",
        "--rand-bytes",
        required=False,
        help="number of random bytes to fetch")
    return parser.parse_args()


def get_credentials(args):
    """ Return credentials to open a TLS connection to the backend """
    # read in key and certificate
    with open(args.client_key, 'rb') as file_hdl:
        private_key = file_hdl.read()
    with open(args.client_cert, 'rb') as file_hdl:
        client_cert = file_hdl.read()
    with open(args.trust_roots, 'rb') as file_hdl:
        trust_roots = file_hdl.read()

    credentials = grpc.ssl_channel_credentials(
        private_key=private_key,
        certificate_chain=client_cert,
        root_certificates=trust_roots)

    return credentials

def get_channel(args, url):
    """ Open a connection to the backend and return the corresponding API client """
    creds = get_credentials(args)
    options = [('grpc.ssl_target_name_override', "pki-srv.pensando.io",),
               ('grpc.lb_policy_name', "pick_first",)]
    print "Backend URLs: {}".format(args.backend_url)
    backend_url = url
    if not backend_url:
        print "Must specify signing server url"
        return None, False
    channel = grpc.secure_channel(backend_url, creds, options)
    try:
        grpc.channel_ready_future(channel).result(timeout=10)
        print("Successfully established secure channel to " + backend_url)
    except Exception as grpc.FutureTimeoutError:
        print("Timeout. Failed to establish secure channel to " + backend_url)
        return None, False

    return channel, True

def fix_endianness(hex_data):
    """ Convert the endianness of the raw byte string read from the chip """
    if len(hex_data) % 4 != 0:
        return None

    result = StringIO.StringIO()
    data = binascii.unhexlify(hex_data)
    for i in range(0, len(data), 4):
        result.write("%08X" % struct.unpack("<I", data[i:i+4]))

    return result.getvalue()

def decode_ecdsa_hex_public_key(pk, curve):
    """ Decodes a raw ECDSA public key in hex format and returns the corresponding EllipticCurvePublicKey object """
    # Expected hex key length (bytes) = field size (bits) / 8 * 2 hex digits per byte * 2 coordinates
    # for SECP384 we expect 384 / 8 * 2 * 2 = 192 hex digits
    if len(pk) != curve.key_size / 8 * 2 * 2:
        return None

    pk_bytes = pk.decode('hex')
    x = utils.int_from_bytes(pk_bytes[0:len(pk_bytes)/2], 'big')
    y = utils.int_from_bytes(pk_bytes[len(pk_bytes)/2:], 'big')
    return ec.EllipticCurvePublicNumbers(x, y, curve).public_key(default_backend())

def store_keys(store_dir, cert, key_set):
    """ Store fetched EK certificate and manufacturing keys in supplied directory """
    with open(os.path.join(store_dir, "ek_cert.der"), "wb") as ek_cert_file:
        ek_cert_file.write(cert)

    with open(os.path.join(store_dir, "sign_CM0.pk"), "wb") as sign_cm0_file:
        sign_cm0_file.write(key_set.ChipManufacturerPublicKey0)
    with open(os.path.join(store_dir, "sign_SM0.pk"), "wb") as sign_sm0_file:
        sign_sm0_file.write(key_set.SystemManufacturerPublicKey0)
    with open(os.path.join(store_dir, "sign_CM1.pk"), "wb") as sign_cm1_file:
        sign_cm1_file.write(key_set.ChipManufacturerPublicKey1)
    with open(os.path.join(store_dir, "sign_SM1.pk"), "wb") as sign_sm1_file:
        sign_sm1_file.write(key_set.SystemManufacturerPublicKey1)

    with open(os.path.join(store_dir, "encr_CM0.frk"), "wb") as encr_cm0_file:
        encr_cm0_file.write(key_set.ESecureFirmwareRootKey0)
    with open(os.path.join(store_dir, "encr_SM0.frk"), "wb") as encr_sm0_file:
        encr_sm0_file.write(key_set.HostFirmwareRootKey0)
    with open(os.path.join(store_dir, "encr_CM1.frk"), "wb") as encr_cm1_file:
        encr_cm1_file.write(key_set.ESecureFirmwareRootKey1)
    with open(os.path.join(store_dir, "encr_SM1.frk"), "wb") as encr_sm1_file:
        encr_sm1_file.write(key_set.HostFirmwareRootKey1)

def main():
    """
    1. Create a (public key, private key) pair
                2. Connect to the specified backend using supplied credentials
                3. Issue a request for a certificate and print the result
                """
    args = parse_args()
    pkiServers = args.backend_url
    pkiServerList = pkiServers.split(",")
    print pkiServerList
    while pkiServerList:
        listLen = len(pkiServerList)
        id = random.randint(0,listLen-1)
        url = pkiServerList[id]
        pkiServerList.remove(url)
        print url
        channel, status = get_channel(args, url)
        if status is False:
            print "Failed to establish a secure channel.."
            continue
        cert_client = certificates_pb2_grpc.CertificatesStub(channel)
        keys_client = keys_pb2_grpc.KeysStub(channel)
        random_client = random_pb2_grpc.RandomStub(channel)

        # Sample hardcoded public keys:
        #    barco_sample_pub_ek_hex = "6da4c7ee1f9776bc0958a6b6f5d11fee30a5f9296786a2e205e74eeae53397e11221f7592c9d51c0d2ee85f37a2a553fe71ac47a73addfeba80260a5ebc0100a8600ff53900983d1f08ad1fb066c7f908be01697109f01e469f504c40aa43b96"
        #    sample_pub_ek_hex = "AB5DA8AC20FF823C1D7B7F97AC225A58CF9BEE7ADFA38D52A189C40BF54199FBB88D5E5E8DC01CB02F47535FCDA48FFBEA16082C5CFD57835EF08E06F7CD4E6726F5F91EA1F9AED9E87704C581538F94858E9FE6441C6C8FD12D52C84A009175"

        # this is an EK as it got read out of the chip
        sample_pub_ek_hex_raw = "AB5DA8AC20FF823C1D7B7F97AC225A58CF9BEE7ADFA38D52A189C40BF54199FBB88D5E5E8DC01CB02F47535FCDA48FFBEA16082C5CFD57835EF08E06F7CD4E6726F5F91EA1F9AED9E87704C581538F94858E9FE6441C6C8FD12D52C84A009175"
        # convert from big endian to little endian
        sample_pub_ek_hex = fix_endianness(sample_pub_ek_hex_raw)
        # decode to python object and validate
        sample_pub_ek = decode_ecdsa_hex_public_key(sample_pub_ek_hex, ec.SECP384R1())
        #convert to DER
        sample_pub_ek_der = sample_pub_ek.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)

        cert_req = certificates_pb2.EKCertificateRequest(
            PublicEK=sample_pub_ek_der,
            ProductName="NAPLES",
            SerialNumber="0123456789xABCDEF",
            PrimaryMACAddress="00:AE:CD:00:00:00",
            PartNumber="NAPLES100RevA",
            ManufacturingDate=str(datetime.utcnow()),
            SKU="XXXYYYZZZ",
            MTPID="FLEXABC")

        try:
            cert_resp = cert_client.IssueEKCertificate(cert_req, timeout=10)
        except Exception as e:
            print "caught an exception", e
            continue
        cert = cryptography.x509.load_der_x509_certificate(
            cert_resp.Certificate, default_backend())
        print "Certificate client received: " + str(cert)

        keys_req = keys_pb2.FetchKeySetRequest(ID="v1")
        keys_resp = keys_client.FetchKeySet(keys_req)
        print "Fetched keys"

        if args.store_dir != None:
            store_keys(args.store_dir, cert_resp.Certificate, keys_resp)

        if args.rand_bytes != None:
            random_req = random_pb2.GetBytesRequest(Size=int(args.rand_bytes))
            random_resp = random_client.GetBytes(random_req)
            print "Fetched {} random bytes:{}".format(args.rand_bytes, binascii.hexlify(random_resp.Bytes))
        break

#main()
