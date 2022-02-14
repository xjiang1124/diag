package main

import (
    "flag"

    "common/diagEngine"
    "common/dcli"
    //"common/errType"
    "config"

    "device/bcm/td3"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "BCM"
)

func BcmPrbsExtHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    durationPtr := fs.Int("duration", 30, "test time")
    polyPtr := fs.String("poly", "prbs58", "PRBS polynomial")

    duration := *durationPtr
    poly := *polyPtr
    
    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "duration", *durationPtr, "poly", *polyPtr)

    err := td3.Prbs(duration, poly)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["PRBSEXT"] = BcmPrbsExtHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
