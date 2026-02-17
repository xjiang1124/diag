package i2cinfo

import (
    "fmt"
    "os"
    "os/exec"
    "runtime"
    "strconv"
    "strings"
    "common/cli"
    "common/errType"
)

var CardType string
var uutType string
var itpType string
var itpIdx byte

type I2cInfo struct {
    Name    string
    Comp    string
    Bus     uint32 // I2C controllor index
    DevAddr byte
    Page    byte   // PMBus device page number
    HubName string
    HubPort byte
    Flag    byte
}

type I2cFpgaMap struct {
    DevName     string
    Bus         uint32
    Mux         uint32
    I2cAddr     uint32
    OffsetLen   int
}

type I2cSensorCoeff struct {
    Coeff float64
}
type I2cSensorInfo struct {
    Name  string
    Sense_Resistor I2cSensorCoeff
}

//I2cInfo Flag Defines

const (
    FLAG_EMPTY = (0<<1)
    FLAG_8BIT_EEPROM = (1<<1)
    FLAG_16BIT_EEPROM = (2<<1)
    I2C_TEST_ENABLE = (3<<1)
    EXTERNAL_VMARG = (4<<1)
)

var I2cTbl    []I2cInfo
//var UutI2cTbl []I2cInfo
var CurI2cTbl []I2cInfo
var SensorTbl []I2cSensorInfo
var CurSensorTbl []I2cSensorInfo


//=========================================
// Naples100 I2C table on ARM
// devAddr is 7-bit address
var Naples100Tbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"CAP0_CORE_DVDD", "TPS53659",  0x2,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CAP0_ARM",       "TPS53659",  0x2,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"CAP0_3V3",       "TPS549A20", 0x2,   0x1a,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CAP0_HBM",       "TPS549A20", 0x2,   0x1b,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CAP0_CORE_AVDD", "TPS549A20", 0x2,   0x1C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x2,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"RTC",            "PCF85263A", 0x2,   0x51,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR",        "TMP422",    0x2,   0x4C,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_1",         "QSFP",      0x0,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"QSFP_1_DOM",     "QSFP",      0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_2",         "QSFP",      0x1,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"QSFP_2_DOM",     "QSFP",      0x1,   0x51,    0x0,    "HUB_NONE",  0,    0},
}

// Naples100 I2C table on MTP SMBus
var Naples100MtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x76,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    0},
}

var OrtanoADITbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"TSENSOR",        "TMPADICOM", 0x0,   0x4C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SPD",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_8BIT_EEPROM},
    I2cInfo {"RTC",            "PCF85263A", 0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_CORE",      "LTC3888",   0x0,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_ARM",       "LTC3888",   0x0,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"VRM_IIN",        "LTC2301",   0x0,   0x08,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_1",         "QSFP",      0x1,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"QSFP_1_DOM",     "QSFP",      0x1,   0x51,    0x0,    "HUB_CPLD",  0,    0},

    I2cInfo {"QSFP_2",         "QSFP",      0x2,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"QSFP_2_DOM",     "QSFP",      0x2,   0x51,    0x0,    "HUB_CPLD",  0,    0},
}

var OrtanoIBASETbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"SPD",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_8BIT_EEPROM},
    I2cInfo {"RTC",            "PCF85263A", 0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_1",         "QSFP",      0x1,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"QSFP_1_DOM",     "QSFP",      0x1,   0x51,    0x0,    "HUB_CPLD",  0,    0},

    I2cInfo {"QSFP_2",         "QSFP",      0x2,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"QSFP_2_DOM",     "QSFP",      0x2,   0x51,    0x0,    "HUB_CPLD",  0,    0},
}

var Ortano2SBASETbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"SPD",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_8BIT_EEPROM},
    I2cInfo {"RTC",            "PCF85263A", 0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_1",         "QSFP",      0x1,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"QSFP_1_DOM",     "QSFP",      0x1,   0x51,    0x0,    "HUB_CPLD",  0,    0},

    I2cInfo {"QSFP_2",         "QSFP",      0x2,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"QSFP_2_DOM",     "QSFP",      0x2,   0x51,    0x0,    "HUB_CPLD",  0,    0},

    I2cInfo {"ELB0_CORE",      "TPS53659A", 0x0,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_ARM",       "TPS53659A", 0x0,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"VDD_DDR",        "TPS549A20", 0x0,   0x1C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VDDQ_DDR",       "TPS549A20", 0x0,   0x1B,    0x0,    "HUB_NONE",  0,    0},
}

var OrtanoIPODTbl0 = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"ELB0_CORE",      "TPS53659A", 0x0,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_ARM",       "TPS53659A", 0x0,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"VDD_DDR",        "TPS549A20", 0x0,   0x1C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VDDQ_DDR",       "TPS549A20", 0x0,   0x1B,    0x0,    "HUB_NONE",  0,    0},
}

var OrtanoITMPTbl0 = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"TSENSOR",        "TMP422",    0x0,   0x4C,    0x0,    "HUB_NONE",  0,    0},
}

var OrtanoIPODTbl = [8][]I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    nil,
   { I2cInfo {"ELB0_CORE",      "TPS53659A", 0x0,   0x62,    0x0,    "HUB_NONE",  0,    0},
     I2cInfo {"ELB0_ARM",       "TPS53659A", 0x0,   0x62,    0x1,    "HUB_NONE",  0,    0},
     I2cInfo {"VDD_DDR",        "TPS549A20", 0x0,   0x1C,    0x0,    "HUB_NONE",  0,    0},
     I2cInfo {"VDDQ_DDR",       "TPS549A20", 0x0,   0x1B,    0x0,    "HUB_NONE",  0,    0},},
   nil,
   nil,
   nil,
   nil,
   nil,
   nil,
}

var OrtanoITMPTbl = [4][]I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    { I2cInfo {"TSENSOR",        "TMP451",    0x0,   0x4C,    0x0,    "HUB_NONE",  0,    0},},
    { I2cInfo {"TSENSOR",        "ADM1032",   0x0,   0x4C,    0x0,    "HUB_NONE",  0,    0},},
    nil,
    nil,
}

var Ortano2STMPTbl = [2][]I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    { I2cInfo {"TSENSOR",        "ADM1032",   0x0,   0x4C,    0x0,    "HUB_NONE",  0,    0},},
    { I2cInfo {"TSENSOR",        "TMP451",    0x0,   0x4C,    0x0,    "HUB_NONE",  0,    0},},
}

var OrtanoTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"TSENSOR",        "TMP451",    0x0,   0x4C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SPD",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_8BIT_EEPROM},
    I2cInfo {"RTC",            "PCF85263A", 0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_CORE",      "TPS53659A", 0x0,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_ARM",       "TPS53659A", 0x0,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"VDD_DDR",        "TPS549A20", 0x0,   0x1C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VDDQ_DDR",       "TPS544B25", 0x0,   0x24,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_1",         "QSFP",      0x1,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"QSFP_1_DOM",     "QSFP",      0x1,   0x51,    0x0,    "HUB_CPLD",  0,    0},

    I2cInfo {"QSFP_2",         "QSFP",      0x2,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"QSFP_2_DOM",     "QSFP",      0x2,   0x51,    0x0,    "HUB_CPLD",  0,    0},
}

