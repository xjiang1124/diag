package main

import (

    "config"
    "flag"
    "common/diagEngine"
    "common/dcli"
    //"common/errType"
    "platform/taormina"
    "device/bcm/td3"
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



func SwitchSnakeHdl(argList []string) {
    var err int = 0
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Uint64("mask", 255, "TD3 Link Mask to Elba's.  Used to mask off Elba Links")
    durationPtr := fs.Int("duration", 300, "Test Duration in seconds")
    loopbackPtr := fs.String("loopback", "ext", "Loopback Level, phy or ext")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "mask", *maskPtr, "duration", *durationPtr, "loopback", *loopbackPtr)


    mask:=*maskPtr 
    duration:=*durationPtr
    loopback:=*loopbackPtr
    
    err = td3.Snake_All_Ports_Forward_Next_Port(uint32(mask), uint32(duration), loopback)

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
    diagEngine.FuncMap["SNAKE"] = SwitchSnakeHdl

    

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
