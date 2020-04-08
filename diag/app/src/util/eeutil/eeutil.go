package main

import (
    "fmt"
    "flag"
    "os"
    "strings"

    "common/cli"
    "common/errType"
    "common/misc"
    //"config"
    "hardware/hwdev"
    "hardware/hwinfo"
    "hardware/i2cinfo"
    "device/eeprom"
    "device/cpld/cpldSmb"
)

func init() {
    //procNameTemp := strings.Split(os.Args[0], "/")
    //procName := procNameTemp[len(procNameTemp)-1]
    //cli.Init("log_"+procName+".txt", config.OutputMode)
}

func dispInfo() {
    for _, eeprom := range(hwinfo.EepromList) {
        i2cinfo.DispI2cInfo(eeprom)
    }
}

func eepromTlbInit(uut string) {
    var cardType string
    if (uut == "UUT_NONE") {
        cardType = os.Getenv("CARD_TYPE")
        if (cardType == "MTP") {
            eeprom.EepromTbl = eeprom.MtpTbl
        } else {
            eeprom.EepromTbl = eeprom.Naples100Tbl
            if eeprom.HpeNaples == 1 {
                eeprom.EepromExtTbl = eeprom.HpeTbl
            }
            if eeprom.HpeSwm == 1 {
                eeprom.EepromTbl = eeprom.HpeTblSWM
                eeprom.EepromExtTbl = eeprom.HpeTblSWMext
            }
            if eeprom.HpeOcp == 1 {
                eeprom.EepromExtTbl = eeprom.HpeTblOCP
            }
            if eeprom.HpeAlom == true {
                eeprom.EepromTbl = eeprom.HpeAlomTblAll
            }
            if (eeprom.CustType == "ORACLE") {
               eeprom.EepromTbl = eeprom.OracleTbl
           }
        }
    } else {
        // Assume now it is ARM
        cardType = os.Getenv(uut)
        eeprom.EepromTbl = eeprom.Naples100Tbl
        if eeprom.HpeNaples == 1 {
            eeprom.EepromExtTbl = eeprom.HpeTbl
        }
        if eeprom.HpeSwm == 1 {
            eeprom.EepromTbl = eeprom.HpeTblSWM
            eeprom.EepromExtTbl = eeprom.HpeTblSWMext
        }
        if eeprom.HpeOcp == 1 {
            eeprom.EepromExtTbl = eeprom.HpeTblOCP
        }
        if eeprom.HpeAlom == true {
            eeprom.EepromTbl = eeprom.HpeAlomTblAll
        }
	if (eeprom.CustType == "ORACLE") {
            eeprom.EepromTbl = eeprom.OracleTbl
        }
    }

    if cardType == "NAPLES25SWM" || cardType == "NAPLES25OCP" {
        eeprom.I2cAddr16 = true
    }

    eeprom.CardType = cardType
    fmt.Println(eeprom.CardType)
}

