package hwvrm

import (
    "common/errType"
)

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
    VrmInfo {"VRM_HBM_P1V2",   "TPS549A20", 0x2,   0x36,    0x0 },
    VrmInfo {"VRM_ARM_P0V9",   "TPS549A20", 0x2,   0x38,    0x0 },
}

var Tps53659Tbl = []string {"VRM_CAPRI_DVDD", "VRM_CAPRI_AVDD" }

var Tps546a20Tbl = []string {"VRM_HBM_P1V2", "VRM_ARMD_P0V9" }

func GetVrmInfoByName(name string) (vrmInfo VrmInfo, err int) {
    for _, vrmInf := range(VrmTbl) {
        if name == vrmInf.Name {
            return vrmInf, errType.Success
        }
    }
    return vrmInfo, errType.Fail

}
