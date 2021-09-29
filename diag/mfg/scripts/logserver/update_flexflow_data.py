#!/usr/bin/python2

import httplib
import re
import sys,os
from datetime import datetime
import yaml as yaml
import json

yamlfile = 'case_20210925_014916.yaml'

def main():
   start=datetime.now()

   DATA = load_cfg_from_yaml(yamlfile)
   #print(json.dumps(DATA, indent = 4 ))

   for eachdata in DATA:
      print(json.dumps(eachdata, indent = 4 ))
      get_flex_flow_data(eachdata)
      post_flex_flow_data(eachdata)
      get_flex_flow_data(eachdata)
      #sys.exit()

   timedifferentfromstart(start)

   return None

def timedifferentfromstart(start):
    difftime = datetime.now()-start
    print('Done Time: ', difftime)       
    print("How many seconds use?: {} seconds".format(difftime.total_seconds()))   

    return difftime

def load_cfg_from_yaml(yaml_file):
    if not os.path.exists(yaml_file):
        sys_exit("Yaml config file: " + yaml_file + " doesn't exist")

    with open(yaml_file, "r") as f:
        cfg = yaml.safe_load(f)

    if not cfg:
        sys_exit("Load yaml config files failed")

    if len(cfg) == 0:
        sys_exit("No content in yaml config files")

    return cfg

def get_flex_flow_data(DATA):

   xml = '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                \
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema"                               \
                   xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                    \
       <soap:Body>                                                                            \
           <GetUnitInfo xmlns="http://www.flextronics.com/FFTesterWS/">                      \
              <strRequest>&lt;?xml version="1.0" ?&gt;                                       \
              &lt;GetUnitInfo xmlns="urn:GetUnitInfo-schema" SerialNumber="{:s}" /&gt;    \
               </strRequest>                                                                  \
               <strStationName>{:s}</strStationName>                             \
               <strUserID>Tester01</strUserID>                                               \
               </GetUnitInfo>                                                                     \
       </soap:Body>                                                                           \
   </soap:Envelope>'.format(DATA["sn"],DATA["stage"])


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
   webservice.putheader("SOAPAction", FLX_PENANG_GET_UUT_INFO_SOAP)

   webservice.putheader("Content-length", "%d" % len(xml))
   webservice.endheaders()

   webservice.send(xml)

   statuscode, statusmessage, header = webservice.getreply()
   print(statuscode,statusmessage,header)
   resp = webservice.getfile().read()
   print(resp.replace("&gt;",">").replace("&lt;","<"))
   match = re.findall(FLX_GET_UUT_INFO_CODE_RE, resp)
   if match:
       print(match[0])
   else:
       print("################## GET UUT INF #######################")
       print resp
       print("################## GET UUT INF #######################")
       print "500"

def post_flex_flow_data(DATA):

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
             &lt;TEST NAME="DL CPLD_PROG" STATUS="PASS" VALUE="" DESCRIPTION="[{:s}]: [{:s}]: " FAILURECODE="PASS" /&gt;&#xD;   \
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
       </soap:Envelope>'.format(DATA["stage"],DATA["sn"],DATA["starttime"],DATA["testtime"],DATA["endtime"],DATA["result"],DATA["CARDTYPE"],DATA["testtime"],DATA["result"],DATA["TESTCHASSIS"],DATA["SLOT"])


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

if __name__ == "__main__":
   sys.exit(main())
