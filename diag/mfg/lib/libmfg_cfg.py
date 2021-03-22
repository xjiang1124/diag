from libdefs import NIC_Type

GLB_CFG_MFG_TEST_MODE = True

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
    diagfw_img = dict()
    diagfw_dat = dict()
    goldfw_img = dict()
    goldfw_dat = dict()

    cpld_img["NAPLES25"] = "naples25_rev9_06222020.bin"
    cpld_ver["NAPLES25"] = "0x9"
    cpld_dat["NAPLES25"] = "06-17"
    sec_cpld_img["NAPLES25"] = "naples25_rev89_06172020.bin"
    sec_cpld_ver["NAPLES25"] = "0x89"
    sec_cpld_dat["NAPLES25"] = "06-17"
    diagfw_img["NAPLES25"] = "naples_diagfw_05212020.tar"
    diagfw_dat["NAPLES25"] = "05-21-2020"
    goldfw_img["NAPLES25"] = "naples_goldfw_iris_RELB_1.12.0-E-52_0728.tar"
    goldfw_dat["NAPLES25"] = "06-18-2020"

    cpld_img["NAPLES25SWM"] = "naples25_swm_rev9_04142020.bin"
    cpld_ver["NAPLES25SWM"] = "0x9"
    cpld_dat["NAPLES25SWM"] = "04-20"
    sec_cpld_img["NAPLES25SWM"] = "naples25_swm_rev89_04142020.bin"
    sec_cpld_ver["NAPLES25SWM"] = "0x89"
    sec_cpld_dat["NAPLES25SWM"] = "04-20"
    diagfw_img["NAPLES25SWM"] = "naples_diagfw_1.3.1-E-42_1119_uboot.tar"
    diagfw_dat["NAPLES25SWM"] = "11-18-2020"
    goldfw_img["NAPLES25SWM"] = "naples_goldfw_1.3.1-E-42_1119.tar"
    goldfw_dat["NAPLES25SWM"] = "11-18-2020"

    cpld_img["NAPLES25SWMDELL"] = "naples25_swmdell_rev2_08202020.bin"
    cpld_ver["NAPLES25SWMDELL"] = "0x2"
    cpld_dat["NAPLES25SWMDELL"] = "00"
    sec_cpld_img["NAPLES25SWMDELL"] = "naples25_swmdell_rev82_08202020.bin"
    sec_cpld_ver["NAPLES25SWMDELL"] = "0x82"
    sec_cpld_dat["NAPLES25SWMDELL"] = "00"
    diagfw_img["NAPLES25SWMDELL"] = "naples_diagfw_1.3.1-E-42_1119_uboot.tar"
    diagfw_dat["NAPLES25SWMDELL"] = "11-18-2020"
    goldfw_img["NAPLES25SWMDELL"] = "naples_fw_RELB++_1.14.2-E-24_2021.02.01.tar"
    goldfw_dat["NAPLES25SWMDELL"] = "01-09-2021"

    cpld_img["NAPLES25OCP"] = "naples25_ocp_rev09_021121.bin"
    cpld_ver["NAPLES25OCP"] = "0x9"
    cpld_dat["NAPLES25OCP"] = "02-11"
    sec_cpld_img["NAPLES25OCP"] = "naples25_ocp_rev89_021121.bin"
    sec_cpld_ver["NAPLES25OCP"] = "0x89"
    sec_cpld_dat["NAPLES25OCP"] = "02-11"
    diagfw_img["NAPLES25OCP"] = "naples_diagfw_1.3.1-E-42_1119_uboot.tar"
    diagfw_dat["NAPLES25OCP"] = "11-18-2020"
    goldfw_img["NAPLES25OCP"] = "naples_fw_RELB++_1.14.2-E-24_2021.02.01.tar"
    goldfw_dat["NAPLES25OCP"] = "01-09-2021"

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
    cpld_dat["NAPLES100"] = "05-41"
    sec_cpld_img["NAPLES100"] = "naples100_cpld_rev89_06032019.bin"
    sec_cpld_ver["NAPLES100"] = "0x89"
    sec_cpld_dat["NAPLES100"] = "06-23"
    diagfw_img["NAPLES100"] = "naples_diagfw_05212020.tar"
    diagfw_dat["NAPLES100"] = "05-21-2020"
    goldfw_img["NAPLES100"] = "naples_goldfw_09182019.tar"
    goldfw_dat["NAPLES100"] = "09-17-2019"

    cpld_img["NAPLES100HPE"] = "naples100_hpe_rev1_07222020.bin"
    cpld_ver["NAPLES100HPE"] = "0x1"
    cpld_dat["NAPLES100HPE"] = "07-22"
    sec_cpld_img["NAPLES100HPE"] = "naples100_hpe_rev81_07222020.bin"
    sec_cpld_ver["NAPLES100HPE"] = "0x81"
    sec_cpld_dat["NAPLES100HPE"] = "07-22"
    diagfw_img["NAPLES100HPE"] = "naples_diagfw_1.3.1-E-42_1119_uboot.tar"
    diagfw_dat["NAPLES100HPE"] = "11-18-2020"
    goldfw_img["NAPLES100HPE"] = "naples_goldfw_1.3.1-E-42_1119.tar"
    goldfw_dat["NAPLES100HPE"] = "11-18-2020"

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

    cpld_img["ORTANO"] = "naples200_Ortano_rev3_2_03112021.bin"
    cpld_ver["ORTANO"] = "0x3"
    cpld_dat["ORTANO"] = "0x02"
    sec_cpld_img["ORTANO"] = "naples200_Ortano_rev83_2_03112021.bin"
    sec_cpld_ver["ORTANO"] = "0x83"
    sec_cpld_dat["ORTANO"] = "0x02"
    fail_cpld_img["ORTANO"] = "naples200_Ortano_failsafe_rev3_2_03112021.bin"
    fail_cpld_ver["ORTANO"] = "0x83"
    fail_cpld_dat["ORTANO"] = "0x02"
    diagfw_img["ORTANO"] = "elba_diagw_1.5.0-EXP_2021.03.06.tar"
    diagfw_dat["ORTANO"] = "03-06-2021"
    goldfw_img["ORTANO"] = "elba_goldfw_1.22.0-26-12-gbd3da13-dirty_2021.03.06.tar"
    goldfw_dat["ORTANO"] = "03-06-2021"

    cpld_img["ORTANO2"] = "naples200_Ortano2_rev3_2_03112021.bin"
    cpld_ver["ORTANO2"] = "0x3"
    cpld_dat["ORTANO2"] = "0x02"
    sec_cpld_img["ORTANO2"] = "naples200_Ortano2_rev83_2_03112021.bin"
    sec_cpld_ver["ORTANO2"] = "0x83"
    sec_cpld_dat["ORTANO2"] = "0x02"
    fail_cpld_img["ORTANO2"] = "naples200_Ortano2_failsafe_rev3_2_03112021.bin"
    fail_cpld_ver["ORTANO2"] = "0x83"
    fail_cpld_dat["ORTANO2"] = "0x02"
    diagfw_img["ORTANO2"] = "elba_diagw_1.5.0-EXP_2021.03.06.tar"
    diagfw_dat["ORTANO2"] = "03-06-2021"
    goldfw_img["ORTANO2"] = "elba_goldfw_1.22.0-26-12-gbd3da13-dirty_2021.03.06.tar"
    goldfw_dat["ORTANO2"] = "03-06-2021"

