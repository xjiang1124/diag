package hwinfo

import (
    "os"
    "fmt"

    "device/boardinfo"
    "device/fanctrl/adt7462"
    "device/powermodule/ltc2301"
    "device/powermodule/ltc3882"
    "device/powermodule/ltc3888"
    "device/bcm/td3"
    "device/fpga/taorfpga"
    "device/fpga/liparifpga"
    "device/powermodule/mp2975"
    "device/powermodule/mp8796"
    "device/powermodule/tps53659"
    "device/powermodule/tps549a20"
    "device/powermodule/tps544b25"
    "device/powermodule/tps544c20"
    "device/powermodule/tps53681"
    "device/powermodule/sn1701022"
    "device/powermodule/tps53688"
    "device/powermodule/pmic"
    "device/powermodule/tps25990"
    "device/powermodule/isl69247"
    "device/powermodule/ina3221a"
    "device/powermodule/ad7997"
    "device/psu/pet1600"
    "device/psu/dps800"
    "device/psu/dps2100"
    "device/tempsensor/tmp42123"
    "device/tempsensor/adm1032"
    "device/tempsensor/tmpadicom"
    "device/tempsensor/lm75a"
    "device/tempsensor/tmp451"
    "device/cpu/XeonD"
    "device/clkgen/rc19013"
    "device/ioexpander/mcp23008"

    "gopkg.in/yaml.v2"
)

const (
    MAX_NUM_FAN = 4
)

type DispStaFunc func(devName string)(err int)

type I2cHubInfo struct {
    hubName string
    channel byte
}

type QsfpInfo_t struct {
    DevName    string
    ModRstReg  int
    ModRstBit  int
    LpReg      int
    LpBit      int
    PrstReg    int
    PrstBit    int
    IntrReg    int
    IntrBit    int
    PrstIntReg int
    PrstIntBit int
    RmIntReg   int
    RmIntBit   int
}

type SfpInfo_t struct {
    DevName     string
    TxDisReg	uint32
    TxDisBit    uint32
    TxFaultReg  uint32
    TxFaultBit  uint32
    PrstReg     uint32
    PrstBit     uint32
    RxLossReg   uint32
    RxLossBit   uint32
}

var cardType string
var uutName string
var itpType string
var itpIdx byte

//===============================
// Naples common 
var CpldInfo interface{}

// EEPROM list
var naplesEepList = []string {"FRU"}
var GinestraEepList = []string {"FRU", "PCIE_FRU"}
var MalfaEepList  = []string {"FRU", "DPU_FRU", "CPLD_FRU"}
var PollaraEepList  = []string {"FRU", "DPU_FRU", "CPLD_FRU"}
var LeniEepList   = []string {"FRU", "DPU_FRU", "CPLD_FRU"}
var LinguaEepList  = []string {"FRU", "DPU_FRU", "CPLD_FRU"}
var lipariEepList = []string {"FRU", "FRU_CPUBRD", "FRU_SWITCH"}
var materaEepList = []string {"FRU", "IOBL", "IOBR", "FPIC"}

//===============================
// Naples100 
// Status display list
var naplesMtpDispStaList map[string]DispStaFunc
var naples100DispStaList map[string]DispStaFunc

// I2C hub map -- dummy
var naples100I2cHubMap map[string] I2cHubInfo

// QSFP table
var naples100QsfpTbl = []QsfpInfo_t {
    //          devName   modRstReg modRstBit lpReg lpBit prstReg prstBit intrReg intrBit prstIntReg prstIntBit rmIntReg rmIntBit
    QsfpInfo_t {"QSFP_1", 0x2,      0,        0x2,  2,    0x2,    4,      0x2,    6,      0x3,       0,         0x3,     2},
    QsfpInfo_t {"QSFP_2", 0x2,      1,        0x2,  3,    0x2,    5,      0x2,    7,      0x3,       1,         0x3,     3},
}

//===============================
// Naples25 
// Status display list
var naples25DispStaList map[string]DispStaFunc

// I2C hub map -- dummy
var naples25I2cHubMap map[string] I2cHubInfo

// SFP table
var naples25SfpTbl = []SfpInfo_t {
    //          devName   txDisReg txDisBit txFaultReg txFaultBit prstReg prstBit rxLossReg rxLossBit
    SfpInfo_t {"SFP_1",  0x2,      0,       0x2,      2,         0x2,     4,      0x2,      6,     },
    SfpInfo_t {"SFP_2",  0x2,      1,       0x2,      3,         0x2,     5,      0x2,      7,     },
}

//===============================
// Forio 
// Status display list
var forioDispStaList map[string]DispStaFunc

// I2C hub map -- dummy
var forioI2cHubMap map[string] I2cHubInfo

// QSFP table
var forioQsfpTbl = []QsfpInfo_t {
    //          devName   modRstReg modRstBit lpReg lpBit prstReg prstBit intrReg intrBit prstIntReg prstIntBit rmIntReg rmIntBit
    QsfpInfo_t {"QSFP_1", 0x2,      0,        0x2,  2,    0x2,    4,      0x2,    6,      0x3,       0,         0x3,     2},
    QsfpInfo_t {"QSFP_2", 0x2,      1,        0x2,  3,    0x2,    5,      0x2,    7,      0x3,       1,         0x3,     3},
}

//===============================
// Biodona 
// Status display list
var biodonaDispStaList map[string]DispStaFunc

//===============================
// Ortano
// Status display list
var ortanoDispStaList map[string]DispStaFunc
var ortanoaDispStaList map[string]DispStaFunc
var ortanoiDispStaList map[string]DispStaFunc
var ortanoitmpDispStaList = [4]DispStaFunc {
    tmp451.DispStatusWithRemote,
    adm1032.DispStatus,
    nil,
    nil,
}

var ortanoiPODDispStaList = [8](map[string]DispStaFunc) {
    nil,
    { "ELB0_CORE":tps53659.DispStatus, "ELB0_ARM":tps53659.DispStatus, "VDDQ_DDR":tps549a20.DispStatus, "VDD_DDR":tps549a20.DispStatus},
    nil,
    nil,
    nil,
    nil,
    nil,
    nil,
}

//===============================
// Lacona
// Status display list
var laconaDispStaList map[string]DispStaFunc
// Ginestra D4
var ginestraD4DispStaList map[string]DispStaFunc
// Ginestra D5
var ginestraD5DispStaList map[string]DispStaFunc

//===============================
// Salina cards
// Status display list
var malfaDispStaList map[string]DispStaFunc
var pollaraDispStaList map[string]DispStaFunc
var leniDispStaList map[string]DispStaFunc
var linguaDispStaList map[string]DispStaFunc

//===============================
// MTP
// Status display list
var mtpDispStaList map[string]DispStaFunc
// EEPROM list
var mtpEepList = []string {"FRU"}
// I2C hub map
var mtpI2cHubMap map[string] I2cHubInfo
var materaI2cHubMap map[string] I2cHubInfo

//===============================
// MTP
// Status display list
var mtpsDispStaList map[string]DispStaFunc

// MTP_MATERA
// Status display list
var materaDispStaList map[string]DispStaFunc

//===============================
// NIC POWER
// Status display list
var nicPwrDispStaList map[string]DispStaFunc

//===============================
// Taormina 
// Status display list
var taorDispStaList map[string]DispStaFunc

// Lipari
var lipariDispStaList map[string]DispStaFunc
var lipariElbaDispStaList map[string]DispStaFunc

// mtfuji (Cisco)
var mtfujiElbaDispStaList map[string]DispStaFunc

