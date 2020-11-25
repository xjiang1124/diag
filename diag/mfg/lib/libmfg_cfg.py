from libdefs import NIC_Type

GLB_CFG_MFG_TEST_MODE = True

MFG_BYPASS_PSU_CHECK = True

# MFG release version control
class NIC_CPLD_Version:
    NAPLES100_VERSION = "0x9"
    NAPLES100_TIMESTAMP = "05-31"
    NAPLES100_SEC_VERSION = "0x89"
    NAPLES100_SEC_TIMESTAMP = "06-03"
    
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

    NAPLES25SWMDELL_VERSION = "0x2"
    NAPLES25SWMDELL_MINOR_VERSION = "00"
    NAPLES25SWMDELL_SEC_VERSION = "0x82"
    NAPLES25SWMDELL_SEC_TIMESTAMP = "00"

    NAPLES25OCP_VERSION = "0x3"
    NAPLES25OCP_TIMESTAMP = "09-22"
    NAPLES25OCP_SEC_VERSION = "0x83"
    NAPLES25OCP_SEC_TIMESTAMP = "09-22"
    
    ORTANO_VERSION = "0x2"      #major rev
    ORTANO_TIMESTAMP = "0x08"    #minor rev
    ORTANO_SEC_VERSION = ""
    ORTANO_SEC_TIMESTAMP = ""


# MFG release images
class MFG_IMAGE_FILES:
    MTP_AMD64_IMAGE = "image_amd64_10222020.tar"
    MTP_ARM64_IMAGE = "image_arm64_10222020.tar"
    
    MTP_PENCTL_IMAGE = "penctl.linux.0915"
    MTP_PENCTL_TOKEN = "penctl.token"
    
    NIC_DIAGFW_IMAGE = "naples_diagfw_05212020.tar"
    NIC_GOLDFW_IMAGE = "naples_goldfw_1.3.1-E-19_0717.tar"
    NIC_GOLDFW_IMAGE_SWM = "naples_goldfw_1.3.1-E-19_0717.tar"
    NIC_DIAGFW_IMAGE_HPE_OCP = "naples_diagfw_1.3.1-E-27.tar"
    NIC_GOLDFW_IMAGE_HPE_OCP = "naples_goldfw_1.3.1-E-28_0731.tar"
    NIC_DIAGFW_IMAGE_SWMDELL = "naples_diagfw_1.3.1-E-31_0824.tar"
    NIC_GOLDFW_IMAGE_SWMDELL = "naples_goldfw_1.3.1-E-31_0824.tar"
    NIC_GOLDFW_IMAGE_IBM = "naples_goldfw1.3.1-E-20_0514.tar"
    NIC_GOLDFW_IMAGE_HPE = "naples_goldfw1_1.3.1-E-28_0731.tar"
    NIC_DIAGFW_IMAGE_HPE_NAPLES100 = "naples_diagfw_1.3.1-E-31_0824.tar"
    NIC_GOLDFW_IMAGE_HPE_NAPLES100 = "naples_goldfw_1.3.1-E-28_0731.tar"
    NIC_DIAGFW_IMAGE_VOMERO2 = "naples_diagfw_w_uboot_1.3.1-E-26_0620.tar"
    NIC_GOLDFW_IMAGE_VOMERO2 = "naples_minigoldfw_1.7.4-C-7_0702.tar"
    NIC_DIAGFW_IMAGE_NAPLES100 = "naples_diagfw_12172019.tar"
    NIC_GOLDFW_IMAGE_NAPLES100 = "naples_goldfw_09182019.tar"
    NIC_DIAGFW_IMAGE_ORTANO = "elba_diagfw_1.17.0-26-5_1112.tar"
    NIC_GOLDFW_IMAGE_ORTANO = "naples_goldfw_1.17.0-11-2_1118.tar"

    NAPLES25_CPLD_IMAGE = "naples25_rev9_06222020.bin"
    NAPLES25_SEC_CPLD_IMAGE = "naples25_rev89_06172020.bin"

    NAPLES25SWM_CPLD_IMAGE = "naples25_swm_rev9_04142020.bin"
    NAPLES25SWM_SEC_CPLD_IMAGE = "naples25_swm_rev89_04142020.bin"

    NAPLES25SWMDELL_CPLD_IMAGE = "naples25_swmdell_rev2_08202020.bin"
    NAPLES25SWMDELL_SEC_CPLD_IMAGE = "naples25_swmdell_rev82_08202020.bin"

    NAPLES25_HPE_OCP_CPLD_IMAGE = "naples25_ocp_rev03_09222020.bin"
    NAPLES25_HPE_OCP_SEC_CPLD_IMAGE = "naples25_ocp_rev83_09222020.bin"
    
    NAPLES100_CPLD_IMAGE = "naples100_cpld_rev9_05312019.bin"
    NAPLES100_SEC_CPLD_IMAGE = "naples100_cpld_rev89_06032019.bin"
    
    NAPLES100IBM_CPLD_IMAGE = "naples100_ibm_rev3_09082020.bin"
    NAPLES100IBM_SEC_CPLD_IMAGE = "naples100_ibm_rev83_09082020.bin"
    
    NAPLES100HPE_CPLD_IMAGE = "naples100_hpe_rev1_07222020.bin"
    NAPLES100HPE_SEC_CPLD_IMAGE = "naples100_hpe_rev81_07222020.bin"
 

    VOMERO_CPLD_IMAGE = "vomero_cpld_rev4_02072020.bin"
    VOMERO_SEC_CPLD_IMAGE = "vomero_cpld_rev84_02102020.bin"
    VOMERO2_CPLD_IMAGE = "vomero2_rev5_07242020.bin"
    VOMERO2_SEC_CPLD_IMAGE = "vomero2_rev85_07242020.bin"

    ORTANO_CPLD_IMAGE = "ortano_rev28_cfg0.bin"
    ORTANO_SEC_CPLD_IMAGE = "" 

