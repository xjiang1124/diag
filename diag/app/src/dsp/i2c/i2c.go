package main

import (
    "flag"
    "fmt"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "hardware/i2cinfo"
    "hardware/hwinfo"
    "common/misc"
    "device/powermodule/tps53659"
    "device/powermodule/tps549a20"
    "config"

    // Used by swig/C 
    //"unsafe"
    //"protocol/i2c"
)

// #cgo CFLAGS: -I../../../../lib/
// #cgo LDFLAGS: -li2c -li2csim
// #include <stdlib.h>
// #include "../../../../lib/i2c/i2c.h"
import "C"


//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "PMBUS"
)

// #ccccgo LDFLAGS: /home/xguo2//workspace/psdiag/diag/app/pkg/linux_arm64/common/libi2c.a
/*
    Read Device ID and compare with expected one
 */
func testTps53659DevId(devName string) (err int) {
    devID, err := tps53659.ReadDeviceID(devName)
    if devID != tps53659.DEVICE_ID {
        dcli.Println("F", devName, " Invalid Device ID: expected", tps53659.DEVICE_ID, "read", devID)
        return errType.FAIL
    }
    return errType.SUCCESS
}

func testTps549a20(devName string) (err int) {
    _, err = tps549a20.ReadStatus(devName)
    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
    }
    return
}

func PmbusPmbusHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Int("mask", 0xFF, "Devices bit mask")

    errgo := fs.Parse(argList)
    if errgo != nil {
        dcli.Println("f", "Parse failed", errgo)
        diagEngine.FuncMsgChan <- errType.FAIL
        return
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("t", "mask", *maskPtr)

    for _, devName := range(hwinfo.PmbusTestList) {
        i2cInfo, err := i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
             diagEngine.FuncMsgChan <- err
             return
        }
        if i2cInfo.Comp == "TPS53659" {
            err = testTps53659DevId(devName)
            if err != errType.SUCCESS {
                 diagEngine.FuncMsgChan <- err
                 return
            }
        } else if i2cInfo.Comp == "TPS549A20" {
            err = testTps549a20(devName)
            if err != errType.SUCCESS {
                 diagEngine.FuncMsgChan <- err
                 return
            }
        } else {
            dcli.Println("f", "Unsupported device: ", devName)
            diagEngine.FuncMsgChan <- errType.INVALID_PARAM
            return
        }
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func PmbusIntrHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Int("mask", 0xFF, "Devices bit mask")

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("f", "Parse failed", err)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("t", "mask", *maskPtr)

    fmt.Println("I2C fmt")
    dcli.Println("d", "I2C!!!")

    //var readData int 
    //rd := C.int(readData)
    rd := [4]C.int {1, 2, 3, 4}
    C.I2cRead(2, 3, &rd[0], 4)
    dcli.Println("d", rd)
    C.I2cWrite(2, 3, &rd[0], 4)

    var readData [4]int
    readData[0] = int(rd[0])
    dcli.Println("d", readData)

    misc.SleepInSec(1)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}
func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["PMBUS"] = PmbusPmbusHdl
    diagEngine.FuncMap["INTR"] = PmbusIntrHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
