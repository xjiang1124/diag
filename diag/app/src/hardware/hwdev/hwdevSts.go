package hwdev

import (
    "sort"
    "strconv"

    "common/cli"
    "common/dmutex"
    "common/errType"

    "device/powermodule/tps53659"

    "hardware/hwinfo"
    "hardware/i2cinfo"

)

func DevInfo(devName string, uutName string) (err int) {
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

    if i2cif.Comp == "TPS53659" {
        tps53659.Info(devName)
    } else {
        cli.Println("e", "Unsupported component:", i2cif.Comp)
    }
    return
}

func DispStatus(devName string, uutName string) (err int){
    if uutName == "UUT_NONE" {
        err = dispStatus(devName)
    } else {
        err = dispStatusUut(devName, uutName)
    }
    return
}

func dispStatusDev(devName string, lockFlag bool) (err int){
    var i2cif i2cinfo.I2cInfo
    if lockFlag == true {
        i2cif, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            return
        }

        lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
        err = dmutex.Lock(lockName)
        if err != errType.SUCCESS {
            return
        }
        defer dmutex.Unlock(lockName)
    }

    err = hwinfo.EnableHubChannelExclusive(devName)
    if err != errType.SUCCESS {
        return
    }
    dispFunc, ok := hwinfo.DispStaList[devName]
    if ok == false {
        cli.Println("f", "Invalde device: ", devName)
        err = errType.INVALID_PARAM
        return
    }
    err = dispFunc(devName)
    return
}

func dispStatusDevUut(devName string, uutName string) (err int){
    var i2cif i2cinfo.I2cInfo
    i2cif, err = i2cinfo.GetI2cInfo(uutName)
    if err != errType.SUCCESS {
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        return
    }
    defer dmutex.Unlock(lockName)

    err = hwinfo.EnableHubChannelUut(uutName)
    if err != errType.SUCCESS {
        return err
    }

    hwinfo.SwitchHwInfo(uutName)
    i2cinfo.SwitchI2cTbl(uutName)

    err = dispStatusDev(devName, false)

    i2cinfo.SwitchI2cTbl("UUT_NONE")
    hwinfo.SwitchHwInfo("UUT_NONE")

    return
}

func dispStatus(devName string) (err int){
    if devName == "ALL" {
        // golang range(map) sequence is random
        // Sorted output
        keys := make([]string, 0)
        for k, _ := range(hwinfo.DispStaList) {
            keys = append(keys, k)
        }
        sort.Strings(keys)
        for _, dev := range(keys) {
            err = dispStatusDev(dev, true)
            if err != errType.SUCCESS {
                return
            }
        }
    } else {
        err = dispStatusDev(devName, true)
    }
    return
}

func dispStatusUut(devName string, uutName string) (err int){
    if devName == "ALL" {
        cli.Println("e", "\"ALL\" does not support by UUT!")
        err = errType.INVALID_PARAM
        return
    }

    err = dispStatusDevUut(devName, uutName)

    return
}
