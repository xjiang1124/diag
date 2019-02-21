package main

import (
    "flag"

    "common/dcli"
    "common/diagEngine"
    "common/errType"
    "device/sfp"
    "hardware/i2cinfo"
)

/*
    Read Device ID and compare with expected one
 */
func testSfp(devName string) (err int) {
    devID, err := sfp.ReadId(devName)

    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    }

    if devID != sfp.ID_SFPP {
        dcli.Println("F", devName, " Invalid Device ID: expected", sfp.ID_SFPP, "read", devID)
        return errType.FAIL
    }
    return
}

func SfpI2CHdl(argList []string) {
    var ret int
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }


    for _, devName := range(sfpTestList) {
        i2cInfo, err := i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
             ret =  err
             break
        }
        dcli.Println("i", "Starting testing", devName)

        switch i2cInfo.Comp {
        case "SFP":
            err = testSfp(devName)
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

