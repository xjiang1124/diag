#!/usr/bin/env python

import argparse
import os
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
    group.add_argument(
        "-ek_crc", "--ek_crc", 
        action='store_true',
        help="Calculate CRC32 of signed EK")
    group.add_argument(
        "-ek_check", "--ek_check", 
        action='store_true',
        help="Validate signed EK")
    group.add_argument(
        "-img_prog", "--img_prog", 
        action='store_true',
        help="Program QSPI images")
    group.add_argument(
        "-key_prog_all", "--key_prog_all", 
        action='store_true',
        help="Quick path to program secure key")
    group.add_argument(
        "-boot_test", "--boot_test", 
        action='store_true',
        help="Post check after key programming")
    group.add_argument(
        "-show_sts", "--show_sts", 
        action='store_true',
        help="Show ESEC related info")
    group.add_argument(
        "-efuse_test", "--efuse_test", 
        action='store_true',
        help="Test efuse by burning bit[127]")

    #======================
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
        default = "192.168.67.213:12266#192.168.67.214:12266",
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
    parser.add_argument(
        "-post_check",
        "--post_check",
        action='store_true',
        help="Uboot post key programming check")

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

    def sign_ek(self, sn, pn, mac, brd_name, mtp, client_key, client_cert, trust_roots, backend_url):
        cmd_fmt = "/home/diag/diag/python/esec/scripts/esec_prog.sh -sign_ek -sn {} -pn {} -mac {} -brd_name {} -mtp {} -k {} -c {} -t {} -b {}"
        ret = 0
        num_retry = 3

        url_list = backend_url.split("#")
        for url in url_list:
            cmd = cmd_fmt.format(sn, pn, mac, brd_name, mtp, client_key, client_cert, trust_roots, url)
            print cmd

            for retry in range(num_retry):
                print url, "signing EK #", retry
                session = common.session_start()
                ret = common.session_cmd_pass_multi(session, cmd, ["PKI PASSED", "SIGNING EK PASSED"])
                common.session_stop(session)
                if ret == 0:
                    break
                time.sleep(5)
            if ret == 0:
                break

        print "ret:", ret
        return ret

    def sign_ek_crc(self):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -ek_crc"
        ret = 0

        session = common.session_start()
        session.sendline(cmd)
        session.expect("diag@MTP.*\$")

        ma = re.compile(r".*([a-fA-F\d]{8}).*")
        src_str = "".join(session.before.splitlines())
        result = ma.match(src_str)
        if result == None:
            print "CRC32 not found"
            ret = -1
        else:
            crc32_ek = result.group(1)
            print "CRC32 calculated:", crc32_ek
            ret = 0

        common.session_stop(session)

        return [ret, crc32_ek]

    def ek_check(self):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -ek_check"
        ret = 0

        session = common.session_start()
        session.sendline(cmd)
        session.expect("diag@MTP.*\$")

        if "Signature Algorithm: ecdsa-with-SHA384" in session.before:
            print "Signed EK validated"
            ret = 0
        else:
            print "Failed to validate signed EK"
            ret = -1

        common.session_stop(session)

        return ret

    def gen_otp(self):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -gen_otp"
        ret = 0

        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, "GEN OTP PASSED")
        common.session_stop(session)

        return ret

    def otp_init(self, sn, slot):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -otp_init -sn {} -slot {}".format(sn, slot)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 120)
        common.session_stop(session)

        return ret

    def boot_test(self, sn, slot):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -post_check -sn {} -slot {}".format(sn, slot)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 300)
        common.session_stop(session)

        return ret

    def key_prog_all(self, sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url):
        os.chdir("/home/diag/diag/scripts/asic/")
        cmd = "tclsh /home/diag/diag/scripts/asic/esec_prog.tcl -stage esec_all\
            -sn {} -slot {} -pn \"{}\" -mac {} -mtp {}\
            -client_key \"{}\" -client_cert \"{}\" -trust_roots \"{}\" -backend_url \"{}\"".\
            format(sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url)
        print cmd
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 300)
        common.session_stop(session)
        return ret

    def key_prog_all_pac(self, sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url):
        os.chdir("/home/diag/diag/scripts/asic/")
        cmd = "tclsh /home/diag/diag/scripts/asic/esec_prog.tcl -stage esec_all_pac\
            -sn {} -slot {} -pn \"{}\" -mac {} -mtp {}\
            -client_key \"{}\" -client_cert \"{}\" -trust_roots \"{}\" -backend_url \"{}\"".\
            format(sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url)
        print cmd
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 600)
        common.session_stop(session)
        return ret

    def show_status(self, sn, slot):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -show_sts -sn {} -slot {}".format(sn, slot)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 300)
        common.session_stop(session)

        return ret

    def esec_prog(self, client_key, client_cert, trust_roots, backend_url, sn, slot, pn, mac, brd_name, mtp, sku):
        self.create_otp_cm_fmt(sn)
        numRetry = 3

        for retry in range(numRetry):
            print "=== ESEC PROG #{}".format(retry)

            # Disable legacy way
            if 0:
                ret = self.enroll_puf(sn, slot)
                if ret != 0:
                    print "=== Enroll PUF failed ==="
                    print "=== ESEC PROG FAILED ==="
                    return ret

                ret = self.sign_ek(sn, pn, mac, brd_name, mtp, client_key, client_cert, trust_roots, backend_url)
                if ret != 0:
                    print "=== Failed to sign pub_ek ==="
                    print "=== ESEC PROG FAILED ==="
                    return ret

                ret = self.ek_check()
                if ret != 0:
                    print "=== Failed to validate signed EK ==="
                    print "=== ESEC PROG FAILED ==="
                    return ret

                [ret, crc32_ek] = self.sign_ek_crc()
                if ret != 0:
                    print "=== Failed to calculated CRC32 of signed EK ==="
                    print "=== ESEC PROG FAILED ==="
                    return ret

                ret = self.gen_otp()
                if ret != 0:
                    print "=== Failed to generate OTP binary ==="
                    print "=== ESEC PROG FAILED ==="
                    return ret

                ret = self.otp_init(sn, slot)
                if ret != 0:
                    print "=== OTP init failed ==="
                    print "=== ESEC PROG FAILED ==="
                    return ret

                ret = self.boot_test(sn, slot)
                if ret != 0:
                    # Enter retry
                    print "=== Bad OTP init ==="
                    print "=== Post boot test failed ==="
                    print "Power cycle slot #{}".format(slot)
                    self.nic_con.power_cycle_multi(115200, slot, 10)
                else:
                    # Move forward
                    break

            ret = self.key_prog_all(sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url)
            if ret != 0:
                print "=== ESEC PROG FAILED ==="
                return ret
            else:
                # Move forward
                break

        file1 = open("/home/diag/diag/tools/pki/crc32_ek.bin", "r+")
        crc32_ek = file1.read()
        crc32_ek = crc32_ek[:-1]
        print("crc32_ek:", crc32_ek)
        file1.close()

        if ret != 0:
            print "=== ESEC PROG FAILED ==="
            return ret
        else:
            print "=== OTP PROG validated #{} ===".format(retry-1)

        print ("slot:", slot)
        [ret, crc32_ek_uboot] = self.check_uboot_esec(int(slot))
        if ret != 0:
            print "=== Failed to check ESEC in uboot ==="
            print "=== ESEC PROG FAILED ==="
            return ret

        if crc32_ek != crc32_ek_uboot:
            print "CRC32 cross check failed; Caculated:", crc32_ek, "Uboot:", crc32_ek_uboot 
            print "=== ESEC PROG FAILED ==="
            return -1

        ret = self.efuse_test(int(slot))
        if ret != 0:
            print "=== Efuse test failed ==="


        if ret == 0:
            print "=== ESEC PROG/VALICATION PASSED ==="
        else:
            print "=== ESEC PROG FAILED ==="

        return ret

    def cleanup (self):
        ret = 0
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -cleanup"
        session = common.session_start()
        ret = common.session_cmd(session, cmd)
        common.session_stop(session)
        return ret

    def check_uboot_esec(self, slot, post_check=False):
        ret = 0
        crc32_ek = ""
        session = common.session_start()
        ret = self.nic_con.enter_uboot_esec(session, slot)
        if ret != 0:
            print "Failed to enter uboot"
            return ret
        ret = self.nic_con.conn_uboot(session)
        if ret != 0:
            print "Failed to connect uboot"
            return ret

        self.nic_con.uart_session_cmd(session, "esec read_serial_number", 30, "Capri# ")
        self.nic_con.uart_session_cmd(session, "esec read_tamper_status", 30, "Capri# ")
        self.nic_con.uart_session_cmd(session, "esec read_boot_status", 30, "Capri# ")
        self.nic_con.uart_session_cmd(session, "esec read_chip_cert crc32", 30, "Capri# ")

        # Find CRC32
        session.sendline("esec read_chip_cert crc32")
        session.expect("Capri# ")
        ma = re.compile(r".*0x([a-fA-F0-9]+).*")
        src_str = "".join(session.before.splitlines())
        result = ma.match(src_str)
        if result == None:
            print "CRC32 not found"
            ret = -1
        else:
            print "EK validated"
            crc32_ek = result.group(1)
            ret = 0

        time.sleep(2)
        self.nic_con.uart_session_stop(session)
        common.session_stop(session)
        return [ret, crc32_ek]

    def img_prog(self, slot):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -img_prog -slot {}".format(slot)
        ret = 0
        pass_sign = "ESEC PROG PASSED"

        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 240)
        common.session_stop(session)

        if ret == 0:
            print "IMG PROG PASSED"
        else:
            print "IMG PROG FAILED"

        return ret

    def efuse_test(self, slot):
        self.nic_con.power_cycle_multi(115200, str(slot), 5)
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -efuse_test -slot {}".format(slot)
        ret = 0

        pass_sign = "ESEC PROG PASSED"

        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 180)
        common.session_stop(session)

        if ret == 0:
            print "EFUSE TEST PASSED"
        else:
            print "EFUSE TEST FAILED"

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
        esec_ctrl.sign_ek(args.sn, args.pn, args.mac, args.brd_name, args.mtp, args.client_key, args.client_cert, args.trust_roots, args.backend_url)
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
        esec_ctrl.check_uboot_esec(int(args.slot), args.post_check)
        sys.exit()

    if args.ek_crc == True:
        esec_ctrl.sign_ek_crc()
        sys.exit()

    if args.ek_check == True:
        esec_ctrl.ek_check()
        sys.exit()

    if args.key_prog_all == True:
        esec_ctrl.key_prog_all(int(args.slot), args.sn, args.pn, args.mac, args.mtp, args.client_key,\
                args.client_cert, args.trust_roots, args.backend_url)
        sys.exit()

    if args.img_prog == True:
        esec_ctrl.img_prog(int(args.slot))
        sys.exit()

    if args.boot_test == True:
        esec_ctrl.boot_test(args.sn, args.slot)
 
    if args.show_sts == True:
        esec_ctrl.show_status(args.sn, args.slot)
        sys.exit()

    if args.efuse_test == True:
        esec_ctrl.efuse_test(int(args.slot))
        sys.exit()

    print "Invalid input"
