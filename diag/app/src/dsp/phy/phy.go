package main

import (
    "flag"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "PHY"
)

func PhyMdioHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Int("mask", 0x3, "Devices bit mask")

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("e", "Parse failed", err)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "mask", *maskPtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.Success
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["MDIO"] = PhyMdioHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
