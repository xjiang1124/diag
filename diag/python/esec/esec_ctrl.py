#!/usr/bin/env python

import argparse
import pexpect
import re
import sys
import time
from collections import OrderedDict

sys.path.append("../lib")
sys.path.append("../regression")
import common
from nic_con import nic_con

def parse_args_diag():
    parser = argparse.ArgumentParser(description="Diagnostic inteface", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "-otp_cm_fmt", "--otp_cm_fmt", 
        action='store_true',
        help="Generate OTP CM format file")
    group.add_argument(
        "-enroll_puf", "--enroll_puf", 
        action='store_true',
        help="Enroll PUF")
    group.add_argument(
        "-sign_ek", "--sign_ek", 
        action='store_true',
        help="HSM to sign pub_ek")
    group.add_argument(
        "-gen_otp", "--gen_otp", 
        action='store_true',
        help="Generate OTP binary files")
    group.add_argument(
        "-otp_init", "--otp_init", 
        action='store_true',
        help="OTP init")
    group.add_argument(
        "-esec_prog", "--esec_prog", 
        action='store_true',
        help="OTP init")
    group.add_argument(
        "-cleanup", "--cleanup", 
        action='store_true',
        help="Clean up")
    group.add_argument(
        "-check_uboot", "--check_uboot", 
        action='store_true',
        help="Clean up")

    parser.add_argument(
        "-k", "--client_key",
        default = "certs/client.key.pem",
        help="path to the file containing the client key")
    parser.add_argument(
        "-c",
        "--client_cert",
        default = "certs/client-bundle.cert.pem",
        help="path to the file containing the client certificates")
    parser.add_argument(
        "-t",
        "--trust_roots",
        default = "certs/rootca.cert.pem",
        help="path to the file containing the trust bundle to verify server certificate")
    parser.add_argument(
        "-b",
        "--backend_url",
        default = "enrico.dev.pensando.io:12267",
        help="comma-separated list of backend URLs")

    parser.add_argument(
        "-slot",
        "--slot",
        #required=True,
        help="Slot")
    parser.add_argument(
        "-sn",
        "--sn",
        #required=True,
        help="Serial number")
    parser.add_argument(
        "-pn",
        "--pn",
        #required=True,
        help="Part number")
    parser.add_argument(
        "-mac",
        "--mac",
        #required=True,
        help="MAC address")
    parser.add_argument(
        "-brd_name",
        "--brd_name",
        #required=True,
        help="Product name")
    parser.add_argument(
        "-mtp",
        "--mtp",
        #required=True,
        help="MTP ID")
    parser.add_argument(
        "-sku",
        "--sku",
        default="SKU",
        help="SKU")
    #parser.add_argument(
    #    "-pub_ek",
    #    "--pub_ek",
    #    default="pub_ek.tcl.txt",
    #    help="File with public ek")
    #parser.add_argument(
    #    "-signed_pub_ek",
    #    "--signed_pub_ek",
    #    default="signed_ek.pub.bin",
    #    help="Output file with signed public ek")
    
    return parser.parse_args()

