from libdefs import NIC_Type
from libdefs import Factory

GLB_CFG_MFG_TEST_MODE = False
FLEX_SHOP_FLOOR_CONTROL = False
MFG_BYPASS_PSU_CHECK = False

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
    timer1_img = dict()
    timer2_img = dict()
    diagfw_img = dict()
    diagfw_dat = dict()
    goldfw_img = dict()
    goldfw_dat = dict()
    uboot_img = dict()
    uboot_dat = dict()

    # write it down here so release script copies this file
    uboot_img["INSTALLER"] = "install_file"

    # Pensando SKU
    cpld_img["NAPLES25"] = "naples25_rev9_06222020.bin"
    cpld_ver["NAPLES25"] = "0x9"
    cpld_dat["NAPLES25"] = "06-17"
    sec_cpld_img["NAPLES25"] = "naples25_rev89_06172020.bin"
    sec_cpld_ver["NAPLES25"] = "0x89"
    sec_cpld_dat["NAPLES25"] = "06-17"
    diagfw_img["NAPLES25"] = "naples_diagfw_05212020.tar"
    diagfw_dat["NAPLES25"] = "05-21-2020"
    goldfw_img["NAPLES25"] = "naples_goldfw_1.3.1-E-19_0717.tar"
    goldfw_dat["NAPLES25"] = "04-18-2020"
    # HPE SKU
    goldfw_img["NAPLES25"] = "naples_goldfw_apulu_1.10.3-C-26_ClouldA_0806.tar"
    goldfw_dat["NAPLES25"] = "06-18-2020"

    # NAPLES25SWM HPE Enterprise (P26968-001)
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

    # NAPLES25SWM HPE Cloud (P41851-001)
    cpld_img["P41851"] = "naples25_swm_revA_06082020.bin"
    cpld_ver["P41851"] = "0xA"
    cpld_dat["P41851"] = "06-08"
    sec_cpld_img["P41851"] = "naples25_swm_rev8A_06082020.bin"
    sec_cpld_ver["P41851"] = "0x8A"
    sec_cpld_dat["P41851"] = "06-08"
    diagfw_img["P41851"] = "naples_diagfw-1.3.1-E-43-EMMC-030321.tar"
    diagfw_dat["P41851"] = "03-03-2021"
    goldfw_img["P41851"] = "naples_goldfw_iris_1.3.1-E-45_2021.01.31.tar"
    goldfw_dat["P41851"] = "01-31-2021"

    # NAPLES25SWM HPE TAA (P46653-001)
    cpld_img["P46653"] = "naples25_swm_revf_03102021.bin"
    cpld_ver["P46653"] = "0xF"
    cpld_dat["P46653"] = "03-10"
    sec_cpld_img["P46653"] = "naples25_swm_rev8f_03102021.bin"
    sec_cpld_ver["P46653"] = "0x8F"
    sec_cpld_dat["P46653"] = "03-10"
    diagfw_img["P46653"] = "naples_diagfw_1.3.1-E-48_2021.06.08.tar"
    diagfw_dat["P46653"] = "06-08-2021"
    goldfw_img["P46653"] = "naples_goldfw_1.3.1-E-48_2021.06.08.tar"
    goldfw_dat["P46653"] = "06-08-2021"

    # NAPLES25SWM Pensando (68-0016)
    cpld_img["68-0016"] = "naples25_swm_revc_01062021.bin"
    cpld_ver["68-0016"] = "0xC"
    cpld_dat["68-0016"] = "01-06"
    sec_cpld_img["68-0016"] = "naples25_swm_rev8c_01062021.bin"
    sec_cpld_ver["68-0016"] = "0x8C"
    sec_cpld_dat["68-0016"] = "01-06"
    diagfw_img["68-0016"] = "naples_diagfw_1.3.1-E-42_1119_uboot.tar"
    diagfw_dat["68-0016"] = "11-18-2020"
    goldfw_img["68-0016"] = "naples_goldfw_1.3.1-E-42_1119.tar"
    goldfw_dat["68-0016"] = "11-18-2020"

    # NAPLES25SWM Pensando TAA (68-0017)
    cpld_img["68-0017"] = "naples25_swm_revc_01062021.bin"
    cpld_ver["68-0017"] = "0xC"
    cpld_dat["68-0017"] = "01-06"
    sec_cpld_img["68-0017"] = "naples25_swm_rev8c_01062021.bin"
    sec_cpld_ver["68-0017"] = "0x8C"
    sec_cpld_dat["68-0017"] = "01-06"
    diagfw_img["68-0017"] = "naples_diagfw_1.3.1-E-42_1119_uboot.tar"
    diagfw_dat["68-0017"] = "11-18-2020"
    goldfw_img["68-0017"] = "naples_goldfw_1.3.1-E-42_1119.tar"
    goldfw_dat["68-0017"] = "11-18-2020"

    cpld_img["NAPLES25SWMDELL"] = "naples25_swmdell_rev3_01062021.bin"
    cpld_ver["NAPLES25SWMDELL"] = "0x3"
    cpld_dat["NAPLES25SWMDELL"] = "00"
    sec_cpld_img["NAPLES25SWMDELL"] = "naples25_swmdell_rev83_01062021.bin"
    sec_cpld_ver["NAPLES25SWMDELL"] = "0x83"
    sec_cpld_dat["NAPLES25SWMDELL"] = "00"
    diagfw_img["NAPLES25SWMDELL"] = "capri_diagfw_uboot_1.3.1-E-65_2022.10.04.tar"
    diagfw_dat["NAPLES25SWMDELL"] = "08-30-2022"
    goldfw_img["NAPLES25SWMDELL"] = "capri_goldfw_1.3.1-E-65_2022.10.04.tar"
    goldfw_dat["NAPLES25SWMDELL"] = "08-31-2022"

    # OCP HPE (P37689-001)
    cpld_img["NAPLES25OCP"] = "NAPLES25_OCP_REV0B_03102021.bin"
    cpld_ver["NAPLES25OCP"] = "0xB"
    cpld_dat["NAPLES25OCP"] = "01-10"
    sec_cpld_img["NAPLES25OCP"] = "NAPLES25_OCP_REV8B_03102021.bin"
    sec_cpld_ver["NAPLES25OCP"] = "0x8B"
    sec_cpld_dat["NAPLES25OCP"] = "01-10"
    diagfw_img["NAPLES25OCP"] = "capri_diagfw_uboot_1.3.1-E-65_2022.10.04.tar"
    diagfw_dat["NAPLES25OCP"] = "08-30-2022"
    goldfw_img["NAPLES25OCP"] = "capri_goldfw_1.3.1-E-65_2022.10.04.tar"
    goldfw_dat["NAPLES25OCP"] = "08-31-2022"
    # OCP DELL (68-0010)
    cpld_img["68-0010"] = "NAPLES25_OCP_REV0B_03102021.bin"
    cpld_ver["68-0010"] = "0xB"
    cpld_dat["68-0010"] = "01-10"
    sec_cpld_img["68-0010"] = "NAPLES25_OCP_REV8B_03102021.bin"
    sec_cpld_ver["68-0010"] = "0x8B"
    sec_cpld_dat["68-0010"] = "01-10"
    diagfw_img["68-0010"] = "capri_diagfw_uboot_1.3.1-E-65_2022.10.04.tar"
    diagfw_dat["68-0010"] = "08-30-2022"
    goldfw_img["68-0010"] = "capri_goldfw_1.3.1-E-65_2022.10.04.tar"
    goldfw_dat["68-0010"] = "08-31-2022"

    cpld_img["NAPLES25SWM833"] = "naples25_833_rev2_02112021.bin"
    cpld_ver["NAPLES25SWM833"] = "0x2"
    cpld_dat["NAPLES25SWM833"] = "02-11"
    sec_cpld_img["NAPLES25SWM833"] = "naples25_833_rev82_02112021.bin"
    sec_cpld_ver["NAPLES25SWM833"] = "0x82"
    sec_cpld_dat["NAPLES25SWM833"] = "02-11"
    diagfw_img["NAPLES25SWM833"] = "naples_diagfw-1.3.1-E-43_20210109.tar"
    diagfw_dat["NAPLES25SWM833"] = "01-09-2021"
    goldfw_img["NAPLES25SWM833"] = "naples_fw_RELB++_1.14.2-E-24_2021.02.01.tar"
    goldfw_dat["NAPLES25SWM833"] = "01-09-2021"

    cpld_img["NAPLES100"] = "naples100_cpld_rev9_05312019.bin"
    cpld_ver["NAPLES100"] = "0x9"
    cpld_dat["NAPLES100"] = "05-31"
    sec_cpld_img["NAPLES100"] = "naples100_cpld_rev89_06032019.bin"
    sec_cpld_ver["NAPLES100"] = "0x89"
    sec_cpld_dat["NAPLES100"] = "05-23"
    diagfw_img["NAPLES100"] = "naples_diagfw_05212020.tar"
    diagfw_dat["NAPLES100"] = "05-21-2020"
    goldfw_img["NAPLES100"] = "naples_goldfw_09182019.tar"
    goldfw_dat["NAPLES100"] = "09-17-2019"

    # Enterprise release
    cpld_img["NAPLES100HPE"] = "naples100_hpe_rev4_03102021.bin"
    cpld_ver["NAPLES100HPE"] = "0x4"
    cpld_dat["NAPLES100HPE"] = "03-10"
    sec_cpld_img["NAPLES100HPE"] = "naples100_hpe_rev84_03102021.bin"
    sec_cpld_ver["NAPLES100HPE"] = "0x84"
    sec_cpld_dat["NAPLES100HPE"] = "03-10"
    diagfw_img["NAPLES100HPE"] = "naples_diagfw-1.3.1-E-43-EMMC-030321.tar"
    diagfw_dat["NAPLES100HPE"] = "03-03-2021"
    goldfw_img["NAPLES100HPE"] = "capri_goldfw_1.3.1-E-59_2022.07.14.tar"
    goldfw_dat["NAPLES100HPE"] = "04-25-2022"
    # Cloud release
    cpld_img["P41854"] = "naples100_hpe_rev2_01052021.bin"
    cpld_ver["P41854"] = "0x2"
    cpld_dat["P41854"] = "01-05"
    sec_cpld_img["P41854"] = "naples100_hpe_rev82_01052021.bin"
    sec_cpld_ver["P41854"] = "0x82"
    sec_cpld_dat["P41854"] = "01-05"
    diagfw_img["P41854"] = "naples_diagfw-1.3.1-E-43-EMMC-030321.tar"
    diagfw_dat["P41854"] = "03-03-2021"
    goldfw_img["P41854"] = "naples_goldfw_iris_1.3.1-E-45_2021.01.31.tar"
    goldfw_dat["P41854"] = "01-31-2021"

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

    cpld_img["NAPLES100DELL"] = "naples100_dell_rev1_05182021.bin"
    cpld_ver["NAPLES100DELL"] = "0x1"
    cpld_dat["NAPLES100DELL"] = "05-18"
    sec_cpld_img["NAPLES100DELL"] = "naples100_dell_rev81_05182021.bin"
    sec_cpld_ver["NAPLES100DELL"] = "0x81"
    sec_cpld_dat["NAPLES100DELL"] = "05-18"
    diagfw_img["NAPLES100DELL"] = "capri_diagfw_1.3.1-E-57_2021.10.29.tar"
    diagfw_dat["NAPLES100DELL"] = "10-29-2021"
    goldfw_img["NAPLES100DELL"] = "capri_goldfw_1.3.1-E-57_2021.10.29.tar"
    goldfw_dat["NAPLES100DELL"] = "10-29-2021"

    cpld_img["FORIO"] = ""
    cpld_ver["FORIO"] = "0x4"
    cpld_dat["FORIO"] = "04-11"
    sec_cpld_img["FORIO"] = ""
    sec_cpld_ver["FORIO"] = ""
    sec_cpld_dat["FORIO"] = ""
    diagfw_img["FORIO"] = ""
    diagfw_dat["FORIO"] = "05-21-2020"
    goldfw_img["FORIO"] = ""
    goldfw_dat["FORIO"] = "04-18-2020"

    cpld_img["VOMERO"] = "vomero_rev4_02072020.bin"
    cpld_ver["VOMERO"] = ""
    cpld_dat["VOMERO"] = ""
    sec_cpld_img["VOMERO"] = "vomero_rev84_02102020.bin"
    sec_cpld_ver["VOMERO"] = ""
    sec_cpld_dat["VOMERO"] = ""
    diagfw_img["VOMERO"] = "naples_diagfw_05212020.tar"
    diagfw_dat["VOMERO"] = "02-03-2020"
    goldfw_img["VOMERO"] = ""
    goldfw_dat["VOMERO"] = "04-18-2020"

    cpld_img["VOMERO2"] = "vomero2_rev5_07242020.bin"
    cpld_ver["VOMERO2"] = "0x5"
    cpld_dat["VOMERO2"] = "00-192"
    sec_cpld_img["VOMERO2"] = "vomero2_rev85_07242020.bin"
    sec_cpld_ver["VOMERO2"] = "0x85"
    sec_cpld_dat["VOMERO2"] = "00-194"
    diagfw_img["VOMERO2"] = "naples_diagfw_w_uboot_1.3.1-E-26_0620.tar"
    diagfw_dat["VOMERO2"] = "06-18-2020"
    goldfw_img["VOMERO2"] = "naples_minigoldfw_1.7.4-C-7_0702.tar"
    goldfw_dat["VOMERO2"] = "07-01-2020"

    cpld_img["ORTANO2"] = "naples200_ortano2_rev3_9_07292021.bin"
    cpld_ver["ORTANO2"] = "0x3"
    cpld_dat["ORTANO2"] = "0x09"
    sec_cpld_img["ORTANO2"] = "naples200_ortano2_rev3_9_07292021.bin"
    sec_cpld_ver["ORTANO2"] = "0x3"
    sec_cpld_dat["ORTANO2"] = "0x09"
    fail_cpld_img["ORTANO2"] = "naples200_ortano2_failsafe_rev3_A_04202022.bin"
    fail_cpld_ver["ORTANO2"] = "0x3"
    fail_cpld_dat["ORTANO2"] = "0x10"
    fea_cpld_img["ORTANO2"] = "naples200_ortano2_fea_04272021.bin"
    diagfw_img["ORTANO2"] = "elba_diagfw_1.15.9-C-100_2022.06.22.tar"
    diagfw_dat["ORTANO2"] = "06-16-2022"
    goldfw_img["ORTANO2"] = "elba_goldfw_1.15.9-C-100_2022.06.22.tar"
    goldfw_dat["ORTANO2"] = "06-16-2022"
    uboot_img["ORTANO2"] = "boot0.rev14.img"
    # ORTANO ORACLE (68-0015)
    # cpld_img["ORTANO2"] = "naples200_ortano2_rev3_9_07292021.bin"
    # cpld_ver["ORTANO2"] = "0x3"
    # cpld_dat["ORTANO2"] = "0x09"
    # sec_cpld_img["68-0015"] = "naples200_ortano2_rev3_9_07292021.bin"
    # sec_cpld_ver["68-0015"] = "0x3"
    # sec_cpld_dat["68-0015"] = "0x09"
    # fail_cpld_img["68-0015"] = "naples200_ortano2_failsafe_rev3_9_07292021.bin"
    # fail_cpld_ver["68-0015"] = "0x3"
    # fail_cpld_dat["68-0015"] = "0x09"
    # fea_cpld_img["ORTANO2"] = "naples200_ortano2_fea_04272021.bin"
    # diagfw_img["ORTANO2"] = "elba_diagfw-uboot_1.15.9-C-30_2021.08.20.tar"
    # diagfw_dat["ORTANO2"] = "08-20-2021"
    goldfw_img["68-0015"] = "elba_goldfw_1.15.9-C-100_2022.06.22.tar"
    goldfw_dat["68-0015"] = "06-16-2022"

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
    diagfw_img["POMONTEDELL"] = "naples_diagfw_elba_1.46.0-E-31_2022.08.16.tar"
    diagfw_dat["POMONTEDELL"] = "08-16-2022"
    goldfw_img["POMONTEDELL"] = "naples_goldfw_elba_1.46.0-E-31_2022.08.16.tar"
    goldfw_dat["POMONTEDELL"] = "08-16-2022"
    uboot_img["POMONTEDELL"] = "boot0.rev14.img"
    uboot_dat["POMONTEDELL"] = "14"

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
    diagfw_img["LACONA32DELL"] = "naples_diagfw_elba_1.46.0-E-31_2022.08.16.tar"
    diagfw_dat["LACONA32DELL"] = "08-16-2022"
    goldfw_img["LACONA32DELL"] = "naples_goldfw_elba_1.46.0-E-31_2022.08.16.tar"
    goldfw_dat["LACONA32DELL"] = "08-16-2022"
    uboot_img["LACONA32DELL"] = "boot0.rev14.img"
    uboot_dat["LACONA32DELL"] = "14"

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
    diagfw_img["LACONA32"] = "naples_diagfw_elba_1.46.0-E-31_2022.08.16.tar"
    diagfw_dat["LACONA32"] = "08-16-2022"
    goldfw_img["LACONA32"] = "naples_goldfw_elba_1.46.0-E-31_2022.08.16.tar"
    goldfw_dat["LACONA32"] = "08-16-2022"
    uboot_img["LACONA32"] = "boot0.rev14.img"
    uboot_dat["LACONA32"] = "14"

    cpld_img["ORTANO2ADI"] = "naples200_ortano2A_rev1_5_02112022.bin"
    cpld_ver["ORTANO2ADI"] = "0x1"
    cpld_dat["ORTANO2ADI"] = "0x05"
    sec_cpld_img["ORTANO2ADI"] = "naples200_ortano2A_rev1_5_02112022.bin"
    sec_cpld_ver["ORTANO2ADI"] = "0x1"
    sec_cpld_dat["ORTANO2ADI"] = "0x05"
    fail_cpld_img["ORTANO2ADI"] = "naples200_ortano2A_failsafe_rev3_D_06082022.bin"
    fail_cpld_ver["ORTANO2ADI"] = "0x3"
    fail_cpld_dat["ORTANO2ADI"] = "0x13"
    fea_cpld_img["ORTANO2ADI"] = "naples200_ortano2A_fea_rev3_D_06082022.bin"
    diagfw_img["ORTANO2ADI"] = "elba_diagfw_1.15.9-C-100_2022.06.22.tar"
    diagfw_dat["ORTANO2ADI"] = "06-16-2022"
    goldfw_img["ORTANO2ADI"] = "elba_goldfw_1.15.9-C-100_2022.06.22.tar"
    goldfw_dat["ORTANO2ADI"] = "06-16-2022"
    uboot_img["ORTANO2ADI"] = "boot0.rev14.img"
    cpld_img["68-0026"] = "naples200_ortano2A_rev3_C_03302022.bin"
    cpld_ver["68-0026"] = "0x3"
    cpld_dat["68-0026"] = "0x12"
    sec_cpld_img["68-0026"] = "naples200_ortano2A_rev3_C_03302022.bin"
    sec_cpld_ver["68-0026"] = "0x3"
    sec_cpld_dat["68-0026"] = "0x12"
    fail_cpld_img["68-0026"] = "naples200_ortano2A_failsafe_rev3_D_06082022.bin"
    fail_cpld_ver["68-0026"] = "0x3"
    fail_cpld_dat["68-0026"] = "0x13"
    goldfw_img["68-0026"] = "elba_goldfw_1.15.9-C-100_2022.06.22.tar"
    goldfw_dat["68-0026"] = "06-16-2022"
    #IBM ADI
    cpld_img["ORTANO2ADIIBM"] = "naples200_ortano2A_rev1_5_02112022.bin"
    cpld_ver["ORTANO2ADIIBM"] = "0x1"
    cpld_dat["ORTANO2ADIIBM"] = "0x05"
    sec_cpld_img["ORTANO2ADIIBM"] = "naples200_ortano2A_rev1_5_02112022.bin"
    sec_cpld_ver["ORTANO2ADIIBM"] = "0x1"
    sec_cpld_dat["ORTANO2ADIIBM"] = "0x05"
    fail_cpld_img["ORTANO2ADIIBM"] = "naples200_ortano2A_rev3_C_failsafe_04072022.bin"
    fail_cpld_ver["ORTANO2ADIIBM"] = "0x3"
    fail_cpld_dat["ORTANO2ADIIBM"] = "0x12"
    fea_cpld_img["ORTANO2ADIIBM"] = "naples200_ortano2A_fea_rev3_C_01192022.bin"
    diagfw_img["ORTANO2ADIIBM"] = "naples_diagfw_elba_1.51.0-G-6_2022.09.30.tar"
    diagfw_dat["ORTANO2ADIIBM"] = "09-29-2022"
    goldfw_img["ORTANO2ADIIBM"] = "naples_goldfw_elba_1.51.0-G-6_2022.09.30.tar"
    goldfw_dat["ORTANO2ADIIBM"] = "09-29-2022"
    uboot_img["ORTANO2ADIIBM"] = "boot0.rev14.img"
    cpld_img["68-0028"] = "naples200_ortano2A_rev3_D_06082022.bin"
    cpld_ver["68-0028"] = "0x3"
    cpld_dat["68-0028"] = "0x13"
    sec_cpld_img["68-0028"] = "naples200_ortano2A_rev3_D_06082022.bin"
    sec_cpld_ver["68-0028"] = "0x3"
    sec_cpld_dat["68-0028"] = "0x13"
    fail_cpld_img["68-0028"] = "naples200_ortano2A_failsafe_rev3_D_06082022.bin"
    fail_cpld_ver["68-0028"] = "0x3"
    fail_cpld_dat["68-0028"] = "0x13"
    goldfw_img["68-0028"] = "naples_goldfw_elba_1.51.0-G-6_2022.09.30.tar"
    goldfw_dat["68-0028"] = "09-29-2022"
    #MSFT ADI
    cpld_img["ORTANO2ADIMSFT"] = "naples200_ortano2A_rev1_5_02112022.bin"
    cpld_ver["ORTANO2ADIMSFT"] = "0x1"
    cpld_dat["ORTANO2ADIMSFT"] = "0x05"
    sec_cpld_img["ORTANO2ADIMSFT"] = "naples200_ortano2A_rev1_5_02112022.bin"
    sec_cpld_ver["ORTANO2ADIMSFT"] = "0x1"
    sec_cpld_dat["ORTANO2ADIMSFT"] = "0x05"
    fail_cpld_img["ORTANO2ADIMSFT"] = "naples200_ortano2A_rev3_C_failsafe_04072022.bin"
    fail_cpld_ver["ORTANO2ADIMSFT"] = "0x3"
    fail_cpld_dat["ORTANO2ADIMSFT"] = "0x12"
    fea_cpld_img["ORTANO2ADIMSFT"] = "naples200_ortano2A_fea_rev3_C_01192022.bin"
    diagfw_img["ORTANO2ADIMSFT"] = "naples_diagfw_elba_1.51.0-G-6_2022.09.30.tar"
    diagfw_dat["ORTANO2ADIMSFT"] = "09-29-2022"
    goldfw_img["ORTANO2ADIMSFT"] = "naples_goldfw_elba_1.51.0-G-6_2022.09.30.tar"
    goldfw_dat["ORTANO2ADIMSFT"] = "09-29-2022"
    uboot_img["ORTANO2ADIMSFT"] = "boot0.rev14.img"
    cpld_img["68-0034"] = "naples200_ortano2A_rev3_D_06082022.bin"
    cpld_ver["68-0034"] = "0x3"
    cpld_dat["68-0034"] = "0x13"
    sec_cpld_img["68-0034"] = "naples200_ortano2A_rev3_D_06082022.bin"
    sec_cpld_ver["68-0034"] = "0x3"
    sec_cpld_dat["68-0034"] = "0x13"
    fail_cpld_img["68-0034"] = "naples200_ortano2A_failsafe_rev3_D_06082022.bin"
    fail_cpld_ver["68-0034"] = "0x3"
    fail_cpld_dat["68-0034"] = "0x13"
    goldfw_img["68-0034"] = "naples_goldfw_elba_1.51.0-G-6_2022.09.30.tar"
    goldfw_dat["68-0034"] = "09-29-2022"

    cpld_img["ORTANO2INTERP"] = "naples200_ortano2I_rev3_A_05132022.bin"
    cpld_ver["ORTANO2INTERP"] = "0x3"
    cpld_dat["ORTANO2INTERP"] = "0x10"
    sec_cpld_img["ORTANO2INTERP"] = "naples200_ortano2I_rev3_A_05132022.bin"
    sec_cpld_ver["ORTANO2INTERP"] = "0x3"
    sec_cpld_dat["ORTANO2INTERP"] = "0x10"
    fail_cpld_img["ORTANO2INTERP"] = "naples200_ortano2I_failsafe_rev3_A_05142022.bin"
    fail_cpld_ver["ORTANO2INTERP"] = "0x3"
    fail_cpld_dat["ORTANO2INTERP"] = "0x10"
    fea_cpld_img["ORTANO2INTERP"] = "naples200_ortano2A_fea_rev3_A_01062022.bin"
    diagfw_img["ORTANO2INTERP"] = "elba_diagfw_1.15.9-C-100_2022.06.22.tar"
    diagfw_dat["ORTANO2INTERP"] = "06-16-2022"
    goldfw_img["ORTANO2INTERP"] = "elba_goldfw_1.15.9-C-100_2022.06.22.tar"
    goldfw_dat["ORTANO2INTERP"] = "06-16-2022"

