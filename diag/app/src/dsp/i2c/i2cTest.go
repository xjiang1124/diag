package main

import (
    "os/exec"
    "regexp"
    "common/cli"
    "common/dcli"
    //"common/misc"
    "common/diagEngine"
    "common/errType"

    "device/fanctrl/adt7462"
    "device/powermodule/tps53659"
    "device/powermodule/tps53659a"
    "device/powermodule/ltc3888"
    "device/powermodule/tps549a20"
    "device/powermodule/tps544b25"
    "device/powermodule/tps544c20"
    "device/powermodule/tps53681"
    "device/powermodule/sn1701022"
    "device/rtc/pcf85263a"
    "device/tempsensor/adm1032"
    "device/tempsensor/tmp42123"
    "device/tempsensor/tmp451"
    "device/tempsensor/tmpadicom"
    "device/tempsensor/max6657"
    "device/tempsensor/lm75a"
    "device/psu/dps800"
    "device/fpga/taorfpga"
    "platform/taormina"

    "hardware/i2cinfo"

    //"time"
)


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
    if ((devID != tps53659a.DEVICE_ID) && (devID != tps53659.DEVICE_ID)) {
        dcli.Println("F", devName, " Invalid Device ID: expected", tps53659a.DEVICE_ID, "read", devID)
        return errType.FAIL
    }
    return
}

/*
    Read Device ID and compare with expected one
 */
func testLTC3888(devName string) (err int) {
    devID, err := ltc3888.ReadDeviceID(devName)

    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    }

    /* hack for now. Probably need to based on device rev */
    if (devID != ltc3888.DEVICE_ID) {
        dcli.Println("F", devName, " Invalid Device ID: expected", ltc3888.DEVICE_ID, "read", devID)
        return errType.FAIL
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

func testTmpADM1032(devName string) (err int) {
    mfgId, err := adm1032.ReadMfgId(devName)
    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    }
    if mfgId != adm1032.MFG_ID_V {
        dcli.Println("F", devName, " Invalid MFG ID: expected", adm1032.MFG_ID_V, "read", mfgId)
        return errType.FAIL
    }
    return
}

func testTmpAdiCom(devName string) (err int) {
    mfgId, err := tmpadicom.ReadMfgId(devName)
    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    }
    if (mfgId != max6657.MFG_ID_V) && (mfgId != max6657.MFG_ID_V_1) {
        dcli.Println("F", devName, " Invalid MFG ID: expected", tmpadicom.MFG_ID_V, "read", mfgId)
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
        if err != errType.SUCCESS {
            dcli.Println("e", "I2cI2cHdl: GetI2cInfo failed for device --> ", devName)
            diagEngine.FuncMsgChan <- err
            return
        }


        if cardType == "TAORMINA" {
            taorfpga.SetI2Cmux((i2cInfo.Bus - 1), uint32(i2cInfo.HubPort))
            if running, _ := taormina.Process_Is_Running("fand"); running == true {
                cli.Printf("i", "fand is running.. killing it\n")
                taormina.Process_Kill("fand")
            }
            if running, _ := taormina.Process_Is_Running("powerd"); running == true {
                cli.Printf("i", "powerd is running.. killing it\n")
                taormina.Process_Kill("powerd")
            }
        }
        dcli.Println("i", "Starting I2C test on", devName, " / Component", i2cInfo.Comp)
        switch i2cInfo.Comp {
            case "MACHXO3":
                if cardType == "TAORMINA" {
                    err = taormina.Elba_CPLD_I2C_Sanity_Test(devName)
                    if err != errType.SUCCESS {
                        ret = err
                    }
                }
            case "TMP451": 
                err = tmp451.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "ADT7462": 
                err = adt7462.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "DPS-800": 
                err = dps800.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "SN1701022": 
                err = sn1701022.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TPS53681": 
                err = tps53681.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TPS544C20": 
                err = tps544c20.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "LM75":
                err = lm75a.I2cTest(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TPS53659":
                err = tps53659.TestTps53659(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TPS53659A":
                err = testTps53659a(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "LTC3888":
                err = testLTC3888(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TPS549A20":
                err = tps549a20.TestTps549a20(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TMP422":
                err = testTmp422(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "ADM1032":
                err = testTmpADM1032(devName)
                if err != errType.SUCCESS {
                    ret = err
                }
            case "TMPADICOM":
                err = testTmpAdiCom(devName)
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
                if cardType == "TAORMINA" {
                    err = taormina.TestTaorFruI2C(devName)
                } else { 
                    err = testFru(devName, i2cInfo.Bus, i2cInfo.DevAddr)
                } 
                if err != errType.SUCCESS {
                    ret = err
                }
            default:
                {
                    dcli.Println("f", "Unsupported device: ", devName)
                    ret = errType.INVALID_PARAM
                }
        } //end switch
    }  //end for loop

    if cardType == "TAORMINA" {
        if ret == errType.SUCCESS {
            dcli.Printf("i","I2C I2C TEST PASSED\n")
        } else {
            dcli.Printf("e","I2C I2C TEST FAILED\n")
        }
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    if (diagEngine.FuncMsgChan == nil) {
        cli.Printf("i", "Diagengine channel is nil.  Called from CLI\n");
    } else {
        diagEngine.FuncMsgChan <- ret
    }
    return
}
