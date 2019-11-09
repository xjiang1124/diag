package main

import (
    "flag"
    "strconv"

    "common/diagEngine"
    "common/dcli"
    //"common/errType"
    "config"
    "device/emmc"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "EMMC"
)

func EmmcEmmcHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    fileSizePtr := fs.Int("filesize", 1, "Test eMMC device")
    countPtr := fs.Int("count", 10, "Test count")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    err := emmc.EmmcTest(strconv.Itoa(*fileSizePtr), *countPtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["EMMC"] = EmmcEmmcHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
