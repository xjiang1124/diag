package main

import (
    "flag"

    "common/dcli"
    "common/diagEngine"
    "common/errType"

    "device/fpga/taorfpga"

    "hardware/hwinfo"
) 

func SfpPresentHdl(argList []string) {
    var err int

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // Iterate over SFP table
    for _, sfpInfo := range hwinfo.SfpTbl {
        regAddr := sfpInfo.PrstReg
        bitPos := sfpInfo.PrstBit
        data, errgo := taorfpga.TaorReadU32(taorfpga.DEVREGION0, uint64(regAddr))  //return value uses golang err (not diag err)
        if errgo != nil {
            dcli.Println("f", sfpInfo.DevName, "Failed to obtain present info")
            err = errType.FAIL
        }

        prstSts := data & (1<<byte(bitPos))
        if prstSts != 0 {
            dcli.Println("i", sfpInfo.DevName, "Present")
        } else {
            dcli.Println("i", sfpInfo.DevName, "Not Present")
        }
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}