# MFG release version control
class NIC_CPLD_Version:
    NAPLES100_VERSION = "0x9"
    NAPLES100_TIMESTAMP = "05-31"
    NAPLES100_SEC_VERSION = "0x89"
    NAPLES100_SEC_TIMESTAMP = "06-23"
    
    NAPLES100IBM_VERSION = "0x3"
    NAPLES100IBM_TIMESTAMP = "09-08"
    NAPLES100IBM_SEC_VERSION = "0x83"
    NAPLES100IBM_SEC_TIMESTAMP = "09-08"
    
    NAPLES100HPE_VERSION = "0x1"
    NAPLES100HPE_TIMESTAMP = "07-22"
    NAPLES100HPE_SEC_VERSION = "0x81"
    NAPLES100HPE_SEC_TIMESTAMP = "07-22"

    NAPLES25_VERSION = "0x9"
    NAPLES25_TIMESTAMP = "06-17"
    NAPLES25_SEC_VERSION = "0x89"
    NAPLES25_SEC_TIMESTAMP = "06-17"

    VOMERO_VERSION = "0x4"
    VOMERO_TIMESTAMP = "02-07"
    VOMERO_SEC_VERSION = "0x84"
    VOMERO_SEC_TIMESTAMP = "02-10"

    VOMERO2_VERSION = "0x5"
    VOMERO2_TIMESTAMP = "00-192"
    VOMERO2_SEC_VERSION = "0x85"
    VOMERO2_SEC_TIMESTAMP = "00-194"
    FORIO_VERSION = "0x4"
    FORIO_TIMESTAMP = "04-11"

    NAPLES25SWM_VERSION = "0x9"
    NAPLES25SWM_TIMESTAMP = "04-20"
    NAPLES25SWM_SEC_VERSION = "0x89"
    NAPLES25SWM_SEC_TIMESTAMP = "04-20"

    NAPLES25SWMDELL_VERSION = "0x3"
    NAPLES25SWMDELL_MINOR_VERSION = "00"
    NAPLES25SWMDELL_SEC_VERSION = "0x83"
    NAPLES25SWMDELL_SEC_TIMESTAMP = "00"

    NAPLES25OCP_VERSION = "0x9"
    NAPLES25OCP_TIMESTAMP = "02-11"
    NAPLES25OCP_SEC_VERSION = "0x89"
    NAPLES25OCP_SEC_TIMESTAMP = "02-11"
    
    ORTANO_VERSION = "0x2"      #major rev
    ORTANO_TIMESTAMP = "0x08"    #minor rev
    ORTANO_SEC_VERSION = "0x2"
    ORTANO_SEC_TIMESTAMP = "0x08"#placeholder version for testing


