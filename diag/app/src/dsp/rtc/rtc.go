package main

import (
    "flag"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "common/i2c"
    "common/misc"
    "config"
    "hardware/pcf85263aReg"
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

    data, err := i2c.Read("RTC", pcf85263aReg.SECONDS, 1)
    if err != errType.SUCCESS {
        diagEngine.FuncMsgChan <- errType.FAIL
    }
    minutesPre := data[0] & 0x7F

    misc.SleepInSec(3)

    data, err = i2c.Read("RTC", pcf85263aReg.SECONDS, 1)
    if err != errType.SUCCESS {
        diagEngine.FuncMsgChan <- errType.FAIL
    }
    minutesPost := data[0] & 0x7F

    // Turn around
    if minutesPost < minutesPre {
        minutesPost = minutesPost + 60
    }

    diff := minutesPost - minutesPre
    if (diff > 2 && diff < 4) {
        diagEngine.FuncMsgChan <- errType.SUCCESS
    } else {
        dcli.Println("e", "time difference is", diff)
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
