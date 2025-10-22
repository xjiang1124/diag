#!/usr/bin/env python2.7

import argparse
import os
import pexpect
import re
import shlex
import sys
import time
import subprocess
import hashlib
from collections import OrderedDict

sys.path.append("../lib")
sys.path.append("../regression")
import common
from nic_con import nic_con
import sal_con

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
        "-dice_prog", "--dice_prog", 
        action='store_true',
        help="DICE UDS program")
    group.add_argument(
        "-cleanup", "--cleanup", 
        action='store_true',
        help="Clean up")
    group.add_argument(
        "-check_uboot", "--check_uboot", 
        action='store_true',
        help="Check chip certificate CRC32")
    group.add_argument(
        "-check_uds_cert", "--check_uds_cert", 
        action='store_true',
        help="Check and validate UDS certificate checksum")
    group.add_argument(
        "-val_uds_cert", "--val_uds_cert", 
        action='store_true',
        help="validate UDS certificate stored")
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
        "-dice_img_prog", "--dice_img_prog", 
        action='store_true',
        help="Program DICE QSPI images")
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
        "-dice_entropy_prog", "--dice_entropy_prog", 
        action='store_true',
        help="Program entropy for DICE")
    group.add_argument(
        "-efuse_prog", "--efuse_prog", 
        action='store_true',
        help="Program pac to efuse")
    group.add_argument(
        "-hmac_fuse_prog", "--hmac_fuse_prog", 
        action='store_true',
        help="Program hmac fuse")
    group.add_argument(
        "-efuse_test", "--efuse_test", 
        action='store_true',
        help="Test efuse by burning bit[127]")
    group.add_argument(
        "-sysrst_test", "--sysrst_test", 
        action='store_true',
        help="Test sysreset with puf error")
    group.add_argument(
        "-get_pn", "--get_pn", 
        action='store_true',
        help="Get Pensando internal PN")
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
        "-hmac_file",
        "--hmac_file",
        help="HMAC file name which contains 512 bits hex value")
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
    parser.add_argument(
        "-fast",
        "--fast_path", 
        action='store_true',
        help="Fast path of key programming")
    parser.add_argument(
        "-d",
        "--dry_run", 
        action='store_true',
        help="Efuse prog dry run")

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

    def get_lines_to_file_after_substring(self, text, substring, file_name, num_lines):
        lines = text.splitlines()
        try:
            index = lines.index(substring)
            data_str = lines[index + 1:index + 1 + num_lines] 
            result = "".join(line.strip() for line in data_str)
        except ValueError:
            return -1

        out_file = open(file_name, "w")
        out_file.write(result)
        out_file.close()
        return 0

    def create_otp_cm_fmt(self, sn, slot):
        tgt_sn_len = 16
        ret = 0

        fmt_txt = """HW_LOCK_BIT 1
ESEC_SECUREBOOT 1
WATCHDOG 1
ESEC_FW_ENABLE 1
CHIP_TAMPERED 0
PUBCMREVOKED 0x00
DEBUGPROTENCM 0xFFFF
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

        print("=== Creating OTP_content_CM; sn: {} ===".format(sn))

        sn_len = len(sn)
        if sn_len > 16 or sn_len == 0:
            print("Invalid SN lenth: expect less than 16; received {}".format(len(sn)))
            ret = -1
        else:
            output = sn.ljust(tgt_sn_len, '\0')

            # If Oracle card, add 'O' to SN
            pn = self.get_pn(slot)
            if pn == "UNKNOWN":
                return -1

            if pn == "68-0015-02" or \
               pn == "68-0026-01" or \
               pn == "68-0049-03" or \
               pn == "68-0089-01" or \
               pn == "68-0029-01" or \
               pn == "68-0074-01" or \
               pn == "68-0075-01" or \
               pn == "68-0075-02" or \
               pn == "68-0095-01" or \
               pn == "68-0077-01":
                output1 = list(output)
                print("Adding Oracle signature")
                output1[15] = 'O'
                output = "".join(output1)

            print("SN:", output)
            output = "".join("{:02x}".format(ord(c)) for c in output)
            output = "0x"+output
            file_output = fmt_txt.format(output)

            text_file = open("OTP_content_CM.txt", "w")
            text_file.write(file_output)
            text_file.close()

        print("=== Creating OTP_content_CM done")
        return ret

    def get_pn(self, slot):
        ret = 0
        cmd = 'eeutil -disp -uut=UUT_{}'.format(slot)
        cmd_list = shlex.split(cmd)
        output = subprocess.check_output(cmd_list)
        #print(output)

        card_type = os.environ['UUT_{}'.format(args.slot)]    
        asic_type = self.get_asic_type(card_type)
        if asic_type == "SALINA":
            ma = re.compile(r".*Assembly Number\s+([\w]{3}-[\w]{6}-[\w]{2,}) .*")
        else:
            ma = re.compile(r".*Assembly Number\s+([\d]{2}-[\d]{4}-[\d]{2}) .*")
        src_str = "".join(output.splitlines())
        result = ma.match(src_str)
        if result == None:
            print("PN not found with Assembly Number")
            pn = "UNKNOWN"
        else:
            pn = result.group(1)
            print("PN:", pn)
            return pn

        # Some cards does not have Assembly Number, they use Part Number instead
        ma = re.compile(r".*Part Number[ ]{8,}([\d]{2}-[\d]{4}-[\d]{2}|[A-Z0-9]{6}-[0-9]{3}|[A-Z0-9]{6}[X|A][A-Z0-9]{2}|[\d]{3}-[\d]{5}).*")
        src_str = "".join(output.splitlines())
        result = ma.match(src_str)
        if result == None:
            print("PN not found with Part Number")
            pn = "UNKNOWN"
            print("========== Dumping eeutil output ============")
            print(output)
        else:
            pn = result.group(1)

        print("PN:", pn)
        return pn

    def enroll_puf(self, sn, slot):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -enroll_puf -sn {} -slot {}".format(sn, slot)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 120)
        common.session_stop(session)

        print("ret:", ret)
        return ret

    def sign_ek(self, sn, pn, mac, card_type, mtp, client_key, client_cert, trust_roots, backend_url):
        cmd_fmt = "/home/diag/diag/python/esec/scripts/esec_prog.sh -sign_ek -sn {} -pn {} -mac {} -card_type {} -mtp {} -k {} -c {} -t {} -b {}"
        ret = 0
        num_retry = 3

        cmd = cmd_fmt.format(sn, pn, mac, card_type, mtp, client_key, client_cert, trust_roots, backend_url)
        print(cmd)

        for retry in range(num_retry):
            print(url, "signing EK #", retry)
            session = common.session_start()
            ret = common.session_cmd_pass_multi(session, cmd, ["PKI PASSED", "SIGNING EK PASSED"])
            common.session_stop(session)
            if ret == 0:
                break
            time.sleep(5)

        print("ret:", ret)
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
            print("CRC32 not found")
            ret = -1
        else:
            crc32_ek = result.group(1)
            print("CRC32 calculated:", crc32_ek)
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
            print("Signed EK validated")
            ret = 0
        else:
            print("Failed to validate signed EK")
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

    def boot_test(self, sn, slot, card_type):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -post_check -sn {} -slot {} -card_type {}".format(sn, slot, card_type)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 300)
        common.session_stop(session)

        return ret

    def get_asic_type(self, card_type):
        asic_type = "CAPRI"
        if card_type == "ORTANO2"       or \
           card_type == "ORTANO2A"      or \
           card_type == "ORTANO2AC"     or \
           card_type == "ORTANO2I"      or \
           card_type == "ORTANO2S"      or \
           card_type == "LACONA32"      or \
           card_type == "LACONA32DELL"  or \
           card_type == "POMONTE"       or \
           card_type == "POMONTEDELL"   or \
           card_type == "PENSANDO":      # dummy condition
            asic_type =  "ELBA"
        if card_type == "GINESTRA_D4"       or \
           card_type == "GINESTRA_D5":
            asic_type = "GIGLIO"
        if card_type == "MALFA"       or \
           card_type == "POLLARA"     or \
           card_type == "LINGUA"      or \
           card_type == "LENI"        or \
           card_type == "LENI48G":
            asic_type = "SALINA"
        print("ASIC_TYPE:", asic_type)
        return asic_type

    def check_fpga_card(self, card_type):
        if card_type == "LACONA32"      or \
           card_type == "LACONA32DELL"  or \
           card_type == "POMONTE"       or \
           card_type == "POMONTEDELL"   or \
           card_type == "PENSANDO":      # dummy condition
            return True
        else:
            return False

    def key_prog_all(self, sn, slot, pn, mac, card_type, mtp, client_key, client_cert, trust_roots, backend_url):
        os.chdir("/home/diag/diag/scripts/asic/")
        common.bash_prompt = '\$ '
        asic_type = self.get_asic_type(card_type)
        if asic_type == "ELBA":
            cmd = "tclsh /home/diag/diag/scripts/asic/esec_prog_elba.tcl -stage esec_all\
                -sn {} -slot {} -pn \"{}\" -mac {} -mtp {}\
                -client_key \"{}\" -client_cert \"{}\" -trust_roots \"{}\" -backend_url \"{}\"".\
                format(sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url)
        elif asic_type == "GIGLIO":
            cmd = "tclsh /home/diag/diag/scripts/asic/esec_prog_giglio.tcl -stage esec_all\
                -sn {} -slot {} -pn \"{}\" -mac {} -mtp {}\
                -client_key \"{}\" -client_cert \"{}\" -trust_roots \"{}\" -backend_url \"{}\"".\
                format(sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url)
        elif asic_type == "SALINA":
            cmd = "tclsh /home/diag/diag/scripts/asic/esec_prog_salina.tcl -stage esec_all\
                -sn {} -slot {} -pn \"{}\" -mac {} -mtp {}\
                -client_key \"{}\" -client_cert \"{}\" -trust_roots \"{}\" -backend_url \"{}\"".\
                format(sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url)
        else:
            cmd = "tclsh /home/diag/diag/scripts/asic/esec_prog.tcl -stage esec_all\
                -sn {} -slot {} -pn \"{}\" -mac {} -mtp {}\
                -client_key \"{}\" -client_cert \"{}\" -trust_roots \"{}\" -backend_url \"{}\"".\
                format(sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url)

        print(cmd)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 300)
        common.session_stop(session)
        return ret

    def key_prog_all_pac(self, sn, slot, pn, mac, card_type, mtp, client_key, client_cert, trust_roots, backend_url):
        os.chdir("/home/diag/diag/scripts/asic/")

        asic_type = self.get_asic_type(card_type)
        if asic_type == "ELBA":
            cmd = "tclsh /home/diag/diag/scripts/asic/esec_prog_elba.tcl -stage esec_all_pac\
                -sn {} -slot {} -pn \"{}\" -mac {} -mtp {}\
                -client_key \"{}\" -client_cert \"{}\" -trust_roots \"{}\" -backend_url \"{}\"".\
            format(sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url)
        elif asic_type == "GIGLIO":
            cmd = "tclsh /home/diag/diag/scripts/asic/esec_prog_giglio.tcl -stage esec_all_pac\
                -sn {} -slot {} -pn \"{}\" -mac {} -mtp {}\
                -client_key \"{}\" -client_cert \"{}\" -trust_roots \"{}\" -backend_url \"{}\"".\
            format(sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url)

        else:
            cmd = "tclsh /home/diag/diag/scripts/asic/esec_prog.tcl -stage esec_all_pac\
                -sn {} -slot {} -pn \"{}\" -mac {} -mtp {}\
                -client_key \"{}\" -client_cert \"{}\" -trust_roots \"{}\" -backend_url \"{}\"".\
                format(sn, slot, pn, mac, mtp, client_key, client_cert, trust_roots, backend_url)

        print(cmd)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 1200)
        common.session_stop(session)
        return ret

    def show_status(self, sn, slot, card_type):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -show_sts -sn {} -slot {} -card_type {}".format(sn, slot, card_type)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 300)
        common.session_stop(session)

        return ret

    def esec_prog(self, client_key, client_cert, trust_roots, backend_url, sn, slot, pn, mac, card_type, mtp, sku, fast_path):
        ret = self.create_otp_cm_fmt(sn, slot)
        if ret != 0:
            print("Failed to create OTP CM")
            print("=== ESEC PROG FAILED ===")
            return -1

        numRetry = 3

        for retry in range(numRetry):
            print("=== ESEC PROG #{}".format(retry))

            # Disable legacy way
            if 0:
                ret = self.enroll_puf(sn, slot)
                if ret != 0:
                    print("=== Enroll PUF failed ===")
                    print("=== ESEC PROG FAILED ===")
                    return ret

                ret = self.sign_ek(sn, pn, mac, card_type, mtp, client_key, client_cert, trust_roots, backend_url)
                if ret != 0:
                    print("=== Failed to sign pub_ek ===")
                    print("=== ESEC PROG FAILED ===")
                    return ret

                ret = self.ek_check()
                if ret != 0:
                    print("=== Failed to validate signed EK ===")
                    print("=== ESEC PROG FAILED ===")
                    return ret

                [ret, crc32_ek] = self.sign_ek_crc()
                if ret != 0:
                    print("=== Failed to calculated CRC32 of signed EK ===")
                    print("=== ESEC PROG FAILED ===")
                    return ret

                ret = self.gen_otp()
                if ret != 0:
                    print("=== Failed to generate OTP binary ===")
                    print("=== ESEC PROG FAILED ===")
                    return ret

                ret = self.otp_init(sn, slot)
                if ret != 0:
                    print("=== OTP init failed ===")
                    print("=== ESEC PROG FAILED ===")
                    return ret

                ret = self.boot_test(sn, slot, card_type)
                if ret != 0:
                    # Enter retry
                    print("=== Bad OTP init ===")
                    print("=== Post boot test failed ===")
                    print("Power cycle slot #{}".format(slot))
                    self.nic_con.power_cycle_multi(slot, 10)
                else:
                    # Move forward
                    break

            if fast_path == True:
                ret = self.key_prog_all(sn, slot, pn, mac, card_type, mtp, client_key, client_cert, trust_roots, backend_url)
            else:
                ret = self.key_prog_all_pac(sn, slot, pn, mac, card_type, mtp, client_key, client_cert, trust_roots, backend_url)
            if ret != 0:
                print("=== ESEC PROG FAILED ===")
                return ret
            else:
                # Move forward
                break

        if ret != 0:
            print("=== ESEC PROG FAILED ===")
            return ret
        else:
            print("=== OTP PROG validated #{} ===".format(retry-1))

        print ("slot:", slot)
        asic_type = self.get_asic_type(card_type)
        if asic_type == "SALINA":
            print("Skip check uboot in this process")
        else:
            file1 = open("/home/diag/diag/tools/pki/crc32_ek.bin", "r+")
            crc32_ek = file1.read()
            crc32_ek = crc32_ek[:-1]
            print("crc32_ek:", crc32_ek)
            file1.close()

            [ret, crc32_ek_uboot] = self.check_uboot_esec(int(slot))
            if ret != 0:
                print("=== Failed to check ESEC in uboot ===")
                print("=== ESEC PROG FAILED ===")
                return ret

            if crc32_ek != crc32_ek_uboot:
                print("CRC32 cross check failed; Caculated:", crc32_ek, "Uboot:", crc32_ek_uboot)
                print("=== ESEC PROG FAILED ===")
                return -1

        asic_type = self.get_asic_type(card_type)
        if asic_type == "ELBA" or asic_type == "GIGLIO" or "SALINA":
            print("Skip sys reset test")
        else:
            ret = self.sysrst_test(int(slot))
            if ret != 0:
               print("sysreset test failed")
               print("=== ESEC PROG FAILED ===")
               return -1

        asic_type = self.get_asic_type(card_type)
        if asic_type == "SALINA":
            print("Skip efuse test")
        else:
            ret = self.efuse_test(int(slot), card_type)
            if ret != 0:
                print("=== Efuse test failed ===")

        if ret == 0:
            print("=== ESEC PROG/VALICATION PASSED ===")
        else:
            print("=== ESEC PROG FAILED ===")

        return ret

    def verify_dice_cert(self, slot, action):
        expstr = ["uart:"]
        expstr1 = ["rt:"]
        ret = 0
        md5sum_cert = ""
        md5sum_uboot= ""
        session = common.session_start()
        #cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x20 -data=0x7".format(slot)
        cmd = "/home/diag/diag/scripts/asic/sal_esecure_lockbits.sh {} 0xbd 0xbd".format(slot)
        common.session_cmd(session, cmd, ending="MTP:\$")
        cmd = "turn_on_slot.sh off {}".format(slot)
        common.session_cmd(session, cmd, ending="MTP:\$")
        time.sleep(10)
        cmd = "turn_on_slot.sh on {}".format(slot)
        common.session_cmd(session, cmd, ending="MTP:\$")
        time.sleep(60)
        print("\nDisable WDT")
        cmd = "i2cset -y {} 0x4A 0x1 0x0".format(int(slot) + 2)
        common.session_cmd(session, cmd)
        cmd = "i2cget -y {} 0x4f 0x1".format(int(slot)+2)
        common.session_cmd(session, cmd)
        #ret = sal_con.enter_a35_zephyr(slot, session, uart_id=0, new_ainic_layout=True, n1_autoboot_delay=30)
        ret = 0
        if ret != 0:
            print("Failed to boot to zephyr prompt")
            cmd = "/home/diag/diag/scripts/asic/sal_esecure_lockbits.sh {} 0x00 0x00".format(slot)
            common.session_cmd(session, cmd)
            common.session_stop(session)
            return [ret, md5sum_cert]

        # Find md5sum
        ret = self.nic_con.uart_session_start(session, slot, uart_id=0)
        if ret != 0:
            print("Failed to enter zephyr prompt")
            self.nic_con.uart_session_stop(session)
            cmd = "/home/diag/diag/scripts/asic/sal_esecure_lockbits.sh {} 0x00 0x00".format(slot)
            common.session_cmd(session, cmd)
            common.session_stop(session)
            return [ret, md5sum_cert]

        try:
            session.expect(["uart:", "MTP:\$"], 1)
            session.expect(["uart:", "MTP:\$"], 1)
        except pexpect.TIMEOUT:
            print("--- Synced ---")

        self.nic_con.uart_session_cmd(session, "dice_dump_cert", 30, expstr)
        src_str = session.before

        self.nic_con.uart_session_stop(session)

        try:
            session.expect(["uart:", "MTP:\$"], 1)
            session.expect(["uart:", "MTP:\$"], 1)
        except pexpect.TIMEOUT:
            print("--- Synced ---")

        cmd = "env | grep COLOR"
        common.session_cmd(session, cmd, ending="MTP:\$")
        cmd = "/home/diag/diag/scripts/asic/sal_esecure_lockbits.sh {} 0x00 0x00".format(slot)
        common.session_cmd(session, cmd, ending="MTP:\$")

        if action == "all":
            index = src_str.find("MD5 Checksum (Hex) :", 1)
            if index == -1 or index == len(src_str) - len("MD5 Checksum (Hex) :"):
                print("=== Failed to get md5sum from zephyr ===")
                print("=== DICE VALIDATION FAILED ===")
                common.session_stop(session)
                ret = -1
            else:
                result = src_str[index + len("MD5 Checksum (Hex) :"):]
                result = result.split()
                md5sum_uboot = result[0]
                print("got md5sum", md5sum_uboot)
            file = open("/home/diag/diag/asic/asic_src/ip/cosim/tclsh/uds_csr_der.crt", "r+")
            md5sum_cert = file.read()
            file.close()
            md5sum_cert = hashlib.md5(md5sum_cert).hexdigest()
            print("md5sum cert:", md5sum_cert, "md5sum uboot", md5sum_uboot)
            if md5sum_cert == md5sum_uboot:
                print("=== uds md5sum check passed ===")
            else:
                print("md5sum check failed; Caculated:", md5sum_cert, "Uboot:", md5sum_uboot)
                print("=== DICE VALIDATION FAILED ===")
                common.session_stop(session)
                return [-1, md5sum_cert]

        index = src_str.find("Raw Cert data (Hex):", 1)
        if index == -1 or index == len(src_str) - len("Raw Cert data (Hex):"):
            print("=== failed to get dice certificate 0 data ===")
            print("=== DICE VALIDATION FAILED ===")
            common.session_stop(session)
            ret = -1
        else:
            result = src_str[index:]
            ret = self.get_lines_to_file_after_substring(result, "Raw Cert data (Hex):", "uds_cert.txt", 72)

        index = result.find("Raw Cert data (Hex):", 1)
        if index == -1 or index == len(result) - len("Raw Cert data (Hex):"):
            print("=== failed to get dice certificate 1 data ===")
            print("=== DICE VALIDATION FAILED ===")
            common.session_stop(session)
            ret = -1
        else:
            result = result[index:]
            ret |= self.get_lines_to_file_after_substring(result, "Raw Cert data (Hex):", "cdi_cert.txt", 106)

        if ret != 0:
            print("=== DICE VALIDATION FAILED ===")
            return (ret, md5sum_uboot)

        cmd ="xxd -r -p uds_cert.txt uds_cert.der"
        common.session_cmd(session, cmd, ending="MTP:\$")
        cmd ="xxd -r -p cdi_cert.txt cdi_cert.der"
        common.session_cmd(session, cmd, ending="MTP:\$")
        cmd = "openssl x509 -inform der -in uds_cert.der -out uds_cert.pem"
        common.session_cmd(session, cmd, ending="MTP:\$")
        cmd = "openssl x509 -inform der -in cdi_cert.der -out cdi_cert.pem"
        common.session_cmd(session, cmd, ending="MTP:\$")
        cmd = "openssl x509 -in uds_cert.pem -noout -text"
        common.session_cmd(session, cmd, ending="MTP:\$")
        cmd = "openssl x509 -in cdi_cert.pem -noout -text"
        common.session_cmd(session, cmd, ending="MTP:\$")
        #cmd = "openssl verify -ignore_critical -CAfile /home/diag/diag/tools/pki/dice_certs/RootCA.pem -untrusted uds_cert.pem cdi_cert.pem"
        cmd = "openssl verify -ignore_critical -CAfile /home/diag/diag/tools/pki/dice_certs/AMD-Root-CA-E3.pem\
                                        -untrusted /home/diag/diag/tools/pki/dice_certs/AMD-Identity-CA-E3.pem\
                                        -untrusted /home/diag/diag/tools/pki/dice_certs/manufacturing_dice_ca_v2.pem -untrusted uds_cert.pem cdi_cert.pem"
        common.session_cmd(session, cmd, ending="MTP:\$")
        #cmd = ""
        #common.session_cmd(session, cmd)
        result = session.before
        common.session_stop(session)

        if "cdi_cert.pem: OK" in result:
            print("=== DICE VALIDATION PASSED ===")
        else:
            print("=== DICE VALIDATION FAILED ===")
            ret = -1

        return [ret, md5sum_uboot]

    def val_dice_esec(self, slot):
        ret, md5sum = self.verify_dice_cert(slot, "validate")
        return [ret, md5sum]

    def check_dice_esec(self, slot):
        ret, md5sum  = self.verify_dice_cert(slot, "all")
        return [ret, md5sum]

    def dice_prog(self, client_key, client_cert, trust_roots, backend_url, slot, sn):
        os.chdir("/home/diag/diag/scripts/asic/")
        common.bash_prompt = '\$ '
        cmd = "tclsh /home/diag/diag/scripts/asic/esec_prog_salina.tcl -stage esec_dice_all\
               -slot {} -sn {} -client_key \"{}\" -client_cert \"{}\" -trust_roots \"{}\" -backend_url \"{}\"".\
               format(slot, sn, client_key, client_cert, trust_roots, backend_url)
        print(cmd)
        pass_sign = "ESEC PROG PASSED"
        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 300)
        common.session_stop(session)

        if ret == 0:
            print("=== DICE PROG PASSED ===")
        else:
            print("=== DICE PROG FAILED ===")

        return [ret, md5sum_cert]

    def cleanup (self):
        ret = 0
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -cleanup"
        session = common.session_start()
        ret = common.session_cmd(session, cmd)
        common.session_stop(session)
        return ret

    def sysreset(self, session, slot=0, timeout=300):
        ret = 0
        if slot == 0 or slot > 10:
            print("Invalid slot number:", slot)
            sys.exit(0)

        session.timeout = timeout
        cmd = "cpldutil -cpld-wr -addr=0x18 -data={}".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(1)
        cmd = "turn_on_slot.sh off {}".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(1)
        cmd = "turn_on_hub.sh {}".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(1)
        cmd = "turn_on_slot_3v3.sh on {}".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(1)
        cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x21 -data=0x34".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(1)
        cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x20 -data=0x7".format(slot)
        common.session_cmd(session, cmd)
        time.sleep(1)
        cmd = "turn_on_slot.sh on {}".format(slot)
        common.session_cmd(session, cmd)
        print("turn on slot, wait for 30 seconds\n")
        sys.stdout.flush()
        time.sleep(30)

        uartsession = common.session_start()
        uartsession.timeout = timeout
        for retry in range(10):
            print("iteration %d\n" % (retry + 1))
            try:
                expstr = ["capri login:", "elba login:"]
                self.nic_con.uart_session_start(uartsession, slot)
                cmd = "sysreset.sh"
                uartsession.sendline(cmd)
                uartsession.expect(expstr, 300)
                self.nic_con.uart_session_stop(uartsession)

            except:
                self.nic_con.uart_session_stop(uartsession)
                print("=== TIMEOUT: failed to sysreset NIC in slot {}".format(slot))
                return -1;

            cmd = "smbutil -uut=uut_{} -dev=cpld -rd -addr=0x2a".format(slot)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()
            res = output.split(";")
            reg = res[1].split("=")
            if int(reg[1],16) != 0:
                print("Puf error counter is no zero %s\n" % reg[1])
                return -1;

            cmd = "smbutil -uut=uut_{} -dev=cpld -rd -addr=0x21".format(slot)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()
            res = output.split(";")
            reg = res[1].split("=")
            if int(reg[1], 16) & 0xfe != 0x34:
                print("Register 0x21 value is not expected %s\n" % reg[1])
                return -1;

            cmd = "smbutil -uut=uut_{} -dev=cpld -rd -addr=0x20".format(slot)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()
            res = output.split(";")
            reg = res[1].split("=")
            if reg[1] != "0x7\n":
                print("Register 0x20 value is not expected %s\n" % reg[1])
                return -1;

            cmd = "inventory -sts -slot {}".format(slot)
            common.session_cmd(session, cmd)
            time.sleep(1)
        return ret

    def check_uboot_esec(self, slot, post_check=False):
        card_type = os.environ['UUT_{}'.format(slot)]
        asic_type = self.get_asic_type(card_type)

        expstr = ["Capri# ", "DSC# "]
        ret = 0
        crc32_ek = ""
        session = common.session_start()
        if asic_type == "SALINA":
            file1 = open("/home/diag/diag/tools/pki/crc32_ek.bin", "r+")
            crc32_ek_file = file1.read()
            crc32_ek_file = crc32_ek_file[:-1]
            print("crc32_ek:", crc32_ek_file)
            file1.close()

            cmd = "smbutil -uut=uut_{} -dev=cpld -wr -addr=0x20 -data=0x7".format(slot)
            common.session_cmd(session, cmd)
            ret = self.nic_con.enter_uboot_salina(session, slot, uart_id=0, v12_reset="v12_reset")
        else:
            ret = self.nic_con.enter_uboot_esec(session, slot)
        if ret != 0:
            print("Failed to enter uboot")
            return ret
        ret = self.nic_con.conn_uboot(session, slot, 0)
        if ret != 0:
            print("Failed to connect uboot")
            return ret

        self.nic_con.uart_session_cmd(session, "esec read_serial_number", 30, expstr)
        self.nic_con.uart_session_cmd(session, "esec read_tamper_status", 30, expstr)
        self.nic_con.uart_session_cmd(session, "esec read_boot_status", 30, expstr)
        self.nic_con.uart_session_cmd(session, "esec read_chip_cert crc32", 30, expstr)

        # Find CRC32
        session.sendline("esec read_chip_cert crc32")
        session.expect(expstr)
        ma = re.compile(r".*0x([a-fA-F0-9]+).*")
        src_str = "".join(session.before.splitlines())
        result = ma.match(src_str)
        if result == None:
            print("CRC32 not found")
            ret = -1
        else:
            crc32_ek = result.group(1)
            if asic_type == "SALINA":
                if crc32_ek != crc32_ek_file:
                    print("EK VALIDATION FAILED")
                    ret = -1
                else:    
                    print("EK VALIDATION PASSED")
            else:
                print("EK validated")
            ret = 0

        time.sleep(2)
        self.nic_con.uart_session_stop(session)
        common.session_stop(session)
        return [ret, crc32_ek]

    def img_prog(self, slot):
        pn = self.get_pn(slot)
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -img_prog -slot {} -pn {}".format(slot,pn)
        ret = 0
        pass_sign = "ESEC PROG PASSED"

        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 240)
        common.session_stop(session)

        if ret == 0:
            print("IMG PROG PASSED")
        else:
            print("IMG PROG FAILED")

        return ret

    def dice_img_prog(self, slot):
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -dice_img_prog -slot {}".format(slot)
        ret = 0
        pass_sign = "ESEC PROG PASSED"

        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 240)
        common.session_stop(session)

        if ret == 0:
            print("DICE IMG PROG PASSED")
        else:
            print("DICE IMG PROG FAILED")

        return ret

    def dice_entropy_prog(self, sn, slot, dry_run):
        ret = 0
        dr = 0
        if dry_run == True:
            dr = 1

        os.chdir("/home/diag/diag/tools/pki")
        cmd_fmt = "python2.7 ./client_dice.py -k dice_certs/client.key.pem -c dice_certs/client.crt.pem -t dice_certs/rootca.crt -b '192.168.67.213:12266#192.168.67.214:12266' -sn {} -n 32 -hsm_rn"
        cmd = cmd_fmt.format(sn)
        cmd_list = shlex.split(cmd)
        output = subprocess.check_output(cmd_list)
        print(output)

        ma = re.compile(r".*Fetched 32 random bytes:*")
        src_str = "".join(output.splitlines())
        result = ma.match(src_str)
        if result == None:
            print("HSM RN not found")
            return -1
        else:
            hsm_rn = result.group(1)
            hsm_rn = hsm_rn.upper()
            print("HSM RN:", hsm_rn)
            print("HSM RN Generated from HSB successful")

    def hmac_fuse_prog(self, slot, card_type, hmac_file, dry_run):
        dr = 0
        if dry_run == True:
            dr = 1
        asic_type = self.get_asic_type(card_type)
        if asic_type == "SALINA":
            cmd = "tclsh /home/diag/diag/scripts/asic/sal_hmac_prog.tcl {} {} {}".format(slot, hmac_file, dr) 
            print(cmd)
            pass_sign = "EFUSE PROG PASSED"
            session = common.session_start()
            ret = common.session_cmd_pass(session, cmd, pass_sign, 300)
            common.session_stop(session)
        else:
            print("feature is not supported for ASICs other than SALINA")

        if ret == 0:
            print("EFUSE PROG PASSED")
        else:
            print("EFUSE PROG FAILED")

        return ret

    def efuse_prog(self, sn, slot, pn, mac, card_type, mtp, client_key, client_cert, trust_roots, backend_url, dry_run):
        ret = 0
        dr = 0
        if dry_run == True:
            dr = 1

        os.chdir("/home/diag/diag/tools/pki")
        cmd_fmt = "python2.7 ./client_diag.py -sn {} -pdn {} -pn \"{}\" -mac {} -mid {} -n 32 -hsm_rn"
        cmd = cmd_fmt.format(sn, card_type, pn, mac, mtp)
        cmd_list = shlex.split(cmd)
        output = subprocess.check_output(cmd_list)
        print(output)
        
        ma = re.compile(r".*Fetched 32 random bytes:(.*)PKI.*")
        src_str = "".join(output.splitlines())
        result = ma.match(src_str)
        if result == None:
            print("HSM RN not found")
            return -1
        else:
            hsm_rn = result.group(1)
            hsm_rn = hsm_rn.upper()
            print("HSM RN:", hsm_rn)

        asic_type = self.get_asic_type(card_type)
        if asic_type == "SALINA":
            cmd = "tclsh /home/diag/diag/scripts/asic/sal_efuse_prog.tcl {} {} {}".format(slot, hsm_rn, dr) 
            print(cmd)
            pass_sign = "EFUSE PROG PASSED"
            session = common.session_start()
            ret = common.session_cmd_pass(session, cmd, pass_sign, 300)
            common.session_stop(session)
        else:
            nic_con1 = nic_con()
            nic_con1.switch_console(int(slot))
            session = common.session_start()
            session.timeout = 60

            nic_con1.uart_session_start(session, slot)
            nic_con1.uart_session_cmd(session, "/data/nic_util/xo3dcpld -w 1 0x2a")
            nic_con1.uart_session_cmd(session, "/data/nic_util/xo3dcpld -r 1")
            nic_con1.uart_session_cmd(session, "cd /data/nic_arm/nic/asic_src/ip/cosim/tclsh")

            if card_type == "GINESTRA_D4" or card_type == "GINESTRA_D5":
                cmd = "./diag.exe gig_efuse_prog.tcl {} {}".format(hsm_rn, dr)
            else:
                cmd = "./diag.exe elb_efuse_prog.tcl {} {}".format(hsm_rn, dr)
            ret = nic_con1.uart_session_cmd_sig(session, cmd, timeout=120, sig=["EFUSE PROG PASSED", "EFUSE PROG FAILED"])

            nic_con1.uart_session_cmd(session, "/data/nic_util/xo3dcpld -w 1 0xa")
            nic_con1.uart_session_cmd(session, "/data/nic_util/xo3dcpld -r 1")

            nic_con1.uart_session_stop(session)
            common.session_stop(session)

        if ret == 0:
            print("EFUSE PROG PASSED")
        else:
            print("EFUSE PROG FAILED")

        return ret

    def efuse_test(self, slot, card_type):
        asic_type = self.get_asic_type(card_type)
        if asic_type == "ELBA" or asic_type == "GIGLIO" or asic_type == "SALINA":
            print("Skip efuse test for Elba cards")
            print("EFUSE TEST PASSED")
            return 0

        self.nic_con.power_cycle_multi(str(slot), 5)
        cmd = "/home/diag/diag/python/esec/scripts/esec_prog.sh -efuse_test -slot {} -card_type {}".format(slot, card_type)
        ret = 0

        pass_sign = "ESEC PROG PASSED"

        session = common.session_start()
        ret = common.session_cmd_pass(session, cmd, pass_sign, 180)
        common.session_stop(session)

        if ret == 0:
            print("EFUSE TEST PASSED")
        else:
            print("EFUSE TEST FAILED")

        return ret

    def sysrst_test(self, slot):
        ret = 0
        session = common.session_start()
        ret = self.sysreset(session, slot)
        session = common.session_stop(session)
        if ret == 0:
            print("systest TEST PASSED")
        else:
            print("systest TEST FAILED")
        return ret

if __name__ == "__main__":
    args = parse_args_diag()
    esec_ctrl = esec_ctrl()

    # cleanup does not need slot
    if args.cleanup == True:
        ret = esec_ctrl.cleanup()
        sys.exit(ret)

    card_type = os.environ['UUT_{}'.format(args.slot)]    
    print("CARD_TYPE:", card_type)

    if args.otp_cm_fmt == True:
        esec_ctrl.create_otp_cm_fmt(args.sn, args.slot)
        sys.exit()

    if args.enroll_puf == True:
        esec_ctrl.enroll_puf(args.sn, args.slot)
        sys.exit()

    if args.sign_ek == True:
        esec_ctrl.sign_ek(args.sn, args.pn, args.mac, card_type, args.mtp, args.client_key, args.client_cert, args.trust_roots, args.backend_url)
        sys.exit()

    if args.gen_otp == True:
        esec_ctrl.gen_otp()
        sys.exit()

    if args.otp_init == True:
        esec_ctrl.otp_init(args.sn, args.slot)
        sys.exit()

    if args.esec_prog == True:
        ret = esec_ctrl.esec_prog(args.client_key, args.client_cert, args.trust_roots, args.backend_url,\
                args.sn, args.slot, args.pn, args.mac, card_type, args.mtp, args.sku, args.fast_path)
        sys.exit(ret)

    if args.dice_prog == True:
        esec_ctrl.dice_prog(args.client_key, args.client_cert, args.trust_roots, args.backend_url,\
                args.slot, args.sn)
        sys.exit()

    if args.check_uboot == True:
        esec_ctrl.check_uboot_esec(int(args.slot), args.post_check)
        sys.exit()

    if args.check_uds_cert == True:
        esec_ctrl.check_dice_esec(int(args.slot))
        sys.exit()

    if args.val_uds_cert == True:
        esec_ctrl.val_dice_esec(int(args.slot))
        sys.exit()

    if args.ek_crc == True:
        esec_ctrl.sign_ek_crc()
        sys.exit()

    if args.ek_check == True:
        esec_ctrl.ek_check()
        sys.exit()

    if args.key_prog_all == True:
        esec_ctrl.key_prog_all(int(args.slot), args.sn, args.pn, args.mac, card_type, args.mtp, args.client_key,\
                args.client_cert, args.trust_roots, args.backend_url)
        sys.exit()

    if args.img_prog == True:
        ret = esec_ctrl.img_prog(int(args.slot))
        sys.exit(ret)

    if args.dice_img_prog == True:
        esec_ctrl.dice_img_prog(int(args.slot))
        sys.exit()

    if args.dice_entropy_prog == True:
        esec_ctrl.dice_entropy_prog(args.sn, int(args.slot), args.dry_run)
        sys.exit()

    if args.efuse_prog == True:
        esec_ctrl.efuse_prog(args.sn, int(args.slot), args.pn, args.mac, card_type, args.mtp, args.client_key,\
                args.client_cert, args.trust_roots, args.backend_url, args.dry_run)
        sys.exit()

    if args.hmac_fuse_prog == True:
        esec_ctrl.hmac_fuse_prog(int(args.slot), card_type, args.hmac_file, args.dry_run)
        sys.exit()

    if args.boot_test == True:
        esec_ctrl.boot_test(args.sn, args.slot, card_type)
 
    if args.sysrst_test == True:
        esec_ctrl.sysrst_test(int(args.slot))
        sys.exit()

    if args.show_sts == True:
        esec_ctrl.show_status(args.sn, args.slot, card_type)
        sys.exit()

    if args.efuse_test == True:
        esec_ctrl.efuse_test(int(args.slot), card_type)
        sys.exit()

    if args.get_pn == True:
        esec_ctrl.get_pn(int(args.slot))
        sys.exit()

    print("Invalid input")