class MTP_IMAGES:
    amd64_img = dict()
    arm64_img = dict()
    mtp_io_cpld_img = dict()
    mtp_io_cpld_ver = dict()
    mtp_jtag_cpld_img = dict()
    mtp_jtag_cpld_ver = dict()

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

    penctl_img = "penctl.linux.02012021"
    penctl_token_img = "penctl.token"
    rotctrl_img = "rotctrl"

# MFG release images
class MFG_IMAGE_FILES:
    MTP_AMD64_IMAGE = "image_amd64_elba_ortanoadi_pilot_v1.45-release.tar"
    MTP_ARM64_IMAGE = "image_arm64_elba_ortanoadi_pilot_v1.45-release.tar"
    ASIC_AMD64_IMAGE = "nic_x86_64.tar.gz"
    ASIC_ARM64_IMAGE = "nic_aarch64.tar.gz"
    
    penctl_img = "penctl.linux.02012021"
    penctl_token_img = "penctl.token"


class PART_NUMBERS_MATCH:
    N100_PEN_PN_FMT = r"68-0003-0[0-9]{1} [A-Z0-9]{2}"        #68-0003-01 01    NAPLES 100 PENSANDO
    N100_NET_PN_FMT = r"111-04635"                            #111-04635        NAPLES 100 NETAPP
    N100_PN_FMT_ALL = r"{:s}|{:s}".format(N100_PEN_PN_FMT,N100_NET_PN_FMT)

    N100_IBM_PN_FMT = r"68-0013-0[0-9]{1} [A-Z0-9]{2}"        #68-0013-01 03    NAPLES100 IBM
    N100_IBM_FMT_ALL = r"{:s}".format(N100_IBM_PN_FMT)

    N100_HPE_PN_FMT     = r"P37692-00[0-9]{1}"                #P37692-001       NAPLES100 HPE 
    N100_HPE_CLD_PN_FMT = r"P41854-00[0-9]{1}"                #P41854-001       NAPLES100 HPE CLOUD
    N100_HPE_FMT_ALL = r"{:s}|{:s}".format(N100_HPE_PN_FMT, N100_HPE_CLD_PN_FMT)

    N100_DELL_PN_FMT  = r"68-0024-0[0-9]{1} [A-Z0-9]{2}"      #68-0024-01 XX    NAPLES100 DELL
    N100_DELL_FMT_ALL = r"{:s}".format(N100_DELL_PN_FMT) 

    N25_PEN_PN_FMT = r"68-0005-0[0-9]{1} [A-Z0-9]{2}"         #68-0005-03 01    NAPLES25 PENSANDO
    N25_HPE_PN_FMT = r"P18669-00[0-9]{1}"                     #P18669-001       NAPLES25 HPE
    N25_EQI_PN_FMT = r"68-0008-0[0-9]{1} [0-9]{2}"            #68-0008-xx yy    NAPLES25 EQUINIX
    N25_PN_FMT_ALL = r"{:s}|{:s}|{:s}".format(N25_PEN_PN_FMT,N25_HPE_PN_FMT,N25_EQI_PN_FMT)

    N25_SWM_HPE_PN_FMT     = r"P26968-00[0-9]{1}"             #P26968-001       NAPLES25 SWM HPE 
    N25_SWM_HPE_CLD_PN_FMT = r"P41851-00[0-9]{1}"             #P41851-001       NAPLES25 SWM HPE CLOUD
    N25_SWM_HPE_TAA_PN_FMT = r"P46653-00[0-9]{1}"             #P46653-001       NAPLES25 SWM HPE TAA
    N25_SWM_PEN_PN_FMT     = r"68-0016-0[0-9]{1} [A-Z0-9]{2}" #68-0016-01 01    NAPLES25 SWM PENSANDO 
    N25_SWM_PEN_TAA_PN_FMT = r"68-0017-0[0-9]{1} [A-Z0-9]{2}" #68-0017-01 01    NAPLES25 SWM PENSANDO TAA 
    N25_SWM_HPE_FMT_ALL = r"{:s}|{:s}|{:s}|{:s}".format(N25_SWM_HPE_PN_FMT, N25_SWM_HPE_CLD_PN_FMT, N25_SWM_HPE_TAA_PN_FMT, N25_SWM_PEN_PN_FMT, N25_SWM_PEN_TAA_PN_FMT)

    N25_SWM_DEL_PN_FMT = r"68-0014-0[0-9]{1} [A-Z0-9]{2}"     #68-0014-01 00       NAPLES25 SWM DELL
    N25_SWM_DEL_FMT_ALL = r"{:s}".format(N25_SWM_DEL_PN_FMT)

    N25_SWM_833_PN_FMT = r"68-0019-0[0-9]{1} [A-Z0-9]{2}"     #68-0019-01 01       NAPLES25 SWM 833 PENSANDO
    N25_SWM_833_FMT_ALL = r"{:s}".format(N25_SWM_833_PN_FMT)

    N25_OCP_PEN_PN_FMT = r"68-0023-0[0-9]{1} [A-Z0-9]{2}"     #68-00xx-xx       NAPLES25 OCP PENSANDO
    N25_OCP_HPE_PN_FMT = r"P37689-00[0-9]{1}"                 #P37689-001       NAPLES25 OCP HPE
    N25_OCP_HPE_CLD_PN_FMT = r"P41857-00[0-9]{1}"             #P41857-001       NAPLES25 OCP HPE CLOUD
    N25_OCP_DEL_PN_FMT = r"68-0010-0[0-9]{1} [A-Z0-9]{2}"     #68-0010-01       NAPLES25 OCP DELL
    N25_OCP_PN_FMT_ALL = r"{:s}|{:s}|{:s}|{:s}".format(N25_OCP_PEN_PN_FMT,N25_OCP_HPE_PN_FMT, N25_OCP_HPE_CLD_PN_FMT, N25_OCP_DEL_PN_FMT)    

    FORIO_PN_FMT = r"68-0007-0[0-9]{1} [0-9]{2}"              #68-0007-01 01    FORIO
    FORIO_FMT_ALL = r"{:s}".format(FORIO_PN_FMT)

    VOMERO_PN_FMT = r"68-0009-0[0-9]{1} [0-9]{2}"             #68-0009-01 01    VOMERO
    VOMERO_FMT_ALL = r"{:s}".format(VOMERO_PN_FMT)

    VOMERO2_PN_FMT = r"68-0011-0[0-9]{1} [A-Z0-9]{2}"         #68-0011-01 01    VOMERO2
    VOMERO2_FMT_ALL = r"{:s}".format(VOMERO2_PN_FMT)

    ORTANO_PN_FMT = r"68-0015-01 [A-Z0-9]{2}"                 #68-0015-01 01    ORTANO
    ORTANO_FMT_ALL = r"{:s}".format(ORTANO_PN_FMT)

    ORTANO2_ORC_PN_FMT = r"68-0015-0[2-9]{1} [A-Z0-9]{2}"     #68-0015-02 01    ORTANO2 ORACLE
    ORTANO2_PEN_PN_FMT = r"68-0021-0[2-9]{1} [A-Z0-9]{2}"     #68-0021-02 01    ORTANO2 GENERIC (PENSANDO)
    ORTANO2_FMT_ALL = r"{:s}|{:s}".format(ORTANO2_ORC_PN_FMT,ORTANO2_PEN_PN_FMT)

    POMONTEDELL_PN_FMT = r"0PCFPC(?:X|A)[0-9]{2}"             #0PCFPC X/A       POMONTE DELL
    LACONA32DELL_PN_FMT = r"0X322F(?:X|A)[0-9]{2}"            #0X322F X/A       LACONA32 DELL
    LACONA32_PN_FMT = r"P47930-00[0-9]{1}"                    #P47930-001       LACONA32 HPE

    ORTANO2ADI_ORC_PN_FMT = r"68-0026-0[1-9]{1} [A-Z0-9]{2}"     #68-0026-01 01    ORTANO2ADI ORACLE
    ORTANO2ADI_FMT_ALL = r"{:s}".format(ORTANO2ADI_ORC_PN_FMT)

    ORTANO2ADI_IBM_PN_FMT = r"68-0028-0[1-9]{1} [A-Z0-9]{2}"     #68-0028-01 01    ORTANO2ADI IBM
    ORTANO2ADIIBM_FMT_ALL = r"{:s}".format(ORTANO2ADI_IBM_PN_FMT)

    ORTANO2ADI_MSFT_PN_FMT = r"68-0034-0[1-9]{1} [A-Z0-9]{2}"     #68-0034-01 01    ORTANO2ADI MICROSOFT
    ORTANO2ADIMSFT_FMT_ALL = r"{:s}".format(ORTANO2ADI_MSFT_PN_FMT)
    ORTANO2ADI_ALL_FMT_ALL = r"{:s}|{:s}|{:s}".format(ORTANO2ADI_ORC_PN_FMT,ORTANO2ADI_IBM_PN_FMT,ORTANO2ADI_MSFT_PN_FMT)

    ORTANO2INTERP_ORC_PN_FMT = r"68-0029-0[1-9]{1} [A-Z0-9]{2}"    #68-0029-01 02    ORTANO2INTERP_ORC_PN_FMT ORACLE
    ORTANO2INTERP_FMT_ALL = r"{:s}".format(ORTANO2INTERP_ORC_PN_FMT)

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

