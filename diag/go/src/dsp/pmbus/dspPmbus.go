package main

import (
    "flag"
    "common/diagEngine"
    "common/dcli"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "PMBUS"
)

func PmbusPmbusHdl(argList []string) int {
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
    diagEngine.FuncMsgChan <- 0
    return 0
}

func PmbusIntrHdl(argList []string) int {
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
    diagEngine.FuncMsgChan <- 0
    return 0
}
func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["PMBUS"] = PmbusPmbusHdl
    diagEngine.FuncMap["INTR"] = PmbusIntrHdl

    dcli.Init("log_"+dspName+".txt")
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
