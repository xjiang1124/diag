package hwpm

type PowerModuleInfo struct {
    name    string
    devAddr uint32
    ctrlReg uint32
    intrReg uint32  // CPLD register
    intrBit uint32
}

var PmInfo = []PowerModuleInfo {
    //               name        devAddr ctrlReg intrReg intrBit
    PowerModuleInfo {"TPS53659", 0xC0,   0x100,  0x104,  0x0},
}

