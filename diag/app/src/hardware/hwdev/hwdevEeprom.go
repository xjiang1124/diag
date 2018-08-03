package hwdev

import (
    "strconv"
    "strings"

    "common/cli"
    "common/dmutex"
    "common/errType"

    "device/eeprom"

    "hardware/hwinfo"
    "hardware/i2cinfo"

)

func EepromUpdate(devName string, mac string, sn string) (err int) {
    var i2cif i2cinfo.I2cInfo

    mac1 := mac
    mac1 = strings.Replace(mac1, " ", "", -1)
    mac1 = strings.Replace(mac1, ":", "", -1)

    sn1 := make([]byte, 20)

    if len(mac1) != 12 {
        cli.Println("f", "Invalide MAC address: ", mac)
        return
    }
    if len(sn) > 20 {
        cli.Println("f", "SN too long: ", sn)
        return
    }

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

    err = eeprom.UpdateMac(devName, []byte(mac1))
    if err != errType.SUCCESS {
        return
    }

    copy(sn1, []byte(sn))
    err = eeprom.UpdateSN(devName, sn1)
    if err != errType.SUCCESS {
        return
    }

    err = eeprom.ProgEeprom(devName)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM update failed!")
        return
    }
    return
}

func EepromDisp(devName string) (err int) {
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

    err = eeprom.DispEeprom(devName)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM update failed!")
        return
    }
    return
}
