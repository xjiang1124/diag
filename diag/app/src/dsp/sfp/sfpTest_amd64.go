//AMD64 BUILD.  DO NOT MESS WITH THE LINE BELOW


// +build amd64

//CODE AND COMMENTS BELOW THIS


package main

import (
    "flag"

    "common/dcli"
    "common/diagEngine"
    //"common/errType"
    //"device/sfp"
    //"device/fpga/taorfpga"
    //"hardware/i2cinfo"
    //"common/misc"
    //"hardware/hwinfo"
    "platform/taormina"
) 

func SfpI2CHdl(argList []string) {

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    ret := taormina.Sfp_i2c_test(argList)
    diagEngine.FuncMsgChan <- ret
    
    return
}

func SfpLaserHdl(argList []string) {
    
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    ret := taormina.Sfp_signal_test(argList)
    diagEngine.FuncMsgChan <- ret}


/*
    Read Device ID and compare with expected one
 */

/*
func testSfp(devName string) (sn string, err int) {
    devID, err := sfp.ReadId(devName)

    if err != errType.SUCCESS {
        dcli.Println("f", devName, " Read status failed!")
        return
    } else {
        dcli.Println("i", devName, " SFP Dev ID=", devID)
    }

    if devID != sfp.ID_SFPP {
        dcli.Println("f", devName, " Invalid Device ID: expected", sfp.ID_SFPP, "read", devID)
        err = errType.FAIL
        return 
    }
    err = sfp.VerifyCheckSums(devName)
    if err != errType.SUCCESS {
        return
    }
    _, _, sn, _, err = sfp.PrintSFPvendorData(devName)
    if err != errType.SUCCESS {
        return
    }

    
    return
}

func SfpI2CHdl(argList []string) {
    var data uint32
    var ret int
    sfpSNmap := make(map[string]byte)

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // Check for SFP Present
    for _, sfpInfo := range hwinfo.SfpTbl {
        regAddr := sfpInfo.PrstReg
        bitPos := sfpInfo.PrstBit
        data, _ = taorfpga.TaorReadU32(taorfpga.DEVREGION0, uint64(regAddr))  //return value uses golang err (not diag err)
        prstSts := data & (1<<byte(bitPos))
        //dcli.Printf("i", "regAddr=0x%x  bitPos=%d  data=0x%x   BIT=%d\n", regAddr, bitPos, data, prstSts)
        if prstSts != 0 {
            dcli.Println("e", sfpInfo.DevName, "SFP Not Present!")
            ret = errType.SFP_NOT_PRESENT
        }
    }
    
    if ret != 0 {
        goto ReturnI2Chdl
    }

    //for _, devName := range(sfpTestList) {
    for _, sfpInfo := range hwinfo.SfpTbl {
        var sn string
        devName := sfpInfo.DevName
        i2cInfo, err := i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
             ret =  err
             break
        }
        dcli.Println("i", "Starting test on", devName)

        switch i2cInfo.Comp {
        case "SFP":
            sn, err = testSfp(devName)
            if err != errType.SUCCESS {
                ret = err
                break
            }
            _, exists := sfpSNmap[sn]
            if exists == true {
                dcli.Printf("f", "ERROR: DEV %s: SFP SN %s was read from another SFP.  Duplicate SN", devName, sn )
                ret = errType.FAIL
                break
            }
            sfpSNmap[sn] = 1

        default:
            dcli.Println("f", "Unsupported device:", devName, "Comp:", i2cInfo.Comp )
            ret = errType.INVALID_PARAM
            break
        }
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
ReturnI2Chdl:
    if ret != 0 {
        dcli.Printf("e", "SFP I2C TEST FAILED\n")
    } else {
        dcli.Printf("i", "SFP I2C TEST PASSED\n")
    }
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
            dcli.Println("e", sfpInfo.DevName, "SFP Not Present!")
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
    if err != 0 {
        dcli.Printf("e", "SFP LASER TEST FAILED\n")
    } else {
        dcli.Printf("i", "SFP LASER TEST PASSED\n")
    }
    diagEngine.FuncMsgChan <- err
    
    return
}
*/
