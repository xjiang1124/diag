#!/usr/bin/python3

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


print(xml)