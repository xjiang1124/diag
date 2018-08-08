package main

import (
    "flag"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "common/misc"
    "config"
    "device/cpld/cpld"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "INTR"
)

func IntrEswHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // enable cpld int enable reg 0x3, bit4
    // clear on source sw global reg 0 bit0
    // toggle sw reset on cpld reg 1 bit0
    // read cpld int status reg 4 bit 4
    data, err := cpld.ReadReg(0x3)
    if err != 0 {
        dcli.Println("e", "CPLD write protect test failed")
        return
    }
    data |= 0x10
    err = cpld.WriteReg(0x3, data)
    if err != 0 {
        dcli.Println("e", "CPLD write protect test failed")
        return
    }
    
    _, err = cpld.ReadMdio(0x1B, 0x0)
    if err != 0 {
        dcli.Println("e", "CPLD write protect test failed")
        return
    }
    
    data, err = cpld.ReadReg(0x1)
    if err != 0 {
        dcli.Println("e", "CPLD write protect test failed")
        return
    }
    data |= 0x1
    err = cpld.WriteReg(0x1, data)
    if err != 0 {
        dcli.Println("e", "CPLD write protect test failed")
        return
    }
    misc.SleepInSec(1)
    data &= 0xFE
    err = cpld.WriteReg(0x1, data)
    if err != 0 {
        dcli.Println("e", "CPLD write protect test failed")
        return
    }
    misc.SleepInSec(1)
    
    data, err = cpld.ReadReg(0x4)
    if data & 0x10 == 0 || err != 0 {
        dcli.Println("e", "CPLD write protect test failed")
        return
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
    diagEngine.FuncMap["ESW"] = IntrEswHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
