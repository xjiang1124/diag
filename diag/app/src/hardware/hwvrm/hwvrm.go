package hwvrm

type VrmInfo struct {
    Name    string
    Comp    string
    I2cIdx  uint32 // I2C controllor index
    DevAddr uint32
    Channel uint32 // TPS53659 only
}

var VrmTbl = []VrmInfo {
    //       name              comp         i2cIdx devAddr  channel 
    VrmInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x2,   0xC4,    0x0 },
    VrmInfo {"VRM_CAPRI_AVDD", "TPS53659",  0x2,   0xC4,    0x1 },
    //VrmInfo {"VRM_HBM",        "TPS549A20", 0x2,   0x36,    0x0 },
    //VrmInfo {"VRM_ARM",        "TPS549A20", 0x2,   0x38,    0x0 },
}

