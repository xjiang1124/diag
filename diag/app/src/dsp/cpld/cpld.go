package main

import (
    "flag"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "config"
    "device/cpld/cpld"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName 	= "CPLD"
    phyId		= 0x141
    devAddr		= 0xD
    regOffset	= 0x2
)

func CpldMdioHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }
    
    data, err := cpld.ReadMdio(devAddr, regOffset)
    if data != phyId || err != 0 {
        dcli.Println("e", "MDIO test failed")
    } else {
        dcli.Println("i", "MDIO test passed")
    }
    
    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func CpldIntHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }
    
    // Write test bits
    cpld.WriteReg(0, 1)
    
    // Read interrupt reg
    data, err := cpld.ReadReg(0)
    
    if (data != 1) || (err != 0) {
        dcli.Println("e", "CPLD interrupt test failed")
    } else {
        dcli.Println("i", "CPLD interrupt test passed")
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func CpldGpioHdl(argList []string) {
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

func CpldWpHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // Read Capri cntl reg0 SD_CS_GPIO_SEL
    data, err := cpld.ReadReg(0x10)
    if (data & 0x8 == 0) || (err != 0) {
        dcli.Println("e", "CPLD write protect test failed")
        return
    } else {
        dcli.Println("i", "CPLD write protect test passed")
    }
    
    // Read Capri cntl reg2
    data, err = cpld.ReadReg(0x12)
    
    if (data & 0xc != 0) || (err != 0) {
        dcli.Println("e", "CPLD write protect test failed")
    } else {
        dcli.Println("i", "CPLD write protect test passed")
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["MDIO"] = CpldMdioHdl
    diagEngine.FuncMap["INT"] = CpldIntHdl
    diagEngine.FuncMap["GPIO"] = CpldGpioHdl
    diagEngine.FuncMap["WP"] = CpldWpHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