var GinestraD5Tbl = []I2cInfo {
    //       name               comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"PCIE_FRU",        "AT24C02C",  0x3,   0x53,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},

    I2cInfo {"FRU",             "AT24C02C",  0x2,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"TSENSOR",         "TMPADICOM", 0x2,   0x4C,    0x0,    "HUB_NONE",  0,    0},//to support second source part
    I2cInfo {"RTC",             "PCF85263A", 0x2,   0x51,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"GIG0_CORE",       "TPS53688",  0x2,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"GIG0_ARM",        "TPS53688",  0x2,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"DDR_VDD",         "PMIC",      0x2,   0x4F,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"DDR_VDDQ",        "PMIC",      0x2,   0x4F,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"DDR_VPP",         "PMIC",      0x2,   0x4F,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VDD_DDR",         "TPS549A20", 0x2,   0x1C,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_1",          "QSFP",      0x0,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"QSFP_1_DOM",      "QSFP",      0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_2",          "QSFP",      0x1,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"QSFP_2_DOM",      "QSFP",      0x1,   0x51,    0x0,    "HUB_NONE",  0,    0},
}

var GinestraD4Tbl = []I2cInfo {
    //       name               comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"PCIE_FRU",        "AT24C02C",  0x3,   0x53,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},

    I2cInfo {"FRU",             "AT24C02C",  0x2,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"TSENSOR",         "TMP451",    0x2,   0x4C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"RTC",             "PCF85263A", 0x2,   0x51,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"GIG0_CORE",       "TPS53688",  0x2,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"GIG0_ARM",        "TPS53688",  0x2,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"DDR_VDDQ",        "TPS549A20", 0x2,   0x1B,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VDD_DDR",         "TPS549A20", 0x2,   0x1C,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_1",          "QSFP",      0x0,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"QSFP_1_DOM",      "QSFP",      0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_2",          "QSFP",      0x1,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"QSFP_2_DOM",      "QSFP",      0x1,   0x51,    0x0,    "HUB_NONE",  0,    0},
}

var GinestraMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CPLD_MCTP",      "CPLD",      0x0,   0x61,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x53,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
}

var MalfaMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x53,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"DPU_FRU",        "AT24C02C",  0x2,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    //READ/WRITE TO CPLD UMF2 FLASH. 
    I2cInfo {"CPLD_FRU",       "MACHXO3",   0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    //READ FROM THE I2C INTERFACE FOR the CPLD UMF2 EEPROM
    I2cInfo {"CPLD_FRU_I2C",   "MACHXO3",   0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
}

var MalfaTbl  = []I2cInfo {
    //       name             comp         Bus    devAddr  page    HubName  HubPort  Flag 
    I2cInfo {"P12V_AUX",      "TPS53688",  0x2,   0x60,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"P12V_AUX_ADC",  "AD7997",    0x2,   0x23,    0x2,    "HUB_NONE", 0,    0},
    I2cInfo {"P12V",          "INA3221A",  0x2,   0x43,    0x1,    "HUB_NONE", 0,    0},
    I2cInfo {"P12V_ADC",      "AD7997",    0x2,   0x23,    0x1,    "HUB_NONE", 0,    0},
    I2cInfo {"CORE",          "TPS53688",  0x2,   0x60,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"ARM",           "TPS53688",  0x2,   0x60,    0x1,    "HUB_NONE", 0,    0},
    I2cInfo {"P3V3",          "INA3221A",  0x2,   0x43,    0x2,    "HUB_NONE", 0,    0},
    I2cInfo {"VDD_DDR",       "INA3221A",  0x2,   0x43,    0x3,    "HUB_NONE", 0,    0},
    I2cInfo {"P1V8",          "INA3221A",  0x2,   0x41,    0x1,    "HUB_NONE", 0,    0},
    I2cInfo {"VDDQ",          "INA3221A",  0x2,   0x41,    0x2,    "HUB_NONE", 0,    0},
    I2cInfo {"VDD_075_MX",    "INA3221A",  0x2,   0x41,    0x3,    "HUB_NONE", 0,    EXTERNAL_VMARG},
    I2cInfo {"VDD_075_PCIE",  "INA3221A",  0x2,   0x42,    0x1,    "HUB_NONE", 0,    EXTERNAL_VMARG},
    I2cInfo {"VDD_12_MX",     "INA3221A",  0x2,   0x42,    0x2,    "HUB_NONE", 0,    EXTERNAL_VMARG},
    I2cInfo {"VDD_12_PCIE",   "INA3221A",  0x2,   0x42,    0x3,    "HUB_NONE", 0,    EXTERNAL_VMARG},
    I2cInfo {"VDD_075_PLL",   "AD7997",    0x2,   0x23,    0x3,    "HUB_NONE", 0,    0},
    I2cInfo {"ISENSE_1",      "INA3221A",  0x2,   0x43,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"ISENSE_2",      "INA3221A",  0x2,   0x42,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"ISENSE_3",      "INA3221A",  0x2,   0x41,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"VDD_12_PCIE_VM","DS4424",    0x2,   0x30,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"VDD_12_MX_VM",  "DS4424",    0x2,   0x30,    0x1,    "HUB_NONE", 0,    0},
    I2cInfo {"VDD_075_PCIE_VM","DS4424",   0x2,   0x30,    0x2,    "HUB_NONE", 0,    0},
    I2cInfo {"VDD_075_MX_VM", "DS4424",    0x2,   0x30,    0x3,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VDD_0",     "PMIC",      0x0,   0x4E,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VDDQ_0",    "PMIC",      0x0,   0x4E,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VPP_0",     "PMIC",      0x0,   0x4E,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VDD_1",     "PMIC",      0x0,   0x4F,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VDDQ_1",    "PMIC",      0x0,   0x4F,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VPP_1",     "PMIC",      0x0,   0x4F,    0x0,    "HUB_NONE", 0,    0},

    I2cInfo {"RTC",           "PCF85263A", 0x2,   0x51,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"PCIE_CLK_BUF",  "RC19008",   0x2,   0x6C,    0x0,    "HUB_NONE", 0,    0}, // 100MHz clk
    I2cInfo {"MX_CLK_BUF",    "RC19004",   0x2,   0x6F,    0x0,    "HUB_NONE", 0,    0}, // 156MHz clk
    I2cInfo {"TSENSOR",       "TMP451",    0x2,   0x4C,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"FRU",           "AT24C02C",  0x3,   0x53,    0x0,    "HUB_NONE", 0,    FLAG_16BIT_EEPROM}, // 4K * 8 bit
    I2cInfo {"DPU_FRU",       "AT24C02C",  0x2,   0x52,    0x0,    "HUB_NONE", 0,    FLAG_16BIT_EEPROM}, // 4K * 8 bit
}

var MalfaSensorTbl = []I2cSensorInfo {
    I2cSensorInfo {"P12V_ADC",      I2cSensorCoeff{ 0.06 }},
    I2cSensorInfo {"P12V_AUX_ADC",  I2cSensorCoeff{ 0.06 }},
    I2cSensorInfo {"P12V",          I2cSensorCoeff{ 0.002 }},
    I2cSensorInfo {"P12V_AUX",      I2cSensorCoeff{ 0.002 }},
    I2cSensorInfo {"P3V3",          I2cSensorCoeff{ 0.001 }},
    I2cSensorInfo {"VDD_DDR",       I2cSensorCoeff{ 0.001 }},
    I2cSensorInfo {"P1V8",          I2cSensorCoeff{ 0.02 }},
    I2cSensorInfo {"VDDQ",          I2cSensorCoeff{ 0.1 }},
    I2cSensorInfo {"VDD_075_MX",    I2cSensorCoeff{ 0.005 }},
    I2cSensorInfo {"VDD_075_PCIE",  I2cSensorCoeff{ 0.005 }},
    I2cSensorInfo {"VDD_12_MX",     I2cSensorCoeff{ 0.005 }},
    I2cSensorInfo {"VDD_12_PCIE",   I2cSensorCoeff{ 0.005 }},
}

var PollaraMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x53,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"DPU_FRU",        "AT24C02C",  0x2,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    //READ/WRITE TO CPLD UMF2 FLASH. 
    I2cInfo {"CPLD_FRU",       "MACHXO3",   0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    //READ FROM THE I2C INTERFACE FOR the CPLD UMF2 EEPROM
    I2cInfo {"CPLD_FRU_I2C",   "MACHXO3",   0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
}

var PollaraTbl = []I2cInfo {
    //       name             comp         Bus    devAddr  page    HubName  HubPort  Flag 
    I2cInfo {"P12V",          "TPS53688",  0x2,   0x60,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"CORE",          "TPS53688",  0x2,   0x60,    0x0,    "HUB_NONE", 0,    0},

    I2cInfo {"RTC",           "PCF85263A", 0x2,   0x51,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"PCIE_CLK_BUF",  "RC19008",   0x2,   0x6C,    0x0,    "HUB_NONE", 0,    0}, // 100MHz clk
    I2cInfo {"MX_CLK_BUF",    "RC19004",   0x2,   0x6F,    0x0,    "HUB_NONE", 0,    0}, // 156MHz clk
    I2cInfo {"TSENSOR",       "TMP451",    0x2,   0x4C,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"FRU",           "AT24C02C",  0x3,   0x53,    0x0,    "HUB_NONE", 0,    FLAG_16BIT_EEPROM},
    I2cInfo {"DPU_FRU",       "AT24C02C",  0x2,   0x52,    0x0,    "HUB_NONE", 0,    FLAG_16BIT_EEPROM},
}

var LeniMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x53,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"DPU_FRU",        "AT24C02C",  0x2,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    //READ/WRITE TO CPLD UMF2 FLASH. 
    I2cInfo {"CPLD_FRU",       "MACHXO3",   0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    //READ FROM THE I2C INTERFACE FOR the CPLD UMF2 EEPROM
    I2cInfo {"CPLD_FRU_I2C",   "MACHXO3",   0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
}

var LeniTbl = []I2cInfo {
    //       name             comp         Bus    devAddr  page    HubName  HubPort  Flag 
    I2cInfo {"P12V_AUX",     "TPS53688",   0x2,   0x60,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"P12V",         "INA3221A",   0x2,   0x43,    0x1,    "HUB_NONE", 0,    0},
    I2cInfo {"CORE",         "TPS53688",   0x2,   0x60,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"ARM",          "TPS53688",   0x2,   0x60,    0x1,    "HUB_NONE", 0,    0},
    I2cInfo {"P3V3",         "INA3221A",   0x2,   0x43,    0x2,    "HUB_NONE", 0,    0},
    I2cInfo {"VDD_DDR",      "INA3221A",   0x2,   0x43,    0x3,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VDD",      "PMIC",       0x0,   0x4F,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VDDQ",     "PMIC",       0x0,   0x4F,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VPP",      "PMIC",       0x0,   0x4F,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"RTC",          "PCF85263A",  0x2,   0x51,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"PCIE_CLK_BUF", "RC19008",    0x2,   0x6C,    0x0,    "HUB_NONE", 0,    0}, // 100MHz clk
    I2cInfo {"MX_CLK_BUF",   "RC19004",    0x2,   0x6F,    0x0,    "HUB_NONE", 0,    0}, // 156MHz clk
    I2cInfo {"TSENSOR",      "TMP451",     0x2,   0x4C,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"FRU",          "AT24C02C",   0x3,   0x53,    0x0,    "HUB_NONE", 0,    FLAG_16BIT_EEPROM},
    I2cInfo {"DPU_FRU",      "AT24C02C",   0x2,   0x52,    0x0,    "HUB_NONE", 0,    FLAG_16BIT_EEPROM},
}

var LeniSensorTbl = []I2cSensorInfo {
    I2cSensorInfo {"P12V",          I2cSensorCoeff{ 0.02 }},
    I2cSensorInfo {"P3V3",          I2cSensorCoeff{ 0.001 }},
    I2cSensorInfo {"VDD_DDR",       I2cSensorCoeff{ 0.001 }},
}

var LinguaMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    //LINGUA HAS NO HOST SIDE PHYSICAL EEPROM.  0x50 IS THE DATA IN UFM2
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"CPLD_MCTP",      "CPLD",      0x0,   0x61,    0x0,    "HUB_NONE",  0,    0},  
    //READ/WRITE TO CPLD UMF2 FLASH. 
    I2cInfo {"CPLD_FRU",       "MACHXO3",   0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    //READ FROM THE I2C INTERFACE FOR the CPLD UMF2 EEPROM
    I2cInfo {"CPLD_FRU_I2C",   "MACHXO3",   0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"CPLD_ADAP",      "CPLD",      0x0,   0x4B,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU_ADAP",       "M24C32",    0x0,   0x57,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
}

var LinguaTbl = []I2cInfo {
    //       name             comp         Bus    devAddr  page    HubName  HubPort  Flag 
    I2cInfo {"QSFP",          "QSFP",      0x0,   0x50,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"DPU_FRU",       "AT24C02C",  0x2,   0x52,    0x0,    "HUB_NONE", 0,    FLAG_16BIT_EEPROM},
    I2cInfo {"TSENSOR",       "TMP451",    0x2,   0x4C,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"RTC",           "PCF85263A", 0x2,   0x51,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"CORE",          "TPS53688",  0x2,   0x60,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"ARM",           "TPS53688",  0x2,   0x60,    0x1,    "HUB_NONE", 0,    0},
    I2cInfo {"VDD_DDR",       "TPS549A20", 0x2,   0x1C,    0x0,    "HUB_NONE",  0,    0},    
    I2cInfo {"PCIE_CLK_BUF",  "RC19008",   0x2,   0x6C,    0x0,    "HUB_NONE", 0,    0}, // 100MHz clk
    I2cInfo {"MX_CLK_BUF",    "RC19004",   0x2,   0x6F,    0x0,    "HUB_NONE", 0,    0}, // 156MHz clk
    
    
}

var OrtanoMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CPLD_MCTP",      "CPLD",      0x0,   0x61,    0x0,    "HUB_NONE",  0,    0},  
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
}

var Ortano2MtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CPLD_MCTP",      "CPLD",      0x0,   0x61,    0x0,    "HUB_NONE",  0,    0},  
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x53,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
}

var LaconaTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"TSENSOR",        "TMP451",    0x0,   0x4C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SPD",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_8BIT_EEPROM},
    I2cInfo {"RTC",            "PCF85263A", 0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_CORE",      "TPS53659A", 0x0,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_ARM",       "TPS53659A", 0x0,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"VDDQ_DDR",       "TPS544B25", 0x0,   0x24,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"SFP_1",          "QSFP",      0x1,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"SFP_1_DOM",      "QSFP",      0x1,   0x51,    0x0,    "HUB_CPLD",  0,    0},

    I2cInfo {"SFP_2",          "QSFP",      0x2,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"SFP_2_DOM",      "QSFP",      0x2,   0x51,    0x0,    "HUB_CPLD",  0,    0},
}

var PomonteTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"TSENSOR",        "TMP451",    0x0,   0x4C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SPD",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_8BIT_EEPROM},
    I2cInfo {"RTC",            "PCF85263A", 0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_CORE",      "TPS53659A", 0x0,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_ARM",       "TPS53659A", 0x0,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"VDDQ_DDR",       "TPS544B25", 0x0,   0x24,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VDD_DDR",        "TPS549A20", 0x0,   0x1C,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_1",         "QSFP",      0x1,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"QSFP_1_DOM",     "QSFP",      0x1,   0x51,    0x0,    "HUB_CPLD",  0,    0},

    I2cInfo {"QSFP_2",         "QSFP",      0x2,   0x50,    0x0,    "HUB_CPLD",  0,    0},
    I2cInfo {"QSFP_2_DOM",     "QSFP",      0x2,   0x51,    0x0,    "HUB_CPLD",  0,    0},
}

var TaorElbaTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"VDD_DDR",        "TPS549A20", 0x0,   0x1C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VDDQ_DDR",       "TPS544B25", 0x0,   0x24,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR",        "TMP422",    0x0,   0x4C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"RTC",            "PCF85263A", 0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"DDR4_SPD0",      "DDR4_SPD",  0x0,   0x56,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"DDR4_SPD1",      "DDR4_SPD",  0x0,   0x51,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"ELB0_CORE",      "TPS53659A", 0x0,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_ARM",       "TPS53659A", 0x0,   0x62,    0x1,    "HUB_NONE",  0,    0},
}

var LipariElbaTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"VDD_DDR",        "MP8796",    0x0,   0x30,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VDDQ_DDR",       "MP8796",    0x0,   0x31,    0x0,    "HUB_NONE",  0,    0},
    //I2cInfo {"PWRMONITOR",        "INA231",    0x0,   0x40,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"ELB0_CORE",      "MP2975",    0x0,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_ARM",       "MP2975",    0x0,   0x62,    0x1,    "HUB_NONE",  0,    0},
}

var MtFujiElbaV1Tbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    0},   //Cisco uses 8-bit FRU 
    I2cInfo {"VDD_DDR",        "LTC3882",   0x0,   0x44,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VDDQ_DDR",       "LTC3882",   0x0,   0x44,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_CORE",      "LTC3882",   0x0,   0x55,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_CORE1",     "LTC3882",   0x0,   0x55,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_CORE2",     "LTC3882",   0x0,   0x66,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_ARM",       "LTC3882",   0x0,   0x66,    0x1,    "HUB_NONE",  0,    0},
}

var MtFujiElbaV2Tbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    0},   
    I2cInfo {"VDD_DDR",        "TPS53659",  0x0,   0x72,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VDDQ_DDR",       "TPS53659",  0x0,   0x72,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_CORE",      "TPS53659",  0x0,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"ELB0_ARM",       "TPS53659",  0x0,   0x62,    0x1,    "HUB_NONE",  0,    0},
}


var CapaciElbaTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"ELB0_CORE",      "TPS53689",  0x0,   0x4B,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"ELB0_ARM",       "TPS53689",  0x0,   0x4B,    0x1,    "HUB_NONE", 0,    0},
}

var DeschutesTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"CORE",           "TPS53689",  0x0,   0x60,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"ARM",            "TPS53689",  0x0,   0x60,    0x1,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VDD",        "PMIC",      0x0,   0x4F,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VDDQ",       "PMIC",      0x0,   0x4F,    0x1,    "HUB_NONE", 0,    0},
    I2cInfo {"DDR_VPP",        "PMIC",      0x0,   0x4F,    0x2,    "HUB_NONE", 0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE", 0,    0},   //Cisco uses 8-bit FRU
}

// Some devices on Deschutes are only accessible from one DPU due to space-saving design
var DeschutesTblDpu0 = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"VDD_DDR_DPU0",   "TPS53689",  0x0,   0x62,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"VDD_DDR_DPU1",   "TPS53689",  0x0,   0x62,    0x1,    "HUB_NONE", 0,    0},
}

var LaconaMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CPLD_MCTP",      "CPLD",      0x0,   0x60,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
}

var LaconaDellMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CPLD_MCTP",      "CPLD",      0x0,   0x60,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
}

// Naples100 I2C table on MTP SMBus
var Naples100HPEMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    0},
}

// Naples100 IBM I2C table on MTP SMBus
var Naples100IBMMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    0},
}

// Naples100 IBM I2C table on MTP SMBus
var Naples100DELLMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    0},
}

//=========================================
// forio I2C table on ARM
// devAddr is 7-bit address
var ForioTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName    HubPort Flag
    I2cInfo {"CAP0_CORE_DVDD", "TPS53659",  0x2,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CAP0_ARM",       "TPS53659",  0x2,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"CAP0_3V3",       "TPS549A20", 0x2,   0x1a,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CAP0_HBM",       "TPS549A20", 0x2,   0x1b,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CAP0_CORE_AVDD", "TPS549A20", 0x2,   0x1C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x2,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"RTC",            "PCF85263A", 0x2,   0x51,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR",        "TMP422",    0x2,   0x4C,    0x0,    "HUB_NONE",  0,    0}, 

    I2cInfo {"QSFP_1",         "QSFP",      0x0,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"QSFP_1_DOM",     "QSFP",      0x0,   0x51,    0x0,    "HUB_NONE",  0,    0},

    I2cInfo {"QSFP_2",         "QSFP",      0x1,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"QSFP_2_DOM",     "QSFP",      0x1,   0x51,    0x0,    "HUB_NONE",  0,    0},
}

// forio I2C table on MTP SMBus
var ForioMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x76,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"I2CSPI",         "CPLD-I2CSPI",0x0,  0x52,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    0},
}

// Vomero2 I2C table on MTP SMBus
var Vomero2MtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x76,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"I2CSPI",         "CPLD-I2CSPI",0x0,  0x52,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x53,    0x0,    "HUB_NONE",  0,    0},
}

// Naples25 I2C table on MTP SMBus
var Naples25SwmDellMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x52,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"FRU_ALOM",       "AT25320B",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"CPLD_ADAP",      "CPLD",      0x0,   0x4B,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU_ADAP",       "AT24C02C",  0x0,   0x57,    0x0,    "HUB_NONE",  0,    0},
}

//=========================================
// NaplesMtp PMBus table
// devAddr is 7-bit address
var NaplesMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName    HubPort  Flag
    I2cInfo {"CAP0_CORE_DVDD", "TPS53659",  0x0,   0x62,    0x0,    "NIC_HUB",    2,    0},
    I2cInfo {"CAP0_CORE_AVDD", "TPS53659",  0x0,   0x62,    0x1,    "NIC_HUB",    2,    0},
    I2cInfo {"CAP0_HBM",       "TPS549A20", 0x0,   0x1b,    0x0,    "NIC_HUB",    2,    0},
    I2cInfo {"CAP0_ARM",       "TPS549A20", 0x0,   0x1C,    0x0,    "NIC_HUB",    2,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "NIC_HUB",    2,    0},
    I2cInfo {"RTC",            "PCF85263A", 0x0,   0x51,    0x0,    "NIC_HUB",    2,    0},
    I2cInfo {"TSENSOR",        "TMP421",    0x0,   0x4C,    0x0,    "NIC_HUB",    2,    0},
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x76,    0x0,    "NIC_HUB",    2,    0},
    I2cInfo {"CPLD_ALT",       "CPLD",      0x0,   0x4A,    0x0,    "NIC_HUB",    2,    0},
    I2cInfo {"CPLD_ADAP",      "CPLD",      0x0,   0x4B,    0x0,    "NIC_HUB",    2,    0},

    I2cInfo {"QSFP_1_A0",      "QSFP",      0x0,   0x50,    0x0,    "NIC_HUB",    1,    0},
    I2cInfo {"QSFP_1_A2",      "QSFP",      0x0,   0x51,    0x0,    "NIC_HUB",    1,    0},

    I2cInfo {"QSFP_2_A0",      "QSFP",      0x0,   0x50,    0x0,    "NIC_HUB",    3,    0},
    I2cInfo {"QSFP_2_A2",      "QSFP",      0x0,   0x51,    0x0,    "NIC_HUB",    3,    0},

    I2cInfo {"NIC_HUB",        "TCA9546A",  0x0,   0x74,    0x0,    "HUB_NONE",   0,    0},
    I2cInfo {"PEX",            "PEX8716",   0x0,   0x38,    0x0,    "NIC_HUB",    0,    0},
}

