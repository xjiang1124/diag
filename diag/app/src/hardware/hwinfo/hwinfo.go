package hwinfo

import (
    "os"

    "device/boardinfo"
    "device/fanctrl/adt7462"
    "device/powermodule/tps53659"
    "device/powermodule/tps549a20"
    "device/psu/pet1600"
    "device/tempsensor/tmp42123"

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

//===============================
// Naples common 
var CpldInfo interface{}

// EEPROM list
var naplesEepList = []string {"FRU"}

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
// MTP
// Status display list
var mtpDispStaList map[string]DispStaFunc
// EEPROM list
var mtpEepList = []string {"FRU"}
// I2C hub map
var mtpI2cHubMap map[string] I2cHubInfo

//===============================
// MTP
// Status display list
var mtpsDispStaList map[string]DispStaFunc

//===============================
// NIC POWER
// Status display list
var nicPwrDispStaList map[string]DispStaFunc

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

    mtpI2cHubList := []string{"HUB_1", "HUB_2", "HUB_3", "HUB_4"}
    mtpsI2cHubList := []string{"HUB_1", "HUB_2", "HUB_3", "HUB_4", "HUB_5"}
    naplesMtpI2cHubList := []string{"NIC_HUB"}
    naples100I2cHubList := []string{"HUB_NONE"}
    naples25I2cHubList := []string{"HUB_NONE"}
    forioI2cHubList := []string{"HUB_NONE"}

    mtpPsuList := []string{"PSU_1", "PSU_2"}
    naples100PsuList := []string{"PSU_NONE"}
    naples25PsuList := []string{"PSU_NONE"}
    forioPsuList := []string{"PSU_NONE"}


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
    dispMap["VOMERO"]      = forioDispStaList
    dispMap["VOMERO2"]      = forioDispStaList
    dispMap["NAPLES100"]   = naples100DispStaList
    dispMap["NAPLES100IBM"]= naples100DispStaList
    dispMap["NAPLES25"]    = naples25DispStaList
    dispMap["NAPLES25OCP"] = naples25DispStaList
    dispMap["NAPLES25SWM"] = naples25DispStaList
    dispMap["NAPLES25WFG"] = naples25DispStaList
    dispMap["NAPLES_MTP"]  = naplesMtpDispStaList
    dispMap["MTP"]         = mtpDispStaList
    dispMap["MTPS"]        = mtpsDispStaList
    dispMap["NIC_POWER"]   = nicPwrDispStaList

    // EEPROM list
    eepromMap = make(map[string][]string)
    eepromMap["MTP"]           = mtpEepList
    eepromMap["MTPS"]          = mtpEepList
    eepromMap["NAPLES_MTP"]    = naplesEepList
    eepromMap["NAPLES100"]     = naplesEepList
    eepromMap["NAPLES100IBM"]  = naplesEepList
    eepromMap["NAPLES25"]      = naplesEepList
    eepromMap["NAPLES25OCP"]   = naplesEepList
    eepromMap["NAPLES25SWM"]   = naplesEepList
    eepromMap["NAPLES25WFG"]   = naplesEepList
    eepromMap["FORIO"]         = naplesEepList
    eepromMap["VOMERO"]        = naplesEepList
    eepromMap["VOMERO2"]        = naplesEepList

    // I2C hub map
    i2cHubMap = make(map[string]map[string]I2cHubInfo)
    i2cHubMap["MTP"] = mtpI2cHubMap
    // MTP=MTPS
    i2cHubMap["MTPS"]           = mtpI2cHubMap
    i2cHubMap["NAPLES100"]      = naples100I2cHubMap
    i2cHubMap["NAPLES100IBM"]   = naples100I2cHubMap
    i2cHubMap["NAPLES25"]       = naples100I2cHubMap
    i2cHubMap["NAPLES25OCP"]    = naples100I2cHubMap
    i2cHubMap["NAPLES25SWM"]    = naples100I2cHubMap
    i2cHubMap["NAPLES25WFG"]    = naples100I2cHubMap
    i2cHubMap["FORIO"]          = naples100I2cHubMap
    i2cHubMap["VOMERO"]         = naples100I2cHubMap
    i2cHubMap["VOMERO2"]         = naples100I2cHubMap

    i2cHubListMap = make(map[string][]string)
    i2cHubListMap["MTP"]           = mtpI2cHubList
    i2cHubListMap["MTPS"]          = mtpsI2cHubList
    i2cHubListMap["NAPLES_MTP"]    = naplesMtpI2cHubList
    i2cHubListMap["NAPLES100"]     = naples100I2cHubList
    i2cHubListMap["NAPLES100IBM"]  = naples100I2cHubList
    i2cHubListMap["NAPLES25"]      = naples25I2cHubList
    i2cHubListMap["NAPLES25OCP"]   = naples25I2cHubList
    i2cHubListMap["NAPLES25SWM"]   = naples25I2cHubList
    i2cHubListMap["NAPLES25WFG"]   = naples25I2cHubList
    i2cHubListMap["FORIO"]         = forioI2cHubList
    i2cHubListMap["VOMERO"]        = forioI2cHubList
    i2cHubListMap["VOMERO2"]        = forioI2cHubList

    // PSU list
    psuListMap = make(map[string][]string)
    psuListMap["MTP"]          = mtpPsuList
    psuListMap["MTPS"]         = mtpPsuList
    psuListMap["NAPLES100"]    = naples100PsuList
    psuListMap["NAPLES100IBM"]  = naples100PsuList
    psuListMap["NAPLES25"]     = naples25PsuList
    psuListMap["NAPLES25OCP"]  = naples25PsuList
    psuListMap["NAPLES25SWM"]  = naples25PsuList
    psuListMap["NAPLES25WFG"]  = naples25PsuList
    psuListMap["FORIO"]        = forioPsuList
    psuListMap["VOMERO"]       = forioPsuList
    psuListMap["VOMERO2"]       = forioPsuList

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
    case "NAPLES100", "NAPLES100IBM":
        QsfpTbl = naples100QsfpTbl
        var t boardinfo.Naples100Cpld_T
        yaml.Unmarshal([]byte(boardinfo.Naples100Cpld), &t)
        CpldInfo = &t
    case "NAPLES25", "NAPLES25SWM", "NAPLES25OCP", "NAPLES25WFG":
        SfpTbl = naples25SfpTbl
        var t boardinfo.Naples25Cpld_T
        yaml.Unmarshal([]byte(boardinfo.Naples25Cpld), &t)
        CpldInfo = &t
    case "FORIO", "VOMERO", "VOMERO2":
        QsfpTbl = forioQsfpTbl
        var t boardinfo.ForioCpld_T
        yaml.Unmarshal([]byte(boardinfo.ForioCpld), &t)
        CpldInfo = &t

    default:
        // Do nothing
    }
}

