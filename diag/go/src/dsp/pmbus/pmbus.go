package main

import (
    "fmt"
    "flag"
    "common/diagEngine"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "PMBUS"
)

func TPmbusPmbusHdl(argList []string) int {
    fmt.Println("handle1", argList)
    return 0
}

func TPmbusIntrHdl(argList []string) int {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Int("mask", 0xFF, "Devices bit mask")

    err := fs.Parse(argList)
    if err != nil {
        fmt.Println("Parse failed", err)
    }
    fmt.Println("mask:", *maskPtr)
    return 0
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["PMBUS"] = TPmbusPmbusHdl
    diagEngine.FuncMap["INTR"] = TPmbusIntrHdl

    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}

