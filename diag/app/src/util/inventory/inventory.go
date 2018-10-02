package main

import (
    "fmt"
    "flag"
    "os"
    "strconv"
    "strings"

    "common/cli"
    "common/errType"
    "device/cpld/naples100Cpld"
    "device/cpld/naplesMtpCpld"
    "hardware/i2cinfo"
    "hardware/hwdev"
)

func init() {
}

func uutPresent(uutName string) (data byte, present bool) {
    devName := "CPLD"
    addr := uint64(naples100Cpld.REG_ID)

    cli.DisableVerbose()
    data, err := hwdev.NaplesCpldRd(devName, addr, uutName)
    if err != errType.SUCCESS {
        present = false
    } else {
        present = true
    }
    cli.EnableVerbose()

    return
}

func present() (err int) {
    var presentStr string

    maxUut := 10
    prsntNoneStr := "UUT_NONE"
    for i := 1; i <= maxUut; i++ {
        uutName := "UUT_"+strconv.Itoa(i)
        data, present := uutPresent(uutName)

        if present == true {
            switch data {
            case naples100Cpld.ID:
                presentStr = "NAPLES100"
            case naplesMtpCpld.ID:
                presentStr = "NAPLES_MTP"
            default:
                presentStr = "Unknown"
            }
        } else {
            presentStr = prsntNoneStr
        }
        cli.Printf("i", "UUT_%-15d     %s\n", i, presentStr)
    }
    return
}


func sysDetect() (err int) {
    var presentStr string
    var fmtStr string = "export UUT_%d=%s\n"

    file, err1 := os.Create("board_env.txt")
    if err1 != nil {
        cli.Println("e", "Cannot create file", err)
    }
    defer file.Close()

    maxUut := 10
    prsntNoneStr := "UUT_NONE"
    for i := 1; i <= maxUut; i++ {
        uutName := "UUT_"+strconv.Itoa(i)
        data, present := uutPresent(uutName)

        if present == true {
            switch data {
            case naples100Cpld.ID:
                presentStr = "NAPLES100"
            case naplesMtpCpld.ID:
                presentStr = "NAPLES_MTP"
            default:
                presentStr = "Unknown"
            }
        } else {
            presentStr = prsntNoneStr
        }
        fmt.Printf(fmtStr, i, presentStr)
    }
    return
}

func myUsage() {
    flag.PrintDefaults()
    //i2cinfo.DispI2cInfoAll()
}

func main() {
    flag.Usage = myUsage

    infoPtr     := flag.Bool(  "info", false, "Show I2C info table")
    uutPtr      := flag.String("uut",  "UUT_NONE", "Target UUT")
    presentPtr  := flag.Bool("present", false, "Show UUT present status")
    envPtr  := flag.Bool("env", false, "Detect/set environment")
    flag.Parse()

    //devName := strings.ToUpper(*devNamePtr)
    uut := strings.ToUpper(*uutPtr)

    if *infoPtr == true {
        if uut != "UUT_NONE" {
            i2cinfo.SwitchI2cTbl(uut)
        }
        i2cinfo.DispI2cInfoAll()
        return
    }

    if *presentPtr == true {
        present()
        return
    }

    if *envPtr == true {
        sysDetect()
        return
    }

    myUsage()
}