class PART_NUMBERS_MATCH:
    N100_PEN_PN_FMT = r"68-0003-0[0-9]{1} [A-Z0-9]{2}"   #68-0003-01 01    PENSANDO
    N100_NET_PN_FMT = r"111-04635"                     #111-04635        NETAPP
    N100_PN_FMT_ALL = r"{:s}|{:s}".format(N100_PEN_PN_FMT,N100_NET_PN_FMT)

    N100_IBM_PN_FMT = r"68-0013-0[0-9]{1} [0-9]{2}"   #68-0013-01 03       IBM
    N100_IBM_FMT_ALL = r"{:s}".format(N100_IBM_PN_FMT)
    exp_pn = N100_IBM_FMT_ALL

    N100_HPE_PN_FMT = r"P37692-00[0-9]{1}"            #P37692-001       HPE 
    N100_HPE_FMT_ALL = r"{:s}".format(N100_HPE_PN_FMT)

    N25_PEN_PN_FMT = r"68-0005-0[0-9]{1} [A-Z0-9]{2}" #68-0005-03 01    PENSANDO
    N25_HPE_PN_FMT = r"P18669-00[0-9]{1}"             #P18669-001       HPE
    N25_EQI_PN_FMT = r"68-0008-0[0-9]{1} [0-9]{2}"    #68-0008-xx yy    EQUINIX
    N25_PN_FMT_ALL = r"{:s}|{:s}|{:s}".format(N25_PEN_PN_FMT,N25_HPE_PN_FMT,N25_EQI_PN_FMT)

    N25_SWM_HPE_PN_FMT = r"P26968-00[0-9]{1}"            #P26968-001       HPE SWM
    N25_SWM_HPE_FMT_ALL = r"{:s}".format(N25_SWM_HPE_PN_FMT)

    N25_SWM_DEL_PN_FMT = r"68-0014-0[0-9]{1} [0-9]{2}"   #68-0014-01 00       DELL SWM
    N25_SWM_DEL_FMT_ALL = r"{:s}".format(N25_SWM_DEL_PN_FMT)

    N25_OCP_PEN_PN_FMT = r"68-0010-0[0-9]{1} [0-9]{2}"   #68-0010-xx       PENSANDO
    N25_OCP_HPE_PN_FMT = r"P37689-00[0-9]{1}"            #P37689-001       HPE
    N25_OCP_DEL_PN_FMT = r"P18671-00[0-9]{1}"            #P18671-001       DELL
    N25_OCP_PN_FMT_ALL = r"{:s}|{:s}|{:s}".format(N25_OCP_PEN_PN_FMT,N25_OCP_HPE_PN_FMT,N25_OCP_DEL_PN_FMT)    

    FORIO_PN_FMT = r"68-0007-0[0-9]{1} [0-9]{2}"   #68-0007-01 01
    FORIO_FMT_ALL = r"{:s}".format(FORIO_PN_FMT)

    VOMERO_PN_FMT = r"68-0009-0[0-9]{1} [0-9]{2}"   #68-0009-01 01
    VOMERO_MT_ALL = r"{:s}".format(VOMERO_PN_FMT)

    VOMERO2_PN_FMT = r"68-0011-0[0-9]{1} [0-9]{2}"   #68-0011-01 01
    VOMERO2_MT_ALL = r"{:s}".format(VOMERO2_PN_FMT)


