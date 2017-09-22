package hwvrm

import (
    "common/errType"
)

type VrmInfo struct {
    Name    string
    Comp    string
    I2cIdx  uint32 // I2C controllor index
    DevAddr uint32
    Channel byte // TPS53659 only
}

var VrmTblNaples = []VrmInfo {
    //       name              comp         i2cIdx devAddr  channel 
    VrmInfo {"VRM_CAPRI_DVDD", "TPS53659",  0x2,   0xC4,    0x0 },
    VrmInfo {"VRM_CAPRI_AVDD", "TPS53659",  0x2,   0xC4,    0x1 },
    VrmInfo {"VRM_HBM",        "TPS549A20", 0x2,   0x36,    0x0 },
    VrmInfo {"VRM_ARM",        "TPS549A20", 0x2,   0x38,    0x0 },
}

var Tps53659TblNaples= []string {"VRM_CAPRI_DVDD", "VRM_CAPRI_AVDD" }

var Tps546a20TblNaples = []string {"VRM_HBM", "VRM_ARMD" }

func GetVrmInfoByName(VrmTbl []VrmInfo, name string) (vrmInfo VrmInfo, err int) {
    for _, vrmInf := range(VrmTbl) {
        if name == vrmInf.Name {
            return vrmInf, errType.SUCCESS
        }
    }
    return vrmInfo, errType.FAIL

}
