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

func FanSpeedSet(devName string, pct int, mask uint64) (err int) {
    var i uint64
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
        for i = 0; i < hwinfo.MAX_NUM_FAN; i++ {
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
