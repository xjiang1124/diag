package tmpadicom

import (
    "common/errType"
    "protocol/smbus"
    "device/tempsensor/max6657"
    "device/tempsensor/adm1032"
)

func ReadMfgId(devName string) (id byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    id, err = smbus.ReadByte(devName, MFG_ID)
    return
}

func ReadDevId(devName string) (id byte, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    id, err = smbus.ReadByte(devName, DEV_ID)
    return
}

func ReadTemp(devName string, channel byte) (integer int64, dec int64, err int) {
    var id byte

    id , err = ReadMfgId(devName)
    if err != errType.SUCCESS {
        return
    }
    if id == max6657.MFG_ID_V {
        integer, dec, err = max6657.ReadTemp(devName, channel)
    } else if id == max6657.MFG_ID_V_1 {
        integer, dec, err = max6657.ReadTemp(devName, channel)
    } else if id == adm1032.MFG_ID_V {
        integer, dec, err = adm1032.ReadTemp(devName, channel)
    } else {
        err = errType.INVALID_PARAM
    }
    return
}

func DispStatus(devName string) (err int) {
    var id byte

    id , err = ReadMfgId(devName)
    if err != errType.SUCCESS {
        return
    }
    if id == max6657.MFG_ID_V {
        err = max6657.DispStatus(devName)
    } else if id == max6657.MFG_ID_V_1 {
        err = max6657.DispStatus(devName)
    } else if id == adm1032.MFG_ID_V {
        err = adm1032.DispStatus(devName)
    } else {
        err = errType.INVALID_PARAM
    }
    return
}

