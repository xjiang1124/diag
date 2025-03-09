#!/usr/bin/python2

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
#import StringIO
from datetime import datetime
import grpc
import random

import cryptography.x509
from cryptography import utils
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from dice import certificates_pb2
from dice import certificates_pb2_grpc
from dice import random_pb2
from dice import random_pb2_grpc


def parse_args():
    """ Parse command-line arguments """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-k",
        "--client_key",
        required=True,
        help="path to the file containing the client key")
    parser.add_argument(
        "-c",
        "--client_cert",
        required=True,
        help="path to the file containing the client certificates")
    parser.add_argument(
        "-t",
        "--trust_roots",
        required=True,
        help="path to the file containing the trust bundle to verify server certificate")
    parser.add_argument(
        "-b",
        "--backend_url",
        required=True,
        help="comma-separated list of backend URLs")
    parser.add_argument(
        "-s",
        "--store_dir",
        required=False,
        help="directory where to store crypto  material")
    parser.add_argument(
        "-hsm_rn",
        "--hsm_rn",
        action="store_true",
        help="Get RN from HSM")
    parser.add_argument(
        "-n",
        "--rand-bytes",
        required=False,
        help="number of random bytes to fetch")
    parser.add_argument(
        "-sn",
        "--sn",
        required=True,
        help="Serial number")
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
    print("Backend URLs: {}".format(args.backend_url))
    backend_url = url
    if not backend_url:
        print("Must specify signing server url")
        return None, False
    channel = grpc.secure_channel(backend_url, creds, options)
    try:
        grpc.channel_ready_future(channel).result(timeout=10)
        print("Successfully established secure channel to " + backend_url)
    except grpc.FutureTimeoutError:
        print("Timeout. Failed to establish secure channel to " + backend_url)
        return None, False

    return channel, True

def store_cert(store_dir, cert):
    """ Store fetched device certificate in supplied directory """
    with open(os.path.join(store_dir, "uds_csr_der.crt"), "wb") as ek_cert_file:
        ek_cert_file.write(cert)

def csr_pem_to_bytes(csr_pem):
    # Load the CSR from PEM format
    csr = cryptography.x509.load_pem_x509_csr(csr_pem.encode('utf-8'))

    # Convert the CSR to DER format (bytes)
    csr_bytes = csr.public_bytes(serialization.Encoding.DER)

    return csr_bytes

