package hwdev

import (
    //"strconv"

    "common/cli"
    //"common/dmutex"
    "common/errType"
    "device/powermodule/tps53659"
    "device/powermodule/tps549a20"

    "hardware/i2cinfo"
    "hardware/hwinfo"

)

func Margin(devName string, pct int, uutName string) (err int) {
    if uutName == "UUT_NONE" {
        err = margin(devName, pct, true)
    } else {
        err = marginUut(devName, pct, uutName)
    }
    return
}

func margin(devName string, pct int, lockFlag bool) (err int){
    var lockName string
    var i2cif i2cinfo.I2cInfo
    if lockFlag == true {
        lockName, i2cif, err = hwinfo.LockDev(devName)
        if err != errType.SUCCESS {
            return
        }
        defer hwinfo.UnlockDev(lockName)
    } else {
        i2cif, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            return
        }
    }

    err = hwinfo.EnableHubChannelExclusive(devName)
    if err != errType.SUCCESS {
        return err
    }

    if i2cif.Comp == "TPS53659" {
        err = tps53659.SetVMargin(devName, pct)
    } else if i2cif.Comp == "TPS549A20" {
       err = tps549a20.SetVMargin(devName, pct)
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func marginUut(devName string, pct int, uutName string) (err int) {
    lockName, err := hwinfo.PreUutSetup(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)

    err = margin(devName, pct, false)
    return
}

func MarginByValue(devName string, tgtVoutMv uint64, uutName string) (err int) {
    if uutName == "UUT_NONE" {
        err = marginByValue(devName, tgtVoutMv, true)
    } else {
        err = marginUutByValue(devName, tgtVoutMv, uutName)
    }
    return
}

func marginByValue(devName string, tgtVoutMv uint64, lockFlag bool) (err int){
    var lockName string
    var i2cif i2cinfo.I2cInfo
    if lockFlag == true {
        lockName, i2cif, err = hwinfo.LockDev(devName)
        if err != errType.SUCCESS {
            return
        }
        defer hwinfo.UnlockDev(lockName)
    } else {
        i2cif, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            return
        }
    }

    err = hwinfo.EnableHubChannelExclusive(devName)
    if err != errType.SUCCESS {
        return err
    }

    if i2cif.Comp == "TPS53659" {
        err = tps53659.SetVMarginByValue(devName, tgtVoutMv)
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func marginUutByValue(devName string, tgtVoutMv uint64, uutName string) (err int) {
    lockName, err := hwinfo.PreUutSetup(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)

    err = marginByValue(devName, tgtVoutMv, false)
    return
}

func Program (devName string, fileName string, verbose bool, uutName string) (err int) {
    if uutName == "UUT_NONE" {
        err = program(devName, fileName, verbose, true)
    } else {
        err = programUut(devName, fileName, verbose, uutName)
    }
    return
}

func program (devName string, fileName string, verbose bool, lockFlag bool) (err int) {
    var lockName string
    var i2cif i2cinfo.I2cInfo
    if lockFlag == true {
        lockName, i2cif, err = hwinfo.LockDev(devName)
        if err != errType.SUCCESS {
            return
        }
        defer hwinfo.UnlockDev(lockName)
    } else {
        i2cif, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            return
        }
    }


    if i2cif.Comp == "TPS53659" {
        tps53659.ProgramVerifyNvm(devName, fileName, "PROGRAM", verbose)
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func programUut (devName string, fileName string, verbose bool, uutName string) (err int) {
    lockName, err := hwinfo.PreUutSetup(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)
    err = program(devName, fileName, verbose, false)
    return
}

func Verify (devName string, fileName string, verbose bool, uutName string) (err int) {
    if uutName == "UUT_NONE" {
        err = verify(devName, fileName, verbose, false)
    } else {
        err = verifyUut(devName, fileName, verbose, uutName)
    }
    return
}

func verify (devName string, fileName string, verbose bool, lockFlag bool) (err int) {
    var lockName string
    var i2cif i2cinfo.I2cInfo
    if lockFlag == true {
        lockName, i2cif, err = hwinfo.LockDev(devName)
        if err != errType.SUCCESS {
            return
        }
        defer hwinfo.UnlockDev(lockName)
    } else {
        i2cif, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            return
        }
    }


    if i2cif.Comp == "TPS53659" {
        err = tps53659.ProgramVerifyNvm(devName, fileName, "VERIFY", verbose)
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func verifyUut (devName string, fileName string, verbose bool, uutName string) (err int) {
    lockName, err := hwinfo.PreUutSetup(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)

    err = verify(devName, fileName, verbose, false)
    return
}

func ReadVout(devName string, uutName string) (voutMv uint64, err int) {
    if uutName == "UUT_NONE" {
        voutMv, err = readVout(devName, true)
    } else {
        voutMv, err = readVoutUut(devName, uutName)
    }
    return
}

func readVout(devName string, lockFlag bool) (voutMv uint64, err int){
    var integer uint64
    var dec uint64
    var lockName string
    var i2cif i2cinfo.I2cInfo
    if lockFlag == true {
        lockName, i2cif, err = hwinfo.LockDev(devName)
        if err != errType.SUCCESS {
            return
        }
        defer hwinfo.UnlockDev(lockName)
    } else {
        i2cif, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            return
        }
    }

    err = hwinfo.EnableHubChannelExclusive(devName)
    if err != errType.SUCCESS {
        return
    }

    if i2cif.Comp == "TPS53659" {
        integer, dec, err = tps53659.ReadVout(devName)
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }

    voutMv = integer * 1000 + dec
    return
}

func readVoutUut(devName string, uutName string) (voutMv uint64, err int) {
    lockName, err := hwinfo.PreUutSetup(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)

    voutMv, err = readVout(devName, false)
    return
}
func ReadIout(devName string, uutName string) (ioutMa uint64, err int) {
    if uutName == "UUT_NONE" {
        ioutMa, err = readIout(devName, true)
    } else {
        ioutMa, err = readIoutUut(devName, uutName)
    }
    return
}

func readIout(devName string, lockFlag bool) (ioutMa uint64, err int){
    var integer uint64
    var dec uint64
    var lockName string
    var i2cif i2cinfo.I2cInfo
    if lockFlag == true {
        lockName, i2cif, err = hwinfo.LockDev(devName)
        if err != errType.SUCCESS {
            return
        }
        defer hwinfo.UnlockDev(lockName)
    } else {
        i2cif, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            return
        }
    }

    err = hwinfo.EnableHubChannelExclusive(devName)
    if err != errType.SUCCESS {
        return
    }

    if i2cif.Comp == "TPS53659" {
        integer, dec, err = tps53659.ReadIout(devName)
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }

    ioutMa = integer * 1000 + dec
    return
}

func readIoutUut(devName string, uutName string) (ioutMa uint64, err int) {
    lockName, err := hwinfo.PreUutSetup(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)

    ioutMa, err = readIout(devName, false)
    return
}