//=========================================
// NIC power board PMBus table
// bus field is linux I2C device index at /dev/i2c-x
// devAddress is 7-bit address
var NicPowerVrmTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x8,   0x62,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VRM_CAPRI_AVDD", "TPS53659",  0x8,   0x62,    0x1,    "HUB_NONE",  0,    0},
    I2cInfo {"VRM_3V3",        "TPS549A20", 0x8,   0x1C,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"VRM_1V2",        "TPS549A20", 0x8,   0x1B,    0x0,    "HUB_NONE",  0,    0},
}

//=========================================
// MTP PMBus table
// bus field is linux I2C device index at /dev/i2c-x
// devAddress is 7-bit address
var MtpI2cTbl = []I2cInfo {
    //       name     comp         Bus  devAddr  channel HubName  HubPort  Flag
    I2cInfo {"PSU_1", "BEL_POWER", 0x0, 0x5B,    0x0,    "HUB_4",    0,    0},
    I2cInfo {"PSU_2", "BEL_POWER", 0x0, 0x5B,    0x0,    "HUB_4",    1,    0},
    I2cInfo {"FRU",   "AT24C02C",  0x0, 0x50,    0x0,    "HUB_4",    2,    0},
    I2cInfo {"FAN",   "ADT7462",   0x0, 0x5C,    0x0,    "HUB_4",    2,    0},
    I2cInfo {"DC_1",  "TPS549A20", 0x0, 0x1A,    0x0,    "HUB_4",    3,    0},
    I2cInfo {"DC_2",  "TPS549A20", 0x0, 0x1B,    0x0,    "HUB_4",    3,    0},
    I2cInfo {"CLKGEN","SI52144",   0x0, 0x6B,    0x0,    "HUB_4",    3,    0},
//    I2cInfo {"HUB_1", "TCA9546A",  0x0, 0x70,    0x0,    "HUB_NONE", 0,    0},
//    I2cInfo {"HUB_2", "TCA9546A",  0x0, 0x71,    0x0,    "HUB_NONE", 0,    0},
//    I2cInfo {"HUB_3", "TCA9546A",  0x0, 0x72,    0x0,    "HUB_NONE", 0,    0},
//    I2cInfo {"HUB_4", "TCA9546A",  0x0, 0x73,    0x0,    "HUB_NONE", 0,    0},
}

//=========================================
// MTP-S PMBus table
// bus field is linux I2C device index at /dev/i2c-x
// devAddress is 7-bit address
var MtpsI2cTbl = []I2cInfo {
    //       name        comp         Bus  devAddr  channel HubName  HubPort  Flag
    I2cInfo {"PSU_1",    "BEL_POWER", 0x0, 0x5B,    0x0,    "HUB_4",    0,    0},
    I2cInfo {"PSU_2",    "BEL_POWER", 0x0, 0x5B,    0x0,    "HUB_4",    1,    0},
    I2cInfo {"FRU",      "AT24C02C",  0x0, 0x50,    0x0,    "HUB_4",    2,    0},
    I2cInfo {"FAN",      "ADT7462",   0x0, 0x5C,    0x0,    "HUB_4",    2,    0},
    I2cInfo {"CLKGEN",   "SI52144",   0x0, 0x6B,    0x0,    "HUB_4",    3,    0},
    I2cInfo {"659_DVDD", "TPS53659",  0x0, 0x62,    0x0,    "HUB_4",    3,    0},
    I2cInfo {"659_AVDD", "TPS53659",  0x0, 0x62,    0x1,    "HUB_4",    3,    0},
    I2cInfo {"A20_U17",  "TPS549A20", 0x0, 0x1A,    0x0,    "HUB_4",    3,    0},
    I2cInfo {"A20_U18",  "TPS549A20", 0x0, 0x1B,    0x0,    "HUB_4",    3,    0},
    I2cInfo {"A20_U40",  "TPS549A20", 0x0, 0x1F,    0x0,    "HUB_4",    3,    0},
    I2cInfo {"A20_U53",  "TPS549A20", 0x0, 0x1C,    0x0,    "HUB_4",    3,    0},

    I2cInfo {"HUB_5",    "TCA9546A",  0x0, 0x74,    0x0,    "HUB_NONE", 0,    0},
    I2cInfo {"PEX_U21",  "PEX8716",   0x0, 0x38,    0x0,    "HUB_5",    0,    0},
    I2cInfo {"PEX_U22",  "PEX8716",   0x0, 0x5D,    0x0,    "HUB_5",    1,    0},
    I2cInfo {"PEX_U23",  "PEX8716",   0x0, 0x5D,    0x0,    "HUB_5",    2,    0},
}

var MtpHubI2cTbl = []I2cInfo {
    I2cInfo {"HUB_1", "TCA9546A",  0x0, 0x70,    0x0,    "HUB_NONE",  0,  0},
    I2cInfo {"HUB_2", "TCA9546A",  0x0, 0x71,    0x0,    "HUB_NONE",  0,  0},
    I2cInfo {"HUB_3", "TCA9546A",  0x0, 0x72,    0x0,    "HUB_NONE",  0,  0},
    I2cInfo {"HUB_4", "TCA9546A",  0x0, 0x73,    0x0,    "HUB_NONE",  0,  0},
}

