package main

import (
    "flag"

    "common/diagEngine"
    "common/dcli"
    //"common/errType"
    "config"

    "platform/taormina"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "SWITCH"
)

func SwitchInventoryHdl(argList []string) {
    var err int = 0

    dcli.Println("i", "Inventory Test")

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}


func SwitchPresentHdl(argList []string) {
    var err int = 0

    err = taormina.Presence_Test()

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}


func SwitchFanrpmHdl(argList []string) {
    var err int = 0
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    tollerancePtr := fs.Int("tollerance", 10, "rpm tollerance")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "tollerance", *tollerancePtr)

    tollerance := *tollerancePtr

    err = taormina.Fan_RPM_test(tollerance)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)

    diagEngine.FuncMap["INVENTORY"] = SwitchInventoryHdl
    diagEngine.FuncMap["PRESENT"] = SwitchPresentHdl
    diagEngine.FuncMap["FANRPM"] = SwitchFanrpmHdl

    

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
