package i2c

import (
    //"fmt"
    "testing"
)

func TestRead(t *testing.T) {
    data, ret := Read("VRM_CAPRI_DVDD", 0x88, 2)
    if data[0] != 0x29 || data [1] != 0xF0 || ret != 0 {
        t.Error(
            "Expected", 0, 0x41, 0x240,
            "Received", ret, data[0], data[1],
        )
    }
}

func TestReadWrite(t *testing.T) {
    dataR, ret := Read("VRM_CAPRI_DVDD", 0x88, 2)
    if dataR[0] != 0x29 || dataR [1] != 0xF0 || ret != 0 {
        t.Error(
            "Expected", 0, 0x41, 0x240,
            "Received", ret, dataR[0], dataR[1],
        )
    }

    var data = []byte {0x2a, 0xF1}
    ret = Write("VRM_CAPRI_DVDD", 0x88, data, 2)
    if ret != 0 {
        t.Error(
            "Expected", 0,
            "Received", ret,
        )
    }

    dataR, ret = Read("VRM_CAPRI_DVDD", 0x88, 2)
    if dataR[0] != 0x2a || dataR [1] != 0xF1 || ret != 0 {
        t.Error(
            "Expected", 0, 0x41, 0x240,
            "Received", ret, dataR[0], dataR[1],
        )
    }

}

