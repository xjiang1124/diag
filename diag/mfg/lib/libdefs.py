from enum import Enum

class NIC_Type:
    NAPLES100 = "NAPLES100"
    NAPLES25 = "NAPLES25"
    FORIO = "FORIO"
    VOMERO = "VOMERO"
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
    FF_KPT = "KPT"
    FF_FST = "FST"


class Env_Cond(Enum):
    MFG_LT = "LT"
    MFG_NT = "NT"
    MFG_HT = "HT"
    MFG_RDT = "RDT"
    MFG_EDVT_HT = "EDVT_HT"
    MFG_EDVT_LT = "EDVT_LT"

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

    MTP_POWER_ON_DELAY = 180
    MTP_POWER_ON_TIMEOUT = 120
    MTP_OS_SHUTDOWN_DELAY = 60
    MTP_POWER_CYCLE_DELAY = 30
    MTP_NETCOPY_DELAY = 600
    MTP_FRU_UPDATE_DELAY = 1200
    MTP_PARA_TEST_DELAY = 1800
    OS_SYNC_DELAY = 300
    SSH_PASSWORD_DELAY = 30
    OS_CMD_DELAY = 120
    NIC_CON_CMD_DELAY = 900
    NIC_CON_INIT_DELAY = 60
    NIC_NETCOPY_DELAY = 120
    NIC_CON_CMD_RETRY = 3
    NIC_MGMT_IP_SET_DELAY = 3
    NIC_MGMT_IP_INIT_RETRY = 3
    NIC_SW_BOOTUP_DELAY = 120
    NIC_AVS_SET_DELAY = 600
    NIC_ESEC_PROG_DELAY = 600
    NIC_POWER_ON_DELAY = 30
    NIC_POWER_OFF_DELAY = 10

    MTP_DIAGMGR_DELAY = 10
    MTP_MGMT_IP_SET_DELAY = 10

    # more than 12 hours
    DIAG_P2C_TIMEOUT = 48000
    # more than 24 hours
    DIAG_4C_TIMEOUT = 96000
    # single test, 1.5 hours
    DIAG_TEST_TIMEOUT = 5400

    # 4 hours
    DIAG_DL_TEST_TIMEOUT = 14400
    DIAG_KPT_TEST_TIMEOUT = 14400
    
    MFG_EDVT_LOW_FAN_SPD = 40
    MFG_EDVT_NORM_FAN_SPD = 40
    MFG_EDVT_HIGH_FAN_SPD = 90
    MFG_EDVT_HIGH_TEMP = 50
    MFG_EDVT_LOW_TEMP = 0
    MFG_EDVT_TEMP_DIFF = 5
    MFG_EDVT_HIGH_VOLT = 5
    MFG_EDVT_LOW_VOLT = -5
    MFG_TEMP_WAIT_TIMEOUT = 180
    MFG_TEMP_SOAK_TIMEOUT = 180
    MFG_TEMP_CHECK_INTERVAL = 10

    # MFG moduling parameters
    MFG_MODEL_EDVT_HIGH_FAN_SPD = 40
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
    ONBOARD_ASIC_LOG_FILES = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/*log"
    ONBOARD_TEST_LOG_FILES = "/home/diag/mtp_regression/*log"
    ONBOARD_NIC_LOG_FILES = "/home/diag/diag/nic_log/*"
    ONBOARD_DL_LOG_FILES = "/home/diag/mtp_dl_script/*log /home/diag/mtp_dl_script/*yaml"
    ONBOARD_KPT_LOG_FILES = "/home/diag/mtp_kpt_script/*log"
    ONBOARD_ASIC_LOG_DIR = "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/"
    ONBOARD_NIC_LOG_DIR = "/home/diag/diag/nic_log/"
    NIC_ONBOARD_ASIC_LOG_DIR = "/data/nic_arm/nic/asic_src/ip/cosim/tclsh/"
    NIC_ONBOARD_DIAG_LOG_DIR = "/home/diag/diag/log/"

    DIAG_QA_LOG_DIR = "/vol/hw/diag/diag_qa/regression_log/"
    DIAG_MFG_DL_LOG_DIR_FMT = "/mfg_log/{:s}/DL/{:s}/"
    DIAG_MFG_P2C_LOG_DIR_FMT = "/mfg_log/{:s}/P2C/{:s}/"
    DIAG_MFG_4C_LOG_DIR_FMT = "/mfg_log/{:s}/4C/{:s}/{:s}/"
    DIAG_MFG_KPT_LOG_DIR_FMT = "/mfg_log/{:s}/KPT/{:s}/"

    DIAG_MFG_MODEL_DL_LOG_DIR_FMT = "/tmp/mfg_log/{:s}/DL/{:s}/"
    DIAG_MFG_MODEL_P2C_LOG_DIR_FMT = "/tmp/mfg_log/{:s}/P2C/{:s}/"
    DIAG_MFG_MODEL_4C_LOG_DIR_FMT = "/tmp/mfg_log/{:s}/4C/{:s}/{:s}/"
    DIAG_MFG_MODEL_KPT_LOG_DIR_FMT = "/tmp/mfg_log/{:s}/KPT/{:s}/"

    MFG_DL_LOG_PKG_FILE = "DL_{:s}_{:s}.tar.gz"
    MFG_DL_LOG_DIR = "DL_{:s}_{:s}/"
    MFG_P2C_LOG_PKG_FILE = "NT_{:s}_{:s}.tar.gz"
    MFG_P2C_LOG_DIR = "NT_{:s}_{:s}/"
    MFG_4C_LOG_PKG_FILE = "{:s}_{:s}_{:s}.tar.gz"
    MFG_4C_LOG_DIR = "{:s}_{:s}_{:s}/"
    MFG_KPT_LOG_PKG_FILE = "KPT_{:s}_{:s}.tar.gz"
    MFG_KPT_LOG_DIR = "KPT_{:s}_{:s}/"


class MTP_DIAG_Path:
    ONBOARD_MTP_DIAG_PATH = "/home/diag/"
    ONBOARD_MTP_NIC_CON_PATH = "/home/diag/diag/python/regression/"
    ONBOARD_MTP_DSHELL_PATH = "/home/diag/diag/python/infra/dshell/"
    ONBOARD_MTP_ESEC_PATH = "/home/diag/diag/python/esec/"
    ONBOARD_MTP_ASIC_PATH = "/home/diag/diag/scripts/asic/"
    ONBOARD_MTP_MTP_DIAG_PATH = "/home/diag/diag/"
    ONBOARD_MTP_NIC_DIAG_PATH = "/home/diag/nic_diag/"
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
    MTP_DIAG_REGRESSION_FAIL = "MTP_DIAG_REGRESSION_TEST_FAIL"
    NIC_DIAG_REGRESSION_FAIL = "NIC_DIAG_REGRESSION_TEST_FAIL"
    NIC_DIAG_REGRESSION_PASS = "NIC_DIAG_REGRESSION_TEST_PASS"
    NIC_DIAG_REGRESSION_RSLT_RE = r"NIC-(\d{{2}}) (\w+) (\w+) {:s}"

class MFG_DIAG_CMDS:
    MTP_DIAG_VERSION_FMT = "version"
    MTP_LOGIN_VERIFY_FMT = "whoami"
    MTP_ASIC_VERSION_FMT = "head /home/diag/diag/asic/asic_version.txt"
    MTP_FAN_STATUS_FMT = "devmgr -dev FAN -status"
    MTP_FAN_SET_SPD_FMT = "devmgr -dev=fan -speed -pct={:d}"
    MTP_VRM_TEST_FMT = "mtptest -vrm"
    MTP_FAN_TEST_FMT = "mtptest -fanspd"
    MTP_FAN_PRSNT_FMT = "mtptest -present"

    MTP_CPLD_READ_FMT = "cpldutil -cpld-rd -addr=0x{:x}"

    MTP_FRU_PROG_FMT = "eeutil -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -uut=UUT_{:d} -update"
    MTP_HP_FRU_PROG_FMT = "eeutil -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -uut=UUT_{:d} -update -hpe"
    MTP_FRU_DISP_FMT = "eeutil -disp -uut=UUT_{:d}"
    MTP_HP_FRU_DISP_FMT = "eeutil -disp -uut=UUT_{:d} -hpe"
    NIC_FRU_PROG_FMT = "{:s}eeutil -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -update"
    NIC_HP_FRU_PROG_FMT = "{:s}eeutil -date='{:s}' -sn='{:s}' -mac='{:s}' -pn='{:s}' -update -hpe"
    NIC_FRU_DISP_FMT = "{:s}eeutil -disp"
    NIC_HP_FRU_DISP_FMT = "{:s}eeutil -disp -hpe"
    NIC_VENDOR_DISP_FMT = "{:s}eeutil -disp -field=sn"

    NIC_JTAG_TEST_FMT = "sys_sanity.sh {:d}"

    NIC_CPLD_PROG_FMT = "{:s}cpld -prog /{:s}"
    NIC_CPLD_READ_FMT = "{:s}cpld -r {:d}"
    NIC_CPLD_REF_FMT = "{:s}cpld -refresh"

    # onboard diag utils version
    NIC_DIAG_UTIL_VERSION_FMT = "head /data/nic_util/version.txt"
    # copied diag version
    NIC_DIAG_VERSION_FMT = "head /home/diag/diag/scripts/version.txt"

    NIC_MOUNT_EMMC_FMT = "mount /dev/mmcblk0p10 /data"
    NIC_FSCK_EMMC_FMT = "fsck -y /dev/mmcblk0p10"
    NIC_DIAG_CLEANUP_FMT = "rm -rf /data/nic*"
    NIC_MOUNT_DISP_FMT = "mount | grep '/dev/mmcblk0p10'"
    NIC_QSPI_PROG_FMT = "fwupdate -p /{:s} -i 'all'"
    NIC_DIAGFW_PROG_FMT = "fwupdate -p /{:s} -i diagfw"
    NIC_EMMC_INIT_FMT = "fwupdate --init-emmc"
    NIC_EMMC_PROG_FMT = "fwupdate -p /{:s} -i 'uboot mainfwa mainfwb'"
    NIC_BOOT_DISP_FMT = "fwupdate -r"
    NIC_SET_SW_BOOT_FMT = "fwupdate -s mainfwa"
    NIC_SET_DIAG_BOOT_FMT = "fwupdate -s diagfw"
    NIC_SET_MGMT_IP_FMT = "ifconfig oob_mnic0 10.1.1.{:d} netmask 255.255.255.0"

    NIC_ESEC_PROG_PRE_FMT = "./esec_ctrl.py -slot {:d} -img_prog"
    NIC_ESEC_PROG_POST_FMT = "./esec_ctrl.py -cleanup"
    NIC_ESEC_CPLD_CHECK_FMT = "./esec_ctrl.py -check_uboot -slot {:d}"
    NIC_ESEC_PROG_FMT = "./esec_ctrl.py -esec_prog -slot {:d} -sn {:s} -pn '{:s}' -mac {:s} -brd_name {:s} -mtp {:s}"

    NIC_IMG_VER_DISP_FMT = "cat /proc/version | sed 's/.*SMP/SMP/'"
    MTP_IMG_VER_DISP_FMT = "cat /proc/version | sed 's/.*SMP/SMP/'"
    NIC_VMARG_SET_FMT = "/home/diag/diag/scripts/vmarg.sh {:s}"

    # Naples100: core_freq=833 arm_freq=2000
    NAPLES100_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 2000"
    NAPLES100_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 2000"
    # Vomero: core_freq=833 arm_freq=2000
    VOMERO_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 833 -arm_freq 2000"
    VOMERO_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 833 -arm_freq 2000"
    # Naples25: core_freq=417 arm_freq=1600
    NAPLES25_VDD_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd vdd -core_freq 417 -arm_freq 1600"
    NAPLES25_ARM_AVS_SET_FMT = "tclsh8.6 set_avs.tcl -sn {:s} -slot {:d} -arm_vdd arm -core_freq 417 -arm_freq 1600"

    NIC_POWER_ON_FMT = "turn_on_slot.sh on {:d}"
    NIC_POWER_OFF_FMT = "turn_on_slot.sh off {:d}"
    MTP_POWER_ON_NIC_FMT = "turn_on_slot.sh on all"
    MTP_POWER_OFF_NIC_FMT = "turn_on_slot.sh off all"

    MTP_SMB_CMD_FMT = "smbutil -rd -addr=0x{:x} -uut='UUT_{:d}' -dev=CPLD"
    MTP_SMB_SEL_FMT = "turn_on_uut.sh {:d}"

    NIC_POWER_CHECK_FMT = "inventory -ps -slot={:d}"
    NIC_POWER_RAIL_DISP_FMT = "inventory -pw -slot={:d}"
    NIC_PRESENT_DISP_FMT = "inventory -present"

    NIC_CON_INIT_FMT = "nic_con.py -br -slot {:d}"
    NIC_CON_ATTACH_FMT = "con_connect.sh {:d}"
    NIC_MGMT_INIT_FMT = "nic_con.py -mgmt -slot {:d}"
    NIC_FPO_MGMT_INIT_FMT = "nic_con.py -mgmt -slot {:d} -fpo"
    NIC_CON_MTEST_FMT = "nic_con.py -mtest -slot {:d}"
    MTP_NIC_PCIE_LINK_POLL_DISABLE_FMT = "nic_con.py -dis_pcie -slot {:d}"
    MTP_NIC_PCIE_LINK_POLL_ENABLE_FMT = "nic_con.py -ena_pcie -slot {:d}"

    NIC_AAPL_INIT_FMT = "nic_test.py -setup_multi -mgmt -aapl -slot_list {:d}"
    MTP_PARA_PRBS_ETH_TEST_FMT = "nic_test.py -prbs -slot_list='{:s}' -wtime=120 -mode=eth -vmarg {:d}"
    MTP_PARA_SNAKE_HBM_FMT = "nic_test.py -snake -slot_list='{:s}' -wtime=180 -vmarg {:d}"
    MTP_PARA_SNAKE_PCIE_FMT = "nic_test.py -snake -slot_list='{:s}' -wtime=180 -mode=pcie -vmarg {:d}"

    MTP_ARP_DELET_FMT = "arp -d {:s}"
    MTP_NIC_MAC_DISP_FMT = "arp -i enp2s0"
    MTP_NIC_PING_FMT = "ping -c 4 {:s}"

    MTP_DIAG_INIT_FMT = "/home/diag/start_diag.sh"
    NIC_DIAG_INIT_FMT = "/home/diag/start_diag.arm64.sh {:d}"
    NIC_DIAG_FINI_FMT = "rm -r /data/debug*"

    MTP_DIAG_MGR_START_FMT = "nohup diagmgr > {:s} 2>&1 &"
    MTP_DSP_START_FMT = "/home/diag/diag/python/infra/dshell/diag -r -c MTP1 -d diagmgr -t dsp_start"
    MTP_DSP_STOP_FMT = "/home/diag/diag/python/infra/dshell/diag -r -c MTP1 -d diagmgr -t dsp_stop"
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
    MFG_LOG_LINK_FMT = "ln {:s} {:s}"

class MFG_DIAG_SIG:
    MTP_DIAG_OK_SIG = "Set up diag amd64 -- Done"
    MTP_DSP_START_OK_SIG = "Test Done: MTP1:DIAGMGR:DSP_START"
    MTP_VRM_OK_SIG = "TEST PASSED"
    MTP_FAN_OK_SIG = "TEST PASSED"
    MTP_PARA_TEST_SIG = "TEST RESULT:"
    MTP_FAN0_PRSNT_SIG = "Fan 0 is present"
    MTP_FAN1_PRSNT_SIG = "Fan 1 is present"
    MTP_FAN2_PRSNT_SIG = "Fan 2 is present"
    NIC_CON_OK_SIG = "# stty speed 4800"
    NIC_MGMT_OK_SIG = "Management port is ready"
    NIC_AAPL_OK_SIG = "AAPL setup done"
    NIC_CON_MTEST_PASS_SIG = "=== MTEST PASSED ==="
    NIC_POWER_OK_SIG = "power good"
    NIC_OS_SHUTDOWN_OK_SIG = "System halted"
    NIC_MOUNT_OK_SIG = "/dev/mmcblk0p10 on /data"
    NIC_ESEC_PROG_PRE_SIG = "IMG PROG PASSED"
    NIC_ESEC_PROG_SIG = "ESEC PROG/VALICATION PASSED"
    NIC_ESEC_CPLD_VERIFY_SIG = "EK validated"
    NIC_FWUPDATE_FAIL_SIG = "FATAL"
    NIC_UBOOT_PCIE_ENA_SIG = "setenv pcie_poll_disable"
    NIC_UBOOT_PCIE_DIS_SIG = "setenv pcie_poll_disable 1"
    MFG_DIAG_ERR_MSG_SIG = "[ERROR]"
    MFG_ASIC_ERR_MSG_SIG = "ERROR ::"
    MFG_ASIC_PASS_MSG_SIG = "#PASS#"
    MFG_ASIC_CTC_ERR_MSG_SIG = "ERROR_CTC_WRITE_READ_COMPARE_FAILURE"
    MFG_ASIC_PCIE_MAPPING_MSG_SIG = "SBUS_PCIE_MAPPING"

class MFG_DIAG_RE:
    MFG_NIC_TYPE_NAPLES100 = r"UUT_(\d+) +NAPLES100"
    MFG_NIC_TYPE_NAPLES25  = r"UUT_(\d+) +NAPLES25"
    MFG_NIC_TYPE_FORIO     = r"UUT_(\d+) +FORIO"
    MFG_NIC_TYPE_VOMERO    = r"UUT_(\d+) +VOMERO"

