package main

import (
    "flag"

    "common/dcli"
    "common/diagEngine"
    "common/errType"
    "device/sfp"
    "hardware/i2cinfo"
    "common/spi"
    "common/misc"
    "hardware/hwinfo"
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

func SfpLaserHdl(argList []string) {
    var err int
    var data uint32

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // Iterate over SFP table
    for _, sfpInfo := range hwinfo.SfpTbl {
        regAddr := sfpInfo.PrstReg
        bitPos := sfpInfo.PrstBit
        spi.CpldRead(regAddr, &data)
        prstSts := data & (1<<byte(bitPos))
        if prstSts != 0 {
            dcli.Println("i", sfpInfo.DevName, "Present")
        } else {
            dcli.Println("i", sfpInfo.DevName, "Not Present!")
            err = errType.SFP_NOT_PRESENT
        }
    }
    
    if err != 0 {
        goto Return
    }
    
    for _, sfpInfo := range hwinfo.SfpTbl {
        txDisReg := sfpInfo.TxDisReg
        txDisBit := sfpInfo.TxDisBit
        errgo := spi.CpldWrite(txDisReg, data | 1 << txDisBit)
        if errgo != errType.SUCCESS {
            dcli.Println("f", sfpInfo.DevName, "Failed to write Tx disable bit")
            err = errgo
            break
        }
        misc.SleepInSec(1)
        
        spi.CpldRead(sfpInfo.TxFaultReg, &data)
        if data & (1 << sfpInfo.TxFaultBit) == 0 {
            dcli.Println("f", sfpInfo.DevName, "Failed to trigger Tx Fault")
            err = errType.SFP_TX_FAULT
            break
        }
        
        spi.CpldRead(sfpInfo.RxLossReg, &data)
        if data & (1 << sfpInfo.RxLossBit) == 0 {
            dcli.Println("f", sfpInfo.DevName, "Failed to trigger Rx Loss")
            err = errType.SFP_RX_LOSS
            break
        }
        
        errgo = spi.CpldWrite(txDisReg, data & (^(1 << byte(txDisBit))))
        if errgo != errType.SUCCESS {
            dcli.Println("f", sfpInfo.DevName, "Failed to clear Tx disable bit")
            err = errgo
            break
        }
        misc.SleepInSec(1)
        
        spi.CpldRead(sfpInfo.TxFaultReg, &data)
        if data & (1 << byte(sfpInfo.TxFaultBit)) > 0 {
            dcli.Println("f", sfpInfo.DevName, "Failed to clear Tx Fault")
            err = errType.SFP_TX_FAULT
            break
        }
        
        spi.CpldRead(sfpInfo.RxLossReg, &data)
        if data & (1 << byte(sfpInfo.RxLossBit)) > 0 {
            dcli.Println("f", sfpInfo.DevName, "Failed to clear Rx Loss")
            err = errType.SFP_RX_LOSS
            break
        }
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
Return:
    diagEngine.FuncMsgChan <- err
    return
}

