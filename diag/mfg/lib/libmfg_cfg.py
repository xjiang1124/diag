from libdefs import NIC_Type
from libdefs import Factory
from libdefs import MTP_DIAG_Path
from libsku_utils import PART_NUMBERS_MATCH

GLB_CFG_MFG_TEST_MODE = False
FLEX_SHOP_FLOOR_CONTROL = False
MFG_BYPASS_PSU_CHECK = False
RUNNING_EDVT = False
ENABLE_SCAN_VERIFY = True
FST_SCAN_ENABLE = False
SALINA_HMAC_PROGRAM_ENABLE = False
MTP_HEALTH_MONITOR = False
DRY_RUN = False

class NIC_IMAGES:
    ### IMAGES VERSION CONTROL FOR DL AND SWI:
    cpld_img = dict()
    cpld_ver = dict()
    cpld_dat = dict()
    cpld_md5 = dict()
    sec_cpld_img = dict()
    sec_cpld_ver = dict()
    sec_cpld_dat = dict()
    sec_cpld_md5 = dict()
    fail_cpld_img = dict()
    fail_cpld_ver = dict()
    fail_cpld_dat = dict()
    fail_cpld_md5 = dict()
    fea_cpld_img = dict()
    ufm1_img = dict()
    timer1_img = dict()
    timer2_img = dict()
    diagfw_img = dict()
    diagfw_dat = dict()
    diagfw_md5 = dict()
    goldfw_img = dict()
    goldfw_dat = dict()
    goldfw_ver = dict()
    goldfw_md5 = dict()
    mainfw_img = dict()
    mainfw_ver = dict()
    mainfw_dat = dict()
    uboot_img = dict()
    uboot_dat = dict()
    uboota_img = dict()
    uboota_dat = dict()
    ubootb_img = dict()
    ubootb_dat = dict()
    cert_img = dict()
    test_fpga_img = dict()
    test_fpga_ver = dict()
    test_fpga_dat = dict()
    arm_a_zephyr_img = dict()
    arm_a_boot0_img = dict()
    arm_a_uboota_img = dict()
    arm_a_ubootb_img = dict()
    arm_a_ubootg_img = dict()
    qspi_prog_sh_img = dict()
    qspi_prog_secure_sh_img = dict()
    qspi_verify_sh_img = dict()
    qspi_verify_secure_sh_img = dict()
    arm_n_boot0_img = dict()
    arm_n_uboota_img = dict()
    arm_n_ubootb_img = dict()
    arm_n_ubootg_img = dict()
    arm_n_kernel_goldfw_img = dict()
    qspi_snake_img = dict()
    arm_a_zephyr_gold_img = dict()
    arm_a_zephyr_a_img = dict()
    arm_a_zephyr_b_img = dict()
    bl1_img = dict()
    pentrust_img = dict()
    fipa_img = dict()
    fipb_img = dict()
    fipg_img = dict()
    fwsel_img = dict()
    device_config_dtb = dict()
    firmware_config_dtb = dict()
    mbist_boot0_img = dict()
    microcontroller_img = dict()

    # write it down here so release script copies this file
    uboot_img["INSTALLER"] = "install_file"

    # NAPLES25SWM HPE Enterprise (P26968-002)
    cpld_img["NAPLES25SWM"] = "naples25_swm_revf_03102021.bin"
    cpld_ver["NAPLES25SWM"] = "0xF"
    cpld_dat["NAPLES25SWM"] = "03-10"
    sec_cpld_img["NAPLES25SWM"] = "naples25_swm_rev8f_03102021.bin"
    sec_cpld_ver["NAPLES25SWM"] = "0x8F"
    sec_cpld_dat["NAPLES25SWM"] = "03-10"
    diagfw_img["NAPLES25SWM"] = "capri_diagfw_uboot_1.3.1-E-65_2022.10.04.tar"
    diagfw_dat["NAPLES25SWM"] = "08-30-2022"
    goldfw_img["NAPLES25SWM"] = "capri_goldfw_1.3.1-E-65_2022.10.04.tar"
    goldfw_dat["NAPLES25SWM"] = "08-31-2022"
    mainfw_img["NAPLES25SWM"] = "naples_fw_iris_1.64.0-E-58_2023_02_14.tar"
    mainfw_dat["NAPLES25SWM"] = ""

    cpld_img["NAPLES25SWMDELL"] = "naples25_swmdell_rev3_01062021.bin"
    cpld_ver["NAPLES25SWMDELL"] = "0x3"
    cpld_dat["NAPLES25SWMDELL"] = "00"
    sec_cpld_img["NAPLES25SWMDELL"] = "naples25_swmdell_rev83_01062021.bin"
    sec_cpld_ver["NAPLES25SWMDELL"] = "0x83"
    sec_cpld_dat["NAPLES25SWMDELL"] = "00"
    diagfw_img["NAPLES25SWMDELL"] = "naples_diagfw-1.3.1-E-43-EMMC-030321.tar"
    diagfw_dat["NAPLES25SWMDELL"] = "03-03-2021"
    goldfw_img["NAPLES25SWMDELL"] = "capri_goldfw_1.3.1-E-59_2022.07.14.tar"
    goldfw_dat["NAPLES25SWMDELL"] = "04-25-2022"
    mainfw_img["NAPLES25SWMDELL"] = "naples_fw_iris_1.28.2-E-93_2022_05_03.tar"
    mainfw_dat["NAPLES25SWMDELL"] = ""

    # OCP HPE (P37689-001) and OCP DELL (68-0010)
    cpld_img["NAPLES25OCP"] = "NAPLES25_OCP_REV0B_03102021.bin"
    cpld_ver["NAPLES25OCP"] = "0xB"
    cpld_dat["NAPLES25OCP"] = "01-10"
    sec_cpld_img["NAPLES25OCP"] = "NAPLES25_OCP_REV8B_03102021.bin"
    sec_cpld_ver["NAPLES25OCP"] = "0x8B"
    sec_cpld_dat["NAPLES25OCP"] = "01-10"
    diagfw_img["NAPLES25OCP"] = "naples_diagfw-1.3.1-E-43-EMMC-030321.tar"
    diagfw_dat["NAPLES25OCP"] = "03-03-2021"
    goldfw_img["NAPLES25OCP"] = "capri_goldfw_1.3.1-E-59_2022.07.14.tar"
    goldfw_dat["NAPLES25OCP"] = "04-25-2022"
    mainfw_img["NAPLES25OCP"] = "naples_fw_iris_1.64.0-E-58_2023_02_14.tar"
    mainfw_dat["NAPLES25OCP"] = ""

    cpld_img["NAPLES100"] = "naples100_cpld_rev9_05312019.bin"
    cpld_ver["NAPLES100"] = "0x9"
    cpld_dat["NAPLES100"] = "05-31"
    sec_cpld_img["NAPLES100"] = "naples100_02_rv89_06032019.bin"
    sec_cpld_ver["NAPLES100"] = "0x89"
    sec_cpld_dat["NAPLES100"] = "06-03"
    diagfw_img["NAPLES100"] = "naples_diagfw_05212020.tar"
    diagfw_dat["NAPLES100"] = "05-21-2020"
    goldfw_img["NAPLES100"] = "naples_goldfw_09182019.tar"
    goldfw_dat["NAPLES100"] = "09-17-2019"
    mainfw_img["NAPLES100"] = "capri_fw_iris_1.4.0-E-110_2022.09.28.tar"
    mainfw_dat["NAPLES100"] = ""

    cpld_img["NAPLES100IBM"] = "naples100_ibm_rev3_09082020.bin"
    cpld_ver["NAPLES100IBM"] = "0x3"
    cpld_dat["NAPLES100IBM"] = "09-08"
    sec_cpld_img["NAPLES100IBM"] = "naples100_ibm_rev83_09082020.bin"
    sec_cpld_ver["NAPLES100IBM"] = "0x83"
    sec_cpld_dat["NAPLES100IBM"] = "09-08"
    diagfw_img["NAPLES100IBM"] = "naples_diagfw_1.3.1-E-21_0521.tar"
    diagfw_dat["NAPLES100IBM"] = "05-21-2020"
    goldfw_img["NAPLES100IBM"] = "naples_goldfw_apulu_1.17.0-42_1117.tar"
    goldfw_dat["NAPLES100IBM"] = "10-17-2020"

    # ### ORTANO MSFT (68-0021)
    # cpld_img["ORTANO2"] = "naples200_ortano2_rev3_A_04202022.bin"
    # cpld_ver["ORTANO2"] = "0x3"
    # cpld_dat["ORTANO2"] = "0x0A"
    # sec_cpld_img["ORTANO2"] = "naples200_ortano2_rev3_A_04202022.bin"
    # sec_cpld_ver["ORTANO2"] = "0x3"
    # sec_cpld_dat["ORTANO2"] = "0x0A"
    # fail_cpld_img["ORTANO2"] = "naples200_ortano2_failsafe_rev3_A_04202022.bin"
    # fail_cpld_ver["ORTANO2"] = "0x3"
    # fail_cpld_dat["ORTANO2"] = "0x0A"
    # fea_cpld_img["ORTANO2"] = "naples200_ortano2_fea_04272021.bin"
    # diagfw_img["ORTANO2"] = "naples_diagfw_elba_1.51.0-G-9.2022.11.17.tar"
    # diagfw_dat["ORTANO2"] = "10-27-2022"
    # goldfw_img["ORTANO2"] = "naples_goldfw_elba_1.51.0-G-9.2022.11.17.tar"
    # goldfw_dat["ORTANO2"] = "10-26-2022"
    # uboot_img["ORTANO2"] = "boot0.rev14.img"
    # uboot_dat["ORTANO2"] = "14"

    ### ORTANO ORACLE (68-0015)
    cpld_img["ORTANO2"] = "ortano_02_working_rev3.14_033023.bin"
    cpld_ver["ORTANO2"] = "0x3"
    cpld_dat["ORTANO2"] = "0x14"
    sec_cpld_img["ORTANO2"] = "ortano_02_working_rev3.14_033023.bin"
    sec_cpld_ver["ORTANO2"] = "0x3"
    sec_cpld_dat["ORTANO2"] = "0x14"
    fail_cpld_img["ORTANO2"] = "ortano_02_rev3.14_failsafe_033023.bin"
    fail_cpld_ver["ORTANO2"] = "0x3"
    fail_cpld_dat["ORTANO2"] = "0x14"
    fea_cpld_img["ORTANO2"] = "naples200_ortano2_fea_04272021.bin"
    diagfw_img["ORTANO2"] = "elba_diagfw_1.15.9-C-145_2023.05.03.tar"
    diagfw_dat["ORTANO2"] = "05-03-2023"
    goldfw_img["ORTANO2"] = "elba_goldfw_1.15.9-C-145_2023.05.03.tar"
    goldfw_dat["ORTANO2"] = "05-03-2023"
    uboot_img["ORTANO2"] = "boot0.rev14.img"
    uboot_dat["ORTANO2"] = "14"

    diagfw_img["68-0015"] = "elba_diagfw_1.15.9-C-145_2023.05.03.tar"
    diagfw_dat["68-0015"] = "05-03-2023"
    goldfw_img["68-0015"] = "elba_goldfw_1.15.9-C-145_2023.05.03.tar"
    goldfw_dat["68-0015"] = "05-03-2023"
    mainfw_img["68-0015"] = "dsc_fw_elba_1.15.9-C-145_2023.05.03.tar"
    mainfw_dat["68-0015"] = ""

    cpld_img["POMONTEDELL"] = "naples200_pom_dell_main_rev2_8_08162022.bin"
    cpld_ver["POMONTEDELL"] = "0x2"
    cpld_dat["POMONTEDELL"] = "0x08"
    sec_cpld_img["POMONTEDELL"] = "naples200_pom_dell_gold_rev2_8_08162022.bin"
    sec_cpld_ver["POMONTEDELL"] = "0x2"
    sec_cpld_dat["POMONTEDELL"] = "0x08"
    fail_cpld_img["POMONTEDELL"] = "naples200_pom_dell_gold_rev2_8_08162022.bin"
    fail_cpld_ver["POMONTEDELL"] = "0x2"
    fail_cpld_dat["POMONTEDELL"] = "0x08"
    timer1_img["POMONTEDELL"] = "naples200_timer1_08162022.bin"
    timer2_img["POMONTEDELL"] = "naples200_timer2_08162022.bin"
    test_fpga_img["POMONTEDELL"] = "naples200_pom_dell_main_rev2_B_10272022.bin"
    test_fpga_ver["POMONTEDELL"] = "0x2"
    test_fpga_dat["POMONTEDELL"] = "0x0B"
    diagfw_img["POMONTEDELL"] = "naples_diagfw_elba_1.46.0-E-31_2022.08.16.tar"
    diagfw_dat["POMONTEDELL"] = "08-16-2022"
    goldfw_img["POMONTEDELL"] = "naples_goldfw_elba_1.46.0-E-31_2022.08.16.tar"
    goldfw_dat["POMONTEDELL"] = "08-16-2022"
    uboot_img["POMONTEDELL"] = "boot0.rev14.img"
    uboot_dat["POMONTEDELL"] = "14"
    mainfw_img["POMONTEDELL"] = "naples_uefi_sb_prod_diag_fw_elba_1.46.0-E-31_2022.08.16.tar"
    mainfw_dat["POMONTEDELL"] = ""

    cpld_img["LACONA32DELL"] = "naples200_lac32_dell_main_rev2_8_08162022.bin"
    cpld_ver["LACONA32DELL"] = "0x2"
    cpld_dat["LACONA32DELL"] = "0x08"
    sec_cpld_img["LACONA32DELL"] = "naples200_lac32_dell_main_rev2_8_08162022.bin"
    sec_cpld_ver["LACONA32DELL"] = "0x2"
    sec_cpld_dat["LACONA32DELL"] = "0x08"
    fail_cpld_img["LACONA32DELL"] = "naples200_lac32_dell_gold_rev2_8_08162022.bin"
    fail_cpld_ver["LACONA32DELL"] = "0x2"
    fail_cpld_dat["LACONA32DELL"] = "0x08"
    timer1_img["LACONA32DELL"] = "naples200_timer1_08162022.bin"
    timer2_img["LACONA32DELL"] = "naples200_timer2_08162022.bin"
    test_fpga_img["LACONA32DELL"] = "naples200_lac32_dell_main_rev2_B_10272022.bin"
    test_fpga_ver["LACONA32DELL"] = "0x2"
    test_fpga_dat["LACONA32DELL"] = "0x0B"
    diagfw_img["LACONA32DELL"] = "naples_diagfw_elba_1.46.0-E-31_2022.08.16.tar"
    diagfw_dat["LACONA32DELL"] = "08-16-2022"
    goldfw_img["LACONA32DELL"] = "naples_goldfw_elba_1.46.0-E-31_2022.08.16.tar"
    goldfw_dat["LACONA32DELL"] = "08-16-2022"
    uboot_img["LACONA32DELL"] = "boot0.rev14.img"
    uboot_dat["LACONA32DELL"] = "14"
    mainfw_img["LACONA32DELL"] = "naples_uefi_sb_prod_diag_fw_elba_1.46.0-E-31_2022.08.16.tar"
    mainfw_dat["LACONA32DELL"] = ""

    cpld_img["LACONA32"] = "naples200_lac32_hpe_main_rev2_8_08162022.bin"
    cpld_ver["LACONA32"] = "0x2"
    cpld_dat["LACONA32"] = "0x08"
    sec_cpld_img["LACONA32"] = "naples200_lac32_hpe_main_rev2_8_08162022.bin"
    sec_cpld_ver["LACONA32"] = "0x2"
    sec_cpld_dat["LACONA32"] = "0x08"
    fail_cpld_img["LACONA32"] = "naples200_lac32_hpe_gold_rev2_8_08162022.bin"
    fail_cpld_ver["LACONA32"] = "0x2"
    fail_cpld_dat["LACONA32"] = "0x08"
    timer1_img["LACONA32"] = "naples200_timer1_08162022.bin"
    timer2_img["LACONA32"] = "naples200_timer2_08162022.bin"
    test_fpga_img["LACONA32"] = "naples200_lac32_hpe_main_rev2_B_10272022.bin"
    test_fpga_ver["LACONA32"] = "0x2"
    test_fpga_dat["LACONA32"] = "0x0B"
    diagfw_img["LACONA32"] = "naples_diagfw_elba_1.46.0-E-31_2022.08.16.tar"
    diagfw_dat["LACONA32"] = "08-16-2022"
    goldfw_img["LACONA32"] = "naples_goldfw_elba_1.46.0-E-31_2022.08.16.tar"
    goldfw_dat["LACONA32"] = "08-16-2022"
    uboot_img["LACONA32"] = "boot0.rev14.img"
    uboot_dat["LACONA32"] = "14"
    mainfw_img["LACONA32"] = "naples_uefi_sb_prod_diag_fw_elba_1.46.0-E-31_2022.08.16.tar"
    mainfw_dat["LACONA32"] = ""

    cpld_img["ORTANO2ADI"] = "ortano_adi_rev1.14_working_041023_12pm.bin"
    cpld_ver["ORTANO2ADI"] = "0x1"
    cpld_dat["ORTANO2ADI"] = "0x14"
    sec_cpld_img["ORTANO2ADI"] = "ortano_adi_rev1.14_working_041023_12pm.bin"
    sec_cpld_ver["ORTANO2ADI"] = "0x1"
    sec_cpld_dat["ORTANO2ADI"] = "0x14"
    fail_cpld_img["ORTANO2ADI"] = "ortano_adi_failsafe_rev3.14_033023.bin"
    fail_cpld_ver["ORTANO2ADI"] = "0x3"
    fail_cpld_dat["ORTANO2ADI"] = "0x14"
    fea_cpld_img["ORTANO2ADI"] = "naples200_ortano2A_fea_rev3_D_06082022.bin"
    diagfw_img["ORTANO2ADI"] = "elba_diagfw_1.15.9-C-145_2023.05.03.tar"
    diagfw_dat["ORTANO2ADI"] = "05-03-2023"
    goldfw_img["ORTANO2ADI"] = "elba_goldfw_1.15.9-C-145_2023.05.03.tar"
    goldfw_dat["ORTANO2ADI"] = "05-03-2023"
    uboot_img["ORTANO2ADI"] = "boot0.rev14.img"
    uboot_dat["ORTANO2ADI"] = "14"
    cpld_img["68-0026"] = "ortano_adi_working_rev3.14_033023.bin"
    cpld_ver["68-0026"] = "0x3"
    cpld_dat["68-0026"] = "0x14"
    sec_cpld_img["68-0026"] = "ortano_adi_working_rev3.14_033023.bin"
    sec_cpld_ver["68-0026"] = "0x3"
    sec_cpld_dat["68-0026"] = "0x14"
    fail_cpld_img["68-0026"] = "ortano_adi_failsafe_rev3.14_033023.bin"
    fail_cpld_ver["68-0026"] = "0x3"
    fail_cpld_dat["68-0026"] = "0x14"
    goldfw_img["68-0026"] = "elba_goldfw_1.15.9-C-145_2023.05.03.tar"
    goldfw_dat["68-0026"] = "05-03-2023"
    mainfw_img["68-0026"] = "dsc_fw_elba_1.15.9-C-145_2023.05.03.tar"
    mainfw_dat["68-0026"] = ""
    #IBM ADI
    cpld_img["ORTANO2ADIIBM"] = "ortano_adi_rev1.14_working_041023_12pm.bin"
    cpld_ver["ORTANO2ADIIBM"] = "0x1"
    cpld_dat["ORTANO2ADIIBM"] = "0x14"
    sec_cpld_img["ORTANO2ADIIBM"] = "ortano_adi_rev1.14_working_041023_12pm.bin"
    sec_cpld_ver["ORTANO2ADIIBM"] = "0x1"
    sec_cpld_dat["ORTANO2ADIIBM"] = "0x14"
    fail_cpld_img["ORTANO2ADIIBM"] = "ortano_adi_failsafe_rev3.14_033023.bin"
    fail_cpld_ver["ORTANO2ADIIBM"] = "0x3"
    fail_cpld_dat["ORTANO2ADIIBM"] = "0x14"
    fea_cpld_img["ORTANO2ADIIBM"] = "naples200_ortano2A_fea_rev3_C_01192022.bin"
    diagfw_img["ORTANO2ADIIBM"] = "elba_diagfw_1.51.0-G-37_2023.05.17.tar"
    diagfw_dat["ORTANO2ADIIBM"] = "05-17-2023"
    goldfw_img["ORTANO2ADIIBM"] = "elba_goldfw_1.51.0-G-37_2023.05.17.tar"
    goldfw_dat["ORTANO2ADIIBM"] = "05-17-2023"
    uboot_img["ORTANO2ADIIBM"] = "boot0.1.51.0-G-37.img"
    uboot_dat["ORTANO2ADIIBM"] = "18"
    uboota_img["ORTANO2ADIIBM"] = "fip_1.51.0-G-37_2023.05.30.img"
    ubootb_img["ORTANO2ADIIBM"] = "fip_1.51.0-G-37_2023.05.30.img"
    cert_img["68-0028"] = "canon-prod-pkcerts.bin"
    cpld_img["68-0028"] = "ortano_adi_working_rev3.14_033023.bin"
    cpld_ver["68-0028"] = "0x3"
    cpld_dat["68-0028"] = "0x14"
    sec_cpld_img["68-0028"] = "ortano_adi_rev83.14_working_secure_033023.bin"
    sec_cpld_ver["68-0028"] = "0x83"
    sec_cpld_dat["68-0028"] = "0x14"
    fail_cpld_img["68-0028"] = "ortano_adi_failsafe_secure_rev83.14_033023.bin"
    fail_cpld_ver["68-0028"] = "0x83"
    fail_cpld_dat["68-0028"] = "0x14"
    goldfw_img["68-0028"] = "naples_sec_goldfw_prod_1.51.0-G-37_2023.05.30.tar"
    goldfw_dat["68-0028"] = "05-17-2023"
    
    #MSFT ADI
    cpld_img["ORTANO2ADIMSFT"] = "ortano_adi_rev1.14_working_041023_12pm.bin"
    cpld_ver["ORTANO2ADIMSFT"] = "0x1"
    cpld_dat["ORTANO2ADIMSFT"] = "0x14"
    sec_cpld_img["ORTANO2ADIMSFT"] = "ortano_adi_rev1.14_working_041023_12pm.bin"
    sec_cpld_ver["ORTANO2ADIMSFT"] = "0x1"
    sec_cpld_dat["ORTANO2ADIMSFT"] = "0x14"
    fail_cpld_img["ORTANO2ADIMSFT"] = "ortano_adi_failsafe_rev3.14_033023.bin"
    fail_cpld_ver["ORTANO2ADIMSFT"] = "0x3"
    fail_cpld_dat["ORTANO2ADIMSFT"] = "0x14"
    fea_cpld_img["ORTANO2ADIMSFT"] = "naples200_ortano2A_fea_rev3_C_01192022.bin"
    diagfw_img["ORTANO2ADIMSFT"] = "elba_diagfw_1.51.0-G-37_2023.05.17.tar"
    diagfw_dat["ORTANO2ADIMSFT"] = "05-17-2023"
    goldfw_img["ORTANO2ADIMSFT"] = "elba_goldfw_1.51.0-G-37_2023.05.17.tar"
    goldfw_dat["ORTANO2ADIMSFT"] = "05-17-2023"
    uboot_img["ORTANO2ADIMSFT"] = "boot0.rev14.img"
    uboot_dat["ORTANO2ADIMSFT"] = "14"
    cpld_img["68-0034"] = "ortano_adi_working_rev3.14_033023.bin"
    cpld_ver["68-0034"] = "0x3"
    cpld_dat["68-0034"] = "0x14"
    sec_cpld_img["68-0034"] = "ortano_adi_working_rev3.14_033023.bin"
    sec_cpld_ver["68-0034"] = "0x3"
    sec_cpld_dat["68-0034"] = "0x14"
    fail_cpld_img["68-0034"] = "ortano_adi_failsafe_rev3.14_033023.bin"
    fail_cpld_ver["68-0034"] = "0x3"
    fail_cpld_dat["68-0034"] = "0x14"
    goldfw_img["68-0034"] = "elba_goldfw_1.51.0-G-37_2023.05.17.tar"
    goldfw_dat["68-0034"] = "05-17-2023"
    mainfw_img["68-0034"] = "dsc_fw_elba_1.61.0-C-96-3_2023.09.29.tar"
    mainfw_dat["68-0034"] = ""

    cpld_img["ORTANO2INTERP"] = "ortano_interposer_working_rev3.14_033023.bin"
    cpld_ver["ORTANO2INTERP"] = "0x3"
    cpld_dat["ORTANO2INTERP"] = "0x14"
    sec_cpld_img["ORTANO2INTERP"] = "ortano_interposer_working_rev3.14_033023.bin"
    sec_cpld_ver["ORTANO2INTERP"] = "0x3"
    sec_cpld_dat["ORTANO2INTERP"] = "0x14"
    fail_cpld_img["ORTANO2INTERP"] = "ortano_interposer_failsafe_rev3.14_033023.bin"
    fail_cpld_ver["ORTANO2INTERP"] = "0x3"
    fail_cpld_dat["ORTANO2INTERP"] = "0x14"
    fea_cpld_img["ORTANO2INTERP"] = "naples200_ortano2A_fea_rev3_A_01062022.bin"
    diagfw_img["ORTANO2INTERP"] = "elba_diagfw_1.15.9-C-145_2023.05.03.tar"
    diagfw_dat["ORTANO2INTERP"] = "05-03-2023"
    goldfw_img["ORTANO2INTERP"] = "elba_goldfw_1.15.9-C-145_2023.05.03.tar"
    goldfw_dat["ORTANO2INTERP"] = "05-03-2023"
    mainfw_img["ORTANO2INTERP"] = "dsc_fw_elba_1.15.9-C-145_2023.05.03.tar"
    mainfw_dat["ORTANO2INTERP"] = ""

    cpld_img["ORTANO2SOLO"] = "ortano_solo_working_rev1.5_033123.bin"
    cpld_ver["ORTANO2SOLO"] = "0x1"
    cpld_dat["ORTANO2SOLO"] = "0x05"
    sec_cpld_img["ORTANO2SOLO"] = "ortano_solo_working_rev1.5_033123.bin"
    sec_cpld_ver["ORTANO2SOLO"] = "0x1"
    sec_cpld_dat["ORTANO2SOLO"] = "0x05"
    fail_cpld_img["ORTANO2SOLO"] = "ortano_solo_failsafe_rev1.5_033123.bin"
    fail_cpld_ver["ORTANO2SOLO"] = "0x1"
    fail_cpld_dat["ORTANO2SOLO"] = "0x05"
    fea_cpld_img["ORTANO2SOLO"] = "naples200_ortano2S_fea_rev1_0_1_10252022.bin"
    diagfw_img["ORTANO2SOLO"] = "elba_diagfw_1.15.9-C-154_2024.04.05.tar"
    diagfw_dat["ORTANO2SOLO"] = "04-05-2024"
    goldfw_img["ORTANO2SOLO"] = "elba_goldfw_1.15.9-C-154_2024.04.05.tar"
    goldfw_dat["ORTANO2SOLO"] = "04-05-2024"
    mainfw_img["ORTANO2SOLO"] = "dsc_fw_elba_1.15.9-C-154_2024.04.05.tar"
    mainfw_dat["ORTANO2SOLO"] = ""

    # Ortano2 SOLO Oracle R4-L
    cpld_img["ORTANO2SOLOL"] = "ortano_solo_working_rev1.5_033123.bin"
    cpld_ver["ORTANO2SOLOL"] = "0x1"
    cpld_dat["ORTANO2SOLOL"] = "0x05"
    sec_cpld_img["ORTANO2SOLOL"] = "ortano_solo_working_rev1.5_033123.bin"
    sec_cpld_ver["ORTANO2SOLOL"] = "0x1"
    sec_cpld_dat["ORTANO2SOLOL"] = "0x05"
    fail_cpld_img["ORTANO2SOLOL"] = "ortano_solo_failsafe_rev1.5_033123.bin"
    fail_cpld_ver["ORTANO2SOLOL"] = "0x1"
    fail_cpld_dat["ORTANO2SOLOL"] = "0x05"
    fea_cpld_img["ORTANO2SOLOL"] = "naples200_ortano2S_fea_rev1_0_1_10252022.bin"
    diagfw_img["ORTANO2SOLOL"] = "elba_diagfw_1.15.9-C-154_2024.04.05.tar"
    diagfw_dat["ORTANO2SOLOL"] = "04-05-2024"
    goldfw_img["ORTANO2SOLOL"] = "elba_goldfw_1.15.9-C-154_2024.04.05.tar"
    goldfw_dat["ORTANO2SOLOL"] = "04-05-2024"
    mainfw_img["ORTANO2SOLOL"] = "dsc_fw_elba_1.15.9-C-154_2024.04.05.tar"
    mainfw_dat["ORTANO2SOLOL"] = ""

    # Ortano2 SOLO Oracle Tall Heat Sink
    cpld_img["ORTANO2SOLOORCTHS"] = "ortano_solo_working_rev1.5_033123.bin"
    cpld_ver["ORTANO2SOLOORCTHS"] = "0x1"
    cpld_dat["ORTANO2SOLOORCTHS"] = "0x05"
    sec_cpld_img["ORTANO2SOLOORCTHS"] = "ortano_solo_working_rev1.5_033123.bin"
    sec_cpld_ver["ORTANO2SOLOORCTHS"] = "0x1"
    sec_cpld_dat["ORTANO2SOLOORCTHS"] = "0x05"
    fail_cpld_img["ORTANO2SOLOORCTHS"] = "ortano_solo_failsafe_rev1.5_033123.bin"
    fail_cpld_ver["ORTANO2SOLOORCTHS"] = "0x1"
    fail_cpld_dat["ORTANO2SOLOORCTHS"] = "0x05"
    fea_cpld_img["ORTANO2SOLOORCTHS"] = "naples200_ortano2S_fea_rev1_0_1_10252022.bin"
    diagfw_img["ORTANO2SOLOORCTHS"] = "elba_diagfw_1.15.9-C-154_2024.04.05.tar"
    diagfw_dat["ORTANO2SOLOORCTHS"] = "04-05-2024"
    goldfw_img["ORTANO2SOLOORCTHS"] = "elba_goldfw_1.15.9-C-154_2024.04.05.tar"
    goldfw_dat["ORTANO2SOLOORCTHS"] = "04-05-2024"
    mainfw_img["ORTANO2SOLOORCTHS"] = "dsc_fw_elba_1.15.9-C-154_2024.04.05.tar"
    mainfw_dat["ORTANO2SOLOORCTHS"] = ""

    # Ortano2 SOLO Microsoft
    cpld_img["ORTANO2SOLOMSFT"] = "ortano_solo_working_rev1.5_033123.bin"
    cpld_ver["ORTANO2SOLOMSFT"] = "0x1"
    cpld_dat["ORTANO2SOLOMSFT"] = "0x05"
    sec_cpld_img["ORTANO2SOLOMSFT"] = "ortano_solo_working_rev1.5_033123.bin"
    sec_cpld_ver["ORTANO2SOLOMSFT"] = "0x1"
    sec_cpld_dat["ORTANO2SOLOMSFT"] = "0x05"
    fail_cpld_img["ORTANO2SOLOMSFT"] = "ortano_solo_failsafe_rev1.5_033123.bin"
    fail_cpld_ver["ORTANO2SOLOMSFT"] = "0x1"
    fail_cpld_dat["ORTANO2SOLOMSFT"] = "0x05"
    fea_cpld_img["ORTANO2SOLOMSFT"] = "naples200_ortano2S_fea_rev1_0_1_10252022.bin"
    diagfw_img["ORTANO2SOLOMSFT"] = "elba_diagfw_1.51.0-G-37_2023.05.17.tar"
    diagfw_dat["ORTANO2SOLOMSFT"] = "05-17-2023"
    goldfw_img["ORTANO2SOLOMSFT"] = "elba_goldfw_1.51.0-G-37_2023.05.17.tar"
    goldfw_dat["ORTANO2SOLOMSFT"] = "05-17-2023"
    mainfw_img["ORTANO2SOLOMSFT"] = "dsc_fw_elba_1.61.0-C-96-3_2023.09.29.tar"
    mainfw_dat["ORTANO2SOLOMSFT"] = ""

    # Ortano2 SOLO S4 # No Mainfw
    cpld_img["ORTANO2SOLOS4"] = "ortano_solo_working_rev1.5_033123.bin"
    cpld_ver["ORTANO2SOLOS4"] = "0x1"
    cpld_dat["ORTANO2SOLOS4"] = "0x05"
    sec_cpld_img["ORTANO2SOLOS4"] = "ortano_solo_working_rev1.5_033123.bin"
    sec_cpld_ver["ORTANO2SOLOS4"] = "0x1"
    sec_cpld_dat["ORTANO2SOLOS4"] = "0x05"
    fail_cpld_img["ORTANO2SOLOS4"] = "ortano_solo_failsafe_rev1.5_033123.bin"
    fail_cpld_ver["ORTANO2SOLOS4"] = "0x1"
    fail_cpld_dat["ORTANO2SOLOS4"] = "0x05"
    fea_cpld_img["ORTANO2SOLOS4"] = "naples200_ortano2S_fea_rev1_0_1_10252022.bin"
    diagfw_img["ORTANO2SOLOS4"] = "elba_diagfw_1.51.0-G-37_2023.05.17.tar"
    diagfw_dat["ORTANO2SOLOS4"] = "05-17-2023"
    goldfw_img["ORTANO2SOLOS4"] = "elba_goldfw_1.51.0-G-37_2023.05.17.tar"
    goldfw_dat["ORTANO2SOLOS4"] = "05-17-2023"
    uboot_img["ORTANO2SOLOS4"] = "boot0.1.51.0-G-37.img"

    # ORTANO2ADI CR
    cpld_img["ORTANO2ADICR"] = "ortano_adi_cr_working_rev1.5_033123.bin"
    cpld_ver["ORTANO2ADICR"] = "0x1"
    cpld_dat["ORTANO2ADICR"] = "0x05"
    sec_cpld_img["ORTANO2ADICR"] = "ortano_adi_cr_working_rev1.5_033123.bin"
    sec_cpld_ver["ORTANO2ADICR"] = "0x1"
    sec_cpld_dat["ORTANO2ADICR"] = "0x05"
    fail_cpld_img["ORTANO2ADICR"] = "ortano_adi_cr_failsafe_rev1.5_033123.bin"
    fail_cpld_ver["ORTANO2ADICR"] = "0x1"
    fail_cpld_dat["ORTANO2ADICR"] = "0x05"
    fea_cpld_img["ORTANO2ADICR"] = "ortano_adi_cr_rev1.2_fea_11162022.bin"
    diagfw_img["ORTANO2ADICR"] = "elba_diagfw_1.15.9-C-154_2024.04.05.tar"
    diagfw_dat["ORTANO2ADICR"] = "04-05-2024"
    goldfw_img["ORTANO2ADICR"] = "elba_goldfw_1.15.9-C-154_2024.04.05.tar"
    goldfw_dat["ORTANO2ADICR"] = "04-05-2024"
    uboot_img["ORTANO2ADICR"] = "boot0.1.15.9-C-154.img"
    uboot_dat["ORTANO2ADICR"] = ""
    cpld_img["68-0049"] = "ortano_adi_cr_working_rev1.5_033123.bin"
    cpld_ver["68-0049"] = "0x1"
    cpld_dat["68-0049"] = "0x05"
    sec_cpld_img["68-0049"] = "ortano_adi_cr_working_rev1.5_033123.bin"
    sec_cpld_ver["68-0049"] = "0x1"
    sec_cpld_dat["68-0049"] = "0x05"
    fail_cpld_img["68-0049"] = "ortano_adi_cr_failsafe_rev1.5_033123.bin"
    fail_cpld_ver["68-0049"] = "0x1"
    fail_cpld_dat["68-0049"] = "0x05"
    goldfw_img["68-0049"] = "elba_goldfw_1.15.9-C-154_2024.04.05.tar"
    goldfw_dat["68-0049"] = "04-05-2024"
    mainfw_img["68-0049"] = "dsc_fw_elba_1.15.9-C-154_2024.04.05.tar"
    mainfw_dat["68-0049"] = ""

    # ORTANO2ADI CR Mircosoft
    cpld_img["ORTANO2ADICRMSFT"] = "ortano_adi_cr_working_rev1.5_033123.bin"
    cpld_ver["ORTANO2ADICRMSFT"] = "0x1"
    cpld_dat["ORTANO2ADICRMSFT"] = "0x05"
    sec_cpld_img["ORTANO2ADICRMSFT"] = "ortano_adi_cr_working_rev1.5_033123.bin"
    sec_cpld_ver["ORTANO2ADICRMSFT"] = "0x1"
    sec_cpld_dat["ORTANO2ADICRMSFT"] = "0x05"
    fail_cpld_img["ORTANO2ADICRMSFT"] = "ortano_adi_cr_failsafe_rev1.5_033123.bin"
    fail_cpld_ver["ORTANO2ADICRMSFT"] = "0x1"
    fail_cpld_dat["ORTANO2ADICRMSFT"] = "0x05"
    fea_cpld_img["ORTANO2ADICRMSFT"] = "ortano_adi_cr_rev1.2_fea_11162022.bin"
    diagfw_img["ORTANO2ADICRMSFT"] = "elba_diagfw_1.51.0-G-37_2023.05.17.tar"
    diagfw_dat["ORTANO2ADICRMSFT"] = "05-17-2023"
    goldfw_img["ORTANO2ADICRMSFT"] = "elba_goldfw_1.51.0-G-37_2023.05.17.tar"
    goldfw_dat["ORTANO2ADICRMSFT"] = "05-17-2023"
    uboot_img["ORTANO2ADICRMSFT"] = "boot0.1.15.9-C-134.img"
    uboot_dat["ORTANO2ADICRMSFT"] = ""
    cpld_img["68-0091"] = "ortano_adi_cr_working_rev1.5_033123.bin"
    cpld_ver["68-0091"] = "0x1"
    cpld_dat["68-0091"] = "0x05"
    sec_cpld_img["68-0091"] = "ortano_adi_cr_working_rev1.5_033123.bin"
    sec_cpld_ver["68-0091"] = "0x1"
    sec_cpld_dat["68-0091"] = "0x05"
    fail_cpld_img["68-0091"] = "ortano_adi_cr_failsafe_rev1.5_033123.bin"
    fail_cpld_ver["68-0091"] = "0x1"
    fail_cpld_dat["68-0091"] = "0x05"
    goldfw_img["68-0091"] = "elba_goldfw_1.51.0-G-37_2023.05.17.tar"
    goldfw_dat["68-0091"] = "05-17-2023"
    mainfw_img["68-0091"] = "dsc_fw_elba_1.61.0-C-96-3_2023.09.29.tar"
    mainfw_dat["68-0091"] = ""

    # ORTANO2ADI CR S4 # No Mainfw
    cpld_img["ORTANO2ADICRS4"] = "ortano_adi_cr_working_rev1.5_033123.bin"
    cpld_ver["ORTANO2ADICRS4"] = "0x1"
    cpld_dat["ORTANO2ADICRS4"] = "0x05"
    sec_cpld_img["ORTANO2ADICRS4"] = "ortano_adi_cr_working_rev1.5_033123.bin"
    sec_cpld_ver["ORTANO2ADICRS4"] = "0x1"
    sec_cpld_dat["ORTANO2ADICRS4"] = "0x05"
    fail_cpld_img["ORTANO2ADICRS4"] = "ortano_adi_cr_failsafe_rev1.5_033123.bin"
    fail_cpld_ver["ORTANO2ADICRS4"] = "0x1"
    fail_cpld_dat["ORTANO2ADICRS4"] = "0x05"
    fea_cpld_img["ORTANO2ADICRS4"] = "ortano_adi_cr_rev1.2_fea_11162022.bin"
    diagfw_img["ORTANO2ADICRS4"] = "elba_diagfw_1.51.0-G-37_2023.05.17.tar"
    diagfw_dat["ORTANO2ADICRS4"] = "05-17-2023"
    goldfw_img["ORTANO2ADICRS4"] = "elba_goldfw_1.51.0-G-37_2023.05.17.tar"
    goldfw_dat["ORTANO2ADICRS4"] = "05-17-2023"
    uboot_img["ORTANO2ADICRS4"] = "boot0.1.51.0-G-37.img"
    uboot_dat["ORTANO2ADICRS4"] = ""

    cpld_img["GINESTRA_D4"] = "ginestra_d4_rev1.2_working.bin"
    cpld_ver["GINESTRA_D4"] = "0x1"
    cpld_dat["GINESTRA_D4"] = "0x02"
    sec_cpld_img["GINESTRA_D4"] = "ginestra_d4_rev1.2_working.bin"
    sec_cpld_ver["GINESTRA_D4"] = "0x1"
    sec_cpld_dat["GINESTRA_D4"] = "0x02"
    fail_cpld_img["GINESTRA_D4"] = "ginestra_d4_rev1.2_failsafe.bin"
    fail_cpld_ver["GINESTRA_D4"] = "0x1"
    fail_cpld_dat["GINESTRA_D4"] = "0x02"
    fea_cpld_img["GINESTRA_D4"] = "ginestra_impl1.bin"
    diagfw_img["GINESTRA_D4"] = "naples_diagfw_elba_1.68-G-4_2023.08.21.tar"
    diagfw_dat["GINESTRA_D4"] = "08-21-2023"
    goldfw_img["GINESTRA_D4"] = "naples_goldfw_elba_1.68-G-4_2023.08.21.tar"
    goldfw_dat["GINESTRA_D4"] = "08-21-2023"
    mainfw_img["GINESTRA_D4"] = "dsc_fw_elba_1.64.0-31.tar"
    mainfw_dat["GINESTRA_D4"] = ""

    cpld_img["GINESTRA_D5"] = "ginestra_d5_rev2_7_working_12132023.bin"
    cpld_ver["GINESTRA_D5"] = "0x2"
    cpld_dat["GINESTRA_D5"] = "0x07"
    sec_cpld_img["GINESTRA_D5"] = "ginestra_d5_rev2_7_working_12132023.bin"
    sec_cpld_ver["GINESTRA_D5"] = "0x2"
    sec_cpld_dat["GINESTRA_D5"] = "0x07"
    fail_cpld_img["GINESTRA_D5"] = "ginestra_d5_rev2_7_failsafe_12132023.bin"
    fail_cpld_ver["GINESTRA_D5"] = "0x2"
    fail_cpld_dat["GINESTRA_D5"] = "0x07"
    fea_cpld_img["GINESTRA_D5"] = "ginestra_impl1.bin"
    diagfw_img["GINESTRA_D5"] = "naples_diagfw_elba_1.68-G-9_2024.02.29.tar"
    diagfw_dat["GINESTRA_D5"] = "12-14-2023"
    goldfw_img["GINESTRA_D5"] = "naples_goldfw_elba_1.68-G-9_2024.02.29.tar"
    goldfw_dat["GINESTRA_D5"] = "12-13-2023"
    mainfw_img["GINESTRA_D5"] = "dsc_fw_elba_1.65.0-C-12-12_2023.08.21.tar"
    mainfw_dat["GINESTRA_D5"] = ""

    cpld_img["GINESTRA_CIS"] = "ginestra_d5_rev2_7_working_12132023.bin"
    cpld_ver["GINESTRA_CIS"] = "0x2"
    cpld_dat["GINESTRA_CIS"] = "0x07"
    sec_cpld_img["GINESTRA_CIS"] = "ginestra_d5_rev2_7_working_12132023.bin"
    sec_cpld_ver["GINESTRA_CIS"] = "0x2"
    sec_cpld_dat["GINESTRA_CIS"] = "0x07"
    fail_cpld_img["GINESTRA_CIS"] = "ginestra_d5_rev2_7_failsafe_12132023.bin"
    fail_cpld_ver["GINESTRA_CIS"] = "0x2"
    fail_cpld_dat["GINESTRA_CIS"] = "0x07"
    fea_cpld_img["GINESTRA_CIS"] = "ginestra_impl1.bin"
    diagfw_img["GINESTRA_CIS"] = "naples_diagfw_elba_1.68-G-19_2024.04.06.tar"
    diagfw_dat["GINESTRA_CIS"] = "04-07-2024"
    goldfw_img["GINESTRA_CIS"] = "naples_goldfw_elba_1.68-G-19_2024.04.06.tar"
    goldfw_dat["GINESTRA_CIS"] = "04-06-2024"
    mainfw_img["GINESTRA_CIS"] = "dsc_fw_elba_1.68-G-19_2024.04.06.tar"
    mainfw_dat["GINESTRA_CIS"] = ""

    cpld_img["58-0001-01"] = "ginestra_d5_rev2_7_working_12132023.bin"
    cpld_ver["58-0001-01"] = "0x2"
    cpld_dat["58-0001-01"] = "0x07"
    cpld_md5["58-0001-01"] = "ee3f1166b1b675ae5bb4189a584b1259"
    fail_cpld_img["58-0001-01"] = "ginestra_d5_rev2_7_failsafe_12132023.bin"
    fail_cpld_ver["58-0001-01"] = "0x2"
    fail_cpld_dat["58-0001-01"] = "0x07"
    fail_cpld_md5["58-0001-01"] = "b1a45f86b7889a8d1bf4513c67c17492"
    fea_cpld_img["58-0001-01"] = "ginestra_impl1.bin"
    diagfw_img["58-0001-01"] = "naples_diagfw_elba_1.68-G-17_2024.03.21.tar"
    diagfw_dat["58-0001-01"] = "03-21-2024"
    diagfw_md5["58-0001-01"] = "209134861198a13872b4e25129177746"

    cpld_img["58-0002-01"] = "ginestra_d5_rev2_7_working_12132023.bin"
    cpld_ver["58-0002-01"] = "0x2"
    cpld_dat["58-0002-01"] = "0x07"
    cpld_md5["58-0002-01"] = "ee3f1166b1b675ae5bb4189a584b1259"
    fail_cpld_img["58-0002-01"] = "ginestra_d5_rev2_7_failsafe_12132023.bin"
    fail_cpld_ver["58-0002-01"] = "0x2"
    fail_cpld_dat["58-0002-01"] = "0x07"
    fail_cpld_md5["58-0002-01"] = "b1a45f86b7889a8d1bf4513c67c17492"
    fea_cpld_img["58-0002-01"] = "ginestra_impl1.bin"
    diagfw_img["58-0002-01"] = "naples_diagfw_elba_1.68-G-17_2024.03.21.tar"
    diagfw_dat["58-0002-01"] = "03-21-2024"
    diagfw_md5["58-0002-01"] = "209134861198a13872b4e25129177746"

    cpld_img["DSC2A-2Q200-32S32F64P-S4A"] = "ginestra_d5_rev2_7_working_12132023.bin"
    cpld_ver["DSC2A-2Q200-32S32F64P-S4A"] = "0x2"
    cpld_dat["DSC2A-2Q200-32S32F64P-S4A"] = "0x07"
    cpld_md5["DSC2A-2Q200-32S32F64P-S4A"] = "ee3f1166b1b675ae5bb4189a584b1259"
    sec_cpld_img["DSC2A-2Q200-32S32F64P-S4A"] = "ginestra_d5_rev2_7_working_12132023.bin"
    sec_cpld_ver["DSC2A-2Q200-32S32F64P-S4A"] = "0x2"
    sec_cpld_dat["DSC2A-2Q200-32S32F64P-S4A"] = "0x07"
    sec_cpld_md5["DSC2A-2Q200-32S32F64P-S4A"] = "ee3f1166b1b675ae5bb4189a584b1259"
    fail_cpld_img["DSC2A-2Q200-32S32F64P-S4A"] = "ginestra_d5_rev2_7_failsafe_12132023.bin"
    fail_cpld_ver["DSC2A-2Q200-32S32F64P-S4A"] = "0x2"
    fail_cpld_dat["DSC2A-2Q200-32S32F64P-S4A"] = "0x07"
    fail_cpld_md5["DSC2A-2Q200-32S32F64P-S4A"] = "b1a45f86b7889a8d1bf4513c67c17492"
    goldfw_img["DSC2A-2Q200-32S32F64P-S4A"] = "naples_goldfw_elba_1.68-G-17_2024.03.21.tar"
    goldfw_dat["DSC2A-2Q200-32S32F64P-S4A"] = "03-21-2024"
    goldfw_md5["DSC2A-2Q200-32S32F64P-S4A"] = "312206364c4e8180df9405b40c4a44ba"

    cpld_img["DSC2A-2Q200-32S32F64P-S4B"] = "ginestra_d5_rev2_7_working_12132023.bin"
    cpld_ver["DSC2A-2Q200-32S32F64P-S4B"] = "0x2"
    cpld_dat["DSC2A-2Q200-32S32F64P-S4B"] = "0x07"
    cpld_md5["DSC2A-2Q200-32S32F64P-S4B"] = "ee3f1166b1b675ae5bb4189a584b1259"
    sec_cpld_img["DSC2A-2Q200-32S32F64P-S4B"] = "ginestra_d5_rev2_7_working_12132023.bin"
    sec_cpld_ver["DSC2A-2Q200-32S32F64P-S4B"] = "0x2"
    sec_cpld_dat["DSC2A-2Q200-32S32F64P-S4B"] = "0x07"
    sec_cpld_md5["DSC2A-2Q200-32S32F64P-S4B"] = "ee3f1166b1b675ae5bb4189a584b1259"
    fail_cpld_img["DSC2A-2Q200-32S32F64P-S4B"] = "ginestra_d5_rev2_7_failsafe_12132023.bin"
    fail_cpld_ver["DSC2A-2Q200-32S32F64P-S4B"] = "0x2"
    fail_cpld_dat["DSC2A-2Q200-32S32F64P-S4B"] = "0x07"
    fail_cpld_md5["DSC2A-2Q200-32S32F64P-S4B"] = "b1a45f86b7889a8d1bf4513c67c17492"
    goldfw_img["DSC2A-2Q200-32S32F64P-S4B"] = "naples_goldfw_elba_1.68-G-18_2024.04.03.tar"
    goldfw_dat["DSC2A-2Q200-32S32F64P-S4B"] = "04-03-2024"
    goldfw_md5["DSC2A-2Q200-32S32F64P-S4B"] = "0c24d9811ac703382cfe046a2106fde9"

    cpld_img["DSC2A-2Q200-32S32F64P-S4C"] = "ginestra_d5_rev2_7_working_12132023.bin"
    cpld_ver["DSC2A-2Q200-32S32F64P-S4C"] = "0x2"
    cpld_dat["DSC2A-2Q200-32S32F64P-S4C"] = "0x07"
    cpld_md5["DSC2A-2Q200-32S32F64P-S4C"] = "ee3f1166b1b675ae5bb4189a584b1259"
    sec_cpld_img["DSC2A-2Q200-32S32F64P-S4C"] = "ginestra_d5_rev2_7_working_12132023.bin"
    sec_cpld_ver["DSC2A-2Q200-32S32F64P-S4C"] = "0x2"
    sec_cpld_dat["DSC2A-2Q200-32S32F64P-S4C"] = "0x07"
    sec_cpld_md5["DSC2A-2Q200-32S32F64P-S4C"] = "ee3f1166b1b675ae5bb4189a584b1259"
    fail_cpld_img["DSC2A-2Q200-32S32F64P-S4C"] = "ginestra_d5_rev2_7_failsafe_12132023.bin"
    fail_cpld_ver["DSC2A-2Q200-32S32F64P-S4C"] = "0x2"
    fail_cpld_dat["DSC2A-2Q200-32S32F64P-S4C"] = "0x07"
    fail_cpld_md5["DSC2A-2Q200-32S32F64P-S4C"] = "b1a45f86b7889a8d1bf4513c67c17492"
    goldfw_img["DSC2A-2Q200-32S32F64P-S4C"] = "naples_goldfw_elba_1.68-G-19_2024.04.06.tar"
    goldfw_dat["DSC2A-2Q200-32S32F64P-S4C"] = "04-06-2024"
    goldfw_md5["DSC2A-2Q200-32S32F64P-S4C"] = "03eddbf464d4f65a5fb1dbfb8f66c910"

    cpld_img["DSC2A-2Q200-32S32F64P-S4"] = "ginestra_d5_rev2_7_working_12132023.bin"
    cpld_ver["DSC2A-2Q200-32S32F64P-S4"] = "0x2"
    cpld_dat["DSC2A-2Q200-32S32F64P-S4"] = "0x07"
    cpld_md5["DSC2A-2Q200-32S32F64P-S4"] = "ee3f1166b1b675ae5bb4189a584b1259"
    sec_cpld_img["DSC2A-2Q200-32S32F64P-S4"] = "ginestra_d5_rev2_7_working_12132023.bin"
    sec_cpld_ver["DSC2A-2Q200-32S32F64P-S4"] = "0x2"
    sec_cpld_dat["DSC2A-2Q200-32S32F64P-S4"] = "0x07"
    sec_cpld_md5["DSC2A-2Q200-32S32F64P-S4"] = "ee3f1166b1b675ae5bb4189a584b1259"
    fail_cpld_img["DSC2A-2Q200-32S32F64P-S4"] = "ginestra_d5_rev2_7_failsafe_12132023.bin"
    fail_cpld_ver["DSC2A-2Q200-32S32F64P-S4"] = "0x2"
    fail_cpld_dat["DSC2A-2Q200-32S32F64P-S4"] = "0x07"
    fail_cpld_md5["DSC2A-2Q200-32S32F64P-S4"] = "b1a45f86b7889a8d1bf4513c67c17492"
    goldfw_img["DSC2A-2Q200-32S32F64P-S4"] = "naples_goldfw_elba_1.68-G-19_2024.04.06.tar"
    goldfw_dat["DSC2A-2Q200-32S32F64P-S4"] = "04-06-2024"
    goldfw_md5["DSC2A-2Q200-32S32F64P-S4"] = "03eddbf464d4f65a5fb1dbfb8f66c910"

    # LENI mean default Leni 64G DDR
    cpld_img["LENI"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    cpld_ver["LENI"] = "0x03"
    cpld_dat["LENI"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    sec_cpld_img["LENI"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    sec_cpld_ver["LENI"] = "0x03"
    sec_cpld_dat["LENI"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fail_cpld_img["LENI"] = "salina_cfg1-rev3_10_0822-1120_fix_rot.bin"
    fail_cpld_ver["LENI"] = "0x03"
    fail_cpld_dat["LENI"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fea_cpld_img["LENI"] = "salina.fea"
    ufm1_img["LENI"] = "leni_ufm1-postdiv1_noStgOv-0214-2025.bin"
    goldfw_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_gold_1.108.0-C-40.tar.gz"
    goldfw_ver["LENI"] = "1.108.0-C-40"
    mainfw_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_athena_mfg_1.124.0-C-6.tar.gz"
    mainfw_ver["LENI"] = "1.124.0-C-6"
    arm_a_boot0_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/boot0.img"
    arm_a_uboota_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/uboota.img"
    arm_a_ubootb_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/ubootb.img"
    arm_a_ubootg_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_gold/salina/ubootg.img"
    arm_a_zephyr_a_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/zephyr.img"
    arm_a_zephyr_b_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/zephyr.img"
    arm_a_zephyr_gold_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_gold/salina/zephyr.img"
    arm_n_boot0_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/boot0.img"
    arm_n_uboota_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/uboota.img"
    arm_n_ubootb_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/ubootb.img"
    arm_n_ubootg_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_gold/salina/ubootg.img"
    arm_n_kernel_goldfw_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_gold/salina/kernel.img"
    device_config_dtb["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/device_config.dtb"
    qspi_prog_sh_img["LENI"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/qspi_prog.sh"
    qspi_snake_img["LENI"] = "salina/leni/leni_snake.tar.gz"
    mbist_boot0_img["LENI"] = "salina/leni/dpu_boot0.tar.gz"
    # LENI DPN
    cpld_img["58-0007-01"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    cpld_ver["58-0007-01"] = "0x03"
    cpld_dat["58-0007-01"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    sec_cpld_img["58-0007-01"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    sec_cpld_ver["58-0007-01"] = "0x03"
    sec_cpld_dat["58-0007-01"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fail_cpld_img["58-0007-01"] = "salina_cfg1-rev3_10_0822-1120_fix_rot.bin"
    fail_cpld_ver["58-0007-01"] = "0x03"
    fail_cpld_dat["58-0007-01"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fea_cpld_img["58-0007-01"] = "salina.fea"
    ufm1_img["58-0007-01"] = "leni_ufm1-postdiv1_noStgOv-0214-2025.bin"
    goldfw_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_gold_1.108.0-C-40.tar.gz"
    goldfw_ver["58-0007-01"] = "1.108.0-C-40"
    mainfw_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_athena_mfg_1.124.0-C-6.tar.gz"
    mainfw_ver["58-0007-01"] = "1.124.0-C-6"
    arm_a_boot0_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/boot0.img"
    arm_a_uboota_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/uboota.img"
    arm_a_ubootb_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/ubootb.img"
    arm_a_ubootg_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_gold/salina/ubootg.img"
    arm_a_zephyr_a_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/zephyr.img"
    arm_a_zephyr_b_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/zephyr.img"
    arm_a_zephyr_gold_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_gold/salina/zephyr.img"
    arm_n_boot0_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/boot0.img"
    arm_n_uboota_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/uboota.img"
    arm_n_ubootb_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/ubootb.img"
    arm_n_ubootg_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_gold/salina/ubootg.img"
    arm_n_kernel_goldfw_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_gold/salina/kernel.img"
    device_config_dtb["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/device_config.dtb"
    qspi_prog_sh_img["58-0007-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/qspi_prog.sh"
    qspi_snake_img["58-0007-01"] = "salina/leni/leni_snake.tar.gz"
    # Leni Standard SKU
    cpld_img["DSC3-2Q400-64S64E64P"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    cpld_ver["DSC3-2Q400-64S64E64P"] = "0x03"
    cpld_dat["DSC3-2Q400-64S64E64P"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    sec_cpld_img["DSC3-2Q400-64S64E64P"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    sec_cpld_ver["DSC3-2Q400-64S64E64P"] = "0x03"
    sec_cpld_dat["DSC3-2Q400-64S64E64P"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fail_cpld_img["DSC3-2Q400-64S64E64P"] = "salina_cfg1-rev3_10_0822-1120_fix_rot.bin"
    fail_cpld_ver["DSC3-2Q400-64S64E64P"] = "0x03"
    fail_cpld_dat["DSC3-2Q400-64S64E64P"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fea_cpld_img["DSC3-2Q400-64S64E64P"] = "salina.fea"
    ufm1_img["DSC3-2Q400-64S64E64P"] = "leni_ufm1-postdiv1_noStgOv-0214-2025.bin"
    goldfw_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/dpu_bundle_salina_gold_1.108.0-C-36.tar.gz"
    goldfw_ver["DSC3-2Q400-64S64E64P"] = "1.108.0-C-36"
    mainfw_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/dpu_bundle_salina_athena_mfg_1.124.0-C-6.tar.gz"
    mainfw_ver["DSC3-2Q400-64S64E64P"] = "1.124.0-C-6"
    arm_a_boot0_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/a35_main/salina/boot0.img"
    arm_a_uboota_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/a35_main/salina/uboota.img"
    arm_a_ubootb_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/a35_main/salina/ubootb.img"
    arm_a_ubootg_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/a35_gold/salina/ubootg.img"
    arm_a_zephyr_a_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/a35_main/salina/zephyr.img"
    arm_a_zephyr_b_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/a35_main/salina/zephyr.img"
    arm_a_zephyr_gold_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/a35_gold/salina/zephyr.img"
    arm_n_boot0_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/n1_main/salina/boot0.img"
    arm_n_uboota_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/n1_main/salina/uboota.img"
    arm_n_ubootb_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/n1_main/salina/ubootb.img"
    arm_n_ubootg_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/n1_gold/salina/ubootg.img"
    arm_n_kernel_goldfw_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/n1_gold/salina/kernel.img"
    device_config_dtb["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/n1_main/salina/device_config.dtb"
    qspi_prog_sh_img["DSC3-2Q400-64S64E64P"] = "salina/leni/leni_1.108.0-C-36/qspi_prog.sh"
    # Leni Oracle SKU
    cpld_img["DSC3-2Q400-64R64E64P-O"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    cpld_ver["DSC3-2Q400-64R64E64P-O"] = "0x03"
    cpld_dat["DSC3-2Q400-64R64E64P-O"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    sec_cpld_img["DSC3-2Q400-64R64E64P-O"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    sec_cpld_ver["DSC3-2Q400-64R64E64P-O"] = "0x03"
    sec_cpld_dat["DSC3-2Q400-64R64E64P-O"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fail_cpld_img["DSC3-2Q400-64R64E64P-O"] = "salina_cfg1-rev3_10_0822-1120_fix_rot.bin"
    fail_cpld_ver["DSC3-2Q400-64R64E64P-O"] = "0x03"
    fail_cpld_dat["DSC3-2Q400-64R64E64P-O"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fea_cpld_img["DSC3-2Q400-64R64E64P-O"] = "salina.fea"
    ufm1_img["DSC3-2Q400-64R64E64P-O"] = "leni_ufm1-postdiv1_noStgOv-0214-2025.bin"
    goldfw_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_gold_1.108.0-C-40.tar.gz"
    goldfw_ver["DSC3-2Q400-64R64E64P-O"] = "1.108.0-C-40"
    mainfw_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_athena_mfg_1.124.0-C-6.tar.gz"
    mainfw_ver["DSC3-2Q400-64R64E64P-O"] = "1.124.0-C-6"
    arm_a_boot0_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/boot0.img"
    arm_a_uboota_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/uboota.img"
    arm_a_ubootb_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/ubootb.img"
    arm_a_ubootg_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_gold/salina/ubootg.img"
    arm_a_zephyr_a_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/zephyr.img"
    arm_a_zephyr_b_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_main/salina/zephyr.img"
    arm_a_zephyr_gold_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/a35_gold/salina/zephyr.img"
    arm_n_boot0_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/boot0.img"
    arm_n_uboota_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/uboota.img"
    arm_n_ubootb_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/ubootb.img"
    arm_n_ubootg_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_gold/salina/ubootg.img"
    arm_n_kernel_goldfw_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_gold/salina/kernel.img"
    device_config_dtb["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/n1_main/salina/device_config.dtb"
    qspi_prog_sh_img["DSC3-2Q400-64R64E64P-O"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/qspi_prog.sh"

    # LENI48G different card type which is Leni with 48G DDR
    cpld_img["LENI48G"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    cpld_ver["LENI48G"] = "0x03"
    cpld_dat["LENI48G"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    sec_cpld_img["LENI48G"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    sec_cpld_ver["LENI48G"] = "0x03"
    sec_cpld_dat["LENI48G"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fail_cpld_img["LENI48G"] = "salina_cfg1-rev3_10_0822-1120_fix_rot.bin"
    fail_cpld_ver["LENI48G"] = "0x03"
    fail_cpld_dat["LENI48G"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fea_cpld_img["LENI48G"] = "salina.fea"
    ufm1_img["LENI48G"] = "leni_ufm1-postdiv1_noStgOv-0214-2025.bin"
    goldfw_img["LENI48G"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_gold_1.108.0-C-40.tar.gz"
    goldfw_ver["LENI48G"] = "1.108.0-C-40"
    mainfw_img["LENI48G"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_athena_mfg_1.124.0-C-6.tar.gz"
    mainfw_ver["LENI48G"] = "1.124.0-C-6"
    arm_a_boot0_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/a35_main/salina/boot0.img"
    arm_a_uboota_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/a35_main/salina/uboota.img"
    arm_a_ubootb_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/a35_main/salina/ubootb.img"
    arm_a_ubootg_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/a35_gold/salina/ubootg.img"
    arm_a_zephyr_a_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/a35_main/salina/zephyr.img"
    arm_a_zephyr_b_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/a35_main/salina/zephyr.img"
    arm_a_zephyr_gold_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/a35_gold/salina/zephyr.img"
    arm_n_boot0_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/n1_main/salina/boot0.img"
    arm_n_uboota_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/n1_main/salina/uboota.img"
    arm_n_ubootb_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/n1_main/salina/ubootb.img"
    arm_n_ubootg_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/n1_gold/salina/ubootg.img"
    arm_n_kernel_goldfw_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/n1_gold/salina/kernel.img"
    device_config_dtb["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/n1_main/salina/device_config.dtb"
    qspi_prog_sh_img["LENI48G"] = "salina/leni48/dpu_1.108.0-C-18/qspi_prog.sh"
    qspi_snake_img["LENI48G"] = "salina/leni48/leni_snake.tar.gz"
    mbist_boot0_img["LENI48G"] = "salina/leni48/dpu_boot0.tar.gz"
    # LENI48G DPN
    cpld_img["58-0003-01"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    cpld_ver["58-0003-01"] = "0x03"
    cpld_dat["58-0003-01"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    sec_cpld_img["58-0003-01"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    sec_cpld_ver["58-0003-01"] = "0x03"
    sec_cpld_dat["58-0003-01"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fail_cpld_img["58-0003-01"] = "salina_cfg1-rev3_10_0822-1120_fix_rot.bin"
    fail_cpld_ver["58-0003-01"] = "0x03"
    fail_cpld_dat["58-0003-01"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fea_cpld_img["58-0003-01"] = "salina.fea"
    ufm1_img["58-0003-01"] = "leni_ufm1-postdiv1_noStgOv-0214-2025.bin"
    goldfw_img["58-0003-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_gold_1.108.0-C-40.tar.gz"
    goldfw_ver["58-0003-01"] = "1.108.0-C-40"
    mainfw_img["58-0003-01"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_athena_mfg_1.124.0-C-6.tar.gz"
    mainfw_ver["58-0003-01"] = "1.124.0-C-6"
    arm_a_boot0_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/a35_main/salina/boot0.img"
    arm_a_uboota_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/a35_main/salina/uboota.img"
    arm_a_ubootb_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/a35_main/salina/ubootb.img"
    arm_a_ubootg_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/a35_gold/salina/ubootg.img"
    arm_a_zephyr_a_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/a35_main/salina/zephyr.img"
    arm_a_zephyr_b_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/a35_main/salina/zephyr.img"
    arm_a_zephyr_gold_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/a35_gold/salina/zephyr.img"
    arm_n_boot0_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/n1_main/salina/boot0.img"
    arm_n_uboota_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/n1_main/salina/uboota.img"
    arm_n_ubootb_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/n1_main/salina/ubootb.img"
    arm_n_ubootg_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/n1_gold/salina/ubootg.img"
    arm_n_kernel_goldfw_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/n1_gold/salina/kernel.img"
    device_config_dtb["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/n1_main/salina/device_config.dtb"
    qspi_prog_sh_img["58-0003-01"] = "salina/leni48/dpu_1.108.0-C-18/qspi_prog.sh"
    qspi_snake_img["58-0003-01"] = "salina/leni48/leni_snake.tar.gz"
    # Leni48G SKU
    cpld_img["DSC3-2Q400-48R64E64P"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    cpld_ver["DSC3-2Q400-48R64E64P"] = "0x03"
    cpld_dat["DSC3-2Q400-48R64E64P"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    sec_cpld_img["DSC3-2Q400-48R64E64P"] = "salina_cfg0-rev3_10_0822-1120_fix_rot.bin"
    sec_cpld_ver["DSC3-2Q400-48R64E64P"] = "0x03"
    sec_cpld_dat["DSC3-2Q400-48R64E64P"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fail_cpld_img["DSC3-2Q400-48R64E64P"] = "salina_cfg1-rev3_10_0822-1120_fix_rot.bin"
    fail_cpld_ver["DSC3-2Q400-48R64E64P"] = "0x03"
    fail_cpld_dat["DSC3-2Q400-48R64E64P"] = "08-22-25_11:20"  # mm-dd-YY_HH:MM
    fea_cpld_img["DSC3-2Q400-48R64E64P"] = "salina.fea"
    ufm1_img["DSC3-2Q400-48R64E64P"] = "leni_ufm1-postdiv1_noStgOv-0214-2025.bin"
    goldfw_img["DSC3-2Q400-48R64E64P"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_gold_1.108.0-C-40.tar.gz"
    goldfw_ver["DSC3-2Q400-48R64E64P"] = "1.108.0-C-40"
    mainfw_img["DSC3-2Q400-48R64E64P"] = "salina/leni/leni_1.108.0-C-40_1.124.0-C-6_OCI/dpu_bundle_salina_athena_mfg_1.124.0-C-6.tar.gz"
    mainfw_ver["DSC3-2Q400-48R64E64P"] = "1.124.0-C-6"
    arm_a_boot0_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/a35_main/salina/boot0.img"
    arm_a_uboota_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/a35_main/salina/uboota.img"
    arm_a_ubootb_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/a35_main/salina/ubootb.img"
    arm_a_ubootg_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/a35_gold/salina/ubootg.img"
    arm_a_zephyr_a_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/a35_main/salina/zephyr.img"
    arm_a_zephyr_b_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/a35_main/salina/zephyr.img"
    arm_a_zephyr_gold_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/a35_gold/salina/zephyr.img"
    arm_n_boot0_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/n1_main/salina/boot0.img"
    arm_n_uboota_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/n1_main/salina/uboota.img"
    arm_n_ubootb_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/n1_main/salina/ubootb.img"
    arm_n_ubootg_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/n1_gold/salina/ubootg.img"
    arm_n_kernel_goldfw_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/n1_gold/salina/kernel.img"
    device_config_dtb["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/n1_main/salina/device_config.dtb"
    qspi_prog_sh_img["DSC3-2Q400-48R64E64P"] = "salina/leni48/dpu_1.108.0-C-18_OCI/qspi_prog.sh"

    # MALFA is the Salina refernce board
    cpld_img["MALFA"] = "salina_cfg0-rev1_12_0117-1441_PLLRSTdelay5ms.bin"
    cpld_ver["MALFA"] = "0x1"
    cpld_dat["MALFA"] = "01-17-25_14:41" #mm-dd-YY_HH:MM
    sec_cpld_img["MALFA"] = "salina_cfg0-rev1_12_0117-1441_PLLRSTdelay5ms.bin"
    sec_cpld_ver["MALFA"] = "0x1"
    sec_cpld_dat["MALFA"] = "01-17-25_14:41" #mm-dd-YY_HH:MM
    fail_cpld_img["MALFA"] = "salina_cfg1-rev1_12_0117-1441_PLLRSTdelay5ms.bin"
    fail_cpld_ver["MALFA"] = "0x1"
    fail_cpld_dat["MALFA"] = "01-17-25_14:41" #mm-dd-YY_HH:MM
    fea_cpld_img["MALFA"] = "salina.fea"
    ufm1_img["MALFA"] = "leni_ufm1_pll_lock_max_011625_nxc1600.txt.bin"
    mainfw_img["MALFA"] = ""
    mainfw_dat["MALFA"] = ""
    arm_a_boot0_img["MALFA"] = "salina/malfa/a35_boot0.img"
    arm_a_uboota_img["MALFA"] = "salina/malfa/a35_uboota.img"
    arm_a_ubootb_img["MALFA"] = "salina/malfa/a35_ubootb.img"
    arm_a_ubootg_img["MALFA"] = "salina/malfa/a35_ubootg.img"
    arm_a_zephyr_a_img["MALFA"] = "salina/malfa/zephyr_dpu.fit"
    arm_a_zephyr_b_img["MALFA"] = "salina/malfa/zephyr.img"
    arm_a_zephyr_gold_img["MALFA"] = "salina/malfa/zephyr.img"
    arm_n_boot0_img["MALFA"] = "salina/malfa/n1_boot0.img"
    arm_n_uboota_img["MALFA"] = "salina/malfa/n1_uboot.img"
    arm_n_ubootb_img["MALFA"] = "salina/malfa/n1_uboot.img"
    arm_n_ubootg_img["MALFA"] = "salina/malfa/n1_uboot.img"
    arm_n_kernel_goldfw_img["MALFA"] = "salina/malfa/kernel.img"
    device_config_dtb["MALFA"] = "salina/malfa/device_config.dtb"
    qspi_prog_sh_img["MALFA"] = "salina/malfa/qspi_prog.sh"
    qspi_snake_img["MALFA"] = "salina/malfa/leni_snake.tar.gz"
    mbist_boot0_img["MALFA"] = "salina/malfa/dpu_boot0.tar.gz"

    # Pollara is AINIC, No N1 firmware image
    cpld_img["POLLARA"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    cpld_ver["POLLARA"] = "0x3"
    cpld_dat["POLLARA"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    sec_cpld_img["POLLARA"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    sec_cpld_ver["POLLARA"] = "0x3"
    sec_cpld_dat["POLLARA"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fail_cpld_img["POLLARA"] = "salina_cfg1-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    fail_cpld_ver["POLLARA"] = "0x3"
    fail_cpld_dat["POLLARA"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fea_cpld_img["POLLARA"] = "salina.fea"
    ufm1_img["POLLARA"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["POLLARA"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_boot0.img"
    arm_a_uboota_img["POLLARA"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_uboota.img"
    arm_a_ubootb_img["POLLARA"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootb.img"
    arm_a_ubootg_img["POLLARA"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootg.img"
    arm_a_zephyr_a_img["POLLARA"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_b_img["POLLARA"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_gold_img["POLLARA"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    qspi_prog_sh_img["POLLARA"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_prog.sh"
    qspi_snake_img["POLLARA"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218.tar.gz"
    qspi_verify_sh_img["POLLARA"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_verify.sh"
    mbist_boot0_img["POLLARA"] = "salina/pollara/ainic_boot0_ctle-iters-7-20250218.tar.gz"

    cpld_img["58-0004-01"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    cpld_ver["58-0004-01"] = "0x3"
    cpld_dat["58-0004-01"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    sec_cpld_img["58-0004-01"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    sec_cpld_ver["58-0004-01"] = "0x3"
    sec_cpld_dat["58-0004-01"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fail_cpld_img["58-0004-01"] = "salina_cfg1-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    fail_cpld_ver["58-0004-01"] = "0x3"
    fail_cpld_dat["58-0004-01"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fea_cpld_img["58-0004-01"] = "salina.fea"
    ufm1_img["58-0004-01"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["58-0004-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_boot0.img"
    arm_a_uboota_img["58-0004-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_uboota.img"
    arm_a_ubootb_img["58-0004-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootb.img"
    arm_a_ubootg_img["58-0004-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootg.img"
    arm_a_zephyr_a_img["58-0004-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_b_img["58-0004-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_gold_img["58-0004-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    qspi_prog_sh_img["58-0004-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_prog.sh"
    qspi_verify_sh_img["58-0004-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_verify.sh"
    qspi_snake_img["58-0004-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218.tar.gz"

    cpld_img["58-0004-02"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    cpld_ver["58-0004-02"] = "0x3"
    cpld_dat["58-0004-02"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    sec_cpld_img["58-0004-02"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    sec_cpld_ver["58-0004-02"] = "0x3"
    sec_cpld_dat["58-0004-02"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fail_cpld_img["58-0004-02"] = "salina_cfg1-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    fail_cpld_ver["58-0004-02"] = "0x3"
    fail_cpld_dat["58-0004-02"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fea_cpld_img["58-0004-02"] = "salina.fea"
    ufm1_img["58-0004-02"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["58-0004-02"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_boot0.img"
    arm_a_uboota_img["58-0004-02"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_uboota.img"
    arm_a_ubootb_img["58-0004-02"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootb.img"
    arm_a_ubootg_img["58-0004-02"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootg.img"
    arm_a_zephyr_a_img["58-0004-02"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_b_img["58-0004-02"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_gold_img["58-0004-02"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    qspi_prog_sh_img["58-0004-02"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_prog.sh"
    qspi_verify_sh_img["58-0004-02"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_verify.sh"
    qspi_snake_img["58-0004-02"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218.tar.gz"

    cpld_img["58-0004-03"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    cpld_ver["58-0004-03"] = "0x3"
    cpld_dat["58-0004-03"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    sec_cpld_img["58-0004-03"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    sec_cpld_ver["58-0004-03"] = "0x3"
    sec_cpld_dat["58-0004-03"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fail_cpld_img["58-0004-03"] = "salina_cfg1-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    fail_cpld_ver["58-0004-03"] = "0x3"
    fail_cpld_dat["58-0004-03"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fea_cpld_img["58-0004-03"] = "salina.fea"
    ufm1_img["58-0004-03"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["58-0004-03"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_boot0.img"
    arm_a_uboota_img["58-0004-03"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_uboota.img"
    arm_a_ubootb_img["58-0004-03"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootb.img"
    arm_a_ubootg_img["58-0004-03"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootg.img"
    arm_a_zephyr_a_img["58-0004-03"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_b_img["58-0004-03"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_gold_img["58-0004-03"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    qspi_prog_sh_img["58-0004-03"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_prog.sh"
    qspi_verify_sh_img["58-0004-03"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_verify.sh"
    qspi_snake_img["58-0004-03"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218.tar.gz"

    cpld_img["58-0010-01"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    cpld_ver["58-0010-01"] = "0x3"
    cpld_dat["58-0010-01"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    sec_cpld_img["58-0010-01"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    sec_cpld_ver["58-0010-01"] = "0x3"
    sec_cpld_dat["58-0010-01"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fail_cpld_img["58-0010-01"] = "salina_cfg1-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    fail_cpld_ver["58-0010-01"] = "0x3"
    fail_cpld_dat["58-0010-01"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fea_cpld_img["58-0010-01"] = "salina.fea"
    ufm1_img["58-0010-01"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["58-0010-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_boot0.img"
    arm_a_uboota_img["58-0010-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_uboota.img"
    arm_a_ubootb_img["58-0010-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootb.img"
    arm_a_ubootg_img["58-0010-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootg.img"
    arm_a_zephyr_a_img["58-0010-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_b_img["58-0010-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_gold_img["58-0010-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    qspi_prog_sh_img["58-0010-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_prog.sh"
    qspi_verify_sh_img["58-0010-10"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_verify.sh"
    qspi_snake_img["58-0010-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218.tar.gz"

    cpld_img["POLLARA-1Q400P"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    cpld_ver["POLLARA-1Q400P"] = "0x3"
    cpld_dat["POLLARA-1Q400P"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    sec_cpld_img["POLLARA-1Q400P"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    sec_cpld_ver["POLLARA-1Q400P"] = "0x3"
    sec_cpld_dat["POLLARA-1Q400P"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fail_cpld_img["POLLARA-1Q400P"] = "salina_cfg1-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    fail_cpld_ver["POLLARA-1Q400P"] = "0x3"
    fail_cpld_dat["POLLARA-1Q400P"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fea_cpld_img["POLLARA-1Q400P"] = "salina.fea"
    ufm1_img["POLLARA-1Q400P"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/boot0.img"
    arm_a_uboota_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/uboota.img"
    arm_a_ubootb_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/ubootb.img"
    arm_a_ubootg_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/goldfw/nonsecure/salina/ubootg.img"
    arm_a_zephyr_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_a_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_b_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_gold_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/goldfw/nonsecure/salina/zephyr.img"
    fwsel_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/fwsel_extosa.bin"
    device_config_dtb["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/device_config.dtb"
    firmware_config_dtb["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/firmware_config_POLLARA-1Q400P.dtb"
    qspi_prog_sh_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/qspi_prog.v2.sh"
    qspi_prog_secure_sh_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/qspi_prog_secure.v2.sh"
    qspi_verify_sh_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/qspi_verify.v2.sh"
    qspi_verify_secure_sh_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/qspi_verify_secure.v2.sh"
    bl1_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/secure/salina/bl1.img"
    pentrust_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/secure/salina/pentrustfw.img"
    fipa_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/secure/salina/fip.img"
    fipb_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/secure/salina/fip.img"
    fipg_img["POLLARA-1Q400P"] = "salina/pollara/ainic_1.117.1-a-31/goldfw/secure/salina/fip.img"

    cpld_img["POLLARA-1Q400P-O"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    cpld_ver["POLLARA-1Q400P-O"] = "0x3"
    cpld_dat["POLLARA-1Q400P-O"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    sec_cpld_img["POLLARA-1Q400P-O"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    sec_cpld_ver["POLLARA-1Q400P-O"] = "0x3"
    sec_cpld_dat["POLLARA-1Q400P-O"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fail_cpld_img["POLLARA-1Q400P-O"] = "salina_cfg1-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    fail_cpld_ver["POLLARA-1Q400P-O"] = "0x3"
    fail_cpld_dat["POLLARA-1Q400P-O"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fea_cpld_img["POLLARA-1Q400P-O"] = "salina.fea"
    ufm1_img["POLLARA-1Q400P-O"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/nonsecure/salina/boot0.img"
    arm_a_uboota_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/nonsecure/salina/uboota.img"
    arm_a_ubootb_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/nonsecure/salina/ubootb.img"
    arm_a_ubootg_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/goldfw/nonsecure/salina/ubootg.img"
    arm_a_zephyr_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_a_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_b_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_gold_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/goldfw/nonsecure/salina/zephyr.img"
    fwsel_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/fwsel_extosa.bin"
    device_config_dtb["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/nonsecure/salina/device_config.dtb"
    firmware_config_dtb["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/nonsecure/salina/firmware_config_POLLARA-1Q400P.dtb"
    qspi_prog_sh_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/qspi_prog.v2.sh"
    qspi_prog_secure_sh_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/qspi_prog_secure.v2.sh"
    qspi_verify_sh_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-31/qspi_verify.v2.sh"
    qspi_verify_secure_sh_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-31/qspi_verify_secure.v2.sh"
    bl1_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/secure/salina/bl1.img"
    pentrust_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/secure/salina/pentrustfw.img"
    fipa_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/secure/salina/fip.img"
    fipb_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/mainfw/secure/salina/fip.img"
    fipg_img["POLLARA-1Q400P-O"] = "salina/pollara/ainic_1.117.1-a-27/goldfw/secure/salina/fip.img"

    cpld_img["POLLARA-1Q400P-D"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    cpld_ver["POLLARA-1Q400P-D"] = "0x3"
    cpld_dat["POLLARA-1Q400P-D"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    sec_cpld_img["POLLARA-1Q400P-D"] = "salina_cfg0-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    sec_cpld_ver["POLLARA-1Q400P-D"] = "0x3"
    sec_cpld_dat["POLLARA-1Q400P-D"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fail_cpld_img["POLLARA-1Q400P-D"] = "salina_cfg1-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    fail_cpld_ver["POLLARA-1Q400P-D"] = "0x3"
    fail_cpld_dat["POLLARA-1Q400P-D"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fea_cpld_img["POLLARA-1Q400P-D"] = "salina.fea"
    ufm1_img["POLLARA-1Q400P-D"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/boot0.img"
    arm_a_uboota_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/uboota.img"
    arm_a_ubootb_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/ubootb.img"
    arm_a_ubootg_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/goldfw/nonsecure/salina/ubootg.img"
    arm_a_zephyr_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_a_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_b_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_gold_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/goldfw/nonsecure/salina/zephyr.img"
    fwsel_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/fwsel_extosa.bin"
    device_config_dtb["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/device_config.dtb"
    firmware_config_dtb["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/nonsecure/salina/firmware_config_POLLARA-1Q400P.dtb"
    qspi_prog_sh_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/qspi_prog.v2.sh"
    qspi_prog_secure_sh_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/qspi_prog_secure.v2.sh"
    qspi_verify_sh_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/qspi_verify.v2.sh"
    qspi_verify_secure_sh_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/qspi_verify_secure.v2.sh"
    bl1_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/secure/salina/bl1.img"
    pentrust_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/secure/salina/pentrustfw.img"
    fipa_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/secure/salina/fip.img"
    fipb_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/mainfw/secure/salina/fip.img"
    fipg_img["POLLARA-1Q400P-D"] = "salina/pollara/ainic_1.117.1-a-31/goldfw/secure/salina/fip.img"

    # Lingua is AINIC, No N1 firmware image
    cpld_img["LINGUA"] = "salina_cfg0-rev2_9_0828-1127_fix_hpe_reload.bin"
    cpld_ver["LINGUA"] = "0x2"
    cpld_dat["LINGUA"] = "08-28-25_11:27" #mm-dd-YY_HH:MM
    sec_cpld_img["LINGUA"] = "salina_cfg0-rev2_9_0828-1127_fix_hpe_reload.bin"
    sec_cpld_ver["LINGUA"] = "0x2"
    sec_cpld_dat["LINGUA"] = "08-28-25_11:27" #mm-dd-YY_HH:MM
    fail_cpld_img["LINGUA"] = "salina_cfg1-rev2_9_0828-1127_fix_hpe_reload.bin"
    fail_cpld_ver["LINGUA"] = "0x2"
    fail_cpld_dat["LINGUA"] = "08-28-25_11:27" #mm-dd-YY_HH:MM
    fea_cpld_img["LINGUA"] = "salina.fea"
    ufm1_img["LINGUA"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["LINGUA"] = "salina/lingua/ainic_lingua_bringup/boot0.img"
    arm_a_uboota_img["LINGUA"] = "salina/lingua/ainic_lingua_bringup/uboota.img"
    arm_a_ubootb_img["LINGUA"] = "salina/lingua/ainic_lingua_bringup/uboota.img"
    arm_a_ubootg_img["LINGUA"] = "salina/lingua/ainic_lingua_bringup/uboota.img"
    arm_a_zephyr_a_img["LINGUA"] = "salina/lingua/ainic_lingua_bringup/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_b_img["LINGUA"] = "salina/lingua/ainic_lingua_bringup/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_gold_img["LINGUA"] = "salina/lingua/ainic_lingua_bringup/firmware_config_hw_board_id_0x04670001.dtb"
    qspi_prog_sh_img["LINGUA"] = "salina/lingua/ainic_lingua_bringup/qspi_prog.sh"
    qspi_verify_sh_img["LINGUA"] = "salina/lingua/ainic_lingua_bringup/qspi_verify.sh"
    qspi_snake_img["LINGUA"] = "salina/lingua/ainic_lingua_bringup.tar.gz"
    mbist_boot0_img["LINGUA"] = "salina/lingua/ainic_boot0.tar.gz"

    cpld_img["58-0006-01"] = "salina_cfg0-rev2_9_0828-1127_fix_hpe_reload.bin"
    cpld_ver["58-0006-01"] = "0x2"
    cpld_dat["58-0006-01"] = "08-28-25_11:27" #mm-dd-YY_HH:MM
    sec_cpld_img["58-0006-01"] = "salina_cfg0-rev2_9_0828-1127_fix_hpe_reload.bin"
    sec_cpld_ver["58-0006-01"] = "0x2"
    sec_cpld_dat["58-0006-01"] = "08-28-25_11:27" #mm-dd-YY_HH:MM
    fail_cpld_img["58-0006-01"] = "salina_cfg1-rev2_9_0828-1127_fix_hpe_reload.bin"
    fail_cpld_ver["58-0006-01"] = "0x2"
    fail_cpld_dat["58-0006-01"] = "08-28-25_11:27" #mm-dd-YY_HH:MM
    fea_cpld_img["58-0006-01"] = "salina.fea"
    ufm1_img["58-0006-01"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["58-0006-01"] = "salina/lingua/ainic_lingua_bringup/boot0.img"
    arm_a_uboota_img["58-0006-01"] = "salina/lingua/ainic_lingua_bringup/uboota.img"
    arm_a_ubootb_img["58-0006-01"] = "salina/lingua/ainic_lingua_bringup/uboota.img"
    arm_a_ubootg_img["58-0006-01"] = "salina/lingua/ainic_lingua_bringup/uboota.img"
    arm_a_zephyr_a_img["58-0006-01"] = "salina/lingua/ainic_lingua_bringup/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_b_img["58-0006-01"] = "salina/lingua/ainic_lingua_bringup/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_gold_img["58-0006-01"] = "salina/lingua/ainic_lingua_bringup/firmware_config_hw_board_id_0x04670001.dtb"
    qspi_prog_sh_img["58-0006-01"] = "salina/lingua/ainic_lingua_bringup/qspi_prog.sh"
    qspi_verify_sh_img["58-0006-01"] = "salina/lingua/ainic_lingua_bringup/qspi_verify.sh"
    qspi_snake_img["58-0006-01"] = "salina/lingua/ainic_lingua_bringup.tar.gz"

    cpld_img["POLLARA-1Q400P-OCP"] = "salina_cfg0-rev2_9_0828-1127_fix_hpe_reload.bin"
    cpld_ver["POLLARA-1Q400P-OCP"] = "0x2"
    cpld_dat["POLLARA-1Q400P-OCP"] = "08-28-25_11:27" #mm-dd-YY_HH:MM
    sec_cpld_img["POLLARA-1Q400P-OCP"] = "salina_cfg0-rev2_9_0828-1127_fix_hpe_reload.bin"
    sec_cpld_ver["POLLARA-1Q400P-OCP"] = "0x2"
    sec_cpld_dat["POLLARA-1Q400P-OCP"] = "08-28-25_11:27" #mm-dd-YY_HH:MM
    fail_cpld_img["POLLARA-1Q400P-OCP"] = "salina_cfg1-rev2_9_0828-1127_fix_hpe_reload.bin"
    fail_cpld_ver["POLLARA-1Q400P-OCP"] = "0x2"
    fail_cpld_dat["POLLARA-1Q400P-OCP"] = "08-28-25_11:27" #mm-dd-YY_HH:MM
    fea_cpld_img["POLLARA-1Q400P-OCP"] = "salina.fea"
    ufm1_img["POLLARA-1Q400P-OCP"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/nonsecure/salina/boot0.img"
    arm_a_uboota_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/nonsecure/salina/uboota.img"
    arm_a_ubootb_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/nonsecure/salina/ubootb.img"
    arm_a_ubootg_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/goldfw/nonsecure/salina/ubootg.img"
    arm_a_zephyr_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_a_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_b_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/nonsecure/salina/zephyr.img"
    arm_a_zephyr_gold_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/goldfw/nonsecure/salina/zephyr.img"
    fwsel_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/fwsel_extosa.bin"
    device_config_dtb["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/nonsecure/salina/device_config.dtb"
    firmware_config_dtb["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/nonsecure/salina/firmware_config_POLLARA-1Q400P.dtb"
    qspi_prog_sh_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/qspi_prog.v2.sh"
    qspi_prog_secure_sh_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/qspi_prog_secure.v2.sh"
    qspi_verify_sh_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/qspi_verify.v2.sh"
    qspi_verify_secure_sh_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/qspi_verify_secure.v2.sh"
    bl1_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/secure/salina/bl1.img"
    pentrust_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/secure/salina/pentrustfw.img"
    fipa_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/secure/salina/fip.img"
    fipb_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/mainfw/secure/salina/fip.img"
    fipg_img["POLLARA-1Q400P-OCP"] = "salina/lingua/ainic_1.117.3-a-61/goldfw/secure/salina/fip.img"

    # GELSOP is AINIC
    cpld_img["GELSOP"] = "gelso_test_8415.jed"
    cpld_ver["GELSOP"] = "0x3"
    cpld_dat["GELSOP"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    sec_cpld_img["GELSOP"] = "gelso_test_8415.jed"
    sec_cpld_ver["GELSOP"] = "0x3"
    sec_cpld_dat["GELSOP"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fail_cpld_img["GELSOP"] = "salina_cfg1-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    fail_cpld_ver["GELSOP"] = "0x3"
    fail_cpld_dat["GELSOP"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fea_cpld_img["GELSOP"] = "salina.fea"
    ufm1_img["GELSOP"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["GELSOP"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_boot0.img"
    arm_a_uboota_img["GELSOP"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_uboota.img"
    arm_a_ubootb_img["GELSOP"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootb.img"
    arm_a_ubootg_img["GELSOP"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootg.img"
    arm_a_zephyr_a_img["GELSOP"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_b_img["GELSOP"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_gold_img["GELSOP"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    qspi_prog_sh_img["GELSOP"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_prog.sh"
    qspi_snake_img["GELSOP"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218.tar.gz"
    qspi_verify_sh_img["GELSOP"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_verify.sh"
    mbist_boot0_img["GELSOP"] = "salina/pollara/ainic_boot0_ctle-iters-7-20250218.tar.gz"
    microcontroller_img["GELSOP"] = "vulcano/gelsop/two_comp_gelso_v0_1_0_0.pldm"

    cpld_img["58-0013-01"] = "gelso_test_8415.jed"
    cpld_ver["58-0013-01"] = "0x3"
    cpld_dat["58-0013-01"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    sec_cpld_img["58-0013-01"] = "gelso_test_8415.jed"
    sec_cpld_ver["58-0013-01"] = "0x3"
    sec_cpld_dat["58-0013-01"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fail_cpld_img["58-0013-01"] = "salina_cfg1-rev3_8_0728-1922_fix_pseq_debounce_rei_en.bin"
    fail_cpld_ver["58-0013-01"] = "0x3"
    fail_cpld_dat["58-0013-01"] = "07-28-25_19:22" #mm-dd-YY_HH:MM
    fea_cpld_img["58-0013-01"] = "salina.fea"
    ufm1_img["58-0013-01"] = "pollara_ufm1-arm1500_nxc750_postdiv1_noStgOv-0214-2025.bin"
    arm_a_boot0_img["58-0013-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_boot0.img"
    arm_a_uboota_img["58-0013-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_uboota.img"
    arm_a_ubootb_img["58-0013-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootb.img"
    arm_a_ubootg_img["58-0013-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/a35_ainic_ubootg.img"
    arm_a_zephyr_a_img["58-0013-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_b_img["58-0013-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    arm_a_zephyr_gold_img["58-0013-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/zephyr.fit-ainic_pcieawd_standalone-ctle-iters-7-20250218"
    qspi_prog_sh_img["58-0013-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_prog.sh"
    qspi_verify_sh_img["58-0013-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218/qspi_verify.sh"
    qspi_snake_img["58-0013-01"] = "salina/pollara/pollara_standalone_ctle-iters-7-20250218.tar.gz"
    microcontroller_img["58-0013-01"] = "vulcano/gelsop/two_comp_gelso_v0_1_0_0.pldm"


class MTP_IMAGES:
    amd64_img = dict()
    arm64_img = dict()
    mtp_io_cpld_img = dict()
    mtp_io_cpld_ver = dict()
    mtp_jtag_cpld_img = dict()
    mtp_jtag_cpld_ver = dict()
    mtp_fpga_img = dict()
    mtp_fpga_ver = dict()
    mtp_fpga_date = dict()

    amd64_img["CAPRI"] = "image_amd64_capri.tar"
    arm64_img["CAPRI"] = "image_arm64_capri.tar"
    mtp_io_cpld_img["CAPRI"] = "NIC_MTP_IO_rev7_10232019.bin"
    mtp_io_cpld_ver["CAPRI"] = "0x7"
    mtp_jtag_cpld_img["CAPRI"] = "NIC_MTP_JTAG_rev3.bin"
    mtp_jtag_cpld_ver["CAPRI"] = "0x3"

    amd64_img["TURBO_CAPRI"] = "image_amd64_capri.tar"
    arm64_img["TURBO_CAPRI"] = "image_arm64_capri.tar"
    mtp_io_cpld_img["TURBO_CAPRI"] = ""
    mtp_io_cpld_ver["TURBO_CAPRI"] = "0x7"
    mtp_jtag_cpld_img["TURBO_CAPRI"] = ""
    mtp_jtag_cpld_ver["TURBO_CAPRI"] = "0x3"

    amd64_img["ELBA"] = "image_amd64_elba.tar"
    arm64_img["ELBA"] = "image_arm64_elba.tar"
    mtp_io_cpld_img["ELBA"] = "mtp_elba_io_rev1_07222020.bin"
    mtp_io_cpld_ver["ELBA"] = "0x1"
    mtp_jtag_cpld_img["ELBA"] = "mtp_elba_jtag_rev1_07302020.bin"
    mtp_jtag_cpld_ver["ELBA"] = "0x1"

    amd64_img["TURBO_ELBA"] = "image_amd64_elba.tar"
    arm64_img["TURBO_ELBA"] = "image_arm64_elba.tar"
    mtp_io_cpld_img["TURBO_ELBA"] = "nic_turbo_mtp_io_rev1_08042021.bin"
    mtp_io_cpld_ver["TURBO_ELBA"] = "0x1"
    mtp_jtag_cpld_img["TURBO_ELBA"] = "nic_turbo_mtp_jtag_09102021.bin"
    mtp_jtag_cpld_ver["TURBO_ELBA"] = "0x1"

    amd64_img["MATERA"] = "image_amd64_elba.tar"
    arm64_img["MATERA"] = "image_arm64_elba.tar"
    # mtp_fpga_img["MATERA"] = "to_be_define.bin"
    mtp_fpga_ver["MATERA"] = "a012"
    mtp_fpga_date["MATERA"] = "12222024"    #mmddYYYY
    mtp_fpga_ver["PANAREA"] = "a005"
    mtp_fpga_date["PANAREA"] = "09162025"    #mmddYYYY

    penctl_img = "penctl.linux.042021"
    penctl_token_img = "penctl.token"
    rotctrl_img = "rotctrl"
    nic_ctl_img = "nicctl"
    python_site_package4mtp_img = "python3.6_site_package.tar.gz"
    mtp_cpu_validation_tool_avt_img = "AVT_Linux_NDA_2.8.24.tar"

# MFG release images
class MFG_IMAGE_FILES:
    MTP_AMD64_IMAGE = "image_amd64_elba.tar"
    MTP_ARM64_IMAGE = "image_arm64_elba.tar"
    
    penctl_img = "penctl.linux.042021"
    penctl_token_img = "penctl.token"
    nic_ctl_img = "nicctl"

class FLEX_ERR_CODE_MAP:
    err_code = dict()
    err_code[-3] = "Unable to locate flex factory based on sn."
    err_code[-2] = "Fail to generate SOAP XML content."
    err_code[9999] = "Connection Failed in Flex side, please contact Flex IT ASAP."
    err_code[120110005] = "NextStateID must be numeric."
    err_code[120110010] = "The serial numbers should not be matched to multiple UnitID ."
    err_code[120110050] = "Cannot take NULL field value for nonexistent unit."
    err_code[120111010] = "Cannot convert UnitID into integer."
    err_code[180020100] = "Cannot find StatusID in luProductionOrderStatus table."
    err_code[180020600] = "Update to ffProductionOrder table has failed."
    err_code[180020700] = "Production order does not exists in ffProductionOrder table."
    err_code[180020800] = "Insertion to ffProductionOrderHistory table has failed."
    err_code[180020810] = "Failed to update ffLineOrder to set Priority to zero."
    err_code[180020830] = "Failed to update ffLineOrder to shift priority of line orders."
    err_code[180030001] = "Missing infromatin in the PackageSettingsXMLstring."
    err_code[180030050] = "Production order does not exist in ffProductionOrder table."
    err_code[180030060] = "@Name is not supplied."
    err_code[180030080] = "@Name is not defined in luProductionOrderDetailDef table."
    err_code[180030090] = "Value does not exist in ffPartDetail table."
    err_code[180040001] = "Error updating ffUnit.."
    err_code[180040200] = "UnitSerianumber not found in DB."
    err_code[180040300] = "The unit does not belong to any production order."
    err_code[180040400] = "Invalid Production Order."
    err_code[180040500] = "The production order has incompatible status."
    err_code[180040600] = "Invalid Line ID."
    err_code[180040700] = "Cannot add the quantity because it would exceed the allowed line quantity."
    err_code[180040800] = "Failed to upate ffLineOrder table with quantity."
    err_code[180040900] = "Some parameters are not filled out correctly"
    err_code[180050001] = "Cannot find ID for 'Active' in luProductionOrderStatus table."
    err_code[180050002] = "Cannot find ID for 'Released' in luProductionOrderStatus table."
    err_code[180050003] = "The line has not defined a highest priority production order."
    err_code[180050004] = "The line production order has not defined a part ID."
    err_code[230010010] = "Incoming UnitStateID is NULL."
    err_code[230010020] = "Incoming StationTypeID is NULL."
    err_code[230010030] = "Routing error (entered a wrong station)."
    err_code[230010040] = "Unable to find a RouteID."
    err_code[230010045] = "The unit is in scrap or hold status."
    err_code[230010050] = "The station does not allow NULL incoming state."
    err_code[250010010] = "Incoming UnitStateIO is NULL."
    err_code[250010020] = "Incoming StationTypeIO is NULL."
    err_code[250010030] = "Cannot find StateOescription in luOutputStateOef table."
    err_code[250010040] = "Unable to find a RouteIO."
    err_code[250010050] = "Cannot resolve multiple next unit state for current station ."
    err_code[250010070] = "Cannot find next outgoing unit state for current station ."
    err_code[270001000] = "Some group entry points to nonexistent parent in @GROUP."
    err_code[270001100] = "Parent cannot point to itself in @GROUP."
    err_code[270001200] = "Some group entry points to nonexistent @OUT."
    err_code[270001300] = "Some test entry points to nonexistent @OUT."
    err_code[270001400] = "Some test entry points to nonexistent @GROUP."
    err_code[270001410] = "Some TextExtra entry has no parent."
    err_code[270001420] = "Some GroupExtra entry has no parent."
    err_code[270001430] = "Some OUTExtra entry has no parent."
    err_code[270001500] = "There are some rows in #GROUP not having parent."
    err_code[270001600] = "Cannot find unit serial number in ffUnit table."
    err_code[270001700] = "Invalid station description in TESTER attribute of FACTORY element."
    err_code[270001710] = "Cannot find LineIO for the given station."
    err_code[270001890] = "Cannot insert to ffTestRef table."
    err_code[270001900] = "One of the OUT in panel has routing error."
    err_code[270001910] = "StartToPO is not defined for basic function frmTestSaveResult."
    err_code[270001920] = "ChangePartNumber is not defined for basic function frmTestSaveResult."
    err_code[270001930] = "Failed to find reverse part number when downgrade part number."
    err_code[270001940] = "CompleteToPO is not defined for basic function frmTestSaveResult."
    err_code[270001950] = "Cannot insert to luJig table."
    err_code[270002000] = "SQL Server failed to insert into ffTestPanel table."
    err_code[270002100] = "SQL Server failed to insert into ffTestPanelExtra table."
    err_code[270002300] = "SQL Server failed to insert into ffTest table."
    err_code[270002400] = "SQL Server failed to insert into ffTestExtra table."
    err_code[270002500] = "SQL Server failed to update @OUT table."
    err_code[270002590] = "SQL Server failed to insert into ffTESTSTEPPASS table."
    err_code[270002600] = "SQL Server failed to update @GROUP table."
    err_code[270002700] = "SQL Server failed to insert into ffTestStepPassExtra table."
    err_code[270002800] = "SQL Server failed to insert into ffMeasurementOetailPass table."
    err_code[270002900] = "SQL Server failed to update @TEST table."
    err_code[270003000] = "SQL Server failed to insert into ffMeasurementOetailPassExtra table."
    err_code[270003100] = "SQL Server failed to update @GROUP table."
    err_code[270003200] = "SQL Server failed to insert into ffTestStepFailExtra table."
    err_code[270003300] = "SQL Server failed to insert into ffMeasurementOetailFail table."
    err_code[270003400] = "SQL Server failed to update @TEST table."
    err_code[270003410] = "SQL Server failed to insert into ffMeasurementOetailFailExtra table."
    err_code[270003500] = "SQL Server failed to update ffUnitOetail table."
    err_code[270003505] = "Test value cannot be trivial when it is going to be saved into ffSerialNumber."
    err_code[270003510] = "SQL Server failed to insert ffSerialNumber table."
    err_code[270003515] = "SQL Server failed to update ffSerialNumber table."
    err_code[270003520] = "The OUT already has a different value in ffSerialNumber."
    err_code[270003521] = "SQL Server failed to insert ffSerialNumber table."
    err_code[270003600] = "SQL Server failed when call uspEXTTestSaveResult."
    err_code[280000026] = "Cannot resolve PartIO."
    err_code[280000027] = "The input @PartIO is not equal to PartIO from ffimportProduct."
    err_code[280000029] = "The input @PartID is not equal to PartID from ffUnit."
    err_code[280000030] = "Unit already exists. Cannot create it again.."
    err_code[280000031] = "The input @PartID is not equal to PartID from ffimportProduct."
    err_code[280000034] = "Cannot find PartID because @PartID is NULl, @ProductionOrderID is null and no info from ffimportProduct and ffUnit."
    err_code[280000035] = "Invalid RMANumber being received."
    err_code[280000036] = "The input @PartID is not equal to PartID from ffUnit."
    err_code[280000037] = "RMA already close. Please select a new RMA#."
    err_code[280000038] = "Cannot get PartID."
    err_code[280000045] = "RMA number does equal the one in ffimportProduct table. 03/16/2005 added @AllowLoopers=l."
    err_code[280000050] = "Cannot find incoming unit state id for the current station ."
    err_code[280000051] = "Unit serial number pattern check failed."
    err_code[280000060] = "SQL Server failed to insert unit into ffUnit table."
    err_code[280000070] = "SQL Server failed to insert unit into ffUnitDetail table."
    err_code[280000080] = "SQL Server failed to update ffUnit table for RMA project type."
    err_code[280000083] = "Failed to insert failure code into ffTest table."
    err_code[280000084] = "Failed to insert record into ffTest table."
    err_code[280000085] = "For a looper the unit StatusID must be 1 when it comes back."
    err_code[280000090] = "SQL Server failed to update ffUnitDetail for RMA project type."
    err_code[280000091] = "Failed updating ffimportProduct."
    err_code[280000092] = "Failed updating ffimportProduct."
    err_code[280000100] = "Failed to insert ffHistory table."
    err_code[280011000] = "Cannot find StatusID for Quarantine in luUnitStatus table."
    err_code[280012000] = "Cannot find StatusID for Processing in luUnitStatus table."
    err_code[280012100] = "Invalid unit status in @xmlAllowedStatus."
    err_code[280013000] = "Cannot find StatusID for Active in fsStatus table."
    err_code[280013100] = "Invalid part status in @xmlAllowedStatus."
    err_code[280014000] = "Cannot find StatusID for Active in luProductionOrderStatus table."
    err_code[280015000] = "Cannot find StatusID for Released in luProductionOrderStatus table."
    err_code[280015100] = "Invalid Production Order status in @xmlAllowedStatus."
    err_code[280016000] = "Invalid unit."
    err_code[280017000] = "Unit is not in an allowed status to run."
    err_code[280017100] = "Unit is not in given status."
    err_code[280018000] = "Unit does not have allowed part status."
    err_code[280019000] = "The production order is not in active or released status."
    err_code[280019100] = "The unit does have production order in allowed status."
    err_code[280030010] = "Cannot pass in NULL as field name."
    err_code[280030020] = "Cannot find column definition for field name."
    err_code[280030050] = "Cannot find Unit in ffUnit table."
    err_code[280030060] = "@ImpFieldName cannot be NULL."
    err_code[280030062] = "More than one row is found in ffimportProduct for this unit."
    err_code[280030066] = "No row is found in ffimportProduct for this unit."
    err_code[280030067] = "Failed to read ffimportProduct table."
    err_code[280030070] = "Data field is not defined as a column for ffUnitDetail."
    err_code[280031010] = "Invalid UnitID being passed in."
    err_code[280050010] = "Nonexistent UnitID passed into uspUNTGetSSN."
    err_code[280050030] = "Nonexistent Serial Numnber Name passed into uspUNTGetSSN."
    err_code[280050050] = "Unit does not exist in ffUnit table."
    err_code[280050060] = "@SNName is not supplied."
    err_code[280050070] = "@SNValue is not supplied ."
    err_code[280050080] = "Failed to insert luSerialNumber table."
    err_code[280050090] = "A serial number of given serial number type already exists for this unit."
    err_code[280050100] = "Failed when update serial number data for unit."
    err_code[280050110] = "Failed to insert ffSerialNumber table."
    err_code[280060020] = "Cannot find unit in ffUnit."
    err_code[280060030] = "Failed to generate serial number for ObtainValueBy=l."
    err_code[280060040] = "Failed to call stored procedure for ObtainValueBy=5."
    err_code[280060050] = "External stored procedure returned nonzero code."
    err_code[280060060] = "ObtainValueBy falls out of range (1,2,3,4,5,6)."
    err_code[280060070] = "Failed to update ffUnitDetail table."
    err_code[280060080] = "Cannot find ID in ffSNFormat table."
    err_code[280060170] = "Failed to insert ffUnitDetail table [uspUNTGenField]"
    err_code[280060180] = "The newly generated field value is not the same as saved one in ffSerialNumber when verification is performed [uspUNTGenField]"
    err_code[280060190] = "The newly generated field value is not the same as saved one in ffUnitDetail when verification is performed [uspUNTGenField]"
    err_code[280070100] = "Failed to update ffUnit table."
    err_code[280070101] = "Cannot find \"Completed \" status in luUnitStatus table."
    err_code[280070105] = "Cannot find \"Processing\" status in luUnitStatus table."
    err_code[280070200] = "Failed to insert ffHistory table."
    err_code[280100130] = "SQL Server failed to update reserved_xx columns in ffUnitDetail table."
    err_code[280100150] = "Some field name is not defined in fsFieldDefinition table."
    err_code[280100190] = "Failed to insert into ffUnitDetail table."
    err_code[280200050] = "When downgrade the partnumber for a unit, the target production order must be NULL."
    err_code[280200100] = "Cannot find \"Processing\" in luUnitStatus table."
    err_code[280200200] = "Cannot find production order Status!for \"released \"."
    err_code[280200300] = "Cannot find production order Status!for \"active\"."
    err_code[280200400] = "Invalid Station!."
    err_code[280200500] = "Invalid ProductionOrderID."
    err_code[280200600] = "Current production order must be in \"active\" or \"released \" status."
    err_code[280200700] = "The new production order must define \"IncomingPartNumber\" in its detail table for part upgrade operation ."
    err_code[280200710] = "Cannot find PartID for IncomingPartNumber defined in ffProductionOrderDetail."
    err_code[280200800] = "Unit does not exist in ffUnit table."
    err_code[280200900] = "Unit cannot be assigned twice to the same production order."
    err_code[280201000] = "Unit must have status 'Processing' or 'ReProcess' to be counted or moved to a production order."
    err_code[280201100] = "Unit must have a part number ."
    err_code[280201200] = "Unit production order must be in \"active\" or \"released \" status when @DecrementOldPO is on."
    err_code[280201300] = "The current production order containing unit must have an ImcomingPartNumber."
    err_code[280201310] = "Cannot find PartID for IncomingPartNumber defined in ffProductionOrderDetail."
    err_code[280201400] = "The new production order must have an incoming part number when its PartID is not the same as that of the unit."
    err_code[280201500] = "Unit 's part number must match IncomingPartNumber of the new production order."
    err_code[280201600] = "When downgrade unit's part number and assign it to a new PO, the new part number of the new PO must be consistent with that of current PO's incomingPartNumber."
    err_code[280201800] = "The unit part number must be consistent with that of the new production order."
    err_code[280202000] = "Failed to update ffUnit with new production order."
    err_code[280202010] = "Failed to update ffUnitDetail with new production order."
    err_code[280202100] = "Failed to update ffLineOrder table with new started quantity."
    err_code[280202110] = "Failed to update ffLineOrder table with new started quantity."
    err_code[280202200] = "The started quantity in ffLineOrder has reached limit, or the line order does not exist."
    err_code[280202300] = "Failed to update ffLineOrder table with new started quantity."
    err_code[280202310] = "Failed to update ffLineOrder table with new started quantity."
    err_code[280202400] = "The started quantity of line order is zero, or the unit does not belong to a line order."
    err_code[280221020] = "BTSAUTO must supply a serial number."
    err_code[280221030] = "Multiple imatching PartID found for BTSAuto."
    err_code[280221040] = "CANNOT find any matching PartID for BTSAuto."
    err_code[600140100] = "Cannot find StationID for given station."
    err_code[600140200] = "Cannot find @StationTypeID for given station."
    err_code[600140300] = "Cannot find LineID for given station."
    err_code[600140400] = "Cannot find default task group for nonexistent unit."
    err_code[600140500] = "Cannot find task group \"frmGetUnitinfo\"based on existing unit info."
    err_code[600140600] = "StartToPO is not defined for basic function frmGetUnitinfo."
    err_code[600140700] = "UnitPattern is not defined for basic function frmGetUnitinfo."
    err_code[600140800] = "ChangePartNumber is not defined for basic function frmGetUnitinfo."
    err_code[600140850] = "SectionHeader is not defined for basic function frmGetUnitinfo."
    err_code[600140870] = "Cannot find SectionHeader ID in ffSectionHeader table."
    err_code[600140900] = "Unit serial number does not match UnitPattern ."
    err_code[600141000] = "Cannot find StationID for given station."
    err_code[600141100] = "Cannot find @StationTypeID for given station."
    err_code[600141200] = "Cannot find LineID for given station."
    err_code[600141210] = "Invalid user ID."
    err_code[600141220] = "The user is not allowed to enter this station."
    err_code[600141300] = "Cannot find default task group for nonexistent unit."
    err_code[600141400] = "Cannot find RouteID for default task group."
    err_code[600141500] = "Cannot find task group \"frmGetUnitinfo\" based on existing unit info."
    err_code[600141600] = "Cannot find next unit state ID for task group frmGetUnitinfo."
    err_code[600141700] = "LineHasPO is not defined for basic function frmGetUnitinfo."
    err_code[600141800] = "PNSource is not defined for basic function frmGetUnitinfo."
    err_code[600141900] = "UnitPattern is not defined for basic function frmGetUnitinfo."
    err_code[600142000] = "PNValidate is not defined for basic function frmGetUnitinfo."
    err_code[600142100] = "SectionHeader is not defined for basic function frmGetUnitinfo."
    err_code[600142200] = "ChangePartNumber is not defined for basic function frmGetUnitinfo."
    err_code[600142250] = "AllowCreate is not defined for basic function frmGetUnitinfo."
    err_code[600142300] = "Cannot find SectionHeader ID in ffSectionHeader table."
    err_code[600142400] = "Unit serial number does not match UnitPattern ."
    err_code[600142500] = "Line must have a PO when part number is figured out from PO, or part number change is involved."
    err_code[600142600] = "Cannot find PartID for case @PNSource=l."
    err_code[600142700] = "Must indicate how to get part number when need create unit."
    err_code[600142800] = "Part number of unit being created does not equal to that of the line PO's."
    err_code[600142900] = "Unit part number is not the same as that the line PO's."
    err_code[600143000] = "Part number of unit being created does not equal to IncomingPartNumber of the line PO."
    err_code[600143100] = "Unit part number is not the same as the IncomingPartNumber of the line PO."
    err_code[600143200] = "Part number of unit being created does not fall into PartID or IncomingPartNumber of the line PO."
    err_code[600143300] = "Unit part number does not fall into PartID or IncomingPartNumber of the line PO."
    err_code[600143350] = "Cannot create unit because flag AllowCreate is off."
    err_code[600143400] = "Failed to find reverse part number when downgrade part number."
    err_code[600143500] = "Failed to update ffUnit when downgrade part number."

MFG_MTP_CPLD_IO_VERSION = "0x5"
MFG_MTP_CPLD_JTAG_VERSION = "0x3"
MFG_MTP_CPLD_IO_ELBA_VERSION = "0x1"
MFG_MTP_CPLD_JTAG_ELBA_VERSION = "0x1"
MFG_AI_NIC_SOFT_ROM_VERSION = "0.4.3"
MFG_DPU_NIC_SOFT_ROM_VERSION = "0.4.3"

DIAG_NIGHTLY_REPORT_ACCOUNT = "diag-nightly@pensando.io"
DIAG_NIGHTLY_REPORT_PASSWD = "diag-nightly"
DIAG_NIGHTLY_REPORT_RECEIPIENT = "ps-diag@pensando.io"
DIAG_OS_PROMPT_LIST = ["$", "#", ">"]
#DIAG_SSH_OPTIONS = " -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"
DIAG_SSH_OPTIONS = " -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"

MFG_VALID_FW_LIST = ["diagfw", "mainfwa", "mainfwb", "goldfw", "extdiag"]
MFG_VALID_NIC_TYPE_LIST = [
    NIC_Type.NAPLES100, NIC_Type.NAPLES25, NIC_Type.VOMERO2, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25OCP, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL, NIC_Type.NAPLES25SWMDELL,
    NIC_Type.NAPLES25SWM833, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP,
    NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4, NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5, NIC_Type.GINESTRA_S4, NIC_Type.GINESTRA_CIS,
    NIC_Type.LENI, NIC_Type.LENI48G, NIC_Type.MALFA, NIC_Type.POLLARA, NIC_Type.LINGUA, NIC_Type.GELSOP
]
MFG_PROTO_NIC_TYPE_LIST = [NIC_Type.FORIO, NIC_Type.VOMERO, NIC_Type.ORTANO]

MTP_REV02_CAPABLE_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL, NIC_Type.VOMERO2]
MTP_REV03_CAPABLE_NIC_TYPE_LIST = [
    NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32,
    NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4,
    NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4, NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5, NIC_Type.GINESTRA_S4, NIC_Type.GINESTRA_CIS
]
MTP_REV04_CAPABLE_NIC_TYPE_LIST = [
    NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32,
    NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4,
    NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4, NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5, NIC_Type.GINESTRA_S4, NIC_Type.GINESTRA_CIS
]

MTP_MATERA_CAPABLE_NIC_TYPE_LIST = [
    NIC_Type.LENI, NIC_Type.LENI48G, NIC_Type.MALFA, NIC_Type.POLLARA, NIC_Type.LINGUA
]

MTP_PANAREA_CAPABLE_NIC_TYPE_LIST = [
    NIC_Type.GELSOP
]

CAPRI_NIC_TYPE_LIST = [
    NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL, NIC_Type.VOMERO2,
    NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP
]
ELBA_NIC_TYPE_LIST = [
    NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS,
    NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4
]
GIGLIO_NIC_TYPE_LIST = [
    NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5, NIC_Type.GINESTRA_S4, NIC_Type.GINESTRA_CIS
]

SALINA_DPU_NIC_TYPE_LIST = [
    NIC_Type.LENI, NIC_Type.LENI48G, NIC_Type.MALFA
]
SALINA_AI_NIC_TYPE_LIST = [
    NIC_Type.POLLARA, NIC_Type.LINGUA
]

VULCANO_NIC_TYPE_LIST = [
    NIC_Type.GELSOP
]

SALINA_NIC_TYPE_LIST = SALINA_DPU_NIC_TYPE_LIST + SALINA_AI_NIC_TYPE_LIST

PSLC_MODE_TYPE_LIST = [
    NIC_Type.VOMERO2, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP,
    NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4, NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5, NIC_Type.GINESTRA_S4, NIC_Type.GINESTRA_CIS,
    NIC_Type.LENI, NIC_Type.LENI48G, NIC_Type.MALFA
]
FPGA_TYPE_LIST = [NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32]
FAILSAFE_CPLD_TYPE_LIST = [
    NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP,
    NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4,
    NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4,
    NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5, NIC_Type.GINESTRA_S4, NIC_Type.GINESTRA_CIS, NIC_Type.LENI, NIC_Type.LENI48G, NIC_Type.MALFA, NIC_Type.POLLARA, NIC_Type.LINGUA
]
ADI_VRM_TYPE_LIST = [
    NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4
]
TWO_OOB_MGMT_PORT_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL]
NO_OOB_MGMT_PORT_TYPE_LIST = [
    NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2SOLOS4,
    NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4,
    NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5, NIC_Type.GINESTRA_S4, NIC_Type.GINESTRA_CIS
]
ETH_25G_TYPE_LIST = [
    NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25OCP,
    NIC_Type.LACONA32, NIC_Type.LACONA32DELL
]
CONSOLE_DDR_BIST_NIC_LIST = [
    NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2SOLOMSFT,
    NIC_Type.ORTANO2SOLOS4, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4
]  # temporary list to hold nic types while gradually offloading ddr_bist from L1 test
DDR_HARCODED_TRAINING_NIC_LIST = []
NEED_UBOOT_IMG_CARD_TYPE_LIST = [NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI,
                                 NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4, NIC_Type.ORTANO2SOLOS4]
MAINFW_TYPE_LIST = [
    NIC_Type.NAPLES100, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25OCP,
    NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2SOLOORCTHS, NIC_Type.ORTANO2ADICR,
    NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2ADICRMSFT,
    NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5
]

# ARM_L1 test set mode hod_1100
ARM_L1_MODE_HOD_1100 = [NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4,
                        NIC_Type.ORTANO2SOLOS4, NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5, NIC_Type.GINESTRA_S4, NIC_Type.GINESTRA_CIS]
CTO_MODEL_TYPE_LIST = [NIC_Type.GINESTRA_S4] + SALINA_NIC_TYPE_LIST + VULCANO_NIC_TYPE_LIST
SWI_UPDATE_FRU_TYPE_LIST = [NIC_Type.GINESTRA_CIS]
# Card Type List Which need attash ROT cable when run FST test
ROT_CABLE_REQUIRED_FOR_FST_TYPE_LIST = [
    NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2INTERP, NIC_Type.ORTANO2SOLO, NIC_Type.ORTANO2SOLOL, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2SOLOORCTHS,
    NIC_Type.ORTANO2SOLOMSFT, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.GINESTRA_D4, NIC_Type.GINESTRA_D5, NIC_Type.LENI, NIC_Type.LENI48G, NIC_Type.POLLARA
]

# Part Number Pattern List Which need attash ROT cable when run FST test
ROT_CABLE_REQUIRED_FOR_FST_PN_LIST = [
    PART_NUMBERS_MATCH.ORTANO2_ORC_PN_FMT,                  #68-0015-02 XX    ORTANO2 ORACLE
    PART_NUMBERS_MATCH.ORTANO2ADI_ORC_PN_FMT,               #68-0026-01 XX    ORTANO2ADI ORACLE
    PART_NUMBERS_MATCH.ORTANO2INTERP_ORC_PN_FMT,            #68-0029-01 XX    ORTANO2 Interposer
    PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_PN_FMT,              #68-0077-01 XX    ORTANO2 SOLO ORACLE
    PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_L_PN_FMT,            #68-0095-01 XX    ORTANO2 SOLO-L ORACLE
    PART_NUMBERS_MATCH.ORTANO2SOLO_ORC_THS_PN_FMT,          #68-0089-01 XX    ORTANO2 SOLO ORACLE Tall Heat Sink
    PART_NUMBERS_MATCH.ORTANO2ADI_CR_PN_FMT,                #68-0049-03 XX    ORTANO2ADI CR
    PART_NUMBERS_MATCH.ORTANO2SOLO_MSFT_PN_FMT,             #68-0090-01 A0    ORTANO2SOLO MICROSOFT
    PART_NUMBERS_MATCH.ORTANO2ADI_CR_MSFT_PN_FMT,           #68-0091-01 A0    ORTANO2ADI CR MICROSOFT
    PART_NUMBERS_MATCH.GINESTRA_D4_PN_FMT,                  #68-0074-01 01    GINESTRA_D4
    PART_NUMBERS_MATCH.GINESTRA_D5_PN_FMT,                  #68-0075-01 01    GINESTRA_D5
    ]

# Board Part Numebr and CPLD ID To Board Id and PCI subsys ID Mapping Table
#  ("Part Numebr", "CPLD ID") : ("Board Id", "PCI subsys ID")
PN_CPLD2BOARDID_PCI_SUBSYS_ID = {
    ("P26968", "0x17")        : ("0x01170001", "0x4008"),
    ("68-0014", "0x20")       : ("0x01200002", "0x400C"),
    ("P37689", "0x19")        : ("0x01170001", "0x4007"),
    ("68-0010", "0x19")       : ("0x01190003", "0x400F"),
    ("68-0003", "0x12")       : ("0x01120002", "0x4001"),
    ("68-0013", "0x1C")       : ("0x011C0001", "0x400A"),
    ("P47930", "0x4A")        : ("0x024A0001", "0x5008"),
    ("P47927", "0x46")        : ("0x02460001", "0x5005"),
    ("68-0020", "0x45")       : ("0x02450001", "0x5004"),
    ("0X322F", "0x49")        : ("0x02490001", "0x5009"),
    ("0W5WGK", "0x49")        : ("0x02490002", "0x5009"),
    ("P47933", "0x48")        : ("0x02480001", "0x5006"),
    ("0PCFPC", "0x47")        : ("0x02470001", "0x5007"),
    ("68-0026", "0x4B")       : ("0x024B0001", "0x500a"),
    ("68-0015", "0x44")       : ("0x02440003", "0x5001"),
    ("68-0028", "0x4B")       : ("0x024B0003", "0x500b"),
    ("68-0021", "0x44")       : ("0x02440001", "0x5003"),
    ("68-0029", "0x4C")       : ("0x024C0001", "0x500c"),
    ("68-0077", "0x4E")       : ("0x024E0001", "0x500d"),
    ("68-0095", "0x4E")       : ("0x024E0001", "0x500d"),
    ("68-0089", "x")          : ("0x024E0003", "0x500f"),
    ("68-0049", "0x50")       : ("0x02500001", "0x500e"),
    ("68-0034", "0x4B")       : ("0x024B0002", "0x5003"),
    ("68-0090", "0x4E")       : ("0x024E0002", "0x5003"),
    ("68-0091", "0x50")       : ("0x02500002", "0x5003"),
    ("68-0074", "0x60")       : ("0x03600001", "0x5100"),
    ("68-0075", "0x61")       : ("0x03610001", "0x5101"),
    ("68-0076", "0x61")       : ("0x03610001", "0x5003"),
    ("68-0086", "0x60")       : ("0x03600001", "0x5100"),
    ("68-0087", "0x61")       : ("0x03610001", "0x5101"),
    ("68-0092", "0x4E")       : ("0x024E0002", ""),
    ("68-0092", "0x50")       : ("0x02500002", "0x5003"),
    ("68-0094", "0x61")       : ("0x03610001", "0x5003"),
    ("102-P10800", "0x64")    : ("0x04640001", "0x5200"),
    ("102-P10801", "0x66")    : ("0x04640002", "0x5200"),
    ("102-P11100", "0x65")    : ("0x04650001", "0x5201"),
    ("102-P11500", "0x67")    : ("0x04670001", "0x5201"),
}

# SKU To Board Id and PCI subsys ID Mapping Table, This is for SWI only
# "SKU String" : ("Board Id", "PCI subsys ID")
SKU2BOARDID_PCI_SUBSYS_ID = {
    "DSC2-2S25-32R32H64P-HA":           ("0x024A0001", "0x5008"),
    "DSC2-2S25-16R16H64P-HA":           ("0x02460001", "0x5005"),
    "DSC2-2S25-16R16H64P-DBA":          ("0x02450001", "0x5004"),
    "DSC2-2S25-16R16H64P-DA":           ("0x02450002", "0x5004"),
    "DSC2-2S25-32R32H64P-DA":           ("0x02490001", "0x5009"),
    "DSC2-2S25-32R32H64P-DBA":          ("0x02490002", "0x5009"),
    "DSC2-2Q100-32R32F64P-HA":          ("0x02480001", "0x5006"),
    "DSC2-2Q100-32R32F64P-DA":          ("0x02470001", "0x5007"),
    "DSC2-2Q200-32R32F64P-R2":          ("0x024B0001", "0x500a"),
    "DSC2-2Q200-32R32F64P-R":           ("0x02440003", "0x5001"),
    "DSC2-2Q200-32R32F64P-B":           ("0x024B0003", "0x500b"),
    "DSC2-2Q200-32R32F64P":             ("0x02440001", "0x5003"),
    "DSC2-2Q200-32R32F64P-R3":          ("0x024C0001", "0x500c"),
    "DSC2-2Q200-32R32F64P-R4":          ("0x024E0001", "0x500d"),
    "DSC2-2Q200-32R32F64P-R4-L":        ("0x024E0001", "0x500d"),
    "DSC2-2Q200-32R32F64P-R4-T":        ("0x024E0003", "0x500f"),
    "DSC2-2Q200-32R32F64P-R5":          ("0x02500001", "0x500e"),
    "DSC2-2Q200-32R32F64P-M2":          ("0x024B0002", "0x5003"),
    "DSC2-2Q200-32R32F64P-M4":          ("0x024E0002", "0x5003"),
    "DSC2-2Q200-32R32F64P-M5":          ("0x02500002", "0x5003"),
    "DSC2A-2Q200-32R32F64P-R":          ("0x03600001", "0x5100"),
    "DSC2A-2Q200-32S32F64P-R":          ("0x03610001", "0x5101"),
    "DSC2A-2Q200-32R32F64P-M":          ("0x03600001", "0x5100"),
    "DSC2A-2Q200-32S32F64P-M":          ("0x03610001", "0x5101"),
    "DSC2-2Q200-32R32F64P-S4":          ("0x02500002", "0x5003"),
    "DSC2A-2Q200-32S32F64P-S4":         ("0x03600001", "0x5100"),
    "DSC2A-2Q200-32S32F64P-S4-B3":      ("0x03610001", "0x5003"),
    "DSC2A-2Q200-32S32F64P-S4-C":       ("0x03610001", "0x5003"),
    "DSC2A-2Q200-32S32F64P-S4-C-B3":    ("0x03610001", "0x5003"),
    "DSC3-2Q400-128S64E256P":           ("0x04620001", "0x5200"),
    "DSC3-2Q400-64S64E64P":             ("0x04640001", "0x5200"),
    "DSC3-2Q400-48R64E64P":             ("0x04640002", "0x5200"),
    "DSC3-2Q400-64R64E64P-O":           ("0x04640001", "0x5200"),
    "POLLARA-1Q400P":                   ("0x04650001", "0x5201"),
    "POLLARA-1Q400P-O":                 ("0x04650001", "0x5201"),
    "POLLARA-1Q400P-D":                 ("0x04650001", "0x5201"),
    "POLLARA-1Q400P-OCP":               ("0x04670001", "0x5201"),
    "VULCANO-1Q800P":                   ("0x04650001", "0x5201"),
    "VULCANO-1Q800P-O":                 ("0x04650001", "0x5201"),
    "VULCANO-1Q800P-OCP":               ("0x04650001", "0x5201"),
}

#get softRom file name
GETSOFTROM_FILE_NAME= {
    "0.4.3":    {
        "qspi_softrom":"prog_qspi_softrom_43.sh",
        "qspi_pentrust":"prog_qspi_pentrust_43.sh",
        "hmac_file":"hmac_value_4.3.hex"
    },
}

NIC_MGMT_USERNAME = "root"
NIC_MGMT_PASSWORD = "pen123"

MTP_INTERNAL_MGMT_IP_ADDR = "10.1.1.100"
MTP_INTERNAL_MGMT_NETMASK = "255.255.255.0"


Factory_network_config = {
    Factory.FSP: {
        "Networks": ["192.168.1.0/24", "192.168.2.0/24", "192.168.3.0/24", "192.168.4.0/24"],
        "Flexflow": "10.206.9.68"
    },
    Factory.MILPITAS: {
        "Networks": ["192.168.5.0/24"],
        "Flexflow": "10.20.33.140"
    },
    Factory.P1: {
        "Networks": ["192.168.8.0/22"],
        "Flexflow": "pnapsotesterws.flex.com"
    },
    Factory.LAB: {
        "Networks": ["10.9.0.0/16"],
        "Flexflow": ""
    }
}

# Don't touch the following xml format, it is required for flex flow report

# Milpitas flex server
FLX_WEBSERVER = "10.20.33.140"
FLX_API_URL = "/Pensando/fftester20.asmx"
FLX_GET_UUT_INFO_SOAP = "http:/www.flextronics.com/FFTester20/GetUnitInfo"
FLX_SAVE_UUT_RSLT_SOAP = "http:/www.flextronics.com/FFTester20/SaveResult"

# Penang flex server
#FLX_PENANG_WEBSERVER = "10.192.155.61"
#FLX_PENANG_WEBSERVER = "172.30.178.5"
#FLX_PENANG_WEBSERVER = "10.206.9.16"
FLX_PENANG_API_URL = "/FFTesterWS_PENSANDO/FFTesterWS.asmx"
FLX_PENANG_GET_UUT_INFO_SOAP = "http://www.flextronics.com/FFTesterWS/GetUnitInfo"
FLX_PENANG_SAVE_UUT_RSLT_SOAP = "http://www.flextronics.com/FFTesterWS/SaveResult"

FLX_GET_UUT_INFO_CODE_RE = r"<GetUnitInfoResult>(\d+)</GetUnitInfoResult>"
FLX_SAVE_UUT_RSLT_CODE_RE = r"<SaveResultResult>(\d+)</SaveResultResult>"

FLX_GET_UUT_INFO_XML_HEAD =                                                                \
'<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                      \
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"                               \
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                    \
     <soap:Body>                                                                           \
         <GetUnitInfo xmlns="http:/www.flextronics.com/FFTester20">'

FLX_GET_UUT_INFO_ENTRY_FMT =                                                               \
            '<strRequest>&lt;?xml version="1.0" ?&gt;                                      \
                &lt;GetUnitInfo xmlns="urn:GetUnitInfo-schema" SerialNumber="{:s}" /&gt;   \
             </strRequest>                                                                 \
             <strStationName>{:s}</strStationName>                                         \
             <strUserID>Admin</strUserID>'

FLX_GET_UUT_INFO_XML_TAIL =                                                                \
       '</GetUnitInfo>                                                                     \
    </soap:Body>                                                                           \
</soap:Envelope>'

FLX_PENANG_GET_UUT_INFO_XML_HEAD =                                                         \
'<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                      \
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"                               \
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                    \
    <soap:Body>                                                                            \
        <GetUnitInfo xmlns="http://www.flextronics.com/FFTesterWS/">'

FLX_PENANG_GET_UUT_INFO_ENTRY_FMT =                                                        \
           '<strRequest>&lt;?xml version="1.0" ?&gt;                                       \
               &lt;GetUnitInfo xmlns="urn:GetUnitInfo-schema" SerialNumber="{:s}" /&gt;    \
            </strRequest>                                                                  \
            <strStationName>{:s}</strStationName>                                          \
            <strUserID>Tester01</strUserID>'

FLX_SAVE_UUT_RSLT_XML_HEAD =                                                               \
'<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                      \
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"                               \
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                    \
   <soap:Body>                                                                             \
      <SaveResult xmlns="http:/www.flextronics.com/FFTester20">                            \
         <strXMLResultText>'

FLX_SAVE_UUT_RSLT_ENTRY_FMT =                                                              \
         '&lt;BATCH&gt;&#xD;                                                               \
          &lt;FACTORY TESTER="{:s}" USER="admin" /&gt;&#xD;                                \
          &lt;PANEL&gt;&#xD;                                                               \
          &lt;DUT ID="{:s}" SOCKET="1" TIMESTAMP="{:s}" TESTTIME="{:s}" ENDTIME="{:s}" STATUS="{:s}"&gt;&#xD;'
FLX_SAVE_UUT_RSLT_ENTRY_EXTRA_FMT =                                                        \
         '&lt;EXTRA {:s} /&gt;&#xD;'
FLX_SAVE_UUT_RSLT_ENTRY_2_FMT =                                                            \
         '&lt;GROUP NAME="{:s}" GROUPINDEX="1" LOOPINDEX="-1" TYPE="PassFailTest" Remark="Comment" TOTALTIME="{:s}" STATUS="{:s}"&gt;&#xD;'

FLX_SAVE_UUT_TEST_RSLT_FMT =                                                               \
         '&lt;TEST NAME="{:s}" STATUS="{:s}" VALUE="{:s}" DESCRIPTION="{:s}" FAILURECODE="{:s}" /&gt;&#xD;'

#TEST NAME="MAC-ADD" STATUS="PASS" VALUE="XXXXXXXXXXXX" DESCRIPTION="FRU MAC-ADD" FAILURECODE="PASS"
#TEST NAME="PART-NO" STATUS="PASS" VALUE="XXXXXXX" DESCRIPTION="FRU PART-NO" FAILURECODE="PASS"

FLX_SAVE_UUT_MAC_RSLT_FMT =                                                               \
         '&lt;TEST NAME="MAC-ADD" STATUS="PASS" VALUE="{:s}" DESCRIPTION="FRU MAC-ADD" FAILURECODE="PASS" /&gt;&#xD;'
FLX_SAVE_UUT_PN_RSLT_FMT =                                                               \
         '&lt;TEST NAME="PART-NO" STATUS="PASS" VALUE="{:s}" DESCRIPTION="FRU PART-NO" FAILURECODE="PASS" /&gt;&#xD;'         

FLX_SAVE_UUT_RSLT_ENTRY_END =                                                              \
         '&lt;/GROUP&gt;&#xD;                                                              \
          &lt;/DUT&gt;&#xD;                                                                \
          &lt;/PANEL&gt;&#xD;'                                                             \
         '&lt;/BATCH&gt;'

FLX_SAVE_UUT_RSLT_XML_TAIL =                                                               \
        '</strXMLResultText>                                                               \
         <strTestRefNo>Test123</strTestRefNo>                                              \
     </SaveResult>                                                                         \
   </soap:Body>                                                                            \
</soap:Envelope>'

FLX_PENANG_SAVE_UUT_RSLT_XML_HEAD =                                                        \
'<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                      \
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"                               \
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                    \
   <soap:Body>                                                                             \
      <SaveResult xmlns="http://www.flextronics.com/FFTesterWS/">                          \
         <strXMLResultText>'

FLX_PENANG_SAVE_UUT_RSLT_ENTRY_FMT =                                                       \
         '&lt;BATCH&gt;&#xD;                                                               \
          &lt;FACTORY TESTER="{:s}" USER="tester01" /&gt;&#xD;                             \
          &lt;PANEL&gt;&#xD;                                                               \
          &lt;DUT ID="{:s}" SOCKET="1" TIMESTAMP="{:s}" TESTTIME="{:s}" ENDTIME="{:s}" STATUS="{:s}"&gt;&#xD;'

VMARG_PERCENTAGE = {
    # nic_test.py will using "_" to seperate vmargin high/low and percentage, so add a leading _ here when fill the percentage
    "DEFAULT"                    : "",
    # For GINESTRA_D5, if run EDVT, percentage parameter is 3, if MFG, percentage parameter is 2
    # header of value list          Normal, EDVT
    "68-0074"                    : ("_2",   "_3"),
    "68-0075"                    : ("_2",   "_3"),
    "68-0076"                    : ("_2",   "_3"),
    "68-0094"                    : ("_2",   "_3"),
}