DIAG_NIGHTLY_REPORT_ACCOUNT = "diag-nightly@pensando.io"
DIAG_NIGHTLY_REPORT_PASSWD = "diag-nightly"
DIAG_NIGHTLY_REPORT_RECEIPIENT = "ps-diag@pensando.io"
DIAG_OS_PROMPT_LIST = ["$", "#", ">"]
#DIAG_SSH_OPTIONS = " -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"
DIAG_SSH_OPTIONS = " -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"

MFG_VALID_FW_LIST = ["diagfw", "mainfwa", "mainfwb", "goldfw", "extdiag"]
MFG_VALID_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES25, NIC_Type.VOMERO2, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25OCP, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP]
MFG_PROTO_NIC_TYPE_LIST = [NIC_Type.FORIO, NIC_Type.VOMERO, NIC_Type.ORTANO]

MTP_REV02_CAPABLE_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL, NIC_Type.VOMERO2]
MTP_REV03_CAPABLE_NIC_TYPE_LIST = [NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP]
MTP_REV04_CAPABLE_NIC_TYPE_LIST = [NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP]

CAPRI_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL, NIC_Type.VOMERO2, NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP]
ELBA_NIC_TYPE_LIST = [NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP]

PSLC_MODE_TYPE_LIST = [NIC_Type.VOMERO2, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2INTERP]
FPGA_TYPE_LIST = [NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32]
TWO_OOB_MGMT_PORT_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL]
CONSOLE_DDR_BIST_NIC_LIST = [NIC_Type.ORTANO2INTERP,NIC_Type.ORTANO2, NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT] #temporary list to hold nic types while gradually offloading ddr_bist from L1 test
DDR_HARCODED_TRAINING_NIC_LIST = []