// capaci (HPE)
var capaciElbaDispStaList map[string]DispStaFunc

// I2C hub map -- not used on Taormina and Lipari
var taorI2cHubMap map[string] I2cHubInfo
var lipariI2cHubMap map[string] I2cHubInfo
var lipariElbaI2cHubMap map[string] I2cHubInfo

// SFP table
var SFP_STAT_REG0 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_3_0_REG) 
var SFP_STAT_REG1 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_7_4_REG) 
var SFP_STAT_REG2 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_11_8_REG) 
var SFP_STAT_REG3 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_15_12_REG) 
var SFP_STAT_REG4 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_19_16_REG) 
var SFP_STAT_REG5 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_23_20_REG) 
var SFP_STAT_REG6 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_27_24_REG) 
var SFP_STAT_REG7 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_31_28_REG) 
var SFP_STAT_REG8 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_35_32_REG) 
var SFP_STAT_REG9 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_39_36_REG) 
var SFP_STAT_REG10 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_43_40_REG) 
var SFP_STAT_REG11 uint32 = uint32(taorfpga.D0_FP_SFP_STAT_47_44_REG) 

var SFP_CTRL_REG0 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_3_0_REG) 
var SFP_CTRL_REG1 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_7_4_REG) 
var SFP_CTRL_REG2 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_11_8_REG) 
var SFP_CTRL_REG3 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_15_12_REG) 
var SFP_CTRL_REG4 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_19_16_REG) 
var SFP_CTRL_REG5 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_23_20_REG) 
var SFP_CTRL_REG6 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_27_24_REG) 
var SFP_CTRL_REG7 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_31_28_REG) 
var SFP_CTRL_REG8 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_35_32_REG) 
var SFP_CTRL_REG9 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_39_36_REG) 
var SFP_CTRL_REG10 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_43_40_REG) 
var SFP_CTRL_REG11 uint32 = uint32(taorfpga.D0_FP_SFP_CTRL_47_44_REG) 

var taorSfpTbl = []SfpInfo_t {
    //          devName  txDisReg        txDisBit     txFaultReg      txFaultBit     prstReg         prstBit    rxLossReg           rxLossBit
    SfpInfo_t {"SFP_1",  SFP_CTRL_REG0,      0,       SFP_STAT_REG0,      1,         SFP_STAT_REG0,     0,      SFP_STAT_REG0,      2,     },
    SfpInfo_t {"SFP_2",  SFP_CTRL_REG0,      8,       SFP_STAT_REG0,      9,         SFP_STAT_REG0,     8,      SFP_STAT_REG0,      10,    },
    SfpInfo_t {"SFP_3",  SFP_CTRL_REG0,      16,      SFP_STAT_REG0,      17,        SFP_STAT_REG0,     16,     SFP_STAT_REG0,      18,    },
    SfpInfo_t {"SFP_4",  SFP_CTRL_REG0,      24,      SFP_STAT_REG0,      25,        SFP_STAT_REG0,     24,     SFP_STAT_REG0,      26,    },
    SfpInfo_t {"SFP_5",  SFP_CTRL_REG1,      0,       SFP_STAT_REG1,      1,         SFP_STAT_REG1,     0,      SFP_STAT_REG1,      2,     },
    SfpInfo_t {"SFP_6",  SFP_CTRL_REG1,      8,       SFP_STAT_REG1,      9,         SFP_STAT_REG1,     8,      SFP_STAT_REG1,      10,    },
    SfpInfo_t {"SFP_7",  SFP_CTRL_REG1,      16,      SFP_STAT_REG1,      17,        SFP_STAT_REG1,     16,     SFP_STAT_REG1,      18,    },
    SfpInfo_t {"SFP_8",  SFP_CTRL_REG1,      24,      SFP_STAT_REG1,      25,        SFP_STAT_REG1,     24,     SFP_STAT_REG1,      26,    },
    SfpInfo_t {"SFP_9",  SFP_CTRL_REG2,      0,       SFP_STAT_REG2,      1,         SFP_STAT_REG2,     0,      SFP_STAT_REG2,      2,     },
    SfpInfo_t {"SFP_10", SFP_CTRL_REG2,      8,       SFP_STAT_REG2,      9,         SFP_STAT_REG2,     8,      SFP_STAT_REG2,      10,    },
    SfpInfo_t {"SFP_11", SFP_CTRL_REG2,      16,      SFP_STAT_REG2,      17,        SFP_STAT_REG2,     16,     SFP_STAT_REG2,      18,    },
    SfpInfo_t {"SFP_12", SFP_CTRL_REG2,      24,      SFP_STAT_REG2,      25,        SFP_STAT_REG2,     24,     SFP_STAT_REG2,      26,    },
    SfpInfo_t {"SFP_13", SFP_CTRL_REG3,      0,       SFP_STAT_REG3,      1,         SFP_STAT_REG3,     0,      SFP_STAT_REG3,      2,     },
    SfpInfo_t {"SFP_14", SFP_CTRL_REG3,      8,       SFP_STAT_REG3,      9,         SFP_STAT_REG3,     8,      SFP_STAT_REG3,      10,    },
    SfpInfo_t {"SFP_15", SFP_CTRL_REG3,      16,      SFP_STAT_REG3,      17,        SFP_STAT_REG3,     16,     SFP_STAT_REG3,      18,    },
    SfpInfo_t {"SFP_16", SFP_CTRL_REG3,      24,      SFP_STAT_REG3,      25,        SFP_STAT_REG3,     24,     SFP_STAT_REG3,      26,    },
    SfpInfo_t {"SFP_17", SFP_CTRL_REG4,      0,       SFP_STAT_REG4,      1,         SFP_STAT_REG4,     0,      SFP_STAT_REG4,      2,     },
    SfpInfo_t {"SFP_18", SFP_CTRL_REG4,      8,       SFP_STAT_REG4,      9,         SFP_STAT_REG4,     8,      SFP_STAT_REG4,      10,    },
    SfpInfo_t {"SFP_19", SFP_CTRL_REG4,      16,      SFP_STAT_REG4,      17,        SFP_STAT_REG4,     16,     SFP_STAT_REG4,      18,    },
    SfpInfo_t {"SFP_20", SFP_CTRL_REG4,      24,      SFP_STAT_REG4,      25,        SFP_STAT_REG4,     24,     SFP_STAT_REG4,      26,    },
    SfpInfo_t {"SFP_21", SFP_CTRL_REG5,      0,       SFP_STAT_REG5,      1,         SFP_STAT_REG5,     0,      SFP_STAT_REG5,      2,     },
    SfpInfo_t {"SFP_22", SFP_CTRL_REG5,      8,       SFP_STAT_REG5,      9,         SFP_STAT_REG5,     8,      SFP_STAT_REG5,      10,    },
    SfpInfo_t {"SFP_23", SFP_CTRL_REG5,      16,      SFP_STAT_REG5,      17,        SFP_STAT_REG5,     16,     SFP_STAT_REG5,      18,    },
    SfpInfo_t {"SFP_24", SFP_CTRL_REG5,      24,      SFP_STAT_REG5,      25,        SFP_STAT_REG5,     24,     SFP_STAT_REG5,      26,    },
    SfpInfo_t {"SFP_25", SFP_CTRL_REG6,      0,       SFP_STAT_REG6,      1,         SFP_STAT_REG6,     0,      SFP_STAT_REG6,      2,     },
    SfpInfo_t {"SFP_26", SFP_CTRL_REG6,      8,       SFP_STAT_REG6,      9,         SFP_STAT_REG6,     8,      SFP_STAT_REG6,      10,    },
    SfpInfo_t {"SFP_27", SFP_CTRL_REG6,      16,      SFP_STAT_REG6,      17,        SFP_STAT_REG6,     16,     SFP_STAT_REG6,      18,    },
    SfpInfo_t {"SFP_28", SFP_CTRL_REG6,      24,      SFP_STAT_REG6,      25,        SFP_STAT_REG6,     24,     SFP_STAT_REG6,      26,    },
    SfpInfo_t {"SFP_29", SFP_CTRL_REG7,      0,       SFP_STAT_REG7,      1,         SFP_STAT_REG7,     0,      SFP_STAT_REG7,      2,     },
    SfpInfo_t {"SFP_30", SFP_CTRL_REG7,      8,       SFP_STAT_REG7,      9,         SFP_STAT_REG7,     8,      SFP_STAT_REG7,      10,    },
    SfpInfo_t {"SFP_31", SFP_CTRL_REG7,      16,      SFP_STAT_REG7,      17,        SFP_STAT_REG7,     16,     SFP_STAT_REG7,      18,    },
    SfpInfo_t {"SFP_32", SFP_CTRL_REG7,      24,      SFP_STAT_REG7,      25,        SFP_STAT_REG7,     24,     SFP_STAT_REG7,      26,    },
    SfpInfo_t {"SFP_33", SFP_CTRL_REG8,      0,       SFP_STAT_REG8,      1,         SFP_STAT_REG8,     0,      SFP_STAT_REG8,      2,     },
    SfpInfo_t {"SFP_34", SFP_CTRL_REG8,      8,       SFP_STAT_REG8,      9,         SFP_STAT_REG8,     8,      SFP_STAT_REG8,      10,    },
    SfpInfo_t {"SFP_35", SFP_CTRL_REG8,      16,      SFP_STAT_REG8,      17,        SFP_STAT_REG8,     16,     SFP_STAT_REG8,      18,    },
    SfpInfo_t {"SFP_36", SFP_CTRL_REG8,      24,      SFP_STAT_REG8,      25,        SFP_STAT_REG8,     24,     SFP_STAT_REG8,      26,    },
    SfpInfo_t {"SFP_37", SFP_CTRL_REG9,      0,       SFP_STAT_REG9,      1,         SFP_STAT_REG9,     0,      SFP_STAT_REG9,      2,     },
    SfpInfo_t {"SFP_38", SFP_CTRL_REG9,      8,       SFP_STAT_REG9,      9,         SFP_STAT_REG9,     8,      SFP_STAT_REG9,      10,    },
    SfpInfo_t {"SFP_39", SFP_CTRL_REG9,      16,      SFP_STAT_REG9,      17,        SFP_STAT_REG9,     16,     SFP_STAT_REG9,      18,    },
    SfpInfo_t {"SFP_40", SFP_CTRL_REG9,      24,      SFP_STAT_REG9,      25,        SFP_STAT_REG9,     24,     SFP_STAT_REG9,      26,    },
    SfpInfo_t {"SFP_41", SFP_CTRL_REG10,     0,       SFP_STAT_REG10,     1,         SFP_STAT_REG10,    0,      SFP_STAT_REG10,     2,     },
    SfpInfo_t {"SFP_42", SFP_CTRL_REG10,     8,       SFP_STAT_REG10,     9,         SFP_STAT_REG10,    8,      SFP_STAT_REG10,     10,    },
    SfpInfo_t {"SFP_43", SFP_CTRL_REG10,     16,      SFP_STAT_REG10,     17,        SFP_STAT_REG10,    16,     SFP_STAT_REG10,     18,    },
    SfpInfo_t {"SFP_44", SFP_CTRL_REG10,     24,      SFP_STAT_REG10,     25,        SFP_STAT_REG10,    24,     SFP_STAT_REG10,     26,    },
    SfpInfo_t {"SFP_45", SFP_CTRL_REG11,     0,       SFP_STAT_REG11,     1,         SFP_STAT_REG11,    0,      SFP_STAT_REG11,     2,     },
    SfpInfo_t {"SFP_46", SFP_CTRL_REG11,     8,       SFP_STAT_REG11,     9,         SFP_STAT_REG11,    8,      SFP_STAT_REG11,     10,    },
    SfpInfo_t {"SFP_47", SFP_CTRL_REG11,     16,      SFP_STAT_REG11,     17,        SFP_STAT_REG11,    16,     SFP_STAT_REG11,     18,    },
    SfpInfo_t {"SFP_48", SFP_CTRL_REG11,     24,      SFP_STAT_REG11,     25,        SFP_STAT_REG11,    24,     SFP_STAT_REG11,     26,    },
}
//ADD FIXME - NEED TO FILL IN
// QSFP table


