package i2cinfo


// Naples25 SWM I2C table on MTP SMBus
var Naples25SwmMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CPLD_MCTP",      "CPLD_MCTP", 0x0,   0x61,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"FRU_ALOM",       "AT25320B",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"CPLD_ADAP",      "CPLD",      0x0,   0x4B,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU_ADAP",       "AT24C02C",  0x0,   0x57,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
}

