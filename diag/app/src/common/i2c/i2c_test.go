package i2c

import (
    "fmt"
    "testing"
)

func TestReadSim(t *testing.T) {
    data, ret := PalReadSim("VRM_CAPRI_DVDD", 0x88, 2)
    fmt.Println(data)
    fmt.Println(ret)
}

func TestRead(t *testing.T) {
    data, ret := Read("VRM_CAPRI_DVDD", 0x88, 2)
    fmt.Println(data)
    fmt.Println(ret)
}