/*
type QsfpInfo_t struct {
    DevName    string
    ModRstReg  int
    ModRstBit  int
    LpReg      int
    LpBit      int
    PrstReg    int
    PrstBit    int
    IntrReg    int
    IntrBit    int
    PrstIntReg int
    PrstIntBit int
    RmIntReg   int
    RmIntBit   int
}
*/

var QSFP_STAT_REG0 int = int(taorfpga.D0_FP_QSFP_STAT_51_48_REG) 
var QSFP_STAT_REG1 int = int(taorfpga.D0_FP_QSFP_STAT_55_52_REG)

var QSFP_CTRL_REG0 int = int(taorfpga.D0_FP_QSFP_CTRL_51_48_REG) 
var QSFP_CTRL_REG1 int = int(taorfpga.D0_FP_QSFP_CTRL_55_52_REG)


var taorQsfpTbl = []QsfpInfo_t {
    //          devName      modRstReg   modRstBit         lpReg      lpBit    prstReg         prstBit       intrReg      intrBit prstIntReg prstIntBit rmIntReg rmIntBit
    QsfpInfo_t {"QSFP_1", QSFP_CTRL_REG0,      0,        QSFP_CTRL_REG0,  1,    QSFP_STAT_REG0,    0,      QSFP_STAT_REG0,    1,      0x3,       0,         0x3,     2},
    QsfpInfo_t {"QSFP_2", QSFP_CTRL_REG0,      8,        QSFP_CTRL_REG0,  9,    QSFP_STAT_REG0,    8,      QSFP_STAT_REG0,    9,      0x3,       1,         0x3,     3},
    QsfpInfo_t {"QSFP_3", QSFP_CTRL_REG0,      16,       QSFP_CTRL_REG0,  17,   QSFP_STAT_REG0,   16,      QSFP_STAT_REG0,    17,     0x3,       0,         0x3,     2},
    QsfpInfo_t {"QSFP_4", QSFP_CTRL_REG0,      24,       QSFP_CTRL_REG0,  25,   QSFP_STAT_REG0,   24,      QSFP_STAT_REG0,    25,     0x3,       1,         0x3,     3},
    QsfpInfo_t {"QSFP_5", QSFP_CTRL_REG1,      0,        QSFP_CTRL_REG1,  1,    QSFP_STAT_REG0,    0,      QSFP_STAT_REG0,    1,      0x3,       0,         0x3,     2},
    QsfpInfo_t {"QSFP_6", QSFP_CTRL_REG1,      8,        QSFP_CTRL_REG1,  9,    QSFP_STAT_REG0,    8,      QSFP_STAT_REG0,    9,      0x3,       1,         0x3,     3},
}

//===============================
//
//===============================
// Internal lookup table
var dispMap map[string]map[string]DispStaFunc
var pmbusTestMap map[string][]string
var eepromMap map[string][]string
var i2cHubMap map[string]map[string]I2cHubInfo
var i2cHubListMap map[string][]string
var psuListMap map[string][]string

