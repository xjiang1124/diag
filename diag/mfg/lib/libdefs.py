from enum import Enum

class NIC_Type:
    NAPLES100 = "NAPLES100"
    NAPLES100IBM = "NAPLES100IBM"
    NAPLES100HPE = "NAPLES100HPE"
    NAPLES100DELL = "NAPLES100DELL"
    NAPLES25 = "NAPLES25"
    FORIO = "FORIO"
    VOMERO = "VOMERO"
    VOMERO2 = "VOMERO2"
    NAPLES25SWM = "NAPLES25SWM"
    NAPLES25OCP = "NAPLES25OCP"
    NAPLES25SWMDELL = "NAPLES25SWMDELL"
    NAPLES25SWM833 = "NAPLES25SWM833"
    ORTANO = "ORTANO"
    ORTANO2 = "ORTANO2"
    POMONTEDELL = "POMONTEDELL"
    LACONA32DELL = "LACONA32DELL"
    LACONA32 = "LACONA32"
    ORTANO2ADI = "ORTANO2ADI"
    ORTANO2ADIIBM = "ORTANO2ADIIBM"
    ORTANO2ADIMSFT = "ORTANO2ADIMSFT"
    ORTANO2INTERP = "ORTANO2INTERP"
    ORTANO2SOLO = "ORTANO2SOLO"
    ORTANO2SOLOORCTHS = "ORTANO2SOLOORCTHS"
    ORTANO2SOLOMSFT = "ORTANO2SOLOMSFT"
    ORTANO2SOLOS4 = "ORTANO2SOLOS4"
    ORTANO2ADICR = "ORTANO2ADICR"
    ORTANO2ADICRMSFT = "ORTANO2ADICRMSFT"
    ORTANO2ADICRS4 = "ORTANO2ADICRS4"
    GINESTRA_D4 = "GINESTRA_D4"
    GINESTRA_D5 = "GINESTRA_D5"
    GINESTRA_S4 = "GINESTRA_S4"
    LENI = "LENI"
    LENI48G = "LENI48G"
    MALFA = "MALFA"
    POLLARA = "POLLARA"
    LINGUA = "LINGUA"
    UNKNOWN = "Unknown"

class PRODUCT_SKU(Enum):
    ADI_IBM       = "DSC2-2Q200-32R32F64P-B"
    ADI_MSFT      = "DSC2-2Q200-32R32F64P-M2"
    SOLO_MSFT     = "DSC2-2Q200-32R32F64P-M4"
    ADICR_MSFT    = "DSC2-2Q200-32R32F64P-M5"
    SOLO_S4       = "DSC2-2Q200-32R32F64P-S4"
    SOLO_ORCL     = "DSC2-2Q200-32R32F64P-R4"
    SOLO_ORCL_TH  = "DSC2-2Q200-32R32F64P-R4-T"
    ADICR_ORCL    = "DSC2-2Q200-32R32F64P-R5"

    GIN_D4_ORCL   = "DSC2A-2Q200-32R32F64P-R"
    GIN_D5_ORCL   = "DSC2A-2Q200-32S32F64P-R"
    GIN_S4        = "DSC2A-2Q200-32S32F64P-S4"
    GIN_S4_B3     = "DSC2A-2Q200-32S32F64P-S4-B3"
    GIN_S4_P3     = "DSC2A-2Q200-32S32F64P-S4-P3"

class MTP_TYPE:
    CAPRI = "CAPRI"
    TURBO_CAPRI = "TURBO_CAPRI"
    ELBA  = "ELBA"
    TURBO_ELBA = "TURBO_ELBA"
    MATERA = "MATERA"

class Factory:
    UNKNOWN = "Unknown"
    MILPITAS = "Milpitas"
    FSP = "Penang FSP"
    P1 = "Penang P1"
    LAB = "MTP lab or HW lab"

class FLEX_TWO_WAY_COMM:
    PRE_POST_RETRY = 2
    POST_RETRY = 2

class FF_Stage(Enum):
    FF_DL = "DL"
    FF_P2C = "P2C"
    FF_2C_H = "2C-H"
    FF_2C_L = "2C-L"
    FF_4C_H = "4C-H"
    FF_4C_L = "4C-L"
    FF_SWI = "SWI"
    FF_FST = "FST"
    FF_CFG = "CFG"
    FF_SRN = "SRN"
    FF_ORT = "ORT"
    FF_RDT = "RDT"
    SCAN_DL = "ScanDL"
    CONVERT = "CONVERT"
    QA = "CI-CD"

    def __str__(self):
        return self.value

class FPN_FF_Stage:
    FF_CFG = "CFG"
    FF_DL = "PSO-DOWNLOAD_AUTO"
    FF_P2C = "PSO-P2C_AUTO"
    FF_2C_H = "PSO-2C-H_AUTO"
    FF_2C_L = "PSO-2C-L_AUTO"
    FF_4C_H = "PSO-4C-H_AUTO"
    FF_4C_L = "PSO-4C-L_AUTO"
    FF_SWI = "PSO-SWI_AUTO"
    FF_FST = "PSO-FST_AUTO"
    FF_ORT = "PSO-ORT_AUTO"
    FF_RDT = "PSO-RDT_AUTO"

#NOT ONLY SWM TEST MODE, ALL TEST MODE WILL USE AS SAME
class Swm_Test_Mode(Enum):
    SWM = "swm"
    SWMALOM = "swmalom"
    ALOM = "alom"
    SW_DETECT = "sw_detect"

    def __str__(self):
        return self.value

class NIC_Status:
    NIC_STA_POWEROFF = 0
    NIC_STA_POWERUP = 1
    NIC_STA_TERM_FAIL = 2
    NIC_STA_MGMT_FAIL = 3
    NIC_STA_DIAG_FAIL = 4
    NIC_STA_PWR_FAIL = 5
    NIC_STA_OK = 10
    NIC_STA_MAX = 11


class MTP_Status:
    MTP_STA_POWEROFF = 0
    MTP_STA_POWERUP = 1
    MTP_STA_ENV_FAIL = 2
    MTP_STA_MGMT_FAIL = 3
    MTP_STA_READY = 10
    MTP_STA_MAX = 11
    
class MTP_Health_Status:
    MTP_NON_HEALTH = 0
    MTP_HEALTH = 1

class NIC_Port_Mask:
    NIC_PORT1_MASK = (0x1 << 0)
    NIC_PORT2_MASK = (0x1 << 1)
    NIC_MGMT_MASK =  (0x1 << 31)
    NIC_ALL_PORT_MASK = NIC_PORT1_MASK | \
                        NIC_PORT2_MASK | \
                        NIC_MGMT_MASK

class Voltage_Margin:
    normal = "normal"
    high = "high"
    low = "low"

