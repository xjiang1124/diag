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
    dspName = "PCIE_H"
)

func Pcie_HPcieHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Int("mask", 0xFFFF, "NIC board bit mask, default up to 16 boards")

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("e", "Parse failed", err)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "mask", *maskPtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["PCIE"] = Pcie_HPcieHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