# MFG release images
class MFG_IMAGE_FILES:
    MTP_AMD64_IMAGE = "image_amd64_03222021.tar"
    MTP_ARM64_IMAGE = "image_arm64_03222021.tar"
    
    MTP_PENCTL_IMAGE = "penctl.linux.0915"
    MTP_PENCTL_TOKEN = "penctl.token"
    
    NIC_DIAGFW_IMAGE = "naples_diagfw_05212020.tar"
    NIC_GOLDFW_IMAGE = "naples_goldfw_1.3.1-E-19_0717.tar"
    NIC_DIAGFW_IMAGE_SWM = "naples_diagfw_1.3.1-E-42_1119_uboot.tar"
    NIC_GOLDFW_IMAGE_SWM = "naples_goldfw_1.3.1-E-42_1119.tar"
    NIC_GOLDFW_IMAGE_SWMDELL = "naples_goldfw_iris_1.14.1-E-12_1025.tar"
    NIC_DIAGFW_IMAGE_HPE_OCP = "naples_diagfw_1.3.1-E-42_1119_uboot.tar"
    NIC_GOLDFW_IMAGE_HPE_OCP = "naples_goldfw_1.3.1-E-42_1119.tar"
    NIC_GOLDFW_IMAGE_IBM = "naples_goldfw_apulu_1.17.0-42_1117.tar"
    NIC_GOLDFW_IMAGE_HPE = "naples_goldfw1_1.3.1-E-28_0731.tar"
    NIC_DIAGFW_IMAGE_HPE_NAPLES100 = "naples_diagfw_1.3.1-E-42_1119_uboot.tar"
    NIC_GOLDFW_IMAGE_HPE_NAPLES100 = "naples_goldfw_1.3.1-E-42_1119.tar"
    NIC_DIAGFW_IMAGE_VOMERO2 = "naples_diagfw_w_uboot_1.3.1-E-26_0620.tar"
    NIC_GOLDFW_IMAGE_VOMERO2 = "naples_minigoldfw_1.7.4-C-7_0702.tar"
    NIC_DIAGFW_IMAGE_NAPLES100 = "naples_diagfw_12172019.tar"
    NIC_GOLDFW_IMAGE_NAPLES100 = "naples_goldfw_09182019.tar"
    NIC_DIAGFW_IMAGE_ORTANO = "elba_diagfw_1.17.0-26-5_1112.tar"
    NIC_GOLDFW_IMAGE_ORTANO = "naples_goldfw_1.17.0-11-2_1108.tar"

    NAPLES25_CPLD_IMAGE = "naples25_rev9_06222020.bin"
    NAPLES25_SEC_CPLD_IMAGE = "naples25_rev89_06172020.bin"

    NAPLES25SWM_CPLD_IMAGE = "naples25_swm_rev9_04142020.bin"
    NAPLES25SWM_SEC_CPLD_IMAGE = "naples25_swm_rev89_04142020.bin"

    NAPLES25SWMDELL_CPLD_IMAGE = "naples25_swmdell_rev3_01062021.bin"
    NAPLES25SWMDELL_SEC_CPLD_IMAGE = "naples25_swmdell_rev83_01062021.bin"

    NAPLES25_HPE_OCP_CPLD_IMAGE = "naples25_ocp_rev09_021121.bin"
    NAPLES25_HPE_OCP_SEC_CPLD_IMAGE = "naples25_ocp_rev89_021121.bin"

    NAPLES100_CPLD_IMAGE = "naples100_cpld_rev9_05312019.bin"
    NAPLES100_SEC_CPLD_IMAGE = "naples100_cpld_rev89_06032019.bin"
    
    NAPLES100IBM_CPLD_IMAGE = "naples100_ibm_rev3_09082020.bin"
    NAPLES100IBM_SEC_CPLD_IMAGE = "naples100_ibm_rev83_09082020.bin"
    
    NAPLES100HPE_CPLD_IMAGE = "naples100_hpe_rev1_07222020.bin"
    NAPLES100HPE_SEC_CPLD_IMAGE = "naples100_hpe_rev81_07222020.bin"
 

    VOMERO_CPLD_IMAGE = "vomero_rev4_02072020.bin"
    VOMERO_SEC_CPLD_IMAGE = "vomero_rev84_02102020.bin"
    VOMERO2_CPLD_IMAGE = "vomero2_rev5_07242020.bin"
    VOMERO2_SEC_CPLD_IMAGE = "vomero2_rev85_07242020.bin"

    ORTANO_CPLD_IMAGE = "ortano_rev28_cfg0.bin"
    ORTANO_SEC_CPLD_IMAGE = "" 


