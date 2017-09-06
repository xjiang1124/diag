package hwpm

type I2cInfo struct {
    name    string
    i2cIdx  uint32 // I2C controllor index
    devAddr uint32
}

var I2cTbl = []I2cInfo {
    //       name        i2cIdx devAddr 
    I2cInfo {"TPS53659", 0x1,   0xC0   },
    I2cInfo {"TPS549_1", 0x1,   0x36   },
    I2cInfo {"TPS549_2", 0x1,   0x38   },
}

