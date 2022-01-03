import httplib
import re
import sys,os

sn = "FPN21490002"

#xml = '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                                      xmlns:xsd="http://www.w3.org/2001/XMLSchema"                                               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                        <soap:Body>                                                                                    <GetUnitInfo xmlns="http://www.flextronics.com/FFTesterWS/"><strRequest>&lt;?xml version="1.0" ?&gt;                                                      &lt;GetUnitInfo xmlns="urn:GetUnitInfo-schema" SerialNumber="{}" /&gt;                </strRequest>                                                                              <strStationName>PSO-DOWNLOAD_AUTO</strStationName>                                                      <strUserID>Tester01</strUserID></GetUnitInfo>                                                                         </soap:Body>                                                                           </soap:Envelope>'.format(sn)

xml = '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                \
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"                               \
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                    \
    <soap:Body>                                                                            \
        <GetUnitInfo xmlns="http://www.flextronics.com/FFTesterWS/">                      \
           <strRequest>&lt;?xml version="1.0" ?&gt;                                       \
           &lt;GetUnitInfo xmlns="urn:GetUnitInfo-schema" SerialNumber="{:s}" /&gt;    \
            </strRequest>                                                                  \
            <strStationName>PSO-DOWNLOAD_AUTO</strStationName>                             \
            <strUserID>Tester01</strUserID>                                               \
            </GetUnitInfo>                                                                     \
    </soap:Body>                                                                           \
</soap:Envelope>'.format(sn)

#http://10.206.9.65/FFTesterWS_PENSANDO/FFTesterWS.asmx
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
webservice.putheader("SOAPAction", FLX_PENANG_GET_UUT_INFO_SOAP)

webservice.putheader("Content-length", "%d" % len(xml))
webservice.endheaders()

webservice.send(xml)

statuscode, statusmessage, header = webservice.getreply()
print(statuscode,statusmessage,header)
resp = webservice.getfile().read()
print(resp.replace("&gt;",">").replace("&lt;","<"))
match = re.findall(FLX_GET_UUT_INFO_CODE_RE, resp)

print resp

if match:
    print(match[0])
else:
    print("################## GET UUT INF #######################")
    print resp
    print("################## GET UUT INF #######################")
    print "500"