class PART_NUMBERS_MATCH:
    N100_PEN_PN_FMT = r"68-0003-0[0-9]{1} [A-Z0-9]{2}"        #68-0003-01 01    NAPLES 100 PENSANDO
    N100_NET_PN_FMT = r"111-04635"                            #111-04635        NAPLES 100 NETAPP
    N100_PN_FMT_ALL = r"{:s}|{:s}".format(N100_PEN_PN_FMT,N100_NET_PN_FMT)

    N100_IBM_PN_FMT = r"68-0013-0[0-9]{1} [A-Z0-9]{2}"           #68-0013-01 03    NAPLES100 IBM
    N100_IBM_FMT_ALL = r"{:s}".format(N100_IBM_PN_FMT)

    N100_HPE_PN_FMT     = r"P37692-00[0-9]{1}"                #P37692-001       NAPLES100 HPE 
    N100_HPE_CLD_PN_FMT = r"P41854-00[0-9]{1}"                #P41854-001       NAPLES100 HPE CLOUD
    N100_HPE_FMT_ALL = r"{:s}|{:s}".format(N100_HPE_PN_FMT, N100_HPE_CLD_PN_FMT)

    N25_PEN_PN_FMT = r"68-0005-0[0-9]{1} [A-Z0-9]{2}"         #68-0005-03 01    NAPLES25 PENSANDO
    N25_HPE_PN_FMT = r"P18669-00[0-9]{1}"                     #P18669-001       NAPLES25 HPE
    N25_EQI_PN_FMT = r"68-0008-0[0-9]{1} [0-9]{2}"            #68-0008-xx yy    NAPLES25 EQUINIX
    N25_PN_FMT_ALL = r"{:s}|{:s}|{:s}".format(N25_PEN_PN_FMT,N25_HPE_PN_FMT,N25_EQI_PN_FMT)

    N25_SWM_HPE_PN_FMT     = r"P26968-00[0-9]{1}"             #P26968-001       NAPLES25 SWM HPE 
    N25_SWM_HPE_CLD_PN_FMT = r"P41851-00[0-9]{1}"             #P41851-001       NAPLES25 SWM HPE CLOUD
    N25_SWM_PEN_PN_FMT     = r"68-0016-0[0-9]{1} [A-Z0-9]{2}" #68-0016-01 01    NAPLES25 SWM PENSANDO 
    N25_SWM_PEN_TAA_PN_FMT = r"68-0017-0[0-9]{1} [A-Z0-9]{2}" #68-0017-01 01    NAPLES25 SWM PENSANDO TAA 
    N25_SWM_HPE_FMT_ALL = r"{:s}|{:s}|{:s}|{:s}".format(N25_SWM_HPE_PN_FMT, N25_SWM_HPE_CLD_PN_FMT, N25_SWM_PEN_PN_FMT, N25_SWM_PEN_TAA_PN_FMT)

    N25_SWM_DEL_PN_FMT = r"68-0014-0[0-9]{1} [A-Z0-9]{2}"        #68-0014-01 00       NAPLES25 SWM DELL
    N25_SWM_DEL_FMT_ALL = r"{:s}".format(N25_SWM_DEL_PN_FMT)

    N25_SWM_833_PN_FMT = r"68-0019-0[0-9]{1} [A-Z0-9]{2}"        #68-0019-01 01       NAPLES25 SWM 833 PENSANDO
    N25_SWM_833_FMT_ALL = r"{:s}".format(N25_SWM_833_PN_FMT)

    N25_OCP_PEN_PN_FMT = r"68-0010-0[0-9]{1} [A-Z0-9]{2}"        #68-0010-xx       NAPLES25 OCP PENSANDO
    N25_OCP_HPE_PN_FMT = r"P37689-00[0-9]{1}"                 #P37689-001       NAPLES25 OCP HPE
    N25_OCP_HPE_CLD_PN_FMT = r"P41857-00[0-9]{1}"             #P41857-001       NAPLES25 OCP HPE CLOUD
    N25_OCP_DEL_PN_FMT = r"P18671-00[0-9]{1}"                 #P18671-001       NAPLES25 OCP DELL
    N25_OCP_PN_FMT_ALL = r"{:s}|{:s}|{:s}|{:s}".format(N25_OCP_PEN_PN_FMT,N25_OCP_HPE_PN_FMT, N25_OCP_HPE_CLD_PN_FMT, N25_OCP_DEL_PN_FMT)    

    FORIO_PN_FMT = r"68-0007-0[0-9]{1} [0-9]{2}"              #68-0007-01 01    FORIO
    FORIO_FMT_ALL = r"{:s}".format(FORIO_PN_FMT)

    VOMERO_PN_FMT = r"68-0009-0[0-9]{1} [0-9]{2}"             #68-0009-01 01    VOMERO
    VOMERO_FMT_ALL = r"{:s}".format(VOMERO_PN_FMT)

    VOMERO2_PN_FMT = r"68-0011-0[0-9]{1} [A-Z0-9]{2}"            #68-0011-01 01    VOMERO2
    VOMERO2_FMT_ALL = r"{:s}".format(VOMERO2_PN_FMT)

    ORTANO_PN_FMT = r"68-0015-0[0-9]{1} [A-Z0-9]{2}"             #68-0015-01 01    ORTANO
    ORTANO_FMT_ALL = r"{:s}".format(ORTANO_PN_FMT)