MFG_MTP_CPLD_IO_VERSION = "0x1" #0x5
MFG_MTP_CPLD_JTAG_VERSION = "0x1" #"0x3"

MFG_QSPI_TIMESTAMP = "05-21-2020"
MFG_GOLD_TIMESTAMP = "04-18-2020"
MFG_GOLD_NAPLES100_TIMESTAMP = "09-17-2019"
MFG_QSPI_VOMERO_TIMESTAMP = "02-03-2020"
MFG_GOLD_VOMERO2_TIMESTAMP = "07-01-2020"
MFG_QSPI_VOMERO2_TIMESTAMP = "06-18-2020"
MFG_QSPI_NAPLES25_HPE_OCP_TIMESTAMP = "07-24-2020"
MFG_GOLD_NAPLES25_HPE_OCP_TIMESTAMP = "07-31-2020"
MFG_QSPI_IBM_TIMESTAMP = "05-21-2020"                                         
MFG_GOLD_IBM_TIMESTAMP = "05-12-2020"
MFG_QSPI_NAPLES100HPE_TIMESTAMP = "08-24-2020"
MFG_GOLD_NAPLES100HPE_TIMESTAMP = "07-31-2020"
MFG_QSPI_NAPLES25_SWMDELL_TIMESTAMP = "08-24-2020"
MFG_QSPI_ORTANO_TIMESTAMP = "11-12-2020"

DIAG_NIGHTLY_REPORT_ACCOUNT = "diag-nightly@pensando.io"
DIAG_NIGHTLY_REPORT_PASSWD = "diag-nightly"
DIAG_NIGHTLY_REPORT_RECEIPIENT = "ps-diag@pensando.io"
DIAG_OS_PROMPT_LIST = ["$", "#", ">"]
#DIAG_SSH_OPTIONS = " -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"
DIAG_SSH_OPTIONS = " -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"

MFG_VALID_FW_LIST = ["diagfw", "mainfwa", "mainfwb", "goldfw"]
MFG_VALID_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES25, NIC_Type.FORIO, NIC_Type.VOMERO, NIC_Type.VOMERO2, NIC_Type.NAPLES25SWM, NIC_Type.NAPLES25OCP, NIC_Type.NAPLES100IBM, NIC_Type.NAPLES100HPE, NIC_Type.NAPLES25SWMDELL, NIC_Type.ORTANO]
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
DELLSWM_DISP_ASSEMBLY_FMT = r"Assembly Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{2})"
VOMERO2_DISP_ASSEMBLY_FMT = r"Assembly Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
ORTANO_DISP_ASSEMBLY_FMT = VOMERO2_DISP_ASSEMBLY_FMT
NAPLES_DISP_PN_FMT = r"Part Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
#NAPLES_DISP_PN_FMT = r"(Part|Assembly) Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
HP_DISP_PN_FMT = r"HPE Product Number +([A-Z0-9]{6}-[0-9]{3})"
HP_SWM_DISP_PN_FMT = r"Part Number +([A-Z0-9]{6}-[0-9]{3})"
ALOM_DISP_BIA_PN_FMT = r"Part Number +([A-Z0-9]{6}-[0-9]{3})"
ALOM_DISP_PIA_PN_FMT = r"HPE Product Number +([A-Z0-9]{6}-B[0-9]{2})"
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

