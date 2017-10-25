package main

import (
    "flag"
    "fmt"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "hardware/hwvrm"
    "common/misc"
    "common/powermodule/tps53659"
    //"common/powermodule/tps549a20"
    "config"

    // Used by swig/C 
    //"unsafe"
    //"common/i2cCSW"
    //"common/i2c"
)

// #cgo CFLAGS: -I../../../../lib/
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
func testTps53659DevId() int {
    var tps tps53659.TPS53659
    for _, vrmName := range(hwvrm.Tps53659TblNaples) {
        vrm, _ := hwvrm.GetVrmInfoByName(vrmName)
        devID, _ := tps.ReadDeviceID(vrm.Name)
        if devID != tps53659.DEVICE_ID {
            dcli.Println("F", "Invalid Device ID: expected", tps53659.DEVICE_ID, "read", devID)
            return errType.FAIL
        }
    }
    return errType.SUCCESS
}


func PmbusPmbusHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Int("mask", 0xFF, "Devices bit mask")

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("f", "Parse failed", err)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("t", "mask", *maskPtr)

    errTest := testTps53659DevId()
    if errTest != errType.SUCCESS {
        diagEngine.FuncMsgChan <- errType.FAIL
        return
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

    //var readData[4] int 
    //rdp :=(*[4]int)(unsafe.Pointer(&readData[0]))
    ////defer C.free(unsafe.Pointer(rdp))
    //C.I2cRead(2, 3, rdp, 4)

    // go to C
    //var readData int
    //i2cCSW.Read(2, 3, &readData, 4)

    // go to C++ class
    //var readData[4] int
    //i2c := i2c.NewI2c()
    //i2c.Read(2, 3, &readData[0], 2)
    //dcli.Println("d", readData)
    //readData = [4]int{1,2,3,4}
    //i2c.Write(2, 3, &readData[0], 4)

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