# please check the label specification
# FLM[Year, like 18, 19, 20][Week: 00-52][4 hex sequential digits]
FLX_MILPITAS_SN_FMT = "FLM\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
FLX_PENANG_SN_FMT = "FP[N|A|B|D]\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
FLX_P1_SN_FMT           = "FPC\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
HP_MILPITAS_SN_FMT = "5UP\d{1}[0-5]{1}\d{1}[0-9B-DF-HJ-NP-TV-Z]{4}"
HP_PENANG_SN_FMT = "[2|3]Y[U|1]\d{1}[0-5]{1}\d{1}[0-9B-DF-HJ-NP-TV-Z]{4}"
NAPLES_SN_FMT = r"{:s}|{:s}".format(FLX_PENANG_SN_FMT,FLX_P1_SN_FMT)
HP_SN_FMT = r"{:s}|{:s}".format(HP_MILPITAS_SN_FMT, HP_PENANG_SN_FMT)
DELL_PPID_COUNTRY_FMT = r"(?:US|MY)"
DELL_PPID_PART_NUM_FMT = r"(?:0PCFPC|0X322F)"
DELL_PPID_MFG_ID_FMT = r"(?:FLUPK|FLEPK)"
DELL_PPID_DATE_CODE_FMT = r"[0-9][1-9A-C][1-9A-V]"
DELL_PPID_SER_NUM_FMT = r"[0-9A-O][0-9A-Z]{3}"
DELL_PPID_REV_FMT = r"[X|A][0-9]{2}"
DELL_PPID_FMT = DELL_PPID_COUNTRY_FMT + DELL_PPID_PART_NUM_FMT + DELL_PPID_MFG_ID_FMT + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT
DELL_PPID_MILPITAS_SN_FMT = r"USFLUPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT
DELL_PPID_PENANG_SN_FMT   = r"MYFLEPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT
DELL_PPID_MILPITAS_FMT = r"US" + DELL_PPID_PART_NUM_FMT + "FLUPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT
DELL_PPID_PENANG_FMT   = r"MY" + DELL_PPID_PART_NUM_FMT + "FLEPK" + DELL_PPID_DATE_CODE_FMT + DELL_PPID_SER_NUM_FMT + DELL_PPID_REV_FMT
DELL_PPID_SN_FMT = r"{:s}|{:s}".format(DELL_PPID_MILPITAS_SN_FMT,DELL_PPID_PENANG_SN_FMT)
DELL_PPID_PN_FMT = DELL_PPID_PART_NUM_FMT + DELL_PPID_REV_FMT
FLX_MILPITAS_BUILD_SN_FMT = r"{:s}|{:s}|{:s}|{:s}".format(FLX_MILPITAS_SN_FMT, HP_MILPITAS_SN_FMT, DELL_PPID_MILPITAS_SN_FMT,DELL_PPID_MILPITAS_FMT)
FLX_PENANG_BUILD_SN_FMT = r"{:s}|{:s}|{:s}|{:s}".format(FLX_PENANG_SN_FMT, HP_PENANG_SN_FMT, DELL_PPID_PENANG_SN_FMT,DELL_PPID_PENANG_FMT)
FLX_P1_BUILD_SN_FMT = r"{:s}".format(FLX_P1_SN_FMT)
DELL_BUILD_SN_FMT = r"{:s}|{:s}".format(DELL_PPID_MILPITAS_SN_FMT, DELL_PPID_PENANG_SN_FMT)
NAPLES_MAC_FMT = r"00AECD[A-F0-9]{6}"
NAPLES_PN_FMT = r"68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2}$"
PN_MINUS_REV_MASK = -3 # (last three digits)
HP_PN_FMT = r"[A-Z0-9]{6}-[0-9]{3}$"
HP_SWN_PN_FMT = r"HPE Product Number +([A-Z0-9]{6}-B[0-9]{2})"
NAPLES_DISP_SN_FMT = r"Serial Number +({:s}|{:s})".format(FLX_PENANG_SN_FMT,FLX_P1_SN_FMT)
HP_DISP_SN_FMT = r"Serial Number +({:s}|{:s})".format(HP_MILPITAS_SN_FMT,HP_PENANG_SN_FMT)
DELL_PPID_DISP_SN_FMT = r"Serial Number +({:s})".format(DELL_PPID_SN_FMT)
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
DELL_PPID_DISP_PN_FMT = r"Part Number +({:s})".format(DELL_PPID_PN_FMT)
HPESWM_DISP_ASSET_FMT = r"Asset Tag Type/Length.*0x(\w+)"
OCP_ADAPTER_FIXED_MAC = "FFFFFFFFFFFF"
OCP_ADAPTER_FIXED_PN  = "00-0000-00 00"

