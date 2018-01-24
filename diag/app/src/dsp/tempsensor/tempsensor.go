package main

import (
    "flag"
    "fmt"

    "common/diagEngine"
    "common/dcli"
    "common/errType"
    "device/tempsensor/tmp422"
    "config"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "TEMPSENSOR"
)

func TempsensorDev_IdHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    id, err := tmp422.ReadMfgId("TEMP_SENSOR")
    if err != errType.SUCCESS {
        diagEngine.FuncMsgChan <- err
        return
    }

    if id != tmp422.MFG_ID_V {
        //dcli.Println("e", "Invalid MFG ID, expected:", tmp422.MFG_ID_V, "received:", id)
        fmt.Println("e", "Invalid MFG ID, expected:", tmp422.MFG_ID_V, "received:", id)
        diagEngine.FuncMsgChan <- errType.TEMPSENSOR_INVALID_ID
        return
    }
    dcli.Println("i", "Manufacture ID matches")

    id, err = tmp422.ReadDevId("TEMP_SENSOR")
    if err != errType.SUCCESS {
        diagEngine.FuncMsgChan <- err
        return
    }

    if id != tmp422.DEV_ID_V {
        dcli.Println("e", "Invalid DEV ID, expected:", tmp422.MFG_ID_V, "received:", id)
        diagEngine.FuncMsgChan <- errType.TEMPSENSOR_INVALID_ID
        return
    }
    dcli.Println("i", "Device ID matches")
    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- errType.SUCCESS
    return
}

func TempsensorTempHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    var err int
    var tempList = []string {"Local:", "Remote1", "Remote2"}
    for i:=0; i<tmp422.MAX_CHANNEL; i++ {
        integer, dec, err1 := tmp422.ReadTemp("TEMP_SENSOR", byte(i))
        if err != errType.SUCCESS {
            err = err1
        }
        temp := fmt.Sprintf("%d.%04d", integer, dec)
        dcli.Println("i", tempList[i], temp)
        if integer < tmp422.LIMIT_LOW || integer > tmp422.LIMIT_HIGH {
            dcli.Println("e", "Temperature over limit!")
            err = errType.TEMPSENSOR_OVER_LIMIT
        }
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["DEV_ID"] = TempsensorDev_IdHdl
    diagEngine.FuncMap["TEMP"] = TempsensorTempHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
