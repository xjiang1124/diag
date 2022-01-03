import httplib
import re
import sys,os
import datetime

sn = "FPN20470021"
#sn = "FPN203700AA"
stage = "PSO-DOWNLOAD_AUTO"


xml = '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                      \
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"                               \
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                    \
   <soap:Body>                                                                             \
      <SaveResult xmlns="http://www.flextronics.com/FFTesterWS/">                          \
         <strXMLResultText>\
         \
         &lt;BATCH&gt;&#xD;                                                               \
          &lt;FACTORY TESTER="{:s}" USER="tester01" /&gt;&#xD;                             \
          &lt;PANEL&gt;&#xD;                                                               \
          &lt;DUT ID="{:s}" SOCKET="1" TIMESTAMP="{:s}" TESTTIME="{:s}" ENDTIME="{:s}" STATUS="{:s}"&gt;&#xD; \
          &lt;GROUP NAME="{:s}" GROUPINDEX="1" LOOPINDEX="-1" TYPE="PassFailTest" Remark="Comment" TOTALTIME="{:s}" STATUS="{:s}"&gt;&#xD; \
          \
          &lt;TEST NAME="DL-NIC_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-654]: [NIC-07]: " FAILURECODE="PASS" /&gt;&#xD;   \
          \
          &lt;/GROUP&gt;&#xD;                                                              \
          &lt;/DUT&gt;&#xD;                                                                \
          &lt;/PANEL&gt;&#xD;                                                              \
          &lt;/BATCH&gt;    \
          \
          </strXMLResultText>                                                               \
                   <strTestRefNo>Test123</strTestRefNo>                                              \
                        </SaveResult>                                                                         \
                           </soap:Body>                                                                            \
    </soap:Envelope>'.format(stage,sn,'2020-12-15_18-00-00','00:20:00','2020-12-15_18-20-00',"PASS","NAPLES100",'00:20:00',"PASS")


FLX_PENANG_WEBSERVER = "10.206.9.16"
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
if match:
    print(match[0])
else:
    print("################## GET UUT INF #######################")
    print resp
    print("################## GET UUT INF #######################")
    print "500"
