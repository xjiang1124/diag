package main

import (
    //"fmt"
    "flag"
    "os"
    "strings"

    "common/cli"
    "config"
    "hardware/hwdev"
    "hardware/hwinfo"
    "hardware/i2cinfo"
    //"device/eeprom"
)

func init() {
    procNameTemp := strings.Split(os.Args[0], "/")
    procName := procNameTemp[len(procNameTemp)-1]
    cli.Init("log_"+procName+".txt", config.OutputMode)
}

func dispInfo() {
    for _, eeprom := range(hwinfo.EepromList) {
        i2cinfo.DispI2cInfo(eeprom)
    }
}

func main() {
    devNamePtr := flag.String("dev",    "ALL",          "Device name")
    infoPtr    := flag.Bool  ("info",   false,          "Display device info")
    dispPtr    := flag.Bool  ("disp",   false,          "Display eeprom content")
    updatePtr  := flag.Bool  ("update", false,          "Update eeprom")
    macPtr     := flag.Uint64("mac",    0, 				"MAC address")
    snPtr      := flag.String("sn",     "",   			"Serial number")
    mfgDatePtr := flag.String("date",   "",   			"Manufacturing date")
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    mac := *macPtr
    sn := strings.ToUpper(*snPtr)
    date := strings.ToUpper(*mfgDatePtr)

    if *infoPtr == true {
        dispInfo()
        return
    }

    if *dispPtr == true {
        hwdev.EepromDisp(devName)
        return
    }

    if *updatePtr == true {
//        hwdev.EepromUpdate(devName, mac, sn)
        if mac != 0 {
            hwdev.EepromUpdateMac(devName, mac)
        }
        if sn != "" {
            hwdev.EepromUpdateSn(devName, sn)
        }
        if date != "" {
            hwdev.EepromUpdateDate(devName, date)
        }
        return
    }

    flag.Usage()
}

