package main

import (
    "flag"
    "os/exec"
    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "config"
    "bytes"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "ASIC"
)

func AsicPcie_PrbsHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    durationPtr := fs.Int("duration", 30, "test time")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "duration", *durationPtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func AsicEth_PrbsHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    durationPtr := fs.Int("duration", 30, "test time")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "duration", *durationPtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func AsicTrfHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", )

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func AsicL1_TestHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    slotPtr := fs.Uint64("slot", 63, "Test slot mask value")
    slotMask := *slotPtr

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }
    
    for i := 0; i < 10; i++ {
        if (slotMask >> uint(i) & 0x1) == 0 {
            break
        }
        cmd := exec.Command("tclsh", "test.tcl", string(i))
        var out bytes.Buffer
        cmd.Stdout = &out
        err := cmd.Run()
    	if err != nil {
    		dcli.Println("e", "L1 test failed on slot"+string(i+1))
    	}
    	dcli.Println("i", "in all caps: %q\n", out.String())
    }

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("i", "slot", *slotPtr)

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["PCIE_PRBS"] = AsicPcie_PrbsHdl
    diagEngine.FuncMap["ETH_PRBS"] = AsicEth_PrbsHdl
    diagEngine.FuncMap["TRF"] = AsicTrfHdl
    diagEngine.FuncMap["L1_TEST"] = AsicL1_TestHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
