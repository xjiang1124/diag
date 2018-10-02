package main

import (
    "fmt"
    "flag"
    "os"
    "strconv"

    "common/cli"
    "common/errType"
    "device/cpld/naples100Cpld"
    "device/cpld/naplesMtpCpld"
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
    var fmtStr string = "export UUT_%d=\"%s\"\n"

    file, err1 := os.Create("/home/diag/diag/log/board_env.txt")
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
        fmt.Fprintf(file, fmtStr, i, presentStr)
    }
    return
}

func myUsage() {
    flag.PrintDefaults()
    //i2cinfo.DispI2cInfoAll()
}

func main() {
    flag.Usage = myUsage

    presentPtr  := flag.Bool("present", false, "Show UUT present status")
    envPtr  := flag.Bool("env", false, "Detect/set environment")
    flag.Parse()

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

