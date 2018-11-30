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

func EepromUpdateMac(devName string, mac string) (err int) {
    var i2cif i2cinfo.I2cInfo

//    mac1 := mac
//    mac = strings.Replace(mac, " ", "", -1)
//    mac = strings.Replace(mac, ":", "", -1)

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

    mac1 := make([]byte, 6)
//    data, _ := strconv.Atoi(mac)
    data, _ := strconv.ParseUint(mac, 16, 64)
    mac1[0] = byte(data >> 40 & 0xFF)
    mac1[1] = byte(data >> 32 & 0xFF)
    mac1[2] = byte(data >> 24 & 0xFF)
    mac1[3] = byte(data >> 16 & 0xFF)
    mac1[4] = byte(data >> 8 & 0xFF)
    mac1[5] = byte(data & 0xFF)

    err = eeprom.UpdateMac(devName, mac1)
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

func EepromUpdateSn(devName string, sn string) (err int) {
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

    sn1 := make([]byte, 11)
    copy(sn1, []byte(sn))
    err = eeprom.UpdateSn(devName, sn1)
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

func EepromUpdateDate(devName string, date string) (err int) {
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

//    date1 := make([]byte, 3)
//    data, _ := strconv.Atoi(date)
//    date1[0] = byte(data / 10000)
//    date1[1] = byte(data % 10000 / 100)
//    date1[2] = byte(data % 100)

    err = eeprom.UpdateDate(devName, date)
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

    err = eeprom.UpdateMacMtp(devName, []byte(mac1))
    if err != errType.SUCCESS {
        return
    }

    copy(sn1, []byte(sn))
    err = eeprom.UpdateSn(devName, sn1)
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

func EepromDisp(devName string, field string) (err int) {
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

    err = eeprom.DispEeprom(devName, field)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM display failed!")
        return
    }
    return
}

func EepromDump(devName string) {
    eeprom.DumpEeprom(devName)
}