class MTP_Const:
    MTP_SLOT_NUM = 10
    MTP_SLOT_INVALID = 10

    MTPS_SLOT_NUM = 4

    MTP_POWER_ON_DELAY = 180
    MTP_POWER_OFF_DELAY = 30
    MTP_POWER_ON_TIMEOUT = 6000
    MTP_REBOOT_DELAY = 120
    MTP_OS_SHUTDOWN_DELAY = 60
    MTP_POWER_CYCLE_DELAY = 30
    MTP_NETCOPY_DELAY = 600
    MTP_FRU_UPDATE_DELAY = 1200
    MTP_PARA_AAPL_INIT_DELAY = 2000
    OS_SYNC_DELAY = 300
    SSH_PASSWORD_DELAY = 30
    MTP_OS_CMD_DELAY = 30
    OS_CMD_DELAY = 600
    NIC_CON_CMD_DELAY = 900
    NIC_CON_INIT_DELAY =120
    NIC_NETCOPY_DELAY = 120
    NIC_CON_CMD_RETRY = 5
    NIC_CON_CMD_DELAY_10 = 10
    NIC_MGMT_IP_SET_DELAY = 3
    NIC_MGMT_IP_INIT_RETRY = 3
    NIC_SW_BOOTUP_DELAY = 120
    NIC_AVS_SET_DELAY = 600
    NIC_ESEC_PROG_DELAY = 1800
    NIC_EFUSE_PROG_DELAY = 1800
    NIC_POWER_ON_DELAY = 80
    NIC_POWER_OFF_DELAY = 10
    NIC_SYSRESET_DELAY = 180
    NIC_FW_SET_DELAY = 300
    NIC_FPGA_PROG_DELAY = 5 * 60
    NIC_L1_ESEC_PROG_DELAY = 5 * 60
    NIC_ESEC_WRITE_PROT_DELAY = 15 * 60
    NIC_I2C_DETECT_DELAY = 60
    NIC_EDMA_ENV_INIT_CMD_DELAY = 600
    NIC_ERASE_QSPI_IMG_DELAY = 900
    NIC_ERASE_BOOT0_IMG_DELAY = 300
    NIC_PROG_BOOT0_IMG_DELAY = 300
    NIC_OCP_RMII_DELAY = 60
    NIC_OCP_CON_DELAY = 5 * 60

    MTP_DIAGMGR_DELAY = 10
    MTP_MGMT_IP_SET_DELAY = 10
    MTP_PCIE_EN_DIS_DELAY = 60
    MTP_HEALTH_MONITOR_CYCLE = 180

    # single test, 1.5 hours
    DIAG_SEQ_TEST_TIMEOUT = 90*60
    # single prbs test, 8 min
    DIAG_PARA_TEST_TIMEOUT = 8*60
    # MEM DDR_STRESS timeout 5 min
    DIAG_MEM_DDR_STRESS_TEST_TIMEOUT = 5*60
    # para/snake test, 30 min
    MTP_PARA_TEST_TIMEOUT = 30*60
    # para/asic l1 test, 30 min
    MTP_PARA_ASIC_L1_TEST_TIMEOUT = 30*60
    SALINA_AI_ASIC_L1_TEST_TIMEOUT = 60*15
    SALINA_DPU_ASIC_L1_TEST_TIMEOUT = 60*60
    MTP_L1_HEALTH_CHECK_TIMEOUT = 10*60

    # more than 12 hours
    MFG_P2C_TEST_TIMEOUT = 48000
    # more than 12 hours
    MFG_ORT_TEST_TIMEOUT = 48000
    # more than 12 hours
    MFG_RDT_TEST_TIMEOUT = 48000
    # more than 24 hours
    MFG_4C_TEST_TIMEOUT = 96000
    # 4 hours
    MFG_DL_TEST_TIMEOUT = 14400
    # 2.5 hour SWM and IBM update to 6 hours
    MFG_SW_TEST_TIMEOUT = 21600
    MFG_MTPSCREEN_TEST_TIMEOUT = 21600
    # 1 hour
    MFG_FST_TEST_TIMEOUT = 3600
    MFG_CFG_TEST_TIMEOUT = 3600

    MFG_ORT_HIGH_FAN_SPD = 100
    MFG_RDT_HIGH_FAN_SPD = 100
    MFG_EDVT_HIGH_FAN_SPD = 100
    MFG_EDVT_NORM_FAN_SPD = 60
    MFG_EDVT_LOW_FAN_SPD = 60
    MFG_EDVT_HIGH_TEMP = 50
    MFG_EDVT_LOW_TEMP = 0
    MFG_TEMP_WAIT_TIMEOUT = 180
    MFG_TEMP_SOAK_TIMEOUT = 180
    MFG_TEMP_CHECK_INTERVAL = 10

    MFG_MATERA_ORT_HIGH_FAN_SPD = 80
    MFG_MATERA_RDT_HIGH_FAN_SPD = 80
    MFG_MATERA_EDVT_HIGH_FAN_SPD = 90
    MFG_MATERA_EDVT_NORM_FAN_SPD = 50
    MFG_MATERA_EDVT_LOW_FAN_SPD = 50

    # MTP temperature controls for chamber and outside
    HIGH_CHAMBER_UPPER_LIMIT = 60
    HIGH_CHAMBER_LOWER_LIMIT = 40
    LOW_CHAMBER_UPPER_LIMIT  = 15
    LOW_CHAMBER_LOWER_LIMIT  = -5

    # MFG moduling parameters
    MFG_MODEL_EDVT_HIGH_FAN_SPD = 60
    MFG_MODEL_EDVT_LOW_FAN_SPD = 60
    MFG_MODEL_EDVT_HIGH_TEMP = 22
    MFG_MODEL_EDVT_LOW_TEMP = 22
    MFG_MODEL_TEMP_SOAK_TIMEOUT = 1

    MFG_MATERA_MODEL_EDVT_HIGH_FAN_SPD = 80
    MFG_MATERA_MODEL_EDVT_NORM_FAN_SPD = 80
    MFG_MATERA_MODEL_EDVT_LOW_FAN_SPD = 80


class MTP_DIAG_Error:
    MTP_DIAG_PASS = "MTP_DIAG_PASS"
    MTP_INV_PARAM = "MTP_DIAG_INV_PARAM"
    MTP_HW_SANITY = "MTP_DIAG_HW_SANITY"
    MTP_DIAG_SANITY = "MTP_DIAG_SW_SANITY"
    MTP_ENV_SETUP = "MTP_DIAG_ENV_SETUP"
    NIC_DIAG_FAIL = "FAIL"
    NIC_DIAG_TIMEOUT = "TIMEOUT"


