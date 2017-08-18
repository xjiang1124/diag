package main

import (
    "config"
    "flag"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "QSFP"
)

func QsfpI2CHdl(argList []string) int {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Int("mask", 0x3, "Devices bit mask")

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
    return errType.Success
}

func QsfpLaserenHdl(argList []string) int {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    instPtr := fs.Int("inst", 0, "Devices bit mask")

    err := fs.Parse(argList)
    if err != nil {
        dcli.Println("f", "Parse failed", err)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("t", "inst", *instPtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.Success
    return errType.Success
}
func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["I2C"] = QsfpI2CHdl
    diagEngine.FuncMap["laseren"] = QsfpLaserenHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
