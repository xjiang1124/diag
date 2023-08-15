import httplib
import re
import sys,os
import os
import sys
import re
from collections import namedtuple, OrderedDict
import argparse
import copy
import json


print('Paste the xml here\n')
xml = input()

print('Input 0 for get, 1 for post\n')
get = input()

def checkXML():

    if(get=='0'):
        ind1 = xml.find('<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                \
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"                               \
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                    \
    <soap:Body>                                                                            \
        <GetUnitInfo xmlns="http://www.flextronics.com/FFTesterWS/">                      \
           <strRequest>&lt;?xml version="1.0" ?&gt;                                       \
           &lt;GetUnitInfo xmlns="urn:GetUnitInfo-schema" SerialNumber="')
        ind2 = xml.find('" /&gt;    \
            </strRequest>                                                                  \
            <strStationName>')
        ind3 = xml.find('}</strStationName>                             \
            <strUserID>Tester01</strUserID>                                               \
            </GetUnitInfo>                                                                     \
    </soap:Body>                                                                           \
</soap:Envelope>')
        if(ind1 < ind2 and ind2 < ind3):
            return 200
        return 500

    elif (get == '1'):
        ind1 = xml.find('<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                      \
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"                               \
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">                    \
   <soap:Body>                                                                             \
      <SaveResult xmlns="http://www.flextronics.com/FFTesterWS/">                          \
         <strXMLResultText>\
         \
         &lt;BATCH&gt;&#xD;                                                               \
          &lt;FACTORY TESTER="')
        ind2 = xml.find('" USER="tester01" /&gt;&#xD;                             \
          &lt;PANEL&gt;&#xD;                                                               \
          &lt;DUT ID="')
        ind3 = xml.find('}" SOCKET="1" TIMESTAMP="')
        ind4 = xml.find('" TESTTIME="')
        ind5 = xml.find('" ENDTIME="')
        ind6 = xml.find('" STATUS="')
        ind7 = xml.find('"&gt;&#xD; \
          &lt;GROUP NAME="')
        ind8 = xml.find('" GROUPINDEX="1" LOOPINDEX="-1" TYPE="PassFailTest" Remark="Comment" TOTALTIME="')
        ind9 = xml.find('" STATUS="')
        ind10 = xml.find('"&gt;&#xD; \
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
    </soap:Envelope>')
        if(ind1 < ind2 and ind2 < ind3 and ind3 < in4 and ind4 < ind5 and ind5< ind6 and ind6 < ind7 and ind7 < ind8 and ind8 < ind9 and ind9 < ind10):
            return 200
        return 500

    else:
        return 500


print(checkXML())