def main():
    """
    1. Create a (public key, private key) pair
                2. Connect to the specified backend using supplied credentials
                3. Issue a request for a certificate and print the result
                """
    args = parse_args()
    pkiServers = args.backend_url
    pkiServerList = pkiServers.split(",")
    print(pkiServerList)
    while pkiServerList:
        listLen = len(pkiServerList)
        id = random.randint(0,listLen-1)
        url = pkiServerList[id]
        pkiServerList.remove(url)
        print(url)
        channel, status = get_channel(args, url)
        if status is False:
            print("Failed to establish a secure channel..")
            continue
        cert_client = certificates_pb2_grpc.CertificatesStub(channel)
        random_client = random_pb2_grpc.RandomStub(channel)


        sample_csr_solarflare = """
-----BEGIN CERTIFICATE REQUEST-----
MIIDbjCCAvQCAQAwgZExJDAiBgNVBAMMG05TOTQ4MC9YNCBJbml0aWFsIERldmlj
ZSBJRDFpMGcGA1UEBRNgMmUxMjg0NzBkMmNmOTU2ZGFkMjRhYjFmZWZmYWQxOTJj
M2RkMDA5OTViN2Q3YjRlZGJmMTJiNTZjMGVjMDBlNjU5NWM5ODExMmZiYTJjNzk2
ODg0NzIwOGMyMTgyMTVhMHYwEAYHKoZIzj0CAQYFK4EEACIDYgAENOTFxxP8tQOg
kiPbre+nmOVsPcX2ru8bsngowxUvQ5gyMeVzd/kyQ1G/goqEgspd6s0duWMWTBWw
gTE25soNG11E0dzYPp8AUWIUvhkbk/LtE8NcmQ2T+OIBmckpU5MmoIIB4TCCAd0G
CSqGSIb3DQEJDjGCAc4wggHKMB0GA1UdDgQWBBQ5bHBk5z2qJnaz58NSbU3kRQfd
8DAOBgNVHQ8BAf8EBAMCAgQwEgYDVR0TAQH/BAgwBgEB/wIBADAbBgNVHSUEFDAS
BgdngQUFBGQGBgdngQUFBGQMMBUGBmeBBQUEBAQLMAkEBwIAD1MAAAAwggEvBgZn
gQUFBAEEggEjMIIBH4AJQU1ELCBJbmMugQlOUzk0ODAvWDSDAQCEAQCmgfwwPQYJ
YIZIAWUDBAICBDDy3vnLgoYHjWX5DrxK26Pv49gOxvc5pjGG5Qqgk+0uI0/a6tGM
UuI5MUyuE0RPyjQwPQYJYIZIAWUDBAICBDC+wCG082jjBpE04BLCtDBwg9OpvdIG
4k5fDYbhPWY2ZVkz7CtBNGWWaBepwgihFxcwPQYJYIZIAWUDBAICBDANub2bWcN0
JJxiRfXCD6YSzAXyUZsOxRXBHdpnzQaQ2A947sMiJRXC7Ru2/YYgHS0wPQYJYIZI
AWUDBAICBDDtjTnEQE/71/WGo/dU1YR9BELGjYBwunaK5FrwXoIZxUwvMq8tNdz9
ZMHqOv0x+yCHAgQDMB4GCisGAQQBgxyCEgYEEDAOMAwGCisGAQQBgxyCEgIwCgYI
KoZIzj0EAwMDaAAwZQIxAKj/Wp0zPSj7QUGkgxtcY5xRcrqc4+fClPJ8+dBSmSBD
wFlEBM3HC5+nfLhempCpaQIwYZWIJAJoTpz0HPvke0HLq31LxpJILUYfF3pnbXPn
+VG80sbs+dSkJOSerRuquvww
-----END CERTIFICATE REQUEST-----
"""

        sample_csr_pensando = """
-----BEGIN CERTIFICATE REQUEST-----
MIIBgzCCAQYCAQAwMzExMC8GA1UEBQwoOTZlMjgxM2Q5NmVlODBkYjg2NDgzOTA0
Y2NhOGQ4NmJlZmZjMTNhODB2MBAGByqGSM49AgEGBSuBBAAiA2IABJQBDNi0kUlF
uQ0NxUuHL7KwgFPo7wpVOQKwNti314Z/ely6QWhCUgTgJfp5mVJ1GMpBifsStO/+
+uaC/2pvQnxo3t8KaGFjLN04K+IA/nZbpNn1DEs+DpAnd9ZHvihgNaBUMFIGCSqG
SIb3DQEJDjFFMEMwHQYDVR0OBBYEFJbigT2W7oDbhkg5BMyo2Gvv/BOoMA4GA1Ud
DwEB/wQEAwICBDASBgNVHRMBAf8ECDAGAQH/AgEAMAwGCCqGSM49BAMDBQADaQAw
ZgIxAI9OKN+BLVBKTQSrxwjojd3j7Of9mVs6TDp1pa5GeVPaBlPGVoCQqFDLmY3Z
st3WMAIxAKPdfWBecA1zlZ+X0D4r5cCbZMJWmCFhrOOYXlAUTXnmjjh0MsfmVVb2
UH+l2kGC/w==
-----END CERTIFICATE REQUEST-----
"""

    if args.hsm_rn == True:
        random_req = random_pb2.GetBytesRequest(Size=int(args.rand_bytes))
        random_resp = random_client.GetBytes(random_req)
        rand_num = binascii.hexlify(random_resp.Bytes)
        print("Fetched {} random bytes:{}".format(args.rand_bytes, rand_num))
        rand_file = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/entropy_{}.txt".format(args.sn)
        fd = open(rand_file, "wb+")
        fd.write(rand_num)
        fd.close()
        print("Fetched {} random bytes".format(args.rand_bytes))
    else:
        #sample_csr_bytes = csr_pem_to_bytes(sample_csr_pensando)

        #with open("/home/diag/diag/asic/asic_src/ip/cosim/tclsh/uds_csr_hex.csr", "r") as file:
        with open("/home/diag/diag/asic/asic_src/ip/cosim/tclsh/uds_csr_der.csr", "r") as file:
            sample_csr_bytes = file.read()

        cert_req = certificates_pb2.CertificateRequest(
            CertificateSigningRequest=sample_csr_bytes)

        cert_resp = cert_client.IssueDICECertificate(cert_req)
        cert = cryptography.x509.load_der_x509_certificate(
            cert_resp.Certificate, default_backend())
        print("Certificate client received: " + str(cert))

        if args.store_dir != None:
            store_cert(args.store_dir, cert_resp.Certificate)

main()
