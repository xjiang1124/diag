package ltc2301

import (
    // "fmt"

    // "common/cli"
    "common/errType"
    // "hardware/i2cinfo"
    "protocol/i2cPtcl"
)

func calcCurrent (iid uint16) (integer uint64, dec uint64, err int) {
    var current uint64
    err = errType.SUCCESS

    iid = (iid & 0xfff0) >> 4
    current = (uint64)(iid) * 5

    return current/1000, current%1000, errType.SUCCESS
}

func ReadIin(devName string) (integer uint64, dec uint64, err int) {
    var data []byte
    var current uint16
 
    err = i2cPtcl.Open(devName, 0, 0x80)
    if err != errType.SUCCESS {
        return 0, 0, err
    }
    data, err = i2cPtcl.Read(2)
    i2cPtcl.Close()
    if err != errType.SUCCESS {
        return 0, 0, err
    }
    current = (uint16)(data[0]) * 256 + (uint16)(data[1])

    integer, dec, err = calcCurrent(current)
    return
}

