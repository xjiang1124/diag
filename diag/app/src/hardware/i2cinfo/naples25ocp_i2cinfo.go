package i2cinfo

// Naples25 OCP I2C table on MTP SMBus
var Naples25OcpMtpTbl = []I2cInfo {
    //       name              comp         Bus    devAddr  channel HubName   HubPort  Flag
    I2cInfo {"CPLD",           "CPLD",      0x0,   0x4A,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"CPLD_ADAP",      "CPLD",      0x0,   0x4B,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU",            "AT24C02C",  0x0,   0x50,    0x0,    "HUB_NONE",  0,    FLAG_16BIT_EEPROM},
    I2cInfo {"FRU_ADAP",       "AT24C02C",  0x0,   0x57,    0x0,    "HUB_NONE",  0,    0},
    I2cInfo {"FRU_SERIALNUM",  "AT24C02C",  0x0,   0x58,    0x0,    "HUB_NONE",  0,    0},
}