//===============================
// Public data
// Dev display list
var DispStaList map[string]DispStaFunc
// Pmbus test device list
var PmbusTestList []string
// EEPROM  device list
var EepromList []string
// I2C hub map
var I2cHubMap map[string] I2cHubInfo
var I2cHubList []string
// PSU list
var PsuList []string
// QSFP table
var QsfpTbl []QsfpInfo_t
var SfpTbl []SfpInfo_t

func init() {
    // Can only do map initialization here

    //===============================
    // NAPLES_MTP
    naplesMtpDispStaList = make(map[string]DispStaFunc)
    naplesMtpDispStaList["CAP0_CORE_DVDD"] = tps53659.DispStatus
    naplesMtpDispStaList["CAP0_CORE_AVDD"] = tps53659.DispStatus
    naplesMtpDispStaList["VRM_HBM"]        = tps549a20.DispStatus
    naplesMtpDispStaList["VRM_ARM"]        = tps549a20.DispStatus
    naplesMtpDispStaList["TSENSOR"]        = tmp42123.DispStatus

    //===============================
    // NAPLES100
    naples100DispStaList = make(map[string]DispStaFunc)
    naples100DispStaList["CAP0_CORE_DVDD"] = tps53659.DispStatus
    naples100DispStaList["CAP0_CORE_AVDD"] = tps549a20.DispStatus
    naples100DispStaList["CAP0_3V3"]       = tps549a20.DispStatus
    naples100DispStaList["CAP0_HBM"]       = tps549a20.DispStatus
    naples100DispStaList["CAP0_ARM"]       = tps53659.DispStatus
    naples100DispStaList["TSENSOR"]        = tmp42123.DispStatus

    // Dummy I2C hub map
    naples100I2cHubMap = make(map[string]I2cHubInfo)

    //===============================
    // NAPLES25
    naples25DispStaList = make(map[string]DispStaFunc)
    naples25DispStaList["CAP0_CORE_DVDD"] = tps53659.DispStatus
    naples25DispStaList["CAP0_CORE_AVDD"] = tps549a20.DispStatus
    naples25DispStaList["CAP0_3V3"]       = tps549a20.DispStatus
    naples25DispStaList["CAP0_HBM"]       = tps549a20.DispStatus
    naples25DispStaList["CAP0_ARM"]       = tps53659.DispStatus
    naples25DispStaList["TSENSOR"]        = tmp42123.DispStatus

    // Dummy I2C hub map
    naples25I2cHubMap = make(map[string]I2cHubInfo)

    //===============================
    // FORIO
    forioDispStaList = make(map[string]DispStaFunc)
    forioDispStaList["CAP0_CORE_DVDD"] = tps53659.DispStatus
    forioDispStaList["CAP0_CORE_AVDD"] = tps549a20.DispStatus
    forioDispStaList["CAP0_3V3"]       = tps549a20.DispStatus
    forioDispStaList["CAP0_HBM"]       = tps549a20.DispStatus
    forioDispStaList["CAP0_ARM"]       = tps53659.DispStatus
    forioDispStaList["TSENSOR"]        = tmp42123.DispStatus

    // Dummy I2C hub map
    forioI2cHubMap = make(map[string]I2cHubInfo)

    //===============================
    // Biodona
    biodonaDispStaList = make(map[string]DispStaFunc)
    biodonaDispStaList["ELB0_CORE"] = tps53659.DispStatus
    biodonaDispStaList["ELB0_ARM"]  = tps53659.DispStatus
    biodonaDispStaList["VDDQ_DDR"]  = tps53659.DispStatus
    biodonaDispStaList["VDD_DDR"]   = tps549a20.DispStatus
    biodonaDispStaList["TSENSOR"]   = tmp42123.DispStatus

    //Ortano
    ortanoDispStaList = make(map[string]DispStaFunc)
    ortanoDispStaList["ELB0_CORE"] = tps53659.DispStatus
    ortanoDispStaList["ELB0_ARM"]  = tps53659.DispStatus
    ortanoDispStaList["VDDQ_DDR"]  = tps544b25.DispStatus
    ortanoDispStaList["VDD_DDR"]   = tps549a20.DispStatus
    ortanoDispStaList["TSENSOR"]   = tmp451.DispStatusWithRemote

    //Ortano ADI
    ortanoaDispStaList = make(map[string]DispStaFunc)
    ortanoaDispStaList["ELB0_CORE"] = ltc3888.DispStatus
    ortanoaDispStaList["ELB0_ARM"]  = ltc3888.DispStatus
    ortanoaDispStaList["VRM_IIN"] = ltc2301.DispStatus
    ortanoaDispStaList["TSENSOR"]   = tmpadicom.DispStatus

    //Ortano Interposer
    ortanoiDispStaList = make(map[string]DispStaFunc)

    itpType = os.Getenv("ITP_TYPE")
    if itpType != "" {
        fmt.Sscanf(itpType, "0x%x", &itpIdx)
        if ( os.Getenv("CARD_TYPE") == "ORTANO2I" ) {
            tmpIdx := (itpIdx & 0xc0 ) >>6
            podIdx := (itpIdx & 0x07 )
            ortanoiDispStaList = ortanoiPODDispStaList[podIdx]
            ortanoiDispStaList["TSENSOR"] = ortanoitmpDispStaList[tmpIdx]
       } else {
            tmpIdx := (itpIdx & 0x04 ) >> 2
            ortanoiDispStaList = ortanoiPODDispStaList[1]
            ortanoiDispStaList["TSENSOR"] = ortanoitmpDispStaList[tmpIdx]
       }
    }

    //Lacona
    laconaDispStaList = make(map[string]DispStaFunc)
    laconaDispStaList["ELB0_CORE"] = tps53659.DispStatus
    laconaDispStaList["ELB0_ARM"]  = tps53659.DispStatus
    laconaDispStaList["VDDQ_DDR"]  = tps544b25.DispStatus
    laconaDispStaList["TSENSOR"]   = tmp451.DispStatusWithRemote

    //GinestraD4
    ginestraD4DispStaList = make(map[string]DispStaFunc)
    ginestraD4DispStaList["GIG0_CORE"] = tps53688.DispStatus
    ginestraD4DispStaList["GIG0_ARM"]  = tps53688.DispStatus
    ginestraD4DispStaList["DDR_VDDQ"]  = tps549a20.DispStatus
    ginestraD4DispStaList["VDD_DDR"]  = tps549a20.DispStatus
    ginestraD4DispStaList["TSENSOR"]   = tmp451.DispStatusWithRemote

    //GinestraD5
    ginestraD5DispStaList = make(map[string]DispStaFunc)
    ginestraD5DispStaList["GIG0_CORE"] = tps53688.DispStatus
    ginestraD5DispStaList["GIG0_ARM"]  = tps53688.DispStatus
    ginestraD5DispStaList["DDR_VDD"]  = pmic.DispStatus
    ginestraD5DispStaList["DDR_VDDQ"]  = pmic.DispStatus
    ginestraD5DispStaList["DDR_VPP"]  = pmic.DispStatus
    ginestraD5DispStaList["VDD_DDR"]  = tps549a20.DispStatus
    ginestraD5DispStaList["TSENSOR"]   = tmpadicom.DispStatus

    //Malfa
    malfaDispStaList = make(map[string]DispStaFunc)
    malfaDispStaList["P12V_AUX"]     = tps53688.DispStatusVsense
    malfaDispStaList["P12V_AUX_ADC"] = ad7997.DispStatusIout    // redundant reading for comparison
    malfaDispStaList["P12V"]         = ina3221a.DispStatus
    malfaDispStaList["P12V_ADC"]     = ad7997.DispStatusIout    // redundant reading for comparison
    malfaDispStaList["CORE"]         = tps53688.DispStatusSalina
    malfaDispStaList["ARM"]          = tps53688.DispStatusSalina
    malfaDispStaList["P3V3"]         = ina3221a.DispStatus
    malfaDispStaList["P1V8"]         = ina3221a.DispStatus
    malfaDispStaList["VDD_DDR"]      = ina3221a.DispStatus
    malfaDispStaList["VDD_075_PCIE"] = ina3221a.DispStatus
    malfaDispStaList["VDD_075_MX"]   = ina3221a.DispStatus
    malfaDispStaList["VDD_12_PCIE"]  = ina3221a.DispStatus
    malfaDispStaList["VDD_12_MX"]    = ina3221a.DispStatus
    malfaDispStaList["VDDQ"]         = ina3221a.DispStatus
    malfaDispStaList["VDD_075_PLL"]  = ad7997.DispStatusVout
    malfaDispStaList["PCIE_CLK_BUF"] = rc19013.DispStatus
    malfaDispStaList["MX_CLK_BUF"]   = rc19013.DispStatus
    malfaDispStaList["TSENSOR"]      = tmp451.DispStatusWithRemote
    malfaDispStaList["DDR_VDD_0"]    = pmic.DispStatus
    malfaDispStaList["DDR_VDDQ_0"]   = pmic.DispStatus
    malfaDispStaList["DDR_VPP_0"]    = pmic.DispStatus
    malfaDispStaList["DDR_VDD_1"]    = pmic.DispStatus
    malfaDispStaList["DDR_VDDQ_1"]   = pmic.DispStatus
    malfaDispStaList["DDR_VPP_1"]    = pmic.DispStatus

    //Pollara
    pollaraDispStaList = make(map[string]DispStaFunc)
    pollaraDispStaList["P12V"]         = tps53688.DispStatusVsense
    pollaraDispStaList["CORE"]         = tps53688.DispStatusSalina
    pollaraDispStaList["TSENSOR"]      = tmp451.DispStatusWithRemote

    //Leni
    leniDispStaList = make(map[string]DispStaFunc)
    leniDispStaList["P12V_AUX"]     = tps53688.DispStatusVsense // TODO: hide this display when aux cable is not present
    leniDispStaList["P12V"]         = ina3221a.DispStatus
    leniDispStaList["CORE"]         = tps53688.DispStatusSalina
    leniDispStaList["ARM"]          = tps53688.DispStatusSalina
    leniDispStaList["P3V3"]         = ina3221a.DispStatus
    leniDispStaList["P1V8"]         = ina3221a.DispStatus
    leniDispStaList["VDD_DDR"]      = ina3221a.DispStatus
    leniDispStaList["VDD_075_PCIE"] = ina3221a.DispStatus
    leniDispStaList["VDD_075_MX"]   = ina3221a.DispStatus
    leniDispStaList["VDD_12_PCIE"]  = ina3221a.DispStatus
    leniDispStaList["VDD_12_MX"]    = ina3221a.DispStatus
    leniDispStaList["VDDQ"]         = ina3221a.DispStatus
    leniDispStaList["VDD_075_PLL"]  = ad7997.DispStatusVout
    leniDispStaList["PCIE_CLK_BUF"] = rc19013.DispStatus
    leniDispStaList["MX_CLK_BUF"]   = rc19013.DispStatus
    leniDispStaList["TSENSOR"]      = tmp451.DispStatusWithRemote

    //Lingua
    linguaDispStaList = make(map[string]DispStaFunc)
    linguaDispStaList["P12V"]         = tps53688.DispStatusVsense
    linguaDispStaList["CORE"]         = tps53688.DispStatusSalina
    linguaDispStaList["TSENSOR"]      = tmp451.DispStatusWithRemote

    // Dummy I2C hub map
    naples100I2cHubMap = make(map[string]I2cHubInfo)

    //===============================
    // MTP
    mtpDispStaList = make(map[string]DispStaFunc)
    mtpDispStaList["PSU_1"] = pet1600.DispStatus
    mtpDispStaList["PSU_2"] = pet1600.DispStatus
    mtpDispStaList["DC_1"]  = tps549a20.DispStatus
    mtpDispStaList["DC_2"]  = tps549a20.DispStatus
    mtpDispStaList["FAN"]   = adt7462.DispStatus

    //===============================
    // MTP
    mtpsDispStaList = make(map[string]DispStaFunc)
    mtpsDispStaList["PSU_1"]    = pet1600.DispStatus
    mtpsDispStaList["PSU_2"]    = pet1600.DispStatus
    mtpsDispStaList["FAN"]      = adt7462.DispStatus
    mtpsDispStaList["A20_U17"]  = tps549a20.DispStatus
    mtpsDispStaList["A20_U18"]  = tps549a20.DispStatus
    mtpsDispStaList["A20_U40"]  = tps549a20.DispStatus
    mtpsDispStaList["A20_U53"]  = tps549a20.DispStatus
    mtpsDispStaList["659_DVDD"] = tps53659.DispStatus
    mtpsDispStaList["659_AVDD"] = tps53659.DispStatus

    //===============================
    // MTP_MATERA
    materaDispStaList = make(map[string]DispStaFunc)
    materaDispStaList["TSENSOR_MB"]   = lm75a.DispStatus
    materaDispStaList["TSENSOR_IOBL"] = lm75a.DispStatus
    materaDispStaList["TSENSOR_IOBR"] = lm75a.DispStatus
    materaDispStaList["EXPDER_IOBL"]  = mcp23008.DispStatus
    materaDispStaList["EXPDER_IOBR"]  = mcp23008.DispStatus
    materaDispStaList["CLK_BUF"]      = rc19013.DispStatus
    materaDispStaList["MEM_VDDIO"] = tps53688.DispStatus
    materaDispStaList["P12V"] = tps25990.DispStatus
    materaDispStaList["CPU_VDDCR"] = isl69247.DispStatus
    materaDispStaList["PSU_1"]   = dps2100.DispStatus
    materaDispStaList["PSU_2"]   = dps2100.DispStatus

    materaI2cHubMap = make(map[string]I2cHubInfo)

    //===============================
    // Taormina
    taorDispStaList = make(map[string]DispStaFunc)
    taorDispStaList["P0V8AVDD_GB_A"]   = tps549a20.DispStatus
    taorDispStaList["P0V8AVDD_GB_B"]   = tps549a20.DispStatus
    taorDispStaList["P0V8RT_B"]        = tps549a20.DispStatus
    taorDispStaList["TSENSOR-1"]       = tmp451.DispStatus
    taorDispStaList["TSENSOR-2"]       = lm75a.DispStatus
    taorDispStaList["TSENSOR-3"]       = lm75a.DispStatus
    taorDispStaList["P0V8RT_A"]        = tps544c20.DispStatus
    taorDispStaList["P3V3"]            = tps544c20.DispStatus
    taorDispStaList["P3V3S"]           = tps544c20.DispStatus
    taorDispStaList["TDNT_PDVDD"]      = tps53681.DispStatus
    taorDispStaList["TDNT_P0V8_AVDD"]  = tps53681.DispStatus
    taorDispStaList["CPU_P1V2_VDDQ"]       = sn1701022.DispStatus
    taorDispStaList["CPU_P1V05_COMBINED"]  = sn1701022.DispStatus
    taorDispStaList["CPU_PVCCIN"]           = sn1701022.DispStatus
    taorDispStaList["CPU_P1V05_VCCSCSUS"]  = sn1701022.DispStatus
    taorDispStaList["PSU_1"]            = dps800.DispStatus
    taorDispStaList["PSU_2"]            = dps800.DispStatus
    taorDispStaList["TSENSOR-CPU"]      = XeonD.DispStatus
    taorDispStaList["TSENSOR-TD3"]      = td3.DispStatus
    taorDispStaList["TSENSOR-ASIC0"]    = taorfpga.AsicCoreTemp
    taorDispStaList["TSENSOR-ASIC1"]    = taorfpga.AsicCoreTemp
    taorDispStaList["FAN_1"]   = adt7462.DispStatus
    taorDispStaList["FAN_2"]   = adt7462.DispStatus

    // ADD FIXME: NEEDS FILLING IN
    taorI2cHubMap = make(map[string]I2cHubInfo)

    //===============================
    // Lipari
    lipariDispStaList = make(map[string]DispStaFunc)
    lipariDispStaList["FAN"]      = liparifpga.DispFanStatus
    lipariDispStaList["MEM_VDDIO"]   = tps53688.DispStatus
    lipariDispStaList["P3V3S2"]   = tps53688.DispStatus
    lipariDispStaList["P3V3S1"]   = tps53688.DispStatus
    lipariDispStaList["P3V3"]     = mp8796.DispStatus
    lipariDispStaList["PSU_1"]   = dps2100.DispStatus
    lipariDispStaList["PSU_2"]   = dps2100.DispStatus

    //Just decalred.. not used on Lipari
    lipariI2cHubMap = make(map[string]I2cHubInfo)

    // Lipari ELBA
    lipariElbaDispStaList = make(map[string]DispStaFunc)
    lipariElbaDispStaList["VDD_DDR"]   = mp8796.DispStatus
    lipariElbaDispStaList["VDDQ_DDR"]   = mp8796.DispStatus
    lipariElbaDispStaList["ELB0_CORE"]   = mp2975.DispStatus
    lipariElbaDispStaList["ELB0_ARM"]   = mp2975.DispStatus

    // MtFuji ELBA
    mtfujiElbaDispStaList = make(map[string]DispStaFunc)
    mtfujiElbaDispStaList["VDD_DDR"]    = ltc3882.DispStatus
    mtfujiElbaDispStaList["VDDQ_DDR"]   = ltc3882.DispStatus
    mtfujiElbaDispStaList["ELB0_CORE"]  = ltc3882.DispStatus
    mtfujiElbaDispStaList["ELB0_CORE1"] = ltc3882.DispStatus
    mtfujiElbaDispStaList["ELB0_CORE2"] = ltc3882.DispStatus
    mtfujiElbaDispStaList["ELB0_ARM"]   = ltc3882.DispStatus

    // Capaci ELBA
    capaciElbaDispStaList = make(map[string]DispStaFunc)
    capaciElbaDispStaList["ELB0_CORE"] = tps53688.DispStatus
    capaciElbaDispStaList["ELB0_ARM"]  = tps53688.DispStatus

    //Just decalred.. not used on Lipari
    lipariElbaI2cHubMap = make(map[string]I2cHubInfo)

    //===============================
    mtpI2cHubMap = make(map[string]I2cHubInfo)
    mtpI2cHubMap["UUT_1"]  = I2cHubInfo{"HUB_1", 0}
    mtpI2cHubMap["UUT_2"]  = I2cHubInfo{"HUB_1", 1}
    mtpI2cHubMap["UUT_3"]  = I2cHubInfo{"HUB_1", 2}
    mtpI2cHubMap["UUT_4"]  = I2cHubInfo{"HUB_1", 3}
    mtpI2cHubMap["UUT_5"]  = I2cHubInfo{"HUB_2", 0}
    mtpI2cHubMap["UUT_6"]  = I2cHubInfo{"HUB_2", 1}
    mtpI2cHubMap["UUT_7"]  = I2cHubInfo{"HUB_2", 2}
    mtpI2cHubMap["UUT_8"]  = I2cHubInfo{"HUB_2", 3}
    mtpI2cHubMap["UUT_9"]  = I2cHubInfo{"HUB_3", 0}
    mtpI2cHubMap["UUT_10"] = I2cHubInfo{"HUB_3", 1}

    materaI2cHubMap = make(map[string]I2cHubInfo)
    materaI2cHubMap["UUT_1"]  = I2cHubInfo{"HUB_1", 0}
    materaI2cHubMap["UUT_2"]  = I2cHubInfo{"HUB_1", 1}
    materaI2cHubMap["UUT_3"]  = I2cHubInfo{"HUB_1", 2}
    materaI2cHubMap["UUT_4"]  = I2cHubInfo{"HUB_1", 3}
    materaI2cHubMap["UUT_5"]  = I2cHubInfo{"HUB_2", 0}
    materaI2cHubMap["UUT_6"]  = I2cHubInfo{"HUB_2", 1}
    materaI2cHubMap["UUT_7"]  = I2cHubInfo{"HUB_2", 2}
    materaI2cHubMap["UUT_8"]  = I2cHubInfo{"HUB_2", 3}
    materaI2cHubMap["UUT_9"]  = I2cHubInfo{"HUB_3", 0}
    materaI2cHubMap["UUT_10"] = I2cHubInfo{"HUB_3", 1}

    mtpI2cHubList := []string{"HUB_1", "HUB_2", "HUB_3", "HUB_4"}
    mtpsI2cHubList := []string{"HUB_1", "HUB_2", "HUB_3", "HUB_4", "HUB_5"}
    naplesMtpI2cHubList := []string{"NIC_HUB"}
    naples100I2cHubList := []string{"HUB_NONE"}
    naples25I2cHubList := []string{"HUB_NONE"}
    forioI2cHubList := []string{"HUB_NONE"}
    taorI2cHubList := []string{"HUB_NONE"}

    mtpPsuList := []string{"PSU_1", "PSU_2"}
    nicPsuList := []string{"PSU_NONE"}


    //===============================
    // NIC_POWER
    nicPwrDispStaList = make(map[string]DispStaFunc)
    nicPwrDispStaList["VRM_CAPRI_DVDD"] = tps53659.DispStatus
    nicPwrDispStaList["VRM_CAPRI_AVDD"] = tps53659.DispStatus
    nicPwrDispStaList["VRM_3V3"]        = tps549a20.DispStatus
    nicPwrDispStaList["VRM_1V2"]        = tps549a20.DispStatus

    //===============================
    // Dictionaries for all platforms
    // Display list
    dispMap = make(map[string]map[string]DispStaFunc)
    dispMap["FORIO"]       = forioDispStaList
    dispMap["NAPLES100"]   = naples100DispStaList
    dispMap["NAPLES100IBM"]= naples100DispStaList
    dispMap["NAPLES100HPE"]= naples100DispStaList
    dispMap["NAPLES100DELL"]= naples100DispStaList
    dispMap["NAPLES25"]    = naples25DispStaList
    dispMap["NAPLES25OCP"] = naples25DispStaList
    dispMap["NAPLES25SWM"] = naples25DispStaList
    dispMap["NAPLES25SWMDELL"] = naples25DispStaList
    dispMap["NAPLES25SWM833"] = naples25DispStaList
    dispMap["NAPLES25WFG"] = naples25DispStaList
    dispMap["NAPLES_MTP"]  = naplesMtpDispStaList
    dispMap["VOMERO"]      = forioDispStaList
    dispMap["VOMERO2"]     = forioDispStaList
    //===============================
    // Elba
    dispMap["BIODONA_D4"]   = biodonaDispStaList
    dispMap["BIODONA_D5"]   = biodonaDispStaList
    dispMap["ORTANO"]       = ortanoDispStaList
    dispMap["ORTANO2"]      = ortanoDispStaList
    dispMap["ORTANO2A"]     = ortanoaDispStaList
    dispMap["ORTANO2AC"]    = ortanoaDispStaList
    dispMap["ORTANO2I"]     = ortanoiDispStaList
    dispMap["ORTANO2S"]     = ortanoiDispStaList
    dispMap["LACONADELL"]   = laconaDispStaList
    dispMap["LACONA"]       = laconaDispStaList
    dispMap["LACONA32DELL"]  = laconaDispStaList
    dispMap["LACONA32"]     = laconaDispStaList
    dispMap["POMONTEDELL"]  = ortanoDispStaList
    dispMap["POMONTE"]      = ortanoDispStaList
    //===============================
    // Giglio
    dispMap["GINESTRA_D4"]   = ginestraD4DispStaList
    dispMap["GINESTRA_D5"]   = ginestraD5DispStaList
    //===============================
    // Salina
    dispMap["MALFA"]        = malfaDispStaList
    dispMap["MALFA_S"]      = malfaDispStaList
    dispMap["POLLARA"]      = pollaraDispStaList
    dispMap["LENI"]         = leniDispStaList
    dispMap["LENI48G"]      = leniDispStaList
    dispMap["LINGUA"]       = linguaDispStaList
    //===============================
    dispMap["MTP"]         = mtpDispStaList
    dispMap["MTPS"]        = mtpsDispStaList
    dispMap["MTP_MATERA"]  = materaDispStaList
    dispMap["NIC_POWER"]   = nicPwrDispStaList
    //===============================
    // Taormina
    dispMap["TAORMINA"]  = taorDispStaList

    // Lipari
    dispMap["LIPARI"]  = lipariDispStaList
    dispMap["LIPARIELBA"]  = lipariElbaDispStaList

    // MtFuji (Cisco)
    dispMap["MTFUJI"]  = mtfujiElbaDispStaList

    // Capaci (HPE)
    dispMap["CAPACI"]  = capaciElbaDispStaList

    // EEPROM list
    eepromMap = make(map[string][]string)
    eepromMap["FORIO"]         = naplesEepList
    eepromMap["NAPLES_MTP"]    = naplesEepList
    eepromMap["NAPLES100"]     = naplesEepList
    eepromMap["NAPLES100IBM"]  = naplesEepList
    eepromMap["NAPLES100HPE"]  = naplesEepList
    eepromMap["NAPLES100DELL"]  = naplesEepList
    eepromMap["NAPLES25"]      = naplesEepList
    eepromMap["NAPLES25OCP"]   = naplesEepList
    eepromMap["NAPLES25SWM"]   = naplesEepList
    eepromMap["NAPLES25SWMDELL"] = naplesEepList
    eepromMap["NAPLES25SWM833"] = naplesEepList
    eepromMap["NAPLES25WFG"]   = naplesEepList
    eepromMap["VOMERO"]        = naplesEepList
    eepromMap["VOMERO2"]       = naplesEepList
    //===============================
    // Elba
    eepromMap["BIODONA_D4"]   = naplesEepList
    eepromMap["BIODONA_D5"]   = naplesEepList
    eepromMap["ORTANO"]       = naplesEepList
    eepromMap["ORTANO2"]      = naplesEepList
    eepromMap["ORTANO2A"]     = naplesEepList
    eepromMap["ORTANO2AC"]    = naplesEepList
    eepromMap["ORTANO2I"]     = naplesEepList
    eepromMap["ORTANO2S"]     = naplesEepList
    eepromMap["LACONADELL"]   =  naplesEepList
    eepromMap["LACONA"]       =  naplesEepList
    eepromMap["LACONA32DELL"]  =  naplesEepList
    eepromMap["LACONA32"]     =  naplesEepList
    eepromMap["POMONTEDELL"]  =  naplesEepList
    eepromMap["POMONTE"]      =  naplesEepList
    //===============================
    // Giglio
    eepromMap["GINESTRA_D4"]   = GinestraEepList
    eepromMap["GINESTRA_D5"]   = GinestraEepList

    //===============================
    eepromMap["MTP"]           = mtpEepList
    eepromMap["MTPS"]          = mtpEepList
    eepromMap["MTP_MATERA"]    = materaEepList
    //===============================
    // Taormina
    eepromMap["TAORMINA"]          = naplesEepList
    //Lipari
    eepromMap["LIPARI"]            = lipariEepList
    // Salina
    eepromMap["MALFA"]             = MalfaEepList
    eepromMap["POLLARA"]           = PollaraEepList
    eepromMap["LENI"]              = LeniEepList
    eepromMap["LENI48G"]           = LeniEepList
    eepromMap["LINGUA"]            = LinguaEepList

    // I2C hub map
    i2cHubMap = make(map[string]map[string]I2cHubInfo)
    i2cHubMap["MTP"] = mtpI2cHubMap
    // MTP=MTPS
    i2cHubMap["MTPS"]           = mtpI2cHubMap
    // MTP_MATERA
    i2cHubMap["MTP_MATERA"]     = materaI2cHubMap

    i2cHubMap["NAPLES100"]      = naples100I2cHubMap
    i2cHubMap["NAPLES100IBM"]   = naples100I2cHubMap
    i2cHubMap["NAPLES100HPE"]   = naples100I2cHubMap
    i2cHubMap["NAPLES100DELL"]   = naples100I2cHubMap
    i2cHubMap["NAPLES25"]       = naples100I2cHubMap
    i2cHubMap["NAPLES25OCP"]    = naples100I2cHubMap
    i2cHubMap["NAPLES25SWM"]    = naples100I2cHubMap
    i2cHubMap["NAPLES25SWMDELL"]= naples100I2cHubMap
    i2cHubMap["NAPLES25SWM833"] = naples100I2cHubMap
    i2cHubMap["NAPLES25WFG"]    = naples100I2cHubMap
    i2cHubMap["FORIO"]          = naples100I2cHubMap
    i2cHubMap["VOMERO"]         = naples100I2cHubMap
    i2cHubMap["VOMERO2"]        = naples100I2cHubMap
    //===============================
    // Elba
    i2cHubMap["BIODONA_D4"]     = naples100I2cHubMap
    i2cHubMap["BIODONA_D5"]     = naples100I2cHubMap
    i2cHubMap["ORTANO"]         = naples100I2cHubMap
    i2cHubMap["ORTANO2"]        = naples100I2cHubMap
    i2cHubMap["ORTANO2A"]       = naples100I2cHubMap
    i2cHubMap["ORTANO2AC"]      = naples100I2cHubMap
    i2cHubMap["ORTANO2I"]       = naples100I2cHubMap
    i2cHubMap["ORTANO2S"]       = naples100I2cHubMap
    i2cHubMap["LACONADELL"]     = naples100I2cHubMap
    i2cHubMap["LACONA"]         = naples100I2cHubMap
    i2cHubMap["LACONA32DELL"]    = naples100I2cHubMap
    i2cHubMap["LACONA32"]       = naples100I2cHubMap
    i2cHubMap["POMONTEDELL"]    = naples100I2cHubMap
    i2cHubMap["POMONTE"]        = naples100I2cHubMap
    //===============================
    // Giglio
    i2cHubMap["GINESTRA_D4"]        = naples100I2cHubMap
    i2cHubMap["GINESTRA_D5"]        = naples100I2cHubMap
    // Salina
    i2cHubMap["MALFA"]          = materaI2cHubMap
    i2cHubMap["POLLARA"]        = materaI2cHubMap
    i2cHubMap["LENI"]           = materaI2cHubMap
    i2cHubMap["LENI48G"]        = materaI2cHubMap
    i2cHubMap["LINGUA"]         = materaI2cHubMap

    //===============================
    // Taormina
    i2cHubMap["TAORMINA"]     = taorI2cHubMap

    //===============================
    // Lipari
    i2cHubMap["LIPARI"]     = lipariI2cHubMap
    i2cHubMap["LIPARIELBA"] = lipariElbaI2cHubMap

    i2cHubListMap = make(map[string][]string)
    i2cHubListMap["MTP"]           = mtpI2cHubList
    i2cHubListMap["MTPS"]          = mtpsI2cHubList
    i2cHubListMap["NAPLES_MTP"]    = naplesMtpI2cHubList
    i2cHubListMap["NAPLES100"]     = naples100I2cHubList
    i2cHubListMap["NAPLES100IBM"]  = naples100I2cHubList
    i2cHubListMap["NAPLES100HPE"]  = naples100I2cHubList
    i2cHubListMap["NAPLES100DELL"]  = naples100I2cHubList
    i2cHubListMap["NAPLES25"]      = naples25I2cHubList
    i2cHubListMap["NAPLES25OCP"]   = naples25I2cHubList
    i2cHubListMap["NAPLES25SWM"]   = naples25I2cHubList
    i2cHubListMap["NAPLES25SWMDELL"] = naples25I2cHubList
    i2cHubListMap["NAPLES25SWM833"] = naples25I2cHubList
    i2cHubListMap["NAPLES25WFG"]   = naples25I2cHubList
    i2cHubListMap["FORIO"]         = forioI2cHubList
    i2cHubListMap["VOMERO"]        = forioI2cHubList
    i2cHubListMap["VOMERO2"]       = forioI2cHubList
    //===============================
    // Elba
    i2cHubListMap["BIODONA_D4"]    = forioI2cHubList
    i2cHubListMap["BIODONA_D5"]    = forioI2cHubList
    i2cHubListMap["ORTANO"]        = forioI2cHubList
    i2cHubListMap["ORTANO2"]       = forioI2cHubList
    i2cHubListMap["ORTANO2A"]      = forioI2cHubList
    i2cHubListMap["ORTANO2AC"]     = forioI2cHubList
    i2cHubListMap["ORTANO2I"]      = forioI2cHubList
    i2cHubListMap["ORTANO2S"]      = forioI2cHubList
    i2cHubListMap["LACONADELL"]    = forioI2cHubList
    i2cHubListMap["LACONA"]        = forioI2cHubList
    i2cHubListMap["LACONA32DELL"]   = forioI2cHubList
    i2cHubListMap["LACONA32"]      = forioI2cHubList
    i2cHubListMap["POMONTEDELL"]   = forioI2cHubList
    i2cHubListMap["POMONTE"]       = forioI2cHubList
    //===============================
    // Giglio
    i2cHubListMap["GINESTRA_D4"]    = forioI2cHubList
    i2cHubListMap["GINESTRA_D5"]    = forioI2cHubList

    //===============================
    // Taormina
    i2cHubListMap["TAORMINA"] = taorI2cHubList

    // PSU list
    psuListMap = make(map[string][]string)
    psuListMap["MTP"]          = mtpPsuList
    psuListMap["MTPS"]         = mtpPsuList
    psuListMap["MTP_MATERA"]   = mtpPsuList
    psuListMap["NAPLES100"]    = nicPsuList
    psuListMap["NAPLES100IBM"] = nicPsuList
    psuListMap["NAPLES100HPE"] = nicPsuList
    psuListMap["NAPLES100DELL"] = nicPsuList
    psuListMap["NAPLES25"]     = nicPsuList
    psuListMap["NAPLES25OCP"]  = nicPsuList
    psuListMap["NAPLES25SWM"]  = nicPsuList
    psuListMap["NAPLES25SWMDELL"] = nicPsuList
    psuListMap["NAPLES25SWM833"] = nicPsuList
    psuListMap["NAPLES25WFG"]  = nicPsuList
    psuListMap["FORIO"]        = nicPsuList
    psuListMap["VOMERO"]       = nicPsuList
    psuListMap["VOMERO2"]      = nicPsuList
    //===============================
    // Elba
    psuListMap["BIODONA_D4"]    = nicPsuList
    psuListMap["BIODONA_D5"]    = nicPsuList
    psuListMap["ORTANO"]        = nicPsuList
    psuListMap["ORTANO2"]       = nicPsuList
    psuListMap["ORTANO2A"]      = nicPsuList
    psuListMap["ORTANO2AC"]      = nicPsuList
    psuListMap["ORTANO2I"]      = nicPsuList
    psuListMap["ORTANO2S"]      = nicPsuList
    psuListMap["LACONADELL"]    = nicPsuList
    psuListMap["LACONA"]        = nicPsuList
    psuListMap["LACONA32DELL"]   = nicPsuList
    psuListMap["LACONA32"]      = nicPsuList
    psuListMap["POMONTEDELL"]   = nicPsuList
    psuListMap["POMONTE"]       = nicPsuList
    //===============================
    // Giglio
    psuListMap["GINESTRA_D4"]    = nicPsuList
    psuListMap["GINESTRA_D5"]    = nicPsuList

    //===============================
    // Taormina
    i2cHubListMap["TAORMINA"] = taorI2cHubList

    //===============================
    // Platform specified list
    // Remark: map may not support all platforms
    cardType = os.Getenv("CARD_TYPE")
    DispStaList, _   = dispMap[cardType]
    //PmbusTestList, _ = pmbusTestMap[cardType]
    EepromList, _    = eepromMap[cardType]
    I2cHubMap, _     = i2cHubMap[cardType]
    I2cHubList, _    = i2cHubListMap[cardType]
    PsuList, _       = psuListMap[cardType]

    //===============================
    // Use switch case to avoid dummy data structure
    switch cardType {
    case "NAPLES100", "NAPLES100IBM", "NAPLES100HPE", "NAPLES100DELL", "BIODONA_D4", "BIODONA_D5":
        QsfpTbl = naples100QsfpTbl
        var t boardinfo.NicCpld_T
        yaml.Unmarshal([]byte(boardinfo.NicCpld), &t)
        CpldInfo = &t
    case "NAPLES25", "NAPLES25SWM", "NAPLES25SWMDELL", "NAPLES25SWM833", "NAPLES25OCP", "NAPLES25WFG",
         "LACONADELL", "LACONA", "LACONA32DELL", "LACONA32":
        SfpTbl = naples25SfpTbl
        var t boardinfo.Naples25Cpld_T
        yaml.Unmarshal([]byte(boardinfo.Naples25Cpld), &t)
        CpldInfo = &t
    case "FORIO", "VOMERO", "VOMERO2", "ORTANO", "ORTANO2", "ORTANO2A", "ORTANO2AC", "ORTANO2I", "ORTANO2S", "POMONTE", "POMONTEDELL",
         "GINESTRA_D4", "GINESTRA_D5":
        QsfpTbl = forioQsfpTbl
        var t boardinfo.ForioCpld_T
        yaml.Unmarshal([]byte(boardinfo.ForioCpld), &t)
        CpldInfo = &t

    case "TAORMINA":
        SfpTbl = taorSfpTbl
        QsfpTbl = taorQsfpTbl

    default:
        QsfpTbl = nil
        // Do nothing
    }
}

