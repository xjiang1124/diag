package hwdev

import (
    "strconv"
    "common/cli"
    "common/dmutex"
    "common/errType"

    "device/fanctrl/adt7462"

    "hardware/hwinfo"
    "hardware/i2cinfo"

)


func FanReadReg(devName string, addr uint32) (data byte, err int) {
    var i2cif i2cinfo.I2cInfo

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

    hwinfo.EnableHubChannelExclusive(devName)
    data, err = adt7462.ReadReg(devName, addr) 
    return
}


func FanWriteReg(devName string, addr uint32, data byte) (err int) {
    var i2cif i2cinfo.I2cInfo

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

    hwinfo.EnableHubChannelExclusive(devName)
    err = adt7462.WriteReg(devName, addr, data)
    return
}

func FanDumpReg(devName string) (err int) {
    var i2cif i2cinfo.I2cInfo

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

    hwinfo.EnableHubChannelExclusive(devName)
    err = adt7462.DumpReg(devName) 
    return
}


func FanSpeedSet(devName string, pct int, mask uint64) (err int) {
    var i uint32
    var i2cif i2cinfo.I2cInfo
    var num_fans int = hwinfo.MAX_NUM_FAN
    if i2cinfo.CardType == "TAORMINA" {
        num_fans = 8
    }

    i2cif, err = i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "FanSpeedSet get i2c info failed for dev  ", devName)
        return
    }

    lockName := "i2c-"+strconv.Itoa(int(i2cif.Bus))
    err = dmutex.Lock(lockName)
    if err != errType.SUCCESS {
        cli.Println("e", "FanSpeedSet mutex lock failed for dev  ", devName)
        return
    }
    defer dmutex.Unlock(lockName)

    hwinfo.EnableHubChannelExclusive(devName)
    if i2cif.Comp == "ADT7462" {
        for i = 0; i < uint32(num_fans); i++ {
            if (mask & (1 << i)) != 0 {
                adt7462.SetFanSpeed(devName, uint64(i), uint64(pct))
            }
        }
    } else {
        cli.Println("e", "Unsupported component: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func FanSpeedGet(devName string, fanIdx uint64) (rpm uint64, err int) {
    var i2cif i2cinfo.I2cInfo

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

    hwinfo.EnableHubChannelExclusive(devName)
    if i2cif.Comp == "ADT7462" {
        rpm, err = adt7462.GetFanSpeed(devName, fanIdx)
    } else {
        cli.Println("e", "Unsupported component: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func FanGetTemp(devName string, tempIdx uint64) (temp int, err int) {
    var i2cif i2cinfo.I2cInfo

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

    hwinfo.EnableHubChannelExclusive(devName)
    if i2cif.Comp == "ADT7462" {
        temp, _, err = adt7462.GetTemp(devName, tempIdx)
    } else {
        cli.Println("e", "Unsupported component: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}

func FanSetup(devName string) (err int) {
    var i2cif i2cinfo.I2cInfo

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

    hwinfo.EnableHubChannelExclusive(devName)
    if i2cif.Comp == "ADT7462" {
        adt7462.Setup(devName)
    } else {
        cli.Println("e", "Unsupported component: ", i2cif.Comp)
        err = errType.INVALID_PARAM
    }
    return
}
