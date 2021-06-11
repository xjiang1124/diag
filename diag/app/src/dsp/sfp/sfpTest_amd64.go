package main

import (
    "flag"

    "common/dcli"
    "common/diagEngine"
    "common/errType"
    "device/sfp"
    "device/fpga/taorfpga"
    "hardware/i2cinfo"
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
    } else {
        dcli.Println("i", devName, " SFP Dev ID=", devID)
    }

    if devID != sfp.ID_SFPP {
        dcli.Println("f", devName, " Invalid Device ID: expected", sfp.ID_SFPP, "read", devID)
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
        data, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, uint64(regAddr))  //return value uses golang err (not diag err)
        prstSts := data & (1<<byte(bitPos))
        //dcli.Printf("i", "regAddr=0x%x  bitPos=%d  data=0x%x   BIT=%d\n", regAddr, bitPos, data, prstSts)
        if prstSts == 0 {
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
        taorfpga.TaorWriteU32(taorfpga.DEVREGION0, uint64(txDisReg), (data | (1 << txDisBit)) )
        misc.SleepInUSec(2000)  //20ms
        
        data, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, uint64(sfpInfo.TxFaultReg)) 
        if data & (1 << sfpInfo.TxFaultBit) == 0 {
            dcli.Println("f", sfpInfo.DevName, "Failed to trigger Tx Fault")
            err = errType.SFP_TX_FAULT
            break
        }
        
        data, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, uint64(sfpInfo.RxLossReg)) 
        if data & (1 << sfpInfo.RxLossBit) == 0 {
            dcli.Println("f", sfpInfo.DevName, "Failed to trigger Rx Loss")
            err = errType.SFP_RX_LOSS
            break
        }
        dcli.Println("i", sfpInfo.DevName, "Tx Fault / Rx Loss passed phase 1")
        
        taorfpga.TaorWriteU32(taorfpga.DEVREGION0, uint64(txDisReg), data & (^(1 << byte(txDisBit))) )
        misc.SleepInUSec(2000)  //20ms
        
        data, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, uint64(sfpInfo.TxFaultReg)) 
        if data & (1 << byte(sfpInfo.TxFaultBit)) > 0 {
            dcli.Println("f", sfpInfo.DevName, "Failed to clear Tx Fault")
            err = errType.SFP_TX_FAULT
            break
        }
        
        data, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, uint64(sfpInfo.RxLossReg)) 
        if data & (1 << byte(sfpInfo.RxLossBit)) > 0 {
            dcli.Println("f", sfpInfo.DevName, "Failed to clear Rx Loss")
            err = errType.SFP_RX_LOSS
            break
        }
        dcli.Println("i", sfpInfo.DevName, "Tx Fault / Rx Loss passed phase 2")
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
Return:
    diagEngine.FuncMsgChan <- err
    
    return
}

