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

func EepromUpdateMac(devName string, bus uint32, devAddr byte, mac string) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    if os.Getenv("CARD_TYPE") == "MTP" && eeprom.CardType == "MTP" {
        mac0 := make([]byte, 12)
        copy(mac0, []byte(mac))
        err = eeprom.UpdateMac(devName, bus, devAddr, mac0)
    } else {
        mac1 := make([]byte, 6)
        data, _ := strconv.ParseUint(mac, 16, 64)
        mac1[0] = byte(data >> 40 & 0xFF)
        mac1[1] = byte(data >> 32 & 0xFF)
        mac1[2] = byte(data >> 24 & 0xFF)
        mac1[3] = byte(data >> 16 & 0xFF)
        mac1[4] = byte(data >> 8 & 0xFF)
        mac1[5] = byte(data & 0xFF)
        err = eeprom.UpdateMac(devName, bus, devAddr, mac1)
    }

    if err != errType.SUCCESS {
        return
    }

    err = eeprom.ProgEeprom(devName, bus, devAddr)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM update failed!")
        return
    }
    return
}

func EepromUpdateSn(devName string, bus uint32, devAddr byte, sn string) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    sn1 := make([]byte, 16)
    copy(sn1, []byte(sn))
    err = eeprom.UpdateSn(devName, bus, devAddr, sn1)
    if err != errType.SUCCESS {
        return
    }

    err = eeprom.ProgEeprom(devName, bus, devAddr)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM update failed!")
        return
    }
    return
}

func EepromUpdatePn(devName string, bus uint32, devAddr byte, pn string) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    pn1 := make([]byte, 13)
    copy(pn1, []byte(pn))
    err = eeprom.UpdatePn(devName, bus, devAddr, pn1)
    if err != errType.SUCCESS {
        return
    }

    err = eeprom.ProgEeprom(devName, bus, devAddr)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM update failed!")
        return
    }
    return
}

func EepromUpdateDate(devName string, bus uint32, devAddr byte, date string) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    err = eeprom.UpdateDate(devName, bus, devAddr, date)
    if err != errType.SUCCESS {
        return
    }

    err = eeprom.ProgEeprom(devName, bus, devAddr)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM update failed!")
        return
    }
    return
}

func EepromUpdateMajor(devName string, bus uint32, devAddr byte, major string) (err int) {

    hwinfo.EnableHubChannelExclusive(devName)

    major1 := make([]byte, 2)
    copy(major1, []byte(major))
    err = eeprom.UpdateMajor(devName, bus, devAddr, major1)
    if err != errType.SUCCESS {
        return
    }

    err = eeprom.ProgEeprom(devName, bus, devAddr)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM update failed!")
        return
    }
    return
}

func EepromUpdate(devName string, bus uint32, devAddr byte, mac string, sn string) (err int) {
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
    err = eeprom.UpdateSn(devName, bus, devAddr, sn1)
    if err != errType.SUCCESS {
        return
    }

    err = eeprom.ProgEeprom(devName, bus, devAddr)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM update failed!")
        return
    }
    return
}

func EepromDisp(devName string, bus uint32, devAddr byte, field string) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    err = eeprom.DispEeprom(devName, bus, devAddr, field)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM display failed!")
        return
    }
    return
}

func EepromDump(devName string, bus uint32, devAddr byte) {
    eeprom.DumpEeprom(devName, bus, devAddr)
}
