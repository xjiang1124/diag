#!/usr/bin/python

# The "cryptography" library must be installed:
# sudo pip install cryptography
#
# Set PYTHONPATH to pki/src/manufacturing/certsvc/api/generated/python

"""
This module is a sample gRPC client for the certsvc server.
The certsvc server is used to issue certificates to NAPLES cards at manufacturing time.
This code will eventually be imported in MTP software to integrate with manufacturing flow.
"""

import argparse
import binascii
from datetime import datetime
import grpc
import random
import sys

import cryptography.x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

import certificates_pb2
import certificates_pb2_grpc
import keys_pb2
import keys_pb2_grpc

import random_pb2
import random_pb2_grpc

#sys.path.insert(0, 'src/manufacturing/svc/client')
import client as cl

def parse_args_diag():
    """ Parse command-line arguments """
    parser = argparse.ArgumentParser(description="Key program inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "-sign_ek",
        "--sign_ek",
        action="store_true",
        help="Sign EK")

    group.add_argument(
        "-hsm_rn",
        "--hsm_rn",
        action="store_true",
        help="Get RN from HSM")

    parser.add_argument(
        "-k", 
        "--client-key", 
        default="certs/client.key.pem",
        #required=True,
        help="path to the file containing the client key")
    parser.add_argument(
        "-c",
        "--client-cert",
        default="certs/client-bundle.cert.pem",
        #required=True,
        help="path to the file containing the client certificates")
    parser.add_argument(
        "-t",
        "--trust-roots",
        default="certs/rootca.cert.pem",
        #required=True,
        help="path to the file containing the trust bundle to verify server certificate")
    parser.add_argument(
        "-b",
        "--backend-url",
        default="192.168.67.213:12266#192.168.67.214:12266",
        #required=True,
        help="comma-separated list of backend URLs")
    parser.add_argument(
        "-s",
        "--store-dir",
        required=False,
        help="directory where to store crypto  material")

    parser.add_argument(
        "-sn",
        "--sn",
        required=True,
        help="Serial number")
    parser.add_argument(
        "-pn",
        "--pn",
        required=True,
        help="Part number")
    parser.add_argument(
        "-mac",
        "--mac",
        required=True,
        help="MAC address")
    parser.add_argument(
        "-pdn",
        "--pd_name",
        required=True,
        help="Product name")
    parser.add_argument(
        "-mid",
        "--mtp_id",
        required=True,
        help="mtp_id")
    parser.add_argument(
        "-sku",
        "--sku",
        default="SKU",
        help="SKU")
    parser.add_argument(
        "-id",
        "--id",
        default="v1",
        help="Key ID version")
    parser.add_argument(
        "-n",
        "--rand-bytes",
        required=False,
        default="256",
        help="number of random bytes to fetch")
    return parser.parse_args()

try:
    args = parse_args_diag()
    pkiServers = args.backend_url
    # replace '#' with ',' in backend_url list
    pkiServers =  pkiServers.replace('#', ',')
    pkiServerList = pkiServers.split(",")
    print pkiServerList
    while pkiServerList:
        listLen = len(pkiServerList)
        id = random.randint(0,listLen-1)
        url = pkiServerList[id]
        pkiServerList.remove(url)
        print url
        channel, status = cl.get_channel(args, url)
        if status is False:
            print "Failed to establish a secure channel.."
            continue
        cert_client = certificates_pb2_grpc.CertificatesStub(channel)
        keys_client = keys_pb2_grpc.KeysStub(channel)
        random_client = random_pb2_grpc.RandomStub(channel)
    
        #hsm_client = cl.get_client(args)
        #keys_client = keys_pb2_grpc.KeysStub(
    
        if args.hsm_rn == True:
            # Get RN from HSM
            random_req = random_pb2.GetBytesRequest(Size=int(args.rand_bytes))
            random_resp = random_client.GetBytes(random_req)
            rand_num = binascii.hexlify(random_resp.Bytes)
            print "Fetched {} random bytes:{}".format(args.rand_bytes, rand_num)
            rand_file = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/rand_sn_{}.txt".format(args.sn)
            fd = open(rand_file, "w+")
            fd.write(rand_num)
            fd.close()
        else:
            pub_ek_raw = open("pub_ek.tcl.txt", "r").read()

            pub_ek = cl.fix_endianness(pub_ek_raw)

            public_key = cl.decode_ecdsa_hex_public_key(pub_ek, ec.SECP384R1())
            der_public_key = public_key.public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo)

            req = certificates_pb2.EKCertificateRequest(
                PublicEK=der_public_key,
                ProductName=args.pd_name,
                SerialNumber=args.sn,
                PrimaryMACAddress=args.mac,
                PartNumber=args.pn,
                ManufacturingDate=str(datetime.utcnow()),
                SKU=args.sku,
                MTPID=args.mtp_id)

            try:
                cert_resp = cert_client.IssueEKCertificate(req, timeout=10)
            except Exception as e:
                print "caught an exception", e
                continue
            cert = cryptography.x509.load_der_x509_certificate(
                cert_resp.Certificate, default_backend())

            data=cert.public_bytes(encoding=serialization.Encoding.DER)
            newfile=open('./signed_ek.pub.bin','wb')
            newfile.write(data)
            newfile.close()

            keys_req = keys_pb2.FetchKeySetRequest(ID=args.id)
            keys_resp = keys_client.FetchKeySet(keys_req)
            print "Fetched keys"

            if args.store_dir != None:
                cl.store_keys(args.store_dir, cert_resp.Certificate, keys_resp)

        print "PKI PASSED"
        break

except Exception as e:
    print e
    print "PKI FAILED"


