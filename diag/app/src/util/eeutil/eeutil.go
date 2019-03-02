package main

import (
    "fmt"
    "flag"
    "os"
    "strings"

    //"common/cli"
    //"config"
    "hardware/hwdev"
    "hardware/hwinfo"
    "hardware/i2cinfo"
    "device/eeprom"
    "device/cpld/cpldSmb"
    "common/misc"
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
    if os.Getenv("CARD_TYPE") == "NAPLES100" {
        eeprom.CardType = "NAPLES100"
        eeprom.EepromTbl = eeprom.Naples100Tbl
    } else if os.Getenv("CARD_TYPE") == "NAPLES25" || uut != "UUT_NONE" {
        eeprom.CardType = "NAPLES25"
        eeprom.EepromTbl = eeprom.Naples100Tbl
    } else if uut == "UUT_NONE" {
        eeprom.CardType = "MTP"
        eeprom.EepromTbl = eeprom.MtpTbl
    } else {
        fmt.Println("Unsupported UUT and card type")
    }
}

func main() {
    devNamePtr := flag.String("dev",    "FRU",          "Device name")
    infoPtr    := flag.Bool  ("info",   false,          "Display device info")
    dispPtr    := flag.Bool  ("disp",   false,          "Display eeprom content")
    updatePtr  := flag.Bool  ("update", false,          "Update eeprom")
    macPtr     := flag.String("mac",    "",             "MAC address")
    snPtr      := flag.String("sn",     "",             "Serial number")
    pnPtr      := flag.String("pn",     "",             "Part number")
    mfgDatePtr := flag.String("date",   "",             "Manufacturing date")
    fieldPtr   := flag.String("field",  "all",          "Display specific eeprom field")
    dumpPtr    := flag.Bool ("dump", 	false,          "Dump FRU")
    uutPtr     := flag.String("uut",  "UUT_NONE", 		"Target UUT")
    majorPtr   := flag.String("maj",     "",            "Hardware mayor reversion")
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    mac := strings.ToUpper(*macPtr)
    sn := strings.ToUpper(*snPtr)
    pn := strings.ToUpper(*pnPtr)
    date := strings.ToUpper(*mfgDatePtr)
    field := strings.ToUpper(*fieldPtr)
    uut := strings.ToUpper(*uutPtr)
    major := strings.ToUpper(*majorPtr)

    lock, _ := hwinfo.PreUutSetup(uut)
    
    defer hwinfo.PostUutClean(lock)

    eepromTlbInit(uut)
    
    if *infoPtr == true {
        dispInfo()
        return
    }

    if *dispPtr == true {
        hwdev.EepromDisp(devName, field)
        return
    }

    if *updatePtr == true {
//        hwdev.EepromUpdate(devName, mac, sn)
        if os.Getenv("CARD_TYPE") == "MTP" && uut != "UUT_NONE" {
            fmt.Println("MTP")
            rd, _ := cpldSmb.ReadSmb("CPLD", 0x21)
            rd = rd & 0xFD
            _ = cpldSmb.WriteSmb("CPLD", 0x21, rd)
        } else {
            CpldWrite(0x1, 0x2)
        }
        misc.SleepInUSec(1000)
        if mac != "" {
            hwdev.EepromUpdateMac(devName, mac)
            misc.SleepInUSec(500000)
        }
        if sn != "" {
            hwdev.EepromUpdateSn(devName, sn)
            misc.SleepInUSec(500000)
        }
        if pn != "" {
            hwdev.EepromUpdatePn(devName, pn)
            misc.SleepInUSec(500000)
        }
        if date != "" {
            hwdev.EepromUpdateDate(devName, date)
            misc.SleepInUSec(500000)
        }
        if major != "" {
            hwdev.EepromUpdateMajor(devName, major)
            misc.SleepInUSec(500000)
        }
        if os.Getenv("CARD_TYPE") == "MTP" && uut != "UUT_NONE" {
            rd, _ := cpldSmb.ReadSmb("CPLD", 0x21)
            rd = rd | 0x2
            _ = cpldSmb.WriteSmb("CPLD", 0x21, rd)
        } else {
            CpldWrite(0x1, 0x6)
        }
        return
    }
    
    if *dumpPtr == true {
        hwdev.EepromDump(devName)
        return
    }

    flag.Usage()
}

