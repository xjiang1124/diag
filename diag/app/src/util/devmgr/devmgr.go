package main

import (
    "fmt"
    "flag"
    //"os"
    "strings"

    "common/cli"
    "common/errType"
    //"config"
    "hardware/i2cinfo"
    "hardware/hwdev"
)

func init() {
    //procNameTemp := strings.Split(os.Args[0], "/")
    //procName := procNameTemp[len(procNameTemp)-1]
    //cli.Init("log_"+procName+".txt", config.OutputMode)
}

func myUsage() {
    flag.PrintDefaults()
    //i2cinfo.DispI2cInfoAll()
}

func main() {
    var err int
    flag.Usage = myUsage

    devNamePtr  := flag.String("dev",     "ALL", "Device name")
    statusPtr   := flag.Bool  ("status",  false, "Device status")
    infoPtr     := flag.Bool  ("info",    false, "Device info")
    listPtr     := flag.Bool  ("list",    false, "Device info")
    rvoutPtr    := flag.Bool  ("rvout",   false, "VRM - Read VOUT in mV")
    rioutPtr    := flag.Bool  ("riout",   false, "VRM - Read IOUT in mA")
    marginPtr   := flag.Bool  ("margin",  false, "VRM - Enable voltage marigining")
    margModePtr := flag.String("mgmode",  "PCT", "VRM - Vmargin mode: PCT - percentage based; MV: value (mv) based")
    pctPtr      := flag.Int   ("pct",     0x0,   "VRM - Margin percentage; FAN - Fan speed percentage")
    voutMvPtr   := flag.Uint64("vout",    8500,  "VRM - Margin in mv")
    vidPtr      := flag.Bool  ("vid",     false, "VRM - Find VID of given vout in mv")
    vbootPtr    := flag.Bool  ("vboot",   false, "VRM - Change vboot in mv")
    programPtr  := flag.Bool  ("program", false, "VRM - Program with specified file")
    verifyPtr   := flag.Bool  ("verify",  false, "VRM - Verify NVM content with specified file")
    filePtr     := flag.String("file",    "",    "VRM - /path/to/image.file")
    verbosePtr  := flag.Bool  ("verbose", false, "Verbose")
    speedPtr    := flag.Bool  ("speed",   false, "FAN - Set fan speed")
    faninitPtr  := flag.Bool  ("faninit", false, "FAN - Initialization")
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
    margMode:= strings.ToUpper(*margModePtr)

    if *listPtr == true {
        i2cinfo.SwitchI2cTbl(uut)
        i2cinfo.DispI2cInfoAll()
        return
    }

    if *statusPtr == true {
        hwdev.DispStatus(devName, uut)
        return
    }

    if *marginPtr == true {
        if margMode == "PCT" {
            err = hwdev.Margin(devName, pct, uut)
        } else if margMode == "MV" {
            err = hwdev.MarginByValue(devName, *voutMvPtr, uut)
        }
        if err != errType.SUCCESS {
            cli.Println("e", "Voltage margin failed!")
        } else {
            hwdev.DispStatus(devName, uut)
        }
        return
    }

    if *vidPtr == true {
        vid, err := hwdev.FindVid(devName, *voutMvPtr, uut)
        if err != errType.SUCCESS {
            cli.Printf("e", "Failed to find vid of %d(mv)\n!", *voutMvPtr)
        } else {
            cli.Printf("i", "%d(mv) vid is 0x%x\n", *voutMvPtr, vid)
        }
        return
    }

    if *vbootPtr == true {
        err = hwdev.UpdateVboot(devName, *voutMvPtr, uut)
        if err != errType.SUCCESS {
            cli.Printf("e", "Failed to update vboot\n!", *voutMvPtr)
        } else {
            cli.Printf("i", "vboot is changed to %d(mv)\n", *voutMvPtr)
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
        hwdev.FanSpeedSet(devName, pct, mask)
        return
    }

    if *faninitPtr == true {
        hwdev.FanSetup(devName)
        return
    }

    if *rvoutPtr == true {
        vout, _ := hwdev.ReadVout(devName, uut)
        fmt.Println(vout)
        return
    }

    if *rioutPtr == true {
        iout, _ := hwdev.ReadIout(devName, uut)
        fmt.Println(iout)
        return
    }

    myUsage()
}

