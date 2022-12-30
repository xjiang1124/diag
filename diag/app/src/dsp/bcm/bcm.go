package main

import (
    "flag"

    "common/diagEngine"
    "common/dcli"
    //"common/errType"
    "config"

    "device/bcm/td3"
    "platform/taormina"
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

    err := taormina.Prbs(duration, poly, 0)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}


func BcmTd3DiagHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    err := td3.BCMShell_Test_Init() 
    if err != 0 {
        dcli.Println("e", "td3.BCMShell_Test_Init Failed with err = ", err)
        diagEngine.FuncMsgChan <- err
        return
    }
    err = td3.TD3_Run_Diags()

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}



func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["PRBSEXT"] = BcmPrbsExtHdl
    diagEngine.FuncMap["TD3DIAG"] = BcmTd3DiagHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
