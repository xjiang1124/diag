package i2cinfo

var BiodonaTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  page    HubName     HubPort 
    I2cInfo {"ELB0_CORE",      "TPS53659",  0x0,   0x62,    0x0,    "HUB_NONE", 0},
    I2cInfo {"ELB0_ARM",       "TPS53659",  0x0,   0x62,    0x1,    "HUB_NONE", 0},
    I2cInfo {"VDDQ_DDR",       "TPS53659",  0x0,   0x22,    0x0,    "HUB_NONE", 0},
    I2cInfo {"VDD_DDR",        "TPS549A20", 0x0,   0x1B,    0x0,    "HUB_NONE", 0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE", 0},
    I2cInfo {"RTC",            "PCF85263A", 0x0,   0x51,    0x0,    "HUB_NONE", 0},
    I2cInfo {"TSENSOR",        "TMP422",    0x0,   0x4C,    0x0,    "HUB_NONE", 0},

    I2cInfo {"ZQSFP_1",        "ZQSFP",     0x1,   0x50,    0x0,    "HUB_NONE", 0},
    I2cInfo {"ZQSFP_2",        "ZQSFP",     0x2,   0x50,    0x0,    "HUB_NONE", 0},
}

// Naples25 I2C table on MTP SMBus
var BiodonaMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName     HubPort 
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE", 0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE", 0},
}

