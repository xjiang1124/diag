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
    "hardware/hwinfo"
    "device/powermodule/tps53659"
    "device/powermodule/tps549a20"
    "device/fanctrl/adt7462"
)

func init() {
    procNameTemp := strings.Split(os.Args[0], "/")
    procName := procNameTemp[len(procNameTemp)-1]
    cli.Init("log_"+procName+".txt", config.OutputMode)
}

func devInfo(devName string) {
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

func dispStatus(devName string) {
    if devName == "ALL" {
        for dev, dispFunc := range(hwinfo.DispStaList) {
            dispFunc(dev)
        }
    } else {
        dispFunc, ok := hwinfo.DispStaList[devName]
        if ok == false {
            cli.Println("f", "Invalde device: ", devName)
            return
        }
        dispFunc(devName)
    }
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

func program (devName string, fileName string, verbose bool) (err int) {
    for _, i2cInfo := range(i2cinfo.I2cTbl) {
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

func verify (devName string, fileName string, verbose bool) (err int) {
    for _, i2cInfo := range(i2cinfo.I2cTbl) {
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

func fanSpeed(devName string, pct int, mask uint64) (err int) {
    var i uint64
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

func main() {
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
    flag.Parse()

    //cli.Println("devNamePtr:", *devNamePtr, "statusPtr:", *statusPtr, "marginPtr:", *marginPtr, "pctPtr:", *pctPtr)
    //cli.Println("i", *readPtr, *writePtr, *sendPtr, *addrPtr, *dataPtr)
    devName := strings.ToUpper(*devNamePtr)
    pct     := *pctPtr
    verbose := *verbosePtr
    mask    := *maskPtr

    if *statusPtr == true {
        dispStatus(devName)
        return
    }

    if *marginPtr == true {
        err := margin(devName, pct)
        if err != errType.SUCCESS {
            cli.Println("e", "Voltage margin failed!")
        } else {
            dispStatus(devName)
            cli.Println("i", "Voltage margin set at", pct, "percent")
        }
        return
    }

    if *programPtr == true {
        program(devName, *filePtr, verbose)
        return
    }

    if *verifyPtr == true {
        verify(devName, *filePtr, verbose)
        return
    }

    if *infoPtr == true {
        devInfo(devName)
        return
    }

    if *speedPtr == true {
        fanSpeed(devName, pct, mask)
        return
    }

    if *faninitPtr == true {
        adt7462.Setup(devName)
        return
    }

}

