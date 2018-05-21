package pex8716

import (
    "common/errType"

    "protocol/smbus"
)

func PexRegRead(devName string, regAddr uint64, buf []byte) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    tmpBuf := make([]byte, 4)

    _, err = smbus.ReadBlock(devName, regAddr, tmpBuf)
    if err != errType.SUCCESS {
        return
    }
    
    for i := 0; i < 4; i++ {
        buf[3-i] = tmpBuf[i]
    }
    return
}

func PexRegWrite(devName string, regAddr uint64, buf []byte) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()
    tmpBuf := make([]byte, 4)

    for i := 0; i < 4; i++ {
        tmpBuf[3-i] = buf[i]
    }
    _, err = smbus.WriteBlock(devName, regAddr, tmpBuf)
    if err != errType.SUCCESS {
        return
    }
    
    return
}
