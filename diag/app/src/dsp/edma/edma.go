package main

import (
    "flag"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "common/runCmd"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "EDMA"
)

func EdmaEdmaHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    cmdStr := "/data/nic_util/run_edma.sh"
    passSign := "EDMA TEST PASSED"
    failSign := "EDMA TEST FAILED"
    err := runCmd.Run(passSign, failSign, cmdStr)

    if err != errType.SUCCESS {
         dcli.Println("e", "EDMA Test Failed!")
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["EDMA"] = EdmaEdmaHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
