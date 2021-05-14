from enum import Enum

class NIC_Type:
    NAPLES100 = "NAPLES100"
    NAPLES100IBM = "NAPLES100IBM"
    NAPLES100HPE = "NAPLES100HPE"
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
    UNKNOWN = "Unknown"


class NIC_Vendor:
    PENSANDO = "Pensando"
    HPE = "HPE"
    UNKNOWN = "Unknown"


class FLX_Factory:
    MILPITAS = "Milpitas"
    PENANG = "Penang"


class FF_Stage:
    FF_DL = "DL"
    FF_P2C = "P2C"
    FF_4C_H = "4C-H"
    FF_4C_L = "4C-L"
    FF_SWI = "SWI"
    FF_FST = "FST"
    FF_CFG = "CFG"


class FPN_FF_Stage:
    FF_CFG = "CFG"
    FF_DL = "PSO-DOWNLOAD_AUTO"
    FF_P2C = "PSO-P2C_AUTO"
    FF_4C_H = "PSO-4C-H_AUTO"
    FF_4C_L = "PSO-4C-L_AUTO"
    FF_SWI = "PSO-SWI_AUTO"
    FF_FST = "PSO-FST_AUTO"


class Env_Cond(Enum):
    MFG_QA = "QA"
    MFG_LT = "LT"
    MFG_NT = "NT"
    MFG_HT = "HT"
    MFG_RDT = "RDT"
    MFG_EDVT_HT = "EDVT_HT"
    MFG_EDVT_LT = "EDVT_LT"

    def __str__(self):
        return self.value

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

    MTPS_SLOT_NUM = 4

    MTP_POWER_ON_DELAY = 180
    MTP_POWER_ON_TIMEOUT = 6000
    MTP_REBOOT_DELAY = 120
    MTP_OS_SHUTDOWN_DELAY = 60
    MTP_POWER_CYCLE_DELAY = 30
    MTP_NETCOPY_DELAY = 600
    MTP_FRU_UPDATE_DELAY = 1200
    MTP_PARA_TEST_DELAY = 1800
    MTP_PARA_AAPL_INIT_DELAY = 1800
    OS_SYNC_DELAY = 300
    SSH_PASSWORD_DELAY = 30
    OS_CMD_DELAY = 600
    NIC_CON_CMD_DELAY = 900
    NIC_CON_INIT_DELAY = 60
    NIC_NETCOPY_DELAY = 120
    NIC_CON_CMD_RETRY = 10
    NIC_MGMT_IP_SET_DELAY = 3
    NIC_MGMT_IP_INIT_RETRY = 3
    NIC_SW_BOOTUP_DELAY = 120
    NIC_AVS_SET_DELAY = 600
    NIC_ESEC_PROG_DELAY = 1800
    NIC_EFUSE_PROG_DELAY = 1800
    NIC_POWER_ON_DELAY = 180
    NIC_POWER_OFF_DELAY = 10
    NIC_SYSRESET_DELAY = 180

    MTP_DIAGMGR_DELAY = 10
    MTP_MGMT_IP_SET_DELAY = 10

    # single test, 1.5 hours
    DIAG_TEST_TIMEOUT = 5400

    # more than 12 hours
    MFG_P2C_TEST_TIMEOUT = 48000
    # more than 24 hours
    MFG_4C_TEST_TIMEOUT = 96000
    # 4 hours
    MFG_DL_TEST_TIMEOUT = 14400
    # 2.5 hour SWM and IBM update to 6 hours
    MFG_SW_TEST_TIMEOUT = 21600
    # 1 hour
    MFG_FST_TEST_TIMEOUT = 3600
    MFG_CFG_TEST_TIMEOUT = 3600
    
    MFG_EDVT_HIGH_FAN_SPD = 90
    MFG_EDVT_NORM_FAN_SPD = 40
    MFG_EDVT_LOW_FAN_SPD = 40
    MFG_EDVT_HIGH_TEMP = 50
    MFG_EDVT_LOW_TEMP = 0
    MFG_EDVT_TEMP_DIFF = 5
    MFG_EDVT_HIGH_VOLT = 5
    MFG_EDVT_LOW_VOLT = -5
    MFG_TEMP_WAIT_TIMEOUT = 180
    MFG_TEMP_SOAK_TIMEOUT = 180
    MFG_TEMP_CHECK_INTERVAL = 10

    # MFG moduling parameters
    MFG_MODEL_EDVT_HIGH_FAN_SPD = 50
    MFG_MODEL_EDVT_LOW_FAN_SPD = 40
    MFG_MODEL_EDVT_HIGH_TEMP = 22
    MFG_MODEL_EDVT_LOW_TEMP = 22
    MFG_MODEL_TEMP_SOAK_TIMEOUT = 1


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
    ONBOARD_ASIC_LOG_FILES = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/*log"
    ONBOARD_CSP_LOG_FILES = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/*txt"
    ONBOARD_TEST_LOG_FILES = "/home/diag/mtp_regression/*log"
    ONBOARD_NIC_LOG_FILES = "/home/diag/diag/nic_log/*"
    ONBOARD_DL_LOG_FILES = "/home/diag/mtp_dl_script/*log /home/diag/mtp_dl_script/*yaml"
    ONBOARD_CFG_LOG_FILES = "/home/diag/mtp_cfg_script/*log /home/diag/mtp_cfg_script/*yaml"
    ONBOARD_SWI_LOG_FILES = "/home/diag/mtp_swi_script/*log"
    ONBOARD_FST_LOG_FILES = "/home/diag/mtp_fst_script/*log"
    ONBOARD_ASIC_LOG_DIR = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/"
    ONBOARD_NIC_LOG_DIR = "/home/diag/diag/nic_log/"
    NIC_ONBOARD_ASIC_LOG_DIR = "/data/nic_arm/nic/asic_src/ip/cosim/tclsh/"

    DIAG_QA_LOG_DIR = "/vol/hw/diag/diag_qa/regression_log/"
    DIAG_MFG_DL_LOG_DIR_FMT = "/mfg_log/{:s}/DL/{:s}/"
    DIAG_MFG_CFG_LOG_DIR_FMT = "/mfg_log/{:s}/CFG/{:s}/"
    DIAG_MFG_P2C_LOG_DIR_FMT = "/mfg_log/{:s}/P2C/{:s}/"
    DIAG_MFG_4C_LOG_DIR_FMT = "/mfg_log/{:s}/4C/{:s}/{:s}/"
    DIAG_MFG_SWI_LOG_DIR_FMT = "/mfg_log/{:s}/SWI/{:s}/"
    DIAG_MFG_FST_LOG_DIR_FMT = "/mfg_log/{:s}/FST/{:s}/"
    DIAG_MFG_CSP_LOG_DIR_FMT = "/mfg_log/CSP_REC/{:s}/"
    DIAG_MFG_MODEL_DL_LOG_DIR_FMT = "/tmp/mfg_log/{:s}/DL/{:s}/"
    DIAG_MFG_MODEL_CFG_LOG_DIR_FMT = "/tmp/mfg_log/{:s}/CFG/{:s}/"
    DIAG_MFG_MODEL_P2C_LOG_DIR_FMT = "/tmp/mfg_log/{:s}/P2C/{:s}/"
    DIAG_MFG_MODEL_4C_LOG_DIR_FMT = "/tmp/mfg_log/{:s}/4C/{:s}/{:s}/"
    DIAG_MFG_MODEL_SWI_LOG_DIR_FMT = "/tmp/mfg_log/{:s}/SWI/{:s}/"
    DIAG_MFG_MODEL_FST_LOG_DIR_FMT = "/tmp/mfg_log/{:s}/FST/{:s}/"
    DIAG_MFG_MODEL_CSP_LOG_DIR_FMT = "/tmp/mfg_log/CSP_REC/{:s}/"                                                                                                                             

    MFG_DL_LOG_PKG_FILE = "DL_{:s}_{:s}.tar.gz"
    MFG_DL_LOG_DIR = "DL_{:s}_{:s}/"
    MFG_CFG_LOG_PKG_FILE = "CFG_{:s}_{:s}.tar.gz"
    MFG_CFG_LOG_DIR = "CFG_{:s}_{:s}/"
    MFG_P2C_LOG_PKG_FILE = "NT_{:s}_{:s}.tar.gz"
    MFG_P2C_LOG_DIR = "NT_{:s}_{:s}/"
    MFG_4C_LOG_PKG_FILE = "{:s}_{:s}_{:s}.tar.gz"
    MFG_4C_LOG_DIR = "{:s}_{:s}_{:s}/"
    MFG_SWI_LOG_PKG_FILE = "SWI_{:s}_{:s}.tar.gz"
    MFG_SWI_LOG_DIR = "SWI_{:s}_{:s}/"
    MFG_FST_LOG_PKG_FILE = "FST_{:s}_{:s}.tar.gz"
    MFG_FST_LOG_DIR = "FST_{:s}_{:s}/"


class MTP_DIAG_Path:
    ONBOARD_MTP_DIAG_PATH = "/home/diag/"
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
    NIC_DIAG_SLOT_SKIPPED = "SKIPPING ALL TESTS ON THIS SLOT"
    MTP_DIAG_REGRESSION_FAIL = "MTP_DIAG_REGRESSION_TEST_FAIL"
    NIC_DIAG_REGRESSION_FAIL = "NIC_DIAG_REGRESSION_TEST_FAIL"
    NIC_DIAG_REGRESSION_PASS = "NIC_DIAG_REGRESSION_TEST_PASS"
    NIC_DIAG_REGRESSION_SKIP = "NIC_DIAG_REGRESSION_TEST_SKIP"
    NIC_DIAG_REGRESSION_RSLT_RE = r"NIC-(\d{{2}}) (\w+) (\w+) {:s}"
    NIC_DIAG_REGRESSION_SKIP_RSLT_RE = r"NIC-(\d{{2}}) {:s}" #SKIP doesnt have type and sn

class MFG_DIAG_CMDS:
    MTP_DIAG_VERSION_FMT = "version"
    MTP_LOGIN_VERIFY_FMT = "echo $USER"
    MTP_ASIC_VERSION_FMT = "head /home/diag/diag/asic/asic_version.txt"
    MTP_REV_FMT =  "env | grep MTP_REV | cat"
    MTP_ASIC_SUPPORTED_FMT =  "env | grep MTP_TYPE | cat"
    MTP_FAN_STATUS_FMT = "devmgr -dev FAN -status"
    MTP_FAN_SET_SPD_FMT = "devmgr -dev=fan -speed -pct={:d}"
    MTP_VRM_TEST_FMT = "mtptest -vrm"
    MTP_FAN_TEST_FMT = "mtptest -fanspd"
    MTP_FAN_PRSNT_FMT = "mtptest -present"

    MTP_CPLD_READ_FMT = "cpldutil -cpld-rd -addr=0x{:x}"

    MTP_FRU_PROG_FMT = "eeutil -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -uut=UUT_{:d} -update"
    MTP_HP_FRU_PROG_FMT = "eeutil -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -uut=UUT_{:d} -update -hpe"
    MTP_HP_SWM_FRU_PROG_FMT = "eeutil -dev=fru -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -uut=UUT_{:d} -update -erase -numBytes=256 -hpeSwm"
    MTP_HP_OCP_FRU_PROG_FMT = "eeutil -dev=fru -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -uut=UUT_{:d} -update -erase -numBytes=256 -hpeOcp"
    MTP_HP_ALOM_FRU_PROG_FMT = "eeutil -dev=fru -date='{:s}' -sn='{:s}' -pn='{:s}' -uut=UUT_{:d} -update -erase -numBytes=1024 -hpeAlom"
    MTP_ORTANO_FRU_PROG_FMT = "eeutil -dev=fru -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -uut=UUT_{:d} -update -erase -numBytes=512"
    MTP_FRU_DISP_FMT = "eeutil -uut=UUT_{:d} -disp"
    MTP_HP_FRU_DISP_FMT = "eeutil -uut=UUT_{:d} -disp -hpe"
    MTP_HP_OCP_FRU_DISP_FMT = "eeutil -uut=UUT_{:d} -disp -dev=fru -hpeOcp"
    MTP_HP_SWM_FRU_DISP_FMT = "eeutil -uut=UUT_{:d} -disp -dev=fru -hpeSwm"
    MTP_HP_ALOM_FRU_DISP_FMT = "eeutil -uut=UUT_{:d} -disp -dev=fru -hpeAlom"
    NIC_FRU_PROG_FMT = "{:s}eeutil -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -update"
    NIC_HP_SWM_FRU_PROG_FMT = "{:s}eeutil -dev=fru -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -update -erase -numBytes=256 -hpeSwm"
    NIC_HP_OCP_FRU_PROG_FMT = "{:s}eeutil -dev=fru -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -update -erase -numBytes=256 -hpeOcp"
    NIC_HP_ALOM_FRU_PROG_FMT = "{:s}eeutil -dev=fru -date='{:s}' -sn='{:s}' -pn='{:s}' -update -erase -numBytes=1024 -hpeAlom"
    NIC_HP_FRU_PROG_FMT = "{:s}eeutil -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -update -hpe"
    NIC_ORTANO_FRU_PROG_FMT = "{:s}eeutil -dev=fru -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -update -erase -numBytes=512"
    NIC_FRU_DISP_FMT = "{:s}eeutil -disp"
    NIC_HP_FRU_DISP_FMT = "{:s}eeutil -disp -hpe"
    NIC_HP_SWM_FRU_DISP_FMT = "{:s}eeutil -disp -dev=fru -hpeSwm"
    NIC_HP_OCP_FRU_DISP_FMT = "{:s}eeutil -disp -dev=fru -hpeOcp"
    NIC_HP_ALOM_FRU_DISP_FMT = "{:s}eeutil -disp -dev=fru -hpeAlom"
    NIC_VENDOR_DISP_FMT_SWM = "{:s}eeutil -disp -field=sn -hpeSwm"
    NIC_VENDOR_DISP_FMT_OCP = "{:s}eeutil -disp -field=sn -hpeOcp"
    NIC_HPESWM_ALOM_FRU_DISP_FMT = "eeutil -disp -uut=UUT_{:d} -hpeAlom"
    NIC_VENDOR_DISP_FMT = "{:s}eeutil -disp -field=sn"
    NIC_HPESWM_VENDOR_DISP_FMT = "{:s}eeutil -disp -field=sn -hpeSwm"

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
    NIC_SETTING_PARTITION_FMT = "mmc enh_area set -y 0 30998528 /dev/mmcblk0"
    NIC_DIAG_ASIC_VERSION_FMT = "head /data/nic_arm/{:s}/asic_version.txt"
    # onboard diag utils version
    NIC_DIAG_UTIL_VERSION_FMT = "head /data/nic_util/version.txt"
    # copied diag version
    NIC_DIAG_VERSION_FMT = "head /home/diag/diag/scripts/version.txt"
    # NIC HAL process
    NIC_HAL_RUNNING_FMT = "ps | grep hal"

    NIC_MOUNT_EMMC_FMT = "mount /dev/mmcblk0p10 /data"
    NIC_FSCK_EMMC_FMT = "fsck -y /dev/mmcblk0p10"
    NIC_DIAG_CLEANUP_FMT = "rm -rf /data/nic*"
    NIC_EMMC_LS_FMT = "ls -al /data/"
    NIC_PARTITION_DISP_FMT = "fdisk -l"
    NIC_MOUNT_DISP_FMT = "mount | grep '/dev/mmcblk0p10'"
    NIC_QSPI_PROG_FMT = "fwupdate -p /{:s} -i 'all'"
    NIC_DIAGFW_PROG_FMT = "fwupdate -p /{:s} -i diagfw"
    NIC_GOLDFW_PROG_FMT = "cd /; tar xvf {:s}; ./fwupdate -p {:s} -i all"
    NIC_EMMC_INIT_FMT = "fwupdate --init-emmc"
    NIC_EMMC_PERF_MODE = "touch /sysconfig/config0/.perf_mode"
    NIC_EMMC_PERF_MODE_CHECK = "[[ -f /sysconfig/config0/.perf_mode ]] ; echo $?"
    NIC_EMMC_PROG_FMT_NAPLES100 = "fwupdate -p /data/{:s} -i 'uboot mainfwa mainfwb'"
    NIC_GOLDFW_PROG_FMT_NAPLES100 = "fwupdate -p /{:s} -i goldfw"
    NIC_EMMC_PROG_FMT = "cd /data; tar xvf {:s}; ./fwupdate -p /data/{:s} -i 'all'"
    NIC_EMMC_B_PROG_FMT = "cd /data; tar xvf {:s}; ./fwupdate -p /data/{:s} -i mainfwb"
    NIC_BOOT_DISP_FMT = "fwupdate -r"
    NIC_IMG_DISP_FMT = "fwupdate -L"
    NIC_IMG_DISP1_FMT = "fwupdate -l"
    NIC_SET_SW_BOOT_FMT = "fwupdate -s mainfwa"
    NIC_SET_DIAG_BOOT_FMT = "fwupdate -s diagfw"
    NIC_SET_GOLD_BOOT_FMT = "fwupdate -s goldfw"
    NIC_SET_MGMT_IP_FMT = "ifconfig oob_mnic0 10.1.1.{:d} netmask 255.255.255.0"
    NIC_DATE_SET_FMT = "date --set='{:s}'"
    NIC_SCP_COMPRESSED_FMT = "tar c -C {:s} {:s} | ssh {:s}@{:s} {:s} \"tar x -C {:s}\"" #format(srcdir,img,user,ip,sshoptions,dstdir)
    NIC_SYS_CLEAN_FMT = "{:s}scripts/sys_clean.sh"

    NIC_ESEC_ERR_CHECK_FMT        = "inventory -esec -slot {:d}"
    NIC_ESEC_PROG_PRE_FMT         = "./esec_ctrl.py -slot {:d} -img_prog"
    NIC_ESEC_PROG_POST_FMT        = "./esec_ctrl.py -cleanup"
    NIC_ESEC_CPLD_CHECK_FMT       = "./esec_ctrl.py -check_uboot -slot {:d} -post_check"
    NIC_EFUSE_PROG_ELBA_MODEL_FMT = "./esec_ctrl.py -efuse_prog -d -slot {:d} -sn {:s} -pn '{:s}' -mac {:s} -brd_name {:s}"
    NIC_EFUSE_PROG_ELBA_FMT       = "./esec_ctrl.py -efuse_prog -slot {:d} -sn {:s} -pn '{:s}' -mac {:s} -brd_name {:s}"
    NIC_ESEC_PROG_FMT             = "./esec_ctrl.py -esec_prog -slot {:d} -sn {:s} -pn '{:s}' -mac {:s} -brd_name {:s} -mtp {:s}"
    NIC_ESEC_PROG_ELBA_FMT        = "./esec_ctrl.py -esec_prog -slot {:d} -sn {:s} -pn '{:s}' -mac {:s} -brd_name {:s} -mtp {:s} -fast"
    NIC_ESEC_PROG_DUMP_FMT        = "./esec_ctrl.py -show_sts -sn {:s} -slot {:d} -brd_name {:s}"

    NIC_IMG_VER_DISP_FMT = "cat /proc/version | sed 's/.*SMP/SMP/'"
    MTP_IMG_VER_DISP_FMT = "cat /proc/version | sed 's/.*SMP/SMP/'"
    NIC_VMARG_SET_FMT = "/home/diag/diag/scripts/vmarg.sh {:s}"
    NIC_DISP_VOLT_FMT = "devmgr -status"

    # Naples100: core_freq=833 arm_freq=1600
    NAPLES100_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 1600"
    NAPLES100_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 1600"
    # Naples100IBM: core_freq=833 arm_freq=1600
    NAPLES100IBM_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 1600"
    NAPLES100IBM_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 1600"
    # Naples100HPE: core_freq=833 arm_freq=1600
    NAPLES100HPE_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 1600"
    NAPLES100HPE_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 1600"
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

    NIC_POWER_ON_FMT = "turn_on_slot.sh on {:d}"
    NIC_POWER_OFF_FMT = "turn_on_slot.sh off {:d}"
    MTP_POWER_ON_NIC_FMT = "turn_on_slot.sh on all"
    MTP_POWER_OFF_NIC_FMT = "turn_on_slot.sh off all"


    MTP_RD_ALOM_CPLD_FMT = "smbutil -rd -addr=0x{:x} -uut='UUT_{:d}' -dev=CPLD_ADAP"
    MTP_WR_ALOM_CPLD_FMT = "smbutil -wr -addr=0x{:x} -data=0x{:x} -uut='UUT_{:d}' -dev=CPLD_ADAP"
    MTP_SMB_CMD_FMT = "smbutil -rd -addr=0x{:x} -uut='UUT_{:d}' -dev=CPLD"
    MTP_SMB_RD_CPLD_FMT = "smbutil -rd -addr=0x{:x} -uut='UUT_{:d}' -dev=CPLD"
    MTP_SMB_WR_CPLD_FMT = "smbutil -wr -addr=0x{:x} -data=0x{:x} -uut='UUT_{:d}' -dev=CPLD"
    MTP_SMB_RE = r"addr 0x%x; data=(0x[0-9a-fA-F]+)"
    MTP_SMB_SEL_FMT = "turn_on_uut.sh {:d}"

    NIC_POWER_CHECK_FMT = "inventory -ps -slot={:d}"
    NIC_POWER_RAIL_DISP_FMT = "inventory -pw -slot={:d}"
    NIC_PRESENT_DISP_FMT = "inventory -present"
    NIC_AVS_POST_FMT = "inventory -sts -slot {:d}"

    NIC_CON_INIT_FMT = "nic_con.py -br -slot {:d}"
    NIC_CON_ATTACH_FMT = "con_connect.sh {:d}"
    NIC_MGMT_INIT_FMT = "nic_con.py -mgmt -slot {:d}"
    NIC_FPO_MGMT_INIT_FMT = "nic_con.py -mgmt -slot {:d} -fpo"
    NIC_CON_MTEST_FMT = "nic_con.py -mtest -slot {:d}"
    MTP_NIC_PCIE_LINK_POLL_DISABLE_FMT = "nic_con.py -dis_pcie -slot {:d}"
    MTP_NIC_PCIE_LINK_POLL_ENABLE_FMT = "nic_con.py -ena_pcie -slot {:d}"

    MTP_PARA_MGMT_INIT_FMT = "nic_test.py -setup_multi -mgmt -slot_list {:s} -asic_type {:s}"
    MTP_PARA_MGMT_AAPL_FMT = "nic_test.py -setup_multi -mgmt -slot_list {:s} -asic_type {:s} -aapl"
    MTP_PARA_PRBS_ETH_TEST_FMT  = "nic_test.py -prbs  -slot_list='{:s}' -wtime=120 -vmarg {:d} -mode=eth"
    MTP_PARA_SNAKE_HBM_FMT      = "nic_test.py -snake -slot_list='{:s}' -wtime=180 -vmarg {:d}"
    MTP_PARA_SNAKE_PCIE_FMT     = "nic_test.py -snake -slot_list='{:s}' -wtime=180 -vmarg {:d} -mode=pcie"
    MTP_PARA_SNAKE_ELBA_ORC_FMT = "nic_test.py -snake -slot_list='{:s}' -wtime=300 -vmarg {:d} -mode=hod"
    MTP_PARA_SNAKE_ELBA_PEN_FMT = "nic_test.py -snake -slot_list='{:s}' -wtime=300 -vmarg {:d} -mode=hod_1100"
    MTP_PARA_UBOOT_ENV_FMT = "nic_test.py -setup_uboot_env -slot_list {:s}"

    MTP_ARP_DELET_FMT = "arp -d {:s}"
    MTP_NIC_MAC_DISP_FMT = "arp -n -i enp2s0"
    MTP_NIC_PING_FMT = "ping -c 4 {:s}"

    MTP_DIAG_INIT_FMT = "/home/diag/start_diag.sh"
    NIC_DIAG_INIT_FMT = "/home/diag/start_diag.arm64.sh {:d}"
    NIC_DIAG_FINI_FMT = "rm -r /data/debug*"
    NIC_DIAG_STOP_HAL_FMT = "killall hal"
    NIC_DIAG_STOP_TCLSH_FMT = "killall tclsh"
    NIC_DIAG_STOP_PICOCOM_FMT = "killall picocom"
    NIC_DIAG_CONFIG_FMT = "source /data/nic_arm/nic_config.sh"

    MTP_DIAG_MGR_START_FMT = "nohup diagmgr > {:s} 2>&1 &"
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

    MFG_LOG_PKG_FMT = "tar czf {:s} -C {:s} {:s}"
    MFG_MK_DIR_FMT = "mkdir -p {:s}"
    MFG_MK_DIR_777_FMT = "mkdir -m777 -p {:s}"          #mkdir with chown 777: rwx privileges
    MFG_LOG_LINK_FMT = "ln {:s} {:s}"

    FST_DIAG_CMD_FMT = "/home/diag/mtp_fst_script/diag_fst_test.py"
    FST_DIAG_CMD_FMT_CLD = "/home/diag/mtp_fst_script/diag_fst_test.py -card_type {} -stage {} -fst {:d}"
    NIC_SW_PROFILE_CMD_FMT = "/{:s}"
    NIC_SW_MODE_SWITCH_FMT = "device_conf_gen.sh switch"
    NIC_SW_DEVICE_CHK_FMT = "pdsctl show device"

class MFG_DIAG_SIG:
    MTP_DIAG_OK_SIG = "Set up diag amd64 -- Done"
    MTP_DSP_START_OK_SIG = "Test Done: MTP1:DIAGMGR:DSP_START"
    MTP_ZMQ_OK_SIG = "SUCCESS"
    MTP_VRM_OK_SIG = "TEST PASSED"
    MTP_FAN_OK_SIG = "TEST PASSED"
    MTP_PARA_TEST_SIG = "TEST RESULT:"
    MTP_FAN0_PRSNT_SIG = "Fan 0 is present"
    MTP_FAN1_PRSNT_SIG = "Fan 1 is present"
    MTP_FAN2_PRSNT_SIG = "Fan 2 is present"
    NIC_CON_OK_SIG = "# stty speed 4800"
    NIC_MGMT_OK_SIG = "Management port is ready"
    NIC_PARTITION_OK_SIG = "setting OTP PARTITION_SETTING_COMPLETED!"
    NIC_PARTITION1_OK_SIG = "Device is already partitioned"
    NIC_EMMC_PERF_MODE_OK_SIG = "0"
    NIC_AAPL_OK_SIG = "AAPL setup done"
    NIC_MGMT_PARA_SIG = "=== Setup env top"
    NIC_HAL_RUNNING_SIG = "/nic/bin/hal"
    NIC_CON_MTEST_PASS_SIG = "=== MTEST PASSED ==="
    NIC_POWER_OK_SIG = "power good"
    NIC_OS_SHUTDOWN_OK_SIG = "halted"
    NIC_MOUNT_OK_SIG = "/dev/mmcblk0p10 on /data"
    NIC_EFUSE_PROG_SIG = "EFUSE PROG PASSED"
    NIC_EFUSE_PROG_FAIL_SIG = "EFUSE PROG FAILED"
    NIC_ESEC_PROG_PRE_SIG = "IMG PROG PASSED"
    NIC_ESEC_PROG_SIG = "ESEC PROG/VALICATION PASSED"
    NIC_ESEC_CPLD_VERIFY_SIG = "EK validated"
    NIC_FWUPDATE_FAIL_SIG = "FATAL"
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
    NIC_SW_DEVICE_CHK_SIG1 = "Device Profile *: bitw-smart-switch"
    NIC_SW_DEVICE_CHK_SIG2 = "Operational Mode *: bitw-smart-switch"

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
    MFG_NIC_TYPE_NAPLES25SWMDELL = r"\bUUT_(\d+) +NAPLES25SWMDELL\b"
    MFG_NIC_TYPE_NAPLES25SWM833 = r"\bUUT_(\d+) +NAPLES25SWM833\b"
    MFG_NIC_TYPE_ORTANO = r"\bUUT_(\d+) +ORTANO\b"
    MFG_NIC_TYPE_ORTANO2 = r"\bUUT_(\d+) +ORTANO2\b"

