package main

import (
    "fmt"
    "common/dspInfra"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "PMBUS"
)

func hdl1(argList []string) uint32 {
    fmt.Println("handle1", argList)
    return 0
}

func hdl2(argList []string) uint32 {
    fmt.Println("handle2", argList)
    return 0
}

func main() {
    dspInfra.FuncMap = make(map[string]dspInfra.TestFn)
    dspInfra.FuncMap["test1"] = hdl1
    dspInfra.FuncMap["test2"] = hdl2

    dspInfra.CardInfoInit(dspName)
    dspInfra.DspInfraInit()
    dspInfra.DspInfraMainLoop()
}

