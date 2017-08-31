package main

import (
    "flag"
    "fmt"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "common/misc"
    "config"

    //"unsafe"
    //"common/i2cCSW"
    //"common/i2c"
)

// #cgo CFLAGS: -I../../common/i2cc
// #cgo LDFLAGS: -li2c
// #include <stdlib.h>
// #include "../../common/i2cc/i2c.h"
import "C"


//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "PMBUS"
)

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

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.Success
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
    diagEngine.FuncMsgChan <- errType.Success
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
