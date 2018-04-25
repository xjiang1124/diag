package hwqsfp

type QsfpInfo struct {
    name    string
    devAddr uint32
    ctrlReg uint32
    intrReg uint32
    intrBit uint32
    rstReg  uint32
    rstBit  uint32
    prstReg uint32
    prstBit uint32
}

var Qsfp0Info = []QsfpInfo {
             //name     devAddr ctrlReg intrReg intrBit resReg  rstBit  prstReg prstBit
    QsfpInfo {"QSFP0",  0xA0,   0xD0,   0x200,  0x0,    0x210,  0x0,    0x220,  0x0},
    QsfpInfo {"QSFP1",  0xA0,   0xD4,   0x204,  0x0,    0x214,  0x0,    0x224,  0x0},
}

