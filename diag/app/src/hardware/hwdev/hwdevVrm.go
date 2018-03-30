package hwdev

import (
    "strconv"

    "common/cli"
    "common/dmutex"
    "common/errType"
    "device/powermodule/tps53659"
    "device/powermodule/tps549a20"

    "hardware/i2cinfo"
    "hardware/hwinfo"

)

func Margin(devName string, pct int, uutName string) (err int) {
    var i2cif i2cinfo.I2cInfo
    if uutName == "UUT_NONE" {
        i2cif, err = i2cinfo.GetI2cInfo(devName)
    } else {
        i2cif, err = i2cinfo.GetI2cInfo(uutName)
    }
    if err != errType.SUCCESS {
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(lockName)

    if uutName == "UUT_NONE" {
        err = margin(i2cif, pct)
    } else {
        err = marginUut(i2cif, pct, uutName)
    }
    return
}

func margin(i2cif i2cinfo.I2cInfo, pct int) (err int){
    devName := i2cif.Name
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

func marginUut(i2cif i2cinfo.I2cInfo, pct int, uutName string) (err int) {
    err = hwinfo.EnableHubChannelUut(uutName)
    if err != errType.SUCCESS {
        return err
    }

    i2cinfo.SwitchI2cTbl(uutName)
    err = margin(i2cif, pct)
    i2cinfo.SwitchI2cTbl("UUT_NONE")
    return
}

func Program (devName string, fileName string, verbose bool, uutName string) (err int) {
    var i2cif i2cinfo.I2cInfo
    if uutName == "UUT_NONE" {
        i2cif, err = i2cinfo.GetI2cInfo(devName)
    } else {
        i2cif, err = i2cinfo.GetI2cInfo(uutName)
    }
    if err != errType.SUCCESS {
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(lockName)

    if uutName == "UUT_NONE" {
        err = program(i2cif, fileName, verbose)
    } else {
        err = programUut(i2cif, fileName, verbose, uutName)
    }
    return
}

func program (i2cif i2cinfo.I2cInfo, fileName string, verbose bool) (err int) {
    devName := i2cif.Name
    if i2cif.Comp == "TPS53659" {
        tps53659.ProgramVerifyNvm(devName, fileName, "PROGRAM", verbose)
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func programUut (i2cif i2cinfo.I2cInfo, fileName string, verbose bool, uutName string) (err int) {
    err = hwinfo.EnableHubChannelUut(uutName)
    if err != errType.SUCCESS {
        return err
    }

    i2cinfo.SwitchI2cTbl(uutName)
    err = program(i2cif, fileName, verbose)
    i2cinfo.SwitchI2cTbl("UUT_NONE")
    return
}

func Verify (devName string, fileName string, verbose bool, uutName string) (err int) {
    var i2cif i2cinfo.I2cInfo
    if uutName == "UUT_NONE" {
        i2cif, err = i2cinfo.GetI2cInfo(devName)
    } else {
        i2cif, err = i2cinfo.GetI2cInfo(uutName)
    }
    if err != errType.SUCCESS {
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(lockName)

    if uutName == "UUT_NONE" {
        err = verify(i2cif, fileName, verbose)
    } else {
        err = verifyUut(i2cif, fileName, verbose, uutName)
    }
    return
}

func verify (i2cif i2cinfo.I2cInfo, fileName string, verbose bool) (err int) {
    devName := i2cif.Name
    if i2cif.Comp == "TPS53659" {
        err = tps53659.ProgramVerifyNvm(devName, fileName, "VERIFY", verbose)
    } else {
        cli.Println("e", "Unsupported device: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func verifyUut (i2cif i2cinfo.I2cInfo, fileName string, verbose bool, uutName string) (err int) {
    err = hwinfo.EnableHubChannelUut(uutName)
    if err != errType.SUCCESS {
        return err
    }

    i2cinfo.SwitchI2cTbl(uutName)
    err = verify(i2cif, fileName, verbose)
    i2cinfo.SwitchI2cTbl("UUT_NONE")
    return
}

