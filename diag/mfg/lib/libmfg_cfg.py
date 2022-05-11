from libdefs import NIC_Type

GLB_CFG_MFG_TEST_MODE = False

MFG_BYPASS_PSU_CHECK = True

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
    diagfw_img = dict()
    diagfw_dat = dict()
    goldfw_img = dict()
    goldfw_dat = dict()
    uboot_img = dict()
    uboot_dat = dict()

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
    diagfw_img["NAPLES25SWM"] = "naples_diagfw-1.3.1-E-43-EMMC-030321.tar"
    diagfw_dat["NAPLES25SWM"] = "03-03-2021"
    goldfw_img["NAPLES25SWM"] = "naples_goldfw_iris_1.3.1-E-45_2021.01.31.tar"
    goldfw_dat["NAPLES25SWM"] = "01-31-2021"

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
    diagfw_img["NAPLES25SWMDELL"] = "naples_diagfw-1.3.1-E-43-EMMC-030321.tar"
    diagfw_dat["NAPLES25SWMDELL"] = "03-03-2021"
    goldfw_img["NAPLES25SWMDELL"] = "naples_goldfw_iris_1.3.1-E-45_2021.01.31.tar"
    goldfw_dat["NAPLES25SWMDELL"] = "01-31-2021"

    # OCP HPE (P37689-001)
    cpld_img["NAPLES25OCP"] = "NAPLES25_OCP_REV0B_03102021.bin"
    cpld_ver["NAPLES25OCP"] = "0xB"
    cpld_dat["NAPLES25OCP"] = "01-10"
    sec_cpld_img["NAPLES25OCP"] = "NAPLES25_OCP_REV8B_03102021.bin"
    sec_cpld_ver["NAPLES25OCP"] = "0x8B"
    sec_cpld_dat["NAPLES25OCP"] = "01-10"
    diagfw_img["NAPLES25OCP"] = "naples_diagfw-1.3.1-E-43-EMMC-030321.tar"
    diagfw_dat["NAPLES25OCP"] = "03-03-2021"
    goldfw_img["NAPLES25OCP"] = "naples_goldfw_iris_1.3.1-E-45_2021.01.31.tar"
    goldfw_dat["NAPLES25OCP"] = "01-31-2021"
    # OCP DELL (68-0010)
    diagfw_img["68-0010"] = "naples_diagfw_1.3.1-E-42_1119_uboot.tar"
    diagfw_dat["68-0010"] = "11-18-2020"

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
    goldfw_img["NAPLES100HPE"] = "naples_goldfw_iris_1.3.1-E-45_2021.01.31.tar"
    goldfw_dat["NAPLES100HPE"] = "01-31-2021"
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
    fail_cpld_img["ORTANO2"] = "naples200_ortano2_failsafe_rev3_9_07292021.bin"
    fail_cpld_ver["ORTANO2"] = "0x3"
    fail_cpld_dat["ORTANO2"] = "0x09"
    fea_cpld_img["ORTANO2"] = "naples200_ortano2_fea_04272021.bin"
    diagfw_img["ORTANO2"] = "elba_diagfw-uboot_1.15.9-C-30_2021.08.20.tar"
    diagfw_dat["ORTANO2"] = "08-20-2021"
    goldfw_img["ORTANO2"] = "elba_goldfw_1.15.9-C-30_2021.08.20.tar"
    goldfw_dat["ORTANO2"] = "08-20-2021"
    # ORTANO ORACLE (68-0015)
    # cpld_img["ORTANO2"] = "naples200_ortano2_rev3_9_07292021.bin"
    # cpld_ver["ORTANO2"] = "0x3"
    # cpld_dat["ORTANO2"] = "0x09"
    # sec_cpld_img["ORTANO2"] = "naples200_ortano2_rev3_7_05142021.bin"
    # sec_cpld_ver["ORTANO2"] = "0x3"
    # sec_cpld_dat["ORTANO2"] = "0x07"
    # fail_cpld_img["ORTANO2"] = "naples200_ortano2_failsafe_rev3_7_05142021.bin"
    # fail_cpld_ver["ORTANO2"] = "0x3"
    # fail_cpld_dat["ORTANO2"] = "0x07"
    # fea_cpld_img["ORTANO2"] = "naples200_ortano2_fea_04272021.bin"
    # diagfw_img["ORTANO2"] = "elba_diagfw-uboot_1.15.9-C-30_2021.08.20.tar"
    # diagfw_dat["ORTANO2"] = "08-20-2021"
    # goldfw_img["ORTANO2"] = "elba_goldfw_1.15.8-C-9_2021.05.22.tar"
    # goldfw_dat["ORTANO2"] = "05-22-2021"
    goldfw_img["68-0015"] = "elba_goldfw_1.15.9-C-46_2021.09.30.tar"
    goldfw_dat["68-0015"] = "09-30-2021"

    cpld_img["POMONTEDELL"] = "naples200_pom_dell_main_rev1_11_02252022.bin"
    cpld_ver["POMONTEDELL"] = "0x1"
    cpld_dat["POMONTEDELL"] = "0x11"
    sec_cpld_img["POMONTEDELL"] = "naples200_pom_dell_main_rev1_11_02252022.bin"
    sec_cpld_ver["POMONTEDELL"] = "0x1"
    sec_cpld_dat["POMONTEDELL"] = "0x11"
    fail_cpld_img["POMONTEDELL"] = "naples200_pom_dell_gold_rev1_11_02252022.bin"
    fail_cpld_ver["POMONTEDELL"] = "0x1"
    fail_cpld_dat["POMONTEDELL"] = "0x11"
    diagfw_img["POMONTEDELL"] = "naples_diagfw_elba_1.46.0-E-15_2022.04.27.tar"
    diagfw_dat["POMONTEDELL"] = "04-08-2022"
    goldfw_img["POMONTEDELL"] = "naples_goldfw_elba_1.46.0-E-15_2022.04.27.tar"
    goldfw_dat["POMONTEDELL"] = "04-08-2022"
    goldfw_dat["90-0017"] = "04-07-2022"

    cpld_img["LACONA32DELL"] = "naples200_lac32_dell_main_rev0_13_09292021.bin"
    cpld_ver["LACONA32DELL"] = "0x0"
    cpld_dat["LACONA32DELL"] = "0x13"
    sec_cpld_img["LACONA32DELL"] = "naples200_lac32_dell_main_rev0_13_09292021.bin"
    sec_cpld_ver["LACONA32DELL"] = "0x0"
    sec_cpld_dat["LACONA32DELL"] = "0x13"
    fail_cpld_img["LACONA32DELL"] = "naples200_lac32_dell_gold_rev0_13_09292021.bin"
    fail_cpld_ver["LACONA32DELL"] = "0x0"
    fail_cpld_dat["LACONA32DELL"] = "0x13"
    diagfw_img["LACONA32DELL"] = "elba_diagfw_1.32.0-E-13_2021.09.21.tar"
    diagfw_dat["LACONA32DELL"] = "09-21-2021"
    goldfw_img["LACONA32DELL"] = "elba_goldfw_1.38-E-7_2021.10.26.tar"
    goldfw_dat["LACONA32DELL"] = "10-22-2021"
    uboot_img["LACONA32DELL"] = "elba_goldfw_1.38-E-7_32g_uboot_2021.11.06.tar"
    uboot_dat["LACONA32DELL"] = "10-22-2021"

    cpld_img["LACONA32"] = "naples200_lac32_hpe_main_rev0_13_09292021.bin"
    cpld_ver["LACONA32"] = "0x0"
    cpld_dat["LACONA32"] = "0x13"
    sec_cpld_img["LACONA32"] = "naples200_lac32_hpe_main_rev0_13_09292021.bin"
    sec_cpld_ver["LACONA32"] = "0x0"
    sec_cpld_dat["LACONA32"] = "0x13"
    fail_cpld_img["LACONA32"] = "naples200_lac32_hpe_gold_rev0_13_09292021.bin"
    fail_cpld_ver["LACONA32"] = "0x0"
    fail_cpld_dat["LACONA32"] = "0x13"
    diagfw_img["LACONA32"] = "elba_diagfw_1.32.0-E-13_2021.09.21.tar"
    diagfw_dat["LACONA32"] = "09-21-2021"
    goldfw_img["LACONA32"] = "elba_goldfw_1.38-E-7_2021.10.26.tar"
    goldfw_dat["LACONA32"] = "10-22-2021"
    uboot_img["LACONA32"] = "elba_goldfw_1.38-E-7_32g_uboot_2021.11.06.tar"
    uboot_dat["LACONA32"] = "10-22-2021"

    cpld_img["ORTANO2ADI"] = "naples200_ortano2A_rev1_5_02112022.bin"
    cpld_ver["ORTANO2ADI"] = "0x1"
    cpld_dat["ORTANO2ADI"] = "0x05"
    sec_cpld_img["ORTANO2ADI"] = "naples200_ortano2A_rev1_5_02112022.bin"
    sec_cpld_ver["ORTANO2ADI"] = "0x1"
    sec_cpld_dat["ORTANO2ADI"] = "0x05"
    fail_cpld_img["ORTANO2ADI"] = "naples200_ortano2A_rev3_C_failsafe_04072022.bin"
    fail_cpld_ver["ORTANO2ADI"] = "0x3"
    fail_cpld_dat["ORTANO2ADI"] = "0x12"
    fea_cpld_img["ORTANO2ADI"] = "naples200_ortano2A_fea_rev3_C_01192022.bin"
    diagfw_img["ORTANO2ADI"] = "elba_diagfw_1.15.9-C-56_2022.01.08.tar"
    diagfw_dat["ORTANO2ADI"] = "01-08-2022"
    goldfw_img["ORTANO2ADI"] = "elba_goldfw_1.15.9-C-64-1-3_2022.04.08.tar"
    goldfw_dat["ORTANO2ADI"] = "04-09-2022"
    cpld_img["68-0026"] = "naples200_ortano2A_rev3_C_03302022.bin"
    cpld_ver["68-0026"] = "0x3"
    cpld_dat["68-0026"] = "0x12"
    sec_cpld_img["68-0026"] = "naples200_ortano2A_rev3_C_03302022.bin"
    sec_cpld_ver["68-0026"] = "0x3"
    sec_cpld_dat["68-0026"] = "0x12"
    fail_cpld_img["68-0026"] = "naples200_ortano2A_rev3_C_failsafe_04072022.bin"
    fail_cpld_ver["68-0026"] = "0x3"
    fail_cpld_dat["68-0026"] = "0x12"
    goldfw_img["68-0026"] = "elba_goldfw_1.15.9-C-64-1-3_2022.04.08.tar"
    goldfw_dat["68-0026"] = "04-09-2022"

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

    MTP_PENCTL_IMAGE = "penctl.linux.02012021"
    MTP_PENCTL_TOKEN = "penctl.token"
    MTP_ROTCTRL_IMAGE = "rotctrl"

