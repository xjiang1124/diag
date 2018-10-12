# No valid content in the Fru
MFG_CFG_NIC_FRU_VALID = False
DIAG_NIGHTLY_REPORT_ACCOUNT = "diag-nightly@pensando.io"
DIAG_NIGHTLY_REPORT_PASSWD = "diag-nightly"
DIAG_OS_PROMPT_LIST = ["$", "#", ">"]
DIAG_SSH_OPTIONS = " -o 'StrictHostKeyChecking=no' -o 'UserKnownHostsFile=/dev/null'"

# please check the label specification
# FL[M,Z,G][Year, like 18, 19, 20][Week: 00-52][4 hex sequential digits]
NAPLES_SN_FMT = r"FL[M,Z,G]\d{2}[0-5]{1}\d{1}[0-9A-F]{4}"
NAPLES_MAC_FMT = r"00AECD[A-F0-9]+$"

FLX_WEBSERVER = "10.20.33.140"
FLX_API_URL = "/Pensando/fftester20.asmx"
FLX_GET_UUT_INFO_SOAP = "http:/www.flextronics.com/FFTester20/GetUnitInfo"
FLX_SAVE_UUT_RSLT_SOAP = "http:/www.flextronics.com/FFTester20/SaveResult"
FLX_GET_UUT_INFO_CODE_RE = R"<GetUnitInfoResult>(\d+)</GetUnitInfoResult>"
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
                                              &lt;GROUP NAME="Board" GROUPINDEX="1" LOOPINDEX="-1" TYPE="PassFailTest" Remark="Comment" TOTALTIME="{:s}" STATUS="{:s}"&gt;&#xD;'
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


