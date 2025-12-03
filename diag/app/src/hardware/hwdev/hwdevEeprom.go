package hwdev

import (
    "os"
    "strconv"
    "strings"
    "common/cli"
    "common/errType"

    "device/cpld/cpldSmb"
    "device/cpld/naples25swmAdapCpld"
    "device/eeprom"

    "hardware/hwinfo"
    "hardware/i2cinfo"

    "os/exec"

)

// Naples25SW need to choose SMBus between NIC and ALOM
func SelSmbFromAdaptor(uutName string, HpeAlom bool) (err int) {
    var ctrlVal byte

    uutType, err := i2cinfo.FindUutTypeMtp(uutName)
    if err != errType.SUCCESS {
        return
    }

    if uutType == "UUT_NONE" {
        // Do nothing
        return
    }

    if uutType != "NAPLES25SWM" {
        // Do nothing
        return
    }


    //Probe for the CPLD
    _ , errGo := exec.Command("/usr/sbin/i2cget","-y","0","0x4b", "0x80").Output()
    if errGo != nil {
        return
    } 
    cli.Printf("i", "SET ALOM CPLD MUX FOR FRU ACCESS\n")


    ctrlVal, err = cpldSmb.ReadSmb("CPLD_ADAP", naples25swmAdapCpld.REG_CTRL)
    if HpeAlom == false {
        //ctrlVal = 0x14
        ctrlVal &^= 0x02
        ctrlVal = ctrlVal | 0x04
    } else {
        //ctrlVal = 0x12
        ctrlVal &^= 0x04
        ctrlVal = ctrlVal| 0x02
    }
    err = cpldSmb.WriteSmb("CPLD_ADAP", naples25swmAdapCpld.REG_CTRL, ctrlVal)

    return
}

func EepromFixNaples25HPE(devName string, bus uint32, devAddr byte) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    err = eeprom.FixNaples25HPEfru(devName, bus, devAddr)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM Fix Naples25HPE failed!")
        return
    }
/*
    err = EepromErase(devName, bus, devAddr, 256)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM erase failed!")
        return
    }
*/

    err = eeprom.ProgEeprom(devName, bus, devAddr)
    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM update failed!")
        return
    }
    return
}

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

    err = eeprom.UpdateSn(devName, bus, devAddr, []byte(sn))
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

    for i := 0; i < len(pn1); i++ {
        pn1[i] = 0x20    //Pad out any remaining p/n length with spaces in case the p/n is not 13 characters
    }
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

func EepromErase(devName string, bus uint32, devAddr byte, numBytes int) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    found, _ := eeprom.CardInListTlv(devName)
    if found == true {
        err = eeprom.EraseEepromTlv(devName, numBytes)
    } else {
        err = eeprom.EraseEeprom(devName, bus, devAddr, numBytes)
    }

    if err != errType.SUCCESS {
        cli.Println("f", "EEPROM Erase failed!")
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

func EepromDump(devName string, bus uint32, devAddr byte, numBytes int, fname string, toFile bool) (output []byte) {
    hwinfo.EnableHubChannelExclusive(devName)
    output, _ = eeprom.DumpEeprom(devName, bus, devAddr, numBytes, fname, toFile)
    return output
}


func EepromMatchSearchFruPN(devName string, bus uint32, devAddr byte, pn string) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    err = eeprom.MatchSearchFruPartnumber(devName, bus, devAddr, pn)
    return err
}

func EepromVerifyCSUM(devName string, bus uint32, devAddr byte, OutputEnabled bool) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    err = eeprom.VerifyFruCSUM(devName, bus, devAddr, OutputEnabled)
    if err != errType.SUCCESS {
        cli.Println("f", "Verify EEPROM Checksum(s) failed!")
        return
    }
    return
}

//==============================================================================
//                         N E W     F U N C T I O N S
//==============================================================================

func EepromUpdateNew(devName string, bus uint32, devAddr byte, sn string, pn string, sku string, mac string, date string, dpn string, skuMode bool, boardID uint32) (err int) {
    //Function updates SN, PN, MAC. and Date. All fields required to update successfully.
    hwinfo.EnableHubChannelExclusive(devName)
    err = eeprom.ProgData(devName, bus, devAddr, sn, pn, sku, mac, date, dpn, skuMode, boardID)
    if err != errType.SUCCESS {
        cli.Println("e", "EEPROM update failed!")
        return
    }

    return
} 

func EepromDisplayNew(devName string, bus uint32, devAddr byte, field string, fpo bool) (err int) {
    //Displays data read from Eeprom
    hwinfo.EnableHubChannelExclusive(devName)

    err = eeprom.DisplayData(devName, bus, devAddr, field, fpo)

    return
}


func EepromUpdateTlvs(devName string, sn string, pn string, sn2 string, pn2 string,
                         mac string, date string) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    err = eeprom.ProgTlvs(devName, sn, pn, sn2, pn2, mac, date)
    if err != errType.SUCCESS {
        cli.Println("e", "EEPROM update failed!")
        return
    }

    return
}

func EepromUpdateTlvField(devName string, field string, value string) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    err = eeprom.ProgTlvField(devName, field, value)
    if err != errType.SUCCESS {
        cli.Println("e", "EEPROM update failed!")
        return
    }

    return
}

func EepromDisplayTlvs(devName string, field string, fpo bool) (err int) {
    hwinfo.EnableHubChannelExclusive(devName)

    err = eeprom.DisplayTlvs(devName, field, fpo)

    return
}

