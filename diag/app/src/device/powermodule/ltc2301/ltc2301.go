package ltc2301

import (
    "common/dcli"
    "common/errType"
    "protocol/i2cPtcl"
)

func ReadIin(devName string) (integer uint64, dec uint64, err int) {
    var data []byte
 
    err = i2cPtcl.Open(devName, 0, 0x8)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to open current sensor device!")
        return
    }
    defer i2cPtcl.Close()

    data, err = i2cPtcl.Read(2)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to read current sensor!")
        return
    }

    curBin := (uint16(data[0]) << 4 ) | ((uint16(data[1]) & 0xF0) >> 4)
    integer = uint64(curBin) * 5 / 1000
    dec = uint64(curBin) * 5 % 1000
    //dcli.Println("d", "int:", integer, "dec:", dec)
    return
}

func DispStatus(devName string) (err int) {
    ReadIin(devName)
    return
}
