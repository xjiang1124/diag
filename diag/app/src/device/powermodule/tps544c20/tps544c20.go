package tps544c20

import (
    "fmt"
    //"os"
    //"cardinfo"
    "common/cli"
    "common/errType"
    "protocol/pmbus"
    "protocol/smbus"
)


func I2cTest(devname string) (err int) {
    var data16 uint16
    pattern := []uint16{0x55AA, 0xAA55}
    err = smbus.Open(devname)
    if err != errType.SUCCESS {
        return
    }
    defer smbus.Close()

    for i:=0; i<len(pattern); i++ {
        err = pmbus.WriteWord(devname, MFR_SPECIFIC_D0, pattern[i])
        if err != errType.SUCCESS {
            cli.Println("e", " pmbus access to", devname,"failed")
            return
        }
        data16, err = pmbus.ReadWord(devname, MFR_SPECIFIC_D0)
        if err != errType.SUCCESS {
            cli.Println("e", " pmbus access to", devname,"failed")
            return
        }
        if data16 != pattern[i] {
            err = errType.FAIL
            cli.Printf("e", "Device-%s Register 0x%x:  Wrote 0x%.04x   Read 0x%.04x\n", devname, MFR_SPECIFIC_D0, pattern[i], data16)
            return
        }
    }

    data16, err = pmbus.ReadWord(devname, DEVICE_CODE)
    if err != errType.SUCCESS {
        cli.Println("e", " pmbus access to", devname,"failed")
        return
    }
    if data16 != DEVICE_CODE_DATA {
        err = errType.FAIL
        cli.Printf("e", "Device-%s Register 0x%x: Read 0x%.04x    Expect 0x%.04x\n", devname, DEVICE_CODE, data16, DEVICE_CODE_DATA)
        return
    }
    return
}


func ReadStatus(devName string) (status uint16, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    status, err = pmbus.ReadWord(devName, STATUS_WORD)
    return
}

//Read target voltage from VOUT COMMAND
func ReadTargetVoltage(devName string) (integer uint64, dec uint64, err int) {
    var VMODE byte
    var VCMD uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    //VMODE, err = pmbus.ReadByte(devName, VOUT_MODE)
    //VMODE = VMODE & 0x1F  //mask exponent
    
    //VCMD, err = pmbus.ReadWord(devName, VOUT_COMMAND)

    integer, dec, err =  pmbus.Linear16(uint64(VMODE), VCMD)
    return
}


//Read target voltage from VOUT 
func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var VMODE byte
    var VOUT uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    VMODE, err = pmbus.ReadByte(devName, VOUT_MODE)
    VMODE = VMODE & 0x1F  //mask exponent
    
    VOUT, err = pmbus.ReadWord(devName, READ_VOUT)

    integer, dec, err =  pmbus.Linear16(uint64(VMODE), VOUT)

    return
}

func ReadIout(devName string) (integer uint64, dec uint64, err int) {
    var IOUT uint16
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    IOUT, err = pmbus.ReadWord(devName, READ_IOUT)

    integer, dec, err =  pmbus.Linear11(IOUT)

    return
}

func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    voutInt, voutFrac, err := ReadVout(devName)
    if err != errType.SUCCESS {
        return
    }
    ioutInt, ioutFrac, err := ReadIout(devName)
    if err != errType.SUCCESS {
        return
    }

    voutFloat := float64(voutInt) + float64(voutFrac)/1000
    ioutFloat := float64(ioutInt) + float64(ioutFrac)/1000
    poutFloat := voutFloat * ioutFloat

    integer = uint64(poutFloat)
    dec = uint64((poutFloat - float64(uint64(poutFloat)))*1000)

    return
}

func DispStatus(devName string) (err int) {

    vrmTitle := []string {"POUT", "VOUT_TGT", "VOUT", "IOUT", "STATUS"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, "NAME")
    for _, title := range(vrmTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    //cli.Println("i", "0.00.00.00.00.00.0--")
    cli.Println("i", "=================================")
    cli.Println("i", outStr)

    outStr = fmt.Sprintf(fmtNameStr, devName)

    dig, frac, _ := ReadPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadTargetVoltage(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)// + "\n"

    cli.Println("i", outStr)

    return

}


func SetVMargin(devName string, pct int) (err int) {
    var marginCmd byte
    var marginVal uint16

    if pct > 8 || pct < -8 {
        return errType.INVALID_PARAM
    }

    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer smbus.Close()

    //Doesn't quite follow what the spec says.
    //Spec says margin will be in 2mv increments, but that doesn't happen on our parts
    //Part resolution is 0.001953125 (2^(-9)) but margin tics don't seem to follow that
    marginVal = 1 + (uint16(pct) * 3)

    if pct == 0 {
        marginCmd = MARGIN_NONE_CMD
    } else if pct > 0 {
        marginCmd = MARGIN_HIGH_IGN_FLT
        pmbus.WriteWord(devName, STEP_VREF_MARGIN_HIGH, marginVal)
    } else {
        marginCmd = MARGIN_LOW_IGN_FLT
        pmbus.WriteWord(devName, STEP_VREF_MARGIN_LOW, marginVal)
    }

    pmbus.WriteByte(devName, OPERATION, marginCmd)

    return
}
