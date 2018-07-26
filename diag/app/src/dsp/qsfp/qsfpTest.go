package main

import (
    "flag"

    "common/dcli"
    "common/diagEngine"
    "common/errType"
    "device/qsfp"
    "hardware/i2cinfo"
)

/*
    Read Device ID and compare with expected one
 */
func testQsfp(devName string) (err int) {
    devID, err := qsfp.ReadId(devName)

    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    }

    if devID != qsfp.ID_QSFP28 {
        dcli.Println("F", devName, " Invalid Device ID: expected", qsfp.ID_QSFP28, "read", devID)
        return errType.FAIL
    }
    return
}

func QsfpI2CHdl(argList []string) {
    var ret int
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    for _, devName := range(qsfpTestList) {
        i2cInfo, err := i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
             ret =  err
             break
        }
        dcli.Println("i", "Starting testing", devName)

        switch i2cInfo.Comp {
        case "QSFP":
            err = testQsfp(devName)
            if err != errType.SUCCESS {
                ret = err
            }

        default:
            dcli.Println("f", "Unsupported device:", devName, "Comp:", i2cInfo.Comp )
            ret = errType.INVALID_PARAM
        }
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- ret
    return
}

