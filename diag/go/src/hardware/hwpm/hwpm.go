package hwpm

type PmInfo struct {
    name    string
    devAddr uint32
    ctrlReg uint32
    intrReg uint32  // CPLD register
    intrBit uint32
}

var Tps53659Info = PmInfo {"TPS53659", 0xC0, 0x100, 0x104, 0x0}


