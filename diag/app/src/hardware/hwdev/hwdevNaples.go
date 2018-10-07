package hwdev

import (
    //"strconv"

    "common/cli"
    "common/errType"
    "device/cpld/cpldSmb"

    //"hardware/i2cinfo"
    "hardware/hwinfo"

)

func NaplesCpldRd(devName string, addr uint64, uutName string) (data byte, err int) {
    var lockName string
    //var i2cif i2cinfo.I2cInfo

    if uutName == "UUT_NONE" {
        cli.Println("e", "UUT slot not specified!")
        err = errType.INVALID_PARAM
        return
    }

    lockName, err = hwinfo.PreUutSetupBlind(uutName)
    defer hwinfo.PostUutClean(lockName)
    if err != errType.SUCCESS {
        return
    }

    data, err = cpldSmb.ReadSmb(devName, addr)

    return
}

func NaplesCpldWr(devName string, addr uint64, data byte, uutName string) (err int) {
    var lockName string
    //var i2cif i2cinfo.I2cInfo

    if uutName == "UUT_NONE" {
        cli.Println("e", "UUT slot not specified!")
        err = errType.INVALID_PARAM
        return
    }

    lockName, err = hwinfo.PreUutSetupBlind(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)

    err = cpldSmb.WriteSmb(devName, addr, data)

    return
}

