package hwdev

import (
    "os"
    "strconv"
    "strings"
    "common/cli"
    "common/errType"

    "device/eeprom"

    "hardware/hwinfo"

)

func EepromUpdateMac(devName string, mac string) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    if os.Getenv("CARD_TYPE") == "MTP" && eeprom.CardType == "MTP" {
        mac0 := make([]byte, 12)
        copy(mac0, []byte(mac))
        err = eeprom.UpdateMac(devName, mac0)
    } else {
        mac1 := make([]byte, 6)
        data, _ := strconv.ParseUint(mac, 16, 64)
        mac1[0] = byte(data >> 40 & 0xFF)
        mac1[1] = byte(data >> 32 & 0xFF)
        mac1[2] = byte(data >> 24 & 0xFF)
        mac1[3] = byte(data >> 16 & 0xFF)
        mac1[4] = byte(data >> 8 & 0xFF)
        mac1[5] = byte(data & 0xFF)
        err = eeprom.UpdateMac(devName, mac1)
    }

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
    hwinfo.EnableHubChannelExclusive(devName)

    sn1 := make([]byte, 16)
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

func EepromUpdatePn(devName string, pn string) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    pn1 := make([]byte, 13)
    copy(pn1, []byte(pn))
    err = eeprom.UpdatePn(devName, pn1)
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
    hwinfo.EnableHubChannelExclusive(devName)

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

func EepromUpdateMajor(devName string, major string) (err int) {

    hwinfo.EnableHubChannelExclusive(devName)

    major1 := make([]byte, 2)
    copy(major1, []byte(major))
    err = eeprom.UpdateMajor(devName, major1)
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
