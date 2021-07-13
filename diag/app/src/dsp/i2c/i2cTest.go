package main

import (
    "os/exec"
    "regexp"

    "common/cli"
    "common/dcli"
    "common/diagEngine"
    "common/errType"

    "device/powermodule/tps53659"
    "device/powermodule/tps53659a"
    "device/powermodule/tps549a20"
    "device/powermodule/tps544b25"
    "device/rtc/pcf85263a"
    "device/tempsensor/tmp42123"
    "device/fpga/taorfpga"

    "hardware/i2cinfo"
)

/*
    Read Device ID and compare with expected one
 */
func testTps53659(devName string) (err int) {
    devID, err := tps53659.ReadDeviceID(devName)

    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    }

    /* hack for now. Probably need to based on device rev */
    if (devID != tps53659.DEVICE_ID) {
        dcli.Println("F", devName, " Invalid Device ID: expected", tps53659.DEVICE_ID, "read", devID)
        return errType.FAIL
    }
    return
}

/*
    Read Device ID and compare with expected one
 */
func testTps53659a(devName string) (err int) {
    devID, err := tps53659a.ReadDeviceID(devName)

    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    }

    /* hack for now. Probably need to based on device rev */
    if (devID != tps53659a.DEVICE_ID) {
        dcli.Println("F", devName, " Invalid Device ID: expected", tps53659.DEVICE_ID, "read", devID)
        return errType.FAIL
    }
    return
}

func testTps549a20(devName string) (err int) {
    _, err = tps549a20.ReadStatus(devName)
    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
    }
    return
}

func testTmp422(devName string) (err int) {
    mfgId, err := tmp42123.ReadMfgId(devName)
    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    }
    if mfgId != tmp42123.MFG_ID_V {
        dcli.Println("F", devName, " Invalid MFG ID: expected", tmp42123.MFG_ID_V, "read", mfgId)
        return errType.FAIL
    }
    return
}

func testPcf85263a(devName string) (err int) {
    err = pcf85263a.DispTime(devName)
    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
    }
    return
}

func testTps544b25(devName string) (err int) {
    _, err = tps544b25.ReadStatus(devName)
    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
    }
    return
}

func testFru(devName string, bus uint32, devAddr byte) (err int) {
    err = errType.FAIL
    out, errGo := exec.Command("/data/nic_util/eeutil", "-dev=fru", "-verify").Output()
    if errGo != nil {
        cli.Println("e", errGo)
        err = errType.FAIL
    }
    outStr := string(out)
    dcli.Println("i","------------\n")
    dcli.Println("i","%s\n", outStr)
    dcli.Println("i","------------\n")
    re :=regexp.MustCompile("FRU Checkum and Type/Length Checks Passed")
    match :=re.MatchString(outStr)
    if match == true {
        err = errType.SUCCESS
    } 
    return
}


func I2cI2cHdl(argList []string) {
    var ret int
    ret = errType.SUCCESS

    cardInfo := diagEngine.GetCardInfo()
    cardType := cardInfo.CardType
    if cardType == "TAORMINA" {
        for _, i2cEntry := range(i2cinfo.CurI2cTbl) {
            if (i2cEntry.Flag & i2cinfo.I2C_TEST_ENABLE) == i2cinfo.I2C_TEST_ENABLE {
                i2cTestList = append(i2cTestList, i2cEntry.Name)
            }
        }
    }
    if len(i2cTestList) == 0 {
        dcli.Println("f", "Variable i2cTestList is empty.  No tests to run")
        ret = errType.INVALID_TEST    
    }

    for _, devName := range(i2cTestList) {
        i2cInfo, err := i2cinfo.GetI2cInfo(devName)

        if cardType == "TAORMINA" {
            taorfpga.SetI2Cmux((i2cInfo.Bus - 1), uint32(i2cInfo.HubPort))
        }
        //if err != errType.SUCCESS {
        //     diagEngine.FuncMsgChan <- err
        //     return
        //}
        dcli.Println("i", "Starting I2C test on", devName, " / Component", i2cInfo.Comp)
        switch i2cInfo.Comp {
        case "LM75":
            dcli.Println("i", "NEED TO ADD TEST")
            if err != errType.SUCCESS {
                ret = err
            }
        case "TPS53659":
            err = testTps53659(devName)
            if err != errType.SUCCESS {
                ret = err
            }
        case "TPS53659A":
            err = testTps53659a(devName)
            if err != errType.SUCCESS {
                ret = err
            }
        case "TPS549A20":
            err = testTps549a20(devName)
            if err != errType.SUCCESS {
                ret = err
            }
        case "TMP422":
            err = testTmp422(devName)
            if err != errType.SUCCESS {
                ret = err
            }
        case "PCF85263A":
            err = testPcf85263a(devName)
            if err != errType.SUCCESS {
                ret = err
            }
        case "TPS544B25":
            err = testTps544b25(devName)
            if err != errType.SUCCESS {
                ret = err
            }
        case "AT24C02C":
            err = testFru(devName, i2cInfo.Bus, i2cInfo.DevAddr)
            if err != errType.SUCCESS {
                ret = err
            }

        default:
            dcli.Println("f", "Unsupported device: ", devName)
            ret = errType.INVALID_PARAM
        }
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- ret
    return
}