# MFG release images
class MFG_IMAGE_FILES:
    MTP_AMD64_IMAGE = "image_amd64_elba_ortano_pilot_v1.39.1-release.tar"
    MTP_ARM64_IMAGE = "image_arm64_elba_ortano_pilot_v1.39.1-release.tar"
    ASIC_AMD64_IMAGE = "nic_x86_64.tar.gz"
    ASIC_ARM64_IMAGE = "nic_aarch64.tar.gz"
    
    MTP_PENCTL_IMAGE = "penctl.linux.0915"
    MTP_PENCTL_TOKEN = "penctl.token"


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
    #ORTANO2ADI_PEN_PN_FMT = r"68-0021-0[1-9]{1} [A-Z0-9]{2}"     #68-0021-01 01    ORTANO2ADI GENERIC (PENSANDO)
    ORTANO2ADI_FMT_ALL = r"{:s}".format(ORTANO2ADI_ORC_PN_FMT)

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
MFG_VALID_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES25, NIC_Type.VOMERO2, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25OCP, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI]
MFG_PROTO_NIC_TYPE_LIST = [NIC_Type.FORIO, NIC_Type.VOMERO, NIC_Type.ORTANO]

MTP_REV02_CAPABLE_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL, NIC_Type.VOMERO2]
MTP_REV03_CAPABLE_NIC_TYPE_LIST = [NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI]
MTP_REV04_CAPABLE_NIC_TYPE_LIST = [NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI]