MFG_MTP_CPLD_IO_VERSION = "0x5"
MFG_MTP_CPLD_JTAG_VERSION = "0x3"
MFG_MTP_CPLD_IO_ELBA_VERSION = "0x1"
MFG_MTP_CPLD_JTAG_ELBA_VERSION = "0x1"

MFG_QSPI_TIMESTAMP = "05-21-2020"
MFG_GOLD_TIMESTAMP = "04-18-2020"
MFG_GOLD_NAPLES100_TIMESTAMP = "09-17-2019"
MFG_QSPI_VOMERO_TIMESTAMP = "02-03-2020"
MFG_GOLD_VOMERO2_TIMESTAMP = "07-01-2020"
MFG_QSPI_VOMERO2_TIMESTAMP = "06-18-2020"
MFG_QSPI_NAPLES25_HPE_OCP_TIMESTAMP = "11-18-2020"
MFG_GOLD_NAPLES25_HPE_OCP_TIMESTAMP = "01-09-2021"
MFG_QSPI_IBM_TIMESTAMP = "05-21-2020"                                         
MFG_GOLD_IBM_TIMESTAMP = "10-17-2020"
MFG_QSPI_NAPLES100HPE_TIMESTAMP = "08-24-2020"
MFG_GOLD_NAPLES100HPE_TIMESTAMP = "07-31-2020"
MFG_QSPI_NAPLES25_SWMDELL_TIMESTAMP = "08-24-2020"
MFG_QSPI_ORTANO_TIMESTAMP = "11-12-2020"
MFG_QSPI_NAPLES25_SWM_TIMESTAMP = "11-18-2020"
MFG_GOLD_NAPLES25_SWM_TIMESTAMP = "11-18-2020"
MFG_GOLD_ORTANO_TIMESTAMP = "11-08-2020"

