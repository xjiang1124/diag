package tps536c7

import (
    "fmt"
    "math"
    "common/cli"
    "common/errType"
    "hardware/i2cinfo"
    "protocol/pmbus"
)


func ReadStatus(devName string) (status uint16, err int) {
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
    err = pmbus.WriteByte(devName, PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    status, err = pmbus.ReadWord(devName, STATUS_WORD)
    return
}




func ReadVin(devName string) (integer uint64, dec uint64, err int) {
    var VIN uint16
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
    err = pmbus.WriteByte(devName, PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    VIN, err = pmbus.ReadWord(devName, READ_VIN)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(VIN)

    return

}


//Read target voltage from VOUT 
func ReadVout(devName string) (integer uint64, dec uint64, err int) {
    var VOUT uint16
    var VMODE uint8
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
    err = pmbus.WriteByte(devName, PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    VMODE, err = pmbus.ReadByte(devName, VOUT_MODE);
    if err != errType.SUCCESS {
        return
    }

    VOUT, err = pmbus.ReadWord(devName, READ_VOUT)
    if err != errType.SUCCESS {
        return
    }

    VMODE = VMODE & 0x1F
    integer, dec, err =  pmbus.Linear16(uint64(VMODE), VOUT)
    return

    return
}


func ReadIin(devName string) (integer uint64, dec uint64, err int) {
    var IIN uint16
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
    err = pmbus.WriteByte(devName, PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    IIN, err = pmbus.ReadWord(devName, READ_IIN)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(IIN)

    return
}


func ReadIout(devName string) (integer uint64, dec uint64, err int) {
    var IOUT uint16
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
    err = pmbus.WriteByte(devName, PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    IOUT, err = pmbus.ReadWord(devName, READ_IOUT)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(IOUT)

    return
}


func ReadPin(devName string) (integer uint64, dec uint64, err int) {
    var PIN uint16
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
    err = pmbus.WriteByte(devName, PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    PIN, err = pmbus.ReadWord(devName, READ_PIN)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(PIN)
    return
}


func ReadPout(devName string) (integer uint64, dec uint64, err int) {
    var POUT uint16
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
    err = pmbus.WriteByte(devName, PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    POUT, err = pmbus.ReadWord(devName, READ_POUT)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(POUT)
    return
}

func ReadTemp(devName string) (integer uint64, dec uint64, err int) {
    var TEMP uint16
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
    err = pmbus.WriteByte(devName, PAGE, page)
    if err != errType.SUCCESS {
        return
    }

    TEMP, err = pmbus.ReadWord(devName, READ_TEMPERATURE_1)
    if err != errType.SUCCESS {
        return
    }

    integer, dec, err =  pmbus.Linear11(TEMP)
    return
}

func GetTemperature(devName string) (temperatures []float64, err int) {
    dig, frac, err := ReadTemp(devName)
    temperatures = append(temperatures, float64(dig) + (float64(frac)/1000))
    return
}


// vrmTitle := []string {"VBOOT", "VOUT", "POUT", "IOUT", "VIN", "PIN", "IIN"}
func DispVoltWattAmp(devName string) (err int) {
    var fmtDigFrac string = "%d.%03d"
    fmtStr := "%-10s"
    fmtNameStr := "%-20s"

    var outStr string
    var outStrTemp string
    outStr = fmt.Sprintf(fmtNameStr, devName)

    outStrTemp = "-"
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err := ReadVout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err = ReadPout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    digIout, fracIout, err := ReadIout(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, digIout, fracIout)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err = ReadVin(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err = ReadPin(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, err = ReadIin(devName)
    if err != errType.SUCCESS { return; }
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    
    fmt.Println(outStr)

    return
}

func DispStatus(devName string) (err int) {
    vrmTitle := []string {"POUT", "VOUT", "IOUT", "PIN", "VIN", "IIN", "TEMP", "STATUS"}
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

    dig, frac, _ = ReadVout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIout(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadPin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadVin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadIin(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    dig, frac, _ = ReadTemp(devName)
    outStrTemp = fmt.Sprintf(fmtDigFrac, dig, frac)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)

    status, _ := ReadStatus(devName)
    outStrTemp = fmt.Sprintf("0x%X", status)
    outStr = outStr + fmt.Sprintf(fmtStr, outStrTemp)// + "\n"

    cli.Println("i", outStr)

    return
}



func SetVMargin(devName string, pct int) (err int) {
    var marginReg uint64
    var marginCmd byte
    //var data uint16
    var dacStepRegVal byte
    //var dacStep uint64
    var voutcmd uint16

    if pct > 10 || pct < -10 {
        cli.Printf("e", "%s Max Margin value is +/- 10 percent", devName)
        return errType.INVALID_PARAM
    }

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

    voutcmd, err = pmbus.ReadWord(devName, VOUT_COMMAND)
    if err != errType.SUCCESS {
        return
    }

    
    // Disable Vmargin
    err = pmbus.WriteByte(devName, pmbus.OPERATION, OP_ON_MARGIN_NONE)
    if err != errType.SUCCESS {
        cli.Println("e", "VMargin failed!")
        return
    }

    if pct == 0 {
        marginCmd = OP_ON_MARGIN_NONE
    } else if pct > 0 {
        marginCmd = OP_MARGIN_HIGH_IGN_FLT
        marginReg = pmbus.VOUT_MARGIN_HIGH
    } else {
        marginCmd = OP_MARGIN_LOW_IGN_FLT
        marginReg = pmbus.VOUT_MARGIN_LOW
    }

    dacStepRegVal, err = pmbus.ReadByte(devName, pmbus.VOUT_MODE)


    //LINEAR16 FORMAT FOR LIPARI
    {
        var integer, dec uint64
        var expval int = int(dacStepRegVal & 0x1F)

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

        fmt.Printf(" voutcmd=%x  marginVal=%x float64(pct)=%f  def_volt=%f\n", voutcmd, (marginVal & 0xFFFF), float64(pct), def_volt)

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
