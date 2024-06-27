package ina3221a

import (
    "fmt"
    "common/cli"
    "common/dcli"
    "common/errType"
    "common/misc"
    "protocol/smbus"
    "hardware/i2cinfo"
    "hardware/vrminfo"
)

func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var channel byte
    var data uint16

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    // page variable is used to store the channel # for this component, not actual page in memory
    channel, err = i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        dcli.Printf("e", "No channel (page) defined for %s", devName)
        return
    }
    reg := voutRegAddr[channel]
    data, err = smbus.ReadWord(devName, reg)
    if err != errType.SUCCESS {
        dcli.Printf("e", "Failed to read device %s's ina3221 register %x", devName, reg)
        return
    }
    data = misc.SwapUint16(data)
    curBin := (float64)(data & RESULT_BITS >> RESERVED_BITS) * VOUT_SCALE
    integer = uint64(curBin)
    dec = uint64(curBin * 1000) % 1000
    return
}

func ReadIout(devName string) (integer uint64, dec uint64, err int) {
    var channel byte
    var data uint16

    senseResistance := vrminfo.GetSenseResistance(devName)

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    // page variable is used to store the channel # for this component, not actual page in memory
    channel, err = i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        dcli.Printf("e", "No channel (page) defined for %s", devName)
        return
    }
    reg := ioutRegAddr[channel]
    data, err = smbus.ReadWord(devName, reg)
    if err != errType.SUCCESS {
        dcli.Printf("e", "Failed to read device %s's register %x", devName, reg)
        return
    }
    data = misc.SwapUint16(data)
    curBin := (float64)(data & RESULT_BITS >> RESERVED_BITS) * IOUT_SCALE / senseResistance
    integer = uint64(curBin)
    dec = uint64(curBin * 1000) % 1000
    return
}

func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    vout_int, vout_dec, vout_err := ReadVout(devName)
    if vout_err != errType.SUCCESS {
        err = vout_err
        return
    }
    iout_int, iout_dec, iout_err := ReadIout(devName)
    if iout_err != errType.SUCCESS {
        err = iout_err
        return
    }
    vout := (float64)((vout_int * 1000) + vout_dec) / 1000
    iout := (float64)((iout_int * 1000) + iout_dec) / 1000
    pout := vout * iout
    integer = uint64(pout)
    dec = uint64(pout * 1000) % 1000
    return
}

func ReadMFRID(devName string) (data uint16, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data, err = smbus.ReadWord(devName, MFR_ID)
    data = misc.SwapUint16(data)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to read device ", devName)
        return
    }

    return
}

func ReadDieID(devName string) (data uint16, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    data, err = smbus.ReadWord(devName, DIE_ID)
    data = misc.SwapUint16(data)
    if err != errType.SUCCESS {
        dcli.Println("e", "Failed to read device ", devName)
        return
    }

    return
}

func DispStatus(devName string) (err int) {
    vrmTitle := []string {"VOUT", "IOUT", "POUT"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", "=================================")
    cli.Println("i", outStr)

    outStr = fmt.Sprintf(fmtNameStr, devName)
    var dig uint64
    var frac uint64
    for _, title := range(vrmTitle) {
        switch title {
        case "VOUT":
            dig, frac, _ = ReadVout(devName)
        case "IOUT":
            dig, frac, _ = ReadIout(devName)
        case "POUT":
            dig, frac, _ = ReadPout(devName)
        default:
            dig = 0
            frac = 0
        }
        outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
        outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    }
    cli.Println("i", outStr)

    return
}