DIAG_NIGHTLY_REPORT_ACCOUNT = "diag-nightly@pensando.io"
DIAG_NIGHTLY_REPORT_PASSWD = "diag-nightly"
DIAG_NIGHTLY_REPORT_RECEIPIENT = "ps-diag@pensando.io"
DIAG_OS_PROMPT_LIST = ["$", "#", ">"]
#DIAG_SSH_OPTIONS = " -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"
DIAG_SSH_OPTIONS = " -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"

MFG_VALID_FW_LIST = ["diagfw", "mainfwa", "mainfwb", "goldfw"]
MFG_VALID_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES25, NIC_Type.FORIO, NIC_Type.VOMERO, NIC_Type.VOMERO2, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25OCP, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.ORTANO, NIC_Type.ORTANO2]
MFG_PROTO_NIC_TYPE_LIST = [NIC_Type.FORIO]

MTP_REV02_CAPABLE_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.VOMERO2]
MTP_REV03_CAPABLE_NIC_TYPE_LIST = [NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP, NIC_Type.ORTANO, NIC_Type.ORTANO2]
MTP_REV04_CAPABLE_NIC_TYPE_LIST = [NIC_Type.NAPLES25, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25SWMDELL, NIC_Type.NAPLES25SWM833, NIC_Type.NAPLES25OCP, NIC_Type.ORTANO, NIC_Type.ORTANO2]

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
OCP_DELL_DISP_PN_FMT = r"Assembly Number +([A-Z0-9]{6}-[0-9]{3})"
HPESWM_DISP_ASSET_FMT = r"Asset Tag Type/Length.*0x(\w+)"

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

