package main

import (
    //"fmt"
    "flag"
    "os"
    "sort"
    "strings"

    "common/cli"
    "common/errType"
    "config"
    "hardware/i2cinfo"
    "hardware/hwinfo"
    "hardware/hwdev"
    "device/powermodule/tps53659"
    "device/powermodule/tps549a20"
    "device/fanctrl/adt7462"
)

func init() {
    procNameTemp := strings.Split(os.Args[0], "/")
    procName := procNameTemp[len(procNameTemp)-1]
    cli.Init("log_"+procName+".txt", config.OutputMode)
}

func devInfo(devName string, uut string) {
    for _, i2cInfo := range(i2cinfo.I2cTbl) {
        if devName != i2cInfo.Name {
            continue
        }
        if i2cInfo.Comp == "TPS53659" {
            tps53659.Info(devName)
            return
        }
    }
    cli.Println("e", "Unsupported device: ", devName)
}

func dispStatus(devName string) (err int){
    if devName == "ALL" {
        // golang range(map) sequence is random
        // Sorted output
        keys := make([]string, 0)
        for k, _ := range(hwinfo.DispStaList) {
            keys = append(keys, k)
        }
        sort.Strings(keys)
        for _, dev := range(keys) {
            dispFunc := hwinfo.DispStaList[dev]
            hwinfo.EnableHubChannelExclusive(dev)
            dispFunc(dev)
        }
    } else {
        hwinfo.EnableHubChannelExclusive(devName)
        dispFunc, ok := hwinfo.DispStaList[devName]
        if ok == false {
            cli.Println("f", "Invalde device: ", devName)
            err = errType.INVALID_PARAM
            return
        }
        dispFunc(devName)
    }
    return
}

func dispStatusUut(devName string, uutName string) (err int){
    if devName == "ALL" {
        cli.Println("e", "\"ALL\" does not support by UUT!")
        err = errType.INVALID_PARAM
        return
    }

    err = hwinfo.EnableHubChannelUut(uutName)
    if err != errType.SUCCESS {
        return err
    }

    hwinfo.SwitchHwInfo(uutName)
    i2cinfo.SwitchI2cTbl(uutName)
    dispFunc, ok := hwinfo.DispStaList[devName]
    if ok == false {
        cli.Println("f", "Invalde device: ", devName)
        err = errType.INVALID_PARAM
        return
    }
    dispFunc(devName)
    i2cinfo.SwitchI2cTbl("UUT_NONE")
    hwinfo.SwitchHwInfo("UUT_NONE")

    return
}

func margin(devName string, pct int) (err int){
    for _, i2cInfo := range(i2cinfo.I2cTbl) {
        if devName != i2cInfo.Name {
            continue
        }
        if i2cInfo.Comp == "TPS53659" {
            tps53659.SetVMargin(devName, pct)
            return
        } else if i2cInfo.Comp == "TPS549A20" {
           tps549a20.SetVMargin(devName, pct)
           return
        }
    }
    cli.Println("e", "Unsupported device: ", devName)
    err = errType.INVALID_PARAM
    return
}

func marginUut(devName string, pct int, uutName string) (err int) {
    err = hwinfo.EnableHubChannelUut(uutName)
    if err != errType.SUCCESS {
        return err
    }

    i2cinfo.SwitchI2cTbl(uutName)
    err = margin(devName, pct)
    i2cinfo.SwitchI2cTbl("UUT_NONE")
    return
}

func program (devName string, fileName string, verbose bool) (err int) {
    for _, i2cInfo := range(i2cinfo.CurI2cTbl) {
        if devName != i2cInfo.Name {
            continue
        }
        if i2cInfo.Comp == "TPS53659" {
            tps53659.ProgramVerifyNvm(devName, fileName, "PROGRAM", verbose)
            return
        }
    }
    cli.Println("e", "Unsupported device: ", devName)
    err = errType.INVALID_PARAM
    return
}

func programUut (devName string, fileName string, verbose bool, uutName string) (err int) {
    err = hwinfo.EnableHubChannelUut(uutName)
    if err != errType.SUCCESS {
        return err
    }

    i2cinfo.SwitchI2cTbl(uutName)
    err = program(devName, fileName, verbose)
    i2cinfo.SwitchI2cTbl("UUT_NONE")
    return
}

func verify (devName string, fileName string, verbose bool) (err int) {
    for _, i2cInfo := range(i2cinfo.CurI2cTbl) {
        if devName != i2cInfo.Name {
            continue
        }
        if i2cInfo.Comp == "TPS53659" {
            tps53659.ProgramVerifyNvm(devName, fileName, "VERIFY", verbose)
            return
        }
    }
    cli.Println("e", "Unsupported device: ", devName)
    err = errType.INVALID_PARAM
    return
}

func verifyUut (devName string, fileName string, verbose bool, uutName string) (err int) {
    err = hwinfo.EnableHubChannelUut(uutName)
    if err != errType.SUCCESS {
        return err
    }

    i2cinfo.SwitchI2cTbl(uutName)
    err = verify(devName, fileName, verbose)
    i2cinfo.SwitchI2cTbl("UUT_NONE")
    return
}

func fanSpeed(devName string, pct int, mask uint64) (err int) {
    var i uint64

    hwinfo.EnableHubChannelExclusive(devName)
    for _, i2cInfo := range(i2cinfo.I2cTbl) {
        if devName != i2cInfo.Name {
            continue
        }
        if i2cInfo.Comp == "ADT7462" {
            for i = 0; i < hwinfo.MAX_NUM_FAN; i++ {
                if (mask & (1 << i)) != 0 {
                    adt7462.SetFanSpeed(devName, uint64(i), uint64(pct))
                }
            }
            return
        }
    }
    cli.Println("e", "Unsupported device: ", devName)
    err = errType.INVALID_PARAM
    return
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
        devInfo(devName, uut)
        return
    }

    if *speedPtr == true {
        fanSpeed(devName, pct, mask)
        return
    }

    if *faninitPtr == true {
        hwinfo.EnableHubChannelExclusive(devName)
        adt7462.Setup(devName)
        return
    }

    myUsage()
}

