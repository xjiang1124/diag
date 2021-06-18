//AMD64 BUILD.  DO NOT MESS WITH THE LINE BELOW


// +build amd64

//CODE AND COMMENTS BELOW THIS

package main

import (
    "flag"

    "common/dcli"
    "common/diagEngine"
    "common/errType"
    //"common/spi"

    "device/qsfp"
    "device/fpga/taorfpga"
    "hardware/hwinfo"
    "hardware/i2cinfo"
)

/*
    Read Device ID and compare with expected one
 */
func testQsfp(devName string) (sn string, err int) {
    devID, err := qsfp.ReadId(devName)

    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    }

    if devID != qsfp.ID_QSFP28 {
        dcli.Println("F", devName, " Invalid Device ID: expected", qsfp.ID_QSFP28, "read", devID)
        err = errType.FAIL
        return 
    }

    err = qsfp.VerifyCheckSums(devName)
    if err != errType.SUCCESS {
        return
    }
    _, _, sn, _, err = qsfp.PrintQSFPvendorData(devName)
    if err != errType.SUCCESS {
        return
    }

    return
}

func QsfpI2CHdl(argList []string) {
    var ret int = 0
    var data uint32
    qsfpSNmap := make(map[string]byte)

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
        diagEngine.FuncMsgChan <- errType.INVALID_PARAM
        return
    }

    if  hwinfo.QsfpTbl == nil {
        dcli.Println("f", "Empty device table 1")
        diagEngine.FuncMsgChan <- errType.INVALID_PARAM
        return
    }


    // Check for SFP Present
    for _, qsfpInfo := range hwinfo.QsfpTbl {
        // Check present bits
        regAddr := qsfpInfo.PrstReg
        bitPos := qsfpInfo.PrstBit
        data, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, uint64(regAddr))  //return value uses golang err (not diag err)
        prstSts := data & (1<<byte(bitPos))
        if prstSts == 0 {
            dcli.Println("i", qsfpInfo.DevName, "Present")
        } else {
            dcli.Println("e", qsfpInfo.DevName, "QSFP Not Present!")
            ret = errType.FAIL
            break
        }
    }
    
    if ret != 0 {
        goto ReturnI2Chdl
    }


    //for _, devName := range(qsfpTestList) {
    for _, qsfpInfo := range hwinfo.QsfpTbl {
        var sn string
        devName := qsfpInfo.DevName
        i2cInfo, err := i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
             ret =  err
             break
        }
        dcli.Println("i", "Starting test on", devName)

        switch i2cInfo.Comp {
        case "QSFP":
            sn, err = testQsfp(devName)
            if err != errType.SUCCESS {
                ret = err
                break
            }
            _, exists := qsfpSNmap[sn]
            if exists == true {
                dcli.Printf("f", "ERROR: DEV %s: QSFP SN %s was read from another QSFP.  Duplicate SN", devName, sn )
                ret = errType.FAIL
                break
            }
            qsfpSNmap[sn] = 1

        default:
            dcli.Println("f", "Unsupported device:", devName, "Comp:", i2cInfo.Comp )
            ret = errType.INVALID_PARAM
            break
        }

    }

ReturnI2Chdl:
    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- ret
    return
}