NIC_MGMT_USERNAME = "root"
NIC_MGMT_PASSWORD = "pen123"

MTP_INTERNAL_MGMT_IP_ADDR = "10.1.1.100"
MTP_INTERNAL_MGMT_NETMASK = "255.255.255.0"


Factory_network_config = {
    Factory.FSP: {
        "Networks": [u"192.168.1.0/24", u"192.168.2.0/24", u"192.168.3.0/24", u"192.168.4.0/24"],
        "Flexflow": "10.206.9.68"
    },
    Factory.MILPITAS: {
        "Networks": [u"192.168.5.0/24"],
        "Flexflow": "10.20.33.140"
    },
    Factory.P1: {
        "Networks": [u"192.168.8.0/22"],
        "Flexflow": "10.192.39.48"
    },
    Factory.LAB: {
        "Networks": [u"192.168.68.0/22"],
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
          &lt;DUT ID="{:s}" SOCKET="1" TIMESTAMP="{:s}" TESTTIME="{:s}" ENDTIME="{:s}" STATUS="{:s}"&gt;&#xD; \
          &lt;GROUP NAME="{:s}" GROUPINDEX="1" LOOPINDEX="-1" TYPE="PassFailTest" Remark="Comment" TOTALTIME="{:s}" STATUS="{:s}"&gt;&#xD;'

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
          &lt;/PANEL&gt;&#xD;'
FLX_SAVE_UUT_RSLT_ENTRY_WITH_EXTRA_END =                                                   \
         '&lt;EXTRA {:s} xmlns:b="tty"/&gt;&#xD;'
FLX_SAVE_UUT_RSLT_ENTRY_BATCH_END =                                                        \
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
          &lt;DUT ID="{:s}" SOCKET="1" TIMESTAMP="{:s}" TESTTIME="{:s}" ENDTIME="{:s}" STATUS="{:s}"&gt;&#xD; \
          &lt;GROUP NAME="{:s}" GROUPINDEX="1" LOOPINDEX="-1" TYPE="PassFailTest" Remark="Comment" TOTALTIME="{:s}" STATUS="{:s}"&gt;&#xD;'

