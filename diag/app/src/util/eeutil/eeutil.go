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
    macPtr     := flag.String("mac",    "AABBCCDDEEFF", "MAC address")
    snPtr      := flag.String("sn",     "0123456789",   "Serial number")
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    mac := strings.ToUpper(*macPtr)
    sn := strings.ToUpper(*snPtr)

    if *infoPtr == true {
        dispInfo()
        return
    }

    if *dispPtr == true {
        hwdev.EepromDisp(devName)
        return
    }

    if *updatePtr == true {
        hwdev.EepromUpdate(devName, mac, sn)
        return
    }

    flag.Usage()
}

