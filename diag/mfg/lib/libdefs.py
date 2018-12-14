from enum import Enum

class NIC_Type:
    NAPLES100 = "NAPLES100"
    NAPLES25 = "NAPLES25"
    UNKNOWN = "Unknown"


class Env_Cond(Enum):
    LTLV = "LTLV"
    LTNV = "LTNV"
    LTHV = "LTHV"
    NTLV = "NTLV"
    NTNV = "NTNV"
    NTHV = "NTHV"
    HTLV = "HTLV"
    HTNV = "HTNV"
    HTHV = "HTHV"
    
    def __str__(self):
        return self.value


class NIC_Status:
    NIC_STA_POWEROFF = 0
    NIC_STA_POWERUP = 1
    NIC_STA_TERM_FAIL = 2
    NIC_STA_MGMT_FAIL = 3
    NIC_STA_DIAG_FAIL = 4
    NIC_STA_OK = 10
    NIC_STA_MAX = 11


class MTP_Status:
    MTP_STA_POWEROFF = 0
    MTP_STA_POWERUP = 1
    MTP_STA_ENV_FAIL = 2
    MTP_STA_MGMT_FAIL = 3
    MTP_STA_READY = 10
    MTP_STA_MAX = 11
    

class NIC_Port_Mask:
    NIC_PORT1_MASK = (0x1 << 0)
    NIC_PORT2_MASK = (0x1 << 1)
    NIC_MGMT_MASK =  (0x1 << 31)
    NIC_ALL_PORT_MASK = NIC_PORT1_MASK | \
                        NIC_PORT2_MASK | \
                        NIC_MGMT_MASK


class MTP_Const:
    MTP_SLOT_NUM = 10
    MTP_SLOT_INVALID = 10

    MTP_POWER_ON_DELAY = 180
    MTP_POWER_ON_TIMEOUT = 480
    MTP_OS_SHUTDOWN_DELAY = 60
    MTP_POWER_CYCLE_DELAY = 30
    MTP_NETCOPY_DELAY = 600
    OS_SYNC_DELAY = 300
    OS_CMD_DELAY = 120
    NIC_CON_CMD_DELAY = 600
    NIC_CON_INIT_RETRY = 3
    NIC_NETCOPY_DELAY = 120
    NIC_MGMT_IP_SET_DELAY = 10
    NIC_MGMT_IP_INIT_RETRY = 3
    NIC_POWER_ON_DELAY = 30
    NIC_POWER_OFF_DELAY = 10

    MTP_DIAGMGR_DELAY = 10
    MTP_MGMT_IP_SET_DELAY = 10

    DIAG_REGRESSION_TIMEOUT = 72000
    DIAG_TEST_TIMEOUT = 7200
    
    MFG_EDVT_LOW_FAN_SPD = 40
    MFG_EDVT_NORM_FAN_SPD = 40
    MFG_EDVT_HIGH_FAN_SPD = 50
    MFG_EDVT_HIGH_TEMP = 50
    MFG_EDVT_LOW_TEMP = 0
    MFG_EDVT_TEMP_DIFF = 5
    MFG_EDVT_HIGH_VOLT = 5
    MFG_EDVT_LOW_VOLT = -5
    MFG_TEMP_WAIT_TIMEOUT = 180
    MFG_TEMP_SOAK_TIMEOUT = 180
    MFG_TEMP_CHECK_INTERVAL = 10


class MTP_DIAG_Error:
    MTP_DIAG_PASS = "MTP_DIAG_PASS"
    MTP_INV_PARAM = "MTP_DIAG_INV_PARAM"
    MTP_HW_SANITY = "MTP_DIAG_HW_SANITY"
    MTP_DIAG_SANITY = "MTP_DIAG_SW_SANITY"
    MTP_ENV_SETUP = "MTP_DIAG_ENV_SETUP"
    NIC_DIAG_FAIL = "MTP_DIAG_NIC_TEST_FAIL"
    NIC_DIAG_TIMEOUT = "MTP_DIAG_NIC_TEST_TIMEOUT"


class MTP_DIAG_Logfile:
    ONBOARD_DIAG_LOG_FILES = "/home/diag/diag/log/*txt"
    ONBOARD_ASIC_LOG_FILES = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/*log"
    ONBOARD_TEST_LOG_FILES = "/home/diag/mtp_regression/*log"

    DIAG_QA_LOG_DIR = "/vol/hw/diag/diag_qa/regression_log/"
    DIAG_MFG_DL_LOG_DIR = "/mfg_log/NAPLES100/DL/"
    DIAG_MFG_P2C_LOG_DIR = "/mfg_log/NAPLES100/P2C/"
    DIAG_MFG_4C_LOG_DIR = "/mfg_log/NAPLES100/4C/"


class MTP_DIAG_Path:
    ONBOARD_MTP_DIAG_PATH = "/home/diag/"
    ONBOARD_NIC_DIAG_PATH = "/home/diag/"
    ONBOARD_MTP_NIC_DIAG_PATH = "/home/diag/nic_diag/"
    ONBOARD_NIC_UTIL_PATH = "/home/diag/diag/util/"
    ONBOARD_MTP_NIC_CON_PATH = "/home/diag/diag/python/regression/"


class MTP_DIAG_Report:
    NIC_DIAG_TEST_START = "{:s} DIAG TEST ({:s}, {:s}) STARTED"
    NIC_DIAG_TEST_PASS = "{:s} DIAG TEST {:s} {:s} PASS, DURATION {:s}"
    NIC_DIAG_TEST_TIMEOUT = "{:s} DIAG TEST {:s} {:s} TIMEOUT, DURATION {:s}"
    NIC_DIAG_TEST_FAIL = "{:s} DIAG TEST {:s} {:s} {:s}, DURATION {:s}"
    NIC_DIAG_TEST_RSLT_RE = r"\[NIC-{:s}\]: +{:s} DIAG TEST (.*) (.*) (.*), DURATION"
    MTP_DIAG_REGRESSION_FAIL = "MTP_DIAG_REGRESSION_TEST_FAIL"
    NIC_DIAG_REGRESSION_FAIL = "DIAG_REGRESSION_TEST_FAIL"
    NIC_DIAG_REGRESSION_PASS = "DIAG_REGRESSION_TEST_PASS"
    NIC_DIAG_REGRESSION_RSLT_RE = r"NIC-(\d{{2}}) (.*) {:s}"
