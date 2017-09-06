package hwpm

type PowerModuleInfo struct {
    name    string
    i2cIdx  uint32 // I2C controllor index
    devAddr uint32
}

var PmInfo = []PowerModuleInfo {
    //               name        i2cIdx devAddr 
    PowerModuleInfo {"TPS53659", 0x1,   0xC0   },
    PowerModuleInfo {"TPS549_1", 0x1,   0x36   },
    PowerModuleInfo {"TPS549_2", 0x1,   0x38   },
}

