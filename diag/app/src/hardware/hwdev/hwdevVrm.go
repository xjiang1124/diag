package hwdev

import (
    //"strconv"
    "common/cli"
    //"common/dmutex"
    "common/errType"
    "device/powermodule/tps53659"
    "device/powermodule/tps53659a"
    "device/powermodule/ltc3888"
    "device/powermodule/ltc3882"
    "device/powermodule/tps53681"
    "device/powermodule/tps549a20"
    "device/powermodule/tps544c20"
    "device/powermodule/tps544b25"
    "device/powermodule/sn1701022"
    "device/powermodule/tps53688"
    "device/powermodule/pmic"
    "device/powermodule/ds4424"
    "device/powermodule/mp8796"
    
    "hardware/i2cinfo"
    "hardware/hwinfo"

)

func Margin(devName string, pct int, uutName string) (err int) {
    if uutName == "UUT_NONE" {
        err = margin(devName, pct, true)
    } else if uutName == "MTP_MATERA" || uutName == "MTP_PANAREA" {
        err = margin(devName, pct, false)
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

        // for external margin controller, the devname is stored in i2ctable as *_VMARG
        if i2cif.Flag == 8 {
            devName = devName + "_VM"
            i2cif, err = i2cinfo.GetI2cInfo(devName)
            if err != errType.SUCCESS {
                return
            }
        }
    }

    err = hwinfo.EnableHubChannelExclusive(devName)
    if err != errType.SUCCESS {
        return err
    }

    if i2cif.Comp == "TPS53659" {
        err = tps53659.SetVMargin(devName, pct)
    } else if i2cif.Comp == "TPS53659A" {
        err = tps53659a.SetVMargin(devName, pct)
    } else if i2cif.Comp == "LTC3888" {
        err = ltc3888.SetVMargin(devName, pct)
    } else if i2cif.Comp == "LTC3882" {
        err = ltc3882.SetVMargin(devName, pct)
    } else if i2cif.Comp == "TPS549A20" {
       err = tps549a20.SetVMargin(devName, pct)
    } else if i2cif.Comp == "TPS544C20" {
       err = tps544c20.SetVMargin(devName, pct)
    } else if i2cif.Comp == "TPS544B25" {
       err = tps544b25.SetVMargin(devName, pct)
    } else if i2cif.Comp == "TPS53681" {
       err = tps53681.SetVMargin(devName, pct)
    } else if i2cif.Comp == "SN1701022" {
       err = sn1701022.SetVMargin(devName, pct)
    } else if i2cif.Comp == "TPS53688" || i2cif.Comp== "TPS53689" {
        err = tps53688.SetVMargin(devName, pct)
    } else if i2cif.Comp == "PMIC" {
        err = pmic.SetVMargin(devName, pct)
    } else if i2cif.Comp == "DS4424" {
        err = ds4424.SetVMargin(devName, pct)
    } else if i2cif.Comp == "MP8796" {
        err = mp8796.SetVMargin(devName, pct)
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

func UpdateVboot(devName string, tgtVbootMv uint64, uutName string) (err int) {
    if uutName == "UUT_NONE" {
        err = updateVboot(devName, tgtVbootMv, true)
    } else {
        err = updateVbootUut(devName, tgtVbootMv, uutName)
    }
    return
}

func updateVboot(devName string, tgtVbootMv uint64, lockFlag bool) (err int){
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
        err = tps53659.UpdateVboot(devName, tgtVbootMv)
    } else if i2cif.Comp == "TPS53659A" {
        err = tps53659a.UpdateVboot(devName, tgtVbootMv)
    } else if i2cif.Comp == "TPS53688" {
        err = tps53688.UpdateVboot(devName, tgtVbootMv)
    } else if i2cif.Comp == "LTC3888" {
        ltc3888.UpdateVboot(devName, tgtVbootMv)
        // cli.Println("i", "Unsupported function", i2cif.Comp)
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func updateVbootUut(devName string, tgtVbootMv uint64, uutName string) (err int) {
    lockName, err := hwinfo.PreUutSetup(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)

    err = updateVboot(devName, tgtVbootMv, false)
    return
}

func FindVid(devName string, tgtVoutMv uint64, uutName string) (vid uint16, err int) {
    if uutName == "UUT_NONE" {
        vid, err = findVid(devName, tgtVoutMv, true)
    } else {
        vid, err = findVidUut(devName, tgtVoutMv, uutName)
    }
    return
}

func findVid(devName string, tgtVoutMv uint64, lockFlag bool) (vid uint16, err int){
    var lockName string
    var i2cif i2cinfo.I2cInfo
    var vid8 byte

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
        vid8, err = tps53659.FindVid(devName, tgtVoutMv)
        vid = (uint16)(vid8)
    } else if i2cif.Comp == "TPS53659A" {
        vid8, err = tps53659a.FindVid(devName, tgtVoutMv)
        vid = (uint16)(vid8)
    } else if i2cif.Comp == "LTC3888" {
        vid, err = ltc3888.FindVid(tgtVoutMv)
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func findVidUut(devName string, tgtVoutMv uint64, uutName string) (vid uint16, err int) {
    lockName, err := hwinfo.PreUutSetup(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)

    vid, err = findVid(devName, tgtVoutMv, false)
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
    } else if i2cif.Comp == "TPS53659A" {
        err = tps53659a.SetVMarginByValue(devName, tgtVoutMv)
    } else if i2cif.Comp == "LTC3888" {
        err = ltc3888.SetVMarginByValue(devName, tgtVoutMv)
    } else if i2cif.Comp == "TPS544B25" {
        err = tps544b25.SetVMarginByValue(devName, tgtVoutMv)
    } else if i2cif.Comp == "PMIC" {
        err = pmic.SetVMarginByValue(devName, tgtVoutMv)
    } else if i2cif.Comp == "TPS53688" || i2cif.Comp== "TPS53689" {
        err = tps53688.SetVMarginByValue(devName, tgtVoutMv)
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
    } else if i2cif.Comp == "TPS53659A" {
        tps53659a.ProgramVerifyNvm(devName, fileName, "PROGRAM", verbose)
    } else if i2cif.Comp == "LTC3888" {
        ltc3888.ProgramVerifyNvm(devName, fileName, "PROGRAM", verbose)
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
    } else if i2cif.Comp == "TPS53659A" {
        err = tps53659a.ProgramVerifyNvm(devName, fileName, "VERIFY", verbose)
    } else if i2cif.Comp == "LTC3888" {
        err = ltc3888.ProgramVerifyNvm(devName, fileName, "VERIFY", verbose)
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
    } else if i2cif.Comp == "TPS53659A" {
        integer, dec, err = tps53659a.ReadVout(devName)
    } else if i2cif.Comp == "LTC3888" {
        integer, dec, err = ltc3888.ReadVout(devName)
    } else if i2cif.Comp == "TPS544B25" {
        integer, dec, err = tps544b25.ReadVout(devName)
    } else if i2cif.Comp == "TPS53688" || i2cif.Comp== "TPS53689" {
        integer, dec, err = tps53688.ReadVout(devName)
    } else if i2cif.Comp == "PMIC" {
        integer, dec, err = pmic.ReadVout(devName)
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
    } else if i2cif.Comp == "TPS53659A" {
        integer, dec, err = tps53659a.ReadIout(devName)
    } else if i2cif.Comp == "LTC3888" {
        integer, dec, err = ltc3888.ReadIout(devName)
    } else if i2cif.Comp == "TPS53688" || i2cif.Comp== "TPS53689" {
        integer, dec, err = tps53688.ReadIout(devName)
    } else if i2cif.Comp == "PMIC" {
        integer, dec, err = pmic.ReadIout(devName)
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

func TriggerVrFault(devName string, lockFlag bool) (err int){
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
        err = tps53659.TriggerVrFault(devName)
    } else if i2cif.Comp == "TPS53659A" {
        err = tps53659a.TriggerVrFault(devName)
    } else if i2cif.Comp == "LTC3888" {
        // To be added later
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

