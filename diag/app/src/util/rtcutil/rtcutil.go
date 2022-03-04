package main

import (
    "flag"
    "strings"

    "common/cli"
    "common/errType"
    "common/misc"
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
    devNamePtr := flag.String("dev",  "RTC",    "Device name")
    //------------------------
    yearPtr  := flag.Int("y",   0, "Year")
    monthPtr := flag.Int("m",   0, "Month")
    dayPtr   := flag.Int("d",   0, "Day")
    hourPtr  := flag.Int("h",   0, "Hour")
    minPtr   := flag.Int("min", 0, "Minute")
    secPtr   := flag.Int("s",   0, "Second")
    //------------------------
    dispPtr  := flag.Bool("disp",  false, "Display current time")
    setPtr   := flag.Bool("set",   false, "Set time")
    testPtr  := flag.Bool("test",  false, "Test RTC")
    smbusPtr := flag.Bool("smbus", false, "Verify RTC raw data on SMBUS")
    i2cPtr   := flag.Bool("i2c",   false, "Verify RTC raw data on I2C")
    dumpPtr  := flag.Bool("dump", false, "Dump RTC registers")
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
    err     := 0

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

    if *dumpPtr == true {
        pcf85263a.DumpReg(devName)
        return
    }

    if *smbusPtr == true {
        year, month, day, hour, min, sec, err = pcf85263a.ReadRaw_smbus(devName)
        if err != errType.SUCCESS {
            cli.Println("e", "failed to read RTC data on smbus")
            return
        }
        cli.Printf("i", "RTC raw data on smbus: %d-%d-%d(y-m-d) %d:%d:%d(h:m:s)\n", year, month, day, hour, min, sec)
        return
    }

    if *i2cPtr == true {
        year, month, day, hour, min, sec, err = pcf85263a.ReadRaw_i2c(devName)
        if err != errType.SUCCESS {
            cli.Println("e", "failed to read RTC data on I2C")
            return
        }
        cli.Printf("i", "RTC raw data on I2C: %d-%d-%d(y-m-d) %d:%d:%d(h:m:s)\n", year, month, day, hour, min, sec)
        return
    }

    if *testPtr == true {
        test_time := 5
        err1 := 0
//        cli.Printf("i", "RTC test: 2nd reading %d seconds after 1st reading, and compare\n", test_time)
        year, month, day, hour, min, sec, err1 = pcf85263a.ReadTime(devName)
        if err1 != errType.SUCCESS {
            cli.Println("e", "failed to read RTC data")
            return
        }
        cli.Printf("i", "RTC 1st reading: %02d/%02d/%02d(m/d/n) %02d:%02d:%02d(h:m:s)\n", month, day, year, hour, min, sec)

        misc.SleepInSec(test_time)
        year2, month2, day2, hour2, min2, sec2, err2 := pcf85263a.ReadTime(devName)
        if err2 != errType.SUCCESS {
            cli.Println("e", "failed to read RTC data")
            return
        }
        cli.Printf("i", "RTC 2nd reading: %02d/%02d/%02d(m/d/n) %02d:%02d:%02d(h:m:s)\n", month2, day2, year2, hour2, min2, sec2)

        if ((year2 == year) && (month2 == month) && (day2 == day) && ((int32(hour2) * 3600 + int32(min2) * 60 + int32(sec2) - 5) == (int32(hour) * 3600 + int32(min) * 60 + int32(sec)))) {
            cli.Printf("i", "RTC Test on %s Passed.\n", devName)
        } else {
            cli.Printf("i", "RTC Test on %s Failed!!!\n", devName)
        }

        return
    }

    myUsage()
}