func main() {
    devNamePtr := flag.String("dev",    "FRU",      "Device name")
    infoPtr    := flag.Bool  ("info",   false,      "Display device info")
    dispPtr    := flag.Bool  ("disp",   false,      "Display eeprom content")
    updatePtr  := flag.Bool  ("update", false,      "Update eeprom")
    erasePtr   := flag.Bool  ("erase",  false,      "Erase all fields")
    dumpPtr    := flag.Bool  ("dump",    false,      "Dump FRU")
    macPtr     := flag.String("mac",    "",         "MAC address")
    snPtr      := flag.String("sn",     "",         "Serial number")
    pnPtr      := flag.String("pn",     "",         "Part number")
    mfgDatePtr := flag.String("date",   "",         "Manufacturing date")
    fieldPtr   := flag.String("field",  "all",      "Display specific eeprom field")
    uutPtr     := flag.String("uut",    "UUT_NONE", "Target UUT")
    majorPtr   := flag.String("maj",    "",         "Hardware major reversion")
    hpePtr     := flag.Bool  ("hpe",    false,      "HPE eeprom operation option")
    hpeSwmPtr  := flag.Bool  ("hpeSwm", false,      "HPE SWM eeprom operation option")
    hpeAlomPtr := flag.Bool  ("hpeAlom",false,      "HPE ALOM eeprom operation option")
    hpeOcpPtr  := flag.Bool  ("hpeOcp", false,      "HPE OCP eeprom operation option")
    custTypePtr:= flag.String("custType", "pensando", "Customerized eeeprom operation option")
    numBytesPtr:= flag.Int   ("numBytes",0,         "Number of bytes to be dumped")
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    mac := strings.ToUpper(*macPtr)
    sn := strings.ToUpper(*snPtr)
    pn := strings.ToUpper(*pnPtr)
    date := strings.ToUpper(*mfgDatePtr)
    field := strings.ToUpper(*fieldPtr)
    uut := strings.ToUpper(*uutPtr)
    major := strings.ToUpper(*majorPtr)
    numBytes := *numBytesPtr
    fixHpe := 1
    custType := strings.ToUpper(*custTypePtr)

    lock, _ := hwinfo.PreUutSetup(uut)
    defer hwinfo.PostUutClean(lock)
    eeprom.CustType = custType
    if *hpeAlomPtr {
        defer hwdev.SelSmbFromAdaptor(uut, false)  //Set mux back to SMB when done
    }

    if *hpePtr == true {
        eeprom.HpeNaples = 1
    }

    if *hpeSwmPtr == true {
        eeprom.HpeSwm = 1
    }

    if *hpeAlomPtr == true {
        eeprom.HpeAlom = true
    }

    if *hpeOcpPtr == true {
        eeprom.HpeOcp = 1
    }

    if uut != "UUT_NONE" {
        i2cinfo.SwitchI2cTbl(uut)
    }

    eepromTlbInit(uut)

    hwdev.SelSmbFromAdaptor(uut, *hpeAlomPtr)
    iInfo, err := i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to obtain I2C info of", devName)
        return
    }

    if *infoPtr == true {
        dispInfo()
        return
    }

    if *dispPtr == true {
        hwdev.EepromDisp(devName, iInfo.Bus, iInfo.DevAddr, field)
        return
    }

    if *erasePtr == true {
        eeprom.Erase = true
        if numBytes == 0 {
            cli.Println("e", "You need to set the number of bytes to erase..failed to execute erase command", devName)
            return;
        }
    } else {
        eeprom.Erase = false
    }

    if *updatePtr == true || eeprom.Erase == true {
        // FIXME: Skip for ALOM
        if os.Getenv("CARD_TYPE") == "MTP" && uut != "UUT_NONE" && eeprom.HpeAlom == false {
            fmt.Println("On MTP")
            rd, _ := cpldSmb.ReadSmb("CPLD", 0x21)
            rd = rd & 0xFD
            _ = cpldSmb.WriteSmb("CPLD", 0x21, rd)
        } else {
            CpldWrite(0x1, 0x2)
        }

        if eeprom.Erase == true {
            cli.Printf("i", "Erasing Addr 0 -  0x%x\n",numBytes)
            hwdev.EepromErase(devName, iInfo.Bus, iInfo.DevAddr, numBytes)
        } 

        if *updatePtr == true {
            misc.SleepInUSec(1000)
            if mac != "" && eeprom.HpeAlom == false {
                hwdev.EepromUpdateMac(devName, iInfo.Bus, iInfo.DevAddr, mac)
                misc.SleepInUSec(500000)
                fixHpe = 0
            }
            if sn != "" {
                hwdev.EepromUpdateSn(devName, iInfo.Bus, iInfo.DevAddr, sn)
                misc.SleepInUSec(500000)
                fixHpe = 0
            }
            if pn != "" {
                hwdev.EepromUpdatePn(devName, iInfo.Bus, iInfo.DevAddr, pn)
                misc.SleepInUSec(500000)
                fixHpe = 0
            }
            if date != "" {
                hwdev.EepromUpdateDate(devName, iInfo.Bus, iInfo.DevAddr, date)
                misc.SleepInUSec(500000)
                fixHpe = 0
            }
            if major != "" {
                hwdev.EepromUpdateMajor(devName, iInfo.Bus, iInfo.DevAddr, major)
                misc.SleepInUSec(500000)
                fixHpe = 0
            }
            //Fix Naples25 HPE that are mispgorammed...option for FAE
            if fixHpe > 0 && *hpePtr == true {
                fmt.Printf(" FIXING NAPLES25 HPE\n")
                hwdev.EepromFixNaples25HPE(devName, iInfo.Bus, iInfo.DevAddr)
                //hwdev.EepromErase(devName, iInfo.Bus, iInfo.DevAddr, 256)

            }
        }

        // FIXME
        if os.Getenv("CARD_TYPE") == "MTP" && uut != "UUT_NONE" && eeprom.HpeAlom == false {
            rd, _ := cpldSmb.ReadSmb("CPLD", 0x21)
            rd = rd | 0x2
            _ = cpldSmb.WriteSmb("CPLD", 0x21, rd)
        } else {
            CpldWrite(0x1, 0x6)
        }
        return
    }

    if *dumpPtr == true {
        hwdev.EepromDump(devName, iInfo.Bus, iInfo.DevAddr, numBytes)
        return
    }

    flag.Usage()
}

