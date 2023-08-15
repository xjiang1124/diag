#!/usr/bin/python3

import requests
import os, sys

BASE = "http://192.168.66.33:5000/"

xml = '''<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"                                      xmlns:xsd="http://www.w3.org/2001/XMLSchema"                                               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body>
<SaveResult xmlns="http://www.flextronics.com/FFTesterWS/">
<strXMLResultText>
&lt;BATCH&gt;&#xD;
&lt;FACTORY TESTER="PSO-P2C_AUTO" USER="tester01" /&gt;&#xD;
&lt;PANEL&gt;&#xD;
&lt;DUT ID="FPA22200198" SOCKET="1" TIMESTAMP="2023-06-27 13:16:32" TESTTIME="0:09:56" ENDTIME="2023-06-27 13:26:28" STATUS="PASS"&gt;&#xD;
&lt;EXTRA PSU_1="S0402000013" OCP_ADAPTER=""  /&gt;&#xD;
&lt;GROUP NAME="ORTANO2" GROUPINDEX="1" LOOPINDEX="-1" TYPE="PassFailTest" Remark="Comment" TOTALTIME="0:09:56" STATUS="PASS"&gt;&#xD;
&lt;TEST NAME="MAC-ADD" STATUS="PASS" VALUE="04-90-81-32-5E-60" DESCRIPTION="FRU MAC-ADD" FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="PART-NO" STATUS="PASS" VALUE="68-0026-01 A0" DESCRIPTION="FRU PART-NO" FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="P2C-CPLD_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="P2C-NIC_BOOT_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="P2C-CPLD_VERIFY" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="P2C-QSPI_VERIFY" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="DIAG_INIT-NIC_PARA_MGMT_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="DIAG_INIT-NIC_BOOT_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="DIAG_INIT-MAC_VALIDATE" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="DIAG_INIT-START_DIAG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="DIAG_INIT-CPLD_DIAG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="DIAG_INIT-NIC_FRU_INIT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="DIAG_INIT-NIC_VMARG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="PRE_CHECK-NIC_TYPE" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="PRE_CHECK-NIC_POWER" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="PRE_CHECK-NIC_JTAG" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="PRE_CHECK-NIC_STATUS" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="PRE_CHECK-NIC_DIAG_BOOT" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;TEST NAME="PRE_CHECK-NIC_CPLD" STATUS="PASS" VALUE="" DESCRIPTION="[MTP-061]: [NIC-06]: " FAILURECODE="PASS" /&gt;&#xD;
&lt;/GROUP&gt;&#xD;
&lt;/DUT&gt;&#xD;
&lt;/PANEL&gt;&#xD;
&lt;/BATCH&gt;</strXMLResultText>
<strTestRefNo>
Test123</strTestRefNo>
</SaveResult>
</soap:Body>
</soap:Envelope>'''

ind1 = xml.find('DUT ID="')+8
ind2 = xml.find('" SOCKET=')
ind3 = xml.find('FACTORY TESTER="')+16
ind4 = xml.find('" USER=')

if(ind1 ==-1 or ind2 == -1 or ind3 == -1 or ind4 == -1):
    print('400, missing field')
    sys.exit(-1)

sn = xml[ind1:ind2]
stage = xml[ind3:ind4]

response = requests.get(BASE + "UUT/" + sn +"/" + stage)
print(response.text)

