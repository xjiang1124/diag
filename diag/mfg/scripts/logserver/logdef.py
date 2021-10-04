from enum import Enum

class KEY_WORD:
	## [2021-03-25_01-15-17] LOG: [MTP-113]: [NIC-05]: FLM21100017 DIAG TEST LV_PRE_CHECK NIC_CPLD PASS, DURATION 0:00:00
	NIC_DIAG_TEST_RSLT_RE = r"{:s} DIAG TEST (.*) (.*) (.*), DURATION"

	## [2021-05-28_22-58-11] ERR: [MTP-810]: [NIC-01]: FPN2120007C DIAG TEST MVL ACC, ERR MSG == [ERROR]   (mvl.go 41) Marvell Chip ID Failed.  Read 0x500f  Expect 0x1150  Mask=0xFFF0 == ERR MSG END
	NIC_DIAG_TEST_ERR_RE = r"{:s} DIAG TEST (.*) ERR MSG END"

	NIC_DIAG_TEST_FAILURE_RE = r"(\[{:s}-\d+\]:\s+?.*[Ff]ailed.*)"

	#NIC-09 ORTANO2 FLM21100052 NIC_DIAG_REGRESSION_TEST_FAIL
	NIC_DIAG_TEST_FINAL_RE = r"(NIC|UUT)-(\d+)\s(.*)\s{:s} NIC_DIAG_REGRESSION_TEST_(.*)"

	## [2021-03-23_16-26-57] LOG: [MTP-207]: [NIC-01]: CPLD1 image: naples200_Ortano2_rev3_2_03112021.bin
	## [2021-03-23_16-26-57] LOG: [MTP-207]: [NIC-01]: CPLD2 image: naples200_Ortano2_failsafe_rev3_2_03112021.bin
	NIC_DIAG_TEST_CPLD_IMAGE = r"NIC-(.*)]:\s(CPLD1|CPLD2|CPLD)\simage(\d)?:\s(.*)"

	## [2021-04-28_22-09-08] LOG: [MTP-208]: [NIC-04]: SN = FLM211000A6; MAC = 00-AE-CD-F6-0E-C8; PN = 68-0021-02 01
	## [2021-04-28_22-29-26] LOG: [MTP-221]: [NIC-02]: Verify NIC FRU Pass, sn=FLM211000AE, mac=00-AE-CD-F6-0F-10, pn=68-0021-02 01, date=042821
	NIC_DIAG_TEST_PN = r"{:s},\smac=(.*),\spn=(.*),\sdate=(.*)"
	#NIC_DIAG_TEST_PN = r"NIC-(.*)]:\sSN = (.*); MAC = (.*); PN = (68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"
	#NIC_DIAG_TEST_PN = r"\sPN = (68-[0-9]{4}-[0-9]{2} [0-9A-Z]{1,2})"

	## [2021-07-11_19-14-57] LOG: [MTP-669]: [NIC-01]: QSPI image: elba_diagfw_lacona_0.2-1-g9feba69_2021.06.22.tar
	NIC_DIAG_TEST_QSPI_IMAGE = r"NIC-(.*)]:\s(QSPI)\simage(\d)?:\s(.*)"

	## [2021-05-29_00-01-23] LOG: [MTP-626]: Try to connect MTP chassis
	#start_ts = libmfg_utils.timestamp_snapshot()

	## [2021-05-29_02-28-59] LOG: [MTP-626]: MTP Diag Regression Test Complete
	#stop_ts = libmfg_utils.timestamp_snapshot()

	#duration = str(stop_ts - start_ts)
	CHECKSTARTDATE = r"start=(\d{4}-\d{2}-\d{2})"

	FINDDATEANDTIME = r"\[(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\]"
	GETMTPINFORMATION = r"LOG: \[(\w+-\d+)\]:\s+==>\s?([\w\s\-]{0,100}):\s?(\w.*\w\)?)\s?"
	GETNICINFORMATION = r"\[(\w+-\d+)\]:\s\[\w+-(\d+)\]:\s==>\s?([\w\s\-]{0,100}):\s?(\w.*$)"
	GERNICFINALRESULT = r"\[(\w+-\d+)\]:\s\w+-(\d+)\s(\w+)\s(\w+)\sNIC_DIAG_REGRESSION_TEST_(\w+)"
	GETIMAGE = r"\[(\w+-\d+)\]:\s\[\w+-(\d+)\]:\s(\w.*image\d?):\s(\w.*$)"
	ERRORMESSAGESTART = r"Error Message Start"
	ERRORMESSAGEEND = r"Error Message End"
	GETELBAASICDIEID = r"ELBA\sASIC_DIE_ID:\s(.*)"
	FINDTEMPWITHTIMESTAMP = r"\[(\d{4}.*)]\sLOG:\s.*==>\sMTP\sInlet\stemp\s=\s(\d.*\d)\s<=="
	TEMPGROUPFROMMFGLOGSTART = r"(devmgr -dev FAN -status.*)"
	TEMPGROUPFROMMFGLOGEND = r"(diag@MTP)"
	GETEMPINFORMATION = r"\[(\d{4}\-\d{2}\-\d{2})-(\d{2}:\d{2}:\d{2}).*\]\s+(NAME|FAN)\s+(\w.*\w)"