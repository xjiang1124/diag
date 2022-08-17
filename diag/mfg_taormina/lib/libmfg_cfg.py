from libdefs import NIC_Type

GLB_CFG_MFG_TEST_MODE = True

class NIC_IMAGES:
    ### IMAGES VERSION CONTROL FOR DL AND SWI:
    cpld_img = dict()
    cpld_ver = dict()
    cpld_dat = dict()
    sec_cpld_img = dict()
    sec_cpld_ver = dict()
    sec_cpld_dat = dict()
    fail_cpld_img = dict()
    fail_cpld_ver = dict()
    fail_cpld_dat = dict()
    fea_cpld_img = dict()
    fea_cpld_dat = dict()
    diagfw_img = dict()
    diagfw_dat = dict()
    goldfw_img = dict()
    goldfw_dat = dict()
    mainfw_dat = dict()

    cpld_img["TAORMINA"] = "17-0054-05_Taormina_ecpld-0002-11112021.bin"
    cpld_ver["TAORMINA"] = "0x1"
    cpld_dat["TAORMINA"] = "0002"
    sec_cpld_img["TAORMINA"] = "17-0054-05_Taormina_ecpld-0002-11112021.bin"
    sec_cpld_ver["TAORMINA"] = "0x1"
    sec_cpld_dat["TAORMINA"] = "0002"
    fail_cpld_img["TAORMINA"] = "17-0054-05_Taormina_ecpld-0002-11112021.bin"
    fail_cpld_ver["TAORMINA"] = "0x1"
    fail_cpld_dat["TAORMINA"] = "0002"
    fea_cpld_img["TAORMINA"] = "17-0054-02_Taormina_ecpld-8002-0505.fea"
    fea_cpld_dat["TAORMINA"] = "45 00 40 00 00 00 00 00 00 00 00 00 00 00 06 20"
    diagfw_img["TAORMINA"] = ""
    diagfw_dat["TAORMINA"] = ""
    goldfw_img["TAORMINA"] = "kernelg_1.29.0-T-Beta-9.img"
    goldfw_dat["TAORMINA"] = "02-24-2021"
    mainfw_dat["TAORMINA"] = "07-08-2022"

class MTP_IMAGES:
    AMD64_IMG = dict()
    ARM64_IMG = dict()

    AMD64_IMG["CAPRI"] = "image_amd64_capri.tar"
    ARM64_IMG["CAPRI"] = "image_arm64_capri.tar"

    AMD64_IMG["ELBA"] = "image_amd64_elba_taormina_v1.14.b.tar"
    ARM64_IMG["ELBA"] = "image_arm64_elba_taormina_v1.14.tar"

