package main

import (
    "flag"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "common/misc"
    "device/rtc/pcf85263a"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "RTC"
)

func RtcI2CHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errE := fs.Parse(argList)
    if errE != nil {
        dcli.Println("e", "Parse failed", errE)
        diagEngine.FuncMsgChan <- errType.FAIL
    }

    _, _, _, _, _, secondPre, err := pcf85263a.ReadTime("RTC")
    if err != errType.SUCCESS {
        diagEngine.FuncMsgChan <- errType.FAIL
    }

    misc.SleepInSec(3)

    _, _, _, _, _, secondPost, err := pcf85263a.ReadTime("RTC")
    if err != errType.SUCCESS {
        diagEngine.FuncMsgChan <- errType.FAIL
    }

    // Turn around
    if secondPost < secondPre {
        secondPost = secondPost + 60
    }

    diff := secondPost - secondPre
    if (diff > 2 && diff < 4) {
        diagEngine.FuncMsgChan <- errType.SUCCESS
    } else {
        dcli.Println("e", "time difference is", diff, ";expected: 3")
        diagEngine.FuncMsgChan <- errType.FAIL
    }
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["I2C"] = RtcI2CHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
