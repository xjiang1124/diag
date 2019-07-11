package main

import (
    "flag"

    "common/dcli"
    "common/diagEngine"
    "common/errType"

    //"device/cpld/cpld"
    "common/spi"
    "device/qsfp"

    "hardware/i2cinfo"
    "hardware/hwinfo"
)

func qsfpLaserEnDis(mask int, enDis int) (err int) {
    bitMask := 1
    for _, devName := range(qsfpTestList) {
        if bitMask & mask == 0 {
            continue
        }

        i2cInfo, errgo := i2cinfo.GetI2cInfo(devName)
        if errgo != errType.SUCCESS {
             err = errgo
             break
        }
        dcli.Println("i", "Starting testing", devName)

        switch i2cInfo.Comp {
        case "QSFP":
            errgo = qsfp.LaserEnDis(devName, enDis)
            if errgo != errType.SUCCESS {
                err = errgo
            }
        default:
            dcli.Println("f", "Unsupported device:", devName, "Comp:", i2cInfo.Comp)
            err = errType.INVALID_PARAM
        }
    }
    return
}

func QsfpLaser_EnHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Int("mask", 0x3, "Devices instance index")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    err := qsfpLaserEnDis(*maskPtr, qsfp.ENABLE)
    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func QsfpLaser_DisHdl(argList []string) {
    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)
    maskPtr := fs.Int("mask", 0x3, "Devices instance index")

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    err := qsfpLaserEnDis(*maskPtr, qsfp.DISABLE)
    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}

func QsfpPresentHdl(argList []string) {
    var err int
    var regData uint32
    var data byte

    fs := flag.NewFlagSet("FlagSet", flag.ContinueOnError)

    errFs := fs.Parse(argList)
    if errFs != nil {
        dcli.Println("e", "Parse failed", errFs)
    }

    // Iterate over QSFP table
    for _, qsfpInfo := range hwinfo.QsfpTbl {
        regAddr := qsfpInfo.PrstReg
        bitPos := qsfpInfo.PrstBit
        spi.CpldRead(uint32(regAddr), &regData)
        data = byte(regData)

        prstSts := data & (1<<byte(bitPos))
        if prstSts != 0 {
            dcli.Println("i", qsfpInfo.DevName, "Present")
        } else {
            dcli.Println("i", qsfpInfo.DevName, "Not Present")
        }
    }

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- err
    return
}
