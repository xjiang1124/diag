from libdefs import NIC_Type

GLB_CFG_MFG_TEST_MODE = True

MFG_BYPASS_PSU_CHECK = True

# MFG release version control
class NIC_CPLD_Version:
    NAPLES100_VERSION = "0x9"
    NAPLES100_TIMESTAMP = "05-31"
    NAPLES100_SEC_VERSION = "0x89"
    NAPLES100_SEC_TIMESTAMP = "06-03"

    NAPLES25_VERSION = "0x4"
    NAPLES25_TIMESTAMP = "08-08"
    NAPLES25_SEC_VERSION = "0x84"
    NAPLES25_SEC_TIMESTAMP = "08-08"

    VOMERO_VERSION = "0x1"
    VOMERO_TIMESTAMP = "05-31"
    VOMERO_SEC_VERSION = "0x81"
    VOMERO_SEC_TIMESTAMP = "05-31"

    FORIO_VERSION = "0x4"
    FORIO_TIMESTAMP = "04-11"


# MFG release images
class MFG_IMAGE_FILES:
    MTP_AMD64_IMAGE = "image_amd64_10182019.tar"
    MTP_ARM64_IMAGE = "image_arm64_10182019.tar"

    NIC_DIAGFW_IMAGE = "naples_diagfw_08082019.tar"
    NIC_GOLDFW_IMAGE = "naples_goldfw_09182019.tar"

    NAPLES25_CPLD_IMAGE = "naples25_cpld_rev4_08082019.bin"
    NAPLES25_SEC_CPLD_IMAGE = "naples25_cpld_rev84_08082019.bin"

    NAPLES100_CPLD_IMAGE = "naples100_cpld_rev9_05312019.bin"
    NAPLES100_SEC_CPLD_IMAGE = "naples100_cpld_rev89_06032019.bin"


MFG_MTP_CPLD_IO_VERSION = "0x5"
MFG_MTP_CPLD_JTAG_VERSION = "0x3"

MFG_QSPI_TIMESTAMP = "08-08-2019"
MFG_GOLD_TIMESTAMP = "09-17-2019"

DIAG_NIGHTLY_REPORT_ACCOUNT = "diag-nightly@pensando.io"
DIAG_NIGHTLY_REPORT_PASSWD = "diag-nightly"
DIAG_NIGHTLY_REPORT_RECEIPIENT = "ps-diag@pensando.io"
DIAG_OS_PROMPT_LIST = ["$", "#", ">"]
DIAG_SSH_OPTIONS = " -o ServerAliveInterval=2 -o ServerAliveCountMax=15 -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=30'"

MFG_VALID_FW_LIST = ["diagfw", "mainfwa", "mainfwb", "goldfw"]
MFG_VALID_NIC_TYPE_LIST = [NIC_Type.NAPLES100, NIC_Type.NAPLES25, NIC_Type.FORIO, NIC_Type.VOMERO]
MFG_PROTO_NIC_TYPE_LIST = [NIC_Type.FORIO]

# please check the label specification
# FLM[Year, like 18, 19, 20][Week: 00-52][4 hex sequential digits]
FLX_MILPITAS_SN_FMT = "FLM\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
FLX_PENANG_SN_FMT = "FPN\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
HP_MILPITAS_SN_FMT = "5UP\d{1}[0-5]{1}\d{1}[0-9B-DF-HJ-NP-TV-Z]{4}"
HP_PENANG_SN_FMT = "2YU\d{1}[0-5]{1}\d{1}[0-9B-DF-HJ-NP-TV-Z]{4}"
NAPLES_SN_FMT = r"{:s}|{:s}".format(FLX_MILPITAS_SN_FMT,FLX_PENANG_SN_FMT)
HP_SN_FMT = r"{:s}|{:s}".format(HP_MILPITAS_SN_FMT, HP_PENANG_SN_FMT)
FLX_MILPITAS_BUILD_SN_FMT = r"{:s}|{:s}".format(FLX_MILPITAS_SN_FMT, HP_MILPITAS_SN_FMT)
FLX_PENANG_BUILD_SN_FMT = r"{:s}|{:s}".format(FLX_PENANG_SN_FMT, HP_PENANG_SN_FMT)
NAPLES_MAC_FMT = r"00AECD[A-F0-9]{6}"
NAPLES_PN_FMT = r"68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2}$"
HP_PN_FMT = r"[A-Z0-9]{6}-[0-9]{3}$"
NAPLES_DISP_SN_FMT = r"Serial Number +({:s}|{:s})".format(FLX_MILPITAS_SN_FMT,FLX_PENANG_SN_FMT)
HP_DISP_SN_FMT = r"HPE Serial Number +({:s}|{:s})".format(HP_MILPITAS_SN_FMT,HP_PENANG_SN_FMT)
NAPLES_DISP_MAC_FMT = r"MAC Address Base +(00-[a,A][e,E]-[c,C][d,D]-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2})"
NAPLES_DISP_DATE_FMT = r"Manufacturing Date/Time.*(\d{2}/\d{2}/\d{2})"
NAPLES_DISP_PN_FMT = r"Part Number +(68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
HP_DISP_PN_FMT = r"HPE Product Number +([A-Z0-9]{6}-[0-9]{3})"
NIC_MGMT_USERNAME = "root"
NIC_MGMT_PASSWORD = "pen123"

