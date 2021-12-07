package main

import (

    "config"
    "flag"
    "common/diagEngine"
    "common/cli"
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

    err = taormina.ShowInventory()

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
    
    err = td3.Snake_Line_Rate(uint32(mask), uint32(duration), loopback, 0, 0)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}


func SwitchElba_Arm_MemoryHdl(argList []string) {
    var err int = 0
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    testtimePtr := fs.Int("testtime", 300, "Test timeout setting")
    maskPtr := fs.Int("mask", 3, "Elba test Mask   0x1 elba0    0x2 elba1   0x3 Both Elbas")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "testtime", *testtimePtr, "mask", *maskPtr)

    mask:=*maskPtr 
    duration:=*testtimePtr

    dcli.Println("i", "START TEST")
    err = taormina.ElbaMemoryTest(uint32(mask), uint32(duration), 0)
    dcli.Printf("i", "END TEST err=%d", err)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}


func SwitchElba_RtcHdl(argList []string) {
    var err int = 0
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Int("mask", 3, "Elba test Mask   0x1 elba0    0x2 elba1   0x3 Both Elbas")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    //dcli.Println("i", "testtime", *testtimePtr, "mask", *maskPtr)

     mask:=*maskPtr 

    dcli.Println("i", "START TEST")
    err = taormina.ElbaRTCtest(uint32(mask), 0)
    dcli.Printf("i", "END TEST err=%d", err)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}


func SwitchFgpa_StrappingHdl(argList []string) {
    var err int = 0
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    expectedvaluePtr := fs.Int("expectedvalue", 2, "Expected Resistor Strapping Value")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "expectedvalue", *expectedvaluePtr)

    expectedvalue:=*expectedvaluePtr 
    err = taormina.FPGA_Strapping_Test(expectedvalue)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func SwitchVrm_FixHdl(argList []string) {
    var err int = 0
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    err = taormina.TD3_VRM_FIX("TDNT_PDVDD")
    cli.Printf("i", "\n")
    err |= taormina.ElbaVRMfix()

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
    diagEngine.FuncMap["ELBA_ARM_MEMORY"] = SwitchElba_Arm_MemoryHdl
    diagEngine.FuncMap["ELBA_RTC"] = SwitchElba_RtcHdl
    diagEngine.FuncMap["FPGA_STRAPPING"] = SwitchFgpa_StrappingHdl
    diagEngine.FuncMap["VRM_FIX"] = SwitchVrm_FixHdl


    

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
