//ARM64 BUILD.  DO NOT MESS WITH THE LINE BELOW


// +build !amd64

//CODE AND COMMENTS BELOW THIS

package main

import (
    "flag"
    "fmt"
    "os"

    "cardinfo"
    "common/dcli"
    "common/diagEngine"
    "common/errType"
    "common/spi"

    "device/qsfp"

    "hardware/hwinfo"
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
    var regData uint32
    var data byte
    var cardType string
    var ctrlType string
    var err int

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    if  hwinfo.QsfpTbl == nil {
        dcli.Println("f", "Empty device table 1")
        ret = errType.INVALID_PARAM
        diagEngine.FuncMsgChan <- ret
        return
    }

    cardType = os.Getenv("CARD_TYPE")
    err, ctrlType = cardinfo.GetCtrlType(cardType)
    if err != errType.SUCCESS { 
        diagEngine.FuncMsgChan <- err
        return
    }

    for _, qsfpInfo := range hwinfo.QsfpTbl {
        devName := qsfpInfo.DevName
        i2cInfo, err := i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
             ret =  err
             break
        }
        dcli.Println("i", "Starting test on", devName)

        if ctrlType != "FPGA" {
            // Check present bits
            regAddr := qsfpInfo.PrstReg
            bitPos := qsfpInfo.PrstBit
            spi.CpldRead(uint32(regAddr), &regData)
            data = byte(regData)
            value := fmt.Sprintf("0x%02x", regData)
            dcli.Println("i", "CPLD QSFP Present Register Value =", value)
            value = fmt.Sprintf("0x%02x", data)
            dcli.Println("i", "CPLD QSFP Present Register Byte Value =", value)
            dcli.Println("i", "CPLD QSFP bitPos = ", bitPos)

            prstSts := data & (1<<byte(bitPos))
            if prstSts != 0 {
                dcli.Println("i", qsfpInfo.DevName, "Present")
            } else {
                dcli.Println("i", qsfpInfo.DevName, "Not Present")
                ret = errType.FAIL
                break
            }
        }

        switch i2cInfo.Comp {
        case "QSFP":
            err = testQsfp(devName)
            if err != errType.SUCCESS {
                ret = err
                break
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

