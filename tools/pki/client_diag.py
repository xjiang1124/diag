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
from datetime import datetime
import grpc
import sys

import cryptography.x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

import certificates_pb2
import certificates_pb2_grpc

#sys.path.insert(0, 'src/manufacturing/certsvc/client')
import client as cl

def parse_args_diag():
    """ Parse command-line arguments """
    parser = argparse.ArgumentParser(description="Key program inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-k", "--client-key", required=True,
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
        "-pub_ek",
        "--pub_ek",
        default="pub_ek.tcl.txt",
        help="File with public ek")
    parser.add_argument(
        "-signed_pub_ek",
        "--signed_pub_ek",
        default="signed_ek.pub.bin",
        help="Output file with signed public ek")

    return parser.parse_args()

args = parse_args_diag()
hsm_client = cl.get_client(args)

pub_ek_raw = open(args.pub_ek, "r").read()

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

resp = hsm_client.IssueEKCertificate(req)
cert = cryptography.x509.load_der_x509_certificate(
    resp.Certificate, default_backend())

data=cert.public_bytes(encoding=serialization.Encoding.DER)
newfile=open(args.signed_pub_ek,'wb')
newfile.write(data)
newfile.close()