class TOR_IMAGES:
    first_article_img = dict()
    flash_boot0 = dict()
    flash_uboot_gold = dict()
    flash_fw_gold = dict()
    flash_uboot_primary = dict()
    flash_fw_primary = dict()
    usb_tarball = dict()
    os_ship_img = dict()
    os_ship_dat = dict()
    os_test_img = dict()
    os_test_dat = dict()
    bios_img = dict()
    bios_dat = dict()
    svos_test_img = dict()
    svos_test_dat = dict()
    svos_test_ver = dict()
    svos_ship_img = dict()
    svos_ship_dat = dict()
    svos_ship_ver = dict()
    tpm_img = dict()
    usb_img = dict()
    tpm_dat = dict()
    fpga_img = dict()
    fpga_dat = dict()
    test_fpga_img = dict()
    test_fpga_dat = dict()
    gpio_cpld_test_img = dict()
    gpio_cpld_test_dat = dict()
    gpio_cpld_ship_img = dict()
    gpio_cpld_ship_dat = dict()
    cpu_cpld_test_img = dict()
    cpu_cpld_test_dat = dict()
    cpu_cpld_ship_img = dict()
    cpu_cpld_ship_dat = dict()
    svos_fpga_image = dict()

    TFTP_SERVER_IP  = "192.168.99.10"
    TFTP_SERVER_DIR = "/"

    TFTP_SERVER_FPGA_DIR = TFTP_SERVER_DIR+"/diag/util/"
    svos_fpga_image["TAORMINA"] = ["fpgautil"]

    first_article_img["TAORMINA"] = "17-0065-02_Taormina-elba-spi-0430.bin"
    flash_boot0["TAORMINA"] = "boot0_1.49.2-T-2.img"
    flash_uboot_gold["TAORMINA"] = "ubootg_1.49.2-T-2.img"
    flash_fw_gold["TAORMINA"] = "kernelg_1.49.2-T-2.img"
    flash_uboot_primary["TAORMINA"] = "uboota_1.49.2-T-2.img"
    flash_fw_primary["TAORMINA"] = "kernela_1.49.2-T-2.img"

    usb_tarball["TAORMINA"] = "Taormina-USB-small.tar.gz"

    ## CX-OS ##
    os_ship_img["TAORMINA"] = "DL_10_10_1000.swi"
    os_ship_dat["TAORMINA"] = "2022-08-15"
    os_test_img["TAORMINA"] = "taormina-swjenkins-hbm_13272610_0803_2022.swi"
    os_test_dat["TAORMINA"] = "2022-08-03"

    ## BIOS ## 
    bios_img["TAORMINA"] = "17-0056-xx_Taormina-bios-v0004.bin"
    bios_dat["TAORMINA"] = "DL-01-0010"

    ## SVOS ##
    svos_test_img["TAORMINA"] = "DL_01_10_0002_INTL.svos"
    svos_test_ver["TAORMINA"] = "DL.01.10.0002-internal"
    svos_test_dat["TAORMINA"] = "2021-11-17"

    svos_ship_img["TAORMINA"] = "DL_01_10_0002.svos"
    svos_ship_ver["TAORMINA"] = "DL.01.10.0002"
    svos_ship_dat["TAORMINA"] = "2021-11-17"

    ## TPM ##
    tpm_img["TAORMINA"] = "tpmUpdate-v6.43.tar.gz"
    tpm_dat["TAORMINA"] = "6.43"

    usb_img["TAORMINA"] = "usb.tar.gz"

    ## FPGA ##
    fpga_img["TAORMINA"] = "17-0055-xx-dual-tagged-0005-06132022-2100.bin"
    fpga_dat["TAORMINA"] = "0005"

    test_fpga_img["TAORMINA"] = "17-0055-xx-dual-tagged-0005-06132022-2100.bin"
    test_fpga_dat["TAORMINA"] = "0005"

    ## CPLDs ##
    gpio_cpld_test_img["TAORMINA"] = "17-0053_03_Taormina_gcpld-0001-11032021.bin"
    gpio_cpld_test_dat["TAORMINA"] = "0001"

    cpu_cpld_test_img["TAORMINA"] = "17-0052-03_Taormina_ccpld-0001-11022021.bin"
    cpu_cpld_test_dat["TAORMINA"] = "0001"

    gpio_cpld_ship_img["TAORMINA"] = "17-0053_03_Taormina_gcpld-0001-11032021.bin"
    gpio_cpld_ship_dat["TAORMINA"] = "0001"

    cpu_cpld_ship_img["TAORMINA"] = "17-0052-03_Taormina_ccpld-0001-11022021.bin"
    cpu_cpld_ship_dat["TAORMINA"] = "0001"


# MFG release images
class MFG_IMAGE_FILES:
    MTP_AMD64_IMAGE = "image_amd64_04272021.tar"
    MTP_ARM64_IMAGE = "image_arm64_04272021.tar"


DIAG_NIGHTLY_REPORT_ACCOUNT = "diag-nightly@pensando.io"
DIAG_NIGHTLY_REPORT_PASSWD = "diag-nightly"
DIAG_NIGHTLY_REPORT_RECEIPIENT = "ps-diag@pensando.io"
DIAG_OS_PROMPT_LIST = ["$", "#", ">"]
#DIAG_SSH_OPTIONS = " -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"
DIAG_SSH_OPTIONS = " -q -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"
SVOS_SSH_OPTIONS = " -y -y -K 2 -I 30"

MFG_VALID_FW_LIST = ["diagfw", "mainfwa", "mainfwb", "goldfw"]
MFG_VALID_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES25, NIC_Type.FORIO, NIC_Type.VOMERO, NIC_Type.VOMERO2, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25OCP, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.ORTANO, NIC_Type.ORTANO2]
MFG_PROTO_NIC_TYPE_LIST = [NIC_Type.FORIO]