class MTP_DIAG_Logfile:
    ONBOARD_DIAG_LOG_FILES = "/home/diag/diag/log/*"
    NIC_ONBOARD_DIAG_LOG_FILES = "/home/diag/diag/log/*"
    MATERA_ONBOARD_ASIC_LOG_FILES = "find /home/diag/diag/asic/asic_src/ip/cosim/tclsh -maxdepth 1 -type f -regex '.*.log' -not -name 'snake_slot*log' -not -name 'pcie_prbs*log' -exec mv {{}} {:s} \\; "
    ONBOARD_ASIC_LOG_FILES = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/*log"
    ONBOARD_CSP_LOG_FILES = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/*txt"
    ONBOARD_BIN_LOG_FILES = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/*_esec_backup.bin"
    ONBOARD_ASIC_DUMP_FILES = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/*tar"
    ONBOARD_NIC_LOG_FILES = "/home/diag/diag/nic_log/*"
    ONBOARD_ASIC_LOG_DIR = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/"
    ONBOARD_NIC_LOG_DIR = "/home/diag/diag/nic_log/"
    NIC_ONBOARD_ASIC_LOG_DIR = "/data/nic_arm/nic/asic_src/ip/cosim/tclsh/"

    SCAN_BARCODE_FILE = "fru_barcode.yaml"


class MTP_DIAG_Path:
    ONBOARD_MTP_DIAG_PATH = "/home/diag/"
    ONBOARD_MTP_DIAG_SCRIPT_PATH = "/home/diag/diag/scripts"
    ONBOARD_MTP_NIC_CON_PATH = "/home/diag/diag/python/regression/"
    ONBOARD_MTP_DSHELL_PATH = "/home/diag/diag/python/infra/dshell/"
    ONBOARD_MTP_ESEC_PATH = "/home/diag/diag/python/esec/"
    ONBOARD_MTP_ASIC_PATH = "/home/diag/diag/scripts/asic/"
    ONBOARD_MTP_MTP_DIAG_PATH = "/home/diag/diag/"
    ONBOARD_MTP_NIC_DIAG_PATH = "/home/diag/nic_diag/"
    ONBOARD_MTP_CSP_PATH = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh"
    ONBOARD_NIC_UTIL_PATH = "/home/diag/diag/util/"
    ONBOARD_NIC_DIAG_PATH = "/home/diag/"
    ONBOARD_NIC_DIAG_UTIL_PATH = "/data/"


class MTP_DIAG_Report:
    NIC_DIAG_TEST_START = "{:s} DIAG TEST ({:s}, {:s}) STARTED"
    NIC_DIAG_TEST_PASS = "{:s} DIAG TEST {:s} {:s} PASS, DURATION {:s}"
    NIC_DIAG_TEST_TIMEOUT = "{:s} DIAG TEST {:s} {:s} TIMEOUT, DURATION {:s}"
    NIC_DIAG_TEST_FAIL = "{:s} DIAG TEST {:s} {:s} {:s}, DURATION {:s}"
    NIC_DIAG_TEST_ERR_MSG = "{:s} DIAG TEST {:s} {:s}, ERR MSG == {:s} == ERR MSG END"
    NIC_DIAG_TEST_RSLT_RE = r"\[NIC-{:s}\]: +{:s} DIAG TEST (.*) (.*) (.*), DURATION"
    NIC_DIAG_TEST_ERR_MSG_RE = r"\[NIC-{:s}\]: +{:s} DIAG TEST {:s} {:s}, ERR MSG == (.*) == ERR MSG END"
    NIC_DIAG_TEST_SKIPPED = "{:s} DIAG TEST ({:s}, {:s}) SKIPPED"
    NIC_DIAG_SLOT_SKIPPED = "SKIPPING ALL TESTS ON THIS SLOT"
    MTP_DIAG_REGRESSION_FAIL = "MTP_DIAG_REGRESSION_TEST_FAIL"
    NIC_DIAG_REGRESSION_FAIL = "NIC_DIAG_REGRESSION_TEST_FAIL"
    NIC_DIAG_REGRESSION_PASS = "NIC_DIAG_REGRESSION_TEST_PASS"
    NIC_DIAG_REGRESSION_SKIP = "NIC_DIAG_REGRESSION_TEST_SKIP"
    NIC_DIAG_REGRESSION_RSLT_RE = r"NIC-(\d{{2}}) (\w+) (\w+) {:s}"
    NIC_DIAG_REGRESSION_SKIP_RSLT_RE = r"NIC-(\d{{2}}) {:s}" #SKIP doesnt have type and sn
    NIC_DIAG_REGRESSION_PN_BY_FRU_RE = r"FRU: {:s},\s.*,\s(\w.*\w)"
    NIC_DIAG_REGRESSION_PN_BY_FRU2_RE = r"SN = {:s},\sPN\s=\s(\w.*\w),\sTYPE\s=\s\w+"
    NIC_DIAG_REGRESSION_MAC_PN_BY_FRU_RE = r"FRU: {:s},\s(\w.*\w),\s(\w.*\w)"
    NIC_DIAG_REGRESSION_ROT_SN_BY_FRU_RE = r"{:s} DIAG TEST FST ROT WITH ROT CABLE (ROT-\d{{5}}) (PASS|FAILED), DURATION"
    NIC_RETEST_BLOCKED_MSG = "--[ MOVE TO DEBUG DO NOT RETEST ]--"
    NIC_UNKNOWN_FAILURE_CODE = "UNKNOWN"

class MFG_DIAG_CMDS:
    MTP_DIAG_VERSION_FMT = "version"
    MTP_LOGIN_VERIFY_FMT = "echo $USER"
    MTP_ASIC_VERSION_FMT = "head /home/diag/diag/asic/asic_version.txt"
    MTP_REV_FMT =  "env | grep MTP_REV | cat"
    MTP_TYPE_FMT =  "env | grep MTP_TYPE | cat"
    MTP_FAN_STATUS_FMT = "devmgr -dev FAN -status"
    MTP_FAN_SET_SPD_FMT = "devmgr -dev=fan -speed -pct={:d}"
    MTP_PSU_DISP_FMT = "devmgr -dev=psu_{:s} -status"
    MTP_MATERA_PSU_DISP_FMT = "fpgautil show psu"
    MTP_VRM_TEST_FMT = "mtptest -vrm"
    MTP_FAN_TEST_FMT = "mtptest -fanspd"
    MTP_FAN_PRSNT_FMT = "mtptest -present"
    MTP_PSU_TEST_FMT = "mtptest -psu"
    NIC_CARD_TYPE_SET_FMT = "export CARD_TYPE={:s}"
    MTP_MATERA_DEVMGR_STATUS_FMT = "devmgr_v2 status"
    MTP_MATERA_FAN_SET_SPD_FMT = "devmgr_v2 fanctrl --pct {:d}"
    MTP_MATERA_INVENTORY_CPU_FMT = "inventory -cpu"
    MTP_MATERA_INVENTORY_DDR_FMT = "inventory -ddr"
    MTP_MATERA_EEUTIL_INFO_FMT = "eeutil -info"
    MTP_MATERA_DISP_DEV_FMT = "eeutil -disp -dev {:s}"

    MTP_MATERA_FPGA_SHOW_FAN_FMT = "fpgautil show fan"
    MTP_FPGA_UTIL_READ32_FMT = "fpgautil r32 {:s}"
    MTP_FPGA_UTIL_WRITE32_FMT = "fpgautil w32 {:s} {:s}"
    MTP_FPGA_UTIL_SPIMODE_OFF_FMT = "fpgautil spimode {:s} off"
    MTP_FPGA_UTIL_REGDUMP_FMT = "fpgautil regdump"
    # fpgautil cpld <slot#> generate/verify/erase/program <cfg0/cfg1/ufm2/fea> <filename>
    MTP_MATERA_FPGAUTIL_CPLD_CMD_FMT = "fpgautil cpld {:s} {:s} {:s} {:s}"
    MTP_MATERA_FPGAUTIL_FLASH_CMD_FMT = "fpgautil flash {:s} {:s} {:s} {:s} {:s}"
    MTP_MATERA_FPGAUTIL_MVLDUMP_CMD_FMT = "fpgautil mvldump {:s} {:s}"
    MTP_MATERA_QSPI_PROG_SH_CMD_FMT = "./qspi_prog.sh {:s}"
    MTP_MATERA_POLLARA_QSPI_PROG_SH_CMD_FMT = "./qspi_prog.v2.sh {:s}"
    MTP_MATERA_POLLARA_QSPI_PROG_SECURE_SH_CMD_FMT = "./qspi_prog_secure.v2.sh {:s}"
    MTP_MATERA_SWITCH_NIC_CONSOLE2A35_FMT = "con_switch.sh {:s} 0"
    MTP_MATERA_SWITCH_NIC_CONSOLE2N1_FMT = "con_switch.sh {:s} 1"
    MTP_CPLD_READ_FMT  = "cpldutil -cpld-rd -addr=0x{:x}"
    MTP_CPLD_WRITE_FMT = "cpldutil -cpld-wr -addr=0x{:x} -data=0x{:x}"
    MTP_MAC_FMT = "cat /sys/class/net/enp4s0/address"

    MTP_NIC_FRU_DUMP_FMT = "eeutil -uut=UUT_{:d} -dump -numBytes=512 && mv eeprom eeprom_{:d}"
    NIC_FRU_DUMP_FMT = "{:s}eeutil -dump -numBytes=512"
    MTP_FRU_PROG_SN_MAJ_MAC_FMT = "eeutil -update -erase -numBytes=64 -sn='{:s}' -maj='{:s}' -mac='{:s}'"

    NIC_JTAG_TEST_FMT = "sys_sanity.sh {:d}"

    NIC_CPLD_PROG_FMT = "{:s}cpld -prog /{:s}"
    NIC_CPLD_READ_FMT = "{:s}cpld -r 0x{:x}"
    NIC_CPLD_REF_FMT = "{:s}cpld -refresh"
    NIC_CPLD_WRITE_FMT = "{:s}cpld -w 0x{:x} 0x{:x}"
    NIC_CPLD_PROG_ELBA_FMT = "{:s}xo3dcpld -prog /{:s} {:s}"
    NIC_CPLD_READ_ELBA_FMT = "{:s}xo3dcpld -r 0x{:x}"
    NIC_CPLD_WRITE_ELBA_FMT = "{:s}xo3cpld -w 0x{:x} 0x{:x}"
    NIC_CPLD_ERASE_ELBA_FMT = "{:s}xo3dcpld -erase {:s}"
    NIC_CPLD_REF_ELBA_FMT = "{:s}xo3dcpld -refresh"
    NIC_CPLD_DUMP_ELBA_FMT = "{:s}xo3dcpld -file {:s} {:s}" #(-file output_file region)
    NIC_CPLD_DUMP_COMPARE_FMT = "cmp -l /{:s} /{:s}"
    # NIC_FPGA_PROG_FMT = "{:s}artix7fpga -prog /{:s} {:s}"
    # NIC_FPGA_DUMP_FMT = "{:s}artix7fpga -file /{:s} {:s}"
    NIC_FPGA_PROG_FMT = "{:s}cpldapp -writeflash /{:s} {:s}"
    NIC_FPGA_DUMP_FMT = "{:s}cpldapp -verifyflash /{:s} {:s}"
    NIC_SGMII_READ_FMT  = "{:s}cpld -smird 0x{:x} 0x{:x}"
    NIC_SGMII_WRITE_FMT = "{:s}cpld -smiwr 0x{:x} 0x{:x} 0x{:x}"
    NIC_SGMII_READ_ELBA_FMT  = "{:s}xo3dcpld -smird 0x{:x} 0x{:x}"
    NIC_SGMII_WRITE_ELBA_FMT = "{:s}xo3dcpld -smiwr 0x{:x} 0x{:x} 0x{:x}"
    NIC_SETTING_PARTITION_FMT = "/emmc_format.sh"
    NIC_DIAG_ASIC_VERSION_FMT = "head /data/nic_arm/{:s}/asic_version.txt"
    # onboard diag utils version
    NIC_DIAG_UTIL_VERSION_FMT = "head /data/nic_util/version.txt"
    # copied diag version
    NIC_DIAG_VERSION_FMT = "head /home/diag/diag/scripts/version.txt"
    # NIC HAL process
    NIC_HAL_RUNNING_FMT = "ps | grep hal"
    NIC_SYSMGR_RUNNING_FMT = "ps | grep sysmgr"
    NIC_SYSMOND_RUNNING_FMT = "ps | grep sysmond"

    NIC_MOUNT_EMMC_FMT = "mount /dev/mmcblk0p10 /data"
    NIC_FSCK_EMMC_FMT = "fsck -y /dev/mmcblk0p10"
    NIC_DIAG_CLEANUP_FMT = "rm -rf /data/nic*"
    NIC_EMMC_LS_FMT = "ls -al /data/"
    NIC_PARTITION_DISP_FMT = "fdisk -l"
    NIC_MOUNT_DISP_FMT = "mount | grep '/dev/mmcblk0p10'"
    NIC_BRINGUP_MGMT_FMT = "sysinit.sh classic hw diag"
    NIC_QSPI_PROG_FMT = "fwupdate -p /{:s} -i 'all'"
    NIC_DIAGFW_PROG_FMT = "fwupdate -p /{:s} -i diagfw"
    NIC_GOLDFW_PROG_FMT = "cd /; tar xvf {:s}; ./fwupdate -p {:s} -i all"
    NIC_UBOOT_PROG_FMT = "/{:s} {:s} /{:s}"

    NIC_EMMC_INIT_FMT = "fwupdate --init-emmc"
    NIC_CHECK_EMMC_FMT = "mmc extcsd read /dev/mmcblk0"
    NIC_EMMC_HWRESET_SET_FMT = "mmc hwreset enable /dev/mmcblk0"
    NIC_EMMC_HWRESET_CHECK_FMT = "mmc extcsd read /dev/mmcblk0 | grep -i reset"
    NIC_EMMC_BKOPS_EN_FMT = "/mmc.latest bkops_en auto /dev/mmcblk0"
    NIC_EMMC_BKOPS_CHECK_FMT = "mmc extcsd read /dev/mmcblk0 | grep -i ops"
    NIC_EMMC_READ_ID_FMT = "cat /sys/block/mmcblk0/device/manfid"
    NIC_EMMC_PERF_MODE = "touch /sysconfig/config0/.perf_mode"
    NIC_EMMC_PERF_MODE_CHECK = "[[ -f /sysconfig/config0/.perf_mode ]] ; echo $?"
    NIC_EMMC_PROG_FMT_NAPLES100 = "fwupdate -p /data/{:s} -i 'uboot mainfwa mainfwb'"
    NIC_GOLDFW_PROG_FMT_NAPLES100 = "fwupdate -p /{:s} -i goldfw"
    NIC_EMMC_PROG_FMT = "cd /data; tar xvf {:s}; ./fwupdate -p /data/{:s} -i 'all'"
    NIC_EMMC_PROG_SALINA_FMT = "cd /data; sysupdate.sh -p {:s}"
    NIC_EMMC_B_PROG_FMT = "cd /data; tar xvf {:s}; ./fwupdate -p /data/{:s} -i mainfwb"
    NIC_BOOT0_PROG_FMT = "cd /data; ./fwupdate -p /data/{:s} -i boot0"
    NIC_BOOT_SHOW_RUNNING_IMG_FMT = "fwupdate -r"
    NIC_BOOT_SHOW_STARTUP_IMG_FMT = "fwupdate -S"
    NIC_IMG_DISP_FMT = "fwupdate -L"
    NIC_IMG_DISP1_FMT = "fwupdate -l"
    NIC_SET_SW_BOOT_FMT = "fwupdate -s mainfwa"
    NIC_SET_DIAG_BOOT_FMT = "fwupdate -s diagfw"
    NIC_SET_GOLD_BOOT_FMT = "fwupdate -s goldfw"
    NIC_SET_EXTOSA_BOOT_FMT = "fwupdate -s extosa"
    NIC_SET_MGMT_IP_FMT = "ifconfig oob_mnic0 10.1.1.{:d} netmask 255.255.255.0"
    NIC_DATE_SET_FMT = "date --set='{:s}'"
    NIC_HW_CLOCK_SYNC_FMT = "hwclock -w"
    NIC_UNTAR_FMT = "tar xf {:s} -C {:s}"
    NIC_SYS_CLEAN_FMT = "{:s}scripts/sys_clean.sh"
    NIC_SET_EXTDIAG_BOOT_FMT = "fwupdate -s extdiag"

    NIC_ESEC_ERR_CHECK_FMT        = "inventory -esec -slot {:d}"
    NIC_ESEC_PROG_PRE_FMT         = "python2 ./esec_ctrl.py -slot {:d} -img_prog"
    SALINA_NIC_ESEC_PROG_PRE_FMT  = "./{:s} {:d}"
    NIC_ESEC_PROG_POST_FMT        = "python2 ./esec_ctrl.py -cleanup"
    NIC_ESEC_CPLD_CHECK_FMT       = "python2 ./esec_ctrl.py -check_uboot -slot {:d} -post_check"
    NIC_ESEC_SALINA_CPLD_CHECK_FMT= "./esec_ctrl.py -check_uboot -slot {:d}"
    NIC_ESEC_SALINA_UDS_CERT_FMT  = "./esec_ctrl.py -check_uds_cert -slot {:d}"
    NIC_ESEC_SALINA_VAL_UDS_CERT_FMT  = "./esec_ctrl.py -val_uds_cert -slot {:d}"
    NIC_EFUSE_PROG_ELBA_MODEL_FMT = "python2 ./esec_ctrl.py -efuse_prog -d -slot {:d} -sn {:s} -pn '{:s}' -mac {:s} -brd_name {:s}"
    NIC_EFUSE_PROG_ELBA_FMT       = "python2 ./esec_ctrl.py -efuse_prog -slot {:d} -sn {:s} -pn '{:s}' -mac {:s} -brd_name {:s}"
    NIC_ESEC_PROG_FMT             = "python2 ./esec_ctrl.py -esec_prog -slot {:d} -sn {:s} -pn '{:s}' -mac {:s} -brd_name {:s} -mtp {:s}"
    NIC_ESEC_PROG_ELBA_FMT        = "python2 ./esec_ctrl.py -esec_prog -slot {:d} -sn {:s} -pn '{:s}' -mac {:s} -brd_name {:s} -mtp {:s} -fast"
    NIC_ESEC_PROG_DUMP_FMT        = "python2 ./esec_ctrl.py -show_sts -sn {:s} -slot {:d} -brd_name {:s}"
    NIC_ESEC_PROG_QSPI_DUMP_FMT   = "tclsh qspi_esec_data_dump.tcl -slot {:d} -mode {:s}"
    NIC_ESEC_HW_UNLOCK_FMT          = "sal_esecure_lockbits.sh {:d} 0 0"
    NIC_ESEC_PROG_DICE_SALINA_FMT = "./esec_ctrl.py -dice_prog -slot {:d} -sn {:s}"
    NIC_ESEC_PROG_DICE_IMG_SALINA_FMT = "./esec_ctrl.py -dice_img_prog -slot {:d}"
    NIC_ESEC_PENTRUST_SALINA_FMT  = "./{:s} {:d}"
    NIC_ESEC_SALINA_HMAC_FUSE_PROG_FMT = "./esec_ctrl.py -hmac_fuse_prog -slot {:d} -hmac_file /home/diag/diag/scripts/asic/{:s}"
    NIC_ESEC_SALINA_HMAC_FUSE_CHK_FMT = "./esec_ctrl.py -hmac_fuse_prog -slot {:d} -hmac_file check_only"
    NIC_I2C_SET_FMT = "i2cset -f -y 0 0x4c 0x19 0x7d"
    NIC_I2C_GET_SPIMODE_FMT = "i2cget  -y {:s} 0x{:s} 0x{:s}"
    NIC_WRITE_CPLD_FMT  = "/data/nic_util/xo3dcpld -w 0x12 0x44"
    NIC_READ_CPLD_FMT  = "/data/nic_util/xo3dcpld -r 0x12"
    NIC_RUN_ASIC_L1_FMT = "./run_l1.sh -sn {:s} -slot {:d} -m {:s} -v {:s} -ddr {:s} -hc {:s}"
    NIC_L1_ESEC_PROG_FMT = "tclsh ./esec_l1_prog_elba.tcl -slot {:d}"
    NIC_L1_ESEC_GIGLIO_PROG_FMT = "tclsh ./esec_l1_prog_giglio.tcl -slot {:d}"
    NIC_MATERA_RUN_ASIC_L1_FMT = "./run_l1.sh -sn {:s} -slot {:d} -m {:s} -v {:s} -ddr {:s} -hc {:s} -joo {:s} -i {:s} -o {:s} -e {:s} -s {:s} -ite {:s}"
    NIC_IMG_VER_DISP_FMT = "cat /proc/version | sed 's/.*SMP/SMP/'"
    MTP_IMG_VER_DISP_FMT = "cat /proc/version | sed 's/.*SMP/SMP/'"
    NIC_VMARG_SET_FMT = "/home/diag/diag/scripts/vmarg.sh {:s} {:s}"
    SALINA_NIC_VMARG_SET_FMT = "./nic_test_v2.py salina vmarg -slot {} -vmarg {} --new_memory_layout"
    SALINA_NIC_DDR_VMARG_SET_FMT = "./nic_test_v2.py salina pcieawd_env -slot {} -all_params ddr_vmarg:{}"
    NIC_DISP_VOLT_FMT = "devmgr -status"
    MTP_MATERA_SWI_CHECK_FMT = "/home/diag/diag/scripts/check_python.sh"
    NIC_OCP_RMII_CHECK_FMT = "tclsh sal_lingua_rmii_test.tcl {:s}"
    NIC_OCP_CON_CHECK_FMT = "./run_lingua_adapter_test.sh {:s}"

    GET_BOARD_CONFIG_FMT = "board_config -r"
    SET_BOARD_CONFIG_FMT = "board_config -w {:s}"
    ASSIGN_BOARD_ID_FMT = "board_config -B {:s}"
    READ_BOARD_ID_FMT = "board_config -b"
    ERASE_BOARD_CONFIG_FMT = "board_config -e"
    SET_IBM_BOARD_CONFIG_FMT = "board_config -C {:s}{:s}"
    ZEPHYR_BOARD_CONFIG_WRITE_FMT =  "board_config write {:s}"
    ZEPHYR_BOARD_CONFIG_DUMP_FMT =  "board_config dump"
    ZEPHYR_BOARD_CONFIG_ERASE_FMT =  "board_config erase"
    ZEPHYR_FW_SELECT_FMT =  "debug update firmware --next-boot {:s}"
    ZEPHYR_SHOW_VERSION_FMT =  "show version"
    NIC_CFG_DUMP_FMT = "dd if=/dev/mtd{:s} of=cfg{:s} bs=64k"
    NIC_CFG_CHECKSUM_FMT = "md5sum cfg{:s}"
    NIC_CHK_SECBOOT_FMT = "/data/nic_util/elba-chk-secboot-rdy.sh"
    NIC_GET_QSPI_PARTITION_FMT = "cat /proc/mtd"
    NIC_ERASE_QSPI_PARTITION_FMT = "flash_erase /dev/mtd{:d} 0 0"
    NIC_GET_EMMC_PARTITION_FMT = "sgdisk -p /dev/mmcblk0"
    NIC_ERASE_EMMC_PARTITION_FMT = "dd if=/dev/zero of=/dev/mmcblk0p{:d} bs=512 count=16"
    NIC_ERASE_QSPI_FMT = "fpgautil flash {:s} 1 sectorerase all"
    NIC_DUMP_BOOT_FMT = "fpgautil flash {:s} 1 generatefile 0 0x100000 {:s}/{:s}_esec_backup.bin"
    SALINA_NIC_ERASE_BOOT0_FMT = "./qspi_erase_boot0.sh {:s}"
    SALINA_NIC_PROGRAM_BOOT0_FMT = "./qspi_prog_boot0.sh {:s}"
    SALINA_ESEC_QSPI_ERASE_FMT = "./esec_qspi_erase.sh {:s}"

    # Naples100: core_freq=833 arm_freq=1600
    NAPLES100_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 1600"
    NAPLES100_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 1600"
    # Naples100IBM: core_freq=833 arm_freq=1600
    NAPLES100IBM_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 1600"
    NAPLES100IBM_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 1600"
    # Naples100HPE: core_freq=833 arm_freq=1600
    NAPLES100HPE_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 1600"
    NAPLES100HPE_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 1600"
    # Naples100DELL: core_freq=833 arm_freq=1600
    NAPLES100DELL_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 1600"
    NAPLES100DELL_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 1600"
    # Vomero: core_freq=833 arm_freq=2200
    VOMERO_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 2200"
    VOMERO_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 2200"
    # Vomero2: core_freq=833 arm_freq=2200
    VOMERO2_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 2200"
    VOMERO2_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 2200"
    # Naples25: core_freq=417 arm_freq=1600
    NAPLES25_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 417 -arm_freq 1600"
    NAPLES25_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 417 -arm_freq 1600"
    # Naples25swm833: same as naples100
    NAPLES25SWM833_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 1600"
    NAPLES25SWM833_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 1600"
    # Ortano and Ortano2:
    ORTANO2_VRM_FIX_FMT = "/data/nic_util/fix_o2_vrm.sh"
    ORTANO_ORC_AVS_SET_FMT  = "tclsh set_avs_elb.tcl -sn {:s} -slot {:d} -core_freq 1033 -arm_freq 3000"
    ORTANO_PEN_AVS_SET_FMT  = "tclsh set_avs_elb.tcl -sn {:s} -slot {:d} -core_freq 1100 -arm_freq 3000"
    # Lacona/Pomonte:
    POMONTEDELL_AVS_SET_FMT  = "tclsh set_avs_elb.tcl -sn {:s} -slot {:d} -core_freq 833 -arm_freq 3000"
    LACONA32DELL_AVS_SET_FMT = "tclsh set_avs_elb.tcl -sn {:s} -slot {:d} -core_freq 833 -arm_freq 3000"
    LACONA32_AVS_SET_FMT     = "tclsh set_avs_elb.tcl -sn {:s} -slot {:d} -core_freq 833 -arm_freq 3000"
    #Ortano MSFT
    ORTANO2_VRM_FIX_OC_FMT = "/data/nic_util/fix_o2_vrm_oc.sh apply"
    # Ginestra
    GINESTRA_AVS_SET_FMT  = "tclsh set_avs_gig.tcl -sn {:s} -slot {:d} -core_freq 1100 -arm_freq 3000"
    # Salina
    SALINA_AVS_SET_FMT  = "tclsh set_avs_sal.tcl -slot {:d}"

    NIC_POWER_ON_FMT = "turn_on_slot.sh on {:d}"
    NIC_POWER_OFF_FMT = "turn_on_slot.sh off {:d}"
    MTP_POWER_ON_NIC_FMT = "turn_on_slot.sh on {:s}"
    MTP_POWER_OFF_NIC_FMT = "turn_on_slot.sh off {:s}"
    SALINA_MBIST_POWER_ON_FMT = "mbist_power_on.sh {:d}"

    MTP_RD_ALOM_CPLD_FMT = "smbutil -rd -addr=0x{:x} -uut='UUT_{:d}' -dev=CPLD_ADAP"
    MTP_WR_ALOM_CPLD_FMT = "smbutil -wr -addr=0x{:x} -data=0x{:x} -uut='UUT_{:d}' -dev=CPLD_ADAP"
    MTP_SMB_CMD_FMT = "smbutil -rd -addr=0x{:x} -uut='UUT_{:d}' -dev=CPLD"
    MTP_SMB_RD_CPLD_FMT = "smbutil -rd -addr=0x{:x} -uut='UUT_{:d}' -dev=CPLD"
    MTP_SMB_WR_CPLD_FMT = "smbutil -wr -addr=0x{:x} -data=0x{:x} -uut='UUT_{:d}' -dev=CPLD"
    MTP_SMB_RE = r"addr 0x%x; data=(0x[0-9a-fA-F]+)"
    MTP_SMB_SEL_FMT = "turn_on_hub.sh {:d}"

    NIC_POWER_CHECK_FMT = "inventory -ps -slot={:d}"
    NIC_POWER_RAIL_DISP_FMT = "inventory -pw -slot={:d}"
    NIC_PRESENT_DISP_FMT = "inventory -present"
    NIC_AVS_POST_FMT = "inventory -sts -slot {:d}"
    NIC_I2C_DUMP_POST_FMT = "i2cdump -y {:d} 0x4a"
    NIC_I2C_DUMP_4B_POST_FMT = "i2cdump -y {:d} 0x4b"

    NIC_ENA_ESEC_WRITE_PROT_FMT = "nic_test.py -ena_esec_wp -slot_list='{:s}'"
    NIC_DIS_ESEC_WRITE_PROT_FMT = "nic_test.py -dis_esec_wp -slot_list='{:s}'"

    NIC_CON_INIT_FMT = "nic_con.py -br -slot {:d}"
    NIC_CON_ATTACH_FMT = "con_connect.sh {:d}"
    NIC_MGMT_INIT_FMT = "nic_con.py -mgmt -slot {:d}"
    NIC_FPO_MGMT_INIT_FMT = "nic_con.py -mgmt -slot {:d} -fpo"
    NIC_CON_MTEST_FMT = "nic_con.py -mtest -slot {:d}"
    MTP_NIC_PCIE_LINK_POLL_DISABLE_FMT = "nic_con.py -dis_pcie -slot {:d}"
    MTP_NIC_PCIE_LINK_POLL_ENABLE_FMT = "nic_con.py -ena_pcie -slot {:d}"

    MTP_PARA_MGMT_INIT_FMT = "nic_test.py -setup_multi -mgmt -slot_list {:s} -asic_type {:s}"
    MTP_PARA_MGMT_AAPL_FMT = "nic_test.py -setup_multi -mgmt -slot_list {:s} -asic_type {:s} -aapl"
    MTP_PARA_MGMT_FPO_FMT  = "nic_test.py -setup_multi -mgmt -slot_list {:s} -asic_type {:s} -fpo"
    MTP_PARA_PRBS_ETH_TEST_FMT  = "nic_test.py -prbs  -slot_list='{:s}' -wtime=120 -vmarg {:s} -mode=eth"
    MTP_PARA_PRBS_ETH_ELBA_FMT  = "nic_test.py -prbs  -slot_list='{:s}' -wtime=180 -vmarg {:s} -mode=eth -dura=60 -asic_type=elba"
    MTP_PARA_PRBS_ETH_GIGLIO_FMT  = "nic_test.py -prbs  -slot_list='{:s}' -wtime=180 -vmarg {:s} -mode=eth -dura=60 -asic_type=giglio"
    MTP_PARA_SNAKE_HBM_FMT      = "nic_test.py -snake -slot_list='{:s}' -wtime=180 -vmarg {:s} -asic_type=capri -num_retry=5"
    MTP_PARA_SNAKE_PCIE_FMT     = "nic_test.py -snake -slot_list='{:s}' -wtime=180 -vmarg {:s} -asic_type=capri -mode=pcie -num_retry=5"
    MTP_PARA_SNAKE_ELBA_ORC_FMT = "nic_test.py -snake -slot_list='{:s}' -wtime=600 -vmarg {:s} -snake_num=4 -dura=3 -mode=hod -num_retry=5"
    MTP_PARA_SNAKE_ELBA_PEN_FMT = "nic_test.py -snake -slot_list='{:s}' -wtime=600 -vmarg {:s} -snake_num=4 -dura=3 -mode=hod_1100 -num_retry=5"
    MTP_PARA_SNAKE_LACONA_FMT   = "nic_test.py -snake -slot_list='{:s}' -wtime=300 -vmarg {:s} -snake_num=6 -dura=120 -mode=nod_525 -num_retry=5"
    MTP_PARA_SNAKE_ELBA_FMT     = "nic_test.py -snake -slot_list='{:s}' -wtime=600 -vmarg {:s} -snake_num=4 -dura=3 -mode=nod -num_retry=5"
    MTP_PARA_SNAKE_GIGLIO_FMT = "nic_test.py -snake -slot_list='{:s}' -wtime=600 -vmarg {:s} -snake_num=6 -dura=120 -mode=hod_1100  -num_retry=5"
    MTP_PARA_ARM_L1_ELBA_FMT             = "python2 arm_l1.py -arm_l1 -slot_list='{:s}' -wtime=30 -vmarg {:s} -mode={:s}"
    MTP_PARA_ARM_L1_ELBA_POMONTEDELL_FMT = "python2 arm_l1.py -arm_l1 -slot_list='{:s}' -wtime=30 -vmarg {:s} -mode=nod"
    MTP_PARA_ARM_L1_ELBA_LACONA_FMT      = "python2 arm_l1.py -arm_l1 -slot_list='{:s}' -wtime=30 -vmarg {:s} -mode=nod_525"
    MTP_PARA_PCIE_PRBS_FMT    = "python2 arm_prbs.py -arm_prbs -mode=PCIE -slot_list='{:s}' -wtime=360 -vmarg {:s} -dura=60 -poly={:s}"
    MTP_PARA_ETH_PRBS_FMT     = "python2 arm_prbs.py -arm_prbs -mode=MX   -slot_list='{:s}' -wtime=360 -vmarg {:s} -dura=60 -poly={:s}"
    MTP_PARA_DDR_BIST_ELBA_FMT = "python2 ddr_bist.py -arm_ddrbist -slot_list '{:s}' -wtime=780 -vmarg {:s}"
    MTP_NCSI_RMII_LINKUP_FMT = "nic_test.py -rmii_linkup_test   -slot_list='{:s}' -vmarg {:s}"
    MTP_NCSI_UART_LPBACK_FMT = "nic_test.py -uart_loopback_test -slot_list='{:s}' -vmarg {:s}"
    MTP_PARA_EDMA_ENV_INIT_FMT  = "python3 nic_test_v2.py check_edma -slot_list {:s}"

    #MATER MTP
    MATERA_MTP_SINGLE_MGMT_INIT_FMT = "nic_test_v2.py setup_single -slot {:s} -mgmt -asic_type {:s}"
    MATERA_SALINA_SINGLE_MGMT_INIT_FMT = "nic_test_v2.py setup_single -slot {:s} -mgmt -asic_type {:s} -no_pc"
    MATERA_MTP_SINGLE_MGMT_FPO_FMT = "nic_test_v2.py setup_single -slot {:s} -mgmt -asic_type {:s} -fpo"
    MATERA_MTP_SINGLE_INIT_FMT = "nic_test_v2.py setup_single -slot {:s} -asic_type {:s}"
    MATERA_MTP_PARA_PCIE_PRBS_FMT = "nic_test_v2.py nic_pcie_prbs_single -slot {:s} -vmarg {:s} -dura 120 -poly {:s} -mode PCIE"
    MATERA_MTP_PARA_SNAKE_ELBA_ORC_FMT = "nic_test_v2.py nic_snake_single -slot {:s} -snake_num 6 -dura 60 -timeout 700 -vmarg {:s} -mode hod -int_lpbk -verbose"
    MATERA_MTP_PARA_SNAKE_ELBA_PEN_FMT = "nic_test_v2.py nic_snake_single -slot {:s} -snake_num 6 -dura 60 -timeout 700 -vmarg {:s}  -mode hod_1100 -int_lpbk -verbose"
    MATERA_MTP_PARA_SNAKE_LACONA_FMT   = "nic_test_v2.py nic_snake_single -slot {:s} -snake_num 6 -dura 120 -timeout 500 -vmarg {:s} -mode nod_525 -int_lpbk -verbose"
    MATERA_MTP_PARA_SNAKE_ELBA_FMT     = "nic_test_v2.py nic_snake_single -slot {:s} -snake_num 6 -dura 60 -timeout 700 -vmarg {:s}  -mode nod -int_lpbk -verbose"
    MATERA_MTP_PARA_SNAKE_GIGLIO_FMT   = "nic_test_v2.py nic_snake_single -slot {:s} -snake_num 6 -dura 120 -timeout 700 -vmarg {:s} -mode=hod_1100 -int_lpbk -verbose"
    MATERA_NIC_SNAKE_MTP_FMT           = "nic_test_v2.py nic_snake_mtp -slot {:s} -timeout {:d} -dura {:d} -snake_type {:s} -vmarg {:s} -card_type {:s} -tcl_path '{:s}' -ite {:s} -int_lpbk {:s}"
    MATERA_NIC_MEM_TEST_MTP_FMT        = "nic_test_v2.py mem_test -slot {:s} -tcl_path {:s} -dura {:s} -vmarg {:s} -threads {:s}"
    MATERA_NIC_EDMA_MTP_FMT           = "nic_test_v2.py edma_test -slot {:s} -tcl_path {:s} -dura {:s} -vmarg {:s}"
    MATERA_NIC_EMMC_TEST_MTP_FMT           = "nic_test_v2.py salina emmc_test -slot {:s} -dura {:s} -ite {:s}"
    MATERA_AINIC_SNAKE_MTP_FMT         = "nic_test_v2.py nic_snake_mtp -slot {:s} -timeout {:d} -dura {:d} -snake_type {:s} -vmarg {:s} -card_type {:s} -tcl_path '{:s}' -ite {:s} -int_lpbk {:s} --lpmode 1"
    MATERA_NIC_PCIE_PRBS_FMT         = "nic_test_v2.py pcie_prbs -slot {:s} -vmarg {:s} -card_type {:s} -tcl_path '{:s}'"
    MATERA_MTP_NIC_BOOT_TO = "python3 sal_con.py --boot_to {:s} --slot {:s}"
    MATERA_MTP_PROG_DPU_DRU_FMT = "nic_test_v2.py prog_dpu_fru -slot {:s}  -skip_fru2"
    MATERA_MTP_SALINA_NIC_JTAG_MBIST = "tclsh jtag_screen.tcl -sn {:s} -slot {:s} -vmarg {:s} -reset {:s}"
    MATERA_MTP_SALINA_NIC_VRM_FIX_FMT = "nic_test_v2.py fix_sal_vrm -slot {:s}"
    MATERA_MTP_CLEAR_J2C_IF_LOCK = "/home/diag/diag/util/jtag_accpcie_salina clr {:s}"
    MATERA_SET_PCIEAWD_ENV_FMT         = "nic_test_v2.py salina pcieawd_env -slot {:s} -eqbk_en 1 -cmn_kp 56 -cmn_ki 9 -tx_prop_adj 1 -rx_prop_adj 4 -tx_mag 9 -rx_mag 9"
    MATERA_ERASE_PCIEAWD_ENV_FMT = "nic_test_v2.py salina pcieawd_env -slot {:s} -erase"
    MATERA_FIX_VRM_FMT         = "nic_test_v2.py fix_sal_vrm -slot {:s}"
    MATERA_I2C_QSFP_FMT         = "nic_test_v2.py test_spi -slot {:s} -vmarg {:s}"
    MATERA_I2C_RTC_FMT         = "tclsh sal_i2c_access.tcl -slot {:s} -vmarg {:s}"
    MATERA_L1_PRE_SETUP_FMT     = "tclsh sal_arm_freq.tcl -slot {:s}"

    MTP_PARA_UBOOT_ENV_FMT = "nic_test.py -setup_uboot_env -slot_list {:s}"
    MTP_PARA_INIT_FMT = "nic_test.py -setup_multi -slot_list {:s} -asic_type {:s}"
    MTP_DISP_ECC_FMT = "nic_test.py -disp_ecc -slot_list {:s}"
    MTP_HWCLOCK_WRITE_FMT = "hwclock -w"

    MTP_ARP_DELET_FMT = "arp -d {:s}"
    MTP_NIC_MAC_DISP_FMT = "arp -n -i enp2s0"
    MTP_NIC_PING_FMT = "ping -c 4 {:s}"
    MATERA_MTP_NIC_MAC_DISP_FMT = "arp -n -i enp3s0f1"

    MTP_DIAG_INIT_FMT = "/home/diag/start_diag.sh"
    NIC_DIAG_INIT_FMT = "/home/diag/start_diag.arm64.sh {:d}"
    NIC_DIAG_FINI_FMT = "rm -r /data/debug*"
    NIC_DIAG_CHECK_HAL_FMT = "ps -elf | grep hal"
    NIC_DIAG_STOP_SYSMGR_FMT = "killall sysmgr"
    NIC_DIAG_STOP_SYSMOND_FMT = "killall sysmond"
    NIC_DIAG_STOP_HAL_FMT = "killall hal"
    NIC_DIAG_STOP_TCLSH_FMT = "killall tclsh"
    NIC_DIAG_STOP_PICOCOM_FMT = "killall -9 picocom"
    NIC_DIAG_CHECK_PICOCOM_FMT = "ps -elf | grep picocom"
    NIC_DIAG_CONFIG_FMT = "source /data/nic_arm/nic_config.sh"

    MTP_DIAG_MGR_START_FMT = "nohup diagmgr > {:s} 2>&1 &"
    MTP_DIAG_MGR_RESTART_FMT = "nohup diagmgr >> {:s} 2>&1 &"
    MTP_DSP_START_FMT = "/home/diag/diag/python/infra/dshell/diag -r -c MTP1 -d diagmgr -t dsp_start"
    MTP_DSP_STOP_FMT = "/home/diag/diag/python/infra/dshell/diag -r -c MTP1 -d diagmgr -t dsp_stop"
    MTP_ZMQ_START_FMT = "/home/diag/diag/python/infra/dshell/diag -rc -c MTP1 -d ASIC -t start_zmq"
    MTP_ZMQ_STOP_FMT = "/home/diag/diag/python/infra/dshell/diag -rc -c MTP1 -d ASIC -t stop_zmq"
    MTP_DSP_CLEANUP_FMT = "/home/diag/diag/python/infra/dshell/diag -csys"
    MTP_DSP_DISP_FMT = "/home/diag/diag/python/infra/dshell/diag -sdsp"
    MTP_DSP_PARAM_FMT = "/home/diag/diag/python/infra/dshell/diag -param {:s}"
    MTP_DIAG_RUN_FMT = "/home/diag/diag/python/infra/dshell/diag -r -c {:s}"
    MTP_DIAG_RSLT_FMT = "/home/diag/diag/python/infra/dshell/diag -sresult -c {:s}"
    MTP_DIAG_SHIST_FMT = "/home/diag/diag/python/infra/dshell/diag -shist"
    MTP_DIAG_CHIST_FMT = "/home/diag/diag/python/infra/dshell/diag -chist"

    NIC_DSP_START_FMT = "/home/diag/diag/python/infra/dshell/diag -r -c NIC{:d} -d diagmgr -t dsp_start"

    NIC_KILL_PROCESS_FMT = "kill -9 -1"
    NIC_SYNC_FS_FMT = "sync"
    NIC_SW_UMOUNT_FMT = "/etc/init.d/S09mount stop"
    NIC_OS_SHUTDOWN_FMT = "poweroff"
    NIC_OS_SHUTDOWN_PEN_FMT = "penvisorctl execute poweroff"

    MFG_LOG_PKG_FMT = "tar czf {:s} -C {:s} {:s}"
    MFG_MK_DIR_FMT = "mkdir -p {:s}"
    MFG_MK_DIR_777_FMT = "mkdir -m777 -p {:s}"          #mkdir with chown 777: rwx privileges
    MFG_LOG_LINK_FMT = "ln {:s} {:s}"
    MFG_DIR_LINK_FMT = "ln -s {:s} {:s}"

    FST_DIAG_CMD_FMT = "/home/diag/mtp_fst_script/diag_fst_test.py"
    FST_DIAG_CMD_FMT_CLD = "/home/diag/mtp_fst_script/diag_fst_test.py -card_type {} -stage {} -fst {:d}"
    NIC_SW_PROFILE_CMD_FMT = "/{:s}"
    NIC_SW_MODE_SWITCH_FMT = "device_conf_gen.sh switch"
    NIC_SW_DEVICE_CHK_FMT = "pdsctl show device"
    NIC_SW_SYSTEM_CHK_FMT = "pdsctl show system"

    NIC_L1_HEALTH_CHECK = "tclsh /home/diag/diag/scripts/asic/l1_test.tcl {:s} {:d} hod 1 normal 0 1 0 1"

    NIC_MVL_ACC_FMT = "{:s}mvl_acc.sh"
    NIC_MVL_STUB_FMT = "{:s}mvl_stub.sh 0"
    NIC_MVL_LINK_FMT = "{:s}mvl_link.sh"
    NIC_FPGA_PHY_TEST_FMT = "{:s}xcvr_phy_intf.sh PRBS"
    NIC_FPGA_PHY_LINK_TEST_FMT = "{:s}xcvr_phy_intf.sh LINKUP"
    NIC_MVL_LINK_CAPRI_FMT = "{:s}mvl_link_capri.sh {:s}"
    NIC_EDMA_TEST_FMT = "{:s}run_edma.sh"
    NIC_I2C_DETECT_FMT = "i2cdetect -y -r {:d}"
    MTP_DEVICE_MARGIN_SET_FMT = "devmgr_v2 margin -d {:s} -p {:d}"
    MTP_STOP_REDIS_FMT = "systemctl stop redis-server"

    def __init__(self, cmdMapStr=None, cmdMapType='dpn'):
        self.cmdMapStr = cmdMapStr
        self.cmdMapType = cmdMapType
        if self.cmdMapStr is not None:
            if self.cmdMapType.lower() == 'dpn':
                from libdefs_dpn_based_mfg_diag_cmd import  dpnMfgDiagCmd
                if self.cmdMapStr in dpnMfgDiagCmd:
                    for k, v in dpnMfgDiagCmd[self.cmdMapStr].__dict__.items():
                        if not callable(v) and not k.startswith("__"):
                            setattr(self, k, v)

class MFG_DIAG_SIG:
    MTP_DIAG_OK_SIG = "Set up diag amd64 -- Done"
    MTP_DSP_START_OK_SIG = "Test Done: MTP1:DIAGMGR:DSP_START"
    MTP_ZMQ_OK_SIG = "SUCCESS"
    MTP_VRM_OK_SIG = "TEST PASSED"
    MTP_FAN_OK_SIG = "TEST PASSED"
    MTP_PSU1_OK_SIG = "PSU_1 TEST PASSED"
    MTP_PSU2_OK_SIG = "PSU_2 TEST PASSED"    
    MTP_PARA_TEST_SIG = "TEST RESULT:"
    MTP_FAN0_PRSNT_SIG = "Fan 0 is present"
    MTP_FAN1_PRSNT_SIG = "Fan 1 is present"
    MTP_FAN2_PRSNT_SIG = "Fan 2 is present"
    MTP_PRSNT_SIG = "TEST PASSED"
    NIC_CON_OK_SIG = "# stty speed 4800"
    NIC_MGMT_OK_SIG = "Management port is ready"
    NIC_PARTITION_OK_SIG = "setting OTP PARTITION_SETTING_COMPLETED!"
    NIC_PARTITION1_OK_SIG = "Device is already partitioned"
    NIC_EMMC_PERF_MODE_OK_SIG = "0"
    NIC_EMMC_HWRESET_PASS_SIG = "H/W reset function [RST_N_FUNCTION]: 0x01"
    NIC_EMMC_HWRESET_FAIL_SIG = "H/W reset function [RST_N_FUNCTION]: 0x00"
    NIC_EMMC_BKOPS_PASS_SIG = "Enable background operations handshake [BKOPS_EN]: 0x02"
    NIC_EMMC_BKOPS_FAIL_SIG = "Enable background operations handshake [BKOPS_EN]: 0x00"
    NIC_FWUPDATE_INIT_EMMC_PASS_SIG = "Creating EXT4 filesystem on /dev/mmcblk0p10"
    NIC_AAPL_OK_SIG = "AAPL setup done"
    NIC_MGMT_PARA_SIG = "=== Setup env top"
    NIC_PARA_SIG = "=== Setup env top"
    MATERA_NIC_MGMT_PARA_SIG = "=== Setup env"
    MATERA_NIC_SALINA_JTAG_MBIST_SIG = "JTAG TESTS PASSED"
    MATERA_NIC_SNAKE_MTP_SIG = "SNAKE TEST PASSED"
    MATERA_NIC_MEM_TEST_MTP_SIG = "GOOGLE STRESS TEST PASSED"
    MATERA_NIC_EMMC_TEST_MTP_SIG = "('Test Ite:', {:d}, ' PASSED')"
    MATERA_NIC_EDMA_MTP_SIG = "EDMA test PASSED"
    MATERA_AINIC_SNAKE_MTP_SIG = "SNAKE TEST PASSED"
    MATERA_AINIC_PCIE_PRBS_SIG = "PRBS test PASSED"
    MATERA_SALINA_FIX_VRM_SIG = "VRM mask applied successfully"
    MATERA_I2C_QSFP_SIG = "QSFP READ TEST PASSED"
    MATERA_I2C_RTC_SIG = "I2C ACCESS TEST PASSED"
    NIC_PARA_EDMA_ENV_INIT_SIG = "EDMA Checking Done"
    NIC_HAL_RUNNING_SIG = "/nic/bin/hal"
    NIC_CON_MTEST_PASS_SIG = "=== MTEST PASSED ==="
    NIC_POWER_OK_SIG = "power good"
    NIC_OS_SHUTDOWN_OK_SIG = "halted"
    NIC_MOUNT_OK_SIG = "/dev/mmcblk0p10 on /data"
    NIC_EFUSE_PROG_SIG = "EFUSE PROG PASSED"
    NIC_EFUSE_PROG_FAIL_SIG = "EFUSE PROG FAILED"
    NIC_HMAC_BEEN_PROG_SIG = "HMAC HAS BEEN PROGRAMMED"
    NIC_HMAC_NOT_PROG_SIG = "HMAC HAS NOT BEEN PROGRAMMED"
    NIC_ESEC_PROG_PRE_SIG = "IMG PROG PASSED"
    NIC_ESEC_PROG_SIG = "ESEC PROG/VALICATION PASSED"
    NIC_ESEC_CPLD_VERIFY_SIG = "EK validated"
    NIC_SALINA_ESEC_CPLD_VERIFY_SIG = "EK VALIDATION PASSED"
    NIC_ESEC_PROG_SIG = "ESEC PROG/VALICATION PASSED"
    NIC_ESEC_DICE_PROG_SIG = "ESEC PROG PASSED"
    NIC_ESEC_PENTRUST_PASS_SIG = "DICE IMG PROG PASSED"
    NIC_ESEC_PENTRUST_FAIL_SIG = "DICE IMG PROG FAILED"
    NIC_ESEC_DICE_CERT_SIG = "DICE VALIDATION PASSED"
    NIC_ESEC_J2C_FAIL_SIG = "CHECK WITH J2C ERROR"
    NIC_FWUPDATE_FAIL_SIG = "FATAL"
    NIC_SYSUPDATE_MAINFW_PASS_SIG = "Setting startup firmware to mainfw"
    NIC_UBOOT_PCIE_ENA_SIG = "setenv pcie_poll_disable"
    NIC_UBOOT_PCIE_DIS_SIG = "setenv pcie_poll_disable 1"
    NIC_SW_PROFILE_FAIL_SIG = "ERROR"
    MFG_DIAG_ERR_MSG_SIG = "[ERROR]"
    MFG_ASIC_ERR_MSG_SIG = "ERROR ::"
    MFG_ASIC_PASS_MSG_SIG = "#PASS#"
    MFG_ASIC_FAIL_MSG_SIG = "#FAIL#"
    MFG_ASIC_PASS_MSG2_SIG = "#PASSED#"
    MFG_ASIC_FAIL_MSG2_SIG = "#FAILED#"
    MFG_ASIC_CTC_ERR_MSG_SIG = "ERROR_CTC_WRITE_READ_COMPARE_FAILURE"
    MFG_ASIC_PCIE_MAPPING_MSG_SIG = "SBUS_PCIE_MAPPING"
    NIC_SW_DEVICE_CHK_SIG1 = "Device [P|p]rofile *: bitw-smart-switch"
    NIC_SW_DEVICE_CHK_SIG2 = "Operational [M|m]ode *: bitw-smart-switch"
    NIC_SW_SYSTEM_CHK_SIG1 = "Die id"
    NIC_MVL_ACC_SIG = "MVL ACC TEST PASSED"
    NIC_MVL_STUB_SIG = "MVL STUB TEST PASSED"
    NIC_MVL_LINK_SIG = "MVL RJ45 port link is up"
    NIC_MVL_LINK1_SIG = "MVL RJ45 port 1 link is up"
    NIC_MVL_LINK2_SIG = "MVL RJ45 port 2 link is up"
    NIC_FPGA_PHY_TEST_SIG = "TRANSCEIVER PHY INTERFACE TEST PASSED"
    NIC_FPGA_PHY_LINK_TEST_SIG = "TRANSCEIVER RJ45 port link is up"
    NIC_EDMA_TEST_SIG = "EDMA TEST PASSED"
    NIC_PARA_ASIC_L1_OK_SIG = "L1 TEST PASSED"
    NIC_PARA_ASIC_L1_FAIL_SIG = "L1 TEST FAILED"
    NIC_PARA_DDR_BIST_OK_SIG = "DDR BIST PASSED"
    NIC_L1_ESEC_PROG_OK_SIG = "L1 ESEC PROG PASSED"
    NIC_L1_PRE_SETUP_OK_SIG = "SAL_ARM_FREQ DONE"
    NIC_EMMC_CHECK_OK_SIG = "Partitioning Setting [PARTITION_SETTING_COMPLETED]: 0x01"
    NIC_ESEC_WRITE_PROT_SIG = "=== ena_dis_esec_wp done"
    NIC_ESEC_WRITE_PROT_OK_SIG = "=== ena_dis_esec_wp passed ==="
    SALINA_NIC_ERASE_BOOT0_OK_SIG = "QSPI ERASE PASSED"
    SALINA_NIC_PROG_BOOT0_OK_SIG = "QSPI PROG PASSED"
    SALINA_NIC_VMARG_SET = "vmarg set"
    NIC_OCP_RMII_OK_SIG = "RMII test PASSED"
    NIC_OCP_CON_OK_SIG = "Adapter Test PASSED"
    NIC_ESEC_HW_UNLOCK_OK_SIG = "Verification passed"
    NIC_PRP_TEST_SIG = "PRP TEST PASSED"

class MFG_DIAG_RE:
    MFG_NIC_TYPE_NAPLES100 = r"\bUUT_(\d+) +NAPLES100\b"
    MFG_NIC_TYPE_NAPLES25  = r"\bUUT_(\d+) +NAPLES25\b"
    MFG_NIC_TYPE_FORIO     = r"\bUUT_(\d+) +FORIO\b"
    MFG_NIC_TYPE_VOMERO    = r"\bUUT_(\d+) +VOMERO\b"
    MFG_NIC_TYPE_VOMERO2   = r"\bUUT_(\d+) +VOMERO2\b"
    MFG_NIC_TYPE_NAPLES25SWM = r"\bUUT_(\d+) +NAPLES25SWM\b"
    MFG_NIC_TYPE_NAPLES25OCP = r"\bUUT_(\d+) +NAPLES25OCP\b"
    MFG_NIC_TYPE_NAPLES100IBM = r"\bUUT_(\d+) +NAPLES100IBM\b"
    MFG_NIC_TYPE_NAPLES100HPE = r"\bUUT_(\d+) +NAPLES100HPE\b"
    MFG_NIC_TYPE_NAPLES100DELL = r"\bUUT_(\d+) +NAPLES100DELL\b"
    MFG_NIC_TYPE_NAPLES25SWMDELL = r"\bUUT_(\d+) +NAPLES25SWMDELL\b"
    MFG_NIC_TYPE_NAPLES25SWM833 = r"\bUUT_(\d+) +NAPLES25SWM833\b"
    MFG_NIC_TYPE_ORTANO = r"\bUUT_(\d+) +ORTANO\b"
    MFG_NIC_TYPE_ORTANO2 = r"\bUUT_(\d+) +ORTANO2\b"
    MFG_NIC_TYPE_POMONTEDELL = r"\bUUT_(\d+) +POMONTEDELL\b"
    MFG_NIC_TYPE_LACONA32DELL = r"\bUUT_(\d+) +LACONA32DELL\b"
    MFG_NIC_TYPE_LACONA32 = r"\bUUT_(\d+) +LACONA32\b"
    MFG_NIC_TYPE_ORTANO2ADI = r"\bUUT_(\d+) +ORTANO2A\b"
    MFG_NIC_TYPE_ORTANO2INTERP = r"\bUUT_(\d+) +ORTANO2I\b"
    MFG_NIC_TYPE_ORTANO2SOLO = r"\bUUT_(\d+) +ORTANO2S\b"
    MFG_NIC_TYPE_ORTANO2ADICR = r"\bUUT_(\d+) +ORTANO2AC\b"
    MFG_NIC_TYPE_GINESTRA_D4 = r"\bUUT_(\d+) +GINESTRA_D4\b"
    MFG_NIC_TYPE_GINESTRA_D5 = r"\bUUT_(\d+) +GINESTRA_D5\b"
    MFG_NIC_TYPE_MALFA = r"\bUUT_(\d+) +MALFA\b"
    MFG_NIC_TYPE_LENI = r"\bUUT_(\d+) +LENI\b"
    MFG_NIC_TYPE_LENI48G = r"\bUUT_(\d+) +LENI48G\b"
    MFG_NIC_TYPE_POLLARA = r"\bUUT_(\d+) +POLLARA\b"
    MFG_NIC_TYPE_LINGUA = r"\bUUT_(\d+) +LINGUA\b"