class esec_ctrl:
    def __init__(self):
        self.nic_con = nic_con()

    def create_otp_cm_fmt(self, sn):
        tgt_sn_len = 16
        ret = 0

        fmt_txt = """HW_LOCK_BIT 1
ESEC_SECUREBOOT 1
WATCHDOG 1
ESEC_FW_ENABLE 1
CHIP_TAMPERED 0
PUBCMREVOKED 0x00
DEBUGPROTENCM 0x00F
SERIALNO {}
PUBCM0 <sign_CM0.pk>
PUBCM1 <sign_CM1.pk>
FRKCM0 <encr_CM0.frk>
FRKCM1 <encr_CM1.frk>
TAMP00_CM 0
TAMP01_CM 1
TAMP02_CM 4
TAMP03_CM 0
TAMP04_CM 0
TAMP05_CM 4
TAMP06_CM 0
TAMP07_CM 4
TAMP08_CM 4
TAMP09_CM 4
TAMP10_CM 1
TAMP11_CM 1
TAMP12_CM 4
TAMP13_CM 1
TAMP14_CM 4
TAMP15_CM 1
TAMP16_CM 1
TAMP17_CM 4
TAMP18_CM 4
TAMP19_CM 4
TAMP20_CM 0
TAMP21_CM 0
TAMP22_CM 0
TAMP23_CM 0
TAMP24_CM 0
TAMP25_CM 0
TAMP26_CM 0
TAMP27_CM 0
TAMP28_CM 0
TAMP29_CM 0
TAMP30_CM 0
TAMP31_CM 0
TAMPERFILTERPERIODCM 0x1f
TAMPERFILTERTHRESHOLDCM 0x05
CHIPCERT <chipcert.der>
PRIVEK <ek.sk>"""

        print "=== Creating OTP_content_CM; sn: {} ===".format(sn)

        sn_len = len(sn)
        if sn_len > 16 or sn_len == 0:
            print "Invalid SN lenth: expect less than 16; received {}".format(len(sn))
            ret = -1
        else:
            output = sn.ljust(tgt_sn_len, '0')
            output = "".join("{:02x}".format(ord(c)) for c in output)
            output = "0x"+output
            file_output = fmt_txt.format(output)

            text_file = open("OTP_content_CM.txt", "w")
            text_file.write(file_output)
            text_file.close()

        print "=== Creating OTP_content_CM done"
        return ret

    def enroll_puf(self, sn, slot):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -enroll_puf -sn {} -slot {}".format(sn, slot)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 120)
        common.session_stop(session)

        print "ret:", ret
        return ret

    def sign_ek(self, sn, pn, mac, brd_name, mtp):
        cmd_fmt = "/home/diag/diag/python/esec/scripts/esec_prog.sh -sign_ek -sn {} -pn {} -mac {} -brd_name {} -mtp {}"
        cmd = cmd_fmt.format(sn, pn, mac, brd_name, mtp)
        ret = 0

        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, "SIGNING EK PASSED")
        common.session_stop(session)

        return ret

    def gen_otp(self):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -gen_otp"
        ret = 0

        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, "GEN OTP PASSED")
        common.session_stop(session)

        print ret
        return ret

    def otp_init(self, sn, slot):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -otp_init -sn {} -slot {}".format(sn, slot)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 120)
        common.session_stop(session)

        print "ret:", ret
        return ret

    def esec_prog(self, client_key, client_cert, trust_roots, backend_url, sn, slot, pn, mac, brd_name, mtp, sku):
        self.create_otp_cm_fmt(sn)
        ret = self.enroll_puf(sn, slot)
        if ret != 0:
            print "=== Enroll PUF failed ==="
            return ret

        ret = self.sign_ek(sn, pn, mac, brd_name, mtp)
        if ret != 0:
            print "=== Failed to sign pub_ek ==="
            return ret

        ret = self.gen_otp()
        if ret != 0:
            print "=== Failed to generate OTP binary ==="
            return ret

        ret = self.otp_init(sn, slot)
        if ret != 0:
            print "=== OTP init failed ==="
            return ret

        print "=== ESEC PORG PASSED ==="
        return ret

    def cleanup (self):
        ret = 0
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -cleanup"
        session = common.session_start()
        ret = common.session_cmd(session, cmd)
        common.session_stop(session)
        return ret

    def check_uboot_esec(self, slot):
        ret = 0
        session = common.session_start()
        ret = self.nic_con.enter_uboot(session, slot)
        ret = self.nic_con.conn_uboot(session)
        if ret == -1:
            print "=== Failed to change uboot board rate! ==="
            print "=== MTEST FAILED ==="
            return ret

        self.nic_con.uart_session_stop(session)
        common.session_stop(session)
        return ret


if __name__ == "__main__":
    args = parse_args_diag()
    esec_ctrl = esec_ctrl()

    if args.otp_cm_fmt == True:
        esec_ctrl.create_otp_cm_fmt(args.sn)
        sys.exit()

    if args.enroll_puf == True:
        esec_ctrl.enroll_puf(args.sn, args.slot)
        sys.exit()

    if args.sign_ek == True:
        esec_ctrl.sign_ek(args.sn, args.pn, args.mac, args.brd_name, args.mtp)
        sys.exit()

    if args.gen_otp == True:
        esec_ctrl.gen_otp()
        sys.exit()

    if args.otp_init == True:
        esec_ctrl.otp_init(args.sn, args.slot)
        sys.exit()

    if args.esec_prog == True:
        esec_ctrl.esec_prog(args.client_key, args.client_cert, args.trust_roots, args.backend_url,\
                args.sn, args.slot, args.pn, args.mac, args.brd_name, args.mtp, args.sku)
        sys.exit()

    if args.cleanup == True:
        esec_ctrl.cleanup()
        sys.exit()

    if args.check_uboot == True:
        esec_ctrl.check_uboot_esec(int(args.slot))
        sys.exit()