CAPRI_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL, NIC_Type.VOMERO2, NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP]
ELBA_NIC_TYPE_LIST = [NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI]

PSLC_MODE_TYPE_LIST = [NIC_Type.VOMERO2, NIC_Type.ORTANO2, NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32, NIC_Type.ORTANO2ADI]
FPGA_TYPE_LIST = [NIC_Type.POMONTEDELL, NIC_Type.LACONA32DELL, NIC_Type.LACONA32]
TWO_OOB_MGMT_PORT_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES100DELL]

# please check the label specification
# FLM[Year, like 18, 19, 20][Week: 00-52][4 hex sequential digits]
FLX_MILPITAS_SN_FMT = "FLM\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
FLX_PENANG_SN_FMT = "FP[N|A]\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
HP_MILPITAS_SN_FMT = "5UP\d{1}[0-5]{1}\d{1}[0-9B-DF-HJ-NP-TV-Z]{4}"
HP_PENANG_SN_FMT = "[2|3]Y[U|1]\d{1}[0-5]{1}\d{1}[0-9B-DF-HJ-NP-TV-Z]{4}"
NAPLES_SN_FMT = r"{:s}|{:s}".format(FLX_MILPITAS_SN_FMT,FLX_PENANG_SN_FMT)
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
DELL_BUILD_SN_FMT = r"{:s}|{:s}".format(DELL_PPID_MILPITAS_SN_FMT, DELL_PPID_PENANG_SN_FMT)
NAPLES_MAC_FMT = r"00AECD[A-F0-9]{6}"
NAPLES_PN_FMT = r"68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2}$"
PN_MINUS_REV_MASK = -3 # (last three digits)
HP_PN_FMT = r"[A-Z0-9]{6}-[0-9]{3}$"
HP_SWN_PN_FMT = r"HPE Product Number +([A-Z0-9]{6}-B[0-9]{2})"
NAPLES_DISP_SN_FMT = r"Serial Number +({:s}|{:s})".format(FLX_MILPITAS_SN_FMT,FLX_PENANG_SN_FMT)
HP_DISP_SN_FMT = r"HPE Serial Number +({:s}|{:s})".format(HP_MILPITAS_SN_FMT,HP_PENANG_SN_FMT)
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


# Don't touch the following xml format, it is required for flex flow report

# Milpitas flex server
FLX_WEBSERVER = "10.20.33.140"
FLX_API_URL = "/Pensando/fftester20.asmx"
FLX_GET_UUT_INFO_SOAP = "http:/www.flextronics.com/FFTester20/GetUnitInfo"
FLX_SAVE_UUT_RSLT_SOAP = "http:/www.flextronics.com/FFTester20/SaveResult"

# Penang flex server
#FLX_PENANG_WEBSERVER = "10.192.155.61"
#FLX_PENANG_WEBSERVER = "172.30.178.5"
FLX_PENANG_WEBSERVER = "10.206.9.16"
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
          &lt;/PANEL&gt;&#xD;                                                              \
          &lt;/BATCH&gt;'

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

