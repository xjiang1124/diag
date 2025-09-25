package ltc3882

import (
    "fmt"
    "math"
    "common/cli"
    "common/errType"
    "hardware/i2cinfo"
    "protocol/pmbus"
)


func ReadFirmwareRevision(devName string) (revision uint16, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    // Always on PAGE 0
    err = pmbus.WriteByte(devName, pmbus.PAGE, 0)
    if err != errType.SUCCESS {
        return
    }

    revision, err = pmbus.ReadWord(devName, USER_DATA_04)

    return
}

func ReadStatus(devName string) (status uint16, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    status, err = pmbus.ReadStatusWord(devName, page)
    return
}

func ReadVboot(devName string) (integer uint64, dec uint64, err int) {
    var VMODE byte
    var VCMD uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    VCMD, err = pmbus.ReadWord(devName, VOUT_COMMAND)
    VMODE, err = pmbus.ReadByte(devName, VOUT_MODE)
    VMODE = VMODE & 0x1F  //mask exponent

    integer, dec, err =  pmbus.Linear16(uint64(VMODE), VCMD)

    return
}

func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var VMODE byte
    var VOUT uint16
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    VOUT, err = pmbus.ReadWord(devName, READ_VOUT)
    VMODE, err = pmbus.ReadByte(devName, VOUT_MODE)
    VMODE = VMODE & 0x1F  //mask exponent

    integer, dec, err =  pmbus.Linear16(uint64(VMODE), VOUT)

    return
}

func ReadIout(devName string) (integer uint64, dec uint64, err int) {
    var data uint16

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    data, err = pmbus.ReadWord(devName, READ_IOUT)
    integer, dec, err = pmbus.Linear11(data) 
    return
}


/****************************************************************** 
* 
* Not Paged.   VIN is for the part
* 
*******************************************************************/ 
func ReadVin(devName string) (integer uint64, dec uint64, err int) {
    var data uint16

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    // Write page register.. always 0 for VIN on this part
    err = pmbus.WriteByte(devName, pmbus.PAGE, 0)
    if err != errType.SUCCESS {
        return
    }

    data, err = pmbus.ReadWord(devName, READ_VIN)
    integer, dec, err = pmbus.Linear11(data) 
    return
}

func ReadTemp(devName string) (integer uint64, dec uint64, err int) {
    var data uint16

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    data, err = pmbus.ReadWord(devName, READ_TEMPERATURE_1)
    integer, dec, err = pmbus.Linear11(data) 
    return
}

func ReadTempInt(devName string) (integer uint64, dec uint64, err int) {
    var data uint16

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    data, err = pmbus.ReadWord(devName, READ_TEMPERATURE_2)
    integer, dec, err = pmbus.Linear11(data) 
    return
}

func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    var data uint16

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    data, err = pmbus.ReadWord(devName, READ_POUT)
    integer, dec, err = pmbus.Linear11(data) 
    return
}



func SetVMargin(devName string, pct int) (err int) {
    var marginReg uint64
    var marginCmd byte
    var voutMode byte
    var voutcmd uint16

    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    defer pmbus.Close()

    page, err := i2cinfo.GetPage(devName)
    if err != errType.SUCCESS {
        return
    }

    // Write page register
    err = pmbus.WriteByte(devName, pmbus.PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    // Disable Vmargin
    err = pmbus.WriteByte(devName, OPERATION, MARGIN_NONE_CMD)
    if err != errType.SUCCESS {
        cli.Println("e", "Disable VMargin failed!")
        return
    }

    if pct == 0 {
        marginCmd = MARGIN_NONE_CMD
    } else if pct > 0 {
        marginCmd = MARGIN_HIGH_CMD
        marginReg = pmbus.VOUT_MARGIN_HIGH
    } else {
        marginCmd = MARGIN_LOW_CMD
        marginReg = pmbus.VOUT_MARGIN_LOW
    }

    voutcmd, err = pmbus.ReadWord(devName, VOUT_COMMAND)

    voutMode, err = pmbus.ReadByte(devName, pmbus.VOUT_MODE)

    {
        var integer, dec uint64
        var expval int = int(voutMode & 0x1F)

        //Get Default Target Voltage for Part
        integer, dec, err =  pmbus.Linear16(uint64(expval), voutcmd)
        def_volt := float64(integer) + (float64(dec)/1000)



        //Get Exponent Portion
        if expval > 0xF {
            expval = 0x20 - expval
            expval = 0 - expval
        }
        exponentF := math.Pow(2, float64(expval))

        //Calculate what to set Margin High or Low Reg to
        marginVal := uint64( (def_volt + (def_volt * (float64(pct) / 100))) / exponentF)

        //fmt.Printf(" voutcmd=%x  marginVal=%x float64(pct)=%f  def_volt=%f\n", voutcmd, (marginVal & 0xFFFF), float64(pct), def_volt)

        if pct != 0 {
            err = pmbus.WriteWord(devName, marginReg, uint16(marginVal))
            if err != errType.SUCCESS {
                cli.Println("e", "WriteWord to %s reg %d failed", devName, marginReg)
                return
            }
        }
        err = pmbus.WriteByte(devName, pmbus.OPERATION, marginCmd)
        if err != errType.SUCCESS {
            cli.Println("e", "WriteByte to %s reg %d failed", devName, pmbus.OPERATION)
            return
        }

    }

    return
}

func DispStatus(devName string) (err int) {
    vrmTitle := []string {"VIN", "VBOOT", "VOUT", "IOUT", "POUT", "TEMPEXT", "TEMPINT", "STATUS", "REVISION"}
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-9s"
    fmtNameStr := "%-12s"

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

    dig, frac, err := ReadVin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    if err != errType.SUCCESS {
        return
    }

    dig, frac, _ = ReadVboot(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadPout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadTemp(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadTempInt(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)
    

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp) 

    fwRevision, _ := ReadFirmwareRevision(devName)
    outStrTemp = fmt.Sprintf("0x%X", fwRevision)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp) + "\n"

    cli.Println("i", outStr)

    return
}


