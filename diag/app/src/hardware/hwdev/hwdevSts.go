package hwdev

import (
    "sort"
    //"strconv"

    "common/cli"
    //"common/dmutex"
    "common/errType"

    "device/powermodule/tps53659"
    "device/powermodule/tps53659a"
    "device/powermodule/ltc3888"

    "hardware/hwinfo"
    "hardware/i2cinfo"

)

func DevInfo(devName string, uutName string) (err int) {
    if uutName == "UUT_NONE" {
        err = devInfo(devName, true)
    } else {
        err = devInfoUut(devName, uutName)
    }
    return
}

func devInfo(devName string, lockFlag bool) (err int) {
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
        tps53659.Info(devName)
    } else if i2cif.Comp == "TPS53659A" {
        tps53659a.Info(devName)
    } else if i2cif.Comp == "LTC3888" {
        ltc3888.Info(devName)
    } else {
        cli.Println("e", "Unsupported component:", devName, i2cif.Comp)
    }
    return
}

func devInfoUut(devName string, uutName string) (err int) {
    lockName, err := hwinfo.PreUutSetup(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)

    err = devInfo(devName, false)
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
    var lockName string

    //LIPARI and MATERA CURRENTLY DO NOT LOCK USING DIAG
    if i2cinfo.CardType != "LIPARI" && 
       i2cinfo.CardType != "MTFUJI" && 
       i2cinfo.CardType != "MTP_MATERA" && 
       i2cinfo.CardType != "MTP_PANAREA" && 
       i2cinfo.CardType != "MTP_PONZA" {
        if lockFlag == true {
            lockName, _, err = hwinfo.LockDev(devName)
            if err != errType.SUCCESS {
                cli.Println("f", "failed to lock the device: ", devName)
                return
            }
            defer hwinfo.UnlockDev(lockName)
        }
    }


    if i2cinfo.CardType == "TAORMINA" {
        //On Taormina (and maybe later platforms), there are parts we
        //need to display status on that are not in the I2C table, so skip trying 
        //to set the mux if the hwinfo component is not in the i2cinfo component
        err = i2cinfo.IsDeviceInI2Ctable(devName)
        if err == errType.SUCCESS {
            err = hwinfo.EnableHubChannelExclusive(devName)
            if err != errType.SUCCESS {
                return
            }
        }
    } else {
        err = hwinfo.EnableHubChannelExclusive(devName)
        if err != errType.SUCCESS {
            return
        }
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
                cli.Println("f", "Failed to retrieve status:", dev)
            }
        }
    } else {
        err = dispStatusDev(devName, true)
    }
    return
}

func dispStatusUut(devName string, uutName string) (err int){
    lockName, err := hwinfo.PreUutSetup(uutName)
    if err != errType.SUCCESS {
        return
    }
    defer hwinfo.PostUutClean(lockName)

    err = dispStatus(devName)
    return
}
