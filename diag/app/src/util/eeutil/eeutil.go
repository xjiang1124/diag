package main

import (
    //"fmt"
    "flag"
    "os"
    "strings"

    "common/cli"
    "common/errType"
    "config"
    "hardware/hwinfo"
    "hardware/i2cinfo"
    "device/eeprom"
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

func update(devName string, mac string, sn string) {
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

    err := eeprom.UpdateMac(devName, []byte(mac1))
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

}

func main() {
    devNamePtr := flag.String("dev",    "ALL",          "Device name")
    infoPtr    := flag.Bool("info",     false,          "Display device info")
    showPtr    := flag.Bool("show",     false,          "Display eeprom content")
    updatePtr  := flag.Bool("update",   false,          "Update eeprom")
    macPtr     := flag.String("mac",    "AABBCCDDEEFF", "MAC address")
    snPtr     := flag.String("sn",      "0123456789",   "Serial number")
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    mac := strings.ToUpper(*macPtr)
    sn := strings.ToUpper(*snPtr)

    if *infoPtr == true {
        dispInfo()
        return
    }

    if *showPtr == true {
        eeprom.DispEeprom(devName)
        return
    }

    if *updatePtr == true {
        update(devName, mac, sn)
        return
    }

    flag.Usage()
}