# please check the label specification
# FLM[Year, like 18, 19, 20][Week: 00-52][4 hex sequential digits]
FLX_MILPITAS_SN_FMT = "FLM\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
FLX_PENANG_SN_FMT = "FPN\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
HP_MILPITAS_SN_FMT = "5UP\d{1}[0-5]{1}\d{1}[0-9B-DF-HJ-NP-TV-Z]{4}"
HP_PENANG_SN_FMT = "[2|3]Y[U|1]\d{1}[0-5]{1}\d{1}[0-9B-DF-HJ-NP-TV-Z]{4}"
NAPLES_SN_FMT = r"{:s}|{:s}".format(FLX_MILPITAS_SN_FMT,FLX_PENANG_SN_FMT)
HP_SN_FMT = r"{:s}|{:s}".format(HP_MILPITAS_SN_FMT, HP_PENANG_SN_FMT)
FLX_MILPITAS_BUILD_SN_FMT = r"{:s}|{:s}".format(FLX_MILPITAS_SN_FMT, HP_MILPITAS_SN_FMT)
FLX_PENANG_BUILD_SN_FMT = r"{:s}|{:s}".format(FLX_PENANG_SN_FMT, HP_PENANG_SN_FMT)
NAPLES_MAC_FMT = r"00AECD[A-F0-9]{6}"
NAPLES_PN_FMT = r"68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2}$"
HP_PN_FMT = r"[A-Z0-9]{6}-[0-9]{3}$"
HP_SWN_PN_FMT = r"HPE Product Number +([A-Z0-9]{6}-B[0-9]{2})"
NAPLES_DISP_SN_FMT = r"Serial Number +({:s}|{:s})".format(FLX_MILPITAS_SN_FMT,FLX_PENANG_SN_FMT)
HP_DISP_SN_FMT = r"HPE Serial Number +({:s}|{:s})".format(HP_MILPITAS_SN_FMT,HP_PENANG_SN_FMT)
ALOM_SN_FMT = r"Serial Number +({:s}|{:s})".format(HP_MILPITAS_SN_FMT,HP_PENANG_SN_FMT)
NAPLES_DISP_MAC_FMT = r"MAC Address Base +(00-[a,A][e,E]-[c,C][d,D]-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2})"
NAPLES_DISP_DATE_FMT = r"Manufacturing Date/Time.*(\d{2}/\d{2}/\d{2})"
#NAPLES_DISP_DATE_FMT = r"(\d{2}/\d{2}/\d{2})"
NAPLES_DISP_PN_FMT = r"Part Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
IBM_DISP_ASSEMBLY_FMT = r"Assembly Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
PEN_DISP_ASSEMBLY_FMT = r"Assembly Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{2})"
VOMERO2_DISP_ASSEMBLY_FMT = r"Assembly Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
ORTANO_DISP_ASSEMBLY_FMT = r"Assembly Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
NAPLES_DISP_PN_FMT = r"Part Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
#NAPLES_DISP_PN_FMT = r"(Part|Assembly) Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
HP_DISP_PN_FMT = r"HPE Product Number +([A-Z0-9]{6}-[0-9]{3})"
HP_SWM_DISP_PN_FMT = r"Part Number +([A-Z0-9]{6}-[0-9]{3})"
ALOM_DISP_BIA_PN_FMT = r"Part Number +([A-Z0-9]{6}-[0-9]{3})"
ALOM_DISP_PIA_PN_FMT = r"HPE Product Number +([A-Z0-9]{6}-B[0-9]{2})"
OCP_DELL_DISP_PN_FMT = r"Assembly Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
HPESWM_DISP_ASSET_FMT = r"Asset Tag Type/Length.*0x(\w+)"
"""
ARUBA_EDC Format:   R-YYWW-ER
- R refers to PCB Revision (e.g. A, B, C...)
- YY refers to last 2 digits of Current Year (eg. Current Year is 2015. YY = 15)
- WW refers to Work Week when changes is made
- ER refers to division that holds the Engineering Responsibility, which is D3 (fixed) for HPN
"""
ARUBA_EDC_FMT = "[0-9A-Z]{1}\-\d{2}[0-5]\d{1}\-[0-9A-Z]{2}"

NIC_MGMT_USERNAME = "root"
NIC_MGMT_PASSWORD = "pen123"
TOR_MGMT_USERNAME = "root"
TOR_MGMT_PASSWORD = "pen123"

MTP_INTERNAL_MGMT_IP_ADDR = "10.1.1.100"
MTP_INTERNAL_MGMT_NETMASK = "255.255.255.0"

TOR_SN_ARUBA_FMT = "US\d{1}[0-9AB]{1}[A-Z]{1}[0-9B-DF-HJ-NP-TV-Z]{2}[0-9B-DF-HJ-NP-TV-Z]{3}"
TOR_SN_FSJ_FMT = "FSJ\d{2}[0-5]\d[0-9A-Z]{4}"
TOR_SN_FMT  = "[0-9A-Za-z]+" #"{:s}|{:s}".format(TOR_SN_FSJ_FMT, TOR_SN_ARUBA_FMT)
TOR_NIC_DISP_SN_FMT = r"Serial Number  +({:s})".format(TOR_SN_FMT)
TOR_MAC_SAVE_FMT = "049081[A-F0-9]{6}"
TOR_MAC_QR_FMT = "04:90:81(:[A-F0-9]{2}){3}"
TOR_MAC_FMT = ".*" #"({:s}|{:s})".format(TOR_MAC_SAVE_FMT, TOR_MAC_QR_FMT)
TOR_DISP_MAC_FMT = "MAC Address Base +([a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2})" #r"MAC Address Base +(04-90-81-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2})"
TOR_MB_PN_FMT = r"73-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2}$"
TOR_HPE_PN_FMT = r"R8S96A"
TOR_PN_FMT  = "[0-9A-Za-z\-]+" #"(JLDSSA|{:s}|{:s}|{:s})".format(NAPLES_PN_FMT, TOR_MB_PN_FMT, TOR_HPE_PN_FMT)
TOR_DISP_PN_FMT = r"Assembly Number +(73-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"

