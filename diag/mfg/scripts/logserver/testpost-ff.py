import httplib
import re
import sys,os
import datetime

sn = "FPN21490002"


xml = '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                                      xmlns:xsd="http://www.w3.org/2001/XMLSchema"                                               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                       <soap:Body>                                                                                   <SaveResult xmlns="http://www.flextronics.com/FFTesterWS/">                                   <strXMLResultText>&lt;BATCH&gt;&#xD;                                                                         &lt;FACTORY TESTER="PSO-DOWNLOAD_AUTO" USER="tester01" /&gt;&#xD;                                       &lt;PANEL&gt;&#xD;                                                                         &lt;DUT ID="{}" SOCKET="1" TIMESTAMP="2021-12-05 05:45:27" TESTTIME="1:54:15" ENDTIME="2021-12-05 07:39:42" STATUS="PASS"&gt;&#xD;           &lt;GROUP NAME="ORTANO2" GROUPINDEX="1" LOOPINDEX="-1" TYPE="PassFailTest" Remark="Comment" TOTALTIME="1:54:15" STATUS="PASS"&gt;&#xD;&lt;TEST NAME="MAC-ADD" STATUS="PASS" VALUE="00-AE-CD-1B-03-60" DESCRIPTION="FRU MAC-ADD" FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="PART-NO" STATUS="PASS" VALUE="68-0015-02 C0" DESCRIPTION="FRU PART-NO" FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-CONSOLE_BOOT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_BOOT_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-NIC_MGMT_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_MGMT_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-SET_PSLC" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-NIC_MGMT_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-NIC_BOOT_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-MAC_VALIDATE" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-START_DIAG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-CPLD_DIAG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-NIC_FRU_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-SCAN_VERIFY" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_POWER" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_TYPE" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_PRSNT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_DIAG_BOOT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-FIX_VRM" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-FRU_PROG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-QSPI_PROG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-CPLD_PROG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-FSAFE_CPLD_PROG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-FEA_PROG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-CPLD_REF" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-CPLD_BOOT_CHECK" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_PWRCYC" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-NIC_PARA_MGMT_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-NIC_BOOT_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-MAC_VALIDATE" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-START_DIAG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-CPLD_DIAG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DIAG_INIT-NIC_FRU_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_POWER" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_PRSNT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-NIC_DIAG_BOOT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-FRU_VERIFY" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-CPLD_VERIFY" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-FEA_VERIFY" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-QSPI_VERIFY" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-BOARD_CONFIG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;TEST NAME="DL-AVS_SET" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-718]: [NIC-08]: " FAILURECODE="PASS" /&gt;&#xD;&lt;/GROUP&gt;&#xD;                                                                        &lt;/DUT&gt;&#xD;                                                                          &lt;/PANEL&gt;&#xD;                                                                        &lt;/BATCH&gt;</strXMLResultText>                                                                        <strTestRefNo>Test123</strTestRefNo>                                                   </SaveResult>                                                                            </soap:Body>      '.format(sn)


FLX_PENANG_WEBSERVER = "10.206.9.65"
FLX_PENANG_API_URL = "/FFTesterWS_PENSANDO/FFTesterWS.asmx"
FLX_PENANG_GET_UUT_INFO_SOAP = "http://www.flextronics.com/FFTesterWS/GetUnitInfo"
FLX_PENANG_SAVE_UUT_RSLT_SOAP = "http://www.flextronics.com/FFTesterWS/SaveResult"

FLX_GET_UUT_INFO_CODE_RE = r"<GetUnitInfoResult>(\d+)</GetUnitInfoResult>"
FLX_SAVE_UUT_RSLT_CODE_RE = r"<SaveResultResult>(\d+)</SaveResultResult>"


webservice = httplib.HTTP(FLX_PENANG_WEBSERVER)
#webservice.putrequest("GET", FLX_PENANG_API_URL+"?op=GetUnitInfo")
webservice.putrequest("POST", FLX_PENANG_API_URL)
webservice.putheader("Content-Type", "text/xml")
webservice.putheader("SOAPAction", FLX_PENANG_SAVE_UUT_RSLT_SOAP)

webservice.putheader("Content-length", "%d" % len(xml))
webservice.endheaders()

webservice.send(xml)
print(xml)

statuscode, statusmessage, header = webservice.getreply()
print(statuscode,statusmessage,header)
resp = webservice.getfile().read()
print(resp.replace("&gt;",">").replace("&lt;","<"))
match = re.findall(FLX_SAVE_UUT_RSLT_CODE_RE, resp)

print resp

if match:
    print(match[0])
else:
    print("################## GET UUT INF #######################")
    print resp
    print("################## GET UUT INF #######################")
    print "500"
