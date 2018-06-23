package main

import (
    "flag"
    "strings"

    //"common/cli"
    //"common/errType"
    "device/rtc/pcf85263a"

    "hardware/i2cinfo"
)

func init() {
}

func myUsage() {
    flag.PrintDefaults()
    //i2cinfo.DispI2cInfoAll()
}

func main() {
    flag.Usage = myUsage
    //------------------------
    infoPtr    := flag.Bool(  "info", false, "Show I2C info table")
    devNamePtr := flag.String("dev",  "",    "Device name")
    //------------------------
    yearPtr  := flag.Int("y",   0, "Year")
    monthPtr := flag.Int("m",   0, "Month")
    dayPtr   := flag.Int("d",   0, "Day")
    hourPtr  := flag.Int("h",   0, "Hour")
    minPtr   := flag.Int("min", 0, "Minute")
    secPtr   := flag.Int("s",   0, "Second")
    //------------------------
    dispPtr  := flag.Bool("disp", false, "Display current time")
    setPtr   := flag.Bool("set",  false, "Set time")
    //------------------------
    uutPtr   := flag.String("uut",  "UUT_NONE", "Target UUT")
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    year    := byte(*yearPtr)
    month   := byte(*monthPtr)
    day     := byte(*dayPtr)
    hour    := byte(*hourPtr)
    min     := byte(*minPtr)
    sec     := byte(*secPtr)
    uut     := strings.ToUpper(*uutPtr)

    if uut != "UUT_NONE" {
        i2cinfo.SwitchI2cTbl(uut)
    }

    if *infoPtr == true {
        i2cinfo.DispI2cInfoAll()
        return
    }

    if *dispPtr == true {
        pcf85263a.DispTime(devName)
        return
    }

    if *setPtr == true {
        pcf85263a.SetTime(devName, year, month, day, hour, min, sec)
        return
    }

    myUsage()
}