var TaorTbl = []I2cInfo {
    //       name              comp          Bus   devAddr  page    HubName   HubPort  Flag
    I2cInfo {"P0V8AVDD_GB_A",  "TPS549A20",   1,   0x1C,    0x0,    "FPGA_HUB_0_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"P0V8AVDD_GB_B",  "TPS549A20",   1,   0x1b,    0x0,    "FPGA_HUB_0_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"P0V8RT_B",       "TPS549A20",   1,   0x1e,    0x0,    "FPGA_HUB_0_0",  0,    I2C_TEST_ENABLE},
    //ON P0 BOARDS, 0x4C TEMP SENSOR IS LOCATED HERE AT 0x48
    //I2cInfo {"TSENSOR-1",      "LM75",        3,   0x48,    0x0,    "FPGA_HUB_2_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"TSENSOR-1",      "TMP451",      3,   0x4C,    0x0,    "FPGA_HUB_2_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"TSENSOR-2",      "LM75",        3,   0x49,    0x0,    "FPGA_HUB_2_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"TSENSOR-3",      "LM75",        3,   0x4A,    0x0,    "FPGA_HUB_2_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"P0V8RT_A",       "TPS544C20",   1,   0x04,    0x0,    "FPGA_HUB_0_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"P3V3",           "TPS544C20",   1,   0x08,    0x0,    "FPGA_HUB_0_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"P3V3S",          "TPS544C20",   1,   0x09,    0x0,    "FPGA_HUB_0_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"TDNT_PDVDD",     "TPS53681",    1,   0x60,    0x0,    "FPGA_HUB_0_3",  3,    I2C_TEST_ENABLE},
    I2cInfo {"TDNT_P0V8_AVDD", "TPS53681",    1,   0x60,    0x1,    "FPGA_HUB_0_3",  3,    I2C_TEST_ENABLE},
    I2cInfo {"CPU_P1V2_VDDQ",     "SN1701022", 1,  0x77,    0x0,    "FPGA_HUB_0_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"CPU_P1V05_COMBINED","SN1701022", 1,  0x77,    0x1,    "FPGA_HUB_0_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"CPU_PVCCIN",        "SN1701022", 1,  0x6B,    0x0,    "FPGA_HUB_0_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"CPU_P1V05_VCCSCSUS","SN1701022", 1,  0x6B,    0x1,    "FPGA_HUB_0_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"PSU_1",           "DPS-800",    2,   0x58,    0x0,    "FPGA_HUB_1_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"PSU_2",           "DPS-800",    2,   0x58,    0x0,    "FPGA_HUB_1_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"FAN_1",           "ADT7462",    2,   0x58,    0x0,    "FPGA_HUB_1_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"FAN_2",           "ADT7462",    2,   0x5C,    0x0,    "FPGA_HUB_1_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"TD3",             "TRIDENT3",   2,   0x44,    0x0,    "FPGA_HUB_1_3",  3,    0},
    I2cInfo {"FRU_EE",          "AT24C02C",   3,   0x50,    0x0,    "FPGA_HUB_2_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"FRU_CERT",        "AT24C02C",   3,   0x51,    0x0,    "FPGA_HUB_2_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA0",      "MACHXO3",    3,   0x4A,    0x0,    "FPGA_HUB_2_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA1",      "MACHXO3",    3,   0x4A,    0x0,    "FPGA_HUB_2_3",  3,    I2C_TEST_ENABLE},
    //THESE DEVICES DONT HAVE I2C, BUT DUE TO HOW HWINFO AND DEVMGR WORKS, THEY NEED ENTRIES IN THIS TABLE
    I2cInfo {"TSENSOR-CPU",      "XeonD",     2,   0x44,    0x0,    "FPGA_HUB_1_0",  0,    0},
    I2cInfo {"TSENSOR-GB",       "Gearbox",   2,   0x44,    0x0,    "FPGA_HUB_1_0",  0,    0},
    I2cInfo {"TSENSOR-RETIMER",  "Retimer",   2,   0x44,    0x0,    "FPGA_HUB_1_0",  0,    0},
    I2cInfo {"TSENSOR-TD3",      "TD3",       2,   0x44,    0x0,    "FPGA_HUB_1_0",  0,    0},
    I2cInfo {"TSENSOR-ASIC0",    "ELBA0",     2,   0x44,    0x0,    "FPGA_HUB_1_0",  0,    0},
    I2cInfo {"TSENSOR-ASIC1",    "ELBA1",     2,   0x44,    0x0,    "FPGA_HUB_1_0",  0,    0},
    //END NON EXISTENT I2C DEVICES
    I2cInfo {"SFP_1",          "SFP",       0x4,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_2",          "SFP",       0x4,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_3",          "SFP",       0x4,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_4",          "SFP",       0x4,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_5",          "SFP",       0x5,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_6",          "SFP",       0x5,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_7",          "SFP",       0x5,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_8",          "SFP",       0x5,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_9",          "SFP",       0x6,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_10",         "SFP",       0x6,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_11",         "SFP",       0x6,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_12",         "SFP",       0x6,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_13",         "SFP",       0x7,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_14",         "SFP",       0x7,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_15",         "SFP",       0x7,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_16",         "SFP",       0x7,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_17",         "SFP",       0x8,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_18",         "SFP",       0x8,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_19",         "SFP",       0x8,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_20",         "SFP",       0x8,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_21",         "SFP",       0x9,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_22",         "SFP",       0x9,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_23",         "SFP",       0x9,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_24",         "SFP",       0x9,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_25",         "SFP",       0xA,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_26",         "SFP",       0xA,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_27",         "SFP",       0xA,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_28",         "SFP",       0xA,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_29",         "SFP",       0xB,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_30",         "SFP",       0xB,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_31",         "SFP",       0xB,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_32",         "SFP",       0xB,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_33",         "SFP",       0xC,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_34",         "SFP",       0xC,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_35",         "SFP",       0xC,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_36",         "SFP",       0xC,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_37",         "SFP",       0xD,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_38",         "SFP",       0xD,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_39",         "SFP",       0xD,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_40",         "SFP",       0xD,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_41",         "SFP",       0xE,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_42",         "SFP",       0xE,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_43",         "SFP",       0xE,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_44",         "SFP",       0xE,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"SFP_45",         "SFP",       0xF,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"SFP_46",         "SFP",       0xF,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"SFP_47",         "SFP",       0xF,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"SFP_48",         "SFP",       0xF,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"QSFP_1",         "QSFP",       0x10,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"QSFP_2",         "QSFP",       0x10,   0x50,    0x0,    "HUB_NONE",  1,    0},
    I2cInfo {"QSFP_3",         "QSFP",       0x10,   0x50,    0x0,    "HUB_NONE",  2,    0},
    I2cInfo {"QSFP_4",         "QSFP",       0x10,   0x50,    0x0,    "HUB_NONE",  3,    0},
    I2cInfo {"QSFP_5",         "QSFP",       0x11,   0x50,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"QSFP_6",         "QSFP",       0x11,   0x50,    0x0,    "HUB_NONE",  1,    0},
}


var LipariTbl = []I2cInfo {
    //       name              comp          Bus   devAddr  page    HubName       HubPort  Flag
    //
    //FPGA-0 DEVICES
    /*
    I2cInfo {"PSU_1_FRU",      "DPS-2100",    0,   0x50,    0x0,    "0_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"PSU_1",          "DPS-2100",    0,   0x58,    0x0,    "0_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"PSU_2_FRU",      "DPS-2100",    0,   0x50,    0x0,    "0_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"PSU_2",          "DPS-2100",    0,   0x58,    0x0,    "0_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"TEMP-CPU-FRNT",  "LM75",        0,   0x48,    0x0,    "0_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"TEMP-CPU-REAR",  "LM75",        0,   0x49,    0x0,    "0_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"TEMP-CPU-CNTR",  "LM75",        0,   0x4A,    0x0,    "0_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"FRU",            "AT24C04C",    0,   0x50,    0x0,    "0_3",  3,    I2C_TEST_ENABLE},
    I2cInfo {"FRU_CERT",       "AT24C04C",    0,   0x51,    0x0,    "0_3",  3,    I2C_TEST_ENABLE},

    I2cInfo {"FAN_1",          "ADT7462",     1,   0x5C,    0x0,    "1_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"FAN_2",          "ADT7462",     1,   0x61,    0x0,    "1_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"CPU_VDDCR",      "ISL69247",    1,   0x60,    0x0,    "1_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"SOC_VDDCR",      "ISL69247",    1,   0x60,    0x1,    "1_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"MEM_VDDIO",      "TPS53688",    1,   0x5E,    0x0,    "1_1",  1,    I2C_TEST_ENABLE},   //cannot ping
    I2cInfo {"P12V",           "TPS25990",    1,   0x41,    0x0,    "1_1",  1,    I2C_TEST_ENABLE},   //hot swap contorller
    I2cInfo {"FRU_SWITCH",     "AT24C04C",    1,   0x50,    0x0,    "1_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"FRU_SWITCH2",    "AT24C04C",    1,   0x51,    0x0,    "1_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"TEMP-FRNT",      "TMP451",      1,   0x4C,    0x0,    "1_3",  3,    I2C_TEST_ENABLE},
    I2cInfo {"P3V3S1",         "TPS53688",    1,   0x6C,    0x0,    "1_3",  3,    I2C_TEST_ENABLE},   //cannot ping

    I2cInfo {"TH4_PDVDD",      "TPS536C7",    2,   0x69,    0x0,    "2_0",  0,    I2C_TEST_ENABLE},   //cannot ping
    I2cInfo {"TH4_P0V75_AVDD", "TPS536C7",    2,   0x69,    0x1,    "2_0",  0,    I2C_TEST_ENABLE},   //cannot ping

    I2cInfo {"TEMP-CNTR",      "LM75",        2,   0x49,    0x0,    "2_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"TEMP-REAR",      "LM75",        2,   0x4A,    0x0,    "2_1",  1,    I2C_TEST_ENABLE},

    I2cInfo {"TH4CLK",         "RC21012A",    2,   0x09,    0x0,    "2_2",  2,    I2C_TEST_ENABLE},   
    I2cInfo {"P3V3"  ,         "MP8796",      2,   0x31,    0x0,    "2_2",  2,    I2C_TEST_ENABLE},   
    I2cInfo {"P3V3S2",         "TPS53688",    2,   0x69,    0x0,    "2_2",  2,    I2C_TEST_ENABLE},   //cannot ping
    */
    I2cInfo {"PSU_1_FRU",      "DPS-2100",    4,   0x50,    0x0,    "0_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"PSU_1",          "DPS-2100",    4,   0x58,    0x0,    "0_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"PSU_2_FRU",      "DPS-2100",    5,   0x50,    0x0,    "0_1",  0,    I2C_TEST_ENABLE},
    I2cInfo {"PSU_2",          "DPS-2100",    5,   0x58,    0x0,    "0_1",  0,    I2C_TEST_ENABLE},
    I2cInfo {"CPU-FRNT-LM75",  "LM75",        6,   0x48,    0x0,    "0_2",  0,    I2C_TEST_ENABLE},
    I2cInfo {"CPU-REAR-LM75",  "LM75",        6,   0x49,    0x0,    "0_2",  0,    I2C_TEST_ENABLE},
    I2cInfo {"CPU-CNTR-LM75",  "LM75",        6,   0x4A,    0x0,    "0_2",  0,    I2C_TEST_ENABLE},
    I2cInfo {"FRU",            "AT24C04C",    7,   0x50,    0x0,    "0_3",  0,    I2C_TEST_ENABLE},
    I2cInfo {"FRU_CPUBRD",     "AT24C04C",    7,   0x50,    0x0,    "0_3",  0,    I2C_TEST_ENABLE},
    I2cInfo {"FRU_CERT",       "AT24C04C",    7,   0x51,    0x0,    "0_3",  0,    I2C_TEST_ENABLE},
    //I2cInfo {"FRU_CPU",        "AT24C04",     0,   0x50,    0x0,    "HUB_NONE", 0, I2C_TEST_ENABLE},
    //I2cInfo {"FRU_SWITCH",     "AT24C256C",   1,   0x50,    0x0,    "HUB_NONE", 0, I2C_TEST_ENABLE},

    I2cInfo {"FAN_1",          "ADT7462",     9,   0x5C,    0x0,    "1_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"FAN_2",          "ADT7462",     9,   0x61,    0x0,    "1_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"CPU_VDDCR",      "ISL69247",    10,   0x60,    0x0,    "1_1",  0,    I2C_TEST_ENABLE},
    I2cInfo {"SOC_VDDCR",      "ISL69247",    10,   0x60,    0x1,    "1_1",  0,    I2C_TEST_ENABLE},
    I2cInfo {"MEM_VDDIO",      "TPS53688",    10,   0x5E,    0x0,    "1_1",  0,    I2C_TEST_ENABLE},   //cannot ping
    I2cInfo {"P12V",           "TPS25990",    10,   0x41,    0x0,    "1_1",  0,    I2C_TEST_ENABLE},   //hot swap contorller
    I2cInfo {"FRU_SWITCH",     "AT24C04C",    11,   0x50,    0x0,    "1_2",  0,    I2C_TEST_ENABLE},
    I2cInfo {"FRU_SWITCH2",    "AT24C04C",    11,   0x51,    0x0,    "1_2",  0,    I2C_TEST_ENABLE},
    I2cInfo {"TEMP-FRNT",      "TMP451",      12,   0x4C,    0x0,    "1_3",  0,    I2C_TEST_ENABLE},
    I2cInfo {"P3V3S1",         "TPS53688",    12,   0x6C,    0x0,    "1_3",  0,    I2C_TEST_ENABLE},   //cannot ping

    I2cInfo {"TH4_PDVDD",      "TPS536C7",    14,   0x69,    0x0,    "2_0",  0,    I2C_TEST_ENABLE},   //cannot ping
    I2cInfo {"TH4_P0V75_AVDD", "TPS536C7",    14,   0x69,    0x1,    "2_0",  0,    I2C_TEST_ENABLE},   //cannot ping

    I2cInfo {"CNTR-LM75",      "LM75",        15,   0x49,    0x0,    "2_1",  0,    I2C_TEST_ENABLE},
    I2cInfo {"REAR-LM75",      "LM75",        15,   0x4A,    0x0,    "2_1",  0,    I2C_TEST_ENABLE},

    I2cInfo {"TH4CLK",         "RC21012A",    16,   0x09,    0x0,    "2_2",  0,    I2C_TEST_ENABLE},   
    I2cInfo {"P3V3"  ,         "MP8796",      16,   0x31,    0x0,    "2_2",  0,    I2C_TEST_ENABLE},   
    I2cInfo {"P3V3S2",         "TPS53688",    16,   0x69,    0x0,    "2_2",  0,    I2C_TEST_ENABLE},   //cannot ping

    //FPGA-1 DEVICES
    I2cInfo {"CPLD_ELBA0",      "MACHXO3",    0,   0x4A,    0x0,    "FPGA1_HUB_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA1",      "MACHXO3",    0,   0x4A,    0x0,    "FPGA1_HUB_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA2",      "MACHXO3",    0,   0x4A,    0x0,    "FPGA1_HUB_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA3",      "MACHXO3",    0,   0x4A,    0x0,    "FPGA1_HUB_3",  3,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA4",      "MACHXO3",    1,   0x4A,    0x0,    "FPGA1_HUB_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA5",      "MACHXO3",    1,   0x4A,    0x0,    "FPGA1_HUB_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA6",      "MACHXO3",    1,   0x4A,    0x0,    "FPGA1_HUB_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"CPLD_ELBA7",      "MACHXO3",    1,   0x4A,    0x0,    "FPGA1_HUB_3",  3,    I2C_TEST_ENABLE},

    I2cInfo {"ELBA0_TEMP",      "TMP451",     54,   0x4C,    0x0,    "FPGA1_HUB_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"ELBA1_TEMP",      "TMP451",     55,   0x4C,    0x0,    "FPGA1_HUB_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"ELBA2_TEMP",      "TMP451",     56,   0x4C,    0x0,    "FPGA1_HUB_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"ELBA3_TEMP",      "TMP451",     57,   0x4C,    0x0,    "FPGA1_HUB_3",  3,    I2C_TEST_ENABLE},
    I2cInfo {"ELBA4_TEMP",      "TMP451",     59,   0x4C,    0x0,    "FPGA1_HUB_0",  0,    I2C_TEST_ENABLE},
    I2cInfo {"ELBA5_TEMP",      "TMP451",     60,   0x4C,    0x0,    "FPGA1_HUB_1",  1,    I2C_TEST_ENABLE},
    I2cInfo {"ELBA6_TEMP",      "TMP451",     61,   0x4C,    0x0,    "FPGA1_HUB_2",  2,    I2C_TEST_ENABLE},
    I2cInfo {"ELBA7_TEMP",      "TMP451",     62,   0x4C,    0x0,    "FPGA1_HUB_3",  3,    I2C_TEST_ENABLE},
    //THESE DEVICES DONT HAVE I2C, BUT DUE TO HOW HWINFO AND DEVMGR WORKS, THEY NEED ENTRIES IN THIS TABLE
    I2cInfo {"FAN",             "FPGA",       2,    0x44,    0x0,    "NONE",         0,    0},
}

var MateraNicI2cBus = map[string]uint32 {
    "UUT_1": 3,
    "UUT_2": 4,
    "UUT_3": 5,
    "UUT_4": 6,
    "UUT_5": 7,
    "UUT_6": 8,
    "UUT_7": 9,
    "UUT_8": 10,
    "UUT_9": 11,
    "UUT_10": 12,
}


var MateraI2cTbl = []I2cInfo {
    //       name            comp         Bus  devAddr  page  HubName     HubPort  Flag
    I2cInfo {"FRU",          "AT24C04C",  20,  0x50,    0x0,  "HUB_NONE",  0,    0},   //MB FRU
    I2cInfo {"IOBL",         "AT24C04C",  18,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"IOBR",         "AT24C04C",  17,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"FPIC",         "AT24C04C",  19,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"CLK_BUF",      "RC19013",   20,  0x6C,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR_MB",   "LM75",      20,  0x48,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR_IOBL", "LM75",      18,  0x48,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR_IOBR", "LM75",      17,  0x48,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"EXPDER_IOBL",  "MCP23008",  18,  0x20,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"EXPDER_IOBR",  "MCP23008",  17,  0x20,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"MEM_VDDIO",    "TPS53688",  16,  0x5E,    0x0,  "HUB_NONE",  0,    0},   //cannot ping
    I2cInfo {"P12V",         "TPS25990",  16,  0x41,    0x0,  "HUB_NONE",  0,    0},   //hot swap contorller
    I2cInfo {"CPU_VDDCR",    "ISL69247",  16,  0x60,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_1_FRU",    "DPS-2100",  14,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_1",        "DPS-2100",  14,  0x58,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_2_FRU",    "DPS-2100",  15,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_2",        "DPS-2100",  15,  0x58,    0x0,  "HUB_NONE",  0,    0},
    //THESE DEVICES DONT HAVE I2C, BUT DUE TO HOW HWINFO AND DEVMGR WORKS, THEY NEED ENTRIES IN THIS TABLE
    I2cInfo {"FAN",       "FPGA",      0, 0xff,    0x0,  "HUB_NONE",  0,    0},
}

var PanareaI2cTbl = []I2cInfo {
    //       name            comp         Bus  devAddr  page  HubName     HubPort  Flag
    I2cInfo {"FRU",          "AT24C04C",  20,  0x50,    0x0,  "HUB_NONE",  0,    0},   //MB FRU
    I2cInfo {"IOBL",         "AT24C04C",  18,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"IOBR",         "AT24C04C",  17,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"FPIC",         "AT24C04C",  19,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"CLK_SYN_FC3_L","RC22308",   18,  0x9,     0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"CLK_SYN_FC3_R","RC22308",   17,  0x9,     0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"CLK_SYN_VC8_L","RC31305",   18,  0x58,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"CLK_SYN_VC8_R","RC31305",   17,  0x58,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR_MB",   "LM75",      20,  0x48,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR_IOBL", "LM75",      18,  0x48,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR_IOBR", "LM75",      17,  0x48,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"MEM_VDDIO",    "TPS53688",  16,  0x5E,    0x0,  "HUB_NONE",  0,    0},   //cannot ping
    I2cInfo {"P12V",         "TPS25990",  16,  0x41,    0x0,  "HUB_NONE",  0,    0},   //hot swap contorller
    I2cInfo {"CPU_VDDCR",    "ISL69247",  16,  0x60,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_1_FRU",    "DPS-2100",  14,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_1",        "DPS-2100",  14,  0x58,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_2_FRU",    "DPS-2100",  15,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_2",        "DPS-2100",  15,  0x58,    0x0,  "HUB_NONE",  0,    0},
    //THESE DEVICES DONT HAVE I2C, BUT DUE TO HOW HWINFO AND DEVMGR WORKS, THEY NEED ENTRIES IN THIS TABLE
    I2cInfo {"FAN",       "FPGA",      0, 0xff,    0x0,  "HUB_NONE",  0,    0},
}

var PonzaI2cTbl = []I2cInfo {
    //       name            comp         Bus  devAddr  page  HubName     HubPort  Flag
    I2cInfo {"DELTA_VR",     "U50SS",     21,  0x10,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR_MB",   "LM75",      20,  0x48,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"FRU",          "AT24C04C",  20,  0x50,    0x0,  "HUB_NONE",  0,    0},   //MB FRU
    I2cInfo {"FPIC",         "AT24C04C",  19,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"CLK_SYN_FC3_L","RC22308",   18,  0x9,     0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"TSENSOR_IOBL", "LM75",      18,  0x48,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"IOBL",         "AT24C04C",  18,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"CLK_SYN_VC8_L","RC31305",   18,  0x58,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"P12V",         "TPS25990",  16,  0x41,    0x0,  "HUB_NONE",  0,    0},   //hot swap contorller
    I2cInfo {"MEM_VDDIO",    "TPS53688",  16,  0x5E,    0x0,  "HUB_NONE",  0,    0},   //cannot ping
    I2cInfo {"CPU_VDDCR",    "ISL69247",  16,  0x60,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_1_FRU",    "DPS-2100",  14,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_1",        "DPS-2100",  14,  0x58,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_2_FRU",    "DPS-2100",  15,  0x50,    0x0,  "HUB_NONE",  0,    0},
    I2cInfo {"PSU_2",        "DPS-2100",  15,  0x58,    0x0,  "HUB_NONE",  0,    0},
    //THESE DEVICES DONT HAVE I2C, BUT DUE TO HOW HWINFO AND DEVMGR WORKS, THEY NEED ENTRIES IN THIS TABLE
    I2cInfo {"FAN",       "FPGA",      0, 0xff,    0x0,  "HUB_NONE",  0,    0},
}

var GelsopMtpTbl = []I2cInfo {
    //       name               comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x3,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"SUCFRU",         "AT24C02C",  0x3,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"FILE",           "FILE",      0x3,   0xFF,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},   //use to write fru output to a bin file
}

var MontaroMtpTbl = []I2cInfo {
    //       name               comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x3,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"SUCFRU",         "AT24C02C",  0x3,   0x7C,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"FILE",           "FILE",      0x3,   0xFF,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},   //use to write fru output to a bin file
}

var SaracenoMtpTbl = []I2cInfo {
    //       name               comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x3,   0x53,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"SUCFRU",         "AT24C02C",  0x3,   0x7C,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"FILE",           "FILE",      0x3,   0xFF,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},   //use to write fru output to a bin file
}

var VulseiMtpTbl = []I2cInfo {
    //       name               comp         Bus    devAddr  page    HubName   HubPort  Flag
    I2cInfo {"FRU",            "AT24C02C",  0x3,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"SUCFRU",         "AT24C02C",  0x3,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"FILE",           "FILE",      0x3,   0xFF,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},   //use to write fru output to a bin file
}

// simulate UUT on Lipari using its 8 Elba CPLD
var MateraHubI2cTbl = []I2cInfo {
}

var PanareaHubI2cTbl = []I2cInfo {
}

func init() {
    CardType = os.Getenv("CARD_TYPE")

    MtpI2cTbl    = append(MtpI2cTbl,    MtpHubI2cTbl...)
    MtpsI2cTbl   = append(MtpsI2cTbl,   MtpHubI2cTbl...)
    MateraI2cTbl = append(MateraI2cTbl, MateraHubI2cTbl...)
    PanareaI2cTbl = append(PanareaI2cTbl, PanareaHubI2cTbl...)
    PonzaI2cTbl = append(PonzaI2cTbl, PanareaHubI2cTbl...)
    NaplesMtpTbl = append(NaplesMtpTbl, MtpHubI2cTbl...)
    Naples100MtpTbl = append(Naples100MtpTbl, MtpHubI2cTbl...)
    Naples100HPEMtpTbl = append(Naples100HPEMtpTbl, MtpHubI2cTbl...)
    Naples100IBMMtpTbl = append(Naples100IBMMtpTbl, MtpHubI2cTbl...)
    Naples100DELLMtpTbl = append(Naples100DELLMtpTbl, MtpHubI2cTbl...)
    Naples25MtpTbl  = append(Naples25MtpTbl, MtpHubI2cTbl...)
    ForioMtpTbl     = append(ForioMtpTbl, MtpHubI2cTbl...)
    BiodonaMtpTbl     = append(BiodonaMtpTbl, MtpHubI2cTbl...)
    OrtanoMtpTbl = append(OrtanoMtpTbl, MtpHubI2cTbl...)
    Ortano2MtpTbl = append(Ortano2MtpTbl, MtpHubI2cTbl...)
    LaconaMtpTbl = append(LaconaMtpTbl, MtpHubI2cTbl...)
    LaconaDellMtpTbl = append(LaconaDellMtpTbl, MtpHubI2cTbl...)
    GinestraMtpTbl = append(GinestraMtpTbl, MtpHubI2cTbl...)
    if CardType == "NAPLES100" ||
       CardType == "NAPLES100HPE" ||
       CardType == "NAPLES100IBM" ||
       CardType == "NAPLES100DELL" {
        I2cTbl = Naples100Tbl
    } else if CardType == "NAPLES25" || CardType == "NAPLES25WFG" {
        I2cTbl = Naples25Tbl
    } else if CardType == "NAPLES25OCP" {
        I2cTbl = Naples25Tbl
    } else if CardType == "NAPLES25SWM" {
        I2cTbl = Naples25Tbl
    } else if CardType == "NAPLES25SWMDELL" {
        I2cTbl = Naples25Tbl
    } else if CardType == "NAPLES25SWM833" {
        I2cTbl = Naples25Tbl
    } else if CardType == "FORIO" {
        I2cTbl = ForioTbl
    } else if CardType == "VOMERO" {
        I2cTbl = ForioTbl
    } else if CardType == "VOMERO2" {
        I2cTbl = ForioTbl
    } else if CardType == "BIODONA_D4" || CardType == "BIODONA_D5" {
        I2cTbl = BiodonaTbl
    } else if CardType == "ORTANO" {
        I2cTbl = OrtanoTbl
    } else if CardType == "ORTANO2" {
        I2cTbl = OrtanoTbl
    } else if CardType == "ORTANO2A" {
        I2cTbl = OrtanoADITbl
    } else if CardType == "ORTANO2AC" {
        I2cTbl = OrtanoADITbl
    } else if CardType == "ORTANO2I" {
        itpType = os.Getenv("ITP_TYPE")

        fmt.Sscanf(itpType, "0x%x", &itpIdx)
        tmpIdx := (itpIdx & 0xc0 )  >> 6
        podIdx := (itpIdx & 0x07 )

        I2cTbl = OrtanoIBASETbl
        I2cTbl = append(I2cTbl, OrtanoIPODTbl[podIdx]...)
        I2cTbl = append(I2cTbl, OrtanoITMPTbl[tmpIdx]...)
    } else if CardType == "ORTANO2S" {
        itpType = os.Getenv("ITP_TYPE")

        fmt.Sscanf(itpType, "0x%x", &itpIdx)
        tmpIdx := (itpIdx & 0x04 )  >> 2

        I2cTbl = Ortano2SBASETbl
        I2cTbl = append(I2cTbl, Ortano2STMPTbl[tmpIdx]...)
    } else if CardType == "LACONADELL"      ||
              CardType == "LACONA"          ||
              CardType == "LACONA32DELL"    ||
              CardType == "LACONA32"        {
        I2cTbl = LaconaTbl
    } else if CardType == "POMONTEDELL"     ||
              CardType == "POMONTE"         {
        I2cTbl = PomonteTbl
    } else if CardType == "GINESTRA_D4" {
        I2cTbl = GinestraD4Tbl
    } else if CardType == "GINESTRA_D5" {
        I2cTbl = GinestraD5Tbl
    } else if CardType == "MALFA" {
        I2cTbl = MalfaTbl
        SensorTbl = MalfaSensorTbl
    } else if CardType == "POLLARA" {
        I2cTbl = PollaraTbl
    } else if CardType == "LINGUA" {
        I2cTbl = LinguaTbl
    } else if CardType == "LENI" || CardType == "LENI48G"{
        I2cTbl = LeniTbl
        SensorTbl = LeniSensorTbl
    } else if CardType == "NIC_POWER" {
        I2cTbl = NicPowerVrmTbl
    } else if CardType == "MTP" {
        I2cTbl = MtpI2cTbl
    } else if CardType == "MTPS" {
        I2cTbl = MtpsI2cTbl
    } else if CardType == "MTP_MATERA" { 
        I2cTbl = MateraI2cTbl
    } else if CardType == "MTP_PANAREA" {
        I2cTbl = PanareaI2cTbl
    } else if CardType == "MTP_PONZA" {
        I2cTbl = PonzaI2cTbl
    } else if CardType == "TAORMINA" {
        I2cTbl = TaorTbl
    } else if CardType == "TAORELBA" {
        I2cTbl = TaorElbaTbl
    } else if CardType == "LIPARI" {
        I2cTbl = LipariTbl
    } else if CardType == "LIPARIELBA" {
        I2cTbl = LipariElbaTbl
    } else if CardType == "MTFUJI" {
        I2cTbl = MtFujiElbaV2Tbl
        if runtime.GOARCH == "arm64" {
            reg, err := ArmReadCPLDreg(0x0A)
            if err != errType.SUCCESS {
                fmt.Printf("ERROR reading MTFUJI REVISION\n")
            }
            reg = ((reg >> 4) & 0xF)
            if reg == 0x00 {
                I2cTbl = MtFujiElbaV1Tbl
            }
        }
    } else if CardType == "CAPACI" {
        I2cTbl = CapaciElbaTbl
    } else if CardType == "DESCHUTES" {
        I2cTbl = DeschutesTbl
        dpuSlot := os.Getenv("DPU_SLOT")
        if dpuSlot == "0" {
            I2cTbl = append(I2cTbl, DeschutesTblDpu0...)
        }
    } else {
        cli.Println("f", "Unsupported card:", CardType)
        return
    }
    CurI2cTbl = I2cTbl
    CurSensorTbl = SensorTbl
}

/** 
 *  
 * Mtfuji put their board rev in CPLD Register 0x0A 
 * Need to read it when running on the ARM side to determine 
 * which i2c table to load. They changed their voltage regulator 
 * on the Rev 02 Mtfuji 
 *  
 */
func ArmReadCPLDreg(register uint32) (data32 uint32, err int) {
    var readReg uint64
    cmdStr := fmt.Sprintf("cpldapp -r 0x%x", register)
    output , errGo := exec.Command("sh", "-c", cmdStr).Output()
    if errGo != nil {
        cli.Println("e", "executing command", cmdStr," returned error ->", errGo)
        err = errType.FAIL
        return
    }
    tmp := strings.TrimSuffix(string(output), "\n")
    readReg, errGo = strconv.ParseUint(tmp, 0, 64)
    if errGo != nil {
        cli.Println("e", "Error ArmReadCPLDreg parsing cpld read data failed ->", errGo)
        err = errType.FAIL
        return
    }
    data32 = uint32(readReg)
    return
}


/**
 * Find UUT type based on environment variable
 * TODO: This functionality can be implemented through redis
 */
func FindUutTypeMtp(uutName string) (uutType string, err int) {
    // This function is only useful on MTP
    cardType, found := os.LookupEnv("CARD_TYPE")
    if found == false {
        cli.Println("e", "Cannot find CARD_TYPE")
        err = errType.INVALID_PARAM
        return
    }

    if (cardType != "MTP" && cardType != "MTPS" && cardType != "MTP_MATERA" && cardType != "MTP_PANAREA" && cardType != "MTP_PONZA") {
        return "UUT_NONE", errType.SUCCESS
    }

    if uutName == "UUT_NONE" {
        return "UUT_NONE", errType.SUCCESS
    }
    uutType, found = os.LookupEnv(uutName)
    if found == false {
        cli.Println("e", "Cannot find uutType with uutName", uutName)
        err = errType.INVALID_PARAM
    }
    return
}

/**
 * Find UUT type based on environment variable
 * Can be used on both MTP and NIC Linux
 */
func FindUutType(uutName string) (uutType string, err int) {
    uutType = "TYPE_NONE"
    var found bool

    if uutName == "UUT_NONE" {
        uutType, found = os.LookupEnv("CARD_TYPE")
        if found == false {
            cli.Println("e", "Cannot find CARD_TYPE")
            err = errType.INVALID_PARAM
        }
    } else {
        uutType, found = os.LookupEnv(uutName)
        if found == false {
            cli.Println("e", "Cannot find uutType with uutName", uutName)
            err = errType.INVALID_PARAM
        }
    }
    return
}

/** 
 * MTP_Matera has specific i2c bus for every slot respectively
 * It needs to update nic i2c bus number after switch CurI2cTbl
 */
func UpdateNicI2cBus(uutName string) (err int) {
    mCardTyp, _ := os.LookupEnv("CARD_TYPE")
    if (mCardTyp != "MTP_MATERA" && mCardTyp != "MTP_PANAREA" && mCardTyp != "MTP_PONZA") {
        err = errType.INVALID_PARAM
        cli.Println("e", "Currently only MATERA/PANAREA/PONZA needs to update nic i2c bus! CARD_TYPE is", mCardTyp)
        return
    }

    if uutName == "UUT_NONE" {
        return
    }

    for i, _ := range(CurI2cTbl) {
        CurI2cTbl[i].Bus = MateraNicI2cBus[uutName] 
    }

    return
}

/**
 * To support Naples_MTP test card. 
 * Todo: support mix of Naples in the same MTP
 */
func SwitchI2cTbl(uutName string) (err int) {
    if uutName == "UUT_BLIND" {
        CurI2cTbl = NaplesMtpTbl
        return
    }

    if uutName == "UUT_NONE" {
        CurI2cTbl = I2cTbl
        return
    }
    uutType, err := FindUutTypeMtp(uutName)
    if err != errType.SUCCESS {
        return
    }
    if uutType == "UUT_NONE" {
        CurI2cTbl = I2cTbl
        return
    }
    if uutType == "NAPLES_MTP" {
        CurI2cTbl = NaplesMtpTbl
    } else if uutType == "NAPLES100" {
        CurI2cTbl = Naples100MtpTbl
    } else if uutType == "NAPLES100HPE"{
        CurI2cTbl = Naples100HPEMtpTbl
    } else if uutType == "NAPLES100IBM"{
        CurI2cTbl = Naples100IBMMtpTbl
    } else if uutType == "NAPLES100DELL"{
        CurI2cTbl = Naples100DELLMtpTbl
    } else if uutType == "NAPLES25" {
        CurI2cTbl = Naples25MtpTbl
    } else if uutType == "NAPLES25OCP" {
        CurI2cTbl = Naples25OcpMtpTbl
    } else if uutType == "NAPLES25SWM" {
        CurI2cTbl = Naples25SwmMtpTbl
    } else if uutType == "NAPLES25SWM833" {
        CurI2cTbl = Naples25SwmMtpTbl
    } else if uutType == "NAPLES25SWMDELL" {
        CurI2cTbl = Naples25SwmDellMtpTbl
    } else if uutType == "NAPLES25WFG" {
        CurI2cTbl = Naples25MtpTbl
    } else if uutType == "FORIO" {
        CurI2cTbl = ForioMtpTbl
    } else if uutType == "VOMERO" {
        CurI2cTbl = ForioMtpTbl
    } else if uutType == "VOMERO2" {
        CurI2cTbl = Vomero2MtpTbl
    } else if uutType == "BIODONA_D4" || uutType == "BIODONA_D5" {
        CurI2cTbl = BiodonaMtpTbl
    } else if uutType == "ORTANO" {
        CurI2cTbl = OrtanoMtpTbl
    } else if uutType == "ORTANO2" {
        CurI2cTbl = Ortano2MtpTbl
    } else if uutType == "ORTANO2A" {
        CurI2cTbl = Ortano2MtpTbl
    } else if uutType == "ORTANO2AC" {
        CurI2cTbl = Ortano2MtpTbl
    } else if uutType == "ORTANO2I" {
        CurI2cTbl = Ortano2MtpTbl
    } else if uutType == "ORTANO2S" {
        CurI2cTbl = Ortano2MtpTbl
    } else if uutType == "GINESTRA_D4" || uutType == "GINESTRA_D5" {
        CurI2cTbl = GinestraMtpTbl
    } else if uutType == "LACONADELL"   ||
              uutType == "LACONA32DELL" ||
              uutType == "POMONTEDELL"  {
        CurI2cTbl = LaconaDellMtpTbl
    } else if uutType == "LACONA"       ||
              uutType == "LACONA32"     ||
              uutType == "POMONTE"      {
        CurI2cTbl = LaconaMtpTbl
    } else if uutType == "TAORMINA" {
        CurI2cTbl = TaorTbl
    } else if uutType == "LIPARI" {
        CurI2cTbl = LipariTbl
    } else if uutType == "MALFA" {
        CurI2cTbl = MalfaMtpTbl
        CurSensorTbl = MalfaSensorTbl
    } else if uutType == "MALFA_S" {
        // this is for validation only;
        // rework a malfa to connect smbus to bus 0 or 2
        // then set mtp environment variable UUT_X=MALFA_S
        CurI2cTbl = MalfaTbl 
        CurSensorTbl = MalfaSensorTbl
    } else if uutType == "POLLARA" {
        CurI2cTbl = PollaraMtpTbl
    } else if uutType == "LINGUA" {
        CurI2cTbl = LinguaMtpTbl
    } else if uutType == "LENI" || uutType == "LENI48G" {
        CurI2cTbl = LeniMtpTbl
        CurSensorTbl = LeniSensorTbl
    } else if uutType == "GELSOP" {
        CurI2cTbl = GelsopMtpTbl
    } else if uutType == "GELSOX" {
        CurI2cTbl = GelsopMtpTbl
    } else if uutType == "GELSOB" {
        CurI2cTbl = GelsopMtpTbl
    } else if uutType == "GELSOU" {
        CurI2cTbl = GelsopMtpTbl
    } else if uutType == "MORTARO" {
        CurI2cTbl = MontaroMtpTbl
    } else if uutType == "SARACENO" {
        CurI2cTbl = SaracenoMtpTbl
        //Saraceno production SuC image moved the eeprom to 0x50.  Probe and see if it's at 0x50 and udpate the table if it is
        //get the slot number
        strLength := len(uutName)
        slot, _ := strconv.ParseUint(uutName[4:strLength], 0, 32)
        //see if device 0x50 is there
        cmdStr := fmt.Sprintf("i2cdetect -y -a %d | grep -w \"50 \"", slot+2)
        output , errGo := exec.Command("sh", "-c", cmdStr).Output()
        if errGo != nil {
            fmt.Printf("Cmd %s failed! %v", cmdStr, errGo)
        } 
        if len(output) > 0 {
            fmt.Printf("Switching Slot-%d Saracneo I2C address to 0x50\n", slot);
            CurI2cTbl[0].DevAddr = 0x50
        }
    } else if uutType == "VULSEI" {
        CurI2cTbl = VulseiMtpTbl
    } else {
        cli.Println("e", "uutType not supported!", uutType)
        err = errType.INVALID_PARAM
    }
    return
}

func SwitchI2cTblByIndex(uutIndex uint) (err int) {
    if uutIndex > 9 {
        cli.Println("e", "uutIndex not supported!", uutIndex)
        err = errType.INVALID_PARAM
        return
    }
    uutName := "UUT_" + strconv.FormatUint(uint64(uutIndex+1), 10)
    uutType, err := FindUutTypeMtp(uutName)
    if err != errType.SUCCESS {
        return
    }
    if uutType == "NAPLES_MTP" {
        CurI2cTbl = NaplesMtpTbl
    } else {
        cli.Println("e", "uutType not supported!", uutType)
        err = errType.INVALID_PARAM
    }
    return
}

func GetI2cInfo(devName string) (i2cinfo I2cInfo, err int) {
    for _, i2cinfo = range(CurI2cTbl) {
        if devName == i2cinfo.Name {
            return
        }
    }
    cli.Println("f", "Unsupported device:", devName)
    err = errType.INVALID_PARAM
    return

}

func IsDeviceInI2Ctable(devName string) (err int) {
    for _, i2cinfo := range(CurI2cTbl) {
        if devName == i2cinfo.Name {
            err = errType.SUCCESS
            return
        }
    }
    err = errType.FAIL
    return
}

func DispI2cInfo(devName string) (err int) {
    var fmtDig string = "%d"
    var fmtHex string = "0x%x"
    var fmtStr = "%-15s"
    var outStr string
    var outStrTemp string

    // Titles
/*    i2cTitle := []string {"DEV_NAME", "COMP", "BUS", "DEV_ADDR", "PAGE(PMBus)"}
    for _, title := range(i2cTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "--------------------")
    cli.Println("i", outStr)
*/
    for _, i2cInfo := range(CurI2cTbl) {
        if i2cInfo.Name != devName {
            continue
        }
        outStr = ""

        outStr = outStr + fmt.Sprintf(fmtStr, i2cInfo.Name)
        outStr = outStr + fmt.Sprintf(fmtStr, i2cInfo.Comp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.Bus)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        outStrTemp = fmt.Sprintf(fmtHex, i2cInfo.DevAddr)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.Page)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        cli.Println("i", outStr)
        return
    }
    err = errType.SUCCESS
    cli.Println("f", "Unsupported device:", devName)
    return
}

func DispI2cInfoAll() (err int) {
    var fmtDig string = "%d"
    var fmtHex string = "0x%x"
    var fmtStr = "%-15s"
    var outStr string
    var outStrTemp string

    // Titles
    i2cTitle := []string {"DEV_NAME", "COMP", "BUS", "DEV_ADDR", "PAGE(PMBus)"}
    for _, title := range(i2cTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", outStr)
    cli.Println("i", "------------------------------------")

    for _, i2cInfo := range(CurI2cTbl) {
        outStr = ""

        outStr = outStr + fmt.Sprintf(fmtStr, i2cInfo.Name)
        outStr = outStr + fmt.Sprintf(fmtStr, i2cInfo.Comp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.Bus)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        outStrTemp = fmt.Sprintf(fmtHex, i2cInfo.DevAddr)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        outStrTemp = fmt.Sprintf(fmtDig, i2cInfo.Page)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

        cli.Println("i", outStr)
    }

    return
}

func GetPage(devName string) (page byte, err int) {
    for _, i2cinfo := range(CurI2cTbl) {
        if i2cinfo.Name == devName {
            page = i2cinfo.Page
            return
        }
    }
    cli.Println("f", "Unsupported card:", devName)
    err = errType.INVALID_PARAM
    return
}

func GetSenseResistance(devName string) (senseResistance float64) {
    senseResistance = 1
    for _, sensorinfo := range(CurSensorTbl) {
        if sensorinfo.Name == devName {
            senseResistance = sensorinfo.Sense_Resistor.Coeff
        }
    }
    return
}
