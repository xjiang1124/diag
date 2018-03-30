package main

import (
    //"fmt"
    "flag"
    "os"
    "strings"

    "common/cli"
    "common/errType"
    "config"
    "hardware/i2cinfo"
    "hardware/hwdev"
)

func init() {
    procNameTemp := strings.Split(os.Args[0], "/")
    procName := procNameTemp[len(procNameTemp)-1]
    cli.Init("log_"+procName+".txt", config.OutputMode)
}

func myUsage() {
    flag.PrintDefaults()
    i2cinfo.DispI2cInfoAll()
}

func main() {
    flag.Usage = myUsage

    devNamePtr  := flag.String("dev",     "ALL", "Device name")
    statusPtr   := flag.Bool(  "status",  false, "Device status")
    infoPtr     := flag.Bool(  "info",    false, "Device info")
    marginPtr   := flag.Bool(  "margin",  false, "VRM - Enable voltage marigining")
    pctPtr      := flag.Int(   "pct",     0x0,   "VRM - Margin percentage; FAN - Fan speed percentage")
    programPtr  := flag.Bool(  "program", false, "VRM - Program with specified file")
    verifyPtr   := flag.Bool(  "verify",  false, "VRM - Verify NVM content with specified file")
    filePtr     := flag.String("file",    "",    "VRM - /path/to/image.file")
    verbosePtr  := flag.Bool(  "verbose", false, "Verbose")
    speedPtr    := flag.Bool(  "speed",   false, "FAN - Set fan speed")
    faninitPtr  := flag.Bool(  "faninit", false, "FAN - Initialization")
    maskPtr     := flag.Uint64("mask",    0x7,   "FAN - fan instance mask")
    uutPtr      := flag.String("uut",     "UUT_NONE", "UUT name, e.g. UUT_1")
    flag.Parse()

    //cli.Println("devNamePtr:", *devNamePtr, "statusPtr:", *statusPtr, "marginPtr:", *marginPtr, "pctPtr:", *pctPtr)
    //cli.Println("i", *readPtr, *writePtr, *sendPtr, *addrPtr, *dataPtr)
    devName := strings.ToUpper(*devNamePtr)
    pct     := *pctPtr
    verbose := *verbosePtr
    mask    := *maskPtr
    uut     := strings.ToUpper(*uutPtr)

    if *statusPtr == true {
        hwdev.DispStatus(devName, uut)
        return
    }

    if *marginPtr == true {
        err := hwdev.Margin(devName, pct, uut)
        if err != errType.SUCCESS {
            cli.Println("e", "Voltage margin failed!")
        } else {
            hwdev.DispStatus(devName, uut)
            cli.Println("i", "Voltage margin set at", pct, "percent")
        }
        return
    }

    if *programPtr == true {
        hwdev.Program(devName, *filePtr, verbose, uut)
        return
    }

    if *verifyPtr == true {
        hwdev.Verify(devName, *filePtr, verbose, uut)
        return
    }

    if *infoPtr == true {
        hwdev.DevInfo(devName, uut)
        return
    }

    if *speedPtr == true {
        hwdev.FanSpeed(devName, pct, mask)
        return
    }

    if *faninitPtr == true {
        hwdev.FanSetup(devName)
        return
    }

    myUsage()
}

