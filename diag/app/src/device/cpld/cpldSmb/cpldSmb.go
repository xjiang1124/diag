package cpldSmb

import (
    //"common/cli"
    "common/errType"
    "protocol/smbus"
)

func ReadSmb(devName string, addr uint64) (data byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data, err = smbus.ReadByte(devName, addr)
    return
}

func WriteSmb(devName string, addr uint64, data byte) (err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    err = smbus.WriteByte(devName, addr, data)
    return
}

