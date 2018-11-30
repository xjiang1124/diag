package main

import (
    //"fmt"
    "flag"
    //"os"
    "strings"

    //"common/cli"
    //"config"
    "hardware/hwdev"
    "hardware/hwinfo"
    "hardware/i2cinfo"
    //"device/eeprom"
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

func main() {
    devNamePtr := flag.String("dev",    "FRU",          "Device name")
    infoPtr    := flag.Bool  ("info",   false,          "Display device info")
    dispPtr    := flag.Bool  ("disp",   false,          "Display eeprom content")
    updatePtr  := flag.Bool  ("update", false,          "Update eeprom")
    macPtr     := flag.String("mac",    "",             "MAC address")
    snPtr      := flag.String("sn",     "",             "Serial number")
    mfgDatePtr := flag.String("date",   "",             "Manufacturing date")
    fieldPtr   := flag.String("field",  "all",          "Display specific eeprom field")
    dumpPtr  	:= flag.Bool ("dump", 	false,          "Dump FRU")
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    mac := strings.ToUpper(*macPtr)
    sn := strings.ToUpper(*snPtr)
    date := strings.ToUpper(*mfgDatePtr)
    field := strings.ToUpper(*fieldPtr)

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
        CpldWrite(0x1, 0x2)
        misc.SleepInUSec(1000)
        if mac != "" {
            hwdev.EepromUpdateMac(devName, mac)
            misc.SleepInUSec(500000)
        }
        if sn != "" {
            hwdev.EepromUpdateSn(devName, sn)
            misc.SleepInUSec(500000)
        }
        if date != "" {
            hwdev.EepromUpdateDate(devName, date)
            misc.SleepInUSec(500000)
        }
        CpldWrite(0x1, 0x6)
        return
    }
    
    if *dumpPtr == true {
        hwdev.EepromDump(devName)
        return
    }

    flag.Usage()
}

