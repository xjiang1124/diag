package i2cinfo

// Same as Naples25Tbl
//var Naples25Tbl = []I2cInfo {
//    //       name              comp         Bus    devAddr  page    HubName     HubPort 
//    I2cInfo {"CAP0_CORE_DVDD", "TPS53659",  0x2,   0x62,    0x0,    "HUB_NONE", 0},
//    I2cInfo {"CAP0_ARM",       "TPS53659",  0x2,   0x62,    0x1,    "HUB_NONE", 0},
//    I2cInfo {"CAP0_3V3",       "TPS549A20", 0x2,   0x1a,    0x0,    "HUB_NONE", 0},
//    I2cInfo {"CAP0_HBM",       "TPS549A20", 0x2,   0x1b,    0x0,    "HUB_NONE", 0},
//    I2cInfo {"CAP0_CORE_AVDD", "TPS549A20", 0x2,   0x1C,    0x0,    "HUB_NONE", 0},
//    I2cInfo {"FRU",            "AT24C02C",  0x2,   0x50,    0x0,    "HUB_NONE", 0},
//    I2cInfo {"RTC",            "PCF85263A", 0x2,   0x51,    0x0,    "HUB_NONE", 0},
//    I2cInfo {"TSENSOR",        "TMP422",    0x2,   0x4C,    0x0,    "HUB_NONE", 0},
//
//    I2cInfo {"SFP_1",          "SFP",       0x0,   0x50,    0x0,    "HUB_NONE", 0},
//    I2cInfo {"SFP_2",          "SFP",       0x1,   0x50,    0x0,    "HUB_NONE", 0},
//}

// Naples25 I2C table on MTP SMBus
var Naples25SwmMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName     HubPort 
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE", 0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE", 0},
    I2cInfo {"FRU_ALOM",       "AT25320B",  0x0,   0x50,    0x0,    "HUB_NONE", 0},
    I2cInfo {"CPLD_ADAP",      "CPLD",      0x0,   0x4B,    0x0,    "HUB_NONE", 0},
    I2cInfo {"FRU_ADAP",       "AT24C02C",  0x0,   0x57,    0x0,    "HUB_NONE", 0},
}

