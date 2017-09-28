package hwpm

type I2cInfo struct {
    name    string
    comp    string
    i2cIdx  uint32 // I2C controllor index
    devAddr uint32
}

var I2cTbl = []I2cInfo {
    //       name              comp         i2cIdx devAddr 
    I2cInfo {"QSFP_0",         "QSFP",      0x0,   0xA0   },
    I2cInfo {"QSFP_1",         "QSFP",      0x1,   0xA0   },
    I2cInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x2,   0xC4   },
    I2cInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x2,   0xC4   },
    I2cInfo {"VRM_HBM",        "TPS549A20", 0x2,   0x36   },
    I2cInfo {"VRM_ARM",        "TPS549A20", 0x2,   0x38   },
    I2cInfo {"FRU",            "EEPROM",    0x3,   0xA2   },
}