MTP_INTERNAL_MGMT_IP_ADDR = "10.1.1.100"
MTP_INTERNAL_MGMT_NETMASK = "255.255.255.0"

FLX_WEBSERVER = "10.20.33.140"
FLX_API_URL = "/Pensando/fftester20.asmx"
FLX_GET_UUT_INFO_SOAP = "http:/www.flextronics.com/FFTester20/GetUnitInfo"
FLX_SAVE_UUT_RSLT_SOAP = "http:/www.flextronics.com/FFTester20/SaveResult"

FLX_PENANG_WEBSERVER = "172.30.178.5"
FLX_PENANG_API_URL = "/FFTesterWS_PENSANDO/FFTesterWS.asmx"
FLX_PENANG_GET_UUT_INFO_SOAP = "http://www.flextronics.com/FFTesterWS/GetUnitInfo"
FLX_PENANG_SAVE_UUT_RSLT_SOAP = "http://www.flextronics.com/FFTesterWS/SaveResult"

FLX_GET_UUT_INFO_CODE_RE = r"<GetUnitInfoResult>(\d+)</GetUnitInfoResult>"
FLX_SAVE_UUT_RSLT_CODE_RE = r"<SaveResultResult>(\d+)</SaveResultResult>"

FLX_GET_UUT_INFO_XML_HEAD = '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
                                            xmlns:xsd="http://www.w3.org/2001/XMLSchema" \
                                            xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"> \
                                 <soap:Body> \
                                     <GetUnitInfo xmlns="http:/www.flextronics.com/FFTester20">'
FLX_GET_UUT_INFO_ENTRY_FMT =             '<strRequest>&lt;?xml version="1.0" ?&gt; \
                                              &lt;GetUnitInfo xmlns="urn:GetUnitInfo-schema" SerialNumber="{:s}" /&gt; \
                                          </strRequest> \
                                          <strStationName>{:s}</strStationName> \
                                          <strUserID>Admin</strUserID>'
FLX_GET_UUT_INFO_XML_TAIL =         '</GetUnitInfo> \
                                 </soap:Body> \
                             </soap:Envelope>'


FLX_SAVE_UUT_RSLT_XML_HEAD = '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
                                             xmlns:xsd="http://www.w3.org/2001/XMLSchema" \
                                             xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"> \
                                  <soap:Body> \
                                      <SaveResult xmlns="http:/www.flextronics.com/FFTester20"> \
                                          <strXMLResultText>'
FLX_SAVE_UUT_RSLT_ENTRY_FMT =                '&lt;BATCH&gt;&#xD; \
                                              &lt;FACTORY TESTER="{:s}" USER="admin" /&gt;&#xD; \
                                              &lt;PANEL&gt;&#xD; \
                                              &lt;DUT ID="{:s}" SOCKET="1" TIMESTAMP="{:s}" TESTTIME="{:s}" ENDTIME="{:s}" STATUS="{:s}"&gt;&#xD; \
                                              &lt;GROUP NAME="{:s}" GROUPINDEX="1" LOOPINDEX="-1" TYPE="PassFailTest" Remark="Comment" TOTALTIME="{:s}" STATUS="{:s}"&gt;&#xD;'
FLX_SAVE_UUT_TEST_RSLT_FMT =                 '&lt;TEST NAME="{:s}" STATUS="{:s}" VALUE="{:s}" DESCRIPTION="{:s}" FAILURECODE="{:s}" /&gt;&#xD;'
FLX_SAVE_UUT_RSLT_ENTRY_END =                '&lt;/GROUP&gt;&#xD; \
                                              &lt;/DUT&gt;&#xD; \
                                              &lt;/PANEL&gt;&#xD; \
                                              &lt;/BATCH&gt;'
FLX_SAVE_UUT_RSLT_XML_TAIL =             '</strXMLResultText> \
                                              <strTestRefNo>Test123</strTestRefNo> \
                                      </SaveResult> \
                                  </soap:Body> \
                              </soap:Envelope>'


