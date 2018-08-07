package main

import (
    "flag"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "config"
)
// #cgo CFLAGS: -I../../../../include
// #cgo LDFLAGS: -lspi
// #include <stdlib.h>
// #include "cType.h"
// #include "../../../../lib/spi_userspace/spi.h"
import "C"
import "unsafe"

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "SPI"
)

func SpiIdHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    var retC C.int
    rd := [6]C.uchar{0, 0, 0, 0, 0, 0}
    retC = C.ReadId(&rd[0])
    if retC != 0 {
        dcli.Println("e", "Failed to read ID back")
    }

    data := C.GoBytes(unsafe.Pointer(&rd[0]), 6)
    dcli.Println("i", "Device id %s", data)

    diagEngine.FuncMsgChan <- errType.SUCCESS
    
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["ID"] = SpiIdHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
