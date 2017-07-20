package main

import (
    "fmt"
    "common/diagEngine"
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
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["test1"] = hdl1
    diagEngine.FuncMap["test2"] = hdl2

    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}

