package main

import (
    "common/dcli"
    "common/diagEngine"
    "common/errType"

    "device/powermodule/tps53659"
    "device/powermodule/tps549a20"
    "device/powermodule/tps544b25"
    "device/rtc/pcf85263a"
    "device/tempsensor/tmp42123"

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

    if devID != tps53659.DEVICE_ID {
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


func I2cI2cHdl(argList []string) {
    var ret int
    ret = errType.SUCCESS

    if len(i2cTestList) == 0 {
        dcli.Println("f", "Variable i2cTestList is empty.  No tests to run")
        ret = errType.INVALID_TEST    
    }

    for _, devName := range(i2cTestList) {
        i2cInfo, err := i2cinfo.GetI2cInfo(devName)
        //if err != errType.SUCCESS {
        //     diagEngine.FuncMsgChan <- err
        //     return
        //}
        dcli.Println("i", "Starting testing", devName, "as component", i2cInfo.Comp)
        switch i2cInfo.Comp {
        case "TPS53659":
            err = testTps53659(devName)
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
